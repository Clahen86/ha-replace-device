"""Translate device triggers when a device moves to another integration.

A button pressed in ZHA is `remote_button_short_press / turn_on`; the same button in Zigbee2MQTT is `action / on`.
The new device's own triggers are listed by Home Assistant, so we only have to pick the one that means the same:
first by words, then (optionally) by asking the AI. What can't be matched is left alone and reported.
"""

from __future__ import annotations

from dataclasses import dataclass
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
from .hardware import async_z2m_actions

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
    # ZHA commands of IKEA-style remotes.
    "move": ("hold", "brightness"),
    "with": (),
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
    # "long_release" is the end of a hold, not a hold.
    if "release" in result:
        result.discard("hold")
    return result


def label(trigger: dict[str, Any]) -> str:
    return " / ".join(str(trigger[k]) for k in ("type", "subtype") if trigger.get(k))


def same_button(old: dict[str, Any], candidate: dict[str, Any]) -> bool:
    """Numbers name buttons ("button_1", "2_short_release"): button 1 is never button 2."""
    old_digits = {w for w in words(old.get("type"), old.get("subtype")) if w.isdigit()}
    new_digits = {w for w in words(candidate.get("type"), candidate.get("subtype")) if w.isdigit()}
    return not old_digits or not new_digits or old_digits == new_digits


def best(old: dict[str, Any], candidates: list[dict[str, Any]]) -> dict[str, Any] | None:
    """The candidate that means the same, if one clearly does."""
    want = words(old.get("type"), old.get("subtype"))
    candidates = [c for c in candidates if same_button(old, c)]
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


@dataclass
class Moved:
    """What is known about the device before and after, to recognise everything that listens to it."""

    new_device_id: str
    old_domain: str | None
    new_domain: str | None
    # ZHA events carry the IEEE address ("54:ef:44:…"); Zigbee2MQTT topics carry the name or the 0x address.
    old_ieee: str | None = None
    old_z2m_name: str | None = None
    old_z2m_ieee: str | None = None
    old_base: str | None = None
    new_z2m_name: str | None = None
    new_base: str | None = None
    new_z2m_ieee: str | None = None
    # "IKEA SOMRIG in ZHA → IKEA SOMRIG in Zigbee2MQTT", for the AI.
    context: str = ""


async def async_translate(hass: HomeAssistant, moved: Moved, ai_entity: str | None) -> dict[str, list[str]]:
    """Rewrite what listens to the old integration in automations.yaml: device triggers, ZHA events, Zigbee2MQTT
    topics, and blueprint inputs meant for the old integration. Entity triggers need nothing: the ids stay."""
    empty: dict[str, list[str]] = {"translated": [], "unresolved": []}
    if moved.old_domain == moved.new_domain:
        return empty
    path = hass.config.path(AUTOMATIONS_FILE)
    try:
        automations = await hass.async_add_executor_job(_load, path)
    except Exception:  # noqa: BLE001 - e.g. !secret in automations.yaml: don't rewrite what we can't read back
        _LOGGER.warning("Could not read %s; device triggers were not translated", path, exc_info=True)
        return empty
    if not isinstance(automations, list):
        return empty

    translated: list[str] = []
    unresolved: list[str] = []
    ai_error: str | None = None
    found = []
    for automation in automations:
        if not isinstance(automation, dict):
            continue
        name = automation.get("alias") or automation.get("id") or "?"
        if isinstance(automation.get("use_blueprint"), dict):
            result = await hass.async_add_executor_job(_blueprint, hass.config.path(), automation, moved)
            if result is True:
                translated.append(f"{name}: blueprint")
            elif result:
                unresolved.append(f"{name}: blueprint ({result})")
            continue
        for trigger in automation.get("triggers", automation.get("trigger")) or []:
            if isinstance(trigger, dict) and (meaning := _old_meaning(trigger, moved)) is not None:
                found.append((name, trigger, meaning))

    if found:
        available = (await async_get_device_automations(hass, DeviceAutomationType.TRIGGER, [moved.new_device_id])).get(
            moved.new_device_id, []
        )
        candidates = [dict(t) for t in available if t.get("domain") == moved.new_domain]
        if moved.new_z2m_ieee and moved.new_base:
            known = {c.get("subtype") for c in candidates}
            candidates += [
                {"domain": "mqtt", "device_id": moved.new_device_id, "type": "action", "subtype": action}
                for action in await async_z2m_actions(hass, moved.new_base, moved.new_z2m_ieee)
                if action not in known
            ]
        choices: dict[int, dict[str, Any] | None] = {i: best(m, candidates) for i, (_, _, m) in enumerate(found)}
        open_items = [i for i, choice in choices.items() if choice is None]
        answer: dict[int, int] = {}
        if open_items and candidates and ai_entity:
            try:
                answer = await ai.async_pick_triggers(
                    hass,
                    ai_entity,
                    [label(found[i][2]) for i in open_items],
                    [label(c) for c in candidates],
                    moved.context,
                )
            except ai.AiError as err:
                ai_error = str(err)
            for n, i in enumerate(open_items):
                if (pick := answer.get(n)) is not None and same_button(found[i][2], candidates[pick]):
                    choices[i] = candidates[pick]
        # Two different presses never become the same one: that was a guess, so ask the user instead.
        taken: dict[tuple[str, str], set[str]] = {}
        for i, (name, _, meaning) in enumerate(found):
            if choices[i] is not None:
                taken.setdefault((name, label(choices[i])), set()).add(label(meaning))
        for i, (name, _, _) in enumerate(found):
            if choices[i] is not None and len(taken[(name, label(choices[i]))]) > 1:
                choices[i] = None
        for i, (name, trigger, meaning) in enumerate(found):
            if (choice := choices[i]) is None:
                unresolved.append(f"{name}: {label(meaning)}")
                continue
            own = {k: trigger[k] for k in _OWN_KEYS if k in trigger}
            trigger.clear()
            trigger.update(
                {"trigger": "device", **{k: v for k, v in choice.items() if k not in ("platform", "metadata")}, **own}
            )
            translated.append(f"{name}: {label(choice)}")

    if translated:
        await hass.async_add_executor_job(_save, path, automations)
    result: dict[str, Any] = {"translated": translated, "unresolved": unresolved}
    if ai_error:
        result["ai_error"] = ai_error
    return result


