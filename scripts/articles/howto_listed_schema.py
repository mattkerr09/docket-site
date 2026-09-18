"""The markup on your page may not be about you.

Promised on the how-to hub. Sourced from `local_seo.py` — registered checks
`local.schema` and `local.applicable` — whose docstrings record a marketplace
being told its own address, telephone, opening hours, geo and price range were
missing, when every one of those facts was about a takeaway it listed.

  * A JSON-LD walker descends every value at any depth deliberately, because
    most real schema is a single `@graph`. But the walk has no idea whose
    business it just found, and `itemListElement` is the one property whose
    entries are by definition the things a page LISTS rather than the thing a
    page IS.
  * The sibling error: "Restaurant markup on <url>" was literally true and read
    to the owner as "this tool thinks we are a restaurant".
  * The repair kept the finding and changed its subject — listing markup is
    what makes a listing page eligible for rich results, so it is still
    reported, attributed to the businesses it describes.
  * The evidence note worth keeping: six chain store-locators were checked for
    the nested-own-branches case and none did it — "none of six is a reason to
    keep the finding cheap, not a reason to delete it".

⚠️ NO SITE OR CHAIN IS NAMED — third-party gate.

⚠️ Nothing on the site covers `itemListElement` today; checked before writing.

Numerals: none. Quantities spelled as words.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from render import render  # noqa: E402


def listed_schema() -> Path:
    body = """
<p class="lede">An audit reports that your address, telephone number, opening hours and price
range are missing from your structured data — and that two of them are present in the markup but
carry no value. You check the page. None of those facts was ever about you. They were about a
takeaway in another city that your page happens to list.</p>

<h2>Why a reader of your markup loses track of whose it is</h2>

<p>Structured data is nested, and a tool that only looks at the top level finds almost nothing —
most real markup is a single graph with everything inside it. So a JSON-LD reader descends through
every value at any depth. That is the right decision and it is why these tools work at all.</p>

<p><strong>But a walk like that has no idea whose business it just found.</strong> It sees a node
with a type it recognises and treats it as yours.</p>

<p>There is exactly one property that settles the question, and it is in the vocabulary already:
<code>itemListElement</code>. Its entries are, by schema.org's own definition, the things a page
<em>lists</em> — not the thing the page <em>is</em>. Anything reached through it belongs to somebody
else.</p>

<h2>What that produced</h2>

<p>On a national food-delivery marketplace, the only structured data on the page was a list of
restaurant nodes — other people's takeaways, each carrying an empty address string and an empty
price range. The check judged the first node it reached and reported that the <em>marketplace's</em>
address, telephone, opening hours, geolocation and price range were missing, and that two fields
were present but blank.</p>

<p>Every one of those statements was about a shop the marketplace does not own, in a town it does
not operate from. There was nothing for the reader to fix, and no way to tell that from the
finding.</p>

<h2>True, and still misleading</h2>

<p>The same site produced a second sentence worth studying separately, because it was not wrong.</p>

<p>Deciding whether the local-business checks apply at all, the tool said it had found
<em>restaurant markup on this URL</em>. That is literally correct — the markup is there, and it is
restaurant markup. It reads to the owner as <strong>"this tool thinks we are a restaurant"</strong>,
which is not what was meant and not true.</p>

<p>The lane genuinely does apply: a site that lists local businesses has local-schema work to do.
<strong>But the reason given for applying it has to be the reason that is actually true.</strong> A
correct sentence that invites a wrong inference costs the same as a wrong one.</p>

<h2>The repair kept the finding and changed its subject</h2>

<p>The obvious fix — ignore anything inside a list — would have been wrong, and this is the part
worth copying.</p>

<p>Thin listing markup <em>is</em> a real finding. Complete entries are what make a listing page
eligible for rich results, so a list of businesses with empty addresses is a genuine missed
opportunity. It is simply not a statement about the publisher. So the finding stayed and its
subject changed: it now describes the businesses the page lists, rather than the page's own
premises.</p>

<p>And dropping it outright would have silenced a real case — a chain that publishes its own
branches inside a list on its store locator.</p>

<h2>The sentence about evidence</h2>

<p>Six chain store locators were checked for exactly that shape, and none of them nests
business-type nodes inside a list. That is a useful result and it is not a licence:
<strong>"none of six" is a reason to keep a finding cheap, not a reason to delete it.</strong></p>

