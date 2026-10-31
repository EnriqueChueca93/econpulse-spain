import pandas as pd
import pytest

from econpulse import transforms


def monthly(values, start="2024-01-01"):
    return pd.Series(values, index=pd.date_range(start, periods=len(values), freq="MS"), dtype="float64")


def quarterly(values, start="2024-01-01"):
    return pd.Series(values, index=pd.date_range(start, periods=len(values), freq="QS"), dtype="float64")


def test_pop_and_yoy_monthly():
    s = monthly([100 + i for i in range(13)])  # Jan 2024 .. Jan 2025
    assert transforms.apply("pop", s, "M").iloc[-1] == pytest.approx((112 / 111 - 1) * 100)
    yoy = transforms.apply("yoy", s, "M")
    assert len(yoy) == 1
    assert yoy.index[0] == pd.Timestamp("2025-01-01")
    assert yoy.iloc[0] == pytest.approx(12.0)


def test_yoy_quarterly_uses_four_periods():
    s = quarterly([100, 101, 102, 103, 110])
    assert transforms.apply("yoy", s, "Q").iloc[-1] == pytest.approx(10.0)


def test_gap_gives_missing_not_wrong_comparison():
    s = monthly([100.0] * 13)
    s = s.drop(pd.Timestamp("2024-01-01"))  # the year-ago observation is missing
    assert transforms.apply("yoy", s, "M").empty


def test_ann3m_and_saar():
    s = monthly([100, 100, 100, 101])
    assert transforms.apply("ann3m", s, "M").iloc[-1] == pytest.approx((1.01 ** 4 - 1) * 100)
    q = quarterly([100, 101])
    assert transforms.apply("saar", q, "Q").iloc[-1] == pytest.approx((1.01 ** 4 - 1) * 100)
    with pytest.raises(ValueError):
        transforms.apply("ann3m", q, "Q")


def test_diff_and_diff_yoy():
    s = quarterly([10.0, 10.5, 11.0, 11.0, 9.5])
    assert transforms.apply("diff", s, "Q").iloc[-1] == pytest.approx(-1.5)
    assert transforms.apply("diff_yoy", s, "Q").iloc[-1] == pytest.approx(-0.5)


def test_daily_yoy_uses_last_value_on_or_before():
    idx = pd.to_datetime(["2025-10-29", "2025-10-31", "2026-10-30"])
    s = pd.Series([1.0, 2.0, 4.0], index=idx)
    # A year before 2026-10-30 is 2025-10-30: no observation, so use 2025-10-29.
    assert transforms.apply("yoy", s, "D").iloc[-1] == pytest.approx(300.0)


def test_unknown_transform_rejected():
    with pytest.raises(ValueError):
        transforms.apply("bogus", monthly([1, 2]), "M")


def test_labels():
    assert transforms.label("pop", "Q") == "q/q"
    assert transforms.label("pop", "M") == "m/m"
    assert transforms.label("diff_yoy", "Q") == "y/y"
    assert transforms.label("level", "D") == ""
