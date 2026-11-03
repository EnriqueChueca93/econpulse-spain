"""ECB-speak (site/ecb-speak.html): how hawkish or dovish the ECB's Governing Council sounds,
after Econvitals' Fedspeak Tracker, scored with Macroscope's word lists (speechscore.py), not an AI.

Speeches of Governing Council members since September 2022:
    Executive Board          the ECB's own full-text file of its speeches
    national governors       the BIS archive of central bankers' speeches (a zip a year) and,
                             for speeches newer than the archive, the BIS feed (each speech's page)
    board speeches newer     the BIS feed, until the ECB's file catches up
Members are recognised by the role printed with each speech ("Governor of the Bank of Spain",
"Member of the Executive Board of the European Central Bank"), so no list of names needs
keeping. Each fetch adds new speeches; once a month, or when the word lists change, everything
is downloaded and scored again, which also picks up the BIS archive's updates. Only scores,
titles and links are stored and shown, never the texts (the BIS allows non-commercial use).
"""

import csv
import html
import io
import re
import unicodedata
import zipfile
from datetime import date, datetime, timedelta, timezone

import numpy as np
import pandas as pd
import requests

from . import http, i18n, policy, speechscore
from .charts import localise
from .i18n import _
from .sources.base import madrid_today
from .store import Store

STORE = "ecbspeak"   # data/ecbspeak.json
START = "2022-09-01"
REBUILD_DAYS = 30
MAX_PAGES = 40       # speech pages read per fetch
MIN_MEMBERS = 3      # members with a scored speech in a cycle for it to have a committee tone
ECB_FILE = "https://www.ecb.europa.eu/press/key/shared/data/all_ECB_speeches.csv"
ECB_SPEECHES = "https://www.ecb.europa.eu/press/key/html/index.en.html"
BIS_ARCHIVE = "https://www.bis.org/pages/download-central-bankers-speeches/speeches-{year}.zip"
BIS_ARCHIVE_PAGE = "https://www.bis.org/speeches/central-bank/download"
BIS_FEED = "https://www.bis.org/doclist/cbspeeches.rss"

# Euro-area national central banks: code -> (name shown, names used in speech bylines, euro since).
NCBS = {
    "BE": ("National Bank of Belgium", "National Bank of Belgium", None),
    "DE": ("Deutsche Bundesbank", "Deutsche Bundesbank", None),
    "EE": ("Eesti Pank", "Eesti Pank|Bank of Estonia", None),
    "IE": ("Central Bank of Ireland", "Central Bank of Ireland", None),
    "GR": ("Bank of Greece", "Bank of Greece", None),
    "ES": ("Banco de España", "Bank of Spain|Banco de España", None),
    "FR": ("Banque de France", "Bank of France|Banque de France", None),
    "HR": ("Croatian National Bank", "Croatian National Bank", "2023-01-01"),
    "IT": ("Banca d'Italia", "Bank of Italy|Banca d'Italia", None),
    "CY": ("Central Bank of Cyprus", "Central Bank of Cyprus", None),
    "LV": ("Latvijas Banka", "Latvijas Banka|Bank of Latvia", None),
    "LT": ("Bank of Lithuania", "Bank of Lithuania", None),
    "LU": ("Banque centrale du Luxembourg", "Central Bank of Luxembourg|Banque centrale du Luxembourg", None),
    "MT": ("Central Bank of Malta", "Central Bank of Malta", None),
    "NL": ("De Nederlandsche Bank", "Netherlands Bank|De Nederlandsche Bank|Nederlandsche Bank", None),
    "AT": ("Oesterreichische Nationalbank", "Oesterreichische Nationalbank|Austrian National Bank|Central Bank of the Republic of Austria", None),
    "PT": ("Banco de Portugal", "Bank of Portugal|Banco de Portugal", None),
    "SI": ("Banka Slovenije", "Bank of Slovenia|Banka Slovenije", None),
    "SK": ("Národná banka Slovenska", "National Bank of Slovakia|Národná banka Slovenska", None),
    "FI": ("Bank of Finland", "Bank of Finland", None),
    "BG": ("Bulgarian National Bank", "Bulgarian National Bank", "2026-01-01"),
}
_NOT_HEAD = r"(?<!Deputy )(?<!Vice )(?<!Vice-)(?<!Sub-)(?<!Alternate )"
GOVERNOR = {code: re.compile(_NOT_HEAD + r"\b(Governor|President|Chair(?:man|person)? of the Board) of (?:the )?(?:" + names + r")\b")
            for code, (_name, names, _since) in NCBS.items()}
