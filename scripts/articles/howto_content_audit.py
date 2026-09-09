#!/usr/bin/env python3
"""Content audit — the job, and which Ahrefs tool does which part of it.

Target query: "ahrefs content audit" (18 impressions, Search Console
2026-08-10 to 2026-09-05).

⚠️ THERE IS NO AHREFS PRODUCT CALLED "CONTENT AUDIT". Checked 2026-09-09:
zero occurrences on ahrefs.com/pricing and zero on ahrefs.com/site-audit.
Ahrefs' named tools are Site Explorer, Keywords Explorer, Site Audit, Rank
Tracker and Content Explorer. The phrase comes from the searcher, not from
Ahrefs, so this page is a how-to and not a /vs/ page — a URL or a title
implying a competitor sells a product they do not sell is a false claim about
their business, which is the thing this project polices hardest.

Everything said about Ahrefs' tools here is quoted from their own pages, read
2026-09-09, and nothing is inferred about features that were not read.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from render import N_CHECKS, N_LANES, render  # noqa: E402


def content_audit() -> Path:
    body = """
<p class="lede">If you searched for an Ahrefs content audit, the first useful thing to know is
that Ahrefs does not sell one. There is no product of that name. What exists is a job — going
through the pages you have published and deciding which to keep, improve, merge or remove — and
several tools that each do a slice of it. Knowing which slice saves you paying for the wrong
one.</p>

<h2>What a content audit actually answers</h2>

<p>Four questions, and they are separable:</p>

<ul>
<li><strong>What have we published?</strong> A complete list. Most sites cannot produce one, and
almost every audit that stalls stalls here.</li>
<li><strong>What is each page for?</strong> One page per intent. Two pages chasing the same
thing compete with each other and split whatever authority they earn.</li>
<li><strong>Is it good enough to rank?</strong> Depth against what already ranks — a judgement,
not a measurement, and the part no tool finishes for you.</li>
<li><strong>Can it be seen at all?</strong> Indexable, in the HTML, not duplicated, not orphaned.
Entirely mechanical, and where most of the real damage hides.</li>
</ul>

<p>The last one is worth doing first, because a brilliant page that a crawler cannot read is a
worse problem than a mediocre one that it can, and it is far cheaper to fix.</p>

<h2>What Ahrefs' real tools do for this</h2>

<p><strong>Content Explorer</strong> is described by Ahrefs as a way to "find top-performing
content, link prospects, and media opportunities in your niche" — content <em>ideas</em> on a
topic. It is an index of what other people have published. That is genuinely useful for deciding
what to write next, and it is the tool whose name most resembles the phrase people search for.
It is not looking at your site.</p>

<p><strong>Site Audit</strong> is the one that crawls your own pages — Ahrefs' own summary is
"audit &amp; optimize your website". It is a technical crawler: status codes, duplicate titles,
broken links, the mechanical fourth question above.</p>

<p><strong>Site Explorer</strong> holds their backlink and organic-traffic data, which is where
"which of my pages actually earn anything" comes from.</p>

<p>So the job is split across at least two products and the judgement is still yours. Nobody is
hiding a Content Audit button — the work simply does not live in one place. If you are weighing
the crawling half specifically, that comparison is on
<a href="/vs/ahrefs-site-audit-alternative/">Docket vs Ahrefs Site Audit</a>, with dated prices
read from their pricing page.</p>

<h2>The order that wastes least time</h2>

<p><strong>1. Get the list.</strong> Crawl your own site and export every indexable URL. Not the
sitemap — the sitemap is what you claim you have. The crawl is what a crawler can actually reach,
and the difference between those two lists is itself a finding.</p>

<p><strong>2. Separate thin from invisible.</strong> These look identical in a spreadsheet and
have opposite remedies. A genuinely thin page needs writing or removing. A page whose body
arrives via JavaScript needs server-rendering — writing more would not help, and deleting it
would be a mistake. Docket labels a word count as a count of the HTML as served when a page
carries a framework's hydration marker, precisely because the two get confused;
<a href="/how-to/javascript-seo-audit/">the JavaScript SEO audit procedure</a> is how you tell
them apart on a single URL.</p>

<p><strong>3. Find the pages competing with each other.</strong> Duplicate and near-duplicate
titles are the cheapest signal — see
<a href="/how-to/fix-duplicate-title-tags/">fixing duplicate title tags</a>. Where two pages
genuinely serve one intent, merge and redirect rather than rewriting both.</p>

