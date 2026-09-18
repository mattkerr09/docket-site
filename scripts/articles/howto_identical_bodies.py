"""Identical content is not always duplicate content.

Promised on the how-to hub. Sourced from `indexability.py`'s duplicate cluster —
registered check `index.duplicate_content` — whose docstrings record two cases
where "these pages are identical, redirect the others" was wrong, one of them
destructively:

  * a documentation site whose several version aliases all declare one
    canonical, reported as competing duplicate titles and descriptions. They do
    not compete; one URL gets indexed. The report was internally inconsistent —
    the body-level check had been corrected the same day and these two had not.
  * an energy supplier where one group of the reported duplicates was
    fifty-four UNRELATED pages across eighteen top-level sections, every one
    recording the same short word count. Re-fetched, the same URLs served
    thousands of words of entirely different content. The server had handed the
    crawler a placeholder.

⚠️ NO SITE IS NAMED — third-party gate.

⚠️ THE NARROWNESS IS DELIBERATE AND MUST BE STATED: a two-URL pair and several
colour variants of one product both survive the filter, as does any large group
whose shared body is substantial rather than placeholder-sized.

⚠️ NUMERALS: 301 is NOT in verify_numbers' status block — write "a permanent
redirect". Quantities spelled as words.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from render import render  # noqa: E402


def identical_bodies() -> Path:
    body = """
<p class="lede">An audit reports that a set of your pages have identical content and tells you to
redirect all but one of them. Sometimes that is exactly right. Twice it has been recorded as
wrong, and the second time a reader who followed it would have redirected their blog, their press
page and their FAQs into a terms-and-conditions page — <strong>and a redirect is not a thing you
undo by noticing.</strong></p>

<p>Pages can share a body for three reasons. Only one of them is duplicate content.</p>

<h2>One: URL variants of the same page</h2>

<p>A trailing slash and no trailing slash. A query string a filter added. A colour a customer can
still buy. These are genuinely one page reachable several ways, they compete with each other for
one result, and consolidating them is what the finding exists for.</p>

<p>The tell is that they <strong>share a section</strong> of your site. Variants of a product page
live under products; variants of an article live under the blog. If the URLs in the group come
from all over the site, they are probably not variants of anything.</p>

<h2>Two: already resolved, and the report has not noticed</h2>

<p>A documentation site publishes several version aliases of the same manual, and every one of
them declares the same canonical. The audit reported that its pages shared duplicated titles and
descriptions, that they competed with each other, and that they gave searchers no way to tell the
results apart.</p>

<p>They do not compete. One URL is indexed, so there is one result — there is nothing to tell
apart. The site had already answered the question the finding was asking.</p>

<p>Worse, the report contradicted itself: the body-level check had been taught to skip
already-canonicalised groups and the title and description checks had not, so the same pages were
resolved in one finding and a defect two findings later. <strong>When one report says both things
about one set of URLs, at least one of them is wrong and the reader cannot tell which.</strong></p>

<p>What to check: if every page in the group declares the same canonical, the group is resolved.
A group whose members declare <em>different</em> canonicals, or none, is where pages really do
compete.</p>

<h2>Three: the server handed out a placeholder</h2>

<p>This is the one that costs money. On an energy supplier's site the audit reported dozens of
pages with identical content across two groups and advised redirecting the extras. One group was
two URL variants of a tariffs page — genuine, and worth fixing.</p>

<p>The other was fifty-four pages that had nothing to do with each other: a heat-pump terms page,
an EV tariffs page, the blog, the press page, the help section. Every one recorded exactly the
same short word count, across eighteen distinct top-level sections. Re-fetched by hand afterwards,
those same URLs served thousands of words of entirely different content.</p>

<p>The site had handed the crawler one short shared body — a holding page, an error template, a
bot-protection interstitial — and the audit judged it as the site's own duplicate content.
<strong>The finding was true about the bytes it received and dangerous as advice.</strong></p>

<h2>The rule that separates them</h2>

<p>Duplicate content comes from URL variants of one page, and variants share a section. So:</p>

<ul>
<li><strong>Several URLs in one section, sharing a full-length body</strong> — duplicate content.
Consolidate.</li>
<li><strong>Many URLs across many unrelated sections, sharing a short body</strong> — a server
handing out a placeholder. Nothing is duplicated; the tool simply was not shown those pages.</li>
</ul>

