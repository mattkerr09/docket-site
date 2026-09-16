#!/usr/bin/env python3
"""Generic AI-sounding copy — what `content.ai_slop` actually detects.

Everything about the check is read from its source, `content.ai_slop` in
`backend/seo_engine/checks/content.py`, and from the test that guards it,
`tests/test_an_english_idiom_is_not_evidence_of_a_language_model.py`.

No figure is published here and there is no dataset behind this page. The
measurement that removed one entry from the phrase list lives in the check's
own comment and in that test; it is described here in words, and the corpus
sites are not named, because they are third parties who did not ask to be
measured in public — see verify_no_named_third_parties.py.

Two external sources, both Google's own, read 2026-09-15:

  * https://developers.google.com/search/docs/fundamentals/creating-helpful-content
    "If you use automation, including AI-generation, to produce content for the
    primary purpose of manipulating search rankings, that's a violation of our
    spam policies."
  * https://developers.google.com/search/docs/essentials/spam-policies
    Scaled content abuse: "many pages are generated for the primary purpose of
    manipulating search rankings and not helping users", with little value to
    users "no matter how it's created".

⚠️ THE PHRASE LIST CANNOT BE PRINTED ON THIS SITE. `scripts/lint.py` bans all
but one of its entries as visible text, in both prose and `<code>`, so a page
that quoted the list would fail the build that publishes it. The page says so
rather than working around it, and the body is a plain string rather than an
f-string so no brace escaping is in play.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from render import render  # noqa: E402


def ai_sounding_copy() -> Path:
    body = """
<p class="lede">You drafted some pages with a language model, and now you are wondering whether
it shows and whether that costs you anything. Docket has a check for it —
<code>content.ai_slop</code>, "Generic AI-sounding copy" — and the first honest thing to say is
what it cannot do.</p>

<h2>It cannot tell you whether a machine wrote your page</h2>

<p>Nothing in the check looks at authorship, and there is no signal in a web page that would let
it. What it does is match a short list of English stock phrases against your body copy. That is a
test of <em>register</em>, not of origin. A human writer with a fondness for stock phrasing fails
it. A model draft that somebody edited properly passes it, and should.</p>

<p>So read a finding from this check as "these pages sound like everyone else's pages", never as
"these pages were generated". The second claim would be unfalsifiable, and a tool that makes
unfalsifiable claims about your writing has stopped being useful.</p>

<h2>What it actually computes</h2>

<p>For every indexable page, Docket lowercases the body text and counts how many phrases from a
fixed list appear in it. A page is reported only if it carries <strong>two distinct
phrases</strong> from that list. One is never enough, and the reason is the most interesting thing
about this check — see below.</p>

<p>Where any pages qualify, the check raises a single finding at <strong>medium severity</strong>
covering all of them, titled that those pages read as generic AI-generated copy. The detail line
quotes the first phrase it matched and the URL it matched on, so the finding carries its own
evidence instead of asking you to take it on trust. It is marked as a large piece of work, which
is honest: rewriting a page is not a settings change.</p>

<p>The fix text is a single sentence, and it is the part worth reading twice:</p>

<blockquote><p>Rewrite in the business's own voice with specifics only you have: real prices, real
timelines, named neighbourhoods, actual customer situations.</p></blockquote>

<p>That is not a style note. Stock phrasing is a symptom; the disease is that the page contains
nothing a competitor could not have written. Prices, timelines, place names and real customer
situations are the things a model cannot invent for you, because it does not know them. Supply
those and the stock phrases tend to fall out on their own, because there is finally something for
the sentence to be about.</p>

<h2>Why two phrases, and the entry that was removed</h2>

<p>The threshold is the check's defence against convicting ordinary writing, and it was very
nearly not enough.</p>

<p>The list once contained an ordinary English connective that predates the language models by a
very long way. It was measured against human-written pages from institutional sites — a church, a
credit union and a trade union, none of them named here — and it turned up on every one of them. Every other
marker in the list turned up on none of them. That is not a tell; it is a joint in the language.</p>

