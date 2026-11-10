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
Docket from their own computer. There is no scheduled sweep of the web: every request under this
name belongs to one audit that one person started on their own machine. Two other things send
requests from our own servers, each under its own name and described below: the free website
checker, when a visitor asks it to check a site, and an occasional research survey.</p>

<h2>How it identifies itself</h2>

<p>Every page request carries this user agent:</p>

<pre><code>{escape(lim["user_agent"])}</code></pre>

<p>Pages that are also opened in a browser engine (to see what JavaScript builds) carry the same name and the same link back to this page.</p>

<h2>One check borrows crawlers' names, and says so</h2>

<p>Unless the audit runs offline, one check asks your server how it treats the crawlers that
decide whether you are found. It requests your homepage once under each of these user agents:
{F.probe_names_html()}. Each is that crawler's own published string, with this added to the
end so your logs show the request was Docket's:</p>

<pre><code>{escape(F.probes()["tag"])}</code></pre>

<p>The crawler's name stays at the front because that is what a firewall or CDN rule matches.
Without it, the answer would be the one your server gives Docket rather than the one it gives
Googlebot, and the check exists to find servers that turn those crawlers away. These requests go
only to the site being audited. An offline audit (<code>docket audit --offline</code>, or
&ldquo;Keep it private&rdquo; in the app) sends none of them.</p>

<h2>How hard it pushes</h2>

<ul>
<li>At most {lim["concurrency"]} requests at a time, with at least {lim["delay_seconds"]}
seconds between requests to your site from each of them.</li>
<li>If your robots.txt sets a <code>Crawl-delay</code>, Docket waits that long instead, up to
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
read, because they asked for that page by name: once by the crawl, again in a browser engine
when the audit renders pages (which loads what that page itself loads, as any browser would),
and once as each crawler above unless the audit runs offline. Nothing else on your site is
requested: no other page, no sitemap, no <code>llms.txt</code> and no favicon. And the person running
the audit can switch robots.txt off, which exists for auditing their own staging sites. If that
matters to you, refuse the user agent at your server as well; that is the only rule a crawler
cannot choose to ignore.</p>

<h2>The free website checker</h2>

<p>The free <a href="/tools/website-checker/">website checker</a> reads a site from our servers
when a visitor types its address. It sends this user agent:</p>

<pre><code>CheckEngineBot/1.0 (+https://checkengineseo.com/bot/)</code></pre>

<p>One check reads at most 25 pages of one site: it starts at most one request every tenth of a
second, four at a time, and stops after 30 seconds whatever it has reached. It reads your
<code>/robots.txt</code> first and obeys the groups written for <code>CheckEngineBot</code> and for
<code>*</code>; a page they disallow is not requested. A site can be checked at most three times a day
and once a minute, whoever asks. It sends no cookies, and it keeps nothing but a short summary for one
hour. To keep it out entirely:</p>

<pre><code>User-agent: CheckEngineBot
Disallow: /</code></pre>

<h2>The research survey</h2>

<p>Now and then we read the robots.txt files of a published list of popular sites and report
what they say, as counts on <a href="/index/">the Index</a>. That survey does not use the audit
name above. It sends this user agent:</p>

<pre><code>{escape(F.blk("meta", "user_agent"))}</code></pre>

<p>It asks each site for <code>/robots.txt</code> once. It asks for <code>/llms.txt</code> only
when the robots.txt it just read allows it, and if a real file answers there it makes one more
request, for a path that cannot exist, to tell a real file from a page that answers everything.
It works through the list about {F.blk("meta", "workers")} different sites at a time, with one
request in flight per site and a short pause between the requests it makes to the same one. The
latest survey is described in
<a href="/index/ai-crawler-blocking-2026-10/">AI crawler blocking, August to October 2026</a>,
which names no site. To be left out of the next one, add a group for
<code>{escape(F.blk("meta", "user_agent").split("/")[0])}</code> with
<code>Disallow: /</code>, or <a href="/contact/">write to us</a>.</p>

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
        modified="2026-11-10",
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
