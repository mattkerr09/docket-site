"""A schema type is a factual claim about what your organisation is.

Promised on the how-to hub. Sourced from `local_seo.py` — registered check
`local.schema` — whose docstrings record three connected failures:

  * the snippet builder handed a university a complete, valid, PASTEABLE block
    declaring it a plumbing firm with a street address and coordinates in
    another country, with url and image interpolated from the audited site.
    Every customer got that block, not only universities.
  * "LocalBusiness, or a subtype" named a type a university does not have:
    CollegeOrUniversity descends from EducationalOrganization, so the offered
    alternatives were Plumber, Dentist and Restaurant.
  * the deliberate asymmetry: being generous about APPLYING the lane is right,
    being generous about WHAT TO RECOMMEND is not, because the output is markup
    a search engine reads as a factual claim.

⚠️ NO SITE IS NAMED — third-party gate. The university and the bakery are
described by what they are; the plumbing firm in the sample data is fictional
and is described rather than quoted by name.

⚠️ The self-implicating beat must survive: a sibling snippet function in
another file states this principle exactly and was written that way. This one
never got the lesson.

Numerals: none. Quantities spelled as words.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from render import render  # noqa: E402


def schema_type() -> Path:
    body = """
<p class="lede">Structured data is not decoration. A type declaration is a machine-readable
sentence saying <em>this organisation is a thing of this kind</em>, and a search engine reads it
as a claim you have made about yourself. Which is why an audit that suggests the wrong type, and
hands you a block to paste, is doing something more serious than being unhelpful.</p>

<h2>The snippet that told everyone they were a plumber</h2>

<p>This one is ours, and it is the worst thing in the catalogue.</p>

<p>The suggested-markup builder produced a complete, valid, ready-to-paste JSON-LD block. It
declared the organisation a plumbing firm, gave it a plumbing company's name, a street address in
a city on another continent and a pair of geographic coordinates to match. And it interpolated the
audited site's own URL and logo into the same block.</p>

<p>A university received it. So did everybody else — a bakery on one continent was handed markup
saying it was a plumber on another.</p>

<p><strong>The interpolation is what makes it dangerous rather than merely silly.</strong> A block
that opens with your real domain reads as researched, and every field below inherits that
credibility. Nobody scrutinises line four of something that got lines one and two right about
them.</p>

<p>The sharpest part: a sibling function elsewhere in the same codebase states this exact
principle in its own comments — that the lines above interpolate the real name and origin, so
anything number-shaped reads as researched and gets pasted verbatim — and was written carefully
because of it. This one lived in a different file and never got the lesson. <strong>A rule learned
in one place does not travel to another by itself.</strong></p>

<h2>The type that does not exist where the advice said it did</h2>

<p>The second failure is quieter and more common in tooling generally.</p>

<p>The advice used to read "add LocalBusiness, or a subtype". For a university that names a type it
does not have: in schema.org's hierarchy <code>CollegeOrUniversity</code> descends from
<code>EducationalOrganization</code>, not from <code>LocalBusiness</code>. So the subtypes on offer
were things like plumber, dentist and restaurant, and none of them was the answer.</p>

<p>A vocabulary has a shape. "Or a subtype" is only useful advice when the thing you are is
actually underneath the thing being named.</p>

<h2>Generous about applying the check, strict about what to recommend</h2>

<p>Here is the distinction that fixed it, and it generalises well past schema.</p>

<p>The test for whether the local-business checks apply at all is deliberately loose — it keys on
signals like a published street address, which universities, government offices, hospitals,
libraries and museums all have. That looseness is correct: those organisations <em>do</em> have
local-search work to do, and excluding them would help nobody.</p>

<p>But the output of the check is markup that makes a claim. <strong>Being generous about applying
a lane is right. Being generous about what to recommend is not.</strong></p>

<p>So only the unambiguous cases are claimed — an education or government domain label is strong
evidence and gets the matching type. Everything else stays with the general type, because a charity
on an ordinary domain looks exactly like a shop from the outside, and <strong>guessing wrong is
precisely the thing the rule exists to prevent.</strong></p>

<h2>Choosing your own type</h2>