<p>Because the check fires on a pair, that one entry was enough to turn a single genuine cliché
into a conviction. On a large tutorial site, one page was reported on the strength of a real
cliché in the article and the ordinary idiom <em>in a reader's comment underneath it</em> — the
page was judged partly on somebody else's writing. The entry is gone, and the test that removed it
also asserts that no remaining marker fires on plainly-written institutional English, so the next
addition has to clear the same bar.</p>

<p>The comment half of that problem is still open and is worth knowing about if you run a blog
with comments enabled. The text Docket reads includes the comment thread, and no check currently
knows where the article stops and the readers start.</p>

<h2>The list is short on purpose, and this site cannot print it</h2>

<p>A long phrase list produces false positives on perfectly good human writing, so the list is
deliberately small and every entry has to earn its place. The entries that survive are the ones
that read as machine-written to almost anybody: the stock opener, the stock transition, the stock
superlative.</p>

<p>There is a small joke in the fact that this page does not quote them. This site runs its own
copy gate over every page it builds, and that gate bans nearly all of the same phrases as visible
text — including inside a code block. A page printing the list in full would fail the build that
published it. If you want the entries, they are legible in the check's source rather than on a
marketing page, which is where a claim about your writing ought to be auditable from.</p>

<h2>What it does not read</h2>

<p>Each of these exclusions exists because the naive version was wrong about somebody:</p>

<ul>
<li><strong>Code samples.</strong> The text these phrase checks read has <code>pre</code>,
<code>code</code>, <code>samp</code> and <code>kbd</code> stripped out of it. Docket once told a
popular CSS framework that its install guide contained placeholder text; the text was
<code>Hello world!</code> inside the code block the guide exists to show. Every documentation
site, tutorial and programming blog was exposed to the same reading.</li>
<li><strong>Pages you have excluded.</strong> The check reads indexable pages only, so anything
carrying a <code>noindex</code> directive is not judged.</li>
<li><strong>Sites that are not in English.</strong> The check is phrase matching against English,
so on a site whose content language is anything else it stands down entirely and the report says
that it did. The alternative — running an English phrase list over Japanese and reporting every
absence as a fact — is how a tool ends up telling a confectioner it has no call to action on
pages that all have one.</li>
<li><strong>Everything else about quality.</strong> This check has no opinion on whether your page
is accurate, useful, or worth reading. It matches phrases.</li>
</ul>

<p>Docket's per-check reasoning, including this one, is listed with every other check it runs on
<a href="/learn/what-docket-checks/">what Docket checks</a>.</p>

<h2>Does any of it actually cost you traffic?</h2>

<p>Google's published position is narrower than the panic around it, and worth reading directly.
Its guidance on
<a href="https://developers.google.com/search/docs/fundamentals/creating-helpful-content">creating
helpful, reliable, people-first content</a> says that using automation, AI generation included, to
produce content for the primary purpose of manipulating rankings violates its spam policies. Its
<a href="https://developers.google.com/search/docs/essentials/spam-policies">spam policies</a>
define scaled content abuse as many pages generated primarily to manipulate rankings rather than
help users, and say that such pages provide little value to users no matter how they were created.</p>

<p>Read those two together and the test is purpose, not production method. A page drafted by a
model, edited by someone who knows the business and genuinely useful to a reader is not what
either document describes. A mass of near-identical pages spun to catch a keyword pattern is,
whoever or whatever typed them.</p>

<p>The second cost is the one nobody publishes a policy about. Readers now pattern-match stock
phrasing instantly, and a prospect who decides on your first paragraph that nobody at the company
wrote this has already decided something about the company. That is not a ranking problem and no
crawler will ever measure it for you.</p>

<h2>What to do when it fires</h2>

<p>Open the pages the finding names and ask one question of each: what does this page contain that
only we could have written? If the answer is nothing, the stock phrases are the least of it.
Replace the generic paragraph with the specific one — what the job costs, how long it takes, which
streets you cover, what the awkward customer situation was and how it was handled. Then read the
result aloud. Stock phrasing is much easier to hear than to see.</p>

