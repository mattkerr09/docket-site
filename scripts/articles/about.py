#!/usr/bin/env python3
"""About and Contact.

Docket audited docketseo.app and raised content.missing_trust_pages: no About, no
Contact. The check is right, and it is the one finding on our own site that a
buyer would care about more than any technical one. A tool that charges $149
and never says who wrote it is asking for trust it has not offered.

Writing the Contact page turned up something worse than the missing page. The
footer on all 25 pages advertised hello@docketseo.app, and docketseo.app has no
MX record. Under RFC 5321 §5.1 a sender with no MX falls back to the address
record, which here is GitHub Pages — port 25 closed. Every message anyone had
sent to that address bounced. A contact channel that silently fails is worse
than no contact channel, because the sender believes they reached someone.

Nothing on these pages is asserted that was not checked: the signing identity
comes from the certificate in the DMG, the channels are ones that resolve, and
the limits are the real ones.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import facts as F  # noqa: E402
from render import (  # noqa: E402
    DMG_NAME, DMG_SIZE, ISSUES, N_CHECKS, N_LANES, PRICE_STR, RELEASE, REPO,
    VOLUME, render,
)


def about() -> Path:
    body = f"""
<p class="lede">Docket is built by Matt Kerr, one person, in the UK. It is a Mac app that
audits a site's SEO, copy and branding against {N_CHECKS} checks across {N_LANES} lanes,
runs the crawl on your own machine, and costs {PRICE_STR} once — {RELEASE} is free while it
is in beta.</p>

<p>That is the whole company. There is no team page because there is no team, no office
address because there is no office, and no support desk because there is one person reading
<a href="{ISSUES}">the issue tracker</a>. Saying so is more useful than a stock photo.</p>

<h2>Why it exists</h2>

<p>Every SEO tool worth using is a subscription to somebody's crawler farm. You paste in a
domain, a queue somewhere fetches it, and you pay monthly for the privilege of being told
what your own HTML says. The crawl is the cheap part. The recurring bill is for the servers,
and the servers exist because the tool was built as a service rather than as software.</p>

<p>Docket is the other shape. The audit engine is Python with no third-party dependencies at
all, frozen into the app, and it runs on your Mac. There is no account, no crawl credit, no
per-seat price and no queue. Audit the same site forty times in an afternoon; nobody is
counting, because there is nobody to count.</p>

<h2>What that changes about the findings</h2>

<p>Running locally is not only a pricing decision. A crawler farm sees your site as an
anonymous datacentre IP; your Mac sees it the way a person does, and can be told to
introduce itself as any crawler you like. That is how Docket can tell you what your CDN
returns to <code>GPTBot</code> specifically, rather than what your robots.txt claims it
should.</p>

<p>It is also why the awkward findings are possible. Docket will tell you your AI opt-out is
unenforceable, that your directive names a crawler that has been retired, or that the
markup Google needs sits past the 2MB it will actually read. We publish those measurements
as datasets rather than as marketing: {F.directives_hosts()} sites' robots.txt files in
<a href="/index/ai-directives/">the directives survey</a>, {F.entity_n()} homepages in
<a href="/learn/sameas-entity-signals/">the entity survey</a>, {F.size_fetched()} in
<a href="/learn/googlebot-2mb-limit/">the page-weight survey</a>. The raw JSON for each is
in <a href="{REPO}">the site's repository</a>, next to the scripts that check every figure
on this site is derived from it rather than typed into a sentence.</p>

<h2>What Docket is not good at</h2>

<p>The honest list, because you will find it out in the first hour anyway:</p>

