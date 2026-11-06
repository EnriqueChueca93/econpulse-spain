"""The Pensions page's computed blocks: contributory pensions of the Social Security system (Batch 29a), and
their sustainability and comparisons (Batch 29b).

The figures come from the Ministry of Labour's statistics bulletin (tables PEN-1 to PEN-31, sources/bel.py):
monthly series of the pensions in force, new and ended pensions, by class, scheme and region, which start in
April 2025 and grow month by month; annual averages since 2016; and the maximum and minimum amounts since
1990. Macroscope adds three calculations: what pensions cost in a year (the average number of pensions times
the average pension times the 14 payments, against nominal GDP), the average pension after inflation, and
registered workers per pension.

Batch 29b compares Spain with its comparators (Eurostat, the OECD), shows the ageing population, and sets out
the 2023 reform and the official assessments, whose figures are entered by hand in pension_assessments.yaml.
Each document there is marked "awaiting AI check" until `python -m econpulse confirm <id>` records that an AI
compared its figures with the publisher's own text (data/pension_checks.json); changing a figure needs a new
check.

In Spanish (Batch 33c-2) the facts, charts, the comparison table and the document cards are written from the
catalogue (scripts/catalogue_pensions.py); the documents' own titles stay as published, and the "awaiting AI
check" status keeps its logic, only its words change.
"""

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import pandas as pd
import yaml

from . import i18n, peers
from .charts import localise
from .i18n import _
from .snapshot import fmt_change, fmt_value, period_label
from .sources.base import MADRID
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

def _on_a_year(now: float, before: float | None) -> str:
    """" · +1.6% on a year" (empty without a year-earlier figure)."""
    if not before:
        return ""
    return " · " + _("{change} on a year").format(change=fmt_change((now / before - 1) * 100, "%", 1))


def overview_facts(data: Data) -> list[dict]:
    out = []
    number, average = _clean(data, "pensions_total"), _clean(data, "pension_avg_total")
    if number is not None:
        out.append({"label": _("Contributory pensions"),
                    "value": _("{n} million").format(n=f"{number.iloc[-1] / 1000:.2f}"),
                    "sub": _("on the 1st of {month}").format(month=period_label(number.index[-1], "M"))
                           + _on_a_year(number.iloc[-1], _year_back(number))})
    if average is not None:
        retirement = _clean(data, "pension_avg_retirement")
        out.append({"label": _("Average pension"), "value": fmt_value(average.iloc[-1], "€", 2),
                    "sub": _("a month, {month}").format(month=period_label(average.index[-1], "M"))
                           + _on_a_year(average.iloc[-1], _year_back(average))
                           + (_("; retirement {amount}").format(amount=fmt_value(retirement.iloc[-1], "€", 2))
                              if retirement is not None else "")})
    cost = annual_cost(data)
    if cost is not None and not cost.empty:
        year = cost.index[-1]
        share = cost["share"].iloc[-1]
        everything = all_public_pensions(data)
        out.append({"label": _("What they cost"), "value": fmt_value(cost["cost"].iloc[-1] / 1000, "€ bn", 0),
                    "sub": _("in {year}, an estimate: pensions × the average pension × {payments} payments").format(
                               year=year, payments=PAYMENTS)
                           + ("" if pd.isna(share) else f"; {fmt_value(share, '% of GDP', 1)}")
                           + (f". {everything}" if everything else "")})
    ratio = workers_per_pension(data)
    if ratio is not None:
        yearly, monthly = ratio
        latest, label = (monthly, period_label(monthly.index[-1], "M")) if not monthly.empty else (yearly, str(yearly.index[-1]))
        out.append({"label": _("Workers per pension"), "value": f"{latest.iloc[-1]:.2f}",
                    "sub": _("registered with the Social Security, {period}").format(period=label)
                           + (_("; {ratio} in {year}").format(ratio=f"{yearly.iloc[0]:.2f}", year=yearly.index[0])
                              if not yearly.empty else "")})
    return out


