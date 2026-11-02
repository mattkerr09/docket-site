#!/usr/bin/env python3
"""/mac-seo-audit-tool/: SEO audit tools that run on a Mac, what they cost, and when to pick each.

Growth action 2 of ~/ops/research/growth-docket-2026-10-14.md. The search "seo audit tool mac" is won by
store listings, directories and listicles, and none of them lays out the real options with prices, a
three-year cost and the refund terms. This page does, and it concedes where a rival is the better choice.

Every fact about a rival is a row of data/mac-options.json, read from the vendor's own pages on the date
stored with it; comparisons.py registers that file as a claim set ("mac-options") so the competitive-claims
gate checks that each fact has a source and the page carries the date. No price is typed here: the costs over
three years and how much more each costs than Docket are computed from the rows. Until 2026-11-02 Docket cost
$349 and Scrutiny cost less; at $59 Docket costs less than every tool in the table from the first year, and the
asserts in mac_options() stop the build if a price change makes that untrue again.
"""
from __future__ import annotations

import html
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from render import speed_words, WINDOWS, BNPL_INSTALMENT, MAC_HW, MACOS, N_CHECKS, PRICE, PRICE_STR, REFUND_DAYS, buy_block, render  # noqa: E402

import comparisons  # noqa: E402

_DATA = json.loads((Path(__file__).resolve().parent.parent.parent / "data" / "mac-options.json").read_text())
_OPTIONS = {o["slug"]: o for o in _DATA["options"]}
_READ = comparisons.CHECKED_HUMAN["mac-options"]
#: The audit of our own site that the free-result figure is made from (docket-app scripts/shot_free.mjs).
_RUN = json.loads((Path(__file__).resolve().parent.parent.parent / "data" / "free-run.json").read_text())

YEARS = 3


def _usd(n: int) -> str:
    return f"${n:,}"


def _more_than_docket(total: int) -> str:
    """How much more `total` is than Docket's one price, in words for the table."""
    return f"{_usd(total - PRICE)} more"


def _cost_rows() -> list:
    """(sort key, tool, first year, over three years, how much more than Docket over three years)."""
    rows = []
    scr = _OPTIONS["scrutiny"]
    rows.append((scr["once"] * 1, scr["name"], _usd(scr["once"]), _usd(scr["once"]),
                 _more_than_docket(scr["once"])))
    rows.append((PRICE, "Docket SEO", PRICE_STR, PRICE_STR, "this is Docket"))
    ps = _OPTIONS["seo-powersuite"]
    wsa = ps["annual_alone"]
    rows.append((wsa * YEARS, "SEO PowerSuite, WebSite Auditor alone", _usd(wsa), _usd(wsa * YEARS),
                 _more_than_docket(wsa * YEARS)))
    sb = _OPTIONS["sitebulb"]
    rows.append((sb["annual"] * YEARS, "Sitebulb Lite", _usd(sb["annual"]), _usd(sb["annual"] * YEARS),
                 _more_than_docket(sb["annual"] * YEARS)))
    rows.append((ps["prepaid_three"], "SEO PowerSuite Professional", _usd(ps["annual"]),
                 f"{_usd(ps['prepaid_three'])} prepaid for three years, or {_usd(ps['annual'] * YEARS)} paid yearly",
                 _more_than_docket(ps["prepaid_three"])))
    sf = _OPTIONS["screaming-frog"]
    rows.append((sf["annual"] * YEARS, sf["name"], _usd(sf["annual"]), _usd(sf["annual"] * YEARS),
                 _more_than_docket(sf["annual"] * YEARS)))
    rows.append((sb["annual_pro"] * YEARS, "Sitebulb Pro", _usd(sb["annual_pro"]),
                 _usd(sb["annual_pro"] * YEARS), _more_than_docket(sb["annual_pro"] * YEARS)))
    return sorted(rows, key=lambda r: r[0])


