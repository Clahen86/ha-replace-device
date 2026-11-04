"""Entity ids that follow the device's name, for the entities only the new device has.

Zigbee2MQTT names the entities of a new device after its address ("sensor.0x54ef441001314fb2_voltage"). The ones
that take over an old entity get the old id; the rest would keep the address. Here they get what Home Assistant's own
"rename entity ids too" would give them: "sensor.<device>_<entity>"."""

from __future__ import annotations

import re
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.util import slugify

# The address part of an id Zigbee2MQTT or ZHA made: "0x54ef441001314fb2_" or "54_ef_44_…_".
_ADDRESS = re.compile(r"^(?:0x[0-9a-f]{8,16}|(?:[0-9a-f]{2}_){7}[0-9a-f]{2})(?:_|$)")


def _part(entry: Any, device: str) -> str:
    """What the entity is called on its own: "Voltage", "Smoke density" …"""
    if entry.name:
        name = str(entry.name)
        return name[len(device) :].strip() if name.lower().startswith(device.lower()) else name
    if entry.original_name:
        return str(entry.original_name)
    if entry.translation_key:
        return str(entry.translation_key).replace("_", " ")
    if entry.has_entity_name:
        return ""  # the device's main entity: it is called what the device is called
    # No name to go by: the id without its address (or without the device's own model prefix).
    object_id = entry.entity_id.split(".", 1)[1]
    return _ADDRESS.sub("", object_id).replace("_", " ")


def plan(
    hass: HomeAssistant, device_name: str, entries: list[Any], free: set[str] | None = None
) -> list[dict[str, str]]:
    """The new id for each entry whose id doesn't follow the device's name; ids already taken get _2, _3 …

    free: ids that are taken now but will be free by then (the old device's, in a test run)."""
    free = free or set()
    registry = er.async_get(hass)
    slug = slugify(device_name)
    if not slug:
        return []
    planned: set[str] = set()
    changes = []
    for entry in entries:
        domain, object_id = entry.entity_id.split(".", 1)
        if object_id == slug or object_id.startswith(f"{slug}_"):
            continue
        part = slugify(_part(entry, device_name))
        base = f"{domain}.{slug}_{part}" if part else f"{domain}.{slug}"
        new_id, n = base, 2
        while new_id in planned or (
            new_id != entry.entity_id
            and new_id not in free
            and (registry.async_get(new_id) or hass.states.get(new_id))
        ):
            new_id, n = f"{base}_{n}", n + 1
        if new_id == entry.entity_id:
            continue
        planned.add(new_id)
        changes.append({"from": entry.entity_id, "to": new_id, "name": str(entry.name or entry.original_name or "")})
    return changes


def apply(hass: HomeAssistant, changes: list[dict[str, str]]) -> list[dict[str, str]]:
    """Rename; returns what was renamed (an id taken in the meantime is skipped)."""
    registry = er.async_get(hass)
    done = []
    for change in changes:
        if registry.async_get(change["from"]) is None or registry.async_get(change["to"]) is not None:
            continue
        try:
            registry.async_update_entity(change["from"], new_entity_id=change["to"])
        except ValueError:
            continue
        done.append(change)
    return done


def replace_ids(text: str, ids: dict[str, str]) -> str:
    """Replace whole entity ids only: "sensor.a_voltage" must not touch "sensor.a_voltage_2"."""
    if not ids:
        return text
    pattern = re.compile(
        r"(?<![\w.])(" + "|".join(re.escape(i) for i in sorted(ids, key=len, reverse=True)) + r")(?![\w])"
    )
    return pattern.sub(lambda m: ids[m.group(1)], text)
