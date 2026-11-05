"""Batches 30a-31c: the Budget explorer, from the IGAE's and the budget office's workbooks (no network)."""

import io
import re
from pathlib import Path

import openpyxl
import pandas as pd
import pytest

from econpulse import budget
from econpulse.build import COMMUNITIES_EXPLORER, NAV_EXTRA, NAV_SUBPAGES, build_site
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


def test_over_time_can_be_lines_or_stacked(tmp_path):
    """Batch B1: a switch in the caption of the charts over time (static/budget.js and static/pge.js draw them)."""
    store = Store(tmp_path / "data")
    store.save_json(budget.STORE, {"fetched_at": "2026-11-02T03:00:00+00:00",
                                   "levels": {"central": budget.build_level(budget.LEVELS[0], COFOG, ACCOUNTS, TAXES)}})
    build_site(load_registry(), store, site_dir=tmp_path / "site")
    for page, words in (("budget-explorer.html", ("Draw as", "Lines", "Stacked")),
                        ("es/budget-explorer.html", ("Dibujar como", "Líneas", "Apilado"))):
        html = (tmp_path / "site" / page).read_text(encoding="utf-8")
        caption = re.search(r'id="fig-bx-trend">\s*<figcaption class="has-range">(.*?)</figcaption>', html, re.S).group(1)
        assert f'aria-label="{words[0]}"' in caption and f'data-form="lines" aria-pressed="true">{words[1]}<' in caption
        assert f'data-form="stack" aria-pressed="false">{words[2]}<' in caption
        assert 'data-form="stack"' not in re.search(r'id="fig-bx-mix">(.*?)</figure>', html, re.S).group(1)
    # The State's budget section needs the budget office's workbooks; its chart over time asks for the same switch.
    for template in ("templates/budget-explorer.html", "templates/es/budget-explorer.html"):
        source = (Path(__file__).parent.parent / template).read_text(encoding="utf-8")
        assert re.search(r'figure\("pge-trend", [^\n]*forms=true\)', source) and re.search(r'figure\("bx-trend", [^\n]*forms=true\)', source)


def test_linked_from_fiscal_and_tools():
    assert ("budget-explorer.html", "Budget explorer") in NAV_SUBPAGES["fiscal.html"]
    assert ("budget-explorer.html", "Budget explorer") in NAV_EXTRA["tools.html"]
    # The communities' explorer, under Regions and Tools (Batch 32a).
    assert COMMUNITIES_EXPLORER == ("budget-explorer.html#level=regions", "Budget explorer: the autonomous communities")
    assert COMMUNITIES_EXPLORER in NAV_SUBPAGES["regions.html"] and COMMUNITIES_EXPLORER in NAV_EXTRA["tools.html"]
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


# ---------------------------------------------------------------- Batch 30c: the State's budget

BUDGET_BOOK = workbook({
    "141": [["1.4. Políticas de gasto"], ["Millones de euros"],
            ["Políticas", "2023", "2023-P", "2024-P"],
            ["Pensiones", 190687.2, 190687.2, 190687.2], ["Defensa", 12316.8, 12316.8, 12316.8],
            ["Investigación civil", 15933.7, 15963.7, 15969.9], ["Investigación militar", 1833.3, 1833.3, 1833.3],
            ["CAPÍTULOS 1 a 8", 220771.0, 220801.0, 220807.2]],
    "15": [["1.5. Ingresos"], ["Capítulos", "2023", "2023-P", "2024-P"], ["Impuestos directos", 269000.3, 269000.3, 269000.3],
           ["Impuestos indirectos", 57809.2, 57809.2, 57809.2], ["TOTAL CAPÍTULOS 1 a 8", 326809.5, 326809.5, 326809.5]]})
