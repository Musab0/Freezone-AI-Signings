"""Bake the rendered pages into static HTML, so the briefing reads correctly without JavaScript
(link previews, strict proxies, some mail clients, search). The scripts still re-render on load.

    python -m tracker.prerender
"""

import logging
import os
import pathlib

from . import publish

PAGES = ["index.html", "explore.html", "how-it-works.html"]
log = logging.getLogger(__name__)


def prerender(site_dir=None):
    site_dir = site_dir or publish.SITE_DIR
    names = [n for n in PAGES if os.path.exists(os.path.join(site_dir, n))]
    if not names:
        return False
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        log.info("playwright not installed - skipping prerender")
        return False
    exe = os.environ.get("CHROMIUM_PATH") or None
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=exe)
        try:
            for name in names:
                path = pathlib.Path(site_dir, name).resolve()
                page = browser.new_page()
                page.goto(path.as_uri())
                page.wait_for_function("() => !document.querySelector('h1') || !/Loading/.test(document.querySelector('h1').textContent)",
                                       timeout=15000)
                html = page.evaluate("() => '<!doctype html>\\n' + document.documentElement.outerHTML")
                page.close()
                path.write_text(html, encoding="utf-8")
        finally:
            browser.close()
    log.info("prerendered %d pages", len(names))
    return True


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    prerender()
