"""IMF-style sector tables for Spain, on the section pages and in one Excel workbook.

Each table follows a table in the IMF's latest Article IV staff report for Spain (Country
Report No. 26/102, May 2026), line for line where public data allow. Actual years come from
the statistical agencies (INE, Eurostat, the ECB); projection years from the IMF's World
Economic Outlook database, which publishes a subset of the staff report's lines. A line the
WEO does not publish shows "…" in the projection years, the IMF's own mark for data that are
not available. A few lines are IMF staff estimates in every year (potential output, the output
gap, the structural balance, net debt), because no statistical agency publishes them.

The debt sustainability analysis has two tables: the IMF's baseline debt decomposition, on the
same sources, and the European Commission's baseline and stress tests from its Debt Sustainability
Monitor (econpulse/fiscal_baseline.json), because the IMF's own stress tests are not published as data.

The section pages show the last three actual years and the projections, as the IMF does;
the workbook (site/data/econpulse-spain-sector-tables.xlsx) has every table from 2015.
"""

from dataclasses import dataclass, field, replace
from datetime import date
from pathlib import Path
from typing import Callable

import pandas as pd

from . import fiscal
from .config import SITE_URL
from .snapshot import MINUS, period_label
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


def year_end(ind_id: str) -> Expr:
    """The last observation of each complete year (December, or the fourth quarter)."""
    def fn(data):
        s = data.raw(ind_id)
        if s is None:
            return None
        s = s.dropna()
        last = s.groupby(s.index.year).tail(1)
        last = last[last.index.month == (10 if data.by_id[ind_id].freq == "Q" else 12)]
        return pd.Series(last.values, index=last.index.year, dtype=float)
    return _expr(fn, [ind_id])


def annual_sum(ind_id: str) -> Expr:
    """The total of each complete calendar year of a monthly or quarterly series."""
    def fn(data):
        s = data.raw(ind_id)
        if s is None:
            return None
        s = s.dropna()
        g = s.groupby(s.index.year)
        full = g.count() == PERIODS[data.by_id[ind_id].freq]
        return g.sum()[full].astype(float)
    return _expr(fn, [ind_id])


def indexed(e: Expr, base: int) -> Expr:
    """The series with the base year = 100."""
    def fn(data):
        s = e(data)
        return None if s is None or base not in s.index else s / s[base] * 100
    return _expr(fn, e.ids)


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


def total(*exprs: Expr) -> Expr:
    return combine(lambda *xs: sum(xs), *exprs)


def less(e: Expr, *exprs: Expr) -> Expr:
    """The first expression less the others."""
    return combine(lambda a, *xs: a - sum(xs), e, *exprs)


def lag(e: Expr) -> Expr:
    """The previous year's value."""
    def fn(data):
        s = e(data)
        return None if s is None else pd.Series(s.values, index=s.index + 1)
    return _expr(fn, e.ids)


def diff(e: Expr) -> Expr:
    return less(e, lag(e))


def dsm(*path: str) -> Expr:
    """A series from the Commission's Debt Sustainability Monitor (econpulse/fiscal_baseline.json)."""
    def fn(data):
        if "fiscal_baseline" not in data.cache:
            data.cache["fiscal_baseline"] = fiscal.load() if fiscal.BASELINE_FILE.exists() else {}
        node = data.cache["fiscal_baseline"].get("dsm")
        for key in path:
            node = node.get(key) if isinstance(node, dict) else None
        if not node:
            return None
        return pd.Series({int(y): float(v) for y, v in node.items() if v is not None}, dtype=float).sort_index()
    return _expr(fn, [])


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
    id: str
    label: str                            # "Table 1", "Table 2a", "DSA 1"...
    title: str                            # as in the IMF's report, without "Spain:"
    unit: str                             # the table's default unit
    section: str                          # the section page that shows it
    block: str                            # the block on that page
    sheet: str                            # workbook sheet name (31 characters at most)
    imf_table: str                        # the Article IV table it follows
    rows: list = field(default_factory=list)
    footnotes: list[str] = field(default_factory=list)
    kind: str = "weo"                     # "weo": statistics then WEO projections; "dsm": the Commission's DSM;
                                          # "actual": no projections
    web_actual: int = WEB_ACTUAL_YEARS    # actual years shown on the page
    first_year: int = FIRST_YEAR          # first year in the workbook
    sources: str = ""                     # the sources line, where the kind's default does not fit
    freq: str = "A"                       # "Q" or "M": a quarterly or monthly view (no projections)

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
    id="real-sector", label="Table 1", title="Main Economic Indicators", unit="Percent change unless otherwise indicated",
    section="gdp", block="real-sector", sheet="T1 Real sector", imf_table="Table 1. Spain: Main Economic Indicators",
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

# ---------------------------------------------------------------- general government operations (Tables 2a, 2b)
# Eurostat's ESA 2010 accounts for the general government, in millions of euros; Table 2a shows them in
# billions, Table 2b in % of GDP. The WEO projects only the totals.

def _gg(code: str) -> Expr:
    return published(code)


TR, TE, B9 = _gg("gg_revenue_eur"), _gg("gg_spending_eur"), _gg("gg_balance_eur")
D2, D5, D91, D61 = _gg("gg_taxes_production_eur"), _gg("gg_taxes_income_eur"), _gg("gg_capital_taxes_eur"), \
    _gg("gg_social_contributions_eur")
D1, P2, P5, D9 = _gg("gg_compensation_eur"), _gg("gg_goods_services_eur"), _gg("gg_capital_formation_eur"), \
    _gg("gg_capital_transfers_eur")
INTEREST_PAID, INTEREST_RECEIVED = _gg("gg_interest_paid_eur"), _gg("gg_interest_received_eur")
BENEFITS, SUBSIDIES, NONPRODUCED = _gg("gg_social_benefits_eur"), _gg("gg_subsidies_eur"), _gg("gg_nonproduced_eur")
TAXES = total(D2, D5, D91)
EXPENSE = less(TE, NONPRODUCED)
CAPITAL = total(P5, D9)
OTHER_EXPENSE = less(EXPENSE, D1, P2, CAPITAL, INTEREST_PAID, BENEFITS)
PRIMARY_EUR = combine(lambda b, paid, rec: b + paid - rec, B9, INTEREST_PAID, INTEREST_RECEIVED)
DEBT_EUR = _gg("gg_debt_eur")

# label, indent, Eurostat (€ mn), WEO in euros, WEO in % of GDP, source note, linked indicator
GG_LINES = [
    ("Revenue", 0, TR, "fc_imf_revenue", "fc_imf_revenue_gdp", "TR", "gg_revenue_eur"),
    ("Taxes", 1, TAXES, None, None, "D2 + D5 + D91", None),
    ("Indirect taxes", 2, D2, None, None, "D2", "gg_taxes_production_eur"),
    ("o.w. VAT", 3, _gg("gg_vat_eur"), None, None, "D211", "gg_vat_eur"),
    ("o.w. Excise", 3, _gg("gg_excise_eur"), None, None, "D214", "gg_excise_eur"),
    ("Direct taxes", 2, D5, None, None, "D5", "gg_taxes_income_eur"),
    ("o.w. Private households 2/", 3, _gg("gg_tax_households_eur"), None, None, "D51A", "gg_tax_households_eur"),
    ("o.w. Corporate 2/", 3, _gg("gg_tax_corporate_eur"), None, None, "D51B", "gg_tax_corporate_eur"),
    ("Capital tax", 2, D91, None, None, "D91", "gg_capital_taxes_eur"),
    ("Social contributions", 1, D61, None, None, "D61", "gg_social_contributions_eur"),
    ("Other revenue", 1, less(TR, TAXES, D61), None, None, "TR less taxes and social contributions", None),
    ("Expenditure", 0, TE, "fc_imf_spending", "fc_imf_spending_gdp", "TE", "gg_spending_eur"),
    ("Expense", 1, EXPENSE, None, None, "TE less NP", None),
    ("Compensation of employees", 2, D1, None, None, "D1", "gg_compensation_eur"),
    ("Use of goods and services", 2, P2, None, None, "P2", "gg_goods_services_eur"),
    ("Capital 3/", 2, CAPITAL, None, None, "P5 + D9", None),
    ("o.w. Gross capital formation", 3, P5, None, None, "P5", "gg_capital_formation_eur"),
    ("o.w. Capital transfers and investment aid", 3, D9, None, None, "D9", "gg_capital_transfers_eur"),
    ("Interest", 2, INTEREST_PAID, None, None, "D41", "gg_interest_paid_eur"),
    ("Social benefits", 2, BENEFITS, None, None, "D62 + D632", "gg_social_benefits_eur"),
    ("Other expense", 2, OTHER_EXPENSE, None, None, "Expense less the lines above", None),
    ("Subsidies", 3, SUBSIDIES, None, None, "D3", "gg_subsidies_eur"),
    ("Other", 3, less(OTHER_EXPENSE, SUBSIDIES), None, None, "Other expense less subsidies", None),
    ("Net acquisition of nonfinancial assets 3/", 1, NONPRODUCED, None, None, "NP", "gg_nonproduced_eur"),
    ("Gross operating balance", 0, less(TR, EXPENSE), None, None, "Revenue less expense", None),
    ("Net lending / borrowing", 0, B9, "fc_imf_balance_eur", "fc_imf_balance", "B9", "gg_balance_eur"),
]


def _gg_rows(in_gdp: bool) -> list:
    rows = []
    for label, indent, expr, weo_eur, weo_gdp, code, link in GG_LINES:
        actual = share(expr, GDP) if in_gdp else scaled(expr, 1e-3)
        weo = weo_gdp if in_gdp else weo_eur
        proj = (published(weo) if in_gdp else scaled(published(weo), 1e-9)) if weo else None
        rows.append(Line(label, actual, proj, indent=indent, source=f"{ESTAT}, ESA 2010: {code}",
                         proj_source=WEO if weo else "", link=link))
    return rows


GG_FOOTNOTES = [
    "1/ General government, ESA 2010 accrual accounts (Eurostat), with the IMF's grouping. The World Economic "
    "Outlook projects only revenue, expenditure, the balances and debt.",
    "2/ Eurostat's detailed tax receipts. The IMF's two sub-lines come from another source: they add up to more "
    "than its direct taxes.",
    "3/ As in the IMF's table, capital spending is gross capital formation plus capital transfers, and net "
    "acquisition of nonfinancial assets covers nonproduced assets (land, licences) only.",
    "4/ Following the World Economic Outlook, the primary balance excludes interest earnings as well as interest "
    "payments.",
]

FISCAL_EUR = SectorTable(
    id="fiscal-eur", label="Table 2a", title="General Government Operations",
    unit="Billions of euros, unless otherwise indicated", section="fiscal", block="government-operations",
    sheet="T2a Fiscal EUR bn", imf_table="Table 2a. Spain: General Government Operations (billions of euros)",
    rows=_gg_rows(False) + [
        Group("Memorandum items"),
        Line("Primary balance 4/", scaled(PRIMARY_EUR, 1e-3), scaled(published("fc_imf_primary_balance_eur"), 1e-9),
             source=f"{ESTAT}; B9 plus D41 paid less D41 received", proj_source=WEO, link="gg_interest_received_eur"),
        Line("General government gross debt (Maastricht)", scaled(DEBT_EUR, 1e-3),
             scaled(published("fc_imf_debt_eur"), 1e-9), source=ESTAT, proj_source=WEO, link="gg_debt_eur"),
        Line("Nominal GDP", scaled(GDP, 1e-3), scaled(published("fc_imf_nominal_gdp"), 1e-9), source=ESTAT,
             proj_source=WEO, link="gdp_nominal_annual"),
    ],
    footnotes=GG_FOOTNOTES,
)

