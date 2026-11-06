#!/usr/bin/env python3
"""/best/screaming-frog-alternatives/: Screaming Frog alternatives for Mac and Windows.

Job 1 of the CEO's catch-up list (2026-11-06, plan: ~/ops/launch/AI-RECOMMEND-PLAN-2026-11-06.md section 4). When
Perplexity was asked "best desktop SEO audit tool for Mac or Windows you buy once, a Screaming Frog alternative" it
answered from ten list articles and Docket was in none of them. This is the same format, written the way the rest of
this site is: every fact about a rival is a row of data/screaming-frog-alternatives.json, read from the vendor's own
pages on the date stored with it (comparisons.py registers that file as the claim set "sf-alternatives", so the
competitive-claims and freshness gates check it), and nothing about a rival is typed here.

The demand this page answers is written down in ~/ops/research/marketing-2026-11-04/docket.md: the search "screaming
frog alternative" is about 880 a month at difficulty 21 per cent (a keyword tool), with "screaming frog alternatives"
and "alternative to screaming frog" beside it. Docket's own Search Console had 0 impressions for the head term in
the 28 days to 5 November (~/ops/research/views-10x-2026-11-05.md).

First-hand substance: Docket's own run (data/free-run.json, made by the shipped app). The page says in plain words that
the other tools were not run, so it never implies a speed or a finding it did not measure.

The /vs/ pages are not touched: they sit in a title test until 1 December 2026.
"""
from __future__ import annotations

import html
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from render import (BNPL_INSTALMENT, MAC_HW, MACOS, N_CHECKS, PRICE, PRICE_STR, REFUND_DAYS, WINDOWS,  # noqa: E402
                    buy_block, render, speed_words)

import comparisons  # noqa: E402

_ROOT = Path(__file__).resolve().parent.parent.parent
_DATA = json.loads((_ROOT / "data" / "screaming-frog-alternatives.json").read_text(encoding="utf-8"))
_TOOLS = {t["slug"]: t for t in _DATA["tools"]}
_READ = comparisons.CHECKED_HUMAN["sf-alternatives"]
#: The audit of our own site that the figures below are made from (docket-app scripts/shot_free.mjs).
_RUN = json.loads((_ROOT / "data" / "free-run.json").read_text(encoding="utf-8"))
_LIMITS = json.loads((_ROOT / "data" / "limits.json").read_text(encoding="utf-8"))

_WORDS = {1: "one", 2: "two", 3: "three", 4: "four", 5: "five", 6: "six", 7: "seven", 8: "eight"}


def _usd(n: int) -> str:
    return f"${n:,}"


def _cap(s: str) -> str:
    """Upper-case the first letter only: str.capitalize() would lower-case Windows and Mac."""
    return s[:1].upper() + s[1:]


