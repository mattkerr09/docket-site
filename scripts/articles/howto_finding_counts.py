"""A finding's count is not decoration — it sorts your work.

Promised on the how-to hub. Sourced from two recorded cases in the app repo:
`ai.entity`, whose `ai.weak_sameas` branch badged the COMPLEMENT of what its
own headline counted, and `cvr.unusable_phone`, whose helper counted link
occurrences where the report renders pages.

The mechanism is one line of the model: `count_unit` defaults to "page", so a
count of anything else is rendered as a number of pages by every surface that
reads it. And `scoring._deduction` grows the penalty with the logarithm of the
count, so a wrong count does not just misinform — it reorders the plan.

⚠️ NO SITE IS NAMED. The deploy's third-party gate refuses pages naming sites
measured without asking, and neither case needs a name.

⚠️ DO NOT CONFLATE THE TWO REACH FORMULAS. The score's deduction uses a
logarithm of the count; the plan's priority uses a square root of it. Both are
documented on /learn/priority-model/ and this page describes their
shape in words rather than restating either.

Numerals: none. Quantities are spelled as words, which `verify_numbers.py`
does not match and which cannot go stale against a dataset.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from render import render  # noqa: E402


def finding_counts() -> Path:
    body = """
<p class="lede">Every finding in an audit report carries a small number beside it — a badge, a
tag, a "…and more" under a shortened list of URLs. It looks like a detail. It is not: that
number is usually what decides how far up your plan the finding sits, so a count of the wrong
thing quietly moves work you do not need to do above work you do.</p>

<h2>The badge that argued with its own headline</h2>

<p>On a hospital's report, a finding's badge read <em>sixteen profiles</em> directly above the
headline <em>Only two recognised profiles in sameAs</em>. Two quantities, one finding, and no
reader can reconcile them.</p>

<p>The headline counted the profiles the site had. The badge counted the ones it did not — the
remainder of the tool's own list of recognised profile types. A complement, presented in the
place a reader expects a total.</p>

<p>That is bad writing, and it is also a bad instruction. A complement implies a target: it says
the hospital should hold every profile type on the list. Nobody needs a Better Business Bureau
listing, a developer-platform organisation and an app-store page, and a finding that implies
otherwise is asking for work that would not help anyone.</p>

<h2>Why a wrong count is not cosmetic</h2>

<p>The number feeds the score. Docket's deduction grows with the logarithm of a finding's count,
so a finding that claims to affect many things takes a larger bite out of your score than the
same finding claiming to affect one.</p>

<p>On that report the effect ran backwards. The inflated count sat on a <strong>low</strong>
severity finding — you have some profiles, here are more you could add — and pushed its
deduction above the untouched deduction of the <strong>medium</strong> finding for having no
<code>sameAs</code> at all. The smaller problem outweighed the bigger one, and nothing in the
report said why.</p>

<p>It also broke a quieter thing. When a plan item names a section of your site, the tool decides
whether that item covers the section <em>completely</em> by comparing the count against the list
of URLs it is showing you. A count of sixteen against a single URL can never come out complete,
so the item could never be described accurately however true it was.</p>

<h2>The default that causes it</h2>

<p>Here is the mechanism, because it tells you what to look for in any tool. A finding's count
carries a unit, and in Docket that unit <strong>defaults to pages</strong>. Every surface that
renders a count — the badge, the summary line, the "…and N more" under a truncated URL list —
reads that unit. So a check that counts anything other than pages and forgets to say so does not
produce a vague number. It produces a confident, specific, wrong sentence about your pages.</p>

<h2>The same bug wearing different clothes</h2>

<p>The phone check had it too, and its version is the clearer one to picture. A phone number
lives in a template. Write it wrongly and you have written it wrongly everywhere, so a site with
one bad number can have that number linked in a header, a footer and a contact block on every
page.</p>

<p>Counting the links, the finding said several numbers were affected and offered "for example"
before one of them — promising a set the reader did not have. And because the count was
occurrences rather than pages, a single page carrying the number in its header and again in its
footer produced a finding tagged <em>two pages</em>, with "…and one more" printed underneath a
list containing the only page there was.</p>

<p><strong>Four links to one number is one number.</strong> The repair is one edit to one
template, and every part of the report said otherwise.</p>

<h2>What to check on your own report</h2>

