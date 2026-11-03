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


def test_trigger_words() -> None:
    from custom_components.replace_device.triggers import best

    ikea = [
        {"type": "action", "subtype": s}
        for s in ("on", "off", "brightness_move_up", "brightness_move_down", "brightness_stop")
    ]
    assert best({"type": "remote_button_short_press", "subtype": "turn_on"}, ikea)["subtype"] == "on"
    assert best({"type": "remote_button_long_press", "subtype": "dim_up"}, ikea)["subtype"] == "brightness_move_up"
    assert best({"type": "remote_button_long_release", "subtype": "dim_up"}, ikea)["subtype"] == "brightness_stop"
    aqara = [{"type": "action", "subtype": s} for s in ("single", "double", "hold", "release")]
    assert best({"type": "remote_button_short_press", "subtype": "remote_button"}, aqara)["subtype"] == "single"
    assert best({"type": "remote_button_double_press", "subtype": "remote_button"}, aqara)["subtype"] == "double"
    assert best({"type": "device_rotated", "subtype": "left"}, aqara) is None
    # And back: Zigbee2MQTT -> ZHA.
    zha = [
        {"type": "remote_button_short_press", "subtype": "turn_on"},
        {"type": "remote_button_short_press", "subtype": "turn_off"},
    ]
    assert best({"type": "action", "subtype": "off"}, zha)["subtype"] == "turn_off"


async def test_translate_triggers_ai_and_undo_all(hass: HomeAssistant, hass_ws_client, tmp_path) -> None:
    """ZHA button triggers become Zigbee2MQTT ones; the AI answers what the words can't; one tap undoes it all."""
    from unittest.mock import patch

    from homeassistant.core import SupportsResponse

    hass.config.config_dir = str(tmp_path)
    zha_entry = MockConfigEntry(domain="zha", title="ZHA")
    zha_entry.add_to_hass(hass)
    mqtt_entry = MockConfigEntry(domain="mqtt", title="Mosquitto broker")
    mqtt_entry.add_to_hass(hass)
    devices, registry = dr.async_get(hass), er.async_get(hass)
    ieee = "00:15:8d:00:01:a2:b3:c4"
    old = devices.async_get_or_create(
        config_entry_id=zha_entry.entry_id,
        identifiers={("zha", ieee)},
        connections={(dr.CONNECTION_ZIGBEE, ieee)},
        name="Gang knap",
    )
    new = devices.async_get_or_create(
        config_entry_id=mqtt_entry.entry_id,
        identifiers={("mqtt", "zigbee2mqtt_0x00158d0001a2b3c4")},
        name="0x00158d0001a2b3c4",
    )
    registry.async_get_or_create(
        "sensor",
        "zha",
        "b",
        suggested_object_id="gang_knap_batteri",
        device_id=old.id,
        config_entry=zha_entry,
        original_device_class="battery",
        unit_of_measurement="%",
    )
    registry.async_get_or_create(
        "sensor",
        "zha",
        "x",
        suggested_object_id="gang_knap_analog",
        device_id=old.id,
        config_entry=zha_entry,
        original_name="Analog input",
    )
    registry.async_get_or_create(
        "sensor",
        "mqtt",
        "b2",
        suggested_object_id="0x00158d0001a2b3c4_battery",
        device_id=new.id,
        config_entry=mqtt_entry,
        original_device_class="battery",
        unit_of_measurement="%",
    )
    registry.async_get_or_create(
        "sensor",
        "mqtt",
        "x2",
        suggested_object_id="0x00158d0001a2b3c4_local_temperature",
        device_id=new.id,
        config_entry=mqtt_entry,
        original_name="Local temperature",
    )
    (tmp_path / "automations.yaml").write_text(
        "- id: '1'\n  alias: Gang lys\n  triggers:\n"
        f"  - trigger: device\n    device_id: {old.id}\n    domain: zha\n    type: remote_button_short_press\n"
        "    subtype: remote_button\n    id: kort\n"
        f"  - trigger: device\n    device_id: {old.id}\n    domain: zha\n    type: device_shaken\n"
        "    subtype: device_shaken\n"
        f"  - trigger: device\n    device_id: {old.id}\n    domain: zha\n    type: device_rotated\n    subtype: left\n"
        "  actions: []\n"
    )
    (tmp_path / "packages").mkdir()
    (tmp_path / "packages" / "gang.yaml").write_text(f"automation:\n  - triggers:\n    - device_id: {old.id}\n")
    asked = []

    async def generate_data(call):
        asked.append(call.data["instructions"])
        if "triggers" in call.data["task_name"]:
            return {"data": '{"answers": [{"n": 1, "pick": 3}, {"n": 2, "pick": 0}]}'}
        return {"data": {"answers": [{"n": 1, "pick": 1}]}}

    hass.services.async_register("ai_task", "generate_data", generate_data, supports_response=SupportsResponse.ONLY)
    entry = MockConfigEntry(domain=DOMAIN, data={}, options={"ai_task": "ai_task.gemini"})
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    client = await hass_ws_client(hass)

    # The AI pairs "Analog input" with "Local temperature", which the words can't.
    await client.send_json_auto_id({"type": "replace_device/plan", "old": old.id, "new": new.id})
    plan = (await client.receive_json())["result"]
    assert plan["mapping"]["sensor.gang_knap_analog"] == "sensor.0x00158d0001a2b3c4_local_temperature"
    assert plan["ai"] == ["sensor.gang_knap_analog"] and plan["ai_enabled"]

    available = [
        {
            "platform": "device",
            "domain": "mqtt",
            "device_id": new.id,
            "type": "action",
            "subtype": s,
            "discovery_id": f"0x00158d0001a2b3c4 action_{s}",
            "metadata": {},
        }
        for s in ("single", "double", "shake")
    ]
    with patch(
        "custom_components.replace_device.triggers.async_get_device_automations", return_value={new.id: available}
    ):
        await client.send_json_auto_id({"type": "replace_device/migrate", "pairs": [{"old": old.id, "new": new.id}]})
        result = (await client.receive_json())["result"]
    await hass.async_block_till_done()
    assert result["devices"] == 1 and result["moved"] == 2
    assert result["unresolved"] == ["Gang lys: device_rotated / left"]

    from homeassistant.util.yaml import load_yaml

    trigger_single, trigger_shake, trigger_rotated = load_yaml(str(tmp_path / "automations.yaml"))[0]["triggers"]
    assert trigger_single == {
        "trigger": "device",
        "domain": "mqtt",
        "device_id": new.id,
        "type": "action",
        "subtype": "single",
        "discovery_id": "0x00158d0001a2b3c4 action_single",
        "id": "kort",
    }
    assert trigger_shake["subtype"] == "shake"  # answered by the AI
    assert trigger_rotated["domain"] == "zha" and trigger_rotated["device_id"] == new.id
    assert new.id in (tmp_path / "packages" / "gang.yaml").read_text()

    # Undo all: the automation is as before, with the old device.
    await client.send_json_auto_id({"type": "replace_device/undo", "batch": result["batch"]})
    assert (await client.receive_json())["result"] == {"undone": 1}
    await hass.async_block_till_done()
    automations = (tmp_path / "automations.yaml").read_text()
    assert "remote_button_short_press" in automations and "discovery_id" not in automations
    assert old.id in automations and new.id not in automations
    assert old.id in (tmp_path / "packages" / "gang.yaml").read_text()


