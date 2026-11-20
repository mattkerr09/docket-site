#!/usr/bin/env python3
"""A dated core-update checklist and the limits of a first-hand audit."""
from __future__ import annotations

from pathlib import Path

from comparisons import source_link
from render import render

DASHBOARD = "https://status.search.google.com/"
GUIDANCE = "https://developers.google.com/search/docs/appearance/core-updates"
READ = "20 November 2026"
SLUG = "traffic-drop-after-november-2026-core-update"
RULE = "broad in nature, and don't target specific sites or individual web pages"

# The supplied AUDIT.md, not the different audit bundled with FACTS.md.
SCORES = (
    ("Crawlability &amp; indexing", "37.9"),
    ("On-page SEO", "26.5"),
    ("Content quality: surface signals only", "69.0"),
    ("Speed &amp; Core Web Vitals: static estimate only, no Core Web Vitals result", "76.3"),
    ("Structured data", "45.0"),
    ("Links", "93.6"),
    ("Security &amp; trust", "86.5"),
    ("Social &amp; sharing", "45.0"),
    ("Local business SEO: does not apply to this site", "65.5"),
    ("AI search visibility", "77.2"),
    ("Conversion &amp; landing pages", "75.0"),
    ("Tracking &amp; campaign readiness", "99.5"),
    ("Brand consistency", "89.0"),
)


def google_note(topic: str, *, dashboard: bool = False, guidance: bool = False) -> str:
    label, url = ("Search Status Dashboard", DASHBOARD) if dashboard else ("core updates guide", GUIDANCE)
    extra = (f', {source_link("Google core updates guide", GUIDANCE)}' if dashboard and guidance else "")
    updated = "" if dashboard and not guidance else " Google's guide was last updated on 10 December 2025."
    return (f'<p class="verified-note">Checked on Google\'s own pages on {READ}. '
            f'Source for {topic}: {source_link("Google " + label, url)}{extra}.{updated}</p>')


def faq_source(text: str, *, dashboard: bool = False) -> str:
    label, url = ("Google Search Status Dashboard", DASHBOARD) if dashboard else ("Google core updates guide", GUIDANCE)
    return f'{text} {source_link(label, url)}. Checked {READ}.'


