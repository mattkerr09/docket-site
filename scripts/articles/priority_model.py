#!/usr/bin/env python3
"""How Docket orders findings — severity, impact, effort and reach.

Sourced from `models.Severity` and its docstring, `models.SEVERITY_WEIGHT`,
`models.Effort` and `models.EFFORT_COST`, `models.Finding.priority`,
`scoring.action_plan` (the four phases, the impact threshold and the item cap),
`scoring.summarize` (which orders by severity BAND first and priority within
it), and `scoring._deduction` (where `tool_limit` returns zero). Every one of
those is in the shipped build.

⚠️ NO TYPED WEIGHTS. Each number on this page comes through `facts` from
`data/priority-model.json`, which `scripts/collect_priority_model.py` generates
by reading the engine's own tables. The reach curve is RECOMPUTED from
`Finding.priority` rather than reimplemented, so a change to that expression
makes the dataset stale instead of making this page quietly wrong. That matters
more here than on most pages: a formula page that drifts still renders
perfectly, and describes a product that no longer exists.

⚠️ WHAT THIS PAGE REFUSES TO SAY.

  1. That the weights are calibrated against measured outcomes. They are not.
     They are an editorial judgement about relative harm, and the page says so.
     No traffic study backs the claim that a critical is worth exactly ten
     notices, and inventing one would be the exact failure this repo exists to
     avoid.
  2. That fixing in this order produces a ranking gain. Docket has measured no
     such thing. The claim made is narrower and defensible: the order is
     consistent, it is stated, and you can audit it yourself.
  3. Any comparison to how another tool prioritises. No rival's algorithm has
     been read at source, so there is nothing to compare against.

The two incidents described in the "when we got this wrong" section are
recorded in the repository's own comments, and both are named by CATEGORY only
— a roofing company, an agency report — never by domain, per the rule that
governs every site we have tested and not published.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import facts as F  # noqa: E402
from render import render  # noqa: E402

#: Worked example. Chosen so the arithmetic is checkable by hand and so the
#: LOWER-severity finding wins, which is the whole point of the formula.
EG_PAGES = 25

#: The two impacts in the worked example. Constants because they appear both in
#: the prose and in the arithmetic below, and a figure that lives in two places
#: is the one shape this site does not allow.
EG_MID_PAGES = 9
EG_HIGH_IMPACT = 7
EG_MEDIUM_IMPACT = 6


def _worked() -> dict:
    """Two findings, ranked by the real weights rather than by a story."""
    high = (F.severity_weight("high") * EG_HIGH_IMPACT * F.reach_at(1)
            / F.effort_cost("large"))
    medium = (F.severity_weight("medium") * EG_MEDIUM_IMPACT * F.reach_at(EG_PAGES)
              / F.effort_cost("trivial"))
    return {"high": round(high, 1), "medium": round(medium, 1)}


def priority_model() -> Path:
    w = _worked()
    levels = F.severity_levels()
    body = f"""
<p class="lede">Every audit tool hands you a list of problems. The hard part is not finding them
— it is knowing which one to do on Monday morning. Docket answers that with a single number it
computes for every finding, and this page is that number written out in full, because a
priority you cannot audit is just an opinion with a sort order.</p>

<h2>The formula</h2>

<p>Each finding gets a priority score of <strong>severity weight x impact x reach, divided by
effort cost</strong>. Higher goes first. Three of those four multiply the case for doing
something; the fourth divides by what it costs you.</p>

<p>There is a fifth term: a finding that names a page where you sell, book or take
enquiries is multiplied by <strong>{F.money_weight():g}</strong>. A missing title on
<code>/pricing</code> and the same missing title on a tag archive used to rank identically, and
for a business paying to be found they are not the same job.</p>

<p>That multiplier is deliberately small. It orders two findings of the same severity and
cannot lift one past a more serious problem — a critical issue anywhere still outranks a medium
one on your pricing page, because this page prints a severity beside every finding and a
ranking that contradicts that label would make one of the two wrong with no way to tell which.
It recognises English paths only, and it errs towards leaving a page alone rather than
promoting the wrong one.</p>

<p>The inputs are worth taking one at a time.</p>

<h3>Severity — how badly it hurts</h3>

<p>There are {len(levels)} severities that represent a problem, and their weights are not evenly
spaced:</p>

<ul>
<li><strong>Critical</strong>, weight {F.severity_weight("critical"):g} — reserved, in the
engine's own words, for "this page or site cannot rank at all": a noindex on a page that earns
money, a robots.txt that disallows everything, a server returning 5xx. Anything that merely
<em>reduces</em> performance is High or below, deliberately, because a critical bucket that
fills with noise stops meaning anything.</li>
<li><strong>High</strong>, weight {F.severity_weight("high"):g}.</li>
<li><strong>Medium</strong>, weight {F.severity_weight("medium"):g}.</li>
<li><strong>Low</strong>, weight {F.severity_weight("low"):g}.</li>
<li><strong>Notice</strong>, weight {F.severity_weight("notice"):g} — including every finding
where Docket is reporting its own blind spot rather than a fault in your site.</li>
</ul>