EXECUTION_SHEETS = {
    "GTOS 016": [["Miles de euros"],
                 ["PRESUPUESTO DE GASTOS ESTADO DE EJECUCIÓN: ÁREAS DE GASTO Y POLÍTICAS HASTA EL 31 DE AGOSTO",
                  "CRÉDITOS DEFINITIVOS (1)", "OBLIGACIONES RECONOCIDAS NETAS (2)", "PAGOS REALIZADOS (3)"],
                 [None, None, None, None],
                 ["1. SERVICIOS PÚBLICOS BASICOS", 21669344, 7883956, 7806598],
                 ["2. Defensa", 21669344, 7883956, 7806598],
                 ["2. ACTUACIONES DE PROTECCIÓN Y PROMOCIÓN SOCIAL", 20508661, 15911213, 15910957],
                 ["1. Pensiones", 20508661, 15911213, 15910957],
                 ["TOTALES", 42178005, 23795169, 23717555]],
    "GTOS M03": [["Miles de euros"], ["PRESUPUESTO DE GASTOS MODIFICACIONES DE CREDITO", "CRÉDITOS EXTRAORDINARIOS (1)", "TOTAL MODIFICACIONES (10)"],
                 [None], ["2. Defensa", 0, 9607135], ["1. Pensiones", 0, 50], ["TOTALES", 0, 9607185]]}
EXECUTION_BOOK = workbook(EXECUTION_SHEETS)


def test_budget_columns_and_policies():
    assert budget._in_force("2023") == (2023, False) and budget._in_force("2023-P") == (2024, True)
    assert budget._in_force(2016) == (2016, False) and budget._in_force("Políticas") == (None, False)
    assert budget._policy("2. Defensa") == "defence" and budget._policy("Investigación civil") == "research_civil"
    assert budget._policy("6. Investigación, desarrollo, innovación y digitalización") == "research"
    assert budget._policy("9. Gestión y admón. de Inclusión,S.Social y Migraciones") == "inclusion_admin"
    assert budget._policy("8. Gestión y administ. de Trabajo y Economía Social") == "labour_admin"
    assert budget.rolled_note([2019, 2020, 2024, 2025, 2026], list(range(2014, 2027))) == \
        "the 2023 budget has stayed in force in 2024, 2025 and 2026"


def test_parse_the_budget_and_its_execution():
    b = budget.parse_budget(BUDGET_BOOK)
    assert sorted(b["spending"]) == [2023, 2024, 2025] and b["rolled_over"] == [2024, 2025]
    assert b["spending"][2025]["pensions"] == 190687.2 and b["spending"][2024]["TOTAL"] == 220801.0
    assert b["revenue"][2025] == {"direct": 269000.3, "indirect": 57809.2, "TOTAL": 326809.5}
    ex = budget.parse_execution(EXECUTION_BOOK)
    assert (ex["month"], ex["day"]) == (8, 31)
    assert ex["policies"]["defence"] == {"final": 21669.3, "obligations": 7884.0, "payments": 7806.6, "initial": 12062.2}
    assert ex["policies"]["TOTAL"]["initial"] == round(42178.005 - 9607.185, 1)
    assert set(ex["policies"]) == {"defence", "pensions", "TOTAL"}            # area headings are skipped


def test_refresh_the_state_budget(monkeypatch):
    sepg = ('<a href="/sitios/sepg/es-ES/x/Documents/2025-P/01%20Presupuestos%20Generales%20del%20Estado%20Consolidados.xlsx">'
            '<a href="/sitios/sepg/es-ES/x/Documents/2023/01%20Presupuestos%20Generales%20del%20Estado%20Consolidados.xlsx">')
    igae = '<a href="/sitios/igae/x/Documents/MENSUAL%20AGOSTO%202026.xlsx"><a href="/sitios/igae/x/Documents/MENSUAL%20JULIO%202026.xlsx">'
    asked = []

    class Reply:
        def __init__(self, url):
            asked.append(url.rsplit("/", 1)[-1])
            self.text = sepg if "Estadisticas.aspx" in url else igae
            self.content = EXECUTION_BOOK if "MENSUAL" in url else BUDGET_BOOK

    monkeypatch.setattr(budget.http, "get", lambda url, **_: Reply(url))
    sb = budget.refresh_state_budget({"execution": {"2024": {"month": 12, "day": 31, "policies": {}}}})
    assert sb["edition"] == "2025-P" and sb["rolled_over"] == [2024, 2025]
    assert set(sb["execution"]) == {"2024", "2025", "2026"} and sb["execution"]["2026"]["month"] == 8
    assert "MENSUAL%20AGOSTO%202026.xlsx" in asked and "MENSUAL%20DICIEMBRE%202025.xlsx" in asked
    page = budget.state_budget_data({"state_budget": sb}, {2023: 1_500_000.0})
    assert page["years"] == [2023, 2024, 2025] and page["gdp"] == [1_500_000.0, None, None]
    assert page["execution"][0]["year"] == 2026 and page["execution"][0]["through"] == "31 August 2026"
    assert [p["code"] for p in page["policies"]] == ["pensions", "defence", "research_civil", "research_military"]


