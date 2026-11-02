"""Batch 18: the tab dropdowns list each page's sections (no network)."""

import numpy as np
import pandas as pd

from econpulse.build import build_site, nav_items
from econpulse.registry import load_registry
from econpulse.store import Store


def test_nav_items_list_sections_and_extras():
    pages = {"gdp": {"blocks": [{"id": "growth", "title": "GDP and its components"}]}}
    items = {i["href"]: i for i in nav_items(pages)}
    assert items["gdp.html"]["children"] == [{"href": "gdp.html#growth", "title": "GDP and its components", "new": False}]
    tools = [c["href"] for c in items["tools.html"]["children"]]
    assert "tools.html#taylor" in tools and "fiscal-explorer.html" in tools and "ecb-speak.html" in tools
    assert items["data.html"]["children"] == []   # no dropdown
    fresh = {i["href"]: i for i in nav_items(pages, {"gdp.html#growth"})}   # a section updated in the past week
    assert fresh["gdp.html"]["children"][0]["new"] is True


def test_every_page_has_the_dropdowns(tmp_path):
    store = Store(tmp_path / "data")
    q = pd.date_range("2005-01-01", "2026-07-01", freq="QS")
    store.save_series("gdp", pd.Series(100 * 1.005 ** np.arange(len(q)), index=q))
    build_site(load_registry(), store, site_dir=tmp_path / "site")
    html = (tmp_path / "site" / "inflation.html").read_text(encoding="utf-8")
    assert 'aria-controls="menu-gdp"' in html and 'id="menu-gdp" hidden' in html
    assert 'id="menu-tools" hidden' in html and 'href="ecb-speak.html">ECB-speak</a>' in html
    gdp = (tmp_path / "site" / "gdp.html").read_text(encoding="utf-8")
    first_block = gdp.split('<h2 id="', 1)[1].split('"', 1)[0]
    assert f'href="gdp.html#{first_block}"' in gdp   # the menu links to the page's own sections


def test_section_pages_link_their_sub_pages(tmp_path):
    """Trade sits under Economic activity and the communities' Budget explorer under Regions (Batch 32a): each
    is in the tab's dropdown and in its page's list of sections."""
    store = Store(tmp_path / "data")
    m = pd.date_range("2015-01-01", "2026-08-01", freq="MS")
    store.save_series("industrial_production", pd.Series(100 + np.arange(len(m)) * 0.1, index=m))
    build_site(load_registry(), store, site_dir=tmp_path / "site")
    activity = (tmp_path / "site" / "activity.html").read_text(encoding="utf-8")
    assert '<a href="trade.html">Trade in goods and services <span aria-hidden="true">&rarr;</span></a>' in activity
    items = {i["href"]: i for i in nav_items({"regions": {"blocks": []}})}
    assert [c["href"] for c in items["regions.html"]["children"]] == ["budget-explorer.html#level=regions"]
    assert "budget-explorer.html#level=regions" in [c["href"] for c in items["tools.html"]["children"]]
    assert "trade.html" not in items