<ul>
<li><strong>Start from what the organisation is, not from what SEO advice mentions.</strong>
<code>LocalBusiness</code> is a common answer because it is a commonly recommended one, not
because it is usually right.</li>
<li><strong>Read the hierarchy before picking a subtype.</strong> Check that your type actually
descends from the one you were told to use — the vocabulary lists its parents.</li>
<li><strong>The fields are mostly the same.</strong> Name, address, telephone and opening hours
appear on educational, governmental, medical and civic types too. Choosing the accurate type costs
you nothing in coverage.</li>
<li><strong>If nothing fits precisely, go up rather than sideways.</strong>
<code>Organization</code> is true of everybody and claims nothing false; a wrong specific type is
worse than a right general one.</li>
</ul>

<h2>Reading any pasteable block an audit gives you</h2>

<ul>
<li><strong>Check every value, not the shape.</strong> The block is valid JSON-LD and will pass a
validator whatever it says about you.</li>
<li><strong>Be most suspicious of the fields that look researched</strong> — addresses,
coordinates, opening hours, prices. Those are the ones a template fills with example data.</li>
<li><strong>Treat your own domain appearing in it as neutral.</strong> It is the easiest field for
a tool to know and the one that buys the rest of the block its credibility.</li>
</ul>

<h2>When this matters most</h2>

<p>Structured data that misdescribes your organisation is not a missed opportunity — it is a
statement search engines can act on, and the consequences run from ignored markup to manual action
depending on how far the claim is from the truth. Two cases deserve care:</p>

<ul>
<li><strong>Coordinates and addresses.</strong> A wrong location claim is the one most likely to
be used and most likely to hurt.</li>
<li><strong>Types that imply regulation</strong> — medical, financial, educational. Claiming to be
a kind of organisation you are not is a different order of error from a missing property.</li>
</ul>

<h2>The fixes that make it worse</h2>

<ul>
<li><strong>Pasting the suggested block and editing later.</strong> Later does not come, and the
block is live in the meantime.</li>
<li><strong>Declaring <code>LocalBusiness</code> because the report asked for it.</strong> If you
are a university, a department or an agency, that sentence is false and the accurate type carries
the same fields.</li>
<li><strong>Adding a second type to satisfy both.</strong> Two conflicting claims are not safer
than one wrong one.</li>
</ul>

<h2>How to pass this check while saying something untrue</h2>

<p>Declare the type the report named, fill in your real address, and you are done — the finding
clears whether or not the type is accurate, because no crawler can verify what kind of
organisation you are. <strong>The check can see the shape of your claim and never its truth</strong>,
which is exactly why the recommendation has to be careful in a way the validation cannot be.</p>

<h2>Where this sits in an audit</h2>

<p>The registered check is <code>local.schema</code>, which covers local-business structured data.
For the case where the markup on your page describes businesses you list rather than your own, see
<a href="/how-to/schema-that-describes-someone-else/">the markup on your page may not be about
you &rarr;</a>. For the other ways structured data goes wrong, see
<a href="/how-to/fix-structured-data-errors/">how to fix structured data errors &rarr;</a>.</p>
"""
    return render(
        cat="how-to", slug="schema-type-is-a-claim",
        title="A schema type is a claim about what you are",
        desc=("An audit saying add LocalBusiness names a type a university does not have — and "
              "a pasteable block can put another firm's facts on your site."),
        h1="A schema type is a claim about what you are",
        crumb='<a href="/">Docket</a> / <a href="/how-to/">Fix it</a> / Schema types',
        body=body,
        faq=[
            ("Is LocalBusiness the right schema type for any organisation with an address?",
             "No. Universities, government offices, hospitals, libraries and museums all publish "
             "addresses, and none of them is a LocalBusiness in schema.org's hierarchy. The "
             "accurate type carries the same fields."),
            ("Can I use a LocalBusiness subtype for a university?",
             "There is not one. CollegeOrUniversity descends from EducationalOrganization, so "
             "advice to pick a LocalBusiness subtype offers alternatives that do not apply."),
            ("Is it safe to paste a suggested structured-data block?",
             "Only after checking every value. These blocks are valid JSON-LD whatever they say, "
             "and a tool that interpolates your real domain makes the example data below it read "
             "as researched."),
            ("What should I use if no type fits precisely?",
             "Go up rather than sideways. Organization is true of every organisation and claims "
             "nothing false, and a wrong specific type is worse than a right general one."),
            ("Does the wrong type actually cause harm?",
             "It can. Markup is read as a claim you made, so a type implying a regulated "
             "category, or a location that is not yours, is a different order of error from a "
             "missing property."),
        ],
    )


if __name__ == "__main__":
    print(schema_type())
