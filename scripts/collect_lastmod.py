#!/usr/bin/env python3
"""Seed data/page-lastmod.json: the day each page's CONTENT last changed.

    python3 scripts/collect_lastmod.py

Matthew's plan, 2026-09-24: "Only change a page's sitemap date when its content
really changes (Docket shows it clearly)". Nearly every URL read 09-23 because
`lastmod` was the last commit to the page's SOURCE MODULE, and one module
builds many pages: an edit to comparisons.py re-dated all fourteen /vs/ pages,
one to pages.py every /for/ and /legal/ page.

The build now keeps a fingerprint per page (build.page_fingerprint: title,
description and the article text, never the head where the build id lives) and
moves a page's date only when its fingerprint moves. This script seeds that
record from history, so switching the rule on does not date every page today:
for each page it walks the committed revisions of its built HTML, newest
first, and takes the commit date of the oldest revision in the current run of
identical fingerprints.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from build import LASTMOD, SITE, page_fingerprint  # noqa: E402


def _git(*args: str) -> str:
    return subprocess.run(["git", "-C", str(ROOT), *args], capture_output=True,
                          text=True).stdout


def main() -> int:
    store: dict = {}
    pages = sorted(p for p in SITE.rglob("index.html"))
    cat = subprocess.Popen(["git", "-C", str(ROOT), "cat-file", "--batch"],
                           stdin=subprocess.PIPE, stdout=subprocess.PIPE)

    def show(rev: str, rel: str) -> str:
        cat.stdin.write(f"{rev}:{rel}\n".encode()); cat.stdin.flush()
        header = cat.stdout.readline().decode()
        if header.endswith("missing\n"):
            return ""
        size = int(header.split()[2])
        body = cat.stdout.read(size); cat.stdout.read(1)
        return body.decode("utf-8", "replace")

    for page in pages:
        rel = page.relative_to(ROOT).as_posix()
        log = [l.split() for l in _git("log", "--format=%H %cI", "--", rel).splitlines() if l]
        if not log:
            continue
        head_fp = page_fingerprint(show(log[0][0], rel))
        date = log[0][1][:10]
        for rev, when in log:
            if page_fingerprint(show(rev, rel)) != head_fp:
                break
            date = when[:10]
        store[page.relative_to(SITE).as_posix()] = {"hash": head_fp, "date": date}
    cat.stdin.close(); cat.wait()
    LASTMOD.write_text(json.dumps(store, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    dates = sorted({v["date"] for v in store.values()})
    print(f"seeded {len(store)} pages; {len(dates)} distinct dates, "
          f"{dates[0]} .. {dates[-1]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
