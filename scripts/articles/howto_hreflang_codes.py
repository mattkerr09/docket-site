#!/usr/bin/env python3
"""hreflang values that are not valid language codes — `intl.hreflang_codes`.

Target query: "hreflang wrong language code". Deliberately NOT the same page as
/how-to/fix-hreflang-return-tags/, which owns reciprocity (a set that is
complete and correctly spelled and still ignored), or
/how-to/fix-lang-attribute-mismatch/, which owns "which of three faults do I
have". This one owns the value inside the attribute: the shape it must take,
the three findings Docket emits about it, and — the part no other page says —
the four things it does not validate.

Sourced from `intl.hreflang_codes` in
`backend/seo_engine/checks/international.py` at the tree shipped as v1.3.69
(the last change to that file, `4f6467e`, is an ancestor of the release
commit), from `extract.py` where `page.hreflang` is populated, and from the
three tests that record what went wrong:

  * test_hreflang_case_is_not_an_error.py
  * test_a_deprecated_code_is_not_an_unknown_one.py
  * test_a_real_language_is_not_unrecognised.py

⚠️ §9 — THE FINDING'S OWN SENTENCE IS WIDER THAN ITS CODE. The detail text of
`intl.hreflang_bad_code` says "the country must be a real ISO 3166-1 code",
which reads as region validation. `_REGION_TYPOS` has exactly three entries —
`uk`, `eu`, `en` — so `en-XX` and `en-QQ` pass, verified by running the check.
What is actually validated is the *shape*, plus those three strings. The page
leads with that rather than repeating the wider sentence.

Second narrowing, same class: the check keeps a `seen` set across the whole
crawl, so each distinct code string is judged once. The count is distinct
codes, not tags and not pages.

Third: `page.hreflang` is built only from `link rel="alternate"` elements in
crawled HTML. Google documents two other carriers — the HTTP `Link:` header and
XML sitemaps — and neither reaches this check.

Every figure and date is a constant below and interpolated: the registry counts
were recomputed from the registry file itself on the read date, not recalled.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from render import RELEASE, render  # noqa: E402

#: The three external sources, read at their canonical homes on READ_ON.
#: Section pointers are constants rather than sentences so a re-reading is one
#: edit and the prose cannot drift away from it.
RFC_URL = "https://www.rfc-editor.org/rfc/rfc5646.html"
RFC = "RFC 5646"
BCP = "BCP 47"
S_CASE = "section 2.1.1"
S_LANG = "section 2.2.1"
S_REGION = "section 2.2.4"
IANA_URL = "https://www.iana.org/assignments/language-subtag-registry"
IANA = "IANA language subtag registry"
GOOGLE_URL = ("https://developers.google.com/search/docs/"
              "specialty/international/localized-versions")
GOOGLE = "Google's localized-versions documentation"
READ_ON = "16 September 2026"

#: Standards named in the body. They carry digits, so they live here.
ISO_LANG = "ISO 639-1"
ISO_REGION = "ISO 3166-1 alpha-2"
ISO_SCRIPT = "ISO 15924"
M49 = "UN M.49"

#: Recomputed from the registry file on READ_ON by parsing every `Type:
#: language` record: 190 two-letter subtags, of which 6 carry `Deprecated:`.
#: The `File-Date` header of the copy read is REGISTRY_DATE.
REGISTRY_DATE = "2026-08-08"
N_CURRENT_TWO_LETTER = 184
N_DEPRECATED = 6
#: Docket's own table, reconciled against that set: the 184 current subtags plus
#: `bh`, kept because a site publishing it has an out-of-date tag rather than an
#: unrecognisable one.
N_TABLE = 185
#: `_REGION_TYPOS` — the whole of Docket's region knowledge.
N_REGION_STRINGS = 3


def hreflang_codes() -> Path:
    body = f"""
