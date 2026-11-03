"""Other places that point at a device or entity: dashboards, other integrations, device actions, and where an entity
is used. Entity IDs stay the same in a replacement, so only device and entity registry ids need rewriting here."""

from __future__ import annotations

import json
import logging
import os
from typing import Any

from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.util.yaml import load_yaml

from .const import AUTOMATIONS_FILE, DOMAIN, SCRIPTS_FILE

_LOGGER = logging.getLogger(__name__)


def _swap(value: Any, ids: dict[str, str]) -> Any:
    """The same JSON value with ids replaced."""
    text = json.dumps(value, default=str)
    new = text
    for old, replacement in ids.items():
        new = new.replace(old, replacement)
    return value if new == text else json.loads(new)


async def async_dashboards(hass: HomeAssistant) -> list[tuple[str, Any, dict]]:
    """(title, dashboard, config) of dashboards made in the UI. YAML dashboards are files the user owns."""
    from homeassistant.components.lovelace.const import LOVELACE_DATA, MODE_STORAGE

    data = hass.data.get(LOVELACE_DATA)
    result = []
    for url, dashboard in data.dashboards.items() if data else []:
        if getattr(dashboard, "mode", None) != MODE_STORAGE:
            continue
        try:
            config = await dashboard.async_load(False)
        except Exception:  # noqa: BLE001 - an empty or broken dashboard is skipped
            continue
        title = (getattr(dashboard, "config", None) or {}).get("title") or url or "Overview"
        result.append((str(title), dashboard, config))
    return result


async def async_rewrite_dashboards(hass: HomeAssistant, ids: dict[str, str]) -> list[str]:
    changed = []
    for title, dashboard, config in await async_dashboards(hass):
        new = _swap(config, ids)
        if new is not config:
            await dashboard.async_save(new)
            changed.append(title)
    return changed


def entries_using(hass: HomeAssistant, ids: dict[str, str], skip: set[str]) -> list[Any]:
    """Config entries of other integrations (e.g. Battery Notes, Powercalc) that store one of the ids."""
    return [
        entry
        for entry in hass.config_entries.async_entries()
        if entry.domain not in skip | {DOMAIN}
        and any(old in json.dumps([dict(entry.data), dict(entry.options)], default=str) for old in ids)
    ]


async def async_rewrite_entries(hass: HomeAssistant, ids: dict[str, str], skip: set[str]) -> list[str]:
    """Point other integrations at the new ids, and reload them so they pick it up."""
    changed = []
    for entry in entries_using(hass, ids, skip):
        hass.config_entries.async_update_entry(
            entry, data=_swap(dict(entry.data), ids), options=_swap(dict(entry.options), ids)
        )
        changed.append(entry.title)
        if entry.state is ConfigEntryState.LOADED:
            hass.config_entries.async_schedule_reload(entry.entry_id)
    return changed


def used_in(hass: HomeAssistant, entity_id: str, dashboards: list[tuple[str, Any, dict]]) -> list[str]:
    """Names of automations, scripts, scenes and dashboards that use an entity."""
    from homeassistant.components import automation, script
    from homeassistant.components.homeassistant import scene

    found = []
    for domain, finder in (
        ("automation", automation.automations_with_entity),
        ("script", script.scripts_with_entity),
        ("scene", scene.scenes_with_entity),
    ):
        if domain in hass.config.components:
            for user in finder(hass, entity_id):
                state = hass.states.get(user)
                found.append((state and state.attributes.get("friendly_name")) or user)
    found += [f"Dashboard: {title}" for title, _, config in dashboards if entity_id in json.dumps(config)]
    return sorted(set(found))


def device_actions(hass: HomeAssistant, device_id: str, domain: str | None) -> list[str]:
    """Device actions and conditions of the old integration (e.g. a ZHA LED effect). They can't be translated."""
    if not domain:
        return []
    found = []
    for name in (AUTOMATIONS_FILE, SCRIPTS_FILE):
        path = hass.config.path(name)
        try:
            data = load_yaml(path) if os.path.isfile(path) else None
        except Exception:  # noqa: BLE001 - a broken file is the editor's business
            continue
        items = data if isinstance(data, list) else list((data or {}).values()) if isinstance(data, dict) else []
        for item in items:
            if not isinstance(item, dict):
                continue
            title = item.get("alias") or item.get("id") or "?"
            for part in ("actions", "action", "conditions", "condition", "sequence"):
                for hit in _walk(item.get(part), device_id, domain):
                    found.append(f"{title}: {hit}")
    return found


def _walk(value: Any, device_id: str, domain: str) -> list[str]:
    if isinstance(value, list):
        return [hit for v in value for hit in _walk(v, device_id, domain)]
    if not isinstance(value, dict):
        return []
    if value.get("device_id") == device_id and value.get("domain") == domain:
        return [str(value.get("type") or value.get("condition") or "?")]
    return [hit for v in value.values() for hit in _walk(v, device_id, domain)]
