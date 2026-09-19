"""Telling a site's navigation from its content, and the five times we did not.

Promised on the how-to hub. Sourced from `content.py`, registered check
`content.thin` — `_reads_as_archive`, `ARCHIVE_ANCHOR_SHARE` and
`ARCHIVE_MIN_ANCHOR_WORDS`:

  * a thin page whose few words ARE its links is an index, and the remedies for
    a thin page are wrong for one. Telling the two apart is the problem.
  * counting links fails at once: an author archive carries dozens, of which two
    or three are its entries and the rest are site navigation. A RAW COUNT
    MEASURES THE TEMPLATE — "the chrome-versus-content mistake this project has
    made four times".
  * ⚠️ AND THE SHARE ALONE WALKED INTO THE SAME MISTAKE A FIFTH TIME. `prose` is
    chrome-stripped only when the markup gives the extractor something to
    recognise navigation BY. A stub carrying dozens of bare `<a>` links with no
    `<nav>` around them put every label in the body, producing a link share
    comfortably over the threshold — a genuine stub excused as an archive. The
    test written for exactly that case caught it.
  * the third discriminator: LENGTH. An anchor must carry at least four words
    before it counts as an entry rather than a label.

⚠️ NO SITE OR VENDOR IS NAMED — third-party gate. No measured numbers are
published: `verify_numbers.py` allows none of them, and the thresholds are
described rather than quoted, except the four-word rule which is a word.

⚠️ /how-to/content-audit/ owns "index pages are not thin pages" and the three
wrong remedies. This page owns the MEASUREMENT and does not restate the advice.
⚠️ /how-to/fix-sameas-that-claims-the-wrong-accounts/ owns repetition-versus-
position; /how-to/where-an-audit-looks-for-your-address/ owns the case where
stripping the region is the bug. Both are cross-linked as the other two
discriminators, not re-derived.

Numerals: none. Quantities spelled as words.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from render import render  # noqa: E402


def furniture_content() -> Path:
    body = """
<p class="lede">Every page has furniture — navigation, a header, a footer, share buttons, a cookie
line — and almost every automated judgement about what a page <em>says</em> depends on telling that
furniture from the content. It is much harder than it sounds. We have got it wrong five separate
times, in five different checks, and the fifth was in the fix for the fourth.</p>

<h2>Where it bites hardest</h2>

<p>A page with very few words is usually a problem. But a page whose few words <em>are</em> its
links is an index — an author archive, a category listing, a tag page — and the standard advice for
a thin page is wrong for one in three different ways, which
<a href="/how-to/content-audit/">a content audit &rarr;</a> sets out.</p>

<p>So before any of that advice can be given, a check has to answer a question with no obvious
handle on it: <strong>is this page short because nobody wrote it, or short because its job is to
point elsewhere?</strong></p>

<h2>Counting the links does not work</h2>

<p>The first idea is always to count links: an index has lots, a stub has few.</p>

<p>An author archive on a publisher's site carries dozens of links. Two or three of them are the
author's articles. Every other one is the site's main navigation, its footer, its section menu and
its social row — the same links on every page of the site.</p>

<p><strong>A raw link count measures the template, not the page.</strong> That is the mistake in
its plainest form, and it is the one we have made repeatedly: a measurement that is perfectly
correct about <em>the document</em> and wrong about <em>the page</em>, because the document
contains the whole site's furniture and the page is what a reader sees.</p>

<h2>So it measures share instead</h2>

<p>The better question is what proportion of the page's words sit inside links. A real index is
mostly its links — that is what makes it an index. A stub with a navigation bar is mostly not.</p>

<p>That works, and it is where the fifth mistake was waiting.</p>

<h2>The fifth time, inside the fix for the fourth</h2>

<p>Computing a share means having the page's text with the furniture already removed. Extractors do
that well — <strong>when the markup gives them something to recognise navigation by.</strong> A
navigation element, a role, a recognisable container.</p>

<p>A page that carries its links as bare anchor tags, with no navigation element around them, gives
the extractor nothing to strip. Every one of those labels lands in the body text. In the case that
caught this, a genuine stub — a page with nothing on it but a row of section links and a line of
contact detail — came out as a long run of one-word labels, which is a link share comfortably over
any threshold. <strong>An empty page was excused as an archive by the rule written to protect
archives.</strong></p>

<p>It was caught by a test written for exactly that shape, which is the only thing that catches
this: the site looked fine, the number looked right, and nothing about the output said the input
was wrong.</p>

<h2>The third discriminator, which is the one worth borrowing</h2>

<p>What finally separates a navigation label from an index entry is neither where it sits nor how
often it appears. <strong>It is how long it is.</strong></p>

<p>An anchor has to carry at least four words before it counts as an entry rather than a label.
"Home", "Contact", "About us", "Our services" never qualify. An article title, a product name, a
person's full name with a role after it — almost always do.</p>

<p>It is crude and it is the most portable of the three, because it needs no crawl and no markup
at all.</p>

<h2>Three ways to separate furniture from content</h2>

