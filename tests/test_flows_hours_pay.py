"""Batch 25d: worker flows, hours, vacancies and pay by activity, and dismissals and temporary layoffs (no network)."""

import io
from pathlib import Path

import numpy as np
import openpyxl
import pandas as pd
import pytest

from econpulse import http, workstats
from econpulse.pages import build_page, page_indicator_ids
from econpulse.registry import load_registry
from econpulse.sources import reg
from econpulse.store import Store
from econpulse.tables import Data


def reg_workbook(total: float) -> bytes:
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "REG-R1"
    for row in (["REGULACIÓN DE EMPLEO", "REG"], ["Agosto 2026 (*)"], ["EMPRESAS (1)", 178, 21, 13.4],
                ["TRABAJADORES AFECTADOS (3)", total, -485, -12.2], ["Varones", 2107], ["Despidos colectivos", 1947],
                ["Suspensión de contrato", total - 1947 - 241], ["Reducción de jornada", 241],
                ["Despidos colectivos", 9999]):          # a later table repeating a label: the first one counts
        ws.append(row)
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def test_reg_links_and_totals():
    base = "https://www.mites.gob.es/estadisticas/reg/"
    html = " ".join(f'<a href="{base}{path}">x</a>' for path in (
        "reg26ago/reg_08_2026.xlsx", "reg25ene/reg_1_2025.xlsx", "reg24ene_dic/reg_1_12_2024.xlsx",
        "reg25/reg_anual_2025.xlsx", "reg22ago/reg_08_2022.xls", "reg22nov/reg_11_2022.xlsx"))
    links = reg.workbook_links(html)
    assert sorted(links) == [pd.Timestamp("2025-01-01"), pd.Timestamp("2026-08-01")]   # monthly, from 2023
    totals = reg.parse_totals(reg_workbook(3479.0))
    assert totals == {"total": 3479.0, "dismissals": 1947.0, "suspensions": 1291.0, "reductions": 241.0}


def test_reg_fetch_reads_only_recent_months(monkeypatch):
    months = pd.date_range("2025-01-01", "2026-08-01", freq="MS")
    monkeypatch.setattr(reg, "_links", lambda: {m: f"u{m:%Y%m}" for m in months})
    asked = []
    monkeypatch.setattr(reg, "_totals", lambda url: asked.append(url) or {"total": 10.0, "dismissals": 4.0})
    assert len(reg.fetch("total").series) == 20
    asked.clear()
    s = reg.fetch("reductions", since=pd.Timestamp("2026-06-01")).series
    assert asked == ["u202606", "u202607", "u202608"] and s.tolist() == [0.0, 0.0, 0.0]   # not listed: none
    with pytest.raises(ValueError):
        reg.fetch("hires")


def test_missing_intermediate_is_added_for_its_host_only(monkeypatch):
    bundle = Path(http.ca_bundle(http.INTERMEDIATES["www.mites.gob.es"])).read_text(encoding="ascii")
    assert bundle.count("BEGIN CERTIFICATE") > 100 and "AC Componentes Informaticos" in bundle
    seen = {}

    class Session:
        def get(self, url, **kwargs):
            seen[url] = kwargs

            class R:
                def raise_for_status(self):
                    pass
            return R()

    monkeypatch.setattr(http, "session", lambda: Session())
    http.get("https://www.mites.gob.es/x")
    http.get("https://ec.europa.eu/y")
    assert seen["https://www.mites.gob.es/x"]["verify"].endswith(".pem")
    assert "verify" not in seen["https://ec.europa.eu/y"]                 # the usual roots


def quarterly_store(tmp_path) -> Store:
    store = Store(tmp_path / "data")
    q = pd.date_range("2015-01-01", "2026-04-01", freq="QS")
    n = len(q)
    store.save_series("hours_sick", pd.Series(np.linspace(5.0, 8.0, n), index=q))
    store.save_series("hours_etcl", pd.Series(128.0, index=q))
    for slug, _ in workstats.SECTIONS:
        store.save_series(f"pay_{slug}", pd.Series(1500.0 + 100 * len(slug) + np.arange(n), index=q))
        store.save_series(f"hours_{slug}", pd.Series(120.0 + len(slug), index=q))
        if slug not in workstats.NO_VACANCIES:
            store.save_series(f"vacancies_{slug}", pd.Series(5.0 + len(slug), index=q))
    store.save_series("wage_cost", pd.Series(2400.0, index=q))
    store.save_series("vacancies", pd.Series(150.0, index=q))
    m = pd.date_range("2023-01-01", "2026-08-01", freq="MS").delete(11)        # no December 2023
    for ind_id, v in (("ere_total", 9.0), ("ere_dismissals", 3.0), ("ere_suspensions", 5.5), ("ere_reductions", 0.5)):
        store.save_series(ind_id, pd.Series(v, index=m))
    return store


def test_callouts_and_facts(tmp_path):
    data = Data(load_registry(), quarterly_store(tmp_path))
    text = workstats.hours_callout(data)
    assert text.startswith("Sick leave took 7.9 hours a month per employee in the four quarters to Q2 2026")
    assert "in 2019" in text and "of the hours worked" in text
    assert "ranged from" in workstats.pay_callout(data)
    facts = workstats.ere_facts(data)
    assert facts[0] == {"label": "Workers affected", "value": "108.0k", "sub": "12 months to Aug 2026, 0% on a year earlier"}
    assert [f["label"] for f in facts][1:] == ["Collective dismissals", "Contract suspensions", "Cuts in hours"]
    assert len(workstats.items("vacancies", "avg_1y")) == len(workstats.SECTIONS) - 4


def test_labour_and_wages_blocks(tmp_path):
    store = quarterly_store(tmp_path)
    q = pd.date_range("2010-04-01", "2026-04-01", freq="QS")
    for ind_id in ("flow_une_emp", "flow_une_inac", "flow_emp_une", "flow_emp_inac", "flow_inac_emp"):
        store.save_series(ind_id, pd.Series(10.0, index=q))
    labour = build_page("labour", load_registry(), store)
    ids = [b["id"] for b in labour["blocks"]]
    assert ids.index("flows") < ids.index("hours") < ids.index("vacancies-sectors") < ids.index("layoffs")
    charts = {c["id"]: c for c in labour["charts"]}
    assert charts["hours-sectors"]["kind"] == "hbar" and len(charts["vacancies-ranking"]["series"][0]["x"]) == 14
    assert charts["layoffs-12m"]["series"][0]["x"][0] == "2024-12-01"        # the first full 12 months after the gap
    wages = build_page("wages", load_registry(), store)
    pay = next(b for b in wages["blocks"] if b["id"] == "pay-sectors")
    assert pay["tables"][0]["rows"][0]["cells"][0] == "€2,400"
    assert {"pay-ranking", "pay-growth-ranking"} <= {c["id"] for c in wages["charts"]}


def test_every_series_is_registered():
    registered = {i.id for i in load_registry()}
    assert (page_indicator_ids("labour") | page_indicator_ids("wages")) - registered == set()
    hours = next(i for i in load_registry() if i.id == "hours_per_person")
    assert hours.params == {"a": "hours_na", "b": "persons_na", "scale": 76.923}
