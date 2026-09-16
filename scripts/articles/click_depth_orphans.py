#!/usr/bin/env python3
"""Click depth and orphan pages — the three findings `index.depth` emits.

Sourced from `index.depth` in
`backend/seo_engine/checks/indexability.py`, the crawler properties the orphan
half consults (`Crawl.supports_link_graph_claims`, `Crawl.saw_the_whole_site`,
`Crawl.nav_in_html`, `Crawl.supports_absence_claims`), `CrawlConfig.max_depth`
and the frontier loop in `crawler.py` that assigns `Page.depth`, the homepage
resolution in `registry.py`, and the test beside them that records what went
wrong:

  * tests/test_an_orphan_needs_the_pages_that_might_link_to_it.py

⚠️ FOUR PLACES WHERE THE REPO IS NARROWER THAN THE OBVIOUS GLOSS, and each one
is on the page rather than smoothed over:

1. "Clicks from the homepage" is depth from the **crawl's start URL**. Depth
   zero is whatever URL you handed Docket, and `registry` keeps a separate
   `homepage_is_root` flag precisely because findings whose wording says
   "homepage" can be wrong about that.
2. The default depth limit is five, and links discovered past it are appended to
   `skipped` rather than fetched. So the deep list can only ever hold pages at
   the threshold or at the ceiling — the count is bounded by the crawl setting
   before it is bounded by the site.
3. **The depth half consults no crawl-quality gate at all.** The orphan half
   does. `supports_link_graph_claims` is documented as governing "inlink counts,
   orphan status and click depth", and `nav_in_html` was written after a
   JavaScript-nav site produced "a meaningless click-depth model" — yet
   `index.deep_pages` never reads either property. That asymmetry is the most
   interesting sentence on the page and it is stated as ours, not hidden.
4. An orphan must be **in your sitemap**. The gloss "a page nothing links to" is
   wider than the code: no sitemap entry, no `index.orphan_pages`, ever.

Also: the withheld branch's own fix text names the page limit, while `skipped`
accrues from the depth budget and the frontier cap too. The page says so.

No typed figures or dates: every number and date below is a module-level
constant, interpolated. FAQ strings are not f-strings, so the few numbers they
carry are spelled out in words, matching the threshold constants above them.

Demand for this topic was NOT measured — no related term cleared a volume
floor. The closing note says so in as many words; nothing on the page claims or
implies an audience was counted.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from render import render  # noqa: E402

#: The depth threshold in `index.deep_pages`: `p.depth >= 4`.
DEEP_AT = 4
#: `CrawlConfig.max_depth`, and the `-d` default on `docket audit`.
DEFAULT_DEPTH = 5
#: `AuditContext.urls_of` caps the URL list attached to any finding; the true
#: total survives on `Finding.count`.
URL_CAP = 25
#: `Crawl.saw_the_whole_site`: skipped <= max(5, 25% of pages crawled).
SKIP_FLOOR = 5
SKIP_PCT = 25
#: `Crawl.nav_in_html`: the average internal links per readable HTML page below
#: which the navigation is presumed absent from the delivered HTML.
NAV_LINKS = 2
#: The coverage floor `supports_absence_claims` falls back to, which the link
#: graph deliberately does NOT inherit.
ABSENCE_FLOOR = 20
#: Flags on `docket audit`.
PAGES_FLAG = "-n"
DEPTH_FLAG = "-d"
#: The measured case in the test named above: a London gelateria, at a page cap
#: that left most of the link graph unread.
G_ORPHANS = 15
G_CRAWLED = 25
G_SKIPPED = 20
G_DATE = "14 August 2026"
#: When the engine source behind this page was read.
READ_ON = "16 September 2026"


def click_depth_and_orphans() -> Path:
    body = f"""
<p class="lede">Two findings in your audit sound like the same complaint about the same
problem. One says pages sit too many clicks from the homepage. The other says nothing links
to a page at all. They come from one check, they are measured in different ways, and only one
of them is withheld when the crawl was too partial to support it.</p>