def new_facts(data: Data) -> list[dict]:
    out = []
    new, in_force = _clean(data, "new_pension_avg_retirement"), _clean(data, "pension_avg_retirement")
    if new is not None:
        same = in_force.get(new.index[-1]) if in_force is not None else None
        month = period_label(new.index[-1], "M")
        sub = (_("a month, granted in {month} · {change} on the average retirement pension").format(
                   month=month, change=fmt_change((new.iloc[-1] / same - 1) * 100, "%", 1)) if same
               else _("a month, granted in {month}").format(month=month))
        out.append({"label": _("A new retirement pension"), "value": fmt_value(new.iloc[-1], "€", 0), "sub": sub})
    ended = _clean(data, "ended_pension_avg_retirement")
    if ended is not None:
        out.append({"label": _("A retirement pension that ends"), "value": fmt_value(ended.iloc[-1], "€", 0),
                    "sub": _("a month, {month}: newer pensions replace smaller ones").format(
                        month=period_label(ended.index[-1], "M"))})
    for ind_id, label in (("new_pensions_total", "Pensions granted"), ("ended_pensions_total", "Pensions ended")):
        s = _clean(data, ind_id)
        if s is None:
            continue
        window = s.rolling(12, min_periods=12).sum().dropna() if len(s) >= 12 else None
        if window is not None and not window.empty:
            out.append({"label": _(label), "value": f"{window.iloc[-1]:,.0f}k",
                        "sub": _("past 12 months, to {month}").format(month=period_label(window.index[-1], "M"))})
    return out


def limits_facts(data: Data) -> list[dict]:
    out = []
    for ind_id, label, sub in (("pension_max", "Maximum pension", "a month"),
                               ("pension_min_spouse", "Minimum, with a dependent spouse", "a month, retirement at 65"),
                               ("pension_min_single", "Minimum, living alone", "a month, retirement at 65")):
        s = _clean(data, ind_id)
        if s is None:
            continue
        out.append({"label": _(label), "value": fmt_value(s.iloc[-1], "€", 2),
                    "sub": f"{_(sub)}, {s.index[-1].year}" + _on_a_year(s.iloc[-1], _year_back(s))})
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
    # The static words are put into the language first (localise), then the figures added; "" keeps the key's place.
    spec = localise({"id": "pension-cost", "title": "What contributory pensions cost", "kind": "bar", "unit": "%",
                     "decimals": 1, "subtitle": "", "freq": "A",
                     "source": _("{source}, Eurostat; Macroscope calculation").format(source=SOURCE),
                     "series": [{"name": "Contributory pensions", "x": _years(share.index), "y": share.round(2).tolist()}]})
    spec["subtitle"] = _("% of GDP, an estimate: pensions × the average pension × {payments} payments").format(
        payments=PAYMENTS)
    return spec


def real_chart(data: Data) -> dict | None:
    real = real_average(data)
    if real is None:
        return None
    first = real.index[0]
    spec = localise({"id": "pension-real", "title": "The average pension and prices", "kind": "line", "unit": "",
                     "decimals": 1, "subtitle": "", "freq": "A",
                     "source": _("{source}, INE; Macroscope calculation").format(source=SOURCE), "ref_lines": [],
                     "series": [{"name": "As paid", "x": _years(real.index), "y": real["nominal"].round(2).tolist()},
                                {"name": "After inflation", "x": _years(real.index), "y": real["real"].round(2).tolist()}]})
    spec["subtitle"] = _("Average pension, annual average, {year} = 100: as paid, and after consumer prices").format(
        year=first)
    spec["ref_lines"] = [{"y": 100, "label": str(first)}]
    return spec


