"""Spain and its comparators, for the International page: France, Germany, Italy, Portugal, Poland, the
United Kingdom, the United States and Canada, with the euro area as the benchmark.

IDS says which series stands for each country on each measure (an indicator id, or (id, transform)).
Most measures go straight into the usual tables and rankings (pages.py); this module adds what needs a
calculation: real GDP against its level at the end of 2019, GDP per head at purchasing power relative to
Spain (the IMF's figure for last year), and where Spain ranks among the nine countries.
"""

import pandas as pd

from . import transforms
from .snapshot import fmt_change, fmt_value, period_label
from .sources.base import madrid_today
from .tables import Data, PanelRow

# (slug, label): Spain, the euro area as the benchmark, then the eight comparators.
COUNTRIES = [("es", "Spain"), ("ea", "Euro area"), ("fr", "France"), ("de", "Germany"), ("it", "Italy"),
             ("pt", "Portugal"), ("pl", "Poland"), ("uk", "United Kingdom"), ("us", "United States"),
             ("ca", "Canada")]
ECB = "ecb_deposit_rate"
_EU = ("fr", "de", "it", "pt", "pl")
IDS: dict[str, dict] = {
    "gdp": {"es": ("gdp", "yoy"), "ea": "gdp_growth_ea", **{s: f"gdp_growth_{s}" for s in _EU},
            "uk": "gdp_growth_uk", "us": "us_gdp_growth", "ca": "gdp_growth_ca"},
    "level": {"es": "gdp", "ea": "gdp_level_ea", **{s: f"gdp_level_{s}" for s in _EU + ("uk", "us", "ca")}},
    "ppp": {s: f"gdp_pc_ppp_{s}" for s, _ in COUNTRIES if s != "ea"},
    "hicp": {"es": "hicp", "ea": "hicp_euro_area", **{s: f"hicp_{s}" for s in _EU},
             "uk": "cpi_uk", "us": ("us_cpi_index", "yoy"), "ca": "cpi_ca"},
    "core": {"es": "hicp_core", "ea": "hicp_core_euro_area", **{s: f"hicp_core_{s}" for s in _EU},
             "uk": "core_cpi_uk", "us": ("us_core_cpi_index", "yoy")},
    "unemp": {"es": "unemployment_monthly", "ea": "unemployment_ea", **{s: f"unemployment_{s}" for s in _EU},
              "uk": "unemployment_uk", "us": "us_unemployment", "ca": "unemployment_ca"},
    "youth": {s: f"youth_unemp_{s}" for s, _ in COUNTRIES},
    "emp": {s: f"emp_rate_{s}" for s, _ in COUNTRIES},
    "y10": {"es": "es_10y_monthly", "de": "de_10y_monthly", **{s: f"bond10_{s}" for s in ("fr", "it", "pt", "pl")},
            "uk": "bond10_uk", "us": "us_10y", "ca": "bond10_ca"},
    "policy": {**{s: ECB for s in ("es", "ea", "fr", "de", "it", "pt")}, "pl": "policy_rate_pl",
               "uk": "policy_rate_uk", "us": "us_fed_funds", "ca": "policy_rate_ca"},
    "spread": {"es": "risk_premium_monthly", "fr": "spread10_fr", "it": "spread10_it", "pt": "spread10_pt"},
}
BASE = pd.Timestamp("2019-10-01")            # the last quarter before the pandemic
LABELS = dict(COUNTRIES)


def _ref(measure: str, slug: str) -> tuple[str, str] | None:
    ref = IDS[measure].get(slug)
    return None if ref is None else (ref if isinstance(ref, tuple) else (ref, "level"))


def indicator_ids() -> set[str]:
    return {_ref(m, s)[0] for m in IDS for s in IDS[m]}


def panel_rows(*measures: str) -> list[PanelRow]:
    """One row per country, with each measure's series; Spain highlighted."""
    return [PanelRow(label, {m: _ref(m, slug) for m in measures if slug in IDS[m]}, highlight=slug == "es")
            for slug, label in COUNTRIES]


def ranking_items(measure: str) -> list[tuple]:
    """The nine countries (not the euro area) for a ranking chart: (id, label, transform)."""
    return [(*_ref(measure, slug)[:1], label, _ref(measure, slug)[1]) for slug, label in COUNTRIES
            if slug != "ea" and slug in IDS[measure]]


