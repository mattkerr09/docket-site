#!/usr/bin/env python3
"""How to fix redirect problems — the three findings `index.redirects` emits.

Sourced from `index.redirects` in
`backend/seo_engine/checks/indexability.py`, the `_redirect_example` helper
above it, `fetcher.Fetcher.get`, which is where the redirect chain is actually
built, and the four tests beside them that record what went wrong:

  * test_a_redirect_chain_names_the_url_you_have_to_change.py
  * test_a_redirect_that_leaves_the_site_does_not_come_back.py
  * test_a_redirect_is_not_a_second_copy_of_the_page.py
  * test_one_redirect_closes_sixty_nine_duplicate_groups.py

⚠️ THE REGISTERED TITLE IS WIDER THAN THE CODE. `index.redirects` is registered
as "Redirect problems" and emits three findings under three other check ids —
`index.redirect_loop`, `index.redirect_chain`, `index.internal_link_to_redirect`
— and none of them is about a status code. `Response.chain` is a list of URLs,
so the engine does not retain per-hop statuses at all and cannot tell a 301 from
a 302 in a chain. Nothing here may say it can. The page says so instead.

No typed figures: the status codes 301/302 are constants of the protocol and are
declared in verify_numbers.ALLOWED; the specification pointers and the date the
sources were read are interpolated from the constants below, and the config
snippets are written in their brace-free forms so nothing in the rendered page
can look like an unrendered placeholder.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from render import render  # noqa: E402

#: The two external sources, read at their own canonical homes on the date
#: below. Section pointers live here rather than in sentences so a re-reading is
#: one edit and the prose cannot drift away from it.
RFC_URL = "https://www.rfc-editor.org/rfc/rfc9110.html"
RFC = "RFC 9110"
S_REDIRECTION = "section 15.4"
S_301 = "section 15.4.2"
S_302 = "section 15.4.3"
GOOGLE_URL = ("https://developers.google.com/search/docs/"
              "crawling-indexing/301-redirects")
GOOGLE = "Google's redirect documentation"
READ_ON = "15 September 2026"


def redirect_problems() -> Path:
    body = f"""
<p class="lede">Your audit came back with a section headed "Redirect problems" and a list of
URLs, and you moved a site or renamed a directory recently, so of course there are redirects.
The useful question is not how many. It is which of these shapes actually costs you something,
and which is a redirect doing exactly the job you set it.</p>

<p>Docket's <code>index.redirects</code> check reports three of them, and they are three
separate findings at three different severities because they are three different jobs:</p>

<ul>
<li><strong>A redirect loop</strong> — <code>index.redirect_loop</code>, at CRITICAL. Nobody
reaches the content. Ever.</li>
<li><strong>A chain</strong> — <code>index.redirect_chain</code>, at MEDIUM. A URL that
redirects more than once before it resolves.</li>
<li><strong>An internal link pointing at a redirect</strong> —
<code>index.internal_link_to_redirect</code>, at LOW. Your own templates linking to the old
URL.</li>
</ul>

<p>That ordering is the answer. If you only have time for one, it is the first, and the third
is housekeeping you can schedule.</p>

<h2>What this cannot tell you</h2>

<p>Said first, because it changes how much weight the list deserves.</p>

<p><strong>Docket does not read your server configuration.</strong> It has never seen your
nginx file, your <code>.htaccess</code>, your CDN rules or your CMS redirect table. Everything
it reports is a redirect its own crawler walked while fetching the pages it crawled, starting
from your homepage and following links. A redirect rule that exists but that nothing on the
site links to is invisible to it. So is one on a page the crawl did not reach.</p>

<p><strong>And it does not record the status code of each hop.</strong> This is the one that
matters most, because it is the opposite of what the phrase "redirect problems" suggests. The
fetcher follows redirects by hand so the intermediate URLs survive, and its own comment says
why: "the hops are the finding: a 302 where a 301 belongs, or a 4-hop chain burning crawl
budget, are both invisible if you only see the destination". What it keeps is
<code>chain</code>, a list of URLs. The statuses are not in it. So no finding under this check
is about a temporary redirect used where a permanent one was meant — Docket cannot see the
difference, and a page that told you otherwise would be describing a check that does not
exist.</p>

<p>It follows that Docket also cannot tell a deliberate temporary redirect from a mistaken
one. Nothing can, from the outside: the status code is a declaration of intent, and only you
know whether the intent was real. Checking that is a job for the commands further down this
page, not for a crawler.</p>

<p>One more, because it changes what a finding means rather than merely limiting it. When a
redirect leaves your site, the crawler keeps the URL you own and discards the title and body at
the far end — another site's words must not be attributed to yours. Those URLs still appear in
the redirect findings, as your signposts pointing off your property, and no claim is made about
what they point at.</p>

<h2>The three findings, and what fires each</h2>

<h3>A loop: nothing gets through</h3>

<p>The fetcher walks the chain itself, and when the next hop is a URL already in the chain it
stops and records a redirect loop. The check picks those up and reports at CRITICAL, with a
sentence that is not hedged: "These URLs redirect back to themselves, so no crawler or visitor
ever reaches content." Its fix text is <em>"Trace the redirect rules for these paths and break
the cycle."</em></p>

