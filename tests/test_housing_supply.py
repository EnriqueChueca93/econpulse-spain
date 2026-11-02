"""Batch 28b: building and households, sales, mortgages, wealth and commercial property (no network)."""

import numpy as np
import pandas as pd

from econpulse import housing
from econpulse.pages import PAGES, build_page, page_indicator_ids
from econpulse.registry import load_registry
from econpulse.snapshot import fmt_value
from econpulse.store import Store
from econpulse.tables import Data


def supply_store(tmp_path) -> Store:
    store = Store(tmp_path / "data")
    m = pd.date_range("2000-01-01", "2026-06-01", freq="MS")
    store.save_series("home_starts", pd.Series(np.r_[np.full(84, 60000.0), np.full(len(m) - 84, 10000.0)], index=m))
    store.save_series("protected_share", pd.Series(14.2, index=m))
    store.save_series("home_permits", pd.Series(np.r_[np.full(len(m) - 12, 10000.0), np.full(12, 11000.0)], index=m))
    q = pd.date_range("2002-01-01", "2026-07-01", freq="QS")
    store.save_series("households", pd.Series(14000.0 + 60.0 * np.arange(len(q)), index=q))          # +240k a year
    census = pd.to_datetime(["1981-10-01", "1991-10-01", "2001-10-01", "2011-10-01", "2021-10-01"])
    store.save_series("homes_per_household", pd.Series([1.45, 1.454, 1.521, 1.401, 1.41], index=census))
    q2 = pd.date_range("1995-01-01", "2026-04-01", freq="QS")
    store.save_series("mortgage_ltv", pd.Series(63.7, index=q2))
    store.save_series("mortgage_ltv80", pd.Series(9.6, index=q2))
    store.save_series("mortgage_term", pd.Series(25.4, index=q2))
    npl = pd.Series(1.45, index=q2)
    npl[pd.Timestamp("2014-01-01")] = 6.32
    store.save_series("housing_npl", npl)
    store.save_series("housing_credit_gdp", pd.Series(np.r_[np.linspace(16.0, 63.3, 62), np.linspace(63.0, 30.2, len(q2) - 62)], index=q2))
    store.save_series("housing_wealth", pd.Series(8185.9, index=q2))
    store.save_series("housing_wealth_income", pd.Series(np.r_[960.0, np.full(len(q2) - 1, 752.6)], index=q2))
    store.save_series("financial_wealth_income", pd.Series(np.linspace(180.0, 258.6, len(q2)), index=q2))
    q3 = pd.date_range("2014-01-01", "2026-04-01", freq="QS")
    for slug, k in (("all", 1.0), ("offices", 2.0), ("industrial", 3.0)):
        store.save_series(f"cpp_{slug}", pd.Series(100.0 + k * np.arange(len(q3)) / 4, index=q3))
    store.save_series("bank_cre_share", pd.Series(4.0, index=q3))
    store.save_series("bank_housing_share", pd.Series(29.1, index=q3))
    return store


def test_the_series_are_registered():
    ids = {i.id for i in load_registry()}
    assert page_indicator_ids("housing") <= ids
    assert {"home_starts", "households", "notary_sales_new", "mortgage_ltv80", "housing_wealth", "cpp_prime",
            "bank_cre_share"} <= ids
    by_id = {i.id: i for i in load_registry()}
    assert by_id["mortgage_term"].unit == "years" and by_id["homes_per_household"].freq == "Q"


def test_supply_facts(tmp_path):
    facts = {f["label"]: f for f in housing.supply_facts(Data(load_registry(), supply_store(tmp_path)))}
    starts = facts["Homes started"]
    assert starts["value"] == "120,000" and "14% protected" in starts["sub"] and "720,000 at the 2000 peak" in starts["sub"]
    assert facts["New homes in building permits"]["sub"].endswith("+10.0% on a year")
    assert facts["New households"]["value"] == "+240,000" and "Q3 2026" in facts["New households"]["sub"]
    assert facts["Homes per household"]["value"] == "1.41" and facts["Homes per household"]["sub"] == "2021 census; 1.52 in 2001"


def test_credit_wealth_and_commercial_facts(tmp_path):
    data = Data(load_registry(), supply_store(tmp_path))
    credit = {f["label"]: f for f in housing.credit_facts(data)}
    assert credit["A new mortgage lends"]["value"] == "63.7%" and "9.6% of mortgages" in credit["A new mortgage lends"]["sub"]
    assert credit["Average term"]["value"] == "25.4 years"
    assert credit["Housing loans gone bad"]["sub"].endswith("6.3% at the 2014 peak")
    assert credit["Housing loans"]["value"] == "30.2% of GDP" and "63.3% at the 2010 peak" in credit["Housing loans"]["sub"]
    wealth = {f["label"]: f for f in housing.wealth_facts(data)}
    assert wealth["Housing wealth"]["value"] == "€8.19 trillion" and "7.5 times" in wealth["Housing wealth"]["sub"]
    assert "(9.6 at the 1995 peak)" in wealth["Housing wealth"]["sub"]
    assert wealth["Net financial wealth"]["value"] == "2.6×" and wealth["Net financial wealth"]["sub"].endswith("since 1995")
    commercial = {f["label"]: f for f in housing.commercial_facts(data)}
    assert commercial["Offices"]["value"] == "+1.6%" and "against 100 in 2014" in commercial["Offices"]["sub"]
    assert commercial["Banks' loans for commercial property"]["sub"].endswith("housing loans 29.1%")


def test_the_page_blocks(tmp_path):
    assert [b["id"] for b in PAGES["housing"]][-5:] == ["supply", "sales", "credit", "debt", "commercial"]
    page = build_page("housing", load_registry(), supply_store(tmp_path))
    blocks = {b["id"]: b for b in page["blocks"]}
    building = blocks["supply"]["tables"][0]
    rows = {r["label"]: r["cells"] for r in building["rows"]}
    assert rows["Homes started, past 12 months"] == ["120,000 homes", "120,000 homes"]
    assert rows["New households, over a year"][0] == "240k"
    charts = {c["id"]: c for c in page["charts"]}
    assert charts["home-starts"]["series"][0]["x"][0] >= "1980-12-01"
    assert {"starts-households", "ltv", "property-credit", "housing-npl", "commercial-prices"} <= set(charts)


def test_units():
    assert fmt_value(8185.9, "€ bn", 0) == "€8,186 bn"
    assert fmt_value(1011.2, "%", 0) == "1,011%"
