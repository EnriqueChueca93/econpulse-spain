"""Batch 34d: contributions to growth, the labour share and productivity on the GDP page (no network)."""

import numpy as np
import pandas as pd
import pytest

from econpulse import gdpdetail, i18n
from econpulse.registry import load_registry
from econpulse.store import Store
from econpulse.tables import Data

Q = pd.date_range("2018-01-01", "2026-07-01", freq="QS")


def accounts(tmp_path) -> Data:
    """Volumes growing at known rates, with fixed nominal shares of GDP (60/20/20/30/-30)."""
    store = Store(tmp_path / "data")
    n = np.arange(len(Q))
    rates = {"cons_hh_npish": 0.01, "consumption_government": 0.005, "investment": 0.02, "exports": 0.015, "imports": 0.01}
    shares = {"cp_cons_hh_npish": 0.6, "cp_cons_government": 0.2, "cp_gfcf": 0.2, "cp_exports": 0.3, "cp_imports": 0.3}
    for ind_id, r in rates.items():
        store.save_series(ind_id, pd.Series(100 * (1 + r) ** n, index=Q))
    gdp_n = pd.Series(300_000.0, index=Q)
    store.save_series("gdp_nominal", gdp_n)
    for ind_id, share in shares.items():
        store.save_series(ind_id, gdp_n * share)
    # INE's domestic-demand contribution includes inventories worth 0.1 pp a quarter on top of C, G and I.
    dom_q = (0.6 * 1.0 + 0.2 * 0.5 + 0.2 * 2.0) + 0.1
    store.save_series("contrib_domestic_qq", pd.Series(dom_q, index=Q))
    store.save_series("gdp", pd.Series(100 * 1.01 ** n, index=Q))
    # The income side and hours: labour 55% of GDP at factor cost (GDP 300 less 30 of net taxes).
    store.save_series("compensation_employees", pd.Series(0.55 * 270_000, index=Q))
    store.save_series("operating_surplus", pd.Series(0.45 * 270_000, index=Q))
    store.save_series("net_taxes_production", pd.Series(30_000.0, index=Q))
    store.save_series("hours_cn", pd.Series(1_000 * 1.004 ** n, index=Q))
    store.save_series("jobs_fte", pd.Series(20_000 * 1.005 ** n, index=Q))
    return Data(load_registry(), store)


def test_demand_contributions_and_inventories(tmp_path):
    parts = gdpdetail.demand(accounts(tmp_path), "q")
    last = Q[-1]
    assert parts["Household consumption"][last] == pytest.approx(0.6)
    assert parts["Fixed investment"][last] == pytest.approx(0.4)
    assert parts["Imports"][last] == pytest.approx(-0.3)            # imports subtract
    assert parts["Inventories"][last] == pytest.approx(0.1)          # the rest of INE's domestic contribution
    y = gdpdetail.demand(accounts(tmp_path), "y")
    assert y["Exports"][last] == pytest.approx(0.3 * (1.015 ** 4 - 1) * 100)


def test_labour_share_and_productivity(tmp_path):
    data = accounts(tmp_path)
    facts = gdpdetail.income_facts(data)
    assert facts[0]["label"] == "Labour share of income" and facts[0]["value"] == "55.0%"
    split = gdpdetail.growth_split_chart(data)
    hours, per_hour, gdp = (s["y"][-1] for s in split["series"])
    assert hours + per_hour == pytest.approx(gdp, abs=1e-6)          # log points add up
    assert hours == pytest.approx(np.log(1.004 ** 4) * 100, abs=1e-3)
    levels = gdpdetail.productivity_levels_chart(data)
    assert levels["series"][0]["name"] == "Output per hour worked" and levels["ref_lines"][0]["y"] == 100
    with i18n.using("es"):
        assert gdpdetail.income_facts(data)[0]["label"] == "Participación del trabajo en la renta"
        assert gdpdetail.productivity_levels_chart(data)["title"] == "Producción por hora y por puesto de trabajo"
