#!/usr/bin/env python3
"""Trust and authorship signals — what `content.eeat` actually computes.

Everything about the check is read from its source, `content.eeat` in
`backend/seo_engine/checks/content.py` (registered as "Trust and authorship
signals"), from `AuditContext.has_page_like` / `json_ld_types` /
`Page.prose` in `registry.py` and `models.py`, and from the test that shaped
half of it, `tests/test_a_quote_form_is_a_contact_page.py`.

There is no dataset behind this page and it publishes no figure. The two
thresholds it describes in words — a form needs more than a single field, and
the author half needs three article-marked pages — are read from the check's
source and are spelled out rather than digitised, because `verify_numbers.py`
refuses a typed figure and there is nothing to derive them from: they are local
literals inside the function, not exported constants. Same choice, for the same
reason, as `/learn/ai-sounding-copy/` describing its own two-phrase threshold.

⚠️ COUPLED TO A DEFECT THAT IS STILL LIVE. The section "What it is actually
looking for" described a defect that has since been fixed, and the page now
says so in the past tense. `json_ld_types` returns `@type` VALUES and `author`
is a schema.org PROPERTY, so the snippet the finding printed as its own remedy
contributed `Article` and `Person` and never `author`. Measured against the
check on a fixture carrying exactly that markup plus a visible byline:
`content.no_author` still fired. Fixed in docket-app on 2026-09-16 —
`_declares_an_author()` walks the JSON-LD for an `author` property with a real
name, and `_BYLINE_CUES` replaced the bare-substring prose test — with
`tests/test_the_author_markup_we_tell_you_to_add_satisfies_the_check.py`
written first and seen to fail. ⚠️ IF THAT CHECK CHANGES AGAIN, THIS SECTION
CHANGES WITH IT: it describes behaviour, not history.

The schema.org reading ("author" is a property, expected types Person and
Organization) is from https://schema.org/author, read the same day.

The check's own `detail` for `content.missing_trust_pages` says Google's
quality guidelines treat missing trust pages "as a negative for any site that
transacts". That sentence is NOT restated here as fact: it is not on the
developers.google.com page above, and the rater guidelines PDF would not parse
when fetched, so nobody on this side has read it. The page quotes what Google
publishes and attributes the stronger claim to the check.

The body is an f-string, so every literal brace in the JSON samples is doubled.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from render import render  # noqa: E402

#: Google's guidance, read at its own canonical home on the date below. Held
#: here rather than typed into a sentence so the date cannot drift away from
#: the reading, and so `verify_numbers.py` sees a derived value.
G_URL = "https://developers.google.com/search/docs/fundamentals/creating-helpful-content"
SCHEMA_AUTHOR_URL = "https://schema.org/author"
READ_ON = "15 September 2026"


def _body() -> str:
    return f"""
<p class="lede">Google's guidance keeps returning to experience and trust, and a crawler can see
neither. What a crawler can see is a much smaller thing: whether your site names a person, and
whether the pages that say who you are exist at all. Docket's check for this is
<code>content.eeat</code>, "Trust and authorship signals". This page is about the distance
between those two sentences, because that distance is the whole answer.</p>

<h2>The honest centre, before anything else</h2>

<p>A byline is not expertise. Markup is not trust. Docket can see whether a page carries a word
that looks like attribution, and whether your site has an About page, a Contact page and a privacy
policy. It cannot assess whether the person named knows anything about the subject, whether the
About page is true, or whether anybody answers the contact form. No automated tool can do those
things, and a tool that implies it can is handing you a number it invented.</p>

<p>So read every finding from this check as a statement about <em>signals</em> rather than about
<em>standing</em>. It says a reader arriving on your site has nothing to go on. Supplying
something to go on is work only a person can do.</p>

<h2>What it actually looks for</h2>

<p>The check produces two findings, and they are less related than the name suggests. Most of it
is about pages; a smaller and looser part is about authorship.</p>

<h3>The three pages</h3>

<p>Docket asks three existence questions and reports the ones that fail as a single finding,
titled with the missing pages named:</p>

