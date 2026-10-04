"""What we watch: UAE free zones, AI vocabulary, deal categories and news sources.

Edit this file to add a zone, an alias, or a keyword. Everything else picks it up.
"""

# tier: "leader" zones get extra, deal-specific queries and a higher signal weight.
# self: DMCC itself - tracked as a benchmark, hidden by default on the dashboard.
# parent: the zone an ecosystem/brand belongs to (e.g. Hub71 sits in ADGM).
ZONES = [
    {"id": "difc", "name": "DIFC", "emirate": "Dubai", "tier": "leader",
     "aliases": ["DIFC", "Dubai International Financial Centre", "Dubai International Financial Center",
                 "DFSA", "Dubai AI Campus", "DIFC Innovation Hub"]},
    {"id": "adgm", "name": "ADGM", "emirate": "Abu Dhabi", "tier": "leader",
     "aliases": ["ADGM", "Abu Dhabi Global Market", "FSRA", "ADGM Academy"]},
    {"id": "hub71", "name": "Hub71", "emirate": "Abu Dhabi", "tier": "major", "parent": "adgm",
     "aliases": ["Hub71"]},
    {"id": "dmcc", "name": "DMCC", "emirate": "Dubai", "tier": "major", "self": True,
     "aliases": ["DMCC", "Dubai Multi Commodities Centre", "DMCC Crypto Centre", "DMCC AI Centre",
                 "Uptown Dubai"]},
    {"id": "tecom", "name": "TECOM (DIC / DMC / DSP / d3 / DKP)", "emirate": "Dubai", "tier": "major",
     "aliases": ["Dubai Internet City", "Dubai Media City", "Dubai Science Park", "Dubai Design District",
                 "Dubai Knowledge Park", "Dubai Studio City", "Dubai Production City", "Dubai Outsource City",
                 "Dubai Industrial City", "TECOM Group", "in5"]},
    {"id": "diez", "name": "DIEZ (DSO / DAFZ / Dubai CommerCity)", "emirate": "Dubai", "tier": "major",
     "aliases": ["Dubai Silicon Oasis", "DSO", "Dubai Airport Freezone", "Dubai Airport Free Zone", "DAFZ",
                 "Dubai CommerCity", "Dubai Integrated Economic Zones", "DIEZ", "Dtec", "District IO"]},
    {"id": "dpworld", "name": "JAFZA / Dubai South", "emirate": "Dubai", "tier": "major",
     "aliases": ["JAFZA", "Jebel Ali Free Zone", "Dubai South", "Dubai Logistics District"]},
    {"id": "dwtc", "name": "DWTC Free Zone", "emirate": "Dubai", "tier": "other",
     "aliases": ["DWTC Free Zone", "Dubai World Trade Centre Free Zone", "Dubai World Trade Centre Authority"]},
    {"id": "dhcc", "name": "Dubai Healthcare City", "emirate": "Dubai", "tier": "other",
     "aliases": ["Dubai Healthcare City", "DHCC", "DHCR"]},
    {"id": "meydan", "name": "Meydan Free Zone", "emirate": "Dubai", "tier": "other",
     "aliases": ["Meydan Free Zone"]},
    {"id": "ifza", "name": "IFZA", "emirate": "Dubai", "tier": "other",
     "aliases": ["IFZA", "International Free Zone Authority"]},
    {"id": "kezad", "name": "KEZAD / AD Ports", "emirate": "Abu Dhabi", "tier": "major",
     "aliases": ["KEZAD", "Khalifa Economic Zones", "Abu Dhabi Airport Free Zone", "ADAFZ"]},
    {"id": "masdar", "name": "Masdar City Free Zone", "emirate": "Abu Dhabi", "tier": "major",
     "aliases": ["Masdar City Free Zone", "Masdar City"]},
    {"id": "twofour54", "name": "twofour54", "emirate": "Abu Dhabi", "tier": "other",
     "aliases": ["twofour54", "Yas Creative Hub"]},
    {"id": "rakez", "name": "RAKEZ", "emirate": "Ras Al Khaimah", "tier": "major",
     "aliases": ["RAKEZ", "Ras Al Khaimah Economic Zone"]},
    {"id": "rakinc", "name": "RAK Innovation City (ex-RAK DAO)", "emirate": "Ras Al Khaimah", "tier": "major",
     "aliases": ["RAK Innovation City", "RAK INC", "RAK DAO", "RAK Digital Assets Oasis"]},
    {"id": "sharjah", "name": "Sharjah zones (SRTIP / SPC / SAIF / Shams)", "emirate": "Sharjah", "tier": "other",
     "aliases": ["SRTIP", "Sharjah Research, Technology and Innovation Park",
                 "Sharjah Research Technology and Innovation Park", "Sharjah Publishing City", "SPC Free Zone",
                 "SAIF Zone", "Sharjah Airport International Free Zone", "Shams Free Zone",
                 "Sharjah Media City", "Hamriyah Free Zone"]},
    {"id": "ajman", "name": "Ajman Free Zone", "emirate": "Ajman", "tier": "other",
     "aliases": ["Ajman Free Zone", "AFZ Ajman"]},
    {"id": "fujairah", "name": "Fujairah zones", "emirate": "Fujairah", "tier": "other",
     "aliases": ["Fujairah Creative City", "Fujairah Free Zone"]},
    {"id": "uaq", "name": "UAQ Free Trade Zone", "emirate": "Umm Al Quwain", "tier": "other",
     "aliases": ["Umm Al Quwain Free Trade Zone", "UAQ FTZ", "UAQ Free Trade Zone"]},
]