ECB_ROLE = re.compile(_NOT_HEAD + r"\b(President|Vice-President|Member of the Executive Board) of the (?:European Central Bank|ECB)\b")
SEATS_ECB = {"President": "ECB President", "Vice-President": "ECB Vice-President"}
# Members whose role is written in the feminine in Spanish ("presidenta", "gobernadora"), by speaker key.
WOMEN = {"lagarde", "schnabel"}


# ---------------------------------------------------------------- recognising members

def role(byline: str, day: str) -> dict | None:
    """Who is speaking, if a Governing Council member: {'institution', 'seat', 'title'}."""
    m = ECB_ROLE.search(byline)
    if m:
        title = m.group(1)
        return {"institution": "ECB", "seat": SEATS_ECB.get(title, "ECB Executive Board"),
                "title": {"President": "President", "Vice-President": "Vice-President"}.get(title, "Executive Board")}
    for code, pattern in GOVERNOR.items():
        if pattern.search(byline) and (NCBS[code][2] is None or day >= NCBS[code][2]):
            return {"institution": code, "seat": code, "title": "Governor"}
    return None


def speaker_key(name: str) -> str:
    plain = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode().lower()
    words = re.findall(r"[a-z]+", plain)
    return words[-1] if words else plain


# ---------------------------------------------------------------- sources

def _doc(day: str, speaker: str, who: dict, title: str, url: str, source: str, text: str) -> dict:
    s = speechscore.score(text)
    return {"id": url or f"{source}:{day}:{speaker_key(speaker)}:{title[:40]}", "date": day, "speaker": speaker.strip(),
            "key": speaker_key(speaker), **who, "speech_title": title.strip(), "url": url, "source": source,
            "words": len(text.split()), "hawkish": s["hawkish"], "dovish": s["dovish"], "score": s["score"],
            "policy_share": s["policy_share"]}


def _byline_name(byline: str) -> str:
    """'Slides by Piero Cipollone, Member of the Executive Board…' -> 'Piero Cipollone'."""
    m = re.search(r"\bby (?:Mr |Ms |Mrs |Dr |Prof\.? )?([^,]+),", byline)
    return m.group(1).strip() if m else byline


def ecb_file_docs(text: str) -> list[dict]:
    csv.field_size_limit(10**9)
    out = []
    for r in csv.DictReader(io.StringIO(text), delimiter="|"):
        day = (r.get("date") or "")[:10]
        if day < START:
            continue
        who = role(r.get("subtitle", ""), day)
        if not who or who["institution"] != "ECB":
            continue
        speaker = (r.get("speakers") or "").split(",")[0] or _byline_name(r.get("subtitle", ""))
        out.append(_doc(day, speaker, who, r.get("title", ""), "", "ECB", r.get("contents", "")))
    return out


def bis_archive_docs(content: bytes) -> list[dict]:
    csv.field_size_limit(10**9)
    out = []
    with zipfile.ZipFile(io.BytesIO(content)) as z:
        for name in z.namelist():
            for r in csv.DictReader(io.TextIOWrapper(z.open(name), encoding="utf-8")):
                day = (r.get("date") or "")[:10]
                who = role(r.get("description", ""), day) if day >= START else None
                if who:
                    title = re.sub(r"^[^:]{2,60}:\s*", "", r.get("title", ""))   # "Name: Title" -> "Title"
                    out.append(_doc(day, r.get("author", ""), who, title, r.get("url", ""), "BIS", r.get("text", "")))
    return out


