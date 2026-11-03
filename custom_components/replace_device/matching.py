"""Pair the entities of the old device with those of the new one.

Names shown in the UI can be in another language on each side (ZHA: "Lokal temperaturforskydning", Zigbee2MQTT:
"Local temperature calibration"), so the language-neutral names are compared too: translation keys, the feature
name inside the unique ID, and the entity ID without the device's own name.
"""

from __future__ import annotations

from difflib import SequenceMatcher
import re

from homeassistant.helpers import entity_registry as er

# Below this a pair is a guess, not a match.
MIN_SCORE = 3.0
# A runner-up this close to the best one means it could just as well be that one.
UNSURE_MARGIN = 1.0

# The same thing called differently by integrations and languages.
_SYNONYMS = {
    "lokal": "local",
    "offset": "calibration",
    "forskydning": "calibration",
    "temperaturforskydning": "temperature calibration",
    "kalibrering": "calibration",
    "nojagtighed": "accuracy",
    "frostbeskyttelse": "frost protection",
    "batteri": "battery",
    "luftfugtighed": "humidity",
    "fugtighed": "humidity",
    "temperatur": "temperature",
    "kontakt": "switch",
    "bornesikring": "child lock",
    "input": "value",
    "sensor": "",
    "zigbee2mqtt": "",
}


def match(old: list[er.RegistryEntry], new: list[er.RegistryEntry]) -> dict[str, str | None]:
    """Old entity_id -> new entity_id (or None). Best pairs first, each entity used once."""
    result: dict[str, str | None] = {o.entity_id: None for o in old}
    taken: set[str] = set()
    for points, old_id, new_id in _scored(old, new):
        if points < MIN_SCORE or result[old_id] is not None or new_id in taken:
            continue
        result[old_id] = new_id
        taken.add(new_id)
    return result


def unsure(old: list[er.RegistryEntry], new: list[er.RegistryEntry], mapping: dict[str, str | None]) -> list[str]:
    """Old entities whose match was close to another candidate: the user (or the AI) should look at them."""
    scores: dict[str, list[tuple[float, str]]] = {}
    for points, old_id, new_id in _scored(old, new):
        scores.setdefault(old_id, []).append((points, new_id))
    found = []
    for old_id, chosen in mapping.items():
        if not chosen or len(scores.get(old_id, [])) < 2:
            continue
        mine = next(p for p, n in scores[old_id] if n == chosen)
        if any(n != chosen and p >= mine - UNSURE_MARGIN for p, n in scores[old_id]):
            found.append(old_id)
    return found


def _scored(old: list[er.RegistryEntry], new: list[er.RegistryEntry]) -> list[tuple[float, str, str]]:
    old_common, new_common = _common_words(old), _common_words(new)
    return sorted(
        (
            (score(o, n, old, new, old_common, new_common), o.entity_id, n.entity_id)
            for o in old
            for n in new
            if o.domain == n.domain
        ),
        reverse=True,
    )


def score(
    o: er.RegistryEntry,
    n: er.RegistryEntry,
    old: list,
    new: list,
    old_common: set[str] | None = None,
    new_common: set[str] | None = None,
) -> float:
    """How alike two entities of the same domain are."""
    points = 0.0
    old_class, new_class = o.device_class or o.original_device_class, n.original_device_class
    if old_class and old_class == new_class:
        points += 3
    elif old_class and new_class:
        points -= 3
    if o.unit_of_measurement and o.unit_of_measurement == n.unit_of_measurement:
        points += 2
    if o.translation_key and o.translation_key == n.translation_key:
        points += 3
    if o.entity_category == n.entity_category:
        points += 1
    # The only light on both devices is the same light, whatever it's called.
    if sum(e.domain == o.domain for e in old) == 1 and sum(e.domain == n.domain for e in new) == 1:
        points += 2
    old_names = names(o, old_common or set())
    new_names = names(n, new_common or set())
    points += 4 * max((_alike(a, b) for a in old_names for b in new_names), default=0.0)
    return points


def names(entry: er.RegistryEntry, common: set[str]) -> list[str]:
    """What an entity is called, in words, in every form we have: shown name, translation key, unique ID, entity ID."""
    found = []
    for raw in (
        entry.original_name,
        entry.translation_key,
        _feature(entry.unique_id),
        entry.entity_id.split(".", 1)[1],
    ):
        words = [w for w in _words(raw) if w not in common]
        if words:
            found.append(" ".join(words))
    return found


def _alike(a: str, b: str) -> float:
    """Shared words count; spelling only when nearly the same ("lokal" ~ "local"), not chance letters."""
    a_words, b_words = set(a.split()), set(b.split())
    overlap = len(a_words & b_words) / len(a_words | b_words) if a_words | b_words else 0.0
    spelling = SequenceMatcher(None, a, b).ratio()
    return max(overlap, spelling if spelling >= 0.8 else 0.0)


def _words(text: str | None) -> list[str]:
    words = []
    for word in re.split(r"[^a-z0-9æøå]+", (text or "").lower().replace("æ", "ae").replace("ø", "o").replace("å", "a")):
        if not word or word.isdigit() or re.fullmatch(r"0x[0-9a-f]+|[0-9a-f]{2}", word):
            continue
        words += _SYNONYMS.get(word, word).split()
    return words


def _feature(unique_id: str | None) -> str:
    """The feature inside a unique ID: "0x0ceff6…_frost_protection_temperature_zigbee2mqtt_sensor" -> frost …"""
    return re.sub(r"(?:0x)?[0-9a-f]{16}|(?:[0-9a-f]{2}:){7}[0-9a-f]{2}", " ", (unique_id or "").lower())


def _common_words(entries: list[er.RegistryEntry]) -> set[str]:
    """Words in every entity ID of a device: its own name ("termostat traeningsrum"), not what the entity is."""
    if len(entries) < 2:
        return set()
    sets = [set(_words(e.entity_id.split(".", 1)[1])) for e in entries]
    return set.intersection(*sets)
