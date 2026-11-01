"""IMF-style sector tables for Spain, on the section pages and in one Excel workbook.

Each table follows a table in the IMF's latest Article IV staff report for Spain (Country
Report No. 26/102, May 2026), line for line where public data allow. Actual years come from
the statistical agencies (INE, Eurostat, the ECB); projection years from the IMF's World
Economic Outlook database, which publishes a subset of the staff report's lines. A line the
WEO does not publish shows "…" in the projection years, the IMF's own mark for data that are
not available. A few lines are IMF staff estimates in every year (potential output, the output
gap, the structural balance), because no statistical agency publishes them.

The section pages show the last three actual years and the projections, as the IMF does;
the workbook (site/data/econpulse-spain-sector-tables.xlsx) has every table from 2015.
"""

from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Callable

import pandas as pd

from .config import SITE_URL
from .snapshot import MINUS
from .tables import Data

WORKBOOK = "econpulse-spain-sector-tables.xlsx"   # in site/data/
NA = "…"
WEB_ACTUAL_YEARS = 3       # actual years on the section pages, as in the IMF's tables
FIRST_YEAR = 2015          # first year in the workbook
REPORT = "IMF's staff report for the 2026 Article IV consultation with Spain (Country Report No. 26/102, May 2026)"
REPORT_PREFIX = "IMF's 2026 Article IV staff report for Spain"   # for the page notes
REPORT_URL = ("https://www.bde.es/f/webbe/GAP/Secciones/SalaPrensa/InformacionInteres/Otros%20documentos/en/"
              "2026-05-22-FMI-ARTICULO4.pdf")   # the Banco de España's copy (imf.org refuses scripted requests)
WEO_URL = "https://data.imf.org/en/datasets/IMF.RES:WEO"
PERIODS = {"M": 12, "Q": 4}

# ---------------------------------------------------------------- series by year
# An expression maps the build's Data to a series indexed by calendar year (int), or None.
# Each carries the indicator ids it reads, so the page can list them.

Expr = Callable[[Data], "pd.Series | None"]


def _expr(fn, ids) -> Expr:
    fn.ids = frozenset(ids)
    return fn


def published(ind_id: str) -> Expr:
    """An annual series as published."""
    def fn(data):
        s = data.raw(ind_id)
        if s is None:
            return None
        s = s.dropna()
        return pd.Series(s.values, index=s.index.year, dtype=float)
    return _expr(fn, [ind_id])


def average(ind_id: str) -> Expr:
    """The mean of each complete calendar year of a monthly or quarterly series."""
    def fn(data):
        s = data.raw(ind_id)
        if s is None:
            return None
        s = s.dropna()
        g = s.groupby(s.index.year)
        full = g.count() == PERIODS[data.by_id[ind_id].freq]
        return g.mean()[full].astype(float)
    return _expr(fn, [ind_id])


def december(ind_id: str) -> Expr:
    """The December value of a monthly series (end of period)."""
    def fn(data):
        s = data.raw(ind_id)
        if s is None:
            return None
        s = s.dropna()
        s = s[s.index.month == 12]
        return pd.Series(s.values, index=s.index.year, dtype=float)
    return _expr(fn, [ind_id])


def growth(e: Expr) -> Expr:
    """% change on the previous year (consecutive years only)."""
    def fn(data):
        s = e(data)
        if s is None:
            return None
        prev = s.reindex(s.index - 1).values
        return pd.Series((s.values / prev - 1) * 100, index=s.index).dropna()
    return _expr(fn, e.ids)


def combine(op, *exprs: Expr) -> Expr:
    """op applied year by year to several expressions (years they all have)."""
    def fn(data):
        parts = [e(data) for e in exprs]
        if any(p is None for p in parts):
            return None
        frame = pd.concat(parts, axis=1, join="inner")
        return pd.Series(op(*(frame.iloc[:, k] for k in range(len(parts)))), index=frame.index).dropna()
    return _expr(fn, set().union(*(e.ids for e in exprs)))


def share(num: Expr, den: Expr, scale: float = 100) -> Expr:
    return combine(lambda a, b: a / b * scale, num, den)


