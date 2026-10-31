"""Financial and ECB pages: market moves, curves, ECB decisions and the mortgage check (no network)."""

import numpy as np
import pandas as pd
import pytest

from econpulse import charts, pages, policy
from econpulse.registry import Indicator, load_registry
from econpulse.store import Store
from econpulse.tables import Data, Level, Move, Row, Spread, Table, build_table


def ind(**kw):
    base = dict(label=kw["id"], label_es=kw["id"], section="financial", source="fake", key=kw["id"], freq="D", unit="%")
    return Indicator(**{**base, **kw})


def daily(values, start="2025-12-29"):
    return pd.Series(values, index=pd.bdate_range(start, periods=len(values)), dtype="float64")


def cells(table: dict, label: str) -> list[str]:
    return next(r["cells"] for r in table["rows"] if r.get("label") == label)


@pytest.fixture
def store(tmp_path):
    return Store(tmp_path / "data")


# ---------------------------------------------------------------- market moves and spreads

def test_market_moves_in_bp_for_rates_and_percent_for_prices(store):
    # Business days from Mon 29 Dec 2025; the year ends on Wed 31 Dec (the 3rd value).
    yields = daily([3.00, 3.10, 3.20] + [3.20 + 0.01 * i for i in range(1, 11)])
    index = daily([100.0, 100.0, 100.0] + [100.0 + i for i in range(1, 11)])
    store.save_series("y", yields)
    store.save_series("ix", index)
    by = [ind(id="y", change_unit="bp", decimals=2), ind(id="ix", unit="index", change_unit="%", decimals=0)]
    table = Table("Market", "", [Level("latest"), Move("1-day", "day"), Move("1-week", "week"), Move("YTD", "ytd"),
                                 Move("1-yr", "year")], [Row("y", "Yield"), Row("ix", "Index")])
    out = build_table(table, Data(by, store))
    # Latest 3.30 (Fri 16 Jan); a week earlier, Fri 9 Jan, was 3.25; the year ended at 3.20.
    assert cells(out, "Yield") == ["3.30%", "+1 bp", "+5 bp", "+10 bp", "–"]
    assert cells(out, "Index") == ["110", "+0.9%", "+4.8%", "+10.0%", "–"]


def test_moves_that_a_monthly_series_cannot_have(store):
    store.save_series("g", pd.Series([10.0] * 11 + [11.0, 12.0], index=pd.date_range("2025-09-01", periods=13, freq="MS")))
    table = Table("T", "", [Move("1-day", "day"), Move("1-week", "week"), Move("1-month", "month"), Move("YTD", "ytd")],
                  [Row("g", "Gas")])
    out = build_table(table, Data([ind(id="g", freq="M", unit="$/MMBtu", change_unit="%")], store))
    assert cells(out, "Gas") == ["–", "–", "+9.1%", "+20.0%"]


def test_spread_and_year_end_level(store):
    store.save_series("es", daily([3.0, 3.1, 3.2, 3.5, 3.6]))
    store.save_series("aaa", daily([2.5, 2.6, 2.7, 2.9, 2.95]))
    by = [ind(id="es", change_unit="bp", decimals=2), ind(id="aaa", change_unit="bp", decimals=2)]
    table = Table("Bonds", "", [Level("latest"), Level("yearend"), Spread("Over AAA")], [Row("es", "Spain", vs="aaa")])
    out = build_table(table, Data(by, store))
    assert out["columns"] == ["Latest", "End-2025", "Over AAA"]
    assert cells(out, "Spain") == ["3.60%", "3.20%", "+65 bp"]


# ---------------------------------------------------------------- curves

def test_curve_reads_every_line_at_shared_dates(store):
    dates = pd.date_range("2025-11-01", "2026-10-29", freq="D")
    for i, mat in enumerate(("a", "b", "c")):
        store.save_series(mat, pd.Series(np.linspace(2.0, 3.0, len(dates)) + i * 0.5, index=dates))
    store.save_series("late", pd.Series(1.0, index=dates[:-2]))  # stops two days earlier
    store.save_series("dfr", pd.Series(2.25, index=dates))
    points = [("a", "1y"), ("b", "5y"), ("c", "10y")]
    definition = {"id": "c", "title": "T", "subtitle": "S", "curve": True, "unit": "%", "decimals": 2,
                  "ref_from": [("dfr", "Deposit rate")],
                  "lines": [{"at": "latest", "name": "{date}", "points": points},
                            {"at": "yearend", "name": "End-{prev_year}", "points": points},
                            {"at": "latest", "name": "Late", "points": [("late", "1y"), ("late", "5y")]}]}
    by = {i: ind(id=i) for i in ("a", "b", "c", "late", "dfr")}
    spec = charts.build_curve(definition, by, store)
    names = [s["name"] for s in spec["series"]]
    assert names == ["27 Oct 2026", "End-2025", "Late"]  # every line read on the latest shared date
    assert spec["series"][0]["x"] == ["1y", "5y", "10y"] and spec["x_kind"] == "category"
    assert spec["series"][1]["y"][0] == pytest.approx(2.0 + 60 / 362, abs=1e-3)  # value on 31 Dec 2025
    assert spec["ref_lines"] == [{"y": 2.25, "label": "Deposit rate 2.25%"}]
    assert "curve" not in spec and "lines" not in spec


