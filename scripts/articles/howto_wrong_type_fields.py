"""A completeness finding assumes the type you declared is the type you meant.

Promised on the how-to hub. Sourced from `structured.py`, registered check
`schema.incomplete`, two cases neither of which is covered elsewhere:

  * `_looks_like_an_organization` (~375). A property portal's homepage declared
    a `Product` node carrying name, url, logo and profile links, and no image,
    so the completeness check advised adding an image and re-testing. Right
    advice for the type; the type was wrong. `logo` is not a Product property,
    there was no offer, price or review anywhere in the block, and a Product
    carrying none of those was never going to produce a product rich result
    however many images it gained. FOLLOWING THAT ADVICE COSTS AN AFTERNOON AND
    CHANGES NOTHING. The guard needs BOTH tells — an Organization-only property
    present AND every product signal absent — so a real product missing only
    its image trips neither.
  * `_miscased` (~736). A large public-sector site's Article blocks declare
    `headLine`. JSON-LD keys are case-sensitive, so the search engine reads no
    headline and the rich result never appears. "Missing headline" is true and
    reads as false. The typo survives review because the eye reads `headLine`
    as `headline`. Case only, never spelling — `headlin`, `head-line` and
    `title` are guesses about intent.

⚠️ NO SITE OR VENDOR IS NAMED — third-party gate. The portal's own name is in
the docstring and must never be published.

⚠️ DISTINGUISH FROM /how-to/when-a-field-is-there-and-still-missing/ (532),
which is a property present with an EMPTY value. This is a property present
under a DIFFERENT NAME, and a type that should not have been asked. The page
states the difference rather than leaving a reader to trip over it.

⚠️ The two-tells principle is already published on /how-to/schema-type-is-a-claim/
(531) as "generous about applying a check, strict about what to recommend".
Cross-linked in one sentence, not re-derived.

Numerals: none. Quantities spelled as words.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from render import render  # noqa: E402


def wrong_type_fields() -> Path:
    body = """
<p class="lede">Every completeness check in every structured-data tool shares one assumption it
never states: that the type you declared is the type you meant. When that assumption fails, the
finding is still arithmetically correct — this type requires that property, you do not have it —
and the work it asks for is worth nothing. Here are the two versions of that, both of which we
shipped before we caught them.</p>

<h2>Add an image to a product that is not a product</h2>

<p>A property portal's homepage declared a <code>Product</code> node. It carried the company's
name, its address on the web, its logo and links to its profiles elsewhere. It had no image, so
the completeness check said so and advised adding one and re-testing.</p>

<p>The advice is correct for the type. The type is wrong.</p>

<p><code>logo</code> is not a property of <code>Product</code> at all. There was no offer, no price
and no review anywhere in the block. <strong>A product block with none of those was never going to
produce a product rich result however many images it gained.</strong> Someone follows that advice,
spends an afternoon wiring the logo into an image field, re-tests, and nothing has changed —
because nothing could have.</p>

<p>The block was the company's own identity markup wearing the wrong type. <strong>The defect was
one line above the one being reported.</strong></p>

<h2>Why a completeness finding cannot see this by itself</h2>

<p>A completeness check works by lookup: what does this type require, what is present, print the
difference. It is a good design, it is why these checks are reliable, and it means the type is an
input rather than something being judged.</p>

<p>So the failure is structural, not a bug in the lookup. <strong>Every required property it names
is a property you do not need, and each one looks like a small, reasonable task.</strong> That is
what makes this expensive: nothing about the finding feels wrong while you are doing it.</p>

<h2>Why the check now needs two tells before it says anything</h2>

<p>Catching this required care, because the cost of being wrong runs the other way too. A genuine
product missing only its image must not be told its type is wrong.</p>

<p>So the guard speaks only when both are true: an Organization-only property is present
<em>and</em> every product signal is absent. One tell is not enough — a real product page trips
neither, and that is the point. It is the same principle as
<a href="/how-to/schema-type-is-a-claim/">being generous about applying a check and strict about
what to recommend &rarr;</a>, applied to the fields rather than to the type.</p>

<h2>The same shape in a smaller font: one capital letter</h2>

<p>A large public-sector site declares <code>headLine</code> in its Article blocks. The property is
<code>headline</code>. JSON-LD keys are case-sensitive, so a search engine reads no headline at
all and the rich result never appears.</p>

<p>The report said "missing headline". True — and it reads as false to anyone looking at a block
that plainly contains the word. <strong>The typo survives review precisely because the eye reads
<code>headLine</code> as <code>headline</code>.</strong> That site is built by people who know
exactly what they are doing, which is the argument for catching it rather than against.</p>

<p>Told a property is missing, you go looking for something absent. Told you wrote it with a
capital letter in the middle, you are done in a minute. Same finding, same severity, same remedy —
a different sentence.</p>

<p>This is a near neighbour of a property that is present and empty, which is a different defect
with a different fix: see <a href="/how-to/when-a-field-is-there-and-still-missing/">when a field
is there and still missing &rarr;</a>. Present-but-empty means fill it in. Present-but-miscased
means rename it.</p>

