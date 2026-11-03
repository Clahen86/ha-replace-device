"""Replace Device: a new device takes over a dead one's names, entity IDs, area and history."""

from __future__ import annotations

from pathlib import Path

from homeassistant.components import frontend, panel_custom
from homeassistant.components.http import StaticPathConfig
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv, issue_registry as ir
from homeassistant.helpers.typing import ConfigType
from homeassistant.loader import async_get_integration

from . import suggest, websocket
from .const import CONF_AI, DOMAIN
from .replace import Replacer

type ReplaceDeviceConfigEntry = ConfigEntry[Replacer]

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)
PANEL = "replace-device"
_STATIC = "/replace_device_static"
_TITLES = {
    "da": "Udskift enhed",
    "de": "Gerät ersetzen",
    "sv": "Byt enhet",
    "nb": "Bytt enhet",
    "nl": "Apparaat vervangen",
}


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    websocket.async_setup(hass)
    await hass.http.async_register_static_paths(
        [StaticPathConfig(_STATIC, str(Path(__file__).parent / "frontend"), cache_headers=False)]
    )
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ReplaceDeviceConfigEntry) -> bool:
    replacer = Replacer(hass)
    replacer.ai_entity = entry.options.get(CONF_AI)
    await replacer.async_load()
    entry.runtime_data = replacer
    entry.async_on_unload(suggest.async_watch(hass))
    entry.async_on_unload(replacer.async_stop)
    entry.async_on_unload(entry.add_update_listener(_options_changed))
    version = (await async_get_integration(hass, DOMAIN)).version
    await panel_custom.async_register_panel(
        hass,
        frontend_url_path=PANEL,
        webcomponent_name="replace-device-panel",
        sidebar_title=_TITLES.get(hass.config.language.split("-")[0], "Replace device"),
        sidebar_icon="mdi:swap-horizontal-circle-outline",
        module_url=f"{_STATIC}/panel.js?v={version}",
        require_admin=True,
    )
    return True


async def _options_changed(hass: HomeAssistant, entry: ReplaceDeviceConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ReplaceDeviceConfigEntry) -> bool:
    frontend.async_remove_panel(hass, PANEL)
    return True


async def async_remove_entry(hass: HomeAssistant, entry: ReplaceDeviceConfigEntry) -> None:
    for domain, issue_id in list(ir.async_get(hass).issues):
        if domain == DOMAIN:
            ir.async_delete_issue(hass, DOMAIN, issue_id)
