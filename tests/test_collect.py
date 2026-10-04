import unittest
from datetime import datetime, timezone

from tracker import article, collect, health
from tracker.http import Response, looks_blocked

NOW = datetime(2026, 10, 4, 6, 0, tzinfo=timezone.utc)
EMPTY_FEED = '<?xml version="1.0"?><rss version="2.0"><channel><title>x</title></channel></rss>'


class FakeFetcher:
    def __init__(self, pages):
        self.pages = dict(pages)
        self.calls = []

    def get(self, url, allow_browser=True):
        self.calls.append(url)
        if "news.google.com" in url or "bing.com" in url:
            return Response(url, 200, EMPTY_FEED, url)
        if url in self.pages:
            body = self.pages[url]
            if isinstance(body, Response):
                return body
            return Response(url, 200, body, url)
        return Response(url, 404, "", url, error="HTTP 404")


def listing(n, start=0):
    links = "".join(f'<li><a href="/news/story-number-{i}">Story {i}</a></li>' for i in range(start, start + n))
    return f"<html><body><nav><a href='/about'>About</a></nav><main><ul>{links}</ul></main></body></html>"


def article_page(title, date_iso=None, body="Plain business update.", human_date=None):
    ld = (f'<script type="application/ld+json">{{"@type":"NewsArticle","headline":"{title}",'
          f'"datePublished":"{date_iso}"}}</script>') if date_iso else ""
    return (f"<html><head><title>{title} | Site</title><meta property='og:description' content='Desc of {title}'>"
            f"{ld}</head><body><nav>Dubai AI Campus menu AI AI</nav><article><h1>{title}</h1>"
            f"{'<p>' + human_date + '</p>' if human_date else ''}<p>{body}</p></article></body></html>")


SRC = {"id": "testzone", "zone": "difc", "name": "Test Newsroom", "domain": "example.ae",
       "listing": ["https://www.example.ae/news"], "pattern": r"example\.ae/news/story-number-\d+$"}


class ArticleParsingTest(unittest.TestCase):
    def test_jsonld_meta_and_nav_stripping(self):
        info = article.parse_article(article_page("DIFC signs AI MoU", "2026-10-02T09:00:00+04:00"), "https://x")
        self.assertEqual(info["title"], "DIFC signs AI MoU")
        self.assertEqual(info["description"], "Desc of DIFC signs AI MoU")
        self.assertEqual(info["published"], "2026-10-02T05:00:00+00:00")
        self.assertNotIn("menu", info["body"])

    def test_human_date_fallbacks(self):
        for text, expected in [("28 Sept 2026", "2026-09-28"), ("July 2, 2026", "2026-07-02"),
                               ("22nd October 2025", "2025-10-22"), ("Published 2026-01-05", "2026-01-05")]:
            info = article.parse_article(article_page("T", human_date=text), "https://x")
            self.assertTrue(info["published"].startswith(expected), text)

    def test_sitemap_index_and_urlset(self):
        index = ('<?xml version="1.0"?><sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
                 '<sitemap><loc>https://e.ae/post-sitemap.xml</loc></sitemap>'
                 '<sitemap><loc>https://e.ae/page-sitemap.xml</loc></sitemap></sitemapindex>')
        pages, children = article.parse_sitemap(index)
        self.assertEqual((pages, children), ([], ["https://e.ae/post-sitemap.xml", "https://e.ae/page-sitemap.xml"]))
        urlset = ('﻿<?xml version="1.0"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
                  '<url><loc> https://e.ae/news/a </loc><lastmod>2026-10-01</lastmod></url></urlset>')
        self.assertEqual(article.parse_sitemap(urlset)[0], [("https://e.ae/news/a", "2026-10-01")])
        self.assertEqual(article.parse_sitemap("<html>not xml"), ([], []))

    def test_robots_and_title_from_url(self):
        self.assertEqual(article.sitemaps_from_robots("User-agent: *\nSitemap: https://a.ae/s.xml\n"),
                         ["https://a.ae/s.xml"])
        self.assertEqual(article.title_from_url("https://a.ae/news/difc-launches-ai-hub/"), "Difc launches ai hub")
        self.assertEqual(article.title_from_url("https://shams.ae/news/details?article=Shams%20AI%20Club&hsLang=en"),
                         "Shams AI Club")

    def test_url_normalisation(self):
        self.assertEqual(collect.normalize_url("https://WWW.Difc.com/news/a/?utm_source=x&id=2#top"),
                         "https://difc.com/news/a?id=2")


class BlockDetectionTest(unittest.TestCase):
    def test_challenge_pages(self):
        self.assertTrue(looks_blocked(403, "Forbidden"))
        self.assertTrue(looks_blocked(200, "<html><title>Just a moment...</title></html>"))
        self.assertFalse(looks_blocked(200, "<html>" + "real content " * 1000 + "akamai</html>"))


