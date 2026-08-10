#!/usr/bin/env python3
"""How to find and fix duplicate title tags.

The reason this page needed a VERIFIED block and the HTTPS how-to did not: that
one is written from our own server's behaviour, which we could read directly.
This one is entirely about what *Google* does, and title-tag advice is the most
folklore-heavy corner of SEO there is. "Keep it under 60 characters" is repeated
everywhere and is not what Google's documentation says. A page whose argument is
that the received wisdom is wrong cannot itself be received wisdom, so every
statement about Google's behaviour below is read from a named source on a named
date and nothing else is stated as fact.

Two claims deliberately did NOT make the page because they could not be sourced
to that standard:

  - "There is no duplicate content penalty." Widely attributed to Google and the
    sentence it comes from is no longer in the canonicalisation documentation.
    What replaced it is narrower and checkable — the spam policies enumerate
    what can trigger an action, and duplicate titles are not enumerated — so
    that is what the page says instead. Weaker claim, real source.

  - "Matching the title to the H1 cuts the rewrite rate to about 20%." The
    figure circulates; Zyppy's own page says only that matching "typically
    dropped the degree of rewriting", unquantified. The page keeps the
    direction and drops the number.

The two headline rewrite figures disagree with each other (87% vs 61.6%) and
both are on the page with the reason they disagree. Picking whichever one suits
the argument is how this topic got its folklore in the first place.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from render import N_CHECKS, render  # noqa: E402

#: The day every claim below was read from the source named beside it.
CHECKED_ON = "2026-08-10"
CHECKED_ON_HUMAN = "10 August 2026"

#: (what was read, where it was read). Same contract as comparisons.VERIFIED:
#: anything not in here is not stated on the page as a fact about Google.
VERIFIED: list[tuple[str, str]] = [
    ("there is no limit on the length of a title element, and the title link is "
     "truncated in results as needed, typically to fit the width of the device",
     "https://developers.google.com/search/docs/appearance/title-link"),
    ("Google may generate a title link from anchors, on-page text or other sources "
     "when it detects an issue with the one on the page, and asks for distinct "
     "descriptive text in the title element of every page on a site",
     "https://developers.google.com/search/docs/appearance/title-link"),
    ("Google put its use of the HTML title element at around 87% after a September "
     "2021 revision, up from the over-80% figure given when the system launched",
     "https://developers.google.com/search/blog/2021/09/more-info-about-titles"),
    ("a study of 80,959 titles across 2,370 sites found Google rewrote 61.6% of "
     "them, with the lowest rewrite rates — 39% to 42% — in the 51-to-60-character "
     "band",
     "https://zyppy.com/seo/google-title-rewrite-study/"),
    ("Google confirmed in March 2026 that it is running a limited test of "
     "AI-generated headlines in web search results",
     "https://searchengineland.com/google-search-ai-headline-rewrites-test-472146"),
    ("Google's spam policies enumerate sixteen behaviours that can lower a ranking "
     "or trigger a manual action, and duplicate or repeated titles is not one",
     "https://developers.google.com/search/docs/essentials/spam-policies"),
    ("Google says not to use the first page of a paginated sequence as the "
     "canonical, to give each page its own, and that it no longer uses rel=next "
     "and rel=prev",
     "https://developers.google.com/search/docs/specialty/ecommerce/"
     "pagination-and-incremental-page-loading"),
]


def _verified_note() -> str:
    items = "; ".join(f'{what} (<a href="{url}" rel="nofollow noopener">source</a>)'
                      for what, url in VERIFIED)
    return (f'<p class="verified-note"><strong>Read {CHECKED_ON_HUMAN}.</strong> '
            f'Every statement above about how Google behaves was read from these '
            f'pages on that date: {items}. Search behaviour moves and these will '
            f'age. Where a number here is contested, both numbers are on the page '
            f'with the reason they differ, rather than the one that argues better.'
            f'</p>')


def duplicate_titles() -> Path:
    body = f"""
<p class="lede">Duplicate title tags are a real problem, and most of the advice about them is
wrong about why. They are not a penalty — Google's spam policies enumerate sixteen behaviours
that can cost a site its ranking, and a repeated title is not one of them. The damage is
quieter than that. Google is left to guess which of several identical-looking pages answers a
query, and you have given away the one line of the search result you get to write.</p>

<h2>What a duplicate title actually costs you</h2>

<p><strong>The wrong page wins the query.</strong> Six pages carrying one title over similar
copy means something has to choose between them, and it will not be you. You wanted the
category page and got page 7 of the archive. You wanted the service page and got the filtered
listing that happened to contain the phrase. Nothing is flagged, nothing looks broken, and the
click lands somewhere that does not convert.</p>

<p><strong>You hand back the line you control.</strong> Google's documentation says plainly
that where it detects an issue with the title on a page, it may build a better title link out
of anchors, on-page text or other sources. A title repeated across a site is close to a
definition of the issue it is describing.</p>

