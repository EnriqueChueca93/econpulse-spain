"""The newest figures on the home page: the "Latest releases" cards at the top, a small trend line
(a sparkline) in every key-indicator tile, and the chart of the week.

Each release of the past fortnight in the release calendar (INE, the Seguridad Social, the ECB) gets a card with
its main figure, that figure over the past few years as a sparkline, and a line of context: the highest or
lowest reading in more than a year ("The highest since Feb 2023"), or else the reading before ("After 9.2% y/y
in Aug 2026"). Sparklines are drawn here, as inline SVG, so they need no script; hovering over one gives its
range.

The chart of the week is the past seven days' release whose figure is the highest or lowest in the longest time
(else the newest), drawn over a long span with a line at the latest reading, so the chart shows how far back
it reaches.

Tiles and cards carry when the site last got new or revised figures for them (`changed_times`, from the update
log): a reader who turned on "Since your last visit" sees those that changed since the data they last saw
(static/app.js).
"""

import numpy as np
import pandas as pd

from . import changes, charts, i18n, transforms
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
WEEK_DAYS = 7              # the chart of the week is picked from the releases of the past week
WEEK_YEARS = {"D": 3, "W": 3, "M": 10, "Q": 15, "A": 30}   # and drawn over this span, or further back if need be


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


def extreme(ts: pd.Series, decimals: int) -> tuple[bool, pd.Timestamp | None, int] | None:
    """Whether the latest reading, as shown (rounded), is above or below the one before, and how far back that
    reaches: (rising, the last earlier date at least as high (or low), or None if there is none, the number of
    readings after that date). None when the two latest readings show the same."""
    shown = ts.round(decimals)
    last, before = shown.iloc[-1], shown.iloc[:-1]
    if before.empty or last == before.iloc[-1]:
        return None
    rising = bool(last > before.iloc[-1])
    reach = before[before >= last] if rising else before[before <= last]
    if reach.empty:
        return rising, None, len(before)
    return rising, reach.index[-1], int((ts.index > reach.index[-1]).sum())


def since_text(rising: bool, since: pd.Timestamp | None, ts: pd.Series, freq: str) -> str:
    """"The highest since Feb 2023", or "The lowest in the series, which starts in 1999"."""
    if since is None:
        text = (_("The highest in the series, which starts in {year}") if rising
                else _("The lowest in the series, which starts in {year}"))
        return text.format(year=ts.index[0].year)
    text = _("The highest since {period}") if rising else _("The lowest since {period}")
    return text.format(period=period_label(since, freq if freq in ("M", "Q", "A") else "M"))


def context(ind: Indicator, ts: pd.Series, transform: str) -> str | None:
    """"The highest since Feb 2023" when the latest reading is the highest (or lowest) in more than a year,
    as shown (rounded), else "After 9.2% y/y in Aug 2026"."""
    if len(ts) < 2 or ind.freq not in NOTABLE:
        return None
    fmt, decimals = _format(ind, transform)
    found = extreme(ts, decimals)
    if found and found[2] > NOTABLE[ind.freq]:
        return since_text(found[0], found[1], ts, ind.freq)
    return _("After {value} in {period}").format(value=fmt(float(ts.iloc[-2])), period=period_label(ts.index[-2], ind.freq))


def _shown(event: dict, items_by_id: dict) -> list[str]:
    """The series of a calendar release whose figures the site shows, for the period it brought."""
    return [i for i in event.get("ids", []) if (item := items_by_id.get(i)) and item["headline"]
            and (not event["period"] or item["headline"]["period"] == event["period"])]


def changed_times(store: Store) -> dict[str, str]:
    """When the site last got new or revised figures for each series (UTC, from the update log). Daily
    market prices, which move with every update, are not counted."""
    out: dict[str, str] = {}
    for n in changes.shown_notes(store.load_json("releases", None) or {}):
        if n["kind"] in ("release", "revision") and n["at"] > out.get(n["id"], ""):
            out[n["id"]] = n["at"]
    return out


