"""The Trade page (site/trade.html): Spain's goods trade by product group.

Monthly exports and imports by chapter of the Harmonised System from Eurostat's Comext
(sources/comext.py), grouped into 18 product groups in the registry (trade_exp_<group>,
trade_imp_<group>). The page shows totals over the past 12 months, which smooth out the months'
seasonality and noise: a table by group, rankings, the balance with and without energy, and the
exports and imports of every group since 2008.
"""

import pandas as pd

from . import transforms
from .snapshot import fmt_change, fmt_value, period_label
from .tables import Data

CHART_START = "2008-01-01"
# (section id, heading, [(group slug, label)]): the labels are short for the charts.
SECTIONS = [
    ("food", "Food and drink", [("meat_fish", "Meat, fish and dairy"), ("fruit_veg", "Fruit and vegetables"),
                                ("fats", "Olive oil and fats"), ("drinks", "Drinks and tobacco"),
                                ("other_food", "Other food and feed")]),
    ("materials", "Energy and materials", [("energy", "Energy"), ("minerals", "Stone, ceramics and glass"),
                                           ("metals", "Metals and ores"), ("wood_paper", "Leather, wood and paper")]),
    ("chemicals", "Chemicals and plastics", [("chemicals", "Chemicals"), ("pharma", "Pharmaceuticals"),
                                             ("plastics", "Plastics and rubber")]),
    ("manufactures", "Manufactures", [("textiles", "Textiles and clothing"), ("machinery", "Machinery"),
                                      ("electrical", "Electrical equipment"), ("vehicles", "Vehicles and parts"),
                                      ("other_transport", "Aircraft, ships and trains"), ("other", "Other goods")]),
]
# PAGE: the page's own sections, for the tab's dropdown.
PAGE = [("overview", "Exports, imports and the balance"), ("by-product", "Trade by product group"),
        ("rankings", "Rankings")] + [(f"group-{sid}", heading) for sid, heading, _ in SECTIONS] + [("about-data", "About the data")]


def groups() -> list[tuple[str, str]]:
    return [g for _, _, items in SECTIONS for g in items]


def _12m(data: Data, ind_id: str) -> pd.Series | None:
    """Total over the past 12 months, € billion."""
    s = data.raw(ind_id)
    if s is None or s.dropna().empty:
        return None
    total = transforms.apply("sum_1y", s.dropna(), "M").dropna() / 1000
    return total if not total.empty else None


def _flows(data: Data, slug: str) -> tuple[pd.Series, pd.Series] | None:
    exp, imp = _12m(data, f"trade_exp_{slug}"), _12m(data, f"trade_imp_{slug}")
    return None if exp is None or imp is None else (exp, imp)


def _yoy(s: pd.Series) -> float | None:
    date = s.index[-1]
    before = s.get(date - pd.DateOffset(years=1))
    return None if before is None or before == 0 else (float(s.iloc[-1]) / float(before) - 1) * 100


def _bn(v: float | None) -> str:
    return "–" if v is None else fmt_value(v, "", 1).strip()


def _pct(v: float | None) -> str:
    return "–" if v is None else fmt_change(v, "%", 1).rstrip("%")


def _eur(v: float, signed: bool = False) -> str:
    """394.4 -> '€394.4 bn'; with signed, -75.2 -> '−€75.2 bn' and 3.1 -> '+€3.1 bn'."""
    body = fmt_value(abs(v), "", 1).strip()
    sign = "−" if v < 0 and body != "0.0" else ("+" if signed and v > 0 and body != "0.0" else "")
    return f"{sign}€{body} bn"


def facts(data: Data) -> list[dict]:
    total = _flows(data, "total")
    if total is None:
        return []
    exp, imp = total
    month = period_label(exp.index[-1], "M")
    on_year = lambda s: f", {fmt_change(g, '%', 1)} on a year earlier" if (g := _yoy(s)) is not None else ""
    bal = float(exp.iloc[-1] - imp.iloc[-1])
    out = [{"label": "Exports of goods", "value": _eur(float(exp.iloc[-1])), "sub": f"12 months to {month}{on_year(exp)}"},
           {"label": "Imports of goods", "value": _eur(float(imp.iloc[-1])), "sub": f"12 months to {month}{on_year(imp)}"},
           {"label": "Trade balance", "value": _eur(bal, signed=True), "sub": f"12 months to {month}"}]
    energy = _flows(data, "energy")
    if energy is not None and energy[0].index[-1] == exp.index[-1]:
        e_bal = float(energy[0].iloc[-1] - energy[1].iloc[-1])
        out.append({"label": "Balance without energy", "value": _eur(bal - e_bal, signed=True),
                    "sub": f"energy alone: {_eur(e_bal, signed=True)}"})
    return out


