"""How Replace Device is used, for the developer (sent with the daily question when sharing is on - see support.py):
which integrations are replaced by which, whether it worked, and what moved. Never names or entity IDs."""

from __future__ import annotations

from typing import Any


def setup_info(replacer: Any) -> dict[str, Any]:
    groups: dict[str, dict[str, Any]] = {}
    counts = {"replacements": 0, "renames": 0, "group_renames": 0, "follows": 0, "bulk": 0, "undone": 0, "swaps": 0, "copies": 0}
    batches = set()
    for r in replacer.history:
        kind = r.get("kind") or "replace"
        if r.get("undone"):
            counts["undone"] += 1
        if kind == "rename":
            counts["group_renames" if (r.get("old_device") or {}).get("model") == "Group" else "renames"] += 1
            continue
        if kind == "follow":
            counts["follows"] += 1
            continue
        if kind in ("swap", "copy"):
            counts["swaps" if kind == "swap" else "copies"] += 1
            continue
        counts["replacements"] += 1
        if r.get("batch"):
            batches.add(r["batch"])
        old_p, new_p = (list(r.get("platforms") or []) + [None, None])[:2]
        plat = "group" if (r.get("old_device") or {}).get("model") == "Group" else f"{old_p or '?'}→{new_p or '?'}"
        g = groups.setdefault(plat, {"kind": "replacement", "platform": plat, "ok": True, "errors": [],
                                     "extra": {"times": 0, "entities": 0, "failed_entities": 0, "files": 0, "undone": 0},
                                     "_makers": {}})
        x = g["extra"]
        x["times"] += 1
        x["entities"] += len(r.get("entities") or [])
        x["failed_entities"] += len(r.get("failed") or [])
        x["files"] += len(r.get("files") or [])
        x["undone"] += 1 if r.get("undone") else 0
        if r.get("failed"):
            g["ok"] = False
            if "some entities could not take over" not in g["errors"]:
                g["errors"].append("some entities could not take over")
        mk = list(r.get("makers") or [])
        if len(mk) == 2 and any(mk):
            key = f"{mk[0] or '?'} → {mk[1] or '?'}"
            g["_makers"][key] = g["_makers"].get(key, 0) + 1
    counts["bulk"] = len(batches)
    devices = []
    for g in groups.values():
        top = max(g.pop("_makers").items(), key=lambda kv: kv[1], default=None)
        if top:
            g["model"] = top[0][:60]
        devices.append(g)
    return {"devices": devices[:30], "counts": counts,
            "features": {"ai": bool(replacer.ai_entity), "hidden_devices": bool(replacer.hidden),
                         "ignored_refs": bool(replacer.ignored_refs)}}
