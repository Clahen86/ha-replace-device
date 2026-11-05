"""The replacement: the new device takes over the old one's names, entity ids, area, settings and history.

History and long-term statistics follow by themselves, because the recorder keeps them by entity_id: when the new
entity gets the old entity_id, it simply continues the old series. Energy sums continue too; a new meter starting
at 0 is seen as a reset.
"""

from __future__ import annotations

import asyncio
from dataclasses import asdict, dataclass, field
import json
import logging
import os
import time
from collections.abc import Awaitable
from typing import Any
from uuid import uuid4

from homeassistant import loader
from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import STATE_UNAVAILABLE, STATE_UNKNOWN
from homeassistant.core import CALLBACK_TYPE, Event, EventStateChangedData, HomeAssistant, callback
from homeassistant.helpers import (
    area_registry as ar,
    device_registry as dr,
    entity_registry as er,
    issue_registry as ir,
)
from homeassistant.helpers.event import async_call_later, async_track_state_change_event
from homeassistant.helpers.storage import Store
from homeassistant.util.file import write_utf8_file_atomic
from homeassistant.util.yaml import parse_yaml

from . import ai, references, rename, tidy, triggers
from .const import AUTOMATIONS_FILE, CHECK_AFTER, DOMAIN, SCENES_FILE, SCRIPTS_FILE, TEXTS, Z2M_BASE_TOPIC
from .hardware import z2m_base_topic, z2m_ieee, z2m_name
from .matching import match, unsure
from .remembered import remembered

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
    # Old entities whose match was a close call: shown with "check", and asked to the AI if there is one.
    unsure: list[str] = field(default_factory=list)

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
    # A device that lost its entities (reset or unpaired first): use the ones Home Assistant still remembers.
    if not old_entities:
        old_entities = remembered(hass, old)
    new_entities = er.async_entries_for_device(entities, new_id, include_disabled_entities=True)
    plan = Plan(
        old, new, old_entities, new_entities, mapping if mapping is not None else match(old_entities, new_entities)
    )
    plan.uses_device = _users_of_device(hass, old_id)
    plan.unsure = unsure(old_entities, new_entities, plan.mapping) if mapping is None else []
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
        # The AI's answers for button triggers, so "Test first" and the replacement ask only once.
        self._trigger_cache: dict[tuple, dict[int, int]] = {}
        # Why the AI couldn't answer the last time it was asked ("quota", …), None when it did.
        self.ai_error: str | None = None
        # Devices the user said are only switched off, not gone.
        self.hidden: list[str] = []

    @callback
    def async_stop(self) -> None:
        for cancel in self._timers:
            cancel()

    async def async_load(self) -> None:
        cutoff = time.time() - _KEEP_DAYS * 86400
        data = await self.store.async_load() or {}
        self.history = [h for h in data.get("history", []) if h["at"] >= cutoff]
        self.hidden = data.get("hidden", [])

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
            "id": uuid4().hex,
            "at": now,
            "old_device": {
                "id": plan.old.id,
                "name": device_name(plan.old),
                "model": plan.old.model,
                "area_id": plan.old.area_id,
                "labels": sorted(plan.old.labels),
            },
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
                {"entity_id": o.entity_id, "was": n.entity_id, "uuid": n.id, **_settings(n), "old": _settings(o)}
                for o, n in pairs
            ],
            "ids": {plan.old.id: plan.new.id} | {o.id: n.id for o, n in pairs},
            "files": [],
            "batch": batch,
            "undone": False,
        }
        old_domain, new_domain = _domain(hass, plan.old), _domain(hass, plan.new)
        # What listens to the old device (ZHA events, Zigbee2MQTT topics), read before the old device is removed.
        moved = _moved(hass, plan, rename_z2m)
        old_ids = [o.entity_id for o, _ in pairs]
        temp_ids = [n.entity_id for _, n in pairs]

        # 1. The old ones make room. Removing the device from its integration removes all its entities.
        removed = await _remove_device(hass, plan.old) if remove_old else False
        for entity_id in old_ids:
            if entities.async_get(entity_id):
                entities.async_remove(entity_id)
        await _wait_until_gone(hass, old_ids)
        # The old device stays (its integration won't let go, or it was kept): a name that says so. Entities its
        # integration makes again are then named after it, instead of taking "_2" of the names that moved.
        if (old_device := devices.async_get(plan.old.id)) is not None:
            record["old_marked"] = {"name_by_user": old_device.name_by_user}
            devices.async_update_device(old_device.id, name_by_user=_old_name(hass, device_name(plan.old)))

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
        paths = {d: hass.config.path(f) for d, f in (("automation", AUTOMATIONS_FILE), ("script", SCRIPTS_FILE))}
        before = {d: await hass.async_add_executor_job(_read, p) for d, p in paths.items()}
        translation = await _safely(
            "translating device triggers",
            triggers.async_translate(hass, moved, self.ai_entity, cache=self._trigger_cache),
            {"translated": [], "unresolved": [], "saved": []},
        )
        if saved := translation.get("saved"):
            record["triggers_before"] = {d: before[d] for d in saved}
            record["triggers_after"] = {d: await hass.async_add_executor_job(_read, paths[d]) for d in saved}
            changed = sorted(set(changed) | set(saved))
        record["triggers"] = translation
        record["moved"] = asdict(moved)
        record["files"] = changed
        # Dashboards made in the UI and other integrations (Battery Notes, Powercalc …) that store the device id.
        skip = {d for d in (old_domain, new_domain) if d}
        record["dashboards"] = await _safely(
            "updating dashboards", references.async_rewrite_dashboards(hass, record["ids"]), []
        )
        # Other integrations' settings and hand-written packages are only listed: the user changes them.
        record["integrations"] = [e.title for e in references.entries_using(hass, record["ids"], skip)]
        record["packages"] = await hass.async_add_executor_job(_packages_using, hass.config.path(), record["ids"])
        # The entities only the new device has get ids after the device's name, like the others.
        own = [entities.async_get(n.entity_id) for n in plan.new_entities if n.entity_id not in set(temp_ids)]
        record["tidied"], tidied_files = await _safely(
            "naming the new entities", self._async_tidy([e for e in own if e], device_name(plan.old)), ([], [])
        )
        changed = sorted(set(changed) | set(tidied_files))
        if reload:
            await self.async_reload(set(changed))
        renamed = False
        if rename_z2m:
            renamed = await _safely(
                "renaming in Zigbee2MQTT", _rename_in_z2m(hass, plan.new, device_name(plan.old)), False
            )

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

    async def async_dry_run(self, plan: Plan, remove_old: bool, rename_z2m: bool = False) -> dict[str, Any]:
        """Everything a replacement would do, worked out without changing anything."""
        hass = self.hass
        pairs = plan.pairs
        ids = {plan.old.id: plan.new.id} | {o.id: n.id for o, n in pairs}
        old_domain, new_domain = _domain(hass, plan.old), _domain(hass, plan.new)
        moved = _moved(hass, plan, rename_z2m)
        users = await hass.async_add_executor_job(_users_of_ids, hass.config.path(), ids)
        translation = await _safely(
            "trying device triggers",
            triggers.async_translate(hass, moved, self.ai_entity, ids=ids, cache=self._trigger_cache),
            {"translated": [], "unresolved": []},
        )
        dashboards = await _safely("reading dashboards", references.async_dashboards(hass), [])
        skip = {d for d in (old_domain, new_domain) if d}
        used = {n.entity_id for _, n in pairs}
        area = plan.old.area_id or plan.new.area_id
        area_entry = ar.async_get(hass).async_get_area(area) if area else None
        def nice(entry: Any) -> str:
            state = hass.states.get(entry.entity_id)
            return entry.name or (state and state.attributes.get("friendly_name")) or entry.original_name or ""

        dropped = [o for o in plan.old_entities if not plan.mapping.get(o.entity_id)]
        own_entries = [er.async_get(hass).async_get(n.entity_id) for n in plan.new_entities if n.entity_id not in used]
        # Ids the old ones free up count as free here, since the replacement removes those first.
        freed = {o.entity_id for o in dropped} if remove_old else set()
        renamed = {
            c["from"]: c["to"]
            for c in tidy.plan(hass, device_name(plan.old), [e for e in own_entries if e], free=freed)
        }
        return {
            "entities": [
                {
                    "from": n.entity_id,
                    "to": o.entity_id,
                    "name": nice(o),
                    "used_in": references.used_in(hass, o.entity_id, dashboards),
                }
                for o, n in pairs
            ],
            "dropped": [o.entity_id for o in dropped],
            "dropped_info": [
                {
                    "entity_id": o.entity_id,
                    "name": nice(o),
                    "used_in": references.used_in(hass, o.entity_id, dashboards),
                }
                for o in dropped
            ],
            "own": [n.entity_id for n in plan.new_entities if n.entity_id not in used],
            "own_info": [
                {"entity_id": n.entity_id, "name": nice(n), "to": renamed.get(n.entity_id)}
                for n in plan.new_entities
                if n.entity_id not in used
            ],
            "device": {
                "from": device_name(plan.new),
                "to": device_name(plan.old),
                "area": area_entry and area_entry.name,
            },
            "remove_old": remove_old,
            # What the old device will be called if it stays.
            "old_name": None if remove_old and _can_remove(hass, plan.old) else _old_name(hass, device_name(plan.old)),
            "z2m_name": moved.new_z2m_name if rename_z2m and moved.new_z2m_name != plan.new.name else None,
            "users": users,
            "triggers": translation,
            "dashboards": [title for title, _, config in dashboards if references.swap(config, ids) is not config],
            "integrations": [entry.title for entry in references.entries_using(hass, ids, skip)],
            "packages": await hass.async_add_executor_job(_packages_using, hass.config.path(), ids),
        }

    async def async_replace_entity(
        self, name: str, old: er.RegistryEntry, new: er.RegistryEntry, batch: str | None = None, reload: bool = True
    ) -> dict[str, Any]:
        """One entity without a device of its own takes over another, e.g. a Zigbee group made again elsewhere."""
        hass, entities = self.hass, er.async_get(self.hass)
        now = time.time()
        record: dict[str, Any] = {
            "id": uuid4().hex,
            "at": now,
            "old_device": {"id": None, "name": name, "model": "Group"},
            "new_device": {"id": None, "name": new.entity_id, "model": "Group"},
            "entities": [
                {
                    "entity_id": old.entity_id,
                    "was": new.entity_id,
                    "uuid": new.id,
                    **_settings(new),
                    "old": _settings(old),
                }
            ],
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
        self.history.append(record)
        self._save()
        return {"id": record["id"], "moved": 1, "changed": record["files"]}

    async def async_undo(self, record_id: str, reload: bool = True) -> bool:
        """Give the new device its own names and entity ids back. The old device returns only if its integration
        finds it again; the history recorded since stays with the old entity ids."""
        record = next((r for r in self.history if r["id"] == record_id and not r["undone"]), None)
        if record is None:
            return False
        if record.get("kind") == "rename":
            return await self._async_undo_rename(record)
        devices, entities = dr.async_get(self.hass), er.async_get(self.hass)
        # Ids given after the device's name go back first.
        back = tidy.apply(self.hass, [{"from": c["to"], "to": c["from"]} for c in reversed(record.get("tidied") or [])])
        if back:
            await self._async_places({c["from"]: c["to"] for c in back}, apply=True)
            record["tidied"] = []
        for item in record["entities"]:
            entry = entities.async_get(item["uuid"])
            if entry is None:
                continue
            # What the entity has now (the old one's settings, and any changes since), so "do again" gives it back.
            item["old"] = _settings(entry)
            new_id = item["was"] if not entities.async_get(item["was"]) else entry.entity_id
            entities.async_update_entity(entry.entity_id, new_entity_id=new_id, **_restore(item))
            for domain in set(entry.options) | set(item["options"]):
                entities.async_update_entity_options(new_id, domain, item["options"].get(domain, {}))
        if (marked := record.get("old_marked")) and (old := devices.async_get(record["old_device"].get("id") or "")):
            devices.async_update_device(old.id, name_by_user=marked.get("name_by_user"))
        device = record["new_device"]
        if device.get("id") and (current := devices.async_get(device["id"])):
            record["old_device"]["area_id"] = current.area_id
            record["old_device"]["labels"] = sorted(current.labels)
            devices.async_update_device(
                device["id"],
                name_by_user=device["name_by_user"],
                area_id=device["area_id"],
                labels=set(device["labels"]),
            )
        # Translated triggers go back only if nobody edited the automations since.
        befores = dict(record.get("triggers_before") or {})
        afters = dict(record.get("triggers_after") or {})
        if record.get("automations_before") is not None:  # made by 0.15.0 and older
            befores["automation"], afters["automation"] = record["automations_before"], record["automations_after"]
        files = {"automation": AUTOMATIONS_FILE, "script": SCRIPTS_FILE}
        for domain, text in befores.items():
            path = self.hass.config.path(files[domain])
            if await self.hass.async_add_executor_job(_read, path) == afters.get(domain):
                await self.hass.async_add_executor_job(write_utf8_file_atomic, path, text)
            else:
                _LOGGER.warning("%s was edited since; translated device triggers were not changed back", files[domain])
        back = {new: old for old, new in record["ids"].items()}
        await self._rewrite(back, reload=reload)
        await references.async_rewrite_dashboards(self.hass, back)
        record["undone"] = True
        self._save()
        return True

    def edit_plan(self, record_id: str) -> dict[str, Any] | None:
        """The names a replacement moved, which of the new device's entities has each one now, and the choices."""
        record = next((r for r in self.history if r["id"] == record_id and not r["undone"]), None)
        device_id = record and record["new_device"].get("id")
        if record is None or not device_id:
            return None
        hass, entities = self.hass, er.async_get(self.hass)
        slots = []
        for item in record["entities"]:
            holder = entities.async_get(item["entity_id"])
            state = hass.states.get(item["entity_id"])
            name = (state and state.attributes.get("friendly_name")) or (item.get("old") or {}).get("name")
            slots.append(
                {
                    "entity_id": item["entity_id"],
                    "name": name or item["entity_id"],
                    "holder": holder.id if holder and holder.device_id == device_id else None,
                }
            )
        choices = []
        for entry in er.async_entries_for_device(entities, device_id, include_disabled_entities=True):
            state = hass.states.get(entry.entity_id)
            choices.append(
                {
                    "uuid": entry.id,
                    "entity_id": entry.entity_id,
                    "domain": entry.domain,
                    "name": entry.original_name or entry.name or entry.entity_id,
                    "state": state.state if state else None,
                    "unit": entry.unit_of_measurement,
                }
            )
        return {
            "id": record_id,
            "device_id": device_id,
            "old_name": record["old_device"]["name"],
            "slots": slots,
            "choices": choices,
        }

    async def async_edit(self, record_id: str, mapping: dict[str, str | None]) -> bool:
        """Change which of the new device's entities carries each moved name (e.g. temperature and battery mixed up).

        Only names change; the device stays where it is. An entity that loses its name gets its own one back."""
        record = next((r for r in self.history if r["id"] == record_id and not r["undone"]), None)
        if record is None or not record["new_device"].get("id"):
            return False
        entities = er.async_get(self.hass)
        items = {item["entity_id"]: item for item in record["entities"]}
        current = {slot: getattr(entities.async_get(slot), "id", None) for slot in items}
        wanted = current | {slot: uuid for slot, uuid in mapping.items() if slot in items}
        picked = [uuid for uuid in wanted.values() if uuid]
        if len(picked) != len(set(picked)) or any(entities.async_get(uuid) is None for uuid in picked):
            return False
        changes = {slot: uuid for slot, uuid in wanted.items() if uuid != current[slot]}
        if not changes:
            return True

        # What each name carries now (the old device's settings and changes since), and each entity's own id/settings.
        carried = {
            slot: _settings(entities.async_get(slot)) if current[slot] else items[slot].get("old") for slot in changes
        }
        own: dict[str, dict[str, Any]] = {}
        for uuid in {current[slot] for slot in changes} | set(changes.values()):
            if not uuid:
                continue
            item = next((i for i in record["entities"] if i["uuid"] == uuid), None)
            entry = entities.async_get(uuid)
            own[uuid] = (
                {k: item[k] for k in (*_SETTINGS, "was")} if item else _settings(entry) | {"was": entry.entity_id}
            )

        # 1. Entities that lose a name get their own id and settings back, so the names are free.
        for slot in changes:
            if (uuid := current[slot]) is None:
                continue
            entry = entities.async_get(uuid)
            target = own[uuid]["was"]
            if entities.async_get(target):
                target = entities.async_generate_entity_id(entry.domain, target.split(".", 1)[1])
            entities.async_update_entity(entry.entity_id, new_entity_id=target, **_restore(own[uuid]))

        # 2. The chosen entities take the names, with everything the name carried.
        for slot, uuid in changes.items():
            item = items[slot]
            if uuid is None:
                record["entities"].remove(item)
                continue
            entry = entities.async_get(uuid)
            settings = carried[slot] or _EMPTY_SETTINGS
            entities.async_update_entity(entry.entity_id, new_entity_id=slot, **_restore(settings))
            for domain, options in settings["options"].items():
                entities.async_update_entity_options(slot, domain, dict(entry.options.get(domain, {})) | dict(options))
            item.update(own[uuid], uuid=uuid, old=settings)
        self._save()
        return True

    async def async_retranslate(self, record_id: str) -> dict[str, list[str]] | None:
        """Translate button triggers again that still point at the old integration (e.g. after an older version)."""
        record = next((r for r in self.history if r["id"] == record_id and not r["undone"]), None)
        if record is None or not record.get("moved"):
            return None
        moved = triggers.Moved(**record["moved"])
        if (device := dr.async_get(self.hass).async_get(moved.new_device_id)) is not None:
            moved.new_z2m_ieee = moved.new_z2m_ieee or z2m_ieee(device)
            moved.new_base = moved.new_base or (
                z2m_base_topic(self.hass, device, Z2M_BASE_TOPIC) if z2m_ieee(device) else None
            )
        translation = await triggers.async_translate(self.hass, moved, self.ai_entity, cache=self._trigger_cache)
        if translation.get("saved"):
            await self.async_reload(set(translation["saved"]))
        record["triggers"] = translation
        self._save()
        return translation

    async def async_redo(self, record_id: str, reload: bool = True) -> bool:
        """Do an undone replacement again: the new entities take the old ids back, also when the old device is gone."""
        record = next((r for r in self.history if r["id"] == record_id and r["undone"]), None)
        if record is None:
            return False
        hass = self.hass
        devices, entities = dr.async_get(hass), er.async_get(hass)
        for item in record["entities"]:
            entry = entities.async_get(item["uuid"])
            if entry is None or entities.async_get(item["entity_id"]):
                continue
            hass.states.async_remove(item["entity_id"])
            old = item.get("old") or _EMPTY_SETTINGS
            entities.async_update_entity(entry.entity_id, new_entity_id=item["entity_id"], **_restore(old))
            for domain, options in old["options"].items():
                entities.async_update_entity_options(
                    item["entity_id"], domain, dict(entry.options.get(domain, {})) | dict(options)
                )
        device, old_device = record["new_device"], record["old_device"]
        if device.get("id") and (current := devices.async_get(device["id"])):
            devices.async_update_device(
                device["id"],
                name_by_user=old_device["name"],
                area_id=old_device.get("area_id") or current.area_id,
                labels=set(old_device.get("labels", [])) | set(current.labels),
            )
        changed = set(await _safely("updating automations and scripts", self._rewrite(record["ids"], False), []))
        if record.get("moved"):
            translation = await _safely(
                "translating device triggers",
                triggers.async_translate(
                    hass, triggers.Moved(**record["moved"]), self.ai_entity, cache=self._trigger_cache
                ),
                {"translated": [], "unresolved": [], "saved": []},
            )
            changed |= set(translation.get("saved") or [])
        await _safely("updating dashboards", references.async_rewrite_dashboards(hass, record["ids"]), [])
        if reload:
            await self.async_reload(changed)
        record["undone"] = False
        self._save()
        return True

    async def async_redo_batch(self, batch: str) -> int:
        records = [r for r in self.history if r.get("batch") == batch and r["undone"]]
        for record in records:
            await self.async_redo(record["id"], reload=False)
        await self.async_reload({"automation", "script", "scene"})
        return len(records)

    async def async_undo_batch(self, batch: str) -> int:
        """Undo every replacement of one "move many", newest first; reload once."""
        records = [r for r in reversed(self.history) if r.get("batch") == batch and not r["undone"]]
        for record in records:
            await self.async_undo(record["id"], reload=False)
        await self.async_reload({"automation", "script", "scene"})
        return len(records)

    def _question(self, plan: Plan) -> tuple[ai.Question, list, list] | None:
        """What to ask the AI about one device: old entities without a (sure) match, new ones still free."""
        doubtful = set(plan.unsure)
        taken = {v for k, v in plan.mapping.items() if v and k not in doubtful}
        old = [o for o in plan.old_entities if not plan.mapping.get(o.entity_id) or o.entity_id in doubtful]
        new = [n for n in plan.new_entities if n.entity_id not in taken and any(n.domain == o.domain for o in old)]
        if not old or not new:
            return None
        question = ai.Question(_context(self.hass, plan), [_describe(e) for e in old], [_describe(e) for e in new])
        return question, old, new

    async def async_fill_many(self, plans: list[Plan]) -> None:
        """Ask the AI about every device not asked before, in one call. A failure is kept in ai_error."""
        if not self.ai_entity:
            return
        todo = []
        for plan in plans:
            key = (plan.old.id, plan.new.id)
            if key in self._ai_cache:
                continue
            if (asked := self._question(plan)) is None:
                self._ai_cache[key] = {}
                continue
            todo.append((key, *asked))
        if not todo:
            return
        try:
            await ai.async_ask_many(self.hass, self.ai_entity, "entities", [question for _, question, _, _ in todo])
        except ai.AiError as err:
            # Not remembered, so it is tried again next time (e.g. when the quota is back).
            self.ai_error = str(err)
            return
        self.ai_error = None
        for key, question, old, new in todo:
            self._ai_cache[key] = {
                old[i].entity_id: new[j].entity_id for i, j in question.answer.items() if old[i].domain == new[j].domain
            }

    async def async_fill_with_ai(self, plan: Plan) -> list[str]:
        """Use the AI's answer for a plan's gaps and close calls; returns the old entities it filled."""
        if not self.ai_entity:
            return []
        await self.async_fill_many([plan])
        answer = self._ai_cache.get((plan.old.id, plan.new.id))
        if answer is None:
            return []
        filled = []
        # The AI's answer for a close call wins; whatever it gives up becomes free for others.
        for old_id in plan.unsure:
            if old_id in answer:
                plan.mapping[old_id] = None
        taken = {v for v in plan.mapping.values() if v}
        for old_id, new_id in answer.items():
            if not plan.mapping.get(old_id) and new_id not in taken:
                plan.mapping[old_id] = new_id
                taken.add(new_id)
                filled.append(old_id)
        plan.unsure = [u for u in plan.unsure if u not in filled]
        return filled

    @callback
    def set_done(self, record_id: str, done: bool) -> bool:
        record = next((r for r in self.history if r["id"] == record_id), None)
        if record is None:
            return False
        record["done"] = done
        self._save()
        return True

    @callback
    def set_hidden(self, device_id: str, hidden: bool) -> None:
        self.hidden = [d for d in self.hidden if d != device_id] + ([device_id] if hidden else [])
        self._save()

    def _save(self) -> None:
        self.store.async_delay_save(lambda: {"history": self.history, "hidden": self.hidden}, 1)

    async def async_reload(self, domains: set[str]) -> None:
        """Reload what was changed. A broken file must not stop the replacement; HA tells the user about it."""
        for domain in sorted(domains):
            if not self.hass.services.has_service(domain, "reload"):
                continue
            try:
                await self.hass.services.async_call(domain, "reload", blocking=True)
            except Exception:  # noqa: BLE001 - e.g. a YAML error the user made elsewhere
                _LOGGER.warning("Could not reload %s after the replacement", domain, exc_info=True)

    # ---------- renaming a device ----------

    async def _async_places(self, ids: dict[str, str], apply: bool) -> dict[str, Any]:
        """Everywhere Home Assistant uses the entity ids; with apply, they are changed there."""
        hass = self.hass
        config_dir = hass.config.path()
        handled = {path for _, path in await hass.async_add_executor_job(_config_files, config_dir)}
        files = await hass.async_add_executor_job(
            rename.yaml_files, config_dir, handled, references.yaml_dashboard_files(hass)
        )
        yaml_changes = await hass.async_add_executor_job(rename.files_using, config_dir, files, ids)
        dashboards = await _safely("reading dashboards", references.async_dashboards(hass), [])
        entries = [
            e
            for e in references.entries_using(hass, ids, set())
            if references.swap([dict(e.data), dict(e.options)], ids, True) != [dict(e.data), dict(e.options)]
        ]
        result: dict[str, Any] = {
            "users": await hass.async_add_executor_job(_users_of_ids, config_dir, ids),
            "yaml": sorted(
                {os.path.relpath(p, config_dir) for p, kind, _ in yaml_changes if kind == "config"}
                | set(await hass.async_add_executor_job(_packages_using, config_dir, ids))
            ),
            "esphome": [os.path.relpath(p, config_dir) for p, kind, _ in yaml_changes if kind == "esphome"],
            "dashboards": [t for t, _, c in dashboards if references.swap(c, ids, True) is not c],
            "integrations": [e.title for e in entries],
            "energy": await _safely("reading the energy dashboard", references.async_energy_uses(hass, ids), False),
            "outside": await hass.async_add_executor_job(references.outside_users, config_dir, list(ids)),
        }
        if not apply:
            return result
        # Hand-written YAML (configuration.yaml, packages, ESPHome) and other integrations' settings are only
        # listed in "yaml", "esphome" and "integrations": the user changes them.
        changed = set(await self._rewrite(ids, reload=False, exact=True))
        await _safely("updating dashboards", references.async_rewrite_dashboards(hass, ids, exact=True), [])
        await _safely("updating the energy dashboard", references.async_rewrite_energy(hass, ids), False)
        await self.async_reload(changed)
        result["changed"] = sorted(changed)
        return result

    def _rename_plan(self, device_id: str, name: str) -> tuple[Any, list[dict[str, str]]]:
        device = dr.async_get(self.hass).async_get(device_id)
        if device is None or not name.strip():
            return None, []
        entries = er.async_entries_for_device(er.async_get(self.hass), device.id, include_disabled_entities=True)
        return device, rename.plan_ids(self.hass, entries, device_name(device), name.strip())

    async def async_rename_dry_run(self, device_id: str, name: str) -> dict[str, Any] | None:
        """What renaming a device would change, without changing anything."""
        device, changes = self._rename_plan(device_id, name)
        if device is None:
            return None
        places = await self._async_places({c["from"]: c["to"] for c in changes}, apply=False)
        return {
            "device": {"from": device_name(device), "to": name.strip()},
            "entities": changes,
            "z2m": z2m_ieee(device) is not None,
            **places,
        }

    async def async_rename(self, device_id: str, name: str) -> dict[str, Any] | None:
        """Rename a device, its entity ids, and everything that uses them. It can be undone."""
        hass = self.hass
        device, changes = self._rename_plan(device_id, name)
        if device is None:
            return None
        name = name.strip()
        old_name, before = device_name(device), device.name_by_user
        dr.async_get(hass).async_update_device(device.id, name_by_user=name)
        done = _rename_all(hass, changes)
        record: dict[str, Any] = {
            "id": uuid4().hex,
            "at": time.time(),
            "kind": "rename",
            "old_device": {"id": device.id, "name": old_name, "model": device.model},
            "new_device": {"id": device.id, "name": name, "model": device.model, "name_by_user": before},
            "entities": [],
            "ids": {},
            "renamed": done,
            "files": [],
            "batch": None,
            "undone": False,
        }
        self.history.append(record)
        self._save()
        places = await self._async_places({c["from"]: c["to"] for c in done}, apply=True)
        record["files"] = places.get("changed", [])
        if z2m_ieee(device):
            await _safely("renaming in Zigbee2MQTT", _rename_in_z2m(hass, device, name), False)
        self._save()
        return {"id": record["id"], "entities": done, **places}

    async def _async_undo_rename(self, record: dict[str, Any]) -> bool:
        hass = self.hass
        device = dr.async_get(hass).async_get(record["new_device"]["id"])
        back = _rename_all(hass, [{"from": c["to"], "to": c["from"]} for c in reversed(record.get("renamed") or [])])
        if device is not None:
            dr.async_get(hass).async_update_device(device.id, name_by_user=record["new_device"].get("name_by_user"))
            if z2m_ieee(device):
                old_name = record["old_device"]["name"]
                await _safely("renaming in Zigbee2MQTT", _rename_in_z2m(hass, device, old_name), False)
        await self._async_places({c["from"]: c["to"] for c in back}, apply=True)
        record["undone"] = True
        self._save()
        return True

    async def _async_tidy(self, entries: list[Any], name: str) -> tuple[list[dict[str, str]], list[str]]:
        """Give entries ids after the device's name and fix what uses the old ids; (renamed, changed file domains)."""
        done = tidy.apply(self.hass, tidy.plan(self.hass, name, entries))
        if not done:
            return [], []
        # The same places as renaming a device: files, YAML templates, dashboards, helpers, the energy dashboard.
        places = await self._async_places({c["from"]: c["to"] for c in done}, apply=True)
        return done, places.get("changed", [])

    def _own_entries(self, record: dict[str, Any]) -> tuple[list[Any], str]:
        """The new device's entities that did not take over an old one, and the device's name now."""
        device = dr.async_get(self.hass).async_get(record["new_device"].get("id") or "")
        if device is None:
            return [], ""
        taken = {item["uuid"] for item in record["entities"]}
        entries = [e for e in er.async_entries_for_device(er.async_get(self.hass), device.id) if e.id not in taken]
        return entries, device_name(device)

    def tidy_plan(self, record_id: str) -> list[dict[str, Any]] | None:
        record = next((r for r in self.history if r["id"] == record_id and not r["undone"]), None)
        if record is None:
            return None
        entries, name = self._own_entries(record)
        return tidy.plan(self.hass, name, entries) if name else []

    async def async_tidy_record(self, record_id: str) -> list[dict[str, str]] | None:
        """Tidy the ids of a replacement made before (or of entities that came later)."""
        record = next((r for r in self.history if r["id"] == record_id and not r["undone"]), None)
        if record is None:
            return None
        entries, name = self._own_entries(record)
        done, files = await self._async_tidy(entries, name) if name else ([], [])
        if done:
            record["tidied"] = list(record.get("tidied") or []) + done
            self._save()
            await self.async_reload(set(files))
        return done

    async def _rewrite(self, ids: dict[str, str], reload: bool = True, exact: bool = False) -> list[str]:
        """Replace device and entity registry ids in the automation, script, scene and package files, then reload.

        exact: whole entity ids only (for renamed entity ids)."""
        changed: set[str] = set()
        for domains, path in await self.hass.async_add_executor_job(_config_files, self.hass.config.path()):
            text = await self.hass.async_add_executor_job(_read, path)
            if text is None:
                continue
            new = tidy.replace_ids(text, ids) if exact else text
            if not exact:
                for old_id, new_id in ids.items():
                    new = new.replace(old_id, new_id)
            if new == text:
                continue
            await self.hass.async_add_executor_job(write_utf8_file_atomic, path, new)
            changed.update(domains)
        if reload:
            await self.async_reload(changed)
        return sorted(changed)


def _moved(hass: HomeAssistant, plan: Plan, rename_z2m: bool) -> triggers.Moved:
    return triggers.Moved(
        new_device_id=plan.new.id,
        old_domain=_domain(hass, plan.old),
        new_domain=_domain(hass, plan.new),
        old_ieee=next((v for k, v in plan.old.connections if k == dr.CONNECTION_ZIGBEE), None),
        old_z2m_name=plan.old.name if z2m_ieee(plan.old) else None,
        old_z2m_ieee=z2m_ieee(plan.old),
        old_base=z2m_base_topic(hass, plan.old, Z2M_BASE_TOPIC) if z2m_ieee(plan.old) else None,
        new_z2m_name=(z2m_name(device_name(plan.old)) if rename_z2m else plan.new.name) if z2m_ieee(plan.new) else None,
        new_base=z2m_base_topic(hass, plan.new, Z2M_BASE_TOPIC) if z2m_ieee(plan.new) else None,
        new_z2m_ieee=z2m_ieee(plan.new),
        context=_context(hass, plan),
    )


def _users_of_ids(config_dir: str, ids: dict[str, str]) -> list[str]:
    """Automations, scripts and scenes that store one of the ids, by name – what _rewrite would change."""
    found: list[str] = []
    for domains, path in _config_files(config_dir):
        text = _read(path)
        if not text or not any(old in text for old in ids):
            continue
        try:
            data = parse_yaml(text)
        except Exception:  # noqa: BLE001 - !include, !secret …: name the file instead
            data = None
        kind = domains[0] if len(domains) == 1 else None
        items = (
            [(kind, item) for item in data]
            if isinstance(data, list) and kind
            else [(kind, {"alias": key, **value}) for key, value in data.items() if isinstance(value, dict)]
            if isinstance(data, dict) and kind == "script"
            else []
        )
        named = [
            f"{k}: {item.get('alias') or item.get('name') or item.get('id') or '?'}"
            for k, item in items
            if isinstance(item, dict) and any(old in json.dumps(item, default=str) for old in ids)
        ]
        found += named or [os.path.relpath(path, config_dir)]
    return sorted(found)


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


_SETTINGS = ("name", "icon", "area_id", "labels", "aliases", "categories", "device_class", "hidden_by", "options")
_EMPTY_SETTINGS: dict[str, Any] = {
    "name": None,
    "icon": None,
    "area_id": None,
    "labels": [],
    "aliases": [],
    "categories": {},
    "device_class": None,
    "hidden_by": None,
    "options": {},
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


def _rename_all(hass: HomeAssistant, changes: list[dict[str, str]]) -> list[dict[str, str]]:
    """Rename entity ids; one whose new id another of them still holds waits for it, so a chain works out."""
    done: list[dict[str, str]] = []
    todo = list(changes)
    while todo:
        step = tidy.apply(hass, todo)
        if not step:
            break
        done += step
        todo = [c for c in todo if c not in step]
    return done


async def _rename_in_z2m(hass: HomeAssistant, device: dr.DeviceEntry, name: str) -> bool:
    """Give the device the same name in Zigbee2MQTT, without letting it change the Home Assistant entity ids."""
    ieee = z2m_ieee(device)
    if ieee is None or not hass.services.has_service("mqtt", "publish"):
        return False
    payload = json.dumps({"from": ieee, "to": z2m_name(name), "homeassistant_rename": False})
    await hass.services.async_call(
        "mqtt",
        "publish",
        {"topic": f"{z2m_base_topic(hass, device, Z2M_BASE_TOPIC)}/bridge/request/device/rename", "payload": payload},
    )
    return True


def _context(hass: HomeAssistant, plan: Plan) -> str:
    """'Aqara WSDCGQ11LM in ZHA → Aqara WSDCGQ11LM in Zigbee2MQTT', so the AI knows what it is looking at."""
    from .hardware import source

    def one(device: dr.DeviceEntry) -> str:
        what = " ".join(p for p in (device.manufacturer, device.model) if p) or device_name(device)
        return f"{what} in {source(hass, device)[1] or 'its integration'}"

    return f"{one(plan.old)} → {one(plan.new)}"


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
    """The files the automation, script and scene editors write - the only YAML files that are changed."""
    return [
        (("automation",), os.path.join(config_dir, AUTOMATIONS_FILE)),
        (("script",), os.path.join(config_dir, SCRIPTS_FILE)),
        (("scene",), os.path.join(config_dir, SCENES_FILE)),
    ]


def _packages_using(config_dir: str, ids: dict[str, str]) -> list[str]:
    """Package files (hand-written configuration) that mention one of the ids. They are only listed, never changed."""
    found = []
    for root, _dirs, names in os.walk(os.path.join(config_dir, "packages")):
        for name in sorted(names):
            path = os.path.join(root, name)
            if name.endswith((".yaml", ".yml")) and (text := _read(path)) and any(old in text for old in ids):
                found.append(os.path.relpath(path, config_dir))
    return found


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


def _old_name(hass: HomeAssistant, name: str) -> str:
    text = TEXTS.get(hass.config.language.split("-")[0], TEXTS["en"])
    return text["old_name"].format(name=name)


def _can_remove(hass: HomeAssistant, device: dr.DeviceEntry) -> bool:
    """Whether _remove_device will most likely manage it (for the test run)."""
    entry = hass.config_entries.async_get_entry(device.config_entry_id) if device.config_entry_id else None
    if entry is None or entry.state is not ConfigEntryState.LOADED:
        return True
    if entry.domain == "zha":
        return hass.services.has_service("zha", "remove")
    return bool(entry.supports_remove_device)


async def _remove_device(hass: HomeAssistant, device: dr.DeviceEntry) -> bool:
    """Remove the old device the way the device page does, if its integration allows it."""
    entry = hass.config_entries.async_get_entry(device.config_entry_id) if device.config_entry_id else None
    if entry is not None and entry.state is ConfigEntryState.LOADED and entry.domain == "zha":
        # ZHA has its own way: zha.remove forgets the device for good. Removing it from the registry only would
        # make ZHA add it again at the next start, with new entity ids.
        return await _remove_from_zha(hass, device)
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


async def _remove_from_zha(hass: HomeAssistant, device: dr.DeviceEntry) -> bool:
    ieee = next((value for kind, value in device.connections if kind == dr.CONNECTION_ZIGBEE), None)
    if ieee is None or not hass.services.has_service("zha", "remove"):
        return False
    try:
        await hass.services.async_call("zha", "remove", {"ieee": ieee}, blocking=True)
    except Exception:  # noqa: BLE001 - ZHA said no
        _LOGGER.warning("ZHA could not remove %s", device_name(device), exc_info=True)
        return False
    registry = dr.async_get(hass)
    if registry.async_get(device.id):
        registry.async_remove_device(device.id)
    return True


async def async_remove_device(hass: HomeAssistant, device_id: str) -> bool:
    """Remove a device that was already replaced but came back (e.g. still known by its old integration)."""
    device = dr.async_get(hass).async_get(device_id)
    return device is not None and await _remove_device(hass, device)


async def _wait_until_gone(hass: HomeAssistant, entity_ids: list[str]) -> None:
    """Give the old entities a moment to remove themselves, then clear what's left (a dead device's state)."""
    for _ in range(100):
        if not any(hass.states.get(e) for e in entity_ids):
            return
        await asyncio.sleep(0)
    for entity_id in entity_ids:
        hass.states.async_remove(entity_id)


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