def scaled(e: Expr, factor: float) -> Expr:
    return combine(lambda a: a * factor, e)


# ---------------------------------------------------------------- table definitions

@dataclass(frozen=True)
class Line:
    label: str
    actual: Expr | None                   # actual years (INE, Eurostat, ECB, or an IMF estimate)
    proj: Expr | None = None              # projection years (IMF WEO); None shows "…"
    indent: int = 0
    decimals: int = 1
    source: str = ""                      # actual years, for the workbook
    proj_source: str = ""                 # projection years, for the workbook
    link: str | None = None               # indicator whose source page the label links to


@dataclass(frozen=True)
class Group:
    label: str


@dataclass(frozen=True)
class SectorTable:
    id: str                               # the block id on its section page
    number: str                           # "1", "2a"...
    title: str                            # as in the IMF's report, without "Spain:"
    unit: str                             # the table's default unit
    section: str                          # the section page that shows it
    sheet: str                            # workbook sheet name (31 characters at most)
    imf_table: str                        # the Article IV table it follows
    rows: list = field(default_factory=list)
    footnotes: list[str] = field(default_factory=list)

    def indicator_ids(self) -> set[str]:
        ids = set()
        for r in self.rows:
            if isinstance(r, Line):
                for e in (r.actual, r.proj):
                    ids |= set(e.ids) if e else set()
        return ids


# Building blocks shared by several lines.
GDP = published("gdp_nominal_annual")
INVESTMENT = published("investment_gdp_annual")
PUBLIC_INVESTMENT = published("public_investment_annual")
NATIONAL_SAVING = share(published("national_saving_annual"), GDP)
# As in the IMF's table, public savings are the government balance plus public investment
# (so capital transfers count as saving), and private savings are the rest of national savings.
PUBLIC_SAVING = combine(lambda b, i: b + i, published("deficit_annual"), PUBLIC_INVESTMENT)
EMPLOYMENT = average("employment_epa")
UNEMPLOYMENT = average("unemployment_epa")
WEO_OUTPUT_GAP = published("fc_imf_output_gap")
WEO_POTENTIAL = growth(combine(lambda y, gap: y / (1 + gap / 100), published("fc_imf_real_gdp"), WEO_OUTPUT_GAP))
WEO_STRUCTURAL = published("fc_imf_structural_balance")

ESTAT, INE, ECB, WEO = "Eurostat", "INE", "ECB", "IMF WEO"
WEO_ESTIMATE = "IMF WEO (staff estimate)"

