#!/usr/bin/env python3
"""/index/llms-txt-adoption-2026-10/: llms.txt in the Tranco top 10,000, read twice.

The August 2026 survey (`/index/ai-directives/`) asked each of the top 10,000
sites for `/llms.txt` and published one figure for it. The October re-run
(`/index/ai-crawler-blocking-2026-10/`) asked again, the same way, and kept the
results without reporting them. This page reports them.

Every number is read out of data/llms-adoption-2026-10.json through `facts.lt*`,
which scripts/build_llms_adoption.py derives from the raw surveys and their
validation files. That file holds aggregates and no host, so this page cannot
name a site even by accident.

WHAT THIS PAGE REFUSES TO SAY, because the data does not:

  1. WHY the count rose. The files exist or they do not; nothing in a survey of
     requests says who wrote one, when, or for what.
  2. That an llms.txt does anything. This page counts files. The August page and
     /learn/what-is-llms-txt/ say what is and is not known about their use.
  3. That sites with a file block AI crawlers less BECAUSE of it. The two go
     together; the data cannot say what links them.
  4. That the 20 sites which stopped removed a file. Only some of them answer as
     a deleted file does.
  5. Anything about a site by name.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import facts as F  # noqa: E402
from render import render  # noqa: E402

KIND_WORDS = {
    "compressed": "compressed data the survey could not decode",
    "robots": "a robots.txt",
    "html": "an HTML page or comment",
    "json": "JSON",
    "xml": "XML",
    "empty": "an empty body",
}


def _c(n: int) -> str:
    return f"{n:,}"


def _p(count: int, base: int) -> str:
    return F.lt_pct(count, base)


def _count_pct(count: int, base: int) -> str:
    return f"{_c(count)} ({_p(count, base)}%)"


def _kinds(by: dict) -> str:
    parts = [f"{KIND_WORDS[k]} ({n})" for k, n in sorted(by.items(), key=lambda kv: (-kv[1], kv[0]))
             if n]
    return ", ".join(parts[:-1]) + (" and " if len(parts) > 1 else "") + parts[-1]


def _answers_rows(a: dict, o: dict) -> str:
    rows = []
    for key, label in (("gone", "Answered 404 or 410, which is what no file looks like"),
                       ("ok_200", "Answered 200"),
                       ("refused", "Refused our bot with a 401, 403, 406, 429 or 503"),
                       ("redirect", "Answered a redirect that was not completed"),
                       ("no_answer", "Gave no answer (an error or a timeout)"),
                       ("other", "Answered some other status")):
        rows.append(f"<tr><td>{label}</td><td>{_count_pct(a['answers'][key], a['asked'])}</td>"
                    f"<td>{_count_pct(o['answers'][key], o['asked'])}</td></tr>")
    return "".join(rows)


def _funnel_rows(a: dict, o: dict) -> str:
    spec = (("Answered 200 at /llms.txt", "answered_200"),
            ("Kept as candidates by the survey's first filter", "candidates"),
            ("Set aside: a made-up path on the same host also answered 200", "soft404"),
            ("Set aside: another kind of file", "wrong_kind"),
            ("Set aside: did not answer 200 in the validation step", "not_200_on_recheck"),
            ("Real llms.txt", "confirmed"))
    out = []
    for label, key in spec:
        strong = key == "confirmed"
        cell = (lambda n: f"<strong>{_c(n)}</strong>") if strong else _c
        name = f"<strong>{label}</strong>" if strong else label
        out.append(f"<tr><td>{name}</td><td>{cell(a[key])}</td><td>{cell(o[key])}</td></tr>")
    return "".join(out)


def _headline_rows(a: dict, o: dict) -> str:
    spec = (("Sites in the list", F.lt("meta", "hosts"), F.lt("meta", "hosts")),
            ("Readable robots.txt", a["readable"], o["readable"]),
            ("Of those, robots.txt let our bot ask for /llms.txt", a["asked"], o["asked"]),
            ("<strong>Real llms.txt</strong>", a["confirmed"], o["confirmed"]))
    rows = [f"<tr><td>{label}</td><td>{_c(x)}</td><td>{_c(y)}</td></tr>" for label, x, y in spec]
    rows.append(f"<tr><td><strong>Share of readable robots.txt files</strong></td>"
                f"<td><strong>{_p(a['confirmed'], a['readable'])}%</strong></td>"
                f"<td><strong>{_p(o['confirmed'], o['readable'])}%</strong></td></tr>")
    rows.append(f"<tr><td>Share of the sites we could ask</td>"
                f"<td>{_p(a['confirmed'], a['asked'])}%</td>"
                f"<td>{_p(o['confirmed'], o['asked'])}%</td></tr>")
    return "".join(rows)


def _panel_rows(p: dict) -> str:
    spec = (("Had a real llms.txt in August", p["aug_total"]),
            ("Had one in October", p["oct_total"]),
            ("Had one both times", p["both"]),
            ("Started having one", p["started"]),
            ("Stopped having one", p["stopped"]),
            ("Had none either time", p["neither"]))
    return "".join(f"<tr><td>{label}</td><td>{_c(n)}</td></tr>" for label, n in spec)


def _band_rows(a: dict, o: dict) -> str:
    rows = []
    for ba, bo in zip(a["bands"], o["bands"]):
        rows.append(f"<tr><td>{_c(ba['from'])} to {_c(ba['to'])}</td>"
                    f"<td>{_c(ba['confirmed'])} of {_c(ba['readable'])} "
                    f"({_p(ba['confirmed'], ba['readable'])}%)</td>"
                    f"<td>{_c(bo['confirmed'])} of {_c(bo['readable'])} "
                    f"({_p(bo['confirmed'], bo['readable'])}%)</td></tr>")
    return "".join(rows)


def _blocking_rows(a: dict, o: dict) -> str:
    rows = []
    for month_label, m in ((F.lt_month("aug"), a), (F.lt_month("oct"), o)):
        b = m["blocking"]
        for grp, name in (("with", "with a real llms.txt"), ("without", "without one")):
            base = b[grp]
            cells = "".join(f"<td>{_p(b[f'{key}_{grp}'], base)}% ({_c(b[f'{key}_{grp}'])} of {_c(base)})</td>"
                            for key in ("search", "training"))
            rows.append(f"<tr><td>{month_label}, {name}</td>{cells}</tr>")
    return "".join(rows)


def _premises(a: dict, o: dict, pan: dict, stop: dict, start: dict) -> None:
    """The page's sentences that say "rose in every band", "most", "under half".

    They are written in words, so they must fail the build if the data stops
    supporting them rather than go on being published.
    """
    shares = [(x["confirmed"] / x["readable"], y["confirmed"] / y["readable"])
              for x, y in zip(a["bands"], o["bands"])]
    counts = [y["confirmed"] - x["confirmed"] for x, y in zip(a["bands"], o["bands"])]
    top = [y["confirmed"] / y["readable"] for y in o["bands"]]
    top_a = [x["confirmed"] / x["readable"] for x in a["bands"]]
    checks = {
        "the share rose in every band": all(y > x for x, y in shares),
        "the count rose in every band": all(c > 0 for c in counts),
        "the first band is highest and the last lowest, both months":
            top[0] == max(top) and top[-1] == min(top) and top_a[0] == max(top_a) and top_a[-1] == min(top_a),
        "under half of the 200 answers were real files, both months":
            2 * a["confirmed"] < a["answered_200"] and 2 * o["confirmed"] < o["answered_200"],
        "most sites that stopped did not answer as a deleted file": 2 * stop.get("gone", 0) < pan["stopped"],
        "most sites that started had been 404 or 410": 2 * start.get("gone", 0) > pan["started"],
        "starts outnumber stops": pan["started"] > pan["stopped"],
        "training blocking fell in both groups":
            o["blocking"]["training_rate_with"] < a["blocking"]["training_rate_with"]
            and o["blocking"]["training_rate_without"] < a["blocking"]["training_rate_without"],
        "files with an llms.txt block a search crawler less, both months":
            a["blocking"]["search_rate_with"] < a["blocking"]["search_rate_without"]
            and o["blocking"]["search_rate_with"] < o["blocking"]["search_rate_without"],
        "the funnel adds up, both months": all(
            m["candidates"] - m["soft404"] - m["wrong_kind"] - m["not_200_on_recheck"] == m["confirmed"]
            for m in (a, o)),
    }
    bad = [name for name, ok in checks.items() if not ok]
    if bad:
        raise SystemExit("llms_adoption: the data no longer supports the page's wording: "
                         + "; ".join(bad))


def llms_adoption() -> Path:
    a, o = F.lt("aug"), F.lt("oct")
    pan, rec, rr = F.lt("panel"), F.lt("reconcile"), F.lt("reread")
    http = F.lt("sensitivity", "http_read")
    aug_date, oct_date = F.lt_date("aug"), F.lt_date("oct")
    aug_month, oct_month = F.lt_month("aug"), F.lt_month("oct")
    meta = F.lt("meta")

    a_pct, o_pct = _p(a["confirmed"], a["readable"]), _p(o["confirmed"], o["readable"])
    of200_a, of200_o = _p(a["confirmed"], a["answered_200"]), _p(o["confirmed"], o["answered_200"])
    delta = o["confirmed"] - a["confirmed"]
    panel_net = pan["oct_total"] - pan["aug_total"]
    panel_growth = _p(panel_net, pan["aug_total"])
    top_a, top_o = a["bands"][0], o["bands"][0]
    top_to = _c(top_a["to"])
    sw = rec["aug_left_out_why"]
    why_labels = (("robots_308", "answered a redirect that never resolved"),
                  ("refused", "refused our bot at robots.txt"),
                  ("disallows_our_agent", "disallowed our bot from <code>/llms.txt</code>"),
                  ("unreachable", "could not be reached"),
                  ("no_robots", "had no robots.txt"),
                  ("oversize", "served a file above the size limit"))
    why_parts = [f"{sw[k]} {text}" for k, text in why_labels if sw[k]]
    why_text = ", ".join(why_parts[:-1]) + (", and " if len(why_parts) > 2 else
                                            " and " if len(why_parts) == 2 else "") + why_parts[-1]
    stop, start = pan["stopped_to"], pan["started_from"]
    stop_other = pan["stopped"] - sum(stop.get(k, 0) for k in ("gone", "soft404", "refused", "page"))
    start_other = pan["started"] - sum(start.get(k, 0) for k in ("gone", "soft404", "refused"))
    fp_a = a["soft404"] + a["wrong_kind"]
    gap = a["candidates"] - fp_a - a["confirmed"]
    sens = pan["rule_sensitive"]["started"] + pan["rule_sensitive"]["stopped"]
    changes = pan["started"] + pan["stopped"]
    fa, fo = a["files"], o["files"]
    bk = o["blocking"]
    bot_name = meta["user_agent"].split("/")[0]
    timeout_s = int(meta["timeout_s"])
    na_a, na_o = a["not_asked_disallowed"], o["not_asked_disallowed"]

    _premises(a, o, pan, stop, start)

    body = f"""
