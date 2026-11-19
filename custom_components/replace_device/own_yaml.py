"""The user's own YAML files: fixed after their OK in the test run ("Fix my own YAML files").

configuration.yaml and everything it includes, packages/, YAML dashboards, AppDaemon's apps.yaml and ESPHome's
files. Only whole ids are replaced, the file is backed up next to itself first (<file>.bak-replace-device-<UTC>),
and it is only written when it still loads exactly as before - apart from the ids. Files the editors write
(automations.yaml …) are handled elsewhere; secrets, .storage, custom_components, backups and code are never touched.
All of it runs in the executor."""

from __future__ import annotations

import hashlib
import os
import re
import shutil
import tempfile
import time
from typing import Any

import yaml
from annotatedyaml.loader import PythonSafeLoader

from . import tidy

_MAX_SIZE = 5_000_000
_MAX_DEPTH = 4
_NEVER_DIRS = (".storage", ".cloud", "custom_components", "deps", "tts", "node-red", "nodered", "node_modules")
# Tags that would read other files or secrets: kept as they are written, never followed.
_TAGS = (
    "!include", "!include_dir_list", "!include_dir_merge_list", "!include_dir_named", "!include_dir_merge_named",
    "!secret", "!env_var", "!input",
)
_KEY_INCLUDE = re.compile(
    r"^\s*([a-z_][a-z0-9_]*)\s*:\s*!include(?:_dir_(?:named|merge_named|list|merge_list))?\s+['\"]?([^\s'\"#]+)",
    re.MULTILINE,
)


class _Loader(PythonSafeLoader):
    """Home Assistant's YAML loader, with !include, !secret … (and ESPHome's !lambda …) kept as written."""


def _opaque(loader: _Loader, *args: Any) -> Any:
    node = args[-1]
    if isinstance(node, yaml.ScalarNode):
        value: Any = loader.construct_scalar(node)
    elif isinstance(node, yaml.SequenceNode):
        value = loader.construct_sequence(node, deep=True)
    else:
        value = yaml.SafeLoader.construct_mapping(loader, node, deep=True)
    return {"!tag": node.tag, "value": value}


for _tag in _TAGS:
    _Loader.add_constructor(_tag, _opaque)
_Loader.add_multi_constructor("!", _opaque)


def parse(text: str) -> Any:
    """The YAML as Home Assistant reads it (tags kept as written). Raises on a YAML error."""
    return yaml.load(text, Loader=lambda stream: _Loader(stream, None))  # noqa: S506 - a safe loader


def never(path: str, config_dir: str, handled: set[str]) -> bool:
    """Files that are never written here."""
    real = os.path.realpath(path)
    root = os.path.realpath(config_dir)
    name = os.path.basename(path)
    if not real.startswith(root + os.sep) or not name.endswith((".yaml", ".yml")):
        return True
    parts = os.path.relpath(real, root).split(os.sep)
    return (
        name == "secrets.yaml"
        or ".bak" in name
        or ".before-" in name
        or os.path.normpath(path) in handled
        or real in {os.path.realpath(h) for h in handled}
        or any(p in _NEVER_DIRS or p.startswith(".") for p in parts[:-1])
    )


def files(
    config_dir: str, found: list[tuple[str, str]], dashboards: list[str], handled: set[str]
) -> list[tuple[str, str]]:
    """(path, kind) of the files that may be fixed: the YAML Home Assistant loads (found: rename.yaml_files),
    packages/, AppDaemon's apps.yaml and ESPHome. kind: config, dashboard, appdaemon or esphome."""
    dash = {os.path.normpath(d) for d in dashboards}
    result: dict[str, str] = {}
    for path, kind in found:
        path = os.path.normpath(path)
        result[path] = "dashboard" if path in dash else kind
    for folder, kind, only in (("packages", "config", None), ("appdaemon", "appdaemon", "apps.yaml")):
        top = os.path.join(config_dir, folder)
        for root, dirs, names in os.walk(top):
            dirs[:] = [d for d in dirs if not d.startswith(".")]
            if root.count(os.sep) - top.count(os.sep) >= _MAX_DEPTH:
                dirs[:] = []
            for name in names:
                if (only is None and name.endswith((".yaml", ".yml"))) or name == only:
                    result.setdefault(os.path.normpath(os.path.join(root, name)), kind)
    return sorted((p, k) for p, k in result.items() if not never(p, config_dir, handled))


