#!/usr/bin/env python3
"""/tools/ai-crawler-checker/: the free AI crawler checker.

Matthew, 2026-09-28: "look at the top performing pages for outlier and see
what we can use to help the other pages and other sites". Outlier's traffic
comes from plain questions about giant brands; Docket's version of that ends
in something a visitor can use without buying anything, which is this page.

HOW IT WORKS. The browser cannot read another site's robots.txt, so the form
asks our Worker (workers/ai-crawler-check/ in this repo, deployed from the Mac)
to fetch it and evaluate it with a port of Docket's own RFC 9309 parser. The
crawler list, owners, purposes and impacts are the engine's own table
(data/ai-agents.json, collected from seo_engine.robots.AI_USER_AGENTS), so the
free tool and the product cannot disagree about who is checked or what a block
costs. Two search crawlers are added here because the questions people ask
about AI Overviews and Copilot are answered by them, not by an AI token.

HONEST LIMITS are on the page, not in a footnote: it reads robots.txt and
nothing else. A CDN or firewall that refuses crawlers is invisible to it, and
the survey figure below says how often that happens.
"""
from __future__ import annotations

import html
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import facts as F  # noqa: E402
from render import (DATA, HAS_SAMPLE, N_CHECKS, PAY4, PRICE, PRICE_STR, SAMPLE_REPORT, price_req_html,  # noqa: E402
                    buy_block, checkout_url, render)

#: The Worker the form calls. `workers/ai-crawler-check/wrangler.toml` names it.
CHECKER_ENDPOINT = "https://ai-crawler-check.kerrco.workers.dev/check"
SURVEYED_HUMAN = "August 2026"

#: The two search crawlers that decide the AI-feature questions. Worded from
#: what this site already publishes: Google's AI features follow Googlebot
#: (the engine's Google-Extended entry, quoting Google), and Copilot crawls as
#: Bingbot (/index/ai-directives/).
SEARCH_CRAWLERS = {
    "Googlebot": {"owner": "Google", "purpose": "search index",
                  "impact": "Google Search, including AI Overviews and AI Mode, which follow "
                            "your Googlebot rules rather than any AI-specific token."},
    "Bingbot": {"owner": "Microsoft", "purpose": "search index",
                "impact": "Bing search. Microsoft's Copilot assistant crawls as Bingbot, so "
                          "this is the rule it reads."},
}

#: Purposes that decide whether an assistant can find and cite a page, as
#: opposed to learning from it.
CITATION_PURPOSES = {"search index", "live fetch", "grounding"}


def _crawlers() -> list[dict]:
    table = json.loads((DATA / "ai-agents.json").read_text())["agents"]
    rows = [{"name": k, **v} for k, v in {**SEARCH_CRAWLERS, **table}.items()]
    for r in rows:
        r["side"] = "cite" if r["purpose"] in CITATION_PURPOSES else "train"
    order = {"Google": 0, "Microsoft": 1, "OpenAI": 2, "Anthropic": 3, "Perplexity": 4}
    rows.sort(key=lambda r: (r["side"] != "cite", r["name"] not in SEARCH_CRAWLERS,
                             order.get(r["owner"], 9), r["owner"], r["name"].lower()))
    return rows


def _table(rows: list[dict], side: str) -> str:
    out = ['<div class="wrap-tbl"><table class="cmp checker-table">',
           '<thead><tr><th>Crawler</th><th>Who</th><th>What a block costs you</th>'
           '<th>Your site</th></tr></thead><tbody>']
    for r in rows:
        if r["side"] != side:
            continue
        out.append(f'<tr data-agent="{html.escape(r["name"])}"><td><code>{html.escape(r["name"])}</code></td>'
                   f'<td>{html.escape(r["owner"])}</td><td>{html.escape(r["impact"])}</td>'
                   f'<td class="verdict">&mdash;</td></tr>')
    out.append('</tbody></table></div>')
    return "".join(out)


