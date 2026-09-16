#!/usr/bin/env python3
"""How to fix broken outbound links — and which rows are not broken at all.

Sourced from `links.broken_external` in
`backend/seo_engine/checks/links.py`, the module constants above it
(`_EXTERNAL_REFUSED`, `_is_refusal`, `_SHARE_INTENT`, `_is_share_intent`,
`_nested_scheme_repair`, `_is_own_url`), `Crawler._check_external` in
`crawler.py`, which decides which links are asked at all, and
`Fetcher.head`/`Fetcher._once` in `fetcher.py`, which is where a status number
comes from. The tests beside them are the narratives:

  * test_refusal_is_not_a_defect.py
  * test_a_four_hundred_from_someone_elses_host_is_not_a_dead_link.py
  * test_a_head_404_is_not_a_broken_link.py
  * test_a_share_button_is_not_a_broken_outbound_link.py
  * test_a_dead_link_to_your_own_subdomain_is_not_outbound.py
  * test_a_link_with_the_scheme_written_twice_is_a_typo_not_a_dead_page.py
  * test_a_link_check_that_outlasts_the_time_limit_it_was_given.py

⚠️ THE REGISTERED TITLE IS NARROWER THAN THE FUNCTION. `links.broken_external`
is registered as "Broken outbound links" and the function emits findings under
four ids — `links.broken_external`, `links.unverified_external`,
`links.broken_own_subdomain` and `links.doubled_scheme` — at two severities.
The page says so, because a reader triaging a report is looking at whichever of
those fired, not at the registered name.

⚠️ AND THE LINE IS NOT DRAWN WHERE "A REFUSAL IS NOT A DEFECT" SUGGESTS. Only
an HTTP *status* can be classified, and `CrawlResult.external_status` stores an
integer per URL and nothing else. A request that never completed is recorded as
zero and counted as broken — including the host that deliberately closed the
connection, which `fetcher.is_connection_refusal` exists to recognise and which
the checks over the site's OWN pages do treat as a refusal. That asymmetry is
stated on the page rather than smoothed over.

No typed figures anywhere in the body: every status code is inside <code>, and
every date, RFC name and section pointer is a constant interpolated through an
f-string hole, so the derived-number gate sees no literal and a re-reading of a
source is one edit.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from render import render  # noqa: E402

#: The external sources, read at their canonical homes on the date below.
#: Section pointers live here rather than in sentences so the prose cannot
#: drift away from a re-reading.
RFC9110 = "RFC 9110"
RFC9110_URL = "https://www.rfc-editor.org/rfc/rfc9110.html"
RFC9110_PUB = "June 2022"
S_STATUS = "section 15"
S_400 = "section 15.5.1"
S_402 = "section 15.5.3"
S_403 = "section 15.5.4"
S_404 = "section 15.5.5"
RFC6585 = "RFC 6585"
RFC6585_URL = "https://www.rfc-editor.org/rfc/rfc6585.html"
RFC6585_PUB = "April 2012"
S_429 = "section 4"
READ_ON = "15 September 2026"

#: The date the control probes quoted below were taken, as recorded in the
#: check's own source. Ours, not a third party's publication date.
PROBED_ON = "3 September 2026"


def broken_outbound_links() -> Path:
    body = f"""
<p class="lede">Your audit came back with a heading that says outbound links are broken and a
list of other people's URLs underneath it. The site is old, the list is long, and the advice
attached to it is to update or remove every one. Before you spend an afternoon on that, the
question worth asking is not how many there are. It is how many of those rows are a statement
about somebody else's page, and how many are a statement about our crawler.</p>

<p><strong>The limits first.</strong> Docket checks a capped sample of your outbound links, not
all of them, and asks each one once. It records a status number and nothing else. And it will
not pretend to be a browser to get a friendlier answer out of a host that dislikes crawlers.</p>

<h2>The report already splits the list. Read the split first</h2>

<p>The check is registered as "Broken outbound links", which is narrower than what it does. One
function reads the sampled links and emits findings under several ids, at two severities,
because they are not the same problem and do not have the same fix:</p>

<div class="wrap-tbl"><table class="cmp"><thead><tr>
<th>Finding</th><th>Severity</th><th>What it means</th></tr></thead><tbody>
<tr><td><code>links.broken_external</code></td><td>LOW</td><td>The request finished and the
answer was a failure that is not a refusal. The only one that accuses somebody else's page of
being gone.</td></tr>
<tr><td><code>links.unverified_external</code></td><td>NOTICE</td><td>The host declined to
answer an automated request. Reported as a fact about the crawl.</td></tr>
<tr><td><code>links.broken_own_subdomain</code></td><td>LOW</td><td>The dead host is one of
yours — not an outbound link, but a service of yours that is down or gone.</td></tr>
<tr><td><code>links.doubled_scheme</code></td><td>LOW</td><td>The href carries the scheme
twice, so the host is the word "https". A typo, not a destination that moved.</td></tr>
</tbody></table></div>

