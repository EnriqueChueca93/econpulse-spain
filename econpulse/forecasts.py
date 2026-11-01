"""What forecasters expect for Spain this year and next, shown on the Analysis page.

Two kinds of source:
    automatic  the OECD Economic Outlook and the European Commission (AMECO), fetched like
               any indicator (fc_* in indicators.yaml); the latest years are the forecasts
    by hand    everyone else (Banco de España, AIReF, FUNCAS, the government, the IMF), in
               forecasts.yaml, since none of them offers the figures through an API

Next to them, EconPulse's own figure for this year's GDP: the quarters INE has published
plus the nowcast for the quarter still to come.
"""

import re
from dataclasses import dataclass, field
from datetime import date

import pandas as pd
import yaml

from . import analytics, transforms
from .config import FORECASTS_FILE
from .snapshot import fmt_value, period_label
from .sources.base import madrid_today
from .tables import DASH, Data

MEASURES = [("gdp", "GDP growth", "real, %"), ("inflation", "Inflation", "annual avg., %"),
            ("unemployment", "Unemployment", "% of labour force"), ("balance", "Budget balance", "% of GDP")]
GROUPS = [("spain", "In Spain"), ("international", "International organisations")]
EC_FORECAST_PAGE = "https://economy-finance.ec.europa.eu/economic-forecast-and-surveys/economic-forecasts_en"


@dataclass
class Forecaster:
    id: str
    name: str
    short: str
    group: str
    url: str | None
    published: date | None
    inflation: str = "CPI"          # what the inflation figure measures: HICP or CPI
    note: str = ""
    values: dict[int, dict[str, float]] = field(default_factory=dict)

    def value(self, year: int, measure: str) -> float | None:
        return self.values.get(year, {}).get(measure)


# Fetched forecasters: measure -> (indicator, transform giving the forecast figure).
AUTOMATIC = [
    {"id": "oecd", "name": "OECD Economic Outlook", "short": "OECD", "inflation": "HICP",
     "series": {"gdp": ("fc_oecd_gdp", "level"), "inflation": ("fc_oecd_inflation", "level"),
                "unemployment": ("fc_oecd_unemployment", "level"), "balance": ("fc_oecd_balance", "level")}},
    {"id": "ec", "name": "European Commission", "short": "Commission", "inflation": "HICP",
     "series": {"gdp": ("fc_ec_gdp_volume", "yoy"), "inflation": ("fc_ec_hicp_index", "yoy"),
                "unemployment": ("fc_ec_unemployment", "level"), "balance": ("fc_ec_balance", "level")}},
]
INDICATORS = [ind for f in AUTOMATIC for ind, _ in f["series"].values()]


