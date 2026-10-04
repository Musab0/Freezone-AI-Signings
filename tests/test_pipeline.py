"""End-to-end: run the real daily pipeline against a fake internet and check every output."""
import json
import os
import shutil
import tempfile
import unittest
from unittest import mock

from tracker import collect, health, publish, run, sources, store
from tests.test_collect import EMPTY_FEED, article_page
from tracker.http import Response

DIFC = {"id": "difc", "zone": "difc", "name": "DIFC Newsroom", "domain": "difc.com",
        "listing": ["https://www.difc.com/whats-on/news"], "pattern": r"difc\.com/whats-on/news/[^/?#]+$"}
BROKEN = {"id": "adgm", "zone": "adgm", "name": "ADGM Announcements", "domain": "adgm.com",
          "listing": ["https://www.adgm.com/media/announcements"], "pattern": r"adgm\.com/media/announcements/.+"}

OUTLET_RSS = """<?xml version="1.0"?><rss version="2.0"><channel><title>AB</title>
<item><title>ADGM and G42 sign agreement to deploy agentic AI across regulator</title>
<link>https://www.arabianbusiness.com/x</link><pubDate>Sat, 03 Oct 2026 08:00:00 GMT</pubDate>
<description>Abu Dhabi Global Market partnership</description></item>
<item><title>Gold prices rise</title><link>https://www.arabianbusiness.com/y</link>
<pubDate>Sat, 03 Oct 2026 08:00:00 GMT</pubDate></item></channel></rss>"""


class FakeNet:
    def __init__(self, use_browser=True, **kw):
        self.pages = {
            "https://www.difc.com/whats-on/news": "<main>" + "".join(
                f'<a href="/whats-on/news/item-{i}">x</a>' for i in range(3)) + "</main>",
            "https://www.difc.com/whats-on/news/item-0": article_page(
                "DIFC launches AI licence fast-track with Microsoft", "2026-10-03T06:00:00Z"),
            "https://www.difc.com/whats-on/news/item-1": article_page("DIFC art week returns", "2026-10-02T06:00:00Z"),
            "https://www.difc.com/whats-on/news/item-2": article_page("Old AI story", "2025-01-01T06:00:00Z"),
            "https://www.adgm.com/media/announcements": Response("u", 403, "Forbidden", "u", error="HTTP 403"),
            "https://www.arabianbusiness.com/feed": OUTLET_RSS,
        }

    def get(self, url, allow_browser=True):
        if "news.google.com" in url or "bing.com" in url:
            return Response(url, 200, EMPTY_FEED, url)
        page = self.pages.get(url)
        if isinstance(page, Response):
            return page
        if page is None:
            return Response(url, 404, "", url, error="HTTP 404")
        return Response(url, 200, page, url)

    def close(self):
        pass


def read(path, as_json=True):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh) if as_json else fh.read()


class PipelineTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        for d in ("data", "digests", "site"):
            os.makedirs(os.path.join(self.tmp, d))
        p = lambda *a: os.path.join(self.tmp, *a)
        self.patches = [
            mock.patch.object(store, "DATA_PATH", p("data", "items.json")),
            mock.patch.object(health, "HEALTH_PATH", p("data", "health.json")),
            mock.patch.object(run, "STATE_PATH", p("data", "state.json")),
            mock.patch.object(publish, "ROOT", self.tmp),
            mock.patch.object(publish, "SITE_DIR", p("site")),
            mock.patch.object(publish, "DIGEST_DIR", p("digests")),
            mock.patch.object(run, "Fetcher", FakeNet),
            mock.patch.object(sources, "OFFICIAL", [DIFC, BROKEN]),
            mock.patch.object(sources, "OUTLET_FEEDS", [{"id": "ab", "name": "Arabian Business",
                                                         "url": "https://www.arabianbusiness.com/feed"}]),
            mock.patch.object(sources, "OUTLET_SEARCH_DOMAINS", []),
            mock.patch.dict(os.environ, {"ANTHROPIC_API_KEY": "", "SMTP_HOST": ""}),
        ]
        for patch in self.patches:
            patch.start()

    def tearDown(self):
        for patch in self.patches:
            patch.stop()
        shutil.rmtree(self.tmp)

    def test_daily_run_end_to_end(self):
        run.main(["--no-email"])
        items = read(os.path.join(self.tmp, "data", "items.json"))["items"]
        titles = sorted(i["title"] for i in items)
        self.assertEqual(titles, ["ADGM and G42 sign agreement to deploy agentic AI across regulator",
                                  "DIFC launches AI licence fast-track with Microsoft"])
        difc = next(i for i in items if i["zones"][0] == "difc")
        self.assertTrue(difc["official"])
        self.assertNotIn("body", difc)
        site = read(os.path.join(self.tmp, "site", "data", "items.json"))
        status = {s["id"]: s["status"] for s in site["health"]["sources"]}
        self.assertEqual(status["difc"], "ok")
        self.assertEqual(status["adgm"], "degraded")       # listing blocked, search still answered
        self.assertEqual(site["health"]["alerts"], [])     # first failure is not an alert yet

        # Second run: ADGM still broken -> alert; nothing re-added.
        run.main(["--no-email"])
        site = read(os.path.join(self.tmp, "site", "data", "items.json"))
        self.assertEqual(len(site["items"]), 2)
        self.assertTrue(any("ADGM" in a for a in site["health"]["alerts"]))
        digest = read(os.path.join(self.tmp, "digests", os.listdir(os.path.join(self.tmp, "digests"))[0]), False)
        self.assertIn("Source health alerts", digest)
        self.assertTrue(os.path.exists(os.path.join(self.tmp, "data", "HEALTH.md")))
        self.assertTrue(os.path.exists(os.path.join(self.tmp, "site", "feed.xml")))

    def test_catch_up_widens_lookback_after_missed_runs(self):
        from datetime import timedelta
        now = collect.utcnow()
        self.assertEqual(run.catch_up_days({"runs": []}, now), 3)
        self.assertEqual(run.catch_up_days({"runs": [{"at": (now - timedelta(days=6)).isoformat()}]}, now), 8)
        self.assertEqual(run.catch_up_days({"runs": [{"at": (now - timedelta(days=90)).isoformat()}]}, now), 30)


if __name__ == "__main__":
    unittest.main()
