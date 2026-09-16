#!/usr/bin/env python3
"""`mar.email_capture` — "Email list building", explained from its own source.

⚠️ WHY THIS PAGE EXISTS AND WHY IT IS NOT THE TRACKING-LANE PAGE.
`/learn/marketing-tag-audit/` owns the lane: it lists every martech check and
argues the coverage question — is the tag on every page. This page takes one
check off that list and reads it line by line, because this particular check is
the one whose *name* misleads. "Email list building" sounds like a judgement
about a form. It is not one. The two pages link to each other rather than
repeating.

**No dataset.** There is no survey behind this page and no figure is quoted
from one. Everything on it is a fact about the shipped check, read from
`backend/seo_engine/checks/martech.py` in the app repo. Where a count appears it
is `len()` of the same object the page prints.

**No external source, deliberately.** The obvious thing to reach for here is an
industry statistic about email — return on spend, list value, signup conversion
rates. Not one of the figures in circulation traces to a primary document that
can be linked and dated, so none of them is on the page. The check itself is
the citation; that is the whole argument of `docs/PAGE_ANATOMY.md`.

WHERE THE BRIEF WAS WRONG — section 9, and this time it caught the brief twice.

1. **"Docket can tell that a form exists and roughly what it asks for."** Not
   here. `mar.email_capture` never looks at a form. It reads `page.text`, which
   is `dom.main_text()` — documented as "Body text minus nav/header/footer/
   aside/form", over `BOILERPLATE_TAGS = frozenset("nav header footer aside
   form".split())`. The `<form>` element is one of the five regions that field
   throws away. A different check, `cvr.no_capture` in `checks/conversion.py`,
   is the one that counts forms and `mailto:`/`tel:`/`sms:` links.

2. **"Someone who assumes a footer form counts as a list-building strategy."**
   The reader is real, but the irony runs the other way: a footer signup is
   close to invisible to this check. `<footer>` is stripped by `main_text` as
   well, so the only route left for it is `page.ctas` — anchors, buttons and
   submit inputs from anywhere in the document. The button label is what gets
   seen, never the form.

3. **"Its threshold."** There is no threshold on capture. There is a threshold
   on the *site*: the finding is withheld unless `len(ctx.indexable) >= 5`.

Also recorded on the page because it is honest and load-bearing: the check's
own `fix` text asserts that a bare newsletter ask "converts poorly". The check
measures no conversion rate at all. The page quotes the sentence and says so.

**Two constants are transcribed, not derived.** `SCAN_CAP` and `MIN_PAGES`
below are copied from the check's source; nothing in this repo fails when the
engine changes them. Flagged in the handover as a gap, not hidden here.
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from render import DATA, render  # noqa: E402

#: When the check's source was read and these constants transcribed from it.
#: A date in prose is refused by the derived-number gate and it is right to be:
#: a date in two places drifts in one of them.
READ_HUMAN = "15 September 2026"

#: The phrases `mar.email_capture` matches, transcribed verbatim from the
#: check. Printed and counted from this one tuple, so the count on the page
#: cannot disagree with the list beside it.
PHRASES = (
    "newsletter", "subscribe", "sign up for", "join our list",
    "email updates", "stay in the loop", "get updates", "mailing list",
)

#: The email tools whose presence makes the check stand down. Also the only
#: three email tools in `extract.TRACKERS` — the short-circuit covers every one
#: the tracker table can recognise, which is a narrower set than the market.
ESPS = ("Klaviyo", "Mailchimp", "HubSpot")

#: `ctx.indexable[:40]` — how many pages the phrase scan reads.
SCAN_CAP = 40
#: `len(ctx.indexable) >= 5` — below this the finding is not emitted at all.
MIN_PAGES = 5


def _row(check_id: str) -> dict:
    with (DATA / "checks.csv").open() as handle:
        for row in csv.DictReader(handle):
            if row["id"] == check_id:
                return row
    raise SystemExit(f"{check_id} is not in checks.csv")


def email_capture_audit() -> Path:
    row = _row("mar.email_capture")
    phrases = "\n".join(f"<li><code>{p}</code></li>" for p in PHRASES)
    esps = ", ".join(ESPS)
    lane_label = row["lane_label"].replace("&", "&amp;")

    body = f"""
<p class="lede">Is your site actually collecting email, or does it only look as though it
is? Docket has a check called <strong>{row["title"]}</strong> — <code>mar.email_capture</code>,
in the <strong>{lane_label}</strong> lane — and the honest answer is that it settles
a much smaller question than its name suggests.</p>

