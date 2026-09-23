#!/usr/bin/env python3
"""How many sites actually disallow Googlebot in robots.txt?

⚠️ WHY THIS PAGE EXISTS. Page one for "how many websites accidentally block
Googlebot in robots.txt", checked 2026-09-15 before a word was written, is
malcare.com, embarque.io, feedthebot.org, blog.photobiz.com, onely.com,
rankmath.com and wp-firewall.com — the seven recorded in `PAGE_ONE` below.
There is **no Google documentation on page one**. Every result is a "how to fix
Blocked by robots.txt in Search Console" tutorial, and **not one of them answers
the prevalence question**. No competitor study of any size was found on it. The
genre assumes the problem is common and never measures it; this page measures
it, which is the entire reason it can win the query.

**Original measurement:** Docket's August 2026 survey of the Tranco top 10,000
robots.txt files, already published as the dataset behind `/index/ai-directives/`
and read here through `facts.py` accessors only.

⚠️ WHAT THIS PAGE MUST NEVER SAY. The page-one genre is about *accidents*. Our
data cannot see an accident. `access` arrives in a raw survey blob whose
collector is NOT in this repository, so the narrow and only supportable reading
is "the file expresses a denial for that token for the path the collector
probed". A site disallowing Googlebot may have meant it exactly. Any sentence of
the form "X% block Googlebot by mistake" would be this page's one fatal claim.

⚠️ NO SIZE STORY IS AVAILABLE HERE. Google documents a robots.txt parse cap, and
the readable maximum does NOT settle whether it bites, because `pop_oversize`
hosts were dropped BEFORE the readable set was formed, on a threshold that is
not in this repository. `facts.pop_oversize()` carries the same warning. The
bucket appears on this page only as excluded population.

**Two gate traps this file is written around.** (a) `verify_numbers.py` reduces a
typed date in prose to a bare year and fails it, so every date is a module
constant and interpolated. (b) `_TRIPLE` only matches an assigned or returned
triple-quoted string, so the FAQ is invisible to the gate — every FAQ entry here
is therefore an f-string with every figure interpolated, by hand rather than by
the gate's insistence.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import facts as F  # noqa: E402
from render import render  # noqa: E402

#: When this query's page one was read, before a word of the page was written.
CHECKED_HUMAN = "15 September 2026"

#: When the survey this page reports was collected. A month typed into prose
#: reduces to a bare year under the derived-number gate and fails the build.
SURVEY_HUMAN = "August 2026"

#: The page-one results recorded before writing, so the count in the prose is
#: derived from the list rather than remembered. Named here and never rendered:
#: the site names no third-party website in published prose.
PAGE_ONE = ("malcare.com", "embarque.io", "feedthebot.org", "blog.photobiz.com",
            "onely.com", "rankmath.com", "wp-firewall.com")

#: Google's documented robots.txt parse cap, in KiB. Verified at source on
#: 2026-09-15 at developers.google.com/search/docs/crawling-indexing/robots/
#: robots_txt, which reads: "Google enforces a robots.txt file size limit of
#: 500 kibibytes (KiB)."
#:
#: ⚠️ Quoted ONLY as a documented limit, and that limit is the ONLY size fact
#: this page may state. Nothing here says how many files approach it, exceed it
#: or sit under it: `pop_oversize` hosts were dropped BEFORE the readable set
#: was formed, on a threshold that is not in this repository, so no statistic
#: computed over the files we did read can speak for them. See the docstring.
PARSE_CAP_KIB = 500


def googlebot_robots_blocks() -> Path:
    attempted = F._d()["attempted"]
    readable = F.directives_hosts()
    unreachable = F.pop_unreachable()
    no_robots = F.pop_no_robots()
    oversize = F.pop_oversize()

    gbot = F.blocks_googlebot()
    gother = F.blocks_googleother()
    gbot_pct = round(100 * gbot / readable, 2)
    gother_pct = round(100 * gother / readable, 2)
    gother_ratio = round(gother / gbot, 1)

    # The three shapes a file can take across the two Google tokens. This is the
    # sharpest evidence on the page that they are separate decisions, and it is
    # ONLY evidence about what files express — see the docstring. The asymmetry
    # carries the argument; the reverse case is small and is not characterised.
    both_google = F.blocks_both_google()
    gother_only = F.blocks_googleother_only()
    gbot_only = F.blocks_googlebot_only()
    only_ratio = round(gother_only / gbot_only, 1)

    blocks_any = F._d()["blocks_any"]
    blocks_citation = F._d()["blocks_citation"]
    any_pct = round(100 * blocks_any / readable, 1)
    citation_pct = round(100 * blocks_citation / readable, 1)
    ai_tokens = len(F.CITATION) + len(F.TRAINING)
    ai_multiple = round(blocks_any / gbot, 1)

    #: "Roughly one file in N". Derived rather than written as a word: the
    #: derived-number gate matches digits, so "one in fifty" would walk straight
    #: past it and go stale beside the percentage it is restating.
    one_in = round(readable / gbot)

    readable_pct = round(100 * readable / attempted, 1)
    unreachable_pct = round(100 * unreachable / attempted, 1)
    no_robots_pct = round(100 * no_robots / attempted, 1)
    oversize_pct = round(100 * oversize / attempted, 1)

    body = f"""
