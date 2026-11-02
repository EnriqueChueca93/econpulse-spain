"""The site's two languages (Batch 33a): English, where everyone starts, and Spanish, under es/.

The build writes every page once per language (econpulse/build.py). While it writes the Spanish one, `lang()`
is "es" and text marked for translation, `_("...")` in Python and in the templates, comes from the catalogue
in econpulse/locale/es.yaml, keyed on the English. Text not in the catalogue yet stays in English, and is
noted in `missing` so a build can say what is left to translate. Numbers keep the English format in both
languages (1.8%, 1,751.2); dates take Spanish month and day names.
"""

import contextvars
import re
from contextlib import contextmanager
from pathlib import Path

import yaml

LANGUAGES = ("en", "es")
CATALOGUE = Path(__file__).parent / "locale" / "es.yaml"

_lang = contextvars.ContextVar("lang", default="en")
_catalogue: dict[str, str] | None = None
missing: dict[str, int] = {}          # English text with no Spanish yet -> times asked for, this run


def lang() -> str:
    return _lang.get()


@contextmanager
def using(code: str):
    """Write in this language inside the block."""
    token = _lang.set(code)
    try:
        yield
    finally:
        _lang.reset(token)


def catalogue() -> dict[str, str]:
    global _catalogue
    if _catalogue is None:
        _catalogue = yaml.safe_load(CATALOGUE.read_text(encoding="utf-8")) or {}
    return _catalogue


def _spanish() -> set[str]:
    global _values
    if _values is None:
        _values = set(catalogue().values())
    return _values


_values: set[str] | None = None


def _(text: str) -> str:
    """`text` in the language being written."""
    if lang() == "en" or not text:
        return text
    out = catalogue().get(text)
    if out is None:
        if text not in _spanish():        # text that is in Spanish already (translated twice) is not missing
            missing[text] = missing.get(text, 0) + 1
        return text
    return out


def maybe(text):
    """`text` in Spanish if the catalogue has it, without noting it as missing: labels that are often proper
    names already (regions, countries) or not text at all."""
    if lang() == "en" or not isinstance(text, str):
        return text
    return catalogue().get(text, text)


def ngettext(singular: str, plural: str, n: int) -> str:
    return _(singular if n == 1 else plural)


def pick(en: str, es: str | None) -> str:
    """One of two texts that come in both languages already (an indicator's English and official Spanish name)."""
    return es if lang() == "es" and es else en


# ---------------------------------------------------------------- dates
MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October",
          "November", "December"]
MONTHS_ES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre",
             "noviembre", "diciembre"]
MON_ES = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]
DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
DAYS_ES = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
DY_ES = ["lun", "mar", "mié", "jue", "vie", "sáb", "dom"]


def mon(d) -> str:
    """"Nov" / "nov"."""
    return MON_ES[d.month - 1] if lang() == "es" else MONTHS[d.month - 1][:3]


def month(d) -> str:
    """"November" / "noviembre"."""
    return MONTHS_ES[d.month - 1] if lang() == "es" else MONTHS[d.month - 1]


def weekday(d) -> str:
    return DAYS_ES[d.weekday()] if lang() == "es" else DAYS[d.weekday()]


def wd(d) -> str:
    """"Mon" / "lun"."""
    return DY_ES[d.weekday()] if lang() == "es" else DAYS[d.weekday()][:3]


def month_year(d) -> str:
    """"Nov 2026" / "nov 2026"."""
    return f"{mon(d)} {d.year}"


def day_month_year(d) -> str:
    """"3 Nov 2026" / "3 nov 2026"."""
    return f"{d.day} {mon(d)} {d.year}"


def day_mon(d) -> str:
    """"3 Nov" / "3 nov"."""
    return f"{d.day} {mon(d)}"


def wd_day_mon(d) -> str:
    """"Tue 3 Nov" / "mar 3 nov"."""
    return f"{wd(d)} {d.day} {mon(d)}"


def long_month_year(d) -> str:
    """"November 2026" / "noviembre de 2026"."""
    return f"{month(d)} de {d.year}" if lang() == "es" else f"{month(d)} {d.year}"


def long_day_month(d) -> str:
    """"3 November" / "3 de noviembre"."""
    return f"{d.day} de {month(d)}" if lang() == "es" else f"{d.day} {month(d)}"


def long_date(d) -> str:
    """"Tuesday 3 November 2026" / "martes 3 de noviembre de 2026"."""
    if lang() == "es":
        return f"{weekday(d)} {d.day} de {month(d)} de {d.year}"
    return f"{weekday(d)} {d.day} {month(d)} {d.year}"


def quarter(d) -> str:
    """"Q3 2026" / "T3 2026"."""
    return f"{'T' if lang() == 'es' else 'Q'}{(d.month - 1) // 3 + 1} {d.year}"


def capital(text: str) -> str:
    """First letter up, for a Spanish date that starts a heading ("Noviembre de 2026")."""
    return text[:1].upper() + text[1:]


# ---------------------------------------------------------------- figures written before the build
# Text written in English when the data was fetched (the log of what changed, release periods) is put into
# Spanish word by word: month names, change labels and units. Numbers stay as they are.
_FIGURE_WORDS = [
    (r"\bq/q ann\.", "t/t anualiz."), (r"\b3m ann\.", "3m anualiz."), (r"\b12-mo total\b", "total 12 meses"),
    (r"\b12-mo avg\.", "media 12 meses"), (r"\b4-qtr total\b", "total 4 trim."), (r"\b4-qtr avg\.", "media 4 trim."),
    (r"\by/y\b", "a/a"), (r"\bq/q\b", "t/t"), (r"\bYTD\b", "en el año"), (r" SA\b", " desest."),
    (r"% of GDP\b", "% del PIB"), (r"(?<=\d) bp\b", " pb"), (r"(?<=\d) mn\b", " mill."), (r"(?<=\d) bn\b", " mm"),
    (r"\bQ([1-4]) (\d{4})\b", r"T\1 \2"),
]
_MONTH_WORDS = {m[:3]: es for m, es in zip(MONTHS, MON_ES)} | {m: es for m, es in zip(MONTHS, MONTHS_ES)}
_MONTH_RE = re.compile(r"\b(" + "|".join(sorted(_MONTH_WORDS, key=len, reverse=True)) + r")\b(?= \d{4}| \d{1,2}\b|$)")


def figures(text: str) -> str:
    """Figures and periods written in English ("0.6% q/q in Q3 2026", "Oct 2026") in the language being written."""
    if lang() == "en" or not text:
        return text
    for pattern, repl in _FIGURE_WORDS:
        text = re.sub(pattern, repl, text)
    return _MONTH_RE.sub(lambda m: _MONTH_WORDS[m.group(1)], text)
