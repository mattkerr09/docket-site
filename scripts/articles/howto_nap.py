#!/usr/bin/env python3
"""How to fix inconsistent name, address and phone (NAP) on your own site.

Sourced from Docket's `local.phone_inconsistent` and `local.address_inconsistent`
(backend/seo_engine/checks/local_seo.py: more than two different phone numbers presented as the
site's own, and more than three spellings of one address, on a site with one set of premises; the
same number written two ways counts once).

Every count and every quoted line of finding text comes from data/nap-run.json, written by
docket-app/scripts/measure_nap_fixture.py: a real Docket audit of a small fixture site of ours, before
and after. The phone numbers in it are 555 numbers. Nothing about a third-party site. Google's guidance was read at its own page on
2026-10-12 and is paraphrased with the link; the page says plainly that it does not claim Google
penalises spelling variants, because Google's page does not say so.
"""
from __future__ import annotations

import datetime
import html
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from render import buy_block, render  # noqa: E402

_RUN = json.loads((Path(__file__).resolve().parent.parent.parent / "data" / "nap-run.json").read_text())


def _when() -> str:
    d = datetime.date.fromisoformat(_RUN["date"])
    return f"{d.day} {d.strftime('%B %Y')}"


def nap() -> Path:
    esc = html.escape
    ph, ad = _RUN["before"]["local.phone_inconsistent"], _RUN["before"]["local.address_inconsistent"]
    body = f"""
<p class="lede">NAP is your business's name, address and phone number. The fix is to choose one exact
form of each, copy it from your Google Business Profile, and print that same block everywhere on your
own site, from one place in the template so it cannot drift. Docket flags a site that shows several
different phone numbers, or one address written several ways. This is housekeeping, and it is worth most
when the variants are real mistakes, such as an old number still in a footer.</p>

<h2>What Google says</h2>

<p>I read Google's page on local ranking on {_when()}:
<a href="https://support.google.com/business/answer/7091">Tips to improve your local ranking on
Google</a>. It says local results are mainly based on relevance, distance and prominence. For
relevance it asks you to provide complete and detailed business information: your full address if
customers can visit, your hours, your category. For prominence it points to links to the business and to
reviews. It also asks you to keep your information up to date.</p>

<p>Be clear about what that does not say. The page does not say that two spellings of your address on your
own site cost you ranking. So the case for tidying is accuracy and a single source of truth, not a penalty.
A wrong number or an old address costs you in a plain way: someone uses it.</p>

<h2>What Docket reports</h2>

<ul>
<li><strong>Several phone numbers.</strong> More than two different numbers that the site presents as its
own, on a site with one set of premises. The same number written two ways, such as
<code>(616) 555-0134</code> and <code>616-555-0134</code>, counts as one number, so formatting alone does
not trigger it.</li>
<li><strong>One address, many spellings.</strong> More than three different spellings of the same address,
such as &ldquo;Street&rdquo; and &ldquo;St&rdquo;, or &ldquo;Suite 2&rdquo; and &ldquo;#2&rdquo;.</li>
</ul>

<p>Both are left alone on a business with more than one place, or a page that links to its locations, because
a number for each branch is correct. Docket also looks at where a number sits. A number in the page chrome,
in the structured data, behind a <code>tel:</code> link or on a contact page is read as the site's own. A
number quoted once in body copy, such as another organisation's helpline, is not counted against you when the
site has said which numbers are its own.</p>

<h2>The fix</h2>

<ol>
<li><strong>Pick the form.</strong> Open your Google Business Profile and copy the name, address and phone
exactly as it shows. That is the form to use.</li>
<li><strong>Print it from one place.</strong> Put the block in the footer template or an include, not typed
on each page, so a change is made once.</li>
<li><strong>Match the structured data.</strong> The <code>telephone</code> and address in your LocalBusiness
markup should be the same as the visible block.</li>
<li><strong>Retire old and spare numbers.</strong> A previous number, a fax line or a call-tracking number
should be removed, or kept only on the one page it belongs to, such as a campaign landing page.</li>
<li><strong>Keep the link working.</strong> The number should sit behind a <code>tel:</code> link, covered in
<a href="/how-to/fix-phone-links-that-will-not-dial/">how to fix phone links that will not dial</a>.</li>
</ol>

<h2>A real before and after</h2>

<p>I wrote a small fixture site for this page: {_RUN["before"]["pages"]} pages of a one-location typewriter repair
workshop. I audited it with Docket on {_when()}. The pages are ours and the phone numbers are made up;
nothing here is measured on anyone else's site.</p>

<p>Before, the footers carried four different numbers, and the address was written four different ways
across them. Docket reported this, in its own words:</p>

<pre><code>{esc(ph["title"])}
{esc(ph["detail"])}

{esc(ad["title"])}</code></pre>

<p>The fixes it printed were: <em>{esc(ph["fix"])}</em> and <em>{esc(ad["fix"])}</em> I then made every footer
the same block, printed from one place:</p>

<pre><code>{esc(_RUN["after_footer"])}</code></pre>

<p>Docket reported neither finding on the second audit.</p>

<h2>What Docket cannot tell you</h2>

<ul>
<li><strong>Anything outside your site.</strong> It reads your pages. Your listings on directories and
map services are yours to check, and no crawl of your site can see them.</li>
<li><strong>Which number is the right one.</strong> It can see that there are four. Only you know which
is the line you answer.</li>
<li><strong>Formatting differences in one number.</strong> It treats the same number written two ways as
one, so it will not ask you to tidy that. Matching your Business Profile exactly is still sensible.</li>
<li><strong>Whether several numbers are deliberate.</strong> It leaves multi-location businesses alone,
but a site with one place and a separate number for sales and support will be flagged, and the decision to
keep both is yours.</li>
</ul>

<h2>Where to start</h2>

<p>Search your site for your phone number and for the first line of your address. If the footer is built
from a template, the fix is usually one edit. The wider ground, the business markup, the name, the place named
in your titles and why a local business may not be showing in the map, is at
<a href="/for/local-business/">why your business is not in the map pack</a>, and the question of where an audit
finds your address is at
<a href="/how-to/where-an-audit-looks-for-your-address/">where an audit looks for your address</a>. What Docket
adds is the same check across every page, ranked with the rest; see how that compares with
<a href="/vs/">other audit tools</a>.</p>

{buy_block("howto-nap", big=False, try_app="howto-nap-try-free")}
"""
    return render(
        cat="how-to", slug="fix-inconsistent-name-address-phone",
        title="How to fix NAP inconsistencies (name, address, phone)",
        desc=("Choose one exact form of your business name, address and phone, print it from one place, "
              "and match your Google Business Profile. What Docket flags."),
        h1="How to fix inconsistent name, address and phone",
        crumb='<a href="/">Docket</a> / <a href="/how-to/">Fix it</a> / name, address and phone',
        body=body,
        faq=[
            ("What is NAP?",
             "Your business's name, address and phone number. NAP consistency means they read the same wherever "
             "they appear on your site."),
            ("Does Google penalise inconsistent NAP?",
             "Google's local ranking guidance asks for complete, accurate and up-to-date business information. It "
             "does not say that spelling variants on your own site are penalised. A wrong or old number is the real "
             "cost."),
            ("What counts as an inconsistent phone number to Docket?",
             "More than two different numbers shown as the site's own on a one-location site. The same number written "
             "two ways counts once."),
            ("Does Docket check my directory listings?",
             "No. It reads your own site only."),
        ],
    )


if __name__ == "__main__":
    print(nap())
