"""Recession signals on the Analysis page (Batch 36): the Sahm rule and the Michez rule, run on Spanish data.

Sahm rule (Claudia Sahm, 2019): the 3-month average of the unemployment rate less its lowest 3-month average over the
previous 12 months. At 0.5 percentage points a recession has likely started.

Michez rule (Pascal Michaillat and Emmanuel Saez, "Has the Recession Started?", Oxford Bulletin of Economics and
Statistics 87, 2025, pp. 1047-1058): the smaller of an unemployment indicator (the 3-month average less its low over the
past 12 months, this month included) and a vacancy indicator (the vacancy rate's high over the past 12 months less its
3-month average), the vacancy rate being job vacancies over the labour force. Requiring both to move makes the signal
less noisy than either. In the United States a recession is possible from 0.29pp and certain from 0.81pp, the lowest
threshold without a false alarm and the highest without a missed recession over 1960-2021; between them the probability
of a recession rises in a straight line.

Two adaptations for Spain, both said on the page:
- INE publishes vacancies once a quarter, so the Michez rule runs on quarters: a quarter's average stands for the
  3-month one, and the quarter with the four before it for the past 12 months. Vacancies and the labour force are
  seasonally adjusted by Macroscope (both are published unadjusted).
- Spain's vacancy rate is under 1% of the labour force, a fraction of the US one, so the vacancy indicator moves by
  tenths of the US one and the US thresholds can't be reached. The thresholds are set the way Michaillat and Saez set
  theirs, on Spain's recessions over 2003-2021. As unemployment in Spain has started rising before the official start
  of a recession, a signal up to a year before it counts as an early detection, not a false alarm, for both rules.

Recessions are those dated by the Spanish Economic Association's business cycle dating committee (AEE, CFCEE): from
the quarter after a peak to the trough, as Michaillat and Saez date US recessions from the NBER's peaks and troughs.
"""

import math

import pandas as pd

from . import i18n, seasonal
from .analytics import _cached, _months_between
from .charts import localise
from .i18n import _
from .snapshot import fmt_value, period_label
from .tables import DASH, Data

USES = ["unemployment_monthly", "vacancies", "vacancies_eurostat", "employment_epa", "unemployment_epa"]
# The AEE committee's peaks and troughs since 1980 (asesec.org/CFCweb): each recession from the quarter after the peak
# to the end of the trough quarter.
RECESSIONS = [("1992-04-01", "1993-09-30"), ("2008-07-01", "2009-12-31"), ("2011-01-01", "2013-06-30"),
              ("2020-01-01", "2020-06-30")]
SAHM_THRESHOLD = 0.5
US_THRESHOLDS = (0.29, 0.81)
LEAD_MONTHS = 12                      # a signal up to a year before a recession's start counts as detecting it
CALIBRATION_END = "2021-12-31"        # Spain's Michez thresholds are set on data to here, as the paper's US ones are
# INE's vacancies more than double from Q4 2009 to Q1 2010 (83,000 to 188,000) in the middle of a recession: a break
# in the survey, not a hiring boom. The vacancy indicator never compares quarters across it.
VACANCY_BREAK = pd.Timestamp("2010-01-01")
SAHM_START = "1987-01-01"


def _periods(a: pd.Timestamp, b: pd.Timestamp, freq: str) -> int:
    """Months (or quarters) from a to b, negative when b comes first."""
    months = _months_between(a, b)
    return months if freq == "M" else months // 3 if months >= 0 else -((-months) // 3)


# ---------------------------------------------------------------- the indicators

def sahm(data: Data) -> pd.Series | None:
    """Sahm's indicator, monthly, percentage points."""
    def compute():
        u = data.raw("unemployment_monthly")
        if u is None or u.dropna().empty:
            return None
        avg = u.dropna().rolling(3).mean()
        out = (avg - avg.shift(1).rolling(12).min()).dropna()
        return out[out.index >= SAHM_START]
    return _cached(data, "recession:sahm", compute)


