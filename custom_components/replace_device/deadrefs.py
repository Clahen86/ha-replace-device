"""Dead references: entity IDs that automations, scripts, scenes and dashboards still use, but that are gone.

For each one the best replacement is suggested (same kind of entity with a similar name, e.g. "…_2" after a device
was paired again). Nothing is changed here: the panel shows it, and the user moves each reference with the same
fix as when an entity ID changes by itself (with undo), or removes a forgotten entity.
"""

from __future__ import annotations

import difflib
import re
from typing import Any

from homeassistant.const import ATTR_FRIENDLY_NAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from . import references

_ID = re.compile(r"^([a-z_]+)\.([a-z0-9_]+)$")
_SUFFIX = re.compile(r"_\d{1,2}$")
# Domains that hold entities; other "x.y" strings in a dashboard (icons, card types …) are not references.
_DOMAINS = {
    "alarm_control_panel", "binary_sensor", "button", "calendar", "camera", "climate", "counter", "cover",
    "date", "datetime", "device_tracker", "event", "fan", "humidifier", "image", "input_boolean", "input_button",
    "input_datetime", "input_number", "input_select", "input_text", "lawn_mower", "light", "lock", "media_player",
    "number", "person", "remote", "scene", "script", "select", "sensor", "siren", "switch", "text", "time",
    "timer", "todo", "update", "vacuum", "valve", "water_heater", "weather", "zone", "automation", "group", "sun",
}
MIN_SCORE = 0.55
SURE = 0.9


def _walk(value: Any, found: set[str]) -> None:
    if isinstance(value, str):
        for part in value.split(","):
            if (m := _ID.match(part.strip())) and m[1] in _DOMAINS:
                found.add(part.strip())
    elif isinstance(value, dict):
        for v in value.values():
            _walk(v, found)
    elif isinstance(value, list):
        for v in value:
            _walk(v, found)


async def _uses(hass: HomeAssistant) -> dict[str, list[dict[str, str]]]:
    """entity_id -> where it is used: [{kind, name, id}]."""
    from homeassistant.components.automation import entities_in_automation
    from homeassistant.components.homeassistant.scene import entities_in_scene
    from homeassistant.components.script import entities_in_script

    uses: dict[str, list[dict[str, str]]] = {}

    def add(entity_id: str, kind: str, name: str, ref: str) -> None:
        # Templates and odd values can turn up as "entities": only real entity IDs count.
        if isinstance(entity_id, str) and entity_id != ref and _ID.match(entity_id):
            uses.setdefault(entity_id, []).append({"kind": kind, "name": name, "id": ref})

    for kind, finder in (("automation", entities_in_automation), ("script", entities_in_script), ("scene", entities_in_scene)):
        for state in hass.states.async_all(kind):
            try:
                ids = finder(hass, state.entity_id)
            except Exception:  # noqa: BLE001 - one broken item doesn't stop the scan
                continue
            for entity_id in ids:
                add(entity_id, kind, state.attributes.get(ATTR_FRIENDLY_NAME) or state.entity_id, state.entity_id)
    for title, _dashboard, config in await references.async_dashboards(hass):
        found: set[str] = set()
        _walk(config, found)
        for entity_id in found:
            add(entity_id, "dashboard", title, title)
    return uses


def _status(hass: HomeAssistant, registry: er.EntityRegistry, entity_id: str) -> str | None:
    """"missing" (gone everywhere), "orphan" (only a leftover in the entity registry) or None (alive)."""
    state = hass.states.get(entity_id)
    entry = registry.async_get(entity_id)
    if entry is None and state is None:
        return "missing"
    if entry is not None and (state is None or state.attributes.get("restored")):
        return "orphan"
    return None


_DIGITS = re.compile(r"\d+")


def _words(obj: str) -> list[str]:
    return [w for w in _DIGITS.sub("", obj).split("_") if len(w) >= 3]


def _same_word(a: str, words: list[str]) -> bool:
    return any(difflib.SequenceMatcher(None, a, b).ratio() >= 0.8 for b in words)


def _distinct(old: str, new: str) -> bool:
    """Two different things with similar names: "lamp1" and "lamp2", "oliwer_power" and "wictor_power".
    The "_2" a device gets when paired again doesn't count."""
    old, new = _SUFFIX.sub("", old), _SUFFIX.sub("", new)
    if _DIGITS.findall(old) != _DIGITS.findall(new):
        return True
    a, b = _words(old), _words(new)
    return any(not _same_word(w, b) for w in a) and any(not _same_word(w, a) for w in b)


