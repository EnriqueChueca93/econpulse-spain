"""Banco de España statistics API (BIEST / HERMES series codes).

Docs: https://www.bde.es/webbe/es/estadisticas/recursos/api-estadisticas-bde.html
Key is the series code shown in the Bank's CSV files, e.g. DPUG0B1F0ZP (Spain 10y yield, daily).

Monthly, quarterly and annual series come in one request (rango=MAX). Daily series
are capped at 36 months per request, so the first fetch walks back year by year
(rango=2000, 2001, ...) from params.start, and later fetches ask only for the
recent window, which fetch.py merges into the stored history.
"""

from datetime import date

import pandas as pd

from .. import http, i18n
from .base import FetchResult, madrid_today, make_series

BASE = "https://app.bde.es/bierest/resources/srdatosapp"
DEFAULT_DAILY_START = 2000
INCREMENTAL = True


VIEWER = "https://app.bde.es/bie_www/bie_wwwias/xml/Arranque.html"


def source_url(key: str, params: dict | None = None) -> str:
    """The series in the Bank's HERMES viewer (its help: "?SERIE=<code>" opens a series directly)."""
    return f"{VIEWER}?SERIE={key}&IDIOMA={'ES' if i18n.lang() == 'es' else 'EN'}"


def _request(key: str, rango: str) -> dict:
    payload = http.get(f"{BASE}/listaSeries", params={"idioma": "es", "series": key, "rango": rango}).json()
    if isinstance(payload, dict):  # error object, e.g. {"errNum": 412, "errMsgDebug": ...}
        raise ValueError(f"Banco de España error {payload.get('errNum')}: {payload.get('errMsgDebug') or payload.get('errMsgUsr')}")
    if not payload or "errNum" in payload[0]:
        raise ValueError(f"Banco de España: series {key!r} not found")
    return payload[0]


def parse(item: dict) -> pd.Series:
    pairs = [(f[:10], v) for f, v in zip(item.get("fechas", []), item.get("valores", [])) if v is not None]
    return make_series((pd.Timestamp(d) for d, _ in pairs), (v for _, v in pairs))


def _daily_ranges(since: pd.Timestamp | None, start_year: int, today: date) -> list[str]:
    if since is not None:
        age_days = (pd.Timestamp(today) - since).days
        for rango, limit in (("3M", 80), ("12M", 350), ("36M", 1070)):
            if age_days <= limit:
                return [rango]
        start_year = since.year
    return [str(y) for y in range(start_year, today.year + 1)]


def fetch(key: str, params: dict | None = None, since: pd.Timestamp | None = None, freq: str | None = None, **_) -> FetchResult:
    params = params or {}
    if freq != "D":
        item = _request(key, "MAX")
        return FetchResult(parse(item), {"source_name": item.get("descripcionCorta", "")})

    pieces, name = [], ""
    for rango in _daily_ranges(since, int(params.get("start", DEFAULT_DAILY_START)), madrid_today()):
        item = _request(key, rango)
        name = item.get("descripcionCorta", name)
        if item.get("valores"):
            try:
                pieces.append(parse(item))
            except ValueError:  # a year with no observations
                continue
    if not pieces:
        raise ValueError(f"Banco de España: no observations for {key!r}")
    series = pd.concat(pieces)
    series = series[~series.index.duplicated(keep="last")].sort_index()
    return FetchResult(series, {"source_name": name})
