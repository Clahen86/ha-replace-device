"""The API the panel talks to."""

from __future__ import annotations

import time
from typing import Any

import voluptuous as vol

from homeassistant.components import websocket_api
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import area_registry as ar, device_registry as dr, entity_registry as er

from .const import DOMAIN
from .replace import Plan, Replacer, async_plan, device_name
from .suggest import is_dead


@callback
def async_setup(hass: HomeAssistant) -> None:
    for command in (ws_devices, ws_plan, ws_replace, ws_history, ws_undo):
        websocket_api.async_register_command(hass, command)


def _replacer(hass: HomeAssistant) -> Replacer | None:
    entries = hass.config_entries.async_loaded_entries(DOMAIN)
    return entries[0].runtime_data if entries else None


def _device(hass: HomeAssistant, device: dr.DeviceEntry) -> dict[str, Any]:
    entities = er.async_entries_for_device(er.async_get(hass), device.id)
    area = ar.async_get(hass).async_get_area(device.area_id) if device.area_id else None
    entry = hass.config_entries.async_get_entry(device.config_entry_id) if device.config_entry_id else None
    dead = is_dead(hass, device.id)
    since = None
    if dead:
        states = [s for e in entities if (s := hass.states.get(e.entity_id))]
        since = min((s.last_changed_timestamp for s in states), default=None)
    return {
        "id": device.id,
        "name": device_name(device),
        "area": area.name if area else None,
        "manufacturer": device.manufacturer,
        "model": device.model or device.model_id,
        "integration": entry.domain if entry else None,
        "integration_title": entry.title if entry else None,
        "entities": len(entities),
        "dead": dead,
        "dead_since": since,
        "created": device.created_at.timestamp(),
    }


def _entity(hass: HomeAssistant, entry: er.RegistryEntry) -> dict[str, Any]:
    state = hass.states.get(entry.entity_id)
    return {
        "entity_id": entry.entity_id,
        "name": (state and state.attributes.get("friendly_name")) or entry.name or entry.original_name,
        "domain": entry.domain,
        "device_class": entry.device_class or entry.original_device_class,
        "unit": entry.unit_of_measurement,
        "state": state.state if state else None,
        "icon": entry.icon or entry.original_icon,
    }


def _plan(hass: HomeAssistant, plan: Plan) -> dict[str, Any]:
    return {
        "old": _device(hass, plan.old),
        "new": _device(hass, plan.new),
        "old_entities": [_entity(hass, e) for e in plan.old_entities],
        "new_entities": [_entity(hass, e) for e in plan.new_entities],
        "mapping": plan.mapping,
        "uses_device": plan.uses_device,
    }


@websocket_api.require_admin
@websocket_api.websocket_command({vol.Required("type"): f"{DOMAIN}/devices"})
@callback
def ws_devices(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]) -> None:
    """All devices with entities, dead ones flagged, and for each dead one the likely replacements."""
    devices = [
        _device(hass, d)
        for d in dr.async_get(hass).devices.values()
        if d.entry_type is None and er.async_entries_for_device(er.async_get(hass), d.id)
    ]
    by_id = {d["id"]: d for d in devices}
    registry = dr.async_get(hass)
    for item in devices:
        if not item["dead"]:
            continue
        dead = registry.async_get(item["id"])
        item["twins"] = [
            d["id"]
            for d in devices
            if not d["dead"]
            and d["id"] != item["id"]
            and (other := registry.async_get(d["id"]))
            and other.manufacturer == dead.manufacturer
            and (other.model or other.model_id) == (dead.model or dead.model_id)
            and d["created"] > (item["dead_since"] or 0) - 86400
        ]
    connection.send_result(
        msg["id"], {"devices": sorted(by_id.values(), key=lambda d: d["name"].lower()), "now": time.time()}
    )


@websocket_api.require_admin
@websocket_api.websocket_command(
    {
        vol.Required("type"): f"{DOMAIN}/plan",
        vol.Required("old"): str,
        vol.Required("new"): str,
        vol.Optional("mapping"): {str: vol.Any(str, None)},
    }
)
@callback
def ws_plan(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]) -> None:
    plan = async_plan(hass, msg["old"], msg["new"], msg.get("mapping"))
    if plan is None:
        connection.send_error(msg["id"], "unknown_device", "Pick two different devices that exist")
        return
    connection.send_result(msg["id"], _plan(hass, plan))


@websocket_api.require_admin
@websocket_api.websocket_command(
    {
        vol.Required("type"): f"{DOMAIN}/replace",
        vol.Required("old"): str,
        vol.Required("new"): str,
        vol.Required("mapping"): {str: vol.Any(str, None)},
        vol.Optional("remove_old", default=True): bool,
    }
)
@websocket_api.async_response
async def ws_replace(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]) -> None:
    plan = async_plan(hass, msg["old"], msg["new"], msg["mapping"])
    replacer = _replacer(hass)
    picked = [v for v in msg["mapping"].values() if v]
    if plan is None or replacer is None or len(picked) != len(set(picked)):
        connection.send_error(msg["id"], "invalid", "Not a valid replacement")
        return
    connection.send_result(msg["id"], await replacer.async_replace(plan, msg["remove_old"]))


@websocket_api.require_admin
@websocket_api.websocket_command({vol.Required("type"): f"{DOMAIN}/history"})
@callback
def ws_history(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]) -> None:
    replacer = _replacer(hass)
    history = [
        {k: r[k] for k in ("id", "at", "old_device", "new_device", "undone")} | {"moved": len(r["entities"])}
        for r in (replacer.history if replacer else [])
    ]
    connection.send_result(msg["id"], {"history": list(reversed(history))})


@websocket_api.require_admin
@websocket_api.websocket_command({vol.Required("type"): f"{DOMAIN}/undo", vol.Required("record"): str})
@websocket_api.async_response
async def ws_undo(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]) -> None:
    replacer = _replacer(hass)
    if replacer is None or not await replacer.async_undo(msg["record"]):
        connection.send_error(msg["id"], "not_found", "Nothing to undo")
        return
    connection.send_result(msg["id"], {"ok": True})
