"""Money and credit on the Financial page (Batch 35): the monetary survey in the IMF's layout, where broad money
growth comes from (35a), and how money, credit, interest rates, growth and inflation move together (35b).

The survey balances by construction: broad money = net foreign assets + net claims on general government + claims on
the private sector and other financial corporations − the liabilities outside broad money (deposits and securities
excluded from it, equity, derivatives) − other items (net). So broad money growth over a year splits exactly into
each counterpart's change as a share of broad money a year earlier.
"""

import pandas as pd

from . import i18n
from .charts import localise
from .i18n import _
from .snapshot import fmt_change, fmt_value, period_label
from .tables import Data

USES = ["ms_nfa", "ms_domestic_claims", "ms_net_claims_gg", "ms_claims_gg", "ms_gov_deposits", "ms_claims_private",
        "ms_loans_nfc", "ms_loans_households", "ms_broad_money", "ms_currency", "ms_transferable", "ms_other_deposits",
        "ms_securities_bm", "ms_deposits_xbm", "ms_securities_xbm", "ms_equity", "ms_derivatives", "ms_oin"]
START = "2015-01-01"


def _s(data: Data, ind_id: str) -> pd.Series | None:
    s = data.raw(ind_id)
    return None if s is None or s.dropna().empty else s.dropna()


def _yoy(s: pd.Series) -> pd.Series:
    return ((s / s.shift(12) - 1) * 100).dropna()


def sources(data: Data) -> dict[str, pd.Series] | None:
    """Each counterpart's contribution to broad money growth over 12 months, percentage points."""
    bm = _s(data, "ms_broad_money")
    parts = {k: _s(data, i) for k, i in (("nfa", "ms_nfa"), ("gg", "ms_net_claims_gg"), ("private", "ms_claims_private"),
                                         ("dx", "ms_deposits_xbm"), ("sx", "ms_securities_xbm"), ("eq", "ms_equity"),
                                         ("der", "ms_derivatives"), ("oin", "ms_oin"))}
    if bm is None or any(v is None for v in parts.values()):
        return None
    base = bm.shift(12)
    share = lambda s: ((s - s.shift(12)) / base * 100).dropna()
    longer = parts["dx"] + parts["sx"] + parts["eq"] + parts["der"] + parts["oin"]
    return {"Net foreign assets": share(parts["nfa"]), "Net claims on general government": share(parts["gg"]),
            "Claims on the private sector": share(parts["private"]),
            "Longer-term liabilities and other items": -share(longer)}


def sources_chart(data: Data) -> dict | None:
    parts, bm = sources(data), _s(data, "ms_broad_money")
    if not parts or bm is None:
        return None
    series = []
    for name, s in parts.items():
        s = s[s.index >= START]
        series.append({"name": name, "x": [d.strftime("%Y-%m-%d") for d in s.index], "y": s.round(3).tolist()})
    g = _yoy(bm)
    g = g[g.index >= START]
    series.append({"name": "Broad money", "kind": "line", "color": "ink", "x": [d.strftime("%Y-%m-%d") for d in g.index],
                   "y": g.round(3).tolist()})
    return localise({"id": "money-sources", "title": "Where broad money growth comes from",
                     "subtitle": "Contributions to broad money growth on a year earlier, percentage points",
                     "kind": "bar", "stack": True, "signed": True, "unit": "pp", "decimals": 1, "freq": "M",
                     "ref_lines": [], "series": series, "source": _("ECB; Banco de España; Macroscope calculation")})


def facts(data: Data) -> list[dict]:
    bm, private, nfa, gg = (_s(data, i) for i in ("ms_broad_money", "ms_claims_private", "ms_nfa", "ms_net_claims_gg"))
    if bm is None:
        return []
    out = [{"label": _("Broad money"), "value": fmt_value(float(bm.iloc[-1]), "€ bn", 0),
            "sub": _("{change} on a year earlier · {month}").format(change=fmt_change(float(_yoy(bm).iloc[-1]), "%", 1),
                                                                    month=period_label(bm.index[-1], "M"))}]
    for s, label in ((private, "Claims on the private sector"), (gg, "Net claims on general government")):
        if s is not None and len(s) > 12:
            out.append({"label": _(label), "value": fmt_change(float(_yoy(s).iloc[-1]), "%", 1),
                        "sub": _("on a year earlier · {month}").format(month=period_label(s.index[-1], "M"))})
    if nfa is not None:
        out.append({"label": _("Net foreign assets"), "value": fmt_value(float(nfa.iloc[-1]), "€ bn", 0),
                    "sub": _("claims on the rest of the world less liabilities to it · {month}").format(
                        month=period_label(nfa.index[-1], "M"))})
    return out