<p class="lede">In {aug_month} we asked the Tranco top 10,000 sites for their
<code>/llms.txt</code>. On {oct_date} we asked the same list again, as close to the same way as the August record allows.
<strong>{_c(o['confirmed'])} sites had a real file in October, which is {o_pct}% of the
{_c(o['readable'])} whose robots.txt we could read. In August it was {_c(a['confirmed'])}, or
{a_pct}%.</strong> The rise is not only a different set of sites answering: of the
{_c(pan['asked_both'])} sites we could ask both times, {pan['started']} started having a real file
and {pan['stopped']} stopped.</p>

<div class="stat-row">
<div class="stat"><b>{o_pct}%</b><span>have a real llms.txt (was {a_pct}%)</span></div>
<div class="stat"><b>{panel_net}</b><span>more real files on the same {_c(pan['asked_both'])} sites ({pan['started']} started, {pan['stopped']} stopped)</span></div>
<div class="stat"><b>{of200_o}%</b><span>of the sites that answered 200 had a real file (was {of200_a}%)</span></div>
<div class="stat"><b>{_p(top_o['confirmed'], top_o['readable'])}%</b><span>of the top {top_to} (was {_p(top_a['confirmed'], top_a['readable'])}%)</span></div>
</div>

<h2>The headline numbers</h2>

