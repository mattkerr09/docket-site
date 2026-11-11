#!/usr/bin/env python3
"""Competitor comparisons.

Each page is authored, not templated. The strategy doc's rule applies: a
format-comparison page and a philosophy-comparison page should not share six
headings, and every page must name at least one thing the competitor does
better. A comparison that never concedes anything reads as marketing, and both
readers and models discount it.
"""
from __future__ import annotations

import datetime
import html
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from brand import FORMER_ADDRESS_SENTENCE  # noqa: E402
import facts as F  # noqa: E402
from render import SITE_BRAND, recorded_with
from render import (_human_date, speed_words, BETA_NOTE, FREE_CLAUSE, MAC_HW, MACOS, N_CHECKS, LATER_PRICE, PRICE_COMPACT, RELEASE,  # noqa: E402
                    price, price_note_html, render, buy_block, rival_monthly_range, COMPETITORS,
                    INTEL, INTEL_DMG, download_url, DATA, REFUND_DAYS, WINDOWS, N_LANES, founding_price_sentence, price_sentence)

#: "Choose the other tool when..." items about which computers Docket runs on. Derived, because one of them
#: still said an Intel Mac could not start Docket after the Intel build shipped.
WRONG_COMPUTER = ("<li><strong>You are on Linux, or want it in a browser.</strong> Docket's desktop app runs on "
                  "Macs and 64-bit Windows only.</li>" if WINDOWS else
                  "<li><strong>You are not on a Mac.</strong> Docket runs on macOS only.</li>")
WONT_START = ("Linux, where only the command-line build runs" if WINDOWS else
              "Windows or Linux, where Docket will not start" if INTEL else
              "Windows, Linux, or an Intel Mac, where Docket will not start")

#: How many optional checks reach the network, spelled, from the engine's own
#: connector registry. Typed as "four" here and in four other places while the
#: registry held five — see facts.optional_connectors for why that mattered and
#: why verify_numbers could not see it.
CONNECTORS_WORD = F.optional_connectors_word()
CONNECTORS_WORD_CAP = CONNECTORS_WORD.capitalize()

#: ⚠️ THIS SAID "Try it against your own site" above a Download link, on
#: thirteen pages. Nothing can be tried: an audit needs a licence key, so the
#: link handed a comparison-shopper 22 MB that stops at a key field. Matthew's
#: plan, 2026-09-24: every /vs/ page shows the price and a Buy button.
CTA = f"""
<div class="callout" id="buy">
<div class="callout-title">One purchase. No subscription.</div>
<p>Docket is a one-time purchase for Mac and Windows: no account, no crawl credits, and the crawl runs
on your machine. {CONNECTORS_WORD_CAP} optional checks fetch data it cannot produce alone; <code>--offline</code>
turns all {CONNECTORS_WORD} off.</p>
{buy_block("vs-page", big=False, try_app="vs-page-try-free")}
{('<p class="intel-dl">Intel Mac? <a href="' + download_url("vs-page-try-free-intel", to=INTEL_DMG) + '" data-ev="Download" data-ev-button="vs-page-try-free-intel">Get the Intel version</a></p>') if INTEL else ''}
</div>"""

#: The same callout for the Ahrefs page, which was inside a registered link
#: experiment until its read was scored on 2026-09-21 (~/ops/search). It had a
#: Buy button and one internal link and nothing else, so an added link would not
#: change what was being measured. It now gets the standard block, Try it free,
#: the sample report and the refund link included. The src stays "vs-ahrefs" so
#: its funnel history is continuous.
CTA_LINK_EXPERIMENT = f"""
<div class="callout" id="buy">
<div class="callout-title">One purchase. No subscription.</div>
<p>Docket is a one-time purchase for Mac and 64-bit Windows. It needs no account and has no crawl credits. The crawl runs
on your machine. {CONNECTORS_WORD_CAP} optional checks fetch data it cannot produce alone. <code>--offline</code>
turns all {CONNECTORS_WORD} off. <a href="/download/">Download Docket →</a></p>
{buy_block("vs-ahrefs", big=False, try_app="vs-ahrefs-try-free", anchor=False)}
{('<p class="intel-dl">Intel Mac? <a href="' + download_url("vs-ahrefs-try-free-intel", to=INTEL_DMG) + '" data-ev="Download" data-ev-button="vs-ahrefs-try-free-intel">Get the Intel version</a></p>') if INTEL else ''}
</div>"""

#: When the factual claims about competitors on these pages were last checked
#: against the competitor's own pages.
#:
#: These pages made seventeen statements about three named companies with no
#: date and no source anywhere on them. Most were concessions, which is the
#: point of the format, but several were falsifiable and two were negative
#: claims about what a competitor does *not* do — the kind most likely to become
#: untrue when they ship something, and the kind a reader has no way to age.
#:
#: A comparison page is the most exposed thing on a marketing site. Undated is
#: not neutral: it silently claims "true now", forever.
CHECKED_ON = "2026-08-10"
CHECKED_ON_HUMAN = "10 August 2026"

#: Claim sets read on a different day from the rest.
#:
#: One shared date was correct while every claim on this site had been read on
#: one afternoon. It stopped being correct the moment a page's facts were read
#: later: the Scrutiny page went live on 2026-08-15 stating "Checked 10 August
#: 2026" about figures nobody had looked at on 10 August. Wrong in the safe
#: direction — earlier than the truth — and still a false date on a claim about
#: somebody else's product, which is the one thing this note exists to prevent.
#:
#: Found by fetching the deployed page and reading it, not from the source.
CHECKED_HUMAN: dict[str, str] = {
    # Re-read 2026-10-19: the product page's own SoftwareApplication schema again (operatingSystem "MacOS", the
    # "There are no plans" answer for Windows, the 149 USD offer, the featureList). Unchanged.
    "scrutiny": "19 October 2026",
    "se-ranking-vs-screaming-frog": "9 November 2026",
    # Supplied browser readings, 2026-11-09: Lite is the Site Audit entry plan,
    # both crawl limits are listed, and bulk ZIP/CSV export supersedes the older help wording.
    "ahrefs": "9 November 2026",
    # Read live 2026-09-16, both tiers and the crawl quotas, from the vendor's
    # own pricing page. The CSV had carried 2026-08-10; re-reading confirmed the
    # prices unchanged and added the monthly crawl allowances, which are the
    # thing this page actually turns on.
    "seoptimer": "9 November 2026",
    # Re-read 2026-10-19 on the rendered plans page: the three plan prices and their annual rates, the "all plans
    # include" list, the five AI models and the core tools were unchanged. The detailed plan table also lists a
    # crawl-page total per plan, which the page had said Sitechecker does not publish; that is now stated and sourced.
    "sitechecker": "19 October 2026",
    # Re-read 2026-10-19, both the brands and the agencies views: the free Trial is now 50 prompts a day for 7 days
    # across three engines (it was 10 prompts run once on ChatGPT), and the agencies view prints add-on prices
    # (the brands view still prints none). Both are corrected below.
    "profound": "19 October 2026",
    # Re-read 2026-10-19, both the In-House and the Agencies tabs, billed annually and quarterly: the plans are now
    # Growth, Pro and Ultra plus Unlimited, at different prices and allowances from the two tiers read on 16 September.
    # Every claim below was rewritten from that read.
    "jetoctopus": "19 October 2026",
    "crawlraven": "19 October 2026",
    # Re-read 2026-10-19: the home page's own text (the free and Pro tiers, the 50 and 10,000 page caps, the $99 a
    # year price for the CLI and for the desktop app, the 16-category and 24-check wording, the JavaScript engine and
    # robots.txt paragraphs). The paid cap is stated against the CLI tier only, which is all the page states.
    "crawler-sh": "19 October 2026",
    # Re-read 2026-10-19 from each source named in the claim list. Until now these had no date of their own and
    # printed the shared 10 August 2026 date.
    # Screaming Frog: the product page (Chromium WRS, 500 URLs, Unlimited with its memory footnote, the Free vs Paid
    # table, and its User-Agent line, which now names AI crawlers and is sourced below) and the pricing page in its
    # USD view ($279 a licence for 1 to 4, per user). Re-read 2026-11-04, every claim unchanged.
    "screaming-frog": "4 November 2026",
    # Sitebulb: the features page (crawl maps, Prioritized Hints). The prices were read on the rendered pricing
    # page: Lite $18 a month or $180 a year, Pro $42 a month or $425 a year.
    "sitebulb": "19 October 2026",
    # Semrush: the pricing page (the Advanced plan is now sold by demo, so the top published plan is Pro+ at $299),
    # the Site Audit issues list, the Site Audit knowledge base article (its old address now redirects), the Site
    # Audit feature page and the technical SEO page.
    "semrush": "19 October 2026",
    # Lighthouse: the repository's default config (the SEO category is unchanged; there is now also an agentic
    # browsing category), the Lighthouse overview, the PageSpeed Insights page and the Core Web Vitals report page.
    "lighthouse": "19 October 2026",
    # Search Console: the API limits page, the two Search Console help pages, the Core Web Vitals report page and the
    # Chrome UX Report methodology page. All unchanged.
    "search-console": "19 October 2026",
}
CHECKED_ISO: dict[str, str] = {
    "scrutiny": "2026-10-19",
    "se-ranking-vs-screaming-frog": "2026-11-09",
    "ahrefs": "2026-11-09",
    "seoptimer": "2026-11-09",
    "sitechecker": "2026-10-19",
    "profound": "2026-10-19",
    "jetoctopus": "2026-10-19",
    "crawlraven": "2026-10-19",
    "crawler-sh": "2026-10-19",
    "screaming-frog": "2026-11-04",
    "sitebulb": "2026-10-19",
    "semrush": "2026-10-19",
    "lighthouse": "2026-10-19",
    "search-console": "2026-10-19",
}

#: What was actually read, and where. Anything not sourced here is not stated as
#: a fact about a competitor on these pages — it is either a concession, or
#: written as a limit of what could be checked.
#: The homepage's four-lane claim, and the day it was last read against the
#: vendors' own pages. Deliberately NOT `CHECKED_ON`: only these two were
#: re-read on this date, and reusing the other constant would assert that
#: Ahrefs, Semrush and Lighthouse had been re-read too.
#:
#: The claim used to read "Four things crawler tools ignore", unsourced and
#: undated, on the highest-traffic page of a site whose every comparison page
#: quotes its source. It was also wrong on its sharpest point — see the third
#: entry below, which is the vendor describing a capability we said they
#: lacked.
#:
#: Re-read 2026-10-19: Screaming Frog's product page (its feature list still names no conversion or landing-page
#: auditing, brand consistency or local-business SEO; the Google Analytics item pulls conversion data in, it does
#: not audit conversion), Sitebulb's features page (none of the four) and Screaming Frog's user guide sentence on the
#: user-agent setting (verbatim as quoted). Unchanged.
HOME_CLAIM_CHECKED = "2026-10-19"
HOME_CLAIM_CHECKED_HUMAN = "19 October 2026"

VERIFIED: dict[str, list[tuple[str, str]]] = {
    "home-four-lanes": [
        ("neither vendor's published feature list names conversion or "
         "landing-page auditing, brand consistency, or local-business SEO",
         "https://www.screamingfrog.co.uk/seo-spider/"),
        ("Sitebulb's features page names none of the four",
         "https://sitebulb.com/features/"),
        # The concession. Read it before writing anything about AI crawlers.
        ('the user-agent configuration "allows you to switch the user-agent of '
         'the HTTP requests made by the SEO Spider and which robots.txt '
         'directives are followed"',
         "https://www.screamingfrog.co.uk/seo-spider/user-guide/configuration/"),
        ('Screaming Frog\'s feature list describes its User-Agent setting as crawling "as a '
         'search bot such as Googlebot or Bingbot, AI crawlers, or your own custom UA"',
         "https://www.screamingfrog.co.uk/seo-spider/"),
    ],
    # Read 2026-08-15 from the SoftwareApplication JSON-LD on the vendor's own
    # product page, which is machine-readable and unambiguous. The visible page
    # also shows "$115 $86.25" beside a stale Black Friday note and a different
    # product (a serviced scheduled scan), and reading a price off that banner
    # would have published a wrong number about a named third party.
    "crawler-sh": [
        ("it describes itself as a local crawler that turns websites into "
         "RAG-ready Markdown for AI training, fine-tuning and agent context, "
         "built in Rust and running on your own machine",
         "https://crawler.sh"),
        ("its free tier is capped at 50 pages a session and its paid CLI tier at "
         "10,000; both CLI Pro and Desktop Pro are priced at 99 US dollars a year, "
         "and the page says one subscription covers both the CLI and the desktop "
         "app",
         "https://crawler.sh"),
        ('it states its SEO coverage twice and differently: "16-category SEO '
         'analysis" beside the paid tier, and "24 automated checks" in its '
         "workflow section",
         "https://crawler.sh"),
        ("it renders JavaScript with its own engine rather than headless "
         "Chrome, and respects robots.txt Disallow, Allow and Crawl-delay with "
         "adaptive pacing on 429 and 403",
         "https://crawler.sh"),
    ],
    "crawlraven": [
        ("its plans are billed monthly: Starter 29 US dollars for one site, Pro 39 for three sites "
         "with 10 a month for each extra site, Agency from 199 for twenty sites, and Enterprise by "
         "quote; a 7-day free trial on one site asks for no credit card",
         "https://crawlraven.com/pricing"),
        ("its cost comparison lists a Pro lifetime plan for 3 websites at 390 US dollars one-time, and "
         "its FAQ says lifetime is a single payment for a fixed number of sites",
         "https://crawlraven.com/pricing"),
        ("a technical SEO audit is listed among the Starter features, which Pro and Agency include, and its "
         "FAQ says it is included on eligible paid or trial websites within a monthly page allowance, with "
         "a CSV findings export; the page describes a 200-point technical audit",
         "https://crawlraven.com/pricing"),
        ("MCP access to up to 30 tools across approved scopes is listed, and its FAQ says MCP can read "
         "stored audits but cannot start them",
         "https://crawlraven.com/pricing"),
        ("the other features it lists are Search Console insights, linked GA4 reporting, keyword and "
         "page performance, keyword maps and cannibalization flags, content gaps and decay tracking, "
         "prioritised action items and, on Pro, import of Ahrefs and Semrush keyword lists",
         "https://crawlraven.com/pricing"),
        ("its FAQ says CrawlRaven offers a free audit tool for up to 100 pages with no account required",
         "https://crawlraven.com/pricing"),
    ],
    "jetoctopus": [
        ("its In-House plans are Growth, Pro and Ultra, priced 459, 1,089 and "
         "2,069 US dollars a month quarterly, or 349, 809 and 1,559 billed "
         'annually, with an Unlimited tier quoted only as "Let\'s talk"',
         "https://jetoctopus.com/pricing/"),
        ("the plans are metered on crawled URLs and log lines per month: 500,000 "
         "URLs and 2 million log lines on Growth, 2 million and 8 million on Pro, "
         "5 million and 25 million on Ultra, and custom on Unlimited",
         "https://jetoctopus.com/pricing/"),
        ("projects, seats and simultaneous crawls are unlimited on every tier, and "
         "the Agencies tab lists the same crawled-URL allowances with prices of its "
         "own, from 549 a month quarterly or 409 billed annually for Growth",
         "https://jetoctopus.com/pricing/"),
        ("its published product list leads with a Log Analyzer that tracks how "
         "Google and AI bots navigate a site, alongside a JavaScript crawler, "
         "GSC integration, AI search visibility, alerts and an MCP integration; "
         "its plan table adds GA4 integration and position tracking",
         "https://jetoctopus.com/pricing/"),
    ],
    "profound": [
        ("its pricing page for brands publishes two tiers and no price: a free "
         "Trial, and Enterprise at custom pricing reached through a demo",
         "https://www.tryprofound.com/pricing"),
        ("its agencies view names an Agency Growth plan with no price beside it, "
         "and prints two add-on prices: full client workspaces at 399 US dollars "
         "a month and 5 trial workspaces at 199 US dollars a month; Agency "
         "Enterprise is custom",
         "https://www.tryprofound.com/pricing"),
        ("the free Trial runs 50 unique prompts daily for 7 days, against "
         "ChatGPT, Gemini and Google AI Overviews, in one language and one "
         "region",
         "https://www.tryprofound.com/pricing"),
        ("Enterprise tracks up to 9 answer engines, with SSO/SAML and SOC2 "
         "compliance listed alongside dedicated support",
         "https://www.tryprofound.com/pricing"),
        ("its published platform list is Monitor, Answer Engine Insights, "
         "Prompt Volumes, Shopping, Agent Analytics, AI Marketer, Agents and "
         "Context Manager. No site crawler or technical audit appears in it",
         "https://www.tryprofound.com/pricing"),
    ],
    "sitechecker": [
        ("its plans are priced 99, 249 and 449 US dollars a month, discounted to "
         "83, 208 and 375 a month when paid annually",
         "https://sitechecker.pro/account/plans/"),
        ("every plan is listed as including unlimited users, unlimited recrawls, "
         "AI search visibility tracking, GSC and GA4 insights, and a rank tracker "
         "with SERP history",
         "https://sitechecker.pro/account/plans/"),
        ("its AI visibility tracker covers five models (ChatGPT, Gemini, Google "
         "AI Mode, Perplexity and Copilot) for brand visibility and for mentions "
         "and citations",
         "https://sitechecker.pro/account/plans/"),
        ("its core tools are listed as website crawler, website monitoring, rank "
         "tracker, GSC dashboard, SEO dashboard and AI visibility tracker",
         "https://sitechecker.pro/account/plans/"),
        ("its plan table lists the total pages crawled across an account: 10,000 on "
         "Basic, 50,000 on Standard, 200,000 on Premium and unlimited on Enterprise, "
         "beside unlimited site recrawls on every plan; the other published limits "
         "are on websites, tracked keywords and AI prompts",
         "https://sitechecker.pro/account/plans/"),
    ],
    "seoptimer": [
        ("its three plans are priced $29, $39 and $59 a month: Starter, Pro and Max",
         "https://www.seoptimer.com/pricing"),
        ("each plan lists a monthly crawl allowance: Starter 4 SEO crawls for 1 site, "
         "Pro 10 SEO crawls, Max 50 SEO crawls",
         "https://www.seoptimer.com/pricing"),
        ("Pro and Max name white label PDF reporting",
         "https://www.seoptimer.com/pricing"),
        ("Max names a lead generation tool",
         "https://www.seoptimer.com/pricing"),
        ("each plan offers a 7 day free trial",
         "https://www.seoptimer.com/pricing"),
    ],
    "scrutiny": [
        ('the vendor\'s own product schema gives operatingSystem "MacOS", with '
         '"There are no plans" for Windows',
         "https://peacockmedia.software/mac/scrutiny/"),
        ("that schema's offer states a price of 149 USD",
         "https://peacockmedia.software/mac/scrutiny/"),
        ('its published featureList is "Link checking, html validation, XML '
         'Sitemap generation, SEO, spell checking, site search"',
         "https://peacockmedia.software/mac/scrutiny/"),
    ],
    "se-ranking-vs-screaming-frog": [
        ('SE Ranking\'s Core plan states "250k pages per month in audit"',
         "https://seranking.com/subscription.html"),
        ('the same plan lists "25K API credits & MCP access"',
         "https://seranking.com/subscription.html"),
        ("its two priced plans are $129.00/mo and $279.00/mo, or $103.20 and "
         "$223.20 billed annually, above an Enterprise tier that says "
         "\u201cTalk to sales\u201d",
         "https://seranking.com/subscription.html"),
        ('it offers a "Start free 14-day trial" with "No credit card required"',
         "https://seranking.com/subscription.html"),
        ('Screaming Frog audits "over 300 SEO issues"',
         "https://www.screamingfrog.co.uk/seo-spider/"),
        ('you can "Download & crawl 500 URLs for free", and its page says "For '
         'just \u00a3199 per year you can purchase a licence, which removes the 500 '
         'URL crawl limit"',
         "https://www.screamingfrog.co.uk/seo-spider/"),
        ('its pricing page lists $279 per licence per year for 1 to 4 licences, '
         'and says "Licences are per user. 2 users will require 2 individual '
         'licences."',
         "https://www.screamingfrog.co.uk/seo-spider/pricing/"),
        ('SE Ranking\'s Growth plan states "2M pages per month in audit"',
         "https://seranking.com/subscription.html"),
        ("its Free vs Paid table puts Scheduling, Crawl Configuration, "
         "Save & Open Crawls, JavaScript Rendering, Crawl Comparison and "
         "Near Duplicate Content on the paid side only",
         "https://www.screamingfrog.co.uk/seo-spider/"),
    ],
    "screaming-frog": [
        ('renders with the "integrated Chromium WRS"',
         "https://www.screamingfrog.co.uk/seo-spider/"),
        ('its feature list describes the User-Agent setting as crawling "as a search bot such '
         'as Googlebot or Bingbot, AI crawlers, or your own custom UA"',
         "https://www.screamingfrog.co.uk/seo-spider/"),
        ('free tier limited to 500 URLs; paid crawl limit "Unlimited", with the maximum '
         '"dependent on allocated memory and storage"',
         "https://www.screamingfrog.co.uk/seo-spider/"),
    ],
    "sitebulb": [
        ('"crawl maps" as an interactive visualisation',
         "https://sitebulb.com/features/"),
        ('"Prioritized Hints": a prioritised, categorised issue list where each '
         "entry explains the issue and why it matters",
         "https://sitebulb.com/features/"),
    ],
    "ahrefs": [
        ("monthly Site Audit plans start at Lite $129, then Standard $249 and Advanced $449. "
         "Enterprise is custom. Starter has no Site Audit allowance. Unverified project limits are "
         "5, 20 and 50 on Lite, Standard and Advanced, with unlimited verified projects",
         "https://ahrefs.com/pricing"),
        ("monthly crawl credits are Lite 100,000, Standard 500,000 and Advanced 1.5M. "
         "Max pages per project are 25,000, 50,000 and 250,000 respectively",
         "https://ahrefs.com/pricing"),
        ("one user is included. Lite permits 2 extra users at $40 a month each, Standard 5 at $60 "
         "and Advanced 10 at $80. The wider platform includes backlink and keyword data and rank tracking",
         "https://ahrefs.com/pricing"),
        ("Site Audit lists 170+ issues as errors, warnings and notices, cloud crawling, JavaScript execution, "
         "raw HTML, rendered HTML and text search, and a speed claim of up to 170k URLs crawled per minute. "
         "Its GSC/GA connection is marked coming soon",
         "https://ahrefs.com/site-audit"),
        ("Ahrefs Free includes Site Audit for verified sites, with 5,000 crawl credits per month per project "
         "and unlimited verified sites",
         "https://ahrefs.com/free"),
        ("Ahrefs Webmaster Tools is now Ahrefs Free. Unverified sites require a paid plan",
         "https://ahrefs.com/webmaster-tools"),
        ("only internal HTML pages returning 200 spend crawl credits. Redirects, errors, images, CSS, "
         "JavaScript files and external links do not. Each verified project's first 5,000 credits a month "
         "are free on every plan",
         "https://help.ahrefs.com/en/articles/3119402-how-are-crawl-credits-in-site-audit-spent"),
        ("additional pay-as-you-go credits are disabled by default. Bought crawl credits last three billing "
         "months. No extra crawl-credit price is stated in this article or the pricing and crawl-credit pages",
         "https://help.ahrefs.com/en/articles/6061657-ahrefs-usage-based-pricing-for-credit-based-plans"),
        ("the pricing FAQ says enabling additional pay-as-you-go credits and data causes automatic charges "
         "when consumption exceeds plan limits",
         "https://ahrefs.com/pricing"),
        ("crawl settings include JavaScript rendering and scheduling by day, time and timezone. "
         "Authentication requires Advanced or higher",
         "https://help.ahrefs.com/en/articles/9082329-how-should-i-configure-my-site-audit-settings"),
        ("always-on auditing is available on Lite and higher",
         "https://help.ahrefs.com/en/articles/10957674-how-always-on-audit-works"),
        ("Project Boost Pro is $20 a month per project, with Ask AI, AI detection for 1,000 URLs per crawl, "
         "auto-submit to IndexNow, instant recrawl and always-on auditing at 10 pages per minute. "
         "Max is $200 a month per project, with Patches, IndexNow, Batch AI, unlimited AI-detection URLs "
         "and always-on auditing at 30 pages per minute",
         "https://ahrefs.com/pricing"),
        ("the Site Audit product page offers bulk ZIP or CSV issue exports with fixing instructions",
         "https://ahrefs.com/site-audit"),
        ("the export help article was also read. This comparison follows the product page's current "
         "bulk ZIP or CSV export wording",
         "https://help.ahrefs.com/en/articles/2646667-how-to-export-site-audit-report"),
        ("Site Audit overview PDFs use Print and most raw data exports are CSV. Cancellation keeps paid "
         "features active to the billing-cycle end, then moves the account to the free tier",
         "https://ahrefs.com/faq"),
        ("Report Builder is listed, with a scheduled-report add-on at $99 a month",
         "https://ahrefs.com/pricing"),
        ("the Site Audit connector for Looker Studio needs Advanced or higher and consumes no credits",
         "https://help.ahrefs.com/en/articles/9229306-how-can-i-use-ahrefs-with-looker-studio"),
        ("AI crawler server tests, conversion checks and tracking-readiness checks are not stated on the "
         "Site Audit page on 9 November 2026. Report branding is not stated there either",
         "https://ahrefs.com/site-audit"),
        ("report branding is not stated on the pricing page on 9 November 2026",
         "https://ahrefs.com/pricing"),
    ],
    # Lighthouse is the one entry here whose source is not a marketing page but
    # a configuration file, which is the strongest form this claim can take:
    # the SEO category is not described there, it is declared. Anyone can open
    # the same file and count the auditRefs.
    #
    # Two of these quote Google describing the limits of its own tool. They are
    # the load-bearing sentences on the page — an argument that Lighthouse's
    # SEO category is deliberately shallow, without Lighthouse saying so, would
    # be our opinion against Google's.
    "lighthouse": [
        ("the SEO category declares ten scored audits (is-crawlable, "
         "document-title, meta-description, http-status-code, link-text, "
         "crawlable-anchors, robots-txt, image-alt, hreflang and canonical) "
         "plus one manual entry, structured-data, carrying a weight of zero; "
         "is-crawlable is weighted so that failing it alone fails the category",
         "https://github.com/GoogleChrome/lighthouse/blob/main/core/config/"
         "default-config.js"),
        ('the category describes itself as "basic search engine optimization '
         'advice", adding that "there are many additional factors Lighthouse '
         'does not score here that may affect your search ranking"',
         "https://github.com/GoogleChrome/lighthouse/blob/main/core/config/"
         "default-config.js"),
        ('it is "an open-source, automated tool" run from Chrome DevTools, the '
         "command line, a Node module or PageSpeed Insights; you give it a URL "
         "to audit, and its documentation lists five sets of audits: "
         "performance, accessibility, best practices, SEO and agentic browsing",
         "https://developer.chrome.com/docs/lighthouse/overview"),
        ("the same config declares an agentic browsing category, shown as a "
         "fraction rather than a score out of 100, whose audits are "
         "agent-accessibility-tree, three WebMCP audits (form coverage, "
         "registered tools, schema validity), cumulative-layout-shift, llms-txt "
         "and ard-schema (an Agentic Resource Discovery manifest); none of them "
         "is named for a per-crawler robots.txt check",
         "https://github.com/GoogleChrome/lighthouse/blob/main/core/config/"
         "default-config.js"),
        ('PageSpeed Insights "uses Lighthouse to analyze the given URL in a '
         'simulated environment" for its lab data, while its field data is '
         '"powered by the Chrome User Experience Report (CrUX) dataset"',
         "https://developers.google.com/speed/docs/insights/v5/about"),
        ("the data behind Search Console's Core Web Vitals report \"comes from "
         'the CrUX report", which gathers metrics "from actual users visiting '
         'your URL (called field data)"',
         "https://support.google.com/webmasters/answer/9205520"),
    ],
    # Semrush is the one competitor whose own naming does not line up with
    # itself: the pricing page sells SEO / Starter / Pro+ / Advanced, and the
    # knowledge base still documents crawl limits under Pro / Guru / Business.
    # Both are quoted here as they were read, and the page says outright that
    # the two sets were not mapped onto each other, because guessing at which
    # tier gets which allowance would be inventing a fact about someone else's
    # product in order to finish a sentence.
    "semrush": [
        ('the entry plan is listed at $139/mo, or $117.33/mo billed annually; '
         'Starter is $199/mo and Pro+ is $299/mo, and the Advanced plan above '
         'them is custom, reached by a demo request; the entry plan lists '
         '"500 keywords to track daily"',
         "https://www.semrush.com/pricing/"),
        ('Site Audit can "check over 140+ website issues", ordered '
         '"Errors (most harmful to a website) - Warnings (harmful) - '
         'Notices (least harmful)"',
         "https://www.semrush.com/kb/542-site-audit-issues-list"),
        ("the crawl allowance is 20,000 pages per audit on Pro and Guru and "
         "100,000 on Business, against 100,000 / 300,000 / 1,000,000 pages a "
         "month, resetting on the 1st rather than rolling over; the same article "
         "says Semrush One Starter includes the Pro SEO Toolkit, Pro+ the Guru "
         "one and Advanced the Business one (the address this claim was first "
         "read at, kb/338, now redirects here)",
         "https://www.semrush.com/kb/31-site-audit"),
        ("AI crawler access is checked per bot, naming ChatGPT-User, "
         "OAI-SearchBot, Googlebot, Google-Extended, Perplexity-User, "
         "PerplexityBot, Claude-User and Claude-SearchBot",
         "https://www.semrush.com/features/site-audit/"),
        ('audits can be scheduled daily, weekly or monthly, with white-label '
         'reporting and tracking of "how each issue category trends over time"',
         "https://www.semrush.com/solutions/technical-seo/"),
    ],
    # Search Console is not a competitor, and the page that uses this key says
    # so in its first sentence. The rule applies with more force rather than
    # less: a statement about what Google's own free tool cannot do is the
    # easiest claim on this site to get wrong and the one a reader is most able
    # to check. Every falsifiable statement about it on that page is here, in
    # Google's own words, with the Google page it was read from.
    #
    # Two figures that circulate constantly in SEO writing are deliberately
    # absent, because no Google page stating them could be found: the 16-month
    # performance-data retention window, and CrUX's 28-day aggregation period.
    # Both are probably right. Neither is sourced, so the page omits them
    # instead of laundering a third-party number into a claim about Google.
    "search-console": [
        ('the URL Inspection API quota is "2000 QPD" and "600 QPM" per site',
         "https://developers.google.com/webmaster-tools/limits"),
        ('"Our tables can show a maximum of 1,000 rows, so some rows might be '
         'omitted"',
         "https://support.google.com/webmasters/answer/96568"),
        ('"Normally, however, collected data should be available in 2-3 days"',
         "https://support.google.com/webmasters/answer/96568"),
        ('Google "might not track some queries that are made a very small number '
         'of times", and most reports "only cover a representative sample" of a '
         "site's URLs",
         "https://support.google.com/webmasters/answer/96568"),
        ('"The data for the Core Web Vitals report comes from the CrUX report": '
         "field data from real visitors, reported at the 75th percentile, and "
         '"A URL group without threshold data for both LCP and CLS will not be '
         'on the report"',
         "https://support.google.com/webmasters/answer/9205520"),
        ("how much traffic a page needs before CrUX will report on it is not "
         'published: "An exact number is not disclosed"',
         "https://developer.chrome.com/docs/crux/methodology"),
    ],
}

