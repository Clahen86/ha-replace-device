"""1.13.2: undo leaves the old entity's statistics under its own id, also when the new device is minutes old."""

import pytest
from homeassistant.components.recorder import get_instance
from homeassistant.components.recorder import statistics as st
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.components.recorder.common import async_wait_recording_done
from .test_improvements import _dev, _replace, _setup
from .test_stats import meta, rows, T0


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(recorder_mock, enable_custom_integrations):
    yield


async def _ids(hass):
    m = await get_instance(hass).async_add_executor_job(lambda: st.get_metadata(hass))
    return sorted(m)


async def test_undo_keeps_old_statistics(hass: HomeAssistant, hass_ws_client, tmp_path) -> None:
    hass.config.config_dir = str(tmp_path)
    old = _dev(hass, "zha", "old", "Hall", [("power", "sensor", False)])
    new = _dev(hass, "mqtt", "new", "0xabc", [("power", "sensor", False)])
    st.async_import_statistics(hass, meta("sensor.hall_power"), rows(5, T0))
    await async_wait_recording_done(hass)
    await _setup(hass)
    client = await hass_ws_client(hass)
    _plan, result = await _replace(client, old, new)
    await hass.async_block_till_done(); await async_wait_recording_done(hass)
    assert await _ids(hass) == ["sensor.hall_power"]
    await client.send_json_auto_id({"type": "replace_device/undo", "record": result["id"]})
    assert (await client.receive_json())["success"]
    await hass.async_block_till_done(); await async_wait_recording_done(hass)
    assert await _ids(hass) == ["sensor.hall_power"]
