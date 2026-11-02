"""Underlying inflation on the Inflation page: key figures, the latest month's distribution of
price changes across the HICP basket, and the items rising fastest and slowest.

The measures themselves are computed when fetching (sources/hicpdist.py) and stored like
any indicator; the latest month's distribution is kept in the weighted median's catalog entry.
"""

import re

import pandas as pd

from . import analytics
from .charts import localise
from .i18n import _
from .snapshot import fmt_value, period_label
from .tables import Data

MEASURE_IDS = ["hicp", "hicp_core", "hicp_wmedian", "hicp_trim10", "hicp_trim30", "hicp_share_above2",
               "hicp_share_above5", "hicp_wmedian_euro_area", "hicp_trim30_euro_area"]
_KIND = re.compile(r"\s+\((ND|SD|D|S)\)$")   # Eurostat marks items non-durable, semi-durable, durable or service


def _latest(data: Data, ind_id: str) -> tuple[float, pd.Timestamp] | None:
    s = data.raw(ind_id)
    if s is None or s.dropna().empty:
        return None
    s = s.dropna()
    return float(s.iloc[-1]), s.index[-1]


def _distribution(data: Data) -> dict | None:
    return data.store.load_catalog().get("hicp_wmedian", {}).get("distribution")


def item_name(label: str) -> str:
    return _KIND.sub("", label).strip()


def facts(data: Data) -> list[dict]:
    out = []
    median, trim, headline = _latest(data, "hicp_wmedian"), _latest(data, "hicp_trim30"), _latest(data, "hicp")
    if median is None:
        return out
    month = period_label(median[1], "M")
    if headline is not None and headline[1] == median[1]:
        out.append({"label": _("Headline HICP, {month}").format(month=month), "value": fmt_value(headline[0], "%", 1),
                    "sub": _("% change on a year earlier")})
    out.append({"label": _("Weighted median"), "value": fmt_value(median[0], "%", 1),
                "sub": _("half the basket is rising faster than this")})
    if trim is not None:
        out.append({"label": _("Trimmed mean, 30%"), "value": fmt_value(trim[0], "%", 1),
                    "sub": _("average without the 15% extremes at each end")})
    share = _latest(data, "hicp_share_above2")
    if share is not None:
        out.append({"label": _("Basket rising faster than 2%"), "value": fmt_value(share[0], "%", 0),
                    "sub": _("share of spending, by weight")})
    return out


def callout(data: Data) -> str | None:
    median, headline = _latest(data, "hicp_wmedian"), _latest(data, "hicp")
    if median is None or headline is None or median[1] != headline[1]:
        return None
    gap = headline[0] - median[0]
    if abs(gap) < 0.5:
        return _("Headline inflation ({headline}) is close to the weighted median ({median}): price rises are spread "
                 "fairly evenly across the basket.").format(headline=fmt_value(headline[0], '%', 1),
                                                            median=fmt_value(median[0], '%', 1))
    text = (_("Headline inflation ({headline}) is {gap} points above the weighted median ({median}): a few items rising "
              "very fast are moving the average more than the typical price change.") if gap > 0 else
            _("Headline inflation ({headline}) is {gap} points below the weighted median ({median}): a few items falling "
              "sharply are moving the average more than the typical price change."))
    return text.format(headline=fmt_value(headline[0], '%', 1), gap=f"{abs(gap):.1f}", median=fmt_value(median[0], '%', 1))


def distribution_chart(data: Data) -> dict | None:
    d = _distribution(data)
    if not d:
        return None
    month = period_label(pd.Timestamp(f"{d['month']}-01"), "M")
    spec = localise({"id": "inflation-spread", "title": "How price rises are spread across the basket",
                     "subtitle": "Share of the HICP basket, by weight, in each band of annual inflation (%)",
                     "kind": "bar", "x_kind": "category", "x_title": "Annual inflation, %", "unit": "%", "decimals": 1,
                     "freq": None, "ref_lines": [], "source": _("Eurostat; Macroscope calculation"),
                     "series": [{"name": "Share of the basket", "x": [b[0] for b in d["bands"]],
                                 "y": [b[1] for b in d["bands"]]}]})
    spec["subtitle"] = f"{spec['subtitle']}, {month}"
    return spec


def movers_table(data: Data) -> dict | None:
    d = _distribution(data)
    if not d or not d.get("highest"):
        return None
    month = period_label(pd.Timestamp(f"{d['month']}-01"), "M")

    def rows(items):
        return [{"heading": False, "label": _(item_name(name)), "label_es": "", "indent": 0, "period_note": "",
                 "url": None, "cells": [analytics._fmt_signed(rate, 1, "%"), f"{share:.1f}%"]}
                for name, rate, share in items]

    return {"title": _("Item"), "caption": _("Rising fastest and slowest · {month}").format(month=month), "through": month,
            "columns": [_("Annual rate"), _("Share of basket")],
            "rows": [{"heading": True, "label": _("Rising fastest")}, *rows(d["highest"]),
                     {"heading": True, "label": _("Rising slowest or falling")}, *rows(d["lowest"])],
            "note": _("Among the {items} detailed items with data, those with at least 0.2% of the basket. "
                      "Eurostat's item names.").format(items=d['items'])}
