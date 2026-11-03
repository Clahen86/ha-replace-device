"""Pair the entities of the old device with those of the new one."""

from __future__ import annotations

from difflib import SequenceMatcher

from homeassistant.helpers import entity_registry as er

# Below this a pair is a guess, not a match.
MIN_SCORE = 3.0


def match(old: list[er.RegistryEntry], new: list[er.RegistryEntry]) -> dict[str, str | None]:
    """Old entity_id -> new entity_id (or None). Best pairs first, each entity used once."""
    pairs = sorted(
        ((score(o, n, old, new), o.entity_id, n.entity_id) for o in old for n in new if o.domain == n.domain),
        reverse=True,
    )
    result: dict[str, str | None] = {o.entity_id: None for o in old}
    taken: set[str] = set()
    for points, old_id, new_id in pairs:
        if points < MIN_SCORE or result[old_id] is not None or new_id in taken:
            continue
        result[old_id] = new_id
        taken.add(new_id)
    return result


def score(o: er.RegistryEntry, n: er.RegistryEntry, old: list, new: list) -> float:
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
    points += 3 * SequenceMatcher(None, _label(o), _label(n)).ratio()
    return points


def _label(entry: er.RegistryEntry) -> str:
    return (entry.original_name or entry.translation_key or entry.entity_id.split(".", 1)[1]).lower()
