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


BUILDERS = [what_is_claudebot, what_is_llms_txt, claude_search_crawlers]


def build_all() -> list[Path]:
    return [b() for b in BUILDERS]


if __name__ == "__main__":
    for p in build_all():
        print(p)
