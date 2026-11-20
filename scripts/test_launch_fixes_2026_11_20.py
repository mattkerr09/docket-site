#!/usr/bin/env python3
"""Offline launch fixes, with both brands and sale expiry built in scratch."""
from __future__ import annotations

import json
from pathlib import Path
import re
import tempfile
import sys

sys.path.insert(1, str(Path(__file__).resolve().parent / "articles"))

import brand
import render as R
from articles import home
from test_black_friday_sale_copy import build_after, words
from test_launch_price_copy import scratch
from test_rename_brand import Page, build


def check_site(site, opened):
    raw = (site / "index.html").read_text()
    strip = re.search(r'<aside id="product-hunt-welcome".*?</aside>', raw, re.S).group()
    attrs = Page(strip).tags[0][1]
    assert "hidden" in attrs
    expected = home.PRODUCT_HUNT_WELCOME
    if not opened:
        expected = expected.removesuffix(" " + R.founding_price_sentence())
    assert words(re.search(r"<p>(.*?)</p>", strip, re.S).group(1)) == expected
    buttons = [attrs for tag, attrs in Page(strip).tags if tag == "a" and attrs.get("data-ev") == "Download"]
    assert len(buttons) == 2
    assert [b["href"] for b in buttons] == [R.download_url("home-producthunt-mac"),
                                            R.download_url("home-producthunt-win", to=R.WIN_SETUP)]
    script = re.search(r'<script id="product-hunt-reveal">(.*?)</script>', raw, re.S).group(1)
    assert script == home.PRODUCT_HUNT_REVEAL
    assert re.findall(r"\.get\((.*?)\)", script) == ["'ref'"]
    assert "new URLSearchParams(location.search)" in script
    assert ".toLowerCase()==='producthunt'" in script
    assert not re.search(r"fetch|XMLHttpRequest|storage|cookie|sendBeacon|https?://", script, re.I)
    assert raw.index(strip) < raw.index('<h1 class="hero-h1">')
    h1 = re.search(r'<h1 class="hero-h1">(.*?)</h1>', raw, re.S).group(1)
    assert words(h1) == "Can ChatGPT, Claude and Perplexity read your site?"
    for path in site.rglob("*.html"):
        page = path.read_text()
        if path != site / "index.html":
            assert 'id="product-hunt-welcome"' not in page, path
        count = page.count(brand.DOWNLOAD_NAME_NOTE)
        assert count == (1 if path == site / "download/index.html" else 0), path
        assert "before it will run an audit" not in page, path
        if path == site / "download/index.html":
            assert page.index(brand.DOWNLOAD_NAME_NOTE) < page.index('data-ev-button="download-steps"')
            assert all(brand.DOWNLOAD_NAME_NOTE not in json.dumps(block) for block in Page(page).json_ld)
    thanks = words((site / "thank-you/index.html").read_text())
    assert "needs it to show the full report and fix plan." in thanks
    terms = words((site / "legal/terms/index.html").read_text())
    assert "the licence key that shows the full report and fix plan." in terms
    for route in ("download", "help", "faq"):
        text = words((site / route / "index.html").read_text())
        assert R.KEY_REPORT_INSTRUCTION in text, route
        assert "then run your audit" not in text, route
        assert "unlock the full audit" not in text, route
    icon = (site / "favicon.ico").read_bytes()
    assert icon.startswith(bytes((0, 0, 1, 0)))
    assert "favicon.ico" not in (site / "sitemap.xml").read_text()
    assert "/favicon.ico" in json.loads((site / "_redirect-map.json").read_text())
    llms = (site / "llms.txt").read_text()
    price = R.price_sentence() if opened else f"{R.PRICE_STR} once."
    assert f"Price: {price}" in llms
    assert "offer.json for the current price" not in " ".join(llms.split())
    assert "offer.json whether a sale is open" in " ".join(llms.split())
    assert json.loads((site / "offer.json").read_text())["price_cents"] == 5900
    return icon


def main():
    with tempfile.TemporaryDirectory(prefix="test-launch-fixes-") as temporary:
        destination = Path(temporary)
        scratch(destination)
        for name in ("docket", "checkengine"):
            build(destination, name)
            icon = check_site(destination / "site", True)
            build(destination, name)
            assert check_site(destination / "site", True) == icon
            build_after(destination, name)
            assert check_site(destination / "site", False) == icon
    print("PASS both brands: hidden home-only welcome, shared buttons, URL-only reveal, unchanged h1")
    print("PASS download-only installer note and truthful licence key copy")
    print("PASS deterministic root ICO, static inventory, sitemap exclusion and unchanged offer contract")
    print("PASS live Price line and sale status wording before and after sale expiry")


if __name__ == "__main__":
    main()
