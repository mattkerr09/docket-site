#!/usr/bin/env python3
"""Three distinct comparisons from the supplied 20 November vendor readings."""
from __future__ import annotations

import re
from pathlib import Path

from comparisons import VERIFIED, _measured, _top_cta, source_link
from render import render
import real_questions_sources  # noqa: F401; keep historical scratch builds stable

READ = "20 November 2026"


def note(*keys: str, topic: str) -> str:
    """One short dated note per section, with a named source and local context."""
    names = {"rq-conductor": "Conductor", "rq-seranking": "SE Ranking",
             "rq-screaming-frog": "Screaming Frog", "rq-semrush": "Semrush",
             "rq-sitebulb": "Sitebulb", "rq-jetoctopus": "JetOctopus",
             "rq-google-live": "Google", "rq-google-ranges": "Google", "rq-noindex": "Google"}
    companies = ' and '.join(dict.fromkeys(names[key] for key in keys))
    urls = dict.fromkeys(url for key in keys for _, url in VERIFIED[key])
    links = ', '.join(source_link("Source " + str(i), url) for i, url in enumerate(urls, 1))
    owner = companies + ("'" if companies.endswith("s") else "'s")
    return (f'<p class="verified-note">Checked on {owner} own pages on {READ}. '
            f'Sources for {topic}: {links}.</p>')


def answer_source(text: str, label: str, url: str) -> str:
    """Keep FAQ evidence visible as well as in the matching FAQPage answer."""
    return f'{text} {source_link(label, url)}. Checked {READ}.'


def prices(key: str) -> list[str]:
    """Use the same price strings as the dated claim list, without a second copy."""
    return re.findall(r'\$[\d,]+(?:\.\d+)?', ' '.join(claim for claim, _ in VERIFIED[key]))


