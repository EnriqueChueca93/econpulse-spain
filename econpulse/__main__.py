"""Command line: python -m econpulse <command>

    fetch   download every indicator into data/ (and INE's release calendar), log what
            changed since the last fetch, and print the latest values
    build   build the static site into site/ from the data already saved
    update  fetch, then build
    list    print the latest values from the data already saved (no download)
    status  freshness report: what failed, what has stopped updating, per source
    forecasts  the forecasters' latest figures, and which await an AI check
    assessments  the pension documents entered by hand, and which await an AI check
    confirm <id> [<id> ...] [--against TEXT] [--note TEXT] [--by NAME]
            record that an AI checked those forecasters' current figures, or a pension
            document's, against the publisher's own document (see econpulse/forecasts.py
            and econpulse/pensions.py); "statedebt" records a check of the Tesoro's list of
            the State's debt (econpulse/statedebt.py)
    serve [--update] [--no-build] [--port N] [--no-browser]
            build the site from the saved data (or fetch fresh data first with --update),
            serve it on this computer and open it in the browser; EconPulse.exe runs this
"""

import argparse
import sys
import time

from . import budget, changes, ecbspeak, forecasts, i18n, pensions, schedule, serve, stance, statedebt
from .build import build_site
from .fetch import fetch_all
from .registry import load_registry
from .snapshot import build_snapshot
from .store import Store
from .tables import Data

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


def print_status(snapshot: dict, catalog: dict, store: Store, known_ids: set[str]) -> int:
    """Per-source summary, then every indicator that needs attention. Returns the number of problems."""
    by_source: dict[str, list[dict]] = {}
    for item in snapshot["indicators"]:
        by_source.setdefault(item["source"], []).append(item)

    headers = ("source", "indicators", "ok", "stale", "error", "not updating")
    rows = []
    for source, items in sorted(by_source.items()):
        count = lambda s: sum(1 for i in items if i["status"] == s)  # noqa: E731
        old = sum(1 for i in items if i["status"] == "ok" and i["out_of_date"])
        rows.append((source, len(items), count("ok") - old, count("stale"), count("error") + count("missing"), old))
    widths = [max(len(str(r[i])) for r in [headers, *rows]) for i in range(len(headers))]
    print("  ".join(h.ljust(w) for h, w in zip(headers, widths)))
    for r in rows:
        print("  ".join(str(c).ljust(w) for c, w in zip(r, widths)))

    problems = [i for i in snapshot["indicators"] if i["status"] != "ok" or i["out_of_date"]]
    if problems:
        print("\nNeeds attention:")
    for item in problems:
        entry = catalog.get(item["id"], {})
        what = "not updating" if item["status"] == "ok" else item["status"]
        print(f"  {item['id']} ({item['source']}): {what}; latest observation {entry.get('last_date', '-')}, "
              f"last successful fetch {entry.get('fetched_at', 'never')}")
        if item.get("error"):
            print(f"      {item['error']}")

    orphans = sorted(p.stem for p in store.series_dir.glob("*.csv") if p.stem not in known_ids)
    if orphans:
        print(f"\nData files with no registry entry (safe to delete): {', '.join(orphans)}")
    if not problems:
        print("\nAll indicators fetched and up to date.")
    return len(problems)


def print_forecasts(data: Data) -> int:
    """Each forecaster's edition, status and figures for this year and next. Returns how many await a check."""
    this, nxt = forecasts.years()
    forecasters = forecasts.forecasters(data)
    for f in sorted(forecasters, key=lambda f: (f.status != forecasts.PENDING, f.id)):
        print(f"{f.id} ({f.name}): {f.status}; published {f.published or '?'}"
              + (f", via {f.via}" if f.via else "") + f"; fingerprint {forecasts.fingerprint(f)}")
        print(f"    source: {f.url}")
        for year in (this, nxt):
            cells = [f"{m} {f.value(year, m)}" for m in forecasts.MEASURE_IDS if f.value(year, m) is not None]
            print(f"    {year}: {', '.join(cells) or '-'}")
            if f.low.get(year):
                print(f"    {year} panel range: " + ", ".join(
                    f"{m} {f.low[year].get(m)} to {f.high[year].get(m)}" for m in forecasts.MEASURE_IDS if m in f.low[year]))
        if f.check:
            print(f"    checked by {f.check['checked_by']} on {f.check['checked_at']}"
                  + (f" against {f.check['checked_against']}" if f.check.get("checked_against") else "")
                  + (f"; note: {f.check['note']}" if f.check.get("note") else ""))
    waiting = [f.id for f in forecasters if f.status == forecasts.PENDING]
    if waiting:
        print(f"\nAwaiting an AI check: {', '.join(waiting)}. Compare each with its source, then run\n"
              f"  python -m econpulse confirm {' '.join(waiting)}")
    return len(waiting)


