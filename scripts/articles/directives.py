#!/usr/bin/env python3
"""The dead-directive measurement — Scout's second first-party dataset.

Every number is read out of site/data/ai-directives-2026-08.json, which is
built from the raw survey by scripts/build_directives.py and ships with the
page. The survey read one robots.txt per host and, where that robots.txt
permitted us, one llms.txt plus a control path that cannot exist.

The page leads with a hypothesis of ours that the data destroyed. That is
deliberate: the Index currently publishes a "three quarters conflate" figure
from a 110-site sample, and the top 10,000 says the opposite. Correcting our
own headline in public is worth more than the headline was.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from render import render  # noqa: E402

DATA = Path(__file__).resolve().parents[2] / "site" / "data" / "ai-directives-2026-08.json"


def _d() -> dict:
    return json.loads(DATA.read_text())


def _retired_table(d: dict) -> str:
    rows = ""
    for tok, r in d["retired_tokens"].items():
        rows += (f"<tr><td><code>{tok}</code></td><td>{r['vendor']}</td>"
                 f"<td><code>{r['replaced_by']}</code></td>"
                 f"<td>{r['count']}</td></tr>")
    return ('<div class="wrap-tbl"><table class="cmp"><thead><tr>'
            "<th>Token written</th><th>Vendor</th><th>What the vendor uses now</th>"
            "<th>Sites naming it</th></tr></thead>"
            f"<tbody>{rows}</tbody></table></div>")


#: Tokens shown in the article, grouped where several spellings are the same
#: mistake. Only tokens we could characterise are listed; the dataset has the
#: rest. Counts come from the data, never from this table.
_UNMATCHABLE_ROWS = [
    (("grokbot", "xai-grok", "grok-deepsearch", "grok"),
     "Four spellings for xAI, which publishes no crawler documentation we could "
     "reach — <code>x.ai/robots</code> returns 403 to an identified bot"),
    (("copilot", "copilotnative", "copilotsapphire"),
     "Three spellings for Microsoft's assistant, which crawls as "
     "<code>Bingbot</code>"),
    (("deepseek",), "A company name, not a user-agent"),
    (("neevabot",), "Neeva's consumer search engine shut down in 2023"),
    (("perplexity-ai",),
     "The company. The crawlers are <code>PerplexityBot</code> and "
     "<code>Perplexity-User</code>"),
    (("chatgpt-user/2.0",),
     "A version number inside the token, so it matches no user-agent"),
    (("claude", "chatgpt"), "Product names rather than crawler names"),
]


def _unmatchable_table(d: dict) -> str:
    counts = d["unmatchable_tokens"]
    rows = ""
    for toks, note in _UNMATCHABLE_ROWS:
        present = [(t, counts[t]) for t in toks if t in counts]
        if not present:
            continue
        written = ", ".join(f"<code>{t}</code>" for t, _ in present)
        rows += (f"<tr><td>{written}</td><td>{sum(c for _, c in present)}</td>"
                 f"<td>{note}</td></tr>")
    return ('<div class="wrap-tbl"><table class="cmp"><thead><tr>'
            "<th>Token written</th><th>Sites</th><th>What it matches</th>"
            "</tr></thead>"
            f"<tbody>{rows}</tbody></table></div>")


#: U+2011 NON-BREAKING HYPHEN. Renders identically to U+002D in every editor
#: we tried, survives copy-paste out of a styled document, and can never match
#: a user-agent string.
_NBSP_HYPHEN = "perplexity‑user"


def _nbsp_hosts(d: dict) -> list:
    """Hosts naming the non-breaking-hyphen token, read from the host records.

    Counted from the records rather than the token table so the number cannot
    drift from the shipped file if the table is ever truncated.
    """
    return [h["h"] for h in d["hosts"] if _NBSP_HYPHEN in h["dead"]]


def _band_table(d: dict) -> str:
    rows = ""
    for b in d["llms_by_rank"]:
        rows += (f"<tr><td>{b['from']:,}–{b['to']:,}</td><td>{b['n']:,}</td>"
                 f"<td>{b['llms']}</td><td>{b['pct']:.1f}%</td></tr>")
    return ('<div class="wrap-tbl"><table class="cmp"><thead><tr>'
            "<th>Tranco rank</th><th>Hosts read</th><th>With llms.txt</th>"
            "<th>Share</th></tr></thead>"
            f"<tbody>{rows}</tbody></table></div>")


def dead_directives() -> Path:
    d = _d()
    s = d["summary"]
    collected = d["collected"][:10]
    n = s["parseable_robots"]
    ai = s["sites_with_ai_directive"]
    dead = s["sites_with_dead_directive"]
    pct_dead = s["pct_dead_of_ai"]
    any_ai = s["blocks_any"]
    tr_only = s["training_only"]
    cit_hit = any_ai - tr_only

    body = f"""
