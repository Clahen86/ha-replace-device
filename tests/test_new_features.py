"""The device's own settings, Zigbee2MQTT bindings and calibration, and fixing the user's own YAML files."""

import json
import os
from unittest.mock import AsyncMock, patch

from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry, async_mock_service

from custom_components.replace_device import own_yaml, z2m
from custom_components.replace_device.const import DOMAIN
from custom_components.replace_device.replace import async_plan


async def _setup(hass):
    entry = MockConfigEntry(domain=DOMAIN, data={})
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry.runtime_data


def _device(hass, platform, ident, name, model, entities, identifier=None):
    entry = MockConfigEntry(domain=platform, title=platform)
    entry.add_to_hass(hass)
    device = dr.async_get(hass).async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(platform, identifier or ident)},
        name=name,
        manufacturer="IKEA",
        model=model,
    )
    reg = er.async_get(hass)
    for key, domain, category, caps in entities:
        reg.async_get_or_create(
            domain,
            platform,
            f"{ident}-{key}",
            suggested_object_id=f"{name}_{key}".lower(),
            device_id=device.id,
            config_entry=entry,
            original_name=key.replace("_", " ").capitalize(),
            translation_key=key,
            entity_category=category,
            capabilities=caps,
        )
    return device


CONFIG = EntityCategory.CONFIG
SETTINGS = [
    ("occupancy", "binary_sensor", None, None),
    ("power_on_behavior", "select", CONFIG, {"options": ["off", "on", "previous"]}),
    ("sensitivity", "number", CONFIG, {"min": 0, "max": 10, "step": 1}),
    ("led", "switch", CONFIG, None),
    ("timeout", "number", CONFIG, {"min": 0, "max": 100, "step": 1}),
    ("temperature_calibration", "number", CONFIG, {"min": -5, "max": 5, "step": 0.1}),
    ("factory_reset", "switch", CONFIG, None),
]


async def test_copy_settings(hass: HomeAssistant, tmp_path) -> None:
    """Same model: the old configuration values go to the new device; dangerous ones and misfits never do."""
    hass.config.config_dir = str(tmp_path)
    old = _device(hass, "zha", "old", "Hall", "E2134", SETTINGS)
    new = _device(hass, "zha", "new", "0xabc", "E2134", SETTINGS)
    for key, value in (
        ("power_on_behavior", "unavailable"),  # dead: the recorder has the last value
        ("sensitivity", "7"),
        ("led", "off"),
        ("timeout", "250"),  # outside the new one's range
        ("temperature_calibration", "1.5"),
        ("factory_reset", "on"),
    ):
        domain = next(d for k, d, _, _ in SETTINGS if k == key)
        hass.states.async_set(f"{domain}.hall_{key}", value)
    hass.states.async_set("select.0xabc_power_on_behavior", "on", {"options": ["off", "on", "previous"]})
    hass.states.async_set("switch.0xabc_led", "on")
    calls = {
        name: async_mock_service(hass, *name.split("."))
        for name in ("select.select_option", "number.set_value", "switch.turn_on", "switch.turn_off")
    }
    replacer = await _setup(hass)
    history = AsyncMock(return_value="previous")
    with patch("custom_components.replace_device.config_values._last_valid", history):
        dry = await replacer.async_dry_run(async_plan(hass, old.id, new.id), True)
        assert {s["entity_id"]: s["value"] for s in dry["settings"]} == {
            "select.hall_power_on_behavior": "previous",
            "number.hall_sensitivity": 7.0,
            "switch.hall_led": "off",
        }
        assert next(s for s in dry["settings"] if s["domain"] == "select")["source"] == "history"
        result = await replacer.async_replace(async_plan(hass, old.id, new.id), True)
    await hass.async_block_till_done()
    assert [c.data for c in calls["select.select_option"]] == [
        {"entity_id": "select.hall_power_on_behavior", "option": "previous"}
    ]
    assert [c.data for c in calls["number.set_value"]] == [{"entity_id": "number.hall_sensitivity", "value": 7.0}]
    assert [c.data["entity_id"] for c in calls["switch.turn_off"]] == ["switch.hall_led"]
    assert not calls["switch.turn_on"]  # factory reset: never
    assert len(result["settings"]["copied"]) == 3 and result["settings"]["failed"] == []
    # Undo doesn't change the device back, and doesn't fail on it. (States set by hand stand in for the entities.)
    for entity_id in ("select.0xabc_power_on_behavior", "switch.0xabc_led"):
        hass.states.async_remove(entity_id)
    assert await replacer.async_undo(result["id"])


