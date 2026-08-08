#!/usr/bin/env python3
"""Internal link equity — measured on our own site, including where it fails.

Written from real numbers produced by Docket's architecture analyser against
docketseo.app. Every figure here was measured; the embarrassing one is included
because a piece about internal linking that only shows sites getting it right
is an advertisement, not an explanation.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import facts as F  # noqa: E402
from render import render  # noqa: E402


def internal_link_equity() -> Path:
    body = f"""
<p class="lede">Internal link equity is the ranking signal your own pages pass to each
other, and it is distributed by where you link — not by what you think matters. Google
treats a link from your homepage as a vote, so a page nothing links to reads as a page
you do not care about, however important it is to your business.</p>

<p>We found this on our own site. Docket crawled docketseo.app, built the internal link graph,
and ran PageRank across it. The download page — the entire commercial point of the site —
received <strong>one internal link</strong> and held <strong>1.25% of the internal link
equity</strong> against a 5.56% average. Our most important page was getting a fifth of what
a typical page got.</p>

<p>Nothing was broken. No error, no warning, nothing a crawler would flag. The page was in
the footer and reachable in one click, and by every conventional check it was fine.</p>

<p>Then we fixed it, and the interesting part is what happened next. The same measurement
today: <strong>{F.equity_pages()} pages and {F.equity_edges()} links</strong>, and the
download page holds <strong>{F.equity_node('/download/')['share_pct']}%</strong> from
{F.equity_node('/download/')['inlinks']} internal links — {F.equity_node('/download/')['index']}×
the {F.equity_average_pct()}% average, rather than 0.22×. The problem did not go away. It
moved.</p>

<h2>Why counting links is not enough</h2>

<p>The obvious measure is inbound internal links: count how many pages link to each page,
sort ascending, fix the bottom. It is a reasonable first pass and it is what most tools
give you. It also misses the thing that matters, because links are not equal. A link from
a page that itself receives no links passes almost nothing.</p>

<p>PageRank handles this by being recursive: a page's value depends on the value of the
pages linking to it, which depends on the pages linking to <em>those</em>. Run it to
convergence and you get a distribution across the whole site. Docket uses the standard
0.85 damping factor from the original paper, so the numbers are comparable to what other
tools report.</p>

<p>The practical difference: ten links from orphaned tag pages are worth less than one
link from your homepage. A raw count says the first is better.</p>

<h2>Reading the numbers</h2>

<p>Raw PageRank values are awkward — 0.0125 means nothing on its own. Divide by the average
and you get something you can act on. Anything under about 0.5× on a page you actually care
about is worth an afternoon. On this site today,
<strong>{F.equity_below_half()} pages sit under it</strong>, and they are the newest ones:
{", ".join(f"<code>{n['path']}</code> at {n['index']}×" for n in F.equity_weakest(3))}. Every
article arrives starved, because nothing links to it until something does.</p>

<p>Three patterns account for most of what goes wrong:</p>

<h3>The footer-only page</h3>
<p>Ours. A page linked from a shared footer gets exactly one link from the graph's point
of view, repeated site-wide. It is reachable, so no crawler complains, and it is starved,
because navigation links carry far less weight than a link inside relevant body copy.</p>

<h3>The isolated cluster</h3>
<p>A blog that links to itself four hundred times and to the product twice. Equity flows
in from the rest of the site, circulates inside the section, and never comes back out.
Docket reports sections that link to nothing outside themselves for this reason.</p>

<h3>The dead end</h3>
<p>Pages that receive links and contain none. Equity arrives and stops. Usually a
template that lost its related-content block during a redesign — and it is invisible
unless you are looking at the graph rather than the page.</p>

<h2>What we changed, and what it cost</h2>

<p>The fix for a starved page is not more links. It is links from pages that have something
to pass: the ones already holding equity, in body copy where the surrounding text gives the
link meaning, with anchor text that says what the destination is rather than "click here".</p>

<p>For us that meant linking the download page from inside the articles people actually
arrive on, not just from the footer. It worked — 0.22× to
{F.equity_node('/download/')['index']}×.</p>

<p>It also concentrated equity on the pages already in the navigation, which is why
{F.equity_below_half()} of {F.equity_pages()} pages now sit under 0.5×. There is no version
of this where every page is above average. The question is never "are any pages starved" —
some always are — but "are the starved ones the ones that matter", and on a site that keeps
publishing, the answer needs revisiting every time it does.</p>

<h2>Where another tool is the better choice</h2>

<p>If you want to <em>explore</em> a large site's structure interactively — click a
cluster, expand it, follow a branch, rearrange the layout — <a
href="/vs/sitebulb-alternative/">Sitebulb</a> is genuinely better at this and it is their
strongest feature. Their force-directed crawl maps are built for that kind of
investigation.</p>

<p>Docket draws a deliberately simpler picture: pages in rings by click depth, sized by
equity. That is a considered trade. Force-directed layouts become unreadable past a few
hundred nodes, and they are non-deterministic, so two audits of the same site produce
different-looking maps and you cannot compare them. We would rather the same crawl always
drew the same map. If interactive exploration is what you want, use Sitebulb.</p>

<h2>The caveat that matters</h2>

<p>A link graph is only as good as the crawl behind it. Auditing a law firm's site
recently, Docket crawled 30 pages and found 935 — and in that fragment, 25 attorney pages
appeared to have no inbound links at all. They were not orphans. The pages that link to
them, starting with the attorney index, had simply not been fetched yet.</p>

<p>That is why Docket will not show you architecture findings from a crawl that saw a
small fraction of a site. A structure diagram looks authoritative whether or not it is
right, which is exactly why it has to say when it is a sample. If you see the caveat,
raise the page limit and run it again.</p>

<h2>Checking your own site</h2>

<ol>
<li>List the five pages that make you money.</li>
<li>For each, count how many other pages link to it in body copy — not navigation, not
the footer.</li>
<li>If the answer is zero or one, that page is running on nothing.</li>
</ol>

<p>You can do this by hand on a small site in about twenty minutes. Docket does it across
every page, ranks the results, and shows you the map. The figures on this page come from
running it against this site on {F.equity()["measured"]}, and they are read from that
measurement rather than typed — this article quoted an 18-page graph for a while after the
site had 23 pages, which is exactly the failure it warns about.</p>

<p><a class="btn" href="/download/">Download Docket</a></p>
"""
    return render(
        cat="learn", slug="internal-link-equity",
        title="Internal link equity: find the pages your site is starving",
        desc=("The ranking signal your pages pass to each other. Measured on our own "
              "site, where fixing a starved page moved the problem rather than ending it."),
        h1="Internal link equity, measured",
        crumb='<a href="/">Docket</a> / <a href="/learn/">Learn</a> / Internal link equity',
        body=body,
        faq=[
            ("What is internal link equity?",
             "The ranking signal your own pages pass to each other through internal "
             "links. It is distributed by where you link, so a page nothing links to "
             "reads to a search engine as a page you do not consider important."),
            ("How is it different from counting internal links?",
             "Counting treats every link as equal. Link equity is recursive — a link "
             "from a page that itself receives no links passes almost nothing, so ten "
             "links from orphaned pages can be worth less than one from your homepage."),
            ("How many internal links should an important page have?",
             "There is no fixed number; it depends on where they come from. A useful "
             "test is relative: if a page receives less than half the internal equity of "
             "an average page on your site, and it matters commercially, it is starved."),
        ],
    )


BUILDERS = [internal_link_equity]


def build_all() -> list[Path]:
    return [b() for b in BUILDERS]


if __name__ == "__main__":
    for p in build_all():
        print(p)
