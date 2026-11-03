"""Entities a device had before they were deleted (e.g. a device reset or unpaired before it was replaced).

Home Assistant keeps deleted entities for a while, with their entity ID and settings, but without the device. They
are found again by the device's address inside their unique ID. Their entity IDs are free, so the new device's
entities can take them – and with them the history, which the recorder keeps by entity ID."""

from __future__ import annotations

import re
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr, entity_registry as er
from homeassistant.helpers.typing import UNDEFINED


class Remembered:
    """A deleted entity, looking like a registry entry where it matters for matching and replacing."""

    def __init__(self, deleted: er.DeletedRegistryEntry) -> None:
        self.entity_id = deleted.entity_id
        self.unique_id = deleted.unique_id
        self.platform = deleted.platform
        self.domain = deleted.entity_id.split(".", 1)[0]
        self.id = deleted.id
        self.device_id = None
        self.name = deleted.name
        self.icon = deleted.icon
        self.area_id = deleted.area_id
        self.labels = set(deleted.labels)
        self.aliases = list(deleted.aliases)
        self.categories = dict(deleted.categories)
        self.device_class = deleted.device_class
        self.hidden_by = None if deleted.hidden_by is UNDEFINED else deleted.hidden_by
        self.options: dict[str, Any] = {} if deleted.options is UNDEFINED else dict(deleted.options)
        self.disabled_by = None if deleted.disabled_by is UNDEFINED else deleted.disabled_by
        # Not kept for deleted entities.
        self.original_name = self.original_device_class = self.original_icon = None
        self.translation_key = self.unit_of_measurement = self.entity_category = self.capabilities = None


def _needles(device: dr.DeviceEntry) -> list[tuple[str, ...]]:
    """Parts of the device's identifiers that its entities' unique IDs contain (all parts of a tuple must; a tuple
    starting with "^" is a prefix)."""
    needles: list[tuple[str, ...]] = []
    for _domain, value in device.identifiers:
        value = str(value).lower()
        if ":aid:" in value:
            # HomeKit: unique IDs start with "<bridge accessory id>_<accessory number>_".
            accessory, aid = value.split(":aid:", 1)
            needles.append(("^", f"{accessory}_{aid}_"))
            continue
        if _domain == "zwave_js" and (zwave := re.fullmatch(r"(\d+)-(\d+)", value)):
            # Z-Wave JS: unique IDs start with "<home id>.<node id>-".
            needles.append(("^", f"{zwave[1]}.{zwave[2]}-"))
            continue
        value = re.sub(r"^(?:zigbee2mqtt_|deviceid_|serial_)|-matternodedevice$", "", value)
        if len(value) >= 8:
            needles.append((value,))
    for kind, value in device.connections:
        if kind in (dr.CONNECTION_ZIGBEE, dr.CONNECTION_NETWORK_MAC) and len(value) >= 8:
            needles.append((value.lower(),))
            # Shelly writes its MAC without colons in unique IDs: "C45BBE6C7B2C-switch:0".
            needles.append((value.lower().replace(":", ""),))
    return needles


def remembered(hass: HomeAssistant, device: dr.DeviceEntry) -> list[Remembered]:
    """Deleted entities of a device whose entity IDs are still free."""
    needles = _needles(device)
    if not needles:
        return []
    registry = er.async_get(hass)
    found = []
    for deleted in registry.deleted_entities.values():
        unique_id = str(deleted.unique_id).lower()
        if registry.async_get(deleted.entity_id) is not None:
            continue
        if deleted.config_entry_id not in (None, device.config_entry_id):
            continue
        if any(_matches(unique_id, needle) for needle in needles):
            found.append(Remembered(deleted))
    return sorted(found, key=lambda e: e.entity_id)


def _matches(unique_id: str, needle: tuple[str, ...]) -> bool:
    if needle[0] == "^":
        return unique_id.startswith(needle[1])
    return all(part in unique_id for part in needle)
