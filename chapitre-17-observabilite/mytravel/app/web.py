"""The live web: search on trusted sites, then read the page.

A search engine returns titles and snippets. A snippet is not a
source: an agent reads the page before it cites it.
"""

import os
import time
from html.parser import HTMLParser
from urllib.parse import urlparse

import httpx
import truststore
from ddgs import DDGS
from ddgs.exceptions import DDGSException
from tavily import TavilyClient

from app.logs import log

# Use the certificates of the system, like a browser does: works
# behind the antivirus or proxy that inspects https at work.
truststore.inject_into_ssl()

MAX_CHARS = 8000  # one page, not a whole site
# Some sites refuse anything that does not look like a browser.
USER_AGENT = "Mozilla/5.0 (compatible; myTravel/1.0)"


def is_allowed(url, domains):
    """https, and the host is one of the domains or a subdomain."""
    try:
        parts = urlparse(url)
        host = parts.hostname or ""
    except ValueError:  # a broken URL is never trusted
        return False
    return parts.scheme == "https" and any(
        host == d or host.endswith("." + d) for d in domains)


def search_engine(query, domains):
    """Tavily if you have a key, DuckDuckGo (no key) otherwise."""
    key = os.environ.get("TAVILY_API_KEY")
    if key:
        found = TavilyClient(key).search(
            query, include_domains=domains, max_results=8)
        return [{"title": r["title"], "url": r["url"],
                 "snippet": r["content"]} for r in found["results"]]
    # First pointed at the first sites of the list, then free.
    sites = " OR ".join(f"site:{d}" for d in domains[:3])
    for attempt in (f"{query} {sites}", query):
        try:
            found = DDGS().text(attempt, max_results=10)
        except DDGSException:  # what ddgs raises for "no results"
            continue
        if any(is_allowed(r["href"], domains) for r in found):
            return [{"title": r["title"], "url": r["href"],
                     "snippet": r["body"]} for r in found]
    return []


def search_web(query, domains, max_results=5):
    """Results from the allowed sites only. Never raises."""
    started = time.perf_counter()
    try:
        found = search_engine(query, domains)
        # Ads and random blogs are filtered here, whatever engine.
        results = [r for r in found
                   if is_allowed(r["url"], domains)][:max_results]
    except Exception as error:  # engine down, quota, no network
        log("search_failed", query=query, error=str(error))
        return []
    log("search", query=query, results=len(results),
        seconds=round(time.perf_counter() - started, 2))
    return results


class PageText(HTMLParser):
    """The visible text of a page, menus and scripts left out."""
    SKIP = {"script", "style", "nav", "header", "footer", "form"}

    def __init__(self):
        super().__init__()
        self.parts, self.skipping = [], 0

    def handle_starttag(self, tag, attrs):
        self.skipping += tag in self.SKIP

    def handle_endtag(self, tag):
        if tag in self.SKIP and self.skipping:
            self.skipping -= 1

    def handle_data(self, data):
        if not self.skipping and data.strip():
            self.parts.append(data.strip())


def read_page(url, domains):
    """The text of an allowed page, redirects included."""
    def check(request):  # every hop, before it is sent
        if not is_allowed(str(request.url), domains):
            raise ValueError(f"not a trusted site: {request.url}")
    check(httpx.Request("GET", url))
    with httpx.Client(timeout=20, follow_redirects=True,
                      headers={"User-Agent": USER_AGENT},
                      event_hooks={"request": [check]}) as client:
        response = client.get(url)
        response.raise_for_status()
    parser = PageText()
    parser.feed(response.text)
    return " ".join(parser.parts)[:MAX_CHARS]
