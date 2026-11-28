"""1.14: swap two devices that moved rooms, and copy one device's automations to a new one like it."""

import pytest

from homeassistant.core import HomeAssistant
from homeassistant.helpers import area_registry as ar, device_registry as dr, entity_registry as er

from .test_improvements import _dev, _setup
from .test_safety_1_14 import _replacer


def _in(hass, device, area_name):
    area = ar.async_get(hass).async_get_area_by_name(area_name) or ar.async_get(hass).async_create(area_name)
    dr.async_get(hass).async_update_device(device.id, area_id=area.id)
    return area


async def test_swap_two_sensors_that_moved_rooms(hass: HomeAssistant, hass_ws_client, tmp_path) -> None:
    hass.config.config_dir = str(tmp_path)
    a = _dev(hass, "zha", "a", "Stue", [("temperature", "sensor", False)])
    b = _dev(hass, "zha", "b", "Sov", [("temperature", "sensor", False)])
    stue_area = _in(hass, a, "Stue")
    sov_area = _in(hass, b, "Soveværelse")
    reg = er.async_get(hass)
    reg.async_update_entity("sensor.stue_temperature", name="Stue temp")
    ua, ub = reg.async_get("sensor.stue_temperature").id, reg.async_get("sensor.sov_temperature").id
    (tmp_path / "automations.yaml").write_text(
        f"- id: '1'\n  alias: Kold stue\n  triggers:\n  - device_id: {a.id}\n    entity_id: {ua}\n    type: temperature\n"
    )
    await _setup(hass)
    client = await hass_ws_client(hass)
    await client.send_json_auto_id({"type": "replace_device/swap_plan", "a": a.id, "b": b.id})
    plan = (await client.receive_json())["result"]
    assert plan["same_kind"] and plan["pairs"] == [{"a": "sensor.stue_temperature", "b": "sensor.sov_temperature", "name": "Stue temp"}]
    await client.send_json_auto_id({"type": "replace_device/swap", "a": a.id, "b": b.id})
    result = (await client.receive_json())["result"]
    await hass.async_block_till_done()
    assert result["swapped"] == 1
    stue = reg.async_get("sensor.stue_temperature")
    assert stue.unique_id == "b-temperature" and stue.name == "Stue temp"  # the one now in the living room
    assert reg.async_get("sensor.sov_temperature").unique_id == "a-temperature"
    devices = dr.async_get(hass)
    assert devices.async_get(b.id).name_by_user == "Stue" and devices.async_get(b.id).area_id == stue_area.id
    assert devices.async_get(a.id).name_by_user == "Sov" and devices.async_get(a.id).area_id == sov_area.id
    text = (tmp_path / "automations.yaml").read_text()
    assert f"device_id: {b.id}" in text and ub in text and ua not in text

    assert await _replacer(hass).async_undo(result["id"])
    await hass.async_block_till_done()
    assert reg.async_get("sensor.stue_temperature").unique_id == "a-temperature"
    assert devices.async_get(a.id).name_by_user is None and devices.async_get(b.id).name_by_user is None
    text = (tmp_path / "automations.yaml").read_text()
    assert f"device_id: {a.id}" in text and ua in text


async def test_swap_needs_the_same_integration(hass: HomeAssistant, hass_ws_client) -> None:
    a = _dev(hass, "zha", "a", "Stue", [("temperature", "sensor", False)])
    b = _dev(hass, "mqtt", "b", "Sov", [("temperature", "sensor", False)])
    await _setup(hass)
    client = await hass_ws_client(hass)
    await client.send_json_auto_id({"type": "replace_device/swap_plan", "a": a.id, "b": b.id})
    assert not (await client.receive_json())["result"]["same_kind"]
    await client.send_json_auto_id({"type": "replace_device/swap", "a": a.id, "b": b.id})
    assert not (await client.receive_json())["success"]


AUTOMATION = """- id: '1'
  alias: Lys i stue ved bevægelse
  triggers:
  - trigger: state
    entity_id: binary_sensor.stue_bevaegelse_occupancy
    to: 'on'
  actions:
  - action: light.turn_on
    target:
      entity_id: light.stue_loft_light
  - action: notify.notify
    data:
      message: Bevægelse
- id: '2'
  alias: Noget andet
  triggers: []
  actions:
  - action: light.turn_off
    target:
      entity_id: light.stue_loft_light
"""


async def test_copy_a_motion_sensors_setup_to_the_bedroom(hass: HomeAssistant, hass_ws_client, tmp_path) -> None:
    hass.config.config_dir = str(tmp_path)
    src = _dev(hass, "zha", "m1", "Stue bevaegelse", [("occupancy", "binary_sensor", False)])
    dst = _dev(hass, "zha", "m2", "Sov bevaegelse", [("occupancy", "binary_sensor", False)])
    lamp1 = _dev(hass, "hue", "l1", "Stue loft", [("light", "light", False)])
    lamp2 = _dev(hass, "hue", "l2", "Sov loft", [("light", "light", False)])
    for d, area in ((src, "Stue"), (lamp1, "Stue"), (dst, "Soveværelse"), (lamp2, "Soveværelse")):
        _in(hass, d, area)
    (tmp_path / "automations.yaml").write_text(AUTOMATION)
    await _setup(hass)
    client = await hass_ws_client(hass)
    await client.send_json_auto_id({"type": "replace_device/copy_plan", "src": src.id, "dst": dst.id})
    plan = (await client.receive_json())["result"]
    assert [c["key"] for c in plan["items"]] == ["1"]  # only what uses the sensor itself
    item = plan["items"][0]
    assert item["new_name"] == "Lys i Soveværelse ved bevægelse" and item["keeps"] == []
    await client.send_json_auto_id({"type": "replace_device/copy", "src": src.id, "dst": dst.id, "keys": ["automation:1"]})
    result = (await client.receive_json())["result"]
    await hass.async_block_till_done()
    text = (tmp_path / "automations.yaml").read_text()
    copy = text.split("Lys i Soveværelse ved bevægelse")[1]
    assert "binary_sensor.sov_bevaegelse_occupancy" in copy and "light.sov_loft_light" in copy
    assert "binary_sensor.stue_bevaegelse_occupancy" in text.split("Noget andet")[0]  # the original is untouched
    assert len(result["created"]) == 1

    assert await _replacer(hass).async_undo(result["id"])
    await hass.async_block_till_done()
    assert "Soveværelse" not in (tmp_path / "automations.yaml").read_text()


