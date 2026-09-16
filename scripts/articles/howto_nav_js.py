#!/usr/bin/env python3
"""Navigation that needs JavaScript — what `links.nav_not_in_html` measures.

Source of record for everything said here about the check:

  * `backend/seo_engine/checks/links.py`, `links.nav_not_in_html` — the
    finding, its severity, its effort, its fix text and its snippet.
  * `backend/seo_engine/crawler.py`, `CrawlResult.nav_in_html` and
    `CrawlResult.html_link_coverage` — the gate and the threshold. The check
    itself owns neither.
  * `backend/seo_engine/crawler.py`, `Config.render_discovery` and
    `Crawler._links_from_browser` — why a client-rendered shell often does
    NOT trigger this check.
  * `backend/seo_engine/renderer.py` — the WebKit helper, and what it costs.
  * `tests/test_crawl_quality.py`, `test_nav_built_by_javascript_invalidates_
    the_link_graph` and `test_a_genuinely_tiny_site_is_not_called_javascript_
    driven` — the two sides of the gate.

NO FIGURE IS TYPED INTO THE PROSE. There is no dataset for this check, so the
page carries none: thresholds appear inside <code>, quoted from the source,
where they are a literal being quoted rather than a measurement being claimed.

The site the check was written against is deliberately not named. See
`scripts/verify_no_named_third_parties.py`.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from render import render  # noqa: E402

#: The day Google's documentation was read for this page.
CHECKED_ON = "2026-09-15"
CHECKED_ON_HUMAN = "15 September 2026"

#: (what was read, where it was read). Nothing outside this list is stated on
#: the page as a fact about how Google behaves.
VERIFIED: list[tuple[str, str]] = [
    ('"Google can only discover your links if they are &lt;a&gt; HTML elements '
     'with an href attribute", and that Googlebot "queues pages for both '
     'crawling and rendering", with rendering happening after the crawl',
     "https://developers.google.com/search/docs/crawling-indexing/javascript/"
     "javascript-seo-basics"),
    ('"Google can only crawl your link if it\'s an &lt;a&gt; HTML element (also '
     'known as anchor element) with an href attribute", and that Google '
     '"can\'t reliably extract URLs from &lt;a&gt; elements that don\'t have an '
     'href attribute or other tags that perform as links because of script '
     'events" — the examples given as not recommended being an anchor with no '
     'href, a span carrying an href, and an anchor whose destination is in an '
     'onclick handler',
     "https://developers.google.com/search/docs/crawling-indexing/links-crawlable"),
]


def _verified_note() -> str:
    items = "; ".join(
        f'{what} (<a href="{url}" rel="nofollow noopener">source</a>)'
        for what, url in VERIFIED
    )
    return f"""
<p class="verified-note"><strong>Read from Google's own documentation on
{CHECKED_ON_HUMAN}.</strong> {items}. If Google has changed any of this since
that date, <a href="/about/">tell us</a> and the page will be corrected rather
than quietly left standing.</p>"""


def fix_navigation_that_needs_javascript() -> Path:
    body = f"""
<p class="lede">Your menu is built by JavaScript, an audit has told you that is a problem,
and you want to know whether it actually is. The answer has two halves: Google will usually
follow the links once it renders the page, and the tool that flagged you is measuring
something narrower than "your menu". Here is what was measured, and what it does and does not
license you to conclude.</p>

<h2>The short answer</h2>

<p>If your navigation ends up as real anchor elements with <code>href</code> attributes after
JavaScript runs, Google can follow them — but only after it renders, and rendering is a
separate, later stage. If your navigation is made of clickable divs, spans, or router
components that never emit an <code>href</code>, it is not a set of links to Google at any
stage, rendered or not. A crawler that does not render at all sees both cases as the same
thing: nothing.</p>

<p>Docket's check cannot tell those two cases apart for you. What it can tell you is whether
the HTML your server sent contained enough internal links to describe a site — a smaller
question with a much firmer answer.</p>

<h2>What <code>links.nav_not_in_html</code> actually measures</h2>

