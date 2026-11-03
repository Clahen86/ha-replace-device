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
from .replace import Plan, Replacer, async_plan, async_remove_device, device_name
from .suggest import is_dead


@callback
def async_setup(hass: HomeAssistant) -> None:
    for command in (
        ws_devices,
        ws_hide,
        ws_remove_device,
        ws_plan,
        ws_replace,
        ws_history,
        ws_undo,
        ws_redo,
        ws_edit_plan,
        ws_edit,
        ws_retranslate,
        ws_migrate_plan,
        ws_migrate,
    ):
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
@websocket_api.async_response
async def ws_devices(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]) -> None:
    """All devices with entities; for the ones without contact, the last battery level and likely replacements."""
    replacer = _replacer(hass)
    hidden = set(replacer.hidden) if replacer else set()
    devices = [
        _device(hass, d)
        for d in dr.async_get(hass).devices.values()
        if d.entry_type is None and er.async_entries_for_device(er.async_get(hass), d.id)
    ]
    registry = dr.async_get(hass)
    took_over = _took_over(hass)
    for item in devices:
        item["hidden"] = item["id"] in hidden
        item["moved_to"] = _moved_to(hass, registry.async_get(item["id"]), took_over)
        if not item["dead"]:
            continue
        dead = registry.async_get(item["id"])
        item["battery"] = await _last_battery(hass, item["id"])
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
    connection.send_result(msg["id"], {"devices": sorted(devices, key=lambda d: d["name"].lower()), "now": time.time()})


async def _last_battery(hass: HomeAssistant, device_id: str) -> float | None:
    """The last battery level a device reported before it lost contact (None if it has no battery or no history)."""
    battery = next(
        (
            e.entity_id
            for e in er.async_entries_for_device(er.async_get(hass), device_id)
            if e.domain == "sensor" and (e.device_class or e.original_device_class) == "battery"
        ),
        None,
    )
    if battery is None or "recorder" not in hass.config.components:
        return None
    from homeassistant.components.recorder import get_instance, history

    try:
        states = await get_instance(hass).async_add_executor_job(history.get_last_state_changes, hass, 5, battery)
    except Exception:  # noqa: BLE001 - no history is no answer, not an error
        return None
    # Newest first: the last number before it went unavailable.
    for state in reversed(states.get(battery, [])):
        try:
            return float(state.state)
        except ValueError:
            continue
    return None


@websocket_api.require_admin
@websocket_api.websocket_command({vol.Required("type"): f"{DOMAIN}/remove_device", vol.Required("device"): str})
@websocket_api.async_response
async def ws_remove_device(
    hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]
) -> None:
    """Remove a leftover of a device that was already replaced, the way its integration does it."""
    removed = await async_remove_device(hass, msg["device"])
    connection.send_result(msg["id"], {"removed": removed})


@websocket_api.require_admin
@websocket_api.websocket_command(
    {vol.Required("type"): f"{DOMAIN}/hide", vol.Required("device"): str, vol.Required("hidden"): bool}
)
@callback
def ws_hide(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]) -> None:
    """Keep a device that is only switched off (a bulb on a wall switch) out of the list."""
    replacer = _replacer(hass)
    if replacer is None:
        connection.send_error(msg["id"], "not_loaded", "Replace Device is not set up")
        return
    replacer.set_hidden(msg["device"], msg["hidden"])
    connection.send_result(msg["id"], {"ok": True})


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
@websocket_api.websocket_command({vol.Required("type"): f"{DOMAIN}/retranslate", vol.Required("record"): str})
@websocket_api.async_response
async def ws_retranslate(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]) -> None:
    replacer = _replacer(hass)
    result = await replacer.async_retranslate(msg["record"]) if replacer else None
    if result is None:
        connection.send_error(msg["id"], "not_found", "Nothing to check")
        return
    connection.send_result(msg["id"], result)


@websocket_api.require_admin
@websocket_api.websocket_command({vol.Required("type"): f"{DOMAIN}/edit_plan", vol.Required("record"): str})
@callback
def ws_edit_plan(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]) -> None:
    replacer = _replacer(hass)
    plan = replacer.edit_plan(msg["record"]) if replacer else None
    if plan is None:
        connection.send_error(msg["id"], "not_found", "Nothing to change")
        return
    connection.send_result(msg["id"], plan)


