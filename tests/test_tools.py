"""Batch 11: data for the interactive tools, the Bundesbank client and the Tools page (no network)."""

import json

import numpy as np
import pandas as pd

from econpulse import tools
from econpulse.build import build_site
from econpulse.registry import Indicator, load_registry
from econpulse.sources import bundesbank
from econpulse.store import Store
from econpulse.tables import Data


def ind(**kw):
    base = dict(label=kw["id"], label_es=kw["id"], section="gdp", source="fake", key=kw["id"], freq="Q", unit="index")
    return Indicator(**{**base, **kw})


def test_trend_data_starts_in_2005_and_skips_missing(tmp_path):
    store = Store(tmp_path / "data")
    q = pd.date_range("2000-01-01", "2026-07-01", freq="QS")
    store.save_series("gdp", pd.Series(100 * 1.005 ** np.arange(len(q)), index=q))
    out = tools.trend_data(Data([ind(id="gdp")], store))
    assert [s["id"] for s in out] == ["gdp"]  # the other trend series have no data here
    assert out[0]["x"][0] == "2005-01-01" and out[0]["freq"] == "Q" and len(out[0]["x"]) == len(out[0]["y"])


def test_rates_data_aligns_the_four_yields(tmp_path):
    store = Store(tmp_path / "data")
    days = pd.bdate_range("2009-12-28", "2010-01-08")
    for i, name in enumerate(("es_10y", "de_10y", "aaa_1y", "aaa_10y")):
        store.save_series(name, pd.Series(1.0 + i, index=days))
    store.save_series("de_10y", pd.Series(2.0, index=days.drop(pd.Timestamp("2010-01-05"))))  # a missing day
    inds = [ind(id=i, freq="D", unit="%") for i in ("es_10y", "de_10y", "aaa_1y", "aaa_10y")]
    out = tools.rates_data(Data(inds, store))
    assert out["x"][0] == "2010-01-01" and "2010-01-05" not in out["x"]  # from 2010, common days only
    assert len(out["x"]) == len(out["es10"]) == len(out["aaa1"]) == 5


def test_bundesbank_skips_days_without_values():
    text = ("DATAFLOW,BBK_STD_FREQ,TIME_PERIOD,OBS_VALUE,OBS_STATUS\n"
            "BBK:BBSIS(1.0),D,2026-10-30,3.40,\nBBK:BBSIS(1.0),D,2026-10-31,.,K\nBBK:BBSIS(1.0),D,2026-10-29,3.42,\n")
    s = bundesbank.parse(text).series
    assert s.to_dict() == {pd.Timestamp("2026-10-29"): 3.42, pd.Timestamp("2026-10-30"): 3.40}
    assert bundesbank.INCREMENTAL is True


def test_tools_page_builds(tmp_path):
    store = Store(tmp_path / "data")
    q = pd.date_range("2005-01-01", "2026-07-01", freq="QS")
    store.save_series("gdp", pd.Series(100 * 1.005 ** np.arange(len(q)), index=q))
    build_site(load_registry(), store, site_dir=tmp_path / "site")
    site = tmp_path / "site"
    html = (site / "tools.html").read_text(encoding="utf-8")
    assert 'id="trend-series"' in html and 'id="taylor-rstar"' in html and 'id="rates-start"' in html
    assert html.index("assets/app.js") < html.index("assets/tools.js")  # tools.js uses window.EP.render from app.js
    payload = (site / "data" / "tools.js").read_text(encoding="utf-8").split("window.EP.tools = ", 1)[1].rstrip().rstrip(";")
    data = json.loads(payload)
    assert [s["id"] for s in data["trend"]] == ["gdp"] and data["taylor"] is None and data["rates"] is None
    assert (site / "assets" / "tools.js").exists()
    assert 'href="tools.html"' in (site / "index.html").read_text(encoding="utf-8")
