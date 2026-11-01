"""Underlying inflation from the spread of price changes across the HICP basket (EconPulse calculation).

Eurostat publishes the harmonised index for about 290 detailed items (ECOICOP ver. 2
subclasses, five digits; around 180-200 have data for Spain) with each year's weights.
For every month we take each item's annual rate of change and compute, as the ECB does
for the euro area:
    median   the weighted median: half the basket, by weight, rose faster and half slower
    trim10   the mean after dropping the 5% of the weight with the highest rates and the 5% lowest
    trim30   the same, dropping 15% at each end
    above2   the share of the basket, by weight, with annual inflation above 2%
    above5   ... above 5%
Key is "<geo>/<measure>", geo ES (Spain) or EA (the euro area). The "median" series also
records the latest month's distribution and the items rising fastest and slowest, for the
Inflation page. Run on euro-area data, the trimmed means match the ECB's own (2018-2025)
within about 0.05 points on average and the median within about 0.15.
"""

import threading

import numpy as np
import pandas as pd

from .. import http
from .base import FetchResult, make_series

BASE = "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data"
MEASURES = ("median", "trim10", "trim30", "above2", "above5")
MIN_ITEMS = 100         # fewer items with data than this in a month: no reading
BANDS = [(-np.inf, 0, "<0")] + [(lo, lo + 1, f"{lo}–{lo + 1}") for lo in range(0, 10)] + [(10, np.inf, "10+")]  # % a year
MOVER_WEIGHT = 0.2      # % of the basket an item needs to be listed among the fastest and slowest risers

_lock = threading.Lock()
_cache: dict = {}       # per geo, computed once per run for all its measures


def source_url(key: str, params: dict | None = None) -> str:
    return "https://ec.europa.eu/eurostat/databrowser/view/prc_hicp_minr/default/table"


def _cells(payload: dict) -> tuple[dict[tuple[str, str], float], dict[str, str]]:
    """JSON-stat values keyed by (item code, time), and the items' English labels."""
    if "error" in payload:
        raise ValueError(f"Eurostat error: {payload['error']}")
    dims, sizes = payload["id"], payload["size"]
    cats = {d: list(payload["dimension"][d]["category"]["index"]) for d in dims}
    strides = [int(np.prod(sizes[i + 1:])) for i in range(len(sizes))]
    item, time = dims.index("coicop18"), dims.index("time")
    out = {}
    for pos, v in payload.get("value", {}).items():
        pos = int(pos)
        coords = [(pos // s) % n for s, n in zip(strides, sizes)]
        out[(cats["coicop18"][coords[item]], cats["time"][coords[time]])] = v
    return out, payload["dimension"]["coicop18"]["category"].get("label", {})


def _detailed(code: str) -> bool:
    return code.startswith("CP") and len(code) == 7   # a five-digit subclass, e.g. CP01111


def tables(index_payload: dict, weight_payload: dict) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, str]]:
    """Monthly indices and yearly weights of the detailed items (columns), and their labels."""
    idx, labels = _cells(index_payload)
    w, _ = _cells(weight_payload)
    items = sorted({c for c, _ in idx if _detailed(c)})
    rows: dict[pd.Timestamp, dict[str, float]] = {}
    for (c, t), v in idx.items():
        if _detailed(c):
            rows.setdefault(pd.Timestamp(f"{t}-01"), {})[c] = v
    index = pd.DataFrame.from_dict(rows, orient="index").reindex(columns=items).sort_index()
    wrows: dict[int, dict[str, float]] = {}
    for (c, t), v in w.items():
        if _detailed(c) and c in index.columns:
            wrows.setdefault(int(t), {})[c] = v
    weights = pd.DataFrame.from_dict(wrows, orient="index").reindex(columns=items).sort_index()
    return index, weights, labels


def distribution(rates: np.ndarray, weights: np.ndarray) -> dict[str, float]:
    """The measures for one month, from items' annual rates and weights (any scale)."""
    order = np.argsort(rates, kind="stable")
    x, w = rates[order], weights[order] / weights.sum()
    cum = np.cumsum(w)
    start = cum - w

    def trimmed(each_tail: float) -> float:
        # Each item keeps the part of its weight inside [each_tail, 1 - each_tail] of the cumulative distribution.
        keep = np.clip(np.minimum(cum, 1 - each_tail) - np.maximum(start, each_tail), 0, None)
        return float((keep * x).sum() / keep.sum())

    return {"median": float(x[min(np.searchsorted(cum, 0.5), len(x) - 1)]), "trim10": trimmed(0.05),
            "trim30": trimmed(0.15), "above2": float(100 * w[x > 2].sum()), "above5": float(100 * w[x > 5].sum())}


def compute(index: pd.DataFrame, weights: pd.DataFrame, labels: dict[str, str]) -> dict:
    yoy = (index / index.shift(12) - 1) * 100
    results: dict[str, dict[pd.Timestamp, float]] = {m: {} for m in MEASURES}
    latest = None
    for month, r in yoy.iterrows():
        if month.year not in weights.index:
            continue
        w = weights.loc[month.year]
        ok = r.notna() & w.notna() & (w > 0)
        if ok.sum() < MIN_ITEMS:
            continue
        for m, v in distribution(r[ok].to_numpy(), w[ok].to_numpy()).items():
            results[m][month] = v
        latest = (month, r[ok], w[ok] / w[ok].sum() * 100)
    if latest is None:
        raise ValueError("no month with enough detailed HICP items")
    month, rates, shares = latest
    bands = [[label, round(float(shares[(rates >= lo) & (rates < hi)].sum()), 2)] for lo, hi, label in BANDS]
    listed = [(labels.get(c, c), round(float(rates[c]), 1), round(float(shares[c]), 2))
              for c in rates.index if shares[c] >= MOVER_WEIGHT]
    listed.sort(key=lambda t: t[1])
    extra = {"month": month.strftime("%Y-%m"), "items": int(len(rates)), "bands": bands,
             "highest": [list(t) for t in reversed(listed[-5:])], "lowest": [list(t) for t in listed[:5]]}
    return {"series": results, "latest": extra}


def _geo(geo: str) -> dict:
    with _lock:
        entry = _cache.get(geo)
        if entry is None:
            try:
                params = {"geo": geo, "format": "JSON", "lang": "EN"}
                index_payload = http.get(f"{BASE}/prc_hicp_minr", params={**params, "unit": "I25"}).json()
                weight_payload = http.get(f"{BASE}/prc_hicp_iw", params=params).json()
                entry = compute(*tables(index_payload, weight_payload))
            except Exception as e:
                entry = e
            _cache[geo] = entry
        if isinstance(entry, Exception):
            raise entry
        return entry


def clear_cache() -> None:
    with _lock:
        _cache.clear()


def fetch(key: str, params: dict | None = None, **_) -> FetchResult:
    geo, measure = key.split("/", 1)
    if measure not in MEASURES:
        raise ValueError(f"unknown measure {measure!r}; choose from {MEASURES}")
    result = _geo(geo)
    values = result["series"][measure]
    meta = {"distribution": result["latest"]} if measure == "median" else {}
    return FetchResult(make_series(values.keys(), values.values()), meta)
