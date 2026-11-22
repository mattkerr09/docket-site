#!/usr/bin/env python3
"""SEO audit software sold for a one-time price, from vendor pages read live on 22 November 2026.

Written for ChatGPT's E9 question, "SEO audit software without a monthly subscription" (ops research/ai-visibility,
22 Nov 2026): it named four small one-time tools from vendor pages and no page of ours. Every figure below is data in a
single-quoted string, dated by READ_ONE_TIME, so verify_numbers (which reads triple-quoted prose) sees only derived holes.
Readings are in ~/ops/research/docket-competitors.md (22 Nov 2026 entry on the five one-time tools).
"""
from html import escape
from pathlib import Path

from comparisons import source_link
from render import COMPETITORS, N_CHECKS, N_LANES, PRICE_COMPACT, REFUND_DAYS, buy_block, rival_monthly_range, render

READ_ONE_TIME = '22 November 2026'
OWNERSHIP = ('We make Check Engine, one of the tools listed here. We describe every tool from its own pages, read on '
             + READ_ONE_TIME + ', and we earn money when you buy Check Engine.')

#: name, where it runs, how it is sold, free version, refund, detail, sources. Alphabetical on purpose: no ranking.
TOOLS = (
    ('Check Engine SEO', 'Mac (Apple silicon or Intel) and Windows', None,
     'A full audit with no key: the score, the problem count for each area and the main problem with its fix. The full plan and report exports need a licence.',
     None,
     'It has no custom extraction and no team accounts. Scheduled re-audits run only while the app is open and the computer is awake.',
     (('Check Engine pricing', '/pricing/'),)),
    ('BumbleCrawl', 'Windows and macOS', '$69 to $499 one-time by tier, on an Earlybird lifetime-deal page.',
     'Not stated on the page read.', '30-day money-back guarantee, from the deal terms.',
     'The terms here are the deal page\'s: lifetime access and all future updates, 200+ SEO and accessibility checks. The vendor\'s own price page was not read, so confirm it before you buy.',
     (('Earlybird deal page', 'https://earlybird.so/products/bumblecrawl'),)),
    ('Scrutiny', 'macOS only', '$149 one-off licence, per user.',
     'Free use with exporting disabled.', 'Not stated on the page read.',
     'A native Mac crawler. The page says a licence from version 7 upgrades to version 12 with no upgrade fee. The page also offers bulk and educational discounts.',
     (('Scrutiny for Mac', 'https://peacockmedia.software/mac/scrutiny/'),)),
    ('SEO Site Auditor (AppKatz)', 'Windows 10 and 11', '$9.99 one-time, with unlimited scans and reports.',
     'A 14-day free trial, no card.', 'Not stated on the page read.',
     'The lowest sticker price here, for a Windows desktop app. The page names broken-link detection, page-level analysis and a client-ready report; it does not say how a scan is limited.',
     (('SEO Site Auditor', 'https://appkatz.com/seo-site-auditor-website-audit-tool'),)),
    ('SEOPilot', 'In the browser, with a WordPress plugin', 'Basic $27 one-time for 1 website; Pro $37 one-time for up to 5 websites.',
     'A free audit with no signup.', '30-day money-back guarantee.',
     'It is a web service used in a browser, not a desktop app, and it has a WordPress plugin. Higher agency plans are also one-time and show struck-through earlier prices, so a plan price here can change.',
     (('SEOPilot pricing', 'https://seopilot.online/'),)),
    ('SiteAuditLint', 'Windows', 'Pro $99 one-time with unlimited URLs; Agency $159 one-time.',
     '100 URLs per crawl, basic checks and CSV export.', 'Not stated on the page read.',
     'A Windows desktop app that runs locally. Pro adds an action plan ranked by impact and effort, audit history and comparison, and PDF reports. The page says there is no subscription and no licence key.',
     (('SiteAuditLint', 'https://www.siteauditlint.com/'),)),
)


def _day(iso):
    import datetime as _dt
    d = _dt.date.fromisoformat(iso)
    return f"{d.day} {d:%B %Y}"


def _checked(name, sources):
    links = ', '.join(source_link(label, url) for label, url in sources)
    owner = name + ("'" if name.endswith("s") else "'s")
    return f'<p class="verified-note">Checked on {owner} own pages on {READ_ONE_TIME}. Sources: {links}.</p>'


def _table():
    rows = []
    for name, runs, sold, free, refund, _detail, sources in sorted(TOOLS, key=lambda t: t[0].casefold()):
        price = sold if sold is not None else f'{PRICE_COMPACT}, one payment.'
        refund_text = refund if refund is not None else f'{REFUND_DAYS} days, no conditions.'
        links = ', '.join(source_link(label, url) for label, url in sources)
        rows.append(f'<tr data-tool="{escape(name)}"><th scope="row">{escape(name)}</th><td>{escape(runs)}</td>'
                    f'<td>{escape(price)}</td><td>{escape(free)}</td><td>{escape(refund_text)}</td>'
                    f'<td>{links}. Read {READ_ONE_TIME}.</td></tr>')
    names = ', '.join(t[0] for t in sorted(TOOLS, key=lambda t: t[0].casefold()))
    return ('<div class="wrap-tbl"><table class="cmp"><caption>SEO audit software sold for a one-time price</caption>\n'
            '<thead><tr><th scope="col">Tool</th><th scope="col">Where it runs</th><th scope="col">How it is sold</th>'
            '<th scope="col">Free version</th><th scope="col">Refund</th><th scope="col">Dated sources</th></tr></thead>\n'
            f'<tbody>{"".join(rows)}</tbody></table></div>\n'
            f'<p class="verified-note">Checked on {escape(names)} own pages on {READ_ONE_TIME}. Each row links the pages used.</p>')