def workers_chart(data: Data) -> dict | None:
    ratio = workers_per_pension(data)
    if ratio is None or ratio[0].empty:
        return None
    yearly = ratio[0]
    return {"id": "workers-per-pension", "title": "Workers per pension", "kind": "line", "unit": "", "decimals": 2,
            "subtitle": "Registered workers per contributory pension, annual averages",
            "freq": "A", "source": _("Seguridad Social, {source}; Macroscope calculation").format(source=SOURCE),
            "series": [{"name": "Workers per pension", "x": _years(yearly.index), "y": yearly.round(3).tolist()}]}


# ---------------------------------------------------------------- sustainability and comparisons (Batch 29b)

DOCS_FILE = Path(__file__).with_name("pension_assessments.yaml")
CHECKS = "pension_checks"             # data/pension_checks.json
CHECKED, PENDING = "AI-checked", "awaiting AI check"
EU_AREAS = [("es", "Spain"), ("fr", "France"), ("de", "Germany"), ("it", "Italy"), ("nl", "Netherlands"),
            ("pt", "Portugal"), ("pl", "Poland"), ("eu", "EU")]
COMPARISON_USES = ([f"pension_spending_{s}" for s, _name in EU_AREAS] + [f"ss_balance_{s}" for s, _name in EU_AREAS]
                   + [f"old_age_dep_{s}" for s, _name in EU_AREAS] + [f"old_age_dep_proj_{s}" for s, _name in EU_AREAS]
                   + [f"public_pensions_{s}" for s, _name in peers.COUNTRIES if s != "ea"]
                   + [f"replacement_rate_{s}" for s, _name in peers.COUNTRIES if s != "ea"])


@dataclass
class Document:
    """A document whose figures were entered by hand (pension_assessments.yaml)."""
    id: str
    publisher: str
    title: str
    short: str
    published: str
    url: str
    figures: list
    raw: dict
    status: str = PENDING
    check: dict | None = None


def fingerprint(raw: dict) -> str:
    """Identifies a document's figures: any change to them needs a new check."""
    return hashlib.sha256(json.dumps(raw, sort_keys=True, ensure_ascii=False, default=str).encode()).hexdigest()[:12]


def documents(store, path: Path = DOCS_FILE) -> list[Document]:
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    checks = store.load_json(CHECKS, {}) if store is not None else {}
    out = []
    for d in raw.get("documents") or []:
        doc = Document(id=d["id"], publisher=d["publisher"], title=d["title"], short=d.get("short", d["title"]),
                       published=str(d.get("published", "")), url=d["url"], figures=d.get("figures") or [], raw=d)
        record = checks.get(doc.id)
        if record and record.get("fingerprint") == fingerprint(d):
            doc.status, doc.check = CHECKED, record
        out.append(doc)
    return out


def confirm(store, doc_id: str, by: str, note: str = "", against: str = "") -> dict:
    """Record that an AI compared this document's figures with the publisher's own text."""
    doc = next((d for d in documents(store) if d.id == doc_id), None)
    if doc is None:
        raise ValueError(f"no pension document {doc_id!r}")
    checks = store.load_json(CHECKS, {})
    record = {"fingerprint": fingerprint(doc.raw), "checked_by": by,
              "checked_at": datetime.now(MADRID).strftime("%Y-%m-%d %H:%M")}
    if against:
        record["checked_against"] = against
    if note:
        record["note"] = note
    checks[doc_id] = record
    store.save_json(CHECKS, dict(sorted(checks.items())))
    return record


def document_ids(path: Path = DOCS_FILE) -> set[str]:
    return {d["id"] for d in (yaml.safe_load(path.read_text(encoding="utf-8")) or {}).get("documents") or []}


def _date_text(text: str) -> str:
    """A date as the yaml or the check record writes it ("17 Mar 2023", "Apr 2024", "2024", "2026-11-02"), in the
    language being written: as it is in English, "17 mar 2023", "abr 2024", "2 nov 2026" in Spanish."""
    if i18n.lang() == "en" or not text or text.isdigit():
        return text
    try:
        d = pd.Timestamp(text)
    except ValueError:
        return text
    if pd.isna(d):
        return text
    return i18n.month_year(d) if len(text.split()) == 2 else i18n.day_month_year(d)