<p>Here is the whole of it. The check stands down if an email tool's tag is already on the
site. Otherwise it reads the opening of each page's body copy, plus the text of its buttons
and of any link that reads as a call to action, and looks for any of a short list of words.
If it finds one, it says nothing. If it finds none, it reports that no email capture was
seen. It never looks at a form.</p>

<h2>What it actually does, in order</h2>

<p><strong>First, language.</strong> The phrase list is English, so the check asks
<code>ctx.prose_language_supported</code> and returns immediately on a site whose prose is
in another language. That gate exists across the codebase because English phrase lists, run
against a site that is not in English, find nothing and report the absence as a fact.</p>

<p><strong>Second, the tag.</strong> It collects the site's trackers and stops if any of
{esps} is among them. That set is not a shortlist of good tools — it is every email
platform the tracker table can recognise, all {len(ESPS)} of them. A site running any other
email service gets no credit for it here and falls through to the word search.</p>

<p><strong>Third, the words.</strong> It walks the first {SCAN_CAP} indexable pages and, for
each, joins the opening of <code>page.text</code> to that page's call-to-action strings,
lowercases the result, and tests it against these:</p>

<ul>
{phrases}
</ul>

<p>The test is a plain substring match, and one hit anywhere stops the scan.</p>

<p><strong>Fourth, the site's size.</strong> Even with nothing found, the finding is
suppressed unless the crawl saw at least {MIN_PAGES} indexable pages, so a smaller site is
never told it has no email capture.</p>

<p>What comes out, when all of that lines up, is a <strong>low-severity</strong> finding with
a <strong>small</strong> effort estimate. It is also marked as requiring a full crawl, which
means the report drops it when the crawl was degraded rather than presenting an absence
gathered from a handful of pages as a fact about the site.</p>

<p class="byline">Every statement above was read from the shipped check's source on
{READ_HUMAN}. If the phrase list or the page limits change in a release, this page is
describing the version before it.</p>

<h2>It does not look for a form</h2>

<p>This is the part worth carrying away, because the check's name argues against it.</p>

<p><code>page.text</code> is built by <code>dom.main_text()</code>, whose docstring reads
"Body text minus nav/header/footer/aside/form". The footer and the form element are two of
the regions it discards. So the signup box in your footer — the one with
the email field and the button — sits inside the two regions this field is defined to
discard. Its words are not in <code>page.text</code> at all.</p>

<p>The one route that survives is <code>page.ctas</code>, which is collected from anchors,
buttons and submit inputs anywhere in the document. If your footer button says
<em>Subscribe</em>, the word arrives that way. If it says <em>Go</em>, or <em>Send</em>, or
it is an arrow icon with no text, nothing arrives and the form is invisible to this check
however well it works.</p>

<p>The inverse is just as true. A page carrying an <code>&lt;input type="email"&gt;</code>
and the sentence "we will let you know when it is back in stock" has a working capture and
none of the listed words, and the check will report it as missing. A blog post about how to
write a newsletter has no capture at all and will pass.</p>

<h2>A substring match is a loose match</h2>

<p>The comparison is <code>phrase in low</code> — a bare substring, not a word-boundary
match. The same codebase has a recorded incident about exactly this shape elsewhere: a
boundary matcher was written for the call-to-action list after ordinary footer links were
counted as calls to action, and the first example in that comment is that
<em>Unsubscribe</em> contains <em>subscribe</em>. That fix was applied to the CTA
vocabulary. This check still compares the plain way.</p>

<p>So a page that says "unsubscribe at any time", or links to a subscriber agreement,
satisfies the search. The error runs in the direction of silence: the check finds a word,
concludes there is a capture, and says nothing. Nothing is reported, nothing looks wrong,
and the finding you did not get is the one you cannot act on.</p>

<h2>What it cannot tell you</h2>

<p>Lead with this, because it is most of the answer to the question at the top.</p>

<p>Docket reads markup. It can observe that a word is present on a page it fetched. It
cannot observe anything on the other side of the form: whether a visitor ever completes it,
whether the address is written anywhere, whether the endpoint the form posts to still
exists, whether a confirmation mail is sent, or whether the list has been mailed once since
the day it was created. A capture that quietly drops every address into a disconnected
inbox reads, from the markup, exactly like one that works.</p>

<p>It also says nothing about how many people sign up, and this page will not estimate it.
No rate appears here, because none was measured — and a number attached to somebody's
signup form by a tool that has never seen a single visitor session is an opinion wearing a
decimal point.</p>

<p>The check itself is less careful about that boundary, and the honest thing is to show
you where. Its fix text, verbatim from the source, reads:</p>

