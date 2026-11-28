"""Two things for devices that both work: swap them, or copy one's setup to a new one.

Swap: two sensors moved between rooms. Each takes the other's names, entity ids, area and settings, and what points at
the device itself (device triggers) follows - so "Stue temperatur" is the one in the living room again, and its history
stays with it. Undo swaps back.

Copy: a new device like one you have (a second motion sensor for the bedroom). The automations and scripts of the one
you have are made again for the new one: its own entities, and the room's lights and the like where the new room has
exactly one of the same kind. Each copy is shown first; one that still uses something in the other room says so.
Undo removes the copies."""

from __future__ import annotations

import json
import os
import time
from typing import Any
from uuid import uuid4

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import area_registry as ar, device_registry as dr, entity_registry as er
from homeassistant.util import slugify
from homeassistant.util.file import write_utf8_file_atomic
from homeassistant.util.yaml import dump, load_yaml

from . import references, tidy
from .const import AUTOMATIONS_FILE, SCRIPTS_FILE
from .matching import match


def _devices(hass: HomeAssistant, a_id: str, b_id: str) -> tuple[dr.DeviceEntry, dr.DeviceEntry] | None:
    devices = dr.async_get(hass)
    a, b = devices.async_get(a_id), devices.async_get(b_id)
    return (a, b) if a and b and a_id != b_id else None


def _pairs(hass: HomeAssistant, a: dr.DeviceEntry, b: dr.DeviceEntry) -> list[tuple[er.RegistryEntry, er.RegistryEntry]]:
    entities = er.async_get(hass)
    ea = er.async_entries_for_device(entities, a.id, include_disabled_entities=True)
    eb = er.async_entries_for_device(entities, b.id, include_disabled_entities=True)
    by_id = {e.entity_id: e for e in eb}
    mapping = match(ea, eb)
    return [(x, by_id[m]) for x in ea if (m := mapping.get(x.entity_id)) in by_id and by_id[m].domain == x.domain]


def _brief(hass: HomeAssistant, device: dr.DeviceEntry) -> dict[str, Any]:
    from .replace import device_name

    area = ar.async_get(hass).async_get_area(device.area_id) if device.area_id else None
    return {"id": device.id, "name": device_name(device), "area": area.name if area else None}


# ---------- swap ----------


def swap_plan(hass: HomeAssistant, a_id: str, b_id: str) -> dict[str, Any] | None:
    from .replace import _domain

    found = _devices(hass, a_id, b_id)
    if not found:
        return None
    a, b = found
    pairs = _pairs(hass, a, b)
    return {
        "a": _brief(hass, a),
        "b": _brief(hass, b),
        # Two of a kind only: a ZHA button and a Zigbee2MQTT one have different device triggers.
        "same_kind": _domain(hass, a) == _domain(hass, b),
        "pairs": [{"a": x.entity_id, "b": y.entity_id, "name": x.name or x.original_name or x.entity_id} for x, y in pairs],
    }


