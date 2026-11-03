"""Replace a ZHA sensor with a Zigbee2MQTT one, via the wizard and via the suggested repair."""

from datetime import timedelta

from pytest_homeassistant_custom_component.common import MockConfigEntry, async_fire_time_changed

from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr, entity_registry as er, issue_registry as ir
from homeassistant.util import dt as dt_util

from custom_components.replace_device import repairs
from custom_components.replace_device.const import DOMAIN
from custom_components.replace_device.matching import match

OLD_SENSORS = [
    ("temperature", "sensor", "temperature", "°C"),
    ("humidity", "sensor", "humidity", "%"),
    ("battery", "sensor", "battery", "%"),
    ("rssi", "sensor", None, "dBm"),
]
NEW_SENSORS = [
    ("temperature", "sensor", "temperature", "°C"),
    ("humidity", "sensor", "humidity", "%"),
    ("battery", "sensor", "battery", "%"),
    ("linkquality", "sensor", None, "lqi"),
    ("pressure", "sensor", "pressure", "hPa"),
]


def _device(hass, platform, ident, name, sensors, model="WSDCGQ11LM"):
    config_entry = MockConfigEntry(domain=platform, title=platform)
    config_entry.add_to_hass(hass)
    device = dr.async_get(hass).async_get_or_create(
        config_entry_id=config_entry.entry_id,
        identifiers={(platform, ident)},
        name=name,
        manufacturer="Aqara",
        model=model,
    )
    registry = er.async_get(hass)
    for key, domain, device_class, unit in sensors:
        registry.async_get_or_create(
            domain,
            platform,
            f"{ident}-{key}",
            suggested_object_id=f"{name}_{key}".lower().replace(" ", "_"),
            device_id=device.id,
            config_entry=config_entry,
            original_device_class=device_class,
            original_name=key.capitalize(),
            unit_of_measurement=unit,
        )
    return device


async def _setup(hass):
    entry = MockConfigEntry(domain=DOMAIN, data={})
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


async def test_match(hass: HomeAssistant) -> None:
    old = _device(hass, "zha", "old", "Kitchen", OLD_SENSORS)
    new = _device(hass, "mqtt", "new", "0x00158d0001", NEW_SENSORS)
    registry = er.async_get(hass)
    result = match(er.async_entries_for_device(registry, old.id), er.async_entries_for_device(registry, new.id))
    assert result == {
        "sensor.kitchen_temperature": "sensor.0x00158d0001_temperature",
        "sensor.kitchen_humidity": "sensor.0x00158d0001_humidity",
        "sensor.kitchen_battery": "sensor.0x00158d0001_battery",
        "sensor.kitchen_rssi": None,
    }


