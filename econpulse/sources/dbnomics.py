"""DBnomics (db.nomics.world): an open mirror of official statistics, run by the Banque de
France and CEPREMAP; no key needed. Used where the original agency needs a key (US BEA).

Key is "<provider>/<dataset>/<series>", e.g. BEA/NIPA-T10111/A191RO-Q (US real GDP, % change on a year earlier).
"""

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


def fetch(key: str, params: dict | None = None, **_) -> FetchResult:
    return parse(http.get(f"{BASE}/{key}", params={"observations": 1}).json())
