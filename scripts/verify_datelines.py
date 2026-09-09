#!/usr/bin/env python3
"""Every `dateModified` this site publishes must be one a human supplied.

**The bug this exists for was live on 2026-09-09.** `render()` emitted
`"dateModified": modified or published`, so a page that never passed a
modification date asserted it was last modified on the day it was published.
Measured on the built tree that morning: **58 of 59 pages carrying a date block
emitted `dateModified` equal to `datePublished`**, and 41 of those sat on
`render()`'s own default of 2026-08-06 — a date no article ever chose.

At least one was provably false. `/learn/dead-contact-address/` declared
2026-08-07 while serving a paragraph added on 2026-08-13 (commit `6c9d6989`,
"The domain now publishes MX records…"), which the live page carried.

**Why it is deleted rather than derived.** This site's rule for a number it
cannot derive is "derive it, or delete it". A dateline cannot be derived here:
an article's prose is built inside its function from interpolated facts rather
than held as a literal, so recovering it per revision would mean EXECUTING old
revisions — which `verify_competitive_claims._verified_at` refuses to do,
because an old revision need not import under today's interpreter. An absent
`dateModified` says "unknown", which is true. An invented one says something
false, and this is the exact class of defect Docket sells itself on finding.

**What this gate asserts.** Every `dateModified` in the built site appears
verbatim as an explicit `modified="..."` argument in `scripts/articles/`. A
value that is in the HTML and in no source is fabricated, which is the failure
above. It is the same cross-check `verify_version_strings.py` makes between a
served string and the thing it is derived from.

**It does not check that a supplied date is CORRECT** — no gate can know when
somebody last meaningfully edited prose. It checks only that a person chose it.

    python3 scripts/verify_datelines.py
    python3 scripts/verify_datelines.py --self-check
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "site"
ARTICLES = ROOT / "scripts" / "articles"

LD = re.compile(r'(?is)<script[^>]*application/ld\+json[^>]*>(.*?)</script>')
SUPPLIED = re.compile(r'modified\s*=\s*"(\d{4}-\d{2}-\d{2})"')


def supplied_dates() -> set[str]:
    """Every modification date a human wrote down in an article source."""
    out: set[str] = set()
    for path in sorted(ARTICLES.glob("*.py")):
        out |= set(SUPPLIED.findall(path.read_text()))
    return out


def published_pairs(html: str):
    """(datePublished, dateModified) for each dated node on one page."""
    for block in LD.findall(html):
        try:
            data = json.loads(block)
        except ValueError:
            # A block this gate cannot parse is REPORTED, never skipped — a
            # fabricated date hiding in unparsed JSON is exactly what it is for.
            yield ("<unparseable>", "<unparseable>")
            continue
        for node in (data if isinstance(data, list) else [data]):
            if isinstance(node, dict) and "datePublished" in node:
                yield (node.get("datePublished"), node.get("dateModified"))


def audit(extra_html: dict[str, str] | None = None):
    """(failures, pages_seen, dated_nodes). `extra_html` is for --self-check."""
    allowed = supplied_dates()
    failures, pages, dated = [], 0, 0
    documents = {str(p.relative_to(SITE)): p.read_text(errors="ignore")
                 for p in sorted(SITE.rglob("index.html"))}
    documents.update(extra_html or {})
    for name, html in documents.items():
        pages += 1
        for pub, mod in published_pairs(html):
            dated += 1
            if mod is None:
                continue
            if mod == "<unparseable>":
                failures.append(f"{name}: a JSON-LD block could not be parsed")
                continue
            if mod not in allowed:
                failures.append(
                    f"{name}: publishes dateModified {mod}, which no article "
                    f"source supplies with modified=\"…\"."
                    + (" It equals datePublished, which is the shape render()"
                       " used to fabricate." if mod == pub else ""))
    return failures, pages, dated


def main() -> int:
    if not SITE.exists():
        print("DATELINE: no site/ directory — run scripts/build.py first.")
        print("That is not a pass.")
        return 1

    if "--self-check" in sys.argv:
        # A GATE THAT HAS NEVER FIRED IS NOT A GATE. Plant the exact shape the
        # bug produced — a dateModified equal to datePublished, on a date no
        # source supplies — and require this code to reject it.
        planted = ('<script type="application/ld+json">'
                   '{"@type":"Article","datePublished":"1999-01-02",'
                   '"dateModified":"1999-01-02"}</script>')
        failures, _, _ = audit({"<planted>": planted})
        if not any("<planted>" in f for f in failures):
            print("DATELINE SELF-CHECK FAILED — a fabricated dateModified was "
                  "not rejected, so a green run from this gate means nothing.")
            return 1
        clean, _, _ = audit()
        print("DATELINE self-check ok — the planted fabrication is rejected and "
              f"the real tree reports {len(clean)} failure(s).")
        return 0

    failures, pages, dated = audit()
    if failures:
        print(f"DATELINE FAILED — {len(failures)} fabricated date(s):")
        for f in failures[:20]:
            print(f"  {f}")
        return 1
    print(f"DATELINE ok — {pages} page(s), {dated} dated node(s); every "
          f"dateModified published is one an article source supplies "
          f"({len(supplied_dates())} in use).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
