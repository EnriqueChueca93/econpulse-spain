"""Every industry: monthly Social Security registrations by industry (site/industry-detail.html).

After Econvitals' industry employment detail: for each industry, the monthly change in registrations (bars)
and its 3-month average (line), seasonally adjusted by Macroscope, with a table of the level and the changes
over 1, 3 and 12 months. Registrations are monthly averages of the general scheme and the self-employed by
two-digit activity (CNAE) from the Social Security's yearly workbooks (sources/afiliacion.py), from 2021.
The groups keep their boundaries across the 2026 change to CNAE-2025; the two moves that cross them (motor
vehicle repair into division 95, real estate development into 68) are linked by the client.
"""

from .sources.afiliacion import moved
from .tables import AvgChange, Change, Data, Heading, Level, Row, Table, build_table

CHART_START = "2023-01-01"

# (section id, title, [(group id, label, divisions, indent, bridge)])
SECTIONS = [
    ("aggregates", "All registrations", [
        ("total", "All registrations (general scheme and self-employed)", "all", 0, None),
        ("goods", "Goods-producing", "01-43", 1, "-68"),
        ("services", "Service-providing", "45-99", 1, "+68"),
    ]),
    ("goods", "Goods-producing", [
        ("agriculture", "Agriculture, forestry and fishing", "01-03", 0, None),
        ("mining", "Mining and quarrying", "05-09", 0, None),
        ("manufacturing", "Manufacturing", "10-33", 0, None),
        ("food", "Food, beverages and tobacco", "10-12", 1, None),
        ("textiles", "Textiles, clothing and leather", "13-15", 1, None),
        ("wood_paper", "Wood, paper and printing", "16-18", 1, None),
        ("chemicals", "Petroleum, chemicals and pharmaceuticals", "19-21", 1, None),
        ("plastics", "Rubber, plastics and other mineral products", "22-23", 1, None),
        ("metals", "Metals and metal products", "24-25", 1, None),
        ("machinery", "Electronics, electrical equipment and machinery", "26-28", 1, None),
        ("vehicles", "Motor vehicles and other transport equipment", "29-30", 1, None),
        ("other_manufacturing", "Furniture, other manufacturing and repair", "31-33", 1, None),
        ("utilities", "Energy, water and waste", "35-39", 0, None),
        ("construction", "Construction", "41-43", 0, "-68"),
    ]),
    ("trade", "Trade, transport and hospitality", [
        ("trade", "Wholesale and retail trade", "45-47", 0, "-95"),
        ("transport", "Transport and storage", "49-53", 0, None),
        ("hospitality", "Accommodation and food services", "55-56", 0, None),
        ("accommodation", "Accommodation", "55", 1, None),
        ("food_services", "Restaurants and bars", "56", 1, None),
    ]),
    ("business", "Information, finance and business services", [
        ("information", "Information and communication", "58-63", 0, None),
        ("computing", "Computer programming and information services", "62-63", 1, None),
        ("finance", "Finance and insurance", "64-66", 0, None),
        ("real_estate", "Real estate", "68", 0, "+68"),
        ("professional", "Professional, scientific and technical", "69-75", 0, None),
        ("administrative", "Administrative and support services", "77-82", 0, None),
    ]),
    ("public", "Education, health and public administration", [
        ("public_admin", "Public administration and defence", "84", 0, None),
        ("education", "Education", "85", 0, None),
        ("health_social", "Health and social work", "86-88", 0, None),
        ("health", "Health", "86", 1, None),
        ("social", "Residential care and social work", "87-88", 1, None),
    ]),
    ("other", "Leisure and other services", [
        ("arts", "Arts, entertainment and recreation", "90-93", 0, None),
        ("other_services", "Other services, incl. repairs", "94-96", 0, "+95"),
        ("households", "Households as employers", "97-98", 0, None),
    ]),
]
# The divisions each move went into, as published (to say how many registrations the links moved).
MOVES = [("ind_div95", "95", "motor vehicle repair, from trade to other services"),
         ("ind_div68", "68", "real estate development, from construction to real estate")]


def indicator_id(group_id: str) -> str:
    return f"ind_{group_id}"


def groups() -> list[tuple]:
    return [g for _, _, items in SECTIONS for g in items]


def summary_table(data: Data) -> dict | None:
    rows = []
    for _, title, items in SECTIONS:
        rows.append(Heading(title))
        rows += [Row(indicator_id(gid), label, indent=indent + 1, season="ours") for gid, label, _, indent, _ in items]
    return build_table(Table(
        title="Registrations by industry",
        caption="Thousands; average change per month, seasonally adjusted by Macroscope for 1 and 3 months",
        columns=[Level("latest"), AvgChange("1-mo", 1), AvgChange("3-mo", 3), AvgChange("12-mo", 12), Change("12-mo %", 12)],
        rows=rows,
        note=("The 12-month columns use the registrations as published; the 1- and 3-month columns are seasonally "
              "adjusted by Macroscope."),
    ), data)


def chart(group_id: str, label: str, data: Data) -> dict | None:
    sa = data.adjusted(indicator_id(group_id))
    if sa is None:
        return None
    change = sa.diff()
    average = change.rolling(3).mean()
    keep = lambda s: s[s.index >= CHART_START].dropna().round(3)
    change, average = keep(change), keep(average)
    if change.empty:
        return None
    iso = lambda s: [d.strftime("%Y-%m-%d") for d in s.index]
    ind = data.by_id[indicator_id(group_id)]
    return {"id": f"ind-{group_id.replace('_', '-')}", "title": label,
            "subtitle": "Change on the month before, thousands, seasonally adjusted; line: 3-month average",
            "kind": "bar", "signed": True, "unit": "k", "decimals": 1, "freq": "M", "ref_lines": [],
            "series": [{"name": "Monthly change", "x": iso(change), "y": change.tolist()},
                       {"name": "3-month average", "kind": "line", "color": "ink", "x": iso(average), "y": average.tolist()}],
            "source": f"{ind.source_name} (afiliación media por actividad); Macroscope seasonal adjustment"}


def moves(data: Data) -> list[str]:
    """How many registrations each link moved, from the destination divisions as published."""
    out = []
    for ind_id, _, what in MOVES:
        s = data.raw(ind_id)
        try:
            out.append(f"about {round(moved(s.dropna()), -1):,.0f} thousand registrations of {what}")
        except (AttributeError, KeyError, TypeError):
            continue
    return out


def page(data: Data) -> dict:
    sections, charts = [], []
    for section_id, title, items in SECTIONS:
        specs = [c for c in (chart(gid, label, data) for gid, label, *_ in items) if c]
        if specs:
            sections.append({"id": section_id, "title": title, "charts": specs})
            charts += specs
    return {"table": summary_table(data), "sections": sections, "charts": charts, "moves": moves(data)}
