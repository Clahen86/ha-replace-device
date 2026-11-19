"""The device's own settings: motion sensitivity, LED brightness, power-on behaviour, occupancy timeout …

When the old and the new device are the same kind (same model, or the same integration and the same setting), the
values of the old device's configuration entities are set on the new device's matching ones, through the normal
services. The old device is usually dead, so its value is its last known state, or the recorder's last valid one."""

from __future__ import annotations

import asyncio
import logging
import re
from datetime import timedelta
from typing import Any

from homeassistant.const import STATE_UNAVAILABLE, STATE_UNKNOWN, EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.util import dt as dt_util

_LOGGER = logging.getLogger(__name__)

DOMAINS = ("number", "select", "switch", "text")
# Never copied: buttons in disguise, and calibration (Zigbee2MQTT's is moved on its own, see z2m.py).
_DANGER = re.compile(
    r"factory|reset|identify|update|firmware|calibrat|restart|reboot|pairing|permit_join|(?<![a-z])ota(?![a-z])",
    re.IGNORECASE,
)
_EMPTY = (STATE_UNAVAILABLE, STATE_UNKNOWN, "", None)
# How far back the recorder is asked for the old value.
_HISTORY_DAYS = 365
_TIMEOUT = 10


def _danger(entry: Any) -> bool:
    words = [entry.entity_id.split(".", 1)[1], entry.original_name, entry.name, entry.translation_key]
    return any(_DANGER.search(str(w)) for w in words if w)


def _config(entry: Any) -> bool:
    return getattr(entry, "entity_category", None) in (EntityCategory.CONFIG, "config")


def _same_setting(old: Any, new: Any) -> bool:
    """The same setting in the same integration: same translation key, or same name."""
    if old.translation_key and old.translation_key == new.translation_key:
        return True
    return bool(old.original_name and str(old.original_name).lower() == str(new.original_name or "").lower())


def pairs(
    old_device: dr.DeviceEntry,
    new_device: dr.DeviceEntry,
    old_domain: str | None,
    new_domain: str | None,
    matched: list[tuple[Any, Any]],
) -> list[tuple[Any, Any]]:
    """The matched configuration entities whose value can be copied."""
    same_model = bool(old_device.model) and old_device.model == new_device.model and (
        not old_device.manufacturer or not new_device.manufacturer or old_device.manufacturer == new_device.manufacturer
    )
    same_integration = bool(old_domain) and old_domain == new_domain
    if not (same_model or same_integration):
        return []
    return [
        (o, n)
        for o, n in matched
        if o.domain == n.domain
        and o.domain in DOMAINS
        and _config(o)
        and _config(n)
        and not _danger(o)
        and not _danger(n)
        and (same_model or _same_setting(o, n))
        and (o.unit_of_measurement or None) == (n.unit_of_measurement or None)
    ]


async def _last_valid(hass: HomeAssistant, entity_id: str) -> str | None:
    """The newest state the recorder has that isn't unavailable or unknown."""
    if "recorder" not in hass.config.components:
        return None
    from homeassistant.components.recorder import get_instance, history

    start = dt_util.utcnow() - timedelta(days=_HISTORY_DAYS)
    try:
        found = await get_instance(hass).async_add_executor_job(
            lambda: history.state_changes_during_period(
                hass, start, entity_id=entity_id, no_attributes=True, descending=True, limit=20,
                include_start_time_state=False,
            )
        )
    except Exception:  # noqa: BLE001 - no recorder, or it couldn't answer
        _LOGGER.debug("No history for %s", entity_id, exc_info=True)
        return None
    for state in found.get(entity_id) or []:
        if state.state not in _EMPTY:
            return state.state
    return None


def _caps(hass: HomeAssistant, entry: Any) -> dict[str, Any]:
    state = hass.states.get(entry.entity_id)
    return dict(state.attributes if state else {}) | dict(entry.capabilities or {})


def valid(domain: str, value: str, caps: dict[str, Any]) -> Any:
    """The value in the form the new entity takes it, or None when it doesn't fit."""
    if domain == "switch":
        return value if value in ("on", "off") else None
    if domain == "select":
        options = caps.get("options")
        return value if isinstance(options, list) and value in options else None
    if domain == "number":
        try:
            number, low, high = float(value), float(caps["min"]), float(caps["max"])
        except (KeyError, TypeError, ValueError):
            return None
        return number if low <= number <= high else None
    if domain == "text":
        if caps.get("mode") == "password":
            return None
        low, high = int(caps.get("min", 0) or 0), int(caps.get("max", 255) or 255)
        if not low <= len(value) <= high:
            return None
        if (pattern := caps.get("pattern")) and not re.fullmatch(str(pattern), value):
            return None
        return value
    return None


async def async_plan(
    hass: HomeAssistant, found: list[tuple[Any, Any]], targets: dict[str, str]
) -> list[dict[str, Any]]:
    """What will be copied: [{entity_id (the id it has after the replacement), domain, name, value, source}].

    targets: old entity id -> the id the new entity takes."""
    plan = []
    for old, new in found:
        state = hass.states.get(old.entity_id)
        value, source = (state.state, "state") if state and state.state not in _EMPTY else (None, "history")
        if value is None:
            value = await _last_valid(hass, old.entity_id)
        if value is None:
            continue
        fitted = valid(old.domain, value, _caps(hass, new))
        if fitted is None:
            continue
        now = hass.states.get(new.entity_id)
        if now is not None and _same(old.domain, now.state, fitted):
            continue  # already set like that
        name = old.name or (state and state.attributes.get("friendly_name")) or old.original_name or old.entity_id
        plan.append(
            {
                "entity_id": targets.get(old.entity_id, old.entity_id),
                "domain": old.domain,
                "name": str(name),
                "value": fitted,
                "source": source,
            }
        )
    return plan


def _same(domain: str, state: str, value: Any) -> bool:
    if domain == "number":
        try:
            return float(state) == float(value)
        except (TypeError, ValueError):
            return False
    return state == value


def _call(item: dict[str, Any]) -> tuple[str, str, dict[str, Any]]:
    domain, value = item["domain"], item["value"]
    if domain == "switch":
        return domain, "turn_on" if value == "on" else "turn_off", {}
    if domain == "select":
        return domain, "select_option", {"option": value}
    if domain == "number":
        return domain, "set_value", {"value": value}
    return domain, "set_value", {"value": value}


async def async_apply(hass: HomeAssistant, plan: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[str]]:
    """Set each value through the normal service. A failure is logged and skipped. Returns (done, failed ids)."""
    done, failed = [], []
    for item in plan:
        domain, service, data = _call(item)
        try:
            async with asyncio.timeout(_TIMEOUT):
                await hass.services.async_call(
                    domain, service, {"entity_id": item["entity_id"], **data}, blocking=True
                )
        except Exception:  # noqa: BLE001 - asleep, gone, or the device said no: the rest goes on
            _LOGGER.warning("Could not copy the setting %s to %s", item["value"], item["entity_id"], exc_info=True)
            failed.append(item["entity_id"])
            continue
        done.append(item)
    return done, failed