def vacancy_rate(data: Data) -> pd.Series | None:
    """Job vacancies over the labour force, %, quarterly, seasonally adjusted by Macroscope. INE's own series where it
    has one (from 2013), Eurostat's copy of it before."""
    def compute():
        ine, eu, emp, ue = (data.raw(i) for i in ("vacancies", "vacancies_eurostat", "employment_epa", "unemployment_epa"))
        if eu is None or emp is None or ue is None:
            return None
        vac = eu.dropna()
        if ine is not None:
            vac = pd.concat([vac[vac.index < ine.dropna().index[0]], ine.dropna()])
        labour_force = (emp / (1 - ue / 100)).dropna()
        rate = (vac / labour_force * 100).dropna()
        try:      # each side of the break on its own, so the jump isn't read as seasonality
            parts = [seasonal.adjust(part, "Q", part.index[0]) for part in _segments(rate)]
        except ValueError:
            return None
        return pd.concat(parts)
    return _cached(data, "recession:vacancy_rate", compute)


def _segments(s: pd.Series) -> list[pd.Series]:
    """A vacancy series split at the 2010 break."""
    return [part for part in (s[s.index < VACANCY_BREAK], s[s.index >= VACANCY_BREAK]) if not part.empty]


def michez(data: Data) -> pd.DataFrame | None:
    """Quarterly: the unemployment indicator "u", the vacancy indicator "v" and the Michez indicator "x" = min(u, v),
    percentage points."""
    def compute():
        u, v = data.raw("unemployment_monthly"), vacancy_rate(data)
        if u is None or v is None:
            return None
        u = u.dropna()
        quarters = u.resample("QS")
        uq = quarters.mean()[quarters.count() == 3]
        # The vacancy rate's high over the past year, never reaching back across the 2010 break.
        high = pd.concat([part.rolling(5, min_periods=1).max() for part in _segments(v)])
        df = pd.concat([(uq - uq.rolling(5).min()).rename("u"), (high - v).rename("v")], axis=1, sort=True).dropna()
        df = df[df.index >= v.index[0] + pd.DateOffset(months=12)]     # a full year for the first high
        df["x"] = df[["u", "v"]].min(axis=1)
        return df
    return _cached(data, "recession:michez", compute)


# ---------------------------------------------------------------- signals and the track record

def _windows(freq: str) -> list[tuple[pd.Timestamp, pd.Timestamp, pd.Timestamp]]:
    """(earliest date a signal counts, start, end) for each recession, at the indicator's frequency."""
    out = []
    for start, end in RECESSIONS:
        s, e = pd.Timestamp(start), pd.Timestamp(end)
        if freq == "Q":
            e = e.to_period("Q").to_timestamp()
        out.append((s - pd.DateOffset(months=LEAD_MONTHS), s, e))
    return out


def signals(s: pd.Series, threshold: float) -> list[pd.Timestamp]:
    """Dates the indicator reaches the threshold after a year below it."""
    out = []
    for d, v in s.items():
        if v >= threshold:
            past = s[(s.index < d) & (s.index >= d - pd.DateOffset(months=12))]
            if len(past) and (past < threshold).all():
                out.append(d)
    return out


def track_record(s: pd.Series, threshold: float, freq: str, judge_recent: bool = False) -> dict:
    """For each recession the indicator covers: the signal that detected it and how many months (or quarters) from
    its start, or "on" (the indicator was still above the threshold from an earlier signal), or neither (missed). Then
    the false alarms, signals that no recession followed within a year, and the recent signals, from the data's last
    year, too soon to judge (unless `judge_recent`)."""
    found = signals(s, threshold)
    rows = []
    for first, start, end in _windows(freq):
        if s.index[0] > first:
            rows.append({"start": start, "end": end, "covered": False})
            continue
        hits = [d for d in found if first <= d <= end]
        row = {"start": start, "end": end, "covered": True, "signal": None, "lag": None, "on_since": None}
        if hits:
            row["signal"], row["lag"] = hits[0], _periods(start, hits[0], freq)
        elif s.asof(first) >= threshold:
            earlier = [d for d in found if d < first]
            row["on_since"] = earlier[-1] if earlier else first
        rows.append(row)
    in_window = lambda d: any(first <= d <= end for first, _start, end in _windows(freq))
    outside = [d for d in found if not in_window(d)]
    cutoff = s.index[-1] - pd.DateOffset(months=LEAD_MONTHS)
    recent = [] if judge_recent else [d for d in outside if d > cutoff]
    return {"recessions": rows, "false_alarms": [d for d in outside if d not in recent], "recent": recent}