<p>The check is registered in the links lane under the name
<code>Navigation reachable without JavaScript</code>, and that title is broader than the
measurement underneath it. Read the source and the measurement is this: for every crawled page
that returned OK and declared an HTML content type, Docket counts the distinct internal
destinations reachable from an <code>&lt;a href&gt;</code> in the delivered markup, then
averages that across those pages.</p>

<p>It does not look at <code>&lt;nav&gt;</code> elements, a menu, a header, or anything a
designer would call navigation. It counts internal anchors, deduplicated per page, and takes
the mean. A page linking the same destination repeatedly contributes one.</p>

<p>Two conditions gate it, and both live on the crawl result rather than in the check:</p>

<ul>
<li>The crawl must have read at least <code>3</code> OK HTML pages. Below that,
<code>nav_in_html</code> returns true regardless — the source comment says
<code>Too small to tell a JS-nav site from a genuinely tiny one</code>, and a
test named <code>test_a_genuinely_tiny_site_is_not_called_javascript_driven</code>
holds that line.</li>
<li>The average must fall below <code>html_link_coverage &gt;= 2.0</code>. The comment
explaining the number is worth quoting rather than paraphrasing:
<code>A site whose pages average fewer than two internal links is not a site with sparse
navigation; it is a site whose navigation is absent from the HTML. Real sites carry a nav, a
footer and body links.</code></li>
</ul>

<p>When it fires, it fires once for the whole site, not per page. Severity is HIGH, the effort
estimate is LARGE, and the finding's own headline takes one of two forms: either
<code>None of your pages contain a single internal link in their HTML</code>, or a sentence
that states the measured average and ends
<code>internal links in the HTML — the navigation is built by JavaScript</code>. The URLs
attached to the finding are the pages nothing in the HTML points at, which is the practical
cost rather than the abstract one.</p>

<p>Its fix text, verbatim:</p>

<blockquote><p>Render the navigation server-side, or output real &lt;a href&gt; elements in the
initial HTML and let JavaScript enhance them. A menu built from &lt;div onclick&gt; or injected
after load is not a link. Test it the way Docket did: fetch the page with JavaScript disabled
and look for &lt;a href&gt; in the source.</p></blockquote>

<p>And the shape it asks for, which is the snippet the finding ships with:</p>

<pre><code>&lt;nav&gt;&lt;a href="/services/"&gt;Services&lt;/a&gt; &lt;a href="/team/"&gt;Team&lt;/a&gt;&lt;/nav&gt;</code></pre>

<h2>The case it was written for, which is not the one you expect</h2>

<p>The obvious client-rendered site — a mount point, a script tag, no text — is not what this
check was built to catch. It was built for a law firm's site that served close to a thousand
words of real, server-rendered copy per page and returned a homepage containing zero internal
links. The prose was in the HTML. The navigation was assembled in the browser.</p>

<p>That shape defeats any audit reasoning from text volume, because the text is all there. It
is also invisible to a human reviewer, who opens the page in a browser that has already run
the JavaScript and sees a perfectly ordinary menu. The consequence recorded in
<code>CrawlResult.nav_in_html</code> is a cascade of confident falsehoods: pages reported as
orphans that nothing links to, the same pages reported as weakly linked, and a click-depth
model built on a link graph that was never the site's. So when <code>nav_in_html</code> is
false, Docket withdraws its own orphan and click-depth claims rather than publishing them —
never conclude absence from a view that could not have shown presence.</p>

<h2>What is not measured, stated plainly</h2>

<p>Docket does not crawl with a browser. The crawl is an HTTP fetch, and the links this check
counts are the ones in the bytes your server returned. A WebKit helper exists and is used in
two narrow places: a small capped sample of every audit is rendered where the helper is
present, and during discovery a page whose raw HTML yielded no links <em>and</em> which looks
like a JavaScript shell is re-read in a browser so its links can be recovered. That helper is
built against the macOS system framework and is simply absent elsewhere, in which case link
recovery degrades to finding nothing.</p>

