"""A form is a call to action — and a checker that knows one shape misses it.

Promised on the how-to hub. Sourced from two recorded cases in the app repo,
both learned on the same day:

  * `cvr.no_cta` reported a page whose entire content is a three-field quote
    form as having nothing that asks the visitor to do anything — and its own
    sentence listed "quote request" among the things it could not find.
  * `cvr.form_friction`'s capture branch matched English anchor phrases and
    English slugs, so it could not see a contact route written in any other
    words.

The source states the general fault in its own words: the check knew one shape
of the thing and reported the absence of every other shape as the absence of
the thing. That sentence is the page.

⚠️ NO SITE IS NAMED. The first case is the project's own ground-truth fixture,
so there is nobody to name; the third-party gate applies to the rest.

⚠️ THE TWO-FIELD THRESHOLD IS DELIBERATE AND IMPERFECT, AND THE PAGE SAYS SO.
Site search is the common single-field form and counting it would silence the
check nearly everywhere, which is the worse error. A newsletter box alone still
counts as no call to action.

Numerals: none. Quantities are spelled as words.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from render import render  # noqa: E402


def cta_forms() -> Path:
    body = """
<p class="lede">An audit reports that a page has no call to action: nothing on it asks the
visitor to do anything — no quote request, no booking, no purchase, no contact. The page is a
quote request. Its entire content is a short form headed "tell us what you need", and the
finding that could not see it listed the exact thing it was looking at among the things it
could not find.</p>

<h2>The fault, stated generally</h2>

<p>That finding was not lazily written. It was checking for buttons and links — the shape a
call to action usually takes — and it was right that there were none. What it then said was
that there was no call to action, which is a different claim and a false one.</p>

<p><strong>A checker that knows one shape of a thing will report every other shape as the
absence of the thing.</strong> That is the whole failure mode, and once you have the sentence
you will find it in most audit reports you read: "no social proof" on a site whose reviews load
from a widget, "no contact details" on a site whose contact page is called something else, "no
schema" on a site using a format the tool does not parse.</p>

<p>The tell is a finding phrased as an absence across a whole page or site. An absence is the
hardest thing to check and the easiest thing to assert.</p>

<h2>Why a form counts</h2>

<p>Plenty of pages convert without a button. An enquiry form, a booking widget, a quote
request, a callback box — the form is not a step towards the action, it <em>is</em> the action,
and there is nothing to click because there is nothing to click through to.</p>

<p>So the repair was to count a form as a call to action. Which immediately raises the question
of what a form is, and the answer Docket uses is deliberately crude: <strong>two or more visible
fields</strong>.</p>

<h2>The limit, kept on purpose</h2>

<p>One field is almost always site search. Counting a single-field form would mean nearly every
site on the web has a call to action on every page, and the check would stop saying anything at
all. A landing page with no action on it is a real and expensive problem, so silencing the check
everywhere to fix one false positive would be the worse trade.</p>

<p>Two consequences follow, and both are honest limits rather than oversights:</p>

<ul>
<li><strong>A newsletter box alone still counts as no call to action.</strong> An email signup
is a real thing to want, but it is not the action a page selling something exists for, and a
page whose only ask is "join our list" is usually a page that forgot to ask for the sale.</li>
<li><strong>Docket does not read your field labels to decide what your form is for.</strong> It
could guess, and a guess that is right most of the time would produce confident wrong sentences
the rest of the time. Field count is blunt, it is stated plainly, and you can overrule it in a
second because you know what your form does.</li>
</ul>

<h2>The same mistake, wearing a different coat</h2>

<p>The check that looks for a route to contact you had this too, and its version shows how the
fault survives a first fix. It recognised contact routes by anchor text and URL slugs — the
English words people use for a contact page. On an English site that works. On any other site it
sees nothing, and reports that visitors have no way to get in touch.</p>

<p>The repair was the same move: count the routes that do not depend on language. A form, a
<code>mailto:</code> link, a <code>tel:</code> link, a message link. Those are the same in every
language.</p>

<p>What remains is worth naming, because it is still a limit today: a perfectly good contact
link written in the site's own language, with no form and no protocol link beside it, is still
invisible to that check. It is better than it was and it is not finished.</p>

