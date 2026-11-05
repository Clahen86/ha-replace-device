"""Entity IDs that change by themselves: a cloud sync renames them, or a device comes back as "…_2".

Home Assistant does not update automations when an entity ID changes, so they stop working without a word. This
watches the entity registry, and when an ID that something uses changes, a repair offers to fix every place that uses
the old ID (automations, scripts, scenes, dashboards made in the UI, the energy dashboard) or to give the entity its old
ID back. The user's own YAML files are only listed, line by line.
"""

from __future__ import annotations

import hashlib
import re
from typing import TYPE_CHECKING, Any

from homeassistant.core import CALLBACK_TYPE, Event, HomeAssistant, callback
from homeassistant.helpers import entity_registry as er, issue_registry as ir
from homeassistant.helpers.event import async_call_later

from .const import DOMAIN

if TYPE_CHECKING:
    from .replace import Replacer

SUFFIX = re.compile(r"^(.+)_(\d{1,2})$")
# Wait a minute: a device that is paired again often gets a temporary name (its 0x… address) and its own name back
# right after, and an integration that renames many entities does it in one go.
DELAY = 60


def issue_id(old: str, new: str) -> str:
    return "renamed_" + hashlib.sha1(f"{old}>{new}".encode()).hexdigest()[:16]


def count(places: dict[str, Any]) -> int:
    """How many places use the old ID (fixed ones and ones to do by hand)."""
    return sum(len(places.get(k) or []) for k in ("users", "dashboards", "integrations", "yaml", "esphome", "outside")) + (
        1 if places.get("energy") else 0
    )


@callback
def async_clear_resolved(hass: HomeAssistant) -> None:
    """Remove repairs that no longer apply: the new ID is gone again, or the old ID is back."""
    registry = er.async_get(hass)
    for (domain, issue), entry in list(ir.async_get(hass).issues.items()):
        if domain != DOMAIN or not issue.startswith("renamed_") or not entry.data:
            continue
        old, new, kind = entry.data.get("old"), entry.data.get("new"), entry.data.get("kind")
        if registry.async_get(new) is None or (kind == "renamed" and registry.async_get(old) is not None):
            ir.async_delete_issue(hass, DOMAIN, issue)


@callback
def async_watch(hass: HomeAssistant, replacer: Replacer) -> CALLBACK_TYPE:
    pending: list[CALLBACK_TYPE] = []
    async_clear_resolved(hass)

    async def _check(old: str, new: str, kind: str) -> None:
        registry = er.async_get(hass)
        if registry.async_get(new) is None or (kind == "renamed" and registry.async_get(old) is not None):
            return  # gone again, or the old ID is back
        places = await replacer.async_follow_places(old, new)
        if not count(places):
            return  # nothing used the old ID: nothing broke
        ir.async_create_issue(
            hass, DOMAIN, issue_id(old, new),
            is_fixable=True, severity=ir.IssueSeverity.WARNING,
            translation_key="renamed" if kind == "renamed" else "suffix",
            translation_placeholders={"old": old, "new": new, "count": str(count(places))},
            data={"old": old, "new": new, "kind": kind},
        )

    @callback
    def _changed(event: Event) -> None:
        # Any change can put things right again (the ID back, the entity gone): tidy up stale repairs first.
        async_clear_resolved(hass)
        if replacer.is_busy():
            return  # Replace Device's own work (a replacement, a rename, an undo …)
        data = event.data
        if data.get("action") == "update" and data.get("old_entity_id"):
            old, new, kind = data["old_entity_id"], data["entity_id"], "renamed"
        elif data.get("action") == "create" and (match := SUFFIX.match(data.get("entity_id", ""))):
            # "sensor.kitchen_temperature_2" while "sensor.kitchen_temperature" is gone: the device came back as new.
            old, new, kind = match[1], data["entity_id"], "suffix"
            if er.async_get(hass).async_get(old) is not None or hass.states.get(old) is not None:
                return
        else:
            return

        async def _later(_now: Any) -> None:
            await _check(old, new, kind)

        pending.append(async_call_later(hass, DELAY, _later))

    unsub = hass.bus.async_listen(er.EVENT_ENTITY_REGISTRY_UPDATED, _changed)

    @callback
    def _stop() -> None:
        unsub()
        for cancel in pending:
            cancel()

    return _stop
