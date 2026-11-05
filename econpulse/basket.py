"""The HICP basket item by item: the Inflation page's treemap.

Eurostat publishes the harmonised index for each detailed item of the basket (an ECOICOP ver. 2 subclass:
bread, diesel, restaurants...) with its weight each year, its share of household spending. After the
indicators are fetched, `refresh` saves them to data/hicp_basket.json (the tables are downloaded once a run,
for the underlying-inflation measures too, sources/hicpdist.py): each item's category, its annual rate of
change month by month and its weight year by year.

`treemap` builds the chart: one tile per item, its area the item's weight in the latest month's basket,
grouped into the 13 categories (ECOICOP divisions). static/app.js lays it out for the reader's screen
(squarified) and colours it by the item's price change on a year earlier (warm above the ECB's 2% target,
cool below) or shades it by its weight. An item's contribution is its weight times its annual rate: roughly
the points it adds to inflation. Items new to the classification have no annual rate for a year, and show
as such. Spanish names are INE's, by code (econpulse/ecoicop_es.json, scripts/ecoicop_names.py).
"""

import json
from datetime import datetime, timezone
from functools import cache
from pathlib import Path

import pandas as pd

from . import i18n
from .i18n import _
from .snapshot import period_label
from .sources import hicpdist
from .store import Store
from .tables import Data
from .underlying import item_name

STORE = "hicp_basket"
NAMES_ES = Path(__file__).with_name("ecoicop_es.json")
TARGET = 2.0
# Shades of price growth, by distance from the target: within 0.5 points is "on target", then 2 and 4 points.
STEPS = (0.5, 2.0, 4.0)
# Shades of weight, % of the basket.
WEIGHT_STEPS = (0.2, 0.5, 1.5)
SOURCE_URL = "https://ec.europa.eu/eurostat/databrowser/view/prc_hicp_minr/default/table"

# The categories' short names, for the map's headers (the full names are in the hover text).
SHORT = {
    "CP01": "Food and soft drinks", "CP02": "Alcohol and tobacco", "CP03": "Clothing and footwear",
    "CP04": "Housing and energy", "CP05": "Household goods", "CP06": "Health care", "CP07": "Transport",
    "CP08": "Information and communication", "CP09": "Recreation and culture", "CP10": "Education",
    "CP11": "Restaurants and hotels", "CP12": "Insurance and finance", "CP13": "Personal care and other",
}


def refresh(store: Store) -> str:
    """Save the basket's items, rates and weights; on failure keep the last copy."""
    saved = store.load_json(STORE, None) or {}
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    try:
        found = payload(*hicpdist.basket("ES"), now)
    except Exception as e:  # keep what we had
        saved.update(error=f"{type(e).__name__}: {e}", failed_at=now)
        store.save_json(STORE, saved)
        return f"not updated ({saved['error']}); keeping the copy from {saved.get('fetched_at', 'never')}"
    store.save_json(STORE, found)
    return f"{len(found['items'])} items, {found['months'][0]} to {found['months'][-1]}"


def payload(index: pd.DataFrame, weights: pd.DataFrame, labels: dict[str, str], now: str) -> dict:
    """What is saved: items with a weight in some year, their annual rates by month (from the first month with
    any) and their weights by year (‰, only where above zero)."""
    yoy = (index / index.shift(12) - 1) * 100
    yoy = yoy.loc[yoy.notna().any(axis=1)]
    items = [c for c in index.columns if (weights[c].fillna(0) > 0).any()]
    return {
        "fetched_at": now,
        "months": [d.strftime("%Y-%m") for d in yoy.index],
        "categories": {d: item_name(labels.get(d, d)) for d in sorted({c[:4] for c in items})},
        "items": {c: item_name(labels.get(c, c)) for c in items},
        "rates": {c: [None if pd.isna(v) else round(float(v), 2) for v in yoy[c]] for c in items},
        "weights": {str(y): {c: round(float(weights.at[y, c]), 3) for c in items if weights.at[y, c] > 0}
                    for y in weights.index},
    }


@cache
def _spanish() -> dict[str, str]:
    return json.loads(NAMES_ES.read_text(encoding="utf-8"))


def name(code: str, english: str) -> str:
    return i18n.pick(english, _spanish().get(code))


def _shade(rate: float | None) -> str:
    if rate is None:
        return "none"
    gap = rate - TARGET
    if abs(gap) < STEPS[0]:
        return "mid"
    step = sum(abs(gap) >= s for s in STEPS)
    return f"{'hot' if gap > 0 else 'cool'}{step}"


def _weight_shade(share: float) -> int:
    return 1 + sum(share >= s for s in WEIGHT_STEPS)


