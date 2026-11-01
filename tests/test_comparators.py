"""Batch 27a: Spain and its eight comparators on the International page (no network)."""

import numpy as np
import pandas as pd

from econpulse import peers
from econpulse.pages import build_page, page_indicator_ids
from econpulse.registry import load_registry
from econpulse.store import Store
from econpulse.tables import Data


def test_the_comparators_and_their_series_are_registered():
    ids = {i.id for i in load_registry()}
    assert [label for _, label in peers.COUNTRIES] == ["Spain", "Euro area", "France", "Germany", "Italy", "Portugal",
                                                       "Poland", "United Kingdom", "United States", "Canada"]
    assert peers.indicator_ids() <= ids and page_indicator_ids("international") <= ids
    assert not {i for i in ids if i.endswith(("_nl", "_jp"))}           # the Netherlands and Japan left the page
    assert [item[1] for item in peers.ranking_items("unemp")][:2] == ["Spain", "France"]   # no euro area bar
    assert peers.euro_area_ref("unemp") == [("unemployment_ea", "Euro area", "level")]
    rows = peers.panel_rows("gdp", "core")
    assert rows[0].highlight and rows[0].ids["gdp"] == ("gdp", "yoy") and "core" not in rows[-1].ids   # Canada


def comparator_store(tmp_path) -> Store:
    store = Store(tmp_path / "data")
    q = pd.date_range("2018-01-01", "2026-07-01", freq="QS")
    after = (q > peers.BASE).astype(float).cumsum()
    for k, (slug, _) in enumerate(peers.COUNTRIES):
        level = 100 + after * (0.5 + 0.1 * k)                          # flat to Q4 2019, then each grows at its pace
        store.save_series(peers.IDS["level"][slug], pd.Series(level, index=q))
        ref = peers.IDS["gdp"][slug]
        if isinstance(ref, str):
            store.save_series(ref, pd.Series(1.0 + 0.2 * k, index=q))
    years = pd.date_range("2020-01-01", f"{peers.ppp_year() + 2}-01-01", freq="YS")
    for k, slug in enumerate(peers.IDS["ppp"]):
        store.save_series(peers.IDS["ppp"][slug], pd.Series(50_000.0 + 5_000 * k, index=years))
    m = pd.date_range("2024-01-01", "2026-09-01", freq="MS")
    for k, (slug, _) in enumerate(peers.COUNTRIES):
        store.save_series(peers.IDS["unemp"][slug], pd.Series(12.0 - k, index=m))
        if isinstance(peers.IDS["hicp"][slug], str):
            store.save_series(peers.IDS["hicp"][slug], pd.Series(np.linspace(2.0, 3.0 + 0.1 * k, len(m)), index=m))
    return store


def test_growth_table_ranks_and_charts(tmp_path):
    data = Data(load_registry(), comparator_store(tmp_path))
    rec = peers.since_2019(data, "de")                                   # Germany, the 4th country: +0.8 a quarter
    assert rec[1] == pd.Timestamp("2026-07-01") and round(rec[0], 1) == round(27 * 0.8, 1)
    table = peers.growth_table(data)
    spain = table["rows"][0]
    assert spain["label"] == "Spain" and spain["highlight"] and spain["cells"][2:] == ["50,000", "100"]
    assert table["rows"][1]["cells"][2:] == ["–", "–"]                     # no GDP per head for the euro area
    assert table["rows"][-1]["cells"][3] == "180"                          # Canada: 90,000 / 50,000
    facts = {f["label"]: f for f in peers.facts(data)}
    assert facts["Unemployment"]["sub"].startswith("the highest of 9")      # Spain's 12% tops the synthetic data
    assert facts["GDP since the end of 2019"]["sub"].startswith("9th largest rise of 9")
    ranking = peers.recovery_ranking(data)
    assert ranking["series"][0]["x"][0] == "Canada" and ranking["ref_lines"][0]["label"] == "Euro area"
    chart = peers.recovery_chart(data)
    assert [s["name"] for s in chart["series"]] == ["Spain", "Euro area", "United States"]
    assert chart["series"][0]["y"][chart["series"][0]["x"].index("2019-10-01")] == 100


def test_international_page_blocks(tmp_path):
    page = build_page("international", load_registry(), comparator_store(tmp_path))
    assert [b["id"] for b in page["blocks"]] == ["peers", "growth", "jobs", "prices-rates"]
    assert {"gdp-since-2019", "gdp-2019-ranking", "ppp-ranking", "unemployment-ranking"} <= {c["id"] for c in page["charts"]}
