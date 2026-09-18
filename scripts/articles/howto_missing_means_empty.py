""""Missing" is the word a reader greps for — and sometimes finds.

Promised on the how-to hub. Sourced from `local_seo.py`, registered checks
`local.schema` and `local.nap`, whose docstrings record the two halves:

  * `local.schema` tests `not node.get(...)`, which is right — an empty value
    feeds a search engine exactly as much as an absent key. But the sentence
    said "Missing: image" to a reader whose markup plainly contained `image`,
    with an empty string in it. The fact-check of that case nearly filed a
    false-positive report AGAINST A CORRECT FINDING. The finding now names the
    empty ones as empty: same count, same remedy, one extra clause.
  * `local.nap`'s phone branch read `tel:` hrefs and text patterns only, while
    its sibling address branch had always read prose AND PostalAddress schema.
    So a business publishing its number as `telephone` in JSON-LD — the
    property Google's own LocalBusiness documentation asks for — was told it
    had no phone number. The LocalBusiness node is what switches the whole lane
    on, so the block that ENABLED the check contained the answer the check then
    called missing.
  * third beat: the report's label is not always the key. "geo coordinates or
    hasMap" is one label over two keys, so grepping the finding's own words
    finds nothing even when the finding is right.

⚠️ NO SITE IS NAMED and NO NUMBER IS QUOTED — third-party gate. The measured
phone number stays out; it is described, never printed.

⚠️ DOES NOT DUPLICATE /learn/audit-tool-accuracy/, which asks what the crawl
SAW (blocked, rate-limited, unrendered). This page is the case where the field
is present in the document the tool read.

Numerals: none. Quantities spelled as words.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from render import render  # noqa: E402


def missing_means_empty() -> Path:
    body = """
<p class="lede">A report says a field is missing. You open your markup, search for the field, and
there it is. At that moment most people conclude the tool cannot read their site and stop
believing the rest of the report — which is the expensive part, because the finding is usually
right and the report is usually wrong about how it said so.</p>

<h2>The field that is there and still missing</h2>

<p>We check local-business structured data for the properties that feed a local result: address,
telephone, opening hours, coordinates, url, image, price range. The test asks whether the property
has a value, not whether the key exists — which is correct. An empty value feeds a search engine
exactly as much as an absent key does, namely nothing.</p>

<p>But the sentence we printed said <em>Missing: image</em>. And on a dental practice page we
measured, the markup contained this:</p>

<pre><code>"image": ""</code></pre>

<p>Put yourself in the reader's chair. You search your own source for <code>image</code>, you find
it, and the tool has just told you it is not there. Everything else in that report now has a
question mark over it.</p>

<p><strong>This one caught us.</strong> Fact-checking that very case, we listed the node's keys,
saw <code>image</code> among them, and came within a step of filing a false-positive report
against a finding that was entirely correct.</p>

<p>The fix was not to the test — the test was right. The finding now says which half of "missing"
you are looking at: the empty ones are named as present-but-empty, with the note that a search
engine reads that the same as absent. Same finding, same count, same remedy. One clause, and the
reader stops arguing with the tool and starts filling in the field.</p>

<h2>The half where the tool really was wrong</h2>

<p>The other half is the one that earns the suspicion, and it is worth understanding because it is
the most common way a good check goes blind.</p>

<p>One fact can have two representations. A phone number can be a <code>tel:</code> link in the
page, or the <code>telephone</code> property of a structured-data block, or both. Our NAP check
read the first and not the second.</p>

<p>So a business that published its number exactly the way the search engine's own local-business
documentation asks for it was the business most likely to be told it had no phone number at all.
<strong>Following the guidance precisely was what triggered the finding.</strong></p>

<p>Two details make it worse. The address branch of the same check had always read both the
visible prose and the <code>PostalAddress</code> in the markup — the rule existed, ten lines away,
in the same function. And the structured-data block is the thing that switches the entire
local-business lane on, so <em>the block that enabled the check contained the answer the check then
called missing.</em></p>

<h2>The label in the report is not the key in your markup</h2>

<p>A smaller trap, and the reason a search can come back empty when nothing is wrong with the
finding. Some report labels cover more than one property. Ours names "geo coordinates or hasMap"
as one item, because either satisfies it — so searching your markup for that phrase finds nothing,
forever, in every site that has ever been audited.</p>

<p>When a label reads like prose rather than like a property name, it is a label. Search for the
properties it mentions, separately.</p>

<h2>How to tell the two apart in half a minute</h2>

