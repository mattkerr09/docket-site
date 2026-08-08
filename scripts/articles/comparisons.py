#!/usr/bin/env python3
"""Competitor comparisons.

Each page is authored, not templated. The strategy doc's rule applies: a
format-comparison page and a philosophy-comparison page should not share six
headings, and every page must name at least one thing the competitor does
better. A comparison that never concedes anything reads as marketing, and both
readers and models discount it.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from render import price, render  # noqa: E402

CTA = """
<div class="callout">
<div class="callout-title">Try it against your own site</div>
<p>Docket is a one-time download for macOS. No account, no crawl credits, and the audit runs
entirely on your machine. <a href="/download/">Download Docket →</a></p>
</div>"""


def screaming_frog() -> Path:
    body = f"""
<p class="lede">Screaming Frog is the better tool if you want raw crawl data and know exactly
what to do with it. Docket is the better tool if you want to be told what to fix first. That is
the whole difference, and which one is right depends on how much of the interpretation you
want to do yourself.</p>

<h2>What Screaming Frog does that Docket does not</h2>
<p>Three things, and they are real:</p>
<ul>
<li><strong>Rendering at scale, in the right engine.</strong> Screaming Frog runs headless
Chrome across an entire crawl, with configurable wait strategies and JavaScript error
capture. Docket renders in WebKit — the engine macOS already ships — and renders a sample, ten
pages by default, enough to answer whether the site is client-rendered and what that costs.
On a large React or Vue site, or for a bug that only appears in Chrome's renderer, Screaming
Frog is the tool.</li>
<li><strong>Custom extraction.</strong> XPath, CSS and regex extraction pulls arbitrary fields
out of a crawl — product prices, author names, whatever you define. Docket has no equivalent.</li>
<li><strong>Scale.</strong> Screaming Frog will crawl millions of URLs given the memory. Docket
is bounded by design.</li>
</ul>

<h2>What Docket does that Screaming Frog does not</h2>
<p>Screaming Frog tells you that 412 pages have a short title. It does not tell you whether
that matters more than the noindex it also found, or which to do on Tuesday morning. Reviewers
describe its lack of built-in interpretation as simultaneously its greatest strength and its
most expensive characteristic — the power is proportional to your own skill and your own time.</p>

<p>Docket ranks every finding by impact against effort and sorts them into four phases:
stop the bleeding, quick wins, build, polish. Each finding states what it costs you in plain
language and carries the exact markup to paste.</p>

<p>Beyond the ordering, Docket audits three areas Screaming Frog has no coverage of at all:</p>
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
<tr><td>Runs on</td><td>Your Mac</td><td>Your machine</td></tr>
<tr><td>Output</td><td>Ranked plan with fixes</td><td>Spreadsheet of crawl data</td></tr>
<tr><td>JavaScript rendering</td><td class="yes">Sampled, via WebKit</td><td class="yes">Yes, every page</td></tr>
<tr><td>Custom XPath extraction</td><td class="no">No</td><td class="yes">Yes</td></tr>
<tr><td>hreflang reciprocity</td><td class="yes">Yes</td><td class="yes">Yes</td></tr>
<tr><td>AI crawler audit</td><td class="yes">Yes</td><td class="no">No</td></tr>
<tr><td>Conversion audit</td><td class="yes">Yes</td><td class="no">No</td></tr>
<tr><td>Local business SEO</td><td class="yes">Yes</td><td class="no">No</td></tr>
<tr><td>Client-ready PDF</td><td class="yes">Built in</td><td>Export and build it yourself</td></tr>
<tr><td>Scheduled re-audits</td><td class="yes">Yes</td><td>Scheduling in the paid tier</td></tr>
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
nobody on the team chose — and the page source looks fine.</li>
</ul>
<p>Docket's robots.txt parser also does full longest-match resolution with <code>*</code> and
<code>$</code> support, which matters more than it sounds: the near-universal
<code>Disallow: /wp-admin/</code> plus <code>Allow: /wp-admin/admin-ajax.php</code> pair is
judged wrongly by any parser that resolves rules in order.</p>

<h2>Which one to pick</h2>
<p><strong>Choose Screaming Frog</strong> if you are a technical SEO, your sites are
JavaScript-heavy, you need custom extraction, or you are crawling hundreds of thousands of
URLs. It is the deeper instrument and its price-to-power ratio is unmatched.</p>
<p><strong>Choose Docket</strong> if you need to hand someone a plan rather than a dataset, if
you care about AI search visibility or whether your landing pages convert, or if you want a
client-ready PDF without building one.</p>
<p>They are not mutually exclusive, and plenty of people will want both.</p>
{CTA}"""

    return render(
        cat="vs", slug="screaming-frog-alternative",
        title="Docket vs Screaming Frog: which SEO crawler should you use?",
        desc=("Screaming Frog gives you raw crawl data; a Docket audit gives a ranked fix plan. "
              "Including what Screaming Frog does better — rendering at scale, custom "
              "extraction."),
        h1="Docket vs Screaming Frog",
        crumb='<a href="/">Docket</a> / <a href="/vs/">Compare</a> / Screaming Frog',
        body=body,
        faq=[
            ("Is Docket a Screaming Frog alternative?",
             "For prioritisation, reporting and non-technical users, yes. For JavaScript "
             "custom XPath extraction, rendering at scale and very large crawls, no — "
             "Screaming Frog does those better and Docket does not try to."),
            ("Does Docket render JavaScript like Screaming Frog?",
             "Yes, through a WebKit helper, though it is off by default and renders a "
             "sample — ten pages by default. Screaming Frog renders every page in headless "
             "Chrome with configurable wait strategies, which is the better tool for a large "
             "single-page application."),
        ],
    )


def sitebulb() -> Path:
    body = f"""