def _figure(f: dict) -> dict:
    """A document's figure as the site describes it, in the language being written (a copy: the raw figures are
    what the check's fingerprint covers)."""
    return {k: _(v) if k in ("label", "value", "where") and isinstance(v, str) else v for k, v in f.items()}


def _card(doc: Document) -> dict:
    check = ""
    if doc.check:
        by, when = _(doc.check["checked_by"]), _date_text(doc.check["checked_at"][:10])
        if doc.check.get("checked_against"):
            check = _("Checked by {by} on {date} against {against}.").format(
                by=by, date=when, against=_(doc.check["checked_against"]))
        else:
            check = _("Checked by {by} on {date}.").format(by=by, date=when)
        if doc.check.get("note"):
            check += " " + _(doc.check["note"])
    # The documents' own titles stay as published; i18n.maybe only puts into Spanish what the site added to one.
    return {"id": doc.id, "publisher": _(doc.publisher), "title": i18n.maybe(doc.title), "short": _(doc.short),
            "published": _date_text(doc.published), "url": doc.url, "figures": [_figure(f) for f in doc.figures],
            "status": _(doc.status), "pending": doc.status == PENDING, "check_note": check}


def _doc(data: Data, doc_id: str) -> Document | None:
    docs = data.cache.get("pension_documents")
    if docs is None:
        docs = data.cache["pension_documents"] = documents(data.store)
    return next((d for d in docs if d.id == doc_id), None)


def reform_documents(data: Data) -> list[dict]:
    doc = _doc(data, "reform2023")
    return [_card(doc)] if doc else []


def assessment_documents(data: Data) -> list[dict]:
    return [_card(d) for i in ("ageing_report_2024", "airef_2026", "airef_2025", "bde_2023") if (d := _doc(data, i))]


def _status_note(doc: Document) -> str:
    return f" · {_(PENDING)}" if doc.status == PENDING else ""


def all_public_pensions(data: Data) -> str:
    """What the cost of the Social Security's contributory pensions leaves out, for the fact beside it: all public
    pensions, with civil servants' (Clases Pasivas, 1.4% of GDP in 2022) and non-contributory ones (0.2%), in the
    Ageing Report's base year. Readers compare the two (11.3% against 13.1%)."""
    doc = _doc(data, "ageing_report_2024")
    proj = (doc.raw.get("projection") if doc else None) or {}
    if not proj.get("years") or not proj.get("es"):
        return ""
    return _("Social Security only; with civil servants' (Clases Pasivas) and non-contributory pensions, {share} of "
             "GDP in {year} ({source})").format(
        share=fmt_value(proj["es"][0], "%", 1), year=proj["years"][0], source=_(doc.publisher)) + _status_note(doc)


# ---------------------------------------------------------------- comparisons

def _last(data: Data, ind_id: str) -> tuple[float, int] | None:
    s = _clean(data, ind_id)
    return None if s is None else (float(s.iloc[-1]), s.index[-1].year)


def _at(data: Data, ind_id: str, year: int) -> float | None:
    s = _clean(data, ind_id)
    if s is None:
        return None
    v = s.get(pd.Timestamp(year, 1, 1))
    return None if v is None or pd.isna(v) else float(v)


# Spain's place among the countries, from the top: whole phrases, so that Spanish can agree them ("la tercera más alta").
_RANKS = {1: "the highest of the {n} countries", 2: "the second highest of the {n} countries",
          3: "the third highest of the {n} countries", 4: "the fourth highest of the {n} countries",
          5: "the fifth highest of the {n} countries"}


def _rank(rank: int, n: int) -> str:
    return _(_RANKS.get(rank, "the {rank}th highest of the {n} countries")).format(rank=rank, n=n)


