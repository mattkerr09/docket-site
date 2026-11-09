#!/usr/bin/env python3
"""Plain questions about AI crawlers, answered in the first two sentences.

Matthew, 2026-09-28: "look at the top performing pages for outlier and see what
we can use to help the other pages and other sites and then do that". Outlier's
best page by far answers a plain question about a giant brand in its first
sentence (search/WHAT-WORKS-2026-09-28.md, "pattern A"). These are Docket's.

⚠️ ONLY WHERE DEMAND IS MEASURED. Candidates were read on Bing (90 days,
exact) and Search Console (90 days) on 2026-09-28 before writing. The full
questions ("is ChatGPT crawling my website", "can I block Copilot") read 0 on
both. Two short names did not:

    llms.txt    658 Bing impressions
    claudebot   403
    gptbot       28   (not written: /learn/does-cloudflare-block-gptbot/ and
                       /learn/ai-crawler-directives/ already carry GPTBot)

The target queries and their baselines are recorded in
~/ops/search/docket-pattern-a-2026-09-28.json for the 28-day read.

Each page: the title is the question; the answer is in the first two
sentences; one measured fact from the Docket Index, read through facts.py;
then the free checker, then the product box.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import facts as F  # noqa: E402
from render import buy_block, render  # noqa: E402

SURVEYED_HUMAN = "August 2026"
ANTHROPIC_BOTS = ("https://support.claude.com/en/articles/8896518-does-anthropic-crawl-data-"
                  "from-the-web-and-how-can-site-owners-block-the-crawler")
ANTHROPIC_IPS = "https://claude.com/crawling/bots.json"
GOOGLE_AI_FEATURES = "https://developers.google.com/search/docs/appearance/ai-features"
LLMSTXT = "https://llmstxt.org/"
ANTHROPIC_SUBPROCESSORS = "https://trust.anthropic.com/subprocessors"
PARALLEL_BOTS = "https://parallel.ai/parallel-web-systems-bots"
BRAVE_CRAWLER = "https://search.brave.com/help/brave-search-crawler"


def _checker(lead: str) -> str:
    return f"""
<h2>Check your own site</h2>
<p>{lead} The free <a href="/tools/ai-crawler-checker/">AI crawler checker</a> reads your
robots.txt the way the crawlers do and shows, crawler by crawler, which ones may fetch your pages
and which rule decided it.</p>
<p><a class="btn" href="/tools/ai-crawler-checker/">Check my site&rsquo;s AI crawlers</a></p>
"""


def _own_robots_example() -> str:
    """What this site's own robots.txt says to Anthropic's three crawlers, read from the file.

    Read from site/robots.txt (written by build.py, committed) rather than typed, so it cannot
    disagree with the file. Emits nothing unless the file still has the shape the sentence
    describes: ClaudeBot and Claude-SearchBot named with only Allow: /, Claude-User not named,
    and a * group that also allows everything.
    """
    path = Path(__file__).resolve().parent.parent.parent / "site" / "robots.txt"
    if not path.exists():
        return ""
    groups: dict[str, list] = {}
    current: list[str] = []
    after_rule = False
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line or ":" not in line:
            continue
        key, _, value = (part.strip() for part in line.partition(":"))
        key = key.lower()
        if key == "user-agent":
            if after_rule:
                current, after_rule = [], False
            current.append(value.lower())
        elif key in ("allow", "disallow"):
            after_rule = True
            for agent in current:
                groups.setdefault(agent, []).append((key, value))
    open_all = [("allow", "/")]
    if (groups.get("claudebot") != open_all or groups.get("claude-searchbot") != open_all
            or "claude-user" in groups or groups.get("*") != open_all):
        return ""
    return """
<h2>What this site&rsquo;s own robots.txt says</h2>
<p>Docket&rsquo;s own file, read when this page was built, names <code>ClaudeBot</code> and
<code>Claude-SearchBot</code> separately and gives each <code>Allow: /</code>. It does not name
<code>Claude-User</code>, so the <code>User-agent: *</code> group applies to it, and that group allows
everything too. All three Anthropic crawlers may fetch this site, and the file keeps the search
crawlers and the training crawlers in separate groups so the next person to edit it can see the difference.</p>
"""


def what_is_claudebot() -> Path:
    blocked = F.claude_search_blocked()
    both = F.claude_search_and_claudebot()
    only = F.claude_search_only()
    surveyed = F._d()["attempted"]

    body = f"""
<p class="lede"><strong>ClaudeBot is Anthropic&rsquo;s web crawler, and it collects pages to
train Claude models.</strong> Blocking it keeps your future pages out of Anthropic&rsquo;s training
data; it does not remove you from Claude&rsquo;s answers, which are fetched by two other
crawlers, Claude-SearchBot and Claude-User.</p>

<h2>Anthropic runs three crawlers, not one</h2>
<p>Anthropic&rsquo;s <a href="{ANTHROPIC_BOTS}" rel="nofollow noopener">own help article</a>
(dated 2026-04-07 on the article, re-read 2026-10-19) names three, and each one answers a different question
about your site:</p>
<div class="wrap-tbl"><table class="cmp">
<thead><tr><th>Crawler</th><th>What Anthropic says it does</th><th>What blocking it does</th></tr></thead>
<tbody>
<tr><td><code>ClaudeBot</code></td><td>&ldquo;helps enhance the utility and safety of our generative
AI models by collecting web content&rdquo;</td><td>Your future pages are excluded from training
data.</td></tr>
<tr><td><code>Claude-SearchBot</code></td><td>&ldquo;navigates the web to improve search result
quality for users&rdquo;</td><td>Your pages are not indexed for Claude&rsquo;s search.</td></tr>
<tr><td><code>Claude-User</code></td><td>fetches a page &ldquo;when individuals ask questions to
Claude&rdquo;</td><td>Claude cannot open your page when someone asks it about you.</td></tr>
</tbody></table></div>
<p>So the question to ask is not &ldquo;should I block Claude?&rdquo; but which of three things
you want to stop. Refusing training while staying findable is a coherent position: block
<code>ClaudeBot</code>, leave the other two open.</p>

<h2>How to block ClaudeBot, and only ClaudeBot</h2>
<p>Two lines in the robots.txt at the root of your site:</p>
<pre><code>User-agent: ClaudeBot
Disallow: /</code></pre>
<p>Anthropic says its crawlers honour robots.txt, and that they also support
<code>Crawl-delay</code>, the non-standard line that asks a crawler to slow down rather than stay
away. If the load is the problem rather than the use, a delay is the gentler answer.</p>
<p>A group that names <code>ClaudeBot</code> replaces your <code>User-agent: *</code> rules for it
completely, so anything you disallow for everyone has to be repeated inside the named group if it
should still apply. And a rule written with a stray character (a version number, a
non-breaking hyphen pasted from a document) can address a name no crawler has; the
<a href="/index/ai-directives/">Docket Index</a> found such rules on real sites.</p>

<h2>What most sites that block Anthropic actually do</h2>
<p>In Docket&rsquo;s {SURVEYED_HUMAN} survey of the Tranco top {surveyed:,}, <strong>{blocked}
sites block Claude-SearchBot, and {both} of them block ClaudeBot as well</strong>, leaving
{only} that give up Claude&rsquo;s search while still allowing training. The pattern is the same
at OpenAI: sites that close the search crawler almost always close the training crawler too,
which suggests most of those search blocks were a side effect of blocking &ldquo;AI&rdquo; as one
thing rather than a decision to disappear from answers.</p>

<h2>Is a request really from ClaudeBot?</h2>
<p>Anyone can put &ldquo;ClaudeBot&rdquo; in a user-agent string. Anthropic publishes the addresses
its crawlers use at <a href="{ANTHROPIC_IPS}" rel="nofollow noopener">claude.com/crawling/bots.json</a>,
so a request can be checked against that list before you block or allow it at your server.</p>

{_own_robots_example()}
<h2>robots.txt is a request, not a lock</h2>
<p>Everything above is about what your file asks. Your CDN or firewall can refuse a crawler
the file welcomes, and a bot-protection setting switched on by someone else is the usual reason a
site that meant to stay open is not. That is also why the checker below reads the file and says
plainly what it cannot see.</p>
{_checker("Most sites have never looked at what their file says to Anthropic&rsquo;s three crawlers.")}
{buy_block("learn-what-is-claudebot", try_app="learn-what-is-claudebot-try-free")}

<h2>Related</h2>
<ul>
<li><a href="/learn/ai-crawler-directives/">Every AI crawler: which to block and which to keep</a></li>
<li><a href="/learn/does-noindex-stop-ai-crawlers/">Does noindex stop AI crawlers?</a></li>
<li><a href="/how-to/fix-ai-crawlers-blocked-by-your-cdn/">When your CDN blocks crawlers your robots.txt allows</a></li>
</ul>
"""
    return render(
        cat="learn", slug="what-is-claudebot",
        modified="2026-10-19",
        title="What is ClaudeBot? What blocking it does, and doesn't",
        desc=("ClaudeBot is Anthropic's training crawler. Blocking it keeps your pages out of "
              "training, not out of Claude's answers. The three Anthropic bots, and how to block one."),
        h1="What is ClaudeBot?",
        crumb='<a href="/">Docket</a> / <a href="/learn/">Learn</a> / What is ClaudeBot?',
        body=body,
        published="2026-09-28",
        faq=[
            ("Does blocking ClaudeBot remove my site from Claude?",
             "No. ClaudeBot collects training data. Claude's answers come from Claude-SearchBot, "
             "which indexes pages for search, and Claude-User, which fetches a page when someone "
             "asks Claude about it. Block ClaudeBot alone and you stay findable."),
            ("Does ClaudeBot obey robots.txt?",
             "Anthropic says its crawlers honour robots.txt and also support the non-standard "
             "Crawl-delay line. robots.txt is still a request: a server or CDN rule is the only "
             "thing that enforces a block."),
            ("How can I tell a real ClaudeBot request from a fake one?",
             "Check the requesting address against the list Anthropic publishes at "
             "claude.com/crawling/bots.json. The user-agent string alone proves nothing."),
        ],
    )


def what_is_llms_txt() -> Path:
    s = F._d()
    n = F.directives_hosts()
    adoption = s["pct_llms_adoption"]
    confirmed = s["llms_confirmed"]
    candidates = s["llms_candidates"]
    false_pos = s["llms_false_positive"]
    false_pct = s["pct_llms_false_positive"]
    edge_pct = s["pct_llms_edge_denied"]

    body = f"""