<ul>
<li><strong>About.</strong> A path containing <code>/about</code>, <code>/who-we-are</code>,
<code>/our-story</code>, <code>/team</code> or <code>/meet</code>.</li>
<li><strong>Contact.</strong> Either a path from a much longer list — <code>/contact</code>,
<code>/get-a-quote</code>, <code>/enquire</code>, <code>/book</code>, <code>/appointment</code>,
<code>/work-with-us</code>, <code>/support</code> and more besides — <em>or</em> any page in the
crawled sample carrying a form that asks for more than a single field.</li>
<li><strong>Privacy policy.</strong> A path containing <code>/privacy</code>.</li>
</ul>

<p>Severity depends on which one is missing. A missing Contact page raises the finding to medium;
a missing About page or privacy policy alone leaves it at low. That ordering is deliberate — a
site nobody can reach has a bigger problem than a site whose ownership is vague.</p>

<p>The fix text is the check's own, and it is worth reading as written rather than paraphrased:</p>

<blockquote><p>Add the missing pages with genuine detail — real names, a physical address if you
have one, a phone number, and who is behind the business.</p></blockquote>

<p>"Genuine detail" is doing the work in that sentence. An About page that says the company was
founded on a passion for excellence is, as a trust signal, indistinguishable from no About page
at all. The crawler cannot tell the difference. Every human reader can.</p>

<h3>It asks whether the page exists, not whether it was crawled</h3>

<p>This is the part most tools get wrong, and the reason is in the check's own comment. The
question is asked against every internal path the crawl <em>saw</em> — links, raw hrefs and
sitemap entries — rather than against the pages it fetched. A capped crawl of a large site reads a
fraction of it, so asking "did we fetch a privacy policy?" reports a missing privacy policy on a
site whose footer links to one from every page. That false positive is worse than a missed
finding: it makes the whole report look careless to the one person who knows the site best.</p>

<p>The same finding is also marked as requiring a full crawl, which means it is dropped rather
than published when the crawl itself was unreliable. A statement of the form "X is missing from
the entire site" is only defensible if the site was actually seen.</p>

<h3>The rule that a quote form is a contact page</h3>

<p>The Contact half used to match three paths. Measured on a ground-truth fixture: a plumber's
site whose enquiry page was <code>/quote.html</code> — a short "tell us what you need" form,
linked from the homepage, the services page and the nav — was told at medium severity that no
Contact page was found.</p>

<p>The path list is wider now, and more usefully, paths are no longer the only rule: a page
carrying an enquiry form is a contact page whatever it is called. A plumber's "Request a callback"
and a consultancy's "Work with us" are the same page under different signage. The form has to ask
for more than a single field, because site search is the common one-field form and counting it
would silence the check on nearly every site — which would be the worse bug of the two.</p>

<p>That was the third check in a single day with the same shape: it knew one form of the thing,
and reported the absence of every other form as the absence of the thing. It is worth naming
because it is the failure mode of every rule-based audit tool, including this one, and the only
defence is measuring against sites that plainly have what they are accused of lacking.</p>

<h3>The authorship half, and what it is really testing</h3>

<p>The second finding, <code>content.no_author</code>, fires at low severity when a site has three
or more pages carrying article markup and no author signal anywhere. An author signal is one of
two things: the page's JSON-LD carries an <code>author</code> property naming somebody, or the
body text carries a byline phrase — "written by", "posted by", "author:" and a couple of
neighbours.</p>

<p><strong>That is the corrected version, and the correction is worth the space.</strong> The
markup test used to ask the wrong question, and it asked it of the exact snippet the finding
itself prints as the remedy:</p>

<pre><code>"author": {{"@type": "Person", "name": "YOUR AUTHOR NAME",
           "url": "https://example.com/team/your-author"}}</code></pre>

<p><a href="{SCHEMA_AUTHOR_URL}">schema.org's <code>author</code></a>, read on {READ_ON}, is a
<em>property</em>; its expected types are <code>Person</code> and <code>Organization</code>. There
is no type called "author". The check was reading the list of <code>@type</code> values on a page
and looking for "author" in it, so that snippet contributed <code>Article</code> and
<code>Person</code> and never the thing being looked for. A site that did precisely what the
report told it to do, re-ran the audit, and saw the same finding with the same remedy.</p>