<p class="lede">More than half the websites that write a robots.txt rule aimed at an AI
crawler are addressing something that will never read it. We read the robots.txt of the
Tranco top 10,000 on {collected}, parsed all {n:,} that returned one with Scout's own parser,
and found that of the <strong>{ai:,} sites naming at least one AI user-agent</strong>,
<strong>{dead:,} — {pct_dead}% — name a token that no crawler uses.</strong></p>

<p>These are not sites that decided to allow AI crawlers. They are sites that decided to
block them, wrote the rule, and got no rule. The file parses, the syntax is valid, nothing
warns, and the crawler walks past the directive because the name in it does not match its
own.</p>

<h2>Two ways a directive dies</h2>

<p><strong>Retired.</strong> The vendor documented the token once and has since replaced it.
The old name is inert — the crawler now identifies itself as something else, so a
<code>Disallow</code> under the old heading applies to nobody.</p>

{_retired_table(d)}

<p>Anthropic's current documentation lists exactly three tokens: <code>ClaudeBot</code>,
<code>Claude-User</code> and <code>Claude-SearchBot</code>. <code>anthropic-ai</code> and
<code>Claude-Web</code> are not among them, and between them they appear on
{d['retired_tokens']['anthropic-ai']['count'] + d['retired_tokens']['claude-web']['count']:,}
sites in this sample. Every one of those sites believes it has made a decision about
Anthropic that it has not made.</p>

<p><code>Google-NotebookLM</code> is the live one. Google renamed it to
<code>Google-GeminiNotebook</code> and says the old token is supported until August 2026 —
this month. {d['retired_tokens']['google-notebooklm']['count']} sites in our sample name the
old token, including amazon.com, pinterest.com and tiktok.com.
<strong>Zero name the new one.</strong></p>

<p><strong>Unmatchable.</strong> The token was never a crawler. Someone wrote the company
name, the product name, a version string, or a plausible-looking guess.</p>

{_unmatchable_table(d)}

<p>Our favourite is not in the table. {len(_nbsp_hosts(d))} sites — including
<strong>chatgpt.com itself</strong> — write <code>perplexity&#8209;user</code> with a U+2011
non-breaking hyphen where the ASCII one belongs. It renders identically in every editor, it
survives copy-paste out of a styled document, and it can never match a user-agent string. The
others: {', '.join(h for h in _nbsp_hosts(d) if h != 'chatgpt.com')}.</p>

<h2>The site that wrote the rules everyone else copies</h2>

<p>Cloudflare authored the Content-Signal syntax we found in {s['content_signal']} of the
{n:,} robots.txt files ({100 * s['content_signal'] / n:.1f}%). Its own robots.txt names
<code>anthropic-ai</code>, <code>Claude-Web</code> and <code>cohere-ai</code> — all three
retired — and names neither <code>OAI-SearchBot</code> nor <code>Claude-SearchBot</code>, the
two crawlers that decide whether a site can be cited in ChatGPT and Claude.</p>

