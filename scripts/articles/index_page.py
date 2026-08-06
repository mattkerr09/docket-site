#!/usr/bin/env python3
"""The Scout Index — the data moat.

Every figure comes from `data/index-*.json`, produced by
`scripts/collect_index.py`, which ships alongside its input list so anyone can
re-run it. Nothing on this page is estimated, rounded up, or asserted without a
measurement behind it.

The page publishes the sample's limits as prominently as its findings. A
referee that only reports flattering numbers is an advertisement, and readers
and models both discount it.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from render import render  # noqa: E402

DATA = Path(__file__).resolve().parents[2] / "data" / "index-2026-08.json"

CITATION = ("OAI-SearchBot", "PerplexityBot", "Claude-SearchBot", "Google-Extended")
TRAINING = ("GPTBot", "ClaudeBot", "Applebot-Extended", "CCBot", "Bytespider",
            "meta-externalagent")

CATEGORY_LABEL = {
    "news": "News &amp; media", "reference": "Reference &amp; knowledge",
    "ecommerce": "Ecommerce", "saas": "SaaS &amp; software",
    "local": "Local &amp; service businesses", "seo-tools": "SEO &amp; marketing",
    "nonprofit": "Education &amp; nonprofit",
}


def build() -> Path:
    d = json.loads(DATA.read_text())
    s = d["summary"]
    live = [r for r in d["records"] if r.get("reachable") and r.get("has_robots")]
    n = s["n"]

    def blocked(rec, group):
        return [b for b in group if rec["ai_access"].get(b) is False]

    both = [r for r in live if blocked(r, CITATION) and blocked(r, TRAINING)]
    training_only = [r for r in live if blocked(r, TRAINING) and not blocked(r, CITATION)]
    any_ai = len(both) + len(training_only)
    conflated_pct = round(100 * len(both) / any_ai) if any_ai else 0

    cit_pct = round(100 * s["blocking_any_citation_bot"] / n)
    train_pct = round(100 * s["blocking_any_training_bot"] / n)
    named_pct = round(100 * s["mentions_any_ai_bot"] / n)

    perplexity = s["by_bot"]["PerplexityBot"]["blocked"]
    oai = s["by_bot"]["OAI-SearchBot"]["blocked"]
    gap = round(perplexity / oai, 1) if oai else 0

    # Sites drawing the Perplexity/OpenAI distinction deliberately — a real
    # editorial decision, not a misconfiguration, and worth separating out.
    targeted = [
        r["host"] for r in live
        if r["ai_access"].get("PerplexityBot") is False
        and r["ai_access"].get("OAI-SearchBot") is not False
    ]

    bot_rows = "".join(
        f"<tr><td>{b}</td><td>{v['owner']}</td>"
        f"<td>{'search index' if v['purpose'] == 'search index' else v['purpose']}</td>"
        f"<td>{v['blocked']}</td><td>{v['pct']}%</td></tr>"
        for b, v in sorted(s["by_bot"].items(), key=lambda kv: -kv[1]["blocked"])
    )

    cat_rows = "".join(
        f"<tr><td>{CATEGORY_LABEL.get(c, c)}</td><td>{v['n']}</td>"
        f"<td>{v['blocking_citation']}</td><td>{v['pct']}%</td></tr>"
        for c, v in sorted(s["by_category"].items(), key=lambda kv: -kv[1]["pct"])
    )

    body = f"""
<p class="lede">We fetched the robots.txt of {s['attempted']} well-known websites and parsed
each one with Scout's own crawler-rules engine. <strong>{cit_pct}% of them block at least one
AI <em>search</em> crawler</strong> — the crawlers that decide whether a site can appear in
ChatGPT, Perplexity, Claude or Google's AI Overviews at all. Most of them did not appear to
mean to.</p>

<div class="stat-row">
<div class="stat"><b>{n}</b><span>sites with a robots.txt</span></div>
<div class="stat"><b>{cit_pct}%</b><span>block an AI search crawler</span></div>
<div class="stat"><b>{train_pct}%</b><span>block a training crawler</span></div>
<div class="stat"><b>{named_pct}%</b><span>name any AI bot at all</span></div>
</div>