<p class="lede">Sitebulb and Docket are aiming at the same problem from different sides.
Sitebulb turns crawl data into visual reports an agency can present. Docket turns it into an
ordered list of work. If you need a diagram of your site architecture, Sitebulb wins outright.
If you need to know what to do on Monday, Docket is more direct about it.</p>

<h2>Sitebulb's real advantage: you can see the site</h2>
<p>Sitebulb's architecture graph is the strongest thing either tool has that the other does
not. It draws the site as an interactive map — isolated content clusters, pages buried too
deep, link equity pooling in the wrong places. Some structural problems are genuinely easier
to see than to read, and a client will understand a picture of their own site faster than a
table about it.</p>
<p>Docket computes the same underlying link graph and does not draw it. That is an open gap and
it is on the roadmap; until it ships, this is a straightforward reason to choose Sitebulb.</p>

<h2>Where Docket is more useful</h2>
<p>Sitebulb prioritises issues and explains them in plain English, which is why it is the
friendlier of the two established crawlers. The remaining complaint in reviews is that its
hints still need experienced judgement to filter — particularly on large or programmatic
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
<tr><td>Runs on</td><td>Your Mac</td><td>Desktop or cloud</td></tr>
<tr><td>Site architecture visualisation</td><td class="yes">Rings by depth, sized by equity</td><td class="yes">Interactive force-directed map</td></tr>
<tr><td>JavaScript rendering</td><td class="yes">Sampled, via WebKit</td><td class="yes">Yes, every page</td></tr>
<tr><td>Team collaboration</td><td class="no">Single machine</td><td class="yes">Cloud tier</td></tr>
<tr><td>Ranked action plan</td><td class="yes">Four phases</td><td>Prioritised hints</td></tr>
<tr><td>AI search visibility</td><td class="yes">Yes</td><td class="no">No</td></tr>
<tr><td>Conversion &amp; tracking audit</td><td class="yes">Yes</td><td class="no">No</td></tr>
<tr><td>Local business SEO</td><td class="yes">Yes</td><td class="no">No</td></tr>
<tr><td>Section-by-section scoring</td><td class="yes">Inferred automatically</td><td>Segments you define</td></tr>
</tbody></table></div>

<p>One difference worth drawing out: both tools score sections of a site separately, but
Sitebulb has you define the segments. Docket infers them from URL structure, on the theory that
the people who most need the feature will not sit down and write segment rules. That is a
trade — inferred sections are less precise than defined ones, and the report says so.</p>

<h2>Which one to pick</h2>
<p><strong>Choose Sitebulb</strong> if visual reporting is how you sell work, if you need the
architecture graph, if your clients' sites are JavaScript-heavy, or if a team needs shared
access.</p>
<p><strong>Choose Docket</strong> if you want the audit to cover marketing and AI visibility as
well as technical SEO, if you would rather own the tool than rent it, or if you want a report
that is careful about the difference between "we checked and it is fine" and "we could not
check".</p>
{CTA}"""

    return render(
        cat="vs", slug="sitebulb-alternative",
        title="Docket vs Sitebulb: visual reports or a ranked plan? (2026)",
        desc=("Sitebulb draws your site architecture and Docket does not — a real reason to "
              "pick it. Where Docket wins: AI visibility, conversion, and stated limits."),
        h1="Docket vs Sitebulb",
        crumb='<a href="/">Docket</a> / <a href="/vs/">Compare</a> / Sitebulb',
        body=body,
        faq=[
            ("Does Docket have site architecture visualisation like Sitebulb?",
             "Both do. Docket draws a deterministic picture — pages in rings by click depth, sized "
             "by link equity. Sitebulb's "
             "architecture map is its strongest feature and a legitimate reason to choose it."),
            ("Is Docket cheaper than Sitebulb?",
             "Docket is a one-time download; Sitebulb is " + price("sitebulb") + ". Over a year the "
             "difference is substantial, but Sitebulb's cloud tier offers team collaboration "
             "that Docket, being single-machine by design, does not."),
        ],
    )


def ahrefs() -> Path:
    body = f"""
