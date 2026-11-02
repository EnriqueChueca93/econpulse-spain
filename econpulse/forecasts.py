"""What forecasters expect for Spain this year and next, shown on the Analysis page.

Every forecaster is read automatically, as indicators (fc_* in indicators.yaml):
    data services  the IMF, the OECD and the European Commission (AMECO, via DBnomics)
    web pages      the Banco de España (its report's projections table) and the FUNCAS Panel
                   (its tables or PDF), whose reference table also gives the government's and
                   AIReF's latest forecasts
forecasts.yaml can override any of them by hand with a newer edition.

Figures read automatically need an AI check before they count: each edition has a
fingerprint (its date and figures), and until `python -m econpulse confirm <id>` records
that fingerprint in data/forecast_checks.json, after an AI has compared the figures with the
publisher's own document, its row is marked "awaiting AI check" and left out of the
average, the facts and the chart. A new edition, or a revision, needs a new check.

Next to the forecasters, Macroscope's own figure for this year's GDP: the quarters INE has
published plus the nowcast for the quarter still to come.
"""

import hashlib
import json
import re
from dataclasses import dataclass, field
from datetime import date, datetime

import pandas as pd
import yaml

from . import analytics, i18n, transforms
from .charts import localise
from .config import FORECASTS_FILE
from .i18n import _
from .snapshot import fmt_value, period_label
from .sources.base import MADRID, madrid_today
from .tables import DASH, Data

MEASURES = [("gdp", "GDP growth", "real, %"), ("inflation", "Inflation", "annual avg., %"),
            ("unemployment", "Unemployment", "% of labour force"), ("balance", "Budget balance", "% of GDP")]
MEASURE_IDS = [m for m, *_rest in MEASURES]
GROUPS = [("spain", "In Spain"), ("international", "International organisations")]
EC_FORECAST_PAGE = "https://economy-finance.ec.europa.eu/economic-forecast-and-surveys/economic-forecasts_en"
CHECKS = "forecast_checks"   # data/forecast_checks.json
# Status of a row: read automatically and AI-checked, read automatically and not yet checked, or entered by hand.
CHECKED, PENDING, HAND = "checked", "awaiting AI check", "entered by hand"


@dataclass
class Forecaster:
    id: str
    name: str
    short: str
    group: str
    url: str | None
    published: date | None
    inflation: str = "CPI"          # what the inflation figure measures: HICP or CPI
    note: str = ""
    via: str = ""                   # where the figures were read, if not from the forecaster itself
    values: dict[int, dict[str, float]] = field(default_factory=dict)
    low: dict[int, dict[str, float]] = field(default_factory=dict)    # a panel's lowest and highest forecasts
    high: dict[int, dict[str, float]] = field(default_factory=dict)
    status: str = HAND
    check: dict | None = None       # the AI check that confirmed these figures

    def value(self, year: int, measure: str) -> float | None:
        return self.values.get(year, {}).get(measure)

    @property
    def counts(self) -> bool:
        """Whether the figures go into the average, the facts and the chart."""
        return self.status != PENDING


def _measures(fmt: str, only=MEASURE_IDS) -> dict[str, str]:
    return {m: fmt.format(m=m) for m in only}


