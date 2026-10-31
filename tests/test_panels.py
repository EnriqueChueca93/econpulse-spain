"""Batch 6: for_each expansion, rolling totals, panels, rankings and the new pages (no network)."""

import numpy as np
import pandas as pd
import pytest

from econpulse import charts, pages, transforms
from econpulse.registry import Indicator, expand, load_registry
from econpulse.sources import derived
from econpulse.store import Store
from econpulse.tables import (Data, Level, Move, Panel, PanelColumn, PanelRow, Row, Table, YearToDate, build_panel,
                              build_table)


def ind(**kw):
    base = dict(label=kw["id"], label_es=kw["id"], section="regions", source="fake", key=kw["id"], freq="M", unit="%")
    return Indicator(**{**base, **kw})


def monthly(values, start="2025-01-01"):
    return pd.Series(values, index=pd.date_range(start, periods=len(values), freq="MS"), dtype="float64")


def cells(table: dict, label: str) -> list:
    return next(r["cells"] for r in table["rows"] if r.get("label") == label)


@pytest.fixture
def store(tmp_path):
    return Store(tmp_path / "data")


# ---------------------------------------------------------------- registry expansion

def test_for_each_fills_every_string():
    entry = {"id": "hicp_{slug}", "label": "HICP, {name}", "key": "prc_hicp_minr", "freq": "M",
             "params": {"geo": "{geo}", "unit": "RCH_A"}, "transforms": ["level"], "decimals": 1,
             "for_each": [{"slug": "de", "geo": "DE", "name": "Germany"}, {"slug": "fr", "geo": "FR", "name": "France"}]}
    out = expand(entry)
    assert [e["id"] for e in out] == ["hicp_de", "hicp_fr"]
    assert out[1]["params"] == {"geo": "FR", "unit": "RCH_A"} and out[1]["label"] == "HICP, France"
    assert out[0]["decimals"] == 1 and "for_each" not in out[0]
    assert expand({"id": "plain"}) == [{"id": "plain"}]


def test_registry_lists_with_yaml_anchors(tmp_path):
    path = tmp_path / "indicators.yaml"
    path.write_text("""
places: &places
  - {slug: a, code: X1}
  - {slug: b, code: X2}
indicators:
  - id: rate_{slug}
    for_each: *places
    label: Rate {slug}
    label_es: Tasa {slug}
    section: regions
    source: ine
    key: "{code}"
    freq: Q
    unit: "%"
""", encoding="utf-8")
    inds = load_registry(path)
    assert [(i.id, i.key) for i in inds] == [("rate_a", "X1"), ("rate_b", "X2")]


def test_real_registry_regions_and_peers():
    by_id = {i.id: i for i in load_registry()}
    for slug, _ in pages.REGIONS:
        for prefix in ("unemployment", "house_prices", "cpi", "gdp_per_head"):
            assert f"{prefix}_{slug}" in by_id
    assert by_id["unemployment_madrid"].key == "EPA452536"
    assert by_id["spread10_it"].params == {"a": "bond10_it", "b": "de_10y_monthly", "scale": 100}


# ---------------------------------------------------------------- transforms and derived

def test_rolling_year_total_and_average():
    s = monthly(np.arange(1, 25))
    total = transforms.apply("sum_1y", s, "M")
    assert total.iloc[0] == sum(range(1, 13)) and total.index[0] == pd.Timestamp("2025-12-01")
    q = pd.Series([-2.0, -4.0, -1.0, -3.0, 0.0], index=pd.date_range("2025-01-01", periods=5, freq="QS"))
    assert transforms.apply("avg_1y", q, "Q").tolist() == [-2.5, -2.0]
    assert transforms.label("sum_1y", "M") == "12-mo total" and transforms.label("avg_1y", "Q") == "4-qtr avg."
    with pytest.raises(ValueError, match="monthly or quarterly"):
        transforms.apply("sum_1y", pd.Series([1.0], index=[pd.Timestamp("2026-01-01")]), "D")


def test_average_of_complete_months():
    # Calendar-day data (weekends included) up to Fri 30 Oct: October is not complete.
    days = pd.date_range("2026-09-01", "2026-10-30", freq="D")
    s = pd.Series(np.where(days.month == 9, 10.0, 20.0), index=days)
    assert derived.average({"d": s}, "d").to_dict() == {pd.Timestamp("2026-09-01"): 10.0}
    # Business-day data to Fri 30 Oct: October is complete (31 Oct is a Saturday).
    bdays = pd.bdate_range("2026-09-01", "2026-10-30")
    assert len(derived.average({"d": pd.Series(1.0, index=bdays)}, "d")) == 2


def test_add():
    a = pd.Series([-3.2, -2.4], index=pd.to_datetime(["2024-01-01", "2025-01-01"]))
    b = pd.Series([2.4, 2.4], index=a.index)
    assert derived.add({"a": a, "b": b}, "a", "b").round(6).tolist() == [-0.8, 0.0]


# ---------------------------------------------------------------- year to date

def test_year_to_date_columns(store):
    store.save_series("t", monthly([10.0] * 12 + [11.0] * 8))  # Jan 2025 - Aug 2026
    store.save_series("avg", monthly([200.0] * 20))
    by = [ind(id="t", unit="mn"), ind(id="avg", unit="€", decimals=0)]
    table = Table("T", "", [Level("latest"), YearToDate("YTD"), YearToDate("YTD y/y", change=True)],
                  [Row("t", "Tourists"), Row("avg", "Average", flow=False)])
    out = build_table(table, Data(by, store))
    assert cells(out, "Tourists") == ["11.0 mn", "88.0 mn", "10.0"]
    assert cells(out, "Average") == ["€200", "–", "–"]


# ---------------------------------------------------------------- panels

