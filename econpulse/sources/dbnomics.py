"""DBnomics (db.nomics.world): an open mirror of official statistics, run by the Banque de
France and CEPREMAP; no key needed. Used where the original agency needs a key (US BEA).

Key is "<provider>/<dataset>/<series>", e.g. BEA/NIPA-T10111/A191RO-Q (US real GDP, % change on a year earlier).
"""

import threading

from .. import http
from .base import FetchResult, make_series, parse_period

BASE = "https://api.db.nomics.world/v22/series"


def source_url(key: str, params: dict | None = None) -> str:
    return f"https://db.nomics.world/{key}"


def parse(payload: dict) -> FetchResult:
    docs = payload.get("series", {}).get("docs", [])
    if not docs:
        raise ValueError("DBnomics returned no series")
    doc = docs[0]
    pairs = [(p, v) for p, v in zip(doc["period"], doc["value"]) if v not in (None, "NA")]
    meta = {"source_updated": doc["indexed_at"][:10]} if doc.get("indexed_at") else {}  # when DBnomics last saw a change
    return FetchResult(make_series((parse_period(p) for p, _ in pairs), (v for _, v in pairs)), meta)


_lock = threading.Lock()
_cache: dict[str, object] = {}


def clear_cache() -> None:
    with _lock:
        _cache.clear()


def fetch(key: str, params: dict | None = None, **_) -> FetchResult:
    """params {batch: "ESP+FRA+..."} asks for the same series of those countries together, once per run
    (the country is the first part of the series code, as in AMECO's ESP.3.1.0.0.RWCDC)."""
    batch = (params or {}).get("batch")
    if not batch:
        return parse(http.get(f"{BASE}/{key}", params={"observations": 1}).json())
    provider, dataset, code = key.split("/", 2)
    country, rest = code.split(".", 1)
    ids = ",".join(f"{provider}/{dataset}/{c}.{rest}" for c in batch.split("+"))
    with _lock:
        entry = _cache.get(ids)
        if entry is None:
            try:
                docs = http.get(BASE, params={"series_ids": ids, "observations": 1}).json().get("series", {}).get("docs", [])
                entry = {d["series_code"].split(".", 1)[0]: d for d in docs}
            except Exception as e:
                entry = e
            _cache[ids] = entry
    if isinstance(entry, Exception):
        raise entry
    if country not in entry:
        raise ValueError(f"DBnomics returned no {country} series for {provider}/{dataset}")
    return parse({"series": {"docs": [entry[country]]}})
