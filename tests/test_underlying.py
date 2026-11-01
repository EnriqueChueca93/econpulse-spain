"""Batch 13: underlying inflation from the detailed HICP items (no network)."""

import numpy as np
import pandas as pd
import pytest

from econpulse import charts, pages, underlying
from econpulse.registry import load_registry
from econpulse.sources import hicpdist
from econpulse.store import Store
from econpulse.tables import Data


def test_distribution_measures():
    m = hicpdist.distribution(np.array([4.0, 1.0, 100.0, 3.0, 2.0]), np.array([1.0, 1.0, 1.0, 1.0, 1.0]))
    assert m["median"] == 3.0
    # 10% trimmed: the lowest and highest items each keep 0.15 of their 0.2 weight.
    assert m["trim10"] == pytest.approx((0.15 * 1 + 0.2 * (2 + 3 + 4) + 0.15 * 100) / 0.9)
    assert m["trim30"] == pytest.approx((0.05 * 1 + 0.2 * (2 + 3 + 4) + 0.05 * 100) / 0.7)
    assert m["above2"] == pytest.approx(60) and m["above5"] == pytest.approx(20)
    # Weights count: a heavy item at 2% pulls the median to it.
    assert hicpdist.distribution(np.array([1.0, 2.0, 9.0]), np.array([1.0, 5.0, 1.0]))["median"] == 2.0


def jsonstat(cells: dict[tuple[str, str], float], codes: list[str], times: list[str], labels=None) -> dict:
    """A Eurostat JSON-stat payload with dimensions freq, coicop18, geo, time."""
    values = {}
    for (c, t), v in cells.items():
        values[str(codes.index(c) * len(times) + times.index(t))] = v
    return {"id": ["freq", "coicop18", "geo", "time"], "size": [1, len(codes), 1, len(times)], "value": values,
            "dimension": {"freq": {"category": {"index": {"M": 0}}},
                          "coicop18": {"category": {"index": {c: i for i, c in enumerate(codes)},
                                                    "label": labels or {c: c for c in codes}}},
                          "geo": {"category": {"index": {"ES": 0}}},
                          "time": {"category": {"index": {t: i for i, t in enumerate(times)}}}}}


def test_compute_from_eurostat_payloads(monkeypatch):
    monkeypatch.setattr(hicpdist, "MIN_ITEMS", 3)
    codes = ["TOTAL", "CP01", "CP01111", "CP01112", "CP04411", "CP07221"]   # only five-digit items count
    months = [f"{y}-{m:02d}" for y in (2025, 2026) for m in range(1, 13)][:21]  # Jan 2025 to Sep 2026
    growth = {"CP01111": 1.01, "CP01112": 1.03, "CP04411": 1.04, "CP07221": 1.30}  # a year
    cells = {}
    for c in codes:
        for i, t in enumerate(months):
            cells[(c, t)] = 100 * growth.get(c, 1.02) ** (i / 12)
    labels = {c: c for c in codes} | {"CP07221": "Diesel (ND)"}
    idx = jsonstat(cells, codes, months, labels)
    w = jsonstat({(c, y): wt for c, wt in zip(codes[2:], (400, 300, 200, 100)) for y in ("2025", "2026")},
                 codes, ["2025", "2026"])
    result = hicpdist.compute(*hicpdist.tables(idx, w))
    median = result["series"]["median"]
    assert list(median) == [pd.Timestamp(f"2026-{m:02d}-01") for m in range(1, 10)]  # a year of history needed first
    assert median[pd.Timestamp("2026-09-01")] == pytest.approx(3.0)   # 40% at 1%, then 30% at 3%
    assert result["series"]["above5"][pd.Timestamp("2026-09-01")] == pytest.approx(10.0)
    latest = result["latest"]
    assert latest["month"] == "2026-09" and latest["items"] == 4
    assert sum(share for _, share in latest["bands"]) == pytest.approx(100)
    assert latest["highest"][0][:2] == ["Diesel (ND)", 30.0] and latest["lowest"][0][1] == 1.0


def test_page_pieces_from_the_stored_distribution(tmp_path):
    store = Store(tmp_path / "data")
    months = pd.date_range("2016-01-01", "2026-09-01", freq="MS")
    for ind_id, level in (("hicp", 5.0), ("hicp_core", 3.5), ("hicp_wmedian", 3.1), ("hicp_trim10", 3.7),
                          ("hicp_trim30", 3.2), ("hicp_share_above2", 71.9), ("hicp_share_above5", 18.3)):
        store.save_series(ind_id, pd.Series(level, index=months))
    store.save_catalog({"hicp_wmedian": {"distribution": {
        "month": "2026-09", "items": 179, "bands": [["<0", 9.1], ["0–1", 12.4], ["10+", 12.4]],
        "highest": [["Diesel (ND)", 34.0, 2.33]], "lowest": [["Passenger transport by train (S)", -11.2, 0.3]]}}})
    data = Data(load_registry(), store)
    facts = underlying.facts(data)
    assert [f["value"] for f in facts] == ["5.0%", "3.1%", "3.2%", "72%"]
    assert "1.9 points above the weighted median" in underlying.callout(data)
    chart = underlying.distribution_chart(data)
    assert chart["series"][0]["x"] == ["<0", "0–1", "10+"] and "Sep 2026" in chart["subtitle"]
    table = underlying.movers_table(data)
    assert [r["label"] for r in table["rows"]] == ["Rising fastest", "Diesel", "Rising slowest or falling",
                                                    "Passenger transport by train"]
    assert table["rows"][1]["cells"] == ["+34.0%", "2.3%"]
    page = pages.build_page("inflation", load_registry(), store)
    block = next(b for b in page["blocks"] if b["id"] == "underlying")
    assert [c["id"] for c in block["charts"]][-1] == "inflation-spread"
    assert block["charts"][0]["source"] == "Eurostat; EconPulse calculation"


def test_calculated_series_credit_eurostat():
    by_id = {i.id: i for i in load_registry()}
    assert charts.source_names(by_id["hicp_wmedian"], by_id) == ["Eurostat", "EconPulse calculation"]
    assert by_id["hicp_wmedian"].source_name == "Eurostat (EconPulse calculation)"
