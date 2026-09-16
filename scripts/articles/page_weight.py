#!/usr/bin/env python3
"""How heavy is too heavy — the two findings `perf.page_weight` emits.

Sourced from `perf.page_weight` in
`backend/seo_engine/checks/performance.py`, its two thresholds at the top of
that file, `words.kb` which decides the unit they are printed in,
`fetcher.Fetcher.get` and `fetcher.MAX_BYTES` where the read is capped,
`extract.extract` which carries the cap across, `models.Page.body_truncated`
which records it, and `registry.AuditContext` which decides which pages are
weighed at all. Every one of those is in the shipped build (the commits that
added `body_truncated` and its "at least" wording, `4cfccac` and `599befc`,
are both ancestors of the 1.3.69 release commit `47c5a40` — checked with
`git merge-base --is-ancestor`, not assumed from the log order).

The test beside it records what went wrong:

  * tests/test_a_capped_read_is_a_floor_not_a_page_size.py

⚠️ FOUR PLACES WHERE THE REPO IS NARROWER THAN THE PHRASE "PAGE WEIGHT".
All four are stated on the page rather than smoothed over:

  1. It weighs the HTML DOCUMENT and nothing else. `page.html_bytes` is
     `len(resp.body)` — the decompressed markup — so images, CSS, JavaScript
     and fonts are not in the number at any point. The finding's own detail
     says "That is the HTML document alone, before images, CSS or JavaScript",
     and the common meaning of "page weight" (everything the browser pulls) is
     NOT what this check measures. A page may be light here and heavy to load.
  2. The registered check is one entry, `perf.page_weight`, and it emits two
     findings under two other ids at two severities: `perf.html_very_heavy`
     (MEDIUM) and `perf.html_heavy` (LOW).
  3. The LOW one is an `elif` AND is gated on a majority: it fires only when
     the moderate pages outnumber half of `ctx.ok_pages`, and never at all
     when any page tripped the MEDIUM branch. It is a site-shape finding, not
     a per-page one.
  4. Only `ctx.ok_pages` is weighed — HTML, 2xx, not an error, not a bot
     challenge, not a browser gate, not chrome-only, not an empty stand-in.
     A PDF is never in this finding, and neither is a page the crawl did not
     reach.

⚠️ AND THE UNIT IS DECIMAL. `words.kb` divides by 1000, and the thresholds are
written decimal (`HTML_VERY_HEAVY = 400_000`), so the KB in this finding is
1000 bytes. `facts.size_median_kb()` divides by 1024, which is right for the
2MB article it was written for and WRONG to stand beside these thresholds —
that mismatch is the defect `words.kb` exists to prevent. So this page does not
call those helpers: `_sample()` below re-counts the same published dataset on
the decimal divisor, and every figure here is on one divisor.

No typed figures and no typed dates: the thresholds, the read ceiling, the
sizes measured, and the dates the sources were read are all module-level
constants or derived from `data/page-size-2026-08.json`, and interpolated. The
shell commands are written brace-free so nothing rendered can look like an
unrendered placeholder.

The oversized page whose size Docket understated is described but not named.
It is a real business that never asked to be measured, and the number is the
whole of the point — see `verify_no_named_third_parties.py` for why that rule
exists, and note that it is a rule this page keeps voluntarily, because that
gate only inspects shipped exposure data and would not have caught a name here.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import facts as F  # noqa: E402
from render import render  # noqa: E402

#: The two thresholds, copied from `checks/performance.py` with their own
#: comment there: "Page weight thresholds (HTML document only, decompressed)."
HEAVY_BYTES = 150_000
VERY_HEAVY_BYTES = 400_000

#: Printed with `words.kb`, which is integer division by 1000. Both thresholds
#: are round in that unit, so these are exact rather than rounded.
HEAVY_KB = HEAVY_BYTES // 1000
VERY_HEAVY_KB = VERY_HEAVY_BYTES // 1000

#: The other divisor, named in the prose only to say it is not the one used.
BINARY_KB = 1024

#: `fetcher.MAX_BYTES` — "Read at most this many bytes of any single response."
#: Binary, because that is how it is written: `8 * 1024 * 1024`.
READ_CEILING_BYTES = 8 * 1024 * 1024
READ_CEILING_KB = READ_CEILING_BYTES // 1000
READ_CEILING_MB = f"{READ_CEILING_BYTES / 1_000_000:.1f}"
#: The same ceiling in the unit it was WRITTEN in. Both are needed in the
#: prose: the decimal figure is what a finding prints, the binary one is the
#: round number that gives the ceiling away.
READ_CEILING_MIB = READ_CEILING_BYTES // 1024 // 1024

#: The page that proved the ceiling could be printed as a measurement, from
#: the test named after it. Docket said `READ_CEILING_KB` KB; refetching the
#: same URL returned this many bytes.
TRUNCATED_PAGE_BYTES = 10_152_527
TRUNCATED_PAGE_MB = f"{TRUNCATED_PAGE_BYTES / 1_000_000:.1f}"
UNDERSTATED_MB = f"{(TRUNCATED_PAGE_BYTES - READ_CEILING_BYTES) / 1_000_000:.2f}"

#: The two sites in the render-cost note in `crawler.py`, quoted for the one
#: thing that note is certain of: the heavier document rendered FASTER. The
#: per-site times themselves are withdrawn in that comment as too noisy to
#: quote, so they are not quoted here either.
RENDER_LIGHT_KB = 136
RENDER_HEAVY_KB = 643

#: Dates the sources were read, so a re-reading is one edit.
CAP_FOUND_ON = "8 September 2026"
READ_ON = "16 September 2026"

#: `AuditContext.urls_of` caps the URL list attached to any finding; `count`
#: keeps the true total and the report says "showing N of M".
URL_CAP = 25


def _sample() -> dict:
    """The published homepage sample, re-counted on the engine's divisor.

    `data/page-size-2026-08.json` is the measurement behind
    `/learn/googlebot-2mb-limit/`. It is reused rather than re-measured, and
    every figure is recomputed here in decimal KB so it can stand beside
    decimal thresholds without the two-divisor mismatch `words.kb` documents.
    """
    data = F.page_size()
    sizes = [r["bytes"] for r in data["results"] if r.get("bytes")]
    return {
        "n": len(sizes),
        "median_kb": data["median_bytes"] // 1000,
        "over_heavy": sum(1 for b in sizes if b > HEAVY_BYTES),
        "over_very_heavy": sum(1 for b in sizes if b > VERY_HEAVY_BYTES),
        "measured": data["measured"],
    }


def page_weight() -> Path:
    s = _sample()
    body = f"""
