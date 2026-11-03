"""A deeper GDP page (Batch 34d): contributions to growth by component and by branch, the income side and the
labour share, productivity in detail, and living standards.

Contributions are a Macroscope calculation from INE's quarterly national accounts (seasonally and calendar
adjusted): a component's volume growth times its share of nominal GDP in the base period (the quarter before for
q/q, the same quarter a year earlier for y/y), the usual approximation for chain-linked volumes. INE publishes
only the domestic and external totals; inventories are what is left of INE's domestic-demand contribution after
consumption and fixed investment, so the demand side adds up to INE's totals, give or take its rounding and the
chain-linking. On the supply side, the ten branches and net taxes on products add up to GDP growth the same way.
"""

import numpy as np
import pandas as pd

from . import i18n
from .charts import localise
from .i18n import _
from .snapshot import fmt_change, fmt_value, period_label
from .tables import Data

# (label, volume id, current-price id, sign): imports subtract from GDP.
DEMAND = [("Household consumption", "cons_hh_npish", "cp_cons_hh_npish", 1),
          ("Government consumption", "consumption_government", "cp_cons_government", 1),
          ("Fixed investment", "investment", "cp_gfcf", 1),
          ("Exports", "exports", "cp_exports", 1),
          ("Imports", "imports", "cp_imports", -1)]
# INE's ten branches: (label, volume id, current-price id, hours id).
BRANCHES = [("Agriculture", "gva_agriculture", "cp_gva_agriculture", "hours_cn_agriculture"),
            ("Industry", "gva_industry", "cp_gva_industry", "hours_cn_industry"),
            ("Construction", "gva_construction", "cp_gva_construction", "hours_cn_construction"),
            ("Trade, transport and hospitality", "gva_trade", "cp_gva_trade", "hours_cn_trade"),
            ("Information and communication", "gva_information", "cp_gva_information", "hours_cn_information"),
            ("Finance and insurance", "gva_finance", "cp_gva_finance", "hours_cn_finance"),
            ("Real estate", "gva_real_estate", "cp_gva_real_estate", "hours_cn_real_estate"),
            ("Professional and administrative services", "gva_professional", "cp_gva_professional", "hours_cn_professional"),
            ("Public administration, education and health", "gva_public", "cp_gva_public", "hours_cn_public"),
            ("Arts and other services", "gva_arts", "cp_gva_arts", "hours_cn_arts")]
NET_TAXES = ("Taxes less subsidies on products", "net_taxes_products", "cp_net_taxes_products")
LAG = {"q": 1, "y": 4}
START = "2022-01-01"
USES = sorted({i for _l, v, c, *_rest in DEMAND + BRANCHES for i in (v, c)} | {h for *_x, h in BRANCHES}
              | {"gdp", "gdp_nominal", "contrib_domestic_qq", "contrib_domestic_yy", "contrib_external_qq",
                 "contrib_external_yy", "net_taxes_products", "cp_net_taxes_products", "hours_cn", "jobs_fte",
                 "compensation_employees", "operating_surplus", "net_taxes_production"})


def _q(data: Data, ind_id: str) -> pd.Series | None:
    s = data.raw(ind_id)
    return None if s is None or s.dropna().empty else s.dropna()


def contribution(data: Data, volume: str, current: str, horizon: str) -> pd.Series | None:
    """Percentage points of GDP growth: volume growth over the horizon times the nominal share at its start."""
    v, n, gdp_n = _q(data, volume), _q(data, current), _q(data, "gdp_nominal")
    if v is None or n is None or gdp_n is None:
        return None
    k = LAG[horizon]
    growth = (v / v.shift(k) - 1) * 100
    share = (n / gdp_n).shift(k)
    return (growth * share).dropna()


