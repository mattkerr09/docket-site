#!/usr/bin/env python3
"""Backlink audit — the job, and what a domain-level graph can and cannot answer.

Target query: "ahrefs backlink audit" (11 impressions, Search Console
2026-08-10 to 2026-09-05).

⚠️ THERE IS NO AHREFS PRODUCT CALLED "BACKLINK AUDIT". Checked 2026-09-09:
zero occurrences across ahrefs.com/pricing, /site-audit, /backlink-checker and
/site-explorer. Their tools are Backlink Checker and Site Explorer. Second
phantom product name in one batch — see UPGRADES.md 2026-09-14.

⚠️ DISTINCT FROM /learn/domain-authority-without-a-subscription/, which explains
the METRIC (harmonic centrality, where the data comes from, what it cannot tell
you). This page is the TASK. They cross-link; one query each.

⚠️ DOCKET'S LINK DATA IS DOMAIN-LEVEL, NOT PAGE-LEVEL. `docket backlinks` reads
Common Crawl's hyperlink graph — domain-to-domain arcs. It cannot list the
individual linking URLs, the anchor text, or build a disavow file, and this page
says so rather than letting the reader assume parity with a backlink index.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import facts as F  # noqa: E402
from render import render  # noqa: E402


def backlink_audit() -> Path:
    body = """
<p class="lede">A backlink audit asks three questions: who links to us, is any of it doing
anything, and is any of it a liability. Ahrefs does not sell a product called "Backlink Audit" —
the work is split across their Backlink Checker and Site Explorer — and the free half of the job
can be done from an open dataset, as long as you know which question that dataset can answer.</p>

<h2>The three questions, and which tool answers which</h2>

<p><strong>Who links to us.</strong> A list of referring domains. This is the cheapest question
and the one an open dataset answers well.</p>

<p><strong>Is it doing anything.</strong> Whether those links carry authority, and whether the
pages they point at are the ones you want ranking. This needs a link index with page-level detail
and a metric attached to it.</p>

<p><strong>Is any of it a liability.</strong> The disavow question — the one people reach for
first and need least. Search engines discount obvious spam automatically; a disavow file
submitted on a hunch can remove links that were helping you. Unless you have bought links or
inherited a domain with a known history, the honest answer is usually "leave it".</p>

<h2>What Ahrefs actually offers here</h2>

<p><strong>Backlink Checker</strong> — in their words, "check backlinks to any site", drawing on
what they describe as the world's biggest index of live backlinks. There is
a free tier. This is the page-level view: individual linking URLs and anchor text.</p>

<p><strong>Site Explorer</strong> — their description is "analyze ANY website's organic traffic,
AI visibility, backlink profile, and paid traffic". This is the paid, full version of the same
data with the metrics and filtering attached.</p>

<p>If what you need is every linking URL with its anchor text, that is what a commercial backlink
index is for and there is no free substitute for it. Docket does not have one and is not going to
pretend otherwise.</p>

<h2>What an open link graph can tell you</h2>

<p>Common Crawl publishes a hyperlink graph of the web — {GRAPH_DOMAINS_M} million domains in the
{GRAPH_RELEASE} release. <code>docket backlinks example.com</code> reads it directly:</p>

<pre><code>docket backlinks example.com --referring</code></pre>

<p>It streams the graph rather than downloading it, so nothing is written to disk, one pass
serves every domain you pass on the command line, and there are no credits to spend. On a real
site — {GRAPH_HOST} — the graph shows {GRAPH_REFERRING:,} referring domains.</p>

<p><strong>The limit, stated plainly: this is a domain-level graph.</strong> It tells you that
one domain links to another. It does not give you the linking page, the anchor text, the link's
first-seen date, or whether it is nofollow. Those are page-level facts and they are not in this
dataset at any price.</p>

<p>So it answers question one properly and question two partially — enough to compare your
referring-domain count against a competitor's, which is the comparison most people actually want
and the one they usually pay a subscription to make once.
<a href="/learn/domain-authority-without-a-subscription/">Domain authority without a
subscription</a> covers the metric side of that: what the ranking derived from this graph means,
and what it deliberately cannot tell you.</p>

<h2>The order to do it in</h2>

<p><strong>1. Count before you read.</strong> Get your referring-domain count and two
competitors'. If you are within the same order of magnitude, links are probably not your
constraint and the audit can stop here — which is a genuinely useful outcome and the one nobody
sells you.</p>

<p><strong>2. Check what the links point at.</strong> Referring domains pointing only at your
homepage is a different problem from links spread across your content, and it is fixable by
choosing what you promote rather than by acquiring more links.</p>

