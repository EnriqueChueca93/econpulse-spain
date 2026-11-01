"""Batch 12: forecasts (automatic and by hand) and the data-surprise indexes (no network)."""

from datetime import date

import numpy as np
import pandas as pd
import pytest

from econpulse import forecasts, pages, surprises
from econpulse.registry import Indicator, load_registry
from econpulse.sources import dbnomics, oecd, source_name
from econpulse.store import Store
from econpulse.tables import Data

HAND = """
forecasters:
  - id: bank
    name: Central Bank
    short: Bank
    group: spain
    url: https://example.org/bank
    published: 2026-10-09
    inflation: HICP
    values:
      2026: {gdp: 2.6, inflation: 3.9, unemployment: 10.0, balance: -2.6}
      2027: {gdp: 2.2, inflation: 3.7}
  - id: gov
    name: Government
    short: Gov
    group: spain
    published: 2026-06-29
    note: Deficit excludes one-offs.
    values:
      2026: {gdp: 2.4, unemployment: null, balance: -2.0}
"""


@pytest.fixture
def hand(tmp_path, monkeypatch):
    path = tmp_path / "forecasts.yaml"
    path.write_text(HAND, encoding="utf-8")
    monkeypatch.setattr(forecasts, "FORECASTS_FILE", path)
    return path


def quarterly_gdp(store):
    q = pd.date_range("2025-01-01", "2026-07-01", freq="QS")
    store.save_series("gdp", pd.Series([100.0] * 4 + [102.0] * 3, index=q))


def test_oecd_edition_dates():
    assert forecasts.eo_month("Economic Outlook 119") == date(2026, 6, 1)
    assert forecasts.eo_month("Economic Outlook 118") == date(2025, 12, 1)
    assert forecasts.eo_month("Economic Outlook 120") == date(2026, 12, 1)
    assert forecasts.eo_month("") is None


def test_oecd_labelled_csv_gives_the_edition():
    text = ("STRUCTURE,STRUCTURE_ID,STRUCTURE_NAME,ACTION,REF_AREA,Reference area,MEASURE,Measure,TIME_PERIOD,"
            "Time period,OBS_VALUE,Observation value\n"
            "DATAFLOW,OECD.ECO.MAD:DSD_EO@DF_EO(1.5),Economic Outlook 119,I,ESP,Spain,GDPV_ANNPCT,GDP growth,2027,,1.67,\n"
            "DATAFLOW,OECD.ECO.MAD:DSD_EO@DF_EO(1.5),Economic Outlook 119,I,ESP,Spain,GDPV_ANNPCT,GDP growth,2026,,2.19,\n")
    r = oecd.parse(text)  # the label columns must not count as series dimensions
    assert r.meta == {"edition": "Economic Outlook 119"}
    assert r.series.to_dict() == {pd.Timestamp("2026-01-01"): 2.19, pd.Timestamp("2027-01-01"): 1.67}


def test_dbnomics_update_date_and_provider_credit():
    payload = {"series": {"docs": [{"period": ["2026", "2027"], "value": [1.0, 2.0], "indexed_at": "2026-05-22T01:32:00Z"}]}}
    assert dbnomics.parse(payload).meta == {"source_updated": "2026-05-22"}
    assert source_name("dbnomics", "AMECO/OVGD/ESP.1.1.0.0.OVGD") == "European Commission (via DBnomics)"
    assert source_name("dbnomics", "BEA/NIPA-T10111/A191RO-Q") == "US BEA (via DBnomics)"
    assert source_name("ine", "X") == "INE"


def test_hand_file_skips_missing_values(hand):
    gov = {f.id: f for f in forecasts.load_manual()}["gov"]
    assert gov.values == {2026: {"gdp": 2.4, "balance": -2.0}}
    assert gov.value(2026, "unemployment") is None and gov.inflation == "CPI"


def test_this_years_gdp_from_published_quarters_and_nowcast(tmp_path):
    store = Store(tmp_path / "data")
    quarterly_gdp(store)
    data = Data(load_registry(), store)
    data.cache["nowcast"] = {"quarter": pd.Timestamp("2026-10-01"), "value": 1.0}
    own = forecasts.gdp_this_year(data, 2026)
    assert own["flat"] == pytest.approx(2.0)  # 3 × 102 + 102, over 4 × 100
    assert own["value"] == pytest.approx((3 * 102 + 102 * 1.01) / 400 * 100 - 100)
    assert forecasts.gdp_this_year(data, 2027) is None


