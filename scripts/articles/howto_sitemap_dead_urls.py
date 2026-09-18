"""When "regenerate your sitemap" is the wrong fix — and once, a destructive one.

Promised on the how-to hub. Sourced from `indexability.py`'s sitemap branch,
whose docstrings record four causes that were reported as stale sitemap entries
under advice to regenerate the file:

  * an insurer where fourteen URLs answered with a server error and one
    identical short body, reported by THREE findings at once — following the
    sitemap one would have deleted the evidence of the fault;
  * a food retailer where the audit's own crawl provoked 429s;
  * URLs where nothing came back at all (a status of zero);
  * docketseo.app on GitHub Pages — the host answered dozens of requests, reset
    one connection, and the finding told us to drop a page that answered 200 in
    a browser the same minute.

⚠️ SELF-IMPLICATING CASE IS OURS AND SAFE TO NAME. The others are third parties
and are described without names.

⚠️ DO NOT RE-EXPLAIN RATE LIMITS OR TIMEOUTS. `/how-to/tell-a-rate-limit-from-a-block/`
and `/how-to/pages-an-audit-could-not-reach/` own those. One sentence each and a
cross-link; the subject here is what the REMEDY does when the diagnosis is wrong.

⚠️ THE NUMERAL 500 IS NOT IN verify_numbers' ALLOWED LIST. Say "a server error"
rather than the code. 200/404/429 are allowed.

Numerals: allowed status codes only; quantities spelled as words.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from render import render  # noqa: E402


def sitemap_dead_urls() -> Path:
    body = """
<p class="lede">An audit reports that some of the URLs in your sitemap are broken, and tells you
to regenerate the file so it contains only live, indexable, canonical pages. When those URLs
really are 404s, that is correct and it is the most common sitemap defect there is. When they are
not, it is the one piece of audit advice that can destroy the evidence you needed.</p>

<h2>The case where following it would have hidden a fault</h2>

<p>An insurer's crawl found fourteen URLs answering with a server error — all of them returning
one identical short body, which is its own tell. Three separate findings named those same fourteen
URLs: one at critical severity saying the server was failing, one saying the pages were empty
stand-ins, and the sitemap one saying to regenerate the file.</p>

<p>A reader who started with the sitemap finding would have removed fourteen entries, and with
them the only list pointing at the fault. The critical finding would then have been describing
pages nothing referenced any more, on a site whose sitemap now looked clean.</p>

<p>The distinction is simple once stated and invisible in a list of "errors":</p>

<ul>
<li><strong>A 404 means the page is gone and your sitemap is stale.</strong> Remove the entry.
That is what the advice is for.</li>
<li><strong>A server error means the page is supposed to exist and your server is broken.</strong>
Removing the entry fixes nothing and deletes the record.</li>
</ul>

<p>Both appear under the same heading in most reports. They call for opposite actions.</p>

<h2>Three more things that are not a stale sitemap</h2>

<ul>
<li><strong>A rate limit.</strong> On a food retailer, the audit's own crawl provoked 429s and
the report named three broken sitemap URLs; a re-run minutes later found none. A 429 is the one
refusal a crawler can cause simply by existing —
<a href="/how-to/tell-a-rate-limit-from-a-block/">a rate limit is not a block &rarr;</a>.</li>
<li><strong>Nothing coming back at all.</strong> A status of zero is the crawler's note that it
stopped waiting, not an answer from your server. Reporting it as "broken" describes one working
page two contradictory ways in one document —
<a href="/how-to/pages-an-audit-could-not-reach/">"could not be reached" is not a
diagnosis &rarr;</a>.</li>
<li><strong>A host that hung up once.</strong> This one is ours. Auditing docketseo.app, the host
answered dozens of requests and reset the connection on a single one. Two findings named that
URL: one correctly calling it rate limiting rather than an outage, and this one telling us to drop
from the sitemap a page that answered 200 in a browser the same minute.</li>
</ul>

<p>All four share a test that is worth memorising. <strong>A host that answered is not gone, so a
refusal from it says nothing about the URL.</strong> If the rest of your site came back, the
sitemap entry is almost certainly fine.</p>

<h2>Why this finding deserves more care than most</h2>

<p>Nearly all audit advice is additive: write a description, add a tag, link to a page. If the
finding was wrong you have spent an hour and added something harmless.</p>

<p>This one is subtractive. It asks you to remove a URL from the single document that tells search
engines which pages you have — which is often exactly the document somebody will use later to work
out what went wrong.</p>