# Read automatically: measure -> indicator, or (indicator, transform giving the forecast figure).
AUTOMATIC = [
    {"id": "bde", "name": "Banco de España", "short": "BdE", "group": "spain", "inflation": "HICP",
     "series": _measures("fc_bde_{m}")},
    {"id": "funcas", "name": "FUNCAS Panel (consensus)", "short": "FUNCAS", "group": "spain", "inflation": "CPI",
     "series": _measures("fc_funcas_{m}"), "low": _measures("fc_funcas_{m}_min"), "high": _measures("fc_funcas_{m}_max"),
     "note": "The FUNCAS Panel is the average of about 19 forecasters (banks, research institutes, consultancies)."},
    {"id": "airef", "name": "AIReF", "short": "AIReF", "group": "spain", "inflation": "CPI", "via": "FUNCAS Panel",
     "series": _measures("fc_airef_{m}")},
    {"id": "government", "name": "Government", "short": "Government", "group": "spain", "inflation": "CPI",
     "via": "FUNCAS Panel", "series": _measures("fc_gov_{m}", ("gdp", "unemployment", "balance"))},
    {"id": "imf", "name": "IMF World Economic Outlook", "short": "IMF", "group": "international", "inflation": "HICP",
     "series": _measures("fc_imf_{m}")},
    {"id": "oecd", "name": "OECD Economic Outlook", "short": "OECD", "group": "international", "inflation": "HICP",
     "series": _measures("fc_oecd_{m}")},
    {"id": "ec", "name": "European Commission", "short": "Commission", "group": "international", "inflation": "HICP",
     "url": EC_FORECAST_PAGE,
     "series": {"gdp": ("fc_ec_gdp_volume", "yoy"), "inflation": ("fc_ec_hicp_index", "yoy"),
                "unemployment": "fc_ec_unemployment", "balance": "fc_ec_balance"}},
]
INDICATORS = [s if isinstance(s, str) else s[0]
              for spec in AUTOMATIC for part in ("series", "low", "high") for s in spec.get(part, {}).values()]


