"""Every place we collect from, and how.

Official free-zone newsrooms are scraped with up to four independent strategies whose results
are merged, so one broken strategy (a redesign, a bot wall, a dead feed) never silently drops a
source:

  rss      - the site's own RSS/Atom feed
  listing  - the newsroom page; links matching `pattern` are articles
  sitemap  - sitemap.xml (or "auto": discovered from robots.txt); URLs matching `pattern`
  search   - Google News + Bing News restricted to the site's domain (added automatically)

Listing/sitemap patterns were verified against the live sites in Oct 2026. `python -m tracker.check`
re-verifies every strategy; CI runs it on every push and weekly.
"""

GENERIC_NEWS_PATTERN = (r"/(?:[a-z]{2}/)?(?:news|newsroom|latest-news|press-releases?|press|media-cent(?:re|er)"
                        r"|media/press-releases?|announcements?|media/news|news-and-events)(?:/[^?#]*)?"
                        r"/[a-z0-9%][^/?#]{14,}/?$")

OFFICIAL = [
    # ---- Leaders
    {"id": "difc", "zone": "difc", "name": "DIFC Newsroom", "domain": "difc.com",
     "listing": ["https://www.difc.com/whats-on/news"],
     "pattern": r"difc\.com/whats-on/news/[^/?#]+$",
     "sitemap": "https://www.difc.com/sitemap.xml", "max_silence_days": 21},
    {"id": "dfsa", "zone": "difc", "name": "DFSA (DIFC regulator)", "domain": "dfsa.ae",
     "listing": ["https://www.dfsa.ae/news"],
     "pattern": r"dfsa\.ae/news/[^/?#]+$",
     "sitemap": "auto", "max_silence_days": 30},
    {"id": "adgm", "zone": "adgm", "name": "ADGM Announcements", "domain": "adgm.com",
     "listing": ["https://www.adgm.com/media/announcements"],
     "pattern": r"adgm\.com/media/announcements/[^/?#]+$",
     "sitemap": "https://www.adgm.com/sitemap.xml", "max_silence_days": 21},
    {"id": "hub71", "zone": "hub71", "name": "Hub71", "domain": "hub71.com",
     "listing": ["https://www.hub71.com/news"],
     "pattern": r"hub71\.(?:com|ae)/(?:news|media|press|blog)[^?#]*/[^/?#]{12,}/?$",
     "sitemap": "auto", "max_silence_days": 45},
    # ---- DMCC (own benchmark)
    {"id": "dmcc", "zone": "dmcc", "name": "DMCC News", "domain": "dmcc.ae",
     "listing": ["https://dmcc.ae/latest-news"],
     "pattern": r"dmcc\.ae/latest-news/[^/?#]+$",
     "sitemap": "auto", "max_silence_days": 30},
    # ---- Dubai
    {"id": "dic", "zone": "tecom", "name": "Dubai Internet City", "domain": "dic.ae",
     "listing": ["https://www.dic.ae/media/press-releases"],
     "pattern": r"dic\.ae/media/press-release/[^/?#]+$",
     "sitemap": "auto", "max_silence_days": 45},
    {"id": "dsp", "zone": "tecom", "name": "Dubai Science Park", "domain": "dsp.ae",
     "listing": ["https://dsp.ae/media/press-releases"],
     "pattern": r"dsp\.ae/media/press-release/[^/?#]+$",
     "sitemap": "auto", "max_silence_days": 60},
    {"id": "dmc", "zone": "tecom", "name": "Dubai Media City", "domain": "dmc.ae",
     "listing": ["https://www.dmc.ae/media/press-releases"],
     "pattern": r"dmc\.ae/media/press-release/[^/?#]+$",
     "sitemap": "auto", "max_silence_days": 60},
    {"id": "jafza", "zone": "dpworld", "name": "JAFZA News", "domain": "jafza.ae",
     "listing": ["https://www.jafza.ae/resource-centre/media/news/"],
     "pattern": r"jafza\.ae/resource-centre/media/news/(?!page/)[^/?#]+/?$",
     "sitemap": "https://www.jafza.ae/sitemap_index.xml", "max_silence_days": 45},
    {"id": "dubaisouth", "zone": "dpworld", "name": "Dubai South Newsroom", "domain": "dubaisouth.ae",
     "listing": ["https://www.dubaisouth.ae/en/newsroom"],
     "pattern": r"dubaisouth\.ae/en/newsroom/[^/?#]+$",
     "sitemap": "https://www.dubaisouth.ae/sitemap.xml", "max_silence_days": 45},
    {"id": "diez", "zone": "diez", "name": "DIEZ / DSO / DAFZ", "domain": "diez.ae",
     "listing": ["https://www.diez.ae/media-centre", "https://www.dso.ae/en/media-centre/news",
                 "https://www.dafz.ae/en/media-centre/news"],
     "pattern": r"(?:diez|dso|dafz)\.ae/[^?#]*(?:news|media|press)[^?#]*/[^/?#]{14,}/?$",
     "sitemap": "auto", "extra_domains": ["dso.ae", "dafz.ae"], "max_silence_days": 45},
    {"id": "meydan", "zone": "meydan", "name": "Meydan Free Zone", "domain": "meydanfz.ae",
     "listing": ["https://www.meydanfz.ae/news"],
     "pattern": r"meydanfz\.ae/news/[^/?#]+$",
     "sitemap": "auto", "max_silence_days": 90},
    {"id": "ifza", "zone": "ifza", "name": "IFZA", "domain": "ifza.com",
     "rss": ["https://ifza.com/en/feed/"], "listing": ["https://ifza.com/en/"],
     "pattern": r"ifza\.com/en/(?!category|tag|page|business-setup|about)[a-z0-9-]{20,}/?$",
     "sitemap": "auto", "max_silence_days": 90},
    {"id": "dwtc", "zone": "dwtc", "name": "DWTC", "domain": "dwtc.com",
     "sitemap": "auto", "pattern": GENERIC_NEWS_PATTERN, "max_silence_days": 120},
    {"id": "dhcc", "zone": "dhcc", "name": "Dubai Healthcare City", "domain": "dhcc.ae",
     "sitemap": "auto", "pattern": GENERIC_NEWS_PATTERN, "max_silence_days": 120},
    # ---- Abu Dhabi
    {"id": "kezad", "zone": "kezad", "name": "KEZAD", "domain": "kezad.ae",
     "sitemap": "auto", "pattern": GENERIC_NEWS_PATTERN, "max_silence_days": 120},
    {"id": "masdar", "zone": "masdar", "name": "Masdar Newsroom", "domain": "masdar.ae",
     "listing": ["https://masdar.ae/en/news/newsroom"],
     "pattern": r"masdar\.ae/en/news/newsroom/[^/?#]+$",
     "sitemap": "https://masdar.ae/sitemap.xml", "max_silence_days": 60},
    {"id": "masdarcity", "zone": "masdar", "name": "Masdar City", "domain": "masdarcity.ae",
     "sitemap": "auto", "pattern": GENERIC_NEWS_PATTERN, "max_silence_days": 120},
    {"id": "twofour54", "zone": "twofour54", "name": "twofour54", "domain": "twofour54.com",
     "sitemap": "auto", "pattern": GENERIC_NEWS_PATTERN, "max_silence_days": 120},
    # ---- Northern Emirates
    {"id": "rakez", "zone": "rakez", "name": "RAKEZ News", "domain": "rakez.com",
     "listing": ["https://rakez.com/en/media-centre/news-and-events/news"],
     "pattern": r"rakez\.com/en/media-centre/news-detail/articleid/\d+/[^/?#]+$",
     "sitemap": "https://rakez.com/sitemap.xml", "max_silence_days": 45},
    {"id": "rakinc", "zone": "rakinc", "name": "RAK Innovation City", "domain": "rakinc.ae",
     "sitemap": "auto", "pattern": GENERIC_NEWS_PATTERN, "max_silence_days": 120},
    {"id": "srtip", "zone": "sharjah", "name": "SRTI Park", "domain": "srtip.ae",
     "rss": ["https://srtip.ae/feed/"], "listing": ["https://srtip.ae/news/"],
     "pattern": r"srtip\.ae/(?!news/|events|contact|careers|leadership|rules|freezone|why-|about|saia|soilab|"
                r"sharjah-business-angels|innovation-ecosystem)[a-z0-9-]{20,}/?$",
     "sitemap": "auto", "max_silence_days": 120},
    {"id": "shams", "zone": "sharjah", "name": "Shams (Sharjah Media City)", "domain": "shams.ae",
     "listing": ["https://www.shams.ae/news"],
     "pattern": r"shams\.ae/news/details\?article=",
     "max_silence_days": 45},
    {"id": "afz", "zone": "ajman", "name": "Ajman Free Zone", "domain": "afz.ae",
     "sitemap": "auto", "pattern": GENERIC_NEWS_PATTERN, "max_silence_days": 180},
]

