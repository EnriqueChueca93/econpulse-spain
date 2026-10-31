"""Seguridad Social: average monthly registrations (afiliados medios), total system.

The ministry publishes the full monthly history since 2001 as a small spreadsheet
("19_Serie afiliación media por regímenes (Total Sistema).xlsx") linked from its
statistics page. We look the link up on that page each time and fall back to the
last known address if the page layout changes.

Key is the column header to read, e.g. "TOTAL SISTEMA".
"""

import io
import re
from urllib.parse import urljoin

import openpyxl
import pandas as pd

from .. import http
from .base import FetchResult, make_series

PAGE = ("https://www.seg-social.es/wps/portal/wss/internet/EstadisticasPresupuestosEstudios/"
        "Estadisticas/EST8/EST10/EST290/EST291")
FALLBACK_FILE = ("https://www.seg-social.es/wps/wcm/connect/wss/5ccf558a-868f-48b3-b832-04fe9f524960/"
                 "19_Serie+afiliaci%C3%B3n+media+por+reg%C3%ADmenes+%28Total+Sistema%29.xlsx?MOD=AJPERES")
_LINK = re.compile(r'href="([^"]*Serie\+afiliaci[^"]*\.xlsx[^"]*)"', re.IGNORECASE)

MONTHS = {
    "enero": 1, "febrero": 2, "marzo": 3, "abril": 4, "mayo": 5, "junio": 6, "julio": 7,
    "agosto": 8, "septiembre": 9, "setiembre": 9, "octubre": 10, "noviembre": 11, "diciembre": 12,
}
_PERIOD = re.compile(r"^\s*([a-záéíóú]+)\s+(\d{4})\s*$", re.IGNORECASE)


def source_url(key: str, params: dict | None = None) -> str:
    return PAGE


def find_file_url(html: str) -> str | None:
    m = _LINK.search(html)
    return urljoin(PAGE, m.group(1).replace("&amp;", "&")) if m else None


def parse(content: bytes, column: str) -> pd.Series:
    ws = openpyxl.load_workbook(io.BytesIO(content), read_only=True, data_only=True).worksheets[0]
    col, dates, values = None, [], []
    for row in ws.iter_rows(values_only=True):
        if col is None:
            for i, cell in enumerate(row):
                if isinstance(cell, str) and cell.strip().upper() == column.upper():
                    col = i
            continue
        label = row[0]
        m = _PERIOD.match(label) if isinstance(label, str) else None
        if m and m.group(1).lower() in MONTHS and isinstance(row[col], (int, float)):
            dates.append(pd.Timestamp(int(m.group(2)), MONTHS[m.group(1).lower()], 1))
            values.append(row[col])
    if col is None:
        raise ValueError(f"Seguridad Social: column {column!r} not found in spreadsheet")
    return make_series(dates, values)


def fetch(key: str, params: dict | None = None, **_) -> FetchResult:
    try:
        url = find_file_url(http.get(PAGE).text) or FALLBACK_FILE
    except Exception:  # noqa: BLE001 - the page is only used to find the link
        url = FALLBACK_FILE
    return FetchResult(parse(http.get(url).content, key), {"source_file": url.split("?")[0]})