<p>It is worth saying because the opposite reasoning is everywhere in tooling — a small sample
that finds nothing gets treated as proof that nothing exists, and a rule is removed on the strength
of not having seen the case yet.</p>

<h2>Reading this on your own report</h2>

<ul>
<li><strong>Ask whose data is missing.</strong> If the finding names fields you would never publish
about yourself — a price range for a company that is not a venue, opening hours for a
marketplace — the node is probably not yours.</li>
<li><strong>Look for a list in your markup.</strong> Search the page source for
<code>itemListElement</code>. Anything under it describes something you are listing.</li>
<li><strong>Check whether the empty strings are yours.</strong> A node with empty values is
usually a template that ran with no data for one entry, which is a different job from missing
markup.</li>
<li><strong>Ask whether the page is one business or many.</strong> Directories, locators,
marketplaces and category pages are the shapes where this goes wrong.</li>
</ul>

<h2>When it matters, and to whom</h2>

<p>Two readers should act on a listing-markup finding, and they should do different things:</p>

<ul>
<li><strong>A publisher of a directory or marketplace.</strong> Complete entries are the point —
empty address and price fields on listed businesses cost the listing page its eligibility, and the
data usually exists in the database behind the page.</li>
<li><strong>A chain publishing its own branches in a list.</strong> Here the nodes really are
yours, and incomplete ones are a genuine local-SEO defect on premises you operate.</li>
</ul>

<p>Everyone else can read it as information about their listings rather than a defect in their own
entity.</p>

<h2>The fixes that make it worse</h2>

<ul>
<li><strong>Adding your own address to a node that describes someone else.</strong> You have now
published a false claim about a third party's premises in machine-readable form.</li>
<li><strong>Deleting the list markup to clear the finding.</strong> The list is the thing that
makes the page eligible for anything. Complete it instead.</li>
<li><strong>Adding a local-business node for your company to a page that is not premises.</strong>
A marketplace is not a shopfront, and claiming to be one is the misrepresentation that structured
data is policed for.</li>
</ul>

<h2>How to clear this without improving anything</h2>

<p>Remove <code>itemListElement</code> and leave the entries loose in the graph. The nodes are
still there, the tool can no longer tell they are listings, and it will go back to treating them as
yours — the finding changes shape rather than disappearing, and you have thrown away the one
signal that made the page legible.</p>

<p><strong>The property that got you a confusing finding is the property that makes the page
readable at all.</strong></p>

<h2>Where this sits in an audit</h2>

<p>The registered checks are <code>local.schema</code>, which covers local-business structured
data, and <code>local.applicable</code>, which decides whether the local lane applies to your site
at all. For the other ways structured data misleads, see
<a href="/how-to/fix-structured-data-errors/">how to fix structured data errors &rarr;</a>; for the
related case of a node that is a pointer rather than a definition, see
<a href="/how-to/schema-id-references/">an @id is a pointer, not a definition &rarr;</a>.</p>
"""
    return render(
        cat="how-to", slug="schema-that-describes-someone-else",
        title="The markup on your page may not be about you",
        desc=("A listing page's schema describes other businesses. Why an audit told a "
              "marketplace its own address was missing from its site."),
        h1="The markup on your page may not be about you",
        crumb='<a href="/">Docket</a> / <a href="/how-to/">Fix it</a> / Listed businesses',
        body=body,
        faq=[
            ("Why does my audit say my address is missing when I have no premises?",
             "Because it probably read a node describing a business your page lists. Anything "
             "reached through itemListElement is something you are listing rather than something "
             "you are."),
            ("What is itemListElement?",
             "The schema.org property whose entries are the things a page lists. It is the one "
             "signal that separates markup about you from markup about everybody else on the "
             "page."),
            ("Should I remove structured data that describes other businesses?",
             "No. Complete entries are what make a listing page eligible for rich results. Fill "
             "the empty fields rather than deleting the list."),
            ("My store locator lists my own branches. Does this apply to me?",
             "The nodes really are yours, so incomplete ones are a genuine defect on premises you "
             "operate. That case is exactly why listing markup is still reported rather than "
             "ignored."),
            ("Is it safe to add my company as a local business on a listings page?",
             "Not unless the page describes premises the public visits. Claiming to be a "
             "shopfront you do not have is the kind of misrepresentation structured data is "
             "policed for."),
        ],
    )


if __name__ == "__main__":
    print(listed_schema())
