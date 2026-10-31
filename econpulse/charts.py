"""Chart specifications: what each chart shows, built from the store in Python.

The browser (static/charts.js) turns a spec into a Plotly chart using the page's
theme colors, so a spec carries data and wording only, never colors.

Spec fields: id, title, subtitle, kind ("line" | "bar"), unit, decimals,
date_format (d3 format for the hover date), series [{name, x, y}],
ref_lines [{y, label}], source, link.
"""

import pandas as pd

from . import transforms
from .registry import Indicator
from .sources import SOURCE_NAMES
from .store import Store

HOME_CHARTS = [
    {
        "id": "inflation",
        "title": "Inflation",
        "subtitle": "Harmonised index (HICP), % change on a year earlier",
        "kind": "line", "unit": "%", "decimals": 1, "start": "2019-01-01",
        "series": [("hicp", "level", "HICP"), ("hicp_core", "level", "Core HICP")],
        "ref_lines": [{"y": 2, "label": "2% target"}],
        "link": "inflation.html",
    },
    {
        "id": "yields",
        "title": "10-year government bond yields",
        "subtitle": "%, daily; the gap between the lines is the prima de riesgo",
        "kind": "line", "unit": "%", "decimals": 2, "start": "2022-01-01", "date_format": "%-d %b %Y",
        "series": [("es_10y", "level", "Spain"), ("de_10y", "level", "Germany")],
        "link": "financial.html",
    },
    {
        "id": "registrations",
        "title": "Social Security registrations",
        "subtitle": "Monthly change, thousands, seasonally adjusted by EconPulse",
        "kind": "bar", "unit": "k", "decimals": 1, "start": "2022-01-01",
        "series": [("afiliados", "sa_diff", "Monthly change")],
        "link": "labour.html",
    },
]


def build_chart(definition: dict, by_id: dict[str, Indicator], store: Store) -> dict | None:
    """One chart spec, or None if none of its series has data."""
    start = pd.Timestamp(definition["start"])
    series, sources = [], []
    for ind_id, transform, name in definition["series"]:
        raw = store.load_series(ind_id)
        if raw is None:
            continue
        ind = by_id[ind_id]
        s = transforms.apply(transform, raw, ind.freq)
        s = s[s.index >= start].round(4)
        series.append({"name": name, "x": [d.strftime("%Y-%m-%d") for d in s.index], "y": s.tolist()})
        sources.append(SOURCE_NAMES.get(ind.source, ind.source))
    if not series:
        return None
    spec = {k: v for k, v in definition.items() if k not in ("series", "start")}
    spec["series"] = series
    spec["source"] = "; ".join(dict.fromkeys(sources))
    return spec


def build_home_charts(indicators: list[Indicator], store: Store) -> list[dict]:
    by_id = {i.id: i for i in indicators}
    charts = (build_chart(c, by_id, store) for c in HOME_CHARTS)
    return [c for c in charts if c]
