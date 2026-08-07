#!/usr/bin/env python3
"""Download, legal and audience/how-to hubs.

Built because Scout audited its own site and found the links to these pages were
broken. Dogfooding caught it in the first run, which is the argument for the
product in miniature.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from render import DMG, DMG_SIZE, N_CHECKS, RELEASE, render  # noqa: E402


def download() -> Path:
    body = f"""
<p class="lede">Scout is a single download for macOS 12 or later on Apple Silicon.
{DMG_SIZE}. There is no account to create, no licence server to phone, and no telemetry.</p>

<p><a class="btn btn-lg" href="{DMG}">Download Scout {RELEASE} for Mac</a></p>
<p style="font-size:.92rem;color:var(--text-dim)">Apple Silicon · macOS 12+ · {DMG_SIZE} ·
<a href="https://github.com/mattkerr09/scout-site/releases">all releases</a></p>

<h2>Opening it</h2>
<p>Double-click it. Scout is signed with a Developer&nbsp;ID and notarised by Apple, so
macOS opens it without a security warning and without any of the right-click or Terminal
workarounds that unsigned software needs.</p>

<h2>What happens on first launch</h2>
<p>Scout opens, starts its local audit engine, and shows a single field. Type a domain, press
Run audit, and watch it crawl. There is no onboarding, no project setup and no plan selection,
because none of those are necessary for the thing you came to do.</p>
<p>The first launch takes a few seconds longer than later ones while the engine unpacks
itself. There is no security prompt to get past: the app is notarised, so macOS verifies it
with Apple and opens it.</p>

<h2>The command line</h2>
<p>The same engine ships as a CLI inside the app bundle. It is the whole product, not a
cut-down version:</p>
<pre><code>scout audit example.com
scout audit example.com -o audit.pdf -n 500
scout audit example.com -f json --no-pages | jq '.score.overall'
scout checks</code></pre>
<p><code>scout audit</code> exits with status 2 when it finds a critical issue, so it can gate
a deployment. Running it in CI against a staging URL will fail the build if someone ships a
<code>noindex</code>, which is a mistake that otherwise gets found weeks later by a traffic
graph.</p>

<h2>Requirements and limits</h2>
<ul>
<li><strong>macOS 12 or later, Apple Silicon.</strong> There is no Intel or Windows build.</li>
<li><strong>An internet connection to the site you are auditing.</strong> Nothing else.</li>
<li><strong>Crawls are bounded</strong> by page count, depth, wall-clock time and response
size. The defaults are deliberately polite; you can raise them.</li>
</ul>

<h2>What happens to your data</h2>
<p>Nothing leaves the machine. The only network requests Scout makes are to the site being
audited, and it identifies itself honestly in its user-agent rather than impersonating
Googlebot — a spoofed user-agent gets a different, sometimes cloaked response, which would
make every finding a lie.</p>
<p>Audit history is stored in <code>~/.scout/</code> as plain JSON. Delete the folder and it
is gone.</p>
"""
    return render(
        cat="download", slug="",
        title="Download Scout for Mac — SEO & marketing audits, one-time",
        desc=("Scout for macOS 12+ on Apple Silicon. 18 MB, no account, no telemetry. "
              "Includes the CLI, which exits non-zero on a critical issue so it can gate a "
              "deploy."),
        h1="Download Scout for Mac",
        crumb='<a href="/">Scout</a> / Download',
        body=body,
        schema_type="WebPage",
    )


def for_hub() -> Path:
    body = f"""
<p class="lede">The same {N_CHECKS} checks run on every site, but which findings matter most changes a
lot by who you are. These pages cover what to look at first.</p>

<h3><a href="/for/agencies/">For SEO agencies</a></h3>
<p>Unlimited client audits with no per-seat or per-crawl cost, and a client-ready PDF that does
not need rebuilding in a deck.</p>

<h3><a href="/for/local-business/">For local businesses</a></h3>
<p>Why you are not in the map pack — LocalBusiness schema, NAP consistency, and the geo
signals that decide "near me" results.</p>

<h3>More coming</h3>
<p>Ecommerce, SaaS and in-house marketing pages are being written. Rather than publish three
thin variations of the same article now, they will appear when each has something specific to
say — near-duplicate pages are the actual flag risk in a programmatic set, not thin ones.</p>
"""
    return render(
        cat="for", slug="",
        title="Scout for agencies, local businesses and marketers",
        desc="Which findings matter most depending on who you are — agencies, local businesses, and more.",
        h1="Scout for your situation",
        crumb='<a href="/">Scout</a> / For you',
        body=body,
        schema_type="CollectionPage",
    )


def for_agencies() -> Path:
    body = """