def _read(path: str) -> tuple[str, str] | None:
    """(text, encoding) with the line endings as they are; None for a big or unreadable file."""
    try:
        if os.path.getsize(path) > _MAX_SIZE:
            return None
        with open(path, "rb") as file:
            raw = file.read()
    except OSError:
        return None
    encoding = "utf-8-sig" if raw.startswith(b"\xef\xbb\xbf") else "utf-8"
    try:
        return raw.decode(encoding), encoding
    except UnicodeDecodeError:
        return None


class _Collision(Exception):
    """Two keys would become one (e.g. customize: for both the old and the new id)."""


def _swap(value: Any, ids: dict[str, str]) -> Any:
    if isinstance(value, str):
        return tidy.replace_ids(value, ids)
    if isinstance(value, dict):
        swapped = {_swap(k, ids): _swap(v, ids) for k, v in value.items()}
        if len(swapped) != len(value):
            raise _Collision
        return swapped
    if isinstance(value, list):
        return [_swap(v, ids) for v in value]
    return value


def _same(old: Any, new: Any, ids: dict[str, str]) -> bool:
    """The new text loads like the old one, with only the ids changed."""
    try:
        return bool(_swap(old, ids) == new)
    except _Collision:
        return False


def _lines(before: str, after: str) -> list[dict[str, Any]]:
    return [
        {"line": n, "before": o, "after": a}
        for n, (o, a) in enumerate(zip(before.splitlines(), after.splitlines(), strict=False), start=1)
        if o != a
    ]


def preview(config_dir: str, todo: list[tuple[str, str]], ids: dict[str, str]) -> dict[str, list[dict[str, Any]]]:
    """{"files": [{file, kind, lines}] that can be fixed, "broken": [{file, kind}] that use an id but wouldn't load}."""
    result: dict[str, list[dict[str, Any]]] = {"files": [], "broken": []}
    for path, kind, text, new, ok in _changes(todo, ids):
        item = {"file": os.path.relpath(path, config_dir), "kind": kind}
        if ok:
            result["files"].append(item | {"lines": _lines(text, new)})
        else:
            result["broken"].append(item)
    return result


def _changes(todo: list[tuple[str, str]], ids: dict[str, str]) -> list[tuple[str, str, str, str, bool]]:
    """(path, kind, text, new text, loads the same) of the files that use an id."""
    found = []
    for path, kind in todo:
        read = _read(path)
        if read is None:
            continue
        text = read[0]
        new = tidy.replace_ids(text, ids)
        if new == text:
            continue
        try:
            ok = _same(parse(text), parse(new), ids)
        except yaml.YAMLError:
            ok = False
        found.append((path, kind, text, new, ok))
    return found


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def _write(path: str, text: str, encoding: str) -> None:
    """Write atomically, with the file's own encoding, line endings and permissions."""
    folder = os.path.dirname(path)
    fd, temp = tempfile.mkstemp(dir=folder, prefix=f".{os.path.basename(path)}.", suffix=".tmp")
    try:
        with os.fdopen(fd, "wb") as file:
            file.write(text.encode(encoding))
            file.flush()
            os.fsync(file.fileno())
        shutil.copymode(path, temp)
        os.replace(temp, path)
    except BaseException:
        if os.path.exists(temp):
            os.remove(temp)
        raise


def _backup(path: str, tag: str = "") -> str:
    stamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    backup = f"{path}.bak-replace-device{tag}-{stamp}"
    n = 2
    while os.path.exists(backup):
        backup, n = f"{path}.bak-replace-device{tag}-{stamp}-{n}", n + 1
    shutil.copy2(path, backup)
    return backup


