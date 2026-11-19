"""Zigbee2MQTT bindings and calibration: moved from the old device to the new one when both are in Zigbee2MQTT.

Zigbee2MQTT keeps both in its retained messages: the bindings of every device in "<base>/bridge/devices" (endpoints →
bindings), and the device options such as temperature_calibration in "<base>/bridge/info" (config → devices). They
are read before the old device is removed, and made again on the new device with Zigbee2MQTT's own requests."""

from __future__ import annotations

import asyncio
import json
import logging
import re
from typing import Any

from homeassistant.core import HomeAssistant, callback

_LOGGER = logging.getLogger(__name__)
_TIMEOUT = 5
_CALIBRATION = re.compile(r"^[a-z0-9_]*calibration$")


async def async_retained(hass: HomeAssistant, topic: str) -> Any:
    """The retained JSON message on a topic, or None (MQTT not loaded, nothing retained, not JSON)."""
    if "mqtt" not in hass.config.components:
        return None
    from homeassistant.components import mqtt

    received: asyncio.Future[str] = hass.loop.create_future()

    @callback
    def _message(msg) -> None:
        if not received.done():
            received.set_result(msg.payload)

    try:
        unsubscribe = await mqtt.async_subscribe(hass, topic, _message)
    except Exception:  # noqa: BLE001 - MQTT not ready
        return None
    try:
        async with asyncio.timeout(_TIMEOUT):
            return json.loads(await received)
    except (TimeoutError, ValueError):
        return None
    finally:
        unsubscribe()


def _find(devices: list[Any], ieee: str) -> dict[str, Any] | None:
    return next(
        (d for d in devices if isinstance(d, dict) and str(d.get("ieee_address", "")).lower() == ieee.lower()), None
    )


def _clusters(device: dict[str, Any], endpoint: str, kind: str) -> set[str] | None:
    """The clusters of one endpoint ("input", "output" or both), or None when the endpoint isn't known."""
    ep = (device.get("endpoints") or {}).get(str(endpoint))
    if not isinstance(ep, dict):
        return None
    clusters = ep.get("clusters") or {}
    kinds = ("input", "output") if kind == "both" else (kind,)
    return {str(c) for k in kinds for c in clusters.get(k) or []}


