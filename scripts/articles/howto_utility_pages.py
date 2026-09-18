"""Site search, cart and confirmation pages that ended up in Google.

Promised on the how-to hub. Sourced from the registered check `content.thin`,
which emits `content.utility_pages_indexable` when site search, cart, login or
confirmation pages are indexable.

Worth its own page because nothing is wrong with the pages themselves. They are
doing their job. The fault is only that they are in an index, which makes it
invisible to anyone reviewing the pages on their merits.

No numeric literals.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from render import render  # noqa: E402


def utility_pages() -> Path:
    body = """
<p class="lede">Somebody searches for your brand and lands on your empty cart. Or on a search
results page for a term nobody sold anything with. Or on the order confirmation that thanks them
for a purchase they never made. None of those pages is broken — they are all working exactly as
built — and every one of them is a bad first impression that you did not choose.</p>

<h2>Which pages this is about</h2>

<p>The utility pages every site has and nobody writes: <strong>internal search results</strong>,
the <strong>cart</strong>, <strong>login</strong> and account screens, <strong>wishlists</strong>,
and <strong>order or enquiry confirmations</strong>. They carry almost no content because
content is not what they are for.</p>

<p>Internal search results are the sharpest case, and the one Google asks site owners to keep
out of the index by name. A search page can generate an unlimited number of URLs — one per query
anybody ever types, including the ones typed by bots — and each looks like a real page to a
crawler.</p>

<h2>Why it survives review</h2>

<p>Because there is nothing to find. Open any of these pages and it looks right, because it is
right. A content audit that judges pages on their merits passes them. A thin-content report
flags them and gets waved away, correctly, because nobody is going to write five hundred words
onto a login form.</p>

<p>The fault is not in the page. It is in the page being <em>available to a search engine</em>,
and that is a property you have to go looking for.</p>

<h2>What it costs</h2>

<ul>
<li><strong>A dead end for a real searcher.</strong> Someone looking for your brand gets a page
with nothing on it and no reason to stay.</li>
<li><strong>A confirmation page found by strangers.</strong> At best it is confusing. If your
analytics counts that page as a conversion, your conversion data now includes people who arrived
from a search result.</li>
<li><strong>Crawl spent on nothing.</strong> An unbounded set of search URLs is an unbounded
amount of fetching that could have gone to pages you wrote.</li>
</ul>

<h2>The fix, and the wrong version of it</h2>

<p>Add a robots meta tag to those pages, and keep <code>follow</code>:</p>

<pre><code>&lt;meta name="robots" content="noindex, follow"&gt;</code></pre>

<p><code>noindex</code> takes the page out. <code>follow</code> means the links on it are still
crawled, which matters on a cart or account page that links onwards into the site.</p>

<p><strong>Do not reach for robots.txt instead.</strong> Disallowing a path stops the crawler
<em>fetching</em> the page — which also stops it seeing the <code>noindex</code> you put there.
A URL that is linked from somewhere can still end up listed on the strength of the link alone,
and now there is no way to tell the engine to drop it. Blocking the crawler and asking it to
forget the page are different requests, and only one of them needs the page to be readable.</p>

<h2>Finding yours</h2>

<p>Ask the engine what it has:</p>

<pre><code>site:example.com inurl:search
site:example.com inurl:cart
site:example.com inurl:checkout</code></pre>

<p>Then check the pages themselves for the tag. If your search URLs use a query string rather
than a path, search for the parameter instead — the shape varies by platform and the fault does
not.</p>

<h2>What this does not cover</h2>

<p>Whether these pages should exist, or how faceted navigation ought to be handled, are design
questions with real trade-offs. This is narrower and more boring: pages that are already right
are telling search engines to list them, and one directive stops it.</p>
"""
    return render(
        cat="how-to", slug="stop-indexing-site-search-and-cart-pages",
        title="Site search and cart pages in Google: take them out",
        desc=("Internal search results, carts and order confirmations get indexed because "
              "nothing about them looks broken. What it costs and the one directive that "
              "fixes it."),
        h1="Site search and cart pages that ended up in Google",
        crumb='<a href="/">Docket</a> / <a href="/how-to/">Fix it</a> / utility pages',
        body=body,
        faq=[
            ("Should internal search results be indexed?",
             "No. Google asks site owners to keep them out of the index, and a search page can "
             "generate an unlimited number of URLs — one per query anyone ever types, "
             "including bots. Each looks like a real page to a crawler."),
            ("What is the fix for indexable cart and login pages?",
             "A robots meta tag with noindex and follow. The noindex takes the page out of the "
             "index; keeping follow means the links on it are still crawled, which matters on "
             "pages that link onwards into the site."),
            ("Can I just block them in robots.txt?",
             "That is the common wrong answer. Disallowing the path stops the crawler fetching "
             "the page, which also stops it seeing the noindex. A linked URL can still be "
             "listed on the strength of the link, and you have removed your own way to ask "
             "for it to be dropped."),
            ("Why do these pages survive a content audit?",
             "Because nothing is wrong with them. They look right because they are right, and "
             "nobody is going to write five hundred words onto a login form. The fault is that "
             "they are available to a search engine, which is a property you have to look for "
             "rather than something visible on the page."),
            ("Does an indexed confirmation page affect analytics?",
             "It can. If the page counts as a conversion, people arriving from a search result "
             "are counted alongside people who actually bought."),
        ],
    )


if __name__ == "__main__":
    print(utility_pages())
