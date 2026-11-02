"""Data surprises: did the latest figures come in above or below what was expected?

Analysts' forecasts for Spanish releases are not freely available, so each figure is
compared with a simple statistical forecast instead: an AR(1) model (the next value
depends on the last one), fitted only on the figures before it. The surprise is the gap in
units of the model's typical error, for the same indicators as the composites. Each index
averages every surprise of the past four months, the newest at full weight and older ones
a quarter less per month, so news keeps counting for a while after it is released.
Macroscope calculation, labelled as such on the page.
"""

import numpy as np
import pandas as pd

from . import analytics, i18n, transforms
from .i18n import _
from .analytics import ACTIVITY, COVID, HISTORY_START, INFLATION, Z_CLIP, Component, _fmt_signed
from .snapshot import period_label
from .tables import Data

MIN_FIT = 36        # pairs of observations needed before the model makes forecasts
CHART_START = pd.Timestamp("2015-01-01")
INDEXES = {"activity": (ACTIVITY, "Activity"), "inflation": (INFLATION, "Inflation")}
# The composites' labels describe their smoothed readings; surprises use each period's own figure.
LABELS = {"unemployment_monthly": "Unemployment rate, monthly change"}


def one_step_forecasts(s: pd.Series) -> pd.Series:
    """For each period, the AR(1) forecast made from the observations before it.

    ``s`` is on a gap-free calendar. Pairs (last value, value) touching the Covid years are
    left out of the fits, as in the composites' norms."""
    s = s.astype(float)
    prev = s.shift(1)
    covid = pd.Series(s.index.year.isin(COVID), index=s.index)
    ok = s.notna() & prev.notna() & ~covid & ~covid.shift(1, fill_value=False)
    x, y, k = prev.where(ok, 0.0), s.where(ok, 0.0), ok.astype(float)
    # Running sums of the pairs strictly before each period: least squares without refitting.
    n, sx, sy = k.cumsum().shift(1), x.cumsum().shift(1), y.cumsum().shift(1)
    sxx, sxy = (x * x).cumsum().shift(1), (x * y).cumsum().shift(1)
    denom = n * sxx - sx ** 2
    b = (n * sxy - sx * sy) / denom.replace(0, np.nan)
    a = (sy - b * sx) / n
    return (a + b * prev).where(n >= MIN_FIT)


def _component(data: Data, c: Component) -> dict | None:
    s = analytics._component_series(data, c, smooth=False)
    if s is None or len(s) < MIN_FIT + 12:
        return None
    freq = data.by_id[c.id].freq
    s = transforms.regular(s, freq)
    forecast = one_step_forecasts(s)
    error = (s - forecast).dropna()
    hist = error[(error.index >= HISTORY_START) & ~error.index.year.isin(COVID)]
    if len(hist) < 12:
        return None
    spread = float(1.4826 * (hist - hist.median()).abs().median()) or float(hist.std())
    if not spread:
        return None
    z = (c.sign * error / spread).clip(-Z_CLIP, Z_CLIP)
    last = error.index[-1]
    return {"component": c, "freq": freq, "z_series": z, "date": last, "value": float(s[last]),
            "forecast": float(forecast[last]), "z": float(z.iloc[-1])}


def accumulate(scores: dict[str, pd.Series], end: pd.Timestamp) -> pd.Series:
    """Monthly weighted average of all the surprises from the past four months (weights 1, ¾, ½, ¼)."""
    months = pd.date_range(HISTORY_START, end, freq="MS")
    weighted = pd.Series(0.0, index=months)
    weights = pd.Series(0.0, index=months)
    for z in scores.values():
        z = z.groupby(z.index).last().reindex(months)
        for lag in range(4):
            past = z.shift(lag)
            use = past.notna()
            weighted[use] += (1 - lag / 4) * past[use]
            weights[use] += 1 - lag / 4
    return (weighted / weights.replace(0, np.nan)).dropna()


def surprise_index(data: Data, key: str) -> dict | None:
    components, _ = INDEXES[key]

    def compute():
        rows = [r for c in components if (r := _component(data, c))]
        if not rows:
            return None
        zs = {r["component"].id: analytics._monthly(r["z_series"], r["freq"]) for r in rows}
        end = max(z.index[-1] for z in zs.values())
        return {"series": accumulate(zs, end), "rows": rows, "end": end}

    return analytics._cached(data, f"surprise:{key}", compute)


def _describe(z: float) -> str:
    if z >= 0.25:
        return "above expectations"
    if z <= -0.25:
        return "below expectations"
    return "in line with expectations"


def _age(row: dict, end: pd.Timestamp) -> int:
    """Months between a figure (quarterly ones sit on their quarter's last month) and the index's end."""
    placed = row["date"] + pd.DateOffset(months=2 if row["freq"] == "Q" else 0)
    return analytics._months_between(placed, end)


def surprise_facts(data: Data) -> list[dict]:
    facts = []
    for key, label in (("activity", "Activity data vs forecasts"), ("inflation", "Inflation data vs forecasts")):
        idx = surprise_index(data, key)
        if idx is None or idx["series"].empty:
            continue
        z = float(idx["series"].iloc[-1])
        recent = [r for r in idx["rows"] if _age(r, idx["end"]) < 4]  # latest figures still in the index
        above = sum(r["z"] > 0 for r in recent)
        facts.append({"label": _(label), "value": _fmt_signed(z),
                      "sub": _("{verdict}, {month}; {above} of {total} recent figures above").format(
                          verdict=_(_describe(z)), month=i18n.month_year(idx["end"]), above=above, total=len(recent))})
    return facts


def surprise_table(data: Data, key: str) -> dict | None:
    idx = surprise_index(data, key)
    if idx is None:
        return None
    _, title = INDEXES[key]
    rows = []
    for r in idx["rows"]:
        c = r["component"]
        ind = data.by_id[c.id]
        show = lambda v: analytics._component_display(data, {"component": c, "value": v})  # noqa: E731
        rows.append({"heading": False, "label": LABELS.get(c.id, c.label.split(" (")[0]), "label_es": ind.label_es, "indent": 0,
                     "period_note": period_label(r["date"], r["freq"]), "url": ind.source_url(),
                     "cells": [show(r["value"]), show(r["forecast"]), _fmt_signed(r["z"], 1)]})
    end = period_label(idx["end"], "M")
    return {"title": title, "caption": f"Latest figures against the statistical forecast · index for {end}",
            "through": end, "columns": ["Actual", "Forecast", "Surprise"], "rows": rows,
            "note": ("Forecast: what an AR(1) model fitted on the earlier figures expected. Surprise: the gap in "
                     "units of the model's typical error since 2013 (Covid years left out); "
                     + ("positive means hotter inflation." if key == "inflation" else
                        "positive means a stronger economy (for unemployment, a smaller rise than expected)."))}


def surprise_chart(data: Data) -> dict | None:
    series = []
    for key, (_, name) in INDEXES.items():
        idx = surprise_index(data, key)
        if idx is not None:
            s = idx["series"][idx["series"].index >= CHART_START].round(3)
            series.append({"name": name, "x": [d.strftime("%Y-%m-%d") for d in s.index], "y": s.tolist()})
    if not series:
        return None
    return {"id": "surprises", "title": "Surprise indexes", "kind": "line", "unit": "", "decimals": 2,
            "subtitle": "Average surprise over the past four months, newest weighted most; above 0 = above forecast",
            "signed": True, "freq": "M", "series": series, "ref_lines": [],
            "source": "Macroscope calculation from INE, Eurostat, Seguridad Social, Red Eléctrica"}
