"""What each section page shows: blocks of econvitals-style tables and charts.

A block is a sub-heading with an intro, one or more tables (econpulse/tables.py) and
a grid of charts (econpulse/charts.py specs). Optional extras, computed from the data:
"facts" (a strip of key figures), "callout" (a sentence below the tables) and tables
given as functions (e.g. the ECB's recent decisions); "uses" lists the indicators
those functions read. Sections without blocks yet show their indicator list only
(see build.SECTION_PAGES for the batch that fills them).
"""

from . import policy
from .charts import build_chart, build_curve
from .registry import Indicator
from .snapshot import fmt_value, period_label
from .store import Store
from .tables import (AvgChange, Change, Contribution, Data, Heading, Level, Move, Row, Spread, Table,
                     build_table)

LEVELS = [Level("latest"), Level("prev"), Level("year")]
HORIZONS = [Change("1-mo ann.", 1, True), Change("3-mo ann.", 3, True), Change("6-mo ann.", 6, True), Change("12-mo", 12)]
SA_NOTE = ("Horizons under 12 months are annualised and use EconPulse seasonal adjustment, because INE publishes "
           "these indices unadjusted. The 12-month column matches the published annual rates.")
TARGET = [{"y": 2, "label": "2% target"}]
MOVES = [Level("latest"), Move("1-day", "day"), Move("1-week", "week"), Move("YTD", "ytd"), Move("1-yr", "year")]
SPAIN_CURVE = [("es_12m_bill", "1y"), ("es_3y", "3y"), ("es_5y", "5y"), ("es_10y", "10y"), ("es_15y", "15y"), ("es_30y", "30y")]
AAA_CURVE = [("aaa_1y", "1y"), ("aaa_3y", "3y"), ("aaa_5y", "5y"), ("aaa_10y", "10y"), ("aaa_15y", "15y"), ("aaa_30y", "30y")]
FORWARDS = [("aaa_fwd_3m", "3m"), ("aaa_fwd_6m", "6m"), ("aaa_fwd_9m", "9m"), ("aaa_fwd_1y", "1y"),
            ("aaa_fwd_2y", "2y"), ("aaa_fwd_3y", "3y")]