async def test_wizard(hass: HomeAssistant, tmp_path) -> None:
    hass.config.config_dir = str(tmp_path)
    old = _device(hass, "zha", "old", "Kitchen", OLD_SENSORS)
    new = _device(hass, "mqtt", "new", "0x00158d0001", NEW_SENSORS)
    from homeassistant.helpers import area_registry as ar, label_registry as lr

    kitchen = ar.async_get(hass).async_create("Køkken")
    label = lr.async_get(hass).async_create("Klima")
    dr.async_get(hass).async_update_device(old.id, area_id=kitchen.id)
    registry = er.async_get(hass)
    old_temp = registry.async_update_entity(
        "sensor.kitchen_temperature", name="Køkken temperatur", labels={label.label_id}, icon="mdi:thermometer"
    )
    registry.async_update_entity_options("sensor.kitchen_temperature", "sensor", {"suggested_display_precision": 1})
    hass.states.async_set("sensor.kitchen_temperature", "unavailable")
    (tmp_path / "automations.yaml").write_text(
        "- id: '1'\n  alias: Kitchen too warm\n  triggers:\n  - trigger: device\n"
        f"    device_id: {old.id}\n    entity_id: {old_temp.id}\n    domain: sensor\n    type: temperature\n"
        "  actions: []\n"
    )
    entry = await _setup(hass)

    result = await hass.config_entries.subentries.async_init((entry.entry_id, "replace"), context={"source": "user"})
    assert result["type"] == "form" and result["step_id"] == "user"
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"], {"old_device": old.id, "new_device": old.id}
    )
    assert result["errors"] == {"base": "same_device"}
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"], {"old_device": old.id, "new_device": new.id}
    )
    assert result["step_id"] == "match"
    assert result["data_schema"]({})["sensor.kitchen_humidity"] == "sensor.0x00158d0001_humidity"
    # Two old entities can't take the same new one.
    picked = {
        "sensor.kitchen_temperature": "sensor.0x00158d0001_temperature",
        "sensor.kitchen_humidity": "sensor.0x00158d0001_temperature",
        "sensor.kitchen_battery": "sensor.0x00158d0001_battery",
        "sensor.kitchen_rssi": "none",
    }
    result = await hass.config_entries.subentries.async_configure(result["flow_id"], picked)
    assert result["errors"] == {"base": "duplicate"}
    picked["sensor.kitchen_humidity"] = "sensor.0x00158d0001_humidity"
    result = await hass.config_entries.subentries.async_configure(result["flow_id"], picked)
    assert result["step_id"] == "confirm"
    summary = result["description_placeholders"]["summary"]
    assert "Køkken temperatur (sensor.kitchen_temperature) ← sensor.0x00158d0001_temperature" in summary
    assert "sensor.kitchen_rssi" in summary and "sensor.0x00158d0001_pressure" in summary

    result = await hass.config_entries.subentries.async_configure(result["flow_id"], {"remove_old": True})
    await hass.async_block_till_done()
    assert result["type"] == "abort" and result["reason"] == "replaced"
    assert result["description_placeholders"]["moved"] == "3"

    # The old device is gone, the new one has its name and area.
    devices = dr.async_get(hass)
    assert devices.async_get(old.id) is None
    new = devices.async_get(new.id)
    assert new.name_by_user == "Kitchen" and new.area_id == kitchen.id
    # The new entity has the old entity_id and everything the user set.
    temp = registry.async_get("sensor.kitchen_temperature")
    assert temp.device_id == new.id and temp.platform == "mqtt"
    assert temp.name == "Køkken temperatur" and temp.icon == "mdi:thermometer" and temp.labels == {label.label_id}
    assert temp.options["sensor"]["suggested_display_precision"] == 1
    assert registry.async_get("sensor.0x00158d0001_temperature") is None
    assert registry.async_get("sensor.kitchen_rssi") is None
    assert registry.async_get("sensor.0x00158d0001_pressure") is not None
    # The automation points at the new device and the new entity.
    automations = (tmp_path / "automations.yaml").read_text()
    assert old.id not in automations and new.id in automations
    assert old_temp.id not in automations and temp.id in automations
    assert entry.runtime_data.history[0]["files"] == ["automation"]


async def test_suggested_repair(hass: HomeAssistant, freezer) -> None:
    old = _device(hass, "zha", "old", "Kitchen", OLD_SENSORS)
    for key, *_ in OLD_SENSORS:
        hass.states.async_set(f"sensor.kitchen_{key}", "unavailable")
    _device(hass, "zha", "other", "Hallway", OLD_SENSORS, model="Other")
    freezer.tick(timedelta(hours=2))
    await _setup(hass)

    new = _device(hass, "mqtt", "new", "0x00158d0001", NEW_SENSORS)
    freezer.tick(timedelta(seconds=121))
    async_fire_time_changed(hass, dt_util.utcnow())
    await hass.async_block_till_done()

    issue = ir.async_get(hass).async_get_issue(DOMAIN, f"suggest_{new.id}")
    assert issue is not None and issue.translation_placeholders["old"] == "Kitchen"
    assert issue.data["candidates"] == [old.id]
    flow = await repairs.async_create_fix_flow(hass, issue.issue_id, issue.data)
    flow.hass, flow.handler, flow.flow_id = hass, DOMAIN, "x"
    result = await flow.async_step_init()
    assert result["step_id"] == "confirm"
    result = await flow.async_step_confirm({"remove_old": True})
    assert result["type"] == "create_entry"
    await hass.async_block_till_done()
    assert er.async_get(hass).async_get("sensor.kitchen_temperature").platform == "mqtt"


