#!/usr/bin/env python3
"""How to write title tags that fit.

Sourced from Docket's five title and description checks and, more usefully,
from `words.display_width` — the reason those checks do not count characters.
That function exists because counting characters applied an English rule to
Japanese and produced a false positive on most of a real site's pages.

The article states no threshold numbers at all. Docket's TITLE_MIN/MAX and
DESC_MIN/MAX are width units, not the character counts every other guide
quotes, so printing them here would invite the reader to compare them against a
number measured a different way. The advice that survives is the shape — put
the distinguishing words first, do not duplicate — which is also the advice
that does not go stale when a threshold moves.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from render import render  # noqa: E402


def title_tags() -> Path:
    body = """
<p class="lede">Almost every guide tells you to keep a title under about sixty characters.
That advice is wrong in a way that only shows up on some sites — because search engines
truncate by <em>pixel width</em>, and characters are not all the same width.</p>

<h2>The character count is the wrong unit</h2>

<p>A title of narrow letters fits far more than a title of wide ones. That is a minor
inaccuracy in English and a serious one elsewhere: East Asian characters render at roughly
double the width of a Latin one, so a Japanese title of twenty characters occupies about
forty Latin characters' worth of space.</p>

<p>Docket measures width rather than length, and the reason is a bug it had. A real product
title on a Japanese site — nineteen characters — was reported as "shorter than the minimum"
on eighteen of twenty pages. In width units it was thirty-one: comfortably normal. The tool
was applying an English rule to a language it does not fit, and reporting the mismatch as the
site's fault.</p>

<p>If your site is entirely English the practical difference is small — a title of capital
Ws truncates sooner than one of lowercase Ls, and that is about it. If any part of your site
is in Japanese, Chinese or Korean, a character-counting tool will report problems that do not
exist and miss ones that do.</p>

<h2>What to aim for</h2>

<p>Long enough to say what the page is, short enough to survive the results page. A title that
gets cut mid-word loses the words you chose most carefully, which are usually at the end.</p>

<p>Two things that matter more than hitting a number:</p>

<ul>
<li><strong>Put the distinguishing words first.</strong> Truncation happens at the end, so a
title that opens with your brand name and closes with the page's actual subject loses the
subject. "Emergency plumber, Leeds — Smith &amp; Co" survives truncation. "Smith &amp; Co —
emergency plumbing services in Leeds and surrounding areas" does not.</li>
<li><strong>Every page needs its own.</strong> Duplicate titles across a site are a signal
that the pages are interchangeable, and search engines will pick one and drop the rest.
Template-generated titles that differ only by a hidden ID are duplicates as far as a reader is
concerned.</li>
</ul>

<h2>Keyword stuffing is a real check, not a legacy one</h2>

<p>Repeating the same term through a title still happens, mostly from templates that
concatenate a category, a subcategory and a product name that all contain the same word.
"Plumber — Plumbers in Leeds — Leeds Plumber" is not a keyword strategy, it is three copies
of one word crowding out anything that would make someone click.</p>

<h2>Meta descriptions</h2>

<p>They are not a ranking factor and they do decide clicks. Google frequently rewrites them,
which is not a reason to leave them empty — a rewrite drawn from a page with no description is
usually a sentence you would not have chosen.</p>

<p>The same width rule applies, and the same duplication rule: a description repeated across a
category's worth of pages tells a reader nothing about which result to click.</p>

<h2>What Docket reports, and why they are separate checks</h2>

<p>Missing, too short, too long, stuffed, and duplicated are five different findings because
they are five different jobs. A page with no title needs writing; a page with a title that is
forty characters too long needs cutting; a hundred pages sharing one title needs a template
change. Rolling them into one "title issues" count tells you the size of the problem and
nothing about the work.</p>

<p>Widths are measured in half-width units — a Latin character counts one, a full-width East
Asian character counts two — so the same thresholds apply to every language on your site.</p>

<p><a class="btn" href="/download/">Download Docket</a></p>
"""
    return render(
        cat="how-to", slug="write-title-tags-that-fit",
        title="How to write title tags that fit (width, not characters)",
        desc=("Search engines truncate by pixel width, not character count — which makes the "
              "usual advice wrong on any site that is not entirely English."),
        h1="How to write title tags that fit",
        crumb='<a href="/">Docket</a> / <a href="/how-to/">Fix it</a> / title tags',
        body=body,
        faq=[
            ("How long should a title tag be?",
             "Long enough to identify the page and short enough to survive truncation. The "
             "useful unit is rendered width rather than character count, because search "
             "engines truncate by pixel width and characters are not all the same width."),
            ("Why does character count give the wrong answer?",
             "East Asian characters render at roughly double the width of a Latin one, so a "
             "twenty-character Japanese title occupies about forty Latin characters' worth of "
             "space. Counting characters applies an English rule to languages it does not "
             "fit."),
            ("Where should the important words go in a title?",
             "First. Truncation happens at the end, so a title opening with your brand name "
             "and closing with the page's subject loses the subject."),
            ("Do meta descriptions affect ranking?",
             "No, but they affect clicks. Google often rewrites them, which is not a reason "
             "to omit them — a rewrite drawn from a page with no description is usually a "
             "sentence you would not have chosen."),
            ("Are duplicate titles a problem?",
             "Yes. They signal that pages are interchangeable, and search engines will "
             "generally pick one and drop the others. Template titles differing only by a "
             "hidden ID count as duplicates."),
        ],
    )


if __name__ == "__main__":
    print(title_tags())
