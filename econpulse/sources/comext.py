"""Eurostat Comext: Spain's goods trade by product (dataset DS-045409, "EU trade since 1988 by HS2-4-6 and CN8").

Monthly values in euros of exports and imports by chapter of the Harmonised System (HS2, 01-99), with
any partner Comext publishes (WORLD by default; EU27_2020_INTRA and EU27_2020_EXTRA for the EU split,
or a country code). Key is a list of chapters, e.g. "01-05,16", or "TOTAL"; params give the flow
("exports" or "imports") and the partner. A group's value is the sum of its chapters in months when
Comext has the total; a chapter with no value that month counts as zero. The API answers slowly when
asked for many chapters at once, so the chapters are requested in batches; one download per partner and
flow serves every group. The total ("TOTAL") comes from one request per flow that covers every partner,
which is quick. Comext's figures follow the community concept (Spain's own customs figures differ
slightly).
"""

import threading

import numpy as np
import pandas as pd

from .. import http
from .base import FetchResult, make_series, parse_period

INCREMENTAL = True
BASE = "https://ec.europa.eu/eurostat/api/comext/dissemination/statistics/1.0/data/DS-045409"
FLOWS = {"imports": "1", "exports": "2"}
CHAPTERS = [f"{i:02d}" for i in range(1, 100)]
BATCH = 20                     # chapters per request: the API slows down sharply with many more
FIRST = "2002-01"

_lock = threading.Lock()
_cache: dict[tuple, object] = {}


def source_url(key: str, params: dict | None = None) -> str:
    return "https://ec.europa.eu/eurostat/comext/newxtweb/"


def chapters(spec: str) -> list[str]:
    """'01-05,16' -> ['01', '02', '03', '04', '05', '16']; 'TOTAL' -> ['TOTAL']."""
    if spec.upper() == "TOTAL":
        return ["TOTAL"]
    out = []
    for part in spec.split(","):
        lo, _, hi = part.strip().partition("-")
        out += [f"{i:02d}" for i in range(int(lo), int(hi or lo) + 1)]
    return out


def parse(payload: dict, column: str = "product") -> pd.DataFrame:
    """Euros by month (rows) and product, or another dimension, (columns) from a Comext JSON-stat answer."""
    if "error" in payload:
        raise ValueError(f"Comext error: {payload['error']}")
    dims, sizes = payload["id"], payload["size"]
    cats = {d: list(payload["dimension"][d]["category"]["index"]) for d in dims}
    strides = [int(np.prod(sizes[i + 1:])) for i in range(len(sizes))]
    product, time = dims.index(column), dims.index("time")
    rows: dict[pd.Timestamp, dict[str, float]] = {}
    for pos, v in payload.get("value", {}).items():
        coords = [(int(pos) // s) % n for s, n in zip(strides, sizes)]
        rows.setdefault(parse_period(cats["time"][coords[time]]), {})[cats[column][coords[product]]] = v
    return pd.DataFrame.from_dict(rows, orient="index").sort_index()


def _download(partner: str, flow: str, since: str) -> pd.DataFrame:
    parts = []
    products = ["TOTAL"] + CHAPTERS
    for i in range(0, len(products), BATCH):
        params = [("reporter", "ES"), ("partner", partner), ("flow", FLOWS[flow]), ("indicators", "VALUE_IN_EUROS"),
                  ("freq", "M"), ("sinceTimePeriod", since), ("format", "JSON"), ("lang", "EN")]
        params += [("product", p) for p in products[i:i + BATCH]]
        parts.append(parse(http.get(BASE, params=params, timeout=180).json()))
    table = pd.concat(parts, axis=1)
    return table.T.groupby(level=0).first().T          # one column per product


def _download_totals(flow: str, since: str) -> pd.DataFrame:
    params = [("reporter", "ES"), ("flow", FLOWS[flow]), ("product", "TOTAL"), ("indicators", "VALUE_IN_EUROS"),
              ("freq", "M"), ("sinceTimePeriod", since), ("format", "JSON"), ("lang", "EN")]
    return parse(http.get(BASE, params=params, timeout=180).json(), column="partner")


def _cached(key: tuple, load) -> pd.DataFrame:
    with _lock:
        entry = _cache.get(key)
        if entry is None:
            try:
                entry = load()
            except Exception as e:
                entry = e
            _cache[key] = entry
    if isinstance(entry, Exception):
        raise entry
    return entry


def table(partner: str, flow: str, since: str = FIRST) -> pd.DataFrame:
    """Every chapter and the total for one partner and flow, cached for the run."""
    return _cached(("chapters", partner, flow, since), lambda: _download(partner, flow, since))


def totals(flow: str, since: str = FIRST) -> pd.DataFrame:
    """All goods for every partner (columns) in one flow, cached for the run."""
    return _cached(("totals", flow, since), lambda: _download_totals(flow, since))


def clear_cache() -> None:
    with _lock:
        _cache.clear()


def fetch(key: str, params: dict | None = None, *, since: pd.Timestamp | None = None, **_) -> FetchResult:
    params = params or {}
    flow, partner = params.get("flow", "exports"), params.get("partner", "WORLD")
    if flow not in FLOWS:
        raise ValueError(f"unknown flow {flow!r}; use exports or imports")
    start = max(pd.Timestamp(FIRST), since).strftime("%Y-%m") if since is not None else FIRST
    if key.upper() == "TOTAL":
        t = totals(flow, start)
        if partner not in t:
            raise ValueError(f"Comext has no trade with partner {partner!r}")
        values = t[partner].dropna()
        return FetchResult(make_series(values.index, values.values), {})
    t = table(partner, flow, start)
    if "TOTAL" not in t:
        raise ValueError("Comext returned no total")
    t = t[t["TOTAL"].notna()]
    wanted = chapters(key)
    values = t.reindex(columns=wanted).fillna(0).sum(axis=1)
    return FetchResult(make_series(values.index, values.values), {})
