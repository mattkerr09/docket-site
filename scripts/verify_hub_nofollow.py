#!/usr/bin/env python3
"""Every static link to the hub's /buy and /dl carries rel="nofollow".

The hub's Buy and Download links are redirects to our own checkout and to the
release file. Without nofollow they send link value to a workers.dev host, and on
Crisp Docket read 493 of them as 73% of the site's outbound links going to one
domain (10-13 audit). render() adds the attribute; this refuses a built page that
slipped through, for example a hand-written file render() never touches.

--self-test plants a bare hub link into a copy of a built page and requires the
gate to refuse it, then plants a nofollow one and requires it to pass.
"""
from __future__ import annotations

import pathlib
import re
import sys

SITE = pathlib.Path(__file__).resolve().parent.parent / "site"
HUB = "https://kerr-affiliate-hub.kerrco.workers.dev"
_TAG = re.compile(r'<a\b[^>]*\bhref="' + re.escape(HUB) + r'/(?:buy|dl)/[^"]*"[^>]*>')


def bare(text: str) -> list[str]:
    return [m.group(0)[:120] for m in _TAG.finditer(text)
            if not re.search(r'\brel="[^"]*\bnofollow\b', m.group(0))]


def main() -> int:
    pages = {p.relative_to(SITE).as_posix(): p.read_text(encoding="utf-8", errors="ignore")
             for p in SITE.rglob("*.html")}
    if not pages:
        print("FAIL  no built site to check")
        return 1
    if "--self-test" in sys.argv:
        planted = f'<a href="{HUB}/buy/docket?src=x">x</a>'
        ok = f'<a rel="nofollow" href="{HUB}/dl/docket?src=x">x</a>'
        if not bare(planted) or bare(ok):
            print("FAIL  self-test: a bare hub link was not refused, or a nofollow one was")
            return 1
    found = [(rel, tag) for rel, text in sorted(pages.items()) for tag in bare(text)]
    if found:
        print(f"FAIL  {len(found)} hub link(s) without rel=\"nofollow\":")
        for rel, tag in found[:15]:
            print(f"    {rel}: {tag}")
        return 1
    print(f"  ok: every hub /buy and /dl link carries nofollow across {len(pages)} built pages"
          + (" (self-test passed)" if "--self-test" in sys.argv else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