def _detects_all(record: dict) -> bool:
    return all(r["signal"] is not None or r["on_since"] is not None for r in record["recessions"] if r["covered"])


def spain_thresholds(data: Data) -> tuple[float, float] | None:
    """The Michez thresholds for Spain, set as Michaillat and Saez set theirs, over 2003-2021, to the hundredth: the
    lowest threshold that gives no false alarm and still catches every recession (readings that stay high just after
    a recession are not new signals) and the highest that misses no recession (the lowest of the recessions' peaks)."""
    def compute():
        m = michez(data)
        if m is None:
            return None
        x = m["x"][m.index <= CALIBRATION_END]
        windows = [(first, end) for first, _start, end in _windows("Q") if first >= x.index[0]]
        if not windows:
            return None
        high = math.floor(min(x[(x.index >= first) & (x.index <= end)].max() for first, end in windows) * 100) / 100
        records = ((k / 100, track_record(x, k / 100, "Q", judge_recent=True)) for k in range(1, int(high * 100) + 1))
        low = next((t for t, r in records if not r["false_alarms"] and _detects_all(r)), None)
        return (low, high) if low is not None and high > low else None
    return _cached(data, "recession:thresholds", compute)


def probability(x: float, low: float, high: float) -> float:
    """Michaillat and Saez's recession probability: 0 below the low threshold, 1 above the high one, linear between."""
    return min(1.0, max(0.0, (x - low) / (high - low)))


# ---------------------------------------------------------------- what the page shows

def _bands(index: pd.DatetimeIndex) -> list[dict]:
    """Recessions as shaded bands on a date axis, those within the chart's dates only (a band stretches the axis)."""
    return [{"x0": start, "x1": end} for start, end in RECESSIONS if pd.Timestamp(end) >= index[0]]


def _pp(v: float) -> str:
    return fmt_value(v, "pp", 2)


def facts(data: Data) -> list[dict]:
    out = []
    s = sahm(data)
    if s is not None and not s.empty:
        out.append({"label": _("Sahm indicator"), "value": _pp(float(s.iloc[-1])),
                    "sub": _("recession signal at 0.5 · {month}").format(month=period_label(s.index[-1], "M"))})
    m, limits = michez(data), spain_thresholds(data)
    if m is not None and not m.empty and limits:
        x, q = float(m["x"].iloc[-1]), period_label(m.index[-1], "Q")
        out.append({"label": _("Michez indicator"), "value": _pp(x),
                    "sub": _("recession possible at {low}, certain at {high} (Spain) · {q}").format(
                        low=_pp(limits[0]), high=_pp(limits[1]), q=q)})
        out.append({"label": _("Recession probability (Michez)"), "value": f"{probability(x, *limits) * 100:.0f}%",
                    "sub": _("with Spain's thresholds · {q}").format(q=q)})
    v = vacancy_rate(data)
    if v is not None and not v.empty:
        out.append({"label": _("Vacancy rate"), "value": fmt_value(float(v.iloc[-1]), "%", 2),
                    "sub": _("job vacancies over the labour force · {q}").format(q=period_label(v.index[-1], "Q"))})
    return out


def _cell(row: dict, freq: str) -> list[str]:
    """A recession's signal and its distance from the start, for the track-record table."""
    if not row["covered"]:
        return [_("no data"), DASH]
    if row["signal"] is not None:
        lag = row["lag"]
        return [period_label(row["signal"], freq), f"+{lag}" if lag > 0 else fmt_value(lag, "index", 0) if lag else "0"]
    if row["on_since"] is not None:
        return [_("still on from {date}").format(date=period_label(row["on_since"], freq)), DASH]
    return [_("missed"), DASH]


