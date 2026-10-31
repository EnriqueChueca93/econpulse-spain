"""fetch -> store -> snapshot -> build, with fake sources (no network)."""

import json

import pandas as pd
import pytest

from econpulse import fetch as fetch_mod
from econpulse import sources
from econpulse.build import build_site
from econpulse.registry import Indicator
from econpulse.snapshot import build_snapshot, fmt_change, fmt_value
from econpulse.sources.base import FetchResult
from econpulse.store import Store


def ind(**kw):
    base = dict(label=kw["id"], label_es=kw["id"], section="financial", source="fake", key=kw["id"], freq="M", unit="%")
    return Indicator(**{**base, **kw})


class FakeClient:
    def __init__(self, data, failing=()):
        self.data, self.failing = data, set(failing)

    def fetch(self, key, params=None):
        if key in self.failing:
            raise ConnectionError("source down")
        return FetchResult(self.data[key], {"flash": key == "es"})

    def source_url(self, key, params=None):
        return f"https://example.org/{key}"


@pytest.fixture
def setup(tmp_path, monkeypatch):
    idx = pd.date_range("2025-01-01", periods=21, freq="MS")
    data = {
        "es": pd.Series([4.0 + i * 0.01 for i in range(21)], index=idx),
        "de": pd.Series([3.5] * 21, index=idx),
    }
    client = FakeClient(data)
    monkeypatch.setitem(sources.CLIENTS, "fake", client)
    indicators = [
        ind(id="es", change_unit="bp", decimals=2, tile=1),
        ind(id="de", change_unit="bp", decimals=2),
        ind(id="spread", source="derived", key="subtract", params={"a": "es", "b": "de", "scale": 100},
            unit="bp", decimals=0, change_unit="bp", tile=2),
    ]
    return Store(tmp_path / "data"), indicators, client


def test_fetch_saves_series_and_catalog(setup):
    store, indicators, _ = setup
    catalog = fetch_mod.fetch_all(indicators, store)
    assert {k: v["status"] for k, v in catalog.items()} == {"es": "ok", "de": "ok", "spread": "ok"}
    assert catalog["es"]["flash"] is True
    assert catalog["es"]["last_date"] == "2026-09-01"
    assert store.load_series("spread").iloc[-1] == pytest.approx(70.0)


def test_failing_source_keeps_old_data_and_others_continue(setup):
    store, indicators, client = setup
    fetch_mod.fetch_all(indicators, store)
    client.failing = {"de"}
    catalog = fetch_mod.fetch_all(indicators, store)
    assert catalog["de"]["status"] == "stale"
    assert "source down" in catalog["de"]["error"]
    assert catalog["es"]["status"] == "ok"
    assert store.load_series("de") is not None  # previous data kept


def test_failing_source_with_no_history_is_error(setup):
    store, indicators, client = setup
    client.failing = {"de"}
    catalog = fetch_mod.fetch_all(indicators, store)
    assert catalog["de"]["status"] == "error"
    assert catalog["spread"]["status"] == "error"  # its input is missing


def test_snapshot_values_and_changes(setup):
    store, indicators, _ = setup
    fetch_mod.fetch_all(indicators, store)
    snap = build_snapshot(indicators, store)
    assert snap["tiles"] == ["es", "spread"]
    es = next(i for i in snap["indicators"] if i["id"] == "es")
    head = es["headline"]
    assert head["display"] == "4.20%"
    assert head["period"] == "Sep 2026"
    assert head["change_year"] == pytest.approx(12.0)  # 0.12 pp shown in bp
    assert es["subline"] == "+12 bp y/y"
    assert es["flash"] is True


def test_build_writes_loadable_js(setup, tmp_path):
    store, indicators, _ = setup
    fetch_mod.fetch_all(indicators, store)
    index = build_site(indicators, store, site_dir=tmp_path / "site")
    js = (tmp_path / "site" / "data" / "snapshot.js").read_text(encoding="utf-8")
    assert js.startswith("window.EP = window.EP || {};")
    payload = js.split("window.EP.snapshot = ", 1)[1].rstrip().rstrip(";")
    assert json.loads(payload)["tiles"] == ["es", "spread"]
    html = index.read_text(encoding="utf-8")
    assert 'src="data/snapshot.js"' in html and 'src="assets/app.js"' in html
    assert (tmp_path / "site" / "assets" / "style.css").exists()


def test_out_of_date_detection():
    today = pd.Timestamp("2026-10-30")
    assert fetch_mod.is_out_of_date("2025-12-01", 120, today)
    assert not fetch_mod.is_out_of_date("2026-09-01", 120, today)
    assert fetch_mod.is_out_of_date(None, 120, today)


@pytest.mark.parametrize("value, unit, decimals, expected", [
    (4.9, "%", 1, "4.9%"),
    (-0.04, "%", 1, "0.0%"),          # no "-0.0"
    (-0.7, "%", 1, "−0.7%"),
    (45.4, "bp", 0, "45 bp"),
    (22852.6, "thousands", 1, "22,852.6k"),
    (1.11724, "rate", 4, "1.1172"),
    (101.4, "% of GDP", 1, "101.4% of GDP"),
])
def test_fmt_value(value, unit, decimals, expected):
    assert fmt_value(value, unit, decimals) == expected


def test_fmt_change_signs():
    assert fmt_change(0.3, "pp", 1) == "+0.3 pp"
    assert fmt_change(-25, "bp", 2) == "−25 bp"
    assert fmt_change(0.01, "pp", 1) == "0.0 pp"
