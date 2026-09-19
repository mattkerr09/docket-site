"""The gap between a checker's categories produces no finding at all.

Promised on the how-to hub. Sourced from `indexability.py`, registered check
`index.broken`:

  * ⚠️ A STATUS IN THE FOUR-HUNDRED RANGE FELL BETWEEN EVERY BUCKET AND NOTHING
    REPORTED IT. The buckets were server errors, not-found/gone, the two
    refusal statuses, and no response at all. Everything else in that range was
    simply not asked about, so a page on an audited site produced NO FINDING
    FROM ANY REGISTERED CHECK. Not a wrong claim — nothing at all, which is the
    kind nobody can argue with.
  * Found while proving that widening the EXTERNAL link rule had not silenced
    the internal one — not from a report, because nobody complains about
    silence.
  * The new finding's own words: these URLs are linked from the site and the
    server refused the request rather than saying the page is gone, "so it will
    not show as a 404 in any report that only counts those". Remedy: read your
    own log line; return a not-found or gone status if it should not exist, fix
    what rejects it if it should.
  * The deliberate silence: `REFUSED` statuses stay excluded because that set is
    what this codebase has already decided is a statement about the CRAWLER
    rather than the site, and the crawl-quality gate owns it.

⚠️ NUMERALS. `verify_numbers.py` allows 200/401/403/404/405/406/429/451/503
ONLY. The status at the centre of this page is NOT allowed, nor is the
permanently-gone one — both are described in words throughout. 404 and 429 are
used because they are allowed.

⚠️ NO SITE IS NAMED — third-party gate.

⚠️ /how-to/pages-an-audit-could-not-reach/ (519) owns the four causes reported
as one unreachable page. This page is about a status reported as NOTHING, and
cross-links rather than restating.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from render import render  # noqa: E402


def silent_gap() -> Path:
    body = """
<p class="lede">Most complaints about an audit are that it said something wrong. This one is about
a report that said nothing — a page on the audited site that no check mentioned, in any section, at
any severity. A wrong sentence you can argue with. A missing one you cannot even find.</p>

<h2>The status that belonged to no category</h2>

<p>Broken-page checks work by sorting responses into buckets. Ours had four: server errors;
not-found and permanently-gone; the two statuses that mean the request was refused; and no response
at all.</p>

<p>That is a sensible list and it has a hole in it. The rest of the four-hundred range — the
statuses that mean the server understood the request and rejected it, that the request took too
long at the application, that it conflicted with something, that its content type was not accepted
— <strong>was never asked about.</strong></p>

<p>So a URL on an audited site, linked from its own pages, answered with one of those, and the
report contained <strong>no finding from any registered check</strong>. Not a wrong claim. Not a
low-severity note. Nothing.</p>

<h2>How it was found, which is the whole point</h2>

<p>Not from a report, and not from anybody telling us. It turned up while checking that a change to
the rule for <em>external</em> links had not accidentally silenced the rule for internal ones — a
neighbouring question, asked for a different reason.</p>

<p><strong>Nobody complains about silence.</strong> A reader can send you a sentence that is wrong,
quote it back and ask what happened. There is no sentence to send about a page that was never
mentioned, and no reason to suspect one exists. That is the same shape as
<a href="/how-to/when-a-fix-creates-a-false-negative/">a guard that quietens a true finding
&rarr;</a>, arriving from the opposite direction: there, a fix created the silence; here, nobody
had written the category at all.</p>

<h2>What that page actually was</h2>

<p>It matters that this is not an exotic case. A URL that your own server rejects is usually one of
three ordinary things: a rule that refuses a request carrying a particular query string or header, a
URL the application cannot parse, or a size limit.</p>

<p>And the consequence is specific. <strong>It is not a 404, so every report that counts 404s shows
you as clean</strong> — while a search engine asking for the same URL gets the same refusal your
visitor did. The page is linked, reachable in principle, and returns nothing usable to anyone.</p>

<p>The remedy is the unglamorous one: request the URL yourself and read your server's own log line
for it. If the URL should not exist, return a not-found or gone status so it is understood as gone.
If it should exist, fix whatever is rejecting it. Either is better than a refusal, which tells a
search engine nothing at all.</p>

<h2>The silences that are correct</h2>

<p>Not every gap should be filled, and this is where a checker earns its keep.</p>

<p>Statuses meaning the crawler itself was turned away stay out of this deliberately. A 429 arriving
during a crawl is the audit being asked to slow down — a fact about the request, not about the
page — and a different part of the product owns that:
<a href="/how-to/tell-a-rate-limit-from-a-block/">telling a rate limit from a block &rarr;</a>.</p>

<p><strong>A check that reports everything has not decided anything.</strong> The question is never
"does this tool have a category for every case" but "does it know which cases it has decided not to
speak about" — and whether it will tell you.</p>

