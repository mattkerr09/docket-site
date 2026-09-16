#!/usr/bin/env python3
"""How to fix phone links that will not dial.

Sourced from Docket's `cvr.unusable_phone` check in
`backend/seo_engine/checks/conversion.py` — its four branches, their severities
and the exact wording of their own fix text — and from the tests beside it,
which record the false positives that shaped each rule.

Every figure and every specification reference is interpolated from a constant
below rather than typed into prose, because `verify_numbers.py` refuses a typed
figure and a typed date, and an RFC number is both a figure and a citation that
somebody has to be able to age. The email survey figures come through
`facts.py`; they measure MX records and the page says so where it uses them.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import facts as F  # noqa: E402
from render import render  # noqa: E402

#: The specification, read at its own canonical home on the date below. The
#: section pointers are held here rather than typed into sentences so that a
#: correction is one edit and the prose cannot drift away from the reading.
RFC_URL = "https://www.rfc-editor.org/rfc/rfc3966"
RFC = "RFC 3966"
READ_ON = "15 September 2026"
S_NUMBERS = "section 5.1"
S_SEPARATORS = "section 5.1.1"
S_ALPHA = "section 5.1.2"
S_GLOBAL = "section 5.1.4"
S_LOCAL = "section 5.1.5"


def phone_links() -> Path:
    body = f"""
<p class="lede">Somebody reading your site on a phone taps your number. Does it dial? The
page was written on a desktop and it is checked on a desktop, and on a desktop tapping a
number is not something anybody does — so the link can be broken for years while every
person who looks at the page sees a phone number that is perfectly correct.</p>

<p>Docket's <code>cvr.unusable_phone</code> reads the <code>href</code> of every
<code>tel:</code> link on the pages it crawls and reports the shapes that cannot place a
call: letters where the digits should be, markup pasted into the number, a single repeated
digit at full number length, and a national number with neither a country code nor a
<code>phone-context</code> parameter. Each is reported as its own finding, at its own
severity, because the repairs have nothing in common.</p>

<h2>What this cannot tell you</h2>

<p>Said first, because it decides whether the finding is worth anything to you.
<strong>Docket does not ring the number.</strong> No call is placed, nothing is looked
up in a numbering plan, and no operator is asked whether the line exists.</p>

<p>So it cannot tell you the number is answered, that it is still yours, that it is current,
or that the person who used to pick it up still works there. It reads your markup and
answers one question: <em>will tapping this place a call</em>. A number that is well formed
and simply wrong — last year's line, two digits transposed, the office you closed — is a
valid <code>tel:</code> URI and this check has nothing to say about it. Closing that gap
would mean dialling strangers' phones from an audit tool, which we are not going to do.</p>

<h2>What counts as a phone number here</h2>

<p>Only a <code>tel:</code> link in the markup. A number sitting in prose is not read by
this check, and the comment in the source says why: a number in prose may be an example, a
fax, or a customer's. The same reasoning covers a <code>tel:</code> that appears inside a
JavaScript string — a grep finds it, the parser does not, and the parser is right, because a
mention is not a promise.</p>

<p>A printed number with no link on it at all is a different check in a different lane
(<code>local.phone_not_clickable</code>, which only runs for sites that look like a local
business). This page is about the link that exists and does not work.</p>

<p>Before anything is judged, the <code>href</code> is percent-decoded. That is not
housekeeping. A site writing <code>tel:0333%200146%20683</code> is writing spaces; filtering
that for digits without decoding it first turns every <code>%20</code> into a
<code>2</code> and a <code>0</code> and invents a number nobody published. Anything after a
semicolon is a parameter and not part of the number.</p>

<h2>The shapes it reports</h2>

<h3>Letters in the href</h3>

<p>A vanity number in the link itself. <a href="{RFC_URL}#section-5.1.2">{RFC} {S_ALPHA}</a>
does not support the notation, because the mapping from letters to keypad digits is not
uniform internationally, so the link dials nothing anywhere. Reported at HIGH, and the fix
text is careful about which half is wrong: <em>"Keep the memorable number as the visible
text and put digits in the href:
<code>&lt;a href="tel:+YOURPHONENUMBER"&gt;YOUR MEMORABLE NUMBER&lt;/a&gt;</code>."</em> The
printed number can stay exactly as it is. Only the thing behind it changes.</p>

