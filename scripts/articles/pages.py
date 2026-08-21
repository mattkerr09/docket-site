#!/usr/bin/env python3
"""Download, legal and audience/how-to hubs.

Built because Docket audited its own site and found the links to these pages were
broken. Dogfooding caught it in the first run, which is the argument for the
product in miniature.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import facts as F  # noqa: E402
from render import (
    FREE_CLAUSE,  # noqa: E402
    BETA_FREE, BILLING_EMAIL, COMPETITORS, DMG, DMG_SIZE, GOVERNING_LAW, ISSUES,
    LINUX, LINUX_NAME, LINUX_SIZE, N_CHECKS, N_LANES, PRICE_STR, PROCESSOR,
    RELEASE, SELLER, SELLER_REG_NO, SUMS, price_note_html, render,
    seller_address,
)


#: Slugs in the order a buyer meets them, cheapest first. Built from the same
#: competitors.csv the comparison pages use, so a price correction there moves
#: this table too.
_COST_SLUGS = ("sitebulb", "screaming-frog", "ahrefs-site-audit",
               "semrush-site-audit")


def _cost_rows() -> str:
    rows = sorted(((F.rival_annual_low(s), s) for s in _COST_SLUGS))
    return "".join(
        f"<tr><td>{COMPETITORS[slug]['name']}</td>"
        f"<td>${low:,}/yr</td><td>${F.three_year_cost(slug):,}</td></tr>"
        for low, slug in rows
    )


def _payment_note() -> str:
    """What actually happens when you press Download, in one paragraph.

    This used to be a hardcoded sentence: "{RELEASE} is free. The beta downloads
    without payment and keeps working; the $79 applies from v1.0." It was true
    while `BETA_FREE` was True, and it went false the moment the version passed
    v1.0 with the flag flipped — the page then told a reader that the price
    applies from v1.0 while offering v1.1.0 for nothing. One fact living in two
    places, and only the constant got updated.

    So it is derived. The wording still refuses to leave a price beside a button
    that charges nothing without saying so, because that is exactly the kind of
    thing this tool exists to flag, and a site that sells an honesty instrument
    cannot be the counterexample.
    """
    if BETA_FREE:
        return (f'<p><strong>{RELEASE} is free while it is in beta.</strong> It downloads '
                f'without payment and keeps working; {PRICE_STR} applies from v1.0.</p>')
    return (
        f'<p><strong>{RELEASE} still downloads and runs without a licence key.</strong> '
        f'The price is {PRICE_STR}, paid once, and buying is what pays for the work — '
        f'but there is no activation step in this build and nothing stops you using it '
        f'first. Said plainly because a price on a page beside a button that charges '
        f'nothing is precisely the kind of thing this tool exists to flag, and it would '
        f'be a poor advertisement to be the example.</p>')


def download() -> Path:
    body = f"""
<p class="lede">Docket is {PRICE_STR}, paid once, for macOS 12 or later on Apple Silicon.
{DMG_SIZE}. No subscription, no crawl credits, no per-seat pricing — audit as many sites as
you like, for as long as you like. There is no account to create and no telemetry. Activating
your licence checks the key with our payment provider once, and about once a day after that;
nothing about the sites you audit is ever sent anywhere.</p>

{_payment_note()}

<p><a class="btn btn-lg" href="{DMG}">Download Docket {RELEASE} for Mac</a></p>
<p style="font-size:var(--t-md);color:var(--text-dim)">Apple Silicon · macOS 12+ · {DMG_SIZE} ·
<a href="https://github.com/mattkerr09/docket-site/releases">all releases</a></p>

<h2>What it will crawl</h2>

<p><strong>No page ceiling.</strong> The default is {F.crawl_default()} pages to a depth of
{F.crawl_depth()} clicks, and setting the page count to 0 removes the limit entirely.</p>

<p>That is worth stating precisely, because "unlimited" on its own is a promise no program
keeps. What still stops a crawl is the {F.crawl_minutes()}-minute wall clock, the frontier
running dry, and — on a genuinely enormous site — your machine's memory, because every page is
held in one list. A crawl that hits the clock stops and tells you it stopped, with everything
it found so far, rather than pretending it finished.</p>

<p>If your site is larger than that, say so plainly to yourself and use
<a href="/vs/screaming-frog-alternative/">Screaming Frog</a> — it crawls without a ceiling and
that is a real reason to pick it. Docket is built to read a site closely rather than to survey
one at that scale. These numbers are generated from the shipped build, not typed here, so they
cannot drift from what the app does.</p>

<h2>What it costs over three years</h2>

<p>{PRICE_STR} once, against a subscription. The arithmetic, from the prices on
<a href="/vs/">the comparison pages</a>:</p>

<div class="wrap-tbl"><table class="cmp"><thead><tr>
<th>Tool</th><th>Cheapest tier</th><th>Three years</th></tr></thead><tbody>
<tr><td><strong>Docket</strong></td><td><strong>{PRICE_STR} once</strong></td>
<td><strong>{PRICE_STR}</strong></td></tr>
{_cost_rows()}
</tbody></table></div>
{price_note_html()}

<p>Docket costs less than a year of the cheapest alternative and nothing after that. That is
the whole pricing argument and it does not need help: the tools above are not overpriced for
what they do, they are simply rented rather than owned.</p>

<h2>Checking what you downloaded</h2>

<p>The Mac app is signed with a Developer&nbsp;ID and notarised by Apple, so macOS verifies it
with Apple before it opens and you need do nothing. The Linux tarball has no equivalent — it is
a plain archive from a URL — so every release publishes
<a href="{SUMS}">SHA256SUMS</a> covering all of its artifacts:</p>

<pre><code>curl -LO {LINUX}
curl -LO {SUMS}
grep linux SHA256SUMS | shasum -a 256 -c -</code></pre>

<p>Be clear about what that proves and what it does not. It proves the file arrived intact and
is the one this release published. It does <strong>not</strong> prove authorship: the checksums
sit on the same release as the tarball, so anyone able to replace one could replace the other.
Apple's notarisation of the Mac build is a genuinely stronger guarantee, and pretending the two
are equivalent would be exactly the kind of claim this tool exists to catch.</p>

<h2>Opening it</h2>
<p>Double-click it. Docket is signed with a Developer&nbsp;ID and notarised by Apple, so
macOS opens it without a security warning and without any of the right-click or Terminal
workarounds that unsigned software needs.</p>

<h2>What happens on first launch</h2>
<p>Docket opens, starts its local audit engine, and shows a single field. Type a domain, press
Run audit, and watch it crawl. There is no onboarding, no project setup and no plan selection,
because none of those are necessary for the thing you came to do.</p>
<p>The first launch takes a few seconds longer than later ones. It used to say "while the
engine unpacks itself" — that was an explanation nobody had measured, and timing the CLI out of
the shipped bundle put its startup at a fifth of a second with no unpacking step to be found.
The delay is real and the reason given for it was invented, so the reason is gone.</p>

<p>There is no security prompt to get past: the app is notarised, so macOS verifies it with
Apple and opens it.</p>

<h2>The command line</h2>
<p>The same engine ships as a CLI inside the app bundle. It is the whole product, not a
cut-down version, and it has six subcommands.</p>

<h3><code>docket audit</code> — the full audit</h3>
<pre><code>docket audit example.com
docket audit example.com -o audit.pdf -n 500
docket audit example.com --render 10        # run each page's JavaScript first
docket audit example.com --offline          # no third-party calls at all
docket audit example.com -f json --no-pages | jq '.score.overall'</code></pre>
<p>It exits with status 2 when it finds a critical issue, so it can gate a deployment. Running
it in CI against a staging URL fails the build if someone ships a <code>noindex</code>, which
is a mistake that otherwise gets found weeks later by a traffic graph.</p>

<p>There is a full walkthrough for that on
<a href="/for/developers/">running Docket in a deploy pipeline</a> — where the binary lives
inside the bundle, a working GitHub Actions job, how long an audit actually takes, and what a
macOS runner costs you per pull request.</p>

<p><code>--fail-on</code> sets the bar. The default is <code>critical</code>, deliberately:
almost every real site has HIGH findings, and a gate that fails on ordinary work gets wrapped
in <code>|| true</code> within a month.</p>

<pre><code>docket audit https://staging.example.com --fail-on critical   # default
docket audit https://staging.example.com --fail-on high
docket audit https://staging.example.com --fail-on never      # report, never fail</code></pre>

<p>Three exit codes, and they are a contract — a pipeline depends on them not moving:</p>

<div class="wrap-tbl"><table class="cmp"><thead><tr>
<th>Code</th><th>Meaning</th></tr></thead><tbody>
<tr><td><code>0</code></td><td>The audit ran and found nothing at or above the threshold</td></tr>
<tr><td><code>1</code></td><td>Docket could not run — bad arguments or a crash. A defect in the
tool, not in your site</td></tr>
<tr><td><code>2</code></td><td>The audit ran and the result is bad</td></tr>
</tbody></table></div>

<p>A site that does not answer is <code>2</code>, not <code>1</code>: Docket ran fine, the site
was not there, and a staging URL that does not respond should stop a deploy. Keeping those
two apart matters more than it sounds — "your site is broken" and "the tool is broken" need
opposite responses from whoever reads the log, and a gate that confuses them stops being
trusted.</p>

<p>That case took a real fix. Auditing a domain that does not resolve used to report three
critical issues: that robots.txt blocked Googlebot, that the site was not served over HTTPS,
and that no pages could be crawled. Only the last was true — there was no robots.txt and
nothing was served, because there was no site. A DNS blip in a pipeline would have failed the
build with two invented criticals and sent somebody hunting for a robots.txt problem that
never existed. When nothing at all can be read, Docket now reports that and stops.</p>

<h3><code>docket diff</code> — what this deploy broke</h3>
<pre><code>docket diff https://example.com https://staging.example.com
docket diff https://example.com https://staging.example.com --fail-on medium</code></pre>

<p>Audits both with identical settings and reports what the second one changed. This is the
better deploy gate, and the reason is arithmetic: every real site carries standing findings, so
a severity threshold tight enough to catch a regression fails every build, and one loose enough
to pass catches nothing. A deploy is only answerable for what it changed.</p>

<p>Regressions are new findings <em>and</em> ones that got worse — a check that was MEDIUM
before and is HIGH now did not appear or disappear, and it is exactly what you want to know.
Improvements never fail a build, however many there are. The default threshold is
<code>high</code> rather than <code>critical</code>, deliberately: a standing HIGH finding is
somebody's backlog, and a HIGH finding that arrived with this deploy is this deploy's fault.</p>

<p>If the two crawls reach very different numbers of pages, Docket refuses to compare them and
exits <code>1</code> — not <code>0</code>. A build that goes green because the comparison was
impossible is worse than one that fails, because the team believes the gate ran.</p>