<p class="lede"><strong>llms.txt is a Markdown file at the root of a website that lists the pages
a language model should read, with a one-line note on each.</strong> It is a proposal, not a
standard, and Google says you do not need it: its documentation on AI Overviews states that you
don&rsquo;t need &ldquo;AI text files&rdquo; to appear there.</p>

<h2>Where it came from and what goes in it</h2>
<p>Jeremy Howard proposed it on 2024-09-03 at <a href="{LLMSTXT}" rel="nofollow noopener">llmstxt.org</a>
(read 2026-09-28). The format is deliberately small:</p>
<ul>
<li>an H1 with the site or project name, which is the only required part;</li>
<li>a blockquote with a short summary;</li>
<li>optional paragraphs of detail;</li>
<li>H2 sections, each a list of links written as <code>- [Title](url): note</code>;</li>
<li>by convention, a section called <em>Optional</em> for things a model can skip when it is short
of room.</li>
</ul>
<p>The point is a short, curated map, not a copy of the site. A model given a long page of
navigation, cookie banners and scripts has to work out what matters; a model given this file is
told. Ours is at <a href="/llms.txt">docketseo.app/llms.txt</a>, and it is generated from the
same data as the pages it lists, so it cannot quote an old price.</p>

<h2>Does it do anything?</h2>
<p>For search, nothing anyone has shown. Google&rsquo;s page on
<a href="{GOOGLE_AI_FEATURES}" rel="nofollow noopener">AI features and your website</a> (updated
2025-12-10) says there are &ldquo;no additional requirements to appear in AI Overviews or AI
Mode&rdquo; and that you &ldquo;don&rsquo;t need to create new machine readable files, AI text
files, or markup&rdquo;. Ranking and citation still come from the crawlers reading your actual
pages.</p>
<p>Where it can help is the narrower case it was designed for: a tool or an assistant that has
already decided to read your site, often a developer pointing an agent at documentation. The AI
labs publish llms.txt files for their own developer docs for exactly that reason. It is cheap to
make, harmless to have, and worth keeping honest: a genuine index of your best pages, not a
list of keywords.</p>

<h2>How many sites actually have one</h2>
<p>More than you would guess. In Docket&rsquo;s {SURVEYED_HUMAN} survey of {n:,} sites with a
readable robots.txt in the Tranco top {s['attempted']:,}, <strong>{adoption}% had a real llms.txt</strong>
({confirmed} files), and the share is highest among the largest sites. Getting that number right
took care: our first pass found {candidates} apparent &ldquo;files&rdquo;, and {false_pos} of
them ({false_pct}%) were not one. Soft 404 pages, sitemaps, robots.txt served at the wrong path.
Any tool that flags a &ldquo;missing&rdquo; or &ldquo;present&rdquo; llms.txt without reading the
body, or without asking for a path that cannot exist, is wrong at least one time in six. The
<a href="/index/ai-directives/">full breakdown is in the Docket Index</a>.</p>
<p>We read the same list again on {F.lt_date('oct')}, and
<strong>{F.lt_pct(F.lt('oct', 'confirmed'), F.lt('oct', 'readable'))}%</strong> had a real
llms.txt ({F.lt('oct', 'confirmed')} files). <a href="/index/llms-txt-adoption-2026-10/">The
change since August is on its own page</a>.</p>

<h2>The file is useless if the crawler cannot fetch it</h2>
<p>The same survey found that among sites whose robots.txt allowed a fetch of
<code>/llms.txt</code>, <strong>{edge_pct}% refused it at the server</strong>: the file said yes
and the firewall said no. Before writing an llms.txt, make sure the crawlers you are writing it for
can reach your pages at all.</p>
{_checker("An llms.txt only matters to a crawler that is allowed in.")}
{buy_block("learn-what-is-llms-txt", try_app="learn-what-is-llms-txt-try-free")}

<h2>Related</h2>
<ul>
<li><a href="/learn/ai-search-visibility/">AI search visibility: what actually decides whether you are cited</a></li>
<li><a href="/learn/ai-crawlers-and-sitemaps/">AI crawlers and sitemaps</a></li>
<li><a href="/learn/ai-crawler-directives/">Every AI crawler: which to block and which to keep</a></li>
</ul>
"""
    return render(
        cat="learn", slug="what-is-llms-txt",
        modified="2026-10-19",
        title="What is llms.txt, and does it do anything?",
        desc=("llms.txt is a Markdown map of your site for language models. Google says you don't "
              "need it for AI Overviews. What goes in it, who has one, and when it helps."),
        h1="What is llms.txt?",
        crumb='<a href="/">Docket</a> / <a href="/learn/">Learn</a> / What is llms.txt?',
        body=body,
        published="2026-09-28",
        faq=[
            ("Does llms.txt help me rank in Google or appear in AI Overviews?",
             "Google's documentation says there are no special requirements to appear in AI "
             "Overviews or AI Mode, and that you don't need AI text files to be included. "
             "Crawler access to your real pages is what counts."),
            ("Is llms.txt the same as robots.txt?",
             "No. robots.txt tells crawlers what they may fetch. llms.txt is a suggested reading "
             "list for a model that is already reading your site. It grants and blocks nothing."),
            ("Should I add one anyway?",
             "It is cheap and harmless if it is a genuine index of your best pages, generated from "
             "the same source as those pages so it cannot go stale. Check first that AI crawlers "
             "can reach your site; a file nobody can fetch does nothing."),
        ],
    )


def what_is_a_sitemap() -> Path:
    s = F.sitemap_own_sites()
    docs = s["docs"]
    sources = docs["sources"]
    own_sites = format(s["own_sites"], ",")
    own_urls = format(s["own_urls"], ",")
    own_ok = format(s["own_ok"], ",")
    own_answered = (f"all {own_urls} of them answered 200" if s["own_ok"] == s["own_urls"]
                    else f"{own_ok} of them answered 200")
    own_lastmod = format(s["own_lastmod"], ",")
    own_priority = format(s["own_priority"], ",")
    own_changefreq = format(s["own_changefreq"], ",")
    own_robots_line = format(s["own_robots_line"], ",")
    one_site_urls = format(s["one_site_urls"], ",")
    one_site_date = s["one_site_date"]
    low_imp = format(s["low_imp"], ",")
    low_imp_pages = format(s["low_imp_pages"], ",")
    gsc_indexed = format(s["gsc_indexed"], ",")
    gsc_inspected = format(s["gsc_inspected"], ",")
    max_urls = format(docs["max_urls"], ",")
    max_mb = format(docs["max_mb"], ",")
    small_site_pages = format(docs["small_site_pages"], ",")
    images_per_page = format(docs["images_per_page"], ",")
    news_days = {2: "two"}[docs["news_days"]]
    own_read_human = F.lt_fmt(s["read"])
    facts_read_human = F.lt_fmt(s["docs_read"])
    gsc_read_human = F.lt_fmt(s["gsc_read"])
    gsc_window_end_human = F.lt_fmt(s["gsc_window_end"])
    index_month = F.index_month()
    index_reached = format(F.index_reached(), ",")
    index_sitemap_line = format(F.index_sitemap_line(), ",")

    body = f"""
<p class="lede"><strong>A sitemap is a file, usually sitemap.xml at the root of your site, that lists the URLs you want
search engines to find, with an optional date each one last changed.</strong> It helps a crawler discover pages. It does
not get a page indexed or ranked: Google calls submitting one "merely a hint". On {own_sites} sites I run, {own_urls} URLs
were listed, and {own_answered} on {own_read_human}. What decided which ones Google showed was everything
else.</p>

<h2>What goes in one</h2>

<p>The format is a short XML list. Each page gets a <code>&lt;url&gt;</code> entry with its address in <code>&lt;loc&gt;</code>, and optionally the date it last
changed in <code>&lt;lastmod&gt;</code>:</p>

<pre><code>&lt;urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"&gt;
  &lt;url&gt;
    &lt;loc&gt;https://example.com/pricing/&lt;/loc&gt;
    &lt;lastmod&gt;2026-11-09&lt;/lastmod&gt;
  &lt;/url&gt;
&lt;/urlset&gt;</code></pre>

<p>One file can hold up to {max_urls} URLs and {max_mb} MB uncompressed. Past that, you split the list into several files and
list those in a sitemap index file. Google's limits are on its <a href="{sources['build_sitemap']}" rel="nofollow noopener">"Build and submit a sitemap"</a> page (read {facts_read_human}),
and the protocol itself is published at <a href="{sources['protocol']}" rel="nofollow noopener">sitemaps.org</a>.</p>

<p>List only the version of each page you want in search: the canonical address, with no redirects, no pages that return an
error, and no pages marked noindex. <a href="{sources['bing_guidelines']}" rel="nofollow noopener">Bing's webmaster guidelines</a> say the same, and say to take deleted and redirected URLs out.</p>

<h2>What Google and Bing do with each tag</h2>

<div class="wrap-tbl"><table class="cmp">
<thead><tr><th>Tag</th><th>Google</th><th>Bing</th></tr></thead>
<tbody>
<tr><td>&lt;loc&gt;</td><td>Required. The page address.</td><td>Required. The page address.</td></tr>
<tr><td>&lt;lastmod&gt;</td><td>Used only when it is consistently and verifiably accurate</td><td>Asked for, as a freshness signal. If every date is today's, Bing says it may not trust them.</td></tr>
<tr><td>&lt;changefreq&gt;</td><td>Ignored</td><td>Ignored</td></tr>
<tr><td>&lt;priority&gt;</td><td>Ignored</td><td>Ignored</td></tr>
</tbody></table></div>

