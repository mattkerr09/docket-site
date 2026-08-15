#!/usr/bin/env python3
"""A claim about a rival must name its source and the day it was read.

Every `/vs/` page on this site quotes the vendor and links the page it came
from, under a "Checked 10 August 2026" note. The homepage did not. It said:

    "Four things crawler tools ignore."
    "Technical SEO is table stakes, and it is all most tools do. These four are
     where the money actually leaks — and each one is a separate subscription
     anywhere else."

Unsourced, undated, on the page with more traffic than every comparison page
combined — and wrong on its sharpest point. Screaming Frog's own user guide,
read 2026-08-13:

    "The user-agent configuration allows you to switch the user-agent of the
     HTTP requests made by the SEO Spider and which robots.txt directives are
     followed."

That is the AI-crawler question, answerable one agent at a time, in a tool we
told the reader ignores it. The homepage now concedes it and says what Docket
adds instead: every crawler in one pass, and the server's actual response
compared against the file — a CDN rule blocking GPTBot is invisible in a
robots.txt that permits it.

**What this gate checks**, on the built HTML rather than the generator, because
the built HTML is what a reader gets:

  1. Any page naming a rival in a comparative sentence carries a check date.
  2. Every claim recorded in `comparisons.VERIFIED` has a source URL.
  3. The homepage's four-lane section still concedes the user-agent capability.

It deliberately does NOT try to judge whether a claim is true — no gate can.
It enforces that a reader can go and check, which is the part that decays
silently.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "site"
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "articles"))

#: Rivals this site names. Kept here rather than derived from VERIFIED so a new
#: name appearing in prose without an entry is caught rather than excused.
RIVALS = ("Screaming Frog", "Sitebulb", "Ahrefs", "Semrush", "Lighthouse",
          "Search Console", "Sitechecker", "SEOptimer", "Ubersuggest", "Scrutiny")

#: Only the unambiguous superiority claims — an assertion that a named rival
#: LACKS something, or that Docket alone has it.
#:
#: The first version of this list also held "cannot", "does not", "never" and
#: "unlike". It failed 23 pages, and reading them showed why: most were
#: concessions. "Screaming Frog and Sitebulb are both better crawlers than
#: Docket by several measures" and "Docket does not attempt that scale" are
#: sentences this site should be proud of, and a gate that demands a citation
#: for praising a rival is a gate someone comments out on a Friday.
#:
#: What is left is the class that was actually wrong: "crawler tools ignore".
#: A reader cannot check "ignores" without being told where to look.
COMPARATIVE = re.compile(
    r"\b(ignores?|ignored|no other tool|the only tool|only Docket|"
    r"nothing else does|no one else)\b", re.I)

#: The concession that must survive. If someone tightens this sentence back
#: into "crawler tools ignore AI search", the gate says so.
CONCESSION = "switch agent and follow that agent"


def _text(html: str, *, chrome: bool = True) -> str:
    """Visible text. With `chrome=False`, the nav and footer are removed first.

    Every page on this site carries "Compare · vs Screaming Frog · vs Sitebulb ·
    vs Ahrefs · vs Semrush" in its footer. The first version of this gate read
    that as fifty pages making undated comparative claims, because a rival's
    name sat within 260 characters of an unrelated "does not" in the body.

    That is the same error this project just corrected in the product itself —
    a link's meaning read out of chrome rather than content — arrived at
    independently, in a gate written to catch exactly this class of mistake.
    """
    html = re.sub(r"<(script|style).*?</\1>", " ", html, flags=re.S | re.I)
    if not chrome:
        html = re.sub(r"<(nav|footer|header)\b.*?</\1>", " ", html,
                      flags=re.S | re.I)
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html))


def main() -> int:
    failures: list[str] = []

    try:
        import comparisons
    except Exception as exc:                      # pragma: no cover - import guard
        print(f"COMPETITIVE FAIL — cannot import comparisons: {exc}", file=sys.stderr)
        return 1

    # 2. Every recorded claim has a source.
    for key, claims in comparisons.VERIFIED.items():
        for claim, source in claims:
            if not source.startswith("http"):
                failures.append(f"{key}: claim has no source URL — {claim[:60]}")
            if not claim.strip():
                failures.append(f"{key}: empty claim against {source}")

    home = SITE / "index.html"
    if not home.exists():
        print("COMPETITIVE FAIL — site/index.html not built", file=sys.stderr)
        return 1
    home_html = home.read_text()

    # 3. The concession survives.
    if CONCESSION not in _text(home_html):
        failures.append(
            "the homepage no longer concedes that a crawler can check robots "
            "directives per user-agent — Screaming Frog's user guide says it "
            "can, and saying otherwise is the error this gate exists for")

    # 1. Comparative sentences carry a date.
    checked = comparisons.HOME_CLAIM_CHECKED_HUMAN
    pages = sorted(SITE.rglob("index.html"))
    unsourced: list[str] = []
    for page in pages:
        text = _text(page.read_text(), chrome=False)
        # Sentence, not proximity. A ±260-character window failed a page whose
        # only "ignore" was "saying so would train you to ignore the check",
        # 300 characters from a paragraph headed "Where someone else's data is
        # better" that concedes Ahrefs has a dataset we cannot match — and
        # dates it. The verb has to be in the same sentence as the name, or the
        # gate is measuring adjacency rather than a claim.
        sentences = re.split(r"(?<=[.!?])\s+", text)
        for rival in RIVALS:
            for sentence in sentences:
                if rival not in sentence or not COMPARATIVE.search(sentence):
                    continue
                dated = ("Checked" in text or checked in text
                         or comparisons.CHECKED_ON_HUMAN in text)
                if not dated:
                    rel = page.relative_to(SITE)
                    unsourced.append(f"{rel}: compares against {rival} with no check date")
                break

        # Every /vs/ page, whatever verb it uses.
        #
        # `COMPARATIVE` matches superiority words — "ignores", "the only tool",
        # "no other tool". A page written entirely in concessions and plain
        # facts matches none of them, so it was never asked for a date. Found
        # 2026-08-15 while adding a comparison against a paid Mac competitor:
        # the page states that rival's price, its operating system and its
        # published feature list, and the break test — deleting every source —
        # left the gate printing "ok".
        #
        # Those are the claims that rot. A superiority claim is wrong the day
        # somebody argues with it; a price is wrong quietly, months later, and
        # a stale price about a named third party is the worst thing on this
        # site to get wrong.
        #
        # Scoped to /vs/ rather than to a wider verb list, because widening the
        # pattern is what produced 23 false failures the first time: most
        # sentences naming a rival elsewhere on this site are concessions, and a
        # gate that demands citations for praise teaches people to route around
        # it. A page under /vs/ exists to compare; there is no case where it
        # should carry no date.
        rel = page.relative_to(SITE)
        if str(rel).startswith("vs/") and str(rel) != "vs/index.html":
            named = [r for r in RIVALS if r in text]
            dated = ("Checked" in text or checked in text
                     or comparisons.CHECKED_ON_HUMAN in text)
            if named and not dated:
                unsourced.append(
                    f"{rel}: names {', '.join(named)} and carries no check "
                    f"date. Every fact on a /vs/ page about somebody else's "
                    f"product — price, platform, feature list — needs a date "
                    f"beside it, whether or not the page claims to be better.")

    failures.extend(sorted(set(unsourced)))

    if failures:
        print("COMPETITIVE FAIL", file=sys.stderr)
        for f in failures:
            print(f"  {f}", file=sys.stderr)
        return 1

    total = sum(len(v) for v in comparisons.VERIFIED.values())
    print(f"COMPETITIVE ok — {total} sourced claim(s) across "
          f"{len(comparisons.VERIFIED)} rival(s); every comparative page dated; "
          f"the homepage concedes what a crawler can do")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
