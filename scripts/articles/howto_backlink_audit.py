#!/usr/bin/env python3
"""A Search Console first backlink audit, with the open graph's limits.

Google sources and our own run come from the supplied backlink-audit-upgrade
FACTS.md. Ahrefs claims retain the original generator's last read date.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from comparisons import source_link  # noqa: E402
from render import render  # noqa: E402

# Dated evidence, not a new reading of the older rival or graph claims.
EVIDENCE = {
    "read": "20 November 2026",
    "modified": "2026-11-20",
    "published": "2026-09-14",
    "ahrefs_read": "19 October 2026",
    "table_rows": 1000,
    "own_sites": "four",
    "own_found": "None",
}
LINKS = "https://support.google.com/webmasters/answer/9049606?hl=en"
DISAVOW = "https://support.google.com/webmasters/answer/2648487?hl=en"
SPAM = "https://developers.google.com/search/docs/essentials/spam-policies"
AHREFS_CHECKER = "https://ahrefs.com/backlink-checker"
AHREFS_EXPLORER = "https://ahrefs.com/site-explorer"
AHREFS_PRICING = "https://ahrefs.com/pricing"
AHREFS_AUDIT = "https://ahrefs.com/site-audit"


def google_source(label: str = "Google Links report", url: str = LINKS) -> str:
    return f'Source: {source_link(label, url)}, read {EVIDENCE["read"]}.'


def backlink_audit() -> Path:
    body = f"""
<p id="measured-answer">To do a backlink audit, list who links to your site, check the links
you do not recognise, and leave most of them alone.
Start with {source_link("Google Search Console's Links report", LINKS)}, read {EVIDENCE['read']},
which shows a sample with up to {EVIDENCE['table_rows']:,} rows per table.
Disavow only in the narrow case in {source_link("Google's disavow guide", DISAVOW)}: many spammy,
artificial or low-quality links that caused, or are likely to cause, a manual action.</p>

<h2>How to do a backlink audit, step by step</h2>
<ol>
<li><strong>Open the Links report.</strong> In Google Search Console, select your own verified
site, then go to <strong>Links &gt; External links &gt; Top linking sites</strong>.
Start here to see who links to you. {google_source()}</li>
<li><strong>Export the list.</strong> Export the table you want to review and save it with
the date. Treat it as a sample, not a complete list of backlinks. {google_source()}</li>
<li><strong>Sort by linking site.</strong> In your saved list, group or sort the rows by the
site linking to you. Our method uses Google's linking-site view so you can review each
source together. {google_source()}</li>
<li><strong>Check the sites you do not recognise.</strong> Open the linking pages where
available and read the links in context. An unfamiliar name alone is not a reason to remove
a link. Google suggests checking whether you recognise your top linking sites.
{google_source()}</li>
<li><strong>Read the link text.</strong> Go to <strong>Links report &gt; External links &gt;
Top linking text</strong>. Look at the words used to link to you alongside the sites you
checked. The domain-level open graph cannot show that text. {google_source()}</li>
<li><strong>Decide what to keep.</strong> Leave ordinary links alone. For links you judge to
be spam, ask the linking site for removal. Consider disavow only if Google's conditions
about a large number of bad links and a manual action both apply.
{google_source()} {google_source("Google disavow guide", DISAVOW)}</li>
<li><strong>Re-check later.</strong> Keep notes of the sites you reviewed and any removal
requests. Our method is to export the report again later and compare the samples. A missing
row does not prove a link was removed because this is not a complete list.
{google_source()}</li>
</ol>

