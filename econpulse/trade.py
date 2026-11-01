"""The Trade page (site/trade.html): Spain's trade in goods and services, its partners and its prices.

Monthly exports and imports by chapter of the Harmonised System from Eurostat's Comext
(sources/comext.py), grouped into 18 product groups in the registry (trade_exp_<group>,
trade_imp_<group>), and all goods by partner (trade_exp_<partner>, trade_imp_<partner>). Services
by type come from the quarterly balance of payments (svc_exp_<type>, svc_imp_<type>), and export and
import prices of industrial products from Eurostat's short-term statistics. The page shows flows as
totals over the past 12 months (four quarters for services), which smooth out the seasons and the
noise of single months: tables, rankings, the balance with and without energy, and every group since 2008.
"""

import pandas as pd

from . import transforms
from .snapshot import fmt_change, fmt_value, period_label
from .tables import Data

CHART_START = "2008-01-01"
COMEXT = "Eurostat (Comext)"
BOP = "Eurostat (balance of payments)"
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
# (partner slug, label, indent): the EU and its members, then the rest of the world.
PARTNERS = [("eu", "European Union", 0), ("france", "France", 1), ("germany", "Germany", 1), ("portugal", "Portugal", 1),
            ("italy", "Italy", 1), ("netherlands", "Netherlands", 1), ("belgium", "Belgium", 1), ("poland", "Poland", 1),
            ("non_eu", "Outside the EU", 0), ("uk", "United Kingdom", 1), ("switzerland", "Switzerland", 1),
            ("turkey", "Türkiye", 1), ("us", "United States", 1), ("mexico", "Mexico", 1), ("brazil", "Brazil", 1),
            ("china", "China", 1), ("japan", "Japan", 1), ("india", "India", 1), ("morocco", "Morocco", 1),
            ("algeria", "Algeria", 1), ("nigeria", "Nigeria", 1)]
BALANCE_PARTNERS = ["france", "portugal", "germany", "china"]
# Services: the main types, and the parts of other business services.
SERVICES = [("travel", "Tourism and travel"), ("transport", "Transport"), ("business", "Other business services"),
            ("ict", "Telecoms and IT"), ("financial", "Financial services"),
            ("insurance", "Insurance and pensions"), ("ip", "Intellectual property"), ("construction", "Construction")]
BUSINESS = [("rd", "Research and development"), ("consulting", "Consulting and professional"),
            ("technical", "Technical and trade-related")]
SERVICE_IDS = {"total": ("bop_q_exports_services", "bop_q_imports_services"),
               "travel": ("bop_q_travel_credit", "bop_q_travel_debit")}
# Prices: (slug, label, indent); the four main industrial groupings add up to industrial goods.
PRICES = [("all", "Industrial goods", 0), ("intermediate", "Intermediate goods", 1), ("capital", "Capital goods", 1),
          ("consumer", "Consumer goods", 1), ("energy", "Energy", 1), ("ex_energy", "Industrial goods except energy", 0)]
# PAGE: the page's own sections, for the tab's dropdown.
PAGE = ([("overview", "Exports, imports and the balance"), ("by-product", "Trade by product group"),
         ("rankings", "Rankings by product"), ("partners", "Trade by partner"), ("services", "Trade in services"),
         ("prices", "Export and import prices")]
        + [(f"group-{sid}", heading) for sid, heading, _ in SECTIONS] + [("about-data", "About the data")])


def groups() -> list[tuple[str, str]]:
    return [g for _, _, items in SECTIONS for g in items]


def _12m(data: Data, ind_id: str) -> pd.Series | None:
    """Total over the past 12 months (four quarters), € billion."""
    s = data.raw(ind_id)
    if s is None or s.dropna().empty:
        return None
    total = transforms.apply("sum_1y", s.dropna(), data.by_id[ind_id].freq).dropna() / 1000
    return total if not total.empty else None