# ---------------------------------------------------------------- Batch 35b: how the variables move together
# Money and prices, credit and growth, monetary transmission, and which variables have led growth and inflation.
# Every reading describes correlations: what has moved together, never what causes what.

LINKS_USES = ["ms_broad_money_long", "hicp", "gdp_nominal", "domestic_demand", "private_credit_growth",
              "credit_flow_nfc", "credit_flow_households", "bis_credit_gdp", "bis_credit_trend", "bis_credit_gap"]
RATES = [("ecb_deposit_rate", "ECB deposit rate"), ("euribor_12m", "12-month Euribor"),
         ("nfc_loan_rate", "Loans to firms"), ("mortgage_rate", "Mortgages"),
         ("deposit_rate_households", "Time deposits"), ("deposit_rate_overnight", "Overnight deposits")]
RATES_USES = [i for i, _name in RATES]
LEADS_USES = ["ms_broad_money_long", "private_credit_growth", "credit_flow_nfc", "credit_flow_households", "gdp_nominal",
              "ecb_deposit_rate", "nfc_loan_rate", "risk_premium_monthly", "gdp", "hicp"]
RATES_START = "2003-01-01"
SAMPLE = "2000-01-01"                        # correlations from here
LEFT_OUT = ("2020-01-01", "2021-12-31")      # the pandemic: pairs that touch these quarters are left out
LEADS = range(9)                             # 0 to 8 quarters ahead
WINDOW = 32                                  # rolling correlations over 32 quarters (8 years)
# The variables that might lead growth and inflation, quarterly (see _quarterly).
LEADERS = [("money", "Broad money growth"), ("credit", "Credit growth"), ("impulse", "Credit impulse"),
           ("rate_change", "ECB rate change"), ("spread", "Loan spread"), ("premium", "Risk premium")]
TARGETS = [("gdp", "Real GDP growth"), ("inflation", "Inflation")]
# The pairs whose correlation is followed over time: (leader, target, quarters ahead, name).
ROLLING = [("money", "inflation", 8, "Money, inflation"),
           ("impulse", "gdp", 1, "Impulse, growth"),
           ("credit", "gdp", 0, "Credit, growth"),
           ("premium", "gdp", 0, "Premium, growth")]
# The ECB's 2022-23 rises: from the month before the first to the month the deposit rate peaked (by the end of 2024).
HIKES = ("2022-06-01", "2024-12-01")


def _dates(index) -> list[str]:
    return [d.strftime("%Y-%m-%d") for d in index]


def _line(name: str, s: pd.Series, **opts) -> dict:
    return {"name": name, "x": _dates(s.index), "y": s.round(3).tolist(), **opts}


def _dashed(series: list[dict]) -> list[dict]:
    """Palette slots 4 to 6 come dashed (see static/app.js), as their colours sit close to the first three's."""
    slot = 0
    for s in series:
        if not s.get("color"):
            slot += 1
            if slot >= 4:
                s.setdefault("dash", "dash")
    return series


def _monthly(s: pd.Series) -> pd.Series:
    """A daily rate as monthly averages (monthly series are unchanged)."""
    return s.resample("MS").mean().dropna()


def _quarter(s: pd.Series, how: str = "mean") -> pd.Series:
    """A monthly (or daily) series by quarter, the average or the last month, for quarters with all three months."""
    groups = _monthly(s).resample("QS")
    out = groups.last() if how == "last" else groups.mean()
    return out[groups.count() == 3].dropna()


def _change(s: pd.Series, quarters: int = 4, pct: bool = True) -> pd.Series:
    """The change on `quarters` quarters earlier, in % or (pct=False) in the series' own units."""
    before = pd.Series(s.values, index=s.index + pd.DateOffset(months=3 * quarters)).reindex(s.index)
    return ((s / before - 1) * 100 if pct else s - before).dropna()


def _describe(r: float) -> str:
    size = "weak" if abs(r) < 0.3 else "moderate" if abs(r) < 0.6 else "strong"
    return _(f"{size} and {'positive' if r >= 0 else 'negative'}")


def _r(r: float) -> str:
    return fmt_value(r, "index", 2)


def _ahead(k: int) -> str:
    return _("same quarter") if k == 0 else i18n.ngettext("{n} quarter ahead", "{n} quarters ahead", k).format(n=k)


