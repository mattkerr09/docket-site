"""A guard that stops one false positive can silence a true finding elsewhere.

Promised on the how-to hub. Sourced from `brand.py`, registered check
`brand.name_consistency`:

  * a preprint archive's logo link is named "archive home". The raw guard passed
    it because "archive" is not a weak word; the salvage step stripped "home" —
    the same salvage that correctly turns "NHS homepage" into "nhs" — and left
    "archive", recorded as a second name the site uses for itself.
  * the rule that fixed it: a link's accessible name is the WEAKEST of four
    sources (it describes a destination, not an identity), so the residue has
    to RESEMBLE THE DOMAIN, the one identity signal a site cannot fake. Measured
    across crawled sites: every real residue resembles its domain; only the
    navigation label does not.
  * ⚠️ THE FIRST VERSION REQUIRED CORROBORATION UNCONDITIONALLY AND BROKE A
    POSITIVE CONTROL. A test asserts that a logo naming one institution on a
    site titled after another IS reported — a real disagreement on a domain
    resembling neither. Demanding corroboration everywhere made the logo source
    incapable of ever being the odd one out: one site's false positive traded
    for another site's false negative.
  * the narrower condition: whether the salvage HAD TO RUN AT ALL. A name that
    was already plain is read as before; one that needed a navigation word
    stripped is a description of a destination.
  * the occurrence floor: a name seen once out of dozens of signals is a single
    odd page, not a second brand — a tagline in one title reported as a company
    name is the kind of confident nonsense that discredits a whole report.
    Declared identity still counts at one occurrence.

⚠️ NO SITE OR VENDOR IS NAMED — third-party gate. The archive, the health
service, the two institutions and the delicatessen are described by category.

⚠️ /how-to/what-your-site-says-you-are-called/ (528) owns four other cases from
this same check, including the harm in rewriting a link's accessible name. This
page owns the REGRESSION and the narrower condition, and links there for the
attribute distinction rather than restating it.

Numerals: none. Quantities spelled as words.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from render import render  # noqa: E402


def fix_false_negative() -> Path:
    body = """
<p class="lede">Every false positive you have ever reported to a tool gets fixed the same way:
somebody adds a condition. The part nobody sees is what that condition does to every other site
the check runs on — because the usual way to stop a rule being wrong about you is to make it
quieter about everyone, and quiet is indistinguishable from correct.</p>

<h2>The navigation label that became a company name</h2>

<p>A preprint archive's logo is a link, and that link's accessible name is "archive home". Good
accessibility practice: it tells a screen-reader user where the link goes.</p>

<p>A check that works out what a site calls itself reads four sources, and one of them is that
accessible name. It has a salvage step that strips navigation words, because plenty of real logo
labels look like "[Company] homepage" and the company is what you want. So "home" came off, and
"archive" was recorded as one of two names the organisation uses for itself.</p>

<p>It is not a name. It is the section the link points to, with the word "home" removed by a step
that was working exactly as designed.</p>

<h2>The rule that fixed it, and why it is about the domain</h2>

<p>A link's accessible name is the weakest of the four identity sources. Structured data and
<code>og:site_name</code> are <em>declarations</em> — a site saying who it is. A link name is a
<em>description of a destination</em>. So the weak source was made to corroborate against the one
identity signal a site cannot easily fake: its own domain.</p>

<p>Across crawled sites the pattern held cleanly — every genuine residue resembles the domain, and
only the navigation label does not:</p>

<table>
<tr><th>What the logo link was called</th><th>Resembles the domain?</th></tr>
<tr><td>The company's name, plainly</td><td>Yes</td></tr>
<tr><td>The company's name plus a description of itself</td><td>Yes</td></tr>
<tr><td>A health service's initials plus "homepage"</td><td>Yes</td></tr>
<tr><td>"archive home", on an archive whose name is not "archive"</td><td>No</td></tr>
</table>

<h2>And then the fix broke a site it had never seen</h2>

<p>This is the half worth publishing.</p>

<p>The first version of that fix required corroboration from <em>every</em> residue. It is the
obvious reading of the rule and it is wrong, because a test in the suite asserts the opposite case:
a logo naming one institution, on a site titled after a completely different one, on a domain
resembling neither. That is a real disagreement, and it is precisely what this check exists to
find.</p>

<p>Demanding corroboration everywhere made the logo source <strong>incapable of ever being the odd
one out</strong>. One site's false positive had been traded for another site's false negative — and
a false negative makes no noise at all. Nobody writes in to say a tool failed to tell them
something.</p>

<h2>The narrower condition</h2>

<p>What separates the two cases is not the name. It is <strong>whether the salvage had to run at
all.</strong></p>

<ul>
<li><strong>An accessible name that was already a plain name</strong> — the company, and nothing
else — is a declaration in everything but format. It is read as before, corroborated or not.</li>
<li><strong>One that needed a navigation word stripped off it</strong> was a description of a
destination, and what remains is as likely to be the section as the company. That residue has to
resemble the domain before it counts.</li>
</ul>