# ---------------------------------------------------------------- Batch 30d: the rest of the execution report

DETAIL_SHEETS = {
    "GTOS 004": [[None],
                 ["PRESUPUESTO DE GASTOS\nESTADO DE EJECUCIÓN. CAPÍTULOS\nHASTA EL 31 DE AGOSTO", "2026", None, None, None,
                  "2025", None, None, None, "% DE REALIZACIÓN"],
                 [None, "CRÉDITOS DEFINITIVOS\n(1)", "GASTOS COMPROMETIDOS\n(2)", "OBLIGACIONES RECONOCIDAS NETAS\n(3)",
                  "PAGOS REALIZADOS\n(4)", "CRÉDITOS DEFINITIVOS\n(5)", "GASTOS COMPROMETIDOS\n(6)",
                  "OBLIGACIONES RECONOCIDAS NETAS\n(7)", "PAGOS REALIZADOS\n(8)", "3/1"],
                 [None],
                 ["1. GASTOS DE PERSONAL", 22605587, 21643051, 15175740, 15034406, 21733200, 20790212, 14313062, 14040236, 67.1],
                 ["5. FDO. DE CONTINGENCIA Y OTROS IMPREV.", 512019, "-", "-", "-", 901188, "-", "-", "-", "-"],
                 ["    TOTAL FDO. CONTINGENCIA Y OTROS IMPREV.", 512019, "-", "-", "-", 901188, "-", "-", "-", "-"],
                 ["    TOTAL OPERACIONES NO FINANCIERAS", 281404759, 225585624, 170765635, 165324955, 269508959, 210000000,
                  153262135, 149493295, 60.7],
                 ["TOTALES", 462162489, 368546662, 280337134, 274260851, 414114569, 340000000, 250000000, 245000000, 60.7]],
    "ING 002": [[None, "Miles de euros"],
                ["PRESUPUESTO DE INGRESOS\nESTADO DE EJECUCIÓN\nHASTA EL 31 DE AGOSTO", "2026", None, None, "2025", None, None,
                 "% DE REALIZACIÓN"],
                [None, "PREVISIONES PRESUPUESTARIAS\n(1)", "DERECHOS RECONOCIDOS NETOS\n(2)", "RECAUDACIÓN      NETA\n(3)",
                 "PREVISIONES PRESUPUESTARIAS\n(4)", "DERECHOS RECONOCIDOS NETOS\n(5)", "RECAUDACIÓN     NETA\n(6)", "3/2"],
                [None],
                ["1. IMPUESTOS DIRECTOS Y COTIZACIONES SOCIALES", 86428536, 86742505, 81608237, 86428536, 72945860, 70000000, 94.1],
                ["   Impuesto sobre la renta de las personas físicas", 51629206, 60197668, 57002140, 51629206, 49974200, 47000000, 94.7],
                ["   Impuesto sobre el patrimonio", 71585, 82873, 79185, 71585, 88381, 80000, 95.6],
                ["               TOTAL OPERACIONES NO FINANCIERAS", 189005004, 165075815, 153499122, 189005004, 144507567,
                 135020829, 93.0],
                ["9. PASIVOS FINANCIEROS", "-", 132752671, 132752671, "-", 151587988, 151587988, 100.0],
                ["               TOTAL OPERACIONES FINANCIERAS", 3539164, 139335339, 139275525, 3539164, 161525324, 161000000, 99.9]],
    "ING 012": [[None, "Miles de euros"],
                ["PRESUPUESTO DE INGRESOS\nRECAUDACIÓN NETA\nHASTA EL 31 DE AGOSTO", "2026", None, None, None, None,
                 "2025", None, None, None, None, "TASAS VARIACIÓN 5/10"],
                [None, "RECAUDACIÓN TOTAL", None, "RECAUDACIÓN CEDIDA", None, "REC. NETA ESTADO\n(6)",
                 "RECAUDACIÓN TOTAL", None, "RECAUDACIÓN CEDIDA", None, "REC. NETA ESTADO\n(12)", None],
                [None, "APLICADA\n(2)", "PENDIENTE     DE APLICAR\n(3)", "CC.AA.\n(4)", "EE.LL.\n(5)", None,
                 "APLICADA\n(8)", "PENDIENTE     DE APLICAR\n(9)", "CC.AA.\n(10)", "EE.LL.\n(11)", None, None],
                [None],
                ["   Impuesto sobre la renta de las personas físicas", 109985897, -860, 51096715, 990691, 57897631,
                 98000000, -500, 46000000, 900000, 51099500, 13.3],
                ["   Impuesto sobre sociedades", 19102254, -17, "-", "-", 19102237, 16000000, "-", "-", "-", 16000000, 19.4],
                ["               TOTAL OPERACIONES NO FINANCIERAS", 253297559, 1023763, 94981932, 1825799, 157513591,
                 228125300, 1440600, 88372100, 1710800, 139483000, 12.9]],
    "TES 015": [[None, None, None, "Miles de euros"],
                ["DÉFICIT DE CAJA\nHASTA EL 31 DE AGOSTO", "2026\n(1)", "2025\n(2)", "TASAS  VARIACIÓN 1/2"],
                [None],
                ["1.- DÉFICIT (-) O SUPERÁVIT (+) DE CAJA NO FINANCIERO:", -34578494, -30216109, 14.4],
                ["\t\t1.1. COBROS:", 157513591, 139482966, 12.9],
                ["\t\t\tPresupuesto Corriente", 153499122, 135020829, 13.7],
                ["3.- NECESIDAD (-) O CAPACIDAD (+) DE ENDEUDAMIENTO (1+2)", -51926213, -74315341, -30.1]],
    "MRR00 26": [[None, "Miles de euros"],
                 ["MECANISMO DE RECUPERACIÓN Y RESILIENCIA\nSECCIONES\nHASTA EL 31 DE AGOSTO", "CREDITOS PRESUPUESTARIOS",
                  None, None, None, "AUTORIZACIONES\n(5)", "GASTOS COMPROMETIDOS\n(6)", "OBLIGACIONES RECONOCIDAS NETAS\n(7)",
                  "PAGOS REALIZADOS\n(8)", "% DE REALIZACIÓN"],
                 [None, "INICIALES\n(1)", "ADAPTACIÓN A.C.M. PRÓRROGA\n(2)", "MODIFICACIONES\n(3)",
                  "TOTAL AJUSTADO 4=1-2+3\n(4)", None, None, None, None, "7/4"],
                 ["DEFENSA", 170593, "-", -85827, 84766, 78475, 78475, 70000, 65000, 82.6],
                 ["ECONOMÍA, COMERCIO Y EMPRESA", 1168107, "-", 14267050, 15435157, 15434549, 15434549, 15000000, 14000000, 97.2],
                 ["IGUALDAD", "-", "-", "-", "-", "-", "-", "-", "-", "-"],
                 [None, 1338700, "-", 14181223, 15519923, 15513024, 15513024, 15070000, 14065000, 97.1]],
    "TCC 45": [[None, "Miles de euros"],
               ["PRESUPUESTO DE GASTOS\nEJECUCIÓN ART. 45: COMUNIDADES AUTONOMAS\nHASTA EL 31 DE AGOSTO", "2026", None, None,
                "2025", None, None, "% DE REALIZACIÓN"],
               [None, "CRÉDITOS DEFINITIVOS\n(1)", "OBLIGACIONES RECONOCIDAS    NETAS\n(2)", "PAGOS REALIZADOS\n(3)",
                "CRÉDITOS DEFINITIVOS\n(4)", "OBLIGACIONES RECONOCIDAS    NETAS\n(5)", "PAGOS REALIZADOS\n(6)", "2/1"],
               ["Programas de servicios sociales", 204704, 99102, 18373, 204704, 150528, 150528, 48.4],
               ["TOTALES", 40000000, 21500000, 21400000, 38000000, 20000000, 19900000, 53.8]]}