def demand(data: Data, horizon: str) -> dict[str, pd.Series]:
    """Each demand component's contribution, inventories as the rest of INE's domestic-demand contribution."""
    out = {label: c * sign for label, v, n, sign in DEMAND if (c := contribution(data, v, n, horizon)) is not None}
    domestic = _q(data, f"contrib_domestic_{horizon}{horizon}")
    consumption_investment = [out[k] for k in ("Household consumption", "Government consumption", "Fixed investment") if k in out]
    if domestic is not None and len(consumption_investment) == 3:
        out["Inventories"] = (domestic - sum(consumption_investment)).dropna()
    return out


def supply(data: Data, horizon: str) -> dict[str, pd.Series]:
    out = {label: c for label, v, n, _h in BRANCHES if (c := contribution(data, v, n, horizon)) is not None}
    label, v, n = NET_TAXES
    if (c := contribution(data, v, n, horizon)) is not None:
        out[label] = c
    return out


def _bars(chart_id: str, title: str, subtitle: str, parts: dict[str, pd.Series], total: pd.Series | None,
          order: list[str]) -> dict | None:
    series = []
    for name in order:
        s = parts.get(name)
        if s is not None:
            s = s[s.index >= START]
            series.append({"name": name, "x": [d.strftime("%Y-%m-%d") for d in s.index], "y": s.round(3).tolist()})
    if not series:
        return None
    if total is not None:
        t = total[total.index >= START]
        series.append({"name": "GDP", "kind": "line", "color": "ink", "x": [d.strftime("%Y-%m-%d") for d in t.index],
                       "y": t.round(3).tolist()})
    return localise({"id": chart_id, "title": title, "subtitle": subtitle, "kind": "bar", "stack": True, "signed": True,
                     "unit": "pp", "decimals": 1, "freq": "Q", "ref_lines": [], "series": series,
                     "source": _("INE; Macroscope calculation")})


def _gdp_growth(data: Data, horizon: str) -> pd.Series | None:
    v = _q(data, "gdp")
    return None if v is None else ((v / v.shift(LAG[horizon]) - 1) * 100).dropna()


DEMAND_ORDER = ["Household consumption", "Government consumption", "Fixed investment", "Inventories", "Exports", "Imports"]


def demand_chart_y(data: Data) -> dict | None:
    return _bars("contrib-demand-yy", "Contributions to growth: demand",
                 "Percentage points of GDP growth on a year earlier; imports subtract", demand(data, "y"),
                 _gdp_growth(data, "y"), DEMAND_ORDER)


def demand_chart_q(data: Data) -> dict | None:
    return _bars("contrib-demand-qq", "Contributions to quarterly growth: demand",
                 "Percentage points of GDP growth on the previous quarter; imports subtract", demand(data, "q"),
                 _gdp_growth(data, "q"), DEMAND_ORDER)


def supply_chart_y(data: Data) -> dict | None:
    parts = supply(data, "y")
    # Ten branches are too many bars to tell apart: the four largest service branches stay, the rest group.
    grouped = {"Industry": parts.get("Industry"), "Construction": parts.get("Construction"),
               "Trade, transport and hospitality": parts.get("Trade, transport and hospitality"),
               "Public administration, education and health": parts.get("Public administration, education and health")}
    others = [s for k, s in parts.items() if k not in grouped and s is not None]
    if others:
        grouped["Other branches and net taxes"] = sum(others).dropna()
    return _bars("contrib-supply-yy", "Contributions to growth: branches",
                 "Percentage points of GDP growth on a year earlier, by branch of activity",
                 {k: v for k, v in grouped.items() if v is not None}, _gdp_growth(data, "y"), list(grouped))