# The Mac options page (/mac-seo-audit-tool/): every fact about a rival on it is a row of
# data/mac-options.json with its own source, and the date the row was read. Registered here, not
# in the builder, so the competitive-claims gate sees the claim set whether or not the page's
# builder has been imported.
import json as _json
from datetime import date as _date

_MAC = _json.loads((Path(__file__).resolve().parent.parent.parent / "data" / "mac-options.json")
                   .read_text(encoding="utf-8"))


def _mac_facts(data: dict) -> list:
    """The claim list for data/mac-options.json. Pure, so the competitive-claims gate can rebuild it from any
    old revision of that file and learn the day a fact last changed."""
    return ([(f"{o['name']}: {o['sold']}; free: {o['free']}; refund: {o['refund']}", o["source"])
             for o in data["options"]]
            + [(what, url) for what, url in data["sources_extra"]])


VERIFIED["mac-options"] = _mac_facts(_MAC)
#: Claim sets whose facts live in a data file rather than in the VERIFIED literal above, as
#: {key: (path from the repo root, builder from the parsed file to the claim list)}. The gate cannot
#: read these out of comparisons.py's history (they are assigned at import), so it replays the data
#: file instead. Without this a data-backed set read as "edited today" on every day after its date.
DATA_CLAIM_SETS = {"mac-options": ("data/mac-options.json", _mac_facts)}
CHECKED_ISO["mac-options"] = _MAC["read"]
_d = _date.fromisoformat(_MAC["read"])
CHECKED_HUMAN["mac-options"] = f"{_d.day} {_d.strftime('%B %Y')}"

# The Screaming Frog alternatives page (/best/screaming-frog-alternatives/): the same pattern as the Mac options
# page above. Every fact about a rival is a row of data/screaming-frog-alternatives.json with its own source and
# the day it was read; nothing about a rival is typed in the builder.
_SFA = _json.loads((Path(__file__).resolve().parent.parent.parent / "data" / "screaming-frog-alternatives.json")
                   .read_text(encoding="utf-8"))


def _sfa_facts(data: dict) -> list:
    """The claim list for data/screaming-frog-alternatives.json. Pure, like _mac_facts."""
    return ([(f"{t['name']}: runs on {t['runs_on']}; {t['sold']}; free: {t['free']}; crawl size: {t['urls']}; {t['features']}"
              + (f"; refunds: {t['refund']}" if t.get("refund") else "")
              + (f"; {t['note']}" if t.get("note") else "")
              + f"; read {_human_date(t.get('read', data['read']))}", t["source"])
             for t in data["tools"]]
            + [(what, url) for what, url in data["sources_extra"]])


# The white-label audit tools list (/best/white-label-seo-audit-tools/): the same pattern, its own data file.
_WLT = _json.loads((Path(__file__).resolve().parent.parent.parent / "data" / "white-label-audit-tools.json")
                   .read_text(encoding="utf-8"))


def _wlt_facts(data: dict) -> list:
    """The claim list for data/white-label-audit-tools.json. Pure, like _mac_facts."""
    return ([(f"{t['name']}: {t['kind']}; {t['white_label']}; {t['sold']}", t["source"]) for t in data["tools"]]
            + [(what, url) for what, url in data["sources_extra"]])


VERIFIED["wl-tools"] = _wlt_facts(_WLT)
DATA_CLAIM_SETS["wl-tools"] = ("data/white-label-audit-tools.json", _wlt_facts)
CHECKED_ISO["wl-tools"] = _WLT["read"]
_d = _date.fromisoformat(_WLT["read"])
CHECKED_HUMAN["wl-tools"] = f"{_d.day} {_d.strftime('%B %Y')}"

# The robots.txt tester page (/tools/robots-txt-tester/): what Google's robots.txt report is, read from Google's own pages.
_GRR = _json.loads((Path(__file__).resolve().parent.parent.parent / "data" / "gsc-robots-report.json")
                   .read_text(encoding="utf-8"))


def _grr_facts(data: dict) -> list:
    """The claim list for data/gsc-robots-report.json. Pure, like _mac_facts."""
    return [(what, url) for what, url in data["claims"]]


VERIFIED["gsc-robots-report"] = _grr_facts(_GRR)
DATA_CLAIM_SETS["gsc-robots-report"] = ("data/gsc-robots-report.json", _grr_facts)
CHECKED_ISO["gsc-robots-report"] = _GRR["read"]
_d = _date.fromisoformat(_GRR["read"])
CHECKED_HUMAN["gsc-robots-report"] = f"{_d.day} {_d.strftime('%B %Y')}"

VERIFIED["sf-alternatives"] = _sfa_facts(_SFA)
DATA_CLAIM_SETS["sf-alternatives"] = ("data/screaming-frog-alternatives.json", _sfa_facts)
CHECKED_ISO["sf-alternatives"] = max(t.get("read", _SFA["read"]) for t in _SFA["tools"])
_d = _date.fromisoformat(CHECKED_ISO["sf-alternatives"])
CHECKED_HUMAN["sf-alternatives"] = f"{_d.day} {_d.strftime('%B %Y')}"

#: The closing sentence of a verification note. Written for a competitor with a
#: price list and a roadmap, which Search Console has neither of, so that page
#: passes its own.
_DEFAULT_CLOSING = (
    "Products change and pricing changes; if something here has gone out of "
    'date, <a href="/about/">tell us</a> and it will be corrected. Everything '
    "else on this page is a comparison of approach, not a claim about their "
    "roadmap."
)


_RUN = json.loads((DATA / "vs-run.json").read_text())


def _run_date() -> str:
    d = datetime.date.fromisoformat(_RUN["date"])
    return f"{d.day} {d.strftime('%B %Y')}"


def _top_cta(src: str, *, anchor: bool = True) -> str:
    """The next step, in the first screen: Try it free, Buy beside it, and the
    price, the refund and the Macs it runs on at the button (the content
    standard, rules 2 and 3). The ending of the page has the longer version."""
    intel = (f'<p class="intel-dl">Intel Mac? <a href="{download_url(src + "-try-free-intel", to=INTEL_DMG)}" '
             f'data-ev="Download" data-ev-button="{src}-try-free-intel">Get the Intel version</a></p>'
             if INTEL else "")
    return f"""
<div class="callout compact" id="try">
{buy_block(src, big=False, try_app=src + "-try-free", anchor=anchor)}
{intel}
</div>"""


def _measured(intro: str, view: str = "table", *, former_address: bool = False) -> str:
    """Docket run on a real public site, with the figures the engine reported.

    Everything here comes from data/vs-run.json, which docket-app's
    scripts/shot_vs.mjs writes in the same run that captures the still: the real
    UI against the real engine, on our own site (publishing someone else's audit
    is not ours to do). Findings that name other companies or sites, a cookie
    consent finding among them, are counted and left out, as in the public
    sample report. Nothing on these pages about the run is typed.

    Three views of one run, because three pages that each carried the same table
    and caption would be near-duplicates of each other (lint's DUP check said
    so): "table" is the findings as a table, "list" is the same findings as an
    ordered list in a sentence each, and "areas" is the area scores with the
    first three findings in a line.
    """
    r = _RUN
    scores = "; ".join(f"{lane['label']} {lane['score']}" for lane in r["lanes"])
    alt = (f"Docket's results window after auditing {r['target']}: the area scores are {scores}. "
           "Areas that do not apply to a site are greyed out.")
    sev = [f"{r['by_severity'][k]} {k}" for k in ("high", "medium", "low", "notice") if k in r["by_severity"]]
    sev_text = ", ".join(sev[:-1]) + " and " + sev[-1] if len(sev) > 1 else "".join(sev)
    top = r["top"]
    lo = min(lane["score"] for lane in r["lanes"])
    hi = max(lane["score"] for lane in r["lanes"])
    full = sum(1 for lane in r["lanes"] if lane["score"] == hi)
    left = f"{r['left_out']} more name other companies or sites, a cookie-consent finding among them, and are left out here as they are in the public sample report."
    caption = {
        "table": (f"The area scoreboard in the Docket{recorded_with(r['engine'])} window after a real audit of "
                  f"{r['target']} "
                  f"on {_run_date()}: {r['pages']} pages crawled in {speed_words(r['seconds'])}, score {r['score']} "
                  f"out of 100, grade {r['grade']}.{FORMER_ADDRESS_SENTENCE if former_address else ''} "
                  "It is the app's interface running against the audit "
                  "engine, captured from that run, not a mockup."),
        "list": (f"Docket's results window for the audit below, run on {_run_date()}. Score {r['score']} out of "
                 f"100, grade {r['grade']}, across {r['pages']} pages in {speed_words(r['seconds'])}, and no crawl "
                 "credits spent, because there are none to spend."),
        "areas": (f"One crawl of {r['pages']} pages, finished in {speed_words(r['seconds'])} on a Mac: score "
                  f"{r['score']}, grade {r['grade']}. On a metered plan that is one crawl spent. Here nothing "
                  "counted it."),
    }[view]
    figure = f"""
<figure class="shot">
  <img src="/assets/vs-docket-run.webp" width="1600" height="1000" loading="lazy" decoding="async"
       data-brand-history alt="{html.escape(alt)}">
  <figcaption data-brand-history>{caption}</figcaption>
</figure>"""
    if view == "table":
        rows = "".join(
            f"<tr><td>{html.escape(t['severity'].capitalize())}</td><td>{html.escape(t['title'])}</td>"
            f"<td>{html.escape(str(t['effort']).capitalize())}</td><td>{t['pages']}</td></tr>"
            for t in top)
        after = f"""
<p>That audit found {r['findings_total']} things to fix: {sev_text}. Below are the ones that do not name
other companies or sites, in the order Docket ranked them. {left}</p>
<div class="wrap-tbl"><table class="cmp">
<thead><tr><th>Severity</th><th>Finding</th><th>Effort</th><th>Pages</th></tr></thead>
<tbody>{rows}</tbody></table></div>"""
    elif view == "list":
        items = "".join(
            f"<li><strong>{html.escape(t['severity'].capitalize())}:</strong> {html.escape(t['title'])}. "
            f"{html.escape(str(t['effort']).capitalize())} effort, {t['pages']} "
            f"page{'s' if t['pages'] != 1 else ''}.</li>" for t in top)
        after = f"""
<p>Docket's findings for that site, {r['findings_total']} in all ({sev_text}), come out as a ranked
list. This is the order it gave, with the ones that name nobody else:</p>
<ol>{items}</ol>
<p>{left}</p>"""
    else:
        first = "; ".join(html.escape(t["title"]) for t in top[:3])
        after = f"""
<p>The twelve areas scored from {lo} to {hi}, and {full} of them scored {hi}. Of the {r['findings_total']}
findings ({sev_text}), the first three Docket ranked among those that name nobody else were: {first}.
{left}</p>"""
    return f"""
<h2>Docket on a real site: ours</h2>
{intro}{figure}{after}
"""


#: SEOptimer's plans as its pricing page lists them (read by hand in a browser 2026-11-09: its site refuses automated requests).
#: (name, monthly price, crawls, what the plan names)
_SEOPT_TRIAL_DAYS = 7
_SEOPT_PLANS = [
    ("Starter", 29, "4 crawls, for 1 site", "20 tracked keywords"),
    ("Pro", 39, "10 crawls", "White label PDF reporting, 3 users"),
    ("Max", 59, "50 crawls", "White label PDF reporting and a lead generation tool, 6 users"),
]
_SEOPT_LO, _SEOPT_HI = _SEOPT_PLANS[0][1], _SEOPT_PLANS[-1][1]
_SEOPT_CRAWLS_LO, _SEOPT_CRAWLS_HI = (int(_SEOPT_PLANS[0][2].split()[0]), int(_SEOPT_PLANS[-1][2].split()[0]))


def _verified_note(key: str, closing: str = _DEFAULT_CLOSING) -> str:
    """A dated, sourced footer for any page making claims about a competitor.

    Rendered rather than remembered, so a claim cannot outlive its check
    quietly. `lint.py` fails the build if a comparison page names a competitor
    and does not carry one of these.
    """
    items = VERIFIED.get(key) or []
    if not items:
        return ""
    checked = CHECKED_HUMAN.get(key, CHECKED_ON_HUMAN)
    checks = "; ".join(
        f'{what} (<a href="{url}" rel="nofollow noopener">source</a>)'
        for what, url in items
    )
    read_note = ("Each rival's read date is shown with its claim below. " if key == "sf-alternatives" else
                 "The factual\nclaims about this product were read from its own pages on that date: ")
    return f"""
<p class="verified-note"><strong>Checked {checked}.</strong> {read_note}{checks}.
{closing}</p>"""


