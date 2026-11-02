"""Batch 30a: the Budget explorer, from the IGAE's national accounts workbooks (no network)."""

import io

import openpyxl
import pandas as pd
import pytest

from econpulse import budget
from econpulse.build import NAV_EXTRA, NAV_SUBPAGES
from econpulse.registry import load_registry
from econpulse.store import Store
from econpulse.tables import Data


def workbook(sheets: dict[str, list[list]]) -> bytes:
    wb = openpyxl.Workbook()
    wb.remove(wb.active)
    for name, rows in sheets.items():
        ws = wb.create_sheet(name)
        for r in rows:
            ws.append(r)
    out = io.BytesIO()
    wb.save(out)
    return out.getvalue()


def cofog_sheet(year_label, values):
    filler = [["ADMINISTRACIÓN CENTRAL"]] * 6
    return filler + [
        [year_label, None, "01. Servicios públicos generales", None, None, "10. Protección social", None, " TOTAL"],
        [None, None, "01.1", "01.8", "Total 01", "10.2", "Total 10", None],
        [None, "GASTO TOTAL", *values],
        ["D.1", "Remuneración de asalariados", 1, 0, 1, 0, 0, 1],
    ]


COFOG = workbook({"Indice": [["ÍNDICE"]], "2023": cofog_sheet("2023", [10, 80, 90, 40, 40, 130]),
                  "2024": cofog_sheet("2024(P)", [12, 90, 102, 50, 50, 152])})
ACCOUNTS = workbook({"Tabla1a": [
    ["ADMINISTRACIÓN CENTRAL"], [], ["CÓDIGO", "CONCEPTOS", "2024", "2025(P)"],
    [None, "RECURSOS NO FINANCIEROS", 300, 330], [None, "RECURSOS CORRIENTES", 300, 330],
    ["D.211", "Impuestos del tipo valor añadido", 100, 110], ["D.51", "Impuestos sobre la renta", 120, 130],
    ["D.611", "Cotizaciones sociales efectivas", 20, 25], ["D.73", "Transferencias corrientes entre AAPP", 60, 65],
    [None, "EMPLEOS NO FINANCIEROS", 400, 420], [None, "EMPLEOS CORRIENTES", 400, 420],
    ["D.1", "Remuneración de asalariados", 100, 105], ["D.62", "Prestaciones sociales", 50, 55],
    ["D.41", "Intereses", 30, 30], ["D.73", "Transferencias corrientes entre AAPP", 220, 230],
    ["B.9", "CAPACIDAD (+) / NECESIDAD (-) DE FINANCIACIÓN", -100, -90]]})
TAXES = workbook({"Tabla1a": [
    ["ADMINISTRACIÓN CENTRAL"], ["CÓDIGO", "CONCEPTOS", "2024", "2025(P)"],
    ["D.51", "Impuestos sobre la renta", 120, 130],
    [None, "Impuesto sobre la Renta de Personas las Físicas / Impuesto sobre la Renta de no Residentes", 80, 85],
    [None, "Impuesto sobre Sociedades / Impuesto sobre la Renta de No Residentes", 40, 45],
    [None, "Impuesto sobre Hidrocarburos", 0, 0]]})


def test_parse_the_workbooks():
    spend, provisional = budget.parse_cofog(COFOG)
    assert spend["TOTAL"] == {2023: 130.0, 2024: 152.0} and spend["01"][2024] == 102.0 and spend["10.2"][2023] == 40.0
    assert provisional == [2024]
    resources, uses, prov = budget.parse_accounts(ACCOUNTS)
    assert resources["TOTAL"][2025] == 330 and uses["D.73"][2024] == 220 and "D.73" in resources and prov == [2025]
    taxes = budget.parse_taxes(TAXES)
    assert taxes["impuesto sobre sociedades / impuesto sobre la renta de no residentes"][2025] == 45


def test_build_a_level_adds_up():
    level = budget.build_level(budget.LEVELS[0], COFOG, ACCOUNTS, TAXES)
    rev, types = level["revenue"], level["type"]
    assert rev["irpf"]["2025"] == 85 and rev["corporate"]["2025"] == 45 and rev["income_other"]["2025"] == 0
    assert rev["transfers"]["2024"] == 60 and rev["TOTAL"]["2024"] == 300
    assert types["transfers"]["2025"] == 230 and types["benefits"]["2024"] == 50 and types["TOTAL"]["2025"] == 420
    assert level["function"]["01.8"]["2024"] == 90 and level["provisional"] == {"function": [2024], "accounts": [2025]}


