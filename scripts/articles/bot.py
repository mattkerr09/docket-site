"""/bot/ — what Docket's crawler is, what it requests, and how to stop it.

Exists because the crawler's user agent pointed at `docket.audit/bot`, and
`.audit` is not a top-level domain: a site owner who saw Docket in their logs
and followed the link found nothing. The user agent now points here (app
commit that changed `fetcher.USER_AGENT`, 2026-09-23).

⚠️ EVERY CLAIM HERE IS THE ENGINE'S BEHAVIOUR, READ FROM ITS SOURCE, and every
figure comes from `data/limits.json`, which `collect_limits.py` reads from
`CrawlConfig` and `Crawler` — nothing is typed. In particular:

  * robots.txt: the crawl follows the rules for Googlebot (the audit
    reproduces what Google can reach) AND, since 2026-09-23, any group that
    names Docket's token. The start URL is fetched regardless — a person typed
    it — and the page says so rather than promising more than the code does.
  * The person running an audit can switch robots.txt off (`--ignore-robots`,
    and the app's setting). The page says so, and says what to do about it.

⚠️ NO NAMED SITES, NO VENDORS.
"""
from __future__ import annotations

import sys
from html import escape
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import facts as F  # noqa: E402
from render import render  # noqa: E402


def bot() -> Path:
    lim = F.limits()
    token = lim["user_agent_token"]
    body = f"""
<p class="lede">If <code>{escape(token)}</code> is in your logs, somebody audited your site with
Docket from their own computer. There is no Docket crawler farm and no scheduled sweep of the web:
every request under this name belongs to one audit that one person started.</p>

<h2>How it identifies itself</h2>

<p>Every page request carries this user agent:</p>

<pre><code>{escape(lim["user_agent"])}</code></pre>

<p>Pages that are also opened in a browser engine — to see what JavaScript builds — carry the
same name and the same link back to this page. Docket never claims to be Googlebot or any other
search engine's crawler.</p>

<h2>How hard it pushes</h2>

<ul>
<li>At most {lim["concurrency"]} requests at a time, with at least {lim["delay_seconds"]}
seconds between requests to your site from each of them.</li>
<li>If your robots.txt sets a <code>Crawl-delay</code>, Docket waits that long instead — up to
{lim["robots_delay_cap_seconds"]} seconds between requests.</li>
<li>If your server answers 429 or 503, it slows down, and honours a <code>Retry-After</code>
header. If refusals keep coming, it stops and says so in the report.</li>
<li>An audit reads {lim["ui_default_pages"]} pages by default, and stops crawling new pages after
{lim["wall_clock_minutes"]} minutes whatever it has reached.</li>
</ul>

<h2>How robots.txt applies to it</h2>

<p>An audit exists to show what search engines can reach, so Docket crawls what your robots.txt
allows <strong>Googlebot</strong> to crawl. It also obeys any group written for it by name. To
ask it to stay out of your site:</p>

<pre><code>User-agent: {escape(token)}
Disallow: /</code></pre>

<p>Two limits, stated plainly rather than discovered. The address the person typed is still
requested once — they asked for that page by name — but nothing beyond it. And the person running
the audit can switch robots.txt off, which exists for auditing their own staging sites. If that
matters to you, refuse the user agent at your server as well; that is the only rule a crawler
cannot choose to ignore.</p>

<h2>If it misbehaved on your site</h2>

<p>Tell us, with the time and the address it requested, and we will find out why.</p>

<p><a class="btn" href="/contact/">How to get in touch</a></p>
"""
    return render(
        cat="bot", slug="",
        title="Docket's crawler: what it requests and how to stop it",
        desc=("What Docket's audit crawler does on your site, how fast it goes, and the "
              "robots.txt rule that asks it to stay out."),
        h1="The Docket crawler",
        crumb='<a href="/">Docket</a> / Crawler',
        body=body,
        published="2026-09-23",
        faq=[
            ("Is Docket a search engine?",
             "No. Nothing it reads is indexed or published. Each request belongs to an audit "
             "somebody ran from their own computer, and the results stay on it."),
            ("How do I stop Docket crawling my site?",
             f"Add a group for {token} with Disallow: / to your robots.txt. The person running "
             "an audit can switch robots.txt off for their own sites, so refusing the user "
             "agent at your server is the rule that always holds."),
            ("Why does Docket follow Googlebot's rules rather than only its own?",
             "Because an audit reports what search engines can reach. A group written for "
             "Docket by name is followed as well."),
        ],
    )
