"""Red Eléctrica (REE) REData API: electricity prices and demand.

Docs: https://www.ree.es/es/datos/apidatos
Keys:
    spot_price   day-ahead market price, €/MWh. Only served at hourly/15-minute
                 resolution in short windows, so we ask for 7 days at a time and
                 average to a daily price.
    demand       daily national electricity demand, MWh, asked one calendar year at a time.

The first fetch walks back to params.start; later fetches only ask for the recent
window, which fetch.py merges into the stored history.
"""

from datetime import date, timedelta

import pandas as pd

from .. import http
from .base import FetchResult, madrid_today, make_series

BASE = "https://apidatos.ree.es/es/datos"
INCREMENTAL = True

WIDGETS = {
    # Day-ahead prices are set the day before, so today's are complete; today's demand is not.
    "spot_price": {"path": "mercados/precios-mercados-tiempo-real", "title": "Precio mercado spot",
                   "trunc": "hour", "chunk_days": 7, "start": "2025-01-01", "lag_days": 0},
    "demand": {"path": "demanda/evolucion", "title": "Demanda",
               "trunc": "day", "chunk_days": None, "start": "2015-01-01", "lag_days": 1},
}


def source_url(key: str, params: dict | None = None) -> str:
    return "https://www.ree.es/es/datos/mercados" if key == "spot_price" else "https://www.ree.es/es/datos/demanda"


def windows(start: date, end: date, chunk_days: int | None) -> list[tuple[date, date]]:
    """Split [start, end] into request windows: fixed-size chunks, or calendar years if chunk_days is None."""
    out, cur = [], start
    while cur <= end:
        stop = min(end, cur + timedelta(days=chunk_days - 1) if chunk_days else date(cur.year, 12, 31))
        out.append((cur, stop))
        cur = stop + timedelta(days=1)
    return out


def parse(payload: dict, title: str) -> pd.Series:
    """Raw observations indexed by local (Madrid) date; intraday data keeps one row per interval."""
    if "errors" in payload:
        raise ValueError(f"REE error: {payload['errors'][0].get('detail')}")
    for item in payload.get("included", []):
        if item["attributes"].get("title") == title:
            values = item["attributes"]["values"]
            # Timestamps carry the Madrid offset ('2026-10-28T23:45:00.000+01:00'): the first 10 chars are the local date.
            stamps = pd.DatetimeIndex([v["datetime"][:10] for v in values])
            return pd.Series([float(v["value"]) for v in values], index=stamps, dtype="float64")
    raise ValueError(f"REE: {title!r} not in response")


def fetch(key: str, params: dict | None = None, since: pd.Timestamp | None = None, **_) -> FetchResult:
    if key not in WIDGETS:
        raise ValueError(f"Unknown REE key {key!r}; choose from {sorted(WIDGETS)}")
    w = WIDGETS[key]
    start = since.date() if since is not None else date.fromisoformat((params or {}).get("start", w["start"]))
    end = madrid_today() - timedelta(days=w["lag_days"])
    pieces = []
    for a, b in windows(start, end, w["chunk_days"]):
        payload = http.get(f"{BASE}/{w['path']}", params={
            "start_date": f"{a.isoformat()}T00:00", "end_date": f"{b.isoformat()}T23:59", "time_trunc": w["trunc"],
        }).json()
        try:
            pieces.append(parse(payload, w["title"]))
        except ValueError:
            if b >= madrid_today() - timedelta(days=2):  # the latest window may not be published yet
                continue
            raise
    if not pieces:
        raise ValueError(f"REE: no data for {key!r}")
    series = pd.concat(pieces)
    if w["trunc"] == "hour":
        series = series.groupby(level=0).mean()  # hourly or 15-minute prices -> daily average
    return FetchResult(make_series(series.index, series.to_numpy()))