<div class="callout">
<div class="callout-title">Quick answer</div>
<p><strong>Rarer than the tutorials assume.</strong> In Docket's {SURVEY_HUMAN} survey of the Tranco
top {attempted:,}, <strong>{gbot:,} of the {readable:,} readable robots.txt files
({gbot_pct}%) express a denial for <code>Googlebot</code></strong>. Every share on this page is a
share of those {readable:,} readable files, not of the {attempted:,} hosts we asked — the rest of
the population is in the table below, and it is large.</p>
<p><strong><code>GoogleOther</code> is the bigger number:</strong> {gother:,} files ({gother_pct}%)
deny it, about {gother_ratio} times as many. That is a different decision, and a more defensible one.</p>
<p><strong>What this does not say.</strong> A robots.txt file records what it expresses, not what
anyone intended. We cannot tell a mistake from a deliberate policy, and this page does not pretend to.</p>
</div>

<h2>Page one answers a different question than the one people ask</h2>

<p>The query that led here — some version of "how many websites accidentally block Googlebot" — has
a page one made entirely of repair manuals. Reading it on {CHECKED_HUMAN} turned up
{len(PAGE_ONE)} of them — tutorials on clearing "Blocked by robots.txt" out of Search Console — and
nothing from Google at all. Every one is useful if you already know you have the problem.</p>

<p>Not one of them says how common the problem is. The genre takes the prevalence for granted: it is
the premise that makes the tutorial worth writing, and it is never measured. That gap is what this
page fills, and the answer turns out to cut against the premise.</p>

<h2>What we measured, and what a share here is a share of</h2>

<p>The survey asked the Tranco top {attempted:,} hosts for <code>/robots.txt</code> in
{SURVEY_HUMAN} and recorded, per host, whether the file expressed a denial for each of a list of
named crawler tokens. Most of that list is AI crawlers; <code>Googlebot</code> and
<code>GoogleOther</code> are in it too, which is why this question can be answered at all.</p>

<p><strong>The population is the first finding, and it belongs before the headline rather than in a
footnote.</strong> Only about {readable_pct}% of the hosts we asked produced a robots.txt this
survey could read and parse. The rest split three ways:</p>

<table>
<thead><tr><th>Outcome</th><th>Hosts</th><th>Share of hosts attempted</th></tr></thead>
<tbody>
<tr><td>Readable, parseable robots.txt — <strong>the denominator for every percentage below</strong></td><td>{readable:,}</td><td>{readable_pct}%</td></tr>
<tr><td>Unreachable: no answer, or an answer we could not use</td><td>{unreachable:,}</td><td>{unreachable_pct}%</td></tr>
<tr><td>Reachable, but serving no robots.txt at all</td><td>{no_robots:,}</td><td>{no_robots_pct}%</td></tr>
<tr><td>Excluded as oversize before the readable set was formed</td><td>{oversize:,}</td><td>{oversize_pct}%</td></tr>
<tr><td><strong>Attempted</strong></td><td><strong>{attempted:,}</strong></td><td><strong>&mdash;</strong></td></tr>
</tbody>
</table>

<p>Those {unreachable:,} unreachable hosts are not evidence of anything about robots.txt. They are
hosts that did not answer us, and a survey that quietly folded them into a denominator would be
reporting its own reach as a property of the web. The {no_robots:,} with no file at all are a real
state and a permissive one — absent robots.txt means nothing is disallowed — but they express no
directive, so they cannot be counted among files that do.</p>

<p><strong>Which means the readable set is not a random sample of the top {attempted:,}.</strong>
Some of the hosts that refused our fetch refused it because they refuse automated fetches generally,
and a host with that posture is not obviously less likely to disallow a crawler by name. So the rate
below is a rate among files we could read, and the rate across the whole list could sit above it. We
have no way to measure the difference, which is a reason to quote the figure with its denominator
attached every time rather than a reason to quietly widen it.</p>

