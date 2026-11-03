"""The replacement: the new device takes over the old one's names, entity ids, area, settings and history.

History and long-term statistics follow by themselves, because the recorder keeps them by entity_id: when the new
entity gets the old entity_id, it simply continues the old series. Energy sums continue too; a new meter starting
at 0 is seen as a reset.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
import logging
import time
from typing import Any

from homeassistant import loader
from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import STATE_UNAVAILABLE, STATE_UNKNOWN
from homeassistant.core import CALLBACK_TYPE, HomeAssistant, callback
from homeassistant.helpers import device_registry as dr, entity_registry as er, issue_registry as ir
from homeassistant.helpers.event import async_call_later
from homeassistant.helpers.storage import Store
from homeassistant.util.file import write_utf8_file_atomic

from .const import AUTOMATIONS_FILE, CHECK_AFTER, DOMAIN, SCRIPTS_FILE, TEXTS
from .matching import match

_LOGGER = logging.getLogger(__name__)
_KEEP_DAYS = 30


@dataclass
class Plan:
    """What will happen, shown to the user before anything changes."""

    old: dr.DeviceEntry
    new: dr.DeviceEntry
    old_entities: list[er.RegistryEntry]
    new_entities: list[er.RegistryEntry]
    mapping: dict[str, str | None]
    # Names of automations and scripts that point at the old device itself (not only its entities).
    uses_device: list[str] = field(default_factory=list)

    @property
    def pairs(self) -> list[tuple[er.RegistryEntry, er.RegistryEntry]]:
        new = {e.entity_id: e for e in self.new_entities}
        return [(o, new[self.mapping[o.entity_id]]) for o in self.old_entities if self.mapping.get(o.entity_id) in new]


def device_name(device: dr.DeviceEntry) -> str:
    return device.name_by_user or device.name or device.model or device.id


def async_plan(
    hass: HomeAssistant, old_id: str, new_id: str, mapping: dict[str, str | None] | None = None
) -> Plan | None:
    devices, entities = dr.async_get(hass), er.async_get(hass)
    old, new = devices.async_get(old_id), devices.async_get(new_id)
    if old is None or new is None or old_id == new_id:
        return None
    old_entities = er.async_entries_for_device(entities, old_id, include_disabled_entities=True)
    new_entities = er.async_entries_for_device(entities, new_id, include_disabled_entities=True)
    plan = Plan(old, new, old_entities, new_entities, mapping or match(old_entities, new_entities))
    plan.uses_device = _users_of_device(hass, old_id)
    return plan


def _users_of_device(hass: HomeAssistant, device_id: str) -> list[str]:
    from homeassistant.components import automation, script

    found = []
    if "automation" in hass.config.components:
        found += automation.automations_with_device(hass, device_id)
    if "script" in hass.config.components:
        found += script.scripts_with_device(hass, device_id)
    names = []
    for entity_id in found:
        state = hass.states.get(entity_id)
        names.append((state and state.attributes.get("friendly_name")) or entity_id)
    return sorted(names)


class Replacer:
    """Carries out replacements and remembers them for 30 days."""

    def __init__(self, hass: HomeAssistant) -> None:
        self.hass = hass
        self.store: Store[dict[str, Any]] = Store(hass, 1, f"{DOMAIN}.history")
        self.history: list[dict[str, Any]] = []
        self._timers: list[CALLBACK_TYPE] = []

    @callback
    def async_stop(self) -> None:
        for cancel in self._timers:
            cancel()

    async def async_load(self) -> None:
        cutoff = time.time() - _KEEP_DAYS * 86400
        self.history = [h for h in (await self.store.async_load() or {}).get("history", []) if h["at"] >= cutoff]

    async def async_replace(self, plan: Plan, remove_old: bool) -> dict[str, Any]:
        hass = self.hass
        devices, entities = dr.async_get(hass), er.async_get(hass)
        pairs = plan.pairs
        record: dict[str, Any] = {
            "at": time.time(),
            "old_device": {"id": plan.old.id, "name": device_name(plan.old), "model": plan.old.model},
            "new_device": {"id": plan.new.id, "name": device_name(plan.new), "model": plan.new.model},
            "entities": [{"entity_id": o.entity_id, "was": n.entity_id, "name": o.name} for o, n in pairs],
            "files": {},
        }
        old_ids = [o.entity_id for o, _ in pairs]
        temp_ids = [n.entity_id for _, n in pairs]

        # 1. The old ones make room. Removing the device from its integration removes all its entities.
        removed = await _remove_device(hass, plan.old) if remove_old else False
        for entity_id in old_ids:
            if entities.async_get(entity_id):
                entities.async_remove(entity_id)
        await _wait_until_gone(hass, old_ids)

        # 2. The new entities take over the old entity ids and everything the user set on them.
        for old_entry, new_entry in pairs:
            entities.async_update_entity(
                new_entry.entity_id,
                new_entity_id=old_entry.entity_id,
                name=old_entry.name,
                icon=old_entry.icon,
                area_id=old_entry.area_id,
                labels=set(old_entry.labels),
                aliases=list(old_entry.aliases),
                categories=dict(old_entry.categories),
                device_class=old_entry.device_class,
                hidden_by=old_entry.hidden_by if old_entry.hidden_by == er.RegistryEntryHider.USER else None,
            )
            for domain, options in old_entry.options.items():
                merged = dict(new_entry.options.get(domain, {})) | dict(options)
                entities.async_update_entity_options(old_entry.entity_id, domain, merged)

        # 3. The new device gets the old one's name and area.
        devices.async_update_device(
            plan.new.id,
            name_by_user=device_name(plan.old),
            area_id=plan.old.area_id or plan.new.area_id,
            labels=set(plan.old.labels) | set(plan.new.labels),
        )

        # 4. Automations and scripts that point at the old device or its entities by id.
        ids = {plan.old.id: plan.new.id} | {o.id: n.id for o, n in pairs}
        changed = await self._rewrite(ids, record)

        # 5. The new entities' first minutes under their own ids are not needed.
        await _clean_recorder(hass, temp_ids)
        await _logbook(hass, plan, old_ids)
        self._timers.append(_check_later(hass, plan, old_ids))

        self.history.append(record)
        self.store.async_delay_save(lambda: {"history": self.history}, 1)
        return {"moved": len(pairs), "removed": removed, "changed": changed}

    async def _rewrite(self, ids: dict[str, str], record: dict[str, Any]) -> list[str]:
        """Replace old device and entity registry ids in the automation and script files, then reload them."""
        changed = []
        for domain, name in (("automation", AUTOMATIONS_FILE), ("script", SCRIPTS_FILE)):
            path = self.hass.config.path(name)
            text = await self.hass.async_add_executor_job(_read, path)
            if text is None:
                continue
            new = text
            for old_id, new_id in ids.items():
                new = new.replace(old_id, new_id)
            if new == text:
                continue
            record["files"][name] = text
            await self.hass.async_add_executor_job(write_utf8_file_atomic, path, new)
            changed.append(domain)
            if self.hass.services.has_service(domain, "reload"):
                await self.hass.services.async_call(domain, "reload", blocking=True)
        return changed


def _read(path: str) -> str | None:
    try:
        with open(path, encoding="utf-8") as file:
            return file.read()
    except FileNotFoundError:
        return None


async def _remove_device(hass: HomeAssistant, device: dr.DeviceEntry) -> bool:
    """Remove the old device the way the device page does, if its integration allows it."""
    entry = hass.config_entries.async_get_entry(device.config_entry_id) if device.config_entry_id else None
    if entry is not None and entry.state is ConfigEntryState.LOADED:
        if not entry.supports_remove_device:
            return False
        try:
            component = await (await loader.async_get_integration(hass, entry.domain)).async_get_component()
            if not await component.async_remove_config_entry_device(hass, entry, device):
                return False
        except Exception:  # noqa: BLE001 - the integration said no in its own way
            _LOGGER.warning("%s did not remove %s", entry.domain, device_name(device), exc_info=True)
            return False
    registry = dr.async_get(hass)
    if registry.async_get(device.id):
        registry.async_remove_device(device.id)
    return True


async def _wait_until_gone(hass: HomeAssistant, entity_ids: list[str]) -> None:
    """Give the old entities a moment to remove themselves, then clear what's left (a dead device's state)."""
    for _ in range(100):
        if not any(hass.states.get(e) for e in entity_ids):
            return
        await asyncio.sleep(0)
    for entity_id in entity_ids:
        hass.states.async_remove(entity_id)


async def _clean_recorder(hass: HomeAssistant, entity_ids: list[str]) -> None:
    if "recorder" not in hass.config.components or not entity_ids:
        return
    from homeassistant.components.recorder import get_instance

    get_instance(hass).async_clear_statistics(entity_ids)
    if hass.services.has_service("recorder", "purge_entities"):
        await hass.services.async_call("recorder", "purge_entities", {"entity_id": entity_ids, "keep_days": 0})


async def _logbook(hass: HomeAssistant, plan: Plan, entity_ids: list[str]) -> None:
    if not hass.services.has_service("logbook", "log"):
        return
    text = TEXTS.get(hass.config.language.split("-")[0], TEXTS["en"])
    new = " ".join(p for p in (plan.new.manufacturer, plan.new.model) if p) or device_name(plan.new)
    data = {"name": device_name(plan.old), "message": text["logbook"].format(new=new), "domain": DOMAIN}
    if entity_ids:
        data["entity_id"] = entity_ids[0]
    await hass.services.async_call("logbook", "log", data)


def _check_later(hass: HomeAssistant, plan: Plan, entity_ids: list[str]) -> CALLBACK_TYPE:
    """Ten minutes later: if none of the new entities has a value, say so."""
    name = device_name(plan.old)

    async def _check(_now) -> None:
        if not entity_ids or any(
            (s := hass.states.get(e)) is not None and s.state not in (STATE_UNAVAILABLE, STATE_UNKNOWN)
            for e in entity_ids
        ):
            return
        ir.async_create_issue(
            hass,
            DOMAIN,
            f"silent_{plan.new.id}",
            is_fixable=False,
            severity=ir.IssueSeverity.WARNING,
            translation_key="silent",
            translation_placeholders={"name": name},
        )

    return async_call_later(hass, CHECK_AFTER, _check)
