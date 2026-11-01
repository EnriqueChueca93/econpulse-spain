"""Batch 16: the Fiscal Explorer's baseline and data (no network)."""

import numpy as np
import pandas as pd
import pytest

from econpulse import fiscal
from econpulse.build import build_site
from econpulse.registry import load_registry
from econpulse.store import Store
from econpulse.tables import Data


@pytest.fixture(scope="module")
def raw():
    return fiscal.load()


@pytest.fixture(scope="module")
def rows(raw):
    return fiscal.baseline(raw)


def test_the_commission_baseline_is_reproduced(raw, rows):
    dsm = {int(y): v for y, v in raw["dsm"]["baseline"]["debt"].items()}
    last = max(dsm)
    assert last == 2036 and rows[last]["source"] == "Commission" and rows[last + 1]["source"] == "EconPulse extension"
    # The derived interest rate and growth, run through the debt equation, give the Commission's path back.
    d = rows[2024]["debt"]
    for y in range(2025, last + 1):
        r = rows[y]
        d = d * (1 + r["i"] / 100) / (1 + r["g"] / 100) - r["pb"] + r["sfa"]
        assert d == pytest.approx(dsm[y], abs=1e-3)
    assert rows[2036]["balance"] == pytest.approx(raw["dsm"]["baseline"]["structural_balance"]["2036"], abs=0.01)


def test_the_extension_behaves_like_the_commission_long_run(raw, rows):
    assert fiscal.END == 2070 and max(rows) == 2070
    # The Commission's S1: the adjustment from 2027 that brings debt to 60% of GDP by 2070.
    assert fiscal.gap(rows, 60.0, 2070) == pytest.approx(raw["dsm"]["gaps"]["S1"], abs=0.1)
    # After 2036 the primary balance falls one for one with the rise in ageing costs.
    ageing = lambda y: sum(rows[y][k] for k in fiscal.AGEING)  # noqa: E731
    assert rows[2050]["pb"] - rows[2036]["pb"] == pytest.approx(-(ageing(2050) - ageing(2036)), abs=1e-9)
    assert rows[2050]["inflation"] == fiscal.INFLATION
    assert abs(rows[2070]["i"] - raw["ageing_report"]["interest_rate"]["2070"]) < abs(rows[2037]["i"] - raw["ageing_report"]["interest_rate"]["2070"])


def test_explorer_data_and_history(tmp_path):
    store = Store(tmp_path / "data")
    years = pd.date_range("1995-01-01", "2025-01-01", freq="YS")
    store.save_series("debt_annual", pd.Series(np.linspace(60, 101.6, len(years)), index=years))
    store.save_series("revenue_annual", pd.Series(40.0, index=years))
    fx = fiscal.explorer_data(Data(load_registry(), store))
    assert fx["years"][0] == 2024 and fx["years"][-1] == 2070 and fx["first_lever_year"] == 2027
    assert len(fx["baseline"]["debt"]) == len(fx["years"]) and fx["baseline"]["debt"][fx["years"].index(2036)] == pytest.approx(107.7229)
    debt = fx["history"]["debt_annual"]
    assert debt["years"][0] == 1970 and debt["values"][debt["years"].index(1995)] == 60.0   # Eurostat from 1995, the Commission before
    assert set(fx["history"]) == {"debt_annual", "revenue_annual"}
    assert fiscal.past_groups(fx["history"]) == [("Debt and balances", [("debt_annual", "Gross public debt")]),
                                                 ("Revenue", [("revenue_annual", "Total revenue")])]
    assert fx["s1_check"] == pytest.approx(fx["gaps"]["S1"], abs=0.1) and "Adverse interest-growth differential" in fx["scenarios"]


def test_page_is_built_with_credits(tmp_path):
    store = Store(tmp_path / "data")
    build_site(load_registry(), store, site_dir=tmp_path / "site")
    html = (tmp_path / "site" / "fiscal-explorer.html").read_text(encoding="utf-8")
    assert "econvitals.org/tools/fiscal-explorer/" in html and "CC0 1.0" in html
    assert "Debt Sustainability Monitor 2025" in html and "2024 Ageing Report" in html
    assert 'id="fx-adj"' in html and 'data-fx-goal="hold"' in html and 'aria-current="page">Tools<' in html
    assert (tmp_path / "site" / "data" / "fiscal.js").exists() and (tmp_path / "site" / "assets" / "fiscal.js").exists()
    assert 'href="fiscal-explorer.html"' in (tmp_path / "site" / "tools.html").read_text(encoding="utf-8")


def test_missing_baseline_file(tmp_path):
    assert fiscal.explorer_data(Data(load_registry(), Store(tmp_path / "data")), path=tmp_path / "none.json") is None
