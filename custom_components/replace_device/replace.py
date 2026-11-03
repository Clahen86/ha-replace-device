"""The replacement: the new device takes over the old one's names, entity ids, area, settings and history.

History and long-term statistics follow by themselves, because the recorder keeps them by entity_id: when the new
entity gets the old entity_id, it simply continues the old series. Energy sums continue too; a new meter starting
at 0 is seen as a reset.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
import json
import logging
import os
import time
from collections.abc import Awaitable
from typing import Any
import uuid

from homeassistant import loader
from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import STATE_UNAVAILABLE, STATE_UNKNOWN
from homeassistant.core import CALLBACK_TYPE, Event, EventStateChangedData, HomeAssistant, callback
from homeassistant.helpers import device_registry as dr, entity_registry as er, issue_registry as ir
from homeassistant.helpers.event import async_call_later, async_track_state_change_event
from homeassistant.helpers.storage import Store
from homeassistant.util.file import write_utf8_file_atomic

from . import ai, references, triggers
from .const import AUTOMATIONS_FILE, CHECK_AFTER, DOMAIN, SCENES_FILE, SCRIPTS_FILE, TEXTS, Z2M_BASE_TOPIC
from .hardware import z2m_ieee, z2m_name
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
    plan = Plan(
        old, new, old_entities, new_entities, mapping if mapping is not None else match(old_entities, new_entities)
    )
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
        # Optional AI Task entity, set from the integration's options.
        self.ai_entity: str | None = None
        self._ai_cache: dict[tuple[str, str], dict[str, str]] = {}

    @callback
    def async_stop(self) -> None:
        for cancel in self._timers:
            cancel()

    async def async_load(self) -> None:
        cutoff = time.time() - _KEEP_DAYS * 86400
        self.history = [h for h in (await self.store.async_load() or {}).get("history", []) if h["at"] >= cutoff]

    async def async_replace(
        self,
        plan: Plan,
        remove_old: bool,
        rename_z2m: bool = False,
        reload: bool = True,
        batch: str | None = None,
    ) -> dict[str, Any]:
        hass = self.hass
        devices, entities = dr.async_get(hass), er.async_get(hass)
        pairs = plan.pairs
        now = time.time()
        record: dict[str, Any] = {
            "id": uuid.uuid4().hex,
            "at": now,
            "old_device": {"id": plan.old.id, "name": device_name(plan.old), "model": plan.old.model},
            # How the new device looked before, so it can be given back.
            "new_device": {
                "id": plan.new.id,
                "name": device_name(plan.new),
                "model": plan.new.model,
                "name_by_user": plan.new.name_by_user,
                "area_id": plan.new.area_id,
                "labels": sorted(plan.new.labels),
            },
            "entities": [
                {"entity_id": o.entity_id, "was": n.entity_id, "uuid": n.id, **_settings(n)} for o, n in pairs
            ],
            "ids": {plan.old.id: plan.new.id} | {o.id: n.id for o, n in pairs},
            "files": [],
            "batch": batch,
            "undone": False,
        }
        old_domain, new_domain = _domain(hass, plan.old), _domain(hass, plan.new)
        old_ids = [o.entity_id for o, _ in pairs]
        temp_ids = [n.entity_id for _, n in pairs]

        # 1. The old ones make room. Removing the device from its integration removes all its entities.
        removed = await _remove_device(hass, plan.old) if remove_old else False
        for entity_id in old_ids:
            if entities.async_get(entity_id):
                entities.async_remove(entity_id)
        await _wait_until_gone(hass, old_ids)

        # 2. The new entities take over the old entity ids and everything the user set on them.
        failed = []
        for old_entry, new_entry in pairs:
            try:
                entities.async_update_entity(
                    new_entry.entity_id, new_entity_id=old_entry.entity_id, **_update(old_entry)
                )
                for domain, options in old_entry.options.items():
                    merged = dict(new_entry.options.get(domain, {})) | dict(options)
                    entities.async_update_entity_options(old_entry.entity_id, domain, merged)
            except (KeyError, ValueError):
                _LOGGER.warning("%s could not take over %s", new_entry.entity_id, old_entry.entity_id, exc_info=True)
                failed.append(old_entry.entity_id)
        if failed:
            pairs = [(o, n) for o, n in pairs if o.entity_id not in failed]
            old_ids, temp_ids = [o.entity_id for o, _ in pairs], [n.entity_id for _, n in pairs]
            record["entities"] = [e for e in record["entities"] if e["entity_id"] not in failed]
            record["ids"] = {plan.old.id: plan.new.id} | {o.id: n.id for o, n in pairs}
        record["failed"] = failed
        # From here on the replacement can be undone, whatever happens in the steps below.
        self.history.append(record)
        self._save()

        # 3. The new device gets the old one's name and area.
        devices.async_update_device(
            plan.new.id,
            name_by_user=device_name(plan.old),
            area_id=plan.old.area_id or plan.new.area_id,
            labels=set(plan.old.labels) | set(plan.new.labels),
        )

        # 4. Automations and scripts that point at the old device or its entities by id, and device triggers that
        #    have other names in the new integration (a ZHA button press is an "action" in Zigbee2MQTT).
        changed = await _safely("updating automations and scripts", self._rewrite(record["ids"], reload=False), [])
        path = hass.config.path(AUTOMATIONS_FILE)
        before = await hass.async_add_executor_job(_read, path)
        translation = await _safely(
            "translating device triggers",
            triggers.async_translate(hass, plan.new.id, old_domain, new_domain, self.ai_entity),
            {"translated": [], "unresolved": []},
        )
        if translation["translated"]:
            record["automations_before"] = before
            record["automations_after"] = await hass.async_add_executor_job(_read, path)
            changed = sorted(set(changed) | {"automation"})
        record["triggers"] = translation
        record["files"] = changed
        # Dashboards made in the UI and other integrations (Battery Notes, Powercalc …) that store the device id.
        skip = {d for d in (old_domain, new_domain) if d}
        record["dashboards"] = await _safely(
            "updating dashboards", references.async_rewrite_dashboards(hass, record["ids"]), []
        )
        record["integrations"] = await _safely(
            "updating other integrations", references.async_rewrite_entries(hass, record["ids"], skip), []
        )
        if reload:
            await self.async_reload(set(changed))
        renamed = False
        if rename_z2m:
            renamed = await _safely(
                "renaming in Zigbee2MQTT", _rename_in_z2m(hass, plan.new, device_name(plan.old)), False
            )

        # 5. The new entities' first minutes under their own ids are not needed.
        await _safely("cleaning up history", _clean_recorder(hass, temp_ids), None)
        await _safely("writing the logbook", _logbook(hass, plan, old_ids), None)
        self._timers.append(_check_later(hass, plan, old_ids))
        self._save()
        return {
            "id": record["id"],
            "moved": len(pairs),
            "removed": removed,
            "changed": changed,
            "renamed": renamed,
            "triggers": translation,
            "dashboards": record["dashboards"],
            "integrations": record["integrations"],
            "failed": failed,
        }

    async def async_replace_entity(
        self, name: str, old: er.RegistryEntry, new: er.RegistryEntry, batch: str | None = None, reload: bool = True
    ) -> dict[str, Any]:
        """One entity without a device of its own takes over another, e.g. a Zigbee group made again elsewhere."""
        hass, entities = self.hass, er.async_get(self.hass)
        now = time.time()
        record: dict[str, Any] = {
            "id": uuid.uuid4().hex,
            "at": now,
            "old_device": {"id": None, "name": name, "model": "Group"},
            "new_device": {"id": None, "name": new.entity_id, "model": "Group"},
            "entities": [{"entity_id": old.entity_id, "was": new.entity_id, "uuid": new.id, **_settings(new)}],
            "ids": {old.id: new.id},
            "files": [],
            "batch": batch,
            "undone": False,
        }
        entities.async_remove(old.entity_id)
        await _wait_until_gone(hass, [old.entity_id])
        temp_id = new.entity_id
        entities.async_update_entity(temp_id, new_entity_id=old.entity_id, **_update(old))
        for domain, options in old.options.items():
            entities.async_update_entity_options(
                old.entity_id, domain, dict(new.options.get(domain, {})) | dict(options)
            )
        record["files"] = await self._rewrite(record["ids"], reload)
        await _clean_recorder(hass, [temp_id])
        self.history.append(record)
        self._save()
        return {"id": record["id"], "moved": 1, "changed": record["files"]}

    async def async_undo(self, record_id: str, reload: bool = True) -> bool:
        """Give the new device its own names and entity ids back. The old device returns only if its integration
        finds it again; the history recorded since stays with the old entity ids."""
        record = next((r for r in self.history if r["id"] == record_id and not r["undone"]), None)
        if record is None:
            return False
        devices, entities = dr.async_get(self.hass), er.async_get(self.hass)
        for item in record["entities"]:
            entry = entities.async_get(item["uuid"])
            if entry is None:
                continue
            new_id = item["was"] if not entities.async_get(item["was"]) else entry.entity_id
            entities.async_update_entity(entry.entity_id, new_entity_id=new_id, **_restore(item))
            for domain in set(entry.options) | set(item["options"]):
                entities.async_update_entity_options(new_id, domain, item["options"].get(domain, {}))
        device = record["new_device"]
        if device.get("id") and devices.async_get(device["id"]):
            devices.async_update_device(
                device["id"],
                name_by_user=device["name_by_user"],
                area_id=device["area_id"],
                labels=set(device["labels"]),
            )
        # Translated triggers go back only if nobody edited the automations since.
        path = self.hass.config.path(AUTOMATIONS_FILE)
        if record.get("automations_before") is not None:
            if await self.hass.async_add_executor_job(_read, path) == record["automations_after"]:
                await self.hass.async_add_executor_job(write_utf8_file_atomic, path, record["automations_before"])
            else:
                _LOGGER.warning("Automations were edited since; translated device triggers were not changed back")
        back = {new: old for old, new in record["ids"].items()}
        await self._rewrite(back, reload=reload)
        await references.async_rewrite_dashboards(self.hass, back)
        await references.async_rewrite_entries(self.hass, back, set())
        record["undone"] = True
        self._save()
        return True

    async def async_undo_batch(self, batch: str) -> int:
        """Undo every replacement of one "move many", newest first; reload once."""
        records = [r for r in reversed(self.history) if r.get("batch") == batch and not r["undone"]]
        for record in records:
            await self.async_undo(record["id"], reload=False)
        await self.async_reload({"automation", "script", "scene"})
        return len(records)

    async def async_fill_with_ai(self, plan: Plan) -> list[str]:
        """Ask the AI about old entities that found no match, when the new device has unused ones of the same kind."""
        if not self.ai_entity:
            return []
        key = (plan.old.id, plan.new.id)
        if key not in self._ai_cache:
            taken = {v for v in plan.mapping.values() if v}
            old = [o for o in plan.old_entities if not plan.mapping.get(o.entity_id)]
            new = [n for n in plan.new_entities if n.entity_id not in taken and any(n.domain == o.domain for o in old)]
            picks = (
                await ai.async_pick_entities(
                    self.hass, self.ai_entity, [_describe(e) for e in old], [_describe(e) for e in new]
                )
                if old and new
                else {}
            )
            self._ai_cache[key] = {
                old[i].entity_id: new[j].entity_id for i, j in picks.items() if old[i].domain == new[j].domain
            }
        filled = []
        taken = {v for v in plan.mapping.values() if v}
        for old_id, new_id in self._ai_cache[key].items():
            if not plan.mapping.get(old_id) and new_id not in taken:
                plan.mapping[old_id] = new_id
                taken.add(new_id)
                filled.append(old_id)
        return filled

    def _save(self) -> None:
        self.store.async_delay_save(lambda: {"history": self.history}, 1)

    async def async_reload(self, domains: set[str]) -> None:
        """Reload what was changed. A broken file must not stop the replacement; HA tells the user about it."""
        for domain in sorted(domains):
            if not self.hass.services.has_service(domain, "reload"):
                continue
            try:
                await self.hass.services.async_call(domain, "reload", blocking=True)
            except Exception:  # noqa: BLE001 - e.g. a YAML error the user made elsewhere
                _LOGGER.warning("Could not reload %s after the replacement", domain, exc_info=True)

    async def _rewrite(self, ids: dict[str, str], reload: bool = True) -> list[str]:
        """Replace device and entity registry ids in the automation, script, scene and package files, then reload."""
        changed: set[str] = set()
        for domains, path in await self.hass.async_add_executor_job(_config_files, self.hass.config.path()):
            text = await self.hass.async_add_executor_job(_read, path)
            if text is None:
                continue
            new = text
            for old_id, new_id in ids.items():
                new = new.replace(old_id, new_id)
            if new == text:
                continue
            await self.hass.async_add_executor_job(write_utf8_file_atomic, path, new)
            changed.update(domains)
        if reload:
            await self.async_reload(changed)
        return sorted(changed)


def _settings(entry: er.RegistryEntry) -> dict[str, Any]:
    """What a user can set on an entity, as JSON. A computed name among the aliases is kept as None."""
    return {
        "name": entry.name,
        "icon": entry.icon,
        "area_id": entry.area_id,
        "labels": sorted(entry.labels),
        "aliases": [a if isinstance(a, str) else None for a in entry.aliases],
        "categories": dict(entry.categories),
        "device_class": entry.device_class,
        "hidden_by": entry.hidden_by,
        "options": {domain: dict(options) for domain, options in entry.options.items()},
    }


def _update(entry: er.RegistryEntry) -> dict[str, Any]:
    return {
        "name": entry.name,
        "icon": entry.icon,
        "area_id": entry.area_id,
        "labels": set(entry.labels),
        "aliases": list(entry.aliases),
        "categories": dict(entry.categories),
        "device_class": entry.device_class,
        "hidden_by": entry.hidden_by if entry.hidden_by == er.RegistryEntryHider.USER else None,
    }


def _restore(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "name": item["name"],
        "icon": item["icon"],
        "area_id": item["area_id"],
        "labels": set(item["labels"]),
        "aliases": [er.COMPUTED_NAME if a is None else a for a in item["aliases"]],
        "categories": item["categories"],
        "device_class": item["device_class"],
        "hidden_by": er.RegistryEntryHider(item["hidden_by"]) if item["hidden_by"] else None,
    }


async def _rename_in_z2m(hass: HomeAssistant, device: dr.DeviceEntry, name: str) -> bool:
    """Give the device the same name in Zigbee2MQTT, without letting it change the Home Assistant entity ids."""
    ieee = z2m_ieee(device)
    if ieee is None or not hass.services.has_service("mqtt", "publish"):
        return False
    payload = json.dumps({"from": ieee, "to": z2m_name(name), "homeassistant_rename": False})
    await hass.services.async_call(
        "mqtt", "publish", {"topic": f"{Z2M_BASE_TOPIC}/bridge/request/device/rename", "payload": payload}
    )
    return True


def _describe(entry: er.RegistryEntry) -> str:
    parts = [
        entry.entity_id,
        entry.original_name,
        entry.device_class or entry.original_device_class,
        entry.unit_of_measurement,
    ]
    return " | ".join(str(p) for p in parts if p)


def _domain(hass: HomeAssistant, device: dr.DeviceEntry) -> str | None:
    entry = hass.config_entries.async_get_entry(device.config_entry_id) if device.config_entry_id else None
    return entry.domain if entry else None


def _config_files(config_dir: str) -> list[tuple[tuple[str, ...], str]]:
    """The files the editors write, and every YAML file in packages/ (which can hold all three)."""
    files: list[tuple[tuple[str, ...], str]] = [
        (("automation",), os.path.join(config_dir, AUTOMATIONS_FILE)),
        (("script",), os.path.join(config_dir, SCRIPTS_FILE)),
        (("scene",), os.path.join(config_dir, SCENES_FILE)),
    ]
    packages = os.path.join(config_dir, "packages")
    for root, _dirs, names in os.walk(packages):
        files += [
            (("automation", "script", "scene"), os.path.join(root, n))
            for n in sorted(names)
            if n.endswith((".yaml", ".yml"))
        ]
    return files


async def _safely[T](what: str, job: Awaitable[T], default: T) -> T:
    """Run a step after the core replacement; if it fails, log it and carry on with the rest."""
    try:
        return await job
    except Exception:  # noqa: BLE001 - one broken dashboard or file must not stop the replacement
        _LOGGER.warning("Replace Device: %s failed", what, exc_info=True)
        return default


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
    """Ten minutes later: if none of the new entities has a value, say so – until one has."""
    name = device_name(plan.old)
    issue_id = f"silent_{plan.new.id}"
    unsubs: list[CALLBACK_TYPE] = []

    @callback
    def _stop() -> None:
        while unsubs:
            unsubs.pop()()

    @callback
    def _reported(event: Event[EventStateChangedData]) -> None:
        state = event.data["new_state"]
        if state is not None and state.state not in (STATE_UNAVAILABLE, STATE_UNKNOWN):
            ir.async_delete_issue(hass, DOMAIN, issue_id)
            _stop()

    async def _check(_now) -> None:
        if not entity_ids or any(
            (s := hass.states.get(e)) is not None and s.state not in (STATE_UNAVAILABLE, STATE_UNKNOWN)
            for e in entity_ids
        ):
            return
        ir.async_create_issue(
            hass,
            DOMAIN,
            issue_id,
            is_fixable=False,
            severity=ir.IssueSeverity.WARNING,
            translation_key="silent",
            translation_placeholders={"name": name},
        )
        unsubs.append(async_track_state_change_event(hass, entity_ids, _reported))

    unsubs.append(async_call_later(hass, CHECK_AFTER, _check))
    return _stop
