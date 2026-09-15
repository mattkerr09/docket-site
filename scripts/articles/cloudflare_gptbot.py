#!/usr/bin/env python3
"""Does Cloudflare block GPTBot by default?

⚠️ WHY THIS PAGE EXISTS AND WHY IT IS NOT THE CDN HOW-TO. `/how-to/fix-ai-crawlers-blocked-by-your-cdn/`
answers "mine is returning 403, how do I fix it". This answers a different
question with a definite answer — "is it on by default, for which crawler, on
which pages" — and the two link to each other rather than repeating.

**Page one, checked 2026-09-15 before writing:** six small and vendor blogs, no
Cloudflare documentation, so the query passes the winnability rule. Every one of
them gives the flat answer "Cloudflare blocks AI bots by default". That answer
went stale on 2026-09-15, which is the whole reason this page can win: the
primary source says something more precise than its summaries do.

**Demand, recorded before writing:** Bing exact impressions over 90 days for
"does cloudflare block gptbot" = 0, "cloudflare block ai crawlers" = 0, "allow
gptbot cloudflare" = 0; related with volume "what does cloudflare do" 354,
"block ai" 80. Bing is a few percent of Google and 0 there is not "nobody asks";
six independent sites having written the page is demand evidence of its own.
Recorded so the 14- and 28-day read can separate "ranked, nobody wanted it" from
"did not rank".
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import facts as F  # noqa: E402
from render import render  # noqa: E402

#: When Cloudflare's own pages were read for this article.
CHECKED_HUMAN = "15 September 2026"

#: The two dated policy changes, from Cloudflare's own pages. Single-sourced so a
#: change has to be made once and cannot go stale in one place while staying
#: current in another — the derived-number gate refuses them typed into prose.
ASKED_FROM_HUMAN = "1 July 2025"
DEFAULTS_CHANGED_HUMAN = "15 September 2026"


def cloudflare_gptbot() -> Path:
    surveyed = F._d()["attempted"]
    edge_denied = F.directives_edge_denied()
    edge_pct = round(100 * edge_denied / surveyed, 2)
    search_blocked = F.oai_search_blocked()
    both = F.oai_search_and_gptbot()
    search_only = F.oai_search_only()
    overlap = F.oai_overlap_pct()
    llms_edge_pct = F._d()["pct_llms_edge_denied"]

    body = f"""
<div class="callout">
<div class="callout-title">Quick answer</div>
<p><strong>It depends which OpenAI crawler, and since {DEFAULTS_CHANGED_HUMAN} it also depends on the
page.</strong> Cloudflare asks every new domain at sign-up whether to allow AI crawlers, and from
{DEFAULTS_CHANGED_HUMAN} new domains onboard with bots classified <em>Training</em> or <em>Agent</em>
blocked on pages that display ads, while <em>Search</em> stays allowed.</p>
<p><strong>GPTBot is the training crawler</strong>, so on a new ad-supported Cloudflare domain it is
blocked by default. <strong>OAI-SearchBot is not</strong> — and that is the one that decides whether
you can be cited.</p>
<p><strong>And the setting is not the whole answer.</strong> Your robots.txt can say yes while your
edge says no, and nothing in the file reveals it.</p>
</div>

<h2>The three OpenAI crawlers are not one thing</h2>

<p>Almost every page written about this treats "AI crawler" as a single switch. OpenAI ships three,
and they do different jobs:</p>

<table>
<thead><tr><th>Crawler</th><th>What it is for</th><th>What blocking it costs you</th></tr></thead>
<tbody>
<tr><td><code>GPTBot</code></td><td>Training</td><td>Your content is not used to train the model.
Nothing about search or citation changes.</td></tr>
<tr><td><code>OAI-SearchBot</code></td><td>Search index</td><td><strong>You stop appearing in
ChatGPT's search results.</strong> This is the expensive one.</td></tr>
<tr><td><code>ChatGPT-User</code></td><td>Live fetch</td><td>A page a user asks about cannot be
fetched and read back to them.</td></tr>
</tbody>
</table>