def euro_area_ref(measure: str) -> list[tuple]:
    ref = _ref(measure, "ea")
    return [] if ref is None else [(ref[0], "Euro area", ref[1])]


def _latest(data: Data, measure: str, slug: str) -> tuple[float, pd.Timestamp, str] | None:
    ref = _ref(measure, slug)
    if ref is None or data.raw(ref[0]) is None:
        return None
    ind = data.by_id[ref[0]]
    s = transforms.apply(ref[1], data.raw(ref[0]).dropna(), ind.freq).dropna()
    return None if s.empty else (float(s.iloc[-1]), s.index[-1], ind.freq)


def since_2019(data: Data, slug: str) -> tuple[float, pd.Timestamp] | None:
    """Real GDP's latest level against the fourth quarter of 2019, % change."""
    ref = _ref("level", slug)
    s = data.raw(ref[0]) if ref else None
    if s is None:
        return None
    s = s.dropna()
    base = s.get(BASE)
    return None if base is None or not base else ((float(s.iloc[-1]) / float(base) - 1) * 100, s.index[-1])


def ppp_year() -> int:
    """The IMF's figures for last year: mostly outturns, where the current year's are projections."""
    return madrid_today().year - 1


def ppp(data: Data) -> dict[str, float]:
    """GDP per head at purchasing power in `ppp_year()`, international dollars, by country."""
    out = {}
    for slug in IDS["ppp"]:
        s = data.raw(IDS["ppp"][slug])
        if s is not None:
            v = s.get(pd.Timestamp(f"{ppp_year()}-01-01"))
            if v is not None and not pd.isna(v):
                out[slug] = float(v)
    return out


def _ordinal(n: int) -> str:
    return f"{n}{'th' if 10 <= n % 100 <= 20 else {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th')}"


def _rank_fact(label: str, values: dict[str, float], word: str, value: str, when: str) -> dict | None:
    """Spain's place among the countries with a value, from the top (`word`: "fastest", "highest")."""
    if "es" not in values or len(values) < 3:
        return None
    rank = 1 + sum(v > values["es"] for k, v in values.items() if k != "es")
    place = f"the {word}" if rank == 1 else f"{_ordinal(rank)} {word}"
    return {"label": label, "value": value, "sub": f"{place} of {len(values)} · {when}"}


def facts(data: Data) -> list[dict]:
    """Where Spain ranks among the nine countries on growth, the recovery since 2019, unemployment and inflation."""
    out = []
    for measure, label, word, unit in (("gdp", "GDP growth", "fastest", "%"), ("unemp", "Unemployment", "highest", "%"),
                                       ("hicp", "Inflation", "highest", "%")):
        latest = {slug: _latest(data, measure, slug) for slug, _ in COUNTRIES if slug != "ea"}
        latest = {k: v for k, v in latest.items() if v}
        if "es" in latest:
            v, date, freq = latest["es"]
            text = fmt_change(v, "%", 1) if measure == "gdp" else fmt_value(v, "%", 1)
            out.append(_rank_fact(label, {k: x[0] for k, x in latest.items()}, word, text,
                                  ("y/y, " if measure == "gdp" else "") + period_label(date, freq)))
    rec = {slug: r for slug, _ in COUNTRIES if slug != "ea" and (r := since_2019(data, slug))}
    if "es" in rec:
        out.insert(1, _rank_fact("GDP since the end of 2019", {k: r[0] for k, r in rec.items()}, "largest rise",
                                 fmt_change(rec["es"][0], "%", 1), period_label(rec["es"][1], "Q")))
    return [f for f in out if f]


