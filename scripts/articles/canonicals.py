#!/usr/bin/env python3
"""Canonical tags — what rel=canonical does, and how it is usually got wrong.

Canonicals attract more stale folklore than any other piece of head markup:
advice written against 2011 behaviour is still repeated as current, and the
single most consequential fact — that Google treats the tag as a hint and
overrides it routinely — is the one most often left out.

So every claim on this page about Google's actual behaviour is read from
Google's own documentation on a stated date and carries a link, in the pattern
comparisons.py uses for claims about competitors. A page correcting folklore
that asks to be taken on trust is just more folklore.

The honesty section is about Docket's own canonical check, which shipped too
strict: it treated "canonical points somewhere else" as a defect, and a large
share of the pages it fired on were doing something legitimate.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from render import N_CHECKS, render  # noqa: E402

#: When every statement below about Google's behaviour was read from Google's
#: own pages. Canonical advice ages badly and most of what circulates was true
#: of a different decade, so an undated claim here would be the exact failure
#: the page is written against.
CHECKED_ON = "2026-08-10"
CHECKED_ON_HUMAN = "10 August 2026"

#: (what was read, where it was read). Anything not in this list is not stated
#: on the page as a fact about how Google behaves — it is either a description
#: of what Docket does, or written as an inference and labelled as one.
VERIFIED: list[tuple[str, str]] = [
    ('indicating a canonical preference "is a hint, not a rule", and "Google may '
     'choose a different page as canonical than you do"',
     "https://developers.google.com/search/docs/crawling-indexing/canonicalization"),
    ('the canonical "will be crawled most regularly; duplicates are crawled less '
     'frequently in order to reduce the crawling load on sites"',
     "https://developers.google.com/search/docs/crawling-indexing/canonicalization"),
    ('"even if you explicitly designate a canonical page, Google might choose a '
     'different canonical for various reasons, such as the quality of the content", '
     'and after a fix "Google might hold pages in a duplicate cluster for up to two weeks"',
     "https://developers.google.com/search/docs/crawling-indexing/"
     "canonicalization-troubleshooting"),
    ("canonicalisation lets search engines consolidate the information they hold for "
     "individual URLs, such as links to them, into one preferred URL; rel=canonical "
     "and a redirect are described as strong signals and a sitemap entry as a weak "
     "one, and absolute URLs are recommended over relative ones",
     "https://developers.google.com/search/docs/crawling-indexing/consolidate-duplicate-urls"),
    ('"Don\'t use the first page of a paginated sequence as the canonical page. '
     'Instead, give each page its own canonical URL", and Google no longer uses '
     "rel=next and rel=prev",
     "https://developers.google.com/search/docs/specialty/ecommerce/"
     "pagination-and-incremental-page-loading"),
    ('"While we don\'t recommend using JavaScript for this, it is possible to inject '
     'a rel="canonical" link tag with JavaScript" — and if you do, it must be the '
     "only one on the page",
     "https://developers.google.com/search/docs/crawling-indexing/javascript/"
     "javascript-seo-basics"),
    ("the wording of the three canonical-related page indexing statuses quoted in the "
     "table above",
     "https://support.google.com/webmasters/answer/7440203"),
]


def _verified_note() -> str:
    items = "; ".join(
        f'{what} (<a href="{url}" rel="nofollow noopener">source</a>)'
        for what, url in VERIFIED
    )
    return f"""
<p class="verified-note"><strong>Read from Google's own documentation on
{CHECKED_ON_HUMAN}.</strong> {items}. Canonical advice ages badly — a great deal
of what circulates was accurate against a version of Search that no longer
exists — so if Google has changed any of this since that date,
<a href="/about/">tell us</a> and the page will be corrected rather than quietly
left standing.</p>"""


# The narrowest useful summary of the page, kept here rather than in the prose:
# a canonical is an argument, and an argument you make in four places at once
# only counts if all four say the same thing.


def canonical_tags() -> Path:
    body = f"""