def latest_releases(store: Store, items_by_id: dict, registry: dict, events: list[dict], today: pd.Timestamp,
                    days: int = DAYS, limit: int = MAX_CARDS, changed: dict | None = None) -> list[dict]:
    """A card for each calendar release of the past `days` days whose figures the site shows, newest first."""
    cards = []
    for e in reversed(events):
        day = e["when"].normalize()
        if not (today - pd.Timedelta(days=days) <= day <= today):
            continue
        shown = _shown(e, items_by_id)
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
            "changed": max((changed[i] for i in shown if i in changed), default=None) if changed else None,
        })
        if len(cards) == limit:
            break
    return cards


def tile_extras(store: Store, item: dict, ind: Indicator, fresh: dict, changed: dict | None = None) -> dict:
    """What a key-indicator tile adds to the snapshot's item: its sparkline, the day of its new figures
    when they came out in the past week, and when the site last got new or revised figures for it."""
    head = item["headline"]
    spark = sparkline(ind, headline_series(ind, store.load_series(ind.id), head["transform"]), head["transform"]) if head else None
    new = fresh.get(ind.id)
    return {**item, "spark": spark, "new": _("New · {day}").format(day=i18n.day_mon(new["day"])) if new else None,
            "changed": (changed or {}).get(ind.id)}


def reach_years(ind: Indicator, ts: pd.Series, transform: str) -> float:
    """How many years back the latest reading, as shown, is the highest or lowest; 0 unless more than a year
    (or the series has no such reading)."""
    if len(ts) < 2 or ind.freq not in NOTABLE:
        return 0.0
    _fmt, decimals = _format(ind, transform)
    found = extreme(ts, decimals)
    if not found or found[2] <= NOTABLE[ind.freq]:
        return 0.0
    return found[2] / transforms.PERIODS_PER_YEAR[ind.freq]


# What a chart's figure is, by transform (the frequency fills "previous ...").
_WHAT = {
    "yoy": "% change on a year earlier",
    "pop": "% change on the previous {period}",
    "diff": "Change on the previous {period}, {unit}",
    "diff_yoy": "Change on a year earlier, {unit}",
    "ann3m": "% change over three months, annualised",
    "saar": "% change on the previous quarter, annualised",
    "sum_1y": "Total over the past year, {unit}",
    "avg_1y": "Average over the past year, {unit}",
}
_PERIOD_WORDS = {"D": "day", "M": "month", "Q": "quarter", "A": "year"}


def subtitle(ind: Indicator, transform: str) -> str:
    """What the chart's figure is: "% change on a year earlier", "Change on the previous month, thousands"..."""
    sa = transform.startswith(transforms.SA_PREFIX)
    base = transform[len(transforms.SA_PREFIX):] if sa else transform
    unit = i18n.maybe(ind.unit) if ind.unit else ""
    if base in _WHAT:
        what = _WHAT[base].replace("{period}", _PERIOD_WORDS.get(ind.freq, "month"))
        text = _(what).format(unit=unit)
    else:
        text = unit[:1].upper() + unit[1:]
    return _("{what}, seasonally adjusted by Macroscope").format(what=text) if sa else text


# The Covid collapse and rebound, base effects included: y/y changes compare with the Omicron winter until March 2023.
COVID = (pd.Timestamp("2020-03-01"), pd.Timestamp("2023-03-31"))
WILD = 2       # a Covid-era reading more than twice the range of the rest of the chart beyond it is cut


