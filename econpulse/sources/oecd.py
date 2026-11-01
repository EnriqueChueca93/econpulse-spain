"""OECD Data Explorer, SDMX REST API (CSV); no key needed.

Key is "<dataflow>/<series key>", as shown on data-explorer.oecd.org, e.g.
    OECD.SDD.TPS,DSD_PRICES@DF_PRICES_ALL,1.0/GBR.M.N.CPI.PA._T.N.GY   (UK CPI, % change on a year earlier)
Empty positions in the series key are wildcards: the query must still match exactly one
series, or the fetch fails rather than mixing series.
"""

import csv
import io

from .. import http
from .base import FetchResult, make_series, parse_period

BASE = "https://sdmx.oecd.org/public/rest/data"
NON_KEY = {"TIME_PERIOD", "OBS_VALUE", "OBS_STATUS", "UNIT_MULT", "DECIMALS", "BASE_PER", "STRUCTURE", "STRUCTURE_ID",
           "STRUCTURE_NAME", "ACTION", "OBS_STATUS_CHANGE"}


def source_url(key: str, params: dict | None = None) -> str:
    flow, series = key.split("/", 1)
    return f"https://data-explorer.oecd.org/vis?df[ag]={flow.split(',')[0]}&df[id]={flow.split(',')[1]}&dq={series}"


def parse(text: str) -> FetchResult:
    rows = list(csv.DictReader(io.StringIO(text.lstrip("﻿"))))
    if not rows:
        raise ValueError("OECD returned no observations")
    dims = [k for k in rows[0] if k not in NON_KEY]
    series = {tuple(r[d] for d in dims) for r in rows}
    if len(series) > 1:
        raise ValueError(f"OECD query matches {len(series)} series; fix the wildcards in the key")
    return FetchResult(make_series((parse_period(r["TIME_PERIOD"]) for r in rows), (r["OBS_VALUE"] for r in rows)))


def fetch(key: str, params: dict | None = None, **_) -> FetchResult:
    flow, series = key.split("/", 1)
    return parse(http.get(f"{BASE}/{flow}/{series}", params={"format": "csv", "startPeriod": "1990"}).text)