<p><strong>It is usually a symptom.</strong> Twenty pages sharing a title is normally twenty
pages that should not all be indexed, or a template with a variable nobody wired up. Rewriting
the twenty titles leaves the cause where it was.</p>

<h2>Two things everyone repeats that are not true</h2>

<h3>That there is a character limit</h3>

<p>Google's documentation is explicit that there is no limit on how long a
<code>&lt;title&gt;</code> element can be, and that the title link is cut short in results only
as needed — typically to fit the width of the device. That is a <strong>pixel
measurement</strong>, and it has been one for years.</p>

<p>The difference is not academic. <code>WILLIAM WORTHINGTON MACHINERY</code> and
<code>illinois willow lily tinsmith</code> are within a character of each other and nowhere near
the same width on a screen. Capitals and wide letters run out of room early; narrow lowercase
survives well past sixty. Roughly 50 to 60 characters is a useful working range, and the
dataset below puts the lowest rewrite rates in that band — but it is a proxy for a width you
should go and look at, not a rule anything is enforcing.</p>

<h3>That the title you write is the title that shows</h3>

<p>Often it is not. Google's own documentation says it "uses a number of different sources to
automatically determine the title link" and does not publish how often each source wins —
checked 2026-08-10. The best independent measurement is a study of <strong>80,959 titles across
2,370 sites</strong>, which found the title Google displayed differed from the one written on
the page <strong>61.6%</strong> of the time.</p>

<p>Read that number carefully: it counts titles <em>identical to</em> yours, so one Google
merely trimmed or reordered counts as changed even though it started from what you wrote. What
it says is that Google usually begins with your title and frequently does not finish there — and in March 2026 it confirmed a limited test that generates headlines with
AI in ordinary web results, which is a different act from shortening one.</p>

<p>None of that argues for skipping the work. Google asks for distinct descriptive text in the
title element of every page, and distinct titles are the input it is judging. You own the
input. You do not own the output, and any guide promising you control of the rendered result is
selling something.</p>

<h2>Finding them</h2>

<p>Three ways, in descending order of completeness.</p>

<ul>
<li><strong>Crawl and pivot.</strong> Any crawler that exports a title column will do. Group the
export by the title string and sort by count descending. The top ten rows are usually the entire
job, because duplicate titles arrive in template-sized batches rather than one at a time.</li>
<li><strong>Docket.</strong> Duplicate and near-duplicate titles sit among its {N_CHECKS}
checks, and the finding is ranked against everything else on the site rather than listed —
thirty duplicates on archive pages you never wanted indexed is not the same discovery as two on
the pages that sell. The crawl runs on your own Mac and each finding carries the markup to
paste.</li>
<li><strong>A <code>site:</code> query, if you have neither.</strong>
<code>site:example.com intitle:"Services | Acme"</code> returns pages carrying that exact title.
It is not an index dump and should not be read as one, but it answers "is this template
repeating, and roughly how far" in about ten seconds.</li>
</ul>

<p>Whatever you use, look for near-duplicates and not only exact matches.
<code>Emergency Plumber in Fairfax, VA</code> and <code>Emergency Plumber in Falls Church,
VA</code> are two distinct strings and one title. Exact-match reporting will tell you the site
is clean. It is not.</p>

<h2>Cause by cause, and what to change</h2>

<p>The cause decides the remedy, and in about half of these the remedy is not a title.</p>

<div class="wrap-tbl"><table class="cmp">
<thead><tr><th>Pattern producing the duplicates</th><th>The fix</th></tr></thead>
<tbody>
<tr><td>Pagination reusing page 1's title</td><td>Append the page number and stop. Canonical
each page to itself, never to page 1</td></tr>
<tr><td>Filter and facet URLs being indexed</td><td>Not a title problem. Canonical to the
unfiltered page; block or noindex the combinations nobody searches for</td></tr>
<tr><td>A facet that does have real demand</td><td>Promote it into a real page: its own title,
its own copy, a canonical to itself</td></tr>
<tr><td>Product variants on separate URLs</td><td>Canonical to the parent product, or, where a
variant genuinely earns a page, lead its title with the thing that differs</td></tr>
<tr><td>Location pages off one template</td><td>Distinct titles only help if the pages are
distinct. If nothing on the page is local, the title is not what is wrong</td></tr>
<tr><td>Two service pages chasing one query</td><td>Merge the weaker into the stronger and 301.
Two titles competing is two pages competing</td></tr>
<tr><td>Brand name leading every title</td><td>Put the distinguishing words first and the brand
last — truncation happens on the right</td></tr>
<tr><td>The homepage title on every page</td><td>A broken template variable. Fix it once in the
layout, not four hundred times in a CMS</td></tr>
</tbody></table></div>

<h3>Paginated archives</h3>