def test_a_gap_in_the_totals_is_caught():
    broken = workbook({"Tabla1a": [
        ["CÓDIGO", "CONCEPTOS", "2024"], [None, "RECURSOS NO FINANCIEROS", 300], ["D.211", "IVA", 100],
        [None, "EMPLEOS NO FINANCIEROS", 50], ["D.1", "Pay", 50], ["B.9", "CAPACIDAD", 250]]})
    with pytest.raises(ValueError, match="adds up"):
        budget.build_level(budget.LEVELS[0], COFOG, broken, TAXES)


def test_explorer_data(tmp_path):
    store = Store(tmp_path / "data")
    level = budget.build_level(budget.LEVELS[0], COFOG, ACCOUNTS, TAXES)
    store.save_json(budget.STORE, {"fetched_at": "2026-11-02T03:00:00+00:00", "levels": {"central": level}})
    years = pd.date_range("2023-01-01", "2025-01-01", freq="YS")
    store.save_series("gdp_nominal_annual", pd.Series([1000.0, 1100.0, 1200.0], index=years))
    store.save_series("gdp_real_annual", pd.Series([1000.0, 1000.0, 1000.0], index=years))
    store.save_series("population_es", pd.Series([48e6, 49e6, 49.4e6], index=years))
    bx = budget.explorer_data(store, Data(load_registry(), store))
    assert bx["years"] == [2023, 2024, 2025] and bx["price_year"] == 2025
    assert [round(p, 2) for p in bx["prices"]] == [83.33, 91.67, 100.0]           # the GDP deflator, 2025 = 100
    central = bx["levels"][0]
    assert central["id"] == "central" and central["function"]["TOTAL"] == [130.0, 152.0, None]
    assert central["revenue"]["vat"] == [None, 100.0, 110.0]
    assert budget.fetched_day(bx) == "2 Nov 2026"
    assert budget.provisional_note(bx) == "2024 for spending by function and 2025 for spending by type and revenue"
    assert [f["code"] for f in bx["functions"]] == [f"{n:02d}" for n in range(1, 11)]
    assert central["product_items"][0]["code"] == "hydrocarbons" and central["product_items"][-1]["code"] == "other"


def test_linked_from_fiscal_and_tools():
    assert ("budget-explorer.html", "Budget explorer") in NAV_SUBPAGES["fiscal.html"]
    assert ("budget-explorer.html", "Budget explorer") in NAV_EXTRA["tools.html"]
    assert "population_es" in {i.id for i in load_registry()}


# ---------------------------------------------------------------- Batch 30b: the communities one by one

def community_accounts(year_label, madrid_pay):
    head = ["CÓDIGO", "CONCEPTOS", "Andalucía", "Comunidad de Madrid"]
    rows = [["ADMINISTRACIÓN REGIONAL"], ["Operaciones no financieras"], [f"Año {year_label}. Millones de euros"], [], [],
            head, [None, "RECURSOS NO FINANCIEROS", 100, 80], ["D.51", "Impuestos sobre la renta", 30, 50],
            ["D.73", "Transferencias corrientes entre AAPP", 70, 30],
            [None, "EMPLEOS NO FINANCIEROS", 110, 80], ["D.1", "Remuneración de asalariados", 60, madrid_pay],
            ["P.2", "Consumos intermedios", 50, 80 - madrid_pay], ["B.9", "CAPACIDAD (+) O NECESIDAD (-)", -10, 0]]
    pct = [["ADMINISTRACIÓN REGIONAL"], [], [f"Año {year_label}. % del PIB regional"], [], [], head,
           [None, "RECURSOS NO FINANCIEROS", 10.0, 4.0]]
    return workbook({"Tabla1a": rows, "Tabla1b": pct})


def community_cofog(year_label):
    def sheet(name, health, total):
        return [[name]] + [[None]] * 5 + [[year_label, None, " 01. Servicios públicos generales", "  07.Salud", "TOTAL"], [],
                                           [None, "GASTO TOTAL", total - health, health, total]]
    return workbook({"Indice": [["ÍNDICE"]], "Tabla1a": sheet("ADMINISTRACIÓN REGIONAL", 70, 190),
                     "Tabla2a": sheet("Andalucía", 40, 110), "Tabla13a": sheet("Madrid", 30, 80)})


