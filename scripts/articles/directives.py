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
    (("claude", "chatgpt"), "Product names rather than crawler names"),
]

#: Tokens that break on the parser rather than on the vendor's name — a
#: character RFC 9309 does not allow in a product token, so the value is cut
#: short and the group addresses whatever survives.
_TRUNCATED_ROWS = [
    ("img2dataset", "the digit stops it"),
    ("chatgpt agent", "the space stops it"),
    ("bigsur.ai", "the dot stops it"),
    ("mistral.ai", "the dot stops it"),
    ("perplexity\u2011user", "a U+2011 non-breaking hyphen stops it"),
]


def _truncated_table(d: dict) -> str:
    tr = d["truncated_tokens"]
    rows = ""
    for tok, note in _TRUNCATED_ROWS:
        e = tr.get(tok)
        if not e:
            continue
        rows += (f"<tr><td><code>{tok}</code></td><td>{e['count']}</td>"
                 f"<td><code>{e['kept']}</code></td><td>{note}</td></tr>")
    return ('<div class="wrap-tbl"><table class="cmp"><thead><tr>'
            "<th>Written</th><th>Sites</th><th>Read as</th><th>Why</th>"
            "</tr></thead>"
            f"<tbody>{rows}</tbody></table></div>")


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


def _token_sites(d: dict, token: str) -> int:
    """How many surveyed hosts name this token. Read from the host records."""
    return sum(1 for h in d["hosts"] if token in h["ai"])


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

<h2>Three ways a directive dies</h2>

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

<p><strong>Undocumented.</strong> The token appears on no vendor page and in no community
list. Someone wrote the company name, the product name, or a plausible-looking guess. We
report these separately and Scout's own check leaves them alone, because "nobody documents
it" is weaker evidence than "the vendor replaced it" — a token could be real and simply
undocumented where we looked.</p>

{_unmatchable_table(d)}

<p><strong>Cut short by the parser.</strong> The third way is the one we nearly published
backwards, and the correction is more useful than the section it replaced.</p>

<p>RFC 9309 is exact about what a crawler name may contain. Section 2.2.1: <em>"The product
token MUST contain only uppercase and lowercase letters ('a-z' and 'A-Z'), underscores ('_'),
and hyphens ('-')."</em> No digits, no dots, no spaces. So we wrote a rule that flagged any
token carrying one — which caught <code>ChatGPT-User/2.0</code>, written by 20 sites in this
sample, and called it dead.</p>

<p>It is not dead. We read Google's open-source robots.txt parser rather than reasoning
about it further, and <code>RobotsMatcher::ExtractUserAgent</code> answers the question in one
line:</p>

<pre><code>// Allowed characters in user-agent are [a-zA-Z_-].
while (absl::ascii_isalpha(*end) || *end == '-' || *end == '_') ++end;</code></pre>

<p>That runs against the value written in <em>your file</em>, not only against the crawler's
own string. <code>ChatGPT-User/2.0</code> is therefore cut to <code>ChatGPT-User</code> and
matches exactly what its author intended. Our rule would have told
<strong>89 sites in this sample that a working configuration was broken</strong> — the same
error the whole page is about, made by us, one step from shipping.</p>

<div class="callout">
<div class="callout-title">What the correction leaves</div>
<p>The truncation is real; the conclusion was wrong. A token is broken when the parser cuts it
and <em>what survives is not a crawler name</em>. That is a narrower rule, it is decidable
from two sources rather than one, and it is what Scout ships.</p>
</div>

{_truncated_table(d)}

<p><code>img2dataset</code> is the one worth staring at. It is in the community
<a href="https://github.com/ai-robots-txt/ai.robots.txt">ai.robots.txt</a> list that people
copy their block rules from, and it cannot work as written: the digit is not a legal product
token character, so the directive is read as <code>img</code>.
{_token_sites(d, 'img2dataset')} sites in this sample copied it, and
<code>bigsur.ai</code> — also on that list, also broken, this time by the dot — accounts for
another {_token_sites(d, 'bigsur.ai')}.</p>

<p>Our favourite is still {len(_nbsp_hosts(d))} sites — including
<strong>chatgpt.com itself</strong> — writing <code>perplexity&#8209;user</code> with a U+2011
non-breaking hyphen where the ASCII one belongs. It renders identically in every editor we
tried and survives copy-paste out of a styled document, so the rule reads as
<code>perplexity</code> and nobody can see why. The others:
{', '.join(h for h in _nbsp_hosts(d) if h != 'chatgpt.com')}.</p>

