#!/usr/bin/env python3
"""Site monitoring — the largest feature with no page of its own.

The gap analysis found the Watchlist described only inside the sitewide
`featureList` JSON-LD string and in passing bullets on five pages. It is an
entire section of the README — scheduled re-audits, change detection, score
history, competitor tracking — and a reader searching for "SEO monitoring" had
nowhere on this site to land.

The two refusals are the reason this page is worth writing rather than
listing. Refusing to diff crawls of very different sizes, and excluding areas
only one side was evaluated on, are both cases of the product declining to
produce a number it cannot stand behind — which is the argument the whole site
makes, in a feature where every competitor produces the number anyway.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from render import render  # noqa: E402


def site_monitoring() -> Path:
    body = """
<p class="lede">An audit tells you what is wrong today. Monitoring tells you what changed —
which is the question you actually have, because a site that was fine last month and is not
fine now has a cause, and a site that has been failing the same check since 2023 is not
news.</p>

<p>Docket re-audits on a schedule you set — daily, weekly or monthly — on your own machine,
with no account and nothing uploaded. Every re-audit is compared against the last one, and
the comparison leads with what got worse.</p>

<p><strong>It runs while Docket is open, and stops when you quit.</strong> The scheduler is
a thread inside the app, not a background service and not a server — there is nothing left
running on your Mac after you close it, and nothing running anywhere else at any time. A
site that falls due while Docket is shut is picked up the next time you open it, so you get
the check late rather than not at all. If you need an audit to run at 3am whether or not
anybody is logged in, that is a job for the Linux CLI in cron or CI, and
<a href="/for/developers/">it is built for exactly that</a>.</p>

<h2>Regressions first, not alphabetically</h2>

<p>The ordering is the feature. Most tools hand you the current state and leave you to
notice what moved; you open the report, see forty issues, and cannot tell which three are
new. Docket separates them: appeared, fixed, got worse, got better, and the score move per
area.</p>

<p>A check that has been failing for six months is a decision you have already made, whether
you made it deliberately or not. A check that passed last week and fails today is somebody's
deploy. Only one of those needs you this morning.</p>

<h2>What it will not tell you, on purpose</h2>

<p>Two refusals, both cases of declining to produce a number that would look useful and be
wrong.</p>

<p><strong>It will not diff two audits that crawled very different numbers of pages.</strong>
It says so instead. If last week reached 50 pages and this week reached 500 — because a
sitemap appeared, or a crawl budget changed, or a section stopped being blocked — then
comparing them invents dozens of "new" issues that were there all along and simply had not
been reached. Every one of those alerts would be false, and you would spend the morning
proving it.</p>

<p><strong>Areas where only one side was evaluated are excluded from the competitor
table</strong>, rather than shown as a win or a loss. If Docket could read your local SEO
signals and could not read a rival's, the honest cell is empty. A tool that filled it would
be handing you a lead you do not have.</p>

<h2>Competitors, and the finding worth acting on</h2>

<p>Attach rival sites and they are audited on the same settings, so the comparison is
like-for-like rather than your thorough crawl against their shallow one. The table shows
where you lead and trail area by area.</p>

<p>The most useful row is not the score. It is the list of issues <em>every competitor has
already fixed</em>. That is the clearest evidence you get that something is both achievable
in your market and expected in it — an issue nobody else has is a standard, not an
opinion.</p>

<h2>Where the history lives</h2>

<p>In <code>~/.docket/</code>, as plain JSON: a watchlist plus one compact snapshot per
audit, a few kilobytes each. You can read it, back it up, put it in version control, or
delete it. Set <code>DOCKET_HOME</code> to keep it somewhere else.</p>

<p>There is no server in this. Nothing is uploaded, there is no account, and if you stop
using Docket your history is still sitting in a folder you own — which is the difference
between monitoring you rent and monitoring you have.</p>

<h2>Scheduled audits are a promise to somebody else's server</h2>

<p>A monitor is a program that visits a site repeatedly without a person present, so the
politeness settings matter more than they do for a one-off audit. Docket crawls with the
same concurrency and delay you set for a manual run, deduplicates URLs, and respects the
page cap. If you are monitoring a site you do not own — a competitor — those settings are
the difference between research and a nuisance.</p>

<p><a class="btn" href="/download/">Download Docket</a></p>
"""
    return render(
        cat="learn", slug="site-monitoring",
        title="SEO monitoring: what changed, not what is wrong",
        desc=("Scheduled re-audits on your own machine, regressions first, and "
              "the two comparisons Docket refuses to make because the number "
              "would look useful and be wrong."),
        h1="Site monitoring",
        crumb='<a href="/">Docket</a> / <a href="/learn/">Learn</a> / Site monitoring',
        body=body,
        faq=[
            ("How often does Docket re-audit a monitored site?",
             "Daily, weekly or monthly — you choose per site. The re-audit runs on your "
             "own machine with the same crawl settings as a manual run, so a monitored "
             "site is not crawled harder than one you audit by hand."),
            ("Does monitoring keep running when Docket is closed?",
             "No. The scheduler is a thread inside the app, so it stops when you quit "
             "and nothing is left running on your machine. A site that falls due while "
             "Docket is shut is re-audited the next time you open it. For unattended "
             "runs on a schedule, use the Linux CLI in cron or CI."),
            ("Does site monitoring need an account or a server?",
             "No. Everything runs locally and history is stored in ~/.docket/ as plain "
             "JSON — a watchlist plus one small snapshot per audit. Nothing is "
             "uploaded, and the history stays yours if you stop using Docket."),
            ("Why does Docket refuse to compare some audits?",
             "Because comparing a 50-page crawl with a 500-page crawl invents dozens of "
             "new issues that were always there and simply had not been reached. Every "
             "one of those alerts would be false, so Docket says the crawls are not "
             "comparable instead of producing the diff."),
            ("What does the competitor comparison actually show?",
             "Where you lead and trail area by area, on rivals audited with the same "
             "settings, plus the issues every competitor has already fixed. Areas where "
             "only one side could be evaluated are left out rather than counted as a "
             "win or a loss."),
        ],
    )


BUILDERS = [site_monitoring]


def build_all() -> list[Path]:
    return [b() for b in BUILDERS]


if __name__ == "__main__":
    for p in build_all():
        print(p)
