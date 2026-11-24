"""Orphaned long-term statistics: statistics left behind by entities that were deleted - moved onto a new entity.

Home Assistant keeps a sensor's long-term statistics (energy, temperature …) under its entity ID, also after the
entity is deleted. Here they are found and given to the entity that took over:

- the new entity has no statistics yet: the old statistics are renamed to it (quick, and can be undone)
- it has some: the old hours from before it started are added in front, and for counters (kWh …) its own sums are
  raised by the old total, so the curve goes on without a jump; the old ID is removed afterwards (not undoable -
  make a backup first)
"""

from __future__ import annotations

import difflib
from datetime import datetime, timezone
import logging
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

_LOGGER = logging.getLogger(__name__)
EPOCH = datetime(2000, 1, 1, tzinfo=timezone.utc)


def _recorder(hass: HomeAssistant):
    from homeassistant.components.recorder import get_instance

    return get_instance(hass)


async def _span(hass: HomeAssistant, statistic_id: str) -> dict[str, Any]:
    """First and last hour, and the last value, of one statistic."""
    from homeassistant.components.recorder import statistics as st

    inst = _recorder(hass)
    first = await inst.async_add_executor_job(
        st.statistics_during_period, hass, EPOCH, None, {statistic_id}, "month", None, {"state", "sum", "mean"}
    )
    last = await inst.async_add_executor_job(st.get_last_statistics, hass, 1, statistic_id, False, {"state", "sum", "mean"})
    rows, lrow = first.get(statistic_id) or [], (last.get(statistic_id) or [None])[0]
    if not rows or lrow is None:
        return {}
    return {"first": rows[0]["start"], "last": lrow["start"], "value": lrow.get("sum") if lrow.get("sum") is not None
            else lrow.get("state") if lrow.get("state") is not None else lrow.get("mean")}


async def async_orphans(hass: HomeAssistant) -> list[dict[str, Any]]:
    """Statistics whose entity is gone, with the best entities to give them to."""
    if "recorder" not in hass.config.components:
        return []
    from homeassistant.components.recorder.statistics import async_list_statistic_ids

    registry = er.async_get(hass)
    all_ids = await async_list_statistic_ids(hass)
    have = {m["statistic_id"] for m in all_ids}
    out = []
    for m in all_ids:
        sid = m["statistic_id"]
        if m.get("source") != "recorder" or registry.async_get(sid) is not None or hass.states.get(sid) is not None:
            continue
        span = await _span(hass, sid)
        if not span:
            continue
        kind = "sum" if m.get("has_sum") else "mean"
        out.append({
            "statistic_id": sid, "name": m.get("name") or sid.split(".", 1)[1].replace("_", " "),
            "unit": m.get("statistics_unit_of_measurement") or m.get("display_unit_of_measurement"), "kind": kind,
            **span, "candidates": _candidates(hass, sid, m, kind, have),
        })
    out.sort(key=lambda o: o["last"], reverse=True)
    return out


def _candidates(hass: HomeAssistant, sid: str, meta: dict[str, Any], kind: str, have: set[str]) -> list[dict[str, Any]]:
    """Live entities with the same unit and kind, most alike by name first."""
    unit = meta.get("statistics_unit_of_measurement") or meta.get("display_unit_of_measurement")
    domain, obj = sid.split(".", 1)
    found = []
    for state in hass.states.async_all(domain):
        a = state.attributes
        sc = a.get("state_class")
        if sc is None or (kind == "sum") != (sc in ("total", "total_increasing")):
            continue
        if (a.get("unit_of_measurement") or None) != (unit or None):
            continue
        name = str(a.get("friendly_name") or state.entity_id)
        score = max(difflib.SequenceMatcher(None, obj, state.object_id).ratio(),
                    difflib.SequenceMatcher(None, obj.replace("_", " "), name.lower()).ratio())
        found.append({"entity_id": state.entity_id, "name": name, "score": round(score, 2), "has_stats": state.entity_id in have})
    found.sort(key=lambda c: c["score"], reverse=True)
    return found[:5]


