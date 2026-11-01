"""Seguridad Social: average monthly registrations by sector and type of work, from the yearly workbooks.

The ministry publishes one workbook a year on its statistics page ("Afiliación 2026_CNAE25.xlsx",
"Afiliación 2025.xlsx"...), each holding that year's months. Its table of seasonally adjusted averages
by employment relationship and sector ("Tabla_desestacionalizados"; "Afiliados_deset" before 2025) gives,
for every month, the average number registered (SALDOS) and the ministry's own seasonally adjusted figure
(Desestacionalizado), from 2022. Its table by two-digit activity ("Tabla_2"; "DATOS PEST2" before 2025)
gives the general scheme and the self-employed by division, from 2021. From 2026 activities follow the new
classification (CNAE-2025): the sectors and the groups of divisions used here keep their boundaries, but
some divisions moved within them (motor vehicle trade, division 45, went into 46 and 47).

Keys: "<raw|sa>:<group>", group one of total, agriculture, industry, construction, services, employees,
self_employed; or "cnae:<divisions>", e.g. "cnae:10-12", "cnae:86", "cnae:58-63,85" or "cnae:all", the sum
of those divisions as published. Only the years since the requested date are downloaded, and each workbook
once per run.

Two moves in CNAE-2025 cross the groups used here: motor vehicle repair went from division 45 to 95, and real
estate development from construction (41) to real estate (68). Params {bridge: "-95"} or {bridge: "+95"} link
a series across the change: the registrations moved are estimated as the destination's December-to-January
jump in 2026 less the same change a year earlier (its seasonal swing), and that number is taken from ("-") or
added to ("+") the series before 2026, so the comparison with a year earlier stays like for like.
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
FIRST_YEAR_CNAE = 2021   # the first workbook with the table by division
CNAE_SHEETS = ("Tabla_2", "DATOS PEST2")
CHANGE = pd.Timestamp("2026-01-01")   # the switch to CNAE-2025
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


def _workbook(content: bytes):
    return openpyxl.load_workbook(io.BytesIO(content), read_only=True, data_only=True)


def parse_table(content: bytes) -> pd.DataFrame:
    """The adjusted-by-sector table of one workbook: one row per month and group, raw and adjusted."""
    wb = _workbook(content)
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


def parse_divisions(content: bytes) -> pd.DataFrame:
    """The table by two-digit activity: registrations by month and division, summed over schemes and sexes."""
    wb = _workbook(content)
    sheet = next((wb[s] for s in CNAE_SHEETS if s in wb.sheetnames), None)
    if sheet is None:
        raise ValueError("Seguridad Social: no table by activity in the workbook")
    rows = sheet.iter_rows(values_only=True)
    header = [_plain(h) for h in next(rows)]
    period_at, value_at = header.index("periodo"), header.index("saldos")
    code_at = next(i for i, h in enumerate(header) if h.startswith("cnae"))
    records = []
    for r in rows:
        period = str(r[period_at] or "").strip()
        if not re.fullmatch(r"20\d{4}", period) or r[value_at] is None:
            continue
        records.append((pd.Timestamp(int(period[:4]), int(period[4:]), 1), str(r[code_at]).strip().zfill(2),
                        float(r[value_at])))
    df = pd.DataFrame.from_records(records, columns=["date", "code", "value"])
    return df.groupby(["date", "code"], as_index=False)["value"].sum()


def divisions(spec: str) -> set[str] | None:
    """'10-12,86' -> {'10', '11', '12', '86'}; 'all' -> None (every division)."""
    if spec == "all":
        return None
    out = set()
    for part in spec.split(","):
        lo, _, hi = part.strip().partition("-")
        out |= {f"{n:02d}" for n in range(int(lo), int(hi or lo) + 1)}
    return out


@functools.lru_cache(maxsize=16)
def _content(url: str) -> bytes:
    return http.get(url, timeout=120).content


@functools.lru_cache(maxsize=16)
def _table(url: str) -> pd.DataFrame:
    return parse_table(_content(url))


@functools.lru_cache(maxsize=16)
def _divisions_table(url: str) -> pd.DataFrame:
    return parse_divisions(_content(url))


@functools.lru_cache(maxsize=1)
def _links() -> dict[int, str]:
    return workbook_links(http.get(PAGE).text)


def moved(series: pd.Series) -> float:
    """Registrations reclassified into these divisions at the change: the December-to-January jump less the
    same change a year earlier."""
    year = CHANGE.year
    at = lambda y, m: float(series[pd.Timestamp(y, m, 1)])
    return (at(year, 1) - at(year - 1, 12)) - (at(year - 1, 1) - at(year - 2, 12))


def _divisions_sum(codes: set[str] | None, years: list[int]) -> pd.Series:
    df = pd.concat([_divisions_table(_links()[y]) for y in years], ignore_index=True)
    if codes is not None:
        df = df[df["code"].isin(codes)]
    return df.groupby("date")["value"].sum().sort_index()


def _fetch_divisions(spec: str, since: pd.Timestamp | None, bridge: str | None = None) -> FetchResult:
    codes = divisions(spec)
    years = sorted(y for y in _links() if y >= max(FIRST_YEAR_CNAE, since.year if since is not None else FIRST_YEAR_CNAE))
    if not years:
        raise ValueError("Seguridad Social: no yearly workbooks found on the statistics page")
    sums = _divisions_sum(codes, years)
    if sums.empty:
        raise ValueError(f"Seguridad Social: no data for divisions {spec!r}")
    if bridge and (sums.index < CHANGE).any():
        sign, destination = bridge[0], bridge[1:]
        around = [y for y in range(CHANGE.year - 2, CHANGE.year + 1) if y in _links()]
        shift = moved(_divisions_sum(divisions(destination), around))
        sums = sums.copy()
        sums[sums.index < CHANGE] += shift if sign == "+" else -shift
    return FetchResult(make_series(sums.index, sums.values), {"source_name": "Afiliación media por actividad"})


def fetch(key: str, params: dict | None = None, since: pd.Timestamp | None = None, **_) -> FetchResult:
    column, _, group = key.partition(":")
    if column == "cnae":
        return _fetch_divisions(group, since, (params or {}).get("bridge"))
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
    series = pd.Series(df[COLUMNS[column]].astype(float).values, index=pd.DatetimeIndex(df["date"]))
    bridge = (params or {}).get("bridge")
    if bridge and (series.index < CHANGE).any():   # the sector table changed classification too
        sign, destination = bridge[0], bridge[1:]
        around = [y for y in range(CHANGE.year - 2, CHANGE.year + 1) if y in _links()]
        shift = moved(_divisions_sum(divisions(destination), around))
        series[series.index < CHANGE] += shift if sign == "+" else -shift
    return FetchResult(make_series(series.index, series.values), {"source_name": "Afiliación media"})