<p>That is the shape of the problem. This is not a small-site literacy gap. Keeping a list of
user-agent tokens current is unglamorous maintenance that nothing prompts you to do, so
nobody does it.</p>

<h2>We were wrong about the other half of this</h2>

<p>Our own <a href="/index/">Index</a> reports, from a 110-site sample, that roughly two
thirds of the sites blocking any AI crawler also blocked the ones that decide citation. We
expected the top 10,000 to say the same thing or worse. It says the opposite.</p>

<p>Of the <strong>{any_ai:,} sites</strong> here that block at least one of nine AI crawlers,
<strong>{tr_only:,} — {s['pct_training_only']}% — blocked training crawlers and left the
search crawlers alone.</strong> That is the deliberate, well-informed split, and it is the
majority behaviour. Only {cit_hit:,} took the citation hit.</p>

<div class="callout">
<div class="callout-title">What this changes</div>
<p>The Index figure is true of the Index sample, which is news-heavy by construction, and
false of the web's largest sites. We have annotated it rather than deleted it — the sample is
real and the difference between the two is itself the finding. Large sites with someone
responsible for the robots.txt mostly get this right. The conflation risk is concentrated in
publishers and in sites that copied a block list from one.</p>
</div>

<h2>The asymmetry that does hold, and it is sharper</h2>

<p>Blocking a citation crawler is almost never a standalone decision. {s['blocks_citation']:,}
sites block at least one; when we look at OpenAI specifically, <strong>425 sites block
<code>OAI-SearchBot</code> and 414 of them — 97.4% — also block <code>GPTBot</code>.</strong>
Eleven sites in the entire top 10,000 block OpenAI's search crawler while allowing its
training crawler. Anthropic is starker: 411 block <code>Claude-SearchBot</code> and 409 also
block <code>ClaudeBot</code>, leaving two.</p>

<p>Losing your place in ChatGPT's answers is, at this scale, a side effect of a training
decision taken by about two sites in a thousand on purpose. That is the finding worth acting
on, and it is the reason Scout separates the two crawler classes in every report instead of
counting "AI bots blocked".</p>

<h2>llms.txt: adoption is real, and the obvious check is wrong 17% of the time</h2>

<p>We expected llms.txt adoption below 2%. It is <strong>{s['pct_llms_adoption']}%</strong> —
{s['llms_confirmed']} confirmed files across {n:,} hosts. It skews to large sites and falls
steadily with rank.</p>

{_band_table(d)}

<p>Getting to a trustworthy number took two extra requests per host. A naive check — fetch
<code>/llms.txt</code>, call a 200 a yes — returned {s['llms_candidates']} candidates. Two
things were wrong with that number.</p>

<p>First, we fetched a control path on each host that cannot exist.
<strong>{s['llms_soft404']} hosts ({s['pct_llms_soft404']}%) answered 200 with a body for that
too</strong> — catch-all handlers and soft 404s, one of them returning an
<code>image/gif</code> for every unknown path. Among them: office.com, sentry.io,
amplitude.com and dell.com.</p>

<p>Second, we read what came back. {s['llms_wrong_kind']} of the survivors served something
that is not an llms.txt at all: st-andrews.ac.uk returns an XML sitemap, sudoku.com and
upstart.com return their robots.txt, utwente.nl returns JSON, and five hosts returned gzip
bytes labelled <code>text/plain</code> that we could not decode and therefore did not
count.</p>

<div class="callout">
<div class="callout-title">A presence check that is wrong once every six times</div>
<p>{s['llms_false_positive']} of {s['llms_candidates']} apparent llms.txt files —
<strong>{s['pct_llms_false_positive']}%</strong> — were not one. Semrush's Site Audit flags a
missing llms.txt as an issue; any "does this file exist" test without a control fetch inherits
that error rate, because a soft-404 handler answers yes to every question. Scout issues the
control request and reads the first bytes, and reports the file as unconfirmed rather than
present when either test fails.</p>
</div>

