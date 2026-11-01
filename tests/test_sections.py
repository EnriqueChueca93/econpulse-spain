"""Section pages: econvitals-style tables, page definitions and their build (no network)."""

import numpy as np
import pandas as pd
import pytest

from econpulse import charts, pages
from econpulse.build import SECTION_PAGES, build_site
from econpulse.registry import Indicator, load_registry
from econpulse.snapshot import summarize
from econpulse.sources import derived
from econpulse.store import Store
from econpulse.tables import AvgChange, Change, Contribution, Data, Heading, Level, Row, Table, build_table


def ind(**kw):
    base = dict(label=kw["id"], label_es=kw["id"] + " (es)", section="inflation", source="fake", key=kw["id"],
                freq="M", unit="index")
    return Indicator(**{**base, **kw})


def monthly(values, start="2015-01-01"):
    return pd.Series(values, index=pd.date_range(start, periods=len(values), freq="MS"), dtype="float64")


def quarterly(values, start="2015-01-01"):
    return pd.Series(values, index=pd.date_range(start, periods=len(values), freq="QS"), dtype="float64")


@pytest.fixture
def store(tmp_path):
    return Store(tmp_path / "data")


def cells(table: dict, label: str) -> list[str]:
    return next(r["cells"] for r in table["rows"] if r.get("label") == label)


# ---------------------------------------------------------------- tables

def test_change_columns_annualise_short_horizons(store):
    # 1% a month, every month: every annualised horizon is 1.01^12 - 1 = 12.7%.
    store.save_series("p", monthly(100 * 1.01 ** np.arange(60)))
    table = Table("Prices", "% change", [Change("1-mo ann.", 1, True), Change("3-mo ann.", 3, True),
                                          Change("1-mo", 1), Change("12-mo", 12)], [Row("p", "P")])
    out = build_table(table, Data([ind(id="p")], store))
    assert cells(out, "P") == ["12.7", "12.7", "1.0", "12.7"]
    assert out["columns"] == ["1-mo ann.", "3-mo ann.", "1-mo", "12-mo"]
    assert out["caption"] == "% change · through Dec 2019" and out["through"] == "Dec 2019"


def test_unadjusted_rows_show_only_annual_changes(store):
    store.save_series("p", monthly(100 * 1.01 ** np.arange(60)))
    table = Table("T", "%", [Change("1-mo ann.", 1, True), Change("12-mo", 12)], [Row("p", "P", season="raw")])
    assert cells(build_table(table, Data([ind(id="p")], store)), "P") == ["–", "12.7"]


def test_our_seasonal_adjustment_removes_a_monthly_pattern(store):
    t = np.arange(120)
    store.save_series("p", monthly(100 * np.exp(0.002 * t + 0.03 * np.sin(2 * np.pi * t / 12))))
    table = Table("T", "%", [Change("1-mo ann.", 1, True)], [Row("p", "Ours", season="ours"), Row("p", "As is")])
    out = build_table(table, Data([ind(id="p")], store))
    # The trend is 0.2% a month = 2.4% annualised; unadjusted, the seasonal swing dominates.
    assert float(cells(out, "Ours")[0]) == pytest.approx(2.4, abs=0.3)
    assert abs(float(cells(out, "As is")[0].replace("−", "-")) - 2.4) > 5


def test_published_rates_fill_only_the_annual_column_at_their_own_precision(store):
    store.save_series("r", quarterly([3.04, 3.05] * 10))
    table = Table("T", "%", [Change("q/q", 3), Change("y/y", 12)], [Row("r", "Rate", is_rate=True)])
    assert cells(build_table(table, Data([ind(id="r", freq="Q", unit="%", decimals=2)], store)), "Rate") == ["–", "3.05"]