<ul>
<li><strong>Read the badge against the headline.</strong> If they disagree, the headline is
usually the honest one — it was written by a person. The badge came from a variable.</li>
<li><strong>Compare the count to the list of URLs.</strong> A count larger than the list is
either a genuine truncation or a unit error, and the "…and N more" line tells you which: if the
list is already showing everything, there is no more.</li>
<li><strong>Ask what one fix would cover.</strong> If the answer is "all of them, in one edit",
the count is measuring your evidence rather than your work.</li>
<li><strong>Distrust a count that implies a completion target</strong> — anything phrased as
what you are missing out of a list the tool is holding.</li>
</ul>

<h2>When this does not matter</h2>

<p>Keep the severity in view. A miscounted low-severity finding at the bottom of a plan costs you
nothing, because you were not going to reach it this quarter and the ordering among items you
will not do is not worth auditing.</p>

<p>It matters when a count moves something <em>across</em> a boundary — above an item you would
otherwise have done first, or into an earlier phase of a plan. That is the case worth the minute
it takes to check, and it is almost always a finding whose count is much larger than the number
of URLs listed beneath it.</p>

<h2>The fixes that make it worse</h2>

<ul>
<li><strong>Working the list top to bottom without reading it.</strong> An ordered plan is a
recommendation, and the ordering is the part most likely to be wrong.</li>
<li><strong>Fixing every instance the count implies.</strong> On a template-set value there is
one instance. Opening thirty pages to change a number that lives in one file is the wasted
afternoon this defect causes.</li>
<li><strong>Chasing a completion target you were never set.</strong> A count of what you lack,
out of a list somebody else wrote, is not a goal.</li>
</ul>

<h2>How to move a finding up the plan without fixing anything</h2>

<p>Worth knowing, because it tells you how much weight the ordering can bear. Split one problem
into more instances — the same bad value in more places, the same broken link on more pages —
and its count rises, its deduction grows, and it climbs. Nothing about the underlying fault
changed, and the fix is still one edit.</p>

<p>Which means an ordering built on counts rewards fragmentation. Any tool that sorts by volume
has this property, including this one. The defence is the question above: what would one fix
cover?</p>

<h2>Where this sits in an audit</h2>

<p>The two registered checks behind the cases here are <code>ai.entity</code>, which covers
entity definition and <code>sameAs</code>, and <code>cvr.unusable_phone</code>, which reads the
<code>href</code> of every phone link. Both now count what their headlines count, and the phone
one names its unit explicitly rather than taking the default.</p>

<p>For how the ordering is actually computed — severity, effort and reach, and where the score
is deliberately not allowed to decide — see
<a href="/learn/priority-model/">how findings are prioritised &rarr;</a>. For the
related case where a count is right but its unit should have been templates rather than pages,
see <a href="/how-to/read-findings-that-blame-the-whole-site/">when a finding blames the whole
site &rarr;</a>.</p>
"""
    return render(
        cat="how-to", slug="check-the-count-on-a-finding",
        title="A finding's count is not decoration",
        desc=("The number badged on an audit finding feeds its score and its place in your "
              "plan. Two cases where it counted the wrong thing on a site."),
        h1="A finding's count is not decoration",
        crumb='<a href="/">Docket</a> / <a href="/how-to/">Fix it</a> / Counts',
        body=body,
        faq=[
            ("What does the number next to an audit finding mean?",
             "Usually how many pages it affects — that is the default unit in Docket and in "
             "most tools. It also feeds the score and the ordering of your plan, so it is not "
             "only a label."),
            ("The count and the headline of a finding disagree. Which is right?",
             "Usually the headline, because a person wrote it and the badge came from a "
             "variable. Compare the count against the list of URLs under the finding before "
             "acting on it."),
            ("Why would a count be larger than the number of pages listed?",
             "Either the list was truncated, which the report should say, or the count is "
             "measuring something other than pages — link occurrences, or items missing from a "
             "list the tool holds."),
            ("Does a wrong count change my score?",
             "Yes. The deduction grows with the count, so an inflated count takes a bigger bite "
             "and can lift a low-severity finding above a more serious one."),
            ("How do I tell whether a count is measuring my work?",
             "Ask what a single fix would cover. If one edit to one template resolves every "
             "instance, the count is measuring evidence rather than work."),
        ],
    )


if __name__ == "__main__":
    print(finding_counts())
