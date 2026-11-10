#!/usr/bin/env python3
"""Build both brands offline in scratch copies and check anonymous app count claims."""
from __future__ import annotations

import json
from pathlib import Path
import re
import shutil
import sys
import tempfile

sys.dont_write_bytecode = True
from test_rename_brand import Page, build, json_values, words

ROOT = Path(__file__).resolve().parent.parent
FALSE_CLAIMS = re.compile(
    r"\b(?:no|zero|without)\s+telemetry\b|\bno account or telemetry\b|"
    r"\btelemetry[- ]free\b|\bno analytics on you\b|\bno tracking\b|"
    r"\bprivate by design\b|\bnever phones? home\b|\bnot phoning home\b|"
    r"\b(?:nothing|no data|no information|never)\s+(?:ever\s+)?leaves?\s+"
    r"(?:your |the )?(?:computer|mac|machine)\b|\bno data leaving the building\b",
    re.I,
)


def allowed_events():
    source = (ROOT / "workers/ai-crawler-check/src/app-events.js").read_text()
    declaration = re.search(r"export const APP_EVENTS = \[([^\]]+)\]", source)
    assert declaration, "Cannot find the Worker's allowed events"
    events = re.findall(r"'([^']+)'", declaration[1])
    assert len(events) == 3 and len(set(events)) == 3, events
    return events


def check_built(destination):
    site = destination / "site"
    raw = (site / "legal/privacy/index.html").read_text()
    section = re.search(r"<h[23]>What the app tells us, anonymously</h[23]>(.*?)(?=<h2>)", raw, re.S)
    assert section, "Privacy page is missing the app counts section"
    text = words(section[1])
    for phrase in (
        "the first time the app is opened", "the first time an audit finishes",
        "the first time the free version reaches its limit", "shows the unlock",
        "app version", "Mac, Windows or Linux", "once per copy and per event",
        "DOCKET_NO_COUNTS=1", "empty file named no-counts", ".docket folder in your home folder",
        "source builds", "offline mode", "Keep it private: only contact this site", "before there is a chance to choose", "internet address", "daily tally", "never who",
        "web address", "results or reports", "licence key", "ID or name", "anything from your files",
        "mcp.docketseo.app/app-event", "no cookie", "no body",
    ):
        assert phrase in text, f"Privacy page is missing: {phrase}"
    for event in allowed_events():
        assert event in text, f"Worker event missing from privacy page: {event}"
    assert not any(dash in text for dash in ("\u2013", "\u2014")), "Keep the new copy plain"

    checked = 0
    for path in sorted(site.rglob("*.html")):
        page_raw = path.read_text()
        text = words(page_raw)
        # Include metadata, alt text and FAQ/schema answers as well as visible prose.
        for block in Page(page_raw).json_ld:
            text += " " + " ".join(json_values(block))
        match = FALSE_CLAIMS.search(text)
        assert not match, f"{path.relative_to(site)}: false app claim: {match[0]}"
        checked += 1
    for name in ("llms.txt", "llms-full.txt"):
        path = site / name
        if path.exists():
            match = FALSE_CLAIMS.search(" ".join(path.read_text().split()))
            assert not match, f"{name}: false app claim: {match[0]}"
    help_data = json.loads((destination / "data/help-answers.json").read_text())
    assert not FALSE_CLAIMS.search(" ".join(json_values(help_data)))
    print(f"APP COUNTS privacy OK: {checked} pages and machine-readable copy")


def main():
    anchor = (ROOT / "data/build-id.txt").read_bytes()
    with tempfile.TemporaryDirectory(prefix="test-app-counts-privacy-") as temporary:
        for mode in ("docket", "checkengine"):
            destination = Path(temporary) / mode
            for directory in ("scripts", "data", "site", "workers/ai-crawler-check/src"):
                shutil.copytree(ROOT / directory, destination / directory,
                                ignore=shutil.ignore_patterns("__pycache__", ".env*", "*.env", "node_modules"))
            # This helper sets DOCKET_SKIP_BRAND_ASSETS=1 and TZ=UTC and clears DOCKET_DEPLOY.
            build(destination, mode)
            check_built(destination)
    assert (ROOT / "data/build-id.txt").read_bytes() == anchor
    print("APP COUNTS privacy OK: both brands built in scratch copies; brand images skipped")


if __name__ == "__main__":
    main()
