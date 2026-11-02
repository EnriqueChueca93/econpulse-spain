"""Batch 33a: the Spanish version of the site and the language switch (no network)."""

import re
from pathlib import Path

import numpy as np
import pandas as pd

from econpulse import changes, i18n
from econpulse.build import build_site
from econpulse.config import TEMPLATES_DIR
from econpulse.registry import Indicator, load_registry
from econpulse.snapshot import fmt_value, period_label
from econpulse.store import Store

# The templates whose text is in Spanish from Batch 33a; the others follow in 33b-33d.
SPANISH_TEMPLATES = ("base.html", "index.html", "calendar.html", "data.html", "404.html", "macros.html")


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