<blockquote><p>Add a single email capture with a real reason to subscribe — a useful guide, a
price list, an availability alert. A bare 'subscribe to our newsletter' converts poorly;
offering something specific converts well.</p></blockquote>

<p>The first sentence is a mechanical instruction and the check can support it. The second
is advice. The check measured no conversion rate on your site or on anyone's, and you should
read that sentence as the opinion of whoever wrote the check rather than as a finding.</p>

<h2>Why the check exists at all, stated mechanically</h2>

<p>The reason to have a capture is not a statistic. It is that search results, social feeds
and ad auctions are all addressed <em>to</em> you by somebody else's system, and a mailing
list is addressed by yours. When a ranking moves or an account is suspended, the list is the
only route to the same people that does not go through the thing that changed. That is a
property of who owns the address book, and it is true without any figure under it.</p>

<h2>Where the nearby checks pick up</h2>

<p>Two of them are worth knowing about, because each answers something this one does not.</p>

<p>The tag half of this check reads the same tracker table as the rest of the lane, and that
table is what the coverage checks work from — whether the tags you believe are running
appear on every page rather than on the template they were added to.
<a href="/learn/marketing-tag-audit/">The tracking lane, and the coverage question it is
built around.</a></p>

<p>The form half belongs to a different lane entirely. <code>cvr.no_capture</code> is the
check that does count forms, and <code>mailto:</code>, <code>tel:</code> and
<code>sms:</code> links, and anything labelled contact, enquire, book or support — and it
fires at high severity when a site has none of them. Its question is whether a visitor can
reach you at all, not whether you are building a list.
<a href="/learn/conversion-audit/">What the conversion lane judges, and what it refuses to
judge for you.</a></p>

<h2>Checking this yourself</h2>

<p>You do not need the tool for the part that matters, and the part that matters is not the
markup. Open your own site on a phone, find the signup, and put a real address into it — one
you can read, not the one the form was built to notify. Then wait.</p>

<p>If nothing arrives, you have learned the thing no crawler can tell you. If something
arrives, open the list itself and look at the date of the most recent send. A capture
feeding a list nobody has mailed in a year is collecting addresses, not building an
audience, and no check in any tool will ever report it.</p>

<p><a class="btn" href="/download/">Download Docket</a></p>
"""

    return render(
        cat="learn", slug="email-capture-audit",
        title="Email capture audit: the check that ignores your form",
        desc=(f"Docket's email list building check never looks at a form. It looks for an "
              f"email tool's tag, or {len(PHRASES)} words in your copy — and here is what "
              f"that can and cannot tell you."),
        h1="Email capture audit",
        crumb='<a href="/">Docket</a> / <a href="/learn/">Learn</a> / Email capture',
        body=body,
        schema_type="Article",
        faq=[
            ("Does Docket check whether my newsletter signup form works?",
             f"No. The email list building check never inspects a form. It looks for an "
             f"email platform's tracking tag, and failing that for one of {len(PHRASES)} "
             f"English phrases in your body copy or your button text. Whether the form submits, "
             f"where the address goes, and whether anyone reads it are all outside what a "
             f"crawler can see."),
            ("Why did Docket say I have no email capture when I do?",
             "Most likely because none of the words it looks for appear near it. The "
             "check reads body copy with the nav, header, footer, aside and form regions "
             "removed, plus the text of buttons and links. A footer form whose button "
             "says Go rather than Subscribe puts nothing in either place, so the capture "
             "is real and invisible to this check."),
            ("Why did Docket stay quiet when I have no signup anywhere?",
             f"Three things silence it. An email platform's tag anywhere on the site; a "
             f"crawl of fewer than {MIN_PAGES} indexable pages; or any page containing one "
             f"of the phrases as a substring, which includes the word unsubscribe, since it "
             f"contains subscribe. The check compares plainly rather than on word "
             f"boundaries."),
            ("Will an email list improve my conversion rate?",
             "This page will not tell you, and neither will the check. No conversion rate "
             "was measured. The mechanical argument for a list is narrower and does not "
             "need a figure: search, social and ad platforms reach your audience through "
             "systems you do not control, and a list reaches the same people through one "
             "you do."),
            ("Does the check work on a site that is not in English?",
             "No, and it says so by standing down. The phrase list is English, so the "
             "check returns before doing anything on a site whose prose is another "
             "language. Reporting an absence found by an English word list on a site that "
             "is not in English would be a fact about the word list, not about the site."),
        ],
    )


BUILDERS = [email_capture_audit]


def build_all() -> list[Path]:
    return [b() for b in BUILDERS]


if __name__ == "__main__":
    for p in build_all():
        print(p)
