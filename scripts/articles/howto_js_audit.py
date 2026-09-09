#!/usr/bin/env python3
"""How to run a JavaScript SEO audit — the procedure, not the concept.

Target query: "javascript seo audit" (22 impressions, Search Console
2026-08-10 to 2026-09-05). /learn/javascript-rendering/ keeps "javascript
rendering" (25) and the conceptual explanation; this page is the steps.
One query per page.

Every number here is measured. The served-vs-rendered figures come from a real
site audited 2026-09-09 while fact-checking Docket 1.3.61; the site is not
named, because publishing a named company's defect to sell a tool is not a
trade this project makes. The figures are reported as what they are — a handful
of pages on one site, not a rate.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import facts as F  # noqa: E402
from render import N_CHECKS, N_LANES, RELEASE, render  # noqa: E402


def javascript_seo_audit() -> Path:
    body = """
<p class="lede">A JavaScript SEO audit answers one question: <em>is the thing you wrote in the
HTML your server sends, or does it only exist after JavaScript runs?</em> Everything else —
which framework, which rendering mode, whose crawler — follows from that answer, and you can
get it in about ten minutes.</p>

<h2>Why the answer is not obvious from looking at the page</h2>

<p>Open the page in a browser and it looks complete, because your browser ran the JavaScript.
View source and you may see something entirely different. Those two views disagree on plenty of
real sites, and the disagreement is invisible until you go looking for it.</p>

<p>It matters because the two audiences behave differently. Google renders JavaScript, on a
delay and with no guarantee about when. The AI crawlers that increasingly decide whether you
get quoted in an answer mostly do not render at all — to them, the page is whatever the server
sent. So a page can rank adequately and be invisible to the systems people now ask instead of
searching. <a href="/learn/ai-search-visibility/">AI search visibility</a> is a separate
surface with a separate failure mode.</p>

<h2>Step 1: read the HTML your server actually sends</h2>

<p>Not the rendered DOM. The bytes.</p>

<pre><code>curl -sS https://example.com/your-page/ | wc -c</code></pre>

<p>Then look at the body text inside those bytes, not the byte count — a big HTML payload with
almost nothing readable in it is exactly the shape you are hunting. A page can be 200 KB of
markup and carry forty words a reader would recognise.</p>

<h2>Step 2: render the same URL and compare</h2>

<p>The audit is the comparison, not either number on its own. In Docket:</p>

<pre><code>docket-render https://example.com/your-page/ --timeout 45 --settle 4</code></pre>

<p>It returns the rendered HTML with the link count, the text length and the script sources, so
you can put the two side by side. Any headless browser does the same job; what matters is that
you measure both views of the same URL in the same session, because comparing today's render
against last week's source tells you about the week, not the page.</p>

<h2>Step 3: read the gap, and know which gap you have</h2>

<p>There are three outcomes and they have different remedies.</p>

<p><strong>The two views agree.</strong> The page is server-rendered. There is no JavaScript SEO
problem here and you can stop — resist the urge to find one.</p>

<p><strong>The HTML is essentially empty.</strong> A shell, a mount point and a script tag.
Every crawler that does not render sees nothing, and the fix is server-side rendering or
prerendering. This is the case most articles describe, and it is the easier one, because it is
obvious the moment you look.</p>

<p><strong>The chrome is server-rendered and the body is not.</strong> This is the one that
hides. The navigation, header and footer arrive in the HTML — so the page is plainly not an
empty shell — while the article itself is fetched after hydration. Measured on one site on
{GAP_MEASURED}, {GAP_COUNT} pages returned {GAP_SERVED} words of main text as served, and
{GAP_RENDERED} once rendered. The pages were not thin. The served HTML was. That is
{GAP_COUNT} pages on one site — an existence proof that the shape occurs and is large when it
does, not a claim about how common it is.</p>

<p>Docket shipped a change for exactly this in {RELEASE}: where a page carries a client-side
framework's hydration marker, a word count is now labelled as a count of the HTML as served,
because a tool that reports "almost no content" about a page carrying six hundred words is
telling you something false in a confident voice.</p>

<h2>Step 4: check what a non-rendering crawler is allowed to fetch</h2>

<p>Rendering is only half of it. A crawler that renders nothing still has to be let in, and the
refusal usually happens somewhere your robots.txt never sees — a bot rule at the CDN, returning
403 to a user-agent the site owner believes is welcome. Send the same request twice, once with
the crawler's user-agent and once with an ordinary browser's, and compare: if only one is
refused, the rule is about the crawler.
<a href="/how-to/fix-ai-crawler-access/">Fixing AI crawler access</a> covers the robots.txt
side of the same question.</p>

