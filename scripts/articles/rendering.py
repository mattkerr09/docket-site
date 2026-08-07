#!/usr/bin/env python3
"""JavaScript rendering — what it is for, and what it changed for Scout.

Numbers here were measured while building the feature: notion.so fetched
statically versus rendered in WebKit, on 2026-08-06.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from render import DMG, DMG_SIZE, render  # noqa: E402


def javascript_rendering() -> Path:
    body = f"""
<p class="lede">A crawler that does not run JavaScript sees the HTML your server sent, which
on a modern site is often an empty shell. We fetched notion.so twice: the served HTML
contained <strong>0 characters of text and 0 links</strong>, and the same page rendered in a
browser contained <strong>2,068 characters and 106 links</strong>.</p>

<p>Everything an audit would say about that page from the static fetch is wrong. Thin
content, no internal links, no structured data — all artefacts of not running the code.</p>

<h2>Who renders and who does not</h2>

<p>Google renders JavaScript, on a second pass that can lag the first by days. That delay is
the whole problem: new pages are discovered late, and internal link signal arrives late or
not at all.</p>

<p>Most AI crawlers do not render at any point. To the crawlers behind ChatGPT and Perplexity,
a client-rendered page is blank. If being cited in AI answers matters to you, server-side
rendering is not an optimisation, it is the entry fee. We measured
<a href="/index/">who is blocked from where</a> separately.</p>

<h2>How Scout does it</h2>

<p>macOS ships a browser engine. WebKit is a system framework, so Scout renders through a
112 KB helper built against it rather than bundling a browser — the download is still {DMG_SIZE},
and nothing is fetched at install time. The audit engine stays what it was: dependency-free
Python that never needed a browser to do most of its job.</p>

<p>Rendering is <strong>off by default</strong>, for two reasons worth stating plainly.
It executes the page's JavaScript, so analytics fire and advertising pixels load — requests
to servers you did not intend to contact when you asked for an audit. And it is roughly ten
to thirty times slower than fetching. Both are decisions for you to make rather than
surprises to discover.</p>

<h2>What it unlocked</h2>

<h3>Pages that only exist after hydration</h3>
<p>The notion.so case. Scout now compares the served HTML against the rendered DOM and
reports the difference as a measurement rather than a suspicion — 0 characters versus 2,068
is a fact you can take to whoever owns the front end.</p>

<h3>What your tag manager actually loaded</h3>
<p>GTM injects tags at runtime, so a static fetch sees the container and nothing else. Scout
used to say "GTM is present, so your analytics may be configured inside it" and stop. Rendering
notion.so surfaced <strong>54 scripts that were not in the served HTML</strong>, among them
Marketo, the LinkedIn Insight Tag and the X advertising pixel.</p>
<p>That matters beyond curiosity. Tags you cannot enumerate are tags nobody is auditing, and
every one of them is a third party receiving your visitors' data.</p>

<h3>Timings from a browser rather than from markup</h3>
<p>First Contentful Paint and DOM Content Loaded now come from the browser's own performance
API. Scout previously inferred layout-shift and paint risk from markup patterns, which is
useful and is not measurement.</p>

<h2>Where this stops, and where another tool is better</h2>

<p>Rendering in WebKit is not rendering in Chrome. Google evaluates your site in a Chromium
renderer, and while the two agree on nearly everything, a bug that only appears in Blink is a
bug Scout will not see.</p>

<p>Rendering also says nothing about how much of the page Google read in the first
place. It fetches at most 2MB of any URL and indexes that as though it were the whole file, so
a heavy page can be truncated before the renderer is ever involved —
<a href="/learn/googlebot-2mb-limit/">measured here</a>.</p>

<p>Nor does rendering give you Core Web Vitals. LCP, INP and CLS are <em>field</em> metrics —
they come from real users on real connections, not from one machine on a fast desk. Scout can
pull that data from the Chrome UX Report when you turn it on, which is the same source Search
Console uses. Any tool presenting a single synthetic run as "your Core Web Vitals" is
misrepresenting what the number is.</p>

<p>And if you want to crawl a large site with rendering at volume, <a
href="/vs/screaming-frog-alternative/">Screaming Frog</a> has been doing it for years with
configurable wait strategies, JavaScript error capture and a rendered-versus-raw diff view
built for exactly this. Scout renders a sample — the shallowest pages, ten by default —
because that answers "is this site client-rendered and what is it costing me" without turning
a five-minute audit into an hour.</p>

<h2>Trying it</h2>

<p>In the app, turn on rendering before you audit. From the command line:</p>

<pre><code>scout audit https://example.com --render 10</code></pre>

<p>The report says how many pages were rendered, which ones needed it, and what the tag
manager loaded. If the helper is missing it says that too, rather than quietly falling back
to a static crawl and letting you believe otherwise.</p>

<p><a class="btn" href="{DMG}">Download Scout for Mac</a></p>
"""
    return render(
        cat="learn", slug="javascript-rendering",
        title="JavaScript rendering: auditing what a browser actually sees",
        desc=("A crawler that does not run JavaScript sees what your server sent. notion.so "
              "returns 0 characters of text statically and 2,068 rendered. What rendering "
              "changes."),
        h1="Auditing what a browser actually sees",
        crumb='<a href="/">Scout</a> / <a href="/learn/">Learn</a> / JavaScript rendering',
        body=body,
        faq=[
            ("Do search engines run JavaScript?",
             "Google does, on a second pass that can lag the first crawl by days. Most AI "
             "crawlers do not render at all, so a client-rendered page is blank to the "
             "crawlers behind ChatGPT and Perplexity."),
            ("Does Scout bundle a browser?",
             "No. macOS ships WebKit as a system framework, so rendering is a 112 KB helper "
             "built against it. The download is " + DMG_SIZE + " and nothing is fetched at install."),
            ("Why is rendering off by default?",
             "It executes the page's JavaScript, so analytics fire and ad pixels load — "
             "requests to servers you did not intend to contact by asking for an audit. It "
             "is also ten to thirty times slower than fetching."),
            ("Can rendering measure Core Web Vitals?",
             "No, and nothing that runs on one machine can. LCP, INP and CLS are field "
             "metrics from real users on real connections. Scout reads them from the Chrome "
             "UX Report, the same source Search Console uses."),
        ],
    )


BUILDERS = [javascript_rendering]


def build_all() -> list[Path]:
    return [b() for b in BUILDERS]


if __name__ == "__main__":
    for p in build_all():
        print(p)
