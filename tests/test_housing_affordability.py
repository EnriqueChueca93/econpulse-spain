"""Batch 28a: housing affordability, renting and house prices against the comparators (no network)."""

import numpy as np
import pandas as pd

from econpulse import housing, peers
from econpulse.pages import build_page, page_indicator_ids
from econpulse.registry import load_registry
from econpulse.store import Store
from econpulse.tables import Data


def housing_store(tmp_path) -> Store:
    store = Store(tmp_path / "data")
    q = pd.date_range("1987-01-01", "2026-04-01", freq="QS")
    store.save_series("house_price_income", pd.Series(np.linspace(4.0, 8.0, len(q)), index=q))     # average 6.0
    store.save_series("mortgage_effort", pd.Series(30.0, index=q))
    q2 = pd.date_range("2013-01-01", "2026-04-01", freq="QS")
    store.save_series("price_m2_appraisal", pd.Series(np.linspace(1500.0, 2400.0, len(q2)), index=q2))
    m = pd.date_range("2018-01-01", "2026-09-01", freq="MS")
    store.save_series("price_m2_idealista", pd.Series(np.linspace(2000.0, 3000.0, len(m)), index=m))
    store.save_series("es_10y_monthly", pd.Series(3.9, index=m))
    store.save_series("rental_yield", pd.Series(2.8, index=q2))
    store.save_series("housing_return", pd.Series(15.0, index=q2))
    years = pd.date_range("1985-01-01", "2025-01-01", freq="YS")
    store.save_series("tenure_owners", pd.Series(73.3, index=years))
    store.save_series("tenure_renters", pd.Series(20.2, index=years))
    oq = pd.date_range("2010-01-01", "2026-04-01", freq="QS")
    for k, (slug, _) in enumerate(housing.COMPARATORS):
        store.save_series(f"real_hpi_{slug}", pd.Series(np.linspace(90.0, 100.0 + 5 * k, len(oq)), index=oq))
        if slug != "pl":
            store.save_series(f"price_income_{slug}", pd.Series(100.0 + 3 * k, index=oq))
        if slug not in ("pl", "us"):
            store.save_series(f"price_rent_{slug}", pd.Series(110.0 + 2 * k, index=oq))
    return store


def test_the_series_are_registered():
    ids = {i.id for i in load_registry()}
    assert page_indicator_ids("housing") <= ids
    assert {"house_price_income", "mortgage_effort", "rental_yield", "real_hpi_pl", "price_income_us"} <= ids
    assert "price_income_pl" not in ids and "price_rent_pl" not in ids and "price_rent_us" not in ids


def test_affordability_and_renting(tmp_path):
    data = Data(load_registry(), housing_store(tmp_path))
    facts = {f["label"]: f for f in housing.affordability_facts(data)}
    assert facts["An average home costs"]["value"] == "8.0 years" and "6.0 on average since 1987" in facts["An average home costs"]["sub"]
    assert facts["Asking price per m²"]["value"] == "€3,000" and facts["Asking price per m²"]["sub"].startswith("Idealista · Sep 2026")
    renting = {f["label"]: f for f in housing.renting_facts(data)}
    assert renting["Households renting"]["value"] == "20.2%" and "73.3% own" in renting["Households renting"]["sub"]
    assert renting["Gross rental yield"]["sub"].endswith("10-year bond 3.9%")
    chart = housing.price_income_chart(data)
    assert chart["ref_lines"][0]["y"] == 6.0 and chart["series"][0]["x"][0] == "1987-01-01"


def test_valuation_against_the_comparators(tmp_path):
    data = Data(load_registry(), housing_store(tmp_path))
    table = housing.valuation_table(data)
    rows = {r["label"]: r["cells"] for r in table["rows"]}
    assert rows["Spain"][2:] == ["100", "110"] and rows["Poland"][2:] == ["–", "–"] and rows["United States"][3] == "–"
    ranking = housing.price_income_ranking(data)
    assert ranking["ref_lines"] == [{"y": 100, "label": "Long-run average"}] and ranking["series"][0]["x"][0] == "Japan"
    page = build_page("housing", load_registry(), housing_store(tmp_path))
    blocks = {b["id"]: b for b in page["blocks"]}
    assert blocks["valuation"]["picker"] and not blocks["affordability"]["picker"]
    chart = next(c for c in page["charts"] if c["id"] == "real-hpi-peers")
    assert chart["pick"] and [s["country"] for s in chart["series"]][0] == "es" and len(chart["series"]) == 11
    assert peers.IDS["real_hpi"]["jp"] == "real_hpi_jp" and "ea" not in peers.IDS["real_hpi"]
