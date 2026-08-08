#!/usr/bin/env python3
"""AI substitution — which of your pages an answer replaces outright.

Numbers are from Docket's own exposure analysis run against two live sites on
2026-08-07, after three false positives found during that run were fixed. The
worse of the two results is ours, which is the only reason the page is worth
reading.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import facts as F  # noqa: E402
from render import render  # noqa: E402


def ai_substitution() -> Path:
    body = f"""
<p class="lede">The AI-search risk to most businesses is not losing rankings. It is keeping
them and losing the visit, because the answer now appears in the result — so the question
worth asking about a page is not how it ranks but whether an answer somewhere else delivers
what it offers.</p>

<p>Docket puts a number on that. Run against <strong>zingermansdeli.com</strong>, a
delicatessen in Ann Arbor, it assessed {F.exposure_assessed('zingermansdeli')} pages and found
<strong>{F.exposure_substitutable_pct('zingermansdeli')}% fully substitutable</strong>, because
{F.exposure_defence('zingermansdeli', 'transact')} of them let the visitor do something and
{F.exposure_defence('zingermansdeli', 'operate')} carry something to operate. Run against
<strong>docketseo.app</strong> it assessed {F.exposure_assessed('scoutseo')} pages and found
{F.exposure_substitutable_pct('scoutseo')}% too — but the worst page on this site scored 0.85
out of 1 a few hours before this was written, and what changed was mostly the measurement
rather than the page.</p>

<h2>The two questions</h2>

<p><strong>How completely can an answer deliver this page's value?</strong> A page that
exists to explain something is a page an assistant replaces outright. It reads it once and
answers the question forever, and no amount of writing it better changes that.</p>

<p><strong>What is here that an answer cannot reproduce?</strong> Six things, in rough order
of strength:</p>

<div class="wrap-tbl"><table class="cmp">
<thead><tr><th>Defence</th><th>Why an answer cannot take it</th></tr></thead>
<tbody>
<tr><td>Data of your own</td><td>An assistant answering from your numbers has to name you.
It converts a lost click into a citation, which is a better outcome than the visit</td></tr>
<tr><td>A transaction</td><td>It can describe your service. It cannot book it, buy it or
quote it</td></tr>
<tr><td>Something to operate</td><td>The value is in the doing. A calculator cannot be
summarised into having been used</td></tr>
<tr><td>Value behind a login</td><td>What is gated is not in a training set</td></tr>
<tr><td>A physical place</td><td>Geography is not substitutable by a language model</td></tr>
<tr><td>Media</td><td>A video loses most of what it is when flattened to text</td></tr>
</tbody></table></div>

<h2>What the two sites show</h2>

<p>The deli is the instructive one. {F.exposure_defence('zingermansdeli', 'transact')} of its
{F.exposure_assessed('zingermansdeli')} assessed pages carry a transaction,
{F.exposure_defence('zingermansdeli', 'login')} put something behind a login,
{F.exposure_defence('zingermansdeli', 'physically')} are anchored to the shop itself. It has no AI
strategy that we can see and does not need one, because almost every page asks the visitor to
do a thing that has to happen on the page. A model can describe a Reuben. It cannot hand you
one.</p>

<p>Our site scores worse, and that is the honest position rather than a modest one. Docket's
site is mostly explanation — that is what a site selling an audit tool tends to be — and the
defence holding most of it up is original data. The page most at risk is the one
explaining what an SEO audit is, which is exactly the shape an assistant answers without a
click. We know what to do about it and it is not an SEO fix.</p>

<h2>Three things we got wrong building this</h2>

<p>The analysis was written days before it was run against anything real. Pointing it at two
live sites produced three false positives in an afternoon, all of them the same mistake:
<strong>counting a signal being mentioned as the signal being present.</strong></p>

<p><strong>Our own site scored as a physical business, three times.</strong> The matcher
looked for phrases like "opening hours" — and Docket's copy explains, at length, that local
businesses need opening-hours markup. Meanwhile the actual delicatessen scored zero. The test
was backwards in both directions at once. It now wants schema.org place markup, or
first-person prose corroborated by a phone number, and the distinction that fixed it is
small and exact: a page about local SEO writes "opening hours", and a business with a counter
writes "our hours".</p>

<p><strong>Three comparison pages scored as carrying a tool</strong>, because "Try it against
your own site" matched a pattern looking for "try it". That is a download button, not a
calculator.</p>

<p><strong>The deli scored "media" on 32 of its
{F.exposure_assessed('zingermansdeli')} pages</strong>, and every single hit was the Google
Tag Manager noscript iframe. A defence that fires on every site running GTM defends nothing.
It now counts a <code>&lt;video&gt;</code> or <code>&lt;audio&gt;</code> element, or an iframe
on a known media host. That number is
{F.exposure_defence('zingermansdeli', 'media')} today.</p>

<p>A fourth turned up when the analysis was finally rendered into a PDF and looked at rather
than read as code. Our privacy policy and terms of use were sitting in the "most exposed"
list — accurate, and useless. A privacy policy's reason to exist is not that people read it.
Legal and utility pages are now left out of the portfolio, which is why the figure above
covers {F.exposure_assessed('scoutseo')} of our pages rather than all of them.</p>

<p>Then three more, all the same shape. This article scored as having a login and a
calculator, because it contains a table explaining that logins and calculators are defences.
And the SEO-audit explainer scored as having <em>no</em> data of its own while reporting that
we read the JSON-LD of {F.entity_n()} sites — the verb list did not include "we read".</p>

