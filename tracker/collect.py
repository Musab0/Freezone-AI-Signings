"""Run every collection strategy, merge results, and record per-strategy health.

Returns raw items in the shape classify.tag() expects. Never raises for a source failure: each
failure is recorded in the health report instead, so one broken site cannot stop the run.
"""

import logging
import re
import urllib.parse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone

from . import article, config, fetch, sources

log = logging.getLogger(__name__)

MAX_ARTICLES_PER_SOURCE = 25     # detail-page fetches per source per run; the rest wait for the next run
BASELINE_TAKE = 10               # on a source's first run, how many newest links to inspect
MAX_CHILD_SITEMAPS = 6
MAX_DETAIL_ATTEMPTS = 3
TRACKING_PARAMS = re.compile(r"^(utm_|fbclid|gclid|mc_|_hs|hsCtaTracking|hsLang)", re.I)


def normalize_url(url):
    parts = urllib.parse.urlsplit(url.strip())
    query = [(k, v) for k, v in urllib.parse.parse_qsl(parts.query, keep_blank_values=True)
             if not TRACKING_PARAMS.match(k)]
    path = parts.path.rstrip("/") or "/"
    return urllib.parse.urlunsplit((parts.scheme or "https", parts.netloc.lower().removeprefix("www."),
                                    path, urllib.parse.urlencode(query), ""))


