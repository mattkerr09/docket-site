#!/usr/bin/env python3
"""How to fix compression and caching headers — Docket's `perf.compression`.

Sourced from `perf.compression` in
`backend/seo_engine/checks/performance.py`, the module docstring above it,
`Page.html_bytes` and `Page.ok` in `models.py`, `AuditContext.ok_pages` in
`registry.py`, `Fetcher.get` and `_decompress` in `fetcher.py` — which is where
the request headers are actually set — and the tests beside them:

  * tests/test_checks.py::test_uncompressed_pages_flagged
  * tests/test_checks.py::test_compressed_pages_not_flagged
  * tests/test_an_absence_is_claimed_only_where_it_can_be_seen.py

⚠️ FOUR PLACES THE CODE IS NARROWER THAN "COMPRESSION AND CACHING HEADERS".

1. Docket's own request advertises `gzip, deflate` and never `br`. The
   `_decompress` docstring says so in terms: "Docket never advertises `br`, so
   brotli cannot arrive from a spec-abiding server." A Brotli-only origin that
   obeys RFC 9110 will therefore hand our crawler an uncompressed document, and
   `perf.no_compression` will fire on a site that compresses correctly for
   every real browser. This is the page's lead, not a footnote.
2. Compression is tested as the PRESENCE of a `content-encoding` header, never
   its value. No algorithm is checked and no saving is measured.
3. Caching is tested as the presence of any ONE of `cache-control`, `etag` or
   `last-modified`, never the value. `Cache-Control: no-store` satisfies it.
4. `perf.no_cache_headers` is a site-level finding gated on a majority of the
   OK pages, not a per-page count like its sibling. A minority of bare pages
   produces no finding at all.

The size floor is read off decompressed HTML — `Page.html_bytes` is documented
as "Raw HTML byte length before any transfer encoding" and is assigned
`len(resp.body)` after `_decompress` has run. It is not a wire size.

No typed figures and no typed dates in prose: the threshold and the severities
are shown inside <code>, which `verify_numbers.py` masks, the specification
pointers and the reading date are interpolated from the constants below, and
the counted lists are measured with len(). Config snippets are brace-free so
nothing in the rendered page can be read as an unrendered placeholder.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from render import render  # noqa: E402

#: The two specifications, read at their canonical homes on the date below.
#: Section pointers live here rather than in sentences so a re-reading is one
#: edit and no sentence can drift away from what was actually read.
SEMANTICS_URL = "https://www.rfc-editor.org/rfc/rfc9110.html"
SEMANTICS = "RFC 9110"
S_CONTENT_ENCODING = "section 8.4"
S_ACCEPT_ENCODING = "section 12.5.3"
S_LAST_MODIFIED = "section 8.8.2"
S_ETAG = "section 8.8.3"

CACHING_URL = "https://www.rfc-editor.org/rfc/rfc9111.html"
CACHING = "RFC 9111"
S_STORING = "section 3"
S_VALIDATION = "section 4.3"
S_CACHE_CONTROL = "section 5.2"

NGINX_URL = "https://nginx.org/en/docs/http/ngx_http_gzip_module.html"
APACHE_URL = "https://httpd.apache.org/docs/2.4/mod/mod_deflate.html"
READ_ON = "15 September 2026"

#: The findings this check can emit. Counted, never typed — see PAGE_ANATOMY.
FINDINGS = ("perf.no_compression", "perf.no_cache_headers")

#: The sibling checks in the same lane. This page is about neither.
NEIGHBOURS = ("perf.page_weight", "perf.render_blocking", "perf.ttfb",
              "perf.modern_images")

_WORDS = {1: "one", 2: "two", 3: "three", 4: "four", 5: "five", 6: "six"}


def _n(count: int) -> str:
    """Spell a small count that was measured rather than remembered."""
    return _WORDS[count]


def compression_and_caching() -> Path:
    body = f"""
<p class="lede">Your audit came back with a heading reading "Compression and caching headers"
and a list of URLs under it, and the two halves of that heading sound like the same afternoon of
server work. They are not. One is usually a single line of configuration and a real saving; the
other is a smaller matter than its name suggests — and on some hosts the first is reported
against a site already doing it correctly.</p>

