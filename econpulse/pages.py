"""What each section page shows: blocks of econvitals-style tables and charts.

A block is a sub-heading with an intro, one or more tables (econpulse/tables.py) and
a grid of charts (econpulse/charts.py specs). Sections without blocks yet show their
indicator list only (see build.SECTION_PAGES for the batch that fills them).
"""

from .charts import build_chart
from .registry import Indicator
from .snapshot import fmt_value, period_label
from .store import Store
from .tables import AvgChange, Change, Contribution, Data, Heading, Level, Row, Table, build_table

LEVELS = [Level("latest"), Level("prev"), Level("year")]
HORIZONS = [Change("1-mo ann.", 1, True), Change("3-mo ann.", 3, True), Change("6-mo ann.", 6, True), Change("12-mo", 12)]
SA_NOTE = ("Horizons under 12 months are annualised and use EconPulse seasonal adjustment, because INE publishes "
           "these indices unadjusted. The 12-month column matches the published annual rates.")
TARGET = [{"y": 2, "label": "2% target"}]

PAGES: dict[str, list[dict]] = {
    # ------------------------------------------------------------------ GDP
    "gdp": [
        {
            "id": "growth",
            "title": "GDP and its components",
            "intro": ("Real growth, seasonally and calendar adjusted by INE. Following Spanish practice, "
                      "quarterly growth is not annualised."),
            "tables": [Table(
                title="Real growth",
                caption="% change; contributions in percentage points",
                columns=[Change("q/q", 3), Change("y/y", 12), Contribution("Contrib. q/q", "q"), Contribution("Contrib. y/y", "y")],
                rows=[
                    Row("gdp", "GDP"),
                    Heading("Spending"),
                    Row("domestic_demand", "Domestic demand", contrib={"q": "contrib_domestic_qq", "y": "contrib_domestic_yy"}),
                    Row("consumption_households", "Household consumption", indent=1),
                    Row("consumption_government", "Government consumption", indent=1),
                    Row("investment", "Fixed investment", indent=1),
                    Row("investment_construction", "Construction", indent=2),
                    Row("investment_housing", "of which housing", indent=3),
                    Row("investment_equipment", "Machinery and equipment", indent=2),
                    Row(None, "External demand (net exports)", contrib={"q": "contrib_external_qq", "y": "contrib_external_yy"},
                        label_es="Demanda externa"),
                    Row("exports", "Exports", indent=1),
                    Row("exports_goods", "Goods", indent=2),
                    Row("exports_services", "Services, including tourism", indent=2),
                    Row("imports", "Imports", indent=1),
                    Heading("Output by sector (gross value added)"),
                    Row("gva_agriculture", "Agriculture"),
                    Row("gva_industry", "Industry"),
                    Row("gva_construction", "Construction"),
                    Row("gva_services", "Services"),
                    Heading("Prices and jobs"),
                    Row("gdp_nominal", "Nominal GDP"),
                    Row("gdp_deflator", "GDP deflator"),
                    Row("jobs_fte", "Employment (full-time equivalent jobs)"),
                ],
                note=("Contributions are percentage points of GDP growth, as published by INE: domestic and external "
                      "demand add up to GDP growth, give or take rounding."),
            )],
            "charts": [
                {"id": "gdp-growth", "title": "Real GDP growth",
                 "subtitle": "% change on the previous quarter (bars) and on a year earlier (line)",
                 "kind": "bar", "signed": True, "unit": "%", "decimals": 1, "start": "2022-01-01",
                 "series": [("gdp", "pop", "q/q"), ("gdp", "yoy", "y/y", {"kind": "line"})]},
                {"id": "gdp-contributions", "title": "What drives annual growth",
                 "subtitle": "Contributions to GDP growth on a year earlier, percentage points",
                 "kind": "bar", "stack": True, "signed": True, "unit": "pp", "decimals": 1, "start": "2022-01-01",
                 "series": [("contrib_domestic_yy", "level", "Domestic demand"),
                            ("contrib_external_yy", "level", "External demand"),
                            ("gdp", "yoy", "GDP", {"kind": "line", "color": "ink"})]},
                {"id": "investment", "title": "Investment",
                 "subtitle": "Real fixed investment, % change on a year earlier",
                 "kind": "line", "unit": "%", "decimals": 1, "start": "2022-01-01",
                 "series": [("investment_construction", "yoy", "Construction"), ("investment_housing", "yoy", "Housing"),
                            ("investment_equipment", "yoy", "Equipment")]},
                {"id": "exports", "title": "Exports",
                 "subtitle": "Real exports, % change on a year earlier; services include tourism",
                 "kind": "line", "unit": "%", "decimals": 1, "start": "2023-01-01",
                 "series": [("exports_goods", "yoy", "Goods"), ("exports_services", "yoy", "Services")]},
                {"id": "sectors", "title": "Output by sector",
                 "subtitle": "Real gross value added, % change on a year earlier",
                 "kind": "line", "unit": "%", "decimals": 1, "start": "2022-01-01",
                 "series": [("gva_industry", "yoy", "Industry"), ("gva_construction", "yoy", "Construction"),
                            ("gva_services", "yoy", "Services")]},
            ],
        },
        {
            "id": "productivity",
            "title": "Productivity and labour costs",
            "intro": ("Output per job and per hour worked, and the labour cost of each unit of output. "
                      "INE publishes these as changes on a year earlier."),
            "tables": [Table(
                title="Productivity and costs",
                caption="% change on a year earlier",
                columns=LEVELS,
                rows=[
                    Row("productivity_fte", "Productivity per full-time equivalent job", is_rate=True),
                    Row("productivity_hour", "Productivity per hour worked", is_rate=True),
                    Row("compensation_per_employee", "Compensation per employee", is_rate=True),
                    Row("unit_labour_cost", "Unit labour cost", is_rate=True),
                ],
            )],
            "charts": [
                {"id": "productivity", "title": "Productivity and unit labour costs",
                 "subtitle": "Productivity per hour, pay per employee and unit labour cost, % change on a year earlier",
                 "kind": "line", "unit": "%", "decimals": 1, "start": "2022-01-01",
                 "series": [("productivity_hour", "level", "Productivity"),
                            ("compensation_per_employee", "level", "Pay"),
                            ("unit_labour_cost", "level", "Unit labour cost")]},
            ],
        },
    ],
    # ------------------------------------------------------------------ Labour
    "labour": [
        {
            "id": "registrations",
            "title": "Social Security registrations",
            "intro": ("Workers registered with the Social Security (afiliados), the earliest monthly read on jobs, "
                      "and job seekers registered at public employment offices (paro registrado)."),
            "tables": [
                Table(
                    title="Monthly change",
                    caption="Average change per month, thousands",
                    columns=[AvgChange("1-mo", 1), AvgChange("3-mo", 3), AvgChange("12-mo", 12)],
                    rows=[Row("afiliados", "Registrations", season="ours"),
                          Row("paro_registrado", "Registered unemployment", season="ours")],
                    note=("The 1- and 3-month columns are seasonally adjusted by EconPulse, so they can differ from the "
                          "ministry's own adjusted figures. The 12-month column uses the published data."),
                ),
                Table(
                    title="Level",
                    caption="Thousands, as published",
                    columns=LEVELS,
                    rows=[Row("afiliados", "Registrations"), Row("paro_registrado", "Registered unemployment")],
                ),
            ],
            "charts": [
                {"id": "afiliados-change", "title": "Registrations: monthly change",
                 "subtitle": "Thousands, seasonally adjusted by EconPulse",
                 "kind": "bar", "signed": True, "unit": "k", "decimals": 1, "start": "2022-01-01",
                 "series": [("afiliados", "sa_diff", "Monthly change")]},
                {"id": "paro-change", "title": "Registered unemployment: monthly change",
                 "subtitle": "Thousands, seasonally adjusted by EconPulse",
                 "kind": "bar", "signed": True, "unit": "k", "decimals": 1, "start": "2022-01-01",
                 "series": [("paro_registrado", "sa_diff", "Monthly change")]},
                {"id": "registrations-yoy", "title": "Jobs and job seekers",
                 "subtitle": "% change on a year earlier",
                 "kind": "line", "unit": "%", "decimals": 1, "start": "2022-01-01",
                 "series": [("afiliados", "yoy", "Registrations"), ("paro_registrado", "yoy", "Registered unemployed")]},
            ],
        },
        {
            "id": "epa",
            "title": "Labour force survey (EPA)",
            "intro": ("INE's quarterly household survey, the official measure of unemployment. It is not seasonally "
                      "adjusted, so the comparison with a year earlier is the cleanest."),
            "tables": [
                Table(
                    title="EPA",
                    caption="% unless stated",
                    columns=LEVELS,
                    rows=[
                        Row("unemployment_epa", "Unemployment rate"),
                        Row("long_term_unemployment", "Long-term unemployment rate"),
                        Row("activity_rate", "Activity rate"),
                        Row("employment_rate", "Employment rate"),
                        Row("temporary_rate", "Temporary contracts, % of employees"),
                        Row("employment_epa", "Employment, thousands"),
                    ],
                ),
                Table(
                    title="Monthly estimates",
                    caption="Unemployment rate, %, seasonally adjusted (Eurostat)",
                    columns=LEVELS,
                    rows=[Row("unemployment_monthly", "All ages"), Row("youth_unemployment", "Under 25")],
                ),
            ],
            "charts": [
                {"id": "unemployment", "title": "Unemployment rate",
                 "subtitle": "% of the labour force: Eurostat's monthly estimate (adjusted) and the EPA (quarterly, unadjusted)",
                 "kind": "line", "unit": "%", "decimals": 1, "start": "2015-01-01",
                 "series": [("unemployment_monthly", "level", "Monthly (SA)"), ("unemployment_epa", "level", "EPA")]},
                {"id": "youth", "title": "Youth unemployment",
                 "subtitle": "Under 25s, % of the labour force, seasonally adjusted",
                 "kind": "line", "unit": "%", "decimals": 1, "start": "2015-01-01",
                 "series": [("youth_unemployment", "level", "Under 25s")]},
                {"id": "temporary", "title": "Temporary contracts",
                 "subtitle": "% of employees; the 2022 labour reform took effect that spring",
                 "kind": "line", "unit": "%", "decimals": 1, "start": "2015-01-01",
                 "series": [("temporary_rate", "level", "Temporary contracts")]},
            ],
        },
    ],
    # ------------------------------------------------------------------ Wages
    "wages": [
        {
            "id": "pay",
            "title": "Pay growth",
            "intro": ("What employers pay per worker and per hour (INE's quarterly labour cost survey, ETCL), "
                      "pay in the national accounts, and rises agreed in collective agreements."),
            "tables": [Table(
                title="Pay",
                caption="% change on a year earlier",
                columns=LEVELS,
                rows=[
                    Row("wage_cost", "Wage cost per worker", transform="yoy"),
                    Row("wage_cost_ordinary", "Regular pay only (no bonuses)", transform="yoy", indent=1),
                    Row("wage_cost_hour", "Wage cost per hour", transform="yoy"),
                    Row("labour_cost", "Total labour cost per worker", transform="yoy"),
                    Row("lci_wages", "Labour cost index, wages (Eurostat)", transform="yoy"),
                    Row("compensation_per_employee", "Compensation per employee (national accounts)"),
                    Row("wage_agreements", "Rise agreed in collective agreements, this year"),
                    Heading("After inflation"),
                    Row("real_wage", "Real wage cost per worker", transform="yoy"),
                ],
                note=("The labour cost survey (ETCL) is not seasonally adjusted and bonuses move between quarters, "
                      "so pay is compared with a year earlier. The collective-agreements figure is the average rise "
                      "agreed for the current year in agreements registered so far, not a change on a year earlier."),
            )],
            "charts": [
                {"id": "wages-prices", "title": "Wages and prices",
                 "subtitle": "% change on a year earlier: wage cost per worker (quarterly) and CPI (monthly)",
                 "kind": "line", "unit": "%", "decimals": 1, "start": "2021-07-01",
                 "series": [("wage_cost", "yoy", "Wages"), ("cpi", "level", "CPI")]},
                {"id": "real-wages", "title": "Real wages",
                 "subtitle": "Wage cost per worker deflated by the CPI, % change on a year earlier",
                 "kind": "bar", "signed": True, "unit": "%", "decimals": 1, "start": "2021-07-01",
                 "series": [("real_wage", "yoy", "Real wages")]},
                {"id": "agreements", "title": "Rises agreed in collective agreements",
                 "subtitle": "Average rise agreed for the year in agreements registered so far, %",
                 "kind": "line", "unit": "%", "decimals": 2, "start": "2015-01-01",
                 "series": [("wage_agreements", "level", "Agreed rise")]},
            ],
        },
    ],
    # ------------------------------------------------------------------ Inflation
    "inflation": [
        {
            "id": "cpi",
            "title": "Consumer prices (IPC)",
            "intro": ("Spain's own consumer price index. Core inflation leaves out energy and unprocessed food, "
                      "the most volatile prices; INE splits the rest into services, goods and processed food."),
            "flash": [("cpi", "CPI"), ("core_cpi", "core CPI")],
            "tables": [Table(
                title="CPI",
                caption="% change",
                columns=HORIZONS,
                rows=[
                    Row("cpi_index", "CPI", season="ours"),
                    Row("core_cpi_index", "Core CPI", season="ours"),
                    Heading("Components"),
                    Row("cpi_services_index", "Services", season="ours"),
                    Row("cpi_goods_index", "Non-energy industrial goods", season="ours"),
                    Row("cpi_processed_food_index", "Processed food, drinks and tobacco", season="ours"),
                    Row("cpi_unprocessed_food_index", "Unprocessed food", season="ours"),
                    Row("cpi_energy_index", "Energy", season="ours"),
                    Heading("Selected items"),
                    Row("cpi_rent_index", "Rents", season="ours"),
                    Row("ppi", "Producer prices, domestic market", season="ours"),
                ],
                note=SA_NOTE,
            )],
            "charts": [
                {"id": "cpi", "title": "CPI inflation", "subtitle": "% change on a year earlier",
                 "kind": "line", "unit": "%", "decimals": 1, "start": "2019-01-01", "ref_lines": TARGET,
                 "series": [("cpi", "level", "CPI"), ("core_cpi", "level", "Core CPI")]},
                {"id": "core-momentum", "title": "Core CPI momentum",
                 "subtitle": "3-month annualised (seasonally adjusted by EconPulse) and 12-month % change",
                 "kind": "line", "unit": "%", "decimals": 1, "start": "2021-01-01", "ref_lines": TARGET,
                 "series": [("core_cpi_index", "sa_ann3m", "3-mo ann."), ("core_cpi_index", "yoy", "12-mo")]},
                {"id": "core-components", "title": "Inside core inflation", "subtitle": "% change on a year earlier",
                 "kind": "line", "unit": "%", "decimals": 1, "start": "2019-01-01",
                 "series": [("cpi_services_index", "yoy", "Services"), ("cpi_goods_index", "yoy", "Goods"),
                            ("cpi_processed_food_index", "yoy", "Processed food")]},
                {"id": "volatile", "title": "Energy and fresh food", "subtitle": "% change on a year earlier",
                 "kind": "line", "unit": "%", "decimals": 1, "start": "2019-01-01",
                 "series": [("cpi_energy_index", "yoy", "Energy"), ("cpi_unprocessed_food_index", "yoy", "Unprocessed food")]},
                {"id": "rents", "title": "Rents", "subtitle": "CPI rents, % change on a year earlier",
                 "kind": "line", "unit": "%", "decimals": 1, "start": "2015-01-01",
                 "series": [("cpi_rent_index", "yoy", "Rents")]},
                {"id": "ppi", "title": "Producer and consumer prices", "subtitle": "% change on a year earlier",
                 "kind": "line", "unit": "%", "decimals": 1, "start": "2019-01-01",
                 "series": [("ppi", "yoy", "Producer prices"), ("cpi", "level", "Consumer prices")]},
            ],
        },
        {
            "id": "hicp",
            "title": "Harmonised prices (IPCA) and the euro area",
            "intro": "The harmonised index is the measure the ECB targets, built the same way in every euro-area country.",
            "tables": [Table(
                title="HICP",
                caption="% change",
                columns=HORIZONS,
                rows=[
                    Row("hicp_index", "HICP", season="ours"),
                    Row("hicp_core_index", "Core HICP", season="ours"),
                    Heading("Euro area"),
                    Row("hicp_euro_area", "HICP", is_rate=True),
                    Row("hicp_core_euro_area", "Core HICP", is_rate=True),
                ],
                note="Core HICP leaves out energy, food, alcohol and tobacco. " + SA_NOTE.replace("INE publishes", "Eurostat publishes"),
            )],
            "charts": [
                {"id": "hicp-ea", "title": "Spain and the euro area", "subtitle": "HICP inflation, % change on a year earlier",
                 "kind": "line", "unit": "%", "decimals": 1, "start": "2019-01-01", "ref_lines": TARGET,
                 "series": [("hicp", "level", "Spain"), ("hicp_euro_area", "level", "Euro area")]},
                {"id": "core-ea", "title": "Core inflation: Spain and the euro area",
                 "subtitle": "Core HICP, % change on a year earlier",
                 "kind": "line", "unit": "%", "decimals": 1, "start": "2019-01-01", "ref_lines": TARGET,
                 "series": [("hicp_core", "level", "Spain"), ("hicp_core_euro_area", "level", "Euro area")]},
            ],
        },
        {
            "id": "pressures",
            "title": "Energy and expectations",
            "intro": ("Energy costs reach consumer prices quickly, and households' expectations feed into "
                      "wage bargaining."),
            "tables": [Table(
                title="Indicator",
                caption="Latest reading and earlier values",
                columns=LEVELS,
                rows=[
                    Row("electricity_price", "Electricity, day-ahead market"),
                    Row("brent_eur", "Brent crude in euros"),
                    Row("gas_eu", "European natural gas"),
                    Row("price_expectations", "Consumers' price expectations (balance)"),
                ],
            )],
            "charts": [
                {"id": "electricity", "title": "Electricity price", "subtitle": "Day-ahead market, daily average, €/MWh",
                 "kind": "line", "unit": "€/MWh", "decimals": 0, "start": "2025-01-01", "date_format": "%-d %b %Y",
                 "series": [("electricity_price", "level", "Day-ahead price")]},
                {"id": "expectations", "title": "Price expectations",
                 "subtitle": "Households expecting faster price rises over the next 12 months, net balance",
                 "kind": "line", "unit": "", "decimals": 1, "start": "2015-01-01",
                 "series": [("price_expectations", "level", "Balance")]},
            ],
        },
    ],
}