def checker() -> Path:
    rows = _crawlers()
    n = len(rows)
    agents = ",".join(r["name"] for r in rows)
    surveyed = F._d()["attempted"]
    edge_denied = F.directives_edge_denied()
    edge_pct = round(100 * edge_denied / surveyed, 2)

    body = f"""
<p class="lede">Type your address. The checker reads your robots.txt the way the crawlers do and
shows, for each of the {n} crawlers below, whether it may fetch your page. The ones that decide
whether ChatGPT, Claude, Perplexity, Google's AI Overviews and Copilot can find and quote you come
first, and the ones that only collect training data come second.</p>

<form class="checker-form" id="checker" autocomplete="off" novalidate>
  <label for="checker-url">Website address</label>
  <div class="checker-row">
    <input id="checker-url" name="url" type="text" inputmode="url" placeholder="yourbusiness.com"
           spellcheck="false" required>
    <button class="btn" type="submit">Check my site</button>
  </div>
  <p class="checker-status" id="checker-status" role="status" aria-live="polite"></p>
</form>

<!-- Shown after any answer. The checker read one file for one page; this says
     so, and says what the product does beyond it, without dressing a free
     robots.txt reading up as an audit (CEO's revenue pass, 2026-09-29). -->
<div class="checker-next" id="checker-next" hidden>
  <p><strong>That was one file, read for one page.</strong> Docket runs {N_CHECKS} checks across
  every page it crawls, this one included, and it requests your pages as each AI crawler, so it
  also sees the server and CDN refusals this checker cannot.</p>
  <div class="buy-block compact">
    <p class="price-line"><span class="price-big">{PRICE_STR}</span><span class="price-pay4">once{PAY4}</span></p>
    {price_req_html()}
    <div class="hero-cta">
      <a class="btn" href="{checkout_url("tools-checker-result")}" data-ev="Buy" data-ev-price="{PRICE}"
         data-ev-button="tools-checker-result">Buy Docket</a>
      {f'<a class="btn-ghost" href="{SAMPLE_REPORT}" data-ev="Sample report" data-ev-button="tools-checker-result">See a sample report</a>' if HAS_SAMPLE else ''}
    </div>
  </div>
</div>

<h2>Crawlers that decide whether AI can cite you</h2>
<p>Block one of these and that assistant cannot read your pages when it answers a question, so it
cannot quote or link you. For most businesses these should be open.</p>
{_table(rows, "cite")}

<h2>Crawlers that collect training data</h2>
<p>These gather text to train future models. Blocking them is a reasonable choice for many
publishers, and it does not stop an assistant from finding and citing you through the crawlers
above.</p>
{_table(rows, "train")}

<h2>What this checker cannot see</h2>
<p>It reads one file, and robots.txt is a request, not a lock. Four things it cannot tell you:</p>
<ul>
<li><strong>Whether your server or CDN lets the crawler in.</strong> A firewall, a bot-protection
setting or a CDN rule can refuse a crawler that robots.txt welcomes. In Docket's {SURVEYED_HUMAN}
survey of the Tranco top {surveyed:,}, <strong>{edge_denied:,} hosts ({edge_pct}%)</strong> refused a
self-identifying bot outright before any robots rule applied.</li>
<li><strong>Tags on the page itself.</strong> A <code>noindex</code> or <code>nosnippet</code> in the
page or its headers limits what a search engine may show, and robots.txt says nothing about it.</li>
<li><strong>Pages that need JavaScript to show their text.</strong> Most AI crawlers do not run it, so a
page can be open to them and still look empty.</li>
<li><strong>What a crawler actually does.</strong> The file asks; well-behaved crawlers obey. It is not
enforcement.</li>
</ul>
<p>It checks the path you type, or your homepage if you type none. Rules for other sections of your
site can differ.</p>

<h2>How it reads the file</h2>
<p>The rules follow RFC 9309, the robots.txt standard, and match the parser inside Docket, so the
two give the same answer for the same file. A crawler obeys every group that names it; only if none
does, it obeys the <code>*</code> groups. The longest matching rule wins, and <code>Allow</code>
wins a tie. If your server answers robots.txt with a server error, crawlers stay out entirely; if
it answers "not found", they may crawl everything.</p>
<p>The checker fetches only your robots.txt, names itself in the request, keeps a copy for a few
minutes so repeated checks do not hit your server, and stores nothing about you or your site.</p>

<h2>Checking every page, and your server</h2>
<p>Docket checks all of this from your Mac, on every page it crawls: it requests pages as each AI
crawler and reports when your server refuses one that robots.txt permits, reads the tags on every
page, and flags text that only appears after JavaScript runs. It then ranks what to fix first, next
to {F.optional_connectors_word()} optional outside checks and the rest of the audit.</p>
{buy_block("tools-ai-crawler-checker")}

<h2>Related</h2>
<ul>
<li><a href="/learn/ai-crawler-directives/">Which AI crawlers to block and which to keep</a></li>
<li><a href="/how-to/fix-ai-crawlers-blocked-by-your-cdn/">When your CDN blocks AI crawlers robots.txt allows</a></li>
<li><a href="/learn/does-noindex-stop-ai-crawlers/">Does noindex stop AI crawlers?</a></li>
<li><a href="/index/">The Docket Index: who blocks AI search crawlers</a></li>
</ul>

<script>
(function () {{
  var ENDPOINT = {json.dumps(CHECKER_ENDPOINT)};
  var AGENTS = {json.dumps(agents)};
  var form = document.getElementById('checker');
  var input = document.getElementById('checker-url');
  var status = document.getElementById('checker-status');
  if (!form || !window.fetch) return;
  function cells() {{ return document.querySelectorAll('tr[data-agent] .verdict'); }}
  function say(text) {{ status.textContent = text; }}
  form.addEventListener('submit', function (e) {{
    e.preventDefault();
    var v = (input.value || '').trim();
    if (!v) {{ say('Enter your website address.'); return; }}
    [].forEach.call(cells(), function (c) {{ c.textContent = '…'; c.className = 'verdict'; }});
    say('Reading robots.txt…');
    fetch(ENDPOINT + '?url=' + encodeURIComponent(v) + '&agents=' + encodeURIComponent(AGENTS))
      .then(function (r) {{ return r.json().then(function (j) {{ return {{ ok: r.ok, j: j }}; }}); }})
      .then(function (res) {{
        var j = res.j;
        if (!res.ok || j.error) {{ say(j.error || 'That address could not be checked.'); [].forEach.call(cells(), function (c) {{ c.textContent = '—'; }}); return; }}
        var by = {{}};
        (j.results || []).forEach(function (r) {{ by[r.agent] = r; }});
        [].forEach.call(document.querySelectorAll('tr[data-agent]'), function (tr) {{
          var r = by[tr.getAttribute('data-agent')];
          var c = tr.querySelector('.verdict');
          if (!r) {{ c.textContent = '—'; return; }}
          c.className = 'verdict ' + (r.allowed ? 'yes' : 'no');
          var how = r.governedBy === 'name' ? 'named in your file' : r.governedBy === 'wildcard' ? 'by your * rules' : r.governedBy === 'status' ? 'by the server’s answer' : 'no rule applies';
          c.textContent = (r.allowed ? 'Allowed' : 'Blocked') + ': ' + how + (r.rule ? ' (' + r.rule + ')' : '');
        }});
        var msg = {{ parsed: 'Read ' + j.robots_url + '.', unavailable: j.robots_url + ' was not found (HTTP ' + j.status + '), so every crawler may crawl.', unreachable: j.robots_url + ' could not be read' + (j.status ? ' (HTTP ' + j.status + ')' : '') + ', so crawlers stay out until it can.', blocked: j.note || 'That address could not be checked.' }}[j.state] || '';
        if (j.note && j.state !== 'blocked') msg += ' ' + j.note;
        if (j.warnings && j.warnings.length) msg += ' ' + j.warnings[0];
        say(msg);
        var next = document.getElementById('checker-next');
        if (next) next.hidden = false;
        if (window.plausible) window.plausible('Checker', {{ props: {{ state: j.state }} }});
      }})
      .catch(function () {{ say('The checker could not be reached. Try again in a minute.'); }});
  }});
}})();
</script>
"""
    return render(
        cat="tools", slug="ai-crawler-checker",
        title="AI crawler checker: can ChatGPT read your site?",
        desc=(f"Free check of your robots.txt against {n} crawlers: which let ChatGPT, Claude, "
              "Perplexity, AI Overviews and Copilot read and cite you, and which only train."),
        h1="Can AI crawlers read your site?",
        crumb='<a href="/">Docket</a> / Tools / AI crawler checker',
        body=body,
        published="2026-09-28",
        schema_type="WebPage",
        faq=[
            ("Is ChatGPT allowed to crawl my website?",
             "Check OAI-SearchBot and ChatGPT-User in the table above. OAI-SearchBot builds the "
             "index ChatGPT Search cites from, and ChatGPT-User fetches a page when someone asks "
             "about it. GPTBot is OpenAI's training crawler; blocking it does not remove you from "
             "ChatGPT's answers."),
            ("Does blocking Google-Extended keep me out of AI Overviews?",
             "No. Google-Extended governs Gemini training and grounding in Gemini Apps and Vertex "
             "AI. AI Overviews and AI Mode follow your Googlebot rules."),
            ("My robots.txt allows every AI crawler. Am I visible?",
             "Not necessarily. A CDN, firewall or bot-protection setting can refuse a crawler "
             "that robots.txt allows, and this checker cannot see that. Docket requests pages as "
             "each crawler to find out."),
        ],
    )


BUILDERS = [checker]


def build_all() -> list[Path]:
    return [b() for b in BUILDERS]


if __name__ == "__main__":
    for p in build_all():
        print(p)
