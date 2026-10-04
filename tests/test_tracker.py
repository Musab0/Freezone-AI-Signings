import os
import unittest
from datetime import datetime, timezone

from tracker import classify, fetch, publish, store

FIXTURE = os.path.join(os.path.dirname(__file__), "fixture.xml")


def tagged():
    with open(FIXTURE, "rb") as fh:
        raw = fetch.parse_feed(fh.read(), "fixture")
    return raw, [t for t in (classify.tag(r) for r in raw) if t]


class ParseTest(unittest.TestCase):
    def test_parses_all_items_with_dates_and_sources(self):
        raw, _ = tagged()
        self.assertEqual(len(raw), 8)
        self.assertEqual(raw[0]["source"], "Example Wire")
        self.assertTrue(raw[0]["published"].startswith("2026-10-02T08:00"))
        self.assertNotIn("<a", raw[0]["summary"])


class ClassifyTest(unittest.TestCase):
    def setUp(self):
        self.raw, self.items = tagged()
        self.by_url = {i["url"]: i for i in self.items}

    def test_drops_non_ai_and_ambiguous_acronyms(self):
        self.assertNotIn("https://example.com/d", self.by_url)   # DIFC but not AI
        self.assertNotIn("https://example.com/f", self.by_url)   # "DSO" with no UAE context

    def test_mou_is_partnership_with_players(self):
        a = self.by_url["https://example.com/a"]
        self.assertEqual(a["zones"], ["difc"])
        self.assertEqual(a["category"], "Partnership / MoU")
        self.assertIn("Microsoft", a["players"])
        self.assertEqual(a["title"], "DIFC signs MoU with ExampleCloud to build generative AI sandbox for fintechs")

    def test_categories_and_parent_rollup(self):
        self.assertEqual(self.by_url["https://example.com/b"]["category"], "Regulation & Policy")
        c = self.by_url["https://example.com/c"]
        self.assertEqual(c["category"], "Investment & Funding")
        self.assertEqual(c["zones"], ["hub71", "adgm"])
        g = self.by_url["https://example.com/g"]
        self.assertEqual(g["zones"], ["diez"])
        self.assertEqual(g["category"], "Adoption & Deployment")

    def test_leader_deal_outscores_own_zone_item(self):
        self.assertGreater(self.by_url["https://example.com/a"]["score"], self.by_url["https://example.com/e"]["score"])


class StoreTest(unittest.TestCase):
    def test_merge_dedupes_and_records_extra_sources(self):
        _, items = tagged()
        now = datetime(2026, 10, 4, tzinfo=timezone.utc)
        data = {"items": [], "rejected": [], "runs": []}
        new = store.merge(data, items, now)
        self.assertEqual(len(new), 5)
        dup = next(i for i in data["items"] if i["url"] == "https://example.com/a")
        self.assertEqual(dup["also_in"], ["Other Paper"])
        self.assertEqual(store.merge(data, items, now), [])

    def test_digest_separates_own_news(self):
        _, items = tagged()
        now = datetime(2026, 10, 4, tzinfo=timezone.utc)
        data = {"items": [], "rejected": [], "runs": []}
        text = publish.render_digest(store.merge(data, items, now), now)
        self.assertIn("4 new competitor items", text)
        self.assertIn("DMCC's own coverage", text)


if __name__ == "__main__":
    unittest.main()