<p class="lede">"How heavy should a page be?" has an answer in Docket, and it is two numbers:
{HEAVY_KB} KB and {VERY_HEAVY_KB} KB. Before you measure yourself against either of them, the
more useful thing to know is what those numbers are counting — because it is much less than the
phrase "page weight" normally means, and on the largest pages it is sometimes not a measurement
at all.</p>

<h2>What is actually on the scale</h2>

<p>The <code>perf.page_weight</code> check weighs <strong>the HTML document, decompressed, and
nothing else</strong>. Not the images. Not the stylesheets, the fonts, the JavaScript bundles or
anything those go on to request. The finding says so in its own detail text — "That is the HTML
document alone, before images, CSS or JavaScript" — and it is worth reading twice, because most
page-weight advice you will find means the total transfer a browser makes to paint the page, and
that is a different number, usually a much larger one.</p>

<p>So the two are not interchangeable in either direction. A page can sit comfortably under
Docket's lower threshold and still take a long time to load, because the weight is in a hero
image and a tag manager. A page can also trip the higher threshold while loading acceptably,
because the markup compresses to a fraction of its size on the wire. Docket counts the
decompressed bytes — what your server sent, after the transfer encoding is undone — which is the
size that matters for parsing and for byte-counted limits, and not the size that left the
server.</p>