<p><strong>The oversize bucket is excluded and stays excluded.</strong> Google documents a
{PARSE_CAP_KIB} KiB parse cap on robots.txt, and it is tempting to use a survey like this one to say
how often real files approach it. We cannot. Those hosts were dropped before the readable set was
formed, on a size threshold that is not in our repository, so nothing measured over the files we did
read can speak for them. They are in the table because leaving them out would make the other rows
add up wrongly, and for no other reason.</p>

<h2>The headline, stated as narrowly as the data supports</h2>

<p>Of the {readable:,} readable files, <strong>{gbot:,} express a denial for
<code>Googlebot</code></strong> — {gbot_pct}%. Roughly one file in {one_in}, in the most visible slice
of the web there is.</p>

<p>Read that sentence literally, because it is written literally. It says the file expresses a
denial. It does not say the site meant to be invisible in Google, and it does not say the site made
a mistake. Those are claims about intent, and nothing in a robots.txt file carries intent. A
publisher fencing off a staging host, a service that genuinely does not want indexing, and an
engineer who shipped a <code>Disallow</code> line from a development environment all produce exactly
the same bytes. We can count the bytes. We cannot read the room.</p>

<p>Against that, the same files are far more willing to refuse an AI crawler: {blocks_any:,} of them
({any_pct}%) deny at least one of the {ai_tokens} AI crawlers this survey tracks, and
{blocks_citation:,} ({citation_pct}%) deny at least one of the crawlers that decide whether a site
can be cited in an AI answer. Blocking an AI crawler is roughly {ai_multiple} times as common as
expressing a denial for Googlebot.</p>

<p><strong>One honest deflation of that comparison.</strong> The AI figure counts a host that denies
any one of {ai_tokens} tokens; the Googlebot figure counts one token. A count of "any of several"
will beat a count of "this one" even if no site cared more about the category — some of the gap is
arithmetic rather than sentiment. The direction survives the caveat, and the size of it should be
read loosely. The full breakdown by token is on the <a href="/index/ai-directives/">AI directives
survey</a>, and the smaller hand-checked sample behind it is <a href="/index/">the Docket Index</a>.</p>

<h2>GoogleOther is the sharper half of this</h2>

<p><code>GoogleOther</code> is Google's general-purpose fetcher: the crawler used for product and
research work other than building the Search index. It shares Googlebot's infrastructure and obeys
its own token in robots.txt. Denying it does not remove a site from Search.</p>

<p>More files deny it than deny <code>Googlebot</code> — {gother:,} against {gbot:,}, about
{gother_ratio} times as many. We cannot show why, and will not guess — but the two tokens are
genuinely different decisions, and the cost of getting them confused is asymmetric:</p>

<table>
<thead><tr><th>Token</th><th>What it fetches for</th><th>What denying it costs</th></tr></thead>
<tbody>
<tr><td><code>Googlebot</code></td><td>The Search index</td><td>Pages stop being fetched for Search. This is the expensive one.</td></tr>
<tr><td><code>GoogleOther</code></td><td>Google product and research work other than the Search index</td><td>Those non-Search uses stop. Search is unaffected.</td></tr>
</tbody>
</table>

<p>Sorting the readable files by which of the two tokens they deny leaves three shapes, and the way
they are sized is the most useful thing on this page:</p>

<table>
<thead><tr><th>Shape</th><th>Files</th><th>What the file expresses</th></tr></thead>
<tbody>
<tr><td>Both tokens denied</td><td>{both_google:,}</td><td>The commonest shape, and most files denying <code>Googlebot</code> are in it — the two often move together.</td></tr>
<tr><td><code>GoogleOther</code> denied, <code>Googlebot</code> allowed</td><td>{gother_only:,}</td><td>Non-Search fetching refused while Search fetching is permitted. The two tokens pulled apart — and the commoner way of pulling them apart, by a factor of about {only_ratio}.</td></tr>
<tr><td><code>Googlebot</code> denied, <code>GoogleOther</code> allowed</td><td>{gbot_only:,}</td><td>The rarest of the three shapes by a wide margin.</td></tr>
</tbody>
</table>

<p><strong>The asymmetry is what carries the argument.</strong> If "Google" were being treated as one
undifferentiated switch, almost everything would sit in the top row and both of the other two would
be marginal. One of them is not marginal at all. Files pull the two tokens apart routinely, and they
pull them apart overwhelmingly in the direction that leaves Search fetching intact.</p>