def contributions_table(data: Data) -> dict | None:
    """The latest quarter's contributions, q/q and y/y, by demand component and by branch."""
    dq, dy, sq, sy = demand(data, "q"), demand(data, "y"), supply(data, "q"), supply(data, "y")
    if not dy or not sy:
        return None
    last = min(s.index[-1] for s in list(dy.values()) + list(sy.values()))
    cell = lambda parts, k: fmt_change(float(parts[k].get(last, np.nan)), "pp", 1) if k in parts and pd.notna(parts[k].get(last, np.nan)) else "–"
    rows = [{"heading": False, "label": _("GDP growth, %"), "label_es": "", "indent": 0, "period_note": "", "url": None,
             "cells": [fmt_change(float(g.get(last)), "%", 1) if (g := _gdp_growth(data, h)) is not None and last in g.index else "–"
                       for h in ("q", "y")]},
            {"heading": True, "label": _("Demand"), "cells": []}]
    rows += [{"heading": False, "label": _(k), "label_es": "", "indent": 1, "period_note": "", "url": None,
              "cells": [cell(dq, k), cell(dy, k)]} for k in DEMAND_ORDER]
    rows.append({"heading": True, "label": _("Branches of activity"), "cells": []})
    rows += [{"heading": False, "label": _(k), "label_es": "", "indent": 1, "period_note": "", "url": None,
              "cells": [cell(sq, k), cell(sy, k)]} for k, *_rest in BRANCHES + [NET_TAXES]]
    quarter = period_label(last, "Q")
    return {"title": _("Contribution"), "caption": _("Percentage points of GDP growth · {quarter}").format(quarter=quarter),
            "through": quarter, "columns": [_("q/q"), _("y/y")], "column_notes": [], "rows": rows,
            "note": _("A Macroscope calculation from INE's accounts: each part's volume growth times its share of nominal "
                      "GDP at the start of the period. INE publishes only the domestic and external totals; inventories are "
                      "what is left of INE's domestic-demand contribution after consumption and investment. Since 2015 the "
                      "parts add up to GDP growth within 0.03 points on average (a quarter of a point at most).")}


# ---------------------------------------------------------------- the income side
def labour_share_chart(data: Data) -> dict | None:
    comp, gos, gdp_n = _q(data, "compensation_employees"), _q(data, "operating_surplus"), _q(data, "gdp_nominal")
    taxes = _q(data, "net_taxes_production")
    if comp is None or gos is None or gdp_n is None or taxes is None:
        return None
    factor = gdp_n - taxes                       # GDP at factor cost: what is paid to labour and capital
    series = []
    for name, s in (("Labour (compensation of employees)", comp / factor * 100),
                    ("Capital and the self-employed (operating surplus and mixed income)", gos / factor * 100)):
        s = s.dropna()
        series.append({"name": name, "x": [d.strftime("%Y-%m-%d") for d in s.index], "y": s.round(2).tolist()})
    return localise({"id": "labour-share", "title": "Who earns the income: labour and capital",
                     "subtitle": "% of GDP at factor cost (GDP less taxes net of subsidies on production and imports)",
                     "kind": "line", "unit": "%", "decimals": 1, "freq": "Q", "ref_lines": [], "series": series,
                     "source": _("INE; Macroscope calculation")})


def income_facts(data: Data) -> list[dict]:
    comp, gos, gdp_n, taxes = (_q(data, i) for i in ("compensation_employees", "operating_surplus", "gdp_nominal", "net_taxes_production"))
    if any(s is None for s in (comp, gos, gdp_n, taxes)):
        return []
    share = (comp / (gdp_n - taxes) * 100).dropna()
    date = share.index[-1]
    before = share[share.index.year == 2019].mean()
    comp4 = comp.rolling(4).sum()
    return [{"label": _("Labour share of income"), "value": fmt_value(float(share.iloc[-1]), "%", 1),
             "sub": _("{quarter}; {then} on average in 2019").format(quarter=period_label(date, "Q"), then=fmt_value(float(before), "%", 1))},
            {"label": _("Compensation of employees"), "value": fmt_value(float(comp4.iloc[-1]) / 1000, "€ bn", 0),
             "sub": _("past four quarters, {change} on a year earlier").format(
                 change=fmt_change((float(comp4.iloc[-1]) / float(comp4.iloc[-5]) - 1) * 100, "%", 1))}]


# ---------------------------------------------------------------- productivity
def _index_2019(s: pd.Series) -> pd.Series:
    base = s[s.index.year == 2019].mean()
    return s / base * 100


