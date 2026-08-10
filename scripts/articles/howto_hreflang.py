#!/usr/bin/env python3
"""How to fix hreflang return tags.

Promised on the how-to hub for several releases and written now. Every claim is
sourced from Docket's own `intl.hreflang_no_return` check — the rule it applies,
the reason it is HIGH, and the sentence it prints — rather than from a summary
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
    body = """
<p class="lede">hreflang is the only common SEO tag that cannot be validated by looking at the
page it sits on. Every tag can be present, spelled correctly and pointing at a live URL, and
the whole set can still be ignored — because the rule is not about the tag, it is about the
pair.</p>

<h2>The rule, in one sentence</h2>

<p>If page A declares page B as an alternate, B must declare A in return. A declaration that
goes one way is discarded. Not downgraded, not partially honoured — <strong>ignored</strong>,
and the wrong language version keeps being served to the wrong country.</p>

<p>This is why it is the hardest hreflang error to find by eye. Open the English page: the tag
block is there, the codes are valid, the URLs resolve. Open the German page: same. The defect
exists only in the relationship between them, and nothing on either page shows it.</p>

<h2>What a complete set looks like</h2>

<p>Every page in the group lists every page in the group — <em>including itself</em>. That
self-reference is the part people leave out, and leaving it out breaks the set:</p>

<pre><code>&lt;link rel="alternate" hreflang="en-gb" href="https://example.com/en-gb/shoes" /&gt;
&lt;link rel="alternate" hreflang="de-de" href="https://example.com/de-de/schuhe" /&gt;
&lt;link rel="alternate" hreflang="x-default" href="https://example.com/shoes" /&gt;</code></pre>

<p>That identical block goes on all three URLs. Not a tailored block per page — the same one.
Generating it once and including it everywhere is the only approach that survives contact with
a growing site, because the failure mode of hand-maintenance is silent.</p>

<h2>The four ways a set breaks</h2>

<ul>
<li><strong>A page omits itself.</strong> The set is incomplete and the whole group is
suspect. Cheapest error to make and cheapest to fix.</li>
<li><strong>One side was updated and the other was not.</strong> A new language launches, the
new pages point at the old ones, nobody edits the old ones. The new language is invisible.</li>
<li><strong>The URLs disagree.</strong> One side uses <code>https://</code> and a trailing
slash, the other does not. These are different URLs, so the return link does not exist as far
as a crawler is concerned — a difference no human reading the two pages would notice.</li>
<li><strong>The target is not indexable.</strong> A return tag pointing at a page that is
<code>noindex</code>, canonicalised elsewhere or returning a 404 is not a return tag. The pair
is broken from the other end.</li>
</ul>

<h2>hreflang and canonical must agree</h2>

<p>This is the conflict that undoes otherwise-correct setups. Each language version should
canonicalise <em>to itself</em>. If the German page carries a canonical pointing at the English
one, you have told search engines two contradictory things: "these are equivalent alternates"
and "the German one is a duplicate that should not be indexed". The canonical wins, the German
page drops out, and the hreflang set silently loses a member.</p>

<p>Self-canonical on every language version. Always.</p>

<h2>Which code to use</h2>

<p>Language alone (<code>de</code>) targets speakers of that language anywhere. Language plus
region (<code>de-at</code>) targets speakers in one country. Use the pair only when the pages
genuinely differ by country — different prices, currency, shipping, legal text. Two pages that
differ by nothing but a flag icon do not need separate regional targeting, and splitting them
divides whatever authority they have earned.</p>

<p><code>x-default</code> names the page for everyone the set does not cover. A language
selector or a global landing page is the right target; your busiest market's homepage is not,
because it will be served to people it was not written for.</p>

<h2>How to check it, and why the check has to crawl</h2>

<p>Any tool that validates hreflang by reading one page can only tell you the codes parse. To
know whether a set is reciprocated, something has to fetch every page in the set and compare
the declarations against each other. Docket does that during the crawl and reports the specific
pair that fails — which page points where, and which page does not point back — because
"hreflang errors: 4" is not something anybody can act on.</p>

<p>It reports this at HIGH severity for a reason: a broken set is not a missed optimisation.
It is a feature that is fully implemented, looks correct on inspection, and does nothing.</p>

<p><a class="btn" href="/download/">Download Docket</a></p>
"""
    return render(
        cat="how-to", slug="fix-hreflang-return-tags",
        title="How to fix hreflang return tags (the error you cannot see)",
        desc=("hreflang only works when the link goes both ways. Why one-way declarations "
              "are ignored, the four ways a set breaks, and why canonical must agree."),
        h1="How to fix hreflang return tags",
        crumb='<a href="/">Docket</a> / <a href="/how-to/">Fix it</a> / hreflang return tags',
        body=body,
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
        ],
    )


if __name__ == "__main__":
    print(hreflang_return_tags())