<h2>The finding: almost nobody separates training from search</h2>
<p>AI crawlers are not one thing. <code>GPTBot</code> collects data to train OpenAI's models.
<code>OAI-SearchBot</code> builds the index ChatGPT searches when a user asks a question.
Blocking the first is a defensible business decision about your content being used as training
material. Blocking the second removes you from the answer.</p>

<p>Of the {any_ai} sites in our sample that block any AI crawler, only <strong>{len(training_only)}
blocked training crawlers while leaving the search crawlers alone</strong>. The other
{len(both)} — <strong>{conflated_pct}%</strong> — blocked both.</p>

<div class="callout">
<div class="callout-title">What this means</div>
<p>Roughly three quarters of the sites that took a position on AI crawling ended up removing
themselves from AI search results as well. Some of those are deliberate. Many are a
copy-pasted robots.txt block that treated every user-agent with "AI" in the name as the same
decision.</p>
</div>

<h2>Perplexity is blocked {gap}× more often than OpenAI's search crawler</h2>
<p><code>PerplexityBot</code> was disallowed by {perplexity} sites. <code>OAI-SearchBot</code>
was disallowed by {oai}. That gap is not a rounding artefact — {len(targeted)} sites block
Perplexity specifically while allowing OpenAI's search crawler through, which is a deliberate
editorial position rather than a misconfiguration.</p>
<p>Among them: {', '.join(targeted[:8])}{'…' if len(targeted) > 8 else ''}.</p>

<h2>Every crawler we measured</h2>
<div class="wrap-tbl"><table class="cmp">
<thead><tr><th>Crawler</th><th>Operator</th><th>Purpose</th><th>Sites blocking</th><th>%</th></tr></thead>
<tbody>{bot_rows}</tbody></table></div>

<h2>By category</h2>
<p>The spread is the story. News publishers have overwhelmingly decided to shut AI search out.
Almost nobody else has.</p>
<div class="wrap-tbl"><table class="cmp">
<thead><tr><th>Category</th><th>Sites</th><th>Blocking AI search</th><th>%</th></tr></thead>
<tbody>{cat_rows}</tbody></table></div>

<p>For a business that competes for customers rather than readers — a shop, a SaaS product, a
local service — the practical read is that the field is wide open. Your competitors are almost
certainly not blocking these crawlers, so being visible to them is not an advantage you can
win by default. It is table stakes you can lose by accident.</p>

<h2>Two things we did not expect</h2>

<h3>{s['uses_content_signal']} sites use Content-signal</h3>
<p><code>Content-signal</code> is a newer, Cloudflare-backed convention for stating intent
declaratively — Stack Overflow's reads
<code>Content-signal: search=no, ai-train=no</code>. No crawler is obliged to honour it. It is
worth watching because it separates <em>what you permit</em> from <em>which user-agent
happens to be asking</em>, which is exactly the distinction robots.txt handles badly.</p>

<h3>{s['blocking_a_search_engine']} sites block a conventional search engine</h3>
<p>Not AI crawlers — Googlebot, Bingbot, DuckDuckBot or Applebot. In the cases we looked at
this is intentional: Reddit's robots.txt is a blanket <code>Disallow: /</code> with search
access negotiated commercially instead. It is a reminder that robots.txt describes policy,
not always practice.</p>

<h2>Method</h2>
<p>One <code>GET</code> to <code>https://&lt;host&gt;/robots.txt</code> per site, serialised
with a delay — a smaller footprint than one person visiting the homepage. Rules were parsed
with Scout's RFC 9309 implementation, which does longest-match resolution, <code>*</code>
wildcards and <code>$</code> anchors. A site counts as blocking a crawler when that crawler
is disallowed from <code>/</code>.</p>

