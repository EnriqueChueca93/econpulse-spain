"""The HICP basket item by item: the Inflation page's treemap, and the basket over time.

Eurostat publishes the harmonised index for each detailed item of the basket (an ECOICOP ver. 2 subclass:
bread, diesel, restaurants...) with its weight each year, its share of household spending. After the
indicators are fetched, `refresh` saves them to data/hicp_basket.json (the tables are downloaded once a run,
for the underlying-inflation measures too, sources/hicpdist.py): each item's category, its annual rate of
change month by month, its contribution to the annual rate of the whole basket and its weight year by year.

Contributions. The HICP is a chain index: each year's basket (its weights) prices the months of that year
against the December before. An item's contribution to the annual rate in month m of year t is then, as
Eurostat computes it,

    A(t-1, Dec) / A(t-1, m) × s(t)   × (P(t, m) / P(t-1, Dec) − 1)
  + A(t-2, Dec) / A(t-1, m) × s(t-1) × (P(t-1, Dec) − P(t-1, m)) / P(t-2, Dec)

where P is the item's index, s its share of the year's basket and A the all-items index: its price change
since December, at this year's weight, plus its change over the rest of last year, at last year's weight. The
contributions add up exactly to the annual rate of the items chained together (`chain`), which is the
published HICP to within 0.05 points every month since 2016. Items new to the classification (in 2026) have
no annual rate for a year but do contribute, through their change since December.

`treemap` builds the chart spec: every item's name, and its rate and contribution month by month since 2016,
and its share of the basket year by year. static/app.js draws from it the map for any month (one tile per
item, its area the item's weight, grouped into the 13 categories; squarified for the reader's screen and
coloured by the price change on a year earlier, warm above the ECB's 2% target and cool below, or shaded by
weight) and the basket over time (the categories' contributions to annual inflation, stacked, with the
headline rate; or their shares of the basket, stacked to 100), or one category's items. Spanish names are
INE's, by code (econpulse/ecoicop_es.json, scripts/ecoicop_names.py).
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
START = "2016-01"       # the charts' first month (the contributions need the year before's basket too)
SOURCE_URL = "https://ec.europa.eu/eurostat/databrowser/view/prc_hicp_minr/default/table"

# The categories' short names, for the map's headers and the charts' legends (the full names are in the hover text).
SHORT = {
    "CP01": "Food and soft drinks", "CP02": "Alcohol and tobacco", "CP03": "Clothing and footwear",
    "CP04": "Housing and energy", "CP05": "Household goods", "CP06": "Health care", "CP07": "Transport",
    "CP08": "Information and communication", "CP09": "Recreation and culture", "CP10": "Education",
    "CP11": "Restaurants and hotels", "CP12": "Insurance and finance", "CP13": "Personal care and other",
}


def refresh(store: Store) -> str:
    """Save the basket's items, rates, contributions and weights; on failure keep the last copy."""
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


def _dec(year: int) -> pd.Timestamp:
    return pd.Timestamp(f"{year}-12-01")


def chain(index: pd.DataFrame, weights: pd.DataFrame) -> tuple[pd.Series, dict[int, pd.Series], pd.DataFrame]:
    """The all-items index rebuilt from the items, 100 in the December before the first basket: each year's
    basket (the items with a weight and a December price to link to, as shares summing to 1) priced against
    the December before, linked year to year. A year without weights yet takes the latest year's. Also returns
    the baskets and the item indices used (a missing month keeps the item's last price)."""
    prices = index.sort_index().ffill()
    first = int(weights.index.min())
    level = {_dec(first - 1): 100.0}
    shares: dict[int, pd.Series] = {}
    for t in range(first, int(prices.index.max().year) + 1):
        dec = _dec(t - 1)
        if dec not in level or dec not in prices.index:
            break
        w = weights.loc[max(y for y in weights.index if y <= t)]
        w = w[(w > 0) & prices.loc[dec].notna()]
        if not len(w):
            break
        shares[t] = w / w.sum()
        months = prices.index[prices.index.year == t]
        rel = prices.loc[months, shares[t].index] / prices.loc[dec, shares[t].index]
        level.update(zip(months, level[dec] * (rel * shares[t]).sum(axis=1)))
    return pd.Series(level).sort_index(), shares, prices


