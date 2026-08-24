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

import sys as _sys
from pathlib import Path as _Path
_sys.path.insert(0, str(_Path(__file__).resolve().parent))
import app_path  # noqa: E402

import re
import sys
import pathlib
from pathlib import Path
from typing import Iterator, List, Tuple

ROOT = Path(__file__).resolve().parent
ARTICLES = ROOT / "articles"

#: Numbers that are constants of the world rather than measurements of it.
#: A reason is required for every entry, and "it looked fine" is not one.
ALLOWED = {
    # -- standards, specs and versions ------------------------------------
    # -- figures read off a dated specimen image ---------------------------
    # These two describe the audit screenshot on the homepage, not the product's
    # current behaviour. They CANNOT be interpolated: the image is a frozen
    # artifact from a named run against builtbykerr.com on 2026-08-17, and a
    # caption that silently tracked a live dataset would eventually describe a
    # picture that shows something else — the exact failure this file prevents,
    # pointed the wrong way.
    #
    # The coupling is the safeguard: if site/assets/real-audit-builtbykerr.webp
    # is ever regenerated, these numbers must be re-read off the new image and
    # changed here. That is a deliberate speed bump, not an oversight.
    "90": ("the overall grade in the audit screenshot on the homepage — read "
           "off the image, which is a specimen from a real run against "
           "builtbykerr.com on 2026-08-17, not a live figure"),
    "58": ("the Local business SEO lane score in that same screenshot. Quoted "
           "because it is the least flattering number in our own report and "
           "the caption's point is that Docket does not hide it"),
    # -- figures read off the dated HERO RECORDING -------------------------
    # Same rule as the screenshot above, for site/assets/app-demo.{mp4,webm}:
    # a screen recording of Docket auditing docketseo.app, captured 2026-08-18
    # through the e2e harness against the SHIPPED sidecar. They describe that
    # recording and nothing else, so interpolating them from a live dataset
    # would eventually caption a video that shows different numbers.
    #
    # If the recording is re-shot, re-read all three off the new footage.
    "57": ("pages crawled in the hero recording — read off the footage, which "
           "is a real run against docketseo.app on 2026-08-18"),
    "35": ("seconds that same recorded run took, read off the same footage"),
    "94": ("the score that recorded run produced. Quoted because the caption's "
           "claim is that this is the app running, not a render of it"),
    "96": ("the check count visible in that recording's status bar. NOT the "
           "product's count, which is derived from data/checks.csv and is "
           "higher — the video is frozen at what shipped on 2026-08-18. It is "
           "quoted only in a source comment warning the next person not to "
           "soften the live prose to match a stale video; if that number ever "
           "appears in PROSE, the video is out of date and the answer is to "
           "re-shoot it, never to change the sentence"),
    "2.30": ("the glibc floor of the Linux build, measured with objdump over "
             "the shipped binary and its bundled libpython — the highest "
             "GLIBC_ symbol version either requires"),
    "2.14": ("what the Linux launcher alone requires; quoted beside 2.30 to "
             "show which half of the bundle sets the floor"),
    "9309": "RFC 9309, the robots.txt standard",
    "2.0": ("a hypothetical future major version of Docket, in the sentence "
            "explaining that 1.x upgrades are free and whether a 2.0 would be "
            "paid has not been decided. A version number in prose, not a "
            "measurement — there is no dataset it could be interpolated from, "
            "and it cannot go stale because it refers to something that does "
            "not exist yet"),
    "2000": ('Google\'s published URL Inspection API quota, quoted verbatim as '
             '"2000 QPD" — their string, without the thousands separator, so it '
             "is a different literal from the 2,000 above"),
    # -- the title-rewrite study, re-verified 2026-08-10 -------------------
    # Read from zyppy.com/seo/google-title-rewrites/ on 2026-08-10: "80,959
    # title tags across 2370 sites in early 2022 from across the globe", and
    # "Google rewrote 61.6% of the titles". Their numbers, not ours.
    "80,959": "titles in the Zyppy title-rewrite study, read 2026-08-10",
    "2,370": "sites in that same study, same reading",
    "61.6": "the share of titles it found rewritten, same reading",
    # -- Semrush, read from their own pages and quoted in VERIFIED ----------
    "20,000": ("Semrush's per-audit crawl allowance on Pro and Guru, from "
               "their KB article 338, quoted and linked in comparisons.VERIFIED"),
    "300,000": ("Semrush's monthly page allowance on Guru, same KB article and "
                "the same VERIFIED entry"),
    "1,000,000": ("Semrush's monthly page allowance on Business, same source"),
    "117.33": ("Semrush's entry plan billed annually, $117.33/mo, from their "
               "pricing page as quoted in VERIFIED"),
    "1,668": ("$139 x 12 — arithmetic on the monthly price above, shown in the "
              "prose so a reader can check the multiplication"),
    # -- Google Search Console's published API limits ----------------------
    "2,000": ('the URL Inspection API quota, "2000 QPD", from Google\'s '
              "published limits page and quoted in VERIFIED"),
    "600": ('the same page\'s "600 QPM" per-property limit'),
    # -- hypotheticals in prose, not measurements of anything --------------
    "4,000": ("a hypothetical page count in an explanation of reach "
              "compression — 'a trivial issue that happens to appear on 4,000 "
              "pages'. Not a measurement of any site"),
    "5,000": ("a hypothetical site size used to show that a 2,000-a-day API "
              "quota cannot inspect it in a day. Arithmetic on a published "
              "quota, not a measurement"),
    "7": ("'page 7 of the archive' — an example of a paginated URL winning the "
          "wrong query. An illustration, not a count"),
    "60": ("the 'about sixty characters' rule of thumb these pages exist to "
           "correct; quoted as the received advice, not asserted as a limit"),
    "301": ("the HTTP status code for a permanent redirect, RFC 9110. A "
            "constant of the protocol, not a measurement of anything"),
    "302": ("the HTTP status code for a temporary redirect, RFC 9110. Named "
            "beside 301 because using it here is the mistake being warned "
            "about"),
    "100,000": ("Ahrefs' Lite plan crawl-credit allowance, read from "
                "ahrefs.com/pricing on 2026-08-10 and linked on the page"),
    "500,000": ("Ahrefs' Standard plan crawl-credit allowance, same source "
                "and date"),
    "1,500,000": ("Ahrefs' Advanced plan crawl-credit allowance, same source "
                  "and date"),
    "139": ("Screaming Frog's Log File Analyser licence, $139 per year, read "
            "from their own pricing page on 2026-08-07 and linked in the "
            "prose. A competitor's price for a SEPARATE product from the SEO "
            "Spider, so it does not belong in competitors.csv, which is keyed "
            "on the main products."),
    "1,000": ("The free tier of that same Log File Analyser: 1,000 log events. "
              "Quoted from their pricing page and linked beside it."),
    "24": ("The threshold of the DELETED palette-size rule — brand.visual_"
           "consistency fired above 24 distinct colours. /learn/brand-"
           "consistency/ explains why that rule died when Docket could finally "
           "read real stylesheets. A historical fact about a rule that no "
           "longer exists cannot be derived from a dataset, and it must not "
           "silently become a current figure either."),
    "49": ("Near-identical colour PAIRS reported on this site's own 26-colour "
           "palette while the alpha channel was being ignored — the bug that "
           "made every opacity variant look like drift. An observation from a "
           "debugging run that no longer reproduces, quoted in the article as "
           "the size of the mistake."),
    "2.1.0": ("SARIF 2.1.0 — the OASIS spec version Docket emits and GitHub "
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
    "12": "macOS 12, the minimum version Docket supports",
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


#: The engine, for facts the site restates because it cannot import it.
ENGINE = app_path.engine()


def _score_band_drift() -> List[str]:
    """The site's mockup bands against the engine's SCORE_BANDS.

    The homepage draws a product mockup whose lane colours must be the ones the
    product would draw. They were hand-picked and two were wrong — a lane at 84
    drawn green when the boundary is 85, and a lane at 63 drawn in the brand
    indigo rather than a severity colour. Both flattered the product.

    They are computed now, but the thresholds are still a second copy of the
    engine's, so this fails the build when the two disagree.

    Imports the engine rather than pattern-matching its source. The first
    version used a regex and read two of the three bands, reporting a drift that
    did not exist — a gate whose failures cannot be trusted is worse than none.
    Silently skips when the engine is absent: the site must stay buildable on
    its own, and a check that cannot run says so rather than passing.
    """
    backend = ENGINE.parent
    if not (ENGINE / "scoring.py").is_file():
        print(f"  note: engine not present at {ENGINE}, score bands unchecked")
        return []
    sys.path.insert(0, str(backend))
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent / "articles"))
    try:
        from seo_engine.scoring import SCORE_BANDS
    except Exception as exc:                                  # noqa: BLE001
        return [f"  cannot import the engine's SCORE_BANDS ({exc}) — the site "
                f"restates them and can no longer check itself"]
    from home import _BANDS

    engine = [(float(f), n) for f, n in SCORE_BANDS]
    site = [(float(f), n) for f, n in _BANDS]
    if [f for f, _ in engine] != [f for f, _ in site]:
        return [f"  score bands drifted: engine {[f for f, _ in engine]}, "
                f"home.py {[f for f, _ in site]}"]
    return []


