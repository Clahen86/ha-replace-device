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
from homeassistant.util.yaml import dump, load_yaml, parse_yaml

from . import ai
from .const import AUTOMATIONS_FILE, SCRIPTS_FILE
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
        # "button1" is the word "button" and the number 1 (Shelly), like "button_1" (ZHA).
        for word in re.findall(r"[a-z]+|\d+", str(part or "").lower()):
            if word:
                result.update(_WORDS.get(word, (word,)))
    # "long_release" is the end of a hold, not a hold.
    if "release" in result:
        result.discard("hold")
    return result


# Fields that only say where a trigger belongs, not what it fires on.
_PLACE_KEYS = {"platform", "trigger", "domain", "device_id", "entity_id", "metadata", "discovery_id", "id", "alias"}


def label(trigger: dict[str, Any]) -> str:
    """'remote_button_short_press / button_1', plus any other field that tells triggers apart (Z-Wave scenes)."""
    main = " / ".join(str(trigger[k]) for k in ("type", "subtype") if trigger.get(k) not in (None, ""))
    extra = ", ".join(
        f"{k}: {v}" for k, v in trigger.items() if k not in _PLACE_KEYS | {"type", "subtype"} and v not in (None, "")
    )
    return f"{main} ({extra})" if extra else main


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


async def async_translate(
    hass: HomeAssistant,
    moved: Moved,
    ai_entity: str | None,
    ids: dict[str, str] | None = None,
    cache: dict[tuple, dict[int, int]] | None = None,
) -> dict[str, Any]:
    """Rewrite what listens to the old integration: device triggers (also in wait_for_trigger), ZHA events,
    Zigbee2MQTT topics, and blueprint inputs meant for the old integration. Entity triggers need nothing: the ids
    stay. automations.yaml and scripts.yaml are written by the editors and rewritten; packages are the user's own
    files, so what would change there is listed to do by hand instead.

    With ids (old registry id -> new) it is a dry run: the files are read as the replacement would have left them,
    and nothing is saved. cache keeps the AI's answers, so a dry run and the replacement ask only once."""
    empty: dict[str, Any] = {"translated": [], "unresolved": [], "changes": [], "saved": []}
    if moved.old_domain == moved.new_domain:
        return empty
    places = await hass.async_add_executor_job(_places, hass.config.path(), ids)

    translated: list[str] = []
    unresolved: list[str] = []
    # Before -> after, for the dry run; by_hand when it is in a package.
    changes: list[dict[str, Any]] = []
    dirty: set[str] = set()
    ai_error: str | None = None
    found = []
    for place in places:
        for kind, name, item in place.items:
            if isinstance(item.get("use_blueprint"), dict):
                result = await hass.async_add_executor_job(_blueprint, hass.config.path(), item, moved, kind)
                if result is True:
                    change = {"automation": name, "before": f"blueprint: {moved.old_domain}"}
                    change["after"] = f"blueprint: {moved.new_domain}"
                    if place.writable:
                        translated.append(f"{name}: blueprint")
                        dirty.add(place.path)
                    else:
                        change["by_hand"] = place.label
                        unresolved.append(f"{name} ({place.label}): blueprint")
                    changes.append(change)
                elif result:
                    unresolved.append(f"{name}: blueprint ({result})")
                continue
            for trigger in _triggers_in(item):
                if (meaning := _old_meaning(trigger, moved)) is not None:
                    found.append((name, trigger, meaning, place))

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
        choices: dict[int, dict[str, Any] | None] = {i: best(f[2], candidates) for i, f in enumerate(found)}
        open_items = [i for i, choice in choices.items() if choice is None]
        answer: dict[int, int] = {}
        if open_items and candidates and ai_entity:
            old_labels = [label(found[i][2]) for i in open_items]
            new_labels = [label(c) for c in candidates]
            key = (moved.new_device_id, tuple(old_labels), tuple(new_labels))
            if cache is not None and key in cache:
                answer = cache[key]
            else:
                try:
                    answer = await ai.async_pick_triggers(hass, ai_entity, old_labels, new_labels, moved.context)
                    if cache is not None:
                        cache[key] = answer
                except ai.AiError as err:
                    ai_error = str(err)
            for n, i in enumerate(open_items):
                if (pick := answer.get(n)) is not None and same_button(found[i][2], candidates[pick]):
                    choices[i] = candidates[pick]
        # Two different presses never become the same one: that was a guess, so ask the user instead.
        taken: dict[tuple[str, str], set[str]] = {}
        for i, (name, _, meaning, _) in enumerate(found):
            if choices[i] is not None:
                taken.setdefault((name, label(choices[i])), set()).add(label(meaning))
        for i, (name, _, _, _) in enumerate(found):
            if choices[i] is not None and len(taken[(name, label(choices[i]))]) > 1:
                choices[i] = None
        for i, (name, trigger, meaning, place) in enumerate(found):
            if (choice := choices[i]) is None:
                unresolved.append(f"{name}: {label(meaning)}")
                continue
            before = label(meaning)  # a device trigger is its own meaning, and is changed in place below
            if not place.writable:
                unresolved.append(f"{name} ({place.label}): {before} → {label(choice)}")
                changes.append({"automation": name, "before": before, "after": label(choice), "by_hand": place.label})
                continue
            own = {k: trigger[k] for k in _OWN_KEYS if k in trigger}
            trigger.clear()
            trigger.update(
                {"trigger": "device", **{k: v for k, v in choice.items() if k not in ("platform", "metadata")}, **own}
            )
            translated.append(f"{name}: {label(choice)}")
            changes.append({"automation": name, "before": before, "after": label(choice)})
            dirty.add(place.path)

    saved = []
    if ids is None:
        for place in places:
            if place.path in dirty:
                await hass.async_add_executor_job(_save, place.path, place.data)
                saved.append(place.domain)
    result: dict[str, Any] = {"translated": translated, "unresolved": unresolved, "changes": changes, "saved": saved}
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


