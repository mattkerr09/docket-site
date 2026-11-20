#!/usr/bin/env python3
"""Ahrefs facts from the supplied 20 November 2026 reading only."""
from pathlib import Path

from comparisons import CTA_LINK_EXPERIMENT, _measured, source_link
from render import N_CHECKS, N_LANES, PRICE_COMPACT, founding_price_sentence, render

READ = "20 November 2026"
AUDIT = "https://ahrefs.com/site-audit"
FREE = "https://ahrefs.com/webmaster-tools"
PLANS = "https://ahrefs.com/pricing"
CONTENT = "https://ahrefs.com/blog/content-audit/"
# Supplied pricing-table and Webmaster Tools readings, including the addendum.
FREE_CREDITS = 5_000
PLANS_READ = (("Lite", 129, 100_000, 25_000),
              ("Standard", 249, 500_000, 50_000),
              ("Advanced", 449, 1_500_000, 250_000))
ISSUES = 180
EXTRA_SEATS = ((2, 40), (5, 60), (10, 80))


def checked(company: str, *sources: tuple[str, str]) -> str:
    links = ', '.join(source_link(label, url) for label, url in sources)
    owner = company + ("'" if company.endswith("s") else "'s")
    return (f'<p class="verified-note">Checked on {owner} own pages on {READ}. '
            f'Sources: {links}.</p>')