# ---------------------------------------------------------------- ECB and mortgages

def test_rate_changes_and_decisions_table(store):
    dfr = pd.Series([2.0] * 5 + [2.25] * 5 + [2.5] * 3, index=pd.date_range("2026-06-01", periods=13, freq="W-WED"))
    assert [(d.strftime("%Y-%m-%d"), lvl, round(bp)) for d, lvl, bp in policy.rate_changes(dfr)] == [
        ("2026-08-12", 2.5, 25), ("2026-07-08", 2.25, 25)]
    store.save_series("ecb_deposit_rate", dfr)
    table = policy.decisions_table(Data([ind(id="ecb_deposit_rate")], store))
    assert table["columns"] == ["Deposit rate", "Change"]
    assert [r["label"] for r in table["rows"]] == ["12 Aug 2026", "8 Jul 2026"]
    assert table["rows"][0]["cells"] == ["2.50%", "+25 bp"]


def test_next_decision_and_facts(store):
    assert policy.next_decision(pd.Timestamp("2026-10-31")) == pd.Timestamp("2026-12-17")
    assert policy.next_decision(pd.Timestamp("2026-12-17")) == pd.Timestamp("2026-12-17")
    assert policy.next_decision(pd.Timestamp("2029-01-01")) is None
    store.save_series("ecb_deposit_rate", pd.Series([2.25, 2.5], index=pd.to_datetime(["2026-09-15", "2026-09-16"])))
    facts = policy.ecb_facts(Data([ind(id="ecb_deposit_rate"), ind(id="estr")], store), today=pd.Timestamp("2026-12-16"))
    assert [(f["label"], f["value"], f["sub"]) for f in facts] == [
        ("Deposit facility rate", "2.50%", "16 Sep 2026"),
        ("Last change", "+25 bp", "took effect 16 Sep 2026"),
        ("Next decision", "17 Dec 2026", "in 1 day"),
    ]


def test_monthly_payment():
    assert policy.monthly_payment(150_000, 4.14, 25) == pytest.approx(803.5, abs=0.5)
    assert policy.monthly_payment(120_000, 0.0, 10) == pytest.approx(1000.0)


def test_mortgage_check(store):
    days = pd.bdate_range("2025-10-01", "2026-10-29")
    euribor = pd.Series(np.where(days < pd.Timestamp("2026-01-01"), 2.19, 3.24), index=days)
    store.save_series("euribor_12m", euribor)
    text = policy.mortgage_check(Data([ind(id="euribor_12m")], store))
    assert "October's average 12-month Euribor (3.24% so far, to 29 Oct)" in text
    assert "costs €803 a month: €85 more than a reset at the rate a year earlier (2.19%)" in text


# ---------------------------------------------------------------- pages

def test_financial_and_ecb_pages_build_with_partial_data(tmp_path):
    store = Store(tmp_path / "data")
    dates = pd.date_range("2025-01-01", "2026-10-31", freq="D")
    store.save_series("ecb_deposit_rate", pd.Series(np.where(dates < pd.Timestamp("2026-06-17"), 2.0, 2.25), index=dates))
    indicators = load_registry()

    ecb = pages.build_page("ecb", indicators, store)
    rates = ecb["blocks"][0]
    assert rates["id"] == "rates" and rates["facts"][0]["value"] == "2.25%"
    assert [t["title"] for t in rates["tables"]] == ["Rate", "Date it took effect"]
    assert {c["id"] for c in ecb["charts"]} >= {"policy-rates", "deposit-history"}

    fin = pages.build_page("financial", indicators, store)
    assert [b["id"] for b in fin["blocks"]] == ["euribor"]  # only the Euribor block has a chart with data
    assert fin["blocks"][0]["callout"] is None  # no Euribor data, no mortgage check
