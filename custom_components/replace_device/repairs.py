"""The suggested replacement: "New sensor found – replace the dead one?"."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.components.repairs import ConfirmRepairFlow, RepairsFlow
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import device_registry as dr, entity_registry as er, selector

from .const import CONF_OLD, CONF_REMOVE_OLD, DOMAIN
from .flows import confirm_schema, describe
from .replace import async_plan, device_name


async def async_create_fix_flow(hass: HomeAssistant, issue_id: str, data: dict[str, Any] | None) -> RepairsFlow:
    if issue_id.startswith("suggest_") and data:
        return SuggestFlow(data)
    if issue_id.startswith("renamed_") and data:
        return RenamedFlow(data)
    return ConfirmRepairFlow()


class RenamedFlow(RepairsFlow):
    """An entity ID changed by itself: fix what uses the old ID, or give the entity its old ID back."""

    def __init__(self, data: dict[str, Any]) -> None:
        self._old: str = data["old"]
        self._new: str = data["new"]
        self._kind: str = data.get("kind", "renamed")

    def _replacer(self) -> Any:
        entries = self.hass.config_entries.async_loaded_entries(DOMAIN)
        return entries[0].runtime_data if entries else None

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        replacer = self._replacer()
        registry = er.async_get(self.hass)
        if replacer is None or registry.async_get(self._new) is None or (
            self._kind == "renamed" and registry.async_get(self._old) is not None
        ):
            # Already in order again (e.g. the device got its own name back): the repair removes itself.
            from .watch import async_clear_resolved

            async_clear_resolved(self.hass)
            return self.async_abort(reason="already_fixed")
        places = await replacer.async_follow_places(self._old, self._new)
        fixed = [u for u in places.get("users", [])] + [f"Dashboard: {d}" for d in places.get("dashboards", [])]
        if places.get("energy"):
            fixed.append("Energy")
        by_hand = (places.get("yaml") or []) + (places.get("esphome") or []) + (places.get("integrations") or [])
        options = ["fix"] + (["restore"] if er.async_get(self.hass).async_get(self._old) is None else [])
        return self.async_show_menu(
            step_id="init",
            menu_options=options,
            description_placeholders={
                "old": self._old, "new": self._new,
                "fixed": "\n".join(f"- {x}" for x in fixed) or "-",
                "by_hand": "\n".join(f"- {x}" for x in by_hand) or "-",
            },
        )

    async def async_step_fix(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        replacer = self._replacer()
        if replacer is None or not await replacer.async_follow(self._old, self._new, "fix"):
            return self.async_abort(reason="unknown_device")
        return self.async_create_entry(data={})

    async def async_step_restore(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        from .watch import async_restore_together, renamed_with

        replacer = self._replacer()
        together = renamed_with(self.hass, self._new)  # read before the ID changes back
        if replacer is None or not await replacer.async_follow(self._old, self._new, "restore"):
            return self.async_abort(reason="unknown_device")
        if together:
            # The whole device was renamed: its old name and the other entities' old IDs come back too.
            async_restore_together(self.hass, self._old)
        return self.async_create_entry(data={})


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
            entries = self.hass.config_entries.async_loaded_entries(DOMAIN)
            if not entries:
                return self.async_abort(reason="unknown_device")
            await entries[0].runtime_data.async_replace(plan, user_input[CONF_REMOVE_OLD])
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
