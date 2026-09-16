#!/usr/bin/env python3
"""Index coverage — what Docket can and cannot tell you about being indexed.

The feature page for the index-coverage connector
(`backend/seo_engine/connectors/index_coverage.py` in the app repo). Every
limitation the connector encodes is stated here, because a table that prints
"missing" for a page nobody could look up is worse than no table.

Sources, each read at its own canonical home on the date below:
  * Google's URL Inspection reference and its published per-site quota;
  * Microsoft's GetCrawlStats reference;
  * IndexNow's own FAQ, for who receives a submission and for the sentence
    saying a submission is not an indexing guarantee.

⚠️ THE PARTICIPANT LIST CAME FROM THE VENDOR, AND OUR TWO INTERNAL RECORDS OF
IT WERE BOTH WRONG. Our submitting tool's docstring named four engines and the
pre-registered scope named four different ones; IndexNow's own FAQ lists the
endpoints below. Neither of ours matched. That is why the connector hardcodes
no list and this page cites one.

⚠️ THE SITE'S PROMISE IS NOT MINE TO CHANGE. "No account, no tracking, your
audits stay on this Mac" is a promise Matthew made and only he edits. This page
therefore states plainly what this one feature sends and to whom, and changes
no wording anywhere else.

No typed figures or dates: the quota, the ceiling and the read date are module
constants interpolated below, and the body contains no brace characters.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from render import render  # noqa: E402

GOOGLE_DOCS = ("https://developers.google.com/webmaster-tools/v1/"
               "urlInspection.index/inspect")
GOOGLE_LIMITS = "https://developers.google.com/webmaster-tools/limits"
GOOGLE_QPD = "2,000"
GOOGLE_QPM = "600"

BING_DOCS = ("https://learn.microsoft.com/en-us/dotnet/api/"
             "microsoft.bing.webmaster.api.interfaces.iwebmasterapi.getcrawlstats")

INDEXNOW_FAQ = "https://www.indexnow.org/faq"
#: The endpoints IndexNow's own FAQ lists, in its order. Ours are not the source.
INDEXNOW_ENGINES = "Amazon, Bing, Naver, Seznam.cz, Yandex and Yep"

#: Brave's search API returns twenty results a page and refuses offsets above
#: nine, so this many results is the whole enumerable window for one host.
BRAVE_WINDOW = "200"

READ_ON = "16 September 2026"


def index_coverage() -> Path:
    body = f"""
<p class="lede">You published a page. Is it actually in Google? Is Bing aware of the site at
all? Did anything ever get told the page changed? A crawler cannot answer any of that by
reading your HTML, because none of it is a property of your page — it is a property of
somebody else's index.</p>

<p>Docket answers it by asking each engine directly, with your own credentials, and the
interesting part of the answer is where it refuses.</p>

<h2>What each engine can actually tell you</h2>

<p>These are not equivalent sources dressed up as one number. Each one supports a different
claim, and the row says which.</p>

<h3>Google, per URL</h3>

<p>The <a href="{GOOGLE_DOCS}">URL Inspection API</a> returns a per-URL verdict and a last-crawl
date for a property you have verified in Search Console. It is the only engine here that
answers per page, and it can, because the
<a href="{GOOGLE_LIMITS}">published quota</a> is {GOOGLE_QPD} inspections per site per day and
{GOOGLE_QPM} per minute — enough for a whole site, every day.</p>

<p>Docket reads the verdict, which is a documented enumeration, and shows Google's own summary
sentence beside it without interpreting it. That sentence is a plain string in the API, it has
no published list of values, and the request takes a language code — so the same state arrives
in different words for different accounts. Matching on the words would report an indexed page
as missing the day Google rewrote them, or for anyone not working in English. Only the two
decisive verdicts become a claim; the rest read as unknown rather than being guessed into a
finding.</p>

<h3>Bing, for the site — not for the page</h3>

<p>Bing's <a href="{BING_DOCS}">crawl statistics</a> give a count of pages in its index for the
whole site, one row per day. There is no per-page column, and there is not going to be one:
the per-URL call throttles after a few dozen requests, so a per-page Bing column would be blank
or wrong on any site large enough to care. The row says site-level, and carries the date of the
reading, because a count without its date is how a number goes stale while everything on screen
agrees with it.</p>

<p>It is worth showing at all because Bing's index is not only Bing's. Several other search
surfaces are served from it, which is also why Docket does not print the same figure again under
their names.</p>

<h3>Brave, for the site, with the ceiling printed</h3>

<p>Brave can be enumerated by listing the host's results a page at a time, but its API stops at a
fixed offset — about {BRAVE_WINDOW} results is the entire window that can ever be read for one
host. Past that point, "not in the results" and "past the end of what I was allowed to read" are
the same observation.</p>

<p>So beyond the window Docket reports blindness, not absence. It will never tell you a page is
missing from Brave when what actually happened is that nobody could look. A tool whose whole
promise is telling you where you are not indexed is exactly the wrong place to invent an
absence.</p>

<h3>IndexNow is your outbox, and it is labelled as one</h3>

<p>IndexNow is how a site announces that a URL changed, to
<a href="{INDEXNOW_FAQ}">the endpoints its FAQ lists</a> — {INDEXNOW_ENGINES}. Docket records
whether a URL was announced and when.</p>

