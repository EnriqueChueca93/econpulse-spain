"""The Fiscal Explorer for Spain (site/fiscal-explorer.html), after Econvitals' Fiscal Explorer.

Baseline: the European Commission's Debt Sustainability Monitor 2025 projection for Spain,
shown exactly to 2036, then extended to 2056 by Macroscope with the same debt equation,

    d(t) = d(t-1) x (1 + i) / (1 + g) - pb(t) + sfa(t)

(debt d and the primary balance pb in % of GDP, i the implicit interest rate on the debt,
g nominal GDP growth), on the Commission's own long-term assumptions: the primary balance
falls by the rise in ageing costs in the 2024 Ageing Report (pensions, health care, long-term
care, education), as in its no-policy-change baseline; nominal growth is the Ageing Report's
potential growth plus 2% inflation; and the implicit interest rate moves an eighth of the way
each year toward the Ageing Report's long-term market rate, as maturing debt is refinanced.

The levers and the goal-solver run in the browser (static/fiscal.js) on the same equation,
as changes from this baseline, so with every lever at zero the page shows the baseline exactly.
History: Eurostat since 1995 and, for debt, the Commission's series back to 1970.
"""

import json

from .config import PACKAGE_DIR
from .tables import Data

BASELINE_FILE = PACKAGE_DIR / "fiscal_baseline.json"   # written by scripts/extract_fiscal_baseline.py
END = 2070               # last projection year (the Ageing Report's horizon); the page starts at 2056
FIRST_LEVER_YEAR = 2027  # levers apply from this year, as in Econvitals' tool
MATURITY = 8             # years: an eighth of the debt is refinanced each year at the market rate
INFLATION = 2.0          # % a year, the GDP deflator after the Commission's horizon
AGEING = ("pensions", "health", "ltc", "education")

# History shown under "The Past": id -> (label, group). Revenue and spending in % of GDP.
HISTORY = [
    ("debt_annual", "Gross public debt", "Debt and balances"),
    ("deficit_annual", "Overall balance", "Debt and balances"),
    ("primary_balance", "Primary balance", "Debt and balances"),
    ("interest_annual", "Interest", "Debt and balances"),
    ("revenue_annual", "Total revenue", "Revenue"),
    ("taxes_production_annual", "Taxes on production and imports (VAT, excise)", "Revenue"),
    ("taxes_income_annual", "Taxes on income and wealth", "Revenue"),
    ("social_contributions_annual", "Social contributions", "Revenue"),
    ("spending_annual", "Total spending", "Spending"),
    ("social_benefits_annual", "Social benefits in cash", "Spending"),
    ("public_wages_annual", "Public employees' pay", "Spending"),
    ("public_investment_annual", "Public investment", "Spending"),
    ("spending_old_age_annual", "Old age (mostly pensions)", "Spending by function"),
    ("spending_health_annual", "Health", "Spending by function"),
    ("spending_education_annual", "Education", "Spending by function"),
]


def load(path=None) -> dict:
    return json.loads((path or BASELINE_FILE).read_text(encoding="utf-8"))


def _series(table: dict) -> dict[int, float]:
    return {int(y): float(v) for y, v in table.items() if v is not None}


