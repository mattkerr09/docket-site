#!/usr/bin/env python3
"""Does noindex stop AI crawlers?

⚠️ WHY THIS PAGE EXISTS AND WHICH PAGES IT MUST NOT BECOME.
`/how-to/fix-ai-crawlers-blocked-by-your-cdn/` diagnoses a 403 you did not
ask for; `/learn/javascript-rendering/` answers whether a crawler that is let
in can read the page. This answers a third question with a definite answer —
whether a tag aimed at indexers has any effect on a crawler's access — and
links to both rather than restating them.

**Page one, checked 2026-09-15 before writing:** datadome.co, dev.to,
dynomapper.com, deepsmith.ai, aischemagen.com, contextbolt.com,
copperanalytics.com, aiboost.co.uk, seo-kreativ.de. All vendor pages and small
blogs; NO OpenAI or Google documentation anywhere on page one, so the query
passes the drop-rule.

**No existing Docket page owns this question.** "noindex" and "AI crawler"
co-occur on several pages — the canonicals article, the comparison pages, the
crawler-directive survey — but in each case the terms meet incidentally inside
a broader argument. Nothing here is a second copy of an existing page's spine.

**Demand, recorded before writing:** Bing exact impressions are recorded for
the 14- and 28-day read and did not gate this decision either way — the point
of recording them is to separate "ranked, nobody wanted it" from "did not
rank", not to decide whether to write. The nine independent sites already
holding page one are demand evidence of their own.

**The original measurement this page rests on** is Docket's August 2026 survey
of the Tranco top 10,000: the edge-refusal figures and the OpenAI crawler
overlap below, both read through facts.py rather than typed.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import facts as F  # noqa: E402
from render import render  # noqa: E402

#: When the survey these figures come from was run. A date in prose is a date
#: that goes stale in one place and stays current in another, so it is stated
#: once and interpolated — the same rule the derived-number gate enforces for
#: figures.
SURVEYED_HUMAN = "August 2026"


def noindex_ai_crawlers() -> Path:
    surveyed = F._d()["attempted"]
    edge_denied = F.directives_edge_denied()
    edge_pct = round(100 * edge_denied / surveyed, 2)
    llms_edge_pct = F._d()["pct_llms_edge_denied"]
    search_blocked = F.oai_search_blocked()
    both = F.oai_search_and_gptbot()
    search_only = F.oai_search_only()
    overlap = F.oai_overlap_pct()
    hosts = F.directives_hosts()
    blocks_training = F._d()["blocks_training"]
    blocks_citation = F._d()["blocks_citation"]

    body = f"""
<div class="callout">
<div class="callout-title">Quick answer</div>
<p><strong>No.</strong> <code>noindex</code> speaks to search <em>indexers</em> about whether a page
may be shown in results. It says nothing about whether the page may be retrieved, and a crawler has
to retrieve the page before it can read the tag at all.</p>
<p><strong>Access is a separate control with separate levers.</strong> Whether an AI crawler gets your
pages is decided by the user-agent tokens in robots.txt — <code>GPTBot</code>, <code>ClaudeBot</code>,
<code>Google-Extended</code> and the rest — and above that by your server or CDN, which can refuse
the request before any file or tag is consulted.</p>
<p><strong>Those two layers disagree more often than anyone expects.</strong> In Docket's
{SURVEYED_HUMAN} survey of the Tranco top {surveyed:,}, <strong>{edge_denied:,} hosts
({edge_pct}%)</strong> turned away a self-identifying bot at the edge, with no tag and no robots rule
involved.</p>
</div>

<h2>What the tag is actually addressed to</h2>

<p>A <code>noindex</code> travels in one of two places: a robots meta element in the HTML, or an
<code>X-Robots-Tag</code> response header. Both of them arrive <em>inside a response</em>. That single
structural fact settles the question. The request was made, the server answered it, the bytes were
transferred, and only then is there a tag for anything to read. Whatever the reader does next, the
copy has already been taken.</p>

<p>For a search engine that honours the directive, what happens next is that the page is withheld from
the results listing. That is a real and useful effect, and it is the effect the tag was designed for.
It is also the wrong tool for the worry that brings most people to this question, which is not "will
this page be listed" but "is this text being ingested".</p>

<p>The interaction runs the other way as well, and it is the reason the two controls should never be
stacked casually. A URL disallowed in robots.txt is not fetched by a compliant crawler, so the
<code>noindex</code> on it is never seen. Blocking access does not deliver a suppression instruction;
it prevents one from being delivered. The directive side of this is
<a href="/how-to/fix-ai-crawler-access/">AI crawler access</a>, and the indexing side sits with
<a href="/learn/canonical-tags/">canonical tags</a>, which are a hint about duplicates rather than a
removal instruction.</p>

