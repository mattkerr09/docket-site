#!/usr/bin/env python3
"""Answer extractability — what `ai.extractability` actually computes.

Everything about the check is read from its source, `ai.extractability` in
`backend/seo_engine/checks/ai_visibility.py` (registered in the AI lane as
"Answer extractability"), from `Document.headings` / `Document.main_text` /
`BOILERPLATE_TAGS` in `dom.py`, from where `page.headings` and
`page.word_count` are assigned in `extract.py`, from `AuditContext.indexable`
and `urls_of` in `registry.py`, from the `requires_full_crawl` suppression in
`audit.py`, and from the test that guards the finding's URL list,
`tests/test_finding_urls.py`.

The check emits exactly ONE finding id — `ai.no_question_headings`, at MEDIUM.
The check id and the finding id are different namespaces, which `audit.py`
records the hard way; both are named on the page so a reader searching their
own report for either string lands somewhere.

⚠️ NO FIGURE IS PUBLISHED HERE AND THERE IS NO DATASET BEHIND THIS PAGE. The
site's AI-crawler datasets measure ACCESS — who is allowed to fetch a page.
This page is about EXTRACTION, and no measurement of extraction exists on this
side or any other. An access percentage carried across into an extraction
sentence would be the worst thing this page could do, so the page publishes no
number at all and says why. `/index/ai-directives/` is linked, not quoted.

The thresholds this page describes in words — three hundred words of main text,
at least three such pages, fewer than a quarter of them — are read from the
check's source and are SPELLED OUT rather than digitised, because
`verify_numbers.py` refuses a typed figure and there is nothing to derive them
from: two are local literals inside the function and the third is
`words.SUBSTANTIAL_WORDS`, which this repo does not import. Same choice, for
the same reason, as `/learn/trust-and-authorship-signals/` and
`/learn/ai-sounding-copy/`.

⚠️ COUPLED TO TWO LIVE PROPERTIES OF THE CHECK. Both are described in the
present tense because they are true of the shipped code today, and both must be
re-read if the check is edited:

  1. The function's own docstring says the signal is "question-form headings
     followed by a concise answer, lists, and tables". The body reads headings
     and nothing else. No list, no table, and nothing under the heading. Same
     shape as `ai.entity` at `ai_visibility.py:957` and `_declares_an_author`
     in `content.py` — a description that names something the implementation
     never reads — though milder, because here the mismatch is with a docstring
     rather than with the remedy the finding prints.
  2. `page.headings` is assigned `doc.headings()`, which walks the WHOLE
     document. `page.word_count` is counted over `doc.main_text()`, which
     strips `BOILERPLATE_TAGS` — nav, header, footer, aside, form. So the
     denominator excludes site chrome and the signal includes it, and one
     footer heading ending in a question mark satisfies the test on every page
     of a site. This is the `chrome_text` problem in `dom.py` pointed the other
     way: there a check that needed the footer could not see it.

Two external sources, both vendors' own, read 2026-09-15 (READ_ON below):

  * https://developers.google.com/search/docs/appearance/ai-features
    "There are no additional requirements to appear in AI Overviews or AI Mode,
    nor other special optimizations necessary." and "There's also no special
    schema.org structured data that you need to add." Scoped on the page to
    Google's own AI features, which is all it covers.
  * https://developers.openai.com/api/docs/bots
    "OAI-SearchBot is used to surface websites in search results in ChatGPT's
    search features." The page documents access and IP ranges and does not
    document how a page is selected. NOTE: the older
    `platform.openai.com/docs/bots` URL 301s here; the resolved URL is the one
    linked.

No claim about how any engine ranks or selects appears on this page, because
neither vendor documents it and we have not measured it.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from render import render  # noqa: E402

#: The day both vendor pages above were fetched and read. One constant so the
#: date is interpolated rather than typed into prose.
READ_ON = "2026-09-15"

GOOGLE_AI = "https://developers.google.com/search/docs/appearance/ai-features"
OPENAI_BOTS = "https://developers.openai.com/api/docs/bots"


def answer_extractability() -> Path:
    body = f"""
<p class="lede">If ChatGPT or Perplexity reads one of your pages, can it actually get an
answer out of it? That is a fair question and it has a mechanical half, which is the half
Docket can help with. The check is <code>ai.extractability</code>, "Answer extractability",
and the honest place to start is with the part of the question no tool on your machine can
reach.</p>

<h2>Nobody can watch an engine read your page</h2>