def credit_impulse(data: Data) -> pd.Series | None:
    """The change in the past 12 months' net new lending to firms and households on the 12 months before, as a
    share of nominal GDP over the past four quarters, %; quarterly (Biggs, Mayer and Pick's measure)."""
    nfc, hh, gdp = (_s(data, i) for i in ("credit_flow_nfc", "credit_flow_households", "gdp_nominal"))
    if nfc is None or hh is None or gdp is None:
        return None
    year = (nfc + hh).dropna().rolling(12).sum().dropna()
    year = year[year.index.month % 3 == 0]
    year.index = year.index.to_period("Q").to_timestamp()
    income = gdp.rolling(4).sum().dropna()
    return (_change(year, 4, pct=False) / income * 100).dropna()


def _quarterly(data: Data) -> dict[str, pd.Series] | None:
    """The leaders and the targets, quarterly: money and credit growth on a year earlier (%), the credit impulse
    (% of GDP), the change in the ECB deposit rate on a year earlier (pp), the rate on new loans to firms less the
    deposit rate (pp), Spain's 10-year spread over Germany (pp); real GDP growth on a year earlier and HICP inflation."""
    s = {i: _s(data, i) for i in LEADS_USES}
    impulse = credit_impulse(data)
    if any(v is None for v in s.values()) or impulse is None:
        return None
    dfr = _quarter(s["ecb_deposit_rate"])
    return {"money": _change(_quarter(s["ms_broad_money_long"], "last")),
            "credit": _quarter(s["private_credit_growth"]),
            "impulse": impulse,
            "rate_change": _change(dfr, 4, pct=False),
            "spread": (_quarter(s["nfc_loan_rate"]) - dfr).dropna(),
            "premium": _quarter(s["risk_premium_monthly"]) / 100,
            "gdp": _change(s["gdp"]),
            "inflation": _quarter(s["hicp"])}


def _pairs(x: pd.Series, y: pd.Series, lead: int) -> pd.DataFrame:
    """x beside y `lead` quarters later, from SAMPLE on, leaving out pairs that touch the pandemic years."""
    ahead = pd.Series(y.values, index=y.index - pd.DateOffset(months=3 * lead))
    df = pd.concat([x.rename("x"), ahead.rename("y")], axis=1, sort=True).dropna()
    df = df[df.index >= SAMPLE]
    target = df.index + pd.DateOffset(months=3 * lead)
    lo, hi = pd.Timestamp(LEFT_OUT[0]), pd.Timestamp(LEFT_OUT[1])
    return df[~(((df.index >= lo) & (df.index <= hi)) | ((target >= lo) & (target <= hi)))]


def lead_correlations(data: Data) -> dict[str, dict[str, list[float]]] | None:
    """{target: {leader: [correlation at 0, 1, ... 8 quarters ahead]}}."""
    q = _quarterly(data)
    if q is None:
        return None
    return {t: {v: [float(df["x"].corr(df["y"])) for df in (_pairs(q[v], q[t], k) for k in LEADS)]
                for v, _label in LEADERS}
            for t, _name in TARGETS}


def _strongest(rs: list[float]) -> tuple[float, int]:
    k = max(LEADS, key=lambda i: abs(rs[i]))
    return rs[k], k


def rolling_correlations(data: Data) -> dict[str, pd.Series] | None:
    q = _quarterly(data)
    if q is None:
        return None
    out = {}
    for x, y, lead, name in ROLLING:
        df = _pairs(q[x], q[y], lead)
        out[name] = df["x"].rolling(WINDOW).corr(df["y"]).dropna()
    return out


# ---- money and prices, credit and growth

