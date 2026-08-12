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
from render import BETA_NOTE, N_CHECKS, PRICE_STR, RELEASE, price, render  # noqa: E402

CTA = """
<div class="callout">
<div class="callout-title">Try it against your own site</div>
<p>Docket is a one-time download for macOS. No account, no crawl credits, and the crawl runs
on your machine. Four optional checks fetch data it cannot produce alone; <code>--offline</code>
turns all four off. <a href="/download/">Download Docket →</a></p>
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

#: What was actually read, and where. Anything not sourced here is not stated as
#: a fact about a competitor on these pages — it is either a concession, or
#: written as a limit of what could be checked.
VERIFIED: dict[str, list[tuple[str, str]]] = {
    "screaming-frog": [
        ('renders with the "integrated Chromium WRS"',
         "https://www.screamingfrog.co.uk/seo-spider/"),
        ('free tier limited to 500 URLs; paid crawl limit "Unlimited", with the maximum '
         '"dependent on allocated memory and storage"',
         "https://www.screamingfrog.co.uk/seo-spider/"),
    ],
    "sitebulb": [
        ('"crawl maps" as an interactive visualisation',
         "https://sitebulb.com/features/"),
        ('"Prioritized Hints" — a prioritised, categorised issue list where each '
         "entry explains the issue and why it matters",
         "https://sitebulb.com/features/"),
    ],
    "ahrefs": [
        ('Site Audit "scans for 170+ issues"', "https://ahrefs.com/site-audit"),
        ("crawl credits are listed per plan — Lite 100,000, Standard 500,000, "
         "Advanced 1,500,000 per month", "https://ahrefs.com/pricing"),
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
        ("the SEO category declares ten scored audits — is-crawlable, "
         "document-title, meta-description, http-status-code, link-text, "
         "crawlable-anchors, robots-txt, image-alt, hreflang and canonical — "
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
         "to audit, and the categories are performance, accessibility, best "
         "practices and SEO",
         "https://developer.chrome.com/docs/lighthouse/overview"),
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
        ('the entry plan is listed at $139/mo, or $117.33/mo billed annually, '
         'and the top standard plan at $549/mo; the entry plan lists '
         '"500 keywords to track daily"',
         "https://www.semrush.com/pricing/"),
        ('Site Audit can "check over 140+ website issues", ordered '
         '"Errors (most harmful to a website) - Warnings (harmful) - '
         'Notices (least harmful)"',
         "https://www.semrush.com/kb/542-site-audit-issues-list"),
        ("the crawl allowance is 20,000 pages per audit on Pro and Guru and "
         "100,000 on Business, against 100,000 / 300,000 / 1,000,000 pages a "
         "month, resetting on the 1st rather than rolling over",
         "https://www.semrush.com/kb/338-how-many-pages-can-i-crawl-in-an-audit"),
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
        ('"The data for the Core Web Vitals report comes from the CrUX report" — '
         "field data from real visitors, reported at the 75th percentile — and "
         '"A URL group without threshold data for both LCP and CLS will not be '
         'on the report"',
         "https://support.google.com/webmasters/answer/9205520"),
        ("how much traffic a page needs before CrUX will report on it is not "
         'published: "An exact number is not disclosed"',
         "https://developer.chrome.com/docs/crux/methodology"),
    ],
}

#: The closing sentence of a verification note. Written for a competitor with a
#: price list and a roadmap, which Search Console has neither of, so that page
#: passes its own.
_DEFAULT_CLOSING = (
    "Products change and pricing changes; if something here has gone out of "
    'date, <a href="/about/">tell us</a> and it will be corrected. Everything '
    "else on this page is a comparison of approach, not a claim about their "
    "roadmap."
)


def _verified_note(key: str, closing: str = _DEFAULT_CLOSING) -> str:
    """A dated, sourced footer for any page making claims about a competitor.

    Rendered rather than remembered, so a claim cannot outlive its check
    quietly. `lint.py` fails the build if a comparison page names a competitor
    and does not carry one of these.
    """
    items = VERIFIED.get(key) or []
    if not items:
        return ""
    checks = "; ".join(
        f'{what} (<a href="{url}" rel="nofollow noopener">source</a>)'
        for what, url in items
    )
    return f"""
<p class="verified-note"><strong>Checked {CHECKED_ON_HUMAN}.</strong> The factual
claims about this product were read from its own pages on that date: {checks}.
{closing}</p>"""


def screaming_frog() -> Path:
    body = f"""
