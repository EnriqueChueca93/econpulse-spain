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