<h3>HTML where the number should be</h3>

<p>An entire anchor tag pasted into the CMS field that expects a phone number, and escaped
by the CMS on the way in — so the dialable part of the <code>href</code> is markup. It is
reported separately, as <code>cvr.phone_href_markup</code>, and the separation was earned.
The letters rule used to catch this case and tell the owner to "put digits in the href",
which they already had: the visible text was an ordinary formatted number and the digits
inside the pasted tag were fine. Advice describing work that is already finished leaves a
reader one conclusion, and it is that the tool is broken.</p>

<p>So this finding says, in as many words, that <strong>the page still looks right</strong>,
and its fix points at the field rather than the copy: <em>"Open the phone-number field in
your CMS and look at what is actually stored in it. Clear it and type the number by itself —
digits and separators only, no <code>&lt;a&gt;</code> tag — and let the template build the
link around it."</em></p>

<h3>A placeholder nobody filled in</h3>

<p>Every digit the same, at seven digits or more. A template that shipped with the example
still in it, reported at HIGH, and the fix is one line: <em>"Replace it with the real number,
or remove the link."</em></p>

<p>The length floor is there because of a real accusation. Without it, the rule fired on
<code>111</code> — a national non-emergency
health line — and said anyone tapping it reaches nobody. <code>999</code>,
<code>911</code>, <code>000</code> and <code>112</code> have exactly the same shape. A
repeated digit is only evidence of an unfilled template at full number length; shorter than
that it is a short code, and short codes are precisely the numbers a health or emergency
service publishes.</p>

<h3>A national number with no way to reach it from outside</h3>

<p><a href="{RFC_URL}#section-5.1">{RFC} {S_NUMBERS}</a> is blunt about this: all phone
numbers must use the global form unless they cannot be represented that way, and a local
number must carry a <code>phone-context</code> parameter naming where it is valid. A bare
national number has neither. It dials correctly from inside the country and incorrectly from
outside it — a total failure for a visitor abroad and none at all for one already there.</p>

<p>So the severity follows what the site itself declares. LOW by default. MEDIUM where the
site publishes <code>hreflang</code>, because a site with <code>hreflang</code> has said it
wants visitors who would be dialling from abroad. That is read from the markup rather than
guessed from the kind of business. The fix again leaves the printed number alone:
<em>"Prefix the country code and a plus in the href, leaving the visible text alone:
<code>&lt;a href="tel:+YOURPHONENUMBER"&gt;YOUR PHONE NUMBER, spaced as you print
it&lt;/a&gt;</code>."</em></p>

<p>The global form is the <code>+</code> and the country code
(<a href="{RFC_URL}#section-5.1.4">{RFC} {S_GLOBAL}</a>). The sanctioned alternative for a
number that genuinely cannot be written that way is the parameter:
<code>tel:5551234;phone-context=+1</code>, or a domain you control
(<a href="{RFC_URL}#section-5.1.5">{RFC} {S_LOCAL}</a>). Docket accepts either and says
nothing.</p>

<h2>Where the check and the specification disagree</h2>

<p>Stated here, because this is the wrong page to hide them.</p>

<p><strong>Short codes get advice the specification says cannot work.</strong> A bare
<code>111</code> or <code>911</code> in an <code>href</code> is still reported as not being
in international format, and the fix text offered is "prefix the country code". {RFC}
{S_NUMBERS} says emergency and service numbers cannot be represented in global form and must
be tagged with a <code>phone-context</code> instead; it points out that
<code>+1-911</code> is not a valid global number. The finding is defensible — a local
number with no context genuinely is outside the specification — and its remedy is not the
one the specification gives. The placeholder rule was taught about short codes. This branch
has not been.</p>

<p><strong>Spaces are tolerated and the specification forbids them.</strong>
<a href="{RFC_URL}#section-5.1.1">{RFC} {S_SEPARATORS}</a> says a <code>tel</code> URI must
not use spaces as visual separators. Docket reads <code>tel:+44 20 7946 0958</code> and
reports nothing at all. That is the check being deliberately narrow rather than
specification-complete: it reports the things that stop a call being placed, and a space
does not. Worth knowing if you are validating against the standard rather than against
what a handset does.</p>

<p>Every reading of the specification on this page is from
<a href="{RFC_URL}">{RFC}, the <code>tel</code> URI scheme</a>, read at rfc-editor.org on
{READ_ON}.</p>

