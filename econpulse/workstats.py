"""Hours, vacancies and pay by activity, and collective dismissals and temporary layoffs (Labour and Wages pages).

Hours worked per worker, job vacancies and wage cost per worker (in total, regular pay only, and per hour
worked) by CNAE-09 section come from INE's labour cost survey (ETCL, quarterly, not seasonally adjusted);
hours per person employed from the national
accounts; the workers affected by collective dismissals and temporary layoffs (ERE and ERTE) from the
Ministry of Labour (sources/reg.py).
"""

import pandas as pd

from . import transforms
from .charts import localise
from .i18n import _
from .snapshot import fmt_change, fmt_value, period_label
from .tables import Data, Heading, Row

# (slug, label): the indicator ids are hours_<slug>, vacancies_<slug> and pay_<slug>.
SECTIONS = [("mining", "Mining"), ("manufacturing", "Manufacturing"), ("energy", "Electricity and gas"),
            ("water", "Water and waste"), ("construction", "Construction"), ("trade", "Trade"),
            ("transport", "Transport and storage"), ("hospitality", "Hospitality"),
            ("information", "Information and IT"), ("finance", "Finance and insurance"),
            ("real_estate", "Real estate"), ("professional", "Professional services"),
            ("administrative", "Administrative services"), ("public_admin", "Public administration"),
            ("education", "Education"), ("health", "Health and social work"), ("arts", "Arts and recreation"),
            ("other_services", "Other services")]
# INE leaves out these sections' vacancies in many quarters.
NO_VACANCIES = {"mining", "energy", "water", "real_estate"}


def items(prefix: str, transform: str) -> list[tuple]:
    """Ranking items (indicator id, label, transform) for every section with this measure."""
    skip = NO_VACANCIES if prefix == "vacancies" else set()
    return [(f"{prefix}_{slug}", label, transform) for slug, label in SECTIONS if slug not in skip]


def rows(prefix: str, transform: str = "level") -> list[Row]:
    skip = NO_VACANCIES if prefix == "vacancies" else set()
    return [Row(f"{prefix}_{slug}", label, indent=1, transform=transform, flow=False)
            for slug, label in SECTIONS if slug not in skip]


def _avg(data: Data, ind_id: str):
    s = data.raw(ind_id)
    if s is None or s.dropna().empty:
        return None
    s = transforms.apply("avg_1y", s.dropna(), data.by_id[ind_id].freq).dropna()
    return s if not s.empty else None


def hours_callout(data: Data) -> str | None:
    """Hours lost to sick leave against 2019, and as a share of the hours worked."""
    sick, worked = _avg(data, "hours_sick"), _avg(data, "hours_etcl")
    if sick is None or worked is None:
        return None
    before = sick[sick.index.year == 2019]
    if before.empty or before.index[-1].month != 10:
        return None
    now, then = float(sick.iloc[-1]), float(before.iloc[-1])
    share = now / float(worked.get(sick.index[-1], float("nan"))) * 100
    text = _("Sick leave took {now} a month per employee in the four quarters to {quarter}, against {then} in 2019 "
             "({change})").format(now=fmt_value(now, 'hours', 1), quarter=period_label(sick.index[-1], 'Q'),
                                  then=fmt_value(then, 'hours', 1), change=fmt_change((now / then - 1) * 100, '%', 0))
    return text + (_(", the equivalent of {share} of the hours worked.").format(share=fmt_value(share, '%', 1))
                   if share == share else ".")


def _extremes(data: Data, prefix: str) -> tuple | None:
    """(lowest label, value), (highest label, value) and the date, on four-quarter averages."""
    latest = {}
    for slug, label in SECTIONS:
        s = _avg(data, f"{prefix}_{slug}")
        if s is not None:
            latest[label] = (float(s.iloc[-1]), s.index[-1])
    if len(latest) < 2:
        return None
    top = max(latest, key=lambda k: latest[k][0])
    low = min(latest, key=lambda k: latest[k][0])
    return (low, latest[low][0]), (top, latest[top][0]), latest[top][1]


