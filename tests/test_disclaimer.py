"""The disclaimer stays where readers meet the data (no network): every page's footer, the About page's full terms in
both languages (with the wording INE and the OECD ask for), the notes on Analysis, Financial and Tools, the RSS feed
and the workbook's "Read me" sheet."""

import xml.etree.ElementTree as ET
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from econpulse import disclaimer, feed
from econpulse.config import TEMPLATES_DIR
from econpulse.store import Store

ROOT = Path(__file__).resolve().parents[1]


def _env() -> Environment:
    env = Environment(loader=FileSystemLoader(TEMPLATES_DIR), extensions=["jinja2.ext.i18n"])
    env.install_gettext_callables(gettext=lambda s: s, ngettext=lambda s, p, n: s if n == 1 else p, newstyle=True)
    return env


def test_every_page_footer_carries_the_disclaimer_and_the_licence():
    html = _env().get_template("base.html").render(lang="en", root="", page_file="index.html", sources=[],
                                                    disclaimer=disclaimer.context("A. Person", "mailto:a@example.org"))
    footer = html[html.index('<footer class="site-footer">'):]
    assert "not investment, financial or tax advice" in footer and "not affiliated with or endorsed" in footer
    assert 'href="about.html#disclaimer"' in footer
    assert f'href="{disclaimer.LICENCE_URL}" rel="license noopener"' in footer and "A. Person" in footer


def test_the_about_page_has_the_full_terms_in_both_languages():
    en, es = (" ".join((ROOT / "templates" / f).read_text(encoding="utf-8").split()) for f in ("about.html", "es/about.html"))
    for page in (en, es):
        assert 'id="disclaimer"' in page and "creativecommons.org/licenses/by-nc/4.0/" in page
        assert page.index('id="disclaimer"') < page.index('id="privacy"')
    # the wording INE asks for when its data are transformed, and the OECD's for adaptations
    assert "own elaboration with data extracted from INE's website" in en
    assert "elaboración propia con datos extraídos del sitio web del INE" in es
    assert "an adaptation of an original work by the OECD" in en and "una adaptación de una obra original de la OCDE" in es
    assert "not investment" not in es and "asesoramiento de inversión" in es


def test_analysis_financial_and_tools_carry_a_note():
    for page in ("analysis", "financial", "tools"):
        assert disclaimer.page_note(page)
    assert disclaimer.page_note("gdp") is None
    html = _env().get_template("section.html").render(page={"title": "Analysis", "intro": "x", "batch": 7}, blocks=[],
                                                       items=[], note=disclaimer.page_note("analysis"), sources=[],
                                                       disclaimer=disclaimer.context(None, None))
    assert '<p class="notice page-note">Macroscope' in html
    for tools in (ROOT / "templates" / "tools.html", ROOT / "templates" / "es" / "tools.html"):
        assert "page-note" in tools.read_text(encoding="utf-8")


def test_the_feed_and_the_workbook_say_it_too(tmp_path):
    channel = ET.fromstring(feed.build_feed(Store(tmp_path / "data"))).find("channel")
    assert disclaimer.SHORT in channel.findtext("description")
    assert "CC BY-NC 4.0" in channel.findtext("copyright")
    lines = disclaimer.readme_lines("3 Nov 2026")
    assert disclaimer.SHORT in lines and any("INE's website" in line for line in lines)
    assert any(disclaimer.LICENCE_URL in line for line in lines)