<h2>Step 5: confirm what was actually fetched</h2>

<p>A render tells you what a browser can build. It does not tell you what any crawler did.
For that you need the server's own record —
<a href="/learn/log-file-analysis/">log file analysis</a> — which is the only view that
distinguishes "Google could reach this" from "Google fetched this". The two disagree constantly,
and on a JavaScript-heavy site they disagree more.</p>

<h2>What this audit does not tell you</h2>

<p>It does not tell you whether Google rendered your page, or when, or what it saw — nobody
outside Google can measure that, and a tool that implies otherwise is selling you a model as a
measurement. It tells you what the two views contain, which is the part you control.</p>

<p>It also will not tell you that a slow render is the reason you are not ranking. Rendering
delay is real and it is frequently blamed for outcomes it did not cause. Measure the gap, fix
the gap, and judge the result against what you recorded before you started.</p>

<h2>Doing it across a whole site</h2>

<p>The steps above are per-URL, which is fine for a spot check and useless for a site with a
thousand pages. Docket runs the comparison across the crawl and reports the pages where the two
views disagree, alongside the rest of a
<a href="/learn/seo-audit/">technical SEO audit</a> —
<a href="/learn/what-docket-checks/">{N_CHECKS} checks across {N_LANES} areas</a>, on your machine, with no
crawl credits. If you would rather see how it compares to the tools you already know, there is
<a href="/vs/screaming-frog-alternative/">Docket vs Screaming Frog</a> and
<a href="/vs/ahrefs-site-audit-alternative/">Docket vs Ahrefs Site Audit</a>.</p>

<p>Whatever you use, the discipline is the same: two views of the same URL, measured in the same
session, and a decision about which of the three gaps you are looking at before you change
anything.</p>

<p><a class="btn" href="/download/">Download Docket</a></p>
""".replace("{RELEASE}", RELEASE) \
     .replace("{GAP_MEASURED}", F.gap_measured()) \
     .replace("{GAP_COUNT}", str(F.gap_count())) \
     .replace("{GAP_SERVED}", F.gap_served()) \
     .replace("{GAP_RENDERED}", F.gap_rendered()) \
     .replace("{N_CHECKS}", str(N_CHECKS)) \
     .replace("{N_LANES}", str(N_LANES))
    return render(
        cat="how-to", slug="javascript-seo-audit",
        title="How to run a JavaScript SEO audit (step by step)",
        desc=("Compare the HTML your server sends against the rendered page, in five steps. "
              "Which of the three gaps you have decides the fix."),
        h1="How to run a JavaScript SEO audit",
        crumb='<a href="/">Docket</a> / <a href="/how-to/">Fix it</a> / JavaScript SEO audit',
        body=body,
        published="2026-09-09",
        faq=[
            ("What is a JavaScript SEO audit?",
             "A comparison of two views of the same URL: the HTML the server returns, and the "
             "page after JavaScript has run. Where they disagree, some crawlers see less than "
             "your visitors do. Everything else in the audit follows from the size and shape "
             "of that gap."),
            ("Does Google render JavaScript?",
             "Yes, on a delay and with no guarantee about when. That is not the same as saying "
             "it makes no difference: the render is a second pass, and the AI crawlers that "
             "increasingly decide whether you are quoted mostly do not render at all. A page "
             "that only exists after JavaScript is invisible to them."),
            ("My page looks fine in the browser. Is that enough?",
             "No, and it is the most common reason this problem goes unnoticed. The browser "
             "ran the JavaScript before you looked. Use view-source or curl to see what the "
             "server sent, which is what a non-rendering crawler gets."),
            ("The HTML has my navigation and footer but not the article. Is that a shell?",
             "Not a shell, and it is the case that hides. An empty shell is obvious; a page "
             "whose chrome is server-rendered looks server-rendered at a glance while the body "
             "arrives after hydration. Compare the MAIN content of the two views, not the page "
             "as a whole, or the navigation will mask the gap."),
            ("Can a tool tell me what Googlebot rendered?",
             "No. Nobody outside Google can measure what Google rendered or when. A tool can "
             "tell you what your server sent and what a browser builds from it; anything "
             "beyond that is a model presented as a measurement."),
        ],
    )


BUILDERS = [javascript_seo_audit]


def build_all() -> list[Path]:
    return [b() for b in BUILDERS]


if __name__ == "__main__":
    for p in build_all():
        print(p)
