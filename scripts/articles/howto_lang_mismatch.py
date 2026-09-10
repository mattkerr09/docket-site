#!/usr/bin/env python3
"""hreflang and html lang mismatch — three different faults with one name.

Target query: "hreflang and html lang mismatch" (11 impressions, Search Console
2026-08-10 to 2026-09-05). Distinct from /how-to/fix-hreflang-return-tags/,
which owns "hreflang tags with errors" (15) and is about the reciprocity rule.
One query per page.

⚠️ WHAT DOCKET ACTUALLY CHECKS, verified in the registry 2026-09-09:
  content.lang_mismatch  — <html lang> against the language the prose is in
  onpage.lang_missing    — no lang attribute at all
  intl.hreflang_bad_code / _unrecognised_lang / _deprecated_lang — the codes
  intl.hreflang_no_self / _no_return / _bad_target — the cluster
There is NO check comparing a page's hreflang self-reference to its own
<html lang>. The page says so rather than implying otherwise.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from render import render  # noqa: E402


def lang_attribute_mismatch() -> Path:
    body = """
<p class="lede">"hreflang and html lang mismatch" is three different faults sharing one
description, and they have three different fixes. Sorting out which one you have takes about a
minute and saves you changing the wrong attribute.</p>

<h2>The three mismatches</h2>

<p><strong>1. The declaration contradicts the prose.</strong> The page says
<code>lang="en"</code> and the text is Spanish. This is the one that does immediate damage: a
screen reader switches pronunciation on that attribute, and a search engine reads it to decide
who the page is for. A translation labelled as the original competes with the original for the
wrong readers instead of reaching its own.</p>

<p><strong>2. The hreflang code contradicts the page's own lang attribute.</strong> The page
declares <code>lang="en-GB"</code> while its own hreflang entry calls it <code>de-DE</code>. One
of the two is wrong, and nothing on the page tells you which — you have to read the prose to
find out, which is why this collapses into fault 1 once you look.</p>

<p><strong>3. The hreflang codes are not valid codes.</strong> <code>hreflang="en-UK"</code> is
a common one — the country is <code>GB</code>, not <code>UK</code> — as are region codes in the
language slot and vice versa. An invalid code is discarded, silently, and the cluster it was
part of is weakened.</p>

<h2>Which one you have, in one minute</h2>

<p>Open the page and read three things in this order.</p>

<p><strong>The prose.</strong> What language is the body text actually in? Not the navigation —
the body. This is the ground truth and everything else is a claim about it.</p>

<p><strong>The <code>&lt;html lang&gt;</code> attribute.</strong> Does it match what you just
read? If not, that is fault 1 and it is the one to fix first, because the other two are claims
about a page whose own declaration is wrong.</p>

<p><strong>The page's own hreflang entry.</strong> In a correct cluster every page lists every
version <em>including itself</em>. Find the line pointing at the URL you are on and check its
code against the lang attribute. Disagreement is fault 2.</p>

<pre><code>&lt;html lang="en-gb"&gt;
&lt;link rel="alternate" hreflang="en-gb" href="https://example.com/en-gb/shoes" /&gt;
&lt;link rel="alternate" hreflang="de-de" href="https://example.com/de-de/schuhe" /&gt;</code></pre>

<p>The self-reference and the lang attribute agree there. That is the whole test.</p>

<h2>Getting the codes right</h2>

<p>The language subtag comes from ISO 639-1 and the optional region from ISO 3166-1 alpha-2, in
that order, separated by a hyphen. The traps worth knowing:</p>

<ul>
<li><strong>The United Kingdom is <code>GB</code>.</strong> <code>en-UK</code> is not a valid
region and is discarded.</li>
<li><strong>Language alone is fine.</strong> <code>en</code> is valid and often better than
guessing at a region you do not actually target.</li>
<li><strong>Region alone is not.</strong> <code>hreflang="gb"</code> reads as a language subtag
and there is no language "gb".</li>
<li><strong>Some old codes were replaced.</strong> Hebrew moved from <code>iw</code> to
<code>he</code>, Indonesian from <code>in</code> to <code>id</code>, Yiddish from
<code>ji</code> to <code>yi</code>. The old ones still appear in templates.</li>
<li><strong><code>x-default</code> is not a language.</strong> It marks the fallback for
visitors none of your versions target, and it belongs in the cluster alongside the real
entries.</li>
</ul>

