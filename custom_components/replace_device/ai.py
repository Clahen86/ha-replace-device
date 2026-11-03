"""Optional AI help (any AI Task entity, e.g. Google Gemini). Everything works without it; the AI only fills gaps."""

from __future__ import annotations

import asyncio
import json
import logging
import re
from typing import Any

from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)
_TIMEOUT = 90


async def _ask(hass: HomeAssistant, entity_id: str, task: str, instructions: str) -> dict[str, Any] | None:
    try:
        async with asyncio.timeout(_TIMEOUT):
            response = await hass.services.async_call(
                "ai_task",
                "generate_data",
                {"entity_id": entity_id, "task_name": task, "instructions": instructions},
                blocking=True,
                return_response=True,
            )
        data = (response or {}).get("data")
        if isinstance(data, str):
            match = re.search(r"\{.*\}", data, re.S)
            data = json.loads(match.group(0)) if match else None
        return data if isinstance(data, dict) else None
    except Exception as err:  # noqa: BLE001 - without an answer we just don't use AI
        _LOGGER.warning("AI help (%s) failed: %s", task, err)
        return None


def _picks(data: dict[str, Any] | None, count: int, options: int) -> dict[int, int]:
    """{question index: option index} from {"answers": [{"n": 1, "pick": 3}]} (1-based, pick 0 = none)."""
    result = {}
    for item in (data or {}).get("answers", []):
        try:
            n, pick = int(item["n"]), int(item["pick"])
        except (KeyError, TypeError, ValueError):
            continue
        if 1 <= n <= count and 1 <= pick <= options:
            result[n - 1] = pick - 1
    return result


async def async_pick_triggers(hass: HomeAssistant, entity_id: str, old: list[str], new: list[str]) -> dict[int, int]:
    """Which of the new device's triggers means the same as each old one."""
    prompt = (
        "A Zigbee/smart home device moved from one Home Assistant integration to another. Its device triggers have "
        "other names now. For each old trigger, pick the new trigger that fires on the same physical action "
        "(same button, same press type). Use 0 if none matches.\n\n"
        "Old triggers:\n" + "\n".join(f"{i}. {t}" for i, t in enumerate(old, 1)) + "\n\n"
        "New triggers:\n" + "\n".join(f"{i}. {t}" for i, t in enumerate(new, 1)) + "\n\n"
        'Answer only with JSON: {"answers": [{"n": 1, "pick": 2}]}'
    )
    return _picks(await _ask(hass, entity_id, "Replace Device: triggers", prompt), len(old), len(new))


async def async_pick_entities(hass: HomeAssistant, entity_id: str, old: list[str], new: list[str]) -> dict[int, int]:
    """Which entity of the new device measures or controls the same as each old one."""
    prompt = (
        "A smart home device is being replaced by another one. For each entity of the old device, pick the entity "
        "of the new device that measures or controls the same thing. Each new entity at most once. "
        "Use 0 if none matches.\n\n"
        "Old entities:\n" + "\n".join(f"{i}. {e}" for i, e in enumerate(old, 1)) + "\n\n"
        "New entities:\n" + "\n".join(f"{i}. {e}" for i, e in enumerate(new, 1)) + "\n\n"
        'Answer only with JSON: {"answers": [{"n": 1, "pick": 2}]}'
    )
    return _picks(await _ask(hass, entity_id, "Replace Device: entities", prompt), len(old), len(new))