REAL_SECTOR = SectorTable(
    id="real-sector", number="1", title="Main Economic Indicators", unit="Percent change unless otherwise indicated",
    section="gdp", sheet="T1 Real sector", imf_table="Table 1. Spain: Main Economic Indicators",
    rows=[
        Group("Demand and supply in constant prices"),
        Line("Gross domestic product", published("gdp_growth_annual"), published("fc_imf_gdp"),
             source=ESTAT, proj_source=WEO, link="gdp_growth_annual"),
        Line("Private consumption", published("consumption_private_growth_annual"), indent=1, source=ESTAT,
             link="consumption_private_growth_annual"),
        Line("Public consumption", published("consumption_public_growth_annual"), indent=1, source=ESTAT,
             link="consumption_public_growth_annual"),
        Line("Gross fixed investment", published("investment_growth_annual"), indent=1, source=ESTAT,
             link="investment_growth_annual"),
        Line("Total domestic demand", published("domestic_demand_growth_annual"), indent=1, source=ESTAT,
             link="domestic_demand_growth_annual"),
        Line("Net exports (contribution to growth)",
             combine(lambda x, m: x + m, published("exports_contribution_annual"), published("imports_contribution_annual")),
             indent=1, source=f"{ESTAT}; exports' plus imports' contributions", link="exports_contribution_annual"),
        Line("Exports of goods and services", published("exports_growth_annual"), published("fc_imf_exports_volume"),
             indent=1, source=ESTAT, proj_source=WEO, link="exports_growth_annual"),
        Line("Imports of goods and services", published("imports_growth_annual"), published("fc_imf_imports_volume"),
             indent=1, source=ESTAT, proj_source=WEO, link="imports_growth_annual"),
        Line("Real GDP per capita", published("gdp_per_capita_growth_annual"), growth(published("fc_imf_gdp_per_capita")),
             source=ESTAT, proj_source=WEO, link="gdp_per_capita_growth_annual"),
        Group("Savings-investment balance (percent of GDP)"),
        Line("Gross domestic investment", INVESTMENT, published("fc_imf_investment"), source=ESTAT, proj_source=WEO,
             link="investment_gdp_annual"),
        Line("Private", combine(lambda t, p: t - p, INVESTMENT, PUBLIC_INVESTMENT), indent=1,
             source=f"{ESTAT}; total less public"),
        Line("Public", PUBLIC_INVESTMENT, indent=1, source=f"{ESTAT}; general government fixed investment",
             link="public_investment_annual"),
        Line("National savings", NATIONAL_SAVING, published("fc_imf_saving"), source=ESTAT, proj_source=WEO,
             link="national_saving_annual"),
        Line("Private", combine(lambda n, p: n - p, NATIONAL_SAVING, PUBLIC_SAVING), indent=1,
             source=f"{ESTAT}; national less public"),
        Line("Public", PUBLIC_SAVING, indent=1, source=f"{ESTAT}; government balance plus public investment",
             link="deficit_annual"),
        Line("Foreign savings", combine(lambda i, s: i - s, INVESTMENT, NATIONAL_SAVING),
             combine(lambda i, s: i - s, published("fc_imf_investment"), published("fc_imf_saving")),
             source=f"{ESTAT}; investment less national savings", proj_source=WEO),
        Line("Household saving rate (percent of gross disposable income)", published("household_saving_rate_annual"),
             source=ESTAT, link="household_saving_rate_annual"),
        Line("Potential output 1/", WEO_POTENTIAL, WEO_POTENTIAL, source=WEO_ESTIMATE, proj_source=WEO),
        Line("Output gap (percent of potential output) 1/", WEO_OUTPUT_GAP, WEO_OUTPUT_GAP, source=WEO_ESTIMATE,
             proj_source=WEO),
        Group("Prices"),
        Line("GDP deflator", published("gdp_deflator_growth_annual"), growth(published("fc_imf_deflator")),
             source=ESTAT, proj_source=WEO, link="gdp_deflator_growth_annual"),
        Line("Headline inflation (average) 2/", growth(average("hicp_index")), published("fc_imf_inflation"),
             source=ESTAT, proj_source=WEO, link="hicp_index"),
        Line("Headline inflation (end of period) 2/", growth(december("hicp_index")), published("fc_imf_inflation_eop"),
             source=ESTAT, proj_source=WEO, link="hicp_index"),
        Line("Core inflation (average) 2/", growth(average("hicp_core_np_index")), source=ESTAT,
             link="hicp_core_np_index"),
        Line("Core inflation (end of period) 2/", growth(december("hicp_core_np_index")), source=ESTAT,
             link="hicp_core_np_index"),
        Group("Employment and wages"),
        Line("Unemployment rate (percent of total labor force)", UNEMPLOYMENT, published("fc_imf_unemployment"),
             source=f"{INE} (EPA), average of the quarters", proj_source=WEO, link="unemployment_epa"),
        Line("Labor productivity 3/", growth(share(published("gdp_real_annual"), average("jobs_fte"), 1)),
             source=f"{ESTAT} real GDP over {INE} full-time equivalent jobs", link="jobs_fte"),
        Line("Labor costs 4/", growth(average("labour_cost")), source=f"{INE} (ETCL), average of the quarters",
             link="labour_cost"),
        Line("Employment", growth(EMPLOYMENT), growth(published("fc_imf_employment")),
             source=f"{INE} (EPA), average of the quarters", proj_source=WEO, link="employment_epa"),
        Line("Labor force", growth(combine(lambda e, u: e / (1 - u / 100), EMPLOYMENT, UNEMPLOYMENT)),
             growth(combine(lambda e, u: e / (1 - u / 100), published("fc_imf_employment"), published("fc_imf_unemployment"))),
             source=f"{INE} (EPA): employment and the unemployment rate", proj_source=WEO, link="employment_epa"),
        Group("Balance of payments (percent of GDP)"),
        Line("Trade balance (goods and services)", share(published("trade_balance_annual"), GDP), source=ESTAT,
             link="trade_balance_annual"),
        Line("Current account balance", share(published("current_account_annual"), GDP),
             published("fc_imf_current_account"), source=ESTAT, proj_source=WEO, link="current_account_annual"),
        Line("Net international investment position", published("niip_gdp_annual"), source=ESTAT,
             link="niip_gdp_annual"),
        Group("Public finance (percent of GDP)"),
        Line("General government balance", published("deficit_annual"), published("fc_imf_balance"), source=ESTAT,
             proj_source=WEO, link="deficit_annual"),
        Line("Primary balance 5/", combine(lambda b, paid, rec: b + paid - rec, published("deficit_annual"),
                                           published("interest_annual"), published("interest_received_annual")),
             published("fc_imf_primary_balance"), source=f"{ESTAT}; balance plus interest paid less interest received",
             proj_source=WEO, link="interest_received_annual"),
        Line("Structural balance 1/", WEO_STRUCTURAL, WEO_STRUCTURAL, source=WEO_ESTIMATE, proj_source=WEO),
        Line("Primary structural balance 1/", combine(lambda s, i: s + i, WEO_STRUCTURAL, published("interest_annual")),
             source=f"{WEO_ESTIMATE} plus interest paid ({ESTAT})"),
        Line("General government debt", published("debt_annual"), published("fc_imf_debt"), source=ESTAT,
             proj_source=WEO, link="debt_annual"),
        Group("Memo items"),
        Line("Credit to the private sector 6/", december("private_credit_growth"), source=f"{ECB}, December on December",
             link="private_credit_growth"),
        Line("Nominal GDP (billions of euros)", scaled(GDP, 1e-3), scaled(published("fc_imf_nominal_gdp"), 1e-9),
             source=ESTAT, proj_source=WEO, link="gdp_nominal_annual"),
        Line("Real GDP (billions of 2020 euros)", scaled(published("gdp_real_annual"), 1e-3),
             scaled(published("fc_imf_real_gdp"), 1e-9), source=ESTAT, proj_source=WEO, link="gdp_real_annual"),
    ],
    footnotes=[
        "1/ IMF staff estimates in every year (World Economic Outlook). Potential output is real GDP over one plus "
        "the output gap; the primary structural balance adds interest paid (Eurostat) to the structural balance.",
        "2/ Harmonised Index of Consumer Prices. Core excludes energy and unprocessed food, as in the IMF's table.",
        "3/ Output per full-time equivalent job.",
        "4/ Total labour cost per worker, all sectors (INE's quarterly labour cost survey). The IMF's line covers the "
        "private sector only.",
        "5/ Following the World Economic Outlook, the primary balance excludes interest earnings as well as interest "
        "payments.",
        "6/ Annual growth of bank loans to the private sector (households, firms and non-bank financial "
        "corporations), adjusted for loan sales and securitisation.",
    ],
)