<p>This has a consequence that cuts against the check's own name, and you should know it
before you act on a finding: <strong>a textbook single-page app often will not trigger this
check at all</strong>, because its pages announce themselves as shells, get rendered during
discovery, and have their real links folded back in. The site that does trigger it is the one
whose copy is served and whose links are not — the shell heuristic never fires, so nothing is
re-read, and the average stays where the bytes left it.</p>

<p>And the larger limit: <strong>Docket cannot tell you what Google did.</strong> It has no
view of Google's render queue, no record of which of your URLs were rendered or when, and no
way to distinguish "Google could reach this" from "Google fetched this". Any tool that implies
otherwise is showing you a model and calling it a measurement. What this check gives you is a
fact about your own server's output, which is the part you control. If you want a record of
what actually fetched what, that lives in your server logs, not in a crawler.</p>

<h2>What Google's documentation says</h2>

<p>Google's own guidance is narrower than the folklore around it. The requirement is stated as
a property of markup, not of frameworks: a link is an anchor element with an
<code>href</code>. Injecting links with JavaScript is explicitly allowed provided the result is
that shape. The documentation's own examples of markup it does not recommend are an anchor
with no <code>href</code>, a <code>span</code> carrying an <code>href</code>, and an anchor
whose destination lives in an <code>onclick</code> handler.</p>

<p>Google also describes crawling and rendering as separate queues, with rendering after the
crawl. That ordering is the whole reason this finding carries a HIGH severity rather than a
shrug: links that exist only after rendering are links that arrive late, and on a site where
every link is in that category, discovery of new pages waits on a stage nobody outside Google
can schedule. The crawlers behind the AI assistants are a harder case again, because most do
not render at any point.
<a href="/learn/javascript-rendering/">How rendering works, and what it costs to run</a> covers
that trade in detail — it executes third-party scripts and is an order of magnitude slower than
fetching, which is why the sample is capped.</p>

{_verified_note()}

<h2>Check it yourself, without a tool</h2>

<p>The check's own fix text tells you how, and it takes one command. Fetch the page the way a
non-rendering crawler does and look at what came back:</p>

<pre><code>curl -sS https://example.com/ | grep -o '&lt;a [^&gt;]*href="[^"]*"' | sort -u</code></pre>

<p>If that prints your menu, the navigation is in the HTML and this finding does not apply to
you. If it prints your footer and nothing else, you have the shape the check looks for. Run it
against a few pages rather than the homepage alone, which is the page most likely to have been
given special treatment.</p>

<h2>The fix</h2>

<p>One thing changes, and it is smaller than a rewrite: emit anchors with destinations in the
initial HTML, and let the client-side router take over from there. Server-side rendering,
static generation and prerendering all produce exactly that, and a router hydrating over a
real anchor is the intended arrangement rather than a workaround.</p>

<p>What does not work is the pattern the fix text names:</p>

<pre><code>&lt;div class="nav-item" onclick="go('/services/')"&gt;Services&lt;/div&gt;</code></pre>

<p>That is a button with link-coloured text. It is not a link to a crawler, it is not a link
to a screen reader, and it cannot be opened in a new tab. An anchor with an <code>href</code>
fixes all three at once.</p>

<p>If your framework's link component renders an anchor, the markup is fine and the finding
is about your rendering mode. If it renders a div, the component is the bug.</p>

<h2>Why it is worth the effort estimate</h2>

<p>The finding's detail makes an argument about sitemaps that is worth repeating, because it
is the one most often waved away. Quoting the check:
<code>A sitemap tells a crawler a page exists; it does not tell it which pages matter, which
is what internal links do.</code> The signal you lose when the navigation is client-side is
not discovery, which the sitemap covers, but the relative weight your own site places on its
own pages — <a href="/learn/internal-link-equity/">how internal links distribute authority</a>
is the mechanism being described.</p>

<h2>When the finding is wrong</h2>

