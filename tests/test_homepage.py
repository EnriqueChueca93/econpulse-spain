"""The home page's latest releases and sparklines (econpulse/homepage.py)."""

import numpy as np
import pandas as pd

from econpulse import homepage, i18n, schedule
from econpulse.build import build_site
from econpulse.registry import Indicator
from econpulse.sources.base import madrid_today
from econpulse.store import Store


def ind(**kw):
    base = dict(label=kw["id"], label_es=kw["id"], section="inflation", source="fake", key=kw["id"], freq="M", unit="%")
    return Indicator(**{**base, **kw})


def monthly(values, end="2026-09-01"):
    return pd.Series(values, index=pd.date_range(end=end, periods=len(values), freq="MS"), dtype=float)


def test_context_names_the_highest_or_lowest_reading_in_more_than_a_year():
    cpi = ind(id="cpi")
    # 4.9% in Sep 2026: last that high in Jun 2025 (15 months before)
    assert homepage.context(cpi, monthly([5.0] + [3.0] * 14 + [4.9]), "level") == "The highest since Jun 2025"
    assert homepage.context(cpi, monthly([1.0] + [3.0] * 14 + [1.2]), "level") == "The lowest since Jun 2025"
    # never so high, over more than a year
    assert homepage.context(cpi, monthly([3.0] * 14 + [4.9]), "level") == "The highest in the series, which starts in 2025"
    # within the year, or no higher than the month before as shown: the reading before
    assert homepage.context(cpi, monthly([5.0] + [3.0] * 5 + [4.9]), "level") == "After 3.0% in Aug 2026"
    assert homepage.context(cpi, monthly([3.0] * 20 + [4.94, 4.9]), "level") == "After 4.9% in Aug 2026"
    q = ind(id="gdp", freq="Q")
    gdp = pd.Series(100 * 1.005 ** np.arange(12), index=pd.date_range(end="2026-07-01", periods=12, freq="QS"))
    assert homepage.context(q, homepage.headline_series(q, gdp, "pop"), "pop") == "After 0.5% q/q in Q2 2026"
    assert homepage.context(ind(id="x", freq="D"), monthly([1.0, 2.0]), "level") is None
    with i18n.using("es"):
        assert homepage.context(cpi, monthly([5.0] + [3.0] * 14 + [4.9]), "level") == "El dato más alto desde jun 2025"


def test_sparkline_points_zero_line_and_range():
    s = homepage.sparkline(ind(id="x"), monthly(np.linspace(-1, 2, 48)), "level")
    points = s["points"].split()
    assert len(points) == 36                                   # three years of a monthly series
    assert (s["x"], s["y"]) == tuple(float(v) for v in points[-1].split(","))
    assert s["y"] == homepage.PAD                              # the last reading is the highest: at the top
    assert s["zero"] is not None and homepage.PAD < s["zero"] < homepage.H - homepage.PAD
    assert s["title"].startswith("Past 3 years: low −0.2% (Oct 2023), high 2.0% (Sep 2026)")
    assert homepage.sparkline(ind(id="x"), monthly([1.0, 2.0]), "level") is None
    assert homepage.sparkline(ind(id="x"), monthly(np.linspace(1, 2, 48)), "level")["zero"] is None
    # daily: weekly averages, ending on the latest reading; the range is the daily readings'
    days = pd.date_range(end="2026-11-04", periods=400, freq="D")
    daily = pd.Series(np.where(days.day_of_week == 6, 0.0, 100.0), index=days)
    d = homepage.sparkline(ind(id="power", freq="D", unit="€/MWh", decimals=0), daily, "level")
    assert 50 <= len(d["points"].split()) <= 54
    assert "low 0 €/MWh" in d["title"] and d["title"].startswith("Past year")


def _site(tmp_path, monkeypatch, event_period):
    store = Store(tmp_path / "data")
    store.save_series("cpi", monthly([5.0] + [3.0] * 14 + [4.9]))
    store.save_catalog({"cpi": {"status": "ok", "fetched_at": "2026-10-30T12:00:00+00:00", "last_date": "2026-09-01"}})
    released = pd.Timestamp(madrid_today()) - pd.Timedelta(days=2) + pd.Timedelta(hours=9)
    events = [{"when": released, "label": "CPI", "period": event_period, "page": "inflation.html", "ids": ["cpi"]}]
    monkeypatch.setattr(schedule, "releases", lambda store, today=None: events)
    build_site([ind(id="cpi", label="CPI inflation", tile=1)], store, site_dir=tmp_path / "site", languages=("en",))
    return (tmp_path / "site" / "index.html").read_text(encoding="utf-8")


def test_the_home_page_opens_with_the_latest_releases(tmp_path, monkeypatch):
    html = _site(tmp_path, monkeypatch, "Sep 2026")
    latest = html.split('id="latest"')[1].split("</section>")[0]
    assert 'class="card latest-card" href="inflation.html' in latest
    assert "CPI inflation, Sep 2026" in latest and "The highest since Jun 2025" in latest
    assert latest.count('class="spark"') == 1
    tile = html.split('class="tiles"')[1].split("</section>")[0]
    assert 'class="spark"' in tile and "<title>Past 3 years: low 3.0%" in tile
    assert 'class="badge badge-new">New · ' in tile          # out in the past week
    assert "news-day" not in html                            # the cards take the place of the list of releases
    # a release whose figures the site does not have yet gets no card
    assert 'id="latest"' not in _site(tmp_path, monkeypatch, "Oct 2026")
