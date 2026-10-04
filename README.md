# Free Zone AI Watch

A daily tracker of **AI contracts, MoUs, adoption, product launches, investment and regulation announced by UAE free zones**. It focuses on the leaders (DIFC and ADGM) so that DMCC knows what competitors are doing.

Every morning at 08:07 Dubai time a GitHub Action:

1. **Searches** Google News and Bing News for each of the ~20 tracked zones combined with AI terms. DIFC and ADGM get extra searches focused on deals. It also polls regional business and tech feeds (Zawya, Gulf Business, Arabian Business, The National, WAM, TahawulTech, Intelligent CIO, Khaleej Times).
2. **Filters and tags** each story. The story must name a tracked zone and an AI term. Each story gets a primary category (Partnership / MoU, Investment, Regulation, Adoption, Product launch, Programmes), notable counterparties (Microsoft, G42, Nvidia, OpenAI…) and a 0–10 *signal* score.
3. **Optionally runs the story through Claude** (if `ANTHROPIC_API_KEY` is set). Claude removes noise, corrects the category and adds a one-line summary plus a "DMCC angle".
4. **Dedupes** the same story across outlets, stores it in `data/items.json`, writes a Markdown digest to `digests/YYYY-MM-DD.md` and can email that digest.
5. **Publishes** the dashboard and an RSS feed to GitHub Pages.

DMCC's own coverage is tracked as a benchmark. It is hidden by default; tick "Include DMCC's own news" to show it.

## Dashboard

- Headline numbers: new items in the last 24h, competitor items over 7 days, and DIFC and ADGM items over 30 days.
- **Who's moving:** competitor activity by zone over 30 days. Click a zone to filter.
- Feed with search, zone, period, category chips, a "DIFC & ADGM only" filter, and sorting by date or by signal.
- `feed.xml`: subscribe in Outlook or Teams (RSS connector) to get items in your inbox or a channel.

## Setup (one time)

1. Merge this branch into `main`. The scheduled workflow only runs from the default branch.
2. **Settings → Pages → Build and deployment → Source: GitHub Actions.** On private repos, Pages needs a paid GitHub plan. If you don't have one, the dated digests in `digests/` still work.
3. Optional settings under Settings → Secrets and variables → Actions:

| Name | Kind | Purpose |
|---|---|---|
| `ANTHROPIC_API_KEY` | secret | Turns on Claude enrichment (summary, DMCC angle, noise filter) |
| `SITE_URL` | variable | Your Pages URL, used in the RSS feed and email |
| `DIGEST_TO` | variable | Comma-separated recipients of the daily email |
| `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `SMTP_FROM` | secrets | Mail server for the digest (STARTTLS, default port 587) |

4. **Actions → Daily free zone AI watch → Run workflow** with `lookback = 30` to backfill the last month. After that it runs every day by itself.

## Customising

All watch-list settings are in [`tracker/config.py`](tracker/config.py):

- `ZONES`: add a zone or alias. Set `tier: "leader"` to give a zone deal-specific searches and a higher weight.
- `AI_TERMS`, `CATEGORIES`, `MAJOR_PLAYERS`: what counts as AI, how categories are assigned, and which counterparties raise the signal.
- `DIRECT_FEEDS`: add official newsroom or trade-press RSS feeds.
- Claude model: set the `TRACKER_MODEL` env var (default `claude-opus-5-5`).

## Run locally

```bash
python -m unittest discover -s tests -v                       # tests (stdlib only)
python -m tracker.run --no-email                              # live run (needs internet)
python -m tracker.run --fixture tests/fixture.xml --no-email  # offline run on synthetic data
cd site && python -m http.server                              # view dashboard at localhost:8000
```

The core pipeline uses only the Python standard library. `requirements.txt` is needed only for the Claude step.

## Limits

- Coverage depends on what news search engines index. A press release that only appears on a zone's own website and gets no media pickup can be missed. Add that zone's newsroom RSS to `DIRECT_FEEDS` if it has one.
- Without Claude, tagging is keyword-based. Expect some false positives, such as a DIFC-based firm's AI news that doesn't involve DIFC itself, and occasional wrong categories.
- Links from Google News are redirect URLs to the original article.
