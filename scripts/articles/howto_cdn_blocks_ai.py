#!/usr/bin/env python3
"""AI crawlers refused by the CDN, not by robots.txt.

⚠️ THE UNMEASURED PAGE OF THE 2026-09 BATCH. No query in the recorded demand
list asked for this. It is written from a real capability
(`ai.blocked_at_the_edge`) and a real measurement, and it carries a falsifier:
zero impressions 28 days after going live means it was written from a capability
we have rather than a question anyone asked. Recorded in
ops/search/docket-batch-2026-09-baselines.json BEFORE the page was written.

⚠️ THE SITE IT WAS MEASURED ON IS NOT NAMED, and will not be. Publishing a named
company's defect to sell a tool is not a trade this project makes.

Distinct from /how-to/fix-ai-crawler-access/, which covers robots.txt and never
mentions a CDN, a WAF or a 403.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from render import render  # noqa: E402


def cdn_blocks_ai_crawlers() -> Path:
    body = """
<p class="lede">Your robots.txt can welcome every AI crawler in the world and your server can
still refuse them at the door. The refusal happens before robots.txt is ever read, it produces
no entry in any SEO tool's report, and the only way to find it is to ask your own server the
same question twice.</p>

<h2>Why robots.txt cannot tell you</h2>

<p>robots.txt is a file a crawler fetches and chooses to obey. A bot rule at your CDN is a
decision made about the request itself — before anything is served, before the crawler has read
a word of your policy. The two live in different places and cannot see each other.</p>

<p>So a site can publish a robots.txt that explicitly allows GPTBot and ClaudeBot, mean it
sincerely, and return <code>403</code> to both. Nothing in the robots.txt file is wrong.
Nothing in any report that reads robots.txt will say otherwise.</p>

<p>The usual cause is not malice or even a decision: managed bot protection ships with a
known-good list, anything not on it gets challenged or blocked, and the AI crawlers are newer
than most of those lists. Cloudflare, Fastly and AWS WAF all expose this as a per-user-agent
rule, and the default posture on several of them has moved toward blocking AI crawlers unless
you say otherwise.</p>

<h2>The test, and the trap inside it</h2>

<p>Send your homepage two requests and compare.</p>

<pre><code>curl -sS -D - -o /dev/null \\
  -A "Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko); compatible; GPTBot/1.1; +https://openai.com/gptbot" \\
  https://example.com/ | head -1

curl -sS -D - -o /dev/null \\
  -A "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36" \\
  https://example.com/ | head -1</code></pre>

<p><strong>Use a GET, not a HEAD.</strong> <code>-D - -o /dev/null</code> makes a real request
and throws the body away. <code>curl -I</code> looks like the tidier way to ask for a status
code and is the wrong tool here: measured on the same site on the same day, the blocked crawler
got <code>403</code> on a GET and <code>200</code> on a HEAD, from the same machine a second
apart. Bot rules are commonly scoped to the requests that actually serve content, so a HEAD can
sail through a rule that stops every real visit. Check with the method a crawler uses.</p>

<p><strong>The trap: a single 403 proves nothing.</strong> The same bot protection usually
refuses <code>curl</code> whatever user-agent it sends. If you run only the first command, see
403 and conclude the crawler is blocked, you may simply have discovered that your CDN dislikes
command-line tools.</p>

<p><strong>Both requests, from the same machine, in the same minute.</strong> That is what makes
it evidence:</p>

<ul>
<li><strong>Browser 200, crawler 403</strong> — the rule is about the crawler. This is the
finding.</li>
<li><strong>Both 403</strong> — your protection is blocking the tool, not the crawler. The
answer has to come from your CDN's own logs; this test cannot reach it.</li>
<li><strong>Both 200</strong> — nothing to fix, and worth knowing rather than assuming.</li>
</ul>

<p>Measured this way on one large developer platform in September 2026: a browser and an
ordinary crawler both received 200, while <strong>seven AI crawlers received 403</strong> —
OAI-SearchBot, GPTBot, ChatGPT-User, PerplexityBot, Perplexity-User, ClaudeBot and
Claude-SearchBot. Its robots.txt allowed every one of them, with a single
<code>User-agent: *</code> group disallowing only a search path and an API path. Re-tested
minutes later from the same address, so it was user-agent based rather than rate limiting. The
site is not named here; the shape is the point.</p>

<h2>Which refusals actually cost you</h2>

<p>Not all of these bots do the same job, and a block does not cost the same thing in each
case.</p>

