#!/usr/bin/env python3
"""WordPress listing comparison, without installation or test claims."""
from __future__ import annotations

from datetime import datetime
from html import escape
from pathlib import Path

from learn_seo_audit_report import fact, note, quote, source
from render import render

# Each quote is from the plugin's own captured description, not a review.
REVIEWS = [
    ("wordpress-seo", "Yoast SEO", "SEO analysis to guide your keyword targeting",
     f"The listing also says {quote('Readability analysis for clear, engaging, user-friendly writing', 'plugins-trimmed.json')}. This analysis is per post or page while you write, not a crawl of the whole site.",
     f"The content analysis section does not mark basic SEO or readability analysis as paid. It does specify {quote('up to 5 keyphrases in Premium', 'plugins-trimmed.json')}. The listing also says its AI tools come with Yoast SEO Premium."),
    ("all-in-one-seo-pack", "All in One SEO", "Get a full audit of every post and term",
     "The listing describes a site audit and a checklist of fixes. Its TruSEO description also covers on-page content and readability. That gives a WordPress editor a way to inspect the writing as well as the wider list of tasks.",
     "The audit description has no PRO or paid label. Its feature list is cut short, so ask the maker which audit features are free."),
    ("seo-by-rank-math", "Rank Math", "Results are returned as a scored report.",
     "The SEO Analysis description says it sends the site URL, target keyword and language when you run a site analysis. It also says an account connection is required for API-based features. That is useful to know before choosing it for a site where outside services need approval.",
     "The SEO Analysis passage is not marked paid. Automatic link audits appear separately under Unique Features of Rank Math PRO. Keep that paid feature separate from the general analysis claim."),
    ("wp-seopress", "SEOPress", "Content analysis with unlimited target keywords",
     "The listing separates content analysis from its Site Audit. The audit description includes Search Console-backed recommendations, scan history and CSV export. It also lists a broken link checker. Read the section heading above those features before assuming they come with the free download.",
     "Site Audit and the broken link checker sit under SEOPress PRO. Content analysis appears in the free feature section."),
    ("squirrly-seo", "Squirrly", "scores how ready each page is to be cited by AI",
     "Its GEO/AEO Audit description names a direct answer near the top, question-style headings, lists, tables, depth, freshness and schema. Elsewhere it names traffic, authority and backlink audits. Those are different questions from a scan that only looks for broken URLs.",
     "The GEO/AEO audit description has no PRO or paid label and gives no free-use allowance."),
    ("smartcrawl-seo", "SmartCrawl", "scans pages and posts for readability and keyword density",
     "The page analyzer describes checks on writing and keyword use, with suggestions for improving content. Its SEO Checkup and Reports description offers recommendations for improving SEO.",
     "The listing calls scheduled SEO audits and URL crawls exclusive Pro features. Its general Checkup and page-analyzer descriptions have no paid label."),
    ("xagio-seo", "Xagio", "Instantly discover which keywords your pages rank for.",
     "The listing calls this Automatic Site Audit and describes ranking keywords per page. Ask the maker about response errors or indexing checks if those are what you need.",
     "The Automatic Site Audit description has no PRO or paid label. The credits mentioned cover website builds, with no audit charge stated."),
    ("broken-link-checker", "Broken Link Checker", "broken links, missing images, and redirects",
     "This listing describes a focused check of links and related problems. It offers a local engine and a cloud-based engine. The local description includes internal and external links in posts, pages and comments. Choose it for that stated job rather than treating a link scan as a complete SEO review.",
     "The link-checking descriptions have no PRO or paid label. Ask the maker about the cloud service allowance."),
]


def build() -> Path:
    plugins = {p['slug']: p for p in source('plugins-trimmed.json')['plugins']}
    sections = []
    for slug, name, excerpt, checks, paid in REVIEWS:
        p = plugins[slug]
        ptr = f'/plugins/{list(plugins).index(slug)}'
        installs = p['active_installs']
        installs = f'{installs // 1_000_000}+ million' if installs >= 1_000_000 else f'{installs:,}+'
        rating = f"{p['rating'] / 20:.1f} out of 5"
        updated = datetime.strptime(p['last_updated'].split()[0], '%Y-%m-%d')
        updated = f'{updated.day} {updated:%B %Y}'
        sections.append(f"""
<section id="{slug}" data-plugin="{slug}">
<h2>{escape(name)}</h2>
<p>The listing says {quote(excerpt, 'plugins-trimmed.json')}.</p>
<p>{checks}</p><p><strong>Free or paid wording:</strong> {paid}</p>
<p class="plugin-facts">
{fact('Active installs', installs, 'plugins-trimmed.json', ptr + '/active_installs')}<br>
{fact('Rating', rating, 'plugins-trimmed.json', ptr + '/rating')}<br>
{fact('Last updated', updated, 'plugins-trimmed.json', ptr + '/last_updated')}
</p>
<p><a href="{escape(p['listing_url'])}">Read {escape(name)} on WordPress.org</a>.</p>
</section>""")
    body = f"""
<p class="lede">A free SEO audit plugin for WordPress can mean a content check, a link checker or a site audit with paid extras. Start with the problem you need it to find. Then read where the listing puts that feature.</p>
<p>We compared the plugins' own WordPress.org descriptions below. Some listings describe free and paid features together. Check the paid-feature note beside each plugin before choosing an audit.</p>

<h2>How to read this comparison</h2>
<p>The short quotations describe what the plugin maker says it checks. Active installs, ratings and update dates come from WordPress.org. These listing facts tell you about use and upkeep. To judge audit accuracy, you need to try the checks on a site you know.</p>
<p>A writer checking readability, an owner finding broken links and an agency planning site repairs need different checks. Start with the plugin whose stated job fits yours.</p>
{''.join(sections)}

<h2>Slim SEO</h2>
<p data-plugin="slim-seo">Slim SEO's listing says its meta tags are generated {quote('for the best SEO scores', 'plugins-trimmed.json')} but describes no checker or audit.</p>

<h2>When you cannot install a WordPress plugin</h2>
<p>A plugin gives you a place to start an audit from inside WordPress. The listing may still describe work sent to a cloud service, as the link checker and Rank Math passages show. Do not assume that starting from the dashboard means all processing stays on your server.</p>
<p>Check Engine is not a WordPress plugin. It audits a site from your Mac or PC, whether the site uses WordPress or not. That makes it an option for a client site or a site where you cannot install plugins. You can review the public pages without asking the owner to add an SEO plugin for your visit.</p>
<p>That choice also changes where you work. If your task is editing a post while you write, an editor's content analysis can sit close to the words you are changing. If your task is handing a client a list of public-page problems, an outside crawl can keep the review separate from their WordPress setup. Decide which task you have before comparing long feature lists.</p>

<h2>Before choosing a free audit feature</h2>
<p>Write down the question you want answered, such as which links need attention or which pages need clearer text. Find the passage that describes that check. Then look for a PRO heading, an account requirement or a service limit around it.</p>
<p>Keep the wording with your decision. A listing's use of audit does not tell you that every check you want is included. The narrow description of Xagio's ranking-keyword audit is a useful example: the name is broad, but the promised task is specific. Paying attention to that difference can save you from choosing a tool for a job it never claimed to do.</p>

<h2>Source note</h2>
{note('plugin_read')}
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
