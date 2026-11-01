"""Bank for International Settlements statistics, SDMX REST API (CSV); no key needed.

Key is "<dataflow>/<series key>", e.g.
    WS_CBPOL/D.US    central bank policy rate, United States, daily
    WS_DSR/Q.ES.H    debt service ratio, Spanish households, quarterly
"""

import csv
import io

from .. import http
from .base import FetchResult, make_series, parse_period

BASE = "https://stats.bis.org/api/v2/data/dataflow/BIS"


def source_url(key: str, params: dict | None = None) -> str:
    flow, series = key.split("/", 1)
    return f"https://data.bis.org/topics/{'CBPOL' if flow == 'WS_CBPOL' else flow.replace('WS_', '')}"


def parse(text: str) -> FetchResult:
    rows = [r for r in csv.DictReader(io.StringIO(text.lstrip("﻿"))) if r.get("OBS_VALUE") not in (None, "", "NaN")]
    return FetchResult(make_series((parse_period(r["TIME_PERIOD"]) for r in rows), (r["OBS_VALUE"] for r in rows)))


def fetch(key: str, params: dict | None = None, **_) -> FetchResult:
    flow, series = key.split("/", 1)
    return parse(http.get(f"{BASE}/{flow}/1.0/{series}", params={"format": "csv", "startPeriod": "1990-01-01"}).text)
