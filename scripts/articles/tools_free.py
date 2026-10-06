#!/usr/bin/env python3
"""/tools/: Docket's free online checkers, and the hub that lists them.

CEO, 2026-10-06, from Matthew's ask to multiply Docket's visitors: over 30 days
the only page besides the homepage that drew people on its own was the AI
crawler checker, and free online checkers are what people search for and link
to. So /tools/ is a front door: each checker answers one question about one URL
in seconds, then says plainly what the Mac audit adds.

EVERY RESULT IS REAL. The checks run in the Worker (workers/ai-crawler-check/,
deployed from the Mac) on the page or file it fetched a moment ago, with rules
ported from Docket's engine and tested against it. Nothing is cached beyond a
few minutes at the edge and nothing about the site checked is stored.
"""
from __future__ import annotations

import html
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from render import (HAS_SAMPLE, INTEL, INTEL_DMG, N_CHECKS, PAY4, PRICE, PRICE_STR,  # noqa: E402
                    REFUND_DAYS, SAMPLE_REPORT, buy_block, checkout_url, download_url,
                    price_req_html, render)

WORKER = "https://ai-crawler-check.kerrco.workers.dev"

#: The free checkers, in the order the hub lists them. (slug, name, question).
TOOLS = [
    ("ai-crawler-checker", "AI crawler checker",
     "Can ChatGPT, Claude, Perplexity and Google's AI Overviews read your site?"),
    ("robots-txt-tester", "Robots.txt tester",
     "Is this exact page open or blocked for Googlebot, Bingbot and the AI crawlers, and which line decides?"),
]


def audit_next(src: str, *, what: str) -> str:
    """Shown after a result: what one free check was, and what the Mac audit adds.

    The free download comes first (content standard: one clear next step, Buy
    beside it), counted through the hub with this page's tag."""
    try_src = f"{src}-try-free"
    intel = (f'<p class="intel-dl">Intel Mac? <a href="{download_url(try_src + "-intel", to=INTEL_DMG)}" '
             f'data-ev="Download" data-ev-button="{try_src}-intel">Get the Intel version</a></p>'
             if INTEL else "")
    sample = (f'<a class="btn-ghost" href="{SAMPLE_REPORT}" data-ev="Sample report" '
              f'data-ev-button="{src}">See a sample report</a>' if HAS_SAMPLE else "")
    return f"""
<div class="checker-next" id="checker-next" hidden>
  <p><strong>That was {what}.</strong> Docket runs {N_CHECKS} checks across your whole site, ranked by
  what to fix first, each with where it is and the change to make. The free download shows your score
  and how many problems each area has.</p>
  <div class="buy-block compact">
    <div class="hero-cta">
      <a class="btn" href="{download_url(try_src)}" data-ev="Download" data-ev-button="{try_src}">Try it free</a>
      <a class="btn-ghost" href="{checkout_url(src)}" data-ev="Buy" data-ev-price="{PRICE}"
         data-ev-button="{src}">Buy once, {PRICE_STR}</a>
      {sample}
    </div>
    <p class="price-line"><span class="price-big">{PRICE_STR}</span><span class="price-pay4">once{PAY4}</span></p>
    {price_req_html()}
    <p class="hero-note">{REFUND_DAYS}-day refund, no conditions.</p>
    {intel}
  </div>
</div>"""