def comparison_facts(data: Data) -> list[dict]:
    out = []
    es, eu = _last(data, "pension_spending_es"), _last(data, "pension_spending_eu")
    if es:
        out.append({"label": _("Pension spending"), "value": fmt_value(es[0], "% of GDP", 1),
                    "sub": (_("all pensions, {year}; EU {eu} (Eurostat)") if eu else _("all pensions, {year} (Eurostat)"))
                           .format(year=es[1], eu=fmt_value(eu[0], "%", 1) if eu else "")})
    rates = {s: v for s, _unused in peers.COUNTRIES if s != "ea" and (v := _last(data, f"replacement_rate_{s}"))}
    if "es" in rates:
        rank = sorted(rates, key=lambda s: -rates[s][0]).index("es") + 1
        out.append({"label": _("Replacement rate"), "value": fmt_value(rates["es"][0], "%", 1),
                    "sub": _("of net pay, for an average earner (OECD, {year}); {rank}").format(
                        year=rates["es"][1], rank=_rank(rank, len(rates)))})
    bal, eu_bal = _last(data, "ss_balance_es"), _last(data, "ss_balance_eu")
    if bal:
        out.append({"label": _("Social security funds' balance"), "value": fmt_change(bal[0], "% of GDP", 1),
                    "sub": _("{year}; EU {eu} (Eurostat)").format(year=bal[1], eu=fmt_change(eu_bal[0], "%", 1))
                           if eu_bal else f"{bal[1]} (Eurostat)"})
    return out


def comparison_table(data: Data) -> dict | None:
    if _last(data, "replacement_rate_es") is None and _last(data, "pension_spending_es") is None:
        return None
    spend_year = (_last(data, "pension_spending_es") or (0, None))[1]
    oecd_year = (_last(data, "public_pensions_es") or (0, None))[1]
    dep_year = (_last(data, "old_age_dep_es") or (0, None))[1]

    def cell(ind_id, year=None, usual=None):
        if year is not None:
            v = _at(data, ind_id, year)
            return "–" if v is None else fmt_value(v, "", 1).strip()
        last = _last(data, ind_id)
        if last is None:
            return "–"
        text = fmt_value(last[0], "", 1).strip()
        return text if usual is None or last[1] == usual else {"value": text, "note": str(last[1])}

    rows = []
    for slug, label in [*[(s, l) for s, l in peers.COUNTRIES if s != "ea"], ("eu", "EU")]:
        rows.append({"heading": False, "label": _(label), "label_es": "", "indent": 0, "period_note": "", "url": None,
                     "highlight": slug == "es",
                     "cells": [cell(f"pension_spending_{slug}", usual=spend_year),
                               cell(f"public_pensions_{slug}", usual=oecd_year),
                               cell(f"replacement_rate_{slug}"),
                               cell(f"old_age_dep_{slug}", usual=dep_year),
                               cell(f"old_age_dep_proj_{slug}", year=2050)]})
    return {"title": _("Country"), "caption": _("Pensions and ageing"), "through": "",
            "columns": [_("Pension spending, % of GDP"), _("Public pensions, % of GDP"), _("Replacement rate, %"),
                        _("65+ per 100 aged 15-64"), _("Same, 2050")],
            "column_notes": [f"Eurostat, {spend_year}" if spend_year else "Eurostat",
                             _("OECD, {year}").format(year=oecd_year) if oecd_year else _("OECD"),
                             _("OECD, net"), f"Eurostat, {dep_year}" if dep_year else "Eurostat", _("projected")],
            "rows": rows,
            "note": _("Pension spending (Eurostat) covers all pensions, public and private, including disability; public "
                      "pensions (OECD) cover public old-age and survivors' pensions only, and come a few years late. The "
                      "replacement rate is what a man on the average wage who starts work at 22 would get from mandatory "
                      "schemes, as % of his net pay before retiring. Eurostat covers EU countries only.")}