async def test_copy_says_what_still_points_at_the_other_room(hass: HomeAssistant, hass_ws_client, tmp_path) -> None:
    hass.config.config_dir = str(tmp_path)
    src = _dev(hass, "zha", "m1", "Stue bevaegelse", [("occupancy", "binary_sensor", False)])
    dst = _dev(hass, "zha", "m2", "Sov bevaegelse", [("occupancy", "binary_sensor", False)])
    lamp1 = _dev(hass, "hue", "l1", "Stue loft", [("light", "light", False)])
    for d, area in ((src, "Stue"), (lamp1, "Stue"), (dst, "Soveværelse")):
        _in(hass, d, area)
    (tmp_path / "automations.yaml").write_text(AUTOMATION)
    await _setup(hass)
    client = await hass_ws_client(hass)
    await client.send_json_auto_id({"type": "replace_device/copy_plan", "src": src.id, "dst": dst.id})
    plan = (await client.receive_json())["result"]
    assert plan["items"][0]["keeps"] == ["light.stue_loft_light"]  # no light in the bedroom: said


async def test_copy_nothing_picked_is_refused(hass: HomeAssistant, tmp_path) -> None:
    hass.config.config_dir = str(tmp_path)
    src = _dev(hass, "zha", "m1", "A", [("occupancy", "binary_sensor", False)])
    dst = _dev(hass, "zha", "m2", "B", [("occupancy", "binary_sensor", False)])
    await _setup(hass)
    from homeassistant.exceptions import HomeAssistantError

    with pytest.raises(HomeAssistantError):
        await _replacer(hass).async_copy(src.id, dst.id, [])


async def test_copy_moves_area_and_device_targets_and_never_takes_an_id(hass: HomeAssistant, tmp_path) -> None:
    hass.config.config_dir = str(tmp_path)
    src = _dev(hass, "zha", "m1", "Stue bevaegelse", [("occupancy", "binary_sensor", False)])
    dst = _dev(hass, "zha", "m2", "Sov bevaegelse", [("occupancy", "binary_sensor", False)])
    lamp1 = _dev(hass, "hue", "l1", "Stue loft", [("light", "light", False)])
    lamp2 = _dev(hass, "hue", "l2", "Sov loft", [("light", "light", False)])
    stue = _in(hass, src, "Stue")
    sov = _in(hass, dst, "Soveværelse")
    _in(hass, lamp1, "Stue")
    _in(hass, lamp2, "Soveværelse")
    (tmp_path / "automations.yaml").write_text(
        f"- id: '1'\n  alias: Stue lys\n  triggers:\n  - trigger: state\n    entity_id: binary_sensor.stue_bevaegelse_occupancy\n"
        f"  actions:\n  - action: light.turn_on\n    target:\n      area_id: {stue.id}\n"
        f"  - device_id: {lamp1.id}\n    domain: light\n    type: turn_on\n"
    )
    await _setup(hass)
    replacer = _replacer(hass)
    import time

    from homeassistant.util.yaml import load_yaml

    taken = str(int(time.time() * 1000))
    text = (tmp_path / "automations.yaml").read_text() + f"- id: '{taken}'\n  alias: Min egen\n  triggers: []\n  actions: []\n"
    (tmp_path / "automations.yaml").write_text(text)
    result = await replacer.async_copy(src.id, dst.id, ["automation:1"])
    data = load_yaml(str(tmp_path / "automations.yaml"))
    copy = next(x for x in data if x["alias"] == "Soveværelse lys")
    assert copy["id"] != taken and copy["actions"][0]["target"]["area_id"] == sov.id
    assert copy["actions"][1]["device_id"] == lamp2.id
    # Someone made their own with the copy's id after all: undo leaves it.
    for x in data:
        if x["alias"] == "Soveværelse lys":
            x["alias"] = "Min ændrede"
    from homeassistant.util.yaml import dump

    (tmp_path / "automations.yaml").write_text(dump(data))
    assert await replacer.async_undo(result["id"])
    assert "Min ændrede" in (tmp_path / "automations.yaml").read_text()


async def test_copy_never_writes_a_file_with_secrets(hass: HomeAssistant, tmp_path) -> None:
    hass.config.config_dir = str(tmp_path)
    src = _dev(hass, "zha", "m1", "A", [("occupancy", "binary_sensor", False)])
    dst = _dev(hass, "zha", "m2", "B", [("occupancy", "binary_sensor", False)])
    (tmp_path / "secrets.yaml").write_text("pw: x\n")
    (tmp_path / "automations.yaml").write_text(
        "- id: '1'\n  alias: A\n  triggers:\n  - trigger: state\n    entity_id: binary_sensor.a_occupancy\n"
        "  actions:\n  - action: notify.x\n    data:\n      message: !secret pw\n"
    )
    await _setup(hass)
    from homeassistant.exceptions import HomeAssistantError

    with pytest.raises(HomeAssistantError):
        await _replacer(hass).async_copy(src.id, dst.id, ["automation:1"])
    assert "!secret pw" in (tmp_path / "automations.yaml").read_text()
