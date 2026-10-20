#!/usr/bin/env python3
"""/index/ai-crawler-blocking-2026-10/: the Tranco top 10,000 read again.

The August 2026 survey (`/index/ai-directives/`) read the robots.txt of the
Tranco top 10,000. This page is the same list and the same definitions, two months
on, read with the method as far as the August record lets us repeat it, and what moved.
Where the two runs differ, or may, the page says so (see `_differences` below).

Every number is read out of data/ai-crawler-blocking-2026-10.json through
`facts.blk*`, which scripts/build_ai_crawler_blocking.py derives from the two
raw surveys. It holds aggregates and no host, so this page cannot name a site
even by accident.

WHAT THIS PAGE REFUSES TO SAY, because the data does not:

  1. WHY the Cloudflare-looking block went from so many sites. The files differ
     between August and October and a re-fetch the same day returned the same
     files; nothing in a robots.txt says whether an owner switched a setting
     off, Cloudflare changed what it writes, or an origin began answering.
  2. That a site matching the August pattern IS a Cloudflare customer. In
     August only the parsed result of each file was kept, so the August
     evidence is a pattern. October kept the text, so October has the marker.
  3. That a 403 on /robots.txt means the site blocks AI. It means our bot was
     refused. RFC 9309 lets a crawler treat an unavailable file as no rules.
  4. Anything about what any crawler did. The survey reads requests.
  5. Any site by name.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import facts as F  # noqa: E402
from render import render  # noqa: E402

CF_DOC = F.blk("cloudflare", "doc", "url")


def _pct(count: int, base: int) -> str:
    return f"{100 * count / base:.1f}"


def _c(n: int) -> str:
    return f"{n:,}"


def _owners() -> dict:
    return {name: owner for name, owner, _p, _i in F.ai_agent_rows()}


def _group(bot: str) -> str:
    crawlers = F.blk("crawlers")
    if bot in crawlers["training"]:
        return "Training"
    if bot in crawlers["search"]:
        return "Search"
    if bot == "Google-Extended":
        return "Counted on its own"
    return "In neither group"


def _headline_rows() -> str:
    ra, ro = F.blk("aug", "readable"), F.blk("oct", "readable")
    rows = []
    for key, label in (("training", "Blocks at least one AI training crawler"),
                       ("search", "Blocks at least one AI search crawler"),
                       ("google_extended", "Blocks Google-Extended"),
                       ("any_of_nine", "Blocks at least one of the nine"),
                       ("training_only", "Blocks training and no search crawler")):
        a, o = F.blk_count(key, "aug"), F.blk_count(key, "oct")
        rows.append(f"<tr><td>{label}</td><td>{_c(a)}</td><td>{_pct(a, ra)}%</td>"
                    f"<td>{_c(o)}</td><td>{_pct(o, ro)}%</td></tr>")
    return "".join(rows)


def _change_rows() -> str:
    rows = []
    for key, label in (("training", "At least one training crawler"),
                       ("search", "At least one search crawler"),
                       ("google_extended", "Google-Extended"),
                       ("any_of_nine", "At least one of the nine")):
        c = F.blk("change", key)
        net = c["gained"] - c["lost"]
        sign = "+" if net > 0 else ("-" if net < 0 else "")
        rows.append(f"<tr><td>{label}</td><td>{_c(c['both'])}</td><td>{_c(c['gained'])}</td>"
                    f"<td>{_c(c['lost'])}</td><td>{sign}{_c(abs(net))}</td></tr>")
    return "".join(rows)


def _crawler_rows() -> str:
    ra, ro = F.blk("aug", "readable"), F.blk("oct", "readable")
    owners = _owners()
    shares = F.blk("shares")
    order = sorted(F.blk("crawlers", "shown"),
                   key=lambda b: -shares[f"bot:{b}"]["oct"])
    rows = []
    for bot in order:
        s, c = shares[f"bot:{bot}"], F.blk("change", f"bot:{bot}")
        rows.append(
            f"<tr><td><code>{bot}</code></td><td>{owners.get(bot, '')}</td>"
            f"<td>{_group(bot)}</td><td>{_c(s['aug'])} ({_pct(s['aug'], ra)}%)</td>"
            f"<td>{_c(s['oct'])} ({_pct(s['oct'], ro)}%)</td>"
            f"<td>{_c(c['gained'])}</td><td>{_c(c['lost'])}</td></tr>")
    return "".join(rows)


def _updated() -> str:
    """The dated correction: what the re-reads changed, old figure beside new.

    The survey keeps, per host, the record a re-read replaced, so the figures as first
    published on 19 October are rebuilt from those (build_ai_crawler_blocking.py) rather
    than typed here. A headline whose percentage moved is named "now X (was Y)"; one that
    did not is named as unchanged, with its counts, because the counts did move.
    """
    rr = F.blk("reread")
    passes, fp = rr["passes"], rr["first_published"]
    upd = F.blk_fmt(max(p["date"] for p in passes))
    first = F.blk_date("oct")
    p308 = next(p for p in passes if p["kind"] == "308")
    pconn = next(p for p in passes if p["kind"] == "connect")
    ro_old, ro = fp["oct"]["readable"], F.blk("oct", "readable")
    changed, same = [], []
    for key, label in (("training", "training-crawler blocking"),
                       ("search", "search-crawler blocking"),
                       ("google_extended", "Google-Extended blocking")):
        old_n, new_n = fp["shares"][key], F.blk("shares", key, "oct")
        old_p, new_p = _pct(old_n, ro_old), _pct(new_n, ro)
        if old_p != new_p:
            changed.append(f"{label} is now {new_p}% ({_c(new_n)} of {_c(ro)}), was {old_p}% "
                           f"({_c(old_n)} of {_c(ro_old)}) on {first}")
        else:
            same.append(f"{label} at {new_p}% ({_c(new_n)} of {_c(ro)}, was {_c(old_n)} of {_c(ro_old)})")
    old_e, new_e = fp["effect"]["training"], F.blk("cloudflare", "effect", "training")
    old_cf = f"{old_e['lost_with_august_signature']} of {old_e['lost']}"
    new_cf = f"{new_e['lost_with_august_signature']} of {new_e['lost']}"
    if old_cf != new_cf:
        changed.append(f"the sites that stopped blocking a training crawler and had the August "
                       f"Cloudflare pattern are now {new_cf}, were {old_cf}")
    else:
        same.append(f"the Cloudflare-pattern share of the sites that stopped, {new_cf}")
    if old_e["net_without_cloudflare"] != new_e["net_without_cloudflare"]:
        changed.append(f"the net rise in training-crawler blocking without the Cloudflare-pattern sites is now "
                       f"{new_e['net_without_cloudflare']}, was {old_e['net_without_cloudflare']}")
    else:
        same.append(f"the net rise without the Cloudflare-pattern sites, {new_e['net_without_cloudflare']}")
    moved = ("What moved: " + "; ".join(changed) + "." if changed
             else "No percentage on this page changed.")
    stayed = (" Unchanged at one decimal, though their counts moved: " + "; ".join(same) + "."
              if same else "")
    return f"""<div class="callout">
