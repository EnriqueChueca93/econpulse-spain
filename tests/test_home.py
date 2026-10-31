"""Seasonal adjustment, the Four Questions, chart specs and the multi-page build (no network)."""

import json

import numpy as np
import pandas as pd
import pytest

from econpulse import charts, questions, seasonal, transforms
from econpulse.build import NAV, SECTION_PAGES, build_site
from econpulse.registry import Indicator
from econpulse.store import Store


def ind(**kw):
    base = dict(label=kw["id"], label_es=kw["id"], section="financial", source="fake", key=kw["id"], freq="M", unit="%")
    return Indicator(**{**base, **kw})


def seasonal_series(years=12, trend=0.002, amplitude=0.03):
    idx = pd.date_range("2012-01-01", periods=12 * years, freq="MS")
    t = np.arange(len(idx))
    pattern = amplitude * np.sin(2 * np.pi * (t % 12) / 12)
    return pd.Series(100 * np.exp(trend * t + pattern), index=idx)


# ---------------------------------------------------------------- seasonal adjustment

def test_seasonal_adjustment_removes_the_pattern():
    s = seasonal_series()
    raw_swings = transforms.apply("pop", s, "M").std()
    sa_swings = transforms.apply("sa_pop", s, "M").std()
    assert sa_swings < raw_swings / 10
    # The underlying trend (0.2% a month) survives.
    assert transforms.apply("sa_pop", s, "M").tail(24).mean() == pytest.approx(0.2, abs=0.02)


def test_seasonal_adjustment_rejects_bad_input():
    with pytest.raises(ValueError, match="monthly or quarterly"):
        seasonal.adjust(seasonal_series(), "D")
    with pytest.raises(ValueError, match="four years"):
        seasonal.adjust(seasonal_series(years=3), "M")
    gappy = seasonal_series().drop(pd.Timestamp("2020-05-01"))
    with pytest.raises(ValueError, match="gaps"):
        seasonal.adjust(gappy, "M")


def test_sa_labels():
    assert transforms.label("sa_diff", "M") == "m/m SA"
    assert transforms.label("sa_ann3m", "M") == "3m ann. SA"


# ---------------------------------------------------------------- four questions

def test_questions_degrade_to_dashes_without_data(tmp_path):
    qs = questions.four_questions([], Store(tmp_path / "empty"))
    assert [q["title"] for q in qs] == [
        "Is inflation coming back to 2%?", "Is the labour market cooling?",
        "Is growth holding up?", "Why are Spain's borrowing costs moving?"]
    assert all(row["value"] == questions.DASH for q in qs for row in q["rows"])


def test_borrowing_cost_parts_add_up(tmp_path):
    store = Store(tmp_path / "data")
    dates = pd.to_datetime(["2025-12-30", "2025-12-31", "2026-10-27", "2026-10-28", "2026-10-29"])
    store.save_series("es_10y", pd.Series([3.30, 3.29, 4.00, 4.03, 4.05], index=dates))
    store.save_series("de_10y", pd.Series([2.85, 2.84, 3.30, 3.33, None], index=dates).dropna())
    inds = [ind(id="es_10y", freq="D"), ind(id="de_10y", freq="D")]
    q = questions.borrowing_costs(questions._Data(inds, store))
    values = [r["value"] for r in q["rows"]]
    # Worked out on 28 Oct, the latest date with both yields: +74 = +49 + +25.
    assert values == ["+74 bp", "+49 bp", "+25 bp"]
    assert "31 Dec 2025" in q["rows"][0]["label"]


# ---------------------------------------------------------------- charts

def test_chart_spec_from_store(tmp_path):
    store = Store(tmp_path / "data")
    idx = pd.date_range("2018-01-01", periods=100, freq="MS")
    store.save_series("a", pd.Series(np.linspace(1, 5, 100), index=idx))
    definition = {"id": "t", "title": "T", "subtitle": "S", "kind": "line", "unit": "%", "decimals": 1,
                  "start": "2019-01-01", "series": [("a", "level", "A"), ("missing", "level", "B")], "link": "x.html"}
    spec = charts.build_chart(definition, {"a": ind(id="a")}, store)
    assert [s["name"] for s in spec["series"]] == ["A"]  # missing series skipped
    assert spec["series"][0]["x"][0] == "2019-01-01"
    assert "start" not in spec and spec["source"] == "fake"
    assert charts.build_chart({**definition, "series": [("missing", "level", "B")]}, {}, store) is None


# ---------------------------------------------------------------- build

def test_build_writes_every_page(tmp_path):
    store = Store(tmp_path / "data")
    idx = pd.date_range("2025-01-01", periods=21, freq="MS")
    store.save_series("es", pd.Series(np.linspace(4.0, 4.2, 21), index=idx))
    store.save_catalog({"es": {"status": "ok", "fetched_at": "2026-10-30T12:00:00+00:00", "last_date": "2026-09-01"}})
    inds = [ind(id="es", label="Spain 10-year yield", change_unit="bp", decimals=2, tile=1)]

    index = build_site(inds, store, site_dir=tmp_path / "site")
    site = tmp_path / "site"
    html = index.read_text(encoding="utf-8")
    assert "Spain 10-year yield" in html and "4.20%" in html
    assert "The economy in four questions" in html
    assert 'src="assets/app.js?v=' in html
    for href, _ in NAV:
        assert (site / href).exists(), href
    assert len(NAV) == len(SECTION_PAGES) + 2
    assert 'aria-current="page"' in (site / "financial.html").read_text(encoding="utf-8")
    snap_js = (site / "data" / "snapshot.js").read_text(encoding="utf-8")
    payload = json.loads(snap_js.split("window.EP.snapshot = ", 1)[1].rstrip().rstrip(";"))
    assert payload["tiles"] == ["es"] and len(payload["questions"]) == 4
    assert (site / "data" / "charts.js").exists()
    assert (site / "assets" / "style.css").exists()
