"""Batch 12b: forecasts read automatically (IMF, Banco de España, FUNCAS) and the AI check (no network)."""

from datetime import date

import pandas as pd
import pytest

from econpulse import forecasts
from econpulse.registry import load_registry
from econpulse.sources import bdeproj, funcas, imf
from econpulse.sources.webtables import number, read_tables
from econpulse.store import Store
from econpulse.tables import Data

IMF_XML = """<?xml version='1.0' encoding='UTF-8'?>
<message:StructureSpecificData xmlns:message="http://www.sdmx.org/resources/sdmxml/schemas/v2_1/message">
<message:DataSet PUBLICATION_DATE="2026-10-13T02:00:00Z">
<Series COUNTRY="ESP" INDICATOR="NGDP_RPCH" FREQUENCY="A">
<Obs TIME_PERIOD="2025" OBS_VALUE="2.592062"/><Obs TIME_PERIOD="2026" OBS_VALUE="2.513334"/>
<Obs TIME_PERIOD="2027" OBS_VALUE="1.796988"/>
</Series></message:DataSet></message:StructureSpecificData>"""

BDE_INDEX = """<a href="/wbe/en/publicaciones/analisis-economico-investigacion/proyecciones-macro-informe-trimestral/
proyecciones-e-informe-trimestral-de-la-economia-espanola-tercer-trimestre-2026.html">Q3</a>""".replace("\n", "")

BDE_REPORT = """<div class="block-entry-content__info"><p>09/10/2026</p></div>
<table><thead>
<tr><th>Annual rate of change in volume terms (%) and % of GDP</th><th></th><th></th><th></th><th></th><th></th></tr>
<tr><th></th><th></th><th colspan="2">2026 Q3<br />projections</th><th colspan="2">Difference with June</th></tr>
<tr><th></th><th>2025</th><th>2026</th><th>2027</th><th>2026</th><th>2027</th></tr></thead>
<tbody>
<tr><td>GDP</td><td>2.6</td><td>2.6</td><td>2.2</td><td>0.3</td><td>0.5</td></tr>
<tr><td>HICP</td><td>2.7</td><td>3.9</td><td>3.7</td><td>0.3</td><td>1.1</td></tr>
<tr><td>HICP excluding energy and food</td><td>2.6</td><td>3.4</td><td>3.5</td><td>0.2</td><td>0.3</td></tr>
<tr><td>Unemployment rate (% of labour force). Annual average</td><td>10.5</td><td>10.0</td><td>9.7</td><td>0.0</td><td>-0.1</td></tr>
<tr><td>General government net lending (+) / net borrowing (-) (% of GDP)</td><td>-2.4</td><td>-2.6</td><td>-2.2</td><td>-0.2</td><td>0.1</td></tr>
</tbody></table>"""

FUNCAS_HTML = """
<table>
<tr><td></td><th colspan="2">PIB</th><th colspan="2">Consumo<br /> hogares</th></tr>
<tr><td></td><td>2026</td><td>2027</td><td>2026</td><td>2027</td></tr>
<tr><td>BBVA Research</td><td>2,4</td><td>2,1</td><td>2,8</td><td>2,0</td></tr>
<tr><td>CONSENSO (MEDIA)</td><td>2,5</td><td>2,0</td><td>2,8</td><td>2,1</td></tr>
<tr><td>Máximo</td><td>2,7</td><td>2,2</td><td>3,0</td><td>2,3</td></tr>
<tr><td>Mínimo</td><td>2,2</td><td>1,8</td><td>2,6</td><td>1,8</td></tr>
<tr><td>Gobierno (junio 2026)</td><td>2,6</td><td>2,2</td><td>&#8212;</td><td>&#8212;</td></tr>
</table>
<table>
<tr><td></td><th colspan="2">IPC general<br /> (media anual)</th><th colspan="2">Tasa de<br /> desempleo</th><th colspan="2">Saldo AA.PP.<br /> (% del PIB)</th></tr>
<tr><td></td><td>2026</td><td>2027</td><td>2026</td><td>2027</td><td>2026</td><td>2027</td></tr>
<tr><td>CONSENSO (MEDIA)</td><td>3,4</td><td>2,5</td><td>9,9</td><td>9,6</td><td>-2,5</td><td>-2,3</td></tr>
<tr><td>AIReF (julio 2026)</td><td>3,3</td><td>2,4</td><td>10,2</td><td>10,1</td><td>-2,6</td><td>&#8212;</td></tr>
</table>"""

