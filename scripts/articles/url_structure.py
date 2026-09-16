#!/usr/bin/env python3
"""URL structure — the five findings `index.url_hygiene` emits, and nothing else.

Sourced from `index.url_hygiene` in
`backend/seo_engine/checks/indexability.py`, from `AuditContext.is_indexable`
in `backend/seo_engine/registry.py` (which decides the population every one of
these five findings is measured over), and from the test beside them,
`tests/test_two_instructions_that_cancel_each_other.py`, which records the one
defect this check has had corrected in prose: the parameter advice used to ask
for a canonical and a robots.txt disallow in the same sentence, and the two
cancel.

⚠️ THE SUBJECT AREA IS ALMOST ENTIRELY FOLKLORE, AND THAT IS THE PAGE.
"URL structure best practice" is written about constantly and measured almost
never. Three claims in particular are repeated everywhere with no source behind
them: that hyphens outrank underscores, that a keyword in the URL carries
ranking weight worth chasing, and that there is an ideal URL length. This page
makes none of them. What it states is either (a) what Docket's check actually
does, read out of the code, or (b) a sentence quoted verbatim from a source
named below with the date it was read.

⚠️ AND THE CHECK IS NARROWER THAN ITS OWN FINDING TITLES. Four places where the
title or the fix text promises more than the code delivers are described on the
page rather than smoothed over:

  * "URLs contain encoded spaces" fires on a literal `+` anywhere in the PATH,
    where `+` does not mean a space at all — that substitution belongs to
    `application/x-www-form-urlencoded`, which is a query-string format.
  * "URLs carry multiple query parameters" counts ampersands and needs two, so
    two parameters never fires it; three do.
  * The session-ID pattern is an unanchored substring, so a parameter merely
    ENDING in those letters matches, and it reads `parsed.query` only — the
    classic `;jsessionid=` in a path segment lands in `ParseResult.params` and
    is not seen.
  * The long-URL rule measures the whole absolute URL, scheme and host
    included, while its fix text talks about slugs.

No typed figures or dates: every threshold, count and read date is a constant
below, interpolated. The literals `%20` and `+` are written inside <code>, both
because they are tokens being quoted and because `verify_numbers` masks code.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from render import render  # noqa: E402

# -- the check's own thresholds, read out of the shipped code -----------------

#: `len(page.url) > 115` — the whole absolute URL, not the slug.
URL_LONG = 115

#: `parsed.query.count("&") >= 2`, which is three or more key-value pairs.
PARAM_AMPERSANDS = 2
PARAM_PAIRS = 3

#: `len(params) > max(3, len(ctx.indexable) * 0.25)` — a floor and a share.
PARAM_FLOOR = 3
PARAM_SHARE_PCT = 25

#: How many findings the check can emit.
N_FINDINGS = 5

# -- outside sources, read at their canonical homes on the date below ---------

GOOGLE_URL = ("https://developers.google.com/search/docs/"
              "crawling-indexing/url-structure")
GOOGLE = "Google's URL structure documentation"
WHATWG_URL = "https://url.spec.whatwg.org/#urlencoded-parsing"
WHATWG = "the WHATWG URL Standard"
#: The URI standard Google's sentence names. A constant so the quotation can be
#: reproduced verbatim without a typed figure reaching the page.
STD = "IETF STD 66"
READ_ON = "16 September 2026"


def url_structure() -> Path:
    body = f"""
<p class="lede">Search for URL structure advice and you get a list of rules delivered with
total confidence and no evidence: hyphens beat underscores, keep it under some number of
characters, get your keyword in the slug. Some of that is in Google's own documentation. Some
of it has never been published by anyone who measured it. This page separates the two, and
says plainly which of them Docket checks — because the answer is fewer than you would guess.</p>

<p>Docket registers one check here, <code>index.url_hygiene</code>, under the title
"URL structure", in the crawlability and indexing lane. It emits up to {N_FINDINGS} findings.
Here they are, with the condition that fires each, exactly as the code has it.</p>

<h2>The five findings</h2>

<h3>A session ID in the query string</h3>

<p>Finding <code>index.session_ids</code>, at HIGH — the most severe thing this check can say.
It fires on a URL whose query string matches <code>sid=</code>, <code>sessionid=</code>,
<code>phpsessid=</code> or <code>jsessionid=</code>, case-insensitively. The detail text is
blunt about why: a session ID makes a new, unique URL for every visit, which is an effectively
infinite duplicate-content space. The fix is to move session state into cookies and strip the
parameter from crawlable URLs.</p>

<p>This one has a source, and it is the only finding in the check that Google's own
documentation addresses head-on. Read on {READ_ON}, {GOOGLE} lists session IDs among the
irrelevant parameters that inflate a site's URL count, and says: "Wherever possible, avoid the
use of session IDs in URLs and consider using cookies instead."</p>

<h3>Uppercase letters in the path</h3>