FISCAL_GDP = SectorTable(
    id="fiscal-gdp", label="Table 2b", title="General Government Operations",
    unit="Percent of GDP, unless otherwise indicated", section="fiscal", block="government-operations",
    sheet="T2b Fiscal % GDP", imf_table="Table 2b. Spain: General Government Operations (percent of GDP)",
    rows=_gg_rows(True) + [
        Group("Memorandum items"),
        Line("Primary balance 4/", share(PRIMARY_EUR, GDP), published("fc_imf_primary_balance"),
             source=f"{ESTAT}; B9 plus D41 paid less D41 received", proj_source=WEO, link="gg_interest_received_eur"),
        Line("Primary structural balance 5/", combine(lambda s, i: s + i, WEO_STRUCTURAL, share(INTEREST_PAID, GDP)),
             source=f"{WEO_ESTIMATE} plus interest paid ({ESTAT})"),
        Line("Structural balance 5/", WEO_STRUCTURAL, WEO_STRUCTURAL, source=WEO_ESTIMATE, proj_source=WEO),
        Line("General government gross debt (Maastricht)", share(DEBT_EUR, GDP), published("fc_imf_debt"),
             source=ESTAT, proj_source=WEO, link="gg_debt_eur"),
        Line("Net debt 5/", published("fc_imf_net_debt"), published("fc_imf_net_debt"), source=WEO_ESTIMATE,
             proj_source=WEO),
        Line("Central government net lending", share(published("cg_balance_eur"), GDP), source=ESTAT,
             link="cg_balance_eur"),
        Line("Output gap 5/", WEO_OUTPUT_GAP, WEO_OUTPUT_GAP, source=WEO_ESTIMATE, proj_source=WEO),
    ],
    footnotes=GG_FOOTNOTES + ["5/ IMF staff estimates in every year (World Economic Outlook). The primary structural "
                              "balance adds interest paid (Eurostat) to the structural balance."],
)

# ---------------------------------------------------------------- debt sustainability (DSA 1, DSA 2)
# The IMF's baseline debt decomposition: d(t) - d(t-1) = primary deficit + (r - g)/(1 + g) x d(t-1)
# + other identified flows + residual, with r the real effective interest rate and g real growth.
# Actual years use interest paid (gross) and show interest earnings as another flow, as the IMF does;
# the WEO publishes interest only net of earnings, so projection years use the net figure.

DEBT = share(DEBT_EUR, GDP)
REAL_GROWTH = published("gdp_growth_annual")
DEFLATOR = published("gdp_deflator_growth_annual")
EFFECTIVE_RATE = share(INTEREST_PAID, lag(DEBT_EUR))
W_DEBT = published("fc_imf_debt")
W_GROWTH = published("fc_imf_gdp")
W_DEFLATOR = growth(published("fc_imf_deflator"))
W_NET_INTEREST = less(published("fc_imf_primary_balance_eur"), published("fc_imf_balance_eur"))
W_EFFECTIVE_RATE = share(W_NET_INTEREST, lag(published("fc_imf_debt_eur")))


def _real_interest(rate: Expr, deflator: Expr, real_growth: Expr, debt: Expr) -> Expr:
    """r / (1 + g) x d(t-1), with r = (1 + i) / (1 + inflation) - 1."""
    return combine(lambda i, p, g, d: ((1 + i / 100) / (1 + p / 100) - 1) / (1 + g / 100) * d,
                   rate, deflator, real_growth, lag(debt))


def _real_growth(real_growth: Expr, debt: Expr) -> Expr:
    """-g / (1 + g) x d(t-1)."""
    return combine(lambda g, d: -g / 100 / (1 + g / 100) * d, real_growth, lag(debt))


PRIMARY_DEFICIT = scaled(share(PRIMARY_EUR, GDP), -1)
W_PRIMARY_DEFICIT = scaled(published("fc_imf_primary_balance"), -1)
REAL_INTEREST = _real_interest(EFFECTIVE_RATE, DEFLATOR, REAL_GROWTH, DEBT)
W_REAL_INTEREST = _real_interest(W_EFFECTIVE_RATE, W_DEFLATOR, W_GROWTH, W_DEBT)
REAL_GROWTH_EFFECT = _real_growth(REAL_GROWTH, DEBT)
W_REAL_GROWTH_EFFECT = _real_growth(W_GROWTH, W_DEBT)
AUTOMATIC = total(REAL_INTEREST, REAL_GROWTH_EFFECT)
W_AUTOMATIC = total(W_REAL_INTEREST, W_REAL_GROWTH_EFFECT)
INTEREST_EARNINGS = scaled(share(INTEREST_RECEIVED, GDP), -1)
IDENTIFIED = total(PRIMARY_DEFICIT, AUTOMATIC, INTEREST_EARNINGS)
W_IDENTIFIED = total(W_PRIMARY_DEFICIT, W_AUTOMATIC)

DSA_BASELINE = SectorTable(
    id="dsa-baseline", label="DSA 1", title="Public Debt Dynamics: Baseline Scenario",
    unit="Percent of GDP unless otherwise indicated", section="fiscal", block="debt-sustainability",
    sheet="DSA1 Baseline", imf_table="Annex III. Figure 4. Spain: Baseline Scenario",
    rows=[
        Line("Public debt", DEBT, W_DEBT, source=f"{ESTAT}; Maastricht debt over GDP", proj_source=WEO,
             link="gg_debt_eur"),
        Line("Change in public debt", diff(DEBT), diff(W_DEBT), source=ESTAT, proj_source=WEO),
        Line("Contribution of identified flows 1/", IDENTIFIED, W_IDENTIFIED, indent=1, source="EconPulse calculation",
             proj_source="EconPulse calculation from the WEO"),
        Line("Primary deficit", PRIMARY_DEFICIT, W_PRIMARY_DEFICIT, indent=2,
             source=f"{ESTAT}; minus the primary balance", proj_source=WEO),
        Line("Noninterest revenues", share(less(TR, INTEREST_RECEIVED), GDP), indent=3, source=f"{ESTAT}; TR less D41"),
        Line("Noninterest expenditures", share(less(TE, INTEREST_PAID), GDP), indent=3, source=f"{ESTAT}; TE less D41"),
        Line("Automatic debt dynamics", AUTOMATIC, W_AUTOMATIC, indent=2, source="EconPulse calculation",
             proj_source="EconPulse calculation from the WEO"),
        Line("Real interest rate", REAL_INTEREST, W_REAL_INTEREST, indent=3, source="EconPulse calculation",
             proj_source="EconPulse calculation from the WEO"),
        Line("Real growth rate", REAL_GROWTH_EFFECT, W_REAL_GROWTH_EFFECT, indent=3, source="EconPulse calculation",
             proj_source="EconPulse calculation from the WEO"),
        Line("Other identified flows: (minus) interest revenues 2/", INTEREST_EARNINGS, indent=2,
             source=f"{ESTAT}; D41 received", link="gg_interest_received_eur"),
        Line("Contribution of residual 3/", less(diff(DEBT), IDENTIFIED), less(diff(W_DEBT), W_IDENTIFIED), indent=1,
             source="EconPulse calculation", proj_source="EconPulse calculation from the WEO"),
        Group("Memo items"),
        Line("Real GDP growth (percent)", REAL_GROWTH, W_GROWTH, source=ESTAT, proj_source=WEO,
             link="gdp_growth_annual"),
        Line("Inflation (GDP deflator; percent)", DEFLATOR, W_DEFLATOR, source=ESTAT, proj_source=WEO,
             link="gdp_deflator_growth_annual"),
        Line("Nominal GDP growth (percent)", growth(GDP), growth(published("fc_imf_nominal_gdp")), source=ESTAT,
             proj_source=WEO, link="gdp_nominal_annual"),
        Line("Effective interest rate (percent) 4/", EFFECTIVE_RATE, W_EFFECTIVE_RATE,
             source=f"{ESTAT}; interest paid over the previous year's debt", proj_source=f"{WEO}; net interest"),
    ],
    footnotes=[
        "1/ Primary deficit, automatic debt dynamics and other identified flows. Automatic debt dynamics are "
        "(r - g)/(1 + g) times the previous year's debt ratio, split into the real effective interest rate r and real "
        "GDP growth g. Spain's debt is in euros, so exchange rates play no part.",
        "2/ The primary balance excludes interest earnings, as in the World Economic Outlook, so they count as "
        "another flow.",
        "3/ Includes stock-flow adjustments (changes in government deposits and other financial assets), which the "
        "IMF shows separately as other transactions.",
        "4/ Interest paid over the previous year's debt. The World Economic Outlook publishes interest only net of "
        "interest earnings, so in projection years the rate and the real interest rate effect are net, and interest "
        "earnings are not shown separately.",
    ],
)

DSM_SOURCE = "European Commission"
DSA_STRESS = SectorTable(
    id="dsa-stress", label="DSA 2", title="Public Debt: European Commission Baseline and Stress Tests",
    unit="Percent of GDP", section="fiscal", block="debt-sustainability", sheet="DSA2 EC stress tests",
    imf_table="(the IMF's stress tests are not published as data; the Commission's are)", kind="dsm",
    web_actual=1, first_year=2024,
    rows=[
        Group("Gross public debt"),
        Line("Baseline (no policy change)", dsm("baseline", "debt"), dsm("baseline", "debt"), source=DSM_SOURCE,
             proj_source=DSM_SOURCE),
        *[Line(name, dsm("scenarios", name), dsm("scenarios", name), indent=1, source=DSM_SOURCE,
               proj_source=DSM_SOURCE)
          for name in ("Lower structural primary balance", "Adverse interest-growth differential", "Financial stress",
                       "Historical structural primary balance")],
        Group("Stochastic projections around the baseline 1/"),
        *[Line(f"{p}th percentile", dsm("percentiles", f"p{p}"), dsm("percentiles", f"p{p}"), indent=1,
               source=DSM_SOURCE, proj_source=DSM_SOURCE) for p in (90, 80, 20, 10)],
        Group("Baseline"),
        Line("Primary balance", dsm("baseline", "primary_balance"), dsm("baseline", "primary_balance"),
             source=DSM_SOURCE, proj_source=DSM_SOURCE),
        Line("Structural primary balance", dsm("baseline", "structural_primary_balance"),
             dsm("baseline", "structural_primary_balance"), source=DSM_SOURCE, proj_source=DSM_SOURCE),
        Line("Interest expenditure", dsm("baseline", "interest"), dsm("baseline", "interest"), source=DSM_SOURCE,
             proj_source=DSM_SOURCE),
        Line("Gross financing needs", dsm("baseline", "gross_financing_needs"),
             dsm("baseline", "gross_financing_needs"), source=DSM_SOURCE, proj_source=DSM_SOURCE),
    ],
    footnotes=[
        "1/ The range of debt paths the Commission simulates from past shocks to growth, interest rates and the "
        "primary balance: four in five paths lie between the 10th and 90th percentiles.",
        "The baseline assumes no change in policy after the Commission's forecast years: the structural primary "
        "balance then moves only with the cost of ageing. The stress tests are the Commission's: a lower structural primary "
        "balance, a higher interest-growth differential, a temporary rise in market interest rates (financial "
        "stress) and a return of the structural primary balance to its historical average.",
    ],
)

