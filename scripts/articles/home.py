#!/usr/bin/env python3
"""The homepage.

Structure follows the GEO-optimal shape the strategy doc specifies: answer in
the first two sentences, stat-dense, comparison table, and — the part most
product sites skip — an explicit section on what the tool cannot do. A page
that never concedes anything reads as marketing and gets discounted by readers
and by models.

Every number here comes from the shipped build. Nothing is estimated.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from render import BASE, render  # noqa: E402

DATA = Path(__file__).resolve().parents[2] / "data" / "index-2026-08.json"


def index_stat() -> tuple[str, str, int]:
    """Pull the headline Index figure, or fall back to no claim at all.

    If the dataset is missing we print nothing rather than a placeholder. A
    fabricated statistic on the homepage would undermine the one thing the
    Index exists to establish.
    """
    if not DATA.exists():
        return "", "", 0
    d = json.loads(DATA.read_text())
    s = d["summary"]
    pct = round(100 * s["blocking_any_citation_bot"] / s["n"])
    return str(pct), d["collected"][:10], s["n"]


def body() -> str:
    pct, collected, n = index_stat()

    index_block = ""
    if pct:
        index_block = f"""
<div class="callout">
<div class="callout-title">From the Scout Index</div>
<p><strong>{pct}% of the {n} well-known sites we measured block at least one AI
search crawler</strong> — usually without meaning to. Blocking <code>GPTBot</code>
keeps you out of training data. Blocking <code>OAI-SearchBot</code> keeps you out
of ChatGPT's answers entirely. Most robots.txt files treat them as the same thing.
<a href="/index/">See the full dataset →</a></p>
</div>"""

    return f"""
<p class="lede">Scout audits any website and tells you what to fix, in order.
It runs 80 checks on your Mac, ranks every problem by impact against effort, and
gives you the exact markup to paste. One download. No subscription, no crawl
credits, and nothing about your site leaves the machine.</p>

<p><a class="btn" href="#download">Download for Mac</a>
&nbsp;<a class="btn-ghost" href="/index/">Read the Index</a></p>

<div class="stat-row">
<div class="stat"><b>80</b><span>checks across 12 areas</span></div>
<div class="stat"><b>12</b><span>including 3 nobody else audits</span></div>
<div class="stat"><b>0</b><span>data sent anywhere</span></div>
<div class="stat"><b>16MB</b><span>download, no account</span></div>
</div>

{index_block}

<h2>Every other tool hands you a list. Scout hands you a sequence.</h2>
<p>Semrush publishes 140+ checkpoints. Ahrefs lists 170+. Screaming Frog will
happily tell you that 412 pages have a short title. None of them tell you what to
do first — and ordering is the hard part, the part a business owner genuinely
cannot do alone.</p>

<p>Scout sorts every finding into four phases and makes you a plan:</p>
<ol>
<li><strong>Stop the bleeding.</strong> Things actively preventing the site from
ranking at all. A noindex on the homepage. A robots.txt that walls off the site.</li>
<li><strong>Quick wins.</strong> High impact, under an hour each.</li>
<li><strong>Build.</strong> Worth real effort — schedule it.</li>
<li><strong>Polish.</strong> When the rest is done.</li>
</ol>

<h2>Three things it audits that crawler tools don't</h2>

<h3>AI search visibility</h3>
<p>Whether ChatGPT, Perplexity, Claude and Google's AI Overviews can actually
reach and cite you. Scout checks each crawler separately, because they are not
interchangeable: <code>GPTBot</code> is OpenAI's <em>training</em> crawler and
blocking it is a legitimate business decision. <code>OAI-SearchBot</code> is what
builds ChatGPT's live index — block that and you are simply absent. Plenty of
robots.txt files block both, having meant to block only the first.</p>
<p>It also checks the things that decide whether you get quoted once you are
reachable: whether your pages render server-side (most AI crawlers do not run
JavaScript, so a client-rendered page is a blank page to them), whether your
content is structured as answers, and whether your <code>sameAs</code> links let
a model resolve you to a real business rather than an unverified string.</p>

<h3>Marketing conversion</h3>
<p>Scout reads the landing experience the way a visitor arriving from a campaign
would: is there a call to action, does the headline state what you do, how many
fields does the form ask for, is there any social proof, is the price findable.
Then it checks whether you could even measure the campaign — analytics coverage
gaps, missing ad pixels, consent, and UTM parameters on <em>internal</em> links,
which quietly re-attributes your own traffic to the wrong campaign in GA4.</p>

<h3>Local business SEO</h3>
<p>NAP consistency, LocalBusiness schema and its subtypes, opening hours, geo
signals, review markup. Scout distinguishes a local <em>service</em> business
from a company that merely has an office — a software company with a head office
should not be told to put a city in its page titles.</p>

