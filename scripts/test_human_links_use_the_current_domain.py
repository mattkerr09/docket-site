#!/usr/bin/env python3
"""Offline reader-link gate. Build only in a temporary repository copy."""
from __future__ import annotations

import json
from pathlib import Path
import re
import tempfile
from urllib.parse import urlsplit

from test_launch_price_copy import scratch
from test_rename_brand import Page, build

ROOT = Path(__file__).resolve().parent.parent
OLD = "https://docketseo.app"
CURRENT = "https://checkengineseo.com"
MACHINE_PATHS = {
    "/updater.json",  # Installed apps check this feed for updates.
    "/offer.json",  # Installed apps read the price and activation offer here.
    "/data/knowledge.json",  # Installed apps fetch their knowledge file here.
}


def check_site(site):
    llms = (site / "llms.txt").read_text()
    assert OLD + "/bot/" not in llms, "llms.txt retains the old crawler page link"
    assert OLD + "/assets/" not in llms, "llms.txt retains an old asset link"
    for path in ("/bot/", "/assets/docket-sample-report.pdf"):
        assert f"]({CURRENT}{path})" in llms, path
    for path in sorted(MACHINE_PATHS):
        assert OLD + path in llms, ("missing machine address", path)

    offer = json.loads((site / "offer.json").read_text())
    assert offer["sample_report_url"] == OLD + "/assets/docket-sample-report.pdf"
    assert offer == json.loads((ROOT / "site/offer.json").read_text()), "offer fields changed"

    pages = list(site.rglob("*.html"))
    machine_links = set()
    for path in pages:
        for tag, attrs in Page(path.read_text()).tags:
            if tag != "a":
                continue
            href = attrs.get("href") or ""
            url = urlsplit(href)
            if url.hostname == "docketseo.app":
                assert url.path in MACHINE_PATHS, (path.relative_to(site), href)
                machine_links.add(url.path)
    assert machine_links == MACHINE_PATHS, machine_links
    sitemap = (site / "sitemap.xml").read_text()
    assert "docketseo.app" not in sitemap
    assert all(urlsplit(url).hostname == "checkengineseo.com"
               for url in re.findall(r"<loc>(.*?)</loc>", sitemap))

    assistants = (site / "ai-assistants/index.html").read_text()
    privacy = (site / "legal/privacy/index.html").read_text()
    assert "https://mcp.docketseo.app/mcp" in assistants
    assert "mcp.docketseo.app/app-event" in privacy
    assert "mailto:support@docketseo.app" in privacy
    assert "/Applications/Docket.app/" in llms
    assert "`checkengine audit`" in llms
    # These are the actual crawler user-agent strings, not links to a page.
    bot = (site / "bot/index.html").read_text()
    assert "Docket-SEO-Audit/1.0 (+https://docketseo.app/bot/)" in bot
    return len(pages)


def main():
    with tempfile.TemporaryDirectory(prefix="test-human-links-") as temporary:
        destination = Path(temporary)
        scratch(destination)
        build(destination, "checkengine")
        count = check_site(destination / "site")
    print("PASS llms.txt reader links use https://checkengineseo.com")
    print("PASS offer.json unchanged, including the installed-app sample report URL")
    print("PASS machine addresses, support email, app bundle and CLI preserved")
    print(f"PASS {count} HTML pages allow only the three retained machine paths; sitemap uses the current host")
    print("SKIP brand image rendering: DOCKET_SKIP_BRAND_ASSETS=1 TZ=UTC")
    print("OK")


if __name__ == "__main__":
    main()
