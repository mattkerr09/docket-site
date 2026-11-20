#!/usr/bin/env python3
"""Content-audit process, sourced to the supplied 20 November Ahrefs read."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from render import N_CHECKS, N_LANES, render
from comparisons import source_link
from ahrefs_first_screen import AUDIT, CONTENT, FREE, FREE_CREDITS, ISSUES, PLANS, checked  # noqa: E402

#: The day the Ahrefs pricing and Site Audit pages were last searched for a product called Content Audit.
CHECKED_HUMAN = "20 November 2026"


def content_audit() -> Path:
    body = f"""
<p id="measured-answer">If you searched for an Ahrefs content audit, Ahrefs does not sell one: no separate tool of that name was listed on its pricing, Site Audit or Webmaster Tools pages read.
Its {source_link("content-audit blog", CONTENT)} describes a process of reviewing pages and improving what holds them back.
The crawler is Site Audit, whose {source_link("product page", AUDIT)} lists {ISSUES}+ SEO and AEO issues; {source_link("Ahrefs Free", FREE)} gives {FREE_CREDITS:,} crawl credits per verified project per month.</p>
{checked("Ahrefs", ("Pricing", PLANS), ("Site Audit", AUDIT), ("Webmaster Tools", FREE), ("Content-audit process", CONTENT))}

<h2>What a content audit actually answers</h2>

<p>Four questions, and they are separable:</p>

<ul>
<li><strong>What have we published?</strong> A complete list. Most sites cannot produce one, and
almost every audit that stalls stalls here.</li>
<li><strong>What is each page for?</strong> One page per intent. Two pages chasing the same
thing compete with each other and split whatever authority they earn.</li>
<li><strong>Is it good enough to rank?</strong> Depth against what already ranks: a judgement,
not a measurement, and the part no tool finishes for you.</li>
<li><strong>Can it be seen at all?</strong> Indexable, in the HTML, not duplicated, not orphaned.
Entirely mechanical, and where most of the real damage hides.</li>
</ul>

<p>The last one is worth doing first, because a brilliant page that a crawler cannot read is a
worse problem than a mediocre one that it can, and it is far cheaper to fix.</p>

<h2>Use Site Audit to start the page list</h2>
<p>Ahrefs' content-audit blog describes using Site Audit to collect URLs, then exporting
internal HTML URLs returning status code 200. That gives you a list to review. It does not
decide which pages deserve to stay or what each page should say.</p>
<p>Ahrefs Free is the current name for Webmaster Tools. Its verified-site allowance is
{FREE_CREDITS:,} crawl credits per project per month. If you are weighing the crawling part,
read <a href="/vs/ahrefs-site-audit-alternative/">Check Engine vs Ahrefs Site Audit</a> for
the paid limits as well.</p>
{checked("Ahrefs", ("Collecting and exporting URLs", CONTENT), ("Free crawl allowance", FREE))}

<h2>The order that wastes least time</h2>

<p><strong>1. Get the list.</strong> Crawl your own site and export every indexable URL. Not the
sitemap: the sitemap is what you claim you have. The crawl is what a crawler can actually reach,
and the difference between those two lists is itself a finding.</p>

<p><strong>2. Separate thin from invisible.</strong> These look identical in a spreadsheet and
have opposite remedies. A genuinely thin page needs writing or removing. A page whose body
arrives via JavaScript needs server-rendering: writing more would not help, and deleting it
would be a mistake. Docket labels a word count as a count of the HTML as served when a page
carries a framework's hydration marker, precisely because the two get confused;
<a href="/how-to/javascript-seo-audit/">the JavaScript SEO audit procedure</a> is how you tell
them apart on a single URL.</p>

<p><strong>3. Find the pages competing with each other.</strong> Duplicate and near-duplicate
titles are the cheapest signal: see
<a href="/how-to/fix-duplicate-title-tags/">fixing duplicate title tags</a>. Where two pages
genuinely serve one intent, merge and redirect rather than rewriting both.</p>

<p><strong>4. Check what is claiming to be canonical.</strong> A page that points its canonical
elsewhere has opted out of ranking, sometimes by accident.
<a href="/learn/canonical-tags/">Canonical tags are a hint, not an instruction</a>, and the
common failure is a template applying one site-wide.</p>

