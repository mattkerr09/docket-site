#!/usr/bin/env python3
"""How to write meta descriptions.

Sourced from Docket's description checks (`onpage.description_missing`, `_long`, `_short` in
backend/seo_engine/checks/onpage.py, with the bounds DESC_MIN and DESC_MAX, and
`index.duplicate_descriptions` in indexability.py).

Every count, character length and quoted line of finding text comes from
data/meta-description-run.json, written by docket-app/scripts/measure_meta_description_fixture.py:
a real Docket audit of a small fixture site of ours, before and after the fix. Nothing about a
third-party site. Google's guidance was read at its own page on 2026-10-10 and is paraphrased
with the link. The two bounds are written from the same file's findings, as words in the prose.
"""
from __future__ import annotations

import datetime
import html
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from render import buy_block, render  # noqa: E402

_RUN = json.loads((Path(__file__).resolve().parent.parent.parent / "data" / "meta-description-run.json").read_text())


def _when() -> str:
    d = datetime.date.fromisoformat(_RUN["date"])
    return f"{d.day} {d.strftime('%B %Y')}"


def meta_descriptions() -> Path:
    esc = html.escape
    b, a = _RUN["before"], _RUN["after"]
    bd, ad, bl, al = _RUN["before_desc"], _RUN["after_desc"], _RUN["before_len"], _RUN["after_len"]
    miss, long_, short, dup = (b["onpage.description_missing"], b["onpage.description_long"],
                               b["onpage.description_short"], b["index.duplicate_descriptions"])
    body = f"""
<p class="lede">A meta description is the sentence under your link in search results. Google
writes its own snippet from the page most of the time, and uses yours only when it describes the
page better. So write one for every page, make each different, say what the page offers and why to
click it, and put the point in the first line. Docket reports four things: no description, one that
runs long, one that is very short, and one shared between pages.</p>

<h2>What Google says</h2>

<p>I read Google's page on this on {_when()}:
<a href="https://developers.google.com/search/docs/appearance/snippet">How to write meta
descriptions</a>. It says snippets are created mainly from the page's own content, and that Google
sometimes uses the description if it gives a more accurate picture of the page than the content
does. It says there is no limit on how long a description can be, and that the snippet is cut to
fit the device width. It says identical or similar descriptions on every page are not helpful,
and to use a site-level description on the home page and a page-level one everywhere else. If you
cannot write them all, it says to do the important pages first.</p>

<p>Two things follow. A description is not a ranking lever, so it is not worth keyword lists. And
it is your one chance to write the pitch yourself, so it is worth a plain sentence per page.</p>

<h2>What Docket reports</h2>

<ul>
<li><strong>No description.</strong> The page has the tag missing or empty.</li>
<li><strong>Too long.</strong> More than 165 wide. Widths are counted in half-width units, so a
full-width character counts twice and the same bound fits every language.</li>
<li><strong>Very short.</strong> Fewer than 70 wide.</li>
<li><strong>Shared.</strong> The same text, ignoring case, on two or more pages that carry real
content.</li>
</ul>

<p>The two bounds are Docket's own and are loose on purpose. Google sets no length, so a
description of 170 is not an error. It is a warning that the end may be cut, and that anything you
wanted a reader to see should come first.</p>

<h2>How to write one</h2>

<ol>
<li><strong>Start with what the page offers.</strong> The thing, in plain words. &ldquo;What a full
typewriter service covers&rdquo; beats &ldquo;Services&rdquo;.</li>
<li><strong>Add the reason to choose it.</strong> A fixed price, a time, what is included, what is
free. Something a reader can compare with the result above yours.</li>
<li><strong>Put the point first.</strong> The end is the part that gets cut.</li>
<li><strong>Write it for that page only.</strong> If you could paste it onto another page, rewrite
it.</li>
<li><strong>Skip the keyword lists.</strong> A sentence a person would say reads better and does
not put the page at risk of looking stuffed.</li>
</ol>

<p>On a site built from templates, a shop or a blog, write the description as a sentence with
slots, not as one fixed line: the product's name, its price, the post's author and date. Google's
own page suggests the same, for information that sits scattered through a page.</p>

<h2>A real before and after</h2>

<p>I wrote a small fixture site for this page: {a["pages"]} pages of a typewriter repair workshop. I
audited it with Docket on {_when()}, rewrote the descriptions, and audited it again. The pages are
ours; nothing here is measured on anyone else's site. Character counts are the length of the text
as written.</p>

<p>Before, the services and prices pages had no description, the about page had one of
{bl["about"]} characters, the contact page had one of {bl["contact"]}, and the ribbons and ink pages
shared one of {bl["ribbons"]}. Docket reported this, in its own words:</p>

<pre><code>{esc(miss["title"])}
{esc(miss["detail"])}

{esc(long_["title"])}
{esc(long_["detail"])}

{esc(short["title"])}
{esc(short["detail"])}

{esc(dup["title"])}
{esc(dup["detail"])}</code></pre>

<p>The fixes it printed were: <em>{esc(miss["fix"])}</em> <em>{esc(long_["fix"])}</em>
<em>{esc(short["fix"])}</em> <em>{esc(dup["fix"])}</em></p>

<p>Here are three of the rewrites. The prices page, which had none:</p>

<pre><code>{esc(ad["prices"])}</code></pre>

<p>That is {al["prices"]} characters. The about page, which ran to {bl["about"]}, now says:</p>

<pre><code>{esc(ad["about"])}</code></pre>

<p>That is {al["about"]}. And the ribbons and ink pages, which had shared one line, now each say what
is on their own page, at {al["ribbons"]} and {al["ink"]} characters:</p>

<pre><code>{esc(ad["ribbons"])}

{esc(ad["ink"])}</code></pre>

<p>Docket reported none of the four findings on the second audit.</p>

<h2>What Docket cannot tell you</h2>

<ul>
<li><strong>Whether Google will show it.</strong> Google decides per search. Your description can be
right and still not be the one on screen.</li>
<li><strong>Whether it is any good.</strong> A description can pass every check and say nothing. The
test is whether someone choosing between your result and the one above it would pick yours.</li>
<li><strong>Pixel width.</strong> It counts characters by width, not pixels, so a description of
150 made of wide letters can still be cut on a phone.</li>
</ul>

<h2>Where to start</h2>

<p>If the finding names a lot of pages, start with the ones that earn money or traffic, as Google
suggests, and write those by hand. For the rest, fix the template so every page gets a sentence made
from its own details rather than the same line. You can check one page's title and description now with
the <a href="/tools/meta-tag-checker/">free title and meta tag checker</a>, and titles have their own
guide at <a href="/how-to/write-title-tags-that-fit/">how to write title tags that fit</a>. What
Docket adds is the same check across every page, ranked with the rest; see how that compares with
<a href="/vs/">other audit tools</a>.</p>

{buy_block("howto-meta-descriptions", big=False, try_app="howto-meta-descriptions-try-free")}
"""
    return render(
        cat="how-to", slug="write-meta-descriptions",
        title="How to write meta descriptions for every page",
        desc=("Write a different description for every page, say what it offers and why to click, "
              "and put the point first. What Google says and what Docket flags."),
        h1="How to write meta descriptions",
        crumb='<a href="/">Docket</a> / <a href="/how-to/">Fix it</a> / meta descriptions',
        body=body,
        faq=[
            ("Does Google use my meta description?",
             "Sometimes. Google builds snippets mainly from the page's content and uses the description "
             "when it gives a more accurate picture of the page."),
            ("How long should a meta description be?",
             "Google sets no limit and cuts the snippet to fit the device. Docket flags more than 165 wide "
             "and fewer than 70 wide, and asks for the point to come first."),
            ("Is a meta description a ranking factor?",
             "Google's guidance describes it as a summary that can be used in the snippet, not as a "
             "ranking signal, so keyword lists in it are not worth the space."),
            ("Do I need a different description on every page?",
             "Yes where you can. Google says identical descriptions on every page are not helpful; do the "
             "important pages first if you cannot do them all."),
        ],
    )


if __name__ == "__main__":
    print(meta_descriptions())
