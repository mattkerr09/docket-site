"""Mentioning filler is not shipping filler.

Promised on the how-to hub. Sourced from the registered check
`content.placeholder` in `backend/seo_engine/checks/content.py`, whose
docstrings record two false positives that a topic-based gate could not fix:

  * a homelessness charity's housing-policy chapter reported at HIGH as
    "unfinished content is live and indexable", because it discussed homes
    under construction;
  * a documentation wiki flagged twice on one site, because one long page used
    a namespaced filler-template name as a worked example and another listed
    that template among the templates that exist.

The repair in each case was a property of the TEXT rather than of the topic:
length for "under construction", continuation for the Latin passage. That
distinction is the page.

⚠️ NO SITE IS NAMED — third-party gate.

⚠️ NUMERALS: the charity's figures, the wiki's word counts and the
two-hundred-word threshold are all omitted or spelled as words.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from render import render  # noqa: E402


def placeholder_text() -> Path:
    body = """
<p class="lede">An audit reports that unfinished content is live and indexable on your site, and
quotes the evidence. You open the page. It is finished, it has been finished for years, and the
words it was flagged for are doing an ordinary job in an ordinary sentence.</p>

<p>Placeholder detection is a keyword search with a very high severity attached, and the two ways
it goes wrong are both instructive — because the fix, twice, was to stop asking what the page was
about and start asking what the text looked like.</p>

<h2>Under construction, about buildings</h2>

<p>A homelessness charity publishes a chapter of its housing-policy plan. Somewhere in it is a
sentence about how many homes are under construction and how many have planning permission. The
audit reported, at high severity, that unfinished content was live and indexable, and quoted that
sentence back as its evidence.</p>

<p>The obvious guard fails here. A check can look at the words around a marker to see whether the
page is <em>discussing</em> placeholder text rather than containing it — but this page is not
discussing placeholder text. It is discussing buildings. There is no cue to find, because the
phrase is being used for its ordinary meaning.</p>

<p>So the guard that worked was length. <strong>A holding page is short</strong> — that is what
the marker is for, a stub somebody left behind. A long finished document that happens to contain
the phrase keeps its finding only if something nearby says <em>this page</em> is the unfinished
thing: check back soon, this section is coming, that shape of sentence.</p>

<p>The alternative was a list of nouns to exclude — buildings, roads, railways — and that list
never ends. <strong>When the exclusions are open-ended, you are using the wrong property.</strong></p>

<h2>Lorem ipsum, named rather than used</h2>

<p>A documentation wiki was flagged twice on one site, both times at high severity, both times
citing the same famous two words.</p>

<p>Neither page was unfinished. One was a long discussion of internationalisation whose author
used a namespaced filler-template name as a worked example of how namespaced template names look.
The other was a help page listing that template among the templates the wiki has. <strong>Any
wiki, CMS or design system that ships a filler template names it somewhere</strong> — usually in
its own documentation, which is exactly the kind of page nobody wants flagged.</p>

<p>Again the discussion guard was useless: the words around those mentions are about namespaces
and template inventories, not about filler.</p>

<p>The tell turned out to be something else entirely. <strong>The Latin never continues.</strong>
Real leftover filler is a passage — it runs on into the rest of the sentence and the paragraph
after it. A mention is two words and stops. Nobody's forgotten placeholder ends after the opening
phrase, and nobody naming it in passing carries on into the rest of the Latin.</p>

<h2>The pattern worth taking away</h2>

<p>Both repairs replaced a question about <em>meaning</em> with a question about <em>shape</em>:</p>

<ul>
<li><strong>How long is the page?</strong> Filler lives on short pages.</li>
<li><strong>Does the passage continue?</strong> Filler is a passage; a reference is a phrase.</li>
</ul>

<p>Shape is cheap to measure, hard to argue with, and does not need a list of every innocent
context a phrase can appear in. Whenever you see a keyword-driven finding that keeps needing new
exceptions, the useful question is not which word to remove from the list — it is
<strong>what the real thing looks like that a mention of it does not</strong>.</p>

