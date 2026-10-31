"""ECB policy and what it means in Spain: the meeting calendar, rate decisions read
from the deposit rate, and the mortgage check on the Financial page.

The decision dates are the ECB's published schedule (the second day of each monetary
policy meeting, when the decision is announced), checked on 31 Oct 2026 at
https://www.ecb.europa.eu/press/calendars/mgcgc/html/index.en.html. Extend the list
when the ECB publishes later years; after the last date the page links to that calendar.
"""

import pandas as pd

from .snapshot import fmt_change, fmt_value
from .sources.base import madrid_today
from .tables import Data

ECB_CALENDAR_URL = "https://www.ecb.europa.eu/press/calendars/mgcgc/html/index.en.html"
ECB_DECISIONS = [pd.Timestamp(d) for d in (
    "2026-12-17",
    "2027-02-04", "2027-03-18", "2027-04-29", "2027-06-10", "2027-07-22", "2027-09-09", "2027-10-28", "2027-12-16",
    "2028-02-03", "2028-03-23", "2028-05-04", "2028-06-08", "2028-07-20", "2028-09-07", "2028-10-12", "2028-12-07",
)]

# A typical Spanish variable-rate mortgage, for the mortgage check.
MORTGAGE = {"principal": 150_000, "years": 25, "margin": 0.9}


def _day(d: pd.Timestamp) -> str:
    return f"{d.day} {d:%b %Y}"


def _today(today=None) -> pd.Timestamp:
    return pd.Timestamp(today or madrid_today()).normalize()


def next_decision(today: pd.Timestamp | None = None) -> pd.Timestamp | None:
    today = _today(today)
    return next((d for d in ECB_DECISIONS if d >= today), None)


def rate_changes(s: pd.Series) -> list[tuple[pd.Timestamp, float, float]]:
    """(date it took effect, new rate, change in bp) for every change, newest first."""
    s = s.dropna().sort_index()
    diff = s.diff()
    changed = diff[diff.abs() > 1e-9]
    return [(d, float(s[d]), float(diff[d]) * 100) for d in reversed(changed.index)]


def decisions_table(data: Data, n: int = 8) -> dict | None:
    s = data.raw("ecb_deposit_rate")
    if s is None:
        return None
    changes = rate_changes(s)[:n]
    if not changes:
        return None
    rows = [{"heading": False, "label": _day(d), "label_es": "", "indent": 0, "period_note": "", "url": None,
             "cells": [fmt_value(level, "%", 2), fmt_change(bp, "bp", 0)]} for d, level, bp in changes]
    latest = s.dropna().index[-1]
    return {
        "title": "Date it took effect",
        "caption": f"Recent changes in the deposit facility rate · through {_day(latest)}",
        "through": _day(latest),
        "columns": ["Deposit rate", "Change"],
        "rows": rows,
        "note": "New rates take effect a few days after the decision is announced (on the Wednesday after it, since 2024).",
    }


def ecb_facts(data: Data, today: pd.Timestamp | None = None) -> list[dict]:
    """The key-facts strip at the top of the ECB page."""
    facts = []
    dfr = data.raw("ecb_deposit_rate")
    if dfr is not None:
        dfr = dfr.dropna()
        facts.append({"label": "Deposit facility rate", "value": fmt_value(float(dfr.iloc[-1]), "%", 2),
                      "sub": _day(dfr.index[-1])})
        changes = rate_changes(dfr)
        if changes:
            d, _, bp = changes[0]
            facts.append({"label": "Last change", "value": fmt_change(bp, "bp", 0), "sub": f"took effect {_day(d)}"})
    today = _today(today)
    nxt = next_decision(today)
    if nxt is not None:
        days = (nxt - today).days
        facts.append({"label": "Next decision", "value": _day(nxt),
                      "sub": "today" if days == 0 else f"in {days} day{'s' if days != 1 else ''}"})
    else:
        facts.append({"label": "Next decision", "value": "See the ECB calendar", "sub": "", "url": ECB_CALENDAR_URL})
    estr = data.raw("estr")
    if estr is not None:
        estr = estr.dropna()
        facts.append({"label": "€STR, overnight", "value": fmt_value(float(estr.iloc[-1]), "%", 3), "sub": _day(estr.index[-1])})
    return facts


def monthly_payment(principal: float, annual_rate: float, years: int) -> float:
    """Monthly payment on a repayment (French) mortgage."""
    r, n = annual_rate / 100 / 12, years * 12
    return principal / n if r == 0 else principal * r / (1 - (1 + r) ** -n)


def mortgage_check(data: Data) -> str | None:
    """What a mortgage reset at this month's Euribor costs, against a year earlier."""
    s = data.raw("euribor_12m")
    if s is None:
        return None
    s = s.dropna()
    monthly = s.resample("MS").mean()
    month = monthly.index[-1]
    year_ago = monthly.get(month - pd.DateOffset(years=1))
    if year_ago is None or pd.isna(year_ago):
        return None
    now, then = float(monthly.iloc[-1]), float(year_ago)
    m = MORTGAGE
    pay_now = monthly_payment(m["principal"], now + m["margin"], m["years"])
    pay_then = monthly_payment(m["principal"], then + m["margin"], m["years"])
    diff = pay_now - pay_then
    partial = s.index[-1] < month + pd.offsets.BMonthEnd(0)  # before the month's last business day
    so_far = f" so far, to {s.index[-1].day} {s.index[-1]:%b}" if partial else ""
    change = "the same as" if abs(diff) < 0.5 else f"€{abs(diff):,.0f} {'more' if diff > 0 else 'less'} than"
    return (f"Mortgage check: a €{m['principal']:,}, {m['years']}-year variable-rate mortgage at Euribor + "
            f"{m['margin']} pp, reset at {month:%B}'s average 12-month Euribor ({now:.2f}%{so_far}), costs "
            f"€{pay_now:,.0f} a month: {change} a reset at the rate a year earlier ({then:.2f}%).")
