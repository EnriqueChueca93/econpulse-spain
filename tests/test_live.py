"""Smoke tests against the real APIs. Skipped by default; run with: pytest -m live"""

import pandas as pd
import pytest

from econpulse.sources import ecb, eurostat, ine

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