def screaming_frog() -> Path:
    # WHAT-WORKS-2026-11-02 pass (CEO, 2026-11-04: "screaming frog alternative", about 880 searches a month, rated
    # easy). The lede answers the search in full with numbers measured on this site by the shipped app; the price
    # comparison is computed from Screaming Frog's own pricing page, re-read 2026-11-04.
    sf = COMPETITORS["screaming-frog"]
    sf_year = int(sf["annual_low"])
    year = sf["price_checked"][:4]
    run = json.loads((DATA / "free-run.json").read_text())
    body = f"""
<p class="lede">Docket is a Screaming Frog alternative for people who want to be told what to fix
first rather than handed the crawl data. It is {PRICE_COMPACT}, where Screaming Frog is ${sf_year} a
year for each user, and when we pointed the free version at this site it read {run["pages"]} pages in
{run["seconds"]} seconds and put the most important of its {run["problems"]} problems first, with the fix.
Screaming Frog is still the better tool for raw crawl data, custom extraction and very large sites.</p>

<h2>What each costs, from their own price</h2>
<div class="wrap-tbl"><table class="cmp">
<thead><tr><th></th><th>Docket</th><th>Screaming Frog</th></tr></thead>
<tbody>
<tr><td>The first year</td><td class="yes">{PRICE_COMPACT}</td><td>${sf_year}</td></tr>
<tr><td>Three years</td><td class="yes">{PRICE_COMPACT}</td><td>${sf_year * 3:,}</td></tr>
<tr><td>Two people, one year</td><td class="yes">{PRICE_COMPACT} ({F.licence_covers()})</td><td>${sf_year * 2:,} (two licences)</td></tr>
</tbody></table></div>
<p>Screaming Frog's figure is its own, for one to four licences, read from its pricing page on
{_human_date(sf["price_checked"])}; it is free up to 500 URLs a crawl. Docket's free version runs the full
audit and shows the score, the count in each area and the top problem in full.</p>

<h2>What Screaming Frog does that Docket does not</h2>
<p>Three things, and they are real:</p>
<ul>
<li><strong>Rendering at scale, in the right engine.</strong> Screaming Frog renders with an
integrated Chromium engine across an entire crawl. Their page calls it the "integrated
Chromium WRS". Docket renders a small sample by default, with more on request through
<code>--render</code>, enough to answer whether the site is client-rendered and what that costs.
On a large React or Vue site, or for a bug that only appears in Chrome's renderer, Screaming
Frog is the tool.</li>
<li><strong>Custom extraction.</strong> XPath, CSS and regex extraction pulls arbitrary fields
out of a crawl: product prices, author names, whatever you define. Docket has no equivalent.</li>
<li><strong>Scale.</strong> Screaming Frog's paid licence lists no crawl limit; their page says
the maximum "is dependent on allocated memory and storage", with a hybrid engine that spills to
disk for large sites. Docket is bounded by design.</li>
</ul>

<h2>What Docket does that Screaming Frog does not</h2>
<p>Screaming Frog tells you that 412 pages have a short title. It does not tell you whether
that matters more than the noindex it also found, or which to do on Tuesday morning. Reviewers
describe its lack of built-in interpretation as simultaneously its greatest strength and its most expensive characteristic. The power is proportional to your own skill and your own time.</p>

<p>Docket ranks every finding by impact against effort and sorts them into four phases:
stop the bleeding, quick wins, build, polish. Each finding states what it costs you in plain
language and carries the exact markup to paste.</p>

<p>Beyond the ordering, Docket audits three areas that Screaming Frog's own feature list does
not cover as checks. That is what their page advertises, not proof the tool cannot be made to do it. Their custom extraction is powerful enough that a determined user could build some of this by
hand, and their user-agent setting names AI crawlers, so you can crawl as one and see what comes back:</p>
<ul>
<li><strong>AI search visibility.</strong> Per-crawler access for ChatGPT, Perplexity, Claude
and Gemini, separating search crawlers from training crawlers. Whether pages are
server-rendered, since most AI crawlers do not execute JavaScript. Entity resolution via
<code>sameAs</code>.</li>
<li><strong>Marketing conversion.</strong> Calls to action, above-the-fold value proposition,
form friction, social proof, pricing transparency, message match between title and headline.</li>
<li><strong>Tracking readiness.</strong> Analytics coverage gaps, missing ad pixels, consent,
and UTM parameters on internal links.</li>
</ul>

<h2>Side by side</h2>
<div class="wrap-tbl"><table class="cmp">
<thead><tr><th></th><th>Docket</th><th>Screaming Frog</th></tr></thead>
<tbody>
<tr><td>Price</td><td>One-time</td><td>Free to 500 URLs, then {price("screaming-frog")}</td></tr>
<tr><td>Who the licence covers</td><td>You, on {F.licence_covers()}</td>
    <td>One user. Their pricing page states that two users need two licences</td></tr>
<tr><td>Runs on</td><td>Your Mac or Windows PC</td><td>Your machine</td></tr>
<tr><td>Output</td><td>Ranked plan with fixes</td><td>Spreadsheet of crawl data</td></tr>
<tr><td>JavaScript rendering</td><td class="yes">Sampled, via WebKit</td><td class="yes">Yes, every page</td></tr>
<tr><td>Custom XPath extraction</td><td class="no">No</td><td class="yes">Yes</td></tr>
<tr><td>hreflang reciprocity</td><td class="yes">Yes</td><td class="yes">Yes</td></tr>
<tr><td>AI crawler audit</td><td class="yes">Yes</td><td class="no">Not listed as a check. Its user-agent setting names AI crawlers</td></tr>
<tr><td>Conversion audit</td><td class="yes">Yes</td><td class="no">Not listed</td></tr>
<tr><td>Local business SEO</td><td class="yes">Yes</td><td class="no">Not listed</td></tr>
<tr><td>Client-ready PDF</td><td class="yes">Built in, with your name and logo if you add them</td><td>Export and build it yourself</td></tr>
<tr><td>Scheduled re-audits</td><td class="yes">Yes, while the app is open</td><td>Scheduling in the paid tier, and it runs headless</td></tr>
</tbody></table></div>

<h2>Where the technical depth is genuinely equal</h2>
<p>Docket implements the checks Screaming Frog is specifically praised for, including the two
that fail silently and that most tools miss:</p>
<ul>
<li><strong>hreflang return tags.</strong> If page A declares B as its alternate and B does not
declare A back, Google discards the whole cluster. Every tag looks correct in isolation, which
is why this survives review.</li>
<li><strong>Conflicting canonicals.</strong> An HTML canonical that disagrees with the one in
the HTTP <code>Link</code> header. The header usually wins, so the page consolidates to a URL
nobody on the team chose, and the page source looks fine.</li>
</ul>
<p>Docket's robots.txt parser also does full longest-match resolution with <code>*</code> and
<code>$</code> support, which matters more than it sounds: the near-universal
<code>Disallow: /wp-admin/</code> plus <code>Allow: /wp-admin/admin-ajax.php</code> pair is
judged wrongly by any parser that resolves rules in order.</p>

<h2>Which one to pick</h2>
<p><strong>Choose Screaming Frog</strong> if you are a technical SEO, your sites are
JavaScript-heavy, you need custom extraction, or you are crawling hundreds of thousands of
URLs. It is the deeper instrument.</p>
<p><strong>Choose Docket</strong> if you need to hand someone a plan rather than a dataset, if
you care about AI search visibility or whether your landing pages convert, or if you want a
client-ready PDF without building one.</p>
<p>They are not mutually exclusive, and plenty of people will want both. If the other name on your list
is a cloud platform that meters its audit, <a href="/vs/se-ranking-vs-screaming-frog/">SE Ranking against
Screaming Frog</a> sets out that trade with both prices read from their own pages, and if that platform is
Ahrefs, our page on <a href="/vs/ahrefs-site-audit-alternative/">Ahrefs Site Audit</a> does the same for its crawl credits. If the site is large
enough that crawl budget is the real question, the tool that answers it is neither of these:
<a href="/vs/jetoctopus-alternative/">JetOctopus</a> reads your server logs, which shows what
Googlebot actually fetched rather than what your site would serve if asked.</p>
{_verified_note("screaming-frog")}
{CTA}"""

    return render(
        cat="vs", slug="screaming-frog-alternative",
        # The title says what the page is, a comparison, and leaves "alternatives" to
        # /best/screaming-frog-alternatives/: two pages answering one search split it
        # (the 8 Nov traffic diagnosis, Cause 5). No year, so it never needs re-dating.
        title=(
            ("Docket vs Screaming Frog: price, limits and uses")
            if SITE_BRAND == "checkengine"
            else ("Docket vs Screaming Frog: price, limits, what it does better")
        ),
        modified="2026-11-09",  # the title no longer targets the "alternatives" search
        desc=(f"{price_sentence()} Screaming Frog is ${sf_year} a year per user. Compare audit tools."),
        h1="Docket vs Screaming Frog",
        crumb='<a href="/">Docket</a> / <a href="/vs/">Compare</a> / Screaming Frog',
        body=body,
        faq=[
            ("Is Docket a Screaming Frog alternative?",
             "For prioritisation, reporting and non-technical users, yes. For JavaScript "
             "custom XPath extraction, rendering at scale and very large crawls, no. "
             "Screaming Frog does those better and Docket does not try to."),
            ("Does Docket render JavaScript like Screaming Frog?",
             "Yes, through a WebKit helper, but only a small automatic sample of each "
             "crawl rather than every page. Screaming Frog renders across the whole crawl "
             "in its integrated Chromium engine, which is the better tool for a large "
             "single-page application."),
        ],
    )


def sitebulb() -> Path:
    body = f"""
<p class="lede">Sitebulb and Docket are aiming at the same problem from different sides.
Sitebulb turns crawl data into visual reports an agency can present. Docket turns it into an
ordered list of work. If you need an interactive crawl map, Sitebulb is the better fit.
If you need to know what to do on Monday, Docket is more direct about it.</p>

<h2>Sitebulb's real advantage: an interactive crawl map</h2>
<p>Sitebulb's interactive crawl map is a feature Docket does not have. It draws the site as
an interactive map: isolated content clusters, pages buried too
deep, link equity pooling in the wrong places. Some structural problems are genuinely easier
to see than to read, and a client will understand a picture of their own site faster than a
table about it.</p>
<p>Docket draws a static structure map in its HTML report: pages in rings by click depth, sized
by link equity. It also compares audits with <code>docket diff</code>, writes client PDFs with
your agency's name and logo, and runs scheduled monitoring while the app is open. The map is
not interactive, so that remains a reason to choose Sitebulb.</p>

<h2>Where Docket is more useful</h2>
<p>Sitebulb prioritises issues and explains them in plain English, which is why it is the
friendlier of the two established crawlers. The remaining complaint in reviews is that its
hints still need experienced judgement to filter, particularly on large or programmatic
sites, where the volume of surfaced issues is itself the problem.</p>

<p>Docket's answer is to be conservative about what it reports and explicit about what it does
not know:</p>
<ul>
<li>An area that does not apply to your site is marked <strong>not applicable</strong>, never
scored 100. A software company with a head office is not told to put a city in its titles.</li>
<li>If a crawl is rate-limited or only reaches a fraction of the site, findings that claim
something is missing <strong>site-wide</strong> are withheld, and the report says they are
unknown rather than passing.</li>
<li>Copy-quality checks are English-only and stand down on other languages instead of
reporting every English phrase as absent.</li>
</ul>

<h2>Side by side</h2>
<div class="wrap-tbl"><table class="cmp">
<thead><tr><th></th><th>Docket</th><th>Sitebulb</th></tr></thead>
<tbody>
<tr><td>Price</td><td>One-time</td><td>{price("sitebulb")}</td></tr>
<tr><td>Runs on</td><td>Your Mac or Windows PC</td><td>Desktop or cloud</td></tr>
<tr><td>Site architecture visualisation</td><td class="yes">Static rings by depth, sized by equity</td><td class="yes">Interactive force-directed map</td></tr>
<tr><td>JavaScript rendering</td><td class="yes">Sampled, via WebKit</td><td class="yes">Yes, every page</td></tr>
<tr><td>Team collaboration</td><td class="no">No team accounts; one licence covers {F.licence_covers()}</td><td class="yes">Cloud tier</td></tr>
<tr><td>Ranked action plan</td><td class="yes">Four phases</td><td>Prioritised hints</td></tr>
<tr><td>AI search visibility</td><td class="yes">Yes</td><td class="no">No</td></tr>
<tr><td>Conversion &amp; tracking audit</td><td class="yes">Yes</td><td class="no">No</td></tr>
<tr><td>Local business SEO</td><td class="yes">Yes</td><td class="no">No</td></tr>
<tr><td>Section-by-section scoring</td><td class="yes">Inferred automatically</td><td>Segments you define</td></tr>
</tbody></table></div>

<p>One difference worth drawing out: Docket splits a site into sections itself, inferring them
from URL structure, on the theory that the people who most need the feature will not sit down
and write rules. Sitebulb's features page describes a Custom URL explorer where you choose the
columns, filters and sort, configuring the view rather than having it inferred. That is a
trade, and the report says so: inferred sections are less precise than ones you define.</p>

<h2>Which one to pick</h2>
<p><strong>Choose Sitebulb</strong> if visual reporting is how you sell work, if you need the
interactive crawl map, if your clients' sites are JavaScript-heavy, or if a team needs shared
access.</p>
<p><strong>Choose Docket</strong> if you want the audit to cover marketing and AI visibility as
well as technical SEO, if you would rather own the tool than rent it, or if you want a report
that is careful about the difference between "we checked and it is fine" and "we could not
check".</p>
{_verified_note("sitebulb")}
{CTA}"""

    return render(
        cat="vs", slug="sitebulb-alternative",
        title=(
            ("Docket vs Sitebulb: visual reports or a ranked plan?")
            if SITE_BRAND == "checkengine"
            else ("Docket vs Sitebulb: visual reports or a ranked plan? (2026)")
        ),
        desc=("Sitebulb has an interactive crawl map; Docket draws a static map in its audit report. "
              "Compare site audits, reports, prices and limits."),
        h1="Docket vs Sitebulb",
        crumb='<a href="/">Docket</a> / <a href="/vs/">Compare</a> / Sitebulb',
        body=body,
        faq=[
            ("Does Docket have site architecture visualisation like Sitebulb?",
             "Both draw maps. Docket draws a static picture in its HTML report: pages in rings by click depth, sized "
             "by link equity. Sitebulb's "
             "interactive crawl map is a reason to choose it."),
            ("Is Docket cheaper than Sitebulb?",
             "Docket is a one-time download; Sitebulb is " + price("sitebulb") + ". Over a year the "
             "difference is substantial, but Sitebulb's cloud tier offers team collaboration "
             "that Docket does not. Docket has no team accounts; one licence covers "
             + F.licence_covers() + "."),
        ],
    )


#: Monthly-billing prices and limits from the supplied 9 November 2026 reading.
_AH = F.ahrefs_credits()
_AH_UNVERIFIED = _AH["unverified_projects"]
_AH_PRICE = _AH["plan_price_per_month_usd"]
_AH_LO, _AH_HI = rival_monthly_range("ahrefs-site-audit")


def _months_past_docket(monthly: int) -> int:
    """The first month in which paying `monthly` a month has cost more than Docket's one price."""
    m = 1
    while monthly * m <= LATER_PRICE:
        m += 1
    return m


def _credit_rows() -> str:
    """Monthly plans with both crawl limits and the cost of twelve monthly bills."""
    rows = []
    for tier in ("Lite", "Standard", "Advanced"):
        monthly = _AH_PRICE[tier]
        rows.append(f"<tr><th scope=\"row\">Ahrefs {tier}</th><td>${monthly}</td>"
                    f"<td>{F.credits_for(tier)}</td><td>{F.max_pages_for(tier)}</td>"
                    f"<td>{_AH_UNVERIFIED[tier]}</td><td>${monthly * 12:,}</td></tr>")
    return "\n".join(rows)


