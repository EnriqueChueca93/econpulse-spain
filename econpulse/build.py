"""Build the static site in site/ from templates/, static/ and the stored data.

Data is written as a .js file (window.EP = ...) and loaded with a <script> tag,
because browsers block fetch() of .json files on pages opened from disk (file://).
A .json copy is written alongside for anything that wants plain JSON later.
"""

import json
import shutil
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from . import __version__
from .config import SITE_DIR, STATIC_DIR, TEMPLATES_DIR
from .registry import Indicator
from .snapshot import build_snapshot
from .sources import SOURCE_NAMES
from .store import Store


def write_data_js(path: Path, name: str, data: dict) -> None:
    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    path.write_text(f"window.EP = window.EP || {{}};\nwindow.EP.{name} = {payload};\n", encoding="utf-8")


def build_site(indicators: list[Indicator], store: Store | None = None, site_dir: Path = SITE_DIR) -> Path:
    snapshot = build_snapshot(indicators, store)

    data_dir = site_dir / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    write_data_js(data_dir / "snapshot.js", "snapshot", snapshot)
    (data_dir / "snapshot.json").write_text(json.dumps(snapshot, ensure_ascii=False, indent=1), encoding="utf-8")

    shutil.copytree(STATIC_DIR, site_dir / "assets", dirs_exist_ok=True)

    # The build stamp goes on every asset URL so browsers never show a cached, older snapshot.
    build_id = "".join(ch for ch in snapshot["generated_at"] if ch.isdigit())[:14]
    env = Environment(loader=FileSystemLoader(TEMPLATES_DIR), autoescape=select_autoescape(["html"]))
    source_names = list(dict.fromkeys(SOURCE_NAMES.get(i.source, i.source) for i in indicators if not i.is_derived))
    html = env.get_template("index.html").render(
        version=__version__, generated_at=snapshot["generated_at"], build_id=build_id, sources=source_names)
    index = site_dir / "index.html"
    index.write_text(html, encoding="utf-8")
    return index
