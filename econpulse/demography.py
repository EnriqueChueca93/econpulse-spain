"""Who works, and participation in an ageing population (Labour page).

The labour-force rates by age, sex, citizenship and education are Eurostat's (labour force survey,
quarterly, not seasonally adjusted). Participation and employment at a fixed age mix are an EconPulse
calculation from Eurostat's population counts by sex and age (sources/ageing.py).
"""

from . import transforms
from .snapshot import fmt_change, fmt_value, period_label
from .sources.ageing import BASE_YEAR
from .tables import Data, Heading, Move, Panel, PanelColumn, PanelRow


def _group(label: str, slug: str, indent: int = 1) -> PanelRow:
    ids = {"act": f"lfs_act_{slug}", "emp": f"lfs_emp_{slug}", "une": f"lfs_une_{slug}"}
    return PanelRow(label, {**ids, "emp_chg": ids["emp"], "une_chg": ids["une"]}, indent=indent)


GROUPS = Panel(
    title="Group",
    caption="% of each group's population (participation, employment) or labour force (unemployment)",
    columns=[PanelColumn("act", "Participation"), PanelColumn("emp", "Employment rate"),
             PanelColumn("emp_chg", "Employment, 1-yr change", col=Move("1-yr", "year")),
             PanelColumn("une", "Unemployment rate"),
             PanelColumn("une_chg", "Unemployment, 1-yr change", col=Move("1-yr", "year"))],
    rows=[_group("All, 15–64", "all", 0),
          Heading("By age"), _group("15–24", "young"), _group("25–54 (prime age)", "prime"), _group("55–64", "older"),
          Heading("By sex, 15–64"), _group("Men", "men"), _group("Women", "women"),
          Heading("By sex, 25–54"), _group("Men", "prime_men"), _group("Women", "prime_women"),
          Heading("By citizenship, 15–64"), _group("Spanish", "spanish"),
          _group("Other EU countries", "eu"), _group("Countries outside the EU", "noneu"),
          Heading("By education, 25–64"), _group("Lower secondary at most", "edu_low"),
          _group("Upper secondary", "edu_mid"), _group("Tertiary", "edu_high")],
    note=("Eurostat's labour force survey (INE's EPA, on Eurostat's age bands: INE's own figures start at 16). "
          "Changes are on the same quarter a year earlier, in percentage points, as the figures are not seasonally "
          "adjusted. Rates for small groups, such as citizens of other EU countries, move more from one quarter to "
          "the next because fewer people are surveyed."),
)


def _avg(data: Data, ind_id: str):
    """The average of the past four quarters, or None."""
    s = data.raw(ind_id)
    if s is None or s.dropna().empty:
        return None
    s = transforms.apply("avg_1y", s.dropna(), "Q").dropna()
    return s if not s.empty else None


def _at(s, year: int) -> float | None:
    """The average of a year's four quarters (the four-quarter average at its last quarter)."""
    v = s[s.index.year == year]
    return float(v.iloc[-1]) if len(v) and v.index[-1].month == 10 else None


def ageing_facts(data: Data) -> list[dict]:
    actual, adjusted = _avg(data, "lfs_participation"), _avg(data, "lfs_participation_aged")
    if actual is None or adjusted is None:
        return []
    date = actual.index[-1]
    now, at_base = float(actual.iloc[-1]), float(adjusted.get(date, float("nan")))
    out = [{"label": "Participation, 15 and over", "value": fmt_value(now, "%", 1),
            "sub": f"average of the four quarters to {period_label(date, 'Q')}"},
           {"label": f"At the {BASE_YEAR} age mix", "value": fmt_value(at_base, "%", 1),
            "sub": f"each age group's rate today, weighted as in {BASE_YEAR}"},
           {"label": f"Effect of ageing since {BASE_YEAR}", "value": fmt_change(now - at_base, "pp", 1),
            "sub": "on the participation rate"}]
    old = _avg(data, "lfs_share_65plus")
    if old is not None and _at(old, BASE_YEAR) is not None:
        out.append({"label": "Aged 65 and over", "value": fmt_value(float(old.iloc[-1]), "%", 1),
                    "sub": f"of people 15 and over, from {fmt_value(_at(old, BASE_YEAR), '%', 1)} in {BASE_YEAR}"})
    return out


def ageing_callout(data: Data) -> str | None:
    """Whether the fall in participation since its peak comes from the age mix or from within age groups."""
    actual, adjusted = _avg(data, "lfs_participation"), _avg(data, "lfs_participation_aged")
    if actual is None or adjusted is None:
        return None
    peak_date = actual.idxmax()
    peak, now = float(actual.max()), float(actual.iloc[-1])
    then, today = adjusted.get(peak_date), adjusted.get(actual.index[-1])
    if then is None or today is None or peak - now < 0.3:
        return None
    text = (f"Participation of everyone aged 15 and over peaked at {fmt_value(peak, '%', 1)} in the four quarters to "
            f"{period_label(peak_date, 'Q')} and is {fmt_value(now, '%', 1)} now. At the {BASE_YEAR} age mix it would "
            f"have gone from {fmt_value(float(then), '%', 1)} to {fmt_value(float(today), '%', 1)}")
    if today > then:
        return text + ": the fall comes from the population's ageing; within age groups, participation has risen on balance."
    return text + ": participation within age groups has fallen too."