async def test_checks_other_places_and_groups(hass: HomeAssistant, hass_ws_client, tmp_path) -> None:
    """Values and units that differ, things only the old one had, other integrations, dashboards and Zigbee groups."""
    from homeassistant.setup import async_setup_component

    hass.config.config_dir = str(tmp_path)
    (tmp_path / "configuration.yaml").write_text("automation: !include automations.yaml\n")
    assert await async_setup_component(hass, "lovelace", {})
    zha_entry = MockConfigEntry(domain="zha", title="ZHA")
    zha_entry.add_to_hass(hass)
    mqtt_entry = MockConfigEntry(domain="mqtt", title="Mosquitto broker")
    mqtt_entry.add_to_hass(hass)
    devices, registry = dr.async_get(hass), er.async_get(hass)
    ieee = "00:15:8d:00:01:a2:b3:c4"
    old = devices.async_get_or_create(
        config_entry_id=zha_entry.entry_id,
        identifiers={("zha", ieee)},
        connections={(dr.CONNECTION_ZIGBEE, ieee)},
        name="Stik",
    )
    new = devices.async_get_or_create(
        config_entry_id=mqtt_entry.entry_id,
        identifiers={("mqtt", "zigbee2mqtt_0x00158d0001a2b3c4")},
        name="0x00",
    )
    for platform, entry, device, uid, object_id, kwargs in (
        (
            "zha",
            zha_entry,
            old,
            "e",
            "stik_energi",
            {
                "original_device_class": "energy",
                "unit_of_measurement": "Wh",
                "capabilities": {"state_class": "total_increasing"},
            },
        ),
        ("zha", zha_entry, old, "s", "stik_start", {"capabilities": {"options": ["Off", "On", "Previous"]}}),
        ("zha", zha_entry, old, "r", "stik_rssi", {"original_device_class": "signal_strength"}),
        (
            "mqtt",
            mqtt_entry,
            new,
            "e2",
            "z_energy",
            {
                "original_device_class": "energy",
                "unit_of_measurement": "kWh",
                "capabilities": {"state_class": "total_increasing"},
            },
        ),
        (
            "mqtt",
            mqtt_entry,
            new,
            "s2",
            "z_power_on_behavior",
            {"capabilities": {"options": ["off", "on", "toggle", "previous"]}},
        ),
    ):
        domain = "select" if "start" in object_id or "behavior" in object_id else "sensor"
        registry.async_get_or_create(
            domain, platform, uid, suggested_object_id=object_id, device_id=device.id, config_entry=entry, **kwargs
        )
    # Only the old one has RSSI, and an automation uses it.
    (tmp_path / "automations.yaml").write_text(
        "- id: '1'\n  alias: Svagt signal\n  triggers:\n  - trigger: state\n"
        "    entity_id: sensor.stik_rssi\n  actions:\n"
        f"  - device_id: {old.id}\n    domain: zha\n    type: issue_all_led_effect\n"
    )
    assert await async_setup_component(
        hass,
        "automation",
        {
            "automation": {
                "id": "1",
                "alias": "Svagt signal",
                "triggers": [{"trigger": "state", "entity_id": "sensor.stik_rssi"}],
                "actions": [],
            }
        },
    )
    notes = MockConfigEntry(domain="battery_notes", title="Stik batteri", data={"device_id": old.id})
    notes.add_to_hass(hass)
    from homeassistant.components.lovelace.const import LOVELACE_DATA

    await (
        hass.data[LOVELACE_DATA]
        .dashboards[None]
        .async_save({"views": [{"cards": [{"type": "device", "device_id": old.id}]}]})
    )
    # A ZHA group, made again in Zigbee2MQTT with the same name.
    registry.async_get_or_create(
        "light",
        "zha",
        "light_zha_group_0x0002",
        suggested_object_id="stue_loft",
        config_entry=zha_entry,
        original_name="Stue loft",
    )
    group_device = devices.async_get_or_create(
        config_entry_id=mqtt_entry.entry_id,
        identifiers={("mqtt", "zigbee2mqtt_1221051039810110150109113116116_9")},
        name="Stue loft",
        model="Group",
        manufacturer="Zigbee2MQTT",
    )
    registry.async_get_or_create(
        "light", "mqtt", "g9", suggested_object_id="stue_loft_2", device_id=group_device.id, config_entry=mqtt_entry
    )
    await _setup(hass)
    client = await hass_ws_client(hass)

    await client.send_json_auto_id({"type": "replace_device/migrate_plan", "source": "zha", "target": "zigbee2mqtt"})
    plan = (await client.receive_json())["result"]
    assert [p["old"]["name"] for p in plan["pairs"]] == ["Stik"]
    checks = plan["pairs"][0]["checks"]
    assert checks["dropped_used"] == [{"entity_id": "sensor.stik_rssi", "used_in": ["Svagt signal"]}]
    by_entity = {c["entity_id"]: c for c in checks["differences"]}
    assert by_entity["sensor.stik_energi"]["energy"]
    assert by_entity["sensor.stik_energi"]["differences"] == [{"kind": "unit", "old": "Wh", "new": "kWh"}]
    assert by_entity["select.stik_start"]["differences"][0]["missing"] == ["Off", "On", "Previous"]
    assert checks["device_actions"] == ["Svagt signal: issue_all_led_effect"]
    assert checks["integrations"] == ["Stik batteri"]
    assert checks["dashboards"] == ["Overview"]
    assert plan["groups"] == [{"name": "Stue loft", "old": "light.stue_loft", "new": "light.stue_loft_2"}]

    pairs = [{"old": old.id, "new": new.id}]
    await client.send_json_auto_id({"type": "replace_device/migrate", "pairs": pairs, "groups": plan["groups"]})
    result = (await client.receive_json())["result"]
    await hass.async_block_till_done()
    assert result["devices"] == 2 and not result["failed"]
    assert notes.data == {"device_id": new.id}
    dashboard = await hass.data[LOVELACE_DATA].dashboards[None].async_load(False)
    assert dashboard["views"][0]["cards"][0]["device_id"] == new.id
    assert registry.async_get("light.stue_loft").platform == "mqtt"
    assert registry.async_get("light.stue_loft_2") is None

    await client.send_json_auto_id({"type": "replace_device/undo", "batch": result["batch"]})
    assert (await client.receive_json())["result"] == {"undone": 2}
    await hass.async_block_till_done()
    assert notes.data == {"device_id": old.id}
    assert registry.async_get("light.stue_loft_2").platform == "mqtt"