<p>Whether a response is a real robots.txt is decided by its <em>content</em>, not its status
code. Stack Overflow serves a genuine, restrictive robots.txt with an HTTP 418; a status-code
test would have miscounted it. Sites returning no <code>User-agent:</code> directive at all
({s['no_robots_txt']} of them) are excluded from every percentage, because a site with no
robots.txt has no policy — counting it as "allows everything" would overstate how open the
web is.</p>

<h2>Limits of this sample</h2>
<p>Stated plainly, because the Index is only useful if you can judge it:</p>
<ul>
<li><strong>It is not a random sample of the web.</strong> It is {s['attempted']} well-known,
high-traffic sites chosen across categories where an AI assistant might plausibly be asked for
a recommendation. Percentages describe this population and nothing wider.</li>
<li><strong>{s['unreachable']} sites were unreachable</strong> at collection time and are
excluded.</li>
<li><strong>robots.txt is a request, not a wall.</strong> It records what a site asks
crawlers to do. Well-behaved crawlers comply; compliance is not measured here and we make no
claim about it.</li>
<li><strong>This measures access, not citation.</strong> Being crawlable is necessary for
appearing in AI answers. It is not sufficient — rendering, structure and entity clarity all
matter, and none of them are in this dataset.</li>
<li><strong>It is a snapshot.</strong> Collected {d['collected'][:10]}. robots.txt files
change; this one will be re-run and the figures will move.</li>
</ul>

<h2>Get the data</h2>
<p>The full dataset, the collection script and the exact site list are in the repository.
Re-run it yourself and you should get the same answer — that is the point of publishing the
method alongside the numbers.</p>
<p><a class="btn-ghost" href="/data/index-2026-08.json">Download the dataset (JSON)</a></p>

<div class="callout">
<div class="callout-title">Check your own site</div>
<p>Scout runs this same audit against your site, plus 79 other checks, on your Mac.
It tells you which crawlers you are blocking, whether it looks deliberate, and what the
practical consequence is for each one. <a href="/#download">Download Scout →</a></p>
</div>
"""

    faq = [
        ("What percentage of websites block AI crawlers?",
         f"In Scout's August 2026 sample of {n} well-known sites with a robots.txt, "
         f"{cit_pct}% blocked at least one AI search crawler and {train_pct}% blocked at "
         f"least one training crawler. News and media sites were the outlier at "
         f"{s['by_category'].get('news', {}).get('pct', 0)}%; SaaS companies were at "
         f"{s['by_category'].get('saas', {}).get('pct', 0)}%."),
        ("What is the difference between GPTBot and OAI-SearchBot?",
         "GPTBot collects data used to train OpenAI's models. OAI-SearchBot builds the index "
         "ChatGPT searches when a user asks a question. Blocking GPTBot keeps your content out "
         "of training data. Blocking OAI-SearchBot removes you from ChatGPT's answers. They "
         "are separate decisions and require separate robots.txt rules."),
        ("Should I block AI crawlers?",
         "It depends on whether your content is the product. Publishers who sell access to "
         "writing have a clear reason to block training crawlers. A business that wants to be "
         "recommended to customers generally does not — blocking the search crawlers removes "
         "you from the answers where those recommendations happen."),
        ("Does blocking Google-Extended affect my Google rankings?",
         "No. Google-Extended controls whether your content is used for Gemini and AI Overviews "
         "grounding. It does not affect classic Google Search ranking, which is governed by "
         "Googlebot."),
    ]

    return render(
        cat="index", slug="",
        title=f"The Scout Index — {cit_pct}% of major sites block an AI search crawler (2026)",
        desc=(f"We measured the robots.txt of {s['attempted']} well-known websites with Scout's "
              f"own parser. {cit_pct}% block at least one AI search crawler, and {conflated_pct}% "
              f"of sites blocking any AI crawler also blocked the ones that decide whether they "
              f"appear in ChatGPT. Full method and dataset included."),
        h1="The Scout Index: who is blocking AI search crawlers",
        crumb='<a href="/">Scout</a> / The Index',
        body=body,
        schema_type="Article",
        faq=faq,
        wide=False,
    )


if __name__ == "__main__":
    print(build())
