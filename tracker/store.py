"""JSON file store with dedupe and retention."""

import json
import os
from datetime import datetime, timedelta, timezone

from . import config

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "items.json")


def load(path=DATA_PATH):
    if not os.path.exists(path):
        return {"items": [], "rejected": [], "runs": []}
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)
    data.setdefault("rejected", [])
    data.setdefault("runs", [])
    return data


def save(data, path=DATA_PATH):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=1)
        fh.write("\n")


def merge(data, candidates, now):
    """Add candidates not seen before. Returns the list of genuinely new items."""
    known = {i["id"]: i for i in data["items"]}
    rejected = set(data["rejected"])
    cutoff = now - timedelta(days=config.RETENTION_DAYS)
    new = []
    for item in candidates:
        if item["id"] in rejected:
            continue
        existing = known.get(item["id"])
        if existing:
            # Same story from another outlet: remember the extra source, keep the earliest date.
            alt = existing.setdefault("also_in", [])
            if item["source"] and item["source"] != existing["source"] and item["source"] not in alt:
                alt.append(item["source"])
            continue
        published = _dt(item.get("published")) or now
        if published < cutoff:
            continue
        # Feeds sometimes omit dates or set future ones; never let an item sit in the future.
        item["published"] = min(published, now).isoformat()
        item["first_seen"] = now.isoformat()
        known[item["id"]] = item
        new.append(item)
    data["items"] = sorted(
        (i for i in known.values() if (_dt(i["published"]) or now) >= cutoff),
        key=lambda i: i["published"], reverse=True,
    )
    return new


def _dt(value):
    if not value:
        return None
    try:
        dt = datetime.fromisoformat(value)
    except ValueError:
        return None
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