def contentking_se_ranking() -> Path:
    sr = "https://seranking.com/subscription.html"
    audit = "https://seranking.com/website-audit.html"
    ck = "https://www.contentkingapp.com"
    conductor = "https://www.conductor.com/platform/monitoring/"
    cp = "https://www.conductor.com/pricing/"
    core, annual_core, growth, annual_growth = prices("rq-seranking")
    history, per_project, core_pages = 60, 2_000_000, 250_000
    body = f"""
<p id="measured-answer">For ContentKing vs SE Ranking, choose Conductor Monitoring for ongoing change checks, or SE Ranking for an audit with a published page allowance.
contentkingapp.com now redirects to {source_link("Conductor's Monitoring page", ck)}, which lists {history} months of history.
{source_link("SE Ranking's audit page", audit)} states up to {per_project:,} pages per project.</p>
{note("rq-conductor", "rq-seranking", topic="the monitoring and audit choice")}
{_top_cta("vs-contentking-seranking", anchor=False)}

<h2>Start with what you need to notice</h2>
<p>A team watching for changes has a different task from a person gathering a list of repairs.
Write down which one you need before comparing prices. A recurring check is useful when someone
will read the changes and act on them. An audit is useful when someone has time set aside to fix
what it finds. Neither buying decision replaces that person.</p>

<h2>Following the ContentKing address today</h2>
<p>The address many readers remember is contentkingapp.com. It now redirects to
{source_link("Conductor Monitoring", conductor)}. Conductor describes continuous monitoring and
{history} months of saved history. That makes it a candidate when keeping a record of changes
matters more to you than starting a fresh crawl by hand.</p>
<p>{source_link("Conductor's pricing page", cp)} publishes no dollar prices. Ask for a quote
for the sites and pages you need to monitor. Do not treat a blank price cell as a free plan.</p>
{note("rq-conductor", topic="Conductor monitoring and pricing")}

<h2>SE Ranking: distinguish a project ceiling from a monthly allowance</h2>
<p>{source_link("SE Ranking Website Audit", audit)} says it can audit up to {per_project:,}
pages per project and names JavaScript rendering. The pricing page also meters pages per month.
Those are different limits. Before running repeated audits, compare your planned total with the
monthly allowance, as well as the size of the largest project.</p>
<div class="wrap-tbl"><table class="cmp">
<caption>SE Ranking prices and monthly audit allowances</caption>
<thead><tr><th scope="col">Plan</th><th scope="col">Monthly billing</th><th scope="col">Annual billing</th><th scope="col">Audit pages per month</th></tr></thead>
<tbody>
<tr><th scope="row">Core</th><td>{core} a month</td><td>{annual_core} a month</td><td>{core_pages:,}</td></tr>
<tr><th scope="row">Growth</th><td>{growth} a month</td><td>{annual_growth} a month</td><td>{per_project:,}</td></tr>
</tbody></table></div>
<p>The regular prices above come from {source_link("SE Ranking's subscription page", sr)}.
Keep the billing choice beside any price you send to a colleague. An annual rate is not the
same commitment as paying for a single month.</p>
{note("rq-seranking", topic="SE Ranking plan limits")}

<h2>Where Check Engine fits this decision</h2>
<p>We make Check Engine. It runs a local audit and ranks fixes by impact and effort. It does
not provide a shared team workspace, and scheduled re-audits run only while the app is open and the computer is awake. If unattended monitoring is the task, keep that requirement at the top of your list.</p>
{_measured("<p>Here is the output from our own site. Use the findings and their scope to judge whether this kind of fix plan matches your work.</p>", view="table")}

<h2>Give change review a named owner</h2>
<p>Before adding another stream of alerts, agree who reads it. A useful review records the
page, what changed, whether the change was intended and what happens next. Route an intended
edit back to the person who made it if the report needs context. Give an unintended edit a
clear repair task. Keeping those decisions together makes the next review easier: someone
can tell a new problem from an old finding that was deliberately accepted.</p>
<p>If nobody can own that review, reserve time for a planned audit instead. The schedule
should match the time you have to investigate, rather than creating a list that grows unread.</p>

<h2>Questions to take to a demo</h2>
<ul>
<li>Which changes will someone on your team review, and who owns the repair?</li>
<li>Does the quote cover all the sites you want to watch?</li>
<li>How many repeat audits fit within the allowance you are buying?</li>
<li>Can you trace a reported change back to a page and decide whether it was intended?</li>
</ul>
<p>For the desktop option beside SE Ranking, read
<a href="/vs/se-ranking-vs-screaming-frog/">SE Ranking vs Screaming Frog</a>.</p>
"""
    return render(
        cat="vs", slug="contentking-vs-se-ranking",
        title="ContentKing vs SE Ranking: monitoring or an audit?",
        desc="Follow the ContentKing redirect to Conductor Monitoring. Compare its published scope with SE Ranking's audit limits and dated plan prices.",
        h1="ContentKing vs SE Ranking",
        crumb='<a href="/">Check Engine</a> / <a href="/vs/">Compare</a> / ContentKing vs SE Ranking',
        body=body, published="2026-11-20", modified="2026-11-20",
        faq=[
            ("Where does the ContentKing web address lead today?", answer_source(
                "contentkingapp.com now redirects to Conductor's Monitoring page.", "ContentKing address", ck)),
            ("Can I compare a public Conductor dollar price with Core?", answer_source(
                f"Conductor's pricing page publishes no dollar prices. SE Ranking Core is {core} a month on monthly billing or {annual_core} a month on annual billing.",
                "Conductor pricing", cp) + ' ' + source_link("SE Ranking pricing", sr)),
            ("Does SE Ranking's project ceiling replace its monthly audit allowance?", answer_source(
                f"No. Its audit page states up to {per_project:,} pages per project. Its pricing page separately lists pages per month, so check both against your crawl plan.",
                "Audit scope", audit) + ' ' + source_link("Monthly allowances", sr)),
        ],
    )