def money_inflation_chart(data: Data) -> dict | None:
    bm, hicp = _s(data, "ms_broad_money_long"), _s(data, "hicp")
    if bm is None or hicp is None:
        return None
    growth = _yoy(bm)
    moved = pd.Series(growth.values, index=growth.index + pd.DateOffset(months=24))
    series = [_line("HICP inflation", hicp[hicp.index >= SAMPLE]),
              _line("Broad money growth", moved[moved.index >= SAMPLE])]
    reading = _("Faster money growth is meant to show up in prices a year or two later. Here broad money is drawn "
                "two years after it was measured, so the lines would move together if it did.")
    leads = lead_correlations(data)
    if leads:
        r = leads["inflation"]["money"][8]
        reading += " " + _("Quarter by quarter since 2000, leaving out 2020 and 2021, the correlation two years on is "
                           "{r}: {link}.").format(r=_r(r), link=_describe(r))
    peak = growth.idxmax()
    later = hicp.get(peak + pd.DateOffset(months=24))
    if later is not None and not pd.isna(later):
        reading += " " + _("Money growth peaked at {peak} in {month}; two years later inflation was {later}.").format(
            peak=fmt_value(float(growth.max()), "%", 1), month=period_label(peak, "M"),
            later=fmt_value(float(later), "%", 1))
    reading += " " + _("As a member of the euro area, Spain's prices follow the euro area's money and energy costs as "
                       "much as its own money.")
    return localise({"id": "money-inflation", "title": "Broad money growth and inflation two years later",
                     "subtitle": "% change on a year earlier; broad money growth is drawn two years after the month it was measured",
                     "kind": "line", "unit": "%", "decimals": 1, "freq": "M", "ref_lines": [], "series": series,
                     "source": _("Banco de España; Eurostat; Macroscope calculation"), "reading": reading})


def velocity(data: Data) -> pd.Series | None:
    """Nominal GDP over the past four quarters (€ bn) over broad money at the end of the quarter (€ bn)."""
    gdp, bm = _s(data, "gdp_nominal"), _s(data, "ms_broad_money_long")
    if gdp is None or bm is None:
        return None
    return (gdp.rolling(4).sum() / 1000 / _quarter(bm, "last")).dropna()


def velocity_chart(data: Data) -> dict | None:
    v = velocity(data)
    if v is None or v.empty:
        return None
    reading = _("How many times a year each euro of broad money pays for the economy's output: nominal GDP over the "
                "money stock. It was {first} in {first_q}, peaked at {peak} in {peak_q} and is {last} in {last_q}.").format(
        first=_r(float(v.iloc[0])), first_q=period_label(v.index[0], "Q"), peak=_r(float(v.max())),
        peak_q=period_label(v.idxmax(), "Q"), last=_r(float(v.iloc[-1])), last_q=period_label(v.index[-1], "Q"))
    if v.iloc[-1] < v.max() * 0.97:
        reading += " " + _("Money has grown faster than nominal GDP since then: households and firms hold more money "
                           "for each euro of output, so money growth alone is a poor guide to spending.")
    return localise({"id": "money-velocity", "title": "The velocity of money",
                     "subtitle": "Nominal GDP over the past four quarters divided by broad money at the end of the quarter",
                     "kind": "line", "unit": "", "decimals": 2, "freq": "Q", "ref_lines": [],
                     "series": [_line("Velocity", v)],
                     "source": _("INE; Banco de España; Macroscope calculation"), "reading": reading})


def credit_growth_chart(data: Data) -> dict | None:
    credit, gdp = _s(data, "private_credit_growth"), _s(data, "gdp_nominal")
    if credit is None or gdp is None:
        return None
    credit, nominal = _quarter(credit), _change(gdp)
    credit, nominal = credit[credit.index >= SAMPLE], nominal[nominal.index >= SAMPLE]
    both = pd.concat([credit.rename("c"), nominal.rename("g")], axis=1, sort=True).dropna()
    boom = both.loc["2005-01-01":"2007-12-31"].mean()
    reading = _("From 2005 to 2007 bank credit grew {c} a year on average, {times} times as fast as nominal GDP "
                "({g}).").format(c=fmt_value(float(boom["c"]), "%", 1), times=f"{boom['c'] / boom['g']:.1f}",
                                 g=fmt_value(float(boom["g"]), "%", 1))
    after = credit[credit.index >= "2008-01-01"]
    falling = after[after < 0]
    if len(falling):
        span = after[(after.index >= falling.index[0]) & (after.index <= falling.index[-1])]
        reading += " " + _("It then shrank in {n} of the {total} quarters from {first} to {last}, as households and "
                           "firms paid down debt.").format(n=len(falling), total=len(span),
                                                           first=period_label(falling.index[0], "Q"),
                                                           last=period_label(falling.index[-1], "Q"))
    r = float(both["c"].corr(both["g"]))
    reading += " " + _("Since 2000 the two have a correlation of {r}: {link}.").format(r=_r(r), link=_describe(r))
    return localise({"id": "money-credit-nominal", "title": "Credit and nominal growth",
                     "subtitle": "% change on a year earlier: bank loans to the private sector (adjusted for sales and write-offs) and nominal GDP",
                     "kind": "line", "unit": "%", "decimals": 1, "freq": "Q", "ref_lines": [],
                     "series": [_line("Nominal GDP", nominal, color="ink"), _line("Bank credit", credit)],
                     "source": _("ECB; INE; Macroscope calculation"), "reading": reading})


