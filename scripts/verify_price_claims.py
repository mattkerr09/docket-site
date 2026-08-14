#!/usr/bin/env python3
"""No page may promise a price trigger that has already passed.

    python3 scripts/verify_price_claims.py

**What went wrong.** The download page carried a hardcoded paragraph:

    "v1.1.0 is free. The beta downloads without payment and keeps working;
     the $79 applies from v1.0."

Both halves were written when `BETA_FREE` was True and the release was 0.1.x.
Flipping that flag to False and shipping v1.0 left the paragraph in place, so
the live site told a reader the price applies from v1.0 while offering v1.1.0
for nothing. One fact in two places, and only the constant was updated.

That is the site's own subject matter. `verify_numbers.py` refuses a number
that was typed rather than derived; this refuses a *claim* that has outlived
the state it described. A site selling an instrument for catching stale and
contradictory copy cannot be the counterexample on its pricing page.

**What is checked, on the built HTML rather than the generator**, because the
built HTML is what a reader gets:

  1. No page says a price "applies from vX" when the current release is already
     at or past vX. That sentence is only true ahead of the trigger.
  2. No page calls the current release free while `BETA_FREE` is False without
     also saying what is true — that there is no activation step yet. Silence
     there reads as a pricing page that charges nothing by accident.
  3. If `BETA_FREE` is True, the beta wording must actually appear. A flag
     nobody surfaces is a flag that will be wrong later and never noticed.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "site"
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "articles"))

import render  # noqa: E402

#: "applies from v1.0", "applies from version 1.0" — the trigger phrasing.
_TRIGGER = re.compile(r"applies from\s+v(?:ersion\s*)?(\d+)\.(\d+)", re.I)


def _release_tuple() -> tuple:
    parts = re.findall(r"\d+", render.RELEASE)
    return tuple(int(p) for p in parts[:2]) or (0, 0)


def _text(path: Path) -> str:
    html = path.read_text(encoding="utf-8", errors="replace")
    html = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", " ", html)
    return " ".join(re.sub(r"<[^>]+>", " ", html).split())


def main() -> int:
    pages = sorted(SITE.rglob("*.html"))
    if not pages:
        print("PRICE FAIL — no built pages found; run the build first")
        return 1

    current = _release_tuple()
    problems = []
    beta_wording_seen = False
    free_claims = []

    for path in pages:
        text = _text(path)
        rel = path.relative_to(SITE)

        for match in _TRIGGER.finditer(text):
            trigger = (int(match.group(1)), int(match.group(2)))
            if current >= trigger:
                problems.append(
                    f"{rel}: says the price \"{match.group(0)}\" while the current "
                    f"release is {render.RELEASE} — the trigger has already passed, "
                    f"so the sentence is false to anyone reading it today")

        if re.search(rf"{re.escape(render.RELEASE)}\s+is free", text, re.I):
            beta_wording_seen = True
            free_claims.append(rel)

    if not render.BETA_FREE:
        for rel in free_claims:
            problems.append(
                f"{rel}: calls {render.RELEASE} free while BETA_FREE is False. "
                f"Say what is actually true — that the build has no activation "
                f"step yet — rather than describing a beta that ended")
    elif not beta_wording_seen:
        problems.append(
            "BETA_FREE is True and no page says so. A reader is being charged "
            "in the copy for something that downloads for nothing")

    if problems:
        print("PRICE CLAIMS FAIL")
        for problem in problems:
            print(f"  - {problem}")
        return 1

    print(f"PRICE ok — {len(pages)} pages, no stale trigger, "
          f"release {render.RELEASE}, BETA_FREE={render.BETA_FREE}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