<p class="lede">An audit came back saying an hreflang value is not a valid language code, or you
are looking at a tag you suspect is wrong and want to know before you edit a template that ships
on every page. The question splits in two, and the useful half is the second: what makes a value
invalid, and how much of that can a crawler actually tell you.</p>

<h2>The shape a value has to take</h2>

<p>An hreflang value is a language subtag, then optionally a script, then optionally a region,
joined by hyphens. Docket's <code>intl.hreflang_codes</code> check matches exactly that and
nothing else:</p>

<pre><code>language   2 or 3 letters      en  de  ceb
script     4 letters, optional  Hant  Cyrl
region     2 letters, or 3 digits, optional   GB  419</code></pre>

<p>Per <a href="{RFC_URL}#section-2.2.1">{RFC} {S_LANG}</a> — the document {BCP} points at —
two-character language subtags "were defined in the IANA registry according to the assignments
found in the standard" {ISO_LANG}, and three-character ones come from the other parts of that
standard. Per <a href="{RFC_URL}#section-2.2.4">{S_REGION}</a>, two-letter regions come from
{ISO_REGION} and "three-character region subtags consist solely of digit (number) characters"
from the {M49} statistical codes. Scripts are {ISO_SCRIPT}. All read at rfc-editor.org
on {READ_ON}.</p>

<p>The value <code>x-default</code> is skipped before any of this runs, which it has to be: it
is a reserved token, not a language, and the pattern above would reject it.</p>

<p>Things that fail the shape test and are reported: <code>en_US</code> with an underscore,
which is how locales are written in a lot of codebases and never how an hreflang value is
written; <code>en-GBR</code>, the three-letter country code; anything with a stray space or a
trailing comma from a templating loop.</p>

<h2>Three findings, not one</h2>

<p>Values that clear the shape test are sorted into three separate findings, and the severity
tells you which pile you are in.</p>

<p><strong><code>intl.hreflang_bad_code</code>, at MEDIUM.</strong> The shape is wrong, or the
region is one of {N_REGION_STRINGS} strings Docket holds as known-wrong. Effort is marked
trivial, because it is a find-and-replace in one template.</p>

<p><strong><code>intl.hreflang_deprecated_lang</code>, at LOW.</strong> A well-formed value
naming a real language by a subtag the registry has retired.</p>

<p><strong><code>intl.hreflang_unrecognised_lang</code>, at NOTICE.</strong> A well-formed
value whose language Docket's table does not contain. It carries the tool-limit flag, scores
nothing, and stays off the fix list — it is a statement about Docket, not about your markup.</p>

<h2>What this check does not validate</h2>

<p>Put first, because it is the difference between a clean result and a correct one.</p>

<p><strong>The region is not checked against the country list.</strong> The finding's own text
says the country "must be a real {ISO_REGION} code", and that is wider than the code behind it.
Docket holds {N_REGION_STRINGS} region strings: <code>uk</code>, which it rewrites to
<code>GB</code>; <code>eu</code>, which is not a country; and <code>en</code>, which is a
language sitting in the region slot. Everything else that is two letters passes. Running the
check over <code>en-XX</code> and <code>en-QQ</code> — both user-assigned in the country
standard, neither a country — produces no finding at all. Note too that the language-in-the-
region-slot case is caught only when that language is English: <code>de-en</code> is reported,
<code>de-fr</code> is not.</p>

<p><strong>Capitalisation is not an error, and Docket will not pretend it is.</strong> {RFC}
{S_CASE} is unambiguous: "At all times, language tags and their subtags, including private use
and extensions, are to be treated as case insensitive". The standard recommends uppercase
regions as a convention, and a convention is not a defect. This is in the code because Docket
got it wrong in public — an earlier table mapped <code>us</code> to <code>US</code> and
<code>za</code> to <code>ZA</code>, and because the region is lowercased before the lookup, two
professionally run sites were told <code>en-US</code> was broken and handed
<code>en-US</code> as the correction. One of them serves every one of its tags lowercase and
they work.</p>