DETAIL_BOOK = workbook({**EXECUTION_SHEETS, **DETAIL_SHEETS})


def test_parse_the_execution_detail():
    d = budget.parse_execution_detail(DETAIL_BOOK)
    assert d["chapters"]["ch1"]["2026"] == {"final": 22605.6, "committed": 21643.1, "obligations": 15175.7, "payments": 15034.4}
    assert d["chapters"]["ch5"]["2026"]["obligations"] == 0.0 and d["chapters"]["nonfinancial"]["2025"]["obligations"] == 153262.1
    assert set(d["chapters"]) == {"ch1", "ch5", "nonfinancial", "total"}      # subtotals and "% realised" are left out
    assert d["revenue"]["irpf"]["2026"] == {"forecast": 51629.2, "rights": 60197.7, "collected": 57002.1}
    assert "ch9" in d["revenue"] and d["revenue"]["nonfinancial"]["2025"]["collected"] == 135020.8
    assert d["taxes"]["irpf"]["2026"] == {"applied": 109985.9, "pending": -0.9, "regions": 51096.7, "local": 990.7, "state": 57897.6}
    assert d["taxes"]["corporate"]["2026"]["regions"] == 0.0 and d["taxes"]["nonfinancial"]["2025"]["state"] == 139483.0
    assert d["cash"] == {"deficit": {"2026": {"value": -34578.5}, "2025": {"value": -30216.1}},
                         "receipts": {"2026": {"value": 157513.6}, "2025": {"value": 139483.0}},
                         "borrowing": {"2026": {"value": -51926.2}, "2025": {"value": -74315.3}}}
    assert d["mrr"]["ministries"] == {"Defence": {"credits": 84.8, "committed": 78.5, "obligations": 70.0, "payments": 65.0},
                                      "Economy, trade and business": {"credits": 15435.2, "committed": 15434.5,
                                                                      "obligations": 15000.0, "payments": 14000.0}}
    assert d["mrr"]["total"]["obligations"] == 15070.0
    assert d["transfers"] == {"regions_current": {"2026": {"final": 40000.0, "obligations": 21500.0, "payments": 21400.0},
                                                  "2025": {"final": 38000.0, "obligations": 20000.0, "payments": 19900.0}}}
    summary = budget.month_summary(d, 2026)
    assert summary["chapters"]["nonfinancial"] == [281404.8, 170765.6, 269509.0, 153262.1] and "policies" not in summary
    policies = budget.parse_execution(DETAIL_BOOK)["policies"]
    assert budget.month_summary(d, 2026, policies)["policies"]["defence"] == [21669.3, 7884.0]
    assert {k: summary[k] for k in budget.MONTH_KEYS} == {"spending": 170765.6, "spending_prev": 153262.1, "revenue": 165075.8,
                                             "revenue_prev": 144507.6, "cash": -34578.5, "cash_prev": -30216.1,
                                             "borrowing": -51926.2, "borrowing_prev": -74315.3, "mrr": 15070.0}


