"""Seasonal adjustment for series the source publishes unadjusted (CPI index, registrations).

Method: STL decomposition (statsmodels, robust to outliers such as the 2020 shock)
on the log of the series, estimated from 2010 onwards. This is an EconPulse
estimate, not an official figure, and it is labelled "SA" wherever it is shown.
"""

import numpy as np
import pandas as pd
from statsmodels.tsa.seasonal import STL

PERIODS = {"M": 12, "Q": 4}
CALENDAR = {"M": "MS", "Q": "QS"}
SEASONAL_WINDOW = {"M": 13, "Q": 7}  # longer window = steadier seasonal factors
ESTIMATION_START = pd.Timestamp("2010-01-01")


def adjust(s: pd.Series, freq: str, start: pd.Timestamp = ESTIMATION_START) -> pd.Series:
    """Seasonally adjusted version of a monthly or quarterly series."""
    if freq not in PERIODS:
        raise ValueError(f"Seasonal adjustment needs a monthly or quarterly series, not {freq!r}")
    r = s[s.index >= start].sort_index().asfreq(CALENDAR[freq])
    if r.isna().any():
        raise ValueError("Seasonal adjustment needs a series without gaps")
    if len(r) < 4 * PERIODS[freq]:
        raise ValueError("Seasonal adjustment needs at least four years of data")
    positive = bool((r > 0).all())
    y = np.log(r) if positive else r
    fit = STL(y, period=PERIODS[freq], seasonal=SEASONAL_WINDOW[freq], robust=True).fit()
    adjusted = y - fit.seasonal
    out = np.exp(adjusted) if positive else adjusted
    out.name = s.name
    out.index.name = s.index.name
    return out
