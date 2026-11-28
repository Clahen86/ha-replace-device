"""1.14: one change at a time, an out-of-date plan removes nothing, undo only in its own automations, redo stops at a
taken id and redoes switch -> light, "change" moves device triggers along, a record before anything changes."""

import asyncio

from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr, entity_registry as er

from custom_components.replace_device import replace as rp

from .test_improvements import _dev, _replace, _setup
from .test_replace import NEW_SENSORS, OLD_SENSORS, _device


def _replacer(hass):
    from custom_components.replace_device.const import DOMAIN

    return hass.config_entries.async_loaded_entries(DOMAIN)[0].runtime_data


async def test_undo_leaves_a_new_automation_with_the_same_line(hass: HomeAssistant, hass_ws_client, tmp_path) -> None:
    hass.config.config_dir = str(tmp_path)
    old = _dev(hass, "zha", "old", "Hall", [("power", "sensor", False)])
    new = _dev(hass, "mqtt", "new", "0xabc", [("power", "sensor", False)])
    (tmp_path / "automations.yaml").write_text(f"- id: '1'\n  alias: A\n  triggers:\n  - device_id: {old.id}\n")
    await _setup(hass)
    client = await hass_ws_client(hass)
    _plan, result = await _replace(client, old, new)
    await hass.async_block_till_done()
    text = (tmp_path / "automations.yaml").read_text()
    # Made for the new device afterwards - the very same line as the one the replacement wrote.
    (tmp_path / "automations.yaml").write_text(text + f"- id: '2'\n  alias: B\n  triggers:\n  - device_id: {new.id}\n")
    await client.send_json_auto_id({"type": "replace_device/undo", "record": result["id"]})
    assert (await client.receive_json())["success"]
    await hass.async_block_till_done()
    a, b = (tmp_path / "automations.yaml").read_text().split("- id: '2'")
    assert old.id in a and new.id in b


async def test_out_of_date_plan_removes_nothing(hass: HomeAssistant, hass_ws_client, tmp_path) -> None:
    hass.config.config_dir = str(tmp_path)
    old = _dev(hass, "zha", "old", "Hall", [("power", "sensor", False)])
    new = _dev(hass, "mqtt", "new", "0xabc", [("power", "sensor", False)])
    await _setup(hass)
    client = await hass_ws_client(hass)
    await client.send_json_auto_id({"type": "replace_device/plan", "old": old.id, "new": new.id})
    plan = (await client.receive_json())["result"]
    er.async_get(hass).async_remove("sensor.0xabc_power")  # gone since the test run
    await client.send_json_auto_id({"type": "replace_device/replace", "old": old.id, "new": new.id, "mapping": plan["mapping"]})
    assert not (await client.receive_json())["success"]
    assert dr.async_get(hass).async_get(old.id) is not None
    assert er.async_get(hass).async_get("sensor.hall_power").platform == "zha"
    assert not _replacer(hass).history


async def test_one_new_device_for_two_old_is_refused(hass: HomeAssistant, hass_ws_client) -> None:
    a = _dev(hass, "zha", "a", "A", [("power", "sensor", False)])
    b = _dev(hass, "zha", "b", "B", [("power", "sensor", False)])
    new = _dev(hass, "mqtt", "new", "0xabc", [("power", "sensor", False)])
    await _setup(hass)
    client = await hass_ws_client(hass)
    pairs = [{"old": a.id, "new": new.id}, {"old": b.id, "new": new.id}]
    await client.send_json_auto_id({"type": "replace_device/migrate", "pairs": pairs})
    assert not (await client.receive_json())["success"]
    assert dr.async_get(hass).async_get(a.id) and dr.async_get(hass).async_get(b.id)


async def test_two_undos_at_once_undo_once(hass: HomeAssistant, hass_ws_client, tmp_path) -> None:
    hass.config.config_dir = str(tmp_path)
    old = _dev(hass, "zha", "old", "Hall", [("power", "sensor", False)])
    new = _dev(hass, "mqtt", "new", "0xabc", [("power", "sensor", False)])
    await _setup(hass)
    client = await hass_ws_client(hass)
    _plan, result = await _replace(client, old, new)
    await hass.async_block_till_done()
    replacer = _replacer(hass)

    async def slow(hass, moves):  # the statistics are read: a moment where a second tap gets in
        await asyncio.sleep(0.01)
        return {}

    real = rp.stats.async_would_follow
    rp.stats.async_would_follow = slow
    try:
        done = await asyncio.gather(replacer.async_undo(result["id"]), replacer.async_undo(result["id"]))
    finally:
        rp.stats.async_would_follow = real
    assert sorted(done) == [False, True]


