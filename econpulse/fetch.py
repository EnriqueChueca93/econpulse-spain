"""Fetch every indicator, save it, and record the outcome in the catalog.

A failing source never stops the run: the indicator keeps its last saved data
and is marked "stale" (or "error" if nothing was ever saved).

New data is merged into the stored history: stored observations before the
first new date are kept, everything from that date on is replaced (so revisions
land). Sources that can't serve full history in one request (INCREMENTAL clients)
are asked only for observations since shortly before the last stored date.
"""

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

import pandas as pd

from . import sources
from .config import FETCH_WORKERS
from .registry import Indicator
from .sources import derived
from .sources.base import FetchResult, madrid_today
from .store import Store

# How far before the last stored observation an incremental fetch starts, to pick up revisions.
REFETCH_DAYS = {"D": 10, "M": 95, "Q": 200, "A": 400}


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _reusable_history(ind: Indicator, store: Store, catalog: dict) -> pd.Series | None:
    """Stored history, if it was fetched with the same definition as now."""
    stored = store.load_series(ind.id)
    if stored is None or stored.empty:
        return None
    if catalog.get(ind.id, {}).get("signature") != ind.signature():
        return None
    return stored


def merge(stored: pd.Series | None, new: pd.Series) -> pd.Series:
    if stored is None or stored.empty:
        return new
    merged = pd.concat([stored[stored.index < new.index[0]], new])
    merged.index.name = "date"
    return merged


def _fetch_one(ind: Indicator, stored: pd.Series | None) -> FetchResult:
    client = sources.CLIENTS[ind.source]
    since = None
    if stored is not None and getattr(client, "INCREMENTAL", False):
        since = stored.index[-1] - pd.Timedelta(days=REFETCH_DAYS[ind.freq])
    result = client.fetch(ind.key, ind.params, since=since, freq=ind.freq)
    if ind.scale != 1:
        result.series = result.series * ind.scale
    return result


def _record_success(catalog: dict, ind: Indicator, series: pd.Series, meta: dict) -> None:
    catalog[ind.id] = {
        "status": "ok",
        "fetched_at": _now(),
        "first_date": series.index[0].strftime("%Y-%m-%d"),
        "last_date": series.index[-1].strftime("%Y-%m-%d"),
        "n_obs": int(series.size),
        "signature": ind.signature(),
        **meta,
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
    history = {ind.id: _reusable_history(ind, store, catalog) for ind in remote}

    with ThreadPoolExecutor(max_workers=FETCH_WORKERS) as pool:
        futures = {ind.id: pool.submit(_fetch_one, ind, history[ind.id]) for ind in remote}
        for ind in remote:
            try:
                result = futures[ind.id].result()
                series = merge(history[ind.id], result.series)
                store.save_series(ind.id, series)
                _record_success(catalog, ind, series, result.meta)
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
            _record_success(catalog, ind, result.series, result.meta)
        except Exception as e:  # noqa: BLE001
            _record_failure(catalog, ind, store, e)

    store.save_catalog(catalog)
    return catalog


def is_out_of_date(last_date: str | None, max_age_days: int, today: pd.Timestamp | None = None) -> bool:
    """True if the latest observation is older than expected, i.e. the source may have stopped updating."""
    if not last_date:
        return True
    today = today or pd.Timestamp(madrid_today())
    return (today - pd.Timestamp(last_date)).days > max_age_days
