"""'You have no analytics' is a claim about a list.

Promised on the how-to hub. Sourced from the registered check `mar.analytics`
in `backend/seo_engine/checks/martech.py`, which carries both halves:

  * THE NUMBER WITH NO EVIDENCE UNDER IT — across hundreds of pages the only
    analytics-family tag found anywhere was a single session-recording tool on
    one page, and the finding read "analytics is missing from N of N pages",
    which tells a story about deployment gaps rather than about having no
    analytics at all.
  * TESTING ONE NAME WHILE A SET EXISTED — a job board with a retired analytics
    tag and no replacement was told it had had no data since, while carrying a
    modern product-analytics tool and a tag manager. The set was already
    defined at the top of the same file and used by the check above it.

⚠️ NO SITE OR VENDOR IS NAMED — third-party gate, and the standing rule not to
name vendors. Products are described by category: "a session-recording tool",
"a retired analytics product and its replacement", "a tag manager".

⚠️ DO NOT URGE CONSENT BANNERS — `mar.no_consent_banner` is unresolved and
awaits Matthew. This page stays off that subject entirely.

⚠️ /learn/marketing-tag-audit/ covers the lane overall and does NOT cover these
two failures. This page cross-links it rather than restating it.

Numerals: none. Quantities spelled as words.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from render import render  # noqa: E402


def analytics_findings() -> Path:
    body = """
<p class="lede">An audit reports that analytics is missing from most of your pages. It sounds
like a statement about your data. It is not — it is a statement about which tag names were on a
list, and which of those appeared in the HTML that was fetched. Those are very different claims,
and the gap between them has produced two instructive mistakes.</p>

<h2>The number with no evidence under it</h2>

<p>On one large site, across hundreds of crawled pages, the only analytics-family tag found
anywhere in the served HTML was a single session-recording tool, on one page. The finding said
analytics was missing from almost every page.</p>

<p>Read that sentence as an owner. It describes a <em>deployment with gaps</em> — some pages
tagged, some not, sessions breaking as visitors cross the boundary, traffic landing in the wrong
bucket. That is a real and common problem, and it is not this one. What had actually been measured
was one stray tag and <strong>no analytics at all</strong>.</p>

<p>Those two situations have nothing in common. One is "your tagging is inconsistent, find the
templates that miss it". The other is "you are not measuring anything, choose a tool". A reader
given the first description will go looking for a gap that does not exist.</p>

<p>The repair was to name the tools. <strong>"This tool appears on one page of the crawl, and no
other analytics tag was found anywhere" is checkable in ten seconds. "Analytics is missing from
most of your pages" is a number with no evidence under it</strong> — and a reader cannot audit a
percentage.</p>

<h2>Testing one name when the question was about a category</h2>

<p>The second case is sharper, because the information needed to avoid it was already in the
file.</p>

<p>A job board carried a genuine tag for a retired analytics product, with a real property
identifier, and none of that product's replacement. The audit told it, at high severity, that only
the retired tag was installed and that it had therefore had no data since the retirement date.</p>

<p>The site also carried a modern product-analytics tool, and a tag manager. <strong>It had been
collecting data the whole time.</strong></p>

<p>The branch had tested for one replacement product <em>by name</em>. The list of every analytics
tool the check knows about was defined at the top of the same file and used by the check
immediately above it. <strong>The most common way a check goes wrong is asking about a name when
the question is about a category</strong> — and the giveaway is a finding that mentions one
product where your situation involves another.</p>

<h2>Why a tag manager changes what can be claimed</h2>

<p>Worth its own section because it is the honest limit, and it cuts both ways.</p>

<p>A tag container collects nothing by itself. Its presence is <em>not</em> evidence that you have
analytics. But it can load an analytics tag at runtime, where a static fetch of the HTML cannot see
it — so its presence <strong>is</strong> evidence that absence cannot be concluded.</p>

<p>That is the whole of it: a container turns "you have no analytics" into "this tool could not
tell". A report that says the first when the second is true has overstated what it looked at, and
any audit reading served HTML rather than running the page is in that position by construction.</p>

<h2>Reading an analytics finding on your own report</h2>

