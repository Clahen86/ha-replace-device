"""Notice a replacement by itself: a new device of the same model shows up while an old one is dead."""

from __future__ import annotations

import time

from homeassistant.const import STATE_UNAVAILABLE
from homeassistant.core import CALLBACK_TYPE, Event, HomeAssistant, callback
from homeassistant.helpers import device_registry as dr, entity_registry as er, issue_registry as ir
from homeassistant.helpers.event import async_call_later

from .const import DEAD_AFTER, DOMAIN, SUGGEST_DELAY
from .replace import device_name


def dead_twins(hass: HomeAssistant, new_id: str) -> list[dr.DeviceEntry]:
    """Dead devices of the same make and model as a new one."""
    devices = dr.async_get(hass)
    new = devices.async_get(new_id)
    if new is None or not (new.model or new.model_id):
        return []
    return [
        device
        for device in devices.devices.values()
        if device.id != new_id
        and device.manufacturer == new.manufacturer
        and ((new.model and device.model == new.model) or (new.model_id and device.model_id == new.model_id))
        and is_dead(hass, device.id)
    ]


def is_dead(hass: HomeAssistant, device_id: str) -> bool:
    """Every entity that has a state has been unavailable for at least an hour."""
    entries = er.async_entries_for_device(er.async_get(hass), device_id)
    if not entries:
        return False
    now = time.time()
    states = [s for entry in entries if (s := hass.states.get(entry.entity_id)) is not None]
    return bool(states) and all(
        s.state == STATE_UNAVAILABLE and now - s.last_changed_timestamp >= DEAD_AFTER for s in states
    )


@callback
def async_watch(hass: HomeAssistant) -> CALLBACK_TYPE:
    """Look for a dead twin two minutes after a device is added."""
    timers: list[CALLBACK_TYPE] = []

    @callback
    def _added(event: Event[dr.EventDeviceRegistryUpdatedData]) -> None:
        if event.data["action"] != "create":
            return
        device_id = event.data["device_id"]

        @callback
        def _look(_now) -> None:
            async_suggest(hass, device_id)

        timers.append(async_call_later(hass, SUGGEST_DELAY, _look))

    unsub = hass.bus.async_listen(dr.EVENT_DEVICE_REGISTRY_UPDATED, _added)

    @callback
    def _stop() -> None:
        unsub()
        for timer in timers:
            timer()

    return _stop


@callback
def async_suggest(hass: HomeAssistant, new_id: str) -> None:
    twins = dead_twins(hass, new_id)
    new = dr.async_get(hass).async_get(new_id)
    if not twins or new is None:
        return
    ir.async_create_issue(
        hass,
        DOMAIN,
        f"suggest_{new_id}",
        is_fixable=True,
        severity=ir.IssueSeverity.WARNING,
        translation_key="suggest" if len(twins) == 1 else "suggest_many",
        translation_placeholders={"new": device_name(new), "old": device_name(twins[0]), "count": str(len(twins))},
        data={"new": new_id, "candidates": [d.id for d in twins]},
    )