def ahrefs() -> Path:
    rules = F.credit_rules()
    help_a, help_b = F.credit_help_centre()
    checked = CHECKED_HUMAN["ahrefs"]
    offer = founding_price_sentence() or f"{PRICE_COMPACT}."
    run = json.loads((DATA / "free-run.json").read_text())
    pro, max_boost = _AH["project_boost"]["Pro"], _AH["project_boost"]["Max"]
    seats = _AH["additional_users"]
    body = f"""
<p class="lede">Docket is an Ahrefs Site Audit alternative for people who want a ranked plan of fixes
and a one-time price. Ahrefs' cloud crawler checks for {_AH['site_audit']['issues']} issues.
Site Audit starts at Lite, ${_AH_PRICE['Lite']} a month on monthly billing. Ahrefs Free gives
{rules['free_credits_per_verified_project_per_month']:,} crawl credits a month per verified project.
Docket audits any public site on Mac or 64-bit Windows, with no account or crawl credits.
{offer} We make Docket. If you need a backlink index, keyword research or rank tracking, choose Ahrefs.</p>
<p class="table-note">Ahrefs facts checked {checked}. Each source is listed below.</p>
{_top_cta("vs-ahrefs-top", anchor=False)}

<h2>Which audit tool fits your work?</h2>
<div class="wrap-tbl"><table class="cmp">
<thead><tr><th scope="col">Your question</th><th scope="col">Ahrefs Site Audit</th><th scope="col">Docket</th></tr></thead>
<tbody>
<tr><th scope="row">What does it cost?</th><td>Lite ${_AH_PRICE['Lite']}, Standard ${_AH_PRICE['Standard']}, Advanced ${_AH_PRICE['Advanced']} a month. Enterprise custom. Starter has no Site Audit allowance.</td><td>{offer}</td></tr>
<tr><th scope="row">Can I try it free?</th><td>Verified sites only. {rules['free_credits_per_verified_project_per_month']:,} crawl credits a month per project.</td><td>Any public site, no account. Score, problem counts by area and the top problem in full.</td></tr>
<tr><th scope="row">Can I audit client sites?</th><td>Paid plans allow {_AH_UNVERIFIED['Lite']}, {_AH_UNVERIFIED['Standard']} or {_AH_UNVERIFIED['Advanced']} unverified projects on Lite, Standard or Advanced.</td><td>Any number of public sites, including client work.</td></tr>
<tr><th scope="row">What limits a crawl?</th><td>Monthly crawl credits and a page cap per project. See the plan table below.</td><td>Your page and depth settings, memory and a {F.crawl_minutes()}-minute default deadline.</td></tr>
<tr><th scope="row">Can it run while I am away?</th><td>Cloud scheduling and always-on audits on Lite and higher.</td><td>Scheduled re-audits run only while the app is open and the computer is awake.</td></tr>
<tr><th scope="row">Does it render JavaScript?</th><td>Yes, with JavaScript rendering enabled in crawl settings.</td><td>Renders a sample of pages as a browser would. The default does not render every page.</td></tr>
<tr><th scope="row">How are fixes sorted?</th><td>Errors, warnings and notices across {_AH['site_audit']['issues']} issues.</td><td>{N_CHECKS} checks in {N_LANES} areas, ranked by impact against effort, with fix text and markup where useful.</td></tr>
<tr><th scope="row">Does it test AI crawler access?</th><td>Not stated on Ahrefs' Site Audit page on {checked}.</td><td>robots.txt rules for {F.ai_agents()} AI crawlers, plus a separate homepage server test.</td></tr>
<tr><th scope="row">Does it have AI features?</th><td>Ask AI and AI detection through Project Boost Pro at ${pro['price_per_project_per_month_usd']} a month per project. Max is ${max_boost['price_per_project_per_month_usd']}.</td><td>Checks whether AI crawlers can reach and read the site.</td></tr>
<tr><th scope="row">Can I brand the report?</th><td>Not stated on Ahrefs' pricing or Site Audit page on {checked}.</td><td>Your name and logo on the client PDF in the paid version.</td></tr>
<tr><th scope="row">Can a team use it?</th><td>{_AH['users_included']} user included. Extra users cost ${seats['Lite']['price_per_month_usd']} to ${seats['Advanced']['price_per_month_usd']} a month each, depending on plan.</td><td>One licence covers {F.licence_covers()}. No team accounts or shared workspace.</td></tr>
<tr><th scope="row">Can it crawl behind a login?</th><td>Authentication on Advanced and higher.</td><td>No login setup for password-protected crawls. It audits pages it can reach publicly.</td></tr>
<tr><th scope="row">Backlinks, keyword index and rank tracking?</th><td>Included in the wider Ahrefs platform.</td><td>No backlink or keyword index. No rank tracking.</td></tr>
<tr><th scope="row">Search Console or Analytics connection?</th><td>The Site Audit page labels GSC/GA as coming soon.</td><td>No Search Console or Analytics account connection.</td></tr>
<tr><th scope="row">Can I use Looker Studio?</th><td>Site Audit connector on Advanced and higher.</td><td>No Looker Studio connector. Paid CSV and JSON exports.</td></tr>
</tbody></table></div>
<p class="table-note">Ahrefs sources read {checked}. <a href="https://ahrefs.com/pricing" rel="nofollow noopener">Plans</a>,
<a href="https://ahrefs.com/site-audit" rel="nofollow noopener">Site Audit</a>,
<a href="https://help.ahrefs.com/en/articles/9082329-how-should-i-configure-my-site-audit-settings" rel="nofollow noopener">crawl settings</a> and
<a href="https://help.ahrefs.com/en/articles/9229306-how-can-i-use-ahrefs-with-looker-studio" rel="nofollow noopener">Looker Studio</a>.</p>

<h2>Is Ahrefs Site Audit free?</h2>
<p>Yes, for sites whose ownership you verify. Ahrefs Free includes
{rules['free_credits_per_verified_project_per_month']:,} crawl credits a month per project and unlimited
verified sites. A paid plan is needed for sites you cannot verify, such as a prospect's or a
competitor's. A client's site can use the free allowance if its ownership is verified.</p>
<p>Docket's free version works on any public site with no account. It runs the audit and shows the score,
the number of problems in each area and the top problem with its fix. The full fix plan and report exports
need a licence. The screenshot below is the free version auditing our company site on
{_human_date(run['date'])}.</p>
<figure class="shot">
<img src="/assets/free-result.webp" width="{run['image']['width']}" height="{run['image']['height']}"
     loading="lazy" decoding="async" alt="Docket's free audit result. Score {run['score']} out of 100, {run['problems']} problems, with the top problem and its fix shown in full.">
<figcaption>{run['pages']} pages crawled in {speed_words(run['seconds'])}. Score {run['score']} out of 100,
{run['problems']} problems found, with {run['more']} more to unlock. Captured from Docket{recorded_with(run['engine'])}.</figcaption>
</figure>
<p class="table-note">Ahrefs sources read {checked}. <a href="https://ahrefs.com/free" rel="nofollow noopener">Ahrefs Free</a> and
<a href="https://ahrefs.com/webmaster-tools" rel="nofollow noopener">Webmaster Tools</a>.</p>

<h2>Crawl credits, page caps and extra charges</h2>
<p>A crawl credit pays for one internal HTML page that returns a 200 status. Redirects, pages that
return an error, images, CSS and JavaScript files, and links to other sites do not spend credits.
Each verified project's first {rules['free_credits_per_verified_project_per_month']:,} credits a month are free on every plan.</p>
<div class="wrap-tbl"><table class="cmp">
<thead><tr><th scope="col">Plan</th><th scope="col">Monthly price</th><th scope="col">Credits a month</th>
<th scope="col">Max pages per project</th><th scope="col">Unverified projects</th><th scope="col">Twelve monthly bills</th></tr></thead>
<tbody>{_credit_rows()}</tbody></table></div>
<p class="table-note">Monthly billing, read {checked}. The last column is the monthly price multiplied by twelve.
<a href="https://ahrefs.com/pricing" rel="nofollow noopener">Ahrefs pricing</a>.</p>
<h3>Two limits to check before a large crawl</h3>
<p>Lite's {F.credits_for('Lite')} monthly credits do not let one project exceed its
{F.max_pages_for('Lite')} page cap. Standard caps a project at {F.max_pages_for('Standard')} pages,
and Advanced at {F.max_pages_for('Advanced')}. Re-crawling pages after a fix uses the monthly allowance again.</p>
<p>Extra pay-as-you-go credits are off by default. If you enable them, Ahrefs' pricing FAQ says you are
automatically charged when use exceeds the plan's limits. Bought credits last
{rules['pay_as_you_go_credits_last_billing_months']} billing months. No price for extra crawl credits was
stated on the pricing page or the credit help pages read on {checked}.</p>
<p>Docket has no monthly credits or per-audit charge. You choose the page and depth settings. A crawl
still stops at its deadline, when it runs out of links, or at the limits of the computer's memory.
The default deadline is {F.crawl_minutes()} minutes. Everything mode allows {F.everything_hours()} hours.</p>
<p class="table-note">Credit sources read {checked}. <a href="{help_a['url']}" rel="nofollow noopener">How crawl credits are spent</a>,
<a href="{help_b['url']}" rel="nofollow noopener">usage-based pricing</a> and
<a href="{_AH['overage_source']}" rel="nofollow noopener">the automatic-charges FAQ on pricing</a>.</p>

<h2>What Ahrefs does that Docket does not</h2>
<ul>
<li><strong>Index data and rank tracking.</strong> Ahrefs supplies backlink and keyword data, plus rank tracking.
Docket has no backlink or keyword index and does not track search rankings. It has no Search Console connection.</li>
<li><strong>Cloud scheduling and always-on crawling.</strong> Ahrefs lets you schedule crawls by day, time and
timezone. Always-on audits are available on Lite and higher. Docket's schedule runs only while the app is open
and the computer is awake. It has no cloud or always-on crawler.</li>
<li><strong>Paid team seats.</strong> Lite includes {_AH['users_included']} user and lets you add up to
{seats['Lite']['maximum']} at ${seats['Lite']['price_per_month_usd']} a month each. Standard allows
{seats['Standard']['maximum']} extra at ${seats['Standard']['price_per_month_usd']} each, and Advanced
{seats['Advanced']['maximum']} at ${seats['Advanced']['price_per_month_usd']} each. Docket has no team accounts or shared workspace.</li>
<li><strong>Password-protected crawls.</strong> Ahrefs' settings help lists authentication on Advanced and higher.
Docket has no setup for logging into a protected site. Use public staging pages or a tool with authentication.</li>
<li><strong>JavaScript across the crawl.</strong> Ahrefs lets you enable JavaScript rendering and search raw HTML,
rendered HTML and page text. Docket renders a sample by default. A bug on an unsampled page may be missed.</li>
<li><strong>Crawl speed and scale.</strong> Ahrefs advertises up to {_AH['site_audit']['urls_per_minute_claim']} URLs
crawled per minute. We have not benchmarked that claim. Docket's default is {F.limits()['concurrency']} concurrent
requests with a {F.limits()['delay_seconds']}-second delay per worker. Large sites take longer on a laptop.</li>
<li><strong>Looker Studio.</strong> Ahrefs' Site Audit connector needs Advanced or higher and consumes no credits.
Docket has no connector.</li>
</ul>
<p class="table-note">Ahrefs sources read {checked}. <a href="https://ahrefs.com/pricing" rel="nofollow noopener">Pricing</a>,
<a href="https://ahrefs.com/site-audit" rel="nofollow noopener">Site Audit</a>,
<a href="https://help.ahrefs.com/en/articles/9082329-how-should-i-configure-my-site-audit-settings" rel="nofollow noopener">crawl settings</a>,
<a href="https://help.ahrefs.com/en/articles/10957674-how-always-on-audit-works" rel="nofollow noopener">always-on audits</a> and
<a href="https://help.ahrefs.com/en/articles/9229306-how-can-i-use-ahrefs-with-looker-studio" rel="nofollow noopener">Looker Studio</a>.</p>

<h2>What Docket adds to the audit workflow</h2>
<p>Docket ranks fixes by impact against effort. It checks calls to action, enquiry forms and tracking
readiness alongside technical SEO. These checks inspect pages. They do not read your conversion results
from an Analytics account.</p>
<p>For AI access, Docket checks robots.txt rules for {F.ai_agents()} AI crawlers. A separate optional server
test requests the homepage as {len(F.probes()['ai'])} AI crawlers and {F.probes()['search']}, with Docket's
identity added to each request. That can find a server refusal even when robots.txt allows the crawler.
It does not prove the crawler will index or cite the page.</p>
<p>AI crawler server tests, conversion checks and tracking-readiness checks are not stated on Ahrefs'
Site Audit page on {checked}. Report branding is not stated on its pricing or Site Audit page on that date.
An omitted feature is not proof that Ahrefs cannot do it. Ask Ahrefs if one decides the purchase.</p>
<p>Docket's paid version puts your own name and logo on the client PDF. The audit runs on your computer,
and its saved crawl and reports stay there unless you share them. {CONNECTORS_WORD_CAP} optional checks
fetch outside data. <code>--offline</code> turns those checks off. The crawler still needs to fetch the site.</p>
<p class="table-note">Ahrefs sources read {checked}. <a href="https://ahrefs.com/site-audit" rel="nofollow noopener">Site Audit</a> and
<a href="https://ahrefs.com/pricing" rel="nofollow noopener">pricing</a>.</p>

<h2>AI features in Ahrefs Site Audit</h2>
<p>Project Boost Pro costs ${pro['price_per_project_per_month_usd']} a month per project. It lists Ask AI in
Site Audit, AI detection for {pro['ai_detection_urls_per_crawl']:,} URLs per crawl, auto-submit to IndexNow,
instant recrawl and always-on auditing at {pro['always_on_pages_per_minute']} pages per minute.</p>
<p>Project Boost Max costs ${max_boost['price_per_project_per_month_usd']} a month per project. It lists
Patches, auto-submit to IndexNow, Batch AI, AI detection for unlimited URLs and always-on auditing at
{max_boost['always_on_pages_per_minute']} pages per minute. These are per-project add-ons. Docket's
AI-visibility checks test crawler access and page readiness.</p>
<p class="table-note">Read {checked}. <a href="https://ahrefs.com/pricing" rel="nofollow noopener">Project Boost pricing</a>.</p>

<h2>Exports, client reports and Looker Studio</h2>
<p>Ahrefs' Site Audit page now says you can export all issues in bulk as {' or '.join(_AH['site_audit']['bulk_export_formats'])}, with fixing instructions.
Its export help article was also read on {checked}. We use the product page's current bulk-export wording here.
Ahrefs' FAQ also lists overview PDFs through Print and most raw data as CSV.</p>
<p>The pricing page lists Report Builder, with a scheduled-report add-on at
${_AH['report_builder_price_per_month_usd']} a month. For Looker Studio, the Site Audit connector needs
Advanced or higher and consumes no credits. Docket's paid PDF, CSV and JSON exports have no export allowance,
and its PDF can carry your name and logo.</p>
<p class="table-note">Sources read {checked}. <a href="https://ahrefs.com/site-audit" rel="nofollow noopener">Bulk ZIP and CSV export</a>,
<a href="https://help.ahrefs.com/en/articles/2646667-how-to-export-site-audit-report" rel="nofollow noopener">export help</a>,
<a href="https://ahrefs.com/faq" rel="nofollow noopener">PDF and CSV formats</a>,
<a href="https://ahrefs.com/pricing" rel="nofollow noopener">Report Builder</a> and
<a href="https://help.ahrefs.com/en/articles/9229306-how-can-i-use-ahrefs-with-looker-studio" rel="nofollow noopener">Looker Studio</a>.</p>

{_measured("<p>This is Docket auditing our own site. The findings below show how its impact and effort ranking turns into a fix plan.</p>", "list")}

<h2>Cost over a year, and what happens if you cancel</h2>
<p>Using monthly billing for a full year costs ${_AH_PRICE['Lite'] * 12:,} on Lite,
${_AH_PRICE['Standard'] * 12:,} on Standard or ${_AH_PRICE['Advanced'] * 12:,} on Advanced, as shown in the
plan table. These totals exclude add-ons, extra users and extra credits. Annual billing has separate prices.
The subscription also pays for Ahrefs' research tools.</p>
<p>Docket has no renewal. {offer} One licence covers any number of sites, including client work,
on {F.licence_covers()}. There is a {REFUND_DAYS}-day refund with no conditions.</p>
<p>Ahrefs says paid features stay active until the end of your billing cycle after cancellation,
then the account moves to the free tier.</p>
<p class="table-note">Read {checked}. <a href="https://ahrefs.com/pricing" rel="nofollow noopener">Monthly prices</a> and
<a href="https://ahrefs.com/faq" rel="nofollow noopener">cancellation</a>.
<a href="/pricing/">Docket pricing</a> and <a href="/legal/refunds/">refund terms</a>.</p>

<h2>Who should use which, and when to use both</h2>
<ul>
<li><strong>Choose Ahrefs</strong> for keyword and backlink research, rank tracking, cloud audits,
team access or authenticated crawling. Check the plan for each feature.</li>
<li><strong>Choose Docket</strong> for a local audit of public sites, ranked fixes and branded client
reports with a one-time licence. Try the free version on the site you need to fix.</li>
<li><strong>Use both</strong> if you need Ahrefs' research data and want Docket's local fix plan and client PDF.</li>
</ul>
<p>For another desktop crawler, see <a href="/vs/screaming-frog-alternative/">Docket vs Screaming Frog</a>.
For the next step after an audit, see <a href="/how-to/content-audit/">how to do a content audit</a>.</p>
{_verified_note("ahrefs")}
{CTA_LINK_EXPERIMENT}"""

    return render(
        cat="vs", slug="ahrefs-site-audit-alternative",
        modified=CHECKED_ISO["ahrefs"],
        title="Ahrefs Site Audit alternative with prices and limits",
        desc=(f"Compare Ahrefs Site Audit from ${_AH_PRICE['Lite']}/month with Docket's one-time site audit. "
              "Free options, crawl credits, JavaScript, AI features and client reports."),
        h1="Ahrefs Site Audit alternative for a one-time price",
        crumb='<a href="/">Docket</a> / <a href="/vs/">Compare</a> / Ahrefs',
        body=body,
        faq=[
            ("Is Ahrefs Site Audit free?",
             f"Ahrefs Free gives {rules['free_credits_per_verified_project_per_month']:,} crawl credits a month per "
             f"verified project, with unlimited verified sites. Sites you cannot verify need a paid plan. "
             f"Read {checked} on Ahrefs' Free page. Docket's free version works on any public site with no account."),
            ("Can I audit a client's site with Ahrefs?",
             f"Yes. Paid plans allow {_AH_UNVERIFIED['Lite']} unverified projects on Lite, "
             f"{_AH_UNVERIFIED['Standard']} on Standard and {_AH_UNVERIFIED['Advanced']} on Advanced, "
             f"per Ahrefs' pricing page read {checked}. If the site's ownership is verified, it can use Ahrefs Free."),
            ("What happens when I run out of Ahrefs crawl credits?",
             "Pay-as-you-go extras are off by default. Enabling them permits automatic charges above the plan limits. "
             f"No extra crawl-credit price was stated on Ahrefs' pricing and credit help pages on {checked}. "
             f"Docket has no credits, but its crawl has page and depth settings and a {F.crawl_minutes()}-minute default deadline."),
            ("Is there a one-time alternative to Ahrefs Site Audit?",
             f"Docket runs on Mac and 64-bit Windows with no crawl credits. {offer} "
             f"One licence covers any number of sites on {F.licence_covers()}."),
            ("Does Ahrefs Site Audit render JavaScript?",
             f"Yes. Its Site Audit page says it executes JavaScript, with rendering enabled in crawl settings. "
             f"Read {checked}. Docket renders a sample of pages by default."),
            ("Does Ahrefs Site Audit have AI features?",
             f"Yes. Project Boost Pro lists Ask AI and AI detection at ${pro['price_per_project_per_month_usd']} "
             f"a month per project. Max lists Batch AI and unlimited AI detection at "
             f"${max_boost['price_per_project_per_month_usd']} a month per project. Read on Ahrefs' pricing page {checked}."),
            ("Can I white-label an Ahrefs site audit?",
             f"Report branding was not stated on Ahrefs' pricing or Site Audit page on {checked}. "
             "Ask Ahrefs about it before buying. Docket's paid version puts your own name and logo on the client PDF."),
            ("Can Docket replace Ahrefs?",
             "For audits of public sites, if a local fix plan fits your work. Docket has no backlink or keyword index, "
             "rank tracking or Search Console connection. It has no shared workspace or always-on crawler, "
             "and its scheduled audits run only while the app is open and the computer is awake."),
        ],
    )


#: The entry plan's monthly price and how many weeks of it Docket's one-time price equals. Derived from
#: competitors.csv and LATER_PRICE, because "roughly five weeks" was typed when Docket cost far less and stayed on the
#: page after the price moved to $349 (it is about eleven weeks of $139 a month).
_SEM_LO, _SEM_HI = rival_monthly_range("semrush-site-audit")
_SEM_WEEKS = round(LATER_PRICE / (int(_SEM_LO) * 12 / 52))


def semrush() -> Path:
    """Docket against the audit module of the larger of the two platforms.

    Deliberately not shaped like the Ahrefs page even though the competitor is
    the same kind of company. That page is about metering; this one is about
    what a subscription bundles, why the price comparison is unfair in Docket's
    favour, and the fact that Semrush shipped per-crawler AI access checks —
    which retires a differentiator this site has leaned on elsewhere. Headings,
    argument and table rows are its own.
    """
    body = f"""
<p class="lede">Semrush sells an index of the web with an audit tool attached. Docket sells the
audit tool and nothing else. If Site Audit is the part of Semrush you actually open, you are
renting the index to get at it, and the question on this page is whether that trade is worth
${_SEM_LO} a month or more to you. For a lot of people it is.</p>

<h2>What the subscription buys that a download cannot</h2>
<p>The concessions come first because they settle the question for most readers. Six things
Semrush gives you that Docket has no version of:</p>
<ul>
<li><strong>Backlinks.</strong> Referring domains, anchor text, who links to a competitor and
not to you. That comes from crawling the web continuously and keeping the result. Docket holds
none of it and is not building any.</li>
<li><strong>Keyword research.</strong> Volume, difficulty, the gap between your coverage and
someone else's. Same index, same reason. A tool without one that prints a monthly search volume
is showing you a guess with a number on it.</li>
<li><strong>Rank tracking.</strong> Their pricing page puts "500 keywords to track daily" on the
entry plan. Docket never looks at a search result page, so it has no idea where you sit on
one.</li>
<li><strong>Trend lines for the whole site.</strong> Their technical SEO page describes tracking
"how each issue category trends over time". That is the chart that shows a client the retainer
bought something. Docket has no equivalent view.</li>
<li><strong>Crawling somewhere other than your desk.</strong> Audits scheduled daily, weekly or
monthly run on their machines whether your laptop is open or shut, at 20,000 pages an audit on
Pro and Guru and 100,000 on Business.</li>
<li><strong>More than one person.</strong> Seats, shared projects, dashboards, alerts.</li>
</ul>

<p>Their knowledge base also says Site Audit can "check over 140+ website issues", against
Docket's {N_CHECKS}. A count is a weak measure of an audit. What decides its worth is
the order the findings arrive in and what each one tells you to do. It is still a larger
number, and writing around that would be its own kind of tell.</p>

<p>One further concession, which retires something this site has leaned on elsewhere. Semrush's
Site Audit page now checks AI crawler access per bot, naming ChatGPT-User, OAI-SearchBot,
Googlebot, Google-Extended, Perplexity-User, PerplexityBot, Claude-User and Claude-SearchBot.
Docket checks the same crawlers. What it adds is the sorting: search crawlers on one side,
training crawlers on the other, which is the distinction that decides whether a block in your
robots.txt costs you citations or only costs a model some training data.</p>

<h2>Severity is not a plan</h2>
<p>Semrush groups findings into three tiers and its knowledge base gives the order as "Errors
(most harmful to a website) - Warnings (harmful) - Notices (least harmful)". That says how bad
each thing is. It does not say what to do on Tuesday morning.</p>
<p>The gap opens as soon as two findings land in the same tier. A <code>noindex</code> left on a
pricing page and 300 thin product descriptions are both errors. One is a two-minute change worth
more than everything else on the list; the other is a quarter of somebody's writing time. Docket
scores each finding on impact against effort and drops it into one of four phases: stop the
bleeding, quick wins, build, polish. Reach is compressed as well, so a trivial issue that
happens to appear on 4,000 pages does not outrank a serious one on the homepage. The report
opens as a sequence instead of a filter you have to operate.</p>

<h2>The audit stays on your computer</h2>
<p>Docket has no account or sign-in. The app sends three anonymous counts, with no site address or audit result.
The <a href="/legal/privacy/">privacy page</a> lists them and how to turn them off. The crawl runs on your machine and each
run is written to <code>~/.docket/</code> as plain JSON you can diff, script against, or delete.
{CONNECTORS_WORD_CAP} checks reach outside by default and <code>--offline</code> turns all {CONNECTORS_WORD} off;
the licence key is checked with the payment provider about once a day.</p>
<p>Two consequences that matter in practice. Auditing a prospect's site before a pitch is a
quieter act on your own laptop than inside a vendor's project workspace. And re-running costs
nothing, so a fix gets verified the moment it ships rather than saved up until a crawl is worth
spending. Semrush's allowance is 100,000 pages a month on Pro, 300,000 on Guru and 1,000,000 on
Business, and their knowledge base notes those reset on the 1st rather than rolling over.</p>

<h2>Feature by feature</h2>
<div class="wrap-tbl"><table class="cmp">
<thead><tr><th></th><th>Docket</th><th>Semrush Site Audit</th></tr></thead>
<tbody>
<tr><td>Billing</td><td>Paid once</td><td>{price("semrush-site-audit")}</td></tr>
<tr><td>Where the crawl runs</td><td>Your computer</td><td>Their cloud</td></tr>
<tr><td>Crawl allowance</td><td class="yes">Whatever your machine will do</td><td>20,000–100,000 per audit, metered monthly</td></tr>
<tr><td>Checks</td><td>{N_CHECKS}</td><td class="yes">140+</td></tr>
<tr><td>Output</td><td class="yes">Four phases, impact against effort</td><td>Errors, warnings, notices</td></tr>
<tr><td>Backlink data</td><td class="no">None</td><td class="yes">Yes</td></tr>
<tr><td>Keyword volume &amp; difficulty</td><td class="no">None</td><td class="yes">Yes</td></tr>
<tr><td>Rank tracking</td><td class="no">No</td><td class="yes">500 keywords daily on the entry plan</td></tr>
<tr><td>Trending over time</td><td>Each run kept locally as JSON</td><td class="yes">Charted by issue category</td></tr>
<tr><td>Seats</td><td class="no">No</td><td class="yes">Yes</td></tr>
<tr><td>Reports with your own name and logo</td><td class="yes">Yes</td><td class="yes">Yes</td></tr>
<tr><td>AI crawler access</td><td class="yes">Per bot, split search from training</td><td class="yes">Per bot</td></tr>
<tr><td>Account required</td><td class="yes">None</td><td>Yes</td></tr>
<tr><td>Runs on</td><td>macOS on {MAC_HW}</td><td class="yes">Any browser</td></tr>
</tbody></table></div>

<h2>The arithmetic, and why it flatters Docket</h2>
<p>Semrush's pricing page lists the entry plan at $139 a month, or $117.33 a month billed
annually. Paid monthly that is $1,668 in the first year and the same again in the second. Docket is {PRICE_COMPACT} ({FREE_CLAUSE}), which works out at roughly {_SEM_WEEKS}
{"week" if _SEM_WEEKS == 1 else "weeks"} of the cheapest Semrush plan.</p>
<p>Then take the flattery back out. That $139 is not the price of a site audit. It is the price
of keyword research, rank tracking and a backlink index, with an audit included. If you use
those three, cancelling to save on the audit saves nothing, because the rest of the platform
still costs $139. The comparison only runs one way: when Site Audit is the tool you open and
the remainder is shelfware.</p>
<p>One caveat we are not going to paper over. Their pricing page currently sells SEO, Starter,
Pro+ and Advanced, and Advanced is custom: you ask for a demo rather than see a price. Their
knowledge base documents crawl limits under Pro, Guru and Business, and says that Semrush One
Starter includes the Pro toolkit, Pro+ the Guru one and Advanced the Business one. It does not
name the $139 SEO plan, so we have not guessed which allowance that one carries. Read the limits on
the plan in front of you rather than trusting the row above.</p>

<h2>Reasons to buy Semrush instead</h2>
<p>Docket is the wrong purchase, and a cheap wrong purchase is still wrong, if any of this is
your week:</p>
<ul>
<li>You need to know who links to a competitor.</li>
<li>You need search volume, keyword difficulty or a content gap analysis.</li>
<li>You track positions for a keyword list and report on the movement.</li>
<li>Two or more people have to open the same results, or the report has to carry a client's
branding.</li>
<li>Audits have to run on a schedule whether or not your machine is awake.</li>
<li>Somebody wants a twelve-month trend line for a board deck.</li>
<li>You are on {WONT_START}.</li>
<li>Your crawls run to hundreds of thousands of URLs.</li>
</ul>
<p>Two of those and it is not a close call. There is no version of this page where Docket wins
that argument on price.</p>

<h2>Who each one is for</h2>
<p><strong>Semrush</strong> suits people for whom search is the job rather than a Thursday
afternoon: agencies pitching on keyword opportunity, in-house SEO teams reporting upward, anyone
whose work needs the index behind it.</p>
<p><strong>Docket</strong> suits people who need the audit itself, in order, on hardware they
control, at a price that stops. Freelancers, marketers who own the website alongside four other
responsibilities, and agencies auditing prospects who have not signed anything yet.</p>
<p>Running both is a normal answer rather than a fence-sit. The platform answers where you
stand; the local tool answers what to change next.</p>
{_verified_note("semrush")}
{CTA}"""

    # Other comparisons: the six /vs/ pages Google had not discovered on
    # 2026-09-22. The /vs/ hub that lists them was last crawled 11 August;
    # this page is among the comparison pages crawled most recently. Kept
    # to comparison pages so no article reading list names a vendor.
    body += """
<h2>Other comparisons</h2>
<ul>
<li><a href="/vs/crawler-sh-alternative/">Docket vs crawler.sh</a></li>
<li><a href="/vs/crawlraven-alternative/">Docket vs CrawlRaven</a></li>
<li><a href="/vs/jetoctopus-alternative/">Docket vs JetOctopus</a></li>
<li><a href="/vs/profound-alternative/">Docket vs Profound</a></li>
<li><a href="/vs/seoptimer-alternative/">Docket vs SEOptimer</a></li>
<li><a href="/vs/sitechecker-alternative/">Docket vs Sitechecker</a></li>
<li><a href="/vs/se-ranking-vs-screaming-frog/">SE Ranking vs Screaming Frog</a></li>
</ul>
"""
    return render(
        cat="vs", slug="semrush-site-audit-alternative",
        title="Docket vs Semrush Site Audit: a one-time alternative",
        desc=("Semrush Site Audit is 140+ checks inside a platform from $139/mo. Docket is a "
              "one-time audit for Mac and Windows with a ranked fix plan."),
        h1="Docket vs Semrush Site Audit",
        crumb='<a href="/">Docket</a> / <a href="/vs/">Compare</a> / Semrush',
        published="2026-08-10",
        body=body,
        faq=[
            ("Is Docket a Semrush alternative?",
             "For the site audit, yes. For the rest of Semrush, no. Keyword volumes, backlink "
             "data and rank tracking come from an index of the web that Docket has no "
             "equivalent of and will not be building. Keep Semrush if you use those; Docket "
             "covers the audit for a one-time price."),
            ("How much cheaper is Docket than Semrush?",
             "Semrush's pricing page lists its entry plan at $139 a month, or $117.33 a month "
             "billed annually, which is $1,668 in a year paid monthly. Docket is " + PRICE_COMPACT
             + f", about {_SEM_WEEKS} {'week' if _SEM_WEEKS == 1 else 'weeks'} of that plan. The saving is only real if the "
             "site audit is the part of Semrush you use."),
            ("Does Docket have crawl limits like Semrush?",
             "Not monthly ones. Semrush's knowledge base lists 20,000 pages per audit on Pro "
             "and Guru and 100,000 on Business, drawn against 100,000 to 1,000,000 pages a "
             "month depending on plan, resetting on the 1st. Docket crawls on your computer, so "
             "the bounds are the page and depth caps you set, and re-running an audit costs "
             "nothing."),
            ("Does Docket check AI crawler access like Semrush?",
             "Both do, so this is not a reason to switch either way. Semrush's Site Audit page "
             "names ChatGPT-User, OAI-SearchBot, Google-Extended, Perplexity-User, "
             "PerplexityBot, Claude-User and Claude-SearchBot among the bots it checks. Docket "
             "checks the same crawlers and separates search crawlers from training crawlers "
             "such as GPTBot, because blocking one of those costs you citations and blocking "
             "the other does not."),
        ],
    )


