"""Live self-test of every source and strategy.

    python -m tracker.check              # all sources
    python -m tracker.check difc adgm    # just these official sources

Fetches each source exactly as the daily run does (without touching stored data), prints a
report, writes it to data/CHECK.md and exits 1 if any source has no working strategy.
"""

import argparse
import logging
import os
import sys

from . import collect, sources
from .http import Fetcher

REPORT = os.path.join(os.path.dirname(__file__), "..", "data", "CHECK.md")


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("only", nargs="*", help="official source ids to check (default: everything)")
    parser.add_argument("--no-browser", action="store_true")
    parser.add_argument("--strict", action="store_true", help="also fail when a source is only degraded")
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.WARNING, format="%(levelname)s %(name)s: %(message)s")

    now = collect.utcnow()
    fetcher = Fetcher(use_browser=not args.no_browser)
    run = collect.Run(fetcher, {}, now, lookback_days=30, baseline_take=3)
    try:
        if args.only:
            for src in sources.OFFICIAL:
                if src["id"] in args.only:
                    run.official(src)
        else:
            run.run_all(zone_search=False)
    finally:
        fetcher.close()

    summary = collect.summarize(run.health)
    lines = [f"# Source check - {now:%Y-%m-%d %H:%M} UTC", "",
             "| Source | Status | Strategy | OK | Count | Via | Error |", "|---|---|---|---|---|---|---|"]
    for source_id in sorted(run.health, key=lambda s: (summary[s]["status"] == "ok", s)):
        for name, r in sorted(run.health[source_id].items()):
            lines.append(f"| {source_id} | {summary[source_id]['status']} | {name.split(':http')[0]} | "
                         f"{'yes' if r['ok'] else 'NO'} | {r['count']} | {r['via']} | {r['error'].replace('|', '/')} |")
    counts = {k: sum(1 for s in summary.values() if s["status"] == k) for k in ("ok", "degraded", "down")}
    official_items = [i for i in run.items if i.get("official") and i.get("origin", "").startswith("site:")]
    lines += ["", f"**Sources:** {counts['ok']} ok, {counts['degraded']} degraded, {counts['down']} down. "
              f"**Items collected:** {len(run.items)} ({len(official_items)} article pages from official sites, "
              f"{sum(1 for i in official_items if i.get('published'))} with a publish date)."]
    lines += ["", "## Sample official articles", ""]
    lines += [f"- [{i['source']}] {i['published'] or 'NO DATE'} - {i['title'][:100]}" for i in official_items[:60]]
    report = "\n".join(lines) + "\n"
    os.makedirs(os.path.dirname(REPORT), exist_ok=True)
    with open(REPORT, "w", encoding="utf-8") as fh:
        fh.write(report)
    print(report)
    failing = counts["down"] + (counts["degraded"] if args.strict else 0)
    sys.exit(1 if failing else 0)


if __name__ == "__main__":
    main()
