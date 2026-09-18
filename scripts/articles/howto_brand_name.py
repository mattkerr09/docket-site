"""How an audit decides what your company is called — and four ways it missed.

Promised on the how-to hub. Sourced from the registered checks
`brand.name_consistency` and `brand.logo` in `backend/seo_engine/checks/brand.py`,
whose docstrings record four measured cases, each of which produced a confident
false finding from an entirely ordinary site:

  * a header logo link whose accessible name described the destination, taken
    as a brand name — with advice that would have replaced a correct link
    description with a bare word;
  * a three-part title whose brand sat in the middle, so the two ends were read
    as the company's name and a region;
  * titles counted by distinct spelling rather than by occurrence, so a
    perfectly consistent suffix lost to a handful of page names;
  * an institution whose logo carries its initials and whose og:site_name
    carries the expansion, reported as two different brands.

⚠️ NO SITE IS NAMED — third-party gate. None of the four lessons needs a name,
and the fourth is better without one because the shape is universal.

⚠️ THIS PAGE MUST NOT CONTRADICT /learn/brand-consistency/, which tells readers
to make sure their logo alt text names the company. That advice stands. What
the first case shows is a DIFFERENT attribute: a link's accessible name, which
describes where the link goes. A logo that is a link carries both, and they are
not interchangeable. The page says so explicitly.

Numerals: none. Quantities spelled as words.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from render import render  # noqa: E402


def brand_name() -> Path:
    body = """
<p class="lede">Before a tool can tell you that your company's name appears inconsistently, it
has to decide what your company is called. Nobody tells it. It reads your titles, your
<code>og:site_name</code>, your <code>Organization</code> schema and your logo, and infers. Four
times that inference produced a confident, specific, wrong sentence — and every site it fired on
was doing something entirely ordinary.</p>

<h2>The advice that would have hurt a screen-reader user</h2>

<p>A national health service's header logo is a link, and that link has an accessible name
ending in the word "homepage" — so that somebody navigating by voice or by screen reader hears
where the link goes rather than just a word. That is exactly what a link's accessible name is
for.</p>

<p>The check read that string as a brand name, decided the organisation called itself several
different things, and advised putting the chosen name verbatim in the logo's alt text. Following
that instruction would have swapped a correct description of a destination for a bare brand word
and told a screen-reader user nothing about where the link leads. <strong>The finding was false
and the remedy would have made the site worse for the people it is hardest to serve.</strong></p>

<p>The distinction underneath is worth keeping, because it is one that trips up people as well
as tools:</p>

<ul>
<li><strong>Alt text describes the image.</strong> On a logo, the image is your company's name
written in a typeface, so the alt text should be your company's name.</li>
<li><strong>A link's accessible name describes the destination.</strong> On a logo that links
home, that is something like "<em>Company</em> homepage".</li>
</ul>

<p>A logo that is a link has both, they have different jobs, and neither is a substitute for the
other. Any advice that tells you to make them identical has confused the two.</p>

<p>The repair was to strip the navigational words and keep whatever brand is left — and to drop
the source entirely when nothing is left, rather than record the remainder as a name. That
second half matters: "Return to homepage" contains no brand at all, and stripping only the tail
would have filed "Return to" as a company name.</p>

<h2>The brand in the middle of the title</h2>

<p>Plenty of sites use three-part titles: page name, company, region. A reader that splits a
title on its separator and looks at the two ends never considers the middle — so on one
restaurant's pages the candidates were the page name and the US state, and the report told the
owner their brand appeared two different ways, quoting the restaurant and the state.</p>

<p>The repair is narrow on purpose. When a title has more than two fragments, the fragment that
resembles your domain is the brand, wherever it sits — and only when exactly one fragment
matches. Guessing which middle fragment is a company name would be worse than the two-ended
reading it replaces, so when nothing resembles the domain the titles contribute nothing at
all.</p>

<p><strong>A check that refuses to speak beats one that flips a coin about a company's
name.</strong></p>

<h2>Counting spellings instead of pages</h2>

<p>A university's sampled titles were all "<em>Page name</em> | <em>Brand</em>" — a perfectly
consistent suffix, which is the thing the check exists to reward. But several of the page names
themselves contained the brand: a history page, a research page, a giving page.</p>

<p>The code compared distinct spellings rather than occurrences. On the suffix side every page
had the same one, so the whole site contributed a single tally mark. On the page-name side each
distinct phrase contributed its own. The page names won, the check concluded that was where the
brand lived, and it offered "Contact", "Disclaimer", "Athletics" and "Cookie Settings" to the
owner as their company's name.</p>

<p>Counted by occurrence the same data says the opposite, immediately and unambiguously. This is
the same defect that shows up in finding badges — <a href="/how-to/check-the-count-on-a-finding/">a
count is a claim about units before it is a claim about size &rarr;</a>.</p>

<h2>An initialism is not a second name</h2>