def _ranking(id_, title, subtitle, unit, decimals, year, points, source) -> dict | None:
    """A ranking of countries drawn by peers._hbar, whose subtitle ends in the year: its words are put into the
    language before the year is added (unless _hbar has done so itself)."""
    date = pd.Timestamp(year, 1, 1)
    spec = peers._hbar(id_, title, subtitle, unit, decimals, date, "A", points, source=source)
    if spec is not None and spec.get("lang") != i18n.lang():
        spec["subtitle"] = subtitle
        localise(spec)
        spec["subtitle"] = f"{spec['subtitle']} · {period_label(date, 'A')}"
    return spec


def replacement_ranking(data: Data) -> dict | None:
    points = {s: v for s, _unused in peers.COUNTRIES if s != "ea" and (v := _last(data, f"replacement_rate_{s}"))}
    if "es" not in points:
        return None
    return _ranking("replacement-ranking", "Pension replacement rates", "Net, for an average earner, % of net pay",
                    "%", 1, points["es"][1], [(peers.LABELS[s], v[0]) for s, v in points.items()],
                    source=_("OECD, Pensions at a Glance"))


def public_pensions_ranking(data: Data) -> dict | None:
    points = {s: v for s, _unused in peers.COUNTRIES if s != "ea" and (v := _last(data, f"public_pensions_{s}"))}
    if "es" not in points:
        return None
    spec = _ranking("public-pensions-ranking", "Public spending on pensions",
                    "Old-age and survivors' pensions, % of GDP", "%", 1, points["es"][1],
                    [(peers.LABELS[s], v[0]) for s, v in points.items()], source=_("OECD, Social Expenditure Database"))
    years = sorted({v[1] for v in points.values()})
    if spec and len(years) > 1:
        spec["subtitle"] = _("Old-age and survivors' pensions, % of GDP, latest year ({first}-{last})").format(
            first=years[0], last=years[-1])
    return spec


def dependency_chart(data: Data) -> dict | None:
    series, projected = [], []
    for slug, name, style in (("es", "Spain", {"color": "ink"}), ("eu", "EU", {"slot": 1})):
        past, future = _clean(data, f"old_age_dep_{slug}"), _clean(data, f"old_age_dep_proj_{slug}")
        if past is None:
            continue
        series.append({"name": name, "x": [d.strftime("%Y-%m-%d") for d in past.index], "y": past.round(2).tolist(), **style})
        if future is not None:
            future = future[future.index > past.index[-1]]
            projected.append(len(series))
            series.append({"name": name, "x": [d.strftime("%Y-%m-%d") for d in future.index],
                           "y": future.round(2).tolist(), "dash": "dot", **style})
    if not series:
        return None
    spec = localise({"id": "old-age-dependency", "title": "Old-age dependency ratio", "kind": "line", "unit": "",
                     "decimals": 1, "subtitle": "People aged 65 and over per 100 aged 15-64; dotted, Eurostat's projection",
                     "freq": "A", "source": _("Eurostat (EUROPOP2023 projections)"), "series": series})
    for i in projected:                           # the country's name in the language, then "projected"
        series[i]["name"] = _("{name}, projected").format(name=series[i]["name"])
    return spec


def dependency_ranking(data: Data) -> dict | None:
    points = [(label, v) for s, label in EU_AREAS if (v := _at(data, f"old_age_dep_proj_{s}", 2050)) is not None]
    if not any(label == "Spain" for label, _unused in points):
        return None
    return _ranking("dependency-2050-ranking", "Old-age dependency in 2050", "65+ per 100 aged 15-64, projected",
                    "", 1, 2050, points, source=_("Eurostat (EUROPOP2023 projections)"))


