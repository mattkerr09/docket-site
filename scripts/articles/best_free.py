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
from render import CHROME_ADDON, FREE_LINE, PRICE_COMPACT, render, with_next_step  # noqa: E402


def free_seo_audit_tools() -> Path:
    body = f"""
<p class="lede">For a free SEO audit, use a page checker for faults on one URL, a crawler for
faults across a site, and Search Console for what Google has seen. The tools below do different
jobs. Start with the question you need answered and check the free limit before you run an audit.
We make Docket, including the free checker listed here.</p>

<div class="callout compact" id="try-now">
<p><strong>Want to audit your website free, right now?</strong> Paste a page into Docket's free SEO
checker for a score, the problems on that page and the first fix, in a few seconds, with no sign-up.</p>
<p><a class="btn" href="/tools/seo-checker/" data-ev="Free check" data-ev-button="best-free-checker-box">Check a page free</a></p>
</div>

<h2>Which free SEO audit tool fits the job?</h2>
<div class="wrap-tbl"><table class="cmp">
<caption>Free website audit tools and their limits</caption>
<thead><tr><th scope="col">Tool</th><th scope="col">Use it for</th><th scope="col">Free limit</th></tr></thead>
<tbody>
<tr><th scope="row">Google Lighthouse</th><td>Page speed and basic SEO checks</td>
<td>One page at a time, not a whole-site crawl</td></tr>
<tr><th scope="row">Google Search Console</th><td>Search queries and indexing in Google</td>
<td>A verified property; reports have row limits and a delay</td></tr>
<tr><th scope="row">Screaming Frog</th><td>Crawling a small site for links, redirects and duplicate titles</td>
<td>Up to 500 URLs in the free tier</td></tr>
<tr><th scope="row">Docket SEO checker, ours</th><td>A page score, its problems and the first fix</td>
<td>One page; no speed test or checks between pages</td></tr>
</tbody></table></div>
<p>New to audits? <a href="/learn/seo-audit/">What an SEO audit includes</a> gives you a checklist.
For a single access question, the <a href="/tools/robots-txt-tester/">robots.txt tester</a> shows
which rule allows or blocks a page.</p>

<h2>Google Lighthouse: free, open source, already installed</h2>

<p>Lighthouse is "an open-source, automated tool" you can run from Chrome DevTools, the command
line, a Node module or a web UI. If you use Chrome, you already have it: open DevTools, pick
Lighthouse, run it.</p>

<p><strong>What it is genuinely good at:</strong> performance on a single page, measured
properly. It is also what powers PageSpeed Insights, which "uses Lighthouse to analyze the
given URL in a simulated environment" for its lab data.</p>

<p><strong>What it does not do, in its own words:</strong> its SEO category declares ten
scored audits and describes itself as "basic search engine optimization advice", noting that
there are more checks it does not perform. It is also <em>per page</em>. It has no concept of
your site as a whole, so orphan pages, canonical conflicts across templates and hreflang
reciprocity are all invisible to it by design.</p>

<h2>Google Search Console: free, and Google's own data about your site</h2>

<p>Search Console tells you what Google did with your site: which queries brought
impressions, which pages were indexed and which were not. It is free, and for anything about
your standing in Google specifically it is the primary source.</p>

<p><strong>The limits are published and worth knowing before you rely on it.</strong> Reports
show "a maximum of 1,000 rows, so some rows might be omitted". Data is not live: "normally,
however, collected data should be available in 2-3 days". Google "might not track some queries
that are made a very small number of times", so the long tail is partly absent. The URL
Inspection API is capped at "2000 QPD" and "600 QPM" per site. These limits cap how fast
a large site can be inspected page by page, even by script.</p>

<p>Its Core Web Vitals report is field data: "the data for the Core Web Vitals report comes
from the CrUX report", gathered from real visitors. That is more truthful than any simulation, and it needs enough traffic to exist. How much is not published: "An exact number is not
disclosed."</p>

<p><strong>And it only works on sites you own.</strong> You verify the property first, which
makes it useless for looking at a competitor, or at a site you are about to take on as a
client.</p>

<h2>Screaming Frog, free tier: a real crawler, capped</h2>

<p>The free tier is limited to 500 URLs. For a small brochure site that is the whole site, and
you get an actual crawl rather than a page-at-a-time check: redirect chains, broken links,
<a href="/how-to/fix-duplicate-title-tags/">duplicate titles across pages</a>.
If you need more than the free tier, <a href="/best/screaming-frog-alternatives/">the Screaming Frog alternatives for Mac and Windows</a>
sets the paid and free ones side by side.</p>

<p>It is the right free answer for anyone comfortable reading crawl data and deciding what
matters. If a spreadsheet of every URL and its status codes is a useful artefact to you rather
than a wall of numbers, take this one.</p>

<h2>Docket's free SEO checker: one page, no sign-up</h2>

<p>We make this one, so read it with that in mind. Paste the address of any page into the
<a href="/tools/seo-checker/" data-ev="Free check" data-ev-button="best-free-checker-entry">free SEO checker</a>
and it returns a score out of 100, the problems on that page by area, and the worst one in full
with the change that fixes it. It runs in your browser with nothing to install, and it works on any
site, yours or a competitor's, so there is nothing to verify first.</p>

<p><strong>What it checks:</strong> whether Googlebot, Bingbot and the AI search crawlers may read
the page, noindex and canonical tags, redirects and HTTPS, the width of the title and description,
headings, structured data and sharing tags. <strong>What it does not:</strong> speed, which is
Lighthouse's job, and anything between pages, because it reads one page at a time.</p>

<h2>Is there a free SEO audit plugin?</h2>
<p>For Chrome, our free <a href="{CHROME_ADDON}" rel="noopener" data-ev="Install"
data-ev-button="best-free-addon">Docket SEO add-on</a> checks the page in the tab you are on,
in your browser, with nothing uploaded and no account. It is a page check, not a whole-site crawl.</p>

<h2>What does a free SEO audit report show?</h2>
<p>The online checker shows a page score, problems by area and the top problem with its fix.
It does not audit the whole website. For a site audit, Docket's download runs on your computer.
{FREE_LINE} The free result is a starting point, not the full paid report.</p>

<h2>So when is anything paid worth it?</h2>

<p>When the free version you use has stopped answering your question:</p>

<ul>
<li><strong>More than 500 URLs</strong>, where the free crawl tier stops.</li>
<li><strong>Whole-site relationships</strong>: a canonical pointing at a noindex page, an
hreflang set that is not reciprocated, a page nothing links to. These need a site crawl,
not just a per-page check.</li>
<li><strong>Being told what to do first.</strong> Every tool above hands you findings. Ordering
them by what they cost you is a separate job from finding them.</li>
</ul>

<p>If the paid tool you already have is Ahrefs, its crawler is <a href="/vs/ahrefs-site-audit-alternative/">Ahrefs Site Audit</a>; our comparison
sets out what it checks and how a crawl is paid for.</p>

<p>Docket's paid version is {PRICE_COMPACT} and adds the full ranked plan.
If the free tools already tell you what to fix, keep using them. For a paid crawler or platform,
<a href="/vs/se-ranking-vs-screaming-frog/">SE Ranking vs Screaming Frog</a> sets out the
different ways their audits are paid for.</p>

<p><a class="btn" href="/download/">Download Docket</a> ·
<a href="/vs/">see how it compares, tool by tool</a></p>

{_verified_note('lighthouse')}
{_verified_note('search-console')}
{_verified_note('screaming-frog')}
"""
    return render(
        cat="best", slug="free-seo-audit-tools",
        modified="2026-11-09",
        title="Free SEO audit tools: uses and limits | Docket",
        desc=("Run a free SEO audit of a page or small site. Compare website audit tools, "
              "free limits, a Chrome plugin and what the free report shows."),
        h1="Free SEO audit tools and their limits",
        crumb='<a href="/">Docket</a> / <a href="/best/">Best</a> / free SEO audit tools',
        body=body,
        faq=[
            ("Is there a free SEO audit plugin?",
             "Yes. Our free Docket SEO add-on for Chrome checks the page in the tab you are on, "
             "in your browser, with nothing uploaded and no account. It checks one page, not the whole site."),
            ("What does a free SEO audit report include?",
             "Docket's free online checker shows a page score, problems by area and the top "
             "problem with its fix. The free desktop download gives a site score, counts by "
             "category and the top problem in full. The rest of the problems and ranked plan are paid."),
            ("What is the best free SEO audit tool?",
             "For a single page, Lighthouse. It is open source, built into Chrome DevTools, "
             "and powers PageSpeed Insights. For how Google actually treats your site, Search "
             "Console. For crawling a small site, Screaming Frog's free tier, capped at 500 "
             "URLs."),
            ("Can I audit my website free without signing up?",
             "Our free Docket SEO checker checks one page in the browser with no sign-up. "
             "Lighthouse runs inside Chrome, and Screaming Frog's free tier crawls up to 500 URLs."),
            ("Is Google Lighthouse enough for SEO?",
             "For one page at a time, often. Its SEO category describes itself as “basic "
             "search engine optimization advice” and notes there are checks it does not "
             "perform, and it has no view of your site as a whole, so canonical conflicts, "
             "hreflang reciprocity and orphan pages are invisible to it."),
            ("Why can't Search Console tell me everything?",
             "Its limits are published: reports show at most 1,000 rows, data lags by about "
             "two to three days, very rare queries may not be tracked, and it only works on "
             "properties you have verified, so it cannot look at a competitor's site."),
            ("When is a paid SEO audit tool worth it?",
             "When a site is bigger than the free crawl tier, when the problems are "
             "relationships between pages rather than faults on one page, or when you need "
             "the findings ordered rather than listed. Below that, the free tools are enough."),
        ],
    )