<p>If the same generic register runs across the whole site rather than a few drafted pages, the
problem is a level up from copy. Docket's brand lane asks whether a person moving between your
pages sees the same company each time, which is
<a href="/learn/brand-consistency/">a question no crawler asks</a> and a different question from
this one.</p>

<p>And if the pages in question exist to answer a question that an AI assistant now answers
directly, rewriting them in your own voice may not be the whole job. Which of your pages an AI
answer can replace, and what defends one, is
<a href="/learn/ai-substitution/">measured separately</a>.</p>

<h2>How much to trust this finding</h2>

<p>Medium severity is the right weight for it. This is a heuristic over a small phrase list, it
knows nothing about authorship, it can still be fooled by a comment thread, and it will miss
machine-written copy that avoids the stock phrases entirely — which is most of it, and increasingly
so. A clean result here is not a certificate that your writing sounds human. It only means these
particular phrases are not doing it.</p>

<p>That asymmetry is worth carrying into every finding any audit tool shows you. The general
version of the question is
<a href="/learn/audit-tool-accuracy/">how to tell whether an audit tool is lying to you</a>.</p>

<p><a class="btn" href="/download/">Download Docket</a></p>
"""
    return render(
        cat="learn", slug="ai-sounding-copy",
        title="Does your copy read as AI-written? What Docket checks",
        desc=("Docket's content.ai_slop check detects a register, not authorship. What it "
              "matches, why it needs two phrases, and what it cannot tell you about your "
              "writing."),
        h1="Copy that reads as AI-written, and what Docket can tell you",
        crumb='<a href="/">Docket</a> / <a href="/learn/">Learn</a> / AI-sounding copy',
        body=body,
        schema_type="Article",
        faq=[
            ("Can Docket tell if my content was written by AI?",
             "No, and neither can anything else reliably. The check matches a short list of "
             "English stock phrases against your body copy, which is a test of register "
             "rather than of authorship. A human writer fond of stock phrasing fails it; an "
             "edited model draft passes it."),
            ("What triggers the generic AI copy check?",
             "A page has to carry two distinct phrases from the check's fixed list before it "
             "is reported. One is never enough. The finding is raised once at medium "
             "severity covering every page that matched, and its detail line quotes the "
             "phrase it found and the page it found it on."),
            ("Why does it need two phrases rather than one?",
             "Because a single phrase convicts ordinary writing. One entry in the list was a "
             "common English connective that turned up on human-written pages across several "
             "institutional sites while no other marker turned up at all. It was removed, "
             "and the test that removed it now asserts that no remaining marker fires on "
             "plainly-written English."),
            ("Does AI-written content get penalised by Google?",
             "Google's spam policies target purpose rather than production method: content "
             "generated primarily to manipulate rankings rather than help users, which they "
             "say provides little value no matter how it was created. An edited draft that "
             "genuinely helps a reader is not what that describes."),
            ("Does the check run on a site that is not in English?",
             "No. It is English phrase matching, so outside English it stands down and the "
             "report says so, rather than finding nothing and reporting the absence as a "
             "fact about the site."),
            ("Does it read my code samples or my comment threads?",
             "Code samples are stripped before matching, because a placeholder inside a code "
             "block is the subject of a tutorial rather than unfinished copy. Comment "
             "threads are not yet separated from the article, so a page can in principle be "
             "matched partly on a reader's words. That gap is known and recorded."),
            ("What should I do if my pages are flagged?",
             "The check's own advice is to rewrite in the business's own voice with "
             "specifics only you have: real prices, real timelines, named neighbourhoods, "
             "actual customer situations. Those are the things a model cannot invent for "
             "you, and supplying them usually displaces the stock phrasing by itself."),
        ],
    )


BUILDERS = [ai_sounding_copy]


def build_all() -> list[Path]:
    return [b() for b in BUILDERS]


if __name__ == "__main__":
    for p in build_all():
        print(p)
