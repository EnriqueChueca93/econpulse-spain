"""What changed since the last update, as plain sentences.

After each fetch, `record` compares every indicator's latest reading with the state saved
the time before (data/releases.json):

    a new period              a release note   "Real GDP: 0.6% q/q in Q3 2026, after 0.7% in Q2 2026."
    the same period, revised  a revision note  (monthly, quarterly and annual series)
    a big daily move          a market note    "Spain 10-year yield: +12 bp since the last update, to 4.15%."

The first run only saves the state, and an indicator added later starts quietly too, so
the log never fills with "new" data that was simply fetched for the first time. Notes are
kept for 60 days.

`fresh_series` says which series brought new figures in the past week (from the release calendar
and from the release notes); the site marks the sections that show them as updated.
"""

import re
from datetime import datetime, timedelta, timezone

import pandas as pd

from .registry import Indicator
from .sources.base import MADRID
from .snapshot import summarize
from .store import Store
from .tables import fmt_move

KEEP_DAYS = 60
# A daily move worth a note: rates by 10 bp, prices by 2%.
MARKET_THRESHOLDS = {"bp": 10.0, "%": 2.0}


def _state(ind: Indicator, store: Store, catalog: dict) -> dict | None:
    series = store.load_series(ind.id)
    if series is None or series.dropna().empty:
        return None
    series = series.dropna()
    item = summarize(ind, series, catalog.get(ind.id, {}))
    head = item["headline"]
    if head is None:
        return None
    return {"date": series.index[-1].strftime("%Y-%m-%d"), "raw": float(series.iloc[-1]),
            "display": f"{head['display']} {head['label']}".strip(), "period": head["period"], "flash": item["flash"]}


def _market_move(ind: Indicator, now: dict, before: dict) -> str | None:
    unit = ind.change_unit or ""
    if unit not in MARKET_THRESHOLDS:
        return None
    ref = before["raw"]
    if ref == 0:
        return None
    change = (now["raw"] / ref - 1) * 100 if unit == "%" else (now["raw"] - ref) * (100 if ind.unit == "%" else 1)
    if abs(change) < MARKET_THRESHOLDS[unit]:
        return None
    return fmt_move(ind, now["raw"], ref)


def record(indicators: list[Indicator], store: Store, now: datetime | None = None) -> list[dict]:
    """Compare with the saved state, log what changed, save the new state. Returns the new notes."""
    now = now or datetime.now(timezone.utc)
    saved = store.load_json("releases", None)
    first_run = saved is None
    saved = saved or {"state": {}, "notes": []}
    catalog = store.load_catalog()
    notes = []
    for ind in indicators:
        current = _state(ind, store, catalog)
        if current is None:
            continue
        before = saved["state"].get(ind.id)
        saved["state"][ind.id] = current
        if before is None:
            continue
        page = f"{ind.section}.html"
        flash = " (flash estimate)" if current["flash"] else ""
        if ind.freq == "D":
            move = _market_move(ind, current, before) if current["date"] > before["date"] else None
            if move:
                notes.append({"kind": "market", "id": ind.id, "page": page,
                              "text": f"{ind.label}: {move} since the last update, to {current['display']}."})
        elif current["date"] > before["date"]:
            notes.append({"kind": "release", "id": ind.id, "page": page,
                          "text": f"{ind.label}: {current['display']} in {current['period']}{flash}, "
                                  f"after {before['display']} in {before['period']}."})
        elif (current["date"] == before["date"] and current["display"] != before["display"]
              and abs(current["raw"] - before["raw"]) > 1e-9 * max(1, abs(before["raw"]))):
            # Only revisions that change the figure as shown: an index revised in its fourth decimal is no news.
            notes.append({"kind": "revision", "id": ind.id, "page": page,
                          "text": f"{ind.label} for {current['period']} revised to {current['display']}, "
                                  f"from {before['display']}."})
    stamp = now.isoformat(timespec="seconds")
    for n in notes:
        n["at"] = stamp
    cutoff = (now - timedelta(days=KEEP_DAYS)).isoformat(timespec="seconds")
    saved["notes"] = [n for n in saved["notes"] if n["at"] >= cutoff] + notes
    saved["updated_at"] = stamp
    if first_run:
        saved["started_at"] = stamp
    store.save_json("releases", saved)
    return notes


