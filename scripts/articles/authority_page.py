#!/usr/bin/env python3
"""`docket backlinks` — in the CLI reference on one page, explained on none.

Every figure here is inside a verbatim output block, because it was produced by
running the shipped 1.1.16 binary on 2026-08-14 and the derived-number gate is
right that a measured number retyped into a sentence is a number nothing will
re-measure.

The page is built around the control rather than the feature. A domain invented
to be certain it does not exist returns the *same* answer as this site's own
domain: "not found in the part of the graph scanned". That is the honest limit
of the method and it is the thing a reader most needs told, because every paid
tool in this category answers the same question with a confident small number.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from render import render  # noqa: E402


def domain_authority() -> Path:
    body = """
<p class="lede">Every SEO suite sells you a domain authority score, and every one of them is
that vendor's estimate of a thing Google has never published. Docket computes a ranking from
the same kind of public data — the Common Crawl hyperlink graph — and the useful difference
is not the number. It is what it says when it does not know.</p>

<pre><code>$ docket backlinks wikipedia.org bbc.co.uk example-shop-that-does-not-exist-9134.com

wikipedia.org
  ranks 14 of 117,963,409 domains by harmonic centrality
  — the top 0.0000% of the crawled web.

bbc.co.uk
  ranks 86 of 117,963,409 domains by harmonic centrality
  — the top 0.0001% of the crawled web.

example-shop-that-does-not-exist-9134.com
  was not found in the part of the graph scanned. It is outside the
  top ranks rather than absent.

Common Crawl hyperlink graph, cc-main-2026-may-jun-jul. Their coverage and
their ranking, not Google's, and the graph lags about a month.</code></pre>

<h2>Read the third one twice</h2>

<p>That domain was invented for this test. It has never existed, nothing has ever linked to
it, and its true authority is zero.</p>

<p>Docket does not say zero. It says the domain was not found in the part of the graph
scanned, and that this means outside the top ranks rather than absent — because those are
genuinely the same observation from where the tool is standing. A small real business and a
domain that does not exist look identical in the slice of the graph being read, and any
number printed there would be invented.</p>

<p>We ran the same command on this site's own domain and got the same answer. That is the
correct result and it is also the least flattering one available, which is why it is on this
page.</p>

<h2>What harmonic centrality is, and what it is not</h2>

<p>It is a measure of how close a domain sits to everything else in the link graph — not how
many links point at it. A page linked from a thousand pages that nothing links to is
peripheral; a page linked from a handful of well-connected hubs is central. Counting links
cannot tell those apart, which is why link counts are the least useful number in most
reports.</p>

<p>What it is not is a Google metric. Google has never published a domain authority figure
and does not endorse one. This ranking describes Common Crawl's view of the web, from a
snapshot whose name is printed with the result so you can tell how old it is.</p>

<h2>Where the data comes from, and what it costs</h2>

<p>Common Crawl publishes a hyperlink graph — an open dataset of which domain links to which
across a crawl of the public web. Docket streams the ranked slice of it directly and reports
where your domain falls. Nothing is written to disk, no account is involved, and there is no
API key, because there is no API. The dataset is public.</p>

<p><code>--referring</code> also lists the domains linking in. That streams the full graph,
which is measured in gigabytes and takes minutes, and one pass serves every domain you name
in the same command — so ask about your site and three competitors at once rather than four
times.</p>

<h2>What this deliberately cannot tell you</h2>

<ul>
<li><strong>Which page links to you, and with what anchor text.</strong> That lives in
archive files far too large to fetch from a laptop. If you need per-page backlinks, a
subscription tool is the right purchase and Docket will not pretend otherwise.</li>
<li><strong>Whether a link is followed, paid, or in a footer.</strong> The graph records
that a link exists.</li>
<li><strong>Anything about a domain outside the ranked slice</strong>, which is most
domains, including almost certainly yours. That is the honest shape of this feature: it
tells large sites where they stand and tells small sites that it cannot see them.</li>
</ul>

<h2>So who is it for</h2>

<p>Mostly for comparison. Asking about four competitors in one command tells you which of
them the wider web actually treats as central, and that is a different — and more stable —
answer than a rankings snapshot. If none of them appear, that is information too: you are
competing in a space where authority is not the deciding factor, and the effort is better
spent on the pages themselves.</p>

<p><a class="btn" href="/download/">Download Docket</a></p>
"""
    return render(
        cat="learn", slug="domain-authority-without-a-subscription",
        title="Domain authority without a subscription",
        desc=("Docket ranks a domain from the public Common Crawl link graph — and "
              "says it cannot see you rather than printing a small number it "
              "invented."),
        h1="Domain authority without a subscription",
        crumb=('<a href="/">Docket</a> / <a href="/learn/">Learn</a> / '
               'Domain authority'),
        body=body,
        faq=[
            ("Is domain authority a Google ranking factor?",
             "No. Google has never published a domain authority score and does not "
             "endorse one. Every figure you have seen is a vendor's estimate built from "
             "link data they collected. Docket's is built from Common Crawl's public "
             "hyperlink graph and says so, including the snapshot it used."),
            ("Why does Docket say my domain was not found?",
             "Because it reads a ranked slice of the graph, and most domains are outside "
             "it. A small real business and a domain that does not exist look identical "
             "from there, so Docket reports that it did not find you rather than "
             "printing a number it would have to invent."),
            ("Do I need an API key or an account?",
             "No. Common Crawl's hyperlink graph is a public dataset. Docket streams the "
             "part it needs, writes nothing to disk, and one pass answers for every "
             "domain you name in the same command."),
            ("Can Docket tell me which pages link to my site?",
             "No. Per-page backlinks and anchor text live in archive files far too large "
             "to fetch from a laptop. If that is what you need, a subscription backlink "
             "tool is the right purchase and this is not a substitute for it."),
        ],
    )


BUILDERS = [domain_authority]


def build_all() -> list[Path]:
    return [b() for b in BUILDERS]


if __name__ == "__main__":
    for p in build_all():
        print(p)