def eo_month(edition: str) -> date | None:
    """When an OECD Economic Outlook came out: No. 119 in June 2026, then every six months."""
    m = re.search(r"(\d+)\s*$", edition or "")
    if not m:
        return None
    steps = int(m[1]) - 119
    return date(2026 + steps // 2, 6 if steps % 2 == 0 else 12, 1)


def load_manual(path=None) -> list[Forecaster]:
    raw = yaml.safe_load((path or FORECASTS_FILE).read_text(encoding="utf-8")) or {}
    out = []
    for f in raw.get("forecasters", []):
        values = {int(y): {k: float(v) for k, v in (vals or {}).items() if v is not None}
                  for y, vals in (f.get("values") or {}).items()}
        out.append(Forecaster(id=f["id"], name=f["name"], short=f.get("short", f["name"]), group=f["group"],
                              url=f.get("url"), published=f.get("published"), inflation=f.get("inflation", "CPI"),
                              note=f.get("note", ""), values=values))
    return out


def _automatic(data: Data) -> list[Forecaster]:
    catalog = data.store.load_catalog()
    out = []
    for spec in AUTOMATIC:
        values: dict[int, dict[str, float]] = {}
        for measure, (ind_id, transform) in spec["series"].items():
            raw = data.store.load_series(ind_id)
            if raw is None or ind_id not in data.by_id:
                continue
            s = transforms.apply(transform, raw, "A").dropna()
            for d, v in s.items():
                values.setdefault(d.year, {})[measure] = round(float(v), 2)
        if not values:
            continue
        first = spec["series"]["gdp"][0]
        entry = catalog.get(first, {})
        if spec["id"] == "oecd":
            published = eo_month(entry.get("edition", ""))
            url = data.by_id[first].source_url() if first in data.by_id else None
        else:
            updated = entry.get("source_updated")
            published = date.fromisoformat(updated) if updated else None
            url = EC_FORECAST_PAGE
        out.append(Forecaster(id=spec["id"], name=spec["name"], short=spec["short"], group="international",
                              url=url, published=published, inflation=spec["inflation"], values=values))
    return out


def forecasters(data: Data) -> list[Forecaster]:
    return analytics._cached(data, "forecasters", lambda: _automatic(data) + load_manual())


def years(today: date | None = None) -> tuple[int, int]:
    this = (today or madrid_today()).year
    return this, this + 1


def gdp_this_year(data: Data, year: int) -> dict | None:
    """Annual GDP growth for ``year`` from the quarters INE has published plus the nowcast for the
    fourth, and the growth if the fourth quarter were flat (what the year has already 'banked')."""
    raw = data.store.load_series("gdp")
    n = analytics.nowcast(data)
    if raw is None or n is None:
        return None
    q = transforms.regular(raw.sort_index(), "Q")
    this = q[q.index.year == year].dropna()
    before = q[q.index.year == year - 1].dropna()
    q4 = pd.Timestamp(year, 10, 1)
    if len(before) != 4 or len(this) != 3 or n["quarter"] != q4:
        return None
    last = float(this.iloc[-1])
    with_nowcast = (this.sum() + last * (1 + n["value"] / 100)) / before.sum() * 100 - 100
    flat = (this.sum() + last) / before.sum() * 100 - 100
    return {"value": float(with_nowcast), "flat": float(flat), "nowcast": n["value"], "through": this.index[-1]}


def _month(d: date | None) -> str:
    return f"{d:%b %Y}" if d else ""


def _cell(v: float | None) -> str:
    return DASH if v is None else fmt_value(v, "%", 1)


def _average(fs: list[Forecaster], year: int, measure: str) -> tuple[float | None, list[float]]:
    vals = [v for f in fs if (v := f.value(year, measure)) is not None]
    return (sum(vals) / len(vals) if vals else None), vals


def _ordered(fs: list[Forecaster], year: int) -> list[tuple[str, list[Forecaster]]]:
    """Forecasters with figures for ``year``, by group, newest edition first."""
    out = []
    for group, title in GROUPS:
        members = [f for f in fs if f.group == group and f.values.get(year)]
        members.sort(key=lambda f: f.published or date.min, reverse=True)
        if members:
            out.append((title, members))
    return out


def forecast_table(data: Data, year: int) -> dict | None:
    fs = forecasters(data)
    groups = _ordered(fs, year)
    if not groups:
        return None
    rows = []
    shown = []
    for title, members in groups:
        rows.append({"heading": True, "label": title})
        for f in members:
            shown.append(f)
            rows.append({"heading": False, "label": f.name, "label_es": "", "indent": 0,
                         "period_note": _month(f.published), "url": f.url,
                         "cells": [_cell(f.value(year, m)) for m, *_ in MEASURES]})
    rows.append({"heading": True, "label": "Summary"})
    rows.append({"heading": False, "label": "Average of the forecasts above", "label_es": "", "indent": 0,
                 "period_note": "", "url": None, "highlight": True,
                 "cells": [_cell(_average(shown, year, m)[0]) for m, *_ in MEASURES]})
    own = gdp_this_year(data, year)
    if own is not None:
        rows.append({"heading": False, "label": "EconPulse: INE's quarters + nowcast", "label_es": "", "indent": 0,
                     "period_note": f"Q4 {_fmt_growth(own['nowcast'])}", "url": None,
                     "cells": [_cell(own["value"]), DASH, DASH, DASH]})
    hicp = [f.short for f in shown if f.inflation == "HICP" and f.value(year, "inflation") is not None]
    cpi = [f.short for f in shown if f.inflation != "HICP" and f.value(year, "inflation") is not None]
    measures = []
    if hicp:
        measures.append(f"the HICP for {_join(hicp)}")
    if cpi:
        measures.append(f"the CPI for {_join(cpi)}")
    notes = [f"Inflation is {' and '.join(measures)}." if measures else "",
             "A budget balance below zero is a deficit.",
             *dict.fromkeys(f.note for f in shown if f.note)]
    return {"title": "Forecaster", "caption": f"Forecasts for {year}", "through": None,
            "columns": [label for _, label, _ in MEASURES], "column_notes": [note for *_, note in MEASURES],
            "rows": rows, "note": " ".join(n for n in notes if n)}


def _fmt_growth(v: float) -> str:
    return analytics._fmt_signed(v, 1, "%")


def _join(names: list[str]) -> str:
    return names[0] if len(names) == 1 else ", ".join(names[:-1]) + " and " + names[-1]


def forecast_facts(data: Data, today: date | None = None) -> list[dict]:
    this, nxt = years(today)
    fs = forecasters(data)
    facts = []
    for year in (this, nxt):
        avg, vals = _average(fs, year, "gdp")
        if avg is not None:
            facts.append({"label": f"GDP growth forecast, {year}", "value": fmt_value(avg, "%", 1),
                          "sub": f"average of {len(vals)}; range {fmt_value(min(vals), '%', 1)} to {fmt_value(max(vals), '%', 1)}"})
    own = gdp_this_year(data, this)
    if own is not None:
        facts.append({"label": f"EconPulse, {this} GDP", "value": fmt_value(own["value"], "%", 1),
                      "sub": f"INE to {period_label(own['through'], 'Q')}, then the Q4 nowcast"})
    avg, vals = _average(fs, this, "inflation")
    if avg is not None:
        facts.append({"label": f"Inflation forecast, {this}", "value": fmt_value(avg, "%", 1),
                      "sub": f"average of {len(vals)}; range {fmt_value(min(vals), '%', 1)} to {fmt_value(max(vals), '%', 1)}"})
    return facts


def forecast_callout(data: Data, today: date | None = None) -> str | None:
    this, _ = years(today)
    own = gdp_this_year(data, this)
    if own is None:
        return None
    return (f"With three quarters published, {this} is largely decided: even with no growth at all in the fourth "
            f"quarter, GDP would grow {fmt_value(own['flat'], '%', 1)} on {this - 1}. The forecasts differ mainly "
            f"in what they expect for {this + 1}.")


def forecast_chart(data: Data, today: date | None = None) -> dict | None:
    this, nxt = years(today)
    fs = [f for _, members in _ordered(forecasters(data), this) for f in members]
    if len(fs) < 2:
        return None
    labels = [f.short for f in fs] + ["Average"]
    series = []
    for year in (this, nxt):
        ys = [f.value(year, "gdp") for f in fs] + [_average(fs, year, "gdp")[0]]
        series.append({"name": str(year), "x": labels, "y": [None if v is None else round(v, 2) for v in ys]})
    own = gdp_this_year(data, this)
    if own is not None:
        for s in series:
            s["x"] = s["x"] + ["EconPulse"]
        series[0]["y"].append(round(own["value"], 2))
        series[1]["y"].append(None)
    return {"id": "forecasts", "title": "GDP growth forecasts", "subtitle": f"Real GDP, % change on a year earlier, {this} and {nxt}",
            "kind": "bar", "x_kind": "category", "x_title": "Forecaster", "unit": "%", "decimals": 1, "freq": None,
            "series": series,
            "ref_lines": [], "source": "Forecasters' publications (see table); EconPulse nowcast"}
