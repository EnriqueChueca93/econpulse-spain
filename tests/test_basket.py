"""The HICP basket (econpulse/basket.py): the chained index and contributions, what is saved, the spec, the page."""

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
HICP = Indicator(id="hicp", label="HICP inflation", label_es="IPCA", section="inflation", source="fake", key="hicp",
                 freq="M", unit="%")


def tables():
    months = pd.date_range("2024-12-01", "2026-03-01", freq="MS")
    grow = lambda rate: 100 * (1 + rate / 100) ** (np.arange(len(months)) / 12)   # noqa: E731
    index = pd.DataFrame({"CP01113": grow(1.0), "CP01122": grow(3.0), "CP07221": grow(20.0),
                          # new in 2026: priced from the December before, so no annual rate for a year
                          "CP07244": [np.nan] * 12 + [100.0, 101.0, 102.0, 103.0],
                          "CP09999": grow(5.0)}, index=months)
    weights = pd.DataFrame({"CP01113": [20.0, 25.0], "CP01122": [30.0, 25.0], "CP07221": [50.0, 40.0],
                            "CP07244": [0.0, 10.0], "CP09999": [0.0, 0.0]}, index=[2025, 2026])
    return index, weights, LABELS


def saved_basket(tmp_path, headline=None):
    store = Store(tmp_path)
    store.save_json(basket.STORE, basket.payload(*tables(), "2026-04-01T00:00:00+00:00"))
    if headline is not None:
        store.save_series("hicp", headline)
    return store


def test_one_item_contributes_its_own_annual_rate():
    months = pd.date_range("2022-12-01", "2025-06-01", freq="MS")
    rng = np.random.default_rng(1)
    index = pd.DataFrame({"CP01111": 100 * np.cumprod(1 + rng.normal(0.003, 0.01, len(months)))}, index=months)
    weights = pd.DataFrame({"CP01111": [1000.0, 1000.0, 1000.0]}, index=[2023, 2024, 2025])
    level, _, _ = basket.chain(index, weights)
    assert level.reindex(months).to_numpy() == pytest.approx(100 * index["CP01111"].to_numpy() / index["CP01111"].iloc[0])
    added, total = basket.contributions(index, weights)
    yoy = (index["CP01111"] / index["CP01111"].shift(12) - 1) * 100
    assert added.index[0] == pd.Timestamp("2024-01-01") and added.index[-1] == pd.Timestamp("2025-06-01")
    assert added["CP01111"].to_numpy() == pytest.approx(yoy.reindex(added.index).to_numpy())
    assert total.to_numpy() == pytest.approx(yoy.reindex(total.index).to_numpy())


def test_contributions_add_up_to_the_chained_index_when_the_basket_changes():
    index, weights, _ = tables()
    level, shares, _ = basket.chain(index, weights)
    assert set(shares) == {2025, 2026} and "CP07244" in shares[2026] and "CP07244" not in shares[2025]
    assert shares[2026].sum() == pytest.approx(1)
    # January 2026 links the 2026 basket to December 2025
    jan = index.loc["2026-01-01"] / index.loc["2025-12-01"]
    assert level[pd.Timestamp("2026-01-01")] == pytest.approx(level[pd.Timestamp("2025-12-01")] * (shares[2026] * jan).sum())
    added, total = basket.contributions(index, weights)
    assert list(added.index.strftime("%Y-%m")) == ["2026-01", "2026-02", "2026-03"]
    assert added.sum(axis=1, min_count=1).to_numpy() == pytest.approx(total.to_numpy())
    # the new item has no annual rate yet but adds its change since December, at its 2026 weight
    hire = added["CP07244"]
    assert hire.iloc[0] == pytest.approx(level[pd.Timestamp("2025-12-01")] / level[pd.Timestamp("2025-01-01")] * 0.1 * 1)
    assert added["CP09999"].isna().all()                  # never in the basket


def test_payload_keeps_rates_contributions_and_weights(tmp_path):
    p = basket.payload(*tables(), "now")
    assert p["months"][0] == "2025-12" and p["months"][-1] == "2026-03"
    assert set(p["items"]) == {"CP01113", "CP01122", "CP07221", "CP07244"}          # never weighted: left out
    assert p["items"]["CP07221"] == "Diesel" and p["categories"] == {"CP01": "Food and non-alcoholic beverages",
                                                                      "CP07": "Transport"}
    assert p["rates"]["CP07221"] == [20.0] * 4 and p["rates"]["CP07244"] == [None] * 4
    assert p["contributions"]["CP07221"][0] is None and p["contributions"]["CP07244"][1] > 0
    for k in range(1, 4):
        assert sum(v[k] for v in p["contributions"].values()) == pytest.approx(p["total"][k], abs=0.01)
    assert p["weights"]["2025"] == {"CP01113": 20.0, "CP01122": 30.0, "CP07221": 50.0}


def test_the_spec_in_both_languages(tmp_path):
    headline = pd.Series([9.0, 9.1, 9.2, 9.3], index=pd.date_range("2025-12-01", periods=4, freq="MS"))
    data = Data([HICP], saved_basket(tmp_path, headline))
    spec = basket.treemap(data)
    assert spec["kind"] == "treemap" and spec["id"] == "basket" and spec["series"] == []
    assert spec["months"] == ["2025-12", "2026-01", "2026-02", "2026-03"] and spec["labels"][-1] == "Mar 2026"
    assert spec["subtitle"].startswith("HICP, Mar 2026")
    codes = [c for c, _ in spec["items"]]
    assert codes == ["CP01113", "CP01122", "CP07221", "CP07244"] and spec["cats"][1] == ["CP07", "Transport", "Transport"]
    assert len(spec["rates"]) == len(spec["contribs"]) == 4 and all(len(r) == 4 for r in spec["rates"] + spec["contribs"])
    assert spec["shares"]["2026"] == [25.0, 25.0, 40.0, 10.0] and spec["shares"]["2025"][3] == 0
    assert spec["headline"] == [9.0, 9.1, 9.2, 9.3] and spec["steps"] == [0.5, 2.0, 4.0]
    gap = max(abs(h - t) for h, t in zip(spec["headline"][1:], basket.payload(*tables(), "now")["total"][1:]))
    assert f"{gap:.2f}" in spec["words"]["fit"]
    assert spec["words"]["legend_growth"][0] == ["cool3", "−2% or less"]
    with i18n.using("es"):
        es = basket.treemap(data)
    assert es["cats"][1][1] == "Transporte" and es["items"][2][1] == "Gasóleo"   # INE's names, by code
    assert es["words"]["growth"] == "Variación de los precios" and es["words"]["time"] == "Evolución" and es["lang"] == "es"
    assert basket.treemap(Data([], saved_basket(tmp_path / "plain")))["words"]["fit"] is None   # no headline series
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
    assert '"kind":"treemap"' in charts and '["CP07221","Diesel"]' in charts
