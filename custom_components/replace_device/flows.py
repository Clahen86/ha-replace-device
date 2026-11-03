"""What the user sees in the replace wizard and in the suggested repair."""

from __future__ import annotations

import voluptuous as vol

from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er, selector

from .const import CONF_REMOVE_OLD, NO_MATCH, TEXTS
from .replace import Plan


def entity_label(hass: HomeAssistant, entry: er.RegistryEntry) -> str:
    state = hass.states.get(entry.entity_id)
    name = (state and state.attributes.get("friendly_name")) or entry.name or entry.original_name
    return f"{name} ({entry.entity_id})" if name else entry.entity_id


def match_schema(hass: HomeAssistant, plan: Plan) -> vol.Schema:
    """One drop-down per old entity, with the guessed match picked."""
    fields = {}
    for old in plan.old_entities:
        options = [selector.SelectOptionDict(value=NO_MATCH, label="—")] + [
            selector.SelectOptionDict(value=new.entity_id, label=entity_label(hass, new))
            for new in plan.new_entities
            if new.domain == old.domain
        ]
        fields[vol.Required(old.entity_id, default=plan.mapping.get(old.entity_id) or NO_MATCH)] = (
            selector.SelectSelector(selector.SelectSelectorConfig(options=options))
        )
    return vol.Schema(fields)


def confirm_schema() -> vol.Schema:
    return vol.Schema({vol.Required(CONF_REMOVE_OLD, default=True): selector.BooleanSelector()})


def describe(hass: HomeAssistant, plan: Plan) -> str:
    """The preview: what moves, what goes, what stays."""
    text = TEXTS.get(hass.config.language.split("-")[0], TEXTS["en"])
    pairs = plan.pairs
    taken = {n.entity_id for _, n in pairs}
    sections = []
    if pairs:
        sections.append([text["moves"]] + [f"- {entity_label(hass, o)} ← {n.entity_id}" for o, n in pairs])
    if dropped := [o for o in plan.old_entities if plan.mapping.get(o.entity_id) not in taken]:
        sections.append([text["dropped"]] + [f"- {entity_label(hass, o)}" for o in dropped])
    if own := [n for n in plan.new_entities if n.entity_id not in taken]:
        sections.append([text["own"]] + [f"- {entity_label(hass, n)}" for n in own])
    if plan.uses_device:
        sections.append([text["users"]] + [f"- {name}" for name in plan.uses_device])
    return "\n\n".join("\n".join(s) for s in sections) or text["nothing"]
