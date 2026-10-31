"""Indicators computed from other indicators already in the store.

Key is the operation; params name the inputs. Examples:
    prima de riesgo in bp:   key: subtract   params: {a: es_10y, b: de_10y, scale: 100}
    Brent in euros:          key: divide     params: {a: brent_usd, b: eurusd, fill: 5}

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


OPERATIONS = {"subtract": subtract, "divide": divide}


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
