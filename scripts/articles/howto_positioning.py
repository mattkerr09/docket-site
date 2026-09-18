"""A site that says a different thing on every page.

Promised on the how-to hub. Sourced from the registered check
`brand.positioning` ("Consistent positioning statement").

The archetype: you do not fail this by writing badly. You fail it by writing
well, one page at a time, each about its own subject — every addition an
improvement and the aggregate quietly degrading.

⚠️ The self-implicating example is recent and real: this site failed its own
check after a run of new pages, each written from a different check, each fine
on its own. And the wrong fix described here is one I tried first.

⚠️ Complements /learn/brand-consistency/ rather than repeating it: that page
asks why no crawler looks at brand at all; this one is about one measurable
property and how it decays.

No numeric literals — the check's thresholds live in the engine, and it has
already been tuned once for being too strict.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from render import render  # noqa: E402


def positioning() -> Path:
    body = """
<p class="lede">Read any one page of your site and it is fine. Read twenty and you cannot say
what the company does. No page is wrong, nothing returns an error, and no report you run will
mention it — because the defect does not exist on a page. It exists between them.</p>

<h2>What is actually being measured</h2>

<p>Meta descriptions, across the whole site, looking for words that recur. Not whether they are
well written, and not whether they contain a keyword: only whether some vocabulary survives from
one page to the next.</p>

<p>A company with a settled position repeats it without trying, because it keeps being the true
thing to say. A company without one invents a fresh pitch per page, each accurate about that
page and unrelated to the last.</p>

<p>Note the opposite defect exists too, and is a different problem: the same templated
description on every page. That is not consistency, it is absence, and it is measured
separately.</p>

<h2>Why good work causes it</h2>

<p>This is the part worth internalising. You do not arrive here by being careless. You arrive by
shipping — a page on one topic, then a page on another, each description written to describe
that page as precisely as possible.</p>

<p>Every addition improves the site. The aggregate gets worse. There is no moment where somebody
does the wrong thing, which is exactly why nothing catches it until somebody measures across
pages instead of within one.</p>

<p>This site did it. A run of new pages went up, each written from a different check, each
description accurate about its own subject and sharing nothing with the others, until the
site's own check fired on the site. It was caught by a gate that runs the check before every
deploy — not by anybody reading the pages, because reading the pages tells you nothing.</p>

<h2>The wrong fixes</h2>

<p><strong>Putting your company name in every description.</strong> This is the first instinct
and it does nothing, for a reason worth stating plainly: <em>a site repeating its own name is
not a site saying something</em>. A good check excludes the brand name from this measurement
entirely, because the name recurs even when no idea does.</p>

<p><strong>Pasting one sentence into all of them.</strong> That trades this defect for the
templated-description one, and it puts a claim on pages it is not true of. A description that
oversells the page it describes is a worse problem than an inconsistent one.</p>

<p><strong>Keyword-stuffing a common term.</strong> The measurement is a proxy for whether you
decided what you do. Gaming the proxy leaves the actual condition exactly where it was.</p>

<h2>The fix</h2>

<p><strong>Decide the sentence first.</strong> One plain line that is true of the business —
what it does, for whom, and the thing that distinguishes it. If nobody can write that line, the
site is not the problem.</p>

<p><strong>Then put its words into the descriptions of the pages they are true of.</strong> Not
into all of them. Not into one they are not true of. The pages about your service should sound
related to each other; a legal notice does not need to.</p>

<p><strong>Check it when you add pages, not once.</strong> This decays by addition, so the only
time it can be caught cheaply is as each page goes up.</p>

<h2>What this cannot tell you</h2>

<p>Whether the sentence you settled on is <em>correct</em>. An audit can see that your pages
share vocabulary, or that they do not. It cannot tell you that you have positioned the business
well, or that the thing you repeat is the thing worth repeating. Those are judgements about a
company, and no crawler has an opinion on them.</p>

<p>It is also a measurement with a floor: a site with only a handful of descriptions has not
said enough for the question to mean anything, and a site covering many subjects spreads its
terms out legitimately. A check worth trusting here sets its bar at a recognisable thread rather
than a majority — and the one behind this page was loosened after being unfair to a real site,
which is the correct direction for a test to move when it disagrees with reality.</p>

<p>The broader question of why crawlers ignore brand entirely is
<a href="/learn/brand-consistency/">a separate piece</a>.</p>
"""
    return render(
        cat="how-to", slug="fix-a-site-that-says-something-different-every-page",
        title="When your site stops saying one thing about itself",
        desc=("No page is wrong, but twenty pages describe twenty businesses. Why an audit "
              "measures your site across pages, and how good work causes this."),
        h1="When your site stops saying one thing about itself",
        crumb='<a href="/">Docket</a> / <a href="/how-to/">Fix it</a> / positioning',
        body=body,
        faq=[
            ("What does a positioning check actually measure?",
             "Whether any vocabulary recurs across your meta descriptions. A company with a "
             "settled position repeats it without trying, because it keeps being the true "
             "thing to say. One without invents a fresh pitch per page."),
            ("Will putting my company name in every description fix it?",
             "No, and a good check excludes the brand name on purpose. A site repeating its "
             "own name is not a site saying something — the name recurs even when no idea "
             "does."),
            ("Is the same description on every page the solution?",
             "That is the opposite defect and it is measured separately. It also puts a claim "
             "on pages it is not true of, which is worse than an inconsistent one."),
            ("How does a site end up like this?",
             "By shipping. Each page gets a description written to describe that page as "
             "precisely as possible, every addition improves the site, and the aggregate gets "
             "worse. There is no moment where somebody does the wrong thing."),
            ("Can a tool tell me whether my positioning is any good?",
             "No. It can see whether your pages share vocabulary. Whether the sentence you "
             "settled on is the right one is a judgement about a company, and no crawler has "
             "an opinion on it."),
        ],
    )


if __name__ == "__main__":
    print(positioning())
