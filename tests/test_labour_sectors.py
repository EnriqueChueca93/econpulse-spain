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