def ageing_facts(data: Data) -> list[dict]:
    out = []
    now, eu = _last(data, "old_age_dep_es"), _last(data, "old_age_dep_eu")
    if now:
        out.append({"label": _("People 65+ per 100 aged 15-64"), "value": f"{now[0]:.1f}",
                    "sub": _("{year}; EU {eu}").format(year=now[1], eu=f"{eu[0]:.1f}") if eu else f"{now[1]}"})
    y2050, eu2050 = _at(data, "old_age_dep_proj_es", 2050), _at(data, "old_age_dep_proj_eu", 2050)
    if y2050 is not None:
        out.append({"label": _("In 2050, projected"), "value": f"{y2050:.1f}",
                    "sub": _("Eurostat's baseline; EU {eu}").format(eu=f"{eu2050:.1f}") if eu2050 is not None
                           else _("Eurostat's baseline")})
    return out


# ---------------------------------------------------------------- outlook and the reform (figures entered by hand)

def _with_status(spec: dict, subtitle: str, doc: Document) -> dict:
    """A chart of figures entered by hand: its words in the language, then the subtitle and the document's status."""
    localise(spec)
    spec["subtitle"] = _(subtitle) + _status_note(doc)
    return spec


def projection_chart(data: Data) -> dict | None:
    doc = _doc(data, "ageing_report_2024")
    proj = (doc.raw.get("projection") if doc else None) or {}
    years = proj.get("years")
    if not years or "es" not in proj:
        return None
    labels = dict(peers.COUNTRIES)
    series = [{"name": labels[s], "x": _years(years), "y": proj[s], "country": s} for s in proj if s in labels]
    return _with_status({"id": "pension-projection", "title": "Projected pension spending", "subtitle": "",
                         "kind": "line", "unit": "%", "decimals": 1, "freq": "A", "pick": True,
                         "source": _("European Commission, 2024 Ageing Report (Table II.1.64), entered by hand"),
                         "series": series},
                        "Gross public pension spending, % of GDP, European Commission 2024 Ageing Report", doc)


def balance_chart(data: Data) -> dict | None:
    series = []
    for slug, name, style in (("es", "Spain", {"color": "ink"}), ("eu", "EU", {})):
        s = _clean(data, f"ss_balance_{slug}")
        if s is not None:
            series.append({"name": name, "x": [d.strftime("%Y-%m-%d") for d in s.index], "y": s.round(2).tolist(), **style})
    if not series:
        return None
    return {"id": "ss-balance", "title": "Social security funds' balance", "kind": "line", "unit": "%", "decimals": 1,
            "subtitle": "Net lending (+) or borrowing (−), % of GDP", "freq": "A", "source": "Eurostat",
            "ref_lines": [{"y": 0, "label": "Balance"}], "series": series}


def mei_chart(data: Data) -> dict | None:
    doc = _doc(data, "reform2023")
    mei = (doc.raw.get("mei") if doc else None) or {}
    if not mei:
        return None
    years = [y for y in sorted(mei) if y < 2050]
    return _with_status({"id": "mei", "title": "The intergenerational equity contribution (MEI)", "kind": "bar",
                         "unit": "", "decimals": 1, "freq": "A",
                         "source": _("Real Decreto-ley 2/2023, entered by hand"), "subtitle": "",
                         "series": [{"name": "MEI", "x": _years(years), "y": [mei[y] for y in years]}]},
                        "Points of pay, employer and worker together; 1.2 from 2029 to 2050", doc)


def solidarity_chart(data: Data) -> dict | None:
    doc = _doc(data, "reform2023")
    sol = (doc.raw.get("solidarity") if doc else None) or {}
    if not sol:
        return None
    years = sorted(sol)
    bands = ["Up to 10% above the base", "10-50% above", "Over 50% above"]
    return _with_status({"id": "solidarity", "title": "The solidarity contribution", "kind": "line", "unit": "%",
                         "decimals": 2, "subtitle": "", "freq": "A",
                         "source": _("Real Decreto-ley 2/2023, entered by hand"),
                         "series": [{"name": name, "x": _years(years), "y": [sol[y][i] for y in years]}
                                    for i, name in enumerate(bands)]},
                        "% of pay above the maximum contribution base, by band", doc)
