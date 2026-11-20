"""Stated facts from the two supplied FACTS.md readings of 20 November 2026.

No captured page text or old data files are used as evidence for this batch.
Annual comparison amounts are derived from labelled annual or monthly prices.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

READ = '20 November 2026'
OWNERSHIP = ('We make Check Engine, one of the tools listed here. We describe every tool '
             'from its own pages, read on 20 November 2026, and we earn money when you buy Check Engine.')


@dataclass(frozen=True)
class Tool:
    name: str
    kind: str
    free: str
    feature: str
    price: str
    annual: Decimal | None
    has_free: bool
    sources: tuple[tuple[str, str], ...]
    detail: str


def tool(name, kind, free, feature, price, annual, has_free, url, detail, *extra):
    return Tool(name, kind, free, feature, price, Decimal(str(annual)) if annual is not None else None,
                has_free, ((name, url),) + extra, detail)


PLUGINS = (
    tool('Yoast SEO', 'WordPress plugin', 'Free plugin; Premium adds content tools.',
         'Page and content analysis; no site-wide audit named on the pages read.',
         'Premium $118.80 a year for one site, ex VAT.', '118.80', True,
         'https://yoast.com/product/yoast-seo-premium-wordpress/',
         'Use the content analysis beside the post you are editing. Premium adds a redirect manager, internal linking tools and SEO Workouts. A content check is a different task from crawling all your URLs.',
         ('WordPress listing', 'https://wordpress.org/plugins/wordpress-seo/')),
    tool('Rank Math', 'WordPress plugin', 'Free SEO Analyzer; no page cap stated. Printing and competitor analysis need PRO.',
         'SEO Analyzer runs inside WordPress.',
         'PRO regular $8.99 a month, billed annually, ex VAT.', '107.88', True,
         'https://rankmath.com/kb/seo-analysis/',
         'The Analyzer starts from the WordPress dashboard. Its printing option is PRO only, as is the Competitor Analyzer. Confirm which output you need before choosing a plan.',
         ('Plans', 'https://rankmath.com/pricing/')),
    tool('All in One SEO', 'WordPress plugin', 'Free plugin; audit features in the free version are not stated on the pages read.',
         'Site Audit Checklist; paid plans include unlimited SEO audits.',
         'Basic normally $99.00 a year for one site.', '99', True,
         'https://aioseo.com/pricing/',
         'The WordPress listing names a Site Audit Checklist with fixes in priority order. The pricing page includes unlimited audits from Basic onward. Do not treat the free download as proof that every audit feature is included.',
         ('WordPress listing', 'https://wordpress.org/plugins/all-in-one-seo-pack/')),
    tool('SEOPress', 'WordPress plugin', 'Free plugin; Site audit and white label need PRO.',
         'PRO site audit with Search Console-backed recommendations, scan history and CSV export.',
         'PRO $49.00 a year for one site, ex VAT; renews at the same price.', '49', True,
         'https://www.seopress.org/pricing/',
         'Keep content analysis separate from the paid Site Audit. The WordPress changelog names scan history, live progress and CSV export for the audit. All PRO licences include white label.',
         ('WordPress listing', 'https://wordpress.org/plugins/wp-seopress/')),
    tool('The SEO Framework', 'WordPress plugin', 'The plugin is free; no site audit named on the pages read.',
         'SEO setup; the Monitor extension page was not read.',
         'Extension Manager $7.00 a month, paid yearly, for two sites.', '84', True,
         'https://theseoframework.com/pricing/',
         'Its FAQ says website analysis needs to happen from outside the site. A Monitor extension is listed, but its own page was not read. Do not assume that extension provides the audit you need.',
         ('Plugin and FAQ', 'https://theseoframework.com/')),
    tool('Squirrly SEO', 'WordPress plugin and cloud tools', 'Free account: one site and one audit suite page a month.',
         'GEO/AEO Audit and cloud Audit Suite.',
         'PRO $19.99 a month, purchased annually.', '239.88', True,
         'https://plugin.squirrly.co/wordpress-seo-pricing/',
         'The WordPress listing asks you to connect a free Squirrly account for cloud tools. The audit allowance matters: PRO lists 100 audit suite pages a month. Starting inside WordPress does not mean every check runs on your server.',
         ('WordPress listing', 'https://wordpress.org/plugins/squirrly-seo/')),
    tool('Slim SEO', 'WordPress plugin', 'Free plugin; no site audit named on the pages read.',
         'Automated SEO setup; do not assume it includes an audit.',
         'Personal $59.00 a year for one site. Black Friday price shown on 20 November 2026.', '59', True,
         'https://wpslimseo.com/products/slim-seo-pro/',
         'The pages describe automated SEO setup rather than a site audit. Every Pro plan includes every Pro feature. Choose an audit tool separately if you need a list of issues across the site.',
         ('WordPress listing', 'https://wordpress.org/plugins/slim-seo/')),
    tool('SEOKEY', 'WordPress plugin', 'Free audit score, content and technical analysis, and action priorities.',
         'Audit all content; PRO adds an enhanced audit, bot 404 monitoring and Search Console connection.',
         'Single $49.00 a year for one site, ex VAT.', '49', True,
         'https://www.seo-key.com/pricing/',
         'The listing was last updated on 15 July 2025 and says tested up to WordPress 6.8.13. Check fit with your WordPress setup before installing. PRO adds audit features beyond the free analysis.',
         ('WordPress listing', 'https://wordpress.org/plugins/seo-key/')),
    tool('Bing Webmaster Tools Site Scan', 'Cloud, outside WordPress', 'Free SEO/GEO tools; Site Scan URL cap not stated.',
         'On-demand crawl for common technical SEO/GEO issues.', 'No paid price stated on the page read.', 0, True,
         'https://www.bing.com/webmasters/about',
         'Site Scan checks the site from outside WordPress. The page calls its SEO/GEO tools free but does not state a URL cap. Confirm crawl coverage before treating the results as a full-site check.'),
    tool('Google Lighthouse', 'Chrome DevTools, command line or Node module', 'Open source; price and URL cap not stated on the page read.',
         'Single-page performance, accessibility and SEO audits; not a crawler.', 'Price not stated on the page read.', None, False,
         'https://developer.chrome.com/docs/lighthouse/overview',
         'Lighthouse checks a page rather than following links across the site. Use it to inspect a page you are changing. The overview does not state a price, so we do not label it a free crawl.'),
)

CRAWLERS = (
    tool('Ahrefs Site Audit', 'Cloud', 'Ahrefs Free: 5,000 crawl credits per verified project per month.',
         'Site Audit page lists 180+ SEO and AEO issues.', 'Lite $1,290 a year; $129.00 a month on monthly billing.', 1290, True,
         'https://ahrefs.com/pricing',
         'Lite includes Site Audit and Always-on audit. It has 100,000 monthly crawl credits and a 25,000-page project cap. Ahrefs Free credits are used for HTML pages returning status code 200.',
         ('Free allowance', 'https://ahrefs.com/webmaster-tools'), ('Site Audit', 'https://ahrefs.com/site-audit')),
    tool('Netpeak Spider', 'Desktop, Windows and macOS', 'Free: 500 URLs and five threads.',
         'Website crawler; Pro has unlimited URLs and white-label PDF reports.',
         'Regular $193.00 a year; $20.00 a month on monthly billing.', 193, True,
         'https://netpeaksoftware.com/pricing/spider',
         'The free crawl stops at 500 URLs. Pro lists 200 threads and unlimited URLs. Use a known set of pages to check the report before planning a larger crawl.',
         ('Crawler', 'https://netpeaksoftware.com/spider')),
    tool('Screaming Frog SEO Spider', 'Desktop', 'Free: 500 URLs per crawl.',
         'Crawler for over 300 SEO issues.', '$279 a year in the USD view, per user.', 279, True,
         'https://www.screamingfrog.co.uk/seo-spider/',
         'This is the reference tool, included so its limits sit beside the alternatives. A licence lasts one year and each user needs a licence. A crawl that reaches the free limit has not checked every URL.',
         ('Licence prices', 'https://www.screamingfrog.co.uk/seo-spider/pricing/')),
    tool('SEO PowerSuite WebSite Auditor', 'Desktop, Windows, Apple and Linux', 'Free: 500 URLs and one project.',
         'Website audit report with issues and repair tips.', 'Professional suite $349.00 a year; stand-alone price not read.', 349, True,
         'https://www.link-assistant.com/pricing.html',
         'WebSite Auditor is part of SEO PowerSuite. Professional lists whole-site crawling. The supplied reading covers the suite price, so do not treat it as a price for the auditor alone.',
         ('Auditor', 'https://www.link-assistant.com/website-auditor/')),
    tool('SEOmator', 'Cloud', 'Free: one project and first diagnosis; 10 AI prompts and 25 Google keywords a day.',
         'Technical audit followed by content review.', 'Starter $490.00 a year; $49.00 a month on monthly billing.', 490, True,
         'https://seomator.com/pricing',
         'The pricing text is dated 25 October 2026 and was read on 20 November 2026. Keep the first diagnosis separate from ongoing paid work. White-label reports are marked after launch, so they are not a live feature here.',
         ('Product', 'https://seomator.com/')),
    tool('Semrush Site Audit', 'Cloud', 'Free account: one demo project and 10 reports a day; no per-audit URL cap stated.',
         'Technical issues grouped by severity.', 'SEO $117.33 a month billed annually; $139.00 a month on monthly billing.', '1407.96', True,
         'https://www.semrush.com/prices/',
         'The SEO plan includes Site Audit, five websites to monitor and 500 keywords to track daily. The pages read do not state Site Audit page limits by plan. Ask about that limit before moving a large crawl.',
         ('Site Audit', 'https://www.semrush.com/features/site-audit/')),
    tool('Sitebulb', 'Desktop and cloud', '14-day trial; no ongoing free version stated.',
         'Desktop Lite: 10,000 URLs per audit; Pro: 500,000.',
         'Desktop Lite $180 a year; $18.00 a month on monthly billing.', 180, False,
         'https://sitebulb.com/pricing/',
         'Sitebulb Pro runs on Windows or Mac. Pro costs $425 a year or $42.00 a month. Cloud starts at $1,500 a year. Decide whether you need a desktop crawl or a shared cloud setup before comparing the price.',
         ('Desktop and cloud', 'https://sitebulb.com/')),
    tool('Raven Tools', 'Cloud', 'Trial offered; no ongoing free tier stated.',
         'Site Auditor and white-label reports.', 'Small Business $468 a year prepaid; $49.00 a month on monthly billing.', 468, False,
         'https://raventools.com/marketing-platform/pricing/',
         'Small Business lists two campaigns or domains. Higher plans add more. A reporting platform can suit work that combines an audit with client updates, but compare the audit itself before buying for the reports.',
         ('Product', 'https://raventools.com/')),
    tool('SE Ranking', 'Cloud', '14-day trial; no ongoing free version stated.',
         'Website Audit with JavaScript rendering; up to 2,000,000 pages per project.',
         'Core regular $103.20 a month on annual billing; $129.00 a month on monthly billing.', '1238.40', False,
         'https://seranking.com/subscription.html',
         'Core lists 250,000 monthly audit pages. The audit feature page describes a larger per-project ceiling, which is not Core\'s monthly allowance. Compare both limits for the plan you would buy.',
         ('Website Audit', 'https://seranking.com/website-audit.html')),
    tool('Conductor Monitoring', 'Cloud', 'Three-week trial; no ongoing free tier stated.',
         'Continuous monitoring and 60 months of history.', 'No dollar price published on the pricing page read.', None, False,
         'https://www.conductor.com/pricing/',
         'Essentials lists 100,000 pages monitored across three websites. The Monitoring page describes continuous checks. ContentKing\'s address redirects to that page; the text read does not state an acquisition.',
         ('Monitoring', 'https://www.conductor.com/platform/monitoring/')),
    tool('JetOctopus', 'Cloud', 'Trial account after a demo; no ongoing free version stated.',
         'Crawler, log analysis, Search Console and GA4 data.', 'Billing periods could not be matched to the displayed prices; no price quoted.', None, False,
         'https://jetoctopus.com/pricing',
         'Growth lists 500,000 crawled URLs and two million log lines a month. The scraped pricing text shows several price pairs without a clear billing-period match. Ask for a dated quote rather than relying on one of those numbers.',
         ('Product', 'https://jetoctopus.com/')),
    tool('Lumar', 'Cloud', 'No free version found on the pages read.',
         'Technical SEO, site speed, accessibility and web analytics.', 'Quote required; no published price read.', None, False,
         'https://www.lumar.io/pricing/',
         'The product describes a cloud website intelligence platform. Its pricing page asks for a quote. Include the scope and size of your crawl in that request so the quote answers the same task as the desktop plans.',
         ('Product', 'https://www.lumar.io/')),
    tool('Oncrawl', 'Cloud', 'Free version not stated on the pages read.',
         'Crawl, log and performance data analysis.', 'Price not read; the pricing address returned no page.', None, False,
         'https://www.oncrawl.com/',
         'Oncrawl describes collecting and joining crawl, log and performance data without sampling. A demo link is present. No price or white-label claim was confirmed in the supplied reading.'),
)

WHITE_LABEL = (
    tool('SEOPress PRO', 'WordPress plugin', 'Free plugin; white label needs PRO.',
         'White label and Site audit included in all PRO licences.', '$49.00 a year for one site, ex VAT.', 49, False,
         'https://www.seopress.org/pricing/',
         'This is a WordPress plugin rather than a client reporting portal. Its pricing page includes both white label and Site audit in PRO. Confirm the report layout you need before treating plugin branding as a client handoff.'),
    tool('Netpeak Spider Pro', 'Desktop, Windows and macOS', 'Free crawl: 500 URLs; white-label reports are Pro only.',
         'PDF technical audit with your logo, contacts and recommendations.', 'Regular $193.00 a year; $20.00 a month on monthly billing.', 193, False,
         'https://netpeaksoftware.com/features/white-label-reporting',
         'The report feature removes Netpeak brand elements and accepts PNG, JPG or SVG logos. Export is PDF. The free plan does not include this report feature.',
         ('Pro price', 'https://netpeaksoftware.com/pricing/spider')),
    tool('AgencyAnalytics', 'Cloud reporting platform', '14-day trial; no ongoing free version stated.',
         'White-labelled client portal, logo, colors and custom domain; not an audit crawler.', '$20.00 a month per client.', 240, False,
         'https://agencyanalytics.com/pricing',
         'Automated client reporting and a white-labelled portal are included with every client. Count clients when making a budget. This is a place to report data, so arrange the site audit separately.',
         ('Features', 'https://agencyanalytics.com/features')),
    tool('Semrush My Reports Pro', 'Cloud reporting', 'Three Base reports with the first paid toolkit; Base does not include white label.',
         'Pro report branding, white label and custom domain.', '$20.00 a month per report; toolkit cost is separate.', 240, False,
         'https://www.semrush.com/kb/34-my-reports',
         'The white-label feature belongs to Pro reports. The Base tier costs $10.00 a month per report and has different features. The old Agency Growth Kit address did not confirm white-label inclusion.',
         ('Agency reporting', 'https://www.semrush.com/solutions/agencies/')),
    tool('Sitebulb Pro', 'Desktop, Windows or Mac', '14-day trial; no ongoing free version stated.',
         'White-label PDF reports with no Sitebulb mention; logo upload not confirmed.', '$425 a year for one user; $42.00 a month on monthly billing.', 425, False,
         'https://sitebulb.com/upgrade-to-pro/',
         'The desktop Pro page describes completely white-label PDFs. A logo-upload setting was not confirmed. The cloud reporting page describes shareable dashboards without a white-label claim.',
         ('Price', 'https://sitebulb.com/pricing/')),
    tool('Raven Tools', 'Cloud', 'Trial offered; no ongoing free tier stated.',
         'Small Business: subdomain, email and report branding; custom domain starts at Grow.',
         'Small Business $468 a year prepaid; $49.00 a month on monthly billing.', 468, False,
         'https://raventools.com/marketing-platform/pricing/',
         'The first two plans list subdomain, email and report white label. Grow and above list Full White Label, with a custom domain from Grow. Keep those levels separate when asking for a sample.'),
    tool('SEO Site Checkup Webmaster', 'Type not stated in the pricing reading', 'No free version stated in the pricing reading.',
         'White-label reports and brand-free exports; Basic excludes them. Webmaster crawls 100 URLs.',
         '$49.00 a month billed yearly; $69.00 a month on monthly billing.', 588, False,
         'https://seositecheckup.com/pricing',
         'Technical audits are included on all listed plans. White-label reports start at Webmaster, whose individual-page crawl limit is 100 URLs. Report branding and crawl coverage are separate limits.'),
    tool('SEO PowerSuite Enterprise', 'Desktop suite', 'Free auditor: 500 URLs and one project; white label needs Enterprise.',
         'White-label reports, custom templates, logo upload and scheduled delivery.', '$599.00 a year for the suite.', 599, False,
         'https://www.link-assistant.com/pricing.html',
         'Enterprise adds white-label reports to Professional features. The dedicated reporting page describes uploading a logo in project settings. The price here is for the suite on its one-year plan.',
         ('Reporting', 'https://www.link-assistant.com/white-label-seo-software-reports.html')),
    tool('SE Ranking with Agency Pack', 'Cloud', '14-day trial; no ongoing free version stated.',
         'Platform and report branding with your own domain.',
         'Core $103.20 a month on annual billing plus $69.00 a month for Agency Pack, annual billing only.', '2066.40', False,
         'https://seranking.com/white-label.html',
         'The Agency Pack is an add-on to a plan. Its price does not buy the base SEO subscription. The annual comparison adds Core and the pack so the starting budget includes both.',
         ('Plans and add-on', 'https://seranking.com/subscription.html')),
    tool('Sitechecker Premium', 'Cloud', '14-day trial; no ongoing free tier stated.',
         'Premium lists custom domain, app interface and email branding; PDF logos described on the feature page.',
         '$449.00 a month on monthly billing; annual plan mapping unclear.', 5388, False,
         'https://sitechecker.pro/white-label/',
         'Premium names custom domain and app and email branding. The white-label feature page describes PDF logos. Whether Basic or Standard includes PDF logos was not stated, so this comparison does not promise that.',
         ('Premium plan', 'https://sitechecker.pro/account/plans/')),
    tool('SEOmator Scale', 'Cloud', 'Free first diagnosis; white label not included in Free.',
         'White-label reports marked after launch, not live.', '$2,490.00 a year; $249.00 a month on monthly billing.', 2490, False,
         'https://seomator.com/pricing',
         'Scale is the only tier marked for white-label reports, and the row says after launch. Treat it as a planned feature. The pricing text is dated 25 October 2026, read on 20 November 2026.'),
)


def ordered(tools):
    # Free availability first. Then the entry paid year's cost, not a score.
    return sorted(tools, key=lambda t: (not t.has_free, t.annual is None,
                                       t.annual or Decimal(0), t.name.casefold()))


def claims(tools):
    return [(f'{t.name}: {t.kind}; {t.free}; {t.feature}; {t.price}; {t.detail}', url)
            for t in tools for _, url in t.sources]
