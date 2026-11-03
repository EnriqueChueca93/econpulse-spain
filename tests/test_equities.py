"""Batch 34c: equities on the Financial page, the IBEX 35 and the Madrid exchange's sectors (no network)."""

import pandas as pd
import pytest

from econpulse import equities, i18n
from econpulse.registry import load_registry
from econpulse.store import Store
from econpulse.tables import Data


def market(tmp_path) -> Data:
    """Trading days to Thursday 29 Oct 2026: each index flat at 100 until the last week, then its own path."""
    store = Store(tmp_path / "data")
    days = pd.bdate_range("2024-12-02", "2026-10-29")
    moves = {"ibex35": 0.02, "madrid_general": 0.01, "madrid_financials": -0.03, "madrid_energy": 0.005,
             "madrid_consumer_goods": 0.0, "madrid_industry": 0.01, "madrid_consumer_services": -0.01, "madrid_tech": 0.0}
    for ind_id, move in moves.items():
        s = pd.Series(100.0, index=days)
        s[s.index >= "2026-01-01"] = 110.0                     # +10% on the last close of 2025
        s.iloc[-1] = 110.0 * (1 + move)                        # the last day's move
        if ind_id == "madrid_tech":
            s = s[s.index < "2026-10-29"]                      # one sector a day behind
        store.save_series(ind_id, s)
    return Data(load_registry(), store)


def test_the_ibex_facts(tmp_path):
    facts = {f["label"]: f for f in equities.facts(market(tmp_path))}
    assert facts["IBEX 35"]["value"] == "112" and facts["IBEX 35"]["sub"] == "close of 29 Oct 2026"
    assert facts["On the day"]["value"] == "+2.0%" and facts["Over a week"]["value"] == "+2.0%"
    assert facts["This year"]["value"] == "+12.2%" and facts["Over a year"]["value"] == "+12.2%"


def test_the_heat_map(tmp_path):
    spec = equities.heatmap(market(tmp_path))
    assert spec["kind"] == "tiles" and [p["key"] for p in spec["periods"]] == ["day", "week", "ytd"]
    # The tiles share the latest close every sector has (the 28th, as technology is a day behind).
    assert spec["subtitle"] == "% change to the close of 28 Oct 2026: rises in blue, falls in red"
    rows = {r["id"]: r for r in spec["rows"]}
    assert [r["id"] for r in spec["rows"]][:2] == ["ibex35", "madrid_general"] and rows["ibex35"]["index"]
    assert rows["madrid_financials"]["values"] == {"day": 0.0, "week": 0.0, "ytd": 10.0}
    assert spec["bounds"]["day"] == [0.25, 1, 2]
    with i18n.using("es"):
        spec = equities.heatmap(market(tmp_path))
        assert spec["title"] == "La Bolsa de Madrid por sectores" and spec["periods"][0]["label"] == "Última sesión"
        assert {r["label"] for r in spec["rows"]} >= {"IBEX 35", "Servicios financieros e inmobiliarios"}


def test_moves_over_each_period():
    s = pd.Series([100.0, 101.0, 99.0, 103.0], index=pd.to_datetime(["2025-12-31", "2026-01-02", "2026-01-05", "2026-01-12"]))
    date = s.index[-1]
    assert equities._change(s, date, "day") == pytest.approx(103 / 99 * 100 - 100)
    assert equities._change(s, date, "week") == pytest.approx(103 / 99 * 100 - 100)    # a week back: the 5th
    assert equities._change(s, date, "ytd") == pytest.approx(3.0)
    assert equities._change(s.iloc[:1], s.index[0], "day") is None
