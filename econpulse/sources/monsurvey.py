"""The monetary survey for Spain (Batch 35a): the IMF's Depository Corporations Survey, rebuilt monthly.

The IMF publishes Spain's survey (dataset IMF.STA,MFS_DC, in the euro-area-wide residency presentation, where the
whole euro area counts as domestic), but its figures end in February 2025. Each line here is rebuilt from the ECB's
balance-sheet statistics of Spanish banks and other MFIs (BSI, sector A) and of the Banco de España (sector N),
with three Banco de España series where BSI lacks them (currency in circulation and banks' derivatives). Checked
against the IMF over 2015-01 to 2025-02 (122 months): within 0.2% on average for every line (0.5% at most for net
foreign assets), see PLAN.md, Batch 35a. Net claims on central government alone can't be rebuilt from public data,
so the survey shows net claims on general government, which matches the IMF's to the euro.

Keys are survey lines (LINES below); values are € billion, end of month.
"""

import threading

import pandas as pd

from . import bde, ecb
from .base import FetchResult, make_series

# [X] in the formulas = BSI/M.ES.N.X.Z01.E; "bde:" = Banco de España series (€ million unless noted).
FOREIGN = "A.AXG.A.1.U4.0000 + N.AXG.A.1.U4.0000 - A.LXG.A.1.U4.0000 - N.LXG.A.1.U4.0000"
CLAIMS_GG = "A.A20.A.1.U2.2100 + A.A30.A.1.U2.2100 + N.A20.A.1.U2.2100 + N.A30.A.1.U2.2100"
GOV_DEPOSITS = "A.L20.A.1.U2.2110 + N.L20.A.1.U2.2110"
CLAIMS_PRIVATE = ("A.A20.A.1.U2.2200 + A.A30.A.1.U2.2200 + A.A50.A.1.U2.2200 + N.A20.A.1.U2.2200 + N.A30.A.1.U2.2200"
                  " + bde:D_BEAD1000/1000")
CURRENCY = "bde:D_MESEFECTBIF"
TRANSFERABLE = "A.L21.A.1.U2.2300 + N.L20.A.1.U2.2300"
OTHER_DEPOSITS = ("A.L22.L.1.U2.2300 + A.L23.D.1.U2.2300 + A.L24.A.1.U2.2300 - A.L24.A.1.U2.2272"
                  " + A.L30.A.1.U2.0000")
SECURITIES_BM = "A.L40.F.1.U2.0000 + A.L40.G.1.U2.0000 - A.A30.F.1.U2.1000 - A.A30.G.1.U2.1000"
DEPOSITS_XBM = ("A.L22.A.1.U2.2300 - A.L22.L.1.U2.2300 + A.L23.A.1.U2.2300 - A.L23.D.1.U2.2300"
                " + A.L24.A.1.U2.2272")
SECURITIES_XBM = ("A.L40.A.1.U2.0000 - A.L40.F.1.U2.0000 - A.L40.G.1.U2.0000 - A.A30.A.1.U2.1000"
                  " + A.A30.F.1.U2.1000 + A.A30.G.1.U2.1000 - N.A30.A.1.U2.1000")
EQUITY = "A.L60.X.1.Z5.0000 + N.L60.X.1.Z5.0000"
DERIVATIVES = "bde:D_BEPD2000/1000"
LOANS_NFC = "A.A20.A.1.U2.2240"
LOANS_HOUSEHOLDS = "A.A20.A.1.U2.2250"

BASE = {"nfa": FOREIGN, "claims_gg": CLAIMS_GG, "gov_deposits": GOV_DEPOSITS, "claims_private": CLAIMS_PRIVATE,
        "currency": CURRENCY, "transferable": TRANSFERABLE, "other_deposits": OTHER_DEPOSITS,
        "securities_bm": SECURITIES_BM, "deposits_xbm": DEPOSITS_XBM, "securities_xbm": SECURITIES_XBM,
        "equity": EQUITY, "derivatives": DERIVATIVES, "loans_nfc": LOANS_NFC, "loans_households": LOANS_HOUSEHOLDS}
LINES = list(BASE) + ["net_claims_gg", "domestic_claims", "broad_money", "oin"]

_lock = threading.Lock()
_cache: dict = {}


def source_url(key: str, params: dict | None = None) -> str:
    return "https://data.ecb.europa.eu/data/datasets/BSI"


def _component(term: str) -> pd.Series:
    """One term of a formula, in € million: a BSI key, or a Banco de España series (with an optional /divisor)."""
    with _lock:
        if term in _cache:
            return _cache[term]
    if term.startswith("bde:"):
        code, _slash, div = term[4:].partition("/")
        s = bde.fetch(code).series / (float(div) if div else 1)
    else:
        s = ecb.fetch(f"BSI/M.ES.N.{term}.Z01.E").series
    s.index = s.index.to_period("M").to_timestamp()
    with _lock:
        _cache[term] = s
    return s


def evaluate(formula: str) -> pd.Series:
    """A formula of terms joined by + and -, in € million, over the months every term has."""
    total, sign = None, 1
    for token in formula.split():
        if token in "+-":
            sign = 1 if token == "+" else -1
            continue
        part = sign * _component(token)
        total = part if total is None else total.add(part, fill_value=None)
    return total.dropna()


def line(key: str) -> pd.Series:
    """A survey line in € million."""
    if key in BASE:
        return evaluate(BASE[key])
    if key == "net_claims_gg":
        return (line("claims_gg") - line("gov_deposits")).dropna()
    if key == "domestic_claims":
        return (line("net_claims_gg") + line("claims_private")).dropna()
    if key == "broad_money":
        return (line("currency") + line("transferable") + line("other_deposits") + line("securities_bm")).dropna()
    if key == "oin":   # other items (net): what balances the survey
        return (line("nfa") + line("domestic_claims") - line("broad_money") - line("deposits_xbm")
                - line("securities_xbm") - line("equity") - line("derivatives")).dropna()
    raise ValueError(f"unknown monetary survey line {key!r}")


def clear_cache() -> None:
    with _lock:
        _cache.clear()


def fetch(key: str, params: dict | None = None, **_) -> FetchResult:
    s = line(key) / 1000
    return FetchResult(make_series(s.index, s.values))
