"""Global central bank stance (site/stance.html): Econvitals' Global Central Bank Stance Matrix,
shown natively.

Econvitals (econvitals.org, by Jason Furman) publishes the matrix's data in a public
repository and places its own text, charts and estimates in the public domain (CC0 1.0),
asking to be cited. Each fetch saves its latest data.json and desk.json to data/stance.json,
keeping the previous copy if a download fails. The page shows the same information, credited:
policy rates (econvitals' compilation of BIS and central banks' own series), the cycle phase
(its rule), its language-model summaries of decisions, the desk calls it compiles from named
banks' research, the market odds it relays (Kalshi, Polymarket, ASX, CME, Bank of England), its
global diffusion index and the ranked nominal and real rates.
"""

from datetime import date, datetime, timezone

from . import http
from .sources.base import madrid_today
from .store import Store

BASE = "https://raw.githubusercontent.com/econvitals/econvitals-data/main/tools/central-bank-stance"
PAGE = "https://econvitals.org/tools/central-bank-stance/"
TERMS = "https://econvitals.org/terms/"
STORE = "stance"   # data/stance.json
PHASES = {"Hiking": "hiking", "Cutting": "cutting", "On Hold": "hold", "Paused": "paused"}


# ---------------------------------------------------------------- fetching

def _check(data: dict, desk: dict) -> None:
    if not data.get("banks") or "summary" not in data or "diffusion" not in data:
        raise ValueError("unexpected stance data: no banks, summary or diffusion")
    if not isinstance(desk.get("banks"), dict):
        raise ValueError("unexpected desk data: no banks")


def refresh(store: Store) -> str:
    """Download econvitals' latest stance data into data/stance.json; on failure keep the last copy."""
    saved = store.load_json(STORE, None) or {}
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    try:
        data = http.get(f"{BASE}/data.json").json()
        desk = http.get(f"{BASE}/desk.json").json()
        _check(data, desk)
    except Exception as e:  # keep what we had: the page says when it was last fetched
        saved.update(error=f"{type(e).__name__}: {e}", failed_at=now)
        store.save_json(STORE, saved)
        return f"not updated ({saved['error']}); keeping the copy from {saved.get('fetched_at', 'never')}"
    store.save_json(STORE, {"fetched_at": now, "data": data, "desk": desk})
    return f"{len(data['banks'])} central banks, data through {data['summary'].get('as_of', '?')}"


# ---------------------------------------------------------------- the page

def _day(iso: str | None, with_weekday: bool = False) -> str:
    if not iso:
        return ""
    d = date.fromisoformat(iso[:10])
    return (f"{d:%a} " if with_weekday else "") + f"{d:%b} {d.day}" + ("" if d.year == madrid_today().year else f", {d.year}")


def _pct(p: float | None) -> str:
    return "" if p is None else f"{round(100 * p)}%"


def _path_month(point: dict) -> str:
    """'Apr', or "Oct ’28" for a point more than a year ahead."""
    d = date.fromisoformat(point["date"][:7] + "-01")
    return f"{d:%b}" + (f" ’{d:%y}" if (point.get("months") or 0) > 12 else "")


def _market(market: dict) -> dict | None:
    """The deepest source leads; the others say whether they agree, as on econvitals."""
    sources = [s for s in market.get("sources", []) if s]
    priced = [s for s in sources if s.get("p_hike") is not None or s.get("p_hold") is not None]
    out = {"lead": None, "agree": [], "paths": []}
    for s in sources:
        if s.get("implied_path") and s.get("p_hike") is None and s.get("p_hold") is None:
            points = " · ".join(f"{_path_month(p)} {p['rate']:.2f}" for p in s["implied_path"][:4])
            out["paths"].append({"source": s["source"], "text": points, "url": s.get("url")})
    if priced:
        def call(s):
            probs = {"cut": s.get("p_cut") or 0, "hold": s.get("p_hold") or 0, "hike": s.get("p_hike") or 0}
            move = max(probs, key=probs.get)
            return move, probs
        lead = priced[0]
        move, probs = call(lead)
        out["lead"] = {"source": lead["source"], "move": move, "p": _pct(probs[move]), "thin": bool(lead.get("thin")),
                       "detail": f"{_pct(probs['cut'])} cut · {_pct(probs['hold'])} hold · {_pct(probs['hike'])} hike",
                       "for": _day(lead.get("decision_date")), "url": lead.get("url")}
        for s in priced[1:]:
            m, p = call(s)
            out["agree"].append({"source": s["source"], "agrees": m == move, "text": f"{_pct(p[m])} {m}",
                                 "thin": bool(s.get("thin"))})
    return out if (out["lead"] or out["paths"]) else None