def baseline(raw: dict) -> dict:
    """Yearly baseline, 2024 to END: the Commission's projection to 2036, then the extension."""
    b = {k: _series(v) for k, v in raw["dsm"]["baseline"].items()}
    ar = {k: _series(v) for k, v in raw["ageing_report"].items()}
    hist = _series(raw["dsm"]["history"])
    first, last = min(b["debt"]), max(b["debt"])
    ageing = {y: sum(ar[k][y] for k in AGEING) for y in ar["pensions"]}
    rows: dict[int, dict] = {}
    prev_debt = hist[first - 1]
    for y in range(first, last + 1):
        d = b["debt"][y]
        effects = b["growth_effect"][y] + b["inflation_effect"][y]
        x = -effects / prev_debt                      # g / (1 + g)
        g = x / (1 - x)
        real = -b["growth_effect"][y] * (1 + g) / prev_debt
        rows[y] = {"debt": d, "pb": b["primary_balance"][y], "interest": b["interest"][y],
                   "i": 100 * b["interest"][y] * (1 + g) / prev_debt, "g": 100 * g, "real": 100 * real,
                   "inflation": 100 * ((1 + g) / (1 + real) - 1), "sfa": b["stock_flow"][y],
                   "coa": b.get("cost_of_ageing", {}).get(y, 0.0), "source": "Commission"}
        prev_debt = d
    i, pb_last = rows[last]["i"], rows[last]["pb"]
    for y in range(last + 1, END + 1):
        real = ar["potential_growth"][y]
        g = (1 + real / 100) * (1 + INFLATION / 100) - 1
        i += (ar["interest_rate"][y] - i) / MATURITY
        pb = pb_last - (ageing[y] - ageing[last])
        d = prev_debt * (1 + i / 100) / (1 + g) - pb
        rows[y] = {"debt": d, "pb": pb, "interest": i * prev_debt / (100 * (1 + g)),
                   "i": i, "g": 100 * g, "real": real, "inflation": INFLATION, "sfa": 0.0,
                   "coa": rows[last]["coa"] + ageing[y] - ageing[last], "source": "Macroscope extension"}
        prev_debt = d
    for y, r in rows.items():
        r["balance"] = r["pb"] - r["interest"]
        for k in AGEING:
            r[k] = ar[k].get(y)
    return rows


def history(data: Data, raw: dict) -> dict:
    out = {}
    for ind_id, label, group in HISTORY:
        s = data.raw(ind_id)
        if s is None:
            continue
        values = {d.year: round(float(v), 2) for d, v in s.dropna().items()}
        if ind_id == "debt_annual":   # the Commission's series before Eurostat's starts
            for y, v in _series(raw["dsm"]["history"]).items():
                values.setdefault(y, round(v, 2))
        out[ind_id] = {"label": label, "group": group, "years": sorted(values), "values": [values[y] for y in sorted(values)]}
    return out


def gap(rows: dict, target: float, year: int, start: int = FIRST_LEVER_YEAR) -> float:
    """The permanent change in the primary balance from ``start`` that brings debt to ``target`` in ``year``."""
    def debt_in(adj):
        d = rows[start - 1]["debt"]
        for y in range(start, year + 1):
            r = rows[y]
            d = d * (1 + r["i"] / 100) / (1 + r["g"] / 100) - (r["pb"] + adj) + r["sfa"]
        return d
    lo, hi = -15.0, 25.0
    for _ in range(60):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if debt_in(mid) > target else (lo, mid)
    return hi


def past_groups(history_data: dict) -> list[tuple[str, list[tuple[str, str]]]]:
    groups: dict[str, list] = {}
    for ind_id, label, group in HISTORY:
        if ind_id in history_data:
            groups.setdefault(group, []).append((ind_id, label))
    return list(groups.items())


def explorer_data(data: Data, path=None) -> dict | None:
    if not (path or BASELINE_FILE).exists():
        return None
    raw = load(path)
    rows = baseline(raw)
    years = sorted(rows)
    keys = ["debt", "pb", "balance", "interest", "i", "g", "real", "inflation", "sfa", "coa", *AGEING]
    return {
        "years": years, "first_lever_year": FIRST_LEVER_YEAR, "maturity": MATURITY, "end": END,
        "last_commission_year": max(int(y) for y in raw["dsm"]["baseline"]["debt"]),
        "baseline": {k: [None if rows[y][k] is None else round(rows[y][k], 4) for y in years] for k in keys},
        "scenarios": {name: {int(y): v for y, v in path_.items()} for name, path_ in raw["dsm"]["scenarios"].items()},
        "percentiles": {p: {int(y): v for y, v in path_.items()} for p, path_ in raw["dsm"]["percentiles"].items()},
        "history": history(data, raw),
        "gaps": raw["dsm"].get("gaps", {}),
        "s1_check": gap(rows, 60.0, 2070),
        "sources": {"dsm": raw["dsm_source"], "ar": raw["ar_source"], "extracted": raw["extracted"]},
    }
