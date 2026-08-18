#!/usr/bin/env python3
"""The conversion lane — nine checks, one of which had a page.

The second of the two lanes the gap analysis found uncovered. `cvr.dead_contact`
had `/learn/dead-contact-address/`; the other eight had nothing but a row in the
catalogue table.

This lane is the one most likely to be dismissed as fluff, so the page leads with
what a crawler can honestly judge and states plainly what it cannot. Conversion
work is mostly judgement and testing, and a tool that implied otherwise would be
selling the thing this site exists to argue against.

**Check names and count come from `data/checks.csv`**, exported from the
shipped engine.

**The findings quoted are real**, from audits run 2026-08-14 against a US coffee
retailer, described by category rather than named.
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


def conversion_audit() -> Path:
    rows = _lane("conversion")
    items = "\n".join(
        f'<li><strong>{r["title"]}</strong> <code>{r["id"]}</code></li>'
        for r in rows)

    body = f"""
<p class="lede">Ranking is only half of it. A page that arrives at the top of the results
and then fails to tell a visitor what to do next has cost you the same money as a page
nobody found — you simply paid it further down the funnel.</p>

<p>Docket runs <strong>{len(rows)} checks</strong> on the pages that have to convert. Not
one of them tells you whether your offer is good, and none of them can replace testing.
What they do is catch the mechanical failures: the page that ranks for a promise it does
not repeat, the contact form nobody can complete, the phone number that will not dial on
the device most people are holding.</p>

<h2>What Docket looks at</h2>

<ul>
{items}
</ul>

<h2>Three findings from one real site</h2>

<p>Auditing a US coffee retailer on 2026-08-14 produced three conversion findings, and they
are a fair illustration of what this lane is and is not good for.</p>

<p><strong>"2 key pages have no clear call to action"</strong>, at HIGH. This is the
mechanical kind and it is worth exactly what it says: two pages whose job is to move
somebody forward offered nothing to click. That is checkable, and it is checkable without
any opinion about the business.</p>

<p><strong>"No social proof on any conversion page"</strong>, at MEDIUM. Also mechanical —
no reviews, testimonials, counts or badges appeared in the markup Docket read. Note the
scope: <em>in the markup Docket read</em>. A site that loads its reviews from a widget
after the page renders has social proof that this check cannot see, which is why it sits at
MEDIUM and not higher.</p>

<p><strong>"The site only serves buyers who are already ready"</strong>, at LOW. This is
the interesting one. Every page was built to sell to somebody who has already decided;
nothing addressed a person still working out whether they want the thing at all. That is a
real gap and it is also a judgement, which is why it is reported at LOW and phrased as an
observation rather than an instruction. You may be running that strategy deliberately.</p>

<h2>Message match is the one people fix first</h2>

<p>The check that most often changes something is <code>cvr.message_match</code>: whether
the promise in your title tag — the words somebody read in the search results and clicked —
is repeated in the headline they land on.</p>

<p>When they differ, the visitor's first act on your page is to check whether they are in
the right place. Some of them decide they are not. Nothing on the page is broken, the
bounce looks like ordinary disinterest, and the cause is one sentence written by a
different person at a different time from the one above it.</p>

<p>It is also the cheapest thing on this list to fix. You are editing one line.</p>

<h2>The phone number that will not dial</h2>

<p>Two checks here exist because of failures that are invisible on a desktop and total on a
phone: a number printed as text with no <code>tel:</code> link, and an email address on a
domain that cannot receive mail. Both look perfectly fine to whoever published them,
because whoever published them never tried to use them from the device their customers
use. <a href="/learn/dead-contact-address/">The mail one is worth its own page</a> — an
address on a domain with no MX record bounces to the sender, so you never learn that
anybody tried.</p>

<h2>What this lane deliberately does not do</h2>

<p>It does not score your copy, judge your design, or predict a conversion rate. It cannot
tell you whether your price is right, whether your offer is compelling, or whether the
person who left would have bought at a different headline. Those are answered by testing
against real visitors, and any tool that claims to answer them from your HTML is selling
you its own opinion with a number attached.</p>

<p>What it can do is make sure the mechanical things are not silently costing you the
traffic you already earned.</p>

<p><a class="btn" href="/download/">Download Docket</a></p>
"""
    return render(
        cat="learn", slug="conversion-audit",
        title="Conversion audit: 9 checks on your landing pages",
        desc=(f"The {len(rows)} conversion checks Docket runs — calls to action, social "
              "proof, message match, dead contact details — and the judgement calls "
              "it refuses to make for you."),
        h1="Conversion audit",
        crumb='<a href="/">Docket</a> / <a href="/learn/">Learn</a> / Conversion audit',
        body=body,
        faq=[
            ("What is a conversion audit?",
             "A check of the pages that have to turn a visitor into an enquiry or a "
             "sale, looking for mechanical failures: no call to action, a headline "
             "that does not match the title people clicked, a phone number that will "
             "not dial, contact details that cannot receive anything."),
            ("Can a tool tell me why my landing page does not convert?",
             "Only partly, and honestly only the mechanical part. Whether the offer is "
             "compelling or the price is right can only be answered by testing against "
             "real visitors. A tool that gives you a conversion score from your HTML is "
             "reporting its own opinion with a number attached."),
            ("What is message match and why does it matter?",
             "Whether the promise in your title tag — the words somebody read in the "
             "search results before clicking — is repeated in the headline they land "
             "on. When it is not, the visitor's first act is to work out whether they "
             "are in the right place, and some decide they are not. It is usually a "
             "one-line fix."),
            ("Does Docket see reviews loaded by JavaScript?",
             "Not by default. The social proof check reports what appeared in the HTML "
             "it read, which is why it is reported at medium rather than higher — a "
             "site whose reviews arrive from a widget after render has social proof "
             "this check cannot see."),
        ],
    )


BUILDERS = [conversion_audit]


def build_all() -> list[Path]:
    return [b() for b in BUILDERS]


if __name__ == "__main__":
    for p in build_all():
        print(p)