# ---------------------------------------------------------------- balance of payments and external debt (Tables 4, 5)
# Eurostat's BPM6 balance of payments and international investment position, in millions of euros.
# The WEO projects only the current account, as a share of GDP.

def _bn(x) -> Expr:
    return scaled(published(x) if isinstance(x, str) else x, 1e-3)


def _pct(x) -> Expr:
    return share(published(x) if isinstance(x, str) else x, GDP)


W_CURRENT_ACCOUNT = published("fc_imf_current_account")
W_CURRENT_ACCOUNT_BN = combine(lambda ca, y: ca / 100 * y * 1e-9, W_CURRENT_ACCOUNT, published("fc_imf_nominal_gdp"))
NIIP_EUR = published("niip_eur_annual")
# The change in the investment position not explained by financial flows (prices, exchange rates, other changes).
VALUATION = _pct(less(diff(NIIP_EUR), published("bop_financial_account")))
BPM6 = f"{ESTAT}, BPM6"

# label, indent, indicator, shown in % of GDP too
BOP_LINES = [
    ("Current account", 0, "current_account_annual", True),
    ("Trade balance of goods and services", 1, "trade_balance_annual", True),
    ("Exports of goods and services", 2, "bop_exports_gs", True),
    ("Exports of goods", 3, "bop_exports_goods", True),
    ("Exports of services", 3, "bop_exports_services", True),
    ("Trade of goods balance", 2, "bop_goods_balance", False),
    ("Imports of goods and services", 2, "bop_imports_gs", True),
    ("Imports of goods", 3, "bop_imports_goods", True),
    ("Imports of services", 3, "bop_imports_services", True),
    ("Services", 2, "bop_services_balance", False),
    ("o.w. Tourism (travel)", 3, "bop_travel_balance", False),
    ("Tourism receipts", 3, "bop_travel_credit", False),
    ("Tourism payments", 3, "bop_travel_debit", False),
    ("Primary income", 1, "bop_primary_income", True),
    ("Secondary income", 1, "bop_secondary_income", True),
    ("General government", 2, "bop_secondary_income_gov", False),
    ("Other sectors", 2, "bop_secondary_income_other", False),
    ("Capital account", 0, "bop_capital_account", True),
    ("Financial account 1/", 0, "bop_financial_account", True),
    ("Direct investment", 1, "bop_fdi_net", True),
    ("Spanish investment abroad", 2, "bop_fdi_abroad", False),
    ("Foreign investment in Spain", 2, "bop_fdi_inward", False),
    ("Portfolio investment", 1, "bop_portfolio", True),
    ("Financial derivatives", 1, "bop_derivatives", True),
    ("Other investment", 1, "bop_other_investment", True),
    ("o.w. Banco de España", 2, "bop_other_investment_bde", None),   # % of GDP only, as in the IMF's table
    ("Change in reserve assets", 1, "bop_reserves", True),
    ("Errors and omissions", 0, "bop_errors", True),
]


def _bop_rows() -> list:
    eur, gdp = [Group("Billions of euros")], [Group("Percent of GDP")]
    for label, indent, ind, in_gdp in BOP_LINES:
        sign = -1 if ind == "bop_travel_debit" else 1   # payments shown as negative, as the IMF does
        ca = ind == "current_account_annual"
        if in_gdp is not None:
            eur.append(Line(label, scaled(_bn(ind), sign), W_CURRENT_ACCOUNT_BN if ca else None, indent=indent,
                            source=BPM6, proj_source=f"{WEO}; current account share of nominal GDP" if ca else "",
                            link=ind))
        if in_gdp is not False:
            gdp.append(Line(label, _pct(ind), W_CURRENT_ACCOUNT if ca else None, indent=indent, source=BPM6,
                            proj_source=WEO if ca else "", link=ind))
    gdp += [Line("Net international investment position", _pct(NIIP_EUR), source=f"{ESTAT}, end of year",
                 link="niip_eur_annual"),
            Line("Valuation changes 2/", VALUATION, source=f"{ESTAT}; change in the position less the financial account")]
    return eur + gdp


BALANCE_OF_PAYMENTS = SectorTable(
    id="balance-of-payments", label="Table 4", title="Balance of Payments",
    unit="Billions of euros and percent of GDP", section="activity", block="external-tables",
    sheet="T4 Balance of payments", imf_table="Table 4. Spain: Balance of Payments",
    rows=_bop_rows(),
    footnotes=[
        "Eurostat, sixth edition of the IMF's Balance of Payments Manual (BPM6). The World Economic Outlook projects "
        "only the current account, as a share of GDP; the euro figure applies it to the WEO's nominal GDP.",
        "1/ Net lending to the rest of the world: net acquisition of foreign assets less net incurrence of liabilities.",
        "2/ The change in the net international investment position not explained by the financial account: changes "
        "in prices and exchange rates, and other changes.",
    ],
)

GOV_EXT = total(published("ext_securities_gov"), published("ext_other_gov"))
MFI_EXT = total(published("ext_securities_mfi"), published("ext_other_mfi"))
OTHER_EXT = total(published("ext_securities_other"), published("ext_other_other"))
GROSS_EXT = total(published("ext_securities"), published("ext_other"), published("ext_direct_investment"))
LOANS_EXT = less(published("ext_other"), published("ext_deposits"))
NET_EXT_EUR = combine(lambda pct, y: pct / 100 * y, published("net_external_debt_gdp"), GDP)
IIP = f"{ESTAT}, international investment position"

# label, indent, expression (€ mn), source note, linked indicator
EXT_LINES = [
    ("Gross external debt 1/", 0, GROSS_EXT, "debt securities, other investment and direct investment debt", None),
    ("General government", 1, GOV_EXT, "S13", "ext_securities_gov"),
    ("Bank of Spain", 1, published("ext_other_bde"), "S121", "ext_other_bde"),
    ("Other monetary financial institutions", 1, MFI_EXT, "S12T", "ext_securities_mfi"),
    ("Other resident sectors", 1, OTHER_EXT, "S1P", "ext_securities_other"),
    ("Debt securities", 1, published("ext_securities"), "F3", "ext_securities"),
    ("Loans, trade credits and other liabilities", 1, LOANS_EXT, "other investment less deposits", None),
    ("Deposits", 1, published("ext_deposits"), "F2", "ext_deposits"),
    ("Direct investment debt liabilities", 1, published("ext_direct_investment"), "direct investment, debt", "ext_direct_investment"),
    ("Net external debt 2/", 0, NET_EXT_EUR, "net external debt (% of GDP) times GDP", "net_external_debt_gdp"),
]

EXTERNAL_DEBT = SectorTable(
    id="external-debt", label="Table 5", title="External Debt", unit="End of year; billions of euros and percent of GDP",
    section="activity", block="external-tables", sheet="T5 External debt", imf_table="Table 5. Spain: External Debt",
    kind="actual", web_actual=5,
    rows=[Group("Billions of euros")]
    + [Line(label, _bn(e), indent=indent, source=f"{IIP}; {note}", link=link) for label, indent, e, note, link in EXT_LINES]
    + [Group("Percent of GDP")]
    + [Line(label, _pct(e) if "Net" not in label else published("net_external_debt_gdp"), indent=indent,
            source=f"{IIP}; {note}", link=link) for label, indent, e, note, link in EXT_LINES],
    footnotes=[
        "1/ Liabilities to non-residents in debt instruments at the end of the year, from Eurostat's international "
        "investment position (BPM6). The sectors, with direct investment debt, add up to the total; so do the "
        "instruments. The IMF's table uses the World Bank's Quarterly External Debt Statistics, which differ slightly.",
        "2/ Gross external debt less external assets in debt instruments (Eurostat).",
    ],
)

# ---------------------------------------------------------------- financial soundness (Table 3)
# Consolidated indicators from the IMF's FSI database (its balance sheet and income items, so the ratios are
# the IMF's own), domestic business from the Banco de España, households from the ECB, housing from INE.

FSI = "IMF FSI database"
BDE = "Banco de España"


def _ratio(num: str, den: str) -> Expr:
    return share(published(num), published(den))


TIER1 = published("fsi_tier1_capital")


def _leverage(data: Data):
    """Tier 1 over the Basel III leverage exposure where reported, otherwise over total assets."""
    t1, exposure, assets = TIER1(data), published("fsi_leverage_exposure")(data), published("fsi_total_assets")(data)
    if t1 is None or assets is None:
        return None
    base = assets if exposure is None else exposure.reindex(assets.index).fillna(assets)
    return (t1 / base * 100).dropna()


LEVERAGE = _expr(_leverage, {"fsi_tier1_capital", "fsi_leverage_exposure", "fsi_total_assets"})
CONSTRUCTION = total(december("bank_credit_construction"), december("bank_credit_real_estate"))
CONSTRUCTION_NPL = total(december("bank_npl_construction"), december("bank_npl_real_estate"))
OTHER_BUSINESS = less(december("bank_credit_business"), CONSTRUCTION)
OTHER_BUSINESS_NPL = less(december("bank_npl_business"), CONSTRUCTION_NPL)
OTHER_HOUSEHOLD = less(december("bank_credit_osr"), december("bank_credit_business"), december("bank_credit_housing"))
OTHER_HOUSEHOLD_NPL = less(december("bank_npl_domestic"), december("bank_npl_business"), december("bank_npl_housing"))