def credit_gdp_chart(data: Data) -> dict | None:
    ratio, trend = _s(data, "bis_credit_gdp"), _s(data, "bis_credit_trend")
    if ratio is None or trend is None:
        return None
    reading = _("Credit from all lenders to firms and households rose to {peak} of GDP in {peak_q}, the debt left by the housing boom, "
                "and was {last} in {last_q}. The long-run trend follows slowly, so after a "
                "bust it stays above the ratio for years.").format(
        peak=fmt_value(float(ratio.max()), "%", 0), peak_q=period_label(ratio.idxmax(), "Q"),
        last=fmt_value(float(ratio.iloc[-1]), "%", 0), last_q=period_label(ratio.index[-1], "Q"))
    return localise({"id": "money-credit-gdp", "title": "Credit to GDP and its long-run trend",
                     "subtitle": "Credit to the private non-financial sector, % of GDP, and the Basel Committee's trend",
                     "kind": "line", "unit": "%", "decimals": 1, "freq": "Q", "ref_lines": [],
                     "series": [_line("Credit to GDP", ratio), _line("Long-run trend", trend)],
                     "source": _("BIS"), "reading": reading})


def credit_gap_chart(data: Data) -> dict | None:
    gap = _s(data, "bis_credit_gap")
    if gap is None:
        return None
    reading = _("The Basel Committee's early-warning gauge: when the gap passes 2 points, banks may be asked to build a "
                "countercyclical capital buffer, which reaches its maximum at 10. Spain's peaked at {peak} points in "
                "{peak_q}, before the banking crisis, and is {last} in {last_q}.").format(
        peak=fmt_value(float(gap.max()), "index", 1), peak_q=period_label(gap.idxmax(), "Q"),
        last=fmt_value(float(gap.iloc[-1]), "index", 1), last_q=period_label(gap.index[-1], "Q"))
    above = gap[gap > 2]
    if len(above) and above.index[-1] < gap.index[-1] and gap.iloc[-1] < 0:
        reading += " " + _("It was last above 2 in {q}. A negative gap after a long deleveraging partly reflects the "
                           "boom still held in the trend, so it overstates how tight credit is.").format(
            q=period_label(above.index[-1], "Q"))
    return localise({"id": "money-credit-gap", "title": "The credit-to-GDP gap",
                     "subtitle": "Credit to GDP less its long-run trend, percentage points",
                     "kind": "bar", "signed": True, "unit": "pp", "decimals": 1, "freq": "Q",
                     "ref_lines": [{"y": 2, "label": "Buffer starts"}, {"y": 10, "label": "Buffer at its maximum"}],
                     "series": [_line("Credit-to-GDP gap", gap)], "source": _("BIS"), "reading": reading})


def impulse_chart(data: Data) -> dict | None:
    impulse, dd = credit_impulse(data), _s(data, "domestic_demand")
    if impulse is None or dd is None:
        return None
    demand = _change(dd)
    demand = demand[demand.index >= impulse.index[0]]
    df = _pairs(impulse, demand, 0)
    r = float(df["x"].corr(df["y"]))
    reading = _("Spending depends on the flow of new credit rather than its stock, so it is the change in that flow, "
                "the credit impulse, that moves with demand. Since {start}, leaving out 2020 and 2021, the correlation "
                "is {r}: {link}. In 2020 the state-guaranteed ICO loans pushed the impulse up while demand "
                "collapsed.").format(start=impulse.index[0].year, r=_r(r), link=_describe(r))
    return localise({"id": "money-impulse", "title": "The credit impulse and domestic demand",
                     "subtitle": "Change in the past year's net new lending to firms and households, % of GDP (bars); real domestic demand, % change on a year earlier (line)",
                     "kind": "bar", "signed": True, "unit": "%", "decimals": 1, "freq": "Q", "ref_lines": [],
                     "series": [_line("Credit impulse", impulse),
                                _line("Domestic demand", demand, kind="line", color="ink")],
                     "source": _("ECB; INE; Macroscope calculation"), "reading": reading})


