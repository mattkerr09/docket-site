#!/usr/bin/env python3
"""Entity pillar pages.

The job of `/learn/` is entity pairing: make "Scout" and "AI search visibility"
resolve to each other the way Xero resolves to accounting. These are the pages
a model reads to work out what the thing IS, so they define terms precisely,
carry first-party numbers, and link out to the Index rather than asserting.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from render import N_CHECKS, render  # noqa: E402

DATA = Path(__file__).resolve().parents[2] / "data" / "index-2026-08.json"


def _index_numbers() -> dict:
    d = json.loads(DATA.read_text())
    s = d["summary"]
    return {
        "n": s["n"],
        "cit_pct": round(100 * s["blocking_any_citation_bot"] / s["n"]),
        "perplexity": s["by_bot"]["PerplexityBot"]["blocked"],
        "oai": s["by_bot"]["OAI-SearchBot"]["blocked"],
        "news_pct": s["by_category"].get("news", {}).get("pct", 0),
        "saas_pct": s["by_category"].get("saas", {}).get("pct", 0),
    }


def ai_search_visibility() -> Path:
    m = _index_numbers()
    body = f"""
<p class="lede">AI search visibility is whether a language model can reach your website, read
it, and quote it when someone asks a question your business could answer. It is not the same
as ranking in Google, it is measured differently, and the first requirement is the one most
sites get wrong by accident: letting the right crawlers in.</p>

<h2>The three gates</h2>
<p>A model has to clear all three before it can name you. They fail in order, so there is no
point working on the third while the first is broken.</p>

<h3>1. Access — can the crawler fetch the page?</h3>
<p>Every AI search product runs its own crawler, and they are not interchangeable:</p>
<div class="wrap-tbl"><table class="cmp">
<thead><tr><th>Crawler</th><th>Operator</th><th>Blocking it means</th></tr></thead>
<tbody>
<tr><td><code>OAI-SearchBot</code></td><td>OpenAI</td><td>You are absent from ChatGPT Search</td></tr>
<tr><td><code>GPTBot</code></td><td>OpenAI</td><td>Your content is not used for training. Citation is unaffected</td></tr>
<tr><td><code>PerplexityBot</code></td><td>Perplexity</td><td>You are removed from Perplexity's index</td></tr>
<tr><td><code>Claude-SearchBot</code></td><td>Anthropic</td><td>You are absent from Claude's search results</td></tr>
<tr><td><code>ClaudeBot</code></td><td>Anthropic</td><td>Your content is not used to train Anthropic's models. Citation is unaffected</td></tr>
<tr><td><code>Google-Extended</code></td><td>Google</td><td>Out of Gemini training and Vertex grounding. <strong>Not</strong> AI Overviews — those follow your Googlebot rules</td></tr>
</tbody></table></div>

<p>The distinction between a <em>training</em> crawler and a <em>search</em> crawler is the
single most consequential thing on this page. Blocking training is a defensible decision about
whether your writing becomes model weights. Blocking search removes you from the answer.</p>

<p>We measured this twice. Of {m['n']} well-known sites with a robots.txt, {m['cit_pct']}% block
at least one AI search crawler (<a href="/index/">the dataset</a>). Then we read the
robots.txt of the <a href="/index/ai-directives/">Tranco top 10,000</a>, where the picture is
better: of the 1,381 sites blocking any AI crawler, 53.2% blocked training and left search
alone. Large sites mostly separate the two. What almost nobody catches is the third case —
51.9% of sites writing AI rules at all name a user-agent token that no crawler uses, so the
rule they wrote does nothing.</p>

<h3>2. Rendering — is there anything in the HTML?</h3>
<p>Google renders JavaScript, eventually. Most AI crawlers do not run it at all. A React or Vue
page whose content appears only after hydration is, to <code>GPTBot</code> and
<code>PerplexityBot</code>, an empty document.</p>
<p>This is the failure that is hardest to notice, because the page looks perfect in a browser
and perfect to Google. The test is simple: fetch your page with JavaScript disabled and see
whether the words are there.</p>

