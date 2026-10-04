"""Daily pipeline: collect -> tag -> dedupe -> (Claude) -> store -> publish -> health -> (email).

    python -m tracker.run                 # normal daily run
    python -m tracker.run --fixture f.xml # run against a saved RSS file (offline testing)
    python -m tracker.run --lookback 30   # backfill a month on first run
"""

import argparse
import json
import logging
import os

from datetime import datetime

from . import classify, collect, config, enrich, fetch, health, notify, prerender, publish, store
from .http import Fetcher

STATE_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "state.json")


def load_state():
    if os.path.exists(STATE_PATH):
        with open(STATE_PATH, encoding="utf-8") as fh:
            return json.load(fh)
    return {}


def save_state(state):
    with open(STATE_PATH, "w", encoding="utf-8") as fh:
        json.dump(state, fh, ensure_ascii=False, indent=0, sort_keys=True)
        fh.write("\n")


def catch_up_days(data, now):
    """Default lookback, widened to cover any gap since the last completed run (missed cron, outage)."""
    if not data.get("runs"):
        return config.LOOKBACK_DAYS
    last = datetime.fromisoformat(data["runs"][-1]["at"])
    return min(30, max(config.LOOKBACK_DAYS, (now - last).days + 2))


def tag_all(raw):
    """Tag and dedupe. Official-site copies win over search/outlet copies of the same story."""
    raw = sorted(raw, key=lambda r: not r.get("official") or r.get("origin", "").startswith(("google", "bing")))
    out, index = [], {}
    for r in raw:
        item = classify.tag(r)
        if not item:
            continue
        if item["id"] in index:
            first = index[item["id"]]
            if item["source"] and item["source"] != first["source"]:
                alt = first.setdefault("also_in", [])
                if item["source"] not in alt:
                    alt.append(item["source"])
            continue
        index[item["id"]] = item
        out.append(item)
    return out


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixture", help="parse this RSS file instead of hitting the network")
    parser.add_argument("--lookback", type=int, default=None, help="days to look back (default from config)")
    parser.add_argument("--no-email", action="store_true")
    parser.add_argument("--no-browser", action="store_true", help="disable the headless-browser fallback")
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    log = logging.getLogger("tracker")

    now = collect.utcnow()
    site_url = os.environ.get("SITE_URL", "")
    state = load_state()
    hist = health.load()

    if args.fixture:
        with open(args.fixture, "rb") as fh:
            raw = fetch.parse_feed(fh.read(), "fixture")
        run_health, new_links = {}, {}
    else:
        fetcher = Fetcher(use_browser=not args.no_browser)
        lookback = args.lookback or catch_up_days(store.load(), now)
        log.info("looking back %d days", lookback)
        run = collect.Run(fetcher, state, now, lookback_days=lookback)
        try:
            raw = run.run_all()
        finally:
            fetcher.close()
        run_health, new_links = run.health, run.new_links

    data = store.load()
    known = {i["id"] for i in data["items"]} | set(data["rejected"])
    candidates = tag_all(raw)
    fresh = [c for c in candidates if c["id"] not in known]
    rejected = enrich.enrich(fresh)
    data["rejected"] = sorted(set(data["rejected"]) | rejected)
    for c in candidates:
        c.pop("body", None)   # only needed for classification; keeps the store small
    new_items = store.merge(data, [c for c in candidates if c["id"] not in rejected], now)

    if run_health:
        hist = health.update(hist, run_health, new_links, now)
        health.save(hist)
    summary = collect.summarize(run_health)
    data["runs"].append({"at": now.isoformat(), "raw": len(raw), "matched": len(candidates), "new": len(new_items),
                         "sources_ok": sum(1 for s in summary.values() if s["status"] == "ok"),
                         "sources_degraded": sum(1 for s in summary.values() if s["status"] == "degraded"),
                         "sources_down": sum(1 for s in summary.values() if s["status"] == "down")})
    data["runs"] = data["runs"][-90:]
    store.save(data)
    if not args.fixture:
        save_state(state)

    alerts = health.alerts(hist, now)
    publish.write_site_data(data, now, hist)
    publish.write_feed(data, now, site_url)
    digest = publish.write_digest(new_items, now, alerts)
    if not args.fixture:
        prerender.prerender()
    with open(os.path.join(publish.ROOT, "data", "HEALTH.md"), "w", encoding="utf-8") as fh:
        fh.write(health.render_markdown(hist, now))
    log.info("run done: %d raw, %d matched, %d new, %d stored; sources ok=%d degraded=%d down=%d; %d alerts",
             len(raw), len(candidates), len(new_items), len(data["items"]), data["runs"][-1]["sources_ok"],
             data["runs"][-1]["sources_degraded"], data["runs"][-1]["sources_down"], len(alerts))

    if not args.no_email and (new_items or alerts):
        notify.send_digest(digest, f"UAE Free Zone AI Watch - {len(new_items)} new ({now:%d %b})", site_url)


if __name__ == "__main__":
    main()
