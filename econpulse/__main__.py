"""Command line: python -m econpulse <command>

    fetch   download every indicator into data/ and print the latest values
    build   build the static site into site/ from the data already saved
    update  fetch, then build
    list    print the latest values from the data already saved (no download)
"""

import argparse
import sys
import time

from .build import build_site
from .fetch import fetch_all
from .registry import load_registry
from .snapshot import build_snapshot
from .store import Store

STATUS_MARK = {"ok": "ok", "stale": "STALE", "error": "ERROR", "missing": "-"}


def print_table(snapshot: dict) -> None:
    rows = []
    for item in snapshot["indicators"]:
        head = item["headline"]
        value = f"{head['display']} {head['label']}".strip() if head else "-"
        status = STATUS_MARK.get(item["status"], item["status"])
        if item["out_of_date"] and item["status"] == "ok":
            status = "OLD"
        if item["flash"]:
            status += " (flash)"
        rows.append((item["id"], item["source"], value, head["period"] if head else "-", status))

    headers = ("indicator", "source", "latest", "period", "status")
    widths = [max(len(str(r[i])) for r in [headers, *rows]) for i in range(len(headers))]
    line = "  ".join(h.ljust(w) for h, w in zip(headers, widths))
    print(line)
    print("-" * len(line))
    for r in rows:
        print("  ".join(str(c).ljust(w) for c, w in zip(r, widths)))

    problems = [i for i in snapshot["indicators"] if i["status"] != "ok"]
    for item in problems:
        print(f"\n! {item['id']}: {item['error']}")
    old = [i["id"] for i in snapshot["indicators"] if i["out_of_date"] and i["status"] == "ok"]
    if old:
        print(f"\n! Not updating recently (check the source still publishes them): {', '.join(old)}")


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser(prog="econpulse", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("command", choices=["fetch", "build", "update", "list"])
    parser.add_argument("--only", help="comma-separated indicator ids to fetch (default: all)")
    args = parser.parse_args(argv)

    indicators = load_registry()
    store = Store()
    only = set(args.only.split(",")) if args.only else None
    if only and (unknown := only - {i.id for i in indicators}):
        parser.error(f"unknown indicator id(s): {', '.join(sorted(unknown))}")

    if args.command in ("fetch", "update"):
        started = time.monotonic()
        catalog = fetch_all(indicators, store, only)
        targets = [i.id for i in indicators if only is None or i.id in only]
        ok = sum(1 for i in targets if catalog.get(i, {}).get("status") == "ok")
        print(f"Fetched {ok}/{len(targets)} indicators in {time.monotonic() - started:.1f}s\n")

    if args.command in ("fetch", "list"):
        print_table(build_snapshot(indicators, store))

    if args.command in ("build", "update"):
        index = build_site(indicators, store)
        print(f"Site built: {index}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
