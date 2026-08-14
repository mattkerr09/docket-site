#!/usr/bin/env python3
"""`docket diff` — mentioned on two pages, explained on none.

Every number and every quoted line here was produced by running the shipped
1.1.16 binary against two local fixture origins on 2026-08-14: a baseline, and a
candidate with every `<title>` stripped — the classic template regression.

The measurement produced a better argument than the one planned. Removing every
title tag introduced one HIGH regression and **three "improvements"**, because
the checks for short titles, missing geo and message mismatch cannot fire on a
page with no title at all. And the score did not move: 55.0 to 55.0. A gate
watching the score would have passed that deploy.

Exit codes were measured, not read from the source: 2 with a HIGH regression, 0
on identical sites, 0 with `--fail-on never`, and 1 when the crawls are not
comparable.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from render import render  # noqa: E402


def deploy_gate() -> Path:
    body = """
<p class="lede">A deploy that quietly removes your title tags does not break the build, does
not throw an error, and does not show up in any dashboard until rankings move weeks later.
<code>docket diff</code> audits two URLs — usually production and staging — and exits
non-zero when the second one introduced something the first did not have.</p>

<pre><code>docket diff https://example.com https://staging.example.com --fail-on high</code></pre>

<h2>What it actually reports</h2>

<p>We ran it against a staged regression: a copy of a four-page site with every
<code>&lt;title&gt;</code> stripped, which is what a template edit does when somebody moves
the head block. The output, verbatim:</p>

<pre><code>1 regression(s) — introduced by the candidate:
  HIGH     onpage.title_missing             new       4 pages have no title tag

3 improvement(s):
  MEDIUM   onpage.title_short               fixed     4 titles are very short
  MEDIUM   local.no_geo_in_titles           fixed     No page title mentions a location
  LOW      cvr.message_mismatch             fixed     3 pages promise one thing in search…</code></pre>

<p>Read that again, because it is the whole argument for gating on a diff rather than a
score. <strong>Deleting every title tag registered as three improvements.</strong> The
checks for short titles, for titles missing a location, and for titles that do not match
the page all stopped firing — correctly, since there is no title to be short or wrong.</p>

<p>And the score did not move. <strong>55.0 before, 55.0 after.</strong> A gate watching the
number would have let that deploy through, and a report showing three fixes and one issue
would have looked like a decent week.</p>

<h2>The exit codes</h2>

<p>Measured, not quoted from a manual:</p>

<ul>
<li><strong>2</strong> — a regression at <code>--fail-on</code> or worse. Fails the build.</li>
<li><strong>0</strong> — nothing introduced.</li>
<li><strong>0</strong> — with <code>--fail-on never</code>, which reports without failing.
Useful for a first week of watching before you let it block anything.</li>
<li><strong>1</strong> — the audits are not comparable, and Docket refuses to judge.</li>
</ul>

<h2>That last one is the important one</h2>

<p>Point it at a four-page baseline and a one-page candidate and it says:</p>

<blockquote><p>These audits crawled very different numbers of pages (4 then 1), so per-issue
comparison would be misleading. Re-run with the same page limit for a like-for-like
changelog.</p></blockquote>

<p>It exits <strong>1</strong>, not 0. Refusing to judge is not a pass.</p>

<p>This matters more in CI than anywhere else. If staging is behind basic auth for half the
crawl, or a sitemap has not generated yet, the candidate crawl is smaller — and a naive
comparison reports every page the crawler never reached as a brand-new issue. You would get
a wall of red on a deploy that changed nothing, chase it for an hour, and then start
ignoring the gate. The failure that teaches people to ignore a gate is worse than the gate
not existing.</p>

<p>The other half of the same decision: both sides are crawled with identical settings.
There is no per-side page limit, because two crawls configured differently are not a
comparison.</p>

<h2>Why the default bar is lower than for a plain audit</h2>

<p><code>docket audit</code> defaults to failing on critical. <code>docket diff</code>
defaults to failing on <strong>high</strong>, and the reason is that a regression is
somebody's deploy. An issue your site has had for two years is a backlog item; the same
issue arriving this afternoon is a change that just happened and can be reverted while the
person who made it still remembers what they did.</p>

<h2>In a pipeline</h2>

<pre><code>- name: SEO regression gate
  run: |
    docket diff "$PROD_URL" "$STAGING_URL" --fail-on high -n 200</code></pre>

<p>Docket's Linux CLI is a single binary with no runtime to install.
<a href="/for/developers/">The rest of the CI story</a> — SARIF for code scanning, JUnit for
test panels, the GitHub Action — is here.</p>

<p><a class="btn" href="/download/">Download Docket</a></p>
"""
    return render(
        cat="how-to", slug="gate-a-deploy-on-seo-regressions",
        title="Gate a deploy on SEO regressions",
        desc=("docket diff audits production against staging and fails the build on "
              "what the deploy introduced — including the regression that registers "
              "as three improvements."),
        h1="How to gate a deploy on SEO regressions",
        crumb='<a href="/">Docket</a> / <a href="/how-to/">Fix it</a> / Deploy gate',
        body=body,
        faq=[
            ("How do I stop a deploy that breaks SEO?",
             "Run docket diff with your production URL and your staging URL in the "
             "pipeline. It audits both with identical settings and exits 2 when the "
             "candidate introduced a regression at the severity you set, so the build "
             "fails before the change reaches production."),
            ("Why not just fail the build on the audit score?",
             "Because a score can hide a regression. Stripping every title tag from a "
             "test site left the score unchanged at 55.0 and registered three "
             "improvements, since the checks for short, mismatched and location-free "
             "titles all stopped firing. The diff still reported the HIGH regression."),
            ("What happens if staging is partly unreachable?",
             "Docket refuses to compare crawls that reached very different numbers of "
             "pages, and exits 1 rather than 0. Refusing to judge is not a pass. "
             "Without that, every page the crawler could not reach would be reported as "
             "a brand-new issue and the gate would be ignored within a week."),
            ("Why does docket diff fail on high when docket audit fails on critical?",
             "Because a regression is a change somebody just made. An issue a site has "
             "had for two years is a backlog item; the same issue arriving this "
             "afternoon can be reverted while the person who made it still remembers "
             "what they did."),
        ],
    )


BUILDERS = [deploy_gate]


def build_all() -> list[Path]:
    return [b() for b in BUILDERS]


if __name__ == "__main__":
    for p in build_all():
        print(p)
