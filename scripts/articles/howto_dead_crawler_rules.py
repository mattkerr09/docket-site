"""A dead crawler token is a fact; what it costs is a different question.

Promised on the how-to hub. Sourced from `ai_visibility.py`, registered check
`ai.dead_crawler_directive`:

  * a computer manufacturer's robots.txt named six retired AI crawler tokens,
    all genuinely retired, and the report said at MEDIUM that those crawlers
    were reading the pages it meant to withhold. The file: the catch-all group
    carried seventeen Disallow rules, the AI group carried seven, and EVERY ONE
    of the seven was also in the catch-all. A crawler matching no group falls
    back to `User-agent: *` — which here was STRICTER. Nothing was lost but a
    `Crawl-delay`. THE TOKENS WERE DEAD, THE CONSEQUENCE WAS FALSE, AND THE
    SEVERITY RESTED ON THE CONSEQUENCE.
  * `covered_by_sibling`: a retired name sharing a group with its live
    replacement costs nothing — the live crawler reads that group and gets
    every rule. Untidy, not an exposure.
  * the refusal: the comparison is an EXACT pattern match. A catch-all
    `Disallow: /` really does cover a narrower rule, but proving it needs
    path-matching semantics and a wrong guess would SILENCE A REAL EXPOSURE, so
    it stays reported. The direction to err in follows what being wrong costs —
    which is the opposite of how the same codebase treats recommendations.

⚠️ NO SITE OR VENDOR IS NAMED — third-party gate. The manufacturer, the news
sites and the token owners in the docstrings stay out.

⚠️ THIS TICK ALSO CORRECTS /index/ai-directives/, which published the stale
consequence: "a dead heading above a Disallow means a restriction you wrote is
not in force". True only when the fallback group does not already carry it.

⚠️ The AI-directives survey owns retired-vs-undocumented-vs-parser-truncated
and "robots.txt is not access". This page owns the COST. Cross-linked.

Numerals: none. Quantities spelled as words.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from render import render  # noqa: E402


def dead_crawler_rules() -> Path:
    body = """
<p class="lede">Finding a retired crawler name in your robots.txt is easy, and every tool that
looks will tell you. What that dead line actually costs you is a completely different question,
and the answer is not in the line you are looking at — it is in the group the crawler reads
instead.</p>

<h2>Six dead names, and nothing was getting through</h2>

<p>A computer manufacturer's robots.txt named six retired AI crawler tokens. All six genuinely
retired: the vendors had replaced those names and the crawlers no longer answer to them. We
reported, at medium severity, that those crawlers were reading the pages it meant to withhold
from them.</p>

<p>That was false, and here is the file that made it false. The catch-all group carried seventeen
<code>Disallow</code> rules. The AI group carried seven — <strong>and every one of the seven was
also in the catch-all.</strong></p>

<p>A crawler that matches no group falls back to <code>User-agent: *</code>. So those crawlers fell
back to a <em>stricter</em> group than the one written for them, and lost no coverage whatsoever.
The only directive that actually went unheard was a <code>Crawl-delay</code>.</p>

<p><strong>The tokens were dead, the consequence was false, and the severity rested entirely on
the consequence.</strong></p>

<h2>A rule's effect belongs to the group, not to the token</h2>

<p>This is the part worth taking away, and it applies to every robots.txt question, not only to AI
crawlers.</p>

<p>Writing a <code>User-agent</code> line does not create protection. It creates a <em>group</em>,
and it removes that crawler from the fallback. So when the heading is a name nothing answers to,
the crawler simply reads the catch-all, and three things can happen:</p>

<table>
<tr><th>The catch-all group is…</th><th>What the dead name cost you</th></tr>
<tr><td>Stricter than the group you wrote</td><td>Nothing. The crawler is more restricted, not less.</td></tr>
<tr><td>Carrying the same rules</td><td>Nothing that matters. The lines are inert but the policy holds.</td></tr>
<tr><td>Looser, or missing rules the dead group had</td><td>This is the real exposure — and the only case worth a severity.</td></tr>
</table>

<p>Nothing about the dead line tells you which of those you are in. <strong>The question is never
"is this token current?" — it is "what does this crawler get instead?"</strong></p>

<h2>Sometimes the replacement is already sitting next to it</h2>

<p>A group can be headed by several <code>User-agent</code> lines, and its rules apply to all of
them. So a retired name stacked in the same group as its live replacement costs nothing at all:
the live crawler reads that group and receives every rule in it.</p>

<p>That is worth knowing before you go tidying. On one site with four dead names, exactly one of
them was actually uncovered — the other three sat beside live replacements or above rules the
catch-all already carried. A finding that said four would have been four times the alarm and three
times the wasted work.</p>

<h2>Which way to be wrong</h2>

<p>The comparison between the two groups is an exact match on the rule patterns, and that is
deliberately crude. A catch-all group saying <code>Disallow: /</code> genuinely does cover a
narrower rule written under a dead name — but proving that in general needs full path-matching, and
a wrong answer would quietly <em>silence a real exposure</em>. So that case stays reported.</p>

