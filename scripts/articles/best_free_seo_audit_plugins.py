#!/usr/bin/env python3
"""WordPress audit choices from the supplied 20 November vendor readings."""
from pathlib import Path

from ahrefs_first_screen import checked
from best_compared_layout import disclosure, method, sections, table
from best_compared_sources import PLUGINS
from comparisons import source_link
from render import buy_block, render


def build() -> Path:
    body = f'''
{disclosure()}
<p id="measured-answer">WordPress SEO audit plugins do different jobs: some review a post, while others scan site problems.
{source_link('Squirrly SEO', 'https://plugin.squirrly.co/wordpress-seo-pricing/')} lists 1 audit suite page a month in its free account.
Match the audit allowance and paid features to the pages you need to check before installing a plugin.</p>
{checked('Squirrly SEO', ('Free audit allowance', 'https://plugin.squirrly.co/wordpress-seo-pricing/'))}
{method('the stated audit or content checks', 'The table includes eight available plugins and two outside checks, clearly labelled. A free download does not mean every audit feature is free.')}
<h2>Plugins and outside checks side by side</h2>
<p>Choose the job first: editing a post, finding broken pages, or making a site repair list.
Bing Site Scan and Lighthouse run outside WordPress. They are included for tasks that do not need another plugin.
For Slim SEO, the year comparison uses the displayed Black Friday price; other sale pages use the regular figure where one was read.</p>
{table(PLUGINS, 'WordPress plugins and outside audit checks')}
{sections(PLUGINS)}
<section data-rival="Ahrefs SEO plugin"><h2>Ahrefs SEO plugin is closed</h2>
<p>The WordPress listing says the plugin closed permanently on 13 February 2026 at the author's request and is not available for download.
It is not an available plugin in the table.</p>
{checked('Ahrefs', ('Closed plugin listing', 'https://wordpress.org/plugins/ahrefs-seo/'))}</section>
<h2>Before adding an audit plugin</h2>
<p>A listing's use of audit does not promise every check you need. Find the passage that describes your task, then look for a paid heading, account requirement or service limit.
Keep content analysis separate from a crawl of the whole site.</p>
<p>For a client site, agree on permission to install and on the report you need. A plugin can start work in WordPress while sending parts of it to a cloud service.
Read those requirements before changing a live setup. An outside check may fit when you cannot add a plugin.</p>
<div class="callout" id="check-engine"><h2>Check Engine: an outside site audit</h2>
<p>We make Check Engine. It audits public pages from your Mac or Windows PC, whether the site uses WordPress or another system.
You do not need to add a plugin to the site. Its free result shows a score, every problem by name, worst first, and the main problem in full with its fix; the full plan and report exports need a licence.</p>
<p>It does not sit beside your post while you write. Use a plugin's content analysis if that is where you need help.
For public-page repairs across a site, try the desktop audit on a small set of pages you know.</p>
{buy_block('wordpress-compared', anchor=False)}</div>
<p>See <a href="/best/free-seo-audit-tools/">free audit tools and limits</a> for checks that do not start in WordPress.</p>
'''
    return render(cat='best', slug='free-seo-audit-plugins-wordpress',
                  title='WordPress SEO audit plugins compared', h1='WordPress SEO audit plugins compared',
                  desc='Compare WordPress audit plugins by stated checks, free limits and yearly prices. Vendor sources read on 20 November 2026.',
                  crumb='<a href="/best/">SEO tools compared</a> / WordPress audit plugins',
                  body=body, published='2026-11-11', modified="2026-11-24",
                  faq=[
                      ('How can I tell whether a WordPress audit feature needs payment?',
                       'Find its own feature heading and plan table. A free plugin listing can describe paid tools too. Save the stated limit beside the report you need.'),
                      ('Should a client approve a new SEO plugin before an audit?',
                       'Agree on the install and the report first. Ask whether you can use a staging copy and whether outside services are allowed.'),
                      ('Can an outside audit replace advice beside a WordPress post?',
                       'An outside audit reviews public pages. Advice in the editor can help while you write. Choose by where you need to make the change.'),
                  ])


def build_all() -> list[Path]:
    return [build()]
