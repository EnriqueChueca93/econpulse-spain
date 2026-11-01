"""Section-page tables in the econvitals style.

One row per indicator and a few columns comparing horizons (1, 3 and 12 months),
points in time (latest, a month ago, a year ago) or market moves (1 day, 1 week,
year to date). Values are computed and formatted here; the template only lays the
strings out. A cell that can't be computed (too little history, or a horizon the
series isn't published at) shows a dash.

Each row says how to treat seasonality (`season`):
    adjusted   published seasonally adjusted: every horizon uses the series as it is
    published  unadjusted, but short-term changes shown as the source reports them
               (house prices q/q, as INE does)
    ours       published unadjusted: horizons under 12 months use EconPulse's adjustment
    raw        published unadjusted and left so: only 12-month horizons are shown

A Panel is the other way round: one row per country or region, one column per
measure (inflation, unemployment…), each column dated by its own latest period.
"""

from dataclasses import dataclass, field

import pandas as pd

from . import seasonal, transforms
from .registry import Indicator
from .snapshot import MINUS, fmt_change, fmt_value, period_label
from .store import Store

DASH = "–"
PERIOD_MONTHS = {"M": 1, "Q": 3}
SEASONS = ("adjusted", "published", "ours", "raw")


# ---------------------------------------------------------------- definitions

@dataclass(frozen=True)
class Change:
    """% change over `months`, annualised if `annualise` (for horizons under a year)."""
    header: str
    months: int
    annualise: bool = False


