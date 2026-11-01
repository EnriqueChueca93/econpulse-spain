"""IMF data service (api.imf.org), SDMX 2.1; no key needed. Used for the World Economic Outlook.

Key is "<agency>,<dataflow>/<series key>", e.g.
    IMF.RES,WEO/ESP.NGDP_RPCH.A   Spain, real GDP growth, history then projections
The IMF's older DataMapper API refuses automated requests; this is its current public
data service. The response says when the edition was published, which is recorded.
"""

import xml.etree.ElementTree as ET

from .. import http
from .base import FetchResult, make_series, parse_period

BASE = "https://api.imf.org/external/sdmx/2.1/data"


def source_url(key: str, params: dict | None = None) -> str:
    agency, flow = key.split("/", 1)[0].split(",", 1)
    return f"https://data.imf.org/en/datasets/{agency}:{flow}"


def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def parse(text: str) -> FetchResult:
    root = ET.fromstring(text)
    series = [el for el in root.iter() if _local(el.tag) == "Series"]
    if len(series) != 1:
        raise ValueError(f"IMF query matches {len(series)} series; it must match exactly one")
    obs = [o.attrib for o in series[0] if _local(o.tag) == "Obs" and o.attrib.get("OBS_VALUE") not in (None, "", "NaN")]
    if not obs:
        raise ValueError("IMF returned no observations")
    meta = {}
    dataset = next((el for el in root.iter() if _local(el.tag) == "DataSet"), None)
    if dataset is not None and dataset.attrib.get("PUBLICATION_DATE"):
        meta["published"] = dataset.attrib["PUBLICATION_DATE"][:10]
    return FetchResult(make_series((parse_period(o["TIME_PERIOD"]) for o in obs), (o["OBS_VALUE"] for o in obs)), meta)


def fetch(key: str, params: dict | None = None, **_) -> FetchResult:
    return parse(http.get(f"{BASE}/{key}", params={"startPeriod": "1990"}).text)