async def test_robust_and_unambiguous(hass: HomeAssistant, hass_ws_client, tmp_path, freezer) -> None:
    """A failing step doesn't stop a replacement, shared hardware ids are not guessed, the silent repair goes away."""
    from unittest.mock import patch

    hass.config.config_dir = str(tmp_path)
    # automations.yaml that can't be read back (a !secret) and a dashboard step that blows up.
    (tmp_path / "automations.yaml").write_text("- id: '1'\n  alias: A\n  triggers: []\n  actions:\n  - x: !secret y\n")
    old = _device(hass, "zha", "old", "Kitchen", OLD_SENSORS)
    new = _device(hass, "mqtt", "new", "0x00158d0001", NEW_SENSORS)
    # Two Shelly channels sharing one serial number on each side.
    shelly_old = MockConfigEntry(domain="shelly", title="Shelly")
    shelly_old.add_to_hass(hass)
    shelly_new = MockConfigEntry(domain="matter", title="Matter")
    shelly_new.add_to_hass(hass)
    devices, registry = dr.async_get(hass), er.async_get(hass)
    for n in (1, 2):
        for entry, platform in ((shelly_old, "shelly"), (shelly_new, "matter")):
            d = devices.async_get_or_create(
                config_entry_id=entry.entry_id,
                identifiers={(platform, f"aabbcc-{n}")},
                serial_number="SHELLY123456",
                name=f"{platform} {n}",
            )
            registry.async_get_or_create("switch", platform, f"{platform}{n}", device_id=d.id, config_entry=entry)
    await _setup(hass)
    client = await hass_ws_client(hass)
    await client.send_json_auto_id({"type": "replace_device/migrate_plan", "source": "shelly", "target": "matter"})
    plan = (await client.receive_json())["result"]
    assert plan["pairs"] == [] and len(plan["missing"]) == 2

    with patch(
        "custom_components.replace_device.references.async_rewrite_dashboards", side_effect=RuntimeError("boom")
    ):
        await client.send_json_auto_id(
            {
                "type": "replace_device/replace",
                "old": old.id,
                "new": new.id,
                "mapping": {"sensor.kitchen_temperature": "sensor.0x00158d0001_temperature"},
            }
        )
        result = (await client.receive_json())["result"]
    await hass.async_block_till_done()
    assert result["moved"] == 1 and result["dashboards"] == [] and result["failed"] == []
    assert er.async_get(hass).async_get("sensor.kitchen_temperature").platform == "mqtt"

    # Ten minutes without a value: a repair. A value: it goes away.
    freezer.tick(timedelta(minutes=11))
    async_fire_time_changed(hass, dt_util.utcnow())
    await hass.async_block_till_done()
    assert ir.async_get(hass).async_get_issue(DOMAIN, f"silent_{new.id}") is not None
    hass.states.async_set("sensor.kitchen_temperature", "21.5")
    await hass.async_block_till_done()
    assert ir.async_get(hass).async_get_issue(DOMAIN, f"silent_{new.id}") is None


def test_z2m_base_topic(hass: HomeAssistant) -> None:
    """Zigbee2MQTT can run under another base topic; it is read from the device's discovery data."""
    from types import SimpleNamespace
    from unittest.mock import patch

    from custom_components.replace_device.hardware import z2m_base_topic

    device = SimpleNamespace(id="x")
    info = {
        "entities": [{"discovery_data": {"payload": {"availability": [{"topic": "zigbee2mqtt_sensor/bridge/state"}]}}}]
    }
    with patch("homeassistant.components.mqtt.debug_info.info_for_device", return_value=info):
        assert z2m_base_topic(hass, device, "zigbee2mqtt") == "zigbee2mqtt_sensor"
    with patch("homeassistant.components.mqtt.debug_info.info_for_device", side_effect=KeyError):
        assert z2m_base_topic(hass, device, "zigbee2mqtt") == "zigbee2mqtt"
