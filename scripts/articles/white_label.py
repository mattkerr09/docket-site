#!/usr/bin/env python3
"""/best/white-label-seo-audit-tools/: SEO audit tools that put an agency's own name on the report.

Job 2 of the CEO's catch-up list (2026-11-06) and the lists program entry "White-label SEO audit tools for agencies".
The measured demand is in ~/ops/research/marketing-2026-11-04/docket.md: "white label seo audit tool" is about 1,600
searches a month and "seo audit report tool" about 1,300, both with no advertiser data in the keyword tool. Search
Console had no impression for any "white label" query on docketseo.app in the 28 days to 2 November.

/for/agencies/ already answers that query as a pitch for Docket (improved on 5 November, after that window). This page is
the other form of the same question, a list of the tools that do it with what each costs, so it names the others fairly,
labels Docket as ours, and does not repeat the agencies page: its own figures are a table of the white-label part and a
first-year cost computed from the rows. The two pages link to each other.

Every fact about a rival is a row of data/white-label-audit-tools.json, read from the vendor's own pages on the date
stored with it; comparisons.py registers it as the claim set "wl-tools". SEOptimer's site refuses automated requests,
and this page does not get round that: its row is the 8 October reading and the page says so beside it.
"""
from __future__ import annotations

import html
import json
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from render import LATER_PRICE, PRICE_COMPACT, REFUND_DAYS, buy_block, render, speed_words  # noqa: E402

import comparisons  # noqa: E402
import facts as F  # noqa: E402

_ROOT = Path(__file__).resolve().parent.parent.parent
_DATA = json.loads((_ROOT / "data" / "white-label-audit-tools.json").read_text(encoding="utf-8"))
_T = {t["slug"]: t for t in _DATA["tools"]}
_READ = comparisons.CHECKED_HUMAN["wl-tools"]
_RUN = json.loads((_ROOT / "data" / "sample-run.json").read_text(encoding="utf-8"))
_WORDS = {1: "one", 2: "two", 3: "three", 4: "four", 5: "five", 6: "six", 7: "seven", 8: "eight", 9: "nine"}


def _human(iso: str) -> str:
    d = date.fromisoformat(iso)
    return f"{d.day} {d.strftime('%B %Y')}"


def _usd(n: float) -> str:
    return f"${round(n):,}"


def _cap(s: str) -> str:
    return s[:1].upper() + s[1:]


