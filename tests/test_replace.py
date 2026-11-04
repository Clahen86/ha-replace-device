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
    assert registry.async_get("sensor.kitchen_pressure") is not None  # named after the device
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
            return {"data": '{"devices": [{"device": 1, "answers": [{"n": 1, "pick": 3}, {"n": 2, "pick": 0}]}]}'}
        return {"data": {"devices": [{"device": 1, "answers": [{"n": 1, "pick": 1}]}]}}

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


async def test_blueprint_zha_event_and_mqtt_listeners(hass: HomeAssistant, tmp_path) -> None:
    """A ZHA->Z2M move fixes a ZHA/Z2M blueprint and a zha_event trigger; a Z2M->ZHA move fixes an MQTT trigger."""
    from pathlib import Path
    from unittest.mock import patch

    from homeassistant.util.yaml import load_yaml

    from custom_components.replace_device.replace import async_plan

    hass.config.config_dir = str(tmp_path)
    blueprints = tmp_path / "blueprints" / "automation" / "damru"
    blueprints.mkdir(parents=True)
    (blueprints / "rodret.yaml").write_text((Path(__file__).parent / "fixtures" / "rodret.yaml").read_text())
    zha_entry = MockConfigEntry(domain="zha", title="ZHA")
    zha_entry.add_to_hass(hass)
    mqtt_entry = MockConfigEntry(domain="mqtt", title="Mosquitto broker")
    mqtt_entry.add_to_hass(hass)
    devices = dr.async_get(hass)
    ieee = "08:dd:eb:ff:fe:60:9e:76"
    zha = devices.async_get_or_create(
        config_entry_id=zha_entry.entry_id,
        identifiers={("zha", ieee)},
        connections={(dr.CONNECTION_ZIGBEE, ieee)},
        name="Kontakt stue",
    )
    z2m = devices.async_get_or_create(
        config_entry_id=mqtt_entry.entry_id,
        identifiers={("mqtt", "zigbee2mqtt_0x08ddebfffe609e76")},
        name="0x08ddebfffe609e76",
    )
    (tmp_path / "automations.yaml").write_text(
        "- id: '1'\n  alias: Sofa lys\n  use_blueprint:\n    path: damru/rodret.yaml\n    input:\n"
        f"      remote_device: {zha.id}\n      light: light.sofa_lys\n"
        "- id: '2'\n  alias: Tænd med kontakt\n  triggers:\n  - trigger: event\n    event_type: zha_event\n"
        f"    event_data:\n      device_ieee: '{ieee}'\n      command: 'on'\n  actions: []\n"
    )
    entry = await _setup(hass)
    available = [
        {
            "platform": "device",
            "domain": "mqtt",
            "device_id": z2m.id,
            "type": "action",
            "subtype": s,
            "discovery_id": f"0x08ddebfffe609e76 action_{s}",
        }
        for s in ("on", "off", "brightness_move_up", "brightness_move_down", "brightness_stop")
    ]
    with patch(
        "custom_components.replace_device.triggers.async_get_device_automations", return_value={z2m.id: available}
    ):
        result = await entry.runtime_data.async_replace(async_plan(hass, zha.id, z2m.id), True, rename_z2m=True)
    await hass.async_block_till_done()
    assert result["triggers"]["unresolved"] == []
    sofa, switch_on = load_yaml(str(tmp_path / "automations.yaml"))
    assert sofa["use_blueprint"]["input"] == {
        "light": "light.sofa_lys",
        "remote_name": "Kontakt stue",
        "base_topic": "zigbee2mqtt",
    }
    assert switch_on["triggers"][0]["type"] == "action" and switch_on["triggers"][0]["subtype"] == "on"

    # And back: Zigbee2MQTT -> ZHA. The blueprint gets the ZHA device again; an MQTT trigger becomes a device trigger.
    zha2 = devices.async_get_or_create(
        config_entry_id=zha_entry.entry_id, identifiers={("zha", "08:dd:eb:ff:fe:60:9e:77")}, name="Ny kontakt"
    )
    devices.async_update_device(z2m.id, name="Kontakt stue")
    (tmp_path / "automations.yaml").write_text(
        "- id: '1'\n  alias: Sofa lys\n  use_blueprint:\n    path: damru/rodret.yaml\n    input:\n"
        "      remote_name: Kontakt stue\n      base_topic: zigbee2mqtt\n      light: light.sofa_lys\n"
        "- id: '3'\n  alias: Sluk\n  triggers:\n  - trigger: mqtt\n    topic: zigbee2mqtt/Kontakt stue/action\n"
        "    payload: 'off'\n  actions: []\n"
    )
    zha_triggers = [
        {"platform": "device", "domain": "zha", "device_id": zha2.id, "type": "remote_button_short_press", "subtype": s}
        for s in ("turn_on", "turn_off")
    ]
    with patch(
        "custom_components.replace_device.triggers.async_get_device_automations", return_value={zha2.id: zha_triggers}
    ):
        await entry.runtime_data.async_replace(async_plan(hass, z2m.id, zha2.id), True)
    await hass.async_block_till_done()
    sofa, off = load_yaml(str(tmp_path / "automations.yaml"))
    assert sofa["use_blueprint"]["input"] == {"light": "light.sofa_lys", "remote_device": zha2.id}
    assert off["triggers"][0]["domain"] == "zha" and off["triggers"][0]["subtype"] == "turn_off"


async def test_code_outside_home_assistant(hass: HomeAssistant, tmp_path) -> None:
    """AppDaemon or Node-RED code that mentions the old device is reported – and only then."""
    from custom_components.replace_device.checks import async_checks
    from custom_components.replace_device.replace import async_plan

    hass.config.config_dir = str(tmp_path)
    zha_entry = MockConfigEntry(domain="zha", title="ZHA")
    zha_entry.add_to_hass(hass)
    ieee = "08:dd:eb:ff:fe:60:9e:76"
    old = dr.async_get(hass).async_get_or_create(
        config_entry_id=zha_entry.entry_id,
        identifiers={("zha", ieee)},
        connections={(dr.CONNECTION_ZIGBEE, ieee)},
        name="Kontakt stue",
    )
    new = _device(hass, "mqtt", "new", "0x08ddebfffe609e76", NEW_SENSORS)
    apps = tmp_path / "appdaemon" / "apps"
    apps.mkdir(parents=True)
    (apps / "lys.py").write_text("self.listen_event(self.tryk, 'zha_event')  # nothing about the device\n")
    plan = async_plan(hass, old.id, new.id)
    assert (await async_checks(hass, plan))["outside"] == []
    (apps / "knap.py").write_text(f"if data['device_ieee'] == '{ieee}':\n    self.turn_on('light.sofa')\n")
    (tmp_path / "node-red").mkdir()
    (tmp_path / "node-red" / "flows.json").write_text('[{"topic": "zigbee2mqtt/0x08ddebfffe609e76/action"}]')
    assert (await async_checks(hass, plan))["outside"] == ["appdaemon/apps/knap.py", "node-red/flows.json"]


