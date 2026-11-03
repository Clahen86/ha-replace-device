"""What could still bite after a replacement, shown before anything changes."""

from __future__ import annotations

from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from . import references
from .replace import Plan, _domain

# Lists of allowed values, where an automation may test for one by name.
_VALUE_LISTS = (
    "options",
    "hvac_modes",
    "preset_modes",
    "fan_modes",
    "swing_modes",
    "effect_list",
    "supported_color_modes",
)


def differences(old: er.RegistryEntry, new: er.RegistryEntry) -> list[dict[str, Any]]:
    """Values, units and kinds of the old entity that the new one doesn't have."""
    found = []
    old_caps, new_caps = old.capabilities or {}, new.capabilities or {}
    for key in _VALUE_LISTS:
        old_values, new_values = old_caps.get(key), new_caps.get(key)
        if isinstance(old_values, list) and isinstance(new_values, list):
            missing = [str(v) for v in old_values if v not in new_values]
            if missing:
                found.append({"kind": "values", "missing": missing, "new": [str(v) for v in new_values]})
    if old.unit_of_measurement and new.unit_of_measurement and old.unit_of_measurement != new.unit_of_measurement:
        found.append({"kind": "unit", "old": old.unit_of_measurement, "new": new.unit_of_measurement})
    old_class, new_class = old_caps.get("state_class"), new_caps.get("state_class")
    if old_class and new_class and old_class != new_class:
        found.append({"kind": "state_class", "old": old_class, "new": new_class})
    return found


async def async_checks(
    hass: HomeAssistant, plan: Plan, dashboards: list[tuple[str, Any, dict]] | None = None
) -> dict[str, Any]:
    if dashboards is None:
        dashboards = await references.async_dashboards(hass)
    taken = {o.entity_id for o, _ in plan.pairs}
    dropped = []
    for old in plan.old_entities:
        if old.entity_id not in taken and (users := references.used_in(hass, old.entity_id, dashboards)):
            dropped.append({"entity_id": old.entity_id, "used_in": users})
    changed = []
    for old, new in plan.pairs:
        if found := differences(old, new):
            energy = (old.device_class or old.original_device_class) == "energy"
            changed.append({"entity_id": old.entity_id, "energy": energy, "differences": found})
    ids = {plan.old.id: plan.new.id} | {o.id: n.id for o, n in plan.pairs}
    skip = {d for d in (_domain(hass, plan.old), _domain(hass, plan.new)) if d}
    return {
        "dropped_used": dropped,
        "differences": changed,
        "device_actions": references.device_actions(hass, plan.old.id, _domain(hass, plan.old)),
        "integrations": [e.title for e in references.entries_using(hass, ids, skip)],
        "dashboards": [title for title, _, config in dashboards if any(i in str(config) for i in ids)],
    }