@dataclass(frozen=True)
class Level:
    """The row's value at a point: "latest", "prev" (a period earlier), "year" (a year
    earlier) or "yearend" (the last value of the previous year).

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
class Move:
    """Market move since `ref`: "day" (previous close), "week", "month", "ytd" or "year".

    Rates move in basis points, prices in % (the indicator's change_unit decides).
    """
    header: str
    ref: str


@dataclass(frozen=True)
class Spread:
    """The row's latest value minus its `vs` series on the same date, in basis points."""
    header: str


@dataclass(frozen=True)
class YearToDate:
    """Total of a monthly flow since January, or with `change` its % change on the same months a year earlier."""
    header: str
    change: bool = False


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
    vs: str | None = None             # what a Spread column compares against
    flow: bool = True                 # a flow that can be summed (YearToDate); False for averages
    label_es: str | None = None
    sa: str | None = None             # a published seasonally adjusted twin, for horizons under 12 months


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
                ids.update(([row.id] if row.id else []) + list(row.contrib.values()) + ([row.vs] if row.vs else []))
        return ids


# ---------------------------------------------------------------- computation

class Data:
    """Stored series for one build, cached raw and seasonally adjusted."""

    def __init__(self, indicators: list[Indicator], store: Store):
        self.by_id = {i.id: i for i in indicators}
        self.store = store
        self._raw: dict[str, pd.Series | None] = {}
        self._sa: dict[str, pd.Series | None] = {}
        self.cache: dict = {}  # results shared by several blocks (econpulse/analytics.py)

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


def _year_end(s: pd.Series, date: pd.Timestamp) -> float | None:
    """The last value before 1 January of `date`'s year."""
    before = s[s.index < pd.Timestamp(date.year, 1, 1)]
    return None if before.empty else float(before.iloc[-1])


def _move_ref(s: pd.Series, freq: str, ref: str) -> float | None:
    date = s.index[-1]
    if ref == "day":
        return float(s.iloc[-2]) if freq == "D" and len(s) > 1 else None
    if ref == "week":
        if freq != "D":
            return None
        v = s.asof(date - pd.Timedelta(days=7))
        return None if pd.isna(v) else float(v)
    if ref == "month":
        return _back(s, date, freq, 1) if freq in ("D", "M") else None
    if ref == "ytd":
        return _year_end(s, date)
    if ref == "year":
        return _back(s, date, freq, 12)
    raise ValueError(f"Unknown move {ref!r}")


def fmt_move(ind: Indicator, value: float, ref: float | None) -> str:
    """A change in the indicator's own convention: bp for rates, % for prices."""
    if ref is None or pd.isna(ref):
        return DASH
    pct_unit = ind.unit in ("%", "% of GDP")
    change_unit = ind.change_unit or ("pp" if pct_unit else ind.unit)
    if change_unit == "%":
        return DASH if ref == 0 else fmt_change((value / ref - 1) * 100, "%", 1)
    if change_unit == "bp":
        return fmt_change((value - ref) * (100 if pct_unit else 1), "bp", 0)
    return fmt_change(value - ref, change_unit, ind.decimals)


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
            if isinstance(col, Move):
                return self.move(col)
            if isinstance(col, Spread):
                return self.spread()
            if isinstance(col, YearToDate):
                return self.year_to_date(col)
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
        elif col.at == "yearend":
            v = _year_end(s, date)
        else:
            v = _back(s, date, self.ind.freq, 12)
        return DASH if v is None else fmt_value(v, unit, decimals)

    def avg_change(self, col: AvgChange) -> float | None:
        s, ind, row = self.series, self.ind, self.row
        if s is None or ind.freq != "M":
            return None
        if col.months < 12:
            if row.sa:
                s = self.data.raw(row.sa)
            elif row.season == "raw":
                return None
            elif row.season == "ours":
                s = self.data.adjusted(row.id)
            if s is None or self.date not in s.index:
                return None
        base = _back(s, self.date, ind.freq, col.months)
        return None if base is None else (float(s.loc[self.date]) - base) / col.months

    def move(self, col: Move) -> str:
        s = self.series
        if s is None:
            return DASH
        return fmt_move(self.ind, float(s.iloc[-1]), _move_ref(s, self.ind.freq, col.ref))

    def year_to_date(self, col: YearToDate) -> str:
        s, ind = self.series, self.ind
        if s is None or ind.freq != "M" or not self.row.flow or ind.unit in ("%", "% of GDP"):
            return DASH
        d = self.date
        this = s[(s.index >= pd.Timestamp(d.year, 1, 1)) & (s.index <= d)]
        if len(this) != d.month:
            return DASH
        if not col.change:
            return fmt_value(float(this.sum()), ind.unit, ind.decimals)
        before = s[(s.index >= pd.Timestamp(d.year - 1, 1, 1)) & (s.index <= d - pd.DateOffset(years=1))]
        if len(before) != d.month or before.sum() == 0:
            return DASH
        return _fmt_num((float(this.sum()) / float(before.sum()) - 1) * 100)

    def spread(self) -> str:
        other = self.data.raw(self.row.vs) if self.row.vs else None
        if self.series is None or other is None:
            return DASH
        other = other.dropna()
        v = other.asof(self.date) if self.data.by_id[self.row.vs].freq == "D" else other.get(self.date)
        if v is None or pd.isna(v):
            return DASH
        return fmt_change((float(self.series.iloc[-1]) - float(v)) * 100, "bp", 0)

    def contribution(self, col: Contribution) -> float | None:
        cid = self.row.contrib.get(col.key)
        s = self.data.raw(cid) if cid else None
        if s is None or self.date is None:
            return None
        v = s.get(self.date)
        return None if v is None or pd.isna(v) else float(v)


def _level_header(col: Level, freqs: set[str], through: pd.Timestamp) -> str:
    if col.header:
        return col.header
    if col.at == "latest":
        return "Latest"
    if col.at == "year":
        return "1-yr ago"
    if col.at == "yearend":
        return f"End-{through.year - 1}"
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
    headers = [_level_header(col, freqs, through) if isinstance(col, Level) else col.header for col in table.columns]
    through_label = period_label(through, main_freq)
    return {
        "title": table.title,
        "caption": f"{table.caption} · through {through_label}",
        "through": through_label,
        "columns": headers,
        "rows": rows,
        "note": table.note,
    }


# ---------------------------------------------------------------- panels (countries, regions)

@dataclass(frozen=True)
class PanelColumn:
    """One measure across every row: `key` picks the row's indicator, `col` says how to show it."""
    key: str
    header: str
    col: object = Level("latest")
    transform: str = "level"


@dataclass
class PanelRow:
    label: str
    ids: dict                         # column key -> indicator id, or (indicator id, transform)
    highlight: bool = False           # e.g. Spain among its peers
    indent: int = 0


@dataclass
class Panel:
    title: str
    caption: str
    columns: list
    rows: list                        # PanelRow, or Heading to start a group of rows
    note: str = ""

    def indicator_ids(self) -> set[str]:
        return {(v[0] if isinstance(v, tuple) else v) for row in self.rows if isinstance(row, PanelRow)
                for v in row.ids.values()}


def build_panel(panel: Panel, data: Data) -> dict | None:
    """The panel as display strings. Each column is labelled with the period most of its
    rows share; a cell from another period carries its own."""
    grid = []
    for row in panel.rows:
        cells = []
        if isinstance(row, Heading):
            grid.append(cells)
            continue
        for col in panel.columns:
            ref = row.ids.get(col.key)
            if ref is None:
                cells.append(None)
                continue
            ind_id, transform = ref if isinstance(ref, tuple) else (ref, col.transform)
            cells.append(_RowCalc(Row(ind_id, transform=transform), data))
        grid.append(cells)
    if not any(c is not None and c.date is not None for cells in grid for c in cells):
        return None

    periods = []
    for j in range(len(panel.columns)):
        dated = [cells[j] for cells in grid if cells and cells[j] is not None and cells[j].date is not None]
        if not dated:
            periods.append(None)
            continue
        counts = pd.Series([c.date for c in dated]).value_counts()
        common = max(counts[counts == counts.max()].index)
        periods.append((common, next(c.freq for c in dated if c.date == common)))

    rows = []
    for row, cells in zip(panel.rows, grid):
        if isinstance(row, Heading):
            rows.append({"heading": True, "label": row.label, "label_es": "", "indent": 0, "period_note": "",
                         "url": None, "cells": [], "highlight": False})
            continue
        out = []
        for col, calc, period in zip(panel.columns, cells, periods):
            if calc is None or calc.date is None:
                out.append(DASH)
                continue
            value = calc.value(col.col)
            if period and (calc.date, calc.freq) != period and value != DASH:
                out.append({"value": value, "note": period_label(calc.date, calc.freq)})
            else:
                out.append(value)
        rows.append({"heading": False, "label": row.label, "label_es": "", "indent": row.indent, "period_note": "",
                     "url": None, "cells": out, "highlight": row.highlight})
    return {
        "title": panel.title,
        "caption": panel.caption,
        "through": None,
        "columns": [col.header for col in panel.columns],
        "column_notes": [period_label(*p) if p else "" for p in periods],
        "rows": rows,
        "note": panel.note,
    }
