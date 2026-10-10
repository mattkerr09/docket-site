#!/usr/bin/env python3
"""How to fix vague and empty link text.

Sourced from Docket's `onpage.anchors` (backend/seo_engine/checks/onpage.py), the phrase
list in registry.py (`_MEANINGLESS_ANCHORS`, written out below exactly as it stands) and
the accessible-name fallback in extract.py (`_accessible_name`: aria-label, then a wrapped
image's alt, then an inline SVG's title; `alt=""` is not a name).

Every count and every quoted line of finding text comes from data/anchor-text-run.json,
written by docket-app/scripts/measure_anchor_text_fixture.py: a real Docket audit of a
small fixture site of ours, before and after the fix. Nothing about a third-party site.
Google's guidance was read at its own page on 2026-10-10 and is paraphrased with the link.
"""
from __future__ import annotations

import datetime
import html
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from render import buy_block, render  # noqa: E402

_RUN = json.loads((Path(__file__).resolve().parent.parent.parent / "data" / "anchor-text-run.json").read_text())

#: The phrases the check treats as vague, in the order the registry holds them.
_PHRASES = ("click here", "here", "read more", "more", "learn more", "this", "link", "this page",
            "continue", "details", "info", "more info", "see more", "go", "download", "view",
            "read", "click", "find out more")


def _when() -> str:
    d = datetime.date.fromisoformat(_RUN["date"])
    return f"{d.day} {d.strftime('%B %Y')}"


