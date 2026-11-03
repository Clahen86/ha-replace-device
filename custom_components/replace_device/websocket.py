"""The API the panel talks to."""

from __future__ import annotations

import time
from typing import Any

import voluptuous as vol

from homeassistant.components import websocket_api
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import area_registry as ar, device_registry as dr, entity_registry as er

from .const import DOMAIN
from . import references
from .checks import async_checks
from .groups import match_groups
from .hardware import hardware_keys, source, z2m_ieee
from .replace import Plan, Replacer, async_plan, device_name
from .suggest import is_dead


@callback
def async_setup(hass: HomeAssistant) -> None:
    for command in (ws_devices, ws_plan, ws_replace, ws_history, ws_undo, ws_migrate_plan, ws_migrate):
        websocket_api.async_register_command(hass, command)


def _replacer(hass: HomeAssistant) -> Replacer | None:
    entries = hass.config_entries.async_loaded_entries(DOMAIN)
    return entries[0].runtime_data if entries else None


def _device(hass: HomeAssistant, device: dr.DeviceEntry) -> dict[str, Any]:
    entities = er.async_entries_for_device(er.async_get(hass), device.id)
    area = ar.async_get(hass).async_get_area(device.area_id) if device.area_id else None
    source_key, source_name = source(hass, device)
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
        "integration": source_key,
        "integration_title": source_name,
        "z2m": z2m_ieee(device) is not None,
        "hardware": sorted(hardware_keys(device)),
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
@websocket_api.async_response
async def ws_plan(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]) -> None:
    plan = async_plan(hass, msg["old"], msg["new"], msg.get("mapping"))
    if plan is None:
        connection.send_error(msg["id"], "unknown_device", "Pick two different devices that exist")
        return
    replacer = _replacer(hass)
    # The AI only fills gaps in a fresh plan; a mapping the user edited is left alone.
    filled = await replacer.async_fill_with_ai(plan) if replacer and "mapping" not in msg else []
    connection.send_result(
        msg["id"],
        _plan(hass, plan)
        | {"ai": filled, "ai_enabled": bool(replacer and replacer.ai_entity), "checks": await async_checks(hass, plan)},
    )


@websocket_api.require_admin
@websocket_api.websocket_command(
    {
        vol.Required("type"): f"{DOMAIN}/replace",
        vol.Required("old"): str,
        vol.Required("new"): str,
        vol.Required("mapping"): {str: vol.Any(str, None)},
        vol.Optional("remove_old", default=True): bool,
        vol.Optional("rename_z2m", default=False): bool,
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
    connection.send_result(msg["id"], await replacer.async_replace(plan, msg["remove_old"], msg["rename_z2m"]))


@websocket_api.require_admin
@websocket_api.websocket_command({vol.Required("type"): f"{DOMAIN}/history"})
@callback
def ws_history(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]) -> None:
    replacer = _replacer(hass)
    history = [
        {k: r[k] for k in ("id", "at", "old_device", "new_device", "undone")}
        | {
            "moved": len(r["entities"]),
            "batch": r.get("batch"),
            "unresolved": r.get("triggers", {}).get("unresolved", []),
        }
        for r in (replacer.history if replacer else [])
    ]
    connection.send_result(msg["id"], {"history": list(reversed(history))})


@websocket_api.require_admin
@websocket_api.websocket_command(
    {vol.Required("type"): f"{DOMAIN}/undo", vol.Exclusive("record", "what"): str, vol.Exclusive("batch", "what"): str}
)
@websocket_api.async_response
async def ws_undo(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]) -> None:
    replacer = _replacer(hass)
    if replacer is None:
        connection.send_error(msg["id"], "not_found", "Nothing to undo")
        return
    if "batch" in msg:
        count = await replacer.async_undo_batch(msg["batch"])
    else:
        count = int(await replacer.async_undo(msg.get("record", "")))
    if not count:
        connection.send_error(msg["id"], "not_found", "Nothing to undo")
        return
    connection.send_result(msg["id"], {"undone": count})