<h2>What to check on your own pages</h2>

<p>Take the pages that are supposed to make money — product, service, pricing, contact,
booking — and ask of each one what a visitor who has decided is meant to do next. Then check
that the thing is actually reachable:</p>

<ul>
<li>A button or link, which is what most tools look for.</li>
<li>A form with enough fields to be an enquiry rather than a search box.</li>
<li>A phone or message link that opens the thing it promises.</li>
<li>A booking or checkout widget — and if it loads after the page renders, expect every
audit tool to miss it and to say so at a lower severity if it is honest.</li>
</ul>

<h2>When this does not matter</h2>

<p>The finding is rated high, and it runs only on the pages judged to be doing commercial
work — not on your blog. An article with no call to action is an article, and the absence of one
there is a stylistic choice rather than a fault.</p>

<p>It is also worth ignoring on a page whose action loads from a third-party script, once you
have confirmed the action is really there. The tool reads the markup it was served; it does not
watch the page work.</p>

<h2>The fixes that make it worse</h2>

<ul>
<li><strong>Adding a button to a page that already converts.</strong> A quote form with a
redundant "Contact us" link above it is not a better page, it is a page with two answers to one
question.</li>
<li><strong>Adding a newsletter box to clear the finding.</strong> It will not clear it, and if
it did you would have swapped the sale for an email address.</li>
<li><strong>Padding a one-field form to two fields.</strong> This does clear the finding. It
also makes the form worse, which is the opposite of the point.</li>
</ul>

<h2>How to clear this finding without improving anything</h2>

<p>Said plainly because it is the honest consequence of a blunt rule: add a second field to any
single-field form and the page now has a call to action as far as the tool is concerned.
Nothing about the page got better and one thing got slightly worse.</p>

<p>Which is the argument for reading a finding rather than clearing it. <strong>A rule simple
enough to be trustworthy is always simple enough to be satisfied dishonestly</strong>, and the
only defence is that you know what your page is for and the tool does not.</p>

<h2>Where this sits in an audit</h2>

<p>The two registered checks are <code>cvr.no_cta</code>, which covers calls to action, and
<code>cvr.form_friction</code>, which covers form length and also emits the
missing-contact-route finding. Both live in the conversion and landing pages area — see
<a href="/learn/conversion-audit/">what that lane checks and what it deliberately does
not &rarr;</a>.</p>

<p>For the related habit of reading the number attached to a finding before acting on it, see
<a href="/how-to/check-the-count-on-a-finding/">a finding's count is not decoration &rarr;</a>.</p>
"""
    return render(
        cat="how-to", slug="cta-findings-that-miss-the-form",
        title="A form is a call to action",
        desc=("An audit that looks for buttons can report a quote page as having nothing to "
              "click. Why a form counts on a site, and what must not."),
        h1="A form is a call to action",
        crumb='<a href="/">Docket</a> / <a href="/how-to/">Fix it</a> / Calls to action',
        body=body,
        faq=[
            ("Does a contact form count as a call to action?",
             "It should. On many pages the form is the action rather than a step towards it, "
             "so a tool that only looks for buttons and links will report a working enquiry "
             "page as having nothing to click."),
            ("Why does a single-field form not count?",
             "Because one field is almost always site search. Counting it would mean nearly "
             "every page on every site passes, and the check would stop being able to find the "
             "landing pages that genuinely ask for nothing."),
            ("Does a newsletter signup count as a call to action?",
             "Not on its own. An email signup is worth having, but a page whose only ask is to "
             "join a list is usually a page that forgot to ask for the sale."),
            ("My audit says my pages have no way to contact me, but they do. Why?",
             "Checks that recognise contact links by their wording only see the language they "
             "were written for. Forms and mailto, tel and message links are language "
             "independent, which is why those are counted first."),
            ("Should I add a button just to clear the finding?",
             "No. If the page already converts, a redundant link above the form gives one "
             "question two answers. Read the finding, confirm the action exists, and move on."),
        ],
    )


if __name__ == "__main__":
    print(cta_forms())
