"""When two findings count the same pages twice.

Promised on the how-to hub. Sourced from `schema.incomplete` in
`structured.py` — a different aspect of the same check used at 524, which
covered what an `@id` reference is. This page is about arithmetic and
explanation:

  * ONE FINDING PER TYPE, NOT ONE PER MISSING-FIELD COMBINATION. A shoe
    retailer's thirty-page crawl produced two findings with the same check id,
    the same fix, titles differing only by a number, and most pages listed
    under both — a total larger than the crawl.
  * THE EXPLANATION WAS A GUESS. "Why are there more blocks than pages" used to
    assert a listing or variant picker for every site; on one site none of the
    blocks was a listing, they were references.
  * THE EXPLANATION WAS GATED ON THE WRONG CONDITION. The reference sentence
    was withheld unless blocks outnumbered pages, so the ordinary one-stub-per-
    page shape never got it. The data was computed identically either way;
    only the printing differed.

⚠️ NO SITE OR VENDOR IS NAMED — third-party gate, and the standing rule not to
name vendors. The commerce platform is "a common commerce platform".

⚠️ MUST CROSS-LINK /how-to/schema-id-references/ RATHER THAN REPEAT IT. That
page owns what an `@id` is and when a dangling one is a real defect.

Numerals: none. Quantities spelled as words.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from render import render  # noqa: E402


def double_counting() -> Path:
    body = """
<p class="lede">A report lists two findings with the same title, the same fix and different
numbers. You add them up and the total is larger than the number of pages crawled. At that point
the useful question is not which number is right — it is what the tool split, and why.</p>

<h2>The same job, reported twice</h2>

<p>On a shoe retailer's crawl of about thirty pages, the report carried two entries with the same
check identifier and the same remedy, their titles differing only in a count of pages with
incomplete product markup. Most of the pages appeared under <em>both</em>. Add the two and you
have more pages in trouble than the crawl contained.</p>

<p>The cause was the grouping key. Findings were keyed on the type <em>and the list of missing
fields</em>, so one type split into as many findings as it had field combinations — and a common
commerce platform reliably produces two, because the main product block is missing one property
and the recommendation carousel is missing another.</p>

<p>The repair was one finding per type, with the combinations moved into the detail where they
inform without splitting the count. Two reasons, and the second is the better one:</p>

<ul>
<li><strong>Completing the markup is one job in one template.</strong> The reader is not going to
do it twice.</li>
<li><strong>The platform's own testing tool reports one verdict per type</strong>, so one finding
per type is also the shape of the thing being checked against.</li>
</ul>

<p><strong>A number a reader can immediately disprove costs more than the finding is worth.</strong>
The underlying problem was real; the sentence carrying it was not believable, and an unbelievable
sentence takes the believable ones down with it.</p>

<h2>The explanation that was written from a guess</h2>

<p>The same check answers a question readers ask constantly: why are there more markup blocks than
pages? The count is executed against your markup and is right. The <em>explanation</em> beside it
used to be a single sentence asserted for every site — that a listing or variant picker repeats
the type, so each copy is read separately.</p>

<p>On one site there were twice as many organisation blocks as pages and <strong>not one of them
was a listing.</strong> They were references pointing at a definition the page never provided. A
reader sent looking for a variant picker would have searched their templates for something that
was not there — and the actual repair is the opposite shape: <em>define the node once</em> rather
than de-duplicate copies.</p>

<p>The tool could tell the two apart from the data it already had. It simply was not looking.
⇒ <strong>A count can be computed while the sentence explaining it is assumed</strong>, and the
assumed half is the one nobody tests.</p>

<h2>The explanation gated on the wrong condition</h2>

<p>Sharper still, and the reason this is worth a page rather than a changelog line.</p>

<p>The sentence explaining that blocks were references was attached to the "more blocks than
pages" branch. So a site with exactly one reference per page — the ordinary shape, and by far the
commonest — was told only that a property was missing, and never that its blocks were pointers at
all.</p>

<p>A hotel group had three pages, three blocks, every one a reference to a definition that did not
exist on the page. The explanation was withheld because three is not more than three. The other
site received it only because it happened to carry two stubs per page. <strong>The underlying data
was computed identically in both cases; only the printing differed.</strong></p>