<h3><code>docket logs</code> — what Googlebot actually fetched</h3>
<pre><code>docket logs access.log
docket logs access.log.gz --url https://example.com
docket logs access.log --verify           # confirm the bot really was Google</code></pre>

<p>A crawl tells you what a search engine <em>could</em> reach. A server log tells you what it
did reach, how often, and what it wasted requests on. Point Docket at a Common or Combined
format access log and it reports the response codes Google actually received, the paths it
fetched most, and how much of its budget went on redirects and errors. Add
<code>--url</code> and it crawls the site too, then shows the two ways the sets differ: pages
you link to that Google did not fetch in that period, and pages Google fetches that the crawl
never found — orphans, retired URLs still being retried, or sitemap-only pages.</p>

<p><strong>A user-agent is a header anybody can send</strong>, and scrapers claim to be
Googlebot constantly. Everything is reported as "claimed" until you pass <code>--verify</code>,
which does the reverse-DNS-then-forward-lookup check
<a href="https://developers.google.com/search/docs/crawling-indexing/verifying-googlebot">Google
documents</a>. It is off by default because it is a DNS round trip per distinct IP. Lines that
are not in a recognised format are counted and reported rather than skipped, because a parser
that quietly drops a third of a file produces confident numbers about the rest.</p>

<p><a href="/vs/screaming-frog-alternative/">Screaming Frog</a> sells a dedicated
<a href="https://www.screamingfrog.co.uk/log-file-analyser/">Log File Analyser</a> as a separate
product at $139 per year, free up to 1,000 log events. It is a much deeper tool than this —
a real interface, saved projects, and far more than a set difference against one crawl. What
Docket gives you is the comparison that answers "is Google spending its time on my important
pages", included in the one-time price rather than as a second subscription.</p>

<h3><code>docket attack</code> — where a competitor's authority does not protect them</h3>
<pre><code>docket attack yoursite.com theircompetitor.com
docket attack yoursite.com theirs.com --demand "emergency plumber"</code></pre>
<p>Audits both sites, compares their link-graph authority, and returns the openings ranked by
how winnable they are rather than how large they are. An older, better-linked competitor is
unbeatable on the pages it has held for years and beatable on the ones it never wrote — and
that distinction is the only part of a competitive analysis that changes what you do on
Monday. Add <code>--demand</code> and it pulls what people actually search for from Google's
public autocomplete, then reports which of those questions neither site answers.</p>

<h3><code>docket backlinks</code> — authority without a subscription</h3>
<pre><code>docket backlinks yoursite.com competitor.com
docket backlinks yoursite.com --referring</code></pre>
<p>Domain authority from Common Crawl's public hyperlink graph, which covers 117,963,409
domains. <code>--referring</code> streams the 9.8 GB graph to list the domains linking in;
it takes minutes and writes nothing to disk.</p>

<h3><code>docket checks</code> and <code>docket serve</code></h3>
<p><code>checks</code> prints every check the engine runs with its lane and severity.
<code>serve</code> runs the local API the desktop app talks to, on 127.0.0.1, which is also
how you would drive Docket from your own scripts.</p>

<h2>Requirements and limits</h2>
<ul>
<li><strong>macOS 12 or later, Apple Silicon</strong> for the desktop app. There is no
Intel or Windows build.</li>
<li><strong>Linux x86_64 for the command line.</strong>
{'<a href="' + LINUX + '">Download the ' + LINUX_SIZE + ' tarball</a> — needs' if LINUX else 'A tarball needing'}
<strong>glibc 2.30</strong> or newer — check yours with <code>ldd --version</code>. That floor
is measured from the shipped binary rather than assumed from the machine that built it: the
launcher itself only needs 2.14, and the bundled Python runtime is what raises it to 2.30.
It is the same engine and the same checks, verified running in a clean container. Two things
it is not: there is no Linux desktop app, only the CLI, and <code>--render</code> does not work
there — the renderer is a WebKit helper that exists only on macOS, so on Linux Docket reports
that rendering was requested and did not happen rather than quietly skipping it.</li>
<li><strong>An internet connection to the site you are auditing.</strong> Nothing else.</li>
<li><strong>Crawls are bounded</strong> by page count, depth, wall-clock time and response
size. The defaults are deliberately polite; you can raise them.</li>
</ul>

<h2>What happens to your data</h2>
<p>The crawl and every check run on your machine, and Docket identifies itself honestly in
its user-agent rather than impersonating Googlebot — a spoofed user-agent gets a different,
sometimes cloaked response, which would make every finding a lie.</p>

<p>Four optional checks do reach out, and it is worth being exact rather than reassuring:
Docket asks your own server what it tells AI crawlers, refreshes its crawler knowledge file
from this site, checks whether the email addresses you publish can actually receive mail, and
fetches Core Web Vitals from Google PageSpeed Insights. <code>--offline</code>, or the offline
tick in the desktop app, turns all four off and the audit still completes — the report then
says which checks did not run rather than quietly scoring them.</p>

<p>Docket also asks docketseo.app once at launch whether a newer version exists, and tells you
if there is one. It sends nothing but the request itself, it never installs anything without
you saying yes, and <code>Check for Updates…</code> in the Docket menu does the same thing on
demand. Said here because a product that sells not phoning home should list the one call it
makes on its own.</p>

<p>What never happens: no telemetry, no account, no analytics on you, and nothing about your
site is sent anywhere for us to see. This page made a stronger, absolute claim until
2026-08-10; it was not true while those four checks were on by default, and it has been
corrected rather than quietly dropped.</p>
<p>Audit history is stored in <code>~/.docket/</code> as plain JSON. Delete the folder and it
is gone.</p>
"""
    return render(
        cat="download", slug="",
        title=f"Download Docket for Mac — {PRICE_STR}, paid once",
        desc=(f"Docket for macOS 12+ on Apple Silicon. {DMG_SIZE}, no account, no telemetry. "
              "Includes the CLI, which exits non-zero on a critical issue so it can gate a "
              "deploy."),
        h1="Download Docket for Mac",
        crumb='<a href="/">Docket</a> / Download',
        body=body,
        schema_type="WebPage",
    )


def for_hub() -> Path:
    body = f"""
<p class="lede">The same {N_CHECKS} checks run on every site, but which findings matter most changes a
lot by who you are. These pages cover what to look at first.</p>

<p>That is not a marketing framing. Docket scores every lane on every site, and the same
finding genuinely carries different weight depending on how the business gets found.</p>

<h2>Why the same finding lands differently</h2>

<p>Missing <code>LocalBusiness</code> schema is close to fatal for a business that lives on
"near me" searches and completely irrelevant to a SaaS company selling to another country. A
slow product page costs an ecommerce site money on every session and costs a reference site
almost nothing. Neither of those is a judgement about how good the site is; they are facts
about which door customers come through.</p>

<p>The place this matters most is the middle of the list. Critical findings are critical for
everyone — a page nobody can index cannot help anybody. It is the twenty MEDIUM findings
underneath where knowing your own situation turns a report into a plan, and where a tool that
only knows how to sort by severity leaves you to guess.</p>

<p>Two things are worth reading whoever you are, because they now apply to every kind of
site: whether AI answer engines can
<a href="/learn/ai-search-visibility/">reach and cite you</a>, and which of your pages an AI
answer <a href="/learn/ai-substitution/">replaces outright</a>. Those were niche two years
ago.</p>

<h2><a href="/for/agencies/">For SEO agencies</a></h2>
<p>Unlimited client audits with no per-seat or per-crawl cost, and a client-ready PDF that does
not need rebuilding in a deck.</p>

<h2><a href="/for/developers/">For developers</a></h2>
<p>The CLI as a deploy gate — exit codes, a working GitHub Actions job, and what it costs to
run on a macOS runner.</p>

<h2><a href="/for/ecommerce/">For online shops</a></h2>
<p>We audited ten large retailers before writing this one, and the result contradicted the
pitch: none had broken product markup. What did show up, and where Screaming Frog is the
better tool for a catalogue.</p>

<h2><a href="/for/local-business/">For local businesses</a></h2>
<p>Why you are not in the map pack — LocalBusiness schema, NAP consistency, and the geo
signals that decide "near me" results.</p>

<h2><a href="/for/saas/">For SaaS companies</a></h2>
<p>{len(F.category_citation_hosts('saas'))} of the {F.category_n('saas')} SaaS sites in the
Index block an answer engine, so the blocking scare is not the story. The story is a marketing
page that is empty until JavaScript runs, and a docs subdomain competing with it.</p>

<h2>One more coming</h2>
<p>An in-house marketing page will appear when it has something specific to say.
Near-duplicate pages are the real flag risk in a programmatic set, not thin ones, so a page
gets written when there is a measurement behind it rather than to fill a gap in a list.</p>

<p>That standard is why the ecommerce page took as long as it did: the honest version could
only be written after auditing real shops, and what came back disagreed with what the page was
going to say. The SaaS page went the same way — the pitch it was going to make is the one its
own data contradicts. If the last one never produces a finding worth publishing, it will not
be written, and this paragraph will say so rather than promising it indefinitely.</p>
"""
    return render(
        cat="for", slug="",
        title="Docket for agencies, local businesses and marketers",
        desc=("Which audit findings matter most depending on who you are — "
              "agencies, local businesses, and more."),
        h1="Docket for your situation",
        crumb='<a href="/">Docket</a> / For you',
        body=body,
        schema_type="CollectionPage",
    )


def for_agencies() -> Path:
    body = """
<p class="lede">The cost that hurts an agency is not the licence — it is the per-seat and
per-crawl metering that makes you think twice before auditing a prospect. Docket is a one-time
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
<p>Docket's PDF is designed to be sent, not rebuilt. It opens with a score and a one-sentence
verdict a client can act on, then a scorecard by area, then the ranked plan — each item with
what it costs the client in plain language and the exact markup their developer needs.</p>
<p>There is also a scope page, and it is there on purpose. It states how many pages were
crawled, what was measured, and explicitly what was not — Core Web Vitals field values,
JavaScript-rendered content, anything inside a tag manager. A report that quietly implies full
coverage is the one that gets you a difficult question in month three.</p>

<h2>Monitoring turns an audit into a retainer</h2>
<p>Save a client site and Docket re-audits it on a schedule, then tells you what changed since
last time: issues that appeared, issues that were resolved, and the score movement per area.
Regressions surface first, because a site that was clean and broke is the thing you need to
know about — a check that has been failing for six months is not news.</p>
<p>That changes the conversation from "here is another audit" to "your developer shipped a
noindex on the pricing page on Tuesday", which is a materially different meeting.</p>