# The PDF's two tables as pdfplumber's text gives them: a label, then figures in column order.
PDF_PAGE_A = """Cuadro 1. Panel de previsiones para España
PIB Consumo hogares Consumo público Formación bruta de capital fijo
2026 2027 2026 2027 2026 2027 2026 2027 2026 2027 2026 2027 2026 2027 2026 2027 2026 2027
CONSENSO (MEDIA) 2,3 2,0 2,6 2,0 1,9 1,7 4,2 3,1 3,5 2,8 4,4 3,0 2,7 2,1 1,7 2,5 3,0 3,2
Máximo 2,7 2,2 2,9 2,3 3,5 2,6 6,3 5,5 6,5 6,9 6,0 4,9 3,0 2,7 3,5 3,3 5,3 5,1
Gobierno (junio 2026) 2,6 2,2 -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --"""
PDF_PAGE_B = """IPC general Tasa de desempleo Saldo AA.PP.
2026 2027 2026 2027 2026 2027 2026 2027 2026 2027 2026 2027 2026 2027
CONSENSO (MEDIA) 3,2 2,3 2,7 2,5 3,3 3,1 2,0 1,5 10,0 9,6 2,2 2,0 -2,5 -2,4
AIReF (mayo 2026) 3,2 2,3 -- -- 3,1 3,2 2,3 [6] 1,9 [6] 10,2 10,1 -- -- -2,6 -2,2"""


def test_table_reader_and_numbers():
    rows = read_tables('<table><tr><th colspan="2">PIB</th><td>x<br/>y</td></tr></table>')[0]
    assert rows == [["PIB", "PIB", "x y"]]
    assert [number(t) for t in ("2,6", "-2.4", "3,6 [3]", "−0,5", "—", "--", "", "n.d.")] == \
        [2.6, -2.4, 3.6, -0.5, None, None, None, None]


def test_imf_series_and_publication_date():
    r = imf.parse(IMF_XML)
    assert r.meta == {"published": "2026-10-13"}
    assert r.series[pd.Timestamp("2026-01-01")] == pytest.approx(2.513334)
    assert imf.source_url("IMF.RES,WEO/ESP.NGDP_RPCH.A") == "https://data.imf.org/en/datasets/IMF.RES:WEO"


def test_bde_newest_report_and_projections_table():
    assert bdeproj.newest_report(BDE_INDEX).endswith("tercer-trimestre-2026.html")
    rows, published = bdeproj.parse_report(BDE_REPORT)
    assert published == date(2026, 10, 9)
    assert rows["GDP"] == {2025: 2.6, 2026: 2.6, 2027: 2.2}  # the revision columns are left out
    assert rows["HICP"] == {2025: 2.7, 2026: 3.9, 2027: 3.7}
    assert rows["Unemployment rate"][2027] == 9.7 and rows["General government net lending"][2026] == -2.6
    with pytest.raises(ValueError):
        bdeproj.parse_report("<table><tr><td>No projections</td></tr></table>")


def test_funcas_html_tables():
    rows = funcas.parse_html(FUNCAS_HTML)
    assert set(rows) == {"consensus", "max", "min", "government", "airef"}  # not the individual panelists
    assert rows["consensus"]["values"] == {"gdp": {2026: 2.5, 2027: 2.0}, "inflation": {2026: 3.4, 2027: 2.5},
                                           "unemployment": {2026: 9.9, 2027: 9.6}, "balance": {2026: -2.5, 2027: -2.3}}
    assert rows["government"]["values"] == {"gdp": {2026: 2.6, 2027: 2.2}}
    assert rows["airef"]["values"]["balance"] == {2026: -2.6}  # a dash is "not published"
    assert funcas.label_month(rows["airef"]["label"]) == date(2026, 7, 1)


def test_funcas_pdf_text():
    rows = funcas.parse_pdf_text([PDF_PAGE_A, PDF_PAGE_B, "Cuadro 2. Previsiones trimestrales"])
    assert rows["consensus"]["values"]["gdp"] == {2026: 2.3, 2027: 2.0}
    assert rows["consensus"]["values"]["unemployment"] == {2026: 10.0, 2027: 9.6}
    assert rows["consensus"]["values"]["balance"] == {2026: -2.5, 2027: -2.4}
    assert rows["airef"]["values"]["unemployment"] == {2026: 10.2, 2027: 10.1}  # footnote marks skipped
    assert rows["government"]["values"] == {"gdp": {2026: 2.6, 2027: 2.2}}
    with pytest.raises(ValueError):  # a row that doesn't fit the expected layout stops the read
        funcas.parse_pdf_text([PDF_PAGE_B.replace("10,0 9,6", "10,0")])