class Run:
    """Collects items + health for one pipeline run."""

    def __init__(self, fetcher, state, now, lookback_days=config.LOOKBACK_DAYS, baseline_take=BASELINE_TAKE):
        self.fetcher = fetcher
        self.state = state                      # {"seen": {src: {url: iso}}, "attempts": {url: n}}
        self.state.setdefault("seen", {})
        self.state.setdefault("attempts", {})
        self.now = now
        self.lookback = timedelta(days=lookback_days)
        self.baseline_take = baseline_take
        self.items = []
        self.health = {}                        # source_id -> {strategy -> result}
        self.new_links = {}                     # source_id -> count of never-seen article URLs this run

    # ------------------------------------------------------------ health bookkeeping
    def _record(self, source_id, strategy, ok, count, error="", via="http", url=""):
        self.health.setdefault(source_id, {})[strategy] = {
            "ok": bool(ok), "count": count, "error": error[:300], "via": via, "url": url}

    # ------------------------------------------------------------ strategies
    def _rss(self, src, url):
        resp = self.fetcher.get(url)
        if not resp.ok:
            self._record(src["id"], f"rss:{url}", False, 0, resp.error or f"HTTP {resp.status}", resp.via, url)
            return []
        entries = fetch.parse_feed(resp.text.encode("utf-8"), f"rss:{src['id']}")
        self._record(src["id"], f"rss:{url}", bool(entries), len(entries),
                     "" if entries else "feed parsed but contained no items", resp.via, url)
        return entries

    def _listing(self, src, url, pattern):
        resp = self.fetcher.get(url)
        if not resp.ok:
            self._record(src["id"], f"listing:{url}", False, 0, resp.error or f"HTTP {resp.status}", resp.via, url)
            return []
        links = [l for l in article.extract_links(resp.text, resp.final_url) if pattern.search(l)]
        links = list(dict.fromkeys(links))
        # Zero matches on a page that loaded means the layout or URL scheme changed: flag it.
        self._record(src["id"], f"listing:{url}", bool(links), len(links),
                     "" if links else "page loaded but no article links matched the pattern", resp.via, url)
        return [(l, None) for l in links]

    def _sitemap_urls(self, src):
        spec = src.get("sitemap")
        if not spec:
            return []
        if spec != "auto":
            return [spec]
        found = []
        for domain in [src["domain"]] + src.get("extra_domains", []):
            resp = self.fetcher.get(f"https://www.{domain}/robots.txt", allow_browser=False)
            if resp.ok:
                found += article.sitemaps_from_robots(resp.text)
            if not found:
                found.append(f"https://www.{domain}/sitemap.xml")
        return list(dict.fromkeys(found))

    def _sitemap(self, src, pattern):
        if not src.get("sitemap"):
            return []
        entries, errors, fetched = [], [], 0
        queue = self._sitemap_urls(src)
        seen = set()
        while queue and fetched < MAX_CHILD_SITEMAPS + 3:
            url = queue.pop(0)
            if url in seen:
                continue
            seen.add(url)
            resp = self.fetcher.get(url)
            fetched += 1
            if not resp.ok:
                errors.append(f"{url}: {resp.error or resp.status}")
                continue
            pages, children = article.parse_sitemap(resp.text)
            if not pages and not children:
                errors.append(f"{url}: not a sitemap")
                continue
            if children:
                newsy = [c for c in children if re.search(r"news|press|post|article|media|announce", c, re.I)]
                queue.extend((newsy or children)[:MAX_CHILD_SITEMAPS])
            entries += [(loc, lastmod) for loc, lastmod in pages if pattern.search(loc)]
        label = f"sitemap:{src.get('sitemap')}"
        self._record(src["id"], label, bool(entries), len(entries),
                     "; ".join(errors) if not entries else "", "http", str(src.get("sitemap")))
        return entries

    # ------------------------------------------------------------ official sources
    def official(self, src):
        pattern = re.compile(src.get("pattern") or sources.GENERIC_NEWS_PATTERN, re.I)
        seen = self.state["seen"].setdefault(src["id"], {})
        first_run = not seen
        cutoff = self.now - self.lookback

        # RSS entries are complete items already.
        for url in src.get("rss", []):
            for e in self._rss(src, url):
                key = normalize_url(e["url"])
                if key in seen:
                    continue
                published = article.parse_date(e.get("published"))
                seen[key] = self.now.isoformat()
                self.new_links[src["id"]] = self.new_links.get(src["id"], 0) + 1
                if first_run and (published is None or published < cutoff):
                    continue
                e.update(source=src["name"], zone_hint=src["zone"], official=True)
                self.items.append(e)

        candidates = []                                  # (url, lastmod) in priority order
        for url in src.get("listing", []):
            candidates += self._listing(src, url, pattern)
        sitemap_entries = self._sitemap(src, pattern)
        # Newest sitemap entries first when lastmod is present.
        sitemap_entries.sort(key=lambda e: e[1] or "", reverse=True)
        candidates += sitemap_entries

        ordered, lastmods = [], {}
        for url, lastmod in candidates:
            key = normalize_url(url)
            if key not in lastmods:
                ordered.append((key, url))
            lastmods[key] = lastmods.get(key) or lastmod

        if first_run:
            # Baseline: remember everything that exists today, inspect only the newest few.
            take = {k for k, _ in ordered[:self.baseline_take]}
            take |= {k for k, _ in ordered if (article.parse_date(lastmods[k]) or cutoff) > cutoff}
            for key, _ in ordered:
                if key not in take:
                    seen[key] = self.now.isoformat()

        unseen = [(k, u) for k, u in ordered if k not in seen]
        self.new_links[src["id"]] = self.new_links.get(src["id"], 0) + len(unseen)
        todo = unseen[:MAX_ARTICLES_PER_SOURCE]
        stale = self.now - max(self.lookback, timedelta(days=30))
        detail_ok = detail_fail = dated = 0
        for key, url in todo:
            resp = self.fetcher.get(url)
            attempts = self.state["attempts"].get(key, 0) + 1
            if resp.ok:
                info = article.parse_article(resp.text, resp.final_url)
                detail_ok += 1
                dated += bool(info["published"])
            elif attempts < MAX_DETAIL_ATTEMPTS:
                self.state["attempts"][key] = attempts
                detail_fail += 1
                continue                                  # retry next run
            else:
                info = {"title": "", "description": "", "published": None, "body": ""}
                detail_fail += 1
            self.state["attempts"].pop(key, None)
            seen[key] = self.now.isoformat()
            published = article.parse_date(info["published"]) or article.parse_date(lastmods.get(key))
            if first_run and (published is None or published < cutoff):
                continue
            if published and published < stale:          # an old page newly exposed, not news
                continue
            self.items.append({
                "title": info["title"] or article.title_from_url(url),
                "url": url,
                "summary": info["description"],
                "body": info["body"],
                "source": src["name"],
                "published": published.isoformat() if published else None,
                "origin": f"site:{src['id']}",
                "zone_hint": src["zone"],
                "official": True,
            })
        if todo:
            problems = []
            if detail_fail:
                problems.append(f"{detail_fail} article pages failed")
            # Some newsrooms (e.g. Dubai South, DIC) print no dates; first-seen time is used instead.
            self._record(src["id"], "articles", detail_ok > 0, detail_ok, "; ".join(problems))
        # Domain-restricted news search, independent of the site being reachable at all.
        for domain in [src["domain"]] + src.get("extra_domains", []):
            for e in self.search(f"site:{domain}", src["id"]):
                e.update(zone_hint=src["zone"], official=True)
                self.items.append(e)

    # ------------------------------------------------------------ search + outlets
    def search(self, query, health_id, label=None):
        out = []
        for engine, template in config.SEARCH_FEEDS.items():
            q = f"{query} when:{self.lookback.days}d" if engine == "google_news" else query
            url = template.format(q=urllib.parse.quote(q))
            resp = self.fetcher.get(url, allow_browser=False)
            name = f"search:{engine}" + (f":{label}" if label else "")
            if not resp.ok:
                self._record(health_id, name, False, 0, resp.error or f"HTTP {resp.status}", resp.via, url)
                continue
            entries = fetch.parse_feed(resp.text.encode("utf-8"), f"{engine}:{health_id}")
            looks_like_feed = "<rss" in resp.text[:2000] or "<feed" in resp.text[:2000]
            self._record(health_id, name, looks_like_feed, len(entries),
                         "" if looks_like_feed else "response was not a feed", resp.via, url)
            out += entries
        return out

    def outlet(self, feed):
        resp = self.fetcher.get(feed["url"], allow_browser=False)
        if not resp.ok:
            self._record(f"outlet:{feed['id']}", "rss", False, 0, resp.error or f"HTTP {resp.status}", resp.via,
                         feed["url"])
            return []
        entries = fetch.parse_feed(resp.text.encode("utf-8"), f"feed:{feed['id']}")
        self._record(f"outlet:{feed['id']}", "rss", bool(entries), len(entries),
                     "" if entries else "feed parsed but contained no items", resp.via, feed["url"])
        for e in entries:
            e["source"] = e.get("source") or feed["name"]
        return entries

    def run_all(self, official=True, outlets=True, zone_search=True):
        jobs = []
        if outlets:
            jobs += [("outlet", f) for f in sources.OUTLET_FEEDS]
            zones = " OR ".join(f'"{z["aliases"][0]}"' for z in config.ZONES if z["tier"] != "other")
            jobs += [("search", (f"site:{d} ({zones} OR \"free zone\") {config.AI_QUERY}",
                                 f"outlet-search:{d}", None)) for d in sources.OUTLET_SEARCH_DOMAINS]
        if zone_search:
            jobs += [("search", (q, f"zone-search:{zid}", f"q{i}")) for i, (zid, q) in enumerate(fetch.build_queries())]

        def work(job):
            kind, arg = job
            return self.outlet(arg) if kind == "outlet" else self.search(*arg)

        # Feeds and searches never need the browser, so they can run in parallel.
        with ThreadPoolExecutor(max_workers=6) as pool:
            for batch in pool.map(work, jobs):
                self.items += batch
        # Official sites run in this thread so the browser fallback is available to them.
        if official:
            for src in sources.OFFICIAL:
                try:
                    self.official(src)
                except Exception as exc:  # a bug in one source must not kill the run
                    log.exception("source %s crashed", src["id"])
                    self._record(src["id"], "crash", False, 0, f"{type(exc).__name__}: {exc}")
        return self.items


def summarize(health):
    """Per-source status: ok (a primary strategy works), degraded (only search works), down."""
    out = {}
    for source_id, strategies in health.items():
        primary = {k: v for k, v in strategies.items() if not k.startswith("search")}
        search = {k: v for k, v in strategies.items() if k.startswith("search")}
        if any(v["ok"] for v in primary.values()):
            status = "ok"
        elif primary and any(v["ok"] for v in search.values()):
            status = "degraded"
        elif not primary and any(v["ok"] for v in search.values()):
            status = "ok"
        else:
            status = "down"
        broken = sorted(k for k, v in strategies.items() if not v["ok"])
        out[source_id] = {"status": status, "broken": broken}
    return out


def utcnow():
    return datetime.now(timezone.utc).replace(microsecond=0)