<p>Read on <a href="{sources['build_sitemap']}" rel="nofollow noopener">each company's own documentation</a> and <a href="{sources['bing_lastmod_blog']}" rel="nofollow noopener">the Bing Webmaster blog</a>, {facts_read_human}.</p>

<p>So the only tag beyond the address that can do anything is lastmod, and only if it is true. A lastmod should change when the
main content, structured data or links on the page change. A new copyright year in the footer doesn't count.</p>

<h2>Do you need one?</h2>

<p><a href="{sources['overview']}" rel="nofollow noopener">Google says you might not</a>, if your site is small (about {small_site_pages} pages or fewer that you want in search) and every page is linked
from somewhere else on the site. You probably do if the site is large, new with few links from other sites, or full of
video, images or news.</p>

<p>Since a sitemap is cheap to make and every common platform can generate one, my advice is to have one anyway, and keep it
honest. A wrong sitemap is worse than none: it points crawlers at pages you don't want and trains them to distrust your dates.</p>

<h2>How to tell search engines where it is</h2>

<ul>
<li><strong>robots.txt:</strong> add a line such as Sitemap: https://example.com/sitemap.xml. Google and Bing both read it, and it can go
  anywhere in the file.</li>
<li><strong>Google Search Console:</strong> the Sitemaps report, which also shows when Google last read the file.</li>
<li><strong>Bing Webmaster Tools:</strong> Submit sitemaps. Bing can also import the sitemaps you submitted to Google.</li>
<li><strong>IndexNow, for changes:</strong> a ping that a URL was added, changed or deleted. Bing says it reads sitemaps about once a day
  and recommends IndexNow on top, and <a href="{sources['indexnow_faq']}" rel="nofollow noopener">the IndexNow site</a> says to use both. Amazon, Bing, Naver, Seznam, Yandex and Yep take part.</li>
</ul>

<p>In Docket's {index_month} study of {index_reached} large, well-known sites (a hand-picked list, not a random sample),
{index_sitemap_line} had a Sitemap line in robots.txt.</p>

<h2>What four real sitemaps showed</h2>

<p>I read the sitemaps of {own_sites} sites I run on {own_read_human}, then requested every URL in them.</p>

<div class="wrap-tbl"><table class="cmp">
<thead><tr><th></th><th>Total</th></tr></thead>
<tbody>
<tr><td>URLs listed</td><td>{own_urls}</td></tr>
<tr><td>Answered 200 (no redirect, no error)</td><td>{own_ok}</td></tr>
<tr><td>Had a lastmod date</td><td>{own_lastmod}</td></tr>
<tr><td>Carried a priority tag</td><td>{own_priority}</td></tr>
<tr><td>Carried a changefreq tag</td><td>{own_changefreq}</td></tr>
<tr><td>Sites with a Sitemap line in robots.txt</td><td>{own_robots_line} of {own_sites}</td></tr>
</tbody></table></div>

<p>Three things stood out.</p>

<p><strong>Most of the tags do nothing.</strong> {own_priority} priority tags and {own_changefreq} changefreq tags, and Google and Bing
ignore every one. They are harmless, but they are noise. Our own generators added them by default.</p>

<p><strong>One site dated every page today.</strong> All {one_site_urls} URLs on one of the sites carried the same lastmod, {one_site_date},
because a sitewide wording change that day touched every page. The dates were true, but a list where every page changed on
the same day looks exactly like a generator stamping today's date on everything, which is the pattern Bing says makes it
distrust lastmod. If a change to the page's furniture touches every page, it is better not to move the date of pages whose
main content didn't change.</p>

<p><strong>Listed is not indexed, and indexed is not shown.</strong> Of the URLs on two of these sitemaps, Google reported
{gsc_indexed} of {gsc_inspected} as "Submitted and indexed" when I asked its URL Inspection API on {gsc_read_human}. Being
in the index did not mean being seen: {low_imp} of the {low_imp_pages} pages on those two sites had fewer than 10 Google
impressions in the 28 days to {gsc_window_end_human}, because few people search for what they cover or a stronger page outranks them. The sitemap did its one job, which is getting pages found.</p>

<h2>What Docket checks in a sitemap</h2>

<p>Docket reads your robots.txt for declared sitemaps, falls back to /sitemap.xml, and then checks the list against the pages
it crawled. The findings it can report:</p>

<ul>
<li>No XML sitemap found, or a declared sitemap that is unreachable.</li>
<li>Sitemap URLs that are broken, or that redirect instead of serving a page.</li>
<li>Sitemap URLs with the site's address written twice, a generator bug that produces addresses nobody can reach.</li>
<li>Noindex pages listed in the sitemap, which asks a search engine to index a page you told it not to.</li>
<li>Indexable pages missing from the sitemap.</li>
<li>Sitemap URLs it could not check, reported as a limit of the check rather than a fault, because a server that refuses a
  crawler may still serve Google.</li>
</ul>

<p>It does not grade your lastmod dates or flag a missing robots.txt Sitemap line. Those you can read by eye in a minute.</p>

<h2>Other kinds of sitemap</h2>

<ul>
<li><strong>Image sitemaps</strong> list images Google might not find on its own, up to {images_per_page} per page.</li>
<li><strong>Video sitemaps</strong> add details about videos hosted on your pages.</li>
<li><strong>News sitemaps</strong> are for Google News publishers, and list only articles from the last {news_days} days.</li>
<li><strong>hreflang in a sitemap:</strong> for sites in several languages, each URL lists every language version, itself included.</li>
<li><strong>An HTML sitemap</strong> is a page of links for people. It is a different thing, and search engines treat it as an ordinary page.</li>
</ul>
{buy_block("learn-what-is-a-sitemap", try_app="learn-what-is-a-sitemap-try-free")}

<h2>Related</h2>
<ul>
<li><a href="/learn/ai-crawlers-and-sitemaps/">AI crawlers and sitemaps</a></li>
<li><a href="/how-to/sitemap-urls-that-are-not-stale/">Sitemap URLs flagged as broken? Check before you regenerate</a></li>
<li><a href="/learn/index-coverage/">Index coverage</a></li>
<li><a href="/learn/canonical-tags/">Canonical tags are a hint, not an instruction</a></li>
</ul>
"""
    return render(
        cat="learn", slug="what-is-a-sitemap",
        modified="2026-11-09",
        title="What is a sitemap? What it does, and what it doesn't",
        desc=("A sitemap lists the URLs you want search engines to find. What goes in one, "
              "what Google and Bing ignore, and what four real sitemaps showed."),
        h1="What is a sitemap?",
        crumb='<a href="/">Docket</a> / <a href="/learn/">Learn</a> / What is a sitemap?',
        body=body,
        published="2026-11-09",
        faq=[
            ("Does a sitemap help SEO?",
             "It helps search engines find your pages, which matters most for new sites and pages with "
             "few links to them. It does not improve rankings, and Google says submitting one is only "
             "a hint, not a guarantee that pages are crawled or indexed."),
            ("Do I need a sitemap for a small website?",
             f"Google says a site of about {small_site_pages} pages or fewer, with every page linked "
             "from somewhere on the site, might not need one. It is still worth having, because it "
             "costs nothing and helps Bing and other engines too."),
            ("How often should I update my sitemap?",
             "Whenever pages are added, removed or change in a meaningful way. Most platforms "
             "regenerate it automatically. Keep lastmod true: change it when the page's main content "
             "changes, not on every rebuild."),
            ("Does Google use priority and changefreq?",
             "No. Google's documentation says it ignores both. Bing ignores them too. Only the URL and "
             "an accurate lastmod are used."),
        ],
    )


def what_is_alt_text() -> Path:
    s = F.alt_text_own_sites()
    sources = s["sources"]
    alt_sites = format(s["alt_sites"], ",")
    alt_pages = format(s["alt_pages"], ",")
    alt_imgs = format(s["alt_imgs"], ",")
    alt_missing = format(s["alt_missing"], ",")
    alt_empty = format(s["alt_empty"], ",")
    alt_over_125 = format(s["alt_over_125"], ",")
    alt_long_site_median = format(s["alt_long_site_median"], ",")
    alt_logo_flagged = format(s["alt_logo_flagged"], ",")
    alt_logo_imgs = format(s["alt_logo_imgs"], ",")
    myth_chars = format(s["myth_chars"], ",")
    google_style_chars = format(s["google_style_chars"], ",")
    missing = "no" if s["alt_missing"] == 0 else alt_missing
    alt_read_human = F.lt_fmt(s["read"])
    facts_read_human = F.lt_fmt(s["facts_read"])

    body = f"""
<p class="lede"><strong>Alt text is the text in an image's alt attribute: the words a screen reader reads out in place of the
picture, and what a browser shows if the image fails to load.</strong> Google also uses it to understand what an image
shows. Write it as the words you would use to replace the image. If the image is pure decoration, leave it empty, as alt="",
which is correct and not an error. Across {alt_pages} pages on {alt_sites} sites I run, {alt_imgs} images had {missing}
missing alt attributes and {alt_empty} empty ones, and every empty one was right.</p>

<h2>What it looks like</h2>

<pre><code>&lt;img src="dalmatian.jpg" alt="Dalmatian puppy playing fetch"&gt;</code></pre>

<p>The test the <a href="{sources['whatwg_images']}" rel="nofollow noopener">HTML standard</a> gives is simple: if every image on the page were replaced by its alt text, the page should mean
the same thing.</p>

<h2>Missing alt and empty alt are different</h2>

<ul>
<li><strong>No alt attribute at all</strong> is the mistake. Some screen readers then read out the file name instead, so a listener hears
  a camera's file name where the picture should be.</li>
<li><strong><a href="{sources['wai_decorative']}" rel="nofollow noopener">An empty alt, alt="",</a></strong> tells assistive technology to skip the image. That is correct for an image that is purely
  decorative, or that only repeats text right next to it.</li>
</ul>

<p>The <a href="{sources['wai_images']}" rel="nofollow noopener">W3C's accessibility guidelines</a> put this first: every image that carries meaning needs a text alternative that does the
same job, and pure decoration should be marked so assistive technology can ignore it.</p>