<div class="callout-title">Updated {upd}</div>
<p>On {first} the collector stopped at a <code>308</code> redirect it did not follow for
{p308['was_robots_308']} <code>/robots.txt</code> requests and {p308['was_llms_308']}
<code>/llms.txt</code> requests. Another {_c(pconn['hosts'])} sites had not connected, or had fallen
back to plain http, under an older Python and TLS library that may have read them wrongly. We read
all {_c(p308['hosts'] + pconn['hosts'])} again on {upd}, under Python <code>3.11</code>, with
redirects followed. The figures on this page include the new reads. The readable base is now
{_c(ro)} files, was {_c(ro_old)}. {moved}{stayed}</p>
<p>The new reads made {_c(p308['became_readable'] + pconn['became_readable'])} sites readable that were
not, and {pconn['stopped_readable']} that were readable were not reached the second time. The sites
that read fine on {first} were not read again.</p>
</div>"""


def _differences() -> str:
    """One plain line for each way the two runs differ, or may, that a re-read cannot remove."""
    sens = F.blk("sensitivity")
    http, big, base = sens["http_read"], sens["above_august_largest"], sens["as_published"]
    size = F.blk("size")

    def tr(block):
        return _pct(block["training"], block["readable"])

    def without(block):
        """"Without them, X% instead of Y%", or "still Y%" when the tenth did not move."""
        if tr(block) == tr(base):
            return f"Without them, training-crawler blocking is still {tr(base)}%."
        return (f"Without them, training-crawler blocking is {tr(block)}% "
                f"instead of {tr(base)}%.")

    return f"""<h3>Where October may differ from August</h3>