<ol>
<li><strong>Find the key, then look at its value.</strong> Present with an empty string, an empty
array, an empty object, or a value of <code>null</code> is the same as absent for every consumer
that matters. The report is right and it is telling you something useful.</li>
<li><strong>Check whether the fact lives somewhere the tool did not look.</strong> Visible text and
structured data are different documents. If your value is only in one and the finding is about the
other, the tool has a blind spot and you have found it.</li>
<li><strong>Check that you searched for the property and not the label.</strong></li>
<li><strong>Check whether the tool saw the page at all.</strong> A blocked, rate-limited or
unrendered crawl produces "missing" for everything, and that is a different problem —
<a href="/learn/audit-tool-accuracy/">how to tell whether an audit tool is lying to you
&rarr;</a>.</li>
</ol>

<h2>When this does not matter</h2>

<p>If the property genuinely is not there, none of the above applies and the finding is simply a
task. The reading skill only pays off when the report and your own eyes disagree, and the whole
point of it is to stop that disagreement from costing you the rest of the report.</p>

<h2>The fixes that make it worse</h2>

<ul>
<li><strong>Deleting the empty key so the markup agrees with the report.</strong> The finding was
not about tidiness. Removing <code>"image": ""</code> changes nothing a search engine can use;
putting an image URL in it does.</li>
<li><strong>Adding a second copy of the fact in the format the tool reads.</strong> If your number
is in structured data and a tool wants it as a link, publishing both in slightly different formats
is how a consistency problem gets created out of nothing — and name, address and phone matching
across every place they appear is its own ranking signal. Publish it twice only if it is byte
for byte the same twice.</li>
<li><strong>Filling a field with a placeholder to clear the line.</strong> A dash in the price
range field satisfies every check that asks whether the field has a value.</li>
<li><strong>Discarding the report over one line.</strong> The failure mode this page exists to
prevent. One badly worded finding is evidence about the wording.</li>
</ul>

<h2>How to pass this check without saying anything</h2>

<p>Every one of these field tests asks whether a value is present, and none of them can ask whether
it is true. A single character in the price range field clears it. A logo in the image field clears
it whether or not the logo is the image a search engine would want. <strong>A completeness check
counts fields; it cannot read them.</strong> That is worth knowing in both directions — it is why
the finding is cheap to clear dishonestly, and why clearing it honestly is worth more than the
finding says.</p>

<h2>Where this sits in an audit</h2>

<p>The registered checks are <code>local.schema</code>, which reads local-business structured data,
and <code>local.nap</code>, which compares your name, address and phone across the site. For what
the type declaration itself claims, see <a href="/how-to/schema-type-is-a-claim/">a schema type is
a claim about what you are &rarr;</a>. For the number beside a finding, see
<a href="/how-to/check-the-count-on-a-finding/">check the count on a finding &rarr;</a>. For the
rest of structured data, see <a href="/how-to/fix-structured-data-errors/">how to fix structured
data errors &rarr;</a>.</p>
"""
    return render(
        cat="how-to", slug="when-a-field-is-there-and-still-missing",
        title="When a field is there and still missing",
        desc=("An audit can call a field missing when your markup holds it empty — and it once "
              "called a phone number missing because it read half of the site's markup."),
        h1="When a field is there and still missing",
        crumb='<a href="/">Docket</a> / <a href="/how-to/">Fix it</a> / Missing fields',
        body=body,
        faq=[
            ("Why does an audit say a field is missing when I can see it in my markup?",
             "Usually because the key is present with an empty value. An empty string, empty "
             "array or null feeds a search engine exactly as much as an absent property, so a "
             "completeness check counts it as missing — correctly."),
            ("Is an empty property the same as no property?",
             "For every consumer that matters, yes. It is worth filling in rather than deleting: "
             "removing the empty key changes nothing, giving it a value changes what a search "
             "engine can show."),
            ("Why was my phone number reported missing when it is in my structured data?",
             "Because a check can read one representation of a fact and not the other. Ours read "
             "tel: links and page text and not the telephone property, so sites following the "
             "local-business documentation exactly were the ones reported as having no number. "
             "It reads both now."),
            ("I searched my markup for the field the report named and found nothing. Is it wrong?",
             "Check whether you searched for a label rather than a property. Some report labels "
             "cover two properties at once, such as coordinates or a map link, and that phrase "
             "appears in no site's markup."),
            ("Should I trust a report that gets one finding's wording wrong?",
             "Read it as evidence about the wording, not about the check. The most useful "
             "question is what the tool actually saw: a blocked or unrendered crawl makes every "
             "absence unsupported, while a badly phrased finding is usually still true."),
        ],
    )


if __name__ == "__main__":
    print(missing_means_empty())
