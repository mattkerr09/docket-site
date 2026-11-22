#!/usr/bin/env python3
"""The comparison directory and the free audit allowances guide."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from best_compared_layout import disclosure, method
from comparisons import source_link
from real_questions_sources import READINGS
from ahrefs_first_screen import FREE, FREE_CREDITS, checked  # noqa: E402
from render import CHROME_ADDON, DATA, FREE_LINE, PRICE_COMPACT, buy_block, render  # noqa: E402

_RUN = json.loads((DATA / "free-run.json").read_text())
_SF_YEAR = re.search(r"\$\d+", READINGS["rq-screaming-frog"][1][0]).group()


#: 22 Nov 2026 (AI visibility, CEO go, fix 3): ChatGPT's E6 and E10 ("free website SEO audit tool", "how to check my website for
#: technical SEO issues for free") named Seobility, SEOptimer and PageSpeed Insights beside Screaming Frog, Ahrefs and Search Console,
#: and this page covered only the last three. Every figure is single-quoted data with its own reading date (verify_numbers reads
#: triple-quoted prose). Readings: ~/ops/research/docket-competitors.md, 22 Nov 2026 entry on the free-tool checks.
_MORE_FREE = (
    ('Seobility SEO Checker', 'Analyses any single web page for free, with no account named on the page read.',
     'A full-site audit is a Premium feature: a free 14-day trial, then $69 a month.',
     (('SEO Checker', 'https://www.seobility.net/en/seocheck/'),), '22 November 2026'),
    ('SEOptimer', 'No ongoing free plan is listed on its pricing page; each plan offers a 7-day free trial.',
     'Plans are $29, $39 and $59 a month. Its site refuses automated readers, so the plans were read by hand on 9 November 2026 and our reader was refused again on 22 November.',
     (('SEOptimer pricing', 'https://www.seoptimer.com/pricing'),), '9 November 2026'),
    ('PageSpeed Insights', 'Free: one URL goes in a single field and a speed report comes back.',
     'It is a performance check for one page at a time, not an audit of every page on a site.',
     (('PageSpeed Insights', 'https://pagespeed.web.dev/'),), '22 November 2026'),
)


def _more_free_tools() -> str:
    rows = ''.join(
        f'<tr data-tool="{name}"><th scope="row">{name}</th><td>{free}</td><td>{beyond}</td>'
        f'<td>{", ".join(source_link(label, url) for label, url in sources)}. Read {read}.</td></tr>'
        for name, free, beyond, sources, read in _MORE_FREE)
    return (
        '<h2>Three more free checks, and what each leaves out</h2>\n'
        '<p>Searchers also ask about three tools that are not in the sections above. Two give you a free result for one page; one has no free plan. '
        'None of them is a free crawl of a whole site, which is what the sections above compare.</p>\n'
        '<div class="wrap-tbl"><table class="cmp"><caption>Seobility, SEOptimer and PageSpeed Insights: free use and its limit</caption>\n'
        '<thead><tr><th scope="col">Tool</th><th scope="col">Free use</th><th scope="col">Beyond free</th><th scope="col">Dated source</th></tr></thead>\n'
        f'<tbody>{rows}</tbody></table></div>\n'
        '<p class="verified-note">Checked on Seobility\'s, SEOptimer\'s and Google\'s own pages: Seobility and PageSpeed Insights on 22 November 2026, '
        'SEOptimer on 9 November 2026 (read by hand). Each row links the page used.</p>\n'
        '<p>Check Engine\'s free app is a different kind of free: a full audit of your site with no key, showing the score, the problem count for each area '
        'and the main problem with its fix. The full plan and the report exports need a licence.</p>')


#: A searcher who lands here from "search engine checker" (Search Console, 28 days to 21 Nov 2026: 71 impressions at 41.1; Bing's top
#: three are all paste-a-URL tools) wants a tool, not a list of tools. One line right after the lede sends them to ours. Internal
#: link, no nofollow; everything it says (a score out of 100, the first fix, no sign-up) is already on this page.
CHECKER_POINTER = ('<p>Want to check one page right now? Paste it into the <a href="/tools/seo-checker/">free SEO checker</a>: '
                   'a score out of 100 and the first fix, with no sign-up.</p>')


def free_seo_audit_tools() -> Path:
    body = f"""
{disclosure()}
<p id="measured-answer">A free SEO audit can find problems, but its crawl limit or locked report can leave work unseen.
Check Engine's <a href="/vs/screaming-frog-alternative/">recorded free audit</a> read {_RUN["pages"]} pages and found {_RUN["problems"]} problems; the free download shows the score, counts and main fix, while the full plan is paid.
{source_link("Screaming Frog", "https://www.screamingfrog.co.uk/seo-spider/")} allows up to 500 URLs per free crawl, and {source_link("Ahrefs Free", FREE)} gives {FREE_CREDITS:,} crawl credits per verified project per month.
{source_link("Semrush's free account", "https://www.semrush.com/prices/")} lists 1 demo project and 10 reports per day; the pages read do not state a per-audit page limit.</p>
{checked("Screaming Frog, Ahrefs and Semrush", ("SEO Spider", "https://www.screamingfrog.co.uk/seo-spider/"), ("Ahrefs Free", FREE), ("Semrush free account", "https://www.semrush.com/prices/"))}
{CHECKER_POINTER}

