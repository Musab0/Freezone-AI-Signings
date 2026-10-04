"""Rule-based tagging: which zone, is it about AI, what kind of move, how significant."""

import hashlib
import re

from . import config

_UAE_RE = re.compile(config.UAE_CONTEXT, re.I)
_AI_RE = re.compile("|".join(config.AI_TERMS), re.I)
_CATEGORY_RES = [(name, re.compile(pattern, re.I)) for name, pattern in config.CATEGORIES]
_PLAYER_RES = [(p, re.compile(r"(?<![\w&])" + re.escape(p) + r"(?![\w&])")) for p in config.MAJOR_PLAYERS]
ZONES_BY_ID = {z["id"]: z for z in config.ZONES}


def _alias_re(alias):
    # Acronyms (all caps) are matched case-sensitively so "dso" in a URL slug or "Difc" typos don't drift.
    flags = 0 if alias.isupper() else re.I
    return re.compile(r"(?<![\w-])" + re.escape(alias) + r"(?![\w-])", flags)


_ZONE_RES = [(z["id"], [(a, _alias_re(a)) for a in z["aliases"]]) for z in config.ZONES]


def clean_title(title, source=""):
    """Google/Bing News append ' - Publisher'; drop it so dedupe works across sources."""
    if source and title.lower().endswith(" - " + source.lower()):
        return title[: -len(source) - 3].strip()
    parts = title.rsplit(" - ", 1)
    if len(parts) == 2 and len(parts[1]) <= 40 and len(parts[0]) > 25:
        return parts[0].strip()
    return title.strip()


def fingerprint(title):
    norm = re.sub(r"[^a-z0-9 ]", "", title.lower())
    norm = re.sub(r"\s+", " ", norm).strip()
    return hashlib.sha1(norm[:90].encode()).hexdigest()[:16]


def detect_zones(text):
    has_uae = bool(_UAE_RE.search(text))
    found = []
    for zone_id, patterns in _ZONE_RES:
        for alias, pattern in patterns:
            if pattern.search(text) and (alias not in config.AMBIGUOUS_ALIASES or has_uae):
                found.append(zone_id)
                break
    # Roll ecosystem brands up to their parent so "Hub71" also counts for ADGM.
    for zone_id in list(found):
        parent = ZONES_BY_ID[zone_id].get("parent")
        if parent and parent not in found:
            found.append(parent)
    return found


def is_ai_related(text):
    return bool(_AI_RE.search(text))


def categorize(text):
    matched = [name for name, pattern in _CATEGORY_RES if pattern.search(text)]
    return (matched[0] if matched else config.DEFAULT_CATEGORY), matched


def find_players(text):
    return [p for p, pattern in _PLAYER_RES if pattern.search(text)]


CATEGORY_WEIGHT = {
    "Partnership / MoU": 3, "Adoption & Deployment": 3, "Product & Launch": 3, "Investment & Funding": 3,
    "Regulation & Policy": 2, "Programmes & Ecosystem": 2, "News & Commentary": 0,
}


def score(item):
    """0-10 'how much should DMCC care' heuristic."""
    s = CATEGORY_WEIGHT.get(item["category"], 1)
    tiers = [ZONES_BY_ID[z]["tier"] for z in item["zones"] if z in ZONES_BY_ID]
    if "leader" in tiers:
        s += 3
    elif "major" in tiers:
        s += 2
    elif tiers:
        s += 1
    s += min(len(item["players"]), 2)
    if _AI_RE.search(item["title"]):
        s += 1
    if any(_alias_re(a).search(item["title"]) for z in item["zones"] for a in ZONES_BY_ID[z]["aliases"]):
        s += 1
    if item.get("official"):
        s += 1
    return min(s, 10)


def is_ai_story(title, summary, body=""):
    """AI in the headline/standfirst, or repeatedly in the article body (one stray nav link is not enough)."""
    if is_ai_related(f"{title}. {summary}"):
        return True
    hits = {m.group(0).lower() for m in _AI_RE.finditer(body or "")}
    return len(_AI_RE.findall(body or "")) >= 3 and len(hits) >= 2


def tag(raw):
    """Turn a raw collected item into a tracked item, or None if it is off-topic."""
    title = clean_title(raw["title"], raw.get("source", ""))
    summary = raw.get("summary", "")
    body = raw.get("body", "")
    text = f"{title}. {summary}"
    zones = detect_zones(f"{text} {body[:3000]}" if raw.get("official") else text)
    hint = raw.get("zone_hint")
    if hint:
        # The publisher's own zone always counts, and comes first.
        zones = [hint] + [z for z in zones if z != hint]
        parent = ZONES_BY_ID.get(hint, {}).get("parent")
        if parent and parent not in zones:
            zones.append(parent)
    if not zones or not is_ai_story(title, summary, body):
        return None
    category, categories = categorize(f"{text} {body[:1500]}")
    item = {
        "id": fingerprint(title),
        "title": title,
        "url": raw["url"],
        "source": raw.get("source", ""),
        "published": raw.get("published"),
        "summary": summary,
        "zones": zones,
        "category": category,
        "categories": categories,
        "players": find_players(f"{text} {body[:3000]}"),
        "origin": raw.get("origin", ""),
        "official": bool(raw.get("official")) and not raw.get("origin", "").startswith(("google", "bing")),
        "enriched": False,
        "body": body[:2000],
    }
    item["score"] = score(item)
    return item
