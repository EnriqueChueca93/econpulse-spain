"""Spain and its comparators, for the International page: France, Germany, Italy, the Netherlands, Portugal,
Poland, the United Kingdom, the United States, Canada and Japan, with the euro area as the benchmark.

IDS says which series stands for each country on each measure (an indicator id, or (id, transform)).
Most measures go straight into the usual tables and rankings (pages.py); this module adds what needs a
calculation: real GDP against its level at the end of 2019, GDP per head at purchasing power relative to
Spain, the IMF's figures for a given year (the public finances, the current account, the outlook), and
where Spain ranks among the eleven countries.
"""

from datetime import date

import pandas as pd

from . import transforms
from .snapshot import fmt_change, fmt_value, period_label
from .sources.base import madrid_today
from .tables import Data, PanelRow

# (slug, label): Spain, the euro area as the benchmark, then the ten comparators.
COUNTRIES = [("es", "Spain"), ("ea", "Euro area"), ("fr", "France"), ("de", "Germany"), ("it", "Italy"),
             ("nl", "Netherlands"), ("pt", "Portugal"), ("pl", "Poland"), ("uk", "United Kingdom"),
             ("us", "United States"), ("ca", "Canada"), ("jp", "Japan")]
ECB = "ecb_deposit_rate"
_EU = ("fr", "de", "it", "nl", "pt", "pl")
_OTHERS = ("uk", "ca", "jp")
# The IMF's World Economic Outlook measures (weo_<measure>_<slug>, every country and the euro area).
WEO = ("growth", "inflation", "unemp", "deficit", "debt", "primary", "ca")
IDS: dict[str, dict] = {
    "gdp": {"es": ("gdp", "yoy"), "ea": "gdp_growth_ea", **{s: f"gdp_growth_{s}" for s in _EU + _OTHERS},
            "us": "us_gdp_growth"},
    "level": {"es": "gdp", "ea": "gdp_level_ea", **{s: f"gdp_level_{s}" for s in _EU + _OTHERS + ("us",)}},
    "ppp": {s: f"gdp_pc_ppp_{s}" for s, _ in COUNTRIES if s != "ea"},
    "hicp": {"es": "hicp", "ea": "hicp_euro_area", **{s: f"hicp_{s}" for s in _EU},
             **{s: f"cpi_{s}" for s in _OTHERS}, "us": ("us_cpi_index", "yoy")},
    "core": {"es": "hicp_core", "ea": "hicp_core_euro_area", **{s: f"hicp_core_{s}" for s in _EU},
             "uk": "core_cpi_uk", "us": ("us_core_cpi_index", "yoy")},
    "unemp": {"es": "unemployment_monthly", "ea": "unemployment_ea",
              **{s: f"unemployment_{s}" for s in _EU + _OTHERS}, "us": "us_unemployment"},
    "youth": {s: f"youth_unemp_{s}" for s, _ in COUNTRIES},
    "emp": {s: f"emp_rate_{s}" for s, _ in COUNTRIES},
    "y10": {"es": "es_10y_monthly", "de": "de_10y_monthly", **{s: f"bond10_{s}" for s in ("fr", "it", "nl", "pt", "pl")},
            **{s: f"bond10_{s}" for s in _OTHERS}, "us": "us_10y"},
    "policy": {**{s: ECB for s in ("es", "ea", "fr", "de", "it", "nl", "pt")}, "pl": "policy_rate_pl",
               **{s: f"policy_rate_{s}" for s in _OTHERS}, "us": "us_fed_funds"},
    "spread": {"es": "risk_premium_monthly", **{s: f"spread10_{s}" for s in ("fr", "it", "nl", "pt")}},
    **{f"weo_{m}": {s: f"weo_{m}_{s}" for s, _ in COUNTRIES} for m in WEO},
    # AMECO (annual): real compensation per employee and real GDP per person employed; no Canada (it stops in 2024)
    "real_pay": {s: f"real_pay_{s}" for s, _ in COUNTRIES if s != "ca"},
    "productivity": {s: f"productivity_{s}" for s, _ in COUNTRIES if s != "ca"},
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


# ---------------------------------------------------------------- the IMF's figures (Batch 27b)
# The World Economic Outlook gives each country's history, the IMF's estimate for the latest year and its
# projections, all in one series; the page picks years: last year (mostly outturns), this year and next.

def weo(data: Data, measure: str, slug: str, year: int) -> float | None:
    s = data.raw(IDS[f"weo_{measure}"].get(slug, ""))
    v = None if s is None else s.get(pd.Timestamp(f"{year}-01-01"))
    return None if v is None or pd.isna(v) else float(v)


def weo_last_year(data: Data) -> int | None:
    s = data.raw(IDS["weo_debt"]["es"])
    return None if s is None else int(s.dropna().index[-1].year)


def weo_edition(data: Data) -> str:
    """'October 2026' (the IMF publishes the WEO in April and October), from the date recorded at fetch."""
    published = data.store.load_catalog().get(IDS["weo_growth"]["es"], {}).get("published")
    return f"{date.fromisoformat(published):%B %Y}" if published else "the latest edition"


def _cells(values: list[float | None], signed: list[bool]) -> list[str]:
    return ["–" if v is None else (fmt_change(v, "", 1) if sign else fmt_value(v, "", 1)).strip()
            for v, sign in zip(values, signed)]


def _row(slug: str, label: str, cells: list[str]) -> dict:
    return {"heading": False, "label": label, "label_es": "", "indent": 0, "period_note": "", "url": None,
            "highlight": slug == "es", "cells": cells}


def interest(data: Data, slug: str, year: int) -> float | None:
    """Net interest paid (interest paid less interest received), % of GDP: the primary balance less the
    overall balance. Negative where a government earns more on its assets than it pays on its debt."""
    primary, overall = weo(data, "primary", slug, year), weo(data, "deficit", slug, year)
    return None if primary is None or overall is None else primary - overall


def finances_table(data: Data) -> dict | None:
    year, last = ppp_year(), weo_last_year(data)
    if last is None:
        return None
    rows = []
    for slug, label in COUNTRIES:
        debt, debt19 = weo(data, "debt", slug, year), weo(data, "debt", slug, 2019)
        values = [weo(data, "deficit", slug, year), weo(data, "primary", slug, year), interest(data, slug, year), debt,
                  None if debt is None or debt19 is None else debt - debt19, weo(data, "debt", slug, last)]
        rows.append(_row(slug, label, _cells(values, [True, True, False, False, True, False])))
    return {"title": "Country", "caption": f"% of GDP · IMF, {weo_edition(data)}", "through": str(year),
            "columns": [f"Budget balance {year}", f"Primary balance {year}", f"Net interest {year}", f"Debt {year}",
                        "Debt since 2019, pp", f"Debt {last} (projected)"],
            "column_notes": [], "rows": rows,
            "note": (f"General government, from the IMF's World Economic Outlook ({weo_edition(data)}): {year} is "
                     "mostly outturn, and the IMF's estimate where the year's accounts are not final. The budget "
                     "balance is net lending (a negative figure is a deficit); the primary balance leaves out interest, "
                     "so net interest (paid less received) is the gap between the two. Debt is gross debt; the last "
                     "column is the IMF's "
                     f"projection for {last}.")}


def outlook_table(data: Data) -> dict | None:
    year = madrid_today().year
    if weo(data, "growth", "es", year) is None:
        return None
    rows = []
    for slug, label in COUNTRIES:
        values = [weo(data, m, slug, y) for m in ("growth", "inflation", "unemp") for y in (year, year + 1)]
        rows.append(_row(slug, label, _cells(values, [True, True, False, False, False, False])))
    return {"title": "Country", "caption": f"% · IMF World Economic Outlook, {weo_edition(data)}", "through": str(year),
            "columns": [f"GDP growth {year}", str(year + 1), f"Inflation {year}", str(year + 1),
                        f"Unemployment {year}", str(year + 1)],
            "column_notes": [], "rows": rows,
            "note": ("The IMF's projections: real GDP growth and average consumer price inflation over the year, and the "
                     "unemployment rate on each country's own definition (so the levels compare less well than the "
                     "changes). The IMF updates them in April and October. The forecasters followed for Spain alone "
                     "are on the Analysis page.")}


def weo_ranking(data: Data, measure: str, year: int, id_, title, subtitle, unit="%", value=None,
                source: str | None = None) -> dict | None:
    """A ranking of the IMF's figure for one year (or of `value(slug)`), the euro area as a reference line."""
    get = value or (lambda slug: weo(data, measure, slug, year))
    points = {slug: v for slug, _ in COUNTRIES if (v := get(slug)) is not None}
    if "es" not in points:
        return None
    return _hbar(id_, title, subtitle, unit, 1, pd.Timestamp(f"{year}-01-01"), "A",
                 [(LABELS[s], v) for s, v in points.items() if s != "ea"], points.get("ea"),
                 source or f"IMF World Economic Outlook, {weo_edition(data)}")


def debt_ranking(data: Data) -> dict | None:
    return weo_ranking(data, "debt", ppp_year(), "debt-ranking", "Government debt", "Gross debt, % of GDP", "%")


def balance_ranking(data: Data) -> dict | None:
    return weo_ranking(data, "deficit", ppp_year(), "balance-ranking", "Budget balance",
                       "General government net lending, % of GDP (negative = deficit)", "%")


def interest_ranking(data: Data) -> dict | None:
    year = ppp_year()
    return weo_ranking(data, "", year, "interest-ranking", "Net interest paid by governments",
                       "Interest paid less interest received, % of GDP", "%",
                       value=lambda slug: interest(data, slug, year))


def current_account_ranking(data: Data) -> dict | None:
    return weo_ranking(data, "ca", ppp_year(), "current-account-ranking", "Current account",
                       "Balance with the rest of the world, % of GDP", "%")


def growth_outlook_ranking(data: Data) -> dict | None:
    year = madrid_today().year
    return weo_ranking(data, "growth", year, "growth-outlook-ranking", f"GDP growth in {year}",
                       "IMF projection, %", "%")


def growth_outlook_next(data: Data) -> dict | None:
    year = madrid_today().year + 1
    return weo_ranking(data, "growth", year, "growth-outlook-next", f"GDP growth in {year}",
                       "IMF projection, %", "%")


def outlook_facts(data: Data) -> list[dict]:
    """Where the IMF's projections put Spain among the eleven countries."""
    year = madrid_today().year
    out = []
    for measure, y, label, word in (("growth", year, f"Growth in {year}", "fastest"),
                                    ("growth", year + 1, f"Growth in {year + 1}", "fastest"),
                                    ("unemp", year + 1, f"Unemployment in {year + 1}", "highest"),
                                    ("debt", weo_last_year(data) or year, "Debt in {last}", "highest")):
        values = {slug: v for slug, _ in COUNTRIES if slug != "ea" and (v := weo(data, measure, slug, y)) is not None}
        if "es" in values:
            text = fmt_change(values["es"], "%", 1) if measure == "growth" else fmt_value(values["es"], "%", 1)
            fact = _rank_fact(label.format(last=y), values, word, text, f"IMF, {weo_edition(data)}")
            if measure == "debt" and fact:
                fact["value"] = f"{values['es']:.0f}% of GDP"
            out.append(fact)
    return [f for f in out if f]


# ---------------------------------------------------------------- pay and productivity (Batch 27b, AMECO)

def annual_change(data: Data, measure: str, slug: str, start: int, end: int) -> float | None:
    """% change of an annual series between two years."""
    s = data.raw(IDS[measure].get(slug, ""))
    if s is None:
        return None
    a, b = s.get(pd.Timestamp(f"{start}-01-01")), s.get(pd.Timestamp(f"{end}-01-01"))
    return None if a is None or b is None or pd.isna(a) or pd.isna(b) or not a else (float(b) / float(a) - 1) * 100


def pay_table(data: Data) -> dict | None:
    year = ppp_year()
    if annual_change(data, "real_pay", "es", 2019, year) is None:
        return None
    rows = []
    for slug, label in COUNTRIES:
        values = [annual_change(data, m, slug, a, year) for m in ("real_pay", "productivity") for a in (year - 1, 2019)]
        rows.append(_row(slug, label, _cells(values, [True] * 4)))
    return {"title": "Country", "caption": f"% change · European Commission (AMECO), {year}", "through": str(year),
            "columns": [f"Real pay, {year}", "Real pay since 2019", f"Productivity, {year}", "Productivity since 2019"],
            "column_notes": [], "rows": rows,
            "note": ("Real pay is compensation per employee (wages and employers' social contributions) deflated by "
                     "consumer prices; productivity is real GDP per person employed. Annual figures from the European "
                     f"Commission's AMECO database: {year} is partly the Commission's estimate. Not available for Canada, "
                     "whose AMECO figures stop in 2024.")}


def real_pay_ranking(data: Data) -> dict | None:
    year = ppp_year()
    return weo_ranking(data, "", year, "real-pay-peers", "Real pay since 2019",
                       "Compensation per employee after consumer prices, % change on 2019", "%",
                       value=lambda slug: annual_change(data, "real_pay", slug, 2019, year),
                       source="European Commission (AMECO)")


def productivity_ranking(data: Data) -> dict | None:
    year = ppp_year()
    return weo_ranking(data, "", year, "productivity-peers", "Productivity since 2019",
                       "Real GDP per person employed, % change on 2019", "%",
                       value=lambda slug: annual_change(data, "productivity", slug, 2019, year),
                       source="European Commission (AMECO)")
