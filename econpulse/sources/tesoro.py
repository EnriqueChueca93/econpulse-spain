"""Tesoro Público: the State's debt in circulation, security by security (Batch 34b).

The Tesoro's page "Valores en circulación" lists every Letra del Tesoro (ISIN, maturity, amount outstanding)
and every Bono and Obligación (ISIN with its type and coupon, maturity, amount outstanding; for inflation-linked
bonds also the indexation coefficient and the face value). Amounts are in € million; an issue's amount changes
on its auction settlement dates, and inflation-linked amounts are revalued at each month's end. The page has
no history, so each fetch keeps a summary as a dated point (the series below) and the full list in the
catalog (the meta of `state_debt_outstanding`), which econpulse/statedebt.py turns into the charts.
robots.txt allows the page; the Tesoro's legal notice allows reuse with the source cited.

Keys: "outstanding" (Letras, Bonos and Obligaciones, € bn), "coupon" (the bonds' average coupon, weighted by
amount, %), "life" (average years to maturity, weighted by amount). A summary point is dated the day of the
fetch; securities that matured between the page's "Datos a" date and that day are left out.
"""

import re
import threading
from datetime import date

from .. import http
from .base import FetchResult, madrid_today, make_series
from .webtables import read_tables

PAGE = "https://www.tesoro.es/deuda-publica/valores-del-tesoro/valores-en-circulacion"
_ISIN = re.compile(r"\b(ES[0-9A-Z]{10})\b")
_COUPON = re.compile(r"(\d+,\d+)")                # "1,30**"; ** marks collective action clauses, which older issues lack
_AS_OF = re.compile(r"Datos a (\d{2}/\d{2}/\d{4})")

_lock = threading.Lock()
_cache: dict = {}   # the page is read once per run, for all three series


def source_url(key: str, params: dict | None = None) -> str:
    return PAGE


def _number(text: str) -> float | None:
    """"28.677,5" -> 28677.5 (Spanish format: dot thousands, comma decimals)."""
    text = (text or "").strip().replace(".", "").replace(",", ".")
    try:
        return float(text)
    except ValueError:
        return None


def _day(text: str) -> date:
    d, m, y = (int(x) for x in text.strip().split("/"))
    return date(y, m, d)


def parse(page_html: str) -> dict:
    """{"letras": [...], "bonds": [...], "as_of": {"letras": iso, "bonds": iso}} from the page."""
    tables = [t for t in read_tables(page_html) if t and t[0] and t[0][0].startswith("Código ISIN")]
    if len(tables) != 2:
        raise ValueError(f"expected two tables (Letras; Bonos y Obligaciones) on the Tesoro page, found {len(tables)}")
    letras_rows, bond_rows = tables
    dates = _AS_OF.findall(page_html)
    if len(dates) < 2:
        raise ValueError("the Tesoro page's 'Datos a' dates were not found")
    letras = []
    for row in letras_rows[1:]:
        isin, amount = _ISIN.search(row[0]), _number(row[2])
        if not isin or amount is None:          # every listed security is read, or nothing is charted
            raise ValueError(f"a Letra on the Tesoro page could not be read: {row}")
        letras.append({"isin": isin.group(1), "maturity": _day(row[1]).isoformat(), "amount": amount})
    bonds = []
    for row in bond_rows[1:]:
        cell, isin, amount = row[0], _ISIN.search(row[0]), _number(row[2])
        rest = cell[isin.end():] if isin else ""
        coupon = _COUPON.search(rest)
        if not isin or amount is None or not coupon:
            raise ValueError(f"a bond on the Tesoro page could not be read: {row}")
        kind = "B" if re.search(r"\bB\b", rest) else "O"
        bonds.append({"isin": isin.group(1), "type": kind, "coupon": float(coupon.group(1).replace(",", ".")),
                      "maturity": _day(row[1]).isoformat(), "amount": amount,
                      "linked": "€i" in rest, "green": "(1)" in rest})
    check(letras, bonds)
    return {"letras": letras, "bonds": bonds,
            "as_of": {"letras": _day(dates[0]).isoformat(), "bonds": _day(dates[1]).isoformat()}}


def check(letras: list, bonds: list) -> None:
    """Refuse a page that reads wrong rather than chart it: enough securities, sane coupons and amounts."""
    if len(letras) < 5 or len(bonds) < 40:
        raise ValueError(f"too few securities read from the Tesoro page ({len(letras)} Letras, {len(bonds)} bonds)")
    if not all(0 <= b["coupon"] <= 10 for b in bonds):
        raise ValueError("a coupon outside 0-10% was read from the Tesoro page")
    total = sum(x["amount"] for x in letras + bonds)
    if not 800_000 <= total <= 3_000_000:
        raise ValueError(f"total outstanding of €{total:,.0f} million read from the Tesoro page is implausible")


def outstanding(snapshot: dict, on: date) -> tuple[list, list]:
    """The Letras and bonds still outstanding on a day (those that matured since the page's date left out)."""
    keep = lambda xs: [x for x in xs if date.fromisoformat(x["maturity"]) > on]
    return keep(snapshot["letras"]), keep(snapshot["bonds"])


def summary(snapshot: dict, on: date) -> dict:
    letras, bonds = outstanding(snapshot, on)
    total = sum(x["amount"] for x in letras + bonds)
    in_bonds = sum(b["amount"] for b in bonds)
    years = lambda x: (date.fromisoformat(x["maturity"]) - on).days / 365.25
    return {"outstanding": total / 1000,
            "coupon": sum(b["coupon"] * b["amount"] for b in bonds) / in_bonds,
            "life": sum(years(x) * x["amount"] for x in letras + bonds) / total}


def _snapshot() -> dict:
    with _lock:
        if "error" in _cache:
            raise _cache["error"]
        if "snapshot" not in _cache:
            try:
                _cache["snapshot"] = parse(http.get(PAGE).text)
            except Exception as e:
                _cache["error"] = e
                raise
        return _cache["snapshot"]


def clear_cache() -> None:
    with _lock:
        _cache.clear()


def fetch(key: str, params: dict | None = None, **_) -> FetchResult:
    if key not in ("outstanding", "coupon", "life"):
        raise ValueError(f"unknown Tesoro series {key!r}")
    snapshot, day = _snapshot(), madrid_today()
    value = summary(snapshot, day)[key]
    meta = {"securities": snapshot} if key == "outstanding" else {}
    return FetchResult(make_series([day], [value]), meta)
