"""Seguridad Social: average monthly registrations by sector and type of work, from the yearly workbooks.

The ministry publishes one workbook a year on its statistics page ("Afiliación 2026_CNAE25.xlsx",
"Afiliación 2025.xlsx"...), each holding that year's months. Its table of seasonally adjusted averages
by employment relationship and sector ("Tabla_desestacionalizados"; "Afiliados_deset" before 2025) gives,
for every month, the average number registered (SALDOS) and the ministry's own seasonally adjusted figure
(Desestacionalizado), from 2022. From 2026 the sectors follow the new activity classification (CNAE-2025).

Key: "<raw|sa>:<group>", group one of total, agriculture, industry, construction, services, employees,
self_employed. Only the years since the requested date are downloaded, and each workbook once per run.
"""

import functools
import io
import re
import unicodedata
from urllib.parse import unquote, urljoin

import openpyxl
import pandas as pd

from .. import http
from .base import FetchResult, make_series

PAGE = ("https://www.seg-social.es/wps/portal/wss/internet/EstadisticasPresupuestosEstudios/"
        "Estadisticas/EST8/EST10/EST290/EST291")
FIRST_YEAR = 2022   # the first workbook with the adjusted table by sector
INCREMENTAL = True  # given `since`, only the workbooks from that year on are downloaded
SHEETS = ("Tabla_desestacionalizados", "Afiliados_deset")
GROUPS = {"total": "total", "agriculture": "agricultura, ganaderia y pesca", "industry": "industria",
          "construction": "construccion", "services": "servicios", "employees": "asalariados",
          "self_employed": "no asalariados"}
COLUMNS = {"raw": "saldos", "sa": "desestacionalizado"}
_LINK = re.compile(r'href="([^"]+\.xlsx[^"]*)"', re.IGNORECASE)
_YEAR = re.compile(r"Afiliaci[^/]*?(20\d\d)", re.IGNORECASE)


def source_url(key: str, params: dict | None = None) -> str:
    return PAGE


def _plain(text) -> str:
    """Lower case without accents, for matching the workbook's labels."""
    text = unicodedata.normalize("NFKD", str(text or ""))
    return "".join(c for c in text if not unicodedata.combining(c)).strip().lower()


def workbook_links(html: str) -> dict[int, str]:
    """The yearly workbooks on the statistics page: {year: url}."""
    links = {}
    for href in _LINK.findall(html):
        m = _YEAR.search(unquote(href).replace("+", " "))
        if m and "serie" not in _plain(unquote(href)):
            links[int(m.group(1))] = urljoin(PAGE, href.replace("&amp;", "&"))
    return links


def parse_table(content: bytes) -> pd.DataFrame:
    """The adjusted-by-sector table of one workbook: one row per month and group, raw and adjusted."""
    wb = openpyxl.load_workbook(io.BytesIO(content), read_only=True, data_only=True)
    sheet = next((wb[s] for s in SHEETS if s in wb.sheetnames), None)
    if sheet is None:
        raise ValueError("Seguridad Social: no table of adjusted registrations by sector in the workbook")
    rows = sheet.iter_rows(values_only=True)
    header = [_plain(h) for h in next(rows)]
    at = {name: header.index(name) for name in ("periodo", "sector", "saldos", "desestacionalizado")}
    records = []
    for r in rows:
        period = str(r[at["periodo"]] or "").strip()
        if not re.fullmatch(r"20\d{4}", period):
            continue
        records.append({"date": pd.Timestamp(int(period[:4]), int(period[4:]), 1), "group": _plain(r[at["sector"]]),
                        "saldos": r[at["saldos"]], "desestacionalizado": r[at["desestacionalizado"]]})
    return pd.DataFrame.from_records(records)


@functools.lru_cache(maxsize=16)
def _table(url: str) -> pd.DataFrame:
    return parse_table(http.get(url, timeout=120).content)


@functools.lru_cache(maxsize=1)
def _links() -> dict[int, str]:
    return workbook_links(http.get(PAGE).text)


def fetch(key: str, params: dict | None = None, since: pd.Timestamp | None = None, **_) -> FetchResult:
    column, _, group = key.partition(":")
    if column not in COLUMNS or group not in GROUPS:
        raise ValueError(f"Seguridad Social: unknown key {key!r}")
    years = sorted(y for y in _links() if y >= max(FIRST_YEAR, since.year if since is not None else FIRST_YEAR))
    if not years:
        raise ValueError("Seguridad Social: no yearly workbooks found on the statistics page")
    frames = [_table(_links()[y]) for y in years]
    df = pd.concat(frames, ignore_index=True)
    df = df[df["group"] == GROUPS[group]].dropna(subset=[COLUMNS[column]]).sort_values("date")
    df = df.drop_duplicates("date", keep="last")
    if df.empty:
        raise ValueError(f"Seguridad Social: no data for {key!r}")
    return FetchResult(make_series(df["date"], df[COLUMNS[column]].astype(float)), {"source_name": "Afiliación media"})