<p>What we are <em>not</em> going to do is tell you the {gother_only:,} files in the middle row made
a considered choice, or that the {gbot_only:,} in the bottom row made a mistake. We cannot see
either. A file denying <code>Googlebot</code> while allowing <code>GoogleOther</code> is simply the
rarest of the three shapes, and some of those files may mean exactly what they say. The usable
conclusion is narrower and holds regardless: these are two tokens, they are moved independently
across this population, and a site treating them as one switch is expressing something it may not
mean. If your file carries one of these lines and not the other, that is worth a deliberate look
rather than a copy-paste.</p>

<h2>What we tried to tell you about the blockers, and could not</h2>

<p>The obvious follow-up is: what kind of site does this? We tried. A hostname-pattern pass over the
blockers placed a handful of them as content delivery or advertising infrastructure — hosts where a
blanket denial is unremarkable — and left the large majority unclassified. A handful out of a
population this size supports no characterisation at all.</p>

<p>So the honest answer is that we do not know what kind of site typically expresses a denial for
Googlebot, and we are not going to gesture at one. If somebody tells you it is mostly small business
sites, or mostly WordPress, or mostly staging environments that leaked, ask what they counted.</p>

<h2>What "Blocked by robots.txt" in Search Console actually means</h2>

<p>The report the tutorials are written about says something narrow: Google wanted to fetch a URL,
consulted your robots.txt, and your file said no. It is a statement about fetching. It is not a
statement about whether the URL is in the index, and that trips people up constantly.</p>

<ul>
<li><strong>robots.txt governs fetching, not indexing.</strong> A disallowed URL can still be listed
in search results from other signals — links to it, for instance — typically with no description,
because the page was never read. If your goal is that a page not appear, robots.txt is the wrong
instrument, and the tag side of that argument is
<a href="/learn/does-noindex-stop-ai-crawlers/">whether noindex stops a crawler</a>.</li>
<li><strong>robots.txt binds only crawlers that read it and comply.</strong> It is a published
request, honoured by the crawlers that choose to honour it. A denial is not a lock.</li>
<li><strong>Allowing a crawler in the file does not mean your server will serve it.</strong> A CDN
rule, a bot-protection product or a rate limiter can refuse a request that robots.txt permits, and
nothing in the file will show it. If that is your situation, the diagnosis is on
<a href="/how-to/fix-ai-crawler-access/">fixing AI crawler access</a>, and the evidence lives in your
own logs — <a href="/learn/log-file-analysis/">log file analysis</a> is how you find out who actually
fetched what.</li>
</ul>

<h2>How to check your own file</h2>

<p>This takes about a minute and does not need a tool.</p>

<ol>
<li><strong>Read the file yourself</strong> at <code>/robots.txt</code> on the exact host and scheme
you care about. A robots.txt applies to the host that served it, so the answer for
<code>www</code> is not automatically the answer for the bare domain, and staging hosts have their
own file.</li>
<li><strong>Find every group heading</strong>, not just the first. Look for
<code>User-agent: Googlebot</code>, <code>User-agent: GoogleOther</code> and
<code>User-agent: *</code> separately, and read the <code>Disallow</code> lines under each. A
crawler obeys the most specific group that names it and ignores the rest, so a permissive
<code>*</code> group does not soften a restrictive <code>Googlebot</code> group.</li>
<li><strong>Check the two Google tokens as two decisions.</strong> They are not interchangeable and
a rule under one says nothing about the other.</li>
<li><strong>Confirm it in Search Console</strong> rather than trusting your reading of the file.
Google's own tooling reports what Google's parser concluded, which is the only interpretation that
matters for Search.</li>
<li><strong>Check that the server agrees with the file.</strong> A permissive robots.txt in front of
an edge that returns a refusal is the failure mode nothing in the file can reveal.</li>
</ol>

<p>Docket reads robots.txt as part of an audit, reports which named crawlers your file denies, and
separately asks your server whether it will actually serve a request — the two halves that this page
keeps insisting are different questions. The full list of what it inspects is on
<a href="/learn/what-docket-checks/">what Docket checks</a>, and the sitemap side of robots.txt, which
is a non-group record with rules of its own, is covered in
<a href="/learn/ai-crawlers-and-sitemaps/">AI crawlers and sitemaps</a>.</p>

<h2>What to take from this</h2>

<p>If you arrived worried, the base rate is reassuring: {gbot_pct}% of readable files in the top
{attempted:,} express a denial for <code>Googlebot</code>, so the ambient assumption that this is
everywhere is not supported by the most visible slice of the web. That is not permission to skip the
check on your own site — a base rate of one in {one_in} is exactly the sort of number that is
comforting in aggregate and catastrophic in your particular case.</p>

