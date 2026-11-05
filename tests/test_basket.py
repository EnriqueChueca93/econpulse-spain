"""The HICP basket as a treemap (econpulse/basket.py): what is saved, the month's view, the spec, the page."""

import numpy as np
import pandas as pd
import pytest

from econpulse import basket, i18n, schedule
from econpulse.build import build_site
from econpulse.registry import Indicator
from econpulse.store import Store
from econpulse.tables import Data

LABELS = {"CP01": "Food and non-alcoholic beverages", "CP07": "Transport", "CP01113": "Bread and bakery products (ND)",
          "CP01122": "Meat, fresh, chilled or frozen (ND)", "CP07221": "Diesel (ND)", "CP07244": "Hire of cars (S)",
          "CP09999": "Never in the basket (S)"}


def tables():
    months = pd.date_range("2024-12-01", "2026-03-01", freq="MS")
    grow = lambda rate: 100 * (1 + rate / 100) ** (np.arange(len(months)) / 12)   # noqa: E731
    index = pd.DataFrame({"CP01113": grow(1.0), "CP01122": grow(3.0), "CP07221": grow(20.0),
                          "CP07244": [np.nan] * 13 + [100.0, 101.0, 102.0],         # new in 2026: no annual rate yet
                          "CP09999": grow(5.0)}, index=months)
    weights = pd.DataFrame({"CP01113": [20.0, 25.0], "CP01122": [30.0, 25.0], "CP07221": [50.0, 40.0],
                            "CP07244": [0.0, 10.0], "CP09999": [0.0, 0.0]}, index=[2025, 2026])
    return index, weights, LABELS


def saved_basket(tmp_path):
    store = Store(tmp_path)
    store.save_json(basket.STORE, basket.payload(*tables(), "2026-04-01T00:00:00+00:00"))
    return store


def test_payload_keeps_rates_from_the_first_annual_rate_and_only_items_with_a_weight(tmp_path):
    p = basket.payload(*tables(), "now")
    assert p["months"][0] == "2025-12" and p["months"][-1] == "2026-03"
    assert set(p["items"]) == {"CP01113", "CP01122", "CP07221", "CP07244"}          # never weighted: left out
    assert p["items"]["CP07221"] == "Diesel" and p["categories"] == {"CP01": "Food and non-alcoholic beverages",
                                                                      "CP07": "Transport"}
    assert p["rates"]["CP07221"] == [20.0] * 4 and p["rates"]["CP07244"] == [None] * 4
    assert p["weights"]["2025"] == {"CP01113": 20.0, "CP01122": 30.0, "CP07221": 50.0}


def test_shades_are_set_by_the_distance_from_the_2pc_target():
    assert [basket._shade(r) for r in (2.0, 2.4, 1.6, 2.5, 3.9, 4.0, 6.0, 1.4, 0.0, -0.1, -2.0, None)] == [
        "mid", "mid", "mid", "hot1", "hot1", "hot2", "hot3", "cool1", "cool2", "cool2", "cool3", "none"]


def test_month_view_weights_rates_and_contributions(tmp_path):
    saved = saved_basket(tmp_path).load_json(basket.STORE, None)
    view = basket.month_view(saved, 3)                 # Mar 2026, with the 2026 weights
    assert [c["code"] for c in view] == ["CP01", "CP07"]
    food, transport = view
    assert food["weight"] == 50.0 and transport["weight"] == 50.0
    assert [i["code"] for i in transport["items"]] == ["CP07221", "CP07244"]
    diesel, hire = transport["items"]
    assert diesel["weight"] == 40.0 and diesel["rate"] == 20.0 and diesel["contribution"] == 8.0 and diesel["shade"] == "hot3"
    assert hire["rate"] is None and hire["contribution"] is None and hire["shade"] == "none"
    # a category's rate is its rated items' weighted average, and its contribution their sum
    assert transport["rate"] == 20.0 and transport["contribution"] == 8.0
    assert food["rate"] == pytest.approx(2.0, abs=0.01) and food["name"] == "Food and soft drinks"
    # a month whose year has no weights yet takes the latest year's
    saved["months"].append("2027-01")
    assert basket.month_view(saved, 4)[0]["weight"] == 50.0


def test_the_treemap_spec_in_both_languages(tmp_path):
    data = Data([], saved_basket(tmp_path))
    spec = basket.treemap(data)
    assert spec["kind"] == "treemap" and spec["id"] == "basket" and spec["series"] == []
    assert spec["subtitle"].startswith("HICP, Mar 2026") and spec["month"] == "Mar 2026"
    assert spec["words"]["legend_growth"][0] == ["cool3", "−2% or less"]
    with i18n.using("es"):
        es = basket.treemap(data)
    transport = [c for c in es["categories"] if c["code"] == "CP07"][0]
    assert transport["name"] == "Transporte" and transport["items"][0]["name"] == "Gasóleo"   # INE's names, by code
    assert es["words"]["growth"] == "Variación de los precios" and es["lang"] == "es"
    assert basket.treemap(Data([], Store(tmp_path / "empty"))) is None


def test_refresh_keeps_the_last_copy_when_the_download_fails(tmp_path, monkeypatch):
    store = saved_basket(tmp_path)

    def broken(geo="ES"):
        raise ConnectionError("down")
    monkeypatch.setattr(basket.hicpdist, "basket", broken)
    assert "keeping the copy from 2026-04-01" in basket.refresh(store)
    kept = store.load_json(basket.STORE, None)
    assert kept["months"][-1] == "2026-03" and kept["error"] == "ConnectionError: down"
    monkeypatch.setattr(basket.hicpdist, "basket", lambda geo="ES": tables())
    assert basket.refresh(store) == "4 items, 2025-12 to 2026-03"


def test_the_inflation_page_shows_the_basket(tmp_path, monkeypatch):
    store = saved_basket(tmp_path / "data")
    monkeypatch.setattr(schedule, "releases", lambda store, today=None: [])
    one = Indicator(id="cpi", label="CPI inflation", label_es="Inflación", section="inflation", source="fake", key="cpi",
                    freq="M", unit="%")
    build_site([one], store, site_dir=tmp_path / "site", languages=("en",))
    html = (tmp_path / "site" / "inflation.html").read_text(encoding="utf-8")
    assert 'id="basket"' in html and 'id="chart-basket"' in html and "The basket, item by item" in html
    charts = (tmp_path / "site" / "data" / "charts-inflation.js").read_text(encoding="utf-8")
    assert '"kind":"treemap"' in charts and '"code":"CP07221"' in charts
