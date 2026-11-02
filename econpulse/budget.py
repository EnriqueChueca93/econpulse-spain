"""The Budget explorer (site/budget-explorer.html): public spending and revenue by theme (Batch 30a).

Everything comes from the IGAE's national accounts of the public administrations (SEC 2010), published as
Excel workbooks for each subsector (Administración central, Fondos de la seguridad social, the whole
Administraciones públicas...), all on the same basis, so years and administrations compare cleanly:

    COFOG_A_<code>.xlsx   spending by function (COFOG): one sheet a year since 1995, the 10 divisions and their
                          groups in columns, total spending in the "GASTO TOTAL" row
    A_<code>.xlsx         non-financial operations since 1995: resources (revenue) and uses (spending) by
                          economic type, in € mn (sheet Tabla1a)
    A_<code>_Imp.xlsx     taxes and social contributions, tax by tax, since 1995 (sheet Tabla1a)

and, for the autonomous communities one by one (Batch 30b):

    COFOG_A_Detalle_CCAA_<year>.xlsx   spending by COFOG division, a sheet for each community, from 2012
    A_CCAA_Det_<year>.xlsx             resources and uses by economic type, a column for each community, in € mn
                                       (Tabla1a) and as % of its GDP (Tabla1b), from 2000
    Detalle_por_CCAA_Imp.xlsx          taxes tax by tax, a sheet a year from 2012, a column for each community

Each community's GDP comes out of the two sheets of A_CCAA_Det (€ over % of GDP), and its population from
Eurostat (1 January, by NUTS 2 region). Only the latest years' workbooks are downloaded again on each fetch;
older years are kept, already read, in data/budget_regional.json.

`refresh` (run with `python -m econpulse fetch`) downloads them and saves what the explorer shows to
data/budget.json; on failure it keeps the last copy. `explorer_data` adds nominal GDP, population and the GDP
deflator from the indicators, for the measures in % of GDP, per person and at constant prices. The explorer itself
runs in the browser (static/budget.js).

Spending of one administration includes what it passes to others: central government's transfers to the
regions, local councils and the Social Security (COFOG group 01.8; ESA D.73 and D.9 within government) were
more than half its spending in 2024. The explorer shows them apart and can leave them out; the whole general
government is consolidated, so they cancel there.
"""

import io
import re
import unicodedata
from datetime import datetime, timezone

import openpyxl
import pandas as pd

from . import http
from .store import Store
from .tables import Data

STORE = "budget"            # data/budget.json
REGIONAL_STORE = "budget_regional"   # data/budget_regional.json: the per-community workbooks, already read
REFETCH_YEARS = 3           # the latest years' per-community workbooks are downloaded again on each fetch
DOCS = "https://www.igae.pap.hacienda.gob.es/sitios/igae/es-ES/Contabilidad/ContabilidadNacional/Publicaciones/Documents"
PAGES = {"cofog": "https://www.igae.pap.hacienda.gob.es/sitios/igae/es-ES/Contabilidad/ContabilidadNacional/Publicaciones/Paginas/iacogofseries.aspx",
         "accounts": "https://www.igae.pap.hacienda.gob.es/sitios/igae/es-ES/Contabilidad/ContabilidadNacional/Publicaciones/Paginas/ianofinancierasTotal.aspx",
         "taxes": "https://www.igae.pap.hacienda.gob.es/sitios/igae/es-ES/Contabilidad/ContabilidadNacional/Publicaciones/Paginas/iaimpuestosycotizaciones.aspx",
         "cofog_ccaa": "https://www.igae.pap.hacienda.gob.es/sitios/igae/es-ES/Contabilidad/ContabilidadNacional/Publicaciones/Paginas/iacofogCA.aspx",
         "accounts_ccaa": "https://www.igae.pap.hacienda.gob.es/sitios/igae/es-ES/Contabilidad/ContabilidadNacional/Publicaciones/Paginas/ianofinancierasCA.aspx",
         "taxes_ccaa": "https://www.igae.pap.hacienda.gob.es/sitios/igae/es-ES/Contabilidad/ContabilidadNacional/Publicaciones/Paginas/iaimpuestosycotizacionesCA.aspx"}
REGIONAL_FILES = {"accounts": ("CCAA-A/A_CCAA_Det_{year}.xlsx", r"A_CCAA_Det_(\d{4})\.xlsx", "accounts_ccaa"),
                  "cofog": ("CCAA-A/COFOG_A_Detalle_CCAA_{year}.xlsx", r"COFOG_A_Detalle_CCAA_(\d{4})\.xlsx", "cofog_ccaa")}
REGIONAL_TAXES = f"{DOCS}/CCAA-A/Detalle_por_CCAA_Imp.xlsx"
EUROSTAT_POPULATION = "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/demo_r_pjanaggr3"
# The administrations: id, IGAE code and folder, name, and whether flows to other administrations show up.
LEVELS = [
    {"id": "central", "code": "AACC", "folder": "AACC-A", "name": "The State (central government)",
     "short": "Central government", "transfers": True,
     "about": "The State and its agencies (Administración central), without the Social Security."},
    {"id": "social_security", "code": "AASS", "folder": "AASS-A", "name": "The Social Security",
     "short": "Social Security", "transfers": True,
     "about": "The Social Security funds: contributory pensions and other benefits, and the public employment service."},
    {"id": "regions", "code": "CCAA", "folder": "CCAA-A", "name": "All autonomous communities",
     "short": "Autonomous communities", "transfers": True, "regional": True,
     "about": "The 17 autonomous communities together (Administración regional): they run most of health, education "
              "and social services, largely paid for by transfers from the State under the regional financing system."},
    {"id": "general", "code": "AAPP", "folder": "AAPP_A", "name": "All public administrations",
     "short": "General government", "transfers": False,
     "about": "Central, regional and local government and the Social Security together, consolidated: flows between "
              "them cancel out."},
]

FUNCTIONS = [
    ("01", "General public services", [
        ("01.1", "Executive and legislative organs, financial, fiscal and external affairs"), ("01.2", "Foreign economic aid"),
        ("01.3", "General services"), ("01.4", "Basic research"), ("01.5", "R&D, general public services"),
        ("01.6", "General public services n.e.c."), ("01.7", "Public debt transactions (interest)"),
        ("01.8", "Transfers to other administrations")]),
    ("02", "Defence", [("02.1", "Military defence"), ("02.2", "Civil defence"), ("02.3", "Foreign military aid"),
                       ("02.4", "R&D, defence"), ("02.5", "Defence n.e.c.")]),
    ("03", "Public order and safety", [("03.1", "Police services"), ("03.2", "Fire-protection services"),
                                       ("03.3", "Law courts"), ("03.4", "Prisons"), ("03.5", "R&D, public order and safety"),
                                       ("03.6", "Public order and safety n.e.c.")]),
    ("04", "Economic affairs", [("04.1", "General economic, commercial and labour affairs"),
                                ("04.2", "Agriculture, forestry, fishing and hunting"), ("04.3", "Fuel and energy"),
                                ("04.4", "Mining, manufacturing and construction"), ("04.5", "Transport"),
                                ("04.6", "Communication"), ("04.7", "Other industries"), ("04.8", "R&D, economic affairs"),
                                ("04.9", "Economic affairs n.e.c.")]),
    ("05", "Environmental protection", [("05.1", "Waste management"), ("05.2", "Waste water management"),
                                        ("05.3", "Pollution abatement"), ("05.4", "Protection of biodiversity and landscape"),
                                        ("05.5", "R&D, environmental protection"), ("05.6", "Environmental protection n.e.c.")]),
    ("06", "Housing and community amenities", [("06.1", "Housing development"), ("06.2", "Community development"),
                                               ("06.3", "Water supply"), ("06.4", "Street lighting"),
                                               ("06.5", "R&D, housing and community amenities"),
                                               ("06.6", "Housing and community amenities n.e.c.")]),
    ("07", "Health", [("07.1", "Medical products, appliances and equipment"), ("07.2", "Outpatient services"),
                      ("07.3", "Hospital services"), ("07.4", "Public health services"), ("07.5", "R&D, health"),
                      ("07.6", "Health n.e.c.")]),
    ("08", "Recreation, culture and religion", [("08.1", "Recreational and sporting services"), ("08.2", "Cultural services"),
                                                ("08.3", "Broadcasting and publishing services"),
                                                ("08.4", "Religious and other community services"),
                                                ("08.5", "R&D, recreation, culture and religion"),
                                                ("08.6", "Recreation, culture and religion n.e.c.")]),
    ("09", "Education", [("09.1", "Pre-primary and primary education"), ("09.2", "Secondary education"),
                         ("09.3", "Post-secondary non-tertiary education"), ("09.4", "Tertiary education"),
                         ("09.5", "Education not definable by level"), ("09.6", "Subsidiary services to education"),
                         ("09.7", "R&D, education"), ("09.8", "Education n.e.c.")]),
    ("10", "Social protection", [("10.1", "Sickness and disability"), ("10.2", "Old age (pensions)"), ("10.3", "Survivors"),
                                 ("10.4", "Family and children"), ("10.5", "Unemployment"), ("10.6", "Housing"),
                                 ("10.7", "Social exclusion n.e.c."), ("10.8", "R&D, social protection"),
                                 ("10.9", "Social protection n.e.c.")]),
]
TRANSFER_FUNCTION = "01.8"