def pay_callout(data: Data) -> str | None:
    """The best- and worst-paid sections, past four quarters, a month and an hour."""
    month = _extremes(data, "pay")
    if month is None:
        return None
    (low, lo), (top, hi), date = month
    text = _("In the four quarters to {quarter}, pay per worker ranged from {low_pay} a month in {low} to {high_pay} "
             "in {high}, {times} times as much.").format(
        quarter=period_label(date, 'Q'), low_pay=fmt_value(lo, '€', 0), low=_(low).lower(), high_pay=fmt_value(hi, '€', 0),
        high=_(top).lower(), times=f"{hi / lo:.1f}")
    hour = _extremes(data, "pay_hour")
    if hour is not None:
        (h_low, h_lo), (h_top, h_hi), _when = hour
        text += " " + _("Per hour worked the range is {low_pay} in {low} to {high_pay} in {high}, {times} times as much: "
                        "part-time work, more common in the lower-paid activities, explains a little of the monthly gap.").format(
            low_pay=fmt_value(h_lo, '€', 2), low=_(h_low).lower(), high_pay=fmt_value(h_hi, '€', 2), high=_(h_top).lower(),
            times=f"{h_hi / h_lo:.1f}")
    return text


# ---------------------------------------------------------------- pay by activity: levels, bonuses and growth
# Bonuses make pay seasonal (most workers get extra months' pay in June and December, and many firms
# pay annual bonuses early in the year), and their timing can shift from one quarter to another, so
# levels and growth are on averages of four quarters; the latest quarter alone is shown beside them.
PAY_ROWS = [("All activities", "wage_cost", "wage_cost_ordinary", "wage_cost_hour")] + [
    (label, f"pay_{slug}", f"pay_regular_{slug}", f"pay_hour_{slug}") for slug, label in SECTIONS]
PAY_USES = sorted({i for row in PAY_ROWS for i in row[1:]} | {"cpi_index"})
BASE_YEAR = 2019


def _year_back(s: pd.Series, date: pd.Timestamp) -> float | None:
    v = s.get(date - pd.DateOffset(years=1))
    return None if v is None or pd.isna(v) or v == 0 else float(v)


def _four(s: pd.Series, date: pd.Timestamp) -> pd.Series | None:
    """The four quarters to `date`, or None if any is missing."""
    part = s[(s.index > date - pd.DateOffset(years=1)) & (s.index <= date)].dropna()
    return part if len(part) == 4 else None


def _cpi_quarters(data: Data) -> pd.Series | None:
    cpi = data.raw("cpi_index")
    if cpi is None:
        return None
    cpi = cpi.dropna()
    grouped = cpi.groupby(cpi.index.to_period("Q"))
    q = grouped.mean()[grouped.count() == 3]
    q.index = q.index.to_timestamp()
    return q


def pay_measures(data: Data, total_id: str, regular_id: str, hour_id: str) -> dict | None:
    """Pay a month and an hour (four-quarter averages), the share from bonuses and extras, growth on a
    year (four-quarter averages and the latest quarter alone), and the change since 2019 after inflation."""
    total = data.raw(total_id)
    if total is None or total.dropna().empty:
        return None
    total = total.dropna()
    date = total.index[-1]
    last4 = _four(total, date)
    if last4 is None:
        return None
    avg = transforms.apply("avg_1y", total, "Q").dropna()
    out = {"date": date, "month": float(last4.mean()), "hour": None, "extra": None, "real": None,
           "growth": None, "quarter": None}
    if (before := _year_back(avg, date)) is not None:
        out["growth"] = (out["month"] / before - 1) * 100
    if (before := _year_back(total, date)) is not None:
        out["quarter"] = (float(total.iloc[-1]) / before - 1) * 100
    hour = data.raw(hour_id)
    if hour is not None and (h4 := _four(hour.dropna(), date)) is not None:
        out["hour"] = float(h4.mean())
    regular = data.raw(regular_id)
    if regular is not None and (r4 := _four(regular.dropna(), date)) is not None:
        out["extra"] = (1 - float(r4.sum()) / float(last4.sum())) * 100
    base = total[total.index.year == BASE_YEAR]
    cpi = _cpi_quarters(data)
    if len(base) == 4 and cpi is not None:
        cpi_base, cpi_now = cpi[cpi.index.year == BASE_YEAR], cpi.reindex(last4.index)
        if len(cpi_base) == 4 and cpi_now.notna().all():
            out["real"] = (out["month"] / float(base.mean())) / (float(cpi_now.mean()) / float(cpi_base.mean())) * 100 - 100
    return out


def _all_measures(data: Data) -> list[tuple[str, dict]]:
    return [(label, m) for label, *ids in PAY_ROWS if (m := pay_measures(data, *ids))]


