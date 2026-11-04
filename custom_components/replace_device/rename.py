"""Renaming a device: its entity ids follow the new name, and so does everything in Home Assistant that uses them.

Home Assistant's own "rename entity ids too" changes the ids but leaves automations, scripts, dashboards and helpers
pointing at the old ones. Here the ids change and every place Home Assistant can reach is updated with them."""

from __future__ import annotations

import os
import re
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.util import slugify

from .tidy import _part, replace_ids

_INCLUDE = re.compile(r"!include(_dir_(?:named|merge_named|list|merge_list))?\s+['\"]?([^\s'\"#]+)")
_MAX_FILES = 2000
_MAX_SIZE = 5_000_000


def plan_ids(hass: HomeAssistant, entries: list[Any], old_name: str, new_name: str) -> list[dict[str, str]]:
    """The new id of each entity: the old name's part swapped for the new one ("sensor.kitchen_x" ->
    "sensor.pantry_x"); an id that doesn't follow the old name gets one after the new name. Taken ids get _2 …"""
    registry = er.async_get(hass)
    old_slug, new_slug = slugify(old_name), slugify(new_name)
    if not new_slug:
        return []
    moving = {e.entity_id for e in entries}
    planned: set[str] = set()
    changes = []
    for entry in entries:
        domain, object_id = entry.entity_id.split(".", 1)
        if old_slug and (object_id == old_slug or object_id.startswith(f"{old_slug}_")):
            base = f"{domain}.{new_slug}{object_id[len(old_slug):]}"
        else:
            part = slugify(_part(entry, old_name))
            base = f"{domain}.{new_slug}_{part}" if part else f"{domain}.{new_slug}"
        new_id, n = base, 2
        # An id another entity of this device gives up is free, unless one of them takes it first.
        while new_id in planned or (
            new_id != entry.entity_id
            and new_id not in moving
            and (registry.async_get(new_id) or hass.states.get(new_id))
        ):
            new_id, n = f"{base}_{n}", n + 1
        planned.add(new_id)
        if new_id != entry.entity_id:
            name = str(entry.name or entry.original_name or "")
            changes.append({"from": entry.entity_id, "to": new_id, "name": name})
    return changes


def yaml_files(config_dir: str, skip: set[str], extra: list[str]) -> list[tuple[str, str]]:
    """(path, kind) of the YAML files Home Assistant loads – configuration.yaml and everything it includes, and YAML
    dashboards – plus ESPHome's (kind "esphome": they also need to be installed on the device again).

    skip: files handled elsewhere (automations.yaml …). secrets.yaml is never touched."""
    found: dict[str, str] = {}
    todo = [os.path.join(config_dir, "configuration.yaml"), *extra]
    while todo and len(found) < _MAX_FILES:
        path = os.path.normpath(todo.pop())
        if path in found or not os.path.isfile(path) or os.path.basename(path) == "secrets.yaml":
            continue
        found[path] = "config"
        try:
            text = _read(path)
        except OSError:
            continue
        for kind, target in _INCLUDE.findall(text or ""):
            target = os.path.normpath(os.path.join(os.path.dirname(path), target))
            if not target.startswith(config_dir):
                continue
            if kind:
                for root, dirs, names in os.walk(target):
                    dirs[:] = [d for d in dirs if not d.startswith(".")]
                    todo += [os.path.join(root, n) for n in names if n.endswith((".yaml", ".yml"))]
            else:
                todo.append(target)
    esphome = os.path.join(config_dir, "esphome")
    if os.path.isdir(esphome):
        for name in sorted(os.listdir(esphome)):
            path = os.path.join(esphome, name)
            if name.endswith((".yaml", ".yml")) and name != "secrets.yaml" and os.path.isfile(path):
                found[path] = "esphome"
    return [(p, k) for p, k in sorted(found.items()) if p not in skip]


def _read(path: str) -> str | None:
    if os.path.getsize(path) > _MAX_SIZE:
        return None
    with open(path, encoding="utf-8") as file:
        return file.read()


def files_using(config_dir: str, files: list[tuple[str, str]], ids: dict[str, str]) -> list[tuple[str, str, str]]:
    """(path, kind, new text) of the files that use one of the ids."""
    changed = []
    for path, kind in files:
        try:
            text = _read(path)
        except OSError:
            continue
        if not text:
            continue
        new = replace_ids(text, ids)
        if new != text:
            changed.append((path, kind, new))
    return changed
