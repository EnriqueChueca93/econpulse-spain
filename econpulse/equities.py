"""Equities on the Financial page (Batch 34c): the IBEX 35 and the Madrid exchange's six sector indices.

Daily closes from the Banco de España (table ti_1_6: Bolsa de Madrid and the CNMV), which publishes them one or
two trading days later; the site fetches twice a day, so these are the latest published closes, not live prices.
The heat map shows each sector's move over the last trading day, the past week and the year so far, as tiles
coloured on a diverging scale (rises blue, falls red, small moves grey). Company-level prices are not shown: no
free source allows them to be republished (see PLAN.md, Batch 34c).
"""

import pandas as pd

from . import i18n
from .charts import localise
from .i18n import _
from .snapshot import fmt_change, fmt_value
from .tables import Data

SECTORS = [("madrid_financials", "Financial services and real estate"), ("madrid_energy", "Oil and energy"),
           ("madrid_consumer_goods", "Consumer goods"), ("madrid_industry", "Basic materials, industry and construction"),
           ("madrid_consumer_services", "Consumer services"), ("madrid_tech", "Technology and telecommunications")]
INDICES = [("ibex35", "IBEX 35"), ("madrid_general", "Madrid general index")]
USES = [i for i, _label in INDICES + SECTORS]
# Colour steps for the tiles: a move smaller than the first bound is grey; beyond the last, the darkest step.
BOUNDS = {"day": [0.25, 1, 2], "week": [0.5, 2, 4], "ytd": [2, 8, 15]}


def _change(s: pd.Series, date: pd.Timestamp, back: str) -> float | None:
    """% change to `date` from the previous close ("day"), a week before ("week") or the last close of the
    previous year ("ytd")."""
    upto = s[s.index <= date]
    if len(upto) < 2:
        return None
    now = float(upto.iloc[-1])
    if back == "day":
        then = upto.iloc[-2]
    elif back == "week":
        then = upto.asof(date - pd.Timedelta(days=7))
    else:
        before = upto[upto.index.year < date.year]
        then = before.iloc[-1] if not before.empty else None
    if then is None or pd.isna(then) or then == 0:
        return None
    return (now / float(then) - 1) * 100


def facts(data: Data) -> list[dict]:
    s = data.raw("ibex35")
    if s is None or s.dropna().empty:
        return []
    s = s.dropna()
    date = s.index[-1]
    out = [{"label": _("IBEX 35"), "value": fmt_value(float(s.iloc[-1]), "index", 0),
            "sub": _("close of {day}").format(day=i18n.day_month_year(date))}]
    for back, label in (("day", "On the day"), ("week", "Over a week"), ("ytd", "This year")):
        v = _change(s, date, back)
        if v is not None:
            out.append({"label": _(label), "value": fmt_change(v, "%", 1), "sub": _("IBEX 35")})
    year_ago = s.asof(date - pd.DateOffset(years=1))
    if not pd.isna(year_ago):
        out.append({"label": _("Over a year"), "value": fmt_change((float(s.iloc[-1]) / float(year_ago) - 1) * 100, "%", 1),
                    "sub": _("IBEX 35")})
    return out


def heatmap(data: Data) -> dict | None:
    """The tiles: each sector's move to the latest close they all share, over three periods."""
    series = {i: s.dropna() for i, _label in SECTORS + INDICES if (s := data.raw(i)) is not None and not s.dropna().empty}
    sectors = [(i, label) for i, label in SECTORS if i in series]
    if len(sectors) < 2:
        return None
    date = min(series[i].index[-1] for i, _label in sectors)
    rows = []
    for i, label in INDICES + SECTORS:
        if i in series:
            rows.append({"label": label, "id": i, "index": i in dict(INDICES),
                         "level": round(float(series[i].asof(date)), 2),
                         "values": {back: (round(v, 2) if (v := _change(series[i], date, back)) is not None else None)
                                    for back in BOUNDS}})
    spec = localise({
        "id": "sector-heatmap", "title": "The Madrid exchange by sector",
        "subtitle": "% change to the close of {day}: rises in blue, falls in red",
        "kind": "tiles", "unit": "%", "decimals": 1, "freq": None, "ref_lines": [], "series": [],
        "rows": [{**r, "label": _(r["label"])} for r in rows],
        "periods": [{"key": "day", "label": _("Last trading day")}, {"key": "week", "label": _("Past week")},
                    {"key": "ytd", "label": _("Year to date")}],
        "bounds": BOUNDS, "source": _("Bolsa de Madrid and CNMV, via the Banco de España")})
    spec["subtitle"] = spec["subtitle"].format(day=i18n.day_month_year(date))
    return spec
