#!/usr/bin/env python3
"""Is the tracker's state and its disclosure the same story?

`render.py` has demanded this test in a comment for some time and nobody wrote
it: *"Dark is a claim that has to be tested in both directions, not assumed:
assert that no fbq call is emitted while the id is empty, AND that planting an
id does emit one. A test that only checks the empty case cannot fail."*

That was right, and the missing half is the dangerous one. A gate that only
proves the dark case passes forever — including on the day someone sets the id
and forgets the privacy policy.

WHAT IT CHECKS, in whichever direction the build is actually in

  DARK (META_PIXEL_ID empty)
    no page may contain fbq, connect.facebook.net, or a pixel id
    the privacy policy must NOT describe a tracker that is not there

  LIVE (META_PIXEL_ID set)
    the snippet and the id must actually appear in the built pages
    and the disclosure must have moved WITH it:
      * the third-party script COUNT must have gone up — render.py's own note
        says "a revision that fixes the prose and leaves the count is still
        false", and the count is the half people forget;
      * the policy must name Meta/Facebook somewhere;
      * it must no longer claim the site sets no cookies, because the pixel
        sets `_fbp`.

WHAT IT CANNOT DO, said plainly rather than implied

  It cannot tell whether the id is the RIGHT one. A wrong id loads the script,
  returns 200 from config and from tr/, and defines fbq — every signal green
  while Meta records nothing. Only the `_fbp` cookie on a real load
  discriminates, which is `~/ops/bin/fbp-check.mjs`, and it has to run against
  the deployed site rather than the build.

  So: this gate is necessary and not sufficient, and a green run here is not
  evidence the pixel works.

    python3 scripts/verify_pixel.py
    python3 scripts/verify_pixel.py --self-test
"""
from __future__ import annotations

import argparse
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
SITE = HERE.parent / "site"
sys.path.insert(0, str(HERE))

import render  # noqa: E402

TRACKER_MARKS = ("fbq(", "connect.facebook.net", "fbevents.js")
PRIVACY = SITE / "legal" / "privacy" / "index.html"

#: The count sentence render.py's comment is about. Captured as a word so the
#: check is about the NUMBER rather than the phrasing around it.
_COUNT = re.compile(
    r"runs\s+(one|two|three|four|five|\d+)\s+third-party\s+scripts?", re.I)
_WORD_TO_INT = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5}


def built_pages() -> list[pathlib.Path]:
    return sorted(SITE.rglob("*.html"))


def pages_with_tracker(pages: list[pathlib.Path]) -> list[str]:
    out = []
    for page in pages:
        text = page.read_text(encoding="utf-8", errors="replace")
        if any(mark in text for mark in TRACKER_MARKS):
            out.append(str(page.relative_to(SITE)))
    return out


def declared_script_count() -> int | None:
    if not PRIVACY.is_file():
        return None
    text = re.sub(r"<[^>]+>", " ", PRIVACY.read_text(encoding="utf-8", errors="replace"))
    m = _COUNT.search(" ".join(text.split()))
    if not m:
        return None
    raw = m.group(1).lower()
    return _WORD_TO_INT.get(raw, int(raw) if raw.isdigit() else None)


def check(pixel_id: str) -> list[str]:
    pages = built_pages()
    if not pages:
        return ["no built pages — run scripts/build.py first. Nothing compared "
                "is not a pass."]
    carrying = pages_with_tracker(pages)
    count = declared_script_count()
    bad: list[str] = []

    if not pixel_id:
        if carrying:
            bad.append(f"META_PIXEL_ID is empty but {len(carrying)} page(s) carry a "
                       f"tracker snippet: {', '.join(carrying[:4])}")
        privacy = PRIVACY.read_text(encoding="utf-8", errors="replace") if PRIVACY.is_file() else ""
        if re.search(r"(?i)meta pixel|facebook pixel", privacy):
            bad.append("the privacy policy describes a Meta pixel that this build "
                       "does not ship — disclosure ahead of the tracker is still a "
                       "policy that does not match the site")
        return bad

    # LIVE
    if not carrying:
        bad.append(f"META_PIXEL_ID is set to {pixel_id[:6]}… but no built page carries "
                   f"the snippet — the tracker is configured and not deployed")
    if not any(pixel_id in p.read_text(encoding="utf-8", errors="replace") for p in pages):
        bad.append("the id itself appears on no page; a snippet without it inits nothing")

    privacy = PRIVACY.read_text(encoding="utf-8", errors="replace") if PRIVACY.is_file() else ""
    if not privacy:
        bad.append("no privacy policy page was built, and a tracker ships with its "
                   "disclosure or not at all")
        return bad
    if not re.search(r"(?i)meta|facebook", privacy):
        bad.append("the privacy policy names neither Meta nor Facebook while the site "
                   "loads their pixel")
    if count is not None and count < 3:
        bad.append(f"the privacy policy still says the site runs {count} third-party "
                   f"script(s). The pixel is a third. render.py's own note: a revision "
                   f"that fixes the prose and leaves the count is still false")
    if re.search(r"(?i)(sets? no cookies|no cookies (?:are|is) set|without cookies)", privacy):
        bad.append("the policy still claims no cookies while the pixel sets _fbp")
    return bad


def self_test() -> int:
    """Both directions, against the ARTIFACT — the built pages, not a mock."""
    pages = built_pages()
    if not pages:
        print("  self-test SKIPPED: no built pages")
        return 1
    carrying = pages_with_tracker(pages)

    if render.META_PIXEL_ID:
        # Live build: prove the gate would catch the disclosure being left behind.
        print("  self-test: a live pixel whose privacy policy was not updated")
        original = PRIVACY.read_text(encoding="utf-8")
        try:
            PRIVACY.write_text(original.replace("three third-party scripts",
                                                "two third-party scripts"))
            if not check(render.META_PIXEL_ID):
                print("  SELF-TEST FAILED — a stale script count passed.")
                return 1
            print("  self-test ok — the stale count was caught")
        finally:
            PRIVACY.write_text(original)
        return 0

    # Dark build: the empty case passing proves nothing on its own, so plant a
    # tracker in a real built page and require the gate to see it.
    print("  self-test: planting a tracker snippet into a built page")
    victim = SITE / "index.html"
    original = victim.read_text(encoding="utf-8")
    try:
        victim.write_text(original.replace("</body>", "<script>fbq('init','000')</script></body>"))
        if not check(""):
            print("  SELF-TEST FAILED — a page carrying fbq passed a DARK build. "
                  "The gate cannot see the thing it guards.")
            return 1
        print("  self-test ok — the planted tracker was caught")
    finally:
        victim.write_text(original)

    if carrying:
        print(f"  note: {len(carrying)} page(s) already carried a tracker before planting")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()

    pixel_id = getattr(render, "META_PIXEL_ID", "")
    state = f"LIVE ({pixel_id[:6]}…)" if pixel_id else "DARK (no id)"
    print(f"  tracker state: {state}")
    count = declared_script_count()
    print(f"  privacy policy declares: {count if count is not None else '?'} third-party script(s)")

    if args.self_test and self_test() != 0:
        return 1

    problems = check(pixel_id)
    if problems:
        print(f"\nPIXEL FAIL — {len(problems)} problem(s):")
        for p in problems:
            print(f"    {p}")
        return 1
    print("\nPIXEL ok — the tracker's state and its disclosure agree.")
    if pixel_id:
        print("  This does NOT prove the id is correct. A wrong id passes every check "
              "here.\n  Confirm the _fbp cookie on the deployed site: "
              "node ~/ops/bin/fbp-check.mjs")
    return 0


if __name__ == "__main__":
    sys.exit(main())