def print_assessments(store) -> int:
    """The pension documents entered by hand; returns how many await an AI check."""
    docs = pensions.documents(store)
    for d in sorted(docs, key=lambda d: (d.status != pensions.PENDING, d.id)):
        print(f"{d.id} ({d.publisher}, {d.published}): {d.status}; fingerprint {pensions.fingerprint(d.raw)}")
        print(f"    source: {d.url}")
        for f in d.figures:
            print(f"    {f['label']}: {f['value']}" + (f" [{f['where']}]" if f.get("where") else ""))
        if d.check:
            print(f"    checked by {d.check['checked_by']} on {d.check['checked_at']}"
                  + (f" against {d.check['checked_against']}" if d.check.get("checked_against") else ""))
    waiting = [d.id for d in docs if d.status == pensions.PENDING]
    if waiting:
        print(f"\nAwaiting an AI check: {', '.join(waiting)}. Compare each with its source, then run\n"
              f"  python -m econpulse confirm {' '.join(waiting)}")
    return len(waiting)


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser(prog="econpulse", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("command", choices=["fetch", "build", "update", "list", "status", "forecasts", "assessments",
                                            "confirm", "serve"])
    parser.add_argument("ids", nargs="*", help="forecaster ids, for confirm")
    parser.add_argument("--only", help="comma-separated indicator ids to fetch (default: all)")
    parser.add_argument("--against", default="", help="confirm: what the figures were compared with")
    parser.add_argument("--note", default="", help="confirm: a note shown under the forecasts table")
    parser.add_argument("--by", default="AI check (Claude)", help="confirm: who checked the figures")
    parser.add_argument("--update", action="store_true", help="serve: fetch fresh data before building")
    parser.add_argument("--no-build", action="store_true", help="serve: serve site/ as it is, without building")
    parser.add_argument("--port", type=int, help="serve: the port (default: the first free one from 8765)")
    parser.add_argument("--no-browser", action="store_true", help="serve: do not open the browser")
    args = parser.parse_args(argv)

    indicators = load_registry()
    store = Store()
    only = set(args.only.split(",")) if args.only else None
    if only and (unknown := only - {i.id for i in indicators}):
        parser.error(f"unknown indicator id(s): {', '.join(sorted(unknown))}")

    fetching = args.command in ("fetch", "update") or (args.command == "serve" and args.update)
    building = args.command in ("build", "update") or (args.command == "serve" and not args.no_build)
    if fetching:
        started = time.monotonic()
        catalog = fetch_all(indicators, store, only)
        targets = [i.id for i in indicators if only is None or i.id in only]
        ok = sum(1 for i in targets if catalog.get(i, {}).get("status") == "ok")
        print(f"Fetched {ok}/{len(targets)} indicators in {time.monotonic() - started:.1f}s")
        print(f"Release calendar: {schedule.refresh(store)} INE releases saved")
        print(f"Central bank stance (Econvitals): {stance.refresh(store)}")
        print(f"ECB-speak: {ecbspeak.refresh(store)}")
        print(f"Budget explorer (IGAE): {budget.refresh(store)}")
        notes = changes.record(indicators, store)
        print(f"What changed: {len(notes)} new note(s)")
        for n in notes:
            print(f"  - {n['text']}")
        print()

    if args.command in ("fetch", "list"):
        print_table(build_snapshot(indicators, store))

    if args.command == "status":
        print_status(build_snapshot(indicators, store), store.load_catalog(), store, {i.id for i in indicators})
        waiting = [f.id for f in forecasts.pending(Data(indicators, store))]
        if waiting:
            print(f"\nForecasts awaiting an AI check: {', '.join(waiting)} (python -m econpulse forecasts)")
        if statedebt.check(Data(indicators, store))[0] == statedebt.PENDING:
            print("The Tesoro's list of the State's debt awaits an AI check (python -m econpulse confirm statedebt)")

    if args.command == "forecasts":
        print_forecasts(Data(indicators, store))

    if args.command == "assessments":
        print_assessments(store)

    if args.command == "confirm":
        if not args.ids:
            parser.error("confirm needs one or more forecaster ids (see python -m econpulse forecasts)")
        data = Data(indicators, store)
        for forecaster_id in args.ids:
            if forecaster_id == "statedebt":
                try:
                    record = statedebt.confirm(store, args.by, args.note, args.against)
                except ValueError as e:
                    parser.error(str(e))
                print(f"Confirmed the Tesoro's list of {record['as_of']['bonds']}: fingerprint {record['fingerprint']}")
                continue
            if forecaster_id in pensions.document_ids():
                record = pensions.confirm(store, forecaster_id, args.by, args.note, args.against)
                print(f"Confirmed {forecaster_id}: fingerprint {record['fingerprint']}")
                continue
            try:
                record = forecasts.confirm(data, forecaster_id, args.by, args.note, args.against)
            except ValueError as e:
                parser.error(str(e))
            print(f"Confirmed {forecaster_id}: edition of {record['published']}, fingerprint {record['fingerprint']}")

    if building:
        index = build_site(indicators, store)
        print(f"Site built: {index} (in Spanish under es/)")
        if i18n.missing:
            print(f"Spanish: {len(i18n.missing)} texts still in English (add them in scripts/write_catalogue.py)")

    if args.command == "serve":
        try:
            serve.serve(port=args.port, open_browser=not args.no_browser)
        except (FileNotFoundError, OSError) as e:
            print(f"Cannot serve the site: {e}")
            return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