<p>Shares here are of the sites whose robots.txt we could read, the base the
<a href="/index/ai-directives/">August page</a> used for its own figure. We asked for
<code>/llms.txt</code> only where that robots.txt let our survey bot fetch it, so some readable
sites sit in the base and could not be in the count: {_c(na_o)} in October and {_c(na_a)} in
August. The last row leaves them out.</p>

<div class="wrap-tbl"><table class="cmp">
<thead><tr><th></th><th>{aug_month}</th><th>{oct_month}</th></tr></thead>
<tbody>{_headline_rows(a, o)}</tbody></table></div>

<p>A file counts as real when it passes three tests, the same three the August page used:</p>
<ul>
<li>the request for <code>/llms.txt</code> answered 200;</li>
<li>a made-up path on the same host did not also answer 200, because a host that does is
answering yes to everything;</li>
<li>the first bytes are not another kind of file: XML, JSON, an HTML comment or page, a robots.txt
or sitemap, compressed data the survey could not read, or nothing.</li>
</ul>

<h2>A 200 answer is not a file</h2>

<p>Counting every site that answered 200 would have found {_c(o['answered_200'])} in October and
{_c(a['answered_200'])} in August. The tests leave {_c(o['confirmed'])} and {_c(a['confirmed'])}.
That is {of200_o}% of the 200 answers in October and {of200_a}% in August. Most of the rest were
pages and empty responses: {_c(o['answered_200_html'])} of the October 200 answers were served as
<code>text/html</code> and {_c(o['answered_200_empty'])} had an empty body. The survey's first
filter set those aside before the tests began. A check of your own site should do the same:
read the first lines of what comes back, and ask for a path that cannot exist before it
believes a 200.</p>

