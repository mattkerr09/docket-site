#!/usr/bin/env python3
"""Offline free-tool title checks for both brands, built only in scratch."""
from __future__ import annotations

from collections import defaultdict
import html
from pathlib import Path
import re
import tempfile

from lint import MAX_TITLE
from test_launch_price_copy import scratch
from test_rename_brand import Page, build

# Search Console query_page, docketseo.app, 2026-10-10 through 2026-11-09.
# Use the relevant phrase without the historical year or search operators.
# The four paths without rows retain their titles, except title-ii-date, which
# needs its tool name first. Their phrases are inferences, not recorded queries.
PHRASES = {
    "/tools/ai-crawler-checker/": "AI crawler checker",
    "/tools/redirect-checker/": "Redirect checker",  # no data: inference
    "/tools/robots-txt-tester/": "Robots txt tester",
    "/tools/meta-tag-checker/": "Title tag length checker",
    "/tools/json-ld-checker/": "JSON-LD testing tool",  # 21 Nov upgrade: "json ld testing tool" 7 at 24.4
    "/tools/serp-preview/": "SERP preview tool",
    "/tools/http-header-checker/": "HTTP header checker",  # no data: inference
    "/tools/seo-checker/": "Free SEO checker",
    "/tools/website-checker/": "Free website checker",  # no data: inference
    "/tools/title-ii-date/": "Which ADA Title II date",  # no data: kept as it was
}


# Only the robots.txt tester's title changed, because only it has real query data (161, 128 and 117
# impressions). Its social titles follow the title; the other nine keep their h1 as the social title.
SOCIAL_FOLLOWS_TITLE = {"/tools/robots-txt-tester/"}


def check_site(site):
    titles = defaultdict(list)
    for path in site.rglob("*.html"):
        match = re.search(r"<title>(.*?)</title>", path.read_text(), re.S)
        if match:
            titles[html.unescape(match[1]).strip()].append(path.relative_to(site))
    for route, phrase in PHRASES.items():
        path = Path(route.strip("/")) / "index.html"
        raw = (site / path).read_text()
        title = html.unescape(re.search(r"<title>(.*?)</title>", raw, re.S)[1]).strip()
        assert title.startswith(phrase), (route, title, phrase)
        assert len(title) <= MAX_TITLE, (route, title, len(title))
        assert titles[title] == [path], (route, title, titles[title])
        tags = Page(raw).tags
        if route not in SOCIAL_FOLLOWS_TITLE:
            continue
        for attribute, name in (("property", "og:title"), ("name", "twitter:title")):
            values = [attrs.get("content") for tag, attrs in tags
                      if tag == "meta" and attrs.get(attribute) == name]
            assert values == [title], (route, name, values, title)


def main():
    with tempfile.TemporaryDirectory(prefix="test-free-tool-titles-") as temporary:
        destination = Path(temporary)
        scratch(destination)
        for name in ("docket", "checkengine"):
            build(destination, name)
            check_site(destination / "site")
            print(f"PASS {name}: 10 free-tool title phrases, length, sitewide uniqueness and social titles")


if __name__ == "__main__":
    main()
