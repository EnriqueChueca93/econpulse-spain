"""The Pensions page's computed blocks (Batch 29a): contributory pensions of the Social Security system.

The figures come from the Ministry of Labour's statistics bulletin (tables PEN-1 to PEN-31, sources/bel.py):
monthly series of the pensions in force, new and ended pensions, by class, scheme and region, which start in
April 2025 and grow month by month; annual averages since 2016; and the maximum and minimum amounts since
1990. EconPulse adds three calculations: what pensions cost in a year (the average number of pensions times
the average pension times the 14 payments, against nominal GDP), the average pension after inflation, and
registered workers per pension.
"""

import pandas as pd

from .snapshot import fmt_change, fmt_value, period_label
from .tables import Data, Level, Change, Panel, PanelColumn, PanelRow

CLASSES = [("total", "All pensions"), ("retirement", "Retirement"), ("widowhood", "Widowhood"),
           ("disability", "Permanent disability"), ("orphans", "Orphans")]
SCHEMES = [("general", "General scheme"), ("self_employed", "Self-employed"), ("sea", "Sea workers"),
           ("coal", "Coal mining"), ("accidents", "Work accidents"), ("diseases", "Occupational diseases"),
           ("sovi", "SOVI (pre-1967 old-age insurance)")]
REGIONS = [("andalucia", "Andalucía"), ("aragon", "Aragón"), ("asturias", "Asturias"), ("baleares", "Illes Balears"),
           ("canarias", "Canarias"), ("cantabria", "Cantabria"), ("castilla_leon", "Castilla y León"),
           ("castilla_mancha", "Castilla-La Mancha"), ("cataluna", "Cataluña"), ("valenciana", "Comunitat Valenciana"),
           ("extremadura", "Extremadura"), ("galicia", "Galicia"), ("madrid", "Madrid"), ("murcia", "Murcia"),
           ("navarra", "Navarra"), ("pais_vasco", "País Vasco"), ("rioja", "La Rioja"), ("ceuta_melilla", "Ceuta y Melilla")]
PAYMENTS = 14          # monthly payments a year, two of them extra (June and November)
COST_USES = ["pensions_total_annual", "pension_avg_total_annual", "gdp_nominal_annual", "cpi_index", "afiliados",
             "pensions_total"]
SOURCE = "Ministerio de Trabajo (BEL)"


def _clean(data: Data, ind_id: str) -> pd.Series | None:
    s = data.raw(ind_id)
    if s is None or s.dropna().empty:
        return None
    return s.dropna()


def _year_back(s: pd.Series) -> float | None:
    v = s.get(s.index[-1] - pd.DateOffset(years=1))
    return None if v is None or pd.isna(v) else float(v)


def _by_year(s: pd.Series) -> pd.Series:
    """Annual series keyed by year."""
    return pd.Series(s.to_numpy(), index=s.index.year)


def _yearly_mean(s: pd.Series, months: int = 12) -> pd.Series:
    """Calendar-year averages of a monthly series, complete years only."""
    groups = s.groupby(s.index.year)
    return groups.mean()[groups.count() == months]


# ---------------------------------------------------------------- calculations

def annual_cost(data: Data) -> pd.DataFrame | None:
    """What contributory pensions cost each year: € mn and % of GDP (an estimate)."""
    number, average = _clean(data, "pensions_total_annual"), _clean(data, "pension_avg_total_annual")
    if number is None or average is None:
        return None
    cost = (_by_year(number) * _by_year(average) * PAYMENTS / 1000).dropna()     # thousands × € → € mn
    gdp = _clean(data, "gdp_nominal_annual")
    share = cost / _by_year(gdp) * 100 if gdp is not None else pd.Series(dtype=float)
    return pd.DataFrame({"cost": cost, "share": share.reindex(cost.index)})


def real_average(data: Data) -> pd.DataFrame | None:
    """The average pension, as published and after consumer prices, first year = 100."""
    average, cpi = _clean(data, "pension_avg_total_annual"), _clean(data, "cpi_index")
    if average is None or cpi is None:
        return None
    average = _by_year(average)
    prices = _yearly_mean(cpi).reindex(average.index)
    out = pd.DataFrame({"nominal": average, "real": average / prices}).dropna()
    return None if out.empty else out / out.iloc[0] * 100


def workers_per_pension(data: Data) -> tuple[pd.Series, pd.Series] | None:
    """Registered workers per pension: yearly (annual averages) and monthly."""
    workers, number = _clean(data, "afiliados"), _clean(data, "pensions_total_annual")
    if workers is None or number is None:
        return None
    yearly = (_yearly_mean(workers) / _by_year(number)).dropna()
    monthly_n = _clean(data, "pensions_total")
    monthly = (workers / monthly_n).dropna() if monthly_n is not None else pd.Series(dtype=float)
    return yearly, monthly


