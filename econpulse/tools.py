"""Data for the interactive tools (site/tools.html). The browser does the arithmetic
(static/tools.js), so here we only gather and align the series each tool needs.

    trend     levels of activity, jobs and prices, to compare with their pre-COVID trend
    taylor    monthly inflation, unemployment and its trend, and the ECB rate
    rates     daily Spanish, German and AAA euro-area yields, to split a move in Spain's 10-year
"""

import pandas as pd

from . import analytics, transforms
from .tables import Data

TREND_START = pd.Timestamp("2005-01-01")
RATES_START = pd.Timestamp("2010-01-01")

# (indicator, transform, label): levels, seasonally adjusted where the source does not.
TREND_SERIES = [
    ("gdp", "level", "Real GDP"),
    ("consumption_households", "level", "Household consumption"),
    ("investment", "level", "Fixed investment"),
    ("exports", "level", "Exports"),
    ("jobs_fte", "level", "Employment (full-time equivalent jobs)"),
    ("afiliados", "sa_level", "Social Security registrations (SA)"),
    ("industrial_production", "level", "Industrial production"),
    ("retail_sales", "level", "Retail sales (real)"),
    ("cpi_index", "sa_level", "Consumer prices (SA)"),
    ("house_prices", "level", "House prices"),
]


def _iso(index) -> list[str]:
    return [d.strftime("%Y-%m-%d") for d in index]


def trend_data(data: Data) -> list[dict]:
    out = []
    for ind_id, transform, label in TREND_SERIES:
        raw = data.store.load_series(ind_id)
        if raw is None or ind_id not in data.by_id:
            continue
        freq = data.by_id[ind_id].freq
        try:
            s = transforms.apply(transform, raw, freq).dropna()
        except ValueError:
            continue
        s = s[s.index >= TREND_START]
        if len(s) < 24:
            continue
        out.append({"id": ind_id, "label": label, "freq": freq, "x": _iso(s.index), "y": s.round(4).tolist()})
    return out


def taylor_data(data: Data) -> dict | None:
    t = analytics.taylor(data)
    if t is None:
        return None
    out = {"r_star": analytics.R_STAR, "target": analytics.TARGET}
    for key, core_id in (("ea", "hicp_core_euro_area"), ("es", "hicp_core")):
        df = t[key].copy()
        core = data.raw(core_id)
        df["core"] = core.reindex(df.index) if core is not None else None
        df = df[df.index >= pd.Timestamp("2002-01-01")]
        out[key] = {"x": _iso(df.index), "inflation": df["inflation"].round(3).tolist(),
                    "core": [None if pd.isna(v) else round(float(v), 3) for v in df["core"]],
                    "unemployment": df["unemployment"].round(3).tolist(), "trend": df["trend"].round(3).tolist()}
    if t["dfr"] is not None:
        d = t["dfr"][t["dfr"].index >= pd.Timestamp("2002-01-01")]
        out["dfr"] = {"x": _iso(d.index), "y": d.round(3).tolist()}
    return out


def rates_data(data: Data) -> dict | None:
    cols = {"es10": "es_10y", "de10": "de_10y", "aaa1": "aaa_1y", "aaa10": "aaa_10y"}
    frames = {}
    for name, ind_id in cols.items():
        s = data.raw(ind_id)
        if s is None:
            return None
        frames[name] = s
    df = pd.DataFrame(frames).dropna()
    df = df[df.index >= RATES_START]
    if df.empty:
        return None
    return {"x": _iso(df.index), **{name: df[name].round(4).tolist() for name in cols}}


def tools_data(data: Data) -> dict:
    return {"trend": trend_data(data), "taylor": taylor_data(data), "rates": rates_data(data)}