def _pair(data: Data, exp_id: str, imp_id: str) -> tuple[pd.Series, pd.Series] | None:
    exp, imp = _12m(data, exp_id), _12m(data, imp_id)
    return None if exp is None or imp is None else (exp, imp)


def _flows(data: Data, slug: str) -> tuple[pd.Series, pd.Series] | None:
    return _pair(data, f"trade_exp_{slug}", f"trade_imp_{slug}")


def _svc(data: Data, slug: str) -> tuple[pd.Series, pd.Series] | None:
    return _pair(data, *SERVICE_IDS.get(slug, (f"svc_exp_{slug}", f"svc_imp_{slug}")))


def _yoy(s: pd.Series) -> float | None:
    date = s.index[-1]
    before = s.get(date - pd.DateOffset(years=1))
    return None if before is None or pd.isna(before) or before == 0 else (float(s.iloc[-1]) / float(before) - 1) * 100


def _bn(v: float | None) -> str:
    return "–" if v is None else fmt_value(v, "", 1).strip()


def _pct(v: float | None) -> str:
    return "–" if v is None else fmt_change(v, "%", 1).rstrip("%")


def _eur(v: float, signed: bool = False) -> str:
    """394.4 -> '€394.4 bn'; with signed, -75.2 -> '−€75.2 bn' and 3.1 -> '+€3.1 bn'."""
    body = fmt_value(abs(v), "", 1).strip()
    sign = "−" if v < 0 and body != "0.0" else ("+" if signed and v > 0 and body != "0.0" else "")
    return f"{sign}€{body} bn"


def _on_year(s: pd.Series) -> str:
    g = _yoy(s)
    return "" if g is None else f", {fmt_change(g, '%', 1)} on a year earlier"


def facts(data: Data) -> list[dict]:
    total = _flows(data, "total")
    if total is None:
        return []
    exp, imp = total
    month = period_label(exp.index[-1], "M")
    bal = float(exp.iloc[-1] - imp.iloc[-1])
    out = [{"label": "Exports of goods", "value": _eur(float(exp.iloc[-1])), "sub": f"12 months to {month}{_on_year(exp)}"},
           {"label": "Imports of goods", "value": _eur(float(imp.iloc[-1])), "sub": f"12 months to {month}{_on_year(imp)}"},
           {"label": "Trade balance", "value": _eur(bal, signed=True), "sub": f"12 months to {month}"}]
    energy = _flows(data, "energy")
    if energy is not None and energy[0].index[-1] == exp.index[-1]:
        e_bal = float(energy[0].iloc[-1] - energy[1].iloc[-1])
        out.append({"label": "Balance without energy", "value": _eur(bal - e_bal, signed=True),
                    "sub": f"energy alone: {_eur(e_bal, signed=True)}"})
    return out


def _flow_row(label: str, flows, indent: int, date: pd.Timestamp, total_exp: float) -> dict | None:
    exp, imp = flows
    if exp.index[-1] != date or imp.index[-1] != date:
        return None
    e, i = float(exp.iloc[-1]), float(imp.iloc[-1])
    return {"heading": False, "label": label, "label_es": "", "indent": indent, "period_note": "", "url": None,
            "highlight": False, "cells": [_bn(e), _pct(_yoy(exp)), _pct(e / total_exp * 100).lstrip("+"),
                                           _bn(i), _pct(_yoy(imp)), fmt_change(e - i, "", 1).strip()]}


def _flow_table(title: str, date: pd.Timestamp, freq: str, rows: list[dict], note: str) -> dict:
    span = "12 months" if freq == "M" else "four quarters"
    return {"title": title, "caption": f"€ billion over the past {span} · through {period_label(date, freq)}",
            "through": period_label(date, freq),
            "columns": ["Exports", "y/y %", "Share of exports %", "Imports", "y/y %", "Balance"],
            "column_notes": [], "rows": [r for r in rows if r], "note": note}