<ul>
<li><strong>Does it name the tools it found?</strong> If not, that is the first thing to distrust.
A list of what was present and where is the evidence; a coverage percentage is a summary of it.</li>
<li><strong>Does the count match the URLs shown?</strong> A claim about most of your pages should
be accompanied by the pages.</li>
<li><strong>Is a tag container present?</strong> If so, treat any "no analytics" claim as
unverified rather than false, and check what the container is configured to load.</li>
<li><strong>Open your own dashboard.</strong> If it has data for yesterday, the finding is about
what a fetcher could see, not about whether you are measuring.</li>
</ul>

<h2>When the finding is real and worth acting on</h2>

<p>Two shapes deserve immediate attention, and neither is about the tool's name:</p>

<ul>
<li><strong>A money page with no tag while the rest of the site has one.</strong> This is the
genuine deployment gap, and it is usually one template — a checkout, a thank-you page, a landing
page built outside the main site.</li>
<li><strong>A funnel tagged inconsistently.</strong> One missing step in a sequence of four does
not cost a quarter of your visibility into it; it can cost the attribution for the whole
path.</li>
</ul>

<h2>The fixes that make it worse</h2>

<ul>
<li><strong>Installing a second analytics product to clear a finding.</strong> You now have two
sources of truth that will disagree, and a slower site, because a report did not recognise the one
you had.</li>
<li><strong>Removing a retired tag before the replacement is verified.</strong> The retired tag may
be the only thing still collecting. Confirm the new one is receiving data first.</li>
<li><strong>Adding tags to pages that already report through a container.</strong> Double-counting
is harder to notice than under-counting and corrupts every comparison you make afterwards.</li>
</ul>

<h2>How to pass this check without measuring anything</h2>

<p>Put a tag container on every page. Every page now carries something an audit recognises as
analytics infrastructure, the coverage number goes to full, and the container can be configured to
load nothing at all.</p>

<p>Which is the argument for the whole page: <strong>a tag in the HTML is evidence that a tag is in
the HTML.</strong> Whether anything is being recorded, whether it reaches a report you read,
whether the numbers are right — none of that is visible from outside, and an audit that implies
otherwise is selling you a conclusion it did not reach.</p>

<h2>Where this sits in an audit</h2>

<p>The registered check is <code>mar.analytics</code>, which covers whether analytics is installed.
For the tracking lane as a whole — what the six checks look for, what was found across real sites,
and what the lane deliberately does not do — see
<a href="/learn/marketing-tag-audit/">the marketing tag audit &rarr;</a>.</p>

<p>For the related habit of reading what a finding actually counted, see
<a href="/how-to/check-the-count-on-a-finding/">a finding's count is not decoration &rarr;</a>.</p>
"""
    return render(
        cat="how-to", slug="analytics-findings-name-the-tag",
        title="'You have no analytics' is a claim about a list",
        desc=("An audit checks a list of tag names, not whether you can see your traffic. Two "
              "cases where a site had analytics and was told it had none."),
        h1="'You have no analytics' is a claim about a list",
        crumb='<a href="/">Docket</a> / <a href="/how-to/">Fix it</a> / Analytics findings',
        body=body,
        faq=[
            ("My audit says I have no analytics but my dashboard has data. Why?",
             "Because it read the served HTML and looked for known tag names. If your tags load "
             "through a container at runtime, or your tool is not on its list, a static fetch "
             "cannot see them."),
            ("Does a tag manager mean I have analytics installed?",
             "No. A container collects nothing by itself. What it does mean is that absence "
             "cannot be concluded, because it can load a tag where a static fetch cannot see "
             "it."),
            ("Why did my audit only mention one analytics product?",
             "Some checks test for a specific product by name rather than for the category. If "
             "the finding names a tool you do not use and ignores the one you do, that is the "
             "failure."),
            ("Is 'analytics missing from most pages' the same as having no analytics?",
             "No, and the two need opposite work. Missing from some pages is a deployment gap in "
             "a template; missing everywhere means nothing is being measured at all."),
            ("Should I add a second analytics tool to clear the finding?",
             "No. You would gain two sources of truth that disagree and a slower site, because a "
             "report did not recognise the one you already had."),
        ],
    )


if __name__ == "__main__":
    print(analytics_findings())