<p class="lede">The cost that hurts an agency is not the licence — it is the per-seat and
per-crawl metering that makes you think twice before auditing a prospect. Scout is a one-time
download that runs on your machine, so a pre-sales audit costs you nothing but the ten minutes
it takes.</p>

<h2>The pre-sales audit problem</h2>
<p>Cloud SEO platforms meter crawls. That is a reasonable way to price infrastructure, and it
has a predictable effect on behaviour: you ration audits. You crawl a prospect's site once
rather than properly, you skip the re-crawl that would verify a fix, and you hesitate before
running a speculative audit on a lead that may not convert.</p>
<p>Running locally removes the calculation entirely. Audit every lead. Audit them again after
the pitch. Audit a competitor's site to show the client the gap.</p>

<h2>The report is the deliverable</h2>
<p>Scout's PDF is designed to be sent, not rebuilt. It opens with a score and a one-sentence
verdict a client can act on, then a scorecard by area, then the ranked plan — each item with
what it costs the client in plain language and the exact markup their developer needs.</p>
<p>There is also a scope page, and it is there on purpose. It states how many pages were
crawled, what was measured, and explicitly what was not — Core Web Vitals field values,
JavaScript-rendered content, anything inside a tag manager. A report that quietly implies full
coverage is the one that gets you a difficult question in month three.</p>

<h2>Monitoring turns an audit into a retainer</h2>
<p>Save a client site and Scout re-audits it on a schedule, then tells you what changed since
last time: issues that appeared, issues that were resolved, and the score movement per area.
Regressions surface first, because a site that was clean and broke is the thing you need to
know about — a check that has been failing for six months is not news.</p>
<p>That changes the conversation from "here is another audit" to "your developer shipped a
noindex on the pricing page on Tuesday", which is a materially different meeting.</p>

<h2>Competitor comparison for pitches</h2>
<p>Attach competitor URLs to a client site and Scout audits them on the same settings, then
shows where the client leads and trails area by area — plus the issues <em>every</em>
competitor has already fixed. That last list is the most persuasive artefact in the tool,
because it converts "you should do this" into "everyone you compete with already did".</p>

<h2>Handing the fix list to a developer</h2>
<p>The friction in agency SEO is rarely finding the problem — it is getting it fixed by someone
who does not report to you. A developer handed "improve your structured data" will deprioritise
it forever. A developer handed a complete, valid JSON-LD block with the client's own address
already in the right fields will paste it in the same afternoon.</p>
<p>That is why every finding carries the change rather than the category, and why the CSV
export exists: it drops straight into a Jira or Linear import without anyone retyping it.</p>

<h2>What to tell clients it cannot do</h2>
<p>Say it early rather than being asked. Scout has no per-page backlink or anchor-text data
and no search volumes — you will still need an index tool for keyword research. Rendering is
available but off by default and samples the shallowest pages, so a very large single-page
application still wants a dedicated rendering crawl.</p>
<p>Being straight about the boundary is also, in practice, a good sales posture. A tool that
claims everything invites the client to test the claim.</p>

<p><a class="btn" href="/download/">Download Scout</a></p>
"""
    return render(
        cat="for", slug="agencies",
        title="Scout for SEO agencies: unlimited client audits, one-time cost (2026)",
        desc=("Per-crawl metering makes agencies ration audits. Scout runs locally with no "
              "per-seat or per-crawl cost, produces a client-ready PDF, and turns scheduled "
              "re-audits into a retainer conversation."),
        h1="Scout for SEO agencies",
        crumb='<a href="/">Scout</a> / <a href="/for/">For you</a> / Agencies',
        body=body,
        faq=[
            ("Can I use Scout for client work?",
             "Yes. Scout is a one-time download with no per-seat or per-crawl limits, so you "
             "can audit as many client and prospect sites as you like."),
            ("Can I white-label the report?",
             "The PDF is Scout-branded. The CSV and JSON exports carry no branding and can be "
             "dropped into your own template."),
        ],
    )


def for_local() -> Path:
    body = """
<p class="lede">If you serve customers in a place, the map pack is your organic search. It is
decided by a small set of signals that are mostly under your control, and the most common
reason a business is missing from it is a schema mistake nobody has ever looked at.</p>