<p>Docket cannot observe ChatGPT or Perplexity reading your site. It cannot tell you whether
you were cited, in which answer, or to whom. Neither can any other crawler, ours or anyone
else's: the answer is assembled inside a product we do not run, from an index we cannot
query, for a reader we never meet. A crawler sees your HTML. It does not see the engine.</p>

<p>So what this check measures is the <em>shape</em> of your content against what lifting an
answer out of it requires. That is a proxy, and the page should say so before it says
anything else. The reasoning behind the proxy is plain enough — a passage that states a
question and then answers it is a passage something can take whole, and eight paragraphs of
throat-clearing is not — but reasoning is not evidence, and a page can satisfy this check and
never be quoted by anything.</p>

<p>The vendors are clearer about this gap than most of the advice written about them.
Google's own guidance, <a href="{GOOGLE_AI}">AI features and your website</a>, read on
{READ_ON}, says: "There are no additional requirements to appear in AI Overviews or AI Mode,
nor other special optimizations necessary", and "There's also no special schema.org
structured data that you need to add." That is Google writing about Google's features, and it
does not describe ChatGPT or Perplexity. OpenAI's
<a href="{OPENAI_BOTS}">crawler documentation</a>, read the same day, says
"<code>OAI-SearchBot</code> is used to surface websites in search results in ChatGPT's search
features" — and then documents access, user-agents and IP ranges, and nothing whatever about
how one page gets chosen over another.</p>

<p>Nothing on this site will tell you what to do to be cited, because outside those companies
nobody knows. What follows is what one check computes, exactly, and what that is worth.</p>

<h2>What the check computes</h2>

<p>It runs site-wide, not per page, and it stands down rather than guessing in three
situations.</p>

<ol>
<li><strong>English only.</strong> The matching is English phrase matching, so the check is
gated on the crawl's language detection and never runs against text it cannot read.</li>
<li><strong>Substantial pages only.</strong> It takes the indexable pages whose main text
runs to three hundred words or more. Main text, which means nav, header, footer, aside and
form are stripped before the counting.</li>
<li><strong>At least three of them.</strong> Below that it returns silently. A four-page
business site gets no finding here, and no pass either.</li>
</ol>

<p>For each surviving page it asks one question: does any <code>h2</code> or <code>h3</code>
end in a question mark? If none does, it joins that page's second- and third-level headings
into a single lowercased string and looks for a question word — how, what, why, when, where,
which, can, do, does, is, are — followed within about sixty characters by a question mark.
Either hit counts the page as asking a question.</p>

<p>Then it divides. If fewer than a quarter of the substantial pages ask a question, the
check raises one finding. Above that line it says nothing at all.</p>

<h2>What the finding says</h2>

<p>One finding id, <code>ai.no_question_headings</code>, at <strong>medium severity</strong>,
titled "Content is not structured as answers to questions". Note that the finding id is not
the check id — searching your report for <code>ai.extractability</code> will not find it.
Its detail names how many of your substantial pages use question-form headings, and then
argues the case:</p>

<blockquote><p>AI answer engines assemble responses by lifting self-contained passages; a
page organised around questions gives them an obvious passage to lift, and a page of
undifferentiated prose does not.</p></blockquote>

<p>Its fix text asks for two things:</p>

<blockquote><p>Add H2s phrased exactly as customers ask them, and answer each in the first
two sentences underneath before elaborating. Keep the answer complete on its own — the model
will quote the paragraph, not the page.</p></blockquote>

<p>It prints a worked example of the shape it wants — a question heading, then the specific
figure or day in the first sentence — and it attaches the URLs of the pages that failed,
capped for readability, with the true total carried alongside. Only the failing pages: it
used to attach every page considered, which sent people to rewrite pages that were already
fine, and the test that pins the current behaviour is
<code>tests/test_finding_urls.py</code>.</p>

<p>It is also marked as requiring a full crawl: on a partial crawl it is withheld and
reported as withheld, rather than quietly downgraded into a pass.</p>

<h2>What it does not compute</h2>

<p>The check's own docstring says the signal is question-form headings "followed by a concise
answer, lists, and tables". The code reads headings. Nothing reads a list, nothing reads a
table, and — this is the one that matters — <strong>nothing reads the text underneath the
heading.</strong></p>

<p>Which means the fix text asks for two things and the check can only see one of them. Phrase
your H2 as a question and the check goes quiet, whether or not you answered it in the first
two sentences, whether or not the answer stands on its own, whether or not there is an answer
at all. The half of the advice that does the actual work is the half nothing verifies.</p>

<p>We would rather write that down than let a green result be read as a guarantee. It is the
same family of gap as two others recorded in the engine, where a check's description named
something its implementation never looked at — milder here, because the mismatch is between
the code and a docstring rather than between the code and the remedy the report prints, but
the same shape.</p>

