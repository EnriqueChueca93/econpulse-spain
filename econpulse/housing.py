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

from . import i18n, peers, transforms
from .charts import localise
from .i18n import _
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
        out.append({"label": _("An average home costs"), "value": fmt_value(pi[0], "years", 1),
                    "sub": _("of a household's gross income · {period}; {avg} on average since 1987").format(
                        period=period_label(pi[1], pi[2]), avg=f"{avg:.1f}")})
    if effort:
        avg = float(data.raw("mortgage_effort").dropna().mean())
        out.append({"label": _("A new mortgage takes"), "value": fmt_value(effort[0], "%", 1),
                    "sub": _("of household income in the first year · {period}; {avg} on average").format(
                        period=period_label(effort[1], effort[2]), avg=fmt_value(avg, '%', 1))})
    for ind_id, label, source in (("price_m2_appraisal", "Price per m², appraisals", "Ministry of Housing"),
                                  ("price_m2_idealista", "Asking price per m²", "Idealista")):
        v = _latest(data, ind_id)
        before = _year_back(data, ind_id)
        if v:
            period = period_label(v[1], v[2])
            sub = (_("{source} · {period}, {change} on a year").format(
                       source=_(source), period=period, change=fmt_change((v[0] / before - 1) * 100, '%', 1))
                   if before else f"{_(source)} · {period}")
            out.append({"label": _(label), "value": fmt_value(v[0], "€", 0), "sub": sub})
    return out


def renting_facts(data: Data) -> list[dict]:
    out = []
    renters = _latest(data, "tenure_renters")
    if renters:
        owners = _latest(data, "tenure_owners")
        out.append({"label": _("Households renting"), "value": fmt_value(renters[0], "%", 1),
                    "sub": _("{year}; {owners} own their home").format(year=renters[1].year,
                                                                         owners=fmt_value(owners[0], '%', 1))
                           if owners else f"{renters[1].year}"})
    yld, bond = _latest(data, "rental_yield"), _latest(data, "es_10y_monthly")
    if yld:
        period = period_label(yld[1], yld[2])
        out.append({"label": _("Gross rental yield"), "value": fmt_value(yld[0], "%", 1),
                    "sub": _("a year's rent over the price · {period}; 10-year bond {bond}").format(
                               period=period, bond=fmt_value(bond[0], '%', 1))
                           if bond else _("a year's rent over the price · {period}").format(period=period)})
    ret = _latest(data, "housing_return")
    if ret:
        out.append({"label": _("Total return on housing"), "value": fmt_value(ret[0], "%", 1),
                    "sub": _("rent plus the rise in price, over a year · {period}").format(
                        period=period_label(ret[1], ret[2]))})
    return out


def _average_line(data: Data, ind_id: str, chart_id: str, title: str, subtitle: str, unit: str, decimals: int):
    """A ratio since its first figure, with its long-run average as a reference line."""
    s = data.raw(ind_id)
    if s is None or s.dropna().empty:
        return None
    s = s.dropna()
    avg = float(s.mean())
    spec = localise({"id": chart_id, "title": title, "subtitle": subtitle, "kind": "line", "unit": unit,
                     "decimals": decimals, "freq": data.by_id[ind_id].freq, "source": "Banco de España", "ref_lines": [],
                     "series": [{"name": title, "x": [d.strftime("%Y-%m-%d") for d in s.index],
                                 "y": s.round(3).tolist()}]})
    # The average's label carries its figure, so it goes in after the words are put into the language.
    spec["ref_lines"] = [{"y": round(avg, 2),
                          "label": _("Average {value}").format(value=fmt_value(avg, unit, decimals).strip())}]
    return spec


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
        rows.append({"heading": False, "label": _(label), "label_es": "", "indent": 0, "period_note": "", "url": None,
                     "highlight": slug == "es", "cells": cells})
    common = pd.Series(dates).mode().max() if dates else None
    return {"title": _("Country"),
            "caption": (_("OECD analytical house prices · {period}").format(period=period_label(common, 'Q'))
                        if common is not None else _("OECD analytical house prices")),
            "through": period_label(common, "Q") if common is not None else "",
            "columns": [_(c) for c in ("Real prices, 1-yr %", "Real prices since 2015 %", "Price to income",
                                       "Price to rent")],
            "column_notes": ["", "", _("100 = long-run average"), _("100 = long-run average")], "rows": rows,
            "note": _("Real prices are house prices deflated by consumer prices. The two ratios compare house prices with "
                      "disposable income per head and with rents, each against the country's own long-run average "
                      "(the OECD's standardised ratios): above 100, homes are dearer than usual against incomes or rents. "
                      "The OECD publishes no standardised ratios for Poland, and none against rents for the United States "
                      "after 2024; some countries' figures come a few quarters late.")}


