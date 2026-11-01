"""Batches 27a and 27b: Spain and its ten comparators on the International page, and the batched requests
that fetch their series (no network)."""

import numpy as np
import pandas as pd
import pytest

from econpulse import peers
from econpulse.pages import build_page, page_indicator_ids
from econpulse.registry import load_registry
from econpulse.store import Store
from econpulse.tables import Data


def test_the_comparators_and_their_series_are_registered():
    ids = {i.id for i in load_registry()}
    assert [label for _, label in peers.COUNTRIES] == ["Spain", "Euro area", "France", "Germany", "Italy", "Netherlands",
                                                       "Portugal", "Poland", "United Kingdom", "United States", "Canada",
                                                       "Japan"]
    assert peers.indicator_ids() <= ids and page_indicator_ids("international") <= ids
    assert {"gdp_growth_nl", "cpi_jp", "weo_debt_ea", "real_pay_jp"} <= ids and "real_pay_ca" not in ids
    assert [item[1] for item in peers.ranking_items("unemp")][:2] == ["Spain", "France"]   # no euro area bar
    assert peers.euro_area_ref("unemp") == [("unemployment_ea", "Euro area", "level")]
    rows = peers.panel_rows("gdp", "core")
    assert rows[0].highlight and rows[0].ids["gdp"] == ("gdp", "yoy") and "core" not in rows[-1].ids   # Japan


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
    assert table["rows"][-1]["cells"][3] == "200"                          # Japan: 100,000 / 50,000
    facts = {f["label"]: f for f in peers.facts(data)}
    assert facts["Unemployment"]["sub"].startswith("the highest of 11")     # Spain's 12% tops the synthetic data
    assert facts["GDP since the end of 2019"]["sub"].startswith("11th largest rise of 11")
    ranking = peers.recovery_ranking(data)
    assert ranking["series"][0]["x"][0] == "Japan" and ranking["ref_lines"][0]["label"] == "Euro area"
    chart = peers.recovery_chart(data)
    assert [s["name"] for s in chart["series"]] == ["Spain", "Euro area", "United States"]
    assert chart["series"][0]["y"][chart["series"][0]["x"].index("2019-10-01")] == 100


def test_international_page_blocks(tmp_path):
    page = build_page("international", load_registry(), comparator_store(tmp_path))
    assert [b["id"] for b in page["blocks"]][:4] == ["peers", "growth", "jobs", "prices-rates"]
    assert {"gdp-since-2019", "gdp-2019-ranking", "ppp-ranking", "unemployment-ranking"} <= {c["id"] for c in page["charts"]}


def test_public_finances_outlook_and_pay(tmp_path, monkeypatch):
    store = comparator_store(tmp_path)
    years = pd.date_range("2015-01-01", "2031-01-01", freq="YS")
    for k, (slug, _) in enumerate(peers.COUNTRIES):
        for m, base in (("growth", 1.0), ("inflation", 2.0), ("unemp", 12.0), ("deficit", -3.0), ("debt", 80.0),
                        ("primary", -1.0), ("ca", 1.0)):
            store.save_series(f"weo_{m}_{slug}", pd.Series(base + (0.1 * k if m != "unemp" else -k * 0.5), index=years))
        if slug != "ca":
            store.save_series(f"real_pay_{slug}", pd.Series(100.0 + np.arange(len(years)) * (0.5 + 0.1 * k), index=years))
            store.save_series(f"productivity_{slug}", pd.Series(50.0 + np.arange(len(years)) * 0.2, index=years))
    store.save_catalog({"weo_growth_es": {"status": "ok", "published": "2026-10-13"}})
    data = Data(load_registry(), store)
    assert peers.weo_edition(data) == "October 2026" and peers.weo_last_year(data) == 2031
    assert peers.interest(data, "es", peers.ppp_year()) == 2.0               # primary -1.0 less balance -3.0
    fin = peers.finances_table(data)
    assert fin["rows"][0]["cells"][:4] == ["−3.0", "−1.0", "2.0", "80.0"] and fin["columns"][-1] == "Debt 2031 (projected)"
    out = peers.outlook_table(data)
    assert out["rows"][0]["cells"] == ["+1.0", "+1.0", "2.0", "2.0", "12.0", "12.0"]
    facts = {f["label"].split(" in ")[0]: f for f in peers.outlook_facts(data)}
    assert facts["Unemployment"]["sub"].startswith("the highest of 11") and facts["Debt"]["value"] == "80% of GDP"
    pay = peers.pay_table(data)
    assert pay["rows"][10]["label"] == "Canada" and pay["rows"][10]["cells"] == ["–"] * 4
    assert peers.interest_ranking(data)["title"] == "Net interest paid by governments"


