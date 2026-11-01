"""Release calendar: when the data on the site is next published.

    INE           its own publication calendar (an iCal file), saved to data/calendar.json
                  at each fetch so the site builds offline
    Seg. Social   registrations and registered unemployment: the second working day
                  of each month, by rule ("expected")
    ECB           monetary policy decisions, from econpulse/policy.py

Only releases that feed the site are listed; INE's other publications are left out.
"""

import re
from datetime import datetime

import pandas as pd

from . import http, policy
from .sources.base import madrid_today
from .store import Store

INE_ICS = "https://www.ine.es/dynt3/Calendario/calendario.ics"
INE_CALENDAR_PAGE = "https://www.ine.es/dynt3/Calendario/calenHTML.htm"

# INE release titles ("<operation>. <period>") -> what the site calls them, where they show
# and the indicators they update. Order matters: the first match wins (the CPI flash first).
INE_RELEASES = [
    (r"^Índice de Precios de Consumo\. Avance", "CPI flash estimate", "inflation.html", ["cpi", "core_cpi"]),
    (r"^Índice de Precios de Consumo\.", "CPI and HICP, full data", "inflation.html", ["cpi_index", "hicp"]),
    (r"^Contabilidad Nacional Trimestral de España\. Avance", "GDP, first estimate", "gdp.html", ["gdp"]),
    (r"^Contabilidad Nacional Trimestral de España\.", "GDP, full quarterly accounts", "gdp.html", ["gdp", "unit_labour_cost"]),
    (r"^Encuesta de Población Activa\. (Trimestre|Primer|Segundo|Tercer|Cuarto)", "Labour force survey (EPA)",
     "labour.html", ["unemployment_epa", "employment_epa"]),
    (r"^Encuesta Trimestral de Coste Laboral\.", "Labour costs (ETCL)", "wages.html", ["wage_cost"]),
    (r"^Índice de Producción Industrial\.", "Industrial production", "activity.html", ["industrial_production"]),
    (r"^Índices de Comercio al por menor\. (?!Ponderaciones)", "Retail sales", "activity.html", ["retail_sales"]),
    (r"^Índice de Precios Industriales\.", "Producer prices", "inflation.html", ["ppi"]),
    (r"^Movimientos Turísticos en Fronteras\.", "Tourist arrivals (FRONTUR)", "activity.html", ["tourist_arrivals"]),
    (r"^Encuesta de Gasto Turístico Mensual\.", "Tourist spending (EGATUR)", "activity.html", ["tourist_spending"]),
    (r"^Índice de Precios de Vivienda\. (?!Medias)", "House prices", "housing.html", ["house_prices"]),
    (r"^Estadística de Transmisiones de Derechos de la Propiedad\. (?!Resultados)", "Home sales", "housing.html",
     ["home_sales"]),
    (r"^Hipotecas Mensual\.", "Mortgages", "housing.html", ["mortgages_homes"]),
    (r"^Contabilidad Regional de España\. Avance PIB", "Regional GDP", "regions.html", []),
]

MONTHS_ES = {m: i + 1 for i, m in enumerate(
    ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre",
     "noviembre", "diciembre"])}
QUARTERS_ES = {"primer": 1, "segundo": 2, "tercer": 3, "cuarto": 4}

# National holidays on fixed dates (regional ones vary); Good Friday is added per year.
FIXED_HOLIDAYS = [(1, 1), (1, 6), (5, 1), (8, 15), (10, 12), (11, 1), (12, 6), (12, 8), (12, 25)]


# ---------------------------------------------------------------- INE calendar

def parse_ics(text: str) -> list[dict]:
    """INE releases that feed the site: {"start": "YYYY-MM-DDTHH:MM", "title": ...}."""
    text = re.sub(r"\r?\n[ \t]", "", text)  # unfold continuation lines
    events = []
    for block in text.split("BEGIN:VEVENT")[1:]:
        start = re.search(r"^DTSTART[^:]*:(\d{8})T?(\d{4})?", block, re.M)
        title = re.search(r"^SUMMARY[^:]*:(.*)$", block, re.M)
        if not start or not title:
            continue
        title = title.group(1).strip().replace("\\,", ",")
        if not any(re.search(pattern, title) for pattern, *_ in INE_RELEASES):
            continue
        day, hm = start.group(1), start.group(2) or "0900"
        events.append({"start": f"{day[:4]}-{day[4:6]}-{day[6:]}T{hm[:2]}:{hm[2:]}", "title": title})
    return sorted(events, key=lambda e: e["start"])


def refresh(store: Store) -> int:
    """Download INE's calendar and save the releases the site uses. Keeps the old file on failure."""
    try:
        text = http.get(INE_ICS).content.decode("utf-8", "replace")
        events = parse_ics(text)
    except Exception as e:  # noqa: BLE001 - a calendar failure must not stop the update
        print(f"Calendar not updated: {e}")
        return 0
    if events:
        store.save_json("calendar", {"source": INE_ICS, "fetched_at": datetime.now().astimezone().isoformat(timespec="seconds"),
                                     "events": events})
    return len(events)


