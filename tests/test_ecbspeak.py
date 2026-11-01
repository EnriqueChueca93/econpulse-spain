"""Batch 17: ECB-speak, word-list scoring of the Governing Council's speeches (no network)."""

import io
import zipfile
from datetime import date

import pandas as pd
import pytest
import requests

from econpulse import ecbspeak, http, speechscore
from econpulse.build import build_site
from econpulse.registry import load_registry
from econpulse.store import Store

HAWK = ("Inflation is rising and price pressures remain high. Upside risks to inflation have grown. "
        "We may need to raise interest rates further, and policy must remain restrictive. Monetary policy will act.")
DOVE = ("Inflation is falling and price pressures are easing. Downside risks to inflation have grown. "
        "We can cut interest rates, as policy can be less restrictive. Monetary policy will support the economy.")


def test_word_list_scores():
    hawk, dove = speechscore.score(HAWK), speechscore.score(DOVE)
    assert hawk["score"] == 100.0 and hawk["hawkish"] >= 4 and hawk["dovish"] == 0
    assert dove["score"] == -100.0
    assert speechscore.score("Inflation was high in the past. Inflation was low before.")["score"] is None  # levels, too few
    payments = "Strong demand for digital payments. " * 6 + "Robust growth in instant payments. " * 4
    assert speechscore.score(payments)["score"] is None   # no monetary-policy sentences at all
    assert set(speechscore.GROUP_NOTES) == set(speechscore.HAWKISH) | set(speechscore.DOVISH)


@pytest.mark.parametrize("byline, day, expected", [
    ("Speech by Ms Christine Lagarde, President of the European Central Bank, at Frankfurt", "2026-05-01", ("ECB", "ECB President")),
    ("Speech by Mr Boris Vujčić, Vice-President of the European Central Bank, at a conference", "2026-07-01", ("ECB", "ECB Vice-President")),
    ("Speech by Ms Isabel Schnabel, Member of the Executive Board of the ECB, at a lecture", "2026-02-11", ("ECB", "ECB Executive Board")),
    ("Speech by Mr José Luis Escrivá, Governor of the Bank of Spain, at Madrid", "2026-06-19", ("ES", "ES")),
    ("Speech by Mr Joachim Nagel, President of the Deutsche Bundesbank, at Frankfurt", "2026-03-01", ("DE", "DE")),
    ("Speech by Mr Gediminas Šimkus, Chairman of the Board of the Bank of Lithuania", "2026-03-01", ("LT", "LT")),
    ("Speech by Ms Chiara Scotti, Deputy Governor of the Bank of Italy, at Milan", "2026-10-23", None),
    ("Speech by Ms Sabine Mauderer, Vice-President of the Deutsche Bundesbank", "2026-03-01", None),
    ("Speech by Mr Boris Vujčić, Governor of the Croatian National Bank", "2022-10-01", None),   # before Croatia joined
    ("Speech by Mr Andrew Bailey, Governor of the Bank of England", "2026-03-01", None),
])
def test_members_are_recognised_by_role(byline, day, expected):
    who = ecbspeak.role(byline, day)
    assert (who["institution"], who["seat"]) == expected if expected else who is None


def test_names_and_bylines():
    assert ecbspeak.speaker_key("Philip R. Lane") == ecbspeak.speaker_key("Philip R Lane") == "lane"
    assert ecbspeak.speaker_key("Boris Vujčić") == "vujcic"
    assert ecbspeak._byline_name("Slides by Piero Cipollone, Member of the Executive Board of the ECB") == "Piero Cipollone"


def ecb_csv() -> str:
    head = "date|speakers|title|subtitle|contents\n"
    return head + "\n".join([
        f"2026-10-30|Philip R. Lane|Policy now|Speech by Philip R. Lane, Member of the Executive Board of the ECB, at X|{HAWK}",
        f"2022-06-01|Christine Lagarde|Too early|Speech by Christine Lagarde, President of the ECB|{HAWK}",
        f"2026-10-20|Claudia Buch|Supervision|Speech by Claudia Buch, Chair of the Supervisory Board of the ECB|{DOVE}",
    ])