<p>That is all it records. Announcing is not indexing, and IndexNow's own FAQ says a submission
"does not guarantee immediate indexing". In a table headed by the question "am I indexed", this
is the single most misreadable column on the page, so it never counts toward the answer. The
states it can report do not overlap with the index verdicts at all — it can say announced, or
not announced, and nothing else.</p>

<h3>AI crawlers, for the origin</h3>

<p>Docket already checks whether your server actually serves the AI crawlers, by asking it — see
<a href="/learn/ai-crawlers-and-sitemaps/">AI crawlers and your sitemap</a> and
<a href="/learn/does-noindex-stop-ai-crawlers/">does noindex stop AI crawlers</a>. That check
probes your home page once per crawler, which makes it an answer about the origin.</p>

<p>It is joined to this table rather than rebuilt, and it is joined as what it is. It does not
appear as a per-page verdict, because nothing about it was measured per page — and a column of
crawler names and status codes looks far more specific than it is.</p>

<h2>What this will not tell you</h2>

<ul>
<li><strong>Why Google has not indexed a page.</strong> It reports the verdict Google gives and
shows Google's own summary; it does not diagnose a decision made inside somebody else's
system.</li>
<li><strong>Per-page Bing or Brave state.</strong> Neither is available at a rate that would
survive a real site, and a column that is right on small sites and wrong on large ones is worse
than no column.</li>
<li><strong>Whether Yandex, Naver, Seznam or Yep indexed anything.</strong> Docket can announce
to them and read nothing back. Announcements are shown; state is not invented.</li>
<li><strong>A single "indexed everywhere" score.</strong> Four sources answering four different
questions do not average into one number, and a number that hides which engine said what is a
number you cannot act on.</li>
</ul>

<h2>Where your URLs go, stated plainly</h2>

<p>This is the one feature in Docket that talks to a search engine about your pages, so it should
be obvious what that means.</p>

<p><strong>Your URLs do go to Google and to Bing.</strong> That is not a side effect, it is the
feature: to ask whether Google has your page, Docket has to tell Google which page you mean. The
requests are made from your Mac, with credentials you supply, against properties you have
verified as yours. Nothing is routed through us, nothing about your site reaches us, and there is
no account with us to hold it. If you would rather not ask, the connector is a switch and the
rest of the audit is unaffected.</p>

<p>The credentials are yours and stay on your machine. Docket never ships a shared key for this:
a shared key would mean your URLs travelling under somebody else's identity, and a per-customer
bill with no ceiling.</p>

<h2>Where to start</h2>

<p>The reads that need no credentials work immediately. Google needs a Search Console property
you have verified; Bing needs its own key. You can run
<a href="/download/">Docket</a> against your site without either and still get the site-level
picture, then add the sign-in when you want the per-page column. What the rest of the audit
covers is on <a href="/learn/what-docket-checks/">what Docket checks</a>.</p>

<p class="small">Sources read on {READ_ON}: Google's URL Inspection reference and published
quota, Microsoft's crawl-statistics reference, and IndexNow's FAQ.</p>
"""
    return render(
        cat="learn", slug="index-coverage",
        title="Is your page actually indexed? How to check",
        desc=("Whether a page is in Google, Bing or Brave is a fact about their index, not "
              "your HTML. What Docket asks each engine, and where it refuses to guess."),
        h1="Checking whether your pages are actually indexed",
        crumb='<a href="/">Docket</a> / <a href="/learn/">Learn</a> / index coverage',
        body=body,
        faq=[
            ("Can Docket tell me if a specific page is in Bing?",
             "No, and no tool can do it reliably at scale. Bing's per-URL endpoint throttles "
             "after a few dozen calls, so a per-page column would be blank or wrong on any "
             "site big enough to need one. Docket shows Bing's site-level count with the date "
             "of the reading instead, and says that is what it is."),
            ("Does Docket send my URLs to Google?",
             "Yes, for the pages you ask it to inspect. There is no way to ask whether Google "
             "has a page without naming the page. The request goes from your Mac using your "
             "own Search Console sign-in against a property you verified, nothing is routed "
             "through us, and turning the connector off stops it entirely."),
            ("Why does a page say unknown instead of missing?",
             "Because nobody looked. Brave's API stops after a fixed number of results per "
             "host, and past that point an absence from the results is not evidence of an "
             "absence from the index. Reporting it as missing would invent a finding on every "
             "page past the cutoff of every large site."),
            ("Is submitting a URL through IndexNow the same as being indexed?",
             "No. IndexNow's own FAQ says a submission does not guarantee indexing. It records "
             "that you announced a change, which is a real and useful action, but it is your "
             "outbox rather than anyone's index. Docket labels it as a submission and never "
             "counts it toward whether a page is indexed."),
            ("Do I need an account with Docket for this?",
             "No. Docket has no accounts. This feature uses credentials you already have with "
             "Google and Bing, entered on your own machine, and the reads that need no "
             "credentials work without any sign-in at all."),
            ("Which engines receive an IndexNow submission?",
             "IndexNow's FAQ lists Amazon, Bing, Naver, Seznam.cz, Yandex and Yep as its "
             "endpoints. Docket does not keep its own copy of that list, because a list "
             "hardcoded in a tool goes quietly out of date while the tool keeps citing it."),
        ],
    )


BUILDERS = [index_coverage]


def build_all() -> list:
    return [b() for b in BUILDERS]


if __name__ == "__main__":
    print(index_coverage())
