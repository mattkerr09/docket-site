#!/usr/bin/env python3
"""The AI crawlers Docket checks, and what blocking each one actually costs.

Sourced from `robots.AI_USER_AGENTS` — the same table the checks read, so the
page and the product cannot disagree about which crawlers were examined — plus
`ai_visibility.CITATION_CRITICAL` and `TRAINING_ONLY`, and the published
robots.txt dataset behind `facts.directives_*`.

⚠️ NO TYPED AGENT LIST AND NO TYPED COUNT. Every name, owner, purpose and
impact line comes through `facts.ai_agent_rows()` from `data/ai-agents.json`,
which `scripts/collect_ai_agents.py` generates. This is the most volatile table
in the engine — OpenAI split `OAI-SearchBot` out of `GPTBot` after launch,
Anthropic retired `Claude-Web`, Google added `Google-CloudVertexBot` — and a
count typed beside a table like that is wrong within weeks with nothing
rendering differently.

⚠️ WHAT THIS PAGE REFUSES TO SAY.

  1. That blocking a training crawler is a mistake. Site owners do it
     deliberately and for good reasons. The page's whole argument is that
     training and search are DIFFERENT DECISIONS, which is destroyed the moment
     it starts arguing for one of them.
  2. That `noai`, `noimageai` or any TDM meta tag is honoured by these
     crawlers. No operator in this table documents support for them. The page
     says what robots.txt does and stops.
  3. Anything about traffic, citations gained, or revenue. The dataset measures
     ACCESS — whether a file permits a crawler — and nothing downstream of it.
  4. Any site by name. The published figures are counts and categories only.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import facts as F  # noqa: E402
from render import render  # noqa: E402


def _rows_html() -> str:
    out = []
    for name, owner, purpose, impact in F.ai_agent_rows():
        out.append(f"<tr><td><code>{name}</code></td><td>{owner}</td>"
                   f"<td>{purpose}</td><td>{impact}</td></tr>")
    return "\n".join(out)


def ai_directives() -> Path:
    search = F.ai_agents_for("search index")
    body = f"""
<p class="lede">Blocking <code>GPTBot</code> and blocking <code>OAI-SearchBot</code> look like the
same decision in a robots.txt file. They are not remotely the same decision, and most sites that
make one make the other by accident. Docket checks
{F.ai_agents_word()} AI crawlers separately, from {F.ai_agent_operators()} companies, because the
cost of blocking each one is different.</p>

<h2>The distinction the whole thing turns on</h2>

<p>An AI company points more than one crawler at your site, and they do different jobs:</p>

<ul>
<li><strong>Training crawlers</strong> collect text to train a model. Blocking one means your
writing does not become training data. It does <em>not</em> remove you from any answer.</li>
<li><strong>Search-index crawlers</strong> build the index an assistant searches when it answers
a question with live citations. Blocking one removes you from those answers entirely.</li>
<li><strong>Live-fetch agents</strong> retrieve a page at the moment a user asks about it —
usually because someone pasted your URL. Blocking one means the assistant cannot read a page a
user explicitly asked it to read.</li>
</ul>

<p>That is why "should I block AI crawlers?" has no single answer. Keeping your writing out of a
training set while staying quotable in ChatGPT Search is a perfectly coherent position, and it
is one robots.txt can express precisely — if you know which name does which job.</p>

<h2>What we found in published robots.txt files</h2>

<p>We read {F.directives_hosts():,} robots.txt files. Of those,
{F.directives_ai_sites():,} name an AI crawler at all, and
{F.directives_blocks_any():,} block at least one. So far so unsurprising. The number worth
sitting with is this one:</p>

<p><strong>{F.directives_training_only():,} of those sites —
{F.directives_training_only_pct():g}% — block only training crawlers</strong>, which is the
decision described above, made deliberately and correctly. The rest did something broader.
Among sites that block <code>OAI-SearchBot</code> and therefore leave ChatGPT Search,
{F.oai_overlap_pct():g}% also block <code>GPTBot</code>.</p>

<p>That overlap is the tell. It is consistent with one decision — "block OpenAI" — applied to
every OpenAI user-agent at once, rather than two decisions taken separately. We cannot prove
intent from a file and we are not going to try: what the number shows is that the two blocks
travel together almost always, and one of them has a cost the other does not.</p>

<p>One caveat that applies to every figure here. These are measurements of
<strong>access</strong> — what a file permits — and nothing downstream. We did not measure
citations, traffic or revenue, and no figure on this page should be read as measuring them.</p>