async def test_no_suggestion_when_alive(hass: HomeAssistant, freezer) -> None:
    _device(hass, "zha", "old", "Kitchen", OLD_SENSORS)
    hass.states.async_set("sensor.kitchen_temperature", "21")
    await _setup(hass)
    new = _device(hass, "mqtt", "new", "0x00158d0001", NEW_SENSORS)
    freezer.tick(timedelta(seconds=121))
    async_fire_time_changed(hass, dt_util.utcnow())
    await hass.async_block_till_done()
    assert ir.async_get(hass).async_get_issue(DOMAIN, f"suggest_{new.id}") is None


async def test_panel_api_and_undo(hass: HomeAssistant, hass_ws_client, tmp_path, monkeypatch) -> None:
    hass.config.config_dir = str(tmp_path)
    monkeypatch.setattr("custom_components.replace_device.suggest.DEAD_AFTER", 0)
    old = _device(hass, "zha", "old", "Kitchen", OLD_SENSORS)
    for key, *_ in OLD_SENSORS:
        hass.states.async_set(f"sensor.kitchen_{key}", "unavailable")
    new = _device(hass, "mqtt", "new", "0x00158d0001", NEW_SENSORS)
    (tmp_path / "automations.yaml").write_text(f"- id: '1'\n  alias: A\n  triggers:\n  - device_id: {old.id}\n")
    await _setup(hass)
    client = await hass_ws_client(hass)

    await client.send_json_auto_id({"type": "replace_device/devices"})
    devices = {d["id"]: d for d in (await client.receive_json())["result"]["devices"]}
    assert devices[old.id]["dead"] and devices[old.id]["twins"] == [new.id]
    assert not devices[new.id]["dead"]

    await client.send_json_auto_id({"type": "replace_device/plan", "old": old.id, "new": new.id})
    plan = (await client.receive_json())["result"]
    assert plan["mapping"]["sensor.kitchen_temperature"] == "sensor.0x00158d0001_temperature"
    assert {e["entity_id"] for e in plan["new_entities"]} >= {"sensor.0x00158d0001_pressure"}

    await client.send_json_auto_id(
        {"type": "replace_device/replace", "old": old.id, "new": new.id, "mapping": plan["mapping"]}
    )
    result = (await client.receive_json())["result"]
    await hass.async_block_till_done()
    assert result["moved"] == 3 and result["removed"]
    registry = er.async_get(hass)
    assert registry.async_get("sensor.kitchen_temperature").platform == "mqtt"
    assert new.id in (tmp_path / "automations.yaml").read_text()

    await client.send_json_auto_id({"type": "replace_device/history"})
    history = (await client.receive_json())["result"]["history"]
    assert history[0]["old_device"]["name"] == "Kitchen" and not history[0]["undone"]

    # Undo: the new device gets its own names and ids back.
    await client.send_json_auto_id({"type": "replace_device/undo", "record": result["id"]})
    assert (await client.receive_json())["success"]
    await hass.async_block_till_done()
    temp = registry.async_get("sensor.0x00158d0001_temperature")
    assert temp is not None and temp.device_id == new.id and temp.name is None
    assert registry.async_get("sensor.kitchen_temperature") is None
    assert dr.async_get(hass).async_get(new.id).name_by_user is None
    assert old.id in (tmp_path / "automations.yaml").read_text()
    await client.send_json_auto_id({"type": "replace_device/undo", "record": result["id"]})
    assert not (await client.receive_json())["success"]