<h2>Three controls, three different jobs</h2>

<table>
<thead><tr><th>Control</th><th>Stops indexing</th><th>Stops fetching</th><th>Who has to co-operate</th></tr></thead>
<tbody>
<tr><td><code>noindex</code> (meta robots or <code>X-Robots-Tag</code>)</td>
<td><strong>Yes</strong>, in search engines that honour it</td>
<td><strong>No.</strong> The page is requested and served in full first</td>
<td>The indexer, after it already holds your page</td></tr>
<tr><td><code>Disallow</code> in robots.txt, per user-agent token</td>
<td><strong>Not directly.</strong> A disallowed URL can still be listed from other signals</td>
<td><strong>Yes</strong>, for crawlers that comply</td>
<td>The crawler, voluntarily, before it requests anything</td></tr>
<tr><td>Your server or CDN</td>
<td>Only as a side effect — there is nothing to index</td>
<td><strong>Yes</strong>, for everybody. This is the enforcement layer</td>
<td>Nobody. The refusal is issued, not requested</td></tr>
</tbody>
</table>

<p>Read down the "stops fetching" column and the answer to the page's question falls out. The only row
that governs retrieval by consent is robots.txt; the only row that governs it absolutely is the
server. The tag is in neither position.</p>

<h2>Which crawler you are refusing matters more than whether you refuse</h2>

<p>Docket's reports sort AI crawlers by the job they do rather than lumping them into one category,
because the cost of blocking is wildly different across them. On the OpenAI side,
<code>GPTBot</code> is the training crawler, <code>OAI-SearchBot</code> builds the search index that
decides whether you can be cited, and <code>ChatGPT-User</code> fetches a page live when somebody asks
about it. Refusing the first is an editorial position plenty of publishers hold on purpose. Refusing
the second removes you from answers, which is rarely what anyone sat down intending.</p>

<p>Across the {hosts:,} hosts in the survey with a parseable robots.txt, <strong>{blocks_training:,}
block at least one training crawler</strong> and <strong>{blocks_citation:,} block at least one
citation crawler</strong>. Two checks in the audit cover the two layers separately —
<code>ai.crawler_access</code> reads what the directives say, and <code>ai.edge_access</code> asks the
server what it actually does. Neither of them is a check on your meta tags, because a meta tag is not
where this is decided.</p>

<h2>The measurement: the edge answers first, and it answers alone</h2>

<p>The survey read robots.txt for the Tranco top {surveyed:,} and, separately, put a request to each
server as a bot that said who it was. The gap between those two readings is the finding.
<strong>{edge_denied:,} hosts — {edge_pct}% — returned 401, 403, 406, 429 or 503</strong> to that
request. None of those refusals was produced by a directive or a tag; the connection was closed before
either could matter.</p>

<p>The same pattern shows up one layer further in. Among hosts whose robots.txt <em>explicitly
permitted</em> a fetch of <code>/llms.txt</code>, <strong>{llms_edge_pct}% were refused the file by
the server anyway</strong>. A site can publish a permissive robots.txt, leave every page indexable,
and still be unreachable to the crawlers it meant to welcome. If that is the shape of what you are
seeing, the diagnosis is on
<a href="/how-to/fix-ai-crawlers-blocked-by-your-cdn/">when your CDN blocks AI crawlers your robots.txt
allows</a>, and the platform defaults behind it are on
<a href="/learn/does-cloudflare-block-gptbot/">Cloudflare and GPTBot</a>.</p>

<h2>One switch, two losses</h2>

<p>The sharper result in the survey is about what people intended. Of the <strong>{search_blocked}</strong>
sites refusing <code>OAI-SearchBot</code>, <strong>{both}</strong> refuse <code>GPTBot</code> as well
— <strong>{overlap}%</strong>. Only <strong>{search_only}</strong> sites in the whole sample gave up
search while still permitting training.</p>

<p>An overlap that tight is not the residue of many separate judgements. It is the signature of a
single blanket switch: somebody decided to refuse training, the control they reached for said "AI
bots", and citation went out with it. Nearly nobody chose that trade, and the ones who did are a
rounding error. Separating the decision per crawler is the whole of the fix, and it costs nothing but
attention.</p>

<h2>The limit, stated plainly</h2>