<h2>The {F.ai_agents_word()} crawlers, and what each block costs</h2>

<table>
<thead><tr><th>User-agent</th><th>Operator</th><th>Job</th><th>What blocking it does</th></tr></thead>
<tbody>
{_rows_html()}
</tbody>
</table>

<p>The impact column is the engine's own wording, printed here from the same table the checks
read, so a crawler added to Docket appears here without anyone editing this page.</p>

<h2>Writing the rules</h2>

<p>Directives are matched against the user-agent string, and the names are exact. A rule for
<code>GPTBot</code> says nothing about <code>OAI-SearchBot</code>, because as far as robots.txt
is concerned they are unrelated crawlers that happen to share an owner.</p>

<p>To stay out of training while staying quotable, name the training crawlers and leave the
search ones alone:</p>

<pre><code>User-agent: GPTBot
Disallow: /

User-agent: Google-Extended
Disallow: /</code></pre>

<p>Two mistakes are worth naming because they are silent. The first is a blanket
<code>User-agent: *</code> block added for some unrelated reason, which catches every crawler in
the table above including the {len(search)} that decide whether you can be cited. The second is
blocking at the CDN or firewall instead of in robots.txt: an edge rule that returns 403 to an AI
crawler is invisible in your robots.txt file, so every tool that reads the file — including the
robots half of Docket — will tell you the crawler is allowed. Docket checks both, and reports
them separately, because a file that says yes and a server that says no is a configuration
nobody chose on purpose.</p>

<h2>What robots.txt cannot do</h2>

<p>It is a request, not a control. It is also the only mechanism these operators document. You
will find advice recommending <code>noai</code> or <code>noimageai</code> meta tags: none of the
operators in the table above documents support for them, so this page does not tell you they
work. If you need a guarantee rather than a request, the honest answer is authentication, not a
directive.</p>

<p>And robots.txt says nothing about whether an assistant can make sense of your page once it
arrives. Most AI crawlers do not run JavaScript, so a page whose content is assembled in the
browser is effectively blank to them even when every rule permits it —
<a href="/learn/ai-search-visibility/">AI search visibility</a> covers the rest of that.</p>

<p><a class="btn" href="/download/">Download Docket</a></p>
"""
    return render(
        cat="learn", slug="ai-crawler-directives",
        title="AI crawler directives: which to block, which to keep",
        desc=(f"Docket checks {F.ai_agents_word()} AI crawlers from "
              f"{F.ai_agent_operators()} companies. Blocking a training bot and blocking a "
              f"search bot are different decisions with different costs."),
        h1="AI crawler directives: which to block, which to keep",
        crumb='<a href="/">Docket</a> / <a href="/learn/">Learn</a> / AI crawler directives',
        body=body,
        faq=[
            ("How many AI crawlers are there?",
             f"Docket checks {F.ai_agents_word()} by name, operated by "
             f"{F.ai_agent_operators()} companies, and the list changes: OpenAI split "
             "OAI-SearchBot out of GPTBot after launch and Anthropic retired Claude-Web. "
             "The number on this page is read from the product's own table rather than "
             "typed, so it cannot drift away from what Docket actually checks."),
            ("Should I block AI crawlers from my website?",
             "It depends which one, and that is the point. Blocking a training crawler keeps "
             "your writing out of a model and costs you no visibility. Blocking a "
             "search-index crawler removes you from the answers that cite live sources. "
             "Many sites make the second decision while intending only the first."),
            ("Does blocking GPTBot stop ChatGPT citing my site?",
             "No. GPTBot collects training data; OAI-SearchBot builds the index ChatGPT "
             "Search answers from. They are separate user-agents and a robots.txt rule for "
             "one says nothing about the other. In the robots.txt files we read, the two "
             f"blocks travel together {F.oai_overlap_pct():g}% of the time."),
            ("Do noai and noimageai meta tags work?",
             "None of the crawler operators in Docket's table documents support for them, so "
             "this page does not tell you they work. robots.txt is the mechanism these "
             "operators publish rules for. A request is all any of them is."),
            ("Why does Docket say a crawler is blocked when my robots.txt allows it?",
             "Because a CDN or firewall rule can return 403 to that crawler regardless of "
             "what the file says, and the file cannot see it. Docket tests access at the "
             "edge as well as reading the rules, and reports the two separately — a file "
             "that says yes and a server that says no is rarely a configuration anyone "
             "chose deliberately."),
        ],
    )


BUILDERS = [ai_directives]


def build_all() -> list:
    return [b() for b in BUILDERS]
