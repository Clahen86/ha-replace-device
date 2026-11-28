"""The setup for the developer: integrations replaced by which, what moved - and no names or entity IDs."""

from types import SimpleNamespace
from unittest.mock import patch

from homeassistant.core import HomeAssistant

from custom_components.replace_device.setup import setup_info
from custom_components.replace_device.support import Support


def test_setup_info():
    hist = [
        {"old_device": {"name": "Kitchen lamp", "model": "TS011F"}, "entities": [{"entity_id": "light.kitchen"}] * 3,
         "failed": [], "files": ["automations.yaml"], "batch": "b1", "undone": False, "platforms": ["zha", "mqtt"],
         "makers": ["Tuya TS011F", "Tuya TS011F"]},
        {"old_device": {"name": "Hall", "model": "X"}, "entities": [{}], "failed": ["light.hall"], "files": [], "batch": "b1",
         "undone": True, "platforms": ["zha", "mqtt"]},
        {"kind": "rename", "old_device": {"name": "Lights", "model": "Group"}},
        {"kind": "follow", "old_device": {"name": "sensor.a"}},
    ]
    su = setup_info(SimpleNamespace(history=hist, ai_entity="ai_task.x", hidden=[], ignored_refs=[]))
    assert su["counts"] == {"replacements": 2, "renames": 0, "group_renames": 1, "follows": 1, "bulk": 1, "undone": 1, "swaps": 0, "copies": 0}
    d = su["devices"][0]
    assert d["platform"] == "zha→mqtt" and d["ok"] is False and d["extra"]["entities"] == 4 and d["model"] == "Tuya TS011F → Tuya TS011F"
    assert "Kitchen" not in str(su) and "light." not in str(su)
    assert su["features"]["ai"] is True


async def test_sent_with_the_daily_question(hass: HomeAssistant) -> None:
    s = Support(hass, "replace_device", "replace-device", "Replace device", setup=lambda: {"counts": {"replacements": 1}})
    await s.async_setup()
    sent = {}

    async def post(path, data, timeout=30):
        sent.update(data)
        return {"reports": [], "notes": []}
    with patch.object(s, "_post", post):
        await s.fetch_answers()
    assert sent["setup"] == {"counts": {"replacements": 1}, "full": False}
    s.d["share"] = False
    sent.clear()
    with patch.object(s, "_post", post):
        await s.fetch_answers()
    assert "setup" not in sent
    s.unload()
