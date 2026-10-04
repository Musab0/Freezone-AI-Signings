"""What we watch: UAE free zones, AI vocabulary, deal categories and news sources.

Edit this file to add a zone, an alias, or a keyword. Everything else picks it up.
"""

# Every UAE free zone (56, plus the Hub71 ecosystem), by emirate. Sources: UAE Federal Tax Authority designated-zone list,
# Wikipedia "List of free-trade zones in the UAE" (Aug 2026 revision) and the zones' own sites.
# tier: "leader" zones get extra, deal-specific news queries. self: DMCC itself.
# parent: the zone an ecosystem brand belongs to (Hub71 -> ADGM). group: operating authority.
def _z(id, name, emirate, aliases, tier="other", group=None, **extra):
    return {"id": id, "name": name, "emirate": emirate, "aliases": aliases, "tier": tier, "group": group or name, **extra}


ZONES = [
    # ---------------- Dubai
    _z("difc", "DIFC", "Dubai", ["DIFC", "Dubai International Financial Centre", "Dubai International Financial Center",
                                 "DFSA", "Dubai AI Campus", "DIFC Innovation Hub", "DIFC AI Campus"], "leader"),
    _z("dmcc", "DMCC", "Dubai", ["DMCC", "Dubai Multi Commodities Centre", "DMCC AI Centre", "DMCC Crypto Centre",
                                 "Jumeirah Lakes Towers Free Zone", "Uptown Dubai"], "major", self=True),
    _z("dic", "Dubai Internet City", "Dubai", ["Dubai Internet City"], "major", "TECOM Group"),
    _z("dmc", "Dubai Media City", "Dubai", ["Dubai Media City"], "major", "TECOM Group"),
    _z("dsp", "Dubai Science Park", "Dubai", ["Dubai Science Park", "DuBiotech", "Dubai Biotechnology and Research Park"], "major", "TECOM Group"),
    _z("d3", "Dubai Design District", "Dubai", ["Dubai Design District"], "other", "TECOM Group"),
    _z("dkp", "Dubai Knowledge Park", "Dubai", ["Dubai Knowledge Park", "Dubai Knowledge Village", "in5"], "other", "TECOM Group"),
    _z("diac", "Dubai International Academic City", "Dubai", ["Dubai International Academic City"], "other", "TECOM Group"),
    _z("dstudio", "Dubai Studio City", "Dubai", ["Dubai Studio City"], "other", "TECOM Group"),
    _z("dprod", "Dubai Production City", "Dubai", ["Dubai Production City", "International Media Production Zone"], "other", "TECOM Group"),
    _z("dout", "Dubai Outsource City", "Dubai", ["Dubai Outsource City", "Dubai Outsource Zone"], "other", "TECOM Group"),
    _z("dind", "Dubai Industrial City", "Dubai", ["Dubai Industrial City"], "other", "TECOM Group"),
    _z("dafz", "Dubai Airport Freezone", "Dubai", ["Dubai Airport Freezone", "Dubai Airport Free Zone", "DAFZ", "DAFZA",
                                                    "Dubai Flower Centre"], "major", "DIEZ"),
    _z("dso", "Dubai Silicon Oasis", "Dubai", ["Dubai Silicon Oasis", "DSO", "District IO", "Dubai Digital Park", "Dtec"], "major", "DIEZ"),
    _z("dcc", "Dubai CommerCity", "Dubai", ["Dubai CommerCity", "Dubai Integrated Economic Zones", "DIEZ"], "major", "DIEZ"),
    _z("jafza", "Jebel Ali Free Zone (JAFZA)", "Dubai", ["JAFZA", "Jafza", "Jebel Ali Free Zone"], "major", "DP World"),
    _z("dubaisouth", "Dubai South", "Dubai", ["Dubai South", "Dubai World Central", "Dubai Logistics District",
                                               "Dubai Logistics City", "Dubai Aviation City"], "major", "Dubai Aviation City Corporation"),
    _z("dwtc", "DWTC Free Zone", "Dubai", ["DWTC Free Zone", "Dubai World Trade Centre Free Zone",
                                            "Dubai World Trade Centre Authority", "Dubai World Trade Centre"], "other"),
    _z("dhcc", "Dubai Healthcare City", "Dubai", ["Dubai Healthcare City", "DHCC", "Dubai Healthcare City Authority"], "other"),
    _z("meydan", "Meydan Free Zone", "Dubai", ["Meydan Free Zone"], "other"),
    _z("ifza", "IFZA", "Dubai", ["IFZA", "International Free Zone Authority"], "other"),
    _z("expo", "Expo City Dubai", "Dubai", ["Expo City Dubai", "Expo City Dubai Authority"], "other"),
    _z("dmaritime", "Dubai Maritime City", "Dubai", ["Dubai Maritime City"], "other"),
    _z("ihc", "International Humanitarian City", "Dubai", ["International Humanitarian City"], "other"),
    _z("dgdp", "Dubai Gold & Diamond Park", "Dubai", ["Dubai Gold and Diamond Park", "Gold & Diamond Park"], "other"),
    _z("ducamz", "Dubai Cars & Automotive Zone", "Dubai", ["DUCAMZ", "Dubai Car and Automotive City", "Dubai Auto Zone"], "other"),
    _z("dtechno", "Dubai Techno Park", "Dubai", ["Dubai Techno Park", "Technopark Dubai"], "other"),
    _z("dtextile", "Dubai Textile Village", "Dubai", ["Dubai Textile Village"], "other"),
    _z("duqe", "DUQE Free Zone", "Dubai", ["DUQE Free Zone", "DUQE"], "other"),
    # ---------------- Abu Dhabi
    _z("adgm", "ADGM", "Abu Dhabi", ["ADGM", "Abu Dhabi Global Market", "FSRA", "ADGM Academy"], "leader"),
    _z("hub71", "Hub71", "Abu Dhabi", ["Hub71"], "major", "ADGM", parent="adgm"),
    _z("kezad", "KEZAD", "Abu Dhabi", ["KEZAD", "Khalifa Economic Zones", "KIZAD", "Khalifa Industrial Zone"], "major", "AD Ports Group"),
    _z("kpftz", "Khalifa Port Free Trade Zone", "Abu Dhabi", ["Khalifa Port Free Trade Zone", "Free Trade Zone of Khalifa Port"], "other", "AD Ports Group"),
    _z("masdar", "Masdar City Free Zone", "Abu Dhabi", ["Masdar City Free Zone", "Masdar City", "MCFZ"], "major"),
    _z("twofour54", "twofour54", "Abu Dhabi", ["twofour54", "Yas Creative Hub", "Abu Dhabi Media Zone"], "other"),
    _z("adafz", "Abu Dhabi Airports Free Zone", "Abu Dhabi", ["Abu Dhabi Airport Free Zone", "Abu Dhabi Airports Free Zone",
                                                               "ADAFZ", "Zayed International Airport Free Zone"], "other"),
    _z("alain", "Al Ain International Airport Free Zone", "Abu Dhabi", ["Al Ain International Airport Free Zone"], "other"),
    _z("icad", "Industrial City of Abu Dhabi", "Abu Dhabi", ["Industrial City of Abu Dhabi", "ICAD"], "other"),
    _z("zonescorp", "ZonesCorp", "Abu Dhabi", ["ZonesCorp", "Higher Corporation for Specialized Economic Zones"], "other"),
    # ---------------- Sharjah
    _z("saif", "SAIF Zone", "Sharjah", ["SAIF Zone", "Sharjah Airport International Free Zone"], "major"),
    _z("hfz", "Hamriyah Free Zone", "Sharjah", ["Hamriyah Free Zone", "HFZA"], "other"),
    _z("spc", "Sharjah Publishing City Free Zone", "Sharjah", ["Sharjah Publishing City", "SPC Free Zone"], "major"),
    _z("shams", "Sharjah Media City (Shams)", "Sharjah", ["Sharjah Media City", "Shams Free Zone", "Shams AI Club"], "other"),
    _z("srtip", "Sharjah Research, Technology and Innovation Park", "Sharjah",
       ["SRTIP", "SRTI Park", "Sharjah Research, Technology and Innovation Park",
        "Sharjah Research Technology and Innovation Park", "Sharjah Innovation Park"], "other"),
    _z("shcc", "Sharjah Healthcare City", "Sharjah", ["Sharjah Healthcare City"], "other"),
    _z("comtech", "Sharjah Communication Technologies Free Zone", "Sharjah",
       ["Sharjah Communication Technologies Free Zone", "COMTECH Free Zone"], "other"),
    _z("usartc", "U.S.A. Regional Trade Center Free Zone", "Sharjah", ["USARTC", "U.S.A. Regional Trade Center"], "other"),
    # ---------------- Ajman
    _z("afz", "Ajman Free Zone", "Ajman", ["Ajman Free Zone", "AFZA"], "other"),
    _z("amc", "Ajman Media City Free Zone", "Ajman", ["Ajman Media City"], "other"),
    _z("ancfz", "Ajman NuVentures Centre Free Zone", "Ajman", ["Ajman NuVentures", "ANCFZ"], "other"),
    # ---------------- Ras Al Khaimah
    _z("rakez", "RAKEZ", "Ras Al Khaimah", ["RAKEZ", "Ras Al Khaimah Economic Zone", "RAK Free Trade Zone"], "major"),
    _z("rakinc", "Innovation City (RAK)", "Ras Al Khaimah", ["Innovation City Ras Al Khaimah", "RAK Innovation City",
                                                             "RAK DAO", "RAK Digital Assets Oasis", "Innovation City"], "major"),
    _z("rakmc", "RAK Maritime City Free Zone", "Ras Al Khaimah", ["RAK Maritime City"], "other"),
    # ---------------- Fujairah
    _z("ffz", "Fujairah Free Zone", "Fujairah", ["Fujairah Free Zone"], "other"),
    _z("fcc", "Fujairah Creative City", "Fujairah", ["Fujairah Creative City", "Creative City Fujairah"], "other"),
    _z("foiz", "Fujairah Oil Industry Zone", "Fujairah", ["Fujairah Oil Industry Zone", "FOIZ"], "other"),
    # ---------------- Umm Al Quwain
    _z("uaqftz", "UAQ Free Trade Zone", "Umm Al Quwain", ["UAQ Free Trade Zone", "Umm Al Quwain Free Trade Zone", "UAQ FTZ"], "other"),
]

# Short aliases that are also ordinary words or ambiguous acronyms need word boundaries
# and are only trusted when the article also mentions the UAE.
AMBIGUOUS_ALIASES = {"DSO", "DAFZ", "FSRA", "DFSA", "in5", "DIEZ", "Dtec", "Masdar City", "Innovation City", "ICAD",
                     "DUQE", "FOIZ", "AFZA", "MCFZ", "Dubai World Trade Centre"}
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
    ("Company Attraction", r"\b(opens? (?:an? )?(?:new )?(?:office|base|headquarters|hq)|regional (?:headquarters|base|hub)|"
                           r"expands? (?:its )?(?:presence|footprint)|sets? up (?:in|its)|relocat\w*|moves? (?:its )?(?:hq|headquarters))\b"),
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

AI_QUERY = '(AI OR "artificial intelligence" OR GenAI OR "generative AI" OR "machine learning" OR agentic)'
DEAL_QUERY = '(MoU OR partnership OR agreement OR signs OR launches OR deploys OR adopts OR investment)'

# How far back each daily run looks; overlap with the previous day is deduplicated.
LOOKBACK_DAYS = 3
# Items older than this are dropped from the store.
RETENTION_DAYS = 730