def _desk(desk_bank: dict | None) -> dict:
    if not desk_bank:
        return {"consensus": None, "tally": "", "calls": [], "quotes": []}
    lean = desk_bank.get("lean", {})
    n = desk_bank.get("n_desks", 0)
    parts = [f"{lean[k]} {k}" for k in ("hike", "hold", "cut") if lean.get(k)]
    calls = [{"house": c.get("institution", ""), "person": c.get("person") or "", "call": c.get("call", ""),
              "size": c.get("size_bp"), "text": c.get("path") or c.get("note") or "", "note": c.get("note") or "",
              "as_of": _day(c.get("as_of"))} for c in desk_bank.get("calls", [])]
    quotes = [{"house": q.get("institution", ""), "text": q.get("quote", ""), "as_of": _day(q.get("as_of"))}
              for q in desk_bank.get("market_quotes", [])]
    tally = (" · ".join(parts) + f" · {n} house{'s' if n != 1 else ''}") if n else ""
    return {"consensus": desk_bank.get("consensus"), "tally": tally, "calls": calls, "quotes": quotes}


def _real(rate: float, core: dict | None) -> float | None:
    if not core or core.get("value") is None:
        return None
    return ((1 + rate / 100) / (1 + core["value"] / 100) - 1) * 100


def page(store: Store) -> dict | None:
    saved = store.load_json(STORE, None)
    if not saved or "data" not in saved:
        return None
    data, desk = saved["data"], saved.get("desk", {})
    desk_banks = desk.get("banks", {})
    today = madrid_today()
    rows = []
    for order, b in enumerate(data["banks"]):
        decision = b.get("decision") or {}
        statement = (desk_banks.get(b["code"]) or {}).get("statement") or {}
        current = statement.get("announced") and statement.get("announced") == decision.get("announced")
        meeting = b.get("next_meeting") or {}
        days = (date.fromisoformat(meeting["date"]) - today).days if meeting.get("date") else None
        core = (desk_banks.get(b["code"]) or {}).get("core_inflation")
        rows.append({
            "order": order, "code": b["code"], "flag": b.get("flag", ""), "name": b["name"], "country": b.get("country", ""),
            "instrument": b.get("instrument", ""), "rate": b.get("rate"), "rate_display": b.get("rate_display", ""),
            "through": _day(b.get("as_of")), "ytd": b.get("ytd_display", ""),
            "last_move": (b.get("last_move") or {}).get("display", ""),
            "decision": {"title": decision.get("title", ""), "date": _day(decision.get("announced")),
                         "iso": decision.get("announced") or "",
                         "url": decision.get("url"),
                         "summary": statement.get("summary") if current else None,
                         "tilt": statement.get("tilt") if current else None,
                         "vote": statement.get("vote") if current else None},
            "phase": b.get("phase", ""), "phase_class": PHASES.get(b.get("phase", ""), "hold"),
            "next_move": (b.get("next_move") or {}).get("text", ""),
            "next_kind": "desk" if (b.get("next_move") or {}).get("kind") == "desk" else "auto",
            "meeting": _day(meeting.get("date"), with_weekday=True), "meeting_iso": meeting.get("date") or "9999-12-31",
            "days": days, "meeting_url": meeting.get("source_url"), "meeting_rule": meeting.get("source") == "rule",
            "desk": _desk(desk_banks.get(b["code"])), "market": _market(b.get("market") or {}),
            "core": core, "real": _real(b["rate"], core) if b.get("rate") is not None else None,
            "spain": b["code"] == "XM",
        })
    upcoming = sorted((r for r in rows if r["days"] is not None and r["days"] >= 0), key=lambda r: r["days"])[:4]
    s = data["summary"]
    diary = sorted((r for r in rows if r["decision"]["title"]), key=lambda r: r["decision"]["iso"], reverse=True)
    diffusion = data["diffusion"]
    latest = diffusion.get("latest", {})
    return {
        "fetched_at": saved.get("fetched_at"), "error": saved.get("error"),   # a successful refresh clears it
        "built": data["meta"].get("generated_at"), "as_of": s.get("as_of"), "as_of_min": s.get("as_of_min"),
        "counts": {"cutting": s.get("cutting", 0), "hold": s.get("hold", 0), "hiking": s.get("hiking", 0),
                   "paused": s.get("paused", 0), "total": s.get("total", len(rows))},
        "upcoming": upcoming, "rows": rows, "diary": diary,
        "diffusion": {"month": latest.get("month"), "n": diffusion["n"][-1] if diffusion.get("n") else None,
                      "index": diffusion["index"][-1] if diffusion.get("index") else None,
                      "previous": diffusion["index"][-2] if len(diffusion.get("index", [])) > 1 else None,
                      "hiking": [x["name"] for x in latest.get("hiking", [])],
                      "cutting": [x["name"] for x in latest.get("cutting", [])],
                      "hold": len(latest.get("hold", [])), "note": diffusion.get("meta", {}).get("note", "")},
        "method": data["meta"].get("note", ""), "core_note": desk.get("meta", {}).get("core_note", ""),
        "desk_source": desk.get("meta", {}).get("source", ""), "market_sources": data["meta"].get("market_sources", []),
        "fast_sources": data["meta"].get("fast_sources", []), "source": data["meta"].get("source", ""),
    }