def bis_zip() -> bytes:
    rows = [("url", "title", "description", "date", "text", "author"),
            ("https://www.bis.org/review/r1.htm", "Olli Rehn: Outlook", "Speech by Mr Olli Rehn, Governor of the Bank of Finland, at H",
             "2026-06-01 00:00:00", DOVE, "Olli Rehn"),
            ("https://www.bis.org/review/r2.htm", "Chiara Scotti: Payments", "Speech by Ms Chiara Scotti, Deputy Governor of the Bank of Italy",
             "2026-06-02 00:00:00", HAWK, "Chiara Scotti"),
            ("https://www.bis.org/review/r3.htm", "Philip R Lane: Policy now", "Speech by Mr Philip R Lane, Member of the Executive Board of the European Central Bank",
             "2026-10-30 00:00:00", HAWK, "Philip R Lane")]
    text = io.StringIO()
    import csv
    csv.writer(text).writerows(rows)
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w") as z:
        z.writestr("speeches_2026.csv", text.getvalue())
    return out.getvalue()


FEED = """<rdf:RDF><item rdf:about="https://www.bis.org/speeches/x"><title>Keeping inflation in check</title>
<link>https://www.bis.org/speeches/20261027-x</link><description>Speech by Mr Olli Rehn, Governor of the Bank of Finland, at Y, 27 October 2026.</description>
<dc:creator>Olli Rehn</dc:creator><dc:date>2026-10-27T00:00:00Z</dc:date></item></rdf:RDF>"""
PAGE = f'<html><div class="text__component"><p>{HAWK}</p></div><div class="publication-body__buttons">PDF</div></html>'


def test_sources_and_dedupe():
    ecb = ecbspeak.ecb_file_docs(ecb_csv())
    assert [(d["speaker"], d["seat"]) for d in ecb] == [("Philip R. Lane", "ECB Executive Board")]  # 2022-06 and Buch left out
    bis = ecbspeak.bis_archive_docs(bis_zip())
    assert [d["speaker"] for d in bis] == ["Olli Rehn", "Philip R Lane"] and bis[0]["speech_title"] == "Outlook"
    merged = ecbspeak._dedupe(ecb + bis)
    lane = [d for d in merged if d["key"] == "lane"]
    assert len(lane) == 1 and lane[0]["source"] == "ECB" and lane[0]["url"] == "https://www.bis.org/review/r3.htm"
    assert ecbspeak.parse_feed(FEED)[0]["url"] == "https://www.bis.org/speeches/20261027-x"
    assert ecbspeak.page_text(PAGE).startswith("Inflation is rising") and "PDF" not in ecbspeak.page_text(PAGE)


class Resp:
    def __init__(self, content=b"", text="", status=200, headers=None):
        self.content, self.text, self.status_code, self.headers = content, text, status, headers or {}

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(response=self)


def test_archive_retries_truncated_files(monkeypatch):
    calls = []

    def get(url, **kw):
        calls.append(url)
        if "2027" in url:
            Resp(status=404).raise_for_status()
        return Resp(content=bis_zip()[:200] if len(calls) < 3 else bis_zip())
    monkeypatch.setattr(http, "get", get)
    assert ecbspeak.archive(2026) == bis_zip() and len(calls) == 3   # two cut-short downloads, then a good one
    assert ecbspeak.archive(2027) is None
    monkeypatch.setattr(http, "get", lambda url, **kw: Resp(content=b"not a zip"))
    assert ecbspeak.archive(2025) is False


def test_cycles():
    thu = pd.Timestamp("2026-10-29")
    assert ecbspeak.cycle_of(thu + pd.Timedelta(days=1)) == thu                          # the Friday after counts
    assert ecbspeak.cycle_of(thu + pd.Timedelta(days=2)) == pd.Timestamp("2026-12-17")   # the Saturday is the next cycle


def doc(day, name, institution, seat, score, title="T"):
    return {"id": f"{day}{name}", "date": day, "speaker": name, "key": ecbspeak.speaker_key(name), "institution": institution,
            "seat": seat, "title": "Governor" if institution != "ECB" else "Executive Board", "speech_title": title, "url": "u",
            "source": "BIS", "words": 1000, "hawkish": 5, "dovish": 1, "score": score, "policy_share": 0.2}


