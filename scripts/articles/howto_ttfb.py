#!/usr/bin/env python3
"""How to reduce server response time (TTFB).

Sourced from Docket's `perf.ttfb` (backend/seo_engine/checks/performance.py: the median
time to first byte across the pages crawled, reported as above target, slow across the site,
or slow the first time and fast when asked again, which is a cache in front of a slow server;
the bounds are written below as words).

Every median and every quoted line of finding text comes from data/ttfb-run.json, written by
docket-app/scripts/measure_ttfb_fixture.py: a real Docket audit of a small fixture site of ours,
served by a local server that waits a set time before each page, four ways. Nothing about a
third-party site. The page says plainly that the fixture shows how Docket reads response time,
not how to speed up a real server. The good and poor bounds were read at web.dev/articles/ttfb
on 2026-10-12 and are paraphrased with the link.
"""
from __future__ import annotations

import datetime
import html
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from render import buy_block, render  # noqa: E402

_RUN = json.loads((Path(__file__).resolve().parent.parent.parent / "data" / "ttfb-run.json").read_text())


def _when() -> str:
    d = datetime.date.fromisoformat(_RUN["date"])
    return f"{d.day} {d.strftime('%B %Y')}"


def ttfb() -> Path:
    esc = html.escape
    slow, cached, mod = (_RUN[k]["finding"] for k in ("slow", "cached", "moderate"))
    body = f"""
<p class="lede">Time to first byte is how long your server takes to start sending a page. If it is
slow, nothing you do to the page itself can make the page fast. Fix it in this order: cache whole
pages, put a CDN in front of the site, speed up whatever is slow behind the cache, and move off the
host if the host is the cause. Measure after each step, so you know which one paid.</p>

<h2>What good looks like</h2>

<p>I read web.dev's guide to the metric on {_when()}:
<a href="https://web.dev/articles/ttfb">Time to First Byte (TTFB)</a>. It calls a good value eight
tenths of a second or less, and a poor one anything over one and eight tenths. It also says TTFB is
not a Core Web Vital, so a site does not strictly have to meet the good bound as long as the slow
start is not stopping it scoring well on the metrics that matter. The reason to care is that the
server's reply comes before everything else: no first paint and no largest paint can happen until
it starts.</p>

<h2>What Docket reports</h2>

<p>Docket takes the median time to first byte across the pages it crawled, and needs at least three
pages to do it. It reports one of three things.</p>

<ul>
<li><strong>Above target.</strong> The median is over eight tenths of a second.</li>
<li><strong>Slow across the site.</strong> The median is over one and eight tenths, reported as high
severity.</li>
<li><strong>Slow the first time, fast when asked again.</strong> Docket is usually the first visitor to
a page, so it sees a cold cache. It asks again for some of the slowest, and if the second answer is fast
it says so: a cache in front of a slow server.</li>
</ul>

<h2>The fix, in order</h2>

<ol>
<li><strong>Cache whole pages.</strong> For a page that is the same for every visitor, the server should
not build it again each time. Full-page caching is the biggest single change on most sites, and on a CMS
it is often a plugin or a setting.</li>
<li><strong>Put a CDN in front.</strong> A CDN answers from a server near the visitor and keeps a copy, so
most requests never reach yours.</li>
<li><strong>Find what is slow behind the cache.</strong> The usual cause is a slow database query on a
main template, or a plugin that does work on every request. A cache hides this for repeat visits and not
for the first visitor after it expires, or for a crawler working through pages nobody has asked for
lately.</li>
<li><strong>Move off the host if the host is the bottleneck.</strong> Shared hosting that is slow at
every hour and for every page is a limit no setting will lift.</li>
</ol>

<p>Redirects add their own wait before the page is even asked for. They are covered in
<a href="/how-to/fix-redirect-problems/">how to fix redirect problems</a>. To see where the time goes on
one page, open your browser's network panel, load the page, click the first request and look at its timing:
the line called waiting for server response is the time to first byte. The command-line tool curl can print it
too: its write-out option has a variable called <code>time_starttransfer</code>.</p>

<p>Load the page a few times. If the first load is slow and the next ones are fast, you have the cache case
below. If every load is slow, the server is slow on every request.</p>

<h2>A real before and after</h2>

<p>I wrote a small fixture site for this page: six pages of a typewriter repair workshop, served by a local
server that waits a set time before it sends each page. I audited it with Docket on {_when()} four times,
changing only the wait. This shows how Docket reads response time. It is not a recipe for speeding up a real
server.</p>

<ul>
<li><strong>Every request waits more than two seconds.</strong> Docket reported:
<em>{esc(slow["title"])}</em></li>
<li><strong>The first request for each page waits that long, and later ones answer at once.</strong> That
is a cache in front of a slow server. Docket reported: <em>{esc(cached["title"])}</em></li>
<li><strong>Every request waits about a second.</strong> Docket reported:
<em>{esc(mod["title"])}</em></li>
<li><strong>No wait.</strong> Docket reported nothing.</li>
</ul>

<p>For the first, its fix was: <em>{esc(slow["fix"])}</em> For the cache case it was:
<em>{esc(cached["fix"])}</em></p>

<h2>What Docket cannot tell you</h2>

<ul>
<li><strong>Why the server is slow.</strong> It measures the wait and not what the server was doing. The
fixes above are the usual causes in order of payoff, and the order is a guide.</li>
<li><strong>How slow it is for your visitors.</strong> It measures from the machine it runs on, so a
server far from that machine looks slower here than it does to someone next door. Field data from
PageSpeed Insights or Search Console is the real picture for your own visitors.</li>
<li><strong>Whether it matters for your site.</strong> TTFB is not a Core Web Vital. A slow reply is worth
fixing because it is the floor under every other loading number, not because the number itself is scored.</li>
</ul>

<h2>Where to start</h2>

<p>Time your home page and two others, a few times each. If the first run is slow and the
rest are fast, warm the cache after you publish and look at what is slow on a cold page. If they are all slow,
turn on full-page caching first. Slow servers also cost you in the loading findings that come after:
<a href="/how-to/fix-render-blocking-resources/">files that block the first paint</a> are the next place to
look. What Docket adds is the same measurement across every page, ranked with the rest; see how that compares
with <a href="/vs/">other audit tools</a>.</p>

{buy_block("howto-ttfb", big=False, try_app="howto-ttfb-try-free")}
"""
    return render(
        cat="how-to", slug="reduce-server-response-time",
        title="How to reduce server response time (TTFB)",
        desc=("Time to first byte is the floor under every loading number. Cache pages, add a CDN, find what "
              "is slow behind the cache, and what a crawler can and cannot tell you."),
        h1="How to reduce server response time (TTFB)",
        crumb='<a href="/">Docket</a> / <a href="/how-to/">Fix it</a> / server response time',
        body=body,
        faq=[
            ("What is a good TTFB?",
             "web.dev calls eight tenths of a second or less good and anything over one and eight tenths poor."),
            ("Is TTFB a Core Web Vital?",
             "No. web.dev says it is not, so meeting the good bound is not strictly required, but a slow reply "
             "sits under every other loading metric."),
            ("What is the quickest way to reduce it?",
             "Cache whole pages. For pages that are the same for every visitor, the server should not rebuild "
             "them on each request."),
            ("Why does Docket report that pages are slow the first time?",
             "Docket is usually the first visitor to a page, so it sees a cold cache. It asks again for some of "
             "the slowest, and if the second answer is fast it reports a cache in front of a slow server."),
        ],
    )


if __name__ == "__main__":
    print(ttfb())