# ---------------------------------------------------------------- facts

def overview_facts(data: Data) -> list[dict]:
    out = []
    number, average = _clean(data, "pensions_total"), _clean(data, "pension_avg_total")
    if number is not None:
        before = _year_back(number)
        out.append({"label": "Contributory pensions", "value": f"{number.iloc[-1] / 1000:.2f} million",
                    "sub": f"on the 1st of {period_label(number.index[-1], 'M')}"
                           + (f" · {fmt_change((number.iloc[-1] / before - 1) * 100, '%', 1)} on a year" if before else "")})
    if average is not None:
        before = _year_back(average)
        retirement = _clean(data, "pension_avg_retirement")
        out.append({"label": "Average pension", "value": f"€{average.iloc[-1]:,.2f}",
                    "sub": f"a month, {period_label(average.index[-1], 'M')}"
                           + (f" · {fmt_change((average.iloc[-1] / before - 1) * 100, '%', 1)} on a year" if before else "")
                           + (f"; retirement €{retirement.iloc[-1]:,.2f}" if retirement is not None else "")})
    cost = annual_cost(data)
    if cost is not None and not cost.empty:
        year = cost.index[-1]
        share = cost["share"].iloc[-1]
        out.append({"label": "What they cost", "value": f"€{cost['cost'].iloc[-1] / 1000:.0f} bn",
                    "sub": f"in {year}, an estimate: pensions × the average pension × {PAYMENTS} payments"
                           + ("" if pd.isna(share) else f"; {share:.1f}% of GDP")})
    ratio = workers_per_pension(data)
    if ratio is not None:
        yearly, monthly = ratio
        latest, label = (monthly, period_label(monthly.index[-1], "M")) if not monthly.empty else (yearly, str(yearly.index[-1]))
        out.append({"label": "Workers per pension", "value": f"{latest.iloc[-1]:.2f}",
                    "sub": f"registered with the Social Security, {label}"
                           + (f"; {yearly.iloc[0]:.2f} in {yearly.index[0]}" if not yearly.empty else "")})
    return out


def new_facts(data: Data) -> list[dict]:
    out = []
    new, in_force = _clean(data, "new_pension_avg_retirement"), _clean(data, "pension_avg_retirement")
    if new is not None:
        same = in_force.get(new.index[-1]) if in_force is not None else None
        gap = f" · {fmt_change((new.iloc[-1] / same - 1) * 100, '%', 1)} on the average retirement pension" if same else ""
        out.append({"label": "A new retirement pension", "value": f"€{new.iloc[-1]:,.0f}",
                    "sub": f"a month, granted in {period_label(new.index[-1], 'M')}{gap}"})
    ended = _clean(data, "ended_pension_avg_retirement")
    if ended is not None:
        out.append({"label": "A retirement pension that ends", "value": f"€{ended.iloc[-1]:,.0f}",
                    "sub": f"a month, {period_label(ended.index[-1], 'M')}: newer pensions replace smaller ones"})
    for ind_id, label in (("new_pensions_total", "Pensions granted"), ("ended_pensions_total", "Pensions ended")):
        s = _clean(data, ind_id)
        if s is None:
            continue
        window = s.rolling(12, min_periods=12).sum().dropna() if len(s) >= 12 else None
        if window is not None and not window.empty:
            out.append({"label": label, "value": f"{window.iloc[-1]:,.0f}k",
                        "sub": f"past 12 months, to {period_label(window.index[-1], 'M')}"})
    return out


def limits_facts(data: Data) -> list[dict]:
    out = []
    for ind_id, label, sub in (("pension_max", "Maximum pension", "a month"),
                               ("pension_min_spouse", "Minimum, with a dependent spouse", "a month, retirement at 65"),
                               ("pension_min_single", "Minimum, living alone", "a month, retirement at 65")):
        s = _clean(data, ind_id)
        if s is None:
            continue
        before = _year_back(s)
        out.append({"label": label, "value": f"€{s.iloc[-1]:,.2f}",
                    "sub": f"{sub}, {s.index[-1].year}"
                           + (f" · {fmt_change((s.iloc[-1] / before - 1) * 100, '%', 1)} on a year" if before else "")})
    return out


# ---------------------------------------------------------------- tables

def _measure_columns(n_header: str, a_header: str) -> list[PanelColumn]:
    return [PanelColumn("n", n_header), PanelColumn("n", "y/y %", col=Change("y/y", 12)),
            PanelColumn("a", a_header), PanelColumn("a", "y/y %", col=Change("y/y", 12))]