def lighthouse() -> Path:
    """Docket vs Lighthouse.

    Not the same shape as the other three, on purpose. Screaming Frog, Sitebulb
    and Ahrefs are alternatives — you buy one instead of Docket. Lighthouse is
    not: it is free, it is Google's, and the correct recommendation is to keep
    running it. A page laid out as "what they do / what we do / pick one" would
    misdescribe the relationship before the reader got to the first table.

    The Core Web Vitals section is the one that matters. Docket does not measure
    LCP, INP or CLS, and this page says so under its own heading rather than in
    a parenthesis, because the reader arriving here is arriving from a speed
    tool and that is the first thing they will assume.
    """
    body = f"""
<p class="lede">Lighthouse is free, open source, built into a browser you already have, and
made by the company whose search engine you are trying to rank in. On page speed it is the
instrument, and nothing here argues for turning it off. What it is not is a site audit:
Lighthouse scores one URL at a time, and its SEO category is ten scored checks that Google's
own description of it calls basic.</p>

<h2>What Lighthouse does better, said first</h2>

<p>Performance, and it is not close. Lighthouse drives a real Chrome, records a trace, and
reports Largest Contentful Paint, Cumulative Layout Shift and Total Blocking Time from that
run, with a filmstrip of the load and a treemap of where the bytes went. Docket has nothing of
the kind and is not building it.</p>

<p>Three more, briefly. It scores accessibility and best practices, two entire categories
Docket does not attempt. It costs nothing at any volume, from Chrome DevTools, the command
line, a Node module for continuous integration, or PageSpeed Insights in a browser tab with no
install at all. And it is Google's, which settles arguments: when a client asks whether Google
cares about a thing, the tool and the search engine came from the same building.</p>

<h2>The SEO category, in full</h2>

<p>Here is the entire list, read from the config file that ships in the Lighthouse repository
rather than from anybody's summary of it: <code>is-crawlable</code>,
<code>document-title</code>, <code>meta-description</code>, <code>http-status-code</code>,
<code>link-text</code>, <code>crawlable-anchors</code>, <code>robots-txt</code>,
<code>image-alt</code>, <code>hreflang</code> and <code>canonical</code>. Ten scored audits,
plus a manual eleventh, <code>structured-data</code>, which carries a weight of zero and
asks you to go and validate your schema somewhere else.</p>

<p><code>is-crawlable</code> is weighted so heavily that failing it fails the category on its
own, and the comment beside it in the config says that is deliberate. Which is the right call.
An accidental <code>noindex</code> is the most expensive mistake in technical SEO, and
Lighthouse finds it in ten seconds for nothing.</p>

<p>The shallowness is stated, not hidden. The description at the top of the category says the
checks follow basic search engine optimisation advice, and that there are many additional
factors Lighthouse does not score which may affect your ranking. That is Google marking the
edge of its own tool, and the useful question is what sits outside the line.</p>

<p>One addition since this page was first written: Lighthouse's documentation now lists a fifth set
of audits, agentic browsing. In the repository config it is shown as a fraction rather than a
score out of 100, and its audits cover WebMCP tools and forms, an accessibility tree for agents, an
<code>llms.txt</code> file and an Agentic Resource Discovery manifest. None of them is named for
whether a particular AI crawler is allowed in by your robots.txt or by your server, which is the
question Docket's AI crawler check answers.</p>

<h2>One URL is the unit</h2>

<p>You give Lighthouse a URL and it reports on that page. Run it against your homepage and you
have audited your homepage.</p>

<p>Most of what quietly breaks a site is not a property of a page. It is a relationship
between pages, and a single-page run cannot see a relationship by construction:</p>
<ul>
<li><strong>hreflang return tags.</strong> Lighthouse checks that the hreflang on this page is
valid. Whether the page it names points back is a two-page question, and Google discards the
whole cluster when the answer is no.</li>
<li><strong>Canonical clusters.</strong> A well-formed <code>rel=canonical</code> passes.
Forty pages all canonicalising to the same URL also passes, forty separate times.</li>
<li><strong><a href="/how-to/fix-duplicate-title-tags/">Duplicate and templated titles</a>.</strong> <code>document-title</code> asks whether
a title exists, not whether it is the same title as three hundred other pages.</li>
<li><strong>Click depth and internal link equity.</strong> Both are properties of the link
graph, and there is no graph in one page load.</li>
</ul>

<h2>What Docket cannot tell you about speed</h2>

<p>Read this before buying, because you are arriving from a speed tool and the assumption is
natural. <strong>Docket does not measure Core Web Vitals.</strong> It has seven speed checks
and every one of them is a cause rather than a vital: time to first byte, compression and
caching headers, page weight, render-blocking resources, image formats, redirect latency, and
layout-shift risk inferred from the markup.</p>

<p>Those are the things you change to fix a bad LCP or CLS. They are not the LCP or the CLS.
Those are field metrics, measured on real users on real connections, which is why Search
Console's Core Web Vitals report is built from the Chrome UX Report rather than from a lab run, and why PageSpeed Insights shows two panels, Lighthouse in a simulated environment on
one side and CrUX field data on the other.</p>

<p>Docket has one optional check that fetches those field values from the PageSpeed Insights
API, which is the same CrUX data Search Console shows. It is one of {CONNECTORS_WORD} optional checks that reach off
your machine; <code>--offline</code> turns them off. The report's scope page says whether
Core Web Vitals field values were read, Google had no field data, or they were not asked for. If you are trying to
move LCP: change what Docket points at, measure it in Lighthouse, confirm it in Search
Console. Docket will tell you which markup is costing you. It will not tell you whether the
fix landed.</p>

<h2>What each one hands you</h2>
<div class="wrap-tbl"><table class="cmp">
<thead><tr><th></th><th>Docket</th><th>Lighthouse</th></tr></thead>
<tbody>
<tr><td>Price</td><td>One-time</td><td class="yes">{price("lighthouse").capitalize()}, open source</td></tr>
<tr><td>Unit of analysis</td><td class="yes">The site, crawled</td><td>One URL per run</td></tr>
<tr><td>SEO checks</td><td>{N_CHECKS} across every area of the audit</td><td>10 scored, 1 manual</td></tr>
<tr><td>Lab performance metrics</td><td class="no">None</td><td class="yes">Its strongest category</td></tr>
<tr><td>Core Web Vitals field data</td><td>Fetched from CrUX unless offline</td><td class="yes">Shown beside the lab run in PageSpeed Insights</td></tr>
<tr><td>Accessibility scoring</td><td class="no">No</td><td class="yes">A full category</td></tr>
<tr><td>Cross-page checks</td><td class="yes">hreflang reciprocity, canonical conflicts, click depth</td><td class="no">Not possible in one run</td></tr>
<tr><td>Structured data</td><td class="yes">Parsed, validated, and generated for you</td><td>Manual audit, weight 0</td></tr>
<tr><td>AI crawler access</td><td class="yes">Per crawler</td><td class="no">No per-crawler check. Its agentic browsing audits cover llms.txt, WebMCP and an agent manifest</td></tr>
<tr><td>Conversion and copy</td><td class="yes">Yes</td><td class="no">Not scored</td></tr>
<tr><td>Output</td><td>Ranked plan with markup to paste</td><td>Four scores out of 100, an agentic browsing fraction and a list</td></tr>
<tr><td>Report</td><td class="yes">Client-ready PDF</td><td>HTML or JSON</td></tr>
<tr><td>Runs on</td><td>Your Mac or PC, no account</td><td class="yes">Chrome, CLI, Node, or the web</td></tr>
</tbody></table></div>

<h2>The order that wastes least time</h2>
<ol>
<li><strong>Lighthouse first, on the page that matters most.</strong> It is free and it takes
ten seconds, and it catches the three faults that stop a page dead: a stray noindex, a
canonical pointing at the wrong URL, a status code that is not 200.</li>
<li><strong>Docket across the whole site.</strong> The cross-page checks, the areas Lighthouse
leaves unscored, and the ordering: findings ranked by impact against effort and sorted into
four phases, each carrying the exact markup to paste.</li>
<li><strong>Search Console once the fix is live.</strong> Field vitals move over a 28-day
window, so the answer to whether it worked is there and nowhere else.</li>
</ol>
<p>These are complementary rather than competing, and the difference fits in a sentence:
Lighthouse grades a page, Docket sequences the work on a site.</p>

<h2>When Lighthouse on its own is enough</h2>
<p>If you run a single landing page, Lighthouse plus a careful read of your own title tags
gets you most of the way, and Docket is a purchase you do not need. If your problem is
speed, Lighthouse is the better tool and this is the wrong page. Use Lighthouse to gate a
performance score in continuous integration. Docket's command line can fail a build on findings
of a chosen severity with <code>--fail-on</code>. The desktop app runs on {MACOS} or later ({MAC_HW}){' and on 64-bit Windows' if WINDOWS else ''}.
Linux runs the command line only.</p>
<p>Docket costs {PRICE_COMPACT}, runs {N_CHECKS} checks on your own machine with no account.
The app sends three anonymous counts, with no site address or audit result. The crawl and report stay on your computer. Some optional checks send page
addresses or topic words to outside services; <code>--offline</code> turns those checks off.
The privacy page lists each request. It earns that money against a free tool from Google in
one situation only: when the question has stopped being how fast is this page and become which
of forty things do I do first. If you are not at that point yet, the honest answer is to stay free:
<a href="/best/free-seo-audit-tools/">the best free SEO audit tools, and when to stop</a>.</p>
{_verified_note("lighthouse")}
{CTA}"""

    # Other comparisons: the six /vs/ pages Google had not discovered on
    # 2026-09-22. The /vs/ hub that lists them was last crawled 11 August;
    # this page is among the comparison pages crawled most recently. Kept
    # to comparison pages so no article reading list names a vendor.
    body += """
<h2>Other comparisons</h2>
<ul>
<li><a href="/vs/crawler-sh-alternative/">Docket vs crawler.sh</a></li>
<li><a href="/vs/crawlraven-alternative/">Docket vs CrawlRaven</a></li>
<li><a href="/vs/jetoctopus-alternative/">Docket vs JetOctopus</a></li>
<li><a href="/vs/profound-alternative/">Docket vs Profound</a></li>
<li><a href="/vs/seoptimer-alternative/">Docket vs SEOptimer</a></li>
<li><a href="/vs/sitechecker-alternative/">Docket vs Sitechecker</a></li>
</ul>
"""
    return render(
        cat="vs", slug="lighthouse-alternative",
        title="Docket vs Google Lighthouse: what its SEO score covers",
        desc=("Lighthouse is free, from Google, and the authority on lab Core Web Vitals. "
              "Its SEO category is ten scored checks on one URL. What a site audit sees "
              "outside it."),
        h1="Docket vs Google Lighthouse",
        crumb='<a href="/">Docket</a> / <a href="/vs/">Compare</a> / Lighthouse',
        body=body,
        faq=[
            ("Does Docket measure Core Web Vitals?",
             "Not itself. Docket measures the causes (server response time, compression and "
             "caching headers, page weight, render-blocking resources, image formats, redirect "
             "latency and layout-shift risk in the markup), and one optional check fetches the "
             "field values from Google's PageSpeed Insights API, the same Chrome UX Report data "
             "Search Console shows. LCP, INP and CLS come from real users, so confirm them in "
             "Search Console rather than in any lab tool, Docket included."),
            ("How many SEO checks does Lighthouse run?",
             "Ten scored audits, plus a manual eleventh that reminds you to validate structured "
             "data somewhere else and counts for zero. Lighthouse's own category description "
             "calls this basic search engine optimisation advice and says there are many "
             "additional factors it does not score."),
            ("Can Lighthouse audit a whole site?",
             "Not on its own. You give Lighthouse one URL and it reports on that page. Much of "
             "what breaks a site is a relationship between pages (hreflang return tags, "
             "canonical clusters, duplicate titles, click depth), and a single-page run cannot "
             "see a relationship by construction."),
            ("Should I stop running Lighthouse if I buy Docket?",
             "No, and this page would be dishonest if it said otherwise. Lighthouse is free, it "
             "is the authority on lab performance metrics, and it scores accessibility and best "
             "practices, which Docket does not. Run Lighthouse on the page you care about, "
             "Docket across the site, and Search Console after you ship."),
        ],
    )


def search_console() -> Path:
    """Docket vs Google Search Console.

    The one page on this site where the concession is not a paragraph near the
    end but the entire opening argument, because it is true: Search Console is
    free, it is Google's own data, and no audit tool substitutes for it. Anyone
    selling one as a replacement is selling a lie, and a page that soft-pedalled
    that to protect a sale would deserve to be disbelieved on everything else.

    So the structure is deliberately not the one the alternative pages use.
    There is no "what they do better / what we do better / pick one", because
    the answer is not "pick one" — it is "both, for different questions". The
    headings say so.

    Every falsifiable claim about Search Console here is quoted from a Google
    page and listed in VERIFIED["search-console"]. Two figures repeated
    everywhere in SEO writing are missing on purpose: the 16-month retention
    window and CrUX's 28-day aggregation period. Neither could be traced to a
    Google page, and this page will not launder a number it could not source
    into a claim about someone else's product.
    """
    body = f"""
<p class="lede">Search Console is free, it is Google's own data, and no audit tool replaces it, this one included. It is the single source of the queries your site actually appeared for,
the clicks and impressions they earned, Core Web Vitals measured on real visitors, and any
manual action taken against you. A product sold to you as a Search Console replacement is
lying. Verify your property first. This page is about the question Search Console does not
answer.</p>

<h2>Four things only Google can tell you</h2>

<p>None of these is derivable from a crawl, by anyone, at any price:</p>

<ul>
<li><strong>Queries, impressions, clicks and average position.</strong> Demand lives in Google's
logs. A crawler on your laptop can read every word of a page and still have no idea whether a
human ever searched for it.</li>
<li><strong>Index status, from the source.</strong> Whether Google holds this URL, which
canonical it chose over the one you declared, when it last crawled, and why a page was excluded.
A crawler can establish that a page is crawlable. Only Google can confirm it is indexed.</li>
<li><strong>Core Web Vitals from real visitors.</strong> Google's help page is explicit:
<em>The data for the Core Web Vitals report comes from the CrUX report</em>, measured on actual
Chrome users and reported at the 75th percentile.</li>
<li><strong>Manual actions and security issues.</strong> A human reviewer's decision about your
site, or a hacked-content notice. No crawl surfaces either, because neither is on your site.</li>
</ul>

<p>If your property is not verified, stop reading and go and do that. It costs nothing, it takes
five minutes, and every paid tool in this category is worse without it.</p>

<h2>The shape of what Search Console reports</h2>

<p>Search Console is a record of what has already happened to pages Google has already visited.
That sentence describes its limits more usefully than a feature list, and Google documents most
of them itself:</p>

<ul>
<li><strong>It does not crawl on demand.</strong> URL Inspection handles one URL at a time, and
Google's published quota for the API is 2,000 queries a day and 600 a minute per property. A
site of 5,000 pages cannot be inspected in a day even by script.</li>
<li><strong>A page with no impressions has no row.</strong> The Performance report is built from
appearances in search results. A page you published this morning, or one Google has never
indexed, is simply absent, and absence is usually the case you were trying to debug.</li>
<li><strong>The tables are truncated on purpose.</strong> Google's own documentation:
<em>Our tables can show a maximum of 1,000 rows, so some rows might be omitted.</em> The same
page adds that it <em>might not track some queries that are made a very small number of
times</em>, and that most reports <em>only cover a representative sample</em> of a site's URLs.
The chart totals and the table will not reconcile, and that is the intended behaviour.</li>
<li><strong>It runs behind.</strong> Google's figure, again from its own help:
<em>Normally, however, collected data should be available in 2-3 days.</em></li>
<li><strong>It reports; it does not sequence.</strong> Page indexing groups excluded URLs by
reason. It does not weigh one reason against another, or against how long a fix takes, and it
will not tell you which to spend Tuesday morning on.</li>
</ul>

<p>Every one of those is correct behaviour for a reporting surface owned by the search engine.
None of them is a defect. Together they are the outline of a different question.</p>

<h2>What Docket does to the same site</h2>

<p>Docket crawls the site as it stands right now and runs {N_CHECKS} checks (technical SEO,
copy, page speed, structured data, local visibility, AI search access and marketing conversion), then ranks every finding by impact against effort and sorts them into four phases.
Each finding states what it costs you in plain language and carries the exact markup to paste.
It writes a client-ready PDF and can score you against a named competitor. The crawl runs on
your computer: no account, results in <code>~/.docket</code>. The app sends three anonymous counts,
with no site address or audit result. The <a href="/legal/privacy/">privacy page</a> lists them and how to turn them off.</p>

<p>The difference is time-shape more than feature list. Search Console answers questions about
last week, on pages Google has met. Docket answers a question about this minute, on every page you have, including the one you published an hour ago.</p>

<h2>A division of labour, question by question</h2>

<div class="wrap-tbl"><table class="cmp">
<thead><tr><th>The question</th><th>Search Console</th><th>Docket</th></tr></thead>
<tbody>
<tr><td>Which queries did I appear for, and what did they earn?</td><td>The only source there is</td><td>Cannot know</td></tr>
<tr><td>Is this URL indexed, and which canonical did Google pick?</td><td>Google's own verdict</td><td>Reports what you declared, not what Google chose</td></tr>
<tr><td>What are my Core Web Vitals on real visitors?</td><td>CrUX field data, 75th percentile</td><td>Fetches the same CrUX values, unless offline</td></tr>
<tr><td>Do I have a manual action?</td><td>The only place it appears</td><td>Cannot know</td></tr>
<tr><td>What is wrong with the page I published an hour ago?</td><td>No data for 2-3 days</td><td>Answered now</td></tr>
<tr><td>What is wrong with a page that has never had an impression?</td><td>Not in the report</td><td>Crawled like any other page</td></tr>
<tr><td>Which of these 60 findings do I do first?</td><td>Grouped by reason</td><td>Ranked by impact against effort, in four phases</td></tr>
<tr><td>What exactly do I paste to fix it?</td><td>Explains the concept</td><td>The markup itself</td></tr>
<tr><td>How do I hand this to a client?</td><td>Export the tables</td><td>Client-ready PDF</td></tr>
<tr><td>How do I compare against a named competitor?</td><td>Not its job</td><td>Side-by-side scoring</td></tr>
<tr><td>Where does my site's data end up?</td><td>Google's servers</td><td>Your computer, in <code>~/.docket</code></td></tr>
</tbody></table></div>

<p>Deliberately no green ticks and red crosses in that table. Nine of those rows are not a
scoreboard; they are two instruments pointed at different things, and colouring Google's cells
red would be the dishonesty this page opened by refusing.</p>

<p>On cost: Search Console is free and has never been anything else. Docket is
{PRICE_COMPACT}. {BETA_NOTE}</p>

<h2>Where Docket defers: Core Web Vitals</h2>

<p><strong>Docket does not measure Core Web Vitals.</strong> Its speed checks are causes (render-blocking resources, uncompressed images, page weight), and a cause is not a metric. The
metrics come from real visitors, which is why Search Console builds that report from CrUX rather
than from a lab run. Docket has one optional check that fetches the same CrUX values through the
PageSpeed Insights API; it is one of {CONNECTORS_WORD} optional checks that reach off your machine, and
<code>--offline</code> turns it off. Google's copy is the authority and the property-wide
grouping is in Search Console, so confirm a speed fix there. For the lab side of the same
problem, see <a href="/vs/lighthouse-alternative/">Docket vs Lighthouse</a>.</p>

<p>There is a hole underneath both tools, and small sites fall into it. A URL needs enough real
Chrome traffic before CrUX will report on it at all, and Google does not publish how much:
<em>An exact number is not disclosed.</em> Search Console's own help adds that
<em>A URL group without threshold data for both LCP and CLS will not be on the report.</em> On a
low-traffic site neither tool hands you a field number. Fix the causes, and read the
origin-level figure instead of a per-URL one.</p>

<h2>How the two fit into a week</h2>

<ol>
<li>Verify the property in Search Console. Nothing substitutes for this step.</li>
<li>Read Page indexing and Performance for what Google already thinks: which pages earn
impressions, which are excluded, and for what stated reason.</li>
<li>Crawl with Docket for what is true today, including every page Search Console has nothing
to say about.</li>
<li>Work the ranked plan, re-crawling after each change. That costs nothing locally.</li>
<li>Come back to Search Console a few days later for the verdict, because that is the only
place a verdict exists.</li>
</ol>

<p>The recommendation is boring, which is usually the sign it is honest: keep the free one
forever, and add the crawler when the question is what to change rather than what happened.</p>
{_verified_note(
    "search-console",
    closing="Google changes its products and its documentation; if something here "
            'has gone out of date, <a href="/about/">tell us</a> and it will be '
            "corrected. Nothing on this page argues that you should use Docket "
            "instead of Search Console, because you should not.",
)}
{CTA}"""

    # Other comparisons: the six /vs/ pages Google had not discovered on
    # 2026-09-22. The /vs/ hub that lists them was last crawled 11 August;
    # this page is among the comparison pages crawled most recently. Kept
    # to comparison pages so no article reading list names a vendor.
    body += """
<h2>Other comparisons</h2>
<ul>
<li><a href="/vs/crawler-sh-alternative/">Docket vs crawler.sh</a></li>
<li><a href="/vs/crawlraven-alternative/">Docket vs CrawlRaven</a></li>
<li><a href="/vs/jetoctopus-alternative/">Docket vs JetOctopus</a></li>
<li><a href="/vs/profound-alternative/">Docket vs Profound</a></li>
<li><a href="/vs/seoptimer-alternative/">Docket vs SEOptimer</a></li>
<li><a href="/vs/sitechecker-alternative/">Docket vs Sitechecker</a></li>
</ul>
"""
    return render(
        cat="vs", slug="google-search-console",
        title="Docket vs Google Search Console: what each answers",
        desc=("Search Console is free, it is Google's own data, and nothing replaces it. What "
              "it cannot tell you, and where an audit on your own computer answers instead."),
        h1="Docket vs Google Search Console",
        crumb='<a href="/">Docket</a> / <a href="/vs/">Compare</a> / Search Console',
        published="2026-08-10",
        body=body,
        faq=[
            ("Can Docket replace Google Search Console?",
             "No, and nothing can. Search Console is the only source of your real queries, "
             "impressions, clicks, Core Web Vitals measured on real visitors, and manual action "
             "notices. It is free and it is Google's own data. Docket audits the site itself "
             "and assumes you already have Search Console set up."),
            ("Why would I need an audit tool if Search Console is free?",
             "Because Search Console reports on pages Google has already crawled, and says "
             "nothing about a page with no impressions yet. It also groups its findings by "
             "reason rather than ranking them. Docket crawls the site as it stands today and "
             "returns an ordered fix plan with the markup to paste."),
            ("Does Docket measure Core Web Vitals?",
             "No. Docket checks the causes of poor performance and can fetch the same CrUX "
             "field values Search Console shows, through the PageSpeed Insights API, as one of "
             f"{CONNECTORS_WORD} optional checks that --offline turns off. The authoritative view is Google's "
             "and it is in Search Console. Confirm a speed fix there, not in Docket."),
            ("Is the URL Inspection tool enough to audit a site?",
             "Not at any scale. It inspects one URL at a time, and Google documents the API "
             "quota as 2,000 queries a day and 600 a minute per property. A site larger than "
             "that cannot be inspected in a day, and inspection reports indexing status rather "
             "than telling you what to change."),
        ],
    )


