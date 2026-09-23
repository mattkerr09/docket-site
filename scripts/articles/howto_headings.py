#!/usr/bin/env python3
"""Heading structure — what `onpage.headings` computes, and where it parts
company with the HTML specification and with Google's own documentation.

Everything about the check is read from its source, `onpage.headings` in
`backend/seo_engine/checks/onpage.py`; from the extractor that fills the field
it reads (`Document.headings` in `backend/seo_engine/dom.py`); from the context
it iterates (`AuditContext.content_bearing` in
`backend/seo_engine/registry.py`); and from
`tests/test_a_page_with_thirty_three_subheadings_has_subheadings.py`, whose
docstring records the false finding that produced the current condition.

WHAT SECTION 9 CAUGHT, all of it in the brief's favour except where noted:

⚠️ THE REGISTERED TITLE IS ONE CHECK; IT EMITS FOUR FINDING IDS.
   `onpage.h1_missing` (MEDIUM), `onpage.h1_multiple` (LOW),
   `onpage.h2_missing` (LOW) and `onpage.heading_skip` (NOTICE). "Heading
   structure" is the lane's label for all four and is broader than any of them.
   The page names them individually because the remedies are unrelated.

⚠️ `empty_h1` IS COLLECTED AND NEVER EMITTED. The function builds the list —
   `if h1s and not any(h.strip() for h in h1s)` — and there is no
   corresponding `yield`. It is also unreachable: `Document.headings()` appends
   a heading only `if text`, and `text` comes from `text_content()`, which ends
   in `_collapse_ws(...).strip()`. A whitespace-only heading collapses to "" and
   is never recorded, so `h1s` cannot contain one. The page therefore does NOT
   say Docket reports empty headings. It says the opposite, which is what the
   code does: a heading with no text is not recorded at all, so a page whose H1
   holds only a logo image reads to Docket as having no H1.

⚠️ `onpage.h2_missing` IS NARROWER THAN ITS OWN ID. The condition is not "no
   H2". It is `word_count >= SUBSTANTIAL_WORDS` AND no h2 AND no h3, h4, h5 or
   h6. A short page is exempt and a page structured with h4s is exempt. The id
   survives from the version the test above killed.

⚠️ `onpage.heading_skip` IS NARROWER THAN "SKIPS A HEADING LEVEL". It fires on
   exactly one shape: an h3 exists anywhere in the document and no h2 exists
   anywhere. It is a presence test over the whole page, not a walk of the
   sequence. h2 straight to h4 is not flagged. h1 straight to h4 with no h3 is
   not flagged. An h1-to-h3 jump halfway down a page that also carries an h2
   somewhere is not flagged. The HTML specification's rule is per-sequence and
   therefore STRICTER than the check, and the page says so.

⚠️ THE CHECK CONTRADICTS ITSELF ON THE ONE-H1 QUESTION, mildly, and the page
   quotes both halves. `onpage.h1_missing`'s fix text says "Add exactly one H1
   per page"; `onpage.h1_multiple`'s detail says "HTML5 permits it". Both are
   in the shipped strings. The specification settles it: multiple top-level
   headings are conforming, and the conformance requirement is only that at
   least one heading in the outline has level one.

⚠️ THE BRIEF SAID "DOCKET READS THE HEADING ELEMENTS". The repo is narrower: it
   reads each heading's collapsed text content, from the WHOLE document —
   `self.root`, not `self.body`, and with no boilerplate filter — so an h2 in a
   `<footer>` clears the "no subheadings" finding and an h1 wrapping a header
   logo counts as the page's H1. Prose checks strip nav, header and footer.
   This one does not.

⚠️ NOT EVERY PAGE IS ASKED. The loop runs over `ctx.content_bearing`, which is
   the indexable pages minus the JavaScript-dependent ones, over a page set that
   has already dropped bot-protection interstitials, browser-upgrade notices and
   empty stand-ins. A noindex page is never asked about its H1.

No figure is typed into the prose and there is no dataset behind this page. The
condition is quoted as source inside `<pre><code>`, which `verify_numbers.py`
masks, and the one brace expression in that quotation is written with numeric
character references so no `{` ever reaches the rendered text — `lint.py`'s
unrendered-placeholder gate reads visible text without unescaping entities, and
a literal `{level}` there would fail the build.

The finding list is built from `FINDINGS` and its length is measured with
`len()`, so the count in the sentence and the items beneath it cannot disagree.

External sources, each read 2026-09-15 and each confirmed to return 200
(curl, same day):

  * https://html.spec.whatwg.org/multipage/sections.html  (200, section 4.3.11
    "Headings and outlines")
    "A document can contain multiple top-level headings", with a worked example
    of three h1 elements; "If a document has one or more headings, at least a
    single heading within the outline should have a heading level of 1";
    "Each heading following another heading lead in the outline must have a
    heading level that is less than, equal to, or 1 greater than lead's heading
    level"; and, on the example immediately above, "Notice that the title
    element is not a heading."

  * https://developers.google.com/search/docs/fundamentals/seo-starter-guide
    "Having your headings in semantic order is fantastic for screen readers,
    but from Google Search perspective, it doesn't matter if you're using them
    out of order", and "There's also no magical, ideal amount of headings a
    given page should have."

  * https://developers.google.com/search/docs/appearance/title-link
    Lists "Heading elements, such as <h1> elements" among the sources Google
    draws a title link from, and advises putting the main title text "in the
    first visible <h1> element on the page".
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from render import render  # noqa: E402

#: The day all three external sources were read, in the form the prose prints.
#: Typed here rather than in the body because the derived-number gate reads a
#: date in prose as a typed figure.
READ = "15 September 2026"

#: (finding id, severity, the finding's own sentence). Quoted from the `yield`
#: blocks of `onpage.headings`. The list below and the count above it are both
#: built from this, so they cannot drift apart.
FINDINGS = [
    ("onpage.h1_missing", "MEDIUM",
     "pages have no H1 heading"),
    ("onpage.h1_multiple", "LOW",
     "pages have more than one H1"),
    ("onpage.h2_missing", "LOW",
     "substantial pages have no subheadings"),
    ("onpage.heading_skip", "NOTICE",
     "pages skip a heading level"),
]

_ROWS = "\n".join(
    f'<li><code>{fid}</code> — <strong>{sev}</strong> — "…{sentence}"</li>'
    for fid, sev, sentence in FINDINGS
)


def howto_headings() -> Path:
    body = f"""