<p>Docket's <code>perf.compression</code> check emits {_n(len(FINDINGS))} findings, under
{_n(len(FINDINGS))} ids, at {_n(len(FINDINGS))} very different severities:</p>

<pre><code>high   perf.no_compression     N pages are served without compression
low    perf.no_cache_headers   Pages are served with no caching headers</code></pre>

<p>The gap between <code>high</code> and <code>low</code> is most of the answer. The check also
grades its own workload, and grades neither as an afternoon: the compression fix is filed as
<code>trivial</code>, which the engine defines as "edit one tag / one line of config, minutes",
and the caching fix as <code>small</code>, "a template change, under an hour".</p>

<h2>What this cannot tell you, first</h2>

<p><strong>Docket reads the headers on the responses it was given. It does not measure how fast
anything felt.</strong> There is no browser, no paint, no device and no network but ours. A
finding here is a fact about the response that arrived at our crawler, and most of this page is
about the distance between that and your site.</p>

<p><strong>It cannot measure Core Web Vitals, and nothing that runs on one machine can.</strong>
Largest Contentful Paint, Interaction to Next Paint and Cumulative Layout Shift come from real
people on real connections. The check module says so in its own opening comment — that it
measures the network and the document, not a rendered browser, and that "a number invented from
static analysis would be worse than no number". Confirm the field values in Search Console.</p>

<p><strong>It does not measure how much compression saved you</strong>, and
<strong>it only looked at HTML.</strong> Nothing is compressed twice and nothing is compared;
the check asks whether a <code>Content-Encoding</code> header was present and stops. Your
stylesheets, scripts and JSON endpoints were never fetched for it, so it has no opinion about
those — even though its own fix text asks you to turn compression on for them.</p>

<h2>The false positive you should check before you change anything</h2>

<p>This one matters, and it is ours rather than yours. Docket's crawler sends <code>Accept-Encoding: gzip, deflate</code>. It does not advertise
Brotli, because there is no Brotli decoder in the Python standard library and the engine is kept
dependency-free. The fetcher says so in its own comment: Docket never advertises
<code>br</code>, so Brotli cannot arrive from a specification-abiding server.</p>

<p>Now read that against the specification. Under
<a href="{SEMANTICS_URL}#section-12.5.3">{SEMANTICS} {S_ACCEPT_ENCODING}</a>, the
<code>Accept-Encoding</code> request header is how a client states which content codings it
will accept, and a server that respects it will not send one that was not offered. So an origin
or CDN configured to serve Brotli and nothing else, behaving correctly, answers our crawler with
an uncompressed document and no <code>Content-Encoding</code> header. Docket then reports
<code>perf.no_compression</code> at <code>high</code> against a site whose real visitors have
had compressed HTML all along.</p>

<p>Check before you touch a configuration file, with the request a browser actually makes:</p>

<pre><code>curl -sI -H 'Accept-Encoding: gzip, deflate, br' https://example.com/ | grep -i content-encoding</code></pre>

<p>If that prints <code>content-encoding: br</code> and the same request without
<code>br</code> prints nothing, the finding is about our request rather than your server and
there is nothing to fix. The general form holds in both directions: a managed host or CDN can
compress for real visitors while answering an unfamiliar client differently, and the response we
got is the only thing this check ever saw.</p>

<h2>What the check actually computes</h2>

<p><strong>Compression.</strong> For every page that returned a success status and parsed as
HTML, Docket asks two questions: is the HTML document bigger than the floor, and is a
<code>Content-Encoding</code> header present. That is the whole test:</p>

<pre><code>uncompressed = [
    p for p in ctx.ok_pages
    if p.html_bytes &gt; 20_000
    and not p.headers.get("content-encoding")
]</code></pre>

<p>Two things follow that people get wrong. First, <em>any</em> value satisfies it. The check
never reads what the header says, so it cannot distinguish gzip from Brotli from
<code>identity</code>. Second, the size floor is measured on the <em>decompressed</em> document:
<code>html_bytes</code> is documented in the model as the raw HTML byte length before any
transfer encoding, and is assigned after the fetcher has unpacked the body. It is the size of
your markup, not of what crossed the wire. A page under the floor is never reported however it
is served, because the saving on a small document does not justify a finding.</p>

