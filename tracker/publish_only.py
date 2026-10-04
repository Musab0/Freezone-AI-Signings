"""Regenerate site files from data/items.json without fetching (used after code/site changes)."""

from datetime import datetime, timezone
import os

from . import publish, store

if __name__ == "__main__":
    now = datetime.now(timezone.utc).replace(microsecond=0)
    data = store.load()
    publish.write_site_data(data, now)
    publish.write_feed(data, now, os.environ.get("SITE_URL", ""))