<p>Two honest notes about those numbers. They are ratios, not measurements: nothing was timed or
tested to establish that a critical is worth exactly
{F.severity_weight("critical") / F.severity_weight("notice"):.0f} notices. They are an editorial
judgement about relative harm, held steady so that two audits of the same site agree with each
other. And the gap between Critical and High is the largest in the table on purpose, because the
distinction it encodes — cannot rank at all, versus ranks worse than it should — is the only one
that changes what you do today.</p>

<h3>Impact — how much this particular instance matters</h3>

<p>Severity is a property of the <em>kind</em> of problem. Impact is set per finding, so two
findings at the same severity can rank differently. It is also the field that decides which
phase of the plan a finding lands in, at a threshold of {F.phase_impact_threshold():g}.</p>

<h3>Reach — how much of the site is affected, with the volume turned down</h3>

<p>This is the input most tools get wrong, and the way Docket handles it is the most opinionated
thing on this page. Reach does <strong>not</strong> scale with the number of affected pages. It
follows a square-root curve that stops growing altogether:</p>

<ul>
<li>1 page — multiplier {F.reach_at(1):g}</li>
<li>{EG_MID_PAGES} pages — multiplier {F.reach_at(EG_MID_PAGES):g}</li>
<li>{EG_PAGES} pages — multiplier {F.reach_at(EG_PAGES):g}</li>
<li>100 pages — multiplier {F.reach_at(100):g}</li>
<li>{F.reach_plateau()} pages — multiplier {F.reach_max():g}, and it never goes higher</li>
<li>5,000 pages — still {F.reach_max():g}</li>
</ul>

<p>Past {F.reach_plateau()} affected pages, one more changes nothing. The reason is written into
the code as a failure mode to avoid: with a raw count, one trivial nit repeated across 5,000
template-generated pages would outrank a critical noindex on your homepage. That is exactly why
large-site audits from big tools are so often unusable — the top of the list is whatever the CMS
happens to do everywhere. Docket caps reach so that breadth matters, but cannot win on its
own.</p>

<h3>Effort — the divisor</h3>

<p>Effort is the only input that makes a score smaller, and the spread is wide:</p>

<ul>
<li><strong>Trivial</strong>, cost {F.effort_cost("trivial"):g} — one tag or one line of config,
minutes.</li>
<li><strong>Small</strong>, cost {F.effort_cost("small"):g} — a template change, under an
hour.</li>
<li><strong>Medium</strong>, cost {F.effort_cost("medium"):g} — a few hours, several templates
or some content.</li>
<li><strong>Large</strong>, cost {F.effort_cost("large"):g} — a project: a migration, a rebuild,
net-new content.</li>
</ul>

<p>A Large fix is divided by {F.effort_cost("large") / F.effort_cost("trivial"):g} times as much
as a Trivial one, which is a strong enough thumb on the scale to reorder the list — and it is
meant to be. A fix nobody has time for is worth less than a smaller fix that ships this
afternoon.</p>

<h2>A worked example, where the milder finding wins</h2>

<p>Two findings on the same site:</p>

<ul>
<li>A <strong>High</strong> on one page, impact {EG_HIGH_IMPACT}, requiring a
<strong>Large</strong> project. Score: {F.severity_weight("high"):g} x {EG_HIGH_IMPACT} x
{F.reach_at(1):g} /
{F.effort_cost("large"):g} = <strong>{w["high"]:g}</strong>.</li>
<li>A <strong>Medium</strong> across {EG_PAGES} pages, impact {EG_MEDIUM_IMPACT}, fixed by a
<strong>Trivial</strong> edit. Score: {F.severity_weight("medium"):g} x {EG_MEDIUM_IMPACT} x
{F.reach_at(EG_PAGES):g} / {F.effort_cost("trivial"):g} =
<strong>{w["medium"]:g}</strong>.</li>
</ul>

<p>The Medium ranks far above the High, and that is the formula working rather than failing. One
is an afternoon's work that improves {EG_PAGES} pages; the other is a quarter's project that
improves one. If you have a morning, the arithmetic agrees with what an experienced consultant
would tell you.</p>

<h2>Four phases, because a sorted list is still not a plan</h2>

<p>The score orders findings, but the plan groups them first, so it reads as a sequence rather
than a leaderboard:</p>

<ol>
<li><strong>Stop the bleeding</strong> — everything Critical, regardless of effort. If a page
cannot rank at all, nothing else you do to it matters.</li>
<li><strong>Quick wins</strong> — impact {F.phase_impact_threshold():g} or above, at
{" or ".join(F.quick_win_efforts_words())} effort.</li>
<li><strong>Build</strong> — impact {F.phase_impact_threshold():g} or above, but real work.</li>
<li><strong>Polish</strong> — everything else worth doing.</li>
</ol>