@websocket_api.require_admin
@websocket_api.websocket_command(
    {
        vol.Required("type"): f"{DOMAIN}/edit",
        vol.Required("record"): str,
        vol.Required("mapping"): {str: vol.Any(str, None)},
    }
)
@websocket_api.async_response
async def ws_edit(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]) -> None:
    replacer = _replacer(hass)
    if replacer is None or not await replacer.async_edit(msg["record"], msg["mapping"]):
        connection.send_error(msg["id"], "invalid", "Not a valid change")
        return
    connection.send_result(msg["id"], {"ok": True})


@websocket_api.require_admin
@websocket_api.websocket_command(
    {vol.Required("type"): f"{DOMAIN}/redo", vol.Exclusive("record", "what"): str, vol.Exclusive("batch", "what"): str}
)
@websocket_api.async_response
async def ws_redo(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]) -> None:
    replacer = _replacer(hass)
    if replacer is None:
        connection.send_error(msg["id"], "not_found", "Nothing to do again")
        return
    if "batch" in msg:
        count = await replacer.async_redo_batch(msg["batch"])
    else:
        count = int(await replacer.async_redo(msg.get("record", "")))
    if not count:
        connection.send_error(msg["id"], "not_found", "Nothing to do again")
        return
    connection.send_result(msg["id"], {"redone": count})


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


def _took_over(hass: HomeAssistant) -> dict[str, dr.DeviceEntry]:
    """Hardware key -> new device of every replacement that is still in force."""
    replacer = _replacer(hass)
    registry = dr.async_get(hass)
    keys: dict[str, dr.DeviceEntry] = {}
    for record in replacer.history if replacer else []:
        if record["undone"] or not (new := registry.async_get(record["new_device"].get("id") or "")):
            continue
        for key in hardware_keys(new):
            keys[key] = new
    return keys


def _moved_to(hass: HomeAssistant, device: dr.DeviceEntry, took_over: dict[str, dr.DeviceEntry]) -> str | None:
    """The name of the device this one was already replaced by, if it is the same hardware (a leftover)."""
    for key in hardware_keys(device):
        if (new := took_over.get(key)) is not None and new.id != device.id:
            return device_name(new) + f" ({source(hass, new)[1]})"
    return None


def _by_key(devices: list[dr.DeviceEntry]) -> dict[str, list[dr.DeviceEntry]]:
    index: dict[str, list[dr.DeviceEntry]] = {}
    for device in devices:
        for key in hardware_keys(device):
            index.setdefault(key, []).append(device)
    return index


def _devices_from(hass: HomeAssistant, key: str) -> list[dr.DeviceEntry]:
    entities = er.async_get(hass)
    return [
        d
        for d in dr.async_get(hass).devices.values()
        if d.entry_type is None
        and source(hass, d)[0] == key
        and (d.model or "").lower() != "group"
        and not any(str(v).startswith("zigbee2mqtt_bridge_") for _, v in d.identifiers)
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
    source_devices = _devices_from(hass, msg["source"])
    sources, targets = _by_key(source_devices), _by_key(_devices_from(hass, msg["target"]))
    pairs, missing, used, leftovers = [], [], set(), []
    took_over = _took_over(hass)
    for old in source_devices:
        if moved := _moved_to(hass, old, took_over):
            leftovers.append(_device(hass, old) | {"moved_to": moved})
            continue
        # Only keys that point at exactly one device on each side: Shelly channels share their MAC, for one.
        keys = [k for k in sorted(hardware_keys(old)) if len(sources.get(k, [])) == 1 and len(targets.get(k, [])) == 1]
        new = next((targets[k][0] for k in keys if targets[k][0].id not in used), None)
        if new is None:
            missing.append(_device(hass, old))
            continue
        used.add(new.id)
        plan = async_plan(hass, old.id, new.id)
        checks = await async_checks(hass, plan, dashboards) if plan else {}
        pairs.append(
            {
                "old": _device(hass, old),
                "new": _device(hass, new),
                "by": next(k for k in keys if targets[k][0].id == new.id).split(":")[0],
                "matched": len(plan.pairs) if plan else 0,
                "total": len(plan.old_entities) if plan else 0,
                "checks": checks,
            }
        )
    groups = [
        {"name": name, "old": old.entity_id, "new": new.entity_id}
        for name, old, new in match_groups(hass, msg["source"], msg["target"])
    ]
    connection.send_result(msg["id"], {"pairs": pairs, "missing": missing, "groups": groups, "leftovers": leftovers})


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
    done, failed, moved, reload, unresolved, translated = [], [], 0, set(), [], 0
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
        translated += len(result["triggers"]["translated"])
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
        {
            "devices": len(done),
            "moved": moved,
            "failed": failed,
            "batch": batch,
            "unresolved": unresolved,
            "translated": translated,
        },
    )