def track_table(data: Data) -> dict | None:
    s, m, limits = sahm(data), michez(data), spain_thresholds(data)
    if s is None or m is None or not limits:
        return None
    sahm_rec, mich_rec = track_record(s, SAHM_THRESHOLD, "M"), track_record(m["x"], limits[0], "Q")
    rows = []
    for a, b in zip(sahm_rec["recessions"], mich_rec["recessions"]):
        label = "{start} – {end}".format(start=period_label(a["start"], "Q"), end=period_label(pd.Timestamp(a["end"]), "Q"))
        rows.append({"label": label, "indent": 0, "cells": _cell(a, "M") + _cell(b, "Q")})
    alarms = lambda dates, freq: ", ".join(period_label(d, freq) for d in dates) or _("none")
    rows.append({"label": _("False alarms"), "indent": 0,
                 "cells": [alarms(sahm_rec["false_alarms"], "M"), DASH, alarms(mich_rec["false_alarms"], "Q"), DASH]})
    if sahm_rec["recent"] or mich_rec["recent"]:
        rows.append({"label": _("Signals in the past year, too soon to judge"), "indent": 0,
                     "cells": [alarms(sahm_rec["recent"], "M"), DASH, alarms(mich_rec["recent"], "Q"), DASH]})
    return {"title": _("Recession (AEE dating)"),
            "caption": _("When each rule first signalled Spain's recessions since 1987, and how long after the start"),
            "columns": [_("Sahm rule"), _("Months from the start"), _("Michez rule (Spain)"), _("Quarters from the start")],
            "rows": rows, "through": "",
            "note": _("Recessions as dated by the Spanish Economic Association's dating committee, from the quarter "
                      "after the peak to the trough. A signal is the first month (or quarter) a rule reaches its "
                      "threshold after a year below it; a negative number means before the recession began. A signal "
                      "up to a year early counts as detecting the recession; one that no recession followed within a "
                      "year is a false alarm. The Michez rule needs vacancy data, which start in 2001, and its Spanish "
                      "thresholds are set so that it gives no false alarm over 2003-2021; from 2022 it is out of "
                      "sample.")}


def sahm_chart(data: Data) -> dict | None:
    s = sahm(data)
    if s is None or s.empty:
        return None
    rec = track_record(s, SAHM_THRESHOLD, "M")
    covered = [r for r in rec["recessions"] if r["covered"]]
    detected = sum(1 for r in covered if r["signal"] is not None)
    latest = float(s.iloc[-1])
    where = (_("The 3-month average unemployment rate was {v} points above its lowest of the previous 12 months in {month}")
             if latest >= 0 else
             _("The 3-month average unemployment rate was {v} points below its lowest of the previous 12 months in {month}"))
    reading = where.format(v=fmt_value(abs(latest), "index", 2), month=period_label(s.index[-1], "M")) + "; "
    reading += _("the rule says a recession has likely started at 0.5. Of Spain's {n} recessions since 1987 it "
                 "signalled {k} within a year before or during them.").format(n=len(covered), k=detected)
    on = [r for r in covered if r["signal"] is None and r["on_since"] is not None]
    if on:
        reading += " " + _("In {year} it was still on from the previous recession, as unemployment kept rising "
                           "between the two.").format(year=on[0]["start"].year)
    alarms = rec["false_alarms"]
    reading += " " + (i18n.ngettext("It gave {n} false alarm: {dates}.", "It gave {n} false alarms: {dates}.",
                                    len(alarms)).format(n=len(alarms), dates=", ".join(period_label(d, "M") for d in alarms))
                      if alarms else _("It gave no false alarms."))
    return localise({"id": "sahm-rule", "title": "The Sahm rule for Spain",
                     "subtitle": "3-month average unemployment rate less its low of the previous 12 months, percentage points; shaded: recessions",
                     "kind": "line", "unit": "pp", "decimals": 2, "freq": "M",
                     "ref_lines": [{"y": SAHM_THRESHOLD, "label": "Sahm threshold"}],
                     "bands": _bands(s.index), "series": [{"name": "Sahm indicator", "x": [d.strftime("%Y-%m-%d") for d in s.index],
                                                     "y": s.round(3).tolist()}],
                     "source": _("Eurostat; AEE; Macroscope calculation"), "reading": reading})