<p><strong>5. Only now, judge quality.</strong> With the mechanical problems cleared you are
reading a much shorter list, and you are reading it about pages that can actually rank.</p>

<h2>Index pages are not thin pages</h2>

<p>A category listing, an A to Z, a tag or author page: its purpose is to point elsewhere, and a low
word count is normal. Every automated content audit flags these, and the advice it gives is
wrong three ways: do not write copy on it, do not merge it, and do not delete it, because other
pages link to it. Judge it on whether the list is worth having and whether anything links to it.
This is a limit worth knowing about whatever tool you use, and Docket says so in the finding
itself rather than leaving you to discover it.</p>

<h2>What Docket does for the mechanical half</h2>

<p>Docket runs {N_CHECKS} checks across {N_LANES} areas on your machine, and the content area
covers the fourth question: pages with almost no body text, pages in the thin band above them,
archive pages that list almost nothing, utility pages that should not be indexed at all, titles
duplicated across pages, and pages whose content is not in the HTML the server sends. It reports
which of those it measured on the served HTML rather than on a rendered page, because that
distinction changes the remedy.</p>

<p>What it does not do: tell you whether a page is <em>good</em>. It has no index of what
competitors published, no keyword volumes, and no opinion about what people search for. If the
question you actually have is "what should I write next", a tool for researching topics is
what you need. The full list of what is and is not covered is
<a href="/learn/what-docket-checks/">what Docket checks</a>, and the wider procedure is
<a href="/learn/seo-audit/">the technical SEO audit</a>.</p>

<h2>Doing it more than once</h2>

<p>A content audit is usually run as a one-off and then not again until the next reorganisation,
which is why the same problems reappear. The mechanical half is worth re-running on a schedule:
<a href="/learn/site-monitoring/">site monitoring</a> is that, and it is different work from a
crawl in that it tells you what changed rather than what is true today. If you want the
server's own record of which pages a crawler actually fetched, that is
<a href="/learn/log-file-analysis/">log file analysis</a>.</p>

<p>And if the reason for the audit is that traffic arrives and does nothing, the content is
probably not the constraint: <a href="/learn/conversion-audit/">a conversion audit</a> asks a
different question of the same pages. If the audit turns up short pages, what to do with each
one is at <a href="/how-to/fix-thin-content-pages/">how to fix thin content pages</a>.</p>

<p><a class="btn" href="/download/">Download Docket</a></p>
""".replace("{N_CHECKS}", str(N_CHECKS)).replace("{N_LANES}", str(N_LANES))
    return render(
        cat="how-to", slug="content-audit",
        title="Content audit with Ahrefs: which tool does what",
        desc=("Ahrefs sells no product called Content Audit. What the job is, which of their "
              "tools covers which part, and the order that wastes least time."),
        h1="How to do a content audit",
        crumb='<a href="/">Docket</a> / <a href="/how-to/">Fix it</a> / Content audit',
        body=body,
        published="2026-09-09",
        modified="2026-11-20",
        faq=[
            ("Does Ahrefs have a content audit tool?",
             f"Ahrefs does not sell one under that name on the pages read. Its blog describes a process, "
             f"and Site Audit is the crawler used to collect URLs. {source_link('Content-audit process', CONTENT)} "
             f"and {source_link('Ahrefs pricing', PLANS)}. Checked {CHECKED_HUMAN}."),
            ("What should a content audit start with?",
             "A complete list of your indexable pages, taken from a crawl rather than from your "
             "sitemap. The sitemap says what you claim to have published; the crawl says what a "
             "crawler can reach, and the gap between the two is a finding in itself."),
            ("Why is a short page not automatically a problem?",
             "Because index pages are short on purpose. A category listing, an A to Z or a tag "
             "page exists to point elsewhere, and the usual advice to write more, merge it or "
             "delete it is wrong for all three. Judge it on whether the list is worth "
             "having and whether anything links to it."),
            ("Can a tool tell me whether my content is good?",
             "No, and one that claims to is scoring a proxy. Tools are reliable on the "
             "mechanical questions: is it indexable, is it duplicated, is it in the HTML, "
             "and those are worth clearing first, because they are cheap and they support "
             "everything else. The judgement about depth stays yours."),
        ],
    )


BUILDERS = [content_audit]


def build_all() -> list[Path]:
    return [b() for b in BUILDERS]


if __name__ == "__main__":
    for p in build_all():
        print(p)
