#!/usr/bin/env python3
"""ADA Title II website dates: a dated explainer and a "Which date applies to us?" calculator.

Matthew, 2026-11-07 ~23:3xZ via the CEO ("do all of these", the AI-2030 report's top three): Docket Public Site Check
for towns, counties and small public bodies. These two pages are its first, content-only step.

EVERY FACT IS FROM THE GOVERNMENT'S OWN TEXT, read 2026-11-07 and kept in data/title-ii.json: the dates from the interim
final rule in the Federal Register (91 FR 20902, 20 April 2026), the five exceptions from 28 CFR 35.201 and the
definitions in 35.104 on eCFR. Nothing here is legal advice and the pages say so; nothing says "compliant".
"""
from __future__ import annotations

import datetime
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from render import render  # noqa: E402

T = json.loads((Path(__file__).resolve().parents[2] / "data" / "title-ii.json").read_text())


def _day(iso: str) -> str:
    d = datetime.date.fromisoformat(iso)
    return f"{d.day} {d:%B %Y}"


LARGE, SMALL = _day(T["large_date"]), _day(T["small_date"])
LARGE_BEFORE, SMALL_BEFORE = _day(T["large_date_before"]), _day(T["small_date_before"])
CHECKED = _day(T["checked"])
POP = f"{T['threshold']:,}"
IFR = T["ifr"]
NOT_ADVICE = ("This page explains the rule in plain words. It is not legal advice; for a decision about your own body, "
              "ask your attorney.")


def _exceptions() -> str:
    return "".join(f"<li><strong>{name}.</strong> {what}</li>" for name, what in T["exceptions"])


def dates_page() -> Path:
    n = len(T["exceptions"])
    body = f"""
<p class="lede"><strong>The ADA Title II website dates moved by one year.</strong> State and local governments with a
total population of {POP} or more now have until <strong>{LARGE}</strong>. Smaller ones, and every special district,
have until <strong>{SMALL}</strong>. The standard did not change: {T["standard"]}.</p>
<p class="tool-free">Checked {CHECKED} against the Federal Register and the current regulation.
<a href="/tools/title-ii-date/">Work out which date applies to you</a>.</p>

<h2>What changed, and what did not</h2>
<p>The Department of Justice published an interim final rule on {_day(IFR["published"])}
(<a href="{IFR["url"]}" rel="noopener">{IFR["citation"]}</a>). It moved the first date from {LARGE_BEFORE} to
{LARGE}, and the second from {SMALL_BEFORE} to {SMALL}. In its own words, it &ldquo;does not alter the substantive
requirements adopted in the 2024 final rule&rdquo;: the same websites, apps and documents are covered, to the same
standard. Comments on the change closed on {_day(IFR["comments_closed"])}, and the Department said it may propose
further changes, so check the date again before you plan around it.</p>

<h2>Which date is yours</h2>
<ul>
<li><strong>{LARGE}</strong>: a state, county, city, town, township or other public body whose total population is
{POP} or more.</li>
<li><strong>{SMALL}</strong>: a public body whose total population is under {POP}, and every special district
(a water, fire, library, park or transit district, for example), whatever its size.</li>
</ul>
<p>&ldquo;Total population&rdquo; is the Census Bureau&rsquo;s figure from the most recent decennial census. A school
district uses the Census Bureau&rsquo;s school district estimate. An agency or authority that has no figure of its
own uses the combined population of the governments it belongs to. The
<a href="/tools/title-ii-date/">date checker</a> walks through it.</p>

<h2>The {n} exceptions, in plain words</h2>
<p>The rule lists {n} kinds of content that do not have to meet the standard ({T["exceptions_section"]}):</p>
<ol>{_exceptions()}</ol>
<p>The second one matters most for a town: agendas, minutes and old reports posted as PDFs before your date are
exempt, unless people still use them to apply for or take part in something. A form or an application posted years ago
is not exempt if it is still how people apply. Anything you post after your date has to meet the standard.</p>

<h2>What to do before your date</h2>
<ol>
<li>Find out which date is yours, using the census figure.</li>
<li>List what is on the site: pages, PDFs, forms, embedded tools from vendors, and any app.</li>
<li>Sort the documents by posting date, so you know which are older and exempt, and which are new or still used to
apply for something.</li>
<li>Check the pages and new documents against {T["standard"]}, and fix what fails, starting with what people need
to apply, pay, register or attend.</li>
<li>Ask every vendor whose content sits on your site what they are doing; content they post for you is yours.</li>
</ol>
<p>An automated check finds some problems, not all of them, and no overlay or widget makes a site meet the standard
by itself. Real fixes are made in the pages and documents.</p>

<p class="qual">{NOT_ADVICE}</p>

<h2>Related</h2>
<ul>
<li><a href="/tools/title-ii-date/">Which Title II date applies to us?</a></li>
<li><a href="/learn/seo-audit/">What a site audit checks</a></li>
</ul>
"""
    return render(
        cat="learn", slug="ada-title-ii-website-dates",
        title=f"ADA Title II website dates: {LARGE} and {SMALL}",
        desc=(f"The DOJ moved the ADA Title II website dates to {LARGE} ({POP}+ people) and {SMALL} (smaller "
              f"bodies, special districts). The {len(T['exceptions'])} exceptions, plainly."),
        h1=f"The ADA Title II website dates moved: {LARGE} and {SMALL}",
        crumb='<a href="/">Docket</a> / <a href="/learn/">Learn</a> / ADA Title II website dates',
        body=body,
        published="2026-11-07",   # first published; the facts are re-checked on T["checked"]
        faq=[
            ("When do local governments have to meet the ADA Title II web rule?",
             f"{LARGE} for state and local governments with a total population of {POP} or more; {SMALL} for "
             f"smaller ones and all special districts. The Department of Justice moved both dates by one year on "
             f"{_day(IFR['published'])}."),
            ("What standard does the ADA Title II web rule use?",
             f"{T['standard']}. The interim final rule changed only the dates."),
            ("Do old PDFs on a town website have to be made accessible?",
             "Not if they were posted before your date, unless people still use them to apply for, get or take part "
             "in a service, programme or activity. Documents posted after your date have to meet the standard."),
        ],
    )