async def test_settings_only_for_the_same_kind(hass: HomeAssistant, tmp_path) -> None:
    hass.config.config_dir = str(tmp_path)
    old = _device(hass, "zha", "old", "Hall", "E2134", SETTINGS)
    new = _device(hass, "mqtt", "new", "0xabc", "OTHER", SETTINGS)
    hass.states.async_set("number.hall_sensitivity", "7")
    replacer = await _setup(hass)
    dry = await replacer.async_dry_run(async_plan(hass, old.id, new.id), True)
    assert dry["settings"] == []
    # A failing service is logged and skipped, never fatal.
    from custom_components.replace_device import config_values

    done, failed = await config_values.async_apply(
        hass, [{"entity_id": "number.x", "domain": "number", "name": "x", "value": 1.0, "source": "state"}]
    )
    assert done == [] and failed == ["number.x"]


OLD, NEW, BULB, OTHER, COORD = "0x000000000000aaaa", "0x000000000000bbbb", "0x000000000000cccc", "0x000000000000dddd", "0x00000000000000c0"
DEVICES = [
    {"ieee_address": COORD, "type": "Coordinator", "friendly_name": "Coordinator", "endpoints": {}},
    {
        "ieee_address": OLD,
        "type": "EndDevice",
        "friendly_name": "Remote",
        "endpoints": {
            "1": {
                "bindings": [
                    {"cluster": "genOnOff", "target": {"type": "endpoint", "endpoint": 1, "ieee_address": BULB}},
                    {"cluster": "genLevelCtrl", "target": {"type": "group", "id": 3}},
                    {"cluster": "genPowerCfg", "target": {"type": "endpoint", "endpoint": 1, "ieee_address": COORD}},
                    {"cluster": "genScenes", "target": {"type": "endpoint", "endpoint": 1, "ieee_address": BULB}},
                ],
                "clusters": {"input": ["genBasic"], "output": ["genOnOff", "genLevelCtrl", "genScenes"]},
            }
        },
    },
    {
        "ieee_address": NEW,
        "type": "EndDevice",
        "friendly_name": NEW,
        "endpoints": {"1": {"bindings": [], "clusters": {"input": ["genBasic", "genOnOff"], "output": ["genOnOff", "genLevelCtrl"]}}},
    },
    {"ieee_address": BULB, "type": "Router", "friendly_name": "Bulb", "endpoints": {}},
    {
        "ieee_address": OTHER,
        "type": "EndDevice",
        "friendly_name": "Switch",
        "endpoints": {
            "2": {"bindings": [{"cluster": "genOnOff", "target": {"type": "endpoint", "endpoint": 1, "ieee_address": OLD}}]}
        },
    },
]
INFO = {
    "config": {
        "devices": {
            OLD: {"friendly_name": "Remote", "temperature_calibration": 0.5, "humidity_calibration": -2, "retain": False},
            NEW: {"friendly_name": NEW, "humidity_calibration": 1},
        }
    }
}


def _z2m_device(hass, entry, ieee, name):
    device = dr.async_get(hass).async_get_or_create(
        config_entry_id=entry.entry_id, identifiers={("mqtt", f"zigbee2mqtt_{ieee}")}, name=name, model="E2001"
    )
    er.async_get(hass).async_get_or_create(
        "sensor", "mqtt", f"{ieee}-battery", suggested_object_id=f"{name}_battery".lower(), device_id=device.id,
        config_entry=entry, original_device_class="battery",
    )
    return device


