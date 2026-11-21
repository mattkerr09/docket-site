#!/usr/bin/env python3
"""How to fix hreflang return tags.

Promised on the how-to hub for several releases and written now. Every claim is
sourced from Docket's own `intl.hreflang_no_return` check (the rule it applies,
the reason it is HIGH, and the sentence it prints) rather than from a summary
of somebody else's guide.

No numeric literals in the prose beyond HTTP status codes, which are declared
in verify_numbers.ALLOWED as constants of the protocol.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from render import render  # noqa: E402


def hreflang_return_tags() -> Path:
    # 21 November 2026: answer first, repair table and measured local crawl findings.
    body = """
<p class="lede">If page A lists page B as a language alternate, B must list A back with the
exact same URL. Every page must list itself too. Fix hreflang return tags by generating one
identical block for the whole set and putting it on every language version.</p>

<h2>The rule, in one sentence</h2>

<p>If page A declares page B as an alternate, B must declare A in return. A declaration that
goes one way is discarded. Not downgraded, not partially honoured: <strong>ignored</strong>,
and the wrong language version keeps being served to the wrong country.</p>

<p>This is why it is the hardest hreflang error to find by eye. Open the English page: the tag
block is there, the codes are valid, the URLs resolve. Open the German page: same. The defect
exists only in the relationship between them, and nothing on either page shows it.</p>

<h2>What a complete set looks like</h2>

<p>Every page in the group lists every page in the group, <em>including itself</em>. That
self-reference is the part people leave out, and leaving it out breaks the set:</p>

<pre><code>&lt;link rel="alternate" hreflang="en-gb" href="https://example.com/en-gb/shoes" /&gt;
&lt;link rel="alternate" hreflang="de-de" href="https://example.com/de-de/schuhe" /&gt;
&lt;link rel="alternate" hreflang="x-default" href="https://example.com/shoes" /&gt;</code></pre>

<p>That identical block goes on all three URLs. Not a tailored block per page: the same one.
Generating it once and including it everywhere is the only approach that survives contact with
a growing site, because the failure mode of hand-maintenance is silent.</p>

<h2>The four ways a set breaks</h2>

<div class="wrap-tbl"><table>
<thead><tr><th>How the set breaks</th><th>What it looks like</th><th>How to fix it</th></tr></thead>
<tbody>
<tr><td>A page omits itself.</td><td>The set is incomplete and the whole group is suspect.
It is the cheapest error to make and fix.</td><td>Add the page's own URL to the shared block.</td></tr>
<tr><td>One side was updated and the other was not.</td><td>A new language launches and links
to the old pages, but they do not link back. The new language is invisible.</td><td>Put the
updated shared block on the old pages as well as the new ones.</td></tr>
<tr><td>The URLs disagree.</td><td>One side uses <code>https://</code> and a trailing slash,
the other does not. A crawler sees different URLs and no return link, even if a person misses
the difference.</td><td>Use the exact same URL for each page throughout the block.</td></tr>
<tr><td>The target is not indexable.</td><td>The return tag points at a page that is
<code>noindex</code>, canonicalised elsewhere or returning a not-found response. The pair is
broken from the other end.</td><td>Make the target indexable with a self-canonical and a live
response, then check the return links again.</td></tr>
</tbody>
</table></div>

<h2>hreflang and canonical must agree</h2>

<p>This is the conflict that undoes otherwise-correct setups. Each language version should
canonicalise <em>to itself</em>. If the German page carries a canonical pointing at the English
one, you have told search engines two contradictory things: "these are equivalent alternates"
and "the German one is a duplicate that should not be indexed". The canonical wins, the German
page drops out, and the hreflang set silently loses a member.</p>

<p>Self-canonical on every language version. Always. The other ways that tag goes wrong (
two on one page, one pointing at a <code>noindex</code> page) are in
<a href="/how-to/fix-conflicting-canonicals/">how to fix conflicting canonicals</a>.</p>

<h2>Which code to use</h2>

<p>Language alone (<code>de</code>) targets speakers of that language anywhere. Language plus
region (<code>de-at</code>) targets speakers in one country. Use the pair only when the pages
genuinely differ by country: different prices, currency, shipping, legal text. Two pages that
differ by nothing but a flag icon do not need separate regional targeting, and splitting them
divides whatever authority they have earned.</p>