FINANCIAL_SOUNDNESS = SectorTable(
    id="financial-soundness", label="Table 3", title="Selected Financial Soundness Indicators",
    unit="Percent, unless otherwise indicated; end of year", section="financial", block="soundness-table",
    sheet="T3 Financial soundness", imf_table="Table 3. Spain: Selected Financial Soundness Indicators",
    kind="actual", web_actual=6,
    sources=("Sources: IMF Financial Soundness Indicators database (consolidated basis); Banco de España (domestic "
             "operations); Eurostat (household debt); INE (house prices and sales); EconPulse calculations."),
    rows=[
        Group("Deposit takers: consolidated basis"),
        Line("Regulatory capital to risk-weighted assets", _ratio("fsi_regulatory_capital", "fsi_rwa"), source=FSI,
             link="fsi_regulatory_capital"),
        Line("Regulatory Tier 1 capital to risk-weighted assets", _ratio("fsi_tier1_capital", "fsi_rwa"), source=FSI,
             link="fsi_tier1_capital"),
        Line("Tier 1 capital to total assets 1/", LEVERAGE, source=FSI, link="fsi_leverage_exposure"),
        Line("Nonperforming loans (billions of euros)", scaled(published("fsi_npl"), 1e-9), source=FSI, link="fsi_npl"),
        Line("Nonperforming loans to total gross loans", _ratio("fsi_npl", "fsi_gross_loans"), source=FSI,
             link="fsi_gross_loans"),
        Line("Specific provisions to nonperforming loans", _ratio("fsi_specific_provisions", "fsi_npl"), source=FSI,
             link="fsi_specific_provisions"),
        Line("Return on assets 2/", _ratio("fsi_income_before_tax", "fsi_average_assets"), source=FSI,
             link="fsi_income_before_tax"),
        Line("Return on equity 2/", _ratio("fsi_income_after_tax", "fsi_average_capital"), source=FSI,
             link="fsi_income_after_tax"),
        Group("Deposit takers: domestic operations"),
        Line("Nonperforming loans (billions of euros)", scaled(december("bank_npl_domestic"), 1e-6), source=BDE,
             link="bank_npl_domestic"),
        Line("Nonperforming loans to total loans", share(december("bank_npl_domestic"), december("bank_credit_osr")),
             source=BDE, link="bank_credit_osr"),
        Line("Specific provisions to nonperforming loans 3/",
             share(december("bank_provisions_osr"), december("bank_npl_osr_all")), source=BDE, link="bank_provisions_osr"),
        Line("Exposure to businesses: construction and real estate (billions of euros)", scaled(CONSTRUCTION, 1e-6),
             source=BDE, link="bank_credit_construction"),
        Line("o/w nonperforming (percent)", share(CONSTRUCTION_NPL, CONSTRUCTION), indent=1, source=BDE,
             link="bank_npl_construction"),
        Line("Exposure to businesses: other (billions of euros)", scaled(OTHER_BUSINESS, 1e-6), source=BDE,
             link="bank_credit_business"),
        Line("o/w nonperforming (percent)", share(OTHER_BUSINESS_NPL, OTHER_BUSINESS), indent=1, source=BDE,
             link="bank_npl_business"),
        Line("Exposure to households: home purchase (billions of euros)", scaled(december("bank_credit_housing"), 1e-6),
             source=BDE, link="bank_credit_housing"),
        Line("o/w nonperforming (percent)", share(december("bank_npl_housing"), december("bank_credit_housing")),
             indent=1, source=BDE, link="bank_npl_housing"),
        Line("Exposure to households: other (billions of euros) 4/", scaled(OTHER_HOUSEHOLD, 1e-6), source=BDE),
        Line("o/w nonperforming (percent)", share(OTHER_HOUSEHOLD_NPL, OTHER_HOUSEHOLD), indent=1, source=BDE),
        Line("Loans to deposits 5/", share(december("bank_loans_osr"), december("bank_deposits_osr"), 1e5), source=BDE,
             link="bank_deposits_osr"),
        Group("Corporate sector"),
        Line("Debt (percent of GDP)", share(published("fsi_nfc_debt"), GDP, 1e-4), source=f"{FSI}; GDP from Eurostat",
             link="fsi_nfc_debt"),
        Line("Debt to total assets 6/", _ratio("fsi_nfc_debt", "fsi_nfc_balance_sheet"), source=FSI,
             link="fsi_nfc_balance_sheet"),
        Group("Household sector"),
        Line("Debt (percent of GDP) 7/", published("household_liabilities_gdp"), source=f"{ESTAT}, financial accounts",
             link="household_liabilities_gdp"),
        Group("Real estate market"),
        Line("House prices (percentage change, end of period)", growth(year_end("house_prices")),
             source="INE, fourth quarter on a year earlier", link="house_prices"),
        Line("Home sales (2007 = 100)", indexed(annual_sum("home_sales"), 2007), source="INE, sales of homes in the year",
             link="home_sales"),
    ],
    footnotes=[
        "1/ Tier 1 capital over the Basel III leverage exposure measure where reported (from 2022), otherwise over "
        "total assets.",
        "2/ As in the IMF's database: net income before tax over average total assets, and net income after tax "
        "over average capital and reserves.",
        "3/ Impairment allowances over nonperforming credit to other resident sectors (credit institutions and "
        "specialised lenders).",
        "4/ Credit to households other than for house purchase, to nonprofit institutions, and unclassified credit.",
        "5/ Based on loans to and deposits from other resident sectors, as in the IMF's table.",
        "6/ Debt over the balance sheet total (debt, equity and other liabilities) of nonfinancial corporations.",
        "7/ Total financial liabilities of households (loans, trade credit and other accounts payable), which is "
        "what the IMF's figures match; loans alone are about 4 points of GDP lower.",
        "Home sales are INE's count from the property registers; the IMF's index, from another source, runs a little "
        "lower.",
    ],
)

# ---------------------------------------------------------------- monetary (Table 6)
# Not in the Article IV for Spain, which as a euro area member has no monetary table: built in the IMF's style
# from the ECB's data on the Banco de España's balance sheet, bank lending and interest rates.

def _monetary_rows(in_gdp: bool) -> list:
    """The Banco de España's balance sheet in billions of euros or in % of GDP; the rest is the same either way."""
    def amount(ind_id: str) -> Expr:
        return share(december(ind_id), GDP) if in_gdp else scaled(december(ind_id), 1e-3)
    return [
        Group(f"Banco de España ({'percent of GDP' if in_gdp else 'billions of euros'})"),
        Line("Total assets", amount("bde_total_assets"), source="ECB, Eurosystem balance sheets", link="bde_total_assets"),
        Line("Securities held for monetary policy purposes", amount("bde_mp_securities"), indent=1, source="ECB",
             link="bde_mp_securities"),
        Line("Lending to credit institutions (monetary policy operations)", amount("bde_mp_lending"), indent=1,
             source="ECB", link="bde_mp_lending"),
        Line("Banknotes in circulation", amount("bde_banknotes"), indent=1, source="ECB", link="bde_banknotes"),
        Line("Credit institutions' reserves and deposits", amount("bde_mp_liabilities"), indent=1, source="ECB",
             link="bde_mp_liabilities"),
        Line("TARGET balance 1/", amount("target_balance"), source="ECB, end of December", link="target_balance"),
        Group("Credit and deposits (annual percent change, December)"),
        Line("Credit to the private sector 2/", december("private_credit_growth"), source="ECB",
             link="private_credit_growth"),
        Line("Loans to households", december("loans_households_growth"), indent=1, source="ECB",
             link="loans_households_growth"),
        Line("o.w. for house purchase", december("housing_loans_growth"), indent=2, source="ECB",
             link="housing_loans_growth"),
        Line("Loans to non-financial corporations", december("loans_nfc_growth"), indent=1, source="ECB",
             link="loans_nfc_growth"),
        Line("Deposits of other resident sectors 3/", growth(december("bank_deposits_osr")), source=BDE,
             link="bank_deposits_osr"),
        Group("Interest rates (percent)"),
        Line("ECB deposit facility rate (end of year)", year_end("ecb_deposit_rate"), source="ECB",
             link="ecb_deposit_rate", decimals=2),
        Line("3-month Euribor (end of year)", year_end("euribor_3m"), source=BDE, link="euribor_3m", decimals=2),
        Line("10-year government bond yield (end of year)", year_end("es_10y"), source=BDE, link="es_10y", decimals=2),
        Line("New loans to households for house purchase (December)", december("mortgage_rate"), source="ECB",
             link="mortgage_rate", decimals=2),
        Line("New loans to non-financial corporations (December)", december("nfc_loan_rate"), source="ECB",
             link="nfc_loan_rate", decimals=2),
        Line("New household time deposits (December)", december("deposit_rate_households"), source="ECB",
             link="deposit_rate_households", decimals=2),
    ]


MONETARY = SectorTable(
    id="monetary", label="Table 6", title="Monetary and Credit Indicators",
    unit="End of year, unless otherwise indicated", section="ecb", block="monetary-table",
    sheet="T6 Monetary", imf_table="(none: the Article IV for Spain has no monetary table)",
    kind="actual", web_actual=6,
    sources="Sources: ECB (Eurosystem balance sheets, TARGET balances, bank balance sheets and interest rates); "
            "Banco de España; EconPulse calculations.",
    rows=_monetary_rows(False),
    footnotes=[
        "1/ The Banco de España's net position in the Eurosystem's payment system; negative is a liability.",
        "2/ Bank loans to households, firms and non-bank financial corporations, adjusted for loan sales and "
        "securitisation.",
        "3/ Deposits held at credit institutions and specialised lenders, unadjusted.",
    ],
)

TABLES = [REAL_SECTOR, FISCAL_EUR, FISCAL_GDP, DSA_BASELINE, DSA_STRESS, FINANCIAL_SOUNDNESS, BALANCE_OF_PAYMENTS,
          EXTERNAL_DEBT, MONETARY]
BY_ID = {t.id: t for t in TABLES}

# ---------------------------------------------------------------- the Sector tables page
# Every table on one page (site/sector-tables.html). Tables with amounts come in two versions the page
# switches between: billions of euros, as in the IMF's report, or percent of GDP. Tables of rates and
# ratios are the same either way.


def _bop_unit_rows(in_gdp: bool) -> list:
    rows = []
    for label, indent, ind, _ in BOP_LINES:
        sign = -1 if ind == "bop_travel_debit" else 1
        ca = ind == "current_account_annual"
        proj = (W_CURRENT_ACCOUNT if in_gdp else W_CURRENT_ACCOUNT_BN) if ca else None
        rows.append(Line(label, scaled(_pct(ind) if in_gdp else _bn(ind), sign), proj, indent=indent, source=BPM6,
                         proj_source=WEO if ca else "", link=ind))
    unexplained = less(diff(NIIP_EUR), published("bop_financial_account"))
    rows += [Line("Net international investment position", _pct(NIIP_EUR) if in_gdp else _bn(NIIP_EUR),
                  source=f"{ESTAT}, end of year", link="niip_eur_annual"),
             Line("Valuation changes 2/", VALUATION if in_gdp else _bn(unexplained),
                  source=f"{ESTAT}; change in the position less the financial account")]
    return rows


def _ext_unit_rows(in_gdp: bool) -> list:
    return [Line(label, (published("net_external_debt_gdp") if "Net" in label else _pct(e)) if in_gdp else _bn(e),
                 indent=indent, source=f"{IIP}; {note}", link=link) for label, indent, e, note, link in EXT_LINES]


# DSA 1 in euros: the debt changes only through the primary deficit, interest and other flows (growth and
# inflation lower the ratio, not the amount owed). Projection years use the WEO's net interest.
DEBT_BN, W_DEBT_BN = scaled(DEBT_EUR, 1e-3), scaled(published("fc_imf_debt_eur"), 1e-9)
PRIMARY_DEFICIT_BN = scaled(PRIMARY_EUR, -1e-3)
W_PRIMARY_DEFICIT_BN = scaled(published("fc_imf_primary_balance_eur"), -1e-9)
INTEREST_PAID_BN, W_NET_INTEREST_BN = scaled(INTEREST_PAID, 1e-3), scaled(W_NET_INTEREST, 1e-9)
INTEREST_RECEIVED_BN = scaled(INTEREST_RECEIVED, -1e-3)