def link_text() -> Path:
    esc = html.escape
    vague, empty = _RUN["before"]["onpage.anchor_vague"], _RUN["before"]["onpage.anchor_empty"]
    phrases = ", ".join(f"<code>{esc(p)}</code>" for p in _PHRASES)
    body = f"""
<p class="lede">Link text should say where the link goes. &ldquo;Click here&rdquo; and &ldquo;read
more&rdquo; say nothing about the page behind them, to a visitor skimming, to a screen reader
reading out a list of links, or to Google. The fix is to rewrite each one as the name of its
destination, and to give every link that holds only an icon a name of its own.</p>

<h2>Why the words matter</h2>

<p>Google's own guidance, which I read on {_when()}, puts it this way: good anchor text is
descriptive, reasonably concise, and relevant to both the page it sits on and the page it links
to. It lists &ldquo;click here&rdquo; and &ldquo;read more&rdquo; as examples of text that is too
generic. It also gives a test worth borrowing: read only the anchor text, out of context, and ask
whether you could tell what the page is about. The page is
<a href="https://developers.google.com/search/docs/crawling-indexing/links-crawlable">Link best
practices for Google</a>.</p>

<p>People hit the same wall. Screen readers can read out every link on a page as a list, with the
sentences around them removed. A list that says &ldquo;read more, read more, click here&rdquo; is
no use to the person listening. The Web Content Accessibility Guidelines ask that a link's purpose
be clear from its text together with its surrounding sentence (success criterion 2.4.4), and
descriptive text meets that without making anyone read around it.</p>

<h2>What Docket reports</h2>

<p>Two findings, from the same check.</p>

<p><strong>Vague link text.</strong> A link is counted when its whole text is one of these
phrases: {phrases}. Docket lowercases the text and trims spaces and the marks
<code>. ! &rarr; &gt; &raquo; &rsaquo; -</code> from the ends first, so &ldquo;Read more
&raquo;&rdquo; counts. It counts every link on every indexable page it crawled, except addresses that start
with <code>#</code>, <code>javascript:</code>, <code>mailto:</code> or <code>tel:</code>. It
reports from the first one it finds.</p>

<p><strong>Links with no text.</strong> A link with no words gets a name from, in order, its
<code>aria-label</code>, the <code>alt</code> of an image inside it, or the <code>title</code> of
an inline SVG inside it. One with none of those is counted as empty, and the finding appears when
more than three are found. An image with <code>alt=""</code> is not a name: that is how a
decorative image is hidden from assistive technology, so a link holding only that has nothing to
announce.</p>

<h2>The fix, pattern by pattern</h2>

<p><strong>A card that ends in &ldquo;Read more&rdquo;.</strong> The card already has a heading
that names the destination. Make the heading the link and delete the extra one.</p>

<pre><code>&lt;h2&gt;Servicing&lt;/h2&gt;
&lt;p&gt;A full clean, oil and ribbon.&lt;/p&gt;
&lt;a href="/services.html"&gt;Read more&lt;/a&gt;

&lt;h2&gt;&lt;a href="/services.html"&gt;Typewriter servicing&lt;/a&gt;&lt;/h2&gt;
&lt;p&gt;A full clean, oil and ribbon.&lt;/p&gt;</code></pre>

<p><strong>A sentence built around &ldquo;click here&rdquo;.</strong> Move the link onto the
words that name the thing, and cut &ldquo;click here&rdquo; from the sentence.</p>

<pre><code>&lt;a href="/prices.pdf"&gt;Click here&lt;/a&gt; for the price list.

Read the &lt;a href="/prices.pdf"&gt;price list (PDF)&lt;/a&gt;.</code></pre>

<p><strong>A link that holds only an icon.</strong> Give the link a name with
<code>aria-label</code>, and mark the icon decorative so it is not announced twice.</p>

<pre><code>&lt;a href="/contact.html"&gt;&lt;img src="/img/mail.svg"&gt;&lt;/a&gt;

&lt;a href="/contact.html" aria-label="Email the workshop"&gt;&lt;img src="/img/mail.svg" alt=""&gt;&lt;/a&gt;</code></pre>

<p><strong>A button-style link that says &ldquo;Download&rdquo;, &ldquo;View&rdquo; or
&ldquo;Continue&rdquo;.</strong> Add the object: &ldquo;Download the price list&rdquo;, &ldquo;View
the order&rdquo;, &ldquo;Continue to payment&rdquo;. Keep it short. Google warns against anchor text
that runs on for a whole sentence as well.</p>

<h2>A real before and after</h2>

<p>I wrote a small fixture site for this page: five pages of a typewriter repair workshop. I
audited it with Docket on {_when()}, rewrote the links, and audited it again. The pages are
ours; nothing here is measured on anyone else's site.</p>

<p>Before, the home page had four cards ending in &ldquo;Read more&rdquo;, &ldquo;Click
here&rdquo; and &ldquo;Learn more&rdquo;, and four icon links with no alt text. Docket reported
this, in its own words:</p>

<pre><code>{esc(vague["title"])}
{esc(vague["detail"])}

{esc(empty["title"])}
{esc(empty["detail"])}</code></pre>

<p>The fixes it printed were: <em>{esc(vague["fix"])}</em> and <em>{esc(empty["fix"])}</em> The
home page after I followed them:</p>

<pre><code>{esc(_RUN["after_home"])}</code></pre>

<p>Docket reported neither finding on the second audit. Nothing about the layout changed: the
cards look the same, and the icons are the same icons.</p>

<h2>What Docket cannot tell you</h2>

<ul>
<li><strong>It checks the words, not whether they are true.</strong> A link called &ldquo;Our
prices&rdquo; that goes to the contact page passes. Reading the text against the destination is
yours to do.</li>
<li><strong>It counts a bare &ldquo;Download&rdquo; or &ldquo;Continue&rdquo; even when the button
sits under a heading that names the file or the step.</strong> If the context is plain, you may
reasonably judge that one overstated. The longer text still costs nothing.</li>
<li><strong>It matches the whole text.</strong> &ldquo;Read more about servicing&rdquo; is not on
the list and is not counted, though it is longer than it needs to be.</li>
</ul>

<h2>When to leave it for later</h2>

<p>A handful of vague links on a small site is a low-effort tidy and a low-impact one. The
finding is ranked that way in the plan. If it names hundreds of links on a large site, they almost
always come from one component, a card or a post teaser, so fix the template once.
<a href="/how-to/fix-image-seo-problems/">Alt text on images</a> is the other half of the icon
links, and a crawler's list of every link on your site, with its text, is one of the things worth
comparing between <a href="/vs/">the audit tools</a>.</p>

{buy_block("howto-link-text", big=False, try_app="howto-link-text-try-free")}
"""
    return render(
        cat="how-to", slug="fix-vague-and-empty-link-text",
        title="How to fix 'click here' and 'read more' link text",
        desc=("Link text should say where the link goes. Rewrite 'click here' and 'read more', "
              "name your icon links, and see what a crawler counts and what it cannot judge."),
        h1="How to fix vague and empty link text",
        crumb='<a href="/">Docket</a> / <a href="/how-to/">Fix it</a> / link text',
        body=body,
        faq=[
            ("Is &ldquo;click here&rdquo; bad for SEO?".replace("&ldquo;", "'").replace("&rdquo;", "'"),
             "Google's link guidance lists it as generic anchor text and recommends text that is "
             "descriptive, concise and relevant to the page it links to."),
            ("What should I write instead of 'read more'?",
             "The name of the destination, such as 'typewriter servicing'. If the card has a heading "
             "that names it, make the heading the link."),
            ("How do I name a link that only holds an icon?",
             "Put an aria-label on the link and give the icon alt=\"\" so it is not announced twice. "
             "A wrapped image with a real alt also works."),
            ("Which phrases does Docket count as vague?",
             "The whole link text has to equal one of: " + ", ".join(_PHRASES) + ". Case and "
             "trailing marks such as arrows are ignored."),
        ],
    )


if __name__ == "__main__":
    print(link_text())
