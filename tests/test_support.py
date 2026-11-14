"""Help: the panel's websocket calls go through (status, hide, share, send)."""

from unittest.mock import patch

from homeassistant.core import HomeAssistant

from custom_components.replace_device.support import Support


async def test_websocket(hass: HomeAssistant, hass_ws_client) -> None:
    s = Support(hass, "replace_device", "replace-device", "Replace device", summary=lambda: {"replacements": 0})
    await s.async_setup()
    client = await hass_ws_client(hass)

    async def post(path, data, timeout=30):
        if path == "/":
            assert data["diagnostics"]["version"] and data["install"]
            return {"ok": True, "id": "20261114-abc123"}
        return {"reports": [], "notes": []}

    with patch.object(s, "_post", post):
        await client.send_json_auto_id({"type": "replace_device/support", "action": "status"})
        r = await client.receive_json()
        assert r["success"] and r["result"]["share"] is True
        await client.send_json_auto_id({"type": "replace_device/support", "action": "send", "note": "hi", "images": []})
        r = await client.receive_json()
        assert r["success"] and r["result"]["ok"] and r["result"]["last_help"]["id"] == "20261114-abc123"
        await client.send_json_auto_id({"type": "replace_device/support", "action": "reply", "report": "20261114-abc123", "text": "x"})
        r = await client.receive_json()
        assert r["success"]
        await client.send_json_auto_id({"type": "replace_device/support", "action": "share", "on": False})
        r = await client.receive_json()
        assert r["success"] and r["result"]["share"] is False
    s.unload()


async def test_update_card_rules(hass: HomeAssistant) -> None:
    """Small fixes: the card after 7 days behind. A new feature version: after 2 days. An error this installation had,
    fixed in a newer version: at once, with one notification in Home Assistant. "Later" hides it for 7 days."""
    import time

    s = Support(hass, "replace_device", "replace-device", "Replace device")
    await s.async_setup()
    sent = []

    async def post(path, data, timeout=30):
        sent.append(data)
        return {"reports": [], "notes": [], "latest": latest}

    day = 86400
    with patch.object(s, "version", lambda: "1.8.1"), patch.object(s, "_post", post), \
            patch("custom_components.replace_device.support.persistent_notification.async_create") as note:
        latest = {"version": "1.8.2", "note": "Fixes a thing", "date": "", "repo": "Clahen86/ha-replace-device"}
        await s.fetch_answers()
        assert sent[-1]["version"] == "1.8.1"
        u = s.update()
        assert u["version"] == "1.8.2" and not u["big"] and not u["due"]  # a small fix: not yet
        s.d["behind"]["1.8.2"] = time.time() - 8 * day
        assert s.update()["due"]  # 8 days behind: now
        await s.snooze()
        assert not s.update()["due"]  # "Later"
        latest = {"version": "1.9.0", "note": "Groups", "date": "", "repo": "Clahen86/ha-replace-device"}
        await s.fetch_answers()
        s.d["behind"]["1.9.0"] = time.time() - 3 * day
        assert s.update()["big"] and s.update()["due"]  # a new feature version breaks through "Later"
        assert not note.called
        # an error this installation had is fixed in a newer version: at once, one notification
        s.d["replies"]["notes"] = [{"error": "KeyError at x.py", "hash": "rd:abc", "msgs": [{"from": "dev", "text": "Thanks! Fixed in 1.8.2"}]}]
        s.d["behind"].clear()
        s._update_notices()
        assert s.update()["fixed"][0]["version"] == "1.8.2" and s.update()["due"]
        assert note.call_count == 1
        s._update_notices()
        assert note.call_count == 1  # not twice
    with patch.object(s, "version", lambda: "1.9.0"):
        assert s.update() is None  # up to date: no card
    s.unload()
