"""Which host is that finding about?

Promised on the how-to hub. Sourced from the registered check `security.https`
in `backend/seo_engine/checks/security.py`, whose docstrings record three cases
with one shape: the finding was right, named no host, and the reader disproved
it by checking a different one.

  * a certificate expiring soon on a host the site redirects to, reported with
    no host named — checking the typed address shows a much longer life, so the
    finding reads as plainly false. The author records making that exact
    mistake with that exact evidence before checking the redirect target.
  * an http:// address that answers without redirecting on the `www.` spelling
    while the apex redirects correctly — reported at HIGH with no host and an
    empty evidence block.
  * an http:// address returning 404, described as "still reachable … two
    indexable copies of every page", which is true of neither.

⚠️ NO SITE IS NAMED — third-party gate. The streaming service and the retailer
are described by what they are.

⚠️ THE DESIGN NOTE MUST SURVIVE: the first repair added a sentence naming the
typed address, and that branch could never run because the crawl's origin is
already the redirect target. A sentence that cannot fire is worse than none.

⚠️ MUST NOT CONTRADICT /how-to/redirect-http-to-https/, which owns the fix and
says Docket probes the plain-HTTP address directly. This page is about reading
the finding; it cross-links there for the repair.

Numerals: 200 and 404 only; certificate lifetimes are spelled in words.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from render import render  # noqa: E402


def which_host() -> Path:
    body = """
<p class="lede">An audit tells you your certificate expires in a fortnight. You check, and it has
months left. You conclude the tool is broken and stop reading — which is the worst outcome
available, because the finding was right about a host you did not check.</p>

<p>Almost every security finding is about <em>one address</em>, and there are usually several
that all look like your site: the bare domain, the <code>www</code> spelling, whatever they
redirect to. A finding that does not say which one it measured invites you to disprove it against
the wrong one.</p>

<h2>The certificate on the host you redirect to</h2>

<p>An audit of a streaming service was started at its <code>www</code> address. Every page
redirected to a different host, and it was that host's certificate that was close to expiry. The
finding said the certificate expires soon and named nothing. Checking the address that had been
typed shows a comfortable margin, so the sentence reads as plainly false.</p>

<p>The person who wrote the check records making exactly that mistake, with exactly that evidence,
before thinking to follow the redirect. That is worth saying because it is the ordinary response:
<strong>a claim you can falsify in ten seconds is one you stop investigating.</strong></p>

<p>Naming the host is the entire fix, and it is all that is available — once a crawl has followed
a redirect, the address you typed is gone, and the tool genuinely cannot tell you what you asked
for. Which produced a second lesson in the same commit: the first repair added a sentence saying
"you asked for this address, which redirects here", and that branch could never run. <strong>A
sentence that cannot fire is worse than no sentence, because it looks like coverage.</strong></p>

<h2>The spelling that redirects and the spelling that does not</h2>

<p>The same shape, one layer down. An audit of a bakery chain began at the <code>www</code>
spelling, where the plain-http address answered without redirecting to https. True, and reported
at high severity — with no host named and no evidence attached.</p>

<p>The apex redirects correctly. So the owner reads the finding, types the bare domain, watches it
redirect to https exactly as it should, and concludes the tool is wrong about something it is
right about.</p>

<p><strong>The <code>www</code> spelling and the bare domain are different hosts.</strong> They can
have different DNS records, different certificates, different redirect rules and different
answers on port eighty. An audit that probed one has said nothing whatever about the other — and
an honest one says so rather than implying it covered both.</p>

<h2>Reachable, or answering, or refusing</h2>

<p>The third case is about the detail rather than the host, and it is the most instructive.</p>

<p>On a large retail site the plain-http address returned 404 — to the crawler and to a browser
alike. The report said the insecure version was still reachable and that there were two indexable
copies of every page. <strong>Neither is true of a 404.</strong> Nothing is reachable and nothing
is indexable. The real harm is smaller and completely different: somebody who types the bare
domain gets an error page instead of the site.</p>

<p>The title was right and the detail was wrong, and that combination is more dangerous than being
wrong outright — because a reader who checks the detail finds it false and stops trusting the
findings that are true.</p>

<p>So "http is still reachable" is really three situations:</p>