<p>The general form: <strong>when a guard is about to silence a whole source, ask what made this
case suspicious, and condition on that instead of on the source.</strong> The suspicious thing here
was never "logo links are unreliable" — it was "this string only became a name because we edited
it".</p>

<h2>What the rule costs, stated plainly</h2>

<p>A company whose domain does not contain its name — a rebrand still living on the old host —
loses this one source, and only when a navigation word had to be removed to find the name. Its
declarations are untouched, so the name is still seen. That is the trade, it was taken
deliberately, and it is the kind of thing a tool should tell you rather than leave you to
discover.</p>

<h2>The other half of not being silly about names</h2>

<p>A related guard, worth knowing because it changes how you read any "second brand" finding: a
name seen once across dozens of signals is a single odd page, not a second identity. A
delicatessen that puts its tagline in one page title is not announcing a new company, and reporting
it as one is the sort of confident nonsense that costs a report its credibility.</p>

<p>Declared identity is exempt: structured data or <code>og:site_name</code> counts at a single
occurrence, because saying it once is still saying it.</p>

<h2>Reading this on your own report</h2>

<ol>
<li><strong>When a tool names a "second brand" you do not recognise, find where it came from.</strong>
A navigation label, a tagline and a section heading all look like names once they are out of
context.</li>
<li><strong>Check how many times it appears.</strong> Once, in a site's worth of signals, is a page
rather than a policy.</li>
<li><strong>Check your declarations first.</strong> Your structured data and
<code>og:site_name</code> are what you have actually claimed; everything else is inference.</li>
<li><strong>Do not rewrite a link's accessible name to satisfy a finding</strong> — it is there for
a reason, and <a href="/how-to/what-your-site-says-you-are-called/">the harm in that is a page of
its own &rarr;</a>.</li>
</ol>

<h2>When the finding is real</h2>

<p>Two genuinely different names for one organisation, across titles and declarations, is worth
fixing — it splits the signals that tell a search engine and an assistant that all these pages
belong to one entity. The point of the guards above is that this finding only means something when
it is rare, and a check that produces it on ordinary sites has made it mean nothing.</p>

<h2>The fixes that make it worse</h2>

<ul>
<li><strong>Changing your accessible names so a tool stops guessing.</strong> They describe
destinations for people who cannot see the logo. That is not negotiable against a report.</li>
<li><strong>Adding your company name into every navigation label.</strong> Now every link says the
same thing and none of them says where it goes.</li>
<li><strong>Removing the odd title rather than the inconsistency.</strong> If two real names exist,
picking one is the fix; deleting the page that revealed it is not.</li>
</ul>

<h2>What this means for any tool you trust</h2>

<p>When you report a false positive and it gets fixed, the honest question to ask is what the fix
cost. A condition that makes a rule quieter about you probably made it quieter about somebody else
too. <strong>The only reason the regression above was caught is that a test existed asserting the
opposite case</strong> — a site where that source <em>should</em> disagree with the rest. Reasoning
would not have caught it; the suite did.</p>

<h2>Where this sits in an audit</h2>

<p>The registered check is <code>brand.name_consistency</code>, which compares the names your site
uses for itself. For four other ways it got that wrong — including why rewriting a logo link's
accessible name is the wrong repair — see
<a href="/how-to/what-your-site-says-you-are-called/">what your site says you are called
&rarr;</a>. For the wider lane, see <a href="/learn/brand-consistency/">brand consistency
&rarr;</a>.</p>
"""
    return render(
        cat="how-to", slug="when-a-fix-creates-a-false-negative",
        title="A fix that hid a real problem somewhere else",
        desc=("An audit stopped reading a navigation label as a brand name — and that fix "
              "left the same check unable to flag a real disagreement on another site."),
        h1="A fix that hid a real problem somewhere else",
        crumb='<a href="/">Docket</a> / <a href="/how-to/">Fix it</a> / Fixes with a cost',
        body=body,
        faq=[
            ("Why did an audit report my navigation label as a company name?",
             "Because a logo link's accessible name describes where the link goes, and a step "
             "that strips navigation words can leave a section name behind. What remains is as "
             "likely to be the section as the company."),
            ("How should a tool decide whether a logo link name is a real brand name?",
             "By whether it had to edit the string to get one. A name that was already plain is "
             "close to a declaration; one left over after a navigation word was stripped should "
             "have to resemble the domain before it counts."),
            ("Can fixing a false positive cause a false negative?",
             "Yes, and it is the common outcome, because the easy fix is to make a rule quieter. "
             "A false negative is silent — nobody writes in to report that a tool failed to tell "
             "them something — so only a test asserting the opposite case catches it."),
            ("An audit says my site uses two brand names. Should I believe it?",
             "Check where the second one came from and how often it appears. A tagline or a "
             "section label appearing once across a whole site is a page, not an identity. What "
             "you declared in structured data or og:site_name is the part you actually claimed."),
            ("Should I rename my logo link so it matches my company name?",
             "No. That name exists so someone using a screen reader knows where the link goes. "
             "Put the company name in your declarations instead, where a tool should be reading "
             "it from anyway."),
        ],
    )


if __name__ == "__main__":
    print(fix_false_negative())
