"""A check that matches a type NAME cannot see a type that inherits from it.

Promised on the how-to hub. Sourced from `ai_visibility.py`, registered check
`ai.entity` (finding id `ai.no_sameas`):

  * a consultancy publishes business markup carrying seven `sameAs` entries,
    including the profiles anyone would name first, and was told "Your
    Organization schema does not link out to any external profile." The check
    asked `json_ld_nodes` for three literal type names; `ProfessionalService`
    is a `LocalBusiness` is an `Organization` BY INHERITANCE, and matching the
    base name alone sees none of the dozens of subtypes.
  * THE FINDING FIRES HARDEST ON THE CUSTOMER WHO DID THE WORK — no schema at
    all gives a true finding; precise markup gives "you did nothing" — and it
    sits near the top of the action plan.
  * `IDENTITY_TYPES` existed in `schemaorg` all along and its own comment states
    the rule. `structured.py` consults it; this did not. THIRD INSTANCE of a set
    living in another file and not being read.
  * the deliberate counterpart, which looks the same and is the opposite: when
    no identity is found at all this check RETURNS SILENTLY, because
    `schema.no_identity` already reports it at HIGH and re-reporting would
    double-count in the score. Overlapping is fine; disagreeing is not.

⚠️ NO SITE OR VENDOR IS NAMED — third-party gate. The consultancy is "a
consultancy"; the profiles are described, never named.

⚠️ DISTINGUISH FROM /how-to/schema-type-is-a-claim/ (531), which is about the
type you SHOULD declare. This is a tool failing to recognise a type correctly
declared — and being more specific is what tripped it. Said on the page.

⚠️ SAME COMMIT corrects /learn/sameas-entity-signals/, whose checklist says to
put the array "inside your Organization node" without noting that a subtype is
an Organization node.

Numerals: none. Quantities spelled as words.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from render import render  # noqa: E402


def type_matching() -> Path:
    body = """
<p class="lede">The worst finding an audit can produce is not a wrong one. It is one that is wrong
specifically about the people who did the work properly — where doing the job carefully is the
thing that trips it. This is that finding, and the cause is a single word being compared as a
word.</p>

<h2>Seven profile links, and a report saying none</h2>

<p>A consultancy publishes business markup on its site with seven <code>sameAs</code> entries in
it, including the professional profiles anyone would name first. Good markup, done deliberately,
of exactly the kind every guide asks for.</p>

<p>The report said:</p>

<blockquote><p>Your Organization schema does not link out to any external profile.</p></blockquote>

<p>That sits near the top of the action plan, so it is among the first things a reader sees — a
flat contradiction of their own file, in the section that says what to do first.</p>

<h2>The check was looking for a word, not a thing</h2>

<p>Schema.org types inherit. A <code>ProfessionalService</code> <em>is</em> a
<code>LocalBusiness</code>, which <em>is</em> an <code>Organization</code>. That is not a
resemblance; it is the structure of the vocabulary, and anything that understands it treats the
specific type as the general one wherever the general one is expected.</p>

<p>Our check asked for three type names and compared the declared type against those strings. A
site declaring the accurate, more specific type matched none of them — and there are dozens of
such subtypes.</p>

<p>Read that against who it hits. <strong>A site with no business markup at all got a true
finding. A site that marked its business up precisely got told it had done nothing.</strong> The
more exactly somebody followed the vocabulary, the more certainly the check went blind.</p>

<h2>Two checks in one product, disagreeing about one site</h2>

<p>The structured-data lane asks the same question — does this site declare a business identity? —
and got it right on the same file. It consults a shared list of identity types whose own comment
states the rule plainly: every subtype qualifies, because each one <em>is</em> the base type by
inheritance.</p>

<p>That list had existed all along, in the same codebase, for exactly this purpose. The check
above it simply did not read it. <strong>The knowledge was not missing; it was in another
file.</strong></p>

<h2>The deliberate half, which looks identical and is the opposite</h2>

<p>Worth separating, because "two checks are about the same thing" is not automatically a fault.</p>

<p>When no business identity is found at all, this check now says nothing. Not because it has no
view, but because the structured-data lane already reports that at high severity, and reporting
the same defect twice would take two bites out of one score for one fix. That deference is
designed.</p>

<p><strong>Two checks overlapping is fine. Two checks disagreeing is the bug.</strong> If a report
describes the same page two different ways, one of them is reading something the other is not, and
that is the thing to chase — see <a href="/how-to/findings-that-double-count/">when the numbers add
up to more than your site &rarr;</a> for the arithmetic version of the same problem.</p>

<h2>This is not the same as declaring the wrong type</h2>

<p>Elsewhere we make the case that <a href="/how-to/schema-type-is-a-claim/">a schema type is a
factual claim about what you are &rarr;</a>, and that picking a type you do not have is a real
error. Both are true and they point in opposite directions for a tool:</p>