def _competitor_annual_sanity() -> List[str]:
    """The annual figures must come from the note's ANNUAL numbers, if it has any.

    `_annual` used to regex every dollar amount out of a human-written price
    note and multiply them all by 12 whenever `/mo` appeared anywhere in the
    string. Three of ten notes named both units, so half their numbers got the
    wrong one — Sitebulb's cheapest tier was published at $216/yr when their
    own note put the yearly plan at $180, in the table that exists to argue
    Docket is cheaper. (That $180 was itself undated. Re-read on 2026-08-10 the
    monthly rates are $18 and $42 and the yearly totals are not in the page at
    all, so the row now carries $184–$428 derived from the 15% those pages
    advertise. One note names both units today.)

    **The first version of this gate did not catch that**, which is the reason
    it is written this way. It allowed "any number in the note, or that number
    x12" — and $216 is $18 x 12, so the wrong value passed. Magnitude is not
    the test; the unit is. Each amount is read with the unit that follows it,
    and a note that states annual prices must have its annual columns taken
    from those, not from the monthly ones multiplied up.
    """
    import csv as _csv

    out: List[str] = []
    path = pathlib.Path(__file__).resolve().parent.parent / "data" / "competitors.csv"
    # $N followed by its unit: /mo, /yr, "annual", "lifetime", or nothing.
    amount = re.compile(r"\$([\d,]+)\s*(?:-\s*\$?[\d,]+)?\s*(/mo|/yr|annual|lifetime)?",
                        re.I)
    for row in _csv.DictReader(path.open()):
        note, slug = row["price_note"], row["slug"]
        annual, monthly = set(), set()
        for m in re.finditer(r"\$([\d,]+)", note):
            tail = note[m.end():m.end() + 24].lower()
            n = int(m.group(1).replace(",", ""))
            # Whichever unit token comes FIRST wins. Fixed precedence read
            # "$422/mo billed annually" as an annual figure, because the tail
            # contains both tokens — the unit is the one attached to the
            # number, which is the nearer one.
            pos = {tok: tail.find(tok) for tok in ("/mo", "/yr", "annual", "lifetime")}
            present = {t: i for t, i in pos.items() if i >= 0}
            unit = min(present, key=present.get) if present else ""
            if unit == "lifetime":
                continue                      # a one-time price is not annual
            if unit in ("/yr", "annual"):
                annual.add(n)
            elif unit == "/mo":
                monthly.add(n)
            else:
                # part of a range: takes the unit of the amount after it
                annual.add(n); monthly.add(n)
        allowed = (annual if annual else {n * 12 for n in monthly}) | {0}
        if annual and monthly:
            allowed |= {0}                    # a mixed note must use the annual side
        for field in ("annual_low", "annual_high"):
            value = int(row.get(field) or 0)
            if value not in allowed:
                out.append(
                    f"PRICE  {slug}.{field} = {value:,} does not come from the "
                    f"{'annual' if annual else 'monthly x12'} figures in "
                    f"\"{note}\" (expected one of {sorted(allowed)})")
        if int(row.get("annual_low") or 0) > int(row.get("annual_high") or 0):
            out.append(f"PRICE  {slug}: annual_low exceeds annual_high")
        if not row.get("annual_basis"):
            out.append(f"PRICE  {slug}: no annual_basis recorded")
    return out


