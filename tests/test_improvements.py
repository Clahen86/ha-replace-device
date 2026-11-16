"""1.12: on/off carried over, switch -> light, undo only what the replacement wrote, meters' jumps."""

from pytest_homeassistant_custom_component.common import MockConfigEntry

from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr, entity_registry as er

from custom_components.replace_device import replace as rp
from custom_components.replace_device.const import DOMAIN


def _dev(hass, platform, ident, name, ents):
    entry = MockConfigEntry(domain=platform, title=platform)
    entry.add_to_hass(hass)
    device = dr.async_get(hass).async_get_or_create(
        config_entry_id=entry.entry_id, identifiers={(platform, ident)}, name=name, manufacturer="X", model="Plug"
    )
    reg = er.async_get(hass)
    for key, domain, disabled in ents:
        reg.async_get_or_create(
            domain, platform, f"{ident}-{key}", suggested_object_id=f"{name}_{key}".lower(), device_id=device.id,
            config_entry=entry, original_name=key.capitalize(),
            disabled_by=er.RegistryEntryDisabler.INTEGRATION if disabled else None,
        )
    return device


async def _setup(hass):
    entry = MockConfigEntry(domain=DOMAIN, data={})
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()


async def _replace(client, old, new):
    await client.send_json_auto_id({"type": "replace_device/plan", "old": old.id, "new": new.id})
    plan = (await client.receive_json())["result"]
    await client.send_json_auto_id({"type": "replace_device/replace", "old": old.id, "new": new.id, "mapping": plan["mapping"]})
    result = (await client.receive_json())["result"]
    return plan, result


async def test_enabled_and_undo_only_own_lines(hass: HomeAssistant, hass_ws_client, tmp_path) -> None:
    hass.config.config_dir = str(tmp_path)
    old = _dev(hass, "zha", "old", "Hall", [("power", "sensor", False), ("rssi", "sensor", False)])
    new = _dev(hass, "mqtt", "new", "0xabc", [("power", "sensor", False), ("rssi", "sensor", True)])
    (tmp_path / "automations.yaml").write_text(f"- id: '1'\n  alias: A\n  triggers:\n  - device_id: {old.id}\n")
    await _setup(hass)
    client = await hass_ws_client(hass)
    plan, result = await _replace(client, old, new)
    await hass.async_block_till_done()
    reg = er.async_get(hass)
    assert plan["mapping"]["sensor.hall_rssi"] == "sensor.0xabc_rssi"
    assert reg.async_get("sensor.hall_rssi").disabled_by is None  # was on: stays on

    # An automation made for the new device afterwards keeps pointing at it after undo.
    text = (tmp_path / "automations.yaml").read_text()
    (tmp_path / "automations.yaml").write_text(text + f"- id: '2'\n  alias: B\n  triggers:\n  - device_id:  {new.id}\n")
    await client.send_json_auto_id({"type": "replace_device/undo", "record": result["id"]})
    assert (await client.receive_json())["success"]
    await hass.async_block_till_done()
    text = (tmp_path / "automations.yaml").read_text()
    assert f"device_id: {old.id}" in text and f"device_id:  {new.id}" in text


async def test_switch_becomes_light(hass: HomeAssistant, hass_ws_client, tmp_path) -> None:
    hass.config.config_dir = str(tmp_path)
    old = _dev(hass, "zha", "old", "Lamp", [("plug", "switch", False)])
    new = _dev(hass, "mqtt", "new", "0xdef", [("plug", "light", False)])
    (tmp_path / "automations.yaml").write_text("- id: '1'\n  alias: A\n  actions:\n  - target:\n      entity_id: switch.lamp_plug\n")
    await _setup(hass)
    client = await hass_ws_client(hass)
    plan, result = await _replace(client, old, new)
    await hass.async_block_till_done()
    assert plan["mapping"]["switch.lamp_plug"] == "light.0xdef_plug"
    assert result["moved"] == 1 and not result["failed"]
    assert er.async_get(hass).async_get("light.lamp_plug").platform == "mqtt"
    assert "light.lamp_plug" in (tmp_path / "automations.yaml").read_text()

    await client.send_json_auto_id({"type": "replace_device/undo", "record": result["id"]})
    assert (await client.receive_json())["success"]
    await hass.async_block_till_done()
    assert "switch.lamp_plug" in (tmp_path / "automations.yaml").read_text()
    assert er.async_get(hass).async_get("light.0xdef_plug") is not None


async def test_meter_jump(hass: HomeAssistant, monkeypatch) -> None:
    reg = er.async_get(hass)
    o = reg.async_get_or_create("sensor", "zha", "o1", suggested_object_id="plug_energy")
    n = reg.async_get_or_create("sensor", "mqtt", "n1", suggested_object_id="tmp_energy")
    hass.states.async_set(n.entity_id, "400", {"state_class": "total_increasing", "unit_of_measurement": "kWh"})

    async def last(_hass, _sid):
        return 300.0

    monkeypatch.setattr(rp.stats, "async_last_state", last)
    jump = await rp._energy_jump(hass, o, n, o.entity_id, 0)
    assert jump["amount"] == 100 and jump["unit"] == "kWh"
    hass.states.async_set(n.entity_id, "5", {"state_class": "total_increasing", "unit_of_measurement": "kWh"})
    assert (await rp._energy_jump(hass, o, n, o.entity_id, 0))["amount"] == 5  # counted as a new start
    hass.states.async_set(n.entity_id, "0", {"state_class": "total_increasing", "unit_of_measurement": "kWh"})
    assert await rp._energy_jump(hass, o, n, o.entity_id, 0) is None  # a new meter at 0: nothing to take out