def archive(year: int, tries: int = 3):
    """A year's BIS archive as bytes; None if the BIS has not published it; False if it failed.
    The BIS server sometimes cuts a download short, so each file is checked and retried."""
    for _attempt in range(tries):
        try:
            content = http.get(BIS_ARCHIVE.format(year=year)).content
            with zipfile.ZipFile(io.BytesIO(content)) as z:
                if z.testzip() is None:
                    return content
        except requests.HTTPError as e:
            if e.response is not None and e.response.status_code == 404:
                return None
        except (requests.RequestException, zipfile.BadZipFile, EOFError):
            pass
    return False


def parse_feed(xml: str) -> list[dict]:
    items = []
    for item in re.findall(r"<item\b.*?</item>", xml, re.S):
        def tag(name):
            m = re.search(rf"<{name}>(.*?)</{name}>", item, re.S)
            return html.unescape(m.group(1)).strip() if m else ""
        items.append({"title": tag("title"), "url": tag("link"), "byline": tag("description"),
                      "speaker": tag("dc:creator"), "date": tag("dc:date")[:10]})
    return items


def page_text(page_html: str) -> str:
    """The speech text on a BIS speech page (the text block before the download buttons)."""
    start = page_html.find('class="text__component"')
    end = page_html.find("publication-body__buttons", start)
    if start >= 0:   # from the end of the opening tag to the start of the buttons' tag
        start = page_html.find(">", start) + 1
        end = page_html.rfind("<", start, end) if end > 0 else -1
        body = page_html[start:end if end > 0 else None]
    else:
        body = page_html
    body = re.sub(r"<(script|style)\b.*?</\1>", " ", body, flags=re.S)
    return " ".join(html.unescape(re.sub(r"<[^>]+>", " ", body)).split())


def _dedupe(docs: list[dict]) -> list[dict]:
    """The same board speech can come from the ECB's file and the BIS: keep the ECB's, with the BIS link."""
    ecb = {(d["date"], d["key"]): d for d in docs if d["source"] == "ECB"}
    out = []
    for d in docs:
        twin = ecb.get((d["date"], d["key"])) if d["source"] == "BIS" and d["institution"] == "ECB" else None
        if twin is not None:
            twin["url"] = twin["url"] or d["url"]
            continue
        out.append(d)
    return sorted(out, key=lambda d: (d["date"], d["key"]))


