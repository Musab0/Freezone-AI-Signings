"""Regression tests built from the live sites (captured Oct 2026).

Each source's pattern must accept real article URLs and reject the newsroom's own navigation /
pagination / category URLs. If a site changes its URL scheme, update the sample here together
with the pattern in tracker/sources.py.
"""
import re
import unittest

from tracker import article, sources

SAMPLES = {
    "difc": (["https://www.difc.com/whats-on/news/flow-expands-into-uae",
              "https://www.difc.com/whats-on/news/difc-regulations-strengthen-spv-structuring-advantage"],
             ["https://www.difc.com/whats-on/news?page=2", "https://www.difc.com/whats-on/news",
              "https://www.difc.com/whats-on/insights/jones-the-grocer-express"]),
    "dfsa": (["https://www.dfsa.ae/news/dfsa-awarded-legal-costs-al-ramz-tribunal-proceedings"],
             ["https://www.dfsa.ae/news", "https://www.dfsa.ae/media-releases"]),
    "adgm": (["https://www.adgm.com/media/announcements/eurazeo-opens-an-office-in-abu-dhabi-reinforcing-its-commitment-to-the-middle-east"],
             ["https://www.adgm.com/media/announcements", "https://www.adgm.com/media"]),
    "hub71": (["https://www.hub71.com/latest-news/press-release/abu-dhabi-enters-worlds-top-50-emerging-ecosystems",
               "https://www.hub71.com/latest-news/blog/building-to-stay-how-hub71-roots-high-growth-companies-in-abu-dhabis-economy"],
              ["https://www.hub71.com/latest-news", "https://www.hub71.com/ar/latest-news/press-release/x"]),
    "dmcc": (["https://dmcc.ae/latest-news/first-tokenised-commodity-asset-launched-under-dmcc-vara-framework-with-world-record-silver-bar"],
             ["https://dmcc.ae/latest-news", "https://twitter.com/intent/tweet?url=https://dmcc.ae/latest-news"]),
    "dic": (["https://www.dic.ae/media/press-release/forcepoint-expands-middle-east-presence-in-dubai-internet-city-to-advance-ai-native-data-security"],
            ["https://www.dic.ae/media/press-releases", "https://www.dic.ae/media/gallery"]),
    "dsp": (["https://dsp.ae/media/press-release/robertet-middle-east-africa-inaugurates-its-regional-headquarters-at-dubai-science-park"],
            ["https://dsp.ae/media/press-releases"]),
    "dmc": (["https://www.dmc.ae/media/press-releases/dubai-media-city-marks-25-years-of-pioneering-innovation-in-the-middle-easts-media-and-content-creation-sector"],
            ["https://www.dmc.ae/media/press-releases"]),
    "jafza": (["https://www.jafza.ae/resource-centre/media/news/jafza-achieves-operational-net-zero-across-its-own-facilities/"],
              ["https://www.jafza.ae/resource-centre/media/news/", "https://www.jafza.ae/resource-centre/media/news/page/2/"]),
    "dubaisouth": (["https://www.dubaisouth.ae/en/newsroom/dubai-south-welcomes-dior-regional-distribution-centre"],
                   ["https://www.dubaisouth.ae/en/newsroom", "https://www.dubaisouth.ae/en/newsroom?page=2"]),
    "meydan": (["https://www.meydanfz.ae/news/meydan-free-zone-odoo-erp-partnership-appsgate"],
               ["https://www.meydanfz.ae/news"]),
    "masdar": (["https://masdar.ae/en/news/newsroom/baltic-eagle-harnesses-the-wind-to-power-progress"],
               ["https://masdar.ae/en/news/newsroom", "https://masdar.ae/ar/news/newsroom", "https://masdar.ae/en/news"]),
    "twofour54": (["https://www.twofour54.com/en/news-and-updates/press-releases/twofour54-unveils-three-fully-purposed-services-to-strengthen-abu-dhabi-media-ecosystem/"],
                  ["https://www.twofour54.com/ar/news-and-updates/press-releases/x/", "https://www.twofour54.com/en/news-and-updates"]),
    "rakez": (["https://rakez.com/en/media-centre/news-detail/articleid/1736/rakez-and-rakbank-launch-uae-first-sixty-minute-business-account-opening"],
              ["https://rakez.com/en/media-centre/news-and-events/news", "https://rakez.com/ar/media-centre/news-and-events/news"]),
    "srtip": (["https://srtip.ae/launch-ai-company-uae/",
               "https://srtip.ae/srti-park-highlights-trends-in-ai-innovation-and-smart-technology-at-workshop/"],
              ["https://srtip.ae/news/", "https://srtip.ae/freezone-business-setup/", "https://srtip.ae/events/"]),
    "shams": (["https://www.shams.ae/news/details?article=Shams%20and%20Wio%20Bank%20Join%20Forces&hsLang=en"],
              ["https://www.shams.ae/news?hsLang=en", "https://www.shams.ae/news"]),
    "masdarcity": (["https://masdarcityfreezone.com/resources/blog/why-masdar-city-free-zone-is-ideal-for-ai-companies"],
                   ["https://masdarcityfreezone.com/resources/business-activities"]),
    "afz": (["https://afz.gov.ae/en/resources/blogs/2024/one-click-business-license-in-uae.html"],
            ["https://afz.gov.ae/en/resources/blogs.html", "https://afz.gov.ae/en/resources/press-kit.html"]),
    "kezad": (["https://www.kezadgroup.com/news-and-media/2026/05/07/rox-to-establish-one-of-the-middle-easts-first-advanced-ai-manufacturing-centres-in-kezads-klp-1-musaffah/"],
              ["https://www.kezadgroup.com/news-and-media/", "https://www.kezadgroup.com/news-and-media/page/2/",
               "https://www.kezadgroup.com/ar/news-and-media/?noredirect=ar-AE"]),
    "rakinc": (["https://innovationcity.com/news/innovation-city-and-iopn-launch-the-middle-east-s-first-sovereign-ai-data-center"],
               ["https://innovationcity.com/news"]),
    "dwtc": (["https://www.dwtc.com/en/press/dwtc-expands-smart-event-infrastructure/"],
             ["https://www.dwtc.com/en/press/", "https://www.dwtc.com/ar/press/"]),
    "dso": (["https://www.dso.ae/w/dubai-integrated-economic-zones-release-esg-report",
             "https://mediaoffice.ae/en/news/2026/jun/25-06/ahmed-bin-saeed-witnesses-opening-of-new-manufacturing-unit-at-dubai-silicon-oasis",
             "https://www.wam.ae/en/article/c0scyr7-dubai-silicon-oasis-noon-minutes-form-strategic"],
            ["https://www.dso.ae/newsroom", "https://www.dso.ae/press", "https://www.dso.ae/events"]),
    "dhcc": (["https://www.dhcc.ae/media/news/one-in-three-business-partners-expand-operations-as-dubai-healthcare-city-records-another-year-of-strong-growth",
              "https://www.dhcc.ae/en/media/news/dubai-healthcare-city-authority-unveils-aed13-billion-development-plan"],
             ["https://www.dhcc.ae/media/news", "https://www.dhcc.ae/media/newsletter"]),
}