def growth_table(data: Data) -> dict | None:
    """GDP growth, GDP against the end of 2019 and GDP per head at purchasing power, by country."""
    rows, dates = [], {}
    pp = ppp(data)
    for slug, label in COUNTRIES:
        g, rec = _latest(data, "gdp", slug), since_2019(data, slug)
        if g:
            dates[slug] = g[1]
        rows.append((slug, label, g, rec))
    if not dates:
        return None
    common = pd.Series(list(dates.values())).mode().max()

    def cell(v: float | None, date: pd.Timestamp | None, signed: bool = True):
        if v is None:
            return "–"
        text = (fmt_change(v, "%", 1) if signed else fmt_value(v, "", 1)).rstrip("%").strip()
        return {"value": text, "note": period_label(date, "Q")} if date is not None and date != common else text

    out = []
    for slug, label, g, rec in rows:
        out.append({"heading": False, "label": label, "label_es": "", "indent": 0, "period_note": "", "url": None,
                    "highlight": slug == "es",
                    "cells": [cell(g[0], g[1]) if g else "–", cell(rec[0], rec[1]) if rec else "–",
                              fmt_value(pp[slug], "", 0).strip() if slug in pp else "–",
                              fmt_value(pp[slug] / pp["es"] * 100, "", 0).strip() if slug in pp and "es" in pp else "–"]})
    return {"title": "Country", "caption": f"Real GDP and GDP per head · {period_label(common, 'Q')}",
            "through": period_label(common, "Q"),
            "columns": ["GDP growth, y/y %", "Against end-2019 %", f"GDP per head, PPP $ ({ppp_year()})", "Spain = 100"],
            "column_notes": [], "rows": out,
            "note": ("GDP growth compares the latest quarter with a year earlier; a period after a figure means it is "
                     "older than the others'. Against end-2019 compares real GDP with the fourth quarter of 2019, the "
                     "last before the pandemic. GDP per head at purchasing power (international dollars) is the IMF's "
                     f"World Economic Outlook figure for {ppp_year()}. Sources: INE, Eurostat, OECD, US BEA, IMF.")}


def _hbar(id_, title, subtitle, unit, decimals, date, freq, points, ref=None, source="") -> dict | None:
    if len(points) < 2:
        return None
    points = sorted(points, key=lambda p: p[1], reverse=True)
    return {"id": id_, "title": title, "kind": "hbar", "x_kind": "category", "x_title": "Country", "highlight": "Spain",
            "subtitle": f"{subtitle} · {period_label(date, freq)}", "unit": unit, "decimals": decimals,
            "series": [{"name": title, "x": [p[0] for p in points], "y": [round(p[1], 3) for p in points]}],
            "ref_lines": [{"y": round(ref, 3), "label": "Euro area"}] if ref is not None else [], "freq": None,
            "source": source}


def recovery_ranking(data: Data) -> dict | None:
    rec = {slug: r for slug, _ in COUNTRIES if (r := since_2019(data, slug))}
    if "es" not in rec:
        return None
    return _hbar("gdp-2019-ranking", "GDP against the end of 2019", "Real GDP, % change on the fourth quarter of 2019",
                 "%", 1, rec["es"][1], "Q", [(LABELS[s], r[0]) for s, r in rec.items() if s != "ea"],
                 rec["ea"][0] if "ea" in rec else None, "INE, Eurostat, OECD, US BEA")


def ppp_ranking(data: Data) -> dict | None:
    pp = ppp(data)
    if "es" not in pp:
        return None
    return _hbar("ppp-ranking", "GDP per head at purchasing power", f"Spain = 100, IMF figures for {ppp_year()}", "", 0,
                 pd.Timestamp(f"{ppp_year()}-01-01"), "A", [(LABELS[s], v / pp["es"] * 100) for s, v in pp.items()],
                 source="IMF World Economic Outlook")


def recovery_chart(data: Data) -> dict | None:
    """Real GDP since 2019, fourth quarter of 2019 = 100: Spain, the euro area and the United States."""
    series = []
    for slug in ("es", "ea", "us"):
        s = data.raw(IDS["level"][slug])
        base = s.get(BASE) if s is not None else None
        if base:
            s = (s.dropna() / float(base) * 100)
            s = s[s.index >= "2019-01-01"].round(2)
            series.append({"name": LABELS[slug], "x": [d.strftime("%Y-%m-%d") for d in s.index], "y": s.tolist()})
    if len(series) < 2:
        return None
    return {"id": "gdp-since-2019", "title": "Real GDP since 2019", "subtitle": "Fourth quarter of 2019 = 100",
            "kind": "line", "unit": "", "decimals": 1, "freq": "Q", "series": series,
            "ref_lines": [{"y": 100, "label": "Q4 2019"}], "source": "INE, Eurostat, OECD"}