<ul>
<li><strong>It answers 200 and serves the site.</strong> This is the real problem: an insecure
copy of every page, indexable, splitting signals with the secure one.</li>
<li><strong>It answers an error.</strong> Nothing is duplicated and nothing is indexed. The cost
is visitors who type the domain without a scheme and land on an error.</li>
<li><strong>It refuses, times out, or errors on the server side.</strong> The tool has learned
nothing. A server failing on its plain-http listener has not told you whether a working listener
would redirect, and a finding that draws a conclusion here is inventing one.</li>
</ul>

<h2>Reading a security finding on your own report</h2>

<ul>
<li><strong>Find the host before you check the claim.</strong> If the report does not name one,
that is the first thing to be sceptical about — not the claim itself.</li>
<li><strong>Check where your audit started and where it landed.</strong> If the crawl followed a
redirect, everything after that is about the destination.</li>
<li><strong>Test both spellings by hand</strong> — the bare domain and the <code>www</code> one,
each over plain http. They are separate configurations and it takes a minute.</li>
<li><strong>Read the status, not the summary.</strong> A 200 and a 404 on the same address call
for different work and appear under the same heading in most tools.</li>
</ul>

<h2>When this matters, and when it does not</h2>

<p>Keep the severity in view. An insecure copy serving 200 is a genuine and common problem, and
worth fixing the day you find it. An http address that errors is a courtesy fix — real, small, and
not urgent. And a certificate close to expiry on any host your traffic touches is urgent wherever
it lives, which is exactly why naming the host matters more than the number of days.</p>

<h2>The fixes that make it worse</h2>

<ul>
<li><strong>Adding a redirect rule for the spelling that already worked.</strong> The finding was
about the other one, and now you have two rules to maintain and one of them does nothing.</li>
<li><strong>Dismissing a finding you disproved on the wrong host.</strong> The most expensive
response on this page, and the one every unnamed finding invites.</li>
<li><strong>Renewing the certificate you checked.</strong> It was not the one expiring.</li>
</ul>

<h2>How to make this finding disappear without fixing anything</h2>

<p>Turn off the plain-http listener entirely. Nothing answers, so nothing can be reported — and
anybody who types your domain without a scheme now gets a connection error rather than your site.
The finding is quieter and the visitor is worse off, which is a fair summary of what happens when
you optimise for a report instead of for a person.</p>

<h2>Where this sits in an audit</h2>

<p>The registered check is <code>security.https</code>, which covers the plain-http address and the
certificate. For the repair itself — the redirect, where to configure it by host, and why HSTS is
a separate step — see
<a href="/how-to/redirect-http-to-https/">how to redirect http to https &rarr;</a>. For the
broader question of which spelling of your domain is canonical, see
<a href="/learn/www-vs-non-www/">www versus non-www, counted rather than asserted &rarr;</a>.</p>
"""
    return render(
        cat="how-to", slug="findings-that-name-no-host",
        title="Which host is that finding about?",
        desc=("A security finding that names no host gets disproved against the wrong one. "
              "Three cases where an audit was right about a site and read as wrong."),
        h1="Which host is that finding about?",
        crumb='<a href="/">Docket</a> / <a href="/how-to/">Fix it</a> / Which host',
        body=body,
        faq=[
            ("My audit says my certificate expires soon but it does not. Why?",
             "Probably because the crawl followed a redirect and the certificate belongs to the "
             "destination host. Check the address your pages actually resolve to rather than the "
             "one you typed."),
            ("Are www and the bare domain the same host?",
             "No. They can have different DNS records, certificates, redirect rules and answers "
             "over plain http, so a probe of one says nothing about the other."),
            ("Is http returning 404 the same as an insecure copy of my site?",
             "No, and the difference matters. A 404 means nothing is reachable and nothing is "
             "indexable; the only cost is that somebody typing your domain without a scheme sees "
             "an error page."),
            ("What should a finding say when the http address refuses or times out?",
             "That it could not tell. A server failing on its plain-http listener has not "
             "revealed whether a working listener would redirect, so any conclusion drawn there "
             "is invented."),
            ("Should I just turn off plain http?",
             "It silences the finding and leaves visitors who type your domain without a scheme "
             "with a connection error. Redirect instead — that is what the address is for."),
        ],
    )


if __name__ == "__main__":
    print(which_host())