<h2>You cannot audit a report for what it does not say</h2>

<p>This generalises past our tool and past this status.</p>

<p>Every check in every auditing product is a condition somebody thought of. The spaces between
those conditions are invisible by construction: they do not show up as zeroes, or as a "nothing
found" row, or as a warning that a case went unclassified. They show up as an absence you have no
way to see, in a document whose whole purpose is to tell you what is there.</p>

<h2>Finding your own gaps</h2>

<ol>
<li><strong>Get the set of status codes your site actually returns</strong> — from your server logs,
your CDN dashboard, or a crawl export — and compare it against the statuses your report names.
Anything in the first list and not the second is a blind spot.</li>
<li><strong>Ask any tool what it does with a status it has no category for.</strong> The good answer
is that it says so. The common answer is nothing.</li>
<li><strong>Test a URL with a query string on it.</strong> Rejection rules live at that boundary
more often than anywhere else, and query-string URLs are exactly the ones a crawl reaches by
following links rather than by reading a sitemap.</li>
<li><strong>Check the count, not just the list.</strong> If your report says how many pages it
crawled and the categories beneath it add up to fewer, the difference is being carried by nothing.</li>
</ol>

<h2>When this matters</h2>

<p>A rejected URL is linked from your own site, so visitors reach for it and get an error page that
is not a 404 and usually says nothing useful. Search engines reach for it too, and record a
refusal — which is neither an invitation to try again nor a statement that the page is gone. The
cost is small per URL and it compounds quietly, because the one report that would have told you
counts only the statuses everyone counts.</p>

<h2>The fixes that make it worse</h2>

<ul>
<li><strong>Blocking the URL at the edge so it stops appearing.</strong> The link on your site still
points at it and the visitor still arrives somewhere useless.</li>
<li><strong>Redirecting every rejection to the homepage.</strong> You have replaced a clear failure
with a page that answers successfully and does not contain what was asked for — a worse problem
with a friendlier status code.</li>
<li><strong>Turning rejections into not-found responses with a catch-all rule.</strong> That is the
right answer for URLs that should not exist and it hides the ones that should, which were the
reason to look.</li>
</ul>

<h2>There is no way to game this one</h2>

<p>Most findings can be cleared without improving anything, and this page usually ends by showing
you how. Not here: the finding appears only when your own server refuses a URL your own site links
to, and the only way to quiet it is to stop refusing or to say plainly that the page is gone.
<strong>Both of those are the actual fix.</strong></p>

<p>Which is worth noticing about a report in general. A finding you can clear dishonestly is
measuring a proxy. A finding you cannot is measuring the thing.</p>

<h2>Where this sits in an audit</h2>

<p>The registered check is <code>index.broken</code>, which covers pages answering with an error.
For the several different causes that once came out as one unreachable page, see
<a href="/how-to/pages-an-audit-could-not-reach/">pages an audit could not reach &rarr;</a>.</p>
"""
    return render(
        cat="how-to", slug="when-a-report-says-nothing-at-all",
        title="When a report says nothing at all",
        desc=("A page on an audited site answered with a status that fitted none of the buckets, "
              "so no check said anything — and silence is the one thing a report cannot show "
              "you."),
        h1="When a report says nothing at all",
        crumb='<a href="/">Docket</a> / <a href="/how-to/">Fix it</a> / Silent gaps',
        body=body,
        faq=[
            ("Why would an audit not mention a broken page at all?",
             "Because broken-page checks sort responses into categories, and a status that fits "
             "none of them produces no finding. It does not appear as a zero or as an "
             "unclassified row — it appears as nothing, which is why nobody reports it."),
            ("My server returns a rejection status on some URLs. Is that a 404?",
             "No, and that is the problem. A refusal means the server understood the request and "
             "declined it, so every report that counts only 404s shows you as clean while a "
             "search engine asking for the same URL gets the same refusal your visitor did."),
            ("What causes a linked URL to be rejected by my own server?",
             "Usually a rule that refuses a request carrying a particular query string or "
             "header, a URL the application cannot parse, or a request size limit. Request one "
             "yourself and read your server's own log line for it."),
            ("Should an audit have a category for every possible status?",
             "Not necessarily. Statuses meaning the crawler was turned away are facts about the "
             "request rather than the page, and a good tool excludes them deliberately and says "
             "so. The test is whether it knows which cases it decided not to speak about."),
            ("How do I find what my audit is not telling me?",
             "Compare the status codes your server logs or CDN actually returned against the "
             "categories your report names, and check whether the per-category counts add up to "
             "the number of pages crawled. The difference is being carried by nothing."),
        ],
    )


if __name__ == "__main__":
    print(silent_gap())