<p>Docket's <code>index.depth</code> check is registered as "Click depth and orphans" and can
emit three findings:</p>

<ul>
<li><strong>Deep pages</strong> — <code>index.deep_pages</code>, at LOW. Indexable pages whose
recorded depth is {DEEP_AT} or more.</li>
<li><strong>Orphan pages</strong> — <code>index.orphan_pages</code>, at MEDIUM. Sitemap URLs
with no internal link pointing at them.</li>
<li><strong>Orphans not checked</strong> — <code>index.orphans_unchecked</code>, a NOTICE
flagged as a tool limitation. The orphan question could not be answered on this crawl, so it
is not answered.</li>
</ul>

<p>That third one is the reason the check is worth reading about rather than merely acting on.
A zero there would mean blind, not clean.</p>

<h2>What "clicks from the homepage" actually counts</h2>

<p>The depth on a page is the level at which the crawler first put that URL into its queue.
The crawl walks outward a level at a time, so the number is the shortest path <em>along links
the crawler followed</em> from where it started.</p>

<p>Three things follow, and none of them matches the phrase in the finding's title.</p>

<p><strong>It is measured from the start URL, not from your homepage.</strong> Point Docket at
a section and that section is depth zero; everything under it counts from there. The engine
keeps a separate flag recording whether the page it is calling the homepage really is the site
root, and that flag exists because a finding once announced a whole site was deindexed when the
only page fetched was a single product page carrying a noindex. Any finding whose wording says
"homepage" inherits that caution, this one included.</p>

<p><strong>It counts links Docket could see.</strong> A menu assembled in the browser is not in
the delivered HTML, so a crawler reading the HTML finds no links in it. Pages reachable in one
click through that menu are then reached, if at all, by some longer route through a footer or a
body link — and their depth is the length of that longer route. The number is real; what it
measures is your link graph as served, which on a client-rendered site is not your link graph
as used.</p>

<p><strong>It is capped before it is measured.</strong> The default click-depth limit is
{DEFAULT_DEPTH}. Links discovered beyond it are not fetched; they are recorded as URLs the
crawl skipped. So on a default run the deep list can only contain pages at the threshold or at
the ceiling, and a genuinely buried page — the one this finding is supposed to be about — never
appears in it, because it was never fetched. If you want the real distribution, raise the limit
or remove it with <code>{DEPTH_FLAG} 0</code>, which means no limit rather than no links.</p>

<h2>The gate this check applies to one half and not the other</h2>

<p>Said plainly, because it is our own asymmetry and you should know about it before you weigh
the LOW finding.</p>

<p>The engine has a property that decides whether link-graph claims are defensible from a given
crawl. Its own documentation says it governs "inlink counts, orphan status and click depth".
One of the conditions inside it was added after a crawl of a site whose navigation is built by
JavaScript produced, in the words of the code, "a meaningless click-depth model" alongside a
list of pages wrongly called orphans.</p>

<p>The orphan half of <code>index.depth</code> consults that property. The depth half does not
read it at all. So on a site whose navigation never reaches the HTML, the orphan claim is
correctly withheld and the deep-pages list is printed anyway — with depths produced by the same
unreadable link graph that caused the orphan claim to be withheld. Treat a deep-pages list on
such a site as a statement about what Docket could crawl, not about your structure. If your
report also carries a finding about navigation that needs JavaScript, that is the signal:
<a href="/how-to/fix-navigation-that-needs-javascript/">how to fix navigation that needs
JavaScript</a> covers what to do about the cause.</p>

<h2>What Docket will call an orphan</h2>

<p>Narrower than the phrase suggests, and worth reading as a list of conditions that must all
hold. A page is reported as an orphan when it was crawled and answered cleanly, it is HTML, it
is not excluded by a noindex directive, <strong>its URL appears in your sitemap</strong>, the
crawl recorded no internal link pointing at it, and it is not the page being treated as the
homepage.</p>

