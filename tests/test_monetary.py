"""Batch 35a: the monetary survey rebuilt from ECB and Banco de España series, and where broad money growth comes
from (no network)."""

import pandas as pd
import pytest

from econpulse import monetary
from econpulse.registry import load_registry
from econpulse.sources import monsurvey
from econpulse.store import Store
from econpulse.tables import Data

MONTHS = pd.date_range("2024-01-01", "2026-09-01", freq="MS")


def test_survey_lines_from_their_components(monkeypatch):
    """Every term is a constant € million series, so each line's arithmetic can be checked by hand."""
    values = {}

    def component(term):
        values.setdefault(term, 10.0 + len(values))           # a different constant per term
        return pd.Series(values[term], index=MONTHS)

    monkeypatch.setattr(monsurvey, "_component", component)
    claims = monsurvey.line("claims_gg")
    expected = sum(values[t] for t in monsurvey.CLAIMS_GG.split() if t != "+")
    assert claims.iloc[-1] == pytest.approx(expected)
    # A minus sign subtracts its term; derived lines combine the base ones; other items (net) balance the survey.
    nfa = monsurvey.line("nfa").iloc[-1]
    a, b, c, d = (values[t] for t in monsurvey.FOREIGN.split() if t not in "+-")
    assert nfa == pytest.approx(a + b - c - d)
    net = monsurvey.line("net_claims_gg").iloc[-1]
    assert net == pytest.approx(monsurvey.line("claims_gg").iloc[-1] - monsurvey.line("gov_deposits").iloc[-1])
    oin = monsurvey.line("oin").iloc[-1]
    others = sum(monsurvey.line(k).iloc[-1] for k in ("broad_money", "deposits_xbm", "securities_xbm", "equity", "derivatives"))
    assert oin == pytest.approx(monsurvey.line("nfa").iloc[-1] + monsurvey.line("domestic_claims").iloc[-1] - others)
    assert monsurvey.fetch("broad_money").series.iloc[-1] == pytest.approx(monsurvey.line("broad_money").iloc[-1] / 1000)


def test_broad_money_growth_splits_exactly(tmp_path):
    store = Store(tmp_path / "data")
    n = pd.Series(range(len(MONTHS)), index=MONTHS, dtype=float)
    lines = {"ms_nfa": 400 + 2 * n, "ms_net_claims_gg": 700 + 3 * n, "ms_claims_private": 1600 + 5 * n,
             "ms_deposits_xbm": 170 + 0 * n, "ms_securities_xbm": 230 + n, "ms_equity": 340 + n, "ms_derivatives": 110 + 0 * n}
    lines["ms_oin"] = 60 + 0.5 * n
    lines["ms_broad_money"] = (lines["ms_nfa"] + lines["ms_net_claims_gg"] + lines["ms_claims_private"] - lines["ms_deposits_xbm"]
                               - lines["ms_securities_xbm"] - lines["ms_equity"] - lines["ms_derivatives"] - lines["ms_oin"])
    for ind_id, s in lines.items():
        store.save_series(ind_id, s)
    data = Data(load_registry(), store)
    parts = monetary.sources(data)
    bm = lines["ms_broad_money"]
    growth = (bm / bm.shift(12) - 1) * 100
    assert (sum(parts.values()) - growth).dropna().abs().max() < 1e-9
    assert parts["Claims on the private sector"].iloc[-1] == pytest.approx(5 * 12 / bm.iloc[-13] * 100)
    facts = monetary.facts(data)
    assert facts[0]["label"] == "Broad money" and facts[0]["sub"].endswith("Sep 2026")


