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
    except Exception as e:  # keep what we had: the page says when it was last fetched
        saved.update(error=f"{type(e).__name__}: {e}", failed_at=now)
        store.save_json(STORE, saved)
        return f"not updated ({saved['error']}); keeping the copy from {saved.get('fetched_at', 'never')}"
    store.save_json(STORE, {"fetched_at": now, "levels": levels, "communities": communities})
    last = max(int(y) for y in levels["central"]["revenue"]["TOTAL"])
    return f"{len(levels)} administrations and {len(communities)} communities, revenue and spending by type through {last}"


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