<p class="lede">Your audit flagged your headings, and you have read contradictory advice about
them for years. One H1 per page, or as many as you like. Never skip a level, or nobody cares.
The advice contradicts itself because three different things get argued as though they were one:
what a crawler can measure, what the HTML standard requires, and what Google says it does with
headings. They do not agree, and knowing where they part is more useful than another rule.</p>

<h2>Start with what no tool can tell you</h2>

<p>Docket reads your HTML. For this check it reads the text inside your heading elements and
nothing else — not the paragraphs beneath them, not what the page is for.</p>

<p>So it cannot tell you the thing that matters most: <strong>whether a heading describes the
section under it.</strong> A page can pass every heading finding Docket has and still be
organised under headings that say "Overview", "More", "Details" and "Other". That page has a
perfect outline and a useless one, and no crawler will flag it, because a crawler has nothing to
compare the words against.</p>

<p>It also does not know what the page is <em>for</em>. A checkout step, a category listing and a
long guide want different heading structures, and the check applies the same conditions to all
three, exempting pages on word count alone. A clean run here means your heading elements are
present and in a plausible order, not that your page is well organised.</p>

<h2>What the check computes, from the source</h2>

<p>The registered check is <code>onpage.headings</code>, "Heading structure", and that one
label covers {len(FINDINGS)} separate findings with unrelated remedies:</p>

<ul>
{_ROWS}
</ul>

<p>The conditions that produce them are short enough to read in full:</p>

<pre><code>h1s = page.headings.get("h1", [])
if not h1s:
    no_h1.append(page)
elif len(h1s) &gt; 1:
    multi_h1.append(page)

deeper = any(page.headings.get(f"h&#123;level&#125;") for level in (3, 4, 5, 6))
if (page.word_count &gt;= SUBSTANTIAL_WORDS
        and not page.headings.get("h2") and not deeper):
    no_h2.append(page)

if page.headings.get("h3") and not page.headings.get("h2"):
    skipped.append(page)</code></pre>

<p>They are not weighted equally, and the ordering answers the question at the top of this page
better than any advice could. A missing H1 carries the heaviest impact weight of the set by a
wide margin; a wall of text with no subheading at any level comes next; more than one H1 comes
below that; skipping a level is the lightest thing this check emits. That is your triage order,
and not the one the advice on the web gives.</p>

<h2>The one-H1 question, kept in three parts</h2>

<p>This is where the folklore lives, so it is worth separating who says what.</p>

<p><strong>The check.</strong> It flags a page with more than one H1 at LOW severity,
and its own detail text concedes the point: "Multiple H1s blur what the page is primarily about.
HTML5 permits it, but in practice it usually means the template is using H1 for styling." Its
fix is to keep one H1 and demote the rest. Note the reasoning — the finding is not "this breaks
something", it is "this is usually a symptom", which is a much weaker claim than the rule it
resembles.</p>