<h2>Why the wrong attribute gets changed</h2>

<p>Because the hreflang block is the visible, fiddly part, so it gets the attention — while the
single <code>lang</code> attribute sits in the template, was set once years ago, and is copied
onto every page including the translated ones. When a translation is added by duplicating an
existing page, the lang attribute comes along for the ride. Every new language multiplies the
error rather than revealing it.</p>

<p>The reciprocity rule is a separate fault again, and the most common hreflang defect there is:
if page A declares B, then B must declare A, or the whole declaration is ignored. That one has
its own page — <a href="/how-to/fix-hreflang-return-tags/">fixing hreflang tags with errors</a>
— because it cannot be seen by looking at either page alone.</p>

<h2>What Docket checks here, and what it does not</h2>

<p>Docket reads the declared language against the language the prose is actually in, and reports
the pages where they disagree — fault 1, per page rather than per site, because one translated
article among hundreds is the usual shape and it is the page that is wrong rather than the site.
It also reports pages with no lang attribute at all, invalid and unrecognised hreflang codes,
deprecated language subtags, missing self-references, missing return tags, and hreflang targets
that 404, redirect or carry a noindex.</p>

<p><strong>It does not compare a page's hreflang self-reference against its own
<code>lang</code> attribute</strong> — fault 2 above. That check does not exist today, and this
page is not going to imply it does. Read the two by hand on a sample of pages, or catch it
through fault 1, which the prose test does find.</p>

<p>The full list is <a href="/learn/what-docket-checks/">what Docket checks</a>, and the wider
procedure is <a href="/learn/seo-audit/">the technical SEO audit</a>. If your pages are built
by a framework and the attributes are injected after load, check
<a href="/how-to/javascript-seo-audit/">what the server actually sends</a> first — an attribute
that only exists after JavaScript runs is not there for the crawlers that do not run it.</p>

<h2>After you change it</h2>

<p>Language declarations are template-level, so a fix is usually one edit affecting many pages —
which is exactly the shape that wants checking afterwards rather than assuming.
<a href="/learn/site-monitoring/">Monitoring</a> tells you what changed rather than what is true
today, and a crawl of the affected section confirms the new attribute is on every page you
expected and none you did not.</p>

<p><a class="btn" href="/download/">Download Docket</a></p>
"""
    return render(
        cat="how-to", slug="fix-lang-attribute-mismatch",
        title="hreflang and html lang mismatch: which one you have",
        desc=("Three different faults share that description and have three different fixes. "
              "How to tell them apart in a minute, and which one to fix first."),
        h1="hreflang and html lang mismatch",
        crumb='<a href="/">Docket</a> / <a href="/how-to/">Fix it</a> / Language mismatch',
        body=body,
        published="2026-09-09",
        faq=[
            ("What is an hreflang and html lang mismatch?",
             "Usually one of three things: the lang attribute contradicts the language the page "
             "is written in; the page's own hreflang entry uses a different code from its lang "
             "attribute; or the hreflang codes are not valid codes. They have different fixes, "
             "so it is worth knowing which one you are looking at."),
            ("Which should I fix first, lang or hreflang?",
             "The lang attribute, if it contradicts the prose. Everything else is a claim about "
             "a page whose own declaration of itself is wrong, and a screen reader is already "
             "mispronouncing the page for real readers today."),
            ("Is en-UK valid?",
             "No. The region subtag comes from ISO 3166-1 alpha-2, where the United Kingdom is "
             "GB, so en-GB is the valid form. An invalid code is discarded silently, which is "
             "why this survives so long in templates."),
            ("Do the lang attribute and hreflang have to match exactly?",
             "They have to agree about the language. A page declaring lang=\"en-gb\" whose own "
             "hreflang self-reference says de-de is telling two different stories about itself, "
             "and one of them is wrong. Reading the body text is what settles which."),
            ("Does Docket detect a mismatch between hreflang and the lang attribute?",
             "Not that specific comparison. Docket checks the declared language against the "
             "language the prose is actually in, reports missing lang attributes, and validates "
             "hreflang codes, self-references, return tags and targets — but it does not compare "
             "a page's hreflang self-reference to its own lang attribute."),
        ],
    )


BUILDERS = [lang_attribute_mismatch]


def build_all() -> list[Path]:
    return [b() for b in BUILDERS]


if __name__ == "__main__":
    for p in build_all():
        print(p)