async def test_undo_then_do_again(hass: HomeAssistant, tmp_path) -> None:
    """After undo the old device is gone; "do again" gives the old entity ids, settings and references back."""
    from custom_components.replace_device.replace import async_plan

    hass.config.config_dir = str(tmp_path)
    old = _device(hass, "zha", "old", "Kitchen", OLD_SENSORS)
    new = _device(hass, "mqtt", "new", "0x00158d0001", NEW_SENSORS)
    registry = er.async_get(hass)
    registry.async_update_entity("sensor.kitchen_temperature", name="Køkken temp", icon="mdi:thermometer")
    (tmp_path / "automations.yaml").write_text(f"- id: '1'\n  alias: A\n  triggers:\n  - device_id: {old.id}\n")
    entry = await _setup(hass)
    replacer = entry.runtime_data
    result = await replacer.async_replace(async_plan(hass, old.id, new.id), True)
    await hass.async_block_till_done()
    assert dr.async_get(hass).async_get(old.id) is None

    assert await replacer.async_undo(result["id"])
    await hass.async_block_till_done()
    assert registry.async_get("sensor.kitchen_temperature") is None
    assert registry.async_get("sensor.0x00158d0001_temperature").name is None
    assert old.id in (tmp_path / "automations.yaml").read_text()

    assert await replacer.async_redo(result["id"])
    await hass.async_block_till_done()
    temp = registry.async_get("sensor.kitchen_temperature")
    assert temp.platform == "mqtt" and temp.name == "Køkken temp" and temp.icon == "mdi:thermometer"
    assert dr.async_get(hass).async_get(new.id).name_by_user == "Kitchen"
    assert new.id in (tmp_path / "automations.yaml").read_text()
    assert not await replacer.async_redo(result["id"])


async def test_edit_pairs_afterwards(hass: HomeAssistant, hass_ws_client) -> None:
    """Temperature and humidity got mixed up: "change" swaps the names afterwards, without moving the device."""
    old = _device(hass, "zha", "old", "Kitchen", OLD_SENSORS)
    new = _device(hass, "mqtt", "new", "0x00158d0001", NEW_SENSORS)
    registry = er.async_get(hass)
    registry.async_update_entity("sensor.kitchen_temperature", name="Køkken temp")
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
    assert registry.async_get("sensor.kitchen_temperature").unique_id == "new-humidity"

    await client.send_json_auto_id({"type": "replace_device/edit_plan", "record": record})
    plan = (await client.receive_json())["result"]
    by_id = {c["entity_id"]: c["uuid"] for c in plan["choices"]}
    slots = {s["entity_id"]: s["holder"] for s in plan["slots"]}
    assert slots["sensor.kitchen_temperature"] == by_id["sensor.kitchen_temperature"]
    pressure = by_id["sensor.kitchen_pressure"]
    # Swap temperature and humidity, and give the battery name to nothing.
    mapping = {
        "sensor.kitchen_temperature": slots["sensor.kitchen_humidity"],
        "sensor.kitchen_humidity": slots["sensor.kitchen_temperature"],
        "sensor.kitchen_battery": None,
    }
    await client.send_json_auto_id({"type": "replace_device/edit", "record": record, "mapping": mapping})
    assert (await client.receive_json())["success"]
    await hass.async_block_till_done()
    temp = registry.async_get("sensor.kitchen_temperature")
    assert temp.unique_id == "new-temperature" and temp.name == "Køkken temp" and temp.device_id == new.id
    assert registry.async_get("sensor.kitchen_humidity").unique_id == "new-humidity"
    assert registry.async_get("sensor.kitchen_battery") is None
    assert registry.async_get("sensor.0x00158d0001_battery") is not None
    # A name can't go to two entities.
    bad = {"sensor.kitchen_temperature": pressure, "sensor.kitchen_humidity": pressure}
    await client.send_json_auto_id({"type": "replace_device/edit", "record": record, "mapping": bad})
    assert not (await client.receive_json())["success"]


async def test_hide_device_without_contact(hass: HomeAssistant, hass_ws_client, monkeypatch) -> None:
    """A bulb switched off at the wall can be hidden: it leaves the list and gets no replacement suggestions."""
    from custom_components.replace_device import suggest

    monkeypatch.setattr("custom_components.replace_device.suggest.DEAD_AFTER", 0)
    old = _device(hass, "zha", "old", "Kitchen", OLD_SENSORS)
    for key, *_ in OLD_SENSORS:
        hass.states.async_set(f"sensor.kitchen_{key}", "unavailable")
    await _setup(hass)
    client = await hass_ws_client(hass)
    await client.send_json_auto_id({"type": "replace_device/hide", "device": old.id, "hidden": True})
    assert (await client.receive_json())["success"]
    await client.send_json_auto_id({"type": "replace_device/devices"})
    devices = {d["id"]: d for d in (await client.receive_json())["result"]["devices"]}
    assert devices[old.id]["dead"] and devices[old.id]["hidden"] and devices[old.id]["battery"] is None

    new = _device(hass, "mqtt", "new", "0x00158d0001", NEW_SENSORS)
    suggest.async_suggest(hass, new.id)
    assert ir.async_get(hass).async_get_issue(DOMAIN, f"suggest_{new.id}") is None
    await client.send_json_auto_id({"type": "replace_device/hide", "device": old.id, "hidden": False})
    assert (await client.receive_json())["success"]
    suggest.async_suggest(hass, new.id)
    assert ir.async_get(hass).async_get_issue(DOMAIN, f"suggest_{new.id}") is not None


async def test_zha_removal_and_leftovers(hass: HomeAssistant, hass_ws_client) -> None:
    """ZHA devices are removed with zha.remove; one that comes back anyway is shown as a leftover, not paired again."""
    from pytest_homeassistant_custom_component.common import async_mock_service

    from homeassistant.config_entries import ConfigEntryState

    from custom_components.replace_device.replace import async_plan

    removed = async_mock_service(hass, "zha", "remove")
    zha_entry = MockConfigEntry(domain="zha", title="ZHA")
    zha_entry.add_to_hass(hass)
    zha_entry.mock_state(hass, ConfigEntryState.LOADED)
    mqtt_entry = MockConfigEntry(domain="mqtt", title="Mosquitto broker")
    mqtt_entry.add_to_hass(hass)
    devices, registry = dr.async_get(hass), er.async_get(hass)
    ieee = "08:6b:d7:ff:fe:00:f8:ec"

    def zha_device():
        device = devices.async_get_or_create(
            config_entry_id=zha_entry.entry_id,
            identifiers={("zha", ieee)},
            connections={(dr.CONNECTION_ZIGBEE, ieee)},
            name="LED Holly værelse",
        )
        registry.async_get_or_create(
            "switch", "zha", f"{ieee}-1", suggested_object_id="led_holly", device_id=device.id, config_entry=zha_entry
        )
        return device

    old = zha_device()
    new = devices.async_get_or_create(
        config_entry_id=mqtt_entry.entry_id,
        identifiers={("mqtt", "zigbee2mqtt_0x086bd7fffe00f8ec")},
        name="0x086b",
    )
    registry.async_get_or_create(
        "switch", "mqtt", "z1", suggested_object_id="z_switch", device_id=new.id, config_entry=mqtt_entry
    )
    entry = await _setup(hass)
    result = await entry.runtime_data.async_replace(async_plan(hass, old.id, new.id), True)
    await hass.async_block_till_done()
    assert result["removed"] and removed[0].data == {"ieee": ieee}
    assert devices.async_get(old.id) is None

    # ZHA adds it again anyway: it is a leftover, never a new pair.
    ghost = zha_device()
    client = await hass_ws_client(hass)
    await client.send_json_auto_id({"type": "replace_device/migrate_plan", "source": "zha", "target": "zigbee2mqtt"})
    plan = (await client.receive_json())["result"]
    assert plan["pairs"] == [] and [d["id"] for d in plan["leftovers"]] == [ghost.id]
    assert plan["leftovers"][0]["moved_to"].startswith("LED Holly værelse")
    await client.send_json_auto_id({"type": "replace_device/devices"})
    devs = {d["id"]: d for d in (await client.receive_json())["result"]["devices"]}
    assert devs[ghost.id]["moved_to"] and not devs[new.id]["moved_to"]
    await client.send_json_auto_id({"type": "replace_device/remove_device", "device": ghost.id})
    assert (await client.receive_json())["result"] == {"removed": True}
    assert len(removed) == 2 and devices.async_get(ghost.id) is None
    zha_entry.mock_state(hass, ConfigEntryState.NOT_LOADED)


