"""Why an audit can find reviews on a site that has none.

Promised on the how-to hub. Sourced from `backend/seo_engine/checks/local_seo.py`,
whose word lists carry four recorded false positives and the reasoning that
removed each phrase:

  * a software foundation's "please review the online license" — and, worse,
    its own sentence saying it does NOT provide testimonials, counted as
    evidence that it does;
  * "stars", which every repository badge on a technical site says;
  * a wildlife charity's joke about five-star accommodation for bees, quoted
    back as proof of displayed customer ratings;
  * a street-address pattern that matched a statistic in this project's own
    marketing copy and classified a Mac software company as a local business,
    producing six findings including two false high-severity headlines.

⚠️ THE FOURTH IS SELF-IMPLICATING AND SAFE TO USE — it is our own copy. The
others are third parties and are described without names, per the deploy's
third-party gate.

⚠️ THE ASYMMETRY IS THE POINT AND MUST NOT BE SOFTENED. The list deliberately
misses some real review sections, because a missed one produces "no customer
reviews" — advice to go and get some — while a false match tells a business to
mark up reviews it does not have and sends it looking for something that is not
there.

Numerals: none in prose. "221b Baker Street" is not used; the house-number case
is described in words.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from render import render  # noqa: E402


def phrase_matching() -> Path:
    body = """
<p class="lede">An audit cannot see your reviews. It reads your text, looks for phrases that
usually sit beside reviews, and infers. That works until a phrase means two things — and then it
tells a business with no customers to mark up its customer ratings, and the business goes looking
for something that is not there.</p>

<h2>The sentence that said the opposite</h2>

<p>A software foundation was told "Reviews are shown but not marked up". The evidence the check
had collected was every use of the word "review" as an ordinary verb — please review the
licence, participants are invited to review the guidelines, allow ten business days to complete
the review.</p>

<p>And one more, which is the one worth remembering. The site's own sentence stating that it does
<strong>not</strong> provide testimonials was counted as evidence that it does.</p>

<p>That is the failure in its purest form: <strong>counting a signal being mentioned as the
signal being present.</strong> A page that discusses reviews, disclaims reviews, links to a
review policy or explains why it has no reviews contains the word as often as a page covered in
them.</p>

<h2>Three more phrases that had to go</h2>

<ul>
<li><strong>"Stars."</strong> Fine on a restaurant, meaningless on a technical site, where every
repository badge says it. The word was in the list; every developer tools page in the sample
matched.</li>
<li><strong>"Five-star."</strong> A wildlife charity teaching children to build a bee hotel wrote
that it offers solitary bees five-star accommodation. The check quoted that joke back as its
evidence of displayed customer ratings. The phrase is a <em>claim about quality</em> — a
five-star hotel, five-star service — and a business describing itself that way is not showing
anybody's review.</li>
<li><strong>A street address that was a statistic.</strong> This one is ours. The address pattern
was case-insensitive and allowed several words between the house number and the street suffix,
and "way" is both a street suffix and an ordinary English word. It matched a sentence in this
project's own marketing copy about domains linking to a competitor "that way", concluded that a
Mac software company was a location-bound local business, and produced six findings including
two false high-severity headlines. <strong>Any page with a statistic in it was one sentence away
from the same fate.</strong></li>
</ul>

<h2>Why the guards cut both ways</h2>

<p>The repair to the address pattern was to require the street name to be capitalised and to
allow at most two words between the number and the suffix. That stops statistics matching. It
also means the pattern is now strict in ways that can miss real addresses — and one was found
immediately: a house number carrying a single lowercase letter, the Baker Street shape, which
the numeric-only version had been failing on all along.</p>

<p>So tightening a pattern is not free, and loosening it is not free either. What you choose
depends entirely on which error costs the reader more.</p>

<h2>The asymmetry that decides where the line goes</h2>

<p>Here the two errors are not equal, and saying why is the most useful thing on this page.</p>

<ul>
<li><strong>A missed review section</strong> produces "no customer reviews found". That is advice
to go and collect some. A business that has reviews reads it, knows better, and ignores it. The
cost is a wasted sentence.</li>
<li><strong>A false match</strong> produces "mark up the reviews you display" to a business that
displays none. It cannot be ignored, because it sounds like a technical instruction: the reader
goes looking for the review section the tool says they have, and there is nothing to find. The
cost is their afternoon and their trust in the report.</li>
</ul>

<p>So the phrase list is deliberately short and deliberately specific — named review platforms,
"out of five stars", "star rating", "what our customers say" — and it deliberately misses a page
simply headed "Reviews" with no other phrasing. That is the safer error, chosen knowingly.</p>

