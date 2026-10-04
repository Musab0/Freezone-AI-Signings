"""Write dashboard data, an RSS feed and a Markdown daily digest."""

import json
import os
from datetime import datetime
from xml.sax.saxutils import escape

from . import config, health
from .classify import ZONES_BY_ID

ROOT = os.path.join(os.path.dirname(__file__), "..")
SITE_DIR = os.path.join(ROOT, "site")
DIGEST_DIR = os.path.join(ROOT, "digests")


def zone_names(item):
    return ", ".join(ZONES_BY_ID[z]["name"] for z in item["zones"] if z in ZONES_BY_ID)


def write_site_data(data, now, hist=None):
    hist = hist or {"sources": {}}
    payload = {
        "health": {
            "alerts": health.alerts(hist, now),
            "sources": [{"id": k, "name": v.get("name", k), "status": v.get("status"), "last_ok": v.get("last_ok"),
                         "working": sorted(n for n, st in v.get("strategies", {}).items() if st.get("ok")),
                         "broken": sorted(n for n, st in v.get("strategies", {}).items() if not st.get("ok"))}
                        for k, v in sorted(hist.get("sources", {}).items())],
        },
        "generated_at": now.isoformat(),
        "zones": [{k: z.get(k) for k in ("id", "name", "emirate", "tier", "self", "parent")} for z in config.ZONES],
        "categories": [name for name, _ in config.CATEGORIES] + [config.DEFAULT_CATEGORY],
        "runs": data["runs"][-30:],
        "items": data["items"],
    }
    os.makedirs(os.path.join(SITE_DIR, "data"), exist_ok=True)
    with open(os.path.join(SITE_DIR, "data", "items.json"), "w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, separators=(",", ":"))


def write_feed(data, now, site_url=""):
    competitors = [i for i in data["items"] if not _is_self_only(i)][:100]
    entries = []
    for i in competitors:
        desc = i.get("ai_summary") or i.get("summary") or ""
        if i.get("dmcc_angle"):
            desc += f"\n\nDMCC angle: {i['dmcc_angle']}"
        entries.append(
            "<item>"
            f"<title>{escape('[' + zone_names(i) + '] ' + i['title'])}</title>"
            f"<link>{escape(i['url'])}</link>"
            f"<guid isPermaLink=\"false\">{i['id']}</guid>"
            f"<category>{escape(i['category'])}</category>"
            f"<pubDate>{datetime.fromisoformat(i['published']).strftime('%a, %d %b %Y %H:%M:%S +0000')}</pubDate>"
            f"<description>{escape(desc)}</description>"
            "</item>"
        )
    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>\n<rss version="2.0"><channel>'
        "<title>UAE Free Zone AI Watch</title>"
        f"<link>{escape(site_url or 'https://github.com/musab0/freezone-ai-signings')}</link>"
        "<description>AI deals, adoption and launches announced by UAE free zones - competitor watch for DMCC"
        "</description>"
        f"<lastBuildDate>{now.strftime('%a, %d %b %Y %H:%M:%S +0000')}</lastBuildDate>"
        + "".join(entries) + "</channel></rss>\n"
    )
    with open(os.path.join(SITE_DIR, "feed.xml"), "w", encoding="utf-8") as fh:
        fh.write(xml)


def _is_self_only(item):
    return all(ZONES_BY_ID.get(z, {}).get("self") for z in item["zones"])


def render_digest(new_items, now, alerts=()):
    competitors = sorted((i for i in new_items if not _is_self_only(i)), key=lambda i: -i["score"])
    own = [i for i in new_items if _is_self_only(i)]
    lines = [f"# UAE Free Zone AI Watch - {now:%d %b %Y}", ""]
    if not competitors:
        lines += ["No new competitor AI announcements detected since the last run.", ""]
    else:
        leaders = [i for i in competitors if {"difc", "adgm"} & set(i["zones"])]
        lines += [f"**{len(competitors)} new competitor items** ({len(leaders)} from DIFC/ADGM).", ""]
        by_cat = {}
        for i in competitors:
            by_cat.setdefault(i["category"], []).append(i)
        for cat, items in sorted(by_cat.items(), key=lambda kv: -max(i["score"] for i in kv[1])):
            lines += [f"## {cat}", ""]
            for i in items:
                lines.append(f"- **[{zone_names(i)}]** [{i['title']}]({i['url']}) - _{i['source']}, "
                             f"{i['published'][:10]}_ (signal {i['score']}/10)")
                if i.get("ai_summary"):
                    lines.append(f"  - {i['ai_summary']}")
                if i.get("dmcc_angle"):
                    lines.append(f"  - DMCC angle: {i['dmcc_angle']}")
            lines.append("")
    if alerts:
        lines += ["## Source health alerts", "", "These scrapers need attention (see data/HEALTH.md):", ""]
        lines += [f"- {a}" for a in alerts] + [""]
    if own:
        lines += ["## For reference: DMCC's own coverage", ""]
        lines += [f"- [{i['title']}]({i['url']}) - _{i['source']}_" for i in own]
        lines.append("")
    return "\n".join(lines)


def write_digest(new_items, now, alerts=()):
    os.makedirs(DIGEST_DIR, exist_ok=True)
    text = render_digest(new_items, now, alerts)
    with open(os.path.join(DIGEST_DIR, f"{now:%Y-%m-%d}.md"), "w", encoding="utf-8") as fh:
        fh.write(text)
    return text