<p>The sitemap condition is the one that surprises people. A page nothing links to and nothing
declares is not reported here — it is not reported anywhere, because a crawler starting from
your homepage and following links has no way to reach it and no way to know it exists. If you
publish no sitemap at all, <code>index.orphan_pages</code> cannot fire under any circumstances.
The finding's own detail text is accurate about this: "These pages appear in the sitemap but
nothing on the site links to them." The gloss that gets repeated elsewhere — any page with no
inbound internal links — is a wider claim than the code makes, and a wider claim than a crawl
can support.</p>

<p>The fix attached to it is deliberately two-sided: "Link to each from a relevant parent or
hub page — or remove it if it is obsolete." Orphans are frequently correct. A page that nothing
links to because nothing should link to it any more is a deletion, not a linking job.</p>

<h2>When the orphan answer is withheld, and why that is the useful part</h2>

<p>"Nothing links to this page" is a claim about your entire site, and you cannot make it from
pages you never fetched. The URLs left unfetched are exactly the ones whose outbound links are
unknown — they are the only candidates for carrying the missing link.</p>

<p>So the check requires that the crawl left nothing meaningful behind: the number of skipped
URLs must be no more than {SKIP_FLOOR}, or {SKIP_PCT}% of the pages crawled, whichever is
larger. A handful of stragglers does not invalidate a link graph. Past that line, Docket emits
the notice instead, and the notice deliberately does <em>not</em> quote how many orphans it
would have reported — that list is precisely what the crawl cannot support, and printing it
would hand you a number to act on while claiming not to. What it quotes instead is how many
URLs were never fetched.</p>

<p>This behaviour was bought with a wrong answer. Measured on a London gelateria on {G_DATE},
at a cap of {G_CRAWLED} pages: {G_ORPHANS} of those pages were reported as orphans, while the
crawl's own log recorded {G_SKIPPED} further URLs discovered and never fetched. Roughly
two-fifths of the link graph had not been looked at, and the pages that would have carried the
links were sitting in the queue. The gate in place at the time passed the crawl, because it
fell back to a {ABSENCE_FLOOR}% coverage floor — a defensible bar for "does a privacy page
exist anywhere on this site?", since a URL seen and never fetched still answers that, and the
wrong bar entirely for "does anything link here?".</p>

<p>That distinction survives in the code as two separate properties, and the looser one was
left alone on purpose. Presence can be established from a list of URLs. Absence of an inlink
cannot.</p>

<h2>The remedy names one limit; there are three</h2>

<p>The notice tells you to re-run without a page limit, using <code>{PAGES_FLAG} 0</code>, or
to raise the limit past the number of URLs the site declares. That is right about the most
common cause and incomplete about the rest. URLs land in the skipped list for three reasons:
the page budget ran out, the click-depth budget rejected the link, or the frontier grew past
several times the page budget.</p>

<p>Only the first is what <code>{PAGES_FLAG} 0</code> addresses. On a site deeper than the
default limit, the depth budget alone can push enough URLs into the skipped list to withhold
the orphan finding, and no page limit you choose will change that. If the notice persists after
an uncapped run, lift the other ceiling too:</p>

<pre><code>docket audit https://example.com {PAGES_FLAG} 0 {DEPTH_FLAG} 0</code></pre>

<p>Both zeros mean "no limit on this dimension", not "no pages" and not "no links" — a
distinction that once cost a whole-site preset its crawl, and is now the documented
convention on both flags.</p>

<h2>What the LOW severity is telling you</h2>

<p>Deep pages are reported at LOW, below orphans at MEDIUM, and that ordering is a judgement
rather than a measurement. The finding's detail says buried pages "get crawled less often and
are read as less important", and that "anything commercially valuable should be within three
clicks". No citation is attached to that finding, unlike others in the same file which carry a
link to the documentation they rest on. Read it as a rule of thumb the check encodes, not as a
published threshold anyone has verified for your site.</p>