def refresh(store: Store, today: date | None = None) -> str:
    """Add new speeches (a full re-read once a month or when the word lists change)."""
    saved = store.load_json(STORE, None) or {}
    now = datetime.now(timezone.utc)
    today = today or madrid_today()
    rebuilt = saved.get("rebuilt_at")
    full = (not saved.get("docs") or saved.get("version") != speechscore.VERSION or not rebuilt
            or (now - datetime.fromisoformat(rebuilt)).days >= REBUILD_DAYS)
    docs = {} if full else {d["id"]: d for d in saved["docs"]}
    meta = {k: saved.get(k) for k in ("rebuilt_at", "ecb_modified", "ecb_last", "bis_archive_last")}
    try:
        head = http.session().head(ECB_FILE, timeout=60, allow_redirects=True)
        modified = head.headers.get("Last-Modified")
        if full or modified != meta.get("ecb_modified"):
            ecb_docs = ecb_file_docs(http.get(ECB_FILE).content.decode("utf-8"))
            docs = {k: d for k, d in docs.items() if d["source"] != "ECB"}
            docs.update({d["id"]: d for d in ecb_docs})
            meta.update(ecb_modified=modified, ecb_last=max((d["date"] for d in ecb_docs), default=None))
        if full:
            archive_last, complete = None, True
            previous = [d for d in saved.get("docs", []) if d["source"] == "BIS"]
            for year in range(int(START[:4]), today.year + 1):
                content = archive(year)
                if content is False:   # failed again: keep that year's speeches and re-read next time
                    complete = False
                    docs.update({d["id"]: d for d in previous if d["date"][:4] == str(year)})
                    continue
                year_docs = bis_archive_docs(content) if content else []   # None: not published yet
                docs.update({d["id"]: d for d in year_docs})
                archive_last = max([archive_last or "", *(d["date"] for d in year_docs)]) or archive_last
            meta.update(bis_archive_last=archive_last or meta.get("bis_archive_last"))
            if complete:
                meta.update(rebuilt_at=now.isoformat(timespec="seconds"))
        new = 0
        for item in parse_feed(http.get(BIS_FEED).text):
            who = role(item["byline"], item["date"])
            if not who or item["url"] in docs or item["date"] < START or new >= MAX_PAGES:
                continue
            if who["institution"] == "ECB" and item["date"] <= (meta.get("ecb_last") or ""):
                continue   # the ECB's own file has it
            text = page_text(http.get(item["url"]).text)
            docs[item["url"]] = _doc(item["date"], item["speaker"], who, item["title"], item["url"], "BIS", text)
            new += 1
    except Exception as e:
        saved.update(error=f"{type(e).__name__}: {e}", failed_at=now.isoformat(timespec="seconds"))
        store.save_json(STORE, saved)
        return f"not updated ({saved['error']})"
    out = _dedupe(list(docs.values()))
    store.save_json(STORE, {"version": speechscore.VERSION, "updated_at": now.isoformat(timespec="seconds"), **meta,
                            "docs": out})
    scored = sum(1 for d in out if d["score"] is not None)
    return f"{len(out)} speeches ({scored} with a policy stance){'; full re-read' if full else f'; {new} new'}"


# ---------------------------------------------------------------- the analysis

MEETINGS = sorted(policy.ECB_PAST_DECISIONS + policy.ECB_DECISIONS)


def cycle_of(day: pd.Timestamp) -> pd.Timestamp | None:
    """The meeting a speech counts toward: the next one, or the one just held, through the Friday after it."""
    return next((m for m in MEETINGS if day <= m + pd.Timedelta(days=1)), None)


def _frame(docs: list[dict]) -> pd.DataFrame:
    df = pd.DataFrame(docs)
    if df.empty:
        return df
    df["date"] = pd.to_datetime(df["date"])
    df["cycle"] = df["date"].map(cycle_of)
    return df


def committee(df: pd.DataFrame) -> pd.DataFrame:
    """Per meeting cycle: the committee's tone (mean of members' average scores), spread and counts."""
    scored = df.dropna(subset=["score"])
    members = scored.groupby(["cycle", "key"])["score"].mean().reset_index()
    out = members.groupby("cycle")["score"].agg(tone="mean", spread="std", members="count",
                                                p25=lambda s: s.quantile(0.25), p75=lambda s: s.quantile(0.75))
    out["documents"] = scored.groupby("cycle").size()
    thin = out["members"] < MIN_MEMBERS   # too few voices to call it the committee's tone
    out.loc[thin, ["tone", "spread", "p25", "p75"]] = np.nan
    return out


def current_members(df: pd.DataFrame, today: pd.Timestamp) -> pd.DataFrame:
    """The latest holder of each seat (ECB President, Vice-President, each national bank) and board
    members heard from in the last six months."""
    latest = df.sort_values("date").groupby("key").tail(1)
    holders = latest.sort_values("date").groupby("seat").tail(1)
    board = latest[(latest["seat"] == "ECB Executive Board") & (latest["date"] >= today - pd.Timedelta(days=183))]
    keep = pd.concat([holders[holders["seat"] != "ECB Executive Board"], board]).drop_duplicates("key")
    return keep[keep["date"] >= today - pd.Timedelta(days=365)]


