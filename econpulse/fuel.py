"""Petrol and diesel at the pump (Batch 32b): the facts above the Inflation page's energy charts.

The prices are the European Commission's Weekly Oil Bulletin (econpulse/sources/oilbulletin.py): each
Monday's average in Spain and the euro area, with and before duties and taxes, in euros per litre.
"""

import pandas as pd

from .snapshot import MINUS, period_label
from .tables import Data

FUELS = (("petrol", "Petrol (Euro-super 95)"), ("diesel", "Diesel"))


def _signed(v: float, decimals: int = 1) -> str:
    text = f"{abs(v):.{decimals}f}"
    if float(text) == 0:
        return text
    return ("+" if v > 0 else MINUS) + text


def facts(data: Data) -> list[dict]:
    out, latest = [], {}
    for fuel, label in FUELS:
        s = data.raw(f"{fuel}_price")
        if s is None:
            continue
        s = s.dropna()
        date, value = s.index[-1], float(s.iloc[-1])
        latest[fuel] = (date, value)
        year_ago = s.asof(date - pd.DateOffset(years=1))
        sub = "" if pd.isna(year_ago) else f"{_signed((value / year_ago - 1) * 100)}% on a year earlier"
        out.append({"label": f"{label}, {period_label(date, 'D')}", "value": f"€{value:.3f} a litre", "sub": sub})

    def at(ind_id: str, date: pd.Timestamp) -> float | None:
        s = data.raw(ind_id)
        if s is None:
            return None
        v = s.dropna().get(date)
        return None if v is None or pd.isna(v) else float(v)

    taxes = {f: 1 - pretax / value for f, (date, value) in latest.items() if (pretax := at(f"{f}_price_pretax", date))}
    if "petrol" in taxes:
        out.append({"label": "Taxes in the pump price", "value": f"{taxes['petrol'] * 100:.0f}%",
                    "sub": "of petrol's" + (f"; {taxes['diesel'] * 100:.0f}% of diesel's" if "diesel" in taxes else "")})
    gaps = {f: value / ea - 1 for f, (date, value) in latest.items() if (ea := at(f"{f}_price_ea", date))}
    if "petrol" in gaps:
        out.append({"label": "Against the euro area", "value": f"{_signed(gaps['petrol'] * 100, 0)}%",
                    "sub": "petrol in Spain against the euro-area average" +
                           (f"; diesel {_signed(gaps['diesel'] * 100, 0)}%" if "diesel" in gaps else "")})
    return out