def test_forecast_table_and_chart(tmp_path, hand):
    store = Store(tmp_path / "data")
    quarterly_gdp(store)
    years = pd.date_range("2024-01-01", "2027-01-01", freq="YS")
    store.save_series("fc_oecd_gdp", pd.Series([3.0, 2.8, 2.2, 1.7], index=years))
    store.save_series("fc_ec_hicp_index", pd.Series([100.0, 102.0, 105.06, 107.0], index=years))
    data = Data(load_registry(), store)
    data.cache["nowcast"] = {"quarter": pd.Timestamp("2026-10-01"), "value": 1.0}
    t = forecasts.forecast_table(data, 2026)
    by_label = {r["label"]: r for r in t["rows"]}
    assert [r["label"] for r in t["rows"] if r["heading"]] == ["In Spain", "International organisations", "Summary"]
    assert by_label["Central Bank"]["cells"] == ["2.6%", "3.9%", "10.0%", "−2.6%"]
    assert by_label["Central Bank"]["period_note"] == "Oct 2026"
    assert by_label["Government"]["cells"] == ["2.4%", "–", "–", "−2.0%"]
    assert by_label["European Commission"]["cells"][1] == "3.0%"  # HICP index, % change on a year earlier
    assert by_label["Average of the forecasts above"]["cells"][0] == "2.4%"  # (2.6 + 2.4 + 2.2) / 3
    assert by_label["EconPulse: INE's quarters + nowcast"]["cells"][0] == "2.3%"
    assert "the HICP for Bank and Commission" in t["note"] and "Deficit excludes one-offs." in t["note"]
    chart = forecasts.forecast_chart(data, today=date(2026, 10, 31))
    assert chart["series"][0]["x"] == ["Bank", "Gov", "OECD", "Commission", "Average", "EconPulse"]
    assert chart["series"][1]["y"][1] is None  # no 2027 figure from the government
    facts = forecasts.forecast_facts(data, today=date(2026, 10, 31))
    assert facts[0]["label"] == "GDP growth forecast, 2026" and "average of 3" in facts[0]["sub"]
    assert "2.0%" in forecasts.forecast_callout(data, today=date(2026, 10, 31))


def test_one_step_forecasts_use_only_earlier_data():
    rng = np.random.default_rng(1)
    idx = pd.date_range("2005-01-01", periods=200, freq="MS")
    x = [0.0]
    for _ in range(199):
        x.append(1.0 + 0.5 * x[-1] + rng.normal(0, 0.1))
    s = pd.Series(x, index=idx)
    f = surprises.one_step_forecasts(s)
    assert f.iloc[: surprises.MIN_FIT + 1].isna().all() and f.iloc[surprises.MIN_FIT + 2:].notna().all()
    assert (f - s).iloc[-50:].abs().max() < 0.5  # close to the true model
    later = s.copy()
    later.iloc[-1] = 99.0  # a different last figure changes no earlier forecast
    pd.testing.assert_series_equal(surprises.one_step_forecasts(later).iloc[:-1], f.iloc[:-1])


def test_surprises_accumulate_over_four_months():
    months = pd.date_range("2026-01-01", "2026-06-01", freq="MS")
    z = pd.Series([np.nan, 2.0, np.nan, np.nan, np.nan, np.nan], index=months)
    zeros = pd.Series(0.0, index=pd.date_range("2025-10-01", "2026-06-01", freq="MS"))
    idx = surprises.accumulate({"a": z, "b": zeros}, months[-1])
    # February's surprise counts at weight 1, then ¾, ½, ¼, and is gone by June; "b" adds zeros
    # at a total weight of 1 + ¾ + ½ + ¼ = 2.5 every month.
    assert idx["2026-02-01"] == pytest.approx(2.0 / (1 + 2.5))
    assert idx["2026-04-01"] == pytest.approx(0.5 * 2.0 / (0.5 + 2.5))
    assert idx["2026-06-01"] == 0.0


def test_surprise_index_and_sign(tmp_path):
    store = Store(tmp_path / "data")
    rng = np.random.default_rng(2)
    idx = pd.date_range("2005-01-01", "2026-09-01", freq="MS")
    hicp = pd.Series(2 + rng.normal(0, 0.3, len(idx)), index=idx)
    hicp.iloc[-1] += 5  # inflation far above what its history predicted
    store.save_series("hicp", hicp)
    unemp = pd.Series(10 + np.cumsum(rng.normal(0, 0.05, len(idx))), index=idx)
    unemp.iloc[-1] += 1  # a jump in unemployment: a negative activity surprise
    store.save_series("unemployment_monthly", unemp)
    data = Data(load_registry(), store)
    inflation = surprises.surprise_index(data, "inflation")
    assert [r["component"].id for r in inflation["rows"]] == ["hicp"] and inflation["rows"][0]["z"] == 3.0  # clipped
    # The index averages the past four months' surprises, the newest weighted most: the 3 dominates.
    assert inflation["series"].iloc[-1] > 0.5
    activity = surprises.surprise_index(data, "activity")
    assert activity["rows"][0]["z"] < -1
    table = surprises.surprise_table(data, "activity")
    assert table["rows"][0]["label"] == "Unemployment rate, monthly change" and table["columns"][1] == "Forecast"
    facts = surprises.surprise_facts(data)
    assert [f["label"] for f in facts] == ["Activity data vs forecasts", "Inflation data vs forecasts"]
    assert facts[1]["sub"].startswith("above expectations")
    page = pages.build_page("analysis", load_registry(), store)
    ids = [b["id"] for b in page["blocks"]]
    assert "surprises" in ids and "forecasts" in ids
    assert any(c["id"] == "surprises" for c in page["charts"])