<h2>How to write good alt text</h2>

<p>The <a href="{sources['wai_images']}" rel="nofollow noopener">W3C's image tutorials</a> sort images into a few kinds, and each gets a different kind of alt:</p>

<div class="wrap-tbl"><table class="cmp">
<thead><tr><th>Kind of image</th><th>What the alt should say</th><th>Example</th></tr></thead>
<tbody>
<tr><td>Informative: a photo or picture that adds meaning</td><td>The essential information, briefly</td><td>alt="Dalmatian puppy playing fetch"</td></tr>
<tr><td>Functional: the only content of a link or button</td><td>What the link or button does, not what it looks like</td><td>alt="Search" on a magnifying-glass button</td></tr>
<tr><td>Image of text</td><td>The same words as the image</td><td>alt="Now open on Sundays"</td></tr>
<tr><td>Decorative: a divider, a background flourish</td><td>Nothing: alt=""</td><td>alt=""</td></tr>
<tr><td>Complex: a chart or a detailed screenshot</td><td>A short alt, with the full detail in nearby text or a caption</td><td>alt="Monthly visits this year" plus the numbers in a table</td></tr>
</tbody></table></div>

<p>Read on the <a href="{sources['wai_decision_tree']}" rel="nofollow noopener">W3C's own pages</a>, {facts_read_human}.</p>

<p>A few habits make most alt text better:</p>

<ul>
<li>Say what the image means here, not every detail in it. The same photo can need different alt on two pages.</li>
<li>Skip "image of" and "picture of". The screen reader already says it is an image.</li>
<li>Don't repeat a caption or a heading that sits right beside it. Use alt="" and let the text do the work.</li>
<li>Don't stuff keywords. Google's own example of bad alt is a list of keywords, and it says this can get a site seen as spam.</li>
</ul>

<h2>The {myth_chars}-character myth</h2>

<p>Many guides say alt text must stay under {myth_chars} characters because screen readers cut it off there. I could not find that rule
in any official source. The W3C's guidance sets no character limit. Neither does the HTML standard, <a href="{sources['mdn_img']}" rel="nofollow noopener">MDN</a> or <a href="{sources['google_images']}" rel="nofollow noopener">Google Search
Central</a>. The only Google page I found that mentions {myth_chars} is a <a href="{sources['google_codelab_125']}" rel="nofollow noopener">design codelab</a> on button labels, and a <a href="{sources['google_style_155']}" rel="nofollow noopener">Google style guide</a> for its
own developer docs says {google_style_chars}.</p>

<p>So length is a judgement, not a limit. Short is usually kinder, because a listener can't skim. On one of the sites I measured,
the median alt was {alt_long_site_median} characters, because each image is a product screenshot that carries a score, a grade
and a count. That is informative, but the W3C's advice for complex images is better: a short alt, and the detail in a caption
or the text around it.</p>

<h2>What four real sites showed</h2>

<p>I read every page in the sitemaps of {alt_sites} sites I run on {alt_read_human} and checked every image.</p>

<div class="wrap-tbl"><table class="cmp">
<thead><tr><th></th><th>Total</th></tr></thead>
<tbody>
<tr><td>Pages</td><td>{alt_pages}</td></tr>
<tr><td>Images</td><td>{alt_imgs}</td></tr>
<tr><td>No alt attribute</td><td>{alt_missing}</td></tr>
<tr><td>Empty alt (alt="")</td><td>{alt_empty}</td></tr>
<tr><td>Alt longer than {myth_chars} characters</td><td>{alt_over_125}</td></tr>
</tbody></table></div>

<p>The most useful finding was about a tool, not a page. Our own internal page audit flagged {alt_logo_flagged} pages on one site for
images with no alt text. Every empty alt on that site, {alt_logo_imgs} in all, was the site's logo inside the home link, right
beside the site's name in text.
There, alt="" is correct: a non-empty alt would make a screen reader say the name twice. The audit had treated an empty alt as
a missing one. A checker that does that trains people to add junk alt text to images that should stay silent.</p>

<h2>What Docket checks</h2>

<p>Docket reports images that have no alt attribute at all, with the pages they are on. It treats alt="" as correct and does not
flag it, and it ignores 1x1 tracking pixels. It also reports links with no text at all, which is often an image link with no
alt, and a logo whose alt text doesn't name your company. A missing alt is an accessibility problem as well as an image-search
one.</p>

<p>It does not judge whether your alt text is good. Only a person who knows why the image is there can do that.</p>

<p>If you run a public body's website, the deadlines for accessible websites under the ADA are on
<a href="/learn/ada-title-ii-website-dates/">our Title II dates page</a>.</p>
{buy_block("learn-what-is-alt-text", try_app="learn-what-is-alt-text-try-free")}
"""
    return render(
        cat="learn", slug="what-is-alt-text",
        modified="2026-11-09",
        title="What is alt text? How to write it and when to leave it empty",
        desc=(f'Alt text is the words that stand in for an image. How to write it, when alt="" '
              f'is right, the {myth_chars}-character myth, and what {alt_pages} real pages showed.'),
        h1="What is alt text?",
        crumb='<a href="/">Docket</a> / <a href="/learn/">Learn</a> / What is alt text?',
        body=body,
        published="2026-11-09",
        faq=[
            ('Does alt text help SEO?',
             'Google uses alt text, together with what it can see in the image, to understand what the image '
             'shows, and uses it as anchor text when the image is a link. Write it for people first. Google '
             'warns that alt filled with keywords can make a site look like spam.'),
            ('How long should alt text be?',
             "No official source sets a limit. The W3C's guidance says to keep it to the essential "
             "information, and to put long detail, such as a chart's numbers, in the text around the image."),
            ('When should alt text be empty?',
             'When the image is purely decorative, or when the same information is already in text right '
             'next to it. Use an empty alt attribute, not a missing one, so screen readers skip it instead of reading '
             'the file name.'),
            ('Is alt text the same as the text you see on hover?',
             'No. Hover text comes from the title attribute. Alt text is read by screen readers and shown '
             "when the image doesn't load."),
        ],
        closer="""
<h2>Related</h2>
<ul>
<li><a href="/how-to/fix-image-seo-problems/">Which image SEO problems actually matter</a></li>
<li><a href="/how-to/fix-vague-and-empty-link-text/">How to fix vague and empty link text</a></li>
</ul>
""",
    )


def what_is_structured_data() -> Path:
    s = F.structured_data_own_sites()
    sources = s["sources"]
    sd_sites = format(s["sd_sites"], ",")
    sd_pages = format(s["sd_pages"], ",")
    sd_with_jsonld = format(s["sd_with_jsonld"], ",")
    sd_blocks = format(s["sd_blocks"], ",")
    sd_parse_errors = format(s["sd_parse_errors"], ",")
    sd_other_formats = format(s["sd_other_formats"], ",")
    sd_faq = format(s["sd_faq"], ",")
    sd_howto = format(s["sd_howto"], ",")
    gallery_count = format(s["gallery_count"], ",")
    sd_read_human = F.lt_fmt(s["read"])
    facts_read_human = F.lt_fmt(s["facts_read"])
    d_faq_limited = F.lt_fmt(s["dates"]["faq_limited"])
    d_howto_gone = F.lt_fmt(s["dates"]["howto_gone"])
    d_seven_gone = F.lt_fmt(s["dates"]["seven_gone"])
    d_faq_gone = F.lt_fmt(s["dates"]["faq_gone"])
    d_faq_limited_month = d_faq_limited.split(" ", 1)[1]
    d_faq_gone_short = d_faq_gone

    body = f"""
<p class="lede"><strong>Structured data is a small block of code, usually JSON-LD, that describes a page in a standard
vocabulary: this is an article, this is its author, this is a product and its price.</strong> <a href="{sources['intro']}" rel="nofollow noopener">Google says it uses it</a> to
understand the page, and to make the page eligible for richer results such as review stars or breadcrumbs. Eligible is the
word that matters: Google does not guarantee any result feature, and it has retired several since 2023, FAQ results among
them. On {sd_sites} sites I run, {sd_with_jsonld} of {sd_pages} pages carry it, and {sd_faq} of them still carry FAQ markup that
Google no longer shows.</p>

<h2>What it looks like</h2>

<pre><code>&lt;script type="application/ld+json"&gt;
{{
  "@context": "https://schema.org",
  "@type": "Organization",
  "name": "Example Bakery",
  "url": "https://example.com/",
  "logo": "https://example.com/logo.png"
}}
&lt;/script&gt;</code></pre>

<p>The words come from <a href="{sources['schema_org']}" rel="nofollow noopener">schema.org, a shared vocabulary</a> that Google, Microsoft, Yahoo and Yandex founded. The script sits in the
page's HTML and nobody sees it. Search engines read it alongside the page.</p>

<h2>The three formats</h2>

<ul>
<li><strong>JSON-LD</strong>, a separate script block like the one above. Google recommends it where your setup allows, because it sits
  apart from the visible HTML and is easy to maintain.</li>
<li><strong>Microdata</strong>, attributes such as itemscope and itemprop written into the visible HTML.</li>
<li><strong>RDFa</strong>, attributes such as typeof and property, also in the HTML.</li>
</ul>

<p>Google says all three are equally fine if the markup is valid. <a href="{sources['bing']}" rel="nofollow noopener">Bing says its crawlers</a> do not prefer one over another.</p>

<h2>What it does, and what it can't promise</h2>

<p>Google's documentation says structured data helps it understand a page and can make it eligible for rich results. It also
says, plainly, that it does not guarantee the markup will show up in search results. I found no Google page that calls it a
ranking factor. Treat it as a way to be understood and to qualify for a feature, not as a way to move up.</p>

<p>Bing says the same thing in its own words: markup alone doesn't guarantee Bing will use it, and it may support its AI
answers without guaranteeing visibility.</p>

<h2>The rules</h2>