TABLES = [REAL_SECTOR]
BY_ID = {t.id: t for t in TABLES}


# ---------------------------------------------------------------- computing a table

def years(data: Data) -> tuple[int, int] | None:
    """The last actual year (annual real GDP published) and the last projection year (the WEO's horizon)."""
    actual = published("gdp_growth_annual")(data)
    if actual is None or actual.empty:
        return None
    last_actual = int(actual.index.max())
    weo = published("fc_imf_gdp")(data)
    last_proj = int(weo.index.max()) if weo is not None and not weo.empty else last_actual
    return last_actual, max(last_actual, last_proj)


def weo_edition(data: Data) -> str:
    """'October 2026', from the publication date the IMF's data service reports."""
    published_on = data.store.load_catalog().get("fc_imf_gdp", {}).get("published")
    if not published_on:
        return ""
    d = date.fromisoformat(published_on)
    return f"{d:%B %Y}"


def values(table: SectorTable, data: Data, first: int, last: int, last_actual: int) -> list[dict]:
    """Rows of the table: group headings, and lines with a value (or None) for each year."""
    out = []
    for r in table.rows:
        if isinstance(r, Group):
            out.append({"heading": True, "label": r.label})
            continue
        actual = r.actual(data) if r.actual else None
        proj = r.proj(data) if r.proj else None
        cells = []
        for y in range(first, last + 1):
            s = actual if y <= last_actual else proj
            v = s.get(y) if s is not None else None
            cells.append(None if v is None or pd.isna(v) else round(float(v), 6))
        out.append({"heading": False, "line": r, "label": r.label, "cells": cells})
    return out


