#!/usr/bin/env python3
"""How to fix layout shift (CLS).

Sourced from Docket's `perf.cls_risk` and `onpage.img_no_dimensions`, which are
the same defect seen from two sides — the check itself says so, and carries
`same_fix_as` so the action plan asks for the work once while both lanes keep
their deduction.

The honest limit is in the check's own detail and is repeated here rather than
softened: Docket infers the risk from markup and cannot measure CLS, which
needs a real browser under real network conditions.

Numeric literals: none beyond CSS values in code samples, which are markup
rather than prose.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from render import render  # noqa: E402


def layout_shift() -> Path:
    body = """
<p class="lede">Layout shift is the page moving under someone's finger. They go to tap a link,
an image finishes loading above it, everything jumps, and they tap an ad instead. Google
measures it as Cumulative Layout Shift, but the reason to fix it is that it is the most
irritating thing a page can do.</p>

<h2>The cause is almost always one thing</h2>

<p>An image with no declared width and height. The browser cannot know how much space to
reserve until the file arrives, so it reserves none — text flows up into the gap, then gets
shoved down when the image lands.</p>

<p>This got worse when responsive images arrived. People removed <code>width</code> and
<code>height</code> because CSS was handling sizing, which was reasonable at the time and is
wrong now: modern browsers use the attributes purely to compute an aspect ratio and reserve
the right space, then let your CSS resize it. Putting them back costs nothing and changes
nothing visually.</p>

<pre><code>&lt;img src="/photo.jpg" alt="…" width="1200" height="800"&gt;</code></pre>

<p>Use the file's real pixel dimensions. They are not a display size — the browser takes the
ratio from them and your stylesheet still decides how big it renders.</p>

<h2>When you cannot know the dimensions</h2>

<p>User-uploaded images, a CMS that does not store sizes, a third-party feed. Reserve the space
in CSS instead:</p>

<pre><code>img { aspect-ratio: 3 / 2; width: 100%; height: auto; }</code></pre>

<p>The container holds its shape before anything loads. Any known ratio beats no ratio.</p>

<h2>The other four causes, in the order they bite</h2>

<ul>
<li><strong>Ads and embeds injected into the flow.</strong> Anything inserted after first
paint pushes content down. Give the slot a fixed minimum height even when empty — an
occasional gap is a far smaller cost than the whole page jumping.</li>
<li><strong>Web fonts swapping.</strong> Text renders in a fallback, the real font arrives, and
every line reflows because the metrics differ. <code>font-display: optional</code> avoids the
swap entirely; matching the fallback's metrics with <code>size-adjust</code> narrows it.</li>
<li><strong>Banners inserted at the top.</strong> Cookie notices, promo bars and "you have
items in your basket" strips added by script after load shift everything below them. Reserve
the space, or overlay rather than insert.</li>
<li><strong>Content that expands on interaction.</strong> Accordions and "read more" are fine:
shifts within half a second of a click or tap are not counted, because the user caused
them.</li>
</ul>

<h2>Where to look first</h2>

<p>Above the fold, on mobile, on a slow connection. A shift only counts when it moves content
that was visible, so an image far down the page that jumps before anyone scrolls to it costs
nothing. Your hero image, your logo, and any banner near the top are worth more attention than
everything below them combined.</p>

<h2>What Docket can and cannot tell you</h2>

<p>It reads the markup and reports pages where most images have no declared size — the
condition that causes shift. <strong>It does not measure CLS.</strong> That needs a real
browser under real network conditions, and any tool claiming a CLS score from a crawl is
reporting a guess as a measurement.</p>

<p>So the finding is a risk, stated as one, with the instruction to confirm the field value in
PageSpeed Insights or Search Console. The two findings you may see — one about images without
dimensions, one about layout-shift risk — are the same defect from two sides, and Docket links
them so the action plan asks for the work once.</p>

<p><a class="btn" href="/download/">Download Docket</a></p>
"""
    return render(
        cat="how-to", slug="fix-layout-shift",
        title="How to fix layout shift (CLS) on your site",
        desc=("Layout shift is almost always images with no width and height. The fix, the "
              "four other causes, and why a crawler can report the risk but not the score."),
        h1="How to fix layout shift",
        crumb='<a href="/">Docket</a> / <a href="/how-to/">Fix it</a> / layout shift',
        body=body,
        faq=[
            ("What causes layout shift?",
             "Most often an image with no width and height attributes: the browser cannot "
             "reserve space before the file arrives, so content flows into the gap and is "
             "pushed down when it lands. Ads, font swaps and injected banners cause the rest."),
            ("Do width and height attributes override my CSS?",
             "No. Modern browsers use them to compute an aspect ratio and reserve space; your "
             "stylesheet still controls the rendered size. Adding them changes nothing "
             "visually."),
            ("What if I don't know the image dimensions?",
             "Reserve the space in CSS with aspect-ratio on the container. Any known ratio is "
             "better than none, and it works for user-uploaded or third-party images."),
            ("Does an accordion opening count as layout shift?",
             "No. Shifts within half a second of a user interaction are excluded, because the "
             "user caused them."),
            ("Can a crawler measure CLS?",
             "No. CLS needs a real browser under real network conditions. A crawler can "
             "identify the markup that causes shift and report it as a risk — anything "
             "presenting a CLS score from a crawl is reporting a guess as a measurement."),
        ],
    )


if __name__ == "__main__":
    print(layout_shift())