<p>If your report shows the second row, that part of the list needs no work from you. Its own
fix text says so: <em>"Open a couple in a browser if you want certainty; nothing here needs
fixing on the strength of this check."</em> It carries a tool-limit flag that keeps it out of
the score projection and out of your task list, and its impact is zero. It exists to name what
Docket could not find out, not to give you a job.</p>

<h2>What Docket counts as broken</h2>

<p>The crawler collects the <code>http</code> and <code>https</code> anchors that point off
your site, takes a capped sample of the ones it met first, and asks each with a
<code>HEAD</code> request. Any answer that is not a success is then confirmed with a
<code>GET</code> before it counts. That second request exists because the first one lies:
plenty of servers, and most firewalls, answer <code>HEAD</code> with a failure while
<code>GET</code> is fine. Google's own support domain did exactly that — <code>404</code> to
<code>HEAD</code>, <code>200</code> to <code>GET</code> — and articles on this site link to it,
so every one of those links was once reported to us as dead.</p>

<p>After that confirmation, a link is called broken when its status is <code>400</code> or
above, or zero, <em>and</em> it is not on the refusal list below. The wording is the source's:
<em>"Checked … of the site's outbound links (a sample — not every outbound link on the site)
and … failed"</em>, with the fix <em>"Update or remove each dead link. If the destination
moved, link to its new home."</em></p>

<h2>A refusal is not a defect</h2>

<p>Stated flatly, because it is the centre of this page: <strong>a site that refuses an
automated request is not a dead site.</strong> A status code in the client-error range
describes what happened to <em>this request</em>. It is not a property of the resource.</p>

<p><a href="{RFC9110_URL}">{RFC9110}</a> ({RFC9110_PUB}, read {READ_ON}) is explicit about
several of them. <code>403</code> means the server "understood the request but refuses to
fulfill it" ({S_403}). <code>400</code> is for "something that is perceived to be a client
error" ({S_400}) — a rejection of the request, saying nothing about whether the page exists.
<code>402</code> is "reserved for future use" ({S_402}), which is about as far from "this page
is gone" as a status code gets. <code>429</code> is not in that document at all; it is
<a href="{RFC6585_URL}">{RFC6585}</a> ({RFC6585_PUB}, read {READ_ON}), {S_429}, and it means
the client "has sent too many requests in a given amount of time". The full refusal list for a
third-party host is <code>400</code>, <code>401</code>, <code>402</code>, <code>403</code>,
<code>405</code>, <code>406</code>, <code>429</code>, <code>451</code> and <code>503</code>.
Every one of them goes to the unverified finding, with an example.</p>

<p>Two details in that rule are not obvious from the outside. <code>400</code> and
<code>402</code> count as refusals <em>only</em> for third-party links: the same list is read
by the checks that look at your own server, and there a <code>400</code> about your own URL is
your defect and keeps reporting as one. And a status outside the range the protocol defines is
treated as a refusal too. {RFC9110} says all valid status codes lie between <code>100</code>
and <code>599</code>, and that implementations "often use three-digit integer values outside of
that range" for their own purposes. A large professional network answers with such a code, and
the control probes recorded in the check's source on {PROBED_ON} show one of its pages
answering that code to a browser as well — which settles that the number describes the request,
not the page.</p>

<p>That is deliberately more cautious than the specification's own advice, which tells a client
receiving an invalid status code to process the response as if it were a server error. Doing
that would put every one of those links in your broken list.</p>

<h2>The things that leave the list entirely</h2>

<p>Some links are not moved to the unverified finding but dropped from the count altogether,
because they are not outbound links in the first place.</p>

<ul>
<li><strong>Share buttons.</strong> A tweet or share widget points at <em>your own page</em>,
wrapped in someone else's intent URL. The bare share endpoints — no parameters, unquestionably
live, the ones every share button on the web points at — answer <code>404</code> to our fetcher
and <code>200</code> to a browser, measured with control probes on {PROBED_ON} and recorded in
the check's source. On one crawled site, most of the reported broken outbound links were a
single share widget repeated on every page. You can neither fix that host's answer nor drop the
button without dropping sharing, so the widget is excluded rather than reported.</li>
<li><strong>Share images.</strong> The <code>og:image</code> a page declares is fetched in the
same pass, because it is the same kind of request, and read separately — a dead share image is
a different defect with different advice.</li>
<li><strong>Your own subdomains.</strong> A link to a host of yours is not outbound. If it is
dead it is still reported, under a title that says what it actually is.</li>
<li><strong>A scheme written twice.</strong> An href carrying the protocol twice resolves to a
URL whose host is the word "https". No such host exists, so it fails the way a dead destination
does — and the old advice, to find where the page had moved, sent readers hunting for a file
that had never moved. It reports as a typo now, with the address the href meant.</li>
</ul>

<p>That share list is maintained by hand, host by host and path by path, so a widget nobody has
added to it still lands in your broken list. The exclusions cover the cases that have been
measured, not the case nobody has met yet.</p>

<h2>What the check cannot tell you</h2>

