#!/usr/bin/env python3
"""Crawler comparison from the supplied 20 November 2026 facts."""
import json
from pathlib import Path

from ahrefs_first_screen import checked
from best_compared_layout import disclosure, method, sections, table
from best_compared_sources import CRAWLERS
from comparisons import source_link
from render import DATA, N_CHECKS, N_LANES, PRICE_COMPACT, REFUND_DAYS, buy_block, render, speed_words

_RUN = json.loads((DATA / 'free-run.json').read_text())
_LIMITS = json.loads((DATA / 'limits.json').read_text())


def sf_alternatives() -> Path:
    from pages import free_result_figure

    body = f'''
{disclosure()}
<p id="measured-answer">Screaming Frog alternatives differ in where they run, their crawl limits and the way you pay.
{source_link('Screaming Frog SEO Spider', 'https://www.screamingfrog.co.uk/seo-spider/')} allows 500 URLs per free crawl.
Compare that allowance with your URL list, then decide whether a desktop crawl, cloud audit or continuous monitor fits your work.</p>
{checked('Screaming Frog', ('SEO Spider', 'https://www.screamingfrog.co.uk/seo-spider/'))}
{method('crawl coverage and the stated audit features', 'The reference crawler stays in the table. A continuous monitor and a one-off crawl answer different questions.')}
<h2>Crawlers and monitors side by side</h2>
<p>The year comparison uses the entry paid plan. Netpeak and SE Ranking use regular prices, so a checkout offer does not decide the order.
Semrush's year amount is twelve times its annual-billing monthly figure. A missing price is left unknown.</p>
{table(CRAWLERS, 'Screaming Frog and alternative crawl setups')}
{sections(CRAWLERS)}
<h2>Choose the work before the software</h2>
<p>For a crawl from your own computer, compare the desktop rows. For repeat checks that do not depend on your computer being awake, look at the cloud tools and ask about scheduling.
If server logs are part of the question, the rows that name log analysis give you a different starting point from a page-only audit.</p>
<p>A crawl total and a monthly allowance are different limits. Write down the size of each site, how often you will repeat the audit and how many users need access.
If a free result stops at its cap, record the unchecked pages before drawing a conclusion about the whole site.</p>
<div class="callout" id="check-engine"><h2>Check Engine: our local fix plan</h2>
<p><strong>At a glance:</strong> {PRICE_COMPACT}, one payment and no subscription. Mac (Apple silicon or Intel) and Windows.
A technical SEO audit that finds broken links and other problems, then ranks what to fix first. {REFUND_DAYS}-day refund, no conditions.</p>
<p>Check Engine runs {N_CHECKS} checks across {N_LANES} areas on Mac and Windows and orders repairs by impact and effort.
Its default crawl is {_LIMITS['ui_default_pages']} pages with a {_LIMITS['wall_clock_minutes']}-minute limit; both can be raised.
It has no custom extraction. It renders a sample of pages in WebKit rather than rendering every page.</p>
{free_result_figure()}
<p>Our <a href="/vs/screaming-frog-alternative/">published free audit</a>, recorded on 9 November 2026 on our own company site, read {_RUN['pages']} pages in {speed_words(_RUN['seconds'])} and found {_RUN['problems']} problems.
The score was {_RUN['score']} out of 100. This small run does not show large-site coverage, and we did not run the rivals for this comparison.</p>
<p>The free app shows a score, counts and the main problem with its fix. The full repair plan and reports need a licence.
Scheduled re-audits run only while the app is open and the computer is awake.</p>
{buy_block('sf-alternatives-page', try_app='sf-alternatives-page-try-free', anchor=False)}</div>
<h2>Check a result you can verify</h2>
<p>Crawl the same known pages with the same start address. Keep settings with each result.
Check whether the report explains a real fault you can reproduce, then repeat the crawl after fixing it.
This page compares stated facts, so it does not award points for speed, accuracy or the number of findings.</p>
<p>For a smaller task, see <a href="/best/free-seo-audit-tools/">free audit tools and limits</a>.
For report branding, read <a href="/best/white-label-seo-audit-tools/">white-label tools compared</a>.
For audit software sold once instead of monthly, read <a href="/best/seo-audit-software-no-subscription/">SEO audit software with no monthly subscription</a>.</p>
'''
    return render(cat='best', slug='screaming-frog-alternatives',
                  # 22 Nov 2026 (AI visibility, CEO go): ChatGPT's E3 named us from the 5 Nov version of this page, titled "for
                  # Mac and Windows (2026)"; the 20 Nov retitle had dropped those words, and E2 (for Mac) cited no page of ours.
                  title='Screaming Frog alternatives for Mac and Windows (2026)',
                  h1='Screaming Frog alternatives for Mac and Windows',
                  desc='Screaming Frog alternatives for Mac and Windows: prices, one-time or subscription, free limits, desktop or cloud. Vendor pages read 20 November 2026.',
                  crumb='<a href="/best/">SEO tools compared</a> / Screaming Frog alternatives',
                  body=body, modified='2026-11-22',
                  faq=[
                      ('What should I record before trying another crawler?',
                       'Save the start address, settings, pages you expect to reach and any known faults. Use the same small set of pages when checking each result.'),
                      ('Does a monthly crawl allowance describe one audit?',
                       'It may be shared across several runs. Read the plan\'s project cap as well as the monthly total, then leave room for a repeat audit after repairs.'),
                      ('How should I compare a monitor with a desktop crawl?',
                       'Write down whether you need a single snapshot or repeated checks. Ask what happens when your computer is off and how long the service keeps earlier results.'),
                  ])


if __name__ == '__main__':
    print(sf_alternatives())