def test_quarterly_row_skips_monthly_horizons(store):
    store.save_series("q", quarterly(100 * 1.01 ** np.arange(20)))
    table = Table("T", "%", [Change("1-mo", 1), Change("3-mo", 3), Change("12-mo", 12)], [Row("q", "Q")])
    assert cells(build_table(table, Data([ind(id="q", freq="Q")], store)), "Q") == ["–", "1.0", "4.1"]


def test_level_columns_and_their_headers(store):
    store.save_series("u", monthly(np.linspace(12.0, 10.0, 25)))
    store.save_series("e", quarterly([15.0, 15.5, 16.0, 16.5, 17.0]))
    by = [ind(id="u", unit="%", decimals=1), ind(id="e", freq="Q", unit="%", decimals=1)]
    cols = [Level("latest"), Level("prev"), Level("year")]
    monthly_only = build_table(Table("T", "%", cols, [Row("u", "U")]), Data(by, store))
    assert monthly_only["columns"] == ["Latest", "1-mo ago", "1-yr ago"]
    assert cells(monthly_only, "U") == ["10.0%", "10.1%", "11.0%"]
    quarterly_only = build_table(Table("T", "%", cols, [Row("e", "E")]), Data(by, store))
    assert quarterly_only["columns"][1] == "1-qtr ago" and cells(quarterly_only, "E") == ["17.0%", "16.5%", "15.0%"]
    mixed = build_table(Table("T", "%", cols, [Row("u", "U"), Row("e", "E")]), Data(by, store))
    assert mixed["columns"][1] == "Previous"


def test_level_of_a_transform(store):
    store.save_series("w", quarterly(100 * 1.04 ** (np.arange(12) / 4)))
    table = Table("T", "%", [Level("latest")], [Row("w", "Wages", transform="yoy")])
    assert cells(build_table(table, Data([ind(id="w", freq="Q", unit="€")], store)), "Wages") == ["4.0%"]


def test_average_monthly_change(store):
    store.save_series("a", monthly(np.arange(36) * 10.0 + 1000))
    table = Table("T", "k", [AvgChange("1-mo", 1), AvgChange("3-mo", 3), AvgChange("12-mo", 12)],
                  [Row("a", "Adjusted"), Row("a", "Raw", season="raw")])
    out = build_table(table, Data([ind(id="a", unit="thousands")], store))
    assert cells(out, "Adjusted") == ["10.0", "10.0", "10.0"]
    assert cells(out, "Raw") == ["–", "–", "10.0"]


def test_contribution_rows_and_lagging_rows(store):
    store.save_series("gdp", quarterly(100 * 1.006 ** np.arange(12)))
    store.save_series("dom_q", quarterly([0.5] * 12))
    store.save_series("ext_q", quarterly([0.1] * 12))
    store.save_series("late", quarterly(100 * 1.01 ** np.arange(11)))  # one quarter behind
    by = [ind(id=i, freq="Q", unit="pp" if "_" in i else "index") for i in ("gdp", "dom_q", "ext_q", "late")]
    table = Table("Real growth", "%", [Change("q/q", 3), Contribution("Contrib. q/q", "q")], [
        Row("gdp", "GDP", contrib={"q": "dom_q"}),
        Heading("Spending"),
        Row(None, "Net exports", contrib={"q": "ext_q"}, label_es="Demanda externa"),
        Row("late", "Lagging"),
    ])
    out = build_table(table, Data(by, store))
    assert cells(out, "GDP") == ["0.6", "0.5"]
    assert cells(out, "Net exports") == ["–", "0.1"]
    rows = {r["label"]: r for r in out["rows"]}
    assert rows["Spending"]["heading"] is True
    assert rows["Net exports"]["label_es"] == "Demanda externa"
    assert rows["Lagging"]["period_note"] == "Q3 2017" and rows["GDP"]["period_note"] == ""
    assert out["through"] == "Q4 2017"


def test_table_without_data_is_skipped(store):
    assert build_table(Table("T", "%", [Change("12-mo", 12)], [Row("missing")]), Data([ind(id="missing")], store)) is None


