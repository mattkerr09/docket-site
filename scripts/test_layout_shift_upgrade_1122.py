#!/usr/bin/env python3
"""Offline checks for the 22 November layout shift upgrade.

Reads the built page, so run it after scripts/build.py (the gate does). Literal
lists only: no git calls, no commit hashes, download links checked by prefix.
"""
from __future__ import annotations

import html
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PAGE = ROOT / "site" / "how-to" / "fix-layout-shift" / "index.html"

KEPT_H2 = [
    "The cause is almost always one thing",
    "When you cannot know the dimensions",
    "The other four causes, in the order they bite",
    "Where to look first",
    "What Check Engine can and cannot tell you",
]
NEW_H2 = "What a real crawl caught"
KEPT_HREFS = {
    "/",
    "/assets/docket-sample-report.pdf",
    "/how-to/",
    "/how-to/fix-render-blocking-resources/",
    "/how-to/serve-images-in-modern-formats/",
    "https://kerr-affiliate-hub.kerrco.workers.dev/buy/docket?src=how-to-fix-layout-shift",
}
KEPT_FAQ = [
    "What causes layout shift?",
    "Do width and height attributes override my CSS?",
    "What if I don't know the image dimensions?",
    "Does an accordion opening count as layout shift?",
    "Can a crawler measure CLS?",
]
NEW_FAQ = "Why didn't the audit flag my one unsized image?"
MODIFIED = "2026-11-22"


def text(fragment: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", fragment))).strip()


def check(raw: str) -> None:
    title = text(re.search(r"<title>(.*?)</title>", raw, re.S).group(1))
    assert len(title) <= 60, f"title too long: {len(title)}"
    assert "CLS" in title and "layout shift" in title.lower(), "title lost its terms"
    assert not re.search("[–—]", raw), "en or em dash in page"

    article = raw.split("<article", 1)[1].split("</article>", 1)[0]
    h2s = [text(h) for h in re.findall(r"<h2[^>]*>(.*?)</h2>", article, re.S)]
    missing = [h for h in KEPT_H2 + [NEW_H2] if h not in h2s]
    assert not missing, f"heading removed: {missing}"
    assert h2s.index(NEW_H2) + 1 == h2s.index("What Check Engine can and cannot tell you"), "new section placement"

    first = article.split("</h1>", 1)[1].split("<h2", 1)[0]
    short = re.search(r"<strong>The short answer:</strong>(.*?)</p>", first, re.S)
    assert short, "short answer missing"
    assert len(text(short.group(1)).split()) <= 60, "short answer too long"

    hrefs = set(re.findall(r'href="([^"]+)"', article))
    assert not KEPT_HREFS - hrefs, f"href removed: {sorted(KEPT_HREFS - hrefs)}"

    section = article.split(f">{NEW_H2}</h2>", 1)[1].split("<h2", 1)[0]
    assert '<div class="wrap-tbl">' in section, "table wrapper missing"
    rows = re.findall(r"<tbody>(.*?)</tbody>", section, re.S)[0].count("<tr>")
    assert rows == 7, f"crawl table rows: {rows}"
    assert not re.search(r"\d", text(section)), "digit in the crawl section"

    blocks = [json.loads(b) for b in re.findall(r'<script type="application/ld\+json">(.*?)</script>', raw, re.S)]
    faq = next(b for b in blocks if b.get("@type") == "FAQPage")
    names = [q["name"] for q in faq["mainEntity"]]
    assert names[0] == NEW_FAQ, "new FAQ not first in JSON-LD"
    assert all(q in names for q in KEPT_FAQ), "original FAQ removed"
    assert NEW_FAQ in text(raw), "new FAQ not visible"
    dated = [b for b in blocks if b.get("@type") in {"Article", "TechArticle", "HowTo"}]
    assert dated and dated[0].get("dateModified") == MODIFIED, "dateModified"


def main() -> int:
    raw = PAGE.read_text(encoding="utf-8")
    check(raw)
    others = [p for p in (ROOT / "site").rglob("index.html") if p != PAGE and NEW_FAQ in p.read_text(encoding="utf-8")]
    assert not others, f"new FAQ also on {others}"

    for label, broken in (
        ("en dash put back", raw.replace("The short answer:", "The short answer –", 1)),
        ("kept heading removed", raw.replace("<h2>Where to look first</h2>", "<h3>Where to look first</h3>", 1)),
    ):
        try:
            check(broken)
        except AssertionError:
            print(f"CONTROL rejected: {label}")
        else:
            raise AssertionError(f"negative control passed: {label}")
    print("LAYOUT SHIFT UPGRADE 1122 ok")
    return 0


if __name__ == "__main__":
    sys.exit(main())