# Spending by economic type: item -> the ESA codes of the uses it adds up.
SPENDING_TYPES = [
    ("pay", "Pay of public employees", ["D.1"]),
    ("purchases", "Purchases of goods and services", ["P.2"]),
    ("benefits", "Social benefits (pensions, unemployment...)", ["D.62", "D.632"]),
    ("interest", "Interest on the debt", ["D.41"]),
    ("subsidies", "Subsidies", ["D.31", "D.39"]),
    ("investment", "Investment", ["P.51g", "P.52+P.53", "NP"]),
    ("capital_transfers", "Capital transfers and investment grants", ["D.92", "D.99"]),
    ("eu", "Contribution to the EU budget", ["D.76"]),
    ("other_current", "Other current transfers", ["D.71", "D.72", "D.74", "D.75"]),
    ("other", "Other", ["D.29", "D.42+..+D.45", "D.51", "D.8"]),
    ("transfers", "Transfers to other administrations", ["D.73", "D.9_S.13"]),
]
# Revenue by type: item -> resources codes; "irpf" and "corporate" come from the tax workbook.
REVENUE_TYPES = [
    ("vat", "VAT (and IGIC in Canarias)", ["D.211"]),
    ("irpf", "Personal income tax", []),
    ("corporate", "Corporate income tax", []),
    ("income_other", "Other taxes on income and wealth", ["D.51", "D.59"]),
    ("products", "Excise and other taxes on products", ["D.212", "D.214"]),
    ("production", "Other taxes on production", ["D.29"]),
    ("capital", "Taxes on capital (inheritance and gifts...)", ["D.91"]),
    ("contributions", "Social contributions", ["D.611", "D.612", "D.613"]),
    ("sales", "Sales of goods and services", ["P.11", "P.12", "P.131"]),
    ("property", "Property income (interest, dividends)", ["D.41", "D.42", "D.43+..+D.45"]),
    ("other", "Other transfers received (EU funds...)", ["D.39", "D.71", "D.72", "D.74", "D.75", "D.92", "D.99"]),
    ("transfers", "Transfers from other administrations", ["D.73", "D.9_S.13"]),
]
# Taxes on products shown one by one (row labels in the tax workbook start with these).
PRODUCT_TAXES = [
    ("hydrocarbons", "Hydrocarbons (fuel duty)", ["impuesto sobre hidrocarburos"]),
    ("tobacco", "Tobacco", ["impuesto sobre las labores del tabaco"]),
    ("alcohol", "Alcohol and beer", ["impuesto sobre el alcohol", "impuesto sobre la cerveza", "impuesto sobre productos intermedios"]),
    ("electricity", "Electricity", ["impuesto especial sobre la electricidad"]),
    ("power", "Tax on the value of electricity generation", ["impuestos sobre el valor de la produccion de la energia electrica"]),
    ("insurance", "Insurance premiums", ["impuesto sobre las primas de seguro"]),
]
INCOME_TAXES = {"irpf": "impuesto sobre la renta de personas", "corporate": "impuesto sobre sociedades"}
# The regions' own taxes on products, shown one by one.
REGION_PRODUCT_TAXES = [
    ("property_transfers", "Property transfers and stamp duty (ITP-AJD)", ["impuestos sobre transmisiones patrimoniales"]),
    ("gambling", "Gambling", ["impuestos y tasas sobre el juego"]),
    ("tourism", "Tourist stays", ["impuesto sobre estancias turisticas"]),
    ("hydrocarbons", "Fuel", ["impuesto sobre hidrocarburos", "impuesto sobre ventas minoristas de determinados hidrocarburos",
                             "impuesto sobre combustibles derivados del petroleo"]),
    ("vehicles", "Vehicle registration", ["impuesto especial sobre determinados medios transporte"]),
]
# The 17 autonomous communities: slug (as in indicators.yaml), name, Eurostat NUTS 2 code, and words that pick out
# the community in the IGAE's column and sheet headings.
COMMUNITIES = [
    ("andalucia", "Andalucía", "ES61", ["andalucia"]), ("aragon", "Aragón", "ES24", ["aragon"]),
    ("asturias", "Asturias", "ES12", ["asturias"]), ("baleares", "Illes Balears", "ES53", ["baleares", "balears"]),
    ("canarias", "Canarias", "ES70", ["canarias"]), ("cantabria", "Cantabria", "ES13", ["cantabria"]),
    ("castilla_mancha", "Castilla-La Mancha", "ES42", ["mancha"]), ("castilla_leon", "Castilla y León", "ES41", ["castilla y leon"]),
    ("cataluna", "Cataluña", "ES51", ["cataluna", "catalunya"]), ("extremadura", "Extremadura", "ES43", ["extremadura"]),
    ("galicia", "Galicia", "ES11", ["galicia"]), ("madrid", "Madrid", "ES30", ["madrid"]),
    ("murcia", "Región de Murcia", "ES62", ["murcia"]), ("navarra", "Navarra", "ES22", ["navarra"]),
    ("rioja", "La Rioja", "ES23", ["rioja"]), ("valenciana", "Comunitat Valenciana", "ES52", ["valencia"]),
    ("pais_vasco", "País Vasco", "ES21", ["pais vasco", "euskadi"]),
]


def _norm(text) -> str:
    text = unicodedata.normalize("NFKD", str(text or "")).encode("ascii", "ignore").decode()
    return " ".join(text.lower().replace("las fisicas", "fisicas").split())


def _code(text) -> str:
    """'D.92 (exc. D.9_S.13)' -> 'D.92'; 'D.42+..+D.45' stays."""
    return str(text or "").strip().split(" ")[0]


def _year(text) -> tuple[int | None, bool]:
    """'2024(P)' -> (2024, True)."""
    m = re.match(r"^\s*(\d{4})\s*(\(P\))?", str(text or ""))
    return (int(m[1]), bool(m[2])) if m else (None, False)


def _num(v) -> float | None:
    return float(v) if isinstance(v, (int, float)) else None


# ---------------------------------------------------------------- the workbooks

def parse_cofog(content: bytes) -> tuple[dict[str, dict[int, float]], list[int]]:
    """Spending by COFOG division ("07"), group ("07.3") and in total ("TOTAL"), by year; provisional years."""
    wb = openpyxl.load_workbook(io.BytesIO(content), read_only=True, data_only=True)
    out: dict[str, dict[int, float]] = {}
    provisional = []
    for ws in wb.worksheets:
        rows = list(ws.iter_rows(values_only=True))
        at = next((i for i, r in enumerate(rows) if len(r) > 1 and _norm(r[1]) == "gasto total"), None)
        if at is None or at < 2:
            continue
        year, prov = _year(rows[at - 2][0])
        if year is None:
            continue
        if prov:
            provisional.append(year)
        codes, divisions = rows[at - 1], rows[at - 2]
        for c, value in enumerate(rows[at]):
            v = _num(value)
            if v is None or c < 2:
                continue
            code = str(codes[c] or "").strip()
            if re.match(r"^\d{2}\.\d$", code):
                key = code
            elif m := re.match(r"^Total\s+(\d{2})$", code):
                key = m[1]
            elif "TOTAL" in str(divisions[c] or "").upper():
                key = "TOTAL"
            else:
                continue
            out.setdefault(key, {})[year] = v
    if "TOTAL" not in out:
        raise ValueError("COFOG workbook: no total spending found")
    return out, sorted(provisional)


