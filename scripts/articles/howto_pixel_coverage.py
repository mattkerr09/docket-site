"""A pixel reported as partly deployed, on no pages at all.

Promised on the how-to hub. Sourced from `martech.py`, registered checks
`mar.ad_pixels` (finding id `mar.pixel_gaps`) and `mar.stack`. One seam, two
consequences, and a refusal:

  * a financial institution's report named six advertising pixels as "only on
    part of the site" and printed "(0 pages)" beside every one of them. The
    finding contradicted its own numbers in its own sentence.
  * the cause: `_site_trackers` merges the served HTML WITH THE RENDERED DOM —
    that is why it exists — while the coverage loop counted `p.trackers`, the
    served HTML alone. A JavaScript-injected pixel therefore lands in the
    inventory and scores zero on every page, and zero is always under the
    seventy-percent bar. The guard was in the neighbouring check and not this
    one.
  * the same seam in `mar.stack` has a worse consequence: a large open-source
    project's site injects its container from a script, so the inventory named
    three tools with a per-page maximum of zero — and the `>= 8` escalation
    that turns the inventory into a script-weight finding reads that same
    number, so a site loading every tag through a container COULD NEVER TRIP
    THE THRESHOLD THAT IS ABOUT EXACTLY THOSE SITES.
  * the refusal: counting from the merged map would not fix it either, because
    only a sample of pages is rendered. So tags seen only after rendering are
    not judged, and the finding NAMES them and says why.

⚠️ NO SITE OR VENDOR IS NAMED — third-party gate plus the standing no-vendor
rule. The six platforms are "six advertising pixels from six platforms"; the
container is "a tag container".

⚠️ DOES NOT DUPLICATE /how-to/analytics-findings-name-the-tag/, which is about
ABSENCE ("you have no analytics"). This page is about PARTIAL COVERAGE.

⚠️ THE LANE PAGE'S INVENTED FRACTION was corrected in the same commit — see
`martech.py` in this directory. It claimed one missing page in a funnel of four
is "a quarter of your conversions", a statistic nothing measured.

Numerals: none. Quantities spelled as words.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from render import render  # noqa: E402


def pixel_coverage() -> Path:
    body = """
<p class="lede">Some findings are wrong in a way you can catch without knowing anything about the
site. A report that says six advertising pixels are installed on part of your site, and prints
"zero pages" beside each one, has contradicted itself inside a single sentence. Here is what was
actually happening, because the cause turns out to be the most common blind spot in tag auditing
and it runs in both directions.</p>

<h2>Six pixels, only on part of the site, none of them on any page</h2>

<p>A financial institution's report carried exactly that. Six advertising pixels from six
platforms, listed under a headline saying they were only on part of the site, each annotated with
a page count of zero.</p>

<p>A pixel on no pages is not partly deployed. It is either absent, or it is somewhere the check
could not count. It was the second one.</p>

<h2>One name over two populations</h2>

<p>Two different questions get asked about tags, and they had been answered from two different
documents.</p>

<p><strong>What is installed on this site?</strong> That inventory is built from the served HTML
merged with the rendered page — merging is the entire reason the inventory exists, because a tag
injected by JavaScript is invisible in the HTML a server sends.</p>

<p><strong>How many pages carry each tag?</strong> That count was reading the served HTML alone.</p>

<p>So a pixel loaded by JavaScript appeared in the first answer and scored nothing in the second.
Zero is always below any coverage threshold, so every such pixel was reported, every time, as a
deployment gap. <strong>The two numbers in the sentence came from different populations wearing
one name.</strong></p>

<p>The neighbouring check in the same file had already been handed the merged map for precisely
this reason, and says so in its own documentation. The guard existed; it had not travelled the few
lines to its neighbour.</p>

<h2>The same seam, with a consequence worth more than the contradiction</h2>

<p>An always-emitted part of the report simply lists what is running on your site — not a defect,
a fact most owners cannot recite about their own property, and the way forgotten agency tags get
noticed.</p>

<p>On a large open-source project's site, which injects its tag container from a script file, that
list named three tools and published a per-page maximum of zero beside them. Same seam, same
contradiction.</p>

<p>But that inventory has an escalation: past eight separate tools on a single page it stops being
a list and becomes a real finding, because each third-party script competes with your content for
the visitor's connection and the page gets slower. <strong>The number that escalation reads was
the served-HTML count.</strong> So a site that loads every one of its tags through a container —
which is the recommended practice, and the configuration most likely to accumulate forgotten tags
— could never reach the threshold. <strong>The gate was unreachable for exactly the population it
was built for.</strong></p>

<h2>Why counting the rendered pages instead would also have been wrong</h2>

<p>The obvious fix is to count coverage from the merged map. It is the wrong fix, and the reason is
worth borrowing for your own analysis.</p>

<p>Rendering every page of a site is expensive, so a sample is rendered. If the coverage count came
from the merged map, a pixel found on the rendered sample would be reported as being on that many
pages — turning <em>we only looked at a few pages properly</em> into <em>it is only on a few
pages</em>. That is a worse error than the one being fixed, because it looks reasonable.</p>

