#!/usr/bin/env python3
"""Every page that sells scheduled monitoring must say what it does not do.

Docket's scheduler is a `daemon=True` thread inside the sidecar process
(`scheduler.py:50`). Quit the app and the thread dies with it; there is no
launchd job, no cron entry, nothing that runs when Docket is closed. A missed
run is not skipped — `Site.is_due()` compares now against `last_checked +
cadence`, so an overdue site fires on the next launch — but it does not fire
while the machine sits there with the app shut.

That is a perfectly reasonable design for a local tool. It stops being
reasonable the moment the feature is sold without it.

Measured on the live site, 2026-08-11: three surfaces advertised scheduled
re-audits with no caveat at all —

    /              "Re-audits on a cadence and tells you what changed."
    /for/agencies/ "turns scheduled re-audits into a retainer"
    /vs/screaming-frog-alternative/
                   Scheduled re-audits | Docket: "Yes" | theirs: "paid tier"

— while `/vs/ahrefs-site-audit-alternative/` had said the honest thing all
along: "Because Docket runs locally, closing the laptop stops a scheduled
audit." Two pages disclosed it and three sold past it, and the one selling
hardest was the agencies page, where the phrase was *retainer* — a monthly
promise to a paying client that the product cannot keep unattended.

The comparison row was the worst of the three in a subtler way. "Yes" against
"Scheduling in the paid tier" reads as Docket winning the row. On this
particular axis Docket is the weaker product, and a comparison table that
flatters itself on a competitor's genuine strength is the kind of thing that
makes a reader distrust every other row on the page.

So: any page that mentions the feature must carry the limit within the same
page. This is a coarse test — same page, not same sentence — because prose
moves around and a stricter proximity rule would fail on ordinary editing. It
catches the failure that actually happened: the claim shipping alone.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

SITE = Path(__file__).resolve().parent.parent / "site"

#: How many pages sell this feature today. A floor, not a count: adding a page
#: that mentions monitoring is ordinary and must not fail the build, but the
#: number dropping means the pattern below stopped matching something.
FLOOR = 4

#: The feature being sold. Matched on the rendered text, not the source, so a
#: claim assembled from a template is still caught.
SELLS = re.compile(
    r"scheduled re-audits?|schedul\w+ monitoring|re-audits? (?:it )?on a (?:schedule|cadence)"
    r"|monitoring turns an audit",
    re.I,
)

#: Any one of these counts as having said the limit out loud. Several phrasings
#: because the pages are written by hand and should stay that way — a gate that
#: demands one exact sentence turns into boilerplate nobody reads.
DISCLOSES = re.compile(
    r"while (?:the app|docket) is open"
    r"|while it is open"
    r"|closing the laptop stops"
    r"|quitting it stops"
    r"|quit docket"
    r"|not a background daemon"
    r"|only while docket"
    r"|while the app is open",
    re.I,
)


def _text(html: str) -> str:
    html = re.sub(r"(?is)<(script|style).*?</\1>", " ", html)
    return " ".join(re.sub(r"<[^>]+>", " ", html).split())


def main() -> int:
    pages = sorted(SITE.rglob("index.html")) + [SITE / "404.html"]
    selling, offenders = [], []

    for path in pages:
        if not path.is_file():
            continue
        text = _text(path.read_text(encoding="utf-8", errors="replace"))
        if not SELLS.search(text):
            continue
        rel = "/" + str(path.relative_to(SITE)).replace("index.html", "")
        selling.append(rel)
        if not DISCLOSES.search(text):
            claim = SELLS.search(text)
            offenders.append((rel, text[max(0, claim.start() - 60):claim.end() + 90]))

    if len(selling) < FLOOR:
        # Breaking one alternative in SELLS during a self-test left the gate
        # matching two pages instead of four — and passing, because a zero
        # guard only fires at zero. Partial blindness looked exactly like
        # success. The floor is what makes a shrinking pattern visible.
        print(f"MONITORING FAIL — only {len(selling)} page(s) matched as selling "
              f"scheduled monitoring; at least {FLOOR} do. The pattern has "
              f"stopped seeing pages it used to see, so a clean result from it "
              f"means nothing.\n  matched: {selling}", file=sys.stderr)
        return 1

    if offenders:
        print(f"MONITORING FAIL — {len(offenders)} page(s) sell scheduled "
              f"monitoring without saying it stops when the app quits:",
              file=sys.stderr)
        for rel, snippet in offenders:
            print(f"  {rel}\n      …{snippet}…", file=sys.stderr)
        print("\n  The scheduler is a daemon thread in the sidecar "
              "(scheduler.py:50). Say so in the same breath as the feature.",
              file=sys.stderr)
        return 1

    print(f"MONITORING ok — {len(selling)} page(s) sell scheduled monitoring, "
          f"all state that it runs only while the app is open")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
