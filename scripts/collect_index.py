#!/usr/bin/env python3
"""Collect the Docket Index dataset: AI-crawler access across real websites.

The moat. Nobody publishes large-N, reproducible measurement of which sites let
AI search engines read them — and Docket's robots.txt parser already answers it
exactly. Every number the site publishes comes from this script, and the script
plus its input list ship with the dataset so anyone can re-run it and get the
same answer.

Politeness: exactly ONE request per host (its /robots.txt), serialised with a
delay. That is a smaller footprint than a single human visiting the homepage.

Usage:
    python3 scripts/collect_index.py sites.txt out.json [--delay 0.4]
"""
from __future__ import annotations

import sys as _sys
from pathlib import Path as _Path
_sys.path.insert(0, str(_Path(__file__).resolve().parent))
import app_path  # noqa: E402

import argparse
import datetime
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

# Docket's own engine — the published numbers must come from the same parser the
# product ships, or the Index is measuring something the tool does not.
ENGINE = app_path.backend()
sys.path.insert(0, str(ENGINE))

from seo_engine.fetcher import Fetcher  # noqa: E402
from seo_engine.robots import AI_USER_AGENTS, SEARCH_USER_AGENTS, RobotsTxt  # noqa: E402

#: Crawlers whose access decides whether you can appear in an AI answer at all,
#: as opposed to whether you are used for model training. Blocking the second is
#: a legitimate policy choice and is reported separately, never as a failure.
CITATION_BOTS = ("OAI-SearchBot", "PerplexityBot", "Claude-SearchBot", )
TRAINING_BOTS = ("GPTBot", "ClaudeBot", "Applebot-Extended", "CCBot", "Bytespider",
                 "meta-externalagent")


def measure(host: str, category: str, fetcher: Fetcher) -> dict:
    url = f"https://{host}/robots.txt"
    resp = fetcher.get(url)

    record = {
        "host": host,
        "category": category,
        "status": resp.status,
        "error": resp.error or "",
        "bytes": len(resp.body),
    }
    if resp.error or resp.status == 0:
        record["reachable"] = False
        return record

    # A robots.txt that answers with HTML is a soft-404 catch-all, not rules.
    is_html = "html" in resp.content_type
    text = "" if is_html else resp.text
    record["reachable"] = True

    # Whether this is a real robots.txt is decided by CONTENT, not status code.
    # stackoverflow.com serves a genuine, restrictive robots.txt with HTTP 418
    # as bot deterrence; a status-only test called it "no robots.txt" while
    # still parsing the body, which is the worst of both. Requiring a
    # `User-agent:` line is the honest test, and it also rejects the 404 pages
    # and block screens that a status test lets through.
    has_directives = bool(re.search(r"^\s*user-agent\s*:", text, re.I | re.M))
    record["has_robots"] = has_directives
    record["served_with_status"] = resp.status
    status = resp.status if has_directives else 404

    # Content-signals (adopted ~2025, Cloudflare-backed) express usage intent
    # declaratively: `Content-signal: search=no, ai-train=no`. It is not
    # robots.txt and no crawler is obliged to honour it, but a site using it has
    # clearly thought about AI access — worth measuring separately.
    signal = re.search(r"^\s*content-signal\s*:\s*(.+)$", text, re.I | re.M)
    record["content_signal"] = signal.group(1).strip() if signal else ""

    robots = RobotsTxt(text, status, url)
    record["ai_access"] = {name: robots.allowed("/", name) for name in AI_USER_AGENTS}
    record["search_access"] = {name: robots.allowed("/", name) for name in SEARCH_USER_AGENTS}
    record["has_sitemap_directive"] = bool(robots.sitemaps)
    record["mentions_any_ai_bot"] = any(
        name.lower() in text.lower() for name in AI_USER_AGENTS
    )
    record["blocks_citation_bots"] = sorted(
        b for b in CITATION_BOTS if record["ai_access"].get(b) is False
    )
    record["blocks_training_bots"] = sorted(
        b for b in TRAINING_BOTS if record["ai_access"].get(b) is False
    )
    record["blocks_search"] = sorted(
        b for b, ok in record["search_access"].items() if ok is False
    )
    return record