<p>Two others came from the opposite direction. "Download" was not counted as a transaction
while "sign up" was, which is an inconsistency rather than a principle. Fixing it then made
this site 100% defended on the strength of one button in the header, so calls to action whose
text appears on every page are treated as navigation now.</p>

<p>Most of those made a site look safer than it was, which is the failure mode that matters
here. We are writing them down because a page arguing that you should measure this should say
what measuring it badly looks like — and because the scores on this page moved while it was
being written, which a reader deserves to know.</p>

<div class="callout">
<div class="callout-title">The weakest of the six, stated plainly</div>
<p>Docket cannot tell a button in your site header from one that is a page's whole purpose. It
drops calls to action whose exact text repeats on every page, which catches a plain
"Download" in the navigation — and not four spellings of the same closing button. Tightening
it further means guessing at page structure, and tuning a scorer against your own site is how
a measurement quietly becomes the answer you wanted. Read the transaction count as "pages that
ask for an action", not "pages whose reason to exist is that action".</p>
</div>

<h2>Where another tool is better</h2>

<p><a href="/vs/">Profound, Otterly and Peec</a> track whether you are actually cited, by
running prompts against the models and recording what comes back. That is downstream reality
and Docket cannot produce it — we do not run prompts, and a tool on your Mac has no way to see
what ChatGPT told someone in Ohio. If the question is "am I being cited today", buy one of
those.</p>

<p>What Docket answers is the question underneath: which pages have a reason to be visited at
all. Those are different measurements and the second one does not go stale, because it is a
property of your content rather than of this month's model.</p>

<h2>What this is not</h2>

<p>It is not a traffic forecast. Docket cannot see your analytics, nobody knows how far AI
answers will erode any particular site, and any tool telling you "you will lose 40% of your
traffic" is inventing the number. A risk score of 0.85 does not mean 85% fewer visits. It
means the page's value is 85% deliverable somewhere else, which is a statement about the page
and not about the future.</p>

<p>It also does not judge your writing. A brilliantly written explainer and a mediocre one
are equally substitutable, because the assistant reads both and answers the question either
way. That is the uncomfortable part and it is why the fix is structural.</p>

<h2>What to do with a high number</h2>

<ol>
<li><strong>Publish something only you can measure.</strong> The one defence that converts a
lost click into a citation. It does not have to be big — a survey of 40 customers is data
nobody else has. Ours are <a href="/index/ai-directives/">a robots.txt survey</a> and
<a href="/learn/sameas-entity-signals/">an entity one</a>, and they are the reason most of
this site is defended at all.</li>
<li><strong>Give explainers something to do.</strong> A quote form, a checker, a booking
step. An explainer with a tool in it stops being a page an answer replaces and becomes one it
points at.</li>
<li><strong>Consider gating your deepest material</strong> behind a free sign-up. What is
gated is not in a training set, and the trade is one readers already understand.</li>
<li><strong>For everything that stays explanatory</strong>, compete to be the source that
gets cited rather than the page that gets read: question-shaped headings, the answer in the
first two sentences, a named author.</li>
</ol>

<p>Docket reports this on every audit, as a portfolio rather than a grade. "These four pages
are fully substitutable and here they are" is something you can act on. A letter is not. The
figures on this page come from auditing both sites on
{F.exposure_measured('scoutseo')} and are read from those runs rather than typed, because a
number in a sentence cannot tell you when it has stopped being true.</p>

<p><a class="btn" href="/download/">Download Docket</a></p>
"""
    return render(
        cat="learn", slug="ai-substitution",
        title="Which of your pages can an AI answer replace?",
        desc=("The AI risk is keeping your rankings and losing the visit. What "
              "defends a page against an answer, measured on two live sites — "
              "and six ways we measured it wrong."),
        h1="Which of your pages an AI answer replaces",
        crumb='<a href="/">Docket</a> / <a href="/learn/">Learn</a> / AI substitution',
        body=body,
        published="2026-08-07",
        faq=[
            ("What makes a web page substitutable by AI?",
             "Being purely explanatory. If the page's whole value is telling the reader "
             "something, an assistant can tell them instead and the visit never happens. "
             "Pages that let someone do something — buy, book, calculate, log in, or turn "
             "up in person — are not substitutable, however good the model gets."),
            ("Does this predict how much traffic I will lose?",
             "No, and nothing can. Docket cannot see your analytics and nobody knows how far "
             "AI answers will erode any particular site. A risk of 0.85 means the page's "
             "value is 85% deliverable elsewhere — a statement about the page, not a "
             "forecast."),
            ("What is the strongest defence against AI substitution?",
             "Data of your own. An assistant answering from your numbers has to name you, "
             "which turns a lost click into a citation — a better outcome than the visit "
             "you were going to lose. On docketseo.app it is the defence holding most "
             "of the site up."),
            ("Will writing better content help?",
             "Not for this. A brilliantly written explainer and a mediocre one are equally "
             "substitutable, because an assistant reads both and answers the question "
             "either way. The fix is structural: give the page something to do."),
        ],
    )


BUILDERS = [ai_substitution]


def build_all() -> list[Path]:
    return [b() for b in BUILDERS]


if __name__ == "__main__":
    for p in build_all():
        print(p)
