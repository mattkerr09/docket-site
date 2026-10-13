#!/usr/bin/env python3
"""How to fix a favicon that is not showing in Google search results.

Sourced from Docket's `social.no_favicon` and the probe that decides it
(backend/seo_engine/crawler.py: open the home page, take the first two <link> tags whose rel
contains "icon", fetch each, and accept one that answers, is not HTML and is not empty; otherwise
try /favicon.ico the same way).

The four-way before and after is from data/favicon-run.json, written by
docket-app/scripts/measure_favicon_fixture.py: a real Docket audit of a small fixture site of ours.
Nothing about a third-party site. Google's favicon guidelines were read at their own page on
2026-10-13 and are paraphrased with the link. Sizes are written as words.
"""
from __future__ import annotations

import datetime
import html
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from render import buy_block, render  # noqa: E402

_RUN = json.loads((Path(__file__).resolve().parent.parent.parent / "data" / "favicon-run.json").read_text())


def _when() -> str:
    d = datetime.date.fromisoformat(_RUN["date"])
    return f"{d.day} {d.strftime('%B %Y')}"


def favicon() -> Path:
    esc = html.escape
    none = _RUN["none"]["finding"]
    body = f"""
<p class="lede">If your favicon is not showing in Google's search results, check four things in this
order. The home page has a <code>&lt;link&gt;</code> tag pointing at it. The file at that address loads.
Googlebot can crawl the home page and Googlebot-Image can crawl the file. And the file is a square. Then wait,
because Google takes days to weeks to pick up a change, and it does not promise to show one.</p>

<h2>What Google says</h2>

<p>I read Google's favicon guidance on {_when()}:
<a href="https://developers.google.com/search/docs/appearance/favicon-in-search">Define a favicon to show in
search results</a>. To be eligible, add a <code>&lt;link&gt;</code> tag to the head of your home page. Google reads
the <code>rel</code> value, which can be <code>icon</code>, the older <code>shortcut icon</code>,
<code>apple-touch-icon</code> or <code>apple-touch-icon-precomposed</code>, and the <code>href</code>, which can
be a relative or a full address and does not have to be on your own host.</p>

<p>Its guidelines, in short:</p>

<ul>
<li>Google supports one favicon per hostname, set on that hostname's home page. A subdirectory such as
<code>/news</code> cannot have its own.</li>
<li>Googlebot-Image must be able to crawl the favicon file, and Googlebot must be able to crawl the home page.
Neither can be blocked.</li>
<li>The favicon must be square and at least eight pixels each way. Google recommends larger than forty-eight
pixels so it looks right on different surfaces.</li>
<li>Supported formats are BMP, GIF, ICO, PNG, JPEG, PPM and TIFF.</li>
<li>The address should be stable, and the image should represent your brand.</li>
<li>A favicon is not guaranteed to appear even when every guideline is met.</li>
</ul>

<p>After a change, Google says recrawling can take anywhere from several days to several weeks. You can ask for the
home page to be indexed again with the URL Inspection tool in Search Console.</p>

<h2>What Docket checks</h2>

<p>Docket opens your home page, takes the first two <code>&lt;link&gt;</code> tags whose <code>rel</code> contains the
word icon, and fetches each one. A file counts if the server answers, the answer is not an HTML page, and it is not
empty. If neither works, it tries <code>/favicon.ico</code> the same way. If nothing loads it reports
<em>{esc(none["title"])}</em>, at low severity.</p>

<p>Two details matter. A tag that points at a missing file does not count: a declared icon that returns a not-found
page is reported as no favicon, because that is what a visitor and a search engine get. And a site that has only a
file at <code>/favicon.ico</code> and no tag passes Docket's check, although Google's page asks for the tag on the
home page. Add the tag.</p>

<h2>The fix</h2>

<pre><code>{esc(none["snippet"])}</code></pre>

<p>Put those lines in the head of your home page, serve the files at those addresses, and open each address in a browser
to be sure it loads. If your site is on a CMS, the favicon is usually a setting under the site's appearance or
identity options, and it writes the tag for you. Do not let a robots.txt rule block the file.</p>

<h2>A real before and after</h2>

<p>I wrote a small fixture site for this page: three pages of a typewriter repair workshop. I audited it with Docket
on {_when()} four times, changing only the favicon. The pages are ours; nothing here is measured on anyone else's
site.</p>

<ul>
<li><strong>No tag and no file.</strong> Docket reported: <em>{esc(none["title"])}</em></li>
<li><strong>A tag pointing at a file that does not exist.</strong> Docket reported the same finding.</li>
<li><strong>The tag, and the file is there.</strong> Docket reported nothing.</li>
<li><strong>No tag, but a file at <code>/favicon.ico</code>.</strong> Docket reported nothing, which is the case
above where Google's guidance asks for more.</li>
</ul>

<p>The tag I used was <code>{esc(_RUN["link"])}</code>. Its fix, for the first two cases, was:
<em>{esc(none["fix"])}</em></p>

<h2>What Docket cannot tell you</h2>

<ul>
<li><strong>Whether the file meets the size and shape rules.</strong> It checks that a file loads, not that it is
square or large enough, and it does not read the format.</li>
<li><strong>Whether Googlebot-Image is blocked.</strong> It does not test that bot against your robots.txt. The
<a href="/tools/robots-txt-tester/">robots.txt tester</a> will show the rules for a given address.</li>
<li><strong>Whether Google shows it.</strong> That is Google's decision, made on its own schedule, and it does not
promise to show one at all.</li>
</ul>

<h2>Where to start</h2>

<p>Open your home page's source and look for the tag, then open the address it names. Most missing favicons are one of
those two steps. The favicon belongs with the other things that shape how your site looks outside its own pages, such
as <a href="/how-to/fix-missing-open-graph-tags/">the preview a shared link shows</a>. What Docket adds is the same check
alongside every other, ranked; see how that compares with <a href="/vs/">other audit tools</a>.</p>

{buy_block("howto-favicon", big=False, try_app="howto-favicon-try-free")}
"""
    return render(
        cat="how-to", slug="fix-favicon-not-showing-in-search",
        title="How to fix a favicon that is not showing in Google search",
        desc=("Add the link tag to your home page, make sure the file loads and Google can crawl it, and wait. "
              "What Google requires and what Docket checks."),
        h1="How to fix a favicon not showing in search results",
        crumb='<a href="/">Docket</a> / <a href="/how-to/">Fix it</a> / favicon',
        body=body,
        faq=[
            ("Why is my favicon not showing in Google search?",
             "Usually the home page has no link tag for it, the file does not load, Googlebot or Googlebot-Image is "
             "blocked, or Google has not recrawled yet. Google also does not guarantee to show one."),
            ("How long does a favicon take to appear?",
             "Google says recrawling can take anywhere from several days to several weeks. The URL Inspection tool can "
             "request indexing of the home page."),
            ("What size and format should a favicon be?",
             "Square, at least eight pixels each way, and Google recommends larger than forty-eight pixels. It supports "
             "BMP, GIF, ICO, PNG, JPEG, PPM and TIFF."),
            ("Does a subdirectory get its own favicon?",
             "No. Google supports one favicon per hostname, set on that hostname's home page."),
        ],
    )


if __name__ == "__main__":
    print(favicon())