# Short aliases that are also ordinary words or ambiguous acronyms need word boundaries
# and are only trusted when the article also mentions the UAE.
AMBIGUOUS_ALIASES = {"DSO", "DAFZ", "SPC Free Zone", "FSRA", "DFSA", "in5", "DIEZ", "Dtec", "RAK INC",
                     "Masdar City", "DHCR", "AFZ Ajman"}
UAE_CONTEXT = r"\b(UAE|Dubai|Abu Dhabi|Sharjah|Ras Al Khaimah|Ajman|Fujairah|Emirat\w*)\b"

AI_TERMS = [
    r"\bAI\b", r"artificial intelligence", r"gen(?:erative)?[ -]?AI", r"\bGenAI\b", r"machine learning",
    r"\bLLMs?\b", r"large language model", r"agentic", r"\bAI agents?\b", r"chatbot", r"\bGPT\b",
    r"computer vision", r"deep learning", r"neural", r"data cent(?:er|re)s?", r"\bGPUs?\b",
    r"\bOpenAI\b", r"\bAnthropic\b", r"\bNvidia\b", r"\bG42\b", r"\bMBZUAI\b", r"\bCore42\b", r"\bInception\b",
    r"\bFalcon\b", r"\bJais\b", r"\bMGX\b", r"\bMistral\b", r"\bCopilot\b", r"\bGemini\b", r"\bClaude\b",
    r"automation", r"robotic", r"\bAI[- ]powered\b", r"\bAI[- ]driven\b", r"\bAI[- ]native\b",
]

# Ordered: the first category whose pattern matches becomes the primary category.
CATEGORIES = [
    ("Partnership / MoU", r"\b(MoU|memorandum|partner\w*|agreement|signs?|signed|signing|collaborat\w*|"
                          r"alliance|joint venture|teams? up|join forces|strategic tie[- ]?up|cooperation)\b"),
    ("Investment & Funding", r"\b(invest\w*|fund\w*|raises?|raised|capital|venture|\$\s?\d|USD\s?\d|AED\s?\d|"
                             r"\d+\s?(?:million|billion|bn|mn)|acqui\w+|stake)\b"),
    ("Regulation & Policy", r"\b(regulat\w*|framework|guidance|guideline\w*|law|legislat\w*|sandbox|"
                            r"governance|consultation paper|rulebook|licen[cs]e regime|AI licen[cs]e|code of conduct)\b"),
    ("Adoption & Deployment", r"\b(deploy\w*|adopt\w*|implement\w*|roll(?:s|ed)? out|integrat\w*|digiti[sz]\w*|"
                              r"automat\w*|uses? AI|using AI|AI[- ]enabled|transform\w*)\b"),
    ("Product & Launch", r"\b(launch\w*|unveil\w*|introduc\w*|debut\w*|releases?|released|new (?:platform|tool|"
                         r"service|product|app)|platform|assistant|agent)\b"),
    ("Programmes & Ecosystem", r"\b(accelerator|incubat\w*|programme|program|cohort|campus|hub|centre of excellence|"
                               r"center of excellence|academy|training|upskill\w*|talent|hackathon|challenge|"
                               r"summit|conference|week|forum|festival|licen[cs]e)\b"),
]
DEFAULT_CATEGORY = "News & Commentary"

# Counterparties that make an announcement more strategically significant.
MAJOR_PLAYERS = [
    "Microsoft", "Google", "Alphabet", "Amazon", "AWS", "Oracle", "IBM", "Meta", "Nvidia", "OpenAI", "Anthropic",
    "G42", "Core42", "MGX", "Mubadala", "ADIA", "ADQ", "Presight", "e&", "du", "Khazna", "Cisco", "Salesforce",
    "SAP", "Huawei", "Alibaba", "Tencent", "Mistral", "Cohere", "xAI", "Qualcomm", "Intel", "AMD", "Dell", "HPE",
    "Accenture", "PwC", "Deloitte", "KPMG", "EY", "McKinsey", "BCG", "Mastercard", "Visa", "HSBC", "Standard Chartered",
    "JPMorgan", "Goldman Sachs", "BlackRock", "MBZUAI", "Emirates NBD", "FAB", "ADNOC", "Binance",
]

# Free (no key) news search feeds. {q} is URL-encoded query text.
SEARCH_FEEDS = {
    "google_news": "https://news.google.com/rss/search?q={q}&hl=en-AE&gl=AE&ceid=AE:en",
    "bing_news": "https://www.bing.com/news/search?q={q}&format=rss&setlang=en-US&cc=AE",
}

# Extra RSS/Atom feeds polled directly (official newsrooms, trade press). Items still
# have to mention a tracked zone and an AI term to be kept.
DIRECT_FEEDS = [
    "https://www.zawya.com/en/rss/business",
    "https://gulfbusiness.com/feed/",
    "https://www.arabianbusiness.com/feed",
    "https://www.thenationalnews.com/arc/outboundfeeds/rss/category/business/?outputType=xml",
    "https://wam.ae/en/rss/feed/economy",
    "https://www.tahawultech.com/feed/",
    "https://www.intelligentcio.com/me/feed/",
    "https://www.khaleejtimes.com/stories.rss",
]

AI_QUERY = '(AI OR "artificial intelligence" OR GenAI OR "generative AI" OR "machine learning" OR agentic)'
DEAL_QUERY = '(MoU OR partnership OR agreement OR signs OR launches OR deploys OR adopts OR investment)'

# How far back each daily run looks; overlap with the previous day is deduplicated.
LOOKBACK_DAYS = 3
# Items older than this are dropped from the store.
RETENTION_DAYS = 730
