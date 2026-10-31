"""ECB Data Portal SDMX REST API.

Docs: https://data.ecb.europa.eu/help/api/data
Key is 'FLOW/SERIES_KEY', e.g. 'FM/D.U2.EUR.4F.KR.DFR.LEV' (deposit facility rate).
"""

import csv
import io

from .. import http
from .base import FetchResult, make_series, parse_period

BASE = "https://data-api.ecb.europa.eu/service/data"


def source_url(key: str, params: dict | None = None) -> str:
    flow, series_key = key.split("/", 1)
    return f"https://data.ecb.europa.eu/data/datasets/{flow}/{flow}.{series_key}"


def parse(text: str) -> FetchResult:
    rows = [r for r in csv.DictReader(io.StringIO(text)) if r.get("OBS_VALUE") not in (None, "")]
    series = make_series((parse_period(r["TIME_PERIOD"]) for r in rows), (r["OBS_VALUE"] for r in rows))
    return FetchResult(series)


def fetch(key: str, params: dict | None = None) -> FetchResult:
    text = http.get(f"{BASE}/{key}", params={"format": "csvdata", "detail": "dataonly", **(params or {})}).text
    return parse(text)
