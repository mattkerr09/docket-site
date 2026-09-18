"""Why an hreflang target is reported as dead.

Promised on the how-to hub. Sourced from the registered check
`intl.hreflang_targets` in `backend/seo_engine/checks/international.py`, which
carries both halves:

  * THE CHECK COULD ONLY FIRE ON CORRECT SITES. `redirect_chain` is the chain
    that led TO a page, not one starting at it, so the old redirect test only
    matched targets that were already right. Over thousands of hreflang targets
    on one site it fired once — on a URL returning 200 that does not redirect —
    and advised pointing hreflang at the final destination to a site already
    doing so.
  * TWO OF THE FOUR "DEAD TARGET" CAUSES ARE FACTS ABOUT THE CRAWLER. A refusal
    is about us, not the target; a status of zero means the target sent nothing
    at all, and that branch once produced a MEDIUM about "unusable URLs" from a
    blip on one machine.

⚠️ NO SITE IS NAMED — third-party gate.

⚠️ DO NOT OVERLAP /how-to/fix-hreflang-return-tags/ (return tags, the four ways
a SET breaks) or /how-to/fix-invalid-hreflang-codes/ (syntax of a value).
Neither covers target health; this page cross-links both.

⚠️ THE "SAME NEWS TWICE" NOTE MUST SURVIVE: the refusal branch deliberately
adds no finding of its own, because the site-level check already reports it.

Numerals: allowed status codes only; quantities spelled as words.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from render import render  # noqa: E402


def hreflang_targets() -> Path:
    body = """
<p class="lede">An audit says your hreflang tags point at URLs that do not work. Before you edit a
single tag, it is worth knowing that "does not work" covers four quite different situations — and
on the two most common ones the honest answer is that the tool learned nothing.</p>

<h2>The four causes, and who each one is about</h2>

<ul>
<li><strong>The target returns an error.</strong> A 404 or a server error on a URL your hreflang
names is real and worth fixing: you are telling search engines that the Spanish version of this
page lives somewhere that is not there.</li>
<li><strong>The target is set to noindex.</strong> Also real, and quieter. An hreflang cluster
pointing at a page you have asked search engines to ignore is a contradiction you wrote
yourself.</li>
<li><strong>The target refused the crawler.</strong> <em>This is a fact about the audit, not about
your site.</em> A 403 to one tool says nothing about what a search engine is served, and it is not
evidence that anything in the cluster is broken.</li>
<li><strong>The target sent nothing at all.</strong> A status of zero is not a response — it is a
refused connection, a DNS hiccup, a timeout, a dropped packet. The tool has no information
whatever about that URL.</li>
</ul>

<p>The last two used to be reported like the first two. The zero case sat inside the
error branch and produced a medium-severity finding saying the reader's hreflang tags pointed at
"unusable URLs" that returned "no response" — <strong>from a blip on one machine.</strong></p>

<h2>The refusal that deliberately says nothing</h2>

<p>Worth its own paragraph, because the fix here was to report <em>less</em>.</p>

<p>When a target refuses the crawler, the check could add an "unverified" note of its own. It does
not — because if the site is refusing the audit at all, the site-level check already says so,
clearly, once. <strong>Two findings describing one fact are not twice as informative; they are the
same news twice, and the reader has to work out they are the same thing.</strong></p>

<p>For what a refusal does and does not tell you, see
<a href="/how-to/pages-an-audit-could-not-reach/">"could not be reached" is not a
diagnosis &rarr;</a>.</p>

<h2>The redirect test that could only fire on correct sites</h2>

<p>This is the half worth the page. The remaining cause — an hreflang target that redirects
somewhere else instead of resolving directly — is genuinely worth reporting, because a cluster
resolves better when every URL in it is a destination rather than a stop on the way.</p>

<p>The old test read the wrong end of the data. A crawler records, for each page it fetched, the
chain of URLs that <em>led to</em> that page. That chain is non-empty exactly when the crawler
arrived by being redirected — which makes the page it is attached to the <strong>final
destination</strong>, the thing hreflang is supposed to point at.</p>

<p>So the check fired when the target was already right. On one site with thousands of distinct
hreflang targets it produced exactly one finding: a URL that returns 200 and does not redirect
anywhere, which the crawler had simply reached from a different address. The advice attached was
<em>point each hreflang at the final destination URL</em> — given to a site that already was.</p>

