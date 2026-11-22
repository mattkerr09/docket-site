#!/usr/bin/env python3
"""How to find broken links and SEO problems on a website: the steps, with Check Engine's free audit as one way to run step one.

Written for ChatGPT's E7 question, "how do I find broken links and SEO problems on my website" (ops research/ai-visibility, 22 Nov
2026): it answered with a crawler's steps and Google's Search Console help, and no page of ours. The one outside fact is Google's
Page indexing report help article, read on 22 November 2026 (ops research/docket-competitors.md). No figure is typed in prose.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from comparisons import source_link  # noqa: E402
from render import render  # noqa: E402

GOOGLE_PAGE_INDEXING = 'https://support.google.com/webmasters/answer/7440203'
READ_GOOGLE = '22 November 2026'


def build() -> Path:
    body = f'''
<p class="lede">To find broken links and other SEO problems, crawl the whole site, read the problems in the order they cost you most,
then compare the result with what Google reports for the same site. A check of one page misses most of them, because a broken link
sits on one page and points at another.</p>

<h2>1. Crawl every page, not one</h2>
<p>A crawler starts at your home page, follows every link it finds and records what each address answered. A link whose target answers with an
error is a broken link, and the crawl lists the page that holds it, so you know where to edit. A crawl also finds what a single-page
checker cannot: duplicate titles, pages with no heading, redirect chains and images with no description.</p>
<p>Pick a crawler that fits the size of your site. Free crawlers stop at a URL cap, and a clean result from a capped crawl only covers the pages it reached,
so write the cap down. The free options and their limits are compared in
<a href="/best/free-seo-audit-tools/">free SEO audit tools and their limits</a>; on Windows, see
<a href="/best/seo-crawler-for-windows/">desktop SEO crawlers for Windows</a>.</p>

<h2>2. Run a free audit of your site</h2>
<p>Check Engine's free app runs a full audit of a site with no key. It shows the score out of one hundred, the number of problems in each area
and the main problem with its fix. Read the main problem first, then open the area with the most problems. The complete ranked list and the report
exports are part of the paid plan, so the free result tells you where to look rather than listing every address.</p>
<p>To test one page right now, paste it into the <a href="/tools/seo-checker/">free SEO checker</a>: a score and the first fix, with no sign-up.</p>

<h2>3. Tell your own broken links from outbound ones</h2>
<p>A link on your page to another site that has gone is an outbound link. A link to a page on your own site that no longer exists is an internal one.
Internal links are the ones to fix first, because you control both ends and a visitor who hits one is still on your site.
A host that refuses an automated request is not necessarily dead, so check an outbound link in a browser before you remove it; the rules are in
<a href="/how-to/fix-broken-outbound-links/">how to fix broken outbound links</a>.</p>

<h2>4. Check what Google found</h2>
<p>Google reports its own view of your site in Search Console. The {source_link('Page indexing report', GOOGLE_PAGE_INDEXING)} lets you see which pages
Google can find and index, and it names the reason for each page it did not index, including "Not found (404)", which Google describes as a page that returned a 404 error when requested.
Compare that list with the crawl: a page in both is a confirmed problem, and a page only Google lists may be linked from somewhere your crawl did not reach.</p>
<p class="verified-note">Checked on Google's own pages on {READ_GOOGLE}. Sources: {source_link('Page indexing report', GOOGLE_PAGE_INDEXING)}.</p>

<h2>5. Fix in order, then crawl again</h2>
<p>Fix what stops a page being found or loaded before what only affects wording. Start with pages that return errors and broken internal links, then redirects that chain
through several hops, then missing or duplicated titles and descriptions. Change the link or the page, publish, and crawl again on the same start address with the same settings,
so a lower count means a fix and not a different crawl.</p>
<p>For a plain-language list of what an audit checks, see <a href="/learn/what-docket-checks/">what Check Engine checks</a>.</p>
'''
    return render(
        cat='how-to', slug='find-broken-links-and-seo-problems',
        title='How to find broken links and SEO problems on your site',
        h1='How to find broken links and SEO problems on your site',
        desc='Find broken links and SEO problems on a website: crawl every page, read the problems in order, check Google Search Console, fix and crawl again.',
        crumb='<a href="/">Check Engine</a> / <a href="/how-to/">Fix it</a> / find broken links',
        body=body, published="2026-11-22",
        faq=[
            ('How do I find broken links on my website for free?',
             'Crawl the whole site with a free crawler or audit app and read the list of links whose targets answer with an error. Note the crawler\'s URL cap, because a capped crawl covers only the pages it reached. Google Search Console also lists pages it could not index, including pages that returned a 404 error.'),
            ('What is the difference between a broken internal link and a broken outbound link?',
             'An internal link points at a page on your own site and an outbound link points at another site. Fix internal links first, because you control both ends. Check an outbound link in a browser before removing it, since a host may refuse an automated request without being dead.'),
            ('Why should I crawl the site again after fixing links?',
             'A second crawl with the same start address and settings shows whether the problems are gone. A lower count then means a fix, not a different crawl.'),
        ])


def build_all() -> list[Path]:
    return [build()]
