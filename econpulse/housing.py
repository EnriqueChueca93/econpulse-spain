"""The Housing page's computed blocks: affordability and valuation (Batch 28a), and supply, credit,
wealth and commercial property (Batch 28b).

Affordability comes from the Banco de España's housing indicators (table si_1_5): what an average home
costs in years of household income, the share of income a new mortgage takes, prices per square metre and
rental yields. Valuation sets Spain against its comparators with the OECD's analytical house prices: real
prices, and the OECD's standardised price-to-income and price-to-rent ratios, each against the country's
own long-run average (= 100). Batch 28b adds the facts above the building, mortgage, wealth and commercial
property blocks, from the same Banco de España table.
"""

import pandas as pd

from . import peers, transforms
from .snapshot import fmt_change, fmt_value, period_label
from .tables import Data

COMPARATORS = [(s, label) for s, label in peers.COUNTRIES if s != "ea"]   # the OECD has no euro-area figures


def _latest(data: Data, ind_id: str) -> tuple[float, pd.Timestamp, str] | None:
    s = data.raw(ind_id)
    if s is None or s.dropna().empty:
        return None
    s = s.dropna()
    return float(s.iloc[-1]), s.index[-1], data.by_id[ind_id].freq


def _year_back(data: Data, ind_id: str) -> float | None:
    s = data.raw(ind_id)
    if s is None or s.dropna().empty:
        return None
    s = s.dropna()
    v = s.get(s.index[-1] - pd.DateOffset(years=1))
    return None if v is None or pd.isna(v) else float(v)


def affordability_facts(data: Data) -> list[dict]:
    out = []
    pi, effort = _latest(data, "house_price_income"), _latest(data, "mortgage_effort")
    if pi:
        avg = float(data.raw("house_price_income").dropna().mean())
        out.append({"label": "An average home costs", "value": f"{pi[0]:.1f} years",
                    "sub": f"of a household's gross income · {period_label(pi[1], pi[2])}; {avg:.1f} on average since 1987"})
    if effort:
        avg = float(data.raw("mortgage_effort").dropna().mean())
        out.append({"label": "A new mortgage takes", "value": fmt_value(effort[0], "%", 1),
                    "sub": f"of household income in the first year · {period_label(effort[1], effort[2])}; "
                           f"{fmt_value(avg, '%', 1)} on average"})
    for ind_id, label, source in (("price_m2_appraisal", "Price per m², appraisals", "Ministry of Housing"),
                                  ("price_m2_idealista", "Asking price per m²", "Idealista")):
        v = _latest(data, ind_id)
        before = _year_back(data, ind_id)
        if v:
            change = f", {fmt_change((v[0] / before - 1) * 100, '%', 1)} on a year" if before else ""
            out.append({"label": label, "value": f"€{v[0]:,.0f}",
                        "sub": f"{source} · {period_label(v[1], v[2])}{change}"})
    return out


def renting_facts(data: Data) -> list[dict]:
    out = []
    renters = _latest(data, "tenure_renters")
    if renters:
        owners = _latest(data, "tenure_owners")
        out.append({"label": "Households renting", "value": fmt_value(renters[0], "%", 1),
                    "sub": f"{renters[1].year}" + (f"; {fmt_value(owners[0], '%', 1)} own their home" if owners else "")})
    yld, bond = _latest(data, "rental_yield"), _latest(data, "es_10y_monthly")
    if yld:
        out.append({"label": "Gross rental yield", "value": fmt_value(yld[0], "%", 1),
                    "sub": f"a year's rent over the price · {period_label(yld[1], yld[2])}"
                           + (f"; 10-year bond {fmt_value(bond[0], '%', 1)}" if bond else "")})
    ret = _latest(data, "housing_return")
    if ret:
        out.append({"label": "Total return on housing", "value": fmt_value(ret[0], "%", 1),
                    "sub": f"rent plus the rise in price, over a year · {period_label(ret[1], ret[2])}"})
    return out


def _average_line(data: Data, ind_id: str, chart_id: str, title: str, subtitle: str, unit: str, decimals: int):
    """A ratio since its first figure, with its long-run average as a reference line."""
    s = data.raw(ind_id)
    if s is None or s.dropna().empty:
        return None
    s = s.dropna()
    avg = float(s.mean())
    return {"id": chart_id, "title": title, "subtitle": subtitle, "kind": "line", "unit": unit, "decimals": decimals,
            "freq": data.by_id[ind_id].freq, "source": "Banco de España",
            "ref_lines": [{"y": round(avg, 2), "label": f"Average {fmt_value(avg, unit, decimals).strip()}"}],
            "series": [{"name": title, "x": [d.strftime("%Y-%m-%d") for d in s.index], "y": s.round(3).tolist()}]}


def price_income_chart(data: Data) -> dict | None:
    return _average_line(data, "house_price_income", "price-income", "House prices and income",
                         "Years of a household's gross income an average home costs", "years", 1)


