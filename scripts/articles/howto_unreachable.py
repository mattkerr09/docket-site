"""'Could not be reached' is the absence of a diagnosis, not a diagnosis.

Promised on the how-to hub. Sourced from `indexability.py`, whose registered
checks `index.broken` and `index.sitemap` carry four recorded cases in which
entirely different causes were reported as one unreachable page, under fix text
sending the reader to DNS and TLS:

  * a cathedral whose pages answered 200 in about sixteen seconds — slow, not
    down, and its slowness was already reported elsewhere in the same run;
  * a podcast where two findings in ONE report described the same address as
    both "did not answer in time" and "broken in your sitemap";
  * a restaurant site where a whole paragraph of marketing copy had been pasted
    into a link field, so no request was ever made;
  * a documentation wiki where connection resets began only after hundreds of
    pages had been read successfully — rate limiting, not an outage.

⚠️ NO SITE IS NAMED — third-party gate.

⚠️ DO NOT RE-EXPLAIN RATE LIMITING. `/how-to/tell-a-rate-limit-from-a-block/`
owns that; the fourth case here is about the EVIDENCE already sitting in the
crawl (the successes), not about throttles. Cross-link instead.

⚠️ `index.unreachable`, `index.timed_out`, `index.malformed_link`,
`index.connection_refused` and `index.sitemap_dead_urls` are FINDING ids. The
registered checks are `index.broken` and `index.sitemap`. The page says so.

Numerals: HTTP status codes only; quantities spelled as words.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from render import render  # noqa: E402


def unreachable() -> Path:
    body = """
<p class="lede">An audit finishes and tells you some of your pages could not be reached at all —
connection failures, DNS errors, certificate problems — and advises you to check DNS, TLS and
server availability. It is the most expensive sentence a report can contain, because it names
three things that are almost never the cause, and somebody spends a day in a control panel where
nothing is wrong.</p>

<p><strong>"Could not be reached" is not a diagnosis. It is the absence of one.</strong> It means
the crawler has no status code to show you, and the reasons for that are wildly different from
each other. Here are four, each recorded from a real run.</p>

<h2>Slow, not down</h2>

<p>A cathedral's site had a long list of URLs reported as unreachable. Every single one carried
the timeout string — not one was a DNS failure or a refused connection. Two were fetched by hand
afterwards and both answered HTTP 200, in about sixteen seconds.</p>

<p>The site was not down. It was slow, and its slowness was <em>already reported two findings
away in the same report</em> as a very high median time to first byte. Everything needed to
explain the unreachable list was in the reader's hands, under a different heading, and the fix
text sent them hunting an outage instead.</p>

<p>The principle that fixes this is worth carrying to any tool: <strong>a timeout is a fact about
the crawler and its timeout setting. A refusal is a fact about this crawler. Neither is a
statement about whether your page exists.</strong></p>

<h2>The report that said both</h2>

<p>On a podcast's site, one report contained two findings naming the same address: one saying the
URL did not answer before the crawl gave up, the other saying a sitemap URL was broken. Fetched
by hand three times, it answered HTTP 200 with a large page twice, in roughly half a minute, and
timed out once.</p>

<p>The second finding was the false one, and the reason is exact: <strong>"your sitemap lists
URLs that return errors" is a claim your site never made, because it never got the chance to
reply.</strong> One branch was reading a status of zero and treating it as an error status. Zero
is not a status; it is the crawler's note to itself that nothing came back.</p>

<p>The repair was to give both checks one shared definition of what a timeout is, so they can
never drift apart again. A report that contradicts itself costs more than either finding is
worth — you now have to work out which half to believe, and most people believe the scarier
one.</p>

<h2>A sentence where a URL should be</h2>

<p>A restaurant site had one unreachable URL whose address was an entire paragraph of marketing
copy about taking bookings for private events. Somebody had pasted prose into the link field in
their editor. No request was ever made — the address could not be parsed — so there was nothing
to say about DNS, TLS or availability, and the report printed several hundred characters of
someone's copy where a URL belongs.</p>

<p>This is a real defect and worth reporting. It is just an entirely different one: a link that
can never resolve, fixable in the page editor in a minute.</p>

<p>There is a trap in the repair, and it generalises. Once the spaces in that paragraph are
encoded it becomes a valid request, and it comes back 404 — so a naive fix would re-label it a
broken internal link, which is <em>true</em>, and which sends the reader looking for a missing
page instead of at the link field where their marketing copy is. <strong>Downgrading a false
claim must not become dropping a true one.</strong></p>

<h2>The host that answered hundreds of times</h2>

<p>A documentation wiki's crawl ended with a long list of unreachable URLs, connection resets,
and the same advice about DNS and TLS. The site was up throughout — a control page answered 200
before and after — and the resets began only after several hundred pages had been read
successfully.</p>