<p>It stayed hidden because the prose half was a bare substring test for the word "author" across
a blob joined from a capped sample of pages. A privacy policy offering to delete "content you
authored" contains it. So does a cookie notice or a plugin credit. Any one of them silenced the
finding sitewide, which is how a broken markup test went unnoticed: sites were being credited by
an unrelated word rather than by an attribution.</p>

<p>Both halves now do what their names say. The markup test reads the <code>author</code> property
out of your structured data, at any depth, and an empty one or a blank name does not count — the
property being present is not the same as somebody being named. The prose test matches byline
phrases rather than the word.</p>

<p><strong>One limit survives the fix, and you should know it.</strong> A visible byline that
reads simply "By Jane Smith", with no structured data behind it, still matches nothing: it is not
one of the byline phrases and it is not markup. That is a narrower miss than the one above and it
is deliberate — "by" alone appears in ordinary prose constantly — but if your attribution is a
bare name under a headline, add the schema rather than expecting the sentence to be read.</p>

<h3>What the count on that finding means</h3>

<p>One more thing to know before treating the number beside <code>content.no_author</code> as a
task list: the author signal is sitewide, so the count is every page carrying article markup, not
the pages that lack an attribution. Nothing in the check identifies a specific unattributed page,
because nothing in it looks at pages individually.</p>

<p>Its population is narrower than it sounds, too. "Article pages" here means pages declaring
article-family schema and nothing else. A blog with no structured data at all is never asked the
question by this check.</p>

<h2>What Google publishes about this, in its own words</h2>

<p>The panic around E-E-A-T is considerably larger than what Google actually documents, and the
documentation is short enough to read. From Google's guidance on
<a href="{G_URL}">creating helpful, reliable, people-first content</a>, read on {READ_ON}:</p>

<blockquote><p>While E-E-A-T itself isn't a specific ranking factor, using a mix of factors that
can identify content with good E-E-A-T is useful.</p></blockquote>

<blockquote><p>Search raters have no control over how pages rank. Rater data is not used directly
in our ranking algorithms.</p></blockquote>

<p>So E-E-A-T is a description of what human raters assess when they sanity-check a change to the
algorithm. It is not a dial, not a score your page carries, and not something any third-party tool
can measure on your behalf. Anyone selling you an E-E-A-T score is selling you their own opinion
with a number written on it.</p>

<p>The same page is much more concrete about attribution, and this part is mechanically useful:</p>

<blockquote><p>Is it self-evident to your visitors who authored your content? … Do pages carry a
byline, where one might be expected? Do bylines lead to further information about the author or
authors involved, giving background about them and the areas they write about?</p></blockquote>

<p>Note what those questions are addressed to: your visitors. A byline that leads to a page about
the person is useful because a reader can follow it. The markup matters after that, not
instead of it.</p>

<p>Google also says, of experience, expertise, authoritativeness and trust, that "of these
aspects, trust is most important". Docket's own finding puts the case for trust pages more
strongly than that source does — it describes their absence as a negative for any site that
transacts, which is a reading of the rater guidelines rather than of the page quoted here. The
narrower published wording is the one to act on, and it is the one linked above.</p>

<h2>Naming a person is not the same as resolving one</h2>

<p><code>content.eeat</code> does not read <code>sameAs</code>, and nothing in it connects an
author's name to an identity anywhere else. Docket does check <code>sameAs</code>, in a separate
check in the AI visibility lane, but that one reads the <em>organisation's</em> node — it asks
whether the business resolves to something a model already knows about, not whether your writer
does. Neither check resolves a named author to a real identity, which is the honest position:
<a href="/learn/sameas-entity-signals/">what sameAs does and who should declare it</a> is a
different question from whether your articles carry a byline.</p>

<h2>What to do with a finding from this check</h2>

<p>The trust-pages half is genuinely worth clearing, and it is an afternoon's work. Add the three
pages. Put real information on them — the name of the person who answers the phone, an address if
you have one, what the company actually is. If your enquiry page is called something other than
Contact, that is fine and Docket will recognise it, but a visitor searching your nav for the word
might not.</p>

<p>The authorship half deserves the weight its severity gives it, which is not much. Do the thing
Google's questions describe rather than the thing the check can detect: a byline on articles where
a reader would expect one, leading to a page that says who the person is and what they know. Add
the schema alongside it, because it is one property and it costs nothing. Just do not expect the
markup on its own to change what this particular check reports.</p>