<p>The practical reading is narrower and safer: depth is a proxy for how much internal linking
a page receives, and internal linking is a thing you control directly. If a page matters and
sits far from everything, the fix is the same either way — a link from a hub or a related-
content block, which is the finding's own advice. <a href="/learn/internal-link-equity/">Internal
link equity, measured</a> covers the distribution behind that proxy, which is the more useful
view once you have more than a handful of pages.</p>

<h2>Reading the list you were given</h2>

<p>The deep list arrives sorted deepest first, which is the order to work in. It is capped at
{URL_CAP} URLs in the report, with the true total kept separately — so a short list is not
necessarily a short problem, and the report says how many it is showing of how many.</p>

<p>Work orphans before depth. An orphan in your sitemap is a page you told search engines about
and then left unreachable by anything else, which is a contradiction you can resolve in one
edit. A deep page is a ranking of your own structure against a threshold, on a number whose
ceiling you set when you started the crawl. And if neither finding appears but the notice does,
nothing has been ruled out: re-run with both limits lifted before concluding your link graph is
clean. Whether a page is indexed at all is a different question with a different answer —
<a href="/learn/index-coverage/">is your page actually indexed?</a> covers how to check that
directly.</p>

<p>One note on why this page exists. We have not measured how many people ask this question,
and nothing here should be read as a claim that an audience for it was counted. It exists
because the check exists, its two halves are easy to confuse, and one of them applies a
crawl-quality gate the other does not. Engine source read on {READ_ON}.</p>

<p><a class="btn" href="/download/">Download Docket</a></p>
"""
    title = "Click depth and orphan pages: what Docket checks"
    desc = ("A Docket audit of your site reports deep pages and orphans from one crawl. "
            "What each threshold really measures, and when the orphan answer is withheld.")
    return render(
        cat="learn", slug="click-depth-and-orphan-pages",
        title=title,
        desc=desc,
        h1="Click depth and orphan pages",
        crumb='<a href="/">Docket</a> / <a href="/learn/">Learn</a> / click depth and orphans',
        body=body,
        faq=[
            ("How many clicks from the homepage is too many?",
             "Docket reports a page at four clicks or more, at its lowest severity, and the "
             "finding's own wording suggests keeping anything commercially valuable within "
             "three. That is a rule of thumb the check encodes rather than a published "
             "threshold, and no citation is attached to it. The number is also capped by your "
             "crawl settings before it is capped by your site."),
            ("Does Docket measure click depth from my homepage?",
             "It measures depth from the URL you started the crawl at. If you audit a section "
             "URL, that section is depth zero and everything is counted from there. The engine "
             "tracks separately whether the page it treats as the homepage is really the site "
             "root, because findings worded around the homepage can otherwise be wrong."),
            ("Why does my audit say orphan pages could not be checked?",
             "Because too many URLs the crawl discovered were never fetched, and those are "
             "exactly the pages that might carry the missing links. Docket withholds the "
             "orphan claim rather than reporting a count nobody should act on, and it tells "
             "you how many URLs were missed instead. Re-run with no page limit, and if the "
             "notice persists, lift the click-depth limit too."),
            ("Will Docket find an orphan page that is not in my sitemap?",
             "No. The orphan finding requires the URL to appear in your sitemap as well as "
             "having no internal links pointing at it. If you publish no sitemap, this finding "
             "cannot fire at all. A page that nothing links to and nothing declares is also a "
             "page a link-following crawler has no way to reach."),
            ("Are orphan pages always a problem?",
             "No, and the fix text says so: link to each from a relevant parent or hub page, "
             "or remove it if it is obsolete. A page nothing links to because nothing should "
             "link to it any more is a deletion. What is not defensible is leaving it in the "
             "sitemap, which tells search engines the page matters while the rest of the site "
             "says it does not."),
        ],
    )


BUILDERS = [click_depth_and_orphans]


def build_all() -> list:
    return [b() for b in BUILDERS]


if __name__ == "__main__":
    print(click_depth_and_orphans())