<p><strong>A host that answered hundreds of times does not have a DNS problem, and the proof was
already in the crawl.</strong> If it resolved and its certificate served those requests, the only
thing left a reset can mean is that it stopped wanting to talk to this crawler. That is a
different finding with a different severity — nothing is wrong with the site, and the pages are
missing from this crawl rather than from anybody's index.</p>

<p>For the general version of that — an audit measuring its own footprint — see
<a href="/how-to/tell-a-rate-limit-from-a-block/">a rate limit is not a block &rarr;</a>.</p>

<h2>Telling them apart on your own report</h2>

<p>Four questions, in this order, and you will usually know within a minute:</p>

<ul>
<li><strong>Did anything on that host answer?</strong> If other pages on the same domain came
back 200, DNS and TLS are fine by definition. Stop considering them.</li>
<li><strong>Is the "URL" actually a URL?</strong> Spaces, sentences and punctuation in the
address mean the request was never made. Look at the page that contains the link.</li>
<li><strong>What does the error say?</strong> A timeout, a reset and a name-resolution failure
are three different sentences, and a good report quotes them. If yours does not, that is worth
knowing about your tool.</li>
<li><strong>Does it answer by hand, and how long does it take?</strong> This settles nearly all
of them. A page that answers in fifteen seconds is a performance problem wearing an availability
problem's clothes.</li>
</ul>

<h2>When this does not matter</h2>

<p>A genuinely unreachable page is serious and this is not an argument for ignoring the finding.
Two cases where it is exactly what it says:</p>

<ul>
<li><strong>A host that answered nothing at all.</strong> No successful fetch anywhere on that
domain, with a name-resolution error, is a real availability problem.</li>
<li><strong>A subdomain or external host that has gone away.</strong> Common on old sites, and
the links to it are worth removing whatever the cause.</li>
</ul>

<p>What does not deserve your time is the same finding on a domain that served the rest of the
crawl.</p>

<h2>The fixes that make it worse</h2>

<ul>
<li><strong>Changing DNS records or reissuing a certificate</strong> because a report said to.
Both are risky operations against a system that is working.</li>
<li><strong>Deleting or redirecting pages you now believe are dead.</strong> If they were slow
rather than gone, you have just removed working pages from your site on the strength of a crawler
setting.</li>
<li><strong>Raising your crawl rate to "get past" the resets.</strong> That is the one action
guaranteed to produce more of them.</li>
</ul>

<h2>How to make the finding disappear without changing anything</h2>

<p>Raise the crawler's timeout, or crawl more slowly. On a slow site the first makes the
unreachable list shrink; on a rate-limited one the second makes it vanish. Nothing about the site
changed.</p>

<p>Which is the tell. <strong>If a setting on your side of the connection changes the finding,
the finding was partly about your side of the connection</strong> — and the honest report is one
that says which part it could not see rather than guessing at a cause.</p>

<h2>Where this sits in an audit</h2>

<p>The registered checks are <code>index.broken</code>, which covers pages returning errors, and
<code>index.sitemap</code>. The identifiers you will see on the findings themselves are different
— the unreachable, timed-out, malformed-link and connection-refused findings all come out of
<code>index.broken</code> — which matters when you go looking for one by name and find nothing.
A finding identifier is not a check identifier.</p>

<p>For the outbound equivalent, where somebody else's server is the one refusing, see
<a href="/how-to/fix-broken-outbound-links/">how to fix broken outbound links (and which are
not) &rarr;</a>.</p>
"""
    return render(
        cat="how-to", slug="pages-an-audit-could-not-reach",
        title="'Could not be reached' is not a diagnosis",
        desc=("An audit reports one thing for four causes, then sends you to DNS. How to tell "
              "slow from down on your own site in a minute."),
        h1="'Could not be reached' is not a diagnosis",
        crumb='<a href="/">Docket</a> / <a href="/how-to/">Fix it</a> / Unreachable pages',
        body=body,
        faq=[
            ("What does 'could not be reached' mean in an audit?",
             "Only that the crawler has no status code to show you. A timeout, a connection "
             "reset, an unparseable address and a real outage all produce it, and they need "
             "completely different fixes."),
            ("My audit says check DNS and TLS. Should I?",
             "Not if any other page on the same domain answered. If the host resolved and "
             "served requests during the same crawl, DNS and the certificate are working and "
             "the cause is elsewhere."),
            ("Is a slow page reported as a broken one?",
             "It can be. A page answering in fifteen seconds exceeds many crawlers' timeouts, "
             "and a timeout is a fact about the crawler's settings rather than about whether "
             "your page exists."),
            ("Why did one report call the same URL both timed out and broken?",
             "Because two checks disagreed about what a status of zero meant. Zero is not an "
             "HTTP status; it is the crawler's note that nothing came back, so nothing can be "
             "concluded about what the server would have said."),
            ("An unreachable URL in my report is a sentence, not an address. Why?",
             "Somebody pasted prose into a link field. The request was never made, so no "
             "infrastructure advice applies — open the page containing the link and replace the "
             "destination."),
        ],
    )


if __name__ == "__main__":
    print(unreachable())