_NO_CHANGE = re.compile(r"revised to (.+), from \1\.$")


def shown_notes(saved: dict) -> list[dict]:
    """The logged notes worth showing: not revisions whose figure, as shown, did not change
    (logged before such revisions were left out)."""
    return [n for n in saved.get("notes", []) if not (n["kind"] == "revision" and _NO_CHANGE.search(n["text"]))]


def latest_notes(store: Store, max_age_days: int = 7) -> dict:
    """Notes from the most recent update that found something, if it was recent."""
    saved = store.load_json("releases", None) or {}
    notes = shown_notes(saved)
    out = {"updated_at": saved.get("updated_at"), "started_at": saved.get("started_at"), "at": None, "notes": []}
    if not notes:
        return out
    last = max(n["at"] for n in notes)
    if datetime.fromisoformat(last) < datetime.now(timezone.utc) - timedelta(days=max_age_days):
        return out
    order = {"release": 0, "revision": 1, "market": 2}
    out["at"] = last
    out["notes"] = sorted((n for n in notes if n["at"] == last), key=lambda n: order.get(n["kind"], 9))
    return out


def recent_releases(store: Store, items_by_id: dict, events: list[dict], today: pd.Timestamp, days: int = 7) -> list[dict]:
    """Calendar releases of the past week with the figures they brought, where the site has them."""
    out = []
    for e in events:
        day = e["when"].normalize()
        if not (today - pd.Timedelta(days=days) <= day <= today):
            continue
        figures = []
        for ind_id in e.get("ids", []):
            item = items_by_id.get(ind_id)
            head = item and item["headline"]
            if head and (not e["period"] or head["period"] == e["period"]):
                figures.append(f"{item['label']} {head['display']} {head['label']}".strip())
        out.append({"day": f"{day:%a} {day.day} {day:%b}", "label": e["label"], "period": e["period"],
                    "page": e["page"], "figures": figures, "ids": e.get("ids", [])})
    return list(reversed(out))


def fresh_series(store: Store, items_by_id: dict, events: list[dict], today: pd.Timestamp, days: int = 7) -> dict:
    """Series with new figures in the past `days` days: id -> {"day": the Madrid date, "period": shown}.

    A calendar release counts when the site now shows the period it brought; a release note (the
    log compares every update with the one before) counts on the day it was written. Revisions and
    market moves do not count."""
    start = today - pd.Timedelta(days=days)
    out: dict[str, dict] = {}

    def add(ind_id: str, day: pd.Timestamp) -> None:
        item = items_by_id.get(ind_id)
        head = item and item["headline"]
        if head and (ind_id not in out or day > out[ind_id]["day"]):
            out[ind_id] = {"day": day, "period": head["period"]}

    for e in events:
        day = e["when"].normalize()
        if start <= day <= today:
            for ind_id in e.get("ids", []):
                item = items_by_id.get(ind_id)
                head = item and item["headline"]
                if head and (not e["period"] or head["period"] == e["period"]):
                    add(ind_id, day)
    for n in (store.load_json("releases", None) or {}).get("notes", []):
        if n["kind"] == "release":
            day = pd.Timestamp(datetime.fromisoformat(n["at"]).astimezone(MADRID).date())
            if start <= day <= today:
                add(n["id"], day)
    return out


def updated_mark(ids, fresh: dict, labels: dict) -> dict | None:
    """For a section showing these series: the day of its newest figures and which they are."""
    hits = sorted((i for i in set(ids) if i in fresh), key=lambda i: (-fresh[i]["day"].value, labels.get(i, i)))
    if not hits:
        return None
    day = fresh[hits[0]]["day"]
    names = [f"{labels.get(i, i)} ({fresh[i]['period']})" for i in hits[:6]]
    return {"day": f"{day.day} {day:%b}", "what": "; ".join(names) + (f"; and {len(hits) - 6} more" if len(hits) > 6 else "")}