<h2>One number in a template is one number</h2>

<p>A phone number lives in the header, or the footer, or both — which means a site that
writes it wrongly writes it wrongly everywhere. The finding therefore names the distinct
numbers and counts the pages, not the links. That matters for the size of the job it seems
to describe: the repair is one line of a template, and a finding that counted occurrences
read as a morning's work.</p>

<h2>Checking your own, without a tool</h2>

<p>Read the hrefs rather than the page:</p>

<pre><code>curl -s https://example.com/ | grep -o 'href="tel:[^"]*"'</code></pre>

<p>What you want back is a <code>+</code>, a country code, and digits. What you do not want
is a letter, an angle bracket, or the same digit over and over. This will also show any
<code>tel:</code> written inside a script, which Docket ignores — so read what it prints
rather than counting it.</p>

<p>Then do the thing the desktop cannot do: open the page on an actual phone and tap the
number. The whole class of failure exists because that step is the one nobody takes.</p>

<h2>The same failure, one channel over</h2>

<p>An email address on a domain that cannot receive mail fails in the same silent way, and
that one we have measured. Among UK shop websites sampled from OpenStreetMap,
{F.small_publishing_pct()}% publish an address in a <code>mailto:</code>, and
{F.small_dead()} of the {F.small_publishing()} domains publishing one cannot accept mail —
<a href="/learn/dead-contact-address/">the survey and its limits are on that page</a>. It
measured MX records. Nothing in it is a measurement of phone links, and that rate does not
carry across to them; we have not surveyed phone links at all.</p>

<p>If your customers find you in a map, the rest of that ground — business schema, the name,
address and phone matching your listing, the place named in your titles — is on
<a href="/for/local-business/">why your business is not in the map pack</a>. The lane this
check sits in, and what else is in it, is on
<a href="/learn/conversion-audit/">the conversion audit page</a>.</p>

<p><a class="btn" href="/download/">Download Docket</a></p>
"""
    return render(
        cat="how-to", slug="fix-phone-links-that-will-not-dial",
        title="How to fix phone links that will not dial",
        desc=("A tel: link can look perfect on screen and dial nothing when tapped. What "
              "Docket's cvr.unusable_phone check reads in the href, and what it cannot "
              "tell you."),
        h1="Phone links that will not dial",
        crumb='<a href="/">Docket</a> / <a href="/how-to/">Fix it</a> / '
              'phone links that will not dial',
        body=body,
        schema_type="Article",
        faq=[
            ("Why does a tel: link work on my desktop but not on a phone?",
             "It does not work on either. Nobody taps a phone number on a desktop, so "
             "the failure only shows itself on the device you are not testing on."),
            ("Does Docket call the number to check it?",
             "No. It reads the href and reports whether tapping it would place a call. It "
             "cannot tell you the line is answered, that the number is current, or that it "
             "is still yours."),
            ("Can I keep a memorable vanity number on the page?",
             "Yes. Keep it as the visible text and put digits in the href. The tel URI "
             "scheme does not support letters, because the mapping from letters to keypad "
             "digits is not the same in every country, so a vanity href dials nothing."),
            ("Do I have to write my number in international format?",
             "RFC 3966 says all phone numbers must use the global form — a plus and a "
             "country code — unless they cannot be represented that way, and that a local "
             "number must carry a phone-context parameter saying where it is valid. Docket "
             "reports a number with neither at LOW, or at MEDIUM where the site publishes "
             "hreflang and is therefore asking for visitors who would dial from abroad."),
            ("Why is my emergency or service short code being reported?",
             "Because it has no country code and no phone-context parameter, so it falls "
             "into the not-in-international-format branch. The advice offered there does "
             "not fit it: the specification says service and emergency numbers cannot be "
             "written in global form and should carry a phone-context instead. It is a "
             "gap in the check, and it is the reason the placeholder rule ignores anything "
             "shorter than a subscriber number."),
            ("What does phone-context do?",
             "It names the scope in which a local number is unique — a country dialling "
             "prefix, or a domain you administer. A local number plus its context is "
             "globally unique again, which is what makes the link usable from outside."),
        ],
    )


BUILDERS = [phone_links]


def build_all() -> list[Path]:
    return [b() for b in BUILDERS]


if __name__ == "__main__":
    for p in build_all():
        print(p)
