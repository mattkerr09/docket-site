#!/usr/bin/env python3
"""Desktop SEO crawlers and audit apps that run on Windows, from vendor pages read on 22 November 2026.

Written for ChatGPT's E8 question, "best desktop SEO crawler app for Windows" (ops research/ai-visibility, 22 Nov 2026): it named
Screaming Frog, Sitebulb, Netpeak Spider and SEO PowerSuite WebSite Auditor, and cited roundups, not a page of ours.
Every figure is data in a single-quoted string (verify_numbers reads triple-quoted prose). Netpeak Spider and WebSite Auditor
come from the 20 November readings in best_compared_sources and keep that date. Readings: ~/ops/research/docket-competitors.md.
"""
from html import escape
from pathlib import Path

from best_compared_sources import CRAWLERS
from comparisons import source_link
from render import COMPETITORS, N_CHECKS, PRICE_COMPACT, REFUND_DAYS, buy_block, render

READ_NEW = '22 November 2026'
READ_EARLIER = '20 November 2026'
OWNERSHIP = ('We make Check Engine, one of the tools listed here. We describe every tool from its own pages, read on '
             + READ_NEW + ' (Netpeak Spider and SEO PowerSuite WebSite Auditor on ' + READ_EARLIER
             + '), and we earn money when you buy Check Engine.')

_EARLIER = {t.name: t for t in CRAWLERS}


def _from_earlier(name, runs):
    t = _EARLIER[name]
    return (name, runs, t.price, t.free, t.detail, t.sources, READ_EARLIER)


def _rows():
    sf = COMPETITORS['screaming-frog']
    rows = [
        ('Check Engine SEO', 'Windows (64-bit) and Mac', None,
         'A full audit with no key: the score, the problem count for each area and the main problem with its fix. The full plan and report exports need a licence.',
         'It has no custom extraction and no team accounts. Scheduled re-audits run only while the app is open and the computer is awake.',
         (('Check Engine pricing', '/pricing/'),), READ_NEW),
        ('Screaming Frog SEO Spider', 'Windows, macOS and Linux', f'${sf["annual_low"]} a year per user.',
         'Free to download with no sign up; crawls up to 500 URLs in one crawl. A licence removes that limit.',
         'The page says it identifies over 300 SEO issues. It is the reference crawler for raw crawl data.',
         (('SEO Spider', 'https://www.screamingfrog.co.uk/seo-spider/'),), READ_NEW),
        ('Sitebulb', 'Windows 10 or 11 and macOS Sonoma or later', 'Lite $18 a month with 10,000 URLs per audit; Pro $42 a month with 500,000 URLs per audit.',
         'No ongoing free plan; a 14-day free trial.',
         'The machine needs 4GB of free RAM, with 8GB recommended. Sitebulb is also sold as a cloud version, which is a different product from the Windows app.',
         (('Sitebulb pricing', 'https://sitebulb.com/subscriptions/pricing/index/'), ('System requirements', 'https://sitebulb.com/download/')), READ_NEW),
        _from_earlier('Netpeak Spider', 'Windows and macOS'),
        _from_earlier('SEO PowerSuite WebSite Auditor', 'Windows, Apple and Linux'),
        ('SiteAuditLint', 'Windows', 'Pro $99 one-time with unlimited URLs; Agency $159 one-time.',
         '100 URLs per crawl, basic checks and CSV export.',
         'A Windows app that runs locally. Pro adds an action plan ranked by impact and effort, audit history and comparison, and PDF reports.',
         (('SiteAuditLint', 'https://www.siteauditlint.com/'),), READ_NEW),
        ('SEO Site Auditor (AppKatz)', 'Windows 10 and 11', '$9.99 one-time, with unlimited scans and reports.',
         'A 14-day free trial, no card.',
         'The page names broken-link detection, page-level analysis and a client-ready report; it does not say how a scan is limited.',
         (('SEO Site Auditor', 'https://appkatz.com/seo-site-auditor-website-audit-tool'),), READ_NEW),
        ('BumbleCrawl', 'Windows and macOS', '$69 to $499 one-time by tier, on an Earlybird lifetime-deal page.',
         'Not stated on the page read.',
         'The terms are the deal page\'s, with a 30-day money-back guarantee. The vendor\'s own price page was not read, so confirm it before you buy.',
         (('Earlybird deal page', 'https://earlybird.so/products/bumblecrawl'),), READ_NEW),
    ]
    return sorted(rows, key=lambda r: r[0].casefold())


def _checked(name, sources, read):
    links = ', '.join(source_link(label, url) for label, url in sources)
    owner = name + ("'" if name.endswith("s") else "'s")
    return f'<p class="verified-note">Checked on {owner} own pages on {read}. Sources: {links}.</p>'


def _table(rows):
    body = []
    for name, runs, sold, free, _detail, sources, read in rows:
        price = sold if sold is not None else f'{PRICE_COMPACT}, one payment.'
        links = ', '.join(source_link(label, url) for label, url in sources)
        body.append(f'<tr data-tool="{escape(name)}"><th scope="row">{escape(name)}</th><td>{escape(runs)}</td><td>{escape(price)}</td>'
                    f'<td>{escape(free)}</td><td>{links}. Read {read}.</td></tr>')
    names = ', '.join(r[0] for r in rows)
    return ('<div class="wrap-tbl"><table class="cmp"><caption>Desktop SEO crawlers and audit apps for Windows</caption>\n'
            '<thead><tr><th scope="col">Tool</th><th scope="col">Where it runs</th><th scope="col">How it is sold</th>'
            '<th scope="col">Free version or trial</th><th scope="col">Dated sources</th></tr></thead>\n'
            f'<tbody>{"".join(body)}</tbody></table></div>\n'
            f'<p class="verified-note">Checked on {escape(names)} own pages, on the dates in the last column. Each row links the pages used.</p>')