async def test_buttons_never_pressed_in_z2m(hass: HomeAssistant, tmp_path) -> None:
    """A SOMRIG moved ZHA -> Z2M where only two presses were known yet: the full action list gives the right ones,
    and button 1 never becomes button 2. "Check buttons again" fixes what an older version left behind."""
    from unittest.mock import AsyncMock, patch

    from homeassistant.util.yaml import load_yaml

    from custom_components.replace_device.replace import async_plan

    hass.config.config_dir = str(tmp_path)
    zha_entry = MockConfigEntry(domain="zha", title="ZHA")
    zha_entry.add_to_hass(hass)
    mqtt_entry = MockConfigEntry(domain="mqtt", title="Mosquitto broker")
    mqtt_entry.add_to_hass(hass)
    devices = dr.async_get(hass)
    ieee = "5c:c7:c1:ff:fe:84:8e:5c"
    old = devices.async_get_or_create(
        config_entry_id=zha_entry.entry_id,
        identifiers={("zha", ieee)},
        connections={(dr.CONNECTION_ZIGBEE, ieee)},
        name="Holly Led Tænd/Sluk",
    )
    new = devices.async_get_or_create(
        config_entry_id=mqtt_entry.entry_id,
        identifiers={("mqtt", "zigbee2mqtt_0x5cc7c1fffe848e5c")},
        name="0x5cc7",
    )
    presses = [
        ("TÆND", "remote_button_short_press", "button_1"),
        ("SLUK", "remote_button_short_press", "button_2"),
        ("WIZ_TÆND", "remote_button_double_press", "button_1"),
        ("WIZ_SLUK", "remote_button_double_press", "button_2"),
        ("WIZ_FARVE", "remote_button_long_press", "button_1"),
        ("ALT_SLUK", "remote_button_long_press", "button_2"),
    ]
    automation = "- id: '1'\n  alias: Holly LED\n  triggers:\n" + "".join(
        f"  - trigger: device\n    device_id: {old.id}\n    domain: zha\n    type: {t}\n    subtype: {s}\n    id: {i}\n"
        for i, t, s in presses
    )
    (tmp_path / "automations.yaml").write_text(automation)
    entry = await _setup(hass)
    known = [
        {"platform": "device", "domain": "mqtt", "device_id": new.id, "type": "action", "subtype": s}
        for s in ("2_short_release", "2_initial_press")
    ]
    actions = [
        f"{b}_{p}"
        for b in (1, 2)
        for p in ("initial_press", "long_press", "short_release", "long_release", "double_press")
    ]
    with (
        patch("custom_components.replace_device.triggers.async_get_device_automations", return_value={new.id: known}),
        patch("custom_components.replace_device.triggers.async_z2m_actions", AsyncMock(return_value=actions)),
    ):
        result = await entry.runtime_data.async_replace(async_plan(hass, old.id, new.id), True)
    await hass.async_block_till_done()
    assert result["triggers"]["unresolved"] == []
    got = {t["id"]: t["subtype"] for t in load_yaml(str(tmp_path / "automations.yaml"))[0]["triggers"]}
    assert got == {
        "TÆND": "1_short_release",
        "SLUK": "2_short_release",
        "WIZ_TÆND": "1_double_press",
        "WIZ_SLUK": "2_double_press",
        "WIZ_FARVE": "1_long_press",
        "ALT_SLUK": "2_long_press",
    }

    # Left behind by an older version: still ZHA on the new device. "Check buttons again" translates them.
    (tmp_path / "automations.yaml").write_text(automation.replace(old.id, new.id))
    with (
        patch("custom_components.replace_device.triggers.async_get_device_automations", return_value={new.id: known}),
        patch("custom_components.replace_device.triggers.async_z2m_actions", AsyncMock(return_value=actions)),
    ):
        again = await entry.runtime_data.async_retranslate(result["id"])
    assert len(again["translated"]) == 6 and again["unresolved"] == []

    # Without the full list, button 1 is left for the user instead of guessed as button 2.
    (tmp_path / "automations.yaml").write_text(automation.replace(old.id, new.id))
    with (
        patch("custom_components.replace_device.triggers.async_get_device_automations", return_value={new.id: known}),
        patch("custom_components.replace_device.triggers.async_z2m_actions", AsyncMock(return_value=[])),
    ):
        guess = await entry.runtime_data.async_retranslate(result["id"])
    got = {t["id"]: t.get("subtype") for t in load_yaml(str(tmp_path / "automations.yaml"))[0]["triggers"]}
    assert got["TÆND"] == "button_1" and got["SLUK"] == "2_short_release"
    assert got["WIZ_SLUK"] == "button_2" and "Holly LED: remote_button_double_press / button_2" in guess["unresolved"]


async def test_match_across_languages(hass: HomeAssistant) -> None:
    """The TRVZB moved ZHA (Danish names) -> Zigbee2MQTT (English names): four °C numbers must not be shuffled."""
    from custom_components.replace_device.matching import match, unsure

    zha_entry = MockConfigEntry(domain="zha")
    zha_entry.add_to_hass(hass)
    mqtt_entry = MockConfigEntry(domain="mqtt")
    mqtt_entry.add_to_hass(hass)
    devices, registry = dr.async_get(hass), er.async_get(hass)
    old = devices.async_get_or_create(config_entry_id=zha_entry.entry_id, identifiers={("zha", "o")}, name="T")
    new = devices.async_get_or_create(config_entry_id=mqtt_entry.entry_id, identifiers={("mqtt", "n")}, name="N")
    zha = [
        ("external_temperature_sensor_value", "External temperature sensor value", "external_temperature_sensor_value"),
        ("frost_protection_temperature", "Frost protection temperature", "frost_protection_temperature"),
        ("lokal_temperaturforskydning", "Lokal temperaturforskydning", "local_temperature_calibration"),
        ("temperature_control_accuracy", "Temperature control accuracy", "temperature_control_accuracy"),
    ]
    for object_id, name, key in zha:
        registry.async_get_or_create(
            "number",
            "zha",
            f"0c:ef:f6:ff:fe:a4:0f:19-1-{key}",
            suggested_object_id=f"termostat_traeningsrum_{object_id}",
            device_id=old.id,
            config_entry=zha_entry,
            original_name=name,
            translation_key=key,
            unit_of_measurement="°C",
        )
    z2m = [
        ("external_temperature_input", "External temperature input"),
        ("frost_protection_temperature", "Frost protection temperature"),
        ("local_temperature_calibration", "Local temperature calibration"),
        ("temperature_accuracy", "Temperature accuracy"),
    ]
    for feature, name in z2m:
        registry.async_get_or_create(
            "number",
            "mqtt",
            f"0x0ceff6fffea40f19_{feature}_zigbee2mqtt_sensor",
            suggested_object_id=f"0x0ceff6fffea40f19_{feature}",
            device_id=new.id,
            config_entry=mqtt_entry,
            original_name=name,
            unit_of_measurement="°C",
        )
    old_entities = er.async_entries_for_device(registry, old.id)
    new_entities = er.async_entries_for_device(registry, new.id)
    result = match(old_entities, new_entities)
    assert result == {
        "number.termostat_traeningsrum_external_temperature_sensor_value": (
            "number.0x0ceff6fffea40f19_external_temperature_input"
        ),
        "number.termostat_traeningsrum_frost_protection_temperature": (
            "number.0x0ceff6fffea40f19_frost_protection_temperature"
        ),
        "number.termostat_traeningsrum_lokal_temperaturforskydning": (
            "number.0x0ceff6fffea40f19_local_temperature_calibration"
        ),
        "number.termostat_traeningsrum_temperature_control_accuracy": "number.0x0ceff6fffea40f19_temperature_accuracy",
    }
    assert isinstance(unsure(old_entities, new_entities, result), list)


