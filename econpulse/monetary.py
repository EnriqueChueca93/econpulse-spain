"""Money and credit on the Financial page (Batch 35): the monetary survey in the IMF's layout, and where broad money
growth comes from.

The survey balances by construction: broad money = net foreign assets + net claims on general government + claims on
the private sector and other financial corporations − the liabilities outside broad money (deposits and securities
excluded from it, equity, derivatives) − other items (net). So broad money growth over a year splits exactly into
each counterpart's change as a share of broad money a year earlier.
"""

import pandas as pd

from .charts import localise
from .i18n import _
from .snapshot import fmt_change, fmt_value, period_label
from .tables import Data

USES = ["ms_nfa", "ms_domestic_claims", "ms_net_claims_gg", "ms_claims_gg", "ms_gov_deposits", "ms_claims_private",
        "ms_loans_nfc", "ms_loans_households", "ms_broad_money", "ms_currency", "ms_transferable", "ms_other_deposits",
        "ms_securities_bm", "ms_deposits_xbm", "ms_securities_xbm", "ms_equity", "ms_derivatives", "ms_oin"]
START = "2015-01-01"


def _s(data: Data, ind_id: str) -> pd.Series | None:
    s = data.raw(ind_id)
    return None if s is None or s.dropna().empty else s.dropna()


def _yoy(s: pd.Series) -> pd.Series:
    return ((s / s.shift(12) - 1) * 100).dropna()


def sources(data: Data) -> dict[str, pd.Series] | None:
    """Each counterpart's contribution to broad money growth over 12 months, percentage points."""
    bm = _s(data, "ms_broad_money")
    parts = {k: _s(data, i) for k, i in (("nfa", "ms_nfa"), ("gg", "ms_net_claims_gg"), ("private", "ms_claims_private"),
                                         ("dx", "ms_deposits_xbm"), ("sx", "ms_securities_xbm"), ("eq", "ms_equity"),
                                         ("der", "ms_derivatives"), ("oin", "ms_oin"))}
    if bm is None or any(v is None for v in parts.values()):
        return None
    base = bm.shift(12)
    share = lambda s: ((s - s.shift(12)) / base * 100).dropna()
    longer = parts["dx"] + parts["sx"] + parts["eq"] + parts["der"] + parts["oin"]
    return {"Net foreign assets": share(parts["nfa"]), "Net claims on general government": share(parts["gg"]),
            "Claims on the private sector": share(parts["private"]),
            "Longer-term liabilities and other items": -share(longer)}


def sources_chart(data: Data) -> dict | None:
    parts, bm = sources(data), _s(data, "ms_broad_money")
    if not parts or bm is None:
        return None
    series = []
    for name, s in parts.items():
        s = s[s.index >= START]
        series.append({"name": name, "x": [d.strftime("%Y-%m-%d") for d in s.index], "y": s.round(3).tolist()})
    g = _yoy(bm)
    g = g[g.index >= START]
    series.append({"name": "Broad money", "kind": "line", "color": "ink", "x": [d.strftime("%Y-%m-%d") for d in g.index],
                   "y": g.round(3).tolist()})
    return localise({"id": "money-sources", "title": "Where broad money growth comes from",
                     "subtitle": "Contributions to broad money growth on a year earlier, percentage points",
                     "kind": "bar", "stack": True, "signed": True, "unit": "pp", "decimals": 1, "freq": "M",
                     "ref_lines": [], "series": series, "source": _("ECB; Banco de España; Macroscope calculation")})


def facts(data: Data) -> list[dict]:
    bm, private, nfa, gg = (_s(data, i) for i in ("ms_broad_money", "ms_claims_private", "ms_nfa", "ms_net_claims_gg"))
    if bm is None:
        return []
    out = [{"label": _("Broad money"), "value": fmt_value(float(bm.iloc[-1]), "€ bn", 0),
            "sub": _("{change} on a year earlier · {month}").format(change=fmt_change(float(_yoy(bm).iloc[-1]), "%", 1),
                                                                    month=period_label(bm.index[-1], "M"))}]
    for s, label in ((private, "Claims on the private sector"), (gg, "Net claims on general government")):
        if s is not None and len(s) > 12:
            out.append({"label": _(label), "value": fmt_change(float(_yoy(s).iloc[-1]), "%", 1),
                        "sub": _("on a year earlier · {month}").format(month=period_label(s.index[-1], "M"))})
    if nfa is not None:
        out.append({"label": _("Net foreign assets"), "value": fmt_value(float(nfa.iloc[-1]), "€ bn", 0),
                    "sub": _("claims on the rest of the world less liabilities to it · {month}").format(
                        month=period_label(nfa.index[-1], "M"))})
    return out
