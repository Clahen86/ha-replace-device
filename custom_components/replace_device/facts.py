"""Facts, not guesses: what Home Assistant itself knows about entities that are gone.

- Renames: every time an entity ID changes, Home Assistant fires entity_registry_updated with the old ID, and the
  recorder keeps it (for as many days as it keeps history).
- The last name and kind the dead entity had, from the recorder's history.
- Leftovers that are surely gone: their integration is removed, their integration no longer provides them, the
  Zigbee network doesn't know the device any more, or the add-on is uninstalled.

The recorder is only read (read-only session, in its own thread), never written.
"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr, entity_registry as er

from .hardware import z2m_base_topic, z2m_ieee

_LOGGER = logging.getLogger(__name__)


# ---------- from the recorder ----------


def _read_history(hass: HomeAssistant, entity_ids: list[str]) -> tuple[dict[str, str], dict[str, dict[str, Any]]]:
    """Runs in the recorder's thread: ({old_id: new_id} from renames, {old_id: last attributes})."""
    from sqlalchemy import select

    from homeassistant.components.recorder import get_instance
    from homeassistant.components.recorder.db_schema import (
        EventData, Events, EventTypes, StateAttributes, States, StatesMeta,
    )
    from homeassistant.helpers.recorder import session_scope

    renames: dict[str, str] = {}
    last: dict[str, dict[str, Any]] = {}
    wanted = set(entity_ids)
    instance = get_instance(hass)
    with session_scope(session=instance.get_session(), read_only=True) as session:
        rows = session.execute(
            select(EventData.shared_data)
            .join(Events, Events.data_id == EventData.data_id)
            .join(EventTypes, EventTypes.event_type_id == Events.event_type_id)
            .where(EventTypes.event_type == er.EVENT_ENTITY_REGISTRY_UPDATED)
            .order_by(Events.time_fired_ts)
        ).all()
        for (shared,) in rows:
            try:
                data = json.loads(shared or "{}")
            except ValueError:
                continue
            old, new = data.get("old_entity_id"), data.get("entity_id")
            if data.get("action") == "update" and old and new:
                # Follow a chain: a -> b, later b -> c, means a is now c.
                for k, v in list(renames.items()):
                    if v == old:
                        renames[k] = new
                renames[old] = new
        for entity_id in wanted:
            row = session.execute(
                select(StateAttributes.shared_attrs)
                .join(States, States.attributes_id == StateAttributes.attributes_id)
                .join(StatesMeta, StatesMeta.metadata_id == States.metadata_id)
                .where(StatesMeta.entity_id == entity_id)
                .order_by(States.last_updated_ts.desc())
                .limit(1)
            ).first()
            if row and row[0]:
                try:
                    last[entity_id] = json.loads(row[0])
                except ValueError:
                    pass
    return {k: v for k, v in renames.items() if k in wanted}, last


async def async_history(hass: HomeAssistant, entity_ids: list[str]) -> tuple[dict[str, str], dict[str, dict[str, Any]]]:
    if not entity_ids or "recorder" not in hass.config.components:
        return {}, {}
    from homeassistant.components.recorder import get_instance

    try:
        return await get_instance(hass).async_add_executor_job(_read_history, hass, entity_ids)
    except Exception:  # noqa: BLE001 - no history: only the other facts are used
        _LOGGER.debug("Could not read renames and names from the recorder", exc_info=True)
        return {}, {}


# ---------- leftovers that are surely gone ----------


async def _z2m_known(hass: HomeAssistant, base: str) -> set[str] | None:
    """IEEE addresses Zigbee2MQTT knows (its retained bridge/devices), None when it doesn't answer."""
    if "mqtt" not in hass.config.components:
        return None
    from homeassistant.components import mqtt

    got: asyncio.Future = asyncio.get_running_loop().create_future()

    def received(msg: Any) -> None:
        if not got.done():
            got.set_result(msg.payload)

    try:
        unsub = await mqtt.async_subscribe(hass, f"{base}/bridge/devices", received)
    except Exception:  # noqa: BLE001
        return None
    try:
        payload = await asyncio.wait_for(got, 5)
        return {str(d.get("ieee_address", "")).lower() for d in json.loads(payload) if d.get("ieee_address")}
    except (TimeoutError, ValueError, TypeError):
        return None
    finally:
        unsub()