def _valuation_ranking(data: Data, measure: str, chart_id: str, title: str, subtitle: str) -> dict | None:
    points = {slug: v for slug, _label in COMPARATORS if (v := against_average(data, measure, slug))}
    if "es" not in points:
        return None
    spec = peers._hbar(chart_id, _(title), _(subtitle), "", 0, points["es"][1], "Q",
                       [(peers.LABELS[s], v[0]) for s, v in points.items()], ref=100, ref_label=_("Long-run average"),
                       source=_("OECD analytical house prices"))
    if spec is not None and spec.get("lang") != i18n.lang():
        # The words went in already in the language being written, and the subtitle ends with a date: put the
        # rest (axis title, country names) into the language, leaving the subtitle as it is.
        dated, spec["subtitle"] = spec["subtitle"], ""
        spec = localise(spec)
        spec["subtitle"] = dated
    return spec


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
    return _("{value} at the {year} peak").format(value=fmt_value(float(s.max()), '%', 1), year=s.idxmax().year)


def supply_facts(data: Data) -> list[dict]:
    out = []
    starts = _window(data, "home_starts", "sum_1y")
    if starts is not None:
        share = _latest(data, "protected_share")
        figures = {"period": period_label(starts.index[-1], 'M'), "peak": _thousands(starts.max()),
                   "year": starts.idxmax().year}
        out.append({"label": _("Homes started"), "value": f"{starts.iloc[-1]:,.0f}",
                    "sub": _("past 12 months · {period}; {share} protected; {peak} at the {year} peak").format(
                               share=f"{share[0]:.0f}%", **figures)
                           if share else _("past 12 months · {period}; {peak} at the {year} peak").format(**figures)})
    permits = _window(data, "home_permits", "sum_1y")
    if permits is not None:
        before = permits.get(permits.index[-1] - pd.DateOffset(years=1))
        period = period_label(permits.index[-1], 'M')
        out.append({"label": _("New homes in building permits"), "value": f"{permits.iloc[-1]:,.0f}",
                    "sub": _("past 12 months · {period}, {change} on a year").format(
                               period=period, change=fmt_change((permits.iloc[-1] / before - 1) * 100, '%', 1))
                           if before else _("past 12 months · {period}").format(period=period)})
    new = _window(data, "households", "diff_yoy")
    if new is not None:
        total = float(data.raw("households").dropna().iloc[-1]) / 1000
        out.append({"label": _("New households"), "value": fmt_change(float(new.iloc[-1]) * 1000, "", 0).strip(),
                    "sub": _("over a year · {period}; {total} million in all").format(
                        period=period_label(new.index[-1], 'Q'), total=f"{total:.1f}")})
    per = data.raw("homes_per_household")
    if per is not None and not per.dropna().empty:
        per = per.dropna()
        before = per[per.index.year == per.index[-1].year - 20]
        year = per.index[-1].year
        out.append({"label": _("Homes per household"), "value": f"{per.iloc[-1]:.2f}",
                    "sub": _("{year} census; {before} in {before_year}").format(
                               year=year, before=f"{before.iloc[-1]:.2f}", before_year=before.index[-1].year)
                           if not before.empty else _("{year} census").format(year=year)})
    return out


