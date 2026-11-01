"""Build the static site in site/ from templates/, static/ and the stored data.

Pages are rendered in Python (Jinja2), so the content is plain HTML. Data for the
charts is written as .js files (window.EP = ...) and loaded with <script> tags,
because browsers block fetch() of .json files on pages opened from disk (file://).
A .json copy of the snapshot is written alongside for anything that wants plain JSON.
"""

import json
import shutil
from datetime import datetime
from pathlib import Path

import pandas as pd
from jinja2 import Environment, FileSystemLoader, select_autoescape

from . import __version__, analytics, changes, ecbspeak, feed, fiscal, industries, schedule, sectortables, stance, surprises, tools, trade
from .charts import build_home_charts
from .config import SITE_DIR, STATIC_DIR, TEMPLATES_DIR
from .pages import build_page
from .questions import four_questions
from .registry import Indicator
from .snapshot import build_snapshot
from .sources.base import MADRID, madrid_today
from .store import Store
from .tables import Data

# Section pages: title, one-line intro, and the batch that fills them in (see PLAN.md).
# What a filled page shows is defined in pages.py.
SECTION_PAGES = {
    "gdp": ("GDP", "What Spain produces, and who is spending: households, firms, government and the rest of the world.", 4),
    "labour": ("Labour market", "Jobs, unemployment and contracts by sector, from the Social Security register and the public employment service, INE's labour force survey (EPA), who works by age, sex, citizenship and education, the effect of an ageing population, worker flows, hours, vacancies and layoffs.", 4),
    "wages": ("Wages", "Pay and labour costs, how they compare with inflation, and pay by activity.", 4),
    "inflation": ("Inflation", "Consumer prices on Spain's own index (IPC) and the harmonised index the ECB targets (IPCA), underlying inflation across the basket, and energy prices.", 4),
    "financial": ("Financial", "Spanish bond yields and the prima de riesgo, Euribor, the IBEX 35, the euro and commodities, and the IMF-style financial soundness indicators.", 5),
    "ecb": ("ECB", "Spain has no monetary policy of its own: the European Central Bank sets rates for the whole euro area. The IMF-style monetary table shows what that means for the Banco de España and Spanish banks.", 5),
    "fiscal": ("Fiscal", "Government deficit and debt, the IMF-style fiscal tables, and debt sustainability.", 6),
    "activity": ("Activity", "Industry, retail, sentiment surveys, tourism, electricity demand, the external accounts and the IMF-style balance of payments and external debt tables.", 6),
    "housing": ("Housing", "House prices, home sales and mortgage rates.", 6),
    "international": ("International", "Spain next to the euro area and its peers.", 6),
    "regions": ("Regions", "The 17 autonomous communities: unemployment, house prices, inflation and income per head.", 6),
    "analysis": ("Analysis", "EconPulse's own readings: the economy against its history, data surprises, a GDP nowcast, what forecasters expect, the 10-year yield split in two, and Taylor rules.", 7),
}

NAV = ([("index.html", "Home")] + [(f"{s}.html", t) for s, (t, _, _) in SECTION_PAGES.items()]
       + [("trade.html", "Trade"), ("sector-tables.html", "Sector tables"), ("tools.html", "Tools"), ("calendar.html", "Calendar"),
          ("data.html", "Data")])
# What each tab's dropdown lists besides the sections of a section page (anchors or other pages).
NAV_EXTRA = {
    "index.html": [("#key-indicators", "Key indicators"), ("#readings", "EconPulse readings"), ("#whats-new", "What's new"),
                   ("#four-questions", "The economy in four questions"), ("#charts", "Charts")],
    "tools.html": [("#trend", "Economy vs pre-COVID trend"), ("#taylor", "Taylor rule"), ("#rates", "Interest rate decomposer"),
                   ("fiscal-explorer.html", "Fiscal Explorer"), ("ecb-speak.html", "ECB-speak"),
                   ("stance.html", "Global central bank stance")],
    "calendar.html": [("#recent", "Released in the past week"), ("#upcoming", "The next two months")],
    "sector-tables.html": [(f"#{section_id}", title) for section_id, title, *_ in sectortables.PAGE],
    "trade.html": [(f"#{section_id}", title) for section_id, title in trade.PAGE],
}
# Pages a section tab's dropdown lists after that page's own sections.
NAV_SUBPAGES = {"labour.html": [("industry-detail.html", "Every industry")]}


