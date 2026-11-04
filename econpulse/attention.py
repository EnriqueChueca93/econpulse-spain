"""What awaits an AI check, for the GitHub issue the daily update keeps open while anything does.

Figures read from web pages and PDFs show "awaiting AI check" on the site until an AI has compared them with the
publisher's own document and recorded it with `python -m econpulse confirm` (forecasts.py, pensions.py,
statedebt.py). After each update, .github/workflows/update.yml runs scripts/ai_check_issue.sh, which asks
`python -m econpulse pending` for the issue's text: when something is waiting it opens an issue labelled
"ai-check", so GitHub tells the site's owner (or, when one is open and the list has changed, rewrites it and
comments); when nothing is waiting it closes the issue. A new scraped source with an AI check belongs in waiting().
"""

import hashlib
from datetime import date

from . import forecasts, pensions, statedebt
from .sources import tesoro
from .tables import Data

TITLE = "Figures await an AI check"
MONTHS = "Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split()


def _day(d: date | str | None) -> str:
    if isinstance(d, str):
        d = date.fromisoformat(d)
    return f"{d.day} {MONTHS[d.month - 1]} {d.year}" if d else "date unknown"


def waiting(data: Data) -> list[dict]:
    """Each thing awaiting a check: {"id" (what `confirm` takes), "what", "edition", "url"}."""
    items = []
    for f in sorted(forecasts.pending(data), key=lambda f: f.id):
        items.append({"id": f.id, "what": f"{f.name}: forecasts",
                      "edition": f"edition of {_day(f.published)}" + (f", read via {f.via}" if f.via else ""),
                      "url": f.url or ""})
    for d in sorted(pensions.documents(data.store), key=lambda d: d.id):
        if d.status == pensions.PENDING:
            items.append({"id": d.id, "what": f"{d.publisher}: {d.short}", "edition": d.published, "url": d.url})
    got = statedebt.snapshot(data)
    if got and statedebt.check(data)[0] == statedebt.PENDING:
        as_of = got[0]["as_of"]
        items.append({"id": "statedebt", "what": "Tesoro Público: the State's debt in circulation",
                      "edition": f"Letras as of {_day(as_of['letras'])}, bonds as of {_day(as_of['bonds'])}",
                      "url": tesoro.PAGE})
    return items


def key(items: list[dict]) -> str:
    """Changes when anything waiting changes: a new item, or a new edition of one."""
    body = "\n".join(sorted(f"{x['id']}|{x['edition']}" for x in items))
    return hashlib.sha1(body.encode("utf-8")).hexdigest()[:12]


def issue_body(items: list[dict], mention: str | None = None) -> str:
    """The issue's text (Markdown), or "" when nothing is waiting. The first line carries key() for the script."""
    if not items:
        return ""
    lines = [f"<!-- ai-check: {key(items)} -->",
             "The daily update found figures read from web pages or PDFs that the site shows as \"awaiting AI "
             "check\" until they are compared with the publisher's own document. Forecasts awaiting a check are "
             "left out of the averages.", ""]
    lines += [f"- **{x['what']}** ({x['edition']})" + (f": {x['url']}" if x["url"] else "") for x in items]
    lines += ["", "To clear it, open a Claude session in the project folder and say \"check the updates\": Claude "
              "compares each with its source, records the check and pushes. This issue closes itself when the "
              "site is rebuilt with nothing waiting.", "",
              "```bash", "python -m econpulse confirm " + " ".join(x["id"] for x in items), "```"]
    if mention:
        lines += ["", f"cc @{mention}"]
    return "\n".join(lines) + "\n"
