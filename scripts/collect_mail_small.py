#!/usr/bin/env python3
"""The small-business half of the dead-contact-address survey.

/learn/dead-contact-address/ measured the Tranco top 1,500 and found no dead
address among the 80 sites that still publish one — then said, in print, that
the population most exposed to this is the one a popularity-ranked list cannot
reach. Small sites are far more likely to publish an address and far less
likely to have anyone watching DNS.

This closes that stated gap rather than inventing a new claim, which needs a
sampling frame a sceptic would accept. The frame, in one sentence:

    Every element tagged `shop` in OpenStreetMap inside the boundaries of ten
    named UK cities that also carries a `website` tag.

Why that frame and not another:

  * It is not ranked by popularity, traffic or size — which is the entire
    property the Tranco sample lacked and this survey needs.
  * Nothing here selects individual businesses. The whole frame is used, so
    there is no slice to justify.
  * It is reproducible by anyone: the Overpass query is printed below and the
    data is ODbL-licensed.

What it is not, said plainly because the article has to say it:

  * OSM coverage is uneven. A business nobody mapped is not in the frame, and
    who gets mapped is not random.
  * A `website` tag is sometimes a Facebook page or a chain's national site
    rather than the shop's own domain. Those are excluded at analysis time,
    but the exclusion is a judgement.
  * Ten UK cities is not the world.

Usage:  python3 scripts/collect_mail_small.py --date YYYY-MM-DD
"""
from __future__ import annotations

import sys as _sys
from pathlib import Path as _Path
_sys.path.insert(0, str(_Path(__file__).resolve().parent))
import app_path  # noqa: E402

import argparse
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(app_path.backend()))

from seo_engine import mailcheck as M  # noqa: E402

CITIES = ("Bristol|Sheffield|Leeds|Nottingham|Norwich|Brighton and Hove|"
          "Cardiff|Edinburgh|Manchester|Liverpool")

OVERPASS = "https://overpass-api.de/api/interpreter"
#: Overpass answers 406 to a browser user-agent. Identifying the tool and a
#: contact is what its usage policy asks for anyway — a shared free API is
#: owed an honest introduction.
OVERPASS_UA = ("docketseo.app survey (github.com/mattkerr09/docket-site) "
               "one query, contact via the repository issue tracker")
QUERY = (
    '[out:json][timeout:180];'
    f'(area["name"~"^({CITIES})$"]["admin_level"~"^(6|8)$"];)->.a;'
    'nwr(area.a)["website"]["shop"];'
    'out tags;'
)

MAILTO = re.compile(rb'href=["\']mailto:([^"\'?>]+)', re.I)
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 "
      "(KHTML, like Gecko) Version/17.0 Safari/605.1.15 Docket/1.0")
MAX_BYTES = 700_000

#: A `website` tag pointing at somebody else's platform is not the shop's own
#: domain, and its MX is not the shop owner's business.
PLATFORMS = (
    "facebook.com", "instagram.com", "twitter.com", "x.com", "linktr.ee",
    "google.com", "sites.google.com", "wixsite.com", "business.site",
    "tripadvisor", "just-eat", "deliveroo", "ubereats", "etsy.com",
    "linkedin.com", "youtube.com", "tiktok.com",
)


#: The frame is cached so Overpass is asked once. It is a free shared service
#: run on donated capacity; re-fetching an unchanged frame on every run is the
#: kind of thing that gets a tool blocked, and deservedly. The cache also makes
#: the survey re-runnable by anyone without a second query.
FRAME_CACHE = ROOT / "data" / "mail-small-frame.json"