<p>Blocking training is a legitimate editorial decision and plenty of publishers make it on purpose.
Blocking search is almost never what someone meant to do. The question "does Cloudflare block GPTBot
by default" matters mostly because of what the answer implies about the other two.</p>

<h2>What Cloudflare actually does, from Cloudflare's own pages</h2>

<p>Read on {CHECKED_HUMAN}, from the primary sources rather than from the summaries:</p>

<ul>
<li><strong>{ASKED_FROM_HUMAN}</strong> — Cloudflare became the first infrastructure provider to block AI
crawlers by default where there is no permission or compensation, and <strong>every new domain is
asked at sign-up</strong> whether to allow them. The choice is presented; it is not silently made.</li>
<li><strong>{DEFAULTS_CHANGED_HUMAN}</strong> — new domains onboarding get updated defaults: bots classified
<strong>Training or Agent are blocked on pages that display ads</strong>, and <strong>Search remains
allowed</strong>.</li>
</ul>

<p>So the flat sentence "Cloudflare blocks AI bots by default", which is what every result on page one
for this question says today, is no longer the whole answer. The default is now scoped by
<em>classification</em> and by <em>whether the page carries ads</em>. An existing domain is wherever
its owner left it, which is usually wherever the sign-up prompt was answered.</p>

<h2>The measurement: what sites actually do, and the mistake in it</h2>

<p>Docket surveyed the <strong>Tranco top {surveyed:,}</strong> in August 2026 — reading robots.txt,
and separately asking each server. Two findings bear directly on this question.</p>

<p><strong>First, the file is not the answer. {edge_denied:,} hosts ({edge_pct}%) refused a
self-identifying bot outright</strong> — 401, 403, 406, 429 or 503 — before any robots.txt rule could
apply. Of the hosts whose robots.txt explicitly permitted a fetch of <code>/llms.txt</code>,
<strong>{llms_edge_pct}% were then denied it by the server anyway</strong>. A site can allow every AI
crawler in the file and still be invisible to all of them.</p>

<p><strong>Second, and this is the part that should change what you do:</strong> of the
<strong>{search_blocked}</strong> sites blocking <code>OAI-SearchBot</code>,
<strong>{both}</strong> also block <code>GPTBot</code> — <strong>{overlap}%</strong>. Only
<strong>{search_only}</strong> sites in the whole survey blocked search without also blocking
training.</p>

<p>That overlap is the signature of a blanket decision rather than a considered one. Almost nobody
sat down and chose to be absent from ChatGPT's search results while allowing training; they turned
"AI crawlers" off as one switch, and search went with it. A default that distinguishes Training from
Search — which is what Cloudflare now ships — is an improvement precisely because the blanket version
is what people were living with.</p>

<h2>How to find out what your own site does</h2>

<p>The only reliable test is to ask your own server as each crawler and compare the answer to an
ordinary request. Two requests, same machine, seconds apart:</p>

<ul>
<li><strong>Browser 200, crawler 403</strong> — your edge is refusing that crawler. This is the finding.</li>
<li><strong>Both 403</strong> — your protection is refusing the <em>tool</em>, not the crawler, and the
answer has to come from your CDN's logs instead.</li>
<li><strong>Both 200</strong> — nothing is blocking on the user-agent string. Note the limit honestly:
Cloudflare verifies bot identity by IP as well, so this does not prove a verified crawler gets through.</li>
</ul>

<p>Docket does this as part of an audit: it asks your origin once per crawler using each crawler's
documented user-agent, with its own name appended so anyone reading their logs can see who asked, and
compares the status against an ordinary request. Nothing that only reads robots.txt can find this,
because nothing in robots.txt is wrong.</p>

<h2>What to do about it</h2>