def plan(
    old_ieee: str, new_ieee: str, devices: Any, info: Any, new_info: Any = None, same_network: bool = True
) -> dict[str, Any]:
    """What to bind and which calibration to copy. "missing" says why nothing could be read about the old device.

    devices, info: the old device's Zigbee2MQTT (bridge/devices, bridge/info); new_info: the new one's, if it is
    another Zigbee2MQTT instance (then nothing is bound: it is another Zigbee network)."""
    result: dict[str, Any] = {"binds": [], "skipped": [], "options": {}, "options_before": {}, "missing": None}
    devices = devices if isinstance(devices, list) else None
    config = ((info or {}).get("config") or {}) if isinstance(info, dict) else {}
    options = config.get("devices") if isinstance(config.get("devices"), dict) else None
    old = _find(devices, old_ieee) if devices is not None else None
    old_options = next((v for k, v in (options or {}).items() if k.lower() == old_ieee.lower()), None)
    if devices is None and options is None:
        result["missing"] = "no_data"
        return result
    if old is None and old_options is None:
        result["missing"] = "old_gone"
        return result

    # Calibration: device options such as temperature_calibration.
    new_config = (((new_info or {}).get("config") or {}) if isinstance(new_info, dict) else {}) or config
    new_all = new_config.get("devices") if isinstance(new_config.get("devices"), dict) else {}
    new_options = next((v for k, v in new_all.items() if k.lower() == new_ieee.lower()), None) or {}
    for key, value in (old_options or {}).items() if isinstance(old_options, dict) else []:
        if (
            _CALIBRATION.match(str(key))
            and isinstance(value, int | float)
            and not isinstance(value, bool)
            and new_options.get(key) != value
        ):
            result["options"][key] = value
            result["options_before"][key] = new_options.get(key)

    # Bindings: only within the same Zigbee network, and only where the new device has the endpoint and cluster.
    if old is None or devices is None or not same_network:
        return result
    new = _find(devices, new_ieee)
    coordinators = {
        str(d.get("ieee_address", "")).lower()
        for d in devices
        if isinstance(d, dict) and d.get("type") == "Coordinator"
    }
    names = {str(d.get("ieee_address", "")).lower(): d.get("friendly_name") for d in devices if isinstance(d, dict)}
    wanted: dict[tuple, list[str]] = {}

    def add(key: tuple, cluster: str) -> None:
        if cluster not in wanted.setdefault(key, []):
            wanted[key].append(cluster)

    # The old device bound to others (a remote bound to a bulb): the new one is bound the same way.
    for ep, data in (old.get("endpoints") or {}).items():
        for bind in (data or {}).get("bindings") or []:
            target, cluster = bind.get("target") or {}, str(bind.get("cluster") or "")
            if not cluster:
                continue
            if target.get("type") == "group" and target.get("id") is not None:
                key = (new_ieee, str(ep), "group", target["id"], None)
            elif target.get("type") == "endpoint" and target.get("ieee_address"):
                to = str(target["ieee_address"]).lower()
                if to in coordinators or to in (old_ieee.lower(), new_ieee.lower()):
                    continue  # Zigbee2MQTT binds the coordinator by itself when it sets up a device
                key = (new_ieee, str(ep), "endpoint", to, target.get("endpoint"))
            else:
                continue
            if new is None or cluster not in (_clusters(new, ep, "both") or set()):
                result["skipped"].append({"cluster": cluster, "endpoint": str(ep), "reason": "new_lacks"})
                continue
            add(key, cluster)
    # Others bound to the old device (a remote bound to the old bulb): bound to the new one instead.
    for device in devices:
        source = str((device or {}).get("ieee_address", "")).lower() if isinstance(device, dict) else ""
        if not source or source in coordinators or source in (old_ieee.lower(), new_ieee.lower()):
            continue
        for ep, data in (device.get("endpoints") or {}).items():
            for bind in (data or {}).get("bindings") or []:
                target, cluster = bind.get("target") or {}, str(bind.get("cluster") or "")
                if target.get("type") != "endpoint" or str(target.get("ieee_address", "")).lower() != old_ieee.lower():
                    continue
                to_ep = target.get("endpoint")
                if not cluster or new is None or cluster not in (_clusters(new, str(to_ep), "input") or set()):
                    result["skipped"].append({"cluster": cluster, "endpoint": str(to_ep), "reason": "new_lacks"})
                    continue
                add((source, str(ep), "endpoint", new_ieee.lower(), to_ep), cluster)

    for (source, ep, kind, to, to_ep), clusters in wanted.items():
        bind: dict[str, Any] = {"from": source, "from_endpoint": _ep(ep), "to": to, "clusters": clusters}
        if kind == "endpoint" and to_ep is not None:
            bind["to_endpoint"] = _ep(to_ep)
        bind["from_name"] = names.get(source.lower()) or source
        bind["to_name"] = names.get(str(to).lower()) or (f"group {to}" if kind == "group" else str(to))
        result["binds"].append(bind)
    return result


def _ep(value: Any) -> Any:
    try:
        return int(value)
    except (TypeError, ValueError):
        return value


def _request(bind: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in bind.items() if k in ("from", "from_endpoint", "to", "to_endpoint", "clusters")}


async def _publish(hass: HomeAssistant, topic: str, payload: dict[str, Any]) -> None:
    await hass.services.async_call("mqtt", "publish", {"topic": topic, "payload": json.dumps(payload)}, blocking=True)


async def async_apply(
    hass: HomeAssistant, base: str, new_ieee: str, todo: dict[str, Any], undo: bool = False
) -> dict[str, Any]:
    """Send the bind (undo: unbind) requests and the calibration (undo: the new device's own values).

    Zigbee2MQTT does each when the device is awake; a battery device may need a button press first."""
    done: dict[str, Any] = {"binds": [], "options": {}, "failed": []}
    if not hass.services.has_service("mqtt", "publish"):
        done["failed"].append("mqtt")
        return done
    request = "unbind" if undo else "bind"
    for bind in todo.get("binds") or []:
        try:
            await _publish(hass, f"{base}/bridge/request/device/{request}", _request(bind))
            done["binds"].append(bind)
        except Exception:  # noqa: BLE001 - logged, the rest goes on
            _LOGGER.warning("Zigbee2MQTT %s request failed: %s", request, bind, exc_info=True)
            done["failed"].append(f"{bind.get('from_name')} → {bind.get('to_name')}")
    options = todo.get("options_before" if undo else "options") or {}
    if options:
        try:
            await _publish(hass, f"{base}/bridge/request/device/options", {"id": new_ieee, "options": options})
            done["options"] = dict(options)
        except Exception:  # noqa: BLE001 - logged, the rest goes on
            _LOGGER.warning("Zigbee2MQTT options request failed", exc_info=True)
            done["failed"].append("options")
    return done