<p><strong>Say what this does not do, because a retainer is a promise.</strong> The schedule is
a thread inside Docket, not a background daemon and not a cron job. It runs while the app is
open on a machine that is awake; quit Docket, or close the laptop, and the clock stops until
you open it again. It catches up on the next launch rather than silently skipping, but if you
need a crawl to land at 3am on a machine nobody is sitting at, a hosted crawler is the right
architecture and that is what the subscription buys. Docket suits an agency that opens it
during the working week, not one that needs unattended overnight runs.</p>

<h2>Competitor comparison for pitches</h2>
<p>Attach competitor URLs to a client site and Docket audits them on the same settings, then
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
<p>Say it early rather than being asked. Docket has no per-page backlink or anchor-text data
and no search volumes — you will still need an index tool for keyword research. Rendering is
available but off by default and samples the shallowest pages, so a very large single-page
application still wants a dedicated rendering crawl.</p>
<p>Being straight about the boundary is also, in practice, a good sales posture. A tool that
claims everything invites the client to test the claim.</p>

<p><a class="btn" href="/download/">Download Docket</a></p>
"""
    return render(
        cat="for", slug="agencies",
        title=f"Docket for SEO agencies: unlimited client audits for {PRICE_STR}",
        desc=("Per-crawl metering makes agencies ration audits. Docket runs locally with no "
              "per-seat or per-crawl cost, and re-audits on a schedule while the app is open."),
        h1="Docket for SEO agencies",
        crumb='<a href="/">Docket</a> / <a href="/for/">For you</a> / Agencies',
        body=body,
        faq=[
            ("Can I use Docket for client work?",
             "Yes. Docket is " + PRICE_STR + " once — free while " + RELEASE + " is in "
             "beta — with no per-seat or per-crawl limits, so you can audit as many client "
             "and prospect sites as you like."),
            ("Can I white-label the report?",
             "The PDF is Docket-branded. The CSV and JSON exports carry no branding and can be "
             "dropped into your own template."),
        ],
    )


def for_developers() -> Path:
    """The deploy gate, for the people who own the pipeline.

    Every figure here is measured or quoted, and the platform limitation leads
    rather than hides at the bottom: a developer whose runners are Ubuntu needs
    to know in the first paragraph that this will not work, because the only
    thing worse than losing that reader is wasting twenty minutes of their time
    first.
    """
    body = f"""
<p class="lede">Docket's CLI exits <code>2</code> when it finds a critical issue, so
<code>docket audit https://staging.example.com</code> is a complete deploy gate in one line and
nothing else has to be installed. Auditing {F.ci_page_cap()} pages took a median of
<strong>{F.ci_median_seconds()} seconds</strong> across {F.ci_sites()} real sites
({F.ci_fastest_seconds()}s to {F.ci_slowest_seconds()}s, measured {F.ci_measured()}), which is
short enough to sit on every pull request without anyone noticing the build got slower.</p>

<h2>Read this first: your runners are probably Linux</h2>

<p>The desktop app is Apple Silicon only, and the Linux CLI is x86_64 — so the action
installs the macOS build. It runs on GitHub Actions'
<a href="https://docs.github.com/en/actions/reference/runners/github-hosted-runners"><code>macos-latest</code></a>,
which is arm64, and it does not run on <code>ubuntu-latest</code> at all. If your pipeline is
Linux and you are not willing to add a macOS job to it, stop reading and use
<a href="https://www.screamingfrog.co.uk/seo-spider/user-guide/general/">Screaming Frog's
command line interface</a> instead: it is available for Windows, Mac and Ubuntu Linux, it runs
headless, and for a Linux-only pipeline it is simply the right tool. That is a real advantage
and there is no version of this page where it is not.</p>

<p>Everything below assumes you are willing to run one macOS job. It costs more than a Linux
one — see the arithmetic further down — and it is the whole of the catch.</p>

<h2>Where the binary actually is</h2>

<p>The CLI ships inside the app bundle, and until now this site told you it existed without
telling you where. It is here:</p>

<pre><code>/Applications/Docket.app/Contents/Resources/docket/docket</code></pre>

<p>Put that directory on your <code>PATH</code> rather than symlinking the binary somewhere
else. The WebKit rendering helper lives beside it as a sibling, and keeping the directory
intact is what lets <code>--render</code> find it.</p>

<h2>A workflow that works</h2>

<pre><code>name: SEO gate
on: [pull_request]

jobs:
  seo:
    runs-on: macos-latest          # arm64. ubuntu-latest will not work.
    steps:
      - name: Install Docket
        run: |
          curl -sL -o docket.dmg {DMG}
          hdiutil attach -nobrowse -quiet docket.dmg -mountpoint /Volumes/Docket
          cp -R /Volumes/Docket/Docket.app /Applications/
          echo "/Applications/Docket.app/Contents/Resources/docket" &gt;&gt; "$GITHUB_PATH"

      - name: Audit staging
        run: docket audit https://staging.example.com -n 100 --fail-on critical</code></pre>

<p>No runtime to install, no <code>pip install</code>, no lockfile to resolve — the download is
{DMG_SIZE} and it is notarised by Apple, so nothing has to be talked past Gatekeeper. Process
overhead was {F.ci_overhead_seconds()}s of the wall-clock in every run measured; effectively all
of the time is the crawl itself, at about {F.ci_seconds_per_page()} seconds per page.</p>

<h2>The exit codes are a contract</h2>

<p>A pipeline depends on these not moving, so they are part of the public interface more than
anything printed is:</p>

<table>
<thead><tr><th>Code</th><th>Meaning</th></tr></thead>
<tbody>
<tr><td><code>0</code></td><td>The audit ran and found nothing at or above the threshold</td></tr>
<tr><td><code>1</code></td><td>Docket could not run. A defect in the tool, not in your site</td></tr>
<tr><td><code>2</code></td><td>The audit ran and the result is bad</td></tr>
</tbody>
</table>

<p><code>1</code> and <code>2</code> are deliberately distinct, because "your site is broken" and
"the tool is broken" demand opposite responses from whoever reads the log at six on a Friday,
and a gate that conflates them gets wrapped in <code>|| true</code> within a month.</p>

<p>A staging URL that does not answer is <code>2</code>, not <code>1</code>: Docket ran
correctly, the site was not there, and that should stop a deploy. This distinction has teeth —
pointing Docket at a hostname that does not resolve used to report three critical issues, of
which two were invented. A DNS blip would have failed a build with a confident story about a
robots.txt file that did not exist. If you are wiring <em>any</em> audit tool into CI, run it
once against a hostname that does not resolve and read what it says. You will learn more in
that run than in ten against a healthy site.</p>

<h2>Gate on what this deploy broke, not on what was already broken</h2>

<p><code>--fail-on</code> defaults to <code>critical</code>, deliberately: almost every real site
carries HIGH findings, and a default that fails on ordinary work gets disabled. But an absolute
threshold is the wrong question for a pipeline, and the reason is arithmetic. Every real site
has standing findings, so a bar tight enough to catch a regression fails every build, and one
loose enough to pass catches nothing. The deploy is only answerable for what it changed.</p>

<pre><code>docket diff https://example.com https://staging.example.com --fail-on medium</code></pre>

<p>That audits both on identical settings and fails only on findings that are new or
<em>worse</em> than production. A check that was MEDIUM before and is HIGH now never appeared or
disappeared — it got worse, which is exactly what the gate is for, and a naive new-versus-old set
comparison misses it entirely. Improvements never fail a build, however many there are.</p>

<p>If the two crawls reach very different numbers of pages, Docket refuses to compare them and
exits <code>1</code> rather than <code>0</code>. A build that goes green because the comparison
was impossible is worse than one that fails, because the team believes the gate ran.</p>

<h2>Findings on the Security tab instead of in the log</h2>

<p>An exit code tells a build to stop and nothing else, so whoever sees red opens the log and
reads text. <code>-f sarif</code> writes SARIF 2.1.0, the format GitHub, GitLab and Azure all
ingest, and the findings become listed alerts with their severity, their description and the
fix attached:</p>

<pre><code>      - name: Audit staging
        run: docket audit https://staging.example.com -n 100 -f sarif &gt; docket.sarif

      - uses: github/codeql-action/upload-sarif@v3
        with:
          sarif_file: docket.sarif</code></pre>

<p><strong>Be clear about what that gets you.</strong> SARIF was designed for static analysis,
where a result points at a file and a line. Docket's findings are about URLs, and there is no
general way to know which source file produced a given URL — a template, a CMS record and a
static file all look identical from outside. So the alerts land on the Security tab, correctly
titled and linked to the affected pages, and they do <em>not</em> annotate the lines of a pull
request the way a linter's SARIF does. If inline diff annotations are what you are after, this
will disappoint you.</p>

<p>Two details worth knowing. CRITICAL and HIGH both map to SARIF's <code>error</code>, because
SARIF has no rank above it — each finding keeps its real severity in <code>properties</code>.
And a finding's location is always a page of your own site: a few checks list a third-party URL
as where you go to fix something, and pointing an alert at Google's settings page would be
nonsense, so those travel as the rule's <code>helpUri</code> instead.</p>

<h2>Findings in the test-report panel</h2>

<p><code>-f junit</code> writes JUnit XML, which is the report widget every CI system already
has — GitLab, Jenkins, Azure, Buildkite, CircleCI. The shape is one testcase per check, so the
panel reads like a test run — {N_CHECKS} tests, four failed — rather than handing
you a wall of text.</p>

<p>Two decisions in that shape matter more than the format. A check that ran and found nothing
is a <strong>pass</strong>; a check that could not run is <strong>skipped</strong>, never
passed. And if the crawl reached no pages at all, every check is skipped and none is green —
a passing test report gets read as a guarantee, and an audit that read nothing has not earned
one. Failures use the same threshold as the exit code, so a build cannot go green while showing
red tests.</p>

<h2>A GitHub Action, so you do not maintain the shell</h2>

<p>The four lines above work and will keep working. If you would rather not own them:</p>

<pre><code>      - uses: mattkerr09/docket-site@{RELEASE}
        with:
          url: https://staging.example.com
          fail-on: critical
          format: junit          # or sarif, or text</code></pre>

<p>It checks the runner first and fails with a sentence you can act on if it is not Apple
Silicon macOS, rather than letting you find out inside an <code>hdiutil</code> error. Full
inputs and exit codes are in
<a href="https://github.com/mattkerr09/docket-site/blob/main/ACTION.md">ACTION.md</a>. It is
not published to the GitHub Marketplace — reference it by repository as shown.</p>

<h2>What it costs to run</h2>