CLASS_TABLE = Panel(
    title="Class",
    caption="Pensions in force on the first of the month",
    columns=_measure_columns("Pensions, thousands", "Average, € a month"),
    rows=[PanelRow(label, {"n": f"pensions_{c}", "a": f"pension_avg_{c}"}, highlight=c == "total", indent=0 if c == "total" else 1)
          for c, label in CLASSES],
    note=("Widowhood pensions go mostly to women; family-support pensions, under 50,000, are counted in the total but "
          "not shown. Source: Ministry of Labour, Boletín de Estadísticas Laborales (table PEN-1), from Social "
          "Security records."),
)

SCHEME_TABLE = Panel(
    title="Scheme",
    caption="Pensions in force on the first of the month",
    columns=_measure_columns("Pensions, thousands", "Average, € a month"),
    rows=[PanelRow(label, {"n": f"pensions_scheme_{s}", "a": f"pension_avg_scheme_{s}"}) for s, label in SCHEMES],
    note=("Schemes (regímenes) group workers by how they paid in. Farm workers and domestic employees joined the "
          "General scheme in 2012. Pensions for work accidents and occupational diseases are counted apart from the "
          "scheme the worker belonged to. SOVI pays the old-age insurance in force before 1967 (table PEN-2)."),
)

REGION_TABLE = Panel(
    title="Region",
    caption="Pensions in force on the first of the month",
    columns=[PanelColumn("n", "Pensions, thousands"), PanelColumn("a", "Average, € a month"),
             PanelColumn("a", "y/y %", col=Change("y/y", 12)), PanelColumn("r", "Average retirement, € a month")],
    rows=[PanelRow(label, {"n": f"pensions_reg_{s}", "a": f"pension_avg_reg_{s}", "r": f"retirement_avg_reg_{s}"})
          for s, label in REGIONS],
    note=("Where the pensioner lives. Average pensions follow past pay: highest in the País Vasco, Asturias and "
          "Madrid, lowest in Extremadura and Galicia (tables PEN-19, PEN-20 and PEN-24)."),
)

LIMITS_TABLE = Panel(
    title="Amount",
    caption="€ a month, of 14 payments a year",
    columns=[PanelColumn("v", "This year"), PanelColumn("v", "A year earlier", col=Level("year")),
             PanelColumn("v", "Change, %", transform="yoy")],
    rows=[PanelRow("Maximum pension", {"v": "pension_max"}),
          PanelRow("Minimum retirement pension at 65: with a dependent spouse", {"v": "pension_min_spouse"}),
          PanelRow("Living alone", {"v": "pension_min_single"}, indent=1),
          PanelRow("With a spouse who is not dependent", {"v": "pension_min_other"}, indent=1)],
    note=("Set each year in the budget and published a year (table PEN-31); shown here over the 14 payments. Pensions "
          "below the minimum are topped up (complemento a mínimos) for pensioners whose other income is low."),
)


# ---------------------------------------------------------------- charts

def _years(index) -> list[str]:
    return [f"{y}-01-01" for y in index]


def cost_chart(data: Data) -> dict | None:
    cost = annual_cost(data)
    if cost is None or cost["share"].dropna().empty:
        return None
    share = cost["share"].dropna()
    return {"id": "pension-cost", "title": "What contributory pensions cost", "kind": "bar", "unit": "%", "decimals": 1,
            "subtitle": f"% of GDP, an estimate: pensions × the average pension × {PAYMENTS} payments",
            "freq": "A", "source": f"{SOURCE}, Eurostat; EconPulse calculation",
            "series": [{"name": "Contributory pensions", "x": _years(share.index), "y": share.round(2).tolist()}]}


def real_chart(data: Data) -> dict | None:
    real = real_average(data)
    if real is None:
        return None
    first = real.index[0]
    return {"id": "pension-real", "title": "The average pension and prices", "kind": "line", "unit": "", "decimals": 1,
            "subtitle": f"Average pension, annual average, {first} = 100: as paid, and after consumer prices",
            "freq": "A", "source": f"{SOURCE}, INE; EconPulse calculation",
            "ref_lines": [{"y": 100, "label": str(first)}],
            "series": [{"name": "As paid", "x": _years(real.index), "y": real["nominal"].round(2).tolist()},
                       {"name": "After inflation", "x": _years(real.index), "y": real["real"].round(2).tolist()}]}


def workers_chart(data: Data) -> dict | None:
    ratio = workers_per_pension(data)
    if ratio is None or ratio[0].empty:
        return None
    yearly = ratio[0]
    return {"id": "workers-per-pension", "title": "Workers per pension", "kind": "line", "unit": "", "decimals": 2,
            "subtitle": "Registered workers per contributory pension, annual averages",
            "freq": "A", "source": f"Seguridad Social, {SOURCE}; EconPulse calculation",
            "series": [{"name": "Workers per pension", "x": _years(yearly.index), "y": yearly.round(3).tolist()}]}
