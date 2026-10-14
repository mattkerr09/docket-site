#!/usr/bin/env python3
"""The recordings on the front page were made by a build that is still current.

    python3 scripts/verify_recordings_fresh.py [--self-test]

WHY. The home page showed "136 pages, 112 seconds" (a recording made by 1.3.94)
and "140 pages crawled in 97 seconds" (1.3.95) while the shipping build audited
152 pages in about 54 seconds: two releases that halved the crawl and added a
first look at eight seconds, and a front page still describing the product from
three weeks earlier (10-14 growth research). Every other gate keeps the site in
step with the app: the version gate checks version strings, `verify_derived_data`
keeps datasets in step with the repo, `verify_numbers` refuses typed numbers.
None of them compares a RECORDING with the build it claims to show, because a
recording is a measurement of one run and is internally consistent forever.

WHAT IT REFUSES. A recording (`data/hero-recording.json`, `data/demo-recording.json`)
whose `engine` is more than MAX_RELEASES patch releases behind the current build
(`data/download.json`), on another minor or major version, or whose `recorded` date
is more than MAX_DAYS days ago. It names the recorder to run:
`docket-app/scripts/record_hero.mjs` and `record_demo.mjs`, each with `--site`.

Both limits are deliberate. Eight releases is about a week at the pace of the
past two, so a recording survives a normal week and not a month; 21 days stops a
quiet period from making an old recording look current. A recording made by an
engine that predates a change the page now describes is the case this exists for.

--self-test plants a stale and a fresh pair of recordings and requires the gate
to refuse the first and pass the second, then requires the real data to pass.
"""
from __future__ import annotations

import datetime as dt
import json
import pathlib
import re
import sys

DATA = pathlib.Path(__file__).resolve().parent.parent / "data"
RECORDINGS = ("hero-recording.json", "demo-recording.json")
MAX_RELEASES = 8
MAX_DAYS = 21


def _version(text: str):
    m = re.fullmatch(r"(\d+)\.(\d+)\.(\d+)", str(text).strip())
    return tuple(int(x) for x in m.groups()) if m else None


def problems(recordings: dict, current: str, today: dt.date) -> list:
    """What is wrong with {name: {engine, recorded}} against the current version."""
    out = []
    now = _version(current)
    if now is None:
        return [f"the current version {current!r} is not major.minor.patch"]
    for name, rec in sorted(recordings.items()):
        engine, recorded = rec.get("engine"), rec.get("recorded")
        then = _version(engine)
        if then is None:
            out.append(f"{name}: engine {engine!r} is not a version")
            continue
        if then[:2] != now[:2]:
            out.append(f"{name}: recorded on {engine}, the build is {current}: another minor version")
        elif now[2] - then[2] > MAX_RELEASES:
            out.append(f"{name}: recorded on {engine}, {now[2] - then[2]} releases behind {current} "
                       f"(limit {MAX_RELEASES})")
        try:
            age = (today - dt.date.fromisoformat(str(recorded))).days
        except ValueError:
            out.append(f"{name}: recorded {recorded!r} is not a date")
            continue
        if age > MAX_DAYS:
            out.append(f"{name}: recorded {age} days ago (limit {MAX_DAYS})")
        elif age < 0:
            out.append(f"{name}: recorded {recorded}, which is in the future")
    return out


def load() -> tuple:
    recs = {n: json.loads((DATA / n).read_text(encoding="utf-8")) for n in RECORDINGS}
    current = json.loads((DATA / "download.json").read_text(encoding="utf-8"))["version"]
    return recs, current


def self_test() -> int:
    today = dt.date(2026, 10, 14)
    fresh = {"hero.json": {"engine": "1.3.109", "recorded": "2026-10-14"},
             "demo.json": {"engine": "1.3.103", "recorded": "2026-10-01"}}
    stale = {"hero.json": {"engine": "1.3.94", "recorded": "2026-09-25"},
             "demo.json": {"engine": "1.3.109", "recorded": "2026-09-01"},
             "old_minor.json": {"engine": "1.2.109", "recorded": "2026-10-14"}}
    if problems(fresh, "1.3.109", today):
        print("FAIL  self-test: a fresh pair was refused:", problems(fresh, "1.3.109", today))
        return 1
    found = problems(stale, "1.3.109", today)
    if len(found) < 3 or not any("releases behind" in f for f in found) or not any("days ago" in f for f in found):
        print("FAIL  self-test: a stale pair was not refused for each reason:", found)
        return 1
    if not problems({"x": {"engine": "banana", "recorded": "yesterday"}}, "1.3.109", today):
        print("FAIL  self-test: unreadable metadata passed")
        return 1
    return 0


def main() -> int:
    if "--self-test" in sys.argv and self_test():
        return 1
    try:
        recs, current = load()
    except (OSError, KeyError, ValueError) as exc:
        print(f"FAIL  the recordings or the current version could not be read: {exc}")
        return 1
    found = problems(recs, current, dt.date.today())
    if found:
        print("FAIL  a front-page recording is older than the build it claims to show:")
        for line in found:
            print("   ", line)
        print("    Re-record: start a dev engine, then in docket-app/ui run")
        print("      node ../scripts/record_hero.mjs OUT --site ../../docket-site --api-port 8811")
        print("      node ../scripts/record_demo.mjs OUT --site ../../docket-site --api-port 8811")
        return 1
    ages = ", ".join(f"{n.split('-')[0]} {r['engine']} on {r['recorded']}" for n, r in sorted(recs.items()))
    print(f"  ok: recordings fresh against {current} ({ages})" + (" (self-test passed)" if "--self-test" in sys.argv else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
