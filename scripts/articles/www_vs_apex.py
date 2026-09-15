#!/usr/bin/env python3
"""www vs non-www: everyone gives the advice, nobody counted.

⚠️ WHY THIS PAGE EXISTS. **Page one, checked 2026-09-15 before writing**, for
"www vs non-www SEO does it still matter 2026": namesilo.com, cognitiveseo.com,
searchenginejournal.com, spyfu.com, wpbeginner.com, seranking.com, llmrefs.com,
seotorontoexperts.ca, seattlenewmedia.com. **No vendor documentation on page
one**, so the query passes the winnability rule. All nine agree with each other
— it no longer matters much, pick one and redirect the other — and **not one of
them measures how many sites actually got it wrong.** That gap is the entire
reason this page exists. The advice is not in dispute; the incidence is simply
unknown, and an unknown incidence is measurable.

**Original measurement:** Docket's own probe of a random sample of the Tranco
top 10,000, 2026-09-15, recorded in `data/www-canonical-2026-09.json`.

⚠️ WHAT THIS PAGE MUST NOT BECOME. `/learn/canonical-tags/` explicitly punts on
this — it says `index.www` handles apex-versus-www separately because it is a
server configuration rather than a markup mistake. So this page **links** that
one and does not re-explain canonical tags.
`/how-to/redirect-http-to-https/` touches apex/www only where a TLS certificate
has to cover both names. Neither spine is repeated here.

⚠️ THE DIRECTION IS NOT MEASURED. The dataset records **whether** a redirect
happened, never **which way round** it resolved. No sentence on this page may
claim sites prefer www, or prefer the apex. See the "what we did not measure"
section, which says so out loud rather than leaving the reader to infer it.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import facts as F  # noqa: E402
from render import render  # noqa: E402

#: When the probe ran. In a constant because the derived-number gate refuses a
#: DATE typed into prose — "15 September 2026" is three literals to a regex that
#: cannot tell a day-of-month from a measurement.
MEASURED_HUMAN = "15 September 2026"

#: The same date, month-precision, for the one sentence that wants the month
#: rather than the day. Split out rather than sliced off the string above,
#: because a slice is a puzzle and a constant is a fact.
MEASURED_MONTH_HUMAN = "September 2026"

#: The month of the separate, much larger robots.txt survey quoted once for
#: contrast. Same reason as above; no digits in it, but it belongs beside its
#: sibling rather than loose in a sentence.
SURVEY_MONTH_HUMAN = "August 2026"


def www_vs_apex() -> Path:
    sample = F.www_sample()
    reachable = F.www_reachable()
    unreachable = F.www_unreachable()
    pct_unreachable = F.www_pct_unreachable()
    both = F.www_both_serve()
    redirects = F.www_redirects()
    non_2xx = F.www_other_non_2xx()
    absent = F.www_other_absent()
    answered = F.www_other_answered()
    pct_sample = F.www_pct_of_sample()
    pct_reachable = F.www_pct_of_reachable()
    pct_answered = F.www_pct_of_answered()

    #: What the FIRST, BROKEN run of this probe reported, before the
    #: final-origin fetch existed. It is carried in the dataset rather than
    #: typed here precisely so this page can cite the error without becoming
    #: the only place it lives — and the dataset's `erroneous_first_run_note`
    #: records that it is not a measurement of anything real.
    first_run_pct = F.www_erroneous_first_run_pct()

    #: Derived, not typed: the share of reachable origins that had already
    #: resolved the question by redirecting one spelling onto the other.
    pct_redirect = round(100 * redirects / reachable, 1)
    #: How far the first, broken run overstated the answer. Derived from the two
    #: dataset figures above, so the multiplication is one a reader can do on the
    #: two numbers printed beside it — and neither input is typed here.
    inflation = round(first_run_pct / pct_sample, 1)

    #: The separate robots.txt survey, quoted ONLY to show that a fifth of hosts
    #: refusing an identified bot is a property of the method rather than a fluke
    #: of this draw. SAME sampling frame — the directives dataset's `population`
    #: field is literally "Tranco top 10000 (list PYG5J)" — but a different month
    #: and a different request (GET /robots.txt, not GET /), which is why the
    #: prose says "suggests" and not "shows".
    survey_n = F._d()["attempted"]
    survey_unreachable = F.pop_unreachable()
    survey_pct_unreachable = round(100 * survey_unreachable / survey_n, 1)

    body = f"""
