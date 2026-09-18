"""A rate limit is not a block — and the audit often caused it.

Promised on the how-to hub. Sourced from two registered checks in
`backend/seo_engine/checks/ai_visibility.py`: `ai.edge_access`, whose docstring
records a crawl that tripped a site's own rate limit and then reported the
throttle as a property of the site, and `ai.dead_crawler_directive`, whose
docstring records a true observation carrying a false consequence.

⚠️ NO SITE IS NAMED. The deploy's third-party gate refuses pages naming sites
measured without asking, and none of these lessons need a name.

⚠️ The strongest beat is the backwards diagnosis: the tool described its own
request as "a plain browser request", so when a WAF matched the honest suffix
in its user-agent and refused it, the tool blamed the network and told the
reader to change networks. An instrument that misdescribes its own request
will misattribute the response.

Numerals: HTTP status codes only, which `verify_numbers.py` allows as constants
of the protocol. Every other quantity is spelled in words or left out.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from render import render  # noqa: E402


def rate_limits() -> Path:
    body = """
<p class="lede">An audit is traffic. It asks for page after page, faster than a person would,
from one address — which is the exact shape of the thing rate limiting exists to slow down. So
a crawl can trip a limit, and then every measurement it takes afterwards is a measurement of
the limit it tripped. The report that comes out says your server is turning crawlers away.
Nobody is turning anyone away.</p>

<h2>The audit that caused the problem it found</h2>

<p>Docket crawls a batch of pages, then asks for the homepage once more as each AI crawler in
turn to see which of them the edge lets through. On one retailer that sequence was enough: the
crawl consumed the allowance, every crawler probe after it came back HTTP 429, and Docket
reported that the server had refused the audit and that the site's bot protection distrusted
the network it ran from.</p>

<p>A browser from the same machine loaded the page a couple of minutes later, twice, without
complaint. A re-run of the audit passed clean. Nothing about the site had changed in between,
because nothing about the site was ever the problem — <strong>the tool had caused the condition
it was reporting</strong>, and then described it as a property of somebody else's server.</p>

<p>This is the shape to keep: <strong>a measurement that a re-run can change is a measurement
about the run, not about the site.</strong> Before you act on any crawler-access finding, run
it again, slower. If it goes away, it was about you.</p>

<h2>A throttle names a wait; a refusal names a door</h2>

<p>HTTP 429 means too many requests, and HTTP 503 means not right now. Both are temporary and
both are usually <em>correct behaviour</em> by a server that is protecting itself. A 403 is a
different sentence: it says this requester is not allowed, and it will still say that tomorrow
at a slower pace.</p>

<p>The tell that settles it is the <code>Retry-After</code> header. A server that sends one is
naming a time to come back — it is scheduling the crawler, not refusing it. Well-behaved
crawlers honour it and return. A rate limit with a <code>Retry-After</code> is not a visibility
problem at all.</p>

<p>Docket got this wrong for a while and it is worth saying how, because the error is easy to
repeat. On a forum, every AI crawler received 429 with a short <code>Retry-After</code> while a
browser from the same address got 200. Docket called that refusal, rated it critical, and sent
the owner to their CDN to add an allow rule for a WAF block that did not exist. The observation
was right and the diagnosis was wrong, which costs the reader an afternoon and their provider a
support ticket.</p>

<h2>The one-click test that settles a 403</h2>

<p>A genuine 403 has two possible causes and they need opposite fixes: the rule is on
<em>who is asking</em>, or the rule is on <em>where they are asking from</em>. Open the same URL
in your own browser, on your own connection:</p>

<ul>
<li><strong>It loads.</strong> The rule is on the identity. Something in the requester's
user-agent matched a bot signature. The change belongs in your bot protection, not on your
site.</li>
<li><strong>It is refused too.</strong> The rule is on the network or the address, and the
user-agent is irrelevant. That is a different setting entirely.</li>
</ul>

<p>Docket had this backwards, and the reason is worth more than the fix. Its crawler sends a
browser-shaped user-agent with an honest suffix naming the tool and linking to a page about it
— which is precisely the substring a WAF rule matches on. But the check's own text called that
"a plain browser request", so when it was refused it concluded the block could not be about
identity and must therefore be about the network, and it told the reader to try a different
connection. A clean browser string from the same machine got 200 and a full page. The network
had never been involved.</p>

<p><strong>An instrument that misdescribes its own request will misattribute the response.</strong>
When a tool reports a refusal, the first question is what it actually sent.</p>

<h2>A true observation with a false consequence</h2>

<p>The third variant is the hardest to catch, because the fact is correct. Docket flags AI
crawler tokens in <code>robots.txt</code> that no longer belong to any crawler — a retired name
sitting in a file that has not been revisited. On a manufacturer's site it found several, all
genuinely dead, and said those crawlers were therefore reading pages the owner meant to withhold
from them.</p>

<p>They were not. A crawler that matches no group of its own falls back to
<code>User-agent: *</code>, and on that file the wildcard group was the <em>stricter</em> of the
two — it carried every rule the AI group carried, and more. The dead tokens cost nothing but a
crawl-delay. The tokens were dead; the consequence was invented; and the severity of the finding
rested entirely on the consequence.</p>

