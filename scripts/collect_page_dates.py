#!/usr/bin/env python3
"""When each built page first appeared, so `datePublished` is not a default.

    python3 scripts/collect_page_dates.py

**The bug this exists for.** `render()` carried `published: str = "2026-08-06"`,
so any article that did not pass `published=` asserted a publication date nobody
chose. Measured 2026-09-09: **38 of 53 render() calls relied on that default**
and 41 built pages published it. 2026-08-06 is the day this REPOSITORY was
created — `bffff490 Initial commit` at 15:22, with `site/` first committed 31
minutes later. It is the repo's birthday wearing a page's publication date.

At least one is plainly false: `/how-to/audit-your-site-from-an-ai-assistant/`
published 2026-08-06 and was written on 2026-09-08, in `a49c106d`, whose subject
line is that page's own title.

**The derivation, and how it was validated.** The date is the first commit that
ADDED the page's built `index.html`. Checked against the 14 pages whose source
passes an explicit `published=` — the only dates a human actually chose:

    12 agree exactly
     2 are one day later   (outrank-a-bigger-competitor, refunds)
     0 are earlier

The two are the author dating a page the day it was written and committing it
the next morning. Nothing derives earlier than a human's own date, which is the
direction that would have meant the derivation was wrong.

⚠️ **A HAND-SUPPLIED DATE ALWAYS WINS.** This dataset is consulted only where
nothing was supplied. Deriving over the top of an explicit date would move those
two pages a day later than their author put them, which is the one change here
that could make a true date false.

⚠️ **`--follow` IS WRONG FOR THIS AND WAS TRIED FIRST.** With `--follow`, every
one of the 59 pages reported 2026-08-06 — rename detection walks back through
the bulk commit that created `site/` and lands on the repo's first day. The
agreement looked total and was an artefact: the derivation had simply
reproduced the default. Without `--follow` the dates spread across eight
distinct days and the validation above becomes possible at all.

**A page not yet committed has no first-add commit**, so it takes today. That is
the same rule `verify_competitive_claims._facts_last_edited` uses for an
uncommitted edit — "its day is today, which is the case a deploy is most likely
to be publishing" — and it is right here for the same reason: a page being built
for the first time is being published today.
"""
from __future__ import annotations

import datetime as _dt
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "site"
OUT = ROOT / "data" / "page-dates.json"


def first_added(path: Path) -> str | None:
    """The day this exact path first appeared, or None if never committed."""
    proc = subprocess.run(
        ["git", "-C", str(ROOT), "log", "--diff-filter=A", "--format=%cI",
         "--", str(path.relative_to(ROOT))],
        capture_output=True, text=True)
    lines = proc.stdout.strip().splitlines()
    return lines[-1][:10] if lines else None


def collect() -> dict:
    today = _dt.date.today().isoformat()
    dates, uncommitted = {}, []
    for page in sorted(SITE.rglob("index.html")):
        key = page.parent.relative_to(SITE).as_posix() or "."
        day = first_added(page)
        if day is None:
            day = today
            uncommitted.append(key)
        dates[key] = day
    return {"dates": dates, "uncommitted": uncommitted, "compiled": today}


def main() -> int:
    if not SITE.exists():
        print("PAGE DATES: no site/ directory — run scripts/build.py first.")
        print("That is not a pass.")
        return 1
    data = collect()
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")
    spread = sorted(set(data["dates"].values()))
    print(f"PAGE DATES ok — {len(data['dates'])} page(s) across "
          f"{len(spread)} distinct day(s): {spread[0]} … {spread[-1]}")
    if data["uncommitted"]:
        print(f"  {len(data['uncommitted'])} not yet committed, dated today: "
              + ", ".join(data["uncommitted"][:5]))
    print(f"  written: {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