# News outlets. Feeds marked verified returned valid RSS in Oct 2026; the rest are reached
# through domain-restricted news search because their feeds are broken or bot-protected.
OUTLET_FEEDS = [
    {"id": "arabianbusiness", "name": "Arabian Business", "url": "https://www.arabianbusiness.com/feed"},
    {"id": "thenational-biz", "name": "The National",
     "url": "https://www.thenationalnews.com/arc/outboundfeeds/rss/category/business/?outputType=xml"},
    {"id": "thenational-tech", "name": "The National",
     "url": "https://www.thenationalnews.com/arc/outboundfeeds/rss/category/future/technology/?outputType=xml"},
    {"id": "tahawultech", "name": "TahawulTech", "url": "https://www.tahawultech.com/feed/"},
    {"id": "intelligentcio", "name": "Intelligent CIO ME", "url": "https://www.intelligentcio.com/me/feed/"},
    {"id": "khaleejtimes", "name": "Khaleej Times", "url": "https://www.khaleejtimes.com/stories.rss"},
    {"id": "agbi", "name": "AGBI", "url": "https://www.agbi.com/feed/"},
    {"id": "itp", "name": "ITP.net", "url": "https://www.itp.net/feed"},
    {"id": "fintechnews", "name": "Fintech News ME", "url": "https://fintechnews.ae/feed/"},
    {"id": "wamda", "name": "Wamda", "url": "https://www.wamda.com/feed"},
    {"id": "gulfbusiness", "name": "Gulf Business", "url": "https://gulfbusiness.com/feed/"},
]
OUTLET_SEARCH_DOMAINS = ["zawya.com", "wam.ae", "gulfnews.com", "gulfbusiness.com", "khaleejtimes.com",
                         "thenationalnews.com", "arabianbusiness.com", "agbi.com", "emirates247.com",
                         "mediaoffice.ae", "mediaoffice.abudhabi"]
