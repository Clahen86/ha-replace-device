"""Swap: the history stays with the room's entity id (the recorder would otherwise take it along)."""

from datetime import timedelta

import pytest

from homeassistant.components.recorder import get_instance
from homeassistant.components.recorder.history import get_significant_states
from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util

from pytest_homeassistant_custom_component.components.recorder.common import async_wait_recording_done

from .test_improvements import _dev, _setup
from .test_safety_1_14 import _replacer


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(recorder_mock, enable_custom_integrations):
    yield


async def _values(hass, entity_id):
    await async_wait_recording_done(hass)
    inst = get_instance(hass)
    await inst.async_block_till_done()
    start = dt_util.utcnow() - timedelta(hours=1)
    got = await inst.async_add_executor_job(get_significant_states, hass, start, None, [entity_id])
    return [s.state for s in got.get(entity_id, [])]


async def test_history_stays_with_the_room(hass: HomeAssistant, tmp_path) -> None:
    hass.config.config_dir = str(tmp_path)
    a = _dev(hass, "zha", "a", "Stue", [("temperature", "sensor", False)])
    b = _dev(hass, "zha", "b", "Sov", [("temperature", "sensor", False)])
    hass.states.async_set("sensor.stue_temperature", "21")
    hass.states.async_set("sensor.sov_temperature", "17")
    await _setup(hass)
    assert await _values(hass, "sensor.stue_temperature") == ["21"]
    await _replacer(hass).async_swap(a.id, b.id)
    await hass.async_block_till_done()
    assert "21" in await _values(hass, "sensor.stue_temperature")
    assert "17" in await _values(hass, "sensor.sov_temperature")
    assert "17" not in await _values(hass, "sensor.stue_temperature")