<p class="lede">A canonical tag tells Google which URL you would prefer it indexed. It does
not tell Google which URL to index. Google's documentation calls a canonical preference
a hint rather than a rule and says outright that it may choose a different page than you
do — so most canonical "bugs" are not broken markup at all. They are Google disagreeing
with you, and the way out is to remove the disagreement rather than to state your
preference more emphatically.</p>

<h2>Google is allowed to overrule you</h2>

<p>The sentence worth reading twice sits in Google's canonicalization documentation:
indicating a canonical preference is a hint, not a rule. The troubleshooting page is
blunter still — even where you have explicitly designated a canonical page, Google might
choose a different one, "for various reasons, such as the quality of the content".</p>

<p>That reframes the whole problem. If Google picked a URL you did not nominate, the tag
in your <code>&lt;head&gt;</code> is usually fine and the site is arguing with itself
somewhere else: internal links point at one URL, the sitemap lists a second, a redirect
aims at a third. Google's own docs rank those inputs — a rel=canonical annotation and a
redirect are strong signals, a sitemap entry is weak. Nothing makes the tag binding, so
declaring it twice, adding it in the HTTP header as well, and repeating it in the sitemap
achieves nothing by itself. Point every signal at the same URL and the disagreement
usually resolves.</p>

<p>Then wait. Google says it may keep pages in a duplicate cluster for up to two weeks
after the underlying issue is fixed, which is longer than most people give a change
before deciding it failed and undoing it.</p>

<h2>What the tag consolidates, and what it leaves alone</h2>

<p>The reason to use one at all is signal consolidation. Google describes canonicalisation
as letting it merge the information it holds for individual URLs — links to them among
them — into a single preferred URL. A link earned by <code>?utm_source=newsletter</code>
can end up counted towards the clean URL instead of stranded on a variant. Crawling works
the same way: the canonical is crawled most regularly and the duplicates less often, which
on a large catalogue decides whether new products are found this week or next month.</p>

<p>What it is not is a redirect. Both URLs still resolve, both still return 200, and a
visitor who lands on the duplicate stays on the duplicate. The tag operates on indexing
and on where signals land. It has no opinion about traffic.</p>

<h2>Seven ways canonicals get set wrong</h2>

<h3>There is no canonical at all</h3>
<p>The commonest and least dramatic failure. Nothing is broken, so nothing gets flagged,
and Google clusters your URL with whatever it thinks is similar and picks for you. A
self-referencing canonical on every indexable page costs one line and takes the choice
back.</p>

<h3>It points at a redirect, or at a 404</h3>
<p>A page canonicalises to <code>/product/blue-widget</code>, which 301s to
<code>/products/blue-widget/</code>. The strongest hint on the page now names a URL that is not
a page, so Google resolves the conflict itself, in whichever direction it prefers. Name
the final 200-status URL. The 404 variant is worse and easier to ship: a target deleted in
a content clean-up, with the canonical left pointing at the hole.</p>

<h3>Every page canonicalises to the homepage</h3>
<p>A CMS default, a theme setting, or a plugin field left holding a site-wide value. The
whole site declares that the only page worth indexing is the front page, and over a few
weeks the rest of it drops out of the index. This one is worth checking first because it
is catastrophic, silent, and takes thirty seconds to rule out.</p>

<h3>Page 2 canonicalises to page 1</h3>
<p>Received wisdom for years, and Google's current guidance is the opposite: don't use the
first page of a paginated sequence as the canonical page — give each page its own
canonical URL. Page 4 contains items page 1 does not, so pointing page 4 at page 1 asks
Google to ignore content that exists nowhere else. Google also stopped using
<code>rel="next"</code> and <code>rel="prev"</code>; ordinary <code>&lt;a href&gt;</code>
links between the pages carry the sequence now.</p>

<h3>The protocol or the trailing slash does not match</h3>
<p><code>http://</code> against <code>https://</code>, <code>www</code> against the apex,
<code>/about</code> against <code>/about/</code>, uppercase against lowercase. Each pair is
two different URLs, and a canonical naming the variant your server does not serve is a
canonical pointing at a redirect. It is also why Google recommends absolute URLs over
relative ones: a relative canonical resolves against whatever host rendered it, including
a staging domain nobody meant to have crawled.</p>

