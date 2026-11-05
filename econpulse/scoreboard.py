"""Spain in context, on the home page: a scoreboard against its peers and what forecasters expect.

The scoreboard puts Spain beside the euro area, Germany, France, Italy and Portugal on seven measures (from the
International page's series, econpulse/peers.py), with Spain's place among the five countries and a dot strip
of where it stands: the countries as grey dots, Spain in blue, the euro area as a tick.

The forecasts are the average of the forecasters followed on the Analysis page (econpulse/forecasts.py) for
growth and inflation this year and next, AI-checked figures only, each with a dot strip of the forecasters
around their average; Macroscope's own estimate of this year's growth is marked in blue.
"""

import pandas as pd

from . import forecasts, i18n, peers
from .forecasts import Forecaster
from .i18n import _
from .snapshot import fmt_change, fmt_value, period_label
from .tables import DASH, Data

COUNTRIES = ["es", "ea", "de", "fr", "it", "pt"]
# (measure, label, note, signed, the word that ranks Spain)
MEASURES = [("gdp", "GDP growth", "y/y", True, "fastest"),
            ("recovery", "GDP since the end of 2019", "%", True, "largest rise"),
            ("hicp", "HICP inflation", "%", False, "highest"),
            ("core", "Core HICP inflation", "%", False, "highest"),
            ("unemp", "Unemployment rate", "%", False, "highest"),
            ("y10", "10-year yield", "%, monthly avg.", False, "highest"),
            ("debt", "Government debt", "% of GDP", False, "highest")]
PLACES = {"fastest": ("the fastest of {n}", "{rank} fastest of {n}"),
          "highest": ("the highest of {n}", "{rank} highest of {n}"),
          "largest rise": ("the largest rise of {n}", "{rank} largest rise of {n}")}
W, H, PAD, R = 160, 32, 7, 4.5       # a dot strip's drawing box and dot radius, in pixels


def strip(points: list[dict], ticks: list[dict] = ()) -> dict | None:
    """Dots on one line, scaled to their range: each point {"value", "title", "kind"} (kind "other" or "main");
    ticks {"value", "title"} mark a benchmark. Dots that would overlap are stacked up and down."""
    values = [p["value"] for p in points] + [t["value"] for t in ticks]
    if len(points) < 2:
        return None
    lo, hi = min(values), max(values)
    spread = (hi - lo) or 1.0

    def x(v):
        return round(PAD + (v - lo) / spread * (W - 2 * PAD), 1)

    dots, placed = [], []
    for p in sorted(points, key=lambda p: (p["kind"] == "main", p["value"])):      # Spain drawn last, on top
        px = x(p["value"])
        near = sum(abs(px - q) < 2 * R for q in placed)
        offset = (near + 1) // 2 * (2 * R - 1) * (1 if near % 2 else -1)
        placed.append(px)
        dots.append({"x": px, "y": round(H / 2 + offset, 1), "r": R + (1 if p["kind"] == "main" else 0),
                     "kind": p["kind"], "title": p["title"]})
    dots.sort(key=lambda d: d["kind"] == "main")
    titles = [t["title"] for t in ticks] + [d["title"] for d in reversed(dots)]
    return {"w": W, "h": H, "dots": dots, "ticks": [{"x": x(t["value"]), "title": t["title"]} for t in ticks],
            "label": "; ".join(titles)}


def _rank(word: str, values: dict[str, float]) -> str | None:
    countries = {k: v for k, v in values.items() if k != "ea"}
    if "es" not in countries or len(countries) < 3:
        return None
    rank = 1 + sum(v > countries["es"] for k, v in countries.items() if k != "es")
    first, other = PLACES[word]
    return _(first if rank == 1 else other).format(rank=peers._ordinal(rank), n=len(countries))


def _reading(data: Data, measure: str, slug: str) -> tuple[float, str] | None:
    """A country's latest value on a measure, and the period it is for."""
    if measure == "recovery":
        found = peers.since_2019(data, slug)
        return None if found is None else (found[0], period_label(found[1], "Q"))
    if measure == "debt":
        v = peers.weo(data, "debt", slug, peers.ppp_year())
        return None if v is None else (v, str(peers.ppp_year()))
    found = peers._latest(data, measure, slug)
    return None if found is None else (found[0], period_label(found[1], found[2]))