<ul>
<li><strong>The desktop app is Mac only.</strong> Apple Silicon, macOS 12 or later. There is
no Windows build and no web version, and neither is planned while it is one person. The same
engine ships as a <a href="/download/">Linux x86_64 command line build</a>, without the
desktop app and without <code>--render</code>. This page denied that entirely until
2026-08-10, when the download page had been describing it for weeks.</li>
<li><strong>It is not a rank tracker.</strong> No keyword positions, no search volume, no
backlink index. <a href="/vs/ahrefs-site-audit-alternative/">Ahrefs</a> and Semrush have
spent years and a great deal of money building those, and Docket has no answer to them.</li>
<li><strong>It is not built for enormous sites.</strong>
<a href="/vs/screaming-frog-alternative/">Screaming Frog</a> will crawl 400,000 URLs and let
you sort them; Docket is built to read a site closely, not to survey one at that scale.</li>
<li><strong>The app's source is not public.</strong> The website and its datasets are; the
application is not. If your policy requires reading the code, Docket will not pass it.</li>
<li><strong>It is version {RELEASE}.</strong> There are things it should connect to and does
not yet — Search Console for your own impressions is the biggest.</li>
</ul>

<h2>How you can check any of this</h2>

<p>The download is signed with an Apple Developer ID and notarised, which means the
certificate carries a legal name and Apple has checked it. You do not have to take that on
faith. After downloading the {DMG_SIZE} disk image:</p>

<pre><code>codesign -dv --verbose=4 "/Volumes/{VOLUME}/Docket.app"
spctl -a -t open --context context:primary-signature -v {DMG_NAME}</code></pre>

<p>The first prints the authority chain, ending at Apple's root. The second should say
<code>accepted</code> and <code>source=Notarized Developer ID</code>. Any Mac app worth
installing will survive both; a surprising number will not.</p>

<h2>What to do if a finding is wrong</h2>

<p>Tell us, with the URL. Docket has shipped false positives — the byte-cap check once
reported a major news site's title tag as past Googlebot's cutoff, when what it had found
was an inline SVG icon label reading "Close icon" and the real title was fine. That is
written up in full on <a href="/learn/googlebot-2mb-limit/">the page about the check</a>,
because a tool that hides its mistakes is asking you to trust its output more than its
authors do.</p>

<p><a class="btn" href="/contact/">How to get in touch</a></p>
"""
    return render(
        cat="about", slug="",
        title="About Docket — who builds it and what it cannot do",
        desc=(f"Docket is a Mac SEO and copy audit tool with {N_CHECKS} checks, built "
              f"by one person in the UK and run on your own machine. What it is bad "
              f"at, and how to verify the download."),
        h1="About Docket",
        crumb='<a href="/">Docket</a> / About',
        body=body,
        published="2026-08-07",
        schema_type="AboutPage",
        faq=[
            ("Who makes Docket?",
             "Matt Kerr, one person, in the UK. There is no team and no company office. "
             "The macOS download is signed with an Apple Developer ID and notarised, so "
             "the legal name on the certificate can be checked with codesign before you "
             "install anything."),
            ("Does Docket send my site data anywhere?",
             "No. The crawl runs on your Mac and results are stored in ~/.docket/ as plain "
             "JSON. Two optional connectors do reach outside: the knowledge refresh fetches "
             "one public file from docketseo.app and tells it nothing about what you are "
             "auditing, and PageSpeed Insights — off unless you add your own Google API "
             "key — necessarily sends Google the URL you asked it to measure."),
            ("What can Docket not do?",
             "It is macOS only on Apple Silicon, it does not track keyword rankings or "
             "backlinks, and it is not built for crawling hundreds of thousands of URLs. "
             "The application source is not public, though the website's datasets are."),
        ],
    )


def contact() -> Path:
    body = f"""
<p class="lede">The issue tracker is the way to reach us:
<a href="{ISSUES}">github.com/mattkerr09/docket-site/issues</a>. It is read by the person who
writes the code, it is public so the answer helps whoever asks next, and — unlike the email
address this page used to advertise — messages sent to it actually arrive.</p>

<p>There is no support email. That is a deliberate correction rather than an omission, and
the reason is the more useful half of this page.</p>

<h2>The address that did not work</h2>

<p>Until today the footer of all 25 pages of this site offered
<code>hello@docketseo.app</code>. That address could not receive mail, and never had.</p>