def parse_accounts(content: bytes) -> tuple[dict, dict, list[int]]:
    """Non-financial resources and uses by ESA code and year (€ mn), and the provisional years."""
    ws = openpyxl.load_workbook(io.BytesIO(content), read_only=True, data_only=True)["Tabla1a"]
    rows = list(ws.iter_rows(values_only=True))
    head = next(i for i, r in enumerate(rows) if _norm(r[0]) == "codigo")
    years = [_year(v) for v in rows[head]]
    resources, uses, part = {}, {}, None
    for r in rows[head + 1:]:
        label = _norm(r[0] or r[1])     # the totals have no code, only a label in the second column
        if label.startswith("recursos no financieros"):
            part, code = resources, "TOTAL"
        elif label.startswith("empleos no financieros"):
            part, code = uses, "TOTAL"
        elif label.startswith(("b.9", "capacidad")):
            break
        elif label.startswith(("recursos corrientes", "recursos de capital", "empleos corrientes", "empleos de capital")):
            continue
        else:
            code = _code(r[0])
        if part is None or not code:
            continue
        for c, (year, _) in enumerate(years):
            if year is not None and (v := _num(r[c])) is not None:
                part.setdefault(code, {})[year] = v
    provisional = [y for y, p in years if y and p]
    if "TOTAL" not in resources or "TOTAL" not in uses:
        raise ValueError("accounts workbook: no total resources or uses found")
    return resources, uses, provisional


def parse_taxes(content: bytes) -> dict[str, dict[int, float]]:
    """Named taxes by year (€ mn), keyed by their normalised row label."""
    ws = openpyxl.load_workbook(io.BytesIO(content), read_only=True, data_only=True)["Tabla1a"]
    rows = list(ws.iter_rows(values_only=True))
    head = next(i for i, r in enumerate(rows) if _norm(r[0]) == "codigo")
    years = [_year(v)[0] for v in rows[head]]
    out = {}
    for r in rows[head + 1:]:
        name = _norm(r[1]) if len(r) > 1 else ""   # column 0 holds the ESA code, when the row has one
        if not name:
            continue
        values = {y: v for c, y in enumerate(years) if y is not None and c < len(r) and (v := _num(r[c])) is not None}
        if values and name not in out:
            out[name] = values
    return out


def _sum(table: dict, codes: list[str], years: list[int]) -> dict[int, float]:
    return {y: round(sum(table.get(c, {}).get(y, 0.0) for c in codes), 1) for y in years
            if any(y in table.get(c, {}) for c in codes)}


def _match(taxes: dict, prefixes: list[str], years: list[int]) -> dict[int, float]:
    rows = [v for name, v in taxes.items() if any(name.startswith(p) for p in prefixes)]
    return {y: round(sum(r.get(y, 0.0) for r in rows), 1) for y in years} if rows else {}


def _by_type(who: str, resources: dict, uses: dict, named: dict, product_taxes: list) -> dict:
    """Spending by type, revenue by type and taxes on products one by one, by year (€ mn).

    Personal and corporate income tax come from the tax workbook; in years it does not cover (the communities
    before 2012), all income tax counts as personal income tax."""
    years = sorted(set(resources["TOTAL"]) & set(uses["TOTAL"]))
    tax_years = {y for row in named.values() for y in row}
    types = {key: _sum(uses, codes, years) for key, _, codes in SPENDING_TYPES}
    revenue = {key: _sum(resources, codes, years) for key, _, codes in REVENUE_TYPES}
    income = _sum(resources, ["D.51"], years)
    for key, prefix in INCOME_TAXES.items():
        found = _match(named, [prefix], years)
        revenue[key] = {y: (found.get(y, 0.0) if y in tax_years else income.get(y, 0.0) if key == "irpf" else 0.0)
                        for y in years if y in income or y in found}
    # Income and wealth taxes other than the two big ones.
    revenue["income_other"] = {y: round(revenue["income_other"].get(y, 0.0) - revenue["irpf"].get(y, 0.0)
                                        - revenue["corporate"].get(y, 0.0), 1) for y in revenue["income_other"]}
    products = {key: {y: v for y, v in _match(named, prefixes, years).items() if y in tax_years}
                for key, _, prefixes in product_taxes}
    products["other"] = {y: round(revenue["products"].get(y, 0.0) - sum(p.get(y, 0.0) for p in products.values()), 1)
                         for y in revenue["products"] if y in tax_years}
    for name, parts, total in (("spending by type", types, uses["TOTAL"]), ("revenue", revenue, resources["TOTAL"])):
        for y in years:
            gap = abs(sum(p.get(y, 0.0) for p in parts.values()) - total[y])
            if gap > 3:
                raise ValueError(f"{who}: {name} in {y} adds up to {gap:.0f} mn less or more than the total")
    return {
        "type": {k: {str(y): v for y, v in s.items()} for k, s in types.items()} | {"TOTAL": {str(y): uses["TOTAL"][y] for y in years}},
        "revenue": {k: {str(y): v for y, v in s.items()} for k, s in revenue.items()} | {"TOTAL": {str(y): resources["TOTAL"][y] for y in years}},
        "products": {k: {str(y): v for y, v in s.items()} for k, s in products.items()},
    }


def build_level(level: dict, cofog: bytes, accounts: bytes, taxes: bytes) -> dict:
    """What the explorer shows for one administration, by year (€ mn)."""
    spend, cofog_prov = parse_cofog(cofog)
    resources, uses, acc_prov = parse_accounts(accounts)
    product_taxes = REGION_PRODUCT_TAXES if level.get("regional") else PRODUCT_TAXES
    return {"function": {k: {str(y): v for y, v in s.items()} for k, s in spend.items()},
            **_by_type(level["id"], resources, uses, parse_taxes(taxes), product_taxes),
            "provisional": {"function": cofog_prov, "accounts": acc_prov}}


# ---------------------------------------------------------------- the communities one by one

def _community(heading) -> str | None:
    name = _norm(heading)
    return next((slug for slug, _, _, keys in COMMUNITIES if any(k in name for k in keys)), None)


def _sheet_year(rows) -> tuple[int | None, bool]:
    """The year in a heading like 'Año 2024. Millones de euros' (provisional if it says so)."""
    for r in rows[:5]:
        m = re.search(r"(\d{4})\s*(\(P\))?", str(r[0] or ""))
        if m and "ano" in _norm(r[0]):
            return int(m[1]), bool(m[2]) or "provisional" in _norm(r[0])
    return None, False


def _columns(head) -> dict[int, str]:
    return {c: slug for c, v in enumerate(head) if c >= 2 and (slug := _community(v))}


def _walk_accounts(rows, head: int, columns: dict[int, str]) -> dict[str, dict]:
    """One year's resources, uses and balance for each community, from a sheet with a column each."""
    out = {slug: {"resources": {}, "uses": {}} for slug in columns.values()}
    part = None
    for r in rows[head + 1:]:
        label = _norm(r[0] or r[1])
        if label.startswith("recursos no financieros"):
            part, code = "resources", "TOTAL"
        elif label.startswith("empleos no financieros"):
            part, code = "uses", "TOTAL"
        elif label.startswith(("recursos corrientes", "recursos de capital", "empleos corrientes", "empleos de capital")):
            continue
        elif label.startswith("b.9"):
            for c, slug in columns.items():
                if (v := _num(r[c])) is not None:
                    out[slug]["balance"] = v
            break
        else:
            code = _code(r[0])
        if part is None or not code:
            continue
        for c, slug in columns.items():
            if (v := _num(r[c])) is not None:
                out[slug][part][code] = v
    return out


def parse_community_accounts(content: bytes) -> tuple[int, bool, dict[str, dict]]:
    """One year's workbook: each community's resources and uses (€ mn), balance and GDP (from the % of GDP sheet)."""
    wb = openpyxl.load_workbook(io.BytesIO(content), read_only=True, data_only=True)
    rows = list(wb["Tabla1a"].iter_rows(values_only=True))
    year, prov = _sheet_year(rows)
    head = next(i for i, r in enumerate(rows) if _norm(r[0]) == "codigo")
    out = _walk_accounts(rows, head, _columns(rows[head]))
    if "Tabla1b" in wb.sheetnames:
        pct_rows = list(wb["Tabla1b"].iter_rows(values_only=True))
        pct_head = next(i for i, r in enumerate(pct_rows) if _norm(r[0]) == "codigo")
        pct = _walk_accounts(pct_rows, pct_head, _columns(pct_rows[pct_head]))
        for slug, acc in out.items():
            share = pct.get(slug, {}).get("resources", {}).get("TOTAL")
            if share and acc["resources"].get("TOTAL"):
                acc["gdp"] = round(acc["resources"]["TOTAL"] / share * 100, 1)
    if year is None or not out:
        raise ValueError("community accounts workbook: no year or no communities found")
    return year, prov, out