def scrutiny() -> Path:
    """The closest positional competitor, and the site never named it.

    A paid macOS desktop SEO app sold for a one-time fee is the shape a buyer
    comparing Docket will land on, and until 2026-08-15 this site compared
    itself only to crawlers and platforms. Leaving out the nearest neighbour is
    the kind of omission a reader notices on their own and reads as evasion.

    Every fact below is from the vendor's own `SoftwareApplication` JSON-LD,
    read 2026-08-15 — machine-readable, so there is nothing to misread. It cost
    less than Docket until 2026-11-02, when Docket went to $59; its published
    feature list contains three things Docket does not do at all. Both are said
    plainly, and the assert below stops the build if the price order flips again.
    """
    assert LATER_PRICE < int(COMPETITORS["scrutiny"]["annual_low"]), "Scrutiny costs less than Docket again: rewrite this page"
    body = f"""
<p>Scrutiny is a macOS desktop SEO tool sold for a one-time fee, which makes it
the closest thing to Docket on the market: no account, no subscription, runs on
your own computer. If you are choosing between the two, the honest summary is that
<strong>Docket costs less, and Scrutiny does several things Docket does not do
at all</strong>.</p>

<h2>What Scrutiny does that Docket does not</h2>
<p>Its published feature list names <strong>link checking, HTML validation, XML
sitemap generation, SEO, spell checking and site search</strong>. Three of those
Docket has no answer to:</p>
<ul>
<li><strong>Spell checking.</strong> Docket does not check spelling, in any
language. If proofreading a site is the job in front of you, Docket is the wrong
purchase.</li>
<li><strong>HTML validation.</strong> Docket checks specific structural things (headings, canonicals, structured data) and does not validate markup against the
specification.</li>
<li><strong>Site search.</strong> Docket has no equivalent of searching your own
crawled content.</li>
</ul>
<p>On price, Docket is the cheaper of the two: {PRICE_COMPACT} against Scrutiny's
{price('scrutiny')}, both paid once.</p>

<h2>What Docket does that Scrutiny's feature list does not name</h2>
<p>The list above names SEO as a single item. What Docket adds is not "more SEO
checks" but categories that list does not cover: whether your landing pages give
a visitor a reason and a route to act, whether your brand is presented
consistently, whether a local business has the markup local results need, and whether AI crawlers can reach you at all.</p>
<p>That last one is the axis Docket is actually built on, and it is worth being
precise about what it means. Reading <code>robots.txt</code> tells you what a
site <em>permits</em>. Docket asks the server, as each crawler, with that
crawler's documented user-agent, and compares the answer. The two disagree more
often than anyone expects: a CDN or WAF rule refuses a crawler your
<code>robots.txt</code> explicitly allows, and nothing in the file will ever tell
you.</p>

<h2>Which one to pick</h2>
<p><strong>Choose Scrutiny</strong> if you want link checking and spell checking
on a Mac for less money, or if validation and site search are what you actually
need. It has been developed for years, it is macOS-native, and for those jobs
Docket has nothing to offer you.</p>
<p><strong>Choose Docket</strong> if you want a ranked fix plan rather than a
dataset, a client-ready report, and the AI-visibility and conversion checks that
Scrutiny's feature list does not name.</p>
<p>Both run on your own machine and neither wants a subscription, which is more
than most of this market can say. If buying once is the part that matters,
<a href="/vs/crawlraven-alternative/">CrawlRaven</a> is the other name worth knowing about. It sells mainly by
the month now, with a lifetime plan beside it, and its pricing page includes a technical audit within a monthly
page allowance.</p>
{_verified_note("scrutiny")}
{CTA}"""

    return render(
        cat="vs", slug="scrutiny-alternative",
        title="Docket vs Scrutiny: two paid Mac SEO tools compared",
        desc=(
            ("Scrutiny does spell checking, HTML validation and site search, which Docket does not. "
             "Docket costs less. What it adds, and when to buy theirs.")
            if SITE_BRAND == "checkengine"
            else ("Scrutiny does spell checking, HTML validation and site search, which "
                  "Docket does not; Docket costs less. What Docket adds, and when to buy "
                  "theirs instead.")
        ),
        h1="Docket vs Scrutiny",
        crumb='<a href="/">Docket</a> / <a href="/vs/">Compare</a> / Scrutiny',
        body=body,
        faq=[
            ("Is Docket a Scrutiny alternative?",
             "Partly. Both are one-time purchases that run locally on a Mac (Docket also runs on Windows). "
             "Scrutiny does spell checking, HTML validation and site search, none of "
             "which Docket does. Docket adds AI-crawler access, conversion and "
             "local-business checks, and produces a ranked fix plan."),
            ("Which is cheaper?",
             f"Docket, at {PRICE_COMPACT} against Scrutiny's {price('scrutiny')}. Both "
             "are one-time purchases rather than subscriptions."),
            ("Does Scrutiny run on Windows?",
             "No. Its product page says there are no plans for Windows. "
             + ("Docket's desktop app has an installer for 64-bit Windows as well as the Mac app, and its "
                "audit engine also ships as a Linux command-line build." if WINDOWS else
                "Docket's desktop app is macOS-only too, though its audit engine also ships as a "
                "Linux command-line build.")),
        ],
    )


def seoptimer() -> Path:
    """The cheapest subscription a buyer comparing Docket will find, and it wins on one thing.

    SEOptimer starts at a third of what Docket costs per month and is built for
    selling audits: white-label PDF reports and, on its top plan, a lead
    generation tool. Since 1.3.147 Docket puts an agency's name and logo on its
    reports, but has no lead generation tool, and the page says so before
    anything else. (2026-11-09: the earlier "custom report domain", "report
    templates" and "audit widget" details were NOT on the vendor's page when it
    was read by hand that day, so they were cut.)

    The honest comparison is not features, it is the meter. Every plan buys a
    fixed number of crawls per month; Docket's crawl limit is the machine. Read
    live 2026-09-16 from the vendor's own pricing page — the prices were
    unchanged since the CSV's 2026-08-10 check, but the crawl quotas had never
    been recorded here and they are the thing that actually decides this.

    ⚠️ NO CLAIM THAT DOCKET REPLACES IT, and no claim about scorecard quality:
    nothing here has been measured against their output. The comparison is
    confined to what each vendor publishes about its own product.
    """
    body = f"""
<p class="lede"><strong>The short answer:</strong> the SEOptimer alternative that fits depends on what you use SEOptimer
for. It is a cloud audit tool sold by the month ({price('seoptimer')}), with white-label PDF reports, a lead generation
tool on its top plan, and a fixed number of crawls on every plan. Docket is an audit you run on your own
computer, bought once for {PRICE_COMPACT}, with no crawl meter, a free version, and reports that can carry your name and logo.
If you want a lead generation tool or a monthly cloud service built for selling audits, stay with SEOptimer. If you want
to hand clients a report under your own name, or re-run audits as often as you like, pick Docket.</p>

<h2>At a glance</h2>
<p class="table-note">Read from SEOptimer's pricing page on {CHECKED_HUMAN["seoptimer"]}. Each plan
offers a {_SEOPT_TRIAL_DAYS} day free trial.</p>
<div class="wrap-tbl"><table class="cmp">
<thead><tr><th>Plan</th><th>Monthly price</th><th>Crawls a month</th><th>What the plan names</th></tr></thead>
<tbody>
{"".join(f"<tr><td>SEOptimer {n}</td><td>${p}</td><td>{c}</td><td>{f}</td></tr>" for n, p, c, f in _SEOPT_PLANS)}
<tr><td class="yes">Docket</td><td class="yes">{PRICE_COMPACT}</td><td class="yes">Unmetered</td>
    <td>Reports with your name and logo. No lead generation tool</td></tr>
</tbody></table></div>
{_top_cta("vs-seoptimer-top")}

<h2>What SEOptimer does that Docket does not</h2>

<ul>
<li><strong>Lead generation.</strong> Its top plan, Max, names a lead generation tool. That is a
marketing product. Docket is a tool you run, and has nothing like it.</li>
</ul>

<p>That is a real concession. Selling audits is a real business and SEOptimer is built for it;
Docket is a tool you run on your own computer.</p>

<h2>The difference that actually decides it: the meter</h2>

<p>Every SEOptimer plan buys a fixed number of crawls per month. Starter is four crawls for one
website. Pro is ten. Max is fifty. That is the shape of every subscription audit tool, and it
changes how you work: a crawl becomes something you spend rather than something you run.</p>

<p>Docket does not meter anything. There is no page allowance, no crawl count and no project
limit, because there is no server keeping score. The audit runs on your computer, and
<code>-n 0</code> removes the page-count limit. A crawl still stops at its time limit of
{F.limits()['wall_clock_minutes']} minutes by default or {F.limits()['everything_hours']} hours
with Everything, its depth limit of {F.crawl_depth()} by default, or when it runs out of links.
Re-running after every fix costs you nothing but
the time, which matters more than it sounds: the natural way to use an audit is to fix
something and immediately check whether you fixed it.</p>

<p>The pricing follows from that. SEOptimer bills monthly and keeps billing.
Docket is {PRICE_COMPACT}. A year on SEOptimer's entry plan costs
${F.rival_annual_low('seoptimer'):,} at its listed monthly rate, more than Docket's one price.
A year is a long time in software and a subscription
you can cancel is a real advantage if you only need one audit.</p>

<h2>What Docket adds</h2>

<p>Docket runs {N_CHECKS} checks across thirteen areas, and four of those areas are not technical
SEO at all: conversion, brand consistency, AI search visibility and campaign tracking. The AI
area checks robots.txt rules for {F.ai_agents()} AI crawlers. A separate check requests your
homepage as {len(F.probes()['ai'])} AI crawlers plus {F.probes()['search']} to find server refusals
the file cannot show. And every finding lands in a ranked plan rather than a categorised list. <a href="/learn/priority-model/">The formula is written out</a> if you want to check the
ordering yourself.</p>

{_measured("<p>SEOptimer's Starter plan buys four crawls a month for one site. This is a single Docket run, on a real site, with the figures the engine reported.</p>", "areas")}

<h2>When to pick SEOptimer instead of Docket</h2>

<ul>
<li><strong>You want a lead generation tool.</strong> SEOptimer's Max plan names one. Docket has
nothing like it.</li>
<li><strong>You only need one audit.</strong> A subscription you can cancel is better value than a
purchase.</li>
{WRONG_COMPUTER}
<li><strong>You audit your own sites and want unlimited re-runs while you fix things.</strong> That is
Docket, for {PRICE_COMPACT}.</li>
</ul>

<p>They are not really the same product. One is a reporting and lead product sold to agencies;
the other is an instrument you point at a site. If the metering is what puts you off,
<a href="/vs/crawler-sh-alternative/">crawler.sh</a> is worth a look for the same reason and
against the same limit: it caps pages per session rather than crawls per month.</p>

<h2>Other SEOptimer alternatives, by what you need</h2>
<ul>
<li><strong>A free one.</strong> Docket's free version shows your score, how many problems each area has and the top
problem in full, on any site, with no key. <a href="/best/free-seo-audit-tools/">The free SEO audit tools we compared</a>
are the other place to start.</li>
<li><strong>A team.</strong> That is what a platform subscription bundles. Our
<a href="/vs/semrush-site-audit-alternative/">Semrush comparison</a> lists seats among what it buys. Docket has no
team accounts, though its reports can carry your name and logo.</li>
<li><strong>Visual reports an agency can present.</strong> <a href="/vs/sitebulb-alternative/">Sitebulb</a> turns crawl
data into reports of that kind.</li>
<li><strong>A desktop crawler for raw data.</strong> <a href="/vs/screaming-frog-alternative/">Screaming Frog</a> gives
you the crawl data and leaves the reading to you.</li>
<li><strong>Another cloud tool that bills by the month.</strong> <a href="/vs/sitechecker-alternative/">Sitechecker</a>
is the one we compare, and that page says its plans advertise unlimited recrawls.</li>
</ul>

{_verified_note("seoptimer")}
{CTA}"""

    return render(
        cat="vs", slug="seoptimer-alternative",
        modified="2026-11-05",  # report branding (1.3.147): Docket's reports can carry your name and logo
        title="SEOptimer alternative for Mac with no crawl limit",
        desc=(f"{price_sentence()} Compare SEOptimer's monthly crawls with Docket's unlimited re-runs."),
        h1="Docket vs SEOptimer",
        crumb='<a href="/">Docket</a> / <a href="/vs/">Compare</a> / SEOptimer',
        body=body,
        faq=[
            ("What is a good SEOptimer alternative for Mac?",
             "Docket, if you audit your own sites and want unlimited re-runs: it runs on your computer, "
             "is bought once and has no crawl allowance, and its reports can carry your name and logo. "
             "It is not the one to pick if you need a lead generation tool, which SEOptimer's "
             "Max plan names and Docket does not."),
            ("Does SEOptimer have a free trial?",
             f"Its pricing page offers a {_SEOPT_TRIAL_DAYS} day free trial on each plan. Docket's free version "
             f"shows your score, how many problems each area has and the top problem in full, with no key and no time "
             f"limit. The full report is a one-time purchase with a {REFUND_DAYS}-day refund."),
            ("How much does SEOptimer cost?",
             f"Its pricing page lists three plans, Starter, Pro and Max, at {price('seoptimer')}. "
             f"Docket is {PRICE_COMPACT}."),
            ("Is Docket an SEOptimer alternative?",
             "For auditing sites and handing clients a report under your own name and logo, yes. "
             "If you want a lead generation tool, no: SEOptimer's Max plan names one and Docket "
             "has nothing like it."),
            ("Is there a free SEOptimer alternative?",
             "Docket's free version shows your score, how many problems each area has and the top "
             "problem in full, on any site, with no key and no time limit. It is not the full "
             f"report, which is {PRICE_COMPACT}. Our guide to free SEO audit tools compares the "
             "other free options we looked at."),
            ("Can I get white-label reports from a SEOptimer alternative?",
             "Yes. In the paid version, Docket's PDF and HTML reports can carry your agency's name "
             "and logo in place of Docket's (Reports, then Report branding), and its CSV and JSON "
             "exports carry no branding at all. SEOptimer also names white-label PDF reporting "
             "on its Pro and Max plans."),
            ("Which is cheaper, Docket or SEOptimer?",
             f"SEOptimer's Starter plan, for its first {_months_past_docket(_SEOPT_LO) - 1} months: "
             f"${_SEOPT_LO} a month against Docket's {PRICE_COMPACT}. From month "
             f"{_months_past_docket(_SEOPT_LO)} it has cost more. Docket has no recurring fee, "
             "and every 1.x update is included, "
             "but a subscription you can cancel is genuinely better value if you only need one audit."),
            ("How many crawls does SEOptimer allow?",
             "Its published plans buy four crawls a month for one website on Starter, ten on Pro "
             "and fifty on Max. Docket does not meter crawls at all: the audit "
             "runs on your own computer and -n 0 removes the page-count limit. A crawl still stops at "
             f"its time limit of {F.limits()['wall_clock_minutes']} minutes by default or "
             f"{F.limits()['everything_hours']} hours with Everything, its depth limit of "
             f"{F.crawl_depth()} by default, or when it runs out of links. Re-running after each fix costs nothing."),
            ("Does SEOptimer check AI crawler access?",
             "This page does not say, because it was not measured. Only what the vendor "
             f"publishes was read. Docket checks robots.txt rules for {F.ai_agents()} AI crawlers. "
             f"A separate check requests your homepage as {len(F.probes()['ai'])} AI crawlers "
             f"plus {F.probes()['search']} to find server refusals the file cannot show."),
        ],
    )


