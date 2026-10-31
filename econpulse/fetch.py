"""Fetch every indicator, save it, and record the outcome in the catalog.

A failing source never stops the run: the indicator keeps its last saved data
and is marked "stale" (or "error" if nothing was ever saved).
"""

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

import pandas as pd

from . import sources
from .config import FETCH_WORKERS
from .registry import Indicator
from .sources import derived
from .sources.base import FetchResult
from .store import Store


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _fetch_one(ind: Indicator) -> FetchResult:
    return sources.CLIENTS[ind.source].fetch(ind.key, ind.params)


def _record_success(catalog: dict, ind: Indicator, result: FetchResult) -> None:
    s = result.series
    catalog[ind.id] = {
        "status": "ok",
        "fetched_at": _now(),
        "first_date": s.index[0].strftime("%Y-%m-%d"),
        "last_date": s.index[-1].strftime("%Y-%m-%d"),
        "n_obs": int(s.size),
        **result.meta,
    }


def _record_failure(catalog: dict, ind: Indicator, store: Store, error: Exception) -> None:
    entry = dict(catalog.get(ind.id, {}))
    has_data = store.series_path(ind.id).exists()
    entry.update(status="stale" if has_data else "error", error=f"{type(error).__name__}: {error}", failed_at=_now())
    catalog[ind.id] = entry


def fetch_all(indicators: list[Indicator], store: Store | None = None, only: set[str] | None = None) -> dict:
    """Fetch the given indicators (or just those in ``only``) and return the updated catalog."""
    store = store or Store()
    catalog = store.load_catalog()
    selected = [i for i in indicators if only is None or i.id in only]
    remote = [i for i in selected if not i.is_derived]

    with ThreadPoolExecutor(max_workers=FETCH_WORKERS) as pool:
        futures = {ind.id: pool.submit(_fetch_one, ind) for ind in remote}
        for ind in remote:
            try:
                result = futures[ind.id].result()
                store.save_series(ind.id, result.series)
                _record_success(catalog, ind, result)
            except Exception as e:  # noqa: BLE001 - one bad source must not stop the rest
                _record_failure(catalog, ind, store, e)

    # Derived indicators run after the remote ones, in registry order.
    for ind in (i for i in selected if i.is_derived):
        try:
            inputs = {}
            for dep in derived.inputs_of(ind.params):
                series = store.load_series(dep)
                if series is None:
                    raise ValueError(f"input {dep!r} has no data")
                inputs[dep] = series
            result = derived.compute(ind.key, ind.params, inputs)
            store.save_series(ind.id, result.series)
            _record_success(catalog, ind, result)
        except Exception as e:  # noqa: BLE001
            _record_failure(catalog, ind, store, e)

    store.save_catalog(catalog)
    return catalog


def is_out_of_date(last_date: str | None, max_age_days: int, today: pd.Timestamp | None = None) -> bool:
    """True if the latest observation is older than expected, i.e. the source may have stopped updating."""
    if not last_date:
        return True
    today = today or pd.Timestamp.today().normalize()
    return (today - pd.Timestamp(last_date)).days > max_age_days