<p class="lede">Ahrefs Site Audit is one module of a keyword and backlink platform. Docket is
only an auditor. If you need keyword volumes and a backlink index, Docket cannot replace Ahrefs
and does not try — that data has to be bought, not built. If the site audit is the part you
actually use, you are paying {price("ahrefs-site-audit")} for it.</p>

<h2>What Ahrefs has that Docket can never have</h2>
<p>A crawled index of the web. That is what powers keyword difficulty, search volume, backlink
profiles, and competitor content gaps. Building it costs tens of millions of dollars a year in
infrastructure. Docket audits what is on your site and how it is configured; it has no opinion
about what people search for, and any tool claiming otherwise without an index behind it is
guessing.</p>

<p>Ahrefs also crawls in the cloud, which matters if you want scheduled audits running while
your laptop is closed, or a team looking at the same data.</p>

<h2>Where the audit itself differs</h2>
<p>Ahrefs lists 170+ checks. More checks with no ordering is a bigger pile, and the practical
question is what you do first. Docket ranks by impact against effort and gives you a sequence.</p>

<p>The cloud model also brings metering. Ahrefs crawls are credit-limited by plan, which means
the audit you run is shaped partly by what you can afford to spend on it. Docket runs on your
machine with no per-crawl cost, so auditing a client site twice in a day costs nothing.</p>

<p>And three areas are simply absent from Ahrefs' audit: per-crawler AI search access,
landing-page conversion, and marketing tracking coverage.</p>

<h2>Side by side</h2>
<div class="wrap-tbl"><table class="cmp">
<thead><tr><th></th><th>Docket</th><th>Ahrefs</th></tr></thead>
<tbody>
<tr><td>Price</td><td>One-time</td><td>{price("ahrefs-site-audit")}</td></tr>
<tr><td>Keyword &amp; backlink data</td><td class="no">None</td><td class="yes">Its main product</td></tr>
<tr><td>Rank tracking</td><td class="no">No</td><td class="yes">Yes</td></tr>
<tr><td>Crawl limits</td><td class="yes">Your machine, your limits</td><td>Credit-metered by plan</td></tr>
<tr><td>Data location</td><td class="yes">Never leaves your Mac</td><td>Cloud</td></tr>
<tr><td>Ranked action plan</td><td class="yes">Yes</td><td>Issues by severity</td></tr>
<tr><td>AI crawler audit</td><td class="yes">Per-crawler</td><td>Partial</td></tr>
<tr><td>Conversion audit</td><td class="yes">Yes</td><td class="no">No</td></tr>
<tr><td>Team access</td><td class="no">Single machine</td><td class="yes">Yes</td></tr>
</tbody></table></div>

<h2>The metering problem, concretely</h2>
<p>Cloud auditing is priced per crawled URL, and that changes how you work in a way that is
easy to miss until you hit it. On Ahrefs' entry plan the monthly crawl allowance is consumed
by every audit you run — so re-auditing a client site after a fix, then again after the next
fix, costs you budget that a larger client might need.</p>
<p>The practical effect is that people run fewer audits than they should. You verify a change
once rather than iterating, and you hesitate before crawling a prospect's site to win the
work. Docket has no equivalent constraint: the crawl happens on your laptop, so running it
twenty times in an afternoon costs nothing but time. For agencies doing pre-sales audits that
difference compounds quickly.</p>
<p>The reverse is also true and worth stating. Because Docket runs locally, closing the laptop
stops a scheduled audit, and there is no shared workspace for a team to look at the same
results. If either of those matters, cloud is the right architecture and the metering is what
you pay for it.</p>

<h2>The honest recommendation</h2>
<p>These tools do not substitute for each other. If you do keyword research and link building,
you need an index, and Ahrefs or Semrush is how you get one. If what you need is a technical
and marketing audit with a plan attached, Docket does that for a one-time cost and never sends
your data anywhere.</p>
<p>Plenty of people run both: an index tool for research, and a local auditor for the work.</p>
{CTA}"""

    return render(
        cat="vs", slug="ahrefs-site-audit-alternative",
        title="Docket vs Ahrefs Site Audit: what you get for $129/mo (2026)",
        desc=("Ahrefs Site Audit is one module of a keyword and backlink platform. Docket is a "
              "one-time local auditor with a ranked fix plan. What each actually does."),
        h1="Docket vs Ahrefs Site Audit",
        crumb='<a href="/">Docket</a> / <a href="/vs/">Compare</a> / Ahrefs',
        body=body,
        faq=[
            ("Can Docket replace Ahrefs?",
             "Only for the site audit. Ahrefs' keyword volumes, difficulty scores and backlink "
             "data come from a crawled index of the web, which Docket has no equivalent of and "
             "does not claim to."),
            ("Does Docket have crawl limits like Ahrefs?",
             "No. Docket runs on your machine, so there are no crawl credits and no per-audit "
             "cost. The only limits are the page and depth caps you set."),
        ],
    )


BUILDERS = [screaming_frog, sitebulb, ahrefs]


def build_all() -> list[Path]:
    return [b() for b in BUILDERS]


if __name__ == "__main__":
    for p in build_all():
        print(p)