def _period_en(text: str) -> str:
    """'Noviembre 2026' -> 'Nov 2026'; 'Tercer trimestre 2026' or 'Trimestre 3/2026' -> 'Q3 2026'."""
    t = text.lower()
    m = re.search(r"trimestre\s+(\d)/(\d{4})", t) or re.search(r"(\d)/(\d{4})", t)
    if m and "trimestre" in t:
        return f"Q{m.group(1)} {m.group(2)}"
    m = re.search(r"(primer|segundo|tercer|cuarto)\s+trimestre\s+(?:de\s+)?(\d{4})", t)
    if m:
        return f"Q{QUARTERS_ES[m.group(1)]} {m.group(2)}"
    m = re.search(r"(" + "|".join(MONTHS_ES) + r")\s+(?:de\s+)?(\d{4})", t)
    if m:
        return f"{pd.Timestamp(int(m.group(2)), MONTHS_ES[m.group(1)], 1):%b %Y}"
    years = re.findall(r"\d{4}", t)  # "Serie 2000-2025": the last year is the new one
    return years[-1] if years else ""


def ine_releases(store: Store) -> list[dict]:
    saved = store.load_json("calendar", {}) or {}
    out = []
    for e in saved.get("events", []):
        for pattern, label, page, ids in INE_RELEASES:
            if re.search(pattern, e["title"]):
                out.append({"when": pd.Timestamp(e["start"]), "label": label, "page": page, "source": "INE",
                            "period": _period_en(e["title"]), "expected": False, "ids": ids})
                break
    return out


# ---------------------------------------------------------------- rule-based releases

def _easter(year: int) -> pd.Timestamp:
    """Easter Sunday (anonymous Gregorian algorithm)."""
    a, b, c = year % 19, year // 100, year % 100
    d, e = divmod(b, 4)
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i, k = divmod(c, 4)
    l_ = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l_) // 451
    month, day = divmod(h + l_ - 7 * m + 114, 31)
    return pd.Timestamp(year, month, day + 1)


def holidays(year: int) -> set[pd.Timestamp]:
    return {pd.Timestamp(year, m, d) for m, d in FIXED_HOLIDAYS} | {_easter(year) - pd.Timedelta(days=2)}


def working_day(year: int, month: int, n: int) -> pd.Timestamp:
    """The n-th working day of a month (Monday to Friday, national holidays off)."""
    day, count, off = pd.Timestamp(year, month, 1), 0, holidays(year)
    while True:
        if day.day_of_week < 5 and day not in off:
            count += 1
            if count == n:
                return day
        day += pd.Timedelta(days=1)


def social_security_releases(start: pd.Timestamp, months: int = 13) -> list[dict]:
    out = []
    for k in range(-1, months):
        first = (start + pd.DateOffset(months=k)).replace(day=1)
        day = working_day(first.year, first.month, 2)
        period = first - pd.DateOffset(months=1)
        out.append({"when": day + pd.Timedelta(hours=9), "label": "Registrations and registered unemployment",
                    "page": "labour.html", "source": "Seguridad Social, SEPE", "period": f"{period:%b %Y}", "expected": True,
                    "ids": ["afiliados", "paro_registrado"]})
    return out


def ecb_releases() -> list[dict]:
    return [{"when": d + pd.Timedelta(hours=14, minutes=15), "label": "ECB monetary policy decision", "page": "ecb.html",
             "source": "ECB", "period": "", "expected": False, "ids": ["ecb_deposit_rate"]} for d in policy.ECB_DECISIONS]


# ---------------------------------------------------------------- views

def releases(store: Store, today: pd.Timestamp | None = None) -> list[dict]:
    """Every known release, in date order."""
    today = pd.Timestamp(today or madrid_today()).normalize()
    events = ine_releases(store) + social_security_releases(today) + ecb_releases()
    return sorted(events, key=lambda e: (e["when"], e["label"]))


def _day_label(d: pd.Timestamp) -> str:
    return f"{d:%a} {d.day} {d:%b}"


def window(store: Store, today: pd.Timestamp | None = None, before: int = 7, after: int = 61) -> list[dict]:
    """Releases from `before` days ago to `after` days ahead, grouped by day, for the Calendar page."""
    today = pd.Timestamp(today or madrid_today()).normalize()
    days: dict[pd.Timestamp, list[dict]] = {}
    for e in releases(store, today):
        day = e["when"].normalize()
        if today - pd.Timedelta(days=before) <= day <= today + pd.Timedelta(days=after):
            days.setdefault(day, []).append({**e, "time": f"{e['when']:%H:%M}"})
    return [{"date": d, "label": f"{d:%A} {d.day} {d:%B %Y}", "past": d < today, "today": d == today, "events": evs}
            for d, evs in sorted(days.items())]


def coming_up(store: Store, today: pd.Timestamp | None = None, count: int = 3, horizon: int = 21) -> dict:
    """The 'Today / Coming up' bar: today's releases and the next few after it."""
    today = pd.Timestamp(today or madrid_today()).normalize()
    events = [e for e in releases(store, today) if today <= e["when"].normalize() <= today + pd.Timedelta(days=horizon)]
    todays = [e for e in events if e["when"].normalize() == today]
    later = [e for e in events if e["when"].normalize() > today][:count]

    def item(e):  # the bar stays short: the period is on the Calendar page
        return {"day": _day_label(e["when"]), "text": e["label"], "page": e["page"], "ids": e.get("ids", [])}

    return {"today": _day_label(today), "today_items": [item(e) for e in todays], "items": [item(e) for e in later]}