def automatic_store(tmp_path, gdp_2027=2.2):
    store = Store(tmp_path / "data")
    years = pd.to_datetime(["2025-01-01", "2026-01-01", "2027-01-01"])
    store.save_series("fc_bde_gdp", pd.Series([2.6, 2.6, gdp_2027], index=years))
    store.save_series("fc_bde_inflation", pd.Series([2.7, 3.9, 3.7], index=years))
    store.save_series("fc_funcas_gdp", pd.Series([2.5, 2.0], index=years[1:]))
    store.save_series("fc_funcas_gdp_min", pd.Series([2.2, 1.8], index=years[1:]))
    store.save_series("fc_funcas_gdp_max", pd.Series([2.7, 2.2], index=years[1:]))
    catalog = {"fc_bde_gdp": {"published": "2026-10-09", "url": "https://www.bde.es/report.html"},
               "fc_funcas_gdp": {"published": "2026-09-16"}, "fc_funcas_gdp_min": {"published": "2026-09-16"},
               "fc_funcas_gdp_max": {"published": "2026-09-16"}}
    store.save_catalog(catalog)
    return store


@pytest.fixture
def no_hand(tmp_path, monkeypatch):
    path = tmp_path / "forecasts.yaml"
    path.write_text("forecasters: []\n", encoding="utf-8")
    monkeypatch.setattr(forecasts, "FORECASTS_FILE", path)
    return path


def test_automatic_figures_await_an_ai_check(tmp_path, no_hand):
    store = automatic_store(tmp_path)
    data = Data(load_registry(), store)
    by_id = {f.id: f for f in forecasts.forecasters(data)}
    bde = by_id["bde"]
    assert bde.status == forecasts.PENDING and bde.published == date(2026, 10, 9) and bde.url.endswith("report.html")
    assert by_id["funcas"].low[2026]["gdp"] == 2.2 and by_id["funcas"].high[2027]["gdp"] == 2.2
    t = forecasts.forecast_table(data, 2026)
    rows = {r["label"]: r for r in t["rows"]}
    assert rows["Banco de España"]["period_note"] == "Oct 2026"
    assert rows["Banco de España"]["flag"] == "awaiting AI check"
    assert rows["Range of the panel"]["cells"][0] == "2.2% to 2.7%"
    assert rows["Average of the forecasts above"]["cells"][0] == "–"  # nothing checked yet
    assert forecasts.forecast_chart(data, today=date(2026, 10, 31)) is None

    record = forecasts.confirm(data, "bde", by="AI check (test)", note="Checked against the report table.")
    assert record["fingerprint"] == forecasts.fingerprint(bde) and record["values"]["2026"]["gdp"] == 2.6
    assert "2025" not in record["values"]  # only the edition's own year on
    data = Data(load_registry(), store)
    bde = {f.id: f for f in forecasts.forecasters(data)}["bde"]
    assert bde.status == forecasts.CHECKED and bde.counts and bde.note == "Checked against the report table."
    rows = {r["label"]: r for r in forecasts.forecast_table(data, 2026)["rows"]}
    assert rows["Banco de España"]["flag"] == ""
    assert rows["Average of the forecasts above"]["cells"][0] == "2.6%"  # BdE only: FUNCAS still unchecked
    assert rows["Average of the forecasts above"]["period_note"] == "AI-checked rows only"


def test_a_new_edition_needs_a_new_check(tmp_path, no_hand):
    store = automatic_store(tmp_path)
    forecasts.confirm(Data(load_registry(), store), "bde", by="test")
    store.save_series("fc_bde_gdp", pd.Series([2.6, 2.6, 2.0], index=pd.to_datetime(["2025-01-01", "2026-01-01", "2027-01-01"])))
    bde = {f.id: f for f in forecasts.forecasters(Data(load_registry(), store))}["bde"]
    assert bde.status == forecasts.PENDING  # the figures changed, so the old check no longer applies


def test_range_only_from_the_consensus_edition(tmp_path, no_hand):
    store = automatic_store(tmp_path)
    catalog = store.load_catalog()
    catalog["fc_funcas_gdp_max"]["published"] = "2026-07-13"  # left over from an older panel
    store.save_catalog(catalog)
    funcas_row = {f.id: f for f in forecasts.forecasters(Data(load_registry(), store))}["funcas"]
    assert funcas_row.low == {} and funcas_row.high == {}


def test_a_newer_hand_entry_overrides(tmp_path, monkeypatch):
    path = tmp_path / "forecasts.yaml"
    path.write_text("""forecasters:
  - {id: bde, name: Banco de España, group: spain, published: 2026-12-15, values: {2026: {gdp: 2.7}}}
  - {id: imf, name: IMF, group: international, published: 2026-04-14, values: {2026: {gdp: 2.1}}}
""", encoding="utf-8")
    monkeypatch.setattr(forecasts, "FORECASTS_FILE", path)
    store = automatic_store(tmp_path)
    data = Data(load_registry(), store)
    by_id = {f.id: f for f in forecasts.forecasters(data)}
    assert by_id["bde"].status == forecasts.HAND and by_id["bde"].value(2026, "gdp") == 2.7  # December beats October
    assert by_id["imf"].status == forecasts.HAND  # no automatic IMF figures in this store, so the hand entry shows
    with pytest.raises(ValueError):
        forecasts.confirm(data, "bde", by="test")  # hand entries need no check