def build() -> Path:
    offer = founding_price_sentence() or f"{PRICE_COMPACT}."
    rows = ''.join(f'<tr><th scope="row">{name}</th><td>${monthly:.2f} a month</td>'
                   f'<td>{credits:,}</td><td>{pages:,}</td></tr>'
                   for name, monthly, credits, pages in PLANS_READ)
    lite_price, lite_credits, lite_pages = PLANS_READ[0][1:]
    (lite_seats, lite_seat_price), (standard_seats, standard_seat_price), (advanced_seats, advanced_seat_price) = EXTRA_SEATS
    body = f"""
<p id="measured-answer">Ahrefs Site Audit is the crawler: its {source_link("Site Audit page", AUDIT)} lists {ISSUES}+ SEO and AEO issues.
{source_link("Ahrefs Free, formerly Webmaster Tools", FREE)}, gives {FREE_CREDITS:,} crawl credits per verified project per month.
{source_link("Ahrefs pricing", PLANS)} lists Lite at ${lite_price:.2f} a month on monthly billing, with {lite_credits:,} crawl credits a month and at most {lite_pages:,} pages per project.
Ahrefs does not list a separate Content Audit tool on the pages read; its {source_link("content-audit blog", CONTENT)} describes a process.</p>
{checked("Ahrefs", ("Site Audit", AUDIT), ("Ahrefs Free", FREE), ("pricing", PLANS), ("content audit", CONTENT))}

<h2>Choose between a free crawl and a paid plan</h2>
<p>Start with the site you need to audit and the size of the crawl. Ahrefs Free provides
Site Audit for verified websites. Its free allowance is {FREE_CREDITS:,} crawl credits per
verified project per month. The Webmaster Tools page says those credits are used when you
crawl an HTML page returning status code 200.</p>
<p>That is a monthly allowance. Before repeating a crawl after repairs, leave room for the
pages you will read again. Keep the allowance beside your URL list so a partial result does
not get mistaken for a complete review.</p>
{checked("Ahrefs", ("Free allowance and credit rules", FREE))}

<h2>Read both paid crawl limits</h2>
<p>Ahrefs' pricing page includes Site Audit and Always-on audit in Lite. Standard includes
Lite's features, and Advanced adds HTTP authentication in Site Audit. These are the monthly
billing figures and crawl limits read on that page:</p>
<div class="wrap-tbl"><table class="cmp">
<caption>Ahrefs monthly prices and Site Audit limits</caption>
<thead><tr><th scope="col">Plan</th><th scope="col">Monthly billing</th><th scope="col">Crawl credits per month</th><th scope="col">Max pages per project</th></tr></thead>
<tbody>{rows}</tbody></table></div>
<p>Prices exclude tax. Lite's monthly credit total does not allow a single project to pass
its page cap. Standard and Advanced also have separate monthly allowances and project caps.
Check both before putting a large site on a plan.</p>
<p>The pricing page offers extra users: up to {lite_seats} on Lite at ${lite_seat_price:.2f} a month each, {standard_seats} on Standard
at ${standard_seat_price:.2f} a month each, and {advanced_seats} on Advanced at ${advanced_seat_price:.2f} a month each. Include those charges if
more people need access.</p>
{checked("Ahrefs", ("Plans, limits and extra users", PLANS))}

<h2>Why the issue counts differ</h2>
<p>Ahrefs' Site Audit page says {ISSUES}+ SEO and AEO issues. Its Webmaster Tools page says
170+ technical and on-page SEO issues. We use the Site Audit page's count here and name the
page so you can check the claim. An issue count alone does not tell you which findings will
matter on your own pages.</p>
{checked("Ahrefs", ("Site Audit issue count", AUDIT), ("Webmaster Tools issue count", FREE))}

<h2>Is Ahrefs content audit another tool?</h2>
<p>No separate Content Audit tool was listed on the pricing, Site Audit or Webmaster Tools
pages read. Ahrefs' blog describes the work as a process: ask what holds the content back,
then improve it. The post describes using Site Audit to collect and export URLs.</p>
<p>For that work, read <a href="/how-to/content-audit/">how to do a content audit with Ahrefs</a>.
A list of URLs starts the review. You still need to decide what each page should do and
whether to keep it, improve it, merge it or remove it.</p>
{checked("Ahrefs", ("Pricing", PLANS), ("Site Audit", AUDIT), ("Webmaster Tools", FREE), ("Content-audit process", CONTENT))}

<h2>Where Check Engine fits</h2>
<p>We make Check Engine. It runs {N_CHECKS} checks across {N_LANES} areas on your computer
and ranks repairs by impact and effort. Its free version shows the score, problem counts
and the top problem with its fix. The full plan and report exports need a licence.</p>
<p>Use Ahrefs Free if its verified-site allowance covers the crawl you need. Consider a
paid Ahrefs plan when its listed limits and included tools fit your work. Try Check Engine
when you want a local fix plan for a public site. It has no backlink or keyword index, no
rank tracking and no shared team workspace.</p>
<p>Check Engine's scheduled re-audits run only while the app is open and the computer is awake.
If you need a crawler running while your computer is off, keep that requirement in your
buying brief. {offer}</p>
{_measured("<p>This is our app checking our own site. Read the findings to judge whether its fix plan fits the work you need to do.</p>", "list")}

<h2>Compare a result before spending money</h2>
<p>Pick a part of the site you know well and inspect the affected pages beside the report.
Check that you can find the reported problem and carry out its repair. After making the
change, repeat the check on the same pages. Save the crawl settings with the result so you
can explain a difference in coverage as well as a difference in findings.</p>
<p>For a different crawl setup, see <a href="/vs/screaming-frog-alternative/">Check Engine vs Screaming Frog</a>.
For Check Engine's licence and refund terms, read <a href="/pricing/">our pricing page</a>.</p>
{CTA_LINK_EXPERIMENT}
"""
    return render(
        cat="vs", slug="ahrefs-site-audit-alternative",
        title="Ahrefs Site Audit: free limits and paid plans",
        desc="Ahrefs Site Audit prices and crawl limits, read 20 November 2026. Compare Ahrefs Free, Lite, Standard and Advanced with a local fix plan.",
        h1="Ahrefs Site Audit: free limits and paid plans",
        crumb='<a href="/">Check Engine</a> / <a href="/vs/">Compare</a> / Ahrefs',
        body=body, modified="2026-11-20",
        faq=[
            ("How many free Ahrefs crawl credits does a verified project get?",
             f"Ahrefs Free gives {FREE_CREDITS:,} crawl credits per verified project per month. "
             f"{source_link('Ahrefs Free allowance', FREE)}. Checked {READ}."),
            ("Does Lite's monthly credit allowance remove its project cap?",
             f"No. Lite has {lite_credits:,} crawl credits a month and a maximum of {lite_pages:,} pages per project. "
             f"It costs ${lite_price:.2f} a month on monthly billing. {source_link('Ahrefs pricing', PLANS)}. Checked {READ}."),
            ("Which Ahrefs page supplies the 180+ issue count here?",
             f"The Site Audit product page. Its Webmaster Tools page uses the older 170+ count. "
             f"{source_link('Site Audit', AUDIT)} and {source_link('Webmaster Tools', FREE)}. Checked {READ}."),
            ("Can Check Engine run scheduled crawls while my computer is off?",
             "No. Its scheduled re-audits run only while the app is open and the computer is awake."),
        ],
    )
