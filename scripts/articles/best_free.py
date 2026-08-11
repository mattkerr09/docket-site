#!/usr/bin/env python3
"""/best/ — the section this site did not have.

Every "best free tool" page written by a vendor has the same problem: the
vendor sells one of the tools. This one answers the question anyway, and the
answer is mostly "use the free ones" — because for a lot of readers that is
true, and a page that pretends otherwise is not worth publishing.

Every claim about a named product comes from `comparisons.VERIFIED`, read from
that product's own pages on `CHECKED_ON` and rendered with the dated note
`lint.py` requires. Nothing here is a recollection.

Docket's own limitation is stated in the same breath as its pitch, per the
house rule: it costs money, and this page says when not to spend it.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from comparisons import _verified_note  # noqa: E402
from render import PRICE_STR, render  # noqa: E402


def free_seo_audit_tools() -> Path:
    body = f"""
<p class="lede">Three genuinely free tools cover most of what a small site needs, and two of
them are made by Google. If you are looking for a free SEO audit, start here and stop reading
when you have enough — this page is on the site of a tool that costs {PRICE_STR}, and most
readers should not buy it.</p>

<h2>Google Lighthouse — free, open source, already installed</h2>

<p>Lighthouse is "an open-source, automated tool" you can run from Chrome DevTools, the command
line, a Node module or a web UI. If you use Chrome, you already have it: open DevTools, pick
Lighthouse, run it.</p>

<p><strong>What it is genuinely good at:</strong> performance on a single page, measured
properly. It is also what powers PageSpeed Insights, which "uses Lighthouse to analyze the
given URL in a simulated environment" for its lab data. For "why is this page slow", nothing
free is better.</p>

<p><strong>What it does not do, in its own words:</strong> its SEO category declares ten
scored audits and describes itself as "basic search engine optimization advice", noting that
there are more checks it does not perform. It is also <em>per page</em> — it has no concept of
your site as a whole, so orphan pages, canonical conflicts across templates and hreflang
reciprocity are all invisible to it by design.</p>

<h2>Google Search Console — free, and the only source of real Google data</h2>

<p>Nothing else tells you what Google actually did with your site: which queries brought
impressions, which pages were indexed and which were not. It is free, and for anything about
your standing in Google specifically it is the primary source.</p>

<p><strong>The limits are published and worth knowing before you rely on it.</strong> Reports
show "a maximum of 1,000 rows, so some rows might be omitted". Data is not live — "normally,
however, collected data should be available in 2-3 days". Google "might not track some queries
that are made a very small number of times", so the long tail is partly absent. The URL
Inspection API is capped at "2000 QPD" and "600 QPM" per property, which means a site of any
size cannot be inspected page by page even by script.</p>

<p>Its Core Web Vitals report is field data: "the data for the Core Web Vitals report comes
from the CrUX report", gathered from real visitors. That is more truthful than any simulation —
and it needs enough traffic to exist. How much is not published: "An exact number is not
provided."</p>

<p><strong>And it only works on sites you own.</strong> You verify the property first, which
makes it useless for looking at a competitor, or at a site you are about to take on as a
client.</p>

<h2>Screaming Frog, free tier — a real crawler, capped</h2>

<p>The free tier is limited to 500 URLs. For a small brochure site that is the whole site, and
you get an actual crawl rather than a page-at-a-time check: redirect chains, broken links,
duplicate titles across pages.</p>

<p>It is the right free answer for anyone comfortable reading crawl data and deciding what
matters. If a spreadsheet of every URL and its status codes is a useful artefact to you rather
than a wall of numbers, take this one.</p>

<h2>So when is anything paid worth it?</h2>

<p>When the free ones have stopped answering your question, which happens in three specific
places:</p>

<ul>
<li><strong>More than 500 URLs</strong>, where the free crawl tier stops.</li>
<li><strong>Whole-site relationships</strong> — a canonical pointing at a noindex page, an
hreflang set that is not reciprocated, a page nothing links to. None of these exist on any
single page, so no per-page tool can see them.</li>
<li><strong>Being told what to do first.</strong> Every tool above hands you findings. Ordering
them by what they cost you is the part that takes an expert, and it is the part a free tool
does not attempt.</li>
</ul>

<p>Docket is {PRICE_STR} paid once, runs on your Mac, and answers
that third one: a ranked plan rather than a list. <strong>It is not free, and if your site is
under 500 URLs and you are comfortable reading Lighthouse and Search Console, you do not need
it.</strong> That is a real answer, not modesty — buying a tool to tell you what three free
ones already told you is a waste of {PRICE_STR}.</p>

<p><a class="btn" href="/download/">Download Docket</a> ·
<a href="/vs/">see how it compares, tool by tool</a></p>

{_verified_note('lighthouse')}
{_verified_note('search-console')}
{_verified_note('screaming-frog')}
"""
    return render(
        cat="best", slug="free-seo-audit-tools",
        title="The best free SEO audit tools (and when to stop)",
        desc=("Three genuinely free tools cover most of what a small site needs. What each "
              "one does, the limits its own documentation states, and when paying helps."),
        h1="The best free SEO audit tools",
        crumb='<a href="/">Docket</a> / <a href="/best/">Best</a> / free SEO audit tools',
        body=body,
        faq=[
            ("What is the best free SEO audit tool?",
             "For a single page, Lighthouse — it is open source, built into Chrome DevTools, "
             "and powers PageSpeed Insights. For how Google actually treats your site, Search "
             "Console. For crawling a small site, Screaming Frog's free tier, capped at 500 "
             "URLs."),
            ("Is Google Lighthouse enough for SEO?",
             "For one page at a time, often. Its SEO category describes itself as “basic "
             "search engine optimization advice” and notes there are checks it does not "
             "perform, and it has no view of your site as a whole — so canonical conflicts, "
             "hreflang reciprocity and orphan pages are invisible to it."),
            ("Why can't Search Console tell me everything?",
             "Its limits are published: reports show at most 1,000 rows, data lags by about "
             "two to three days, very rare queries may not be tracked, and it only works on "
             "properties you have verified — so it cannot look at a competitor's site."),
            ("When is a paid SEO audit tool worth it?",
             "When a site is bigger than the free crawl tier, when the problems are "
             "relationships between pages rather than faults on one page, or when you need "
             "the findings ordered rather than listed. Below that, the free tools are enough."),
        ],
    )


def best_hub() -> Path:
    body = """
<p class="lede">Which tool to use, by the job you are actually doing. Every claim about a named
product here was read from that product's own documentation and is dated on the page — because
a recommendation that cannot be checked is an advertisement.</p>

<h2>Free SEO audit tools</h2>
<p>Three genuinely free tools cover most of what a small site needs, and two of them are made
by Google. What each does, the limits its own documentation states, and the three specific
points where paying starts to help.
<a href="/best/free-seo-audit-tools/">The best free SEO audit tools →</a></p>

<h2>More coming</h2>
<p>Further guides are being written, one per job worth choosing a tool for.</p>
"""
    return render(
        cat="best", slug="",
        title="Best SEO tools, by the job you are doing — Docket",
        desc=("Which SEO tool fits which job, with every claim read from the product's own "
              "documentation and dated on the page."),
        h1="Best tools, by job",
        crumb='<a href="/">Docket</a> / Best',
        body=body,
        schema_type="CollectionPage",
    )


if __name__ == "__main__":
    print(free_seo_audit_tools())