<div class="wrap-tbl"><table class="cmp">
<thead><tr><th>Sites</th><th>{aug_month}</th><th>{oct_month}</th></tr></thead>
<tbody>{_funnel_rows(a, o)}</tbody></table></div>

<p>The made-up path removes the most. {_c(o['soft404'])} candidates in October sat on a host that
also answered 200 for a path we invented, which is what a catch-all rule or a soft 404 page does,
against {_c(a['soft404'])} in August. Another {o['wrong_kind']} were a different kind of
file: {_kinds(o['wrong_kind_by'])}. In August the figure was {a['wrong_kind']}.</p>

<p>One note on August's arithmetic. That page sets aside {fp_a} of its {_c(a['candidates'])}
candidates, so {_c(a['candidates'])} less {fp_a} is not {_c(a['confirmed'])}. The other {gap}
did not answer 200 in the validation step, though the survey had recorded a 200 for them, and a
file we could not confirm is not counted. October's collector read each file once and checked
that response, so its row is 0.</p>

<h2>What the servers said</h2>

<p>This is what <code>/llms.txt</code> answered at the {_c(o['asked'])} sites we could ask in
October, with August's {_c(a['asked'])} beside it.</p>

<div class="wrap-tbl"><table class="cmp">
<thead><tr><th>Answer</th><th>{aug_month}</th><th>{oct_month}</th></tr></thead>
<tbody>{_answers_rows(a, o)}</tbody></table></div>

