#!/usr/bin/env python3
"""No claim about another company's product may sit unread for long.

    python3 scripts/verify_claim_freshness.py              # the gate (deploy.sh runs it)
    python3 scripts/verify_claim_freshness.py --self-test

WHY. On 19 October 2026 twelve competitor claim sets were re-read in one sitting. Five had last been read in
August or mid-September, and four of those had changed underneath us: JetOctopus had new plans and prices, Semrush's
top plan had gone to a quote, Profound's trial terms had changed, and Sitechecker published crawl totals we said it
did not. verify_competitive_claims.py stops a sentence changing without its date moving. Nothing stopped a date simply
getting old. This does.

THE RULE (CEO, 19 October 2026). Any claim set older than 30 days is re-read on the Monday search-health pass. This
gate lists every set past 30 days on each deploy (WARN), and refuses the deploy once any set passes 45 days (FAIL).
That leaves two Mondays of slack, then a claim nobody re-read stops shipping.

WHAT IT READS. Every competitor's checked date (articles.comparisons.CHECKED_ISO, the dates the comparison pages
print), the home page's claim date (HOME_CLAIM_CHECKED), and each data file whose top-level "read" date is the date a
vendor's page was read (FRESH_DATA below).
"""
from __future__ import annotations

import datetime as dt
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

WARN_DAYS = 30
FAIL_DAYS = 45
#: Data files read off a vendor's own page, by their top-level "read" date.
FRESH_DATA = ("data/ahrefs-credits-2026-09.json", "data/mac-options.json")


def collect() -> dict:
    from articles import comparisons as C  # noqa: E402

    out = {f"comparison: {k}": v for k, v in C.CHECKED_ISO.items()}
    out["home page claims"] = C.HOME_CLAIM_CHECKED
    for rel in FRESH_DATA:
        p = ROOT / rel
        if p.exists():
            read = json.loads(p.read_text()).get("read")
            if read:
                out[f"data: {rel}"] = read
    return out


def judge(dates: dict, today: dt.date) -> tuple:
    """(lines, failed): one line per set past WARN_DAYS, oldest first."""
    rows = []
    for name, iso in dates.items():
        age = (today - dt.date.fromisoformat(iso)).days
        if age > WARN_DAYS:
            rows.append((age, name, iso))
    rows.sort(reverse=True)
    lines = [f"  {'FAIL' if age > FAIL_DAYS else 'WARN'}  {name}: read {iso}, {age} days ago" for age, name, iso in rows]
    return lines, any(age > FAIL_DAYS for age, _, _ in rows)


def self_test() -> int:
    today = dt.date(2026, 10, 19)
    lines, failed = judge({"fresh": "2026-10-10", "old": "2026-09-10"}, today)
    assert not failed and len(lines) == 1 and "WARN  old" in lines[0], lines
    lines, failed = judge({"stale": "2026-08-15"}, today)
    assert failed and "FAIL  stale" in lines[0], lines
    lines, failed = judge({"a": "2026-10-19"}, today)
    assert not failed and not lines
    print("CLAIM FRESHNESS self-test ok")
    return 0


def main() -> int:
    if "--self-test" in sys.argv:
        return self_test()
    dates = collect()
    lines, failed = judge(dates, dt.datetime.now(dt.timezone.utc).date())
    if not lines:
        print(f"CLAIM FRESHNESS ok: {len(dates)} claim sets, every one read within {WARN_DAYS} days")
        return 0
    print(f"CLAIM FRESHNESS: {len(lines)} of {len(dates)} claim sets are older than {WARN_DAYS} days. Re-read them on "
          f"the Monday search-health pass (re-read the vendor's page, then move the date in comparisons.py or the data "
          f"file); past {FAIL_DAYS} days the deploy stops.")
    print("\n".join(lines))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