<p>Delivering mail to a domain means looking up its MX record. <code>docketseo.app</code> has
none. <a href="https://www.rfc-editor.org/rfc/rfc5321#section-5.1">RFC 5321 §5.1</a> says a
sender that finds no MX record falls back to the domain's address record — which for this
site is GitHub Pages, whose servers do not answer on port 25. So every message went out,
found nowhere to go, and bounced.</p>

<p>Nobody noticed because a bounce goes to the sender, not to us. This is the exact failure
Docket is built to catch and did not: a channel that is advertised, believed, and dead. It is
now a check we run on our own build, and it will be a check in the app.</p>

<h2>Where to send what</h2>

<div class="wrap-tbl"><table class="cmp"><thead><tr>
<th>If you want to</th><th>Use</th></tr></thead><tbody>
<tr><td>Report a wrong or confusing finding</td>
<td><a href="{ISSUES}/new">Open an issue</a> with the URL you audited and the check ID —
it is printed next to every finding, like <code>index.byte_cap</code></td></tr>
<tr><td>Report a crash or a bug</td>
<td><a href="{ISSUES}/new">Open an issue</a> with your macOS version and what you were
doing</td></tr>
<tr><td>Ask whether Docket does something</td>
<td>Check <a href="/learn/what-docket-checks/">the full check list</a> first, then
<a href="{ISSUES}/new">ask</a></td></tr>
<tr><td>Request a feature</td>
<td><a href="{ISSUES}/new">Open an issue</a>. The known gaps are listed on
<a href="/about/">the about page</a> — no need to file those again</td></tr>
<tr><td>Report a security problem</td>
<td>Please do not open a public issue. Use GitHub's
<a href="{REPO}/security/advisories/new">private advisory form</a></td></tr>
</tbody></table></div>

<h2>What a good bug report contains</h2>

<p>A finding you disagree with is the most valuable thing you can send, and the difference
between a report that can be acted on and one that cannot is usually one line:</p>

<ul>
<li><strong>The URL you audited.</strong> Not a description of it — the address, so the same
crawl can be run.</li>
<li><strong>The check ID.</strong> Every finding carries one. It names the exact function
that produced the output, which turns a search into a lookup.</li>
<li><strong>What you expected instead, and why.</strong> If a specification or a vendor's own
documentation says otherwise, a link to it settles the question immediately. Docket's checks
cite their sources for the same reason.</li>
</ul>

<h2>What to expect back</h2>

<p>One person reads the tracker, so there is no response-time promise here — an invented one
would be the same category of thing as the address that bounced. What is promised is that a
report naming a specific URL and check ID gets a specific answer, and that if Docket is wrong
the correction gets written down where the mistake was made.</p>

<p><a class="btn" href="{ISSUES}/new">Open an issue on GitHub</a></p>
"""
    return render(
        cat="contact", slug="",
        title="Contact Docket — report a bug or a wrong finding",
        desc=("Reach Docket through the GitHub issue tracker: bugs, wrong audit "
              "findings, feature requests — and why the address this site used "
              "to advertise could not receive mail."),
        h1="Contact",
        crumb='<a href="/">Docket</a> / Contact',
        body=body,
        published="2026-08-07",
        schema_type="ContactPage",
        faq=[
            ("How do I report a finding I think is wrong?",
             "Open an issue on GitHub with the URL you audited and the check ID printed "
             "beside the finding. Those two things let the same crawl be reproduced, which "
             "is the difference between a report that can be fixed and one that cannot."),
            ("Is there a support email address?",
             "No. The site previously listed hello@docketseo.app, which could not receive "
             "mail: the domain has no MX record, so senders fell back to the GitHub Pages "
             "address record, where nothing answers on port 25. Every message bounced. The "
             "issue tracker is used instead because messages sent there arrive."),
            ("How do I report a security issue?",
             "Not in a public issue. Use GitHub's private security advisory form on the "
             "repository so the problem can be fixed before it is described publicly."),
        ],
    )


BUILDERS = [about, contact]


def build_all() -> list[Path]:
    return [b() for b in BUILDERS]


if __name__ == "__main__":
    for p in build_all():
        print(p)