async def test_z2m_bindings_and_calibration(hass: HomeAssistant, tmp_path) -> None:
    hass.config.config_dir = str(tmp_path)
    published = async_mock_service(hass, "mqtt", "publish")
    mqtt_entry = MockConfigEntry(domain="mqtt", title="Mosquitto broker")
    mqtt_entry.add_to_hass(hass)
    old = _z2m_device(hass, mqtt_entry, OLD, "Remote")
    new = _z2m_device(hass, mqtt_entry, NEW, NEW)
    replacer = await _setup(hass)

    async def retained(_hass, topic):
        return DEVICES if topic == "zigbee2mqtt/bridge/devices" else INFO

    with patch("custom_components.replace_device.z2m.async_retained", side_effect=retained):
        dry = await replacer.async_dry_run(async_plan(hass, old.id, new.id), True)
        assert dry["z2m"]["missing"] is None
        assert dry["z2m"]["options"] == {"temperature_calibration": 0.5, "humidity_calibration": -2}
        assert {(b["from"], b["to"], tuple(b["clusters"])) for b in dry["z2m"]["binds"]} == {
            (NEW, "Bulb", ("genOnOff",)),
            (NEW, "group 3", ("genLevelCtrl",)),
            ("Switch", NEW, ("genOnOff",)),
        }
        assert dry["z2m"]["skipped"] == 1  # genScenes: the new remote doesn't have it
        result = await replacer.async_replace(async_plan(hass, old.id, new.id), True)
    await hass.async_block_till_done()
    sent = [(c.data["topic"], json.loads(c.data["payload"])) for c in published]
    binds = [p for t, p in sent if t == "zigbee2mqtt/bridge/request/device/bind"]
    assert {"from": NEW, "from_endpoint": 1, "to": BULB, "to_endpoint": 1, "clusters": ["genOnOff"]} in binds
    assert {"from": NEW, "from_endpoint": 1, "to": 3, "clusters": ["genLevelCtrl"]} in binds
    assert {"from": OTHER, "from_endpoint": 2, "to": NEW, "to_endpoint": 1, "clusters": ["genOnOff"]} in binds
    assert len(binds) == 3
    assert ("zigbee2mqtt/bridge/request/device/options",
            {"id": NEW, "options": {"temperature_calibration": 0.5, "humidity_calibration": -2}}) in sent
    assert len(result["z2m"]["binds"]) == 3

    # Undo: unbound again, and the new device's own calibration back (null removes it in Zigbee2MQTT).
    published.clear()
    assert await replacer.async_undo(result["id"])
    sent = [(c.data["topic"], json.loads(c.data["payload"])) for c in published]
    assert len([t for t, _ in sent if t == "zigbee2mqtt/bridge/request/device/unbind"]) == 3
    assert ("zigbee2mqtt/bridge/request/device/options",
            {"id": NEW, "options": {"temperature_calibration": None, "humidity_calibration": 1}}) in sent


def test_z2m_plan_without_the_old_device() -> None:
    assert z2m.plan(OLD, NEW, None, None)["missing"] == "no_data"
    gone = [d for d in DEVICES if d["ieee_address"] != OLD]
    assert z2m.plan(OLD, NEW, gone, {"config": {"devices": {}}})["missing"] == "old_gone"
    # Another Zigbee2MQTT instance is another network: calibration only, nothing bound.
    other = z2m.plan(OLD, NEW, DEVICES, INFO, {"config": {"devices": {}}}, same_network=False)
    assert other["binds"] == [] and other["options"] == {"temperature_calibration": 0.5, "humidity_calibration": -2}


async def test_zha_to_z2m_binds_nothing(hass: HomeAssistant, tmp_path) -> None:
    hass.config.config_dir = str(tmp_path)
    old = _device(hass, "zha", "old", "Hall", "E2134", SETTINGS[:1])
    new = _device(hass, "mqtt", "new", "0xabc", "E2134", SETTINGS[:1], identifier=f"zigbee2mqtt_{NEW}")
    replacer = await _setup(hass)
    assert (await replacer.async_dry_run(async_plan(hass, old.id, new.id), True))["z2m"] is None


def _write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as file:
        file.write(text)


def _plug(hass, platform, ident, name, domain):
    entry = MockConfigEntry(domain=platform, title=platform)
    entry.add_to_hass(hass)
    device = dr.async_get(hass).async_get_or_create(
        config_entry_id=entry.entry_id, identifiers={(platform, ident)}, name=name, manufacturer="X", model="Plug"
    )
    er.async_get(hass).async_get_or_create(
        domain, platform, f"{ident}-plug", suggested_object_id=name.lower(), device_id=device.id, config_entry=entry,
        original_name="Plug",
    )
    return device