<p>Do not write forty descriptive titles for forty pages of an index; appending the page number
is correct and sufficient. Give each page in the sequence a canonical pointing at itself.
Google's pagination guidance says in as many words not to use the first page of a sequence as
the canonical, and that it no longer uses <code>rel="next"</code> and <code>rel="prev"</code> —
the relationship is carried by ordinary links now. Canonicalising page 3 to page 1 is the
common mistake, and it quietly withdraws everything only reachable from page 3.</p>

<h3>Filters and facets</h3>

<p>The largest source of duplicate titles on any store, and rewriting the titles is the wrong
move, because most of those URLs should not be in the index at all. Decide first whether the
problem is index bloat or wasted crawling, because the two remedies interfere: a canonical
consolidates a URL that is still being crawled, and a robots rule stops it being crawled and
therefore stops the canonical ever being read. Pick the wrong one and you get a report that
looks fixed over a site that behaves the same.</p>

<h3>Pages that differ by one word</h3>

<p>The uncomfortable case, and the usual one on local and service sites. Where two pages differ
only by a city name or a swapped adjective, giving them distinct titles is cosmetic: you have
made the strings unique and left two pages competing for one query. Either give each page
something only it can say — a real address, real prices, work you actually did there — or merge
them and redirect. A unique title on a page with no reason to exist is a unique title on a page
with no reason to exist.</p>

<h2>What this will not fix</h2>

<p><strong>Duplicate titles are not why a thin page fails to rank.</strong> A page carrying
eighty words nobody needed will rank nowhere behind a perfect, unique, pixel-measured title. If
a page is not ranking and its title is duplicated, the duplicate title is something you
noticed, not a diagnosis.</p>

<p><strong>There is nothing to recover from.</strong> No manual action covers this, so if
traffic fell off a cliff, titles are not where the week should go. Look at what changed on the
day it fell.</p>

<p><strong>It will not stop the rewriting.</strong> Distinct titles improve your odds and settle
nothing. Keeping the title close to the page's H1 is the one lever with published evidence
behind it, and the study that found it declined to put a number on the effect, so treat it as a
direction rather than a dial.</p>

<p><strong>Clearing the list is not the goal.</strong> Three hundred duplicate titles on archive
pages you would rather were not indexed is a day of work with nothing measurable at the end of
it. The ordering matters more than the count — the useful output is the four that pay, not the
number 304.</p>

<h2>Where the claims on this page came from</h2>

{_verified_note()}

<p><a class="btn" href="/download/">Download Docket</a></p>
"""
    return render(
        cat="how-to", slug="fix-duplicate-title-tags",
        title="How to fix duplicate title tags — and what it won't fix",
        desc=("Duplicate titles are not a penalty. They let the wrong page win the "
              "query and waste the one line of the result you get to write."),
        h1="How to fix duplicate title tags",
        crumb='<a href="/">Docket</a> / <a href="/how-to/">Fix it</a> / duplicate titles',
        published=CHECKED_ON,
        body=body,
        faq=[
            ("Do duplicate title tags cause a Google penalty?",
             "No. Google's spam policies enumerate sixteen behaviours that can lower a "
             "ranking or trigger a manual action, and duplicate or repeated titles is not "
             "among them. The real cost is that Google has to decide which of several "
             "near-identical pages answers a query and will sometimes pick the wrong one, "
             "and that a repeated title is one of the clearest invitations for Google to "
             "write its own title link instead of using yours."),
            ("How long should a title tag be?",
             "Google's documentation says there is no limit on the length of a title "
             "element, and that the title link is truncated in results as needed, typically "
             "to fit the width of the device. That is a pixel measurement rather than a "
             "character count. Roughly 50 to 60 characters is a useful working range and "
             "the lowest measured rewrite rates sit in that band, but a title of wide "
             "capitals runs out of room sooner than a narrow one of the same length."),
            ("Why does Google show a different title than the one I wrote?",
             "Because it generates its own where it judges yours unhelpful — half-empty, "
             "boilerplate, repeated across the site, or a poor description of the page. "
             "Google has put its use of the HTML title element at about 87% of the time; an "
             "independent study of 80,959 titles across 2,370 sites found the displayed "
             "title differed from the written one 61.6% of the time. The two count "
             "different things. Write distinct titles regardless: they are the input Google "
             "is judging."),
            ("Should paginated pages have unique titles?",
             "Yes, but minimally. Appending the page number is enough, and each page in the "
             "sequence should carry a canonical pointing at itself — Google's pagination "
             "guidance says not to use the first page of a sequence as the canonical. "
             "Writing genuinely distinct descriptive titles for pages 2 through 40 of an "
             "archive is work that returns nothing."),
            ("Do near-duplicate titles count, or only exact matches?",
             "They count, and they are the ones most reports miss. Twelve location pages "
             "differing only by city name are twelve distinct strings and one title. Where a "
             "single swapped word is all that separates two pages, the titles are not really "
             "the problem — the pages are."),
        ],
    )


if __name__ == "__main__":
    print(duplicate_titles())