<p>And if you find such a line, resist the urge to classify it as an accident before you have asked
whoever wrote it. We could not make that call from the outside on {gbot:,} sites, and neither can a
tutorial that never counted them.</p>

<p><a class="btn" href="/download/">Download Docket</a></p>
"""
    # Further reading: pages Google had not yet discovered on 2026-09-22 (URL
    # Inspection: "unknown to Google"), linked from this page because Google
    # recrawls it often and last crawled the hubs that list them in August.
    # Chosen by topic; each such page is linked from exactly one article.
    body += """
<h2>Further reading</h2>
<ul>
<li><a href="/how-to/sitemap-urls-that-are-not-stale/">When 'regenerate your sitemap' is wrong</a></li>
<li><a href="/how-to/fix-paginated-pages-that-canonicalise-to-page-1/">Pagination: the canonical mistake that hides pages</a></li>
<li><a href="/learn/url-structure/">SEO URL structure best practice, minus the folklore</a></li>
<li><a href="/learn/what-docket-checks/">Every check Docket runs, by area</a></li>
</ul>
"""
    return render(
        cat="learn", slug="who-blocks-googlebot",
        title="How many sites disallow Googlebot in robots.txt?",
        desc=(f"We read robots.txt for the Tranco top {attempted:,}. Of the readable files, "
              f"{gbot_pct}% deny Googlebot and more deny GoogleOther. What that can, and "
              "cannot, tell you."),
        h1="How many sites actually block Googlebot in robots.txt?",
        crumb='<a href="/">Docket</a> / <a href="/learn/">Learn</a> / Who blocks Googlebot',
        body=body,
        published="2026-09-15",
        faq=[
            ("How many websites block Googlebot in robots.txt?",
             f"In Docket's {SURVEY_HUMAN} survey of the Tranco top {attempted:,}, {gbot:,} of the "
             f"{readable:,} readable robots.txt files expressed a denial for Googlebot — {gbot_pct}%. "
             f"That share is of the readable files only: {unreachable:,} hosts were unreachable, "
             f"{no_robots:,} served no robots.txt at all, and {oversize:,} were excluded as oversize "
             "before the readable set was formed."),
            ("How many of those blocks are accidents?",
             "We cannot tell you, and neither can anyone else working from robots.txt alone. The "
             "file records what it expresses, not what anyone intended: a deliberate policy and a "
             "line shipped from a development environment produce identical bytes. Any figure "
             "presented as a rate of accidental Googlebot blocking is a guess wearing a percentage "
             "sign."),
            ("Is blocking GoogleOther the same as blocking Googlebot?",
             f"No. Googlebot fetches for the Search index; GoogleOther is Google's general-purpose "
             f"fetcher for product and research work other than building that index, and it obeys "
             f"its own token. Denying GoogleOther does not remove a site from Search. More files "
             f"deny it than deny Googlebot — {gother:,} against {gbot:,}, about {gother_ratio} times "
             f"as many. The files also pull the two apart in one direction far more than the other: "
             f"{gother_only:,} deny GoogleOther while allowing Googlebot, against {gbot_only:,} the "
             f"other way round, with {both_google:,} denying both. Which is why treating 'Google' as "
             "one switch is worth a second look."),
            ("Does a Disallow line keep a page out of Google's index?",
             "Not reliably. robots.txt governs fetching, not indexing: a disallowed URL can still be "
             "listed from other signals, usually without a description because the page was never "
             "read. robots.txt also binds only the crawlers that read it and comply, and a file that "
             "allows a crawler says nothing about whether your server will actually serve it."),
            ("Do more sites block AI crawlers than block Googlebot?",
             f"Yes, by a wide margin in this survey: {blocks_any:,} readable files ({any_pct}%) deny "
             f"at least one of the {ai_tokens} AI crawlers tracked, and {blocks_citation:,} "
             f"({citation_pct}%) deny at least one crawler that feeds AI answers, against {gbot:,} "
             f"({gbot_pct}%) for Googlebot. Read the gap loosely: the AI figure counts a denial of "
             "any one of several tokens while the Googlebot figure counts one, so some of the "
             "difference is arithmetic rather than sentiment."),
        ],
    )


BUILDERS = [googlebot_robots_blocks]


def build_all() -> list[Path]:
    return [b() for b in BUILDERS]


if __name__ == "__main__":
    for p in build_all():
        print(p)
