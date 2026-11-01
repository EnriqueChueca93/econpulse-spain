"""Batch 26a: the Trade page, goods trade by product group from Eurostat's Comext (no network)."""

import numpy as np
import pandas as pd
import pytest

from econpulse import trade
from econpulse.build import NAV, build_site
from econpulse.registry import load_registry
from econpulse.sources import comext
from econpulse.store import Store
from econpulse.tables import Data


def payload(products: list[str], months: list[str], value) -> dict:
    """Comext-shaped JSON-stat: one value per product and month (None leaves it out)."""
    dims = {"freq": ["M"], "reporter": ["ES"], "partner": ["WORLD"], "product": products, "flow": ["2"],
            "indicators": ["VALUE_IN_EUROS"], "time": months}
    sizes = [len(v) for v in dims.values()]
    values = {}
    for p, prod in enumerate(products):
        for t, month in enumerate(months):
            v = value(prod, month)
            if v is not None:
                values[str(p * len(months) + t)] = v
    return {"id": list(dims), "size": sizes, "value": values,
            "dimension": {d: {"category": {"index": {k: i for i, k in enumerate(v)}}} for d, v in dims.items()}}


def test_groups_cover_every_chapter_once():
    assert comext.chapters("01-05,16") == ["01", "02", "03", "04", "05", "16"] and comext.chapters("total") == ["TOTAL"]
    keys = [i.key for i in load_registry() if i.id.startswith("trade_exp_") and i.key != "TOTAL"]
    assert len(keys) == len(trade.groups()) == 18
    covered = [c for k in keys for c in comext.chapters(k)]
    assert sorted(covered) == comext.CHAPTERS          # each chapter in exactly one group (77 and 98 are unused)


def test_download_in_batches_and_sum(monkeypatch):
    asked = []

    class Response:
        def __init__(self, products):
            self.products = products

        def json(self):
            return payload(self.products, ["2026-07", "2026-08"],
                           lambda p, m: None if (p, m) == ("16", "2026-08") else (1000.0 if p == "TOTAL" else 10.0))

    def get(url, params=None, timeout=None):
        products = [v for k, v in params if k == "product"]
        asked.append((dict((k, v) for k, v in params if k != "product"), products))
        return Response(products)

    comext.clear_cache()
    monkeypatch.setattr(comext.http, "get", get)
    s = comext.fetch("01-05,16", {"flow": "exports"}, since=pd.Timestamp("2026-07-01")).series
    assert all(len(products) <= comext.BATCH for _, products in asked) and len(asked) == 5
    assert asked[0][0]["sinceTimePeriod"] == "2026-07" and asked[0][0]["flow"] == "2"
    assert s.tolist() == [60.0, 50.0]                  # chapter 16 missing in August counts as zero
    asked.clear()
    comext.fetch("84", {"flow": "exports"}, since=pd.Timestamp("2026-07-01"))
    assert asked == []                                 # one download serves every group
    with pytest.raises(ValueError):
        comext.fetch("84", {"flow": "re-exports"})
    comext.clear_cache()


def trade_store(tmp_path) -> Store:
    store = Store(tmp_path / "data")
    m = pd.date_range("2018-01-01", "2026-08-01", freq="MS")
    n = len(m)
    growth = 1 + np.arange(n) / 1000
    store.save_series("trade_exp_total", pd.Series(30_000.0 * growth, index=m))
    store.save_series("trade_imp_total", pd.Series(35_000.0 * growth, index=m))
    for k, (slug, _) in enumerate(trade.groups()):
        store.save_series(f"trade_exp_{slug}", pd.Series((500.0 + 100 * k) * growth, index=m))
        store.save_series(f"trade_imp_{slug}", pd.Series(1_200.0 * growth if slug == "energy" else 900.0 * growth, index=m))
    return store


def test_trade_page(tmp_path):
    data = Data(load_registry(), trade_store(tmp_path))
    page = trade.page(data)
    labels = [f["label"] for f in page["facts"]]
    assert labels == ["Exports of goods", "Imports of goods", "Trade balance", "Balance without energy"]
    assert page["facts"][0]["value"] == "€395.1 bn"            # 12 x 30,000 x 1.0975, to August 2026
    first = page["table"]["rows"][0]
    assert first["label"] == "All goods" and first["cells"][2] == "100.0" and first["cells"][5].startswith("−")
    assert [r["label"] for r in page["table"]["rows"] if r["heading"]] == ["Food and drink", "Energy and materials",
                                                                          "Chemicals and plastics", "Manufactures"]
    ranking = next(c for c in page["rankings"] if c["id"] == "exports-ranking")
    assert ranking["series"][0]["x"][0] == "Other goods" and ranking["series"][0]["y"] == sorted(ranking["series"][0]["y"], reverse=True)
    assert len(page["charts"]) == 2 + 3 + 18
    assert [s["id"] for s in page["sections"]] == ["group-food", "group-materials", "group-chemicals", "group-manufactures"]


def test_trade_tab_is_built(tmp_path):
    store = trade_store(tmp_path)
    assert ("trade.html", "Trade") in NAV
    build_site(load_registry(), store, site_dir=tmp_path / "site")
    html = (tmp_path / "site" / "trade.html").read_text(encoding="utf-8")
    assert 'aria-current="page">Trade</a>' in html and 'id="fig-trade-vehicles"' in html
    assert "Vehicles and parts (87)" in html and (tmp_path / "site" / "data" / "charts-trade.js").exists()
