"""Batch U1: site-wide usability (no network). The browser behaviour (charts drawn as they scroll into
view, CSV downloads, section links, back to top) lives in static/app.js; these tests check the markup and
files it relies on."""

from econpulse.registry import load_registry
from econpulse.build import build_site
from econpulse.config import SITE_URL

from test_trade import full_store


def test_every_page_has_its_own_description_and_previews(tmp_path):
    build_site(load_registry(), full_store(tmp_path), site_dir=tmp_path / "site")
    site = tmp_path / "site"
    labour = (site / "labour.html").read_text(encoding="utf-8")
    assert 'rel="icon" href="assets/favicon.svg"' in labour and (site / "assets" / "favicon.svg").exists()
    assert '<meta property="og:title" content="Labour market · EconPulse Spain">' in labour
    descriptions = set()
    for page in site.glob("*.html"):
        html = page.read_text(encoding="utf-8")
        start = html.index('<meta name="description" content="') + len('<meta name="description" content="')
        descriptions.add(html[start:html.index('"', start)])
    assert len(descriptions) >= len(list(site.glob("*.html"))) - 1    # only the home page keeps the site's line


def test_chart_cards_offer_csv_and_tables_keep_their_labels(tmp_path):
    build_site(load_registry(), full_store(tmp_path), site_dir=tmp_path / "site")
    trade = (tmp_path / "site" / "trade.html").read_text(encoding="utf-8")
    assert trade.count('class="chart-link chart-csv"') == trade.count('class="card chart-card"') > 0
    assert '<tr class="group-row"><td colspan="7"><span>Food and drink</span></td></tr>' in trade
    tools = (tmp_path / "site" / "tools.html").read_text(encoding="utf-8")
    assert 'class="chart-link chart-csv" data-chart="trend-line" hidden' in tools   # shown once the chart is drawn


def test_not_found_page(tmp_path):
    build_site(load_registry(), full_store(tmp_path), site_dir=tmp_path / "site")
    html = (tmp_path / "site" / "404.html").read_text(encoding="utf-8")
    assert "<h1>Page not found</h1>" in html and '<base href="/econpulse-spain/">' in html
    assert SITE_URL.endswith("/econpulse-spain/") and 'href="trade.html"' in html and 'aria-current="page"' not in html


def test_search_index(tmp_path):
    """Batch U3: pages, sections, charts and series, each linked to where the site shows it."""
    import json

    build_site(load_registry(), full_store(tmp_path), site_dir=tmp_path / "site")
    site = tmp_path / "site"
    text = (site / "data" / "search.js").read_text(encoding="utf-8")
    index = json.loads(text[text.index("["):text.rindex("]") + 1])
    by_title = {}
    for kind, title, context, href, extra in index:
        by_title.setdefault((kind, title), (context, href, extra))
    assert by_title[(0, "Trade")][1] == "trade.html" and by_title[(1, "Trade by partner")][1] == "trade.html#partners"
    assert by_title[(2, "Exports by partner")][1] == "trade.html#fig-partner-exports-ranking"
    context, href, extra = by_title[(3, "Goods exports to China")]
    assert href == "trade.html#partners" and context == "Trade · Eurostat (Comext)" and "China" in extra
    assert by_title[(3, "Services exports, transport")][1] == "trade.html#services"
    # a series nobody charts links to its row on the Data page, which carries that anchor
    orphans = [href for kind, _, _, href, _ in index if kind == 3 and href.startswith("data.html#ind-")]
    data = (site / "data.html").read_text(encoding="utf-8")
    assert orphans and all(f'id="{href.split("#")[1]}"' in data for href in orphans)
    html = (site / "labour.html").read_text(encoding="utf-8")
    assert 'id="search-open"' in html and 'data-index="data/search.js?v=' in html and 'role="dialog"' in html


def test_series_link_to_their_own_page():
    from econpulse.pages import indicator_anchors

    built = {"gdp": {"blocks": [{"id": "real-sector"}]}, "labour": {"blocks": [{"id": "epa"}]}}
    anchors = indicator_anchors(built, {"unemployment_epa": "labour"})
    assert anchors["unemployment_epa"] == "labour.html#epa"   # shown on GDP's IMF table too, but its home is Labour


