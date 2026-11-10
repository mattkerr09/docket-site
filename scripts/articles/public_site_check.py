#!/usr/bin/env python3
"""Public Site Check launch page. Kept out of the build until the CEO enables it.

Product facts and the measured proof line were checked by Claude on 2026-11-08.
Title II dates come from the same source as the live date tool and guide.
"""
from __future__ import annotations

from html import escape
from pathlib import Path
import re
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from brand import html as brand_html
from render import FOUNDING_MOUNT, NAV, render  # noqa: E402
from articles.title_ii import LARGE, SMALL, POP  # noqa: E402


PUBLIC_SITE_CHECK_PAGE = False
# TODO CEO: set the add-on's checkout URL when its product is ready. Never use the SEO licence URL.
PSC_BUY_URL = ""
#: The add-on's price (PLAN decision 2, 2026-11-08) and the standard its checks cite; the date the page's facts were read.
PSC_PRICE = 149
WCAG = "2.1"
CHECKED = "8 November 2026"

PROOF = ("We ran it on our own site first: 26 issues on the first 25 pages it checked, all fixed; "
         "the re-check found none on 39 pages.")
LIMITS = ("Automated checks find some accessibility problems, not all. "
          "This is not legal advice and does not say whether a site meets the law.")

# Number, name and level from the engine's rules.py, supplied in the job.
CRITERIA = [
    ("1.1.1", "Non-text Content", "A"),
    ("1.3.1", "Info and Relationships", "A"),
    ("1.4.1", "Use of Color", "A"),
    ("1.4.2", "Audio Control", "A"),
    ("1.4.3", "Contrast (Minimum)", "AA"),
    ("1.4.10", "Reflow", "AA"),
    ("2.4.1", "Bypass Blocks", "A"),
    ("2.4.2", "Page Titled", "A"),
    ("2.4.4", "Link Purpose (In Context)", "A"),
    ("2.4.6", "Headings and Labels", "AA"),
    ("2.4.7", "Focus Visible", "AA"),
    ("3.1.1", "Language of Page", "A"),
    ("3.3.2", "Labels or Instructions", "A"),
    ("4.1.1", "Parsing", "A"),
    ("4.1.2", "Name, Role, Value", "A"),
]


def public_site_check() -> Path:
    rows = "".join(
        f'<tr><th scope="row">{number}</th><td>{name}</td><td>{level}</td></tr>'
        for number, name, level in CRITERIA
    )
    buy = (f'<p><a class="btn" href="{escape(PSC_BUY_URL, quote=True)}" data-ev="Buy" '
           'data-ev-button="public-site-check">Buy Public Site Check</a></p>') if PSC_BUY_URL else ""
    body = f"""
<p class="lede">Public Site Check is a ${PSC_PRICE} add-on to Docket SEO&rsquo;s desktop app for Mac and 64-bit Windows.
It checks a public body&rsquo;s site against WCAG {WCAG} Level A and AA, sorts posted documents by its Title II date,
and writes a plain-words board report as a PDF.</p>
<p>For towns, counties, school districts, libraries and special districts.
<strong>It works without a Docket SEO licence.</strong> A clerk can hand the report to a council or board.</p>
<p class="tool-free">Checked {CHECKED}.</p>

<aside class="tool-out" aria-label="Limits">
<p><strong>{LIMITS}</strong></p>
<p>Public Site Check never recommends an overlay.</p>
</aside>

<div class="buy-block">
<p><strong>${PSC_PRICE} once per licence.</strong> Unlimited sites on that computer. Updates included. 30-day refund.
For Mac and 64-bit Windows. No Docket SEO licence needed.</p>
{buy}
</div>

<h2>Which Title II date applies to your public body?</h2>
<p>Public bodies with a total population of {POP} or more have until <strong>{LARGE}</strong>.
Those with fewer people, and every special district, have until <strong>{SMALL}</strong>.
Use the <a href="/tools/title-ii-date/">Title II date tool</a> to work out your date and which population figure to use.
The <a href="/learn/ada-title-ii-website-dates/">Title II dates guide</a> explains the rule, exceptions and sources.</p>

<h2>The 15 success criteria it checks</h2>
<p>Each finding names its WCAG {WCAG} success criterion and level. Contrast, focus and reflow need the app&rsquo;s
renderer, which renders a sample of pages. The other checks read the HTML.</p>
<div class="wrap-tbl"><table class="cmp">
<caption>WCAG {WCAG} Level A and AA checks in Public Site Check</caption>
<thead><tr><th scope="col">Number</th><th scope="col">Success criterion</th><th scope="col">Level</th></tr></thead>
<tbody>{rows}</tbody>
</table></div>

<h2>Sort the posted documents</h2>
<p>PDFs are read for tags, language, title and whether they are scanned images.
Word and PowerPoint files are flagged for review.</p>
<p>Each document is sorted against your body&rsquo;s Title II date:</p>
<ul>
<li>posted before your date: likely exempt, unless people use it to apply for or take part in something</li>
<li>posted after your date</li>
<li>date unknown</li>
</ul>
<p><strong>Dates are clues, not proof.</strong> Review the dates and how each document is used before deciding
what needs work.</p>

<h2>A report for your council or board</h2>
<p>The board report is a PDF in plain words. It includes:</p>
<ul>
<li>Which Title II date applies and why.</li>
<li>What was checked, with counts by criterion.</li>
<li>The worst pages first, with the fix.</li>
<li>The documents table.</li>
<li>The limits and the line saying it is not legal advice.</li>
</ul>

<h2>What we found on our own site</h2>
<p>{PROOF}</p>
<p>That re-check covers the automated checks on those pages. People still need to check what automation misses.</p>

<h2>Start with your date</h2>
<p><a href="/tools/title-ii-date/">Find your public body&rsquo;s Title II date</a>, then read the
<a href="/learn/ada-title-ii-website-dates/">guide to the dates and exceptions</a> as you plan the work.</p>
"""
    page = render(
        cat="public-site-check", slug="",
        title="Public Site Check: WCAG checks and a board report",
        desc=(f"A ${PSC_PRICE} desktop add-on for public bodies: WCAG {WCAG} Level A and AA checks, "
              "documents sorted by Title II date, and a plain-words board report PDF."),
        h1="Public Site Check",
        crumb='<a href="/">Docket</a> / Public Site Check',
        body=body,
        # The shared renderer derives the first publication date when the page is enabled.
        schema_type="WebPage",
    )
    # Shared chrome sells the separate SEO licence and its founding offer.
    # Keep this page's sole buy path tied to PSC_BUY_URL, without changing other pages.
    original_nav = brand_html(NAV)
    nav = re.sub(r'<a\b[^>]*data-ev="Buy"[^>]*>.*?</a>', "", original_nav, flags=re.S)
    html = page.read_text(encoding="utf-8").replace(original_nav, nav, 1)
    if FOUNDING_MOUNT:
        html = html.replace(FOUNDING_MOUNT, "", 1)
    page.write_text(html, encoding="utf-8")
    return page


def build_all() -> list[Path]:
    return [public_site_check()] if PUBLIC_SITE_CHECK_PAGE else []
