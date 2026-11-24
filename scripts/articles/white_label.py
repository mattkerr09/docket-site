#!/usr/bin/env python3
"""White-label reporting from the supplied 20 November vendor readings."""
from html import escape
import json
from pathlib import Path

import facts as F
from ahrefs_first_screen import checked
from best_compared_layout import disclosure, method, sections, table
from best_compared_sources import WHITE_LABEL
from comparisons import source_link
from render import DATA, REFUND_DAYS, buy_block, render, speed_words

_RUN = json.loads((DATA / 'sample-run.json').read_text())


def white_label_tools() -> Path:
    br = _RUN['branded_image']
    body = f'''
{disclosure()}
<p id="measured-answer">White-label SEO audit tools differ in what carries your name: a PDF, an online report or a client portal.
{source_link('SEO PowerSuite Enterprise', 'https://www.link-assistant.com/pricing.html')} lists white-label reports at $599.00 a year for the suite.
Check which plan includes branding, and the report format you will send, before buying.</p>
{checked('SEO PowerSuite', ('Enterprise plan', 'https://www.link-assistant.com/pricing.html'))}
{method('the stated white-label feature and the plan that includes it', 'No ongoing free white-label version was confirmed. Free audit tiers and trials are shown separately from paid branding.')}
<h2>Report branding and plan limits</h2>
<p>The table includes audit crawlers, a WordPress plugin and reporting platforms, with the type labelled.
The annual comparison is for the stated branding plan. AgencyAnalytics is per client, and Semrush My Reports is per report with any toolkit cost separate.
For Sitechecker, the amount is twelve monthly payments rather than a quoted annual plan. SE Ranking includes Core plus the Agency Pack.
Netpeak uses its regular price. SEOmator is listed as a planned feature, not an available white-label report.</p>
{table(WHITE_LABEL, 'White-label tools, formats and yearly cost basis')}
{sections(WHITE_LABEL)}
<h2>Ask for the report you will actually send</h2>
<p>Send the maker a short brief with your logo, the file format you need and whether clients must log in.
Ask for a sample from the same plan you would buy. A PDF without a vendor's name does not by itself promise a custom web address or a client portal.</p>
<p>Count the reports, clients and websites you expect to use. A per-report price can grow with delivery volume; a per-client plan grows with your client list.
A plugin's white-label setting may solve a WordPress task without covering the same handoff as a cloud reporting tool.</p>
<div class="callout" id="check-engine"><h2>Check Engine: our branded report exports</h2>
<p>The paid app replaces Check Engine's name and logo with your agency's name and logo on PDF and HTML reports, with a Prepared by line.
A licence covers {F.licence_covers()}, and the refund period is {REFUND_DAYS} days.
It has no client portal, custom report domain, editable report templates or rank tracking.</p>
<figure class="shot"><img src="{br['src']}" width="{br['width']}" height="{br['height']}" loading="lazy" decoding="async"
alt="A real audit report with a placeholder logo and the name {escape(br['name'])}.">
<figcaption>A real Check Engine report on our own site, with Report branding set to a placeholder.</figcaption></figure>
<p>This report was recorded on 11 November 2026. It covers {_RUN['pages']} pages, took {speed_words(_RUN['seconds'])} and lists {_RUN['issues']} issues.
It is our own recorded result, not a test of the other tools. Nothing here measures whose report is more useful.</p>
<p>Scheduled re-audits run only while the app is open and the computer is awake.
If clients need a login or an always-available report address, include that requirement in your search.</p>
{buy_block('wl-tools-page', try_app='wl-tools-page-try-free', anchor=False)}</div>
<h2>Keep the audit and the handoff together</h2>
<p>Agree on which pages the audit covers and how a client will receive it.
After a repair, save the next result with its date so both of you can follow what changed.
Branding should make the report clear about who prepared it without hiding the scope or the limits of the audit.</p>
<p>For crawl coverage, compare <a href="/best/screaming-frog-alternatives/">Screaming Frog alternatives</a>.
For our report setup, see <a href="/for/agencies/">Check Engine for agencies</a>.</p>
'''
    return render(cat='best', slug='white-label-seo-audit-tools',
                  title='White-label SEO audit tools compared', h1='White-label SEO audit tools compared',
                  desc='Compare white-label report formats, required plans and year costs. Vendor sources read on 20 November 2026, with planned features labelled.',
                  crumb='<a href="/best/">SEO tools compared</a> / White-label SEO audit tools',
                  body=body, modified='2026-11-20',
                  faq=[
                      ('What should a white-label report sample show before I pay?',
                       'Ask for a sample from the plan you would buy. Check your logo, the vendor marks, the file format and any client login or report address you need.'),
                      ('Should I budget white-label reports by client or by file?',
                       'Use the unit the plan charges for. Count expected clients and reports separately, then include any base subscription or branding add-on.'),
                      ('Does removing a vendor logo provide a client portal?',
                       'A report without a vendor logo is a branding feature. Ask separately about client access, custom domains and report storage.'),
                      ('How should I treat a report feature described as after launch?',
                       'Treat it as planned. Confirm that it is available on the plan you need before making a purchase depend on it.'),
                  ])


if __name__ == '__main__':
    print(white_label_tools())
