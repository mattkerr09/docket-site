#!/usr/bin/env python3
"""WordPress listing comparison, without installation or test claims."""
from __future__ import annotations

from html import escape
from pathlib import Path

from learn_seo_audit_report import fact, note, quote, source
from render import render

# Each quote is from the plugin's own captured description, not a review.
REVIEWS = [
    ("all-in-one-seo-pack", "All in One SEO", "Get a full audit of every post and term",
     "The listing describes a site audit and a checklist of fixes. Its TruSEO description also covers on-page content and readability. That gives a WordPress editor a way to inspect the writing as well as the wider list of tasks.",
     "The captured audit passage is not marked PRO or paid. The source ends partway through its feature list, so it does not settle all free-plan limits."),
    ("seo-by-rank-math", "Rank Math", "Results are returned as a scored report.",
     "The SEO Analysis description says it sends the site URL, target keyword and language when you run a site analysis. It also says an account connection is required for API-based features. That is useful to know before choosing it for a site where outside services need approval.",
     "The SEO Analysis passage is not marked paid. Automatic link audits appear separately under Unique Features of Rank Math PRO. Keep that paid feature separate from the general analysis claim."),
    ("wp-seopress", "SEOPress", "Content analysis with unlimited target keywords",
     "The listing separates content analysis from its Site Audit. The audit description includes Search Console-backed recommendations, scan history and CSV export. It also lists a broken link checker. Read the section heading above those features before assuming they come with the free download.",
     "Site Audit and the broken link checker sit under SEOPress PRO. Content analysis appears in the free feature section. A free plugin listing does not make the PRO site audit free."),
    ("squirrly-seo", "Squirrly", "scores how ready each page is to be cited by AI",
     "Its GEO/AEO Audit description names a direct answer near the top, question-style headings, lists, tables, depth, freshness and schema. Elsewhere it names traffic, authority and backlink audits. Those are different questions from a scan that only looks for broken URLs.",
     "The captured GEO/AEO audit passage is not marked PRO or paid. The text read does not give enough detail to promise unrestricted free use."),
    ("smartcrawl-seo", "SmartCrawl", "scans pages and posts for readability and keyword density",
     "The page analyzer describes checks on writing and keyword use, with suggestions for improving content. Its SEO Checkup and Reports description promises recommendations for improving SEO. These are listing claims; we did not run either feature on a WordPress site.",
     "The listing calls scheduled SEO audits and URL crawls exclusive Pro features. Its general Checkup and page-analyzer descriptions are not individually marked paid in the text read."),
    ("xagio-seo", "Xagio", "Instantly discover which keywords your pages rank for.",
     "The listing calls this Automatic Site Audit and narrows it to ranking keywords per page. That wording matters. If your task is checking response errors or indexing rules, the quoted audit description does not establish that it does that job.",
     "The Automatic Site Audit passage is not marked PRO or paid. The listing mentions credits for website builds, which does not establish a charge for this audit feature."),
    ("broken-link-checker", "Broken Link Checker", "broken links, missing images, and redirects",
     "This listing describes a focused check of links and related problems. It offers a local engine and a cloud-based engine. The local description includes internal and external links in posts, pages and comments. Choose it for that stated job rather than treating a link scan as a complete SEO review.",
     "The captured link-checking passages are not marked PRO or paid. This comparison does not establish any cloud service allowance beyond the wording we read."),
]


