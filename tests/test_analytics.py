"""Batch 7: composites, the GDP nowcast, the 10-year decomposition and Taylor rules (no network)."""

import numpy as np
import pandas as pd
import pytest

from econpulse import analytics, pages
from econpulse.analytics import Component
from econpulse.registry import Indicator, load_registry
from econpulse.store import Store
from econpulse.tables import Data


def ind(**kw):
    base = dict(label=kw["id"], label_es=kw["id"], section="analysis", source="fake", key=kw["id"], freq="M", unit="%")
    return Indicator(**{**base, **kw})


def monthly(values, start="2013-01-01"):
    return pd.Series(values, index=pd.date_range(start, periods=len(values), freq="MS"), dtype="float64")


@pytest.fixture
def store(tmp_path):
    return Store(tmp_path / "data")


# ---------------------------------------------------------------- composites

def test_component_z_scores_signs_and_clipping(store):
    n = 120
    noise = np.tile([-1.0, 1.0], n // 2)
    store.save_series("good", monthly(np.r_[noise[:-1], 2.0]))          # ends 2 deviations above normal
    store.save_series("bad", monthly(np.r_[noise[:-1], 2.0]))           # same, but higher is worse
    store.save_series("wild", monthly(np.r_[noise[:-1], 50.0]))         # clipped
    data = Data([ind(id=i) for i in ("good", "bad", "wild")], store)
    comps = [Component("good", "Good"), Component("bad", "Bad", sign=-1), Component("wild", "Wild")]
    c = analytics.composite(data, comps, "test")
    z = {r["component"].id: r["z"] for r in c["rows"]}
    # Median 0, MAD 1 -> scale 1.4826: a reading of 2 is +1.35.
    assert z["good"] == pytest.approx(2 / 1.4826, abs=1e-3)
    assert z["bad"] == pytest.approx(-2 / 1.4826, abs=1e-3)
    assert z["wild"] == analytics.Z_CLIP
    assert c["series"].iloc[-1] == pytest.approx((z["good"] + z["bad"] + z["wild"]) / 3)
    assert analytics.composite(data, comps, "test") is c  # cached for the build


def test_older_readings_lose_weight(store):
    store.save_series("new", monthly(np.r_[np.tile([-1.0, 1.0], 60), 1.0]))  # one month further on
    store.save_series("old", monthly(np.r_[np.tile([-1.0, 1.0], 59), -1.0, 3.0]))
    data = Data([ind(id="new"), ind(id="old")], store)
    c = analytics.composite(data, [Component("new", "New"), Component("old", "Old")], "w")
    rows = {r["component"].id: r for r in c["rows"]}
    assert rows["new"]["age"] == 0 and rows["old"]["age"] == 1
    expected = (1.0 * rows["new"]["z"] + 0.75 * rows["old"]["z"]) / 1.75
    assert c["series"].iloc[-1] == pytest.approx(expected)


def test_covid_years_do_not_set_the_norm(store):
    values = np.tile([-1.0, 1.0], 84)
    s = monthly(values)
    s["2020-03-01":"2021-12-01"] = -30.0
    assert analytics._norm(s) == pytest.approx((0.0, 1.4826))


# ---------------------------------------------------------------- nowcast

def _nowcast_store(tmp_path):
    store = Store(tmp_path / "data")
    months = pd.date_range("2010-01-01", "2026-09-01", freq="MS")
    t = np.arange(len(months))
    cycle = 0.004 * np.sin(t / 9)
    afil = 1000 * np.exp(np.cumsum(0.0015 + cycle) + 0.01 * np.sin(2 * np.pi * (months.month - 1) / 12))
    ipi = 100 * np.exp(np.cumsum(0.0005 + 0.5 * cycle))
    store.save_series("afiliados", pd.Series(afil, index=months))
    store.save_series("industrial_production", pd.Series(ipi[:-1], index=months[:-1]))  # one month behind
    quarters = pd.date_range("2010-01-01", "2026-04-01", freq="QS")
    qq = 0.3 + 100 * pd.Series(cycle, index=months).resample("QS").mean().reindex(quarters).to_numpy()
    store.save_series("gdp", pd.Series(100 * np.cumprod(1 + qq / 100), index=quarters))
    inds = [ind(id="afiliados", unit="thousands"), ind(id="industrial_production", unit="index"),
            ind(id="gdp", freq="Q", unit="index")]
    return Data(inds, store)


def test_nowcast_targets_the_next_quarter(tmp_path):
    data = _nowcast_store(tmp_path)
    n = analytics.nowcast(data)
    assert n["quarter"] == pd.Timestamp("2026-07-01")  # the quarter after the last GDP figure
    assert {c["input"].id: c["months"] for c in n["coverage"]} == {"afiliados": 3, "industrial_production": 2}
    assert np.isfinite(n["value"]) and n["rmse"] is not None and n["backtest"]
    assert n["rmse"] < n["naive_rmse"]  # GDP here is driven by the cycle the inputs track
    facts = analytics.nowcast_facts(data)
    assert facts[0]["label"] == "GDP nowcast (placeholder), Q3 2026" and facts[2]["value"] == "5 of 6"


def test_ar1_extension():
    s = monthly(100 * 1.01 ** np.arange(60))
    out = analytics._ar1_extend(s, pd.Timestamp("2018-03-01"), growth=True)
    assert out.index[-1] == pd.Timestamp("2018-03-01")
    assert out.iloc[-1] / out.iloc[-2] == pytest.approx(1.01, abs=1e-6)


# ---------------------------------------------------------------- decomposition and Taylor rules

def test_yield_decomposition_parts_add_up(store):
    days = pd.bdate_range("2025-10-01", "2026-10-30")
    es = pd.Series(np.linspace(3.0, 4.0, len(days)), index=days)
    de = pd.Series(np.linspace(2.6, 3.3, len(days)), index=days)
    store.save_series("es_10y", es)
    store.save_series("de_10y", de.iloc[:-1])  # one day behind: the table uses the last common day
    table = analytics.yield_decomposition_table(Data([ind(id="es_10y", freq="D"), ind(id="de_10y", freq="D")], store))
    assert "29 Oct 2026" in table["caption"]
    to_bp = lambda s: int(s.replace("−", "-").replace(" bp", ""))
    total, bund, spread = ([to_bp(c) for c in r["cells"]] for r in table["rows"])
    assert all(abs(t - (b + s)) <= 1 for t, b, s in zip(total, bund, spread))


def test_taylor_rule_formula():
    months = pd.date_range("2005-01-01", periods=240, freq="MS")
    df = analytics._rule(pd.Series(3.0, index=months), pd.Series(10.0, index=months))
    # Flat unemployment: no gap. 0.5 + 3 + 0.5 x (3 - 2) = 4.0
    assert df["u_gap"].abs().max() < 1e-9
    assert df["rule"].iloc[-1] == pytest.approx(4.0)
    higher = analytics._rule(pd.Series(3.0, index=months), pd.Series(np.r_[[10.0] * 239, 11.0], index=months))
    assert higher["rule"].iloc[-1] < 4.0  # more unemployment than trend: a lower rate


# ---------------------------------------------------------------- page

def test_analysis_page_builds_with_partial_data(tmp_path):
    store = Store(tmp_path / "data")
    days = pd.bdate_range("2025-10-01", "2026-10-30")
    store.save_series("es_10y", pd.Series(np.linspace(3.0, 4.0, len(days)), index=days))
    store.save_series("de_10y", pd.Series(np.linspace(2.6, 3.3, len(days)), index=days))
    page = pages.build_page("analysis", load_registry(), store)
    assert [b["id"] for b in page["blocks"]] == ["yields"]  # the other blocks have no data: dropped
    assert page["blocks"][0]["tables"][0]["rows"][0]["label"] == "Spain 10-year yield"
    assert analytics.home_facts(Data(load_registry(), store)) == []