<p>One more boundary, because it changes what a count means: only pages the crawl actually
reached are weighed, and only the ones that answered normally. The check reads
<code>ok_pages</code>, which is HTML pages with a 2xx status that were not errors, not bot
challenges, not browser gates, and not bodies that turned out to be the site's own repeated
navigation. A PDF never appears in this finding. Neither does a page nothing linked to.</p>

<h2>The two thresholds, and which one you have</h2>

<p>Docket registers this as one check and reports it as two findings, which are two different
claims:</p>

<ul>
<li><strong>A page over {VERY_HEAVY_KB} KB</strong> — <code>perf.html_very_heavy</code>, at
MEDIUM. Named pages, worst first, with the largest one printed by size. This fires on a single
page; one is enough.</li>
<li><strong>A site whose documents are generally large</strong> — <code>perf.html_heavy</code>,
at LOW. Pages between {HEAVY_KB} KB and {VERY_HEAVY_KB} KB, and it fires only if
<em>more than half</em> of the crawled pages are in that band.</li>
</ul>

<p>Two properties of that second one are easy to misread. It is an alternative, not an addition:
if any page tripped the MEDIUM branch, the LOW finding does not appear at all, so the absence of
"HTML documents are larger than they need to be" is not evidence that your other pages are
small. And it is a statement about the shape of the site rather than about any page — a handful
of fat templates on an otherwise lean site will not reach the majority and will not be reported
here.</p>

<p>The KB in both is decimal — a thousand bytes, not the {BINARY_KB} a lot of tools mean by the
same two letters. Docket publishes every measured size through one divisor, which exists because
two findings once described the same page in two units inside the same report, each correct in
its own file and disagreeing with its neighbour. If you convert Docket's KB yourself, divide by
a thousand and you will land where it did.</p>

<h2>When the number is a floor and not a size</h2>

<p>This is the part worth knowing before you act on any oversized-page finding, in Docket or
anywhere else.</p>

<p>Docket's fetcher stops reading a response at {READ_CEILING_MIB} mebibytes, which is
{READ_CEILING_MB} MB in the decimal unit its findings print. That is deliberate — the
comment at the constant calls it "~20x the 95th percentile HTML page; anything past it is a
download, not a document" — and it keeps one pathological URL from eating a crawl. The
consequence is the interesting bit. Whatever the page really weighs, the bytes Docket holds stop
there:</p>

<pre><code>if len(raw) &gt; self.max_bytes:
    raw = raw[: self.max_bytes]
    truncated = True</code></pre>

<p>For a while the checks never saw that flag. The fetcher recorded it, the extractor dropped
it, and the page-weight finding printed the ceiling as though it were the measurement. Found on
{CAP_FOUND_ON} on a large resources hub: Docket reported {READ_CEILING_KB} KB, and fetching the
same URL returned {TRUNCATED_PAGE_BYTES:,} bytes — about {TRUNCATED_PAGE_MB} MB. The report
understated the page by {UNDERSTATED_MB} MB while sounding precise to the kilobyte.</p>

<p><strong>The tell was that the figure was a round power of two.</strong> {READ_CEILING_KB} KB
is exactly {READ_CEILING_MIB} mebibytes, and no real page is that size by coincidence. If
a tool hands you a page size that is suspiciously round in binary — a ceiling number rather than
a measured one — check whether you are reading the page or reading the tool's limit. That
applies to whatever crawler you use, not only to this one.</p>

<p>What the shipped build does now is carry the flag across and change the sentence. One line in
the extractor:</p>

<pre><code>page.body_truncated = bool(getattr(resp, "truncated", False))</code></pre>