<ul>
<li><strong>Decide per crawler, not per category.</strong> Blocking <code>GPTBot</code> and allowing
<code>OAI-SearchBot</code> and <code>ChatGPT-User</code> is a coherent position: no training, still
citable. A single "block AI" toggle does not express it.</li>
<li><strong>Check the edge, not the file.</strong> Your robots.txt is a request. Your server is the
answer, and {edge_pct}% of the top {surveyed:,} sites answer differently from their file.</li>
<li><strong>Re-check after any CDN change.</strong> Managed bot rules ship with lists that update
without you, and AI crawlers are newer than most of those lists.</li>
</ul>

<p>If your crawlers are already getting a 403 while robots.txt allows them, the diagnosis and fix are
on <a href="/how-to/fix-ai-crawlers-blocked-by-your-cdn/">when your CDN blocks AI crawlers your
robots.txt allows</a>. The directive side — which tokens are live, which are retired and which do
nothing — is <a href="/how-to/fix-ai-crawler-access/">AI crawler access</a>. A crawler you let in still has
to be able to read the page, which is <a href="/how-to/javascript-seo-audit/">the JavaScript SEO
audit</a>.</p>

<p><a class="btn" href="/download/">Download Docket</a></p>
"""
    return render(
        cat="learn", slug="does-cloudflare-block-gptbot",
        title="Cloudflare blocks GPTBot on new ad-supported domains — but not OAI-SearchBot",
        desc=("Since 15 September 2026 new Cloudflare domains block Training and Agent bots on "
              "ad pages and allow Search. Which OpenAI crawler is affected, and how to check yours."),
        h1="Does Cloudflare block GPTBot by default?",
        crumb='<a href="/">Docket</a> / <a href="/learn/">Learn</a> / Cloudflare and GPTBot',
        body=body,
        published="2026-09-15",
        faq=[
            ("Does Cloudflare block GPTBot by default?",
             f"On a new domain onboarding from {DEFAULTS_CHANGED_HUMAN}, bots classified Training or Agent "
             "are blocked on pages that display ads, and GPTBot is the training crawler — so yes, "
             "there. Search-classified bots such as OAI-SearchBot stay allowed. Every new domain "
             f"has also been asked the question at sign-up since {ASKED_FROM_HUMAN}, so an existing domain "
             "is wherever its owner left that prompt."),
            ("Does blocking GPTBot stop me appearing in ChatGPT?",
             "No. GPTBot is the training crawler. OAI-SearchBot builds the search index and "
             "ChatGPT-User fetches pages a user asks about. Blocking GPTBot alone keeps your "
             "content out of training while leaving you citable — that is a coherent position, and "
             "a single 'block AI' toggle does not express it."),
            ("My robots.txt allows GPTBot. Does that settle it?",
             f"No. In Docket's August 2026 survey of the Tranco top {surveyed:,}, {edge_pct}% of hosts refused "
             f"a self-identifying bot outright before any robots.txt rule could apply, and {llms_edge_pct}% of "
             "hosts whose robots.txt permitted /llms.txt were then denied it by the server. "
             "robots.txt is a request; the server is the answer."),
            ("How do I check whether my site blocks an AI crawler?",
             "Request the same URL twice from the same machine, once with the crawler's user-agent "
             "and once with an ordinary browser's, and compare. Browser 200 with crawler 403 is the "
             "finding. Both 403 usually means your protection dislikes command-line tools rather "
             "than the crawler. Both 200 means nothing blocks on the user-agent string, though "
             "Cloudflare also verifies bot identity by IP."),
            ("Is blocking AI crawlers a mistake?",
             "Blocking training crawlers is a legitimate editorial choice. Blocking search crawlers "
             f"rarely is, and the survey suggests most people do it without meaning to: of the {search_blocked} "
             f"sites blocking OAI-SearchBot, {both} also block GPTBot, and only {search_only} blocked search "
             "without blocking training. That overlap is the shape of one switch, not a decision."),
        ],
    )


BUILDERS = [cloudflare_gptbot]


def build_all() -> list[Path]:
    return [b() for b in BUILDERS]


if __name__ == "__main__":
    for p in build_all():
        print(p)