<p>There is no threshold on this one. One is enough, because one is a page that cannot be
reached by anybody, and a loop is almost always two rules written at different times that each
look correct on their own — a trailing-slash rule and a lowercase rule, a CDN redirect and an
application redirect, an old rule and its replacement.</p>

<p><a href="{RFC_URL}#section-15.4">{RFC} {S_REDIRECTION}</a> puts the obligation on the
client rather than the server: "A client SHOULD detect and intervene in cyclical redirections
(i.e., 'infinite' redirection loops)." That is why a loop is not a crash. Every client
eventually gives up, quietly, and what the visitor sees is a browser that stops with an error
page nobody reports to you.</p>

<h3>A chain: more than one hop before it resolves</h3>

<p>The rule is exactly as narrow as it sounds — a page whose recorded chain has two or more
hops in it. One redirect is not a chain and is not reported here. The finding is MEDIUM, it
prints one chain written out with arrows as its example, and its fix text is <em>"Point the
first URL in each chain straight at the final destination, in one hop."</em></p>

<p>Two bugs in that sentence are worth repeating, because they are the reason to trust the
current version. The finding used to list the <em>last</em> URL of each chain — the
destination, which redirects nowhere and needs no change — while its own fix asked you to
change the first. And the example was built by slicing the first few hops, which silently
dropped the destination once a chain got long enough. Both were measured on a real site, both
are fixed, and both have tests named after them.</p>

<p>Chains come from history rather than carelessness: each rule was right when it was written.
The site moved to HTTPS, then to a new URL structure, then a section was renamed, and each
change added a hop to redirects that already existed. Collapsing them is the least glamorous
and most reliable thing on this page — take the first URL, point it at the last, delete the
middle.</p>

<h3>An internal link pointing at a redirect</h3>

<p>The narrowest of the three, and the one whose definition is worth reading before you act on
it. It fires on a URL whose chain is exactly one hop long <strong>and</strong> which the crawl
saw an internal link pointing at. Both halves are required. A single-hop redirect that nothing
on your site links to is reported by none of these three findings, which is correct: it is a
redirect working as intended, catching an old inbound link, and there is nothing to fix.</p>

<p>Reported at LOW, with the fix <em>"Update these internal links to their destination
URL."</em> The URLs it lists are the redirecting ones, not the destinations — the same
distinction the chain finding got wrong — because the redirecting URL is the string you have
to find in your templates.</p>

<h2>The claim this page will not make</h2>

<p>You will have read that a permanent redirect passes some specific percentage of "link
equity". No figure of that kind appears here. {GOOGLE} does not state one, and a number
repeated without a source is not evidence that it is true.</p>

<p>Being precise about this cuts our own side too. The chain finding's detail text says an
extra hop "dilutes the signal passed through the redirect" — a claim Docket's own source does
not carry a citation for, and you should weigh it accordingly. The part of that sentence that
survives scrutiny is the other half: each extra hop is another round trip before any content
arrives, and that is measurable on your own connection.</p>

<p>What {GOOGLE} does say, read on {READ_ON}, is about signals rather than percentages:
for a permanent redirect, "Googlebot follows the redirect, and the indexing pipeline uses the
redirect as a signal that the redirect target should be canonical". For a temporary one,
"Googlebot follows the redirect, but the indexing pipeline doesn't use the redirect as a signal
that the redirect target should be canonical."</p>

<p>That is the real cost of the wrong status code, and it is a cost in canonicalisation rather
than in leaked equity. A redirect is one of the signals that decides which URL gets indexed;
<a href="/learn/canonical-tags/">what a canonical tag actually does</a> covers the other
declaration you can make about the same question, and the two can disagree.</p>

<h2>Checking the status codes yourself</h2>

<p>Since Docket does not keep them, get them directly. This prints every hop's status line and
every <code>Location</code> header, in order:</p>

<pre><code>curl -sIL https://example.com/old-url | grep -i '^HTTP/\\|^location:'</code></pre>

<p>Read it as pairs. A permanent move should show <code>301</code> and the new URL, once.
Two or more pairs before the final <code>200</code> is the chain. The same URL appearing twice
is the loop. A <code>302</code> where you meant a permanent move is the mistake nothing in
your audit will catch for you.</p>

<p>Per <a href="{RFC_URL}#section-15.4.2">{RFC} {S_301}</a>, <code>301</code> means "the target
resource has been assigned a new permanent URI and any future references to this resource ought
to use one of the enclosed URIs"; per <a href="{RFC_URL}#section-15.4.3">{S_302}</a>,
<code>302</code> means only that "the target resource resides temporarily under a different
URI". Both read at rfc-editor.org on {READ_ON}. The default in a lot of framework helpers and
control panels is the temporary one, which is how sites end up declaring a permanent move in
words and a temporary one in the header.</p>

<p>Fixing a chain rarely needs a new rule, only an edited one. On nginx, a permanent move
written as a single directive rather than a block:</p>