def page_indicator_ids(section: str) -> set[str]:
    """Every indicator a section page reads (tables, charts, flash notes)."""
    ids = set()
    for block in PAGES.get(section, []):
        for t in block["tables"]:
            ids |= t.indicator_ids()
        for c in block.get("charts", []):
            ids |= {s[0] for s in c["series"]}
        ids |= {i for i, _ in block.get("flash", [])}
    return ids


def _flash_note(block: dict, tables: list[dict], data: Data) -> str:
    """A line for flash estimates newer than the table, e.g. INE's CPI flash for the latest month."""
    catalog = data.store.load_catalog()
    through = tables[0]["through"] if tables else ""
    parts, period = [], None
    for ind_id, name in block.get("flash", []):
        s = data.raw(ind_id)
        if s is None or not catalog.get(ind_id, {}).get("flash"):
            continue
        s = s.dropna()
        period = period_label(s.index[-1], data.by_id[ind_id].freq)
        if period != through:
            parts.append(f"{name} {fmt_value(float(s.iloc[-1]), '%', 1)}")
    if not parts:
        return ""
    return (f"Flash estimate for {period}: {', '.join(parts)} on a year earlier. "
            "The table follows when INE publishes the full index.")


def build_page(section: str, indicators: list[Indicator], store: Store) -> dict:
    """Blocks for one section page, plus the chart specs its script draws."""
    data = Data(indicators, store)
    blocks, charts = [], []
    for block in PAGES.get(section, []):
        tables = [t for t in (build_table(t, data) for t in block["tables"]) if t]
        specs = [c for c in (build_chart(c, data.by_id, store) for c in block.get("charts", [])) if c]
        flash = _flash_note(block, tables, data)
        if not tables and not specs:
            continue
        blocks.append({"id": block["id"], "title": block["title"], "intro": block["intro"],
                       "tables": tables, "charts": specs, "flash": flash})
        charts += specs
    return {"blocks": blocks, "charts": charts}