def eo_month(edition: str) -> date | None:
    """When an OECD Economic Outlook came out: No. 119 in June 2026, then every six months."""
    m = re.search(r"(\d+)\s*$", edition or "")
    if not m:
        return None
    steps = int(m[1]) - 119
    return date(2026 + steps // 2, 6 if steps % 2 == 0 else 12, 1)


def _edition_date(entry: dict) -> date | None:
    """When the edition behind a fetched series was published, from what its source recorded."""
    for key in ("published", "source_updated"):
        if entry.get(key):
            return date.fromisoformat(entry[key][:10])
    return eo_month(entry.get("edition", "")) if entry.get("edition") else None


def load_manual(path=None) -> list[Forecaster]:
    raw = yaml.safe_load((path or FORECASTS_FILE).read_text(encoding="utf-8")) or {}
    out = []
    for f in raw.get("forecasters") or []:
        values = {int(y): {k: float(v) for k, v in (vals or {}).items() if v is not None}
                  for y, vals in (f.get("values") or {}).items()}
        out.append(Forecaster(id=f["id"], name=f["name"], short=f.get("short", f["name"]), group=f["group"],
                              url=f.get("url"), published=f.get("published"), inflation=f.get("inflation", "CPI"),
                              note=f.get("note", ""), values=values, status=HAND))
    return out


def _read(data: Data, parts: dict) -> tuple[dict[int, dict[str, float]], dict]:
    """Figures by year and measure from fetched series, and the catalog entry of the first one."""
    catalog = data.store.load_catalog()
    values: dict[int, dict[str, float]] = {}
    entry = None
    for measure, spec in parts.items():
        ind_id, transform = (spec, "level") if isinstance(spec, str) else spec
        raw = data.store.load_series(ind_id)
        if raw is None or ind_id not in data.by_id:
            continue
        entry = entry or catalog.get(ind_id, {})
        for d, v in transforms.apply(transform, raw, "A").dropna().items():
            values.setdefault(d.year, {})[measure] = round(float(v), 4)
    return values, entry or {}


def _automatic(data: Data) -> list[Forecaster]:
    out = []
    for spec in AUTOMATIC:
        values, entry = _read(data, spec["series"])
        if not values:
            continue
        published = _edition_date(entry)
        f = Forecaster(id=spec["id"], name=spec["name"], short=spec["short"], group=spec["group"],
                       url=entry.get("url") or spec.get("url") or data.by_id[_first(spec)].source_url(),
                       published=published, inflation=spec["inflation"], note=spec.get("note", ""),
                       via=spec.get("via", ""), values=values, status=PENDING)
        if "low" in spec:
            low, low_entry = _read(data, spec["low"])
            high, high_entry = _read(data, spec["high"])
            # Only a range from the same edition as the consensus.
            if _edition_date(low_entry) == published == _edition_date(high_entry):
                f.low, f.high = low, high
        out.append(f)
    return out


def _first(spec: dict) -> str:
    s = next(iter(spec["series"].values()))
    return s if isinstance(s, str) else s[0]


def _month_key(d: date | None) -> tuple[int, int]:
    return (d.year, d.month) if d else (0, 0)


def fingerprint(f: Forecaster) -> str:
    """Identifies an edition's figures: its date and every forecast from its own year on."""
    start = f.published.year if f.published else madrid_today().year

    def part(table):
        return {str(y): {m: round(v, 1) for m, v in sorted(ms.items())} for y, ms in sorted(table.items()) if y >= start}

    payload = {"id": f.id, "published": str(f.published), "values": part(f.values), "low": part(f.low),
               "high": part(f.high)}
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()[:12]


def _apply_checks(fs: list[Forecaster], checks: dict) -> None:
    for f in fs:
        record = checks.get(f.id)
        if f.status == PENDING and record and record.get("fingerprint") == fingerprint(f):
            f.status, f.check = CHECKED, record
            if record.get("note"):
                f.note = " ".join(n for n in (f.note, record["note"]) if n)


def forecasters(data: Data) -> list[Forecaster]:
    """Every forecaster: the automatic ones, unless forecasts.yaml has a newer edition by hand."""
    def compute():
        auto = _automatic(data)
        _apply_checks(auto, data.store.load_json(CHECKS, {}))
        by_id = {f.id: f for f in auto}
        for hand in load_manual():
            current = by_id.get(hand.id)
            if current is None or _month_key(hand.published) > _month_key(current.published):
                by_id[hand.id] = hand
        return list(by_id.values())

    return analytics._cached(data, "forecasters", compute)


def pending(data: Data) -> list[Forecaster]:
    return [f for f in forecasters(data) if f.status == PENDING]


def confirm(data: Data, forecaster_id: str, by: str, note: str = "", against: str = "") -> dict:
    """Record that an AI checked this forecaster's current figures against the publisher's document.

    ``against`` says what they were compared with (kept in the record); ``note`` is shown under the table."""
    f = next((f for f in forecasters(data) if f.id == forecaster_id), None)
    if f is None:
        raise ValueError(f"no forecaster {forecaster_id!r}; choose from {', '.join(x.id for x in forecasters(data))}")
    if f.status == HAND:
        raise ValueError(f"{forecaster_id} is entered by hand in forecasts.yaml; there is nothing to confirm")
    checks = data.store.load_json(CHECKS, {})
    record = {"fingerprint": fingerprint(f), "published": str(f.published), "checked_by": by,
              "checked_at": datetime.now(MADRID).strftime("%Y-%m-%d %H:%M"),
              "values": {str(y): f.values[y] for y in sorted(f.values) if y >= (f.published.year if f.published else 0)}}
    if against:
        record["checked_against"] = against
    if note:
        record["note"] = note
    checks[forecaster_id] = record
    data.store.save_json(CHECKS, dict(sorted(checks.items())))
    data.cache.pop("forecasters", None)
    return record


def years(today: date | None = None) -> tuple[int, int]:
    this = (today or madrid_today()).year
    return this, this + 1


def gdp_this_year(data: Data, year: int) -> dict | None:
    """Annual GDP growth for ``year`` from the quarters INE has published plus the nowcast for the
    fourth, and the growth if the fourth quarter were flat (what the year has already 'banked')."""
    raw = data.store.load_series("gdp")
    n = analytics.nowcast(data)
    if raw is None or n is None:
        return None
    q = transforms.regular(raw.sort_index(), "Q")
    this = q[q.index.year == year].dropna()
    before = q[q.index.year == year - 1].dropna()
    q4 = pd.Timestamp(year, 10, 1)
    if len(before) != 4 or len(this) != 3 or n["quarter"] != q4:
        return None
    last = float(this.iloc[-1])
    with_nowcast = (this.sum() + last * (1 + n["value"] / 100)) / before.sum() * 100 - 100
    flat = (this.sum() + last) / before.sum() * 100 - 100
    return {"value": float(with_nowcast), "flat": float(flat), "nowcast": n["value"], "through": this.index[-1]}


def _month(d: date | None) -> str:
    return i18n.month_year(d) if d else ""


def _cell(v: float | None) -> str:
    return DASH if v is None else fmt_value(v, "%", 1)


def _range_cell(f: Forecaster, year: int, measure: str) -> str:
    lo, hi = f.low.get(year, {}).get(measure), f.high.get(year, {}).get(measure)
    if lo is None or hi is None:
        return DASH
    return _("{low} to {high}").format(low=fmt_value(lo, '%', 1), high=fmt_value(hi, '%', 1))


def _average(fs: list[Forecaster], year: int, measure: str) -> tuple[float | None, list[float]]:
    vals = [v for f in fs if f.counts and (v := f.value(year, measure)) is not None]
    return (sum(vals) / len(vals) if vals else None), vals


def _ordered(fs: list[Forecaster], year: int) -> list[tuple[str, list[Forecaster]]]:
    """Forecasters with figures for ``year``, by group, newest edition first."""
    out = []
    for group, title in GROUPS:
        members = [f for f in fs if f.group == group and f.values.get(year)]
        members.sort(key=lambda f: f.published or date.min, reverse=True)
        if members:
            out.append((title, members))
    return out


def _row_note(f: Forecaster) -> str:
    parts = [_month(f.published)]
    if f.via:
        parts.append(_("via {source}").format(source=_(f.via)))
    return " · ".join(p for p in parts if p)


def _note(f: Forecaster) -> str:
    """A forecaster's note under the table in the language being written: its own note, then its AI check's
    (_apply_checks joins the two)."""
    extra = (f.check or {}).get("note", "")
    if extra and f.note.endswith(extra):
        parts = [f.note[:len(f.note) - len(extra)].rstrip(), extra]
    else:
        parts = [f.note]
    return " ".join(_(p) for p in parts if p)


def forecast_table(data: Data, year: int) -> dict | None:
    fs = forecasters(data)
    groups = _ordered(fs, year)
    if not groups:
        return None
    rows = []
    shown = []
    for title, members in groups:
        rows.append({"heading": True, "label": _(title)})
        for f in members:
            shown.append(f)
            rows.append({"heading": False, "label": _(f.name), "label_es": "", "indent": 0,
                         "period_note": _row_note(f), "url": f.url, "flag": _(PENDING) if f.status == PENDING else "",
                         "cells": [_cell(f.value(year, m)) for m in MEASURE_IDS]})
            if f.low.get(year) and f.high.get(year):
                rows.append({"heading": False, "label": _("Range of the panel"), "label_es": "", "indent": 1,
                             "period_note": _("lowest to highest"), "url": None,
                             "cells": [_range_cell(f, year, m) for m in MEASURE_IDS]})
    rows.append({"heading": True, "label": _("Summary")})
    rows.append({"heading": False, "label": _("Average of the forecasts above"), "label_es": "", "indent": 0,
                 "period_note": _("AI-checked rows only") if any(not f.counts for f in shown) else "", "url": None,
                 "highlight": True, "cells": [_cell(_average(shown, year, m)[0]) for m in MEASURE_IDS]})
    own = gdp_this_year(data, year)
    if own is not None:
        rows.append({"heading": False, "label": _("Macroscope: INE's quarters + nowcast"), "label_es": "", "indent": 0,
                     "period_note": _("Q4 {growth}").format(growth=_fmt_growth(own['nowcast'])), "url": None,
                     "cells": [_cell(own["value"]), DASH, DASH, DASH]})
    # Short names are the chart's; proper names stay as they are when the catalogue has no other form.
    hicp = [i18n.maybe(f.short) for f in shown if f.inflation == "HICP" and f.value(year, "inflation") is not None]
    cpi = [i18n.maybe(f.short) for f in shown if f.inflation != "HICP" and f.value(year, "inflation") is not None]
    if hicp and cpi:
        measures = _("Inflation is the HICP for {hicp} and the CPI for {cpi}.").format(hicp=_join(hicp), cpi=_join(cpi))
    elif hicp:
        measures = _("Inflation is the HICP for {names}.").format(names=_join(hicp))
    elif cpi:
        measures = _("Inflation is the CPI for {names}.").format(names=_join(cpi))
    else:
        measures = ""
    checking = _("Figures are read automatically from each publisher's data service, web page or PDF, and count in "
                 "the average and the chart only after an AI check against the publisher's own document.")
    if any(f.status == PENDING for f in shown):
        checking += " " + _("Rows marked “awaiting AI check” are newly read and not yet checked.")
    via = [i18n.maybe(f.short) for f in shown if f.via]
    notes = [measures,
             _("A budget balance below zero is a deficit."),
             checking,
             _("{names} figures are taken from the FUNCAS Panel's reference table, which lists each with the "
               "month it was published.").format(names=_join(via)) if via else "",
             *dict.fromkeys(_note(f) for f in shown if f.note)]
    return {"title": _("Forecaster"), "caption": _("Forecasts for {year}").format(year=year), "through": None,
            "columns": [_(label) for _m, label, _n in MEASURES], "column_notes": [_(note) for *_rest, note in MEASURES],
            "rows": rows, "note": " ".join(n for n in notes if n)}


def _fmt_growth(v: float) -> str:
    return analytics._fmt_signed(v, 1, "%")


def _join(names: list[str]) -> str:
    if len(names) == 1:
        return names[0]
    return _("{names} and {last}").format(names=", ".join(names[:-1]), last=names[-1])


def forecast_facts(data: Data, today: date | None = None) -> list[dict]:
    this, nxt = years(today)
    fs = forecasters(data)
    facts = []
    for year in (this, nxt):
        avg, vals = _average(fs, year, "gdp")
        if avg is not None:
            facts.append({"label": _("GDP growth forecast, {year}").format(year=year), "value": fmt_value(avg, "%", 1),
                          "sub": _spread(vals)})
    own = gdp_this_year(data, this)
    if own is not None:
        facts.append({"label": _("Macroscope, {year} GDP").format(year=this), "value": fmt_value(own["value"], "%", 1),
                      "sub": _("INE to {quarter}, then the Q4 nowcast").format(quarter=period_label(own['through'], 'Q'))})
    avg, vals = _average(fs, this, "inflation")
    if avg is not None:
        facts.append({"label": _("Inflation forecast, {year}").format(year=this), "value": fmt_value(avg, "%", 1),
                      "sub": _spread(vals)})
    return facts


def _spread(vals: list[float]) -> str:
    return _("average of {n}; range {low} to {high}").format(
        n=len(vals), low=fmt_value(min(vals), '%', 1), high=fmt_value(max(vals), '%', 1))


def forecast_callout(data: Data, today: date | None = None) -> str | None:
    this, _nxt = years(today)
    own = gdp_this_year(data, this)
    if own is None:
        return None
    return _("With three quarters published, {year} is largely decided: even with no growth at all in the fourth "
             "quarter, GDP would grow {flat} on {previous}. The forecasts differ mainly in what they expect for "
             "{following}.").format(year=this, flat=fmt_value(own['flat'], '%', 1), previous=this - 1, following=this + 1)


def forecast_chart(data: Data, today: date | None = None) -> dict | None:
    this, nxt = years(today)
    fs = [f for _title, members in _ordered(forecasters(data), this) for f in members if f.counts]
    if len(fs) < 2:
        return None
    labels = [f.short for f in fs] + ["Average"]
    series = []
    for year in (this, nxt):
        ys = [f.value(year, "gdp") for f in fs] + [_average(fs, year, "gdp")[0]]
        # The years are named after the spec is put into the language being written: they are not text.
        series.append({"name": "", "x": labels, "y": [None if v is None else round(v, 2) for v in ys]})
    own = gdp_this_year(data, this)
    if own is not None:
        for s in series:
            s["x"] = s["x"] + ["Macroscope"]
        series[0]["y"].append(round(own["value"], 2))
        series[1]["y"].append(None)
    spec = localise({"id": "forecasts", "title": "GDP growth forecasts", "subtitle": "",
                     "kind": "bar", "x_kind": "category", "x_title": "Forecaster", "unit": "%", "decimals": 1,
                     "freq": None, "series": series, "ref_lines": [],
                     "source": _("Forecasters' publications (see table), AI-checked; Macroscope nowcast")})
    for s, year in zip(spec["series"], (this, nxt)):
        s["name"] = str(year)
    spec["subtitle"] = _("Real GDP, % change on a year earlier, {year} and {following}").format(year=this, following=nxt)
    return spec