<ul>
<li>Mark up only what readers can see. <a href="{sources['policies']}" rel="nofollow noopener">Google's guidelines</a> say not to mark up content that isn't visible on the page.</li>
<li>It has to be true. No fake reviews, and no ratings or prices that the page doesn't show.</li>
<li>Breaking these rules can cost a page its rich result eligibility through a manual action. Google says that kind of action
  does not change how the page ranks in ordinary results.</li>
</ul>

<h2>What Google has retired</h2>

<p>Rich result features come and go, and many guides still promise ones that no longer exist. From Google's own changelog:</p>

<div class="wrap-tbl"><table class="cmp">
<thead><tr><th>When</th><th>What changed</th></tr></thead>
<tbody>
<tr><td>{d_faq_limited}</td><td>FAQ results limited to well-known government and health sites</td></tr>
<tr><td>{d_howto_gone}</td><td>How-to results no longer shown, on mobile or desktop</td></tr>
<tr><td>{d_seven_gone}</td><td>Course info, estimated salary, learning video, special announcement and vehicle listing results removed</td></tr>
<tr><td>{d_faq_gone}</td><td>FAQ results no longer shown at all</td></tr>
</tbody></table></div>

<p>Read on <a href="{sources['updates']}" rel="nofollow noopener">developers.google.com/search/updates</a>, {facts_read_human}.</p>

<p><a href="{sources['gallery']}" rel="nofollow noopener">Google's gallery lists</a> {gallery_count} result features today, including article, breadcrumb, product, recipe, review
snippet, event, job posting, organization, software app and video. If a guide promises FAQ dropdowns or how-to steps in
Google's results, it is out of date.</p>

<h2>What four real sites showed</h2>

<p>I read every page in the sitemaps of {sd_sites} sites I run on {sd_read_human} and parsed every structured data block.</p>

<div class="wrap-tbl"><table class="cmp">
<thead><tr><th></th><th>Total</th></tr></thead>
<tbody>
<tr><td>Pages</td><td>{sd_pages}</td></tr>
<tr><td>Pages with JSON-LD</td><td>{sd_with_jsonld}</td></tr>
<tr><td>JSON-LD blocks</td><td>{sd_blocks}</td></tr>
<tr><td>Blocks that failed to parse</td><td>{sd_parse_errors}</td></tr>
<tr><td>Pages with Microdata or RDFa</td><td>{sd_other_formats}</td></tr>
<tr><td>Pages with FAQ markup</td><td>{sd_faq}</td></tr>
<tr><td>Pages with how-to markup</td><td>{sd_howto}</td></tr>
</tbody></table></div>

<p>Two things stood out.</p>

<p><strong>The basics were in place.</strong> Every block parsed. The common types were breadcrumbs, organization, person and article,
which are the ones Google's gallery still uses.</p>

<p><strong>Most of the FAQ markup is dead weight in Google.</strong> {sd_faq} pages carry FAQPage markup, added by our page templates. For
sites like ours it could not have produced a result: Google had already limited FAQ results to government and health sites
in {d_faq_limited_month}. It does no harm, and Bing still reads schema.org, but it earns nothing in Google Search. Before we knew it was retired, our own study of which pages earn clicks had
already found FAQ markup more common on the pages that got nothing.</p>

<h2>How to test it</h2>

<ul>
<li><strong>Google's Rich Results Test</strong> shows which Google result features your markup qualifies for, and can preview them.</li>
<li><strong><a href="{sources['validator']}" rel="nofollow noopener">The Schema Markup Validator</a></strong>, at validator.schema.org, checks any schema.org markup, without Google's feature rules.</li>
</ul>

<p>They answer different questions. A page can be valid schema.org and still qualify for nothing in Google.</p>

<h2>What Docket checks</h2>

<p>Docket reads the structured data on every page it crawls. It reports:</p>

<ul>
<li>JSON-LD that fails to parse, and markup holding an unfilled template tag.</li>
<li>A site with no structured data at all, or with it on only a small share of pages.</li>
<li>Identity markup that a script adds in the browser rather than serving in the HTML, and no breadcrumb markup.</li>
<li>Ratings or prices marked up but not shown on the page, which is the kind of markup Google's guidelines rule out.</li>
<li>Pages with question-and-answer content and no FAQ markup, as a low-priority note that says plainly Google retired FAQ
  results on {d_faq_gone_short}, so the markup no longer buys a result feature.</li>
</ul>
{buy_block("learn-what-is-structured-data", try_app="learn-what-is-structured-data-try-free")}
"""
    return render(
        cat="learn", slug="what-is-structured-data",
        modified="2026-11-09",
        title="What is structured data? What Google still uses in 2026",
        desc=("Structured data is markup that tells search engines what a page is about. "
              "The formats, what it can't promise, what Google retired, and what real pages showed."),
        h1="What is structured data?",
        crumb='<a href="/">Docket</a> / <a href="/learn/">Learn</a> / What is structured data?',
        body=body,
        published="2026-11-09",
        faq=[
            ("Is structured data a ranking factor?",
             "Google's documentation doesn't say it is. It says structured data helps Google understand a page "
             "and can make it eligible for rich results, without guaranteeing them."),
            ("Does FAQ schema still work?",
             f"Not in Google Search. Google stopped showing FAQ rich results on {d_faq_gone_short}. "
             "The markup does no harm, but it no longer produces an expandable answer."),
            ("Which format should I use?",
             "JSON-LD, which Google recommends where your setup allows. Microdata and RDFa work too, "
             "and Bing reads all three."),
            ("Is schema markup the same as structured data?",
             "In practice, yes. Schema markup usually means structured data written with the schema.org "
             "vocabulary, which is what Google and Bing read."),
        ],
        closer="""
<h2>Related</h2>
<ul>
<li><a href="/how-to/fix-structured-data-errors/">How to fix structured data errors</a></li>
<li><a href="/how-to/fix-structured-data-that-does-not-match-the-page/">Structured data that says what the page does not</a></li>
<li><a href="/tools/json-ld-checker/">JSON-LD checker</a></li>
<li><a href="/learn/what-is-a-sitemap/">What is a sitemap?</a></li>
</ul>
""",
    )


def what_is_robots_txt() -> Path:
    s = F.robots_txt_facts()
    sources = s["sources"]
    own_disallowed = format(s["own_disallowed"], ",")
    max_kib = format(s["max_kib"], ",")
    err_stop_hours = format(s["err_stop_hours"], ",")
    err_cache_days = format(s["err_cache_days"], ",")
    cache_hours = format(s["cache_hours"], ",")
    own_read_human = F.lt_fmt(s["read"])
    facts_read_human = F.lt_fmt(s["facts_read"])
    d_noindex_retired = F.lt_fmt(s["d_noindex_retired"])
    index_reached = format(F.index_reached(), ",")
    index_no_robots = format(F.index_no_robots(), ",")
    index_ai_mention = format(F.index_ai_mention(), ",")
    index_block_training = format(F.index_block_training(), ",")
    index_block_citation = format(F.index_block_citation(), ",")
    index_block_search = format(F.index_block_search(), ",")
    index_ccbot = format(F.index_ccbot(), ",")

    body = f"""
<p class="lede"><strong>robots.txt is a plain text file at the root of a site that tells crawlers which URLs they may and may
not fetch.</strong> It controls crawling, not indexing: a blocked page can still appear in Google, just without a
description. And it is a request, not a lock: well-behaved crawlers follow it, and anyone else can still open the URL. Of
the {index_reached} large sites in Docket's study, {index_no_robots} had no robots.txt at all.</p>

<h2>What it looks like</h2>

<pre><code>User-agent: *
Disallow: /cart/
Disallow: /search

User-agent: GPTBot
Disallow: /

Sitemap: https://example.com/sitemap.xml</code></pre>

<p>Each group starts with one or more User-agent lines, naming the crawler, then the rules for it. The star means any crawler
that isn't named elsewhere. The file must sit at the top of the host, as /robots.txt, and it covers only that host,
protocol and port. A robots.txt on www.example.com says nothing about shop.example.com.</p>

<h2>The lines Google reads</h2>

<ul>
<li><strong>User-agent:</strong> which crawler the group is for.</li>
<li><strong>Disallow:</strong> a path the crawler should not fetch.</li>
<li><strong>Allow:</strong> a path it may fetch, even inside a disallowed folder.</li>
<li><strong>Sitemap:</strong> where your sitemap is. This one can go anywhere in the file.</li>
</ul>

<p>Google ignores everything else. Crawl-delay is not supported by Google, though Bing honours it. A noindex line in
robots.txt has done nothing in Google since {d_noindex_retired}.</p>

<h2>How the rules match</h2>

<p>Three rules decide what a crawler does, and they trip people up more than the syntax does.</p>

<p><strong>A crawler follows one group: the most specific one that names it.</strong> If there is a group for Googlebot, Googlebot ignores
the star group entirely. Groups don't add up. One of the sites I run handles this correctly: it names each AI crawler in its
own group and repeats the same Disallow lines in every one, because a named group would otherwise lose the rules written
under the star.</p>

<p><strong>Within a group, the longest matching rule wins.</strong> With Disallow: /shop and Allow: /shop/sale, the sale pages are allowed,
because the longer rule is the closer match. When an Allow and a Disallow are the same length, Google picks the less
restrictive one, the Allow.</p>

