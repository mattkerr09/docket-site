#!/usr/bin/env python3
"""How to fix conflicting canonical tags.

Promised on the how-to hub and written now. Sourced from Docket's own five
canonical checks — `index.canonical_conflict`, `canonical_missing`,
`canonical_non_self`, `canonical_offsite` and `canonical_to_noindex` — which is
also the article's structure: those five are the five ways this goes wrong, and
they are separate checks because they have separate fixes.

No numeric literals beyond HTTP status codes, which ALLOWED declares as
constants of the protocol.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from render import render  # noqa: E402


def conflicting_canonicals() -> Path:
    body = """
<p class="lede">A canonical tag is a page telling search engines which URL is the real one.
It is a hint, not an instruction — which means the failure mode is not an error message, it is
being quietly ignored, or quietly obeyed when you did not mean it.</p>

<h2>Two canonicals on one page</h2>

<p>The worst version, because it looks fine. A page carries two
<code>rel=canonical</code> tags naming different URLs — usually because a theme injects one and
an SEO plugin injects another, and nobody has viewed the rendered head since both were
installed.</p>

<p>The page now contradicts itself about where it lives. Google's documented response to
conflicting canonicals is to ignore them all and pick a URL itself, which means you have
installed two tools to control indexing and ended up with less control than if you had
installed neither.</p>

<p><strong>Fix:</strong> exactly one <code>rel=canonical</code> per page. Find the second
source and turn it off rather than trying to make the two agree — two things writing the same
tag will disagree again the next time either is updated.</p>

<h2>The canonical points at a noindex page</h2>

<p>This one is self-defeating in a specific way. Page A canonicalises to page B; page B says
<code>noindex</code>. You have said "the real version of this content is over there" and "that
one must not be indexed". Both pages drop out, and the content disappears from search
entirely.</p>

<p>It usually happens when a page is retired: someone adds <code>noindex</code> to the old URL
and forgets that other pages still name it as canonical.</p>

<p><strong>Fix:</strong> decide which URL should be indexed and make it self-canonical without
<code>noindex</code>. Do not use canonical to remove pages from the index — that is what
<code>noindex</code> is for, and using canonical instead is how sites lose the wrong page.</p>

<h2>The canonical points at another site</h2>

<p>A cross-domain canonical is legitimate for syndicated content: if you republish an article
on a partner site, that copy canonicalising back to your original is exactly right. What is
almost never right is your own pages canonicalising to a domain you do not control, which
usually arrives with a copied template or a staging environment that was promoted with its
config intact.</p>

<p><strong>Fix:</strong> if you did not mean to hand the URL to someone else, make it
self-canonical. Check the whole template, not the one page you noticed.</p>

<h2>No canonical at all</h2>

<p>Not fatal — search engines will choose a URL. But you have left the choice to them on any
page reachable at more than one address, and most pages are: with and without a trailing
slash, with tracking parameters appended, under both <code>http://</code> and
<code>https://</code>, with and without <code>www</code>. Every share with a
<code>?utm_source=</code> on it is another candidate.</p>

<p><strong>Fix:</strong> a self-referencing canonical on every indexable page, absolute, with
the protocol and host you actually want. Self-canonical is not redundant — it is how a page
says "the version without the tracking parameters is the one".</p>

<h2>The canonical points somewhere unexpected</h2>

<p>The subtlest failure: every page in a section canonicalising to the section's landing page.
Each product canonicalises to the category, each article to the blog index. Someone
implemented "canonical" as "the parent page" rather than "this page", and every individual
page is now telling search engines not to index it.</p>

<p>Sites in this state can lose almost their entire long tail while every page still returns
200 and looks perfectly healthy in a browser.</p>

<p><strong>Fix:</strong> self-canonical, unless there is a specific duplicate to consolidate.
If you want the concept rather than the fix list,
<a href="/learn/canonical-tags/">what a canonical tag actually does</a> explains it.</p>

<h2>Why a crawler finds these and a page check does not</h2>

<p>Four of the five need context beyond the page itself: whether the target is
<code>noindex</code>, whether it is on your domain, whether it is the page's own URL, whether
another page also claims it. Docket separates them into distinct findings because they have
distinct fixes — "canonical problems: 12" tells you nothing about which of five different jobs
you are being asked to do.</p>

<p><a class="btn" href="/download/">Download Docket</a></p>
"""
    return render(
        cat="how-to", slug="fix-conflicting-canonicals",
        title="How to fix conflicting canonical tags",
        desc=("Two canonicals on one page, canonicals pointing at noindex pages or another "
              "domain, and the section-wide mistake that can cost a site its long tail."),
        h1="How to fix conflicting canonical tags",
        crumb='<a href="/">Docket</a> / <a href="/how-to/">Fix it</a> / conflicting canonicals',
        body=body,
        faq=[
            ("What happens if a page has two canonical tags?",
             "Google's documented behaviour is to ignore conflicting canonical tags and "
             "choose a URL itself. Two tools each writing the tag leaves you with less "
             "control over indexing than having neither."),
            ("Can a canonical tag point to a noindex page?",
             "It can, and it is self-defeating: you have said the real version is elsewhere "
             "and that the elsewhere must not be indexed. Both pages drop out. Use noindex "
             "to remove a page, never a canonical."),
            ("Should every page canonicalise to itself?",
             "Yes, unless there is a specific duplicate to consolidate. Self-canonical is "
             "how a page says the version without tracking parameters, without www, on "
             "https, is the one that should be indexed."),
            ("Is a cross-domain canonical ever correct?",
             "Yes — for syndicated content. A partner's republished copy canonicalising back "
             "to your original is exactly right. Your own pages canonicalising to a domain "
             "you do not control almost never is."),
        ],
    )


if __name__ == "__main__":
    print(conflicting_canonicals())