<p>and the finding prefixes its size with <em>"at least"</em> when that flag is set. So the
report reads "Largest: at least NNN KB on that URL" for a capped read, and prints the exact
figure with no hedge for every page read to the end. That partition is the point, and it has its
own test: saying "at least" on every heavy page would turn hundreds of exact, correct figures
into guesses.</p>

<p>Two caveats on the flag, both true of the code as it stands. It is set on the
<code>perf.html_very_heavy</code> finding, which is the one that prints a named page's size —
the LOW finding prints a count and no per-page figure, so there is nothing there to hedge. And
truncation has a second cause besides the ceiling: the fetcher reads against a wall-clock
deadline, and a server that answers quickly and then dribbles the body gets cut off at the
deadline with whatever arrived kept and marked truncated. A partial read is still worth
something — the alternative is discarding work already paid for — but it means "at least" can
mean "your server was slow" as well as "your page was enormous".</p>

<h2>So how heavy is too heavy?</h2>

<p>Treat {VERY_HEAVY_KB} KB as a line worth investigating rather than a rule, because the web
does not respect it. We measured the homepages of the sites in our own sample list on
{s['measured']} for a different article: of the {s['n']} that answered, <strong>{s['over_heavy']}
are over {HEAVY_KB} KB and {s['over_very_heavy']} are over {VERY_HEAVY_KB} KB</strong>, and the
median is {s['median_kb']} KB of HTML. The median well-known homepage is past Docket's upper
threshold. Those thresholds are strict on purpose, and a finding at MEDIUM is an invitation to
look rather than a verdict that your site is broken.</p>

<p>The honest reason to care is not a ranking penalty, and this page will not claim one. The
finding's own detail says a heavy document "delays the first paint by seconds" on a phone
connection — an inference from the size, not something Docket timed, and worth weighing
accordingly. The repository is blunter about this elsewhere: a note in the crawler records that
of two sites measured with the shipped renderer, the one serving {RENDER_LIGHT_KB} KB rendered
<em>slower</em> than the one serving {RENDER_HEAVY_KB} KB, and concludes "do not tune this cap
against document size". Whatever dominates the time is script execution and the network
waterfall, and it has not been isolated.</p>

<p>What document size does control, exactly and without inference, is a byte budget:
<a href="/learn/googlebot-2mb-limit/">Googlebot stops reading at 2MB</a>, headers included, and
hands the fragment it got to indexing as though it were the whole file. That is a different
check with a different threshold, and it is the one where a large document silently costs you
something. If you only read one of the two pages, and your documents are genuinely large, read
that one.</p>

<h2>Measuring it yourself</h2>

<p>Docket's number is reproducible in one line. This is the count it takes — the decompressed
HTML document, nothing referenced:</p>

<pre><code>curl -sS --compressed https://example.com/ | wc -c</code></pre>

<p>Drop <code>--compressed</code> and you get the bytes as they would arrive if your visitor's
browser did not negotiate an encoding. Ask for gzip explicitly and count again, and the
difference between the two is what compression is saving you on this page:</p>

<pre><code>curl -sS -H 'Accept-Encoding: gzip' https://example.com/ | wc -c</code></pre>

<p>If those two numbers are the same, the document is not being compressed at all, which is a
separate finding and a much cheaper fix than trimming markup —
<a href="/how-to/fix-compression-and-caching/">how to fix compression and caching headers</a>
covers it. Doing that first is the right order: compression changes what the visitor waits for
without changing a line of your templates.</p>

<h2>What actually makes a document heavy</h2>

<p>The check's own remedy names the usual causes, and after a few hundred crawls they are
reliably the same three:</p>

<ol>
<li><strong>Inlined CSS and JavaScript.</strong> Every page carries its own copy, so nothing is
cached across pages and the same bytes are paid for again on every navigation. Moving them into
linked files removes them from the document entirely.</li>
<li><strong>Base64 images inlined into the markup.</strong> An encoded image is larger than the
file it came from, and it lands in the one budget that counts here.</li>
<li><strong>A whole listing rendered into one page.</strong> An entire catalogue, or navigation
that prints thousands of links before the content starts. The fix is pagination, and it usually
helps more than the byte count suggests.</li>
</ol>