<p>So when a finding tells you what something <em>costs</em>, check whether the tool measured the
cost or inferred it. Inferring it means modelling the fallback behaviour of whatever reads the
file, and most tools do not.</p>

<h2>When none of this matters</h2>

<p>Said plainly, because the checks above are rated where they are for a reason and not every
one of them is worth your afternoon:</p>

<ul>
<li><strong>A throttle against an aggressive crawler is your rate limiting working.</strong> If a
crawler is taking pages faster than a person could read them and your server slows it down, that
is the system behaving correctly. A commercial crawler that cannot tolerate a
<code>Retry-After</code> is not a crawler you need to accommodate.</li>
<li><strong>A dead token in robots.txt is tidiness, not visibility</strong>, unless the fallback
group is genuinely more permissive than the group the token sat in. Check that before you edit
anything.</li>
<li><strong>A 403 against a tool that names itself may be exactly what you configured.</strong>
Plenty of sites deliberately refuse self-identifying automated readers. If that was the decision,
the finding is a description of your policy rather than a fault in it.</li>
</ul>

<h2>The fixes that make it worse</h2>

<ul>
<li><strong>Turning off bot protection to make a report go green.</strong> The report was
measuring a request that no real crawler makes, at a rate no real crawler uses.</li>
<li><strong>Adding an allow rule at your CDN for a block that does not exist.</strong> This is
what a misdiagnosed 429 leads to. The rule does nothing, and it stays in the configuration for
years as a thing nobody dares remove.</li>
<li><strong>Retrying immediately.</strong> On many edges a burst of retries during a cool-down
extends it, so the second audit looks worse than the first and the picture gets darker each time
you check.</li>
<li><strong>Allowlisting by IP range.</strong> Crawler address ranges move, and an allowlist that
names them is a maintenance promise you did not mean to make. Verify by reverse DNS if you need
to verify at all.</li>
</ul>

<h2>How to make the finding disappear without changing anything</h2>

<p>Worth knowing, because it tells you what the finding is worth. Crawl one page at a time with
a pause between requests and the rate limit never fires, so the crawler probes all return 200
and the report is clean. Nothing about your site is different. The same is true in reverse: crawl
harder and a clean site produces refusals.</p>

<p>Which means <strong>the absence of this finding proves less than its presence</strong>, and
its presence proves less than a second, slower run that reproduces it. Any tool that reports edge
access without telling you how hard it crawled is handing you a number it cannot support.</p>

<h2>Where this sits in an audit</h2>

<p>The two registered checks are <code>ai.edge_access</code>, which tests server access for AI
crawlers, and <code>ai.dead_crawler_directive</code>, which reads retired tokens in
<code>robots.txt</code>. Both live in Docket's AI search visibility area.</p>

<p>Their findings carry different identifiers from the checks that emit them —
<code>ai.throttled_at_the_edge</code> and <code>ai.edge_untestable</code> both come out of
<code>ai.edge_access</code> — which is worth knowing when you search for one and find nothing. A
finding identifier is not a check identifier.</p>

<p>The untestable one is the useful habit here: when a run cannot measure something, the honest
output is a notice saying so, not a pass. <a href="/learn/audit-tool-accuracy/">A gate that
could not measure is not a pass &rarr;</a></p>
"""
    return render(
        cat="how-to", slug="tell-a-rate-limit-from-a-block",
        title="A rate limit is not a block",
        desc=("An audit that crawls your site can trip its own rate limit, then report the "
              "throttle as a fault. How to tell a wait from a refusal."),
        h1="A rate limit is not a block",
        crumb='<a href="/">Docket</a> / <a href="/how-to/">Fix it</a> / Rate limits',
        body=body,
        faq=[
            ("Is HTTP 429 a block?",
             "No. It means too many requests, and it is temporary. A server that sends it with "
             "a Retry-After header is naming a time to come back rather than turning the "
             "crawler away. HTTP 403 is the refusal."),
            ("Why did my audit report crawler blocks that a re-run did not?",
             "Because the first run probably caused them. A crawl is traffic from one address, "
             "which is what rate limiting slows down, so the probes that follow the crawl can "
             "all be measuring the limit the crawl tripped."),
            ("My site returns 403 to an audit tool. Is that a problem?",
             "Only if you did not intend it. Open the same URL in your browser: if it loads, "
             "the rule is on the user-agent and lives in your bot protection; if your browser "
             "is refused too, the rule is on the network."),
            ("Should I remove retired AI crawler names from robots.txt?",
             "It is tidiness rather than visibility, unless the wildcard group those crawlers "
             "fall back to is more permissive than the group the retired name sat in. Compare "
             "the two groups before editing."),
            ("How do I know a crawler-access finding is real?",
             "Run the audit again, more slowly, and see whether it survives. A measurement that "
             "a re-run can change is a measurement about the run rather than about the site."),
        ],
    )


if __name__ == "__main__":
    print(rate_limits())