<p>We compared the two runs point by point. These are the same: the host list and its rank order,
the {F.blk('meta', 'probed_crawlers')} crawlers asked about (the same names), the parser, the
{timeout_text()}-second timeout and no retries as August's published method states, and how an answer
becomes a state (a 200 is readable, any other status is no robots.txt, no answer is unreachable).
These differ, or may:</p>

<ul>
<li><strong>The user agent.</strong> October's is explained on <a href="/bot/">the bot page</a>.
August's string was not kept, so we cannot say the two were the same. A site that answers
different agents differently would show it, most of all in the refusals.</li>
<li><strong>Pace and order.</strong> October asked {F.blk('meta', 'workers')} sites at a time in a
shuffled order and took {F.blk_minutes('oct')} minutes. August's pace and order were not recorded;
it took {F.blk_minutes('aug')}.</li>
<li><strong>Plain http.</strong> October tried plain http when https could not connect:
{_c(http['hosts'])} sites, {_c(http['readable'])} of them readable. August's record does not say
whether it did. {without(http['without']).replace('Without them', 'Without those ' + _c(http['readable']))}</li>
<li><strong>The file-size cutoff.</strong> October did not parse files above
{_c(F.blk('meta', 'oversize_bytes'))} bytes. August's cutoff was not kept, and lay above
{_c(size['largest_readable_aug'])}. {big['files']} October files are larger than anything August
parsed. {without(big['without'])}</li>
<li><strong>The Python that ran it.</strong> October's main run used Python <code>3.9</code> and
an older TLS library. August's records read as a newer Python's: they hold no unfollowed
<code>308</code>. That is why the redirects and the sites that had not connected were read again
(see the update above). A site that the older library reached and the newer one would not is
still counted, because sites that read fine were not read again.</li>
</ul>"""


def timeout_text() -> str:
    return str(int(F.blk("meta", "timeout_s")))


def ai_crawler_blocking() -> Path:
    att = F.blk("oct", "attempted")
    ra, ro = F.blk("aug", "readable"), F.blk("oct", "readable")
    panel = F.blk("panel", "n")
    aug_date, oct_date = F.blk_date("aug"), F.blk_date("oct")
    aug_month = F.blk_month("aug")

    tr_a, tr_o = F.blk_pct("training", "aug"), F.blk_pct("training", "oct")
    se_a, se_o = F.blk_pct("search", "aug"), F.blk_pct("search", "oct")
    ge_a, ge_o = F.blk_pct("google_extended", "aug"), F.blk_pct("google_extended", "oct")
    tr_chg, se_chg = F.blk("change", "training"), F.blk("change", "search")
    ge_chg = F.blk("change", "google_extended")

    cf = F.blk("cloudflare")
    eff_tr = cf["effect"]["training"]
    eff_ge = cf["effect"]["google_extended"]
    flow = cf["signature_flow"]
    cf_aug, cf_oct = cf["august"], cf["october"]
    kinds = cf_oct["kinds"]
    docs_n = len(cf["documented_agents"])
    docs_names = ", ".join(f"<code>{a}</code>" for a in cf["documented_agents"])
    longer = kinds.get("longer", 0)
    other_names = ", ".join(f"<code>{a}</code>"
                            for a in cf_aug["largest_cluster"]["names_beyond_the_documented_eight"])
    sig_aug = cf_aug["signature_all"]
    moved = F.blk("movement")
    ref = F.blk("refusal")
    rc = F.blk("recheck")
    re_asked = rc["gone"]["asked"] + rc["kept"]["asked"]
    re_same = rc["gone"]["same_file"] + rc["kept"]["same_file"]
    par = F.blk("parser")
    size = F.blk("size")
    n_probe = F.blk("meta", "probed_crawlers")
    top_o, top_o_n = F.blk_top(key="oct")
    top_a, _top_a_n = F.blk_top(key="aug")
    as_in_aug = ", as it was in August" if top_o == top_a else ""
    timeout_s = int(F.blk("meta", "timeout_s"))
    unreach_a, unreach_o = F.blk("aug", "unreachable"), F.blk("oct", "unreachable")
    norobots_o, over_o = F.blk("oct", "no_robots"), F.blk("oct", "oversize")
    train_names = ", ".join(f"<code>{b}</code>" for b in F.blk("crawlers", "training"))
    search_names = ", ".join(f"<code>{b}</code>" for b in F.blk("crawlers", "search"))
    no_marker_sentence = (
        "None of them carries the Cloudflare comments."
        if flow["gone_still_readable_no_marker"] == flow["gone_still_readable"]
        else f"{flow['gone_still_readable_no_marker']} of them carry none of the Cloudflare comments.")
    cf_share_of_lost = _pct(eff_tr["lost_with_august_signature"], eff_tr["lost"])
    net_wo = eff_tr["net_without_cloudflare"]
    rise_pts = f"{100 * net_wo / panel:.1f}"

    body = f"""