async def test_device_that_lost_its_entities(hass: HomeAssistant, hass_ws_client) -> None:
    """A W100 reset in HomeKit lost its entities; the remembered names go to the Matter one, with a press warning."""
    from custom_components.replace_device.checks import async_checks
    from custom_components.replace_device.replace import async_plan

    hk = MockConfigEntry(domain="homekit_controller", title="Aqara Hub M3")
    hk.add_to_hass(hass)
    matter = MockConfigEntry(domain="matter", title="Matter")
    matter.add_to_hass(hass)
    devices, registry = dr.async_get(hass), er.async_get(hass)
    old = devices.async_get_or_create(
        config_entry_id=hk.entry_id,
        identifiers={("homekit_controller:accessory-id", "C3:85:8B:5C:4D:CB:aid:65")},
        name="Sensor",
        serial_number="54ef4410014a64af",
    )
    devices.async_update_device(old.id, name_by_user="Trænings termostat styring")
    for domain, uid, object_id, cls, events in (
        ("sensor", "C3:85:8B:5C:4D:CB_65_10", "sensor_temperature", "temperature", None),
        (
            "event",
            "C3:85:8B:5C:4D:CB_65_20",
            "sensor_button1",
            "button",
            ["single_press", "double_press"],
        ),
        ("sensor", "C3:85:8B:5C:4D:CB_99_65_10", "other_accessory", None, None),
    ):
        registry.async_get_or_create(
            domain,
            "homekit_controller",
            uid,
            suggested_object_id=object_id,
            config_entry=hk,
            device_id=old.id if "_65_" in uid else None,
            original_device_class=cls,
            capabilities={"event_types": events} if events else None,
        )
    registry.async_update_entity("sensor.sensor_temperature", name="Træning temp")
    for entity_id in ("sensor.sensor_temperature", "event.sensor_button1", "sensor.other_accessory"):
        registry.async_remove(entity_id)
    assert er.async_entries_for_device(registry, old.id) == []

    new = devices.async_get_or_create(
        config_entry_id=matter.entry_id, identifiers={("matter", "serial_54EF4410014A64AF")}, name="Climate Sensor W100"
    )
    registry.async_get_or_create(
        "sensor",
        "matter",
        "775E-1-temp",
        suggested_object_id="climate_sensor_w100_temperatur",
        device_id=new.id,
        config_entry=matter,
        original_name="Temperatur",
        original_device_class="temperature",
    )
    registry.async_get_or_create(
        "event",
        "matter",
        "775E-3-button",
        suggested_object_id="climate_sensor_w100_button_3",
        device_id=new.id,
        config_entry=matter,
        original_name="Button (3)",
        original_device_class="button",
        capabilities={"event_types": ["multi_press_1", "multi_press_2", "long_press"]},
    )
    entry = await _setup(hass)
    client = await hass_ws_client(hass)
    await client.send_json_auto_id({"type": "replace_device/devices"})
    found = {d["id"]: d for d in (await client.receive_json())["result"]["devices"]}
    assert found[old.id]["remembered"] == 2

    plan = async_plan(hass, old.id, new.id)
    assert plan.mapping == {
        "event.sensor_button1": "event.climate_sensor_w100_button_3",
        "sensor.sensor_temperature": "sensor.climate_sensor_w100_temperatur",
    }
    checks = await async_checks(hass, plan)
    press = next(c for c in checks["differences"] if c["entity_id"] == "event.sensor_button1")
    assert press["differences"][0]["new"] == ["multi_press_1", "multi_press_2", "long_press"]

    await entry.runtime_data.async_replace(plan, True)
    await hass.async_block_till_done()
    temp = registry.async_get("sensor.sensor_temperature")
    assert temp.platform == "matter" and temp.name == "Træning temp"
    assert registry.async_get("event.sensor_button1").platform == "matter"
    assert devices.async_get(new.id).name_by_user == "Trænings termostat styring"


def test_press_names_differ() -> None:
    """Live entities: presses that the new event entity doesn't have are listed."""
    from types import SimpleNamespace

    from custom_components.replace_device.checks import differences

    def entity(events):
        return SimpleNamespace(domain="event", capabilities={"event_types": events}, unit_of_measurement=None)

    found = differences(entity(["single_press", "long_press"]), entity(["multi_press_1", "long_press"]))
    assert found == [{"kind": "values", "missing": ["single_press"], "new": ["multi_press_1", "long_press"]}]


def test_statistics_gone() -> None:
    """The ZHA smoke density kept statistics, the Zigbee2MQTT one doesn't: say so before."""
    from types import SimpleNamespace

    from custom_components.replace_device.checks import differences

    old = SimpleNamespace(domain="sensor", capabilities={"state_class": "measurement"}, unit_of_measurement=None)
    new = SimpleNamespace(domain="sensor", capabilities=None, unit_of_measurement=None)
    assert differences(old, new) == [{"kind": "statistics_gone", "old": "measurement"}]