<p><strong>3. Check the pages are still there.</strong> An earned link pointing at a URL you
retired is authority arriving at a 404. This is the most common repairable finding in a backlink
audit and it costs one redirect — Docket's crawl reports the broken internal targets, and
<a href="/learn/log-file-analysis/">your server log</a> shows the external ones actually being
requested.</p>

<p><strong>4. Only then consider disavow.</strong> And usually decide against it.</p>

<h2>What Docket does and does not do here</h2>

<p>Docket reads the public graph for referring-domain counts and a comparative ranking, on your
machine, with no subscription. It has no backlink index of its own, no anchor-text data, no
disavow workflow, and no opinion about link quality. Those are the parts a commercial index
exists for, and if they are what your week needs, buy one —
<a href="/vs/ahrefs-site-audit-alternative/">the comparison against Ahrefs Site Audit</a> is
about the crawling half only, and says the same thing about their link data.</p>

<p>What Docket audits properly is what is on your own site: the
<a href="/learn/seo-audit/">technical audit</a> across
<a href="/learn/what-docket-checks/">every check it runs</a>, including the internal link
structure that decides where authority goes once it arrives — see
<a href="/learn/internal-link-equity/">internal link equity</a>. A link profile you cannot use
because the pages it points at are thin or unreachable is a content and crawling problem wearing
a backlink costume.</p>

<p><a class="btn" href="/download/">Download Docket</a></p>
""".replace("{GRAPH_DOMAINS_M}", F.graph_domains_m()) \
   .replace("{GRAPH_RELEASE}", F.graph_release()) \
   .replace("{GRAPH_HOST}", F.graph_example_host()) \
   .replace("{GRAPH_REFERRING:,}", f"{F.graph_example_referring():,}")
    # Further reading: pages Google had not yet discovered on 2026-09-22 (URL
    # Inspection: "unknown to Google"), linked from this page because Google
    # recrawls it often and last crawled the hubs that list them in August.
    # Chosen by topic; each such page is linked from exactly one article.
    body += """
<h2>Further reading</h2>
<ul>
<li><a href="/learn/click-depth-and-orphan-pages/">Click depth and orphan pages</a></li>
<li><a href="/how-to/fix-pages-competing-for-one-search/">Pages competing for the same search</a></li>
<li><a href="/how-to/fix-your-money-pages-first/">Fix the pages that make you money first</a></li>
<li><a href="/learn/priority-model/">How Docket decides what to fix first</a></li>
</ul>
"""
    return render(
        cat="how-to", slug="backlink-audit",
        title="Backlink audit: which questions are worth paying for",
        desc=("Ahrefs sells no product called Backlink Audit. The three questions an audit "
              "asks, which tool answers each, and what an open link graph cannot."),
        h1="How to do a backlink audit",
        crumb='<a href="/">Docket</a> / <a href="/how-to/">Fix it</a> / Backlink audit',
        body=body,
        published="2026-09-14",
        faq=[
            ("Does Ahrefs have a backlink audit tool?",
             "Not under that name. Checked across their pricing, Site Audit, Backlink Checker "
             "and Site Explorer pages, the phrase does not appear. The work people mean by "
             "“backlink audit” is done with Backlink Checker for individual links and Site "
             "Explorer for the full profile."),
            ("Can I audit backlinks for free?",
             "Partly. Common Crawl's public hyperlink graph gives referring domains at the "
             "domain level, which answers “who links to us” and lets you compare your count "
             "against a competitor's. It does not give linking URLs, anchor text or nofollow "
             "status — those need a commercial backlink index."),
            ("Should I disavow bad backlinks?",
             "Usually not. Search engines discount obvious spam on their own, and a disavow "
             "file submitted on a hunch can remove links that were helping. The case for it is "
             "narrow: links you or a predecessor bought, or a domain with a known history."),
            ("What is the difference between a domain-level and a page-level link graph?",
             "A domain-level graph records that one domain links to another. A page-level index "
             "records which URL links to which URL, with the anchor text. The first is enough "
             "to count referring domains and compare sites; the second is what you need to look "
             "at an individual link."),
            ("What is the most common fixable finding in a backlink audit?",
             "An earned link pointing at a URL that no longer exists. The authority arrives at "
             "a 404 and one redirect recovers it. It is worth checking before anything more "
             "ambitious, because it costs almost nothing and nobody is selling it to you."),
        ],
    )


BUILDERS = [backlink_audit]


def build_all() -> list[Path]:
    return [b() for b in BUILDERS]


if __name__ == "__main__":
    for p in build_all():
        print(p)