<p>Every check Docket runs, with the reasoning behind each one, is listed on
<a href="/learn/what-docket-checks/">what Docket checks</a>.</p>

<h2>How much to trust this finding</h2>

<p>The trust-pages half is the reliable one: it asks a question with a factual answer, it asks it
against discovered paths rather than crawled ones, and it stands down entirely when the crawl was
too thin to support the claim. A finding from it is nearly always real.</p>

<p>The authorship half is a heuristic with a known gap in both directions, described above in
detail because a reader deciding whether to act on it needs to know which direction their own site
falls in. A clean result there is not evidence that your content is attributed. A finding there is
not evidence that it is not.</p>

<p><a class="btn" href="/download/">Download Docket</a></p>
"""


def trust_and_authorship() -> Path:
    return render(
        cat="learn", slug="trust-and-authorship-signals",
        title="Trust and authorship signals a crawler can see",
        desc=("What content.eeat looks for on a site: About, Contact and privacy "
              "pages, plus an author signal. What it measures, what it misses, and "
              "why E-E-A-T is not a score."),
        h1="Trust and authorship signals, and what a crawler can actually see",
        crumb='<a href="/">Docket</a> / <a href="/learn/">Learn</a> / Trust and authorship signals',
        body=_body(),
        schema_type="Article",
        faq=[
            ("Can a tool measure E-E-A-T?",
             "No. Google's own documentation says E-E-A-T is not a specific ranking factor, "
             "and that the human raters who assess it have no control over how pages rank and "
             "their data is not used directly in the ranking algorithms. What a tool can "
             "measure is a handful of signals that tend to travel with it — whether an About "
             "page exists, whether there is a way to make contact, whether a page names an "
             "author. Anything presented as an E-E-A-T score is an opinion with a number "
             "written on it."),
            ("What does Docket's trust and authorship check actually look at?",
             "Two things. Whether your site has an About page, a way to get in touch and a "
             "privacy policy, judged against every internal path the crawl saw rather than "
             "only the pages it fetched. And whether any author signal appears anywhere on "
             "the site, for sites carrying article markup."),
            ("My contact page is not called Contact. Will Docket report it as missing?",
             "It should not. The check matches a wide list of paths — quote, enquire, book, "
             "appointment, work with us, support and others — and separately counts any page "
             "carrying a form that asks for more than a single field as a way to make "
             "contact, whatever the path is called. That rule exists because the earlier "
             "version told a plumbing firm it had no contact page while its quote form was "
             "linked from every page on the site."),
            ("Why does a single-field form not count?",
             "Because site search is the common single-field form, and counting it would "
             "silence the check on nearly every site. A check that never fires is worse than "
             "one that occasionally asks for a page you already have under another name."),
            ("Docket says my articles have no visible author, but they have bylines. Why?",
             "Because the author test is narrow. It matches a JSON-LD type whose name "
             "contains the word author, or the words 'written by' or 'author' in the body "
             "text. A byline reading 'By Jane Smith' matches none of those, and correct "
             "schema markup contributes the type Person rather than author, since author is "
             "a schema.org property and not a type. Your bylines are fine. The check is "
             "reading for something narrower than a byline."),
            ("Does adding an author help anything other than this check?",
             "Google's guidance asks whether it is self-evident to your visitors who authored "
             "your content, whether pages carry a byline where one would be expected, and "
             "whether bylines lead to further information about the author. Those questions "
             "are addressed to readers, not crawlers. A byline that leads to a page saying "
             "who the person is and what they know is the thing worth having; the markup is "
             "worth adding afterwards because it is one property and costs nothing."),
            ("Is a missing privacy policy as serious as a missing contact page?",
             "Docket does not treat it that way. A missing contact page raises the finding to "
             "medium severity; a missing About page or privacy policy on its own leaves it at "
             "low. A site nobody can reach has the bigger problem."),
        ],
    )


BUILDERS = [trust_and_authorship]


def build_all() -> list[Path]:
    return [b() for b in BUILDERS]


if __name__ == "__main__":
    for p in build_all():
        print(p)