async def test_ai_one_call_context_and_quota(hass: HomeAssistant, hass_ws_client) -> None:
    """Move many asks the AI once for all devices, says what each device is, and a used-up quota is shown."""
    from homeassistant.core import SupportsResponse
    from homeassistant.exceptions import HomeAssistantError

    asked = []
    quota = {"used": False}

    async def generate_data(call):
        if quota["used"]:
            raise HomeAssistantError("429 RESOURCE_EXHAUSTED: quota per day")
        asked.append(call.data["instructions"])
        return {
            "data": {
                "devices": [
                    {"device": 1, "answers": [{"n": 1, "pick": 1}]},
                    {"device": 2, "answers": [{"n": 1, "pick": 1}]},
                ]
            }
        }

    hass.services.async_register("ai_task", "generate_data", generate_data, supports_response=SupportsResponse.ONLY)
    zha_entry = MockConfigEntry(domain="zha", title="ZHA")
    zha_entry.add_to_hass(hass)
    mqtt_entry = MockConfigEntry(domain="mqtt", title="Mosquitto broker")
    mqtt_entry.add_to_hass(hass)
    devices, registry = dr.async_get(hass), er.async_get(hass)
    pairs = []
    for n in (1, 2):
        ieee = f"00:15:8d:00:01:a2:b3:c{n}"
        old = devices.async_get_or_create(
            config_entry_id=zha_entry.entry_id,
            identifiers={("zha", ieee)},
            connections={(dr.CONNECTION_ZIGBEE, ieee)},
            name=f"Sensor {n}",
            manufacturer="LUMI",
            model="lumi.weather",
        )
        new = devices.async_get_or_create(
            config_entry_id=mqtt_entry.entry_id,
            identifiers={("mqtt", f"zigbee2mqtt_0x00158d0001a2b3c{n}")},
            name=f"0x{n}",
            manufacturer="Aqara",
            model="WSDCGQ11LM",
        )
        registry.async_get_or_create(
            "sensor",
            "zha",
            f"{ieee}-a",
            suggested_object_id=f"sensor_{n}_analog",
            device_id=old.id,
            config_entry=zha_entry,
            original_name="Analog input",
        )
        registry.async_get_or_create(
            "sensor",
            "mqtt",
            f"z{n}-t",
            suggested_object_id=f"z{n}_local_temperature",
            device_id=new.id,
            config_entry=mqtt_entry,
            original_name="Local temperature",
        )
        for device, platform, entry_ in ((old, "zha", zha_entry), (new, "mqtt", mqtt_entry)):
            registry.async_get_or_create(
                "sensor",
                platform,
                f"{device.id}-b",
                suggested_object_id=f"{device.name}_battery".lower(),
                device_id=device.id,
                config_entry=entry_,
                original_device_class="battery",
                unit_of_measurement="%",
            )
        pairs.append({"old": old.id, "new": new.id})
    entry = MockConfigEntry(domain=DOMAIN, data={}, options={"ai_task": "ai_task.gemini"})
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    client = await hass_ws_client(hass)

    await client.send_json_auto_id({"type": "replace_device/migrate", "pairs": pairs})
    result = (await client.receive_json())["result"]
    assert result["moved"] == 4 and result["ai_error"] is None
    assert len(asked) == 1 and "Device 2: Aqara" not in asked[0]
    assert "LUMI lumi.weather in ZHA → Aqara WSDCGQ11LM in Zigbee2MQTT" in asked[0]
    assert registry.async_get("sensor.sensor_1_analog").platform == "mqtt"

    # The quota is used up: the panel is told, and nothing is guessed.
    quota["used"] = True
    third = devices.async_get_or_create(config_entry_id=zha_entry.entry_id, identifiers={("zha", "x")}, name="Gammel")
    registry.async_get_or_create(
        "sensor",
        "zha",
        "x-a",
        suggested_object_id="gammel_analog",
        device_id=third.id,
        config_entry=zha_entry,
        original_name="Analog input",
    )
    fresh = devices.async_get_or_create(config_entry_id=mqtt_entry.entry_id, identifiers={("mqtt", "y")}, name="Ny")
    registry.async_get_or_create(
        "sensor",
        "mqtt",
        "y-t",
        suggested_object_id="ny_local_temperature",
        device_id=fresh.id,
        config_entry=mqtt_entry,
        original_name="Local temperature",
    )
    for device, platform, entry_ in ((third, "zha", zha_entry), (fresh, "mqtt", mqtt_entry)):
        registry.async_get_or_create(
            "sensor",
            platform,
            f"{device.id}-b",
            suggested_object_id=f"{device.name}_battery".lower(),
            device_id=device.id,
            config_entry=entry_,
            original_device_class="battery",
            unit_of_measurement="%",
        )
    await client.send_json_auto_id({"type": "replace_device/plan", "old": third.id, "new": fresh.id})
    plan = (await client.receive_json())["result"]
    assert plan["ai_error"] == "quota" and plan["mapping"]["sensor.gammel_analog"] is None


async def test_channels_pair_in_order(hass: HomeAssistant) -> None:
    """A double switch ZHA -> Z2M keeps L1/L2 apart, and HomeKit buttons 1-3 become Matter buttons 3-5 in order."""
    from custom_components.replace_device.matching import match

    devices, registry = dr.async_get(hass), er.async_get(hass)
    entries = {}
    for domain in ("zha", "mqtt", "homekit_controller", "matter"):
        entries[domain] = MockConfigEntry(domain=domain)
        entries[domain].add_to_hass(hass)

    def device(domain, name, items):
        d = devices.async_get_or_create(
            config_entry_id=entries[domain].entry_id, identifiers={(domain, name)}, name=name
        )
        for entity_domain, uid, object_id, original in items:
            registry.async_get_or_create(
                entity_domain,
                domain,
                uid,
                suggested_object_id=object_id,
                device_id=d.id,
                config_entry=entries[domain],
                original_name=original,
            )
        return er.async_entries_for_device(registry, d.id)

    zha = device(
        "zha",
        "Dobbelt",
        [
            ("switch", "aa:bb:cc:dd:ee:ff:00:11-2-6", "dobbelt_kontakt_2", None),
            ("switch", "aa:bb:cc:dd:ee:ff:00:11-1-6", "dobbelt_kontakt", None),
        ],
    )
    z2m = device(
        "mqtt",
        "0x",
        [
            ("switch", "0xaabbccddeeff0011_switch_l1_zigbee2mqtt", "x_switch_l1", "Switch (l1)"),
            ("switch", "0xaabbccddeeff0011_switch_l2_zigbee2mqtt", "x_switch_l2", "Switch (l2)"),
        ],
    )
    assert match(zha, z2m) == {
        "switch.dobbelt_kontakt": "switch.x_switch_l1",
        "switch.dobbelt_kontakt_2": "switch.x_switch_l2",
    }

    hk = device("homekit_controller", "W100", [("event", f"C3_65_{n}", f"sensor_button{n}", None) for n in (3, 1, 2)])
    mt = device(
        "matter", "W100m", [("event", f"775E-{n}-button", f"w100_button_{n}", f"Button ({n})") for n in (5, 3, 4)]
    )
    assert match(hk, mt) == {
        "event.sensor_button1": "event.w100_button_3",
        "event.sensor_button2": "event.w100_button_4",
        "event.sensor_button3": "event.w100_button_5",
    }


