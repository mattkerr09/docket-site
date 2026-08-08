#!/usr/bin/env python3
"""Find published numbers that are typed rather than derived.

    python3 scripts/verify_numbers.py

The Index published "30% of major sites block an AI search crawler" over a
dataset that said 25 of 98. Nothing was lying: a correction updated the prose
that recomputes from records and left the stored aggregate alone, and the
headline read the aggregate. Both numbers were in the repo. They disagreed for
a week and no test could have noticed, because both were internally
consistent.

The general shape of that bug is a number that exists in prose *and* in data.
So this does not compare the two — it looks for prose numbers that have no
derivation at all, because those are the ones that cannot be kept in step. A
figure interpolated from a dataset goes stale the moment the dataset is rebuilt
and the page is not; a figure typed into a sentence goes stale silently and
stays that way.

Every literal it finds is either a real drift risk or belongs in ALLOWED with a
reason. Nothing here is clever: the value is that the list is short enough to
read, and that adding to it is a deliberate act.

**Known gap.** It matches digits, so a figure spelled out in words — "none of
those five" next to a derived count of 5 — walks straight past it. That was
caught by eye on the 2MB article and the sentence now interpolates. Closing it
properly means a number-word list and a lot of false positives on "one",
"two" and "second", which is a worse trade than reading the prose.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Iterator, List, Tuple

ROOT = Path(__file__).resolve().parent
ARTICLES = ROOT / "articles"

#: Numbers that are constants of the world rather than measurements of it.
#: A reason is required for every entry, and "it looked fine" is not one.
ALLOWED = {
    # -- standards, specs and versions ------------------------------------
    "9309": "RFC 9309, the robots.txt standard",
    "24": ("The threshold of the DELETED palette-size rule — brand.visual_"
           "consistency fired above 24 distinct colours. /learn/brand-"
           "consistency/ explains why that rule died when Scout could finally "
           "read real stylesheets. A historical fact about a rule that no "
           "longer exists cannot be derived from a dataset, and it must not "
           "silently become a current figure either."),
    "49": ("Near-identical colour PAIRS reported on this site's own 26-colour "
           "palette while the alpha channel was being ignored — the bug that "
           "made every opacity variant look like drift. An observation from a "
           "debugging run that no longer reproduces, quoted in the article as "
           "the size of the mistake."),
    "2.1.0": ("SARIF 2.1.0 — the OASIS spec version Scout emits and GitHub "
              "ingests. A version number in a format name, not a measurement; "
              "it changes when OASIS publishes a new spec, not when we "
              "measure anything."),
    "2.2.1": "RFC 9309 section number",
    "5321": "RFC 5321, the SMTP standard — cited for the implicit-MX fallback",
    "2606": "RFC 2606, which reserves .example/.invalid/.test",
    "365": "Microsoft 365, a product name rather than a measurement",
    # The homepage's results mock is a picture of the interface, not a claim
    # about anyone's site. Its severity chips are part of the illustration.
    "9": "severity chip in the homepage's UI replica, not a measurement",
    "2010": ("Screaming Frog's founding year, quoted from their own about page: "
             "'a UK search marketing agency founded in 2010'. Linked in the prose."),
    "5.1": "RFC 5321 section number",
    "25": "TCP port 25, where SMTP is not answering on our address record",
    "0.85": "PageRank damping factor from the original paper",
    "5.0": "Mozilla/5.0, part of every user-agent string ever written",
    "537.36": "AppleWebKit build in the user-agent strings we quote",
    "12": "macOS 12, the minimum version Scout supports",
    "2": "'the first two sentences', '.2MB', ordinals",
    "3": "ordinals and list counts in prose",
    "1": "ordinals",
    "4": "ordinals",
    "5": "ordinals, 'the five pages that make you money'",
    "10": "'ten pages by default' — the render sample size",
    "0": "'0 characters', ordinals",
    # -- dates -------------------------------------------------------------
    "2024": "year in a dated claim", "2025": "year in a dated claim",
    "2026": "year in a dated claim", "2023": "year in a dated claim",
    "2011": "U+2011, a Unicode codepoint",
    "8896518": "Anthropic support article number",
    # -- third-party figures we quote and cannot derive --------------------
    "137,210": "domains in Ahrefs' llms.txt study — their number, not ours",
    "97": "97% of llms.txt files unrequested — Ahrefs' finding",
    "1.1": "1.1% of requests from AI retrieval bots — Ahrefs' finding",
    "170": "Ahrefs' own '170+ SEO issues' claim",
    "140": "Semrush's own '140+ checkpoints' claim",
    "500": "Screaming Frog's free-tier URL limit, from their pricing page",
    "10,000": "the Tranco list size we sampled — a chosen constant",
    "80": "'~80 LocalBusiness subtypes', schema.org",
    "25": "rich result types in Google's gallery",
    # -- HTTP status codes. Constants of the protocol. --------------------
    "200": "HTTP 200", "401": "HTTP 401", "403": "HTTP 403",
    "404": "HTTP 404", "405": "HTTP 405", "406": "HTTP 406",
    "429": "HTTP 429", "451": "HTTP 451", "503": "HTTP 503",
    "95": "95% confidence interval — a convention, not a measurement",
    "100": "a percentage ceiling, or a score out of 100",
    # -- measurements taken once, by hand, and named as such ---------------
    "2,068": "notion.so rendered character count, measured 2026-08-06",
    "106": "notion.so rendered link count, measured 2026-08-06",
    "54": "scripts GTM injected on notion.so, measured 2026-08-06",
    "112": "the render helper is 112 KB — a build artefact, checked by hand",
    "9.8": "the Common Crawl link graph is 9.8 GB",
    "117,963,409": "domains in the Common Crawl release; the app reads this "
                   "live, the prose quotes the release we measured against",
    "418": "HTTP 418, quoted because Stack Overflow really serves one",
    "2.4": "'structured data sits at 2.4 MB' — an invented example of a page "
           "past the cutoff, chosen to be just over it",
    "2.48": "where cnn.com's inline SVG <title> sits. Measured, and preserved "
            "as the reading our own bug produced — the current figure beside "
            "it is derived",
    "400,000": "'which of my 400,000 URLs are heavy' — an invented crawl size",
    "127.0.0.1": "the loopback address",
    "0.0125": "an illustrative raw PageRank value, chosen to be awkward",
    "0.5": "the 0.5x equity threshold this site recommends — a rule of thumb "
           "we chose, not a measurement",
    "412": "an invented example of a Screaming Frog row",
    "400": "an invented example of a 400-row spreadsheet",
    "40,000": "invented LinkedIn follower count in a worked example",
    "40": "'lose 40% of your traffic' — the invented forecast we refuse to "
          "make, and 'a survey of 40 customers' as an example of small data",
    "300": "'close to 300 sites' — Awario's crawlers, excluded from the "
           "population, so the exact figure is not in the shipped dataset",
    "89": "check 89, ai.edge_access — an identifier, not a measurement",
    # -- historical values, true of a moment we name in the sentence -------
    "1.25": "the download page's share BEFORE the fix, stated as history",
    "5.56": "the average share at that time, stated as history",
    "0.22": "the download page's index before the fix, stated as history",
    "23": "'the site had 23 pages' — the moment the stale figure was caught",
    "30": "a law firm crawl that reached 30 of 935 pages, a one-off anecdote",
    "935": "pages that law firm actually had", "25": "attorney pages in it",
    # The exposure portfolios are shipped as datasets now and read through
    # facts.py, so none of their figures need to live here.
    "32": "'the deli scored media on 32 pages' — the count BEFORE the fix, "
          "stated as history next to the current figure, which is derived",
    "85": "'0.85 does not mean 85% fewer visits' — explaining the scale, and "
          "the 85 sites in the entity survey where it is interpolated",
    "50": "sites declaring an organisation, interpolated where it matters",
    "41": "sites declaring sameAs, interpolated where it matters",
}

#: Numbers inside these HTML constructs are structural, not claims.
_SKIP_LINE = re.compile(
    r"^\s*(?:<(?:/?(?:h[1-6]|div|table|thead|tbody|tr|th|td|ul|ol|li|pre)\b)"
    r"|#|@|\"\"\")", re.I)

#: Prose lives in a triple-quoted string that is either assigned or returned.
#:
#: This matched only `body = """..."""` for months, and home.py returns its
#: sections directly — `return f"""..."""` — so THE ENTIRE HOMEPAGE was never
#: scanned. It was the one page guaranteed to be read by everybody. An
#: unverified "14 TiB" claim about Common Crawl's archives survived there for
#: weeks after being deleted from build.py for being unverifiable, because the
#: sweep that removed it could not see the file.
#:
#: A docstring is also triple-quoted, and is deliberately not matched: it is
#: neither assigned nor returned, so the anchors below exclude it.
_TRIPLE = re.compile(
    r'(?:(?:body|BODY|intro|CTA)\s*=|return)\s*(f?)"""(.*?)"""', re.S)
#: An HTML attribute value. Coordinates, font sizes and rgba() colours are
#: markup, not claims about the world — the homepage's inline SVG alone put
#: eight of them in front of a reader, and a list you skim is a list you stop
#: reading. Masked for the same reason <code> is.
_ATTR = re.compile(r'\b[a-zA-Z-]+="[^"]*"')

#: Inside <code> is a literal being quoted — a token, a version, a snippet.
#: `ChatGPT-User/2.0` is the subject of a sentence, not a claim about the world.
_CODE = re.compile(r"<code>.*?</code>", re.S)
#: An f-string hole. Everything inside one is derived, which is the point.
_HOLE = re.compile(r"\{[^{}]*\}")
#: A number, without swallowing the punctuation after it. The first version
#: matched "401," and "Section 2.2.1" as "2.2", which put six tokenisation
#: artefacts in front of a reader deciding whether each was a real risk — and a
#: list you skim is a list you stop reading.
_NUMBER = re.compile(
    r"(?<![\w.#-])(\d{1,3}(?:,\d{3})*(?:\.\d+)*|\d+(?:\.\d+)*)(?![\w.-])")


def _literals(path: Path) -> Iterator[Tuple[int, str, str]]:
    src = path.read_text()
    for match in _TRIPLE.finditer(src):
        start_line = src[: match.start()].count("\n") + 1
        body = match.group(2)
        # Blank out every interpolation before looking for numbers: a figure
        # inside {} is derived by construction and is exactly what we want.
        masked = _ATTR.sub(" ", _CODE.sub(" ", _HOLE.sub(" ", body)))
        for offset, line in enumerate(masked.splitlines()):
            if _SKIP_LINE.match(line):
                continue
            for number in _NUMBER.findall(line):
                if number in ALLOWED:
                    continue
                yield start_line + offset, number, line.strip()[:96]


def main() -> int:
    problems: List[str] = []
    # build.py carries the hub entry summaries, which are article prose on a
    # published page and were not being scanned. "Tranco top 1,500" was typed
    # into one and sailed through, which is the exact bug this file exists for.
    scanned = sorted(ARTICLES.glob("*.py")) + [ARTICLES.parent / "build.py"]
    for path in scanned:
        for line_no, number, context in _literals(path):
            problems.append(
                f"  {path.name}:{line_no}  {number!r}\n      {context}")

    if not problems:
        print(f"PASS — every number in article prose is derived or allowed "
              f"({len(ALLOWED)} allowed constants)")
        return 0
    print(f"FAIL — {len(problems)} typed number(s) in article prose.\n")
    print("Each is a figure that cannot go stale loudly. Interpolate it from "
          "the dataset, or add it to ALLOWED with a reason.\n")
    for problem in problems:
        print(problem)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
