"""Batch 33a: the Spanish version of the site and the language switch (no network)."""

import re
from pathlib import Path

import numpy as np
import pandas as pd

from econpulse import changes, i18n, industries, policy, trade, workstats
from econpulse.build import SECTION_PAGES, build_site
from econpulse.config import TEMPLATES_DIR
from econpulse.pages import PAGES, build_page
from econpulse.registry import Indicator, load_registry
from econpulse.snapshot import fmt_value, period_label
from econpulse.store import Store
from econpulse.tables import Data, Heading, Panel, Table

# The templates whose text is in Spanish (33a: the frame and the home page; 33b: the section pages); the
# others follow in 33c-33d.
SPANISH_TEMPLATES = ("base.html", "index.html", "calendar.html", "data.html", "404.html", "macros.html", "section.html")
# The section pages in Spanish from Batch 33b, 33c-1 and 33c-2 (all of them).
SPANISH_SECTIONS = ("gdp", "labour", "wages", "inflation", "financial", "ecb", "fiscal", "activity", "regions", "analysis",
                    "housing", "pensions", "international")


def test_every_marked_text_of_the_translated_pages_has_its_spanish():
    marked = set()
    for name in SPANISH_TEMPLATES:
        text = (TEMPLATES_DIR / name).read_text(encoding="utf-8")
        marked |= set(re.findall(r'_\("([^"]+)"', text))
        marked |= {s for pair in re.findall(r'ngettext\("([^"]+)", "([^"]+)"', text) for s in pair}
    missing = sorted(m for m in marked if m not in i18n.catalogue())
    assert not missing, missing
    assert (TEMPLATES_DIR / "es" / "about.html").exists()


def test_dates_and_figures_in_spanish():
    d = pd.Timestamp("2026-11-03")
    assert i18n.lang() == "en" and period_label(d, "M") == "Nov 2026" and period_label(d, "Q") == "Q4 2026"
    with i18n.using("es"):
        assert period_label(d, "D") == "3 nov 2026" and period_label(d, "M") == "nov 2026" and period_label(d, "Q") == "T4 2026"
        assert i18n.long_date(d) == "martes 3 de noviembre de 2026" and i18n.capital(i18n.long_month_year(d)) == "Noviembre de 2026"
        assert i18n.wd_day_mon(d) == "mar 3 nov"
        assert i18n.figures("0.6% q/q in Q3 2026, after 0.7% in Oct 2025") == "0.6% t/t in T3 2026, after 0.7% in oct 2025"
        assert i18n.figures("+465.5k y/y") == "+465.5k a/a" and i18n.figures("+1.2% m/m SA") == "+1.2% m/m desest."
        assert i18n.figures("29 May 2026") == "29 may 2026" and i18n.figures("in May") == "in may"
        assert fmt_value(1.25, "% of GDP", 1) == "1.2% del PIB" and fmt_value(12.0, "bp", 0) == "12 pb"   # numbers stay English
        assert i18n._("Inflation") == "Inflación" and i18n._("Nothing like this") == "Nothing like this"
        assert i18n.missing.get("Nothing like this")
    assert i18n._("Inflation") == "Inflation"


def test_logged_notes_are_rebuilt_in_spanish():
    gdp = Indicator(id="gdp", label="Real GDP", label_es="Producto interior bruto (volumen)", section="gdp", source="ine",
                    key="x", freq="Q", unit="index")
    note = {"kind": "release", "id": "gdp", "text": "Real GDP: 0.6% q/q in Q3 2026 (flash estimate), after 0.7% q/q in Q2 2026."}
    assert changes.note_text(note, gdp) == note["text"]
    with i18n.using("es"):
        assert changes.note_text(note, gdp) == ("Producto interior bruto (volumen): 0.6% t/t en T3 2026 (avance), "
                                                "tras 0.7% t/t en T2 2026.")
        revision = {"kind": "revision", "id": "gdp", "text": "Real GDP for Q2 2026 revised to 0.8% q/q, from 0.7% q/q."}
        assert changes.note_text(revision, gdp) == "Producto interior bruto (volumen), T2 2026: revisado a 0.8% t/t, desde 0.7% t/t."
        odd = {"kind": "release", "id": "gdp", "text": "Something else entirely."}
        assert changes.note_text(odd, gdp) == odd["text"]          # what cannot be taken apart stays as logged


