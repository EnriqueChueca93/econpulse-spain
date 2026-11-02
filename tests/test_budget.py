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
    assert next(r for r in bx["revenues"] if r["code"] == "products")["children"][0]["code"] == "hydrocarbons"


def test_linked_from_fiscal_and_tools():
    assert ("budget-explorer.html", "Budget explorer") in NAV_SUBPAGES["fiscal.html"]
    assert ("budget-explorer.html", "Budget explorer") in NAV_EXTRA["tools.html"]
    assert "population_es" in {i.id for i in load_registry()}