async def test_hue_zwave_shelly_shapes(hass: HomeAssistant) -> None:
    """Device and entity ids exactly as Hue, Z-Wave JS and Shelly write them (from their code in Home Assistant)."""
    from custom_components.replace_device.hardware import hardware_keys
    from custom_components.replace_device.remembered import remembered
    from custom_components.replace_device.triggers import best, label

    devices, registry = dr.async_get(hass), er.async_get(hass)
    entries = {d: MockConfigEntry(domain=d) for d in ("hue", "zha", "zwave_js", "shelly")}
    for entry in entries.values():
        entry.add_to_hass(hass)

    # Hue: the Zigbee address carries the endpoint ("-0b"). It is still the same bulb as in ZHA.
    hue = devices.async_get_or_create(
        config_entry_id=entries["hue"].entry_id,
        identifiers={("hue", "3f2c8f0e-uuid")},
        connections={(dr.CONNECTION_ZIGBEE, "00:17:88:01:0b:12:34:56-0b")},
    )
    zha = devices.async_get_or_create(
        config_entry_id=entries["zha"].entry_id,
        identifiers={("zha", "00:17:88:01:0b:12:34:56")},
        connections={(dr.CONNECTION_ZIGBEE, "00:17:88:01:0b:12:34:56")},
    )
    assert hardware_keys(hue) & hardware_keys(zha) == {"ieee:001788010b123456"}

    # Shelly: buttons are "button1", "button2" – button 1 never becomes button 2.
    shelly = [{"type": t, "subtype": f"button{b}"} for b in (1, 2) for t in ("single", "double", "long")]
    assert best({"type": "remote_button_short_press", "subtype": "button_2"}, shelly)["subtype"] == "button2"
    assert best({"type": "remote_button_long_press", "subtype": "button_1"}, shelly) == {
        "type": "long",
        "subtype": "button1",
    }

    # Z-Wave JS: scenes differ in property_key and value, so those are shown to the AI too.
    scene = {
        "platform": "device",
        "domain": "zwave_js",
        "device_id": "x",
        "type": "event.value_notification.central_scene",
        "property_key": "002",
        "value": "KeyPressed2x",
        "endpoint": 0,
    }
    assert (
        label(scene) == "event.value_notification.central_scene (property_key: 002, value: KeyPressed2x, endpoint: 0)"
    )

    # Remembered names: Z-Wave unique IDs start with "<home>.<node>-", Shelly's use the MAC without colons.
    zw = devices.async_get_or_create(
        config_entry_id=entries["zwave_js"].entry_id, identifiers={("zwave_js", "3245146787-5")}
    )
    sh = devices.async_get_or_create(
        config_entry_id=entries["shelly"].entry_id,
        identifiers={("shelly", "C45BBE6C7B2C")},
        connections={(dr.CONNECTION_NETWORK_MAC, "c4:5b:be:6c:7b:2c")},
    )
    for domain, entry, uid, object_id in (
        ("zwave_js", entries["zwave_js"], "3245146787.5-37-0-currentValue", "zw_switch"),
        ("zwave_js", entries["zwave_js"], "3245146787.55-37-0-currentValue", "other_node"),
        ("shelly", entries["shelly"], "C45BBE6C7B2C-switch:0", "sh_switch"),
    ):
        registry.async_get_or_create("switch", domain, uid, suggested_object_id=object_id, config_entry=entry)
        registry.async_remove(f"switch.{object_id}")
    assert [e.entity_id for e in remembered(hass, zw)] == ["switch.zw_switch"]
    assert [e.entity_id for e in remembered(hass, sh)] == ["switch.sh_switch"]


async def test_dry_run_changes_nothing(hass: HomeAssistant, hass_ws_client, tmp_path) -> None:
    """ "Test first" shows the blueprint, the zha_event and the device trigger it would change – and changes nothing."""
    from pathlib import Path
    from unittest.mock import patch

    hass.config.config_dir = str(tmp_path)
    blueprints = tmp_path / "blueprints" / "automation" / "damru"
    blueprints.mkdir(parents=True)
    (blueprints / "rodret.yaml").write_text((Path(__file__).parent / "fixtures" / "rodret.yaml").read_text())
    zha_entry = MockConfigEntry(domain="zha", title="ZHA")
    zha_entry.add_to_hass(hass)
    mqtt_entry = MockConfigEntry(domain="mqtt", title="Mosquitto broker")
    mqtt_entry.add_to_hass(hass)
    devices, entities = dr.async_get(hass), er.async_get(hass)
    ieee = "08:dd:eb:ff:fe:60:9e:76"
    zha = devices.async_get_or_create(
        config_entry_id=zha_entry.entry_id,
        identifiers={("zha", ieee)},
        connections={(dr.CONNECTION_ZIGBEE, ieee)},
        name="Kontakt stue",
    )
    z2m = devices.async_get_or_create(
        config_entry_id=mqtt_entry.entry_id,
        identifiers={("mqtt", "zigbee2mqtt_0x08ddebfffe609e76")},
        name="0x08ddebfffe609e76",
    )
    entities.async_get_or_create(
        "sensor",
        "zha",
        f"{ieee}-1-1",
        suggested_object_id="kontakt_stue_batteri",
        device_id=zha.id,
        config_entry=zha_entry,
        original_device_class="battery",
    )
    entities.async_get_or_create(
        "sensor",
        "mqtt",
        "0x08ddebfffe609e76_battery_zigbee2mqtt",
        suggested_object_id="x_battery",
        device_id=z2m.id,
        config_entry=mqtt_entry,
        original_device_class="battery",
    )
    automations = (
        "- id: '1'\n  alias: Sofa lys\n  use_blueprint:\n    path: damru/rodret.yaml\n    input:\n"
        f"      remote_device: {zha.id}\n      light: light.sofa_lys\n"
        "- id: '2'\n  alias: Tænd med kontakt\n  triggers:\n  - trigger: event\n    event_type: zha_event\n"
        f"    event_data:\n      device_ieee: '{ieee}'\n      command: 'on'\n  actions: []\n"
        "- id: '3'\n  alias: Sluk med kontakt\n  triggers:\n  - trigger: device\n    domain: zha\n"
        f"    device_id: {zha.id}\n    type: remote_button_short_press\n    subtype: turn_off\n  actions: []\n"
    )
    (tmp_path / "automations.yaml").write_text(automations)
    await _setup(hass)
    available = [
        {"platform": "device", "domain": "mqtt", "device_id": z2m.id, "type": "action", "subtype": s}
        for s in ("on", "off", "brightness_move_up", "brightness_move_down", "brightness_stop")
    ]
    client = await hass_ws_client(hass)
    with patch(
        "custom_components.replace_device.triggers.async_get_device_automations", return_value={z2m.id: available}
    ):
        await client.send_json_auto_id({"type": f"{DOMAIN}/plan", "old": zha.id, "new": z2m.id})
        plan = (await client.receive_json())["result"]
        await client.send_json_auto_id(
            {"type": f"{DOMAIN}/dry_run", "old": zha.id, "new": z2m.id, "mapping": plan["mapping"], "rename_z2m": True}
        )
        dry = (await client.receive_json())["result"]
        await client.send_json_auto_id({"type": f"{DOMAIN}/migrate_dry_run", "pairs": [{"old": zha.id, "new": z2m.id}]})
        many = (await client.receive_json())["result"]

    assert dry["entities"] == [
        {"from": "sensor.x_battery", "to": "sensor.kontakt_stue_batteri", "name": "", "used_in": []}
    ]
    assert dry["device"]["to"] == "Kontakt stue" and dry["remove_old"] is True and dry["z2m_name"] == "Kontakt stue"
    assert dry["users"] == ["automation: Sluk med kontakt", "automation: Sofa lys"]
    changes = {c["automation"]: c for c in dry["triggers"]["changes"]}
    assert changes["Tænd med kontakt"]["after"] == "action / on"
    assert changes["Sluk med kontakt"] == {
        "automation": "Sluk med kontakt",
        "before": "remote_button_short_press / turn_off",
        "after": "action / off",
    }
    assert changes["Sofa lys"]["before"] == "blueprint: zha" and dry["triggers"]["unresolved"] == []
    assert many["devices"][0]["name"] == "Kontakt stue" and len(many["devices"][0]["triggers"]["changes"]) == 3
    # Nothing was changed.
    assert (tmp_path / "automations.yaml").read_text() == automations
    assert devices.async_get(zha.id) is not None and devices.async_get(z2m.id).name_by_user is None
    assert entities.async_get("sensor.x_battery") and entities.async_get("sensor.kontakt_stue_batteri")


