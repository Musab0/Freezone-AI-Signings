"""Optional Claude pass: confirm relevance, fix the category, write a DMCC-angle note.

Runs only when ANTHROPIC_API_KEY is set; the pipeline works without it on rules alone.
"""

import json
import logging
import os
from typing import List, Literal, Optional

from . import config

log = logging.getLogger(__name__)

MODEL = os.environ.get("TRACKER_MODEL", "claude-opus-5-5")
BATCH_SIZE = 20

CategoryName = Literal[tuple(name for name, _ in config.CATEGORIES) + (config.DEFAULT_CATEGORY,)]  # type: ignore

SYSTEM = f"""You are a competitive-intelligence analyst for DMCC (Dubai Multi Commodities Centre), a UAE free zone.
You screen news about OTHER UAE free zones (especially DIFC and ADGM) and their AI moves: contracts, MoUs,
partnerships, AI adoption/deployment, AI products or platforms, AI licences/regulation, AI investment, AI
programmes/campuses. Zone ids you may use: {", ".join(z["id"] for z in config.ZONES)}.

For each item decide:
- relevant: true only if a UAE free zone authority, its regulator, or its flagship programme/campus is a party
  to, or the announcer of, an AI-related development. A company merely "based in DIFC" announcing something
  unrelated to the zone counts only if it is a notable AI deal signed or launched in/with the zone.
  Stock-price wraps, opinion listicles and duplicate rewrites are not relevant.
- zones: the zone ids actually involved.
- category: the single best category.
- counterparties: named organisations on the other side of the deal (empty if none).
- summary: one factual sentence (max 35 words) of what was announced.
- dmcc_angle: one sentence (max 30 words) on why DMCC should care or how it could respond.
- importance: 1 (trivia) to 5 (strategic move DMCC leadership should hear about this week).
Base everything only on the text given; do not invent facts."""

try:
    import anthropic
    from pydantic import BaseModel

    class Judgement(BaseModel):
        id: str
        relevant: bool
        zones: List[str]
        category: CategoryName
        counterparties: List[str]
        summary: str
        dmcc_angle: str
        importance: int

    class Judgements(BaseModel):
        items: List[Judgement]
except ImportError:  # optional dependency
    anthropic = None


def _client() -> Optional["anthropic.Anthropic"]:
    if not os.environ.get("ANTHROPIC_API_KEY"):
        log.info("ANTHROPIC_API_KEY not set - skipping Claude enrichment")
        return None
    if anthropic is None:
        log.warning("anthropic/pydantic not installed - skipping Claude enrichment")
        return None
    return anthropic.Anthropic()


def enrich(items):
    """Enrich items in place. Returns the ids Claude judged irrelevant."""
    client = _client()
    pending = [i for i in items if not i.get("enriched")]
    if not client or not pending:
        return set()
    rejected = set()
    valid_zones = {z["id"] for z in config.ZONES}
    for start in range(0, len(pending), BATCH_SIZE):
        batch = pending[start:start + BATCH_SIZE]
        payload = [{"id": i["id"], "title": i["title"], "source": i["source"], "published": i["published"],
                    "snippet": i["summary"][:400], "rule_zones": i["zones"], "rule_category": i["category"]}
                   for i in batch]
        try:
            response = client.messages.parse(
                model=MODEL,
                max_tokens=16000,
                system=SYSTEM,
                messages=[{"role": "user", "content": "Classify these news items:\n" + json.dumps(payload)}],
                output_format=Judgements,
            )
        except anthropic.APIStatusError as exc:
            log.warning("Claude batch failed (%s) - keeping rule-based tags", exc.status_code)
            continue
        except anthropic.APIConnectionError as exc:
            log.warning("Claude unreachable (%s) - keeping rule-based tags", exc)
            continue
        if response.stop_reason == "refusal" or response.parsed_output is None:
            log.warning("Claude returned no parsable output (stop_reason=%s)", response.stop_reason)
            continue
        by_id = {i["id"]: i for i in batch}
        for j in response.parsed_output.items:
            item = by_id.get(j.id)
            if not item:
                continue
            item["enriched"] = True
            if not j.relevant:
                rejected.add(j.id)
                continue
            zones = [z for z in j.zones if z in valid_zones]
            if zones:
                item["zones"] = zones
            item["category"] = j.category
            item["counterparties"] = j.counterparties
            item["ai_summary"] = j.summary
            item["dmcc_angle"] = j.dmcc_angle
            item["importance"] = max(1, min(5, j.importance))
            item["score"] = round((item["score"] + item["importance"] * 2) / 2)
    log.info("Claude enriched %d items, rejected %d", len(pending), len(rejected))
    return rejected