async def async_swap(replacer: Any, a_id: str, b_id: str, uuids: list[list[str]] | None = None) -> dict[str, Any]:
    """Swap the two. uuids: the pairs to swap (undo swaps exactly the same ones back)."""
    from .replace import _domain, _rename, _restore, _settings, device_name

    hass = replacer.hass
    found = _devices(hass, a_id, b_id)
    if not found or _domain(hass, found[0]) != _domain(hass, found[1]):
        raise HomeAssistantError("Only two devices of the same integration can swap")
    a, b = found
    entities, devices = er.async_get(hass), dr.async_get(hass)
    if uuids is None:
        pairs = _pairs(hass, a, b)
    else:
        pairs = [(x, y) for u, v in uuids if (x := entities.async_get(u)) and (y := entities.async_get(v))]
    if not pairs:
        raise HomeAssistantError("These two have nothing to swap")
    from . import stats

    record = {
        "id": uuid4().hex, "at": time.time(), "kind": "swap", "running": True,
        "old_device": {"id": a.id, "name": device_name(a), "name_by_user": a.name_by_user, "model": a.model},
        "new_device": {"id": b.id, "name": device_name(b), "name_by_user": b.name_by_user, "model": b.model},
        "entities": [], "pairs": [], "failed": [], "ids": {}, "files": [], "batch": None, "undone": False,
    }
    if uuids is None:  # written down before anything changes (an undo is part of its own record)
        replacer.history.append(record)
        await replacer.store.async_save(replacer._data())
    swapped, failed, moved = record["pairs"], record["failed"], []
    for x, y in pairs:
        x, y = entities.async_get(x.id), entities.async_get(y.id)  # as they are now
        if x is None or y is None:
            continue
        ida, idb, sa, sb = x.entity_id, y.entity_id, _settings(x), _settings(y)
        tmp = entities.async_generate_entity_id(x.domain, f"{ida.split('.', 1)[1]}_swapping")
        if not _rename(entities, ida, tmp, {}):
            failed.append(ida)
            continue
        # The entity shows up under its new id a moment later: its old state is out of the way at once.
        hass.states.async_remove(ida)
        if not _rename(entities, idb, ida, _restore(sa)):
            _rename(entities, tmp, ida, {})  # back as it was
            failed.append(ida)
            continue
        hass.states.async_remove(idb)
        if not _rename(entities, tmp, idb, _restore(sb)):  # put both back as they were
            _rename(entities, ida, idb, _restore(sb))
            _rename(entities, tmp, ida, _restore(sa))
            failed.append(ida)
            continue
        moved.append((ida, idb, tmp))
        for domain in set(sa["options"]) | set(sb["options"]):
            entities.async_update_entity_options(ida, domain, sa["options"].get(domain, {}))
            entities.async_update_entity_options(idb, domain, sb["options"].get(domain, {}))
        swapped.append([x.id, y.id])
    await stats.async_swap_history(hass, moved)
    devices.async_update_device(a.id, name_by_user=device_name(b), area_id=b.area_id, labels=set(b.labels))
    devices.async_update_device(b.id, name_by_user=device_name(a), area_id=a.area_id, labels=set(a.labels))
    # Device triggers and the like store the device's and entity's own ids: they follow the room too.
    ids = {a.id: b.id, b.id: a.id} | {u: v for u, v in swapped} | {v: u for u, v in swapped}
    from .replace import _safely

    record["files"] = await _safely("updating automations and scripts", replacer._rewrite(ids, reload=False), [])
    record["dashboards"] = await _safely("updating dashboards", references.async_rewrite_dashboards(hass, ids), [])
    await replacer.async_reload(set(record["files"]))
    record.pop("running", None)
    replacer._save()
    return {"id": record["id"], "swapped": len(swapped), "failed": failed, "changed": record["files"]}


async def async_swap_back(replacer: Any, record: dict[str, Any]) -> bool:
    """Undo: the same pairs swapped back, and each device's own name as it was."""
    a, b = record["old_device"], record["new_device"]
    await async_swap(replacer, a["id"], b["id"], uuids=record["pairs"])
    devices = dr.async_get(replacer.hass)
    for d in (a, b):
        if devices.async_get(d["id"]):
            devices.async_update_device(d["id"], name_by_user=d.get("name_by_user"))
    return True


# ---------- copy ----------


def _maps(
    hass: HomeAssistant, src: dr.DeviceEntry, dst: dr.DeviceEntry
) -> tuple[dict[str, str], dict[str, str], set[str], dict[str, str]]:
    """Entity ids and registry/device ids of the one you have -> the new one's, also the room's lights … where the new
    room has exactly one of the same kind. And the entity ids still left in the old room."""
    entities, devices = er.async_get(hass), dr.async_get(hass)
    ents: dict[str, str] = {}
    hexes = {src.id: dst.id}
    for x, y in _pairs(hass, src, dst):
        ents[x.entity_id] = y.entity_id
        hexes[x.id] = y.id

    def area(e: er.RegistryEntry) -> str | None:
        return e.area_id or (devices.async_get(e.device_id).area_id if e.device_id and devices.async_get(e.device_id) else None)

    def kind(e: er.RegistryEntry) -> tuple:
        return (e.domain, e.device_class or e.original_device_class)

    room: set[str] = set()
    names: dict[str, str] = {}
    if src.area_id and dst.area_id and src.area_id != dst.area_id:
        # Other devices in the room (a lamp by its device) where the new room has exactly one of the same model.
        theirs = [d for d in devices.devices.values() if d.area_id == dst.area_id and d.id != dst.id]
        for d in devices.devices.values():
            if d.area_id == src.area_id and d.id != src.id:
                same = [t for t in theirs if t.model and t.model == d.model]
                if len(same) == 1:
                    hexes[d.id] = same[0].id
                else:
                    room.add(d.id)
                    names[d.id] = d.name_by_user or d.name or d.id
    if src.area_id and src.area_id != dst.area_id:
        here = [e for e in entities.entities.values() if area(e) == src.area_id and e.device_id != src.id and not e.disabled_by]
        there = [e for e in entities.entities.values() if dst.area_id and area(e) == dst.area_id and e.device_id != dst.id and not e.disabled_by]
        for e in here:
            same = [t for t in there if kind(t) == kind(e)]
            if len(same) == 1:
                ents[e.entity_id] = same[0].entity_id
                hexes[e.id] = same[0].id
            else:
                room.add(e.entity_id)
    return ents, hexes, room, names