def effort_chart(data: Data) -> dict | None:
    return _average_line(data, "mortgage_effort", "mortgage-effort", "What a new mortgage takes",
                         "First-year payments, % of household gross income", "%", 1)


# ---------------------------------------------------------------- against the comparators (OECD)

def against_average(data: Data, measure: str, slug: str) -> tuple[float, pd.Timestamp] | None:
    """The OECD's standardised ratio (the country's long-run average = 100): its latest value and date."""
    s = data.raw(f"{measure}_{slug}")
    if s is None or s.dropna().empty:
        return None
    s = s.dropna()
    return float(s.iloc[-1]), s.index[-1]


def real_since_2015(data: Data, slug: str) -> tuple[float, pd.Timestamp] | None:
    s = data.raw(f"real_hpi_{slug}")
    if s is None or s.dropna().empty:
        return None
    s = s.dropna()
    base = s[s.index.year == 2015]
    return None if base.empty else (float(s.iloc[-1] / base.mean() * 100 - 100), s.index[-1])


def valuation_table(data: Data) -> dict | None:
    if against_average(data, "price_income", "es") is None:
        return None
    rows, dates = [], []
    for slug, label in COMPARATORS:
        yoy = None
        s = data.raw(f"real_hpi_{slug}")
        if s is not None and not s.dropna().empty:
            s = s.dropna()
            before = s.get(s.index[-1] - pd.DateOffset(years=1))
            yoy = None if before is None else (float(s.iloc[-1]) / float(before) - 1) * 100
            dates.append(s.index[-1])
        since = real_since_2015(data, slug)
        pi, pr = against_average(data, "price_income", slug), against_average(data, "price_rent", slug)
        cells = ["–" if yoy is None else fmt_change(yoy, "", 1).strip(),
                 "–" if since is None else fmt_change(since[0], "", 1).strip(),
                 "–" if pi is None else fmt_value(pi[0], "", 0).strip(),
                 "–" if pr is None else fmt_value(pr[0], "", 0).strip()]
        rows.append({"heading": False, "label": label, "label_es": "", "indent": 0, "period_note": "", "url": None,
                     "highlight": slug == "es", "cells": cells})
    common = pd.Series(dates).mode().max() if dates else None
    return {"title": "Country", "caption": "OECD analytical house prices" + (f" · {period_label(common, 'Q')}" if common is not None else ""),
            "through": period_label(common, "Q") if common is not None else "",
            "columns": ["Real prices, 1-yr %", "Real prices since 2015 %", "Price to income", "Price to rent"],
            "column_notes": ["", "", "100 = long-run average", "100 = long-run average"], "rows": rows,
            "note": ("Real prices are house prices deflated by consumer prices. The two ratios compare house prices with "
                     "disposable income per head and with rents, each against the country's own long-run average "
                     "(the OECD's standardised ratios): above 100, homes are dearer than usual against incomes or rents. "
                     "The OECD publishes no standardised ratios for Poland, and none against rents for the United States "
                     "after 2024; some countries' figures come a few quarters late.")}


def _valuation_ranking(data: Data, measure: str, chart_id: str, title: str, subtitle: str) -> dict | None:
    points = {slug: v for slug, _ in COMPARATORS if (v := against_average(data, measure, slug))}
    if "es" not in points:
        return None
    return peers._hbar(chart_id, title, subtitle, "", 0, points["es"][1], "Q",
                       [(peers.LABELS[s], v[0]) for s, v in points.items()], ref=100, ref_label="Long-run average",
                       source="OECD analytical house prices")


def price_income_ranking(data: Data) -> dict | None:
    return _valuation_ranking(data, "price_income", "price-income-peers", "House prices against incomes",
                              "Price-to-income ratio, 100 = the country's long-run average")


def price_rent_ranking(data: Data) -> dict | None:
    return _valuation_ranking(data, "price_rent", "price-rent-peers", "House prices against rents",
                              "Price-to-rent ratio, 100 = the country's long-run average")


# ---------------------------------------------------------------- supply, sales, credit and wealth (Batch 28b)

def _window(data: Data, ind_id: str, transform: str) -> pd.Series | None:
    """A series after a transform (e.g. its 12-month total), or None without data."""
    s = data.raw(ind_id)
    if s is None or s.dropna().empty:
        return None
    out = transforms.apply(transform, s.dropna(), data.by_id[ind_id].freq)
    return None if out.empty else out


def _thousands(v: float) -> str:
    """A count to the nearest thousand, e.g. 766,000."""
    return f"{round(v, -3):,.0f}"


def _peak(data: Data, ind_id: str) -> str:
    """'63.3% at the 2010 peak', for a series in %."""
    s = data.raw(ind_id).dropna()
    return f"{fmt_value(float(s.max()), '%', 1)} at the {s.idxmax().year} peak"