<p>Finding <code>index.url_uppercase</code>, at LOW. Any uppercase letter anywhere in the path
fires it. Not the host, which is case-insensitive by definition; not the query string. Just the
path. The stated reason is that a path is case-sensitive on most servers, so two casings of the
same page can both be indexed, and the fix is to standardise on lowercase and redirect the
mixed-case versions permanently.</p>

<p>Sourced, again on {READ_ON}: "Like any other HTTP client following {STD}, Google
Search's URL handling is case sensitive (for example, Google treats both <code>/APPLE</code>
and <code>/apple</code> as distinct URLs with their own content)." The same passage says what
to do if your server does not care about case — "convert all text to the same case so it's
easier for Google to determine that URLs reference the same page."</p>

<h3>Encoded spaces — and this title is wider than its rule</h3>

<p>Finding <code>index.url_spaces</code>, at LOW. It fires when the path contains
<code>%20</code> <strong>or</strong> a literal <code>+</code>. The reasoning given is practical
rather than algorithmic: spaces in URLs are ugly when shared, break in plain-text contexts and
get mis-copied. The fix is to use hyphens between words.</p>

<p>The second trigger is looser than the finding's name. A <code>+</code> means a space only
inside an <code>application/x-www-form-urlencoded</code> payload, which is a query-string
format — {WHATWG} spells the substitution out in its parsing steps: "Replace any 0x2B (+) in
name and value with 0x20 (SP)", where name and value are the halves of a query pair. In a path
segment a plus is just a plus. So a page published at a path containing one gets reported as
carrying an encoded space when it carries no space at all. Worth knowing before you go and
rename anything.</p>

<h3>A long URL</h3>

<p>Finding <code>index.url_long</code>, at NOTICE — the lowest severity Docket reports a
defect at, and correctly so. It fires when the URL is longer than {URL_LONG} characters. The detail text says
long URLs get truncated in search results and shared links; the fix says to shorten slugs to
the two or three words that describe the page.</p>

<p>Two honest caveats. The measurement is taken over the entire absolute URL — scheme, host and
all — while the advice talks about slugs, so a long hostname spends part of a budget you cannot
edit by renaming a page. And the threshold itself has no outside source. It is a
house number, chosen by us. Read in full on {READ_ON}, {GOOGLE} states no character
limit for URLs anywhere on the page. That is why this finding is a notice and not an error, and
why nothing here tells you that a URL over that length will rank worse. Nobody knows that.</p>

<h3>Lots of parameterised URLs</h3>

<p>Finding <code>index.url_params</code>, at MEDIUM, and the only one of the five with a
site-level threshold rather than a per-URL one. A URL counts toward it when its query string
contains at least {PARAM_AMPERSANDS} ampersands, which means {PARAM_PAIRS} or more key-value
pairs — two parameters never counts. The finding is then reported only if the number of such
URLs exceeds both a floor of {PARAM_FLOOR} and {PARAM_SHARE_PCT} per cent of the indexable
pages in the crawl, whichever is larger. A handful of filtered URLs on a big site stays quiet.
A site that is mostly filter combinations does not.</p>

<p>The remedy attached to it was rewritten after a sweep through every fix text in the product
asking one question of each: what happens to a reader who does exactly this? The old sentence
asked for a canonical on parameterised URLs <em>and</em> a robots.txt disallow on the same
patterns. Each is defensible alone. Together they defeat each other, because a URL Googlebot
cannot fetch is a canonical it cannot read, and the URL can still be indexed with nothing behind
it. The advice now gives them as alternatives and says which case each suits: canonicalise and
stay crawlable for parameter spaces you want consolidated; disallow, and do not bother with a
canonical, for spaces you never want crawled at all.</p>

<h2>What this page refuses to tell you</h2>

<p><strong>That hyphens beat underscores for ranking.</strong> {GOOGLE} does recommend hyphens
— "we recommend using hyphens (<code>-</code>) instead of underscores (<code>_</code>) to
separate words in your URLs, as it helps users and search engines better identify concepts in
the URL" — and gives a reason that is about legibility and convention, not about a scoring
difference: underscores are already used to join words into single names in programming
languages. No effect size is published. <strong>And Docket does not check for underscores at
all.</strong> No finding in this check looks at them. A page that told you Docket enforced
Google's hyphen recommendation would be describing software that does not exist.</p>

<p><strong>That a keyword in the URL is worth restructuring for.</strong> The closest thing to
a source is the recommendation to "use readable words rather than long ID numbers in your
URLs", which is an argument about human comprehension and sits under a heading about descriptive
URLs. No weight, no measurement, no ranking claim. Docket checks nothing of the kind and will
never tell you a slug is missing a keyword.</p>

<p><strong>That there is an ideal URL length.</strong> Covered above: our own threshold is a
house number and is labelled as one, and Google publishes none.</p>