<table>
<tr><th>Test</th><th>Works when</th><th>Fails when</th></tr>
<tr><td>Repetition — it appears on many pages</td><td>You have the whole crawl to compare
against</td><td>You are looking at one page, or the furniture is nested inside content</td></tr>
<tr><td>Region — it sits inside a navigation, header or footer element</td><td>The markup is
semantic</td><td>The markup is bare, or the thing you want lives in the footer</td></tr>
<tr><td>Length — a label is short, an entry is long</td><td>Always available, needs nothing</td>
<td>The entries really are one or two words</td></tr>
</table>

<p>None is reliable alone. We use all three, in different checks, and each is a different answer to
the same question. The other two have their own pages, for the cases where each goes wrong:
<a href="/how-to/fix-sameas-that-claims-the-wrong-accounts/">why repetition beats position when you
are deciding whose a link is &rarr;</a>, and
<a href="/how-to/where-an-audit-looks-for-your-address/">why stripping the furniture is exactly
wrong when the fact you want is in the footer &rarr;</a>.</p>

<h2>Checking this on your own site</h2>

<ol>
<li><strong>When a tool calls a listing page thin, ask what it counted.</strong> If it counted
links, it counted your template.</li>
<li><strong>Look at whether your navigation is inside a navigation element.</strong> Bare anchor
tags are valid, they render identically, and they make every automated reading of your pages
worse.</li>
<li><strong>If your index entries are genuinely short</strong> — a glossary, an A to Z, a size
chart — expect tools to under-count them, and do not let a report talk you into padding them.</li>
<li><strong>Read the page with styles switched off.</strong> What you see is roughly what a
text-based reader gets, and the ratio of furniture to content becomes obvious immediately.</li>
</ol>

<h2>When this matters</h2>

<p>The severity sits on both ends and they are the same bug. Wrong in one direction, a publisher is
told at high severity to delete author pages — breaking a byline link on every article that author
wrote. Wrong in the other, a genuinely empty page is excused as an index and never fixed. A tool
that cannot tell furniture from content will do both, on the same site, in the same report.</p>

<h2>The fixes that make it worse</h2>

<ul>
<li><strong>Padding an index page with prose so it stops looking thin.</strong> Its job is to point
elsewhere; the words you add are read by nobody and dilute the links that matter.</li>
<li><strong>Removing navigation from a page to change its ratio.</strong> You have made the page
worse for people in order to make a number better.</li>
<li><strong>Deleting a short page because a report offered it as one of three options.</strong>
A deletion is not undone by noticing it was wrong, which makes it the one option to be slowest
about.</li>
</ul>

<h2>How to look like an index without being one</h2>

<p>Put a few dozen long anchor texts on a stub. Any measure of "is this page mostly links" is
satisfied by adding links, and no crawler can tell an index of real things from an index of
nothing.</p>

<p>Which is the honest limit: <strong>these rules recognise the shape of an index, never its
usefulness.</strong> Whether the things listed are worth reaching is a judgement about your site
that no tool makes, and it is the only question that decides whether the page should exist.</p>

<h2>Where this sits in an audit</h2>

<p>The registered check is <code>content.thin</code>, which reports pages with very little content
and reports index pages separately. For what to do with the list it gives you, see
<a href="/how-to/content-audit/">how to run a content audit &rarr;</a>.</p>
"""
    return render(
        cat="how-to", slug="telling-furniture-from-content",
        title="Telling your site's furniture from its content",
        desc=("An audit that reads a site's navigation as its content will excuse an empty page "
              "as an index — the same confusion made five times, and the three ways out of it."),
        h1="Telling your site's furniture from its content",
        crumb='<a href="/">Docket</a> / <a href="/how-to/">Fix it</a> / Furniture or content',
        body=body,
        faq=[
            ("Why does an audit call my category or author page thin?",
             "Because it is short, which is true. The question is whether it is short because "
             "nobody wrote it or short because its job is to point elsewhere — and the advice "
             "for the first is wrong for the second in three different ways."),
            ("Why is counting links a bad way to recognise an index page?",
             "Because a raw count measures your template. An author archive carries dozens of "
             "links of which two or three are its entries; the rest are the same navigation and "
             "footer links that appear on every page of the site."),
            ("Does semantic markup change how tools read my pages?",
             "Yes, more than most people expect. Navigation inside a navigation element can be "
             "recognised and set aside. The same links as bare anchor tags land in the page's "
             "body text, and every measurement of what the page says is then wrong."),
            ("What separates a navigation label from a real index entry?",
             "Length is the most portable test. Ours requires an anchor to carry at least four "
             "words before it counts as an entry — enough to exclude Home, Contact and About us, "
             "and to include almost any article or product title."),
            ("Can a tool tell whether my index page is any good?",
             "No. These rules recognise the shape of an index, never its usefulness. Whether the "
             "things it lists are worth reaching is a judgement about your site, and it is the "
             "only question that decides whether the page should exist."),
        ],
    )


if __name__ == "__main__":
    print(furniture_content())