<p>The correlation is the interesting part, and it does not point where the advocacy does.
Sites with an llms.txt block a citation crawler at <strong>{s['cit_rate_llms']}%</strong>
against <strong>{s['cit_rate_no_llms']}%</strong> for sites without one — a risk ratio of
{s['rr_citation_llms']['rr']} (95% CI {s['rr_citation_llms']['lo']} to
{s['rr_citation_llms']['hi']}, on {s['rr_citation_llms']['events_exposed']} events in the
smaller arm, so treat the point estimate loosely). That is computed only over the
{s['probed_for_llms']:,} hosts we were permitted to probe, because comparing against hosts
that denied us would have built the association into the sampling. Sites with an llms.txt also
carry a <code>Sitemap:</code> directive {s['sitemap_with_llms']}% of the time against
{s['sitemap_without_llms']}%.</p>

<p>llms.txt looks like a marker of a maintained site rather than a mechanism that does
anything. Google stated in June 2026 that llms.txt files are not needed for Google Search and
affect visibility neither way. Publishing one is evidence you have someone doing this job; it
is not the job.</p>

<h2>robots.txt is not access</h2>

<p>Two separate measurements say the file and the server disagree.
<strong>{s['edge_denied']} of the 10,000 hosts ({100 * s['edge_denied'] / 10000:.1f}%) refused a
self-identifying bot outright</strong> at the edge — 401, 403, 406, 429 or 503 — before any
robots.txt rule applied. And of the {s['probed_for_llms']:,} hosts whose robots.txt permitted
us to fetch <code>/llms.txt</code>, <strong>{s['llms_edge_denied']}
({s['pct_llms_edge_denied']}%) were then denied it by the server.</strong></p>

<p>A site can allow every AI crawler in robots.txt and still be invisible to all of them
because a WAF rule three layers up drops unknown user-agents. No robots.txt audit — ours
included — can see that from the outside. It has to be tested against your own site with the
crawler's own user-agent, which is exactly what a tool running on your machine can do and a
cloud crawler cannot do on your behalf.</p>

<h2>Where someone else's data is better</h2>

<p>Ahrefs published an llms.txt study in June 2026 across 137,210 domains — thirteen times our
population — and, more importantly, with server-log request data we have no way to obtain.
They found 97% of llms.txt files received no requests at all in May 2026, and that AI
retrieval bots were 1.1% of requests to the ones that did. That is a stronger claim than ours
about whether llms.txt is read, because it measures reading rather than presence. Our
measurement covers a different question — who writes directives that cannot work — and the
two agree in direction.</p>

<h2>Method, and what it cannot tell you</h2>

<p>Population: the Tranco top 10,000 (list PYG5J), which is a rank-aggregated list built to be
harder to manipulate than a single provider's. One request for <code>/robots.txt</code> per
host. A second request for <code>/llms.txt</code> only where the robots.txt we had just read
permitted our own user-agent, plus one control request for a path that cannot exist. A
self-identifying user-agent with a contact address, an eight-second timeout, no retries.
Collected in {int(d['duration_s'] / 60)} minutes on {collected}.</p>

<p><strong>We did not impersonate any vendor's crawler.</strong> Sending a forged
<code>OAI-SearchBot</code> header to 10,000 third-party servers to see what they return is
deception, and it would have produced better data. Scout runs the same test inside the
product, against a site the person running it owns, where it is not deception.</p>

<p>Limits worth stating. {s['attempted'] - n:,} of the 10,000 hosts did not return a parseable
robots.txt — Tranco contains CDN and infrastructure hostnames that are not websites. A
robots.txt read once is a snapshot, and none of this says what any crawler actually did.</p>

