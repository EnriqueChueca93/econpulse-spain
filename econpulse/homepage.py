"""The newest figures on the home page: the "Latest releases" cards at the top, and a small trend line
(a sparkline) in every key-indicator tile.

Each release of the past fortnight in the release calendar (INE, the Seguridad Social, the ECB) gets a card with
its main figure, that figure over the past few years as a sparkline, and a line of context: the highest or
lowest reading in more than a year ("The highest since Feb 2023"), or else the reading before ("After 9.2% y/y
in Aug 2026"). Sparklines are drawn here, as inline SVG, so they need no script; hovering over one gives its
range.
"""

import numpy as np
import pandas as pd

from . import i18n, transforms
from .i18n import _
from .registry import Indicator
from .snapshot import fmt_change, fmt_value, period_label
from .store import Store

DAYS = 14            # how far back the cards go
MAX_CARDS = 6
# How much history a sparkline shows, and the words for it.
WINDOW_YEARS = {"D": 1, "W": 1, "M": 3, "Q": 5, "A": 12}
# A reading is "the highest since ..." only when that is more than this many periods back (more than a year).
NOTABLE = {"M": 12, "Q": 4, "A": 2}
W, H, PAD = 120, 30, 3     # the sparkline's drawing box, in its own units (stretched to the tile's width)


def _format(ind: Indicator, transform: str):
    """How a reading of this indicator, so transformed, is written: as the tile writes it."""
    pct = transform in transforms.PERCENT_TRANSFORMS
    unit, decimals = ("%", 1) if pct else (ind.unit, ind.decimals)
    write = fmt_change if transform in transforms.DIFF_TRANSFORMS else fmt_value
    label = transforms.label(transform, ind.freq)

    def fmt(v: float) -> str:
        return f"{write(v, unit, decimals)} {label}".strip()
    return fmt, decimals


def headline_series(ind: Indicator, series: pd.Series | None, transform: str) -> pd.Series:
    """The series as its tile headlines it (y/y, q/q, the level...)."""
    if series is None or series.dropna().empty:
        return pd.Series(dtype=float)
    try:
        return transforms.apply(transform, series.dropna(), ind.freq).dropna()
    except ValueError:          # too little history to adjust, say
        return pd.Series(dtype=float)


def _span(years: int) -> str:
    return _("Past year") if years == 1 else _("Past {n} years").format(n=years)


def sparkline(ind: Indicator, ts: pd.Series, transform: str) -> dict | None:
    """Points for a small line of the past few years, with the last point marked, a dashed zero line when the
    line crosses zero, and its range as hover text. A daily series is drawn by its weekly averages (a day of the
    week would mislead: electricity is cheapest on Sundays), ending on the latest reading; its range is the
    daily readings'."""
    if ts.empty:
        return None
    years = WINDOW_YEARS.get(ind.freq, 3)
    part = ts[ts.index > ts.index[-1] - pd.DateOffset(years=years)]
    drawn = part
    if ind.freq == "D":
        drawn = pd.concat([part.resample("W").mean().dropna().iloc[:-1], part.iloc[-1:]])
    if len(drawn) < 3:
        return None
    values = drawn.to_numpy(dtype=float)
    lo, hi = float(values.min()), float(values.max())
    spread = (hi - lo) or 1.0
    xs = np.linspace(PAD, W - PAD, len(values))
    ys = PAD + (hi - values) / spread * (H - 2 * PAD)
    fmt, _decimals = _format(ind, transform)
    when = (lambda d: period_label(d, ind.freq)) if ind.freq != "D" else i18n.day_month_year
    title = _("{span}: low {low} ({low_when}), high {high} ({high_when})").format(
        span=_span(years), low=fmt(part.min()), low_when=when(part.idxmin()), high=fmt(part.max()), high_when=when(part.idxmax()))
    zero = PAD + hi / spread * (H - 2 * PAD) if lo < 0 < hi else None
    return {"w": W, "h": H, "points": " ".join(f"{x:.1f},{y:.1f}" for x, y in zip(xs, ys)),
            "x": round(float(xs[-1]), 1), "y": round(float(ys[-1]), 1),
            "zero": None if zero is None else round(zero, 1), "title": title}


def context(ind: Indicator, ts: pd.Series, transform: str) -> str | None:
    """"The highest since Feb 2023" when the latest reading is the highest (or lowest) in more than a year,
    as shown (rounded), else "After 9.2% y/y in Aug 2026"."""
    if len(ts) < 2 or ind.freq not in NOTABLE:
        return None
    fmt, decimals = _format(ind, transform)
    shown = ts.round(decimals)
    last, before = shown.iloc[-1], shown.iloc[:-1]
    if last != before.iloc[-1]:
        rising = last > before.iloc[-1]
        reach = before[before >= last] if rising else before[before <= last]
        if reach.empty:
            if len(before) > NOTABLE[ind.freq]:
                text = (_("The highest in the series, which starts in {year}") if rising
                        else _("The lowest in the series, which starts in {year}"))
                return text.format(year=ts.index[0].year)
        elif (ts.index > reach.index[-1]).sum() > NOTABLE[ind.freq]:
            text = _("The highest since {period}") if rising else _("The lowest since {period}")
            return text.format(period=period_label(reach.index[-1], ind.freq))
    return _("After {value} in {period}").format(value=fmt(float(ts.iloc[-2])), period=period_label(ts.index[-2], ind.freq))


def latest_releases(store: Store, items_by_id: dict, registry: dict, events: list[dict], today: pd.Timestamp,
                    days: int = DAYS, limit: int = MAX_CARDS) -> list[dict]:
    """A card for each calendar release of the past `days` days whose figures the site shows, newest first."""
    cards = []
    for e in reversed(events):
        day = e["when"].normalize()
        if not (today - pd.Timedelta(days=days) <= day <= today):
            continue
        shown = [i for i in e.get("ids", []) if (item := items_by_id.get(i)) and item["headline"]
                 and (not e["period"] or item["headline"]["period"] == e["period"])]
        if not shown or shown[0] not in registry:
            continue
        item, ind = items_by_id[shown[0]], registry[shown[0]]
        head = item["headline"]
        ts = headline_series(ind, store.load_series(ind.id), head["transform"])
        others = [items_by_id[i] for i in shown[1:]]
        cards.append({
            "day": i18n.wd_day_mon(day), "release": e["label"], "page": e["page"], "ids": e.get("ids", []),
            "label": item["label"], "value": head["display"], "unit": head["label"], "period": head["period"],
            "flash": item["flash"], "spark": sparkline(ind, ts, head["transform"]),
            "context": context(ind, ts, head["transform"]),
            "others": [f"{o['label']}: {o['headline']['display']} {o['headline']['label']}".strip() for o in others],
        })
        if len(cards) == limit:
            break
    return cards


def tile_extras(store: Store, item: dict, ind: Indicator, fresh: dict) -> dict:
    """What a key-indicator tile adds to the snapshot's item: its sparkline, and the day of its new figures
    when they came out in the past week."""
    head = item["headline"]
    spark = sparkline(ind, headline_series(ind, store.load_series(ind.id), head["transform"]), head["transform"]) if head else None
    new = fresh.get(ind.id)
    return {**item, "spark": spark, "new": _("New · {day}").format(day=i18n.day_mon(new["day"])) if new else None}