<p><strong>4. Check what is claiming to be canonical.</strong> A page that points its canonical
elsewhere has opted out of ranking, sometimes by accident.
<a href="/learn/canonical-tags/">Canonical tags are a hint, not an instruction</a>, and the
common failure is a template applying one site-wide.</p>

<p><strong>5. Only now, judge quality.</strong> With the mechanical problems cleared you are
reading a much shorter list, and you are reading it about pages that can actually rank.</p>

<h2>Index pages are not thin pages</h2>

<p>A category listing, an A–Z, a tag or author page — its job is to point elsewhere, and a low
word count is normal. Every automated content audit flags these, and the advice it gives is
wrong three ways: do not write copy on it, do not merge it, and do not delete it, because other
pages link to it. Judge it on whether the list is worth having and whether anything links to it.
This is a limit worth knowing about whatever tool you use, and Docket says so in the finding
itself rather than leaving you to discover it.</p>

<h2>What Docket does for the mechanical half</h2>

<p>Docket runs {N_CHECKS} checks across {N_LANES} areas on your machine, and the content lane
covers the fourth question: pages with almost no body text, pages in the thin band above them,
archive pages that list almost nothing, utility pages that should not be indexed at all, titles
duplicated across pages, and pages whose content is not in the HTML the server sends. It reports
which of those it measured on the served HTML rather than on a rendered page, because that
distinction changes the remedy.</p>

<p>What it does not do: tell you whether a page is <em>good</em>. It has no index of what
competitors published, no keyword volumes, and no opinion about what people search for. If the
question you actually have is "what should I write next", Content Explorer or a keyword tool is
the right purchase and Docket is not. The full list of what is and is not covered is
<a href="/learn/what-docket-checks/">what Docket checks</a>, and the wider procedure is
<a href="/learn/seo-audit/">the technical SEO audit</a>.</p>

<h2>Doing it more than once</h2>

<p>A content audit is usually run as a one-off and then not again until the next reorganisation,
which is why the same problems reappear. The mechanical half is worth re-running on a schedule —
<a href="/learn/site-monitoring/">site monitoring</a> is that, and it is a different job from a
crawl in that it tells you what changed rather than what is true today. If you want the
server's own record of which pages a crawler actually fetched, that is
<a href="/learn/log-file-analysis/">log file analysis</a>.</p>

<p>And if the reason for the audit is that traffic arrives and does nothing, the content is
probably not the constraint — <a href="/learn/conversion-audit/">a conversion audit</a> asks a
different question of the same pages.</p>

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
        faq=[
            ("Does Ahrefs have a content audit tool?",
             "Not under that name. Checked on their pricing and Site Audit pages, Ahrefs' named "
             "tools are Site Explorer, Keywords Explorer, Site Audit, Rank Tracker and Content "
             "Explorer. The work people mean by “content audit” is split across Site "
             "Audit for the technical side and Content Explorer for what others have published."),
            ("What is the difference between Content Explorer and Site Audit?",
             "Content Explorer indexes what other people have published, for finding ideas and "
             "link prospects in a niche. Site Audit crawls your own website. If the question is "
             "about your existing pages, Site Audit is the relevant half."),
            ("What should a content audit start with?",
             "A complete list of your indexable pages, taken from a crawl rather than from your "
             "sitemap. The sitemap says what you claim to have published; the crawl says what a "
             "crawler can reach, and the gap between the two is a finding in itself."),
            ("Why is a short page not automatically a problem?",
             "Because index pages are short on purpose. A category listing, an A–Z or a tag "
             "page exists to point elsewhere, and the usual advice — write more, merge it, "
             "delete it — is wrong for all three. Judge it on whether the list is worth "
             "having and whether anything links to it."),
            ("Can a tool tell me whether my content is good?",
             "No, and one that claims to is scoring a proxy. Tools are reliable on the "
             "mechanical questions — is it indexable, is it duplicated, is it in the HTML "
             "— and those are worth clearing first, because they are cheap and they gate "
             "everything else. The judgement about depth stays yours."),
        ],
    )


BUILDERS = [content_audit]


def build_all() -> list[Path]:
    return [b() for b in BUILDERS]


if __name__ == "__main__":
    for p in build_all():
        print(p)
