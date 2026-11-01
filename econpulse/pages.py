"""What each section page shows: blocks of econvitals-style tables and charts.

A block is a sub-heading with an intro, one or more tables (econpulse/tables.py) and
a grid of charts (econpulse/charts.py specs). Optional extras, computed from the data:
"facts" (a strip of key figures), "callout" (a sentence below the tables), and tables
or charts given as functions (the ECB's recent decisions, the analytics); "uses"
lists the indicators those functions read. Sections without blocks yet show their indicator list only
(see build.SECTION_PAGES for the batch that fills them).
"""

from . import analytics, demography, forecasts, peers, policy, sectortables, surprises, underlying, workstats
from .charts import build_chart, build_curve, build_ranking, build_xy
from .registry import Indicator
from .snapshot import fmt_value, period_label
from .store import Store
from .tables import (AvgChange, Change, Contribution, Data, Heading, Level, Move, Panel, PanelColumn, PanelRow,
                     Row, Spread, Table, YearToDate, build_panel, build_table)

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
FLOWS = [Level("latest"), Change("y/y", 12), YearToDate("Year to date"), YearToDate("YTD y/y", change=True)]

# Autonomous communities (slugs match the `regions` list in indicators.yaml).
REGIONS = [
    ("andalucia", "Andalucía"), ("aragon", "Aragón"), ("asturias", "Asturias"), ("baleares", "Illes Balears"),
    ("canarias", "Canarias"), ("cantabria", "Cantabria"), ("castilla_leon", "Castilla y León"),
    ("castilla_mancha", "Castilla-La Mancha"), ("cataluna", "Cataluña"), ("valenciana", "Comunitat Valenciana"),
    ("extremadura", "Extremadura"), ("galicia", "Galicia"), ("madrid", "Madrid"), ("murcia", "Murcia"),
    ("navarra", "Navarra"), ("pais_vasco", "País Vasco"), ("rioja", "La Rioja"),
]


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
        {
            "id": "real-sector",
            "title": "IMF-style main indicators",
            "intro": ("Table 1 of the IMF's 2026 Article IV report for Spain, rebuilt from public data: actual years "
                      "from INE, Eurostat and the ECB, projections from the IMF's World Economic Outlook database. "
                      "That database publishes only some of the report's lines, so the others show … in the "
                      "projection years."),
            "facts": sectortables.facts,
            "uses": sorted(sectortables.REAL_SECTOR.indicator_ids()),
            "tables": [sectortables.table_function("real-sector")],
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
            "id": "sectors",
            "title": "Jobs by sector",
            "intro": ("Average monthly Social Security registrations by sector and by type of work, from the ministry's "
                      "monthly workbooks. The 1- and 3-month changes use the ministry's own seasonal adjustment; the "
                      "12-month change, the figures as published. From January 2026 the sectors follow the new "
                      "classification of activities (CNAE-2025); EconPulse links construction and services across the "
                      "change, which moved real estate development from one to the other. Every industry, month by "
                      "month, is on its own page (Labour market menu, or the chart's More link)."),
            "tables": [
                Table(
                    title="Monthly change",
                    caption="Average change per month, thousands",
                    columns=[AvgChange("1-mo", 1), AvgChange("3-mo", 3), AvgChange("12-mo", 12)],
                    rows=[Row("reg_sector_total", "All registrations", sa="reg_sector_total_sa"),
                          Heading("By sector"),
                          Row("reg_agriculture", "Agriculture, livestock and fishing", indent=1, sa="reg_agriculture_sa"),
                          Row("reg_industry", "Industry", indent=1, sa="reg_industry_sa"),
                          Row("reg_construction", "Construction", indent=1, sa="reg_construction_sa"),
                          Row("reg_services", "Services", indent=1, sa="reg_services_sa"),
                          Heading("By type of work"),
                          Row("reg_employees", "Employees", indent=1, sa="reg_employees_sa"),
                          Row("reg_self_employed", "Self-employed", indent=1, sa="reg_self_employed_sa")],
                    note=("The sectors add up to slightly less than the total: a few registrations have no activity "
                          "recorded."),
                ),
                Table(
                    title="Level",
                    caption="Thousands, as published, and % change on a year earlier",
                    columns=[Level("latest"), Change("12-mo", 12)],
                    rows=[Row("reg_sector_total", "All registrations"), Heading("By sector"),
                          Row("reg_agriculture", "Agriculture, livestock and fishing", indent=1),
                          Row("reg_industry", "Industry", indent=1), Row("reg_construction", "Construction", indent=1),
                          Row("reg_services", "Services", indent=1), Heading("By type of work"),
                          Row("reg_employees", "Employees", indent=1), Row("reg_self_employed", "Self-employed", indent=1)],
                ),
            ],
            "charts": [
                {"id": "sector-jobs-change", "title": "Jobs by sector: monthly change", "link": "industry-detail.html",
                 "subtitle": "Thousands, seasonally adjusted by the Social Security; agriculture is in the table",
                 "kind": "bar", "stack": True, "signed": True, "unit": "k", "decimals": 1, "start": "2023-01-01",
                 "series": [("reg_services_sa", "diff", "Services"), ("reg_industry_sa", "diff", "Industry"),
                            ("reg_construction_sa", "diff", "Construction")]},
                {"id": "sector-jobs-yoy", "title": "Jobs by sector: change on a year earlier",
                 "subtitle": "% change in average registrations, as published",
                 "kind": "line", "unit": "%", "decimals": 1, "start": "2023-01-01",
                 "series": [("reg_services", "yoy", "Services"), ("reg_industry", "yoy", "Industry"),
                            ("reg_construction", "yoy", "Construction"),
                            ("reg_sector_total", "yoy", "All registrations", {"color": "ink"})]},
            ],
        },
        {
            "id": "unemployment-sectors",
            "title": "Unemployment by sector",
            "intro": ("Registered unemployment by the sector of the last job, from the public employment service "
                      "(SEPE), and the number of people receiving unemployment benefits."),
            "tables": [
                Table(
                    title="Monthly change",
                    caption="Average change per month, thousands",
                    columns=[AvgChange("1-mo", 1), AvgChange("3-mo", 3), AvgChange("12-mo", 12)],
                    rows=[Row("paro_registrado", "Registered unemployment", season="ours"),
                          Heading("By sector of the last job"),
                          Row("paro_agriculture", "Agriculture", indent=1, season="ours"),
                          Row("paro_industry", "Industry", indent=1, season="ours"),
                          Row("paro_construction", "Construction", indent=1, season="ours"),
                          Row("paro_services", "Services", indent=1, season="ours"),
                          Row("paro_no_previous_job", "No previous job", indent=1, season="ours")],
                    note=("The 1- and 3-month columns are seasonally adjusted by EconPulse; the 12-month column uses "
                          "the published data."),
                ),
                Table(
                    title="Level",
                    caption="Thousands, as published, and % change on a year earlier",
                    columns=[Level("latest"), Change("12-mo", 12)],
                    rows=[Row("paro_registrado", "Registered unemployment"), Heading("By sector of the last job"),
                          Row("paro_agriculture", "Agriculture", indent=1), Row("paro_industry", "Industry", indent=1),
                          Row("paro_construction", "Construction", indent=1), Row("paro_services", "Services", indent=1),
                          Row("paro_no_previous_job", "No previous job", indent=1), Heading("Benefits"),
                          Row("benefit_recipients", "Unemployment benefit recipients", indent=1)],
                ),
            ],
            "charts": [
                {"id": "paro-sectors-yoy", "title": "Unemployment by sector: change on a year earlier",
                 "subtitle": "% change in registered unemployment, as published",
                 "kind": "line", "unit": "%", "decimals": 1, "start": "2023-01-01",
                 "series": [("paro_services", "yoy", "Services"), ("paro_industry", "yoy", "Industry"),
                            ("paro_construction", "yoy", "Construction"),
                            ("paro_registrado", "yoy", "All", {"color": "ink"})]},
            ],
        },
        {
            "id": "contracts",
            "title": "Contracts and the labour reform",
            "intro": ("Employment contracts registered each month with the public employment service. The labour "
                      "reform in force since 2022 restricted temporary contracts: permanent ones, including the "
                      "seasonal fijo discontinuo kind, went from about one in ten new contracts in 2019–21 to about "
                      "four in ten since."),
            "tables": [
                Table(
                    title="Contracts",
                    caption="Thousands",
                    columns=FLOWS,
                    rows=[Row("contracts_total", "All contracts"),
                          Row("contracts_permanent", "Permanent", indent=1),
                          Row("contracts_fixed_discontinuous", "o.w. fijo discontinuo (seasonal permanent)", indent=2),
                          Row("contracts_conversions", "o.w. conversions from temporary", indent=2),
                          Row("contracts_temporary", "Temporary", indent=1),
                          Heading("By working time"),
                          Row("contracts_full_time", "Full time", indent=1),
                          Row("contracts_part_time", "Part time", indent=1),
                          Row("contracts_fixed_discontinuous", "Fijo discontinuo", indent=1)],
                    note="By working time, the public employment service counts fijo discontinuo contracts separately.",
                ),
                Table(
                    title="Shares",
                    caption="% of all contracts, average of the past 12 months",
                    columns=LEVELS,
                    rows=[Row("contracts_permanent_share", "Permanent", transform="avg_1y", flow=False),
                          Row("contracts_fd_share", "o.w. fijo discontinuo", indent=1, transform="avg_1y", flow=False),
                          Row("contracts_part_time_share", "Part time", transform="avg_1y", flow=False)],
                ),
            ],
            "charts": [
                {"id": "contracts-share", "title": "Permanent contracts and the 2022 reform",
                 "subtitle": "% of contracts registered, average of the past 12 months",
                 "kind": "line", "unit": "%", "decimals": 1, "start": "2015-01-01",
                 "series": [("contracts_permanent_share", "avg_1y", "Permanent"),
                            ("contracts_fd_share", "avg_1y", "Fijo discontinuo"),
                            ("contracts_part_time_share", "avg_1y", "Part time")]},
                {"id": "contracts-mix", "title": "Contracts by type",
                 "subtitle": "Thousands registered over the past 12 months",
                 "kind": "bar", "stack": True, "unit": "k", "decimals": 0, "start": "2018-01-01",
                 "series": [("contracts_temporary", "sum_1y", "Temporary"),
                            ("contracts_permanent_other", "sum_1y", "Other permanent"),
                            ("contracts_fixed_discontinuous", "sum_1y", "Fijo discontinuo")]},
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
        {
            "id": "groups",
            "title": "Who works: age, sex, citizenship and education",
            "intro": ("The labour force survey by group, from Eurostat. Employment rates have risen for every "
                      "group since 2019, most for women and people aged 55–64, and prime-age employment "
                      "(25–54) is closing in on the euro area's. Charts show averages of the past four quarters, "
                      "as the figures are not seasonally adjusted."),
            "tables": [demography.GROUPS],
            "charts": [
                {"id": "prime-employment", "title": "Prime-age employment: Spain and the euro area",
                 "subtitle": "Employment rate, ages 25–54, %, average of the past four quarters",
                 "kind": "line", "unit": "%", "decimals": 1, "start": "2005-01-01",
                 "series": [("lfs_emp_prime", "avg_1y", "Spain"),
                            ("lfs_emp_prime_ea", "avg_1y", "Euro area", {"color": "ink"})]},
                {"id": "employment-age", "title": "Employment rate by age",
                 "subtitle": "%, average of the past four quarters",
                 "kind": "line", "unit": "%", "decimals": 1, "start": "2005-01-01",
                 "series": [("lfs_emp_young", "avg_1y", "15–24"), ("lfs_emp_prime", "avg_1y", "25–54"),
                            ("lfs_emp_older", "avg_1y", "55–64")]},
                {"id": "employment-sex", "title": "Women and men at prime age",
                 "subtitle": "Employment rate, ages 25–54, %, average of the past four quarters",
                 "kind": "line", "unit": "%", "decimals": 1, "start": "2005-01-01",
                 "series": [("lfs_emp_prime_men", "avg_1y", "Men"), ("lfs_emp_prime_women", "avg_1y", "Women")]},
                {"id": "unemployment-citizenship", "title": "Unemployment by citizenship",
                 "subtitle": "Ages 15–64, % of the labour force, average of the past four quarters",
                 "kind": "line", "unit": "%", "decimals": 1, "start": "2005-01-01",
                 "series": [("lfs_une_spanish", "avg_1y", "Spanish"), ("lfs_une_eu", "avg_1y", "Other EU"),
                            ("lfs_une_noneu", "avg_1y", "Non-EU")]},
                {"id": "unemployment-education", "title": "Unemployment by education",
                 "subtitle": "Ages 25–64, % of the labour force, average of the past four quarters",
                 "kind": "line", "unit": "%", "decimals": 1, "start": "2005-01-01",
                 "series": [("lfs_une_edu_low", "avg_1y", "Lower secondary"),
                            ("lfs_une_edu_mid", "avg_1y", "Upper secondary"),
                            ("lfs_une_edu_high", "avg_1y", "Tertiary")]},
            ],
        },
        {
            "id": "ageing",
            "title": "Participation and an ageing population",
            "intro": ("As the baby-boom generations reach retirement, a growing share of adults are past working "
                      "age, which pulls down the participation and employment rates of everyone aged 15 and over "
                      "even when each age group works as much as before. EconPulse holds the population's mix by "
                      "sex and five-year age group at its 2008 shares, letting each group's own rate move, to show "
                      "how much of the change comes from ageing."),
            "facts": demography.ageing_facts,
            "callout": demography.ageing_callout,
            "tables": [Table(
                title="Ages 15 and over",
                caption="% of the population aged 15 and over, average of the past four quarters",
                columns=LEVELS,
                rows=[Row("lfs_participation", "Participation rate", transform="avg_1y", flow=False),
                      Row("lfs_participation_aged", "At the 2008 age mix", indent=1, transform="avg_1y", flow=False),
                      Row("lfs_epop", "Employment rate", transform="avg_1y", flow=False),
                      Row("lfs_epop_aged", "At the 2008 age mix", indent=1, transform="avg_1y", flow=False),
                      Row("lfs_share_65plus", "Aged 65 and over, % of people 15 and over", transform="avg_1y",
                          flow=False)],
                note=("EconPulse calculation from Eurostat's labour force survey: the rates of men and women in 13 age "
                      "groups (15–19 to 70–74, and 75 and over), weighted by each group's share of the population, "
                      "actual or as in 2008. People in private households only."),
            )],
            "charts": [
                {"id": "participation-ageing", "title": "Participation and ageing",
                 "subtitle": "Participation rate, ages 15 and over, %, average of the past four quarters",
                 "kind": "line", "unit": "%", "decimals": 1, "start": "2000-01-01",
                 "series": [("lfs_participation", "avg_1y", "Actual"),
                            ("lfs_participation_aged", "avg_1y", "At the 2008 age mix",
                             {"color": "ink", "dash": "dot"})]},
                {"id": "employment-ageing", "title": "Employment and ageing",
                 "subtitle": "Employment rate, ages 15 and over, %, average of the past four quarters",
                 "kind": "line", "unit": "%", "decimals": 1, "start": "2000-01-01",
                 "series": [("lfs_epop", "avg_1y", "Actual"),
                            ("lfs_epop_aged", "avg_1y", "At the 2008 age mix", {"color": "ink", "dash": "dot"})]},
                {"id": "participation-age", "title": "Participation by age",
                 "subtitle": "%, average of the past four quarters",
                 "kind": "line", "unit": "%", "decimals": 1, "start": "2005-01-01",
                 "series": [("lfs_act_young", "avg_1y", "15–24"), ("lfs_act_prime", "avg_1y", "25–54"),
                            ("lfs_act_older", "avg_1y", "55–64")]},
                {"id": "share-65", "title": "An older population",
                 "subtitle": "Aged 65 and over, % of people aged 15 and over, average of the past four quarters",
                 "kind": "line", "unit": "%", "decimals": 1, "start": "2000-01-01",
                 "series": [("lfs_share_65plus", "avg_1y", "Aged 65 and over")]},
            ],
        },
        {
            "id": "flows",
            "title": "Worker flows: finding and losing jobs",
            "intro": ("Behind the unemployment rate, people move all the time: some of the unemployed find work or "
                      "give up looking, and some of the employed lose their jobs or leave the labour force. Eurostat "
                      "follows the same people from one quarter to the next in the labour force survey. More of the "
                      "unemployed find a job each quarter than before the pandemic, and fewer workers lose theirs."),
            "tables": [Table(
                title="From one quarter to the next",
                caption="% of each group, seasonally adjusted",
                columns=LEVELS,
                rows=[Heading("The unemployed"),
                      Row("flow_une_emp", "Find a job", indent=1),
                      Row("flow_une_inac", "Stop looking (leave the labour force)", indent=1),
                      Heading("The employed"),
                      Row("flow_emp_une", "Lose their job", indent=1),
                      Row("flow_emp_inac", "Leave the labour force", indent=1),
                      Heading("The inactive"),
                      Row("flow_inac_emp", "Start work", indent=1)],
                note="Eurostat's labour market transitions, from the labour force survey's panel of households.",
            )],
            "charts": [
                {"id": "flows-unemployed", "title": "Where the unemployed go",
                 "subtitle": "% of the unemployed who, a quarter later, are employed or out of the labour force",
                 "kind": "line", "unit": "%", "decimals": 1, "start": "2010-01-01",
                 "series": [("flow_une_emp", "level", "Find a job"), ("flow_une_inac", "level", "Stop looking")]},
                {"id": "flows-employed", "title": "Losing or leaving a job",
                 "subtitle": "% of the employed who, a quarter later, are unemployed or out of the labour force",
                 "kind": "line", "unit": "%", "decimals": 1, "start": "2010-01-01",
                 "series": [("flow_emp_une", "level", "Lose their job"),
                            ("flow_emp_inac", "level", "Leave the labour force")]},
            ],
        },
        {
            "id": "hours",
            "title": "Hours worked",
            "intro": ("Hours show how much work gets done, not just how many people do it. Hours per person "
                      "employed have drifted down since the early 2000s as part-time work and shorter schedules "
                      "spread. INE's labour cost survey adds hours per employee by activity and the hours lost to "
                      "sick leave."),
            "callout": workstats.hours_callout,
            "tables": [Table(
                title="Hours",
                caption="Hours, unless stated",
                columns=LEVELS,
                rows=[Heading("National accounts, seasonally adjusted"),
                      Row("hours_per_person", "Hours a week per person employed", indent=1),
                      Row("hours_na", "Hours worked, millions a quarter", indent=1),
                      Row("persons_na", "People employed, thousands", indent=1),
                      Heading("Per employee a month, average of the past four quarters"),
                      Row("hours_etcl", "Hours worked", indent=1, transform="avg_1y", flow=False),
                      Row("hours_sick", "Hours lost to sick leave", indent=1, transform="avg_1y", flow=False),
                      Row("hours_overtime", "Overtime", indent=1, transform="avg_1y", flow=False)],
                note=("Hours a week are the quarter's hours per person employed divided by 13. Hours per employee "
                      "come from INE's labour cost survey (ETCL), which covers employees in industry, construction "
                      "and services, and are not seasonally adjusted."),
            )],
            "charts": [
                {"id": "hours-per-person", "title": "Hours per person employed",
                 "subtitle": "Hours worked a week, national accounts, seasonally adjusted",
                 "kind": "line", "unit": "", "decimals": 1, "start": "1995-01-01",
                 "series": [("hours_per_person", "level", "Hours a week")]},
                {"id": "sick-leave", "title": "Hours lost to sick leave",
                 "subtitle": "Hours per employee a month, average of the past four quarters",
                 "kind": "line", "unit": "", "decimals": 1, "start": "2009-01-01",
                 "series": [("hours_sick", "avg_1y", "Sick leave")]},
                {"id": "hours-sectors", "kind": "hbar", "title": "Hours worked by activity",
                 "subtitle": "Hours per employee a month, average of the past four quarters",
                 "unit": "", "decimals": 1, "x_title": "Activity", "transform": "avg_1y",
                 "items": workstats.items("hours", "avg_1y"),
                 "ref_from": [("hours_etcl", "All", "avg_1y")]},
            ],
        },
        {
            "id": "slack",
            "title": "Slack and vacancies",
            "intro": ("Unemployment understates how much spare labour there is. Eurostat's measure of slack adds "
                      "part-timers who want more hours and people who could work but are not looking. Vacancies show "
                      "the other side: the posts firms are trying to fill."),
            "tables": [Table(
                title="Labour market",
                caption="% unless stated",
                columns=LEVELS,
                rows=[
                    Row("labour_slack", "Labour market slack, % of the extended labour force"),
                    Row("unemployment_epa", "Unemployment rate (EPA)"),
                    Row("vacancies", "Job vacancies, thousands"),
                    Row("vacancies", "Job vacancies, average of the past four quarters", transform="avg_1y"),
                ],
                note="Vacancies are not seasonally adjusted, so the four-quarter average shows the trend.",
            )],
            "charts": [
                {"id": "slack", "title": "Slack and unemployment",
                 "subtitle": "% of the labour force; slack also counts the underemployed and people not looking",
                 "kind": "line", "unit": "%", "decimals": 1, "start": "2009-01-01",
                 "series": [("labour_slack", "level", "Slack (SA)"), ("unemployment_epa", "level", "Unemployment (EPA)")]},
                {"id": "beveridge", "kind": "xy", "title": "Beveridge curve",
                 "subtitle": "Each point is a quarter: unemployment against vacancies (four-quarter average)",
                 "start": "2014-04-01",
                 "x": ("unemployment_epa", "level", "Unemployment rate", "%"),
                 "y": ("vacancies", "avg_1y", "Vacancies", "k")},
            ],
        },
        {
            "id": "vacancies-sectors",
            "title": "Vacancies by activity",
            "intro": ("The posts firms and public bodies are trying to fill, from INE's labour cost survey. "
                      "Vacancies are few in Spain by European standards, and a large share of them are in public "
                      "administration."),
            "tables": [Table(
                title="Vacancies",
                caption="Thousands, average of the past four quarters",
                columns=LEVELS,
                rows=workstats.VACANCY_ROWS,
                note=("Not seasonally adjusted. Mining, energy, water and real estate are left out: INE does not "
                      "publish their vacancies in many quarters."),
            )],
            "charts": [
                {"id": "vacancies-ranking", "kind": "hbar", "title": "Where the vacancies are",
                 "subtitle": "Thousands, average of the past four quarters",
                 "unit": "k", "decimals": 1, "x_title": "Activity", "transform": "avg_1y",
                 "items": workstats.items("vacancies", "avg_1y")},
                {"id": "vacancies-sectors", "title": "Vacancies in the largest private activities",
                 "subtitle": "Thousands, average of the past four quarters",
                 "kind": "line", "unit": "k", "decimals": 1, "start": "2014-07-01",
                 "series": [("vacancies_trade", "avg_1y", "Trade"), ("vacancies_hospitality", "avg_1y", "Hospitality"),
                            ("vacancies_manufacturing", "avg_1y", "Manufacturing")]},
            ],
        },
        {
            "id": "layoffs",
            "title": "Collective dismissals and temporary layoffs",
            "intro": ("Firms in difficulty can dismiss groups of workers (despidos colectivos, through an ERE) or, "
                      "under an ERTE, suspend contracts or cut working hours for a time, keeping people on the payroll "
                      "while unemployment benefits cover part of their pay. The Ministry of Labour counts the workers "
                      "affected by the procedures of each month. Figures start in January 2023; December 2023 is "
                      "missing, as the ministry published only that year's total."),
            "facts": workstats.ere_facts,
            "tables": [Table(
                title="Workers affected",
                caption="Thousands",
                columns=FLOWS,
                rows=[Row("ere_total", "All procedures"),
                      Row("ere_dismissals", "Collective dismissals", indent=1),
                      Row("ere_suspensions", "Contract suspensions (ERTE)", indent=1),
                      Row("ere_reductions", "Cuts in working hours (ERTE)", indent=1)],
                note="Provisional monthly figures (Estadística de Regulación de Empleo); each year's final figures differ slightly.",
            )],
            "charts": [
                {"id": "layoffs-monthly", "title": "Workers affected each month",
                 "subtitle": "Thousands, by measure",
                 "kind": "bar", "stack": True, "unit": "k", "decimals": 1, "start": "2023-01-01",
                 "series": [("ere_dismissals", "level", "Dismissals"), ("ere_suspensions", "level", "Suspensions"),
                            ("ere_reductions", "level", "Cuts in hours")]},
                {"id": "layoffs-12m", "title": "Workers affected over the past 12 months",
                 "subtitle": "Thousands, by measure",
                 "kind": "line", "unit": "k", "decimals": 1, "start": "2024-01-01",
                 "series": [("ere_dismissals", "sum_1y", "Dismissals"), ("ere_suspensions", "sum_1y", "Suspensions"),
                            ("ere_reductions", "sum_1y", "Cuts in hours")]},
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
        {
            "id": "pay-sectors",
            "title": "Pay by activity",
            "intro": ("Average wage cost per worker by activity, from INE's labour cost survey: gross pay including "
                      "bonuses, before the worker's tax and contributions, for full-time and part-time employees "
                      "together, a month and per hour actually worked, with the share that comes from bonuses and "
                      "extra months' pay. Averages of four quarters, as bonuses make pay seasonal."),
            "callout": workstats.pay_callout,
            "uses": workstats.PAY_USES,
            "tables": [workstats.pay_table],
            "charts": [
                {"id": "pay-ranking", "kind": "hbar", "title": "Monthly pay by activity",
                 "subtitle": "Wage cost per worker, € a month, average of the past four quarters",
                 "unit": "€", "decimals": 0, "x_title": "Activity", "transform": "avg_1y",
                 "items": workstats.items("pay", "avg_1y"),
                 "ref_from": [("wage_cost", "All", "avg_1y")]},
                {"id": "pay-hour-ranking", "kind": "hbar", "title": "Pay per hour by activity",
                 "subtitle": "Wage cost per hour actually worked, €, average of the past four quarters",
                 "unit": "€", "decimals": 2, "x_title": "Activity", "transform": "avg_1y",
                 "items": workstats.items("pay_hour", "avg_1y"),
                 "ref_from": [("wage_cost_hour", "All", "avg_1y")]},
                workstats.extra_pay_chart,
            ],
        },
        {
            "id": "pay-growth",
            "title": "Pay growth by activity",
            "intro": ("How fast pay is rising in each activity, and how it has done against prices since 2019. Growth "
                      "compares averages of four quarters: the latest quarter alone can jump or fall when bonuses "
                      "come at a different time of the year, above all in the activities that pay large ones."),
            "facts": workstats.growth_facts,
            "callout": workstats.growth_callout,
            "uses": workstats.PAY_USES,
            "tables": [],
            "charts": [workstats.pay_growth_chart, workstats.real_pay_chart, workstats.bonus_timing_chart],
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
            "id": "underlying",
            "title": "Underlying inflation",
            "intro": ("A few big price moves, like energy, can push headline inflation around. These measures look at "
                      "the whole spread of price changes across about 180 detailed items of the harmonised basket: "
                      "the weighted median is the rate half the basket is rising faster than, and the trimmed means "
                      "average what is left after dropping the most extreme rises and falls. EconPulse calculation from "
                      "Eurostat data, following the method the ECB uses for the euro area."),
            "facts": underlying.facts,
            "callout": underlying.callout,
            "uses": underlying.MEASURE_IDS,
            "tables": [Table(
                title="Measure",
                caption="Annual inflation, % change on a year earlier",
                columns=LEVELS,
                rows=[
                    Row("hicp", "Headline HICP"),
                    Row("hicp_core", "Core HICP"),
                    Row("hicp_wmedian", "Weighted median"),
                    Row("hicp_trim10", "Trimmed mean, 10%"),
                    Row("hicp_trim30", "Trimmed mean, 30%"),
                    Heading("How widespread"),
                    Row("hicp_share_above2", "Basket rising faster than 2%"),
                    Row("hicp_share_above5", "Basket rising faster than 5%"),
                    Heading("Euro area"),
                    Row("hicp_euro_area", "Headline HICP"),
                    Row("hicp_wmedian_euro_area", "Weighted median"),
                    Row("hicp_trim30_euro_area", "Trimmed mean, 30%"),
                ],
                note=("Each item's annual rate is weighted by its share of household spending that year. The 10% "
                      "trimmed mean drops 5% of the basket at each end of the distribution, the 30% one drops 15%. "
                      "Run on euro-area data, the trimmed means match the ECB's own within about 0.05 points on "
                      "average (2018–2025) and the median within about 0.15; the ECB's series stopped in December "
                      "2025. Detailed items start in 2015 for Spain and 2017 for the euro area."),
            ), underlying.movers_table],
            "charts": [
                {"id": "underlying", "title": "Headline and underlying inflation", "subtitle": "HICP, % change on a year earlier",
                 "kind": "line", "unit": "%", "decimals": 1, "start": "2016-01-01", "ref_lines": TARGET,
                 "series": [("hicp", "level", "Headline", {"color": "ink"}), ("hicp_wmedian", "level", "Weighted median"),
                            ("hicp_trim30", "level", "Trimmed mean 30%"), ("hicp_core", "level", "Core")]},
                {"id": "underlying-ea", "title": "Weighted median: Spain and the euro area",
                 "subtitle": "HICP, % change on a year earlier", "kind": "line", "unit": "%", "decimals": 1,
                 "start": "2018-01-01", "ref_lines": TARGET,
                 "series": [("hicp_wmedian", "level", "Spain"), ("hicp_wmedian_euro_area", "level", "Euro area")]},
                {"id": "breadth", "title": "How widespread are price rises?",
                 "subtitle": "Share of the HICP basket, by weight, with annual inflation above 2% and above 5%",
                 "kind": "line", "unit": "%", "decimals": 0, "start": "2016-01-01",
                 "series": [("hicp_share_above2", "level", "Above 2%"), ("hicp_share_above5", "level", "Above 5%")]},
                underlying.distribution_chart,
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
                    Row("euro_stoxx50", "Euro Stoxx 50 (monthly average)"),
                    Heading("The euro, per euro"),
                    Row("eurusd", "US dollars"),
                    Row("eurgbp", "British pounds"),
                    Row("eurchf", "Swiss francs"),
                    Row("eurjpy", "Japanese yen"),
                    Heading("Energy and metals"),
                    Row("brent_usd", "Brent crude, dollars"),
                    Row("brent_eur", "Brent crude, euros"),
                    Row("gas_eu", "European natural gas (monthly)"),
                    Row("electricity_price", "Electricity, day-ahead"),
                    Row("gold", "Gold (monthly)"),
                    Row("copper", "Copper (monthly)"),
                ],
                note=("Each row is the latest close its source has published; a date next to a row means it differs "
                      "from the rest. Monthly rows are monthly averages. For the euro, a rise means a stronger euro."),
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
            "id": "stress",
            "title": "Financial stress and banks",
            "intro": ("The ECB's composite indicator of systemic stress (CISS) combines tension in money, bond, share "
                      "and currency markets and among banks into one number, from 0 (calm) to 1 (crisis). The bad-loan "
                      "ratio shows how much bank lending is not being repaid."),
            "tables": [Table(
                title="Indicator",
                caption="Index (0 to 1) or %",
                columns=LEVELS,
                rows=[
                    Row("ciss_es", "Financial stress, Spain"),
                    Row("ciss_ea", "Financial stress, euro area"),
                    Row("npl_ratio", "Bad-loan ratio, %"),
                ],
            )],
            "charts": [
                {"id": "ciss", "title": "Financial stress", "subtitle": "ECB composite indicator of systemic stress, 0 to 1, daily",
                 "kind": "line", "unit": "", "decimals": 2, "start": "2007-01-01", "date_format": DAILY,
                 "series": [("ciss_es", "level", "Spain"), ("ciss_ea", "level", "Euro area")]},
                {"id": "npl", "title": "Bad loans", "subtitle": "Doubtful loans, % of lending to households and firms",
                 "kind": "line", "unit": "%", "decimals": 2, "start": "2000-01-01",
                 "series": [("npl_ratio", "level", "Bad-loan ratio")]},
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
        {
            "id": "soundness-table",
            "title": "IMF-style financial soundness indicators",
            "intro": ("Table 3 of the IMF's 2026 Article IV report for Spain: bank capital, asset quality and "
                      "profitability from the IMF's own Financial Soundness Indicators database, banks' domestic "
                      "exposures from the Banco de España, and corporate, household and housing indicators."),
            "uses": sorted(sectortables.FINANCIAL_SOUNDNESS.indicator_ids()),
            "tables": [sectortables.table_function("financial-soundness")],
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
        {
            "id": "monetary-table",
            "title": "IMF-style monetary and credit indicators",
            "intro": ("The Banco de España's balance sheet in the Eurosystem, bank lending and deposits, and interest "
                      "rates, at the end of each year. The Article IV report for Spain has no monetary table, since "
                      "the ECB sets policy for the euro area; this one follows the IMF's layout for other countries."),
            "uses": sorted(sectortables.MONETARY.indicator_ids()),
            "tables": [sectortables.table_function("monetary")],
        },
    ],
    # ------------------------------------------------------------------ Activity
    "activity": [
        {
            "id": "output",
            "title": "Industry, shops and electricity",
            "intro": ("Monthly signs of how much the economy is producing and selling. Electricity demand arrives "
                      "daily, ahead of everything else, but moves with the weather."),
            "tables": [Table(
                title="Activity",
                caption="% change",
                columns=[Change("1-mo", 1), Change("3-mo ann.", 3, True), Change("12-mo", 12)],
                rows=[
                    Row("industrial_production", "Industrial production"),
                    Row("retail_sales", "Retail sales, real"),
                    Row("car_sales", "Car sales", season="raw"),
                    Row("electricity_demand_monthly", "Electricity demand", season="raw"),
                ],
                note=("Industrial production and retail sales are seasonally and calendar adjusted by INE. Car sales "
                      "and electricity demand are not, so only the 12-month change is shown."),
            )],
            "charts": [
                {"id": "industry-retail", "title": "Industry and retail", "subtitle": "% change on a year earlier",
                 "kind": "line", "unit": "%", "decimals": 1, "start": "2022-01-01",
                 "series": [("industrial_production", "yoy", "Industrial production"), ("retail_sales", "yoy", "Retail sales")]},
                {"id": "electricity-demand", "title": "Electricity demand",
                 "subtitle": "Average daily demand, % change on a year earlier",
                 "kind": "bar", "signed": True, "unit": "%", "decimals": 1, "start": "2023-01-01",
                 "series": [("electricity_demand_monthly", "yoy", "Demand")]},
                {"id": "car-sales", "title": "Car sales", "subtitle": "Past 12 months, thousands of cars",
                 "kind": "line", "unit": "k", "decimals": 0, "start": "2015-01-01",
                 "series": [("car_sales", "sum_1y", "Car sales", {"scale": 0.001})]},
            ],
        },
        {
            "id": "surveys",
            "title": "Business and consumer surveys",
            "intro": ("The European Commission asks firms and households every month how things are going. "
                      "Surveys come out before the hard data they foreshadow."),
            "tables": [Table(
                title="Survey",
                caption="Index or balance",
                columns=LEVELS,
                rows=[
                    Row("economic_sentiment", "Economic sentiment (average = 100)"),
                    Row("consumer_confidence", "Consumer confidence"),
                    Row("industry_confidence", "Industry confidence"),
                    Row("construction_confidence", "Construction confidence"),
                ],
                note=("Confidence indicators are balances: the share of positive answers minus negative ones, so zero "
                      "means as many optimists as pessimists. Spanish services and retail confidence stopped in 2024."),
            )],
            "charts": [
                {"id": "sentiment", "title": "Economic sentiment", "subtitle": "Index, long-run average = 100",
                 "kind": "line", "unit": "", "decimals": 1, "start": "2015-01-01",
                 "ref_lines": [{"y": 100, "label": "Average"}],
                 "series": [("economic_sentiment", "level", "Sentiment")]},
                {"id": "confidence", "title": "Confidence", "subtitle": "Balance of positive minus negative answers",
                 "kind": "line", "unit": "", "decimals": 1, "start": "2019-01-01",
                 "series": [("consumer_confidence", "level", "Consumers"), ("industry_confidence", "level", "Industry"),
                            ("construction_confidence", "level", "Construction")]},
            ],
        },
        {
            "id": "tourism",
            "title": "Tourism",
            "intro": ("Spain is one of the world's most visited countries. Arrivals and spending come from INE's "
                      "border surveys (FRONTUR, EGATUR), receipts from the balance of payments."),
            "tables": [Table(
                title="Tourism",
                caption="Latest month, not seasonally adjusted; changes in %",
                columns=FLOWS,
                rows=[
                    Row("tourist_arrivals", "International tourists"),
                    Row("tourist_spending", "Their spending"),
                    Row("tourism_receipts", "Tourism receipts (balance of payments)"),
                ],
                note="Year to date sums the months since January and compares them with the same months a year earlier.",
            )],
            "charts": [
                {"id": "arrivals", "title": "International tourists", "subtitle": "Past 12 months, millions",
                 "kind": "line", "unit": "mn", "decimals": 1, "start": "2015-01-01",
                 "series": [("tourist_arrivals", "sum_1y", "Tourists")]},
                {"id": "tourist-spending", "title": "Tourist spending", "subtitle": "Past 12 months, € billion",
                 "kind": "line", "unit": "€ bn", "decimals": 1, "start": "2015-01-01",
                 "series": [("tourist_spending", "sum_1y", "Spending", {"scale": 0.001})]},
            ],
        },
        {
            "id": "external",
            "title": "External accounts",
            "intro": ("What Spain earns from the rest of the world against what it pays: trade, tourism, income "
                      "and transfers. A surplus means Spain lends to the rest of the world."),
            "tables": [Table(
                title="Balance",
                caption="% of GDP or € million",
                columns=LEVELS,
                rows=[
                    Row("current_account", "Current account, % of GDP (quarter)"),
                    Row("current_account", "Current account, % of GDP (past 4 quarters)", transform="avg_1y"),
                    Row("current_account_monthly", "Current account, past 12 months", transform="sum_1y"),
                    Row("tourism_receipts", "Tourism receipts, past 12 months", transform="sum_1y"),
                ],
            )],
            "charts": [
                {"id": "current-account", "title": "Current account balance",
                 "subtitle": "% of GDP, average of the past four quarters",
                 "kind": "line", "signed": True, "unit": "%", "decimals": 1, "start": "2000-01-01",
                 "series": [("current_account", "avg_1y", "Current account")]},
            ],
        },
        {
            "id": "external-tables",
            "title": "IMF-style external accounts",
            "intro": ("Tables 4 and 5 of the IMF's 2026 Article IV report for Spain: the balance of payments, in euros "
                      "and in % of GDP, and external debt by sector and instrument, from Eurostat. The World Economic "
                      "Outlook projects only the current account, so the other lines show … in the projection years."),
            "uses": sorted(sectortables.BALANCE_OF_PAYMENTS.indicator_ids() | sectortables.EXTERNAL_DEBT.indicator_ids()),
            "tables": [sectortables.table_function("balance-of-payments"), sectortables.table_function("external-debt")],
        },
    ],
    # ------------------------------------------------------------------ Housing
    "housing": [
        {
            "id": "prices",
            "title": "House prices",
            "intro": "INE's house price index, built from notarised sales, for new and second-hand homes.",
            "tables": [Table(
                title="Prices",
                caption="% change",
                columns=[Change("q/q", 3), Change("y/y", 12)],
                rows=[
                    Row("house_prices", "All homes", season="published"),
                    Row("house_prices_new", "New homes", season="published", indent=1),
                    Row("house_prices_used", "Second-hand homes", season="published", indent=1),
                    Row("real_house_prices", "After inflation", season="published"),
                    Row("cpi_rent_index", "Rents (CPI)", season="ours"),
                ],
                note=("House prices are not seasonally adjusted; the quarterly change is as INE reports it. The rents "
                      "quarterly change uses EconPulse seasonal adjustment."),
            )],
            "charts": [
                {"id": "house-prices", "title": "House prices", "subtitle": "% change on a year earlier",
                 "kind": "line", "unit": "%", "decimals": 1, "start": "2015-01-01",
                 "series": [("house_prices_new", "yoy", "New homes"), ("house_prices_used", "yoy", "Second-hand")]},
                {"id": "real-house-prices", "title": "Real house prices since the boom",
                 "subtitle": "House prices deflated by the CPI, Q1 2007 = 100",
                 "kind": "line", "unit": "", "decimals": 1, "start": "2007-01-01",
                 "ref_lines": [{"y": 100, "label": "Q1 2007"}],
                 "series": [("real_house_prices", "level", "Real house prices", {"rebase": "2007-01-01"})]},
            ],
        },
        {
            "id": "sales",
            "title": "Sales, mortgages and permits",
            "intro": ("How many homes change hands, how many are bought with a mortgage, and how many new ones "
                      "are in the pipeline."),
            "tables": [Table(
                title="Housing market",
                caption="Latest month, not seasonally adjusted; changes in %",
                columns=FLOWS,
                rows=[
                    Row("home_sales", "Home sales"),
                    Row("mortgages_homes", "Mortgages on homes"),
                    Row("mortgage_lending_homes", "Amount lent on them"),
                    Row("average_mortgage", "Average mortgage", flow=False),
                    Row("new_mortgage_lending", "New mortgage lending by banks"),
                    Row("home_permits", "New homes in building permits"),
                ],
                note=("Sales and mortgages come from the property registers (INE), new lending from banks' reports "
                      "to the ECB, which include renegotiated loans."),
            )],
            "charts": [
                {"id": "home-sales", "title": "Home sales", "subtitle": "Past 12 months, thousands",
                 "kind": "line", "unit": "k", "decimals": 0, "start": "2008-01-01",
                 "series": [("home_sales", "sum_1y", "Home sales", {"scale": 0.001})]},
                {"id": "mortgages", "title": "Mortgages on homes", "subtitle": "Past 12 months, thousands",
                 "kind": "line", "unit": "k", "decimals": 0, "start": "2008-01-01",
                 "series": [("mortgages_homes", "sum_1y", "Mortgages", {"scale": 0.001})]},
                {"id": "permits", "title": "Building permits", "subtitle": "New homes in permits, past 12 months, thousands",
                 "kind": "line", "unit": "k", "decimals": 0, "start": "2008-01-01",
                 "series": [("home_permits", "sum_1y", "Permits", {"scale": 0.001})]},
            ],
        },
        {
            "id": "debt",
            "title": "Household finances",
            "intro": ("Spanish households have paid down much of the debt they took on in the boom; most mortgages "
                      "are variable-rate, so rates matter quickly."),
            "tables": [Table(
                title="Indicator",
                caption="%",
                columns=LEVELS,
                rows=[
                    Row("household_debt_gdp", "Household debt, % of GDP"),
                    Row("household_debt_income", "Household debt, % of disposable income"),
                    Row("debt_service_ratio", "Debt service, % of disposable income"),
                    Row("saving_rate", "Saving rate, % of disposable income (SA)"),
                    Row("housing_loans_growth", "Housing loans, growth on a year earlier"),
                    Row("mortgage_rate", "New mortgages, average rate"),
                ],
                note=("Debt service is what households pay in interest and principal (BIS). The saving rate is "
                      "the share of disposable income not spent (INE)."),
            )],
            "charts": [
                {"id": "household-debt", "title": "Household debt", "subtitle": "% of GDP",
                 "kind": "line", "unit": "%", "decimals": 1, "start": "2003-01-01",
                 "series": [("household_debt_gdp", "level", "Household debt")]},
                {"id": "saving", "title": "Household saving rate", "subtitle": "% of disposable income, seasonally adjusted",
                 "kind": "line", "unit": "%", "decimals": 1, "start": "2000-01-01",
                 "series": [("saving_rate", "level", "Saving rate")]},
                {"id": "housing-loans", "title": "Housing loans and mortgage rates",
                 "subtitle": "%: growth of housing loans on a year earlier, and the rate on new mortgages",
                 "kind": "line", "unit": "%", "decimals": 1, "start": "2010-01-01",
                 "series": [("housing_loans_growth", "level", "Loan growth"), ("mortgage_rate", "level", "Mortgage rate")]},
            ],
        },
    ],
    # ------------------------------------------------------------------ Fiscal
    "fiscal": [
        {
            "id": "balance",
            "title": "Deficit and debt",
            "intro": ("The general government (state, regions, local councils and social security) as reported to "
                      "the European Commission. EU rules set reference values of a 3% deficit and 60% debt."),
            "tables": [
                Table(
                    title="Public finances",
                    caption="% of GDP, calendar year",
                    columns=[Level("latest"), Level("prev", header="Year before")],
                    rows=[
                        Row("deficit_annual", "Budget balance"),
                        Row("primary_balance", "Before interest (primary balance)", indent=1),
                        Row("interest_annual", "Interest paid", indent=1),
                        Row("revenue_annual", "Revenue"),
                        Row("spending_annual", "Spending"),
                        Row("debt_annual", "Debt at year end"),
                    ],
                    note="A negative balance is a deficit.",
                ),
                Table(
                    title="Latest quarters",
                    caption="% of GDP",
                    columns=LEVELS,
                    rows=[
                        Row("government_balance", "Budget balance, past four quarters", transform="avg_1y"),
                        Row("government_debt", "Debt"),
                    ],
                    note="The quarterly balance is not seasonally adjusted, so it is averaged over four quarters.",
                ),
            ],
            "charts": [
                {"id": "deficit", "title": "Budget balance", "subtitle": "% of GDP, calendar years",
                 "kind": "bar", "signed": True, "unit": "%", "decimals": 1, "start": "1995-01-01",
                 "ref_lines": [{"y": -3, "label": "EU limit"}],
                 "series": [("deficit_annual", "level", "Balance")]},
                {"id": "debt", "title": "Government debt", "subtitle": "% of GDP, quarterly",
                 "kind": "line", "unit": "%", "decimals": 1, "start": "2000-01-01",
                 "ref_lines": [{"y": 60, "label": "EU reference"}],
                 "series": [("government_debt", "level", "Debt")]},
                {"id": "revenue-spending", "title": "Revenue and spending", "subtitle": "% of GDP, calendar years",
                 "kind": "line", "unit": "%", "decimals": 1, "start": "1995-01-01",
                 "series": [("spending_annual", "level", "Spending"), ("revenue_annual", "level", "Revenue")]},
                {"id": "interest", "title": "Interest on the debt", "subtitle": "% of GDP, calendar years",
                 "kind": "line", "unit": "%", "decimals": 1, "start": "1995-01-01",
                 "series": [("interest_annual", "level", "Interest")]},
            ],
        },
        {
            "id": "government-operations",
            "title": "IMF-style government operations",
            "intro": ("Tables 2a and 2b of the IMF's 2026 Article IV report for Spain: revenue, spending and the "
                      "balances in euros and in % of GDP, from Eurostat's accounts for the general government. The "
                      "World Economic Outlook projects only the totals, so the other lines show … in the projection "
                      "years."),
            "uses": sorted(sectortables.FISCAL_EUR.indicator_ids() | sectortables.FISCAL_GDP.indicator_ids()),
            "tables": [sectortables.table_function("fiscal-eur"), sectortables.table_function("fiscal-gdp")],
        },
        {
            "id": "debt-sustainability",
            "title": "Debt sustainability",
            "intro": ("What drives the debt ratio, in the IMF's layout (DSA 1: Eurostat for past years, the World "
                      "Economic Outlook for projections), and how it fares under stress, from the European "
                      "Commission's Debt Sustainability Monitor (DSA 2), since the IMF does not publish its own "
                      "stress tests as data. The Fiscal Explorer runs the Commission's baseline to 2070."),
            "facts": sectortables.dsa_facts,
            "uses": sorted(sectortables.DSA_BASELINE.indicator_ids()),
            "tables": [sectortables.table_function("dsa-baseline"), sectortables.table_function("dsa-stress")],
            "charts": [sectortables.dsa_fan_chart, sectortables.dsa_stress_chart],
        },
    ],
    # ------------------------------------------------------------------ International
    "international": [
        {
            "id": "peers",
            "title": "Spain and its comparators",
            "intro": ("Spain next to the euro area and eight comparators: France, Germany, Italy, Portugal and Poland in "
                      "the EU, and the United Kingdom, the United States and Canada. The sections below take growth, "
                      "jobs, and prices and interest rates in turn."),
            "facts": peers.facts,
            "uses": sorted(peers.IDS["level"].values()),
            "tables": [Panel(
                title="Country",
                caption="%",
                columns=[PanelColumn("gdp", "GDP growth, y/y"), PanelColumn("hicp", "Inflation"),
                         PanelColumn("core", "Core inflation"), PanelColumn("unemp", "Unemployment"),
                         PanelColumn("y10", "10-year yield"), PanelColumn("policy", "Policy rate")],
                rows=peers.panel_rows("gdp", "hicp", "core", "unemp", "y10", "policy"),
                note=("Inflation is the harmonised index (HICP) in the EU and each country's CPI elsewhere; core "
                      "inflation leaves out food and energy, where a current measure is available. 10-year yields are "
                      "monthly averages. The euro-area countries share the ECB's deposit rate; the US rate is the "
                      "mid-point of the Fed's target range. Sources: INE, Eurostat, ECB, OECD, BIS, US BLS and BEA."),
            )],
            "charts": [],
        },
        {
            "id": "growth",
            "title": "Growth",
            "intro": ("How fast each economy is growing, how far it has come since the end of 2019, the last quarter "
                      "before the pandemic, and how rich it is per head at purchasing power."),
            "uses": sorted(set(peers.IDS["level"].values()) | set(peers.IDS["ppp"].values())),
            "tables": [peers.growth_table],
            "charts": [
                peers.recovery_chart,
                peers.recovery_ranking,
                {"id": "gdp-growth-ranking", "kind": "hbar", "title": "GDP growth",
                 "subtitle": "Real GDP, % change on a year earlier", "unit": "%", "decimals": 1, "x_title": "Country",
                 "highlight": "Spain", "items": peers.ranking_items("gdp"), "ref_from": peers.euro_area_ref("gdp")},
                peers.ppp_ranking,
            ],
        },
        {
            "id": "jobs",
            "title": "Jobs",
            "intro": ("Unemployment, for everyone and for people under 25, and the share of people aged 15 to 64 in "
                      "work. Spain's unemployment and youth unemployment are the highest of the group."),
            "tables": [Panel(
                title="Country",
                caption="% · changes on a year earlier in percentage points",
                columns=[PanelColumn("unemp", "Unemployment"), PanelColumn("unemp", "1-yr change", col=Move("1-yr", "year")),
                         PanelColumn("youth", "Youth unemployment"),
                         PanelColumn("emp", "Employment rate, 15-64"), PanelColumn("emp", "1-yr change", col=Move("1-yr", "year"))],
                rows=peers.panel_rows("unemp", "youth", "emp"),
                note=("Unemployment and youth unemployment are seasonally adjusted monthly rates; youth unemployment "
                      "and the employment rate follow the OECD's harmonised definitions (people aged 15 to 24, and 15 "
                      "to 64), and Eurostat's for the euro area (under 25). Sources: Eurostat, OECD, US BLS."),
            )],
            "charts": [
                {"id": "unemployment-ranking", "kind": "hbar", "title": "Unemployment", "subtitle": "% of the labour force",
                 "unit": "%", "decimals": 1, "x_title": "Country", "highlight": "Spain",
                 "items": peers.ranking_items("unemp"), "ref_from": peers.euro_area_ref("unemp")},
                {"id": "youth-ranking", "kind": "hbar", "title": "Youth unemployment",
                 "subtitle": "People aged 15-24, % of the labour force that age", "unit": "%", "decimals": 1,
                 "x_title": "Country", "highlight": "Spain", "items": peers.ranking_items("youth"),
                 "ref_from": peers.euro_area_ref("youth")},
                {"id": "employment-ranking", "kind": "hbar", "title": "Employment rate",
                 "subtitle": "People aged 15-64 in work, % of the population that age", "unit": "%", "decimals": 1,
                 "x_title": "Country", "highlight": "Spain", "items": peers.ranking_items("emp"),
                 "ref_from": peers.euro_area_ref("emp")},
                {"id": "unemployment-peers", "title": "Unemployment", "subtitle": "% of the labour force, seasonally adjusted",
                 "kind": "line", "unit": "%", "decimals": 1, "start": "2008-01-01",
                 "series": [("unemployment_monthly", "level", "Spain"), ("unemployment_ea", "level", "Euro area"),
                            ("unemployment_pt", "level", "Portugal")]},
            ],
        },
        {
            "id": "prices-rates",
            "title": "Prices and interest rates",
            "intro": ("Inflation, policy rates and what governments pay to borrow for ten years. Spain, France, "
                      "Germany, Italy and Portugal share the ECB's rates; Poland, the UK, the US and Canada set their own."),
            "tables": [Panel(
                title="Country",
                caption="% · spread in basis points",
                columns=[PanelColumn("hicp", "Inflation"), PanelColumn("core", "Core inflation"),
                         PanelColumn("policy", "Policy rate"), PanelColumn("y10", "10-year yield"),
                         PanelColumn("spread", "Spread over Germany")],
                rows=peers.panel_rows("hicp", "core", "policy", "y10", "spread"),
                note=("Inflation on a year earlier (HICP in the EU, CPI elsewhere). 10-year yields and spreads over "
                      "Germany's are monthly averages; spreads are shown for the euro-area countries. Sources: INE, "
                      "Eurostat, ECB, OECD, BIS, US BLS."),
            )],
            "charts": [
                {"id": "inflation-ranking", "kind": "hbar", "title": "Inflation", "subtitle": "% change on a year earlier",
                 "unit": "%", "decimals": 1, "x_title": "Country", "highlight": "Spain",
                 "items": peers.ranking_items("hicp"), "ref_from": peers.euro_area_ref("hicp")},
                {"id": "inflation-peers", "title": "Inflation", "subtitle": "% change on a year earlier (US: CPI)",
                 "kind": "line", "unit": "%", "decimals": 1, "start": "2019-01-01", "ref_lines": TARGET,
                 "series": [("hicp", "level", "Spain"), ("hicp_euro_area", "level", "Euro area"),
                            ("us_cpi_index", "yoy", "United States")]},
                {"id": "policy-rates-peers", "title": "Policy rates", "subtitle": "%, daily",
                 "kind": "line", "unit": "%", "decimals": 2, "start": "2019-01-01",
                 "series": [("ecb_deposit_rate", "level", "ECB deposit rate"), ("us_fed_funds", "level", "US Fed funds"),
                            ("policy_rate_uk", "level", "Bank of England")]},
                {"id": "yields-ranking", "kind": "hbar", "title": "10-year government bond yields",
                 "subtitle": "%, monthly average", "unit": "%", "decimals": 2, "x_title": "Country", "highlight": "Spain",
                 "items": peers.ranking_items("y10")},
                {"id": "spreads", "title": "Borrowing costs over Germany",
                 "subtitle": "10-year yield minus Germany's, basis points, monthly averages",
                 "kind": "line", "unit": "bp", "decimals": 0, "start": "2008-01-01",
                 "series": [("risk_premium_monthly", "level", "Spain"), ("spread10_it", "level", "Italy"),
                            ("spread10_pt", "level", "Portugal")]},
            ],
        },
    ],
    # ------------------------------------------------------------------ Regions
    "regions": [
        {
            "id": "snapshot",
            "title": "The autonomous communities",
            "intro": ("Spain's 17 autonomous communities differ widely in unemployment, house prices and income per "
                      "head. Regional figures come from INE's labour force survey, house price index, CPI and "
                      "regional accounts."),
            "tables": [Panel(
                title="Region",
                caption="%, unless stated",
                columns=[PanelColumn("unemp", "Unemployment rate"),
                         PanelColumn("unemp_chg", "Change on a year", col=Move("1-yr", "year")),
                         PanelColumn("prices", "House prices, y/y", transform="yoy"),
                         PanelColumn("cpi", "Inflation"),
                         PanelColumn("gdppc", "GDP per head, Spain = 100")],
                rows=[PanelRow("Spain", {"unemp": "unemployment_epa", "unemp_chg": "unemployment_epa",
                                         "prices": "house_prices", "cpi": ("cpi_index", "yoy"),
                                         "gdppc": "gdp_per_head_spain"}, True)]
                     + [PanelRow(name, {"unemp": f"unemployment_{slug}", "unemp_chg": f"unemployment_{slug}",
                                        "prices": f"house_prices_{slug}", "cpi": f"cpi_{slug}",
                                        "gdppc": f"gdp_per_head_{slug}"}) for slug, name in REGIONS],
                note=("Unemployment comes from the labour force survey (EPA), not seasonally adjusted. Ceuta and "
                      "Melilla are left out: their survey samples are small."),
            )],
            "charts": [
                {"id": "unemployment-regions", "kind": "hbar", "title": "Unemployment by region",
                 "subtitle": "% of the labour force (EPA)", "unit": "%", "decimals": 1,
                 "items": [(f"unemployment_{slug}", name) for slug, name in REGIONS],
                 "ref_from": [("unemployment_epa", "Spain")]},
                {"id": "gdppc-regions", "kind": "hbar", "title": "GDP per head by region",
                 "subtitle": "Spain = 100, current prices", "unit": "", "decimals": 0,
                 "items": [(f"gdp_per_head_{slug}", name) for slug, name in REGIONS],
                 "ref_from": [("gdp_per_head_spain", "Spain")]},
                {"id": "house-prices-regions", "kind": "hbar", "title": "House prices by region",
                 "subtitle": "% change on a year earlier", "unit": "%", "decimals": 1, "transform": "yoy",
                 "items": [(f"house_prices_{slug}", name) for slug, name in REGIONS],
                 "ref_from": [("house_prices", "Spain")]},
                {"id": "inflation-regions", "kind": "hbar", "title": "Inflation by region",
                 "subtitle": "CPI, % change on a year earlier", "unit": "%", "decimals": 1,
                 "items": [(f"cpi_{slug}", name) for slug, name in REGIONS],
                 "ref_from": [("cpi_index", "Spain", "yoy")]},
            ],
        },
    ],
    # ------------------------------------------------------------------ Analysis (EconPulse originals)
    "analysis": [
        {
            "id": "composites",
            "title": "The economy against its history",
            "intro": ("Two summary readings. Each indicator is compared with its own record since 2013 (a z-score: "
                      "0 is normal, +1 is one typical deviation above), then the scores are averaged, giving the "
                      "newest data the most weight. EconPulse calculation, not an official statistic."),
            "facts": analytics.composite_facts,
            "uses": [c.id for c in analytics.ACTIVITY + analytics.INFLATION],
            "tables": [lambda data: analytics.composite_table(data, "activity"),
                       lambda data: analytics.composite_table(data, "inflation")],
            "charts": [analytics.composite_chart],
        },
        {
            "id": "surprises",
            "title": "Data surprises",
            "intro": ("Did the latest figures beat or miss expectations? Analysts' forecasts for Spanish data are not "
                      "freely available, so each figure is compared with a simple statistical forecast: what the "
                      "indicator's own past predicted. Above zero, the data came in stronger (or inflation hotter) "
                      "than that forecast. EconPulse calculation, not a survey of forecasters."),
            "facts": surprises.surprise_facts,
            "uses": [c.id for c in analytics.ACTIVITY + analytics.INFLATION],
            "tables": [lambda data: surprises.surprise_table(data, "activity"),
                       lambda data: surprises.surprise_table(data, "inflation")],
            "charts": [surprises.surprise_chart],
        },
        {
            "id": "nowcast",
            "title": "GDP nowcast",
            "intro": ("An estimate of this quarter's GDP growth before INE publishes it, from Social Security "
                      "registrations, industrial production and last quarter's growth (a bridge equation fitted "
                      "on 2013 onwards, leaving out 2020-21)."),
            "facts": analytics.nowcast_facts,
            "uses": ["gdp"] + [i.id for i in analytics.NOWCAST_INPUTS],
            "tables": [analytics.nowcast_inputs_table, analytics.nowcast_record_table],
            "charts": [analytics.nowcast_chart],
        },
        {
            "id": "forecasts",
            "title": "What forecasters expect",
            "intro": ("The latest forecasts for Spain this year and next, with EconPulse's own figure for this year's "
                      "GDP. Each forecaster's row shows when it was published: forecasts made months apart saw "
                      "different data, so differences are partly about timing."),
            "facts": forecasts.forecast_facts,
            "callout": forecasts.forecast_callout,
            "uses": forecasts.INDICATORS + ["gdp"] + [i.id for i in analytics.NOWCAST_INPUTS],
            "tables": [lambda data: forecasts.forecast_table(data, forecasts.years()[0]),
                       lambda data: forecasts.forecast_table(data, forecasts.years()[1])],
            "charts": [forecasts.forecast_chart],
        },
        {
            "id": "yields",
            "title": "What moves the 10-year yield",
            "intro": ("Spain's 10-year yield is the German yield plus the prima de riesgo. Splitting a move into the "
                      "two shows whether it is about euro-area rates or about Spain."),
            "uses": ["es_10y", "de_10y"],
            "tables": [analytics.yield_decomposition_table],
            "charts": [
                {"id": "yield-parts", "title": "Spain's 10-year yield, in two parts",
                 "subtitle": "%, monthly averages: the German yield plus the prima de riesgo",
                 "kind": "bar", "stack": True, "unit": "%", "decimals": 2, "start": "2010-01-01",
                 "series": [("de_10y_monthly", "level", "German yield"),
                            ("risk_premium_monthly", "level", "Prima de riesgo", {"scale": 0.01}),
                            ("es_10y_monthly", "level", "Spain", {"kind": "line", "color": "ink"})]},
            ],
        },
        {
            "id": "taylor",
            "title": "Taylor rules: the euro area and Spain",
            "intro": ("A Taylor rule turns inflation and slack into a suggested policy rate. Run on euro-area data it "
                      "is a yardstick for the ECB; run on Spanish data it shows the rate Spain would get if it set its "
                      "own, the cost of one rate for all."),
            "facts": analytics.taylor_facts,
            "uses": ["hicp_euro_area", "unemployment_ea", "hicp", "unemployment_monthly", "ecb_deposit_rate"],
            "tables": [analytics.taylor_table],
            "charts": [analytics.taylor_chart],
        },
    ],
}


def block_indicator_ids(block: dict) -> set[str]:
    """Every indicator a block reads (tables, charts, flash notes, extras)."""
    ids = set()
    for t in block["tables"]:
        if isinstance(t, (Table, Panel)):
            ids |= t.indicator_ids()
    for c in block.get("charts", []):
        if callable(c):
            continue  # a computed chart: its inputs are listed in the block's "uses"
        ids |= {i for i, *_ in c.get("ref_from", [])}
        if c.get("curve"):
            ids |= {i for line in c["lines"] for i, _ in line["points"]}
        elif c.get("kind") == "hbar":
            ids |= {item[0] for item in c["items"]}
        elif c.get("kind") == "xy":
            ids |= {c["x"][0], c["y"][0]}
        else:
            ids |= {s[0] for s in c["series"]}
    return ids | {i for i, _ in block.get("flash", [])} | set(block.get("uses", []))


def page_indicator_ids(section: str) -> set[str]:
    """Every indicator a section page reads."""
    ids = set()
    for block in PAGES.get(section, []):
        ids |= block_indicator_ids(block)
    return ids


def indicator_anchors(built: dict[str, dict], home: dict[str, str] | None = None) -> dict[str, str]:
    """Indicator id -> the first block that shows it ("labour.html#hours"), among the blocks that were
    built (`built`: section -> built page): on the indicator's own section page (`home`: id -> section)
    if it shows it, otherwise on the first page that does."""
    home = home or {}
    by_section: dict[str, dict[str, str]] = {}
    for section, blocks in PAGES.items():
        shown = {b["id"] for b in built.get(section, {}).get("blocks", [])}
        found = by_section.setdefault(section, {})
        for block in blocks:
            if block["id"] in shown:
                for ind_id in sorted(block_indicator_ids(block)):
                    found.setdefault(ind_id, f"{section}.html#{block['id']}")
    anchors = {}
    for section, found in by_section.items():
        for ind_id, href in found.items():
            own = by_section.get(home.get(ind_id, ""), {})
            anchors.setdefault(ind_id, own.get(ind_id, href))
    return anchors


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


def _build_any_table(t, data: Data) -> dict | None:
    if isinstance(t, Table):
        return build_table(t, data)
    if isinstance(t, Panel):
        return build_panel(t, data)
    return t(data)  # a function, e.g. the ECB's recent decisions


def _chart_builder(definition: dict):
    if definition.get("curve"):
        return build_curve
    if definition.get("kind") == "hbar":
        return build_ranking
    if definition.get("kind") == "xy":
        return build_xy
    return build_chart


def build_page(section: str, indicators: list[Indicator], store: Store) -> dict:
    """Blocks for one section page, plus the chart specs its script draws."""
    data = Data(indicators, store)
    blocks, charts = [], []
    for block in PAGES.get(section, []):
        tables = [t for t in (_build_any_table(t, data) for t in block["tables"]) if t]
        specs = [c for c in ((c(data) if callable(c) else _chart_builder(c)(c, data.by_id, store))
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