<p><strong>Only tags in crawled HTML are seen.</strong> The values come from
<code>link rel="alternate"</code> elements in the pages the crawl fetched. {GOOGLE} describes
two other ways to declare the same thing — an HTTP <code>Link:</code> header, which it
recommends for non-HTML files, and annotations in an XML sitemap. Neither reaches this check,
so a site that declares hreflang in its sitemap gets silence here rather than a clean bill.</p>

<p><strong>The count is distinct codes.</strong> Each value string is judged once for the whole
crawl. A template repeating one wrong code on every page produces one entry, not one per page,
and the URL shown beside it is the first page the crawler happened to see it on rather than the
only one to fix.</p>

<h2>The one region typo worth its own paragraph</h2>

<p><code>en-uk</code> is the common one, and it is genuinely wrong rather than
stylistically wrong. In the {IANA} — the list {BCP} defers to, read on {READ_ON} at the URL
below, <code>File-Date</code> {REGISTRY_DATE} — the record reading
<code>Description: United Kingdom</code> has the subtag <code>GB</code>. There is no
<code>UK</code> record of any type. {GOOGLE} states the consequence directly: "Only language
codes listed in {ISO_LANG} and region codes listed in ISO 3166-1 Alpha 2 are supported; other
codes that aren't listed in those standards, such as es-419, aren't supported."</p>

<p>Which raises the divergence you should know about before you trust a pass. Docket accepts
<code>es-419</code>, because {BCP} explicitly permits {M49} numerics in the region slot, and
that sentence of Google's says Google does not. Both are accurately reported here: the value is
well-formed under the standard and unsupported by one search engine. Docket checks the standard,
so a value like that leaves the audit silently, and silence is not a promise that Google honours
it.</p>

<h2>Retired subtags: a tidy-up, not a fault</h2>

<p>{N_DEPRECATED} two-letter language subtags in the registry carry both a deprecation and a
replacement, and every one of them still turns up in production. The registry's own pairings,
read on {READ_ON}:</p>

<pre><code>in -&gt; id   Indonesian      iw -&gt; he   Hebrew
ji -&gt; yi   Yiddish         jw -&gt; jv   Javanese
mo -&gt; ro   Moldavian       bh -&gt; bih  Bihari languages</code></pre>

<p>This finding exists because of a specific piece of dishonesty. A global retailer publishing
<code>in-ID</code> across its hreflang block was told Docket did not recognise the language —
true of Docket's table, and useless, because <code>in</code> is not an unknown language. It is
the superseded subtag for Indonesian and the registry names its replacement. A notice saying
"our fault, nothing to do" was sitting on something with a documented answer.</p>

<p>What the finding deliberately does not say is that search engines ignore the old form.
Nobody outside those companies can measure that, so the claim is absent and the severity is LOW.
The recommendation is the registry's: use the current subtag, and change the matching entries on
the pages at the other end in the same edit, or the pair stops lining up. That pairing rule is
the subject of <a href="/how-to/fix-hreflang-return-tags/">how to fix hreflang return
tags</a>, and it is the more expensive failure of the two.</p>

<h2>When Docket says it does not recognise a language</h2>

<p>Docket's language table holds {N_TABLE} two-letter subtags: the {N_CURRENT_TWO_LETTER}
current in the registry as of <code>File-Date</code> {REGISTRY_DATE}, plus <code>bh</code>,
which is deprecated rather than unknown. A value whose language is not in that table is
well-formed, may be entirely correct, and gets a notice that scores zero.</p>

<p>Two real cases explain why it is a notice. Cebuano is <code>ceb</code> — it has no two-letter
form at all, so no two-letter table can ever contain it, and {RFC} {S_LANG} permits the
three-letter subtag. Aragonese is <code>an</code>, an ordinary current subtag that was simply
missing from an earlier, shorter version of the table; a real multilingual site was told its
language was unrecognised, and the fix was to widen the table rather than to soften the wording.
Docket cannot tell your typo from our short list, so it says which of the two it is claiming.</p>

