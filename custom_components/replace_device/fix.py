"""The user's own YAML files and other integrations' settings that use an old id.

- Files (packages/, files configuration.yaml includes, custom_sentences/, ESPHome) are hand-written configuration:
  they are never written. The test run shows every line to change (before → after), for the user to do by hand.
- Other integrations: only if the user ticks one in the test run, and only through the integration's own options
  flow - the same form the user would fill in by hand - so the integration validates and saves its own settings.
  Entries without such a form stay on the list.
"""

from __future__ import annotations

import logging
import os
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from . import references, tidy

_LOGGER = logging.getLogger(__name__)


def _read(path: str) -> str | None:
    try:
        with open(path, encoding="utf-8") as file:
            return file.read()
    except OSError:
        return None


def swap_text(text: str, ids: dict[str, str], exact: bool) -> str:
    """The text with the ids changed: whole entity ids only (exact), or any occurrence of a registry id."""
    if exact:
        return tidy.replace_ids(text, ids)
    for old, new in ids.items():
        text = text.replace(old, new)
    return text


def _lines(before: str, after: str) -> list[dict[str, Any]]:
    """Every changed line with its line number. Only ids change, never line breaks, so the lines pair up."""
    return [
        {"line": n, "before": o, "after": a}
        for n, (o, a) in enumerate(zip(before.splitlines(), after.splitlines(), strict=False), start=1)
        if o != a
    ]


def files_preview(config_dir: str, files: list[str], ids: dict[str, str], exact: bool) -> list[dict[str, Any]]:
    """For each of the user's own files (relative to config_dir) that uses an id: the full change, line by line.

    These files are never written - the user makes the change by hand."""
    found = []
    for rel in files:
        path = os.path.join(config_dir, rel)
        if os.path.basename(path) == "secrets.yaml" or (text := _read(path)) is None:
            continue
        new = swap_text(text, ids, exact)
        if new != text:
            found.append({"file": rel, "lines": _lines(text, new)})
        elif lines := _mentions(text, ids):
            # Code outside Home Assistant (AppDaemon, Node-RED …) can spell an id in its own way: show where.
            found.append({"file": rel, "lines": lines})
    return found


def _mentions(text: str, ids: dict[str, str]) -> list[dict[str, Any]]:
    """Lines that mention an old id in any spelling, with the new id to use instead."""
    found = []
    for n, line in enumerate(text.splitlines(), start=1):
        low = line.lower()
        for old, new in ids.items():
            if len(old) >= 6 and old.lower() in low:
                found.append({"line": n, "before": line, "after": f"{old} → {new}", "hint": True})
                break
    return found


def entries_preview(hass: HomeAssistant, ids: dict[str, str], exact: bool, skip: set[str]) -> list[dict[str, Any]]:
    """Other integrations whose settings (options) can be changed through their own form."""
    found = []
    for entry in references.entries_using(hass, ids, skip):
        options = dict(entry.options)
        new = references.swap(options, ids, exact)
        if not entry.supports_options or new == options or references.swap(dict(entry.data), ids, exact) != dict(
            entry.data
        ):
            continue  # nothing in the options, no form, or the ids are in data only the integration may write
        changes = [
            {"before": str(options[key]), "after": str(new[key])} for key in options if options[key] != new.get(key)
        ]
        found.append({"entry_id": entry.entry_id, "title": entry.title, "domain": entry.domain, "lines": changes})
    return found


async def async_apply_entries(
    hass: HomeAssistant, entry_ids: list[str], ids: dict[str, str], exact: bool
) -> tuple[list[str], list[str]]:
    """Change the picked integrations' settings through their own options flow. Returns (changed, failed) titles."""
    changed, failed = [], []
    for entry_id in entry_ids:
        entry = hass.config_entries.async_get_entry(entry_id)
        if entry is None:
            continue
        options = dict(entry.options)
        new = references.swap(options, ids, exact)
        if new == options:
            continue
        flow_id = None
        try:
            result = await hass.config_entries.options.async_init(entry_id)
            flow_id = result.get("flow_id")
            schema = result.get("data_schema")
            if result["type"] is not FlowResultType.FORM or schema is None:
                raise ValueError(f"no form ({result['type']})")
            keys = [str(key) for key in schema.schema]
            user_input = {key: new[key] for key in keys if key in new}
            result = await hass.config_entries.options.async_configure(flow_id, user_input)
            flow_id = None if result["type"] is FlowResultType.CREATE_ENTRY else flow_id
            if flow_id is not None:
                raise ValueError(f"the form did not accept it ({result['type']}: {result.get('errors')})")
            changed.append(entry.title)
        except Exception:  # noqa: BLE001 - it stays on the list for the user
            _LOGGER.warning("Could not change %s through its own settings form", entry.title, exc_info=True)
            failed.append(entry.title)
            if flow_id is not None:
                hass.config_entries.options.async_abort(flow_id)
    return changed, failed