def _price_stamp_integrity() -> List[str]:
    """A date and a source are one fact, and half of it renders as a lie.

    `price_note_html` prints `Name (source)` as a link per stamped competitor.
    A row stamped with a date but no URL renders an anchor to `""` — which is
    the current page — so the reader clicks "source" and is told the price
    sources itself. A row with a URL and no date is worse: it is dropped from
    the caveat entirely and counted among the ones "last confirmed earlier",
    while carrying the very evidence that says otherwise.

    Neither is hypothetical bookkeeping. Seven rows were stamped in one pass on
    2026-08-10, by a script, from a dict of slugs to URLs; a slug typo'd in one
    dict and not the other produces exactly these halves.
    """
    import csv as _csv

    out: List[str] = []
    path = pathlib.Path(__file__).resolve().parent.parent / "data" / "competitors.csv"
    for row in _csv.DictReader(path.open()):
        slug, when, src = row["slug"], row["price_checked"], row["price_source"]
        if when and not re.fullmatch(r"\d{4}-\d{2}-\d{2}", when):
            out.append(f"PRICE  {slug}: price_checked {when!r} is not YYYY-MM-DD")
        if when and not src.startswith("https://"):
            out.append(f"PRICE  {slug}: dated {when} but price_source is "
                       f"{src!r}; the caveat renders a link to nowhere")
        if src and not when:
            out.append(f"PRICE  {slug}: has a source but no date, so it is "
                       f"counted as unchecked while holding the evidence")
    return out