TOOL_JS = r"""
(function () {
  var f = document.getElementById('t2-form'); if (!f) return;
  var out = document.getElementById('t2-out'), kind = document.getElementById('t2-kind'), pop = document.getElementById('t2-pop');
  var popRow = document.getElementById('t2-pop-row'), popLabel = document.getElementById('t2-pop-label');
  var D = JSON.parse(document.getElementById('t2-data').textContent);
  var labels = {county: 'Population of the county (decennial census)', municipal: 'Population of the city, town, village or township (decennial census)',
                school: "Population of the school district (Census Bureau's school district estimate)",
                instrumentality: 'Combined population of the governments it belongs to (decennial census)'};
  function sync() {
    var k = kind.value; var needs = (k in labels);
    popRow.hidden = !needs; if (needs) popLabel.textContent = labels[k];
  }
  kind.addEventListener('change', function () { sync(); out.hidden = true; });
  f.addEventListener('submit', function (e) {
    e.preventDefault(); var k = kind.value, why, when;
    if (!k) { out.hidden = false; out.textContent = 'Choose the kind of public body first.'; return; }
    if (k === 'special') { when = D.small; why = 'Every special district has the later date, whatever its size.'; }
    else if (k === 'state') { when = D.large; why = 'Every state has more than ' + D.pop + ' people.'; }
    else {
      var n = parseInt(String(pop.value).replace(/[^0-9]/g, ''), 10);
      if (!(n >= 0)) { out.hidden = false; out.textContent = 'Enter the population as a number.'; pop.focus(); return; }
      if (n >= D.threshold) { when = D.large; why = n.toLocaleString('en-US') + ' is ' + D.pop + ' or more.'; }
      else { when = D.small; why = n.toLocaleString('en-US') + ' is under ' + D.pop + '.'; }
    }
    out.hidden = false;
    out.innerHTML = '';
    var p1 = document.createElement('p'); p1.className = 't2-when'; p1.textContent = 'Your date: ' + when + '.'; out.appendChild(p1);
    var p2 = document.createElement('p'); p2.textContent = why + ' From then, your website and apps, and documents you post from that date, have to meet ' + D.standard + ', apart from the ' + D.n + ' exceptions.'; out.appendChild(p2);
  });
  sync();
})();
"""