def links_facts(data: Data) -> list[dict]:
    out = []
    v, impulse, gap = velocity(data), credit_impulse(data), _s(data, "bis_credit_gap")
    if v is not None and not v.empty:
        out.append({"label": _("Velocity of money"), "value": _r(float(v.iloc[-1])),
                    "sub": _("nominal GDP per euro of broad money · {q}").format(q=period_label(v.index[-1], "Q"))})
    if impulse is not None and not impulse.empty:
        out.append({"label": _("Credit impulse"), "value": fmt_change(float(impulse.iloc[-1]), "% of GDP", 1),
                    "sub": _("change in a year's net new lending · {q}").format(q=period_label(impulse.index[-1], "Q"))})
    if gap is not None:
        out.append({"label": _("Credit-to-GDP gap"), "value": fmt_change(float(gap.iloc[-1]), "pp", 1),
                    "sub": _("BIS; above 2 points calls for a capital buffer · {q}").format(
                        q=period_label(gap.index[-1], "Q"))})
    return out


# ---- monetary transmission

def _rates(data: Data) -> dict[str, pd.Series] | None:
    out = {i: _s(data, i) for i in RATES_USES}
    return None if any(v is None for v in out.values()) else {i: _monthly(s) for i, s in out.items()}


def passthrough(data: Data) -> dict | None:
    """How far each rate moved over the ECB's 2022-23 rises: {"start", "peak", "change": {id: pp}}."""
    rates = _rates(data)
    if rates is None:
        return None
    start = pd.Timestamp(HIKES[0])
    dfr = rates["ecb_deposit_rate"]
    rising = dfr[(dfr.index > start) & (dfr.index <= HIKES[1])]
    if rising.empty or start not in dfr.index:
        return None
    peak = rising.idxmax()
    change = {i: float(s[peak] - s[start]) for i, s in rates.items() if start in s.index and peak in s.index}
    return {"start": start, "peak": peak, "change": change}


def rates_chart(data: Data) -> dict | None:
    rates = _rates(data)
    if rates is None:
        return None
    series = _dashed([_line(name, rates[i][rates[i].index >= RATES_START], **({"color": "ink"} if i == "ecb_deposit_rate" else {}))
                      for i, name in RATES])
    reading = _("The ECB sets the deposit rate; 12-month Euribor, what banks charge each other, moves ahead of it on "
                "expected decisions, and Spain's variable-rate mortgages are mostly priced off it. Banks' rates on new "
                "loans follow within months; what they pay on deposits moves less, and on overnight deposits barely "
                "at all.")
    return localise({"id": "money-rates", "title": "From the ECB's rate to banks' rates",
                     "subtitle": "% a year, monthly averages; banks' rates on new loans and on new deposits of households",
                     "kind": "line", "unit": "%", "decimals": 2, "freq": "M", "ref_lines": [], "series": series,
                     "source": _("ECB; Banco de España"), "reading": reading})


def spreads_chart(data: Data) -> dict | None:
    rates = _rates(data)
    if rates is None:
        return None
    dfr = rates["ecb_deposit_rate"]
    spreads = {i: (rates[i] - dfr).dropna() for i, _name in RATES[2:]}
    spreads = {i: s[s.index >= RATES_START] for i, s in spreads.items()}
    series = _dashed([_line(name, spreads[i]) for i, name in RATES[2:]])
    nfc, on = spreads["nfc_loan_rate"], spreads["deposit_rate_overnight"]
    reading = _("What banks charge on new loans above the ECB's rate, and what they pay on deposits below it. The spread "
                "on new loans to firms was {nfc} points in {month}, against {avg} on average since 2003. Overnight "
                "deposits paid {low} points less than the ECB's rate at the widest, in {low_month}.").format(
        nfc=_r(float(nfc.iloc[-1])), month=period_label(nfc.index[-1], "M"), avg=_r(float(nfc.mean())),
        low=_r(float(-on.min())), low_month=period_label(on.idxmin(), "M"))
    return localise({"id": "money-spreads", "title": "What banks charge and pay over the ECB's rate",
                     "subtitle": "Rates on new business less the ECB deposit rate, percentage points",
                     "kind": "line", "signed": True, "unit": "pp", "decimals": 1, "freq": "M", "ref_lines": [],
                     "series": series, "source": _("ECB; Banco de España; Macroscope calculation"), "reading": reading})