def test_the_site_is_built_in_both_languages(tmp_path):
    store = Store(tmp_path / "data")
    q = pd.date_range("2015-01-01", "2026-07-01", freq="QS")
    store.save_series("gdp", pd.Series(100 * 1.005 ** np.arange(len(q)), index=q))
    build_site(load_registry(), store, site_dir=tmp_path / "site")
    site = tmp_path / "site"
    en, es = (site / "index.html").read_text(encoding="utf-8"), (site / "es" / "index.html").read_text(encoding="utf-8")
    assert '<html lang="en">' in en and '<html lang="es">' in es
    assert '<a class="brand" href="index.html">Macroscope <span>Spain</span></a>' in en
    assert '<a class="brand" href="index.html">Macroscope <span>España</span></a>' in es
    # The switch: each page links to its counterpart, the current language marked; assets are shared.
    assert 'href="es/index.html" hreflang="es"' in en and 'href="../index.html" hreflang="en"' in es
    assert 'hreflang="es" lang="es" title="Español" aria-current="true">ES</a>' in es
    assert 'href="../assets/style.css?v=' in es and not (site / "es" / "assets").exists()
    assert '<link rel="alternate" hreflang="es" href="https://enriquechueca93.github.io/macroscope-spain/es/index.html">' in en
    # Spanish text: the tabs, the official names of the series, Spanish periods.
    assert ">Inicio</a>" in es and ">Mercado laboral</a>" in es and "Indicadores clave" in es
    assert '<span class="tile-label">Producto interior bruto (volumen)</span>' in es and "T3 2026" in es
    assert '<span class="tile-label">Real GDP</span>' in en and "Q3 2026" in en
    for page in ("calendar.html", "data.html", "about.html", "inflation.html"):
        assert (site / "es" / page).exists(), page
    assert "<h1>Calendario de publicaciones</h1>" in (site / "es" / "calendar.html").read_text(encoding="utf-8")
    assert "<h1>Acerca de Macroscope España</h1>" in (site / "es" / "about.html").read_text(encoding="utf-8")
    assert "<h1>Datos y fuentes</h1>" in (site / "es" / "data.html").read_text(encoding="utf-8")
    assert not (site / "es" / "404.html").exists() and not (site / "es" / "feed.xml").exists()
    assert (site / "es" / "data" / "search.js").exists() and (site / "es" / "data" / "snapshot.js").exists()


def _fixed_texts(section: str) -> set[str]:
    """Every text a section page's definition writes as it is: block titles and intros, table titles, captions,
    headers, rows and notes, chart titles, subtitles, axes, series and reference lines."""
    texts = set()
    for block in PAGES[section]:
        texts |= {block["title"], block["intro"]}
        for t in block["tables"]:
            if isinstance(t, (Table, Panel)):
                texts |= {t.title, t.caption, t.note} | {c.header for c in t.columns if c.header}
                texts |= {r.label for r in t.rows if getattr(r, "label", None)}
        for c in block.get("charts", []):
            if callable(c):
                continue
            texts |= {c.get(k) for k in ("title", "subtitle", "x_title")}
            texts |= {r["label"] for r in c.get("ref_lines", []) if r.get("label")} | {r[1] for r in c.get("ref_from", [])}
            if c.get("curve"):
                texts |= {line["name"] for line in c["lines"]} | {m for line in c["lines"] for _id, m in line["points"]}
            elif c.get("kind") == "hbar":
                texts |= {item[1] for item in c["items"]}
            elif c.get("kind") == "xy":
                texts |= {c["x"][2], c["y"][2]}
            else:
                texts |= {s[2] for s in c["series"]}
    return {t for t in texts if t}


