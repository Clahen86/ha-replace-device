"""Orphaned statistics: found after the entity is deleted, and given to the entity that took over."""

from datetime import datetime, timedelta, timezone

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from homeassistant.components.recorder import get_instance
from homeassistant.components.recorder.statistics import async_import_statistics, statistics_during_period
from homeassistant.core import HomeAssistant

from pytest_homeassistant_custom_component.components.recorder.common import async_wait_recording_done

from custom_components.replace_device import stats
from custom_components.replace_device.const import DOMAIN

T0 = datetime(2026, 1, 1, tzinfo=timezone.utc)


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(recorder_mock, enable_custom_integrations):
    """The recorder has to be set up before Home Assistant itself."""
    yield


@pytest.fixture
async def ready(hass: HomeAssistant):
    yield


def meta(sid):
    return {"statistic_id": sid, "source": "recorder", "name": None, "unit_of_measurement": "kWh", "unit_class": "energy",
            "has_sum": True, "mean_type": 0, "has_mean": False}


def rows(n, start, base=0.0):
    return [{"start": start + timedelta(hours=i), "state": base + i + 1, "sum": base + i + 1} for i in range(n)]


async def _sums(hass, sid):
    inst = get_instance(hass)
    await inst.async_block_till_done()
    r = await inst.async_add_executor_job(statistics_during_period, hass, T0 - timedelta(days=1), None, {sid}, "hour", None, {"sum"})
    return [x["sum"] for x in r.get(sid, [])]


async def test_rename_to_a_new_entity_without_statistics(ready, hass: HomeAssistant) -> None:
    async_import_statistics(hass, meta("sensor.old_plug_energy"), rows(5, T0))
    hass.states.async_set("sensor.new_plug_energy", "0", {"state_class": "total_increasing", "unit_of_measurement": "kWh"})
    await get_instance(hass).async_block_till_done()
    orphans = await stats.async_orphans(hass)
    assert [o["statistic_id"] for o in orphans] == ["sensor.old_plug_energy"]
    assert orphans[0]["candidates"][0]["entity_id"] == "sensor.new_plug_energy"
    assert (await stats.async_migrate(hass, "sensor.old_plug_energy", "sensor.new_plug_energy"))["done"] == "renamed"
    assert await _sums(hass, "sensor.new_plug_energy") == [1, 2, 3, 4, 5]
    assert await _sums(hass, "sensor.old_plug_energy") == []


async def test_merge_carries_the_sum_over(ready, hass: HomeAssistant) -> None:
    async_import_statistics(hass, meta("sensor.old_plug_energy"), rows(5, T0))
    async_import_statistics(hass, meta("sensor.new_plug_energy"), rows(3, T0 + timedelta(hours=10)))
    hass.states.async_set("sensor.new_plug_energy", "3", {"state_class": "total_increasing", "unit_of_measurement": "kWh"})
    await get_instance(hass).async_block_till_done()
    res = await stats.async_migrate(hass, "sensor.old_plug_energy", "sensor.new_plug_energy")
    assert res["done"] == "merged" and res["hours"] == 5 and res["carried"] == 5
    assert await _sums(hass, "sensor.new_plug_energy") == [1, 2, 3, 4, 5, 6, 7, 8]  # no jump back to 1
    assert await _sums(hass, "sensor.old_plug_energy") == []


async def test_a_live_entity_is_not_orphaned(ready, hass: HomeAssistant) -> None:
    async_import_statistics(hass, meta("sensor.alive"), rows(2, T0))
    hass.states.async_set("sensor.alive", "2", {"state_class": "total_increasing", "unit_of_measurement": "kWh"})
    await get_instance(hass).async_block_till_done()
    assert await stats.async_orphans(hass) == []
    with pytest.raises(ValueError):
        await stats.async_migrate(hass, "sensor.alive", "sensor.other")


async def test_nothing_to_add_then_delete(ready, hass: HomeAssistant) -> None:
    """The new one already has the same hours (what happened to the dryer's new plug): nothing to move - delete it."""
    async_import_statistics(hass, meta("sensor.old_plug_energy"), rows(3, T0 + timedelta(hours=5)))
    async_import_statistics(hass, meta("sensor.new_plug_energy"), rows(10, T0))
    hass.states.async_set("sensor.new_plug_energy", "10", {"state_class": "total_increasing", "unit_of_measurement": "kWh"})
    await async_wait_recording_done(hass)
    with pytest.raises(ValueError, match="nothing_to_add"):
        await stats.async_migrate(hass, "sensor.old_plug_energy", "sensor.new_plug_energy")
    await stats.async_delete(hass, "sensor.old_plug_energy")
    assert await _sums(hass, "sensor.old_plug_energy") == []
    assert len(await _sums(hass, "sensor.new_plug_energy")) == 10