async def test_buttons_in_scripts_and_packages(hass: HomeAssistant, tmp_path) -> None:
    """Button triggers in scripts.yaml are translated and changed back; in packages/ they are listed to do by hand."""
    from unittest.mock import patch

    from homeassistant.util.yaml import load_yaml

    from custom_components.replace_device.replace import async_plan

    hass.config.config_dir = str(tmp_path)
    zha_entry = MockConfigEntry(domain="zha", title="ZHA")
    zha_entry.add_to_hass(hass)
    mqtt_entry = MockConfigEntry(domain="mqtt", title="Mosquitto broker")
    mqtt_entry.add_to_hass(hass)
    devices = dr.async_get(hass)
    ieee = "08:dd:eb:ff:fe:60:9e:76"
    zha = devices.async_get_or_create(
        config_entry_id=zha_entry.entry_id,
        identifiers={("zha", ieee)},
        connections={(dr.CONNECTION_ZIGBEE, ieee)},
        name="Kontakt stue",
    )
    z2m = devices.async_get_or_create(
        config_entry_id=mqtt_entry.entry_id,
        identifiers={("mqtt", "zigbee2mqtt_0x08ddebfffe609e76")},
        name="0x08ddebfffe609e76",
    )
    zha_wait = (
        "  - wait_for_trigger:\n    - trigger: event\n      event_type: zha_event\n"
        f"      event_data:\n        device_ieee: '{ieee}'\n        command: 'on'\n"
    )
    (tmp_path / "automations.yaml").write_text("[]\n")
    scripts = f"vent_paa_knap:\n  alias: Vent på knap\n  sequence:\n{zha_wait}"
    (tmp_path / "scripts.yaml").write_text(scripts)
    (tmp_path / "packages").mkdir()
    package = (
        "automation:\n- id: pk1\n  alias: Pakke sluk\n  triggers:\n  - trigger: event\n    event_type: zha_event\n"
        f"    event_data:\n      device_ieee: '{ieee}'\n      command: 'off'\n  actions: []\n"
    )
    (tmp_path / "packages" / "knap.yaml").write_text(package)
    entry = await _setup(hass)
    available = [
        {"platform": "device", "domain": "mqtt", "device_id": z2m.id, "type": "action", "subtype": s}
        for s in ("on", "off")
    ]
    with patch(
        "custom_components.replace_device.triggers.async_get_device_automations", return_value={z2m.id: available}
    ):
        dry = await entry.runtime_data.async_dry_run(async_plan(hass, zha.id, z2m.id), True, False)
        assert (tmp_path / "scripts.yaml").read_text() == scripts
        assert [c.get("by_hand") for c in dry["triggers"]["changes"]] == [None, "packages/knap.yaml"]
        result = await entry.runtime_data.async_replace(async_plan(hass, zha.id, z2m.id), True)
    await hass.async_block_till_done()
    wait = load_yaml(str(tmp_path / "scripts.yaml"))["vent_paa_knap"]["sequence"][0]["wait_for_trigger"][0]
    assert wait["trigger"] == "device" and wait["subtype"] == "on"
    assert (tmp_path / "packages" / "knap.yaml").read_text() == package
    assert result["triggers"]["unresolved"] == ["Pakke sluk (packages/knap.yaml): off → action / off"]
    assert "script" in result["changed"]

    assert await entry.runtime_data.async_undo(result["id"])
    await hass.async_block_till_done()
    assert load_yaml(str(tmp_path / "scripts.yaml"))["vent_paa_knap"]["sequence"][0]["wait_for_trigger"][0][
        "event_type"
    ] == "zha_event"


async def test_own_entities_get_ids_after_the_device(hass: HomeAssistant, tmp_path) -> None:
    """Entities only the new device has get ids after the device's name; what uses them follows, and undo turns back."""
    from homeassistant.util.yaml import load_yaml

    from custom_components.replace_device.replace import async_plan

    hass.config.config_dir = str(tmp_path)
    zha_entry = MockConfigEntry(domain="zha", title="ZHA")
    zha_entry.add_to_hass(hass)
    mqtt_entry = MockConfigEntry(domain="mqtt", title="Mosquitto broker")
    mqtt_entry.add_to_hass(hass)
    devices, entities = dr.async_get(hass), er.async_get(hass)
    zha = devices.async_get_or_create(config_entry_id=zha_entry.entry_id, identifiers={("zha", "a")}, name="Røgalarm Gang")
    z2m = devices.async_get_or_create(
        config_entry_id=mqtt_entry.entry_id, identifiers={("mqtt", "zigbee2mqtt_0x54ef441001314fb2")}, name="0x54ef"
    )
    entities.async_get_or_create(
        "binary_sensor", "zha", "a-1", suggested_object_id="rogalarm_gang", device_id=zha.id, config_entry=zha_entry,
        original_device_class="smoke",
    )
    entities.async_get_or_create(
        "binary_sensor", "mqtt", "0x54_smoke", suggested_object_id="0x54ef441001314fb2_smoke", device_id=z2m.id,
        config_entry=mqtt_entry, original_device_class="smoke", has_entity_name=True, original_name="Smoke",
    )
    for key, name in (("voltage", "Voltage"), ("voltage2", "Voltage")):
        entities.async_get_or_create(
            "sensor", "mqtt", f"0x54_{key}", suggested_object_id=f"0x54ef441001314fb2_{key}", device_id=z2m.id,
            config_entry=mqtt_entry, has_entity_name=True, original_name=name,
        )
    automations = (
        "- id: '1'\n  alias: Lav spænding\n  triggers:\n  - trigger: numeric_state\n"
        "    entity_id: sensor.0x54ef441001314fb2_voltage\n    below: 2.5\n"
        "  actions:\n  - action: notify.x\n    data:\n      message: \"{{ states('sensor.0x54ef441001314fb2_voltage2') }}\"\n"
    )
    (tmp_path / "automations.yaml").write_text(automations)
    entry = await _setup(hass)
    replacer = entry.runtime_data
    plan = async_plan(hass, zha.id, z2m.id)

    dry = await replacer.async_dry_run(plan, True)
    assert {e["entity_id"]: e["to"] for e in dry["own_info"]} == {
        "sensor.0x54ef441001314fb2_voltage": "sensor.rogalarm_gang_voltage",
        "sensor.0x54ef441001314fb2_voltage2": "sensor.rogalarm_gang_voltage_2",
    }

    result = await replacer.async_replace(async_plan(hass, zha.id, z2m.id), True)
    await hass.async_block_till_done()
    assert entities.async_get("binary_sensor.rogalarm_gang").device_id == z2m.id
    assert entities.async_get("sensor.rogalarm_gang_voltage").unique_id == "0x54_voltage"
    assert entities.async_get("sensor.rogalarm_gang_voltage_2").unique_id == "0x54_voltage2"
    text = (tmp_path / "automations.yaml").read_text()
    assert "sensor.rogalarm_gang_voltage\n" in text and "states('sensor.rogalarm_gang_voltage_2')" in text
    assert "0x54ef" not in text
    assert replacer.tidy_plan(result["id"]) == []

    # A Zigbee2MQTT update adds an entity later: "Tidy up" in Edit gives it a name too.
    entities.async_get_or_create(
        "sensor", "mqtt", "0x54_linkquality", suggested_object_id="0x54ef441001314fb2_linkquality", device_id=z2m.id,
        config_entry=mqtt_entry, has_entity_name=True, original_name="Linkquality",
    )
    assert [c["to"] for c in replacer.tidy_plan(result["id"])] == ["sensor.rogalarm_gang_linkquality"]
    assert len(await replacer.async_tidy_record(result["id"])) == 1
    assert entities.async_get("sensor.rogalarm_gang_linkquality")

    assert await replacer.async_undo(result["id"])
    await hass.async_block_till_done()
    assert entities.async_get("sensor.0x54ef441001314fb2_voltage")
    assert entities.async_get("sensor.0x54ef441001314fb2_linkquality")
    assert load_yaml(str(tmp_path / "automations.yaml"))[0]["triggers"][0]["entity_id"] == (
        "sensor.0x54ef441001314fb2_voltage"
    )


