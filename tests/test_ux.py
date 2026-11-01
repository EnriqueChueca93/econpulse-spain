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
