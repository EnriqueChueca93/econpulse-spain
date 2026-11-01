"""Participation and employment adjusted for an ageing population (EconPulse calculation).

Eurostat's labour force survey counts people in private households by sex, five-year age group and
labour status (lfsq_pganws, from 1998). The participation rate of everyone aged 15 and over is the
average of each group's own rate weighted by the group's share of the population, so it falls as the
population ages even if no group changes its behaviour. Holding the shares at their BASE_YEAR average
while each group's rate moves shows participation at the BASE_YEAR age mix; the gap to the actual rate
is the effect of the change in the age mix since then. The same goes for the employment rate (employed
people as a share of the population). Groups: men and women in 13 age bands (15-19 ... 70-74, 75+).
Keys: "participation", "participation_adjusted", "employment", "employment_adjusted", % of the
population aged 15 and over, and "share_65plus", the share of that population aged 65 and over;
quarterly, not seasonally adjusted. The recombined actual rates match Eurostat's published ones
within 0.1 points.
"""

import threading

import numpy as np
import pandas as pd

from .. import http
from .base import FetchResult, make_series, parse_period

BASE = "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data"
DATASET = "lfsq_pganws"
BASE_YEAR = 2008
BANDS = ("Y15-19", "Y20-24", "Y25-29", "Y30-34", "Y35-39", "Y40-44", "Y45-49", "Y50-54", "Y55-59", "Y60-64",
         "Y65-69", "Y70-74", "Y_GE75")
SEXES = ("M", "F")
KEYS = ("participation", "participation_adjusted", "employment", "employment_adjusted", "share_65plus")
OLD = ("Y65-69", "Y70-74", "Y_GE75")

_lock = threading.Lock()
_cache: dict[str, object] = {}


def source_url(key: str, params: dict | None = None) -> str:
    return f"https://ec.europa.eu/eurostat/databrowser/view/{DATASET}/default/table"


def counts(payload: dict) -> pd.DataFrame:
    """Thousands of people by quarter (rows) and (labour status, sex, age band) (columns)."""
    if "error" in payload:
        raise ValueError(f"Eurostat error: {payload['error']}")
    dims, sizes = payload["id"], payload["size"]
    cats = {d: list(payload["dimension"][d]["category"]["index"]) for d in dims}
    strides = [int(np.prod(sizes[i + 1:])) for i in range(len(sizes))]
    rows = {}
    for pos, v in payload.get("value", {}).items():
        coords = {d: cats[d][(int(pos) // s) % n] for d, s, n in zip(dims, strides, sizes)}
        if coords["sex"] in SEXES and coords["age"] in BANDS and coords["wstatus"] in ("POP", "ACT", "EMP"):
            rows.setdefault(parse_period(coords["time"]), {})[(coords["wstatus"], coords["sex"], coords["age"])] = v
    cols = pd.MultiIndex.from_product([("POP", "ACT", "EMP"), SEXES, BANDS])
    return pd.DataFrame.from_dict(rows, orient="index").reindex(columns=cols).sort_index()


def compute(table: pd.DataFrame, base_year: int = BASE_YEAR) -> dict[str, pd.Series]:
    pop = table["POP"]
    pop = pop[pop.notna().all(axis=1)]          # a quarter needs every group's population
    if pop.empty:
        raise ValueError("no quarter with every group's population")
    # Groups too small to publish (women 75+ in some quarters) count as having nobody active.
    act = table["ACT"].reindex(pop.index).fillna(0)
    emp = table["EMP"].reindex(pop.index).fillna(0)
    shares = pop.div(pop.sum(axis=1), axis=0)
    in_base = shares[shares.index.year == base_year]
    if len(in_base) < 4:
        raise ValueError(f"the base year {base_year} needs four quarters")
    base = in_base.mean()
    out = {"share_65plus": shares.loc[:, (slice(None), list(OLD))].sum(axis=1) * 100}
    for name, count in (("participation", act), ("employment", emp)):
        rate = count / pop
        out[name] = (shares * rate).sum(axis=1) * 100
        out[f"{name}_adjusted"] = (rate * base).sum(axis=1) * 100
    return out


def _results() -> dict[str, pd.Series]:
    with _lock:
        entry = _cache.get("ES")
        if entry is None:
            try:
                payload = http.get(f"{BASE}/{DATASET}", params={"geo": "ES", "citizen": "TOTAL", "unit": "THS_PER",
                                                                "format": "JSON", "lang": "EN"}).json()
                entry = compute(counts(payload))
            except Exception as e:
                entry = e
            _cache["ES"] = entry
        if isinstance(entry, Exception):
            raise entry
        return entry


def clear_cache() -> None:
    with _lock:
        _cache.clear()


def fetch(key: str, params: dict | None = None, **_) -> FetchResult:
    if key not in KEYS:
        raise ValueError(f"unknown measure {key!r}; choose from {KEYS}")
    s = _results()[key].round(3)
    return FetchResult(make_series(s.index, s.values), {"base_year": BASE_YEAR})