def _label(row) -> str:
    title = row["title"] if row["institution"] == "ECB" else "Governor"
    if i18n.lang() == "es" and title != "Executive Board" and row["key"] in WOMEN:
        title += " (woman)"   # "Presidenta", "Gobernadora"
    return f"{_short(row['institution'])} · {_(title)}"


def analysis(store: Store, today: date | None = None) -> dict | None:
    saved = store.load_json(STORE, None)
    if not saved or not saved.get("docs"):
        return None
    today = pd.Timestamp(today or madrid_today())
    df = _frame(saved["docs"])
    comm = committee(df)
    scored = df.dropna(subset=["score"]).copy()
    scored["relative"] = scored["score"] - scored["cycle"].map(comm["tone"])
    cycles = [c for c in comm.index if c + pd.Timedelta(days=1) < today]
    last_full = cycles[-1] if cycles else None
    current = cycle_of(today)
    recent_cycles = [c for c in MEETINGS if c <= current][-4:]
    members, unscored = [], []
    for _row, m in current_members(df, today).iterrows():
        own = scored[scored["key"] == m["key"]].sort_values("date")
        year = own[own["date"] >= today - pd.Timedelta(days=365)]
        window = own[own["cycle"].isin(recent_cycles)]
        quiet = window.empty
        basis = year.tail(3) if quiet else window
        if basis.empty:   # nothing scorable in the last year: listed, not plotted
            unscored.append({"name": m["speaker"], "label": _label(m), "spain": m["institution"] == "ES",
                             "speeches": int((df["key"] == m["key"]).sum())})
            continue
        members.append({"key": m["key"], "name": m["speaker"], "label": _label(m), "institution": m["institution"],
                        "stance": round(float(basis["score"].mean()), 1),
                        "relative": round(float(basis["relative"].mean()), 1) if basis["relative"].notna().any() else None,
                        "relative_recent": [None if pd.isna(v) else round(float(v), 1) for v in own["relative"].tail(2).iloc[::-1]],
                        "relative_range": [round(float(year["relative"].min()), 1), round(float(year["relative"].max()), 1)]
                                          if year["relative"].notna().any() else None,
                        "recent": [round(float(v), 1) for v in own["score"].tail(2).iloc[::-1]],
                        "range": [round(float(year["score"].min()), 1), round(float(year["score"].max()), 1)] if not year.empty else None,
                        "n": int(len(basis)), "quiet": quiet, "spain": m["institution"] == "ES"})
    members.sort(key=lambda r: r["stance"], reverse=True)

    def tone(c):
        return None if c is None or c not in comm.index or pd.isna(comm.loc[c, "tone"]) else round(float(comm.loc[c, "tone"]), 1)

    year_ago = min(comm.index, key=lambda c: abs((c - (last_full - pd.Timedelta(days=365))).days)) if last_full is not None else None
    week = df[df["date"] >= today - pd.Timedelta(days=7)].sort_values("date", ascending=False)
    own_avg = {}
    latest = scored.sort_values("date", ascending=False).head(12)
    for _row, d in latest.iterrows():
        prior = scored[(scored["key"] == d["key"]) & (scored["date"] < d["date"])].tail(6)
        own_avg[d["id"]] = round(float(d["score"] - prior["score"].mean()), 1) if not prior.empty else None
    return {
        "updated_at": saved.get("updated_at"), "error": saved.get("error"),
        "ecb_last": saved.get("ecb_last"), "bis_archive_last": saved.get("bis_archive_last"),
        "documents": int(len(df)), "scored": int(len(scored)),
        "last_full": last_full, "current": current, "tone_last": tone(last_full), "tone_current": tone(current),
        "docs_last": int(comm.loc[last_full, "documents"]) if last_full is not None else 0,
        "docs_current": int(comm.loc[current, "documents"]) if current in comm.index else 0,
        "tone_year_ago": tone(year_ago), "year_ago": year_ago,
        "spread_last": round(float(comm.loc[last_full, "spread"]), 1) if last_full is not None and pd.notna(comm.loc[last_full, "spread"]) else None,
        "members": members, "unscored": unscored, "committee": comm, "week": week.to_dict("records"),
        "latest": [{**d, "own": own_avg.get(d["id"])} for d in latest.to_dict("records")],
        "decisions": decision_tones(comm, store.load_series("ecb_deposit_rate")),
    }


