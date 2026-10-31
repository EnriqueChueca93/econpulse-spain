"""Eurostat dissemination API (JSON-stat 2.0).

Docs: https://wikis.ec.europa.eu/display/EUROSTATHELP/API+Statistics+-+data+query
Key is the dataset code; params must pin every dimension except time to one value.
"""

from .. import http
from .base import FetchResult, make_series, parse_period

BASE = "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data"


def source_url(key: str, params: dict | None = None) -> str:
    return f"https://ec.europa.eu/eurostat/databrowser/view/{key}/default/table"


def parse(payload: dict) -> FetchResult:
    if "error" in payload:
        raise ValueError(f"Eurostat error: {payload['error']}")
    dims, sizes = payload["id"], payload["size"]
    extra = {d: n for d, n in zip(dims, sizes) if d != "time" and n != 1}
    if extra:
        raise ValueError(f"Query is ambiguous; pin these dimensions to one value: {extra}")
    time_index = payload["dimension"]["time"]["category"]["index"]  # label -> position
    by_pos = {pos: label for label, pos in time_index.items()}
    values = payload.get("value", {})
    # With every other dimension fixed, a value's position is its time position.
    obs = sorted((by_pos[int(pos)], v) for pos, v in values.items())
    series = make_series((parse_period(label) for label, _ in obs), (v for _, v in obs))
    return FetchResult(series, {"source_name": payload.get("label", ""), "source_updated": payload.get("updated")})


def fetch(key: str, params: dict | None = None, **_) -> FetchResult:
    payload = http.get(f"{BASE}/{key}", params={**(params or {}), "format": "JSON", "lang": "EN"}).json()
    return parse(payload)