def peer_table(data: Data) -> dict | None:
    """Spain beside its peers: a row per measure, a column per country, Spain's place and a dot strip."""
    names = {slug: _(peers.LABELS[slug]) for slug in COUNTRIES}
    rows = []
    for measure, label, note, signed, word in MEASURES:
        found = {slug: r for slug in COUNTRIES if (r := _reading(data, measure, slug))}
        if "es" not in found or len(found) < 3:
            continue
        period = found["es"][1]
        unit = "%"

        def show(v):
            return fmt_change(v, unit, 1) if signed else fmt_value(v, unit, 1 if measure != "y10" else 2)

        cells = []
        for slug in COUNTRIES:
            if slug not in found:
                cells.append({"text": DASH, "period": None, "spain": slug == "es"})
                continue
            v, when = found[slug]
            cells.append({"text": show(v), "period": when if when != period else None, "spain": slug == "es"})
        points = [{"value": found[s][0], "kind": "main" if s == "es" else "other",
                   "title": f"{names[s]}: {show(found[s][0])} ({found[s][1]})"} for s in found if s != "ea"]
        ticks = [{"value": found["ea"][0], "title": f"{names['ea']}: {show(found['ea'][0])} ({found['ea'][1]})"}] \
            if "ea" in found else []
        rows.append({"label": _(label), "note": i18n.figures(note) if note in ("%", "y/y") else _(note), "period": period,
                     "cells": cells, "place": _rank(word, {s: v[0] for s, v in found.items()}),
                     "strip": strip(points, ticks)})
    if not rows:
        return None
    return {"countries": [names[s] for s in COUNTRIES], "rows": rows, "edition": peers.weo_edition(data),
            "debt_year": peers.ppp_year()}


def _name(f: Forecaster) -> str:
    """"Banco de España, Oct 2026"."""
    when = i18n.month_year(f.published) if f.published else ""
    return f"{_(f.name)}, {when}" if when else _(f.name)


def _short(f: Forecaster) -> str:
    """"BdE (Oct 2026)", for the list of forecasters."""
    when = i18n.month_year(f.published) if f.published else ""
    return f"{i18n.maybe(f.short)} ({when})" if when else i18n.maybe(f.short)


def outlook(data: Data) -> dict | None:
    """The forecasters' average for growth and inflation, this year and next, with each forecaster on a strip."""
    this, nxt = forecasts.years()
    fs = [f for f in forecasts.forecasters(data) if f.counts]
    own = forecasts.gdp_this_year(data, this)
    boxes = []
    for measure, label in (("gdp", "GDP growth"), ("inflation", "Inflation")):
        for year in (this, nxt):
            avg, vals = forecasts._average(fs, year, measure)
            if avg is None or len(vals) < 2:
                continue
            points = [{"value": v, "kind": "other", "title": f"{_name(f)}: {fmt_value(v, '%', 1)}"}
                      for f in fs if (v := f.value(year, measure)) is not None]
            extra = None
            if measure == "gdp" and year == this and own is not None:
                points.append({"value": own["value"], "kind": "main",
                               "title": _("Macroscope: {value}, from INE to {quarter} and the nowcast").format(
                                   value=fmt_value(own["value"], "%", 1), quarter=period_label(own["through"], "Q"))})
                extra = _("Macroscope's estimate: {value}").format(value=fmt_value(own["value"], "%", 1))
            boxes.append({"label": _("{measure}, {year}").format(measure=_(label), year=year),
                          "value": fmt_value(avg, "%", 1),
                          "sub": forecasts._spread(vals), "extra": extra,
                          "strip": strip(points, [{"value": avg, "title": _("Average: {value}").format(
                              value=fmt_value(avg, "%", 1))}])})
    if not boxes:
        return None
    names = sorted({_short(f) for f in fs}, key=lambda n: n.lower())
    return {"boxes": boxes, "who": forecasts._join(names)}
