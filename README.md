# Free Zone AI Watch

**Live site:** https://musab0.github.io/Freezone-AI-Signings/ ([Briefing](https://musab0.github.io/Freezone-AI-Signings/) · [Explore](https://musab0.github.io/Freezone-AI-Signings/explore.html) · [How it works](https://musab0.github.io/Freezone-AI-Signings/how-it-works.html)). Presentation plan: [PLAN.md](PLAN.md).

A daily tracker of **AI contracts, MoUs, adoption, product launches, investment and regulation announced by UAE free zones**. It covers all 56 UAE free zones across the 7 emirates (plus the Hub71 ecosystem), with extra depth on DIFC and ADGM, and describes what each zone announced without comparing or ranking them.

Twice a day (08:07 and 18:07 Dubai time) a GitHub Action:

1. **Scrapes 25 free zone newsrooms directly, and runs news search for every one of the 56 zones.** Sources include DIFC, the DFSA, ADGM, Hub71, Dubai Internet City, Dubai Media City, Dubai Science Park, Dubai Silicon Oasis, DAFZ, JAFZA, Dubai South, DWTC, Dubai Healthcare City, Meydan, IFZA, KEZAD, Masdar and Masdar City, twofour54, RAKEZ, RAK Innovation City, SRTIP, Shams and Ajman. DMCC's own newsroom is scraped too.
2. **Reads the government news agencies' Google News sitemaps.** WAM (Emirates News Agency) and the Abu Dhabi Media Office republish nearly every announcement made by Dubai and Abu Dhabi bodies, free zones included. That gives every zone a second path that is independent of its own website.
3. **Reads 11 news outlet feeds.** These are Arabian Business, The National (business and tech), Khaleej Times, AGBI, TahawulTech, Intelligent CIO, ITP, Fintech News ME, Wamda and Gulf Business. Outlets with broken or bot-protected feeds (Zawya, WAM, Gulf News and others) are covered through news search restricted to their domain.
4. **Searches Google News and Bing News** for each zone combined with AI terms.
5. **Filters and tags each story.** The story must name a tracked zone and an AI term; official articles are checked against their full body text. Each story gets a primary category (Partnership / MoU, Investment, Regulation, Adoption, Product launch, Programmes), notable counterparties and a 0–10 *signal* score.
6. **Optionally runs the story through Claude** (if `ANTHROPIC_API_KEY` is set). Claude removes noise, corrects the category and adds a one-line factual summary.
7. **Dedupes** the same story across the official site, outlets and search, preferring the official copy. It then stores the result, writes a daily digest, updates the dashboard and RSS feed, and can email the digest.

## How the scraper stays reliable

No scraper can guarantee it never breaks: sites redesign, add bot walls or go offline. This one is built so that **one failure never silently loses a source**, and so that **any failure is reported to you**.

| Layer | What it does |
|---|---|
| **Several strategies per source** | Each official newsroom is read through as many of these as it supports, and the results are merged: its RSS feed, its newsroom listing page, its sitemap (found automatically from robots.txt) and domain-restricted Google/Bing News search. If one breaks, the others still deliver. |
| **Verified patterns** | Every listing and sitemap pattern was checked against the live sites (Oct 2026). `tests/test_real_sites.py` keeps real article URLs and navigation URLs as regression samples. |
| **Robust fetching** | A browser user agent, gzip support, retries with backoff, respect for `Retry-After`, and at most one request per host per second. |
| **Three fetch tiers** | Every page is fetched over plain HTTP first. Blocked or challenge pages (Cloudflare, Akamai, Incapsula) are retried in a real headless Chromium browser (Playwright), and then through a rendering reader proxy (Jina Reader by default; set `READER_PROXY` to use your own, or set it empty to switch it off). A newsroom page that loads but shows no article links, because its list is drawn by JavaScript, is re-rendered before it counts as a failure. |
| **Independent second path** | Free zone releases are also collected from the WAM and Abu Dhabi Media Office news sitemaps. A zone whose website is down or blocked is still covered whenever the agencies carry its news. |
| **Self-healing state** | Article URLs are remembered once seen, so nothing is processed twice. Failed article pages are retried on the next two runs, then kept with a title taken from the URL rather than dropped. |
| **Catch-up** | If a run is missed (outage, disabled Actions), the next run widens its lookback to cover the gap, up to 30 days. |
| **Robust date extraction** | Dates are read from JSON-LD, then meta tags, then `<time>`, then the earliest date in the article text. Future dates such as event dates are ignored. When no date exists, the time the story was first seen is used. |
| **Health monitoring** | Every strategy's result is recorded on every run (`data/health.json` and `data/HEALTH.md`, plus the dashboard's **Source health** panel). A strategy counts as **failed** when it errors *or* when a page loads but no article links match, which is how a redesign shows up. |
| **Alerts** | After 2 consecutive failures, or when a newsroom goes quiet for longer than its normal rhythm, a **GitHub issue labelled `source-health`** is opened automatically, along with a section in the digest email. The issue closes itself when the source recovers. |
| **Live CI check** | `python -m tracker.check` exercises every source against the real sites. It runs on every code change and every Monday (`Source check` workflow), and the job fails if any source is completely down. |