<p class="lede">In {aug_month} we read the robots.txt of the Tranco top 10,000 sites. On
{oct_date} we read the same list again, as close to the same way as the August record allows.
<strong>{tr_o}% of the files we could read
now block at least one AI training crawler, down from {tr_a}%.</strong> The share blocking an AI
search crawler is {se_o}%, against {se_a}% before. The drop in training-crawler blocking has a
clear shape: {eff_tr['lost_with_august_signature']} of the {_c(eff_tr['lost'])} sites that stopped
blocking one had, in August, the pattern of Cloudflare's managed robots.txt block.</p>

<div class="stat-row">
<div class="stat"><b>{tr_o}%</b><span>block a training crawler (was {tr_a}%)</span></div>
<div class="stat"><b>{se_o}%</b><span>block a search crawler (was {se_a}%)</span></div>
<div class="stat"><b>{ge_o}%</b><span>block Google-Extended (was {ge_a}%)</span></div>
<div class="stat"><b>{cf_share_of_lost}%</b><span>of the sites that stopped blocking training looked like Cloudflare's block</span></div>
</div>

{_updated()}

<h2>The headline numbers</h2>

<p>Every percentage here is a share of the sites whose robots.txt we could read: {_c(ra)} in
{aug_month} and {_c(ro)} in October. Sites move in and out of that group, which is why the
next section compares the sites that were readable both times.</p>

<div class="wrap-tbl"><table class="cmp">
<thead><tr><th>Share of readable files</th><th>August sites</th><th>August</th><th>October sites</th><th>October</th></tr></thead>
<tbody>{_headline_rows()}</tbody></table></div>

<p>The training crawlers are {train_names}. The search crawlers, the ones that decide whether a
site can be cited in an AI answer, are {search_names}. <code>Google-Extended</code> is counted on
its own, because Google documents it as the control for Gemini training and says AI features in
Search follow the Googlebot rules. These are the same definitions the
<a href="/index/ai-directives/">August survey</a> used. A file blocks a crawler when it
disallows the site root for that name, which is a statement about what the file asks and not
about what any crawler did.</p>

<h2>What changed on the same sites</h2>

<p>{_c(panel)} sites had a readable file in both months. Comparing them with themselves leaves
out the {_c(F.blk('panel', 'readable_aug_only'))} that were readable only in August and the
{_c(F.blk('panel', 'readable_oct_only'))} readable only in October.</p>

<div class="wrap-tbl"><table class="cmp">
<thead><tr><th>Blocking, same {_c(panel)} sites</th><th>Both months</th><th>Started</th><th>Stopped</th><th>Net</th></tr></thead>
<tbody>{_change_rows()}</tbody></table></div>

<p>Most sites did not move. {_c(moved['same'])} of the {_c(panel)} blocked exactly the same set
of the {n_probe} crawlers we checked in both months. {moved['more_blocked']} blocked more,
{moved['fewer_blocked']} blocked fewer, and {moved['mixed']} added some and dropped others.</p>