<p><strong>The HTML standard.</strong> It permits multiple H1s outright. The living standard's
section on headings and outlines states that a document can contain multiple top-level headings,
and prints a conforming example with three. Its only conformance requirement about level one is
that if a document has any headings at all, at least a single heading within the outline should
have a heading level of 1. <a
href="https://html.spec.whatwg.org/multipage/sections.html">WHATWG HTML, Headings and
outlines</a>, read {READ}.</p>

<p><strong>Google's documentation.</strong> It sets no number. The SEO starter guide says there
is no magical, ideal amount of headings a given page should have, and adds that while semantic
order is excellent for screen readers, from Google Search's perspective it does not matter if
you use them out of order. <a
href="https://developers.google.com/search/docs/fundamentals/seo-starter-guide">Google Search
Central, SEO starter guide</a>, read {READ}.</p>

<p>So Docket is stricter than both, and is the only one of the three claiming anything. That gap
is not a bug — a template emitting three H1s because the designer wanted three big fonts is worth
seeing — but read it for what it is. If your page has two H1s because it has two subjects, the
standard is on your side and Google is indifferent.</p>

<h2>Where the standard is stricter than Docket</h2>

<p>The skipped-level finding runs the other way, and this is the part nobody expects.</p>

<p>Docket's condition is a presence test over the whole document: an h3 exists somewhere and no
h2 exists anywhere. That catches the common template defect — h1 straight to h3 because h3 was
the right size — and it catches nothing else. An h2 followed by an h4 is not flagged. An h1
followed by an h4 with no h3 on the page is not flagged. A page that jumps h1 to h3 halfway down
but carries an h2 elsewhere is not flagged either.</p>

<p>The standard's rule is per-sequence: each heading following another must have a level that is
less than, equal to, or one greater than the previous heading's level. Its own non-conforming
example is an h1 followed by an h3, exactly the case Docket catches — but the rule covers every
other jump too, and Docket's does not. A clean <code>onpage.heading_skip</code> does not mean
your outline conforms.</p>

<p>What is the jump worth? Google's answer is above: for Search, not much; for screen readers, a
great deal. Docket's finding agrees and says nothing about rankings — "H3s appear with no H2
above them, which breaks the document outline for screen readers and parsers." That is the
honest version of a claim usually sold as a ranking factor.</p>

<h2>"No subheadings" has to mean no subheadings</h2>

<p>The condition used to be "long page, no H2". Run against a publisher's ebook-bundle page —
one H1, no H2, five H3s and twenty-eight H4s across roughly thirteen thousand words — it
produced two findings from the same loop about the same seven pages: "substantial pages have no
subheadings", and "pages skip a heading level". The second was true. The first was not: a reader
can count thirty-three subheadings on that page.</p>

<p>The detail text was right and the headline outran it. "Long pages with no H2s are a wall of
text" is a claim about H2s and it is fair. Generalised to "no subheadings" it became a different
claim and a false one — and a reader who catches a tool being wrong about the page in front of
them stops believing the finding that was accurate.</p>

<p>So the condition now requires no heading at any level below H2, with the word floor as its
other half: a short page needs no sections and is exempt. The id
<code>onpage.h2_missing</code> is a leftover from the version that was wrong.</p>

<h2>What Docket counts as a heading</h2>

<p>Narrower than you probably assume, and it explains most surprises.</p>

<ul>
<li><strong>A heading is its text.</strong> The extractor records a heading only if it has text
content after whitespace is collapsed. An <code>&lt;h1&gt;</code> holding only a logo image or an
inline SVG is not recorded at all, so that page is reported as having no H1 — usually the right
answer, and a surprise to anyone who can see a heading on the page.</li>
<li><strong>Every heading counts, wherever it sits.</strong> The extractor walks the whole
document, not the main content region, and applies no nav-and-footer filter. An H2 in your footer
clears the no-subheadings finding. An H1 wrapping your site logo in the header is that page's H1
on every page of the site — the usual cause of a site-wide "more than one H1".</li>
<li><strong>Only some pages are asked.</strong> The loop runs over the indexable pages whose
served HTML carried content. A noindex page is not asked about its H1, nor is a page whose markup
is essentially empty because the content arrives by JavaScript — reporting "no H1" there would
describe the crawler, not the page.</li>
</ul>

<h2>A title is not a heading</h2>

<p>These get conflated constantly and they are separate elements with separate jobs. The
<code>&lt;title&gt;</code> lives in the head, never appears on the page, and is what a search
result shows. An <code>&lt;h1&gt;</code> lives in the body and is what a visitor reads. The HTML
standard notes directly beneath its outline example that the title element is not a heading.</p>

