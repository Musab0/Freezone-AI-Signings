"""Source health history and alerting.

A strategy that fails once is noise (sites blip); one that fails on consecutive runs is a broken
scraper. Alerts fire when:
  - a source has no working strategy at all (status "down") for ALERT_AFTER_RUNS runs, or
  - a primary strategy (rss/listing/sitemap/articles) fails ALERT_AFTER_RUNS runs in a row, or
  - an official newsroom has published nothing new for longer than its max_silence_days.
"""

import json
import os
from datetime import datetime, timedelta

from . import collect, sources

HEALTH_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "health.json")
ALERT_AFTER_RUNS = 2
SOURCE_NAMES = {s["id"]: s["name"] for s in sources.OFFICIAL}
SOURCE_NAMES.update({f"outlet:{f['id']}": f["name"] for f in sources.OUTLET_FEEDS})
SILENCE = {s["id"]: s.get("max_silence_days") for s in sources.OFFICIAL}


def load(path=HEALTH_PATH):
    if not os.path.exists(path):
        return {"sources": {}}
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def save(data, path=HEALTH_PATH):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=1, sort_keys=True)
        fh.write("\n")


def update(history, run_health, new_links, now):
    """Fold one run's results into the persistent history. Returns the history."""
    stamp = now.isoformat()
    summary = collect.summarize(run_health)
    history["updated"] = stamp
    srcs = history.setdefault("sources", {})
    for source_id, strategies in run_health.items():
        h = srcs.setdefault(source_id, {"name": SOURCE_NAMES.get(source_id, source_id), "strategies": {}})
        h["name"] = SOURCE_NAMES.get(source_id, h.get("name", source_id))
        status = summary[source_id]["status"]
        h["down_runs"] = h.get("down_runs", 0) + 1 if status == "down" else 0
        if status != h.get("status"):
            h["since"] = stamp
        h["status"] = status
        h["last_run"] = stamp
        if status != "down":
            h["last_ok"] = stamp
        if new_links.get(source_id):
            h["last_new"] = stamp
        h.setdefault("first_seen", stamp)
        for name, result in strategies.items():
            s = h["strategies"].setdefault(name, {})
            s["fails"] = 0 if result["ok"] else s.get("fails", 0) + 1
            s.update({k: result[k] for k in ("ok", "count", "error", "via", "url")})
            if result["ok"]:
                s["last_ok"] = stamp
    return history


def alerts(history, now):
    out = []
    for source_id, h in sorted(history.get("sources", {}).items()):
        name = h.get("name", source_id)
        if h.get("down_runs", 0) >= ALERT_AFTER_RUNS:
            errs = "; ".join(f"{k}: {v.get('error')}" for k, v in h["strategies"].items() if not v.get("ok"))
            out.append(f"**{name}** is DOWN ({h['down_runs']} runs): no strategy works. {errs}")
            continue
        for strat, s in sorted(h.get("strategies", {}).items()):
            if not strat.startswith("search") and s.get("fails", 0) >= ALERT_AFTER_RUNS:
                out.append(f"**{name}** - `{strat}` failing {s['fails']} runs in a row: {s.get('error')}"
                           + (" (other strategies still cover this source)" if h.get("status") == "ok" else ""))
        limit = SILENCE.get(source_id)
        last_new = h.get("last_new") or h.get("first_seen")
        if limit and last_new and now - datetime.fromisoformat(last_new) > timedelta(days=limit):
            out.append(f"**{name}** has had no new articles for {limit}+ days - the newsroom may have moved.")
    return out


def render_markdown(history, now):
    lines = ["# Source health", "", f"_Updated {history.get('updated', '')}_", ""]
    al = alerts(history, now)
    if al:
        lines += ["## Alerts", ""] + [f"- {a}" for a in al] + [""]
    else:
        lines += ["All sources healthy.", ""]
    lines += ["| Source | Status | Working strategies | Broken strategies |", "|---|---|---|---|"]
    for source_id, h in sorted(history.get("sources", {}).items(), key=lambda kv: (kv[1].get("status") == "ok", kv[0])):
        good = [f"{k} ({v.get('count')})" for k, v in sorted(h["strategies"].items()) if v.get("ok")]
        bad = [f"{k}: {v.get('error')}" for k, v in sorted(h["strategies"].items()) if not v.get("ok")]
        lines.append(f"| {h.get('name', source_id)} | {h.get('status')} | {', '.join(good) or '-'} | "
                     f"{'<br>'.join(bad).replace('|', '/') or '-'} |")
    return "\n".join(lines) + "\n"