def test_every_fixed_text_of_the_33b_pages_has_its_spanish():
    known = i18n.catalogue()
    for section in SPANISH_SECTIONS:
        title, intro, _batch = SECTION_PAGES[section]
        missing = sorted(t for t in _fixed_texts(section) | {title, intro} if t not in known)
        assert not missing, (section, missing)
    labels = {label for _id, title, items in industries.SECTIONS for label in [title] + [i[1] for i in items]}
    labels |= {label for _slug, label in workstats.SECTIONS} | {title for _id, title in trade.PAGE}
    assert not sorted(t for t in labels if t not in known)


def test_the_euro_sign_follows_the_figure_in_spanish():
    assert fmt_value(58.2, "€ bn", 1) == "€58.2 bn" and fmt_value(-1449, "€", 0) == "−€1,449"
    with i18n.using("es"):
        assert fmt_value(58.2, "€ bn", 1) == "58.2 mm €" and fmt_value(-1449, "€", 0) == "−1,449 €"
        assert fmt_value(3.5, "€ mn", 1) == "3.5 mill. €"


def test_tables_charts_and_facts_are_written_in_spanish(tmp_path):
    store = Store(tmp_path / "data")
    q = pd.date_range("2015-01-01", "2026-07-01", freq="QS")
    store.save_series("gdp", pd.Series(100 * 1.005 ** np.arange(len(q)), index=q))
    days = pd.date_range("2024-01-01", "2026-10-30", freq="D")
    store.save_series("ecb_deposit_rate", pd.Series(np.where(days < pd.Timestamp("2026-06-17"), 2.25, 2.0), index=days))
    indicators = load_registry()
    en = build_page("gdp", indicators, store)
    with i18n.using("es"):
        es = build_page("gdp", indicators, store)
        facts = policy.ecb_facts(Data(indicators, store), today=pd.Timestamp("2026-11-02"))
        decisions = policy.decisions_table(Data(indicators, store))
    table, chart = es["blocks"][0]["tables"][0], es["charts"][0]
    assert en["blocks"][0]["title"] == "GDP and its components" and es["blocks"][0]["title"] == "El PIB y sus componentes"
    assert table["title"] == "Crecimiento real" and table["caption"].endswith("· hasta T3 2026")
    assert table["columns"][:2] == ["t/t", "a/a"] and table["rows"][0]["label"] == "PIB"
    assert chart["title"] == "Crecimiento del PIB real" and [s["name"] for s in chart["series"]] == ["t/t", "a/a"]
    assert en["charts"][0]["series"][0]["name"] == "q/q" and chart["lang"] == "es"
    assert [f["label"] for f in facts] == ["Tipo de la facilidad de depósito", "Último cambio", "Próxima decisión"]
    assert facts[0]["sub"] == "30 oct 2026" and facts[1]["sub"] == "en vigor desde el 17 jun 2026"
    assert facts[2]["value"] == "17 dic 2026" and facts[2]["sub"] == "dentro de 45 días" and facts[1]["value"] == "−25 pb"
    assert decisions["title"] == "Fecha de entrada en vigor" and decisions["rows"][0]["label"] == "17 jun 2026"


def test_the_imf_tables_in_spanish():
    from econpulse import sectortables
    table = sectortables.BY_ID["real-sector"]
    assert sectortables.table_title(table).startswith("Table 1. ")
    with i18n.using("es"):
        assert sectortables.table_title(table).startswith("Cuadro 1. ")
        assert i18n._("proj.") == "proy."
        missing = sorted(r.label for t in sectortables.TABLES for r in t.rows
                         if getattr(r, "label", None) and r.label not in i18n.catalogue())
        assert not missing, missing
    # The Excel workbook stays English, one folder up from the Spanish pages.
    assert (TEMPLATES_DIR / "es" / "sector-tables.html").exists()
