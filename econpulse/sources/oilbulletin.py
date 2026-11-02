"""European Commission Weekly Oil Bulletin: pump prices of petrol and diesel in every EU country.

The bulletin's page links one workbook with the whole history, weekly since 2005: a sheet of prices with
duties and taxes and one of prices before them, in euros per 1,000 litres, one column per country and product
("ES_price_with_tax_euro95", "EUR_price_wo_tax_diesel"; EUR is the euro area, EU the EU, both weighted averages).
Prices are those of each Monday. The workbook's address changes when it is replaced, so it is read from the
page each run, and the workbook is read once per run for every series that uses it.

Key: the column's name. Values are returned in euros per litre.
"""

import html
import io
import re
import threading
from datetime import datetime
from urllib.parse import urljoin

import openpyxl

from .. import http
from .base import FetchResult, make_series

PAGE = "https://energy.ec.europa.eu/data-and-analysis/weekly-oil-bulletin_en"
_HISTORY = re.compile(r'href="([^"]*/document/download/[^"]*Prices_History[^"]*\.xlsx[^"]*)"', re.I)
SHEETS = {"with_tax": "Prices with taxes", "wo_tax": "Prices wo taxes"}

_lock = threading.Lock()
_cache: dict = {}   # the workbook is read once per run, for all the bulletin's series


def source_url(key: str, params: dict | None = None) -> str:
    return PAGE


def history_link(page_html: str) -> str:
    m = _HISTORY.search(page_html)
    if not m:
        raise ValueError("no prices-history workbook linked on the Weekly Oil Bulletin page")
    return urljoin(PAGE, html.unescape(m.group(1)))


def parse_sheet(ws) -> dict[str, list[tuple[datetime, float]]]:
    """{column name: [(date, value), ...]}: the first row names the columns, the first column dates the
    weeks; rows without a date (headings, units, notes at the foot) are left out."""
    rows = ws.iter_rows(values_only=True)
    names = next(rows)
    out: dict[str, list] = {str(n): [] for n in names[1:] if n}
    for row in rows:
        if not row or not isinstance(row[0], datetime):
            continue
        for name, value in zip(names[1:], row[1:]):
            if name and isinstance(value, (int, float)):
                out[str(name)].append((row[0], float(value)))
    return out


def parse_workbook(content: bytes) -> dict[str, list[tuple[datetime, float]]]:
    wb = openpyxl.load_workbook(io.BytesIO(content), read_only=True, data_only=True)
    columns = {}
    for sheet in SHEETS.values():
        if sheet not in wb.sheetnames:
            raise ValueError(f"no sheet {sheet!r} in the Weekly Oil Bulletin workbook")
        columns.update(parse_sheet(wb[sheet]))
    return columns


def _workbook() -> dict:
    with _lock:
        if "error" in _cache:
            raise _cache["error"]
        if "columns" not in _cache:
            try:
                url = history_link(http.get(PAGE).text)
                _cache.update(columns=parse_workbook(http.get(url).content), url=url)
            except Exception as e:
                _cache["error"] = e
                raise
        return _cache


def clear_cache() -> None:
    with _lock:
        _cache.clear()


def fetch(key: str, params: dict | None = None, **_) -> FetchResult:
    book = _workbook()
    if key not in book["columns"]:
        raise ValueError(f"no column {key!r} in the Weekly Oil Bulletin workbook")
    points = book["columns"][key]
    return FetchResult(make_series((d for d, _ in points), (v / 1000 for _, v in points)), {"url": book["url"]})