def sitechecker() -> Path:
    """The rival that answers the AI question Docket deliberately does not.

    Sitechecker tracks whether a brand is MENTIONED in ChatGPT, Gemini, Google
    AI Mode, Perplexity and Copilot. Docket checks whether those crawlers are
    ALLOWED IN. Those are different questions, and this site has spent a lot of
    words insisting on that distinction in its own favour — every AI figure we
    publish is about access, never extraction. The same distinction cuts the
    other way here, and the page says so rather than blurring it.

    ⚠️ THE CRAWL-METER ARGUMENT DOES NOT APPLY HERE IN THE SAME FORM. Its
    plans advertise unlimited recrawls, so the point made on
    /vs/seoptimer-alternative/ (a count of crawls a month) would be false about
    this vendor. But the plan table also caps the total pages crawled across an
    account (10,000, 50,000 and 200,000 on the first three plans), which this
    page said it did not publish until the 2026-10-19 re-read found the row.
    The rendered table fills the Basic and Standard cells from the page's own
    styles, so a plain fetch of the HTML shows them blank. Each rival gets the
    comparison that is true of it.

    Read live 2026-10-19 from the vendor's own plans page, rendered in a
    browser. Nothing about output quality is claimed in either direction: it
    has not been measured.
    """
    body = f"""
<p>Sitechecker is a cloud SEO platform from {price('sitechecker')}. It overlaps with Docket on
crawling and very little else, and the honest headline is that <strong>it answers questions
Docket refuses to answer at all</strong>.</p>

<h2>What Sitechecker does that Docket does not</h2>

<ul>
<li><strong>Rank tracking.</strong> Its rank tracker keeps SERP history for the keywords you
track. Docket does not track rankings, and says so on its own home page: that needs a crawled
index of the whole web, which is bought rather than built.</li>
<li><strong>AI brand visibility.</strong> Its AI visibility tracker covers five models (ChatGPT, Gemini, Google AI Mode, Perplexity and Copilot) and reports brand visibility,
mentions and citations. <strong>This is the one worth reading twice</strong>, because it looks
like something Docket does and is not.</li>
<li><strong>Search Console and Analytics dashboards</strong>, and website monitoring that
tracks changes over time from the cloud. Docket re-audits saved sites on a schedule while the
app is open. It does not track rankings.</li>
</ul>

<h2>The AI distinction, stated against our own interest</h2>

<p>Docket checks AI <strong>access</strong>: robots.txt rules for {F.ai_agents()} named AI crawlers.
A separate check requests your homepage as {len(F.probes()['ai'])} AI crawlers plus {F.probes()['search']}
from your own computer. A firewall can treat the real, verified crawler differently, so your
server's own logs settle whether it was allowed through.</p>

<p>Sitechecker is answering a different question: whether an assistant currently mentions you.
That is a measurement of an outcome, and Docket does not make it. Every AI figure this site
publishes is about access rather than about being quoted, and we have been careful to say so everywhere else, so it would be dishonest to imply the two overlap here. <strong>If what you
want to know is whether ChatGPT names your brand today, Docket cannot tell you and Sitechecker
is built to.</strong></p>

<p>The two are complements more than alternatives. Access is a precondition: a crawler that
cannot read your pages will not cite them. Docket checks the rules and homepage access from
your computer; your server's logs show what happened to the real crawler. Whether
citation then happens is a question about the model, and needs a tool that watches the model.
<a href="/vs/profound-alternative/">Profound</a> does only that half, at enterprise pricing, if
tracking mentions is the whole of what you need. What Docket checks on the access side is
<a href="/learn/ai-crawler-directives/">written out crawler by crawler</a>.</p>

<h2>What Docket adds</h2>

<p>{N_CHECKS} checks across thirteen areas, including conversion and brand consistency, which
do not appear in Sitechecker's listed core tools. Findings arrive as a ranked plan with the fix
written out rather than as a dashboard. <a href="/learn/priority-model/">The ordering formula is published</a>. It runs on your computer
with no account, and the crawl and the report stay there. And it is {PRICE_COMPACT} rather than
a monthly bill.</p>

<p>That last one is the plainest difference. A year on Sitechecker's entry plan costs several
times what Docket costs in total, and the second year costs the same again. Set against that:
Sitechecker monitors from its cloud and tracks rankings. Docket re-audits saved sites on a
schedule while the app is open, but does not track rankings.</p>

<h2>Which to buy</h2>

<ul>
<li><strong>Buy Sitechecker</strong> if you need rank tracking, ongoing monitoring, or to know
whether AI assistants are mentioning your brand.</li>
<li><strong>Buy Docket</strong> if you want a deep one-off audit of what is wrong and in what
order, including conversion and brand, without an account or a recurring bill.</li>
</ul>

<p>One contrast worth carrying away: Sitechecker does not count how often you crawl, and much of this
market does. Its plans advertise unlimited recrawls, and cap the pages tracked across an account at
10,000, 50,000 and 200,000 on the first three plans. <a href="/vs/seoptimer-alternative/">SEOptimer</a>
sells four, ten or fifty crawls a month depending on the tier, which changes how you work far more than
any feature list does.
Nothing here compares the quality of the two crawlers' output, because that has not been
measured. Both vendors' published feature lists are what this page is built from.</p>

{_verified_note("sitechecker")}
{CTA}"""

    return render(
        cat="vs", slug="sitechecker-alternative",
        title="Docket vs Sitechecker: access or mentions?",
        desc=(
            ("Sitechecker tracks rankings and whether AI assistants mention you. Docket checks "
             "whether those crawlers can reach you. Different questions, said plainly.")
            if SITE_BRAND == "checkengine"
            else ("Sitechecker tracks rankings and whether AI assistants mention you; Docket "
                  "checks whether those crawlers can reach you at all. Different questions, "
                  "said plainly.")
        ),
        h1="Docket vs Sitechecker",
        crumb='<a href="/">Docket</a> / <a href="/vs/">Compare</a> / Sitechecker',
        body=body,
        faq=[
            ("Is Docket a Sitechecker alternative?",
             "Only partly, and the gap matters. Sitechecker tracks keyword rankings and "
             "whether five AI models mention your brand. Docket does neither. Docket audits "
             "what is wrong with your site and ranks the fixes, and checks whether AI "
             "crawlers are allowed to reach you in the first place."),
            ("Does Docket track AI visibility like Sitechecker?",
             "No, and the difference is worth being precise about. Sitechecker measures "
             "whether assistants mention you, which is an outcome. Docket checks robots.txt "
             f"rules for {F.ai_agents()} AI crawlers. A separate check requests your homepage as "
             f"{len(F.probes()['ai'])} AI crawlers plus {F.probes()['search']}. Access is a "
             "precondition for citation, not the same thing as it."),
            ("Which is cheaper?",
             f"Docket costs less even for a month at the listed prices: {PRICE_COMPACT}; "
             f"Sitechecker starts at {price('sitechecker')} and keeps billing. Choose Sitechecker "
             "for its cloud platform tools, including monitoring and rank history. Docket "
             "re-audits saved sites on a schedule while the app is open, but does not track rankings."),
            ("Does Sitechecker limit how much you can crawl?",
             "Not how often. Its plans advertise unlimited recrawls, unlike SEOptimer, which "
             "sells four, ten or fifty crawls a month. They do cap the total pages crawled "
             "across an account: 10,000 on Basic, 50,000 on Standard and 200,000 on Premium, "
             "unlimited on Enterprise. The other limits it publishes are on websites, tracked "
             "keywords and AI prompts. Docket has no limits of any of those kinds, because "
             "there is no account."),
        ],
    )


def profound() -> Path:
    """An answer-engine tracker with no crawler, sold by demo. Barely the same category.

    Profound measures whether a brand appears in AI answers across up to nine
    answer engines. Docket measures whether those crawlers can reach the site at
    all. The Sitechecker page already makes an access-versus-mentions argument,
    so this page deliberately makes a DIFFERENT one: Profound's published
    platform list contains no crawler and no technical audit, and its plan for
    brands has no price on the page: the two tiers are a free trial and "get a
    demo".

    ⚠️ NO PLAN PRICE IS QUOTED, because none is published. This row carried
    "$99-$399/mo billed yearly" from 2026-08-10 and its own source no longer
    supports it; the figure was removed from `competitors.csv` rather than
    printed here. The re-read of 2026-10-19 found that the AGENCIES view does
    print two add-on amounts ($399 a month for a full client workspace, $199
    for five trial workspaces), so "publishes no price" would now be false as
    a flat sentence; the page says it for brands and names the agencies
    amounts. A page arguing that Docket's price is on the page cannot invent a
    plan price for the company it is comparing against.

    ⚠️ NOTHING IS CLAIMED ABOUT WHAT PROFOUND CANNOT DO — only about what its
    own pricing page lists. "No crawler appears in the published platform list"
    is a statement about the list.
    """
    body = f"""
<p>Profound tracks whether AI assistants mention your brand. Docket audits whether those
assistants' crawlers can read your site in the first place. Those sound adjacent and they are
not the same purchase at all. The clearest way to see it is that
<strong>Profound does not publish a price for its brand plans</strong>.</p>

<h2>Two tiers, neither of them a price</h2>

<p>Its pricing page lists a free <strong>Trial</strong> (50 prompts a day for 7 days, against ChatGPT, Gemini and Google AI Overviews, in one language and one region) and <strong>Enterprise</strong>, at custom
pricing, reached by booking a demo. Enterprise tracks up to nine answer engines and lists
SSO/SAML and SOC2 compliance beside dedicated support.</p>

<p>Switch the same page to its agencies view and it does print some money: full client workspaces
are an add-on at $399 a month each, and five trial workspaces are $199 a month. The Agency Growth
plan they attach to has no price beside it, and Agency Enterprise is custom, so there is still no
plan price to set against anything.</p>

<p>That is an enterprise sales motion, and the compliance line tells you who it is for. It is
not a criticism: tracking nine answer engines across languages and regions is genuinely
expensive to operate, and companies that need it have procurement departments. But it means the
comparison with Docket is not really about features. One is a platform you are onboarded onto.
The other is a {PRICE_COMPACT} download with the price on the page.</p>

<h2>What Profound does that Docket does not</h2>

<p>Its published platform names Monitor, Answer Engine Insights, Prompt Volumes, Shopping, Agent
Analytics, AI Marketer, Agents and Context Manager. Answer Engine Insights analyses how your
brand and your competitors appear in AI platforms. <strong>Docket does none of this.</strong> It
cannot tell you whether ChatGPT named you this week, how often, or beside whom.</p>

<h2>What Docket does that Profound's platform list does not name</h2>

<p>No site crawler and no technical audit appears in that list. Docket is entirely that:
{N_CHECKS} checks across thirteen areas, run against your own pages.</p>

<p>The two meet at one specific point, and it is worth being precise about it. Docket checks
robots.txt rules for {F.ai_agents()} AI crawlers. A separate check requests your homepage as
{len(F.probes()['ai'])} AI crawlers plus {F.probes()['search']} from your own computer.
That is the question underneath a visibility report: if a tracker tells you that you
are not being cited, one possible reason is that the crawler was never allowed to read the page.
A firewall can treat the real, verified crawler differently, so your server's own logs settle
whether it was allowed through. Docket cannot tell you whether citation then happens. The
robots.txt half of the question, for one address and without installing anything, is the free
<a href="/tools/ai-crawler-checker/">AI crawler checker</a>; it cannot see a server refusing a crawler,
which is the part Docket adds.</p>

<h2>Which to buy</h2>

<ul>
<li><strong>Book the Profound demo</strong> if measuring your presence in AI answers is a reporting obligation: you need it across engines, languages and regions, and someone is asking
for the numbers.</li>
<li><strong>Buy Docket</strong> if you want to know what is wrong with your site and in what
order, including whether AI crawlers can reach it, without an account or a sales call.</li>
</ul>

<p>Plenty of companies would sensibly do both, and they are not substitutes in either direction.
If mention-tracking is what you want but an enterprise contract is not,
<a href="/vs/sitechecker-alternative/">Sitechecker</a> does it across five models inside an
ordinary SEO subscription. The access question Docket answers instead is
<a href="/learn/ai-crawler-directives/">set out crawler by crawler</a>. Nothing here compares the
accuracy of Profound's tracking, which we have not measured and have no way to measure from
outside.</p>

{_verified_note("profound")}
{CTA}"""

    return render(
        cat="vs", slug="profound-alternative",
        title=(
            ("Profound vs Docket: mentions and AI crawler access")
            if SITE_BRAND == "checkengine"
            else ("Profound alternative? Docket checks AI access, not mentions")
        ),
        desc=(f"{price_sentence()} Profound tracks brand mentions. Docket checks AI crawler access."),
        h1="Docket vs Profound",
        crumb='<a href="/">Docket</a> / <a href="/vs/">Compare</a> / Profound',
        body=body,
        faq=[
            ("Is Docket a Profound alternative?",
             "No, and it would be misleading to say otherwise. Profound reports whether AI "
             "assistants mention your brand across answer engines. Docket audits your site "
             "and checks whether those crawlers are permitted to read it. Neither replaces "
             "the other."),
            ("How much does Profound cost?",
             "Its pricing page for brands publishes no figure. It lists a free trial (50 "
             "prompts a day for 7 days, across ChatGPT, Gemini and Google AI Overviews) and "
             "Enterprise at custom pricing reached through a demo. Only its agencies view "
             "prints amounts: $399 a month for a full client workspace and $199 a month for "
             "five trial workspaces, with no price for the Agency Growth plan itself. "
             "Docket is a one-time purchase with the price on the page, which is the "
             "starkest difference between them."),
            ("Can Docket tell me if ChatGPT mentions my brand?",
             "No. Docket measures access, not mentions: whether each AI crawler is allowed "
             "in, and whether your server agrees with your robots.txt. If a tracker says you "
             "are not being cited, Docket can tell you whether a blocked crawler is one "
             "reason. It cannot tell you whether citation happens."),
        ],
    )


def jetoctopus() -> Path:
    """The one that reads your server logs, which Docket cannot do at all.

    JetOctopus is an enterprise log-analysis and crawl platform. Its published
    product list leads with a Log Analyzer, and that is a data source Docket has
    no access to: Docket audits what a site serves to a crawler, and logs record
    what crawlers actually did. On a large site the logs are the more valuable
    of the two and there is no argument otherwise.

    So the concession is the whole first half of this page, and the comparison
    that follows is about SCALE rather than quality. Their plans are metered in
    millions of crawled URLs and millions of log lines; Docket runs on a Mac.

    ⚠️ MCP IS NOT A DIFFERENTIATOR HERE. Docket ships an MCP server and so does
    JetOctopus — their product list names one. Claiming it would have been the
    easy sentence and it would have been false.

    ⚠️ The cheaper of the two ways to buy a year is quoted (annual, not
    quarterly), per the rule in `facts._annual`: it is their real price and the
    less flattering number for us.
    """
    body = f"""
<p>JetOctopus is an enterprise technical-SEO platform built around server log files. Docket is a
{PRICE_COMPACT} desktop app for Mac and Windows. Before any comparison is worth making, the important part:
<strong>JetOctopus reads your server logs and Docket cannot</strong>, and on a large site that is
the most valuable technical-SEO data there is.</p>

<h2>What log analysis gives you that no crawler can</h2>

<p>A crawler, Docket included, tells you what your site serves when something asks. Logs tell
you what Googlebot actually did: which pages it fetched, how often, which it ignored for months,
where it spent a crawl budget you did not know you were spending. Those are different questions,
and the second cannot be inferred from the first. JetOctopus's product list leads with its Log
Analyzer for that reason, and adds a JavaScript crawler, GSC and GA4 integration, position
tracking, alerts and its own AI search visibility product.</p>

<p>If crawl budget on a large catalogue is your problem, a tool that cannot see your logs is not
the answer, and this page is not going to pretend otherwise.</p>

<h2>Where the comparison actually sits: scale</h2>

<p>Their In-House plans are metered in crawled URLs and log lines a month: 500,000 URLs and two
million log lines on Growth, two million and eight million on Pro, five million and twenty-five
million on Ultra, with an Unlimited tier quoted only as "Let's talk". Projects, seats and
simultaneous crawls are unlimited on every tier. That is a platform for sites with hundreds of
thousands to millions of pages and a team around them.</p>

<p>Their published rates: {price('jetoctopus')}. That works out at
{F.rival_annual_low('jetoctopus'):,} US dollars for a year on the entry plan at the cheaper of the
two rates, and {F.rival_annual_high('jetoctopus'):,} on the top priced plan.
Docket is {PRICE_COMPACT}. Setting those numbers
beside each other is close to meaningless, because they are not sold to the same buyer, but it does tell you which question you are asking. If a platform fee of several thousand dollars a year is a normal
line item, JetOctopus is in your category and Docket is not.</p>

<h2>What Docket does</h2>

<p>{N_CHECKS} checks across thirteen areas, on your own computer, with no account. <code>-n 0</code>
removes the page-count limit. A crawl still stops at its time limit of {F.limits()['wall_clock_minutes']}
minutes by default or {F.limits()['everything_hours']} hours with Everything, its depth limit of
{F.crawl_depth()} by default, or when it runs out of links. Re-running after each fix costs nothing because
nothing is metered. Four of those areas are not technical SEO at all: conversion, brand
consistency, AI search visibility and campaign tracking. Findings arrive as a ranked plan with
the fix written out, and <a href="/learn/priority-model/">the ordering formula is published</a>.</p>

<p>One thing worth not claiming: an MCP integration. Docket ships one so that an AI assistant can
run an audit, and JetOctopus's product list names one too. It is not a difference between them.</p>

<h2>Which to buy</h2>

<ul>
<li><strong>Buy JetOctopus</strong> if you have server logs worth analysing, a site measured in
hundreds of thousands of pages or more, and a budget that treats SEO tooling as infrastructure.</li>
<li><strong>Buy Docket</strong> if you want a deep audit of a site you can crawl from your own
machine, ranked into an order, once, for a fixed price.</li>
</ul>

<p>If scale is your problem but server logs are not,
<a href="/vs/screaming-frog-alternative/">Screaming Frog</a> is the other tool built for very
large crawls and costs a fraction of this. Nothing here compares crawl accuracy or the quality of
either tool's findings, which has not been measured. The facts above are what each vendor
publishes about its own product.</p>

{_verified_note("jetoctopus")}
{CTA}"""

    return render(
        cat="vs", slug="jetoctopus-alternative",
        title=(
            ("Docket vs JetOctopus: logs at scale, or your own audit")
            if SITE_BRAND == "checkengine"
            else ("Docket vs JetOctopus: logs at scale, or an audit you own")
        ),
        desc=("JetOctopus reads your server logs and meters crawling by the URLs a month. "
              "Docket cannot read logs at all. Which question you are asking decides it."),
        h1="Docket vs JetOctopus",
        crumb='<a href="/">Docket</a> / <a href="/vs/">Compare</a> / JetOctopus',
        body=body,
        faq=[
            ("Is Docket a JetOctopus alternative?",
             "Not for log analysis, which is what JetOctopus is built around and Docket "
             "cannot do at all. For auditing a site you can crawl from your own machine and "
             "getting the fixes in priority order, Docket does that for a one-time price "
             "instead of an enterprise subscription."),
            ("Does Docket analyse server log files?",
             "No. Docket audits what your site serves to a crawler. Logs record what "
             "crawlers actually did (which pages Googlebot fetched, how often, and which it "
             "ignored), and that cannot be inferred from a crawl. On a large site it is the "
             "more valuable of the two data sources."),
            ("How much does JetOctopus cost?",
             f"Its published In-House plans are {price('jetoctopus')}, which is "
             f"{F.rival_annual_low('jetoctopus'):,} US dollars for a year on the entry plan at the "
             f"cheaper annual rate, with an Unlimited tier quoted only on request. Docket is {PRICE_COMPACT} "
             "once. They are not sold to the same buyer."),
            ("Do both have an MCP integration?",
             "Yes. Docket ships an MCP server so an assistant can run an audit, and "
             "JetOctopus's product list names an MCP integration too. It is not a difference "
             "between them, and this page does not present it as one."),
        ],
    )


#: CrawlRaven's plans as its pricing page lists them, read 2026-10-19 and recorded in
#: VERIFIED["crawlraven"] and data/competitors.csv. Kept as named values so the prose
#: interpolates them rather than typing them.
_CR_STARTER, _CR_PRO, _CR_AGENCY = 29, 39, 199
_CR_PRO_SITES, _CR_AGENCY_SITES, _CR_EXTRA_SITE = 3, 20, 10
_CR_LIFETIME = 390
_CR_TRIAL_DAYS, _CR_FREE_PAGES = 7, 100
_CR_AUDIT_POINTS, _CR_MCP_TOOLS = 200, 30


