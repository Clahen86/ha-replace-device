"""1.14: a switch that became a light gets light.turn_on; a reload that fails is said, with "Try again"."""

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError

from custom_components.replace_device import actions

from .test_improvements import _dev, _replace, _setup
from .test_safety_1_14 import _replacer

AUTOMATION = """- id: '1'
  alias: Lys
  triggers: []
  actions:
  - action: switch.turn_on
    target:
      entity_id: switch.lamp_plug
  - action: switch.turn_off
    target:
      entity_id:
      - switch.lamp_plug
      - switch.other
"""


async def test_switch_action_becomes_light_and_back(hass: HomeAssistant, hass_ws_client, tmp_path) -> None:
    hass.config.config_dir = str(tmp_path)
    old = _dev(hass, "zha", "old", "Lamp", [("plug", "switch", False)])
    new = _dev(hass, "mqtt", "new", "0xdef", [("plug", "light", False)])
    (tmp_path / "automations.yaml").write_text(AUTOMATION)
    await _setup(hass)
    client = await hass_ws_client(hass)
    _plan, result = await _replace(client, old, new)
    await hass.async_block_till_done()
    text = (tmp_path / "automations.yaml").read_text()
    assert "action: light.turn_on" in text
    assert "action: switch.turn_off" in text  # also a real switch in it: left, and said
    assert any("switch.turn_off" in x for x in result["triggers"]["unresolved"])
    assert await _replacer(hass).async_undo(result["id"])
    await hass.async_block_till_done()
    text = (tmp_path / "automations.yaml").read_text()
    assert "action: switch.turn_on" in text and "light." not in text


def test_only_where_every_target_moved(tmp_path) -> None:
    (tmp_path / "scripts.yaml").write_text(
        "flash:\n  alias: Blink\n  sequence:\n  - service: switch.toggle\n    entity_id: light.a\n"
        "  - action: switch.turn_on\n    data:\n      entity_id: switch.b\n"
    )
    got = actions.translate(str(tmp_path), {"switch.a": "light.a", "switch.c": "switch.c2"})
    text = (tmp_path / "scripts.yaml").read_text()
    assert "service: light.toggle" in text and "action: switch.turn_on" in text
    assert got["domains"] == ["script"] and len(got["changed"]) == 1 and not got["open"]


async def test_failed_reload_is_kept_and_tried_again(hass: HomeAssistant, hass_ws_client, tmp_path) -> None:
    hass.config.config_dir = str(tmp_path)
    await _setup(hass)
    replacer = _replacer(hass)
    broken = {"yes": True}

    async def reload(call):
        if broken["yes"]:
            raise HomeAssistantError("Invalid config for automation")

    hass.services.async_register("automation", "reload", reload)
    await replacer.async_reload({"automation"})
    broken["yes"] = False
    client = await hass_ws_client(hass)
    await client.send_json_auto_id({"type": "replace_device/history"})
    assert "Invalid config" in (await client.receive_json())["result"]["reload_failed"]["automation"]
    await client.send_json_auto_id({"type": "replace_device/reload_again"})
    assert (await client.receive_json())["result"]["reload_failed"] == {}


def test_area_targets_are_left_for_the_user(tmp_path) -> None:
    (tmp_path / "automations.yaml").write_text(
        "- id: '1'\n  alias: A\n  actions:\n  - action: switch.turn_on\n    target:\n      entity_id: light.a\n      area_id: stue\n"
    )
    got = actions.translate(str(tmp_path), {"switch.a": "light.a"})
    assert not got["changed"] and got["open"] and "switch.turn_on" in (tmp_path / "automations.yaml").read_text()
