#!/usr/bin/env python3
"""How common are internal links carrying UTM parameters?

⚠️ WHY THIS PAGE EXISTS AND WHY IT IS NOT THE TRACKING-LANE PAGE.
`/learn/marketing-tag-audit/` owns the tracking lane: the six martech checks and
a self-check, and it explains the internal-UTM *mechanism* in one paragraph.
This page does not re-argue the mechanism. It answers a question that paragraph
does not: **how often does this actually happen, and in what shape when it
does.** The two link to each other rather than repeating.

**Pre-registration — the prior check (2026-09-15)** of "internal links with UTM
parameters SEO problem" returned nine results: searchengineland.com,
seroundtable.com, searchseven.co.uk, site-analyzer.pro, berreby.ai, attri.io,
sammyseo.com, vonclaro.com, seovendor.co. **No vendor documentation; no study of
any size.** Every one of them asserts that the practice is harmful; **not one
measures how often it happens.**

**RE-RUN, 2026-09-15, by the writer of this page.** Same query. The result set
came back **identical — the same nine domains, in the same order.** No
google.com, no developers.google.com, no support.google.com/analytics, no GA4
help page appeared anywhere on page one. No prevalence measurement, no sample
size, no survey by anyone. The assertion-without-a-denominator gap the brief
described is still exactly the gap, so the page stands as scoped. Had a vendor
doc or a published measurement appeared, the honest move would have been to
kill the page rather than add a tenth assertion; it did not, so we ship.

**Original measurement:** Docket's own audit of 40 Tranco hosts, 2026-09-15, in
`data/utm-internal-2026-09.json`. Every figure on the page is read through
`facts.py`; nothing is typed into prose.

**WHERE THE BRIEF WAS SOFTENED.** The brief calls the per-host distribution
"bimodal". The counts do sit at two ends with nothing between, but there are six
affected hosts and six observations cannot establish the shape of a
distribution. The page shows the split, names the two cases, and says in its own
words that it will not call it bimodal on this evidence.

**THE CEILING IS LOAD-BEARING.** `pages_affected` is bounded by the crawl limit.
A host at the cap means every page we looked at carried such a link — NOT that
the site has that many pages. It is stated in the paragraph that introduces the
page-count column, not in a footnote, because a reader who takes the cap for a
site total has been misled by us rather than by their own carelessness.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import facts as F  # noqa: E402
from render import render  # noqa: E402

#: When the sample was crawled, and when page one was re-checked. Dates live in
#: constants and are interpolated: the derived-number gate refuses a date typed
#: into prose, and it is right to — a date in two places drifts in one of them.
MEASURED_HUMAN = "15 September 2026"
CHECKED_HUMAN = "15 September 2026"

#: The pool the sample was drawn from. It is recorded in the dataset's `method`
#: string as prose rather than as a field, so there is no accessor for it; a
#: single constant is the next best thing to one. Flagged in the handover.
TRANCO_POOL_HUMAN = "10,000"

#: The boundary `facts.utm_hosts_isolated()` counts against, used BOTH to
#: classify the table rows and to word the sentence about them, so the prose and
#: the classification cannot disagree.
ISOLATED_MAX = 4
ISOLATED_MAX_HUMAN = "four"


def internal_utm() -> Path:
    sample = F.utm_sample()
    crawled_ok = F.utm_crawled_ok()
    hosts = F.utm_hosts()
    pct = F.utm_pct_hosts()
    links_total = F.utm_links_total()
    links_median = F.utm_links_median()
    links_max = F.utm_links_max()
    pages = F.utm_pages_affected()
    at_cap = F.utm_hosts_at_cap()
    isolated = F.utm_hosts_isolated()
    cap = F.utm_page_cap()
    seed = F._u()["seed"]
    clean = sample - hosts

    #: One row per affected host, built from the distribution itself so the
    #: table can never say something the list does not. Hosts are lettered
    #: because they are withheld: publishing a named site's misconfiguration to
    #: sell a tool is not a trade this project makes.
    def _shape(n: int) -> str:
        if n >= cap:
            return ("Every page we crawled. A <strong>lower bound</strong> — "
                    "the true figure is however many pages the site has.")
        if n <= ISOLATED_MAX:
            return "Isolated. Consistent with links tagged one at a time, by hand."
        return "Nearly every page we crawled. Consistent with a template."

    rows = "\n".join(
        f"<tr><td>Host {chr(65 + i)}</td><td>{n}{' (at the crawl limit)' if n >= cap else ''}"
        f"</td><td>{_shape(n)}</td></tr>"
        for i, n in enumerate(pages))

    body = f"""