def test_credit_impulse_is_the_change_in_the_years_new_lending(tmp_path):
    """Net new lending rising by €1 bn a month each year: the year's flow grows by a fixed amount, so the impulse is
    that amount over a year's GDP."""
    store = Store(tmp_path / "data")
    months = pd.date_range("2020-01-01", "2024-12-01", freq="MS")
    year = pd.Series(months.year - 2020, index=months, dtype=float)
    store.save_series("credit_flow_nfc", 1000 + 500 * year)           # € mn a month
    store.save_series("credit_flow_households", 200 + 500 * year)
    quarters = pd.date_range("2020-01-01", "2024-10-01", freq="QS")
    store.save_series("gdp_nominal", pd.Series(300_000.0, index=quarters))
    data = Data(load_registry(), store)
    impulse = monetary.credit_impulse(data)
    # A year's flow rises by 12 × €1 bn = €12 bn on the year before, over GDP of 4 × €300 bn: 1% of GDP.
    assert impulse.loc["2023-01-01":].round(9).eq(1.0).all()
    assert impulse.index[0] == pd.Timestamp("2021-10-01")             # 12 months for a year's flow, 4 more quarters


def test_lead_pairs_find_the_lead_and_leave_out_the_pandemic():
    quarters = pd.date_range("2000-01-01", "2026-07-01", freq="QS")
    x = pd.Series([((i * 7) % 11) - 5.0 for i in range(len(quarters))], index=quarters)
    y = pd.Series(x.values, index=x.index + pd.DateOffset(months=9))    # y repeats x three quarters later
    assert monetary._pairs(x, y, 3)["x"].corr(monetary._pairs(x, y, 3)["y"]) == pytest.approx(1.0)
    assert abs(monetary._pairs(x, y, 0)["x"].corr(monetary._pairs(x, y, 0)["y"])) < 0.9
    pairs = monetary._pairs(x, y, 3)
    target = pairs.index + pd.DateOffset(months=9)
    touches = lambda d: (d >= pd.Timestamp("2020-01-01")) & (d <= pd.Timestamp("2021-12-31"))
    assert not touches(pairs.index).any() and not touches(target).any()


def test_quarters_need_all_three_months():
    months = pd.date_range("2025-01-01", "2025-08-01", freq="MS")
    s = pd.Series(range(len(months)), index=months, dtype=float)
    q = monetary._quarter(s)
    assert list(q.index) == [pd.Timestamp("2025-01-01"), pd.Timestamp("2025-04-01")]   # Q3 has two months only
    assert q.iloc[0] == pytest.approx(1.0) and monetary._quarter(s, "last").iloc[1] == pytest.approx(5.0)
    assert monetary._change(pd.Series([100.0, 110.0], index=[pd.Timestamp("2024-01-01"), pd.Timestamp("2025-01-01")])).iloc[0] \
        == pytest.approx(10.0)


def test_passthrough_measures_the_2022_23_rises(tmp_path):
    store = Store(tmp_path / "data")
    days = pd.date_range("2021-01-01", "2025-06-30", freq="D")
    dfr = pd.Series(-0.5, index=days)
    dfr[days >= "2022-07-27"] = 0.0
    dfr[days >= "2023-09-20"] = 4.0
    dfr[days >= "2024-06-12"] = 3.75
    store.save_series("ecb_deposit_rate", dfr)
    months = pd.date_range("2021-01-01", "2025-06-01", freq="MS")
    monthly = lambda before, after: pd.Series([before if m <= pd.Timestamp("2022-06-01") else after for m in months], index=months)
    store.save_series("euribor_12m", monthly(0.5, 4.0))
    store.save_series("nfc_loan_rate", monthly(1.5, 5.25))
    store.save_series("mortgage_rate", monthly(2.0, 4.0))
    store.save_series("deposit_rate_households", monthly(0.1, 2.5))
    store.save_series("deposit_rate_overnight", monthly(0.0, 0.1))
    data = Data(load_registry(), store)
    p = monetary.passthrough(data)
    assert p["start"] == pd.Timestamp("2022-06-01") and p["peak"] == pd.Timestamp("2023-10-01")
    assert p["change"]["ecb_deposit_rate"] == pytest.approx(4.5)
    assert p["change"]["nfc_loan_rate"] == pytest.approx(3.75)
    assert p["change"]["deposit_rate_overnight"] == pytest.approx(0.1)
    chart = monetary.passthrough_chart(data)
    assert chart["series"][0]["x"][0] == "ECB deposit rate" and "83%" in chart["reading"]
