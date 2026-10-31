"""Indicators computed from other indicators already in the store.

Key is the operation; params name the inputs. Example (prima de riesgo, in bp):
    source: derived
    key: subtract
    params: {a: es_10y, b: de_10y, scale: 100}
"""

import pandas as pd

from .base import FetchResult


def subtract(inputs: dict[str, pd.Series], a: str, b: str, scale: float = 1.0) -> pd.Series:
    joined = pd.concat({"a": inputs[a], "b": inputs[b]}, axis=1, join="inner").dropna()
    return (joined["a"] - joined["b"]) * scale


OPERATIONS = {"subtract": subtract}


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