async def async_migrate(hass: HomeAssistant, old: str, new: str) -> dict[str, Any]:
    """Give the statistics of old (gone) to new. Returns what was done: "renamed" or "merged"."""
    from homeassistant.components.recorder import statistics as st

    inst = _recorder(hass)
    from functools import partial

    meta = await inst.async_add_executor_job(partial(st.get_metadata, hass, statistic_ids={old, new}))
    if old not in meta:
        raise ValueError("no_statistics")
    if er.async_get(hass).async_get(old) is not None or hass.states.get(old) is not None:
        raise ValueError("not_orphaned")
    if new not in meta:
        inst.async_update_statistics_metadata(old, new_statistic_id=new)
        await inst.async_block_till_done()
        return {"done": "renamed"}

    # Both have statistics: the old hours before the new ones start go in front, sums are carried over.
    types = {"mean", "min", "max", "sum", "state", "last_reset"}
    rows = await inst.async_add_executor_job(st.statistics_during_period, hass, EPOCH, None, {old, new}, "hour", None, types)
    old_rows, new_rows = rows.get(old) or [], rows.get(new) or []
    if not new_rows:
        raise ValueError("no_statistics")
    start_new = new_rows[0]["start"]
    meta_new = dict(meta[new][1])
    if meta_new.get("has_sum"):
        before = [r for r in old_rows if r["start"] < start_new]  # counters: only in front, or the sums would break
    else:
        have = {r["start"] for r in new_rows}
        before = [r for r in old_rows if r["start"] not in have]  # measurements: every hour the new one doesn't have
    if not before:
        raise ValueError("nothing_to_add")

    def stat(r: dict[str, Any]) -> dict[str, Any]:
        d: dict[str, Any] = {"start": datetime.fromtimestamp(r["start"], timezone.utc)}
        for k in ("mean", "min", "max", "sum", "state"):
            if r.get(k) is not None:
                d[k] = r[k]
        if r.get("last_reset") is not None:
            d["last_reset"] = datetime.fromtimestamp(r["last_reset"], timezone.utc)
        return d

    st.async_import_statistics(hass, meta_new, [stat(r) for r in before])
    carried = None
    if meta_new.get("has_sum") and before and before[-1].get("sum") is not None:
        carried = float(before[-1]["sum"])
        if carried:
            inst.async_adjust_statistics(new, datetime.fromtimestamp(start_new, timezone.utc), carried,
                                         meta_new.get("unit_of_measurement") or "")
    inst.async_clear_statistics([old])
    await inst.async_block_till_done()
    return {"done": "merged", "hours": len(before), "carried": carried}


async def async_would_follow(hass: HomeAssistant, moves: dict[str, str]) -> dict[str, str]:
    """Of the coming renames (old id -> new id): those where the recorder takes the old id's statistics along, because
    the new id has none of its own. Undo uses it: the entity gets its own id back, the history stays with the name."""
    if "recorder" not in hass.config.components or not (moves := {o: n for o, n in moves.items() if o != n}):
        return {}
    from functools import partial

    from homeassistant.components.recorder import statistics as st

    ids = set(moves) | set(moves.values())
    meta = await _recorder(hass).async_add_executor_job(partial(st.get_metadata, hass, statistic_ids=ids))
    return {o: n for o, n in moves.items() if o in meta and n not in meta}


async def async_keep(hass: HomeAssistant, kept: dict[str, str]) -> None:
    """Statistics the recorder moved along with a rename go back to the id they were recorded under."""
    if not kept:
        return
    inst = _recorder(hass)
    await inst.async_block_till_done()  # the recorder's own renames first
    for old, new in kept.items():
        inst.async_update_statistics_metadata(new, new_statistic_id=old)
    await inst.async_block_till_done()


async def async_delete(hass: HomeAssistant, statistic_id: str) -> None:
    """Remove statistics that are left behind (only those of an entity that is gone)."""
    if er.async_get(hass).async_get(statistic_id) is not None or hass.states.get(statistic_id) is not None:
        raise ValueError("not_orphaned")
    inst = _recorder(hass)
    inst.async_clear_statistics([statistic_id])
    await inst.async_block_till_done()


async def async_last_state(hass: HomeAssistant, statistic_id: str) -> float | None:
    """The meter's last reading in the long-term statistics (a dead meter's state is just "unavailable")."""
    from homeassistant.components.recorder import statistics as st

    try:
        last = await _recorder(hass).async_add_executor_job(st.get_last_statistics, hass, 1, statistic_id, False, {"state"})
    except Exception:  # noqa: BLE001 - no recorder, no statistics
        return None
    row = (last.get(statistic_id) or [None])[0]
    return float(row["state"]) if row and row.get("state") is not None else None


async def async_fix_jump(hass: HomeAssistant, fix: dict[str, Any], undo: bool = False) -> bool:
    """Take a new meter's jump out of the energy sums, once the hour it shows in is written (undo: put it back).

    fix: {"statistic_id", "amount", "unit", "old", "after", "start"?}. Returns True when the sums were adjusted."""
    from homeassistant.components.recorder import statistics as st

    inst = _recorder(hass)
    sid = fix["statistic_id"]
    start = fix.get("start")
    if start is None:
        # The first hour after the replacement where the meter shows another reading than the old one had.
        rows = await inst.async_add_executor_job(
            st.statistics_during_period, hass, datetime.fromtimestamp(fix["after"], timezone.utc), None, {sid}, "hour", None, {"state"}
        )
        start = next((r["start"] for r in rows.get(sid) or [] if r.get("state") is not None and abs(float(r["state"]) - fix["old"]) > 1e-6), None)
        if start is None:
            return False  # not written yet: tried again later
        fix["start"] = start
    amount = fix["amount"] if undo else -fix["amount"]
    inst.async_adjust_statistics(sid, datetime.fromtimestamp(start, timezone.utc), amount, fix["unit"] or "")
    await inst.async_block_till_done()
    return True
