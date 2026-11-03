"""The suggested replacement: "New sensor found – replace the dead one?"."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.components.repairs import ConfirmRepairFlow, RepairsFlow
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import device_registry as dr, selector

from .const import CONF_OLD, CONF_REMOVE_OLD, DOMAIN
from .flows import confirm_schema, describe
from .replace import async_plan, device_name


async def async_create_fix_flow(hass: HomeAssistant, issue_id: str, data: dict[str, Any] | None) -> RepairsFlow:
    if issue_id.startswith("suggest_") and data:
        return SuggestFlow(data)
    return ConfirmRepairFlow()


class SuggestFlow(RepairsFlow):
    def __init__(self, data: dict[str, Any]) -> None:
        self._new: str = data["new"]
        self._candidates: list[str] = data["candidates"]
        self._old = ""

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        devices = dr.async_get(self.hass)
        candidates = [d for c in self._candidates if (d := devices.async_get(c))]
        if not candidates or devices.async_get(self._new) is None:
            return self.async_abort(reason="unknown_device")
        if len(candidates) == 1:
            self._old = candidates[0].id
            return await self.async_step_confirm()
        if user_input is not None:
            self._old = user_input[CONF_OLD]
            return await self.async_step_confirm()
        options = [selector.SelectOptionDict(value=d.id, label=device_name(d)) for d in candidates]
        return self.async_show_form(
            step_id="pick",
            data_schema=vol.Schema(
                {vol.Required(CONF_OLD): selector.SelectSelector(selector.SelectSelectorConfig(options=options))}
            ),
        )

    async def async_step_pick(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        return await self.async_step_init(user_input)

    async def async_step_confirm(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        plan = async_plan(self.hass, self._old, self._new)
        if plan is None:
            return self.async_abort(reason="unknown_device")
        if user_input is not None:
            entry = self.hass.config_entries.async_entries(DOMAIN)[0]
            await entry.runtime_data.async_replace(plan, user_input[CONF_REMOVE_OLD])
            return self.async_create_entry(data={})
        return self.async_show_form(
            step_id="confirm",
            data_schema=confirm_schema(),
            description_placeholders={
                "old": device_name(plan.old),
                "new": device_name(plan.new),
                "summary": describe(self.hass, plan),
            },
        )