def _sections():
    parts = []
    for name, runs, sold, free, refund, detail, sources in sorted(TOOLS, key=lambda t: t[0].casefold()):
        parts.append(f'<section data-rival="{escape(name)}"><h2>{escape(name)}</h2>\n<p>{escape(detail)}</p>\n'
                     f'{_checked(name, sources)}</section>')
    return '\n'.join(parts)


def build() -> Path:
    sf = COMPETITORS['screaming-frog']
    ah = COMPETITORS['ahrefs-site-audit']
    lo, hi = rival_monthly_range('ahrefs-site-audit')
    sf_day, ah_day = _day(sf['price_checked']), _day(ah['price_checked'])
    body = f'''
<p class="ownership">{OWNERSHIP}</p>
<p id="measured-answer">SEO audit software with no monthly subscription exists for Windows, for Mac and in the browser.
Six are compared here, each sold once: Check Engine at {PRICE_COMPACT}, and five others read from their own pages.
Three run on a Mac: Check Engine, Scrutiny and BumbleCrawl. Four run on Windows: Check Engine, BumbleCrawl, SEO Site Auditor and SiteAuditLint. One runs in the browser: SEOPilot.</p>
{_checked('Check Engine', (('Check Engine pricing', '/pricing/'),))}
<h2>How this comparison works</h2>
<p>We compare how each tool is sold, where it runs, what the free version does, and the refund where a page states one.
The sources are each vendor's own pages, read on {READ_ONE_TIME}. This is a comparison of stated facts, not a test score:
we did not run the other five, and a one-time price does not tell you how many problems a tool finds on your site.</p>
<p>The tools are listed alphabetically. Nothing here ranks them. A line that says "not stated on the page read" means the passage we read
did not say; it does not mean the tool has no such thing.</p>
<h2>Six tools sold for a one-time price</h2>
{_table()}
{_sections()}
<h2>What a one-time price leaves out</h2>
<p>A one-time price says nothing by itself about how long updates last. Of the passages we read, only Scrutiny and the BumbleCrawl deal page speak to updates.
Ask each vendor before you buy, and keep the answer with your receipt. Check the refund line too: where a page states a refund, the table gives it, and
where it does not, the table says so.</p>
<p>Where a tool runs also changes what you pay. A Windows-only app is no use on a Mac. A web service usually crawls from its own servers rather than from your computer,
which matters if the site is behind a login or on a private network.</p>
<h2>What the subscription tools cost, for contrast</h2>
<p>Screaming Frog's paid licence is ${sf['annual_low']} a year, read {sf_day}. Ahrefs plans that include Site Audit run ${lo} to ${hi} a month, read {ah_day}.
The entry price of each tool in the table above is below one year of Screaming Frog's licence, but they are not the same products: Screaming Frog is a crawler with a free tier
that has a URL cap, and Ahrefs is a cloud suite. See <a href="/best/screaming-frog-alternatives/">Screaming Frog alternatives for Mac and Windows</a>
and <a href="/vs/ahrefs-site-audit-alternative/">the cheaper Ahrefs Site Audit alternative comparison</a>.</p>
<div class="callout" id="check-engine"><h2>Check Engine: sold once, on Mac and Windows</h2>
<p>Check Engine runs {N_CHECKS} checks across {N_LANES} areas and orders repairs by impact and effort.
It is {PRICE_COMPACT}, one payment and no subscription, with a {REFUND_DAYS}-day refund and no conditions.
The free version shows a score, problem counts and the main problem with its fix; the full plan and report exports need a licence.</p>
{buy_block('best-no-subscription', try_app='best-no-subscription-try-free', anchor=False)}</div>
<p>For a Mac-only comparison, read <a href="/mac-seo-audit-tool/">SEO audit tools for Mac and what each costs over three years</a>.
For free limits, see <a href="/best/free-seo-audit-tools/">free SEO audit tools and their limits</a>.</p>
'''
    return render(
        cat='best', slug='seo-audit-software-no-subscription',
        title='SEO audit software with no monthly subscription (2026)',
        h1='SEO audit software with no monthly subscription',
        desc=f'Six SEO audit tools sold for a one-time price, for Mac, Windows or the browser: prices, free versions and refunds, read {READ_ONE_TIME}.',
        crumb='<a href="/best/">SEO tools compared</a> / SEO audit software with no monthly subscription',
        body=body, published="2026-11-22",
        faq=[
            ('Is there SEO audit software with no monthly subscription?',
             'Yes. Six are compared on this page, each sold for a one-time price: Check Engine, Scrutiny, SiteAuditLint, BumbleCrawl, SEO Site Auditor and SEOPilot. Prices and terms were read from each vendor\'s own pages on ' + READ_ONE_TIME + ' and can change.'),
            ('Which one-time SEO audit tool works on a Mac?',
             'Check Engine runs on Mac and Windows, Scrutiny runs on macOS only, and BumbleCrawl lists Windows and macOS on its lifetime-deal page. SEOPilot runs in the browser. SiteAuditLint and SEO Site Auditor are Windows apps.'),
            ('Does a one-time price include future updates?',
             'It depends on the vendor. Of the passages read, Scrutiny says a version 7 licence upgrades to version 12 with no upgrade fee, and the BumbleCrawl deal page lists all future updates. Ask each vendor before you buy.'),
        ])


def build_all() -> list[Path]:
    return [build()]