def crawlraven() -> Path:
    """The closest thing to Docket's pitch among the cheaper tools, and it now has an audit.

    ⚠️ THIS PAGE WAS OUT OF DATE ON 2026-10-19 AND WAS REWRITTEN, NOT PATCHED. It said
    CrawlRaven sold one-time licences in batches that step up every ten, that every
    paid tier marked its technical audit "coming soon", that it had a free tier for one
    site and white-label reports, and that its MCP listed 13 tools. Read again on
    2026-10-19, its pricing page shows monthly plans (Starter, Pro, Agency) with a
    fixed-site lifetime plan beside them, the technical audit included within a monthly
    page allowance, a 7-day trial, and MCP of up to 30 tools that can read stored audits
    but not start them. The page had slid from position 8 to 19 for "crawlraven" in the
    week of 10-11, and a comparison whose central claim the vendor's page no longer makes
    is a plausible reason.

    What stays: the overlap in pitch is conceded first, and nothing is claimed about the
    quality of either audit, because neither was measured.
    """
    r = _RUN
    first = r["top"][0]
    body = f"""
<p class="lede">CrawlRaven is the closest tool to Docket's pitch among the cheaper ones: it joins Search
Console and GA4 to a technical audit and hands back prioritised action items. It is sold by the month, with a
fixed-site lifetime plan beside it, and its audit runs within a monthly page allowance. Docket is an app for Mac and
64-bit Windows, bought once, with no allowance. The overlap is real, so it is said first.</p>

<h2>What CrawlRaven does that Docket does not</h2>

<ul>
<li><strong>Search Console and GA4, joined up.</strong> It connects both and reports keyword and
page performance against what visitors actually did. Docket audits your pages; it does not pull
your Search Console history or your analytics.</li>
<li><strong>Keyword work.</strong> Keyword maps, clusters, cannibalization flags, content gaps,
runner-up keywords and decay tracking, and on Pro an import of your Ahrefs or Semrush keyword lists.
Docket does none of this. It does not track rankings or research keywords.</li>
<li><strong>A trial and a free tool.</strong> A {_CR_TRIAL_DAYS} day free trial of everything in Pro on one site,
with no card, and a free audit tool for up to {_CR_FREE_PAGES} pages with no account. Docket's free version covers
any site but shows only the score, how many problems each area has and the top problem in full.</li>
</ul>

<p>It also lists MCP access to up to {_CR_MCP_TOOLS} tools across approved scopes, and its FAQ says MCP can read
stored audits but cannot start them. Docket ships an MCP server so an assistant can run an audit.</p>

<h2>The technical audit is there now, within an allowance</h2>

<p>An earlier version of this page said CrawlRaven's pricing page listed the technical audit as not yet
available. Read on {CHECKED_HUMAN["crawlraven"]}, it no longer does. The audit is listed among the Starter
features, and the FAQ says it is included on eligible paid or trial websites within a monthly page allowance, with
a CSV export of findings. The page describes a {_CR_AUDIT_POINTS}-point technical audit.</p>

<p>Docket runs {N_CHECKS} checks across thirteen areas, four of them not technical SEO at all: conversion, brand
consistency, AI search visibility and campaign tracking. It has no page allowance, and the crawl and the report stay
on your computer. A count of checks is a weak measure, and nothing here compares the quality of either tool's output,
which has not been measured.</p>

<h2>What one Docket run looks like</h2>

<p>CrawlRaven's audit is measured against a monthly page allowance. For scale, one Docket run on our own site,
{_run_date()}: {r["pages"]} pages crawled in {speed_words(r["seconds"])} on a Mac, score {r["score"]} out of 100,
grade {r["grade"]}, {r["findings_total"]} things to fix, and nothing spent because there is nothing to spend. The
finding Docket ranked first among those that name nobody else was &ldquo;{html.escape(first["title"])}&rdquo;,
{first["effort"]} effort, on {first["pages"]} page{"s" if first["pages"] != 1 else ""}.</p>

<h2>On the price</h2>

<p class="table-note">Read from CrawlRaven's pricing page on {CHECKED_HUMAN["crawlraven"]}. Its cost comparison
lists the lifetime plan; the monthly plans are the ones it leads with.</p>
<div class="wrap-tbl"><table class="cmp">
<thead><tr><th>Plan</th><th>Price</th><th>Sites included</th></tr></thead>
<tbody>
<tr><td>CrawlRaven Starter</td><td>${_CR_STARTER} a month</td><td>1</td></tr>
<tr><td>CrawlRaven Pro</td><td>${_CR_PRO} a month, plus ${_CR_EXTRA_SITE} a month for each extra site</td><td>{_CR_PRO_SITES}</td></tr>
<tr><td>CrawlRaven Agency</td><td>From ${_CR_AGENCY} a month</td><td>{_CR_AGENCY_SITES}</td></tr>
<tr><td>CrawlRaven Pro lifetime</td><td>${_CR_LIFETIME} as a single payment</td><td>{_CR_PRO_SITES}, fixed</td></tr>
<tr><td class="yes">Docket</td><td class="yes">{PRICE_COMPACT}</td><td class="yes">Any site</td></tr>
</tbody></table></div>

<p>CrawlRaven's Starter plan costs less than Docket for its first {_months_past_docket(_CR_STARTER) - 1} months, at
${_CR_STARTER} a month; from month {_months_past_docket(_CR_STARTER)} it has cost more. Twelve months of Starter come to
${_CR_STARTER * 12} for one site, against {PRICE_COMPACT} for any site; the lifetime plan is
${_CR_LIFETIME} for {_CR_PRO_SITES}. They are not the same purchase: one is a content-insights platform with a
metered audit, the other is the audit, running locally on your own computer with no account and no site limit.</p>

<h2>Which to buy</h2>

<ul>
<li><strong>Buy CrawlRaven</strong> if your question is which content to write and update, you
want Search Console and GA4 in one view, and you are happy to pay by the month for it.</li>
<li><strong>Buy Docket</strong> if your question is what is technically wrong with the site and
in what order to fix it, with a price that stops and no allowance to watch.</li>
</ul>

<p>They are close enough in spirit that owning both is not absurd. If a one-time price is what drew you here,
the other one worth knowing about is <a href="/vs/scrutiny-alternative/">Scrutiny</a>, a Mac app bought once
for {price('scrutiny')}, and stronger than either of us at link checking.</p>

{_verified_note("crawlraven")}
{CTA}"""

    return render(
        cat="vs", slug="crawlraven-alternative",
        modified="2026-11-08",  # Mac and 64-bit Windows, not Mac only (CEO QC),
        title="CrawlRaven vs Docket: price, technical audit, MCP",
        desc=(f"{price_sentence()} Compare CrawlRaven's cloud audit with Docket for Mac and Windows."),
        h1="Docket vs CrawlRaven",
        crumb='<a href="/">Docket</a> / <a href="/vs/">Compare</a> / CrawlRaven',
        body=body,
        faq=[
            ("Is Docket a CrawlRaven alternative?",
             "For the audit, yes. CrawlRaven joins Search Console and GA4 to a technical audit sold by the "
             "month; Docket is the technical audit, bought once, with conversion, brand and AI-visibility "
             "checks alongside it. It is not an alternative if you need Search Console and GA4 data or "
             "keyword work, which Docket does not do."),
            ("Which is cheaper, Docket or CrawlRaven?",
             f"CrawlRaven for its first {_months_past_docket(_CR_STARTER) - 1} months, then Docket. Its Starter "
             f"plan is ${_CR_STARTER} a month for one site, against Docket's {PRICE_COMPACT} for any site. Twelve months of Starter come to ${_CR_STARTER * 12}, and its "
             f"lifetime plan for {_CR_PRO_SITES} sites is ${_CR_LIFETIME}, as read on {CHECKED_HUMAN['crawlraven']}."),
            ("Does CrawlRaven have a technical SEO audit?",
             f"Yes. On {CHECKED_HUMAN['crawlraven']} its pricing page listed it among the Starter features, and "
             "its FAQ said it is included on eligible paid or trial websites within a monthly page allowance. "
             "When we read their pricing in September, the audit was not yet available."),
            ("Do both have an MCP integration?",
             f"Yes. CrawlRaven lists MCP access to up to {_CR_MCP_TOOLS} tools and says MCP can read stored "
             "audits but cannot start them. Docket ships an MCP server so an assistant can run an audit."),
            ("Does CrawlRaven have a free version?",
             f"It offers a {_CR_TRIAL_DAYS} day free trial on one site and a free audit tool for up to "
             f"{_CR_FREE_PAGES} pages with no account. Docket's free version shows your score, how many "
             "problems each area has and the top problem in full, on any site, with no key."),
            ("Does Docket connect to Google Search Console?",
             "Not for the keyword and traffic history CrawlRaven reports. Docket audits what "
             "your pages contain and how your server is configured, on your own machine, "
             "without an account."),
        ],
    )


def crawler_sh() -> Path:
    """The one that shares Docket's politics and does a different job.

    crawler.sh runs locally, needs no account, has no cloud bill and no
    per-page fee. That is Docket's own argument, made by somebody else, and
    saying so plainly is what makes the rest of the page believable.

    What it is FOR is different: its own headline calls it a local Markdown
    extractor for AI training and RAG. SEO analysis is one of its features
    rather than its purpose. Docket has nothing that turns a site into a
    training corpus.

    ⚠️ JAVASCRIPT RENDERING IS NOT A DIFFERENTIATOR. They render with their own
    engine instead of headless Chrome; Docket renders a sample of every audit in
    WebKit. Both do it.

    ⚠️ THEIR CHECK COUNT IS STATED TWICE AND DIFFERENTLY on the same page — "16
    categories" beside the paid tier, "24 automated checks" in the workflow
    section. Both are quoted rather than whichever suits this page, because
    picking one would be choosing the flattering reading of somebody else's
    marketing.
    """
    body = f"""
<p>crawler.sh and Docket agree about almost everything except what a crawler is for. It runs on
your own machine, needs no account, has no cloud bill and no per-page fee, which is Docket's entire argument, made by somebody else. Where they part company is purpose.</p>

<h2>What crawler.sh is for</h2>

<p>Its own headline calls it a local Markdown extractor for AI training and RAG: point it at a
site and it returns clean, readable Markdown ready for a retrieval pipeline, a fine-tuning
corpus or an agent's context, with word count, byline, language and excerpt on every page.
<strong>Docket does nothing of the kind.</strong> If you are building a dataset out of web
content, Docket is the wrong tool and crawler.sh is built for precisely that.</p>

<p>It also does SEO analysis, and describes that coverage in two different ways on the same page: "16-category SEO analysis" beside its paid tier, and "24 automated checks" in its
workflow section. The examples it gives are missing titles, duplicate meta descriptions, noindex
directives, thin content, broken links, long URLs and content-freshness signals.</p>

<h2>What Docket is for</h2>

<p>{N_CHECKS} checks across thirteen areas, four of which are not technical SEO at all (conversion, brand consistency, AI search visibility and campaign tracking), arriving as a ranked plan rather than a list of issues, with <a href="/learn/priority-model/">the ordering formula
published</a>. The overlap with their SEO feature is real but partial: the technical checks on
their list are ones Docket also runs, and most of what Docket runs is not on their list.</p>

<h2>The page cap</h2>

<p>This is the one measurable difference between two tools that both run locally. crawler.sh's
free tier is capped at 50 pages a session and its paid CLI tier at 10,000. In Docket,
<code>-n 0</code> removes the page-count limit. A crawl still stops at its time limit of
{F.limits()['wall_clock_minutes']} minutes by default or {F.limits()['everything_hours']} hours
with Everything, its depth limit of {F.crawl_depth()} by default, or when it runs out of links.</p>

<p>On price they are not close. crawler.sh is {price('crawler-sh')}, renewed yearly. Docket is
{PRICE_COMPACT}. At these list prices, Docket costs less from the first year.
Both can be tried free with no account: crawler.sh's free tier stops at 50 pages a
session, and Docket's free version runs the whole audit but shows only the score, how many
problems each area has and the top problem in full.</p>

<p>One thing that is <em>not</em> a difference: both render JavaScript. They use their own
engine rather than headless Chrome; Docket renders a sample of every audit in the WebKit that
macOS already ships.</p>

<h2>Which to buy</h2>

<ul>
<li><strong>Use crawler.sh</strong> if you want site content as Markdown for an AI pipeline, or
a free local crawler for a small site with SEO checks attached.</li>
<li><strong>Buy Docket</strong> if you want the audit itself: what is wrong, across technical,
conversion, brand and AI visibility, ranked into the order to fix it, with no page limit.</li>
</ul>

<p>If running locally is the part that matters to you,
<a href="/vs/scrutiny-alternative/">Scrutiny</a> is the third tool in that shape: a Mac app, bought once.
It adds spell checking, HTML validation and site search. Nothing here compares the quality of
either tool's checks, which has not been measured. Both vendors' own published descriptions are
what this page is built from.</p>

{_verified_note("crawler-sh")}
{CTA}"""

    return render(
        cat="vs", slug="crawler-sh-alternative",
        title="Docket vs crawler.sh: an audit, or Markdown for AI?",
        desc=("Both run locally with no account. crawler.sh turns sites into Markdown for AI "
              "training and caps pages per session; Docket is the audit, ranked, uncapped."),
        h1="Docket vs crawler.sh",
        crumb='<a href="/">Docket</a> / <a href="/vs/">Compare</a> / crawler.sh',
        body=body,
        faq=[
            ("Is Docket a crawler.sh alternative?",
             "Only for the SEO half. crawler.sh is a local Markdown extractor for AI training "
             "and RAG with SEO analysis attached; Docket has nothing that turns a site into a "
             "training corpus. For auditing and prioritising what is wrong with a site, "
             "Docket does considerably more."),
            ("Does crawler.sh limit how many pages you can crawl?",
             "Yes. Its free tier is capped at 50 pages a session and its paid CLI tier at "
             "10,000. In Docket, -n 0 removes the page-count limit. A crawl still stops at "
             f"its time limit of {F.limits()['wall_clock_minutes']} minutes by default or "
             f"{F.limits()['everything_hours']} hours with Everything, its depth limit of "
             f"{F.crawl_depth()} by default, or when it runs out of links."),
            ("Which is cheaper?",
             f"Docket, at {PRICE_COMPACT} against crawler.sh's {price('crawler-sh')}, which "
             "renews every year. Both have a free version that needs no account; Docket's "
             "shows the score, how many problems each area has and the top problem in full, not the rest."),
            ("Do both render JavaScript?",
             "Yes, and it is not a difference between them. crawler.sh uses its own render "
             "engine rather than headless Chrome; Docket renders a sample of every audit in "
             "the WebKit engine macOS already ships."),
        ],
    )


_SR_LO, _SR_HI = rival_monthly_range("seranking")


def se_ranking_vs_screaming_frog() -> Path:
    """Two tools people compare that are not the same KIND of thing.

    Every figure here was read from each vendor's own purchase page on
    2026-09-08 and is recorded in VERIFIED["se-ranking-vs-screaming-frog"].

    ⚠️ THIS PAGE NEARLY PUBLISHED A CHEAPER SE RANKING TIER THAT DOES NOT
    EXIST. An earlier reading recorded the plans as $89/$129/$279. On the page
    the $89 is the AI Search ADD-ON — printed "+$ 71.20 $ 89.00 /mo" inside an
    Add-on block next to Agency Pack (+$69/mo) and API (+$45/mo) — and the plus
    sign is the only thing separating an add-on from a plan. There are two
    priced plans and an Enterprise tier reading "Talk to sales".
    """
    sr = "https://seranking.com/subscription.html"
    sf = "https://www.screamingfrog.co.uk/seo-spider/"
    key = "se-ranking-vs-screaming-frog"
    body = f"""
<p class="lede"><strong>SE Ranking vs Screaming Frog:</strong> choose SE Ranking if you need
rank tracking and keyword research alongside a site audit. Choose Screaming Frog if you need
a desktop crawler and want to work with the crawl data yourself. SE Ranking's cloud audit is
<strong>metered by pages per month</strong>. Screaming Frog's paid licence has
<strong>no page meter</strong>; its free tier has a URL cap.</p>

<ul class="short-answer">
<li><strong>SE Ranking suits</strong> a marketer who wants rank tracking, keyword research and an
audit in one place, and is happy to pay monthly for it.</li>
<li><strong>Screaming Frog suits</strong> an SEO who wants raw crawl data from a desktop tool, on
very large sites, with no page meter.</li>
<li><strong>Docket suits</strong> someone on a Mac or Windows PC who wants a ranked list of what to fix, bought
once, with no meter.</li>
</ul>

<h2>SE Ranking vs Screaming Frog: prices and audit limits</h2>
<p class="table-note">Vendor figures were read from each vendor's own pages;
the evidence list below gives the pages and the dates read.</p>
<div class="wrap-tbl"><table class="cmp">
<thead><tr><th>&nbsp;</th><th>SE Ranking</th><th>Screaming Frog</th><th>Docket</th></tr></thead>
<tbody>
<tr><td>How you pay</td><td>Monthly subscription</td><td>Annual licence</td>
    <td class="yes">Once</td></tr>
<tr><td>Published price</td><td>{price("seranking")}</td><td>{price("screaming-frog")}</td>
    <td class="yes">{PRICE_COMPACT}</td></tr>
<tr><td>Plans</td><td>Core and Growth, then an Enterprise tier that says &ldquo;Talk to sales&rdquo;</td>
    <td>One tier. Licences are per user</td>
    <td class="yes">One licence, {F.licence_covers()}</td></tr>
<tr><td>Audit volume</td><td>Metered: Core states &ldquo;250k pages per month in audit&rdquo;, Growth
    &ldquo;2M pages per month in audit&rdquo;</td>
    <td class="yes">Unmetered; the free tier stops at 500 URLs</td>
    <td class="yes">Unmetered</td></tr>
<tr><td>Where the crawl runs</td><td>Their cloud</td><td class="yes">Your machine</td>
    <td class="yes">Your Mac or PC</td></tr>
<tr><td>Try before buying</td><td>&ldquo;Start free 14-day trial&rdquo;, &ldquo;No credit card
    required&rdquo;</td><td>Free tier, 500 URLs</td>
    <td>Free: your score, how many problems each area has and the top problem in full. Then a {REFUND_DAYS}-day refund</td></tr>
</tbody></table></div>
{_top_cta("vs-sr-sf")}
{price_note_html()}

<h2>When should you choose SE Ranking?</h2>

<p>Not a crawler. The audit is one module inside a rank-tracking and keyword platform, and the
Core plan states &ldquo;250k pages per month in audit&rdquo; and &ldquo;25K API credits &amp; MCP access&rdquo;.
The Growth plan states &ldquo;2M pages per month in audit&rdquo;. If you want daily rank tracking
across major search engines, that is the product, and neither of the other two here does it at
all.</p>

<p>The page meter is the thing to check before you buy. 250k pages a month is generous for one
site and starts to matter when you are auditing many, or re-auditing the same large site often.</p>

<h2>When should you choose Screaming Frog?</h2>

<p>The opposite trade. It audits &ldquo;over 300 SEO issues&rdquo;, it runs on your machine,
and nothing counts your pages. Their page says you can &ldquo;Download &amp; crawl 500 URLs for
free&rdquo;, and that &ldquo;For just &pound;199 per year you can purchase a licence, which
removes the 500 URL crawl limit&rdquo;. In US dollars the pricing page lists {price("screaming-frog")}
per licence, and says licences are per user, so two people need two. The free tier is genuinely
useful and genuinely limited: their Free vs Paid table puts Scheduling, Crawl Configuration,
Save &amp; Open Crawls, JavaScript Rendering, Crawl Comparison and Near Duplicate Content on the
paid side only, so the free version cannot save a crawl or render JavaScript.</p>
<p>If you only need a free audit, the <a href="/best/free-seo-audit-tools/">free SEO audit tools
list</a> puts the page checkers and site crawler beside their limits.</p>

<p>What you get back is data. Screaming Frog is the better tool if you know what you are looking for: very large crawls, a specific hypothesis to test. It does not
rank what to fix first, and it does not try to.</p>

<h2>Where Docket sits, and where it does not</h2>

<p>Docket is the third shape: bought once, run locally, unmetered, and the output is a ranked
plan rather than a table. Every finding carries how bad it is, how long the fix takes and the
change to make. That is the whole pitch, and it is worth being clear about what it costs you.</p>

<p><strong>Docket does not track rankings.</strong> No keyword positions, no daily rank
checks, no competitor position history. If that is why you were looking at SE Ranking, Docket
does not replace it and this page is not trying to talk you out of it.</p>

<p>Screaming Frog's Free vs Paid table lists &ldquo;JavaScript Rendering&rdquo; on the paid side.
Docket renders a sample by default.</p>

<p>SE Ranking is a cloud platform used in a browser. Screaming Frog runs on Windows, macOS
and Ubuntu. Docket runs on Macs with Apple silicon or Intel{' and on 64-bit Windows' if WINDOWS else ''}.</p>

{_measured("<p>Most of this page is about what the other two do. This is what Docket does: a real audit of our own site, with the figures the engine reported.</p>", former_address=True)}

<h2>Can you use both?</h2>

<p>Yes, because they do different jobs. SE Ranking tracks rankings and keywords and meters its audit by pages per
month. Screaming Frog crawls on your own machine and returns raw data, with no page meter. Nothing about one stops you
running the other. The price table above lists their published prices, with sources and dates below. If you
add a third tool for the part neither does, a ranked list of what to fix first, that is where Docket sits.</p>

<p>If the platform you already pay for is Ahrefs rather than SE Ranking, <a href="/vs/ahrefs-site-audit-alternative/">Ahrefs Site Audit</a> is set out the same way,
with what it checks and how a crawl is paid for.</p>

<h2>When to pick SE Ranking or Screaming Frog instead of Docket</h2>

<ul>
<li><strong>You need daily rank tracking and keyword research.</strong> Pick <a href="{sr}"
    rel="nofollow noopener">SE Ranking</a>, and the audit comes along with it. Docket does not
    track rankings.</li>
<li><strong>You crawl very large sites, or you want raw data to interrogate yourself.</strong>
    Pick <a href="{sf}" rel="nofollow noopener">Screaming Frog</a>. It handles far larger crawls
    than Docket.</li>
{WRONG_COMPUTER}
<li><strong>You want to know what is wrong with your site and what to do about it, on a Mac or Windows PC, with
    no subscription or page meter.</strong> That is what Docket is for.</li>
</ul>
{_verified_note(key, closing="If a figure here has gone stale, <a href='/about/'>tell us</a>.")}
{CTA}
"""
    return render(
        cat="vs", slug="se-ranking-vs-screaming-frog",
        modified="2026-11-09",
        title="SE Ranking vs Screaming Frog: prices, limits | Docket",
        desc=("SE Ranking combines a cloud site audit with rank tracking. Screaming Frog is a "
              "desktop crawler. Compare prices, audit limits and when to use each."),
        h1="SE Ranking vs Screaming Frog",
        crumb='<a href="/">Docket</a> / <a href="/vs/">Compare</a> / SE Ranking vs Screaming Frog',
        body=body,
        faq=[
            ("Which is better for a site audit, SE Ranking or Screaming Frog?",
             "It depends on the job. Screaming Frog is a desktop crawler with no page meter and a "
             "free tier of 500 URLs, for people who want raw crawl data. SE Ranking's audit is one "
             "module of a subscription platform, metered by pages per month and sold beside rank "
             "tracking and keyword research. Docket is a third option for Mac and Windows users: bought once, "
             "unmetered, with a ranked list of fixes."),
            ("How much does SE Ranking cost compared with Screaming Frog?",
             f"SE Ranking is {price('seranking')}. Screaming Frog is {price('screaming-frog')}, "
             f"with a free tier up to 500 URLs. The evidence list gives the sources and dates read. "
             f"Docket is {PRICE_COMPACT}."),
            ("Is SE Ranking's site audit unlimited?",
             "No. Its Core plan states \u201c250k pages per month in audit\u201d, so the audit "
             "is metered by pages per month. Screaming Frog's paid licence has no page meter."),
            ("Can I use Screaming Frog for free?",
             "Yes, up to 500 URLs. Their Free vs Paid table puts Scheduling, Crawl "
             "Configuration, Save & Open Crawls, JavaScript Rendering, Crawl Comparison and "
             "Near Duplicate Content on the paid side, so the free version cannot save a "
             "crawl or render JavaScript."),
            ("Can I use SE Ranking and Screaming Frog together?",
             "Yes. They do different jobs: SE Ranking tracks rankings and keywords and meters its audit "
             "by pages per month, while Screaming Frog crawls on your own machine and returns raw data "
             "with no page meter. Neither ranks what to fix first, which is the gap Docket fills for Mac and Windows "
             "users."),
            ("Which one tracks keyword rankings?",
             "SE Ranking. Screaming Frog does not, and neither does Docket. If daily rank "
             "tracking is what you need, that is the one of the three that does it."),
        ],
    )


BUILDERS = [screaming_frog, sitebulb, ahrefs, semrush, lighthouse,
            search_console, scrutiny, seoptimer, sitechecker, profound,
            jetoctopus, crawlraven, crawler_sh,
            se_ranking_vs_screaming_frog]


def build_all() -> list[Path]:
    return [b() for b in BUILDERS]


if __name__ == "__main__":
    for p in build_all():
        print(p)