def frame(refresh: bool = False) -> list[dict]:
    """The sampling frame, fetched once from Overpass and then cached."""
    if FRAME_CACHE.exists() and not refresh:
        return json.loads(FRAME_CACHE.read_text())
    req = urllib.request.Request(
        OVERPASS, data=urllib.parse.urlencode({"data": QUERY}).encode(),
        headers={"User-Agent": OVERPASS_UA, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=240) as resp:
        payload = json.loads(resp.read())

    # How many mapped shop locations share each domain. One location is a
    # good proxy for an independent business and several for a chain — derived
    # from the data rather than from an opinion about which brands are chains,
    # which would be a selection nobody could check.
    from collections import Counter as _Counter
    locations: _Counter = _Counter()
    seen, out = set(), []
    for element in payload.get("elements", []):
        tags = element.get("tags") or {}
        site = (tags.get("website") or "").strip()
        if not site:
            continue
        if not site.lower().startswith(("http://", "https://")):
            site = "https://" + site
        host = (urllib.parse.urlsplit(site).hostname or "").lower()
        if not host or any(p in host for p in PLATFORMS):
            continue
        bare = host[4:] if host.startswith("www.") else host
        locations[bare] += 1
        # One entry per domain: a chain with nine mapped branches is one
        # website, and counting it nine times would weight the result by how
        # many shops somebody bothered to map.
        if bare in seen:
            continue
        seen.add(bare)
        out.append({"host": host, "domain": bare, "shop": tags.get("shop", ""),
                    "osm": f"{element.get('type')}/{element.get('id')}"})
    for record in out:
        record["locations"] = locations[record["domain"]]
    out.sort(key=lambda r: r["osm"])
    FRAME_CACHE.write_text(json.dumps(out, indent=1) + "\n")
    return out


def fetch(host: str, timeout: float = 12.0):
    for scheme in ("https://", "http://"):
        req = urllib.request.Request(f"{scheme}{host}/", headers={"User-Agent": UA})
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                body = resp.read(MAX_BYTES)
                found = {a.decode("ascii", "replace").strip().lower()
                         for a in MAILTO.findall(body)}
                return resp.status, sorted(found)
        except urllib.error.HTTPError as exc:
            return exc.code, []
        except Exception:  # noqa: BLE001 — unreachable is data
            continue
    return 0, []


def survey(record: dict) -> dict:
    status, addresses = fetch(record["host"])
    row = dict(record, status=status, addresses=addresses[:4], domains={})
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

    for domain in domains[:2]:
        verdict = M.check_domain(domain, timeout=4.0)
        row["domains"][domain] = {
            "accepts": verdict.accepts_mail, "conclusive": verdict.conclusive,
            "static_host": verdict.static_host, "reason": verdict.reason,
        }
    return row


def _shape(reason: str) -> str:
    """The failure mode, without the domain that suffered it."""
    if "none of them resolves" in reason:
        return "publishes an MX record naming a host that does not resolve"
    if "no address record" in reason:
        return "the domain in the address has no MX and no address record"
    if "static files" in reason:
        return "no MX, and the address record is a static host"
    return "no MX record"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", required=True)
    ap.add_argument("--workers", type=int, default=20)
    ap.add_argument("--out", default="data/mail-small-2026-08.json")
    ap.add_argument("--refresh-frame", action="store_true",
                    help="re-query Overpass instead of using the cached frame")
    args = ap.parse_args()

    print("fetching the frame from Overpass…")
    records = frame(refresh=args.refresh_frame)
    print(f"frame: {len(records)} distinct domains")

    began = time.time()
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        rows = list(pool.map(survey, records))

    answered = [r for r in rows if r["status"] == 200]
    publishing = [r for r in answered if r["domains"]]

    def verdicts(row):
        return list(row["domains"].values())

    dead = [r for r in publishing
            if any(v["accepts"] is False and v["conclusive"] for v in verdicts(r))]
    probe_only = [r for r in publishing if r not in dead
                  and any(v["accepts"] is False for v in verdicts(r))]
    undetermined = [r for r in publishing
                    if all(v["accepts"] is None for v in verdicts(r))]
    ok = [r for r in publishing if any(v["accepts"] is True for v in verdicts(r))]

    payload = {
        "measured": args.date,
        "frame": ("Every element tagged shop in OpenStreetMap inside the "
                  "boundaries of ten named UK cities that also carries a "
                  "website tag, deduplicated to one entry per domain"),
        "cities": CITIES.split("|"),
        "overpass_query": QUERY,
        "source": "OpenStreetMap, ODbL",
        "method": (
            "One homepage request per domain. An address counts as published "
            "only when it appears in a mailto: href. Consumer providers, RFC "
            "2606 reserved names and websites pointing at a social or "
            "marketplace platform are excluded. A domain counts as dead only "
            "where DNS alone establishes it — no MX plus an address record on "
            "a static host that does not run SMTP, or no MX and no address "
            "record. Verdicts resting on a port-25 probe are reported "
            "separately because outbound 25 is widely blocked."
        ),
        "frame_size": len(records),
        "answered": len(answered),
        "publishing_mailto": len(publishing),
        "accepts_mail": len(ok),
        "dead_conclusive": len(dead),
        "dead_probe_only": len(probe_only),
        "undetermined": len(undetermined),
        "duration_s": round(time.time() - began, 1),
        "single_location": {
            "publishing": sum(1 for r in publishing if r["locations"] == 1),
            "dead": sum(1 for r in dead if r["locations"] == 1),
            "accepts": sum(1 for r in ok if r["locations"] == 1),
        },
        # De-identified on purpose. These are real corner shops and locksmiths
        # that never asked to be audited, and "this named business cannot
        # receive email" is not a fact this site has any business publishing
        # about them. The aggregate is the finding; the roll of names is not.
        #
        # The frame is published separately and is just OpenStreetMap data,
        # so the survey stays reproducible by anyone willing to re-run it.
        "dead_shapes": sorted(
            {(r["shop"], _shape(v["reason"]))
             for r in dead for v in r["domains"].values()
             if v["accepts"] is False and v["conclusive"]}
        ),
    }
    (ROOT / args.out).write_text(json.dumps(payload, indent=2) + "\n")

    print(f"frame {payload['frame_size']}, answered {payload['answered']}, "
          f"publishing a mailto {payload['publishing_mailto']}")
    print(f"  accepts mail      {payload['accepts_mail']}")
    print(f"  dead (DNS alone)  {payload['dead_conclusive']}")
    print(f"  dead (probe only) {payload['dead_probe_only']}")
    print(f"  undetermined      {payload['undetermined']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
