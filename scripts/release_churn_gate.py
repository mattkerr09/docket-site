#!/usr/bin/env python3
"""Require a named reason when a release changes more than 12 pages' text.

Compared with origin/main (the last deployed state), not HEAD: see baseline_ref."""
from __future__ import annotations

from brand import BASE, LASTMOD_FILE, SITE_BRAND

import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent.parent
LASTMOD = "data/" + LASTMOD_FILE
MAX_CHANGED_PAGES = 12


def baseline_ref() -> str:
    """The state to compare against: the last pushed (deployed) main.

    Releases here are committed BEFORE deploy.sh runs, so HEAD already holds the
    change and would always read zero. origin/main moves only when a deploy pushes.
    CHURN_BASELINE overrides it; with no origin/main (a fresh clone, a test repo)
    the gate falls back to HEAD."""
    ref = os.environ.get("CHURN_BASELINE", "").strip() or "origin/main"
    check = subprocess.run(["git", "rev-parse", "--verify", "--quiet", f"{ref}^{{commit}}"],
                           cwd=ROOT, capture_output=True, text=True)
    return ref if check.returncode == 0 else "HEAD"


def head_lastmod() -> dict:
    ref = baseline_ref()
    candidates = [LASTMOD]
    if SITE_BRAND == "checkengine":
        # Before the rename ships, the deployed baseline has Docket hashes.
        candidates.append("data/page-lastmod.json")
    for path in candidates:
        result = subprocess.run(
            ["git", "show", f"{ref}:{path}"], cwd=ROOT,
            capture_output=True, text=True,
        )
        if result.returncode == 0:
            return json.loads(result.stdout)
        # Only a missing file permits the fallback. Other git errors must fail.
        listing = subprocess.run(
            ["git", "ls-tree", "--name-only", ref, "--", path],
            cwd=ROOT, capture_output=True, text=True, check=True,
        )
        if listing.stdout.strip():
            raise ValueError(result.stderr.strip())
    return {}


def main() -> int:
    try:
        current = json.loads((ROOT / LASTMOD).read_text(encoding="utf-8"))
        previous = head_lastmod()
        changed = sorted(
            page for page, record in current.items()
            if page not in previous or record["hash"] != previous[page]["hash"]
        )
    except (OSError, ValueError, KeyError, TypeError, AttributeError,
            subprocess.CalledProcessError) as error:
        print(f"CHURN FAIL  Could not compare page hashes. {error}", file=sys.stderr)
        return 1

    print(f"CHURN  {len(changed)} changed pages. Limit is {MAX_CHANGED_PAGES}.")
    for page in changed[:15]:
        path = page.removesuffix("index.html")
        print(f"  {BASE}/{path}")

    if len(changed) <= MAX_CHANGED_PAGES:
        print("CHURN OK")
        return 0

    reason = os.environ.get("DOCKET_SITEWIDE_REASON", "").strip()
    if reason:
        print(f"CHURN OK  DOCKET_SITEWIDE_REASON={reason}")
        return 0

    print("CHURN FAIL  Set DOCKET_SITEWIDE_REASON to a sentence explaining the site-wide change.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