<p>robots.txt has no teeth. It is a published request that well-behaved crawlers choose to honour, and
a crawler that ignores it faces nothing but its own operator's policy. Anything that must be refused
rather than asked has to be refused at the server or the CDN — which is exactly why the edge figure
above is the one worth acting on, and why a robots.txt audit on its own cannot tell you what your site
does.</p>

<p>The honest counterpart is that the edge is blunt. A rule that turns away an unrecognised user-agent
turns away the crawlers you wanted along with the ones you did not, and it leaves no trace in any file
a reader of your site can inspect.</p>

<h2>What to do instead</h2>

<ul>
<li><strong>Stop treating <code>noindex</code> as an access control.</strong> Use it for what it does:
keeping a page out of search results. It is not a consent mechanism and was never offered as one.</li>
<li><strong>Decide per crawler, in robots.txt.</strong> Refusing a training crawler while admitting a
search crawler is a coherent, statable position. A single category toggle cannot express it — and
check the names you write, because more than half the files that write an AI rule at all
<a href="/index/ai-directives/">address a crawler that no longer answers to it</a>.</li>
<li><strong>Test the server, not the file.</strong> Request the same URL twice from one machine — once
as an ordinary browser, once as the crawler — and compare. A browser 200 against a crawler 403 is the
finding, and it is invisible to anything that only reads robots.txt.</li>
<li><strong>Check that a crawler you admit can read what it gets</strong>, which is a separate failure
again — see <a href="/learn/javascript-rendering/">JavaScript rendering</a> and
<a href="/learn/ai-search-visibility/">AI search visibility</a>.</li>
<li><strong>Look at your own site the way an assistant does</strong>, rather than the way your CMS
does: <a href="/how-to/audit-your-site-from-an-ai-assistant/">audit your site from an AI
assistant</a>.</li>
</ul>

<p><a class="btn" href="/download/">Download Docket</a></p>
"""
    return render(
        cat="learn", slug="does-noindex-stop-ai-crawlers",
        title="noindex does not stop AI crawlers – robots.txt does",
        desc=("noindex tells indexers not to list a page; it cannot stop a crawler fetching it. "
              "What robots.txt and your server control instead, and which layer is refusing yours."),
        h1="Does noindex stop AI crawlers?",
        crumb='<a href="/">Docket</a> / <a href="/learn/">Learn</a> / noindex and AI crawlers',
        body=body,
        published="2026-09-15",
        faq=[
            ("Does noindex stop AI crawlers?",
             "No. A noindex directive is carried inside the response — either as a robots meta "
             "element or an X-Robots-Tag header — so the crawler has already requested and "
             "received the page by the time it can read the tag. noindex governs whether a search "
             "engine shows the page in results, not whether anything may fetch it."),
            ("What does stop an AI crawler, then?",
             "Two layers. A Disallow rule in robots.txt against that crawler's user-agent token "
             "stops crawlers that choose to comply, before they request anything. Your server or "
             "CDN stops everything, because the refusal is issued rather than requested. robots.txt "
             "is a published request; the server is the only enforcement."),
            ("If I block a crawler in robots.txt, will it still see my noindex?",
             "No, and that is the trap in stacking the two. A compliant crawler does not fetch a "
             "disallowed URL, so it never reads the noindex on it. Blocking access prevents a "
             "suppression instruction from being delivered rather than delivering one."),
            ("Does blocking GPTBot keep me out of AI answers?",
             "Not by itself. GPTBot is the training crawler; OAI-SearchBot builds the search index "
             "that decides whether you can be cited, and ChatGPT-User fetches a page live when "
             "somebody asks about it. Refusing training while admitting search is a coherent "
             f"position, though the survey suggests it is rarely the one taken: of {search_blocked} "
             f"sites refusing OAI-SearchBot, {both} ({overlap}%) refuse GPTBot too, and only "
             f"{search_only} gave up search while permitting training."),
            ("My robots.txt allows AI crawlers. Is that the whole answer?",
             f"No. In Docket's {SURVEYED_HUMAN} survey of the Tranco top {surveyed:,}, "
             f"{edge_denied:,} hosts ({edge_pct}%) refused a self-identifying bot outright — 401, "
             f"403, 406, 429 or 503 — before any robots rule could apply, and {llms_edge_pct}% of "
             "hosts whose robots.txt explicitly permitted a fetch of /llms.txt were then denied it "
             "by the server. Test the server, not the file."),
        ],
    )


BUILDERS = [noindex_ai_crawlers]


def build_all() -> list[Path]:
    return [b() for b in BUILDERS]


if __name__ == "__main__":
    for p in build_all():
        print(p)