DAILY = "%-d %b %Y"

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
    # ------------------------------------------------------------------ Financial
    "financial": [
        {
            "id": "markets",
            "title": "Markets",
            "intro": ("The latest close and how far each market has moved. Yields come from Banco de España, exchange "
                      "rates are the ECB's daily reference rates and Brent is the US EIA spot price (via FRED)."),
            "tables": [Table(
                title="Market",
                caption="Latest close; rates move in basis points (bp), prices in %",
                columns=MOVES,
                rows=[
                    Heading("Bonds and rates"),
                    Row("es_10y", "Spain 10-year yield"),
                    Row("de_10y", "Germany 10-year yield"),
                    Row("risk_premium", "Prima de riesgo"),
                    Row("euribor_12m", "12-month Euribor"),
                    Heading("Shares"),
                    Row("ibex35", "IBEX 35"),
                    Heading("The euro, per euro"),
                    Row("eurusd", "US dollars"),
                    Row("eurgbp", "British pounds"),
                    Row("eurchf", "Swiss francs"),
                    Row("eurjpy", "Japanese yen"),
                    Heading("Energy"),
                    Row("brent_usd", "Brent crude, dollars"),
                    Row("brent_eur", "Brent crude, euros"),
                    Row("gas_eu", "European natural gas (monthly)"),
                    Row("electricity_price", "Electricity, day-ahead"),
                ],
                note=("Each row is the latest close its source has published; a date next to a row means it differs "
                      "from the rest. For the euro, a rise means a stronger euro."),
            )],
            "charts": [
                {"id": "ibex", "title": "IBEX 35", "subtitle": "Index, daily close",
                 "kind": "line", "unit": "", "decimals": 0, "start": "2024-01-01", "date_format": DAILY,
                 "series": [("ibex35", "level", "IBEX 35")]},
                {"id": "eurusd", "title": "The euro against the dollar", "subtitle": "US dollars per euro, daily",
                 "kind": "line", "unit": "", "decimals": 4, "start": "2024-01-01", "date_format": DAILY,
                 "series": [("eurusd", "level", "EUR/USD")]},
                {"id": "brent", "title": "Brent crude", "subtitle": "Price per barrel, in dollars and in euros, daily",
                 "kind": "line", "unit": "", "decimals": 1, "start": "2024-01-01", "date_format": DAILY,
                 "series": [("brent_usd", "level", "Dollars"), ("brent_eur", "level", "Euros")]},
            ],
        },
        {
            "id": "bonds",
            "title": "Bond yields and the prima de riesgo",
            "intro": ("What the Spanish state pays to borrow at each maturity, and the extra it pays over the safest "
                      "euro-area governments. The prima de riesgo is the gap with Germany at 10 years."),
            "tables": [Table(
                title="Spanish government bonds",
                caption="Yield, %; changes and the spread over AAA euro-area bonds in basis points",
                columns=[Level("latest"), Move("1-week", "week"), Move("1-month", "month"), Move("YTD", "ytd"),
                         Spread("Over AAA")],
                rows=[
                    Row("es_12m_bill", "12-month bill", vs="aaa_1y"),
                    Row("es_3y", "3-year", vs="aaa_3y"),
                    Row("es_5y", "5-year", vs="aaa_5y"),
                    Row("es_10y", "10-year", vs="aaa_10y"),
                    Row("es_15y", "15-year", vs="aaa_15y"),
                    Row("es_30y", "30-year", vs="aaa_30y"),
                    Heading("Over Germany"),
                    Row("risk_premium", "Prima de riesgo, 10-year"),
                ],
                note=("AAA yields are the ECB's estimate of the curve for AAA-rated euro-area governments, the closest "
                      "thing to a risk-free euro rate. Banco de España's prima de riesgo uses benchmark bonds, so it "
                      "differs a little from Spain's 10-year yield minus Germany's."),
            )],
            "charts": [
                {"id": "curve", "curve": True, "title": "Spanish yield curve", "subtitle": "Yield by maturity, %",
                 "unit": "%", "decimals": 2,
                 "lines": [{"at": "latest", "name": "{date}", "points": SPAIN_CURVE},
                           {"at": "month", "name": "A month earlier", "points": SPAIN_CURVE},
                           {"at": "yearend", "name": "End-{prev_year}", "points": SPAIN_CURVE}]},
                {"id": "curve-aaa", "curve": True, "title": "Spain and the safest euro-area bonds",
                 "subtitle": "Yield by maturity, %: Spain against the AAA euro-area curve",
                 "unit": "%", "decimals": 2,
                 "lines": [{"at": "latest", "name": "Spain", "points": SPAIN_CURVE},
                           {"at": "latest", "name": "Euro area AAA", "points": AAA_CURVE}]},
                {"id": "risk-premium", "title": "Prima de riesgo since 2008",
                 "subtitle": "Spain's 10-year yield over Germany's, basis points, daily; it peaked at 636 bp in July 2012",
                 "kind": "line", "unit": "bp", "decimals": 0, "start": "2008-01-01", "date_format": DAILY,
                 "series": [("risk_premium", "level", "Prima de riesgo")]},
                {"id": "yields-10y", "title": "10-year yields: Spain and Germany",
                 "subtitle": "%, daily; the gap between the lines is the prima de riesgo",
                 "kind": "line", "unit": "%", "decimals": 2, "start": "2022-01-01", "date_format": DAILY,
                 "series": [("es_10y", "level", "Spain"), ("de_10y", "level", "Germany")]},
            ],
        },
        {
            "id": "euribor",
            "title": "Euribor and mortgages",
            "intro": ("Most Spanish mortgages are variable-rate: once or twice a year the payment resets to the "
                      "12-month Euribor plus a fixed margin, so ECB decisions reach households quickly."),
            "tables": [Table(
                title="Rate",
                caption="%",
                columns=LEVELS,
                rows=[
                    Row("euribor_3m", "3-month Euribor"),
                    Row("euribor_12m", "12-month Euribor"),
                    Row("es_12m_bill", "12-month Treasury bill"),
                    Row("mortgage_rate", "New mortgages, average rate"),
                ],
                note="The mortgage rate is the ECB's average for new house-purchase loans to Spanish households.",
            )],
            "callout": policy.mortgage_check,
            "uses": ["euribor_12m"],
            "charts": [
                {"id": "euribor-mortgages", "title": "Euribor and mortgage rates",
                 "subtitle": "%: 12-month Euribor (daily) and the average rate on new mortgages (monthly)",
                 "kind": "line", "unit": "%", "decimals": 2, "start": "2019-01-01",
                 "series": [("euribor_12m", "level", "12-month Euribor"), ("mortgage_rate", "level", "New mortgages")]},
                {"id": "euribor-ecb", "title": "Euribor and the ECB",
                 "subtitle": "%: Euribor follows the ECB's deposit rate and where markets expect it to go",
                 "kind": "line", "unit": "%", "decimals": 2, "start": "2019-01-01", "date_format": DAILY,
                 "series": [("ecb_deposit_rate", "level", "ECB deposit rate", {"shape": "hv"}),
                            ("euribor_3m", "level", "3-month Euribor"), ("euribor_12m", "level", "12-month Euribor")]},
            ],
        },
    ],
    # ------------------------------------------------------------------ ECB
    "ecb": [
        {
            "id": "rates",
            "title": "Policy rates",
            "intro": ("The ECB sets three rates. The one that steers the economy is the deposit facility rate, what banks "
                      "earn on money left at the central bank: it puts a floor under market rates, and €STR, the "
                      "overnight rate banks charge each other, trades just below it."),
            "facts": policy.ecb_facts,
            "uses": ["ecb_deposit_rate", "estr"],
            "tables": [
                Table(
                    title="Rate",
                    caption="%; changes in basis points",
                    columns=[Level("latest"), Move("1-month", "month"), Move("YTD", "ytd"), Move("1-yr", "year")],
                    rows=[
                        Row("ecb_deposit_rate", "Deposit facility"),
                        Row("ecb_mro_rate", "Main refinancing operations"),
                        Row("ecb_mlf_rate", "Marginal lending facility"),
                        Row("estr", "€STR, overnight market rate"),
                    ],
                ),
                policy.decisions_table,
            ],
            "charts": [
                {"id": "policy-rates", "title": "ECB rates since 2019", "subtitle": "%, daily",
                 "kind": "line", "unit": "%", "decimals": 2, "start": "2019-01-01", "date_format": DAILY,
                 "series": [("ecb_deposit_rate", "level", "Deposit rate", {"shape": "hv"}),
                            ("ecb_mro_rate", "level", "Main refinancing", {"shape": "hv"}),
                            ("estr", "level", "€STR")]},
                {"id": "rates-inflation", "title": "Rates and inflation",
                 "subtitle": "%: the ECB deposit rate and euro-area inflation (HICP, headline and core)",
                 "kind": "line", "unit": "%", "decimals": 1, "start": "2019-01-01", "ref_lines": TARGET,
                 "series": [("ecb_deposit_rate", "level", "Deposit rate", {"shape": "hv"}),
                            ("hicp_euro_area", "level", "Inflation"), ("hicp_core_euro_area", "level", "Core")]},
                {"id": "deposit-history", "title": "The deposit rate since 1999", "subtitle": "%",
                 "kind": "line", "unit": "%", "decimals": 2, "start": "1999-01-01", "date_format": DAILY,
                 "series": [("ecb_deposit_rate", "level", "Deposit rate", {"shape": "hv"})]},
            ],
        },
        {
            "id": "expectations",
            "title": "What markets expect",
            "intro": ("There is no free feed of the swap rates traders use to price ECB decisions. As a rough stand-in, "
                      "these are forward rates on AAA euro-area government bonds: the short-term rate the bond market "
                      "implies for each future date. They include a term premium, so they tend to overstate the "
                      "expected path, more so further out."),
            "tables": [Table(
                title="Forward rate",
                caption="%; the gap with today's deposit rate in basis points",
                columns=[Level("latest"), Level("prev"), Spread("Over deposit rate")],
                rows=[
                    Row("aaa_fwd_3m", "3 months ahead", vs="ecb_deposit_rate"),
                    Row("aaa_fwd_6m", "6 months ahead", vs="ecb_deposit_rate"),
                    Row("aaa_fwd_9m", "9 months ahead", vs="ecb_deposit_rate"),
                    Row("aaa_fwd_1y", "1 year ahead", vs="ecb_deposit_rate"),
                    Row("aaa_fwd_2y", "2 years ahead", vs="ecb_deposit_rate"),
                    Row("aaa_fwd_3y", "3 years ahead", vs="ecb_deposit_rate"),
                ],
            )],
            "charts": [
                {"id": "path", "curve": True, "title": "Market-implied path",
                 "subtitle": "Euro-area AAA forward rates by horizon, %", "x_title": "Horizon",
                 "unit": "%", "decimals": 2, "ref_from": [("ecb_deposit_rate", "Deposit rate")],
                 "lines": [{"at": "latest", "name": "{date}", "points": FORWARDS},
                           {"at": "month", "name": "A month earlier", "points": FORWARDS}]},
                {"id": "forward-1y", "title": "The rate expected a year ahead",
                 "subtitle": "%: AAA forward rate one year ahead and the deposit rate",
                 "kind": "line", "unit": "%", "decimals": 2, "start": "2022-01-01", "date_format": DAILY,
                 "series": [("aaa_fwd_1y", "level", "1 year ahead"),
                            ("ecb_deposit_rate", "level", "Deposit rate", {"shape": "hv"})]},
            ],
        },
    ],
}


