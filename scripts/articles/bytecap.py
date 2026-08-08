#!/usr/bin/env python3
"""Googlebot's 2MB cutoff, and how close real sites sit to it.

Every figure comes from site/_data/page-size-2026-08.json via facts.py. The
Google quotes were re-read from the source immediately before publishing,
because the page names the sites it measured.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import facts as F  # noqa: E402
from render import render  # noqa: E402

SOURCE = ("https://developers.google.com/search/blog/2026/03/"
          "crawler-blog-post")


def _over_table() -> str:
    rows = "".join(
        f"<tr><td>{site['host']}</td><td>{site['mb']} MB</td>"
        f"<td>{site['critical_kb']} KB</td></tr>"
        for site in F.size_over_list()
    )
    return ('<div class="wrap-tbl"><table class="cmp"><thead><tr>'
            "<th>Site</th><th>HTML served</th><th>Last required markup at</th>"
            "</tr></thead>"
            f"<tbody>{rows}</tbody></table></div>")


def byte_cap() -> Path:
    largest = F.size_largest()
    body = f"""
<p class="lede">Googlebot reads at most 2MB of any HTML page, headers included, and hands
that fragment to indexing as if it were the whole file. We measured the homepages of
{F.size_fetched()} well-known sites and found <strong>{F.size_over_cap()} already past the
cutoff</strong> — the largest, {largest['host']}, serving {largest['mb']} MB, which is
{largest['times_cap']} times the limit.</p>

<p>None of those {F.size_over_cap()} is losing markup Google requires. That is the honest headline and it is
the less alarming one: the title, canonical and structured data on every over-sized page we
measured sit comfortably inside the first 2MB. What they are losing is content, silently, with
nothing anywhere to say so.</p>

<h2>What Google actually says</h2>

<p>From <a href="{SOURCE}">the Search Central crawler post</a>, and the exact wording is the
whole point:</p>

<ul>
<li>Googlebot "crawls only the first 2MB of a resource, <strong>including the HTTP
header</strong>".</li>
<li>The portion it did get "is passed along to our indexing systems and the Web Rendering
Service <strong>as if it were the complete file</strong>".</li>
<li>Bytes past the threshold "aren't fetched, they aren't rendered, and they aren't
indexed".</li>
</ul>

<p>Read those together and the failure mode is specific. Google does not reject an oversized
page, does not report an error, and does not tell you in Search Console. It reads the first
2MB, treats it as the document, and moves on. A page whose structured data sits at 2.4 MB does
not have late structured data — <strong>it has none</strong>, from Google's point of view,
while every tool that reads that page from disk sees it perfectly.</p>

<p>Two limits people conflate with this one: PDFs get 64MB, and any crawler that sets no limit
of its own gets 15MB. Referenced files — your CSS, your JavaScript, your images — each have
their own separate budget and do not count against the parent page. Moving an inline block
into a linked file removes it from this problem outright.</p>

<h2>What we measured</h2>

<p>We fetched the homepage of every site in the Docket Index sample list on 2026-08-07 and
recorded two things: how many bytes came back, and how far into those bytes the last title,
canonical, meta robots directive and JSON-LD block sat. {F.size_fetched()} of
{F.size_attempted()} answered.</p>

<p>The median homepage is <strong>{F.size_median_kb()} KB</strong>, comfortably inside the
limit. The 90th percentile is <strong>{F.size_p90_kb()} KB</strong> — which is the number
worth sitting with, because it means one homepage in ten is already within a third of a cutoff
nobody mentions.</p>

{_over_table()}

<p>{largest['host']} is the striking one: {largest['mb']} MB served, with everything Google
needs inside the first {largest['critical_kb']} KB. More than half of that page is fetched by
nobody. It costs them nothing measurable today, and it is a large amount of work being done
for an audience that does not exist.</p>

<h2>The false positive we caught on the way</h2>

<p>The first version of this measurement reported that {largest['host']}'s
<strong>title tag</strong> sat at 2.48 MB, past the cutoff. That would have been the headline
of this page.</p>

