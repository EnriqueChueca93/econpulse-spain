"""Batch 25c: labour-force rates by group and participation at a fixed age mix (no network)."""

import itertools

import numpy as np
import pandas as pd
import pytest

from econpulse import demography
from econpulse.pages import build_page, page_indicator_ids
from econpulse.registry import load_registry
from econpulse.sources import ageing
from econpulse.store import Store
from econpulse.tables import Data, Heading, Panel, PanelColumn, PanelRow, build_panel

RATES = {"Y15-19": 0.2, "Y65-69": 0.1, "Y70-74": 0.05, "Y_GE75": 0.01}   # other bands: 0.8 active, 0.7 employed


def payload(quarters: list[str], old_pop) -> dict:
    """lfsq_pganws-shaped JSON-stat: thousands by sex, age band, labour status and quarter.
    Every band has 100 people a sex, except the 65+ bands, which have old_pop(quarter index)."""
    dims = {"freq": ["Q"], "unit": ["THS_PER"], "sex": ["M", "F", "T"], "citizen": ["TOTAL"],
            "age": list(ageing.BANDS) + ["Y15-64"], "wstatus": ["POP", "ACT", "EMP"], "geo": ["ES"], "time": quarters}
    sizes = [len(v) for v in dims.values()]
    strides = [int(np.prod(sizes[i + 1:])) for i in range(len(sizes))]
    values = {}
    for coords in itertools.product(*[range(n) for n in sizes]):
        c = {d: dims[d][i] for d, i in zip(dims, coords)}
        if c["sex"] == "T" or c["age"] == "Y15-64":
            continue                                   # aggregates the calculation must ignore
        q = quarters.index(c["time"])
        pop = old_pop(q) if c["age"] in ageing.OLD else 100.0
        rate = RATES.get(c["age"], 0.8)
        v = {"POP": pop, "ACT": pop * rate, "EMP": pop * rate * 0.875}[c["wstatus"]]
        if c["age"] == "Y_GE75" and c["sex"] == "F" and c["wstatus"] != "POP" and q == len(quarters) - 1:
            continue                                   # too few to publish
        values[str(sum(i * s for i, s in zip(coords, strides)))] = v
    return {"id": list(dims), "size": sizes, "value": values,
            "dimension": {d: {"category": {"index": {k: i for i, k in enumerate(v)}}} for d, v in dims.items()}}


def test_ageing_lowers_the_actual_rate_but_not_the_adjusted_one():
    quarters = [f"{y}-Q{q}" for y in (2007, 2008, 2009) for q in (1, 2, 3, 4)]
    table = ageing.counts(payload(quarters, lambda q: 100.0 + 20 * q))     # the 65+ bands grow
    assert table.shape == (12, 3 * 2 * 13)
    out = ageing.compute(table, base_year=2008)
    actual, adjusted = out["participation"], out["participation_adjusted"]
    assert actual.iloc[0] > actual.iloc[-1]                                  # more people past working age
    base = actual[actual.index.year == 2008].mean()
    assert adjusted.iloc[4:-1].round(9).nunique() == 1                       # no group changed its behaviour
    assert adjusted.iloc[5] == pytest.approx(base, abs=1e-9)
    assert adjusted.iloc[-1] < adjusted.iloc[-2]                             # women 75+ unpublished: count as nobody active
    assert out["share_65plus"].is_monotonic_increasing
    assert out["employment"].iloc[0] == pytest.approx(actual.iloc[0] * 0.875)
    with pytest.raises(ValueError):
        ageing.compute(table, base_year=2010)


def test_fetch_serves_each_measure(monkeypatch):
    quarters = [f"2008-Q{q}" for q in (1, 2, 3, 4)]
    ageing.clear_cache()
    calls = []

    class Response:
        def json(self):
            return payload(quarters, lambda q: 100.0)

    monkeypatch.setattr(ageing.http, "get", lambda url, params=None: calls.append(url) or Response())
    for key in ageing.KEYS:
        assert len(ageing.fetch(key).series) == 4
    assert len(calls) == 1                                                   # one download a run
    with pytest.raises(ValueError):
        ageing.fetch("unemployment")
    ageing.clear_cache()


def test_panel_headings(tmp_path):
    store = Store(tmp_path / "data")
    q = pd.date_range("2024-01-01", "2026-04-01", freq="QS")
    store.save_series("lfs_emp_young", pd.Series(np.linspace(20, 27, len(q)), index=q))
    panel = Panel(title="Group", caption="%", columns=[PanelColumn("emp", "Employment rate")],
                  rows=[Heading("By age"), PanelRow("15–24", {"emp": "lfs_emp_young"}, indent=1)])
    assert panel.indicator_ids() == {"lfs_emp_young"}
    t = build_panel(panel, Data(load_registry(), store))
    assert t["rows"][0]["heading"] and t["rows"][0]["label"] == "By age"
    assert t["rows"][1]["cells"] == ["27.0%"] and t["rows"][1]["indent"] == 1


def test_labour_page_group_and_ageing_blocks(tmp_path):
    store = Store(tmp_path / "data")
    q = pd.date_range("2005-01-01", "2026-04-01", freq="QS")
    n = len(q)
    for ind_id in demography.GROUPS.indicator_ids() | {"lfs_emp_prime_ea"}:
        store.save_series(ind_id, pd.Series(70.0 + np.arange(n) * 0.05, index=q))
    store.save_series("lfs_participation", pd.Series(np.r_[np.linspace(55, 60, 30), np.linspace(60, 58, n - 30)], index=q))
    store.save_series("lfs_participation_aged", pd.Series(np.linspace(58, 63, n), index=q))
    store.save_series("lfs_share_65plus", pd.Series(np.linspace(17, 24, n), index=q))
    page = build_page("labour", load_registry(), store)
    ids = [b["id"] for b in page["blocks"]]
    assert ids.index("groups") + 1 == ids.index("ageing")
    groups = next(b for b in page["blocks"] if b["id"] == "groups")
    rows = groups["tables"][0]["rows"]
    assert [r["label"] for r in rows if r["heading"]] == ["By age", "By sex, 15–64", "By sex, 25–54",
                                                         "By citizenship, 15–64", "By education, 25–64"]
    assert rows[0]["cells"][2] == "+0.2 pp"                                  # four quarters of +0.05
    ageing_block = next(b for b in page["blocks"] if b["id"] == "ageing")
    labels = [f["label"] for f in ageing_block["facts"]]
    assert labels[:3] == ["Participation, 15 and over", "At the 2008 age mix", "Effect of ageing since 2008"]
    assert "the fall comes from the population's ageing" in ageing_block["callout"]
    assert {"prime-employment", "participation-ageing", "share-65"} <= {c["id"] for c in page["charts"]}


def test_every_group_series_is_registered():
    registered = {i.id for i in load_registry()}
    assert page_indicator_ids("labour") - registered == set()
    ind = next(i for i in load_registry() if i.id == "lfs_une_edu_low")
    assert ind.key == "lfsq_urgaed" and ind.params["isced11"] == "ED0-2" and ind.params["age"] == "Y25-64"