<h2>The four things that decide local visibility</h2>

<h3>1. Your business type in schema</h3>
<p>The single most common error we see is a business that publishes a complete, correct address
in structured data while declaring itself a generic <code>Organization</code>. Local pack
results, map placement and the open/closed label are driven by <code>LocalBusiness</code> and
its subtypes — <code>Plumber</code>, <code>Dentist</code>, <code>Restaurant</code>,
<code>Attorney</code>. A plain <code>Organization</code> does not qualify for any of them.</p>
<p>It is a one-word fix and we have found it on national franchises.</p>

<h3>2. NAP consistency</h3>
<p>Name, address and phone have to be byte-identical everywhere they appear — on your site and
on your Google Business Profile. "St" on one and "Street" on the other, or two variations of
the same phone number, weakens the match between your website and your listing. Google is
trying to decide whether these two things describe one business, and every inconsistency makes
that harder.</p>

<h3>3. Location in the places that rank</h3>
<p>Local searches are overwhelmingly "&lt;service&gt; in &lt;place&gt;" or "&lt;service&gt;
near me". If no page title on your site names the place you serve, you are not competing for
those searches at all. The fix is unglamorous: put the city in the titles of your homepage and
main service pages.</p>
<p>Scout only gives this advice to businesses that actually compete locally. A software company
with a head office publishes an address too, and telling it to put a city in its titles would
make them worse — so the check distinguishes a local <em>service</em> business from a company
that merely has premises.</p>

<h3>4. Reviews, and marking them up</h3>
<p>Review volume and recency are among the strongest local ranking factors, and increasingly
they are what an AI assistant leans on when it recommends a business. If you display reviews
without <code>Review</code> or <code>AggregateRating</code> markup they cannot appear as stars
in search results.</p>
<p>One warning: the markup has to match what the page actually shows. Rating markup on a page
with no visible reviews is a policy violation that can cost you every rich result on the site,
not just that one.</p>

<h2>The things people fix that do not matter much</h2>
<p>Meta keywords do nothing. Neither does keyword density. Submitting to a hundred directories
mostly generates inconsistent NAP data, which actively hurts. If you have limited time, the
four items above are where it goes.</p>

<h2>What to check today</h2>
<ol>
<li>Is your phone number a <code>tel:</code> link? Most local searches happen on a phone, and
plain text turns a one-tap call into a copy-and-paste.</li>
<li>Does your homepage carry <code>LocalBusiness</code> schema with the right subtype, an
address, opening hours and a <code>sameAs</code> link to your Google Business Profile?</li>
<li>Does any page title name your city?</li>
</ol>
<p>Scout checks all of these and tells you which of your business's specific signals are
missing. <a href="/download/">Download it</a> and run one audit — it takes a few minutes.</p>
"""
    return render(
        cat="for", slug="local-business",
        title="Local SEO audit: why you are not in the map pack (2026)",
        desc=("The four signals that decide local visibility — LocalBusiness schema and its "
              "subtypes, NAP consistency, geo targeting and review markup — and the one-word "
              "schema mistake we find on national franchises."),
        h1="Why your business is not in the map pack",
        crumb='<a href="/">Scout</a> / <a href="/for/">For you</a> / Local business',
        body=body,
        faq=[
            ("Why is my business not showing in Google Maps?",
             "The most common technical causes are missing or incorrectly typed LocalBusiness "
             "schema, inconsistent name/address/phone data between your site and your Google "
             "Business Profile, no location named in page titles, and too few recent reviews."),
            ("What is the difference between Organization and LocalBusiness schema?",
             "LocalBusiness and its subtypes qualify for local pack results, map placement and "
             "the open/closed label. A generic Organization does not, even when it publishes a "
             "full address."),
        ],
    )


def howto_hub() -> Path:
    body = """
<p class="lede">Fix guides for the specific problems Scout reports. Each one explains what the
issue costs you, then gives the change to make.</p>

<h3><a href="/how-to/fix-ai-crawler-access/">Fix AI crawler access in robots.txt</a></h3>
<p>How to let ChatGPT, Perplexity and Claude read your site without giving away training data —
they are separate decisions and need separate rules.</p>