# ---------------------------------------------------------------- derived, snapshot, chart options

def test_deflate_uses_complete_periods_only():
    wages = quarterly([1000.0, 1100.0], start="2026-01-01")
    prices = monthly([100, 100, 100, 110, 110, 110, 120], start="2026-01-01")  # July alone: Q3 incomplete
    out = derived.deflate({"w": wages, "p": prices}, "w", "p", period="Q")
    assert out.tolist() == [1000.0, 1000.0]


def test_snapshot_skips_a_transform_that_cannot_be_computed():
    short = monthly(np.arange(24) * 5.0 + 100, start="2024-01-01")  # too short to seasonally adjust
    item = summarize(ind(id="a", unit="thousands", transforms=("sa_diff", "diff_yoy")), short, {})
    assert [v["transform"] for v in item["values"]] == ["diff_yoy"]


def test_chart_series_options_and_frequency(store):
    store.save_series("q", quarterly(100 * 1.01 ** np.arange(20)))
    store.save_series("m", monthly(np.ones(60)))
    definition = {"id": "c", "title": "C", "subtitle": "S", "kind": "bar", "unit": "%", "decimals": 1,
                  "start": "2015-01-01", "series": [("q", "pop", "Q"), ("m", "level", "M", {"kind": "line", "color": "ink"})]}
    spec = charts.build_chart(definition, {"q": ind(id="q", freq="Q"), "m": ind(id="m")}, store)
    assert spec["series"][1]["kind"] == "line" and spec["series"][1]["color"] == "ink"
    assert "kind" not in spec["series"][0]
    assert spec["freq"] == "M"


# ---------------------------------------------------------------- page definitions and build

def test_pages_reference_real_indicators():
    known = {i.id for i in load_registry()}
    for section in pages.PAGES:
        assert section in SECTION_PAGES
        missing = pages.page_indicator_ids(section) - known
        assert not missing, f"{section}: {missing}"


def test_page_ids_are_unique():
    for section, blocks in pages.PAGES.items():
        block_ids = [b["id"] for b in blocks]
        chart_ids = [c["id"] for b in blocks for c in b.get("charts", []) if not callable(c)]
        assert len(set(block_ids)) == len(block_ids), section
        assert len(set(chart_ids)) == len(chart_ids), section


def test_section_page_build_degrades_with_partial_data(tmp_path):
    store = Store(tmp_path / "data")
    store.save_series("gdp", quarterly(100 * 1.006 ** np.arange(40), start="2016-01-01"))
    store.save_catalog({"gdp": {"status": "ok", "fetched_at": "2026-10-30T12:00:00+00:00", "last_date": "2025-10-01"}})
    indicators = load_registry()

    page = pages.build_page("gdp", indicators, store)
    assert [b["id"] for b in page["blocks"]] == ["growth"]  # productivity block has no data: dropped
    table = page["blocks"][0]["tables"][0]
    assert cells(table, "GDP") == ["0.6", "2.4", "–", "–"]
    assert cells(table, "Household consumption") == ["–", "–", "–", "–"]
    assert {c["id"] for c in page["charts"]} == {"gdp-growth", "gdp-contributions"}

    build_site(indicators, store, site_dir=tmp_path / "site")
    gdp_html = (tmp_path / "site" / "gdp.html").read_text(encoding="utf-8")
    assert "GDP and its components" in gdp_html and 'class="data-table stat-table"' in gdp_html
    assert 'src="data/charts-gdp.js?v=' in gdp_html
    assert (tmp_path / "site" / "data" / "charts-gdp.js").exists()
    # A page with no data shows the placeholder (Fiscal always has the Commission's shipped DSA figures).
    housing_html = (tmp_path / "site" / "housing.html").read_text(encoding="utf-8")
    assert "arrive in Batch 6" in housing_html and "plotly" not in housing_html