<p><strong>A tag seen only after rendering cannot support a claim about the pages that were not
rendered.</strong> So coverage is judged only for tags visible in the served HTML, and the tags
that were not judged are named in the finding, with the reason. A tool that tells you what it
declined to measure is worth more than one that produces a number for everything.</p>

<h2>Reading a coverage finding on your own report</h2>

<ol>
<li><strong>Check the count against the claim.</strong> "Only on part of the site" and "zero pages"
cannot both be true. When a finding's headline and its numbers disagree, believe the numbers and
distrust the headline.</li>
<li><strong>Ask whether the tag is in your HTML at all.</strong> View source and search for it. If
it is not there but your platform reports traffic, the tag is being injected at runtime and any
static count of it is meaningless.</li>
<li><strong>Check the platform's own diagnostics.</strong> Every major advertising platform will
tell you which of your pages fired its pixel in the last day. That is the measurement; a crawl is
a proxy for it.</li>
<li><strong>Look hardest at pages built outside your main template</strong> — campaign landing
pages, a checkout rebuilt by someone else, anything on a subdomain. That is where genuine coverage
gaps live.</li>
</ol>

<h2>When partial coverage is real, and what it costs</h2>

<p>The underlying finding is worth keeping, which is why the noise mattered. A pixel that is
missing from pages in the conversion path cannot record those conversions or add those visitors to
a retargeting audience — the event fires on a page the platform never saw the visitor reach.</p>

<p>Notice what that does not say: it does not put a fraction on it. How much a gap costs depends on
which page is missing the tag and what the platform does with a broken path, and an audit that
quotes you a percentage of lost conversions has invented it.</p>

<h2>The fixes that make it worse</h2>

<ul>
<li><strong>Hard-coding the pixel on every page as well as in your container.</strong> Now it fires
twice on the pages that had it, your conversion counts inflate, and every comparison you make
afterwards is against corrupted history.</li>
<li><strong>Moving everything into a container to make the report clean.</strong> It will work —
and you have traded a visible gap for an invisible one, because now nothing outside the browser
can see any of your tags.</li>
<li><strong>Chasing a pixel reported on no pages.</strong> Before you touch anything, confirm the
platform is receiving events. The most likely thing that is broken is the report.</li>
<li><strong>Removing a tag you do not recognise.</strong> Find out what it is first. The one you
do not recognise is often the one someone else's reporting depends on.</li>
</ul>

<h2>How to make every coverage number perfect</h2>

<p>Load every tag through a container and leave nothing in the served HTML. No static audit can
find a coverage gap, because none can find anything at all — and the inventory that would have
warned you about script weight goes quiet at the same time. <strong>A coverage number measures what
a fetcher could see, not what fired.</strong> Worth holding on to in both directions: it is why the
finding was wrong here, and why a clean one is not proof that your measurement works.</p>

<h2>Where this sits in an audit</h2>

<p>The registered checks are <code>mar.ad_pixels</code>, which looks at advertising pixels, and
<code>mar.stack</code>, the inventory of what is installed. For the case where a report claims you
have no analytics at all, see <a href="/how-to/analytics-findings-name-the-tag/">"you have no
analytics" is a claim about a list &rarr;</a>. For the lane as a whole, see
<a href="/learn/marketing-tag-audit/">the marketing tag audit &rarr;</a>. For why a tag in the HTML
and a tag on the page are different documents, see <a href="/how-to/javascript-seo-audit/">how to
audit a JavaScript site &rarr;</a>.</p>
"""
    return render(
        cat="how-to", slug="pixels-reported-on-zero-pages",
        title="A pixel reported on part of the site, and no pages",
        desc=("An audit counted tag coverage from one document and the inventory from another, so "
              "pixels on a site were reported as partly deployed and on no pages at once."),
        h1="A pixel on part of the site, and on no pages",
        crumb='<a href="/">Docket</a> / <a href="/how-to/">Fix it</a> / Pixel coverage',
        body=body,
        faq=[
            ("Why does an audit say a pixel is on part of my site and then show zero pages?",
             "Because the inventory and the coverage count were read from different documents. "
             "The inventory includes tags found after the page was rendered; the count read only "
             "the HTML the server sent, so a tag injected by JavaScript scores zero everywhere."),
            ("Does a pixel loaded through a tag container count as installed?",
             "For your advertising platform, yes — it fires. For any audit reading served HTML, "
             "it is invisible, so coverage numbers about it are unsupported rather than wrong. "
             "Check the platform's own diagnostics instead."),
            ("Should I hard-code pixels on every page to fix a coverage finding?",
             "No. If the tag also loads through your container it will fire twice, inflating "
             "conversions and corrupting the history you compare against."),
            ("How much does a missing pixel actually cost?",
             "It depends on which page is missing it. The concrete loss is that conversions on "
             "that page cannot be recorded and those visitors cannot be added to a retargeting "
             "audience. Any audit quoting you a percentage has invented it."),
            ("How can I tell whether a coverage finding is real?",
             "Open your own platform's reporting. If it shows events from the pages the audit "
             "called untagged, the finding is about what a fetcher could see. If it shows a gap "
             "on a page in your conversion path, the finding is real and worth fixing today."),
        ],
    )


if __name__ == "__main__":
    print(pixel_coverage())
