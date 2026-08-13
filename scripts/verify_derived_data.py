#!/usr/bin/env python3
"""Refuse to ship a dataset that is a function of the app repo and out of date.

    python3 scripts/verify_derived_data.py [--fix]

`verify_numbers.py` already refuses to ship a *typed* number: every published
figure has to interpolate from a dataset rather than sit in prose. That gate
does its job and has a blind spot it does not state — a number can be perfectly
derived and still be wrong, because the dataset it derives from was built once
and never rebuilt. Prose and data agree with each other; both are stale; nothing
disagrees, so nothing fails.

Measured 2026-08-13. /learn/audit-tool-accuracy/ published:

    "17 of the 35 test files exist for no other reason"   and "811 tests"

Running `collect_regressions.py` against the app repo, unchanged, gave **74 of
145** and **1781 tests**. The figure was six days old and understated the work
by more than half. `collect_regressions.py` exists *because this already
happened once* — its own docstring records the count drifting from 541 to 561 —
and it drifted again, for the reason it was written to prevent: nothing ran it.

**Only datasets that are a pure function of the repo belong here.** Rerunning
one is a correction: same input, same answer, and any difference is drift.

`brand.json` deliberately does not qualify, and the distinction is the whole
design. It measures sixteen real third-party sites on a stated date. Rerunning
it produced different numbers on 2026-08-13 — `median_colours` 79 to 69,
`with_colour_drift` 13 to 12 — not because the old figures were wrong but
because those sites changed. That is a new measurement, and it needs a fresh
date, a look at the prose that cites it, and sixteen requests to people who
never asked to be measured twice. A deploy gate must not do any of that
silently, so measurement datasets stay out and stay dated.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

#: (collector, the file it writes). Add a row only when rerunning the collector
#: is a correction rather than a fresh measurement — see the module docstring.
DERIVED = [
    ("collect_regressions.py", "site/_data/regressions.json"),
]

#: Checks run from the *app* repo, which owns the fact. `--check` reports
#: staleness without writing, which is what a gate wants.
#:
#: `export_checks_csv.py --check` has existed since the catalogue stopped being
#: hand-maintained, and its own docstring calls it "the form worth wiring into
#: a release". It was wired nowhere. When it was finally run on 2026-08-13 it
#: exited 1 — not because the catalogue was stale but because its default
#: output path was `/tmp/scout-site/...`, where the site lived before the
#: rename. The guard on the most prominent number on this site had been aiming
#: at a directory that no longer exists.
APP_CHECKS = [
    ("export_checks_csv.py --check", ["scripts/export_checks_csv.py", "--check"]),
]


def main() -> int:
    fix = "--fix" in sys.argv
    stale = []

    for collector, target in DERIVED:
        path = ROOT / target
        before = path.read_bytes() if path.exists() else b""
        result = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / collector)],
            capture_output=True, text=True, cwd=str(ROOT))
        if result.returncode != 0:
            print(f"FAIL  {collector} exited {result.returncode}")
            print((result.stderr or result.stdout)[-800:])
            return 1
        after = path.read_bytes()
        if after != before:
            stale.append((collector, target))
            if not fix:
                # Put it back. A gate that edits the tree it is checking turns
                # "you have not run the collector" into "you have uncommitted
                # changes", which is a different and more confusing failure.
                path.write_bytes(before)

    import app_path
    app = app_path.find()
    for label, argv in APP_CHECKS:
        result = subprocess.run([sys.executable, *[str(app / a) if a.endswith(".py") else a
                                                   for a in argv]],
                                capture_output=True, text=True, cwd=str(app))
        line = (result.stdout or result.stderr).strip().splitlines()
        print("  " + (line[0] if line else label))
        if result.returncode != 0:
            print(f"\nFAIL  {label} — the published catalogue does not describe "
                  "the engine this would ship beside.")
            return 1

    if not stale:
        print(f"derived data ok — {len(DERIVED)} dataset(s) and "
              f"{len(APP_CHECKS)} catalogue check(s) match the app repo")
        return 0

    for collector, target in stale:
        print(f"STALE  {target} — regenerate it:  python3 scripts/{collector}")
    if fix:
        print("  (--fix given: the files above have been regenerated, commit them)")
        return 0
    print("\nThis is the shape of bug verify_numbers.py cannot see: the prose and")
    print("the dataset agree with each other and both are out of date.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
