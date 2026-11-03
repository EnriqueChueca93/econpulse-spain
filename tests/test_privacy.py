"""The privacy promises on the About page stay true: no cookies, nothing loaded from other sites, and every
choice kept in local storage listed in the notice (no network)."""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ABOUT = [ROOT / "templates" / "about.html", ROOT / "templates" / "es" / "about.html"]
# The keys the notice lists. "ep-sector-freq-" is a prefix: the table's id follows it.
LISTED = {"ep-theme", "ep-peers", "ep-sector-unit", "ep-sector-freq-"}


def _front_end() -> list[Path]:
    """Our own templates and scripts. plotly.js is a vendored library, checked separately below."""
    files = list((ROOT / "templates").rglob("*.html")) + list((ROOT / "static").glob("*.js"))
    files += [ROOT / "static" / "style.css"]
    return [f for f in files if f.name != "plotly-basic.min.js"]


def test_no_cookies_or_other_browser_storage():
    for f in _front_end() + [ROOT / "static" / "plotly-basic.min.js"]:
        text = f.read_text(encoding="utf-8")
        for banned in ("document.cookie", "sessionStorage", "indexedDB", "sendBeacon"):
            assert banned not in text, f"{f.name} uses {banned}: update the privacy notice on the About page first"


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
    """Scripts, styles, fonts, images and frames all come from the site itself, so no third party sees a visit.
    Plain links to other sites are fine: they load nothing until clicked."""
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