{method('the check each tool describes', 'For a paid upgrade we use Screaming Frog at $279 a year, then Ahrefs Lite at $1,290 a year, then Semrush SEO at $117.33 a month billed annually. The monthly figure multiplied by twelve gives $1,407.96. Google states no price in the pages read, so it follows the priced entries.')}
{checked("Screaming Frog, Ahrefs and Semrush", ("SEO Spider", "https://www.screamingfrog.co.uk/seo-spider/"), ("Ahrefs plans", "https://ahrefs.com/pricing"), ("Semrush plans", "https://www.semrush.com/prices/"))}
<h2>Free audit allowances and a live access check</h2>
<div class="wrap-tbl"><table class="cmp">
<caption>Free website audit tools and their limits</caption>
<thead><tr><th scope="col">Tool</th><th scope="col">Use it for</th><th scope="col">Free limit</th></tr></thead>
<tbody>
<tr><th scope="row">Screaming Frog</th><td>A free desktop crawl</td>
<td>Up to 500 URLs per crawl</td></tr>
<tr><th scope="row">Ahrefs Free</th><td>Site Audit for verified websites</td>
<td>{FREE_CREDITS:,} crawl credits per verified project per month</td></tr>
<tr><th scope="row">Semrush free account</th><td>Try its tools within the stated report allowance</td>
<td>1 demo project and 10 reports per day; no per-audit page limit stated</td></tr>
<tr><th scope="row">Google URL Inspection live test</th><td>Check whether Google's inspection fetcher can access a page for indexing</td>
<td>A live test of the entered URL; no price stated on the page read</td></tr>
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

<div class="callout" id="check-engine"><h2>Check Engine's free SEO checker: one page, no sign-up</h2>

<p>We make this one, so read it with that in mind. Paste the address of any page into the
<a href="/tools/seo-checker/" data-ev="Free check" data-ev-button="best-free-checker-entry">free SEO checker</a>
and it returns a score out of 100, the problems on that page by area, and the worst one in full
with the change that fixes it. It runs in your browser with nothing to install, and it works on any
site, yours or a competitor's, so there is nothing to verify first.</p>

<p><strong>What it checks:</strong> whether Googlebot, Bingbot and the AI search crawlers may read
the page, noindex and canonical tags, redirects and HTTPS, the width of the title and description,
headings, structured data and sharing tags. <strong>What it does not:</strong> speed and anything between pages, because it reads one page at a time.</p>

{_more_free_tools()}
<h2>Is there a free SEO audit plugin?</h2>
<p>For Chrome, our free <a href="{CHROME_ADDON}" rel="noopener" data-ev="Install"
data-ev-button="best-free-addon">Docket SEO add-on</a> checks the page in the tab you are on,
in your browser, with nothing uploaded and no account. It is a page check, not a whole-site crawl.</p>

<h2>What does a free SEO audit report show?</h2>
<p>The recorded free audit above was run on our own company site on 9 November 2026.</p>
<p>The online checker shows a page score, problems by area and the main problem with its fix.
It does not audit the whole website. For a site audit, Docket's download runs on your computer.
{FREE_LINE} The free result is a starting point, not the full paid report.</p>

<p>Docket's paid version is {PRICE_COMPACT} and adds the full ranked plan.
If the free tools already tell you what to fix, keep using them. For a paid crawler or platform,
<a href="/vs/se-ranking-vs-screaming-frog/">SE Ranking vs Screaming Frog</a> sets out the
different ways their audits are paid for.</p>

{buy_block('best-free-compared', anchor=False)}
</div>
<h2>When does a free limit leave work undone?</h2>

<p>When the free version you use has stopped answering your question:</p>

<ul>
<li><strong>A larger crawl.</strong> Compare the number of URLs you need with the free allowance.</li>
<li><strong>Checks between pages.</strong> A check of one page cannot settle a question about the whole site.</li>
<li><strong>A full fix plan.</strong> Check whether your free result includes the repair details you need.</li>
</ul>
<p>For titles that repeat across pages, see <a href="/how-to/fix-duplicate-title-tags/">how to fix duplicate title tags</a>.</p>

<p>If the paid tool you already have is Ahrefs, its crawler is <a href="/vs/ahrefs-site-audit-alternative/">Ahrefs Site Audit</a>; our comparison
sets out what it checks and how a crawl is paid for.</p>

