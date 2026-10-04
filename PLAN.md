# Free Zone AI Watch: plan for the CTO and CEO presentations

_Prepared 4 Oct 2026._

## 1. The two audiences and what each will ask

| | **CTO (first meeting)** | **CEO (second meeting)** |
|---|---|---|
| Core question | "Can we trust it, run it and afford it?" | "What are competitors doing, and what should we do?" |
| Will judge on | Architecture, reliability evidence, security and compliance, cost, maintainability, how it fails | A clear answer in under 60 seconds, credibility of sources, implications for DMCC |
| Will reject it if | It's a black box, it fails silently, it depends on fragile scraping with no monitoring, or it has unclear data rights | It's a raw news feed, it's empty, or it has no "so what" |

## 2. Where the product stood before this plan (honest audit)

| # | Gap | Who notices | Severity |
|---|---|---|---|
| G1 | **The dashboard is empty.** The scraper has never run live because GitHub Actions is blocked on the account, so there's nothing to show. | Both | Critical |
| G2 | **It's a news feed, not a briefing.** There's no executive summary, no DMCC-versus-competitors comparison, no trend and no recommendations. | CEO | Critical |
| G3 | **There's no technical story.** Architecture, reliability model, source coverage, security, cost and roadmap live only in the README. | CTO | High |
| G4 | **It isn't hosted.** It has no URL to open in the meeting or on a phone. | Both | High |
| G5 | **Hosting depends on Actions,** which is blocked on this account. | CTO | High |
| G6 | **Source coverage is invisible.** Nobody can see which zones are covered or how. | CTO | Medium |
| G7 | **There's no printable brief** to send before or after the meeting. | CEO | Medium |
| G8 | **It's unclear who looks after it.** There's no runbook for when an alert fires and no ownership model. | CTO | Medium |

## 3. Improvements (what is built in this round)

### For the CEO
1. **Executive briefing as the landing page** (`index.html`):
   - One headline sentence and 4 key findings, each linked to its sources
   - A leader scorecard for DIFC, ADGM and DMCC: AI moves in the last 90 days, the flagship AI initiative, and AI capital or firms reported
   - A monthly chart of AI announcements by zone (DIFC, ADGM, DMCC, others)
   - The top competitor moves, ranked by signal
   - **"What it means for DMCC"**: 4 concrete recommended responses
   - Print-ready, so *Print → PDF* gives a 2-page brief to circulate
2. **Real, verified data.** 19 AI announcements from May–Sep 2026 across 8 competitor free zones and DMCC. Each was opened and checked by hand (headline, date and key facts confirmed on the publisher's page) and links to its source. These records are labelled as analyst-verified so they are never mistaken for automated output.

### For the CTO
3. **"How it works" page** (`how-it-works.html`):
   - An architecture diagram from collection to briefing
   - The 3-tier fetch model (HTTP, headless browser, reader proxy) and the 4 collection strategies per source
   - A live **source coverage matrix** generated from `tracker/sources.py`, so it can't drift from the code
   - Source health, data freshness and alert rules
   - Security and compliance: no credentials stored in the repo, read-only public sources, robots.txt respected, optional Claude step, data-licensing note on news-search feeds
   - Run cost (≈ $0 without Claude; roughly $5–20 a month with it) and test coverage (36 automated tests)
   - Known limitations and a roadmap
4. **Explorer page** (`explore.html`): the full searchable feed and the health panel, for analysts and live questions.

### Hosting and operations
5. **GitHub Pages that doesn't depend on Actions.** The site is a plain static folder (`docs/`) committed to the repo and served by Pages in "Deploy from a branch" mode. The daily pipeline refreshes it once Actions works, but the page stays up even if Actions never runs.
6. **Runbook** in the README: what to do when a source-health issue opens.
7. Remove the temporary Actions probe workflow.

## 4. Running order for the meetings

**CTO (15 min):** How it works → architecture → reliability and health → coverage matrix → security and cost → limitations and roadmap → ask for a budget owner, an Actions or hosting decision, and an API key.

**CEO (10 min):** Briefing headline → leader scorecard → chart → top 3 moves → "What it means for DMCC" → decision asked: approve a weekly AI-competitor brief to the leadership team.

## 5. Out of scope for this round (roadmap)
- SSO-protected hosting (Azure Static Web Apps or an internal server) if the brief should not be public
- Arabic-language sources (WAM Arabic sitemap, Al Khaleej, Al Bayan)
- A Microsoft Teams channel post and Outlook digest via webhook
- Analyst feedback buttons ("relevant / not relevant") to tune the classifier
- Deal-value extraction and a counterparty network view

## 6. Delivery status (executed 4 Oct 2026)

| Item | Status |
|---|---|
| Executive briefing (`docs/index.html`) | Done: headline, KPIs, leader scorecard, monthly chart with table view, type-of-move mix, findings, top moves, recommendations, print-to-PDF |
| Verified data | Done: 19 items in `data/seed.json`, loaded with `python -m tracker.seed`; data-integrity tests added |
| How it works (`docs/how-it-works.html`) | Done: architecture diagram, reliability model, security and cost, coverage matrix generated from code, health, quality, limitations |
| Explorer (`docs/explore.html`) | Done: shared navigation, all-time default, "verified" badge |
| robots.txt compliance | Implemented and tested (it was claimed but not implemented before) |
| Hosting | Static `docs/` folder on `main`, served by GitHub Pages ("Deploy from a branch → main → /docs"). It doesn't depend on Actions |
| Tests | 36 passing |
