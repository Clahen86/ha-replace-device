"""A switch that became a light (or the other way): the action follows its new kind.

The entity id is changed everywhere already (switch.lamp -> light.lamp); an action like "switch.turn_on" on it would
then fail. Here turn_on/turn_off/toggle get the new domain - only where every entity the action targets is one of the
moved ones of that domain. An action that targets others too, or a service the new kind doesn't have, is listed for
the user instead. automations.yaml and scripts.yaml are read and written as Home Assistant's editors do."""

from __future__ import annotations

import os
from typing import Any

from homeassistant.util.file import write_utf8_file_atomic
from homeassistant.util.yaml import dump, load_yaml

from .const import AUTOMATIONS_FILE, SCRIPTS_FILE

# Services with the same name and meaning in these domains.
_SAME = {"turn_on", "turn_off", "toggle"}
_HAS_SAME = {"light", "switch", "fan", "input_boolean", "siren", "humidifier", "media_player", "remote"}


def _targets(step: dict[str, Any]) -> list[str]:
    found: list[str] = []
    for holder in (step, step.get("target"), step.get("data")):
        if isinstance(holder, dict):
            ids = holder.get("entity_id")
            found += [ids] if isinstance(ids, str) else [i for i in ids if isinstance(i, str)] if isinstance(ids, list) else []
    return found


def _walk(node: Any, moved: dict[str, str], name: str, changed: list[str], open_: list[str]) -> None:
    if isinstance(node, list):
        for x in node:
            _walk(x, moved, name, changed, open_)
        return
    if not isinstance(node, dict):
        return
    key = "action" if isinstance(node.get("action"), str) else "service" if isinstance(node.get("service"), str) else None
    if key and "." in node[key]:
        domain, service = node[key].split(".", 1)
        targets = _targets(node)
        hit = [t for t in targets if t in moved.values()]
        olds = {o.split(".", 1)[0] for o, n in moved.items() if n in hit}
        if hit and domain in olds:
            kinds = {t.split(".", 1)[0] for t in hit}
            # Also targets by area, device or label: those may be switches still - the user decides.
            wide = any(isinstance(h, dict) and any(h.get(k) for k in ("area_id", "device_id", "label_id", "floor_id"))
                       for h in (node, node.get("target"), node.get("data")))
            if not wide and len(hit) == len(targets) and len(kinds) == 1 and service in _SAME and (new := kinds.pop()) in _HAS_SAME and domain in _HAS_SAME:
                node[key] = f"{new}.{service}"
                changed.append(f"{name}: {domain}.{service} → {new}.{service}")
            else:
                open_.append(f"{name}: {domain}.{service} → {', '.join(hit)}")
    for value in node.values():
        _walk(value, moved, name, changed, open_)


def translate(config_dir: str, moved: dict[str, str]) -> dict[str, Any]:
    """moved: old entity id -> new entity id (already written in the files). Runs in the executor."""
    moved = {o: n for o, n in moved.items() if o.split(".", 1)[0] != n.split(".", 1)[0]}
    result: dict[str, Any] = {"changed": [], "open": [], "domains": []}
    if not moved:
        return result
    for domain, file in (("automation", AUTOMATIONS_FILE), ("script", SCRIPTS_FILE)):
        path = os.path.join(config_dir, file)
        if not os.path.isfile(path):
            continue
        with open(path, encoding="utf-8") as f:
            if any(t in f.read() for t in ("!include", "!secret", "!env_var")):
                continue  # would come back written out in full (secrets too): left for the user
        try:
            data = load_yaml(path)
        except Exception:  # noqa: BLE001 - a file it can't read back is never written
            continue
        items = (
            [(str(a.get("alias") or a.get("id") or "?"), a) for a in data if isinstance(a, dict)] if isinstance(data, list)
            else [(str(v.get("alias") or k), v) for k, v in data.items() if isinstance(v, dict)] if isinstance(data, dict)
            else []
        )
        before = len(result["changed"])
        for name, item in items:
            for part in ("actions", "action", "sequence"):
                _walk(item.get(part), moved, name, result["changed"], result["open"])
        if len(result["changed"]) > before:
            write_utf8_file_atomic(path, dump(data))
            result["domains"].append(domain)
    return result