<h3>More coming</h3>
<p>Guides for hreflang return tags, conflicting canonicals, soft 404s and structured data
errors are being written. They will appear as each is written properly rather than as
variations on a template.</p>
"""
    return render(
        cat="how-to", slug="",
        title="How to fix common SEO problems — Scout",
        desc="Fix guides for the specific issues Scout reports, with the exact change to make.",
        h1="Fix guides",
        crumb='<a href="/">Scout</a> / Fix it',
        body=body,
        schema_type="CollectionPage",
    )


def howto_ai_access() -> Path:
    body = """
<p class="lede">To let AI assistants cite you while keeping your content out of model training,
you need separate robots.txt rules for the search crawlers and the training crawlers. Most
sites that try this end up blocking both, because the user-agent names do not make the
difference obvious.</p>

<h2>Which crawler does what</h2>
<p>Each AI company runs at least two, and they serve different purposes:</p>
<div class="wrap-tbl"><table class="cmp">
<thead><tr><th>Crawler</th><th>Purpose</th><th>Block it if…</th></tr></thead>
<tbody>
<tr><td><code>OAI-SearchBot</code></td><td>Builds ChatGPT Search's index</td><td>You do not want to appear in ChatGPT</td></tr>
<tr><td><code>GPTBot</code></td><td>Collects training data</td><td>You do not want your content in model weights</td></tr>
<tr><td><code>ChatGPT-User</code></td><td>Fetches a page when a user asks about it</td><td>Rarely — this is a user acting on your behalf</td></tr>
<tr><td><code>PerplexityBot</code></td><td>Builds Perplexity's index</td><td>You do not want to appear in Perplexity</td></tr>
<tr><td><code>Claude-SearchBot</code></td><td>Builds Claude's search index</td><td>You do not want to appear in Claude</td></tr>
<tr><td><code>ClaudeBot</code></td><td>Collects training data</td><td>You do not want your content in model weights</td></tr>
<tr><td><code>Google-Extended</code></td><td>Gemini and AI Overviews grounding</td><td>You do not want to appear in AI Overviews</td></tr>
</tbody></table></div>
<p><code>Google-Extended</code> is worth singling out: blocking it has no effect on your normal
Google Search ranking, which is governed by <code>Googlebot</code>. People block it fearing
otherwise.</p>

<h2>Allow citation, refuse training</h2>
<p>This is the configuration most businesses actually want. Paste it above any existing rules:</p>
<pre><code># AI search crawlers — these decide whether we can be cited.
User-agent: OAI-SearchBot
Allow: /

User-agent: PerplexityBot
Allow: /

User-agent: Claude-SearchBot
Allow: /

User-agent: Google-Extended
Allow: /

# Training crawlers — opt out of model training.
User-agent: GPTBot
Disallow: /

User-agent: ClaudeBot
Disallow: /

User-agent: CCBot
Disallow: /</code></pre>

<h2>The mistake that causes this</h2>
<p>A single blanket block:</p>
<pre><code>User-agent: GPTBot
User-agent: ChatGPT-User
User-agent: OAI-SearchBot
User-agent: PerplexityBot
Disallow: /</code></pre>
<p>Consecutive <code>User-agent</code> lines form one group, so the <code>Disallow</code>
applies to all four. This snippet circulated widely in 2024 as "block AI crawlers" and it
removes you from ChatGPT and Perplexity results as well as from training.</p>
<p>In our measurement of 98 major sites, roughly three quarters of those blocking any AI
crawler had also blocked the search crawlers. <a href="/index/">The data is here</a>.</p>

<h2>What allowing them does not do</h2>
<p>Allowing a crawler is necessary for citation. It is not sufficient, and it is worth setting
expectations before you go looking for results.</p>
<p>Two other things decide whether you actually get quoted. The first is rendering: most AI
crawlers do not execute JavaScript, so a page whose content appears only after hydration is an
empty document to them no matter what robots.txt says. The second is whether there is anything
quotable — a heading phrased as the question someone asked, followed by a direct answer in the
first two sentences, gets lifted; eight paragraphs of preamble do not.</p>
<p>There is also a timing reality. Search indexes refresh on their own schedule, so a robots.txt
change made today does not produce citations tomorrow. Allow the crawlers, then judge it over
weeks rather than days.</p>

