"""Batch 15: the central bank stance page, from Econvitals' data (no network)."""

import copy

import pytest

from econpulse import http, stance
from econpulse.build import build_site
from econpulse.registry import load_registry
from econpulse.store import Store


def bank(code, name, rate, decision_day, meeting, market=None, **extra):
    return {"code": code, "name": name, "country": extra.get("country", name), "flag": "", "instrument": "Policy rate",
            "rate": rate, "rate_display": f"{rate:.2f}%", "as_of": "2026-10-31", "ytd_display": "+25 bp",
            "last_move": {"display": "▲ 25 bp · Sep 2026"}, "phase": extra.get("phase", "Hiking"),
            "next_move": {"text": "In a hiking cycle (rule)", "kind": "auto"},
            "decision": {"announced": decision_day, "title": f"{name} decision", "url": f"https://example.org/{code}"},
            "next_meeting": {"date": meeting, "source": "calendar", "source_url": "https://example.org/calendar"},
            "market": market or {"sources": []}}


DATA = {
    "meta": {"generated_at": "2026-11-01T00:06:41+00:00", "note": "Cycle phase is a transparent heuristic.",
             "source": "BIS — Central bank policy rates (WS_CBPOL)", "fast_sources": [], "market_sources": ["Polymarket", "Kalshi"]},
    "summary": {"as_of": "2026-11-01", "total": 2, "cutting": 0, "hold": 1, "hiking": 1, "paused": 0},
    "banks": [
        bank("XM", "European Central Bank", 2.5, "2026-10-29", "2026-12-17", country="Euro area", market={"sources": [
            {"source": "Polymarket", "decision_date": "2026-12-17", "p_cut": 0.012, "p_hold": 0.13, "p_hike": 0.8675, "thin": False},
            {"source": "Kalshi", "decision_date": "2026-12-17", "p_cut": 0.01, "p_hold": 0.13, "p_hike": 0.86, "thin": True}]}),
        bank("GB", "Bank of England", 3.75, "2026-09-17", "2026-11-05", phase="On Hold", country="United Kingdom", market={"sources": [
            {"source": "Bank of England OIS curve", "p_hike": None, "p_hold": None,
             "implied_path": [{"date": "2027-01", "months": 3, "rate": 4.161}, {"date": "2028-10", "months": 24, "rate": 4.842}]}]}),
    ],
    "diffusion": {"meta": {"note": "Each bank's stance is read from BIS."}, "months": ["2026-10", "2026-11"],
                  "index": [28.9, 27.0], "hiking": [14, 13], "cutting": [3, 3], "hold": [20, 21], "n": [37, 37],
                  "latest": {"month": "2026-11", "hiking": [{"name": "European Central Bank"}], "cutting": [], "hold": [{"name": "x"}]}},
}
DESK = {
    "meta": {"source": "Desk research (named houses)", "core_note": "Real rate = (1 + rate) / (1 + core) - 1."},
    "banks": {
        "XM": {"lean": {"hike": 4, "hold": 3, "cut": 0}, "n_desks": 7, "consensus": "Hike",
               "calls": [{"institution": "Citi", "person": "Giada Giani", "call": "hike", "size_bp": 25, "note": "flash HICP 4.0%",
                          "as_of": "2026-10-30"}],
               "market_quotes": [{"institution": "Berenberg", "quote": "Market prices two or three further rises.", "as_of": "2026-10-29"}],
               "statement": {"announced": "2026-09-10", "summary": "Raised rates.", "tilt": "hawkish"},   # an older decision
               "core_inflation": {"value": 2.5}},
        "GB": {"lean": {"hike": 7}, "n_desks": 7, "consensus": "Hike", "calls": [], "market_quotes": [],
               "statement": {"announced": "2026-09-17", "summary": "Held at 3.75% (6-3 vote).", "tilt": "hawkish", "vote": "6-3"},
               "core_inflation": {"value": 2.8}},
    },
}


class Fake:
    def __init__(self, payload):
        self.payload = payload

    def json(self):
        return copy.deepcopy(self.payload)


@pytest.fixture
def store(tmp_path, monkeypatch):
    monkeypatch.setattr(http, "get", lambda url, **kw: Fake(DATA if url.endswith("data.json") else DESK))
    monkeypatch.setattr(stance, "madrid_today", lambda: __import__("datetime").date(2026, 11, 1))
    s = Store(tmp_path / "data")
    assert stance.refresh(s) == "2 central banks, data through 2026-11-01"
    return s


def test_refresh_keeps_the_last_copy_on_failure(store, monkeypatch):
    def broken(url, **kw):
        raise ConnectionError("down")
    monkeypatch.setattr(http, "get", broken)
    assert stance.refresh(store).startswith("not updated (ConnectionError: down)")
    saved = store.load_json(stance.STORE)
    assert saved["data"]["summary"]["total"] == 2 and saved["error"]
    assert stance.page(store)["error"] == "ConnectionError: down"


def test_page_rows(store):
    p = stance.page(store)
    ecb, boe = p["rows"]
    assert ecb["spain"] and ecb["days"] == 46 and ecb["meeting"] == "Thu Dec 17"
    assert ecb["decision"]["summary"] is None   # the summary is of an earlier decision: "summary pending"
    assert boe["decision"]["summary"] == "Held at 3.75% (6-3 vote)." and boe["decision"]["vote"] == "6-3"
    assert ecb["desk"]["tally"] == "4 hike · 3 hold · 7 houses" and ecb["desk"]["quotes"][0]["house"] == "Berenberg"
    lead = ecb["market"]["lead"]
    assert (lead["source"], lead["move"], lead["p"]) == ("Polymarket", "hike", "87%")
    assert ecb["market"]["agree"] == [{"source": "Kalshi", "agrees": True, "text": "86% hike", "thin": True}]
    assert boe["market"]["lead"] is None and boe["market"]["paths"][0]["text"] == "Jan 4.16 · Oct ’28 4.84"
    assert ecb["real"] == pytest.approx(0.0) and boe["real"] == pytest.approx((1.0375 / 1.028 - 1) * 100)
    assert [r["code"] for r in p["upcoming"]] == ["GB", "XM"] and [r["code"] for r in p["diary"]] == ["XM", "GB"]


def test_charts(store):
    diffusion, nominal, real = stance.charts(store)
    assert diffusion["series"][0]["y"][-1] == round(100 * 13 / 37, 1) and diffusion["series"][1]["y"][-1] == round(-100 * 3 / 37, 1)
    assert diffusion["series"][2]["y"] == [28.9, 27.0]
    assert nominal["series"][0]["x"] == ["BoE", "ECB"] and real["highlight"] == "ECB"


def test_page_is_built_and_credits_econvitals(store, tmp_path):
    build_site(load_registry(), store, site_dir=tmp_path / "site")
    html = (tmp_path / "site" / "stance.html").read_text(encoding="utf-8")
    assert "econvitals.org/tools/central-bank-stance/" in html and "CC0 1.0" in html and "Jason Furman" in html
    assert 'aria-current="page">Tools<' in html and 'id="bank-xm" class="highlight-row"' in html
    assert "summary pending" in html and "Berenberg" in html
    assert 'href="stance.html"' in (tmp_path / "site" / "tools.html").read_text(encoding="utf-8")


def test_page_without_data(tmp_path):
    s = Store(tmp_path / "data")
    assert stance.page(s) is None and stance.charts(s) == []