async def test_fix_own_yaml_files(hass: HomeAssistant, tmp_path) -> None:
    """A switch that is now a light: whole ids are fixed in the user's own YAML (after their OK), backed up first,
    never in secrets, .storage, backups or files that would load differently - and undo puts it back."""
    hass.config.config_dir = str(tmp_path)
    old = _plug(hass, "zha", "old", "Kitchen", "switch")
    new = _plug(hass, "mqtt", "new", "0xabc", "light")
    c = str(tmp_path)
    configuration = (
        "homeassistant:\n  packages: !include_dir_named packages\n"
        "template: !include templates.yaml\nsensor: !include sensor.yaml\n"
        "group:\n  kitchen:\n    entities:\n      - switch.kitchen\n"
    )
    _write(f"{c}/configuration.yaml", configuration)
    templates = (
        "- sensor:\n    - name: Plug on\r\n      state: \"{{ is_state('switch.kitchen', 'on') }}\"\r\n"
        "    - name: Others\r\n      state: \"{{ states('switch.kitchen_2') ~ states('xswitch.kitchen') }}\"\r\n"
    )
    _write(f"{c}/templates.yaml", templates)
    _write(f"{c}/sensor.yaml", "- platform: template\n  sensors: {}\n")
    package = f"automation:\n  - alias: Plug\n    triggers:\n      - trigger: device\n        device_id: {old.id}\n"
    _write(f"{c}/packages/plug.yaml", package)
    collide = "homeassistant:\n  customize:\n    switch.kitchen:\n      icon: mdi:a\n    light.kitchen:\n      icon: mdi:b\n"
    _write(f"{c}/packages/customize.yaml", collide)
    _write(f"{c}/esphome/display.yaml", "sensor:\n  - platform: homeassistant\n    entity_id: switch.kitchen\n")
    _write(f"{c}/appdaemon/apps/apps.yaml", "plug:\n  module: plug\n  entity: switch.kitchen\n")
    untouched = {
        "secrets.yaml": "plug: switch.kitchen\n",
        "packages/plug.yaml.bak-old": package,
        "templates.yaml.before-x": templates,
        ".storage/core.yaml": "switch.kitchen\n",
        "custom_components/x/services.yaml": "switch.kitchen\n",
        "appdaemon/apps/plug.py": "self.turn_on('switch.kitchen')\n",
    }
    for rel, text in untouched.items():
        _write(f"{c}/{rel}", text)
    plan = lambda: async_plan(hass, old.id, new.id, {"switch.kitchen": "light.0xabc"})
    replacer = await _setup(hass)

    dry = await replacer.async_dry_run(plan(), True)
    files = {f["file"]: f for f in dry["own_yaml"]["files"]}
    assert set(files) == {
        "configuration.yaml", "templates.yaml", "packages/plug.yaml", "esphome/display.yaml", "appdaemon/apps/apps.yaml"
    }
    assert files["esphome/display.yaml"]["kind"] == "esphome"
    assert [f["file"] for f in dry["own_yaml"]["broken"]] == ["packages/customize.yaml"]
    assert (tmp_path / "templates.yaml").read_bytes() == templates.encode()  # a test run changes nothing

    # Without the OK, nothing is written.
    result = await replacer.async_replace(plan(), True)
    assert result["own_yaml"] is None and (tmp_path / "templates.yaml").read_bytes() == templates.encode()
    assert await replacer.async_undo(result["id"])
    assert await replacer.async_redo(result["id"])
    assert await replacer.async_undo(result["id"])

    old, new = _plug(hass, "zha", "old2", "Kitchen", "switch"), dr.async_get(hass).async_get(new.id)
    _write(f"{c}/packages/plug.yaml", package.replace(package.split("device_id: ")[1].strip(), old.id))
    plan = lambda: async_plan(hass, old.id, new.id, {"switch.kitchen": "light.0xabc"})
    reloads = async_mock_service(hass, "template", "reload")
    result = await replacer.async_replace(plan(), True, picked={"yaml": True})
    await hass.async_block_till_done()
    own = result["own_yaml"]
    assert set(own["files"]) == set(files) and own["esphome"] == ["esphome/display.yaml"]
    assert own["failed"] == ["packages/customize.yaml"] and own["restart"]  # configuration.yaml itself changed
    assert len(reloads) == 1
    text = (tmp_path / "templates.yaml").read_bytes().decode()
    assert "is_state('light.kitchen', 'on')" in text and "\r\n" in text
    assert "states('switch.kitchen_2') ~ states('xswitch.kitchen')" in text
    assert new.id in (tmp_path / "packages/plug.yaml").read_text() and old.id not in (tmp_path / "packages/plug.yaml").read_text()
    assert "light.kitchen" in (tmp_path / "configuration.yaml").read_text()
    assert (tmp_path / "packages/customize.yaml").read_text() == collide
    for rel, before in untouched.items():
        assert (tmp_path / rel).read_bytes() == before.encode()
    backups = [n for n in os.listdir(c) if n.startswith("templates.yaml.bak-replace-device-")]
    assert len(backups) == 1 and (tmp_path / backups[0]).read_bytes() == templates.encode()
    record = next(r for r in replacer.history if r["id"] == result["id"])
    assert {f["file"] for f in record["own_yaml"]["files"]} == set(files)

    # Undo: untouched files get their backup back; an edited file only the lines that were changed.
    with open(f"{c}/appdaemon/apps/apps.yaml", "a", encoding="utf-8") as file:
        file.write("other:\n  entities: [light.kitchen]\n")
    assert await replacer.async_undo(result["id"])
    assert (tmp_path / "templates.yaml").read_bytes() == templates.encode()
    assert old.id in (tmp_path / "packages/plug.yaml").read_text()
    apps = (tmp_path / "appdaemon/apps/apps.yaml").read_text()
    assert "  entity: switch.kitchen\n" in apps and "other:\n  entities: [light.kitchen]\n" in apps