<p><strong>The direction you err in should follow what being wrong costs.</strong> A false alarm
here costs somebody an afternoon reading their own robots.txt. A missed one costs the thing they
were trying to protect. Those are not symmetric, so the rule is not symmetric.</p>

<p>Which is the opposite of how the same codebase treats
<a href="/how-to/schema-type-is-a-claim/">what it recommends you publish &rarr;</a>, where a
confident wrong guess ends up in your markup as a claim you made. Same product, two rules, because
the cost of being wrong points in two different directions.</p>

<h2>Checking your own file</h2>

<ol>
<li><strong>List every <code>User-agent</code> line naming an AI product</strong>, and check each
token against that vendor's own crawler documentation rather than a blog post.</li>
<li><strong>Then do the step almost nobody does: compare that group's rules against the catch-all
group's.</strong> If every rule in the AI group also appears under <code>*</code>, a dead name
there has cost you nothing.</li>
<li><strong>Look for a live replacement in the same group.</strong> If it is there, the dead line
beside it is untidy and harmless.</li>
<li><strong>Test from outside the file.</strong> Fetch a page you meant to withhold using the
crawler's user-agent string and see what the server actually does.</li>
</ol>

<h2>When a dead token really is an exposure</h2>

<p>Keep the severity where the harm is. If your AI group disallows paths that the catch-all group
does not — a members' area, a search endpoint, anything you separated out precisely because you
did not want it crawled — then a retired name above those rules means they are not in force for
that crawler. Nothing else in the file is protecting them. That one is worth doing today.</p>

<h2>The fixes that make it worse</h2>

<ul>
<li><strong>Deleting the dead line and stopping there.</strong> You have removed a rule that did
nothing and added nothing that does. Write the current token first.</li>
<li><strong>Adding the new token to a group you have not read.</strong> You are now applying that
group's rules to a live crawler. Read them before you attach a working name to them.</li>
<li><strong>Treating robots.txt as access control.</strong> It is a request, honoured by the
crawlers that choose to. If the content must not be fetched, that is an authentication job —
<a href="/index/ai-directives/">the directives survey &rarr;</a> goes into what the file can and
cannot do.</li>
<li><strong>Copying an AI block from another site.</strong> That is how retired names spread in the
first place: they were correct when someone published them and nothing re-checks a copied file.</li>
</ul>

<h2>How to make this finding go quiet without protecting anything</h2>

<p>Delete the AI group entirely. There are now no dead tokens to report, and your site is governed
by the catch-all alone — which is the exact situation the finding was describing. <strong>A check
about dead rules cannot see rules you never wrote.</strong> The silence means the same thing it
meant before; only the paperwork changed.</p>

<h2>Where this sits in an audit</h2>

<p>The registered check is <code>ai.dead_crawler_directive</code>, which reads robots.txt for
crawler names that no longer match anything. For the survey of how common this is across large
sites, and the three separate ways a directive dies, see <a href="/index/ai-directives/">the AI
directives survey &rarr;</a>. For what a <code>noindex</code> tag does and does not do to these
crawlers, see <a href="/learn/does-noindex-stop-ai-crawlers/">does noindex stop AI crawlers
&rarr;</a>.</p>
"""
    return render(
        cat="how-to", slug="what-a-dead-crawler-rule-costs",
        title="What a dead robots.txt rule actually costs",
        desc=("An audit can call a retired crawler name an exposure when a site's catch-all group "
              "is stricter — what a dead rule costs depends on where the crawler lands instead."),
        h1="What a dead robots.txt rule actually costs",
        crumb='<a href="/">Docket</a> / <a href="/how-to/">Fix it</a> / Dead crawler rules',
        body=body,
        faq=[
            ("My robots.txt names a retired AI crawler. Is my site exposed?",
             "Not necessarily. A crawler matching no group falls back to User-agent: *, so the "
             "dead name only costs you a restriction the catch-all group does not already "
             "carry. If the catch-all is stricter, the crawler is more restricted, not less."),
            ("How do I tell whether a dead crawler rule matters?",
             "Compare the rules in that group against the rules under User-agent: *. Anything "
             "present in the dead group and absent from the catch-all is what stopped being in "
             "force. Everything else is untidy rather than an exposure."),
            ("Does a retired token beside its live replacement do any harm?",
             "No. A group's rules apply to every user-agent named above it, so if the current "
             "name is in the same group the live crawler receives every rule. Remove the old "
             "line when convenient."),
            ("Should I just delete my AI crawler rules if they are not working?",
             "That removes the finding and not the problem. Deleting the group leaves your site "
             "governed by the catch-all alone, which is the situation the finding was "
             "describing. Write the current token above the rules you meant to apply."),
            ("Why would a tool report this when nothing is getting through?",
             "Because the dead token is easy to verify and the consequence is not. Ours made "
             "exactly that mistake: it reported six retired names as an active exposure on a "
             "site whose catch-all group carried every rule the AI group had, and more."),
        ],
    )


if __name__ == "__main__":
    print(dead_crawler_rules())