def apply(config_dir: str, todo: list[tuple[str, str]], ids: dict[str, str]) -> dict[str, Any]:
    """Fix the files: back up, check that it still loads the same, write. Returns {"files": [...], "failed": [...]}
    where each file is {file, kind, backup, before, after (sha256), lines (the new lines), domains}."""
    done: dict[str, Any] = {"files": [], "failed": []}
    for path, kind, text, new, ok in _changes(todo, ids):
        rel = os.path.relpath(path, config_dir)
        if not ok:
            done["failed"].append(rel)
            continue
        read = _read(path)
        if read is None or read[0] != text:
            done["failed"].append(rel)  # changed while we looked
            continue
        try:
            backup = _backup(path)
            _write(path, new, read[1])
        except OSError:
            done["failed"].append(rel)
            continue
        before = set(text.splitlines())
        done["files"].append(
            {
                "file": rel,
                "kind": kind,
                "backup": os.path.relpath(backup, config_dir),
                "before": _sha(text),
                "after": _sha(new),
                "lines": [ln for ln in new.splitlines() if ln not in before],
            }
        )
    return done


def undo(config_dir: str, fixed: list[dict[str, Any]], back: dict[str, str]) -> list[str]:
    """Put the old ids back: the backup when the file is as it was left, else only the lines that were changed."""
    restored = []
    for item in fixed:
        path = os.path.join(config_dir, item["file"])
        read = _read(path)
        if read is None:
            continue
        text, encoding = read
        backup = os.path.join(config_dir, item.get("backup") or "")
        old = _read(backup) if item.get("backup") and os.path.isfile(backup) else None
        if _sha(text) == item.get("after") and old is not None and _sha(old[0]) == item.get("before"):
            new = old[0]
        else:
            # Edited since: only the lines this made go back, and only if it still loads the same.
            mine = set(item.get("lines") or [])
            parts = text.splitlines(keepends=True)
            for i, line in enumerate(parts):
                if line.rstrip("\r\n") in mine:
                    parts[i] = tidy.replace_ids(line, back)
            new = "".join(parts)
            forward = {new_id: old_id for old_id, new_id in back.items()}
            try:
                # Loads like the file does now, apart from the ids put back.
                if new == text or not _same(parse(new), parse(text), forward):
                    continue
            except yaml.YAMLError:
                continue
            try:
                _backup(path, "-undo")
            except OSError:
                continue
        try:
            _write(path, new, encoding)
        except OSError:
            continue
        restored.append(item["file"])
    return restored


def domains(config_dir: str, changed: list[str], candidates: list[tuple[str, str]]) -> tuple[set[str], bool]:
    """The integrations whose YAML changed (to reload), and whether a restart may be needed (configuration.yaml
    itself, or a part that can't be reloaded)."""
    found: set[str] = set()
    restart = False
    changed_paths = {os.path.normpath(os.path.join(config_dir, c)) for c in changed}
    packages = os.path.normpath(os.path.join(config_dir, "packages"))
    includes: list[tuple[str, str]] = []
    for path, kind in candidates:
        if kind != "config" or (read := _read(path)) is None:
            continue
        for key, target in _KEY_INCLUDE.findall(read[0]):
            includes.append((key, os.path.normpath(os.path.join(os.path.dirname(path), target))))
    for path in changed_paths:
        if os.path.basename(path) == "configuration.yaml" and os.path.dirname(path) == os.path.normpath(config_dir):
            restart = True
            continue
        keys = {k for k, t in includes if path == t or path.startswith(t + os.sep)}
        if path.startswith(packages + os.sep) or "packages" in keys:
            # A package can hold several integrations: its top-level keys.
            try:
                data = parse((_read(path) or ("", ""))[0])
            except yaml.YAMLError:
                data = None
            found |= {str(k) for k in data} if isinstance(data, dict) else set()
            keys.discard("packages")
        found |= keys
    return found, restart