<p class="lede">Screaming Frog is the better tool if you want raw crawl data and know exactly
what to do with it. Docket is the better tool if you want to be told what to fix first. That is
the whole difference, and which one is right depends on how much of the interpretation you
want to do yourself.</p>

<h2>What Screaming Frog does that Docket does not</h2>
<p>Three things, and they are real:</p>
<ul>
<li><strong>Rendering at scale, in the right engine.</strong> Screaming Frog renders with an
integrated Chromium engine across an entire crawl — their page calls it the "integrated
Chromium WRS". Docket renders in WebKit — the engine macOS already ships — and renders a sample, ten
pages by default, enough to answer whether the site is client-rendered and what that costs.
On a large React or Vue site, or for a bug that only appears in Chrome's renderer, Screaming
Frog is the tool.</li>
<li><strong>Custom extraction.</strong> XPath, CSS and regex extraction pulls arbitrary fields
out of a crawl — product prices, author names, whatever you define. Docket has no equivalent.</li>
<li><strong>Scale.</strong> Screaming Frog's paid licence lists no crawl limit; their page says
the maximum "is dependent on allocated memory and storage", with a hybrid engine that spills to
disk for large sites. Docket is bounded by design.</li>
</ul>

<h2>What Docket does that Screaming Frog does not</h2>
<p>Screaming Frog tells you that 412 pages have a short title. It does not tell you whether
that matters more than the noindex it also found, or which to do on Tuesday morning. Reviewers
describe its lack of built-in interpretation as simultaneously its greatest strength and its
most expensive characteristic — the power is proportional to your own skill and your own time.</p>

<p>Docket ranks every finding by impact against effort and sorts them into four phases:
stop the bleeding, quick wins, build, polish. Each finding states what it costs you in plain
language and carries the exact markup to paste.</p>

<p>Beyond the ordering, Docket audits three areas that Screaming Frog's own feature list does
not cover. That is what their page advertises, not proof the tool cannot be made to do it —
their custom extraction is powerful enough that a determined user could build some of this by
hand:</p>
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
<tr><td>AI crawler audit</td><td class="yes">Yes</td><td class="no">Not listed</td></tr>
<tr><td>Conversion audit</td><td class="yes">Yes</td><td class="no">Not listed</td></tr>
<tr><td>Local business SEO</td><td class="yes">Yes</td><td class="no">Not listed</td></tr>
<tr><td>Client-ready PDF</td><td class="yes">Built in</td><td>Export and build it yourself</td></tr>
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
{_verified_note("screaming-frog")}
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
             "sample — ten pages by default. Screaming Frog renders across the whole crawl "
             "in its integrated Chromium engine, which is the better tool for a large "
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

<p>One difference worth drawing out: Docket splits a site into sections itself, inferring them
from URL structure, on the theory that the people who most need the feature will not sit down
and write rules. Sitebulb's features page describes a Custom URL explorer where you choose the
columns, filters and sort — configuring the view rather than having it inferred. That is a
trade, and the report says so: inferred sections are less precise than ones you define.</p>

<h2>Which one to pick</h2>
<p><strong>Choose Sitebulb</strong> if visual reporting is how you sell work, if you need the
architecture graph, if your clients' sites are JavaScript-heavy, or if a team needs shared
access.</p>
<p><strong>Choose Docket</strong> if you want the audit to cover marketing and AI visibility as
well as technical SEO, if you would rather own the tool than rent it, or if you want a report
that is careful about the difference between "we checked and it is fine" and "we could not
check".</p>
{_verified_note("sitebulb")}
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
<p>Ahrefs' Site Audit page says it "scans for 170+ issues". More checks with no ordering is a
bigger pile, and the practical
question is what you do first. Docket ranks by impact against effort and gives you a sequence.</p>

<p>The cloud model also brings metering. Ahrefs' pricing page lists a monthly crawl-credit
allowance per plan — 100,000 on Lite, 500,000 on Standard, 1,500,000 on Advanced — so the audit
you run is shaped partly by what you can afford to spend on it. Docket runs on your machine with
no per-crawl cost, so auditing a client site twice in a day costs nothing.</p>

<p>And three areas are not listed among the checks on Ahrefs' Site Audit page: per-crawler AI
search access, landing-page conversion, and marketing tracking coverage. That is what their page
does and does not advertise, which is not the same as proof the product cannot do it — if you
need one of these, ask them rather than taking this page's word for it.</p>