def test_charts_only_use_what_the_basic_bundle_has(tmp_path):
    """Batch U4: the site ships Plotly's basic bundle (scatter, bar and pie traces); a chart of any other
    type would fail to draw, so none may appear in the scripts or templates."""
    import re
    from pathlib import Path

    root = Path(__file__).resolve().parent.parent
    sources = [p for p in list((root / "static").glob("*.js")) + list((root / "templates").glob("*.html"))
               if not p.name.endswith(".min.js")]
    used = {t for p in sources for t in re.findall(r'type:\s*["\'](\w+)["\']', p.read_text(encoding="utf-8"))}
    axes_and_shapes = {"date", "category", "linear", "log", "line", "rect", "circle", "path"}
    assert used - axes_and_shapes <= {"scatter", "bar", "pie"} and {"scatter", "bar"} <= used
    bundle = (root / "static" / "plotly-basic.min.js").read_text(encoding="utf-8")
    assert "plotly.js (basic - minified) v4.1.1" in bundle[:120] and "MIT license" in bundle[:200]
    build_site(load_registry(), full_store(tmp_path), site_dir=tmp_path / "site")
    site = tmp_path / "site"
    assert 'src="assets/plotly-basic.min.js?v=' in (site / "trade.html").read_text(encoding="utf-8")
    assert not (site / "assets" / "plotly.min.js").exists()


def test_fresh_series_and_marks(tmp_path):
    """Batch U5: which series brought figures in the past week, and the mark a section gets."""
    import pandas as pd

    from econpulse import changes
    from econpulse.store import Store

    store = Store(tmp_path / "data")
    today = pd.Timestamp("2026-11-01")
    items = {"cpi": {"label": "CPI inflation", "headline": {"period": "Oct 2026"}},
             "gdp": {"label": "Real GDP", "headline": {"period": "Q3 2026"}},
             "ppi": {"label": "Producer prices", "headline": {"period": "Aug 2026"}},
             "exports": {"label": "Goods exports", "headline": {"period": "Aug 2026"}}}
    events = [{"when": pd.Timestamp("2026-10-30 09:00"), "period": "Oct 2026", "ids": ["cpi"]},
              {"when": pd.Timestamp("2026-10-26 09:00"), "period": "Sep 2026", "ids": ["ppi"]},   # not shown yet
              {"when": pd.Timestamp("2026-10-20 09:00"), "period": "Q3 2026", "ids": ["gdp"]},    # too old
              {"when": pd.Timestamp("2026-11-04 09:00"), "period": "Oct 2026", "ids": ["gdp"]}]   # not yet
    store.save_json("releases", {"state": {}, "notes": [
        {"kind": "release", "id": "exports", "at": "2026-10-31T21:23:00+00:00"},       # 31 Oct in Madrid
        {"kind": "revision", "id": "gdp", "at": "2026-10-31T21:23:00+00:00"}]})
    fresh = changes.fresh_series(store, items, events, today)
    assert set(fresh) == {"cpi", "exports"} and fresh["exports"]["day"] == pd.Timestamp("2026-10-31")
    mark = changes.updated_mark(["exports", "cpi", "gdp"], fresh, {k: v["label"] for k, v in items.items()})
    assert mark == {"day": "31 Oct", "what": "Goods exports (Aug 2026); CPI inflation (Oct 2026)"}
    assert changes.updated_mark(["gdp"], fresh, {}) is None


def test_updated_sections_are_marked_and_linked(tmp_path):
    from datetime import datetime, timezone

    store = full_store(tmp_path)
    store.save_json("releases", {"state": {}, "updated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                                 "notes": [{"kind": "release", "id": "trade_exp_total", "page": "international.html",
                                            "text": "Goods exports (Comext): €401,843 mn in Aug 2026.",
                                            "at": datetime.now(timezone.utc).isoformat(timespec="seconds")}]})
    build_site(load_registry(), store, site_dir=tmp_path / "site")
    site = tmp_path / "site"
    trade = (site / "trade.html").read_text(encoding="utf-8")
    assert 'Exports, imports and the balance <span class="badge badge-ok badge-updated" title="New figures: ' \
           'Goods exports (Comext) (Aug 2026)">Updated' in trade
    # The page's own section list, and the Economic activity tab's link to it (Trade is no longer a tab: Batch 32a).
    assert '<a href="#overview" class="has-new"' in trade and '<a href="trade.html" class="has-new"' in trade
    index = (site / "index.html").read_text(encoding="utf-8")
    assert '<a href="trade.html#overview">Goods exports (Comext): €401,843 mn in Aug 2026.</a>' in index


def test_international_page_has_the_comparator_chooser(tmp_path):
    """The chooser is on the International page only, with Spain left out (it is always drawn)."""
    from test_comparators import comparator_store

    build_site(load_registry(), comparator_store(tmp_path), site_dir=tmp_path / "site")
    html = (tmp_path / "site" / "international.html").read_text(encoding="utf-8")
    assert 'id="country-picker" data-max="3"' in html and 'data-default="ea,de,us"' in html
    assert html.count('class="chip" data-country=') == 11 and 'data-country="es"' not in html
    assert 'id="country-picker"' not in (tmp_path / "site" / "labour.html").read_text(encoding="utf-8")