<h2>Check it worked</h2>
<p>Rules resolve by longest match, not by order, so a later <code>Disallow: /</code> under
<code>User-agent: *</code> does not override an earlier specific <code>Allow</code> — but a
longer path pattern does. This is where hand-checking gets unreliable.</p>
<p>Scout parses robots.txt the way Google does and tells you, per crawler, whether it can
reach your site and what blocking it actually costs. That check is one of {N_CHECKS} and runs in the
first few seconds of any audit.</p>
<p><a class="btn" href="/download/">Download Scout</a></p>
"""
    return render(
        cat="how-to", slug="fix-ai-crawler-access",
        title="How to let ChatGPT and Perplexity read your site (robots.txt, 2026)",
        desc=("Search crawlers and training crawlers are separate decisions needing separate "
              "robots.txt rules. The copy-paste configuration that allows citation while "
              "opting out of training, and the widely-shared snippet that gets it wrong."),
        h1="How to fix AI crawler access",
        crumb='<a href="/">Scout</a> / <a href="/how-to/">Fix it</a> / AI crawler access',
        body=body,
        faq=[
            ("How do I let ChatGPT read my website?",
             "Allow OAI-SearchBot in robots.txt. That is the crawler that builds ChatGPT "
             "Search's index. GPTBot is a separate crawler used for training and can be "
             "blocked without affecting whether ChatGPT can cite you."),
            ("Does blocking GPTBot stop ChatGPT citing my site?",
             "No. GPTBot collects training data. Citation in ChatGPT Search depends on "
             "OAI-SearchBot, which is a separate user-agent and needs its own rule."),
        ],
    )


def privacy() -> Path:
    body = """
<p>Scout is desktop software that runs on your Mac. This policy covers both the application
and this website.</p>

<h2>The application</h2>
<p>Scout collects nothing. There is no account, no telemetry, no crash reporting and no licence
check. The only network requests the app makes are to the website you ask it to audit.</p>
<p>Audit results and your saved-site list are stored on your machine in <code>~/.scout/</code>
as plain JSON files. They are never transmitted. Deleting that folder removes them permanently.</p>

<h2>This website</h2>
<p>This site is static. It sets no cookies, runs no analytics and embeds no third-party
scripts or fonts. Standard server logs may record IP addresses and requested URLs, which are
used only to keep the site running.</p>

<h2>Data you give us</h2>
<p>If you email us, we hold that email in order to reply to it. Nothing else.</p>

<h2>Changes</h2>
<p>If this policy changes, the updated version appears on this page.</p>

<h2>Contact</h2>
<p>Questions about privacy or anything else: <a href="mailto:hello@scoutseo.app">hello@scoutseo.app</a>.</p>
"""
    return render(
        cat="legal", slug="privacy",
        title="Privacy policy — Scout",
        desc="Scout collects nothing. No account, no telemetry, no analytics on this site.",
        h1="Privacy policy",
        crumb='<a href="/">Scout</a> / Privacy',
        body=body,
        schema_type="WebPage",
    )


def terms() -> Path:
    body = """
<p>By downloading or using Scout you agree to these terms.</p>

<h2>Licence</h2>
<p>Scout is licensed to you for use on machines you own or control. You may audit any number of
websites, including on behalf of clients.</p>

<h2>Responsible use</h2>
<p>Scout crawls websites. You are responsible for the sites you point it at. Its defaults are
deliberately gentle — requests are rate-limited, it honours <code>robots.txt</code> unless you
turn that off, and it backs off when a server signals it is being asked for too much. Please do
not raise those limits on sites you do not own or have permission to crawl.</p>

<h2>No warranty</h2>
<p>Scout is provided as is. It reports what it can observe in the HTML and HTTP responses a
site returns. It cannot guarantee rankings, traffic or any commercial outcome, and its findings
are advice rather than a certification. Search engines change their behaviour without notice.</p>
<p>The scope page in every report lists what was and was not measured. Please read it before
relying on an audit for a decision that matters.</p>

<h2>Liability</h2>
<p>To the maximum extent permitted by law, we are not liable for any loss arising from use of
Scout, including lost traffic, revenue or rankings.</p>

<h2>Contact</h2>
<p><a href="mailto:hello@scoutseo.app">hello@scoutseo.app</a></p>
"""
    return render(
        cat="legal", slug="terms",
        title="Terms of use — Scout",
        desc="Licence, responsible crawling, and the limits of what an audit can promise.",
        h1="Terms of use",
        crumb='<a href="/">Scout</a> / Terms',
        body=body,
        schema_type="WebPage",
    )


BUILDERS = [download, for_hub, for_agencies, for_local, howto_hub, howto_ai_access,
            privacy, terms]


def build_all() -> list[Path]:
    return [b() for b in BUILDERS]


if __name__ == "__main__":
    for p in build_all():
        print(p)
