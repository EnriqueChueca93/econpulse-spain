"""Batch 8: the release calendar, what-changed notes, and the Calendar, About and Data pages (no network)."""

from datetime import datetime, timedelta, timezone

import numpy as np
import pandas as pd
import pytest

from econpulse import changes, schedule
from econpulse.build import build_site
from econpulse.registry import Indicator
from econpulse.store import Store

ICS = """BEGIN:VCALENDAR\r
BEGIN:VEVENT\r
DTSTART;TZID=Europe/Madrid:20261113T090000\r
SUMMARY:Índice de Precios de Consumo. Octubre 2026\r
END:VEVENT\r
BEGIN:VEVENT\r
DTSTART;TZID=Europe/Madrid:20261127T090000\r
SUMMARY:Índice de Precios de Consumo. Avance. Noviem\r
 bre 2026\r
END:VEVENT\r
BEGIN:VEVENT\r
DTSTART;TZID=Europe/Madrid:20261118T110000\r
SUMMARY:Tablas de mortalidad. Año 2025\r
END:VEVENT\r
BEGIN:VEVENT\r
DTSTART;TZID=Europe/Madrid:20261030T090000\r
SUMMARY:Contabilidad Nacional Trimestral de España. Avance. Trimestre 3/2026\r
END:VEVENT\r
END:VCALENDAR\r
"""


def ind(**kw):
    base = dict(label=kw["id"], label_es=kw["id"], section="activity", source="fake", key=kw["id"], freq="M", unit="%")
    return Indicator(**{**base, **kw})


@pytest.fixture
def store(tmp_path):
    return Store(tmp_path / "data")


# ---------------------------------------------------------------- calendar

def test_parse_ics_keeps_site_releases_and_unfolds_lines():
    events = schedule.parse_ics(ICS)
    assert [e["title"] for e in events] == [
        "Contabilidad Nacional Trimestral de España. Avance. Trimestre 3/2026",
        "Índice de Precios de Consumo. Octubre 2026",
        "Índice de Precios de Consumo. Avance. Noviembre 2026",  # folded line joined; mortality tables dropped
    ]
    assert events[0]["start"] == "2026-10-30T09:00"


@pytest.mark.parametrize("title, period", [
    ("Índice de Precios de Consumo. Avance. Noviembre 2026", "Nov 2026"),
    ("Encuesta de Población Activa. Tercer trimestre 2026", "Q3 2026"),
    ("Encuesta Trimestral de Coste Laboral. Trimestre 3/2026", "Q3 2026"),
    ("Contabilidad Regional de España. Avance PIB. Serie 2000-2025", "2025"),
])
def test_periods_in_english(title, period):
    assert schedule._period_en(title) == period


def test_working_days_skip_weekends_and_holidays():
    assert schedule._easter(2026) == pd.Timestamp("2026-04-05")
    assert pd.Timestamp("2026-04-03") in schedule.holidays(2026)  # Good Friday
    assert schedule.working_day(2026, 1, 2) == pd.Timestamp("2026-01-05")   # 1 Jan off, 2 Jan is the first
    assert schedule.working_day(2026, 11, 2) == pd.Timestamp("2026-11-03")
    rel = schedule.social_security_releases(pd.Timestamp("2026-10-31"), months=2)
    assert [(e["when"].date().isoformat(), e["period"]) for e in rel] == [
        ("2026-09-02", "Aug 2026"), ("2026-10-02", "Sep 2026"), ("2026-11-03", "Oct 2026")]
    assert all(e["expected"] for e in rel)


def test_calendar_views(store):
    store.save_json("calendar", {"events": schedule.parse_ics(ICS)})
    today = pd.Timestamp("2026-10-31")
    bar = schedule.coming_up(store, today, count=2)
    assert bar["today"] == "Sat 31 Oct" and bar["today_items"] == []
    assert [i["text"] for i in bar["items"]] == ["Registrations and registered unemployment", "CPI and HICP, full data"]
    days = schedule.window(store, today, before=7, after=30)
    assert days[0]["past"] and days[0]["events"][0]["label"] == "GDP, first estimate"
    labels = [e["label"] for d in days for e in d["events"]]
    assert "CPI flash estimate" in labels and "ECB monetary policy decision" not in labels  # 17 Dec is too far
    assert "ECB monetary policy decision" in [e["label"] for d in schedule.window(store, today) for e in d["events"]]


# ---------------------------------------------------------------- what changed

def _save(store, ind_id, values, start="2026-01-01", freq="MS"):
    store.save_series(ind_id, pd.Series(values, index=pd.date_range(start, periods=len(values), freq=freq)))


