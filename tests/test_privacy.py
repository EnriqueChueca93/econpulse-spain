"""The privacy promises on the About page stay true (no network): nothing is loaded from another site except Google
Analytics, and that only from static/consent.js after a visitor accepts; the only cookie code deletes cookies; every
choice kept in local storage is listed in the notice; and the banner offers "Reject" exactly as it offers "Accept"."""

import re
from pathlib import Path

import pytest
from jinja2 import Environment, FileSystemLoader

from econpulse import disclaimer
from econpulse.build import web_analytics
from econpulse.config import TEMPLATES_DIR

ROOT = Path(__file__).resolve().parents[1]
ABOUT = [ROOT / "templates" / "about.html", ROOT / "templates" / "es" / "about.html"]
CONSENT = ROOT / "static" / "consent.js"
# The keys the notice lists. "ep-sector-freq-" is a prefix: the table's id follows it.
LISTED = {"ep-consent", "ep-theme", "ep-peers", "ep-sector-unit", "ep-sector-freq-", "ep-visits"}


def _front_end() -> list[Path]:
    """Our own templates and scripts. plotly.js is a vendored library, checked separately below."""
    files = list((ROOT / "templates").rglob("*.html")) + list((ROOT / "static").glob("*.js"))
    files += [ROOT / "static" / "style.css"]
    return [f for f in files if f.name != "plotly-basic.min.js"]


def test_no_other_browser_storage_and_cookies_only_deleted():
    for f in _front_end() + [ROOT / "static" / "plotly-basic.min.js"]:
        text = f.read_text(encoding="utf-8")
        for banned in ("sessionStorage", "indexedDB", "sendBeacon"):
            assert banned not in text, f"{f.name} uses {banned}: update the privacy notice on the About page first"
        if f != CONSENT:
            assert "document.cookie" not in text, f"{f.name} touches cookies: only static/consent.js may, to delete them"
    writes = re.findall(r"document\.cookie\s*=[^;]*;[^\n]*", CONSENT.read_text(encoding="utf-8"))
    assert writes and all("Max-Age=0" in w for w in writes), "consent.js may only delete cookies"


def test_every_stored_choice_is_listed_in_the_notice():
    found = set()
    for f in _front_end():
        text = f.read_text(encoding="utf-8")
        if "localStorage" in text:
            found |= set(re.findall(r'"(ep-[a-z-]+)"', text))
    assert found, "expected the theme, peers and sector-table choices"
    assert found <= LISTED, f"stored but not in the privacy notice: {sorted(found - LISTED)}"
    for page in ABOUT:
        text = page.read_text(encoding="utf-8")
        assert 'id="privacy"' in text and "data-forget-choices" in text
        for key in LISTED:
            assert f"<code>{key}</code>" in text, f"{page.name} doesn't list {key}"


def test_nothing_is_loaded_from_another_site():
    """Scripts, styles, fonts, images and frames all come from the site itself. Plain links to other sites are fine:
    they load nothing until clicked. Google Analytics is the one exception, tested below."""
    external = re.compile(
        r'<script[^>]*\bsrc="(?:https?:)?//'
        r'|<link[^>]*\brel="(?:stylesheet|preload|preconnect|dns-prefetch|modulepreload)"[^>]*\bhref="(?:https?:)?//'
        r'|<link[^>]*\bhref="(?:https?:)?//[^"]*"[^>]*\brel="(?:stylesheet|preload|preconnect|dns-prefetch)"'
        r'|<(?:img|iframe|embed|object|source|video|audio)\b[^>]*\b(?:src|data)="(?:https?:)?//'
        r'|@import|url\(\s*["\']?(?:https?:)?//',
        re.IGNORECASE)
    for f in _front_end():
        hit = external.search(f.read_text(encoding="utf-8"))
        assert hit is None, f"{f.name} loads from another site: {hit.group(0)[:80]}"


def test_google_analytics_loads_only_from_consent_js_and_only_after_a_yes():
    for f in _front_end():
        text = f.read_text(encoding="utf-8")
        if f != CONSENT:
            assert "googletagmanager" not in text and "gtag(" not in text, f"{f.name} reaches Google outside consent.js"
    lines = CONSENT.read_text(encoding="utf-8").splitlines()
    calls = [line for line in lines if re.search(r"\bload\(\)", line) and "function load" not in line]
    assert calls and all('=== "yes"' in line for line in calls), "load() must follow a stored or given yes"
    assert 'ad_storage: "denied"' in "\n".join(lines) and "allow_google_signals: false" in "\n".join(lines)


def test_analytics_stays_off_until_every_setting_is_there():
    assert web_analytics(None, None, None) is None
    assert web_analytics("G-ABC123XYZ", "A. Person", None) is None   # no contact for the notice: no analytics
    on = web_analytics("G-ABC123XYZ", "A. Person", "https://github.com/someone")
    assert on["path"] == "/macroscope-spain/" and on["contact_label"] == "github.com/someone"
    assert web_analytics("G-ABC123XYZ", "A. Person", "mailto:a@example.org")["contact_label"] == "a@example.org"
    with pytest.raises(ValueError):
        web_analytics("UA-12345-1", "A. Person", "https://github.com/someone")


def _base(ga) -> str:
    env = Environment(loader=FileSystemLoader(TEMPLATES_DIR), extensions=["jinja2.ext.i18n"])
    env.install_gettext_callables(gettext=lambda s: s, ngettext=lambda s, p, n: s if n == 1 else p, newstyle=True)
    return env.get_template("base.html").render(lang="en", root="", page_file="index.html", ga=ga, sources=[],
                                                disclaimer=disclaimer.context("A. Person", None))


def test_the_banner_offers_reject_exactly_as_it_offers_accept():
    html = _base(web_analytics("G-ABC123XYZ", "A. Person", "https://github.com/someone"))
    banner = re.search(r'<section class="consent".*?</section>', html, re.S).group(0)
    buttons = re.findall(r'<button type="button" class="([^"]+)" data-consent="(yes|no)">', banner)
    assert sorted(b[1] for b in buttons) == ["no", "yes"] and len({b[0] for b in buttons}) == 1
    assert " hidden " in banner and 'href="about.html#privacy"' in banner and "third-party" in banner
    assert "data-cookie-settings" in html and "assets/consent.js" in html
    off = _base(None)
    assert 'class="consent"' not in off and "consent.js" not in off and "data-cookie-settings" not in off