#: Sold once, and described in full on /best/seo-audit-software-no-subscription/: repeating those paragraphs here made the two pages
#: share 31% of their text (lint's duplicate check), so this page keeps their table rows and links there.
_ONE_TIME_ELSEWHERE = ('SiteAuditLint', 'SEO Site Auditor (AppKatz)', 'BumbleCrawl')


def _sections(rows):
    return '\n'.join(f'<section data-rival="{escape(r[0])}"><h2>{escape(r[0])}</h2>\n<p>{escape(r[4])}</p>\n{_checked(r[0], r[5], r[6])}</section>'
                     for r in rows if r[0] not in _ONE_TIME_ELSEWHERE)


def build() -> Path:
    rows = _rows()
    body = f'''
<p class="ownership">{OWNERSHIP}</p>
<p id="measured-answer">Eight desktop SEO crawlers and audit apps run on Windows, from a free crawler to apps sold once or by the year.
Check Engine is one of them, at {PRICE_COMPACT}. The others are read from their own pages, so each row says how it is sold, what its free version or trial does and where it runs.</p>
{_checked('Check Engine', (('Check Engine pricing', '/pricing/'),), READ_NEW)}
<h2>What the table covers</h2>
<p>Each row gives the platforms an app supports, its price and how it is sold, and what its free version or trial allows. Sources are the vendors' own pages, dated in the last column.
These are stated facts from those pages; we ran none of the other seven apps, so the table says nothing about how many real problems each one finds on a site.</p>
<p>Rows are in alphabetical order and carry no ranking. Where a cell says a detail was not stated, the passage we read was silent on it.</p>
<h2>Eight Windows crawlers and audit apps</h2>
{_table(rows)}
{_sections(rows)}
<h2>Three apps sold once</h2>
<p>SiteAuditLint, SEO Site Auditor and BumbleCrawl are paid once rather than yearly. Their terms, refunds and what each page says about updates are set out on
<a href="/best/seo-audit-software-no-subscription/">SEO audit software with no monthly subscription</a>.</p>
<h2>Choosing for a Windows machine</h2>
<p>Start with what the free version lets you finish. A crawl cap that stops before the end of your site leaves pages unchecked, so write down the size of the site first.
Then check how the app is sold: a yearly licence or a monthly plan renews, while a one-time price does not, but says nothing about how long updates last.</p>
<p>If the same team also uses a Mac, look at the Where it runs column: several of these apps run on both. Sitebulb publishes a memory minimum and a recommendation in its system requirements;
read them before you start a large audit. For crawl-limit and price comparisons across Mac, Windows and cloud tools, see
<a href="/best/screaming-frog-alternatives/">Screaming Frog alternatives for Mac and Windows</a>, and for tools sold once,
<a href="/best/seo-audit-software-no-subscription/">SEO audit software with no monthly subscription</a>.</p>
<div class="callout" id="check-engine"><h2>Check Engine: Windows and Mac, sold once</h2>
<p>Check Engine runs {N_CHECKS} checks and orders repairs by impact and effort. It is {PRICE_COMPACT}, one payment and no subscription, with a {REFUND_DAYS}-day refund and no conditions.
The free version shows a score, every problem by name, worst first, and the main problem in full with its fix; the full plan and report exports need a licence.</p>
{buy_block('best-windows-crawlers', try_app='best-windows-crawlers-try-free', anchor=False)}</div>
'''
    return render(
        cat='best', slug='seo-crawler-for-windows',
        title='Best desktop SEO crawler for Windows, compared (2026)',
        h1='Best desktop SEO crawler for Windows, compared',
        desc="Eight desktop SEO crawlers and audit apps for Windows compared: where each runs, how it is sold and what its free version does, from vendor pages.",
        crumb='<a href="/best/">SEO tools compared</a> / Desktop SEO crawlers for Windows',
        body=body, published="2026-11-22", modified="2026-11-24",
        faq=[
            ('What is a free desktop SEO crawler for Windows?',
             'Screaming Frog, Netpeak Spider and SEO PowerSuite WebSite Auditor each state a free crawl of up to 500 URLs, and SiteAuditLint states 100 URLs per crawl. Check Engine\'s free audit needs no key and shows the score, every problem by name and the main problem in full with its fix.'),
            ('Which of these Windows crawlers are sold for a one-time price?',
             'SiteAuditLint, SEO Site Auditor, BumbleCrawl and Check Engine are sold once. Screaming Frog, Sitebulb, Netpeak Spider and SEO PowerSuite are yearly or monthly. Prices were read from each vendor\'s pages and can change.'),
            ('Which of these also run on a Mac?',
             'Check Engine, Screaming Frog, Sitebulb, Netpeak Spider, SEO PowerSuite WebSite Auditor and BumbleCrawl list a Mac or Apple build. SiteAuditLint and SEO Site Auditor are Windows apps.'),
        ])


def build_all() -> list[Path]:
    return [build()]