def best_hub() -> Path:
    body = """
<p class="lede">Which tool to use, by the job you are actually doing. Every claim about a named
product here was read from that product's own documentation and is dated on the page, because a recommendation that cannot be checked is an advertisement.</p>

<h2>Free SEO audit tools</h2>
<p>Three genuinely free tools cover most of what a small site needs, and two of them are made
by Google. What each does, the limits its own documentation states, and the three specific
points where paying starts to help.
<a href="/best/free-seo-audit-tools/">The best free SEO audit tools →</a></p>

<h2>Screaming Frog alternatives</h2>
<p>Crawlers and audit tools for Mac and Windows, set beside Screaming Frog: what each costs, which computers it runs on,
how much it crawls, and when it is the better choice. Ours is one of them and is labelled as ours.
<a href="/best/screaming-frog-alternatives/">Screaming Frog alternatives for Mac and Windows →</a></p>

<h2>White-label SEO audit tools</h2>
<p>The tools that put your own name on an audit report, with what the white-label part of each one is, what a year of it
costs, and when each is the better choice. Ours is one of them and is labelled as ours.
<a href="/best/white-label-seo-audit-tools/">White-label SEO audit tools for agencies →</a></p>

<h2>How a tool gets onto one of these pages</h2>
<p>There is no scoring formula and no ranking here, because a number invented to order a list is
still invented. A guide gets written when there is a job worth choosing a tool for, and it names
the tool that does that job best, which is regularly not ours.</p>
<ul>
<li><strong>Every capability claim comes from the vendor.</strong> Not from a review, not from a
comparison table someone else built, and not from memory. Where a page says a tool does or does
not do something, it is reading that tool's own documentation or published feature list, with a
link and the date it was read. Documentation changes; an undated claim is one you cannot check.</li>
<li><strong>A missing feature is written up as a missing claim.</strong> If a vendor's own pages
never mention something, that is what the page says, not that the product is incapable of
it. Those are different statements, and only one of them is evidence.</li>
<li><strong>Prices are the vendor's, in the vendor's own terms.</strong> Taken from their pricing
page, in the currency and billing period that page states, and dated like everything else.</li>
<li><strong>No link on this site earns a commission.</strong> There are no affiliate parameters on
any outbound link here, and nothing paid to be listed.</li>
</ul>

<h2>We make one of the tools</h2>
<p>Docket is ours, which is exactly why every sentence about it deserves checking, so the method above is pointed back at us too. Every comparison page on this site names what the other
tool does better than Docket. One of them says plainly that a competitor is cheaper. Where Docket
has no answer at all (rendering at scale, Core Web Vitals, backlinks, rank tracking), the page covering that tool says so before it makes any case in our favour. A page here that
reads like an advertisement is a bug in the page.</p>

<h2>More coming</h2>
<p>Further guides are being written, one per job worth choosing a tool for.</p>
"""
    return render(
        cat="best", slug="",
        title="Best SEO tools, by the job you are doing | Docket",
        desc=("Which SEO tool fits which job on your site, with every claim read from the "
              "product's own "
              "documentation and dated on the page."),
        h1="Best tools, by job",
        crumb='<a href="/">Docket</a> / Best',
        body=with_next_step(body, "hub-best"),
        schema_type="CollectionPage",
    )


if __name__ == "__main__":
    print(free_seo_audit_tools())
