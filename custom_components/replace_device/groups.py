"""Zigbee groups (made in ZHA or Zigbee2MQTT). The group itself has to be made again in the new integration; this
pairs the old and new group entities by name, so the new one can take over the entity id and history."""

from __future__ import annotations

import re

from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr, entity_registry as er

from .hardware import Z2M_SOURCE

_NOISE = re.compile(r"\b(?:zha|z2m|zigbee2mqtt|group|groups|gruppe|grupper|0x[0-9a-f]+)\b")


def group_entities(hass: HomeAssistant, source: str) -> list[tuple[str, er.RegistryEntry]]:
    """(group name, entity) for the groups of one integration."""
    entities, devices = er.async_get(hass), dr.async_get(hass)
    found = []
    for entry in entities.entities.values():
        if source == "zha" and entry.platform == "zha" and "zha_group" in (entry.unique_id or ""):
            state = hass.states.get(entry.entity_id)
            name = entry.name or entry.original_name or (state and state.attributes.get("friendly_name")) or ""
            found.append((name or entry.entity_id.split(".", 1)[1], entry))
        elif source == Z2M_SOURCE and entry.platform == "mqtt" and entry.device_id:
            device = devices.async_get(entry.device_id)
            if (
                device
                and (device.model or "").lower() == "group"
                and any(str(value).startswith("zigbee2mqtt_") for _, value in device.identifiers)
            ):
                found.append((device.name_by_user or device.name or entry.entity_id, entry))
    return found


def _key(name: str) -> str:
    return re.sub(r"[^a-z0-9æøå]+", " ", _NOISE.sub(" ", name.lower().replace("_", " "))).strip()


def match_groups(hass: HomeAssistant, source: str, target: str) -> list[tuple[str, er.RegistryEntry, er.RegistryEntry]]:
    """Old and new group entities with the same name and kind (light to light)."""
    new = {(_key(name), entry.domain): entry for name, entry in group_entities(hass, target)}
    pairs = []
    for name, entry in group_entities(hass, source):
        if (twin := new.get((_key(name), entry.domain))) is not None:
            pairs.append((name, entry, twin))
    return pairs