def page_indicator_ids(section: str) -> set[str]:
    """Every indicator a section page reads (tables, charts, flash notes, extras)."""
    ids = set()
    for block in PAGES.get(section, []):
        for t in block["tables"]:
            if isinstance(t, Table):
                ids |= t.indicator_ids()
        for c in block.get("charts", []):
            if c.get("curve"):
                ids |= {i for line in c["lines"] for i, _ in line["points"]} | {i for i, _ in c.get("ref_from", [])}
            else:
                ids |= {s[0] for s in c["series"]}
        ids |= {i for i, _ in block.get("flash", [])} | set(block.get("uses", []))
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
        tables = [t for t in ((build_table(t, data) if isinstance(t, Table) else t(data)) for t in block["tables"]) if t]
        specs = [c for c in ((build_curve if c.get("curve") else build_chart)(c, data.by_id, store)
                             for c in block.get("charts", [])) if c]
        flash = _flash_note(block, tables, data)
        facts = block["facts"](data) if "facts" in block else []
        callout = block["callout"](data) if "callout" in block else None
        if not tables and not specs:
            continue
        blocks.append({"id": block["id"], "title": block["title"], "intro": block["intro"], "facts": facts,
                       "tables": tables, "callout": callout, "charts": specs, "flash": flash})
        charts += specs
    return {"blocks": blocks, "charts": charts}