def parse_community_cofog(content: bytes) -> tuple[int, bool, dict[str, dict[str, float]]]:
    """One year's workbook: each community's spending by COFOG division and in total (€ mn)."""
    wb = openpyxl.load_workbook(io.BytesIO(content), read_only=True, data_only=True)
    out, year, prov = {}, None, False
    for ws in wb.worksheets:
        rows = list(ws.iter_rows(values_only=True))
        slug = _community(rows[0][0]) if rows and rows[0] else None
        at = next((i for i, r in enumerate(rows) if len(r) > 1 and _norm(r[1]) == "gasto total"), None)
        if not slug or at is None or at < 2:
            continue
        year, prov = _year(rows[at - 2][0])
        spend = {}
        for c, head in enumerate(rows[at - 2]):
            v = _num(rows[at][c]) if c < len(rows[at]) else None
            if v is None or c < 2:
                continue
            if m := re.match(r"^\s*(\d{2})\.", str(head or "")):
                spend[m[1]] = v
            elif "TOTAL" in str(head or "").upper() or (head is None and spend):
                spend["TOTAL"] = v
        spend.setdefault("TOTAL", round(sum(v for k, v in spend.items()), 1))
        out[slug] = spend
    if year is None or not out:
        raise ValueError("community COFOG workbook: no year or no communities found")
    return year, prov, out


def parse_community_taxes(content: bytes) -> dict[int, dict[str, dict[str, float]]]:
    """Every year's taxes, tax by tax, for each community (€ mn): {year: {community: {tax: value}}}."""
    wb = openpyxl.load_workbook(io.BytesIO(content), read_only=True, data_only=True)
    out = {}
    for name in wb.sheetnames:
        if not re.match(r"^Tabla\d+a$", name):        # the "b" sheets are in % of GDP
            continue
        rows = list(wb[name].iter_rows(values_only=True))
        year, _ = _sheet_year(rows)
        head = next((i for i, r in enumerate(rows) if _norm(r[0]) == "codigo"), None)
        if year is None or head is None:
            continue
        columns = _columns(rows[head])
        taxes = {slug: {} for slug in columns.values()}
        for r in rows[head + 1:]:
            label = _norm(r[1]) if len(r) > 1 else ""
            if not label:
                continue
            for c, slug in columns.items():
                if (v := _num(r[c])) is not None and label not in taxes[slug]:
                    taxes[slug][label] = v
        out[year] = taxes
    return out


def build_community(slug: str, accounts: dict, cofog: dict, taxes: dict) -> dict:
    """One community's series (€ mn) from the years' parsed workbooks: {year: that year's figures}."""
    resources, uses, gdp, balance = {}, {}, {}, {}
    for year, by_slug in accounts.items():
        acc = by_slug.get(slug)
        if not acc:
            continue
        for code, v in acc["resources"].items():
            resources.setdefault(code, {})[int(year)] = v
        for code, v in acc["uses"].items():
            uses.setdefault(code, {})[int(year)] = v
        if "gdp" in acc:
            gdp[int(year)] = acc["gdp"]
        if "balance" in acc:
            balance[int(year)] = acc["balance"]
    named = {}
    for year, by_slug in taxes.items():
        for tax, v in by_slug.get(slug, {}).items():
            named.setdefault(tax, {})[int(year)] = v
    function = {}
    for year, by_slug in cofog.items():
        for code, v in by_slug.get(slug, {}).items():
            function.setdefault(code, {})[str(year)] = v
    return {"function": function, **_by_type(slug, resources, uses, named, REGION_PRODUCT_TAXES),
            "gdp": {str(y): v for y, v in gdp.items()}, "balance": {str(y): v for y, v in balance.items()}}


def _listed_years(kind: str) -> list[int]:
    """The years whose per-community workbooks the IGAE lists on its page."""
    _, pattern, page = REGIONAL_FILES[kind]
    return sorted({int(y) for y in re.findall(pattern, http.get(PAGES[page]).text)})


