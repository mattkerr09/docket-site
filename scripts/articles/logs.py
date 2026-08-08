#!/usr/bin/env python3
"""Log-file analysis — the difference between what Google could crawl and did.

Every number is real. There is no access log for this site to publish figures
from (it is served by GitHub Pages, which gives the owner no logs), so the
article does not pretend to have one: the measured content is Google's own
published crawler address ranges, counted from the primary source, plus a spot
check that Docket's verification accepts addresses drawn from them.

The spot check is six addresses. It is described as a smoke test and never as a
percentage, because six is not a rate.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import facts as F  # noqa: E402
from render import PRICE_STR, render  # noqa: E402


def log_file_analysis() -> Path:
    body = f"""
<p class="lede">A crawl tells you what a search engine <em>could</em> reach on your site; a
server log tells you what it actually fetched, how often, and what it wasted requests on. The
two disagree constantly, and the single most common mistake in reading a log is trusting the
user-agent — which is why Google publishes
<strong>{F.gbot_total_prefixes():,} IP prefixes</strong> across
{F.gbot_lists()} lists so you can check.</p>

<h2>The user-agent is a claim, not an identity</h2>

<p>Every line in your access log carries whatever user-agent the client chose to send.
"Googlebot" is a string, and scrapers send it constantly — partly to get past blocks, partly
because pretending to be a search engine is the easiest way to look legitimate in somebody
else's log file.</p>

<p>So a report that says "Googlebot fetched 40,000 pages last month" is really saying "40,000
requests claimed to be Googlebot". Those are different numbers and only one of them tells you
anything about your crawl budget.</p>

<p>There are two honest ways to resolve it. Google
<a href="https://developers.google.com/search/apis/ipranges/googlebot.json">publishes its
crawler ranges as JSON</a> — as of {F.gbot_measured()}, <strong>{F.gbot_prefixes()}</strong>
prefixes for Googlebot itself ({F.gbot_ipv4()} IPv4 and {F.gbot_ipv6()} IPv6), plus separate
lists for special-case crawlers and user-triggered fetches, {F.gbot_total_prefixes():,} in
total. Or you do the check Google
<a href="https://developers.google.com/search/docs/crawling-indexing/verifying-googlebot">documents</a>:
a reverse DNS lookup on the client IP, then a forward lookup on the hostname it returns, and
the original address has to come back.</p>

<p>The second step is the one people skip, and skipping it defeats the whole exercise. A PTR
record is set by whoever controls the address block, so anyone can make their IP claim to be
<code>crawl-something.googlebot.com</code>. Only resolving that name <em>back</em> proves it.
Docket does both, and there is a test that fails if the forward lookup is ever removed.</p>

<p>Docket's verification was spot-checked against {F.gbot_spot_size()} addresses taken from
Google's published Googlebot ranges — addresses that are Googlebot by Google's own definition
— and accepted {F.gbot_spot_verified()} of {F.gbot_spot_size()}. That is a smoke test against
real DNS rather than a rate; six addresses cannot be turned into a percentage and this page is
not going to pretend otherwise.</p>

<h2>What the log tells you that a crawl cannot</h2>

<p>Run <code>docket logs access.log --url https://example.com</code> and it crawls the site as
well, then reports the two ways the sets disagree.</p>

<p><strong>Pages Google fetched that the crawl never found.</strong> Orphans with no internal
link pointing at them, URLs you retired that Google is still retrying, pages that exist only in
the sitemap. Each is a page a crawler alone would never show you, because a crawler starts at
the homepage and follows links.</p>

<p><strong>Pages you link to that Google did not fetch.</strong> Careful here, and Docket prints
the caveat next to the number: a log covers a period. Absence from one week of logs means
Google did not fetch that page in that week. It does not mean Google cannot see it, and a tool
that lets you read it that way is setting you up to go fixing a problem you do not have.</p>

<p>And the response codes Google actually received. Every redirect and every 404 in that list
is a request spent on your site that returned nothing indexable — the clearest measure of
wasted crawl budget there is, and it is measured rather than modelled.</p>

<h2>Where the dedicated tool is better</h2>

<p>Screaming Frog sells a
<a href="https://www.screamingfrog.co.uk/log-file-analyser/">Log File Analyser</a> as a separate
product, $139 per year with a free tier capped at 1,000 log events. It is a much deeper tool
than what Docket does: a real interface for exploring the data, saved projects, imports that
handle far more formats, and analysis over time rather than a single comparison. If log
analysis is a regular part of your work, buy it — it is built for that and Docket is not.</p>

<p>What Docket gives you is the one comparison that answers "is Google spending its time on my
important pages", included in the {PRICE_STR} one-time price rather than as a second annual
subscription. That is the whole claim, and it is deliberately narrow.</p>

<h2>What Docket deliberately does not do here</h2>

<p>It reads Common and Combined format, and gzip. Anything else is counted as unparsed and
reported as a number, because a parser that quietly skips a third of a file produces
confident-looking statistics about the rest. It does not follow sessions, does not chart
anything over time, and does not store your logs — it reads the file, prints, and exits.</p>

<p>It also does not do reverse DNS unless you ask. <code>--verify</code> is a lookup per
distinct address, so it is off by default and everything says "claiming to be Google" until
you turn it on.</p>

<p><a class="btn" href="/download/">Download Docket</a></p>
"""
    return render(
        cat="learn", slug="log-file-analysis",
        title="Log file analysis: what Googlebot fetched, not what it could",
        desc=(f"Google publishes {F.gbot_total_prefixes():,} crawler IP prefixes because a "
              f"user-agent proves nothing. How to read an access log honestly, and where "
              f"the dedicated tool beats this one."),
        h1="Log file analysis: what Googlebot actually fetched",
        crumb='<a href="/">Docket</a> / <a href="/learn/">Learn</a> / Log file analysis',
        body=body,
        published="2026-08-08",
        faq=[
            ("How do I know if it was really Googlebot in my logs?",
             "Not from the user-agent, which is a header anybody can send. Either check the "
             "client IP against Google's published crawler ranges — "
             f"{F.gbot_total_prefixes():,} prefixes across {F.gbot_lists()} lists as of "
             f"{F.gbot_measured()} — or do a reverse DNS lookup on the IP followed by a "
             "forward lookup on the hostname it returns, confirming the original address "
             "comes back. The second step matters: a PTR record is set by whoever controls "
             "the address block, so a reverse lookup alone proves nothing."),
            ("What can a server log tell me that a crawl cannot?",
             "Which pages a search engine actually fetched and how often, which is a "
             "different question from which pages it could reach. That surfaces orphan pages "
             "with no internal links, retired URLs still being retried, and the share of "
             "requests that returned a redirect or an error — crawl budget spent on nothing "
             "indexable."),
            ("If a page is missing from my logs, can Google not see it?",
             "No, and treating it that way sends you fixing a problem you may not have. A log "
             "covers a period. A page absent from one week of logs was not fetched that week; "
             "it may be crawled rarely because it changes rarely. Look for it across a longer "
             "window before concluding anything."),
            ("Does Docket replace a dedicated log file analyser?",
             "No. Screaming Frog's Log File Analyser is a separate product at $139 per year "
             "and is much deeper — a real interface, saved projects, more formats, analysis "
             "over time. Docket does one comparison, log against crawl, included in its "
             "one-time price. If log analysis is a regular part of your work, the dedicated "
             "tool is the right purchase."),
        ],
    )


BUILDERS = [log_file_analysis]


def build_all() -> list[Path]:
    return [b() for b in BUILDERS]


if __name__ == "__main__":
    for p in build_all():
        print(p)
