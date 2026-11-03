"""Optional AI help (any AI Task entity, e.g. Google Gemini). Everything works without it; the AI only fills gaps.

Each question says which device it is and where it moves (make, model, from and to), because "Button (3)" means
little on its own. Many devices are asked about in one call, so a big move doesn't use up a free daily quota. When
the AI can't answer, the reason is passed on, so the panel can say so instead of leaving it in the log.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
import json
import logging
import re
from typing import Any

from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)
_TIMEOUT = 120
_QUOTA = re.compile(r"429|quota|resource.?exhausted|rate.?limit|per.?day", re.I)
_RULES = (
    "Pick only when it is clearly the same thing. Use 0 when unsure: a wrong guess breaks the user's automations, "
    "an empty answer only asks them to check."
)


@dataclass
class Question:
    """One device: what it is, and old items to find among new ones."""

    context: str
    old: list[str]
    new: list[str]
    answer: dict[int, int] = field(default_factory=dict)


class AiError(Exception):
    """The AI didn't answer; the message is short and meant for the user."""


async def _ask(hass: HomeAssistant, entity_id: str, task: str, instructions: str) -> dict[str, Any]:
    try:
        async with asyncio.timeout(_TIMEOUT):
            response = await hass.services.async_call(
                "ai_task",
                "generate_data",
                {"entity_id": entity_id, "task_name": task, "instructions": instructions},
                blocking=True,
                return_response=True,
            )
    except Exception as err:  # noqa: BLE001 - any failure means: no AI answer this time
        _LOGGER.warning("AI help (%s) failed: %s", task, err)
        raise AiError("quota" if _QUOTA.search(str(err)) else str(err)[:200] or type(err).__name__) from err
    data = (response or {}).get("data")
    if isinstance(data, str):
        match = re.search(r"\{.*\}", data, re.S)
        try:
            data = json.loads(match.group(0)) if match else None
        except ValueError:
            data = None
    if not isinstance(data, dict):
        raise AiError("unreadable answer")
    return data


def _picks(items: Any, count: int, options: int) -> dict[int, int]:
    """{question index: option index} from [{"n": 1, "pick": 3}] (1-based, pick 0 = none)."""
    result = {}
    for item in items if isinstance(items, list) else []:
        try:
            n, pick = int(item["n"]), int(item["pick"])
        except (KeyError, TypeError, ValueError):
            continue
        if 1 <= n <= count and 1 <= pick <= options:
            result[n - 1] = pick - 1
    return result


async def async_ask_many(hass: HomeAssistant, entity_id: str, kind: str, questions: list[Question]) -> None:
    """Ask about many devices in one call; fills each question's answer. Raises AiError."""
    questions = [q for q in questions if q.old and q.new]
    if not questions:
        return
    what = (
        "For each old entity, pick the entity of the new device that measures or controls the same thing "
        "(each new entity at most once)."
        if kind == "entities"
        else "For each old button trigger, pick the new trigger that fires on the same physical action: the same "
        "button number and the same press type (short, double, long, release)."
    )
    blocks = []
    for d, q in enumerate(questions, 1):
        blocks.append(
            f"Device {d}: {q.context}\n"
            + "Old:\n"
            + "\n".join(f"  {i}. {o}" for i, o in enumerate(q.old, 1))
            + "\n"
            + "New:\n"
            + "\n".join(f"  {i}. {n}" for i, n in enumerate(q.new, 1))
        )
    prompt = (
        "Smart home devices are being replaced or moved to another Home Assistant integration. "
        f"{what} {_RULES}\n\n" + "\n\n".join(blocks) + "\n\n"
        'Answer only with JSON: {"devices": [{"device": 1, "answers": [{"n": 1, "pick": 2}]}]}'
    )
    data = await _ask(hass, entity_id, f"Replace Device: {kind}", prompt)
    for item in data.get("devices", []):
        try:
            question = questions[int(item["device"]) - 1]
        except (KeyError, TypeError, ValueError, IndexError):
            continue
        question.answer = _picks(item.get("answers"), len(question.old), len(question.new))


async def async_pick_triggers(
    hass: HomeAssistant, entity_id: str, old: list[str], new: list[str], context: str = ""
) -> dict[int, int]:
    """Which of the new device's triggers means the same as each old one. Raises AiError."""
    question = Question(context or "a button or remote", old, new)
    await async_ask_many(hass, entity_id, "triggers", [question])
    return question.answer