def passthrough_chart(data: Data) -> dict | None:
    p = passthrough(data)
    if p is None or "ecb_deposit_rate" not in p["change"]:
        return None
    ids = [i for i, _name in RATES if i in p["change"]]
    names = dict(RATES)
    dfr = p["change"]["ecb_deposit_rate"]
    share = lambda i: f"{p['change'][i] / dfr * 100:.0f}%"
    reading = _("The ECB raised its deposit rate by {dfr} points between {start} and {peak}. Over the same months the "
                "rate on new loans to firms rose {nfc} points ({nfc_share} of the rise), new mortgages {mort} ({mort_share}), "
                "new time deposits {td} ({td_share}) and overnight deposits {on} ({on_share}).").format(
        dfr=_r(dfr), start=period_label(p["start"], "M"), peak=period_label(p["peak"], "M"),
        nfc=_r(p["change"]["nfc_loan_rate"]), nfc_share=share("nfc_loan_rate"),
        mort=_r(p["change"]["mortgage_rate"]), mort_share=share("mortgage_rate"),
        td=_r(p["change"]["deposit_rate_households"]), td_share=share("deposit_rate_households"),
        on=_r(p["change"]["deposit_rate_overnight"]), on_share=share("deposit_rate_overnight"))
    return localise({"id": "money-passthrough", "title": "How much of the 2022–23 rises reached each rate",
                     "subtitle": "Change from the month before the ECB's first rise to the month its deposit rate peaked, percentage points",
                     "kind": "hbar", "unit": "pp", "decimals": 2, "freq": "M", "highlight": _("ECB deposit rate"),
                     "ref_lines": [], "series": [{"name": "", "x": [_(names[i]) for i in ids],
                                                  "y": [round(p["change"][i], 3) for i in ids]}],
                     "source": _("ECB; Banco de España; Macroscope calculation"), "reading": reading})


def rates_facts(data: Data) -> list[dict]:
    rates, p = _rates(data), passthrough(data)
    if rates is None:
        return []
    dfr, nfc, on = rates["ecb_deposit_rate"], rates["nfc_loan_rate"], rates["deposit_rate_overnight"]
    raw = _s(data, "ecb_deposit_rate")
    out = [{"label": _("ECB deposit rate"), "value": fmt_value(float(raw.iloc[-1]), "%", 2),
            "sub": _("since {day}").format(day=i18n.day_month_year(raw[raw != raw.iloc[-1]].index[-1] + pd.Timedelta(days=1)))
            if (raw != raw.iloc[-1]).any() else ""},
           {"label": _("New loans to firms"), "value": fmt_value(float(nfc.iloc[-1]), "%", 2),
            "sub": _("{spread} points over the ECB's rate · {month}").format(
                spread=_r(float(nfc.iloc[-1] - dfr[nfc.index[-1]])), month=period_label(nfc.index[-1], "M"))}]
    if p and p["change"].get("ecb_deposit_rate"):
        for i, label in (("nfc_loan_rate", "Passed on to loans to firms"), ("deposit_rate_overnight", "Passed on to overnight deposits")):
            if i in p["change"]:
                out.append({"label": _(label), "value": f"{p['change'][i] / p['change']['ecb_deposit_rate'] * 100:.0f}%",
                            "sub": _("of the ECB's 2022–23 rises, by {month}").format(month=period_label(p["peak"], "M"))})
    return out


# ---- what matters most

def leads_chart(data: Data, target: str) -> dict | None:
    leads = lead_correlations(data)
    if leads is None:
        return None
    labels = ["0"] + [f"+{k}" for k in LEADS if k]
    series = _dashed([{"name": name, "x": labels, "y": [round(r, 3) for r in leads[target][v]]} for v, name in LEADERS])
    found = [(*_strongest(leads[target][v]), name) for v, name in LEADERS]
    best, worst = max(found, key=lambda f: f[0]), min(found, key=lambda f: f[0])
    reading = _("Correlations, not causes: a variable can lead because it moves first or because it reacts to the "
                "same news faster.")
    with_it = {"gdp": "Moving most closely with growth: {name} ({r}, {ahead}).",
               "inflation": "Moving most closely with inflation: {name} ({r}, {ahead})."}[target]
    reading += " " + _(with_it).format(name=_(best[2]), r=_r(best[0]), ahead=_ahead(best[1]))
    if worst[0] < 0:
        reading += " " + _("Moving most closely against it: {name} ({r}, {ahead}).").format(
            name=_(worst[2]), r=_r(worst[0]), ahead=_ahead(worst[1]))
    rate = leads["gdp"]["rate_change"]
    if target == "gdp" and rate[0] > 0.2 and abs(rate[8]) < 0.15:
        reading += " " + _("Rate rises go with strong growth at first, as the ECB raises rates in good times; the link "
                           "fades within two years.")
    title = {"gdp": "What has moved with growth", "inflation": "What has moved with inflation"}[target]
    subtitle = {"gdp": "Correlation with real GDP growth 0 to 8 quarters later, since 2000, leaving out 2020 and 2021",
                "inflation": "Correlation with inflation 0 to 8 quarters later, since 2000, leaving out 2020 and 2021"}[target]
    return localise({"id": f"money-leads-{target}", "title": title, "subtitle": subtitle, "kind": "line",
                     "x_kind": "category", "unit": "", "decimals": 2, "freq": "Q", "ref_lines": [], "series": series,
                     "source": _("ECB; Banco de España; INE; Eurostat; Macroscope calculation"), "reading": reading})


