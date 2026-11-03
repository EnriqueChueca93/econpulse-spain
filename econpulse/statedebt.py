"""The State's debt, security by security (Batch 34b): what falls due each future year, and the stock by coupon.

From the Tesoro's list of Letras, Bonos and Obligaciones in circulation (econpulse/sources/tesoro.py), kept in
the catalog with the `state_debt_outstanding` series. On the Fiscal page beside the IMF-style debt tables and
on the Financial page beside Spain's government bonds.

- Repayments by year: principal is each security's amount falling due in its maturity year; interest is the
  coupons on the bonds still outstanding (Spanish bonds pay one coupon a year, on the maturity date's day and
  month). A run-off profile of today's debt: the debt the State will issue to refinance is not in it. Letras
  pay no coupon (they are sold at a discount), so their interest is not in the bars. Inflation-linked bonds
  are taken at today's indexed amount.
- The stock by coupon: one bubble per Bono or Obligación, its maturity across, its coupon up, its amount as
  the bubble's area.

The list is read from a web page, not a data feed, so each edition (the page's "Datos a" dates and amounts)
shows "awaiting AI check" until an AI has compared it with the Tesoro's page and recorded it with
`python -m econpulse confirm statedebt` (see the memory on scraped figures; forecasts.py has the same pattern).
"""

import hashlib
import json
from datetime import date, datetime

from . import i18n
from .charts import localise
from .i18n import _
from .snapshot import fmt_value
from .sources import tesoro
from .tables import Data

SERIES = "state_debt_outstanding"
USES = ["state_debt_outstanding", "state_debt_avg_coupon", "state_debt_avg_life"]
CHECKS = "statedebt_checks"          # data/statedebt_checks.json: the AI checks recorded
CHECKED, PENDING = "checked", "awaiting AI check"
SOURCE = "Tesoro Público"


def snapshot(data: Data) -> tuple[dict, date] | None:
    """The latest list and the day it was fetched (securities that matured since are left out from that day)."""
    snap = data.store.load_catalog().get(SERIES, {}).get("securities")
    s = data.raw(SERIES)
    if not snap or s is None or s.dropna().empty:
        return None
    return snap, s.dropna().index[-1].date()


def fingerprint(snap: dict) -> str:
    """One edition of the list: its dates and every security's amount."""
    body = json.dumps([snap["as_of"], sorted((x["isin"], x["amount"]) for x in snap["letras"] + snap["bonds"])])
    return hashlib.sha1(body.encode("utf-8")).hexdigest()[:12]


def check(data: Data) -> tuple[str, dict | None]:
    """(status, the AI check of this edition or None)."""
    got = snapshot(data)
    if not got:
        return PENDING, None
    record = data.store.load_json(CHECKS, {}).get("latest")
    if record and record.get("fingerprint") == fingerprint(got[0]):
        return CHECKED, record
    return PENDING, None


def confirm(store, by: str, note: str = "", against: str = "") -> dict:
    """Record that an AI compared the current list with the Tesoro's page."""
    snap = store.load_catalog().get(SERIES, {}).get("securities")
    if not snap:
        raise ValueError("no Tesoro list saved yet: run python -m econpulse fetch --only state_debt_outstanding")
    record = {"fingerprint": fingerprint(snap), "as_of": snap["as_of"], "checked_by": by,
              "checked_at": datetime.now().strftime("%Y-%m-%d"), "checked_against": against, "note": note}
    checks = store.load_json(CHECKS, {})
    store.save_json(CHECKS, {"latest": record, "history": (checks.get("history", []) + [record])[-50:]})
    return record


def _coupon_day(year: int, maturity: date) -> date:
    try:
        return maturity.replace(year=year)
    except ValueError:                      # 29 February in a year without one
        return date(year, 2, 28)


def repayments(snap: dict, on: date) -> dict[int, tuple[float, float]]:
    """{year: (principal, interest)} in € billion, from the rest of `on`'s year to the last maturity."""
    letras, bonds = tesoro.outstanding(snap, on)
    out: dict[int, list[float]] = {}
    for x in letras + bonds:
        out.setdefault(date.fromisoformat(x["maturity"]).year, [0.0, 0.0])[0] += x["amount"] / 1000
    for b in bonds:
        maturity = date.fromisoformat(b["maturity"])
        for year in range(on.year, maturity.year + 1):
            if on < _coupon_day(year, maturity) <= maturity:
                out.setdefault(year, [0.0, 0.0])[1] += b["coupon"] / 100 * b["amount"] / 1000
    first, last = on.year, max(out)
    return {y: tuple(out.get(y, (0.0, 0.0))) for y in range(first, last + 1)}