def population_by_community() -> dict[str, dict[str, float]]:
    """Average population of each community by year: the mean of 1 January of the year and of the next (Eurostat)."""
    nuts = {code: slug for slug, _, code, _ in COMMUNITIES}
    j = http.get(EUROSTAT_POPULATION, params={"format": "JSON", "geo": list(nuts), "sex": "T", "age": "TOTAL",
                                              "unit": "NR"}).json()
    times = {v: int(k) for k, v in j["dimension"]["time"]["category"]["index"].items()}
    geos = {v: k for k, v in j["dimension"]["geo"]["category"]["index"].items()}
    jan = {}
    for key, v in j["value"].items():
        k = int(key)
        jan.setdefault(nuts[geos[(k // len(times)) % len(geos)]], {})[times[k % len(times)]] = v
    return {slug: {str(y): (v + by_year[y + 1]) / 2 if y + 1 in by_year else v for y, v in by_year.items()}
            for slug, by_year in jan.items()}


def refresh_communities(store: Store) -> dict:
    """Each community's series, downloading only the workbooks not yet read and the latest years'."""
    raw = store.load_json(REGIONAL_STORE, None) or {}
    for kind, parse in (("accounts", parse_community_accounts), ("cofog", parse_community_cofog)):
        done = raw.get(kind, {})
        years = _listed_years(kind)
        provisional = set(raw.get(f"{kind}_provisional", []))
        for year in years:
            if str(year) in done and year < years[-1] - REFETCH_YEARS + 1:
                continue
            got, prov, by_slug = parse(http.get(f"{DOCS}/{REGIONAL_FILES[kind][0].format(year=year)}").content)
            done[str(got)] = by_slug
            provisional.discard(got)
            if prov:
                provisional.add(got)
        raw[kind], raw[f"{kind}_provisional"] = done, sorted(provisional)
    store.save_json(REGIONAL_STORE, {k: raw[k] for k in ("accounts", "accounts_provisional", "cofog", "cofog_provisional")})
    taxes = {str(y): v for y, v in parse_community_taxes(http.get(REGIONAL_TAXES).content).items()}
    population = population_by_community()
    out = {}
    for slug, *_ in COMMUNITIES:
        if not any(slug in by_slug for by_slug in raw["accounts"].values()):
            continue
        out[slug] = build_community(slug, raw["accounts"], raw["cofog"], taxes)
        out[slug]["population"] = population.get(slug, {})
        out[slug]["provisional"] = {"function": raw["cofog_provisional"], "accounts": raw["accounts_provisional"]}
    return out


def urls(level: dict) -> dict[str, str]:
    code, folder = level["code"], level["folder"]
    return {"cofog": f"{DOCS}/{folder}/COFOG_A_{code}.xlsx", "accounts": f"{DOCS}/{folder}/A_{code}.xlsx",
            "taxes": f"{DOCS}/{folder}/A_{code}_Imp.xlsx"}


def refresh(store: Store) -> str:
    """Download the IGAE workbooks into data/budget.json; on failure keep the last copy."""
    saved = store.load_json(STORE, None) or {}
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    try:
        levels = {}
        for level in LEVELS:
            files = {k: http.get(u).content for k, u in urls(level).items()}
            levels[level["id"]] = build_level(level, files["cofog"], files["accounts"], files["taxes"])
        communities = refresh_communities(store)
        state_budget = refresh_state_budget(saved.get("state_budget"))
    except Exception as e:  # keep what we had: the page says when it was last fetched
        saved.update(error=f"{type(e).__name__}: {e}", failed_at=now)
        store.save_json(STORE, saved)
        return f"not updated ({saved['error']}); keeping the copy from {saved.get('fetched_at', 'never')}"
    store.save_json(STORE, {"fetched_at": now, "levels": levels, "communities": communities, "state_budget": state_budget})
    last = max(int(y) for y in levels["central"]["revenue"]["TOTAL"])
    return f"{len(levels)} administrations and {len(communities)} communities, revenue and spending by type through {last}"



# ---------------------------------------------------------------- the State's budget (Batch 30c)
# The budget itself, unlike the national accounts above: what the Presupuestos Generales del Estado plan, by
# spending policy, and how much of it the State has spent. Two sources:
#   the budget office (SEPG): each year's statistics workbook of the consolidated budget (the State, its agencies
#       and the Social Security), with the initial appropriations by spending policy (chapters 1 to 8) and the
#       revenue by chapter for the past ten years or so; a column "2023-P" is the 2023 budget rolled over into 2024
#   the IGAE: the monthly execution of the State's own budget (without the Social Security), by spending policy:
#       final appropriations, obligations recognised and payments to date, and the year's changes to the budget

SEPG_PAGE = ("https://www.sepg.pap.hacienda.gob.es/sitios/sepg/es-ES/Presupuestos/DocumentacionEstadisticas/"
             "Estadisticas/Paginas/Estadisticas.aspx")
SEPG_FILE = re.compile(r'href="([^"]*/Documents/([0-9]{4}(?:-P)?)/01%20Presupuestos%20Generales%20del%20Estado%20Consolidados\.xlsx)"')
HISTORY_EDITION = "2023"    # the edition whose series reach back furthest (2014) on the same policy structure
EXECUTION_PAGE = ("https://www.igae.pap.hacienda.gob.es/sitios/igae/es-ES/Contabilidad/ContabilidadPublica/CPE/"
                  "EjecucionPresupuestaria/Paginas/imejecucionpresupuesto.aspx")
EXECUTION_FILE = re.compile(r'href="([^"]*/Documents/MENSUAL%20([A-Z]+)%20([0-9]{4})\.xlsx)"')
SPANISH_MONTHS = {"ENERO": 1, "FEBRERO": 2, "MARZO": 3, "ABRIL": 4, "MAYO": 5, "JUNIO": 6, "JULIO": 7, "AGOSTO": 8,
                  "SEPTIEMBRE": 9, "OCTUBRE": 10, "NOVIEMBRE": 11, "DICIEMBRE": 12}
# Spending policies (políticas de gasto): key, label, and the start of their Spanish names. Order matters where
# one name starts like another.
POLICIES = [
    ("pensions", "Pensions", ["pensiones"]),
    ("unemployment", "Unemployment benefits", ["desempleo"]),
    ("other_benefits", "Other cash benefits", ["otras prestaciones economicas"]),
    ("social_services", "Social services and promotion", ["servicios sociales"]),
    ("employment", "Employment promotion", ["fomento del empleo"]),
    ("housing", "Housing", ["acceso a la vivienda"]),
    ("labour_admin", "Labour and social economy administration", ["gestion y administracion de trabajo", "gestion y administ. de trabajo"]),
    ("inclusion_admin", "Inclusion, Social Security and migration administration", ["gestion y administracion de la inclusion", "gestion y admon. de inclusion"]),
    ("health", "Health", ["sanidad"]),
    ("education", "Education", ["educacion"]),
    ("culture", "Culture", ["cultura"]),
    ("justice", "Justice", ["justicia"]),
    ("defence", "Defence", ["defensa"]),
    ("security", "Public safety and prisons", ["seguridad ciudadana"]),
    ("foreign", "Foreign policy and development aid", ["politica exterior"]),
    ("agriculture", "Agriculture, fisheries and food", ["agricultura"]),
    ("industry", "Industry and energy", ["industria"]),
    ("trade", "Trade, tourism and SMEs", ["comercio"]),
    ("transport_subsidies", "Transport subsidies", ["subvenciones al transporte"]),
    ("infrastructure", "Infrastructure and resilient ecosystems", ["infraestructuras"]),
    ("research_civil", "Civil research", ["investigacion civil"]),
    ("research_military", "Military research", ["investigacion militar"]),
    ("research", "Research, development, innovation and digitalisation", ["investigacion"]),
    ("other_economic", "Other economic affairs", ["otras actuaciones de caracter economico"]),
    ("institutions", "Constitutional bodies and government", ["organos constitucionales"]),
    ("general_services", "General services", ["servicios de caracter general"]),
    ("tax_admin", "Financial and tax administration", ["administracion financiera"]),
    ("transfers", "Transfers to other administrations", ["transferencias a otras admin"]),
    ("debt", "Public debt", ["deuda publica"]),
    ("internal", "Transfers within the State's public sector", ["transferencias internas"]),
]
BUDGET_REVENUE = [
    ("direct", "Direct taxes and social contributions", ["impuestos directos"]),
    ("indirect", "Indirect taxes", ["impuestos indirectos"]),
    ("fees", "Fees, prices and other revenue", ["tasas"]),
    ("current_transfers", "Current transfers", ["transferencias corrientes"]),
    ("property", "Property income", ["ingresos patrimoniales"]),
    ("asset_sales", "Sales of real investments", ["enajenacion"]),
    ("capital_transfers", "Capital transfers", ["transferencias de capital"]),
    ("financial_assets", "Financial assets", ["activos financieros"]),
]


def _policy(label, table=POLICIES) -> str | None:
    """'2. Defensa' or 'Defensa' -> 'defence'."""
    name = re.sub(r"^\d+\.\s*", "", _norm(label))
    return next((key for key, _, prefixes in table if any(name.startswith(p) for p in prefixes)), None)


def _in_force(label) -> tuple[int | None, bool]:
    """A budget column: '2023' is the 2023 budget, '2023-P' the 2023 budget rolled over into 2024."""
    m = re.match(r"^\s*(\d{4})(-P)?\s*$", str(label if label is not None else ""))
    if not m:
        return None, False
    return (int(m[1]) + 1, True) if m[2] else (int(m[1]), False)


def _budget_sheet(rows, table) -> tuple[dict[int, dict[str, float]], list[int]]:
    head = next(i for i, r in enumerate(rows) if r and _norm(r[0]) in ("politicas", "capitulos"))
    columns = {c: _in_force(v) for c, v in enumerate(rows[head]) if _in_force(v)[0]}
    out, rolled, total = {}, set(), {}
    for r in rows[head + 1:]:
        label = _norm(r[0]) if r and r[0] else ""
        if label.startswith(("capitulos 1 a 8", "total capitulos")):
            for c, (year, _) in columns.items():
                if (v := _num(r[c])) is not None:
                    total[year] = v
            continue
        key = _policy(r[0], table) if label else None
        if not key:
            continue
        for c, (year, rolled_over) in columns.items():
            if (v := _num(r[c])) is not None:
                out.setdefault(year, {})[key] = out.get(year, {}).get(key, 0.0) + v
                if rolled_over:
                    rolled.add(year)
    for year, t in total.items():
        out.setdefault(year, {})["TOTAL"] = t
    return out, sorted(rolled)


def parse_budget(content: bytes) -> dict:
    """The consolidated budget by spending policy and revenue by chapter, by year in force (€ mn)."""
    wb = openpyxl.load_workbook(io.BytesIO(content), read_only=True, data_only=True)
    spending, rolled = _budget_sheet(list(wb["141"].iter_rows(values_only=True)), POLICIES)
    revenue, _ = _budget_sheet(list(wb["15"].iter_rows(values_only=True)), BUDGET_REVENUE)
    if not spending:
        raise ValueError("budget workbook: no spending policies found")
    return {"spending": spending, "revenue": revenue, "rolled_over": rolled}


def parse_execution(content: bytes) -> dict:
    """The State's execution by spending policy to date: appropriations (initial and final), obligations and
    payments (€ mn), from tables GTOS 016 and GTOS M03."""
    wb = openpyxl.load_workbook(io.BytesIO(content), read_only=True, data_only=True)

    def table(name, wanted):
        rows = list(wb[name].iter_rows(values_only=True))
        head = rows[1]
        cols = {key: next(c for c, v in enumerate(head) if v and text in _norm(v)) for key, text in wanted.items()}
        title = " ".join(str(v) for r in rows[:3] for v in r if v)
        out = {}
        for r in rows[2:]:
            label = str(r[0] or "").strip()
            if not label:
                continue
            key = "TOTAL" if _norm(label).startswith("totales") else (None if label.isupper() else _policy(label))
            if key:
                out[key] = {k: (_num(r[c]) or 0.0) / 1000 for k, c in cols.items()}   # thousands -> € mn
        return out, title

    spent, title = table("GTOS 016", {"final": "creditos", "obligations": "obligaciones", "payments": "pagos"})
    changes, _ = table("GTOS M03", {"changes": "total modificaciones"})
    m = re.search(r"HASTA EL (\d{1,2}) DE ([A-Z]+)", title.upper())
    if not m or m[2] not in SPANISH_MONTHS or "TOTAL" not in spent:
        raise ValueError("execution workbook: no date or no totals found")
    for key, row in spent.items():
        row["initial"] = round(row["final"] - changes.get(key, {}).get("changes", 0.0), 1)
        for k in ("final", "obligations", "payments"):
            row[k] = round(row[k], 1)
    return {"month": SPANISH_MONTHS[m[2]], "day": int(m[1]), "policies": spent}



# ---------------------------------------------------------------- the budget's execution in depth (Batch 30d)
# More tables of the same monthly IGAE workbook. Each gives the year to date and the same months of the year
# before: revenue (ING 002), the collection of the big taxes with the parts passed to the regions and councils
# (ING 012), spending by economic chapter (GTOS 004), the cash deficit and borrowing need (TES 015), the EU
# recovery funds (MRR00) and transfers to the regions and local councils (TCC 45, 75, 46, 76).

EXEC_CHAPTERS = [
    ("ch1", "Pay of staff", ["1. gastos de personal"]),
    ("ch2", "Purchases of goods and services", ["2. gastos en bienes"]),
    ("ch3", "Interest", ["3. gastos financieros"]),
    ("ch4", "Current transfers", ["4. transferencias corrientes"]),
    ("ch5", "Contingency fund", ["5. fdo", "5. fondo"]),
    ("ch6", "Investment", ["6. inversiones reales"]),
    ("ch7", "Capital transfers", ["7. transferencias de capital"]),
    ("nonfinancial", "Non-financial spending", ["total operaciones no financieras"]),
    ("ch8", "Financial assets", ["8. activos financieros"]),
    ("ch9", "Debt repayments", ["9. pasivos financieros"]),
    ("total", "Total", ["totales", "t o t a l e s"]),
]
EXEC_REVENUE = [
    ("ch1", "Direct taxes and social contributions", ["1. impuestos directos"]),
    ("irpf", "Personal income tax", ["impuesto sobre la renta de las", "impuesto sobre la renta de personas"]),
    ("corporate", "Corporate income tax", ["impuesto sobre sociedades"]),
    ("nonresident", "Non-residents' income tax", ["impuesto sobre la renta de no"]),
    ("ch2", "Indirect taxes", ["2. impuestos indirectos"]),
    ("vat", "VAT", ["impuesto sobre el valor"]),
    ("excise", "Excise duties", ["impuestos especiales"]),
    ("ch3", "Fees, prices and other revenue", ["3. tasas"]),
    ("ch4", "Current transfers", ["4. transferencias corrientes"]),
    ("ch5", "Property income", ["5. ingresos patrimoniales"]),
    ("ch6", "Sales of real investments", ["6. enajenacion"]),
    ("ch7", "Capital transfers", ["7. transferencias de capital"]),
    ("nonfinancial", "Non-financial revenue", ["total operaciones no financieras"]),
    ("ch8", "Financial assets", ["8. activos financieros"]),
    ("ch9", "Borrowing", ["9. pasivos financieros"]),
    ("total", "Total", ["totales", "t o t a l e s"]),
]
EXEC_TAXES = [
    ("irpf", "Personal income tax", ["impuesto sobre la renta de las", "impuesto sobre la renta de personas"]),
    ("vat", "VAT", ["impuesto sobre el valor"]),
    ("corporate", "Corporate income tax", ["impuesto sobre sociedades"]),
    ("excise", "Excise duties", ["impuestos especiales"]),
    ("nonresident", "Non-residents' income tax", ["impuesto sobre la renta de no"]),
    ("nonfinancial", "All non-financial revenue", ["total operaciones no financieras"]),
]
EXEC_CASH = [
    ("deficit", "Cash balance", ["1.- deficit"]),
    ("receipts", "Receipts", ["1.1. cobros"]),
    ("payments", "Payments", ["1.2. pagos"]),
    ("assets", "Change in financial assets", ["2.- variacion de activos"]),
    ("borrowing", "Net borrowing need", ["3.- necesidad"]),
]
EXEC_TRANSFERS = [("TCC 45", "regions_current", "To the regions, current"), ("TCC 75", "regions_capital", "To the regions, capital"),
                  ("TCC 46", "local_current", "To local councils, current"), ("TCC 76", "local_capital", "To local councils, capital")]
MINISTRIES = [
    ("asuntos ext", "Foreign affairs, EU and cooperation"), ("presidencia", "Presidency, justice and parliament"),
    ("defensa", "Defence"), ("hacienda", "Finance"), ("interior", "Interior"),
    ("transportes", "Transport and sustainable mobility"), ("educacion", "Education, vocational training and sport"),
    ("trabajo", "Labour and social economy"), ("industria", "Industry and tourism"),
    ("agricultura", "Agriculture, fisheries and food"), ("politica territorial", "Territorial policy and democratic memory"),
    ("transicion ecologica", "Ecological transition"), ("para la transicion ecologica", "Ecological transition"),
    ("cultura", "Culture"), ("vivienda", "Housing and urban agenda"), ("sanidad", "Health"),
    ("economia", "Economy, trade and business"), ("ciencia", "Science, innovation and universities"),
    ("derechos soc", "Social rights, consumer affairs and Agenda 2030"), ("igualdad", "Equality"),
    ("juventud", "Youth and children"), ("inclusion", "Inclusion, Social Security and migration"),
    ("para la transf. digital", "Digital transformation and civil service"),
    ("transformacion digital", "Digital transformation and civil service"),
]


def _row_key(label, table) -> str | None:
    name = _norm(label)
    return next((key for key, _, prefixes in table if any(name.startswith(p) for p in prefixes)), None)


def _year_columns(rows, header: tuple) -> dict[int, tuple[int | None, str]]:
    """Each value column's year (carried right from the first header row until another heading) and its name
    (the lower header rows joined)."""
    width = max(len(rows[r]) for r in header if r < len(rows))
    out, current = {}, None
    for c in range(1, width):
        top = rows[header[0]][c] if c < len(rows[header[0]]) else None
        if top not in (None, ""):
            m = re.match(r"^\s*(\d{4})", str(top))
            current = int(m[1]) if m else None
        name = " ".join(_norm(rows[r][c]) for r in header[1:] if r < len(rows) and c < len(rows[r]) and rows[r][c])
        out[c] = (current, name)
    return out


def _read(rows, wanted: dict[str, str], table, header=(1, 2)) -> dict[str, dict[str, dict[str, float]]]:
    """{row key: {year: {column key: € mn}}} from a table with the year in the first header row."""
    picks = {}
    for c, (year, name) in _year_columns(rows, header).items():
        for key, needle in wanted.items():
            if year is not None and needle in name and (year, key) not in picks:
                picks[(year, key)] = c
    out = {}
    for r in rows[max(header) + 1:]:
        label = str(r[0] or "").strip() if r else ""
        key = _row_key(label, table) if label else None
        if not key or key in out:
            continue
        out[key] = {}
        for (year, col), c in picks.items():
            v = _num(r[c]) if c < len(r) else None
            out[key].setdefault(str(year), {})[col] = round((v or 0.0) / 1000, 1)
    return out


def _mrr(rows) -> dict:
    """EU recovery funds by ministry: appropriations, commitments, obligations and payments (€ mn)."""
    head = rows[1]
    cols = {"credits": next(c for c, v in enumerate(rows[2]) if v and "total" in _norm(v)),
            **{key: next(c for c, v in enumerate(head) if v and text in _norm(v))
               for key, text in (("committed", "comprometidos"), ("obligations", "obligaciones"), ("payments", "pagos"))}}
    out, total = {}, None
    for r in rows[3:]:
        values = {k: round((_num(r[c]) or 0.0) / 1000, 1) for k, c in cols.items() if c < len(r)}
        label = str(r[0] or "").strip()
        if not label and any(_num(x) for x in r[1:]):
            total = values
            continue
        name = next((en for es, en in MINISTRIES if _norm(label).startswith(es)), label.title())
        if label and any(values.values()):
            out[name] = {k: out.get(name, {}).get(k, 0.0) + v for k, v in values.items()}
    return {"ministries": out, "total": total or {k: round(sum(m[k] for m in out.values()), 1) for k in cols}}


def parse_execution_detail(content: bytes) -> dict:
    """Revenue, tax collection, chapters, cash, EU funds and transfers to date, with the year before (€ mn)."""
    wb = openpyxl.load_workbook(io.BytesIO(content), read_only=True, data_only=True)

    def rows(name):
        return list(wb[name].iter_rows(values_only=True)) if name in wb.sheetnames else None

    out = {}
    if (r := rows("GTOS 004")):
        out["chapters"] = _read(r, {"final": "creditos", "committed": "comprometidos", "obligations": "obligaciones",
                                    "payments": "pagos"}, EXEC_CHAPTERS)
    if (r := rows("ING 002")):
        out["revenue"] = _read(r, {"forecast": "previsiones", "rights": "derechos", "collected": "recaudacion"}, EXEC_REVENUE)
    if (r := rows("ING 012")):
        out["taxes"] = _read(r, {"applied": "aplicada", "pending": "pendiente", "regions": "cc.aa", "local": "ee.ll",
                                 "state": "neta estado"}, EXEC_TAXES, header=(1, 2, 3))
    if (r := rows("TES 015")):
        out["cash"] = _read(r, {"value": ""}, EXEC_CASH, header=(1,))
    mrr = next((n for n in wb.sheetnames if n.startswith("MRR00")), None)
    if mrr:
        out["mrr"] = _mrr(rows(mrr))
    transfers = {}
    for sheet, key, _ in EXEC_TRANSFERS:
        if (r := rows(sheet)):
            got = _read(r, {"final": "creditos", "obligations": "obligaciones", "payments": "pagos"},
                        [("total", "Total", ["totales"])])
            if got.get("total"):
                transfers[key] = got["total"]
    out["transfers"] = transfers
    return out


def month_summary(detail: dict, year: int, policies: dict | None = None) -> dict:
    """One month's totals to date, for the year's path: spending, revenue, cash, a year earlier too; and for the
    pace of spending, each chapter's final appropriations and obligations (this year and the year before) and,
    from table GTOS 016, each policy's (this year only)."""
    def pick(part, row, col, y):
        return detail.get(part, {}).get(row, {}).get(str(y), {}).get(col)
    out = {"chapters": {k: [pick("chapters", k, "final", year), pick("chapters", k, "obligations", year),
                            pick("chapters", k, "final", year - 1), pick("chapters", k, "obligations", year - 1)]
                        for k in detail.get("chapters", {})}}
    if policies is not None:
        out["policies"] = {k: [round(v["final"], 1), round(v["obligations"], 1)] for k, v in policies.items()}
    return out | {"spending": pick("chapters", "nonfinancial", "obligations", year),
            "spending_prev": pick("chapters", "nonfinancial", "obligations", year - 1),
            "revenue": pick("revenue", "nonfinancial", "rights", year),
            "revenue_prev": pick("revenue", "nonfinancial", "rights", year - 1),
            "cash": pick("cash", "deficit", "value", year), "cash_prev": pick("cash", "deficit", "value", year - 1),
            "borrowing": pick("cash", "borrowing", "value", year),
            "borrowing_prev": pick("cash", "borrowing", "value", year - 1),
            "mrr": (detail.get("mrr") or {}).get("total", {}).get("obligations")}


def refresh_state_budget(saved: dict | None) -> dict:
    """The consolidated budget's series and the State's execution: the latest month, and the previous December."""
    saved = saved or {}
    page = http.get(SEPG_PAGE).text
    editions = {label: url for url, label in SEPG_FILE.findall(page)}
    if not editions:
        raise ValueError("SEPG statistics page: no consolidated budget workbooks found")
    host = "https://www.sepg.pap.hacienda.gob.es"
    latest = max(editions, key=lambda label: _in_force(label)[0])     # "2025-P" (in force in 2026) beats "2025"
    budget = {"spending": {}, "revenue": {}, "rolled_over": set()}
    for label in [HISTORY_EDITION, latest] if HISTORY_EDITION in editions else [latest]:
        part = parse_budget(http.get(host + editions[label]).content)
        for kind in ("spending", "revenue"):
            budget[kind].update(part[kind])                 # the latest edition wins where they overlap
        budget["rolled_over"] |= set(part["rolled_over"])
    execution = dict(saved.get("execution", {}))
    months = {y: dict(m) for y, m in saved.get("months", {}).items()}     # {year: {month: that month's totals}}
    files = {(int(y), SPANISH_MONTHS[m]): url for url, m, y in EXECUTION_FILE.findall(http.get(EXECUTION_PAGE).text)
             if m in SPANISH_MONTHS}
    if files:
        year, month = max(files)
        base = "https://www.igae.pap.hacienda.gob.es"
        december = (f"/sitios/igae/es-ES/Contabilidad/ContabilidadPublica/CPE/EjecucionPresupuestaria/Documents/"
                    f"MENSUAL%20DICIEMBRE%20{year - 1}.xlsx")
        # The latest month and the previous December in full; the year's other months for their totals and the
        # pace only, once each (the IGAE lists only the current year's workbooks, so the monthly path is kept as it
        # grows; a month kept before the pace was added is read again).
        wanted = [(year, month, files[(year, month)], True), (year - 1, 12, files.get((year - 1, 12), december), True)]
        wanted += [(y, m, url, False) for (y, m), url in sorted(files.items())
                   if y == year and m != month and "policies" not in months.get(str(y), {}).get(str(m), {})]
        for y, mo, url, full in wanted:
            try:
                content = http.get(url if url.startswith("http") else base + url).content
                detail = parse_execution_detail(content)
                got = parse_execution(content)
            except Exception:
                if (y, mo) == (year, month):
                    raise
                continue                                    # an older December that is not online: keep what we had
            months.setdefault(str(y), {})[str(mo)] = month_summary(detail, y, got["policies"])
            if full:
                execution[str(y)] = {**got, "detail": detail}
    return {"spending": {str(y): v for y, v in sorted(budget["spending"].items())},
            "revenue": {str(y): v for y, v in sorted(budget["revenue"].items())},
            "rolled_over": sorted(budget["rolled_over"]), "edition": latest, "execution": execution, "months": months}


def rolled_note(rolled: list[int], years: list[int]) -> str:
    """'the 2023 budget has stayed in force in 2024, 2025 and 2026', for the latest run of rolled-over years."""
    if not rolled:
        return ""
    run = [max(rolled)]
    while run[0] - 1 in rolled:
        run.insert(0, run[0] - 1)
    listed = ", ".join(str(y) for y in run[:-1]) + (" and " if len(run) > 1 else "") + str(run[-1])
    tense = "has stayed" if run[-1] == max(years) else "stayed"
    return f"the {run[0] - 1} budget {tense} in force in {listed}"


MONTH_KEYS = ("spending", "spending_prev", "revenue", "revenue_prev", "cash", "cash_prev", "borrowing", "borrowing_prev", "mrr")
INDENTED = {"irpf", "corporate", "nonresident", "vat", "excise"}      # the taxes under their chapters


def detail_for_page(detail: dict, year: int) -> dict:
    """The execution tables of one year, as rows the page can draw: this year and the year before."""
    this, prev = str(year), str(year - 1)

    def cell(part, row, col, y):
        return detail.get(part, {}).get(row, {}).get(y, {}).get(col)

    revenue = [{"code": k, "label": label, "indent": 1 if k in INDENTED else 0,
                **{c: cell("revenue", k, c, this) for c in ("forecast", "rights", "collected")},
                "rights_prev": cell("revenue", k, "rights", prev), "collected_prev": cell("revenue", k, "collected", prev)}
               for k, label, _ in EXEC_REVENUE if k in detail.get("revenue", {})]
    taxes = []
    for k, label, _ in EXEC_TAXES:
        if k not in detail.get("taxes", {}):
            continue
        now, before = detail["taxes"][k].get(this, {}), detail["taxes"][k].get(prev, {})
        taxes.append({"code": k, "label": label, "collected": round(now.get("applied", 0) + now.get("pending", 0), 1),
                      "regions": now.get("regions"), "local": now.get("local"), "state": now.get("state"),
                      "collected_prev": round(before.get("applied", 0) + before.get("pending", 0), 1) if before else None})
    chapters = [{"code": k, "label": label, **{c: cell("chapters", k, c, this) for c in ("final", "committed", "obligations", "payments")},
                 "obligations_prev": cell("chapters", k, "obligations", prev)}
                for k, label, _ in EXEC_CHAPTERS if k in detail.get("chapters", {})]
    cash = {k: {"label": label, "value": cell("cash", k, "value", this), "prev": cell("cash", k, "value", prev)}
            for k, label, _ in EXEC_CASH if k in detail.get("cash", {})}
    mrr = detail.get("mrr") or {}
    transfers = [{"code": key, "label": label, **{c: detail["transfers"][key].get(this, {}).get(c) for c in ("final", "obligations")},
                  "obligations_prev": detail["transfers"][key].get(prev, {}).get("obligations")}
                 for _, key, label in EXEC_TRANSFERS if key in detail.get("transfers", {})]
    return {"revenue": revenue, "taxes": taxes, "chapters": chapters, "cash": cash, "transfers": transfers,
            "mrr": {"rows": sorted(({"label": n, **v} for n, v in mrr.get("ministries", {}).items()),
                                   key=lambda r: -r.get("credits", 0)), "total": mrr.get("total")} if mrr else None}


def pace_for_page(months: dict) -> dict:
    """{year: {"policies"|"chapters": {code: {"final": [12], "obligations": [12]}}}} in € mn: each month's final
    appropriations and obligations to date. A year's chapters also come from the next year's year-earlier columns,
    so the year before the first kept workbook has its months too."""
    years = sorted({int(y) for y in months} | {int(y) - 1 for y in months})
    out = {}
    for y in years:
        own, after = months.get(str(y), {}), months.get(str(y + 1), {})
        part = {"policies": {}, "chapters": {}}
        for m in range(1, 13):
            here, later = own.get(str(m), {}), after.get(str(m), {})
            for code, (final, spent) in here.get("policies", {}).items():
                row = part["policies"].setdefault(code, {"final": [None] * 12, "obligations": [None] * 12})
                row["final"][m - 1], row["obligations"][m - 1] = final, spent
            for code in set(here.get("chapters", {})) | set(later.get("chapters", {})):
                mine, theirs = here.get("chapters", {}).get(code), later.get("chapters", {}).get(code)
                pair = mine[:2] if mine and mine[1] is not None else theirs[2:] if theirs and theirs[3] is not None else None
                if pair:
                    row = part["chapters"].setdefault(code, {"final": [None] * 12, "obligations": [None] * 12})
                    row["final"][m - 1], row["obligations"][m - 1] = pair
        if part["policies"] or part["chapters"]:
            out[str(y)] = part
    return out


def state_budget_data(saved: dict, gdp: dict[int, float]) -> dict | None:
    """The State's budget for the page: series by policy and chapter, and the execution tables."""
    sb = saved.get("state_budget")
    if not sb:
        return None
    years = sorted(int(y) for y in sb["spending"])
    spend_keys = [k for k, _, _ in POLICIES if any(k in sb["spending"][str(y)] for y in years)]
    rev_keys = [k for k, _, _ in BUDGET_REVENUE if any(k in sb["revenue"].get(str(y), {}) for y in years)]
    labels = {k: label for k, label, _ in POLICIES + BUDGET_REVENUE}
    month_names = ["", "January", "February", "March", "April", "May", "June", "July", "August", "September",
                   "October", "November", "December"]
    execution = []
    for y, ex in sorted(sb.get("execution", {}).items(), reverse=True):
        if "TOTAL" not in ex.get("policies", {}):
            continue
        rows = [{"code": k, "label": labels[k], **ex["policies"][k]} for k, _, _ in POLICIES if k in ex["policies"]]
        execution.append({"year": int(y), "month": ex["month"], "through": f"{ex['day']} {month_names[ex['month']]} {y}",
                          "full_year": ex["month"] == 12, "rows": rows, "total": ex["policies"]["TOTAL"],
                          "detail": detail_for_page(ex.get("detail") or {}, int(y))})
    return {
        "years": years, "rolled_over": sb["rolled_over"], "edition": sb.get("edition", ""),
        "rolled_note": rolled_note(sb["rolled_over"], years),
        "gdp": [gdp.get(y) for y in years],
        "policies": [{"code": k, "label": labels[k]} for k in spend_keys],
        "spending": {k: [sb["spending"][str(y)].get(k) for y in years] for k in spend_keys + ["TOTAL"]},
        "revenues": [{"code": k, "label": labels[k]} for k in rev_keys],
        "revenue": {k: [sb["revenue"].get(str(y), {}).get(k) for y in years] for k in rev_keys + ["TOTAL"]},
        "execution": execution,
        "months": {y: {k: [m.get(str(n), {}).get(k) for n in range(1, 13)] for k in MONTH_KEYS}
                   for y, m in sb.get("months", {}).items()},
        "pace": pace_for_page(sb.get("months", {})),
        "pace_items": {"policies": [{"code": k, "label": labels[k]} for k, _, _ in POLICIES],
                       "chapters": [{"code": k, "label": label} for k, label, _ in EXEC_CHAPTERS]},
        "pages": {"sepg": SEPG_PAGE, "igae": EXECUTION_PAGE},
    }


# ---------------------------------------------------------------- the page

def _annual(data: Data, ind_id: str, months: int = 12) -> dict[int, float]:
    s = data.raw(ind_id)
    if s is None:
        return {}
    s = s.dropna()
    if data.by_id[ind_id].freq == "A":
        return {d.year: float(v) for d, v in s.items()}
    groups = s.groupby(s.index.year)
    means = groups.mean()[groups.count() == months]
    return {int(y): float(v) for y, v in means.items()}


def explorer_data(store: Store, data: Data) -> dict | None:
    saved = store.load_json(STORE, None)
    if not saved or not saved.get("levels"):
        return None
    levels = saved["levels"]
    years = sorted({int(y) for lv in levels.values() for part in ("function", "type", "revenue")
                    for s in lv[part].values() for y in s})
    gdp, population, real = _annual(data, "gdp_nominal_annual"), _annual(data, "population_es"), _annual(data, "gdp_real_annual")
    deflator = {y: gdp[y] / real[y] for y in gdp if real.get(y)}        # the GDP deflator, back to 1995
    price_year = max((y for y in deflator if y <= years[-1]), default=None)

    def series(table: dict) -> dict[str, list]:
        return {k: [s.get(str(y)) for y in years] for k, s in table.items()}

    def products(regional: bool) -> list[dict]:
        return ([{"code": k, "label": label} for k, label, _ in (REGION_PRODUCT_TAXES if regional else PRODUCT_TAXES)]
                + [{"code": "other", "label": "Other taxes on products"}])

    out_levels = []
    for spec in LEVELS:
        lv = levels.get(spec["id"])
        if not lv:
            continue
        out_levels.append({**{k: spec[k] for k in ("id", "name", "short", "about", "transfers")},
                           "function": series(lv["function"]), "type": series(lv["type"]),
                           "revenue": series(lv["revenue"]), "products": series(lv["products"]),
                           "product_items": products(spec.get("regional", False)),
                           "provisional": lv["provisional"], "sources": urls(spec)})
    for slug, name, _, _ in COMMUNITIES:
        lv = saved.get("communities", {}).get(slug)
        if not lv:
            continue
        out_levels.append({"id": slug, "name": name, "short": name, "community": True, "transfers": True,
                           "about": f"The regional administration of {name}: spending by function from 2012, revenue and "
                                    "spending by type from 2000, taxes one by one from 2012.",
                           "function": series(lv["function"]), "type": series(lv["type"]),
                           "revenue": series(lv["revenue"]), "products": series(lv["products"]),
                           "product_items": products(True), "provisional": lv["provisional"],
                           "gdp": [lv["gdp"].get(str(y)) for y in years],
                           "population": [lv["population"].get(str(y)) for y in years],
                           "balance": [lv["balance"].get(str(y)) for y in years]})
    return {
        "years": years,
        "fetched_at": saved.get("fetched_at", ""),
        "gdp": [gdp.get(y) for y in years],
        "population": [population.get(y) for y in years],
        "prices": [deflator[y] / deflator[price_year] * 100 if y in deflator and price_year else None for y in years],
        "price_year": price_year,
        "functions": [{"code": c, "label": label, "children": [{"code": g, "label": gl} for g, gl in groups]}
                      for c, label, groups in FUNCTIONS],
        "types": [{"code": k, "label": label} for k, label, _ in SPENDING_TYPES],
        "revenues": [{"code": k, "label": label, "children": [{"code": "products"}] if k == "products" else []}
                     for k, label, _ in REVENUE_TYPES],
        "transfer_function": TRANSFER_FUNCTION,
        "levels": out_levels,
        "state_budget": state_budget_data(saved, gdp),
        "pages": PAGES,
    }


def fetched_day(bx: dict) -> str:
    """'2 Nov 2026', when the IGAE workbooks were last downloaded."""
    if not bx.get("fetched_at"):
        return "never"
    d = datetime.fromisoformat(bx["fetched_at"])
    return f"{d.day} {d:%b %Y}"


def provisional_note(bx: dict) -> str:
    """Which years are provisional, from central government's workbooks."""
    central = next((lv for lv in bx["levels"] if lv["id"] == "central"), None)
    if not central:
        return ""
    parts = []
    if central["provisional"].get("function"):
        parts.append(f"{max(central['provisional']['function'])} for spending by function")
    if central["provisional"].get("accounts"):
        parts.append(f"{max(central['provisional']['accounts'])} for spending by type and revenue")
    return " and ".join(parts)