def white_label_tools() -> Path:
    esc = html.escape
    so_read = _human(_T["seoptimer"]["read"])
    pw, np_, sb, se, sm, sc, so = (_T[k] for k in ("seo-powersuite", "netpeak-spider", "sitebulb", "se-ranking",
                                                   "semrush", "sitechecker", "seoptimer"))
    # What a year costs if white label is the thing you are buying, lowest listed way in. Computed from the rows.
    year = [
        ("Docket SEO", LATER_PRICE, f"{PRICE_COMPACT}, with nothing to renew"),
        ("Netpeak Spider", np_["monthly"] * 12, f"{_usd(np_['monthly'])} a month, kept for twelve months"),
        ("SEOptimer Pro", so["monthly"] * 12, f"{_usd(so['monthly'])} a month, kept for twelve months (read {so_read})"),
        ("Sitebulb Pro", sb["annual"], f"{_usd(sb['annual'])} a year"),
        ("SEO PowerSuite Enterprise", pw["annual"], f"{_usd(pw['annual'])} a year"),
        ("Semrush with the Pro Report add-on", (sm["plan_monthly_annual"] + sm["addon_monthly"]) * 12,
         f"the SEO plan billed annually plus {_usd(sm['addon_monthly'])} a month for the add-on"),
        ("SE Ranking with the Agency Pack", (se["plan_monthly_annual"] + se["addon_monthly"]) * 12,
         f"the Core plan billed annually plus {_usd(se['addon_monthly'])} a month for the pack"),
    ]
    year.sort(key=lambda r: r[1])
    assert year[0][0] == "Docket SEO", "Docket is no longer the cheapest first year: rewrite the sentences that say so"
    year_rows = "\n".join(f"<tr><th scope=\"row\">{esc(n)}</th><td>{esc(PRICE_COMPACT) if n == 'Docket SEO' else _usd(c)}</td><td>{esc(how)}</td></tr>"
                          for n, c, how in year)
    cheapest_rival = year[1]

    docket_part = ("Your agency's name and logo in place of Docket's on the PDF and HTML reports, with &ldquo;Prepared "
                   "by&rdquo; you (the paid version)")
    rows = [
        ("Docket SEO", "a desktop app for Mac and Windows", docket_part, f"{PRICE_COMPACT}, {F.licence_covers()}")
    ]
    for t in (np_, sb, pw, se, sm, sc, so):
        rows.append((t["name"], t["kind"], esc(_cap(t["white_label"])), esc(_cap(t["sold"]))))
    side = "\n".join(
        f'<tr><th scope="row">{esc(r[0])}</th><td>{esc(_cap(r[1]))}</td><td>{r[2]}</td><td>{r[3]}</td></tr>'
        for r in rows)

    br = _RUN["branded_image"]
    body = f"""
<p class="lede">Eight tools let you put your own name on an SEO audit: Docket, Netpeak Spider, Sitebulb, SEO PowerSuite,
SE Ranking, Semrush, Sitechecker and SEOptimer. This page says what the white-label part of each one is, what it
costs for a year, and when each is the better choice. Docket is ours and is the cheapest of them for a year, and
the page says plainly where it does less.</p>

<h2>Short answer: pick by how you sell audits</h2>
<ul>
<li><strong>You send a report and want to pay once:</strong> Docket at {PRICE_COMPACT}, with your name and logo on the PDF and
HTML report and no limit on how many sites you audit.</li>
<li><strong>You want a crawler on your own computer with branded PDFs:</strong> Netpeak Spider by the month,
Sitebulb Pro or SEO PowerSuite Enterprise by the year.</li>
<li><strong>You want your own report address, report templates and a place for clients to log in:</strong> a cloud tool,
SEOptimer or SE Ranking with its Agency Pack. Docket has none of those.</li>
<li><strong>You already pay for Semrush:</strong> its Pro Report add-on is {_usd(sm["addon_monthly"])} a month.</li>
</ul>

<h2>The {_WORDS[len(rows)]} side by side</h2>
<p>Read {_READ} from each vendor's own pages (sources at the foot of the page), with one exception: SEOptimer's site
refuses automated requests, so its row is the reading of {so_read} and is marked. Prices are US dollar list prices
for one person.</p>
<div class="wrap-tbl"><table class="cmp"><thead><tr><th>Tool</th><th>What it is</th><th>The white-label part</th>
<th>What it costs</th></tr></thead><tbody>
{side}
</tbody></table></div>

<h2>What a year of white label costs</h2>
<p>The lowest listed way to get your own name on the report, for one year using Docket's price from December for the savings. A
subscription is paid again every year; Docket is not. Sitechecker is left out of this table because the pages read do
not say which of its plans unlocks white label, so any figure for it would be a guess.</p>
<div class="wrap-tbl"><table class="cmp"><thead><tr><th>Tool</th><th>First year</th><th>How that is made up</th></tr></thead><tbody>
{year_rows}
</tbody></table></div>
<p>Docket costs at least {_usd(cheapest_rival[1] - LATER_PRICE)} less in the first year than the next cheapest, {esc(cheapest_rival[0])}.
It is cheap because one person builds it and there is no sales team, not because it does less of the one job on this
page. The cloud tools cost more and do more: SE Ranking and Semrush are whole SEO platforms with rank tracking, which
this table does not weigh.</p>

<h2>Where each one is the better choice</h2>
<ul>
<li><strong>SEOptimer or SE Ranking</strong> if you want a branded report on your own domain, report templates, or
client logins. In SEOptimer, {esc(so["white_label"])}. In SE Ranking, {esc(se["white_label"])}.
<a href="/vs/seoptimer-alternative/">Docket and SEOptimer compared</a>.</li>
<li><strong>SEO PowerSuite Enterprise</strong> if you also want rank tracking and backlink tools from the same company, and
report templates you can edit. It lists {esc(pw["white_label"])}.</li>
<li><strong>Sitebulb Pro</strong> if the audit is a deliverable built on a visual crawl. {esc(_cap(sb["white_label"]))}.</li>
<li><strong>Netpeak Spider</strong> if you want to pay by the month for a desktop crawler: {esc(np_["white_label"])}.</li>
<li><strong>Semrush</strong> if you are already on it: {esc(sm["white_label"])}.</li>
<li><strong>Sitechecker</strong> if you want to try a cloud tool built around white label: {esc(sc["sold"])}.</li>
</ul>

<h2>Docket, the one we make: what it does and does not</h2>
<p>Docket is ours. In the paid version the PDF and HTML reports carry your agency's name and logo in place of Docket's
and say &ldquo;Prepared by&rdquo; you. A licence covers {F.licence_covers()}, a pre-sales audit costs nothing extra, and
the whole price is refunded within {REFUND_DAYS} days. It does not give you a report on your own web address, editable
report templates, a login for clients, or rank tracking. Its schedule runs while the app is open on a computer that is
awake. If you need any of those, pick one of the cloud tools above.
<a href="/for/agencies/">Docket for agencies, in full</a>.</p>

<figure class="shot">
  <img src="{br["src"]}" width="{br["width"]}" height="{br["height"]}" loading="lazy" decoding="async"
       alt="Page one of a Docket audit report with Report branding set: a placeholder logo reading YOUR LOGO and the name {esc(br["name"])} where Docket's mark and name would be.">
  <figcaption>Page one of a real Docket report on our own site, with Report branding set to a placeholder. Without
  branding the same page carries Docket's shield and name.</figcaption>
</figure>

<p>That report covers {_RUN["pages"]} pages, took {speed_words(_RUN["seconds"])} and lists {_RUN["issues"]} issues. It
is the only thing on this page we ran ourselves. We did not run the other tools, so nothing here says one makes a better
report than another, only what each vendor's own pages say it does and what it costs. Most have a free trial, so the
fair test is the one you run yourself: audit the same small site in two of them and send each report to a friend.</p>

{buy_block("wl-tools-page", try_app="wl-tools-page-try-free", anchor=False)}

<h2>Next</h2>
<p>If the other name on your list is a crawler rather than a reporting platform, see
<a href="/best/screaming-frog-alternatives/">Screaming Frog alternatives for Mac and Windows</a>. For one that is only
a free check, <a href="/best/free-seo-audit-tools/">the best free SEO audit tools</a> says where each stops.</p>

{comparisons._verified_note("wl-tools", closing=f"SEOptimer's row was read on {so_read} and is not re-read here because its site refuses automated requests. If a price or a feature on this page is out of date, <a href='/contact/'>tell us</a> and it will be corrected.")}
"""
    return render(
        cat="best", slug="white-label-seo-audit-tools",
        title="White-label SEO audit tools for agencies (2026)",
        desc=("Eight SEO audit tools that put your agency's name on the report: the white-label part, what a year "
              "costs, and when each wins. Read from their own pages."),
        h1="White-label SEO audit tools for agencies",
        crumb='<a href="/">Docket</a> / <a href="/best/">Best</a> / White-label SEO audit tools',
        body=body,
        faq=[
            ("What is the best white-label SEO audit tool?",
             f"It depends on how you sell audits. Docket is the cheapest for a year at {PRICE_COMPACT} and puts your name "
             "and logo on the PDF and HTML report. SEOptimer and SE Ranking with its Agency Pack add a report on your own "
             "domain and client logins, and cost more."),
            ("Can I put my own logo on an SEO audit report?",
             "Yes, in each of the tools on this page. Docket, Netpeak Spider, SEO PowerSuite Enterprise, SE Ranking, Semrush "
             "and SEOptimer say so on their own pages, and Sitebulb Pro lists customised PDF reports. Which plan unlocks it "
             "differs, and the table says which."),
            ("Is there a white-label SEO audit tool I pay for once?",
             f"Docket is a one-off {PRICE_COMPACT}. The others on this page are monthly or yearly subscriptions."),
            ("Does Docket have a client portal or a custom report domain?",
             "No. It makes the report as a PDF and an HTML file that carry your name and logo, and you send it yourself. "
             "A custom report address, report templates and client logins are what the cloud tools charge for."),
        ],
    )


if __name__ == "__main__":
    print(white_label_tools())