def credit_facts(data: Data) -> list[dict]:
    out = []
    ltv, over = _latest(data, "mortgage_ltv"), _latest(data, "mortgage_ltv80")
    if ltv:
        period = period_label(ltv[1], ltv[2])
        out.append({"label": _("A new mortgage lends"), "value": fmt_value(ltv[0], "%", 1),
                    "sub": _("of the home's price on average · {period}; {over} of mortgages lend more than 80%").format(
                               period=period, over=fmt_value(over[0], '%', 1))
                           if over else _("of the home's price on average · {period}").format(period=period)})
    term = _latest(data, "mortgage_term")
    if term:
        out.append({"label": _("Average term"), "value": fmt_value(term[0], "years", 1),
                    "sub": _("of new mortgages on homes · {period}").format(period=period_label(term[1], term[2]))})
    npl = _latest(data, "housing_npl")
    if npl:
        out.append({"label": _("Housing loans gone bad"), "value": fmt_value(npl[0], "%", 2),
                    "sub": _("non-performing · {period}; {peak}").format(period=period_label(npl[1], npl[2]),
                                                                         peak=_peak(data, 'housing_npl'))})
    debt = _latest(data, "housing_credit_gdp")
    if debt:
        out.append({"label": _("Housing loans"), "value": fmt_value(debt[0], "% of GDP", 1),
                    "sub": _("owed by households · {period}; {peak}").format(period=period_label(debt[1], debt[2]),
                                                                             peak=_peak(data, 'housing_credit_gdp'))})
    return out


def wealth_facts(data: Data) -> list[dict]:
    out = []
    homes, ratio = _latest(data, "housing_wealth"), _latest(data, "housing_wealth_income")
    if homes:
        period = period_label(homes[1], homes[2])
        if ratio:
            s = data.raw("housing_wealth_income").dropna()
            sub = _("what households' homes are worth · {period}; {times} times their disposable income "
                    "({peak} at the {year} peak)").format(period=period, times=f"{ratio[0] / 100:.1f}",
                                                         peak=f"{float(s.max()) / 100:.1f}", year=s.idxmax().year)
        else:
            sub = _("what households' homes are worth · {period}").format(period=period)
        out.append({"label": _("Housing wealth"),
                    "value": _("€{amount} trillion").format(amount=f"{homes[0] / 1000:.2f}"), "sub": sub})
    fin = _latest(data, "financial_wealth_income")
    if fin:
        s = data.raw("financial_wealth_income").dropna()
        period = period_label(fin[1], fin[2])
        sub = (_("disposable income: savings and investments less debts · {period}; the highest since {year}").format(
                   period=period, year=s.index[0].year)
               if fin[0] >= float(s.max()) else
               _("disposable income: savings and investments less debts · {period}").format(period=period))
        out.append({"label": _("Net financial wealth"), "value": f"{fin[0] / 100:.1f}×", "sub": sub})
    return out


def commercial_facts(data: Data) -> list[dict]:
    out = []
    for ind_id, label in (("cpp_all", "Commercial property prices"), ("cpp_offices", "Offices"),
                          ("cpp_industrial", "Industrial buildings")):
        v, before = _latest(data, ind_id), _year_back(data, ind_id)
        if v and before:
            out.append({"label": _(label), "value": fmt_change((v[0] / before - 1) * 100, "%", 1),
                        "sub": _("on a year · {period}; {index} against 100 in 2014").format(
                            period=period_label(v[1], v[2]), index=f"{v[0]:.1f}")})
    cre, homes = _latest(data, "bank_cre_share"), _latest(data, "bank_housing_share")
    if cre:
        period = period_label(cre[1], cre[2])
        out.append({"label": _("Banks' loans for commercial property"), "value": fmt_value(cre[0], "%", 1),
                    "sub": _("of their loans · {period}; housing loans {homes}").format(
                               period=period, homes=fmt_value(homes[0], '%', 1))
                           if homes else _("of their loans · {period}").format(period=period)})
    return out
