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
