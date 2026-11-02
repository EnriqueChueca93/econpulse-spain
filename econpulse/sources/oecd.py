"""OECD Data Explorer, SDMX REST API (CSV); no key needed.

Key is "<dataflow>/<series key>", as shown on data-explorer.oecd.org, e.g.
    OECD.SDD.TPS,DSD_PRICES@DF_PRICES_ALL,1.0/GBR.M.N.CPI.PA._T.N.GY   (UK CPI, % change on a year earlier)
Empty positions in the series key are wildcards: the query must still match exactly one
series, or the fetch fails rather than mixing series.

params: {edition: true} also asks for the dataflow's name and records it, e.g.
"Economic Outlook 119" for the forecasts, whose values change with each edition.
"""

import csv
import io
import re
import threading

from .. import http
from .base import FetchResult, make_series, parse_period

BASE = "https://sdmx.oecd.org/public/rest/data"
NON_KEY = {"TIME_PERIOD", "OBS_VALUE", "OBS_STATUS", "UNIT_MULT", "DECIMALS", "BASE_PER", "STRUCTURE", "STRUCTURE_ID",
           "STRUCTURE_NAME", "ACTION", "OBS_STATUS_CHANGE"}
_CODE_COLUMN = re.compile(r"^[A-Z][A-Z0-9_]*$")  # the labelled format adds "Reference area" etc. after each code


def source_url(key: str, params: dict | None = None) -> str:
    flow, series = key.split("/", 1)
    return f"https://data-explorer.oecd.org/vis?df[ag]={flow.split(',')[0]}&df[id]={flow.split(',')[1]}&dq={series}"


def parse(text: str) -> FetchResult:
    rows = list(csv.DictReader(io.StringIO(text.lstrip("﻿"))))
    if not rows:
        raise ValueError("OECD returned no observations")
    dims = [k for k in rows[0] if k not in NON_KEY and _CODE_COLUMN.match(k)]
    series = {tuple(r[d] for d in dims) for r in rows}
    if len(series) > 1:
        raise ValueError(f"OECD query matches {len(series)} series; fix the wildcards in the key")
    meta = {"edition": rows[0]["STRUCTURE_NAME"]} if rows[0].get("STRUCTURE_NAME") else {}
    return FetchResult(make_series((parse_period(r["TIME_PERIOD"]) for r in rows), (r["OBS_VALUE"] for r in rows)), meta)


def parse_by_area(text: str) -> dict[str, FetchResult]:
    """One result per reference area of a query that names several ("ESP+FRA..."); each area must
    still match exactly one series."""
    rows = list(csv.DictReader(io.StringIO(text.lstrip("﻿"))))
    if not rows:
        raise ValueError("OECD returned no observations")
    dims = [k for k in rows[0] if k not in NON_KEY and _CODE_COLUMN.match(k)]
    by_area: dict[str, list[dict]] = {}
    for r in rows:
        by_area.setdefault(r["REF_AREA"], []).append(r)
    out = {}
    for area, group in by_area.items():
        if len({tuple(r[d] for d in dims) for r in group}) > 1:
            raise ValueError(f"OECD query matches several series for {area}; fix the wildcards in the key")
        out[area] = FetchResult(make_series((parse_period(r["TIME_PERIOD"]) for r in group),
                                            (r["OBS_VALUE"] for r in group)), {})
    return out


_lock = threading.Lock()
_cache: dict[str, object] = {}


def clear_cache() -> None:
    with _lock:
        _cache.clear()


def fetch(key: str, params: dict | None = None, **_) -> FetchResult:
    """params {batch: "ESP+FRA+..."} asks for those areas together, once per run (the OECD limits how
    often it may be called), and returns this key's area (the first part of the series key)."""
    params = params or {}
    flow, series = key.split("/", 1)
    fmt = "csvfilewithlabels" if params.get("edition") else "csv"
    start = str(params.get("start", "1990"))      # {start: 1960} for the whole history, e.g. for long-run averages
    if not params.get("batch"):
        return parse(http.get(f"{BASE}/{flow}/{series}", params={"format": fmt, "startPeriod": start}).text)
    # The area is not always the first part of the key (the national accounts have Q.Y.GBR...): it is the
    # part that is one of the batch's areas.
    areas, parts = params["batch"].split("+"), series.split(".")
    at = next((i for i, part in enumerate(parts) if part in areas), None)
    if at is None:
        raise ValueError(f"no area of the batch {params['batch']} in the key {series}")
    area = parts[at]
    url = f"{BASE}/{flow}/" + ".".join(params["batch"] if i == at else part for i, part in enumerate(parts))
    key = f"{url}|{start}"
    with _lock:
        entry = _cache.get(key)
        if entry is None:
            try:
                entry = parse_by_area(http.get(url, params={"format": "csv", "startPeriod": start}).text)
            except Exception as e:
                entry = e
            _cache[key] = entry
    if isinstance(entry, Exception):
        raise entry
    if area not in entry:
        raise ValueError(f"OECD returned no {area} series for {series}")
    return entry[area]