def test_the_execution_detail_for_the_page():
    page = budget.detail_for_page(budget.parse_execution_detail(DETAIL_BOOK), 2026)
    irpf = next(r for r in page["revenue"] if r["code"] == "irpf")
    assert irpf["indent"] == 1 and irpf["rights_prev"] == 49974.2 and irpf["collected_prev"] == 47000.0
    assert [r["code"] for r in page["revenue"]] == ["ch1", "irpf", "nonfinancial", "ch9"]
    tax = page["taxes"][0]
    assert (tax["code"], tax["collected"], tax["regions"], tax["state"], tax["collected_prev"]) == \
        ("irpf", 109985.0, 51096.7, 57897.6, 97999.5)
    assert page["taxes"][-1]["code"] == "nonfinancial"
    assert page["cash"]["deficit"] == {"label": "Cash balance", "value": -34578.5, "prev": -30216.1}
    assert [r["label"] for r in page["mrr"]["rows"]] == ["Economy, trade and business", "Defence"]     # largest first
    assert page["transfers"] == [{"code": "regions_current", "label": "To the regions, current", "final": 40000.0,
                                  "obligations": 21500.0, "obligations_prev": 20000.0}]
    assert budget.detail_for_page({}, 2026)["mrr"] is None


def test_each_months_totals_are_kept(monkeypatch):
    sepg = '<a href="/sitios/sepg/es-ES/x/Documents/2025-P/01%20Presupuestos%20Generales%20del%20Estado%20Consolidados.xlsx">'
    igae = "".join(f'<a href="/sitios/igae/x/Documents/MENSUAL%20{m}%202026.xlsx">' for m in ("AGOSTO", "JULIO", "JUNIO", "MAYO"))
    asked = []

    class Reply:
        def __init__(self, url):
            asked.append(url.rsplit("/", 1)[-1])
            self.text = sepg if "Estadisticas.aspx" in url else igae
            self.content = DETAIL_BOOK if "MENSUAL" in url else BUDGET_BOOK

    monkeypatch.setattr(budget.http, "get", lambda url, **_: Reply(url))
    kept = {"spending": 1.0, "policies": {}}
    sb = budget.refresh_state_budget({"months": {"2026": {"6": kept, "5": {"spending": 2.0}}}})
    assert "MENSUAL%20JULIO%202026.xlsx" in asked and "MENSUAL%20JUNIO%202026.xlsx" not in asked     # June was kept
    assert "MENSUAL%20MAYO%202026.xlsx" in asked                                # May was kept before the pace: read again
    assert sorted(sb["months"]["2026"], key=int) == ["5", "6", "7", "8"] and sb["months"]["2026"]["6"] == kept
    assert sb["months"]["2026"]["5"]["policies"]["defence"] == [21669.3, 7884.0]
    assert sb["months"]["2025"]["12"]["spending"] == 153262.1                   # the December file, read for its own year
    assert sb["execution"]["2026"]["detail"]["cash"]["deficit"]["2026"]["value"] == -34578.5
    page = budget.state_budget_data({"state_budget": sb}, {})
    assert page["months"]["2026"]["spending"][4:9] == [170765.6, 1.0, 170765.6, 170765.6, None]
    assert page["execution"][0]["detail"]["taxes"][0]["code"] == "irpf"
    defence = page["pace"]["2026"]["policies"]["defence"]
    assert defence["final"][4:8] == [21669.3, None, 21669.3, 21669.3] and defence["obligations"][7] == 7884.0
    assert page["pace"]["2025"]["chapters"]["nonfinancial"]["obligations"][4:8] == [153262.1, None, 153262.1, 153262.1]
    assert page["pace_items"]["chapters"][0] == {"code": "ch1", "label": "Pay of staff"}