def test_never_touched_and_loader(tmp_path) -> None:
    c = str(tmp_path)
    handled = {os.path.join(c, "automations.yaml")}
    for rel in ("secrets.yaml", "a.yaml.bak", "a.yaml.bak-x", "a.before-x.yaml", ".storage/x.yaml",
                "custom_components/x/y.yaml", "automations.yaml", "x.py", "node-red/flows.yaml"):
        assert own_yaml.never(os.path.join(c, rel), c, handled), rel
    assert not own_yaml.never(os.path.join(c, "packages/x.yaml"), c, handled)
    assert not own_yaml.never(os.path.join(c, "esphome/x.yaml"), c, handled)
    # Home Assistant's own loader is left as it was.
    from annotatedyaml.loader import PythonSafeLoader

    assert PythonSafeLoader.yaml_constructors["!include"] is not own_yaml._Loader.yaml_constructors["!include"]
    assert own_yaml.parse("a: !secret x\nb: !lambda return 1;\n") == {
        "a": {"!tag": "!secret", "value": "x"}, "b": {"!tag": "!lambda", "value": "return 1;"}
    }


async def test_panel_sends_fix_my_yaml(hass: HomeAssistant, hass_ws_client, tmp_path) -> None:
    """The panel's dry run lists the files, and "replace" takes the tick."""
    hass.config.config_dir = str(tmp_path)
    old = _plug(hass, "zha", "old", "Kitchen", "switch")
    new = _plug(hass, "mqtt", "new", "0xabc", "switch")
    _write(f"{tmp_path}/packages/plug.yaml", f"automation:\n  - triggers:\n      - device_id: {old.id}\n")
    await _setup(hass)
    client = await hass_ws_client(hass)
    mapping = {"switch.kitchen": "switch.0xabc"}
    await client.send_json_auto_id(
        {"type": "replace_device/dry_run", "old": old.id, "new": new.id, "mapping": mapping}
    )
    dry = (await client.receive_json())["result"]
    assert [f["file"] for f in dry["own_yaml"]["files"]] == ["packages/plug.yaml"]
    await client.send_json_auto_id(
        {"type": "replace_device/replace", "old": old.id, "new": new.id, "mapping": mapping, "fix": {"yaml": True}}
    )
    result = (await client.receive_json())["result"]
    assert result["own_yaml"]["files"] == ["packages/plug.yaml"]
    assert new.id in (tmp_path / "packages/plug.yaml").read_text()
