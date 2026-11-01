"""Batch 25a: jobs, unemployment and contracts by sector on the Labour page (no network)."""

import io

import numpy as np
import openpyxl
import pandas as pd
import pytest

from econpulse.pages import build_page
from econpulse.registry import load_registry
from econpulse.sources import afiliacion
from econpulse.store import Store
from econpulse.tables import AvgChange, Data, Row, Table, build_table


def workbook(sheet: str, rows: list) -> bytes:
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = sheet
    ws.append(["PERIODO", "Sector", "SALDOS", "SALDOS_EST", "SALDOS_PROME", "Desestacionalizado", "SALDOS_CUI"])
    for r in rows:
        ws.append(r)
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def test_reads_the_yearly_workbooks():
    content = workbook("Afiliados_deset", [
        ["202401", "Agricultura, ganadería y pesca", 1000.0, None, None, 990.0, 0],
        ["202401", "Total", 21000.0, None, None, 21100.0, 0],
        ["202402", "Total", 21050.0, None, None, 21150.0, 0],
        ["Nota", None, None, None, None, None, None],
    ])
    table = afiliacion.parse_table(content)
    assert list(table["group"].unique()) == ["agricultura, ganaderia y pesca", "total"]   # accents dropped
    assert table[table["group"] == "total"]["desestacionalizado"].tolist() == [21100.0, 21150.0]
    html = ('<a href="/wps/wcm/connect/x/Afiliaci%C3%B3n+2025.xlsx?MOD=AJPERES">2025</a>'
            '<a href="/wps/wcm/connect/y/Afiliaci%C3%B3n+2026_CNAE25.xlsx">2026</a>'
            '<a href="/wps/wcm/connect/z/19_Serie+afiliaci%C3%B3n+media+por+reg%C3%ADmenes.xlsx">serie</a>')
    links = afiliacion.workbook_links(html)
    assert sorted(links) == [2025, 2026] and links[2026].startswith("https://www.seg-social.es/")


def test_fetch_joins_the_years_and_asks_only_for_recent_ones(monkeypatch):
    tables = {
        2025: afiliacion.parse_table(workbook("Afiliados_deset", [["202512", "Industria", 2500.0, None, None, 2510.0, 0]])),
        2026: afiliacion.parse_table(workbook("Tabla_desestacionalizados", [["202601", "Industria", 2490.0, None, None, 2515.0, 0]])),
    }
    monkeypatch.setattr(afiliacion, "_links", lambda: {2025: "u2025", 2026: "u2026"})
    asked = []
    monkeypatch.setattr(afiliacion, "_table", lambda url: asked.append(url) or tables[int(url[1:])])
    sa = afiliacion.fetch("sa:industry").series
    assert sa.tolist() == [2510.0, 2515.0] and asked == ["u2025", "u2026"]
    asked.clear()
    afiliacion.fetch("raw:industry", since=pd.Timestamp("2026-02-01"))
    assert asked == ["u2026"]
    with pytest.raises(ValueError):
        afiliacion.fetch("raw:mining")


def test_published_adjusted_twin_for_short_horizons(tmp_path):
    store = Store(tmp_path / "data")
    m = pd.date_range("2024-01-01", "2026-09-01", freq="MS")
    raw = pd.Series(1000.0 + 10 * np.arange(len(m)) + np.where(m.month == 9, 50, 0), index=m)   # a September bump
    store.save_series("reg_industry", raw)
    store.save_series("reg_industry_sa", pd.Series(1000.0 + 10 * np.arange(len(m)), index=m))
    data = Data(load_registry(), store)
    t = build_table(Table(title="t", caption="c", columns=[AvgChange("1-mo", 1), AvgChange("12-mo", 12)],
                          rows=[Row("reg_industry", "Industry", sa="reg_industry_sa")]), data)
    one, twelve = t["rows"][0]["cells"]
    assert one == "10.0"          # the adjusted twin: no September bump
    assert twelve == "10.0"       # the published series: September on September


def test_labour_page_blocks(tmp_path):
    store = Store(tmp_path / "data")
    m = pd.date_range("2018-01-01", "2026-09-01", freq="MS")
    for ind_id in ("reg_sector_total", "reg_services", "reg_industry", "reg_construction", "paro_registrado", "paro_services"):
        store.save_series(ind_id, pd.Series(1000.0 + np.arange(len(m)), index=m))
        if ind_id.startswith("reg_"):
            store.save_series(ind_id + "_sa", pd.Series(1000.0 + np.arange(len(m)), index=m))
    store.save_series("contracts_total", pd.Series(1500.0, index=m))
    store.save_series("contracts_permanent", pd.Series(600.0, index=m))
    store.save_series("contracts_permanent_share", pd.Series(40.0, index=m))
    page = build_page("labour", load_registry(), store)
    ids = [b["id"] for b in page["blocks"]]
    assert ids.index("registrations") < ids.index("sectors") < ids.index("unemployment-sectors") < ids.index("contracts")
    sectors = next(b for b in page["blocks"] if b["id"] == "sectors")
    total = next(r for r in sectors["tables"][0]["rows"] if r.get("label") == "All registrations")
    assert total["cells"] == ["1.0", "1.0", "1.0"]
    assert {c["id"] for c in page["charts"]} >= {"sector-jobs-change", "sector-jobs-yoy", "contracts-share"}


