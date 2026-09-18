"""Telling a decision from a mistake, when the file looks the same either way.

Promised on the how-to hub. Sourced from `ai_visibility.py`, registered check
`ai.crawler_access`:

  * a national broadcaster names and disallows AI citation crawlers as
    published editorial policy. The check called that CRITICAL and capped an
    otherwise well-run site's score for a decision already made on purpose.
    Being swept up by a wildcard is a different thing — it may never have been
    considered, and that one is worth interrupting somebody over.
  * ⚠️ THE MIDDLE CASE LANDED IN THE BRANCH WRITTEN FOR THE EMPTY ONE. The test
    was `all(named)`, false as soon as one crawler is unnamed, so a file naming
    and disallowing two of three by hand and letting a wildcard catch the third
    produced, at CRITICAL: "None of them is named in your robots.txt, so a
    wildcard rule is catching them and this may never have been a decision."
    Two were named, one line above the wildcard. That sentence is what turns a
    notice into a critical, AND THE REMEDY TOLD THEM TO RE-ALLOW THE TWO
    CRAWLERS THEY HAD JUST DECIDED TO BLOCK.
  * the fix: partition the set rather than switch on it. Both findings fire.
  * the snippet used to be a FIXED four-line block whatever was measured,
    including a crawler the survey evidence excludes and crawlers the reader
    had not blocked. It is derived now. A snippet is something people paste.

⚠️ NO SITE OR VENDOR IS NAMED — third-party gate. The broadcaster is "a
national broadcaster"; no user-agent belonging to a measured site is quoted.

⚠️ /learn/ai-crawler-directives/ owns the taxonomy (training vs search-index vs
live-fetch), the wildcard warning and the CDN-versus-robots split. This page
owns how a REPORT should treat a decision, and cross-links rather than
restating.

⚠️ The snippet beat is a near neighbour of /how-to/schema-type-is-a-claim/
(531). Different failure — there the example values read as researched, here
the list did not match the finding above it. Named and linked in one sentence.

Numerals: none. Quantities spelled as words.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from render import render  # noqa: E402


def policy_vs_defect() -> Path:
    body = """
<p class="lede">The hard part of an audit is not finding what is wrong. It is telling a mistake
from a decision — and in a configuration file those look identical. The same line means "we
thought about this and chose it" on one site and "nobody has ever read this line" on another, and
nothing in the file says which. Getting that wrong in the loud direction is how a tool ends up
shouting at somebody for doing their job.</p>

<h2>A published policy, reported as a critical defect</h2>

<p>A national broadcaster names the AI crawlers that decide whether it can be cited, and disallows
them. Deliberately, as editorial policy, in its own file, by people who know exactly what those
names do.</p>

<p>We called it critical, and capped an otherwise well-run site's score over it.</p>

<p>Nothing was wrong. The decision had been made, by the people entitled to make it, and the
report's contribution was to tell them their published policy was a defect and hand them a block
of markup to undo it.</p>

<h2>And the case that really is worth interrupting someone over</h2>

<p>The opposite situation produces the same line in the file. A blanket
<code>User-agent: *</code> rule gets added for an unrelated reason — an aggressive scraper, a
staging leak, advice from years ago — and it sweeps up every crawler, including the ones that
decide whether an assistant can cite you live.</p>

<p>Nobody decided that. Nobody knows it happened. It is exactly the thing an audit exists to
surface.</p>

<p>Two situations, one observation in the file: <em>this crawler is disallowed</em>. What separates
them is not the rule. <strong>It is whether the crawler is named.</strong> A name is somebody
typing a specific crawler on purpose. A wildcard is a net.</p>

<h2>The sentence that was false about the reader's own file</h2>

<p>Then the interesting failure, which is the reason this page exists.</p>

<p>The check asked whether <em>all</em> the blocked crawlers were named. That question has a
sensible answer at each end and a dangerous one in the middle. A file that names and disallows two
crawlers by hand, and lets a wildcard catch a third, answers no — not all of them are named — and
the report that follows was written for a file that named none:</p>

<blockquote><p><strong>robots.txt blocks three AI search crawlers.</strong> None of them is named
in your robots.txt, so a wildcard rule is catching them and this may never have been a
decision.</p></blockquote>

<p>Two of them were named. In that file. One line above the wildcard.</p>

<p>Three things make this worse than a wording slip. That sentence is the one that turns a notice
into a critical, so the false claim is load-bearing. The remedy under it told the reader to
re-allow two crawlers they had just deliberately blocked. And the reader can disprove the whole
thing by opening the file the report is describing.</p>

<p><strong>"None" is a strong word, and in a report it is usually a mis-stated "not all".</strong>
When a finding makes a universal claim about your configuration, check it against the
configuration — a mixed case is the one most likely to be described by a branch written for a pure
one.</p>

<h2>The fix was to stop making it choose</h2>

<p>The set is partitioned now instead of switched on. The named ones and the wildcard-caught ones
are separate findings: one records a policy at a notice, the other is the interruption. Both can
appear on the same report about the same file, because both are true of different crawlers.</p>

<p>That is the general shape. <strong>When one sentence is asked to describe a mixed set, it will
be wrong about part of it.</strong> The answer is rarely a better sentence; it is usually two
findings.</p>

<h2>The paste-ready block that ignored the measurement</h2>