def pay_table(data: Data) -> dict | None:
    measures = _all_measures(data)
    if not measures or measures[0][0] != "All activities":
        return None
    date = measures[0][1]["date"]
    num = lambda v, d=1: "–" if v is None else fmt_value(v, "", d).strip()
    pct = lambda v: "–" if v is None else fmt_change(v, "%", 1).rstrip("%")
    rows = []
    for k, (label, m) in enumerate(measures):
        if k == 1:
            rows.append({"heading": True, "label": _("By activity"), "cells": []})
        if m["date"] != date:
            continue
        rows.append({"heading": False, "label": _(label), "label_es": "", "indent": 0 if k == 0 else 1, "period_note": "",
                     "url": None, "highlight": False,
                     "cells": [num(m["month"], 0), num(m["hour"], 2), num(m["extra"]), pct(m["growth"]),
                               pct(m["quarter"]), pct(m["real"])]})
    return {"title": _("Activity"),
            "caption": _("€ and % · averages of the past four quarters · through {period}").format(period=period_label(date, 'Q')),
            "through": period_label(date, "Q"),
            "columns": [_(c) for c in ("€ a month", "€ an hour", "Bonuses and extras %", "y/y %", "Latest qtr y/y %")]
                       + [_("Since {year}, after inflation %").format(year=BASE_YEAR)],
            "column_notes": [], "rows": rows,
            "note": _("Wage cost per worker: gross pay before the worker's tax and contributions, for full-time and "
                      "part-time employees together. Bonuses and extras are the share of pay from bonuses, extra "
                      "months' pay and arrears. y/y compares the average of the past four quarters with the four before; "
                      "the latest quarter alone can swing with the timing of bonuses. The change since 2019 compares the "
                      "past four quarters with 2019, deflated by the CPI over the same quarters.")}


def _pay_ranking(id_, title, subtitle, unit, decimals, date, points, ref=None) -> dict | None:
    points = [p for p in points if p[1] is not None]
    if len(points) < 2:
        return None
    points.sort(key=lambda p: p[1], reverse=True)
    spec = localise({"id": id_, "title": title, "kind": "hbar", "x_kind": "category", "x_title": "Activity",
                     "subtitle": subtitle, "unit": unit, "decimals": decimals,
                     "series": [{"name": title, "x": [p[0] for p in points], "y": [round(p[1], 3) for p in points]}],
                     "ref_lines": [{"y": round(ref, 3), "label": "All"}] if ref is not None else [], "freq": None,
                     "source": "INE"})
    spec["subtitle"] = f"{spec['subtitle']} · {period_label(date, 'Q')}"
    return spec


def _ranking_of(data: Data, key: str, *args) -> dict | None:
    measures = _all_measures(data)
    if not measures or measures[0][0] != "All activities":
        return None
    first = measures[0][1]
    points = [(label, m[key]) for label, m in measures[1:] if m["date"] == first["date"]]
    return _pay_ranking(*args[:5], first["date"], points, first[key])


def extra_pay_chart(data: Data) -> dict | None:
    return _ranking_of(data, "extra", "pay-extra-ranking", "How much of pay is bonuses and extras",
                       "Bonuses, extra months' pay and arrears, % of pay over the past four quarters", "%", 1)


def pay_growth_chart(data: Data) -> dict | None:
    return _ranking_of(data, "growth", "pay-growth-ranking", "Pay growth by activity",
                       "Average of the past four quarters, % change on the four before", "%", 1)


def real_pay_chart(data: Data) -> dict | None:
    return _ranking_of(data, "real", "real-pay-ranking", _("Pay since {year}, after inflation").format(year=BASE_YEAR),
                       _("Past four quarters against {year}, deflated by the CPI, % change").format(year=BASE_YEAR), "%", 1)


def _swing(data: Data) -> tuple[str, str, dict] | None:
    """The activity whose latest quarter strays furthest from its four-quarter growth (at least 5 points)."""
    best = None
    for (label, *ids), slug in zip(PAY_ROWS[1:], (s for s, _ in SECTIONS)):
        m = pay_measures(data, *ids)
        if m and m["growth"] is not None and m["quarter"] is not None:
            gap = abs(m["quarter"] - m["growth"])
            if gap >= 5 and (best is None or gap > best[0]):
                best = (gap, slug, label, m)
    return None if best is None else best[1:]


def bonus_timing_chart(data: Data) -> dict | None:
    """All pay and regular pay quarter by quarter, for the activity whose latest quarter swings most."""
    swing = _swing(data)
    if swing is None:
        return None
    slug, label, _measures = swing
    total, regular = data.raw(f"pay_{slug}"), data.raw(f"pay_regular_{slug}")
    if total is None or regular is None:
        return None
    series = []
    for name, s in (("All pay", total), ("Regular pay", regular)):
        s = s.dropna()
        s = s[s.index >= f"{BASE_YEAR}-01-01"].round(0)
        series.append({"name": name, "x": [d.strftime("%Y-%m-%d") for d in s.index], "y": s.tolist()})
    spec = localise({"id": "pay-bonus-timing", "title": "",
                     "subtitle": "Wage cost per worker, € a month; the gap between the lines is bonuses, extra months' pay and arrears",
                     "kind": "line", "unit": "€", "decimals": 0, "freq": "Q", "ref_lines": [], "series": series, "source": "INE"})
    spec["title"] = _("{activity}: pay quarter by quarter").format(activity=_(label))
    return spec


