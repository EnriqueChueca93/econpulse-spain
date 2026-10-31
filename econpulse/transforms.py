"""Standard transformations of a stored series.

Monthly, quarterly and annual series are first put on a gap-free calendar, so a
missing period gives a missing result instead of silently comparing the wrong dates.

    level     the series as published
    pop       % change on the previous period (m/m, q/q)
    yoy       % change on the same period a year earlier
    ann3m     3-month % change, annualised (monthly series)
    saar      q/q % change, annualised (quarterly series)
    diff      change on the previous period, in the series' own units
    diff_yoy  change on a year earlier, in the series' own units
    sum_1y    total over the past year (12 months, 4 quarters), for flows like tourist arrivals
    avg_1y    average over the past year, e.g. a quarterly deficit as a share of GDP

Prefix sa_ (sa_level, sa_pop, sa_ann3m, sa_saar, sa_diff) applies EconPulse's own
seasonal adjustment first (see seasonal.py), for series published unadjusted.
"""

import pandas as pd

from . import seasonal

FREQS = ("D", "M", "Q", "A")
PERIODS_PER_YEAR = {"M": 12, "Q": 4, "A": 1}
_CALENDAR = {"M": "MS", "Q": "QS", "A": "YS"}

SA_PREFIX = "sa_"
_BASE_TRANSFORMS = ("level", "pop", "yoy", "ann3m", "saar", "diff", "diff_yoy", "sum_1y", "avg_1y")
_SA_TRANSFORMS = tuple(SA_PREFIX + t for t in ("level", "pop", "ann3m", "saar", "diff"))
TRANSFORMS = _BASE_TRANSFORMS + _SA_TRANSFORMS
PERCENT_TRANSFORMS = {"pop", "yoy", "ann3m", "saar", "sa_pop", "sa_ann3m", "sa_saar"}
DIFF_TRANSFORMS = {"diff", "diff_yoy", "sa_diff"}


def regular(s: pd.Series, freq: str) -> pd.Series:
    """Reindex to a gap-free period-start calendar (daily series are left as they are)."""
    if freq in _CALENDAR and not s.empty:
        return s.asfreq(_CALENDAR[freq])
    return s


def year_ago(s: pd.Series, freq: str) -> pd.Series:
    """The value one year before each observation (last available on or before, for daily data)."""
    if freq in PERIODS_PER_YEAR:
        return s.shift(PERIODS_PER_YEAR[freq])
    base = s.reindex(s.index - pd.DateOffset(years=1), method="ffill")
    return pd.Series(base.to_numpy(), index=s.index)


def apply(name: str, s: pd.Series, freq: str) -> pd.Series:
    if name not in TRANSFORMS:
        raise ValueError(f"Unknown transform {name!r}; choose from {TRANSFORMS}")
    if freq not in FREQS:
        raise ValueError(f"Unknown frequency {freq!r}; choose from {FREQS}")
    if name.startswith(SA_PREFIX):
        s, name = seasonal.adjust(s, freq), name[len(SA_PREFIX):]
    r = regular(s.sort_index(), freq)
    if name == "level":
        out = r
    elif name == "pop":
        out = (r / r.shift(1) - 1) * 100
    elif name == "yoy":
        out = (r / year_ago(r, freq) - 1) * 100
    elif name == "ann3m":
        if freq != "M":
            raise ValueError("ann3m needs a monthly series")
        out = ((r / r.shift(3)) ** 4 - 1) * 100
    elif name == "saar":
        if freq != "Q":
            raise ValueError("saar needs a quarterly series")
        out = ((r / r.shift(1)) ** 4 - 1) * 100
    elif name == "diff":
        out = r.diff(1)
    elif name in ("sum_1y", "avg_1y"):
        if freq not in ("M", "Q"):
            raise ValueError(f"{name} needs a monthly or quarterly series")
        window = r.rolling(PERIODS_PER_YEAR[freq], min_periods=PERIODS_PER_YEAR[freq])
        out = window.sum() if name == "sum_1y" else window.mean()
    else:  # diff_yoy
        out = r - year_ago(r, freq)
    return out.dropna()


def label(name: str, freq: str) -> str:
    """Short label shown next to a transformed value, e.g. 'q/q' or 'y/y'.

    Changes (diff, diff_yoy) share the labels of the % changes; their display
    carries an explicit sign and unit instead ('+465.5k y/y').
    """
    if name.startswith(SA_PREFIX):
        return f"{label(name[len(SA_PREFIX):], freq)} SA".strip()
    if name in ("pop", "diff"):
        return {"D": "d/d", "M": "m/m", "Q": "q/q", "A": "y/y"}[freq]
    if name in ("sum_1y", "avg_1y"):
        span = "12-mo" if freq == "M" else "4-qtr"
        return f"{span} {'total' if name == 'sum_1y' else 'avg.'}"
    return {"level": "", "yoy": "y/y", "diff_yoy": "y/y", "ann3m": "3m ann.", "saar": "q/q ann."}[name]
