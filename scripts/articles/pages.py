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
from render import (  # noqa: E402
    COMPETITORS, DMG, DMG_SIZE, LINUX, LINUX_NAME, LINUX_SIZE, N_CHECKS,
    PRICE_STR, RELEASE, SUMS, render,
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


def download() -> Path:
    body = f"""
<p class="lede">Docket is {PRICE_STR}, paid once, for macOS 12 or later on Apple Silicon.
{DMG_SIZE}. No subscription, no crawl credits, no per-seat pricing — audit as many sites as
you like, for as long as you like. There is no account to create, no licence server to phone,
and no telemetry.</p>

<p><strong>{RELEASE} is free.</strong> The beta downloads without payment and keeps working; the
{PRICE_STR} applies from v1.0. Said plainly because a price on a page beside a button that
charges nothing is the kind of thing this tool exists to flag.</p>

<p><a class="btn btn-lg" href="{DMG}">Download Docket {RELEASE} for Mac</a></p>
<p style="font-size:.92rem;color:var(--text-dim)">Apple Silicon · macOS 12+ · {DMG_SIZE} ·
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

<h2>More coming, and one that is not</h2>
<p>SaaS and in-house marketing pages will appear when each has something specific to say.
Near-duplicate pages are the real flag risk in a programmatic set, not thin ones, so a page
gets written when there is a measurement behind it rather than to fill a gap in a list.</p>

<p>That standard is why the ecommerce page took as long as it did: the honest version could
only be written after auditing real shops, and what came back disagreed with what the page was
going to say. If the other two never produce a finding worth publishing, they will not be
written, and this paragraph will say so rather than promising them indefinitely.</p>
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
              "per-seat or per-crawl cost, and turns scheduled re-audits into a retainer."),
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
than every push, or run the job on a Mac you already own — Docket has no licence server and no
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

<h2>More coming</h2>
<p>Guides for hreflang return tags, conflicting canonicals, soft 404s and structured data
errors are being written. They will appear as each is written properly rather than as
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
<p>This site is static. It sets no cookies, runs no analytics and embeds no third-party
scripts or fonts. Standard server logs may record IP addresses and requested URLs, which are
used only to keep the site running.</p>

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
    body = """
<p>By downloading or using Docket you agree to these terms.</p>

<h2>Licence</h2>
<p>Docket is licensed to you for use on machines you own or control. You may audit any number of
websites, including on behalf of clients.</p>

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
<p>To the maximum extent permitted by law, we are not liable for any loss arising from use of
Docket, including lost traffic, revenue or rankings.</p>

<h2>Contact</h2>
<p><a href="/contact/">Get in touch</a></p>
"""
    return render(
        cat="legal", slug="terms",
        title="Terms of use for Docket and docketseo.app",
        desc="Licence, responsible crawling, and the limits of what an audit can promise.",
        h1="Terms of use",
        crumb='<a href="/">Docket</a> / Terms',
        body=body,
        schema_type="WebPage",
    )


BUILDERS = [download, for_hub, for_agencies, for_developers, for_ecommerce,
            for_local, howto_hub,
            howto_ai_access,
            privacy, terms]


def build_all() -> list[Path]:
    return [b() for b in BUILDERS]


if __name__ == "__main__":
    for p in build_all():
        print(p)