<h2>Side by side</h2>
<div class="wrap-tbl"><table class="cmp">
<thead><tr><th></th><th>Docket</th><th>Ahrefs</th></tr></thead>
<tbody>
<tr><td>Price</td><td>One-time</td><td>{price("ahrefs-site-audit")}</td></tr>
<tr><td>Keyword &amp; backlink data</td><td class="no">None</td><td class="yes">Its main product</td></tr>
<tr><td>Rank tracking</td><td class="no">No</td><td class="yes">Yes</td></tr>
<tr><td>Crawl limits</td><td class="yes">Your machine, your limits</td><td>Credit-metered by plan</td></tr>
<tr><td>Data location</td><td class="yes">Crawl runs on your Mac; four optional checks fetch data unless <code>--offline</code></td><td>Cloud</td></tr>
<tr><td>Ranked action plan</td><td class="yes">Yes</td><td>Issues by severity</td></tr>
<tr><td>AI crawler audit</td><td class="yes">Per-crawler</td><td>Not listed as per-crawler</td></tr>
<tr><td>Conversion audit</td><td class="yes">Yes</td><td class="no">Not listed</td></tr>
<tr><td>Team access</td><td class="no">Single machine</td><td class="yes">Yes</td></tr>
</tbody></table></div>

<h2>The metering problem, concretely</h2>
<p>Cloud auditing is priced per crawled URL, and that changes how you work in a way that is
easy to miss until you hit it. Ahrefs' entry plan lists 100,000 crawl credits a month. Their
pricing page does not spell out what spends a credit, so the exact arithmetic is theirs to
state, not ours — but a monthly allowance means re-auditing a client site after a fix, then
again after the next fix, draws down a budget that a larger client might need.</p>
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
{_verified_note("ahrefs")}
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
{price("semrush-site-audit")} to you. For a lot of people it is.</p>

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
<li><strong>More than one person.</strong> Seats, shared projects, white-label reports carrying
someone else's logo, dashboards, alerts.</li>
</ul>

<p>Their knowledge base also says Site Audit can "check over 140+ website issues", against
Docket's {N_CHECKS}. A count is a weak measure of an audit and more checks with no ordering is
just a longer list. It is still a larger number, and writing around that would be its own kind
of tell.</p>

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

<h2>Nothing leaves your Mac</h2>
<p>Docket has no account, no sign-in and no telemetry. The crawl runs on your machine and each
run is written to <code>~/.docket/</code> as plain JSON you can diff, script against, or delete.
Four checks reach outside by default and <code>--offline</code> turns all four off.</p>
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
<tr><td>Where the crawl runs</td><td>Your Mac</td><td>Their cloud</td></tr>
<tr><td>Crawl allowance</td><td class="yes">Whatever your machine will do</td><td>20,000–100,000 per audit, metered monthly</td></tr>
<tr><td>Checks</td><td>{N_CHECKS}</td><td class="yes">140+</td></tr>
<tr><td>Output</td><td class="yes">Four phases, impact against effort</td><td>Errors, warnings, notices</td></tr>
<tr><td>Backlink data</td><td class="no">None</td><td class="yes">Yes</td></tr>
<tr><td>Keyword volume &amp; difficulty</td><td class="no">None</td><td class="yes">Yes</td></tr>
<tr><td>Rank tracking</td><td class="no">No</td><td class="yes">500 keywords daily on the entry plan</td></tr>
<tr><td>Trending over time</td><td>Each run kept locally as JSON</td><td class="yes">Charted by issue category</td></tr>
<tr><td>Seats and white-label reports</td><td class="no">No</td><td class="yes">Yes</td></tr>
<tr><td>AI crawler access</td><td class="yes">Per bot, split search from training</td><td class="yes">Per bot</td></tr>
<tr><td>Account required</td><td class="yes">None</td><td>Yes</td></tr>
<tr><td>Runs on</td><td>macOS on Apple Silicon</td><td class="yes">Any browser</td></tr>
</tbody></table></div>

