"""HTTP fetching with retries, bot-wall detection and an optional real-browser fallback.

Every network call in the tracker goes through Fetcher.get so behaviour (timeouts, retries,
politeness, fallbacks) is uniform and tests can swap in a fake.
"""

import gzip
import logging
import os
import random
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import urllib.robotparser
import zlib
from dataclasses import dataclass

log = logging.getLogger(__name__)

BROWSER_UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
              "Chrome/128.0.0.0 Safari/537.36")
HEADERS = {
    "User-Agent": BROWSER_UA,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,application/rss+xml,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate",
    "Cache-Control": "no-cache",
}
RETRY_STATUS = {408, 425, 429, 500, 502, 503, 504, 520, 521, 522, 523, 524}
BLOCK_STATUS = {401, 403, 406, 429, 503}
CHALLENGE_MARKERS = (
    "just a moment...", "cf-browser-verification", "challenge-platform", "attention required! | cloudflare",
    "access denied", "request unsuccessful. incapsula", "_incapsula_resource", "pardon our interruption",
    "please enable javascript and cookies", "ddos protection by", "are you a robot", "bot verification",
    "<title>403 forbidden</title>", "akamai", "errors.edgesuite.net",
)


@dataclass
class Response:
    url: str
    status: int
    text: str
    final_url: str
    via: str = "http"          # "http" or "browser"
    error: str = ""

    @property
    def ok(self):
        return 200 <= self.status < 300 and bool(self.text) and not self.error


def looks_blocked(status, text):
    if status in BLOCK_STATUS:
        return True
    head = (text or "")[:6000].lower()
    # Real pages can mention "akamai" (CDN asset URLs), so only trust markers on short pages.
    return len(head) < 6000 and any(m in head for m in CHALLENGE_MARKERS)


def _decode(raw, headers):
    enc = (headers.get("Content-Encoding") or "").lower()
    if enc == "gzip" or raw[:2] == b"\x1f\x8b":
        raw = gzip.decompress(raw)
    elif enc == "deflate":
        try:
            raw = zlib.decompress(raw)
        except zlib.error:
            raw = zlib.decompress(raw, -zlib.MAX_WBITS)
    charset = "utf-8"
    ctype = headers.get("Content-Type") or ""
    if "charset=" in ctype:
        charset = ctype.split("charset=")[-1].split(";")[0].strip().strip('"') or "utf-8"
    try:
        return raw.decode(charset, errors="replace")
    except LookupError:
        return raw.decode("utf-8", errors="replace")


