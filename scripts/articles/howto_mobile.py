"""Mobile SEO: what a crawl can and cannot check.

Promised on the how-to hub. Sourced from the checks that actually bear on a
phone — `onpage.lang` (which covers the viewport declaration), `perf.cls_risk`,
`perf.page_weight`, `perf.render_blocking`, `perf.ttfb` and
`cvr.unusable_phone` — and, more importantly, from what none of them can see.

The point of the page is the boundary. A crawler can prove some things about a
mobile page and cannot prove the ones people actually mean by "mobile-friendly",
and saying so is worth more than a score that covers the gap.

No numeric literals.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from render import render  # noqa: E402


def mobile() -> Path:
    body = """
<p class="lede">Google indexes the mobile version of your site. Not a mobile version of your
desktop site — the mobile page is the page, and the desktop one is the variant nobody ranks.
That makes "is it mobile-friendly?" an important question and a badly-defined one, because it
is several different questions and only some of them can be answered without a phone.</p>

<h2>What a crawl can actually prove</h2>

<p><strong>Whether the page declares a viewport.</strong> Without
<code>&lt;meta name="viewport"&gt;</code>, a phone assumes the page was built for a desktop and
renders it at desktop width, then scales it down. Everything is legible only to someone willing
to pinch. This is the one genuinely binary mobile fault: the tag is there or it is not.</p>

<pre><code>&lt;meta name="viewport" content="width=device-width, initial-scale=1"&gt;</code></pre>

<p><strong>How heavy the page is.</strong> Weight matters more on a phone than on a laptop,
because the connection is worse and the radio costs battery. A crawl can total what the page
pulls in and say whether that is reasonable for somebody on mobile data.</p>

<p><strong>What blocks the first render.</strong> Stylesheets and scripts in the head that must
be fetched and parsed before anything appears. On a fast connection this is invisible. On a slow
one it is the whole experience.</p>

<p><strong>How long the server takes to answer.</strong> Before any of the above happens,
somebody waits for the first byte. That wait is the same on every device and it is the floor
under every other speed number.</p>

<p><strong>Whether images will shove the layout around.</strong> An image with no width and
height reserves no space, so the text reflows when it arrives. On a phone, that is the paragraph
you were reading jumping off the screen, or the button moving under your thumb as you press it.</p>

<p><strong>Whether a phone number will dial.</strong> A number typed as text is a number a
mobile visitor has to select, copy and paste. One wrapped in <code>tel:</code> is one tap. For a
business that takes calls, this is the mobile fault with the shortest line to lost revenue.</p>

<h2>What a crawl cannot tell you, and nobody should pretend otherwise</h2>

<p>Everything above is a fact about the document. The things people usually mean by
"mobile-friendly" are facts about the <em>experience</em>, and no crawler has one:</p>

<ul>
<li><strong>Whether the text is readable</strong> at the distance a phone is actually held.</li>
<li><strong>Whether a thumb can reach the button</strong>, or whether it sits under the browser
chrome at the bottom of the screen.</li>
<li><strong>Whether the menu opens</strong> and closes without trapping you.</li>
<li><strong>Whether the form can be filled in</strong> with a keyboard covering half the screen
and a dropdown that fights the native picker.</li>
<li><strong>Whether the page is usable in sunlight</strong>, one-handed, on a train.</li>
</ul>

<p>A tool that returns a single "mobile score" is scoring the first list and quietly implying
the second. That is the failure worth avoiding: a green result on things nobody struggles with,
presented as a verdict on the thing they do.</p>

<h2>What to actually do</h2>

<p>Run the crawl for the document facts, because they are cheap, provable and genuinely break
pages. Fix the viewport tag first if it is missing — it is the only one that makes every other
mobile problem worse.</p>

<p>Then pick up a phone. Your own, on mobile data rather than the office wifi, and go through
the two or three journeys that make you money: find the page, read enough to decide, and get in
touch or buy. Anything that annoys you will annoy somebody who has not already decided to
persevere.</p>

<p>The crawl narrows the list. The phone tells you whether the site works.</p>
"""
    return render(
        cat="how-to", slug="check-mobile-seo-from-a-crawl",
        title="Mobile SEO: what a crawl can and cannot check",
        desc=("Google indexes the mobile page. Which mobile faults an audit can prove from "
              "your site's HTML, which need a real phone, and why one score hides it."),
        h1="Mobile SEO: what a crawl can and cannot check",
        crumb='<a href="/">Docket</a> / <a href="/how-to/">Fix it</a> / mobile',
        body=body,
        faq=[
            ("Does the viewport meta tag still matter?",
             "Yes, and it is the one binary mobile fault. Without it a phone renders the page "
             "at desktop width and scales it down, so everything is small until the visitor "
             "pinches. Use width=device-width, initial-scale=1."),
            ("Can an SEO crawler tell me if my site is mobile-friendly?",
             "Partly. It can prove document facts: the viewport declaration, page weight, "
             "render-blocking resources, server response time, images that shift the layout, "
             "and phone numbers that will not dial. It cannot tell you whether text is "
             "readable, whether a thumb reaches the button, or whether the form is usable."),
            ("Why do images without width and height hurt on mobile?",
             "They reserve no space, so the layout reflows when they load. On a small screen "
             "that means the paragraph you are reading jumps away, or a button moves under "
             "your thumb as you press it."),
            ("Is mobile-first indexing the same as having a mobile site?",
             "No. It means the mobile version is the version Google indexes and ranks. If "
             "content exists only on your desktop page, treat it as content that does not "
             "exist."),
            ("What is the fastest mobile fix for a business that takes calls?",
             "Wrap the phone number in a tel: link. A number typed as plain text has to be "
             "selected, copied and pasted; a tel: link is one tap."),
        ],
    )


if __name__ == "__main__":
    print(mobile())