def screaming_frog_semrush() -> Path:
    sf = "https://www.screamingfrog.co.uk/seo-spider/"
    sfp = "https://www.screamingfrog.co.uk/seo-spider/pricing/"
    sem = "https://www.semrush.com/prices/"
    sa = "https://www.semrush.com/features/site-audit/"
    licence = prices("rq-screaming-frog")[0]
    monthly, annual = prices("rq-semrush")
    free_urls, gbp, demo, reports = 500, 199, 1, 10
    body = f"""
<p id="measured-answer">For Screaming Frog vs Semrush, choose Screaming Frog for a desktop crawl, or Semrush when you want Site Audit alongside daily keyword tracking.
{source_link("Screaming Frog's product page", sf)} offers up to {free_urls} URLs per crawl for free.
{source_link("Semrush's pricing page", sem)} lists the SEO plan at {monthly} a month on monthly billing or {annual} a month billed annually.</p>
{note("rq-screaming-frog", "rq-semrush", topic="the desktop and subscription choice")}
{_top_cta("vs-screamingfrog-semrush", anchor=False)}

<h2>Try the crawl task before choosing a subscription</h2>
<ol>
<li>Pick a section of your site that you know well. Include pages with different templates.</li>
<li>Write down the question you need answered, such as which pages have the wrong title.</li>
<li>Read a finding, open the affected page and check whether you can carry out the repair.</li>
<li>Estimate how often you will repeat that task. Then compare the cost over that period.</li>
</ol>
<p>This keeps the decision tied to work you will do. A long feature list is hard to value
until you know which part will change your next hour of work.</p>

<h2>Screaming Frog: the desktop choice</h2>
<p>{source_link("SEO Spider", sf)} is downloaded desktop software. The free version is
limited to {free_urls} URLs in a single crawl. A licence is {licence} a year in the USD view;
the GBP view is £{gbp} a year. These are annual prices, and licences last a year.</p>
<p>Choose it when you want to run a crawl on your computer. Use the free crawl to judge how
you work with the results before deciding whether to buy a licence. Keep your test's URL count
in view: reaching the free limit does not show that the rest of the site is clear.</p>
{note("rq-screaming-frog", topic="the yearly licence")}

<h2>Semrush: price the wider task too</h2>
<p>The {source_link("Semrush SEO plan", sem)} includes Site Audit, daily keyword tracking
and websites to monitor. The published rate is {monthly} a month on monthly billing, or
{annual} a month billed annually. If you plan to use the keyword tracking as well as the audit,
assess both parts of the purchase.</p>
<p>{source_link("Semrush Site Audit", sa)} lists issues ranked by severity. That gives you a
place to start reading. You still need to inspect the affected page and decide what to change.</p>
<dl>
<dt>Free account wording</dt>
<dd>{demo} demo project and {reports} reports per day across its vital tools.</dd>
<dt>Per-audit page limit</dt>
<dd>Not stated on the pricing and Site Audit pages read for this comparison.</dd>
</dl>
<p>A daily report count is not a count of pages you can crawl. Ask which crawl allowance
applies to your intended plan before committing a large site to it.</p>
{note("rq-semrush", topic="Semrush free and paid accounts")}

<h2>A fix plan from Check Engine</h2>
<p>Check Engine is another desktop choice, bought once. Its report ranks fixes by impact
and effort. It does not track keyword positions. If keyword tracking is part of your brief,
keep a tool that provides it in the comparison.</p>
{_measured("<p>This run shows the kind of repairs our report puts first. It is a dated example from our site, not a speed comparison with either rival.</p>", view="list")}

<h2>Keep the purchase tied to a task you can finish</h2>
<p>Put the task, the person doing it and the expected output in the same note. For example,
you may need a list of pages to edit, with enough detail for the writer to find the right
template. Someone else may need a report they can revisit during a regular review. Open an
example result and try that handoff before choosing a plan. If the recipient still needs
you to explain every row, include that time in the decision.</p>
<p>Keep the billing period in the same note too. That prevents a price copied into a chat
from losing the commitment that went with it.</p>

<h2>Make the next check a practical one</h2>
<p>Save a short list of the findings you expect to work on. After you make those repairs,
repeat the check on the same pages. The useful result is being able to explain what changed,
not simply collecting a different score. See <a href="/learn/seo-audit-report/">how to read a
real audit report</a> for a worked example with its limits left visible.</p>
"""
    return render(
        cat="vs", slug="screaming-frog-vs-semrush",
        title="Screaming Frog vs Semrush: crawl limits and prices",
        desc="Compare Screaming Frog's free desktop crawl and annual USD licence with Semrush SEO pricing. See the free-account wording and missing page limit.",
        h1="Screaming Frog vs Semrush",
        crumb='<a href="/">Check Engine</a> / <a href="/vs/">Compare</a> / Screaming Frog vs Semrush',
        body=body, published="2026-11-20", modified="2026-11-20",
        faq=[
            ("Is the Screaming Frog USD licence a monthly charge?", answer_source(
                f"No. It is {licence} a year in the USD view. The GBP view is £{gbp} a year, and licences last a year.", "Licence pricing", sfp)),
            ("Does a Semrush demo project promise a full-site free crawl?", answer_source(
                "The free account says 1 demo project and 10 reports per day. The pages read do not state a per-audit page limit, so those figures do not establish a free full-site crawl allowance.",
                "Semrush free account", sem)),
            ("Which of these plans includes daily keyword tracking with Site Audit?", answer_source(
                "The Semrush SEO plan lists both. Choose based on whether you will use the tracking as well as the audit.", "SEO plan features", sem)),
        ],
    )


