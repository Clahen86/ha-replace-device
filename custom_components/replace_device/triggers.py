"""Translate device triggers when a device moves to another integration.

A button pressed in ZHA is `remote_button_short_press / turn_on`; the same button in Zigbee2MQTT is `action / on`.
The new device's own triggers are listed by Home Assistant, so we only have to pick the one that means the same:
first by words, then (optionally) by asking the AI. What can't be matched is left alone and reported.
"""

from __future__ import annotations

import logging
import os
import re
from typing import Any

from homeassistant.components.device_automation import DeviceAutomationType, async_get_device_automations
from homeassistant.core import HomeAssistant
from homeassistant.util.file import write_utf8_file_atomic
from homeassistant.util.yaml import dump, load_yaml

from . import ai
from .const import AUTOMATIONS_FILE

_LOGGER = logging.getLogger(__name__)

# What the words in trigger names mean, so both sides can be compared.
_WORDS: dict[str, tuple[str, ...]] = {
    "short": ("single",),
    "click": ("single",),
    "single": ("single",),
    "press": (),
    "pressed": (),
    "remote": (),
    "button": (),
    "action": (),
    "turn": (),
    "double": ("double",),
    "triple": ("triple",),
    "quadruple": ("quadruple",),
    "long": ("hold",),
    "hold": ("hold",),
    "release": ("release", "stop"),
    "released": ("release", "stop"),
    "stop": ("release", "stop"),
    "dim": ("brightness",),
    "brightness": ("brightness",),
    "on": ("on",),
    "off": ("off",),
    "up": ("up",),
    "down": ("down",),
    "left": ("left",),
    "right": ("right",),
    "drop": ("fall",),
    "fall": ("fall",),
}
# Keys of a trigger that belong to the automation, not to the device.
_OWN_KEYS = ("id", "alias", "enabled", "variables")
_MIN_SCORE = 0.5


def words(*parts: Any) -> set[str]:
    result: set[str] = set()
    for part in parts:
        for word in re.split(r"[^a-z0-9]+", str(part or "").lower()):
            if word:
                result.update(_WORDS.get(word, (word,)))
    return result


def label(trigger: dict[str, Any]) -> str:
    return " / ".join(str(trigger[k]) for k in ("type", "subtype") if trigger.get(k))


def best(old: dict[str, Any], candidates: list[dict[str, Any]]) -> dict[str, Any] | None:
    """The candidate that means the same, if one clearly does."""
    want = words(old.get("type"), old.get("subtype"))
    if not want:
        return None
    scored = sorted(
        (
            (len(want & (have := words(c.get("type"), c.get("subtype")))) / len(want | have), i)
            for i, c in enumerate(candidates)
        ),
        reverse=True,
    )
    if not scored or scored[0][0] < _MIN_SCORE or (len(scored) > 1 and scored[1][0] == scored[0][0]):
        return None
    return candidates[scored[0][1]]


async def async_translate(
    hass: HomeAssistant, new_device_id: str, old_domain: str, new_domain: str, ai_entity: str | None
) -> dict[str, list[str]]:
    """Rewrite device triggers of the old integration on the (already renamed) new device id in automations.yaml."""
    if old_domain == new_domain:
        return {"translated": [], "unresolved": []}
    path = hass.config.path(AUTOMATIONS_FILE)
    try:
        automations = await hass.async_add_executor_job(_load, path)
    except Exception:  # noqa: BLE001 - e.g. !secret in automations.yaml: don't rewrite what we can't read back
        _LOGGER.warning("Could not read %s; device triggers were not translated", path, exc_info=True)
        return {"translated": [], "unresolved": []}
    if not isinstance(automations, list):
        return {"translated": [], "unresolved": []}
    found = []
    for automation in automations:
        if not isinstance(automation, dict):
            continue
        for trigger in automation.get("triggers", automation.get("trigger")) or []:
            if (
                isinstance(trigger, dict)
                and trigger.get("device_id") == new_device_id
                and trigger.get("domain") == old_domain
            ):
                found.append((automation, trigger))
    if not found:
        return {"translated": [], "unresolved": []}

    available = (await async_get_device_automations(hass, DeviceAutomationType.TRIGGER, [new_device_id])).get(
        new_device_id, []
    )
    candidates = [dict(t) for t in available if t.get("domain") == new_domain]
    choices: dict[int, dict[str, Any] | None] = {i: best(t, candidates) for i, (_, t) in enumerate(found)}
    open_items = [i for i, choice in choices.items() if choice is None]
    if open_items and candidates and ai_entity:
        answer = await ai.async_pick_triggers(
            hass, ai_entity, [label(found[i][1]) for i in open_items], [label(c) for c in candidates]
        )
        for n, i in enumerate(open_items):
            if (pick := answer.get(n)) is not None:
                choices[i] = candidates[pick]

    translated, unresolved = [], []
    for i, (automation, trigger) in enumerate(found):
        name = automation.get("alias") or automation.get("id") or "?"
        if (choice := choices[i]) is None:
            unresolved.append(f"{name}: {label(trigger)}")
            continue
        own = {k: trigger[k] for k in _OWN_KEYS if k in trigger}
        trigger.clear()
        trigger.update(
            {"trigger": "device", **{k: v for k, v in choice.items() if k not in ("platform", "metadata")}, **own}
        )
        translated.append(f"{name}: {label(choice)}")
    if translated:
        await hass.async_add_executor_job(_save, path, automations)
    return {"translated": translated, "unresolved": unresolved}


def _load(path: str) -> Any:
    return load_yaml(path) if os.path.isfile(path) else None


def _save(path: str, data: Any) -> None:
    write_utf8_file_atomic(path, dump(data))