def date_tool() -> Path:
    ex = T["examples"]; tw, co, parts = ex["township"], ex["county"], ex["authority_parts"]
    both = sum(parts)
    def when(n): return LARGE if n >= T["threshold"] else SMALL
    data = json.dumps({"large": LARGE, "small": SMALL, "threshold": T["threshold"], "pop": POP, "standard": T["standard"], "n": str(len(T["exceptions"]))})
    body = f"""
<p class="lede">Choose the kind of public body and, where asked, its census population. The answer comes from the
rule as it stands on {CHECKED}: {LARGE} for {POP} people or more, {SMALL} for fewer and for every special district.</p>
<form id="t2-form" class="checker-form" autocomplete="off" novalidate>
<label for="t2-kind">Kind of public body</label>
<div class="checker-row">
<select id="t2-kind" required>
<option value="">Choose one</option>
<option value="state">A state government, or one of its agencies</option>
<option value="county">A county</option>
<option value="municipal">A city, town, village or township</option>
<option value="school">An independent school district</option>
<option value="special">A special district (water, fire, library, park, transit and similar)</option>
<option value="instrumentality">An agency or authority of one or more local governments</option>
</select>
</div>
<div id="t2-pop-row" hidden>
<label id="t2-pop-label" for="t2-pop">Population</label>
<div class="checker-row">
<input id="t2-pop" type="text" inputmode="numeric" placeholder="for example {tw:,}">
</div>
</div>
<div class="checker-row" style="margin-top:.9rem"><button type="submit" class="btn">Find our date</button></div>
</form>
<div id="t2-out" class="tool-out" aria-live="polite" hidden></div>
<script type="application/json" id="t2-data">{data}</script>
<script>{TOOL_JS}</script>

<h2>Four examples</h2>
<ul>
<li><strong>A township of {tw:,} people.</strong> Under {POP}, so {when(tw)}.</li>
<li><strong>A county of {co:,} people.</strong> {POP} or more, so {when(co)}. Its townships and villages each go by
their own population, not the county&rsquo;s.</li>
<li><strong>A fire district or a library district.</strong> A special district, so {SMALL}, even if it serves a large
city.</li>
<li><strong>A transit authority set up by two cities.</strong> It has no census figure of its own, so it uses the two
cities&rsquo; populations added together: {parts[0]:,} and {parts[1]:,} make {both:,}, so {when(both)}.</li>
</ul>

<h2>What has to meet the standard on that date</h2>
<p>Your web pages and any mobile app, including what vendors run for you on your site, such as payment, permit or
booking pages. Documents count too: PDFs, Word files, slides and spreadsheets you post from that date on, and older ones
people still use to apply for something. Five kinds of content are exempt, among them older documents that are only
kept for the record and what members of the public post. The explainer lists all five.</p>

<h2>Where to find the population</h2>
<p>The rule uses the Census Bureau&rsquo;s figure from the most recent decennial census; data.census.gov shows it for every
county, city, town and township. A school district uses the Census
Bureau&rsquo;s school district estimate. The <a href="/learn/ada-title-ii-website-dates/">full explainer</a> has the
{len(T["exceptions"])} exceptions and the sources.</p>
<p>Nothing you type leaves your browser, and the checker stores nothing. It covers the date only; whether a page meets the standard is a separate check.</p>
<p class="qual">{NOT_ADVICE}</p>
"""
    return render(
        cat="tools", slug="title-ii-date",
        title="Which ADA Title II date applies to us? Free checker",
        desc=(f"Free checker for towns, counties, school and special districts: is your ADA Title II website date "
              f"{LARGE} or {SMALL}? Based on the current rule."),
        h1="Which ADA Title II website date applies to us?",
        crumb='<a href="/">Docket</a> / <a href="/tools/">Tools</a> / Title II date checker',
        body=body,
        published="2026-11-07",   # first published; the facts are re-checked on T["checked"]
        schema_type="WebPage",
        faq=[
            ("Is a special district on the earlier date if it serves a big city?",
             f"No. Every special district has {SMALL}, whatever its size."),
            ("Which population figure counts?",
             "The Census Bureau's figure from the most recent decennial census; for an independent school district, "
             "the Census Bureau's school district estimate."),
        ],
    )


BUILDERS = [dates_page, date_tool]


def build_all() -> list[Path]:
    return [b() for b in BUILDERS]