<p>The search crawlers barely moved: {se_chg['gained']} sites started blocking one and
{se_chg['lost']} stopped. The movement was in the training crawlers and in
<code>Google-Extended</code>, and it ran one way. {_c(tr_chg['lost'])} sites stopped blocking a
training crawler and {tr_chg['gained']} started. For <code>Google-Extended</code> the figures
are {_c(ge_chg['lost'])} and {ge_chg['gained']}.</p>

<h2>Crawler by crawler</h2>

<p>Shares here use all readable files in each month. Started and stopped use the same sites in
both. <code>{top_o}</code> is the name blocked most often in October, by {_c(top_o_n)} sites{as_in_aug}.</p>

<div class="wrap-tbl"><table class="cmp">
<thead><tr><th>Crawler</th><th>Operator</th><th>Group</th><th>August</th><th>October</th><th>Started</th><th>Stopped</th></tr></thead>
<tbody>{_crawler_rows()}</tbody></table></div>

<h2>How much of this is Cloudflare's managed robots.txt</h2>

<p>Cloudflare can put a block of lines at the top of a site's robots.txt. Its
<a href="{CF_DOC}" rel="noopener">documentation</a>, which we read on
{F.blk_fmt(cf['doc']['read'])} and which is dated {F.blk_fmt(cf['doc']['page_dated'])}, shows
the block: a <code>Content-signal</code> line, an <code>Allow: /</code> for everyone, and a
<code>Disallow: /</code> for {docs_n} named AI crawlers ({docs_names}), all between the
comments <code>{cf['doc']['begin_marker']}</code> and <code>{cf['doc']['end_marker']}</code>.
We matched against that text.</p>

<h3>October: the text itself</h3>

<p>In October we kept each file's text, so we could look for those comments.
{cf_oct['marker_all']} of the {_c(ro)} readable files carry them. Only {cf_oct['verbatim_documented']}
of those matches the documented block line for line. {longer} carry a longer list of crawler
names, and {cf_oct['modal_block']['files']} of those share the same list of
{cf_oct['modal_block']['crawlers']} names. Cloudflare's page says the lines are generated from a site's
Search, Agent and Training policies, which would explain a list longer than the one it prints. A
further {cf_oct['policy_comment_only']} files carry only the comment block that explains Content
Signals, with no rule that restricts anything.</p>

<h3>August: a pattern, not a text</h3>

<p>The August survey kept what its parser made of each file and not the text, so there is no
comment to look for. What it kept does show a pattern: a <code>Content-signal</code> line and a
<code>Disallow</code> for all {docs_n} documented crawlers. {sig_aug} readable files matched.
{cf_aug['largest_cluster']['files']} of them were the same length,
{_c(cf_aug['largest_cluster']['bytes'])} bytes, with the same {cf_aug['largest_cluster']['user_agent_lines']}
user-agent lines, one of which ({other_names}) is not in the documented block. Files that
identical were generated, not typed, and Cloudflare's page says it creates the whole file for a
site that has none. We say the August matches look like Cloudflare's block. We cannot prove it
from parsed data.</p>

<h3>Where the August pattern went</h3>

<ul>
<li>{flow['kept']} still match, readable in both months.</li>
<li>{flow['gone_still_readable']} are readable in both months and no longer match.
{no_marker_sentence}</li>
<li>{flow['gone_refused']} now refuse our bot when it asks for robots.txt.</li>
<li>{flow['gone_no_robots_other'] + flow['gone_unreachable'] + flow['gone_oversize']} are
unreachable, answer with some other error, or serve a file too large to parse.</li>
</ul>

<h3>What it does to the headline</h3>

<p>Of the {_c(eff_tr['lost'])} sites that stopped blocking a training crawler,
{eff_tr['lost_with_august_signature']} ({cf_share_of_lost}%) matched the August pattern. Of the
{eff_tr['gained']} that started, {eff_tr['gained_with_marker_or_signature']} carry the October
comments or match the pattern. Set those aside and training-crawler blocking went the other
way: {eff_tr['gained_without']} sites started and {eff_tr['lost_without']} stopped, a net rise of
{net_wo} sites, or {rise_pts} percentage points of the {_c(panel)}. The same holds for
<code>Google-Extended</code>, where {eff_ge['lost_with_august_signature']} of the
{eff_ge['lost']} that stopped matched the pattern.</p>

