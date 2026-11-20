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

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from comparisons import source_link
from real_questions_sources import READINGS
from ahrefs_first_screen import FREE, FREE_CREDITS, checked  # noqa: E402
from render import CHROME_ADDON, DATA, FREE_LINE, PRICE_COMPACT, render, with_next_step  # noqa: E402

_RUN = json.loads((DATA / "free-run.json").read_text())
_SF_YEAR = re.search(r"\$\d+", READINGS["rq-screaming-frog"][1][0]).group()


def free_seo_audit_tools() -> Path:
    body = f"""
<p id="measured-answer">A free SEO audit can find problems, but its crawl limit or locked report can leave work unseen.
Check Engine's <a href="/vs/screaming-frog-alternative/">recorded free audit</a> read {_RUN["pages"]} pages and found {_RUN["problems"]} problems; the free download shows the score, counts and top fix, while the full plan is paid.
{source_link("Screaming Frog", "https://www.screamingfrog.co.uk/seo-spider/")} allows up to 500 URLs per free crawl, and {source_link("Ahrefs Free", FREE)} gives {FREE_CREDITS:,} crawl credits per verified project per month.
{source_link("Semrush's free account", "https://www.semrush.com/prices/")} lists 1 demo project and 10 reports per day; the pages read do not state a per-audit page limit.</p>
{checked("Screaming Frog, Ahrefs and Semrush", ("SEO Spider", "https://www.screamingfrog.co.uk/seo-spider/"), ("Ahrefs Free", FREE), ("Semrush free account", "https://www.semrush.com/prices/"))}

<h2>Which free SEO audit tool fits the task?</h2>
<div class="wrap-tbl"><table class="cmp">
<caption>Free website audit tools and their limits</caption>
<thead><tr><th scope="col">Tool</th><th scope="col">Use it for</th><th scope="col">Free limit</th></tr></thead>
<tbody>
<tr><th scope="row">Google URL Inspection live test</th><td>Check whether Google's inspection fetcher can access a page for indexing</td>
<td>A live test of the entered URL</td></tr>
<tr><th scope="row">Screaming Frog</th><td>A free desktop crawl</td>
<td>Up to 500 URLs per crawl</td></tr>
<tr><th scope="row">Ahrefs Free</th><td>Site Audit for verified websites</td>
<td>{FREE_CREDITS:,} crawl credits per verified project per month</td></tr>
<tr><th scope="row">Semrush free account</th><td>Try its tools within the stated report allowance</td>
<td>1 demo project and 10 reports per day; no per-audit page limit stated</td></tr>
<tr><th scope="row">Docket SEO checker, ours</th><td>A page score, its problems and the first fix</td>
<td>One page; no speed test or checks between pages</td></tr>
</tbody></table></div>
<p>New to audits? <a href="/learn/seo-audit/">What an SEO audit includes</a> gives you a checklist.
For a single access question, the <a href="/tools/robots-txt-tester/">robots.txt tester</a> shows
which rule allows or blocks a page.</p>

{checked("Google, Screaming Frog, Ahrefs and Semrush", ("URL Inspection", "https://support.google.com/webmasters/answer/9012289"), ("SEO Spider", "https://www.screamingfrog.co.uk/seo-spider/"), ("Ahrefs Free", FREE), ("Semrush free account", "https://www.semrush.com/prices/"))}

<h2>Google URL Inspection: a live access check</h2>
<p>Search Console's URL Inspection live test fetches and examines the URL in real time.
Google names its fetcher Google-InspectionTool. The test confirms whether that fetcher can
access the page for indexing. It does not confirm that the page will be indexed.</p>
<p>A rendered screenshot is available only in a live test. Use it when you need to inspect
what the test rendered. Keep the entered address and the result together so someone else
can repeat the check on the same page.</p>
{checked("Google", ("URL Inspection live-test guidance", "https://support.google.com/webmasters/answer/9012289"))}

<h2>Screaming Frog: a free desktop crawl up to 500 URLs</h2>
<p>SEO Spider is downloaded desktop software. Its free version allows up to 500 URLs in a
single crawl. If the pages you need fit that limit, try it before paying for a crawler.
If the crawl reaches the limit, do not treat the unread part of the site as checked.</p>
<p>A licence is {_SF_YEAR} a year in the USD view. That is a yearly charge. For more options, see
<a href="/best/screaming-frog-alternatives/">Screaming Frog alternatives for Mac and Windows</a>.</p>
{checked("Screaming Frog", ("Free crawl and USD licence", "https://www.screamingfrog.co.uk/seo-spider/"))}

<h2>Ahrefs Free: a monthly allowance for verified sites</h2>
<p>Ahrefs Free, formerly Webmaster Tools, includes Site Audit for verified websites.
It gives {FREE_CREDITS:,} crawl credits per verified project per month. The page says a credit
is used when an HTML page returns status code 200. Use this option if that allowance fits your
site and the repeat crawls you plan to run.</p>
{checked("Ahrefs", ("Ahrefs Free allowance", FREE))}

<h2>Semrush: read the free-account wording</h2>
<p>The free account lists 1 demo project and 10 reports per day across its vital tools.
The pricing and Site Audit pages read do not state a per-audit page limit. A report count
does not tell you how many URLs a crawl can cover. Confirm that allowance before relying on
it for a site review.</p>
{checked("Semrush", ("Free account", "https://www.semrush.com/prices/"), ("Site Audit", "https://www.semrush.com/features/site-audit/"))}

<h2>Docket's free SEO checker: one page, no sign-up</h2>

<p>We make this one, so read it with that in mind. Paste the address of any page into the
<a href="/tools/seo-checker/" data-ev="Free check" data-ev-button="best-free-checker-entry">free SEO checker</a>
and it returns a score out of 100, the problems on that page by area, and the worst one in full
with the change that fixes it. It runs in your browser with nothing to install, and it works on any
site, yours or a competitor's, so there is nothing to verify first.</p>

<p><strong>What it checks:</strong> whether Googlebot, Bingbot and the AI search crawlers may read
the page, noindex and canonical tags, redirects and HTTPS, the width of the title and description,
headings, structured data and sharing tags. <strong>What it does not:</strong> speed and anything between pages, because it reads one page at a time.</p>

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
<li><strong>A larger crawl.</strong> Compare the number of URLs you need with the free allowance.</li>
<li><strong>Checks between pages.</strong> A check of one page cannot settle a question about the whole site.</li>
<li><strong>A full fix plan.</strong> Check Engine's free result shows the top problem; the rest of its plan is paid.</li>
</ul>
<p>For titles that repeat across pages, see <a href="/how-to/fix-duplicate-title-tags/">how to fix duplicate title tags</a>.</p>

<p>If the paid tool you already have is Ahrefs, its crawler is <a href="/vs/ahrefs-site-audit-alternative/">Ahrefs Site Audit</a>; our comparison
sets out what it checks and how a crawl is paid for.</p>

<p>Docket's paid version is {PRICE_COMPACT} and adds the full ranked plan.
If the free tools already tell you what to fix, keep using them. For a paid crawler or platform,
<a href="/vs/se-ranking-vs-screaming-frog/">SE Ranking vs Screaming Frog</a> sets out the
different ways their audits are paid for.</p>

<p><a class="btn" href="/download/">Download Docket</a> ·
<a href="/vs/">see how it compares, tool by tool</a></p>

"""
    return render(
        cat="best", slug="free-seo-audit-tools",
        modified="2026-11-20",
        title="Free SEO audit: tools and limits",
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
            ("Which free crawler fits a small site?",
             "Screaming Frog allows up to 500 URLs per crawl. Ahrefs Free offers 5,000 crawl credits "
             f"per verified project per month. {source_link('SEO Spider', 'https://www.screamingfrog.co.uk/seo-spider/')} "
             f"and {source_link('Ahrefs Free', FREE)}. Checked 20 November 2026."),
            ("Does Semrush state a free per-audit page limit here?",
             "The pages read state 1 demo project and 10 reports per day, with no per-audit page limit. "
             f"{source_link('Semrush free account', 'https://www.semrush.com/prices/')}. Checked 20 November 2026."),
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