def fmt(v: float | None, decimals: int = 1) -> str:
    if v is None:
        return NA
    text = f"{abs(v):,.{decimals}f}"
    return MINUS + text if v < 0 and float(text.replace(",", "")) != 0 else text


def web_table(table: SectorTable, data: Data) -> dict | None:
    """The table for its section page: the last actual years and the WEO projections."""
    span = years(data)
    if not span:
        return None
    last_actual, last = span
    first = last_actual - WEB_ACTUAL_YEARS + 1
    rows = []
    for r in values(table, data, first, last, last_actual):
        if r["heading"]:
            rows.append(r)
            continue
        line = r["line"]
        rows.append({"heading": False, "label": r["label"], "label_es": "", "indent": line.indent, "period_note": "",
                     "url": data.by_id[line.link].source_url() if line.link in data.by_id else None,
                     "cells": [fmt(v, line.decimals) for v in r["cells"]]})
    edition = weo_edition(data)
    n_proj = last - last_actual
    return {
        "title": f"Table {table.number}. {table.title}",
        "caption": (f"{table.unit} · actual data to {last_actual}"
                    + (f", IMF projections (World Economic Outlook, {edition}) from {last_actual + 1}" if n_proj else "")),
        "through": str(last_actual),
        "columns": [str(y) for y in range(first, last + 1)],
        "column_notes": [""] * WEB_ACTUAL_YEARS + ["proj."] * n_proj,
        "rows": rows,
        "note": " ".join(table.footnotes) + f" {NA} not available: the IMF's database does not publish the line. "
                f"After the {REPORT_PREFIX}; past years differ where the data have been revised since.",
    }



def table_function(table_id: str):
    """A page-table function for econpulse/pages.py."""
    return lambda data: web_table(BY_ID[table_id], data)


def facts(data: Data) -> list[dict]:
    span = years(data)
    if not span:
        return []
    return [
        {"label": "Actual data", "value": f"to {span[0]}", "sub": "INE, Eurostat, the ECB"},
        {"label": "Projections", "value": f"IMF, {weo_edition(data) or 'WEO'}", "sub": "World Economic Outlook database",
         "url": WEO_URL},
        {"label": "Every table, from 2015", "value": "Excel workbook", "sub": WORKBOOK, "url": f"data/{WORKBOOK}"},
    ]


# ---------------------------------------------------------------- the workbook