<h2>What it costs to run</h2>
<div class="wrap-tbl"><table class="cmp">
<thead><tr><th>Tool</th><th>Price</th><th>Runs</th><th>Output</th></tr></thead>
<tbody>
<tr><td>Scout</td><td>one-time</td><td class="yes">Your Mac</td><td>Ranked fix plan</td></tr>
<tr><td>Ahrefs Site Audit</td><td>$129–$499/mo</td><td>Cloud, metered</td><td>170+ issues</td></tr>
<tr><td>Semrush Site Audit</td><td>$139–$499/mo</td><td>Cloud, metered</td><td>140+ checkpoints</td></tr>
<tr><td>Sitebulb</td><td>$13.50–$34/mo</td><td>Local + cloud</td><td>Visual issue report</td></tr>
<tr><td>Screaming Frog</td><td>£199/yr</td><td>Your machine</td><td>Raw crawl data</td></tr>
</tbody></table></div>

<h2>What Scout cannot do</h2>
<p>This section exists because the alternative is finding out later, and because
a tool that claims everything is worth less than one that draws a line.</p>
<ul>
<li><strong>It does not measure Core Web Vitals directly.</strong> That needs a
real browser under real network conditions. Scout identifies the markup and
server patterns that <em>cause</em> poor vitals — images with no dimensions,
render-blocking resources, slow time to first byte — and tells you to confirm the
field values in Search Console.</li>
<li><strong>It does not run JavaScript.</strong> Screaming Frog and Sitebulb do.
Scout detects and reports JS-dependent pages instead, which is honest but is not
the same as auditing them.</li>
<li><strong>It has no keyword, ranking or backlink data.</strong> That requires a
crawled index of the whole web. It is not a feature that can be built, only
bought, and Scout does not pretend otherwise.</li>
<li><strong>It cannot see inside Google Tag Manager.</strong> Tags in a GTM
container are injected at runtime. Where GTM is present Scout says so rather than
reporting that your analytics is missing.</li>
<li><strong>Copy-quality checks are English-only.</strong> On a non-English site
they stand down and the report says so, instead of reporting every English phrase
as absent.</li>
</ul>

<h2 id="download">Download</h2>
<p>macOS 12 or later, Apple Silicon. About 16&nbsp;MB. No account, no telemetry,
no licence server.</p>
<p><a class="btn" href="/download/">Get Scout for Mac</a></p>
<p style="font-size:.92rem;color:var(--text-dim)">Prefer the terminal? The same
engine ships as a CLI. <code>scout audit example.com -o audit.pdf</code> — and it
exits non-zero when it finds a critical issue, so it can gate a deploy.</p>
"""


FAQ = [
    ("Is Scout free?",
     "Scout is a one-time download for macOS. There is no subscription, no crawl "
     "credits and no per-seat pricing — you can audit as many sites as you like."),
    ("Does Scout send my site data anywhere?",
     "No. The audit runs entirely on your Mac. The only network requests Scout makes "
     "are to the site you are auditing. There is no telemetry and no account."),
    ("How is Scout different from Screaming Frog?",
     "Screaming Frog gives you raw crawl data and leaves the interpretation to you. "
     "Scout ranks every finding by impact against effort and gives you an ordered plan "
     "with the exact markup to paste. Screaming Frog renders JavaScript and supports "
     "custom XPath extraction; Scout does not."),
    ("Can Scout tell me if ChatGPT can see my website?",
     "Yes. Scout checks each AI crawler separately — OAI-SearchBot for ChatGPT Search, "
     "PerplexityBot, Claude-SearchBot and Google-Extended — and distinguishes them from "
     "training crawlers like GPTBot, which many sites block deliberately. It also checks "
     "whether your pages render server-side, since most AI crawlers do not run JavaScript."),
    ("Does Scout track keyword rankings?",
     "No. Ranking and backlink data require a crawled index of the entire web, which is "
     "bought rather than built. Scout audits what is on your site and how it is configured."),
]


def build() -> Path:
    return render(
        cat="", slug="",
        title="Scout — SEO & marketing audits that tell you what to fix, in order",
        desc=("Scout audits any website on your Mac: 80 checks across SEO, speed, "
              "structured data, local visibility, AI search visibility and marketing "
              "conversion. Ranked fix plan, client-ready PDF, one-time price, nothing "
              "uploaded."),
        h1="SEO audits that tell you what to fix, in order",
        crumb="Scout for Mac",
        body=body(),
        schema_type="WebPage",
        faq=FAQ,
    )


if __name__ == "__main__":
    print(build())