class PatternTest(unittest.TestCase):
    def test_every_sampled_source_matches_articles_and_rejects_navigation(self):
        by_id = {s["id"]: s for s in sources.OFFICIAL}
        for source_id, (good, bad) in SAMPLES.items():
            pat = re.compile(by_id[source_id].get("pattern") or sources.GENERIC_NEWS_PATTERN, re.I)
            for url in good:
                self.assertTrue(pat.search(url), f"{source_id} should match {url}")
            for url in bad:
                self.assertFalse(pat.search(url), f"{source_id} should NOT match {url}")

    def test_every_official_source_has_a_way_in(self):
        for s in sources.OFFICIAL:
            self.assertTrue(s.get("domain"), s["id"])  # domain search always runs
            if s.get("listing") or s.get("sitemap"):
                re.compile(s.get("pattern") or sources.GENERIC_NEWS_PATTERN)


class RealDateFormatsTest(unittest.TestCase):
    def test_adgm_meta_format(self):
        self.assertEqual(article.parse_date("01/10/2026 11:00:00 AM").date().isoformat(), "2026-10-01")

    def test_dmcc_prefers_publish_date_over_event_date(self):
        text = ("DMCC to Host Second Edition of Dubai Diamond Week This October July 29, 2026 Share this article "
                "Dubai Diamond Week will take place on 29 October 2026")
        self.assertEqual(article.find_date(text).date().isoformat(), "2026-07-29")

    def test_dfsa_and_hub71_inline_dates(self):
        self.assertEqual(article.find_date("###### 15 Jul 2026, 10:00 am # DFSA").date().isoformat(), "2026-07-15")
        self.assertEqual(article.find_date("ALL NEWS # Abu Dhabi Enters 17 Jun, 2026 SHARE").date().isoformat(),
                         "2026-06-17")

    def test_future_dates_are_not_publish_dates(self):
        self.assertIsNone(article.find_date("applications close 31 October 2099"))


if __name__ == "__main__":
    unittest.main()