<p><strong>A short phrase is cheap to add and expensive to be wrong about.</strong> The source
notes that this is the sixth time a phrase has been removed for being a signal in one context and
ordinary English in another, and the third time in that one list — which tells you how strong the
pull is towards adding just one more word.</p>

<h2>How to read a phrase-matched finding on your own site</h2>

<p>Any finding that claims your pages <em>show</em> something — reviews, prices, testimonials,
locations, opening hours — was almost certainly inferred from text rather than observed. Three
questions settle it:</p>

<ul>
<li><strong>Does the report quote its evidence?</strong> If it does, read the quote before the
headline. Most of the cases above were obvious the moment somebody looked at the matched
sentence.</li>
<li><strong>Is the matched word a verb?</strong> "Review", "rate", "star", "book", "order" and
"contact" are all nouns that audits look for and verbs that people write.</li>
<li><strong>Is the page <em>about</em> the thing rather than <em>doing</em> the thing?</strong> A
policy page about reviews, a help article about booking, a blog post about pricing — each one
will match a phrase list and none of them is the signal.</li>
</ul>

<h2>When this does not matter</h2>

<p>On a genuine local business — a restaurant, a clinic, a shop with an address and opening
hours — these findings are usually right, because the phrases mean what they look like they mean.
The failure mode is concentrated on sites that are <em>not</em> location-bound and on technical
or editorial sites, where the same vocabulary is ordinary prose.</p>

<p>If your site has no premises the public visits, a local-business finding is worth a sceptical
read before it is worth any work at all.</p>

<h2>The fixes that make it worse</h2>

<ul>
<li><strong>Adding review markup to satisfy the finding.</strong> Structured data describing
reviews you do not display is a misrepresentation of your page, and it is the kind that search
engines act on.</li>
<li><strong>Rewriting your prose to avoid the trigger words.</strong> Removing "please review the
licence" from a licence page to quieten a tool is letting the tool edit your site.</li>
<li><strong>Adding a business address to a site that has no premises</strong> because a
local-business check fired. It fired because of a sentence about something else.</li>
</ul>

<h2>How to make this finding appear on any site</h2>

<p>Write a sentence about reviews. That is the whole trick, and it is why the finding's presence
is weak evidence on its own and its quoted evidence is strong evidence. <strong>A phrase list can
tell you a page mentions something; only a person can tell you the page is doing it.</strong></p>

<h2>Where this sits in an audit</h2>

<p>The registered checks are <code>local.reviews</code>, which covers review signals, and
<code>local.applicable</code>, which decides whether a site is a local business at all — the one
the address pattern feeds, and the one that was wrong about us. Both sit in the local business
area.</p>

<p>For the related habit of reading what a finding actually counted before acting on it, see
<a href="/how-to/check-the-count-on-a-finding/">a finding's count is not decoration &rarr;</a>.
For the opposite failure — a tool reporting the absence of something it simply could not
recognise — see <a href="/how-to/cta-findings-that-miss-the-form/">a form is a call to
action &rarr;</a>.</p>
"""
    return render(
        cat="how-to", slug="findings-from-phrase-matching",
        title="Why an audit finds reviews you do not have",
        desc=("Audits infer from text, and a phrase can mean two things. Why a site gets told "
              "to mark up reviews it has none of, and which error is safer."),
        h1="Why an audit finds reviews you do not have",
        crumb='<a href="/">Docket</a> / <a href="/how-to/">Fix it</a> / Phrase matching',
        body=body,
        faq=[
            ("Why does my audit say I show reviews when I do not?",
             "Because it matched a phrase rather than seeing a review. Words like review, rate "
             "and star are nouns a tool looks for and verbs people write, so a page that "
             "discusses reviews matches as readily as one covered in them."),
            ("Should I add review structured data to clear the finding?",
             "No. Markup describing reviews you do not display misrepresents the page, and that "
             "is the kind of misrepresentation search engines act on. Confirm the reviews exist "
             "first."),
            ("Why was my site classed as a local business when it has no premises?",
             "Usually a street-address pattern matching ordinary prose. Several street suffixes "
             "are common English words, so a sentence containing a number and one of them can "
             "read as an address."),
            ("Is it better for a check to miss reviews or to invent them?",
             "To miss them. A missed section produces advice to go and get reviews, which you "
             "can ignore. A false match sends you looking for a review section you do not have, "
             "which you cannot."),
            ("How do I tell a real phrase-matched finding from a false one?",
             "Read the quoted evidence before the headline, and ask whether the page is about "
             "the thing or doing the thing. A policy page about reviews matches every phrase "
             "list and is not the signal."),
        ],
    )


if __name__ == "__main__":
    print(phrase_matching())