<p>In October {_p(o['answers']['refused'], o['asked'])}% of the sites we could ask refused the
request, against {_p(a['answers']['refused'], a['asked'])}% in August. Their robots.txt said our
bot could ask and their server said no, the gap <a href="/index/ai-directives/">the August
page</a> covers under &ldquo;robots.txt is not access&rdquo;. <a
href="/how-to/fix-ai-crawlers-blocked-by-your-cdn/">A CDN setting</a> is one way a server can do
that and leave no trace in robots.txt; we cannot tell which way these sites did it. A refused
request is not counted as a missing file, because we do not know what was behind it.</p>

<h2>What changed on the same sites</h2>

<p>{_c(pan['asked_both'])} sites had a readable robots.txt that let us ask in both months.
Comparing them with themselves removes the effect of which sites answered each time.</p>

<div class="wrap-tbl"><table class="cmp">
<thead><tr><th>Same {_c(pan['asked_both'])} sites</th><th>Sites</th></tr></thead>
<tbody>{_panel_rows(pan)}</tbody></table></div>

<p>That is {panel_net} more real files on the same sites, {panel_growth}% more than in August.
{pan['started']} sites started against {pan['stopped']} that stopped.</p>

<p><strong>Most of the sites that stopped do not look like a deleted file.</strong> Of the
{pan['stopped']}:</p>
<ul>
<li>{stop.get('gone', 0)} now answer <code>404</code> or <code>410</code>, which is what a deleted
file looks like.</li>
<li>{stop.get('soft404', 0)} answer 200 for the made-up path as well, so their file now fails the
second test. Whether it is still there we cannot tell.</li>
<li>{stop.get('refused', 0)} refuse our bot.</li>
<li>{stop.get('page', 0)} answer 200 with something that is not a text file.</li>
<li>{stop_other} gave a server error or a redirect we could not complete.</li>
</ul>

<p><strong>Most of the sites that started had no file in August.</strong> Of the
{pan['started']}, {start.get('gone', 0)} answered <code>404</code> or <code>410</code> then,
{start.get('soft404', 0)} answered 200 for the made-up path too, {start.get('refused', 0)} refused
our bot, and {start_other} did something else.</p>

<p>The full counts moved by {delta}, and the same-site comparison explains it:
{pan['started']} that started, minus {pan['stopped']} that stopped, minus
{_c(rec['aug_not_asked_in_oct'])} that had a file in August and could not be asked in October,
plus {_c(rec['oct_not_asked_in_aug'])} that have one in October and could not be asked in August,
is {delta}. Of the {_c(rec['aug_not_asked_in_oct'])} we could not ask in October, {why_text}.</p>

<h2>Where in the list</h2>

<p>The ranks are Tranco's and unchanged from August. The share and the count rose in every
band. The top {top_to} sites were the most likely to have a file in both months and the last
band the least.</p>

<div class="wrap-tbl"><table class="cmp">
<thead><tr><th>Tranco rank</th><th>{aug_month}</th><th>{oct_month}</th></tr></thead>
<tbody>{_band_rows(a, o)}</tbody></table></div>

<h2>What the files look like</h2>

<p>For each file we confirmed we kept the first {meta['head_chars']} characters and its size.
<strong>{_count_pct(fo['h1'], fo['confirmed'])} of the October files open with a Markdown
H1</strong>, the one required part of the format described on
<a href="/learn/what-is-llms-txt/">what llms.txt is</a>, against
{_count_pct(fa['h1'], fa['confirmed'])} in August. {_count_pct(fo['h1_blockquote'], fo['confirmed'])}
have a blockquote summary straight after it, against
{_count_pct(fa['h1_blockquote'], fa['confirmed'])}. {_c(fo['text_plain'])} were served as
<code>text/plain</code> and {_c(fo['text_markdown'])} as <code>text/markdown</code>.</p>

<p>The middle file is {_c(fo['median_bytes'])} bytes, against {_c(fa['median_bytes'])} in
August. {fo['over_100kb']} are larger than 100 KB (August: {fa['over_100kb']}) and
{fo['under_1kb']} are smaller than 1 KB (August: {fa['under_1kb']}). We cannot say anything about
the links or sections further down a file, because we did not keep them.</p>

