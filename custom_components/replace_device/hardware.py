"""Recognise the same physical device across integrations: Zigbee IEEE address, serial number or MAC address."""

from __future__ import annotations

import json
import re

from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.loader import async_get_loaded_integration

_Z2M = re.compile(r"^zigbee2mqtt_0x([0-9a-f]{16})$")
Z2M_SOURCE = "zigbee2mqtt"
# Names people know these by.
_SHORT = {"zha": "ZHA", "zwave_js": "Z-Wave JS"}


def hardware_keys(device: dr.DeviceEntry) -> set[str]:
    """Ids that stay the same when a device moves to another integration."""
    keys = set()
    for _domain, value in device.identifiers:
        if match := _Z2M.match(str(value).lower()):
            keys.add(f"ieee:{match[1]}")
        elif str(value).lower().startswith("serial_"):
            keys.add(_serial(str(value)[7:]))
    for kind, value in device.connections:
        if kind == dr.CONNECTION_ZIGBEE:
            keys.add(f"ieee:{value.replace(':', '').lower().removeprefix('0x')}")
        elif kind == dr.CONNECTION_NETWORK_MAC:
            keys.add(f"mac:{value.replace(':', '').lower()}")
    if device.serial_number:
        keys.add(_serial(device.serial_number))
    keys.discard("")
    return keys


def _serial(value: str) -> str:
    value = value.strip().lower()
    # Placeholder serials ("0000", "123456") are not unique.
    if len(value) < 6 or len(set(value)) < 3:
        return ""
    return f"serial:{value}"


def z2m_ieee(device: dr.DeviceEntry) -> str | None:
    """The 0x… address of a Zigbee2MQTT device, which Zigbee2MQTT accepts as its id."""
    for _domain, value in device.identifiers:
        if match := _Z2M.match(str(value).lower()):
            return f"0x{match[1]}"
    return None


def source(hass: HomeAssistant, device: dr.DeviceEntry) -> tuple[str | None, str | None]:
    """Where a device comes from, as (key, name). Zigbee2MQTT devices are told apart from other MQTT devices."""
    if any(str(value).startswith("zigbee2mqtt_") for _, value in device.identifiers):
        return Z2M_SOURCE, "Zigbee2MQTT"
    entry = hass.config_entries.async_get_entry(device.config_entry_id) if device.config_entry_id else None
    if entry is None:
        return None, None
    if entry.domain in _SHORT:
        return entry.domain, _SHORT[entry.domain]
    try:
        name = async_get_loaded_integration(hass, entry.domain).name
    except Exception:  # noqa: BLE001 - not loaded: use the entry's own title
        name = entry.title
    return entry.domain, name


def z2m_name(name: str) -> str:
    """A friendly name Zigbee2MQTT accepts: no MQTT wildcards, no topic levels."""
    return re.sub(r"[#+]", "", name).replace("/", "-").strip()


def z2m_base_topic(hass: HomeAssistant, device: dr.DeviceEntry, default: str) -> str:
    """The MQTT base topic of the Zigbee2MQTT instance a device belongs to (it can be changed, and several can run).

    Every Zigbee2MQTT entity is available only while "<base>/bridge/state" is online, so the topic is in its
    discovery data."""
    try:
        from homeassistant.components.mqtt import debug_info

        text = json.dumps(debug_info.info_for_device(hass, device.id), default=str)
    except Exception:  # noqa: BLE001 - MQTT not loaded, or its debug info changed
        return default
    match = re.search(r'([^"\\\s]+)/bridge/state', text)
    return match[1] if match else default
