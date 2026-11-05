"""Spain beside its peers, and what forecasters expect, on the home page (econpulse/scoreboard.py)."""

from datetime import date

import numpy as np
import pandas as pd

from econpulse import forecasts, i18n, scoreboard
from econpulse.forecasts import CHECKED, PENDING, Forecaster
from econpulse.registry import Indicator
from econpulse.store import Store
from econpulse.tables import Data

HICP = {"es": ("hicp", 4.9), "ea": ("hicp_euro_area", 4.0), "de": ("hicp_de", 2.8), "fr": ("hicp_fr", 3.8),
        "it": ("hicp_it", 5.6), "pt": ("hicp_pt", 3.9)}


def ind(**kw):
    base = dict(label=kw["id"], label_es=kw["id"], section="international", source="fake", key=kw["id"], freq="M", unit="%")
    return Indicator(**{**base, **kw})


def _data(tmp_path, late=("pt",)):
    store = Store(tmp_path / "data")
    for slug, (series_id, last) in HICP.items():
        end = "2026-09-01" if slug in late else "2026-10-01"
        store.save_series(series_id, pd.Series(np.r_[np.full(23, 2.0), last], index=pd.date_range(end=end, periods=24, freq="MS")))
    return Data([ind(id=i) for i, _v in HICP.values()], store)


def test_strip_scales_stacks_and_names_its_dots():
    s = scoreboard.strip([{"value": 1.0, "kind": "other", "title": "A"}, {"value": 1.0, "kind": "other", "title": "B"},
                          {"value": 3.0, "kind": "main", "title": "Spain"}], [{"value": 2.0, "title": "Euro area"}])
    xs = [d["x"] for d in s["dots"]]
    assert xs == [scoreboard.PAD, scoreboard.PAD, scoreboard.W - scoreboard.PAD]     # the range fills the strip
    assert s["dots"][0]["y"] != s["dots"][1]["y"]                                   # equal values are stacked
    assert s["dots"][-1]["kind"] == "main" and s["dots"][-1]["r"] > s["dots"][0]["r"]   # Spain last, on top
    assert s["ticks"] == [{"x": scoreboard.W / 2, "title": "Euro area"}]
    assert s["label"].startswith("Euro area; Spain;")
    assert scoreboard.strip([{"value": 1.0, "kind": "main", "title": "Spain"}]) is None


def test_peer_table_row_place_and_late_countries(tmp_path):
    table = scoreboard.peer_table(_data(tmp_path))
    assert table["countries"] == ["Spain", "Euro area", "Germany", "France", "Italy", "Portugal"]
    (row,) = table["rows"]                      # only HICP inflation has data here
    assert row["label"] == "HICP inflation" and row["period"] == "Oct 2026"
    assert [c["text"] for c in row["cells"]] == ["4.9%", "4.0%", "2.8%", "3.8%", "5.6%", "3.9%"]
    assert row["cells"][0]["spain"] and row["cells"][-1]["period"] == "Sep 2026"   # Portugal is a month behind
    assert row["place"] == "2nd highest of 5"
    assert [t["title"] for t in row["strip"]["ticks"]] == ["Euro area: 4.0% (Oct 2026)"]
    with i18n.using("es"):
        assert scoreboard.peer_table(_data(tmp_path))["rows"][0]["place"] == "la 2.ª cifra más alta de los 5"


def _forecaster(id_, gdp, inflation, status=CHECKED):
    return Forecaster(id=id_, name=id_.upper(), short=id_.upper(), group="spain", url=None, published=date(2026, 10, 1),
                      values={2026: {"gdp": gdp, "inflation": inflation}, 2027: {"gdp": gdp - 0.5}}, status=status)


def test_outlook_averages_checked_forecasts_and_marks_macroscope(tmp_path, monkeypatch):
    fs = [_forecaster("a", 2.4, 3.0), _forecaster("b", 2.6, 3.4), _forecaster("c", 9.9, 9.9, status=PENDING)]
    monkeypatch.setattr(forecasts, "forecasters", lambda data: fs)
    monkeypatch.setattr(forecasts, "years", lambda today=None: (2026, 2027))
    monkeypatch.setattr(forecasts, "gdp_this_year", lambda data, year: {"value": 2.63, "through": pd.Timestamp("2026-07-01")})
    out = scoreboard.outlook(_data(tmp_path))
    labels = [b["label"] for b in out["boxes"]]
    assert labels == ["GDP growth, 2026", "GDP growth, 2027", "Inflation, 2026"]    # 2027 inflation: no figures
    gdp = out["boxes"][0]
    assert gdp["value"] == "2.5%" and gdp["sub"] == "average of 2; range 2.4% to 2.6%"     # the pending one is left out
    assert gdp["extra"] == "Macroscope's estimate: 2.6%" and gdp["strip"]["dots"][-1]["kind"] == "main"
    assert out["boxes"][1]["extra"] is None and out["who"] == "A (Oct 2026) and B (Oct 2026)"


def test_the_home_page_shows_both(tmp_path, monkeypatch):
    from econpulse.build import build_site
    data = _data(tmp_path)
    monkeypatch.setattr(forecasts, "forecasters", lambda data: [_forecaster("a", 2.4, 3.0), _forecaster("b", 2.6, 3.4)])
    data.store.save_catalog({i: {"status": "ok", "fetched_at": "2026-11-04T12:00:00+00:00"} for i in data.by_id})
    build_site(list(data.by_id.values()), data.store, site_dir=tmp_path / "site", languages=("en",))
    html = (tmp_path / "site" / "index.html").read_text(encoding="utf-8")
    peers = html.split('id="peers"')[1].split("</section>")[0]
    assert '<td class="num spain">4.9%' in peers and "2nd highest of 5" in peers and 'class="dot dot-main"' in peers
    outlook = html.split('id="outlook"')[1].split("</section>")[0]
    assert outlook.count('class="card outlook-box"') == 3 and 'href="analysis.html#forecasts"' in outlook
    assert 'href="index.html#peers"' in html and 'href="index.html#outlook"' in html