def nav_items(section_pages: dict) -> list[dict]:
    """The tabs, each with the sections its dropdown links to."""
    items = []
    for href, label in NAV:
        section = href.removesuffix(".html")
        if section in section_pages:
            children = [(f"#{b['id']}", b["title"]) for b in section_pages[section]["blocks"]] + NAV_SUBPAGES.get(href, [])
        else:
            children = NAV_EXTRA.get(href, [])
        items.append({"href": href, "label": label, "id": section,
                      "children": [{"href": c if not c.startswith("#") else href + c, "title": t} for c, t in children]})
    return items


def write_data_js(path: Path, name: str, data) -> None:
    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    path.write_text(f"window.EP = window.EP || {{}};\nwindow.EP.{name} = {payload};\n", encoding="utf-8")


def _madrid_time(iso: str | None) -> str:
    if not iso:
        return "never"
    t = datetime.fromisoformat(iso).astimezone(MADRID)
    return f"{t.day} {t:%b %Y}, {t:%H:%M} Madrid time"


def _source_summary(items: list[dict]) -> list[dict]:
    rows: dict[str, dict] = {}
    for item in items:
        row = rows.setdefault(item["source"], {"source": item["source"], "total": 0, "ok": 0, "problems": 0,
                                               "fetched_at": None})
        row["total"] += 1
        if item["status"] == "ok" and not item["out_of_date"]:
            row["ok"] += 1
        else:
            row["problems"] += 1
        if item["fetched_at"] and (row["fetched_at"] is None or item["fetched_at"] > row["fetched_at"]):
            row["fetched_at"] = item["fetched_at"]
    for row in rows.values():
        row["fetched"] = _madrid_time(row["fetched_at"]).replace(" Madrid time", "")
    return sorted(rows.values(), key=lambda r: -r["total"])


def _copy_assets(site_dir: Path) -> None:
    shutil.copytree(STATIC_DIR, site_dir / "assets", dirs_exist_ok=True)
    # Plotly ships inside the Python package, so the site works offline with no CDN.
    import plotly
    bundle = Path(plotly.__file__).parent / "package_data" / "plotly.min.js"
    target = site_dir / "assets" / "plotly.min.js"
    if bundle.exists() and (not target.exists() or target.stat().st_size != bundle.stat().st_size):
        shutil.copyfile(bundle, target)