async def test_redo_stops_when_the_name_is_taken_again(hass: HomeAssistant, hass_ws_client, tmp_path) -> None:
    hass.config.config_dir = str(tmp_path)
    old = _dev(hass, "zha", "old", "Hall", [("power", "sensor", False)])
    new = _dev(hass, "mqtt", "new", "0xabc", [("power", "sensor", False)])
    await _setup(hass)
    client = await hass_ws_client(hass)
    _plan, result = await _replace(client, old, new)
    await hass.async_block_till_done()
    replacer = _replacer(hass)
    assert await replacer.async_undo(result["id"])
    await hass.async_block_till_done()
    reg = er.async_get(hass)
    reg.async_get_or_create("sensor", "zha", "back", suggested_object_id="hall_power")  # the old one came back
    await client.send_json_auto_id({"type": "replace_device/redo", "record": result["id"]})
    assert not (await client.receive_json())["success"]
    assert reg.async_get("sensor.hall_power").unique_id == "back"
    assert next(r for r in replacer.history if r["id"] == result["id"])["undone"]


async def test_redo_switch_becomes_light_again(hass: HomeAssistant, hass_ws_client, tmp_path) -> None:
    hass.config.config_dir = str(tmp_path)
    old = _dev(hass, "zha", "old", "Lamp", [("plug", "switch", False)])
    new = _dev(hass, "mqtt", "new", "0xdef", [("plug", "light", False)])
    (tmp_path / "automations.yaml").write_text("- id: '1'\n  alias: A\n  actions:\n  - target:\n      entity_id: switch.lamp_plug\n")
    await _setup(hass)
    client = await hass_ws_client(hass)
    _plan, result = await _replace(client, old, new)
    await hass.async_block_till_done()
    replacer = _replacer(hass)
    assert await replacer.async_undo(result["id"])
    await hass.async_block_till_done()
    assert "switch.lamp_plug" in (tmp_path / "automations.yaml").read_text()
    assert await replacer.async_redo(result["id"])
    await hass.async_block_till_done()
    assert "light.lamp_plug" in (tmp_path / "automations.yaml").read_text()


async def test_change_moves_device_triggers_along(hass: HomeAssistant, hass_ws_client, tmp_path) -> None:
    """Temperature and humidity mixed up, then put right: a device trigger on the old temperature follows the name."""
    hass.config.config_dir = str(tmp_path)
    old = _device(hass, "zha", "old", "Kitchen", OLD_SENSORS)
    new = _device(hass, "mqtt", "new", "0x00158d0001", NEW_SENSORS)
    reg = er.async_get(hass)
    old_temp = reg.async_get("sensor.kitchen_temperature").id
    new_temp = reg.async_get("sensor.0x00158d0001_temperature").id
    new_hum = reg.async_get("sensor.0x00158d0001_humidity").id
    (tmp_path / "automations.yaml").write_text(f"- id: '1'\n  alias: Cold\n  triggers:\n  - entity_id: {old_temp}\n")
    await _setup(hass)
    client = await hass_ws_client(hass)
    wrong = {
        "sensor.kitchen_temperature": "sensor.0x00158d0001_humidity",
        "sensor.kitchen_humidity": "sensor.0x00158d0001_temperature",
        "sensor.kitchen_battery": "sensor.0x00158d0001_battery",
        "sensor.kitchen_rssi": None,
    }
    await client.send_json_auto_id({"type": "replace_device/replace", "old": old.id, "new": new.id, "mapping": wrong})
    record = (await client.receive_json())["result"]["id"]
    await hass.async_block_till_done()
    assert new_hum in (tmp_path / "automations.yaml").read_text()
    mapping = {"sensor.kitchen_temperature": new_temp, "sensor.kitchen_humidity": new_hum}
    await client.send_json_auto_id({"type": "replace_device/edit", "record": record, "mapping": mapping})
    assert (await client.receive_json())["success"]
    await hass.async_block_till_done()
    text = (tmp_path / "automations.yaml").read_text()
    assert new_temp in text and new_hum not in text
    # Undo afterwards puts the old one back, not the wrong one.
    assert await _replacer(hass).async_undo(record)
    await hass.async_block_till_done()
    assert old_temp in (tmp_path / "automations.yaml").read_text()


