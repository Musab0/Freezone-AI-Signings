"""Stdlib-only HTML/XML parsing: links, sitemaps, and article metadata (title, date, body)."""

import html as htmllib
import json
import re
import urllib.parse
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from html.parser import HTMLParser

SKIP_TAGS = {"script", "style", "noscript", "svg", "nav", "header", "footer", "form", "aside", "iframe", "template"}
VOID_TAGS = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "track", "wbr"}


class _Parser(HTMLParser):
    def __init__(self, base_url):
        super().__init__(convert_charrefs=True)
        self.base_url = base_url
        self.links = []
        self.meta = {}
        self.jsonld = []
        self.title = ""
        self.h1 = ""
        self.times = []
        self._stack = []          # open tags (non-void), for skip/scope tracking
        self._skip = 0
        self._in_title = self._in_h1 = self._in_jsonld = False
        self._buf = []
        self.main_text = []       # text inside <article>/<main>
        self.all_text = []
        self._scope = 0

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "a" and a.get("href"):
            href = a["href"].strip()
            if not href.startswith(("javascript:", "mailto:", "tel:", "#")):
                self.links.append(urllib.parse.urljoin(self.base_url, href).split("#")[0])
        elif tag == "meta":
            key = (a.get("property") or a.get("name") or a.get("itemprop") or "").lower()
            if key and a.get("content") and key not in self.meta:
                self.meta[key] = a["content"].strip()
        elif tag == "time" and a.get("datetime"):
            self.times.append(a["datetime"])
        elif tag == "base" and a.get("href"):
            self.base_url = urllib.parse.urljoin(self.base_url, a["href"])
        if tag in VOID_TAGS:
            return
        self._stack.append(tag)
        if tag in SKIP_TAGS and not (tag == "script" and "ld+json" in (a.get("type") or "")):
            self._skip += 1
        if tag == "script" and "ld+json" in (a.get("type") or ""):
            self._in_jsonld, self._buf = True, []
        if tag in ("article", "main") or a.get("role") == "main":
            self._scope += 1
        if tag == "title":
            self._in_title = True
        if tag == "h1" and not self.h1:
            self._in_h1, self._buf_h1 = True, []

    def handle_endtag(self, tag):
        if tag in VOID_TAGS or tag not in self._stack:
            return
        # Pop up to and including the matching tag (tolerates unclosed children).
        while self._stack:
            t = self._stack.pop()
            if t in SKIP_TAGS and not (t == "script" and self._in_jsonld):
                self._skip = max(0, self._skip - 1)
            if t in ("article", "main"):
                self._scope = max(0, self._scope - 1)
            if t == "script" and self._in_jsonld:
                self._in_jsonld = False
                self.jsonld.append("".join(self._buf))
            if t == "title":
                self._in_title = False
            if t == "h1" and self._in_h1:
                self._in_h1 = False
                self.h1 = clean(" ".join(self._buf_h1))
            if t == tag:
                break

    def handle_data(self, data):
        if self._in_jsonld:
            self._buf.append(data)
            return
        if self._in_title:
            self.title += data
        if self._in_h1:
            self._buf_h1.append(data)
        if self._skip:
            return
        if data.strip():
            self.all_text.append(data)
            if self._scope:
                self.main_text.append(data)


def clean(text):
    return re.sub(r"\s+", " ", htmllib.unescape(text or "")).strip()


def parse_html(text, base_url):
    p = _Parser(base_url)
    try:
        p.feed(text)
        p.close()
    except Exception:  # malformed markup: keep whatever was parsed
        pass
    return p


def extract_links(text, base_url):
    return list(dict.fromkeys(parse_html(text, base_url).links))


# ---------------------------------------------------------------- dates

