#!/usr/bin/env python3
"""Live inspection and request identification are different tests."""
from __future__ import annotations

import json
from pathlib import Path

from comparisons import source_link
from real_questions_comparisons import READ, answer_source, note
from render import DATA, _human_date, render

INSPECTION = "https://support.google.com/webmasters/answer/9012289"
VERIFY = "https://developers.google.com/crawling/docs/crawlers-fetchers/verify-google-requests"
RANGES = "https://developers.google.com/static/crawling/ipranges/"
# Counted in the supplied live readings: name, readable label, total, IPv4, IPv6.
CREATED = "19 November 2026"
PREFIXES = (
    ("common-crawlers", "Common crawlers", 317, 170, 147),
    ("special-crawlers", "Special crawlers", 272, 136, 136),
    ("user-triggered-fetchers", "User-triggered fetchers", 1088, 544, 544),
    ("user-triggered-fetchers-google", "Google-controlled user-triggered fetchers", 504, 252, 252),
    ("user-triggered-agents", "User-triggered agents", 20, 12, 8),
)


def build() -> Path:
    rows = ''.join(
        f'<tr><th scope="row">{label}</th><td>{total:,}</td><td>{v4}</td><td>{v6}</td>'
        f'<td>{source_link("Range source", RANGES + name + ".json")}</td></tr>'
        for name, label, total, v4, v6 in PREFIXES)
    old = json.loads((DATA / "googlebot.json").read_text())
    common = PREFIXES[0][2]
    body = f"""
<p id="measured-answer">For a Googlebot test or Googlebot tester, start with Google's URL Inspection live test in Search Console: its documented fetcher is <q>Google-InspectionTool</q>.
{source_link("Google's live-test guide", INSPECTION)} says the test checks access for indexing, not whether the page will be indexed.
For identifying a visitor, our count of Google's published {source_link("common crawler ranges", RANGES + "common-crawlers.json")} found {common} prefixes; that count is not a page-access test.</p>
{note("rq-google-live")}
{note("rq-google-ranges")}

<h2>First choose which question you are asking</h2>
<dl>
<dt>Can Google's inspection fetcher read this page now?</dt>
<dd>Use the URL Inspection live test in Search Console.</dd>
<dt>Was a request in my logs really from Google's crawler?</dt>
<dd>Verify the visitor's IP address using DNS or the published ranges.</dd>
<dt>What did our own range check establish?</dt>
<dd>How many published prefixes each list contained on the day it was read.</dd>
</dl>
<p>These checks have different inputs. An inspection starts with a page address. A visitor
check starts with an IP address from a log. A count of ranges starts with a published list.
Keep that distinction beside the result so you do not answer the wrong question.</p>

<h2>Run Google's live page test</h2>
<ol>
<li>Open URL Inspection in Search Console and enter the page you want to inspect.</li>
<li>Run the live test and read the access result for that URL.</li>
<li>Use the live test's rendered screenshot when you need to inspect what was rendered.</li>
</ol>
<p>Google's guide says: <q>The live URL test only confirms if Google-InspectionTool can access
your page for indexing.</q> A screenshot is available only in a live test. An accessible page
is not a promise that it will enter the index. These are the limits stated in
{source_link("Google's URL Inspection documentation", INSPECTION)}.</p>
{note("rq-google-live")}

<h2>Identify a visit from its IP address</h2>
<p>{source_link("Google's verification guide", VERIFY)} gives a DNS procedure: reverse lookup
the visiting IP, check that the returned name is in googlebot.com, google.com or
googleusercontent.com, then look that name up forwards and confirm it returns the original IP.
The second lookup is part of the check, not an optional extra.</p>
<p>The guide also allows matching the IP against the published crawler and fetcher ranges.
They use CIDR notation, so test membership in a range rather than comparing the IP as a text
string. Choose the crawler or fetcher list that matches the kind of request you are checking.</p>
{note("rq-google-ranges")}

<h2>What we counted on 20 November 2026</h2>
<p>We fetched each published list, counted its prefix entries, and counted entries marked IPv4
and IPv6 separately. Each list's own creation date was {CREATED}. These are counts of
network prefixes, not individual IP addresses and not visits to your site.</p>
<div class="wrap-tbl"><table>
<caption>Published Google crawler and fetcher ranges, counted on {READ}</caption>
<thead><tr><th scope="col">List</th><th scope="col">Prefixes</th><th scope="col">IPv4</th><th scope="col">IPv6</th><th scope="col">Source</th></tr></thead>
<tbody>{rows}</tbody></table></div>
{note("rq-google-ranges")}

<h2>Our earlier DNS check had a narrower purpose</h2>
<p>On {_human_date(old["measured"])}, Check Engine's recorded spot check took one address from each of the
first few published common-crawler ranges. All {old['spot_check_verified']} of the
{old['spot_check_size']} addresses passed our reverse-then-forward DNS check. That is a small
check of our verification code against real DNS. It is not a success rate for all Googlebot
addresses, and it did not fetch your page.</p>
<p>The saved range counts and the spot check are described in our
<a href="/learn/log-file-analysis/">log file analysis guide</a>. A successful local fetch is
still a result from the client that made it. Use Google's own live inspection when your
question is what its inspection fetcher can access today.</p>
"""
    return render(
        cat="how-to", slug="test-a-page-as-googlebot",
        title="Googlebot tester: test a page or verify a visit",
        desc="Use Google's URL Inspection live test for a page, then DNS or published ranges to identify a Googlebot visit. Dated counts and clear limits.",
        h1="Googlebot tester: test a page or verify a visit",
        crumb='<a href="/">Check Engine</a> / <a href="/how-to/">Fix it</a> / Googlebot test',
        body=body, published="2026-11-20",
        faq=[
            ("Is the live inspection fetcher named Googlebot in Google's guide?", answer_source(
                "The guide names Google-InspectionTool. Use that name when describing what the live access result establishes.", "Live-test documentation", INSPECTION)),
            ("Is a reverse DNS name the whole Googlebot visit check?", answer_source(
                "No. Google says to check the returned domain and run a forward lookup to confirm the original IP. Matching the IP against the published ranges is another documented method.", "Request verification", VERIFY)),
            ("Do the published prefix counts tell me how often Google visited?",
             "No. They count entries in Google's published range lists on the date read. They contain no request history for your site. Use your server's records to count visits."),
            ("Does our October DNS spot check prove a page can be fetched?",
             "No. It checked address verification against real DNS. It did not test page access, and its small sample cannot be presented as a general success rate."),
        ],
    )