<p>It was wrong. Inline SVG icons carry <code>&lt;title&gt;</code> elements as accessibility
labels, and the one at 2.48 MB reads "Close icon". Our rule took the <em>last</em> match for
every element, which is right for JSON-LD — each block is separate content, so a block past
the cutoff is data Google never gets — and wrong for a document title, which is the first one
and lives in the head. {largest['host']}'s real title is at {largest['critical_kb']} KB.</p>

<p>We are writing that down because it is the same mistake in both directions. The check
exists because tools read pages from disk and see things Google never received; the bug was
our tool reading a page from disk and seeing something that was not what it thought.</p>

<h2>Where another tool is better</h2>

<p><a href="/vs/screaming-frog-alternative/">Screaming Frog</a> reports page size across a
whole crawl and lets you sort and filter on it, at a scale Docket is not built for. If the
question is "which of my 400,000 URLs are heavy", that is the tool, and it has been doing it
for years.</p>

<p>What it will not tell you is which required markup falls past 2MB on the pages that are,
because that needs the byte offset of each element rather than the size of the file. That is
the part Docket adds, and it only matters on the pages Screaming Frog would have found for
you first.</p>

<h2>What to do if a page is over</h2>

<ol>
<li><strong>Find the weight.</strong> It is almost always one of three things: base64 images
inlined into the HTML, large inline CSS or JavaScript blocks, or navigation that renders
thousands of links before the content starts.</li>
<li><strong>Move inline blocks into linked files.</strong> They stop counting against the page
entirely — referenced resources each get their own budget.</li>
<li><strong>Put required markup in the head</strong> and keep it there. Structured data
injected at the end of the body is the common way to lose it.</li>
<li><strong>Check again after a redesign.</strong> Page weight grows; the limit does not.</li>
<li><strong>Remember this happens before rendering.</strong> If the page is also
<a href="/learn/javascript-rendering/">built by JavaScript</a>, the renderer only ever sees
the fragment that was fetched.</li>
</ol>

<p>Docket runs this as <code>index.byte_cap</code> on every audit, and reports the two cases separately: a page
merely over the limit is losing content, and a page whose required markup falls past the
cutoff is losing indexation. They are not the same problem and they do not deserve the same
urgency.</p>

<p><a class="btn" href="/download/">Download Docket</a></p>
"""
    return render(
        cat="learn", slug="googlebot-2mb-limit",
        title="Googlebot stops reading at 2MB and never tells you",
        desc=(f"Googlebot fetches 2MB of a page and indexes that as the whole file. We "
              f"measured {F.size_fetched()} homepages: {F.size_over_cap()} are already "
              f"past it."),
        h1="Googlebot stops reading at 2MB",
        crumb='<a href="/">Docket</a> / <a href="/learn/">Learn</a> / The 2MB limit',
        body=body,
        published="2026-08-07",
        faq=[
            ("How much of a page does Googlebot fetch?",
             "Up to 2MB of any individual URL, including the HTTP headers. PDFs get 64MB, "
             "and any crawler that sets no limit of its own defaults to 15MB. Referenced "
             "resources like CSS and images have their own separate budgets and do not "
             "count against the page that links them."),
            ("What happens to the rest of the page?",
             "Nothing. In Google's words the bytes past the threshold are not fetched, "
             "not rendered and not indexed, and the portion that was fetched is passed to "
             "indexing as if it were the complete file. There is no error and no Search "
             "Console report."),
            ("Is 2MB of HTML a realistic problem?",
             f"For most sites, no — the median homepage in our sample was "
             f"{F.size_median_kb()} KB. But {F.size_over_cap()} of {F.size_fetched()} "
             f"well-known sites we measured were already past it, and the 90th percentile "
             f"was {F.size_p90_kb()} KB, so one in ten is closer than its owners probably "
             f"think."),
            ("How do I make a page smaller?",
             "Move inline CSS, JavaScript and base64 images into linked files. That removes "
             "them from the page's budget completely, because every referenced resource has "
             "its own. Navigation that renders thousands of links before the content is the "
             "other common cause."),
        ],
    )


BUILDERS = [byte_cap]


def build_all() -> list[Path]:
    return [b() for b in BUILDERS]


if __name__ == "__main__":
    for p in build_all():
        print(p)