<p><strong>Paths are case-sensitive, and two wildcards work.</strong> /Shop and /shop are different paths. A star matches any run of
characters, and a dollar sign marks the end of the URL, so Disallow: /*.pdf$ blocks every PDF. The words Disallow and
User-agent themselves are not case-sensitive.</p>

<h2>What robots.txt can't do</h2>

<p><strong>It can't keep a page out of search results.</strong> Google's own guide says robots.txt is not a way to keep a page out of
Google. If other pages link to a blocked URL, Google may still list it, with no description, because it never read the
page. To keep a page out, let it be crawled and give it a noindex tag, or put it behind a password. A noindex on a page
that robots.txt blocks is never seen, so the two together fail.</p>

<p><strong>It can't hide anything.</strong> The RFC that standardised robots.txt says its rules are not a form of access authorisation.
One of my own sites learned this the obvious way: its robots.txt disallows {own_disallowed} internal files, and on
{own_read_human} all {own_disallowed} still loaded for anyone who asked for them. Nothing in them was secret, but the
robots.txt line protected none of it.</p>

<h2>How Google treats the file itself</h2>

<div class="wrap-tbl"><table class="cmp">
<thead><tr><th>Situation</th><th>What Google does</th></tr></thead>
<tbody>
<tr><td>The file is over {max_kib} KiB</td><td>Reads the first {max_kib} KiB and ignores the rest</td></tr>
<tr><td>robots.txt returns 404 or another 4xx (not 429)</td><td>Crawls as if there were no robots.txt</td></tr>
<tr><td>robots.txt returns a 5xx</td><td>Stops crawling the site for {err_stop_hours} hours, then uses the last good copy for up to {err_cache_days} days</td></tr>
<tr><td>Any successful read</td><td>Caches the file for up to {cache_hours} hours</td></tr>
</tbody></table></div>

<p>From Google's robots.txt specification, read {facts_read_human}.</p>

<p>That 5xx row is the one to watch. A server error on robots.txt doesn't mean "no rules"; for Google it means "stop".</p>

<h2>AI crawlers in robots.txt</h2>

<p>Each AI company documents its own crawler names, and they do different jobs. Blocking the training crawler is not the
same as leaving an AI's search:</p>

<div class="wrap-tbl"><table class="cmp">
<thead><tr><th>Company</th><th>Name in robots.txt</th><th>What blocking it does</th></tr></thead>
<tbody>
<tr><td>OpenAI</td><td>GPTBot</td><td>Asks that your content not be used for training</td></tr>
<tr><td>OpenAI</td><td>OAI-SearchBot</td><td>Keeps your pages out of ChatGPT's search results</td></tr>
<tr><td>Anthropic</td><td>ClaudeBot</td><td>Asks that your future content not be used for training</td></tr>
<tr><td>Anthropic</td><td>Claude-SearchBot</td><td>Stops Claude indexing your content for search</td></tr>
<tr><td>Anthropic</td><td>Claude-User</td><td>Stops Claude fetching your page when a user asks about it</td></tr>
<tr><td>Google</td><td>Google-Extended</td><td>Opts out of Gemini training and grounding. It does not affect Google Search</td></tr>
</tbody></table></div>

<p>Read on each company's own crawler page, {facts_read_human}.</p>

<p>Docket's study shows how sites use these. Of the {index_reached} large, well-known sites it read (a hand-picked list, not a
random sample), {index_ai_mention} mentioned at least one AI crawler, {index_block_training} blocked at least one training
crawler, {index_block_citation} blocked at least one crawler that feeds AI answers, and {index_block_search} blocked a
search engine. The most-blocked name was CCBot, Common Crawl's crawler, on {index_ccbot} sites. The <a
href="/learn/ai-crawler-directives/">AI crawler directives guide</a> covers which to keep and which to block.</p>

<h2>What Docket checks</h2>

<p>Docket reads your robots.txt before it crawls and follows the rules written for Googlebot, and for Docket's own crawler if
you name it, matching them the way the standard describes: longest match, wildcards and the dollar sign. It reports:</p>

<ul>
<li>a robots.txt that blocks a crawler from the whole site;</li>
<li>a robots.txt with syntax problems, or one that returns a server error;</li>
<li>AI search crawlers and AI training crawlers that are blocked, listed separately because they do different jobs;</li>
<li>a CDN or firewall that blocks a crawler your robots.txt allows.</li>
</ul>

<p>You can test a single URL against your file with the free <a href="/tools/robots-txt-tester/">robots.txt tester</a>.</p>

<h2>Sources</h2>
<ul>
<li><a href="{sources['google_intro']}" rel="nofollow noopener">Google, robots.txt introduction</a></li>
<li><a href="{sources['google_spec']}" rel="nofollow noopener">Google, how Google interprets robots.txt</a></li>
<li><a href="{sources['google_noindex']}" rel="nofollow noopener">Google, block indexing with noindex</a></li>
<li><a href="{sources['rfc9309']}" rel="nofollow noopener">RFC 9309</a></li>
<li><a href="{sources['bing_crawl_control']}" rel="nofollow noopener">Bing, crawl control</a></li>
<li><a href="{sources['openai_bots']}" rel="nofollow noopener">OpenAI crawlers</a></li>
<li><a href="{sources['anthropic_bots']}" rel="nofollow noopener">Anthropic crawlers</a></li>
<li><a href="{sources['google_crawlers']}" rel="nofollow noopener">Google common crawlers</a></li>
</ul>

{buy_block("learn-what-is-robots-txt", try_app="learn-what-is-robots-txt-try-free")}
"""
    return render(
        cat="learn", slug="what-is-robots-txt",
        modified="2026-11-09",
        title="What is robots.txt? What it controls, and what it can't",
        desc=("robots.txt asks crawlers which URLs not to fetch. How rules match, what Google and Bing ignore, "
              "why it can't keep a page out of search, and what big sites block."),
        h1="What is robots.txt?",
        crumb='<a href="/">Docket</a> / <a href="/learn/">Learn</a> / What is robots.txt?',
        body=body,
        published="2026-11-09",
        faq=[
            ("Does robots.txt stop a page from being indexed?",
             "No. It stops crawling. Google can still list a blocked URL, without a description, if other pages "
             "link to it. To keep a page out of search, allow crawling and add a noindex tag."),
            ("Do I need a robots.txt file?",
             "Not strictly. With no robots.txt, crawlers treat every URL as allowed. Many sites have one anyway, "
             "to point to the sitemap and keep crawlers out of cart, search and admin pages."),
            ("Does Google support crawl-delay?",
             "No. Google ignores it. Bing honours it. To slow Googlebot down, your server can answer with a 503 "
             "or 429 status for a while."),
            ("Is robots.txt case-sensitive?",
             "The paths are: /Shop and /shop are different. The field names, such as Disallow, and the crawler "
             "names are not."),
        ],
        closer="""
<h2>Related</h2>
<ul>
<li><a href="/learn/ai-crawler-directives/">Every AI crawler: which to block and which to keep</a></li>
<li><a href="/learn/who-blocks-googlebot/">Who blocks Googlebot, and who blocks GoogleOther</a></li>
<li><a href="/tools/robots-txt-tester/">robots.txt tester</a></li>
<li><a href="/learn/what-is-a-sitemap/">What is a sitemap?</a></li>
</ul>
""",
    )


def what_is_a_404_error() -> Path:
    s = F.error_404_own_sites()
    sources = s["sources"]
    own_sites = format(s["own_sites"], ",")
    own_paths = format(s["own_paths"], ",")
    own_requests = format(s["own_requests"], ",")
    own_real_404 = format(s["own_real_404"], ",")
    own_soft_404 = format(s["own_soft_404"], ",")
    own_noindex_sites = format(s["own_noindex_sites"], ",")
    own_links_min = format(s["own_links_min"], ",")
    own_links_max = format(s["own_links_max"], ",")
    own_read_human = F.lt_fmt(s["read"])

    body = f"""
<p class="lede"><strong>A 404 error is the status code a web server sends when it has nothing at the address you asked for:
404 Not Found.</strong> It doesn't say whether the page is gone for good or just never existed. On its own, a 404 is not an
SEO problem: Google says a 404 on some URLs doesn't count against the rest of your site. The 404s worth fixing are the ones
your own pages link to, and the "soft 404": a missing page that answers with 200 OK instead. I asked {own_sites} sites I run for
pages that don't exist, {own_requests} requests in all, and every one answered with a real 404.</p>

<h2>What the code means</h2>

<p>HTTP status codes are three-digit answers a server gives with every response. The ones that start with 4 mean the request
couldn't be served as asked. 404 is the most common. The HTTP standard, RFC 9110, says it means the server did not find
anything for that address, and that it does not indicate whether this is temporary or permanent.</p>

<p>Its close relative is <strong>410 Gone</strong>, which says the page is gone and that this is likely permanent. You don't need it: the
standard says it isn't necessary to mark every removed page as gone, and Google says it treats all 4xx codes the same way,
apart from 429.</p>

<h2>Do 404s hurt SEO?</h2>

<p>Not by themselves. Google's documentation says a 4xx code has no effect on how fast it crawls your site, and that a URL
that returns 404 is removed from the index if it was indexed. Google's own post on the question says that 404s on some pages
don't hurt the rest of your site. The web is full of dead addresses, and a search engine expects to meet them.</p>

<p>They do cost you in three cases:</p>

<ul>
<li><strong>Your own pages link to them.</strong> A visitor clicks and hits a dead end, and the link goes nowhere useful. Fix the link, or
  redirect the old address to the page that replaced it.</li>
<li><strong>The page moved.</strong> If the content lives at a new address, a 301 redirect to it keeps visitors and the links other sites
  gave you. Use a 404 when there's no replacement, and a 301 when there is.</li>
<li><strong>It's a soft 404.</strong> That one gets its own section.</li>
</ul>

<h2>The soft 404: a missing page that says 200</h2>

<p>A soft 404 is a page that tells the reader "not found" but tells the browser and the crawler "200 OK". Google then treats it
as a real page, keeps crawling it, and its documentation says soft 404s waste your crawl budget. The two common causes:</p>

<ul>
<li>A site that serves its "page not found" design with a 200 status. Some page builders and single-page apps do this by
  default.</li>
<li>Sending every missing URL to the home page with a redirect. Google says not to redirect many old URLs to one irrelevant
  page such as the home page, because it can treat that as a soft 404.</li>
</ul>

<p>The test takes a minute: ask your site for an address that can't exist, and look at the status code it sends back, not just
the page it shows.</p>

<h2>What four real sites returned</h2>

<p>On {own_read_human} I asked {own_sites} sites I run for {own_paths} made-up paths each: a missing folder, a missing guide and
an old-style .html page.</p>

<div class="wrap-tbl"><table class="cmp">
<thead><tr><th></th><th>Result</th></tr></thead>
<tbody>
<tr><td>Requests</td><td>{own_requests}</td></tr>
<tr><td>Answered with a real 404</td><td>{own_real_404}</td></tr>
<tr><td>Answered 200 (a soft 404)</td><td>{own_soft_404}</td></tr>
<tr><td>Not-found pages marked noindex</td><td>{own_noindex_sites} of {own_sites} sites</td></tr>
<tr><td>Links back into the site on the not-found page</td><td>from {own_links_min} to {own_links_max}</td></tr>
</tbody></table></div>

<p>All of them got the status code right. Where they differed was what a lost visitor could do next. The best not-found page
offered {own_links_max} links back into the site. The weakest offered {own_links_min}. A 404 page is still a page someone is looking at: give them the main sections, a search box and a way to the
thing they most likely wanted.</p>

<h2>How to handle a 404, by situation</h2>

<div class="wrap-tbl"><table class="cmp">
<thead><tr><th>Situation</th><th>What to return</th></tr></thead>
<tbody>
<tr><td>The page never existed, or someone mistyped</td><td>404, with a helpful not-found page</td></tr>
<tr><td>The page was removed and nothing replaces it</td><td>404 or 410</td></tr>
<tr><td>The page moved, or a better page replaces it</td><td>A 301 redirect to that page</td></tr>
<tr><td>A misspelled address that people keep using</td><td>A 301 redirect to the right page</td></tr>
<tr><td>A page shows "not found" but returns 200</td><td>Fix the server so it returns 404</td></tr>
</tbody></table></div>

<h2>What Docket checks</h2>

<p>Docket asks your site for a made-up address on every audit and reports when it answers 200 instead of 404, which is the
site-wide soft 404 test above. It also reports pages that show an error message but return 200, missing pages that your own
pages link to, links to your own subdomains that are broken, and outbound links that are broken. A 404 that nothing links to
is left alone, because that one is fine.</p>

<h2>Sources</h2>
<ul>
<li><a href="{sources['rfc9110_404']}" rel="nofollow noopener">RFC 9110, 404 Not Found</a></li>
<li><a href="{sources['rfc9110_410']}" rel="nofollow noopener">RFC 9110, 410 Gone</a></li>
<li><a href="{sources['mdn_404']}" rel="nofollow noopener">MDN, 404</a></li>
<li><a href="{sources['google_status_codes']}" rel="nofollow noopener">Google, HTTP status codes and crawling</a></li>
<li><a href="{sources['google_crawl_budget']}" rel="nofollow noopener">Google, crawl budget</a></li>
<li><a href="{sources['google_404_blog']}" rel="nofollow noopener">Google Search blog, do 404s hurt my site</a></li>
<li><a href="{sources['google_site_move']}" rel="nofollow noopener">Google, site moves (redirects to the home page)</a></li>
<li><a href="{sources['google_301']}" rel="nofollow noopener">Google, 301 redirects</a></li>
</ul>

{buy_block("learn-what-is-a-404-error", try_app="learn-what-is-a-404-error-try-free")}
"""
    return render(
        cat="learn", slug="what-is-a-404-error",
        modified="2026-11-09",
        title="What is a 404 error? What it means, and when it's fine",
        desc=("A 404 means the server found nothing at that address. When it's harmless, when it isn't, "
              "the soft 404 trap, 404 vs 410, and what four real sites returned."),
        h1="What is a 404 error?",
        crumb='<a href="/">Docket</a> / <a href="/learn/">Learn</a> / What is a 404 error?',
        body=body,
        published="2026-11-09",
        faq=[
            ("Do 404 errors hurt SEO?",
             "Not on their own. Google says 404s on some URLs don't count against the rest of your site, and it "
             "removes those URLs from its index. They matter when your own pages link to them, when the content "
             "moved and needed a redirect, or when a missing page returns 200 instead."),
            ("What's the difference between 404 and 410?",
             "404 means nothing was found, without saying whether that's permanent. 410 Gone says it is likely "
             "permanent. Google says it treats all 4xx codes the same, apart from 429, so either works for a "
             "removed page."),
            ("Should I redirect every 404 to my home page?",
             "No. Google warns that sending many old URLs to one irrelevant page, such as the home page, can be "
             "treated as a soft 404. Redirect a URL only to a page that really replaces it, and let the rest "
             "return 404."),
            ("What is a soft 404?",
             "A page that says \"not found\" to the reader but returns 200 OK to the browser. Search engines then "
             "treat it as a real page and keep crawling it. The fix is to make the server return 404 for addresses "
             "that don't exist."),
        ],
        closer="""
<h2>Related</h2>
<ul>
<li><a href="/how-to/fix-soft-404s/">Soft 404s: how to find and fix them</a></li>
<li><a href="/how-to/fix-redirect-problems/">How to fix redirect problems</a></li>
<li><a href="/learn/what-is-robots-txt/">What is robots.txt?</a></li>
<li><a href="/learn/what-is-a-sitemap/">What is a sitemap?</a></li>
</ul>
""",
    )


def what_is_a_favicon() -> Path:
    s = F.favicon_own_sites()
    sources = s["sources"]
    own_sites = format(s["own_sites"], ",")
    own_declare = format(s["own_declare"], ",")
    own_apple = format(s["own_apple"], ",")
    own_svg_only = format(s["own_svg_only"], ",")
    own_ico_404 = format(s["own_ico_404"], ",")
    own_robots_block = format(s["own_robots_block"], ",")
    g_min_px = format(s["g_min_px"], ",")
    g_rec_px = format(s["g_rec_px"], ",")
    apple_px = format(s["apple_px"], ",")
    manifest_small = format(s["manifest_small"], ",")
    manifest_large = format(s["manifest_large"], ",")
    own_read_human = F.lt_fmt(s["read"])
    facts_read_human = F.lt_fmt(s["facts_read"])

    body = f"""
<p class="lede"><strong>A favicon is the small icon that stands for your site: in the browser tab, in bookmarks, on a phone's
home screen, and next to your site's name in search results.</strong> You add it with a link tag in the page's head. For
Google, it has to be square, at least {g_min_px} pixels, in a format Google lists, and declared on your home page. SVG,
the format many modern sites use, is not on Google's list. On {own_sites} sites I run, {own_svg_only} declared only an SVG
icon.</p>

<h2>What it looks like in the HTML</h2>

<pre><code>&lt;link rel="icon" href="/favicon.ico" sizes="any"&gt;
&lt;link rel="icon" href="/icon.svg" type="image/svg+xml"&gt;
&lt;link rel="apple-touch-icon" href="/apple-touch-icon.png"&gt;</code></pre>

<p>The browser picks the best icon from what you declare. If you declare none, browsers fall back to asking for /favicon.ico at
the root of the site, which is why that file shows up in server logs even on sites that never made one.</p>

<h2>Google's rules for the icon in search results</h2>

<p>From Google Search Central's favicon page, read {facts_read_human}:</p>

<ul>
<li><strong>Square, and at least {g_min_px} by {g_min_px} pixels.</strong> Google recommends larger than {g_rec_px} by {g_rec_px}, so it
  looks good on every surface.</li>
<li><strong>A format Google lists:</strong> BMP, GIF, ICO, PNG, JPEG, PPM or TIFF. SVG and WebP are not on the list.</li>
<li><strong>On the home page.</strong> Put the link tag in the head of your home page. Google supports one favicon per hostname, so a
  subdomain needs its own, and a section of a site can't have a different one.</li>
<li><strong>Crawlable.</strong> Googlebot-Image must be able to fetch the file, and robots.txt must not block the icon or the home page.</li>
<li><strong>A stable address.</strong> Google asks you not to change the favicon's URL often.</li>
<li><strong>Patience.</strong> Google says a new favicon can take from several days to several weeks to appear, and that a favicon is not
  guaranteed to appear at all.</li>
</ul>

<p>Google reads four kinds of link for this: icon, shortcut icon, apple-touch-icon and apple-touch-icon-precomposed.</p>

<h2>SVG: fine for browsers, not on Google's list</h2>

<p>SVG favicons are popular because one small file stays sharp at every size, and Chromium browsers and Firefox support them.
But Google Search's list of favicon formats does not include SVG. The safe setup is the one above: an ICO or PNG icon for
everything that needs a bitmap, an SVG for browsers that want it, and an apple-touch-icon for phones.</p>

<h2>What four real sites declare</h2>

<p>I read the home page of {own_sites} sites I run on {own_read_human} and fetched every icon they declared.</p>

<div class="wrap-tbl"><table class="cmp">
<thead><tr><th></th><th>Sites</th></tr></thead>
<tbody>
<tr><td>Declare a favicon in the head</td><td>{own_declare} of {own_sites}</td></tr>
<tr><td>Have a {apple_px} by {apple_px} apple-touch-icon</td><td>{own_apple} of {own_sites}</td></tr>
<tr><td>Declare only an SVG as their icon</td><td>{own_svg_only} of {own_sites}</td></tr>
<tr><td>Return 404 for /favicon.ico</td><td>{own_ico_404} of {own_sites}</td></tr>
<tr><td>Block the icon in robots.txt</td><td>{own_robots_block} of {own_sites}</td></tr>
</tbody></table></div>

<p>The SVG-only sites are probably still covered in Google, because Google also reads apple-touch-icon, and both have a PNG
there. But that rests on one tag. Adding a PNG or ICO icon of at least {g_rec_px} pixels would make it certain, and it would
stop the 404s for /favicon.ico in their logs.</p>

<h2>The sizes worth making</h2>

<div class="wrap-tbl"><table class="cmp">
<thead><tr><th>File</th><th>Size</th><th>Used by</th></tr></thead>
<tbody>
<tr><td>favicon.ico or a PNG icon</td><td>{g_rec_px} pixels or larger, square</td><td>Browsers, and Google Search results</td></tr>
<tr><td>icon.svg</td><td>Any (it scales)</td><td>Modern browser tabs</td></tr>
<tr><td>apple-touch-icon.png</td><td>{apple_px} by {apple_px}</td><td>iPhone and iPad home screens</td></tr>
<tr><td>Manifest icons</td><td>{manifest_small} and {manifest_large} pixels</td><td>Installed web apps on Chromium browsers</td></tr>
</tbody></table></div>

<h2>Does a favicon help SEO?</h2>

<p>Not as a ranking signal. Google's favicon page says nothing about rankings. What it changes is how your result looks: a
recognisable icon beside your name in the results, and in a crowded list of tabs. Treat it as part of looking finished, not
as a way to move up.</p>

<h2>What Docket checks</h2>

<p>Docket fetches the icons your home page declares to make sure at least one is a real image file, not an error page served in
its place, and falls back to /favicon.ico when none of them works. It reports when no usable favicon is found. It does not check the icon's format
against Google's list, so an SVG-only favicon is worth checking by eye. If your icon still isn't showing in Google, our
<a href="/how-to/fix-favicon-not-showing-in-search/">guide to a favicon missing from search</a> walks through the usual causes.</p>

<h2>Sources</h2>
<ul>
<li><a href="{sources['google_favicon']}" rel="nofollow noopener">Google, favicon in search results</a></li>
<li><a href="{sources['whatwg_icon']}" rel="nofollow noopener">HTML standard, rel="icon"</a></li>
<li><a href="{sources['mdn_link']}" rel="nofollow noopener">MDN, the link element</a></li>
<li><a href="{sources['webdev_svg_favicon']}" rel="nofollow noopener">web.dev, an adaptive SVG favicon</a></li>
<li><a href="{sources['webdev_manifest']}" rel="nofollow noopener">web.dev, the web app manifest</a></li>
</ul>

{buy_block("learn-what-is-a-favicon", try_app="learn-what-is-a-favicon-try-free")}
"""
    return render(
        cat="learn", slug="what-is-a-favicon",
        modified="2026-11-09",
        title="What is a favicon? Sizes, formats and Google's rules",
        desc=("A favicon is the small icon for your site in tabs, bookmarks and search results. "
              "Google's current rules, which formats it lists, and what four real sites declare."),
        h1="What is a favicon?",
        crumb='<a href="/">Docket</a> / <a href="/learn/">Learn</a> / What is a favicon?',
        body=body,
        published="2026-11-09",
        faq=[
            ("What size should a favicon be?",
             f"Google requires a square of at least {g_min_px} pixels and recommends larger than {g_rec_px}. A "
             f"{g_rec_px}-pixel or larger PNG or ICO, plus an SVG for browsers and a {apple_px}-pixel apple-touch-icon, "
             f"covers search, tabs and phones."),
            ("Does Google support SVG favicons?",
             f"Google Search's favicon page lists BMP, GIF, ICO, PNG, JPEG, PPM and TIFF, and not SVG. Browsers support "
             f"SVG, so use it alongside a PNG or ICO icon, not instead of one."),
            ("Why isn't my favicon showing in Google?",
             f"Common causes: it isn't declared on the home page, it isn't square, it's smaller than {g_min_px} pixels, "
             f"it's in a format Google doesn't list, robots.txt blocks it, or Google hasn't recrawled yet, which can "
             f"take several weeks."),
            ("Do I still need a favicon.ico file?",
             f"Not for Google, which reads the icon you declare. But browsers and other tools ask for /favicon.ico when "
             f"nothing is declared, so having one avoids a stream of 404s."),
        ],
        closer="""
<h2>Related</h2>
<ul>
<li><a href="/how-to/fix-favicon-not-showing-in-search/">Why your favicon isn't showing in search</a></li>
<li><a href="/learn/what-is-a-404-error/">What is a 404 error?</a></li>
<li><a href="/learn/what-is-robots-txt/">What is robots.txt?</a></li>
<li><a href="/learn/what-is-structured-data/">What is structured data?</a></li>
</ul>
""",
    )


def claude_search_crawlers() -> Path:
    """Which crawlers feed Claude's web search? Answered from the operators' own pages, read 2026-11-06.

    Matthew, 2026-11-07 00:1xZ via the CEO: "make sure we're seen by Claude". Claude's own web search did not
    find docketseo.app by name. Anthropic's Trust Center lists its web-search subprocessors; Parallel and Brave
    each say what their crawler does. Nothing here is a guess about how Claude weighs them: Anthropic does not
    publish that, and the page says so."""
    body = f"""
<p class="lede"><strong>Claude&rsquo;s web search reads pages through Anthropic&rsquo;s own crawlers and
through outside search providers.</strong> Anthropic&rsquo;s are Claude-SearchBot and Claude-User.
Anthropic&rsquo;s subprocessor list also names three web search providers: Brave Search, Parallel Web
Systems and turbopuffer. Parallel&rsquo;s crawler is ShapBot. Brave&rsquo;s crawler has no name of its
own and follows your Googlebot rules.</p>

<h2>Each one, in its operator&rsquo;s words</h2>
<div class="wrap-tbl"><table class="cmp">
<thead><tr><th>Crawler</th><th>Operator</th><th>What the operator says</th><th>What robots.txt does</th></tr></thead>
<tbody>
<tr><td><code>Claude-SearchBot</code></td><td>Anthropic</td><td>&ldquo;navigates the web to improve search
result quality for users&rdquo;</td><td>Its own group, or <code>*</code>, decides.</td></tr>
<tr><td><code>Claude-User</code></td><td>Anthropic</td><td>fetches a page &ldquo;when individuals ask
questions to Claude&rdquo;</td><td>Its own group, or <code>*</code>, decides.</td></tr>
<tr><td><code>ShapBot</code></td><td>Parallel Web Systems</td><td>&ldquo;collects publicly available web
content to build and maintain Parallel&rsquo;s search index&rdquo;</td><td>Follows a <code>ShapBot</code>
group, or <code>*</code>. Parallel says changes take effect within about a day.</td></tr>
<tr><td><code>Shap-User</code></td><td>Parallel Web Systems</td><td>identifies itself &ldquo;when accessing
content on behalf of users&rdquo;</td><td>Parallel says it is meant for visibility, not to be managed by
automated controls, so a block may not stop it.</td></tr>
<tr><td>Brave Search&rsquo;s crawler</td><td>Brave</td><td>&ldquo;does not advertise a differentiated user
agent&rdquo;</td><td>Brave says a page Googlebot may not crawl is not crawled by Brave either.</td></tr>
</tbody></table></div>
<p class="table-note">Read on {_read_day()} from <a href="{ANTHROPIC_SUBPROCESSORS}" rel="nofollow noopener">Anthropic&rsquo;s
subprocessor list</a>, <a href="{PARALLEL_BOTS}" rel="nofollow noopener">Parallel&rsquo;s bot page</a>, effective the
same day, and <a href="{BRAVE_CRAWLER}" rel="nofollow noopener">Brave&rsquo;s crawler page</a>. Anthropic&rsquo;s
own crawlers are from <a href="{ANTHROPIC_BOTS}" rel="nofollow noopener">its help article</a>.</p>
<p>turbopuffer is on the list too. It makes search database software, and Anthropic does not say what
part it plays in Claude&rsquo;s search. Anthropic does not publish how Claude weighs any of these
providers either, so the safe position is to be open to all of them.</p>

<h2>How to stay findable</h2>
<p>If your robots.txt allows everything, there is nothing to change. If it closes the door to bots it
does not know, which is common after a wave of AI blocking, name the search crawlers and open them:</p>
<pre><code>User-agent: Claude-SearchBot
User-agent: Claude-User
User-agent: ShapBot
Allow: /</code></pre>
<p>Keep Googlebot open as well, because Brave follows those rules. Blocking ClaudeBot, which collects
training data, does not affect any of this; <a href="/learn/what-is-claudebot/">what ClaudeBot does</a>
explains the difference. A firewall or CDN rule can still refuse a crawler your file welcomes, and that
is the most common reason a site that meant to stay open is not.</p>

<h2>Docket checks them</h2>
<p>The free <a href="/tools/ai-crawler-checker/">AI crawler checker</a> now includes ShapBot and
Shap-User beside Anthropic&rsquo;s crawlers, and Docket&rsquo;s app adds them in its next release.</p>
{_checker("Most sites have never checked what their file says to the crawlers behind Claude&rsquo;s search.")}
{buy_block("learn-claude-search-crawlers", try_app="learn-claude-search-crawlers-try-free")}

<h2>Related</h2>
<ul>
<li><a href="/learn/what-is-claudebot/">What is ClaudeBot?</a></li>
<li><a href="/learn/ai-crawler-directives/">Every AI crawler: which to block and which to keep</a></li>
<li><a href="/how-to/fix-ai-crawlers-blocked-by-your-cdn/">When your CDN blocks crawlers your robots.txt allows</a></li>
</ul>
"""
    return render(
        cat="learn", slug="claude-search-crawlers",
        title="Which crawlers feed Claude's web search?",
        desc=("Claude's search reads pages through Claude-SearchBot, Claude-User and providers Anthropic lists: "
              "Brave, Parallel's ShapBot and turbopuffer."),
        h1="Which crawlers feed Claude&rsquo;s web search?",
        crumb='<a href="/">Docket</a> / <a href="/learn/">Learn</a> / Crawlers behind Claude&rsquo;s search',
        body=body,
        published="2026-11-06",
        faq=[
            ("Does Claude use Brave Search?",
             "Anthropic's subprocessor list names Brave Search as a web search provider for all its products. "
             "Brave's crawler has no separate user agent and follows your Googlebot rules."),
            ("What is ShapBot?",
             "Parallel Web Systems' crawler. Parallel says it collects public web content to build its search "
             "index, and Anthropic lists Parallel as a web search provider for Claude."),
            ("Should I block ShapBot?",
             "Only if you want to stay out of Parallel's index. Parallel says restricting it may reduce your "
             "visibility through its search features, and Claude's web search uses Parallel."),
        ],
    )


def _read_day() -> str:
    return "6 November 2026"


BUILDERS = [what_is_claudebot, what_is_llms_txt, what_is_a_sitemap, what_is_alt_text, what_is_structured_data, what_is_robots_txt, what_is_a_404_error, what_is_a_favicon, claude_search_crawlers]


def build_all() -> list[Path]:
    return [b() for b in BUILDERS]


if __name__ == "__main__":
    for p in build_all():
        print(p)
