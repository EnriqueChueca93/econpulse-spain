"""Turn stored series into the snapshot the site displays: latest values, changes,
display strings and status for every indicator.

Number formatting lives here (not in JavaScript) so the site and the CLI agree.
"""

import math
from datetime import datetime, timezone

import pandas as pd

from . import i18n, transforms
from .fetch import is_out_of_date
from .registry import Indicator
from .store import Store

MINUS = "−"  # typographic minus, as on econvitals


def period_label(date: pd.Timestamp, freq: str) -> str:
    """"26 Oct 2026", "Oct 2026", "Q3 2026", "2026" (in Spanish "26 oct 2026", "oct 2026", "T3 2026")."""
    if freq == "D":
        return i18n.day_month_year(date)
    if freq == "M":
        return i18n.month_year(date)
    if freq == "Q":
        return i18n.quarter(date)
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
        return f"{_num(v, decimals, thousands=True)}%"
    if unit == "% of GDP":
        return f"{_num(v, decimals)}{i18n._('% of GDP')}"
    if unit == "bp":
        return f"{_num(v, 0)} {i18n._('bp')}"
    if unit == "thousands":
        return f"{n}k"
    if unit in ("index", "balance", "rate"):
        return n
    if unit == "$/bbl":
        return f"{sign}${digits}"
    # In Spanish the euro sign follows the figure ("58.2 mm €"); the number keeps the English format.
    es = i18n.lang() == "es"
    if unit == "€ mn":
        return f"{n} {i18n._('mn')} €" if es else f"{sign}€{digits} {i18n._('mn')}"
    if unit == "€ bn":
        return f"{n} {i18n._('bn')} €" if es else f"{sign}€{digits} {i18n._('bn')}"
    if unit == "€":
        return f"{n} €" if es else f"{sign}€{digits}"
    return f"{n} {i18n._(unit)}"  # e.g. "224.9 €/MWh", "93,858 vehicles"


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
        return f"{head['change_ytd_display']} {i18n.figures('YTD')}"
    if head["change_year_display"]:
        return f"{head['change_year_display']} {i18n.figures('y/y')}"
    return ""


def summarize(ind: Indicator, series: pd.Series | None, entry: dict) -> dict:
    values = []
    if series is not None and not series.empty:
        for name in ind.transforms:
            try:
                v = summarize_transform(ind, series, name)
            except ValueError:  # e.g. too little history to seasonally adjust
                v = None
            if v:
                values.append(v)
    last_date = entry.get("last_date") or (series.index[-1].strftime("%Y-%m-%d") if series is not None else None)
    status = entry.get("status", "missing" if series is None else "ok")
    return {
        "id": ind.id,
        "label": i18n.pick(ind.label, ind.label_es),   # the official Spanish name on the Spanish site
        "label_en": ind.label,
        "label_es": ind.label_es,
        "section": ind.section,
        "freq": ind.freq,
        "tile": ind.tile,
        "notes": ind.notes,
        "source": i18n._(ind.source_name),
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