<div class="callout">
<div class="callout-title">Quick answer</div>
<p><strong>No, it barely matters which one you choose — and yes, you still have to choose one.</strong>
That is what every result on page one for this question says, and it is correct. None of them counts
how many sites actually still have two live copies, so we did.</p>
<p><strong>In a random sample of {sample} hosts drawn from the Tranco top 10,000 and probed on
{MEASURED_HUMAN}, {both} still served the site on both spellings</strong> — {pct_sample}% of the
sample, {pct_reachable}% of the {reachable} origins that answered at all, {pct_answered}% of the
{answered} whose other spelling returned a 2xx. Three different denominators, three different
numbers, and they are not interchangeable.</p>
<p><strong>Most of the web has already settled it:</strong> {redirects} of {reachable} reachable
origins — {pct_redirect}% — redirected one spelling onto the other. The advice is not wrong. It is
just aimed at a minority now, and nobody had said how small a minority.</p>
</div>

<h2>Nine pages agree with each other. None of them counted.</h2>

<p>Search this question and you get nine results that say the same three things: search engines have
handled it for years, it is a duplicate-content problem rather than a ranking-factor problem, pick one
spelling and redirect the other. That advice is sound and this page does not argue with it.</p>

<p>What is missing from all nine is the number that decides whether you need to act. "Sites that get
this wrong split their signals" is a mechanism, not a measurement. It tells you what happens to a site
in that state; it does not tell you whether yours is likely to be one, or whether the problem is still
a live one in {MEASURED_MONTH_HUMAN} at all. So we measured the incidence instead of restating the
mechanism.</p>

<h2>What we measured, and on how many hosts</h2>

<p><strong>Start with the size, because it governs everything below: {sample} hosts.</strong> A random
sample of the Tranco top 10,000, drawn with a recorded seed, two requests per host, no page crawl.
This is a sample, not a survey — it is small enough that a reader should treat every share here as an
indication rather than a census, and every figure on this page is published with the denominator it
came from.</p>

<p>For each host the probe does two things in order, and <strong>the order is the whole
measurement</strong>:</p>

<ol>
<li><strong>Fetch the host and follow redirects to find the site's final origin.</strong> Whichever
spelling the site actually settled on, that is now the canonical host.</li>
<li><strong>Fetch the opposite spelling of that origin</strong> and see where it lands.</li>
</ol>

<p>This replicates the check Docket ships rather than approximating it. The audit engine runs the same
logic against your own site, and it deliberately does not ask the naive question "do both spellings
return 200?", because that question produces false findings on real servers.</p>

<h2>Four outcomes, and only one of them is a defect</h2>

<table>
<thead><tr><th>What the other spelling did</th><th>Hosts</th><th>Is it a problem?</th></tr></thead>
<tbody>
<tr><td>Did not resolve at all</td><td>{absent}</td><td><strong>No.</strong> There is no second
hostname, so there is nothing to canonicalise.</td></tr>
<tr><td>Answered, but not with the site — 404, 403 or another non-2xx</td><td>{non_2xx}</td>
<td><strong>No.</strong> A 404 on the other spelling is the correct configuration, and a 403 is
usually a bot block. Neither is a second copy of anything.</td></tr>
<tr><td>Answered 2xx and landed back on the canonical host</td><td>{redirects}</td><td><strong>No.</strong>
This is the resolved state the advice asks for.</td></tr>
<tr><td>Answered 2xx and did <em>not</em> land back on the canonical host</td><td>{both}</td>
<td><strong>Yes.</strong> Two hostnames are serving the site.</td></tr>
<tr><td><strong>Reachable origins</strong></td><td><strong>{reachable}</strong></td><td></td></tr>
</tbody>
</table>

<p>The second row is the one that separates a real check from a naive one, and Docket learned it the
expensive way. An independent-bookshop marketplace answers 403 to everything automated. Both spellings
returned 403, neither redirected to the other, and the tool reported a duplicate-content finding at
high severity. There was no duplicate. There were two bot-block pages. A search engine sees no second
copy of that site, because there is no second copy — there is a door that is shut on both names.</p>

<p>So a non-2xx on the other spelling is scored as fine here, not as a failure and not as a pass we
are quietly proud of. Those {non_2xx} hosts are still counted among the {reachable} reachable ones;
they are simply outside the {answered}-host denominator, because you cannot serve a second copy of a
page you did not serve.</p>

<h2>The first run was wrong by a factor of {inflation}, and the reason is the useful part</h2>

<p>The first version of this probe reported <strong>{first_run_pct}% of sites serving both
spellings</strong> — roughly half the web, which should have been unbelievable on its face. The
shipped figure is {pct_sample}% of the sample. <strong>One missing fetch, {inflation} times the
answer.</strong></p>

<p>The bug: it compared the <code>www</code> spelling against <strong>the apex it started from</strong>
instead of resolving the site's final origin first. Consider a site correctly canonicalised on
<code>www</code>. The probe requested the apex, got redirected to <code>www</code>, then requested
<code>www</code>, got a 200, observed that this 200 was not the apex it had started at — and scored a
perfectly configured site as a duplicate. Every site that chose <code>www</code> failed. That is a
large fraction of the web, which is exactly why the wrong number looked like half of it.</p>