<h2>Sites that have a file block AI crawlers less often</h2>

<p>The August page found that sites with an llms.txt were less likely to block an AI search
crawler. October shows the same shape. These shares use the sites we could ask, and the crawler
groups are the ones on <a href="/index/ai-crawler-blocking-2026-10/">the crawler-blocking
page</a>.</p>

<div class="wrap-tbl"><table class="cmp">
<thead><tr><th>Sites we could ask</th><th>Block at least one AI search crawler</th>
<th>Block at least one AI training crawler</th></tr></thead>
<tbody>{_blocking_rows(a, o)}</tbody></table></div>

<p>Only {bk['search_with']} of the {_c(bk['with'])} sites with a file block a search crawler, which
is too few for the ratio ({bk['rr_search']['rr']:.3f}, 95% interval {bk['rr_search']['lo']:.2f}
to {bk['rr_search']['hi']:.2f}) to be read closely. The table says which sites have both things. It does
not say that publishing a file changes who gets blocked, or the reverse, and nothing here shows
what links them. Training-crawler blocking fell in both groups since August, which
<a href="/index/ai-crawler-blocking-2026-10/">the crawler-blocking page</a> looks at.</p>

<h2>How we measured</h2>

<p><strong>Sample and dates.</strong> The sites are the Tranco top 10,000 (list PYG5J): the same hosts in
the same order as the {aug_month} survey, read on {aug_date} and on {oct_date}. How
the run was set up, and how the robots.txt files were parsed so that both months read alike, is
on <a href="/index/ai-crawler-blocking-2026-10/">the crawler-blocking page</a>. The survey's user
agent, <code>{bot_name}</code>, is explained on <a href="/bot/">the bot page</a>.</p>

<p><strong>The llms.txt request.</strong> After reading a site's robots.txt, we asked for
<code>/llms.txt</code> only if that file let the survey bot fetch it. When what came back looked
like a file, we asked once more, for a path that cannot exist on that host. One request each, no
retries, and a timeout of {timeout_s} seconds.</p>

<p><strong>Same tests, both months.</strong> The tests above are applied unchanged to both
months. Before anything is counted for October they are run on the August records, and the build
stops unless they give back the figures the August page published. They do.</p>

<h2>What this does not tell you</h2>

<ul>
<li><strong>Whether anyone reads these files.</strong> This counts files that exist. The
<a href="/index/ai-directives/">August page</a> covers what is known about use.</li>
<li><strong>The top of the web, not the web.</strong> These are {_c(meta['hosts'])} popular
hosts on two days. A small business site is unlikely to be on the list.</li>
<li><strong>Some sites are in no share.</strong> {_c(na_o)}
readable sites did not let our bot ask. Others had no readable robots.txt at all, including the
sites that refused our bot there, which <a href="/index/ai-crawler-blocking-2026-10/">the
crawler-blocking page</a> counts.</li>
<li><strong>Some sites were read again.</strong> The October collector ran under Python
<code>3.9</code> with an older TLS library, and did not follow an HTTP <code>308</code> redirect.
{rr['was_robots_308']} sites answered <code>/robots.txt</code> with one and {rr['was_llms_308']}
answered <code>/llms.txt</code> with one; {_c(rr['connect_hosts'])} more had not connected or had
fallen back to plain http. All {_c(rr['hosts'])} were read again on {F.lt_fmt(rr['date'])}, under
Python <code>{rr['python_major_minor']}</code> with redirects followed, and every figure on this page
includes the new reads: {rr['confirmed_among']} of those sites have a real llms.txt. Sites that read
fine on {oct_date} were not read again.</li>
<li><strong>Some differences from August cannot be removed.</strong> August's user agent, its
pace and order, whether it fell back to plain http, and its file-size cutoff were not recorded.
<a href="/index/ai-crawler-blocking-2026-10/">The crawler-blocking page</a> lists them. Without the
{_c(http['readable'])} sites read over plain http, the share of readable files with a real llms.txt
would be {_p(http['confirmed_total'] - http['confirmed'], http['readable_total'] - http['readable'])}%
instead of {o_pct}%.</li>
<li><strong>August's first filter could not be recovered.</strong> The rule that turned a 200
into a candidate was rebuilt for October. The tests after it are identical, and only {sens} of the
{changes} sites that started or stopped sit on the difference.</li>
<li><strong>Only how files open.</strong> We kept {meta['head_chars']} characters of each file.</li>
<li><strong>A real file is not a good or a current one.</strong> We checked that it is there and
what it opens with.</li>
<li><strong>One computer, one day each.</strong> A site that shows different visitors different
files would not show it. Two months is a short gap, {pan['stopped']} sites stopped, and we ran no
test of whether any difference is more than chance.</li>
</ul>