def _old_meaning(trigger: dict[str, Any], moved: Moved) -> dict[str, Any] | None:
    """What a trigger listening to the old integration fires on, as {"type", "subtype"}; None if it doesn't."""
    kind = trigger.get("trigger") or trigger.get("platform")
    if (
        kind == "device"
        and trigger.get("device_id") == moved.new_device_id
        and trigger.get("domain") == moved.old_domain
    ):
        return trigger
    if kind == "event" and trigger.get("event_type") == "zha_event":
        data = trigger.get("event_data") or {}
        if data.get("device_id") == moved.new_device_id or (
            moved.old_ieee and data.get("device_ieee") == moved.old_ieee
        ):
            return {
                "type": data.get("command"),
                "subtype": data.get("args") if isinstance(data.get("args"), str) else "",
            }
    if kind == "mqtt" and moved.old_base:
        topics = {f"{moved.old_base}/{n}/action" for n in (moved.old_z2m_name, moved.old_z2m_ieee) if n}
        if trigger.get("topic") in topics:
            return {"type": "action", "subtype": trigger.get("payload")}
    return None


def _blueprint(config_dir: str, automation: dict[str, Any], moved: Moved) -> bool | str | None:
    """Move blueprint inputs meant for the old integration to the ones for the new integration.

    True when changed, a short reason when an input is for the old integration but there is no input to move it to,
    None when the blueprint has nothing to do with the device."""
    use = automation["use_blueprint"]
    inputs = use.get("input") or {}
    try:
        blueprint = load_yaml(os.path.join(config_dir, "blueprints", "automation", str(use.get("path"))))
        schema = _flat_inputs(blueprint["blueprint"]["input"])
    except Exception:  # noqa: BLE001 - missing or unreadable blueprint
        return None
    old_keys = [
        key
        for key, value in inputs.items()
        if (value == moved.new_device_id and _device_filter(schema.get(key)) not in (None, "", moved.new_domain))
        or (moved.old_z2m_name and value == moved.old_z2m_name and _is_z2m_text(key, schema.get(key)))
    ]
    if not old_keys:
        return None
    new_values: dict[str, Any] = {}
    for key, spec in schema.items():
        if key in old_keys:
            continue
        if _device_filter(spec) == moved.new_domain:
            new_values[key] = moved.new_device_id
        elif moved.new_z2m_name and _is_z2m_text(key, spec):
            new_values[key] = moved.new_base if _is_topic(key, spec) else moved.new_z2m_name
    if not new_values:
        return ", ".join(old_keys)
    for key in old_keys:
        inputs.pop(key, None)
    if moved.new_z2m_name is None:
        # Moving away from Zigbee2MQTT: its name and topic inputs don't apply any more.
        for key, spec in schema.items():
            if _is_z2m_text(key, spec):
                inputs.pop(key, None)
    inputs.update(new_values)
    use["input"] = inputs
    return True


def _flat_inputs(inputs: dict[str, Any]) -> dict[str, Any]:
    flat: dict[str, Any] = {}
    for key, value in (inputs or {}).items():
        if isinstance(value, dict) and isinstance(value.get("input"), dict):
            flat.update(value["input"])
        else:
            flat[key] = value or {}
    return flat


def _device_filter(spec: Any) -> str | None:
    """The integration a device input is limited to ("" when it is a device input without one, None otherwise)."""
    selector = (spec or {}).get("selector") or {}
    if "device" not in selector:
        return None
    filters = (selector["device"] or {}).get("filter") or (selector["device"] or {}).get("integration") or []
    for item in filters if isinstance(filters, list) else [filters]:
        if isinstance(item, dict) and item.get("integration"):
            return item["integration"]
        if isinstance(item, str):
            return item
    return ""


def _text(key: str, spec: Any) -> str:
    spec = spec or {}
    return f"{key} {spec.get('name', '')} {spec.get('description', '')}".lower()


def _is_z2m_text(key: str, spec: Any) -> bool:
    """A text input for Zigbee2MQTT: its name or its base topic."""
    if "device" in ((spec or {}).get("selector") or {}):
        return False
    text = _text(key, spec)
    return any(w in text for w in ("zigbee2mqtt", "z2m", "mqtt")) and (
        _is_topic(key, spec) or any(w in text for w in ("name", "friendly", "remote", "controller", "device"))
    )


def _is_topic(key: str, spec: Any) -> bool:
    return "topic" in _text(key, spec)


def _load(path: str) -> Any:
    return load_yaml(path) if os.path.isfile(path) else None


def _save(path: str, data: Any) -> None:
    write_utf8_file_atomic(path, dump(data))
