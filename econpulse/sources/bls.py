"""US Bureau of Labor Statistics public API, version 1 (no key: up to 25 requests a day,
10 years per request). Key is the BLS series id, e.g. CUUR0000SA0 (CPI-U, all items, NSA).
"""

import pandas as pd

from .. import http
from .base import FetchResult, madrid_today, make_series

URL = "https://api.bls.gov/publicAPI/v1/timeseries/data/"


def source_url(key: str, params: dict | None = None) -> str:
    return f"https://data.bls.gov/timeseries/{key}"


def parse(payload: dict, key: str) -> FetchResult:
    if payload.get("status") != "REQUEST_SUCCEEDED":
        raise ValueError(f"BLS: {payload.get('status')} {' '.join(payload.get('message', []))}".strip())
    series = next(s for s in payload["Results"]["series"] if s["seriesID"] == key)
    obs = [o for o in series["data"] if o["period"].startswith("M") and o["period"] != "M13" and o["value"] not in ("-", "")]
    dates = (pd.Timestamp(int(o["year"]), int(o["period"][1:]), 1) for o in obs)
    return FetchResult(make_series(dates, (o["value"] for o in obs)))


def fetch(key: str, params: dict | None = None, **_) -> FetchResult:
    year = madrid_today().year
    # The API is POST-only; http.get is for GETs, so use the shared session directly.
    r = http.session().post(URL, json={"seriesid": [key], "startyear": str(year - 9), "endyear": str(year)},
                            timeout=http.HTTP_TIMEOUT)
    r.raise_for_status()
    return parse(r.json(), key)
