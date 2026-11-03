"""Set up once, then "Replace a device" on the integration page."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.config_entries import (
    OptionsFlow,
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    ConfigSubentryFlow,
    SubentryFlowResult,
)
from homeassistant.core import callback
from homeassistant.helpers import selector

from .const import CONF_AI, CONF_NEW, CONF_OLD, CONF_REMOVE_OLD, DOMAIN, NO_MATCH, SUBENTRY_REPLACE
from .flows import confirm_schema, describe, match_schema
from .replace import async_plan, device_name


class ReplaceDeviceConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        if user_input is not None:
            return self.async_create_entry(title="Replace Device", data={})
        return self.async_show_form(step_id="user")

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        return ReplaceDeviceOptionsFlow()

    @classmethod
    @callback
    def async_get_supported_subentry_types(cls, config_entry: ConfigEntry) -> dict[str, type[ConfigSubentryFlow]]:
        return {SUBENTRY_REPLACE: ReplaceFlow}


class ReplaceDeviceOptionsFlow(OptionsFlow):
    """Optional AI: helps with entities and button triggers it can't match by itself."""

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        if user_input is not None:
            return self.async_create_entry(data=user_input)
        schema = vol.Schema(
            {
                vol.Optional(CONF_AI, description={"suggested_value": self.config_entry.options.get(CONF_AI)}): (
                    selector.EntitySelector(selector.EntitySelectorConfig(domain="ai_task"))
                )
            }
        )
        return self.async_show_form(step_id="init", data_schema=schema)


class ReplaceFlow(ConfigSubentryFlow):
    """Old device → new device → check the pairs → replace. Nothing is saved as a subentry."""

    def __init__(self) -> None:
        self._old = self._new = ""
        self._mapping: dict[str, str | None] | None = None

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> SubentryFlowResult:
        errors = {}
        if user_input is not None:
            if user_input[CONF_OLD] == user_input[CONF_NEW]:
                errors["base"] = "same_device"
            else:
                self._old, self._new = user_input[CONF_OLD], user_input[CONF_NEW]
                return await self.async_step_match()
        schema = vol.Schema(
            {vol.Required(CONF_OLD): selector.DeviceSelector(), vol.Required(CONF_NEW): selector.DeviceSelector()}
        )
        return self.async_show_form(
            step_id="user", data_schema=self.add_suggested_values_to_schema(schema, user_input), errors=errors
        )

    async def async_step_match(self, user_input: dict[str, Any] | None = None) -> SubentryFlowResult:
        plan = async_plan(self.hass, self._old, self._new, self._mapping)
        if plan is None:
            return self.async_abort(reason="unknown_device")
        errors = {}
        if user_input is not None:
            picked = [v for v in user_input.values() if v != NO_MATCH]
            if len(picked) != len(set(picked)):
                errors["base"] = "duplicate"
            else:
                self._mapping = {k: None if v == NO_MATCH else v for k, v in user_input.items()}
                return await self.async_step_confirm()
        if not plan.old_entities:
            self._mapping = {}
            return await self.async_step_confirm()
        return self.async_show_form(
            step_id="match",
            data_schema=match_schema(self.hass, plan),
            errors=errors,
            description_placeholders={"old": device_name(plan.old), "new": device_name(plan.new)},
        )

    async def async_step_confirm(self, user_input: dict[str, Any] | None = None) -> SubentryFlowResult:
        plan = async_plan(self.hass, self._old, self._new, self._mapping)
        if plan is None:
            return self.async_abort(reason="unknown_device")
        if user_input is not None:
            result = await self._get_entry().runtime_data.async_replace(plan, user_input[CONF_REMOVE_OLD])
            reason = "replaced" if result["removed"] or not user_input[CONF_REMOVE_OLD] else "replaced_keep_old"
            return self.async_abort(
                reason=reason,
                description_placeholders={"old": device_name(plan.old), "moved": str(result["moved"])},
            )
        return self.async_show_form(
            step_id="confirm",
            data_schema=confirm_schema(),
            description_placeholders={
                "old": device_name(plan.old),
                "new": device_name(plan.new),
                "summary": describe(self.hass, plan),
            },
        )
