#!/usr/bin/env python3
"""The tracking lane — six checks, and until now not one page on this site.

A gap analysis of every capability in the app against every page here found two
whole lanes with no coverage at all. This is the larger one: six checks that ran
on every audit since the lane was written, described nowhere except as six rows
in the catalogue table.

**Every check name and the count come from `data/checks.csv`**, which is
exported from the shipped engine. Typing "six checks" here would put the number
in a place nothing verifies, which is the fault this site has a gate for.

**The measurements are from audits run on 2026-08-14** and are reported as what
they are: four sites, named by category rather than by name, because a business
that never asked to be audited should not be an example in somebody's marketing.
Four is not a sample and no rate is computed from it.
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from render import DATA, render  # noqa: E402

SITE = Path(__file__).resolve().parents[2] / "site"


def _lane(lane: str) -> list[dict]:
    with (DATA / "checks.csv").open() as handle:
        return [r for r in csv.DictReader(handle) if r["lane"] == lane]


def marketing_tag_audit() -> Path:
    rows = _lane("martech")
    items = "\n".join(
        f'<li><strong>{r["title"]}</strong> <code>{r["id"]}</code></li>'
        for r in rows)

    body = f"""
<p class="lede">A marketing tag audit answers one question: does the tracking you believe is
running actually run, on every page, for every visitor? It is a different question from
"is the tag installed", and the gap between them is where reporting quietly stops matching
reality.</p>

<p>Docket runs <strong>{len(rows)} checks</strong> in this area on every audit. They are the
least glamorous part of the report and the most likely to be costing money right now,
because a missing tag does not break anything a visitor can see. Nothing errors. The site
looks fine. The numbers in your dashboard are simply smaller than the truth, and they have
been for as long as nobody checked.</p>

<h2>Why "installed" is the wrong question</h2>

<p>Tag managers are installed once, on a template, and then the site grows. A landing page
built for one campaign gets published from a different template. A checkout flow gets
rebuilt by a contractor. A blog moves to a subdomain. Each of those is a page where the tag
is absent, and none of them announce it — the tag is still installed, on the pages it was
installed on.</p>

<p>So the check that matters is coverage: of the pages Docket read, how many carried the
tag. One page missing a pixel in a funnel of four is a quarter of your conversions
attributed to nobody.</p>

<h2>What Docket looks for</h2>

<ul>
{items}
</ul>

<p>Two of those need explaining, because they are not what people expect from a tag audit.</p>

<p><strong>Consent and privacy compliance</strong> is checked because a tag firing before
consent is worse than a tag missing. A missing tag costs you data. A tag that fires before
the visitor agrees is a legal exposure in the EU and the UK, and it is invisible in every
dashboard — the data arrives and looks perfect.</p>

<p><strong>UTM tagging hygiene</strong> is about your own links. Inconsistent casing splits
one campaign into two rows in your reports, and internal links carrying UTM parameters
overwrite the original source of the session — so a visitor who arrived from search and
then clicked your own tagged banner is recorded as arriving from the banner. Your best
channel gets credited to your worst.</p>

<h2>What we found looking at real sites</h2>

<p>On 2026-08-14 we audited four live business sites — an Italian food retailer, a French
bakery chain, a US coffee retailer and a US museum — and the tracking lane produced a
finding on the coffee retailer that is worth quoting exactly as it was written:</p>

<blockquote><p>No analytics tag on any page Docket could see</p></blockquote>

<p>The important words are <em>could see</em>. That site renders its pages with JavaScript
and ships almost no HTML, so a tag injected at runtime would not appear in what Docket read.
The finding says what was observed and stops there, rather than concluding that a large
retailer has no analytics — which would be a claim about somebody's business made from an
absence of evidence.</p>

<p>That is deliberate, and it is the same rule everywhere in the product: a check that could
not see must not report nothing as though it were zero. If you want the JavaScript-rendered
answer, <code>--render</code> runs the page in WebKit and audits what a browser actually
gets. <a href="/learn/javascript-rendering/">How that works, and when it is worth the
time.</a></p>

<p>Four sites is not a sample and there is no rate here to quote. It is one measurement,
reported because it shows what the lane does and where it stops.</p>

<h2>Doing this yourself, without Docket</h2>

<p>You do not need a tool for the first pass. Open your site, view source on five pages
chosen from different templates — homepage, a product or service page, a blog post, a
landing page, the thank-you page after a form — and search each for your measurement ID.
The thank-you page is the one to check first: it is the page that proves a conversion
happened, it is usually built last, and it is the page most often published from a template
nobody added the tag to.</p>

<p>If all five carry it, you have ruled out the common failure. If one does not, you have
found the thing this lane exists for, and it took four minutes.</p>

<h2>What this lane deliberately does not do</h2>

<p>It does not tell you whether your tracking is <em>correct</em> — whether the events fire
on the right actions, whether revenue is passed accurately, whether your goals mean what
you think. Those need to be tested in your analytics account against real sessions, and a
crawler cannot see them. Docket reports what is present in the pages it read and does not
guess at the rest.</p>

<p><a class="btn" href="/download/">Download Docket</a></p>
"""
    return render(
        cat="learn", slug="marketing-tag-audit",
        title="Marketing tag audit: is your tracking on every page?",
        desc=(f"The {len(rows)} tracking checks Docket runs — analytics coverage, ad "
              "pixels, consent timing, UTM hygiene — and the common failure you "
              "can check yourself in four minutes."),
        h1="Marketing tag audit",
        crumb='<a href="/">Docket</a> / <a href="/learn/">Learn</a> / Marketing tag audit',
        body=body,
        faq=[
            ("What is a marketing tag audit?",
             "A check that the analytics and advertising tags you believe are running "
             "actually appear on every page, for every visitor, and fire at the right "
             "time. It is different from checking a tag is installed: tags are "
             "installed on templates, and sites grow pages that use other templates."),
            ("Why would a page be missing my analytics tag?",
             "Because tags are added to a template, not to a site. Landing pages built "
             "for a campaign, checkout flows rebuilt by a contractor, and blogs moved "
             "to a subdomain are all pages published outside the template the tag was "
             "added to. Nothing errors when it happens."),
            ("Can Docket see tags that JavaScript injects at runtime?",
             "Not by default — it reports what is present in the HTML it read, and says "
             "so rather than concluding a site has no analytics. Running an audit with "
             "--render executes the page's JavaScript in WebKit first and audits what a "
             "browser actually receives."),
            ("Does Docket check whether my tracking is correct?",
             "No. It checks what is present in the pages it read. Whether events fire on "
             "the right actions and whether revenue is passed accurately can only be "
             "tested against real sessions in your analytics account, and a crawler "
             "cannot see them."),
        ],
    )


BUILDERS = [marketing_tag_audit]


def build_all() -> list[Path]:
    return [b() for b in BUILDERS]


if __name__ == "__main__":
    for p in build_all():
        print(p)