<div class="callout">
<div class="callout-title">Quick answer</div>
<p><strong>A modest minority of sites do it.</strong> In a random sample of
<strong>{sample}</strong> Tranco hosts crawled on {MEASURED_HUMAN}, <strong>{hosts} of {sample}
({pct}%)</strong> emitted at least one link to their own site carrying UTM parameters.
<strong>{clean} of {sample}</strong> emitted none at all.</p>
<p><strong>The share is not the useful part. The shape is.</strong> The affected hosts split in
two: some carried such links on a handful of pages, and some carried them on
every page we looked at. We measured where the links are, not how they got there — but the two
shapes point at different work. A handful of pages is consistent with links tagged one at a time;
every page is consistent with something in a template, and <strong>a template would be one fix
rather than many</strong>.</p>
<p><strong>We did not measure any consequence.</strong> This counts what the HTML emits. What an
analytics tool then does with it is documented behaviour, not something this survey observed — the
mechanism is explained on <a href="/learn/marketing-tag-audit/">the marketing tag audit</a>.</p>
</div>

<h2>Everyone asserts it. Nobody counted it.</h2>

<p>Search for the SEO problem with UTM parameters on internal links and page one is unanimous: it
overwrites the original source of the session, it multiplies URLs, stop doing it. Re-checked on
{CHECKED_HUMAN}, every result on page one made the argument. <strong>Not one of them stated how often
it happens.</strong> There was no vendor documentation on the page and no study of any size — no
sample, no denominator, no rate. Nine pages agreeing on a mechanism is not evidence about a
prevalence, and after a while an unmeasured claim starts to sound measured simply from repetition.</p>

<p>So the mechanism is not our finding and this page does not re-argue it. It is well documented, and
<a href="/learn/marketing-tag-audit/">the marketing tag audit</a> already explains in a paragraph what
a tagged internal link does to a session. What follows is the missing half: <strong>how often, and in
what shape.</strong></p>

<h2>What we counted, exactly</h2>

<p>On {MEASURED_HUMAN}, Docket crawled <strong>{sample}</strong> hosts drawn with a recorded seed
(<code>{seed}</code>) from the Tranco top {TRANCO_POOL_HUMAN} — at most <strong>{cap}</strong> pages
each, with its own identified user-agent and its own backoff. Ordinary crawling at the scale a
customer runs, not a special-purpose scrape.</p>

<p>A host counts as affected when any indexable page it served emitted a link to the same site whose
URL carries a <code>utm_</code> parameter. That definition is narrower in several places than the
phrase "internal links with UTM parameters" suggests, and the differences are worth having in front of
you before the numbers:</p>

<ul>
<li><strong>Same site means the same host, with <code>www.</code> treated as equivalent to the
apex.</strong> A link from a blog subdomain to the main domain is not counted as internal here. If you
tag links across your own subdomains, this survey did not see it.</li>
<li><strong>Indexable pages only.</strong> A tagged link sitting on a <code>noindex</code> page does
not make its host count.</li>
<li><strong>Links, not destinations.</strong> The same tagged navigation item appearing on three pages
is three links. The totals below are counts of anchors, not of distinct URLs.</li>
<li><strong>The match is on the <code>utm_</code> prefix appearing in the link, not on a list of five
approved parameter names.</strong> Anything named <code>utm_</code>-something counts, and so, in
principle, would a <code>utm_</code> that turned up somewhere in a URL that was not a parameter at
all. We did not find a case of the latter, but we also did not go looking for one.</li>
</ul>

<p><strong>All {crawled_ok} of {sample} hosts crawled successfully.</strong> That is worth stating
rather than assuming. In a survey where unreachable hosts drop out — a robots.txt survey, say — the
denominator quietly thins and every share computed from it is a share of whoever answered. Here the
denominator is the sample.</p>

<h2>The number</h2>

<p><strong>{hosts} of the {sample} hosts ({pct}%)</strong> emitted at least one internal link carrying
UTM parameters. Across those hosts, <strong>{links_total}</strong> such links in total, with a median
of <strong>{links_median}</strong> per affected host and a maximum of <strong>{links_max}</strong> on
a single host.</p>