def _within(snap: dict, on: date, days: int) -> tuple[float, float]:
    """Principal and coupons falling due in the next `days` days, € billion."""
    letras, bonds = tesoro.outstanding(snap, on)
    end = date.fromordinal(on.toordinal() + days)
    principal = sum(x["amount"] for x in letras + bonds if date.fromisoformat(x["maturity"]) <= end) / 1000
    coupons = 0.0
    for b in bonds:
        maturity = date.fromisoformat(b["maturity"])
        for year in (on.year, on.year + 1):
            if on < _coupon_day(year, maturity) <= min(end, maturity):
                coupons += b["coupon"] / 100 * b["amount"] / 1000
    return principal, coupons


def facts(data: Data) -> list[dict]:
    got = snapshot(data)
    if not got:
        return []
    snap, on = got
    totals = tesoro.summary(snap, on)
    principal, coupons = _within(snap, on, 365)
    status, record = check(data)
    as_of = i18n.day_month_year(date.fromisoformat(snap["as_of"]["bonds"]))
    out = [
        {"label": _("Letras, Bonos and Obligaciones"), "value": fmt_value(totals["outstanding"], "€ bn", 1),
         "sub": _("outstanding; the Tesoro's list of {day}").format(day=as_of)},
        {"label": _("Due in the next 12 months"), "value": fmt_value(principal, "€ bn", 1),
         "sub": _("of principal, and {coupons} of coupons").format(coupons=fmt_value(coupons, "€ bn", 1))},
        {"label": _("Average coupon"), "value": fmt_value(totals["coupon"], "%", 2),
         "sub": _("Bonos and Obligaciones, weighted by amount")},
        {"label": _("Average life"), "value": _("{years} years").format(years=f"{totals['life']:.1f}"),
         "sub": _("to maturity, weighted by amount")},
    ]
    if status == CHECKED:
        out.append({"label": _("Data check"), "value": _("checked by AI"),
                    "sub": _("on {day}, against {what}").format(day=i18n.day_month_year(date.fromisoformat(record["checked_at"])),
                                                              what=_(record["checked_against"]) or _("the Tesoro's page"))})
    else:
        out.append({"label": _("Data check"), "value": _("awaiting AI check"),
                    "sub": _("read automatically from the Tesoro's web page; not yet compared with it by an AI")})
    return out


def repayments_chart(data: Data) -> dict | None:
    got = snapshot(data)
    if not got:
        return None
    snap, on = got
    years = repayments(snap, on)
    x = [f"{y}-01-01" for y in years]
    spec = localise({
        "id": "state-debt-repayments", "title": "The State's debt: what falls due each year",
        "subtitle": "€ billion on the Letras, Bonos and Obligaciones outstanding on {day}; {year}: the rest of the year",
        "kind": "bar", "stack": True, "unit": "€ bn", "decimals": 1, "freq": "A", "ref_lines": [],
        "series": [{"name": "Principal", "x": x, "y": [round(p, 3) for p, _i in years.values()]},
                   {"name": "Interest (coupons)", "x": x, "y": [round(i, 3) for _p, i in years.values()]}],
        "source": _("{source}; Macroscope calculation").format(source=SOURCE)})
    spec["subtitle"] = spec["subtitle"].format(day=i18n.day_month_year(on), year=on.year)
    return spec


def bonds_chart(data: Data) -> dict | None:
    got = snapshot(data)
    if not got:
        return None
    snap, on = got
    _letras, bonds = tesoro.outstanding(snap, on)
    groups = (("Ordinary", lambda b: not b["linked"] and not b["green"]), ("Inflation-linked", lambda b: b["linked"]),
              ("Green", lambda b: b["green"]))
    series = []
    for name, keep in groups:
        chosen = sorted((b for b in bonds if keep(b)), key=lambda b: b["maturity"])
        if chosen:
            series.append({"name": name, "x": [b["maturity"] for b in chosen], "y": [b["coupon"] for b in chosen],
                           "size": [round(b["amount"] / 1000, 2) for b in chosen], "text": [b["isin"] for b in chosen]})
    if not series:
        return None
    return localise({
        "id": "state-debt-coupons", "title": "The stock of debt by interest rate",
        "subtitle": "Each bubble is a Bono or Obligación: its maturity, its coupon and, by its size, the amount "
                    "outstanding; Letras pay no coupon",
        "kind": "bubble", "unit": "%", "decimals": 2, "freq": "D", "x_title": "Maturity date", "y_label": "Coupon",
        "size_label": "Amount outstanding", "size_unit": "€ bn", "ref_lines": [], "series": series,
        "source": _(SOURCE)})