<p><strong>A remedy that deletes a record should demand a higher standard of proof than one that
adds a tag.</strong> That is the whole argument of this page, and it applies well beyond sitemaps:
treat "remove", "delete" and "regenerate" differently from "add".</p>

<h2>Reading the finding on your own report</h2>

<ul>
<li><strong>Look at the status beside each URL, not the heading.</strong> If the report does not
show you a status per URL, that is worth knowing about your tool before you act.</li>
<li><strong>Check whether the same URL appears in another finding.</strong> When it does, the
louder finding is usually the true one and this is the echo. On that insurer's report the same
fourteen URLs were in three.</li>
<li><strong>Re-run before you remove anything.</strong> A list that shrinks on the second run was
partly about the run.</li>
<li><strong>Open one in a browser.</strong> Thirty seconds, and it settles every case above.</li>
</ul>

<h2>When the advice is exactly right</h2>

<p>Keep the severity in view — this is a real and common defect, and three shapes of it deserve
the fix as written:</p>

<ul>
<li><strong>Genuine 404s</strong>, usually pages deleted without the sitemap being rebuilt.</li>
<li><strong>URLs that redirect.</strong> A sitemap should list destinations, not stops on the
way.</li>
<li><strong>Pages you have deliberately excluded from indexing.</strong> Listing a page you have
told search engines to ignore is a contradiction, and the sitemap is the easier half to fix.</li>
</ul>

<h2>The fixes that make it worse</h2>

<ul>
<li><strong>Regenerating the sitemap while the server is failing.</strong> Your generator will
faithfully omit every page that could not be rendered, and you will have shipped the outage into
the file.</li>
<li><strong>Removing URLs by hand from a generated file.</strong> The next build puts them back,
and you have learned nothing except that the finding returns.</li>
<li><strong>Cutting the sitemap down until the finding clears.</strong> Which brings us to the
obvious.</li>
</ul>

<h2>How to clear this finding completely</h2>

<p>Publish a sitemap containing one URL that works. The finding goes to zero and so does the
usefulness of the file — a sitemap's job is to list your pages, and a tool counting broken entries
cannot notice the ones you never declared.</p>

<p>Which is the honest limit of the check: <strong>it can only be wrong about URLs you told it
about.</strong> Nothing in a sitemap finding says anything about the pages missing from your
sitemap altogether.</p>

<h2>Where this sits in an audit</h2>

<p>The registered checks are <code>index.sitemap</code>, which reads the file and the URLs in it,
and <code>index.broken</code>, which owns the server-error and unreachable findings that this one
kept duplicating. The identifiers on the findings themselves differ from both — worth knowing when
you search for one by name.</p>

<p>For the outbound version of the same confusion between a refusal and a dead page, see
<a href="/how-to/fix-broken-outbound-links/">how to fix broken outbound links (and which are
not) &rarr;</a>.</p>
"""
    return render(
        cat="how-to", slug="sitemap-urls-that-are-not-stale",
        title="When 'regenerate your sitemap' is wrong",
        desc=("A sitemap finding says regenerate. For a 404 that is right; for four other causes "
              "on a site an audit can make it destructive."),
        h1="When 'regenerate your sitemap' is wrong",
        crumb='<a href="/">Docket</a> / <a href="/how-to/">Fix it</a> / Sitemap URLs',
        body=body,
        faq=[
            ("My sitemap URLs are reported broken but they load fine. Why?",
             "Usually because the crawler got a refusal, a rate limit or a timeout rather than an "
             "answer. If the rest of your site came back during the same crawl, the host is "
             "working and the entries are almost certainly fine."),
            ("Should I remove a sitemap URL that returns a server error?",
             "No. A 404 means the page is gone and the entry is stale; a server error means the "
             "page is supposed to exist and the server is broken. Removing the entry hides the "
             "fault instead of fixing it."),
            ("Why did three findings name the same URLs?",
             "Because several checks can see the same failed fetch from different angles. When "
             "that happens the loudest finding is usually the true one and the others are "
             "echoes — act on the one whose remedy addresses the cause."),
            ("Should a sitemap list redirecting URLs?",
             "No. A sitemap should list destinations rather than stops on the way, so a URL that "
             "redirects belongs in the file only as the address it redirects to."),
            ("Does a clean sitemap finding mean my sitemap is good?",
             "Only that the URLs you declared are reachable. Nothing in the check can see the "
             "pages missing from the file, which is the more common and more expensive sitemap "
             "problem."),
        ],
    )


if __name__ == "__main__":
    print(sitemap_dead_urls())
