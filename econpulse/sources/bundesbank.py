"""Deutsche Bundesbank statistics, SDMX REST API (CSV); no key needed.

Key is "<dataflow>/<series key>", e.g.
    BBSIS/D.I.ZST.ZI.EUR.S1311.B.A604.R10XX.R.A.A._Z._Z.A   German 10-year federal yield, daily
Daily series list weekends as "." (no value). After the first download only recent
observations are requested, since the full history is several megabytes.
"""

import csv
import io

import pandas as pd

from .. import http
from .base import FetchResult, make_series, parse_period

BASE = "https://api.statistiken.bundesbank.de/rest/data"
INCREMENTAL = True


def source_url(key: str, params: dict | None = None) -> str:
    flow, series = key.split("/", 1)
    return f"https://www.bundesbank.de/dynamic/action/en/statistics/time-series-databases/time-series-databases/759784/759784?tsId={flow}.{series}"


def parse(text: str) -> FetchResult:
    rows = [r for r in csv.DictReader(io.StringIO(text.lstrip("﻿"))) if r.get("OBS_VALUE") not in (None, "", ".")]
    return FetchResult(make_series((parse_period(r["TIME_PERIOD"]) for r in rows), (r["OBS_VALUE"] for r in rows)))


def fetch(key: str, params: dict | None = None, since: pd.Timestamp | None = None, **_) -> FetchResult:
    query = {"format": "sdmx_csv", "lang": "en"}
    if since is not None:
        query["startPeriod"] = since.strftime("%Y-%m-%d")
    return parse(http.get(f"{BASE}/{key}", params=query).text)