def build_site(indicators: list[Indicator], store: Store | None = None, site_dir: Path = SITE_DIR) -> Path:
    store = store or Store()
    snapshot = build_snapshot(indicators, store)
    items = snapshot["indicators"]
    by_id = {i["id"]: i for i in items}
    charts = build_home_charts(indicators, store)
    snapshot["questions"] = four_questions(indicators, store)
    readings_data = Data(indicators, store)
    snapshot["readings"] = analytics.home_facts(readings_data) + surprises.surprise_facts(readings_data)

    data_dir = site_dir / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    write_data_js(data_dir / "snapshot.js", "snapshot", snapshot)
    write_data_js(data_dir / "charts.js", "charts", charts)
    (data_dir / "snapshot.json").write_text(json.dumps(snapshot, ensure_ascii=False, indent=1), encoding="utf-8")
    _copy_assets(site_dir)

    # The build stamp goes on every asset URL so browsers never show a cached, older snapshot.
    build_id = "".join(ch for ch in snapshot["generated_at"] if ch.isdigit())[:14]
    env = Environment(loader=FileSystemLoader(TEMPLATES_DIR), autoescape=select_autoescape(["html"]),
                      trim_blocks=True, lstrip_blocks=True)
    section_pages = {s: build_page(s, indicators, store) for s in SECTION_PAGES}   # the navigation lists their sections
    common = {
        "version": __version__,
        "build_id": build_id,
        "built": _madrid_time(snapshot["generated_at"]),
        "as_of": _madrid_time(snapshot["data_as_of"]).replace(" Madrid time", ""),
        "sources": list(dict.fromkeys(i.source_name for i in indicators if not i.is_derived)),
        "nav": nav_items(section_pages),
        "coming_up": schedule.coming_up(store),
    }

    def render(template: str, filename: str, **context) -> Path:
        path = site_dir / filename
        active = context.pop("active", filename)   # a tool page highlights "Tools" in the navigation
        html = env.get_template(template).render(**common, active=active, **context)
        path.write_text(html, encoding="utf-8")
        return path

    today = pd.Timestamp(madrid_today())
    recent = changes.recent_releases(store, by_id, schedule.releases(store, today), today)
    whats_new = {**changes.latest_notes(store), "recent": recent}
    for key in ("at", "updated_at", "started_at"):
        whats_new[key] = _madrid_time(whats_new[key]).replace(" Madrid time", "") if whats_new[key] else None
    index = render("index.html", "index.html", tiles=[by_id[t] for t in snapshot["tiles"]],
                   questions=snapshot["questions"], charts=charts, readings=snapshot["readings"],
                   whats_new=whats_new)
    for section, (title, intro, batch) in SECTION_PAGES.items():
        page = section_pages[section]
        charts_file = None
        if page["charts"]:
            charts_file = f"data/charts-{section}.js"
            write_data_js(site_dir / charts_file, "charts", page["charts"])
        render("section.html", f"{section}.html", page={"title": title, "intro": intro, "batch": batch},
               blocks=page["blocks"], charts_file=charts_file,
               items=[i for i in items if i["section"] == section])
    groups = [{"id": s, "title": t, "items": [i for i in items if i["section"] == s]} for s, (t, _, _) in SECTION_PAGES.items()]
    attention = [i for i in items if i["status"] != "ok" or i["out_of_date"]]
    workbook = sectortables.write_workbook(readings_data, data_dir / sectortables.WORKBOOK, built=common["built"])
    detail = industries.page(readings_data)
    if detail["charts"]:
        write_data_js(data_dir / "charts-industries.js", "charts", detail["charts"])
    render("industry-detail.html", "industry-detail.html", active="labour.html", table=detail["table"],
           sections=detail["sections"], moves=detail["moves"],
           charts_file="data/charts-industries.js" if detail["charts"] else None)
    goods = trade.page(readings_data)
    if goods["charts"]:
        write_data_js(data_dir / "charts-trade.js", "charts", goods["charts"])
    render("trade.html", "trade.html", facts=goods["facts"], table=goods["table"], overview=goods["overview"],
           rankings=goods["rankings"], extras=goods["extras"], sections=goods["sections"], chapters=goods["chapters"], page_nav=trade.PAGE,
           charts_file="data/charts-trade.js" if goods["charts"] else None)
    sector = sectortables.page(readings_data)
    if sector["charts"]:
        write_data_js(data_dir / "charts-sectortables.js", "charts", sector["charts"])
    render("sector-tables.html", "sector-tables.html", sections=sector["sections"],
           charts_file="data/charts-sectortables.js" if sector["charts"] else None,
           workbook=f"data/{sectortables.WORKBOOK}" if workbook else None)
    render("data.html", "data.html", source_summary=_source_summary(items), groups=[g for g in groups if g["items"]],
           attention=attention, total=len(items), workbook=f"data/{sectortables.WORKBOOK}" if workbook else None,
           sector_tables=[(f"{t.section}.html#{t.block}", f"{t.label}. {t.title}") for t in sectortables.TABLES])
    render("calendar.html", "calendar.html", days=schedule.window(store, today), recent=recent,
           calendar_page=schedule.INE_CALENDAR_PAGE)
    counts = {}
    for i in items:
        counts[i["source"]] = counts.get(i["source"], 0) + 1
    render("about.html", "about.html", total=len(items), source_counts=sorted(counts.items(), key=lambda kv: -kv[1]))
    (site_dir / feed.FEED_FILE).write_text(feed.build_feed(store), encoding="utf-8", newline="\n")
    write_data_js(data_dir / "tools.js", "tools", tools.tools_data(Data(indicators, store)))
    render("tools.html", "tools.html", taylor_defaults={"r_star": analytics.R_STAR})
    fx = fiscal.explorer_data(Data(indicators, store))
    if fx:
        write_data_js(data_dir / "fiscal.js", "fiscal", fx)
    render("fiscal-explorer.html", "fiscal-explorer.html", active="tools.html", fx=fx,
           s1_check=fx["s1_check"] if fx else None, past_groups=fiscal.past_groups(fx["history"]) if fx else [])
    speak = ecbspeak.page(store)
    if speak:
        write_data_js(data_dir / "charts-ecbspeak.js", "charts", speak["charts"])
        with open(data_dir / "charts-ecbspeak.js", "a", encoding="utf-8") as f:
            f.write("window.EP.speakRelative = " + json.dumps(speak["relative"], ensure_ascii=False, separators=(",", ":")) + ";\n")
    render("ecb-speak.html", "ecb-speak.html", active="tools.html", p=speak, charts=speak["charts"] if speak else [],
           charts_file="data/charts-ecbspeak.js" if speak else None, ecb_page=ecbspeak.ECB_SPEECHES,
           bis_page=ecbspeak.BIS_ARCHIVE_PAGE)
    stance_charts = stance.charts(store)
    if stance_charts:
        write_data_js(data_dir / "charts-stance.js", "charts", stance_charts)
    render("stance.html", "stance.html", active="tools.html", s=stance.page(store), charts=stance_charts,
           charts_file="data/charts-stance.js" if stance_charts else None,
           econvitals_page=stance.PAGE, econvitals_terms=stance.TERMS)
    return index