<p>Push back on it in three situations. A site that genuinely has little internal linking — a
brochure site whose pages link only to the homepage — can land under the threshold with no
JavaScript involved; the average does not know why it is low. A crawl that was blocked or
truncated may have read pages unrepresentative of the site. And a site whose links Docket
recovered by rendering has those links counted, so a finding you expected may correctly not
appear. In all three, settle it with the <code>curl</code> command above, on pages you choose
rather than pages a crawler chose.</p>

<h2>Where to go next</h2>

<p>This page is about navigation specifically. If the question is broader — whether your
content, not your menu, exists before JavaScript runs — that is a different procedure, and
<a href="/how-to/javascript-seo-audit/">running a JavaScript SEO audit</a> walks through
comparing the served HTML against the rendered page. If you want the rest of what Docket looks
at while it is in there, <a href="/learn/what-docket-checks/">the full check list</a> is
published, and <a href="/learn/seo-audit/">what a technical SEO audit covers</a> sets the
context.</p>

<p><a class="btn" href="/download/">Download Docket</a></p>
"""
    return render(
        cat="how-to", slug="fix-navigation-that-needs-javascript",
        title="Fix navigation that needs JavaScript to work",
        desc=("Docket's nav_not_in_html check counts internal links across a site in the HTML "
              "your server "
              "sent. What it measures, what it cannot tell you about Google, and the fix."),
        h1="Fixing navigation that only exists after JavaScript runs",
        crumb=('<a href="/">Docket</a> / <a href="/how-to/">Fix it</a> / '
               'navigation that needs JavaScript'),
        body=body,
        published=CHECKED_ON,
        schema_type="Article",
        faq=[
            ("My menu is built by JavaScript. Can Google follow it?",
             "If the menu ends up as anchor elements with href attributes, yes — Google's "
             "documentation says a link is an anchor with an href, and injecting one with "
             "JavaScript is allowed. The catch is timing: crawling and rendering are separate "
             "queues, so those links are found on a later pass. If the menu is made of "
             "clickable divs or spans with no href, it is not a link at any stage."),
            ("What does the nav_not_in_html check actually count?",
             "Distinct internal destinations reachable from an anchor element with an href, in "
             "the HTML the server returned, deduplicated per page and averaged across every "
             "crawled page that returned OK with an HTML content type. It does not inspect "
             "nav elements or look for a menu. The finding is raised once for the site, at HIGH "
             "severity, with a LARGE effort estimate."),
            ("Why did my single-page app not get flagged?",
             "Probably because Docket recovered its links. During discovery, a page whose raw "
             "HTML yields no links and which looks like a JavaScript shell is re-read in "
             "WebKit, and the links found there are used. The site this check was written for "
             "is the opposite case: real server-rendered copy, so the shell heuristic never "
             "fires, and navigation that is client-side, so the links are never there."),
            ("Can Docket tell me whether Googlebot rendered my navigation?",
             "No. Nobody outside Google can measure what Google rendered, or when. Docket "
             "reports what your server sent and, on a capped sample, what a local WebKit "
             "engine builds from it. Googlebot's rendering is not identical to that, and no "
             "finding here should be read as a statement about what Google in particular "
             "did."),
            ("My site is small and got flagged anyway. Is that a false positive?",
             "It may be. The check needs at least three crawled HTML pages before it will "
             "look at all, but a genuinely sparse brochure site can still fall under the "
             "average without any JavaScript being involved. Fetch a few pages with curl and "
             "grep for anchors — if your links are in the source, the finding does not apply "
             "to you."),
            ("Is a sitemap enough to make up for it?",
             "It keeps the pages discoverable and does nothing about the rest. The check's "
             "own wording is that a sitemap tells a crawler a page exists but not which pages "
             "matter, which is the job internal links do. Losing the navigation from the HTML "
             "costs you the second thing, not the first."),
        ],
    )


BUILDERS = [fix_navigation_that_needs_javascript]


def build_all() -> list[Path]:
    return [b() for b in BUILDERS]


if __name__ == "__main__":
    for p in build_all():
        print(p)
