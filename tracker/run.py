"""Daily pipeline: fetch -> tag -> dedupe -> (Claude) -> store -> publish -> (email).

    python -m tracker.run                 # normal daily run
    python -m tracker.run --fixture f.xml # run against a saved RSS file (offline testing)
    python -m tracker.run --lookback 30   # backfill a month on first run
"""

import argparse
import logging
import os
from datetime import datetime, timezone

from . import classify, enrich, fetch, notify, publish, store


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixture", help="parse this RSS file instead of hitting the network")
    parser.add_argument("--lookback", type=int, default=None, help="days to look back (default from config)")
    parser.add_argument("--no-email", action="store_true")
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    log = logging.getLogger("tracker")

    now = datetime.now(timezone.utc).replace(microsecond=0)
    site_url = os.environ.get("SITE_URL", "")

    if args.fixture:
        with open(args.fixture, "rb") as fh:
            raw = fetch.parse_feed(fh.read(), "fixture")
        stats = {"feeds_total": 1, "feeds_with_items": 1 if raw else 0}
    else:
        kwargs = {"lookback_days": args.lookback} if args.lookback else {}
        raw, stats = fetch.fetch_all(**kwargs)

    data = store.load()
    known = {i["id"] for i in data["items"]} | set(data["rejected"])
    candidates, seen = [], set()
    for r in raw:
        item = classify.tag(r)
        if item and item["id"] not in seen:
            seen.add(item["id"])
            candidates.append(item)

    fresh = [c for c in candidates if c["id"] not in known]
    rejected = enrich.enrich(fresh)
    data["rejected"] = sorted(set(data["rejected"]) | rejected)
    new_items = store.merge(data, [c for c in candidates if c["id"] not in rejected], now)

    data["runs"].append({"at": now.isoformat(), "raw": len(raw), "matched": len(candidates),
                         "new": len(new_items), **stats})
    data["runs"] = data["runs"][-90:]
    store.save(data)

    publish.write_site_data(data, now)
    publish.write_feed(data, now, site_url)
    digest = publish.write_digest(new_items, now)
    log.info("run done: %d raw, %d matched, %d new, %d total stored",
             len(raw), len(candidates), len(new_items), len(data["items"]))

    if not args.no_email and new_items:
        notify.send_digest(digest, f"UAE Free Zone AI Watch - {len(new_items)} new ({now:%d %b})", site_url)


if __name__ == "__main__":
    main()