<h2>Reading this on your own report</h2>

<ul>
<li><strong>Read the quoted sentence, not the headline.</strong> Both cases above were obvious in
the quote. A placeholder finding that does not quote its evidence is not worth acting on until you
find the phrase yourself.</li>
<li><strong>Ask whether the page is short.</strong> A long, finished, linked-to page flagged as
unfinished is almost always a false positive.</li>
<li><strong>Ask whether the marker is the subject.</strong> Documentation about templates,
policy about construction, a style guide about typesetting — all of them name the thing without
being it.</li>
</ul>

<h2>When the finding is real, and it is worth a lot</h2>

<p>Keep the severity in view: this one deserves its rating, because live placeholder content is
among the most damaging things a site can publish without noticing. It is usually:</p>

<ul>
<li><strong>A stub from a build that was never finished</strong>, still linked from a menu.</li>
<li><strong>A template shipped with its example text intact</strong> — a new section, a new
location page, a new product added from a copy of another.</li>
<li><strong>A page that says it is coming soon</strong> and has said so for two years. That is a
page telling every visitor and every search engine not to bother, and either finishing it or
removing it is the right call.</li>
</ul>

<h2>The fixes that make it worse</h2>

<ul>
<li><strong>Editing real prose to avoid the trigger phrase.</strong> Rewriting a policy document
so it does not say "under construction" is letting a keyword list edit your content.</li>
<li><strong>Removing a filler template from your design system's documentation.</strong> It
exists; documenting it is correct; the audit is the thing that is wrong.</li>
<li><strong>Noindexing the flagged page.</strong> A finished, useful page hidden from search to
clear a false positive is the most expensive possible response to a keyword match.</li>
</ul>

<h2>How to trigger this on any site</h2>

<p>Write an article about placeholder text. This one would have matched before the guards existed,
which is a fair description of the whole category: <strong>a keyword check cannot distinguish
writing about a thing from doing it, and only the shape of the text can.</strong></p>

<h2>Where this sits in an audit</h2>

<p>The registered check is <code>content.placeholder</code>, which covers placeholder content in
the content quality area. For the same failure in a different lane — a phrase that is a signal in
one context and ordinary English in another — see
<a href="/how-to/findings-from-phrase-matching/">why an audit finds reviews you do not
have &rarr;</a>. For why a finding that keeps needing exceptions should be gated rather than
caveated, see <a href="/how-to/findings-that-flag-correct-pages/">a caveat is not a
gate &rarr;</a>.</p>
"""
    return render(
        cat="how-to", slug="placeholder-text-findings",
        title="Mentioning filler is not shipping filler",
        desc=("An audit can call a finished page unfinished because it mentions placeholder "
              "text. Why the shape of the text on a site beats its topic."),
        h1="Mentioning filler is not shipping filler",
        crumb='<a href="/">Docket</a> / <a href="/how-to/">Fix it</a> / Placeholder text',
        body=body,
        faq=[
            ("Why does my audit say a finished page is unfinished?",
             "Because it matched a phrase such as lorem ipsum or under construction. Both appear "
             "in ordinary writing — one in documentation about templates, the other in anything "
             "about building work."),
            ("How can a tool tell filler from a mention of filler?",
             "By shape rather than topic. Real filler sits on short pages and runs on as a "
             "passage; a mention is a phrase on a long page that stops after the opening "
             "words."),
            ("Should I rewrite a page to avoid the trigger phrase?",
             "No. If the page is finished and the phrase is doing an ordinary job, the finding "
             "is wrong. Editing real prose around a keyword list is letting the list write your "
             "content."),
            ("Is placeholder content actually damaging?",
             "Yes, when it is real. A stub still linked from a menu, or a template shipped with "
             "its example text intact, tells every visitor and every search engine that the page "
             "is not finished."),
            ("My design system documents a filler template. Will that be flagged?",
             "It can be, and it should not be. Documenting a template that exists is correct; a "
             "check that flags it is matching the name rather than the content."),
        ],
    )


if __name__ == "__main__":
    print(placeholder_text())