def michez_chart(data: Data) -> dict | None:
    m, limits = michez(data), spain_thresholds(data)
    if m is None or m.empty or not limits:
        return None
    last, x = m.iloc[-1], float(m["x"].iloc[-1])
    num = lambda v: fmt_value(float(v), "index", 2)
    reading = _("The smaller of two signals: unemployment's rise above its low of the past year ({u} points) and "
                "vacancies' fall below their high ({v} points), in {q}. Set the way Michaillat and Saez set theirs, "
                "Spain's thresholds say a recession is possible from {low} points and certain from {high}.").format(
        u=num(last["u"]), v=num(last["v"]), q=period_label(m.index[-1], "Q"), low=num(limits[0]), high=num(limits[1]))
    if x >= limits[0]:
        reading += " " + _("At {x}, the rule says a recession may have started, with a probability of {p}. Both moves "
                           "are small, a few hundredths of a point.").format(
            x=num(x), p=f"{probability(x, *limits) * 100:.0f}%")
        s = sahm(data)
        if s is not None and not s.empty and s.iloc[-1] < SAHM_THRESHOLD:
            reading += " " + _("The Sahm rule isn't signalling.")
    else:
        reading += " " + _("At {x}, below the lower threshold, it signals no recession.").format(x=num(x))
    reading += " " + _("With three recessions to learn from, these thresholds are rough. The US ones, 0.29 and 0.81, "
                       "can't be reached in Spain, where vacancies are a far smaller share of the labour force.")
    return localise({"id": "michez-rule", "title": "The Michez rule for Spain",
                     "subtitle": "The smaller of the unemployment and vacancy indicators, quarterly, percentage points; shaded: recessions",
                     "kind": "bar", "unit": "pp", "decimals": 2, "freq": "Q",
                     "ref_lines": [{"y": limits[0], "label": "Recession possible"},
                                   {"y": limits[1], "label": "Recession certain"}],
                     "bands": _bands(m.index), "series": [{"name": "Michez indicator", "x": [d.strftime("%Y-%m-%d") for d in m.index],
                                                     "y": m["x"].round(3).tolist()}],
                     "source": _("Eurostat; INE; AEE; Macroscope calculation"), "reading": reading})


def vacancy_chart(data: Data) -> dict | None:
    v = vacancy_rate(data)
    if v is None or v.empty:
        return None
    reading = _("The Michez rule's second input. Job vacancies were {v} of the labour force in {q}, against {low} at "
                "the lowest, in {low_q}. In the United States it was between about 4% and 7% from 2021 to 2024, so a "
                "fall in vacancies there moves the indicator by points and here by hundredths.").format(
        v=fmt_value(float(v.iloc[-1]), "%", 2), q=period_label(v.index[-1], "Q"), low=fmt_value(float(v.min()), "%", 2),
        low_q=period_label(v.idxmin(), "Q"))
    if v.index[0] < VACANCY_BREAK:
        reading += " " + _("INE's figures more than double from the end of 2009 to the start of 2010, a break in the "
                           "survey: the line stops there, and the rule never compares quarters across it.")
    # An empty point at the break, so the line doesn't join the two sides of it.
    x = [d.strftime("%Y-%m-%d") for d in v.index]
    y = [round(float(val), 4) for val in v]
    if v.index[0] < VACANCY_BREAK <= v.index[-1]:
        at = int((v.index < VACANCY_BREAK).sum())
        x.insert(at, (VACANCY_BREAK - pd.Timedelta(days=1)).strftime("%Y-%m-%d"))
        y.insert(at, None)
    return localise({"id": "vacancy-rate", "title": "Spain's vacancy rate",
                     "subtitle": "Job vacancies, % of the labour force, seasonally adjusted by Macroscope; shaded: recessions",
                     "kind": "line", "unit": "%", "decimals": 2, "freq": "Q", "ref_lines": [], "bands": _bands(v.index),
                     "series": [{"name": "Vacancy rate", "x": x, "y": y}],
                     "source": _("Eurostat; INE; Macroscope calculation"), "reading": reading})