DSA_BASELINE_AMOUNTS = replace(
    DSA_BASELINE, id="dsa-baseline-amounts", unit="Billions of euros unless otherwise indicated",
    rows=[
        Line("Public debt", DEBT_BN, W_DEBT_BN, source=f"{ESTAT}; Maastricht debt", proj_source=WEO, link="gg_debt_eur"),
        Line("Change in public debt", diff(DEBT_BN), diff(W_DEBT_BN), source=ESTAT, proj_source=WEO),
        Line("Primary deficit", PRIMARY_DEFICIT_BN, W_PRIMARY_DEFICIT_BN, indent=1,
             source=f"{ESTAT}; minus the primary balance", proj_source=WEO),
        Line("Interest payments 1/", INTEREST_PAID_BN, W_NET_INTEREST_BN, indent=1, source=f"{ESTAT}; D41 paid",
             proj_source=f"{WEO}; net interest", link="gg_interest_paid_eur"),
        Line("(minus) Interest revenues 1/", INTEREST_RECEIVED_BN, indent=1, source=f"{ESTAT}; D41 received",
             link="gg_interest_received_eur"),
        Line("Other flows (stock-flow adjustment) 2/",
             less(diff(DEBT_BN), PRIMARY_DEFICIT_BN, INTEREST_PAID_BN, INTEREST_RECEIVED_BN),
             less(diff(W_DEBT_BN), W_PRIMARY_DEFICIT_BN, W_NET_INTEREST_BN), indent=1, source="EconPulse calculation",
             proj_source="EconPulse calculation from the WEO"),
        Group("Memo items"),
        Line("Nominal GDP (billions of euros)", scaled(GDP, 1e-3), scaled(published("fc_imf_nominal_gdp"), 1e-9), source=ESTAT,
             proj_source=WEO, link="gdp_nominal_annual"),
        Line("Nominal GDP growth (percent)", growth(GDP), growth(published("fc_imf_nominal_gdp")), source=ESTAT, proj_source=WEO,
             link="gdp_nominal_annual"),
        Line("Effective interest rate (percent) 1/", EFFECTIVE_RATE, W_EFFECTIVE_RATE,
             source=f"{ESTAT}; interest paid over the previous year's debt", proj_source=f"{WEO}; net interest"),
    ],
    footnotes=[
        "In euros the debt changes only through the deficit and other flows; growth and inflation lower the debt "
        "ratio, not the amount owed, so their effects appear only in the percent-of-GDP version.",
        "1/ Interest paid and received. The World Economic Outlook publishes interest only net of interest earnings, "
        "so projection years show net interest and no separate interest revenues.",
        "2/ The change in debt the deficit does not explain: mainly changes in government deposits and other "
        "financial assets.",
    ],
)


def _dsm_gdp(data: Data):
    """The Commission's nominal GDP path (€ mn): Eurostat's GDP in its first year, grown at the baseline's
    nominal growth rate."""
    if "dsm_gdp" not in data.cache:
        gdp, rows = GDP(data), (fiscal.baseline(fiscal.load()) if fiscal.BASELINE_FILE.exists() else {})
        base = dsm("baseline", "debt")(data)
        path = {}
        if gdp is not None and base is not None and int(base.index.min()) in gdp.index:
            first = int(base.index.min())
            path[first] = float(gdp[first])
            for y in range(first + 1, int(base.index.max()) + 1):
                path[y] = path[y - 1] * (1 + rows[y]["g"] / 100)
        data.cache["dsm_gdp"] = pd.Series(path, dtype=float)
    return data.cache["dsm_gdp"]


DSM_GDP = _expr(_dsm_gdp, {"gdp_nominal_annual"})


_DSM_GROUPS = {"Gross public debt": "Gross public debt (billions of euros) 1/",
               "Stochastic projections around the baseline 1/":
                   "Stochastic projections around the baseline (billions of euros) 1/ 2/",
               "Baseline": "Baseline (billions of euros)"}


def _dsm_amounts(row):
    if isinstance(row, Group):
        return Group(_DSM_GROUPS.get(row.label, row.label))
    to_bn = lambda e: combine(lambda v, y: v / 100 * y * 1e-3, e, DSM_GDP)
    return replace(row, actual=to_bn(row.actual), proj=to_bn(row.proj))


DSA_STRESS_AMOUNTS = replace(
    DSA_STRESS, id="dsa-stress-amounts", unit="Billions of euros", rows=[_dsm_amounts(r) for r in DSA_STRESS.rows],
    footnotes=[
        "1/ The Commission's debt ratios times its baseline nominal GDP (Eurostat's GDP in 2024, grown at the "
        "baseline's nominal growth rate). The stress tests and percentiles are shown at baseline GDP, as a guide to "
        "scale: each scenario also has its own path for GDP, which the Commission does not publish.",
        "2/ The range of debt paths the Commission simulates from past shocks to growth, interest rates and the "
        "primary balance: four in five paths lie between the 10th and 90th percentiles.",
        "The baseline assumes no change in policy after the Commission's forecast years: the structural primary "
        "balance then moves only with the cost of ageing.",
    ],
)

BOP_AMOUNTS = replace(BALANCE_OF_PAYMENTS, id="bop-amounts", unit="Billions of euros", rows=_bop_unit_rows(False))
BOP_GDP = replace(BALANCE_OF_PAYMENTS, id="bop-gdp", unit="Percent of GDP", rows=_bop_unit_rows(True))
EXT_AMOUNTS = replace(EXTERNAL_DEBT, id="ext-amounts", unit="End of year; billions of euros", rows=_ext_unit_rows(False))
EXT_GDP = replace(EXTERNAL_DEBT, id="ext-gdp", unit="End of year; percent of GDP", rows=_ext_unit_rows(True))
MONETARY_GDP = replace(MONETARY, id="monetary-gdp", rows=_monetary_rows(True))


# Any table in the other unit. A line's unit is in its label or its group heading, as the IMF writes
# them: "(percent of GDP)" lines become billions of euros (with nominal GDP: Eurostat for actual years,
# the WEO for projections) and "(billions of euros)" lines percent of GDP. Lines in their own units
# (percent change, percent of potential GDP or of disposable income) stay as they are; where their group
# heading changes unit, the line's unit is spelled out.
W_NOMINAL_GDP = published("fc_imf_nominal_gdp")
OWN_UNITS = {"Potential output 1/": "percent change", "Structural balance 1/": "percent of potential GDP",
             "Primary structural balance 1/": "percent of GDP"}
SHARE, AMOUNT = "(percent of GDP)", "(billions of euros)"


def _amounts(e: Expr | None, projection: bool = False) -> Expr | None:
    if e is None:
        return None
    return combine(lambda v, y: v / 100 * y * (1e-9 if projection else 1e-3), e, W_NOMINAL_GDP if projection else GDP)


def _shares(e: Expr | None, projection: bool = False) -> Expr | None:
    if e is None:
        return None
    return combine(lambda v, y: v / (y * (1e-9 if projection else 1e-3)) * 100, e, W_NOMINAL_GDP if projection else GDP)


def _with_unit(label: str, unit: str) -> str:
    """'Structural balance 1/' -> 'Structural balance (percent of potential GDP) 1/'."""
    head, _, tail = label.rpartition(" ")
    if head and tail.endswith("/") and tail[:-1].isdigit():
        return f"{head} ({unit}) {tail}"
    return f"{label} ({unit})"


def convert(table: SectorTable, to: str) -> SectorTable:
    """The table with its amounts in billions of euros (to="amounts") or in percent of GDP (to="gdp")."""
    rows, group_in_shares = [], False
    for r in table.rows:
        if isinstance(r, Group):
            group_in_shares = SHARE in r.label
            rows.append(Group(r.label.replace(SHARE, AMOUNT)) if to == "amounts" else r)
            continue
        own_unit = "(percent of" in r.label or "(billions of" in r.label
        if AMOUNT in r.label and "GDP (billions" not in r.label:
            measure = "amount"
        elif SHARE in r.label or (group_in_shares and not own_unit and r.label not in OWN_UNITS):
            measure = "share"
        else:
            measure = "rate"
        if to == "amounts" and measure == "share":
            r = replace(r, label=r.label.replace(SHARE, AMOUNT), actual=_amounts(r.actual), proj=_amounts(r.proj, True))
        elif to == "gdp" and measure == "amount":
            r = replace(r, label=r.label.replace(AMOUNT, SHARE), actual=_shares(r.actual), proj=_shares(r.proj, True))
        elif to == "amounts" and group_in_shares and r.label in OWN_UNITS:
            r = replace(r, label=_with_unit(r.label, OWN_UNITS[r.label]))
        rows.append(r)
    return replace(table, id=f"{table.id}-{to}", rows=rows)


def _path(data: Data, actual: Expr, proj: Expr | None = None, first: int = FIRST_YEAR) -> pd.Series:
    """Actual years, then the projections: the values a table line shows, as one series."""
    last_actual, last = years(data) or (0, 0)
    a, p = actual(data), proj(data) if proj else None
    parts = [a[(a.index >= first) & (a.index <= last_actual)]] if a is not None else []
    if p is not None:
        parts.append(p[(p.index > last_actual) & (p.index <= last)])
    parts = [s for s in parts if not s.empty]
    return pd.concat(parts).dropna() if parts else pd.Series(dtype=float)


def _spec(chart_id: str, title: str, subtitle: str, series: list, source: str, kind: str = "line", unit: str = "%",
          **options) -> dict | None:
    series = [s for s in series if s["x"]]
    if not series:
        return None
    return {"id": chart_id, "title": title, "subtitle": subtitle, "kind": kind, "unit": unit, "decimals": 1,
            "freq": "A", "ref_lines": [], "series": series, "source": source, **options}


def chart_growth(data: Data) -> dict | None:
    span_ = years(data)
    if not span_:
        return None
    actual, proj = _path(data, published("gdp_growth_annual")), published("fc_imf_gdp")(data)
    proj = proj[(proj.index > span_[0]) & (proj.index <= span_[1])] if proj is not None else pd.Series(dtype=float)
    return _spec("st-growth", "Real GDP growth", f"% change on the year before; actual to {span_[0]}, then the IMF's "
                 "projection", [_line("Actual", actual), _line("IMF projection", proj)],
                 "Eurostat; IMF World Economic Outlook", kind="bar", signed=True)


def chart_saving(data: Data) -> dict | None:
    return _spec("st-saving", "Saving, investment and the current account",
                 "% of GDP; the IMF's projections from the first year after the last actual figures",
                 [_line("National savings", _path(data, NATIONAL_SAVING, published("fc_imf_saving"))),
                  _line("Gross investment", _path(data, INVESTMENT, published("fc_imf_investment"))),
                  _line("Current account", _path(data, share(published("current_account_annual"), GDP),
                                                 W_CURRENT_ACCOUNT))],
                 "Eurostat; IMF World Economic Outlook")


def chart_fiscal(data: Data) -> dict | None:
    return _spec("st-fiscal", "Government revenue and expenditure",
                 "% of GDP; the IMF's projections after the last actual year",
                 [_line("Expenditure", _path(data, share(TE, GDP), published("fc_imf_spending_gdp"))),
                  _line("Revenue", _path(data, share(TR, GDP), published("fc_imf_revenue_gdp")))],
                 "Eurostat; IMF World Economic Outlook")


def chart_debt_dynamics(data: Data) -> dict | None:
    other = less(diff(DEBT), PRIMARY_DEFICIT, AUTOMATIC)
    w_other = less(diff(W_DEBT), W_PRIMARY_DEFICIT, W_AUTOMATIC)
    first = FIRST_YEAR + 1
    return _spec("st-debt-dynamics", "What changes the debt ratio",
                 "Percentage points of GDP: the parts of DSA 1, actual years then the IMF's projections",
                 [_line("Primary deficit", _path(data, PRIMARY_DEFICIT, W_PRIMARY_DEFICIT, first)),
                  _line("Interest rate less growth", _path(data, AUTOMATIC, W_AUTOMATIC, first)),
                  _line("Other flows and residual", _path(data, other, w_other, first)),
                  _line("Change in debt", _path(data, diff(DEBT), diff(W_DEBT), first), kind="line", color="ink")],
                 "Eurostat; IMF World Economic Outlook; EconPulse calculation", kind="bar", unit="pp", stack=True,
                 signed=True)


def chart_capital(data: Data) -> dict | None:
    return _spec("st-capital", "Bank capital", "% of risk-weighted assets, consolidated, end of year",
                 [_line("Regulatory capital", _path(data, _ratio("fsi_regulatory_capital", "fsi_rwa"))),
                  _line("Tier 1 capital", _path(data, _ratio("fsi_tier1_capital", "fsi_rwa")))],
                 "IMF Financial Soundness Indicators database")


