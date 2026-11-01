"""World Bank commodity prices ("Pink Sheet"), monthly averages in US dollars; no key needed.

The spreadsheet moves to a new address with each monthly update, so its link is looked up
on the commodity-markets page every time. Key is the column header, e.g. "Crude oil, Brent",
"Natural gas, Europe", "Gold", "Copper". The file is downloaded once per run for all of them.
"""

import io
import re
import threading

import openpyxl

from .. import http
from .base import FetchResult, make_series, parse_period

PAGE = "https://www.worldbank.org/en/research/commodity-markets"
_LINK = re.compile(r'href="([^"]*CMO-Historical-Data-Monthly\.xlsx)"')
_cache: dict[str, list] = {}
_lock = threading.Lock()


def source_url(key: str, params: dict | None = None) -> str:
    return PAGE


def find_file_url(html: str) -> str:
    m = _LINK.search(html)
    if not m:
        raise ValueError("World Bank: no link to the monthly price spreadsheet on the commodity-markets page")
    return m.group(1)


def _rows() -> list:
    with _lock:
        if "rows" not in _cache:
            url = find_file_url(http.get(PAGE).text)
            book = openpyxl.load_workbook(io.BytesIO(http.get(url).content), read_only=True, data_only=True)
            _cache["rows"] = list(book["Monthly Prices"].iter_rows(values_only=True))
        return _cache["rows"]


def parse(rows: list, key: str) -> FetchResult:
    header = next((r for r in rows if r and key in r), None)
    if header is None:
        raise ValueError(f"World Bank: no column {key!r}")
    col = header.index(key)
    data = [r for r in rows if r and isinstance(r[0], str) and re.fullmatch(r"\d{4}M\d{2}", r[0])]
    values = [r[col] if isinstance(r[col], (int, float)) else None for r in data]
    return FetchResult(make_series((parse_period(r[0]) for r in data), values))


def fetch(key: str, params: dict | None = None, **_) -> FetchResult:
    return parse(_rows(), key)


def reset() -> None:
    with _lock:
        _cache.clear()