def test_panel_columns_carry_their_period(store):
    store.save_series("u_es", pd.Series([11.0, 10.0], index=pd.to_datetime(["2025-07-01", "2026-07-01"])))
    store.save_series("u_a", pd.Series([15.0, 14.0], index=pd.to_datetime(["2025-07-01", "2026-07-01"])))
    store.save_series("u_b", pd.Series([7.0, 7.5], index=pd.to_datetime(["2025-04-01", "2026-04-01"])))  # lags
    store.save_series("p_a", monthly(100 * 1.01 ** np.arange(20)))
    by = [ind(id=i, freq="Q", decimals=1, change_unit="pp") for i in ("u_es", "u_a", "u_b")] + [ind(id="p_a", unit="index")]
    panel = Panel("Region", "%", [PanelColumn("u", "Unemployment"), PanelColumn("uc", "Change", col=Move("1-yr", "year")),
                                  PanelColumn("p", "Prices, y/y", transform="yoy")],
                  [PanelRow("Spain", {"u": "u_es", "uc": "u_es"}, highlight=True),
                   PanelRow("A", {"u": "u_a", "uc": "u_a", "p": "p_a"}),
                   PanelRow("B", {"u": "u_b", "uc": "u_b", "p": ("missing", "yoy")})])
    out = build_panel(panel, Data(by + [ind(id="missing")], store))
    assert out["columns"] == ["Unemployment", "Change", "Prices, y/y"]
    assert out["column_notes"] == ["Q3 2026", "Q3 2026", "Aug 2026"]
    assert cells(out, "Spain") == ["10.0%", "−1.0 pp", "–"]
    assert cells(out, "A") == ["14.0%", "−1.0 pp", "12.7%"]
    assert cells(out, "B")[0] == {"value": "7.5%", "note": "Q2 2026"}  # a lagging region says so
    assert cells(out, "B")[2] == "–"
    assert out["rows"][0]["highlight"] is True


# ---------------------------------------------------------------- charts

def test_ranking_sorts_and_references(store):
    store.save_series("a", monthly([5.0, 6.0]))
    store.save_series("b", monthly([9.0, 8.0]))
    store.save_series("c", monthly(100 * 1.02 ** np.arange(14)))  # an index: ranked on its y/y change
    store.save_series("avg", monthly([7.0, 7.5]))
    by = {i: ind(id=i) for i in ("a", "b", "avg")} | {"c": ind(id="c", unit="index")}
    definition = {"id": "r", "kind": "hbar", "title": "T", "subtitle": "S", "unit": "%", "decimals": 1,
                  "highlight": "B", "items": [("a", "A"), ("b", "B"), ("c", "C", "yoy")], "ref_from": [("avg", "Average")]}
    spec = charts.build_ranking(definition, by, store)
    assert spec["series"][0]["x"] == ["C", "B", "A"]  # largest first; C is ranked on its y/y change
    assert spec["series"][0]["y"][0] == pytest.approx(26.8, abs=0.1) and spec["series"][0]["y"][1] == 8.0
    assert spec["ref_lines"] == [{"y": 7.5, "label": "Average"}]
    assert spec["subtitle"] == "S · Feb 2025" and spec["highlight"] == "B" and "items" not in spec


def test_chart_scale_rebase_and_derived_sources(store):
    store.save_series("x", monthly([50.0, 100.0, 150.0]))
    store.save_series("calc", monthly([1.0, 2.0, 3.0]))
    by = {"x": ind(id="x", source="ine"), "calc": ind(id="calc", source="derived", key="divide", params={"a": "x", "b": "x"})}
    definition = {"id": "c", "title": "T", "subtitle": "S", "kind": "line", "unit": "", "decimals": 1, "start": "2025-01-01",
                  "series": [("x", "level", "Rebased", {"rebase": "2025-02-01"}), ("calc", "level", "Scaled", {"scale": 10})]}
    spec = charts.build_chart(definition, by, store)
    assert spec["series"][0]["y"] == [50.0, 100.0, 150.0]
    assert spec["series"][1]["y"] == [10.0, 20.0, 30.0]
    assert "rebase" not in spec["series"][0] and "scale" not in spec["series"][1]
    assert spec["source"] == "INE; EconPulse calculation"


# ---------------------------------------------------------------- pages

def test_regions_and_international_pages_build(tmp_path):
    store = Store(tmp_path / "data")
    q = pd.date_range("2024-01-01", periods=11, freq="QS")
    store.save_series("unemployment_epa", pd.Series(np.linspace(12, 10, 11), index=q))
    store.save_series("unemployment_madrid", pd.Series(np.linspace(9, 8, 11), index=q))
    store.save_series("unemployment_andalucia", pd.Series(np.linspace(17, 15, 11), index=q))
    store.save_series("hicp", monthly(np.linspace(2, 5, 20)))
    store.save_series("hicp_de", monthly(np.linspace(2, 3, 20)))
    indicators = load_registry()

    regions = pages.build_page("regions", indicators, store)
    table = regions["blocks"][0]["tables"][0]
    assert [r["label"] for r in table["rows"]][:3] == ["Spain", "Andalucía", "Aragón"]
    assert cells(table, "Madrid")[0] == "8.00%"
    ranking = next(c for c in regions["charts"] if c["id"] == "unemployment-regions")
    assert ranking["series"][0]["x"] == ["Andalucía", "Madrid"] and ranking["ref_lines"][0]["label"] == "Spain"

    intl = pages.build_page("international", indicators, store)
    peers = intl["blocks"][0]["tables"][0]
    assert cells(peers, "Spain")[1] == "5.0%" and cells(peers, "Germany")[1] == "3.0%"
    assert cells(peers, "United States")[1] == "–"
