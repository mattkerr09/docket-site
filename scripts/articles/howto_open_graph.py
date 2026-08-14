#!/usr/bin/env python3
"""The social lane — five checks, no page anywhere on this site.

The gap analysis found the social lane apparently covered, because a naive grep
for "favicon" matches every page: every page on this site has a
`<link rel="icon">` in its own markup. That was a false positive, and the manual
read found zero dedicated coverage.

Written around `social.og_image_dead` rather than `social.og_missing`, because
the missing-tag case is well covered by every other tool and the dead-image case
is the one people cannot diagnose. The person who broke it is the last person who
will see it broken: every platform caches the preview it scraped, so the sharer
keeps seeing the old, working card.

Check names come from `backend/seo_engine/checks/social.py`, read on 2026-08-14.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from render import render  # noqa: E402


def howto_open_graph() -> Path:
    body = """
<p class="lede">If your links share as a bare URL, or a blank grey rectangle, the cause is
almost always one of three things: no Open Graph tags at all, an og:image that no longer
exists, or an image the platform will not accept. They look identical when you paste the
link, and they need different fixes.</p>

<h2>Work out which one you have</h2>

<p>View source on the page and search for <code>og:</code>. What you find decides
everything after this.</p>

<ul>
<li><strong>Nothing.</strong> The platform is falling back to whatever it can scrape —
usually the title tag and no image. Add the tags below.</li>
<li><strong>Tags, but no <code>og:image</code>.</strong> You get a small text card instead
of the large image one. This is the most common state on sites built before previews
mattered.</li>
<li><strong>An <code>og:image</code> that is there.</strong> Then open that URL directly in
a browser. If it 404s, you have found it.</li>
</ul>

<h2>The dead image is the one nobody catches</h2>

<p>An <code>og:image</code> pointing at a file that no longer exists is the failure worth
knowing about, because <strong>the person who broke it is the last person who will see it
broken</strong>.</p>

<p>Every platform caches the preview it scraped the first time. You share your page, see the
card you have always seen, and conclude it works. Everyone who shares it after the image
moved gets a blank rectangle. Nothing in your analytics records a share that looked broken,
so the feedback never arrives.</p>

<p>It happens on ordinary maintenance: a CMS upgrade renames the uploads folder, a CDN path
changes, a marketing image gets tidied away, a staging URL was left in the tag and staging
was decommissioned. The page still works. Only the preview is gone.</p>

<p>Docket fetches the <code>og:image</code> URL and reports a dead one at MEDIUM — higher
than a missing tag, because a missing tag is a card you never had and a dead image is one
you think you have.</p>

<h2>The tags to add</h2>

<pre><code>&lt;meta property="og:title" content="The headline you want shared"&gt;
&lt;meta property="og:description" content="One or two sentences."&gt;
&lt;meta property="og:image" content="https://example.com/share.png"&gt;
&lt;meta property="og:url" content="https://example.com/this-page/"&gt;
&lt;meta property="og:type" content="website"&gt;
&lt;meta name="twitter:card" content="summary_large_image"&gt;</code></pre>

<p>Four things that decide whether it works:</p>

<ul>
<li><strong>The image URL must be absolute.</strong> <code>/share.png</code> is a common
and total failure — the scraper is not on your site and cannot resolve it.</li>
<li><strong>It must be reachable without a login or a cookie.</strong> Scrapers are not
signed in. An image behind auth is a dead image as far as the preview is concerned.</li>
<li><strong>Use around 1200×630.</strong> Much smaller and platforms fall back to the small
card; the large card is the whole point.</li>
<li><strong>Serve it over https.</strong> An http image on an https page is mixed content,
which is a separate finding and a separate problem.</li>
</ul>

<p>The Twitter/X card tag is worth including even though X reads Open Graph as a fallback,
because <code>summary_large_image</code> is what turns the small card into the large one.
Without it you get the small card on a site that already has everything it needs for the
large one.</p>

<h2>Check it before you need it</h2>

<p>Each platform has a debugger that re-scrapes on demand — that is what to use after a fix,
because your own paste test will keep showing you the cached card. If you have a Docket
audit to hand, the social lane already fetched the image and told you whether it resolved.</p>

<h2>Why this is an SEO page and not a design one</h2>

<p>Open Graph tags are not a ranking signal, and anyone telling you they are is guessing.
They decide whether a link that somebody chose to share arrives looking like something worth
clicking. The traffic is already earned at that point; the preview decides how much of it
survives the trip.</p>

<p><a class="btn" href="/download/">Download Docket</a></p>
"""
    return render(
        cat="how-to", slug="fix-missing-open-graph-tags",
        title="Fix a link preview that shows no image",
        desc=("No Open Graph tags, a dead og:image, or an image the platform will "
              "not take — they look identical when you paste a link and need "
              "different fixes."),
        h1="How to fix a broken link preview",
        crumb='<a href="/">Docket</a> / <a href="/how-to/">Fix it</a> / Link previews',
        body=body,
        faq=[
            ("Why does my link preview show no image?",
             "Either the page has no og:image tag, or it has one pointing at a file that "
             "no longer exists, or the image is unreachable to a scraper — a relative "
             "URL, something behind a login, or an http image on an https page. Open "
             "the og:image URL directly in a browser to tell which."),
            ("Why do I still see the old preview after fixing it?",
             "Because platforms cache the preview they scraped the first time. The "
             "person who broke it is the last person to see it broken. Use the "
             "platform's own debugger to force a re-scrape rather than pasting the link "
             "again yourself."),
            ("Do Open Graph tags help SEO rankings?",
             "No, and anyone saying otherwise is guessing. They decide whether a link "
             "somebody already chose to share arrives looking worth clicking. The "
             "traffic is earned before the preview is involved."),
            ("What size should an og:image be?",
             "Around 1200x630 pixels, served over https at an absolute URL that needs no "
             "login. Much smaller and platforms fall back to the small text card, which "
             "defeats the point of adding the image."),
        ],
    )


BUILDERS = [howto_open_graph]


def build_all() -> list[Path]:
    return [b() for b in BUILDERS]


if __name__ == "__main__":
    for p in build_all():
        print(p)
