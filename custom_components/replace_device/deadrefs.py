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


def _walk(value: Any, found: set[str], hints: dict[str, dict[str, set[str]]] | None = None, view: str = "") -> None:
    """Entity IDs in a dashboard; hints get the card's own name for it ("name: Bathroom ceiling") and the view."""
    if isinstance(value, str):
        for part in value.split(","):
            if (m := _ID.match(part.strip())) and m[1] in _DOMAINS:
                found.add(part.strip())
                if hints is not None and view:
                    hints.setdefault(part.strip(), {"names": set(), "views": set()})["views"].add(view)
    elif isinstance(value, dict):
        if "cards" in value or "sections" in value or "badges" in value:
            view = str(value.get("title") or view)  # a view (or a titled stack) - often a room
        entity = value.get("entity")
        if hints is not None and isinstance(entity, str) and isinstance(value.get("name"), str) and _ID.match(entity):
            hints.setdefault(entity, {"names": set(), "views": set()})["names"].add(value["name"])
        for v in value.values():
            _walk(v, found, hints, view)
    elif isinstance(value, list):
        for v in value:
            _walk(v, found, hints, view)


async def _uses(
    hass: HomeAssistant, hints: dict[str, dict[str, set[str]]] | None = None
) -> dict[str, list[dict[str, str]]]:
    """entity_id -> where it is used: [{kind, name, id}]. hints: names and views the dashboards give it."""
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
        _walk(config, found, hints, title)  # a dashboard per room ("Soveværelse") is a room too
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
    return [w for w in _DIGITS.sub("", obj).split("_") if len(w) >= 2]


def _same_word(a: str, words: list[str]) -> bool:
    if len(a) < 4:
        return a in words  # "tv", "led": only the exact word
    return any(difflib.SequenceMatcher(None, a, b).ratio() >= 0.8 for b in words)


# Extra entities a device has besides the main one: never the replacement for something that wasn't one too.
_SIDE = {"batteri", "battery", "linkquality", "signal", "rssi", "spaending", "voltage", "lqi", "firmware", "update",
         "identify", "identificer"}


_DANSK = str.maketrans({"æ": "ae", "ø": "oe", "å": "aa", " ": "_", "-": "_"})


def _norm(text: str) -> str:
    return re.sub(r"[^a-z0-9_]", "", str(text).lower().translate(_DANSK))


def _same_numbers(old: str, new: str) -> bool:
    """"kaelder3_2" and "kaelder_paere_3" are both number 3 (the "_2" is from pairing again)."""
    want = _DIGITS.findall(_SUFFIX.sub("", old))
    return want in (_DIGITS.findall(new), _DIGITS.findall(_SUFFIX.sub("", new)))


def _covers(old: str, new_words: list[str]) -> float:
    """Share of the old ID's words found in the new entity (ID and name) - 1.0 when every word is there."""
    words = _words(_SUFFIX.sub("", old))
    return sum(_same_word(w, new_words) for w in words) / len(words) if words else 0.0


def _distinct(old: str, new: str) -> bool:
    """Two different things with similar names: "lamp1" and "lamp2", "oliwer_power" and "wictor_power".
    The "_2" a device gets when paired again doesn't count."""
    if not _same_numbers(old, new):
        return True
    a, b = _words(_SUFFIX.sub("", old)), _words(_SUFFIX.sub("", new))
    return any(not _same_word(w, b) for w in a) and any(not _same_word(w, a) for w in b)


def _label(entity_id: str) -> str:
    return entity_id.split(".", 1)[1].replace("_", " ")


def _area_of(hass: HomeAssistant, registry: er.EntityRegistry, entity_id: str) -> str:
    from homeassistant.helpers import area_registry as ar, device_registry as dr

    entry = registry.async_get(entity_id)
    if entry is None:
        return ""
    area_id = entry.area_id or (
        (d := dr.async_get(hass).async_get(entry.device_id)) and d.area_id if entry.device_id else None
    )
    area = ar.async_get(hass).async_get_area(area_id) if area_id else None
    return area.name.lower() if area else ""


def _pool(hass: HomeAssistant, registry: er.EntityRegistry) -> list[dict[str, Any]]:
    """A snapshot of the live entities, so the comparing can run outside the event loop."""
    pool = []
    for state in hass.states.async_all():
        if state.attributes.get("restored"):
            continue
        obj = state.object_id
        name = str(state.attributes.get(ATTR_FRIENDLY_NAME) or _label(state.entity_id)).lower()
        pool.append({
            "entity_id": state.entity_id, "domain": state.domain, "obj": obj, "base": _SUFFIX.sub("", obj),
            "name": name, "words": _words(obj) + _words(_norm(name)), "area": _area_of(hass, registry, state.entity_id),
            "device_class": state.attributes.get("device_class"), "unit": state.attributes.get("unit_of_measurement"),
        })
    return pool