<h3>The canonical is written by JavaScript</h3>
<p>Possible, and not advised. Google's JavaScript documentation says so directly, and adds
the condition that trips most implementations: an injected canonical must be the only one
on the page. Frameworks that write one client-side on top of a static tag already in the
source ship two, and two contradictory hints is a weaker position than one.</p>

<h3>A cross-domain canonical nobody meant to ship</h3>
<p>Staging environments pushed to production with their canonicals intact, or a migration
that left half a site nominating the domain it moved off. Cross-domain canonicals are
legitimate and useful — they are the correct tool for syndicated content — and they are
also the one canonical mistake that hands your indexing to somebody else's site.</p>

<h2>Reading the statuses in Search Console</h2>

<div class="wrap-tbl"><table class="cmp">
<thead><tr><th>What Search Console says</th><th>What it usually means</th><th>What to do</th></tr></thead>
<tbody>
<tr><td>Alternate page with proper canonical tag</td><td>Google agreed with you. The page
correctly points at a canonical, and that canonical is the one indexed</td><td>Nothing.
This status is the system working, and it accounts for a great many of the "errors"
people set out to fix</td></tr>
<tr><td>Duplicate, Google chose different canonical than user</td><td>Google read your
canonical and picked something else. Almost always the two pages are near-identical and
the other URL carries stronger signals — more internal links, a redirect aimed at it, a
sitemap entry</td><td>Inspect the URL, read Google's chosen canonical, and decide who is
right. If you are, point the internal links and the sitemap at your choice. If Google is,
adopt its choice and move on</td></tr>
<tr><td>Duplicate without user-selected canonical</td><td>There is no canonical on the
page. Google clustered it with others and chose on your behalf</td><td>Add a
self-referencing canonical. This status is the cheapest one on the list to clear</td></tr>
<tr><td>Duplicate, submitted URL not selected as canonical</td><td>You put the URL in
your sitemap and Google indexed a different one. A sitemap is a weak signal losing an
argument with stronger ones</td><td>The sitemap is not the thing to change. Either
differentiate the pages or consolidate them properly with a redirect</td></tr>
<tr><td>Page with redirect, on a URL you canonicalised to</td><td>Your canonical names a
URL that redirects somewhere else</td><td>Repoint the canonical at the final
destination</td></tr>
<tr><td>Not found (404), on a URL you canonicalised to</td><td>The target was deleted and
the canonical was not updated</td><td>Restore the target or repoint the tag. Until then
the hint is discarded</td></tr>
</tbody></table></div>

<p>The URL Inspection tool is where this gets settled: it reports the user-declared
canonical and the Google-selected canonical side by side. When they differ, that gap is
the finding — not the tag.</p>

<h2>What a canonical will not fix</h2>

<p><strong>It is not a remedy for thin duplicate pages.</strong> Forty near-identical
location pages with the town name swapped are forty thin pages whether or not they point
at each other. A canonical says which one to index; it does not make the indexed one worth
ranking. If only one of the forty deserves to exist, delete thirty-nine and redirect
them.</p>

<p><strong>It does not control which URL a person sees.</strong> Anyone who reaches the
duplicate stays on it — canonicals affect indexing, not delivery. If a variant must not be
reachable, that is a redirect. If it must not be indexed at all, that is
<code>noindex</code>, which is a directive rather than a hint, and the two do not belong on
the same URL because they ask for different things.</p>

<p><strong>It cannot be read on a URL you have disallowed.</strong> Blocking a duplicate in
<code>robots.txt</code> stops Google fetching it, which stops Google seeing the canonical
you put on it. The tag has to be crawlable to do anything.</p>

<h2>The check we had to narrow</h2>

<p>Docket's canonical check shipped too strict. It treated <em>canonical does not equal the
page's own URL</em> as a defect, which is a reasonable rule on a plain brochure site and
fires constantly on real ones, against setups working exactly as intended.</p>

