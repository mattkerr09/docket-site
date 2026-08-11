#!/usr/bin/env python3
"""Refuse to publish an audit of a business that never asked for one.

On 2026-08-11 this site was serving, at `/learn/ai-substitution/`:

    Run against **zingermansdeli.com**, a delicatessen in Ann Arbor, it
    assessed 33 pages and found **0% fully substitutable** …

and, at `/_data/exposure-zingermansdeli.json`, HTTP 200, the whole thing: the
domain, and 33 page URLs with their titles and per-page risk scores. The same
file was readable from the public repo. Nobody asked us to do that.

The result happened to be flattering. That is not a defence — it was flattering
*this* week, the scorer changes, and the consent was never there either way.

**Why a gate and not a note.** "Do not name private parties who never asked to
be audited" was a rule in a prompt, which means it held exactly as long as
someone remembered it. Every other rule on this project that survived became
something that fails a build. This one is now one of those.

What it checks, in the built site and the data it ships:

1. No `_data/exposure-*.json` carries a real hostname or per-page URLs. The
   article needs `pages_assessed`, `substitutable_pct` and `defence_counts`;
   it never needed the URLs, and those are what identify.
2. The one exception is our own site, by exact allowlist, because naming
   ourselves is consent by definition.

**What this deliberately does not do.** It cannot tell a named *competitor*
from a named *audit subject*, and it does not try. This site names competitors
constantly and should — those pages quote published prices and documentation,
which is fair comment about a product on sale, not a measurement taken of
someone's website without asking. Rather than guess at intent from prose, this
checks the narrow, mechanical thing that actually went wrong: audit *data*
about a third party being published. A future page that names a business in
prose while running Docket against it would pass this and still be wrong, and
that is worth knowing about the gate rather than assuming coverage it lacks.

It also cannot help with git history. The identifying data is in this repo's
past commits, and removing it there is a rewrite of published history — a
decision for the repo's owner, not for a build gate.
"""
from __future__ import annotations

import json
import pathlib
import re
import sys

SITE = pathlib.Path(__file__).resolve().parent.parent / "site"

#: Hosts we may publish measurements of, because they are ours.
#:
#: `scoutseo.app` is here because it is this same site under its pre-rename
#: domain. The 2026-08-07 exposure run recorded page URLs on it, and the honest
#: options were to rewrite those URLs or to state the fact. Rewriting a
#: measurement to look tidier is how a dataset stops being evidence, so the
#: data is untouched and the allowlist carries the explanation.
OURS = {"docketseo.app", "www.docketseo.app", "scoutseo.app", "www.scoutseo.app"}

#: Keys that carry a per-page breakdown. Aggregates are fine; these are not.
PER_PAGE_KEYS = ("pages", "urls", "page_urls", "worst", "most_exposed")

HOSTNAME = re.compile(r"https?://([a-z0-9.-]+)", re.I)


def fail(lines: list[str]) -> None:
    print(f"THIRD PARTY: {len(lines)} problem(s) — audit data about a business "
          f"that did not ask for it")
    for line in lines:
        print(f"  {line}")
    sys.exit(1)


def main() -> int:
    data_dir = SITE / "_data"
    exposures = sorted(data_dir.glob("exposure-*.json")) if data_dir.is_dir() else []
    problems: list[str] = []

    for path in exposures:
        try:
            payload = json.loads(path.read_text())
        except (OSError, json.JSONDecodeError) as exc:
            problems.append(f"{path.name}: unreadable ({exc})")
            continue

        blob = json.dumps(payload)
        hosts = {h.lower().lstrip("www.") if h.lower().startswith("www.") else h.lower()
                 for h in HOSTNAME.findall(blob)}
        outsiders = {h for h in hosts
                     if h not in {o.lstrip("www.") for o in OURS} and h not in OURS}
        if outsiders:
            problems.append(
                f"{path.name}: names {sorted(outsiders)[:3]} — a site we measured "
                f"and do not own")

        for key in PER_PAGE_KEYS:
            value = payload.get(key)
            if isinstance(value, list) and value:
                owned = str(payload.get("site", "")).lower()
                if not any(o in owned for o in OURS):
                    problems.append(
                        f"{path.name}: carries {len(value)} per-page entries under "
                        f"{key!r} for a site we do not own — the article uses the "
                        f"aggregates, and the URLs are what identify the business")

    if problems:
        fail(problems)

    # The control. If the glob stops matching — files renamed, directory moved —
    # every loop above runs zero times and this file reports success while
    # checking nothing. That is the failure this project keeps meeting.
    if not exposures:
        print("THIRD PARTY: no exposure-*.json found at all. Either they moved, or "
              "this gate is watching an empty directory and cannot tell the "
              "difference. Point it at the right place before trusting it.")
        return 1

    owned = sum(1 for p in exposures
                if any(o in json.loads(p.read_text()).get("site", "").lower()
                       for o in OURS))
    print(f"THIRD PARTY ok — {len(exposures)} exposure dataset(s), {owned} ours, "
          f"none naming a site we measured without asking")
    return 0


if __name__ == "__main__":
    sys.exit(main())