def summarise(records: list[dict]) -> dict:
    # Only sites with a real robots.txt can be said to allow or block anything.
    # A site with none has no policy; counting it as "allows everything"
    # would overstate openness and understate the blocking figures.
    live = [r for r in records if r.get("reachable") and r.get("has_robots")]
    n = len(live)
    if not n:
        return {"n": 0}

    by_bot = {}
    for bot in AI_USER_AGENTS:
        blocked = sum(1 for r in live if r["ai_access"].get(bot) is False)
        by_bot[bot] = {
            "blocked": blocked,
            "pct": round(100 * blocked / n, 1),
            "owner": AI_USER_AGENTS[bot]["owner"],
            "purpose": AI_USER_AGENTS[bot]["purpose"],
        }

    by_category: dict[str, dict] = defaultdict(lambda: {"n": 0, "blocking_citation": 0})
    for r in live:
        bucket = by_category[r["category"]]
        bucket["n"] += 1
        if r["blocks_citation_bots"]:
            bucket["blocking_citation"] += 1
    for bucket in by_category.values():
        bucket["pct"] = round(100 * bucket["blocking_citation"] / bucket["n"], 1)

    return {
        "n": n,
        "attempted": len(records),
        "unreachable": sum(1 for r in records if not r.get("reachable")),
        "no_robots_txt": sum(1 for r in records if r.get("reachable") and not r.get("has_robots")),
        "mentions_any_ai_bot": sum(1 for r in live if r.get("mentions_any_ai_bot")),
        "blocking_any_citation_bot": sum(1 for r in live if r["blocks_citation_bots"]),
        "blocking_any_training_bot": sum(1 for r in live if r["blocks_training_bots"]),
        "blocking_a_search_engine": sum(1 for r in live if r["blocks_search"]),
        "has_sitemap_directive": sum(1 for r in live if r.get("has_sitemap_directive")),
        "uses_content_signal": sum(1 for r in live if r.get("content_signal")),
        "by_bot": by_bot,
        "by_category": dict(by_category),
        "most_blocked": sorted(
            by_bot.items(), key=lambda kv: -kv[1]["blocked"]
        )[:5],
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("sites", help="text file: host,category per line")
    ap.add_argument("out", help="where to write the JSON dataset")
    ap.add_argument("--delay", type=float, default=0.4)
    args = ap.parse_args()

    entries = []
    for line in Path(args.sites).read_text().splitlines():
        line = line.split("#", 1)[0].strip()
        if not line:
            continue
        host, _, category = line.partition(",")
        entries.append((host.strip(), (category or "other").strip()))

    fetcher = Fetcher(timeout=12.0)
    records = []
    import time

    for i, (host, category) in enumerate(entries, 1):
        try:
            records.append(measure(host, category, fetcher))
        except Exception as e:  # noqa: BLE001 — one bad host must not lose the run
            records.append({"host": host, "category": category,
                            "reachable": False, "error": f"{type(e).__name__}: {e}"})
        if i % 20 == 0:
            print(f"  {i}/{len(entries)}", file=sys.stderr, flush=True)
        time.sleep(args.delay)

    payload = {
        "collected": datetime.datetime.now(datetime.timezone.utc)
        .isoformat(timespec="seconds"),
        "method": (
            "One GET to https://<host>/robots.txt per site. Parsed with Docket's own "
            "RFC 9309 robots parser (longest-match, wildcard and $-anchor support). "
            "A site is counted as blocking a crawler when that crawler is disallowed "
            "from '/'. Sites whose robots.txt is unreachable are excluded from "
            "percentages and reported separately."
        ),
        "summary": summarise(records),
        "records": records,
    }
    Path(args.out).write_text(json.dumps(payload, indent=2))
    s = payload["summary"]
    print(f"\n{s['n']} sites measured ({s['unreachable']} unreachable)")
    print(f"  blocking >=1 AI search crawler: {s['blocking_any_citation_bot']} "
          f"({100 * s['blocking_any_citation_bot'] / s['n']:.1f}%)")
    print(f"  blocking >=1 training crawler:  {s['blocking_any_training_bot']} "
          f"({100 * s['blocking_any_training_bot'] / s['n']:.1f}%)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