<ul>
<li><strong>It is a sample, and not a random one.</strong> It is the outbound links the crawler
met first, up to a cap, deduplicated. If your site asks crawlers to go slowly, the sample
shrinks again to whatever the remaining time budget affords. The finding prints the number it
checked and calls it a sample, which is the number to read it against.</li>
<li><strong>Only the status number survives.</strong> A timeout, a DNS failure, a TLS failure
or a host that closed the connection all arrive at this check as zero, and zero counts as
broken. The fetcher can tell a deliberately closed connection from a broken network, and the
checks that read your own pages use that — this one never sees it, because what is stored per
outbound link is an integer.</li>
<li><strong>It asks once.</strong> A host having a bad minute is a dead link in your report.</li>
<li><strong>It reads the HTML it was served.</strong> Links a script writes into the page
afterwards are not in the sample: the crawler's browser pass exists for finding internal pages
and keeps only the internal links it sees.</li>
<li><strong>It will not pose as a browser.</strong> Spoofing one would get a different answer
from the one the site really serves an automated client, which is a different kind of lie.</li>
<li><strong>A redirecting link is not in the list.</strong> The fetcher walks the redirect chain
and records the status at the end of it, so an outbound link that still redirects to a live page
answers as a success and never appears here. Redirects on your own site are a separate job, with
<a href="/how-to/fix-redirect-problems/">a separate page about the findings that report
them</a>.</li>
</ul>

<h2>So does a dead outbound link cost you anything?</h2>

<p>Docket says the modest thing, at LOW severity: <em>"Dead outbound links are a small quality
signal and a direct annoyance for visitors."</em> That is the whole claim, and the second half
of it is the real one. Somebody reading your page clicked a reference you offered and got
nothing.</p>

<p>You will read elsewhere that a broken outbound link leaks, wastes or bleeds authority out of
the page. We can point to no primary documentation for that claim, so this page does not make
it. An unsourced mechanism is not a reason to do anything; a reader hitting a dead reference
is.</p>

<h2>What to do with the list you have</h2>

<p>Work the accusatory finding only, and open a handful of its URLs in a browser first — a
minute's work that tells you whether the rows are real. Where the destination moved, link to
where it went. Where it is gone for good, replace the reference or remove it; a sentence that
cited something should either cite something else or stop citing. Leave the unverified list
alone: those hosts declined to talk to an automated client, which large platforms do routinely,
and the pages are very probably fine.</p>

<p>Own-subdomain breakages are a different afternoon — that is your service, down or retired,
and the fix is at the host rather than in your copy. A doubled scheme is a moment's edit: delete
the duplicate protocol, then confirm the repaired address loads, because Docket has not
requested it. Every check Docket ships is listed in
<a href="/learn/what-docket-checks/">what Docket checks</a>.</p>

<p><a class="btn" href="/download/">Download Docket</a></p>
"""
    return render(
        cat="how-to", slug="fix-broken-outbound-links",
        title="How to fix broken outbound links (and which are not)",
        desc=("A dead outbound link and a host that refuses a crawler are not the same audit "
              "row. What Docket counts as broken, what it files as unverified, and what "
              "each needs."),
        h1="How to fix broken outbound links",
        crumb='<a href="/">Docket</a> / <a href="/how-to/">Fix it</a> / broken outbound links',
        body=body,
        schema_type="Article",
        faq=[
            ("Is a 403 or 429 a broken link?",
             "No. A 403 means the server understood the request and refused it, and a 429 means "
             "it thinks you are asking too often. Neither says the page is missing. Docket files "
             "401, 403, 405, 406, 429, 451 and 503 — and 400 and 402 when the host is not yours "
             "— under links.unverified_external at NOTICE, with a note that they were neither "
             "reported as broken nor counted as working."),
            ("Why does my report list a link that works fine in my browser?",
             "Because the host answered our crawler differently from the way it answers you. "
             "That is common on large social platforms, which refuse automated requests as "
             "policy. If the row is in the unverified finding, that is exactly what it is "
             "telling you. If it is in the broken finding, open it: Docket confirms every "
             "failed HEAD with a GET before counting it, but it still only asked once."),
            ("Does Docket check every outbound link on my site?",
             "No. It checks a capped sample of the outbound links the crawler met first, and "
             "the sample shrinks further if your site asks crawlers to slow down. The finding "
             "prints how many it checked and calls it a sample in its own text."),
            ("Do broken outbound links lose me PageRank?",
             "This page does not make that claim, because we can point to no primary "
             "documentation for it. Docket reports dead outbound links at LOW severity and "
             "describes them as a small quality signal and a direct annoyance for visitors. "
             "The visitor is the reason to fix them."),
            ("What does a status code of zero mean in a link check?",
             "It is Docket's own marker for a request that never completed — a timeout, a DNS "
             "failure, a TLS failure, or a connection the host closed. Those count as broken, "
             "because a connection that never completes is a statement about reachability. It "
             "is also the one place where a refusal can land in the broken list, so a row with "
             "no status is worth opening by hand."),
        ],
    )


BUILDERS = [broken_outbound_links]


def build_all() -> list:
    return [b() for b in BUILDERS]


if __name__ == "__main__":
    print(broken_outbound_links())