MONTHS = {m: i for i, m in enumerate(
    ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"], 1)}
_MON = r"(jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)[a-z]*\.?"
DATE_PATTERNS = [
    re.compile(r"\b(\d{1,2})(?:st|nd|rd|th)?\s+" + _MON + r",?\s+(\d{4})\b", re.I),     # 28 Sept 2026
    re.compile(r"\b" + _MON + r"\s+(\d{1,2})(?:st|nd|rd|th)?,?\s+(\d{4})\b", re.I),      # July 2, 2026
    re.compile(r"\b(\d{4})-(\d{2})-(\d{2})\b"),                                         # 2026-07-02
    re.compile(r"\b(\d{1,2})/(\d{1,2})/(\d{4})\b"),                                      # 01/10/2026
]


def parse_date(value):
    """Parse ISO, RFC 822 or human dates. Returns aware UTC datetime or None."""
    if not value:
        return None
    value = str(value).strip()
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        try:
            dt = parsedate_to_datetime(value)
        except (TypeError, ValueError, IndexError):
            dt = find_date(value)
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    dt = dt.astimezone(timezone.utc)
    return None if dt > datetime.now(timezone.utc) + timedelta(days=1) else dt


def find_date(text, latest=None):
    """Earliest-positioned plausible date in free text (publish dates sit above the body;
    later dates are usually event dates). Dates after `latest` (default: tomorrow) are ignored."""
    latest = latest or datetime.now(timezone.utc) + timedelta(days=1)
    found = []
    for i, pat in enumerate(DATE_PATTERNS):
        for m in pat.finditer(text or ""):
            try:
                if i == 0:
                    day, mon, year = int(m.group(1)), MONTHS[m.group(2).lower()[:3]], int(m.group(3))
                elif i == 1:
                    mon, day, year = MONTHS[m.group(1).lower()[:3]], int(m.group(2)), int(m.group(3))
                elif i == 2:
                    year, mon, day = int(m.group(1)), int(m.group(2)), int(m.group(3))
                else:  # dd/mm/yyyy (UAE convention), mm/dd only when the first number can't be a month
                    a, b, year = int(m.group(1)), int(m.group(2)), int(m.group(3))
                    day, mon = (a, b) if b <= 12 else (b, a)
                dt = datetime(year, mon, day, tzinfo=timezone.utc)
            except (ValueError, KeyError):
                continue
            if 2000 <= year and dt <= latest:
                found.append((m.start(), dt))
    return min(found)[1] if found else None


# ---------------------------------------------------------------- articles

def _jsonld_objects(blobs):
    for blob in blobs:
        try:
            data = json.loads(blob.strip())
        except ValueError:
            continue
        stack = [data]
        while stack:
            obj = stack.pop()
            if isinstance(obj, list):
                stack.extend(obj)
            elif isinstance(obj, dict):
                yield obj
                if "@graph" in obj:
                    stack.append(obj["@graph"])


def parse_article(text, url):
    """Pull title / description / published date / body text out of an article page."""
    p = parse_html(text, url)
    title = description = published = None
    for obj in _jsonld_objects(p.jsonld):
        types = obj.get("@type")
        types = types if isinstance(types, list) else [types]
        if any(t in ("NewsArticle", "Article", "BlogPosting", "PressRelease", "Report", "WebPage") for t in types):
            title = title or obj.get("headline") or (obj.get("name") if "WebPage" not in types else None)
            description = description or obj.get("description")
            published = published or obj.get("datePublished") or obj.get("dateCreated")
    m = p.meta
    title = clean(title or m.get("og:title") or m.get("twitter:title") or p.h1 or p.title)
    description = clean(description or m.get("og:description") or m.get("description")
                        or m.get("twitter:description"))
    body = clean(" ".join(p.main_text) or " ".join(p.all_text))
    dt = None
    for candidate in (published, m.get("article:published_time"), m.get("datepublished"),
                      m.get("publishdate"), m.get("pubdate"), m.get("date"), m.get("dc.date"),
                      m.get("sailthru.date"), *(p.times[:3])):
        dt = parse_date(candidate)
        if dt:
            break
    if dt is None:
        # Fall back to the first human-readable date near the top of the article body.
        dt = find_date(body[:1500])
    return {"title": title, "description": description[:600], "published": dt.isoformat() if dt else None,
            "body": body[:8000]}


def title_from_url(url):
    slug = urllib.parse.unquote(urllib.parse.urlparse(url).path.rstrip("/").rsplit("/", 1)[-1])
    q = urllib.parse.parse_qs(urllib.parse.urlparse(url).query)
    if "article" in q:  # e.g. shams.ae/news/details?article=Title%20Here
        return q["article"][0].strip()
    slug = re.sub(r"\.(html?|aspx|php)$", "", slug)
    slug = re.sub(r"-[0-9a-f]{5}$", "", slug)
    return re.sub(r"[-_]+", " ", slug).strip().capitalize()


# ---------------------------------------------------------------- sitemaps & feeds

def _local(tag):
    return tag.rsplit("}", 1)[-1]


def parse_sitemap(text):
    """Return (page entries [(loc, lastmod)], child sitemap urls)."""
    try:
        root = ET.fromstring(text.lstrip("﻿").strip().encode("utf-8"))
    except ET.ParseError:
        return [], []
    pages, children = [], []
    kind = _local(root.tag)
    for node in root:
        if _local(node.tag) not in ("url", "sitemap"):
            continue
        loc = lastmod = None
        for child in node:
            name = _local(child.tag)
            if name == "loc" and child.text:
                loc = child.text.strip()
            elif name == "lastmod" and child.text:
                lastmod = child.text.strip()
        if not loc:
            continue
        (children if kind == "sitemapindex" else pages).append(loc if kind == "sitemapindex" else (loc, lastmod))
    return pages, children


def sitemaps_from_robots(text):
    return [line.split(":", 1)[1].strip() for line in (text or "").splitlines()
            if line.lower().startswith("sitemap:")]


def parse_news_sitemap(text):
    """Google News sitemap -> [(loc, publication_date, title)]. Plain urlsets work too (no title)."""
    try:
        root = ET.fromstring(text.lstrip("\ufeff").strip().encode("utf-8"))
    except ET.ParseError:
        return []
    out = []
    for node in root:
        if _local(node.tag) != "url":
            continue
        loc = date = title = None
        for child in node.iter():
            name = _local(child.tag)
            if name == "loc" and child.text and loc is None:
                loc = child.text.strip()
            elif name in ("publication_date", "lastmod") and child.text and not date:
                date = child.text.strip()
            elif name == "title" and child.text:
                title = clean(child.text)
        if loc:
            out.append((loc, date, title))
    return out
