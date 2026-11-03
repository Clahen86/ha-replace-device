"""Replace Device: a new device takes over a dead one's names, entity IDs, area and history."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import issue_registry as ir

from . import suggest
from .const import DOMAIN
from .replace import Replacer

type ReplaceDeviceConfigEntry = ConfigEntry[Replacer]


async def async_setup_entry(hass: HomeAssistant, entry: ReplaceDeviceConfigEntry) -> bool:
    replacer = Replacer(hass)
    await replacer.async_load()
    entry.runtime_data = replacer
    entry.async_on_unload(suggest.async_watch(hass))
    entry.async_on_unload(replacer.async_stop)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ReplaceDeviceConfigEntry) -> bool:
    return True


async def async_remove_entry(hass: HomeAssistant, entry: ReplaceDeviceConfigEntry) -> None:
    for domain, issue_id in list(ir.async_get(hass).issues):
        if domain == DOMAIN:
            ir.async_delete_issue(hass, DOMAIN, issue_id)