def decision_tones(comm: pd.DataFrame, deposit: pd.Series | None) -> dict:
    """The committee's tone in the cycles that ended in a hike, a cut or a hold: does it track the ECB?"""
    if deposit is None or comm.empty:
        return {}
    out: dict[str, list[float]] = {"hike": [], "cut": [], "hold": []}
    for meeting, row in comm.iterrows():
        before = deposit.asof(meeting)
        after = deposit.asof(meeting + pd.Timedelta(days=8))
        if pd.isna(row["tone"]) or pd.isna(before) or pd.isna(after) or meeting > deposit.index[-1]:
            continue
        kind = "hike" if after > before + 1e-9 else "cut" if after < before - 1e-9 else "hold"
        out[kind].append(float(row["tone"]))
    return {k: {"n": len(v), "tone": round(float(np.mean(v)), 1)} for k, v in out.items() if v}


# ---------------------------------------------------------------- the page

def _short(institution: str) -> str:
    return _("ECB") if institution == "ECB" else _(NCBS[institution][0])


def _localised(spec: dict) -> dict:
    """The spec's words in Spanish on the Spanish pass (the English spec is left exactly as it was)."""
    return localise(spec) if i18n.lang() != "en" else spec


def _span(values) -> list[float]:
    """A symmetric x range that fits every value, rounded up to the next 20."""
    top = max([abs(v) for v in values if v is not None] + [20])
    top = min(100, int(np.ceil(top / 20) * 20))
    return [-top, top]


def charts(a: dict) -> dict:
    """The standings (absolute, and relative to the committee) and the committee's tone over time."""
    def rows(kind):
        members = [m for m in a["members"] if (m["stance"] if kind == "absolute" else m["relative"]) is not None]
        key = "stance" if kind == "absolute" else "relative"
        members = sorted(members, key=lambda m: m[key], reverse=True)
        return [{"label": f"{m['name']} · {_short(m['institution'])}", "sub": m["label"] + (" · " + _("quiet lately") if m["quiet"] else ""),
                 "stance": m[key], "recent": m["recent"] if kind == "absolute" else m["relative_recent"],
                 "range": m["range"] if kind == "absolute" else m["relative_range"], "highlight": m["spain"]} for m in members]
    absolute, relative = rows("absolute"), rows("relative")
    base = {"id": "speak-standings", "kind": "dots", "unit": "", "decimals": 0, "left": "dovish", "right": "hawkish",
            "title": "Current standings", "subtitle": "Score, −100 dovish to +100 hawkish",
            "source": _("ECB and BIS speeches; Macroscope word-list scores")}
    standings = _localised({**base, "rows": absolute, "x_range": [-100, 100]})
    relative_spec = _localised({**base, "rows": relative,
                                "x_range": _span([v for r in relative for v in [r["stance"], *(r["range"] or []), *(r["recent"] or [])]])})
    comm = a["committee"].dropna(subset=["tone"])
    x = [d.strftime("%Y-%m-%d") for d in comm.index]
    timeline = {"id": "speak-committee", "kind": "line", "unit": "", "decimals": 0, "signed": True, "freq": "M",
                "title": "Committee tone", "subtitle": "Each meeting cycle, −100 dovish to +100 hawkish",
                "date_format": "%-d %b %Y", "ref_lines": [],
                "series": [{"name": "Committee", "x": x, "y": comm["tone"].round(1).tolist(), "color": "ink"},
                           {"name": "Most hawkish quarter of members", "x": x, "y": comm["p75"].round(1).tolist(), "dash": "dot"},
                           {"name": "Most dovish quarter", "x": x, "y": comm["p25"].round(1).tolist(), "dash": "dot"}],
                "source": _("ECB and BIS speeches; Macroscope word-list scores")}
    return {"charts": [standings, _localised(timeline)], "relative": relative_spec}