def chart_bad_loans(data: Data) -> dict | None:
    return _spec("st-bad-loans", "Nonperforming loans", "% of loans, end of year",
                 [_line("Domestic business", _path(data, share(december("bank_npl_domestic"),
                                                                december("bank_credit_osr")))),
                  _line("Consolidated (incl. abroad)", _path(data, _ratio("fsi_npl", "fsi_gross_loans")))],
                 "Banco de España; IMF Financial Soundness Indicators database")


def chart_current_account(data: Data) -> dict | None:
    income = total(published("bop_primary_income"), published("bop_secondary_income"))
    return _spec("st-current-account", "The current account and its parts", "% of GDP",
                 [_line("Goods", _path(data, _pct("bop_goods_balance"))),
                  _line("Services", _path(data, _pct("bop_services_balance"))),
                  _line("Primary and secondary income", _path(data, _pct(income))),
                  _line("Current account", _path(data, _pct("current_account_annual")), kind="line", color="ink")],
                 f"{BPM6}", kind="bar", stack=True, signed=True)


def chart_external(data: Data) -> dict | None:
    return _spec("st-external", "External position and debt", "% of GDP, end of year",
                 [_line("Gross external debt", _path(data, _pct(GROSS_EXT))),
                  _line("Net external debt", _path(data, published("net_external_debt_gdp"))),
                  _line("Net investment position", _path(data, _pct(NIIP_EUR)))],
                 f"{IIP}")


def chart_credit(data: Data) -> dict | None:
    return _spec("st-credit", "Bank lending", "Annual % change in December, adjusted for loan sales; firms are "
                 "non-financial corporations",
                 [_line("Households", _path(data, december("loans_households_growth"))),
                  _line("Firms", _path(data, december("loans_nfc_growth"))),
                  _line("Private sector", _path(data, december("private_credit_growth")), color="ink")],
                 "ECB", signed=True)


def chart_central_bank(data: Data) -> dict | None:
    return _spec("st-central-bank", "The Banco de España in the Eurosystem",
                 "€ billion, end of year: securities bought for monetary policy, lending to banks, and its TARGET "
                 "balance (net position in the Eurosystem's payment system)",
                 [_line("Policy securities", _path(data, scaled(december("bde_mp_securities"), 1e-3))),
                  _line("Lending to banks", _path(data, scaled(december("bde_mp_lending"), 1e-3))),
                  _line("TARGET balance", _path(data, scaled(december("target_balance"), 1e-3)))],
                 "ECB", unit="bn")


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


def span(table: SectorTable, data: Data) -> tuple[int, int] | None:
    """The table's last actual year and last projection year."""
    if table.kind == "dsm":
        history, debt = dsm("history")(data), dsm("baseline", "debt")(data)
        if history is None or debt is None:
            return None
        return int(history.index.max()), int(debt.index.max())
    if table.kind == "actual":   # no projections: to the last year of the first line
        first = next(r for r in table.rows if isinstance(r, Line)).actual(data)
        if first is None or first.empty:
            return None
        return int(first.index.max()), int(first.index.max())
    return years(data)


def weo_edition(data: Data) -> str:
    """'October 2026', from the publication date the IMF's data service reports."""
    published_on = data.store.load_catalog().get("fc_imf_gdp", {}).get("published")
    if not published_on:
        return ""
    d = date.fromisoformat(published_on)
    return f"{d:%B %Y}"


def dsm_edition(data: Data) -> str:
    dsm("history")(data)   # loads the file into the cache
    return data.cache.get("fiscal_baseline", {}).get("dsm_source", {}).get("edition", "the Debt Sustainability Monitor")


def projections_phrase(table: SectorTable, data: Data) -> str:
    if table.kind == "dsm":
        return "European Commission projections"
    edition = weo_edition(data)
    return f"IMF projections (World Economic Outlook{', ' + edition if edition else ''})"