def divisions_workbook(sheet: str, code_header: str, rows: list) -> bytes:
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = sheet
    ws.append(["PERIODO", code_header, "DesRegimen", "Descripcion_Sexo", "SALDOS"])
    for r in rows:
        ws.append(r)
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def test_divisions_table_and_codes():
    content = divisions_workbook("Tabla_2", "CNAE_25", [
        ["202601", "1", "REGIMEN GENERAL", "Mujer", 10.0], ["202601", "01", "REG. ESP. AUTONOMOS", "Varón", 5.0],
        ["202601", "86", "REGIMEN GENERAL", "Mujer", 7.0], ["Total", None, None, None, None]])
    df = afiliacion.parse_divisions(content)
    assert df.set_index("code")["value"].to_dict() == {"01": 15.0, "86": 7.0}     # summed over schemes and sexes
    assert afiliacion.divisions("10-12,86") == {"10", "11", "12", "86"} and afiliacion.divisions("all") is None


def test_classification_bridge(monkeypatch):
    # Division 95 gains 200 at the change on top of its usual January dip (-1); trade loses them.
    months = pd.date_range("2024-11-01", "2026-03-01", freq="MS")
    rows = []
    for d in months:
        after = d >= pd.Timestamp("2026-01-01")
        jan = -1.0 if d.month == 1 else 0.0
        rows.append((d, "95", 100.0 + jan + (200.0 if after else 0.0)))
        rows.append((d, "47", 1000.0 + jan * 10 - (200.0 if after else 0.0)))
    table = pd.DataFrame(rows, columns=["date", "code", "value"])
    monkeypatch.setattr(afiliacion, "_links", lambda: {2024: "a", 2025: "b", 2026: "c"})
    year_of = {"a": 2024, "b": 2025, "c": 2026}
    monkeypatch.setattr(afiliacion, "_divisions_table", lambda url: table[table["date"].dt.year == year_of[url]])
    raw = afiliacion.fetch("cnae:45-47").series
    linked = afiliacion.fetch("cnae:45-47", {"bridge": "-95"}).series
    assert afiliacion.moved(table[table.code == "95"].groupby("date")["value"].sum()) == pytest.approx(200.0)
    assert raw[pd.Timestamp("2025-12-01")] - raw[pd.Timestamp("2026-02-01")] == pytest.approx(200.0)
    assert linked[pd.Timestamp("2025-12-01")] == pytest.approx(linked[pd.Timestamp("2026-02-01")])   # no jump
    assert linked[pd.Timestamp("2026-02-01")] == raw[pd.Timestamp("2026-02-01")]                       # 2026 as published


def test_industry_detail_page(tmp_path):
    from econpulse import industries
    from econpulse.build import build_site
    store = Store(tmp_path / "data")
    m = pd.date_range("2021-01-01", "2026-09-01", freq="MS")
    trend = 1000.0 + np.arange(len(m)) + 5 * np.sin(np.arange(len(m)) * 2 * np.pi / 12)
    for gid in ("total", "manufacturing", "hospitality"):
        store.save_series(industries.indicator_id(gid), pd.Series(trend, index=m))
    data = Data(load_registry(), store)
    page = industries.page(data)
    assert {c["id"] for c in page["charts"]} == {"ind-total", "ind-manufacturing", "ind-hospitality"}
    chart = next(c for c in page["charts"] if c["id"] == "ind-total")
    assert [s["name"] for s in chart["series"]] == ["Monthly change", "3-month average"]
    assert chart["series"][0]["x"][0] == "2023-01-01"
    row = next(r for r in page["table"]["rows"] if not r["heading"] and r["label"].startswith("All registrations"))
    assert row["cells"][0] == "1,063.7k"           # 1,068 plus the seasonal term in September
    every = {g[0] for g in industries.groups()}
    assert {i.id for i in load_registry() if i.id.startswith("ind_")} >= {industries.indicator_id(g) for g in every}
    build_site(load_registry(), store, site_dir=tmp_path / "site")
    labour = (tmp_path / "site" / "labour.html").read_text(encoding="utf-8")
    assert 'href="industry-detail.html">Every industry</a>' in labour        # in the Labour tab's menu
    detail = (tmp_path / "site" / "industry-detail.html").read_text(encoding="utf-8")
    assert 'id="fig-ind-manufacturing"' in detail and 'aria-current="page">Labour market</a>' in detail