<p>Being precise here cuts our own side too, which is the point of saying it out loud. The
uppercase finding's premise — that paths are case-sensitive on most servers — is stated as a
general fact by the check and is not measured by it per site; Docket does not probe your server
to find out whether it folds case. Treat that finding as "these URLs could be a duplicate pair"
rather than "these URLs are one".</p>

<h2>What the crawl actually saw</h2>

<p>All five findings are computed over the crawl's indexable pages: fetched, HTML, an OK status,
not carrying <code>noindex</code>. That has consequences worth holding on to. A URL the crawl
never reached is in none of these lists. A URL your sitemap declares but nothing links to may or
may not be in them, depending on how far the crawl got. And a parameterised URL that you have
already excluded with <code>noindex</code> is correctly invisible here, because it is not a page
competing for indexing.</p>

<p>So the counts are a floor, not a census — the shape of the problem on the pages Docket read,
which on a large site is a sample. If a parameter space is the thing you are worried about, the
number that matters is not in the finding; it is in whether the crawl kept discovering new
combinations until it ran out of budget.</p>

<h2>What to do with the list</h2>

<p>In severity order, which is also roughly the order of how much a fix buys you. Session IDs
first — that is a duplicate-content generator and the only item here Google's documentation
explicitly asks you to remove. Then the parameter finding, if it fired, taking the canonical
route or the robots.txt route but not both. Then casing, which is a server rule plus redirects
rather than a URL-by-URL job. The encoded-space and long-URL findings are cosmetic; they are a
notice and a low for a reason, and renaming live URLs to satisfy them costs you redirects you
did not need.</p>

<p>The thread running through most of this is which URL gets indexed when several serve the same
thing, which is a bigger subject than any one check.
<a href="/learn/canonical-tags/">What a canonical tag actually does</a> covers the declaration
you make about that directly, including how often it gets overridden;
<a href="/learn/index-coverage/">index coverage</a> covers reading the outcome. And if the fix
you land on is a redirect, <a href="/how-to/fix-redirect-problems/">redirect loops, chains and
internal links pointing at redirects</a> is the shape to avoid creating on the way.</p>

<p><a class="btn" href="/download/">Download Docket</a></p>
"""
    return render(
        cat="learn", slug="url-structure",
        title="SEO URL structure: what is checked, what is folklore",
        desc=("What a Docket audit of your site's URLs reports, finding by finding: session "
              "IDs, casing, encoded spaces, length and parameters — and the claims with no source."),
        h1="SEO URL structure best practice, minus the folklore",
        crumb='<a href="/">Docket</a> / <a href="/learn/">Learn</a> / URL structure',
        body=body,
        faq=[
            ("Does Docket check whether my URLs use hyphens instead of underscores?",
             "No. Google's URL structure documentation does recommend hyphens over "
             "underscores, and gives a legibility reason rather than a ranking one, but no "
             "finding in Docket's URL structure check looks at underscores. The check reports "
             "session IDs, uppercase letters in the path, encoded spaces, URLs past a length "
             "threshold, and a site that is mostly parameterised URLs."),
            ("What is the ideal URL length for SEO?",
             "There is no published figure, and this page does not invent one. Google's URL "
             "structure documentation states no character limit anywhere. Docket does have a "
             "length threshold, it is a number we chose rather than one we measured, and the "
             "finding it produces is a notice rather than an error for exactly that reason."),
            ("Do keywords in the URL help rankings?",
             "No source we can cite says so with a measurement attached. Google's guidance is "
             "to use readable words rather than long ID numbers, which is an argument about "
             "people understanding the URL. Docket never reports a URL for lacking a keyword, "
             "and restructuring live URLs on that theory costs you redirects for no known "
             "gain."),
            ("Why is a URL flagged for encoded spaces when it has no space in it?",
             "The rule fires on a literal plus sign in the path as well as on a percent-encoded "
             "space, and a plus only means a space inside a query string, where the "
             "form-urlencoded format defines that substitution. In a path segment a plus is "
             "just a character. The finding is accurate about what it matched and wider than "
             "its title suggests, so check the URL before renaming anything."),
            ("My site uses query parameters everywhere and Docket said nothing. Why?",
             "That finding is the only one in the check with a site-level threshold. A URL has "
             "to carry three or more parameters to count at all, and the finding is only "
             "reported when the number of such URLs clears both a small floor and a share of "
             "the indexable pages the crawl read. A few filtered URLs on a large site stay "
             "below it by design."),
            ("Does Docket see URLs it did not crawl?",
             "No. Every finding here is computed over the pages the crawl fetched that were "
             "indexable HTML — so the counts are a floor rather than a census. On a large site "
             "with a big parameter space, the more useful signal is whether the crawl kept "
             "finding new URL combinations until it ran out of budget."),
        ],
    )


BUILDERS = [url_structure]


def build_all() -> list:
    return [b() for b in BUILDERS]


if __name__ == "__main__":
    print(url_structure())
