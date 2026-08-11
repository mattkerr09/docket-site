#!/usr/bin/env python3
"""Do the mail exchangers a domain publishes actually exist?

The sibling question to `collect_mail_small.py`. That one asked whether a
business publishes a working email address; this one asks something narrower
and nastier of the same population: of the domains that *do* publish an MX
record, how many name a host that does not resolve?

That case passes every "does this domain have an MX record" test ever written.
The record sits in the zone file looking exactly right. There is no host at the
other end.

Same frame, so the two surveys are comparable and Overpass is not asked again:
every element tagged `shop` in OpenStreetMap inside ten named UK city
boundaries carrying a `website` tag, deduplicated to one domain each. See
collect_mail_small.py for why that frame and what it does not cover.

Nothing here needs a homepage fetch — this is DNS only, against domains
OpenStreetMap already publishes.

Usage:  python3 scripts/collect_mx.py --date YYYY-MM-DD
"""
from __future__ import annotations

import sys as _sys
from pathlib import Path as _Path
_sys.path.insert(0, str(_Path(__file__).resolve().parent))
import app_path  # noqa: E402

import argparse
import json
import sys
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(app_path.backend()))

from seo_engine import mailcheck as M  # noqa: E402

FRAME = ROOT / "site" / "_data" / "mail-small-frame.json"


def probe(record: dict):
    """(named exchangers, how many resolve, the shape of the first) or None.

    A lookup that could not complete counts as resolving. The question is
    whether the host is absent, and a network that cannot answer is not
    evidence that it is — the same tri-state discipline as the check itself.
    """
    domain = record["domain"]
    try:
        mx = M.mx_hosts(domain, timeout=3.0)
    except M.Unknown:
        return None
    named = [h for h in mx if h and not h.startswith("(")]
    if not named:
        return None

    alive = 0
    for host in named:
        try:
            if M.a_records(host, timeout=3.0):
                alive += 1
        except M.Unknown:
            alive += 1
    return {"named": len(named), "alive": alive,
            "shape": M.mx_shape(named[0]) or "an exchanger on its own hostname"}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", required=True)
    ap.add_argument("--workers", type=int, default=24)
    ap.add_argument("--out", default="site/_data/mx-2026-08.json")
    args = ap.parse_args()

    frame = json.loads(FRAME.read_text())
    began = time.time()
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        rows = [r for r in pool.map(probe, frame) if r]

    all_dead = [r for r in rows if r["alive"] == 0]
    partial = [r for r in rows if 0 < r["alive"] < r["named"]]

    payload = {
        "measured": args.date,
        "frame": ("The same OpenStreetMap frame as the address survey: every "
                  "element tagged shop inside ten named UK city boundaries "
                  "carrying a website tag, one entry per domain"),
        "source": "OpenStreetMap, ODbL — DNS only, no pages were fetched",
        "method": (
            "For every domain in the frame, resolve its MX records and then "
            "resolve each named exchanger. A domain counts as dead only when "
            "no exchanger resolves. A lookup that could not complete counts "
            "as resolving, because a network that cannot answer is not "
            "evidence that a host is absent."
        ),
        "frame_size": len(frame),
        "publishing_mx": len(rows),
        "all_exchangers_dead": len(all_dead),
        "partial_failure": len(partial),
        # The provider shape, never the business and never the cause. A tenant
        # that no longer resolves could be a lapsed subscription, a migration
        # half-finished, or a record left behind; that is not visible from
        # outside and guessing would be worse than saying nothing.
        "dead_shapes": dict(Counter(r["shape"] for r in all_dead).most_common()),
        "duration_s": round(time.time() - began, 1),
    }
    (ROOT / args.out).write_text(json.dumps(payload, indent=2) + "\n")

    print(f"frame {payload['frame_size']}, publishing an MX "
          f"{payload['publishing_mx']}")
    print(f"  every exchanger dead  {payload['all_exchangers_dead']}")
    print(f"  partial failure       {payload['partial_failure']}")
    for shape, n in payload["dead_shapes"].items():
        print(f"      {n:3d}  {shape}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
