#!/usr/bin/env python3
"""How many addresses Google actually crawls from, and whether our check works.

/learn/log-file-analysis/ argues that you cannot identify Googlebot from a
user-agent string, and that argument needs a number rather than an assertion.
Google publishes its crawler address ranges as three JSON files, so this counts
them from the primary source and records the date, because the lists change.

It also spot-checks Docket's own verification: take one address out of each of
the first few published Googlebot ranges and run the reverse-then-forward DNS
check on it. Those addresses are Googlebot by Google's own definition, so
anything that fails is a bug in us.

That is a spot check and the dataset says so. Six addresses is not a rate and
must never be published as a percentage — it is a smoke test that the check
does what it claims against real DNS, nothing more. The sample is small on
purpose: every address costs two lookups against somebody else's resolver.
"""
from __future__ import annotations

import sys as _sys
from pathlib import Path as _Path
_sys.path.insert(0, str(_Path(__file__).resolve().parent))
import app_path  # noqa: E402

import ipaddress
import json
import time
import urllib.request
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "site" / "_data" / "googlebot.json"
BASE = "https://developers.google.com/static/search/apis/ipranges"

#: The three lists Google publishes, and what each is for.
LISTS = {
    "googlebot": "Googlebot itself — the crawler that builds the search index",
    "special-crawlers": "AdsBot, APIs-Google and the other special-case crawlers",
    "user-triggered-fetchers": "fetches a user asked for, such as Search Console live tests",
}

#: How many addresses to actually resolve. Small on purpose.
SPOT_CHECK = 6


def _fetch(name: str) -> dict:
    req = urllib.request.Request(
        f"{BASE}/{name}.json",
        headers={"User-Agent": "docketseo.app dataset collector"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def main() -> None:
    import sys
    sys.path.insert(0, str(app_path.backend()))
    from seo_engine.logfile import verify_ip

    lists = {}
    total = 0
    for name, purpose in LISTS.items():
        data = _fetch(name)
        prefixes = data.get("prefixes", [])
        v4 = [p for p in prefixes if "ipv4Prefix" in p]
        v6 = [p for p in prefixes if "ipv6Prefix" in p]
        lists[name] = {
            "purpose": purpose,
            "prefixes": len(prefixes),
            "ipv4": len(v4),
            "ipv6": len(v6),
            "google_creation_time": data.get("creationTime"),
        }
        total += len(prefixes)
        print(f"  {name}: {len(prefixes)} prefixes ({len(v4)} v4, {len(v6)} v6)")

    # Spot check against addresses that are Googlebot by Google's definition.
    googlebot = _fetch("googlebot")
    v4 = [p["ipv4Prefix"] for p in googlebot["prefixes"] if "ipv4Prefix" in p]
    sample = [str(next(ipaddress.ip_network(c).hosts())) for c in v4[:SPOT_CHECK]]
    verified = [ip for ip in sample if verify_ip(ip)]
    print(f"  spot check: {len(verified)}/{len(sample)} verified")

    data = {
        "measured": time.strftime("%Y-%m-%d"),
        "lists": lists,
        "total_prefixes": total,
        "googlebot_prefixes": lists["googlebot"]["prefixes"],
        "googlebot_ipv4": lists["googlebot"]["ipv4"],
        "googlebot_ipv6": lists["googlebot"]["ipv6"],
        "spot_check_size": len(sample),
        "spot_check_verified": len(verified),
        "note": (
            "Counted from Google's own published JSON at "
            f"{BASE}/, which carries its own creationTime — the lists change, "
            "so the date matters. The spot check resolves one address from "
            "each of the first few published Googlebot ranges through Docket's "
            "reverse-then-forward DNS check; those addresses are Googlebot by "
            "Google's definition, so a failure would be our bug. It is a smoke "
            "test against real DNS and NOT a rate: six addresses cannot be "
            "published as a percentage, and the sample is small deliberately "
            "because each check costs two lookups on somebody else's "
            "resolver."),
    }
    OUT.write_text(json.dumps(data, indent=2) + "\n")
    print(f"\ntotal {total} prefixes across {len(lists)} lists")


if __name__ == "__main__":
    main()
