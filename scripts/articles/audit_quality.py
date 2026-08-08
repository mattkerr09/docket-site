#!/usr/bin/env python3
"""How to tell whether an audit tool is lying to you.

Every figure comes from site/_data/regressions.json through facts.py, which is
generated from Docket's own test suite. The counting rule is in the dataset and
it is deliberately conservative — a test file counts only if it names a
specific thing Docket got wrong.

The article has to teach, not confess. A reader should finish it able to
interrogate any tool's output, including this one's.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import facts as F  # noqa: E402
from render import N_CHECKS, render  # noqa: E402


def audit_quality() -> Path:
    body = f"""
<p class="lede">An SEO audit is a pile of confident sentences about your site, and the useful
question is which of them the tool actually checked. <strong>{F.regression_files()} of Docket's
{F.test_files()} test files</strong> — {F.regression_pct()}% — exist because Docket said
something that was not true, and every one of those mistakes belongs to a family you can look
for in any tool's report.</p>

<p>This is not a confession. It is the four questions worth asking of any finding, each of
which we learned by getting it wrong first.</p>

<h2>Did it look at what it says it looked at?</h2>

<p>Docket had eight checks that scanned the first 40 pages of a crawl and then reported "No
email capture anywhere on the site". On a site with fewer pages than that, it is true. On a
larger one it is a statement about every page the tool never opened.</p>

<p>The tell is a total claim with no number in it. "No X anywhere", "no Y found", "the site
has no Z" — those are claims about a population, and a tool that sampled cannot make them.
Compare with "12 pages have no title tag", which says exactly what it counted.</p>

<p><strong>What to do with it:</strong> when a report tells you something is missing site-wide,
find out how many pages it read. If that number is smaller than your site, the finding is a
hypothesis. Check one page it did not visit before you act.</p>

<h2>Do the headline and the detail agree?</h2>

<p>A Docket finding once read, in two consecutive lines:</p>

<pre><code>35 outbound links all point to github.com
74% of outbound links go to a single domain.</code></pre>

<p>Both came from the same two numbers. The word "all" was written into the title by hand and
was only ever true at 100%.</p>

<p>That is worse than sloppy. "All your outbound links point to one domain" is what an injected
spam footer looks like, and the fix text underneath told the reader their site might be
compromised and to go scanning templates. At the proportion the detail line actually reports,
that sends someone hunting for a hack which is not there.</p>

<p><strong>What to do with it:</strong> read the headline and the body of the same finding
against each other. They are computed from one set of numbers and there is no honest reason for
them to differ. When they do, believe the one with the arithmetic in it.</p>

<h2>Was anything actually observed?</h2>

<p>This is the sharpest one, and it took us three separate fixes to get right.</p>

<p>Point Docket at a domain that does not exist and it used to report three critical issues:
that robots.txt blocked Googlebot, that the site was not served over HTTPS, and that no pages
could be crawled. Only the third was true. There was no robots.txt and nothing was served,
because there was no site — the tool was reporting its own inability to see anything as a set
of defects in the thing it could not see.</p>

<p>The same shape had already been fixed twice before, by different routes: once when a
rate-limited crawl read a single error page and announced "no analytics installed anywhere on
the site" about a site that had analytics, and once for the page caps above. Three roads to
the same wrong sentence, and a guard built for one of them covered neither of the others.</p>

<p>A fourth road opened later, and it is the one worth watching for in any tool. Docket warns when
a page carries star-rating markup but shows no rating to visitors, because Google treats that as
grounds for a manual action that removes every rich result a site has. It was deciding this from
the served HTML. Point it at a shop that draws its star widget in JavaScript and it accused two
perfectly compliant product pages of the most serious thing the tool can say. Re-running with
rendering turned on cleared them completely.</p>

<p>Notice the shape: nothing was broken, nothing was degraded, the crawl was clean. The tool
simply answered a question about the rendered page using a document that was not the rendered
page. Now it will not make that accusation without rendered evidence, and where it has none it
says so and stays at a notice.</p>

<p><strong>What to do with it:</strong> when a tool reports an absence, ask what it saw. If the
crawl was blocked, rate-limited, or returned nothing, every "missing" finding in that report is
unsupported — not wrong necessarily, just unevidenced. And if a finding is about what a visitor
sees, ask whether the tool rendered the page or read the HTML. Those are different documents on
most modern sites, and only one of them is what Google judges.</p>

<h2>Would the tool have caught it, or did a person have to notice?</h2>

<p>Docket's byte-cap check once reported a major news site's title tag as sitting past
Googlebot's 2MB cutoff. It was reading an inline SVG icon label that said "Close icon"; the
real title was {F.size_largest()['critical_kb']} KB in and perfectly fine. That was caught one
edit before it went into <a href="/learn/googlebot-2mb-limit/">an article naming the site</a>.</p>

