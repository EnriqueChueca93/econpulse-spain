"""Banco de España macroeconomic projections for Spain, read from its quarterly report pages.

The bank publishes no data feed for its projections, but each report's web page carries
them in a table. The list of reports is asked for newest first (?sort=DESC: since November 2026
its default order is oldest first), and the report taken is the one with the latest date listed,
which must be recent, so a change of order can't silently bring back an old report. Key is a row label of
the English table up to its first bracket: "GDP", "HICP", "Unemployment rate",
"General government net lending". Figures read this way are shown on the site as
awaiting an AI check until confirmed (see econpulse/forecasts.py).
"""

import re
import threading
from datetime import date

from .. import http
from .base import FetchResult, madrid_today, make_series
from .webtables import number, read_tables, year

SITE = "https://www.bde.es"
INDEX = f"{SITE}/wbe/en/publicaciones/analisis-economico-investigacion/proyecciones-macro-informe-trimestral/"
_REPORT = re.compile(r'href="(/wbe/en/publicaciones/analisis-economico-investigacion/proyecciones-macro-informe-trimestral/'
                     r'proyecciones-e-informe-trimestral[^"]*\.html)"')
_ENTRY = re.compile(r'block-search-result__date">\s*(\d{2})/(\d{2})/(\d{4})\s*</p>.*?href="'
                    r'(/wbe/en/publicaciones/analisis-economico-investigacion/proyecciones-macro-informe-trimestral/[^"]+\.html)"',
                    re.S)
LISTING = INDEX + "?sort=DESC"
MAX_AGE_DAYS = 240                  # a report every quarter: anything older means the listing was misread
_DATE = re.compile(r'block-entry-content__info">\s*<p>\s*(\d{2})/(\d{2})/(\d{4})\s*</p>')

_lock = threading.Lock()
_cache: dict = {}   # the report is read once per run, for all four rows


def source_url(key: str, params: dict | None = None) -> str:
    return INDEX


def newest_report(index_html: str, today: date | None = None) -> str:
    """The report with the latest date in the listing (or, with no dates, the first report link)."""
    entries = [(date(int(y), int(m), int(d)), href) for d, m, y, href in _ENTRY.findall(index_html)]
    if not entries:
        m = _REPORT.search(index_html)
        if not m:
            raise ValueError("no report link on the Banco de España projections page")
        return SITE + m.group(1)
    newest, href = max(entries)
    if ((today or madrid_today()) - newest).days > MAX_AGE_DAYS:
        raise ValueError(f"the newest report on the Banco de España projections page is from {newest}: "
                         "has the listing's order or layout changed?")
    return SITE + href


def _label(text: str) -> str:
    return text.split(" (", 1)[0].strip().rstrip(".")


def parse_report(html: str) -> tuple[dict[str, dict[int, float]], date | None]:
    """The projections table ({row label: {year: value}}) and the report's date."""
    m = _DATE.search(html)
    published = date(int(m[3]), int(m[2]), int(m[1])) if m else None
    for table in read_tables(html):
        years_row = next((r for r in table if sum(year(c) is not None for c in r) >= 3), None)
        if years_row is None:
            continue
        # The first column for each year: later ones are revisions against the previous round.
        columns = {}
        for i, c in enumerate(years_row):
            if (y := year(c)) is not None and y not in columns.values():
                columns[i] = y
        rows = {}
        for r in table:
            if r and r[0] and r is not years_row:
                values = {y: v for i, y in columns.items() if i < len(r) and (v := number(r[i])) is not None}
                if values:
                    rows.setdefault(_label(r[0]), values)
        if "GDP" in rows:
            return rows, published
    raise ValueError("no projections table (with a GDP row) on the report page")


def _report() -> dict:
    with _lock:
        if "error" in _cache:
            raise _cache["error"]
        if "rows" not in _cache:
            try:
                url = newest_report(http.get(LISTING).text)
                rows, published = parse_report(http.get(url).text)
                _cache.update(rows=rows, published=published, url=url)
            except Exception as e:
                _cache["error"] = e
                raise
        return _cache


def clear_cache() -> None:
    with _lock:
        _cache.clear()


def fetch(key: str, params: dict | None = None, **_) -> FetchResult:
    report = _report()
    if key not in report["rows"]:
        raise ValueError(f"no row {key!r} in the projections table; rows: {', '.join(report['rows'])}")
    values = sorted(report["rows"][key].items())
    meta = {"url": report["url"]}
    if report["published"]:
        meta["published"] = report["published"].isoformat()
    return FetchResult(make_series((date(y, 1, 1) for y, _ in values), (v for _, v in values)), meta)
