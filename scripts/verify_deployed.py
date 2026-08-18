#!/usr/bin/env python3
"""Did the build that is on this disk actually reach the internet?

**The failure this exists for.** On 2026-08-17 two commits were merged, the
tree was clean and equal to origin/main, every gate in `deploy.sh` was green,
and `site/index.html` carried a real-audit screenshot and a "30 days, no
conditions" refund line. The live site served neither. The answer came back
from Matthew as *"dockets site is still the same or its not updating"*, and it
became rule 0.8 the next day: a commit is not a ship, a green build is not a
live page.

Twenty-odd gates guarded the build. Nothing at all watched the gap between the
build and the CDN, which is the one place a reader lives.

**Why a build id and not a page diff.** `verify_live.py` already fetches pages
and checks their content, and it still could not have caught this cheaply: the
thing missing was partly a `.webp`, and an image is not in `index.html`. So the
id is a sha256 over *every file* under `site/` — markup, CSS, fonts, images,
datasets — which means any change anywhere changes it, and checking one URL
then proves the whole tree is current.

**Why it cannot chase its own tail.** The placeholder `__BUILD_ID__` is a
fixed-length constant and is hashed in place, before it is rewritten. Stamping
the id therefore cannot alter the id being stamped.

**What this does NOT prove.** That the pages are correct — that is every other
gate's job. Only that what a stranger is served is what was built here. Those
are different claims and this repo has now been bitten by assuming the first
implies the second.

    python3 scripts/verify_deployed.py               # after deploy
    python3 scripts/verify_deployed.py --wait 300    # poll while the CDN catches up
"""
from __future__ import annotations

import argparse
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BUILD_ID = ROOT / "site" / "_data" / "build-id.txt"
URL = "https://docketseo.app/"

#: Cache-busting is the point: a CDN that hands back a cached copy would let a
#: failed deploy pass, which is the exact bug being guarded.
HEADERS = {
    "Cache-Control": "no-cache",
    "Pragma": "no-cache",
    "User-Agent": "docket-verify-deployed/1.0",
}


def served_build_id(url: str) -> tuple[str, int]:
    req = urllib.request.Request(url + f"?cb={time.time_ns()}", headers=HEADERS)
    with urllib.request.urlopen(req, timeout=30) as response:
        body = response.read().decode("utf-8", "replace")
    marker = '<meta name="build-id" content="'
    start = body.find(marker)
    if start == -1:
        return "", len(body)
    start += len(marker)
    return body[start:body.find('"', start)], len(body)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--wait", type=int, default=0,
                    help="seconds to keep polling while the CDN propagates")
    ap.add_argument("--url", default=URL)
    args = ap.parse_args()

    if not BUILD_ID.is_file():
        print(f"FAIL: {BUILD_ID} is missing — run scripts/build.py first")
        return 1
    expected = BUILD_ID.read_text().strip()

    deadline = time.time() + args.wait
    while True:
        try:
            got, size = served_build_id(args.url)
        except (urllib.error.URLError, OSError) as error:
            got, size = f"<unreachable: {error}>", 0

        if got == expected:
            print(f"DEPLOYED ok — {args.url} serves build {expected} "
                  f"({size:,} bytes), which is what is in site/")
            return 0

        if time.time() >= deadline:
            print(f"FAIL: {args.url} serves build id {got!r}, "
                  f"but site/ was built as {expected!r}.")
            if not got:
                print("  No build-id meta tag at all — the served page predates "
                      "this check, so the deploy has not landed.")
            print("  The build on this disk is not the build on the internet. "
                  "That is the 2026-08-17 failure, and it is what this gate is for.")
            return 1

        time.sleep(10)


if __name__ == "__main__":
    raise SystemExit(main())