<p>What fixed the class was not the fix. It was a test that fails the build if the mistake
returns, and later a second kind of test that greps the source for the <em>shape</em> of the
mistake rather than the instance. That one earned itself immediately: after we had swept a file
by hand and fixed three findings that listed every crawled page as their URLs, the pattern test
named two more in the same file.</p>

<p><strong>What to do with it:</strong> ask a vendor what happens when they find a false
positive. "We fixed it" is a worse answer than "we fixed it and here is the test that fails if
it comes back", because the first one will happen again the next time somebody refactors.</p>

<h2>Where the older tools are better</h2>

<p>Directly: <a href="https://www.screamingfrog.co.uk/about/">Screaming Frog</a> describes
itself as an agency founded in 2010, and
<a href="/vs/sitebulb-alternative/">Sitebulb</a> has been at this for years too. Every mistake
above is the kind of thing that a very large number of other people's sites finds for you, and
they have had far more of those than Docket has.</p>

<p>So the honest position is not that Docket is more accurate than either. It is that Docket is
newer, which means it has more undiscovered false positives than they do, and the only useful
response to that is to publish the ones we find and make them fail the build. Every mistake in
this article is written up in the code that fixes it, with the site it happened to, and
{F.regression_files()} of the {F.test_files()} test files exist for no other reason.</p>

<h2>The version of this that matters most</h2>

<p>All of it gets more expensive the moment an audit is automated. Docket's CLI exits non-zero
on a critical finding so it can gate a deployment, which is genuinely useful and also means a
fabricated critical stops being an annoyance and starts failing somebody's build at six in the
evening.</p>

<p>The invented-criticals bug above was harmless for as long as nobody automated the tool. It
was found by testing the error path of the deploy gate, which is to say: <strong>the feature
that made the bug dangerous is also what exposed it.</strong> If you are about to wire any
audit tool into CI, run it first against a hostname that does not resolve and read what it
tells you. You will learn more about the tool in that one run than in ten against a healthy
site.</p>

<p><a class="btn" href="/download/">Download Docket</a></p>
"""
    return render(
        cat="learn", slug="audit-tool-accuracy",
        title="How to tell whether an audit tool is lying to you",
        desc=(f"Four questions to ask of any SEO finding, each learned by getting it "
              f"wrong. {F.regression_files()} of Docket's {F.test_files()} test files "
              f"exist because Docket said something untrue."),
        h1="How to tell whether an audit tool is lying to you",
        crumb='<a href="/">Docket</a> / <a href="/learn/">Learn</a> / Audit accuracy',
        body=body,
        published="2026-08-07",
        faq=[
            ("How do I know if an SEO tool's findings are accurate?",
             "Ask four things of any finding: how many pages it actually read before "
             "claiming something is missing site-wide, whether its headline and its detail "
             "report the same number, whether anything was observed at all when it reports "
             "an absence, and whether the vendor keeps a regression test when they fix a "
             "false positive."),
            ("What is a false positive in an SEO audit?",
             "A finding that is confidently stated and not true. The common causes are a "
             "tool sampling part of a site and reporting about all of it, a crawl that was "
             "blocked or returned nothing being read as evidence of absence, and pattern "
             "matches that fire on the wrong thing — an inline SVG label counted as the "
             "page title, for instance."),
            ("Why does a failed crawl produce false findings?",
             "Because 'we did not see it' and 'it is not there' are the same observation to "
             "a tool that is not careful. A rate-limited crawl that reads one error page "
             "has no evidence about analytics, phone numbers or anything else, but a naive "
             "check reports all of them as missing. Look for a line saying the crawl was "
             "degraded; if the report does not mention it, the silence is not reassurance."),
            ("Why does an SEO tool flag things that look fine in my browser?",
             "Usually because it read the HTML your server sent and you are looking at the "
             "page after JavaScript ran. On most modern sites those are different documents. "
             "Anything a tool says about what a visitor sees — visible prices, review stars, "
             "headings, body copy — is only trustworthy if it rendered the page. Ask whether "
             "the tool rendered, and if it did not, treat those findings as unconfirmed "
             "rather than wrong."),
            ("Should I run an SEO audit in CI?",
             "It is the strongest use of one, because it catches a noindex before it ships "
             "rather than weeks later on a traffic graph. Test it first against a hostname "
             "that does not resolve: a tool that invents findings about a site it never "
             "reached will fail your build with advice about a problem you do not have."),
        ],
    )


BUILDERS = [audit_quality]


def build_all() -> list[Path]:
    return [b() for b in BUILDERS]


if __name__ == "__main__":
    for p in build_all():
        print(p)