def _name(alias: str, src: dict[str, Any], dst: dict[str, Any]) -> str:
    new = alias
    for key in ("name", "area"):
        if src.get(key) and dst.get(key) and src[key].lower() in new.lower():
            i = new.lower().index(src[key].lower())
            new = new[:i] + dst[key] + new[i + len(src[key]):]
    return new if new != alias else f"{alias} ({dst['name']})"


def _area_values(node: Any) -> list[str]:
    if isinstance(node, list):
        return [v for x in node for v in _area_values(x)]
    if not isinstance(node, dict):
        return []
    out = []
    for k, v in node.items():
        if k == "area_id":
            out += [v] if isinstance(v, str) else [x for x in v if isinstance(x, str)] if isinstance(v, list) else []
        else:
            out += _area_values(v)
    return out


def _areas(node: Any, old: str | None, new: str | None) -> Any:
    """area_id: the old room -> the new room (only in area_id fields: an area id is a plain word)."""
    if not old or not new:
        return node
    if isinstance(node, list):
        return [_areas(x, old, new) for x in node]
    if not isinstance(node, dict):
        return node
    out = {}
    for k, v in node.items():
        if k == "area_id":
            out[k] = new if v == old else [new if x == old else x for x in v] if isinstance(v, list) else v
        else:
            out[k] = _areas(v, old, new)
    return out


def _build(config_dir: str, ents: dict[str, str], hexes: dict[str, str], room: set[str], src: dict, dst: dict) -> list[dict[str, Any]]:
    """Every automation and script that uses the one you have, made again for the new one. Runs in the executor."""
    out = []
    for kind, file in (("automation", AUTOMATIONS_FILE), ("script", SCRIPTS_FILE)):
        path = os.path.join(config_dir, file)
        try:
            data = load_yaml(path) if os.path.isfile(path) else None
        except Exception:  # noqa: BLE001 - a file it can't read is left alone
            continue
        items = (
            [(str(x.get("id") or i), x) for i, x in enumerate(data) if isinstance(x, dict)] if kind == "automation" and isinstance(data, list)
            else [(str(k), v) for k, v in data.items() if isinstance(v, dict)] if kind == "script" and isinstance(data, dict)
            else []
        )
        for key, item in items:
            text = json.dumps(item, default=str)
            # Only what uses the device itself (its id, its entities) - not everything in its room.
            if not any(h in text for h in src["own_hexes"]) and tidy.replace_ids(text, src["own_ids"]) == text:
                continue
            new_text = tidy.swap_ids(tidy.replace_ids(text, ents), hexes)
            copy = _areas(json.loads(new_text), src.get("area_id"), src.get("new_area_id"))
            new_text = json.dumps(copy)
            alias = str(item.get("alias") or key)
            copy["alias"] = _name(alias, src, dst)
            keeps = sorted(src["names"].get(e, e) for e in room if tidy.replace_ids(new_text, {e: "\0"}) != new_text)
            if src.get("area_id") and src["area_id"] in _area_values(copy):
                keeps.append(src["area"])
            out.append({"kind": kind, "key": key, "name": alias, "new_name": copy["alias"], "keeps": keeps, "item": copy})
    return out


async def _prepare(hass: HomeAssistant, src_id: str, dst_id: str) -> tuple[list[dict[str, Any]], dict, dict] | None:
    found = _devices(hass, src_id, dst_id)
    if not found:
        return None
    s, d = found
    ents, hexes, room, names = _maps(hass, s, d)
    pairs = _pairs(hass, s, d)
    mine = er.async_entries_for_device(er.async_get(hass), s.id, include_disabled_entities=True)
    src = _brief(hass, s) | {
        "area_id": s.area_id if s.area_id != d.area_id else None,
        "new_area_id": d.area_id,
        "names": names,
        "pairs": [x.id for x, _ in pairs],
        "own_hexes": [s.id, *(e.id for e in mine)],
        "own_ids": {e.entity_id: "\0" for e in mine},  # a marker: replaced = used
    }
    room |= {e.entity_id for e in mine if e.entity_id not in ents}  # what the new one has no match for: said too
    dst = _brief(hass, d)
    built = await hass.async_add_executor_job(_build, hass.config.path(), ents, hexes, room, src, dst)
    return built, src, dst


async def copy_plan(hass: HomeAssistant, src_id: str, dst_id: str) -> dict[str, Any] | None:
    got = await _prepare(hass, src_id, dst_id)
    if got is None:
        return None
    built, src, dst = got
    return {
        "src": {k: src[k] for k in ("id", "name", "area")}, "dst": dst, "pairs": len(src["pairs"]),
        "items": [{k: c[k] for k in ("kind", "key", "name", "new_name", "keeps")} for c in built],
    }