async def test_move_many_zha_to_z2m(hass: HomeAssistant, hass_ws_client) -> None:
    """ZHA and Zigbee2MQTT devices are paired on their IEEE address, whatever they are called."""
    from pytest_homeassistant_custom_component.common import async_mock_service

    from custom_components.replace_device.hardware import hardware_keys

    published = async_mock_service(hass, "mqtt", "publish")
    zha_entry = MockConfigEntry(domain="zha", title="ZHA")
    zha_entry.add_to_hass(hass)
    mqtt_entry = MockConfigEntry(domain="mqtt", title="Mosquitto broker")
    mqtt_entry.add_to_hass(hass)
    devices, registry = dr.async_get(hass), er.async_get(hass)
    made = {}
    for name, ieee in (("Stue sensor", "00:15:8d:00:01:a2:b3:c4"), ("Gang knap", "54:ef:44:10:01:69:24:45")):
        old = devices.async_get_or_create(
            config_entry_id=zha_entry.entry_id,
            identifiers={("zha", ieee)},
            connections={(dr.CONNECTION_ZIGBEE, ieee)},
            name=name,
            manufacturer="LUMI",
            model="lumi.weather",
        )
        compact = ieee.replace(":", "")
        new = devices.async_get_or_create(
            config_entry_id=mqtt_entry.entry_id,
            identifiers={("mqtt", f"zigbee2mqtt_0x{compact}")},
            name=f"0x{compact}",
            manufacturer="Aqara",
            model="WSDCGQ11LM",
        )
        registry.async_get_or_create(
            "sensor",
            "zha",
            f"{ieee}-temp",
            suggested_object_id=f"{name}_temperatur".lower().replace(" ", "_"),
            device_id=old.id,
            config_entry=zha_entry,
            original_device_class="temperature",
            unit_of_measurement="°C",
        )
        registry.async_get_or_create(
            "sensor",
            "mqtt",
            f"0x{compact}-temp",
            suggested_object_id=f"0x{compact}_temperature",
            device_id=new.id,
            config_entry=mqtt_entry,
            original_device_class="temperature",
            unit_of_measurement="°C",
        )
        made[name] = (old, new)
        assert hardware_keys(old) & hardware_keys(new) == {f"ieee:{compact}"}
    # A Zigbee2MQTT device with no ZHA twin, and an MQTT device that is not Zigbee2MQTT.
    lonely = devices.async_get_or_create(
        config_entry_id=zha_entry.entry_id, identifiers={("zha", "aa:aa:aa:aa:aa:aa:aa:aa")}, name="Lonely"
    )
    registry.async_get_or_create("light", "zha", "lonely", device_id=lonely.id, config_entry=zha_entry)
    await _setup(hass)
    client = await hass_ws_client(hass)

    await client.send_json_auto_id({"type": "replace_device/migrate_plan", "source": "zha", "target": "zigbee2mqtt"})
    plan = (await client.receive_json())["result"]
    assert {p["old"]["name"] for p in plan["pairs"]} == {"Stue sensor", "Gang knap"}
    assert all(p["by"] == "ieee" and p["matched"] == 1 for p in plan["pairs"])
    assert [m["name"] for m in plan["missing"]] == ["Lonely"]

    pairs = [{"old": p["old"]["id"], "new": p["new"]["id"]} for p in plan["pairs"]]
    await client.send_json_auto_id({"type": "replace_device/migrate", "pairs": pairs, "rename_z2m": True})
    result = (await client.receive_json())["result"]
    await hass.async_block_till_done()
    assert result["devices"] == 2 and result["moved"] == 2 and not result["failed"]
    assert registry.async_get("sensor.stue_sensor_temperatur").platform == "mqtt"
    assert devices.async_get(made["Gang knap"][1].id).name_by_user == "Gang knap"
    topics = {c.data["topic"] for c in published}
    assert topics == {"zigbee2mqtt/bridge/request/device/rename"}
    assert '"to": "Stue sensor"' in " ".join(c.data["payload"] for c in published)
    assert all('"homeassistant_rename": false' in c.data["payload"] for c in published)