def sitebulb_jetoctopus() -> Path:
    sb = "https://sitebulb.com/"
    sp = "https://sitebulb.com/pricing/"
    jo = "https://jetoctopus.com/"
    jp = "https://jetoctopus.com/pricing"
    lite, pro, cloud = prices("rq-sitebulb")
    lite_urls, pro_urls = 10_000, 500_000
    plans = (("Growth", 500_000, 2_000_000), ("Pro", 2_000_000, 8_000_000), ("Ultra", 5_000_000, 25_000_000))
    rows = ''.join(f'<tr><th scope="row">{name}</th><td>{urls:,}</td><td>{lines:,}</td></tr>' for name, urls, lines in plans)
    body = f"""
<p id="measured-answer">For Sitebulb vs JetOctopus, choose Sitebulb's desktop product if you want a crawl on Windows or Mac, or JetOctopus if you need cloud crawling with log analysis.
{source_link("Sitebulb's pricing page", sp)} lists Lite at {lite} a month for {lite_urls:,} URLs per audit and Pro at {pro} a month for {pro_urls:,} URLs per audit.
For a cloud crawler with logs, {source_link("JetOctopus's product page", jo)} describes that combination.</p>
{note("rq-sitebulb", "rq-jetoctopus", topic="the desktop and cloud choice")}
{_top_cta("vs-sitebulb-jetoctopus", anchor=False)}

<h2>Do you have a crawl question or a log question?</h2>
<p>A crawl shows what your site serves to the crawler running that audit. A server log is a
record of requests your server received. If you need to compare those views, arrange access
to the logs before buying a log tool. Without the records, there is nothing to analyse.</p>
<p>Write a question you can test, such as whether pages found in a crawl also appear in the
server records. That is a clearer starting point than treating a larger URL allowance as a
reason to buy by itself.</p>

<h2>Sitebulb's choices are desktop and cloud</h2>
<p>{source_link("Sitebulb", sb)} offers desktop crawling for Windows or Mac as well as a
cloud product. The {source_link("USD pricing page", sp)} lists these monthly options:</p>
<ul>
<li><strong>Desktop Lite:</strong> {lite} a month, {lite_urls:,} URLs per audit.</li>
<li><strong>Desktop Pro:</strong> {pro} a month, {pro_urls:,} URLs per audit.</li>
<li><strong>Cloud:</strong> from {cloud} a month.</li>
</ul>
<p>Choose the product first, then the allowance. A desktop Pro allowance describes that
product's audit; it is not a statement about the Cloud plan. Estimate the size of your crawl
and leave room for URLs you have not yet counted.</p>
{note("rq-sitebulb", topic="Sitebulb products")}

<h2>JetOctopus pairs a cloud crawl with log analysis</h2>
<p>{source_link("JetOctopus", jo)} describes a cloud crawler with log analysis. That is a
better fit when the request history is part of the task, rather than an extra you might try
later. Its pricing page lists separate monthly allowances for crawled URLs and log lines.</p>
<div class="wrap-tbl"><table class="cmp">
<caption>JetOctopus monthly crawl and log allowances</caption>
<thead><tr><th scope="col">Plan</th><th scope="col">Crawled URLs per month</th><th scope="col">Log lines per month</th></tr></thead>
<tbody>{rows}</tbody></table></div>
<p>For cost, see {source_link("JetOctopus's pricing page", jp)}. We could not resolve which
price figures applied to which billing period from the page read, so no JetOctopus price is
quoted here. Confirm the billing period along with the allowances in your quote.</p>
{note("rq-jetoctopus", topic="JetOctopus allowances")}

<h2>What Check Engine can contribute</h2>
<p>Our app audits a site locally and produces a ranked plan of repairs. It does not analyse
server logs. Use it for findings you can check from a crawl; a question about actual requests
needs the request records and a tool that reads them.</p>
{_measured("<p>The area scores below come from our own crawl. They describe that run's coverage and findings, with no claim about another crawler's results.</p>", view="areas")}

<h2>A short buying brief</h2>
<p>Record the computer or cloud setup you want to use, the approximate crawl size, the
frequency of repeat runs and whether logs are required. Give each vendor the same brief.
Then compare the returned terms. A page limit, a monthly allowance and a starting price answer
different questions and should stay in separate columns.</p>
<p>If logs are central to your work, read <a href="/learn/log-file-analysis/">what log file
analysis measures</a> before deciding what a crawl alone can settle.</p>
"""
    return render(
        cat="vs", slug="sitebulb-vs-jetoctopus",
        title="Sitebulb vs JetOctopus: desktop, cloud and log analysis",
        desc="Choose between Sitebulb's desktop and cloud crawls and JetOctopus's cloud crawler with logs. Dated Sitebulb prices and separate crawl and log limits.",
        h1="Sitebulb vs JetOctopus",
        crumb='<a href="/">Check Engine</a> / <a href="/vs/">Compare</a> / Sitebulb vs JetOctopus',
        body=body, published="2026-11-20", modified="2026-11-20",
        faq=[
            ("Must I use Sitebulb in the cloud?", answer_source(
                "No. Sitebulb offers desktop software for Windows or Mac as well as its cloud product. Decide which setup you want before comparing allowances.", "Sitebulb products", sb)),
            ("Why is no JetOctopus price quoted in this comparison?", answer_source(
                "The billing period attached to the price figures could not be resolved from the page read. See JetOctopus's pricing page and confirm the billing choice before buying.", "JetOctopus pricing", jp)),
            ("Are JetOctopus log lines counted as crawled URLs?", answer_source(
                "Its pricing page lists separate allowances for crawled URLs and log lines per month. Estimate both types of use instead of treating them as a single pool.", "Separate plan limits", jp)),
            ("Can Check Engine answer a log question without server records?",
             "No. Check Engine does not analyse server logs. Its audit reads what the site serves during a crawl, which cannot establish the history of requests your server received."),
        ],
    )


def build_all() -> list[Path]:
    return [contentking_se_ranking(), screaming_frog_semrush(), sitebulb_jetoctopus()]
