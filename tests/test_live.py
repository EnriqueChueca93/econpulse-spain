"""Smoke tests against the real APIs. Skipped by default; run with: pytest -m live"""

import pandas as pd
import pytest

from econpulse.sources import bde, dbnomics, ecb, eurostat, fred, ine, oecd, ree, segsocial

pytestmark = pytest.mark.live


def recent(series: pd.Series, days: int) -> bool:
    return (pd.Timestamp.today() - series.index[-1]).days < days


def test_ine_cpi():
    s = ine.fetch("IPC290750").series
    assert len(s) > 600 and recent(s, 90)


def test_eurostat_unemployment():
    s = eurostat.fetch("une_rt_m", {"geo": "ES", "s_adj": "SA", "age": "TOTAL", "sex": "T", "unit": "PC_ACT"}).series
    assert 0 < s.iloc[-1] < 40 and recent(s, 120)


def test_ecb_deposit_rate():
    s = ecb.fetch("FM/D.U2.EUR.4F.KR.DFR.LEV").series
    assert -1 < s.iloc[-1] < 10 and recent(s, 10)


def test_bde_10y_recent_window():
    s = bde.fetch("DPUG0B1F0ZP", freq="D", since=pd.Timestamp.today() - pd.Timedelta(days=30)).series
    assert 0 < s.iloc[-1] < 15 and recent(s, 10)


def test_bde_monthly():
    s = bde.fetch("DPU1JA0D000_TVA", freq="M").series
    assert len(s) > 100 and recent(s, 120)


def test_segsocial_registrations():
    s = segsocial.fetch("TOTAL SISTEMA").series
    assert 15e6 < s.iloc[-1] < 30e6 and recent(s, 100)


def test_fred_brent():
    s = fred.fetch("DCOILBRENTEU").series
    assert 10 < s.iloc[-1] < 400 and recent(s, 14)


def test_ree_price_recent_window():
    s = ree.fetch("spot_price", since=pd.Timestamp.today() - pd.Timedelta(days=5)).series
    assert len(s) >= 3 and recent(s, 3)


def test_forecast_feeds():
    """The OECD Economic Outlook names its edition; AMECO runs past this year and says when it changed."""
    r = oecd.fetch("OECD.ECO.MAD,DSD_EO@DF_EO,/ESP.GDPV_ANNPCT.A", {"edition": True})
    assert r.meta["edition"].startswith("Economic Outlook") and r.series.index[-1].year > pd.Timestamp.now().year
    r = dbnomics.fetch("AMECO/ZUTN/ESP.1.0.0.0.ZUTN")
    assert r.series.index[-1].year > pd.Timestamp.now().year and len(r.meta["source_updated"]) == 10
