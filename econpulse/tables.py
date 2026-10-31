"""Section-page tables in the econvitals style.

One row per indicator and a few columns comparing horizons (1, 3 and 12 months) or
points in time (latest, a month ago, a year ago). Values are computed and formatted
here; the template only lays the strings out. A cell that can't be computed (too
little history, or a horizon the series isn't published at) shows a dash.

Each row says how to treat seasonality (`season`):
    adjusted  published seasonally adjusted: every horizon uses the series as it is
    ours      published unadjusted: horizons under 12 months use EconPulse's adjustment
    raw       published unadjusted and left so: only 12-month horizons are shown
"""

from dataclasses import dataclass, field

import pandas as pd

from . import seasonal, transforms
from .registry import Indicator
from .snapshot import MINUS, fmt_value, period_label
from .store import Store

DASH = "–"
PERIOD_MONTHS = {"M": 1, "Q": 3}
SEASONS = ("adjusted", "ours", "raw")


# ---------------------------------------------------------------- definitions

@dataclass(frozen=True)
class Change:
    """% change over `months`, annualised if `annualise` (for horizons under a year)."""
    header: str
    months: int
    annualise: bool = False


@dataclass(frozen=True)
class Level:
    """The row's value at a point: "latest", "prev" (a period earlier) or "year" (a year earlier).

    With no header, one is chosen from the rows' frequency ("1-mo ago", "1-qtr ago").
    """
    at: str
    header: str | None = None


@dataclass(frozen=True)
class AvgChange:
    """Average change per month over the last `months` months, in the series' own units."""
    header: str
    months: int


@dataclass(frozen=True)
class Contribution:
    """Contribution to GDP growth, read from the row's `contrib` series ("q" or "y")."""
    header: str
    key: str


@dataclass
class Row:
    id: str | None
    label: str | None = None          # defaults to the indicator's label
    indent: int = 0
    season: str = "adjusted"
    transform: str = "level"          # what Level and AvgChange columns read, e.g. "yoy"
    is_rate: bool = False             # the series already is a % change on a year earlier
    contrib: dict = field(default_factory=dict)   # {"q": indicator id, "y": indicator id}
    label_es: str | None = None


@dataclass
class Heading:
    label: str


@dataclass
class Table:
    title: str                        # also the header of the label column
    caption: str                      # units; " · through <period>" is appended
    columns: list
    rows: list
    note: str = ""

    def indicator_ids(self) -> set[str]:
        ids = set()
        for row in self.rows:
            if isinstance(row, Row):
                ids.update(([row.id] if row.id else []) + list(row.contrib.values()))
        return ids


# ---------------------------------------------------------------- computation

class Data:
    """Stored series for one build, cached raw and seasonally adjusted."""

    def __init__(self, indicators: list[Indicator], store: Store):
        self.by_id = {i.id: i for i in indicators}
        self.store = store
        self._raw: dict[str, pd.Series | None] = {}
        self._sa: dict[str, pd.Series | None] = {}

    def raw(self, ind_id: str) -> pd.Series | None:
        if ind_id not in self._raw:
            s = self.store.load_series(ind_id)
            self._raw[ind_id] = None if s is None or s.empty else transforms.regular(s.sort_index(), self.by_id[ind_id].freq)
        return self._raw[ind_id]

    def adjusted(self, ind_id: str) -> pd.Series | None:
        if ind_id not in self._sa:
            raw = self.raw(ind_id)
            try:
                self._sa[ind_id] = None if raw is None else seasonal.adjust(raw.dropna(), self.by_id[ind_id].freq)
            except ValueError:
                self._sa[ind_id] = None
        return self._sa[ind_id]


def _fmt_num(v: float | None, decimals: int = 1) -> str:
    if v is None or pd.isna(v):
        return DASH
    text = f"{abs(v):,.{decimals}f}"
    return MINUS + text if v < 0 and float(text.replace(",", "")) != 0 else text


def _back(s: pd.Series, date: pd.Timestamp, freq: str, months: int) -> float | None:
    """The value `months` before `date`: same calendar slot for M/Q, last available for daily."""
    target = date - pd.DateOffset(months=months)
    v = s.asof(target) if freq == "D" else s.get(target)
    return None if v is None or pd.isna(v) else float(v)


