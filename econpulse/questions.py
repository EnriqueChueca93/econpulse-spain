"""The Economy in Four Questions: the home page's plain-language summary.

Each question is a small table of readings plus one paragraph of context. A reading
whose data is missing shows a dash instead of breaking the page.
"""

import pandas as pd

from . import transforms
from .registry import Indicator
from .snapshot import fmt_change, fmt_value, period_label
from .store import Store

DASH = "–"


class _Data:
    def __init__(self, indicators: list[Indicator], store: Store):
        self.by_id = {i.id: i for i in indicators}
        self.store = store
        self._cache: dict[str, pd.Series | None] = {}

    def series(self, ind_id: str, transform: str = "level") -> pd.Series:
        key = f"{ind_id}:{transform}"
        if key not in self._cache:
            raw = self.store.load_series(ind_id)
            self._cache[key] = None if raw is None else transforms.apply(transform, raw, self.by_id[ind_id].freq)
        s = self._cache[key]
        if s is None or s.empty:
            raise LookupError(f"no data for {ind_id}")
        return s

    def period(self, ind_id: str, s: pd.Series) -> str:
        return period_label(s.index[-1], self.by_id[ind_id].freq)


def _row(label: str, compute) -> dict:
    try:
        value, note = compute()
    except (LookupError, ValueError):
        value, note = DASH, ""
    return {"label": label, "value": value, "note": note}


def inflation(d: _Data) -> dict:
    def hicp():
        s = d.series("hicp")
        return fmt_value(s.iloc[-1], "%", 1), d.period("hicp", s)

    def core():
        s = d.series("core_cpi")
        flash = " (flash)" if d.store.load_catalog().get("core_cpi", {}).get("flash") else ""
        return fmt_value(s.iloc[-1], "%", 1), d.period("core_cpi", s) + flash

    def core_pace():
        s = d.series("core_cpi_index", "sa_ann3m")
        return fmt_value(s.iloc[-1], "%", 1), d.period("core_cpi_index", s)

    return {
        "title": "Is inflation coming back to 2%?",
        "rows": [
            _row("HICP inflation, past 12 months", hicp),
            _row("Core CPI, past 12 months", core),
            _row("Core CPI, recent pace (3-month annualised, SA)", core_pace),
        ],
        "text": ("The ECB targets 2% inflation on the harmonised index (HICP) for the euro area as a whole. "
                 "Core inflation leaves out energy and unprocessed food to show the underlying trend; "
                 "the 3-month pace shows where it is heading."),
        "link": "inflation.html",
        "link_label": "Inflation",
    }


def labour(d: _Data) -> dict:
    def last_month():
        s = d.series("afiliados", "sa_diff")
        return fmt_change(s.iloc[-1], "thousands", 1), d.period("afiliados", s)

    def three_month():
        s = d.series("afiliados", "sa_diff")
        return fmt_change(s.tail(3).mean(), "thousands", 1) + " per month", ""

    def unemployment():
        s = d.series("unemployment_monthly")
        year_ago = s.get(s.index[-1] - pd.DateOffset(years=1))
        vs = f"vs {fmt_value(year_ago, '%', 1)} a year ago" if year_ago is not None else ""
        return fmt_value(s.iloc[-1], "%", 1), f"{d.period('unemployment_monthly', s)}, {vs}".strip(", ")

    return {
        "title": "Is the labour market cooling?",
        "rows": [
            _row("Social Security registrations, last month (SA)", last_month),
            _row("3-month average (SA)", three_month),
            _row("Unemployment rate (monthly, SA)", unemployment),
        ],
        "text": ("Social Security registrations (afiliados) are Spain's closest equivalent to payrolls: "
                 "the average number of people paying in each month. Seasonally adjusted by EconPulse, "
                 "so they show the trend rather than the summer and Christmas swings."),
        "link": "labour.html",
        "link_label": "Labour market",
    }


def growth(d: _Data) -> dict:
    def last_quarter():
        s = d.series("domestic_demand", "pop")
        return fmt_value(s.iloc[-1], "%", 1) + " q/q", d.period("domestic_demand", s)

    def four_quarters():
        s = d.series("domestic_demand", "yoy")
        return fmt_value(s.iloc[-1], "%", 1) + " y/y", ""

    def gdp():
        q, y = d.series("gdp", "pop"), d.series("gdp", "yoy")
        return f"{fmt_value(q.iloc[-1], '%', 1)} q/q", f"{fmt_value(y.iloc[-1], '%', 1)} y/y, {d.period('gdp', q)}"

    return {
        "title": "Is growth holding up?",
        "rows": [
            _row("Domestic demand, last quarter", last_quarter),
            _row("Domestic demand, past four quarters", four_quarters),
            _row("Real GDP, last quarter", gdp),
        ],
        "text": ("Domestic demand, spending by Spanish households, firms and government, is the cleanest "
                 "read on the economy's own momentum, before exports and imports. Growth rates are not annualised, "
                 "following Spanish convention."),
        "link": "gdp.html",
        "link_label": "GDP",
    }


def borrowing_costs(d: _Data) -> dict:
    """Change in the 10-year yield this year = change in the Bund + change in the prima de riesgo.

    Worked out on the latest date both yields exist, so the two parts add up exactly.
    """
    def parts():
        both = pd.concat({"es": d.series("es_10y"), "de": d.series("de_10y")}, axis=1).dropna()
        latest = both.index[-1]
        before = both[both.index < pd.Timestamp(latest.year, 1, 1)]
        if before.empty:
            raise LookupError("no observation before the start of the year")
        base = before.iloc[-1]
        es, de = (both.iloc[-1]["es"] - base["es"]) * 100, (both.iloc[-1]["de"] - base["de"]) * 100
        return es, de, es - de, before.index[-1], latest

    try:
        es, de, spread, base_date, latest = parts()
        since = f"since {base_date.day} {base_date:%b %Y}"
        rows = [
            {"label": f"Spain 10-year yield {since}", "value": fmt_change(es, "bp", 0), "note": ""},
            {"label": "German Bund (euro-area rates)", "value": fmt_change(de, "bp", 0), "note": ""},
            {"label": "Prima de riesgo (Spain-specific)", "value": fmt_change(spread, "bp", 0),
             "note": f"to {latest.day} {latest:%b %Y}"},
        ]
    except (LookupError, ValueError):
        rows = [{"label": label, "value": DASH, "note": ""} for label in
                ("Spain 10-year yield this year", "German Bund (euro-area rates)", "Prima de riesgo (Spain-specific)")]
    return {
        "title": "Why are Spain's borrowing costs moving?",
        "rows": rows,
        "text": ("Spain's 10-year yield is the German Bund yield, which moves with euro-area interest rates and "
                 "inflation expectations, plus the prima de riesgo, the extra return investors demand to hold "
                 "Spanish debt. Which part moved says whether the change is about the euro area or about Spain. "
                 "Here the prima de riesgo is the Spanish yield minus the Bund, so the parts add up; Banco de "
                 "España's headline spread (the tile above) uses benchmark bonds and can differ by a few bp."),
        "link": "financial.html",
        "link_label": "Financial",
    }


def four_questions(indicators: list[Indicator], store: Store) -> list[dict]:
    d = _Data(indicators, store)
    return [inflation(d), labour(d), growth(d), borrowing_costs(d)]