async def test_rename_device_everywhere(hass: HomeAssistant, tmp_path) -> None:
    """Renaming a device renames its entity ids and every place that uses them; undo turns it all back."""
    hass.config.config_dir = str(tmp_path)
    mqtt_entry = MockConfigEntry(domain="mqtt", title="Mosquitto broker")
    mqtt_entry.add_to_hass(hass)
    group = MockConfigEntry(
        domain="group", title="Alle temperaturer",
        options={"group_type": "sensor", "entities": ["sensor.kokken_sensor_temperature", "sensor.other"]},
    )
    group.add_to_hass(hass)
    devices, entities = dr.async_get(hass), er.async_get(hass)
    device = devices.async_get_or_create(
        config_entry_id=mqtt_entry.entry_id, identifiers={("mqtt", "zigbee2mqtt_0x00158d0001a2b3")}, name="0x00158d"
    )
    devices.async_update_device(device.id, name_by_user="Køkken sensor")
    entities.async_get_or_create(
        "sensor", "mqtt", "t", suggested_object_id="kokken_sensor_temperature", device_id=device.id,
        config_entry=mqtt_entry, has_entity_name=True, original_name="Temperature",
    )
    entities.async_get_or_create(
        "sensor", "mqtt", "l", suggested_object_id="0x00158d0001a2b3_linkquality", device_id=device.id,
        config_entry=mqtt_entry, has_entity_name=True, original_name="Linkquality",
    )
    # Another device's entity with a longer id that starts the same must not change.
    entities.async_get_or_create("sensor", "mqtt", "x", suggested_object_id="kokken_sensor_temperature_avg")
    (tmp_path / "configuration.yaml").write_text("template: !include templates.yaml\nautomation: !include automations.yaml\n")
    (tmp_path / "templates.yaml").write_text(
        "- sensor:\n  - name: Varm\n    state: \"{{ states('sensor.kokken_sensor_temperature') | float > 25 }}\"\n"
        "  - name: Snit\n    state: \"{{ states('sensor.kokken_sensor_temperature_avg') }}\"\n"
    )
    (tmp_path / "automations.yaml").write_text(
        "- id: '1'\n  alias: Varmt i køkkenet\n  triggers:\n  - trigger: numeric_state\n"
        "    entity_id: sensor.kokken_sensor_temperature\n    above: 25\n  actions: []\n"
    )
    (tmp_path / "scripts.yaml").write_text(
        "signal:\n  sequence:\n  - action: notify.x\n    data:\n      message: \"{{ states('sensor.0x00158d0001a2b3_linkquality') }}\"\n"
    )
    (tmp_path / "packages").mkdir()
    (tmp_path / "packages" / "p.yaml").write_text("homeassistant:\n  customize:\n    sensor.kokken_sensor_temperature:\n      icon: mdi:fire\n")
    (tmp_path / "esphome").mkdir()
    (tmp_path / "esphome" / "display.yaml").write_text(
        "sensor:\n  - platform: homeassistant\n    entity_id: sensor.kokken_sensor_temperature\n"
    )
    (tmp_path / "secrets.yaml").write_text("x: sensor.kokken_sensor_temperature\n")
    entry = await _setup(hass)
    replacer = entry.runtime_data

    dry = await replacer.async_rename_dry_run(device.id, "Spisekammer")
    assert {c["from"]: c["to"] for c in dry["entities"]} == {
        "sensor.kokken_sensor_temperature": "sensor.spisekammer_temperature",
        "sensor.0x00158d0001a2b3_linkquality": "sensor.spisekammer_linkquality",
    }
    assert dry["yaml"] == ["templates.yaml"] and dry["esphome"] == ["esphome/display.yaml"]
    assert dry["integrations"] == ["Alle temperaturer"]
    assert entities.async_get("sensor.kokken_sensor_temperature")  # nothing changed yet

    result = await replacer.async_rename(device.id, "Spisekammer")
    await hass.async_block_till_done()
    assert devices.async_get(device.id).name_by_user == "Spisekammer"
    assert entities.async_get("sensor.spisekammer_temperature").unique_id == "t"
    assert entities.async_get("sensor.spisekammer_linkquality").unique_id == "l"
    templates = (tmp_path / "templates.yaml").read_text()
    assert "states('sensor.spisekammer_temperature')" in templates and "sensor.kokken_sensor_temperature_avg" in templates
    assert "sensor.spisekammer_temperature" in (tmp_path / "automations.yaml").read_text()
    assert "sensor.spisekammer_linkquality" in (tmp_path / "scripts.yaml").read_text()
    assert "sensor.spisekammer_temperature:" in (tmp_path / "packages" / "p.yaml").read_text()
    assert "sensor.spisekammer_temperature" in (tmp_path / "esphome" / "display.yaml").read_text()
    assert "kokken_sensor" in (tmp_path / "secrets.yaml").read_text()
    assert group.options["entities"] == ["sensor.spisekammer_temperature", "sensor.other"]
    assert entities.async_get("sensor.kokken_sensor_temperature_avg")

    assert await replacer.async_undo(result["id"])
    await hass.async_block_till_done()
    assert devices.async_get(device.id).name_by_user == "Køkken sensor"
    assert entities.async_get("sensor.kokken_sensor_temperature").unique_id == "t"
    assert entities.async_get("sensor.0x00158d0001a2b3_linkquality").unique_id == "l"
    assert "sensor.kokken_sensor_temperature\n" in (tmp_path / "automations.yaml").read_text()
    assert group.options["entities"] == ["sensor.kokken_sensor_temperature", "sensor.other"]


async def test_old_device_that_stays_says_so(hass: HomeAssistant) -> None:
    """A kept old device gets a name that says it can be deleted; undo gives its name back."""
    from custom_components.replace_device.replace import async_plan

    old = _device(hass, "zha", "old", "Kitchen", OLD_SENSORS)
    new = _device(hass, "mqtt", "new", "0x00158d0001", NEW_SENSORS)
    entry = await _setup(hass)
    replacer = entry.runtime_data
    dry = await replacer.async_dry_run(async_plan(hass, old.id, new.id), False)
    assert dry["old_name"] == "Kitchen (old – can be deleted)"
    result = await replacer.async_replace(async_plan(hass, old.id, new.id), False)
    await hass.async_block_till_done()
    devices = dr.async_get(hass)
    assert devices.async_get(old.id).name_by_user == "Kitchen (old – can be deleted)"
    assert devices.async_get(new.id).name_by_user == "Kitchen"
    assert await replacer.async_undo(result["id"])
    assert devices.async_get(old.id).name_by_user is None