class OfficialSourceTest(unittest.TestCase):
    def pages(self, n=15, start=0):
        p = {"https://www.example.ae/news": listing(n, start)}
        for i in range(start, start + n):
            p[f"https://www.example.ae/news/story-number-{i}"] = article_page(
                f"Story {i} DIFC AI partnership", "2026-10-03T08:00:00Z" if i < 2 else "2025-01-01T08:00:00Z")
        return p

    def test_first_run_baselines_then_picks_up_only_new(self):
        state = {}
        f = FakeFetcher(self.pages())
        run = collect.Run(f, state, NOW, lookback_days=3)
        run.official(SRC)
        # 15 links exist, but only the 2 recent ones are emitted; the rest are remembered as seen.
        emitted = [i["url"] for i in run.items if i.get("origin") == "site:testzone"]
        self.assertEqual(emitted, ["https://www.example.ae/news/story-number-0",
                                   "https://www.example.ae/news/story-number-1"])
        self.assertEqual(len(state["seen"]["testzone"]), 15)
        self.assertTrue(run.health["testzone"]["listing:https://www.example.ae/news"]["ok"])

        pages = self.pages(16)
        pages["https://www.example.ae/news/story-number-15"] = article_page("Brand new AI deal", "2026-10-04T05:00:00Z")
        run2 = collect.Run(FakeFetcher(pages), state, NOW, lookback_days=3)
        run2.official(SRC)
        new = [i for i in run2.items if i.get("origin") == "site:testzone"]
        self.assertEqual([i["title"] for i in new], ["Brand new AI deal"])
        self.assertEqual(new[0]["zone_hint"], "difc")
        self.assertEqual(run2.new_links["testzone"], 1)

    def test_layout_change_is_flagged_not_silent(self):
        f = FakeFetcher({"https://www.example.ae/news": "<html><main><a href='/other/thing'>x</a></main></html>"})
        run = collect.Run(f, {}, NOW)
        run.official(SRC)
        result = run.health["testzone"]["listing:https://www.example.ae/news"]
        self.assertFalse(result["ok"])
        self.assertIn("no article links matched", result["error"])
        self.assertEqual(collect.summarize(run.health)["testzone"]["status"], "degraded")

    def test_failed_article_pages_retry_then_fall_back_to_slug_title(self):
        state = {"seen": {"testzone": {"https://example.ae/news/story-number-0": "x"}}}
        pages = {"https://www.example.ae/news": listing(2),
                 "https://www.example.ae/news/story-number-1": Response("u", 500, "", "u", error="HTTP 500")}
        for attempt in range(1, 3):
            run = collect.Run(FakeFetcher(pages), state, NOW)
            run.official(SRC)
            self.assertEqual([i for i in run.items if i.get("origin") == "site:testzone"], [])
            self.assertEqual(state["attempts"]["https://example.ae/news/story-number-1"], attempt)
        run = collect.Run(FakeFetcher(pages), state, NOW)
        run.official(SRC)
        items = [i for i in run.items if i.get("origin") == "site:testzone"]
        self.assertEqual(items[0]["title"], "Story number 1")
        self.assertNotIn("https://example.ae/news/story-number-1", state["attempts"])

    def test_sitemap_auto_discovery_covers_a_dead_listing(self):
        src = dict(SRC, sitemap="auto")
        pages = {
            "https://www.example.ae/robots.txt": "User-agent: *\nSitemap: https://www.example.ae/sitemap_index.xml",
            "https://www.example.ae/sitemap_index.xml":
                '<sitemapindex><sitemap><loc>https://www.example.ae/news-sitemap.xml</loc></sitemap></sitemapindex>',
            "https://www.example.ae/news-sitemap.xml":
                '<urlset><url><loc>https://www.example.ae/news/story-number-7</loc>'
                '<lastmod>2026-10-03</lastmod></url></urlset>',
            "https://www.example.ae/news/story-number-7": article_page("Seven AI", human_date="3 October 2026"),
        }
        run = collect.Run(FakeFetcher(pages), {}, NOW)
        run.official(src)
        self.assertEqual(collect.summarize(run.health)["testzone"]["status"], "ok")
        self.assertEqual([i["title"] for i in run.items if i.get("origin") == "site:testzone"], ["Seven AI"])

    def test_crashing_source_does_not_stop_run(self):
        class Boom(FakeFetcher):
            def get(self, url, allow_browser=True):
                raise RuntimeError("boom")
        run = collect.Run(Boom({}), {}, NOW)
        from tracker import sources
        saved = sources.OFFICIAL
        sources.OFFICIAL = [SRC]
        try:
            run.run_all(outlets=False, zone_search=False)
        finally:
            sources.OFFICIAL = saved
        self.assertEqual(collect.summarize(run.health)["testzone"]["status"], "down")


class HealthTest(unittest.TestCase):
    def test_alert_after_consecutive_failures_and_recovery(self):
        bad = {"testzone": {"listing:x": {"ok": False, "count": 0, "error": "HTTP 403", "via": "http", "url": "x"}}}
        good = {"testzone": {"listing:x": {"ok": True, "count": 9, "error": "", "via": "http", "url": "x"}}}
        hist = health.update({"sources": {}}, bad, {}, NOW)
        self.assertEqual(health.alerts(hist, NOW), [])           # one failure = blip
        hist = health.update(hist, bad, {}, NOW)
        alerts = health.alerts(hist, NOW)
        self.assertEqual(len(alerts), 1)
        self.assertIn("DOWN", alerts[0])
        hist = health.update(hist, good, {"testzone": 1}, NOW)
        self.assertEqual(health.alerts(hist, NOW), [])
        self.assertIn("testzone", health.render_markdown(hist, NOW))


if __name__ == "__main__":
    unittest.main()


class NoSitemapTest(unittest.TestCase):
    def test_source_without_sitemap_records_no_sitemap_failure(self):
        run = collect.Run(FakeFetcher(OfficialSourceTest().pages(2)), {}, NOW)
        run.official(SRC)
        self.assertFalse(any(k.startswith("sitemap") for k in run.health["testzone"]))