def test_change_notes(store):
    inds = [ind(id="cpi", label="CPI inflation", change_unit="pp", section="inflation"),
            ind(id="y10", label="Spain 10-year yield", freq="D", decimals=2, change_unit="bp", section="financial"),
            ind(id="ix", label="IBEX 35", freq="D", unit="index", decimals=0, change_unit="%", section="financial")]
    _save(store, "cpi", [3.0, 3.2, 3.5])
    _save(store, "y10", [3.00, 3.05], start="2026-10-28", freq="D")
    _save(store, "ix", [100.0, 101.0], start="2026-10-28", freq="D")
    t0 = datetime(2026, 10, 31, 12, tzinfo=timezone.utc)
    assert changes.record(inds, store, now=t0) == []  # the first run only saves the state

    _save(store, "cpi", [3.0, 3.2, 3.4, 3.9])                       # a revision to March and a new April
    _save(store, "y10", [3.00, 3.05, 3.20], start="2026-10-28", freq="D")    # +15 bp: worth a note
    _save(store, "ix", [100.0, 101.0, 101.5], start="2026-10-28", freq="D")  # +0.5%: not
    notes = changes.record(inds + [ind(id="new")], store, now=t0 + timedelta(days=1))
    texts = [n["text"] for n in notes]
    assert texts == ["CPI inflation: 3.9% in Apr 2026, after 3.5% in Mar 2026.",
                     "Spain 10-year yield: +15 bp since the last update, to 3.20%."]
    assert notes[0]["page"] == "inflation.html" and notes[1]["kind"] == "market"

    _save(store, "cpi", [3.0, 3.2, 3.4, 3.8])
    notes = changes.record(inds, store, now=t0 + timedelta(days=2))
    assert [n["text"] for n in notes] == ["CPI inflation for Apr 2026 revised to 3.8%, from 3.9%."]
    assert len(store.load_json("releases")["notes"]) == 3


def test_latest_notes_and_recent_releases(store):
    now = datetime.now(timezone.utc)
    store.save_json("releases", {"state": {}, "updated_at": now.isoformat(), "notes": [
        {"at": (now - timedelta(days=1)).isoformat(timespec="seconds"), "kind": "release", "id": "a", "page": "x", "text": "old"},
        {"at": now.isoformat(timespec="seconds"), "kind": "market", "id": "b", "page": "x", "text": "move"},
        {"at": now.isoformat(timespec="seconds"), "kind": "release", "id": "c", "page": "x", "text": "new"}]})
    out = changes.latest_notes(store)
    assert [n["text"] for n in out["notes"]] == ["new", "move"]  # the latest update only, releases first

    items = {"gdp": {"label": "Real GDP", "headline": {"display": "0.6%", "label": "q/q", "period": "Q3 2026"}},
             "cpi": {"label": "CPI inflation", "headline": {"display": "4.9%", "label": "", "period": "Sep 2026"}}}
    events = [{"when": pd.Timestamp("2026-10-30 09:00"), "label": "GDP, first estimate", "period": "Q3 2026",
               "page": "gdp.html", "ids": ["gdp"]},
              {"when": pd.Timestamp("2026-10-30 09:00"), "label": "CPI flash estimate", "period": "Oct 2026",
               "page": "inflation.html", "ids": ["cpi"]}]
    recent = changes.recent_releases(store, items, events, pd.Timestamp("2026-10-31"))
    assert recent[1]["figures"] == ["Real GDP 0.6% q/q"]
    assert recent[0]["figures"] == []  # the site has September, not the October flash yet: no figure shown


# ---------------------------------------------------------------- pages

def test_calendar_about_and_data_pages_build(tmp_path):
    store = Store(tmp_path / "data")
    store.save_series("x", pd.Series(np.linspace(1, 2, 24), index=pd.date_range("2024-11-01", periods=24, freq="MS")))
    store.save_catalog({"x": {"status": "ok", "fetched_at": "2026-10-31T12:00:00+00:00", "last_date": "2026-10-01"}})
    store.save_json("calendar", {"events": schedule.parse_ics(ICS)})
    build_site([ind(id="x", label="Test series", tile=1)], store, site_dir=tmp_path / "site")
    site = tmp_path / "site"
    for page in ("calendar.html", "about.html", "data.html"):
        assert (site / page).exists()
    home = (site / "index.html").read_text(encoding="utf-8")
    assert 'class="release-bar"' in home and "calendar.html" in home and 'href="about.html"' in home
    assert "All 1 series were fetched successfully" in (site / "data.html").read_text(encoding="utf-8")
    assert "INE's own calendar" in (site / "calendar.html").read_text(encoding="utf-8")