def test_the_pace_of_spending():
    months = {"2026": {"1": {"policies": {"defence": [12062.2, 473.6]}, "chapters": {"ch6": [19000.0, 300.0, 18000.0, 250.0]}},
                       "2": {"policies": {"defence": [12766.2, 1481.0]}, "chapters": {"ch6": [19100.0, 900.0, 18100.0, None]}}},
              "2025": {"12": {"policies": {"defence": [17465.0, 17267.8]}, "chapters": {"ch6": [18500.0, 16500.0, 17000.0, 15000.0]}}}}
    pace = budget.pace_for_page(months)
    assert sorted(pace) == ["2024", "2025", "2026"]
    assert pace["2026"]["policies"]["defence"]["obligations"][:3] == [473.6, 1481.0, None]
    assert pace["2026"]["policies"]["defence"]["final"][:2] == [12062.2, 12766.2]
    # 2025's chapters: January from the 2026 workbook's year-earlier columns (February's is missing), December its own.
    assert pace["2025"]["chapters"]["ch6"]["obligations"] == [250.0] + [None] * 10 + [16500.0]
    assert pace["2025"]["policies"]["defence"]["final"][11] == 17465.0
    assert pace["2024"]["chapters"]["ch6"]["obligations"][11] == 15000.0 and pace["2024"]["policies"] == {}