<p>Within each phase, items stay in priority order. The plan prints
{F.plan_item_cap()} items at most — a plan of two hundred things is not a plan — and every item
it keeps carries the true total, so the report can say how many it is not showing. That last
part exists because of a mistake described below.</p>

<h2>Where Docket does not let the score decide</h2>

<p>Two places, both deliberate.</p>

<p><strong>The summary at the top of the report is ordered by severity, not priority.</strong>
Priority is the right answer to "what should I do first", because reach genuinely should decide
the work order. It is the wrong answer to "what are the five biggest problems", and a section
headed that way which lists five Mediums above a High contradicts the severity label the same
report prints beside each one. When two things on one page disagree, the reader cannot tell
which to believe. So the summary sorts by severity band and uses priority only to order within
a band.</p>

<p><strong>Findings that describe Docket's own blind spots cost your score nothing.</strong>
When a check cannot see enough to answer — a link graph assembled by JavaScript, an external
link that could not be fetched — it says so rather than guessing, and that finding is marked as
a limit of the tool. Those are excluded from the score deduction entirely, because a site Docket
<em>cannot read</em> should not score below one it can for that reason alone.</p>

<h2>When we got this wrong</h2>

<p>Both of the rules above are repairs, and the repository records what prompted them.</p>

<p>The summary ordering was found by reading a full report for a roofing company rather than
looking at its score. All five headline items were Medium, while both High findings — one of
them invisible rating markup, which carries a Google manual-action risk — sat past position ten,
which is further than anyone reads. Nothing was broken; priority was doing exactly what it was
designed to do, in a section where that was the wrong question.</p>

<p>The plan cap was found on an agency report of several hundred pages whose cover promised
fifty items while the plan printed {F.plan_item_cap()} numbered ones, with nothing explaining
the gap. A reader who counted would conclude the report withheld ten fixes it had charged for.
The cap stayed — it is there for a reason — but every item now carries the total so the
renderers can say what was left out.</p>

<p>And the tool-limit exclusion was subtler than it looks. Those findings were given an impact
of zero, which everyone assumed protected the score. It did not: impact never enters the score
calculation at all, which is driven by severity and reach, so a blind-spot notice deducted from
a lane exactly like any other notice. The test that was supposed to guard this asserted that
impact was zero — the premise, not the behaviour it was named for. The fix was two lines; the
lesson was that a test should assert the thing it claims to protect.</p>

<h2>Checking it yourself</h2>

<p>None of this has to be taken on trust. Every finding in a Docket report carries its own
severity, impact, effort and affected-page count, and the JSON export carries the computed
priority alongside them, so you can recompute any score on this page from the numbers in your
own report. If our arithmetic and yours disagree, one of us has a bug, and we would like to know
which.</p>

<p><a class="btn" href="/download/">Download Docket</a></p>
"""
    return render(
        cat="learn", slug="priority-model",
        title="How Docket decides what to fix first",
        desc=("Severity, impact, reach and effort, and the formula that combines them. "
              "The weights an audit ranks your site with, written out so you can check them."),
        h1="How Docket decides what to fix first",
        crumb='<a href="/">Docket</a> / <a href="/learn/">Learn</a> / What to fix first',
        body=body,
        faq=[
            ("How does Docket decide which SEO problem to fix first?",
             "It computes a priority score for every finding: severity weight multiplied by "
             "impact and by reach, divided by the effort the fix takes. Findings are then "
             "grouped into four phases — critical problems, quick wins, longer builds, and "
             "polish — and ordered by score inside each phase."),
            ("Why does a medium-severity issue rank above a high one?",
             "Because reach and effort are in the formula. A medium problem across dozens of "
             "pages that one template edit fixes will outrank a high-severity problem on a "
             "single page that needs a rebuild. That is intended: it matches what an "
             "experienced consultant would tell you to do with one free afternoon."),
            ("Does a problem on more pages always rank higher?",
             "No. Reach follows a square-root curve that stops growing entirely past "
             f"{F.reach_plateau()} affected pages, so breadth matters but cannot win on its "
             "own. Without that cap, one trivial issue repeated across thousands of "
             "template-generated pages would outrank a critical problem on the homepage, "
             "which is the usual reason large-site audits are unreadable."),
            ("Are Docket's severity weights based on measured ranking data?",
             "No, and the page says so. They are an editorial judgement about relative harm, "
             "held consistent so that two audits of the same site agree. No study backs a "
             "claim that any particular issue costs a specific amount of traffic, and Docket "
             "does not make one."),
            ("What is a tool-limit finding and why does it not affect my score?",
             "It is Docket reporting its own blind spot rather than a fault in your site — a "
             "link graph it could not read, an external link it could not fetch. Those are "
             "excluded from the score deduction, because a site Docket cannot fully read "
             "should not score lower than one it can for that reason alone."),
        ],
    )


BUILDERS = [priority_model]


def build_all() -> list:
    return [b() for b in BUILDERS]