<ul>
<li><strong>Search and live-fetch crawlers</strong> — OAI-SearchBot, ChatGPT-User,
PerplexityBot, Perplexity-User, Claude-SearchBot, Claude-User. These decide whether you can be
cited in an answer at all. Blocking them is a visibility loss, and it is the one that hurts.</li>
<li><strong>Training crawlers</strong> — GPTBot, ClaudeBot and their equivalents. Whether to
allow these is a real editorial decision with arguments on both sides, and a deliberate block is
a legitimate position rather than a defect.</li>
<li><strong>Everything else</strong> — ad-verification bots and similar visit pages you have
submitted to them and have nothing to do with organic or AI-answer visibility. Blocking them
costs nothing in search.</li>
</ul>

<p>The defect is not "a bot was blocked". It is <strong>a bot being blocked in a way the site
owner did not choose and cannot see</strong>, while their own robots.txt says the opposite.</p>

<h2>Fixing it</h2>

<p>Ask whoever runs your CDN or WAF to allow the specific user-agents you want, as an explicit
rule rather than by relaxing bot protection generally. On Cloudflare, Fastly and AWS WAF this is
a per-user-agent allow. Then <strong>re-run the two-request test</strong> rather than trusting
the change — a rule that was added in the wrong order, or to the wrong hostname, looks identical
to a rule that works until you ask the server.</p>

<p>If the block turns out to be deliberate, write it down somewhere the next person will find
it. Most of the sites in this state are not making a choice; they inherited a default, and the
second most common outcome after fixing it is doing the same work again in a year.</p>

<h2>Where this sits in an audit</h2>

<p>Docket checks this per crawler on your live server, by making the same comparison described
above, and reports it against what your robots.txt claims — which is why it can say "your
robots.txt allows these and your server refuses them" rather than either half alone. The
robots.txt side of the question is <a href="/how-to/fix-ai-crawler-access/">fixing AI crawler
access</a>, and the wider surface is <a href="/learn/ai-search-visibility/">AI search
visibility</a>.</p>

<p>Worth pairing it with one other question, because they compound: a crawler that is let in
still has to be able to read the page. If your content arrives after JavaScript runs, the
crawlers that do not render see an empty page even with a 200 —
<a href="/how-to/javascript-seo-audit/">the JavaScript SEO audit</a> is how you check that, and
a site with both problems is invisible twice over. The full list of what Docket looks at is
<a href="/learn/what-docket-checks/">what Docket checks</a>, inside
<a href="/learn/seo-audit/">the technical audit</a>.</p>

<p><a class="btn" href="/download/">Download Docket</a></p>
"""
    return render(
        cat="how-to", slug="fix-ai-crawlers-blocked-by-your-cdn",
        title="AI crawlers getting 403 when robots.txt allows them",
        desc=("Your CDN can refuse GPTBot and ClaudeBot before robots.txt is ever read. The "
              "two-request test that proves it, and the trap that makes one request useless."),
        h1="When your CDN blocks AI crawlers your robots.txt allows",
        crumb='<a href="/">Docket</a> / <a href="/how-to/">Fix it</a> / CDN blocking AI crawlers',
        body=body,
        published="2026-09-14",
        faq=[
            ("Why is GPTBot getting a 403 when my robots.txt allows it?",
             "Because robots.txt and your CDN's bot rules are different systems that cannot see "
             "each other. robots.txt is a file a crawler fetches and obeys; a CDN bot rule is a "
             "decision about the request, made before anything is served. Managed bot "
             "protection ships with a known-good list, and AI crawlers are newer than most of "
             "those lists."),
            ("How do I check whether my CDN is blocking an AI crawler?",
             "Request the same URL twice from the same machine — once with the crawler's "
             "user-agent, once with an ordinary browser's — and compare the status codes. "
             "Browser 200 with crawler 403 is the finding. Both 403 means your protection is "
             "refusing the tool rather than the crawler, and the answer has to come from your "
             "CDN's logs."),
            ("Does a 403 from curl prove the crawler is blocked?",
             "No, and this is the most common mistake in checking it. Bot protection usually "
             "refuses curl whatever user-agent it sends, so a single 403 may only tell you that "
             "your CDN dislikes command-line tools. The comparison is the evidence, not the "
             "status code on its own."),
            ("Is blocking AI crawlers always a mistake?",
             "No. Blocking training crawlers is a legitimate editorial decision. The defect is "
             "blocking search and live-fetch crawlers — the ones that decide whether you can be "
             "cited in an answer — without choosing to, while your robots.txt says the "
             "opposite."),
            ("Will an SEO tool that reads robots.txt find this?",
             "No. Nothing in the robots.txt file is wrong, so nothing that reads it will "
             "report anything. Finding it requires asking your own server as each crawler and "
             "comparing the answer to an ordinary request."),
        ],
    )


BUILDERS = [cdn_blocks_ai_crawlers]


def build_all() -> list[Path]:
    return [b() for b in BUILDERS]


if __name__ == "__main__":
    for p in build_all():
        print(p)