def table(data: Data) -> dict | None:
    total = _flows(data, "total")
    if total is None:
        return None
    date, total_exp = total[0].index[-1], float(total[0].iloc[-1])
    rows = [_flow_row("All goods", total, 0, date, total_exp)]
    for _, heading, items in SECTIONS:
        rows.append({"heading": True, "label": heading, "cells": []})
        for slug, label in items:
            flows = _flows(data, slug)
            if flows is not None:
                rows.append(_flow_row(label, flows, 1, date, total_exp))
    return _flow_table("Product group", date, "M", rows,
                       "Changes compare the past 12 months with the 12 months before. Product groups gather chapters "
                       "of the Harmonised System (see About the data).")


def _line(id_, title, subtitle, series, start=CHART_START, **extra) -> dict:
    iso = lambda s: [d.strftime("%Y-%m-%d") for d in s.index]
    keep = lambda s: s[s.index >= start].dropna().round(3)
    out = []
    for name, s, *opts in series:
        s = keep(s)
        out.append({"name": name, "x": iso(s), "y": s.tolist(), **(opts[0] if opts else {})})
    return {"id": id_, "title": title, "subtitle": subtitle, "kind": "line", "unit": "€ bn", "decimals": 1,
            "freq": "M", "ref_lines": [], "series": out, "source": COMEXT, **extra}


def _ranking(id_, title, subtitle, unit, decimals, date, points: list[tuple[str, float]], ref=None,
             x_title="Product group", freq="M", source=COMEXT) -> dict | None:
    if len(points) < 2:
        return None
    points = sorted(points, key=lambda p: p[1], reverse=True)
    return {"id": id_, "title": title, "kind": "hbar", "x_kind": "category", "x_title": x_title,
            "subtitle": f"{subtitle} · {period_label(date, freq)}", "unit": unit, "decimals": decimals,
            "series": [{"name": title, "x": [p[0] for p in points], "y": [round(p[1], 3) for p in points]}],
            "ref_lines": [{"y": round(ref[1], 3), "label": ref[0]}] if ref else [], "freq": None,
            "source": source}


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


def partners(data: Data) -> dict | None:
    """Goods trade with the EU and Spain's main partners."""
    total = _flows(data, "total")
    if total is None:
        return None
    exp_all, imp_all = total
    date, total_exp, total_imp = exp_all.index[-1], float(exp_all.iloc[-1]), float(imp_all.iloc[-1])
    flows = {slug: f for slug, _, _ in PARTNERS if (f := _flows(data, slug)) and f[0].index[-1] == date}
    if not flows:
        return None
    rows = [_flow_row("All partners", total, 0, date, total_exp)]
    rows += [_flow_row(label, flows[slug], indent, date, total_exp) for slug, label, indent in PARTNERS if slug in flows]
    month = period_label(date, "M")
    countries = [(label, float(flows[slug][0].iloc[-1]), float(flows[slug][1].iloc[-1]))
                 for slug, label, indent in PARTNERS if indent and slug in flows]
    out_facts = []
    if "eu" in flows:
        eu = float(flows["eu"][0].iloc[-1])
        out_facts.append({"label": "Exports sold in the EU", "value": f"{eu / total_exp * 100:.1f}%",
                          "sub": f"{_eur(eu)} over the 12 months to {month}"})
    if countries:
        market = max(countries, key=lambda c: c[1])
        supplier = max(countries, key=lambda c: c[2])
        deficit = min(countries, key=lambda c: c[1] - c[2])
        out_facts += [{"label": "Largest market", "value": market[0],
                       "sub": f"{_eur(market[1])} of exports, {market[1] / total_exp * 100:.1f}% of the total"},
                      {"label": "Largest supplier", "value": supplier[0],
                       "sub": f"{_eur(supplier[2])} of imports, {supplier[2] / total_imp * 100:.1f}% of the total"},
                      {"label": "Largest deficit", "value": deficit[0],
                       "sub": f"{_eur(deficit[1] - deficit[2], signed=True)} over the 12 months"}]
    charts_ = []
    if "eu" in flows:
        charts_.append(_line("trade-eu-share", "The EU's share of Spain's goods trade",
                             "% of exports and imports over the past 12 months",
                             [("Exports", flows["eu"][0] / exp_all * 100), ("Imports", flows["eu"][1] / imp_all * 100)],
                             start="2002-12-01", unit="%"))
    picked = [(label, flows[slug]) for slug in BALANCE_PARTNERS for s, label, _ in PARTNERS if s == slug and slug in flows]
    if picked:
        charts_.append(_line("trade-partner-balances", "Trade balance with selected partners",
                             "Exports less imports over the past 12 months, € billion",
                             [(label, e - i) for label, (e, i) in picked], start="2005-01-01", signed=True))
    charts_ += [c for c in (
        _ranking("partner-exports-ranking", "Exports by partner", "€ billion over the past 12 months", "€ bn", 1, date,
                 [(lab, e) for lab, e, _ in countries], x_title="Partner"),
        _ranking("partner-balance-ranking", "Trade balance by partner", "Exports less imports, € billion, past 12 months",
                 "€ bn", 1, date, [(lab, e - i) for lab, e, i in countries], x_title="Partner"),
    ) if c]
    return {"id": "partners", "title": "Trade by partner",
            "intro": ("Where Spain's goods go and where they come from: the EU and the largest partners, over the past "
                      "12 months. Most exports go to the EU; imports lean more on China and on energy suppliers."),
            "facts": out_facts,
            "table": _flow_table("Partner", date, "M", rows,
                                 "Changes compare the past 12 months with the 12 months before. All goods, by country "
                                 "of destination for exports and of origin for imports."),
            "charts": charts_}