<p><strong>Caching.</strong> Here the shape is different, and this is the part most likely to
surprise you. A page counts as having no caching headers only when <em>all</em> of
<code>Cache-Control</code>, <code>ETag</code> and <code>Last-Modified</code> are absent. Any one
of the three is enough to clear it. And the finding is then gated on the site rather than the
page: it is only emitted when more than half of the crawled OK pages are bare. If a minority of
your pages have no caching headers, this check says nothing at all — and its title, "Pages are
served with no caching headers", is deliberately a statement about the site rather than a
count.</p>

<p>As with compression, presence is the test and the value is never read.
<code>Cache-Control: no-store</code> clears this check completely, because the check is asking
whether you said anything about caching, not whether it was wise.</p>

<h2>Turning compression on</h2>

<p>On nginx, the <a href="{NGINX_URL}">gzip module documentation</a> is short and worth reading
in full. The directive defaults to off, and HTML is a special case: the documentation says
plainly that responses with the <code>text/html</code> type are always compressed, so
<code>text/html</code> does not belong in the type list.</p>

<pre><code>gzip on;
gzip_types text/css application/javascript application/json image/svg+xml;
gzip_min_length 256;</code></pre>

<p>On Apache, <a href="{APACHE_URL}">mod_deflate</a> does the same job from the vhost or
<code>.htaccess</code>:</p>

<pre><code>AddOutputFilterByType DEFLATE text/html text/css application/javascript application/json image/svg+xml</code></pre>

<p>If you are on a managed platform and control neither file — the common case, and the reason
this page exists — the setting is in your host's dashboard rather than your repository. On a CDN
it is usually one toggle applied at the edge, and the CDN compresses on the way out whether or
not your origin did. That is why the fix is graded <code>trivial</code>: it is not a deploy.</p>

<h2>Caching headers, and what to actually set</h2>

<p>The reason this one is <code>low</code> rather than <code>high</code> is that a missing
caching header costs you nothing on a first visit, which is most search traffic. It costs you on
repeat visits and on re-crawls.</p>

<p><a href="{CACHING_URL}#section-3">{CACHING} {S_STORING}</a> sets out when a cache may store a
response at all, and <a href="{CACHING_URL}#section-5.2">{CACHING} {S_CACHE_CONTROL}</a> defines
<code>Cache-Control</code> as the field carrying directives to caches along the
request/response chain. The other two headers the check looks for are validators rather than
policy: <a href="{SEMANTICS_URL}#section-8.8.3">{SEMANTICS} {S_ETAG}</a> defines
<code>ETag</code>, <a href="{SEMANTICS_URL}#section-8.8.2">{SEMANTICS} {S_LAST_MODIFIED}</a>
defines <code>Last-Modified</code>, and either lets a client ask "has this changed" and be told
no — the conditional-request mechanism in
<a href="{CACHING_URL}#section-4.3">{CACHING} {S_VALIDATION}</a>. That is the part crawlers use,
and why a validator alone satisfies the check.</p>

<p>For HTML that changes when you publish, the check's own suggested value is conservative and
sensible:</p>

<pre><code>Cache-Control: public, max-age=0, must-revalidate</code></pre>

<p>That does not mean "do not cache". It means the cache may keep a copy and must check with
you before reusing it — which, with an <code>ETag</code> alongside it, turns most repeat fetches
into a short response with no body. For fingerprinted assets, a long <code>max-age</code> with
<code>immutable</code> is the usual pairing. Those are not what this check looked at, but they
are where the saving is.</p>

<h2>What this check is not</h2>

<p>Header findings attract everything else that is slow, so the boundaries are worth stating.
Docket's speed lane runs this check alongside separate ones with their own ids, their own
thresholds and their own findings:</p>

<ul>
<li><code>{NEIGHBOURS[0]}</code> — the size of the HTML document itself, decompressed. Same
<code>html_bytes</code> field, different question: compression is about how it was sent, weight
is about how much of it there is.</li>
<li><code>{NEIGHBOURS[1]}</code> — stylesheets and scripts that block the first paint. Counted
from the markup, and reported per page.</li>
<li><code>{NEIGHBOURS[2]}</code> — time to first byte, taken from the fetch and reported against
the median across the site.</li>
<li><code>{NEIGHBOURS[3]}</code> — images still served as JPEG or PNG where a modern format
would be smaller.</li>
</ul>