def month_view(saved: dict, k: int) -> list[dict]:
    """The categories and their items in month `k` of the saved months, largest first: weights as % of the
    basket (that year's), rates, contributions (points of annual inflation) and shades."""
    year = saved["months"][k][:4]
    weights = saved["weights"].get(year) or saved["weights"][max(y for y in saved["weights"] if y <= year)]
    total = sum(weights.values())
    groups: dict[str, list[dict]] = {}
    for code, w in weights.items():
        rates = saved["rates"].get(code) or []
        rate = rates[k] if k < len(rates) else None
        share = w / total * 100
        groups.setdefault(code[:4], []).append({
            "code": code, "name": name(code, saved["items"].get(code, code)), "weight": round(share, 3),
            "rate": rate, "contribution": None if rate is None else round(share * rate / 100, 3),
            "shade": _shade(rate), "wshade": _weight_shade(share)})
    out = []
    for code, items in groups.items():
        items.sort(key=lambda i: -i["weight"])
        rated = [i for i in items if i["rate"] is not None]
        weight, rated_weight = sum(i["weight"] for i in items), sum(i["weight"] for i in rated)
        rate = round(sum(i["weight"] * i["rate"] for i in rated) / rated_weight, 2) if rated_weight else None
        out.append({"code": code, "name": _(SHORT.get(code, code)), "full": name(code, saved["categories"].get(code, code)),
                     "weight": round(weight, 3), "rate": rate,
                     "contribution": round(sum(i["contribution"] for i in rated), 3) if rated else None,
                     "shade": _shade(rate), "items": items})
    return sorted(out, key=lambda c: -c["weight"])


def _words() -> dict:
    """What the script writes, in the page's language."""
    def pct(v):
        return f"{v:g}%".replace("-", "−")
    lo, mid, hi = STEPS
    t = TARGET
    return {
        "growth": _("Price growth"), "weight": _("Weight"), "show": _("Show"),
        "back": _("← All categories"), "open": _("Open {name}"),
        "share": _("{share} of the basket"), "rate": _("{rate} on a year earlier"),
        "adds": _("adds about {pp} points to inflation"), "takes": _("takes about {pp} points off inflation"),
        "none": _("No annual rate yet: new in the classification"),
        "hint": _("Hover over or tap a tile for its figures. Click a category to open it."),
        "hint_open": _("Hover over or tap a tile for its figures."),
        "category": _("Category"), "item": _("Item"), "weight_col": _("Weight, % of the basket"),
        "rate_col": _("Annual rate, %"), "contribution_col": _("Contribution, points"),
        "legend_growth": [
            ["cool3", _("{x} or less").format(x=pct(t - hi))], ["cool2", f"{pct(t - hi)} {_('to')} {pct(t - mid)}"],
            ["cool1", f"{pct(t - mid)} {_('to')} {pct(t - lo)}"], ["mid", f"{pct(t - lo)} {_('to')} {pct(t + lo)}"],
            ["hot1", f"{pct(t + lo)} {_('to')} {pct(t + mid)}"], ["hot2", f"{pct(t + mid)} {_('to')} {pct(t + hi)}"],
            ["hot3", _("{x} or more").format(x=pct(t + hi))], ["none", _("no annual rate yet")]],
        "legend_weight": [[1, _("below {x}").format(x=pct(WEIGHT_STEPS[0]))],
                          [2, f"{pct(WEIGHT_STEPS[0])} {_('to')} {pct(WEIGHT_STEPS[1])}"],
                          [3, f"{pct(WEIGHT_STEPS[1])} {_('to')} {pct(WEIGHT_STEPS[2])}"],
                          [4, _("{x} or more").format(x=pct(WEIGHT_STEPS[2]))]],
        "legend_growth_title": _("Price change on a year earlier:"), "legend_weight_title": _("Share of the basket:"),
    }


def treemap(data: Data) -> dict | None:
    """The chart spec (kind "treemap") for the latest month; None before the basket is downloaded."""
    saved = data.store.load_json(STORE, None)
    if not saved or not saved.get("months"):
        return None
    k = len(saved["months"]) - 1
    month = pd.Timestamp(saved["months"][k] + "-01")
    categories = month_view(saved, k)
    return {
        "id": "basket", "kind": "treemap", "lang": i18n.lang(),
        "title": _("The basket, item by item"),
        "subtitle": _("HICP, {month}: each tile is an item, sized by its share of household spending").format(
            month=period_label(month, "M")),
        "unit": "%", "decimals": 1, "freq": None, "series": [], "ref_lines": [],
        "month": period_label(month, "M"), "target": TARGET, "categories": categories, "words": _words(),
        "source": _("Eurostat (HICP); Macroscope calculation"),
        "sources": [{"name": "Eurostat", "url": SOURCE_URL}, {"name": _("Macroscope calculation")}],
    }