class _RowCalc:
    def __init__(self, row: Row, data: Data):
        self.row, self.data = row, data
        self.ind = data.by_id.get(row.id) if row.id else None
        self.series = data.raw(row.id) if row.id else None
        if self.series is not None:
            self.series = self.series.dropna()
            if self.series.empty:
                self.series = None
        # A row with no series of its own (e.g. net exports) is dated by its contributions.
        anchor = self.series
        if anchor is None:
            for cid in row.contrib.values():
                anchor = data.raw(cid)
                if anchor is not None:
                    anchor = anchor.dropna()
                    self.anchor_freq = data.by_id[cid].freq
                    break
        else:
            self.anchor_freq = self.ind.freq
        self.date = anchor.index[-1] if anchor is not None and not anchor.empty else None

    @property
    def freq(self) -> str | None:
        return getattr(self, "anchor_freq", None)

    def value(self, col) -> str:
        try:
            if isinstance(col, Change):
                # A published rate keeps its own precision (e.g. agreed pay rises, 3.05%).
                return _fmt_num(self.change(col), self.ind.decimals if self.row.is_rate else 1)
            if isinstance(col, Level):
                return self.level(col)
            if isinstance(col, AvgChange):
                return _fmt_num(self.avg_change(col))
            if isinstance(col, Contribution):
                return _fmt_num(self.contribution(col))
        except (ValueError, KeyError, IndexError):
            return DASH
        raise TypeError(f"Unknown column type {col!r}")

    def change(self, col: Change) -> float | None:
        s, ind, row = self.series, self.ind, self.row
        if s is None or ind.freq not in PERIOD_MONTHS:
            return None
        if row.is_rate:
            return float(s.iloc[-1]) if col.months == 12 else None
        if col.months % PERIOD_MONTHS[ind.freq]:
            return None
        if col.months < 12:
            if row.season == "raw":
                return None
            if row.season == "ours":
                s = self.data.adjusted(row.id)
                if s is None:
                    return None
        latest = float(s.loc[self.date])
        base = _back(s, self.date, ind.freq, col.months)
        if base is None or base == 0:
            return None
        ratio = latest / base
        if col.annualise and col.months < 12:
            return (ratio ** (12 / col.months) - 1) * 100
        return (ratio - 1) * 100

    def _transformed(self) -> tuple[pd.Series, str, int]:
        ind, row = self.ind, self.row
        if row.transform == "level":
            return self.series, ind.unit, ind.decimals
        s = transforms.apply(row.transform, self.series, ind.freq)
        pct = row.transform in transforms.PERCENT_TRANSFORMS
        return s, ("%" if pct else ind.unit), (1 if pct else ind.decimals)

    def level(self, col: Level) -> str:
        if self.series is None:
            return DASH
        s, unit, decimals = self._transformed()
        if s.empty:
            return DASH
        date = s.index[-1]
        if col.at == "latest":
            v = float(s.iloc[-1])
        elif col.at == "prev":
            months = 1 if self.ind.freq == "D" else PERIOD_MONTHS.get(self.ind.freq, 12)
            v = _back(s, date, self.ind.freq, months)
        else:
            v = _back(s, date, self.ind.freq, 12)
        return DASH if v is None else fmt_value(v, unit, decimals)

    def avg_change(self, col: AvgChange) -> float | None:
        s, ind, row = self.series, self.ind, self.row
        if s is None or ind.freq != "M":
            return None
        if col.months < 12:
            if row.season == "raw":
                return None
            if row.season == "ours":
                s = self.data.adjusted(row.id)
                if s is None:
                    return None
        base = _back(s, self.date, ind.freq, col.months)
        return None if base is None else (float(s.loc[self.date]) - base) / col.months

    def contribution(self, col: Contribution) -> float | None:
        cid = self.row.contrib.get(col.key)
        s = self.data.raw(cid) if cid else None
        if s is None or self.date is None:
            return None
        v = s.get(self.date)
        return None if v is None or pd.isna(v) else float(v)


def _level_header(col: Level, freqs: set[str]) -> str:
    if col.header:
        return col.header
    if col.at == "latest":
        return "Latest"
    if col.at == "year":
        return "1-yr ago"
    if freqs == {"Q"}:
        return "1-qtr ago"
    if freqs <= {"M", "D"}:
        return "1-mo ago"
    return "Previous"


def build_table(table: Table, data: Data) -> dict | None:
    """The table as display strings, or None if none of its rows has data."""
    calcs = [(_RowCalc(r, data) if isinstance(r, Row) else r) for r in table.rows]
    dated = [c for c in calcs if isinstance(c, _RowCalc) and c.date is not None]
    if not dated:
        return None
    # The table is "through" the period most of its main-frequency rows share (the latest, on a tie);
    # rows on another frequency or period carry their own period next to the label.
    main_freq = dated[0].freq
    dates = pd.Series([c.date for c in dated if c.freq == main_freq])
    counts = dates.value_counts()
    through = max(counts[counts == counts.max()].index)
    freqs = {c.freq for c in dated}

    rows = []
    for c in calcs:
        if isinstance(c, Heading):
            rows.append({"heading": True, "label": c.label})
            continue
        ind, row = c.ind, c.row
        source = ind or (data.by_id.get(next(iter(row.contrib.values()))) if row.contrib else None)
        note = ""
        if c.date is not None and (c.freq != main_freq or c.date != through):
            note = period_label(c.date, c.freq)
        rows.append({
            "heading": False,
            "label": row.label or (ind.label if ind else ""),
            "label_es": row.label_es or (source.label_es if source else ""),
            "indent": row.indent,
            "period_note": note,
            "url": source.source_url() if source else None,
            "cells": [c.value(col) for col in table.columns],
        })
    headers = [_level_header(col, freqs) if isinstance(col, Level) else col.header for col in table.columns]
    through_label = period_label(through, main_freq)
    return {
        "title": table.title,
        "caption": f"{table.caption} · through {through_label}",
        "through": through_label,
        "columns": headers,
        "rows": rows,
        "note": table.note,
    }
