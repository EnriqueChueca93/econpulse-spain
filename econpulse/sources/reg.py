"""Collective dismissals and temporary layoffs (ERE and ERTE): Ministry of Labour, Regulación de Empleo.

The ministry's Estadística de Regulación de Empleo (REG) publishes a workbook a month ("avance") with the
workers affected by the procedures authorised or communicated that month under articles 51 and 47 of the
Workers' Statute: collective dismissals (despidos colectivos, ERE), contract suspensions and cuts in
working hours (the temporary layoffs known as ERTE). Table REG-R1 has the totals. Monthly workbooks are
read from January 2023; earlier ones were cumulative or laid out differently. Each month's figures are
provisional and the year's workbook later revises them slightly (2025: about 123,300 workers in the
monthly files, 124,900 in the annual one).
Keys: "total", "dismissals", "suspensions", "reductions" (workers affected in the month).
"""

import io
import re
import unicodedata
from functools import lru_cache

import openpyxl
import pandas as pd

from .. import http
from .base import FetchResult, make_series

INCREMENTAL = True
PAGE = "https://www.mites.gob.es/es/estadisticas/condiciones_trabajo_relac_laborales/REG/welcome.htm"
# Monthly workbooks only: e.g. .../reg/reg26ago/reg_08_2026.xlsx (not the reg24ene_dic or reg25 annual ones).
LINK = re.compile(r"https://www\.mites\.gob\.es/estadisticas/reg/reg\d{2}[a-z]{3}/reg_(\d{1,2})_(\d{4})\.xlsx")
FIRST = pd.Timestamp("2023-01-01")
ROWS = {"TRABAJADORES AFECTADOS": "total", "DESPIDOS COLECTIVOS": "dismissals",
        "SUSPENSION DE CONTRATO": "suspensions", "REDUCCION DE JORNADA": "reductions"}


def source_url(key: str, params: dict | None = None) -> str:
    return PAGE


def workbook_links(html: str) -> dict[pd.Timestamp, str]:
    """Month -> URL of that month's workbook, from January 2023."""
    out = {}
    for m in LINK.finditer(html):
        month = pd.Timestamp(int(m[2]), int(m[1]), 1)
        if month >= FIRST:
            out[month] = m[0]
    return out


def _label(text: str) -> str:
    """'Suspensión de contrato (2)' -> 'SUSPENSION DE CONTRATO'."""
    text = re.sub(r"\(\d+\)", "", text)
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    return " ".join(text.upper().split())


def parse_totals(content: bytes) -> dict[str, float]:
    """The month's workers affected, in total and by measure, from table REG-R1."""
    wb = openpyxl.load_workbook(io.BytesIO(content), read_only=True, data_only=True)
    out = {}
    for row in wb["REG-R1"].iter_rows(values_only=True):
        cells = [v for v in row if v is not None]
        if len(cells) > 1 and isinstance(cells[0], str) and isinstance(cells[1], (int, float)):
            key = ROWS.get(_label(cells[0]))
            if key and key not in out:
                out[key] = float(cells[1])
    if "total" not in out:
        raise ValueError("REG-R1 has no total of workers affected")
    return out


@lru_cache(maxsize=None)
def _links() -> dict[pd.Timestamp, str]:
    return workbook_links(http.get(PAGE).text)


@lru_cache(maxsize=None)
def _totals(url: str) -> dict[str, float]:
    return parse_totals(http.get(url).content)


def fetch(key: str, params: dict | None = None, *, since: pd.Timestamp | None = None, **_) -> FetchResult:
    if key not in ROWS.values():
        raise ValueError(f"unknown measure {key!r}; choose from {sorted(ROWS.values())}")
    months = {m: u for m, u in _links().items() if since is None or m >= since}
    if not months:
        raise ValueError("no monthly REG workbook listed")
    values = {m: _totals(u).get(key, 0.0) for m, u in sorted(months.items())}
    return FetchResult(make_series(values.keys(), values.values()), {})
