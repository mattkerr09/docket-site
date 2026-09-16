#!/usr/bin/env python3
"""Fail the deploy when this site stops saying one thing about itself.

`brand.positioning` fired on docketseo.app on 2026-09-15, across every page
carrying a meta description: beyond the brand name, not one word reached the
share of pages the check asks for. The finding was fair. A site that ships one
page at a time writes one pitch at a time, and nobody had decided what the
sentence was.

The sentence is: **Docket audits your site on your own Mac.** The two words
that carry it are `audit` and `site`, and this gate exists because an editorial
property decays silently. Twelve descriptions were rewritten to clear it; the
thirteenth page shipped after this could put it back under, and nothing would
say so until the next full audit of our own site.

⚠️ THIS RUNS THE SHIPPED CHECK, IT DOES NOT REIMPLEMENT IT.
The threshold, the stop-word list and the brand-name exclusion all live inside
`positioning()` as locals — there is nothing to import and nothing to keep in
sync. A gate that re-derived them would be a plausible substitute for the
check, and would agree with it right up until someone tuned the check. So the
descriptions are read out of the built HTML, wrapped in the smallest object
`positioning()` actually touches, and handed to the real function.

⚠️ NOT A KEYWORD RULE. This does not require any particular word. It requires
that *some* shared vocabulary survives, which is what the check measures. If a
future rewrite threads a better pair of words through the site, this passes on
those instead and no one has to edit this file.
"""
from __future__ import annotations

import glob
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import app_path  # noqa: E402

app_path.on_path()

from seo_engine.checks.brand import positioning  # noqa: E402

ORIGIN = "https://docketseo.app"
SITE = Path(__file__).resolve().parents[1] / "site"


class _Page:
    """Only what `positioning()` reads: a URL and a meta description."""

    def __init__(self, url: str, description: str):
        self.url = url
        self.meta_description = description


class _Site:
    origin = ORIGIN
    final_origin = ORIGIN


class _Context:
    """The three attributes and one method `positioning()` uses."""

    def __init__(self, pages):
        self.indexable = pages
        self.site = _Site()
        self.prose_language_supported = True

    def urls_of(self, pages, cap: int = 25):
        return [p.url for p in pages][:cap]


def described_pages():
    """Every indexable built page that carries a meta description.

    `noindex` pages are excluded because `ctx.indexable` excludes them, and two
    of ours carry it deliberately.
    """
    files = set(glob.glob(str(SITE / "**" / "index.html"), recursive=True))
    files |= set(glob.glob(str(SITE / "*.html")))
    pages = []
    for path in sorted(files):
        html = Path(path).read_text(encoding="utf-8")
        if re.search(r'<meta name="robots"[^>]*noindex', html):
            continue
        found = re.search(r'<meta name="description" content="([^"]*)"', html)
        if not found:
            continue
        rel = str(Path(path).relative_to(SITE)).replace("index.html", "")
        pages.append(_Page(f"{ORIGIN}/{rel}", found.group(1)))
    return pages


def main() -> int:
    pages = described_pages()
    if not pages:
        print("verify_positioning: no built pages with descriptions — build first")
        return 1

    findings = list(positioning(_Context(pages)))
    if not findings:
        print(f"verify_positioning: ok — {len(pages)} descriptions share a vocabulary")
        return 0

    finding = findings[0]
    print("verify_positioning: FAIL — Docket's own check fires on Docket's own site")
    print()
    print(f"  {finding.title}")
    print(f"  {finding.detail}")
    print()
    print("  The sentence is: Docket audits your site on your own Mac.")
    print("  Put its words into the descriptions of the pages they are true of —")
    print("  not into all of them, and not into one they are not true of.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