<p>macOS minutes are the expensive ones. GitHub
<a href="https://docs.github.com/en/billing/reference/actions-minute-multipliers">publishes</a>
{F.gh_macos_per_min()} per minute for a standard macOS runner against {F.gh_linux_per_min()}
for Linux — about {F.gh_macos_multiple()} times — and billed minutes round up. The measured
audit is well under a minute, so a run bills as one: roughly
<strong>{F.gh_gate_cost_cents()} cents per gate</strong>, or {F.gh_monthly_cost(200)} for two
hundred pull requests in a month.</p>

<p>Worth saying plainly: that is a recurring cost on a tool sold as a one-time
{PRICE_STR}, and it is GitHub's, not ours. If it bothers you, gate on merges to main rather
than every push, or run the job on a Mac you already own — Docket has no
seat count, so a self-hosted runner is free.</p>

<h2>Three things not to do</h2>

<p><strong>Do not gate on the score.</strong> It is a weighted composite and it moves when the
weighting changes. Gate on severities, which are defined per check and do not drift.</p>

<p><strong>Do not run it against production on every push.</strong> Point it at staging. Docket
backs off on 429 and 503 rather than hammering, but a crawl on every commit is still traffic
your own analytics has to explain.</p>

<p><strong>Do not turn on <code>--render</code> and leave it.</strong> Rendering runs each page
through WebKit and it is much slower than the numbers above, which were measured without it.
Turn it on for the pages that need it, or on a nightly job rather than a per-PR one.</p>

<h2>Where this is thin</h2>

<p>SARIF gets findings onto the Security tab but not onto the pull request diff, for the
reason above — that one is structural rather than unfinished. `docket diff` is not wired into
the action yet, so gating on what a deploy broke means running it as a plain step. Nothing
is cached between runs, so every job re-downloads {DMG_SIZE}. And the timings above are one
machine on home broadband on a single day, across {F.ci_sites()} sites — one of them swung
fifteen seconds between two consecutive runs. Treat them as an order of magnitude, not a
benchmark, and measure your own.</p>

<p><a class="btn" href="/download/">Download Docket</a></p>
"""
    return render(
        cat="for", slug="developers",
        title="SEO checks in your deploy pipeline: Docket's CLI as a gate",
        desc=(f"Docket's CLI exits 2 on a critical finding, so it gates a deploy in one "
              f"line. {F.ci_page_cap()} pages in a median {F.ci_median_seconds()}s across "
              f"{F.ci_sites()} sites. Apple Silicon only."),
        h1="SEO checks in your deploy pipeline",
        crumb='<a href="/">Docket</a> / <a href="/for/">For you</a> / Developers',
        body=body,
        published="2026-08-07",
        faq=[
            ("Can I run an SEO audit in CI?",
             "Yes, and it is the strongest use of one, because it catches a noindex before it "
             "ships rather than weeks later on a traffic graph. Docket's CLI exits 0 when "
             "clean, 2 when it finds something at or above your threshold, and 1 only when "
             "the tool itself could not run."),
            ("Does Docket run on GitHub Actions?",
             "On macos-latest, which is arm64. Docket is Apple Silicon only, so it will not "
             "run on ubuntu-latest. If your pipeline is Linux-only, Screaming Frog's CLI runs "
             "on Windows, Mac and Ubuntu Linux and is the better fit."),
            ("How long does a Docket audit take in a pipeline?",
             f"A median of {F.ci_median_seconds()} seconds for {F.ci_page_cap()} pages across "
             f"{F.ci_sites()} real sites measured on {F.ci_measured()}, or roughly "
             f"{F.ci_seconds_per_page()} seconds per page. Process startup was "
             f"{F.ci_overhead_seconds()}s, so almost all of it is the crawl. Rendering with "
             f"--render is considerably slower and was not included."),
            ("Can Docket output SARIF for GitHub code scanning?",
             "Yes — docket audit -f sarif writes SARIF 2.1.0, which you can hand to "
             "github/codeql-action/upload-sarif. The findings appear as alerts on the "
             "Security tab with their severity and fix. They do not annotate the pull "
             "request diff: SARIF locations are files and lines, and an SEO finding is "
             "about a URL, which cannot generally be mapped back to a source file."),
            ("Does Docket have a GitHub Action?",
             "Yes — reference mattkerr09/docket-site in a `uses:` step. It installs Docket, "
             "runs the audit and exits with the same codes as the CLI, and it checks the "
             "runner first so a Linux job fails with a sentence you can act on rather than a "
             "confusing disk-image error. It is not on the GitHub Marketplace; reference it "
             "by repository."),
            ("Can Docket write JUnit output for my CI test panel?",
             "Yes, with -f junit. One testcase per check, so the panel reads as a test run. A "
             "check that ran and found nothing passes; one that could not run is skipped, "
             "never passed; and if the crawl reached no pages, every check is skipped and "
             "none is green — a passing test report is read as a guarantee."),
            ("Should the build fail on the SEO score?",
             "No. The score is a weighted composite and moves when the weighting changes. "
             "Gate on severities with --fail-on, or better, use docket diff to fail only on "
             "findings this deploy introduced or made worse — every real site carries standing "
             "findings, so an absolute threshold either fails every build or none of them."),
        ],
    )


def for_ecommerce() -> Path:
    """The audience page the /for/ hub had been promising.

    Written after measuring, not before, and the measurement contradicted the
    obvious pitch: large shops are mostly clean. The page leads with that.
    """
    body = f"""
<p class="lede">We audited {F.ecom_shops()} large online shops expecting to find broken product
markup, and did not find it — <strong>zero</strong> had missing or invalid Product schema and
zero had thin product pages, at a median score of {F.ecom_median_score()}. The problems that
did show up are narrower and more dangerous than the ones an SEO pitch usually promises, and
one of them can remove every rich result you have.</p>

<h2>What we actually found</h2>

<p>{F.ecom_shops()} of {F.ecom_attempted()} shops crawled cleanly on {F.ecom_measured()},
{F.ecom_page_cap()} pages each, mostly product pages. {F.ecom_unreachable()} refused the
crawler or timed out and are excluded from every count below — a site that could not be read
cannot fail a check, and counting it as a pass would flatter these numbers.</p>

<div class="wrap-tbl"><table class="cmp"><thead><tr>
<th>Checked</th><th>Shops affected</th></tr></thead><tbody>
<tr><td>Missing, invalid or incomplete Product schema</td>
<td><strong>{F.ecom_schema_problems()} of {F.ecom_shops()}</strong></td></tr>
<tr><td>Product pages with almost no content</td>
<td><strong>{F.ecom_thin()} of {F.ecom_shops()}</strong></td></tr>
<tr><td>Indexing problems (noindex, canonical conflicts)</td>
<td><strong>{F.ecom_indexing()} of {F.ecom_shops()}</strong></td></tr>
<tr><td>Star ratings Docket could not confirm were visible</td>
<td><strong>{F.ecom_rating_unconfirmed()} of {F.ecom_shops()}</strong></td></tr>
</tbody></table></div>

<p>Scores ran from {F.ecom_worst_score()} to {F.ecom_best_score()}. These are well-resourced
retailers with teams, so this is the easy case rather than a random sample of the web — but it
is worth saying plainly that the standard pitch, that your product markup is quietly broken,
did not survive contact with ten real shops.</p>

<h2>The one that carries real risk</h2>

<p>{F.ecom_rating_unconfirmed()} shops carry <code>AggregateRating</code> markup on pages where
Docket could not confirm, from the HTML alone, that a rating is actually shown to a visitor.
That is not an accusation — it is the check declining to make one. Google's
<a href="https://developers.google.com/search/docs/appearance/structured-data/review-snippet">review
snippet guidance</a> requires the rating to be visible on the page carrying the markup, and the
consequence of getting it wrong is a manual action that removes every rich result across the
whole site, not just the offending page.</p>

<p>Star widgets are very often drawn in JavaScript, so the served HTML has markup and no
visible rating while the rendered page is perfectly compliant. Docket used to call that a
violation and was wrong about a real shop; it now demands rendered evidence before it accuses,
and says "unconfirmed" otherwise. Run <code>--render</code> and the question is settled either
way.</p>

<h2>Where a competitor is better for this</h2>

<p>If what you need is to pull the price, the availability and the SKU off every product page
and diff them against your feed, <a href="/vs/screaming-frog-alternative/">Screaming Frog</a>
does that properly with custom extraction and Docket does not do it at all. We
<a href="/learn/audit-tool-accuracy/">decided against building it</a> rather than shipping a
worse version of a mature feature, and for inventory-scale auditing that decision means
Screaming Frog is the right tool. Its crawl has no page ceiling either, which matters when a
catalogue runs to six figures.</p>

<p>For keyword and competitor product research, Ahrefs and Semrush own search-volume indexes
that Docket has no equivalent of and is not trying to build.</p>

<h2>What Docket is for, on a shop</h2>

<p>The four lanes a crawler does not cover, which on an ecommerce site are: whether an AI
answer <a href="/learn/ai-substitution/">replaces the page</a> a customer would have visited;
whether your <a href="/learn/brand-consistency/">brand is consistent</a> across a catalogue
built by several teams over several years; whether the checkout path's copy actually converts;
and whether your <a href="/learn/dead-contact-address/">contact address can receive mail</a>,
which for a shop taking returns is not a small thing.</p>

<p>Plus the deploy gate. A catalogue site ships constantly, and
<a href="/for/developers/">a noindex reaching production</a> is the mistake that costs the most
and is noticed the latest.</p>