"""
    page = render(
        cat="best", slug="free-seo-audit-tools",
        modified="2026-11-22",
        title="Free SEO audit: tools and limits",
        desc=("Run a free SEO audit of a page or small site. Compare website audit tools, "
              "free limits, a Chrome plugin and what the free report shows."),
        h1="Free SEO audit tools and their limits",
        crumb='<a href="/best/">SEO tools compared</a> / free SEO audit tools',
        body=body,
        faq=[
            ("Is there a free SEO audit plugin?",
             "Yes. Our free Docket SEO add-on for Chrome checks the page in the tab you are on, "
             "in your browser, with nothing uploaded and no account. It checks one page, not the whole site."),
            ("What does a free SEO audit report include?",
             "Docket's free online checker shows a page score, problems by area and the main "
             "problem with its fix. The free desktop download gives a site score, counts by "
             "category and the main problem in full. The rest of the problems and ranked plan are paid."),
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
    # Keep render's existing Free Offer detection, then change only this visible
    # sentence. The shared helper and all schema bytes keep their prior form.
    raw = page.read_text(encoding="utf-8")
    raw = raw.replace(FREE_LINE + ' The free result',
                      FREE_LINE.replace('top problem', 'main problem') + ' The free result', 1)
    page.write_text(raw, encoding="utf-8")
    return page


def best_hub() -> Path:
    body = f"""
{disclosure()}
<p id="measured-answer">Compare SEO tools by the work in front of you: a free crawl, a WordPress check or a report for a client.
{source_link('Screaming Frog', 'https://www.screamingfrog.co.uk/seo-spider/')} allows 500 URLs per free crawl.
Use the guides below to compare stated limits and costs before choosing what to try on your site.</p>
{checked('Screaming Frog', ('Free crawl allowance', 'https://www.screamingfrog.co.uk/seo-spider/'))}
{method('the task each guide covers', 'The order applies to tool tables in each guide. This directory groups the guides by the work they answer; it gives no product a rank.')}
<h2>Start with the free allowance</h2>
<p>A small crawl may fit an ongoing free version. A trial ends, while a free tier can still have a cap.
The free-tools guide separates those limits from a single-page access check.
<a href="/best/free-seo-audit-tools/">Free SEO audit: tools and limits</a>.</p>
<h2>Check a WordPress site</h2>
<p>A post's content analysis and a site-wide audit are different tasks. Read the paid-feature boundary before adding a plugin.
The guide also labels outside checks for sites where you cannot install one.
<a href="/best/free-seo-audit-plugins-wordpress/">WordPress SEO audit plugins compared</a>.</p>
<h2>Choose where a crawl runs</h2>
<p>A desktop crawl uses your computer. A cloud service changes where you work and how you pay.
A monitor checks for changes over time. Keep those tasks separate when you compare allowances.
<a href="/best/screaming-frog-alternatives/">Screaming Frog alternatives compared</a>.</p>
<h2>Pay once, not monthly</h2>
<p>Some audit software is sold for a one-time price instead of a subscription. The guide compares six, for Mac, Windows and the browser,
and says what each page states about the free version and the refund.
<a href="/best/seo-audit-software-no-subscription/">SEO audit software with no monthly subscription</a>.</p>
<h2>Prepare a report for a client</h2>
<p>Write down whether you need a PDF, a web report or a client login. A branding add-on may be charged separately from the audit plan.
The guide marks reporting platforms and planned features so you can ask for the right sample.
<a href="/best/white-label-seo-audit-tools/">White-label SEO audit tools compared</a>.</p>
<h2>What the source can establish</h2>
<p>A vendor's page can establish its stated price, limit and feature wording on the read date.
It cannot establish that its audit finds more real faults on your site than another tool.
A missing feature claim is left unknown rather than treated as proof that the tool cannot do it.</p>
<p>We have no measured dataset that ranks these tools. For a trial, use pages you know, keep the settings and check the findings against the page.
If the audit stops at a cap, keep that limit with the result. A partial crawl should not be presented as a whole-site review.</p>
<div class="callout" id="check-engine"><h2>Check Engine is the tool we sell</h2>
<p>Check Engine is our desktop audit app. The free result shows a score, counts and the main problem with its fix.
The full plan and report exports are paid. It has no backlink index, rank tracking or shared team workspace.</p>
<p>Its scheduled re-audits run only while the app is open and the computer is awake.
Read the product box in a guide for the current price and the limits relevant to that task.
<a href="/pricing/">Check Engine pricing</a>.</p></div>
"""
    return render(
        cat="best", slug="",
        title="SEO tools compared, by the job you are doing",
        desc="Compare SEO tools by task, free limits, yearly costs and stated features. Read the published method and dated vendor sources.",
        h1="SEO tools compared, by the job you are doing",
        crumb='<a href="/">Check Engine</a> / SEO tools compared',
        body=body, modified="2026-11-22", schema_type="CollectionPage",
        faq=[
            ("How do I choose which SEO comparison guide to read?",
             "Start with the result you need: a crawl, a WordPress check or a client report. Write down the number of pages and the output you must hand over."),
            ("Why do these guides leave some prices unknown?",
             "A quote-only plan or an unclear billing period cannot support a checked yearly total. Ask the maker for a dated quote with its limits."),
            ("Can a feature list show how well an audit will work on my site?",
             "It describes what the maker says the tool does. Try a known set of pages and verify the findings before relying on a full report."),
        ],
    )


if __name__ == "__main__":
    print(free_seo_audit_tools())
