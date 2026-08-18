#!/usr/bin/env python3
"""Does any page name a version that is not the one being shipped?

**The failure this exists for happened on a sibling site, not this one.**
bookbreaker.bet served "Bookbreaker 0.1.0 is out" on all 116 of its pages while
`/download/` handed over the 0.1.2 dmg. The version sat inline in a site-wide
banner where the generator's model could not reach it, so it stopped moving at
0.1.1 and nothing noticed for two releases. Every other number on that site was
derived and correct; this one was typed.

Docket ships a version roughly every twenty minutes at the moment, which makes
it the same accident waiting for the same conditions. Checked on 2026-08-18
across all 57 live pages: exactly one version string is served, `1.1.50`, and it
is the release. So this gate starts green — which is the point. A gate that is
red the day it is written gets switched off, and then it protects nothing.

**What it deliberately does NOT do.** It does not care where the string came
from. A version rendered from `_data` and a version typed by hand look identical
to a reader, and the reader is who this is for; the only question worth asking
is whether what a page says matches what the release is. `verify_numbers.py`
already refuses a *typed* number where a derived one belongs, and that is a
different question from this one.

    python3 scripts/verify_version_strings.py
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import render  # noqa: E402

SITE = Path(__file__).resolve().parent.parent / "site"

#: Docket's scheme. Deliberately narrow: a looser `\d+\.\d+\.\d+` matches
#: "Chrome/126.0.0.0" in a user-agent string and CSS values, and a gate that
#: fires on those is one nobody reads.
#: The `v` prefix is optional and matters: the first draft used `\b1\.` and
#: silently saw nothing on the pages that write "v1.1.50", because there is no
#: word boundary between a letter and a digit. It reported three strings and
#: missed the majority — and a control that injected a stale version into one of
#: those pages passed. A gate that cannot see the thing it guards is worse than
#: no gate, because it reports OK.
_VERSION = re.compile(r"(?<![\w.])v?(1\.\d+\.\d+)\b")

_TAGS = re.compile(r"(?is)<(script|style)[^>]*>.*?</\1>")


def visible(html: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", _TAGS.sub(" ", html)))


def main() -> int:
    pages = sorted(SITE.rglob("*.html"))
    if not pages:
        print("VERSION FAIL — no built pages; run scripts/build.py first")
        return 1

    # `render.RELEASE` is the TAG ("v1.1.50"); pages render the bare
    # version ("1.1.50"). The first draft compared them directly and
    # reported three pages wrong while printing "says 1.1.50 — the
    # release is v1.1.50", which is the same version with a prefix.
    release = render.RELEASE.lstrip("v")
    problems: list[str] = []
    seen = 0

    for path in pages:
        raw = path.read_text(encoding="utf-8", errors="replace")
        # Raw, not just visible: a stale version inside a download URL or
        # a JSON-LD softwareVersion is the worst kind and both are
        # stripped by `visible()`. The pattern is narrow enough that CSS
        # and script bodies do not trip it.
        text = raw
        for match in set(_VERSION.findall(text)):
            seen += 1
            if match != release:
                rel = path.relative_to(SITE)
                problems.append(
                    f"    {rel} says {match} — the release is {release}. "
                    f"A reader is being told about a build they cannot download.")

    if problems:
        print(f"VERSION FAIL — {len(problems)} page(s) name a version that is "
              f"not {release}:")
        for p in sorted(problems):
            print(p)
        print("\n  bookbreaker.bet shipped two releases past a banner with the")
        print("  version typed inline. Derive it, or delete it.")
        return 1

    print(f"VERSION ok — {len(pages)} pages, {seen} version string(s), "
          f"all {release}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
