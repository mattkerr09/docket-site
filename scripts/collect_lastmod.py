#!/usr/bin/env python3
"""Seed the selected brand's lastmod store from real content changes.

    python3 scripts/collect_lastmod.py
    python3 scripts/collect_lastmod.py --site /path/to/scratch/site

Matthew's plan, 2026-09-24: "Only change a page's sitemap date when its content
really changes (Docket shows it clearly)". Nearly every URL read 09-23 because
`lastmod` was the last commit to the page's SOURCE MODULE, and one module
builds many pages: an edit to comparisons.py re-dated all fourteen /vs/ pages,
one to pages.py every /for/ and /legal/ page.

The build now keeps a fingerprint per page (build.page_fingerprint: title,
description and the article's own text, excluding shared boilerplate) and
moves a page's date only when its fingerprint moves. This script seeds that
record from history, so switching the rule on does not date every page today:
for each page it walks the committed revisions of its built HTML, newest
first, and takes the commit date of the oldest revision in the current run of
identical fingerprints.
"""
from __future__ import annotations

import argparse
import collections
import datetime
import json
import subprocess
import sys
from urllib.parse import urlsplit
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from build import LASTMOD, SITE, page_fingerprint  # noqa: E402


def _git(*args: str) -> str:
    return subprocess.run(["git", "-C", str(ROOT), *args], capture_output=True,
                          text=True, check=True).stdout


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--site", type=Path, default=SITE,
                        help="Built site to seed; history is read from this repository.")
    args = parser.parse_args()
    site = args.site.resolve()
    store: dict = {}
    # The sitemap is the build's exact page inventory. A body can legitimately
    # demonstrate content="noindex", so do not search entire HTML for it.
    sitemap = ET.parse(site / "sitemap.xml")
    pages = sorted(site / urlsplit(node.text).path.lstrip("/") / "index.html"
                   for node in sitemap.findall(".//{*}loc"))
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

    try:
        for number, page in enumerate(pages, 1):
            key = page.relative_to(site).as_posix()
            raw = page.read_text(encoding="utf-8")
            rel = "site/" + key
            log = [l.split() for l in _git("log", "--format=%H %cI", "--", rel).splitlines() if l]
            head_fp = page_fingerprint(raw)
            # If current content has not shipped in any committed HTML yet, it is
            # new today. Otherwise walk the consecutive identical revisions back.
            date = datetime.date.today().isoformat()
            for rev, when in log:
                if page_fingerprint(show(rev, rel)) != head_fp:
                    break
                date = when[:10]
            store[key] = {"hash": head_fp, "date": date, "changed_in_build": False}
            if number % 50 == 0:
                print(f"read history for {number}/{len(pages)} pages", flush=True)
    finally:
        cat.stdin.close()
        cat.stdout.close()
        status = cat.wait()
    if status != 0:
        raise RuntimeError("git cat-file failed")
    LASTMOD.write_text(json.dumps(store, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    dates = sorted({v["date"] for v in store.values()})
    print(f"seeded {len(store)} pages; {len(dates)} distinct dates, "
          f"{dates[0]} .. {dates[-1]}")
    for day, count in sorted(collections.Counter(v["date"] for v in store.values()).items()):
        print(f"  {day}: {count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
