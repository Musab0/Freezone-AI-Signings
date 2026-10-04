"""Load the analyst-verified seed set (data/seed.json) into the store, then republish the site.

    python -m tracker.seed

Idempotent: items already in the store (same headline fingerprint) are updated, not duplicated.
"""

import json
import os

from . import classify, collect, health, prerender, publish, store

SEED_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "seed.json")


def load_seed(path=None):
    with open(path or SEED_PATH, encoding="utf-8") as fh:
        seed = json.load(fh)
    items = []
    for s in seed["items"]:
        item = {
            "id": classify.fingerprint(s["title"]),
            "title": s["title"], "url": s["url"], "source": s["source"], "published": s["published"],
            "summary": s.get("ai_summary", ""), "zones": s["zones"], "category": s["category"],
            "categories": [s["category"]], "players": classify.find_players(f"{s['title']} {s.get('ai_summary', '')}"),
            "counterparties": s.get("counterparties", []), "ai_summary": s.get("ai_summary", ""),
            "dmcc_angle": s.get("dmcc_angle", ""), "importance": s.get("importance", 3),
            "origin": "research", "official": False, "enriched": True,
            "verified": seed.get("verified_on"), "first_seen": seed.get("verified_on") + "T00:00:00+00:00",
        }
        item["score"] = round((classify.score(item) + item["importance"] * 2) / 2)
        items.append(item)
    return items


def main():
    now = collect.utcnow()
    data = store.load()
    seeded = {i["id"]: i for i in load_seed()}
    data["items"] = [i for i in data["items"] if i["id"] not in seeded] + list(seeded.values())
    data["items"].sort(key=lambda i: i["published"], reverse=True)
    store.save(data)
    publish.write_site_data(data, now, health.load())
    publish.write_feed(data, now, os.environ.get("SITE_URL", ""))
    prerender.prerender()
    print(f"seeded {len(seeded)} verified items; store now holds {len(data['items'])}")


if __name__ == "__main__":
    main()
