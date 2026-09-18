#!/usr/bin/env python3
"""How to find and fix pages competing for the same search.

Promised on the how-to hub. Sourced from Docket's `content.competing_pages`
check, including the part that is not obvious from the outside: the site's own
subject has to be removed before anything is compared, or every page on a
focused site looks like it competes with every other.

No numeric literals — the thresholds live in the engine, and a figure written
into prose here would be the second place that number lives.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from render import render  # noqa: E402


def competing_pages() -> Path:
    body = """
<p class="lede">Google shows one result per site for most queries. When two of your pages aim at
the same search, they do not double your chances — they split the internal links and relevance
that should have backed one page, and neither ranks as well as one would have. Nobody reports
this to you, because both pages look fine.</p>

<h2>Why nothing catches it</h2>

<p>Every audit tool looks for <strong>duplicate</strong> content: identical titles, identical
bodies. Competing pages are not duplicates. They are genuinely different pages — different
words, different length, usually written months apart by different people, often both good.
That is exactly why they survive: there is nothing wrong with either one on its own.</p>

<p>The damage is only visible in relation. "Best running shoes for flat feet" and "Running
shoes for flat feet: a buyer's guide" are two answers to one question. A duplicate-content
check compares them and finds no duplication, because there is none.</p>

<h2>How to find them by hand</h2>

<p>Ask your site the question a searcher would, and see how many answers it has:</p>

<pre><code>site:example.com running shoes flat feet</code></pre>

<p>If several of your own pages come back and you cannot immediately say which one is
<em>the</em> answer, neither can a search engine. That is the test — not whether the pages are
similar, but whether you can name the one that should win.</p>

<h2>The part that goes wrong when you automate it</h2>

<p>The obvious approach is to group pages by the words their titles share. On a real site this
reports everything. A bakery's pages all say "sourdough"; a dental practice's all say "dental".
Group on that and the site is competing with itself on every page, which is noise, and noise
gets switched off.</p>

<p><strong>Subtract what the whole site is about before comparing anything.</strong> What is
left is what each page is chasing individually — "starters", "classes", "delivery" — and pages
that share <em>those</em> are the ones actually pointed at the same search. It is also worth
requiring more than one word in common, or every page containing "guide" competes with every
other one.</p>

<h2>Deciding which page wins</h2>

<p>Pick the winner on evidence you already have, in this order:</p>

<ul>
<li><strong>Which one already ranks?</strong> If one of them is getting impressions for the
query and the other is not, the decision is made. Do not overturn it because you prefer the
other page's writing.</li>
<li><strong>Which one is better linked?</strong> Internal links are a vote you cast yourself.
The page your own site points at more is the page you already treat as the answer.</li>
<li><strong>Which one matches the intent?</strong> A comparison page and a product page can
carry the same words while answering different questions. If they genuinely answer different
questions, the fix is not a merge — see below.</li>
</ul>

<h2>The fix</h2>

<p><strong>If they answer the same question:</strong> keep one, fold anything worth keeping
from the other into it, and redirect the loser to the winner with a 301. The redirect is the
point — it moves the links the losing page had earned, which is most of what it was worth.</p>

<p><strong>If they answer different questions:</strong> make that true on the page. Rewrite
each title and opening paragraph so a reader can tell them apart in a search result, and link
them to each other so the relationship is stated rather than implied.</p>

<h2>What not to do</h2>

<p><strong>Do not add <code>noindex</code> to the loser.</strong> It stops competing and it
also stops passing on the links it earned. A redirect keeps that value; a noindex discards it.</p>

<p><strong>Do not canonicalise between pages that are genuinely different.</strong> A canonical
says "this is the same thing". If the pages really answer different questions, that is a false
statement, and search engines are free to ignore it — usually by picking whichever page they
prefer, which returns you to the problem you started with.</p>

<p><strong>Do not delete the loser.</strong> Deleting throws away the links along with the
page. Redirect instead: it is the same outcome for the reader and a better one for the site.</p>
"""
    return render(
        cat="how-to", slug="fix-pages-competing-for-one-search",
        title="Pages competing for the same search: find and fix them",
        desc=("Two of your pages aiming at one query split your links and relevance, so "
              "neither ranks as well as one would. How to spot it and which page to keep."),
        h1="Pages competing for the same search",
        crumb='<a href="/">Docket</a> / <a href="/how-to/">Fix it</a> / competing pages',
        body=body,
        faq=[
            ("What is keyword cannibalisation?",
             "Two or more pages on the same site aiming at the same search. They are not "
             "duplicates — they are different pages answering one question — so the internal "
             "links and relevance that should back a single page are split between them."),
            ("Is it the same as duplicate content?",
             "No, and that is why it is easy to miss. Duplicate content means the pages are "
             "the same. Competing pages are genuinely different and often both good; the "
             "problem only exists in the relationship between them."),
            ("How do I know which page to keep?",
             "Use evidence you already have: which page already ranks for the query, and "
             "which one your own site links to more. If neither is clear, keep the one whose "
             "intent matches the search rather than the one you prefer."),
            ("Should I noindex or delete the page I am not keeping?",
             "Neither. Redirect it to the winner with a 301, which moves the links it had "
             "earned. Noindex stops it competing but discards that value, and deleting throws "
             "it away along with the page."),
            ("Can two pages target similar words without competing?",
             "Yes, when they genuinely answer different questions — a comparison page and a "
             "product page, for example. Make the difference visible in the title and opening "
             "paragraph, and link them to each other."),
        ],
    )


if __name__ == "__main__":
    print(competing_pages())