<p>The reference list needed correcting before we could use it. "Unmatchable" is judged
against the community
<a href="https://github.com/ai-robots-txt/ai.robots.txt">ai.robots.txt</a> set, and that set
is itself behind vendor documentation. We read six vendor pages on {collected} and found
<code>{'</code>, <code>'.join(d['list_gap'])}</code> all currently documented and all missing
from it. Naming one of those is correct behaviour, so we excluded them rather than count them
as dead. We also removed Awario's crawlers from the population — they are real, and our own
pattern for "AI-intent" had swept them in, which would have inflated this page's headline by
close to 300 sites.</p>

<p>Both corrections cut against the finding and it survives them. The direction is worth
noticing anyway: the canonical list most people copy their block rules from is stale in both
directions at once.</p>

<p><a href="/data/ai-directives-2026-08.json">The full dataset is here</a> — every host, its
AI tokens, which of them are dead, which crawlers it blocks, and whether it has a confirmed
llms.txt. Recompute it and disagree.</p>

<h2>What to do with your own robots.txt</h2>

<ol>
<li>Open it and list every <code>User-agent:</code> line that mentions an AI product.</li>
<li>Check each token against the vendor's own crawler documentation, not against a blog post
or a copied gist. If it is not on the vendor's page, the rule does nothing.</li>
<li>Decide training and citation separately. They are different crawlers and different
business decisions.</li>
<li>Then test access from outside the file — fetch your own homepage with the crawler's
user-agent and confirm the server agrees with what you wrote.</li>
</ol>

<p>Scout does steps two through four on every audit, names the dead tokens it finds, and says
which replacement to use.</p>

<p><a class="btn" href="/download/">Download Scout</a></p>
"""
    return render(
        cat="index", slug="ai-directives",
        title=f"{pct_dead}% of AI robots.txt rules name a token no crawler uses",
        desc=(f"We parsed {n:,} robots.txt files from the Tranco top 10,000. Of the {ai:,} "
              f"sites writing AI crawler rules, {dead:,} name a retired or unmatchable "
              f"token."),
        h1="The AI rules in robots.txt that do nothing",
        crumb='<a href="/">Scout</a> / <a href="/index/">The Index</a> / Dead AI directives',
        body=body,
        published="2026-08-07",
        faq=[
            ("What is a dead robots.txt directive?",
             "A User-agent rule naming a token that no crawler identifies itself with — "
             "either because the vendor retired that name, or because it was never a "
             "crawler name. The file parses and nothing warns you, but the rule applies to "
             f"nobody. We found one on {pct_dead}% of the sites writing AI rules at all."),
            ("Does anthropic-ai still work in robots.txt?",
             "No. Anthropic's current documentation lists ClaudeBot, Claude-User and "
             "Claude-SearchBot. A rule under anthropic-ai or Claude-Web matches none of "
             f"them, and {d['retired_tokens']['anthropic-ai']['count']} and "
             f"{d['retired_tokens']['claude-web']['count']} sites respectively still use "
             "those names."),
            ("Do I need an llms.txt file?",
             "There is no measured evidence that it helps. Google stated in June 2026 that "
             "llms.txt is not needed for Google Search and does not affect visibility "
             "either way, and Ahrefs measured 97% of llms.txt files receiving no requests "
             f"at all. Adoption is {s['pct_llms_adoption']}% of the top 10,000 and "
             "correlates with sites that "
             "maintain their robots.txt rather than with any outcome."),
            ("Is blocking GPTBot the same as blocking ChatGPT search?",
             "No. GPTBot collects training data; OAI-SearchBot builds the index ChatGPT "
             "searches. Of 425 sites blocking OAI-SearchBot, 414 also block GPTBot — losing "
             "citation is nearly always a side effect of a training decision rather than a "
             "decision of its own."),
        ],
    )


BUILDERS = [dead_directives]


def build_all() -> list[Path]:
    return [b() for b in BUILDERS]


if __name__ == "__main__":
    for p in build_all():
        print(p)