<p>None of those is fixed by a compression header and none of them fixes one. The full list of
what the engine looks at, lane by lane, is on
<a href="/learn/what-docket-checks/">what Docket checks</a>. The lane's other markup-level
finding is written up at <a href="/how-to/fix-layout-shift/">how to fix layout shift</a>, which
carries the same limit from the other side: Docket infers layout-shift risk from markup and
cannot measure the metric.</p>

<p>The closest relative outside this lane is response headers of a different kind.
<a href="/how-to/fix-missing-security-headers/">Missing security headers</a> are set in the same
file, at the same edge, by the same person — and this site fails two of those checks itself,
because its host cannot set response headers at all. If you are opening that file anyway, do
both.</p>

<h2>So which is worth an afternoon</h2>

<p>Neither, on the check's own grading, and that is the useful answer. Confirm the compression
finding with the <code>curl</code> above, because a Brotli-only host produces it falsely. If it
holds, turn compression on: one line, and the largest single win this check can point at. Then
set a <code>Cache-Control</code> value and make sure a validator is present — worth doing, not
urgent. Spend the rest of the afternoon on
<a href="/how-to/">something else on the list</a>.</p>

<p>Every external reading on this page was taken on {READ_ON}:
<a href="{SEMANTICS_URL}">{SEMANTICS}, HTTP Semantics</a> and
<a href="{CACHING_URL}">{CACHING}, HTTP Caching</a> at rfc-editor.org, the
<a href="{NGINX_URL}">gzip module</a> at nginx.org, and
<a href="{APACHE_URL}">mod_deflate</a> at httpd.apache.org.</p>

<p><a class="btn" href="/download/">Download Docket</a></p>
"""
    return render(
        cat="how-to", slug="fix-compression-and-caching",
        title="Fix compression and caching headers",
        desc=("What Docket's perf.compression check reads, the Brotli quirk "
              "that makes it report a site that already compresses, and which "
              "half is worth your time."),
        h1="How to fix compression and caching headers",
        crumb='<a href="/">Docket</a> / <a href="/how-to/">Fix it</a> / compression and caching',
        body=body,
        faq=[
            ("Does Docket check for Brotli?",
             "No, and this is the check's most important limit. Docket's crawler sends "
             "Accept-Encoding: gzip, deflate and never advertises br, because there is no "
             "Brotli decoder in the Python standard library. A server that only offers "
             "Brotli and obeys RFC 9110 will send our crawler an uncompressed document, so "
             "perf.no_compression can fire on a site that compresses perfectly for real "
             "browsers. Confirm with curl -sI -H 'Accept-Encoding: gzip, deflate, br' "
             "before changing anything."),
            ("What counts as compressed?",
             "The presence of a Content-Encoding header on the response, whatever its "
             "value. The check never reads the algorithm, never compares sizes and makes no "
             "claim about how much was saved. It is a presence test, not a measurement."),
            ("Why does the compression finding only cover some pages?",
             "There is a size floor, and it is measured on the decompressed HTML rather "
             "than on what crossed the wire. Pages whose markup is smaller than the floor "
             "are never reported however they are served, because the saving on a small "
             "document does not justify a finding."),
            ("What counts as a caching header?",
             "Any one of Cache-Control, ETag or Last-Modified. A page only counts as bare "
             "when all three are absent, and the finding is only raised when more than half "
             "the crawled pages are bare — so it is a statement about the site, not a count "
             "of pages. The value is never read, so Cache-Control: no-store clears the "
             "check as thoroughly as a good policy would."),
            ("Will fixing this improve my Core Web Vitals score?",
             "It may improve the experience, but Docket cannot tell you, and neither can "
             "any tool running on one machine. LCP, INP and CLS come from real visitors on "
             "real connections. Docket measures the causes; the field values belong in "
             "Search Console."),
            ("Does compression affect rankings directly?",
             "Not as a header. Nothing in the check claims a ranking effect and this page "
             "will not invent one. Smaller responses arrive faster, which is worth having "
             "on its own terms."),
        ],
    )


BUILDERS = [compression_and_caching]


def build_all() -> list[Path]:
    return [b() for b in BUILDERS]


if __name__ == "__main__":
    for p in build_all():
        print(p)
