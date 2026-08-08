#!/usr/bin/env python3
"""How many sites publish a contact address that cannot receive mail?

docketseo.app did, on all 25 of its pages, for weeks. The question this answers
is whether that was an unusual mistake or an ordinary one, and no published
figure exists either way — so it gets measured rather than guessed.

Method, stated because the number is only worth as much as it:

  * Population is the Tranco top-10,000 sample already collected for the AI
    directives survey, in rank order. Homepage only — one request per host.
  * An address counts as *published* if it appears in a `mailto:` href. Prose
    scraping is left out deliberately: an address written as text may be an
    example, an image caption or a customer's, whereas a mailto is markup
    somebody wrote meaning "write to this".
  * Consumer providers and RFC 2606 reserved names are excluded. Whether
    gmail.com accepts mail is not a fact about the site publishing it.
  * A domain is counted dead only where Docket's own `mailcheck` says so
    conclusively — no MX and an address record on a static host that does not
    run SMTP, or no MX and no address record at all. Anything resting on a
    port-25 probe is recorded separately and excluded from the headline,
    because outbound 25 is blocked on many networks and a blocked probe looks
    exactly like a closed port.

Usage:  python3 scripts/collect_mail.py [--limit 600] [--out site/_data/...]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path.home() / "Downloads" / "SEO audit app" / "backend"))

from seo_engine import mailcheck as M  # noqa: E402

MAILTO = re.compile(rb'href=["\']mailto:([^"\'?>]+)', re.I)
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 "
      "(KHTML, like Gecko) Version/17.0 Safari/605.1.15 Docket/1.0")
#: Homepages are the target and some are enormous. Every mailto worth finding
#: is in the markup long before this.
MAX_BYTES = 900_000


def fetch(host: str, timeout: float = 12.0):
    """(status, addresses). status 0 means the site did not answer."""
    for scheme in ("https://", "http://"):
        req = urllib.request.Request(f"{scheme}{host}/",
                                     headers={"User-Agent": UA})
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                body = resp.read(MAX_BYTES)
                found = {a.decode("ascii", "replace").strip().lower()
                         for a in MAILTO.findall(body)}
                return resp.status, sorted(found)
        except urllib.error.HTTPError as exc:
            return exc.code, []
        except Exception:  # noqa: BLE001 — unreachable is data, not a crash
            continue
    return 0, []


def survey_host(record: dict) -> dict:
    host, rank = record["h"], record["r"]
    status, addresses = fetch(host)
    row = {"host": host, "rank": rank, "status": status,
           "addresses": addresses[:6], "domains": {}}
    if status != 200 or not addresses:
        return row

    domains = []
    for address in addresses:
        domain = address.rpartition("@")[2]
        if (not domain or domain in M.CONSUMER_DOMAINS
                or M.looks_like_placeholder(address)
                or not M.valid_domain(domain)):
            continue
        if domain not in domains:
            domains.append(domain)

    for domain in domains[:3]:
        verdict = M.check_domain(domain, timeout=4.0)
        row["domains"][domain] = {
            "accepts": verdict.accepts_mail,
            "conclusive": verdict.conclusive,
            "static_host": verdict.static_host,
            "reason": verdict.reason,
        }
    return row


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=600)
    ap.add_argument("--workers", type=int, default=16)
    ap.add_argument("--out", default="site/_data/mail-2026-08.json")
    ap.add_argument("--date", required=True, help="YYYY-MM-DD the survey ran")
    args = ap.parse_args()

    source = json.loads(
        (ROOT / "site" / "data" / "ai-directives-2026-08.json").read_text())
    hosts = sorted(source["hosts"], key=lambda h: h["r"])[:args.limit]

    began = time.time()
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        rows = list(pool.map(survey_host, hosts))

    answered = [r for r in rows if r["status"] == 200]
    publishing = [r for r in answered if r["domains"]]

    def verdicts(row):
        return list(row["domains"].values())

    dead_conclusive = [r for r in publishing
                       if any(v["accepts"] is False and v["conclusive"]
                              for v in verdicts(r))]
    dead_probed = [r for r in publishing
                   if r not in dead_conclusive
                   and any(v["accepts"] is False for v in verdicts(r))]
    undetermined = [r for r in publishing
                    if all(v["accepts"] is None for v in verdicts(r))]
    ok = [r for r in publishing
          if any(v["accepts"] is True for v in verdicts(r))]

    payload = {
        "measured": args.date,
        "population": (f"Tranco top {args.limit} by rank, from the same list as "
                       f"the AI directives survey (PYG5J)"),
        "method": (
            "One homepage request per host. An address counts as published "
            "only when it appears in a mailto: href. Consumer providers and "
            "RFC 2606 reserved names are excluded. A domain is dead in the "
            "headline figure only where DNS alone establishes it: no MX plus "
            "an address record on a static host that does not run SMTP, or no "
            "MX and no address record. Verdicts resting on a port-25 probe "
            "are reported separately because outbound 25 is widely blocked."
        ),
        "attempted": len(rows),
        "answered": len(answered),
        "publishing_mailto": len(publishing),
        "dead_conclusive": len(dead_conclusive),
        "dead_probe_only": len(dead_probed),
        "undetermined": len(undetermined),
        "accepts_mail": len(ok),
        "duration_s": round(time.time() - began, 1),
        "dead_examples": [
            {"host": r["host"], "rank": r["rank"],
             "domain": d, "reason": v["reason"], "static_host": v["static_host"]}
            for r in dead_conclusive for d, v in r["domains"].items()
            if v["accepts"] is False and v["conclusive"]
        ][:25],
        "rows": [r for r in rows if r["domains"]],
    }

    out = ROOT / args.out
    out.write_text(json.dumps(payload, indent=2) + "\n")
    print(f"attempted {payload['attempted']}, answered {payload['answered']}, "
          f"publishing a mailto {payload['publishing_mailto']}")
    print(f"  accepts mail      {payload['accepts_mail']}")
    print(f"  dead (DNS alone)  {payload['dead_conclusive']}")
    print(f"  dead (probe only) {payload['dead_probe_only']}")
    print(f"  undetermined      {payload['undetermined']}")
    print(f"-> {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