<p>This is written out at length because <strong>it is the mistake a reader running their own check
will make.</strong> The instinctive test is "curl both, compare". The instinctive test is wrong, and it
is wrong in the direction that manufactures work for you. Resolve the final origin first. Everything
after that is easy.</p>

<h2>What this measurement does not say</h2>

<p>The limits below are not formalities, and a reader who skips them will over-read every figure
above:</p>

<ul>
<li><strong>{unreachable} of the {sample} sampled origins — {pct_unreachable}% — never answered an
identified bot at all.</strong> They are excluded: not counted as pass, not counted as fail. That is a
real hole in the denominator, and if hosts that refuse identified bots differ systematically from
hosts that do not, every share above is drawn from a population that is not quite the web. For scale,
a separate robots.txt survey of the <em>whole</em> Tranco top 10,000 in {SURVEY_MONTH_HUMAN} found
{survey_unreachable:,} of {survey_n:,} hosts — {survey_pct_unreachable}% — unreachable to the same
kind of identified request. Same list, different month, a different request, and the same rough
fifth. That suggests the unreachable share is a property of asking as a named bot rather than an
accident of a {sample}-host draw; it does not make those hosts' configuration knowable.</li>
<li><strong>The list is not the web either.</strong> The Tranco top 10,000 is a rank-aggregated list
of busy hostnames, and it contains CDN and infrastructure hostnames that are not websites at all. A
hostname with no site on it can still redirect, or not, and it is counted here the same as a
publisher.</li>
<li><strong>We did not measure consequences.</strong> Nothing here says a site serving both spellings
lost rankings, traffic or anything else. It says two hostnames both serve the site. The harm is a
well-described mechanism, not something this probe observed, and we are not going to dress a hostname
count up as a traffic study.</li>
<li><strong>This is one request pair per host, at one moment.</strong> A site can behave differently
by geography, by CDN node, or on a different day. A host that redirected cleanly for us may not for a
visitor routed through another edge.</li>
<li><strong>We did not record which spelling sites choose.</strong> The probe stored <em>whether</em>
a redirect happened, never which way round it resolved, so this page cannot tell you whether the web
prefers <code>www</code> or the bare apex. That is a different measurement and we have not taken it.
Anyone quoting a split in that direction is not quoting us.</li>
</ul>

<p>The whole dataset behind this page — every count, the sampling frame, the method, and the note
explaining the first run's error — is published as
<a href="/data/www-canonical-2026-09.json">www-canonical-2026-09.json</a>. Host names are not in
it: publishing a named site's misconfiguration to sell a tool is not a trade this project
makes.</p>

<h2>Run the same two requests on your own site</h2>

<p>You need a terminal and about thirty seconds. Resolve the final origin first — that is the step the
broken run skipped:</p>

<pre><code>curl -sS -L -D - -o /dev/null https://example.com/ \\
  | grep -iE '^(HTTP/|location:)'</code></pre>

<p>That prints the status line and <code>Location</code> header of every hop and throws the bodies
away. Read the hostname off the last hop: that is your canonical origin, whichever spelling it turned
out to be. Now ask the opposite spelling where <em>it</em> lands, using the same command:</p>

<pre><code>curl -sS -L -D - -o /dev/null https://www.example.com/ \\
  | grep -iE '^(HTTP/|location:)'</code></pre>

<p>Match the result against the table above. If the last hop is a 2xx on your canonical origin, you
are done. If the last hop is a 2xx on any other hostname — including the case where it lands on some
third hostname entirely — you have two copies. If the other spelling 404s, does not resolve, or
answers 403, you have nothing to fix.</p>

<p>Use a real GET rather than <code>curl -I</code>. A HEAD request is a different request, and servers
and CDNs are entitled to answer it differently from the GET a search engine will actually send.</p>

<p>Do it with a path attached as well, not just the homepage. A redirect that sends every URL to the
homepage of the other spelling is a different and worse bug than no redirect at all, and a homepage-only
test cannot see it.</p>

<h2>If you are in the minority, the fix is one rule</h2>

<p>A site-wide <strong>301</strong> from the spelling you are not keeping to the one you are,
<strong>preserving the path and query string</strong>. Not a 302, which asks search engines to keep
both in play. Not a homepage redirect, which throws away every deep link pointing at the losing
spelling. One rule, at the server or CDN, applied to everything.</p>

<p>Which spelling you keep does not matter for search. It matters for cookies, for certificate
coverage and for what your existing links already say, so the honest tiebreak is "whichever one most of
your inbound links and your existing configuration already point at". Then make everything else agree
with it: internal links, sitemap entries, canonical tags and the address in your analytics.</p>