def test_batched_requests_share_one_answer(monkeypatch):
    from econpulse.sources import dbnomics, imf, oecd

    calls = []

    class R:
        def __init__(self, text=None, payload=None):
            self.text, self._payload = text, payload

        def json(self):
            return self._payload

    xml = ('<m:GenericData xmlns:m="x"><m:DataSet PUBLICATION_DATE="2026-10-13T00:00:00">'
           '<m:Series COUNTRY="ESP"><m:Obs TIME_PERIOD="2025" OBS_VALUE="2.5"/></m:Series>'
           '<m:Series COUNTRY="JPN"><m:Obs TIME_PERIOD="2025" OBS_VALUE="0.7"/></m:Series></m:DataSet></m:GenericData>')
    csv_text = "REF_AREA,FREQ,MEASURE,TIME_PERIOD,OBS_VALUE\nESP,M,UR,2026-08,22.7\nJPN,M,UR,2026-08,4.0\n"
    payload = {"series": {"docs": [{"series_code": "ESP.3.1.0.0.RWCDC", "period": ["2025"], "value": [103.5]},
                                   {"series_code": "JPN.3.1.0.0.RWCDC", "period": ["2025"], "value": [97.6]}]}}

    def get(url, params=None, timeout=None):
        calls.append(url)
        if "imf" in url:
            return R(text=xml)
        if "oecd" in url:
            return R(text=csv_text)
        return R(payload=payload)

    for client in (imf, oecd, dbnomics):
        client.clear_cache()
        monkeypatch.setattr(client.http, "get", get)
    jp = imf.fetch("IMF.RES,WEO/JPN.NGDP_RPCH.A", {"batch": "ESP+JPN"})
    es = imf.fetch("IMF.RES,WEO/ESP.NGDP_RPCH.A", {"batch": "ESP+JPN"})
    assert jp.series.iloc[-1] == 0.7 and es.series.iloc[-1] == 2.5 and es.meta["published"] == "2026-10-13"
    assert oecd.fetch("FLOW/JPN.M.UR", {"batch": "ESP+JPN"}).series.iloc[-1] == 4.0
    assert oecd.fetch("FLOW/ESP.M.UR", {"batch": "ESP+JPN"}).series.iloc[-1] == 22.7
    assert dbnomics.fetch("AMECO/RWCDC/JPN.3.1.0.0.RWCDC", {"batch": "ESP+JPN"}).series.iloc[-1] == 97.6
    assert len(calls) == 3 and calls[0].endswith("/IMF.RES,WEO/ESP+JPN.NGDP_RPCH.A") and "ESP+JPN.M.UR" in calls[1]
    with pytest.raises(ValueError):
        imf.fetch("IMF.RES,WEO/FRA.NGDP_RPCH.A", {"batch": "ESP+JPN"})     # not in the shared answer
    for client in (imf, oecd, dbnomics):
        client.clear_cache()


def test_for_each_over_several_lists():
    from econpulse.registry import expand

    out = expand({"id": "weo_{m}_{slug}", "label": "{name}, {area}", "for_each": [
        [{"m": "growth", "name": "growth"}, {"m": "debt", "name": "debt"}],
        [{"slug": "es", "area": "Spain"}, {"slug": "jp", "area": "Japan"}]]})
    assert [e["id"] for e in out] == ["weo_growth_es", "weo_growth_jp", "weo_debt_es", "weo_debt_jp"]
    assert out[-1]["label"] == "debt, Japan"