<p>One honest limit. Not every crawler runs Google's parser, and one doing naive substring
matching might behave differently. That is the point rather than a caveat: a rule whose
meaning depends on whose parser reads it is not a rule you can rely on.</p>

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
included — can see that from the outside. It has to be tested against the site itself, with
the crawler's own user-agent.</p>

<h3>nature.com, which gets this more right than almost anyone and still has a hole</h3>

<p>Nature's robots.txt blocks <code>GPTBot</code>, <code>PerplexityBot</code> and
<code>ClaudeBot</code>. We asked their server for the homepage as each of seven documented AI
crawlers on {collected} and compared the answers to an ordinary browser request, which
returned 200. All three of those crawlers got <strong>406</strong> — the file and the edge
agreeing, policy enforced twice, exactly as intended.</p>

<p>One did not fit. <code>Perplexity-User</code> — the agent that fetches a page when a person
asks Perplexity about it — is <strong>allowed in their robots.txt and refused 406 by their
server</strong>. Nothing in the file says so. It is not a robots.txt decision at all; it is a
rule in front of it, and the only way to find it is to ask.</p>

<p>We are naming Nature because they are among the most careful publishers we measured, not
because they are careless. If a site that separates training from citation correctly, in the
file, still has one crawler blocked somewhere they cannot see, the odds on a site that has
never thought about it are not good.</p>

<h3>What we did not measure, and why</h3>

<p>We could have run those seven probes against all 10,000 hosts and published a per-crawler
edge-blocking table. It would have been the most quotable thing on this page. We did not
collect it.</p>

<p>Sending an <code>OAI-SearchBot</code> user-agent to ten thousand strangers to see what
their servers do is unsolicited scanning, whatever the header says underneath. One request
inside an audit somebody asked for is a different act. So the survey figure above is
<strong>{s['edge_denied']} hosts refusing <em>our own</em> self-identifying bot</strong>, which
is what we were entitled to learn, and the per-crawler answer is something Scout works out
for one site at a time — the site in front of it.</p>

<p>That is check 89, <code>ai.edge_access</code>. It probes the audited origin only, appends
<code>Scout-SEO-Audit</code> to every vendor string so nobody's log shows a forged crawler,
and reports the contradictions rather than the refusals: a crawler your file blocks and your
server also blocks is your policy working twice, and saying so would train you to ignore the
check. On Nature it reports one finding, not four.</p>

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

<h2>The check this became</h2>

<p>Scout ships this as <code>ai.dead_crawler_directive</code>, and it flags a deliberately
smaller number than the {pct_dead}% at the top of this page.
<strong>{s['sites_provably_broken']} sites — {s['pct_provably_broken_of_ai']}% of everyone
writing an AI crawler rule</strong> — carry a token that is either vendor-retired with a
documented replacement, or cut short by the parser into something no crawler is called. Those
two we can prove. "Absent from the community list" we cannot, so the product does not say
it.</p>

<p>The same principle keeps <code>cohere-ai</code> out of the check entirely, on
{_token_sites(d, 'cohere-ai')} sites in this sample. Cohere plainly
retired it — nobody documents it — but we could not find a current Cohere crawler page saying
what replaced it, and telling {_token_sites(d, 'cohere-ai')} sites their rule is dead on an
assumption is the error this check exists to catch.</p>

<p>Severity follows the consequence rather than the tidiness. A dead heading above a
<code>Disallow</code> means a restriction you wrote is not in force, and the crawler is
reading what you meant to withhold. A dead heading above nothing but <code>Allow</code> costs
nothing and is reported as a note.</p>

<h2>What to do with your own robots.txt</h2>

<ol>
<li>Open it and list every <code>User-agent:</code> line that mentions an AI product.</li>
<li>Check each token against the vendor's own crawler documentation, not against a blog post
or a copied gist. If it is not on the vendor's page, the rule does nothing.</li>
<li>Look for anything that is not a letter, a hyphen or an underscore. A digit, a dot, a space
or an invisible character cuts the token short at that point.</li>
<li>Decide training and citation separately. They are different crawlers and different
business decisions.</li>
<li>Then test access from outside the file — fetch your own homepage with the crawler's
user-agent and confirm the server agrees with what you wrote.</li>
</ol>

<p>Scout does steps two through five on every audit, names the dead tokens it finds, and
prints the replacement rules to paste.</p>

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