<p>Two adjacent jobs are worth doing in the same sitting. Your TLS certificate has to cover both names
even after you pick one, because the losing spelling still has to complete a handshake before it can
serve your redirect — that is covered in
<a href="/how-to/redirect-http-to-https/">redirecting HTTP to HTTPS</a>. And if your pages already
carry canonical tags, they now need to name the spelling you kept;
<a href="/how-to/fix-conflicting-canonicals/">conflicting canonical tags</a> is the failure mode where
half your templates were updated and half were not.</p>

<h2>Where this sits next to canonical tags</h2>

<p>It is tempting to reach for <code>rel="canonical"</code> here, and that is the wrong tool.
<a href="/learn/canonical-tags/">Canonical tags</a> deliberately leaves apex-versus-www alone: it is a
server configuration, not a markup mistake, and a tag asking politely for one hostname while the server
happily serves both is a weaker instruction than a redirect that makes the second hostname stop
existing. Fix it at the server. The tag is for the duplicates a server cannot resolve.</p>

<p>Docket checks this on every audit as part of the crawl setup rather than as a page-level rule —
the full list of what it looks at is in <a href="/learn/what-docket-checks/">what Docket checks</a>,
and <a href="/learn/seo-audit/">what an SEO audit is</a> covers where a hostname check sits among the
rest. The {SURVEY_MONTH_HUMAN} survey quoted above for the unreachable share is published in full in
the <a href="/index/ai-directives/">AI directives index</a>.</p>

<p><a class="btn" href="/download/">Download Docket</a></p>
"""
    return render(
        cat="learn", slug="www-vs-non-www",
        title="www vs non-www: what sites actually do, measured",
        desc=("Nine page-one results agree you should pick one. None counted. Docket probed a "
              "random sample of the Tranco top 10,000 to see how many still serve both."),
        h1="www vs non-www: does it still matter?",
        crumb='<a href="/">Docket</a> / <a href="/learn/">Learn</a> / www vs non-www',
        body=body,
        published="2026-09-15",
        faq=[
            ("Does www vs non-www still matter for SEO?",
             f"Only if you have not picked one, and most sites have. In a random sample of {sample} "
             f"hosts from the Tranco top 10,000 probed on {MEASURED_HUMAN}, {redirects} of the "
             f"{reachable} origins that answered — {pct_redirect}% — already redirected one spelling "
             f"onto the other. Just {both} served the site on both spellings: {pct_sample}% of the "
             f"sample, {pct_reachable}% of reachable origins, {pct_answered}% of the {answered} whose "
             "other spelling returned a 2xx. It is a real defect and it is an uncommon one."),
            ("How do I check whether my own site serves both?",
             f"Two requests, in this order. First fetch your site and follow redirects to find its "
             f"final origin — that is your canonical hostname, whichever spelling it turned out to be. "
             f"Then fetch the opposite spelling of that origin and see where it lands. A 2xx that ends "
             f"up back on your canonical host is fine. A 2xx that ends up anywhere else, including a "
             f"third hostname, means two copies. Skipping the first fetch is the mistake that made our "
             f"own first run report {first_run_pct}% instead of {pct_sample}%."),
            ("My other spelling returns a 403 or a 404. Is that a problem?",
             f"No, and treating it as one is a common false positive. A 404 on the spelling you are "
             f"not using is the correct configuration, and a 403 is usually a bot block rather than a "
             f"page. Two bot-block responses are not duplicate content. Docket learned this from an "
             f"independent-bookshop marketplace that answers 403 to everything automated: both "
             f"spellings returned 403 and the tool wrongly reported a duplicate. In the sample, "
             f"{non_2xx} of {reachable} reachable origins answered non-2xx on the other spelling and "
             f"are scored as fine."),
            ("Should I use a canonical tag or a redirect?",
             f"A redirect. A site-wide 301 from the spelling you are dropping to the one you are "
             f"keeping, preserving the path and query string — not a 302, and not a redirect that "
             f"sends everything to the homepage. A canonical tag asks politely for one hostname while "
             f"your server carries on serving both; a 301 makes the second hostname stop serving. "
             f"Docket's canonical checks deliberately leave apex-versus-www alone for that reason: it "
             f"is a server configuration rather than a markup mistake."),
            ("Do more sites use www or the bare apex?",
             f"We do not know, and this page will not guess. The probe recorded whether a redirect "
             f"happened, not which direction it resolved, so the {redirects} redirecting origins out "
             f"of {reachable} reachable ones are not split by spelling anywhere in the data. It is a "
             f"measurement we have not taken. Separately, {unreachable} of the {sample} sampled hosts "
             f"— {pct_unreachable}% — never answered an identified bot at all and are excluded from "
             "every figure here, which is a real limit on all of them."),
        ],
    )


BUILDERS = [www_vs_apex]


def build_all() -> list[Path]:
    return [b() for b in BUILDERS]


if __name__ == "__main__":
    for p in build_all():
        print(p)
