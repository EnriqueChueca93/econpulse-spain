"""Batch 10 sources: OECD, BIS, BLS, DBnomics, EIA and World Bank parsers, and XY charts (no network)."""

import numpy as np
import pandas as pd
import pytest

from econpulse import charts
from econpulse.registry import Indicator
from econpulse.sources import bis, bls, dbnomics, eia, oecd, worldbank
from econpulse.store import Store


def test_oecd_single_series_and_ambiguity():
    one = ("STRUCTURE,STRUCTURE_ID,ACTION,REF_AREA,FREQ,MEASURE,TIME_PERIOD,OBS_VALUE\n"
           "DATAFLOW,X,I,GBR,M,CPI,2026-08,3.8\nDATAFLOW,X,I,GBR,M,CPI,2026-09,3.6\n")
    s = oecd.parse(one).series
    assert s.index[-1] == pd.Timestamp("2026-09-01") and s.iloc[-1] == 3.6
    two = one + "DATAFLOW,X,I,GBR,M,CORE,2026-09,3.1\n"
    with pytest.raises(ValueError, match="matches 2 series"):
        oecd.parse(two)


def test_bis_skips_missing_values():
    text = ("FREQ,REF_AREA,TIME_PERIOD,OBS_VALUE\nD,US,2026-10-24,NaN\nD,US,2026-10-27,3.875\n"
            "Q,ES,2026-Q1,5.1\n")
    s = bis.parse(text).series
    assert s.to_dict() == {pd.Timestamp("2026-01-01"): 5.1, pd.Timestamp("2026-10-27"): 3.875}


def test_bls_monthly_values_only():
    payload = {"status": "REQUEST_SUCCEEDED", "Results": {"series": [{"seriesID": "LNS14000000", "data": [
        {"year": "2026", "period": "M09", "value": "4.2"},
        {"year": "2026", "period": "M08", "value": "4.3"},
        {"year": "2025", "period": "M13", "value": "4.1"}]}]}}
    s = bls.parse(payload, "LNS14000000").series
    assert s.to_dict() == {pd.Timestamp("2026-08-01"): 4.3, pd.Timestamp("2026-09-01"): 4.2}
    with pytest.raises(ValueError, match="REQUEST_NOT_PROCESSED"):
        bls.parse({"status": "REQUEST_NOT_PROCESSED", "message": ["daily threshold"]}, "X")


def test_dbnomics_drops_na():
    payload = {"series": {"docs": [{"period": ["2026-Q2", "2026-Q3", "2026-Q4"], "value": [2.3, 2.1, "NA"]}]}}
    s = dbnomics.parse(payload).series
    assert s.index[-1] == pd.Timestamp("2026-07-01") and s.iloc[-1] == 2.1


def test_eia_weekly_rows_to_days():
    html = ("<tr><td class='B6'>&nbsp;&nbsp;2026 Oct-19 to Oct-23</td> <td class='B3'>118.82</td> <td class='B3'>115.22</td>"
            " <td class='B3'>117.37</td> <td class='B3'>125.39</td> <td class='B3'>128.30</td> </tr>"
            "<tr><td class='B6'>&nbsp;&nbsp;2026 Oct-26 to Oct-30</td> <td class='B3'>128.12</td> <td class='B3'>123.10</td>"
            " <td class='B3'></td> <td class='B3'></td> <td class='B3'></td> </tr>")
    s = eia.parse(html).series
    assert len(s) == 7
    assert s[pd.Timestamp("2026-10-23")] == 128.30 and s.index[-1] == pd.Timestamp("2026-10-27")


def test_worldbank_link_and_columns():
    html = '<a href="https://thedocs.worldbank.org/en/doc/abc-0050012026/related/CMO-Historical-Data-Monthly.xlsx">Monthly</a>'
    assert worldbank.find_file_url(html).endswith("abc-0050012026/related/CMO-Historical-Data-Monthly.xlsx")
    rows = [("World Bank Commodity Price Data",), (None, "Crude oil, Brent", "Gold"), (None, "($/bbl)", "($/troy oz)"),
            ("2026M08", 110.0, 4300.0), ("2026M09", 120.5, "…")]
    assert worldbank.parse(rows, "Crude oil, Brent").series.iloc[-1] == 120.5
    assert worldbank.parse(rows, "Gold").series.index[-1] == pd.Timestamp("2026-08-01")  # "…" is not a value
    with pytest.raises(ValueError, match="no column"):
        worldbank.parse(rows, "Silver")


def test_xy_chart(tmp_path):
    store = Store(tmp_path / "data")
    q = pd.date_range("2014-01-01", periods=12, freq="QS")
    store.save_series("u", pd.Series(np.linspace(25, 10, 12), index=q))
    store.save_series("v", pd.Series(np.linspace(60, 155, 12), index=q))
    by = {i: Indicator(id=i, label=i, label_es=i, section="labour", source="ine", key=i, freq="Q", unit="%") for i in ("u", "v")}
    spec = charts.build_xy({"id": "b", "kind": "xy", "title": "Beveridge", "subtitle": "S", "start": "2015-01-01",
                            "x": ("u", "level", "Unemployment rate", "%"), "y": ("v", "level", "Vacancies", "k")}, by, store)
    s = spec["series"][0]
    assert spec["kind"] == "xy" and spec["x_label"] == "Unemployment rate" and spec["y_unit"] == "k"
    assert s["text"][0] == "Q1 2015" and len(s["x"]) == len(s["y"]) == len(s["text"]) == 8
    assert spec["source"] == "INE"