def build() -> Path:
    rows = ''.join(f'<tr><th scope="row">{label}</th><td>{score}</td></tr>'
                   for label, score in SCORES)
    body = f"""
<p id="measured-answer">A core update is not an error you can fix with one change.
Google says these changes are <q>{RULE}</q> in its {source_link("core updates guide", GUIDANCE)}.
The {source_link("Google Search Status Dashboard", DASHBOARD)} says the November 2026 core update started on 10 November 2026, may take up to 2 weeks and was still rolling out when read on 20 November 2026.
First rule out technical causes you can check, then judge content quality, and wait for Google to post the rollout's end before reading the traffic data.</p>
{google_note("the rollout dates and scope", dashboard=True, guidance=True)}

<h2>Check the dates first</h2>
<p>Open Search Console and compare clicks from before 10 November 2026 with clicks after that
date. Write down when the fall began and which pages lost clicks. Keep the same filters in
both views so that you are comparing the same part of the site.</p>
<p>As of 20 November 2026, Google's dashboard had no end date for this update. It says the
update applies globally and to all languages. Rankings can keep moving until Google posts
the end. Save the comparison now, then read it again after the rollout ends. A drop that
started before 10 November 2026 is probably something else, so check its timing before
attributing it to this update.</p>
{google_note("the start date and unfinished rollout", dashboard=True)}

<h2>Rule out the technical causes</h2>
<p>These are not what a core update measures. They are checks to rule out a technical fault
so you do not mistake it for the update. The check names below match Check Engine's checks;
a finding still needs a person to decide whether the setting is intended.</p>
<ul>
<li><strong>Broken internal links:</strong> open the missing destination and correct the link
or restore the page. Check <code>index.broken</code>; finding <code>index.broken_internal_links</code>.</li>
<li><strong>Noindex:</strong> inspect the page's tag and response header. Keep a deliberate
exclusion. Check <code>index.noindex</code>.</li>
<li><strong>robots.txt:</strong> read the rule for the affected pages and check whether bots
can read them. Checks <code>index.robots_blocks_all</code>, <code>ai.crawler_access</code>
and <code>ai.edge_access</code>.</li>
<li><strong>Redirects:</strong> follow the old address to its final page and confirm that is
where you meant to send readers. Check <code>index.redirects</code>;
finding <code>index.internal_link_to_redirect</code>.</li>
<li><strong>Canonicals:</strong> compare the declared preferred address with the page you
want listed. Checks <code>index.canonical</code> and <code>index.canonical_conflict</code>.</li>
<li><strong>Duplicate titles:</strong> review the pages together before deciding whether to
rename or combine them. Check <code>index.duplicate_content</code>;
finding <code>index.duplicate_titles</code>.</li>
<li><strong>Sitemap:</strong> check that it exists and lists the pages you intend to publish.
Check <code>index.sitemap</code>; finding <code>index.sitemap_missing</code>.</li>
<li><strong>Mixed content:</strong> check images loaded over http on secure pages.
Checks <code>security.https</code> and <code>security.mixed_content</code>;
finding <code>security.mixed_content_passive</code>.</li>
<li><strong>Layout-shift risk:</strong> review space reserved for images and other elements.
Check <code>perf.cls_risk</code>. This is a static estimate, not a Core Web Vitals result.</li>
</ul>
<p>These checks speak to crawl and index basics, and partly to page experience. They do not
judge whether a page gives a helpful, reliable answer to a person. That needs a separate
content review, as described in {source_link("Google's core updates guide", GUIDANCE)}.</p>
{google_note("the content review and the limits of technical checks")}

<h2>What we found on a real site</h2>
<p>On 20 November 2026, we ran Check Engine SEO 1.3.164, build 1669, the shipped macOS app,
on a public software consulting blog. Default crawl settings read 593 pages in a full report.
The run took 128 seconds. This is an example of what an audit can find, not a diagnosis of a
traffic drop. We have no evidence here that this site's traffic fell.</p>
<p>The overall score was 65.5 of 100 on Check Engine's own scale, not a Google score.
It says nothing about why traffic moved. PageSpeed Insights did not run, so Core Web Vitals
are not in this score. The Speed &amp; Core Web Vitals area below is a static estimate only.</p>
<div class="wrap-tbl"><table>
<caption>Check Engine area scores out of 100, recorded on 20 November 2026</caption>
<thead><tr><th scope="col">Area and limits</th><th scope="col">Score on Check Engine's scale</th></tr></thead>
<tbody>{rows}</tbody></table></div>
<p>The crawl and page checks gave us specific things to inspect:</p>
<ul>
<li>7 pages linked from your own site do not exist: <code>index.broken_internal_links</code>.</li>
<li>11 pages share duplicate titles: <code>index.duplicate_titles</code>.</li>
<li>1 page has noindex: <code>index.noindex</code>. Check whether that is intended.</li>
<li>The sitemap was missing: <code>index.sitemap_missing</code>.</li>
<li>589 pages have no meta description: <code>onpage.description_missing</code>.</li>
<li>34 pages load images over http: <code>security.mixed_content_passive</code>.</li>
<li>593 pages do not declare a language: <code>onpage.lang_missing</code>.</li>
<li>11 pages are at high risk of layout shift: <code>perf.cls_risk</code>, a static estimate
only. This is not a measured Core Web Vitals result.</li>
</ul>
<p>None of those counts establishes a cause for a ranking change. The content-quality
checks are surface signals only, such as word counts, reading patterns and the presence of
dates. They do not judge helpful, reliable, people-first content or whether it is better
than another page.</p>
<p>Other findings have nothing to do with a core update: no structured data on 593 pages,
no contact form, brand and social findings, and tracking and conversion checks.
Structured data can help rich results; it is not a core-update recovery fix.</p>
<p>The Local business findings do not apply to this site. The detector treated a software
blog as a local business, so its findings about local-business markup, a form, reviews and
a phone link are not faults here. The Local business SEO score in the table is recorded
for completeness, with that same limit.</p>
<p class="verified-note">Audit recorded on 20 November 2026 with the shipped Check Engine
macOS app and default crawl settings. Scores use Check Engine's own scale. Speed and
layout-shift risk are static estimates only; PageSpeed Insights did not run.</p>

<h2>What Check Engine cannot tell you</h2>
<p>Check Engine cannot tell you why Google ranked you lower. No tool can establish the
reason for one site's drop. Finding a broken link during a rollout does not prove the
rollout caused the drop, and repairing it does not promise recovery.</p>
<p>Once you have ruled out technical faults, read the affected pages as a visitor would.
Does each page answer the question it promises to answer? Is the explanation reliable?
What would a reader still need to find elsewhere? A word count or an author name cannot
answer those questions for you.</p>
<p>Google's {source_link("core updates guide", GUIDANCE)}, read on 20 November 2026, says
it can take several months for its systems to confirm lasting improvements in helpful,
reliable, people-first content. It gives no recovery date for your site.</p>
{google_note("content quality and the time improvements can take")}

<h2>Choose the next check</h2>
<p>Start with the <a href="/tools/seo-checker/">free SEO checker</a> on your own page.
Use the full app below if you need to look across the site. Keep a record of technical
repairs and content edits, with their dates, so you can tell what changed when you return
to Search Console after the rollout ends.</p>
"""
    return render(
        cat="how-to", slug=SLUG,
        title="Traffic dropped after the November 2026 core update?",
        desc="Check dates and technical faults before judging a core-update traffic drop. A dated Google source and a real audit show what a checker can and cannot tell you.",
        h1="Traffic dropped after the November 2026 core update: what to check first",
        crumb='<a href="/">Check Engine</a> / <a href="/how-to/">Fix it</a> / Core update traffic drop',
        body=body, published="2026-11-20", modified="2026-11-20",
        faq=[
            ("Has Google posted an end date for the November 2026 core update?", faq_source(
                "As of 20 November 2026, no end date was posted. The dashboard says the rollout began on 10 November 2026 and may take up to 2 weeks. Rankings can keep moving until Google posts the end.", dashboard=True)),
            ("Should I repair a broken page during the November core rollout?",
             "Yes, if you have checked that it is a real fault. Record the repair and its date. Do not treat a technical repair as proof of why rankings moved or as a promise of recovery."),
            ("Does a low Check Engine score explain a core-update traffic drop?",
             "No. The score uses Check Engine's own scale, not Google's. Its technical checks help rule out faults. Its content checks are surface signals and cannot judge whether a page is helpful."),
            ("Can content improvements guarantee recovery before this rollout ends?", faq_source(
                "No recovery date is promised. Google says it can take several months for its systems to confirm lasting improvements in helpful, reliable, people-first content.")),
        ],
    )