async def test_change_only_to_the_new_devices_entities(hass: HomeAssistant, hass_ws_client, tmp_path) -> None:
    hass.config.config_dir = str(tmp_path)
    old = _device(hass, "zha", "old", "Kitchen", OLD_SENSORS)
    new = _device(hass, "mqtt", "new", "0x00158d0001", NEW_SENSORS)
    other = _dev(hass, "zha", "other", "Other", [("power", "sensor", False)])
    await _setup(hass)
    client = await hass_ws_client(hass)
    _plan, result = await _replace(client, old, new)
    await hass.async_block_till_done()
    foreign = er.async_get(hass).async_get("sensor.other_power").id
    assert other.id
    await client.send_json_auto_id(
        {"type": "replace_device/edit", "record": result["id"], "mapping": {"sensor.kitchen_temperature": foreign}}
    )
    assert not (await client.receive_json())["success"]


async def test_written_down_before_the_old_one_is_removed(hass: HomeAssistant, hass_ws_client, tmp_path, monkeypatch) -> None:
    hass.config.config_dir = str(tmp_path)
    old = _dev(hass, "zha", "old", "Hall", [("power", "sensor", False)])
    new = _dev(hass, "mqtt", "new", "0xabc", [("power", "sensor", False)])
    await _setup(hass)
    replacer = _replacer(hass)
    seen = []

    async def remove(hass, device):
        seen.append(dict(replacer.history[-1]) if replacer.history else None)
        return False

    monkeypatch.setattr(rp, "_remove_device", remove)
    client = await hass_ws_client(hass)
    _plan, result = await _replace(client, old, new)
    assert seen and seen[0]["running"] and seen[0]["id"] == result["id"]
    assert "running" not in replacer.history[-1]

    # A restart in the middle: the record is still there, marked.
    replacer.history[-1]["running"] = True
    await replacer.store.async_save(replacer._data())
    again = rp.Replacer(hass)
    await again.async_load()
    again.async_stop()
    assert again.history[-1].get("interrupted") and "running" not in again.history[-1]


async def test_two_replacements_of_the_same_old_device_at_once(hass: HomeAssistant, hass_ws_client, tmp_path) -> None:
    """Two tabs: the second waits, then finds its plan out of date - the first one's new entity is left alone."""
    hass.config.config_dir = str(tmp_path)
    old = _dev(hass, "zha", "old", "Hall", [("power", "sensor", False)])
    one = _dev(hass, "mqtt", "one", "0xone", [("power", "sensor", False)])
    two = _dev(hass, "mqtt", "two", "0xtwo", [("power", "sensor", False)])
    await _setup(hass)
    replacer = _replacer(hass)
    p1 = rp.async_plan(hass, old.id, one.id)
    p2 = rp.async_plan(hass, old.id, two.id)
    got = await asyncio.gather(
        replacer.async_replace(p1, True), replacer.async_replace(p2, True), return_exceptions=True
    )
    assert isinstance(got[1], rp.HomeAssistantError)
    assert er.async_get(hass).async_get("sensor.hall_power").unique_id == "one-power"


async def test_nothing_changes_when_the_record_cant_be_saved(hass: HomeAssistant, tmp_path, monkeypatch) -> None:
    hass.config.config_dir = str(tmp_path)
    old = _dev(hass, "zha", "old", "Hall", [("power", "sensor", False)])
    new = _dev(hass, "mqtt", "new", "0xabc", [("power", "sensor", False)])
    await _setup(hass)
    replacer = _replacer(hass)

    async def refuse(data):  # what Home Assistant does on a write error: logs it and returns
        return None

    monkeypatch.setattr(replacer.store, "async_save", refuse)
    import pytest

    with pytest.raises(rp.HomeAssistantError):
        await replacer.async_replace(rp.async_plan(hass, old.id, new.id), True)
    assert er.async_get(hass).async_get("sensor.hall_power").platform == "zha"
    assert dr.async_get(hass).async_get(old.id) is not None and not replacer.history


async def test_redo_stops_when_the_new_entity_is_gone(hass: HomeAssistant, hass_ws_client, tmp_path) -> None:
    hass.config.config_dir = str(tmp_path)
    old = _dev(hass, "zha", "old", "Hall", [("power", "sensor", False)])
    new = _dev(hass, "mqtt", "new", "0xabc", [("power", "sensor", False)])
    await _setup(hass)
    client = await hass_ws_client(hass)
    _plan, result = await _replace(client, old, new)
    await hass.async_block_till_done()
    replacer = _replacer(hass)
    assert await replacer.async_undo(result["id"])
    await hass.async_block_till_done()
    er.async_get(hass).async_remove("sensor.0xabc_power")
    import pytest

    with pytest.raises(rp.HomeAssistantError):
        await replacer.async_redo(result["id"])