<p>The filter is deliberately narrow so the ordinary case survives it. A two-URL pair is untouched.
Several colour variants of one product are untouched, because they sit in one section and carry
full bodies. So is any large group whose shared body is substantial rather than placeholder-sized
— a real templated page with real content is a real duplicate-content problem.</p>

<h2>Checking your own group in two minutes</h2>

<ul>
<li><strong>Do the URLs share a section?</strong> If they are scattered across the site, treat the
finding as a fetch problem rather than a content problem.</li>
<li><strong>Is the shared body short?</strong> A few hundred words shared by pages that should be
long is a stand-in, not an article.</li>
<li><strong>Does the word count repeat exactly?</strong> Identical counts across unrelated pages
is the clearest single signal that one body was served to all of them.</li>
<li><strong>Re-fetch one by hand.</strong> Open it in a browser. If it is full of content, the
crawler was served something you were not.</li>
</ul>

<h2>When the finding is real</h2>

<p>Duplicate content is a genuine and common defect, and two shapes deserve the fix as written:</p>

<ul>
<li><strong>Filter and sort parameters</strong> generating an unbounded set of near-identical
pages from one listing.</li>
<li><strong>A site reachable at more than one address</strong> — with and without www, http and
https — serving the same pages at each. That is a server configuration rather than a content
problem, and it is usually a single fix.</li>
</ul>

<h2>The fixes that make it worse</h2>

<ul>
<li><strong>Redirecting before confirming the group is variants.</strong> The most expensive
mistake on this page. A permanent redirect tells every search engine and every visitor that the
page has moved for good, and taking it back does not restore what it cost.</li>
<li><strong>Adding noindex to the extras instead.</strong> Less destructive and still wrong when
the pages are not duplicates — you have hidden working pages because a crawl was served a
placeholder.</li>
<li><strong>Rewriting the pages to be different.</strong> Somebody has occasionally been told to
do this to unrelated pages that were never the same. Check what was actually served first.</li>
</ul>

<h2>How to make the finding disappear without fixing anything</h2>

<p>Crawl again when your server is not serving the placeholder, and the group vanishes. Which is
the same tell as everywhere else: <strong>if a re-run changes the finding, the finding was partly
about the run</strong> — see
<a href="/how-to/pages-an-audit-could-not-reach/">"could not be reached" is not a
diagnosis &rarr;</a>.</p>

<h2>Where this sits in an audit</h2>

<p>The registered check is <code>index.duplicate_content</code>, which covers duplicate pages. The
identifiers on its findings differ from the check's own, which matters when you search for one by
name.</p>

<p>For the related case where two pages are not identical but are competing anyway, see
<a href="/how-to/fix-pages-competing-for-one-search/">when your own pages compete &rarr;</a>.
For why a remedy that removes something deserves more proof than one that adds something, see
<a href="/how-to/sitemap-urls-that-are-not-stale/">when "regenerate your sitemap" is
wrong &rarr;</a>.</p>
"""
    return render(
        cat="how-to", slug="identical-content-three-causes",
        title="Identical content is not always duplicate",
        desc=("Three reasons pages share a body, and only one is duplicate content. Why an audit "
              "told a site to redirect its own blog away."),
        h1="Identical content is not always duplicate content",
        crumb='<a href="/">Docket</a> / <a href="/how-to/">Fix it</a> / Identical bodies',
        body=body,
        faq=[
            ("My audit says unrelated pages have identical content. Why?",
             "Almost always because the server served the crawler one short shared body — a "
             "holding page or an interstitial — rather than the real pages. Re-fetch one by hand "
             "before acting on it."),
            ("Should I redirect pages an audit calls duplicates?",
             "Only after confirming they are URL variants of one page. Variants share a section "
             "of the site; a group scattered across unrelated sections is a fetch problem, and a "
             "permanent redirect is not undone by noticing."),
            ("Do pages that all declare the same canonical still count as duplicates?",
             "No. If every page in the group names one canonical, the site has already resolved "
             "it and one URL gets indexed. A group whose members declare different canonicals, "
             "or none, is the one that matters."),
            ("Are product colour variants duplicate content?",
             "They can be, and they are the ordinary case the rule is built to keep. They sit in "
             "one section and carry full bodies, so they are treated as genuine variants rather "
             "than as a server problem."),
            ("How do I tell a placeholder from real duplicate content?",
             "Look at the word count. Unrelated pages recording exactly the same short count, "
             "across many sections of the site, is one body served to all of them rather than "
             "content anybody wrote twice."),
        ],
    )


if __name__ == "__main__":
    print(identical_bodies())
