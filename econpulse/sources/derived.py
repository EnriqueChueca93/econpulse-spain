"""Indicators computed from other indicators already in the store.

Key is the operation; params name the inputs. Examples:
    prima de riesgo in bp:   key: subtract   params: {a: es_10y, b: de_10y, scale: 100}
    Brent in euros:          key: divide     params: {a: brent_usd, b: eurusd, fill: 5}
    real wages:              key: deflate    params: {a: wage_cost, b: cpi_index, period: Q}

Inputs are aligned on common dates. For daily data from different calendars,
`fill: n` carries the second input forward up to n days, so a holiday in one
series doesn't drop the observation.
"""

import pandas as pd

from .base import FetchResult


def _align(inputs: dict[str, pd.Series], a: str, b: str, fill: int = 0) -> pd.DataFrame:
    sa, sb = inputs[a], inputs[b]
    if fill:
        sb = sb.reindex(sb.index.union(sa.index)).ffill(limit=fill).reindex(sa.index)
    return pd.DataFrame({"a": sa, "b": sb}).dropna()


def subtract(inputs: dict[str, pd.Series], a: str, b: str, scale: float = 1.0, fill: int = 0) -> pd.Series:
    joined = _align(inputs, a, b, fill)
    return (joined["a"] - joined["b"]) * scale


def divide(inputs: dict[str, pd.Series], a: str, b: str, scale: float = 1.0, fill: int = 0) -> pd.Series:
    joined = _align(inputs, a, b, fill)
    return joined["a"] / joined["b"] * scale


def deflate(inputs: dict[str, pd.Series], a: str, b: str, period: str = "M", scale: float = 100.0) -> pd.Series:
    """a in real terms: divided by the price index b averaged over each of a's periods (M or Q).

    Only complete periods of b are used, so a quarter with one month of prices is left out.
    """
    rule, months = {"M": ("MS", 1), "Q": ("QS", 3)}[period]
    prices = inputs[b].resample(rule)
    complete = prices.count() == months
    joined = pd.DataFrame({"a": inputs[a], "b": prices.mean()[complete]}).dropna()
    return joined["a"] / joined["b"] * scale


OPERATIONS = {"subtract": subtract, "divide": divide, "deflate": deflate}


def inputs_of(params: dict) -> list[str]:
    """Indicator ids this derived indicator depends on."""
    return [params[k] for k in ("a", "b") if k in params]


def compute(key: str, params: dict, inputs: dict[str, pd.Series]) -> FetchResult:
    if key not in OPERATIONS:
        raise ValueError(f"Unknown derived operation: {key!r}")
    series = OPERATIONS[key](inputs, **params).round(6)
    series.index.name = "date"
    if series.empty:
        raise ValueError("Derived series is empty (inputs don't overlap)")
    return FetchResult(series)