def rolling_chart(data: Data) -> dict | None:
    rolls = rolling_correlations(data)
    if not rolls or not all(len(s) for s in rolls.values()):
        return None
    series = []
    for name, s in rolls.items():
        # Every quarter from the first window to the last, empty where a window would touch 2020-21: a gap, not a
        # straight line across the pandemic.
        full = s.reindex(pd.date_range(s.index[0], s.index[-1], freq="QS"))
        series.append({"name": name, "x": _dates(full.index), "y": [None if pd.isna(v) else round(float(v), 3) for v in full]})
    series = _dashed(series)
    swings = sorted(rolls.items(), key=lambda kv: -(kv[1].max() - kv[1].min()))
    name, s = swings[0]
    pair = {"Money, inflation": "Broad money growth with inflation two years later",
            "Impulse, growth": "The credit impulse with growth a quarter later",
            "Credit, growth": "Credit growth with growth in the same quarter",
            "Premium, growth": "The risk premium with growth in the same quarter"}[name]
    reading = _("Each point is the correlation over the 32 quarters (8 years) up to it, skipping 2020 and 2021. The "
                "links are far from fixed. {name}: from {lo} to {hi}, and {last} in the latest window.").format(
        name=_(pair), lo=_r(float(s.min())), hi=_r(float(s.max())), last=_r(float(s.iloc[-1])))
    return localise({"id": "money-rolling", "title": "Do the links hold? Correlations over eight-year windows",
                     "subtitle": "Correlation over the previous 32 quarters, leaving out 2020 and 2021: broad money growth with inflation two years later, the credit impulse with real GDP growth a quarter later, credit growth and the risk premium with growth in the same quarter",
                     "kind": "line", "unit": "", "decimals": 2, "freq": "Q", "ref_lines": [], "series": series,
                     "source": _("ECB; Banco de España; INE; Eurostat; Macroscope calculation"), "reading": reading})


def leads_table(data: Data) -> dict | None:
    leads = lead_correlations(data)
    if leads is None:
        return None
    rows = []
    for v, name in LEADERS:
        cells = []
        for t, _target in TARGETS:
            r, k = _strongest(leads[t][v])
            cells += [_r(r), str(k)]
        rows.append({"label": _(name), "indent": 0, "cells": cells})
    return {"title": _("Leader"), "caption": _("The strongest correlation at 0 to 8 quarters ahead, since 2000, leaving out 2020 and 2021"),
            "columns": [_("With real GDP growth"), _("Quarters ahead"), _("With inflation"), _("Quarters ahead")],
            "rows": rows, "through": "",
            "note": _("Broad money growth: on a year earlier, end of quarter. Credit growth: bank loans to the private "
                      "sector on a year earlier, adjusted for sales and write-offs. Credit impulse: the change in a "
                      "year's net new lending to firms and households, % of GDP (from 2005). ECB rate change: the "
                      "deposit rate on a year earlier. Loan spread: the rate on new loans to firms less the ECB deposit "
                      "rate. Risk premium: Spain's 10-year yield less Germany's. Growth and inflation are on a year "
                      "earlier, quarterly. Overlapping yearly changes make neighbouring quarters alike, so small "
                      "correlations are not reliable.")}


def leads_facts(data: Data) -> list[dict]:
    leads = lead_correlations(data)
    if leads is None:
        return []
    out = []
    for t, label_pos, label_neg in (("gdp", "Moves most with growth", "Moves most against growth"),
                                    ("inflation", "Moves most with inflation", "Moves most against inflation")):
        found = [(*_strongest(leads[t][v]), name) for v, name in LEADERS]
        for pick, label in ((max(found, key=lambda f: f[0]), label_pos), (min(found, key=lambda f: f[0]), label_neg)):
            if (pick[0] > 0) == (label is label_pos):
                out.append({"label": _(label), "value": _r(pick[0]),
                            "sub": "{name}, {ahead}".format(name=_(pick[2]), ahead=_ahead(pick[1]))})
    return out
