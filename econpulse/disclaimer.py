"""The site's disclaimer, in one place: the line in every page's footer (templates/base.html), the RSS feed's
description, the Excel workbook's "Read me" sheet, and the notes on the Analysis, Financial and Tools pages. The full
terms are on the About page (#disclaimer, in templates/about.html and templates/es/about.html).

What the sources ask of reusers (checked 3 Nov 2026): credit them; say plainly when their figures have been
transformed (ECB, Eurostat, IMF, OECD; INE's wording is "own elaboration with data extracted from INE's website");
don't imply they endorse the reuse (INE, IMF, OECD); the IMF asks for permission before commercial reuse.
"""

from .i18n import _

SHORT = ("For information only: not investment, financial or tax advice. Figures come from their sources and can be "
         "revised or contain errors, so check the source before relying on them. Macroscope Spain is independent and "
         "is not affiliated with or endorsed by any of them.")

LICENCE = "CC BY-NC 4.0"
LICENCE_URL = "https://creativecommons.org/licenses/by-nc/4.0/"

# A one-line note at the top of the pages whose figures are most easily taken for advice or forecasts of record.
PAGE_NOTES = {
    "analysis": ("Macroscope's own readings and estimates: calculations from public data with simple, documented "
                 "methods, not official statistics, forecasts of record or investment advice. Forecasters' figures are "
                 "theirs, as they published them."),
    "financial": ("Market prices, yields and rates as of the site's latest update, not live: for information only, "
                  "not investment advice or a recommendation to buy or sell anything."),
    "tools": ("The tools run simple models on public data: their results show what the assumptions imply, and are "
              "not forecasts or advice."),
}


def page_note(page: str) -> str | None:
    note = PAGE_NOTES.get(page)
    return _(note) if note else None


def context(owner: str | None, contact: str | None) -> dict:
    """For the templates: the footer line, the licence, and who runs the site (config.py)."""
    label = None
    if contact:
        label = contact.removeprefix("mailto:") if contact.startswith("mailto:") else contact.removeprefix("https://").rstrip("/")
    return {"short": _(SHORT), "licence": LICENCE, "licence_url": LICENCE_URL, "owner": owner, "contact": contact,
            "contact_label": label}


def readme_lines(built: str = "") -> list[str]:
    """The workbook's "Read me" sheet, in English like the workbook."""
    return [
        "Macroscope Spain: IMF-style sector tables",
        f"Built {built}" if built else "",
        "",
        SHORT,
        "",
        "Sources: every table names its sources under it, and the Contents sheet lists the IMF tables they follow.",
        "Figures are as published by each source. Anything derived from them (ratios, growth rates, sums, lines "
        "rebuilt to follow the IMF's tables) is Macroscope's own calculation from published series, not an official "
        "statistic.",
        "INE's figures are taken from INE's website, www.ine.es; those Macroscope transforms are its own elaboration "
        "with data extracted from INE's website.",
        "Data from the ECB, Eurostat, the IMF, the OECD and the other sources remain theirs and follow their terms; "
        "the IMF asks for permission before any commercial reuse of its data.",
        "",
        f"Macroscope's own tables are licensed under {LICENCE} ({LICENCE_URL}): share and adapt them for "
        "non-commercial purposes, crediting Macroscope Spain with a link and saying if you changed them.",
        "Full terms: https://enriquechueca93.github.io/macroscope-spain/about.html#disclaimer",
    ]