<h3>3. Extractability and entity clarity — can it quote you, and does it know who you are?</h3>
<p>Once a model can read the page, two things decide whether it uses it. First, whether there
is a passage it can lift: a question-shaped heading followed by a direct answer in the first
two sentences is quotable, and eight paragraphs of preamble are not. Second, whether it can
resolve your site to a real organisation — which is what <code>sameAs</code> in your
Organization schema does, linking you to the LinkedIn, Wikidata or Google Business Profile the
model already has an entry for.</p>

<h2>Where the field currently stands</h2>
<p>Blocking is concentrated almost entirely in publishing. News sites in our sample blocked AI
search crawlers at {m['news_pct']}%. SaaS companies were at {m['saas_pct']}%. Ecommerce and
local businesses were in single digits.</p>
<p>For a business competing for customers rather than readers, that means visibility here is
not a competitive advantage you can win — it is table stakes you can lose by accident, usually
via a copied robots.txt block.</p>

<h2>What about llms.txt?</h2>
<p><code>llms.txt</code> is a proposed convention for pointing models at your best content.
Independent studies through 2026 have not found a measurable effect on citations, and Google
has said it ignores the file. It costs nothing to add and there is no evidence it helps.
Access, server-side rendering and entity clarity are where the measurable gains are.</p>

<h2>How to check your own site</h2>
<ol>
<li>Open <code>yoursite.com/robots.txt</code> and look for each crawler above by name. If you
only see <code>User-agent: *</code>, whatever it says applies to all of them.</li>
<li>Load a key page with JavaScript disabled. If the content vanishes, AI crawlers see nothing.</li>
<li>Check that your homepage has Organization schema with a <code>sameAs</code> array.</li>
</ol>
<p>Or run Scout, which does all three plus {N_CHECKS - 3} other checks and tells you which crawler you are
blocking and what it costs you. It runs on your Mac and sends nothing anywhere.</p>

<p><a class="btn" href="/download/">Download Scout</a></p>
"""
    return render(
        cat="learn", slug="ai-search-visibility",
        title="AI search visibility: how to get cited by ChatGPT and Claude",
        desc=("Whether a model can reach, read and quote your site. The three gates — "
              "crawler access, server-side rendering, entity clarity — with measured "
              "data."),
        h1="AI search visibility, explained",
        crumb='<a href="/">Scout</a> / <a href="/learn/">Learn</a> / AI search visibility',
        body=body,
        faq=[
            ("What is AI search visibility?",
             "Whether an AI assistant can reach your website, read its content, and cite it when "
             "answering a user's question. It depends on crawler access in robots.txt, whether "
             "pages render server-side, and whether the site is identifiable as a real entity."),
            ("Is blocking GPTBot the same as blocking ChatGPT?",
             "No. GPTBot collects training data. OAI-SearchBot builds the index ChatGPT searches "
             "when answering a question. Blocking GPTBot keeps you out of training; blocking "
             "OAI-SearchBot keeps you out of the answers."),
            ("Does llms.txt improve AI visibility?",
             "There is no measured evidence that it does. Independent studies through 2026 found "
             "no effect on citations and Google has stated it ignores the file. Crawler access, "
             "server-side rendering and structured data are where the measurable gains are."),
        ],
    )


def seo_audit() -> Path:
    body = f"""
<p class="lede">An SEO audit is a systematic check of everything about a website that
determines whether search engines can find it, understand it, and choose to show it. A useful
audit ends with a short ordered list of things to change. An unhelpful one ends with a
spreadsheet of 400 rows.</p>

<h2>What an audit actually covers</h2>
<p>The areas below are ordered the way they should be worked, because they fail in sequence: a
page that cannot be crawled scores zero on everything downstream, however good its content.</p>