def build() -> Path:
    plugins = {p['slug']: p for p in source('plugins-trimmed.json')['plugins']}
    sections = []
    for slug, name, excerpt, checks, paid in REVIEWS:
        p = plugins[slug]
        ptr = f'/plugins/{list(plugins).index(slug)}'
        sections.append(f"""
<section id="{slug}" data-plugin="{slug}">
<h2>{escape(name)}</h2>
<p>The listing says {quote(excerpt, 'plugins-trimmed.json')}.</p>
<p>{checks}</p><p><strong>Free or paid wording:</strong> {paid}</p>
<table data-table="plugin"><caption>{escape(name)} listing facts</caption><tbody>
<tr><th>Active installs</th><td>{fact('Active installs', p['active_installs'], 'plugins-trimmed.json', ptr + '/active_installs')}</td></tr>
<tr><th>Rating on the listing API scale</th><td>{fact('Rating', p['rating'], 'plugins-trimmed.json', ptr + '/rating')}</td></tr>
<tr><th>Last updated</th><td>{fact('Last updated', p['last_updated'], 'plugins-trimmed.json', ptr + '/last_updated')}</td></tr>
</tbody></table>
<p><a href="{escape(p['listing_url'])}">Read {escape(name)} on WordPress.org</a>.</p>
</section>""")
    body = f"""
<p class="lede">A free SEO audit plugin for WordPress can mean a content check, a link checker or a site audit with paid extras. Start with the problem you need it to find. Then read where the listing puts that feature.</p>
<p>We read the plugins' own WordPress.org descriptions and compared their audit claims below. We did not install or test these plugins. Some listings describe free and paid features together, so a free download is not enough evidence that its site audit is free.</p>

<h2>How to read this comparison</h2>
<p>The short quotations describe what the plugin maker says it checks. Active installs, rating and update time come from the same saved listing response. We show the rating in the API's own form, without converting it to stars or treating it as a test result. These facts describe the listing when it was read; they do not measure audit accuracy.</p>
{note('plugin_read')}
<p>There is no overall winner here. A writer checking readability, an owner finding broken links and an agency planning site repairs need different evidence. Use the paid-feature note beside each plugin to decide what to check next on its listing. Where the captured text does not settle access, we leave that question open.</p>
{''.join(sections)}

<h2>Yoast SEO and Slim SEO</h2>
<p>The Yoast SEO and Slim SEO listings make no site-audit claim in the text we read.</p>

<h2>When you cannot install a WordPress plugin</h2>
<p>A plugin gives you a place to start an audit from inside WordPress. The listing may still describe work sent to a cloud service, as the link checker and Rank Math passages show. Do not assume that starting from the dashboard means all processing stays on your server.</p>
<p>Check Engine is not a WordPress plugin. It audits a site from your Mac or PC, whether the site uses WordPress or not. That makes it an option for a client site or a site where you cannot install plugins. You can review the public pages without asking the owner to add an SEO plugin for your visit.</p>
<p>That choice also changes where you work. If your task is editing a post while you write, an editor's content analysis can sit close to the words you are changing. If your task is handing a client a list of public-page problems, an outside crawl can keep the review separate from their WordPress setup. Decide which task you have before comparing long feature lists.</p>

<h2>Before choosing a free audit feature</h2>
<p>Write down the question you want answered, such as which links need attention or which pages need clearer text. Find the passage that describes that check. Then look for a PRO heading, an account requirement or a service limit around it. Ask the maker if the captured description leaves access unclear.</p>
<p>Keep the wording with your decision. A listing's use of audit does not tell you that every check you want is included. The narrow description of Xagio's ranking-keyword audit is a useful example: the name is broad, but the promised task is specific. Paying attention to that difference can save you from choosing a tool for a job it never claimed to do.</p>

<h2>Source note</h2>
<p>Our comparison uses the saved plugins-trimmed.json response from the WordPress.org plugin information service. We kept the descriptions with their surrounding free and PRO headings. The quotes above are short extracts from those descriptions, not our test results or customer reviews.</p>
{note('local_read')}
"""
    return render(
        cat="best", slug="free-seo-audit-plugins-wordpress",
        title="Free SEO audit plugin for WordPress: listing claims",
        desc="Compare WordPress plugins by their own audit claims, active installs, ratings and update dates. See which audit features the listings mark as paid.",
        h1="Free SEO audit plugin choices for WordPress",
        crumb='<a href="/best/">Best tools</a> / WordPress audit plugins',
        body=body, published="2026-11-11",
        faq=[
            ("What should I ask before adding an audit plugin to a client site?",
             "Ask who can approve the install and whether a staging copy is available. Agree on the report you need before changing the client's WordPress setup."),
            ("Does a listing rating tell me which plugin finds more SEO problems?",
             "It does not answer that comparison. To judge coverage for your work, ask for an example result that shows the specific problem you need to find."),
            ("Should the audit plugin replace my current WordPress SEO setup?",
             "Do not make that decision from this list alone. Check the maker's migration guidance and review what your current setup controls before replacing it."),
        ],
    )


def build_all() -> list[Path]:
    return [build()]