def _caveat_branches() -> List[str]:
    """Exercise the caveat's dead branches, because dead is where the bugs sit.

    With ten of ten prices dated, the "some were not checked" sentence never
    renders. It rendered "The other 1 were last confirmed earlier" — found by
    calling the function with stubbed data rather than by reading the site,
    because the site cannot currently produce it. It becomes reachable the day
    an eleventh competitor is added, which is the day nobody is looking at this
    line.

    Same defect as the "Only 0%" in the audit engine's exposure summary: a
    template that was never run with the awkward number in it.
    """
    import importlib  # noqa: PLC0415

    out: List[str] = []
    render = importlib.import_module("render")
    saved = render.COMPETITORS

    def caveat(rows) -> str:
        render.COMPETITORS = rows
        return re.sub(r"<[^>]+>", "", render.price_note_html())

    def row(name, when, src="https://example.test/pricing"):
        return {"name": name, "price_checked": when,
                "price_source": src if when else ""}

    try:
        one = caveat({"a": row("Alpha", "2026-08-10"), "b": row("Beta", "")})
        if "other 1 were" in one or "One other was" not in one:
            out.append(f"CAVEAT one unchecked competitor reads: {one.strip()!r}")

        two = caveat({"a": row("Alpha", "2026-08-10"), "b": row("Beta", ""),
                      "c": row("Gamma", "")})
        if "The other 2 were" not in two:
            out.append(f"CAVEAT two unchecked competitors reads: {two.strip()!r}")

        same = caveat({"a": row("Alpha", "2026-08-10"),
                       "b": row("Beta", "2026-08-10")})
        if same.count("2026-08-10") != 1:
            out.append("CAVEAT one shared date is printed more than once")

        mixed = caveat({"a": row("Alpha", "2026-08-10"),
                        "b": row("Beta", "2026-07-01")})
        if "2026-07-01" not in mixed or "2026-08-10" not in mixed:
            out.append("CAVEAT differing dates are not both shown")

        none = caveat({"a": row("Alpha", "")})
        if "none checked recently" not in none:
            out.append(f"CAVEAT nothing checked reads: {none.strip()!r}")
    finally:
        render.COMPETITORS = saved
    return out


def main() -> int:
    problems: List[str] = (_score_band_drift() + _competitor_annual_sanity()
                           + _price_stamp_integrity() + _caveat_branches())
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