<h2>Where to get the list of links</h2>
<div class="wrap-tbl"><table>
<thead><tr><th scope="col">Source</th><th scope="col">What it shows</th>
<th scope="col">Page-level or domain-level</th><th scope="col">Cost basis as stated</th>
<th scope="col">Limit</th></tr></thead>
<tbody>
<tr><th scope="row">{source_link("Google Search Console Links report", LINKS)}</th>
<td>Linking sites, linked pages and top linking text for your own verified site</td>
<td>Page-level and site summaries</td><td>Free</td>
<td>A sample, not every backlink. Up to {EVIDENCE['table_rows']:,} rows per table;
tables may be cut short. Read {EVIDENCE['read']}.</td></tr>
<tr><th scope="row">Open link graph through Check Engine</th>
<td>Referring domains and a comparative ranking from Common Crawl</td>
<td>Domain-level only</td><td>No subscription; no graph credits to spend</td>
<td>No linking URLs, anchor text, first-seen dates or nofollow status. A site may be outside
the scanned ranks. Our own run: {EVIDENCE['read']}.</td></tr>
<tr><th scope="row">{source_link("Ahrefs Backlink Checker", AHREFS_CHECKER)}</th>
<td>Individual linking URLs and anchor text</td><td>Page-level</td><td>A free tier</td>
<td>Free-tier allowance not stated here. Read {EVIDENCE['ahrefs_read']}.</td></tr>
<tr><th scope="row">{source_link("Ahrefs Site Explorer", AHREFS_EXPLORER)}</th>
<td>The backlink profile with metrics and filtering</td><td>Page-level</td><td>Paid</td>
<td>Plan allowance not stated here. Read {EVIDENCE['ahrefs_read']}.</td></tr>
</tbody></table></div>

<h2>We ran it on our own sites</h2>
<p>On {EVIDENCE['read']}, we ran Check Engine's quick open-graph lookup on our own
{EVIDENCE['own_sites']} sites. {EVIDENCE['own_found']} was found in the part of the graph
scanned. The results were inconclusive: our sites were outside the scanned top ranks,
not shown to be absent from the web's links.</p>
<p>This run did not request the list of referring domains. For a new or small site, a missing
graph result is a reason to start with Search Console, not proof that nobody links to you.
Use the open graph for domains that appear in it. {google_source()}</p>

<h2>The three questions, and which tool answers which</h2>
<p><strong>Who links to us?</strong> Start with Search Console for your own site. The open
graph can add a list of referring domains when the domain appears in it.</p>
<p><strong>Is it doing anything?</strong> Check which pages the links point at. A commercial
link index adds page-level detail and metrics. Neither a domain count nor a ranking on its
own tells you whether an individual link helps.</p>
<p><strong>Is any of it a liability?</strong> Use Google's conditions below before taking
action. An audit should not turn an unfamiliar link into a removal request by default.</p>

<h2>What Ahrefs actually offers here</h2>
<p>Ahrefs's tools are <strong>Backlink Checker</strong> and <strong>Site Explorer</strong>.
Backlink Checker has a free tier for the page-level view, including linking URLs and anchor
text. Site Explorer is the paid view of the backlink profile with metrics and filtering.</p>
<p>We found no product called "Backlink Audit" across Ahrefs's
{source_link("pricing", AHREFS_PRICING)}, {source_link("Site Audit", AHREFS_AUDIT)},
{source_link("Backlink Checker", AHREFS_CHECKER)} and
{source_link("Site Explorer", AHREFS_EXPLORER)} pages when checked
{EVIDENCE['ahrefs_read']}. These are the older product readings, not a fresh check.</p>

<h2>What an open link graph can tell you</h2>
<p>Common Crawl publishes a public hyperlink graph. Check Engine reads domain-to-domain
links from it. To request referring domains, use:</p>
<pre><code>docket backlinks example.com --referring</code></pre>
<p>It streams the graph rather than saving it to disk. A pass serves all the domains you
request together, with no graph credits to spend.</p>
<p><strong>The limit: this is a domain-level graph.</strong> It records that a domain links
to another domain. It cannot show the linking page, anchor text, first-seen date or nofollow
status. It cannot build a disavow file or judge link quality.</p>
<p><a href="/learn/domain-authority-without-a-subscription/">Domain authority without a
subscription</a> explains the ranking derived from that graph and its limits.</p>