def growth_facts(data: Data) -> list[dict]:
    measures = _all_measures(data)
    if not measures or measures[0][0] != "All activities":
        return []
    first = measures[0][1]
    quarter = period_label(first["date"], "Q")
    out = []
    if first["growth"] is not None:
        out.append({"label": _("Pay growth, all activities"), "value": fmt_change(first["growth"], "%", 1),
                    "sub": _("four quarters to {quarter} on the four before").format(quarter=quarter)})
    if first["real"] is not None:
        out.append({"label": _("Since {year}, after inflation").format(year=BASE_YEAR), "value": fmt_change(first["real"], "%", 1),
                    "sub": _("pay per worker against the CPI, all activities")})
    ranked = sorted(((label, m["growth"]) for label, m in measures[1:]
                     if m["date"] == first["date"] and m["growth"] is not None), key=lambda p: p[1])
    if len(ranked) >= 2:
        out += [{"label": _("Fastest rise"), "value": _(ranked[-1][0]),
                 "sub": _("{change} on a year").format(change=fmt_change(ranked[-1][1], '%', 1))},
                {"label": _("Slowest rise"), "value": _(ranked[0][0]),
                 "sub": _("{change} on a year").format(change=fmt_change(ranked[0][1], '%', 1))}]
    return out


def growth_callout(data: Data) -> str | None:
    """Why one activity's latest quarter looks out of line: usually the timing of bonuses."""
    swing = _swing(data)
    if swing is None:
        return None
    slug, label, m = swing
    total = data.raw(f"pay_{slug}").dropna()
    date = m["date"]
    prev = date - pd.DateOffset(months=3)
    vs = lambda v: (_("{change} higher") if v >= 0 else _("{change} lower")).format(change=fmt_value(abs(v), '%', 1))
    before = _year_back(total, prev) if prev in total.index else None
    if before is not None:
        when = _("{first} than a year earlier in {prev} and {second} in {quarter}").format(
            first=vs((float(total[prev]) / before - 1) * 100), prev=period_label(prev, 'Q'), second=vs(m['quarter']),
            quarter=period_label(date, 'Q'))
    else:
        when = _("{first} than a year earlier in {quarter}").format(first=vs(m['quarter']), quarter=period_label(date, 'Q'))
    text = (_("{activity} swings most from quarter to quarter: pay per worker was {when}, but the average of the past "
              "four quarters grew {change}.") if m['growth'] >= 0 else
            _("{activity} swings most from quarter to quarter: pay per worker was {when}, but the average of the past "
              "four quarters fell {change}.")).format(activity=_(label), when=when, change=fmt_value(abs(m['growth']), '%', 1))
    regular = data.raw(f"pay_regular_{slug}")
    if regular is not None and date in regular.index and (r_before := _year_back(regular.dropna(), date)) is not None:
        move = float(total.iloc[-1]) - _year_back(total, date)
        extra_move = move - (float(regular[date]) - r_before)
        if move and extra_move / move > 0.5:
            text += " " + _("Most of the swing is in bonuses and other extra payments, which came at a different time of "
                            "the year; the chart below shows them quarter by quarter.")
    return text


def ere_facts(data: Data) -> list[dict]:
    """Workers affected in the past 12 months, in total and by measure."""
    out = []
    for ind_id, label in (("ere_total", "Workers affected"), ("ere_dismissals", "Collective dismissals"),
                          ("ere_suspensions", "Contract suspensions"), ("ere_reductions", "Cuts in hours")):
        s = data.raw(ind_id)
        if s is None:
            continue
        total = transforms.apply("sum_1y", s.dropna(), "M").dropna()
        if total.empty:
            continue
        date = total.index[-1]
        year_ago = total.get(date.replace(year=date.year - 1))
        sub = _("12 months to {month}").format(month=period_label(date, 'M'))
        if year_ago:
            sub += ", " + _("{change} on a year earlier").format(
                change=fmt_change((float(total.iloc[-1]) / float(year_ago) - 1) * 100, '%', 0))
        out.append({"label": _(label), "value": fmt_value(float(total.iloc[-1]), "thousands", 1), "sub": sub})
    return out


VACANCY_ROWS = [Row("vacancies", "All vacancies", transform="avg_1y", flow=False), Heading("By activity"),
                *rows("vacancies", "avg_1y")]