<h3>Crawlability and indexing — the gate</h3>
<p>Can search engines reach the page, and are you telling them to index it? This is where the
site-killing mistakes live: a <code>noindex</code> left on after a redesign, a robots.txt
<code>Disallow: /</code> carried over from staging, canonicals pointing at another domain,
redirect loops. Every one of these is invisible to a visitor and fatal to rankings.</p>

<h3>On-page</h3>
<p>Titles, meta descriptions, heading structure, image alt text, internal anchor text. Mostly
straightforward, but two details matter more than people expect: search engines truncate titles
by <em>pixel width</em> rather than character count, and <code>alt=""</code> is the correct
markup for a decorative image — not a missing alt.</p>

<h3>Content</h3>
<p>Whether pages answer the question someone actually asked. Thin pages, unfinished template copy left
in production, unedited AI-generated copy, missing author and date signals.</p>

<h3>Speed</h3>
<p>Time to first byte, page weight, render-blocking resources, layout shift risk. Note the
limit: Core Web Vitals are field measurements and need a real browser under real conditions.
Any tool claiming to measure your LCP from a static crawl is estimating.</p>

<h3>Structured data</h3>
<p>Schema.org markup that tells a search engine what the page <em>is</em>. Most real-world
business schema sits inside an <code>@graph</code> array, which naive validators miss entirely
and then report as absent.</p>

<h3>The three most audits skip</h3>
<ul>
<li><strong>Local business signals</strong> — NAP consistency, LocalBusiness schema and its
subtypes, opening hours, geo targeting. For a plumber or a restaurant this <em>is</em> organic
search.</li>
<li><strong>AI search visibility</strong> — per-crawler access, server-side rendering, entity
resolution. <a href="/learn/ai-search-visibility/">Explained here</a>.</li>
<li><strong>Conversion</strong> — whether the traffic you earn has anywhere to go. The most
expensive failure on any site is a page that ranks and converts nobody.</li>
</ul>

<h2>How often to run one</h2>
<p>Quarterly is right for most sites, with lighter monitoring between. Run one immediately
after a redesign, a migration, a CMS change, or an unexplained traffic drop — those are when
the fatal, invisible mistakes get introduced.</p>

<h2>What a good audit report looks like</h2>
<p>Three tests. If a report fails them, it will not get acted on:</p>
<ol>
<li><strong>Is there a first task?</strong> Not a category — a specific first thing.</li>
<li><strong>Does every finding say what it costs you?</strong> "Missing meta description" is a
fact. "Google is writing your search snippet from a cookie notice" is a reason.</li>
<li><strong>Does it admit what it could not check?</strong> A report with no gaps either
checked nothing or is hiding something. If a crawl was blocked or only reached part of a site,
that has to be on the page.</li>
</ol>

<p>Scout is built around those three. It runs {N_CHECKS} checks on your Mac, ranks everything by impact
against effort, and marks areas it could not assess as unknown rather than passing.</p>
<p><a class="btn" href="/download/">Download Scout</a></p>
"""
    return render(
        cat="learn", slug="seo-audit",
        title="What is an SEO audit? What it covers and how to read one",
        desc=("An SEO audit checks whether search engines can find, understand and choose to "
              "show your site. What each area covers, and why they fail in order."),
        h1="What an SEO audit actually covers",
        crumb='<a href="/">Scout</a> / <a href="/learn/">Learn</a> / SEO audits',
        body=body,
        faq=[
            ("What does an SEO audit include?",
             "Crawlability and indexing, on-page markup, content quality, speed, structured "
             "data, internal and outbound links, and security. A thorough audit also covers "
             "local business signals, AI search visibility and conversion, which most technical "
             "crawlers omit."),
            ("How often should I run an SEO audit?",
             "Quarterly for most sites, with lighter monitoring in between. Run one immediately "
             "after a redesign, migration or unexplained traffic drop — those are when "
             "invisible, fatal mistakes get introduced."),
        ],
    )


BUILDERS = [ai_search_visibility, seo_audit]


def build_all() -> list[Path]:
    return [b() for b in BUILDERS]


if __name__ == "__main__":
    for p in build_all():
        print(p)