<p>Three groups accounted for nearly all of it, and all three were correct markup.
Paginated listings nominating a view-all URL. Syndicated articles pointing at the original
publisher, where flagging it red told the reader to break the one thing they had got
right. Faceted and parameterised URLs collapsing to the clean version, which is the
textbook use of the tag.</p>

<p>What survived is the part that can be established rather than guessed.
<code>index.canonical</code> resolves the declared target and reports what happened at the
other end: a redirect, a 404, a different host, a URL differing from the page only by
protocol or trailing slash. Those are verifiable. <code>index.canonical_conflict</code>
fires when a page declares more than one, which is never deliberate.
<code>index.www</code> handles apex-versus-www separately, because that is a server
configuration rather than a markup mistake.</p>

<p>A canonical that merely points elsewhere is now reported without a severity — a
statement of fact with the resolved target attached, so you can see at a glance whether it
is your syndication arrangement or your CMS having an opinion. The limit worth stating
plainly: Docket cannot tell a deliberate cross-domain canonical from an accidental one,
because that distinction lives in a commercial agreement and not in the HTML.</p>

<h2>Ten minutes on your own site</h2>

<ol>
<li>View source on any three pages and search for <code>rel="canonical"</code>. If they
all name the homepage, stop reading and fix that.</li>
<li>Copy each canonical target into a browser. It should return the page itself, at that
exact URL, with no redirect in the address bar.</li>
<li>Check that the protocol, the host and the trailing slash match how the page is
actually served.</li>
<li>In Search Console, open the page indexing report and look only at "Duplicate, Google
chose different canonical than user". That is the list where Google is telling you it
read your preference and declined it.</li>
</ol>

<p>Docket does this across a whole site rather than three pages: it checks canonical
validity, resolves the declared target, and flags the ones landing on redirects, 404s or a
different host — among {N_CHECKS} checks that run on your Mac, with no account and nothing
uploaded. Findings come back ranked by cost against effort, each with the exact markup to
paste.</p>

<p><a class="btn" href="/download/">Download Docket</a></p>
{_verified_note()}
"""
    return render(
        cat="learn", slug="canonical-tags",
        title="Canonical tags are a hint, not an instruction",
        desc=("Google treats rel=canonical as a hint and regularly picks a different "
              "canonical. The failure patterns behind that, and what Search Console "
              "is telling you."),
        h1="Canonical tags, and the ways they get set wrong",
        crumb='<a href="/">Docket</a> / <a href="/learn/">Learn</a> / Canonical tags',
        body=body,
        published=CHECKED_ON,
        faq=[
            ("Is a canonical tag a directive that Google has to follow?",
             "No. Google's documentation describes a canonical preference as a hint "
             "rather than a rule, and says it may choose a different page as canonical "
             "than you do. The tag is a strong signal weighed against your redirects, "
             "internal links and sitemap, not an instruction."),
            ("Why does Search Console say Google chose a different canonical?",
             "Because it read your tag and disagreed, usually because a near-identical "
             "URL carries stronger signals. The fix is to stop contradicting yourself: "
             "point internal links, redirects and the sitemap at the same URL the "
             "canonical names, then allow up to two weeks for the cluster to settle."),
            ("Should paginated pages canonicalise to page one?",
             "No. Google's guidance is to give each page in a sequence its own canonical "
             "URL, because page four contains items that page one does not. Pointing "
             "them all at page one asks Google to ignore content that exists nowhere "
             "else on the site."),
            ("Do canonical tags fix duplicate content?",
             "Only the indexing half of it. A canonical says which URL to index; it does "
             "not make the indexed page worth ranking. If forty near-identical pages "
             "each add nothing, the answer is to consolidate them with redirects rather "
             "than to label them."),
        ],
    )


BUILDERS = [canonical_tags]


def build_all() -> list[Path]:
    return [b() for b in BUILDERS]


if __name__ == "__main__":
    for p in build_all():
        print(p)