def _candidates(old: dict[str, Any], pool: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """The best replacements, most likely first, with how sure (0-1). old: the dead ID with what is known about it,
    and the dashboard's own name for it and the views (rooms) it is in - often the best clue. Pure: runs in a thread."""
    domain, obj = old["entity_id"].split(".", 1)
    base = _SUFFIX.sub("", obj)
    old_name, old_words = old["name"].lower(), _words(obj)
    old.setdefault("rooms", set())
    names = [n.lower() for n in old["card_names"]]
    views = {v.lower() for v in old["views"]}
    scored = []
    for c in pool:
        if c["domain"] != domain:
            continue
        o_obj, name, new_words = c["obj"], c["name"], c["words"]
        # Quick filter: nothing in common at all - not worth comparing.
        if not (set(old_words) & set(new_words)) and not names and difflib.SequenceMatcher(None, obj, o_obj).quick_ratio() < 0.6:
            continue
        score = max(
            difflib.SequenceMatcher(None, obj, o_obj).ratio(),
            difflib.SequenceMatcher(None, base, c["base"]).ratio() * 0.97,
            difflib.SequenceMatcher(None, old_name, name).ratio() * 0.95,
        )
        # The card's own name ("Badeværelse loft") against the live entity's name.
        named = max((difflib.SequenceMatcher(None, n, name).ratio() for n in names), default=0)
        # Every word of the old ID in the new one's ID or name, with the same number: "gang_kaelder3_2" ->
        # "gang_kaelder_paere_3", "…_sensor_tilstedevaerelse" -> "…_sensor_occupancy" (named "… tilstedeværelse").
        covered = _covers(obj, new_words) if _same_numbers(obj, o_obj) else 0.0
        if c["base"] == base:
            score = max(score, 0.97)  # "sensor.kitchen_2" for "sensor.kitchen": the device came back as new
        elif named >= 0.9:
            score = max(score, named * 0.96)  # the dashboard calls it exactly that
        elif covered == 1.0 and len(_words(base)) >= 2:
            extra = len(set(new_words) - set(old_words))
            score = max(score, 0.95 - min(extra, 6) * 0.01)  # all the words, same number; fewer extra words first
        elif _distinct(obj, o_obj):
            score = min(score, 0.7)  # a different lamp, person or room: never a "sure" match
        else:
            score = max(score, named * 0.9)
        if (_SIDE & set(new_words)) and not (_SIDE & set(old_words)):
            score -= 0.25  # "…_batteri" for a door sensor: a side entity of the device, not the device
        if views and c["area"] and any(c["area"] in v or v in c["area"] for v in views):
            score += 0.04  # in the room the card is shown in
        elif old["rooms"] and c["area"] and c["area"] not in old["rooms"]:
            score -= 0.2  # the card is in the bedroom view, this one is in another room
        if old["device_class"] and c["device_class"] not in (None, old["device_class"]):
            score -= 0.25
        if old["unit"] and c["unit"] not in (None, old["unit"]):
            score -= 0.25
        if score >= MIN_SCORE:
            scored.append((score, c["entity_id"], name))
    scored.sort(reverse=True)
    return [{"entity_id": e, "name": n, "score": round(min(s, 1.0), 2)} for s, e, n in scored[:3]]


def _score_all(olds: list[dict[str, Any]], pool: list[dict[str, Any]]) -> list[list[dict[str, Any]]]:
    return [_candidates(o, pool) for o in olds]


async def async_scan(hass: HomeAssistant, ignored: list[str]) -> list[dict[str, Any]]:
    """Every dead reference: where it's used, what it is, and the best replacements."""
    registry = er.async_get(hass)
    hints: dict[str, dict[str, set[str]]] = {}
    uses = await _uses(hass, hints)
    result, olds = [], []
    for entity_id, where in uses.items():
        status = _status(hass, registry, entity_id)
        if status is None:
            continue
        entry = registry.async_get(entity_id)
        hint = hints.get(entity_id) or {}
        seen: set[tuple[str, str]] = set()
        places = [w for w in where if (w["kind"], w["id"]) not in seen and not seen.add((w["kind"], w["id"]))]
        name = (entry and (entry.name or entry.original_name)) or next(iter(sorted(hint.get("names", ()))), None) \
            or _label(entity_id)
        olds.append({
            "entity_id": entity_id, "name": name, "card_names": sorted(hint.get("names", ())),
            "views": sorted(hint.get("views", ())),
            "device_class": entry and (entry.device_class or entry.original_device_class),
            "unit": entry and entry.unit_of_measurement,
        })
        result.append({
            "entity_id": entity_id, "status": status, "name": name, "platform": entry.platform if entry else None,
            "used_in": places, "card_names": sorted(hint.get("names", ()))[:3], "ignored": entity_id in ignored,
        })
    pool = _pool(hass, registry)
    from homeassistant.helpers import area_registry as ar

    areas = [a.name.lower() for a in ar.async_get(hass).async_list_areas()]
    for o in olds:
        # The views that are rooms ("Soveværelse"); "Overview" or "Info" say nothing about where it is.
        o["rooms"] = {a for a in areas for v in o["views"] if a in v.lower() or v.lower().strip() in a}
    for r, candidates in zip(result, await hass.async_add_executor_job(_score_all, olds, pool)):
        r["candidates"] = candidates
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