def services(data: Data) -> dict | None:
    """Services trade by type, from the quarterly balance of payments."""
    total = _svc(data, "total")
    if total is None:
        return None
    exp_all, imp_all = total
    date, total_exp = exp_all.index[-1], float(exp_all.iloc[-1])
    flows = {slug: f for slug, _ in SERVICES + BUSINESS if (f := _svc(data, slug)) and f[0].index[-1] == date}
    labels = dict(SERVICES + BUSINESS)
    if all(slug in flows for slug, _ in SERVICES):
        # Other services: the total less the main types (manufacturing, repairs, personal and government services).
        other = tuple((t - sum(flows[slug][k] for slug, _ in SERVICES)).dropna() for k, t in enumerate(total))
        if not other[0].empty and other[0].index[-1] == date:
            flows["other"], labels["other"] = other, "Other services"
    rows = [_flow_row("All services", total, 0, date, total_exp)]
    for slug, label in SERVICES:
        if slug in flows:
            rows.append(_flow_row(label, flows[slug], 1, date, total_exp))
        if slug == "business":
            rows += [_flow_row(lab, flows[s], 2, date, total_exp) for s, lab in BUSINESS if s in flows]
    if "other" in flows:
        rows.append(_flow_row("Other services", flows["other"], 1, date, total_exp))
    quarter = period_label(date, "Q")
    span = f"four quarters to {quarter}"
    bal = total_exp - float(imp_all.iloc[-1])
    out_facts = [{"label": "Exports of services", "value": _eur(total_exp), "sub": f"{span}{_on_year(exp_all)}"},
                 {"label": "Imports of services", "value": _eur(float(imp_all.iloc[-1])), "sub": f"{span}{_on_year(imp_all)}"},
                 {"label": "Services surplus", "value": _eur(bal, signed=True), "sub": span}]
    if "travel" in flows:
        rest = exp_all - flows["travel"][0]
        out_facts.append({"label": "Exports other than tourism", "value": _eur(float(rest.iloc[-1])),
                          "sub": f"{float(rest.iloc[-1]) / total_exp * 100:.0f}% of services exports{_on_year(rest)}"})
    charts_ = [_line("services-totals", "Exports and imports of services", "€ billion over the past four quarters",
                     [("Exports", exp_all), ("Imports", imp_all)], start="2000-01-01", freq="Q", source=BOP)]
    if "travel" in flows:
        charts_.append(_line("services-tourism", "Tourism and other services exports",
                             "Exports, € billion over the past four quarters",
                             [("Tourism and travel", flows["travel"][0]), ("Other services", exp_all - flows["travel"][0])],
                             start="2000-01-01", freq="Q", source=BOP))
    short = {"business": "Business services", "ict": "Telecoms and IT", "transport": "Transport"}
    main = [(name, flows[s][0]) for s, name in short.items() if s in flows]
    if main:
        charts_.append(_line("services-business", "Business, IT and transport exports",
                             "Exports, € billion over the past four quarters", main, freq="Q", source=BOP))
    kinds = [s for s, _ in SERVICES if s in flows] + (["other"] if "other" in flows else [])
    charts_ += [c for c in (
        _ranking("services-exports-ranking", "Services exports by type", "€ billion over the past four quarters", "€ bn", 1,
                 date, [(labels[s], float(flows[s][0].iloc[-1])) for s in kinds], x_title="Type of service", freq="Q",
                 source=BOP),
        _ranking("services-balance-ranking", "Services balance by type", "Exports less imports, € billion, past four quarters",
                 "€ bn", 1, date, [(labels[s], float(flows[s][0].iloc[-1] - flows[s][1].iloc[-1])) for s in kinds],
                 x_title="Type of service", freq="Q", source=BOP),
    ) if c]
    return {"id": "services", "title": "Trade in services",
            "intro": ("Spain's exports and imports of services by type, from the balance of payments. Tourism is the "
                      "largest single item, but the other services together bring in more than half of exports."),
            "facts": out_facts,
            "table": _flow_table("Type of service", date, "Q", rows,
                                 "Changes compare the past four quarters with the four before. Other services are the "
                                 "total less the types shown: manufacturing and repair services, personal, cultural "
                                 "and government services, for which Eurostat publishes no separate Spanish figures."),
            "charts": charts_}


