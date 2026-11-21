"""A measured explanation of crawl and indexing directives."""
from pathlib import Path

from render import buy_block, render


def crawler_directives() -> Path:
    body = f"""
<p class="lede"><strong>Crawler directives are rules in robots.txt, a meta robots tag or an X-Robots-Tag HTTP header.</strong> They control fetching, indexing and following links. They can stack badly: a page blocked in robots.txt is never fetched by a crawler that obeys it, so that crawler never sees the page's noindex.</p>

<h2>The three kinds, side by side</h2>

<p>The first question is whether a crawler may fetch a URL. The next is what it may do with a page it has fetched. These are separate questions. robots.txt answers the first. The meta robots tag and X-Robots-Tag answer the next. Reading them as though they all control the same thing makes a crawl block look like a way to remove a page from search.</p>

<div class="wrap-tbl"><table class="cmp">
<thead><tr><th>Directive</th><th>Where it lives</th><th>What it controls</th><th>What it cannot do</th></tr></thead>
<tbody>
<tr><td>robots.txt</td><td>The site's robots.txt file</td><td>Which URLs a crawler should not fetch</td><td>Let a crawler read noindex on a page it blocks</td></tr>
<tr><td>meta robots</td><td>A tag in the page</td><td>Whether a fetched page may be indexed and its links followed</td><td>Reach a crawler that never fetches the page</td></tr>
<tr><td>X-Robots-Tag</td><td>An HTTP response header</td><td>Whether a fetched page may be indexed and its links followed</td><td>Replace the robots.txt decision about fetching a URL</td></tr>
</tbody></table></div>

<p>A meta robots tag is part of the page a crawler reads. An X-Robots-Tag is sent as an HTTP header rather than written as a tag in that page. Both concern a fetched page. Keep that distinction in mind when checking a page: the place a rule lives affects whether the crawler gets to read it at all. The same word, noindex, does not help if the crawler cannot reach the rule.</p>

<p>A named user-agent group adds another question: which crawler is the rule for? A group in robots.txt applies only to the crawler that answers to that name. A rule can be in the right file yet name a crawler that does not answer to it. Check the name as well as the URL rule. The <a href="/learn/what-is-robots-txt/">robots.txt guide</a> explains the file, and the <a href="/learn/ai-crawler-directives/">AI crawler directives guide</a> covers crawler names.</p>

<h2>When two directives collide</h2>

<p><strong>To remove a page from search, let it be fetched and use noindex. Do not also block it in robots.txt.</strong> The block prevents the fetch that would reveal noindex. This is not a useful contest in which the crawler reads both rules and picks a winner. The crawler obeying robots.txt never reads the page, so it never reaches the page's instruction about indexing.</p>

<p>We saw this in a local test. A page carried noindex and was listed in the sitemap, but robots.txt disallowed it. The audit could not see its noindex because the page was never fetched. Its sitemap listing did not make that hidden instruction visible to the audit. Checking only the tag in the page would miss the problem: the tag was there, but the crawler could not read it.</p>

<p>Work through the path in order. First check whether robots.txt lets the crawler fetch the URL. Then check the fetched page's indexing rule. If your goal is removal from search, a noindex tag needs that fetch. Adding a robots.txt block to the same page cuts off the step that makes noindex readable. Keep the goal separate from the method: stopping a fetch and asking that a fetched page not be indexed are different instructions.</p>

<h2>What a real crawl caught</h2>

<p>We built a small local test site and ran Check Engine's audit on it. The results below describe what that audit could read and report. Two disallowed pages were never fetched and never reported, including the page with both noindex and a sitemap listing. That absence matters: an audit that obeys robots.txt cannot report a tag on a page it never reads. X-Robots-Tag was not tested because the test server could not send headers.</p>

<div class="wrap-tbl"><table class="cmp">
<thead><tr><th>Setup</th><th>What Check Engine reported</th></tr></thead>
<tbody>
<tr><td>Two pages disallowed by robots.txt, including one with noindex and a sitemap listing</td><td>Neither page was fetched or reported. The audit could not see the blocked page's noindex.</td></tr>
<tr><td>Two pages with noindex and no robots.txt block</td><td>Both were reported as blocked from indexing, at high severity.</td></tr>
<tr><td>One noindex page listed in the sitemap</td><td>The sitemap listing was reported at low severity.</td></tr>
<tr><td>robots.txt groups for anthropic-ai and Claude-Web</td><td>Rules naming a crawler that does not answer to that name were reported at medium severity.</td></tr>
<tr><td>A page with meta robots nofollow</td><td>No finding was raised.</td></tr>
<tr><td>X-Robots-Tag</td><td>Not tested. The test server could not send headers.</td></tr>
</tbody></table></div>

<p>The high and low findings describe different parts of the setup. The fetched pages with noindex were reported as blocked from indexing. The noindex page's sitemap listing was reported at low severity. Read the setup beside the finding rather than treating every mention of noindex as the same result. The blocked pages did not produce either kind of finding, because they were outside what this crawl fetched.</p>

<p>The nofollow result has a narrower meaning. A page with that meta robots instruction raised nothing in this test. It does not turn nofollow into an indexing instruction. Indexing a page and following its links are separate choices that the meta robots tag can express. Likewise, the header row is a limit of this test, not a measured result for X-Robots-Tag. We did not test the header and cannot say what this audit would have reported for it.</p>

<h2>How to check your own site</h2>

<ul>
<li>Start with the URL and the crawler name. Read the <a href="/learn/what-is-robots-txt/">guide to robots.txt</a> and check whether the rule stops that crawler fetching the page.</li>
<li>If the aim is to remove the page from search, allow the fetch and use noindex. Check that robots.txt does not hide the page's instruction.</li>
<li>Read the meta robots tag and the X-Robots-Tag HTTP header as rules about a fetched page. Keep indexing and following links separate when you read them.</li>
<li>Compare noindex pages with the sitemap. In our test, a noindex page listed there produced a low severity finding.</li>
<li>Check named groups against the name the crawler answers to. Use the <a href="/learn/ai-crawler-directives/">AI crawler directives guide</a> for detail.</li>
</ul>

<p>When reading an audit, ask what it was able to fetch before deciding what an absent finding means. Our blocked pages showed why: no report did not mean no noindex. It meant the crawler never read those pages. A useful check connects the robots.txt rule, the fetched page and the finding. If any part is missing, describe that limit plainly, just as we have for the untested HTTP header.</p>

{buy_block("learn-crawler-directives", try_app="learn-crawler-directives-try-free")}
"""
    return render(
        cat="learn", slug="crawler-directives",
        title="Crawler directives: robots.txt, meta robots, X-Robots-Tag",
        desc=("Crawler directives control fetching, indexing and following links. "
              "Compare robots.txt, meta robots and X-Robots-Tag, with a real crawl test."),
        h1="What are crawler directives?",
        crumb='<a href="/">Docket</a> / <a href="/learn/">Learn</a> / Crawler directives',
        body=body,
        published="2026-11-21", modified="2026-11-21",
        faq=[
            ("If I block a page in robots.txt and add noindex, which wins?",
             "A crawler that obeys robots.txt never fetches the blocked page, so it never sees the page's noindex. "
             "To remove a page from search, allow the fetch and use noindex. Do not also block it in robots.txt."),
            ("Is nofollow a crawler directive?",
             "Yes. The meta robots tag can tell a crawler whether a fetched page's links may be followed. "
             "A page with meta robots nofollow raised no finding in our local test."),
            ("Do AI crawlers follow the same directives?",
             'A named user-agent group in robots.txt applies only to the crawler that answers to that name. '
             'See the <a href="/learn/ai-crawler-directives/">AI crawler directives guide</a> for detail.'),
        ],
    )