def sf_alternatives() -> Path:
    esc = html.escape
    sf, sb, ps, np_, scr, lc = (_TOOLS[k] for k in ("screaming-frog", "sitebulb", "seo-powersuite",
                                                    "netpeak-spider", "scrutiny", "librecrawl"))
    others = len(_TOOLS)                          # every tool in the data is an alternative or Screaming Frog itself:
    #                                               five alternatives, with Docket the sixth, and Screaming Frog
    seven = len(_TOOLS) + 1                       # the tools in the table, Screaming Frog and Docket included
    ui_pages = _LIMITS["ui_default_pages"]
    minutes = _LIMITS["wall_clock_minutes"]
    # The sentences below depend on the order of these prices. If a price change breaks one, the build stops here
    # rather than publishing a sentence the table no longer supports.
    assert PRICE < sf["annual"] and PRICE < scr["once"], "a rival now costs less than Docket once: rewrite the prose"
    assert sb["annual"] < sf["annual"] < sb["annual_pro"], "Sitebulb's prices no longer straddle Screaming Frog's"
    assert lc["once"] == 0, "LibreCrawl is no longer free: the first answer on the page is wrong"

    docket_runs = (f"Mac ({MAC_HW}, {MACOS} or later) and 64-bit Windows" if WINDOWS
                   else f"Mac only: {MAC_HW}, {MACOS} or later")
    glance = [
        ("Screaming Frog SEO Spider", sf["runs_on"], sf["sold"], sf["free"], sf["urls"]),
        ("Sitebulb", sb["runs_on"], sb["sold"], sb["free"], sb["urls"]),
        ("SEO PowerSuite (WebSite Auditor)", ps["runs_on"], ps["sold"], ps["free"], ps["urls"]),
        ("Netpeak Spider", np_["runs_on"], np_["sold"], np_["free"], np_["urls"]),
        ("Scrutiny", scr["runs_on"], scr["sold"], scr["free"], scr["urls"]),
        ("LibreCrawl", lc["runs_on"], lc["sold"], lc["free"], lc["urls"]),
        ("Docket SEO", docket_runs,
         f"{PRICE_STR} once, or four payments of {BNPL_INSTALMENT}",
         "a full audit with no key: the score, the number of problems in each area and the most important one in full",
         f"{ui_pages} pages by default and {minutes} minutes, and both can be raised"),
    ]
    table = "\n".join(
        "<tr>" + f'<th scope="row">{esc(r[0])}</th>' + "".join(f"<td>{esc(c)}</td>" for c in r[1:]) + "</tr>"
        for r in glance)

    from pages import free_result_figure  # noqa: E402  (lazy: pages imports a great deal)
    free_figure = free_result_figure()
    body = f"""
<p class="lede">Screaming Frog's SEO Spider is the crawler the others are measured against, and it is free
up to {sf["free_cap"]} URLs. If you have outgrown that, or you want to pay a different way, there
are {_WORDS[others]} others worth a look: Sitebulb, SEO PowerSuite's WebSite Auditor, Netpeak Spider, Scrutiny,
LibreCrawl and ours, Docket. This page says what each costs, which computers it runs on, how much it will crawl,
and when it is the better choice than Screaming Frog. Docket is the answer for some readers and not for others,
and the page says which.</p>

<h2>Short answer: pick by what you are missing</h2>
<ul>
<li><strong>You want it free:</strong> LibreCrawl, if you are happy to start it from a script or Docker, or
Screaming Frog itself or WebSite Auditor for sites under {sf["free_cap"]} URLs.</li>
<li><strong>You want to pay monthly, not yearly:</strong> Netpeak Spider, from {_usd(np_["monthly"])} a month.</li>
<li><strong>You make reports for clients:</strong> Sitebulb Pro.</li>
<li><strong>You want rank tracking and backlinks from the same company:</strong> SEO PowerSuite.</li>
<li><strong>You want to pay once, on a Mac:</strong> Scrutiny at {_usd(scr["once"])}, or Docket at {PRICE_STR}.</li>
<li><strong>You want to pay once, on Windows or a Mac, and be handed a list of what to fix first:</strong>
Docket at {PRICE_STR}.</li>
<li><strong>You want raw crawl data, exact control and the biggest sites:</strong> stay with Screaming Frog.
Nothing below changes that.</li>
</ul>

<h2>{_cap(_WORDS[seven])} tools side by side</h2>
<p>Read {_READ} from each vendor's own pages (sources at the foot of the page). Prices are US dollar list prices
for one person. The first row is the tool you are comparing against.</p>
<div class="wrap-tbl"><table class="cmp"><thead><tr><th>Tool</th><th>Runs on</th><th>What it costs</th>
<th>Free version</th><th>How much it crawls</th></tr></thead><tbody>
{table}
</tbody></table></div>

<h2>Where each one is better than Screaming Frog, and where it is not</h2>

<h3>Sitebulb</h3>
<p>{esc(_cap(sb["runs_on"]))}. Its Lite plan is {_usd(sb["annual"])} a year, which is less than Screaming Frog's
{_usd(sf["annual"])}, and its Pro plan is {_usd(sb["annual_pro"])} a year, which is more. The difference between the
plans is size: {esc(sb["urls"])}. Pro also adds what an agency uses every week: scheduled audits, audit comparisons and
customised PDF reports. It is the better choice when the output is a report for someone else. Screaming Frog's feature list
names {esc(sf["features"].replace("its feature list names ", ""))}, so the gap on features is smaller than a price
difference suggests, and the better question is which of the two you find easier to read.
<a href="/vs/sitebulb-alternative/">Docket and Sitebulb compared</a>.</p>

<h3>SEO PowerSuite (WebSite Auditor)</h3>
<p>It runs on {esc(ps["runs_on"])}. It has a free version, {esc(ps["free"])}, which makes it the nearest like for
like to Screaming Frog's own free tier. Paying is {_usd(ps["annual"])} a year for WebSite Auditor alone, or
{_usd(ps["annual_suite"])} a year for the whole suite. {esc(_cap(ps["features"]))}. That is the reason to choose it:
you are buying a set of SEO tools and the auditor comes with them. The cost to know about is the
return policy: {esc(ps["refund"])}.</p>

<h3>Netpeak Spider</h3>
<p>It runs on {esc(np_["runs_on"])} and is sold by the month: {esc(np_["sold"])}. It {esc(np_["features"])}. If your
need for a crawler comes in bursts, paying for the months you use it can cost less than a licence that lasts a year,
and {esc(np_["refund"])}. The pages we read do not say how many URLs it will crawl, so check that before you plan
around a large site.</p>

<h3>Scrutiny</h3>
<p>It is {esc(scr["runs_on"])}. It is {esc(scr["sold"])}, with {esc(scr["free"])}, so you can try it before you pay.
Its page lists {esc(scr["features"])}. That makes it a tidy fit for someone who looks after a few
sites on a Mac and wants a one-off price. It is not an option on Windows, and it is not a crawler for work you
share with a team on other platforms. <a href="/vs/scrutiny-alternative/">Docket and Scrutiny compared</a>.</p>

<h3>LibreCrawl</h3>
<p>It is {esc(lc["sold"])}, and it has no paid tier. It runs on {esc(lc["runs_on"])}, and you start it
yourself. Its page lists {esc(lc["features"])}, and {esc(lc["note"])}. You choose it when the
price has to be nothing, or when you want to read and change the code. The trade is the one every self-run tool has: you
install it, you update it and nobody is paid to answer when it breaks.</p>

<h2>Docket, the one we make, and what we ran ourselves</h2>
<p>Docket is ours. It runs on {esc(docket_runs)}, costs {PRICE_STR} once, and refunds the whole price within
{REFUND_DAYS} days. It runs {N_CHECKS} checks on every page it reads, including whether AI crawlers such as GPTBot and
ClaudeBot can reach the site, and it puts what it finds in the order to fix it, with the exact markup to paste. That
is the difference from Screaming Frog, which gives you the data and leaves the ordering to you.</p>
<p>It is weaker than Screaming Frog in three places and you should know them before you buy. It has no custom
extraction, so it cannot pull a field of your choice out of every page. It renders JavaScript in WebKit on a sample of
pages and not on every page. And it crawls {ui_pages} pages by default and stops at {minutes} minutes, which you can
raise, but it is not built for a site of hundreds of thousands of URLs.
<a href="/vs/screaming-frog-alternative/">Docket and Screaming Frog compared in full</a>.</p>
{free_figure}
<p>We ran the free version of Docket {esc(_RUN["engine"])}, as shipped, on this site, {esc(_RUN["target"])}. It
read {_RUN["pages"]} pages in {speed_words(_RUN["seconds"])}, scored the site {_RUN["score"]} out of 100
({esc(_RUN["grade"])}), and found {_RUN["problems"]} problems. The free version put the most important one in full,
with its fix, and said how many more the paid version shows.</p>
<p>We did not run the other tools for this page. Everything above about them is what their own pages say, with the
date, and none of it says one is faster or finds more than another, because we did not measure that. Every tool in
the table has a free version or a free trial, and the length of each is in the table. The
quickest honest comparison is the one you run yourself: crawl the same small site with two of them and compare what
you are told to do.</p>

{buy_block("sf-alternatives-page", try_app="sf-alternatives-page-try-free", anchor=False)}

<h2>Not in the list</h2>
<p>Ahrefs Site Audit and Semrush Site Audit run in a browser and are sold inside larger subscriptions, so they are not
desktop crawlers; <a href="/vs/ahrefs-site-audit-alternative/">Ahrefs</a> and
<a href="/vs/semrush-site-audit-alternative/">Semrush</a> are compared separately. If the thing you need is only a
free check, <a href="/best/free-seo-audit-tools/">the best free SEO audit tools</a> says where each one stops. For a
Mac-only view with the cost over three years, see <a href="/mac-seo-audit-tool/">SEO audit tools for Mac</a>.</p>

{comparisons._verified_note("sf-alternatives", closing="If a price or a feature on this page is out of date, <a href='/contact/'>tell us</a> and it will be corrected.")}
"""
    return render(
        cat="best", slug="screaming-frog-alternatives",
        title="Screaming Frog alternatives for Mac and Windows (2026)",
        desc=(f"{_cap(_WORDS[others])} Screaming Frog alternatives for Mac and Windows: what each costs, what it crawls, "
              "its free version, and when it wins. Read from their own pages, November 2026."),
        h1="Screaming Frog alternatives for Mac and Windows",
        crumb='<a href="/">Docket</a> / <a href="/best/">Best</a> / Screaming Frog alternatives',
        body=body,
        faq=[
            ("What is the best free alternative to Screaming Frog?",
             f"LibreCrawl is free with no paid tier and is open source under the MIT licence, but you start it yourself "
             f"from a script or Docker. SEO PowerSuite's WebSite Auditor has a free version that crawls up to "
             f"{ps['free_cap']} URLs, and Screaming Frog itself is free up to {sf['free_cap']} URLs."),
            ("Is there a Screaming Frog alternative I pay for once?",
             f"Yes. Scrutiny is a one-off {_usd(scr['once'])} purchase and runs on a Mac only. Docket is a one-off "
             f"{PRICE_STR} and runs on a Mac and on 64-bit Windows. Sitebulb, SEO PowerSuite and Screaming Frog are "
             "sold by the year, and Netpeak Spider by the month."),
            ("Which Screaming Frog alternatives work on Windows?",
             "Docket, Sitebulb, SEO PowerSuite's WebSite Auditor and Netpeak Spider all list a Windows version. "
             "Scrutiny is Mac only, and LibreCrawl runs anywhere that can run Docker or Python."),
            ("Is Docket a replacement for Screaming Frog?",
             "For some people. Docket ranks what it finds and says what to fix first, runs on a Mac and on Windows, "
             f"and costs {PRICE_STR} once. Screaming Frog is the better tool for raw crawl data, custom extraction, "
             "JavaScript rendering on every page and very large sites, and plenty of people use both."),
        ],
    )


if __name__ == "__main__":
    print(sf_alternatives())