<p>The check's fix text is one sentence for the first and third of those: move inline blocks to
cached external files, and paginate long listings. Note what that does to the second finding as
well — external files are cached across pages, so the site-wide LOW finding tends to close on
the same edit.</p>

<p>One caveat if your pages are built by JavaScript: the document Docket weighed is the one your
server sent, before any of it ran.
<a href="/learn/javascript-rendering/">What JavaScript rendering costs you</a> covers why the
served document and the finished page can be very different sizes, and which one each tool is
looking at.</p>

<h2>Reading your own finding</h2>

<p>The list attached to any finding is capped at {URL_CAP} URLs while the count beside it keeps
the true total, so "showing {URL_CAP} of a larger number" means exactly that. On the MEDIUM
finding that list is sorted heaviest first, so the pages you cannot see are the smaller ones;
the LOW finding lists its band in crawl order. Start at the top, check whether the
largest figure carries an "at least", and if it does, fetch that URL yourself before deciding
how bad it is. Everything else on the list is a measurement you can trust to the kilobyte.</p>

<p><a class="btn" href="/download/">Download Docket</a></p>
"""
    return render(
        cat="learn", slug="page-weight",
        title="Page weight and SEO: how heavy is too heavy?",
        desc=(f"A Docket audit of your site flags an HTML document over {VERY_HEAVY_KB} KB. "
              f"What that counts, what it leaves out, and when a size is a floor "
              f"rather than a measurement."),
        h1="Page weight: how heavy is too heavy?",
        crumb='<a href="/">Docket</a> / <a href="/learn/">Learn</a> / Page weight',
        body=body,
        faq=[
            ("What counts as page weight in Docket?",
             "The HTML document on its own, decompressed, and nothing it references. Images, "
             "stylesheets, fonts and JavaScript bundles are not in the number, so a page that "
             "passes this check can still be slow to load. Most page-weight advice means the "
             "total a browser downloads, which is a different and usually much larger figure."),
            ("How heavy is too heavy for a web page?",
             "Docket draws two lines on the HTML document: one at a hundred and fifty "
             "kilobytes, which it only reports when more than half the crawled pages sit in "
             "that band, and one at four hundred kilobytes, which it reports for a single "
             "page. Both "
             "are strict compared with the real web — the median homepage in our own sample of "
             "well-known sites is past the higher of the two."),
            ("Why does my report say 'at least' before a page size?",
             "Because the crawler stopped reading before the page ended, so the figure is the "
             "point it stopped at rather than the size of the document. That happens when a "
             "response passes the fetcher's eight-mebibyte read ceiling, and also when a slow "
             "server is still dribbling the body when the deadline expires. Fetch the URL "
             "yourself to get the real size."),
            ("Does page weight affect Google rankings?",
             "This page does not claim a ranking penalty, because Docket has not measured one "
             "and the finding's own note about delaying first paint is an inference from the "
             "size rather than something timed. What document size provably controls is "
             "Googlebot's byte budget: it reads a fixed amount of any URL and indexes that "
             "fragment as if it were the whole file."),
            ("Is a large HTML file the same as a slow page?",
             "No, and the repository records a case against assuming it. Of two sites measured "
             "with the shipped renderer, the one serving roughly a sixth of the markup rendered "
             "slower than the heavier one, and the note concludes that document size should not "
             "be used to predict render cost. Script execution and the network waterfall "
             "dominate, and neither is visible in a byte count."),
        ],
    )


BUILDERS = [page_weight]


def build_all() -> list:
    return [b() for b in BUILDERS]


if __name__ == "__main__":
    print(page_weight())
