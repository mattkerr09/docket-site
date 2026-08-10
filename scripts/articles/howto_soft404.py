#!/usr/bin/env python3
"""How to fix soft 404s.

Promised on the how-to hub. Sourced from Docket's `index.soft_404` check, which
requests a deliberately invalid URL and reports when the server answers 200 —
including the wording it uses and why it is MEDIUM rather than HIGH.

Status codes are the only numeric literals; ALLOWED declares them as constants
of the protocol.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from render import render  # noqa: E402


def soft_404s() -> Path:
    body = """
<p class="lede">A soft 404 is a page that tells a human "not found" and tells a crawler
"200 OK". Both messages are on the same response, and only one of them is machine-readable —
so the site ends up with an unbounded supply of indexable pages that contain nothing.</p>

<h2>How to see it in ten seconds</h2>

<p>Ask for a URL that cannot exist and look at the status line, not the page:</p>

<pre><code>curl -sI https://example.com/this-page-does-not-exist-9x7q | head -1</code></pre>

<p>You want <code>404</code>. If you get <code>200</code>, every mistyped link, every stale
URL in someone's old newsletter, and every path a scraper invents is now a page on your site
as far as a search engine is concerned. The browser looked fine the whole time, which is
exactly why this survives so long.</p>

<h2>Why it costs more than it looks</h2>

<ul>
<li><strong>Crawl budget goes to nothing.</strong> A crawler cannot tell a real page from an
error page that returns success, so it keeps fetching them and re-fetching them.</li>
<li><strong>Thin, near-duplicate pages accumulate.</strong> Every invalid URL produces the
same "sorry, nothing here" content at a different address. That is a duplicate-content
pattern generated automatically, forever.</li>
<li><strong>Real 404s stop being visible.</strong> Search Console's coverage reports are one
of the few places broken internal links surface. When errors return 200 they never appear
there, and the actual broken links stay hidden.</li>
<li><strong>Redirecting everything to the homepage is the same bug.</strong> A blanket 301
from any unknown URL to <code>/</code> is a soft 404 with extra steps: still no error, still
no signal, and now the homepage is the destination of every mistake.</li>
</ul>

<h2>The fix, by cause</h2>

<p><strong>A JavaScript app that renders "not found" client-side.</strong> The server returned
the shell with 200 before the router decided the route was invalid. Fix it at the server or
edge: the route table has to be known where the status is set, not only in the browser. If
that is genuinely impossible, the fallback is <code>noindex</code> on the rendered error
state — worse than a 404, better than an indexable one.</p>

<p><strong>A CMS with a friendly error page.</strong> Some templates serve the error page as
ordinary content. The page can stay exactly as it is; the response code has to change.</p>

<p><strong>A catch-all route.</strong> A wildcard handler that renders something for every
path. Give it an explicit not-found branch that sets the status.</p>

<p><strong>Deleted content.</strong> If the URL earned links, <code>301</code> to the closest
genuine replacement — not the homepage. If there is no replacement, <code>404</code> is the
honest answer, and <code>410</code> is better still when the removal is permanent: it tells
crawlers not to come back.</p>

<h2>The error page itself should still be good</h2>

<p>Returning the right status costs you nothing in the experience. A 404 page can carry your
navigation, a search box, and links to the sections people most often want — and still be a
404. The status code is for machines and the page is for people; the mistake is letting the
page's friendliness overwrite the machine's answer.</p>

<h2>What Docket does</h2>

<p>It requests a URL that cannot exist and reads the status. That is the only way to find this
— nothing in the markup of a real page reveals how the server treats an unreal one, so a
checker that only looks at pages you link to will never see it. It is reported at MEDIUM: the
site works for visitors, which is why nobody noticed, and it quietly degrades everything a
crawler concludes.</p>

<p><a class="btn" href="/download/">Download Docket</a></p>
"""
    return render(
        cat="how-to", slug="fix-soft-404s",
        title="How to fix soft 404s (pages that return 200)",
        desc=("A missing page that answers 200 makes every mistyped URL indexable. How to "
              "check it in one command, what it costs, and the fix for each cause."),
        h1="How to fix soft 404s",
        crumb='<a href="/">Docket</a> / <a href="/how-to/">Fix it</a> / soft 404s',
        body=body,
        faq=[
            ("What is a soft 404?",
             "A page that tells a person the content is missing while returning HTTP 200 to "
             "the crawler. The human message and the machine message disagree, and only the "
             "machine one affects indexing."),
            ("How do I check for soft 404s?",
             "Request a URL that cannot exist and read the status line rather than the page: "
             "curl -sI https://example.com/this-page-does-not-exist | head -1. You want a "
             "404. A 200 means every invalid URL is an indexable page."),
            ("Is redirecting unknown URLs to the homepage a fix?",
             "No — it is the same bug with extra steps. There is still no error signal, and "
             "the homepage becomes the destination for every mistyped link."),
            ("Should I use 404 or 410?",
             "404 for anything that might come back or was never there. 410 when the removal "
             "is deliberate and permanent — it tells crawlers not to return."),
            ("Can my 404 page still look nice?",
             "Yes. Keep the navigation, the search box and the helpful links. The status code "
             "is for machines and the page is for people; only the code has to change."),
        ],
    )


if __name__ == "__main__":
    print(soft_404s())
