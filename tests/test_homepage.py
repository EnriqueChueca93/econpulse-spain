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
    store.save_json("releases", {"state": {}, "notes": [
        {"kind": "release", "id": "cpi", "page": "inflation.html", "at": "2026-11-04T19:08:42+00:00", "text": "CPI inflation: 4.9% in Sep 2026, after 3.0% in Aug 2026."}]})
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
    # when the site got the figures, for "Since your last visit", which the reader turns on (hidden without a script)
    assert tile.count('data-changed="2026-11-04T19:08:42+00:00"') == 1
    assert latest.count('data-changed="2026-11-04T19:08:42+00:00"') == 1
    assert 'id="since-visit" hidden data-build="' in html and "Turn it on" in html
    # the chart of the week, drawn from the home page's charts file
    week = html.split('id="chart-of-the-week"')[1].split("</section>")[0]
    assert 'id="chart-week"' in week and "Sep 2026: 4.9%. The highest since Jun 2025." in week
    assert "This one is from CPI, out on" in week
    assert '"id":"week"' in (tmp_path / "site" / "data" / "charts.js").read_text(encoding="utf-8")
    # a release whose figures the site does not have yet gets no card
    assert 'id="latest"' not in _site(tmp_path, monkeypatch, "Oct 2026")


def _item(i, label, period, transform="level", display="4.9%", unit=""):
    return {"id": i, "label": label, "flash": False,
            "headline": {"transform": transform, "display": display, "label": unit, "period": period}}


def test_changed_times_take_the_latest_release_or_revision_but_not_market_moves(tmp_path):
    store = Store(tmp_path)
    store.save_json("releases", {"state": {}, "notes": [
        {"kind": "release", "id": "cpi", "at": "2026-11-01T10:00:00+00:00", "text": "CPI: ..."},
        {"kind": "revision", "id": "cpi", "at": "2026-11-03T10:00:00+00:00", "text": "CPI for Sep revised to 3.1%, from 3.0%."},
        {"kind": "revision", "id": "gdp", "at": "2026-11-04T10:00:00+00:00", "text": "GDP for Q3 revised to 0.6%, from 0.6%."},
        {"kind": "market", "id": "es_10y", "at": "2026-11-04T10:00:00+00:00", "text": "Spain 10-year: +12 bp"},
    ]})
    # a "revision" that changed nothing as shown is no news; a market move is not a new figure
    assert homepage.changed_times(store) == {"cpi": "2026-11-03T10:00:00+00:00"}


def test_subtitle_says_what_the_figure_is():
    m, q = ind(id="m", unit="thousands"), ind(id="q", freq="Q")
    assert homepage.subtitle(m, "yoy") == "% change on a year earlier"
    assert homepage.subtitle(q, "pop") == "% change on the previous quarter"
    assert homepage.subtitle(m, "sa_diff") == "Change on the previous month, thousands, seasonally adjusted by Macroscope"
    assert homepage.subtitle(m, "level") == "Thousands"
    with i18n.using("es"):
        assert homepage.subtitle(m, "yoy") == "Variación interanual, %"
        assert homepage.subtitle(q, "pop") == "Variación intertrimestral, %"


def test_chart_of_the_week_is_the_figure_furthest_back_at_its_high_or_low(tmp_path):
    store = Store(tmp_path)
    today = pd.Timestamp("2026-11-05")
    # producer prices: the highest since Aug 2023 (37 months back); arrivals: nothing notable, but newer
    store.save_series("ppi", monthly(np.r_[np.linspace(5, 20, 30), [20.0], np.linspace(19, 3, 38), [18.3]]))
    store.save_series("arrivals", monthly(np.r_[np.linspace(1, 9, 39), [8.0]]))
    registry = {"ppi": ind(id="ppi", label="Producer prices"), "arrivals": ind(id="arrivals", label="Tourist arrivals")}
    items = {"ppi": _item("ppi", "Producer prices", "Sep 2026", display="18.3%"),
             "arrivals": _item("arrivals", "Tourist arrivals", "Sep 2026", display="1.0%")}
    events = [{"when": today - pd.Timedelta(days=d, hours=-9), "label": label, "period": "Sep 2026",
               "page": "activity.html", "ids": [i]} for d, label, i in ((3, "PPI", "ppi"), (1, "FRONTUR", "arrivals"))]
    week = homepage.chart_of_the_week(store, items, registry, events, today)
    spec = week["spec"]
    assert week["release"] == "PPI" and spec["id"] == "week" and spec["title"] == "Producer prices"
    assert spec["series"][0]["name"] == "Producer prices" and spec["kind"] == "line"
    assert spec["reading"] == "Sep 2026: 18.3%. The highest since Aug 2023."
    assert spec["ref_lines"] == [{"y": 18.3, "label": "Sep 2026"}]
    assert spec["series"][0]["x"][0] <= "2021-08-01"          # back far enough to show the earlier high
    # with nothing notable, the newest release; in Spanish too
    store.save_series("ppi", monthly(np.r_[np.linspace(1, 9, 39), [8.0]]))
    assert homepage.chart_of_the_week(store, items, registry, events, today)["release"] == "FRONTUR"
    with i18n.using("es"):
        assert homepage.chart_of_the_week(store, items, registry, events, today)["spec"]["title"] == "Tourist arrivals"
    # nothing out in the past week: no chart
    assert homepage.chart_of_the_week(store, items, registry, events, today + pd.Timedelta(days=10)) is None


def test_the_chart_of_the_week_starts_after_covid_swings_that_would_flatten_it():
    # Oct 2016 to Sep 2026: a reading moving between 2 and 8, and a surge to 15 in 2020-22
    calm = 5 + 3 * np.sin(np.arange(120) / 4)
    calm[41:75] = np.linspace(5, 15, 34)
    start, keep = pd.Timestamp("2016-10-01"), pd.Timestamp("2024-09-01")
    # a surge within twice the range of the rest stays (the 2022 inflation surge)
    assert homepage.calm_start(monthly(calm), start, keep) == start
    # a Covid-era jump far outside it is cut: the chart starts the month after the last one
    wild = calm.copy()
    wild[[42, 54]] = [900.0, -400.0]                                          # Apr 2020 and Apr 2021
    assert homepage.calm_start(monthly(wild), start, keep) == pd.Timestamp("2021-05-01")
    # but never past a reading the chart must show
    assert homepage.calm_start(monthly(wild), start, pd.Timestamp("2021-01-01")) == pd.Timestamp("2020-05-01")
    # outside the Covid years nothing is cut
    late = calm.copy()
    late[100] = 900.0                                                       # Feb 2025
    assert homepage.calm_start(monthly(late), start, keep) == start
