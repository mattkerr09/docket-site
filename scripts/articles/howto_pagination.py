"""Pagination and the canonical mistake that hides pages.

Promised on the how-to hub. Sourced from `links.pagination`, which emits
`links.pagination_canonical` when pages 2..n declare page 1 as their canonical.

The reason this is worth a page: the mistake looks like good hygiene. Somebody
is trying to avoid duplicate content and instead tells Google the deeper pages
are duplicates, which takes everything only reachable from them out with it.

No numeric literals, and no dates. The engine's own fix text states that
rel=prev/next is no longer used without pinning a year to it, and this mirrors
that rather than asserting one.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from render import render  # noqa: E402


def pagination() -> Path:
    body = """
<p class="lede">For canonical pagination, each page that lists different items should point
its canonical at itself. Do not point every page at the first page. That tells search engines
the later pages are duplicates, even though they hold different products or articles.</p>
<p>To audit your site, open a later page in a series and check its canonical in the HTML.
If it points back to the first page, fix the pagination template and check the series again.</p>

<h2>Should paginated pages canonicalise to the first page?</h2>

<p>Pages 2, 3 and 4 declare page 1 as their canonical:</p>

<pre><code>&lt;!-- on /blog/page/2/ --&gt;
&lt;link rel="canonical" href="https://example.com/blog/" /&gt;</code></pre>

<p>That says: <em>this page is a duplicate of page one, index that instead.</em> It is a
statement about the page, and it is false. Page two is not another copy of page one; it holds
different items.</p>

<p>The cost is not the archive page itself, which nobody was searching for. It is everything
<strong>only reachable from it</strong>. On a catalogue or a blog with a long back-file, the
deeper pages are the only route to most of the site. A canonical is a hint. If a crawler treats these pages as duplicates, it
may stop fetching them, and the items only reachable through them may stop being crawled too.</p>

<h2>Why sensible people do it</h2>

<p>Because it looks like duplicate-content hygiene. The pages share a title, a heading and a
layout, so collapsing them to one canonical feels tidy, and it is the shape of advice that
circulated widely when pagination markup was a live topic. The instinct is right and the target
is wrong: near-identical <em>chrome</em> around different <em>items</em> is not duplication.</p>

<h2>How to set canonical tags for pagination</h2>

<p><strong>Make every paginated page self-canonical.</strong> Page two's canonical is page two:</p>

<pre><code>&lt;!-- on /blog/page/2/ --&gt;
&lt;link rel="canonical" href="https://example.com/blog/page/2/" /&gt;</code></pre>

<p><strong>Link the series properly in the HTML.</strong> Previous and next links, and numbered
links where the series is short enough, as real anchors a crawler can follow without running
JavaScript. This is what discovery now relies on: <code>rel="prev"</code> and
<code>rel="next"</code> are no longer used by Google for indexing, so the ordinary links are
doing the work.</p>

<p><strong>Give each page something of its own</strong> where you reasonably can: a distinct
title, or a heading that says which slice of the series it is. Not to rank the archive, but so
nothing about the page invites the collapse you have just undone.</p>

<h2>How to check a pagination canonical</h2>

<p>Fetch the second page of any series and read its canonical:</p>

<pre><code>curl -s https://example.com/blog/page/2/ | grep -i 'rel="canonical"'</code></pre>

<p>If that prints page one, you have found it. Check a product category as well as the blog.
These are usually set by a template, so the fault tends to be either absent or everywhere.</p>
<p>After the template change, fetch a later page again. Its canonical should match its own
address. Check that previous, next and numbered links still lead to the right pages.</p>
<p>A canonical is only part of an <a href="/learn/seo-audit/">SEO audit</a>.
If a later page cannot be crawled, use the <a href="/tools/robots-txt-tester/">robots.txt tester</a>
to check for a blocking rule before changing its canonical.</p>

<h2>What this does not cover</h2>

<p>It is about what the pages <em>declare</em>, not about whether pagination is the right design.
An infinite scroll or a "load more" button that never changes the URL has the opposite problem:
there are no deeper pages for a crawler to find at all, canonical or otherwise. A view-all
page is a different trade again. Those are decisions about the site. This is a line in the head
that is saying something untrue about it.</p>
"""
    return render(
        cat="how-to", slug="fix-paginated-pages-that-canonicalise-to-page-1",
        modified="2026-11-09",
        title="Canonical pagination: how to fix it | Docket",
        desc=("Each paginated page with different items should be self-canonical. "
              "Audit your site for canonicals pointing to the first page and fix the template."),
        h1="Canonical pagination: which URL should each page use?",
        crumb='<a href="/">Docket</a> / <a href="/how-to/">Fix it</a> / pagination',
        body=body,
        faq=[
            ("What is canonical pagination?",
             "It is how canonical tags identify the preferred URL for each page in a series. "
             "When each page lists different items, each should point its canonical at itself, "
             "rather than treating later pages as copies of the first."),
            ("Should paginated pages canonicalise to page 1?",
             "No. It tells search engines that pages 2 and beyond are duplicates of page 1, so "
             "they may stop being crawled, and everything only reachable from them goes with "
             "them. Each paginated page should be self-canonical."),
            ("Do I still need rel=prev and rel=next?",
             "Google no longer uses them for indexing. Ordinary previous, next and numbered "
             "links in the HTML are what discovery relies on now, so make sure they are real "
             "anchors rather than JavaScript."),
            ("How do I check my pagination in one command?",
             "Fetch the second page and grep its head for the canonical link: "
             "curl -s https://example.com/blog/page/2/ | grep -i canonical. If it prints page "
             "one, that is the fault. Check a product category as well as the blog, since "
             "templates make it all-or-nothing."),
            ("Is duplicate chrome on paginated pages a duplicate-content problem?",
             "No. Sharing a title, heading and layout while listing different items is not "
             "duplication. Collapsing them with a canonical is the thing that causes harm."),
            ("What about infinite scroll or a load-more button?",
             "That is the opposite problem: if the URL never changes there are no deeper pages "
             "for a crawler to find at all. It is a design decision rather than a declaration "
             "that is untrue, and needs a different fix."),
        ],
    )


if __name__ == "__main__":
    print(pagination())