<h2>Should I disavow?</h2>
<p>Google says: <q>In most cases, Google can assess which links to trust without additional
guidance, so most sites will not need to use this tool.</q></p>
<p>Its conditions both need to apply: a considerable number of spammy, artificial or
low-quality links, and those links caused, or are likely to cause, a manual action.
Google warns that incorrect use can harm your site's performance in search.
Try to get the links removed first. {google_source("Google disavow guide", DISAVOW)}</p>
<p>Google defines link spam by the aim of manipulating rankings. Its examples include buying
or selling links for rankings and excessive link exchanges. That is a more useful test than
whether you recognise a domain name. {google_source("Google spam policies", SPAM)}</p>

<h2>What Check Engine does and does not do here</h2>
<p>Check Engine does not audit backlinks. It reads the public graph for referring-domain
counts and a comparative ranking. It has no backlink index of its own, no anchor-text data,
no disavow workflow and no opinion about link quality.
<a href="/vs/ahrefs-site-audit-alternative/">The comparison against Ahrefs Site Audit</a>
covers the crawling work.</p>
<p>Use its <a href="/learn/seo-audit/">technical audit</a> and
<a href="/learn/what-docket-checks/">list of checks</a> to inspect your own pages.
Check that linked pages still exist before seeking more links. Its crawl reports broken
internal targets; <a href="/learn/log-file-analysis/">your server log</a> shows external
requests for retired pages. Read <a href="/learn/internal-link-equity/">internal link
equity</a> for how internal links connect the pages that receive backlinks.</p>

<h2>Further reading</h2>
<ul>
<li><a href="/learn/click-depth-and-orphan-pages/">Click depth and orphan pages</a></li>
<li><a href="/how-to/fix-pages-competing-for-one-search/">Pages competing for the same search</a></li>
<li><a href="/how-to/fix-your-money-pages-first/">Fix the pages that make you money first</a></li>
<li><a href="/learn/priority-model/">How Check Engine decides what to fix first</a></li>
</ul>
<p><a class="btn" href="/download/">Download Docket</a></p>
"""
    return render(
        cat="how-to", slug="backlink-audit",
        title="Backlink audit: how to do one, step by step",
        modified=EVIDENCE["modified"],
        desc=("Start a backlink audit in Google Search Console. Export linking sites, check "
              "unfamiliar links, compare sources and use Google's narrow disavow test."),
        h1="Backlink audit: how to do one, step by step",
        crumb='<a href="/">Docket</a> / <a href="/how-to/">Fix it</a> / Backlink audit',
        body=body,
        published=EVIDENCE["published"],
        faq=[
            ("Which Search Console view should I open first for a backlink audit?",
             "Open Links, then External links, then Top linking sites for your own verified "
             "site. Export the sample and review the linking sites you do not recognise. "
             + google_source()),
            ("Does a missing open-graph result mean my small site has no backlinks?",
             f"No. In our run on {EVIDENCE['read']}, {EVIDENCE['own_found'].lower()} of our own "
             f"{EVIDENCE['own_sites']} sites was found in the scanned ranks. That result was "
             "inconclusive. Start with your verified site's Search Console Links report. "
             + google_source()),
            ("Can I use the open graph to read the words in a backlink?",
             "No. It records links between domains, not linking URLs or anchor text. For "
             "your own site, open Links report, External links, then Top linking text. "
             + google_source()),
            ("Is an unfamiliar linking site enough reason to submit a disavow file?",
             "No. Google's conditions require a considerable number of spammy, artificial "
             "or low-quality links and a manual action caused, or likely to be caused, by "
             "them. Incorrect use can harm search performance. "
             + google_source("Google disavow guide", DISAVOW)),
            ("What should I save so I can repeat a backlink audit later?",
             "Keep the dated export, notes on the linking sites you checked and any removal "
             "requests. Compare it with a later export, remembering that Google's report "
             "is a sample: a missing row does not prove removal. " + google_source()),
        ],
    )


BUILDERS = [backlink_audit]


def build_all() -> list[Path]:
    return [b() for b in BUILDERS]


if __name__ == "__main__":
    for p in build_all():
        print(p)
