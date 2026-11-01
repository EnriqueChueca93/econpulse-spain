"""FUNCAS Panel de previsiones: the consensus of about 19 forecasters for Spain, every two months.

FUNCAS's website (WordPress) lists the panel posts through its public REST API, newest
first. The newest post's tables are read when it has them; otherwise its PDF, with
pdfplumber. For reference the panel also shows the latest forecasts of the government
and AIReF, labelled with their month ("Gobierno (junio 2026)"), which is how those two
reach the site.

Key is "<row>/<measure>":
    row      consensus, max, min (the highest and lowest panelist), government, airef
    measure  gdp, inflation (CPI, annual average), unemployment, balance (general government, % of GDP)
Figures read this way are shown as awaiting an AI check until confirmed (econpulse/forecasts.py).
"""

import io
import json
import re
import threading
from datetime import date

from .. import http
from .base import FetchResult, make_series
from .webtables import number, read_tables, year

API = "https://www.funcas.es/wp-json/wp/v2/textointegro"
ROWS = {"consensus": r"^CONSENSO", "max": r"^M[áa]ximo", "min": r"^M[íi]nimo",
        "government": r"^Gobierno\b", "airef": r"^AIReF\b"}
MEASURES = {"gdp": r"^PIB\b", "inflation": r"^IPC general", "unemployment": r"^Tasa de\s*desempleo",
            "balance": r"^Saldo AA\.?\s*PP"}
MONTHS = {m: i for i, m in enumerate(("enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto",
                                      "septiembre", "octubre", "noviembre", "diciembre"), start=1)}
# The PDF's two tables, told apart by how many figures each row has (pairs of years):
# national accounts (PIB first) and prices, jobs and public finances.
PDF_LAYOUTS = [(18, "PIB", {"gdp": 0}), (14, "IPC general", {"inflation": 0, "unemployment": 4, "balance": 6})]
_PDF_ROW = re.compile(r"^(CONSENSO \(MEDIA\)|M[áa]ximo|M[íi]nimo|Gobierno \([^)]*\)|AIReF \([^)]*\))\s+(.+)$")
_PDF_LINK = re.compile(r'href="(https://www\.funcas\.es/wp-content/uploads/\d{4}/\d{2}/PP\d{4}\.pdf)"')

_lock = threading.Lock()
_cache: dict = {}   # the panel is read once per run, for every key

Rows = dict[str, dict]   # row key -> {"label": printed label, "values": {measure: {year: value}}}


def source_url(key: str, params: dict | None = None) -> str:
    return "https://www.funcas.es/?s=panel+de+previsiones"


def row_key(label: str) -> str | None:
    return next((k for k, pattern in ROWS.items() if re.match(pattern, label.strip())), None)


def label_month(label: str) -> date | None:
    """'Gobierno (junio 2026)' -> 1 June 2026: when that forecast was published."""
    m = re.search(r"\((\w+)\s+(\d{4})\)", label)
    if m and m[1].lower() in MONTHS:
        return date(int(m[2]), MONTHS[m[1].lower()], 1)
    return None


def _put(rows: Rows, label: str, measure: str, yr: int, value: float | None) -> None:
    key = row_key(label)
    if key and value is not None:
        entry = rows.setdefault(key, {"label": label.strip(), "values": {}})
        entry["values"].setdefault(measure, {})[yr] = value


def parse_html(content: str) -> Rows:
    rows: Rows = {}
    for table in read_tables(content):
        header = next((r for r in table if any(re.match(p, c) for c in r for p in MEASURES.values())), None)
        years = next((r for r in table if sum(year(c) is not None for c in r) >= 2), None)
        if header is None or years is None:
            continue
        columns = {}
        for i, (h, y) in enumerate(zip(header, years)):
            measure = next((m for m, p in MEASURES.items() if re.match(p, h)), None)
            if measure and year(y):
                columns[i] = (measure, year(y))
        for r in table:
            if r and row_key(r[0]):
                for i, (measure, yr) in columns.items():
                    if i < len(r):
                        _put(rows, r[0], measure, yr, number(r[i]))
    return rows


