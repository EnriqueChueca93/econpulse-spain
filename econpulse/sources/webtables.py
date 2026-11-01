"""Helpers for sources that publish their figures in web pages rather than data feeds.

read_tables() turns every HTML table into rows of cell texts, repeating a cell's text
across the columns it spans, so a header like "PIB" over two year columns labels both.
number() reads a figure as printed: "2,6", "-2.4", "3,6 [3]" (a footnote mark), and
dashes for "not published".
"""

import re
from html.parser import HTMLParser

_NUMBER = re.compile(r"^[-−–]?\d+(?:[.,]\d+)?$")
_FOOTNOTE = re.compile(r"\s*(\[\w+\]|\(\w\))\s*$")


class _TableReader(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.tables: list[list[list[str]]] = []
        self._open: list[list[list[str]]] = []   # tables being read (they can nest)
        self._row: list[str] | None = None
        self._cell: list[str] | None = None
        self._span = 1

    def handle_starttag(self, tag, attrs):
        if tag == "table":
            self._open.append([])
        elif tag == "tr" and self._open:
            self._row = []
        elif tag in ("td", "th") and self._row is not None:
            self._cell = []
            try:
                self._span = max(1, int(dict(attrs).get("colspan") or 1))
            except ValueError:
                self._span = 1
        elif tag == "br" and self._cell is not None:
            self._cell.append(" ")

    def handle_endtag(self, tag):
        if tag in ("td", "th") and self._cell is not None and self._row is not None:
            text = " ".join("".join(self._cell).split())
            self._row.extend([text] * self._span)
            self._cell = None
        elif tag == "tr" and self._row is not None and self._open:
            self._open[-1].append(self._row)
            self._row = None
        elif tag == "table" and self._open:
            self.tables.append(self._open.pop())

    def handle_data(self, data):
        if self._cell is not None:
            self._cell.append(data)


def read_tables(html: str) -> list[list[list[str]]]:
    reader = _TableReader()
    reader.feed(html)
    reader.close()
    return reader.tables


def number(text: str | None) -> float | None:
    """A printed figure, or None for a blank or a dash ("—", "–", "--")."""
    if text is None:
        return None
    t = _FOOTNOTE.sub("", text.strip()).replace("\xa0", "").replace(" ", "")
    if not _NUMBER.match(t):
        return None
    return float(t.replace("−", "-").replace("–", "-").replace(",", "."))


def year(text: str) -> int | None:
    t = text.strip()
    return int(t) if re.fullmatch(r"(19|20)\d\d", t) else None
