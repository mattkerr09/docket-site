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

#: A redirect stub left behind when a URL moves is not content and must not be
#: judged as content. It is deliberately near-empty, deliberately noindexed,
#: and it exists so an old URL keeps working instead of 404ing — which is what
#: this product tells everybody else to do.
#:
#: The exemption is narrow on purpose: BOTH a noindex robots meta AND a refresh
#: to another page. A page that is merely thin, or merely noindexed, still gets
#: judged. Widening this any further would turn "thin" into a rule anyone can
#: opt out of, and a gate nobody can fail is not a gate.
_NOINDEX = re.compile(r'<meta[^>]+name=["\']?robots["\']?[^>]+noindex', re.I)
_REFRESH = re.compile(r'<meta[^>]+http-equiv=["\']?refresh', re.I)


def is_redirect_stub(raw: str) -> bool:
    return bool(_NOINDEX.search(raw) and _REFRESH.search(raw))
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

# Substring matching fired on "track whether you are actually cited", because
# the banned opener "whether you are a" is a prefix of "…you are actually".
# Every entry is a phrase, so every entry gets word boundaries. A linter that
# flags correct prose is one somebody eventually disables wholesale.
_BANNED_RE = [
    (phrase, re.compile(r"(?<!\w)" + re.escape(phrase) + r"(?!\w)", re.I))
    for phrase in BANNED
]

#: An f-string hole that reached the page. `/how-to/fix-ai-crawler-access/`
#: shipped a body containing `{F.index_n()}` because the string it lived in was
#: not an f-string — the interpolation was correct, the quote mark was not, and
#: nothing else would have noticed.
_UNRENDERED = re.compile(r"\{[A-Za-z_][A-Za-z0-9_.\[\]'\"()]*\}")
#: CSS comments, stripped before counting braces so prose inside them cannot
#: be mistaken for syntax.
_CSS_COMMENT = re.compile(r"/\*.*?\*/", re.S)
_STYLE_BLOCK = re.compile(r"<style>(.*?)</style>", re.S | re.I)
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


#: A universal claim about tools other than this one.
#:
#: The homepage led with "Every other tool hands you a list" for months. It is
#: false of Sitebulb, whose own feature page advertises "Prioritized Hints" and
#: "a list of prioritized and categorized issues up-front". A buyer who has
#: used Sitebulb reads that headline and stops believing the rest of the page.
#:
#: The engine has had a structural gate against absolutes in finding titles for
#: several iterations — an absolute is a claim about the arithmetic, not a turn
#: of phrase. The marketing copy never got one, which is exactly how it shipped.
#: Claims about our own site ("every page", "every audit") are unaffected; this
#: only fires on a universal quantifier aimed at the competition.
_COMPETITOR_ABSOLUTE = re.compile(
    r"\b(every|all|no|none of the|nobody|the only|nothing)\b"
    r"[^.<>]{0,40}?"
    # Three words were tried and removed, because a gate that cries wolf gets
    # switched off in a week:
    #
    #   "crawler"    — used generically here ("nothing a crawler would flag"),
    #                  and it fired on a comparison table whose cells strip
    #                  down to "No Yes hreflang reciprocity Yes Yes AI crawler".
    #   "competitor" — in this product it means the *user's* market rivals, as
    #                  in "the issues every competitor has already fixed". That
    #                  is a feature description, not a claim about software.
    #   "alternative"— every /vs/ page is titled "<tool> alternative".
    #
    # The residual gap is real and worth stating: "no competing product does X"
    # would slip through. What is caught is the shape that actually shipped.
    r"\b(other tool|other tools|other product|other products|"
    r"competing tool|competing tools|else does)\b",
    re.I,
)


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

        if is_redirect_stub(raw):
            # Not content. See is_redirect_stub for why this exemption is this
            # narrow and must stay that way.
            continue

        title = html.unescape(m.group(1).strip()) if (m := _TITLE.search(raw)) else ""
        desc = html.unescape(m.group(1).strip()) if (m := _DESC.search(raw)) else ""
        if not title or len(title) > MAX_TITLE:
            fails.append(f"TITLE  {p}: {len(title)} chars (max {MAX_TITLE})")
        if not desc or len(desc) > MAX_DESC:
            fails.append(f"DESC   {p}: {len(desc)} chars (max {MAX_DESC})")

        for match in _COMPETITOR_ABSOLUTE.finditer(text):
            fails.append(
                f"ABSOLUTE {p}: {match.group(0)!r} — a universal claim about "
                f"other tools. Name the ones it is true of, or name the "
                f"exception.")

        for hole in set(_UNRENDERED.findall(text)):
            fails.append(f"HOLE   {p}: unrendered placeholder {hole}")

        # A stray `}` at the top level makes a browser discard the next rule
        # and say nothing. Deleting a scroll-reveal rule left its closing brace
        # behind, which killed `a{color:var(--amber-light)}`, and every body
        # link on every article rendered in default browser blue on a near-black
        # page until someone looked at one. Counting braces is crude and it
        # catches exactly that.
        for css in _STYLE_BLOCK.findall(raw):
            clean = _CSS_COMMENT.sub("", css)
            opens, closes = clean.count("{"), clean.count("}")
            if opens != closes:
                fails.append(
                    f"CSS    {p}: {opens} '{{' vs {closes} '}}' — a stray brace "
                    f"silently drops the rule after it")

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

        hits = [phrase for phrase, rx in _BANNED_RE if rx.search(low)]
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
        print("PASS — voice, length, headings, placeholders, CSS, thin "
              "and duplicate checks clean")
        return 0
    print(f"\nFAIL ({len(fails)}):")
    for f in sorted(fails):
        print("  " + f)
    return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1] if len(sys.argv) > 1 else "site"))
