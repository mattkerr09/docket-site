#!/usr/bin/env python3
"""Count the test files that exist because Docket said something untrue.

/learn/audit-tool-accuracy/ publishes this as a proportion, and a flattering
number needs its counting rule published beside it. Until now the rule was
published and the arithmetic was not: regressions.json was written by hand,
so it drifted — it claimed 541 tests when the suite had 561, and no gate
could see that because nothing regenerated it.

So the rule is executable here and the dataset records which files it matched.
Anybody can run this against the app repo and get the same answer.

Two deliberate choices:

  * The total comes from `pytest --collect-only -q`, not from counting `def
    test_` with a regex. Parametrised tests are many tests from one function
    and the regex undercounts them by a lot. The number published is the
    number pytest reports.

  * A file counts only when its own prose names a specific thing Docket got
    wrong. Every test file in the repo describes a contract; that is not the
    claim. The phrases below are the ones that only appear when somebody is
    writing down a mistake that actually happened.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

APP = Path("/Users/matthewkerr/Downloads/SEO audit app")
OUT = Path(__file__).resolve().parent.parent / "site" / "_data" / "regressions.json"

# The published rule, as a regex. Each alternative describes a mistake in the
# past tense or names one by its category — not a contract in the present tense.
PAST_MISTAKE = re.compile(
    r"false positive"
    r"|false accusation"
    r"|falsely accus"
    r"|invented"
    r"|fabricat"
    r"|was false"
    r"|the bug\b"
    r"|used to (?:produce|say|report|be|call|claim|fire|accus)"
    r"|would have (?:gone|been|called|reported|shipped|failed|accused)"
    r"|nearly (?:published|shipped|deleted)",
    re.I,
)

RULE = (
    "A test file counts only if it names a specific thing Docket got wrong — "
    "'false positive', 'false accusation', 'invented', 'was false', 'the bug', "
    "'used to produce/say/report/be/call/claim/fire/accuse', 'would have "
    "gone/been/called/reported/shipped/failed/accused', or 'nearly "
    "published/shipped/deleted'. Counting the word 'test' would prove nothing, "
    "and every test file describes a contract — only some record a mistake. "
    "The total is what `pytest --collect-only -q` reports, not a count of `def "
    "test_`: parametrised tests are many tests from one function."
)


def _collected() -> dict[str, int]:
    """Ask pytest for the count per file.

    A regex over `def test_` undercounts parametrised tests badly, so the
    published total is pytest's. This repo's pytest prints only the per-file
    lines and no "N collected" summary, so the total is their sum — and the
    set of files it names is cross-checked against the glob below, because a
    file pytest cannot import contributes 0 tests silently.
    """
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", "--collect-only", "-q"],
        cwd=APP, capture_output=True, text=True, timeout=900,
    )
    if proc.returncode != 0:
        raise SystemExit(
            f"pytest collection failed ({proc.returncode}); refusing to "
            f"publish a total from a broken run.\n{proc.stdout[-2000:]}")
    counts = {m.group(1): int(m.group(2)) for m in
              re.finditer(r"^(\S+\.py): (\d+)$", proc.stdout, re.M)}
    if not counts:
        raise SystemExit(f"no per-file counts in pytest output:\n{proc.stdout[-2000:]}")
    return counts


def main() -> None:
    files = sorted((APP / "tests").glob("test_*.py"))
    if not files:
        raise SystemExit(f"no test files under {APP / 'tests'}")

    matched = [f.name for f in files if PAST_MISTAKE.search(f.read_text())]
    total_files = len(files)

    counts = _collected()
    seen = {Path(p).name for p in counts}
    missing = {f.name for f in files} - seen
    if missing:
        raise SystemExit(
            f"pytest did not collect {sorted(missing)} — a file it cannot "
            f"import contributes 0 tests without saying so. Fix that before "
            f"publishing a total.")

    data = {
        "test_files": total_files,
        "files_pinning_a_past_mistake": len(matched),
        "pct": round(100 * len(matched) / total_files, 1),
        "tests_total": sum(counts.values()),
        "rule": RULE,
        "files": matched,
        "note": (
            "The rule was widened on 2026-08-07, when this collector was "
            "written and the figure stopped being maintained by hand. The "
            "earlier rule matched 12 of the same 30 files (40.0%); the two it "
            "missed were test_rating_visibility.py, which exists because Docket "
            "told a real ecommerce site its rich results were at risk when "
            "they were not, and test_knowledge_consistency.py. Both plainly "
            "record mistakes and the earlier phrasing simply did not name the "
            "words they used. Recorded here because the rule changed in the "
            "same edit as the count did, and a percentage that rises for two "
            "different reasons at once should say so."),
    }
    OUT.write_text(json.dumps(data, indent=2) + "\n")
    print(f"{len(matched)}/{total_files} files ({data['pct']}%), "
          f"{data['tests_total']} tests")
    for name in matched:
        print(f"  {name}")


if __name__ == "__main__":
    main()
