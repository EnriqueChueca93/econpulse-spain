"""Under each chart, "Source:" links straight to the page with the chart's data (charts.source_links, the
source_line macro in templates/macros.html)."""

from jinja2 import Environment, FileSystemLoader

from econpulse import charts, i18n
from econpulse.config import TEMPLATES_DIR
from econpulse.registry import load_registry
from econpulse.sources import bde

BY_ID = {i.id: i for i in load_registry()}


def links(*items):
    return charts.source_links([(name, BY_ID[i]) for name, i in items], BY_ID)


def test_one_page_per_source_links_the_source_name():
    # three countries from one Eurostat dataset: one page
    assert links(("Spain", "hicp"), ("Euro area", "hicp_euro_area"), ("Germany", "hicp_de")) == \
        [{"name": "Eurostat", "url": BY_ID["hicp"].source_url()}]


def test_several_pages_are_named_by_series_and_the_rest_go_under_show_data():
    two = links(("CPI", "cpi"), ("Industrial production", "industrial_production"))
    assert [link["label"] for link in two[0]["links"]] == ["CPI", "Industrial production"] and two[0]["more"] == []
    regions = [i for i in BY_ID if i.startswith("house_prices_") and BY_ID[i].source == "ine"][:6]
    six = links(*[(i, i) for i in regions])
    assert len(six[0]["links"]) == charts.MAX_LINKS and len(six[0]["more"]) == 6 - charts.MAX_LINKS


def test_a_calculation_links_its_inputs_and_is_credited_last():
    out = links(("GDP deflator", "gdp_deflator"))
    assert out[-1] == {"name": "Macroscope calculation"}
    assert {link["url"] for link in out[0]["links"]} == {BY_ID["gdp_nominal"].source_url(), BY_ID["gdp"].source_url()}


def test_banco_de_espana_links_open_its_series_viewer_in_the_reader_s_language():
    assert bde.source_url("D_1JA0D000") == f"{bde.VIEWER}?SERIE=D_1JA0D000&IDIOMA=EN"
    with i18n.using("es"):
        assert bde.source_url("D_1JA0D000").endswith("IDIOMA=ES")


def _card(spec) -> str:
    env = Environment(loader=FileSystemLoader(TEMPLATES_DIR), extensions=["jinja2.ext.i18n"])
    env.install_gettext_callables(gettext=lambda s, **kw: s % kw if kw else s,
                                  ngettext=lambda s, p, n, **kw: s if n == 1 else p, newstyle=True)
    return env.from_string('{% from "macros.html" import chart_card %}{{ chart_card(c) }}').render(c=spec)


def test_the_line_under_the_chart():
    page = lambda n: {"label": f"S{n}", "url": f"https://example.org/{n}"}
    html = _card({"id": "x", "title": "T", "subtitle": "s", "source": "INE; Eurostat",
                  "sources": [{"name": "INE", "links": [page(i) for i in range(4)], "more": [page(4), page(5)]},
                              {"name": "Eurostat", "url": "https://example.org/es"}, {"name": "Macroscope calculation"}]})
    line = html.split('class="secondary chart-source">')[1].split("</span>\n")[0]
    assert line.startswith("Source: INE &mdash; <a href=\"https://example.org/0\" target=\"_blank\" rel=\"noopener\">S0")
    assert "and 2 more, under Show data; <a href=\"https://example.org/es\"" in line
    assert line.endswith("; Macroscope calculation")
    assert html.count('class="chart-sources"') == 1 and 'href="https://example.org/5"' in html.split("<details")[1]
    plain = _card({"id": "y", "title": "T", "subtitle": "s", "source": "Tesoro Público"})
    assert "Source: Tesoro Público" in plain and "chart-sources" not in plain
