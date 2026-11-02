"""Batch 29a: the Pensions page and the Ministry of Labour's bulletin tables (no network)."""

import numpy as np
import pandas as pd

from econpulse import pensions
from econpulse.build import NAV, SECTION_PAGES
from econpulse.pages import build_page, page_indicator_ids
from econpulse.registry import load_registry
from econpulse.sources import bel
from econpulse.store import Store
from econpulse.tables import Data


class FakeSheet:
    """Rows as a BEL pension table lays them out: years, a year-to-date row, then months under year markers."""

    def __init__(self, rows):
        self.rows = rows
        self.nrows, self.ncols = len(rows), max(len(r) for r in rows)

    def cell_value(self, r, c):
        row = self.rows[r]
        return row[c] if c < len(row) else ""


class FakeBook:
    def __init__(self, *sheets):
        self.sheets = sheets

    def sheet_by_index(self, i):
        return self.sheets[i]


def bel_rows():
    return [
        ["PEN- 1. Pensiones e importe medio, según clase", ""],
        ["AÑOS", "Número", "Importe medio"],
        ["2024...........", 10188.8, 1255.43],
        ["2025...........", 10354.59, 1311.7],
        ["2025:", "", ""],
        ["(ENE-SEP).....", 10333.6, 1310.07],
        ["2025:", "", ""],
        ["NOV...........", 10420.2, 1316.69],
        ["DIC...........", 10434.9, 1317.71],
        ["2026:", "", ""],
        ["ENE...........", 10452.7, "-"],
        ["FEB...........", 10446.9, 1366.2],
        ["(1) Véanse FUENTES Y NOTAS", ""],
    ]


def test_bel_reads_years_and_months(monkeypatch):
    monkeypatch.setattr(bel.xlrd, "open_workbook", lambda file_contents: FakeBook(FakeSheet(bel_rows())))
    out = bel.parse(b"", col=2)
    assert out["A"].to_dict() == {pd.Timestamp("2024-01-01"): 1255.43, pd.Timestamp("2025-01-01"): 1311.7}
    assert list(out["M"].index) == [pd.Timestamp("2025-11-01"), pd.Timestamp("2025-12-01"), pd.Timestamp("2026-02-01")]
    assert bel.parse(b"", col=1)["M"][pd.Timestamp("2026-01-01")] == 10452.7


def test_bel_blocks(monkeypatch):
    rows = [["AÑOS", "MÁXIMA"], [2025.0, 45746.4], [2026.0, 47034.4], ["", ""], ["AÑOS", "JUBILACIÓN"],
            [2025.0, 15786.4], [2026.0, 17592.4]]
    monkeypatch.setattr(bel.xlrd, "open_workbook", lambda file_contents: FakeBook(FakeSheet(rows)))
    assert bel.parse(b"", col=1)["A"].iloc[-1] == 47034.4
    assert bel.parse(b"", col=1, block=1)["A"].iloc[-1] == 17592.4


def test_registry_and_tab():
    inds = load_registry()
    ids = {i.id for i in inds}
    assert page_indicator_ids("pensions") <= ids
    assert sum(i.source == "bel" for i in inds) == 104
    assert {"pensions_total", "pension_avg_retirement_annual", "pension_max", "retirement_avg_reg_ceuta_melilla"} <= ids
    tabs = [href for href, _ in NAV]
    assert tabs.index("pensions.html") == tabs.index("housing.html") + 1 and "pensions" in SECTION_PAGES


def pension_store(tmp_path) -> Store:
    store = Store(tmp_path / "data")
    years = pd.date_range("2016-01-01", "2025-01-01", freq="YS")
    store.save_series("pensions_total_annual", pd.Series(np.linspace(9400.0, 10400.0, len(years)), index=years))
    store.save_series("pension_avg_total_annual", pd.Series(np.linspace(900.0, 1300.0, len(years)), index=years))
    store.save_series("gdp_nominal_annual", pd.Series(1_700_000.0, index=years))
    m = pd.date_range("2015-01-01", "2026-09-01", freq="MS")
    store.save_series("cpi_index", pd.Series(np.linspace(80.0, 104.0, len(m)), index=m))
    store.save_series("afiliados", pd.Series(21000.0, index=m))
    recent = pd.date_range("2025-04-01", "2026-09-01", freq="MS")
    store.save_series("pensions_total", pd.Series(np.linspace(10324.0, 10547.4, len(recent)), index=recent))
    store.save_series("pension_avg_total", pd.Series(np.linspace(1309.0, 1374.57, len(recent)), index=recent))
    store.save_series("pension_avg_retirement", pd.Series(1576.1, index=recent))
    store.save_series("new_pension_avg_retirement", pd.Series(1711.4, index=recent))
    store.save_series("new_pensions_total", pd.Series(50.0, index=recent))
    limits = pd.date_range("1990-01-01", "2026-01-01", freq="YS")
    store.save_series("pension_max", pd.Series(np.r_[np.full(len(limits) - 1, 3267.6), 3359.6], index=limits))
    return store


def test_calculations(tmp_path):
    data = Data(load_registry(), pension_store(tmp_path))
    cost = pensions.annual_cost(data)
    assert round(cost.loc[2025, "cost"]) == round(10400 * 1300 * 14 / 1000)
    assert round(cost.loc[2016, "share"], 2) == round(9400 * 900 * 14 / 1000 / 1_700_000 * 100, 2)
    real = pensions.real_average(data)
    assert real.loc[2016].tolist() == [100.0, 100.0] and real.loc[2025, "nominal"] > real.loc[2025, "real"]
    yearly, monthly = pensions.workers_per_pension(data)
    assert round(yearly.loc[2016], 3) == round(21000 / 9400, 3) and round(monthly.iloc[-1], 2) == round(21000 / 10547.4, 2)


def test_facts(tmp_path):
    data = Data(load_registry(), pension_store(tmp_path))
    facts = {f["label"]: f for f in pensions.overview_facts(data)}
    assert facts["Contributory pensions"]["value"] == "10.55 million" and "Sep 2026" in facts["Contributory pensions"]["sub"]
    assert facts["Average pension"]["value"] == "€1,374.57" and facts["Average pension"]["sub"].endswith("retirement €1,576.10")
    assert facts["What they cost"]["value"] == "€189 bn" and facts["What they cost"]["sub"].endswith("; 11.1% of GDP")
    assert facts["Workers per pension"]["value"] == "1.99" and facts["Workers per pension"]["sub"].endswith("2.23 in 2016")
    new = {f["label"]: f for f in pensions.new_facts(data)}
    assert new["A new retirement pension"]["sub"].endswith("+8.6% on the average retirement pension")
    assert new["Pensions granted"]["value"] == "600k"
    limits = {f["label"]: f for f in pensions.limits_facts(data)}
    assert limits["Maximum pension"]["value"] == "€3,359.60" and limits["Maximum pension"]["sub"].endswith("+2.8% on a year")


def test_the_page(tmp_path):
    page = build_page("pensions", load_registry(), pension_store(tmp_path))
    blocks = {b["id"]: b for b in page["blocks"]}
    assert "overview" in blocks and "limits" in blocks
    charts = {c["id"] for c in page["charts"]}
    assert {"pension-real", "pension-cost", "workers-per-pension", "pension-limits"} <= charts
