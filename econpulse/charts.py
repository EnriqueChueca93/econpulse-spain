"""Chart specifications: what each chart shows, built from the store in Python.

The browser (static/charts.js) turns a spec into a Plotly chart using the page's
theme colors, so a spec carries data and wording only, never colors.

Spec fields: id, title, subtitle, kind ("line" | "bar"), unit, decimals,
date_format (d3 format for the hover date), series [{name, x, y, kind?, color?}],
ref_lines [{y, label}], stack (stacked bars), signed (show + on rises), freq
(the finest frequency among the series), source, link.

In a definition each series is (indicator id, transform, name) with an optional
fourth item of options: {"kind": "line"} to draw one series differently from the
chart, {"color": "ink"} for a total drawn in text colour rather than a palette slot.
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
        "kind": "bar", "signed": True, "unit": "k", "decimals": 1, "start": "2022-01-01",
        "series": [("afiliados", "sa_diff", "Monthly change")],
        "link": "labour.html",
    },
]


FREQ_ORDER = "DMQA"


def build_chart(definition: dict, by_id: dict[str, Indicator], store: Store) -> dict | None:
    """One chart spec, or None if none of its series has data."""
    start = pd.Timestamp(definition["start"])
    series, sources, freqs = [], [], []
    for ind_id, transform, name, *options in definition["series"]:
        raw = store.load_series(ind_id)
        if raw is None:
            continue
        ind = by_id[ind_id]
        try:
            s = transforms.apply(transform, raw, ind.freq)
        except ValueError:  # e.g. too little history to seasonally adjust
            continue
        s = s[s.index >= start].round(4)
        if s.empty:
            continue
        series.append({"name": name, "x": [d.strftime("%Y-%m-%d") for d in s.index], "y": s.tolist(),
                       **(options[0] if options else {})})
        sources.append(SOURCE_NAMES.get(ind.source, ind.source))
        freqs.append(ind.freq)
    if not series:
        return None
    spec = {k: v for k, v in definition.items() if k not in ("series", "start")}
    spec["series"] = series
    spec["freq"] = min(freqs, key=FREQ_ORDER.index)
    spec["source"] = "; ".join(dict.fromkeys(sources))
    return spec


def build_home_charts(indicators: list[Indicator], store: Store) -> list[dict]:
    by_id = {i.id: i for i in indicators}
    charts = (build_chart(c, by_id, store) for c in HOME_CHARTS)
    return [c for c in charts if c]
