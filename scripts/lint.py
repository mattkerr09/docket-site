#!/usr/bin/env python3
"""SEO article gate — blocks AI-slop prose, thin pages, and near-duplicates.

Ported from Crisp, where every rule in it was earned by something that actually
went wrong on a live programmatic set. Kept verbatim rather than "improved":
the duplicate-shingle threshold and the chrome exclusion in particular were
tuned against real failures, and re-deriving them from scratch would just
repeat the same mistakes.

Run before shipping any article set:
    python3 scripts/lint.py site

Three checks, each of which is a real ship-blocker (all three come from what actually went
wrong on the Outlier programmatic set, plus matt's 2026-07-23 rule "articles must not look
like AI wrote it"):

  VOICE      banned stock phrases + the "not just X, it's Y" construction. These are the
             tells readers and reviewers pattern-match on instantly.
  THIN       < MIN_WORDS of real body text. Thin pages are a flag risk on their own.
  DUPLICATE  near-identical 8-word shingles across pages. This — not thinness — is what
             actually tripped the Outlier set, because programmatic pages drift toward one
             template. Two pages sharing too much phrasing means one of them shouldn't exist.

Exit 1 if anything fails, so it can gate a build.
"""
from __future__ import annotations

import html
import re
import sys
from collections import defaultdict
from pathlib import Path

MIN_WORDS = 600
SHINGLE_N = 8
# Google truncates a title around 580px — roughly 60 characters — and a meta
# description around 160 on desktop. Past that the tail is not shown to anyone,
# so it is copy nobody reads occupying the only two lines of a result you
# control. An August 2026 check found 9 titles and 13 descriptions over, all
# written by us, all trimmable without losing anything. Gated so it stays fixed.
MAX_TITLE = 60
MAX_DESC = 165
DUP_RATIO = 0.28          # >28% shared shingles between two pages = too close

# The tells. Lowercased substring match against visible text.
BANNED = [
    "in today's digital", "in today's fast-paced", "ever-evolving", "ever-changing",
    "let's dive in", "let's explore", "dive into the world", "look no further",
    "game-changer", "game changer", "unlock the power", "take your videos to the next level",
    "revolutionize", "revolutionary", "cutting-edge", "state-of-the-art",
    "seamlessly integrate", "effortlessly", "seamless experience",
    "in conclusion", "at the end of the day", "when it comes to",
    "whether you're a", "whether you are a",
    "it's important to note", "it is important to note",
    "harness the power", "elevate your", "supercharge",
    "in the realm of", "navigating the", "delve into",
]
# "It's not just X, it's Y" / "isn't just X — it's Y"
NOT_JUST = re.compile(r"\b(it'?s|is|isn'?t|not)\s+just\s+\w+[,—-]\s*it'?s\b", re.I)

_HEADING = re.compile(r"<h([1-6])[^>]*>", re.I)
_TITLE = re.compile(r"<title>(.*?)</title>", re.S | re.I)
_DESC = re.compile(r'<meta name="description" content="(.*?)"', re.S | re.I)
_TAG = re.compile(r"<(script|style)[^>]*>.*?</\1>", re.S | re.I)
# Nav and footer are IDENTICAL on every page by design. Counting them as shared prose makes
# any well-templated site look like a duplicate farm — the first run of this linter flagged
# two pages at 30% whose only overlap was the footer and a shared comparison table. Shared
# chrome is fine; shared PHRASING is the actual spam signal, so measure only the body.
_CHROME = re.compile(r"<(nav|footer)[^>]*>.*?</\1>", re.S | re.I)
_HTML = re.compile(r"<[^>]+>")


def visible_text(html: str, *, body_only: bool = False) -> str:
    html = _TAG.sub(" ", html)
    if body_only:
        html = _CHROME.sub(" ", html)
    return re.sub(r"\s+", " ", _HTML.sub(" ", html)).strip()


def shingles(text: str, n: int = SHINGLE_N) -> set[str]:
    w = re.findall(r"[a-z0-9']+", text.lower())
    return {" ".join(w[i:i + n]) for i in range(max(0, len(w) - n + 1))}


def main(root: str) -> int:
    pages = sorted(Path(root).rglob("index.html"))
    if not pages:
        print(f"no pages under {root}")
        return 1

    fails: list[str] = []
    sh: dict[Path, set[str]] = {}

    for p in pages:
        try:
            raw = p.read_text(encoding="utf-8", errors="ignore")
            text = visible_text(raw)
        except OSError:
            continue

        title = html.unescape(m.group(1).strip()) if (m := _TITLE.search(raw)) else ""
        desc = html.unescape(m.group(1).strip()) if (m := _DESC.search(raw)) else ""
        if not title or len(title) > MAX_TITLE:
            fails.append(f"TITLE  {p}: {len(title)} chars (max {MAX_TITLE})")
        if not desc or len(desc) > MAX_DESC:
            fails.append(f"DESC   {p}: {len(desc)} chars (max {MAX_DESC})")

        # A skipped heading level breaks the outline a screen reader announces
        # and the one a search engine reads. Four hub pages jumped h1 straight
        # to h3 purely for the smaller type, which a font-size handles.
        levels = [int(m) for m in _HEADING.findall(_CHROME.sub(" ", raw))]
        prev = 0
        for level in levels:
            if prev and level > prev + 1:
                fails.append(f"HEADS  {p}: h{prev} -> h{level}")
                break
            prev = level
        words = len(text.split())
        low = text.lower()

        hits = [b for b in BANNED if b in low]
        if NOT_JUST.search(text):
            hits.append("not-just-X-its-Y")
        if hits:
            fails.append(f"VOICE  {p}: {', '.join(hits[:4])}")
        # LEGAL PAGES ARE EXEMPT from the word floor. MIN_WORDS is an SEO rule for articles —
        # a refund policy should be as short as it can be while staying complete, and padding one
        # to clear a word count makes it worse for the reader and no better legally.
        #
        # SECTION HUBS are exempt for the same reason: /vs/ and /learn/ are navigation, and a
        # link list padded to 600 words is worse for the reader and no better for search. A hub
        # is any index.html exactly one level under the site root — deeper pages are articles
        # and are held to the floor.
        rel = p.relative_to(Path(root)).as_posix()
        is_hub = rel.count("/") == 1 and rel.endswith("index.html")
        if words < MIN_WORDS and "/legal/" not in str(p).replace("\\", "/") and not is_hub:
            fails.append(f"THIN   {p}: {words}w (min {MIN_WORDS})")
        # duplicate check ignores shared nav/footer chrome — see _CHROME above
        sh[p] = shingles(visible_text(p.read_text(encoding="utf-8", errors="ignore"),
                                      body_only=True))

    # near-duplicate detection, pairwise within the set
    seen: set[tuple[Path, Path]] = set()
    for a, sa in sh.items():
        if len(sa) < 40:
            continue
        for b, sb in sh.items():
            if a >= b or (a, b) in seen or len(sb) < 40:
                continue
            seen.add((a, b))
            overlap = len(sa & sb) / min(len(sa), len(sb))
            if overlap > DUP_RATIO:
                fails.append(f"DUP    {a.parent.name} ~ {b.parent.name}: {overlap:.0%} shared")

    print(f"checked {len(pages)} pages")
    if not fails:
        print("PASS — voice, length, headings, thin and duplicate checks clean")
        return 0
    print(f"\nFAIL ({len(fails)}):")
    for f in sorted(fails):
        print("  " + f)
    return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1] if len(sys.argv) > 1 else "site"))
