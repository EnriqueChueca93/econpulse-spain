"""IMF data service (api.imf.org), SDMX 2.1; no key needed. Used for the World Economic Outlook.

Key is "<agency>,<dataflow>/<series key>", e.g.
    IMF.RES,WEO/ESP.NGDP_RPCH.A   Spain, real GDP growth, history then projections
The IMF's older DataMapper API refuses automated requests; this is its current public
data service. The response says when the edition was published, which is recorded.
"""

import threading
import xml.etree.ElementTree as ET

from .. import http
from .base import FetchResult, make_series, parse_period

BASE = "https://api.imf.org/external/sdmx/2.1/data"


def source_url(key: str, params: dict | None = None) -> str:
    agency, flow = key.split("/", 1)[0].split(",", 1)
    return f"https://data.imf.org/en/datasets/{agency}:{flow}"


def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _series_result(series, meta: dict) -> FetchResult:
    obs = [o.attrib for o in series if _local(o.tag) == "Obs" and o.attrib.get("OBS_VALUE") not in (None, "", "NaN")]
    if not obs:
        raise ValueError("IMF returned no observations")
    return FetchResult(make_series((parse_period(o["TIME_PERIOD"]) for o in obs), (o["OBS_VALUE"] for o in obs)), dict(meta))


def _parse_all(text: str) -> tuple[list, dict]:
    root = ET.fromstring(text)
    series = [el for el in root.iter() if _local(el.tag) == "Series"]
    meta = {}
    dataset = next((el for el in root.iter() if _local(el.tag) == "DataSet"), None)
    if dataset is not None and dataset.attrib.get("PUBLICATION_DATE"):
        meta["published"] = dataset.attrib["PUBLICATION_DATE"][:10]
    return series, meta


def parse(text: str) -> FetchResult:
    series, meta = _parse_all(text)
    if len(series) != 1:
        raise ValueError(f"IMF query matches {len(series)} series; it must match exactly one")
    return _series_result(series[0], meta)


def parse_by_country(text: str) -> dict[str, FetchResult]:
    """One result per country of a query that names several ("ESP+FRA.NGDP_RPCH.A")."""
    series, meta = _parse_all(text)
    out = {}
    for s in series:
        try:
            out[s.attrib.get("COUNTRY", "")] = _series_result(s, meta)
        except ValueError:
            continue
    return out


_lock = threading.Lock()
_cache: dict[str, object] = {}


def clear_cache() -> None:
    with _lock:
        _cache.clear()


def fetch(key: str, params: dict | None = None, **_) -> FetchResult:
    """params {batch: "ESP+FRA+..."} asks for those countries together, once per run, and returns
    this key's country (the first part of the series key) from the shared answer."""
    batch = (params or {}).get("batch")
    if not batch:
        return parse(http.get(f"{BASE}/{key}", params={"startPeriod": "1990"}).text)
    flow, series_key = key.split("/", 1)
    country, rest = series_key.split(".", 1)
    url = f"{BASE}/{flow}/{batch}.{rest}"
    with _lock:
        entry = _cache.get(url)
        if entry is None:
            try:
                entry = parse_by_country(http.get(url, params={"startPeriod": "1990"}).text)
            except Exception as e:
                entry = e
            _cache[url] = entry
    if isinstance(entry, Exception):
        raise entry
    if country not in entry:
        raise ValueError(f"IMF returned no {country} series for {rest}")
    return entry[country]