<p><code>x-default</code> names the page for everyone the set does not cover. A language
selector or a global landing page is the right target; your busiest market's homepage is not,
because it will be served to people it was not written for.</p>

<h2>How to check it, and why the check has to crawl</h2>

<p>Any tool that validates hreflang by reading one page can only tell you the codes parse. To
know whether a set is reciprocated, something has to fetch every page in the set and compare
the declarations against each other. Docket does that during the crawl and reports the specific
pair that fails (which page points where, and which page does not point back) because
"hreflang errors: 4" is not something anybody can act on.</p>

<p>It reports this at HIGH severity for a reason: a broken set is not a missed optimisation.
It is a feature that is fully implemented, looks correct on inspection, and does nothing.</p>

<h2>What a real crawl caught</h2>

<p>For this update, we built a small local test
site with eight pages: one index and seven language versions of one page. English, German and
French formed the correct control set. Each listed itself, the others and an
<code>x-default</code>, and each canonicalised to itself. English also listed Spanish,
Portuguese, Italian and Dutch, each broken in a different way. The crawl took a few seconds.</p>

<div class="wrap-tbl"><table>
<thead><tr><th>Page</th><th>What was wrong</th><th>What Docket reported</th></tr></thead>
<tbody>
<tr><td>English, German and French</td><td>Nothing in the control set.</td><td>No hreflang
finding on the correct set.</td></tr>
<tr><td>Spanish</td><td>No hreflang at all, so the link from English went one way.</td><td>
"hreflang links are not reciprocated" at high severity for English to Spanish.</td></tr>
<tr><td>Portuguese</td><td>Returned the link to the English URL with a query string added.</td><td>
"hreflang links are not reciprocated" at high severity for English to Portuguese. A return to
a URL variant counted as missing, just like no return at all.</td></tr>
<tr><td>Italian</td><td>Returned the link correctly, but its canonical pointed at English.</td><td>
A canonical finding at low severity for canonicalising to a different URL. It was not reported
as a broken hreflang pair.</td></tr>
<tr><td>Dutch</td><td>Returned the link correctly, but did not list itself.</td><td>Hreflang
tags with no self-reference, at medium severity.</td></tr>
</tbody>
</table></div>

<p>The Italian case shows up as a canonical finding, so read canonical findings and hreflang
findings together.</p>

<p><a class="btn" href="/download/">Download Docket</a></p>
"""
    return render(
        cat="how-to", slug="fix-hreflang-return-tags",
        title="Hreflang return tags: how to fix no return tag errors",
        desc=("Each alternate must link back to the exact same URL and list itself. "
              "Fix hreflang return tags with a shared block, plus see what a real crawl caught."),
        h1="How to fix hreflang return tags",
        crumb='<a href="/">Docket</a> / <a href="/how-to/">Fix it</a> / hreflang return tags',
        body=body,
        modified="2026-11-21",
        faq=[
            ("What is an hreflang return tag?",
             "If page A lists page B as a language alternate, B must list A in return. That "
             "reciprocal declaration is the return tag. Without it the declaration is "
             "one-way and search engines ignore it."),
            ("Does every page need to list itself in hreflang?",
             "Yes. Each page in the set must include a self-referencing hreflang entry "
             "alongside the entries for the other versions. Omitting it is the most common "
             "way a set breaks."),
            ("Can hreflang and canonical tags conflict?",
             "They can, and it is the conflict that undoes most correct-looking setups. Each "
             "language version must canonicalise to itself. A canonical pointing at another "
             "language says that page is a duplicate, which removes it from the set."),
            ("Why can't I spot this by viewing the page source?",
             "Because nothing is wrong on the page you are looking at. Every tag can be "
             "present and valid in isolation; the error exists only in the relationship "
             "between two pages, so finding it requires fetching both and comparing them."),
            ("What does 'no return tags' mean?",
             "A page lists an alternate that does not list it back, or lists it back at a "
             "different URL. That could be a query string, http instead of https, or a "
             "missing trailing slash. The return must use the exact same URL."),
        ],
    )


if __name__ == "__main__":
    print(hreflang_return_tags())