def _has_tags(path: str) -> bool:
    """A file with !include, !secret … would come back written out in full (secrets too): never written here."""
    try:
        with open(path, encoding="utf-8") as f:
            return any(t in f.read() for t in ("!include", "!secret", "!env_var"))
    except OSError:
        return False


def _write(config_dir: str, chosen: list[dict[str, Any]]) -> list[dict[str, str]]:
    """The copies added at the end of automations.yaml / scripts.yaml, as the editors write them."""
    created = []
    for kind, file in (("automation", AUTOMATIONS_FILE), ("script", SCRIPTS_FILE)):
        mine = [c for c in chosen if c["kind"] == kind]
        if not mine:
            continue
        path = os.path.join(config_dir, file)
        if _has_tags(path):
            raise HomeAssistantError(f"{file} uses !include or !secret, so it isn't written here - copy by hand")
        data = load_yaml(path) if os.path.isfile(path) else None
        if kind == "automation":
            data = list(data or [])
            taken = {str(x.get("id")) for x in data if isinstance(x, dict)}
            n = int(time.time() * 1000)
            for c in mine:
                while str(n) in taken:
                    n += 1
                taken.add(str(n))
                item = {"id": str(n), **{k: v for k, v in c["item"].items() if k != "id"}}
                data.append(item)
                created.append({"kind": kind, "key": item["id"], "name": c["new_name"]})
        else:
            data = dict(data or {})
            for c in mine:
                key = slugify(c["new_name"]) or "copy"
                n = 2
                while key in data:
                    key, n = f"{slugify(c['new_name'])}_{n}", n + 1
                data[key] = c["item"]
                created.append({"kind": kind, "key": key, "name": c["new_name"]})
        write_utf8_file_atomic(path, dump(data))
    return created


async def async_copy(replacer: Any, src_id: str, dst_id: str, keys: list[str]) -> dict[str, Any]:
    from .replace import device_name

    hass = replacer.hass
    got = await _prepare(hass, src_id, dst_id)
    if got is None:
        raise HomeAssistantError("Pick two devices that exist")
    built, src, dst = got
    chosen = [c for c in built if f"{c['kind']}:{c['key']}" in set(keys)]
    if not chosen:
        raise HomeAssistantError("Nothing picked to copy")
    created = await hass.async_add_executor_job(_write, hass.config.path(), chosen)
    domains = {c["kind"] for c in created}
    await replacer.async_reload(domains)
    devices = dr.async_get(hass)
    s, d = devices.async_get(src_id), devices.async_get(dst_id)
    record = {
        "id": uuid4().hex, "at": time.time(), "kind": "copy",
        "old_device": {"id": src_id, "name": device_name(s) if s else src["name"], "model": s.model if s else None},
        "new_device": {"id": dst_id, "name": device_name(d) if d else dst["name"], "model": d.model if d else None},
        "entities": [], "created": created, "ids": {}, "files": sorted(domains), "batch": None, "undone": False,
    }
    replacer.history.append(record)
    replacer._save()
    return {"id": record["id"], "created": created}


def _remove(config_dir: str, created: list[dict[str, str]]) -> set[str]:
    changed = set()
    for kind, file in (("automation", AUTOMATIONS_FILE), ("script", SCRIPTS_FILE)):
        # Only a copy that is still the one it made (same id and name): never another with the same id or key.
        keys = {c["key"]: c.get("name") for c in created if c["kind"] == kind}
        path = os.path.join(config_dir, file)
        if not keys or not os.path.isfile(path) or _has_tags(path):
            continue
        data = load_yaml(path)

        def mine(key: str, item: Any) -> bool:
            return key in keys and isinstance(item, dict) and (keys[key] is None or item.get("alias") == keys[key])

        if kind == "automation" and isinstance(data, list):
            new: Any = [x for x in data if not mine(str(x.get("id")) if isinstance(x, dict) else "", x)]
            same = len(new) == len(data)
        elif isinstance(data, dict):
            new = {k: v for k, v in data.items() if not mine(k, v)}
            same = len(new) == len(data)
        else:
            continue
        if not same:
            write_utf8_file_atomic(path, dump(new))
            changed.add(kind)
    return changed


async def async_copy_back(replacer: Any, record: dict[str, Any]) -> bool:
    """Undo: the copies are removed (one already deleted by hand is simply gone)."""
    changed = await replacer.hass.async_add_executor_job(_remove, replacer.hass.config.path(), record.get("created") or [])
    await replacer.async_reload(changed)
    return True