COMMUNITY_TAXES = workbook({"Tabla1a": [
    ["ADMINISTRACIÓN REGIONAL"], [], ["AÑO 2024. Millones de euros"], [], [],
    ["CÓDIGO", "CONCEPTOS", "Andalucía", "Comunidad de Madrid"],
    ["D.51", "Impuestos sobre la renta", 30, 50], [None, "Impuesto sobre la Renta de Personas las Físicas", 30, 50],
    [None, "Impuestos sobre Transmisiones Patrimoniales y Actos Jurídicos Documentados", 0, 0]],
    "Tabla1b": [["% del PIB"], [], ["AÑO 2024. % del PIB"]]})


def test_community_names():
    assert [budget._community(n) for n in ("Comunitat Valenciana", "Castilla-La Mancha", "Castilla y León", "Región de Murcia",
                                           "Illes Balears", "Comunidad Foral de Navarra", "Ceuta")] == \
        ["valenciana", "castilla_mancha", "castilla_leon", "murcia", "baleares", "navarra", None]


def test_parse_community_workbooks():
    year, prov, acc = budget.parse_community_accounts(community_accounts("2024", 50))
    assert (year, prov) == (2024, False) and set(acc) == {"andalucia", "madrid"}
    assert acc["andalucia"]["resources"]["D.73"] == 70 and acc["andalucia"]["balance"] == -10
    assert acc["andalucia"]["gdp"] == 1000.0 and acc["madrid"]["gdp"] == 2000.0     # € over % of GDP
    year, prov, spend = budget.parse_community_cofog(community_cofog("2024(P)"))
    assert (year, prov) == (2024, True) and spend["andalucia"] == {"01": 70, "07": 40, "TOTAL": 110}
    assert "regions" not in spend and set(spend) == {"andalucia", "madrid"}
    taxes = budget.parse_community_taxes(COMMUNITY_TAXES)
    assert list(taxes) == [2024] and taxes[2024]["madrid"]["impuesto sobre la renta de personas fisicas"] == 50


def test_build_a_community():
    accounts = {"2011": budget.parse_community_accounts(community_accounts("2011", 40))[2],
                "2024": budget.parse_community_accounts(community_accounts("2024", 50))[2]}
    cofog = {"2024": budget.parse_community_cofog(community_cofog("2024"))[2]}
    taxes = budget.parse_community_taxes(COMMUNITY_TAXES)
    madrid = budget.build_community("madrid", accounts, cofog, taxes)
    assert madrid["function"]["07"] == {"2024": 30} and madrid["gdp"] == {"2011": 2000.0, "2024": 2000.0}
    assert madrid["revenue"]["irpf"] == {"2011": 50.0, "2024": 50.0}       # 2011: no tax detail, all income tax
    assert madrid["revenue"]["transfers"]["2024"] == 30 and madrid["type"]["pay"] == {"2011": 40.0, "2024": 50.0}
    assert madrid["balance"]["2024"] == 0 and madrid["products"]["property_transfers"] == {"2024": 0.0}


def test_only_new_and_recent_workbooks_are_downloaded(tmp_path, monkeypatch):
    store = Store(tmp_path / "data")
    years = list(range(2018, 2025))
    files = {f"A_CCAA_Det_{y}.xlsx": community_accounts(str(y), 50) for y in years}
    files |= {f"COFOG_A_Detalle_CCAA_{y}.xlsx": community_cofog(str(y)) for y in years}
    files["Detalle_por_CCAA_Imp.xlsx"] = COMMUNITY_TAXES
    listing = " ".join(files)
    asked = []

    class Reply:
        def __init__(self, url):
            name = url.rsplit("/", 1)[-1]
            self.text, self.content = listing, files.get(name, b"")
            asked.append(name)

    monkeypatch.setattr(budget.http, "get", lambda url, **_: Reply(url))
    monkeypatch.setattr(budget, "population_by_community", lambda: {"madrid": {"2024": 7.0e6}})
    first = budget.refresh_communities(store)
    assert first["madrid"]["population"] == {"2024": 7.0e6} and first["madrid"]["type"]["TOTAL"]["2018"] == 80
    downloads = [a for a in asked if a.endswith(".xlsx")]
    assert len(downloads) == 2 * len(years) + 1
    asked.clear()
    budget.refresh_communities(store)
    again = sorted(a for a in asked if a.endswith(".xlsx") and "Det_" in a)
    assert again == ["A_CCAA_Det_2022.xlsx", "A_CCAA_Det_2023.xlsx", "A_CCAA_Det_2024.xlsx"]