<h3>What we cannot tell you</h3>

<p>Why. Some owners will have switched the setting off. Cloudflare may have changed what it
writes: its page for the setting was last updated {F.blk_fmt(cf['doc']['page_dated'])}, and we
did not test whether that matters. An origin server may have started answering with a robots.txt
where there was none. What we can say is that the files differ, and that the difference is not a
glitch of one fetch: we asked again, later the same day, for {re_asked} of them, and {re_same}
came back byte for byte the file we had stored.</p>

<h2>Blocking that robots.txt cannot show</h2>

<p>A server can say no without a rule. {_c(ref['aug'])} hosts refused our bot outright in August,
with a 401, 403, 406, 429 or 503 before any robots.txt rule applied, and {_c(ref['oct'])} did in
October. {ref['readable_aug_now_refused']} sites whose file we could read in August now refuse
us, and {ref['refused_aug_now_readable']} went the other way. Of the {sig_aug} sites that matched
the August Cloudflare pattern, {ref['signature_hosts_now_refused']}
({_pct(ref['signature_hosts_now_refused'], sig_aug)}%) now refuse us, against
{_c(ref['other_readable_now_refused'])} of the other {_c(ref['other_readable'])} readable sites
({_pct(ref['other_readable_now_refused'], ref['other_readable'])}%).</p>

<p>We did not count a refusing host as blocking. A refusal says nothing about what the file
says, and <a href="https://www.rfc-editor.org/rfc/rfc9309" rel="noopener">RFC 9309</a> lets a
crawler that meets an unavailable robots.txt treat the site as having no rules. Refusing hosts
are not in the same-sites comparison above. They matter because the other way to keep AI out is
the server, and that route is
<a href="/how-to/fix-ai-crawlers-blocked-by-your-cdn/">a CDN rule can do it with no trace in the file</a>.</p>

<h2>How we measured</h2>

<p><strong>Sample.</strong> The host list and the rank order are the {aug_month} survey's,
unchanged: the <a href="https://tranco-list.eu/" rel="noopener">Tranco</a> top 10,000, list
PYG5J. We did not refresh it, so a site that has entered or left the top 10,000 since is not
here. {_c(att)} hosts were attempted in both months.</p>

<p><strong>Collection.</strong> On {oct_date}, from one computer, we asked each host for
<code>/robots.txt</code> once over https, and over plain http only when https could not connect
at all. The user agent names this survey and links to <a href="/bot/">the page that explains it</a>.
A timeout of {timeout_s} seconds, no retries, {F.blk('meta', 'workers')} different hosts at a time. Where the file
let our user agent fetch <code>/llms.txt</code> we asked for that too, with one extra request
for a path that cannot exist; those results have <a href="/index/llms-txt-adoption-2026-10/">a page of their own</a> and are not reported here. The run took
{F.blk_minutes('oct')} minutes. The {aug_month} run took {F.blk_minutes('aug')}. The sites counted in the update at
the top were read again with the same user agent and the same rules.</p>

<p><strong>Reading the files.</strong> Docket's robots.txt parser was fixed in two ways after
the August survey. A comment line or a blank line used to end a group, so the rules after it were
dropped. And when a file had two <code>User-agent: *</code> groups, only the first was read. To
compare like with like, every figure on this page uses the parser as it stood in August. Read with today's
parser the same October files give {_c(par['training_current_parser'])} sites blocking a training
crawler instead of {_c(par['training_aug_parser'])}, and {_c(par['files_read_differently'])} files
read differently in all. The fix makes the October figures a little higher, not lower. We cannot re-read August with
it, because August's text was not kept, which is why both months use the older reading.</p>

<p><strong>Rebuilding the collector.</strong> The script that gathered the August data is in
neither of our repositories, so we rebuilt it from the August records and the method published
with them. We checked what can be checked: the code that turns raw records into figures, run on
the August records, returns the August figures this site already published. That covers the
arithmetic and not the collector. The nearest comparison for the collector is the mix of
outcomes. {_pct(F.blk('aug', 'unreachable'), att)}% of hosts were unreachable in August and
{_pct(unreach_o, att)}% in October; {_pct(ra, att)}% had a readable file in August and
{_pct(ro, att)}% in October.</p>

