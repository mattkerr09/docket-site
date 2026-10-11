#!/usr/bin/env python3
"""How to fix thin content pages.

Sourced from Docket's thin-content checks (backend/seo_engine/checks/content.py:
`content.very_thin`, `content.thin`, `content.utility_pages_indexable`, with the hub
exemption `_is_hub` and the bands THIN_WORDS and VERY_THIN_WORDS, written below as words).

Every count, word count and quoted line of finding text comes from
data/thin-content-run.json, written by docket-app/scripts/measure_thin_content_fixture.py:
a real Docket audit of a small fixture site of ours, before and after. Nothing about a
third-party site. Google's guidance was read at its own page on 2026-10-11 and is
paraphrased or quoted briefly with the link. The sentences added to the fixture's expanded
pages are filler written for the fixture; the page says so.
"""
from __future__ import annotations

import datetime
import html
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from render import buy_block, render  # noqa: E402

_RUN = json.loads((Path(__file__).resolve().parent.parent.parent / "data" / "thin-content-run.json").read_text())


def _when() -> str:
    d = datetime.date.fromisoformat(_RUN["date"])
    return f"{d.day} {d.strftime('%B %Y')}"


def thin_content() -> Path:
    esc = html.escape
    b, a = _RUN["before"], _RUN["after"]
    vt, th, ut = b["content.very_thin"], b["content.thin"], b["content.utility_pages_indexable"]
    bw, aw = b["words"], a["words"]

    def row(label: str, path: str, did: str) -> str:
        after = f"{aw[path]} words" if path in aw else "removed"
        return (f"<tr><td>{esc(label)}</td><td>{bw[path]} words</td><td>{esc(did)}</td>"
                f"<td>{after}</td></tr>")

    table = (
        row("Portable repair", "/portable-repair.html", "Written out properly")
        + row("Office machines", "/office-machines.html", "Merged into Services and removed, links updated (on a live site, with a 301)")
        + row("Ribbon replacement", "/ribbon-replacement.html", "Written out properly")
        + row("Platen service", "/platen-service.html", "Written out properly")
        + row("Site search", "/search.html", "Set to noindex, follow")
        + row("Guides (a section index)", "/guides/", "Left alone")
    )
    body = f"""
<p class="lede">A thin page has too little on it to answer what someone came for. The fix is not
more words. Decide for each page which of four things it needs: to be written out properly, to be
merged into a stronger page, to be kept out of the index, or to be left alone. Docket flags short
pages as a way to find the candidates. Google has said it has no preferred word count.</p>

<h2>What Google says</h2>

<p>I read Google's guidance on helpful content on {_when()}:
<a href="https://developers.google.com/search/docs/fundamentals/creating-helpful-content">Creating
helpful, reliable, people-first content</a>. Its self-assessment asks whether the content gives a
substantial, complete or comprehensive description of the topic. It also asks whether you are writing
to a particular word count because you have heard that Google has a preferred one, and answers the
question itself: no, it does not.</p>

<p>So length is a weak signal and a useful one. A very short page is often an unfinished one, which
is why it is worth looking at. A long page can still say nothing. The test is whether a reader who
arrives with a question leaves with the answer.</p>

<h2>What Docket reports</h2>

<ul>
<li><strong>Almost no content.</strong> Under sixty words of body text, reported as high severity.</li>
<li><strong>Thin.</strong> From sixty up to a hundred and fifty words, reported as medium.</li>
<li><strong>Search and utility pages that are indexable.</strong> Site search, carts, logins and
confirmation pages are short because that is what they are for. Docket reports them separately, with a
one-line fix.</li>
</ul>

<p>It leaves several kinds of page alone. A section index, a page whose job is to list three or more
pages beneath its own address, is skipped, because a short list is what an index should be. A page whose
text arrives by JavaScript is skipped and left to the JavaScript check, because its served HTML says
little about it. Tag, author and category archives are reported on their own with their own advice.
The two bands are Docket's triage lines, not Google's.</p>

<h2>Decide for each page</h2>

<ol>
<li><strong>Does anyone search for this?</strong> Then write it properly. A page earns its place by what
it tells the reader, so put in the specifics they came for: what is included, what it costs, how long it
takes, who it suits and what happens next. A service page needs those. A definition may need three lines.</li>
<li><strong>Is there a stronger page on the same subject?</strong> Then fold what is worth keeping into
it, redirect the old address to it with a 301, and update the links that pointed at the old one. If two
pages are chasing the same search, that is
<a href="/how-to/fix-pages-competing-for-one-search/">a different problem with the same fix</a>. The
redirects themselves are in <a href="/how-to/fix-redirect-problems/">how to fix redirect
problems</a>.</li>
<li><strong>Does it have a job but nothing to rank for?</strong> Site search, a cart, a thank-you page.
Add <code>&lt;meta name="robots" content="noindex, follow"&gt;</code> and leave the page alone. Nothing needs
writing.</li>
<li><strong>Is it an index?</strong> A category list, an A to Z, a tag or author page. Judge it on whether
the list is worth having and whether anything links to it, not on its length.</li>
<li><strong>Does it have no purpose at all?</strong> Remove it, and redirect it if anything links to it.</li>
</ol>

<h2>What not to do</h2>

<p>Do not pad. Adding filler to cross a number clears a word count and changes nothing for the reader,
and the reader is the test Google describes. Do not noindex a page you want to rank in order to quieten a
finding. And do not delete a page that other pages link to without redirecting it, because the links
break and the value they carried goes with the page.</p>

<h2>A real before and after</h2>

<p>I wrote a small fixture site for this page: a typewriter repair workshop, a dozen pages. I audited it
with Docket on {_when()}, dealt with each short page in the way the list above suggests, and audited it
again. The pages are ours; nothing here is measured on anyone else's site. Docket reported this, in its
own words:</p>

<pre><code>{esc(vt["title"])}
{esc(vt["detail"])}

{esc(th["title"])}
{esc(th["detail"])}

{esc(ut["title"])}</code></pre>

<p>What I did, with Docket's word counts for each page:</p>

<div class="wrap-tbl"><table>
<thead><tr><th>Page</th><th>Before</th><th>What I did</th><th>After</th></tr></thead>
<tbody>{table}</tbody></table></div>

<p>On the second audit Docket reported none of the three findings. Two things in that table are worth
reading. The section index at {bw["/guides/"]} words was never reported, before or after, because
it lists the pages beneath it. And the words I added to the three expanded pages are filler written for the
fixture, so that the counts would move. They are not the advice. On a real site, what takes a page out of
the thin band is what it tells the reader, and Docket cannot judge that.</p>

<h2>What Docket cannot tell you</h2>

<ul>
<li><strong>Whether a page is useful.</strong> It counts words. A contact page, a definition or a
price list can be complete and short. A long page can be thin in everything but length.</li>
<li><strong>Whether a short page is meant to be short.</strong> It skips section indexes it can recognise
by their links, but it cannot tell a deliberately brief page from an unfinished one. That is for you to
decide, page by page.</li>
<li><strong>What a page looks like after JavaScript runs.</strong> It reads the served HTML, so a page
built in the browser is left to the JavaScript finding rather than judged here.</li>
</ul>

<h2>Where to start</h2>

<p>Start with the pages that sell. A thin page about a service you charge for is worth an afternoon; a
thin page about nothing in particular may be worth a redirect. Sort the finding's list by what each page is
for before you open the first one. The same finding is part of a wider
<a href="/how-to/content-audit/">content audit</a>, and what Docket adds is the check across every
page, ranked with the rest; see how that compares with <a href="/vs/">other audit tools</a>.</p>

{buy_block("howto-thin-content", big=False, try_app="howto-thin-content-try-free")}
"""
    return render(
        cat="how-to", slug="fix-thin-content-pages",
        title="How to fix thin content pages without padding them",
        desc=("A thin page has too little to answer what someone came for. Write it properly, merge it, "
              "noindex it or leave it, and why Google has no word count."),
        h1="How to fix thin content pages",
        crumb='<a href="/">Docket</a> / <a href="/how-to/">Fix it</a> / thin content',
        body=body,
        faq=[
            ("What is thin content?",
             "A page with too little on it to answer what the reader came for. Docket flags short pages as "
             "candidates, and the judgement about whether one is really thin is yours."),
            ("How many words should a page have?",
             "Google says it has no preferred word count. A page should give a substantial, complete description "
             "of its topic, and some topics take three lines."),
            ("Should I noindex thin pages?",
             "Only if the page has a job but nothing to rank for, such as site search or a cart. For a page you "
             "want found, write it properly or merge it into a stronger page and redirect."),
            ("Does Docket flag a section index as thin?",
             "No. A page that lists three or more pages beneath its own address is treated as an index and left "
             "alone, because a short list is what an index should be."),
        ],
    )


if __name__ == "__main__":
    print(thin_content())