def mac_options() -> Path:
    esc = html.escape
    scr, sf, sb, ps = (_OPTIONS[k] for k in ("scrutiny", "screaming-frog", "sitebulb", "seo-powersuite"))
    # The claims below depend on the order of these numbers. If a price change breaks one, the build stops
    # here rather than publishing a sentence the table no longer supports.
    cheapest = min(scr["once"], sf["annual"], sb["annual"], ps["annual_alone"], ps["annual"])
    assert PRICE < cheapest, "a tool in the table now costs less than Docket in year one: rewrite the prose below"

    side_rows = [
        ("Docket SEO", f"Mac ({MAC_HW}, {MACOS} or later) and 64-bit Windows" if WINDOWS else f"Mac only: {MAC_HW}, {MACOS} or later",
         f"{PRICE_STR} once, or four payments of {BNPL_INSTALMENT}",
         "A full audit with no key: the score, the number of problems in each area and the most important one in full",
         f"{REFUND_DAYS} days, no conditions",
         "you want a ranked list of what to fix first, from a tool that runs on your own Mac with nothing to renew")
    ]
    for o in (sf, sb, scr, ps):
        side_rows.append((o["name"], o["on_mac"], o["sold"], o["free"], o["refund"], o["better_when"]))
    side = "\n".join(
        "<tr>" + f"<th scope=\"row\">{esc(r[0])}</th>" + "".join(f"<td>{esc(c)}</td>" for c in r[1:]) + "</tr>"
        for r in side_rows)

    cost = "\n".join(
        f"<tr><th scope=\"row\">{esc(name)}</th><td>{esc(y1)}</td><td>{esc(y3)}</td><td>{esc(when)}</td></tr>"
        for _, name, y1, y3, when in _cost_rows())

    body = f"""
<p class="lede">If you want to audit a site from a Mac, five tools are worth comparing: Docket, Screaming
Frog, Sitebulb, Scrutiny and SEO PowerSuite. This page says what each one costs, how it is sold, what the free
version does, whether you can get your money back, and when it is the better choice. It also says when Docket
is not.</p>

<h2>The five, side by side</h2>
<p>Checked {_READ}, from each vendor's own pages (sources at the foot of the page). Prices are US dollar list
prices for one person.</p>
<div class="wrap-tbl"><table class="cmp"><thead><tr><th>Tool</th><th>On a Mac</th><th>How it is sold</th>
<th>Free version</th><th>Refund</th><th>It is the better choice when</th></tr></thead><tbody>
{side}
</tbody></table></div>

<h2>What each costs over {YEARS} years</h2>
<p>Add up what you would have paid at list price, with no discount codes, if you kept using the tool for
{YEARS} years. A subscription is paid again every year; Docket and Scrutiny are not.</p>
<div class="wrap-tbl"><table class="cmp"><thead><tr><th>Tool</th><th>Year one</th><th>Over {YEARS} years</th>
<th>More than Docket over {YEARS} years</th></tr></thead><tbody>
{cost}
</tbody></table></div>
<p>Docket costs less than every other tool here from the first day: {PRICE_STR} once, against
{_usd(scr["once"])} once for Scrutiny and {_usd(sf["annual"])} a year for Screaming Frog. It is cheap because one
person in Grand Rapids builds it, with no investors to repay and no sales team, not because it does less. Docket's
one price includes every 1.x release, and Scrutiny's page does not say how long its free updates last.</p>

<h2>If you want your money back</h2>
<p>Docket refunds the whole price within {REFUND_DAYS} days of the receipt, with no conditions and no form.
Screaming Frog refunds in full if you contact them within {esc(sf["refund"].split(" ")[0])} days. SEO PowerSuite's
return policy says it will not provide refunds at any time. The pages read for Sitebulb and Scrutiny do not state
a refund policy, so ask them before you pay.</p>

<h2>When to pick something other than Docket</h2>
<ul>
<li><strong>Screaming Frog</strong> if you want raw crawl data and exact control over what is extracted, or you
need JavaScript rendered across a whole crawl. Docket gives you a ranked answer and not the raw table.
<a href="/vs/screaming-frog-alternative/">The two compared in detail</a>.</li>
<li><strong>Sitebulb</strong> if you work for clients and want visual site maps, scheduled audits, audit
comparisons and branded PDF reports. <a href="/vs/sitebulb-alternative/">The two compared</a>.</li>
<li><strong>Scrutiny</strong> if you want spell checking, HTML validation or site search. <a href="/vs/scrutiny-alternative/">The two compared</a>.</li>
<li><strong>SEO PowerSuite</strong> if you also want rank checking and backlink tools from the same company.</li>
</ul>

<h2>What Docket does not do</h2>
<p>{'Docket runs on a Mac or a 64-bit Windows PC.' if WINDOWS else 'Docket runs only on a Mac.'} It does not track where you rank for a keyword. It is lighter than Screaming Frog
on custom extraction and on rendering JavaScript across a crawl, and it says so on the comparison page. It
runs {N_CHECKS} checks on every page it reads, including whether AI crawlers such as GPTBot and ClaudeBot can reach your
site, and puts what it found in the order to fix it. Its last audit of this site covered {_RUN["pages"]} pages in
{speed_words(_RUN["seconds"])}. The free audit shows the score, how many problems each area has and the single most important problem in full, so you can
see what it finds on your own site before you pay anything.</p>

<h2>Not in the table</h2>
<p>Ahrefs Site Audit and Semrush Site Audit run in a browser and are sold as part of larger subscriptions, so
they are not Mac apps; see <a href="/vs/ahrefs-site-audit-alternative/">Ahrefs</a> and
<a href="/vs/semrush-site-audit-alternative/">Semrush</a>. The Mac App Store also sells small crawlers. They were
not compared here.</p>

{buy_block("mac-options-page", try_app="mac-options-page-try-free", phone=False)}
{comparisons._verified_note("mac-options", closing="If a price on this page is out of date, <a href='/contact/'>tell us</a> and it will be corrected.")}
"""
    return render(
        cat="", slug="mac-seo-audit-tool",
        title="SEO audit tools for Mac, and what each costs over 3 years",
        desc=("Five SEO audit tools that run on a Mac: price, how each is sold, refund terms, and when each is "
              "the better choice. Read from their own pages, October 2026."),
        h1="SEO audit tools for Mac",
        crumb='<a href="/">Docket</a> / <a href="/vs/">Compare</a> / Mac SEO audit tools',
        body=body,
        faq=[
            ("Which SEO audit tools run on a Mac?",
             "Docket, Screaming Frog SEO Spider, Sitebulb and Scrutiny run as Mac apps, and SEO PowerSuite lists an "
             "Apple build. Ahrefs and Semrush are web tools and run in a browser."),
            ("Is there a one-time-price SEO audit tool for Mac?",
             f"Yes. Scrutiny is a one-off {_usd(scr['once'])} purchase and Docket is a one-off {PRICE_STR}. The others in this "
             "comparison are yearly subscriptions."),
            ("Does Docket have a free version?",
             "Yes. A full audit runs with no key and shows your score, the number of problems in each area and the "
             "most important problem in full with its fix."),
        ],
    )