def write_workbook(data: Data, path: Path, built: str = "") -> bool:
    """Every table, with history from FIRST_YEAR, as one .xlsx file. False when there are no data yet."""
    from openpyxl import Workbook
    from openpyxl.styles import Alignment, Border, Font, PatternFill, Side

    span = years(data)
    if not span:
        return False
    last_actual, last = span
    edition = weo_edition(data)
    bold, title_font, muted = Font(bold=True), Font(bold=True, size=13), Font(italic=True, color="595959")
    proj_fill = PatternFill("solid", fgColor="EEF2F7")
    rule = Border(bottom=Side(style="thin", color="7F7F7F"))
    year_list = list(range(FIRST_YEAR, last + 1))

    wb = Workbook()
    contents = wb.active
    contents.title = "Contents"
    contents["A1"] = "EconPulse Spain: IMF-style sector tables"
    contents["A1"].font = title_font
    contents["A2"] = f"Built {built}" if built else ""
    contents["A2"].font = muted
    row = 4
    contents.cell(row, 1, "Table").font = bold
    contents.cell(row, 2, "Follows").font = bold
    contents.cell(row, 3, "Shown on").font = bold
    for t in TABLES:
        row += 1
        c = contents.cell(row, 1, f"Table {t.number}. {t.title}")
        c.hyperlink = f"#'{t.sheet}'!A1"
        c.font = Font(color="1F4E79", underline="single")
        contents.cell(row, 2, t.imf_table)
        contents.cell(row, 3, f"{SITE_URL}{t.section}.html#{t.id}")
    row += 2
    notes = [
        f"Lines follow the tables in the {REPORT}, where public data allow.",
        f"Actual years ({FIRST_YEAR}-{last_actual}) come from INE, Eurostat and the ECB; projection years "
        f"({last_actual + 1}-{last}) from the IMF's World Economic Outlook database"
        + (f" ({edition} edition)." if edition else "."),
        f"{NA} means not available: the WEO database does not publish the line (the staff report's own projections "
        "are only in the report), or the statistics do not go back that far.",
        "Potential output, the output gap and the structural balance are IMF staff estimates in every year.",
        "Past years can differ from the staff report's because the data have been revised since it was written.",
        "Figures are as published by each source; anything derived is computed by EconPulse from published series.",
        f"IMF staff report: {REPORT_URL}",
        f"IMF WEO database: {WEO_URL}",
    ]
    contents.cell(row, 1, "Notes").font = bold
    for n in notes:
        row += 1
        contents.cell(row, 1, n)
    contents.column_dimensions["A"].width = 48
    contents.column_dimensions["B"].width = 48
    contents.column_dimensions["C"].width = 60

    for t in TABLES:
        ws = wb.create_sheet(t.sheet)
        ws["A1"] = f"Table {t.number}. Spain: {t.title}"
        ws["A1"].font = title_font
        ws["A2"] = f"({t.unit})"
        ws["A2"].font = muted
        first_proj_col = 2 + (last_actual + 1 - FIRST_YEAR)
        if last > last_actual:
            ws.cell(3, first_proj_col, "Projections").font = bold
        header = [""] + [str(y) for y in year_list] + ["Source, actual years", "Source, projections"]
        for col, h in enumerate(header, start=1):
            c = ws.cell(4, col, int(h) if h.isdigit() else h)
            c.font = bold
            c.border = rule
            c.alignment = Alignment(horizontal="right" if h.isdigit() else "left")
        r_idx = 4
        for r in values(t, data, FIRST_YEAR, last, last_actual):
            r_idx += 1
            label = ws.cell(r_idx, 1, r["label"])
            if r["heading"]:
                label.font = bold
                continue
            line = r["line"]
            label.alignment = Alignment(indent=2 * line.indent)
            for k, v in enumerate(r["cells"]):
                c = ws.cell(r_idx, 2 + k, NA if v is None else v)
                c.number_format = "#,##0." + "0" * line.decimals if line.decimals else "#,##0"
                c.alignment = Alignment(horizontal="right")
                if year_list[k] > last_actual:
                    c.fill = proj_fill
            ws.cell(r_idx, 2 + len(year_list), line.source if line.actual else NA)
            ws.cell(r_idx, 3 + len(year_list), line.proj_source if line.proj else NA)
        r_idx += 2
        ws.cell(r_idx, 1, "Sources: INE, Eurostat and the ECB for actual years; IMF World Economic Outlook"
                + (f" ({edition})" if edition else "") + " for projections; EconPulse calculations.").font = muted
        for n in t.footnotes + [f"{NA} not available."]:
            r_idx += 1
            ws.cell(r_idx, 1, n).font = muted
        ws.column_dimensions["A"].width = 52
        for k in range(len(year_list)):
            ws.column_dimensions[ws.cell(4, 2 + k).column_letter].width = 9
        ws.column_dimensions[ws.cell(4, 2 + len(year_list)).column_letter].width = 44
        ws.column_dimensions[ws.cell(4, 3 + len(year_list)).column_letter].width = 22
        ws.freeze_panes = "B5"
    path.parent.mkdir(parents=True, exist_ok=True)
    wb.save(path)
    return True