def calm_start(ts: pd.Series, start: pd.Timestamp, keep: pd.Timestamp) -> pd.Timestamp:
    """The chart's start moved past Covid-era readings far outside the range of the rest of the chart (`WILD`
    times that range beyond it: tourist spending was up 1,800% on a year earlier in 2021), which would flatten
    everything else into a line; but never past `keep`, the earliest reading the chart must show. Real episodes
    stay: the 2022 surge in inflation and producer prices is well within that."""
    shown = ts[ts.index >= start]
    covid = (shown.index >= COVID[0]) & (shown.index <= COVID[1])
    rest = shown[~covid]
    if len(rest) < 6:
        return start
    lo, hi = float(rest.min()), float(rest.max())
    width = (hi - lo) or 1.0
    wild = shown[covid & (shown.index < keep) & ((shown > hi + WILD * width) | (shown < lo - WILD * width))]
    if wild.empty:
        return start
    after = ts.index[ts.index > wild.index[-1]]
    return max(start, after[0]) if len(after) else start


def chart_of_the_week(store: Store, items_by_id: dict, registry: dict, events: list[dict], today: pd.Timestamp,
                      days: int = WEEK_DAYS) -> dict | None:
    """The chart spec (id "week") for the past week's release whose figure is the highest or lowest in the
    longest time, else the newest; with the release's name, day and page for the section around it."""
    best = None
    for e in events:
        day = e["when"].normalize()
        if not (today - pd.Timedelta(days=days) <= day <= today):
            continue
        shown = _shown(e, items_by_id)
        if not shown or shown[0] not in registry:
            continue
        item, ind = items_by_id[shown[0]], registry[shown[0]]
        transform = item["headline"]["transform"]
        ts = headline_series(ind, store.load_series(ind.id), transform)
        if len(ts) < 3:
            continue
        # A tie goes to the newer release, then to the series id: the same pick in both languages.
        score = (reach_years(ind, ts, transform), e["when"], ind.id)
        if best is None or score > best[0]:
            best = (score, e, item, ind, ts)
    if best is None:
        return None
    (reach, when, _id), e, item, ind, ts = best
    head = item["headline"]
    transform = head["transform"]
    _fmt, decimals = _format(ind, transform)
    start = ts.index[-1] - pd.DateOffset(years=WEEK_YEARS.get(ind.freq, 10))
    keep = ts.index[-1] - pd.DateOffset(years=2)   # a recent spike is the story: never cut
    found = extreme(ts, decimals)
    if reach and found and found[1] is None:       # the highest in the series: the whole series
        start = keep = ts.index[0]
    elif reach and found:                          # far enough back to show the earlier reading it passed
        start, keep = min(start, found[1] - pd.DateOffset(years=2)), min(keep, found[1])
    start = calm_start(ts, start, keep)
    base =transform[len(transforms.SA_PREFIX):] if transform.startswith(transforms.SA_PREFIX) else transform
    bars = transform in transforms.DIFF_TRANSFORMS or base == "pop"
    spec = charts.build_chart({
        "id": "week", "kind": "bar" if bars else "line", "decimals": decimals,
        "unit": "%" if transform in transforms.PERCENT_TRANSFORMS else ind.unit,
        "signed": bars or base in ("yoy", "ann3m", "saar"), "start": start.strftime("%Y-%m-%d"),
        "series": [(ind.id, transform, "")],
    }, registry, store)
    if spec is None:
        return None
    value = f"{head['display']} {head['label']}".strip() + (_(" (flash estimate)") if item["flash"] else "")
    # The words go in after build_chart, which would look them up in the catalogue: they are in the page's
    # language already.
    spec.update({
        "title": item["label"], "subtitle": subtitle(ind, transform),
        "ref_lines": [{"y": round(float(ts.iloc[-1]), 4), "label": head["period"]}],
        "reading": i18n.capital(_("{period}: {value}. {context}.").format(
            period=head["period"], value=value, context=context(ind, ts, transform) or "")),
        "link": e["page"],
    })
    spec["series"][0]["name"] = item["label"]
    return {"spec": spec, "release": e["label"], "day": i18n.wd_day_mon(when.normalize()), "ids": e.get("ids", [])}