def test_analysis(tmp_path):
    store = Store(tmp_path / "data")
    docs = [doc("2026-10-01", "Isabel Schnabel", "ECB", "ECB Executive Board", 60.0),
            doc("2026-10-02", "Olli Rehn", "FI", "FI", 40.0),
            doc("2026-10-03", "Joachim Nagel", "DE", "DE", 20.0),
            doc("2026-10-05", "Luis de Guindos", "ECB", "ECB Vice-President", 0.0),
            doc("2026-10-06", "Boris Vujčić", "ECB", "ECB Vice-President", 30.0),   # the new holder of the seat
            doc("2026-10-07", "Jose Luis Escrivá", "ES", "ES", None),
            doc("2026-09-01", "Lone Voice", "MT", "MT", -50.0)]                     # alone in its cycle
    store.save_json(ecbspeak.STORE, {"docs": docs, "updated_at": "2026-11-01T06:00:00+00:00"})
    deposit = pd.Series([2.25, 2.25, 2.5], index=pd.to_datetime(["2026-06-17", "2026-10-29", "2026-11-04"]))
    store.save_series("ecb_deposit_rate", deposit)
    a = ecbspeak.analysis(store, today=date(2026, 11, 1))
    assert a["last_full"] == pd.Timestamp("2026-10-29") and a["tone_last"] == pytest.approx((60 + 40 + 20 + 0 + 30) / 5)
    assert pd.isna(a["committee"].loc[pd.Timestamp("2026-09-10"), "tone"])   # fewer than three members
    names = [m["name"] for m in a["members"]]
    assert "Luis de Guindos" not in names and "Boris Vujčić" in names and names[0] == "Isabel Schnabel"
    assert [u["name"] for u in a["unscored"]] == ["Jose Luis Escrivá"] and a["unscored"][0]["spain"]
    assert a["decisions"] == {"hike": {"n": 1, "tone": 30.0}}
    assert ecbspeak.decision_sentence(a["decisions"]) == ("Does it track what the ECB did? The committee's tone averaged "
                                                         "+30 in the 1 cycle that ended in a rate rise.")
    p = ecbspeak.page(store, today=date(2026, 11, 1))
    assert p["next_meeting"] == "17 Dec 2026" and p["quiet_from"] == "10 Dec 2026"
    assert p["charts"][0]["kind"] == "dots" and p["relative"]["rows"]


def test_refresh_and_page(tmp_path, monkeypatch):
    def get(url, **kw):
        if url == ecbspeak.ECB_FILE:
            return Resp(content=ecb_csv().encode("utf-8"))
        if "speeches-2026.zip" in url:
            return Resp(content=bis_zip())
        if "speeches-" in url:
            Resp(status=404).raise_for_status()
        if url == ecbspeak.BIS_FEED:
            return Resp(text=FEED)
        return Resp(text=PAGE)
    monkeypatch.setattr(http, "get", get)
    monkeypatch.setattr(http.session(), "head", lambda url, **kw: Resp(headers={"Last-Modified": "Fri, 30 Oct 2026"}))
    store = Store(tmp_path / "data")
    assert ecbspeak.refresh(store, today=date(2026, 11, 1)).startswith("3 speeches")   # Lane (ECB), Rehn twice
    saved = store.load_json(ecbspeak.STORE)
    assert saved["version"] == speechscore.VERSION and saved["rebuilt_at"] and saved["bis_archive_last"] == "2026-10-30"
    monkeypatch.setattr(http, "get", lambda url, **kw: (_ for _ in ()).throw(requests.ConnectionError("down")))
    assert ecbspeak.refresh(store).startswith("not updated") and len(store.load_json(ecbspeak.STORE)["docs"]) == 3
    build_site(load_registry(), store, site_dir=tmp_path / "site")
    html = (tmp_path / "site" / "ecb-speak.html").read_text(encoding="utf-8")
    assert "econvitals.org/tools/fedspeak/" in html and "word lists" in html and "Upside risks to inflation" in html
    assert 'href="ecb-speak.html"' in (tmp_path / "site" / "tools.html").read_text(encoding="utf-8")