<h2>Two ways it says you passed when you did not</h2>

<p>Both of these acquit, which is the direction that should worry you. A false accusation
wastes an afternoon; a false pass ends the enquiry.</p>

<h3>Your footer can acquit your entire site</h3>

<p>The word count that decides which pages are substantial is measured over main content,
with nav, header, footer and aside stripped out. The headings are collected from the whole
document, chrome included. The denominator excludes your furniture and the signal does
not.</p>

<p>So a single heading in a site-wide footer — "Questions?", "Need a hand?", "Ready to get
started?" — appears on every page of the site and satisfies the test on every page of the
site. Nothing in the check can tell that heading from one over an answer. If your template
has one, this check is currently telling you nothing about your content.</p>

<h3>A closing button is not a question your customers ask</h3>

<p>Any second- or third-level heading ending in a question mark counts, and plenty of them
are sales furniture rather than enquiry. "Ready to book?" above a form is not a passage
anything can lift. What the check tests is the punctuation of your headings; what its name
promises is that an answer can be taken out of your page. Read it as the first, and answer
the second yourself by reading the page.</p>

<h2>Where this check ends and the others begin</h2>

<p>Three checks in two lanes sit near this one and none of them is doing its job:</p>

<div class="wrap-tbl"><table class="cmp">
<thead><tr><th>Check</th><th>Asks</th><th>Reads</th></tr></thead>
<tbody>
<tr><td><code>ai.extractability</code></td><td>Is there an obvious passage to lift?</td>
<td>Your <code>h2</code> and <code>h3</code> text</td></tr>
<tr><td><code>ai.citable_facts</code></td><td>Is there anything worth repeating in it?</td>
<td>Your body prose, for a number attached to something a reader could check</td></tr>
<tr><td><code>content.ai_slop</code></td><td>Does it read like everyone else's page?</td>
<td>Your body prose, for stock phrasing</td></tr>
</tbody></table></div>

<p>The sibling is the interesting one. <code>ai.citable_facts</code> wants a figure joined to
an attribution — a measurement someone could dispute, a date, a licence, a price — and it
counts a bare number as nothing, because "ten tips for this year" is a number with nothing
behind it. A page can pass extractability and fail that one: perfectly quotable structure
wrapped around nothing worth quoting. It can also fail extractability and pass that one,
which is the more common and more fixable position. Worth knowing if you are reading both in
the same report: the two checks do not agree on where "substantial" starts, and the lower
floor belongs to the citable-facts side. That is a divergence in the source rather than a
decision anybody wrote down.</p>

<p><code>content.ai_slop</code> is in a different lane and answers a different complaint —
<a href="/learn/ai-sounding-copy/">what it detects, and what it cannot</a> is its own page.
Nothing here is about how your writing sounds.</p>

<h2>The uncomfortable relationship with substitution</h2>

<p>There is a tension between this check and the one question on this site with a worse
answer. Making a page maximally liftable also makes it maximally replaceable: a
self-contained answer under a question-shaped heading is precisely what an assistant can take
and hand to somebody instead of your page.
<a href="/learn/ai-substitution/">Which of your pages an AI answer replaces</a> is that
question, and it comes to the opposite conclusion for purely explanatory pages — which are
the ones that score best here.</p>

<p>The resolution is not to write worse headings. Extractability is the right goal for pages
carrying something only you have, where being quoted names you, and the wrong goal for pages
whose whole value is the explanation. Both run on every audit. Read them together.</p>

<h2>Before any of this, the page has to be fetchable</h2>

<p>This check reads HTML that Docket already has. If a crawler is disallowed in your
robots.txt or refused at your CDN, it never reaches the question this page is about — and
that is a separate thing Docket measures separately, by reading your robots.txt against each
crawler by name. <a href="/how-to/fix-ai-crawler-access/">Fixing AI crawler access</a> is the
one to do first, and <a href="/learn/ai-search-visibility/">the three gates</a> sets out the
order: access, then rendering, then everything on this page.</p>

<h2>Why there is no number on this page</h2>

<p>This site publishes surveys of who blocks which AI crawler, including
<a href="/index/ai-directives/">a reading of robots.txt across the Tranco top ten
thousand</a>. Those measure <strong>access</strong>. This page is about
<strong>extraction</strong>, and we have no measurement of extraction — nobody does, for the
reason in the first section. So no figure appears above, and none is borrowed from the access
work to stand in for one. A percentage about who can fetch your page tells you nothing about
what an engine did after it arrived, and a page that let a reader carry one across to the
other would be doing the thing this whole site exists to object to.</p>