<p>{sample} hosts is a small sample and we are not going to dress it up as more. It supports "this is
a real minority practice, not a myth and not a majority"; it does not support a confident rate to the
decimal place, and it says nothing about sites outside the top of the Tranco list. Every share on this
page is quoted with its denominator for that reason.</p>

<h2>The distribution, which is the actual finding</h2>

<p><strong>Read the page-count column with its ceiling in mind.</strong> We crawled at most
<strong>{cap}</strong> pages per host, so the number of affected pages cannot exceed
<strong>{cap}</strong>. <strong>A host showing {cap} means every page we looked at carried such a link
— not that the site has {cap} pages.</strong> For those hosts the count is a lower bound and
<strong>the share of the site affected is unmeasured</strong>. <strong>{at_cap}</strong> of the
affected hosts sit at that ceiling.</p>

<table>
<thead><tr><th>Host (withheld)</th><th>Pages carrying such a link, of up to {cap} crawled</th>
<th>What that shape is consistent with</th></tr></thead>
<tbody>
{rows}
</tbody>
</table>

<p>The affected hosts do not sit on a smooth curve from "a bit" to "a lot". They sit at the two ends:
<strong>{isolated}</strong> hosts had it on {ISOLATED_MAX_HUMAN} pages or fewer, and the rest had it on
nearly or exactly every page crawled, with nothing in between. <strong>Say that carefully, though.</strong>
{hosts} hosts is far too few to establish the shape of a distribution — a split this clean in a group
this small could be chance, and we are not going to call it bimodal on this evidence. What it does do
is show you the two cases exist, and they are worth telling apart when you look at your own site.</p>

<p>Those two clusters are different problems that happen to trip the same check:</p>

<ul>
<li><strong>The handful.</strong> Somebody built a link by hand — a banner, a promo, an email landing
page reused as an internal CTA — and pasted the tagged URL rather than the clean one. The fix is to
edit those links. Finding them is the whole job.</li>
<li><strong>The whole site.</strong> A header, footer, nav or card component is emitting the parameter
on every render. <strong>This looks like the worse problem and is usually the cheaper one:</strong> it
is one template, and changing it changes every page at once. The page count is not a measure of how
much work it is.</li>
</ul>

<p>A per-page count without this split is close to useless, which may be why nobody publishes one. A
tool that reports "{links_max} internal links carrying UTM parameters" and stops has told you the
size of the number and nothing about the size of the job.</p>

<h2>A tagged internal link is not automatically a mistake</h2>

<p>Some teams tag their own links deliberately. If you want to know how many people clicked the
specific banner in the middle of your homepage, tagging that link is one way to find out, and a team
that does it knowingly has accepted the cost in exchange for the measurement. That is a decision, not
an error.</p>

<p>Nothing in this survey can tell those apart. <strong>The check reports the links; it does not read
intent</strong>, and neither do we. When you look at your own results you are the only person who
knows which of your tagged links were chosen and which were pasted. What the numbers here support is
narrow and worth stating plainly: this happens on a minority of sites, and where it happens it is
usually either a few links or all of them.</p>

<h2>How to find them on your own site</h2>

<p>You do not need a tool for the first pass. Look at the rendered HTML of a page and search it for
<code>utm_</code> appearing inside an <code>href</code> that points at your own domain. In a browser,
view source and search for <code>utm_</code>; from a terminal, fetch the page and grep for anchors:</p>

<pre><code>curl -s https://example.com/ | grep -o 'href="[^"]*utm_[^"]*"'</code></pre>

<p>Two things to keep straight while you read the output. <strong>A tagged link pointing somewhere
else is not this problem</strong> — tagging outbound links to a partner or to your own campaign
landing pages on another domain is what UTMs are for. And <strong>check the header, footer and any
repeated card component first</strong>, because that is where the whole-site pattern lives; if you
find it there, you have found every page at once.</p>

<p>Whether a parameterised URL is then treated as a duplicate of the clean one is a canonical
question, and not one this survey measured — that is
<a href="/learn/canonical-tags/">canonical tags</a>, and when the signals disagree,
<a href="/how-to/fix-conflicting-canonicals/">fixing conflicting canonicals</a>. Docket runs the
internal-UTM check as part of its tracking lane, alongside the rest of
<a href="/learn/conversion-audit/">the conversion checks</a>; the full catalogue is
<a href="/learn/what-docket-checks/">what Docket checks</a>, and the lane-by-lane walkthrough is
<a href="/learn/seo-audit/">the SEO audit</a>.</p>

<h2>What this page does and does not claim</h2>