def _devices_from(hass: HomeAssistant, key: str) -> list[dr.DeviceEntry]:
    entities = er.async_get(hass)
    return [
        d
        for d in dr.async_get(hass).devices.values()
        if d.entry_type is None
        and source(hass, d)[0] == key
        and (d.model or "").lower() != "group"
        and er.async_entries_for_device(entities, d.id)
    ]


@websocket_api.require_admin
@websocket_api.websocket_command(
    {vol.Required("type"): f"{DOMAIN}/migrate_plan", vol.Required("source"): str, vol.Required("target"): str}
)
@websocket_api.async_response
async def ws_migrate_plan(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]) -> None:
    """Every device of one integration paired with the same physical device in another, and their Zigbee groups."""
    dashboards = await references.async_dashboards(hass)
    targets: dict[str, dr.DeviceEntry] = {}
    for device in _devices_from(hass, msg["target"]):
        for key in hardware_keys(device):
            targets.setdefault(key, device)
    pairs, missing = [], []
    for old in _devices_from(hass, msg["source"]):
        keys = hardware_keys(old)
        new = next((targets[k] for k in sorted(keys) if k in targets), None)
        if new is None:
            missing.append(_device(hass, old))
            continue
        plan = async_plan(hass, old.id, new.id)
        checks = await async_checks(hass, plan, dashboards) if plan else {}
        pairs.append(
            {
                "old": _device(hass, old),
                "new": _device(hass, new),
                "by": next(k for k in sorted(keys) if k in targets).split(":")[0],
                "matched": len(plan.pairs) if plan else 0,
                "total": len(plan.old_entities) if plan else 0,
                "checks": checks,
            }
        )
    groups = [
        {"name": name, "old": old.entity_id, "new": new.entity_id}
        for name, old, new in match_groups(hass, msg["source"], msg["target"])
    ]
    connection.send_result(msg["id"], {"pairs": pairs, "missing": missing, "groups": groups})


@websocket_api.require_admin
@websocket_api.websocket_command(
    {
        vol.Required("type"): f"{DOMAIN}/migrate",
        vol.Required("pairs"): [{vol.Required("old"): str, vol.Required("new"): str}],
        vol.Optional("groups", default=[]): [
            {vol.Required("name"): str, vol.Required("old"): str, vol.Required("new"): str}
        ],
        vol.Optional("remove_old", default=True): bool,
        vol.Optional("rename_z2m", default=False): bool,
    }
)
@websocket_api.async_response
async def ws_migrate(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]) -> None:
    """Replace many devices in one go; automations and scripts are reloaded once at the end."""
    replacer = _replacer(hass)
    if replacer is None:
        connection.send_error(msg["id"], "not_loaded", "Replace Device is not set up")
        return
    batch = str(int(time.time() * 1000))
    done, failed, moved, reload, unresolved = [], [], 0, set(), []
    for pair in msg["pairs"]:
        plan = async_plan(hass, pair["old"], pair["new"])
        if plan is None:
            failed.append(pair["old"])
            continue
        await replacer.async_fill_with_ai(plan)
        result = await replacer.async_replace(plan, msg["remove_old"], msg["rename_z2m"], reload=False, batch=batch)
        done.append(result["id"])
        moved += result["moved"]
        reload.update(result["changed"])
        unresolved += result["triggers"]["unresolved"]
    entities = er.async_get(hass)
    for group in msg["groups"]:
        old, new = entities.async_get(group["old"]), entities.async_get(group["new"])
        if old is None or new is None:
            failed.append(group["old"])
            continue
        result = await replacer.async_replace_entity(group["name"], old, new, batch=batch, reload=False)
        done.append(result["id"])
        moved += 1
        reload.update(result["changed"])
    await replacer.async_reload(reload)
    connection.send_result(
        msg["id"],
        {"devices": len(done), "moved": moved, "failed": failed, "batch": batch, "unresolved": unresolved},
    )
