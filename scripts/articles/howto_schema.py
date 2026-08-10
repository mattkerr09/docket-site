#!/usr/bin/env python3
"""How to fix structured data errors.

The last of the four guides the how-to hub has been promising. Sourced from
Docket's own schema checks — `schema.invalid_json`, `schema.no_identity`,
`schema.none`, `schema.no_breadcrumbs`, `schema.low_coverage` and the
`schema.incomplete.*` family — including their severities, which carry the
argument: invalid JSON-LD is HIGH because the markup is not partially working,
it is absent.

Percentages in the prose would be measurements, so there are none; the only
numeric literals are HTTP status codes, declared in ALLOWED.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from render import render  # noqa: E402


def structured_data_errors() -> Path:
    body = """
<p class="lede">Structured data is the one part of a page written entirely for machines, which
means nothing about the page tells you when it is broken. It renders identically whether the
markup is perfect, malformed, or contradicting what a visitor can see.</p>

<h2>JSON-LD that does not parse</h2>

<p>The most consequential error and the least visible. A trailing comma, a smart quote pasted
from a document, an unescaped quotation mark inside a description — any one of them makes the
block invalid JSON, and invalid JSON is not partially read. The whole block is discarded.</p>

<p>So a page can carry complete, correct Product markup and be treated exactly like a page
with no markup at all. Nothing appears in the page, nothing appears in the browser, and the
rich result you built simply never arrives.</p>

<p><strong>Fix:</strong> validate the rendered output, not the template. The commonest cause
is a CMS field interpolated straight into JSON without escaping — a product description
containing a <code>"</code> breaks the document, and it breaks only for the products whose
descriptions happen to contain one, which is why it survives spot-checking.</p>

<h2>The site never says who it is</h2>

<p>A site can carry Article markup on every post and Product markup on every listing and still
never declare the organisation behind them. That is the entity search engines attach
everything else to — the thing that makes "who published this" answerable.</p>

<p>Docket reports this at HIGH when a site uses structured data but omits an
<code>Organization</code> or <code>LocalBusiness</code> node, because the omission is
invisible: every individual page validates, and the graph has no root.</p>

<p><strong>Fix:</strong> one <code>Organization</code> (or <code>LocalBusiness</code>, for a
business with premises) with the name, logo, URL and <code>sameAs</code> links to the profiles
you actually control. Put it in one place and include it everywhere rather than repeating it
per template.</p>

<h2>Markup that contradicts the page</h2>

<p>The category with real consequences. Ratings in the markup that appear nowhere on the page,
a price in the markup that differs from the price displayed, availability that says in-stock
on a sold-out product. Search engines' guidelines require the marked-up content to be visible
to the visitor, and this is the class most likely to attract a manual penalty rather than
simply being ignored.</p>

<p>It is usually not deceptive. It is usually a template that emits an aggregate rating from a
field the page no longer displays, or a price from a source the page stopped using.</p>

<p><strong>Fix:</strong> mark up only what a visitor can see on that page. If the rating is
real, show it; if it is not shown, remove it from the markup.</p>

<h2>Required properties missing</h2>

<p>Each rich result type has properties that are required rather than recommended, and a type
missing one is ineligible — not degraded. Docket reports these per type, because "structured
data errors: 9" does not tell you whether nine pages need one field each or one page needs
nine.</p>

<p><strong>Fix:</strong> work by type. Every eligible rich result has a documented required
set, and filling the required ones matters far more than adding optional ones to types that
already qualify.</p>

<h2>Coverage, which is a judgement rather than an error</h2>

<p>Reported at LOW deliberately. A site where a minority of pages carry markup is not broken —
plenty of pages have no rich result to earn. What the number is for is noticing when the
templates that <em>should</em> carry it do not: products, articles, FAQs, the pages with an
eligible type sitting unclaimed.</p>

<h2>Why the validator and the crawler disagree</h2>

<p>Testing tools check one URL you paste in. The failures above are mostly template-level and
data-dependent — they appear on the subset of pages whose content happens to break the
template. A single-URL test on a page that works tells you nothing about the ones that do not,
which is why this is a crawl problem rather than a validation problem.</p>

<p><a class="btn" href="/download/">Download Docket</a></p>
"""
    return render(
        cat="how-to", slug="fix-structured-data-errors",
        title="How to fix structured data errors",
        desc=("Invalid JSON-LD is discarded whole, not partially read. The five ways schema "
              "breaks, why a single-URL validator misses most of them, and the fix for each."),
        h1="How to fix structured data errors",
        crumb='<a href="/">Docket</a> / <a href="/how-to/">Fix it</a> / structured data errors',
        body=body,
        faq=[
            ("What happens if my JSON-LD has a syntax error?",
             "The whole block is discarded. Invalid JSON is not partially read, so a page "
             "with complete, correct markup and one trailing comma is treated exactly like a "
             "page with no markup at all."),
            ("Why does my structured data validate but produce no rich result?",
             "Usually a required property is missing for that type, or the marked-up content "
             "is not visible on the page. Both leave the markup valid and ineligible."),
            ("Can I mark up a rating that is not shown on the page?",
             "No. Search engines require marked-up content to be visible to the visitor, and "
             "this is the category most likely to attract a manual action rather than simply "
             "being ignored."),
            ("Does every page need structured data?",
             "No. Plenty of pages have no eligible rich result type. Coverage matters where a "
             "template should carry it — products, articles, FAQs — not as a number to "
             "maximise."),
            ("Why isn't a single-URL validator enough?",
             "Most schema failures are template-level and data-dependent: they appear only on "
             "pages whose content happens to break the template, such as a description "
             "containing a quotation mark. Testing a page that works proves nothing about the "
             "ones that do not."),
        ],
    )


if __name__ == "__main__":
    print(structured_data_errors())