def _zha_known(hass: HomeAssistant) -> set[str] | None:
    try:
        from homeassistant.components.zha.helpers import get_zha_gateway

        return {str(ieee).lower() for ieee in get_zha_gateway(hass).devices}
    except Exception:  # noqa: BLE001 - ZHA isn't set up
        return None


async def _addons(hass: HomeAssistant) -> set[str] | None:
    if "hassio" not in hass.config.components:
        return None
    try:
        from homeassistant.components.hassio import get_addons_info

        return set((get_addons_info(hass) or {}).keys())
    except Exception:  # noqa: BLE001
        return None


async def async_leftovers(hass: HomeAssistant, settled: bool = True) -> list[dict[str, Any]]:
    """Devices and entities that are surely gone - each with the reason. Switched-off devices are never here.
    settled: Home Assistant has run long enough that every integration has added its entities."""
    devices, entities = dr.async_get(hass), er.async_get(hass)
    found: list[dict[str, Any]] = []
    gone_devices: set[str] = set()
    bases: dict[str, set[str] | None] = {}
    zha = _zha_known(hass)
    addons = await _addons(hass)
    for device in devices.devices.values():
        entries = [hass.config_entries.async_get_entry(e) for e in device.config_entries]
        reason = None
        if device.config_entries and all(e is None for e in entries):
            reason = "integration_removed"
        elif (ieee := z2m_ieee(device)) is not None:
            base = z2m_base_topic(hass, device, "zigbee2mqtt")
            if base not in bases:
                bases[base] = await _z2m_known(hass, base)
            if bases[base] is not None and ieee.lower() not in bases[base]:
                reason = "not_in_z2m"
        elif zha is not None and (ieee := next((v for k, v in device.connections if k == dr.CONNECTION_ZIGBEE), None)) \
                and any(e and e.domain == "zha" for e in entries) and str(ieee).lower() not in zha:
            reason = "not_in_zha"
        elif addons is not None and device.model == "Home Assistant Add-on" \
                and (slug := next((v for k, v in device.identifiers if k == "hassio"), None)) and slug not in addons:
            reason = "addon_removed"
        if reason:
            gone_devices.add(device.id)
            found.append({
                "kind": "device", "id": device.id, "name": device.name_by_user or device.name or device.id,
                "reason": reason, "entities": [e.entity_id for e in er.async_entries_for_device(entities, device.id, True)],
            })
    for entry in entities.entities.values():
        if entry.device_id in gone_devices:
            continue  # removed with its device
        config = hass.config_entries.async_get_entry(entry.config_entry_id) if entry.config_entry_id else None
        state = hass.states.get(entry.entity_id)
        reason = None
        if entry.config_entry_id and config is None:
            reason = "integration_removed"
        elif settled and config is not None and config.state is ConfigEntryState.LOADED and not entry.disabled_by \
                and (state is None or state.attributes.get("restored")):
            reason = "not_provided"  # the integration runs, but no longer makes this entity
        if reason:
            found.append({"kind": "entity", "id": entry.entity_id, "name": entry.name or entry.original_name or entry.entity_id,
                          "reason": reason, "entities": [entry.entity_id]})
    for x in found:
        # "Not provided" is also what a switched-off Chromecast or TV looks like (they are only made when seen):
        # never "surely gone".
        x["sure"] = x["reason"] != "not_provided"
    found.sort(key=lambda x: (not x["sure"], x["reason"], x["name"].lower()))
    return found


async def async_remove_leftovers(hass: HomeAssistant, items: list[dict[str, str]], settled: bool) -> list[str]:
    """Remove leftovers - checked again first, so only what is still surely gone goes."""
    still = {(x["kind"], x["id"]) for x in await async_leftovers(hass, settled)}
    return [i["id"] for i in items if (i["kind"], i["id"]) in still and await _remove(hass, i["kind"], i["id"])]


async def _remove(hass: HomeAssistant, kind: str, item_id: str) -> bool:
    if kind == "entity":
        er.async_get(hass).async_remove(item_id)
        return True
    from .replace import _remove_device

    device = dr.async_get(hass).async_get(item_id)
    if device is None:
        return False
    if await _remove_device(hass, device):
        return True
    dr.async_get(hass).async_remove_device(item_id)  # its integration is gone or doesn't know it: just the registry
    return True