<p>Every count above, the sampling frame, the seed, what the check actually treats as an
internal link, and the two things we decline to claim from it are published as
<a href="/data/utm-internal-2026-09.json">utm-internal-2026-09.json</a>. Host names are not in
it, by policy.</p>

<ul>
<li><strong>No consequence was measured.</strong> We counted what the HTML emits. This survey did not
open an analytics account, did not watch a session, and did not observe a single re-attributed visit.
Any sentence you read elsewhere that moves from "this link is tagged" to "you lost this attribution"
has crossed from documentation into assumption, and this page does not cross it.</li>
<li><strong>The sample is small and stated.</strong> {sample} hosts, seed <code>{seed}</code>, crawled
{MEASURED_HUMAN}. Every share above carries its denominator.</li>
<li><strong>Nothing dropped out.</strong> {crawled_ok} of {sample} hosts crawled successfully, so the
denominator is the sample rather than the subset that answered.</li>
<li><strong>The page counts have a ceiling.</strong> At most {cap} pages per host, so {at_cap} hosts
are lower bounds and the affected share of those sites is unknown.</li>
<li><strong>Intent is unread.</strong> A tagged internal link may be deliberate. The check reports it
either way.</li>
<li><strong>The mechanism is not ours.</strong> It is documented and widely explained; our
contribution is the count and the shape.</li>
</ul>

<p><a class="btn" href="/download/">Download Docket</a></p>
"""
    return render(
        cat="learn", slug="internal-utm-links",
        title="How common are internal links with UTM parameters?",
        desc=(f"We crawled {sample} Tranco hosts and counted. {hosts} emitted internal links "
              f"carrying UTM parameters — and the affected hosts split into two different problems."),
        h1="How common are internal links with UTM parameters?",
        crumb='<a href="/">Docket</a> / <a href="/learn/">Learn</a> / Internal UTM links',
        body=body,
        published="2026-09-15",
        faq=[
            ("How many sites put UTM parameters on their own internal links?",
             f"In a random sample of {sample} Tranco hosts crawled on {MEASURED_HUMAN}, {hosts} "
             f"({pct}%) emitted at least one link to their own site carrying UTM parameters, and "
             f"{clean} emitted none. All {crawled_ok} hosts crawled successfully, so that share is "
             f"out of the whole sample rather than out of whoever answered. {sample} hosts is a "
             f"small sample: it supports 'a real minority practice', not a precise rate."),
            ("Is it a few links or the whole site?",
             f"Both, and that is the finding. Among the {hosts} affected hosts the counts sit at two "
             f"ends with nothing between: {isolated} had such links on {ISOLATED_MAX_HUMAN} pages or "
             f"fewer, and the rest had them on nearly or exactly every page crawled — though {hosts} "
             f"hosts is too few to call that a distribution shape rather than chance. A handful of "
             f"pages is usually "
             f"hand-pasted links; every page is a template emitting the parameter on every render, "
             f"which is one fix rather than many. Across affected hosts there were {links_total} "
             f"such links in total, median {links_median} per host, maximum {links_max}."),
            ("Does a host showing the maximum page count mean the site has that many pages?",
             f"No, and this is the easiest number on the page to misread. We crawled at most {cap} "
             f"pages per host, so the page count cannot exceed {cap}. A host showing {cap} means "
             f"every page we looked at carried such a link — the true number is however many pages "
             f"that site has. {at_cap} of the {hosts} affected hosts sit at that ceiling, and the "
             f"share of those sites affected is unmeasured."),
            ("Did you measure the damage to analytics attribution?",
             f"No. The survey counted what {sample} hosts emit in their HTML. It did not observe a "
             f"single session, a single re-attribution, or a single lost conversion. What an "
             f"analytics tool does with a tagged internal link is documented behaviour, not "
             f"something this survey measured, and the mechanism is explained on the marketing tag "
             f"audit page rather than here."),
            ("Is tagging an internal link always a mistake?",
             f"No. Some teams tag a specific internal link on purpose — an on-site banner, say — "
             f"and accept the attribution cost to get the click count. That is a decision. Nothing "
             f"in a crawl distinguishes it from a pasted URL, so the check reports the links and "
             f"does not read intent; across {sample} hosts we can say how often it appears and in "
             f"what shape, and nothing about why."),
        ],
    )


BUILDERS = [internal_utm]


def build_all() -> list[Path]:
    return [b() for b in BUILDERS]


if __name__ == "__main__":
    for p in build_all():
        print(p)
