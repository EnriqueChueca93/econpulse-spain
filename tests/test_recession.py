"""Batch 36: the Sahm and Michez rules on Spanish data, their track record against the AEE's recessions, and the
Spanish Michez thresholds (no network)."""

import pandas as pd
import pytest

from econpulse import recession
from econpulse.registry import load_registry
from econpulse.store import Store
from econpulse.tables import Data


def _data(tmp_path) -> Data:
    return Data(load_registry(), Store(tmp_path / "data"))


def test_sahm_indicator_is_the_rise_above_the_previous_years_low(tmp_path):
    months = pd.date_range("2000-01-01", "2002-12-01", freq="MS")
    u = pd.Series(10.0, index=months)
    u[u.index >= "2002-01-01"] = 11.2                    # unemployment jumps 1.2 points in January 2002
    store = Store(tmp_path / "data")
    store.save_series("unemployment_monthly", u)
    s = recession.sahm(Data(load_registry(), store))
    assert s["2001-12-01"] == pytest.approx(0.0)
    assert s["2002-01-01"] == pytest.approx(0.4)          # one month of 11.2 in the 3-month average
    assert s["2002-03-01"] == pytest.approx(1.2)
    assert recession.signals(s, 0.5) == [pd.Timestamp("2002-02-01")]


def test_track_record_counts_early_late_ongoing_and_false_signals():
    quarters = pd.date_range("1990-01-01", "2021-10-01", freq="QS")
    x = pd.Series(0.0, index=quarters)
    x["1991-10-01":"1993-07-01"] = 1.0                    # two quarters before the 1992 recession (starts Q2 1992)
    x["2001-01-01":"2001-04-01"] = 1.0                    # no recession follows: a false alarm
    x["2008-10-01":"2013-04-01"] = 1.0                    # one quarter into 2008-09, and still on when 2011 starts
    x["2020-04-01"] = 1.0                                 # one quarter into 2020
    x["2021-07-01"] = 1.0                                 # in the data's last year: too soon to call it false
    record = recession.track_record(x, 0.5, "Q")
    rows = record["recessions"]
    assert [r["lag"] for r in rows] == [-2, 1, None, 1]
    assert rows[2]["signal"] is None and rows[2]["on_since"] == pd.Timestamp("2008-10-01")
    assert record["false_alarms"] == [pd.Timestamp("2001-01-01")]
    assert record["recent"] == [pd.Timestamp("2021-07-01")]
    assert recession.track_record(x, 0.5, "Q", judge_recent=True)["false_alarms"][-1] == pd.Timestamp("2021-07-01")


def test_the_vacancy_indicator_never_reaches_across_the_2010_break(tmp_path):
    data = _data(tmp_path)
    months = pd.date_range("2002-01-01", "2011-12-01", freq="MS")
    data.store.save_series("unemployment_monthly", pd.Series(10.0, index=months).where(months < "2009-01-01", 11.0))
    quarters = pd.date_range("2002-01-01", "2011-10-01", freq="QS")
    v = pd.Series(0.4, index=quarters).where(quarters < recession.VACANCY_BREAK, 0.8)   # the level doubles at the break
    v[v.index >= "2011-01-01"] = 0.7
    data.cache["recession:vacancy_rate"] = v
    m = recession.michez(data)
    assert m.loc["2010-01-01", "v"] == pytest.approx(0.0) and m.loc["2010-10-01", "v"] == pytest.approx(0.0)
    assert m.loc["2011-01-01", "v"] == pytest.approx(0.1)   # a fall within the new level counts


def test_spain_thresholds_follow_the_papers_method(tmp_path):
    """Lowest threshold with no false alarm, highest with no missed recession, over 2003-2021."""
    quarters = pd.date_range("2003-01-01", "2026-04-01", freq="QS")
    x = pd.Series(0.0, index=quarters)
    x["2005-10-01"] = 0.039                               # a blip no recession followed
    x["2007-10-01":"2009-01-01"] = 0.17                   # 2008-09
    x["2010-07-01":"2012-10-01"] = 0.25                   # 2011-13
    x["2013-07-01"] = 0.09                                # still high just after the recession: not a new signal
    x["2020-04-01":"2020-10-01"] = 0.152                  # 2020
    x["2024-01-01"] = 0.5                                 # after 2021: out of sample, doesn't move the thresholds
    data = _data(tmp_path)
    data.cache["recession:michez"] = pd.DataFrame({"u": x, "v": x, "x": x})
    assert recession.spain_thresholds(data) == (0.04, 0.15)
    assert recession.probability(0.095, 0.04, 0.15) == pytest.approx(0.5)
    assert recession.probability(0.02, 0.04, 0.15) == 0 and recession.probability(0.3, 0.04, 0.15) == 1


def test_michez_indicator_needs_both_unemployment_up_and_vacancies_down(tmp_path):
    data = _data(tmp_path)
    months = pd.date_range("2002-01-01", "2006-12-01", freq="MS")
    u = pd.Series(10.0, index=months)
    u[u.index >= "2005-01-01"] = 11.0                     # unemployment up a point from 2005
    data.store.save_series("unemployment_monthly", u)
    quarters = pd.date_range("2002-01-01", "2006-10-01", freq="QS")
    v = pd.Series(0.6, index=quarters)
    v[v.index >= "2005-07-01"] = 0.5                      # vacancies down 0.1 points from Q3 2005
    data.cache["recession:vacancy_rate"] = v
    m = recession.michez(data)
    assert m.loc["2005-01-01", "u"] == pytest.approx(1.0) and m.loc["2005-01-01", "x"] == pytest.approx(0.0)
    assert m.loc["2005-07-01", "x"] == pytest.approx(0.1)   # both moved: the smaller one, vacancies'