def sources_line(table: SectorTable, data: Data) -> str:
    if table.sources:
        return table.sources
    if table.kind == "dsm":
        return f"Source: {dsm_edition(data)}, Spain's country fiche."
    if table.kind == "actual":
        return "Sources: Eurostat; EconPulse calculations."
    edition = weo_edition(data)
    return ("Sources: INE, Eurostat and the ECB for actual years; IMF World Economic Outlook"
            + (f" ({edition})" if edition else "") + " for projections; EconPulse calculations.")


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
    """The table for its section page: the last actual years and the projections."""
    if table.freq != "A":
        return period_web_table(table, data)
    years_ = span(table, data)
    if not years_:
        return None
    last_actual, last = years_
    first = last_actual - table.web_actual + 1
    rows = []
    for r in values(table, data, first, last, last_actual):
        if r["heading"]:
            rows.append(r)
            continue
        line = r["line"]
        rows.append({"heading": False, "label": r["label"], "label_es": "", "indent": line.indent, "period_note": "",
                     "url": data.by_id[line.link].source_url() if line.link in data.by_id else None,
                     "cells": [fmt(v, line.decimals) for v in r["cells"]]})
    n_proj = last - last_actual
    if table.kind == "dsm":
        note = " ".join(table.footnotes) + " " + sources_line(table, data)
    elif table.kind == "actual":
        note = " ".join(table.footnotes) + f" After the {REPORT_PREFIX}."
    else:
        note = (" ".join(table.footnotes) + f" {NA} not available: the IMF's database does not publish the line. "
                f"After the {REPORT_PREFIX}; past years differ where the data have been revised since.")
    return {
        "title": f"{table.label}. {table.title}",
        "caption": (f"{table.unit} · actual data to {last_actual}"
                    + (f", {projections_phrase(table, data)} from {last_actual + 1}" if n_proj else "")),
        "through": str(last_actual),
        "columns": [str(y) for y in range(first, last + 1)],
        "column_notes": [""] * table.web_actual + ["proj."] * n_proj,
        "rows": rows,
        "note": note,
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


def dsa_facts(data: Data) -> list[dict]:
    out = []
    weo = published("fc_imf_debt")(data)
    if weo is not None and not weo.empty:
        y = int(weo.index.max())
        out.append({"label": f"Debt in {y}, IMF", "value": f"{fmt(weo[y])}% of GDP",
                    "sub": f"World Economic Outlook{', ' + weo_edition(data) if weo_edition(data) else ''}"})
    base = dsm("baseline", "debt")(data)
    if base is not None:
        y = int(base.index.max())
        out.append({"label": f"Debt in {y}, European Commission", "value": f"{fmt(base[y])}% of GDP",
                    "sub": "No-policy-change baseline"})
    s1 = data.cache.get("fiscal_baseline", {}).get("dsm", {}).get("gaps", {}).get("S1")
    if s1 is not None:
        out.append({"label": "Sustainability gap S1, Commission", "value": f"{fmt(s1)}% of GDP",
                    "sub": "Adjustment from 2027 that brings debt to 60% of GDP by 2070", "url": "fiscal-explorer.html"})
    return out


def _line(name: str, s: pd.Series, **style) -> dict:
    return {"name": name, "x": [f"{y}-01-01" for y in s.index], "y": [round(float(v), 3) for v in s.values], **style}


def _debt_path(data: Data, start: int) -> pd.Series | None:
    """The Commission's debt history joined to its baseline."""
    history, base = dsm("history")(data), dsm("baseline", "debt")(data)
    if history is None or base is None:
        return None
    return pd.concat([history[history.index >= start], base[base.index > history.index.max()]])


def dsa_fan_chart(data: Data) -> dict | None:
    path = _debt_path(data, 2010)
    if path is None:
        return None
    series = [_line("Commission baseline", path, color="ink")]
    p90, p10 = dsm("percentiles", "p90")(data), dsm("percentiles", "p10")(data)
    if p90 is not None and p10 is not None:
        series += [_line("90th percentile", p90, slot=1, dash="dash"), _line("10th percentile", p10, slot=1, dash="dash")]
    weo, years_ = published("fc_imf_debt")(data), span(DSA_STRESS, data)
    if weo is not None and years_:
        series.append(_line("IMF (WEO)", weo[weo.index >= years_[0]], slot=2))
    return {"id": "dsa-fan", "title": "Public debt: baselines and fan chart",
            "subtitle": "% of GDP; the Commission's baseline with the 10th and 90th percentiles of its stochastic "
                        "projections, and the IMF's projection",
            "kind": "line", "unit": "%", "decimals": 1, "freq": "A", "ref_lines": [], "series": series,
            "source": "European Commission (Debt Sustainability Monitor 2025); IMF World Economic Outlook"}


def dsa_stress_chart(data: Data) -> dict | None:
    path = _debt_path(data, 2015)
    if path is None:
        return None
    series = [_line("Baseline", path, color="ink")]
    # Short names, so the end labels fit beside the plot; DSA 2 gives the Commission's full names.
    for slot, (name, short) in enumerate((("Lower structural primary balance", "Lower primary balance"),
                                          ("Adverse interest-growth differential", "Adverse r − g"),
                                          ("Financial stress", "Financial stress")), start=1):
        s = dsm("scenarios", name)(data)
        if s is not None:
            series.append(_line(short, s, slot=slot))
    return {"id": "dsa-stress", "title": "Public debt under the Commission's stress tests",
            "subtitle": "% of GDP; baseline and three of the Commission's four stress tests (all four are in DSA 2)",
            "kind": "line", "unit": "%", "decimals": 1, "freq": "A", "ref_lines": [], "series": series,
            "source": "European Commission (Debt Sustainability Monitor 2025)"}


# ---------------------------------------------------------------- the workbook

def write_workbook(data: Data, path: Path, built: str = "") -> bool:
    """Every table, with history from FIRST_YEAR, as one .xlsx file. False when there are no data yet."""
    from openpyxl import Workbook
    from openpyxl.styles import Alignment, Border, Font, PatternFill, Side

    main = years(data)
    if not main:
        return False
    last_actual, last = main
    edition = weo_edition(data)
    bold, title_font, muted = Font(bold=True), Font(bold=True, size=13), Font(italic=True, color="595959")
    proj_fill = PatternFill("solid", fgColor="EEF2F7")
    rule = Border(bottom=Side(style="thin", color="7F7F7F"))

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
    tables = [t for t in TABLES if span(t, data)]
    for t in tables:
        row += 1
        c = contents.cell(row, 1, f"{t.label}. {t.title}")
        c.hyperlink = f"#'{t.sheet}'!A1"
        c.font = Font(color="1F4E79", underline="single")
        contents.cell(row, 2, t.imf_table)
        contents.cell(row, 3, f"{SITE_URL}{t.section}.html#{t.block}")
    row += 2
    notes = [
        f"Lines follow the tables in the {REPORT}, where public data allow.",
        f"Actual years ({FIRST_YEAR}-{last_actual}) come from INE, Eurostat and the ECB; projection years "
        f"({last_actual + 1}-{last}) from the IMF's World Economic Outlook database"
        + (f" ({edition} edition)." if edition else "."),
        f"{NA} means not available: the WEO database does not publish the line (the staff report's own projections "
        "are only in the report), or the statistics do not go back that far.",
        "Potential output, the output gap, the structural balance and net debt are IMF staff estimates in every year.",
        f"DSA 2 is the European Commission's: {dsm_edition(data)}. The IMF's own stress tests are not published "
        "as data.",
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

    for t in tables:
        t_actual, t_last = span(t, data)
        year_list = list(range(t.first_year, t_last + 1))
        ws = wb.create_sheet(t.sheet)
        ws["A1"] = f"{t.label}. Spain: {t.title}"
        ws["A1"].font = title_font
        ws["A2"] = f"({t.unit})"
        ws["A2"].font = muted
        if t_last > t_actual:
            ws.cell(3, 2 + (t_actual + 1 - t.first_year), "Projections").font = bold
        header = [""] + [str(y) for y in year_list] + ["Source, actual years", "Source, projections"]
        for col, h in enumerate(header, start=1):
            c = ws.cell(4, col, int(h) if h.isdigit() else h)
            c.font = bold
            c.border = rule
            c.alignment = Alignment(horizontal="right" if h.isdigit() else "left")
        r_idx = 4
        for r in values(t, data, t.first_year, t_last, t_actual):
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
                if year_list[k] > t_actual:
                    c.fill = proj_fill
            ws.cell(r_idx, 2 + len(year_list), line.source if line.actual else NA)
            ws.cell(r_idx, 3 + len(year_list), line.proj_source if line.proj else NA)
        r_idx += 2
        ws.cell(r_idx, 1, sources_line(t, data)).font = muted
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


# ---------------------------------------------------------------- quarterly and monthly views
# Tables with quarterly or monthly data also come as period tables: the last 8 quarters or 13 months, actual
# data only. Their expressions map the build's Data to a series indexed by the start of each quarter or month.
# Lines published only once a year are left out of these views.

PERIOD_START = {"Q": "QS", "M": "MS"}
PERIOD_COUNT = {"Q": 8, "M": 13}
PERIOD_WORD = {"A": "Annual", "Q": "Quarterly", "M": "Monthly"}


def at(ind_id: str, to: str, how: str = "last") -> Expr:
    """A series by quarter or month: as published, or the last value or mean of each complete period."""
    def fn(data):
        s = data.raw(ind_id)
        if s is None:
            return None
        s, source = s.dropna().astype(float), data.by_id[ind_id].freq
        if s.empty or source == to:
            return s
        if source in ("A", "Q") and to in ("Q", "M"):
            return None   # no finer data to show
        periods = s.index.to_period(to)
        grouped = s.groupby(periods)
        out = grouped.last() if how == "last" else grouped.mean()
        last_seen = s.groupby(periods).apply(lambda g: g.index.max())
        ends = out.index.to_timestamp(how="end").normalize()
        if source == "M":   # a quarter is complete when its last month is in
            complete = pd.Series(last_seen.dt.month.values % 3 == 0, index=out.index) if how == "last" else \
                grouped.count() == 3
        else:               # daily: complete once the period is within four days of its end
            complete = pd.Series((ends - pd.DatetimeIndex(last_seen.values)).days <= 4, index=out.index)
        out = out[complete.values]
        out.index = out.index.to_timestamp()
        return out
    return _expr(fn, [ind_id])


def yoy(e: Expr) -> Expr:
    """% change on the same period a year earlier."""
    def fn(data):
        s = e(data)
        if s is None:
            return None
        prev = s.reindex(s.index - pd.DateOffset(years=1)).values
        return pd.Series((s.values / prev - 1) * 100, index=s.index).dropna()
    return _expr(fn, e.ids)


GDP_QUARTER = at("gdp_nominal", "Q")


def _gdp_year_to(to: str) -> Expr:
    """GDP over the past four quarters (€ mn) for each quarter or month: the latest published by then."""
    def fn(data):
        q = data.raw("gdp_nominal")   # a regular quarterly calendar: a missing quarter gives no sum
        if q is None:
            return None
        rolled = q.rolling(4).sum().dropna()
        if rolled.empty:
            return None
        index = pd.date_range(rolled.index.min(), pd.Timestamp.today().normalize(), freq=PERIOD_START[to])
        return rolled.reindex(index.union(rolled.index)).ffill().reindex(index)
    return _expr(fn, {"gdp_nominal"})


def _per_gdp(e: Expr, gdp: Expr) -> Expr:
    """An amount in € mn as a percent of GDP."""
    return combine(lambda v, y: v / y * 100, e, gdp)


def _amount_of(e: Expr, gdp: Expr) -> Expr:
    """A share of GDP as billions of euros."""
    return combine(lambda v, y: v / 100 * y * 1e-3, e, gdp)


def period_web_table(table: SectorTable, data: Data) -> dict | None:
    """A quarterly or monthly table: the latest periods, leaving out lines with no data at that frequency."""
    computed = [(r, r.actual(data) if isinstance(r, Line) and r.actual else None) for r in table.rows]
    lasts = [s.dropna().index.max() for _, s in computed if s is not None and not s.dropna().empty]
    if not lasts:
        return None
    through = max(lasts)
    columns = pd.date_range(end=through, periods=PERIOD_COUNT[table.freq], freq=PERIOD_START[table.freq])
    rows, heading = [], None
    for r, s in computed:
        if isinstance(r, Group):
            heading = r
            continue
        cells = [None if s is None or p not in s.index or pd.isna(s[p]) else float(s[p]) for p in columns]
        if all(c is None for c in cells):
            continue
        if heading:
            rows.append({"heading": True, "label": heading.label})
            heading = None
        rows.append({"heading": False, "label": r.label, "label_es": "", "indent": r.indent, "period_note": "",
                     "url": data.by_id[r.link].source_url() if r.link in data.by_id else None,
                     "cells": [fmt(c, r.decimals) for c in cells]})
    word = PERIOD_WORD[table.freq].lower()
    return {
        "title": f"{table.label}. {table.title}",
        "caption": f"{table.unit} · {word} data to {period_label(through, table.freq)}",
        "through": period_label(through, table.freq),
        "columns": [period_label(c, table.freq) for c in columns],
        "column_notes": None,
        "rows": rows,
        "note": " ".join(table.footnotes) + f" Lines published only once a year are left out; {NA} not yet published.",
    }


def _real_sector_quarterly(in_amounts: bool) -> SectorTable:
    gdp_q, gdp_year = GDP_QUARTER, _gdp_year_to("Q")
    share_of = lambda e, base: _amount_of(e, base) if in_amounts else e
    q = lambda ind, how="last": at(ind, "Q", how)
    employment = q("employment_epa")
    return replace(
        REAL_SECTOR, id=f"real-sector-q-{'amounts' if in_amounts else 'gdp'}", freq="Q",
        unit="Percent change on a year earlier unless otherwise indicated",
        rows=[
            Group("Demand and supply in constant prices"),
            Line("Gross domestic product", yoy(q("gdp")), source=INE, link="gdp"),
            Line("Private consumption", yoy(q("consumption_households")), indent=1, source=INE,
                 link="consumption_households"),
            Line("Public consumption", yoy(q("consumption_government")), indent=1, source=INE,
                 link="consumption_government"),
            Line("Gross fixed investment", yoy(q("investment")), indent=1, source=INE, link="investment"),
            Line("Total domestic demand", yoy(q("domestic_demand")), indent=1, source=INE, link="domestic_demand"),
            Line("Net exports (contribution to growth)", q("contrib_external_yy"), indent=1, source=INE,
                 link="contrib_external_yy"),
            Line("Exports of goods and services", yoy(q("exports")), indent=1, source=INE, link="exports"),
            Line("Imports of goods and services", yoy(q("imports")), indent=1, source=INE, link="imports"),
            Group("Households"),
            Line("Household saving rate (percent of gross disposable income)", q("saving_rate"), source=INE,
                 link="saving_rate"),
            Group("Prices"),
            Line("GDP deflator", yoy(q("gdp_deflator")), source=INE, link="gdp_nominal"),
            Line("Headline inflation (average) 1/", yoy(q("hicp_index", "mean")), source=ESTAT, link="hicp_index"),
            Line("Headline inflation (end of period) 1/", yoy(q("hicp_index")), source=ESTAT, link="hicp_index"),
            Line("Core inflation (average) 1/", yoy(q("hicp_core_np_index", "mean")), source=ESTAT,
                 link="hicp_core_np_index"),
            Line("Core inflation (end of period) 1/", yoy(q("hicp_core_np_index")), source=ESTAT,
                 link="hicp_core_np_index"),
            Group("Employment and wages"),
            Line("Unemployment rate (percent of total labor force)", q("unemployment_epa"), source=INE,
                 link="unemployment_epa"),
            Line("Labor productivity 2/", q("productivity_fte"), source=INE, link="productivity_fte"),
            Line("Labor costs 3/", yoy(q("labour_cost")), source=INE, link="labour_cost"),
            Line("Employment", yoy(employment), source=INE, link="employment_epa"),
            Line("Labor force", yoy(combine(lambda e, u: e / (1 - u / 100), employment, q("unemployment_epa"))),
                 source=INE, link="employment_epa"),
            Group(f"Balance of payments ({'billions of euros' if in_amounts else 'percent of GDP'})"),
            Line("Current account balance 4/", share_of(q("current_account"), gdp_q), source=ESTAT,
                 link="current_account"),
            Group(f"Public finance ({'billions of euros' if in_amounts else 'percent of GDP'})"),
            Line("General government balance 4/", share_of(q("government_balance"), gdp_q), source=ESTAT,
                 link="government_balance"),
            Line("General government debt 5/", share_of(q("government_debt"), gdp_year), source=ESTAT,
                 link="government_debt"),
            Group("Memo items"),
            Line("Credit to the private sector 6/", q("private_credit_growth"), source=ECB, link="private_credit_growth"),
            Line("Nominal GDP (billions of euros, the quarter)", scaled(gdp_q, 1e-3), source=INE, link="gdp_nominal"),
        ],
        footnotes=[
            "Growth rates compare each quarter with the same quarter a year earlier.",
            "1/ Harmonised Index of Consumer Prices; core excludes energy and unprocessed food. Average: the quarter's "
            "mean; end of period: its last month.",
            "2/ Output per full-time equivalent job.",
            "3/ Total labour cost per worker, all sectors (INE's quarterly labour cost survey).",
            "4/ The quarter's flow" + (" in euros (its share of the quarter's GDP times that GDP)" if in_amounts
                                       else ", as a share of the quarter's GDP") + ", not seasonally adjusted.",
            "5/ End of quarter" + (", in euros." if in_amounts else ", as a share of GDP over the past four quarters."),
            "6/ Annual growth of bank loans to the private sector at the end of the quarter, adjusted for loan sales "
            "and securitisation.",
        ],
    )


def _monetary_periodic(to: str, in_gdp: bool) -> SectorTable:
    gdp_year = _gdp_year_to(to)
    p = lambda ind: at(ind, to)
    amount = (lambda ind: _per_gdp(p(ind), gdp_year)) if in_gdp else (lambda ind: scaled(p(ind), 1e-3))
    return replace(
        MONETARY, id=f"monetary-{to.lower()}-{'gdp' if in_gdp else 'amounts'}", freq=to,
        unit="End of period, unless otherwise indicated",
        rows=[
            Group(f"Banco de España ({'percent of GDP' if in_gdp else 'billions of euros'})"),
            Line("Total assets", amount("bde_total_assets"), source="ECB", link="bde_total_assets"),
            Line("Securities held for monetary policy purposes", amount("bde_mp_securities"), indent=1, source="ECB",
                 link="bde_mp_securities"),
            Line("Lending to credit institutions (monetary policy operations)", amount("bde_mp_lending"), indent=1,
                 source="ECB", link="bde_mp_lending"),
            Line("Banknotes in circulation", amount("bde_banknotes"), indent=1, source="ECB", link="bde_banknotes"),
            Line("Credit institutions' reserves and deposits", amount("bde_mp_liabilities"), indent=1, source="ECB",
                 link="bde_mp_liabilities"),
            Line("TARGET balance 1/", amount("target_balance"), source="ECB", link="target_balance"),
            Group("Credit and deposits (percent change on a year earlier)"),
            Line("Credit to the private sector 2/", p("private_credit_growth"), source="ECB", link="private_credit_growth"),
            Line("Loans to households", p("loans_households_growth"), indent=1, source="ECB",
                 link="loans_households_growth"),
            Line("o.w. for house purchase", p("housing_loans_growth"), indent=2, source="ECB", link="housing_loans_growth"),
            Line("Loans to non-financial corporations", p("loans_nfc_growth"), indent=1, source="ECB",
                 link="loans_nfc_growth"),
            Line("Deposits of other resident sectors 3/", yoy(p("bank_deposits_osr")), source=BDE,
                 link="bank_deposits_osr"),
            Group("Interest rates (percent)"),
            Line("ECB deposit facility rate", p("ecb_deposit_rate"), source="ECB", link="ecb_deposit_rate", decimals=2),
            Line("3-month Euribor", p("euribor_3m"), source=BDE, link="euribor_3m", decimals=2),
            Line("10-year government bond yield", p("es_10y"), source=BDE, link="es_10y", decimals=2),
            Line("New loans to households for house purchase 4/", p("mortgage_rate"), source="ECB", link="mortgage_rate", decimals=2),
            Line("New loans to non-financial corporations 4/", p("nfc_loan_rate"), source="ECB", link="nfc_loan_rate", decimals=2),
            Line("New household time deposits 4/", p("deposit_rate_households"), source="ECB",
                 link="deposit_rate_households", decimals=2),
        ],
        footnotes=[
            "1/ The Banco de España's net position in the Eurosystem's payment system; negative is a liability."
            + (" Shares of GDP use GDP over the past four quarters." if in_gdp else ""),
            "2/ Bank loans to households, firms and non-bank financial corporations, adjusted for loan sales and "
            "securitisation.",
            "3/ Deposits held at credit institutions and specialised lenders, unadjusted.",
            "4/ New business in the " + ("month" if to == "M" else "quarter's last month") + ".",
        ],
    )


def previous(e: Expr, months: int) -> Expr:
    """The value the given number of months earlier."""
    def fn(data):
        s = e(data)
        return None if s is None else pd.Series(s.values, index=s.index + pd.DateOffset(months=months))
    return _expr(fn, e.ids)


def _quarterly_id(annual_id: str) -> str:
    """The quarterly twin of an annual balance of payments or investment position series."""
    return {"current_account_annual": "bop_q_current_account", "trade_balance_annual": "bop_q_trade_balance",
            "niip_eur_annual": "niip_q_eur", "net_external_debt_gdp": "net_external_debt_q"}.get(
        annual_id, annual_id.replace("bop_", "bop_q_", 1).replace("ext_", "ext_q_", 1))


def _bop_quarterly(in_gdp: bool) -> SectorTable:
    gdp_q, gdp_year = GDP_QUARTER, _gdp_year_to("Q")
    flow = (lambda e: _per_gdp(e, gdp_q)) if in_gdp else (lambda e: scaled(e, 1e-3))
    rows = []
    for label, indent, ind, _ in BOP_LINES:
        qid = _quarterly_id(ind)
        rows.append(Line(label, scaled(flow(at(qid, "Q")), -1 if ind == "bop_travel_debit" else 1), indent=indent,
                         source=f"{BPM6}, quarterly", link=qid))
    niip = at("niip_q_eur", "Q")
    unexplained = less(niip, previous(niip, 3), at("bop_q_financial_account", "Q"))
    rows += [Line("Net international investment position 3/", _per_gdp(niip, gdp_year) if in_gdp else scaled(niip, 1e-3),
                  source=f"{ESTAT}, end of quarter", link="niip_q_eur"),
             Line("Valuation changes 2/", flow(unexplained),
                  source=f"{ESTAT}; change in the position less the financial account")]
    return replace(
        BALANCE_OF_PAYMENTS, id=f"bop-q-{'gdp' if in_gdp else 'amounts'}", freq="Q",
        unit="Percent of the quarter's GDP" if in_gdp else "Billions of euros", rows=rows,
        footnotes=[
            "Eurostat, BPM6: each quarter's flows, not seasonally adjusted" + (", as a share of that quarter's GDP."
                                                                                 if in_gdp else "."),
            "1/ Net lending to the rest of the world: net acquisition of foreign assets less net incurrence of liabilities.",
            "2/ The change in the net international investment position over the quarter not explained by the "
            "financial account: changes in prices and exchange rates, and other changes.",
            "3/ End of quarter" + ("; as a share of GDP over the past four quarters." if in_gdp else "."),
        ],
    )


def _ext_quarterly(in_gdp: bool) -> SectorTable:
    gdp_year = _gdp_year_to("Q")
    q = lambda ind: at(ind, "Q")
    stock = (lambda e: _per_gdp(e, gdp_year)) if in_gdp else (lambda e: scaled(e, 1e-3))
    lines = [
        ("Gross external debt 1/", 0, total(q("ext_q_securities"), q("ext_q_other"), q("ext_q_direct_investment")), None),
        ("General government", 1, total(q("ext_q_securities_gov"), q("ext_q_other_gov")), "ext_q_securities_gov"),
        ("Bank of Spain", 1, q("ext_q_other_bde"), "ext_q_other_bde"),
        ("Other monetary financial institutions", 1, total(q("ext_q_securities_mfi"), q("ext_q_other_mfi")),
         "ext_q_securities_mfi"),
        ("Other resident sectors", 1, total(q("ext_q_securities_other"), q("ext_q_other_other")), "ext_q_securities_other"),
        ("Debt securities", 1, q("ext_q_securities"), "ext_q_securities"),
        ("Loans, trade credits and other liabilities", 1, less(q("ext_q_other"), q("ext_q_deposits")), None),
        ("Deposits", 1, q("ext_q_deposits"), "ext_q_deposits"),
        ("Direct investment debt liabilities", 1, q("ext_q_direct_investment"), "ext_q_direct_investment"),
    ]
    net = q("net_external_debt_q")
    rows = [Line(label, stock(e), indent=indent, source=f"{IIP}, end of quarter", link=link) for label, indent, e, link in lines]
    rows.append(Line("Net external debt 2/", net if in_gdp else _amount_of(net, gdp_year), source=f"{ESTAT}, end of quarter",
                     link="net_external_debt_q"))
    return replace(
        EXTERNAL_DEBT, id=f"ext-q-{'gdp' if in_gdp else 'amounts'}", freq="Q",
        unit="End of quarter; percent of GDP over the past four quarters" if in_gdp else "End of quarter; billions of euros",
        rows=rows,
        footnotes=[
            "1/ Liabilities to non-residents in debt instruments at the end of the quarter, from Eurostat's international "
            "investment position (BPM6). The sectors, with direct investment debt, add up to the total; so do the "
            "instruments.",
            "2/ Gross external debt less external assets in debt instruments (Eurostat)"
            + ("." if in_gdp else "; in euros, its share of GDP over the past four quarters times that GDP."),
        ],
    )


BOP_Q = (_bop_quarterly(False), _bop_quarterly(True))
EXT_Q = (_ext_quarterly(False), _ext_quarterly(True))
REAL_SECTOR_Q = (_real_sector_quarterly(True), _real_sector_quarterly(False))
MONETARY_Q = (_monetary_periodic("Q", False), _monetary_periodic("Q", True))
MONETARY_M = (_monetary_periodic("M", False), _monetary_periodic("M", True))


# ---------------------------------------------------------------- the Sector tables page: sections

# id, title, intro, tables (a pair is amounts, then % of GDP; a dict gives the annual, quarterly and monthly
# views), charts
PAGE = [
    ("real-sector", "Real sector",
     "The IMF's main table for Spain: demand, saving and investment, prices, the labour market, and a summary of the "
     "external and public accounts.",
     [{"A": (convert(REAL_SECTOR, "amounts"), convert(REAL_SECTOR, "gdp")), "Q": REAL_SECTOR_Q}],
     [chart_growth, chart_saving]),
    ("fiscal", "Government operations",
     "Revenue, spending and the balances of the general government, from Eurostat's accounts.",
     [(FISCAL_EUR, FISCAL_GDP)], [chart_fiscal]),
    ("debt-sustainability", "Debt sustainability",
     "What changes the debt, in the IMF's layout, and how it fares under the European Commission's stress tests. In "
     "percent of GDP, DSA 1 splits the change in the debt ratio, growth and inflation included; in euros, the change "
     "in the amount owed, which only the deficit, interest and other flows move.",
     [(DSA_BASELINE_AMOUNTS, DSA_BASELINE), (DSA_STRESS_AMOUNTS, DSA_STRESS)],
     [chart_debt_dynamics, dsa_fan_chart, dsa_stress_chart]),
    ("financial-soundness", "Financial soundness",
     "Bank capital, asset quality and profitability, banks' exposures at home, and the debt of firms and households.",
     [(convert(FINANCIAL_SOUNDNESS, "amounts"), convert(FINANCIAL_SOUNDNESS, "gdp"))], [chart_capital, chart_bad_loans]),
    ("balance-of-payments", "Balance of payments",
     "Spain's transactions with the rest of the world, and the investment position they build up.",
     [{"A": (BOP_AMOUNTS, BOP_GDP), "Q": BOP_Q}], [chart_current_account]),
    ("external-debt", "External debt",
     "What Spanish residents owe to non-residents, by sector and instrument.",
     [{"A": (EXT_AMOUNTS, EXT_GDP), "Q": EXT_Q}], [chart_external]),
    ("monetary", "Monetary and credit",
     "The Banco de España's balance sheet in the Eurosystem, bank lending and deposits, and interest rates.",
     [{"A": (MONETARY, MONETARY_GDP), "Q": MONETARY_Q, "M": MONETARY_M}], [chart_credit, chart_central_bank]),
]


def _view(freq: str, entry, data: Data) -> dict | None:
    if isinstance(entry, tuple):
        amounts, gdp = (web_table(x, data) for x in entry)
        return {"freq": freq, "label": PERIOD_WORD[freq], "amounts": amounts, "gdp": gdp} if amounts and gdp else None
    single = web_table(entry, data)
    return {"freq": freq, "label": PERIOD_WORD[freq], "single": single} if single else None


def page(data: Data) -> dict:
    """The Sector tables page: its sections (each table's views, in both units) and chart specs."""
    sections, charts = [], []
    for section_id, title, intro, tables, chart_fns in PAGE:
        built = []
        for n, entry in enumerate(tables, start=1):
            entries = entry if isinstance(entry, dict) else {"A": entry}
            views = [v for v in (_view(f, entries[f], data) for f in ("A", "Q", "M") if f in entries) if v]
            if views:
                first = views[0].get("single") or views[0]["amounts"]
                built.append({"id": f"{section_id}-{n}", "title": first["title"], "views": views})
        specs = [c for c in (fn(data) for fn in chart_fns) if c]
        if built or specs:
            sections.append({"id": section_id, "title": title, "intro": intro, "tables": built, "charts": specs})
            charts += specs
    return {"sections": sections, "charts": charts}
