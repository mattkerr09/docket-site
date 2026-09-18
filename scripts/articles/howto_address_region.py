"""Where an audit looks for your address — and what happens when it looks everywhere.

Promised on the how-to hub. Sourced from `local_seo.py`, registered checks
`local.nap` and `local.schema`. One continuous story across three docstrings:

  * `_address_text` (~306): `page.text` is main content with nav, header,
    footer, aside and form STRIPPED — right for "what does this page say",
    wrong here, because THE FOOTER IS WHERE A BUSINESS PUTS ITS ADDRESS. The
    four-shape table is published verbatim in words: the only markup the check
    worked on was the least semantic one, so a site following the advice these
    reports give (`<main>`, `<footer>`) was the site that got the false
    positive.
  * `_address_key` (~1102): the fix — appending chrome — created the next bug.
    Flattened text has no punctuation between regions, so the breadcrumb ran
    into the footer address and one address published identically on every page
    was reported as thirty-one variations, with the advice to standardise on
    one format. THE FIX FOR THE BLINDNESS CREATED THE OVER-REACH.
  * `_looks_like_street_line` (~1090): "contains a digit anywhere" was not
    enough — a not-found breadcrumb reads "Home 404". The test is the FIRST
    token, digit or a unit word (suite, flat, floor, unit).
  * the rendered fold-in: a site-builder platform drawing its footer in
    JavaScript had no address anywhere the served HTML could show, and the
    report stated as fact that the business published none.

⚠️ NO SITE IS NAMED AND NO ADDRESS IS PRINTED — third-party gate plus
verify_numbers. The union is "a membership organisation", the roofing company
is "a roofing company", the fixture is "a test fixture".

⚠️ NOT A CONTRADICTION of /how-to/fix-sameas-that-claims-the-wrong-accounts/,
which says repetition separates furniture from content and position does not.
That is about deciding WHOSE a link is. This is about WHERE A TOOL LOOKS. The
page states the distinction rather than leaving it to be noticed.

Numerals: none except the allowed status code in the breadcrumb example.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from render import render  # noqa: E402


def address_region() -> Path:
    body = """
<p class="lede">Two of the strangest findings a local business gets are opposites of each other:
<em>no physical address found anywhere on the site</em>, on a site whose address is at the bottom
of every page, and <em>dozens of address variations found</em>, on a site that publishes one
address identically everywhere. They have the same cause, and the second one is what the fix for
the first one did.</p>

<h2>The region most likely to hold it was the region nothing could see</h2>

<p>Almost every content check wants the page without its furniture. Strip the navigation, the
header, the footer, the sidebar and the forms, and what is left is what the page actually says —
which is the right input for word counts, for readability, for whether a heading describes the
text beneath it.</p>

<p>It is exactly the wrong input for an address. <strong>The footer is where a business puts its
address.</strong> So the single region most likely to hold the thing being looked for was the one
region the check could not see.</p>

<p>We found this on a test fixture that carried a full street address below its copy and was told,
in plain English, that no physical address appeared anywhere on the site. Four markup shapes were
tested afterwards, and the address survived into the stripped text in exactly one of them:</p>

<table>
<tr><th>Markup</th><th>Address visible to the check</th></tr>
<tr><td>A <code>&lt;footer&gt;</code> element, page has a <code>&lt;main&gt;</code></td><td>No</td></tr>
<tr><td>A <code>&lt;footer&gt;</code> element, no <code>&lt;main&gt;</code></td><td>No — stripped as boilerplate</td></tr>
<tr><td>A plain <code>&lt;div&gt;</code> footer, page has a <code>&lt;main&gt;</code></td><td>No — outside the main container</td></tr>
<tr><td>A plain <code>&lt;div&gt;</code> footer, no <code>&lt;main&gt;</code></td><td>Yes</td></tr>
</table>

<p>Read that table again. The only markup the check worked on was the least semantic version.
<strong>A site that followed the advice these very reports hand out — use
<code>&lt;main&gt;</code>, use <code>&lt;footer&gt;</code> — was the site that got the false
positive.</strong></p>

<h2>Then it read the whole page, and the nav became part of the address</h2>

<p>The fix looks obvious: search the chrome too. It is the right fix, and it produced the opposite
failure within one release.</p>

<p>Flattened page text has no punctuation between regions. A breadcrumb ends and a footer begins
with nothing but a space between them, so the last words of your navigation and the first words of
your address are one sentence as far as any pattern is concerned.</p>

<p>Address patterns work backwards from the postcode, walking through comma-separated components.
Nothing in flattened text marks where a breadcrumb stops and a building name starts. So the first
component came back as the breadcrumb plus the building name — and because the breadcrumb differs
on every page, so did the address.</p>

<p>A membership organisation publishes exactly one address, identically, in the footer of every
page. We told it that <strong>thirty-one address variations appeared across its site</strong>, and
advised it to standardise on one exact format everywhere. It already had.</p>

<h2>What fixed it, and what the fix cost</h2>

<p>From flattened text you cannot tell where a building name begins. You can tell where the
<em>street line</em> begins, because it carries the number. So the key became everything from the
first comma-component that starts with a digit — or with a unit word, since "Suite", "Flat",
"Floor" and "Unit" start plenty of real street lines — and leading components with neither are
dropped.</p>

<p>That has a price, and it is worth naming rather than burying: <strong>a building name present on
some pages and absent on others is no longer reported as an inconsistency.</strong> Those two forms
now compare equal. That is not the mismatch this check exists for — the one that matters is a
street abbreviated one way here and another way there, or two versions of the same phone number —
and it was worth losing to stop telling a site with one address that it had thirty-one.</p>

