#!/usr/bin/env python3
"""A noindex procedure for both the document and response header."""
from __future__ import annotations

from comparisons import source_link
from real_questions_comparisons import answer_source, note
from render import render

GOOGLE = "https://developers.google.com/search/docs/crawling-indexing/block-indexing"
METHODS = 2  # The meta tag and HTTP header in the supplied Google reading.
RULE = "the page or resource must not be blocked by a robots.txt file"


def build() -> Path:
    body = f"""
<p id="measured-answer">A meta noindex checker needs to inspect {METHODS} places: the HTML meta tag and the X-Robots-Tag response header, as {source_link("Google's noindex guide", GOOGLE)} explains.
Google says <q>{RULE}</q> for noindex to be effective.
Check both places before deciding that a missing meta tag means the page has no noindex rule.</p>
{note("rq-noindex")}

<h2>Read the page source for meta robots</h2>
<p>Open the exact page address you want to check. Use your browser's View Source command and
search for <code>noindex</code>. Look at the whole tag, including its name and content, so you
can tell a directive from a word in the article you are reading.</p>
<pre><code>&lt;meta name="robots" content="noindex"&gt;
&lt;meta name="googlebot" content="noindex"&gt;</code></pre>
<p>These are the meta tag forms shown in {source_link("Google's guide", GOOGLE)}. The robots
name is the general form; googlebot names that crawler. Copy the tag into your notes before
changing a template. This helps you find which setting wrote it if the directive comes back.</p>
{note("rq-noindex")}

<h2>Read the response headers as well</h2>
<p>Open the browser's developer tools, choose the Network panel and reload the page. Select
the document request, then read its response headers. Check the final page response if the
address redirects. Look for <code>X-Robots-Tag</code>.</p>
<pre><code>X-Robots-Tag: noindex</code></pre>
<p>Google documents the HTTP header as another way to return noindex. A header is part of the
server response, so searching only the HTML cannot find it. Google's guide also shows
<code>none</code> as a header value for preventing indexing.</p>
<p>Record the response you actually inspected. A screenshot of the page's design does not
show its response headers. If you ask someone else to fix a header, send the address and the
header text, rather than only the visible page.</p>
{note("rq-noindex")}

<h2>Why blocking the crawl can hide the rule</h2>
<blockquote><p>Google says <q>{RULE}</q>.</p></blockquote>
<p>The page also has to be accessible to the crawler. If access is blocked, Google says the
crawler will not see the noindex rule and the page can still appear in search results.
Google does not support a noindex rule in robots.txt. Put the indexing directive in the meta
tag or response header instead, following {source_link("the noindex documentation", GOOGLE)}.</p>
{note("rq-noindex")}

<h2>Use the existing page check, then finish the manual check</h2>
<p>The <a href="/tools/meta-tag-checker/">Check Engine meta tag checker</a> is a useful starting
point for the page's meta tags. Keep the response-header check beside it. A meta result by
itself does not establish what a separate server header says.</p>
<p>If a page should be listed, ask the person responsible for its template and server settings
whether the directive is intended. If it should stay out, keep the directive and check that
the crawler can read it. The same finding can call for opposite changes depending on the
page's purpose.</p>

<h2>Keep a small record of the decision</h2>
<ul>
<li>The exact address and the final response you checked.</li>
<li>The meta directive, if present, with its name and content.</li>
<li>The response header, if present, with its complete value.</li>
<li>Whether you want the page listed, and who owns that decision.</li>
</ul>
<p>After a repair, reload and repeat both checks. Do this on another page using the same
template as well. A correction on a single document does not prove a shared setting changed.
For a wider review of the result, see <a href="/learn/seo-audit/">what an SEO audit covers</a>.</p>
"""
    return render(
        cat="how-to", slug="check-a-page-for-noindex",
        title="Meta noindex checker: check tags and response headers",
        desc="Check meta robots in the page source and X-Robots-Tag in response headers. Google's robots.txt rule explains why an unread noindex can fail.",
        h1="Meta noindex checker: how to check a page for noindex",
        crumb='<a href="/">Check Engine</a> / <a href="/how-to/">Fix it</a> / Check noindex',
        body=body, published="2026-11-20",
        faq=[
            ("Can a noindex header exist when View Source has no meta robots tag?", answer_source(
                "Yes. X-Robots-Tag is an HTTP response header. Inspect the response headers as well as the HTML before drawing a conclusion.", "Header guidance", GOOGLE)),
            ("Should I add noindex to robots.txt to remove a listing?", answer_source(
                "No. Google does not support that rule in robots.txt. Its guide describes a meta tag or HTTP response header, on a resource the crawler can access.", "Noindex rules", GOOGLE)),
            ("What should I save before changing a noindex setting?",
             "Save the exact address, the meta tag and response header you found, and the intended listing decision. That gives the person making the change a result they can check again."),
            ("Does a noindex finding always call for removing the directive?",
             "No. First decide whether the page should be listed. A checkout step or a private draft may have a different purpose from an article you want readers to find. Check the intended outcome before editing."),
        ],
    )
