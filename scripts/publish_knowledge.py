#!/usr/bin/env python3
"""Validate and publish the SEO knowledge feed.

The *judgement* in keeping this current is not automatable: deciding that a
newly announced crawler matters, or that a piece of advice has been superseded,
means reading primary sources and thinking. That happens in the improvement
loop. This script is the gate that stands between that thinking and the live
feed, so a careless edit cannot ship.

It refuses to publish a file that:
  * is not valid JSON, or is a schema version the shipped app cannot read
  * carries no compiled date, or one older than what is already live
  * has lost crawlers without saying so (a silent deletion is how a site ends
    up blocking a bot Scout stopped mentioning)
  * cites no source for a section that has entries
"""
from __future__ import annotations

import json
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LIVE = "https://scoutseo.app/data/knowledge.json"
LOCAL = ROOT / "site" / "data" / "knowledge.json"
SCHEMA_VERSION = 1


def _live() -> dict:
    try:
        with urllib.request.urlopen(LIVE, timeout=15) as resp:
            return json.loads(resp.read().decode())
    except Exception:  # noqa: BLE001 — nothing live yet is a valid state
        return {}


def main() -> int:
    problems: list[str] = []
    try:
        fresh = json.loads(LOCAL.read_text())
    except Exception as exc:  # noqa: BLE001
        print(f"FAIL — {LOCAL} is not readable JSON: {exc}")
        return 1

    if fresh.get("schema_version") != SCHEMA_VERSION:
        problems.append(
            f"schema_version is {fresh.get('schema_version')}, the shipped app "
            f"reads {SCHEMA_VERSION}"
        )
    if not fresh.get("compiled"):
        problems.append("no compiled date")

    live = _live()
    if live:
        if fresh.get("compiled", "") <= live.get("compiled", ""):
            problems.append(
                f"compiled {fresh.get('compiled')} is not newer than the live "
                f"{live.get('compiled')} — clients ignore it"
            )
        lost = set(live.get("ai_crawlers") or {}) - set(fresh.get("ai_crawlers") or {})
        if lost:
            noted = {s.get("advice", "") + s.get("why", "")
                     for s in fresh.get("superseded") or []}
            unexplained = [b for b in lost if not any(b in n for n in noted)]
            if unexplained:
                problems.append(
                    "crawlers removed with no `superseded` entry explaining why: "
                    + ", ".join(sorted(unexplained))
                )

    for section in ("ai_crawlers", "web_vitals", "algorithm_notes"):
        if fresh.get(section) and not (fresh.get("sources") or {}).get(section):
            problems.append(f"{section} has entries but no source recorded")

    if problems:
        print("FAIL — knowledge feed not publishable:")
        for p in problems:
            print(f"  · {p}")
        return 1

    print(f"PASS — knowledge feed dated {fresh['compiled']}, "
          f"{len(fresh.get('ai_crawlers') or {})} crawlers, "
          f"{len(fresh.get('algorithm_notes') or [])} notes")
    return 0


if __name__ == "__main__":
    sys.exit(main())