<p>One more trap inside the fix. "Starts with a digit" is not the same as "contains a digit", and
the first version used the looser test. A breadcrumb on a not-found page reads <code>Home 404</code>
and contains one, which left false variations surviving on exactly the pages nobody looks at.</p>

<h2>Position tells you where to look, not what you found</h2>

<p>It is worth separating two questions that sound alike.</p>

<p><strong>Where should a tool look?</strong> Everywhere. Excluding a region from the search is how
you get told you have no address. The footer, the header and the navigation are all places real
facts live.</p>

<p><strong>What does the position of something tell you about it?</strong> Very little. Elsewhere
we make the case that <a href="/how-to/fix-sameas-that-claims-the-wrong-accounts/">repetition
separates a site's furniture from its content and position does not &rarr;</a>, because markup is
whatever the theme author chose. Both are true. Search the whole document; do not conclude much
from which part of it a thing turned up in.</p>

<h2>And the served HTML is not always where the address is</h2>

<p>There is a third version of the same false positive, and it is the one most likely to be live
right now on a site built with a drag-and-drop platform.</p>

<p>If the footer is drawn by JavaScript after the page loads, the address is in no document a
crawler receives from the server. A roofing company whose homepage displays its address in the
footer was told, as a statement of fact, that it published no address anywhere — and that finding
sat third in its report.</p>

<p>The answer was already in the building: a sample of pages is rendered the way a browser builds
them, and that text is folded in. If your own tooling reports an absence, the first question is
which document it read — see <a href="/how-to/javascript-seo-audit/">how to audit a JavaScript
site &rarr;</a>.</p>

<h2>Checking your own report</h2>

<ol>
<li><strong>If a tool says you have no address, look at your footer's markup.</strong> Semantic
elements are correct and worth keeping; the tool is what needs fixing. Check the rendered page
against the served HTML before believing either.</li>
<li><strong>If a tool reports many variations, read the variations it lists.</strong> If they share
a common tail and differ only at the front, you are looking at your own navigation, not at an
inconsistency.</li>
<li><strong>Count your premises before believing a count of variations.</strong> A business with
several branches has several addresses on purpose, and that is not the same finding.</li>
<li><strong>Compare the site against the listing, which is the comparison that pays.</strong> The
match between what you publish and what your business profile says is the thing this check is a
proxy for.</li>
</ol>

<h2>The fixes that make it worse</h2>

<ul>
<li><strong>Moving your address out of the footer to satisfy a tool.</strong> The footer is where
visitors look for it and where a search engine expects it.</li>
<li><strong>Deleting the building name because a report called it a variation.</strong> The report
was reading a breadcrumb. Removing real information to quiet a false finding is the most expensive
possible response to it.</li>
<li><strong>Publishing the address twice in slightly different formats</strong> so that whichever
one a tool reads, it finds something. That manufactures the exact inconsistency the check exists
to catch.</li>
<li><strong>Standardising a format that was already standard.</strong> Free, and it costs an
afternoon.</li>
</ul>

<h2>How to pass every address check while telling nobody where you are</h2>

<p>Put your address in an image. Every text-reading check on every tool goes quiet, because there
is no text to read and none of them can tell the difference between a fact expressed in pixels and
a fact that is absent. Customers cannot copy it, screen readers cannot announce it, and a search
engine cannot match it against your business listing — but the report is clean. <strong>An absence
finding is a statement about what the tool read, and that is worth remembering in both
directions:</strong> when it is wrong about you, and when it is quiet about something it never
saw.</p>

<h2>Where this sits in an audit</h2>

<p>The registered checks are <code>local.nap</code>, which compares your name, address and phone
everywhere they appear, and <code>local.schema</code>, which reads the structured-data version of
the same facts. For the case where a field is present but empty, see
<a href="/how-to/when-a-field-is-there-and-still-missing/">when a field is there and still missing
&rarr;</a>. For judging an absence finding in general, see
<a href="/learn/audit-tool-accuracy/">how to tell whether an audit tool is lying to you &rarr;</a>.
For the map-pack signals themselves, see <a href="/for/local-business/">why your business is not in
the map pack &rarr;</a>.</p>
"""
    return render(
        cat="how-to", slug="where-an-audit-looks-for-your-address",
        title="Where an audit looks for your address",
        desc=("An audit that strips page furniture cannot see the footer your address sits in "
              "— and one that reads everything called a site's single address many variations."),
        h1="Where an audit looks for your address",
        crumb='<a href="/">Docket</a> / <a href="/how-to/">Fix it</a> / Address findings',
        body=body,
        faq=[
            ("Why does an audit say my site has no address when it is in the footer?",
             "Because most content checks strip the navigation, header and footer before reading "
             "a page, and the footer is exactly where a business puts its address. Semantic "
             "markup makes it worse, not better: the stripping is what hides it."),
            ("Why am I told I have many address variations when I publish only one?",
             "Because flattened page text has no punctuation between regions, so a breadcrumb "
             "runs into the footer address and the pattern reads both as one string. A different "
             "breadcrumb on every page produces a different variation on every page."),
            ("Should I move my address out of the footer?",
             "No. The footer is where visitors look and where a search engine expects it. A tool "
             "that cannot read it is the thing that needs fixing."),
            ("Does this affect addresses drawn by JavaScript?",
             "Yes, and more severely. If a platform draws the footer after the page loads, the "
             "address is in no document the server sent, so a check reading served HTML reports "
             "it as absent. Compare the rendered page with the served HTML."),
            ("What is the address check actually for?",
             "Matching what your site publishes against your business listing. A street "
             "abbreviated one way in one place and another way elsewhere, or two versions of one "
             "phone number, weakens that match. A building name appearing on some pages and not "
             "others does not, which is why it is deliberately no longer reported."),
        ],
    )


if __name__ == "__main__":
    print(address_region())