<p><a class="btn" href="/download/">Download Docket</a></p>
"""
    return render(
        cat="for", slug="ecommerce",
        title="Docket for ecommerce: what 10 real shops actually got wrong",
        desc=(f"We audited {F.ecom_shops()} large online shops. Zero had broken Product "
              f"schema and zero had thin product pages. What did show up, and where "
              f"Screaming Frog is the better tool."),
        h1="Docket for online shops",
        crumb='<a href="/">Docket</a> / <a href="/for/">For you</a> / Ecommerce',
        body=body,
        published="2026-08-07",
        faq=[
            ("Do online shops usually have broken product schema?",
             f"Not in our sample. We audited {F.ecom_shops()} large retailers and none had "
             f"missing, invalid or incomplete Product schema, and none had thin product "
             f"pages. These are well-resourced companies rather than a random sample, but "
             f"the common claim that your product markup is quietly broken did not survive "
             f"contact with them."),
            ("What happens if my star ratings are not visible?",
             "Google requires the rating to be visible on the page carrying the "
             "AggregateRating markup, and a manual action for breaking that removes rich "
             "results across the entire site rather than just the page at fault. The common "
             "false alarm is a star widget drawn in JavaScript: the served HTML has no "
             "visible rating and the rendered page is fine. Check the rendered page before "
             "believing any tool that accuses you of this."),
            ("Can Docket extract prices from every product page?",
             "No. Screaming Frog does that with custom extraction and it is the right tool "
             "for auditing a catalogue against a feed. Docket deliberately does not compete "
             "there — it also has a page ceiling per crawl, which matters for a large "
             "catalogue."),
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
<p>Docket only gives this advice to businesses that actually compete locally. A software company
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
<p>Docket checks all of these and tells you which of your business's specific signals are
missing. <a href="/download/">Download it</a> and run one audit — it takes a few minutes.</p>
"""
    return render(
        cat="for", slug="local-business",
        title="Local SEO audit: why you are not in the map pack (2026)",
        desc=("The four signals that decide map-pack visibility — LocalBusiness schema, NAP "
              "consistency, geo targeting and review markup — and the mistake franchises make."),
        h1="Why your business is not in the map pack",
        crumb='<a href="/">Docket</a> / <a href="/for/">For you</a> / Local business',
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


#: Somebody else's measurement, dated and linked, because we cannot reproduce
#: it. Docket sees what a crawler *would* be able to read on one site; Vercel
#: sees what crawlers actually did across its network. The SaaS page needs both
#: halves and they can only come from different places.
#:
#: Same rule as comparisons.VERIFIED: the figures live here with their source
#: rather than being typed into a sentence, so a correction is one edit and the
#: prose cannot drift away from what was read.
VERCEL_CRAWLER = {
    "url": "https://vercel.com/blog/the-rise-of-the-ai-crawler",
    "read_on": "10 August 2026",
    "chatgpt_js": "11.50",
    "claude_js": "23.84",
}


def for_saas() -> Path:
    """The SaaS audience page the /for/ hub had been holding open.

    Written from the Index's own SaaS slice rather than from the pitch, and the
    slice contradicts the pitch: essentially nobody in it blocks an answer
    engine. So the page spends its length on the failure that is invisible in
    robots.txt — a marketing site that is empty until JavaScript runs — and
    says plainly that the scary version of the story is not what the data says.

    Deliberately shares no heading with the other /for/ pages. A SaaS site's
    problems are its own: rendering, a docs subdomain competing with marketing,
    and pages nobody links to any more.
    """
    v = VERCEL_CRAWLER
    saas_hosts = ", ".join(F.category_hosts("saas"))
    signal_hosts = ", ".join(F.category_content_signal_hosts("saas"))
    body = f"""
<p class="lede">The story sold to SaaS marketers is that AI crawlers are being shut out of the
web and you are probably shut out too. Measured, that is not what is happening:
<a href="/index/">the Docket Index</a> holds {F.category_n('saas')} SaaS sites and
{len(F.category_citation_hosts('saas'))} of them block a crawler that feeds an answer engine.
The failure that actually costs you a citation is not in <code>robots.txt</code> at all. The
crawler is let in, it arrives, and the page is empty when it gets there.</p>

<h2>The blocking story, measured</h2>

<p>On {F.index_measured()} we read <code>robots.txt</code> for {F.category_n('saas')} SaaS
hosts as part of the Index. All {F.category_n('saas')} answered with a file our parser could
read. Named so you can judge the sample: {saas_hosts}.</p>

<div class="wrap-tbl"><table class="cmp"><thead><tr>
<th>Crawler</th><th>What it feeds</th><th>Disallowed by</th></tr></thead><tbody>
<tr><td>OAI-SearchBot</td><td>ChatGPT's index</td>
<td><strong>{F.category_blocked('saas', 'OAI-SearchBot')} of
{F.category_n('saas')}</strong></td></tr>
<tr><td>Claude-SearchBot</td><td>Claude's index</td>
<td><strong>{F.category_blocked('saas', 'Claude-SearchBot')} of
{F.category_n('saas')}</strong></td></tr>
<tr><td>PerplexityBot</td><td>Perplexity's index</td>
<td><strong>{F.category_blocked('saas', 'PerplexityBot')} of
{F.category_n('saas')}</strong></td></tr>
<tr><td>Google-Extended</td><td>Gemini grounding</td>
<td>{F.category_blocked('saas', 'Google-Extended')} of {F.category_n('saas')}</td></tr>
<tr><td>GPTBot</td><td>OpenAI training</td>
<td>{F.category_blocked('saas', 'GPTBot')} of {F.category_n('saas')}</td></tr>
<tr><td>ClaudeBot</td><td>Anthropic training</td>
<td>{F.category_blocked('saas', 'ClaudeBot')} of {F.category_n('saas')}</td></tr>
<tr><td>CCBot</td><td>Common Crawl</td>
<td>{F.category_blocked('saas', 'CCBot')} of {F.category_n('saas')}</td></tr>
</tbody></table></div>

<p>{F.category_mentions_ai('saas')} of the {F.category_n('saas')} name an AI crawler at all,
{F.category_sitemap('saas')} declare a sitemap, and four publish Content-Signal preferences:
{signal_hosts}. These are large companies with people whose job this is, so it is the easy
case rather than a random sample of SaaS — a seed-stage site that inherited its
<code>robots.txt</code> from a boilerplate repo is a different risk, and that is the site
worth checking. But the pitch that everyone is pulling up the drawbridge, or that you are shut
out by accident, did not survive contact with these {F.category_n('saas')}.</p>

<p>The related failure is a rule aimed at a crawler retired years ago:
{F.directives_dead_pct()}% of the sites writing AI rules at all across the Tranco top 10,000
carry one, <code>anthropic-ai</code> alone sitting on {F.token_sites('anthropic-ai')} of them.
Docket reads both in the same pass as everything else — one check, not a strategy.</p>

<h2>What actually costs you the citation</h2>

<p>Vercel measured the other half on its own network:
<a href="{v['url']}" rel="nofollow noopener">none of the major AI crawlers render
JavaScript</a>. ChatGPT's crawler fetched JavaScript files in {v['chatgpt_js']}% of requests
and Claude's in {v['claude_js']}%, and neither executed them. Applebot and Gemini are the
exceptions, because both sit on infrastructure that already renders. That is their
measurement, read on {v['read_on']}; we cannot reproduce it, and if crawler behaviour has
moved since, the argument below moves with it.</p>

<p>What Docket shows you is your own side of that. It fetched notion.so twice, once as a
crawler and once through WebKit: the served HTML held 0 characters of text and 0 links, the
rendered page held 2,068 characters and 106 links —
<a href="/learn/javascript-rendering/">the full measurement is here</a>. Notion is not a badly
built site. It is a normally built one, and to a crawler that does not execute code it is a
blank sheet.</p>

<p>So if your marketing site is a React or Next.js app without server rendering on every
route: your <code>robots.txt</code> says yes and your framework says nothing. Docket reports
how much of each page's text and links exist before hydration, which is the number to take to
whoever owns the front end.</p>

<h2>What a first audit surfaces on a SaaS site</h2>

<p>A caveat, because the alternative is inventing a statistic: we have not audited a
representative sample of SaaS sites and cannot tell you how often each of these fires. What
follows is what the SaaS <em>shape</em> produces — a marketing site, a docs subdomain, a
changelog and a pricing page — roughly in the order the ranking puts them.</p>

<div class="wrap-tbl"><table class="cmp"><thead><tr>
<th>#</th><th>What turns up</th><th>Why it bites here</th></tr></thead><tbody>
<tr><td>1</td><td>Marketing copy absent from the served HTML</td>
<td>Your homepage and feature pages read as blank to everything that does not
render</td></tr>
<tr><td>2</td><td>Navigation that only exists after hydration</td>
<td>No links in the HTML means no discovery path, so everything below the nav goes
undiscovered</td></tr>
<tr><td>3</td><td>A pricing page with no structured data</td>
<td>Plan names and prices drawn client-side are invisible twice over — to the crawler, and to
any rich result</td></tr>
<tr><td>4</td><td>Docs and marketing aimed at one query</td>
<td>Two hosts, two titles, one intent. Google picks, and it is usually not the page with the
trial button</td></tr>
<tr><td>5</td><td>Orphaned feature pages</td>
<td>Shipped for a launch, linked from one blog post, now at depth five or reachable from
nothing</td></tr>
<tr><td>6</td><td>Changelog and blog rot</td>
<td>Dead outbound links, 404s from renamed features, and no machine-readable date on
anything</td></tr>
<tr><td>7</td><td>Near-duplicate comparison pages</td>
<td>Forty pages off one template read as one page. Thinness is survivable; sameness is the
part that gets a set flagged</td></tr>
<tr><td>8</td><td>No entity definition</td>
<td>Nothing in the markup says which company you are. Organization plus
<code>sameAs</code> is the cheapest item on this list to fix</td></tr>
</tbody></table></div>

<p>Each finding arrives with the change rather than the category — the JSON-LD block, the tag,
the header — because a ranked plan you still have to translate into a ticket is not a plan.
The CSV export drops into Linear or Jira without anyone retyping it.</p>

<h2>Two hosts, one query</h2>

<p>The most common structural problem on a SaaS site is not technical. It is that two teams
wrote a page about the same thing. Marketing owns <code>/pricing</code>, docs owns
<code>docs.example.com/billing</code>, and both answer "what does this cost". You do not get
to choose which one a search engine shows.</p>

<p>Docket audits one host per crawl, so this is two runs and a comparison you make yourself.
The duplicate check works inside a single crawl and not across two, and saying otherwise would
describe a feature that does not exist. What you get is every title and description in one
place per host, which is enough to see the collisions in a few minutes — and the docs run
usually turns up auto-generated API pages nobody meant to index.</p>

<h2>What this will not do</h2>

<ul>
<li><strong>No search volumes, no backlinks, no rank tracking.</strong> There is no index
behind Docket and there will not be one.</li>
<li><strong>It does not measure Core Web Vitals.</strong> LCP, INP and CLS are field metrics
from real users on real connections, and one machine on a fast desk cannot produce them.
Docket flags the patterns that cause them — render-blocking resources, layout-shift risk, page
weight, slow server response — and you confirm the numbers in Search Console. With your own
Google API key it will read Chrome UX Report data, which is Google measuring, not us.</li>
<li><strong>It does not see behind your login.</strong> The product is not audited. The
marketing site, docs, blog and pricing page are.</li>
<li><strong>It does not run prompts against models,</strong> so it cannot tell you whether
ChatGPT named you this morning. <a href="/vs/">Profound, Otterly and Peec</a> do that.</li>
<li><strong>Rendering is a sample</strong> — ten of the shallowest pages by default, which
answers "is this client-rendered and what is it costing me" without turning a five-minute
audit into an hour. It is not a full rendered crawl of a large application.</li>
<li><strong>It is macOS on Apple Silicon.</strong> No Windows, no Linux desktop, no web
version. The CLI inside the bundle runs on <a href="/for/developers/">macOS CI runners</a>.</li>
</ul>

<h2>When Docket is the wrong tool for you</h2>

<p>Four cases, and it is cheaper for both of us if you find yours here.</p>

<p><strong>You need keyword research, backlink data or rank tracking.</strong> Those need an
index of the whole web and Docket has none. Buy the subscription; this does not replace
it.</p>

<p><strong>You need a multi-seat dashboard.</strong> There is no server, no account and no
shared workspace — audit history sits in <code>~/.docket/</code> as plain JSON on one Mac.
That is the point when a founder is auditing their own site, and a genuine problem for a
growth team of six who want one live view. Exports travel; state does not.</p>

<p><strong>Your site is one static landing page.</strong> Running {N_CHECKS} checks across
{N_LANES} areas against six pages is overkill, and a free single-page checker will tell you
the same three things in thirty seconds.</p>

<p><strong>You need rendered crawling at volume.</strong> A six-figure URL count with
JavaScript execution on every page is
<a href="/vs/screaming-frog-alternative/">Screaming Frog's</a> territory and has been for
years.</p>

<h2>Why the price is a number rather than a plan</h2>

<p>{PRICE_STR}, once, from v1.0 — and {FREE_CLAUSE}. No seats, no
crawl credits, no renewal date. You price a SaaS product yourself, so you know what a
recurring line item does to a buying decision at a company that already has eleven of
them.</p>

<p>The rest follows from running on your own machine: no upload, no telemetry, no account, and
results that stay in <code>~/.docket/</code> as JSON you can read with <code>cat</code>. Save
the site and scheduled re-audits report what changed, regressions first — which is how you
learn a <code>noindex</code> reached production on Tuesday rather than from a traffic graph
three weeks later. The schedule lives inside the app rather than in launchd, so it runs while
Docket is open and picks up anything overdue the next time you launch it; if you need the crawl
to happen whether or not anyone is at the machine, that is what a hosted crawler is for.</p>

<p><a class="btn" href="/download/">Download Docket</a></p>
"""
    return render(
        cat="for", slug="saas",
        title="Docket for SaaS: audit your marketing site and docs",
        desc=(f"The blocking scare is not the SaaS story: "
              f"{len(F.category_citation_hosts('saas'))} of {F.category_n('saas')} SaaS "
              f"sites in our Index shut an answer engine out. The real problem is a page "
              f"that is blank until JavaScript runs."),
        h1="Docket for SaaS companies",
        crumb='<a href="/">Docket</a> / <a href="/for/">For you</a> / SaaS',
        body=body,
        published="2026-08-10",
        faq=[
            ("Will Docket tell me if ChatGPT mentions my product?",
             "No. Docket does not run prompts against any model, so it cannot see what an "
             "assistant told someone yesterday. It measures what decides whether you are "
             "eligible to be cited at all: whether AI crawlers are allowed in, whether your "
             "pages carry their content in the served HTML, and whether your entity markup "
             "makes it clear which company you are. Profound, Otterly and Peec track "
             "citations themselves."),
            ("Do AI crawlers read JavaScript-rendered pages?",
             f"Mostly not. Vercel measured this across its own network and found that none of "
             f"the major AI crawlers render JavaScript: ChatGPT's crawler fetched JavaScript "
             f"files in {v['chatgpt_js']}% of requests and Claude's in {v['claude_js']}%, and "
             f"neither executed them. Applebot and Gemini are the exceptions, because both "
             f"run on infrastructure that already renders. If your marketing pages are "
             f"client-rendered, the rest of them see whatever your server sent."),
            ("Can Docket audit my docs subdomain and my marketing site together?",
             "Not in one crawl. Point it at each host separately and read the two title lists "
             "side by side, because the duplicate check works inside a single crawl rather "
             "than across two. That comparison takes a few minutes by hand, and describing it "
             "as automatic would mean describing a feature that does not exist."),
            ("Does Docket measure Core Web Vitals?",
             "No. LCP, INP and CLS are field metrics that come from real users on real "
             "connections, and nothing running on one machine can produce them. Docket flags "
             "the markup and server patterns that cause bad vitals - render-blocking "
             "resources, layout-shift risk, page weight, slow server response - and you "
             "confirm the actual numbers in Search Console. It will read Chrome UX Report "
             "field data if you add your own Google API key, which is Google measuring rather "
             "than Docket measuring."),
            ("Is Docket really a one-time purchase?",
             f"Yes. {PRICE_STR} once from v1.0, and the current build is free while "
             f"{RELEASE} is in beta. There are no seats, no crawl credits, no account and no "
             f"telemetry, and audit history is stored on your Mac in ~/.docket/ as plain "
             f"JSON."),
        ],
    )


def howto_hub() -> Path:
    body = f"""
<p class="lede">Fix guides for the specific problems Docket reports. Each one explains what the
issue costs you, then gives the change to make.</p>

<p>Before any individual guide, the question that decides whether an audit is worth
anything: <strong>what do you do first?</strong> A list of {N_CHECKS} checks against a real
site produces dozens of findings, and the order you work them in matters more than any single
fix.</p>

<h2>The order to fix things in</h2>

<p>Docket ranks every finding by the same formula, and it is worth knowing because you can
apply it by hand to any tool's output:</p>

<pre><code>priority = severity x impact x reach / effort</code></pre>

<p>Three of those are obvious. The fourth is where most tools go wrong: <strong>reach grows
sub-linearly</strong> in the number of pages affected — a capped square root rather than a raw
count. Without that damping, a trivial nit on every page of a large site outranks a
<code>noindex</code> on your homepage, and the report becomes a list you scroll past. Sorting
by "number of pages affected", which is the default in several crawlers, is exactly that
failure.</p>

<p>In practice this collapses to a short rule. Fix anything that stops a page being indexed at
all, first and immediately — those are rare and they are absolute. Then work down by
priority, which naturally puts small changes on important pages above large changes on
unimportant ones. A finding marked TRIVIAL or SMALL effort with HIGH severity is almost always
the best hour you will spend.</p>

<h2>What a fix guide here will not do</h2>

<p>None of these say "improve your content" or "build quality links". If a guide cannot name
the exact element to change, it has not earned the page. Where a change depends on something
only you know — whether you want AI engines training on your writing, for instance — the
guide sets out the decision rather than making it for you.</p>

<h2><a href="/how-to/fix-ai-crawler-access/">Fix AI crawler access in robots.txt</a></h2>
<p>How to let ChatGPT, Perplexity and Claude read your site without giving away training data —
they are separate decisions and need separate rules. Measured against
{F.directives_hosts()} sites' robots.txt files, most people who block AI crawlers get this
wrong in the same direction.</p>

<h2>Redirecting http:// to https://</h2>
<p>The 301 every host configures differently, and the certificate state that makes the
"Enforce HTTPS" setting refuse to turn on — written from our own site failing this exact
check. <a href="/how-to/redirect-http-to-https/">How to redirect http:// to https:// →</a></p>

<h2>hreflang return tags</h2>
<p>The only common SEO tag that cannot be checked by reading the page it sits on: a
declaration that goes one way is ignored entirely, and every tag looks correct in isolation.
<a href="/how-to/fix-hreflang-return-tags/">How to fix hreflang return tags →</a></p>

<h2>Conflicting canonical tags</h2>
<p>Two canonicals on one page, a canonical pointing at a noindex page, and the section-wide
mistake that can cost a site its entire long tail while every page still returns 200.
<a href="/how-to/fix-conflicting-canonicals/">How to fix conflicting canonicals →</a></p>

<h2>Soft 404s</h2>
<p>A missing page that answers 200 turns every mistyped URL into an indexable page. How to
check it in one command, and the fix for each cause.
<a href="/how-to/fix-soft-404s/">How to fix soft 404s →</a></p>

<h2>Structured data errors</h2>
<p>Invalid JSON-LD is discarded whole rather than partially read, so a page with complete
markup and one trailing comma is treated like a page with none. The five ways schema breaks,
and why a single-URL validator misses most of them.
<a href="/how-to/fix-structured-data-errors/">How to fix structured data errors →</a></p>

<h2>Layout shift (CLS)</h2>
<p>Almost always images with no width and height: the browser cannot reserve the space, so
content jumps as they load. The fix, the four other causes, and why a crawler can report the
risk but never the score. <a href="/how-to/fix-layout-shift/">How to fix layout shift →</a></p>

<h2>Duplicate title tags</h2>
<p>Rarely a penalty and routinely misdiagnosed: what duplicate titles actually cost you, the
character limit that does not exist, and the fix by what caused them — pagination, facets,
product variants, near-identical location pages.
<a href="/how-to/fix-duplicate-title-tags/">How to fix duplicate title tags →</a></p>

<h2>Missing security headers</h2>
<p>HSTS, nosniff and Referrer-Policy, what each one actually does, and where to set them on
every common host. Written as a self-audit, because this site fails two of the three checks
it is describing and the reason is worth reading.
<a href="/how-to/fix-missing-security-headers/">How to fix missing security headers →</a></p>

<h2>Gating a deploy on regressions</h2>
<p>Audit production against staging and fail the build on what the deploy introduced. The
case for diffing findings rather than a score: stripping every title tag from a test site
left the score unchanged and registered three improvements.
<a href="/how-to/gate-a-deploy-on-seo-regressions/">How to gate a deploy →</a></p>

<h2>Link previews with no image</h2>
<p>Three different faults look identical when you paste a link: no Open Graph tags, an
og:image pointing at a file that no longer exists, or an image a scraper cannot reach. The
dead image is the one nobody catches, because every platform caches the preview it scraped
first — so the person who broke it is the last to see it broken.
<a href="/how-to/fix-missing-open-graph-tags/">How to fix a broken link preview →</a></p>

<h2>Title tags that fit</h2>
<p>Search engines truncate by pixel width, not character count — which makes the usual "under
sixty characters" advice wrong on any site that is not entirely English.
<a href="/how-to/write-title-tags-that-fit/">How to write title tags that fit →</a></p>

<h2>More coming</h2>
<p>Further guides are being written, one per issue Docket reports. They will appear as each is written properly rather than as
variations on a template.</p>
"""
    return render(
        cat="how-to", slug="",
        title="How to fix common SEO problems — Docket",
        desc=("Fix guides for the specific issues an audit reports, in the order "
              "worth doing them, with the exact change to make."),
        h1="Fix guides",
        crumb='<a href="/">Docket</a> / Fix it',
        body=body,
        schema_type="CollectionPage",
    )


def howto_ai_access() -> Path:
    body = f"""
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
<p>In our measurement of {F.index_n()} major sites, {F.index_conflated_pct()}% of those
blocking any AI crawler had also blocked the search crawlers — but reading the robots.txt of
the Tranco top 10,000 later showed the opposite at scale: of {F.directives_blocks_any():,}
sites blocking any AI crawler there, {F.directives_training_only_pct()}% blocked training and
left search alone. <a href="/index/">The data is here</a>.</p>

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
<p>Docket parses robots.txt the way Google does and tells you, per crawler, whether it can
reach your site and what blocking it actually costs. That check is one of {N_CHECKS} and runs in the
first few seconds of any audit.</p>
<p><a class="btn" href="/download/">Download Docket</a></p>
"""
    return render(
        cat="how-to", slug="fix-ai-crawler-access",
        title="Let ChatGPT and Perplexity read your site (robots.txt, 2026)",
        desc=("Search and training crawlers are separate decisions. The robots.txt that allows "
              "citation while opting out of training, and the shared snippet that gets it "
              "wrong."),
        h1="How to fix AI crawler access",
        crumb='<a href="/">Docket</a> / <a href="/how-to/">Fix it</a> / AI crawler access',
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
<p>Docket is desktop software that runs on your Mac. This policy covers both the application
and this website.</p>

<h2>The application</h2>
<p>Docket collects nothing. There is no account, no telemetry, no crash reporting and no licence
check.</p>
<p>An earlier version of this policy said the only network requests the app makes are to the
website you ask it to audit. That was not accurate, and a privacy policy is the last document
that should be approximately true. Docket makes requests to three kinds of destination:</p>
<ul>
<li><strong>The site you asked it to audit.</strong> The crawl itself, from your machine, and
the edge-access checks that re-request your pages while identifying as each AI crawler.</li>
<li><strong>docketseo.app, for one public file.</strong> The knowledge refresh connector is on
by default and fetches <code>/data/knowledge.json</code> — the current AI crawler list, Core
Web Vitals thresholds and ranking notes. It is a GET with no body and no query string. It
carries no identifier and tells the server nothing about what you are auditing; the request
is indistinguishable from someone opening that file in a browser.</li>
<li><strong>Google, only if you configure it.</strong> The PageSpeed Insights connector needs
your own Google API key and does nothing without one. When enabled it necessarily sends
Google the URL you asked it to measure, because that is what the API takes. Leave it off and
no request is made.</li>
</ul>
<p>Every connector can be turned off individually, and an offline switch disables all of them
at once, leaving only the crawl of your own site.</p>
<p>Audit results and your saved-site list are stored on your machine in <code>~/.docket/</code>
as plain JSON files. They are never transmitted. Deleting that folder removes them permanently.</p>

<h2>This website</h2>
<p>This site is static and runs two third-party scripts. The first is
<a href="https://plausible.io/privacy-focused-web-analytics">Plausible</a>, which counts page
views. Plausible states that it uses no cookies, collects no personal data and does not track
visitors across sites; it is hosted in the EU. Nothing about your audits reaches it &mdash;
audits run on your Mac and this website never sees them. Standard server logs may record IP
addresses and requested URLs, which are used only to keep the site running.</p>
<p>The second is <a href="https://usesled.com">Sled</a>, which credits the right person when
somebody recommends Docket. It is the only thing on this site that can set a cookie, and it is
conditional: arrive through an affiliate link and a single <code>ta_ref</code> cookie records
which affiliate sent you, so they are paid if you buy. Arrive from a search result, a bookmark
or a link of ours and no cookie is set at all &mdash; which is what almost every visitor does.
It records which affiliate sent a visit, never who the visitor is.</p>
<p>This paragraph replaced one that said the site &ldquo;sets no cookies&rdquo; and runs
&ldquo;one third-party script&rdquo;. Both were true until Sled was added, and a privacy page
that enumerates what a site does not do is only worth reading if the enumeration stays
complete.</p>
<p>If you would rather not be counted, any content blocker stops it, and nothing on this site
depends on it loading.</p>

<h2>Data you give us</h2>
<p>There is no contact form and no mailing list. If you open an issue on GitHub, that issue
is public and GitHub's privacy policy applies to it; we hold nothing separately.</p>

<h2>Changes</h2>
<p>If this policy changes, the updated version appears on this page.</p>

<h2>Contact</h2>
<p>Questions about privacy or anything else: <a href="/contact/">get in touch</a>.</p>
"""
    return render(
        cat="legal", slug="privacy",
        title="Privacy policy — what Docket collects, and what it does not",
        desc="Docket collects nothing. No account, no telemetry, no analytics on this site.",
        h1="Privacy policy",
        crumb='<a href="/">Docket</a> / Privacy',
        body=body,
        schema_type="WebPage",
    )


def terms() -> Path:
    """Terms of use, including the commercial terms of the sale.

    DRAFT — NOT REVIEWED BY A LAWYER. The product facts in it were read out of
    docket-app and out of this repository; the legal shape of it has had no
    professional eye on it, and the tax section is an open question rather than
    an answer.

    Before this rewrite the page described a free download and nothing else.
    A grep of the built file returned zero occurrences of refund, cancel,
    payment, VAT, tax, consumer, governing law, jurisdiction and termination,
    on the terms page of a product with a price on eleven other pages of the
    same site.

    The liability clause was one sentence excluding everything. That is
    unenforceable against a consumer almost everywhere it would be read, and an
    exclusion a court strikes out protects nobody — so it is now a cap at the
    amount paid with the usual carve-outs, which is both smaller and likely to
    survive.
    """
    if BETA_FREE:
        price_para = f"""
<p><strong>Today the price is nothing.</strong> {RELEASE} is a free beta. It downloads without
payment, it does not expire, and this site has no checkout, so no sale has taken place and the
commercial sections below describe terms that take effect when one can.</p>
<p>From v1.0 Docket costs {PRICE_STR} in US dollars, paid once. Not a subscription: there is no
renewal date, no seat count and nothing to cancel, because nothing recurs.</p>"""
    else:
        price_para = f"""
<p>Docket costs {PRICE_STR} in US dollars, paid once. Not a subscription: there is no renewal
date, no seat count and nothing to cancel, because nothing recurs.</p>"""

    # Same escape as on the refunds page, and the same reason.
    seller = SELLER.replace("&", "&amp;")
    # The Linux tarball is promised only when the release actually carries one.
    # The download page described one in detail for seven releases during which
    # none was published; a terms page is a worse place to repeat that.
    linux_clause = (", plus a Linux command-line tarball"
                    if LINUX_NAME else "")

    tax_para = f"""
<p>Prices are shown in US dollars. Whether sales tax or VAT is added at checkout, and which
party is responsible for remitting it, depends on {PROCESSOR or 'the payment processor'} and on
where you are buying from. That is not settled yet and this paragraph will say which it is
before a checkout opens, rather than leaving you to discover it on the payment
screen.</p>""" if not PROCESSOR else f"""
<p>Prices are shown in US dollars. Any sales tax or VAT due is calculated and shown by
{PROCESSOR} at checkout, before you pay.</p>"""

    body = f"""
<p>By downloading or using Docket you agree to these terms. If you buy a licence, the sections
on price, delivery and refunds are part of that agreement.</p>

<h2>Who you are dealing with</h2>
<p>Docket is published and sold by {seller}, of {seller_address()}. The software is written by
Matt Kerr. Correspondence goes through <a href="/contact/">the channels on the contact
page</a>.</p>

<h2>What it costs</h2>
{price_para}
<p>One purchase covers you, the person or company that paid, on any machine you own or control.
You may audit any number of websites with it, including on behalf of clients, and you may
charge those clients for the work. There is no per-seat price and no crawl allowance.</p>

<h2>What you may not do with it</h2>
<p>Do not resell, sublicense or redistribute the application itself, and do not offer it as a
hosted service to people who have not bought it. Reports it produces are yours: send them,
rebrand the CSV and JSON exports, bill for them.</p>

<h2>Delivery</h2>
<p>Delivery is a download. Docket ships as a notarised macOS disk image of {DMG_SIZE} from
<a href="https://github.com/mattkerr09/docket-site/releases">the releases page</a>{linux_clause}.
There is nothing to post and no activation email to wait for.</p>
<p>Two consequences of how this is sold, both stated because a buyer will meet them. The
download link is public, so payment is not the thing that makes the file reachable — what payment
buys is the licence key that lets it run. And updates are published to every copy: while Docket
is on version 1.x, upgrades cost nothing and install through the app's own updater. Whether a
future 2.0 is a paid upgrade has not been decided; if it ever is, the copy you paid for keeps
working.</p>

<h2>Refunds</h2>
<p>Thirty days, no conditions. The full policy, including how to ask and what happens to your
copy afterwards, is on <a href="/legal/refunds/">the refund page</a> and forms part of these
terms.</p>

<h2>Tax</h2>
{tax_para}

<h2>Responsible use</h2>
<p>Docket crawls websites. You are responsible for the sites you point it at. Its defaults are
deliberately gentle — requests are rate-limited, it honours <code>robots.txt</code> unless you
turn that off, and it backs off when a server signals it is being asked for too much. Please do
not raise those limits on sites you do not own or have permission to crawl.</p>

<h2>No warranty</h2>
<p>Docket is provided as is. It reports what it can observe in the HTML and HTTP responses a
site returns. It cannot guarantee rankings, traffic or any commercial outcome, and its findings
are advice rather than a certification. Search engines change their behaviour without notice.</p>
<p>The scope page in every report lists what was and was not measured. Please read it before
relying on an audit for a decision that matters.</p>

<h2>Liability</h2>
<p>If you are a consumer, nothing in these terms removes or reduces a right you have under the
law where you live, and the rest of this section applies only as far as that law allows.</p>
<p>Subject to that, and to the extent the law permits: the total liability of {seller} arising
out of Docket or these terms is limited to the amount you paid for the licence, and neither
lost traffic, lost revenue, lost rankings, lost profits nor loss of data is recoverable.
Liability for fraud, for fraudulent misrepresentation, and for death or personal injury caused
by negligence is not excluded, because it cannot be.</p>

<h2>Ending the licence</h2>
<p>Your licence ends if you take a refund — on the day it is issued — or if you break these
terms in a way you do not put right after being asked. In either case, delete the application.
Your licence key stops validating in either case, and the application stops running audits
within about a day of that — the check is daily, and a revoked key is refused immediately
rather than being given the offline grace period. Deleting the application is still asked of
you, but it is no longer the only thing standing between a cancelled licence and continued
use.</p>
<p>Your audit history in <code>~/.docket/</code> is yours in every case. It was never uploaded,
so there is nothing on our side to delete or withhold.</p>

<h2>Governing law</h2>
<p>These terms are governed by the law of {GOVERNING_LAW}, and any dispute goes to the courts
located there. If you are a consumer resident somewhere else, this does not deprive you of the
protection of any mandatory consumer law of the country you live in, or of the right to bring a
claim in your local courts where that law gives you one.</p>

<h2>Changes to these terms</h2>
<p>The version in force for a purchase is the one published on the day it was made. Changes
appear on this page and apply from the day they appear, not before.</p>

<h2>Contact</h2>
<p><a href="/contact/">Get in touch</a></p>
"""
    return render(
        cat="legal", slug="terms",
        title="Terms of use for Docket and docketseo.app",
        desc=("Licence, price, delivery, refunds, liability and governing law — plus "
              "responsible crawling and the limits of what an audit can promise."),
        h1="Terms of use",
        crumb='<a href="/">Docket</a> / Terms',
        body=body,
        modified="2026-08-11",
        schema_type="WebPage",
    )


def refunds() -> Path:
    """The refund and cancellation policy.

    DRAFT — NOT REVIEWED BY A LAWYER. Every fact in it was read out of this
    repository or out of docket-app rather than taken from a template, but that
    makes it accurate about the product, not compliant. It needs a lawyer's eye
    on the consumer-law paragraph in particular before it is published.

    Written because the page did not exist. `lint.py` has carried the sentence
    "a refund policy should be as short as it can be while staying complete"
    since legal pages were exempted from the word floor — the exemption was
    written for a page nobody had built, which is how a gap survives a year of
    linting.

    Three things in here are unusual and all three are deliberate:

    * **The window is derived, not chosen.** Thirty days is four runs of the
      default weekly cadence in `store.CADENCES`, which is the shortest span
      over which the monitoring feature can demonstrate the thing it is sold
      for. A fourteen-day window would expire before the product had shown its
      own headline capability.
    * **It states that the copy keeps working after a refund.** There is no
      licence server (`home.py`, `pages.py` and `about.py` all promise there is
      not), so no revocation is possible. A policy that implied otherwise would
      be describing software that does not exist.
    * **It carries no conditions.** Docket collects no telemetry, so "unused",
      "fewer than N audits" and "within reason" are all unverifiable. A
      condition the seller cannot check is one applied by mood.
    """
    if PROCESSOR:
        processor_name = PROCESSOR
        processor_ref = f"<strong>{PROCESSOR}</strong>"
    else:
        processor_name = "the payment processor"
        processor_ref = "the payment processor"

    reg_no = f", company number {SELLER_REG_NO}" if SELLER_REG_NO else ""
    # The legal name has an ampersand in it. SELLER stays plain text because it
    # is a name, not markup; the escape happens where it is written into HTML.
    seller = SELLER.replace("&", "&amp;")

    if BETA_FREE:
        beta = f"""
<div class="callout">
<div class="callout-title">There is nothing to refund today</div>
<p>{RELEASE} is free. It downloads without payment, it keeps working, and this site has no
checkout to pay through. This policy is published before there is a transaction behind it
because the {PRICE_STR} is already written on this site, and a price with no refund terms
beside it is half a sentence.</p>
<p>If you have paid money for a copy of Docket, it did not reach us. Say so on
<a href="{ISSUES}">the issue tracker</a> and where it went will be written up in public.</p>
</div>"""
    else:
        beta = ""

    if BILLING_EMAIL:
        channel = f"""
<p>Refund requests go to <a href="mailto:{BILLING_EMAIL}">{BILLING_EMAIL}</a>, or as a reply to
the receipt {processor_name} sends you. Either arrives.</p>"""
    else:
        channel = f"""
<p>Reply to the receipt {processor_name} sends when you buy. That message comes from an address
that accepts replies and it quotes the order reference, which is the one detail needed to find
a payment.</p>

<p>There is no billing address at <code>docketseo.app</code> yet, and the reason is worth having
rather than hiding. Mail to a domain with no MX record does not bounce back to us — it bounces
to you, silently, and we never learn you wrote.
<a href="/learn/dead-contact-address/">That already happened here once</a>, to
<code>hello@docketseo.app</code>, on every page of this site. A build check now resolves the
MX of any address this site prints and refuses to publish one that cannot receive mail. It is
why you are not reading an invented address on this page.</p>

<p>What has changed since that was written: <code>docketseo.app</code> now publishes an MX
record and does accept mail. So the original obstacle is gone, and only a smaller one is left —
delivery to the domain is not the same as a mailbox existing behind a particular name, and the
address we intend to publish has not yet had a real message sent to it and read. The moment it
has, it goes on this page. We would rather show you this sentence than an address nobody has
tested.</p>"""

    body = f"""
<p class="lede">Thirty days from the date of purchase, no conditions and no questions asked, on
any paid copy of Docket. What follows is how to ask, what happens to the copy on your Mac
afterwards, and why the window is thirty days rather than a number picked because it sounded
generous.</p>
{beta}
<h2>The policy</h2>

<p>Ask within 30 days of the date on your receipt and the full purchase price goes back to the
payment method it came from, along with any tax charged on top of it. Docket is sold as one
item at one price, so there is no partial refund to calculate and none is offered.</p>

<p>You do not have to have stopped using it, give a reason, or send evidence of anything.</p>

<h2>Why thirty days</h2>

<p>Three reasons, and each is a fact about this product rather than a convention:</p>

<ul>
<li><strong>You can run the whole thing before paying.</strong> The beta is free and keeps
working, so the evaluation happens before the money does. A refund window is therefore a second
look rather than the first one, and it does not have to carry the whole weight of the
decision.</li>
<li><strong>Monitoring needs weeks to say anything.</strong> The default re-audit cadence is
weekly, and the thing being sold — what changed on your site since last time — is empty on the
first run and thin on the second. Thirty days is four of them. A fourteen-day window would end
before the feature had demonstrated itself, which would make it a policy that quietly excluded
the reason some people bought.</li>
<li><strong>It can be honoured by one person.</strong> Issuing a refund is one action in
{processor_ref}'s dashboard. Nothing has to be reclaimed, deactivated, closed or
chased, so the length of the window costs nothing but the money.</li>
</ul>

<h2>How to ask</h2>
{channel}
<p>Please do not open a GitHub issue about a refund. The tracker is the contact channel for
everything else here and it is deliberately public, which is right for a wrong finding and
wrong for a payment: a refund request carries your name, an order reference and sometimes the
reason you are unhappy, and none of the three belong on a page anyone can read.</p>

<h2>What happens to your copy</h2>

<p>It stops working. Taking a refund revokes the licence key that came with your purchase, and
Docket re-checks that key about once a day — so the copy on your Mac will refuse to run an audit
within roughly a day of the refund being issued. A revoked key is refused immediately and is not
given the offline grace period that a merely-unreachable licence server would allow.</p>

<p>This changed with version 1.1.59. Before it, Docket had no licence server at all and a
refunded copy kept working indefinitely; that is no longer true, and it would be worse to leave
the old promise standing than to say so plainly. Your audit history is untouched either way — see
below.</p>

<p>What is asked is that you delete the application and stop using it. What that rests on is
that you will. The licence granted by <a href="/legal/terms/">the terms of use</a> ends the day
the refund is issued; the enforcement of it is a sentence rather than a switch, and pretending
otherwise would describe software that was not built.</p>

<p>Your audit history is yours and stays yours. It lives on your machine in
<code>~/.docket/</code> as plain JSON — <code>sites.json</code> for the watchlist and
<code>history/</code> for the snapshots. Nothing there was ever uploaded, so nothing there is
deleted from our side, because there is no our side. Removing that folder removes it.</p>

<h2>Conditions that are deliberately absent</h2>

<p>None of these will be asked, because none of them could be checked. Docket has no account
and no telemetry, so nothing ties a payment to a copy of the application, and the seller has no
way to know:</p>

<ul>
<li>how many sites you audited, or whether you opened the app at all;</li>
<li>how many PDF or CSV reports you exported, or who you sent them to;</li>
<li>whether you are asking for the first time or the fourth;</li>
<li>which machines you installed it on.</li>
</ul>

<p>A refund policy conditioned on facts the seller cannot verify is one applied by mood, and
that is worse than having no condition at all. So there are none, and this paragraph exists so
that the absence reads as a decision rather than an oversight.</p>

<p>One correction to make in the same breath, because a page claiming perfect ignorance would
be exactly the sort of claim this tool exists to check. Docket does make one request of its
own accord: on launch it asks <code>docketseo.app/updater.json</code> whether a newer build
exists, and stays silent if there is none or there is no network. That file is static and
served by GitHub Pages. The log behind it records an address and a time, the way any page
fetch does, and it carries no identifier that could be matched against an order — but it is
named here rather than left out.</p>

<h2>When the money arrives</h2>

<p>The refund is issued to the original payment method, because that is what card rules
require and it is also the only route that reliably works. How long it takes to appear on your
statement sits between {processor_name} and your bank, and neither answers to us. No
number of days is promised here for the same reason no response time is promised on
<a href="/contact/">the contact page</a>: an invented figure is worse than an admitted
unknown.</p>

<h2>Chargebacks</h2>

<p>A chargeback and a refund move the same money in the same direction. Ask first — it is
faster for you, and a disputed charge is answered with the same refund plus a copy of this
page, several weeks later, after a fee. If a refund has been asked for and not answered, raise
the chargeback; that is what the mechanism is for.</p>

<h2>If you are buying from outside the United States</h2>

<p>Consumer law where you live may give you rights this policy cannot shorten, and nothing on
this page attempts to. In the UK and across the EU a distance sale of digital content carries a
14-day right to cancel, and a seller is allowed to ask you to give it up in exchange for an
immediate download. Docket does not ask you to give it up. The 30 days above are longer and
carry fewer conditions, so the waiver would buy the buyer nothing and cost the seller a
paragraph of small print.</p>

<h2>Changes to this page</h2>

<p>The version of this policy in force for a purchase is the one published on the day the
purchase was made. If it changes, the new version appears here and applies from that day
forward, not backwards.</p>

<h2>Who you are paying</h2>

<p>Docket is sold by {seller}{reg_no}, of {seller_address()}. The terms of the sale, including
the governing law, are on <a href="/legal/terms/">the terms of use page</a>.</p>
"""
    return render(
        cat="legal", slug="refunds",
        title="Refund policy — 30 days, no conditions",
        desc=("Thirty days from purchase, no conditions — Docket collects no usage data it "
              "could condition one on. How to ask, and what happens to your copy after."),
        h1="Refund and cancellation policy",
        crumb='<a href="/">Docket</a> / Refunds',
        body=body,
        published="2026-08-11",
        schema_type="WebPage",
    )


BUILDERS = [download, for_hub, for_agencies, for_developers, for_ecommerce,
            for_local, for_saas, howto_hub,
            howto_ai_access,
            privacy, terms, refunds]


def build_all() -> list[Path]:
    return [b() for b in BUILDERS]


if __name__ == "__main__":
    for p in build_all():
        print(p)
