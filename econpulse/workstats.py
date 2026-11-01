"""Hours, vacancies and pay by activity, and collective dismissals and temporary layoffs (Labour and Wages pages).

Hours worked per worker, job vacancies and wage cost per worker by CNAE-09 section come from INE's labour
cost survey (ETCL, quarterly, not seasonally adjusted); hours per person employed from the national
accounts; the workers affected by collective dismissals and temporary layoffs (ERE and ERTE) from the
Ministry of Labour (sources/reg.py).
"""

from . import transforms
from .snapshot import fmt_change, fmt_value, period_label
from .tables import Data, Heading, Row

# (slug, label): the indicator ids are hours_<slug>, vacancies_<slug> and pay_<slug>.
SECTIONS = [("mining", "Mining"), ("manufacturing", "Manufacturing"), ("energy", "Electricity and gas"),
            ("water", "Water and waste"), ("construction", "Construction"), ("trade", "Trade"),
            ("transport", "Transport and storage"), ("hospitality", "Hospitality"),
            ("information", "Information and IT"), ("finance", "Finance and insurance"),
            ("real_estate", "Real estate"), ("professional", "Professional services"),
            ("administrative", "Administrative services"), ("public_admin", "Public administration"),
            ("education", "Education"), ("health", "Health and social work"), ("arts", "Arts and recreation"),
            ("other_services", "Other services")]
# INE leaves out these sections' vacancies in many quarters.
NO_VACANCIES = {"mining", "energy", "water", "real_estate"}


def items(prefix: str, transform: str) -> list[tuple]:
    """Ranking items (indicator id, label, transform) for every section with this measure."""
    skip = NO_VACANCIES if prefix == "vacancies" else set()
    return [(f"{prefix}_{slug}", label, transform) for slug, label in SECTIONS if slug not in skip]


def rows(prefix: str, transform: str = "level") -> list[Row]:
    skip = NO_VACANCIES if prefix == "vacancies" else set()
    return [Row(f"{prefix}_{slug}", label, indent=1, transform=transform, flow=False)
            for slug, label in SECTIONS if slug not in skip]


def _avg(data: Data, ind_id: str):
    s = data.raw(ind_id)
    if s is None or s.dropna().empty:
        return None
    s = transforms.apply("avg_1y", s.dropna(), data.by_id[ind_id].freq).dropna()
    return s if not s.empty else None


def hours_callout(data: Data) -> str | None:
    """Hours lost to sick leave against 2019, and as a share of the hours worked."""
    sick, worked = _avg(data, "hours_sick"), _avg(data, "hours_etcl")
    if sick is None or worked is None:
        return None
    before = sick[sick.index.year == 2019]
    if before.empty or before.index[-1].month != 10:
        return None
    now, then = float(sick.iloc[-1]), float(before.iloc[-1])
    share = now / float(worked.get(sick.index[-1], float("nan"))) * 100
    text = (f"Sick leave took {fmt_value(now, 'hours', 1)} a month per employee in the four quarters to "
            f"{period_label(sick.index[-1], 'Q')}, against {fmt_value(then, 'hours', 1)} in 2019 "
            f"({fmt_change((now / then - 1) * 100, '%', 0)})")
    return text + (f", the equivalent of {fmt_value(share, '%', 1)} of the hours worked." if share == share else ".")


def pay_callout(data: Data) -> str | None:
    """The best- and worst-paid sections, past four quarters."""
    latest = {}
    for slug, label in SECTIONS:
        s = _avg(data, f"pay_{slug}")
        if s is not None:
            latest[label] = (float(s.iloc[-1]), s.index[-1])
    if len(latest) < 2:
        return None
    top = max(latest, key=lambda k: latest[k][0])
    low = min(latest, key=lambda k: latest[k][0])
    ratio = latest[top][0] / latest[low][0]
    return (f"In the four quarters to {period_label(latest[top][1], 'Q')}, pay per worker ranged from "
            f"{fmt_value(latest[low][0], '€', 0)} a month in {low.lower()} to {fmt_value(latest[top][0], '€', 0)} "
            f"in {top.lower()}, {ratio:.1f} times as much. Part of the gap reflects hours: part-time work is "
            "more common in the lower-paid activities.")


def ere_facts(data: Data) -> list[dict]:
    """Workers affected in the past 12 months, in total and by measure."""
    out = []
    for ind_id, label in (("ere_total", "Workers affected"), ("ere_dismissals", "Collective dismissals"),
                          ("ere_suspensions", "Contract suspensions"), ("ere_reductions", "Cuts in hours")):
        s = data.raw(ind_id)
        if s is None:
            continue
        total = transforms.apply("sum_1y", s.dropna(), "M").dropna()
        if total.empty:
            continue
        date = total.index[-1]
        year_ago = total.get(date.replace(year=date.year - 1))
        sub = f"12 months to {period_label(date, 'M')}"
        if year_ago:
            sub += f", {fmt_change((float(total.iloc[-1]) / float(year_ago) - 1) * 100, '%', 0)} on a year earlier"
        out.append({"label": label, "value": fmt_value(float(total.iloc[-1]), "thousands", 1), "sub": sub})
    return out


VACANCY_ROWS = [Row("vacancies", "All vacancies", transform="avg_1y", flow=False), Heading("By activity"),
                *rows("vacancies", "avg_1y")]
