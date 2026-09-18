#!/usr/bin/env python3
"""How to fix the pages that earn, before the ones that do not.

Promised on the how-to hub. Sourced from the priority weighting added in
1.3.77 and from `links.money_page_weak_inlinks`, including the restraint that
matters more than the feature: the lift orders findings WITHIN a severity band
and is deliberately too small to cross one.

Complements /learn/priority-model/, which is about the formula. This is about
which pages the formula should favour, and why knowing that is the owner's job
rather than the tool's.

No numeric literals — the multiplier lives in the engine and is published, with
its value interpolated, on the priority-model page.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from render import render  # noqa: E402


def money_pages() -> Path:
    body = """
<p class="lede">Most audit tools hand you a list sorted by how broken things are. None of them
know that one of your pages takes card details and another is a tag archive nobody has opened
since 2019. A missing title on each is the same finding, ranked the same way — and only one of
them is why the phone stopped ringing.</p>

<h2>Which pages are your money pages</h2>

<p>The ones where a visitor does the thing you want: buys, books, requests a quote, starts a
trial, or gets in touch. On most sites that is a short list — pricing, contact, the booking
form, the main service or product pages, and the homepage, which is where the traffic that
reaches the others usually lands.</p>

<p>If you are unsure whether a page belongs on the list, ask what would happen if it returned an
error for a day. If you would find out from your bank balance rather than from your analytics,
it is a money page.</p>

<p>Write the list down. It is the piece of information no tool has and you already do, and
almost everything below depends on it.</p>

<h2>Why the ranking does not know</h2>

<p>A priority score is usually built from how severe a problem is, how many pages it affects,
and how much work the fix is. Every one of those terms is about the <em>problem</em>. None is
about the <em>page</em>. So a broken title on your pricing page and the same broken title on a
paginated archive arrive at the same number, and the plan orders them by accident.</p>

<p>Docket now multiplies a finding's priority when it lands on a page where the site earns, so
the same fault sorts above its twin elsewhere.
<a href="/learn/priority-model/">The formula is published in full</a>, including that term.</p>

<h2>The restraint that matters more than the feature</h2>

<p>It is tempting to weight commercial pages heavily. Do not, and the reason is worth
understanding if you are doing this by hand.</p>

<p><strong>An important page does not make a small problem into a big one.</strong> A critical
fault anywhere on the site — a page that cannot be indexed at all, a server returning errors —
still outranks a medium-severity issue on your pricing page. If the weighting were strong
enough to reverse that, the plan would contradict the severity printed next to every item, and
a reader could not tell which of the two labels to believe.</p>

<p>So the useful rule is: <strong>let page value break ties, not set the order.</strong> Work
down by severity; within each band, do the money pages first.</p>

<h2>What to check on them first</h2>

<p>Run these against your list before anything else on the site:</p>

<ul>
<li><strong>Can it be indexed at all?</strong> A <code>noindex</code> or a blocked path on a
page that sells is the whole problem, and it is invisible to everyone except a crawler.</li>
<li><strong>Is it linked from more than one place?</strong> A pricing page reachable only from
the footer reads as incidental. Site-wide link checks stay quiet about a handful of
thinly-linked pages, which is right in general and wrong here.</li>
<li><strong>Does the contact route work?</strong> A phone number that will not dial on a phone,
a form that posts nowhere, an address that has not been true since the last move.</li>
<li><strong>Does it say the price, or say why it does not?</strong> A page that makes somebody
email to find out what something costs loses the ones who will not.</li>
<li><strong>Does it load on the connection your customers have?</strong> Not yours.</li>
</ul>

<h2>What this does not do</h2>

<p>It does not tell you which pages earn. No crawler can see your revenue, and any tool that
claims to rank by business value without being told what your business is has guessed. The
weighting recognises the shape of a commercial page — a path like <code>/pricing</code> or
<code>/contact</code> — which covers the common case and misses a site that names things
differently. That is a floor, not a census: it can miss a money page, and it will not promote
one that is not.</p>

<p>So keep your own list. The tool orders the work; you decide what the work is for.</p>
"""
    return render(
        cat="how-to", slug="fix-your-money-pages-first",
        title="Fix the pages that make you money first",
        desc=("Audit tools rank by how broken a thing is, not by which page it is on. How to "
              "identify your money pages and let page value break ties without overriding "
              "severity."),
        h1="Fix the pages that make you money first",
        crumb='<a href="/">Docket</a> / <a href="/how-to/">Fix it</a> / money pages',
        body=body,
        faq=[
            ("What is a money page?",
             "A page where a visitor buys, books, requests a quote, starts a trial or gets in "
             "touch — plus the homepage. A useful test: if it returned an error for a day, "
             "would you notice it in revenue rather than in analytics?"),
            ("Why do audit tools rank a pricing page the same as a tag archive?",
             "Because the usual priority terms — severity, how many pages are affected, and "
             "how much work the fix is — are all about the problem. None of them is about "
             "which page the problem is on."),
            ("Should an important page outrank a more serious problem elsewhere?",
             "No. A critical fault anywhere still comes first. Let page value break ties "
             "within a severity band rather than set the order, or the plan contradicts the "
             "severity shown next to each item."),
            ("What should I check on a money page first?",
             "Whether it can be indexed at all, whether more than one page links to it, "
             "whether the contact route actually works, whether it states the price, and "
             "whether it loads on your customers' connections rather than yours."),
            ("Can a tool work out which pages earn on its own?",
             "Not really. It can recognise the shape of a commercial page from its path, which "
             "covers the common case and misses sites that name things differently. Keep your "
             "own list — it is the information you have and the tool does not."),
        ],
    )


if __name__ == "__main__":
    print(money_pages())