def parse_pdf_text(pages: list[str]) -> Rows:
    """Rows from the text of the PDF's pages: each line is a label then its figures in column order."""
    rows: Rows = {}
    for text in pages:
        lines = [line.strip() for line in text.splitlines()]
        found = [(m[1], [t for t in m[2].split() if not re.fullmatch(r"\[\w+\]", t)])
                 for line in lines if (m := _PDF_ROW.match(line))]
        consensus = next((tokens for label, tokens in found if label.startswith("CONSENSO")), None)
        if consensus is None:
            continue
        layout = next((lay for lay in PDF_LAYOUTS if lay[0] == len(consensus) and lay[1] in text), None)
        years_line = next((line for line in lines if re.fullmatch(r"((19|20)\d\d\s*){4,}", line)), None)
        if layout is None or years_line is None:
            raise ValueError(f"unexpected FUNCAS PDF table ({len(consensus)} figures per row)")
        first, second = (int(y) for y in years_line.split()[:2])
        width, _, positions = layout
        for label, tokens in found:
            if len(tokens) != width:
                raise ValueError(f"FUNCAS PDF row {label!r} has {len(tokens)} figures, expected {width}")
            for measure, pair in positions.items():
                _put(rows, label, measure, first, number(tokens[2 * pair]))
                _put(rows, label, measure, second, number(tokens[2 * pair + 1]))
    return rows


def _pdf_rows(url: str) -> Rows:
    import pdfplumber  # only needed when a post has no HTML tables

    with pdfplumber.open(io.BytesIO(http.get(url).content)) as pdf:
        return parse_pdf_text([page.extract_text() or "" for page in pdf.pages])


def latest_posts() -> list[dict]:
    r = http.get(API, params={"search": "panel de previsiones de la economia espanola", "orderby": "date",
                              "order": "desc", "per_page": 4, "_fields": "date,link,title,content"})
    posts = json.loads(r.content.decode("utf-8-sig"))  # the site prefixes its JSON with a byte-order mark
    return [p for p in posts if re.match(r"Panel de previsiones de la econom", p["title"]["rendered"])]


def read_panel(post: dict) -> Rows:
    rows = parse_html(post["content"]["rendered"])
    if "consensus" not in rows:
        link = _PDF_LINK.search(post["content"]["rendered"])
        if not link:
            raise ValueError(f"FUNCAS panel post has neither tables nor a PDF: {post['link']}")
        rows = _pdf_rows(link.group(1))
    if "consensus" not in rows:
        raise ValueError(f"no consensus row in the FUNCAS panel: {post['link']}")
    return rows


def _panel() -> dict:
    with _lock:
        if "error" in _cache:
            raise _cache["error"]
        if "rows" not in _cache:
            try:
                posts = latest_posts()
                if not posts:
                    raise ValueError("no FUNCAS panel posts found")
                newest = posts[0]
                _cache.update(rows=read_panel(newest), published=newest["date"][:10], url=newest["link"])
            except Exception as e:
                _cache["error"] = e
                raise
        return _cache


def clear_cache() -> None:
    with _lock:
        _cache.clear()


def fetch(key: str, params: dict | None = None, **_) -> FetchResult:
    row, measure = key.split("/", 1)
    panel = _panel()
    entry = panel["rows"].get(row)
    values = sorted((entry or {}).get("values", {}).get(measure, {}).items())
    if not values:
        raise ValueError(f"the FUNCAS panel of {panel['published']} has no {measure} figure for {row}")
    meta = {"url": panel["url"], "panel": panel["published"], "published": panel["published"]}
    if row in ("government", "airef"):
        month = label_month(entry["label"])
        meta["published"] = month.isoformat() if month else panel["published"]
    return FetchResult(make_series((date(y, 1, 1) for y, _ in values), (v for _, v in values)), meta)