def hub() -> Path:
    items = "".join(
        f'<li><a href="/tools/{slug}/"><strong>{html.escape(name)}</strong></a>: {html.escape(q)}</li>'
        for slug, name, q in TOOLS)
    body = f"""
<p class="lede">Free checks you can run on any page, in your browser, with no account and nothing
to install. Each one answers one question in a few seconds.</p>
<ul class="tool-list">{items}</ul>

<h2>Which one to use</h2>
<p><strong>A page dropped out of search, or never showed up.</strong> Start with the robots.txt
tester. Paste the page's own address, not the homepage, because rules are written per path and the
homepage can be open while a whole section is closed. It names the line that decides, which is the
line to change.</p>
<p><strong>ChatGPT, Claude or Perplexity never mention you.</strong> The AI crawler checker reads the
same file for the crawlers those assistants send, and splits the ones that let an assistant quote
you from the ones that only collect training data. Blocking the second kind is a reasonable choice;
blocking the first kind usually is not.</p>

<h2>What a free check can and cannot tell you</h2>
<p>Each checker reads what a crawler would read at the moment you ask: one robots.txt file, for one
page. It cannot see a firewall or CDN that refuses a crawler the file allows, and it does not look at
the rest of your site. The rules come from Docket, the Mac app these pages belong to, so a free check
and the app give the same answer for the same page. The checkers fetch only what they need, name
themselves in the request, keep a copy for a few minutes so repeated checks do not hit your server,
and store nothing about the sites checked.</p>
<p>Docket runs {N_CHECKS} checks across every page of a site, requests pages as each AI crawler to
find the refusals a file cannot show, and ranks what to fix first.</p>
{buy_block("tools-hub", try_app="tools-hub-try-free")}
"""
    return render(
        cat="tools", slug="",
        title="Free SEO checkers: robots.txt, AI crawlers",
        desc=("Free online SEO checkers: test a page against robots.txt for Googlebot and the AI "
              "crawlers, and see which AI assistants can read your site. No account."),
        h1="Free SEO checkers",
        crumb='<a href="/">Docket</a> / Tools',
        body=body,
        published="2026-10-06",
        schema_type="CollectionPage",
    )


#: Who the robots.txt tester asks about, in table order. Search engines first,
#: then the AI crawlers that decide whether an assistant can cite a page, then
#: the training crawlers.
ROBOTS_AGENTS = [
    ("Googlebot", "Google", "Google Search, including AI Overviews and AI Mode"),
    ("Bingbot", "Microsoft", "Bing, and Copilot, which crawls as Bingbot"),
    ("Applebot", "Apple", "Siri and Spotlight suggestions"),
    ("DuckDuckBot", "DuckDuckGo", "DuckDuckGo search"),
    ("OAI-SearchBot", "OpenAI", "ChatGPT Search results"),
    ("ChatGPT-User", "OpenAI", "ChatGPT fetching a page a user asked about"),
    ("Claude-SearchBot", "Anthropic", "Claude's search results"),
    ("PerplexityBot", "Perplexity", "Perplexity's index and citations"),
    ("GPTBot", "OpenAI", "OpenAI model training"),
    ("ClaudeBot", "Anthropic", "Anthropic model training"),
    ("Google-Extended", "Google", "Gemini training and grounding, not Search"),
    ("CCBot", "Common Crawl", "the open web corpus many models train on"),
]