def _label(entity_id: str) -> str:
    return entity_id.split(".", 1)[1].replace("_", " ")


def _candidates(hass: HomeAssistant, registry: er.EntityRegistry, entity_id: str, alive: list[str]) -> list[dict[str, Any]]:
    """The best replacements, most likely first, with how sure (0-1)."""
    domain, obj = entity_id.split(".", 1)
    base = _SUFFIX.sub("", obj)
    old_entry = registry.async_get(entity_id)
    old_name = ((old_entry and (old_entry.name or old_entry.original_name)) or _label(entity_id)).lower()
    old_class = old_entry and (old_entry.device_class or old_entry.original_device_class)
    old_unit = old_entry and old_entry.unit_of_measurement
    scored = []
    for other in alive:
        if not other.startswith(domain + "."):
            continue
        o_obj = other.split(".", 1)[1]
        state = hass.states.get(other)
        name = str((state and state.attributes.get(ATTR_FRIENDLY_NAME)) or _label(other)).lower()
        score = max(
            difflib.SequenceMatcher(None, obj, o_obj).ratio(),
            difflib.SequenceMatcher(None, base, _SUFFIX.sub("", o_obj)).ratio() * 0.97,
            difflib.SequenceMatcher(None, old_name, name).ratio() * 0.95,
        )
        if _SUFFIX.sub("", o_obj) == base:
            score = max(score, 0.97)  # "sensor.kitchen_2" for "sensor.kitchen": the device came back as new
        elif _distinct(obj, o_obj):
            score = min(score, 0.7)  # a different lamp, person or room: never a "sure" match
        if state is not None:
            if old_class and state.attributes.get("device_class") not in (None, old_class):
                score -= 0.25
            if old_unit and state.attributes.get("unit_of_measurement") not in (None, old_unit):
                score -= 0.25
        if score >= MIN_SCORE:
            scored.append((score, other, name))
    scored.sort(reverse=True)
    return [{"entity_id": e, "name": n, "score": round(s, 2)} for s, e, n in scored[:3]]


async def async_scan(hass: HomeAssistant, ignored: list[str]) -> list[dict[str, Any]]:
    """Every dead reference: where it's used, what it is, and the best replacements."""
    registry = er.async_get(hass)
    uses = await _uses(hass)
    alive = [s.entity_id for s in hass.states.async_all() if not s.attributes.get("restored")]
    result = []
    for entity_id, where in uses.items():
        status = _status(hass, registry, entity_id)
        if status is None:
            continue
        entry = registry.async_get(entity_id)
        seen: set[tuple[str, str]] = set()
        places = [w for w in where if (w["kind"], w["id"]) not in seen and not seen.add((w["kind"], w["id"]))]
        result.append(
            {
                "entity_id": entity_id,
                "status": status,
                "name": (entry and (entry.name or entry.original_name)) or _label(entity_id),
                "platform": entry.platform if entry else None,
                "used_in": places,
                "candidates": _candidates(hass, registry, entity_id, alive),
                "ignored": entity_id in ignored,
            }
        )
    # One live entity can't be the sure replacement for several dead ones (five bulbs -> one group light).
    best: dict[str, list[dict]] = {}
    for r in result:
        if r["candidates"] and r["candidates"][0]["score"] >= SURE:
            best.setdefault(r["candidates"][0]["entity_id"], []).append(r)
    for refs in best.values():
        if len(refs) > 1:
            for r in refs:
                r["candidates"][0]["score"] = min(r["candidates"][0]["score"], 0.75)
    order = {"automation": 0, "script": 1, "scene": 2, "dashboard": 3}
    result.sort(key=lambda r: (r["ignored"], min(order.get(u["kind"], 9) for u in r["used_in"]),
                               -(r["candidates"][0]["score"] if r["candidates"] else 0), r["entity_id"]))
    return result


def async_remove_orphan(hass: HomeAssistant, entity_id: str) -> bool:
    """Remove a forgotten entity (only a leftover in the registry, nothing provides it any more)."""
    registry = er.async_get(hass)
    if _status(hass, registry, entity_id) != "orphan":
        return False
    registry.async_remove(entity_id)
    return True
