"""Contributory pensions: the Ministry of Labour's statistics bulletin (Boletín de Estadísticas Laborales, BEL).

The bulletin's pension tables (PEN-1 to PEN-31, from the Social Security's own records) come as old-format
.xls workbooks, one a table, e.g. https://www.mites.gob.es/estadisticas/bel/PEN/pen1.xls, refreshed early
each month. In most tables, rows labelled with a year ("2016.....") hold annual averages since 2016, and
after a "2025:" marker, rows labelled with a month ("ABR.....") hold the last 18 months: pensions in force
on the first of the month, or new pensions and pensions ended during it. PEN-31 holds each year's maximum
and minimum amounts since 1990, in euros a year, in two blocks of rows on its first sheet.

Key: the table, e.g. "pen1"; params: sheet (index, default 0), col (the column's index in the sheet, the
year labels being column 0) and block (which run of year rows, default 0). freq A reads the year rows,
freq M the month rows; fetch.py keeps the months already stored, so the monthly history grows from
April 2025 as the bulletin moves on.
"""

import re
from functools import lru_cache

import pandas as pd
import xlrd

from .. import http
from .base import FetchResult, make_series

BASE = "https://www.mites.gob.es/estadisticas/bel/PEN"
INDEX = f"{BASE}/index.htm"
MONTHS = {"ENE": 1, "FEB": 2, "MAR": 3, "ABR": 4, "MAY": 5, "JUN": 6,
          "JUL": 7, "AGO": 8, "SEP": 9, "OCT": 10, "NOV": 11, "DIC": 12}
_YEAR_ROW = re.compile(r"^(\d{4})(?:\.0)?\.*$")     # "2016.........." (or 2016.0 in PEN-31)
_YEAR_MARK = re.compile(r"^(\d{4}):$")             # "2026:" starts that year's months
_MONTH_ROW = re.compile(r"^([A-Z]{3})\.+$")         # "SEP..........."


def source_url(key: str, params: dict | None = None) -> str:
    return INDEX


def _number(v) -> float | None:
    if isinstance(v, (int, float)):
        return float(v)
    return None   # "-" (none in that scheme or year) or blank


def parse(content: bytes, sheet: int = 0, col: int = 1, block: int = 0) -> dict[str, pd.Series]:
    """A column of one sheet as {"A": annual values, "M": monthly values}."""
    sh = xlrd.open_workbook(file_contents=content).sheet_by_index(sheet)
    annual, monthly = {}, {}
    year, blocks, in_years = None, -1, False
    for r in range(sh.nrows):
        label = str(sh.cell_value(r, 0)).strip()
        value = _number(sh.cell_value(r, col)) if col < sh.ncols else None
        if m := _YEAR_ROW.match(label):
            if not in_years:
                blocks, in_years = blocks + 1, True
            if blocks == block and value is not None:
                annual[pd.Timestamp(int(m[1]), 1, 1)] = value
            continue
        in_years = False
        if m := _YEAR_MARK.match(label):
            year = int(m[1])
        elif (m := _MONTH_ROW.match(label)) and m[1] in MONTHS and year and value is not None:
            monthly[pd.Timestamp(year, MONTHS[m[1]], 1)] = value
    return {"A": pd.Series(annual, dtype=float), "M": pd.Series(monthly, dtype=float)}


@lru_cache(maxsize=None)
def _workbook(table: str) -> bytes:
    return http.get(f"{BASE}/{table}.xls").content


def fetch(key: str, params: dict | None = None, *, freq: str | None = None, **_) -> FetchResult:
    params = params or {}
    if freq not in ("A", "M"):
        raise ValueError(f"BEL tables have annual and monthly rows, not {freq!r}")
    found = parse(_workbook(key), int(params.get("sheet", 0)), int(params.get("col", 1)), int(params.get("block", 0)))[freq]
    if found.empty:
        raise ValueError(f"BEL {key}: no {'annual' if freq == 'A' else 'monthly'} values in column {params.get('col', 1)}")
    found = found.sort_index()
    return FetchResult(make_series(found.index, found.to_numpy()), {"source_name": f"BEL {key.upper()}"})
