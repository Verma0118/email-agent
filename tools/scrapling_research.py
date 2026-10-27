#!/usr/bin/env python3
"""
Scrapling research helper for the email-agent skill.

Fetches a public web page (company site, bio page, blog post, news article)
and prints clean, draft-ready intel: title, meta description, headings, key
links, and trimmed body text. Used in Step 2 Pass C (company intel) and for
scraping any citable public page found during research.

Does NOT scrape LinkedIn (login wall + ToS). Use the browser MCP for LinkedIn
and the exa MCP tools for people/company search. This is for public HTTP pages.

Usage:
    scrapling_research.py <url> [--full] [--links]
    scrapling_research.py https://acme.com/about
    scrapling_research.py https://acme.com --full --links

Flags:
    --full   print full page text (default: first ~1500 chars)
    --links  print interesting links (about/team/careers/news/blog/press)
"""
import sys
from urllib.parse import urljoin, urlparse

try:
    from scrapling.fetchers import Fetcher
except ImportError:
    sys.exit("scrapling not installed in this interpreter. "
             "Run with ~/.venvs/scrapling/bin/python")

LINK_KEYWORDS = ("about", "team", "career", "job", "news", "blog",
                 "press", "leadership", "founder", "story", "mission")


def clean(text: str) -> str:
    return " ".join(text.split())


def main() -> int:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    flags = {a for a in sys.argv[1:] if a.startswith("--")}
    if not args:
        print(__doc__)
        return 2
    url = args[0]
    if not urlparse(url).scheme:
        url = "https://" + url

    try:
        page = Fetcher.get(url, timeout=25)
    except Exception as e:  # network / fetch errors
        print(f"FETCH FAILED: {e}")
        return 1

    if page.status >= 400:
        print(f"HTTP {page.status} for {url}")
        return 1

    def first(sel):
        hits = page.css(sel)
        return clean(str(hits[0])) if hits else ""

    title = first("title::text")
    meta = ""
    for m in page.css("meta[name='description']") + page.css("meta[property='og:description']"):
        c = m.attrib.get("content", "") if hasattr(m, "attrib") else ""
        if c:
            meta = clean(c)
            break

    h1 = [clean(str(t)) for t in page.css("h1::text")][:3]
    h2 = [clean(str(t)) for t in page.css("h2::text")][:8]

    body = clean(page.get_all_text())
    limit = len(body) if "--full" in flags else 1500

    print(f"URL:    {url}")
    print(f"STATUS: {page.status}")
    print(f"TITLE:  {title}")
    if meta:
        print(f"META:   {meta}")
    if h1:
        print("H1:     " + " | ".join(h1))
    if h2:
        print("H2:     " + " | ".join(h2))
    print("\n--- BODY TEXT ---")
    print(body[:limit])
    if "--full" not in flags and len(body) > limit:
        print(f"\n[trimmed {len(body) - limit} chars — rerun with --full]")

    if "--links" in flags:
        seen, interesting = set(), []
        for a in page.css("a"):
            href = a.attrib.get("href", "") if hasattr(a, "attrib") else ""
            if not href or href.startswith(("#", "mailto:", "tel:", "javascript:")):
                continue
            full = urljoin(url, href)
            low = full.lower()
            if any(k in low for k in LINK_KEYWORDS) and full not in seen:
                seen.add(full)
                interesting.append(full)
        if interesting:
            print("\n--- KEY LINKS ---")
            for link in interesting[:15]:
                print(link)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
