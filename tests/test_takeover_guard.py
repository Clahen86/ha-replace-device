"""1.13.2: a replacement never removes an old entity that the new one then can't take over (#53)."""

from pytest_homeassistant_custom_component.common import MockConfigEntry

from homeassistant.core import HomeAssistant
from homeassistant.helpers import area_registry as ar, device_registry as dr, entity_registry as er

from .test_improvements import _dev, _replace, _setup


async def test_target_held_by_a_state_is_skipped(hass: HomeAssistant, hass_ws_client, tmp_path) -> None:
    """A switch that becomes a light, where light.<name> is already a state without a registry entry (YAML)."""
    hass.config.config_dir = str(tmp_path)
    old = _dev(hass, "zha", "old", "Lamp", [("plug", "switch", False)])
    new = _dev(hass, "mqtt", "new", "0xdef", [("plug", "light", False)])
    hass.states.async_set("light.lamp_plug", "on")
    await _setup(hass)
    client = await hass_ws_client(hass)
    _plan, result = await _replace(client, old, new)
    await hass.async_block_till_done()
    reg = er.async_get(hass)
    assert result["failed"] == ["switch.lamp_plug"]
    # the new light is kept under a name of its own; the YAML light keeps its id
    assert [e.platform for e in reg.entities.values() if e.domain == "light"] == ["mqtt"]
    assert reg.async_get("light.lamp_plug") is None and hass.states.get("light.lamp_plug").state == "on"


async def test_area_without_own_name_still_takes_over(hass: HomeAssistant, hass_ws_client, tmp_path) -> None:
    """The old entity had an area of its own; the new one is its device's main entity (no name of its own)."""
    hass.config.config_dir = str(tmp_path)
    old = _dev(hass, "zha", "old", "Lamp", [("plug", "switch", False)])
    entry = MockConfigEntry(domain="mqtt", title="mqtt")
    entry.add_to_hass(hass)
    new = dr.async_get(hass).async_get_or_create(
        config_entry_id=entry.entry_id, identifiers={("mqtt", "new")}, name="0xdef", manufacturer="X", model="Plug"
    )
    reg = er.async_get(hass)
    reg.async_get_or_create(
        "switch", "mqtt", "new-plug", suggested_object_id="0xdef_plug", device_id=new.id, config_entry=entry,
        has_entity_name=True, original_name=None,
    )
    kitchen = ar.async_get(hass).async_create("Kitchen")
    dr.async_get(hass).async_update_device(old.id, area_id=kitchen.id)
    reg.async_update_entity("switch.lamp_plug", area_id=kitchen.id)
    await _setup(hass)
    client = await hass_ws_client(hass)
    _plan, result = await _replace(client, old, new)
    await hass.async_block_till_done()
    assert result["failed"] == []
    took = reg.async_get("switch.lamp_plug")
    assert took is not None and took.platform == "mqtt"
    assert dr.async_get(hass).async_get(new.id).area_id == kitchen.id  # the area is on the device


async def test_undo_goes_on_when_one_entity_cant_move(hass: HomeAssistant, hass_ws_client, tmp_path) -> None:
    """Undo where one entity's own old id is now taken by a state: that one is skipped, the other still goes back."""
    hass.config.config_dir = str(tmp_path)
    old = _dev(hass, "zha", "old", "Hall", [("power", "sensor", False), ("rssi", "sensor", False)])
    new = _dev(hass, "mqtt", "new", "0xabc", [("power", "sensor", False), ("rssi", "sensor", False)])
    await _setup(hass)
    client = await hass_ws_client(hass)
    _plan, result = await _replace(client, old, new)
    await hass.async_block_till_done()
    reg = er.async_get(hass)
    assert reg.async_get("sensor.hall_power").platform == "mqtt"
    hass.states.async_set("sensor.0xabc_power", "1")  # the id undo would give back is taken
    await client.send_json_auto_id({"type": "replace_device/undo", "record": result["id"]})
    assert (await client.receive_json())["success"]
    await hass.async_block_till_done()
    assert reg.async_get("sensor.0xabc_rssi").platform == "mqtt"  # went back
    assert reg.async_get("sensor.hall_power").platform == "mqtt"  # stayed, instead of stopping the undo


async def test_file_not_utf8_is_left_alone(hass: HomeAssistant, hass_ws_client, tmp_path) -> None:
    """An old file in latin-1 (æøå) doesn't stop the replacement - it is skipped, the rest is done."""
    hass.config.config_dir = str(tmp_path)
    old = _dev(hass, "zha", "old", "Hall", [("power", "sensor", False)])
    new = _dev(hass, "mqtt", "new", "0xabc", [("power", "sensor", False)])
    raw = f"- id: '1'\n  alias: Køkken\n  triggers:\n  - device_id: {old.id}\n".encode("latin-1")
    (tmp_path / "automations.yaml").write_bytes(raw)
    (tmp_path / "scripts.yaml").write_text("s:\n  sequence:\n  - action: homeassistant.turn_on\n    target:\n      entity_id: sensor.0xabc_power\n")
    await _setup(hass)
    client = await hass_ws_client(hass)
    _plan, result = await _replace(client, old, new)
    await hass.async_block_till_done()
    assert result["moved"] == 1 and result["failed"] == []
    assert (tmp_path / "automations.yaml").read_bytes() == raw
    assert er.async_get(hass).async_get("sensor.hall_power").platform == "mqtt"


async def test_off_or_resting_entities_are_not_orphans(hass: HomeAssistant) -> None:
    """Dead references: an entity the user turned off, or one whose integration is down for now, is never offered
    for removal. One its running integration no longer gives is."""
    from homeassistant.config_entries import ConfigEntryState

    from custom_components.replace_device import deadrefs

    reg = er.async_get(hass)
    up = MockConfigEntry(domain="mqtt", state=ConfigEntryState.LOADED)
    down = MockConfigEntry(domain="tuya", state=ConfigEntryState.SETUP_RETRY)
    up.add_to_hass(hass)
    down.add_to_hass(hass)
    reg.async_get_or_create("sensor", "mqtt", "off", suggested_object_id="off", config_entry=up,
                            disabled_by=er.RegistryEntryDisabler.USER)
    reg.async_get_or_create("sensor", "tuya", "rest", suggested_object_id="rest", config_entry=down)
    reg.async_get_or_create("sensor", "mqtt", "gone", suggested_object_id="gone", config_entry=up)
    assert not deadrefs.async_remove_orphan(hass, "sensor.off")
    assert not deadrefs.async_remove_orphan(hass, "sensor.rest")
    assert deadrefs.async_remove_orphan(hass, "sensor.gone")
    assert reg.async_get("sensor.off") and reg.async_get("sensor.rest") and reg.async_get("sensor.gone") is None