def productivity_levels_chart(data: Data) -> dict | None:
    gdp, hours, jobs = _q(data, "gdp"), _q(data, "hours_cn"), _q(data, "jobs_fte")
    if gdp is None or hours is None or jobs is None:
        return None
    series = []
    for name, s in (("Output per hour worked", _index_2019(gdp / hours)), ("Output per full-time equivalent job", _index_2019(gdp / jobs)),
                    ("Hours worked", _index_2019(hours))):
        s = s.dropna()
        s = s[s.index >= "2008-01-01"]
        series.append({"name": name, "x": [d.strftime("%Y-%m-%d") for d in s.index], "y": s.round(2).tolist()})
    return localise({"id": "productivity-levels", "title": "Output per hour and per job",
                     "subtitle": "Real GDP per hour worked and per full-time equivalent job, and hours worked; 2019 = 100",
                     "kind": "line", "unit": "", "decimals": 1, "freq": "Q", "ref_lines": [{"y": 100, "label": "2019"}],
                     "series": series, "source": _("INE; Macroscope calculation")})


def growth_split_chart(data: Data) -> dict | None:
    """GDP growth on a year earlier split into hours worked and output per hour (log points, so they add up)."""
    gdp, hours = _q(data, "gdp"), _q(data, "hours_cn")
    if gdp is None or hours is None:
        return None
    lg = lambda s: (np.log(s / s.shift(4)) * 100).dropna()
    parts = {"Hours worked": lg(hours), "Output per hour": lg(gdp / hours)}
    total = lg(gdp)
    return _bars("growth-split", "Growth from more hours or from more output per hour",
                 "Real GDP growth on a year earlier, split in two (log points)", parts, total,
                 ["Hours worked", "Output per hour"])


def branch_productivity_chart(data: Data) -> dict | None:
    """Output per hour by branch: the past four quarters against 2019, %."""
    points, date = [], None
    for label, v, _n, h in BRANCHES:
        vol, hours = _q(data, v), _q(data, h)
        if vol is None or hours is None:
            continue
        ph = (vol / hours).dropna()
        base = ph[ph.index.year == 2019].mean()
        if pd.isna(base) or len(ph) < 4:
            continue
        points.append((label, (ph.iloc[-4:].mean() / base - 1) * 100))
        date = ph.index[-1]
    if len(points) < 2:
        return None
    points.sort(key=lambda p: p[1], reverse=True)
    spec = localise({"id": "productivity-branches", "title": "Output per hour by branch since 2019",
                     "subtitle": "Real gross value added per hour worked, past four quarters against 2019, % change",
                     "kind": "hbar", "x_kind": "category", "x_title": "Branch", "unit": "%", "decimals": 1, "freq": None,
                     "ref_lines": [], "source": _("INE; Macroscope calculation"),
                     "series": [{"name": "Output per hour", "x": [p[0] for p in points], "y": [round(p[1], 2) for p in points]}]})
    spec["subtitle"] = f"{spec['subtitle']} · {period_label(date, 'Q')}"
    return spec


def productivity_facts(data: Data) -> list[dict]:
    gdp, hours = _q(data, "gdp"), _q(data, "hours_cn")
    if gdp is None or hours is None:
        return []
    ph = _index_2019(gdp / hours).dropna()
    date = ph.index[-1]
    yoy = (ph.iloc[-1] / ph.iloc[-5] - 1) * 100
    since = ph[ph.index >= "2000-01-01"]
    years = (date - since.index[0]).days / 365.25
    trend = ((since.iloc[-1] / since.iloc[0]) ** (1 / years) - 1) * 100
    return [{"label": _("Output per hour worked"), "value": fmt_value(float(ph.iloc[-1]), "index", 1),
             "sub": _("2019 = 100 · {quarter}").format(quarter=period_label(date, "Q"))},
            {"label": _("On a year earlier"), "value": fmt_change(float(yoy), "%", 1), "sub": _("output per hour worked")},
            {"label": _("A year, since 2000"), "value": fmt_change(float(trend), "%", 1), "sub": _("average growth of output per hour")}]