def _latest(data: Data, ind_id: str, date: pd.Timestamp | None = None) -> tuple[float, float | None] | None:
    """The latest level (on `date`, if given) and its change on a year earlier, %."""
    s = data.raw(ind_id)
    if s is None or s.dropna().empty:
        return None
    s = s.dropna()
    if date is not None and s.index[-1] != date:
        return None
    return float(s.iloc[-1]), _yoy(s)


def prices(data: Data) -> dict | None:
    """Export and import prices of industrial goods, and the terms of trade."""
    ex, im = data.raw("export_prices_all"), data.raw("import_prices_all")
    if ex is None or im is None or ex.dropna().empty or im.dropna().empty:
        return None
    date = min(ex.dropna().index[-1], im.dropna().index[-1])
    month = period_label(date, "M")
    rows, levels = [], {}
    for slug, label, indent in PRICES:
        e, i = _latest(data, f"export_prices_{slug}", date), _latest(data, f"import_prices_{slug}", date)
        if e is None or i is None:
            continue
        levels[slug] = (e, i)
        rows.append({"heading": False, "label": label, "label_es": "", "indent": indent, "period_note": "", "url": None,
                     "highlight": False, "cells": [fmt_value(e[0], "", 1).strip(), _pct(e[1]),
                                                   fmt_value(i[0], "", 1).strip(), _pct(i[1]),
                                                   fmt_value(e[0] / i[0] * 100, "", 1).strip()]})
    if "all" not in levels:
        return None
    (e_lvl, e_yoy), (i_lvl, i_yoy) = levels["all"]
    out_facts = [{"label": "Export prices", "value": fmt_change(e_yoy, "%", 1) if e_yoy is not None else "–",
                  "sub": f"industrial goods, {month} on a year earlier"},
                 {"label": "Import prices", "value": fmt_change(i_yoy, "%", 1) if i_yoy is not None else "–",
                  "sub": f"industrial goods, {month} on a year earlier"}]
    tot = _latest(data, "terms_of_trade_industrial")
    if tot is not None and tot[1] is not None:
        out_facts.append({"label": "Terms of trade", "value": fmt_change(tot[1], "%", 1),
                          "sub": "export prices relative to import prices, on a year earlier"})
    if "ex_energy" in levels and levels["ex_energy"][0][1] is not None and levels["ex_energy"][1][1] is not None:
        out_facts.append({"label": "Export prices without energy", "value": fmt_change(levels["ex_energy"][0][1], "%", 1),
                          "sub": f"import prices without energy: {fmt_change(levels['ex_energy'][1][1], '%', 1)}"})
    yoy = lambda ind_id: transforms.apply("yoy", data.raw(ind_id).dropna(), "M")
    charts_ = [_line("prices-yoy", "Export and import prices", "Industrial goods, % change on a year earlier",
                     [("Export prices", yoy("export_prices_all")), ("Import prices", yoy("import_prices_all"))],
                     start="2006-01-01", unit="%", signed=True, source="Eurostat")]
    terms = [(name, data.raw(i).dropna()) for i, name in (("terms_of_trade", "Goods and services"), ("terms_of_trade_goods", "Goods"))
             if data.raw(i) is not None and not data.raw(i).dropna().empty]
    if terms:
        charts_.append(_line("terms-of-trade", "Terms of trade",
                             "Export deflator ÷ import deflator, 2015 = 100 (national accounts)", terms,
                             start="1995-01-01", unit="", freq="Q", source="Eurostat (national accounts)",
                             ref_lines=[{"y": 100, "label": "2015"}]))
    for flow, title in (("export", "Export prices by type of good"), ("import", "Import prices by type of good")):
        lines = [(label, data.raw(f"{flow}_prices_{slug}").dropna()) for slug, label, indent in PRICES
                 if indent and slug in levels]
        if lines:
            charts_.append(_line(f"{flow}-prices-groups", title, "Index, 2021 = 100", lines, start="2015-01-01",
                                 unit="", source="Eurostat", ref_lines=[{"y": 100, "label": "2021"}]))
    return {"id": "prices", "title": "Export and import prices",
            "intro": ("What Spanish industry charges abroad and what it pays for industrial goods bought from abroad. "
                      "When export prices rise faster than import prices, the terms of trade improve and the same "
                      "exports pay for more imports."),
            "facts": out_facts,
            "table": {"title": "Industrial goods", "caption": f"Index, 2021 = 100 · {month}", "through": month,
                      "columns": ["Export prices", "y/y %", "Import prices", "y/y %", "Export ÷ import prices"],
                      "column_notes": [], "rows": rows,
                      "note": ("Export prices are the prices Spanish industry charges for products sold abroad; import "
                               "prices are those of industrial products bought from abroad. Not seasonally adjusted.")},
            "charts": charts_}


def page(data: Data) -> dict:
    overview, rankings, per_group = charts(data)
    sections = []
    for sid, heading, _ in SECTIONS:
        specs = [c for s, c in per_group if s == sid]
        if specs:
            sections.append({"id": f"group-{sid}", "title": heading, "charts": specs})
    extras = [x for x in (partners(data), services(data), prices(data)) if x]
    groups_hs = {}
    for ind in data.by_id.values():
        if ind.id.startswith("trade_exp_") and ind.source == "comext" and ind.key != "TOTAL":
            groups_hs[ind.id.removeprefix("trade_exp_")] = ind.key
    return {"facts": facts(data), "table": table(data), "overview": overview, "rankings": rankings,
            "extras": extras, "sections": sections,
            "charts": overview + rankings + [c for x in extras for c in x["charts"]] + [c for _, c in per_group],
            "chapters": [(label, groups_hs.get(slug, "")) for slug, label in groups()]}
