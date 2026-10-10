#!/usr/bin/env python3
"""How to fix render-blocking resources.

Sourced from Docket's `perf.render_blocking` (backend/seo_engine/checks/performance.py)
and the classifier that feeds it (extract.py: a script with a src and no async or
defer, and not a module, and a stylesheet with no media restriction).

Every count and every quoted line of finding text comes from data/render-blocking-run.json,
written by docket-app/scripts/measure_render_blocking_fixture.py: a real Docket audit of a
small fixture site of ours, before and after the fix. Nothing about a third-party site.
The five-file threshold is the check's own and is written as a word.
"""
from __future__ import annotations

import datetime
import html
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from render import buy_block, render  # noqa: E402

_RUN = json.loads((Path(__file__).resolve().parent.parent.parent / "data" / "render-blocking-run.json").read_text())


def _when() -> str:
    d = datetime.date.fromisoformat(_RUN["date"])
    return f"{d.day} {d.strftime('%B %Y')}"


def render_blocking() -> Path:
    b, a = _RUN["before"], _RUN["after"]
    nb, na = b["most_blocking"], a["most_blocking"]
    f = b["finding"]
    esc = html.escape
    # The finding's own detail names the page it measured; the fixture's address is
    # a local port and means nothing to a reader, so it is replaced, and said to be.
    detail = esc(f["detail"].split(" on http")[0]) + " on the page measured."
    body = f"""
<p class="lede">A render-blocking resource is a stylesheet or a script in the head that the
browser must download and read before it can paint anything. The fix is two moves. Add
<code>defer</code> to the scripts the first screen does not need, and load the stylesheets the
first screen does not need after it. Keep what the first screen needs, and nothing else, in the
way.</p>

<h2>What counts as blocking</h2>

<p>Two things stop the first paint.</p>

<ul>
<li><strong>A script with a <code>src</code> and no <code>async</code> or <code>defer</code>.</strong>
The browser stops reading the page, fetches the file, runs it, and only then carries on.
A script with <code>type="module"</code> is deferred by default, so it does not block.</li>
<li><strong>A stylesheet with no media restriction.</strong> The browser will not paint until it
has every such stylesheet, because painting without one would flash unstyled text.</li>
</ul>

<p>Inline <code>&lt;style&gt;</code> blocks make no request, so they are not part of this.
Putting the few rules the first screen needs inline is a normal way to keep one file off the
critical path.</p>

<h2>Scripts: add defer</h2>

<p><code>defer</code> downloads the file while the page is read and runs it after the page is
parsed, in the order written. That is the right choice for most scripts, including the ones
that depend on each other.</p>

<pre><code>&lt;script src="/js/app.js" defer&gt;&lt;/script&gt;</code></pre>

<p><code>async</code> runs the file as soon as it arrives, in no promised order. Use it only for
a script that depends on nothing and that nothing depends on, such as a stats snippet. When in
doubt, use <code>defer</code>.</p>

<h2>Stylesheets: keep one, load the rest late</h2>

<p>Work out which stylesheet draws the first screen: the layout, the type, the header. That one
stays as a normal link. The others (a theme for a page you are not on, a widget library, a print
sheet) can wait.</p>

<pre><code>&lt;link rel="stylesheet" href="/css/layout.css"&gt;
&lt;link rel="stylesheet" href="/css/widgets.css" media="print" onload="this.media='all'"&gt;
&lt;noscript&gt;&lt;link rel="stylesheet" href="/css/widgets.css"&gt;&lt;/noscript&gt;</code></pre>

<p>A <code>media="print"</code> stylesheet does not block, because it is not needed for the
screen. The <code>onload</code> switches it to every medium once it has arrived. The
<code>noscript</code> line is for a visitor with scripts off, who would otherwise never get that
file. If you can, merge small files into the one you keep. Fewer files is fewer requests, even
over HTTP/2.</p>

<h2>A real before and after</h2>

<p>I wrote a small fixture site for this page: a typewriter repair workshop, a few pages, four
stylesheets and three scripts in the head. I audited it with Docket on {_when()}, changed the
head, and audited it again. The pages are ours; nothing here is measured on anyone else's site.</p>

<p>Before: all four stylesheets and all three scripts were plain. Docket reported this, in its own
words:</p>

<pre><code>{esc(f["title"])}
{detail}</code></pre>

<p>The fix it printed was: <em>{esc(f["fix"])}</em> The head after I followed it:</p>

<pre><code>{esc(_RUN["after_head"])}</code></pre>

<p>That left {na} blocking file on each page, down from {nb}, and Docket stopped reporting the
page. Nothing visible changed, because the stylesheets I moved were not needed for the first
screen. Whether a stylesheet is needed for the first screen is the one judgement here, and a
crawler cannot make it for you.</p>

<h2>What Docket counts, and what it cannot see</h2>

<p>The check counts the blocking files on each page it crawled and reports the pages with five or
more. It reads the markup, as a browser's first pass would.</p>

<ul>
<li><strong>It counts a blocking script wherever it sits.</strong> A plain script at the very end
of the body costs the content above it much less than one in the head, and Docket counts both
the same. If every blocking file Docket names is at the end of the body, read the finding as an
overstatement.</li>
<li><strong>It does not know which stylesheet draws the first screen.</strong> That is why the
fix above asks you to decide.</li>
<li><strong>It does not measure Largest Contentful Paint.</strong> Blocking files delay the first
paint, which is part of it, and the finding says so. The measured value for your page is in
PageSpeed Insights or Search Console. A browser run such as Lighthouse measures one page in
detail, and Docket counts the same defect across every page it crawls; see
<a href="/vs/lighthouse-alternative/">Docket and Lighthouse side by side</a>.</li>
</ul>

<h2>When it is not worth doing</h2>

<p>A page with two blocking files has little to gain, and the check stays quiet below five for that
reason. If the finding names a handful of pages on a large site, fix the shared template first,
since one change in the head fixes all of them. A slow server is a different cause, covered in
<a href="/how-to/fix-compression-and-caching/">how to fix compression and caching</a>, and
images that push the page around are covered in
<a href="/how-to/fix-layout-shift/">how to fix layout shift</a>.</p>

{buy_block("howto-render-blocking", big=False, try_app="howto-render-blocking-try-free")}
"""
    return render(
        cat="how-to", slug="fix-render-blocking-resources",
        title="How to fix render-blocking resources on your site",
        desc=("Scripts and stylesheets that stop the first paint. Defer the scripts, load the CSS "
              "you do not need first, and what a crawler can and cannot tell you about it."),
        h1="How to fix render-blocking resources",
        crumb='<a href="/">Docket</a> / <a href="/how-to/">Fix it</a> / render-blocking resources',
        body=body,
        published=_RUN["date"],
        faq=[
            ("What does render-blocking mean?",
             "The browser has to download and read the file before it can paint anything. "
             "A plain script in the head and a stylesheet with no media restriction both do that."),
            ("Should I use defer or async?",
             "Use defer for most scripts. It runs them after the page is read, in the order written. "
             "Use async only for a script that depends on nothing and that nothing depends on."),
            ("Will loading CSS with media=print and onload break my page without JavaScript?",
             "It can, so add a noscript link to the same file. Visitors with scripts off then get "
             "the stylesheet normally."),
            ("Does Docket measure Largest Contentful Paint?",
             "No. It counts the blocking files in the markup of every page it crawls. The measured "
             "value for a page comes from PageSpeed Insights or Search Console."),
        ],
    )


if __name__ == "__main__":
    print(render_blocking())