<h2>The arithmetic, and why it flatters Docket</h2>
<p>Semrush's pricing page lists the entry plan at $139 a month, or $117.33 a month billed
annually. Paid monthly that is $1,668 in the first year and the same again in the second. Docket
is {PRICE_STR} once — {RELEASE} is free while it is in beta — which works out at roughly five
weeks of the cheapest Semrush plan.</p>
<p>Then take the flattery back out. That $139 is not the price of a site audit. It is the price
of keyword research, rank tracking and a backlink index, with an audit included. If you use
those three, cancelling to save on the audit saves nothing, because the rest of the platform
still costs $139. The comparison only runs one way: when Site Audit is the tool you open and
the remainder is shelfware.</p>
<p>One caveat we could not resolve and are not going to paper over. Their pricing page currently
sells SEO, Starter, Pro+ and Advanced. Their knowledge base still documents crawl limits under
Pro, Guru and Business. We have not worked out which new name inherits which old allowance, so
read the limits on the plan in front of you rather than trusting the row above.</p>

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
<li>You are on Windows, Linux, or an Intel Mac, where Docket will not start.</li>
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

    return render(
        cat="vs", slug="semrush-site-audit-alternative",
        title="Docket vs Semrush Site Audit: a one-time alternative",
        desc=("Semrush Site Audit is 140+ checks inside a platform from $139/mo. Docket is a "
              "one-time Mac audit with a ranked fix plan. Where Semrush genuinely wins."),
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
             "billed annually, which is $1,668 in a year paid monthly. Docket is " + PRICE_STR
             + " paid once, about five weeks of that plan. The saving is only real if the "
             "site audit is the part of Semrush you use."),
            ("Does Docket have crawl limits like Semrush?",
             "Not monthly ones. Semrush's knowledge base lists 20,000 pages per audit on Pro "
             "and Guru and 100,000 on Business, drawn against 100,000 to 1,000,000 pages a "
             "month depending on plan, resetting on the 1st. Docket crawls on your Mac, so "
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
plus a manual eleventh — <code>structured-data</code> — which carries a weight of zero and
asks you to go and validate your schema somewhere else.</p>

<p><code>is-crawlable</code> is weighted so heavily that failing it fails the category on its
own, and the comment beside it in the config says that is deliberate. Which is the right call.
An accidental <code>noindex</code> is the most expensive mistake in technical SEO, and
Lighthouse finds it in ten seconds for nothing.</p>

<p>The shallowness is stated, not hidden. The description at the top of the category says the
checks follow basic search engine optimisation advice, and that there are many additional
factors Lighthouse does not score which may affect your ranking. That is Google marking the
edge of its own tool, and the useful question is what sits outside the line.</p>

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
<li><strong>Duplicate and templated titles.</strong> <code>document-title</code> asks whether
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
Console's Core Web Vitals report is built from the Chrome UX Report rather than from a lab
run — and why PageSpeed Insights shows two panels, Lighthouse in a simulated environment on
one side and CrUX field data on the other.</p>

<p>Docket has one optional check that fetches those field values from the PageSpeed Insights
API, which is the same CrUX data Search Console shows. It is one of four checks that reach off
your machine, <code>--offline</code> turns them off, and the scope page of every PDF names
Core Web Vitals field values among the things that were not measured. If you are trying to
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
<tr><td>AI crawler access</td><td class="yes">Per crawler</td><td class="no">Not scored</td></tr>
<tr><td>Conversion and copy</td><td class="yes">Yes</td><td class="no">Not scored</td></tr>
<tr><td>Output</td><td>Ranked plan with markup to paste</td><td>Four scores out of 100 and a list</td></tr>
<tr><td>Report</td><td class="yes">Client-ready PDF</td><td>HTML or JSON</td></tr>
<tr><td>Runs on</td><td>Your Mac, no account</td><td class="yes">Chrome, CLI, Node, or the web</td></tr>
</tbody></table></div>

<h2>The order that wastes least time</h2>
<ol>
<li><strong>Lighthouse first, on the page that matters most.</strong> It is free and it takes
ten seconds, and it catches the three faults that stop a page dead: a stray noindex, a
canonical pointing at the wrong URL, a status code that is not 200.</li>
<li><strong>Docket across the whole site.</strong> The cross-page checks, the areas Lighthouse
leaves unscored, and the ordering — findings ranked by impact against effort and sorted into
four phases, each carrying the exact markup to paste.</li>
<li><strong>Search Console once the fix is live.</strong> Field vitals move over a 28-day
window, so the answer to whether it worked is there and nowhere else.</li>
</ol>
<p>These are complementary rather than competing, and the difference fits in a sentence:
Lighthouse grades a page, Docket sequences the work on a site.</p>

<h2>When Lighthouse on its own is enough</h2>
<p>If you run a single landing page, Lighthouse plus a careful read of your own title tags
gets you most of the way, and Docket is a purchase you do not need. If your problem is
speed, Lighthouse is the better tool and this is the wrong page. If you want a score gated in
continuous integration, Lighthouse ships as a Node module built for that and Docket has no
equivalent. And if you are not on an Apple Silicon Mac running macOS 12 or later, Docket will
not run at all.</p>
<p>Docket costs {PRICE_STR} once, runs {N_CHECKS} checks on your own machine with no account,
no licence check and no telemetry, and keeps everything under <code>~/.docket</code>.
{RELEASE} is free while it is in beta. It earns that money against a free tool from Google in
one situation only: when the question has stopped being how fast is this page and become which
of forty things do I do first.</p>
{_verified_note("lighthouse")}
{CTA}"""

    return render(
        cat="vs", slug="lighthouse-alternative",
        title="Docket vs Google Lighthouse: what its SEO score covers",
        desc=("Lighthouse is free, from Google, and the authority on lab Core Web Vitals. "
              "Its SEO category is ten scored checks on one URL. What sits outside it."),
        h1="Docket vs Google Lighthouse",
        crumb='<a href="/">Docket</a> / <a href="/vs/">Compare</a> / Lighthouse',
        body=body,
        faq=[
            ("Does Docket measure Core Web Vitals?",
             "Not itself. Docket measures the causes — server response time, compression and "
             "caching headers, page weight, render-blocking resources, image formats, redirect "
             "latency and layout-shift risk in the markup — and one optional check fetches the "
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
             "what breaks a site is a relationship between pages — hreflang return tags, "
             "canonical clusters, duplicate titles, click depth — and a single-page run cannot "
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
<p class="lede">Search Console is free, it is Google's own data, and no audit tool replaces
it — this one included. It is the single source of the queries your site actually appeared for,
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
indexed, is simply absent — and absence is usually the case you were trying to debug.</li>
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

<p>Docket crawls the site as it stands right now and runs {N_CHECKS} checks — technical SEO,
copy, page speed, structured data, local visibility, AI search access and marketing
conversion — then ranks every finding by impact against effort and sorts them into four phases.
Each finding states what it costs you in plain language and carries the exact markup to paste.
It writes a client-ready PDF and can score you against a named competitor. The crawl runs on
your Mac: no account, no telemetry, results in <code>~/.docket</code>.</p>

<p>The difference is time-shape more than feature list. Search Console answers questions about
last week, on pages Google has met. Docket answers a question about this minute, on every page
you have — including the one you published an hour ago.</p>

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
<tr><td>Where does my site's data end up?</td><td>Google's servers</td><td>Your Mac, in <code>~/.docket</code></td></tr>
</tbody></table></div>

<p>Deliberately no green ticks and red crosses in that table. Nine of those rows are not a
scoreboard; they are two instruments pointed at different things, and colouring Google's cells
red would be the dishonesty this page opened by refusing.</p>

<p>On cost: Search Console is free and has never been anything else. Docket is
{PRICE_STR} paid once. {BETA_NOTE}</p>

<h2>Where Docket defers: Core Web Vitals</h2>

<p><strong>Docket does not measure Core Web Vitals.</strong> Its speed checks are causes —
render-blocking resources, uncompressed images, page weight — and a cause is not a metric. The
metrics come from real visitors, which is why Search Console builds that report from CrUX rather
than from a lab run. Docket has one optional check that fetches the same CrUX values through the
PageSpeed Insights API; it is one of four checks that reach off your machine, and
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

    return render(
        cat="vs", slug="google-search-console",
        title="Docket vs Google Search Console: what each answers",
        desc=("Search Console is free, it is Google's own data, and nothing replaces it. What "
              "it cannot tell you, and where a crawl on your own Mac answers instead."),
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
             "four optional checks that --offline turns off. The authoritative view is Google's "
             "and it is in Search Console. Confirm a speed fix there, not in Docket."),
            ("Is the URL Inspection tool enough to audit a site?",
             "Not at any scale. It inspects one URL at a time, and Google documents the API "
             "quota as 2,000 queries a day and 600 a minute per property. A site larger than "
             "that cannot be inspected in a day, and inspection reports indexing status rather "
             "than telling you what to change."),
        ],
    )


BUILDERS = [screaming_frog, sitebulb, ahrefs, semrush, lighthouse, search_console]


def build_all() -> list[Path]:
    return [b() for b in BUILDERS]


if __name__ == "__main__":
    for p in build_all():
        print(p)