def charts(store: Store) -> list[dict]:
    saved = store.load_json(STORE, None)
    if not saved or "data" not in saved:
        return []
    ctx = page(store)
    diff = saved["data"]["diffusion"]
    out = []
    if diff.get("months"):
        x = [f"{m}-01" for m in diff["months"]]
        n = [max(k, 1) for k in diff["n"]]
        out.append({"id": "diffusion", "title": "Global policy diffusion index",
                    "subtitle": f"Share of {diff['n'][-1]} central banks hiking minus share cutting, %, monthly",
                    "kind": "bar", "stack": True, "unit": "%", "decimals": 1, "freq": "M", "signed": True, "ref_lines": [],
                    "series": [{"name": "Share hiking", "x": x, "y": [round(100 * h / k, 1) for h, k in zip(diff["hiking"], n)]},
                               {"name": "Share cutting", "x": x, "y": [round(-100 * c / k, 1) for c, k in zip(diff["cutting"], n)]},
                               {"name": "Index", "x": x, "y": diff["index"], "kind": "line", "color": "ink"}],
                    "source": "Econvitals, from BIS central bank policy rates (CC0)"})
    for key, title, subtitle in (("rate", "Policy rates, nominal", "%, highest to lowest"),
                                 ("real", "Policy rates, real", "%, after core inflation over the last 12 months")):
        ranked = sorted((r for r in ctx["rows"] if r[key] is not None), key=lambda r: r[key], reverse=True)
        if ranked:
            out.append({"id": f"ranked-{key}", "title": title, "subtitle": subtitle, "kind": "hbar", "x_kind": "category",
                        "x_title": "Central bank", "unit": "%", "decimals": 2, "highlight": "ECB", "freq": None,
                        "series": [{"name": title, "x": [_short(r["name"]) for r in ranked],
                                    "y": [round(r[key], 2) for r in ranked]}],
                        "ref_lines": [], "source": "Econvitals (CC0): BIS and central banks; core inflation from national agencies"})
    return out


SHORT = {"Federal Reserve": "Fed", "European Central Bank": "ECB", "Bank of Japan": "BoJ", "Bank of England": "BoE",
         "Bank of Canada": "BoC", "Reserve Bank of Australia": "RBA", "Swiss National Bank": "SNB",
         "Sveriges Riksbank": "Riksbank", "Norges Bank": "Norges Bank", "Reserve Bank of New Zealand": "RBNZ",
         "People's Bank of China": "PBoC", "Reserve Bank of India": "RBI"}


def _short(name: str) -> str:
    return SHORT.get(name, name)