def table(data: Data) -> dict | None:
    total = _flows(data, "total")
    if total is None:
        return None
    exp_all, imp_all = total
    date = exp_all.index[-1]

    def row(label, flows, indent):
        exp, imp = flows
        if exp.index[-1] != date:
            return None
        e, i = float(exp.iloc[-1]), float(imp.iloc[-1])
        return {"heading": False, "label": label, "label_es": "", "indent": indent, "period_note": "", "url": None,
                "highlight": False, "cells": [_bn(e), _pct(_yoy(exp)), _pct(e / float(exp_all.iloc[-1]) * 100).lstrip("+"),
                                               _bn(i), _pct(_yoy(imp)), fmt_change(e - i, "", 1).strip()]}

    rows = [row("All goods", total, 0)]
    for _, heading, items in SECTIONS:
        rows.append({"heading": True, "label": heading, "cells": []})
        for slug, label in items:
            flows = _flows(data, slug)
            if flows is not None and (r := row(label, flows, 1)):
                rows.append(r)
    return {"title": "Product group", "caption": f"€ billion over the past 12 months · through {period_label(date, 'M')}",
            "through": period_label(date, "M"),
            "columns": ["Exports", "y/y %", "Share of exports %", "Imports", "y/y %", "Balance"],
            "column_notes": [], "rows": rows,
            "note": ("Changes compare the past 12 months with the 12 months before. Product groups gather chapters "
                     "of the Harmonised System (see About the data).")}


def _line(id_, title, subtitle, series, start=CHART_START, **extra) -> dict:
    iso = lambda s: [d.strftime("%Y-%m-%d") for d in s.index]
    keep = lambda s: s[s.index >= start].round(3)
    out = []
    for name, s, *opts in series:
        s = keep(s)
        out.append({"name": name, "x": iso(s), "y": s.tolist(), **(opts[0] if opts else {})})
    return {"id": id_, "title": title, "subtitle": subtitle, "kind": "line", "unit": "€ bn", "decimals": 1,
            "freq": "M", "ref_lines": [], "series": out, "source": "Eurostat (Comext)", **extra}


def _ranking(id_, title, subtitle, unit, decimals, date, points: list[tuple[str, float]], ref=None) -> dict | None:
    if len(points) < 2:
        return None
    points = sorted(points, key=lambda p: p[1], reverse=True)
    return {"id": id_, "title": title, "kind": "hbar", "x_kind": "category", "x_title": "Product group",
            "subtitle": f"{subtitle} · {period_label(date, 'M')}", "unit": unit, "decimals": decimals,
            "series": [{"name": title, "x": [p[0] for p in points], "y": [round(p[1], 3) for p in points]}],
            "ref_lines": [{"y": round(ref[1], 3), "label": ref[0]}] if ref else [], "freq": None,
            "source": "Eurostat (Comext)"}


def charts(data: Data) -> tuple[list[dict], list[dict], list[dict]]:
    """The overview charts, the rankings, and one chart per group (with its section id)."""
    total = _flows(data, "total")
    if total is None:
        return [], [], []
    exp, imp = total
    date = exp.index[-1]
    overview = [_line("trade-totals", "Exports and imports of goods", "€ billion over the past 12 months",
                      [("Exports", exp), ("Imports", imp)], start="2005-01-01")]
    energy = _flows(data, "energy")
    if energy is not None:
        bal = exp - imp
        e_bal = (energy[0] - energy[1]).reindex(bal.index)
        overview.append(_line("trade-balance", "The trade balance and energy",
                              "Balance over the past 12 months, € billion",
                              [("All goods", bal, {"color": "ink"}), ("Energy", e_bal), ("Everything else", bal - e_bal)],
                              start="2005-01-01", signed=True))
    points = [(label, *flows) for slug, label in groups()
              if (flows := _flows(data, slug)) and flows[0].index[-1] == date]
    growth = [(lab, _yoy(e)) for lab, e, _ in points]
    rankings = [c for c in (
        _ranking("exports-ranking", "Exports by product group", "€ billion over the past 12 months", "€ bn", 1, date,
                 [(lab, float(e.iloc[-1])) for lab, e, _ in points]),
        _ranking("balance-ranking", "Trade balance by product group", "Exports less imports, € billion, past 12 months",
                 "€ bn", 1, date, [(lab, float(e.iloc[-1] - i.iloc[-1])) for lab, e, i in points]),
        _ranking("export-growth-ranking", "Export growth by product group",
                 "Past 12 months, % change on the 12 months before", "%", 1, date,
                 [(lab, g) for lab, g in growth if g is not None],
                 ("All goods", _yoy(exp)) if _yoy(exp) is not None else None),
    ) if c]
    per_group = []
    for sid, _, items in SECTIONS:
        for slug, label in items:
            flows = _flows(data, slug)
            if flows is None:
                continue
            spec = _line(f"trade-{slug.replace('_', '-')}", label, "€ billion over the past 12 months",
                         [("Exports", flows[0]), ("Imports", flows[1])])
            per_group.append((sid, spec))
    return overview, rankings, per_group


def page(data: Data) -> dict:
    overview, rankings, per_group = charts(data)
    sections = []
    for sid, heading, _ in SECTIONS:
        specs = [c for s, c in per_group if s == sid]
        if specs:
            sections.append({"id": f"group-{sid}", "title": heading, "charts": specs})
    groups_hs = {}
    for ind in data.by_id.values():
        if ind.id.startswith("trade_exp_") and ind.source == "comext" and ind.key != "TOTAL":
            groups_hs[ind.id.removeprefix("trade_exp_")] = ind.key
    return {"facts": facts(data), "table": table(data), "overview": overview, "rankings": rankings,
            "sections": sections, "charts": overview + rankings + [c for _, c in per_group],
            "chapters": [(label, groups_hs.get(slug, "")) for slug, label in groups()]}
