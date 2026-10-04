"""Integrity checks for the data shown to leadership: the verified set, insights and coverage."""
import json
import os
import unittest
from datetime import datetime

from tracker import config, publish, seed, sources

ROOT = os.path.join(os.path.dirname(__file__), "..")
ZONE_IDS = {z["id"] for z in config.ZONES}
CATEGORIES = {name for name, _ in config.CATEGORIES} | {config.DEFAULT_CATEGORY}


class SeedTest(unittest.TestCase):
    def test_every_verified_item_is_complete_and_consistent(self):
        with open(seed.SEED_PATH, encoding="utf-8") as fh:
            raw = json.load(fh)
        verified_on = datetime.fromisoformat(raw["verified_on"] + "T23:59:59+00:00")
        titles = set()
        for s in raw["items"]:
            self.assertTrue(s["url"].startswith("https://"), s["title"])
            self.assertTrue(set(s["zones"]) <= ZONE_IDS, s["title"])
            self.assertIn(s["category"], CATEGORIES, s["title"])
            self.assertLessEqual(datetime.fromisoformat(s["published"]), verified_on, s["title"])
            self.assertTrue(1 <= s["importance"] <= 5)
            self.assertTrue(s["ai_summary"] and s["dmcc_angle"], s["title"])
            self.assertNotIn(s["title"], titles)
            titles.add(s["title"])
        items = seed.load_seed()
        self.assertEqual(len({i["id"] for i in items}), len(items))
        self.assertTrue(all(0 <= i["score"] <= 10 and i["verified"] for i in items))


class InsightsTest(unittest.TestCase):
    def test_insights_reference_real_zones(self):
        with open(os.path.join(ROOT, "data", "insights.json"), encoding="utf-8") as fh:
            ins = json.load(fh)
        self.assertTrue(ins["headline"])
        self.assertGreaterEqual(len(ins["findings"]), 3)
        self.assertGreaterEqual(len(ins["recommendations"]), 3)
        for f in ins["findings"]:
            self.assertTrue(set(f["zones"]) <= ZONE_IDS)


class CoverageTest(unittest.TestCase):
    def test_coverage_matrix_lists_every_registered_source(self):
        rows = publish.coverage()
        expected = len(sources.OFFICIAL) + len(sources.AGGREGATORS) + len(sources.OUTLET_FEEDS)
        self.assertEqual(len(rows), expected)
        for r in rows:
            if r["kind"] == "Official newsroom":
                self.assertTrue(r["search"])
                self.assertIn(r["zone"], ZONE_IDS)


if __name__ == "__main__":
    unittest.main()