{_differences()}

<h2>What this does not tell you</h2>

<ul>
<li><strong>It is the top of the web, not the web.</strong> Percentages describe these
{_c(att)} sites on these two days. A small business site is unlikely to be on the list.</li>
<li><strong>Some sites are in no percentage.</strong> In October {_c(unreach_o)} hosts were
unreachable, {_c(norobots_o)} answered with no robots.txt, and {_c(over_o)} served a file above
the size limit.</li>
<li><strong>A readable file is not always a real one.</strong> A 200 response that turns out to
be an error page or an empty body counts as readable and blocks nothing, as it did in August.</li>
<li><strong>August's Cloudflare evidence is a pattern.</strong> Only October has the text.</li>
<li><strong>The size limit was reconstructed.</strong> The largest readable file was
{_c(size['largest_readable_aug'])} bytes in August and {_c(size['largest_readable_oct'])} in
October.</li>
<li><strong>One vantage point.</strong> One computer asked on one day. A site that serves
different files to different visitors would not show it.</li>
<li><strong>Requests, not behaviour.</strong> Nothing here says whether any crawler obeyed any
file, or whether blocking one changed anyone's traffic.</li>
</ul>

<h2>Get the data</h2>

<p>The summary behind every table above is one small file. It holds counts and no site, and
nothing on this page names one.</p>

<p><a class="btn-ghost" href="/data/ai-crawler-blocking-2026-10.csv">Download the summary (CSV)</a></p>

<div class="callout">
<div class="callout-title">Check your own site</div>
<p>Docket reads your robots.txt one AI crawler at a time and tells you which training and
search crawlers your site blocks, and whether the server agrees with the file. The <a href="/tools/ai-crawler-checker/">free checker</a> does it for one address.</p>
</div>

<p><a class="btn" href="/download/">Download Docket</a></p>
"""

    faq = [
        ("Did more sites block AI crawlers in October 2026 than in August?",
         f"Fewer blocked a training crawler. {tr_o}% of readable robots.txt files in the Tranco "
         f"top 10,000 did in October, against {tr_a}% in August. The share blocking an AI "
         f"search crawler was {se_o}%, against {se_a}%. On the same {_c(panel)} sites, "
         f"{_c(tr_chg['lost'])} stopped blocking a training crawler and {tr_chg['gained']} "
         "started."),
        ("What does Cloudflare's managed robots.txt look like?",
         f"A block of lines at the top of the file, between the comments "
         f"{cf['doc']['begin_marker']} and {cf['doc']['end_marker']}. It carries a "
         f"Content-signal line, Allow: / for everyone, and Disallow: / for named AI crawlers. "
         f"Cloudflare's page prints {docs_n} names. In October, {cf_oct['marker_all']} of "
         f"{_c(ro)} readable files carried the comments."),
        ("Which AI crawler do sites block most often?",
         f"{top_o}, in October, at {_c(top_o_n)} of {_c(ro)} readable files. The search "
         "crawlers are blocked far less often than the training crawlers."),
        ("Does this page name any of the sites it measured?",
         "No. It publishes counts and shares only, and so does the download."),
    ]

    desc = (f"The same 10,000 sites' robots.txt, read in August and October: AI "
            f"training-crawler blocking fell from {tr_a}% to {tr_o}%, mostly sites that "
            f"look like Cloudflare's block.")
    return render(
        cat="index", slug="ai-crawler-blocking-2026-10",
        title=f"Sites blocking AI training crawlers: {tr_a}% to {tr_o}%",
        desc=desc,
        h1="Who blocks AI crawlers: the same 10,000 sites, two months apart",
        crumb='<a href="/">Docket</a> / <a href="/index/">The Index</a> / AI crawler blocking, October 2026',
        body=body,
        published="2026-10-19",
        modified="2026-10-20",
        faq=faq,
    )


BUILDERS = [ai_crawler_blocking]


def build_all() -> list:
    return [b() for b in BUILDERS]


if __name__ == "__main__":
    for p in build_all():
        print(p)