<p>That is a class of bug worth recognising in any report you read: <strong>an explanation
attached to the wrong condition is invisible, because the people who most need it are exactly the
ones who never see it.</strong></p>

<h2>Reading a report whose numbers do not add up</h2>

<ul>
<li><strong>Add the counts.</strong> If the total exceeds the pages crawled, findings are
overlapping and at least one grouping is wrong.</li>
<li><strong>Compare the URL lists.</strong> Two findings naming the same pages are one finding
with a split key, not two problems.</li>
<li><strong>Check whether the fixes are identical.</strong> Same remedy, same check, different
number is the signature.</li>
<li><strong>Treat the explanation and the count differently.</strong> The count was probably
measured. The sentence saying <em>why</em> may have been written once, for a different kind of
site, and never revisited.</li>
</ul>

<h2>When the split is legitimate</h2>

<p>Not every division is a defect, and two are worth keeping:</p>

<ul>
<li><strong>Different types.</strong> Incomplete product markup and incomplete organisation
markup are genuinely different jobs in different templates.</li>
<li><strong>Different severities.</strong> A missing required property and a missing recommended
one deserve separate treatment even on one type, because only one of them costs you eligibility
for anything.</li>
</ul>

<p>What is not legitimate is splitting by the <em>combination of things missing</em>, because that
is a property of the data rather than of the work.</p>

<h2>The fixes that make it worse</h2>

<ul>
<li><strong>Working both findings as separate tickets.</strong> The second is the first, and you
will "fix" a template that was already corrected.</li>
<li><strong>Adding the missing property to the reference blocks.</strong> See
<a href="/how-to/schema-id-references/">an @id is a pointer, not a definition &rarr;</a> — that
duplicates a definition rather than completing one.</li>
<li><strong>Hunting for a listing because the report mentioned one.</strong> If your blocks are
references, there is no listing to find.</li>
</ul>

<h2>How the count gets smaller without anything improving</h2>

<p>Crawl fewer pages. Every page-count finding shrinks, the report reads better, and the templates
are unchanged — which is the standing hazard of any measure expressed as a number of pages rather
than a number of templates. For the general version of that, see
<a href="/how-to/read-findings-that-blame-the-whole-site/">when a finding blames the whole
site &rarr;</a>.</p>

<h2>Where this sits in an audit</h2>

<p>The registered check is <code>schema.incomplete</code>, which covers incomplete structured data.
For what an <code>@id</code> reference actually is, and when one is a genuine defect rather than a
misread, see <a href="/how-to/schema-id-references/">an @id is a pointer, not a
definition &rarr;</a>. For the number attached to any finding and what it feeds, see
<a href="/how-to/check-the-count-on-a-finding/">a finding's count is not decoration &rarr;</a>.</p>
"""
    return render(
        cat="how-to", slug="findings-that-double-count",
        title="When two findings count the same pages twice",
        desc=("Two entries, one check, overlapping pages and a total bigger than the crawl. What "
              "an audit split, and why the site's real job is one."),
        h1="When two findings count the same pages twice",
        crumb='<a href="/">Docket</a> / <a href="/how-to/">Fix it</a> / Double counting',
        body=body,
        faq=[
            ("My audit lists two findings with the same title and different numbers. Why?",
             "Almost always a grouping key that includes something other than the job. If the "
             "fixes are identical and the URL lists overlap, it is one finding split in two."),
            ("The page counts add up to more than my site has. Which is right?",
             "Neither, on its own. Overlapping findings double-count the pages they share, so "
             "compare the URL lists rather than trusting either total."),
            ("Should incomplete markup be one finding per type or per missing field?",
             "Per type. Completing the markup is one job in one template, and the validator you "
             "will check against reports one verdict per type."),
            ("Why does my report say a listing repeats my markup when I have no listing?",
             "Because the explanation may be asserted rather than measured. A count is usually "
             "computed from your markup; the sentence explaining it can be a guess written for a "
             "different kind of site."),
            ("Can I trust a finding whose explanation is wrong?",
             "Treat the two separately. The measured part is often right and the narrative around "
             "it weaker — but an explanation you can disprove will cost the finding its "
             "credibility whether or not it deserves that."),
        ],
    )


if __name__ == "__main__":
    print(double_counting())