<h2>What that check refuses to guess</h2>

<p>It matches on case and never on spelling. <code>headlin</code>, <code>head-line</code> and
<code>title</code> are all plausible things somebody meant by <code>headline</code>, and none of
them can be asserted. <strong>A confident wrong guess about your markup is worse than a generic
sentence</strong>, because you will act on the confident one.</p>

<p>Worth applying to any tool that offers to interpret your code: the useful ones tell you what
they measured, and go quiet where they would have to guess.</p>

<h2>Checking your own report</h2>

<ol>
<li><strong>Read the type before you read the missing fields.</strong> Ask whether the thing on
that page really is one of those. A homepage is almost never a product.</li>
<li><strong>Search your block for the property without regard to case.</strong> If it is there in
another capitalisation, that is your whole fix.</li>
<li><strong>Ask whether the rich result is even reachable.</strong> A product result needs an
offer, a price or reviews. If the block has none of those and you have no plans to add them, the
missing image is not the reason you have no rich result.</li>
<li><strong>Test the live URL, not the template.</strong> What the search engine's testing tool
says about the page you actually serve is the only verdict that counts.</li>
</ol>

<h2>When the completeness finding is exactly right</h2>

<p>Keep the severity where it belongs. A real product block on a real product page missing
<code>name</code> or <code>image</code> is a rich result you were entitled to and did not get, on
a page built to sell something. That is worth the afternoon. The point of this page is to tell
that case apart from the one where the same sentence buys you nothing.</p>

<h2>The fixes that make it worse</h2>

<ul>
<li><strong>Filling in the required fields of a type you should not have declared.</strong> The
block now makes more claims, all of them about something the page is not.</li>
<li><strong>Adding a correctly typed block and leaving the wrong one in place.</strong> Two blocks
describing the same thing as two different kinds of thing is worse than one wrong block.</li>
<li><strong>Declaring both spellings of a miscased property.</strong> One of them is ignored, you
now maintain two copies of the value, and they will diverge.</li>
<li><strong>Trusting a validator's silence.</strong> Structured-data validators check shape. A
block can be perfectly valid, perfectly complete and about the wrong kind of thing.</li>
</ul>

<h2>How to complete the markup and gain nothing</h2>

<p>Put a value in every property the report names. The finding clears, because a completeness check
counts properties and cannot ask whether anything you sell is for sale. <strong>Completeness is not
eligibility.</strong> Whether you get a rich result is decided by whether the markup describes
something the search engine shows results for — which is a question about the type, and about the
page, and never about the length of the property list.</p>

<h2>Where this sits in an audit</h2>

<p>The registered check is <code>schema.incomplete</code>, which reads structured data for required
properties. For what a type declaration claims about you, see
<a href="/how-to/schema-type-is-a-claim/">a schema type is a claim about what you are &rarr;</a>.
For two findings from this check that counted the same pages twice, see
<a href="/how-to/findings-that-double-count/">when the numbers add up to more than your site
&rarr;</a>. For the rest of the lane, see <a href="/how-to/fix-structured-data-errors/">how to fix
structured data errors &rarr;</a>.</p>
"""
    return render(
        cat="how-to", slug="completeness-findings-assume-your-type",
        title="A completeness check assumes your type is right",
        desc=("An audit told a site to add an image to a Product block that was really its "
              "company identity — the finding was true, the type was wrong, the fix changes "
              "nothing."),
        h1="A completeness check assumes your type is right",
        crumb='<a href="/">Docket</a> / <a href="/how-to/">Fix it</a> / Completeness findings',
        body=body,
        faq=[
            ("Why would adding the missing properties not fix my structured data?",
             "Because a completeness check assumes the type you declared is correct. If the "
             "block is really your organisation's identity markup declared as a product, every "
             "property it asks for belongs to something the page is not."),
            ("How do I know the type on a block is wrong?",
             "Look for properties that do not belong to it, and for the signals the type needs "
             "that are entirely absent. A product block carrying a logo, with no offer, price or "
             "review anywhere in it, is your organisation wearing the wrong label."),
            ("An audit says a property is missing but I can see it. Why?",
             "Check its capitalisation first. JSON-LD keys are case-sensitive, so headLine and "
             "headline are different properties and only one of them is read. If the spelling "
             "and case are both right, the value is probably empty, which counts as missing."),
            ("Should I add a second block with the correct type?",
             "Not while the wrong one is still there. Two blocks describing the same thing as "
             "two different kinds of thing is a worse claim than one wrong block. Correct the "
             "type in place."),
            ("Does complete markup mean I will get a rich result?",
             "No. Completeness is not eligibility. Whether a result appears depends on what the "
             "markup describes and whether the search engine shows results for that kind of "
             "thing, and a validator checks neither."),
        ],
    )


if __name__ == "__main__":
    print(wrong_type_fields())