def _fmt_day(d) -> str:
    """"29 Oct 2026" / "29 oct 2026"."""
    return i18n.day_month_year(pd.Timestamp(d))


def decision_sentence(decisions: dict) -> str | None:
    """'The committee's tone averaged +35 in the 9 cycles that ended in a rate rise, ...'."""
    phrases = {"hike": ("{tone} in the {n} cycle that ended in a rate rise", "{tone} in the {n} cycles that ended in a rate rise"),
               "cut": ("{tone} in the {n} cycle that ended in a cut", "{tone} in the {n} cycles that ended in a cut"),
               "hold": ("{tone} in the {n} cycle that ended with rates on hold",
                        "{tone} in the {n} cycles that ended with rates on hold")}
    parts = [i18n.ngettext(*phrases[k], decisions[k]["n"]).format(tone=_signed(decisions[k]["tone"]), n=decisions[k]["n"])
             for k in ("hike", "cut", "hold") if k in decisions]
    if not parts:
        return None
    listed = parts[0] if len(parts) == 1 else _("{names} and {last}").format(names=", ".join(parts[:-1]), last=parts[-1])
    return _("Does it track what the ECB did? The committee's tone averaged {listed}.").format(listed=listed)


def _signed(v: float) -> str:
    return ("+" if v > 0 else "−" if v < 0 else "") + f"{abs(v):.0f}"


def page(store: Store, today: date | None = None) -> dict | None:
    a = analysis(store, today)
    if a is None:
        return None
    today = pd.Timestamp(today or madrid_today())
    nxt = next((m for m in MEETINGS if m >= today), None)

    def row(d):
        return {"date": _fmt_day(d["date"]), "name": d["speaker"], "where": _short(d["institution"]),
                "title": d["speech_title"], "url": d.get("url") or ECB_SPEECHES,
                "score": None if pd.isna(d.get("score")) else d["score"],
                "relative": None if pd.isna(d.get("relative", np.nan)) else round(float(d["relative"]), 1),
                "own": d.get("own"), "spain": d["institution"] == "ES"}
    return {
        **{k: a[k] for k in ("documents", "scored", "tone_last", "tone_current", "docs_last", "docs_current",
                             "tone_year_ago", "spread_last", "members", "unscored", "decisions", "error")},
        "updated_at": (a["updated_at"] or "")[:16].replace("T", " "),
        "last_full": _fmt_day(a["last_full"]) if a["last_full"] is not None else None,
        "current": _fmt_day(a["current"]) if a["current"] is not None else None,
        "year_ago": _fmt_day(a["year_ago"]) if a["year_ago"] is not None else None,
        "ecb_last": _fmt_day(a["ecb_last"]) if a["ecb_last"] else None,
        "bis_archive_last": _fmt_day(a["bis_archive_last"]) if a["bis_archive_last"] else None,
        "week": [row(d) for d in a["week"]], "latest": [row(d) for d in a["latest"]],
        "next_meeting": _fmt_day(nxt) if nxt is not None else None,
        "quiet_from": _fmt_day(nxt - pd.Timedelta(days=7)) if nxt is not None else None,
        "groups": [{"side": side, "name": _(g), "note": _(speechscore.GROUP_NOTES[g]), "patterns": pats}
                   for side, lists in speechscore.word_lists().items() for g, pats in lists.items()],
        "min_matches": speechscore.MIN_MATCHES, "min_members": MIN_MEMBERS,
        "decision_text": decision_sentence(a["decisions"]),
        **charts(a),
    }