<pre><code>rewrite ^/old-url$ /new-url permanent;</code></pre>

<p>On Apache, in the virtual host or an <code>.htaccess</code> file:</p>

<pre><code>Redirect 301 /old-url /new-url</code></pre>

<p>Point the first URL at the final destination in both cases. Leave the intermediate rules in
place if other inbound links still use them; what you are removing is the hop, not the
history.</p>

<h2>Three neighbouring checks that are not this one</h2>

<p>Docket reports redirects in more than one place, deliberately, and confusing them wastes
your time:</p>

<ul>
<li><strong>Client-side redirects</strong> — <code>index.meta_refresh</code>, at NOTICE. A page
that answers <code>200</code> with a normal body and then moves the visitor with
<code>&lt;meta http-equiv="refresh"&gt;</code>. It has no chain and no redirect status, so
everything on this page is blind to it; that is why it needed a check of its own. It is a
notice rather than an error because static hosting frequently cannot issue a server-side
redirect at all, and scolding somebody for using the only tool their host gives them is not
advice.</li>
<li><strong>Redirect latency</strong> — <code>perf.redirect_volume</code>, in the performance
lane. It fires on the share of crawled URLs that went through any redirect, one hop included,
which is a question about cost rather than correctness.</li>
<li><strong>Canonical conflicts</strong> — the <code>index.canonical</code> check, whose
findings include <code>index.canonical_conflict</code>. A redirect and a canonical tag are two
ways of naming the real URL, and they can contradict each other.</li>
</ul>

<h2>The redirect that closes sixty-nine findings</h2>

<p>The most expensive redirect defect Docket has measured was a missing one. A university
department's audit carried a HIGH finding about pages with identical content across dozens of
groups, and the remedy attached to it asked for a canonical decision per group. The crawl had
already measured the cause: the site answered on both <code>http://</code> and
<code>https://</code>, with the same paths under both schemes, and the report said so
separately as <code>security.no_http_redirect</code>. One server rule closed the lot. The
reader had been handed sixty-nine decisions for a one-line fix, and the check that owned the
remedy now reads the flag the crawl had recorded.</p>

<p>If your audit shows duplicate content and no HTTPS redirect, do the redirect first and
re-run. <a href="/how-to/redirect-http-to-https/">How to redirect http:// to https://</a>
covers the rule by host, including the certificate state that blocks the setting on GitHub
Pages — which we found because Docket reported the same fault on this site.</p>

<h2>What to do with the list you have</h2>

<p>Loops first. Chains next, collapsed to one hop each, starting with the URLs you actually
earned links to. Internal links pointing at redirects last, as a template edit rather than a
URL-by-URL job. Then check the status codes by hand on the redirects that matter, because that
is the one part of this no crawl report will do for you.</p>

<p><a class="btn" href="/download/">Download Docket</a></p>
"""
    return render(
        cat="how-to", slug="fix-redirect-problems",
        title="How to fix redirect problems: loops, chains, links",
        desc=("Redirect loops, chains and internal links pointing at redirects — what Docket's "
              "index.redirects check reports, what it cannot see, and which ones cost you."),
        h1="How to fix redirect problems",
        crumb='<a href="/">Docket</a> / <a href="/how-to/">Fix it</a> / redirect problems',
        body=body,
        faq=[
            ("Are all redirects bad for SEO?",
             "No. A redirect that sends one old URL to one new URL in a single hop is the "
             "correct way to move a page, and Docket does not report it at all unless your own "
             "internal links still point at the old URL. What gets reported is a loop, a chain "
             "of two or more hops, and a template still linking to the redirecting URL."),
            ("Does Docket tell me which redirects are 301 and which are 302?",
             "No. The crawler keeps the list of URLs it walked, not the status of each hop, so "
             "no finding under this check distinguishes a permanent redirect from a temporary "
             "one. Check that yourself with curl -sIL against the URL and read the status lines "
             "it prints."),
            ("How much link equity does a redirect lose?",
             "This page does not give a figure, because Google's redirect documentation does "
             "not publish one and the percentages you see quoted elsewhere have no source. "
             "What Google's documentation does say is that a permanent redirect is used as a "
             "signal that the target should be canonical, and a temporary one is not."),
            ("Why does my audit list a redirect I do not have a rule for?",
             "Docket reports the redirects its crawler actually walked from the pages it "
             "crawled, so a hop can come from your CDN, your host's trailing-slash handling, or "
             "a platform-level rule rather than from your own configuration file. It never "
             "reads that configuration, so the crawl is the evidence, not the rule list."),
            ("Does a redirect chain get shortened automatically by Google?",
             "Googlebot follows redirects, but each hop is still a request a visitor's browser "
             "makes and your own links still point at the first URL. Collapsing the chain in "
             "your configuration is a one-line edit; leaving it means every visitor pays for "
             "the history of your URL structure."),
        ],
    )


BUILDERS = [redirect_problems]


def build_all() -> list:
    return [b() for b in BUILDERS]


if __name__ == "__main__":
    print(redirect_problems())