@dataclass
class _Place:
    """A file with automations or scripts in it."""

    path: str
    label: str
    domain: str
    data: Any
    writable: bool
    # (kind, name, automation or script)
    items: list[tuple[str, str, dict[str, Any]]]


def _places(config_dir: str, ids: dict[str, str] | None) -> list[_Place]:
    """automations.yaml and scripts.yaml (written by the editors), and the automations and scripts in packages/."""
    places = []

    def read(path: str) -> Any:
        try:
            return _load(path, ids)
        except Exception:  # noqa: BLE001 - e.g. !secret: don't rewrite what we can't read back
            _LOGGER.warning("Could not read %s; its device triggers were not translated", path, exc_info=True)
            return None

    automations = read(os.path.join(config_dir, AUTOMATIONS_FILE))
    if isinstance(automations, list):
        items = [("automation", _name(a), a) for a in automations if isinstance(a, dict)]
        path = os.path.join(config_dir, AUTOMATIONS_FILE)
        places.append(_Place(path, AUTOMATIONS_FILE, "automation", automations, True, items))
    scripts = read(os.path.join(config_dir, SCRIPTS_FILE))
    if isinstance(scripts, dict):
        items = [("script", _name(v, k), v) for k, v in scripts.items() if isinstance(v, dict)]
        places.append(_Place(os.path.join(config_dir, SCRIPTS_FILE), SCRIPTS_FILE, "script", scripts, True, items))
    for root, _dirs, names in os.walk(os.path.join(config_dir, "packages")):
        for file in sorted(n for n in names if n.endswith((".yaml", ".yml"))):
            path = os.path.join(root, file)
            data = read(path)
            if not isinstance(data, dict):
                continue
            items = []
            for key, value in data.items():
                kind = str(key).split(" ")[0]
                if kind == "automation":
                    for a in value if isinstance(value, list) else [value]:
                        if isinstance(a, dict):
                            items.append(("automation", _name(a), a))
                elif kind == "script" and isinstance(value, dict):
                    items += [("script", _name(v, k), v) for k, v in value.items() if isinstance(v, dict)]
            if items:
                places.append(_Place(path, os.path.relpath(path, config_dir), "", data, False, items))
    return places


def _name(item: dict[str, Any], key: str = "") -> str:
    return str(item.get("alias") or key or item.get("id") or "?")


def _triggers_in(item: dict[str, Any]) -> list[dict[str, Any]]:
    """An automation's triggers, and the triggers of every wait_for_trigger in its actions or a script's sequence."""
    found = [t for t in item.get("triggers", item.get("trigger")) or [] if isinstance(t, dict)]

    def walk(value: Any) -> None:
        if isinstance(value, dict):
            for key, inner in value.items():
                if key == "wait_for_trigger":
                    found.extend(t for t in (inner if isinstance(inner, list) else [inner]) if isinstance(t, dict))
                else:
                    walk(inner)
        elif isinstance(value, list):
            for inner in value:
                walk(inner)

    walk({k: v for k, v in item.items() if k not in ("triggers", "trigger")})
    return found


def _blueprint(config_dir: str, automation: dict[str, Any], moved: Moved, kind: str = "automation") -> bool | str | None:
    """Move blueprint inputs meant for the old integration to the ones for the new integration.

    True when changed, a short reason when an input is for the old integration but there is no input to move it to,
    None when the blueprint has nothing to do with the device."""
    use = automation["use_blueprint"]
    inputs = use.get("input") or {}
    try:
        blueprint = load_yaml(os.path.join(config_dir, "blueprints", kind, str(use.get("path"))))
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


def _load(path: str, ids: dict[str, str] | None = None) -> Any:
    if not os.path.isfile(path):
        return None
    if ids is None:
        return load_yaml(path)
    with open(path, encoding="utf-8") as file:
        text = file.read()
    for old_id, new_id in ids.items():
        text = text.replace(old_id, new_id)
    return parse_yaml(text)


def _save(path: str, data: Any) -> None:
    write_utf8_file_atomic(path, dump(data))
