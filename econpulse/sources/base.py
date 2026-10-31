"""Shared types and helpers for source clients.

Every client exposes ``fetch(key, params) -> FetchResult``. Dates are stored as
the first day of the period: September 2026 -> 2026-09-01, Q3 2026 -> 2026-07-01.
"""

import re
from dataclasses import dataclass, field

import pandas as pd


@dataclass
class FetchResult:
    series: pd.Series                         # DatetimeIndex (period start) -> float
    meta: dict = field(default_factory=dict)  # e.g. {"flash": True}


_QUARTER = re.compile(r"^(\d{4})-?Q([1-4])$")
_MONTH = re.compile(r"^(\d{4})-?M?(\d{2})$")
_DAY = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_YEAR = re.compile(r"^\d{4}$")


def parse_period(label: str) -> pd.Timestamp:
    """Turn '2026-09', '2026-Q3', '2026Q3', '2026M09', '2026' or '2026-10-30' into a period-start date."""
    label = label.strip()
    if m := _QUARTER.match(label):
        return pd.Timestamp(int(m[1]), 3 * int(m[2]) - 2, 1)
    if _DAY.match(label):
        return pd.Timestamp(label)
    if m := _MONTH.match(label):
        return pd.Timestamp(int(m[1]), int(m[2]), 1)
    if _YEAR.match(label):
        return pd.Timestamp(int(label), 1, 1)
    raise ValueError(f"Unrecognised period label: {label!r}")


def make_series(dates, values) -> pd.Series:
    """Build a clean float series: sorted, de-duplicated, no missing values."""
    s = pd.Series(pd.to_numeric(list(values), errors="coerce"), index=pd.DatetimeIndex(list(dates)), dtype="float64")
    s = s[~s.index.duplicated(keep="last")].sort_index().dropna()
    s.index.name = "date"
    if s.empty:
        raise ValueError("Source returned no observations")
    return s