<p>The honest use of that notice: read the codes it lists, and check any you do not recognise
yourself against the <a href="{IANA_URL}">{IANA}</a>. That file is plain text and searchable in
a browser.</p>

<h2>Checking a value without running anything</h2>

<p>Pull the tags off a page and read the values in one column:</p>

<pre><code>curl -s https://example.com/ | grep -o 'hreflang="[^"]*"' | sort -u</code></pre>

<p>Then, for each value you are unsure of, search the registry file for the language subtag and
for the region separately. A subtag record that carries a <code>Deprecated</code> line names its
replacement on the next line. A region you cannot find at all is the <code>en-uk</code> case:
the tag is discarded and the page it pointed at is not connected to anything.</p>

<p>If the codes all check out and the set still is not working, the fault is one page over —
either the cluster is not reciprocal, or the declared language of the page contradicts its own
prose. <a href="/how-to/fix-lang-attribute-mismatch/">hreflang and html lang mismatch</a>
separates those. <a href="/learn/what-docket-checks/">What Docket checks</a> lists the rest of
the indexing lane these findings sit in.</p>

<p>Everything on this page describes the build shipped as {RELEASE}, read in the engine source
rather than from the manual.</p>

<p><a class="btn" href="/download/">Download Docket</a></p>
"""
    return render(
        cat="how-to", slug="fix-invalid-hreflang-codes",
        title="Invalid hreflang codes: the rule, and what is not checked",
        desc=("What makes an hreflang value invalid, the three findings a Docket audit of your "
              "site emits for it, and the four things it does not validate."),
        h1="hreflang values that are not valid language codes",
        crumb='<a href="/">Docket</a> / <a href="/how-to/">Fix it</a> / Invalid hreflang codes',
        body=body,
        published="2026-09-16",
        faq=[
            ("Is en-UK a valid hreflang value?",
             "No. The region subtag comes from the country standard, where the United Kingdom "
             "is GB, and there is no UK record of any type in the IANA language subtag "
             "registry. Google's own documentation says region codes outside that standard are "
             "not supported, so en-uk connects the page to nothing."),
            ("Does hreflang have to be uppercase for the country?",
             "No. The standard states that language tags and their subtags are to be treated as "
             "case insensitive at all times. Uppercase regions are a recommended convention, "
             "not a requirement, and af-za and af-ZA are the same tag. Docket reports neither."),
            ("Why does Docket say it does not recognise a language code I know is real?",
             "Because its language table is two-letter only, and some languages have no "
             "two-letter form — Cebuano is the usual example. That finding is a notice carrying "
             "a tool-limit flag: it scores nothing and stays off the fix list, because it is a "
             "statement about the tool rather than about your markup."),
            ("Is a deprecated language subtag like in-ID broken?",
             "It is out of date rather than broken. The registry marks it deprecated and names "
             "the current subtag, id for Indonesian. Whether a given search engine still honours "
             "the old form cannot be measured from outside, so Docket reports it at LOW as a "
             "tidy-up and makes no claim about what any engine does with it."),
            ("Will Docket catch every invalid country code in my hreflang tags?",
             "No, and this is the limit worth knowing. It validates the shape of the value and "
             "holds three region strings it knows are wrong; a two-letter region outside that "
             "short list passes even when no such country exists. Check unfamiliar regions "
             "against the country standard yourself."),
            ("Does Docket read hreflang from my XML sitemap?",
             "Not in this check. The values it judges come from link rel=alternate elements in "
             "the HTML it crawled. Google also supports hreflang in an HTTP Link header and in "
             "XML sitemap annotations, and a site declaring them that way gets no finding here "
             "rather than a clean result."),
        ],
    )


BUILDERS = [hreflang_codes]


def build_all() -> list:
    return [b() for b in BUILDERS]


if __name__ == "__main__":
    for p in build_all():
        print(p)
