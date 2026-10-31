"""Turn stored series into the snapshot the site displays: latest values, changes,
display strings and status for every indicator.

Number formatting lives here (not in JavaScript) so the site and the CLI agree.
"""

import math
from datetime import datetime, timezone

import pandas as pd

from . import sources, transforms
from .fetch import is_out_of_date
from .registry import Indicator
from .store import Store

MINUS = "−"  # typographic minus, as on econvitals


def period_label(date: pd.Timestamp, freq: str) -> str:
    if freq == "D":
        return f"{date.day} {date:%b %Y}"
    if freq == "M":
        return f"{date:%b %Y}"
    if freq == "Q":
        return f"Q{(date.month - 1) // 3 + 1} {date.year}"
    return str(date.year)


def _num(v: float, decimals: int, thousands: bool = False) -> str:
    text = f"{abs(v):,.{decimals}f}" if thousands else f"{abs(v):.{decimals}f}"
    # Avoid "-0.0": only show a sign if the rounded number isn't zero.
    if v < 0 and float(text.replace(",", "")) != 0:
        return MINUS + text
    return text


def fmt_value(v: float, unit: str, decimals: int) -> str:
    n = _num(v, decimals, thousands=True)
    sign, digits = (MINUS, n[1:]) if n.startswith(MINUS) else ("", n)
    if unit == "%":
        return f"{_num(v, decimals)}%"
    if unit == "% of GDP":
        return f"{_num(v, decimals)}% of GDP"
    if unit == "bp":
        return f"{_num(v, 0)} bp"
    if unit == "thousands":
        return f"{n}k"
    if unit in ("index", "balance", "rate"):
        return n
    if unit == "$/bbl":
        return f"{sign}${digits}"
    if unit == "€ mn":
        return f"{sign}€{digits} mn"
    if unit == "€":
        return f"{sign}€{digits}"
    return f"{n} {unit}"  # e.g. "224.9 €/MWh", "93,858 vehicles"


def fmt_change(c: float, unit: str, decimals: int) -> str:
    if unit == "bp":
        decimals = 0
    body = fmt_value(c, unit, decimals)
    is_zero = float(_num(abs(c), decimals, thousands=True).replace(",", "")) == 0
    return body if body.startswith(MINUS) or is_zero else "+" + body


def _clean(v) -> float | None:
    return None if v is None or (isinstance(v, float) and math.isnan(v)) else round(float(v), 6)


def summarize_transform(ind: Indicator, series: pd.Series, name: str) -> dict | None:
    ts = transforms.apply(name, series, ind.freq)
    if ts.empty:
        return None
    date, value = ts.index[-1], float(ts.iloc[-1])
    pct = name in transforms.PERCENT_TRANSFORMS
    unit = "%" if pct else ind.unit
    decimals = 1 if pct else ind.decimals

    # Reference points for changes.
    prev = float(ts.iloc[-2]) if ts.size > 1 else None
    year_ago = ts.asof(date - pd.DateOffset(years=1)) if ind.freq == "D" else ts.get(date - pd.DateOffset(years=1))
    ytd_base = ts[ts.index < pd.Timestamp(date.year, 1, 1)]
    ytd_base = float(ytd_base.iloc[-1]) if not ytd_base.empty else None

    # How changes are expressed: rates in pp or bp (a % rate shown in bp is scaled by 100),
    # change_unit "%" means relative % change (e.g. exchange rates), otherwise the series' own units.
    if pct:
        change_unit = "pp"
    elif ind.change_unit:
        change_unit = ind.change_unit
    elif unit in ("%", "% of GDP"):
        change_unit = "pp"
    else:
        change_unit = unit
    relative = change_unit == "%" and not pct
    scale = 100 if (change_unit == "bp" and unit in ("%", "% of GDP")) else 1
    change_decimals = 1 if relative else decimals

    def change(ref):
        if ref is None or pd.isna(ref):
            return None
        if relative:
            return (value / float(ref) - 1) * 100
        return (value - float(ref)) * scale

    is_diff = name in transforms.DIFF_TRANSFORMS
    out = {
        "transform": name,
        "label": transforms.label(name, ind.freq),
        "unit": unit,
        "date": date.strftime("%Y-%m-%d"),
        "period": period_label(date, ind.freq),
        "value": _clean(value),
        "display": fmt_change(value, unit, decimals) if is_diff else fmt_value(value, unit, decimals),
        "prev": _clean(prev),
        "year_ago": _clean(year_ago),
        "ytd_base": _clean(ytd_base),
        "change_unit": change_unit,
    }
    for key, ref in (("change_prev", prev), ("change_year", year_ago), ("change_ytd", ytd_base)):
        c = change(ref)
        out[key] = _clean(c)
        out[key + "_display"] = None if c is None else fmt_change(c, change_unit, change_decimals)
    return out


def subline(ind: Indicator, values: list[dict]) -> str:
    """The second line of a key-indicator tile."""
    head = values[0]
    # A headline that is already a change (q/q, y/y, +k) is followed by the next measure, not a change of a change.
    if head["transform"] != "level" and len(values) > 1:
        return f"{values[1]['display']} {values[1]['label']}".strip()
    if ind.freq == "D" and head["change_ytd_display"]:
        return f"{head['change_ytd_display']} YTD"
    if head["change_year_display"]:
        return f"{head['change_year_display']} y/y"
    return ""


def summarize(ind: Indicator, series: pd.Series | None, entry: dict) -> dict:
    values = []
    if series is not None and not series.empty:
        values = [v for v in (summarize_transform(ind, series, t) for t in ind.transforms) if v]
    last_date = entry.get("last_date") or (series.index[-1].strftime("%Y-%m-%d") if series is not None else None)
    status = entry.get("status", "missing" if series is None else "ok")
    return {
        "id": ind.id,
        "label": ind.label,
        "label_es": ind.label_es,
        "section": ind.section,
        "freq": ind.freq,
        "tile": ind.tile,
        "notes": ind.notes,
        "source": sources.SOURCE_NAMES.get(ind.source, ind.source),
        "source_url": ind.source_url(),
        "status": status,
        "out_of_date": is_out_of_date(last_date, ind.max_age),
        "flash": bool(entry.get("flash")),
        "fetched_at": entry.get("fetched_at"),
        "error": entry.get("error") if status != "ok" else None,
        "values": values,
        "headline": values[0] if values else None,
        "subline": subline(ind, values) if values else "",
    }


def build_snapshot(indicators: list[Indicator], store: Store | None = None) -> dict:
    store = store or Store()
    catalog = store.load_catalog()
    items = [summarize(ind, store.load_series(ind.id), catalog.get(ind.id, {})) for ind in indicators]
    fetched = [i["fetched_at"] for i in items if i["fetched_at"]]
    return {
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "data_as_of": max(fetched) if fetched else None,
        "tiles": [i["id"] for i in sorted((i for i in items if i["tile"]), key=lambda i: i["tile"])],
        "indicators": items,
    }