<h2>Get the data</h2>

<p>The summary behind every table above is one small file. It holds counts and no site, and
nothing on this page names one.</p>

<p><a class="btn-ghost" href="/data/llms-adoption-2026-10.csv">Download the summary (CSV)</a></p>

<div class="callout">
<div class="callout-title">Check your own site</div>
<p>Docket lists a missing llms.txt as a notice and says it is optional, and when your server
refuses the request it reports that it could not check rather than calling the file missing.
Whether AI crawlers can reach your pages at all comes first, and the
<a href="/tools/ai-crawler-checker/">free checker</a> tests that for one address.</p>
</div>

<h2>Related</h2>
<ul>
<li><a href="/learn/what-is-llms-txt/">What is llms.txt, and does it do anything?</a></li>
<li><a href="/index/ai-directives/">The AI rules in robots.txt that do nothing</a>, the August survey</li>
<li><a href="/index/ai-crawler-blocking-2026-10/">AI crawler blocking, August to October 2026</a></li>
</ul>

<p><a class="btn" href="/download/">Download Docket</a></p>
"""

    faq = [
        ("How many of the top 10,000 websites have an llms.txt?",
         f"On {oct_date}, {_c(o['confirmed'])} of the {_c(o['readable'])} sites in the Tranco top "
         f"10,000 with a readable robots.txt had a real llms.txt, which is {o_pct}%. In "
         f"{aug_month} it was {_c(a['confirmed'])}, or {a_pct}%."),
        ("Does a 200 response at /llms.txt mean a site has one?",
         f"No. {_c(o['answered_200'])} sites answered 200 in October and {_c(o['confirmed'])} "
         f"had a real file, {of200_o}%. The rest were mostly web pages, empty responses or hosts "
         "that answer 200 for any address, including one that cannot exist."),
        ("Did more sites add an llms.txt between August and October 2026?",
         f"Yes, on the same sites. Of {_c(pan['asked_both'])} sites we could ask both times, "
         f"{pan['started']} started having a real file and {pan['stopped']} stopped, and only "
         f"{stop.get('gone', 0)} of those {pan['stopped']} now answer the way a deleted file does."),
        ("Does this page name any of the sites it measured?",
         "No. It publishes counts and shares only, and so does the download."),
    ]

    return render(
        cat="index", slug="llms-txt-adoption-2026-10",
        title=f"llms.txt in the top 10,000 sites: {a_pct}% to {o_pct}%",
        desc=(f"The same 10,000 sites asked for /llms.txt in August and October 2026: real files "
              f"rose from {_c(a['confirmed'])} to {_c(o['confirmed'])}, and under half of the "
              f"sites answering 200 had one."),
        h1="llms.txt in the top 10,000 sites, two months apart",
        crumb='<a href="/">Docket</a> / <a href="/index/">The Index</a> / llms.txt adoption, October 2026',
        body=body,
        published="2026-10-19",
        faq=faq,
    )


BUILDERS = [llms_adoption]


def build_all() -> list:
    return [b() for b in BUILDERS]


if __name__ == "__main__":
    for p in build_all():
        print(p)
