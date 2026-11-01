"""Batch 14: the RSS feed, quieter revision notes and chart links (no network)."""

import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone

import numpy as np
import pandas as pd

from econpulse import changes, feed
from econpulse.build import build_site
from econpulse.registry import Indicator, load_registry
from econpulse.store import Store

NOTES = [
    {"kind": "release", "id": "gdp", "page": "gdp.html", "text": "Real GDP: 0.6% q/q in Q3 2026, after 0.7% in Q2 2026.",
     "at": "2026-10-30T09:05:00+00:00"},
    {"kind": "revision", "id": "us_cpi_index", "page": "international.html",
     "text": "CPI, United States for Sep 2026 revised to 3.7% y/y, from 3.7% y/y.", "at": "2026-10-31T02:50:46+00:00"},
    {"kind": "market", "id": "es_10y", "page": "financial.html",
     "text": "Spain 10-year yield: +12 bp since the last update, to 3.55%.", "at": "2026-10-31T17:40:00+00:00"},
]


def test_feed_items(tmp_path):
    store = Store(tmp_path / "data")
    store.save_json("releases", {"state": {}, "notes": NOTES, "updated_at": "2026-10-31T17:40:00+00:00"})
    root = ET.fromstring(feed.build_feed(store, site_url="https://example.org/site/"))
    channel = root.find("channel")
    assert channel.findtext("lastBuildDate") == "Sat, 31 Oct 2026 17:40:00 GMT"
    items = channel.findall("item")
    # Newest first; the revision that changed nothing as shown is left out.
    assert [i.findtext("category") for i in items] == ["Market move", "New data"]
    assert items[0].findtext("link") == "https://example.org/site/financial.html"
    assert items[1].findtext("guid") == "econpulse-spain:release:gdp:2026-10-30T09:05:00+00:00"
    assert items[1].findtext("pubDate") == "Fri, 30 Oct 2026 09:05:00 GMT"
    assert root.find("channel/{http://www.w3.org/2005/Atom}link").get("href") == "https://example.org/site/feed.xml"


def test_feed_without_notes(tmp_path):
    root = ET.fromstring(feed.build_feed(Store(tmp_path / "data")))
    assert root.find("channel/item") is None and root.findtext("channel/title")


def test_revisions_that_change_nothing_shown_are_not_logged(tmp_path):
    store = Store(tmp_path / "data")
    ind = Indicator(id="cpi", label="CPI inflation", label_es="IPC", section="inflation", source="fake", key="cpi",
                    freq="M", unit="%", change_unit="pp")
    months = pd.date_range("2026-07-01", periods=3, freq="MS")
    store.save_series("cpi", pd.Series([3.0, 3.2, 3.51], index=months))
    t0 = datetime(2026, 10, 31, 12, tzinfo=timezone.utc)
    changes.record([ind], store, now=t0)
    store.save_series("cpi", pd.Series([3.0, 3.2, 3.53], index=months))   # still 3.5% as shown
    assert changes.record([ind], store, now=t0 + timedelta(days=1)) == []
    store.save_series("cpi", pd.Series([3.0, 3.2, 3.62], index=months))
    assert [n["text"] for n in changes.record([ind], store, now=t0 + timedelta(days=2))] == \
        ["CPI inflation for Sep 2026 revised to 3.6%, from 3.5%."]


def test_site_links_the_feed_and_every_chart(tmp_path):
    store = Store(tmp_path / "data")
    q = pd.date_range("2005-01-01", "2026-07-01", freq="QS")
    store.save_series("gdp", pd.Series(100 * 1.005 ** np.arange(len(q)), index=q))
    build_site(load_registry(), store, site_dir=tmp_path / "site")
    site = tmp_path / "site"
    assert (site / "feed.xml").exists()
    gdp = (site / "gdp.html").read_text(encoding="utf-8")
    assert 'type="application/rss+xml"' in gdp and 'href="feed.xml">RSS feed</a>' in gdp
    figures = gdp.count('<figure class="card chart-card" id="fig-')
    assert figures > 0 and gdp.count('class="chart-link" data-figure="fig-') == figures
    tools = (site / "tools.html").read_text(encoding="utf-8")
    assert 'id="fig-trend-line"' in tools and 'data-figure="fig-trend-line"' in tools