<ul>
<li><strong>Choosing your type:</strong> be accurate, and prefer the specific one that genuinely
describes you.</li>
<li><strong>Reading someone's type:</strong> accept every type that inherits from the one you were
looking for, because the specific one is the general one.</li>
</ul>

<p>The failure here was the second, caused by people doing the first correctly.</p>

<h2>Checking your own report</h2>

<ol>
<li><strong>When a finding says your markup lacks something you can see, look at the type
first.</strong> If you declared a specific business type and the finding names the generic one,
that is the signature.</li>
<li><strong>Search your markup for the property, not for the type name.</strong> The property is
what matters; the type is what the tool was matching on.</li>
<li><strong>Look for the same question answered elsewhere in the report.</strong> If one lane says
you have business markup and another says you do not, you have found a disagreement rather than a
defect.</li>
<li><strong>Validate with the search engine's own testing tool.</strong> It resolves inheritance,
because it is the parser that actually decides.</li>
</ol>

<h2>When the finding is real</h2>

<p>Keep the weight where it belongs. If <code>sameAs</code> genuinely is absent, a model has a
string where it could have had a resolved entity — it cannot connect your site to the business it
already knows about from a professional profile or a reference database. It is among the cheapest
things on any list to fix, which is exactly why a false version of it is expensive: it spends the
credibility of a finding people would otherwise act on.</p>

<h2>The fixes that make it worse</h2>

<ul>
<li><strong>Changing your accurate specific type to the generic one to satisfy a tool.</strong>
You would be making your markup less true so a report goes quiet. The tool is the thing that is
wrong.</li>
<li><strong>Adding a second, generic node beside the specific one.</strong> Now two blocks
describe one organisation, and anything reading them has to decide which you meant.</li>
<li><strong>Filling the array to clear the line.</strong> Profiles you do not control are a claim
about somebody else's accounts —
<a href="/how-to/fix-sameas-that-claims-the-wrong-accounts/">whose accounts are in your sameAs
&rarr;</a>.</li>
</ul>

<h2>How to satisfy this check without being findable</h2>

<p>Put any plausible URLs in the array. Nothing in a crawl verifies that a profile is yours, so
the finding clears on the presence of links rather than on the existence of an entity.
<strong>The check can see that you pointed somewhere; it cannot see whether anything points
back.</strong> Which is the actual job — the value is in the profiles being real, being yours and
carrying the same name, and no audit can confirm any of that from your markup alone.</p>

<h2>Where this sits in an audit</h2>

<p>The registered check is <code>ai.entity</code>, which asks whether a model can resolve your site
to a business it already knows. For what the property does and which URLs belong in it, see
<a href="/learn/sameas-entity-signals/">sameAs and entity signals &rarr;</a>. For the type
declaration itself, see <a href="/how-to/schema-type-is-a-claim/">a schema type is a claim about
what you are &rarr;</a>.</p>
"""
    return render(
        cat="how-to", slug="when-a-check-cannot-see-your-markup",
        title="When a check cannot see the markup you wrote",
        desc=("An audit told a consultancy its schema linked to no profiles while seven sat in "
              "the file — the check matched a type name literally and never saw the site's "
              "subtype."),
        h1="When a check cannot see the markup you wrote",
        crumb='<a href="/">Docket</a> / <a href="/how-to/">Fix it</a> / Type matching',
        body=body,
        faq=[
            ("Why does an audit say I have no Organization schema when I do?",
             "Check which type you declared. Schema.org types inherit, so a specific business "
             "type is an Organization — but a tool comparing the declared type against a list of "
             "names will miss every subtype. Declaring the accurate type is what trips it."),
            ("Should I change my schema type to Organization so tools recognise it?",
             "No. That makes your markup less accurate so a report goes quiet. The specific type "
             "is correct and carries the same properties; the tool is what needs fixing."),
            ("Two findings in one report disagree about my site. Which is right?",
             "Whichever one is reading more of your markup. A disagreement means the two checks "
             "match on different things — usually one accepts inherited types and the other "
             "compares names. Validate with the search engine's own tool, which resolves "
             "inheritance."),
            ("Is it a problem that two checks cover the same thing?",
             "Overlap is fine and often deliberate: one of ours stays silent when another lane "
             "already reports the same defect, so a single fix does not cost the score twice. "
             "Disagreement is the problem, not overlap."),
            ("Does a full sameAs array prove anything?",
             "Not by itself. Nothing in a crawl checks that a profile is yours or that it points "
             "back, so the finding clears on the presence of links. The value comes from the "
             "profiles being real, being yours and carrying the same name."),
        ],
    )


if __name__ == "__main__":
    print(type_matching())