def robots_tester() -> Path:
    rows = "".join(
        f'<tr data-agent="{html.escape(a)}"><td><code>{html.escape(a)}</code></td>'
        f'<td>{html.escape(o)}</td><td>{html.escape(w)}</td><td class="verdict">&mdash;</td></tr>'
        for a, o, w in ROBOTS_AGENTS)
    agents = ",".join(a for a, _, _ in ROBOTS_AGENTS)
    body = f"""
<p class="lede">Paste the address of any page. The tester fetches that site's robots.txt and reads
it the way the crawlers do, then shows, for this exact page, who may crawl it and which line in the
file decides.</p>

<form class="checker-form" id="checker" autocomplete="off" novalidate>
  <label for="checker-url">Page address</label>
  <div class="checker-row">
    <input id="checker-url" name="url" type="text" inputmode="url"
           placeholder="yourbusiness.com/services/" spellcheck="false" required>
    <button class="btn" type="submit">Test this page</button>
  </div>
  <label for="checker-agent" class="checker-extra">Another crawler (optional)</label>
  <input id="checker-agent" class="checker-extra-input" type="text" placeholder="e.g. AhrefsBot"
         spellcheck="false" maxlength="40">
  <p class="checker-status" id="checker-status" role="status" aria-live="polite"></p>
</form>

<div class="wrap-tbl"><table class="cmp checker-table" id="robots-table">
<thead><tr><th>Crawler</th><th>Who</th><th>What it is for</th><th>This page</th></tr></thead>
<tbody>{rows}</tbody></table></div>
<p class="checker-sitemaps" id="checker-sitemaps" hidden></p>
{audit_next("tools-robots-tester", what="one file, read for one page")}

<h2>How to read the answer</h2>
<p><strong>Allowed</strong> or <strong>Blocked</strong> is what the file tells that crawler about this
page. The rule beside it is the line that decided, and "named in your file" means a group addresses
that crawler by name, so your <code>*</code> rules no longer apply to it. If no line matches, the page
is allowed.</p>
<p>The rules follow RFC 9309, the robots.txt standard, and match the parser inside Docket. A crawler
obeys every group that names it; only if none does, it obeys the <code>*</code> groups. The longest
matching rule wins, and <code>Allow</code> wins a tie. <code>*</code> matches any run of characters and
a <code>$</code> at the end anchors it. If the server answers robots.txt with a server error, crawlers
stay out of the whole site; if it answers "not found", everything is allowed.</p>

<h2>What robots.txt does not do</h2>
<ul>
<li><strong>It does not remove a page from search.</strong> A blocked page can still be indexed from
links pointing at it, without its content. To keep a page out, allow crawling and add a
<code>noindex</code> tag.</li>
<li><strong>It is a request, not a lock.</strong> Well-behaved crawlers obey it. A firewall or CDN rule
is what actually refuses a request, and this tester cannot see one.</li>
<li><strong>It is per host.</strong> <code>www.</code> and the bare domain, and every subdomain, each
have their own file. The tester reads the file for the host you type.</li>
</ul>

<h2>Checking every page</h2>
<p>Docket reads robots.txt for every page it crawls, requests pages as each AI crawler to find server
and CDN refusals, and checks the <code>noindex</code> tags and headers this tester cannot see, then
ranks all of it with the rest of its {N_CHECKS} checks.</p>
{buy_block("tools-robots-tester", try_app="tools-robots-tester-try-free")}

<h2>Related</h2>
<ul>
<li><a href="/tools/ai-crawler-checker/">AI crawler checker: can ChatGPT read your site?</a></li>
<li><a href="/learn/ai-crawler-directives/">Which AI crawlers to block and which to keep</a></li>
<li><a href="/learn/does-noindex-stop-ai-crawlers/">Does noindex stop AI crawlers?</a></li>
</ul>

<script>
(function () {{
  var ENDPOINT = {json.dumps(WORKER + "/check")};
  var AGENTS = {json.dumps(agents)};
  var form = document.getElementById('checker');
  var input = document.getElementById('checker-url');
  var extra = document.getElementById('checker-agent');
  var status = document.getElementById('checker-status');
  var tbody = document.querySelector('#robots-table tbody');
  if (!form || !window.fetch) return;
  function say(t) {{ status.textContent = t; }}
  function row(agent) {{
    var tr = tbody.querySelector('tr[data-agent="' + agent + '"]');
    if (tr) return tr;
    tr = document.createElement('tr'); tr.setAttribute('data-agent', agent); tr.className = 'custom';
    ['', '', 'the crawler you added', ''].forEach(function (t, i) {{
      var td = document.createElement('td'); if (i === 0) {{ var c = document.createElement('code'); c.textContent = agent; td.appendChild(c); }} else td.textContent = t;
      if (i === 3) td.className = 'verdict'; tr.appendChild(td);
    }});
    tbody.appendChild(tr); return tr;
  }}
  form.addEventListener('submit', function (e) {{
    e.preventDefault();
    var v = (input.value || '').trim();
    if (!v) {{ say('Enter a page address.'); return; }}
    var custom = (extra.value || '').trim().replace(/[^A-Za-z_-]/g, '');
    [].forEach.call(tbody.querySelectorAll('tr.custom'), function (tr) {{ tr.remove(); }});
    var agents = AGENTS + (custom ? ',' + custom : '');
    if (custom) row(custom);
    var path = '/';
    try {{ var u = new URL(/^[a-z]+:\\/\\//i.test(v) ? v : 'https://' + v); path = (u.pathname || '/') + (u.search || ''); }} catch (err) {{}}
    [].forEach.call(tbody.querySelectorAll('.verdict'), function (c) {{ c.textContent = '…'; c.className = 'verdict'; }});
    say('Reading robots.txt…');
    fetch(ENDPOINT + '?url=' + encodeURIComponent(v) + '&path=' + encodeURIComponent(path) + '&agents=' + encodeURIComponent(agents))
      .then(function (r) {{ return r.json().then(function (j) {{ return {{ ok: r.ok, j: j }}; }}); }})
      .then(function (res) {{
        var j = res.j;
        if (!res.ok || j.error) {{ say(j.error || 'That address could not be checked.'); return; }}
        var refused = j.state === 'unavailable' && (j.status === 401 || j.status === 403);
        (j.results || []).forEach(function (r) {{
          var c = row(r.agent).querySelector('.verdict');
          if (refused) {{ c.className = 'verdict'; c.textContent = 'Unknown: the site refused this tester'; return; }}
          c.className = 'verdict ' + (r.allowed ? 'yes' : 'no');
          var how = r.governedBy === 'name' ? 'named in your file' : r.governedBy === 'wildcard' ? 'by your * rules' : r.governedBy === 'status' ? 'by the server’s answer' : 'no rule matches';
          c.textContent = (r.allowed ? 'Allowed' : 'Blocked') + ': ' + how + (r.rule ? ' (' + r.rule + ')' : '');
        }});
        var msg = {{ parsed: 'Read ' + j.robots_url + ' for ' + j.path + '.', unavailable: (j.status === 401 || j.status === 403) ? j.robots_url + ' refused this checker (HTTP ' + j.status + '). The site may send crawlers it trusts a file this checker cannot see, so the answer is unknown.' : j.robots_url + ' was not found (HTTP ' + j.status + '), so every crawler may crawl.', unreachable: j.robots_url + ' could not be read' + (j.status ? ' (HTTP ' + j.status + ')' : '') + ', so crawlers stay out until it can.', blocked: j.note || 'That address could not be checked.' }}[j.state] || '';
        if (j.note && j.state !== 'blocked') msg += ' ' + j.note;
        if (j.warnings && j.warnings.length) msg += ' ' + j.warnings.slice(0, 2).join(' ');
        say(msg);
        var sm = document.getElementById('checker-sitemaps');
        if (j.sitemaps && j.sitemaps.length) {{ sm.textContent = 'Sitemaps listed in the file: ' + j.sitemaps.join(', '); sm.hidden = false; }} else sm.hidden = true;
        var next = document.getElementById('checker-next'); if (next) next.hidden = false;
        if (window.plausible) window.plausible('Checker', {{ props: {{ tool: 'robots', state: j.state }} }});
      }})
      .catch(function () {{ say('The tester could not be reached. Try again in a minute.'); }});
  }});
}})();
</script>
"""
    return render(
        cat="tools", slug="robots-txt-tester",
        title="Robots.txt tester for Googlebot and AI crawlers",
        desc=("Free robots.txt tester: paste a page address and see whether Googlebot, Bingbot, "
              "GPTBot and other crawlers may crawl it, and which line decides."),
        h1="Robots.txt tester",
        crumb='<a href="/">Docket</a> / <a href="/tools/">Tools</a> / Robots.txt tester',
        body=body,
        published="2026-10-06",
        schema_type="WebPage",
        faq=[
            ("How do I test my robots.txt?",
             "Paste the address of a page into the tester above. It fetches the site's robots.txt, "
             "applies the rules the way crawlers do, and shows for each crawler whether that page is "
             "allowed and which line decided."),
            ("Does Disallow in robots.txt remove a page from Google?",
             "No. It stops Googlebot fetching the page, but the page can still be indexed from links "
             "to it, without its content. To keep a page out of search, allow crawling and add a "
             "noindex tag."),
            ("Why is a page blocked when my * rules allow it?",
             "Because a group names that crawler. A crawler that finds a group addressed to it by "
             "name obeys only that group and ignores the * rules entirely."),
        ],
    )


BUILDERS = [hub, robots_tester]


def build_all() -> list[Path]:
    return [b() for b in BUILDERS]


if __name__ == "__main__":
    for p in build_all():
        print(p)