<p>A national academy carries its initials in its logo and its full name in
<code>og:site_name</code>. The check reported two different brand names and warned that a
knowledge panel, a shared link preview and an assistant's citation could each show a different
one.</p>

<p>They are the same name. An institution using its own initialism in its logo is one of the
most ordinary things in this check's input, and the substring test beside it cannot see the
relationship, because an initialism shares no substring with its expansion.</p>

<p>The repair stays mechanical rather than becoming a guess: the letters of the short form must
<em>be</em> the initials, in order, of the words in the long form, with a small skip-list for
articles and prepositions in several languages so that a name containing "of" or "de" still
matches. Two names cannot pass that test by luck.</p>

<h2>What to check on your own site</h2>

<p>The finding is worth having — a company that calls itself three things across its own markup
really does fragment its entity signals. Check the four places by hand, in this order:</p>

<ul>
<li><strong><code>og:site_name</code></strong>, which is what a shared link preview shows.</li>
<li><strong>Your <code>Organization</code> schema's name</strong>, which is what structured-data
consumers read.</li>
<li><strong>The stable fragment of your title tags</strong> — the part that does not change from
page to page.</li>
<li><strong>Your logo's alt text</strong>, which should be your company name — and, separately,
the logo link's accessible name, which should describe where it goes.</li>
</ul>

<h2>When this does not matter</h2>

<p>It sits at medium severity, and deservedly, but three cases are not worth your time:</p>

<ul>
<li><strong>An initialism and its expansion.</strong> Same name. If a tool flags it, the tool is
wrong.</li>
<li><strong>A legal entity name in one place and a trading name in another</strong> — "Company
Limited" in the schema and "Company" everywhere else is normal and usually required.</li>
<li><strong>A region or division in a title suffix.</strong> Extra context in a title is a
choice about your titles, not an inconsistency in your name.</li>
</ul>

<h2>The fixes that make it worse</h2>

<ul>
<li><strong>Overwriting a logo link's accessible name with the bare brand.</strong> This is the
first case. It clears nothing real and costs somebody their bearings.</li>
<li><strong>Adding your company name to every page name</strong> so the titles look consistent.
It shortens the part of the title that tells a searcher what the page is, and if your titles
already carry a stable suffix it was never needed.</li>
<li><strong>Renaming the company in your schema to match a typo elsewhere.</strong> Make the
outliers match the right name, not the other way round.</li>
</ul>

<h2>How to satisfy this without being consistent</h2>

<p>Put the same string in all four places and stop thinking about it. That is genuinely the
right fix here — but notice that it also means the check can only ever see agreement between
four fields you control, not whether the world knows you by that name. It cannot read a
directory listing, a knowledge panel or anybody else's citation of you. <strong>It measures
whether your own markup agrees with itself, which is a precondition for consistency and not the
same thing as consistency.</strong></p>

<h2>Where this sits in an audit</h2>

<p>The registered checks are <code>brand.name_consistency</code>, which compares what your
markup calls you, and <code>brand.logo</code>, which covers logo presence and markup. Both are
in the brand area — see
<a href="/learn/brand-consistency/">the question no crawler asks &rarr;</a> for what that lane
measures and where dedicated tools beat an SEO crawler at it.</p>
"""
    return render(
        cat="how-to", slug="what-your-site-says-you-are-called",
        title="What your site says your company is called",
        desc=("How an audit infers your company name, and four cases where it was wrong — "
              "including advice that would have hurt a site's accessibility."),
        h1="What your site says your company is called",
        crumb='<a href="/">Docket</a> / <a href="/how-to/">Fix it</a> / Brand name',
        body=body,
        faq=[
            ("Where does an audit get my company name from?",
             "It infers it from your markup — the stable fragment of your title tags, your "
             "og:site_name, your Organization schema and your logo. Nothing tells it directly, "
             "so every brand-name finding rests on a guess that can be wrong."),
            ("Should my logo's alt text and its link name be the same?",
             "No. Alt text describes the image, so on a logo it should be your company name. A "
             "link's accessible name describes the destination, so on a logo that links home it "
             "should say so. They have different jobs."),
            ("My audit says my brand appears two ways, but one is just our initials.",
             "Then the tool is wrong. An initialism and its expansion are the same name, and a "
             "check that cannot recognise that is comparing strings rather than names."),
            ("Does a region in my title suffix count as an inconsistent name?",
             "It should not. Extra context after your company name is a decision about your "
             "titles. A tool that only reads the two ends of a title can mistake the region for "
             "the brand when the brand sits in the middle."),
            ("Is brand name consistency worth fixing?",
             "Usually yes and it is quick: put the same string in your og:site_name, your "
             "Organization schema, your title suffix and your logo alt text. It is a "
             "precondition for consistency rather than proof of it."),
        ],
    )


if __name__ == "__main__":
    print(brand_name())