<p><strong>A test that fires only on correct input is worse than a test that never fires</strong>,
because it produces confident work for people who had nothing to fix, and it is invisible in
aggregate: the finding count looks plausible, the affected sites look unlucky, and nobody
investigates a rule that is quiet on the sites where the fault is real.</p>

<p>The repair was to collect the URLs that were redirected <em>away from</em> — the first entries
of those chains — and test membership of that set instead.</p>

<h2>Reading this on your own report</h2>

<ul>
<li><strong>Look at the reason beside each target, not the headline.</strong> "Returns 404",
"is set to noindex", "redirects instead of resolving" and "returned no response" are four
different jobs, and one of them is not a job at all.</li>
<li><strong>Open a target that was called unreachable.</strong> If it loads in a browser, the
finding was about the crawl.</li>
<li><strong>Check whether the whole site refused the audit.</strong> If there is a site-level
refusal finding, treat every target-level one as unverified rather than false.</li>
<li><strong>For a redirecting target, follow it once.</strong> Point the tag at where you land,
and check the page you land on carries the return tag back.</li>
</ul>

<h2>When this matters</h2>

<p>An hreflang cluster is a set of mutual claims, and one bad member weakens the set rather than
just itself — which is why a dead target is worth more attention than its severity suggests. But
that is true only of the causes that are about your site. A target reported as unreachable by a
tool that could not connect is not a defect in your markup, and rewriting tags to chase it makes
a correct cluster wrong.</p>

<h2>The fixes that make it worse</h2>

<ul>
<li><strong>Removing an hreflang entry because its target was unreachable during one crawl.</strong>
You have broken a mutual set to satisfy a transient network condition.</li>
<li><strong>Repointing tags at URLs that were already destinations.</strong> The unfollowable
advice above, and the reason the test was rewritten.</li>
<li><strong>Adding a redirect so the target "resolves".</strong> The target was fine; the tag
should name it directly and usually already does.</li>
</ul>

<h2>How to clear this without improving anything</h2>

<p>Delete the hreflang annotations. Every target-health finding disappears, along with any chance
of the right language version being served — which is the general shape of these pages: <strong>the
fastest way to a clean report is always to remove the thing being measured.</strong></p>

<h2>Where this sits in an audit</h2>

<p>The registered check is <code>intl.hreflang_targets</code>, which covers hreflang target
health. Its siblings cover the other halves of the subject:
<a href="/how-to/fix-hreflang-return-tags/">return tags and the four ways a set breaks &rarr;</a>,
and <a href="/how-to/fix-invalid-hreflang-codes/">invalid language and region codes &rarr;</a>.</p>
"""
    return render(
        cat="how-to", slug="hreflang-targets-that-look-dead",
        title="Why an hreflang target is reported as dead",
        desc=("Four reasons an hreflang target is called broken, two of which are facts about "
              "the audit rather than about your site."),
        h1="Why an hreflang target is reported as dead",
        crumb='<a href="/">Docket</a> / <a href="/how-to/">Fix it</a> / hreflang targets',
        body=body,
        faq=[
            ("My hreflang targets load fine but the audit calls them unreachable. Why?",
             "Because the crawler got no response — a refused connection, a DNS hiccup or a "
             "timeout. A status of zero is not something your server sent, so nothing has been "
             "learned about that URL."),
            ("Is a 403 on an hreflang target a problem?",
             "Not necessarily. A refusal is a fact about the tool that asked, not about what a "
             "search engine is served. If the whole site refused the audit, treat target-level "
             "findings as unverified."),
            ("Should hreflang point at a URL that redirects?",
             "No — point it at where the redirect lands, and make sure that page carries the "
             "return tag back. A cluster resolves better when every member is a destination."),
            ("Can an hreflang target be noindex?",
             "It should not be. Naming a page in a language cluster while telling search engines "
             "to ignore that page is a contradiction, and the cluster is the easier half to "
             "correct."),
            ("One bad target — does it matter?",
             "More than its severity suggests. An hreflang set is a group of mutual claims, so a "
             "member that does not resolve weakens the set rather than only itself."),
        ],
    )


if __name__ == "__main__":
    print(hreflang_targets())