Run the live check yourself at any time:

```bash
python -m tracker.check            # every source, writes data/CHECK.md
python -m tracker.check difc adgm  # just these
```

DMCC's own coverage is tracked as a benchmark. It is hidden by default; tick "Include DMCC's own news" to show it.

## Dashboard

- Headline numbers: new items in the last 24h, AI items over 7 days, and DIFC and ADGM items over 30 days.
- **Who's announcing:** AI items by zone over 30 days. Click a zone to filter.
- Feed with search, zone, period, category chips, a "DIFC & ADGM only" filter, and sorting by date or by signal.
- `feed.xml`: subscribe in Outlook or Teams (RSS connector) to get items in your inbox or a channel.

## Setup (one time)

1. Merge this branch into `main`. The scheduled workflow only runs from the default branch.
2. **Hosting:** GitHub Pages serves the `gh-pages` branch, which is a copy of the `docs/` folder. The daily job republishes it after each run. To publish by hand: `git push --force origin "$(git subtree split --prefix docs HEAD)":refs/heads/gh-pages`.
3. **Daily refresh:** this needs GitHub Actions to run on the repo (Settings → Actions → General → "Allow all actions", and no billing hold on the account). The workflow regenerates `docs/` and commits it, and Pages republishes it automatically.
4. Optional settings under Settings → Secrets and variables → Actions:

| Name | Kind | Purpose |
|---|---|---|
| `ANTHROPIC_API_KEY` | secret | Turns on Claude enrichment (summary, noise filter) |
| `SITE_URL` | variable | Your Pages URL, used in the RSS feed and email |
| `DIGEST_TO` | variable | Comma-separated recipients of the daily email |
| `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `SMTP_FROM` | secrets | Mail server for the digest (STARTTLS, default port 587) |

5. **Actions → Daily free zone AI watch → Run workflow** with `lookback = 30` to backfill the last month. After that it runs every day by itself.

## Customising

All watch-list settings are in [`tracker/config.py`](tracker/config.py):

- `ZONES`: add a zone or alias. Set `tier: "leader"` to give a zone deal-specific searches and a higher weight.
- `AI_TERMS`, `CATEGORIES`, `MAJOR_PLAYERS`: what counts as AI, how categories are assigned, and which counterparties raise the signal.
- [`tracker/sources.py`](tracker/sources.py): official newsrooms (listing URL, article URL pattern, sitemap, RSS) and outlet feeds. When you change a pattern, add a real URL to `tests/test_real_sites.py`.
- Claude model: set the `TRACKER_MODEL` env var (default `claude-opus-5-5`).

## Verified data and analyst notes

- `data/seed.json`: analyst-verified announcements. Each headline, date and key fact was checked on the source page. Load or refresh them with `python -m tracker.seed`.
- `data/insights.json`: the briefing's headline and factual findings. Edit it before each leadership briefing; the page picks it up on the next publish.

## Runbook: when a source-health issue opens

1. Open `data/HEALTH.md` (or the issue). It names the source and the failing strategy (`listing:`, `sitemap:`, `rss:`, `articles`).
2. Run `python -m tracker.check <source-id>` locally to reproduce.
3. If the site changed its URL scheme, update the source's `pattern` / `listing` in `tracker/sources.py` and add a real URL to `tests/test_real_sites.py`.
4. If the site blocks automated clients, nothing is lost while other strategies are green (status `degraded`). Escalate only if the source is `down`.

## Run locally

```bash
python -m unittest discover -s tests -t . -v                  # 37 tests, offline
python -m tracker.run --no-email                              # live run (needs internet)
python -m tracker.run --fixture tests/fixture.xml --no-email  # offline run on synthetic data
cd docs && python -m http.server                              # view the site at localhost:8000
```

The core pipeline uses only the Python standard library. `requirements.txt` is needed only for the Claude step.

## Limits

- DAFZ and the DIEZ site block automated clients, and the Dubai Media Office (mediaoffice.ae) publishes no sitemap. These rely on the browser and reader tiers, the government agencies and news search. The health panel shows which tier is working for each source.
- Google News and Bing RSS terms allow personal, non-commercial use. For an organisation-wide deployment, consider a licensed news API; the official newsroom scrapers don't depend on them.
- Without Claude, tagging is keyword-based. Expect some false positives, such as a DIFC-based firm's AI news that doesn't involve DIFC itself, and occasional wrong categories.
- Links from Google News are redirect URLs to the original article.
