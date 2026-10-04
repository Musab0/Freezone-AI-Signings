"""RSS/Atom parsing and the zone x AI news-search queries."""

import html
import logging
import re
import urllib.parse
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

from . import config

log = logging.getLogger(__name__)

TAG_RE = re.compile(r"<[^>]+>")


def build_queries():
    """One AI query per zone; leaders also get a deal-focused query."""
    queries = []
    for zone in config.ZONES:
        names = " OR ".join(f'"{a}"' for a in zone["aliases"][:3])
        queries.append((zone["id"], f"({names}) {config.AI_QUERY}"))
        if zone["tier"] == "leader":
            queries.append((zone["id"], f"({names}) {config.AI_QUERY} {config.DEAL_QUERY}"))
    return queries


def clean_text(value):
    if not value:
        return ""
    return re.sub(r"\s+", " ", html.unescape(TAG_RE.sub(" ", value))).strip()


def _parse_date(value):
    if not value:
        return None
    value = value.strip()
    try:
        dt = parsedate_to_datetime(value)
    except (TypeError, ValueError):
        try:
            dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _local(tag):
    return tag.rsplit("}", 1)[-1]


def parse_feed(payload, origin):
    """Parse RSS 2.0 or Atom into plain dicts."""
    try:
        root = ET.fromstring(payload)
    except ET.ParseError as exc:
        log.warning("bad XML from %s: %s", origin, exc)
        return []
    items = []
    for node in root.iter():
        if _local(node.tag) not in ("item", "entry"):
            continue
        fields = {}
        for child in node:
            name = _local(child.tag)
            if name == "link" and child.get("href"):
                fields.setdefault("link", child.get("href"))
            elif name == "source":
                fields["source"] = clean_text(child.text)
                fields.setdefault("source_url", child.get("url"))
            elif child.text and name not in fields:
                fields[name] = child.text
        title = clean_text(fields.get("title"))
        link = (fields.get("link") or "").strip()
        if not title or not link:
            continue
        published = _parse_date(fields.get("pubDate") or fields.get("published") or fields.get("updated")
                                or fields.get("date"))
        items.append({
            "title": title,
            "url": link,
            "summary": clean_text(fields.get("description") or fields.get("summary") or fields.get("encoded"))[:600],
            "source": fields.get("source") or _source_from_url(fields.get("source_url") or link),
            "published": published.isoformat() if published else None,
            "origin": origin,
        })
    return items


def _source_from_url(url):
    host = urllib.parse.urlparse(url or "").netloc.lower()
    return host[4:] if host.startswith("www.") else host
