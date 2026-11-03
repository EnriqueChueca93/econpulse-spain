"""An RSS 2.0 feed of what changed at each update (site/feed.xml), from the notes changes.py
keeps in data/releases.json: new releases, revisions and big market moves.

Feed readers need absolute links, so items point at config.SITE_URL. Each note becomes an
item with a stable id, so a reader shows it once however often the feed is rebuilt.
"""

import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import format_datetime

from . import i18n
from .changes import note_text, shown_notes
from .config import SITE_URL
from .i18n import _
from .store import Store

FEED_FILE = "feed.xml"       # site/feed.xml in English; site/es/feed.xml in Spanish (Batch 33d)
MAX_ITEMS = 100
KIND_TITLES = {"release": "New data", "revision": "Revision", "market": "Market move"}


def _rfc822(iso: str) -> str:
    return format_datetime(datetime.fromisoformat(iso).astimezone(timezone.utc), usegmt=True)


def build_feed(store: Store, site_url: str = SITE_URL, registry: dict | None = None) -> str:
    """The feed in the language being written: in Spanish the notes are rebuilt in Spanish (changes.note_text,
    which needs the registry's indicators) and the links go to the Spanish pages."""
    es = i18n.lang() == "es"
    base = site_url + ("es/" if es else "")
    saved = store.load_json("releases", None) or {}
    notes = sorted(shown_notes(saved), key=lambda n: n["at"], reverse=True)[:MAX_ITEMS]
    ET.register_namespace("atom", "http://www.w3.org/2005/Atom")
    rss = ET.Element("rss", {"version": "2.0"})
    channel = ET.SubElement(rss, "channel")
    ET.SubElement(channel, "title").text = _("Macroscope Spain: what changed")
    ET.SubElement(channel, "link").text = base
    ET.SubElement(channel, "description").text = _(
        "New releases, revisions and big market moves in Spain's economic data, one item per change, "
        "as found by each Macroscope Spain update.")
    ET.SubElement(channel, "language").text = "es" if es else "en"
    ET.SubElement(channel, "{http://www.w3.org/2005/Atom}link",
                  {"href": base + FEED_FILE, "rel": "self", "type": "application/rss+xml"})
    updated = saved.get("updated_at") or (notes[0]["at"] if notes else None)
    if updated:
        ET.SubElement(channel, "lastBuildDate").text = _rfc822(updated)
    for n in notes:
        text = note_text(n, (registry or {}).get(n["id"])) if es else n["text"]
        kind = _(KIND_TITLES.get(n["kind"], "Update"))
        item = ET.SubElement(channel, "item")
        ET.SubElement(item, "title").text = text
        ET.SubElement(item, "link").text = base + n.get("page", "")
        ET.SubElement(item, "description").text = f"{kind}: {text}"
        ET.SubElement(item, "category").text = kind
        guid = f"econpulse-spain:{n['kind']}:{n['id']}:{n['at']}"
        ET.SubElement(item, "guid", {"isPermaLink": "false"}).text = guid + (":es" if es else "")
        ET.SubElement(item, "pubDate").text = _rfc822(n["at"])
    ET.indent(rss)
    return '<?xml version="1.0" encoding="utf-8"?>\n' + ET.tostring(rss, encoding="unicode") + "\n"