def supply_facts(data: Data) -> list[dict]:
    out = []
    starts = _window(data, "home_starts", "sum_1y")
    if starts is not None:
        share = _latest(data, "protected_share")
        out.append({"label": "Homes started", "value": f"{starts.iloc[-1]:,.0f}",
                    "sub": f"past 12 months · {period_label(starts.index[-1], 'M')}"
                           + (f"; {share[0]:.0f}% protected" if share else "")
                           + f"; {_thousands(starts.max())} at the {starts.idxmax().year} peak"})
    permits = _window(data, "home_permits", "sum_1y")
    if permits is not None:
        before = permits.get(permits.index[-1] - pd.DateOffset(years=1))
        change = f", {fmt_change((permits.iloc[-1] / before - 1) * 100, '%', 1)} on a year" if before else ""
        out.append({"label": "New homes in building permits", "value": f"{permits.iloc[-1]:,.0f}",
                    "sub": f"past 12 months · {period_label(permits.index[-1], 'M')}{change}"})
    new = _window(data, "households", "diff_yoy")
    if new is not None:
        total = float(data.raw("households").dropna().iloc[-1]) / 1000
        out.append({"label": "New households", "value": fmt_change(float(new.iloc[-1]) * 1000, "", 0).strip(),
                    "sub": f"over a year · {period_label(new.index[-1], 'Q')}; {total:.1f} million in all"})
    per = data.raw("homes_per_household")
    if per is not None and not per.dropna().empty:
        per = per.dropna()
        before = per[per.index.year == per.index[-1].year - 20]
        out.append({"label": "Homes per household", "value": f"{per.iloc[-1]:.2f}",
                    "sub": f"{per.index[-1].year} census"
                           + (f"; {before.iloc[-1]:.2f} in {before.index[-1].year}" if not before.empty else "")})
    return out


def credit_facts(data: Data) -> list[dict]:
    out = []
    ltv, over = _latest(data, "mortgage_ltv"), _latest(data, "mortgage_ltv80")
    if ltv:
        out.append({"label": "A new mortgage lends", "value": fmt_value(ltv[0], "%", 1),
                    "sub": f"of the home's price on average · {period_label(ltv[1], ltv[2])}"
                           + (f"; {fmt_value(over[0], '%', 1)} of mortgages lend more than 80%" if over else "")})
    term = _latest(data, "mortgage_term")
    if term:
        out.append({"label": "Average term", "value": f"{term[0]:.1f} years",
                    "sub": f"of new mortgages on homes · {period_label(term[1], term[2])}"})
    npl = _latest(data, "housing_npl")
    if npl:
        out.append({"label": "Housing loans gone bad", "value": fmt_value(npl[0], "%", 2),
                    "sub": f"non-performing · {period_label(npl[1], npl[2])}; {_peak(data, 'housing_npl')}"})
    debt = _latest(data, "housing_credit_gdp")
    if debt:
        out.append({"label": "Housing loans", "value": fmt_value(debt[0], "% of GDP", 1),
                    "sub": f"owed by households · {period_label(debt[1], debt[2])}; {_peak(data, 'housing_credit_gdp')}"})
    return out


def wealth_facts(data: Data) -> list[dict]:
    out = []
    homes, ratio = _latest(data, "housing_wealth"), _latest(data, "housing_wealth_income")
    if homes:
        sub = f"what households' homes are worth · {period_label(homes[1], homes[2])}"
        if ratio:
            s = data.raw("housing_wealth_income").dropna()
            sub += (f"; {ratio[0] / 100:.1f} times their disposable income "
                    f"({float(s.max()) / 100:.1f} at the {s.idxmax().year} peak)")
        out.append({"label": "Housing wealth", "value": f"€{homes[0] / 1000:.2f} trillion", "sub": sub})
    fin = _latest(data, "financial_wealth_income")
    if fin:
        s = data.raw("financial_wealth_income").dropna()
        high = f"; the highest since {s.index[0].year}" if fin[0] >= float(s.max()) else ""
        out.append({"label": "Net financial wealth", "value": f"{fin[0] / 100:.1f}×",
                    "sub": f"disposable income: savings and investments less debts · {period_label(fin[1], fin[2])}{high}"})
    return out


def commercial_facts(data: Data) -> list[dict]:
    out = []
    for ind_id, label in (("cpp_all", "Commercial property prices"), ("cpp_offices", "Offices"),
                          ("cpp_industrial", "Industrial buildings")):
        v, before = _latest(data, ind_id), _year_back(data, ind_id)
        if v and before:
            out.append({"label": label, "value": fmt_change((v[0] / before - 1) * 100, "%", 1),
                        "sub": f"on a year · {period_label(v[1], v[2])}; {v[0]:.1f} against 100 in 2014"})
    cre, homes = _latest(data, "bank_cre_share"), _latest(data, "bank_housing_share")
    if cre:
        out.append({"label": "Banks' loans for commercial property", "value": fmt_value(cre[0], "%", 1),
                    "sub": f"of their loans · {period_label(cre[1], cre[2])}"
                           + (f"; housing loans {fmt_value(homes[0], '%', 1)}" if homes else "")})
    return out