class Fetcher:
    """Thread-safe for plain HTTP. Browser fallback is serialised behind a lock."""

    def __init__(self, timeout=30, retries=3, use_browser=True, min_host_interval=1.0, reader_proxy=None):
        self.timeout = timeout
        self.check_robots = os.environ.get("RESPECT_ROBOTS", "1") != "0"
        self._robots = {}
        self.reader_proxy = os.environ.get("READER_PROXY", "https://r.jina.ai/") if reader_proxy is None else reader_proxy
        self.retries = retries
        self.use_browser = use_browser
        self.min_host_interval = min_host_interval
        self._host_last = {}
        self._host_lock = threading.Lock()
        self._browser_lock = threading.Lock()
        self._pw = self._browser = None
        self._browser_thread = None
        self._browser_failed = False

    # -- politeness: never hit the same host more than once per min_host_interval
    def _wait_for_host(self, url):
        host = urllib.parse.urlparse(url).netloc
        with self._host_lock:
            now = time.monotonic()
            wait = self._host_last.get(host, 0) + self.min_host_interval - now
            self._host_last[host] = max(now, self._host_last.get(host, 0) + self.min_host_interval)
        if wait > 0:
            time.sleep(wait)

    def _http(self, url):
        last = Response(url, 0, "", url, error="not attempted")
        for attempt in range(self.retries):
            self._wait_for_host(url)
            req = urllib.request.Request(url, headers=HEADERS)
            try:
                with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                    text = _decode(resp.read(), resp.headers)
                    return Response(url, resp.status, text, resp.geturl())
            except urllib.error.HTTPError as exc:
                try:
                    body = _decode(exc.read(), exc.headers)
                except Exception:
                    body = ""
                last = Response(url, exc.code, body, url, error=f"HTTP {exc.code}")
                if exc.code not in RETRY_STATUS:
                    return last
                retry_after = exc.headers.get("Retry-After", "")
                delay = int(retry_after) if retry_after.isdigit() else 2 ** attempt * 2
            except Exception as exc:  # DNS, TLS, timeouts, resets
                last = Response(url, 0, "", url, error=f"{type(exc).__name__}: {exc}")
                delay = 2 ** attempt * 2
            if attempt < self.retries - 1:
                time.sleep(min(delay, 30) + random.random())
        return last

    def _browser_get(self, url):
        with self._browser_lock:
            if self._browser_failed:
                return None
            # Playwright's sync API is bound to the thread that started it.
            if self._browser is not None and self._browser_thread != threading.get_ident():
                return None
            try:
                if self._browser is None:
                    from playwright.sync_api import sync_playwright
                    self._pw = sync_playwright().start()
                    self._browser = self._pw.chromium.launch(args=["--disable-blink-features=AutomationControlled"])
                    self._browser_thread = threading.get_ident()
                ctx = self._browser.new_context(user_agent=BROWSER_UA, locale="en-US")
                page = ctx.new_page()
                try:
                    resp = page.goto(url, wait_until="domcontentloaded", timeout=self.timeout * 1000)
                    # Give client-side rendering and JS challenges a moment to settle.
                    try:
                        page.wait_for_load_state("networkidle", timeout=15000)
                    except Exception:
                        pass
                    text = page.content()
                    status = resp.status if resp else 0
                    if looks_blocked(status, text):
                        page.wait_for_timeout(6000)
                        text = page.content()
                    return Response(url, status or 200, text, page.url, via="browser")
                finally:
                    ctx.close()
            except ImportError:
                log.info("playwright not installed - browser fallback disabled")
                self._browser_failed = True
            except Exception as exc:
                log.warning("browser fetch failed %s: %s", url, exc)
                return Response(url, 0, "", url, via="browser", error=f"browser: {exc}")
        return None

    def _reader_get(self, url):
        """Last resort: a public rendering proxy (default Jina Reader) that returns the page's HTML.
        Disable with READER_PROXY="" or point it at your own instance."""
        if not self.reader_proxy:
            return None
        req = urllib.request.Request(self.reader_proxy + url, headers={
            "User-Agent": BROWSER_UA, "X-Return-Format": "html", "Accept": "text/html"})
        try:
            self._wait_for_host(self.reader_proxy)
            with urllib.request.urlopen(req, timeout=max(self.timeout, 60)) as resp:
                return Response(url, resp.status, _decode(resp.read(), resp.headers), url, via="reader")
        except Exception as exc:
            return Response(url, 0, "", url, via="reader", error=f"reader: {exc}")

    # Search engines' RSS endpoints are designed for feed readers; robots.txt is checked for every site we crawl.
    ROBOTS_EXEMPT = ("news.google.com", "www.bing.com", "r.jina.ai")

    def allowed(self, url):
        """robots.txt check (cached per host). Unreachable or missing robots.txt means allowed."""
        parts = urllib.parse.urlsplit(url)
        if parts.netloc in self.ROBOTS_EXEMPT or parts.path.endswith("robots.txt"):
            return True
        with self._host_lock:
            rp = self._robots.get(parts.netloc)
        if rp is None:
            rp = urllib.robotparser.RobotFileParser()
            resp = self._http(f"{parts.scheme}://{parts.netloc}/robots.txt") if self.check_robots else None
            if resp is not None and resp.ok:
                rp.parse(resp.text.splitlines())
            else:
                rp.allow_all = True
            with self._host_lock:
                self._robots[parts.netloc] = rp
        return rp.can_fetch(BROWSER_UA, url)

    def get(self, url, allow_browser=True):
        if self.check_robots and not self.allowed(url):
            return Response(url, 0, "", url, error="disallowed by robots.txt")
        resp = self._http(url)
        blocked = looks_blocked(resp.status, resp.text)
        if resp.ok and not blocked:
            return resp
        retryable = blocked or resp.status == 0 or (resp.status < 400 and not resp.text)
        if self.use_browser and allow_browser and retryable:
            b = self._browser_get(url)
            if b and b.ok and not looks_blocked(b.status, b.text):
                return b
        if retryable:  # the reader proxy is plain HTTP, so it is safe from any thread
            r = self._reader_get(url)
            if r and r.ok and not looks_blocked(r.status, r.text):
                return r
        if blocked and not resp.error:
            resp.error = "blocked by bot protection"
        return resp

    def render(self, url):
        """Fetch a page that needs JavaScript: headless browser first, then the reader proxy."""
        if self.use_browser:
            b = self._browser_get(url)
            if b and b.ok and not looks_blocked(b.status, b.text):
                return b
        r = self._reader_get(url)
        if r and r.ok and not looks_blocked(r.status, r.text):
            return r
        return None

    def close(self):
        with self._browser_lock:
            try:
                if self._browser:
                    self._browser.close()
                if self._pw:
                    self._pw.stop()
            except Exception:
                pass
            self._browser = self._pw = None
