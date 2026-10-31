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

from jinja2 import Environment, FileSystemLoader, select_autoescape

from . import __version__, analytics
from .charts import build_home_charts
from .config import SITE_DIR, STATIC_DIR, TEMPLATES_DIR
from .pages import build_page
from .questions import four_questions
from .registry import Indicator
from .snapshot import build_snapshot
from .sources import SOURCE_NAMES
from .sources.base import MADRID
from .store import Store
from .tables import Data

# Section pages: title, one-line intro, and the batch that fills them in (see PLAN.md).
# What a filled page shows is defined in pages.py.
SECTION_PAGES = {
    "gdp": ("GDP", "What Spain produces, and who is spending: households, firms, government and the rest of the world.", 4),
    "labour": ("Labour market", "Jobs, registrations and unemployment, from the Social Security register and the labour force survey (EPA).", 4),
    "wages": ("Wages", "Pay and labour costs, and how they compare with inflation.", 4),
    "inflation": ("Inflation", "Consumer prices on Spain's own index (IPC) and the harmonised index the ECB targets (IPCA), plus energy prices.", 4),
    "financial": ("Financial", "Spanish bond yields and the prima de riesgo, Euribor, the IBEX 35, the euro and commodities.", 5),
    "ecb": ("ECB", "Spain has no monetary policy of its own: the European Central Bank sets rates for the whole euro area.", 5),
    "fiscal": ("Fiscal", "Government deficit and debt.", 6),
    "activity": ("Activity", "Industry, retail, sentiment surveys, tourism, electricity demand and the external accounts.", 6),
    "housing": ("Housing", "House prices, home sales and mortgage rates.", 6),
    "international": ("International", "Spain next to the euro area and its peers.", 6),
    "regions": ("Regions", "The 17 autonomous communities: unemployment, house prices, inflation and income per head.", 6),
    "analysis": ("Analysis", "EconPulse's own readings: the economy against its history, a GDP nowcast, the 10-year yield split in two, and Taylor rules.", 7),
}

NAV = [("index.html", "Home")] + [(f"{s}.html", t) for s, (t, _, _) in SECTION_PAGES.items()] + [("data.html", "Data")]


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
        row = rows.setdefault(item["source"], {"source": item["source"], "total": 0, "ok": 0, "problems": 0})
        row["total"] += 1
        if item["status"] == "ok" and not item["out_of_date"]:
            row["ok"] += 1
        else:
            row["problems"] += 1
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
    snapshot["readings"] = analytics.home_facts(Data(indicators, store))

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
    common = {
        "version": __version__,
        "build_id": build_id,
        "built": _madrid_time(snapshot["generated_at"]),
        "as_of": _madrid_time(snapshot["data_as_of"]).replace(" Madrid time", ""),
        "sources": list(dict.fromkeys(SOURCE_NAMES.get(i.source, i.source) for i in indicators if not i.is_derived)),
        "nav": NAV,
    }

    def render(template: str, filename: str, **context) -> Path:
        path = site_dir / filename
        html = env.get_template(template).render(**common, active=filename, **context)
        path.write_text(html, encoding="utf-8")
        return path

    index = render("index.html", "index.html", tiles=[by_id[t] for t in snapshot["tiles"]],
                   questions=snapshot["questions"], charts=charts, readings=snapshot["readings"])
    for section, (title, intro, batch) in SECTION_PAGES.items():
        page = build_page(section, indicators, store)
        charts_file = None
        if page["charts"]:
            charts_file = f"data/charts-{section}.js"
            write_data_js(site_dir / charts_file, "charts", page["charts"])
        render("section.html", f"{section}.html", page={"title": title, "intro": intro, "batch": batch},
               blocks=page["blocks"], charts_file=charts_file,
               items=[i for i in items if i["section"] == section])
    groups = [{"id": s, "title": t, "items": [i for i in items if i["section"] == s]} for s, (t, _, _) in SECTION_PAGES.items()]
    render("data.html", "data.html", source_summary=_source_summary(items), groups=[g for g in groups if g["items"]])
    return index