def contributions(index: pd.DataFrame, weights: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    """Each item's contribution to the annual rate of the all-items index, points, by month (Eurostat's
    formula for a chain index, above), and that index's annual rate, which they add up to."""
    level, shares, prices = chain(index, weights)
    out, rate = {}, {}
    for m in level.index:
        t, before = m.year, m - pd.DateOffset(years=1)
        if t not in shares or t - 1 not in shares or before not in level.index:
            continue
        now, last = shares[t], shares[t - 1]
        dec1, dec2 = _dec(t - 1), _dec(t - 2)
        this_year = level[dec1] / level[before] * now * (prices.loc[m, now.index] / prices.loc[dec1, now.index] - 1)
        last_year = (level[dec2] / level[before] * last
                     * (prices.loc[dec1, last.index] - prices.loc[before, last.index]) / prices.loc[dec2, last.index])
        out[m] = this_year.add(last_year, fill_value=0) * 100
        rate[m] = (level[m] / level[before] - 1) * 100
    table = pd.DataFrame(out).T.reindex(columns=index.columns) if out else pd.DataFrame(columns=index.columns)
    return table, pd.Series(rate, dtype=float)


def _numbers(values, decimals: int) -> list:
    return [None if pd.isna(v) else round(float(v), decimals) for v in values]


def payload(index: pd.DataFrame, weights: pd.DataFrame, labels: dict[str, str], now: str) -> dict:
    """What is saved: items with a weight in some year; their annual rates and contributions (points) by month,
    from the first month with any rate; the items chained together's annual rate ("total", which the
    contributions add up to); and the items' weights by year (‰, only where above zero)."""
    yoy = (index / index.shift(12) - 1) * 100
    yoy = yoy.loc[yoy.notna().any(axis=1)]
    added, total = contributions(index, weights)
    added = added.reindex(index=yoy.index, columns=index.columns)
    items = [c for c in index.columns if (weights[c].fillna(0) > 0).any()]
    return {
        "fetched_at": now,
        "months": [d.strftime("%Y-%m") for d in yoy.index],
        "categories": {d: item_name(labels.get(d, d)) for d in sorted({c[:4] for c in items})},
        "items": {c: item_name(labels.get(c, c)) for c in items},
        "rates": {c: _numbers(yoy[c], 2) for c in items},
        "contributions": {c: _numbers(added[c], 3) for c in items},
        "total": _numbers(total.reindex(yoy.index), 2),
        "weights": {str(y): {c: round(float(weights.at[y, c]), 3) for c in items if weights.at[y, c] > 0}
                    for y in weights.index},
    }


@cache
def _spanish() -> dict[str, str]:
    return json.loads(NAMES_ES.read_text(encoding="utf-8"))


def name(code: str, english: str) -> str:
    return i18n.pick(english, _spanish().get(code))


def _words(fit: float | None) -> dict:
    """What the script writes, in the page's language."""
    def pct(v):
        return f"{v:g}%".replace("-", "−")
    lo, mid, hi = STEPS
    t = TARGET
    return {
        "view": _("View"), "map": _("Map"), "time": _("Over time"), "month": _("Month"), "year": _("Year"),
        "growth": _("Price growth"), "weight": _("Weight"), "show": _("Show"),
        "back": _("← All categories"), "open": _("Open {name}"), "all": _("All categories"),
        "share": _("{share} of the basket"), "rate": _("{rate} on a year earlier"),
        "adds": _("adds about {pp} points to inflation"), "takes": _("takes about {pp} points off inflation"),
        "none": _("No annual rate yet: new in the classification"),
        "hint": _("Hover over or tap a tile for its figures. Click a category to open it."),
        "hint_open": _("Hover over or tap a tile for its figures."),
        "hint_time": _("Hover over or tap the chart for each period's figures. Pick a category to see its items."),
        "fit": None if fit is None else _("The categories add up to the published rate to within {pp} points "
                                         "every month.").format(pp=f"{fit:.2f}"),
        "subtitle_map": _("HICP, {month}: each tile is an item, sized by its share of household spending"),
        "subtitle_growth": _("Contributions to annual HICP inflation by category, percentage points, and the "
                             "headline rate, %"),
        "subtitle_growth_open": _("{name}: its items' contributions to annual HICP inflation, percentage points"),
        "subtitle_weight": _("Each category's share of the basket, %, year by year"),
        "subtitle_weight_open": _("{name}: each item's share of the category's spending, %, year by year"),
        "headline": _("Headline inflation"), "total_of": _("{name}, total"),
        "rest": _("Everything else"), "rest_items": _("Other items"), "pp": _("pp"),
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
    """The chart spec (kind "treemap"): the basket month by month since 2016, the map opening on the latest;
    None before the basket is downloaded."""
    saved = data.store.load_json(STORE, None)
    if not saved or not saved.get("months") or "contributions" not in saved or saved["months"][-1] < START:
        return None
    k0 = next(k for k, m in enumerate(saved["months"]) if m >= START)
    months = saved["months"][k0:]
    dates = [pd.Timestamp(m + "-01") for m in months]
    codes = sorted(saved["items"])
    shares = {}
    for year, w in sorted(saved["weights"].items()):
        total = sum(w.values())
        shares[year] = [round(w.get(c, 0) / total * 100, 3) for c in codes]
    headline = data.raw("hicp") if "hicp" in data.by_id else None
    headline = [None if headline is None or d not in headline.index or pd.isna(headline[d]) else round(float(headline[d]), 1)
                for d in dates]
    gaps = [abs(h - t) for h, t in zip(headline, saved["total"][k0:]) if h is not None and t is not None]
    words = _words(max(gaps) if gaps else None)
    return {
        "id": "basket", "kind": "treemap", "lang": i18n.lang(),
        "title": _("The basket, item by item"),
        "subtitle": words["subtitle_map"].format(month=period_label(dates[-1], "M")),
        "unit": "%", "decimals": 1, "freq": None, "series": [], "ref_lines": [],
        "target": TARGET, "steps": list(STEPS), "wsteps": list(WEIGHT_STEPS),
        "months": months, "labels": [period_label(d, "M") for d in dates],
        "cats": [[c, _(SHORT.get(c, c)), name(c, saved["categories"].get(c, c))] for c in sorted(saved["categories"])],
        "items": [[c, name(c, saved["items"][c])] for c in codes],
        "rates": [_numbers(saved["rates"][c][k0:], 1) for c in codes],
        "contribs": [saved["contributions"][c][k0:] for c in codes],
        "shares": shares, "headline": headline, "words": words,
        "source": _("Eurostat (HICP); Macroscope calculation"),
        "sources": [{"name": "Eurostat", "url": SOURCE_URL}, {"name": _("Macroscope calculation")}],
    }