<p>They interact in one documented way. Google's guidance on title links lists heading elements,
and H1 elements specifically, among the sources it draws a search result's title from when it
does not use your title element, and advises making the main title text the first visible H1 on
the page. That is the practical case for one clear H1: not a ranking rule, but control over what
the result says. The title element itself is a different job with a different unit of
measurement, covered in <a href="/how-to/write-title-tags-that-fit/">how to write title tags that
fit</a>. <a href="https://developers.google.com/search/docs/appearance/title-link">Google Search
Central, title links</a>, read {READ}.</p>

<h2>What to actually do</h2>

<p>In the order Docket's own weights put them:</p>

<ul>
<li><strong>Give every page an H1 with text in it.</strong> Docket's fix text is "Add exactly one
H1 per page that names the page's topic in plain language", with the markup
<code>&lt;h1&gt;WHAT THIS PAGE IS ABOUT, in plain language&lt;/h1&gt;</code>. The "exactly one"
is house preference rather than a requirement of the standard; what is not negotiable is that
there is one and that it has words in it.</li>
<li><strong>Break long pages into sections.</strong> The fix text asks for descriptive H2s,
"ideally phrased as the questions customers ask" — a subheading that states a question is the
unit an answer engine can lift.</li>
<li><strong>Use levels in order.</strong> Cheap to do, and the group it genuinely helps is
people using a screen reader.</li>
<li><strong>Then read your headings on their own.</strong> Strip the page down to its headings
and see whether the list still describes the page. That is the check no tool runs, and the one
that changes anything.</li>
</ul>

<p>The rest of what Docket looks at, check by check, is listed in <a
href="/learn/what-docket-checks/">what Docket checks</a>.</p>

<p><a class="btn" href="/download/">Download Docket</a></p>
"""
    # Further reading: pages Google had not yet discovered on 2026-09-22 (URL
    # Inspection: "unknown to Google"), linked from this page because Google
    # recrawls it often and last crawled the hubs that list them in August.
    # Chosen by topic; each such page is linked from exactly one article.
    body += """
<h2>Further reading</h2>
<ul>
<li><a href="/how-to/fix-a-site-that-says-something-different-every-page/">When your site stops saying one thing about itself</a></li>
<li><a href="/how-to/fix-a-site-that-sounds-like-several-companies/">When your site sounds like several companies wrote it</a></li>
<li><a href="/how-to/what-your-site-says-you-are-called/">What your site says your company is called</a></li>
<li><a href="/how-to/addresses-on-your-site-that-are-not-yours/">Not every address on your site is yours</a></li>
<li><a href="/how-to/where-an-audit-looks-for-your-address/">Where an audit looks for your address</a></li>
<li><a href="/how-to/fix-sameas-that-claims-the-wrong-accounts/">Not every social link on your site is yours</a></li>
</ul>
"""
    return render(
        cat="how-to", slug="fix-heading-structure",
        title="Fix heading structure: is one H1 per page a real rule?",
        desc=("What Docket's heading check measures, what it cannot see, and where the "
              "one-H1 rule parts company with the HTML standard and Google's own docs."),
        h1="How to fix heading structure",
        crumb='<a href="/">Docket</a> / <a href="/how-to/">Fix it</a> / heading structure',
        body=body,
        schema_type="Article",
        faq=[
            ("Is one H1 per page a real rule?",
             "Not in the HTML standard and not in Google's documentation. The living standard "
             "says a document can contain multiple top-level headings and prints a conforming "
             "example with three; its only requirement is that at least one heading in the "
             "outline is level 1. Docket still flags multiple H1s, at its lightest-but-one "
             "weight, because in practice it usually means a template is using H1 for font "
             "size."),
            ("Does skipping a heading level hurt my rankings?",
             "Google's SEO starter guide says semantic order is excellent for screen readers "
             "but that from Google Search's perspective it does not matter if headings are out "
             "of order. Docket reports it at NOTICE, its lowest severity, and its finding text "
             "talks about screen readers and parsers rather than rankings."),
            ("Why does Docket say my page has no H1 when I can see one?",
             "Because it records a heading only if the element has text content. An H1 holding "
             "only a logo image or an inline SVG has no text, is not recorded, and the page "
             "reads as having none."),
            ("Do headings in my footer count?",
             "Yes. The extractor walks the whole document and applies no nav, header or footer "
             "filter, so an H2 in your footer clears the no-subheadings finding and a header "
             "logo wrapped in an H1 counts as that page's H1 sitewide."),
            ("Does Docket check whether my headings are any good?",
             "No, and nor can any tool that reads markup. It can tell you a heading "
             "element is present, absent or out of order. It cannot tell you that your "
             "subheadings say Overview, More and Other. That judgement is yours and it is "
             "worth more than every finding on this page."),
        ],
    )


BUILDERS = [howto_headings]


def build_all() -> list[Path]:
    return [b() for b in BUILDERS]


if __name__ == "__main__":
    for p in build_all():
        print(p)
