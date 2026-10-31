"""FRED (Federal Reserve Bank of St. Louis), public CSV download; no API key needed.

Key is the FRED series id, e.g. DCOILBRENTEU (Brent spot price, US$ per barrel, daily).
"""

import csv
import io

from .. import http
from .base import FetchResult, make_series, parse_period

BASE = "https://fred.stlouisfed.org/graph/fredgraph.csv"


def source_url(key: str, params: dict | None = None) -> str:
    return f"https://fred.stlouisfed.org/series/{key}"


def parse(text: str, key: str) -> FetchResult:
    reader = csv.reader(io.StringIO(text))
    header = next(reader)
    if len(header) < 2:
        raise ValueError(f"FRED: unexpected header {header!r}")
    rows = [r for r in reader if len(r) >= 2 and r[1] not in ("", ".")]
    return FetchResult(make_series((parse_period(r[0]) for r in rows), (r[1] for r in rows)))


def fetch(key: str, params: dict | None = None, **_) -> FetchResult:
    return parse(http.get(BASE, params={"id": key}).text, key)