<h2>What to actually do</h2>

<ol>
<li><strong>Take the fix text at its word, both halves.</strong> Phrase the heading as the
question a customer asks, and put the answer in the first two sentences under it. The check
sees the first half. The second half is the one that does anything.</li>
<li><strong>Make the answer survive being cut out.</strong> "It depends on the size of the
room" is not an answer once it has been separated from the heading above it. Name the thing,
the figure and the condition in the same sentence.</li>
<li><strong>Check your footer before you trust a pass.</strong> If there is a question mark in
a site-wide heading, this check has been passing your pages for a reason that has nothing to
do with them.</li>
<li><strong>Use the customer's words, not the trade's.</strong> That is the usual reason a
page full of questions still reads as a brochure.</li>
<li><strong>Do not add the question if you do not have the answer.</strong> A heading that
asks something and then wanders is worse than a plain one, and it now passes a check while
being worse.</li>
</ol>

<p><a class="btn" href="/download/">Download Docket</a></p>
"""
    # Further reading: pages Google had not yet discovered on 2026-09-22 (URL
    # Inspection: "unknown to Google"), linked from this page because Google
    # recrawls it often and last crawled the hubs that list them in August.
    # Chosen by topic; each such page is linked from exactly one article.
    body += """
<h2>Further reading</h2>
<ul>
<li><a href="/how-to/schema-type-is-a-claim/">A schema type is a claim about what you are</a></li>
<li><a href="/how-to/schema-id-references/">An @id is a pointer, not a definition</a></li>
<li><a href="/how-to/schema-that-describes-someone-else/">The markup on your page may not be about you</a></li>
<li><a href="/how-to/json-ld-parser-errors/">Read the JSON-LD error, not the guess</a></li>
<li><a href="/how-to/fix-structured-data-that-does-not-match-the-page/">Structured data that says what the page does not</a></li>
<li><a href="/how-to/completeness-findings-assume-your-type/">A completeness check assumes your type is right</a></li>
<li><a href="/how-to/when-a-field-is-there-and-still-missing/">When a field is there and still missing</a></li>
</ul>
"""
    return render(
        cat="learn", slug="answer-extractability",
        title="Answer extractability: can an AI quote your page?",
        desc=("Docket's answer-extractability check reads your question-form "
              "headings. What it computes, what it cannot see, and why that is "
              "a proxy."),
        h1="Whether an AI answer can be lifted from your page",
        crumb='<a href="/">Docket</a> / <a href="/learn/">Learn</a> / Answer extractability',
        body=body,
        schema_type="Article",
        faq=[
            ("Can Docket tell whether ChatGPT has cited my site?",
             "No, and nor can any other crawler. An AI answer is assembled inside a product "
             "nobody outside that company can query, for a user the crawler never meets. "
             "Docket measures the shape of your content against what lifting an answer "
             "requires, which is a proxy for the thing you want to know and is not the "
             "thing itself."),
            ("What does the answer-extractability check actually look at?",
             "The second- and third-level headings of every indexable page carrying three "
             "hundred words or more of main text. It counts a page as asking a question if "
             "any of those headings ends in a question mark, or if a question word appears "
             "shortly before one. If fewer than a quarter of those pages qualify, it raises "
             "one medium-severity finding listing the pages that do not."),
            ("Does it check that I answered the question?",
             "No. Nothing in the check reads the text under the heading, and nothing reads "
             "your lists or tables either, although the check's own description mentions "
             "them. Its fix text asks you to phrase the heading as a question and answer it "
             "in the first two sentences; only the first of those is measured. Doing half "
             "the work clears the check."),
            ("Why did my site pass when none of my pages answer anything?",
             "Check your footer. Headings are collected from the whole document, including "
             "nav and footer, while the word count that decides which pages count is taken "
             "from main content with those regions stripped. One site-wide footer heading "
             "ending in a question mark satisfies the test on every page of the site."),
            ("Is adding question headings the same as AI optimisation?",
             "Not according to the vendors. Google states there are no additional "
             "requirements or special optimisations needed to appear in its AI features, and "
             "no special structured data. OpenAI documents which crawler surfaces pages in "
             "ChatGPT search and documents nothing about how a page is selected. Question "
             "headings help a reader find the answer, which is a good enough reason on its "
             "own."),
        ],
    )


BUILDERS = [answer_extractability]


def build_all() -> list[Path]:
    return [b() for b in BUILDERS]


if __name__ == "__main__":
    for p in build_all():
        print(p)