<p>One more, because it rides along with the same finding. The report offers a robots.txt snippet
to paste. It used to be a fixed list — the same user-agent lines for everybody, including a
crawler our own survey evidence says to leave out of that recommendation, and including crawlers
the reader had not blocked in the first place.</p>

<p>It is derived from the measurement now: the block names the crawlers actually found to be
caught, and nothing else. <strong>A snippet is something people paste</strong>, which makes it the
one part of a report that must never be generic. That is a cousin of
<a href="/how-to/schema-type-is-a-claim/">a suggested markup block carrying somebody else's facts
&rarr;</a> — there the example values read as researched; here the list simply did not match the
finding above it.</p>

<h2>Reading this on your own report</h2>

<ol>
<li><strong>Open the file and look for the name.</strong> If the crawler is named, someone typed
it. If only a wildcard covers it, decide now whether you meant to.</li>
<li><strong>Check any universal claim against the file itself.</strong> "None", "every" and "all"
are where reports go wrong, and your file is the evidence.</li>
<li><strong>Decide training and citation separately</strong> — they are different crawlers doing
different jobs, and the costs are not comparable:
<a href="/learn/ai-crawler-directives/">which AI crawler does what &rarr;</a>.</li>
<li><strong>Check the edge as well as the file.</strong> A file that says yes and a server that
says no is a configuration nobody chose.</li>
</ol>

<h2>When this is a real problem</h2>

<p>Keep the weight where it belongs. A wildcard catching search-index crawlers removes you from
answers that cite live sources, and it is invisible precisely because the rule was added for
something else and has been sitting there ever since. That is worth the interruption. A named
block is worth a line in the report and nothing more.</p>

<h2>The fixes that make it worse</h2>

<ul>
<li><strong>Undoing a deliberate block because a report shouted.</strong> If your organisation
decided to stay out of those answers, a tool's severity is not a reason to reverse it. Tools do
not know your policy.</li>
<li><strong>Blocking the whole set because one crawler is a problem.</strong> The names are
matched exactly and the jobs are different; a rule for one says nothing about another.</li>
<li><strong>Fixing the file and leaving the firewall.</strong> An edge rule refusing a crawler is
invisible in robots.txt, so every tool reading the file will tell you the crawler is allowed.</li>
<li><strong>Pasting a suggested block without reading it.</strong> Check that every line names a
crawler you actually meant to change.</li>
</ul>

<h2>How to make this read as policy without deciding anything</h2>

<p>Name every crawler explicitly in your file. The finding drops from an interruption to a note,
because naming is the signal of intent — and naming costs you nothing and commits you to nothing.
<strong>The check is reading a proxy for deliberateness, not deliberateness</strong>, and no file
can carry the difference. Worth knowing in both directions: it is why a named block is treated
gently, and why a wildcard deserves a look even when you are fairly sure you meant it.</p>

<h2>Where this sits in an audit</h2>

<p>The registered check is <code>ai.crawler_access</code>, which reads robots.txt for AI crawler
access. For what each crawler does and what blocking it costs, see
<a href="/learn/ai-crawler-directives/">the AI crawler directives &rarr;</a>. For a rule that names
a crawler nothing answers to, see <a href="/how-to/what-a-dead-crawler-rule-costs/">what a dead
robots.txt rule actually costs &rarr;</a>. For the case where the audit itself was refused, see
<a href="/how-to/tell-a-rate-limit-from-a-block/">telling a rate limit from a block &rarr;</a>.</p>
"""
    return render(
        cat="how-to", slug="when-a-policy-is-reported-as-a-defect",
        title="When a report calls your decision a defect",
        desc=("An audit called a publisher's deliberate policy a critical defect and capped the "
              "site's score — then told a reader none of their crawlers were named when two "
              "were."),
        h1="When a report calls your decision a defect",
        crumb='<a href="/">Docket</a> / <a href="/how-to/">Fix it</a> / Policy or defect',
        body=body,
        faq=[
            ("An audit says blocking AI crawlers is a critical issue. Is it?",
             "Only if you did not mean to. A named, deliberate block is a policy and should be "
             "reported as a note; a crawler swept up by a wildcard rule added for some other "
             "reason is the case worth acting on, because nobody decided it."),
            ("How can a tool tell a deliberate block from an accidental one?",
             "It cannot, exactly. It reads a proxy: whether the crawler is named. Naming a "
             "specific user-agent is someone typing it on purpose, while a wildcard is a net. "
             "That proxy is good enough to set severity and not good enough to be certain."),
            ("My report says none of my crawlers are named, but some are. Why?",
             "Because a test asking whether all of them are named answers no as soon as one is "
             "not, and the sentence underneath was written for a file that named none. Check "
             "any universal claim against the file itself."),
            ("Should I re-allow crawlers my organisation deliberately blocked?",
             "No. A severity level is not a policy decision. If the block was considered and "
             "chosen, the correct outcome is that the report records it and moves on."),
            ("Is fixing robots.txt enough to let an AI crawler in?",
             "Not always. A rule at your CDN or firewall that refuses the crawler is invisible "
             "in robots.txt, so a file that permits it and a server that refuses it will both be "
             "true at once. Check the response your server actually gives."),
        ],
    )


if __name__ == "__main__":
    print(policy_vs_defect())
