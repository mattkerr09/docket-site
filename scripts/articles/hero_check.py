"""The home hero's robots.txt check, using the free tool's crawler data."""
from __future__ import annotations

import json

from render import WINDOWS, WIN_SETUP, download_url
from crawler_fix import FIX_JS, search_names as _search_names
from tool_ai_crawlers import CHECKER_ENDPOINT, CITATION_PURPOSES, _crawlers


def hero_check_block() -> str:
    rows = _crawlers()
    agents = ",".join(r["name"] for r in rows)
    search_names = _search_names(rows)
    assistants = [
        {"label": label, "agents": [r["name"] for r in rows
                                      if r["owner"] == owner and r["purpose"] in CITATION_PURPOSES]}
        for label, owner in (("ChatGPT", "OpenAI"), ("Claude", "Anthropic"),
                             ("Perplexity", "Perplexity"))
    ]
    verdicts = "".join(
        f'<li>{assistant["label"]}: <strong id="hero-check-verdict-{i}"></strong></li>'
        for i, assistant in enumerate(assistants)
    )
    downloads = (f'<a class="btn{" dl-mac" if WINDOWS else ""}" '
                 f'href="{download_url("home-hero-check")}">Run the full free audit</a>')
    if WINDOWS:
        downloads += (f'<a class="btn dl-win" '
                      f'href="{download_url("home-hero-check-win", to=WIN_SETUP)}">'
                      'Run the full free audit</a>')
    return rf"""<form class="hero-check" action="/tools/ai-crawler-checker/" method="get">
  <label for="hero-check-address">Your website address</label>
  <div class="hero-check-row">
    <input id="hero-check-address" type="text" name="d" inputmode="url" autocomplete="off"
           autocapitalize="off" spellcheck="false" placeholder="yoursite.com">
    <button class="btn" type="submit">Check it free</button>
  </div>
</form>
<p class="hero-check-privacy">The checker fetches only your robots.txt, names itself in the request, keeps a copy for a few
minutes so repeated checks do not hit your server, and stores nothing about you or your site.</p>
<div class="hero-check-result" id="hero-check-result" role="status" aria-live="polite">
  <p id="hero-check-status"></p>
  <div id="hero-check-answer" hidden>
    <ul>{verdicts}</ul>
    <p id="hero-check-summary"></p>
    <div id="hero-check-fix" hidden>
      <h2>How to fix it</h2>
      <p id="hero-check-fix-google" hidden>Your robots.txt blocks Googlebot as well, so start there: removing that block lets these crawlers in too. Then, if you want to refuse model training, add Disallow groups for the training crawlers only.</p>
      <div id="hero-check-fix-wildcard" hidden>
        <p>These crawlers are blocked by your * rule. Add these lines to your robots.txt. A group that names a crawler beats the * rule for that crawler.</p>
        <pre id="hero-check-fix-snippet"></pre>
        <button class="btn-ghost" type="button" data-copy="hero-check-fix-snippet">Copy</button>
      </div>
      <p id="hero-check-fix-name" hidden></p>
      <p id="hero-check-fix-server" hidden></p>
    </div>
    <p>This reads your robots.txt only. A firewall or CDN can still refuse a crawler that robots.txt allows, and no robots.txt check can see that.</p>
  </div>
</div>
<div class="hero-check-next" id="hero-check-next" hidden>
  {downloads}
  <a id="hero-check-every" href="/tools/ai-crawler-checker/">See every crawler</a>
</div>
<style>
.hero-check{{max-width:33rem;margin:0 0 .7rem}}
.hero-check label{{display:block;font-size:var(--t-base);margin-bottom:.4rem}}
.hero-check-row{{display:flex;gap:.5rem}}
.hero-check input{{min-width:0;flex:1;padding:.75rem;border:1px solid var(--border-strong);
  border-radius:var(--radius-sm);background:var(--surface);color:var(--text);font:inherit;font-size:1rem}}
.hero-check button{{flex-shrink:0;padding:.75rem 1rem}}
.hero-check-privacy{{max-width:33rem;font-size:var(--t-sm);color:var(--text-dim);line-height:1.5;margin:0 0 1rem}}
.hero-check-result{{max-width:33rem;font-size:var(--t-base);overflow-wrap:anywhere}}
.hero-check-result p:empty{{display:none}}
.hero-check-result ul{{list-style:none;padding:0;margin:0 0 .7rem}}
.hero-check-next{{margin:0 0 1.5rem}}
#hero-check-fix{{max-width:33rem}}
#hero-check-fix h2{{font-size:var(--t-base);margin:.8rem 0 .4rem}}
#hero-check-fix pre{{white-space:pre-wrap;overflow-wrap:anywhere;margin:.5rem 0}}
.hero-check-next a{{margin:0 .5rem .5rem 0}}
.hero-check-next a:not(.btn){{display:inline-block;text-decoration:underline}}
</style>
<script>
(function () {{
  {FIX_JS}
  var ENDPOINT = {json.dumps(CHECKER_ENDPOINT)};
  var AGENTS = {json.dumps(agents)};
  var SEARCH_NAMES = {json.dumps(search_names)};
  var ASSISTANTS = {json.dumps(assistants)};
  var form = document.querySelector('form.hero-check');
  if (!form || !window.fetch) return;
  var input = document.getElementById('hero-check-address');
  var status = document.getElementById('hero-check-status');
  var answer = document.getElementById('hero-check-answer');
  var summary = document.getElementById('hero-check-summary');
  var fixBox = document.getElementById('hero-check-fix');
  var next = document.getElementById('hero-check-next');
  var every = document.getElementById('hero-check-every');
  var request = 0;
  var copy = fixBox.querySelector('[data-copy]');
  copy.addEventListener('click', function () {{
    var el = document.getElementById(copy.getAttribute('data-copy'));
    var done = function () {{ var t = copy.textContent; copy.textContent = 'Copied'; setTimeout(function () {{ copy.textContent = t; }}, 1500); }};
    if (navigator.clipboard && navigator.clipboard.writeText) navigator.clipboard.writeText(el.textContent).then(done, function () {{}});
    else {{
      var range = document.createRange();
      range.selectNodeContents(el);
      var selection = window.getSelection();
      selection.removeAllRanges();
      selection.addRange(range);
      try {{ document.execCommand('copy'); done(); }} catch (e) {{}}
    }}
    if (window.plausible) window.plausible('fix_copied');
  }});
  [].forEach.call(next.querySelectorAll('.btn'), function (link) {{
    link.addEventListener('click', function () {{
      if (window.plausible) window.plausible('result_to_download');
    }});
  }});
  form.addEventListener('submit', function (e) {{
    e.preventDefault();
    if (window.plausible) window.plausible('check_started');
    run();
  }});
  function run() {{
    var current = ++request;
    var v = (input.value || '').trim();
    answer.hidden = true;
    next.hidden = true;
    fixBox.hidden = true;
    document.getElementById('hero-check-fix-snippet').textContent = '';
    document.getElementById('hero-check-fix-name').textContent = '';
    document.getElementById('hero-check-fix-server').textContent = '';
    if (!v) {{ status.textContent = 'Enter your website address.'; return; }}
    status.textContent = 'Reading robots.txt…';
    fetch(ENDPOINT + '?url=' + encodeURIComponent(v) + '&agents=' + encodeURIComponent(AGENTS))
      .then(function (r) {{ return r.json().then(function (j) {{ return {{ ok: r.ok, j: j }}; }}); }})
      .then(function (res) {{
        if (current !== request) return;
        var j = res.j;
        if (!res.ok || j.error) {{ status.textContent = j.error || 'That address could not be checked.'; return; }}
        var refused = j.state === 'unavailable' && (j.status === 401 || j.status === 403);
        var by = {{}};
        (j.results || []).forEach(function (r) {{ by[r.agent] = r; }});
        var blocked = 0;
        var blockedCrawlers = 0;
        var readable = 0;
        ASSISTANTS.forEach(function (assistant, i) {{
          var returned = assistant.agents.map(function (name) {{ return by[name]; }}).filter(Boolean);
          var denied = returned.filter(function (r) {{ return r.allowed === false; }}).length;
          var verdict = 'Not checked';
          if (refused) verdict = 'Unknown: the site refused this checker';
          else if (denied) {{ verdict = 'Blocked'; blocked++; blockedCrawlers += denied; }}
          else if (returned.length && returned.every(function (r) {{ return r.allowed === true; }})) {{
            verdict = 'Can read'; readable++;
          }}
          document.getElementById('hero-check-verdict-' + i).textContent = verdict;
        }});
        var msg = {{ parsed: 'Read ' + j.robots_url + '.', unavailable: (j.status === 401 || j.status === 403) ? j.robots_url + ' refused this checker (HTTP ' + j.status + '). The site may send crawlers it trusts a file this checker cannot see, so the answer is unknown.' : j.robots_url + ' was not found (HTTP ' + j.status + '), so every crawler may crawl.', unreachable: j.robots_url + ' could not be read' + (j.status ? ' (HTTP ' + j.status + ')' : '') + ', so crawlers stay out until it can.', blocked: j.note || 'That address could not be checked.' }}[j.state] || '';
        if (j.note && j.state !== 'blocked') msg += ' ' + j.note;
        if (j.warnings && j.warnings.length) msg += ' ' + j.warnings[0];
        status.textContent = msg;
        var fix = buildCrawlerFix(j.results || [], SEARCH_NAMES);
        fixBox.hidden = !(fix.byWildcard.length || fix.byName.length || fix.byServer.length);
        document.getElementById('hero-check-fix-google').hidden = !fix.googleBlocked;
        document.getElementById('hero-check-fix-wildcard').hidden = !fix.snippet;
        document.getElementById('hero-check-fix-snippet').textContent = fix.snippet;
        var named = document.getElementById('hero-check-fix-name');
        named.hidden = !fix.byName.length;
        named.textContent = fix.byName.length ? "Your robots.txt names these crawlers and disallows them, so this reads as a decision: " + fix.byName.join(', ') + ". If you want them to read your site, delete that crawler's Disallow line, or change it to Allow: /." : '';
        var server = document.getElementById('hero-check-fix-server');
        server.hidden = !fix.byServer.length;
        server.textContent = fix.byServer.length ? 'These crawlers were blocked by the way your server answered for robots.txt, not by a rule: ' + fix.byServer.join(', ') + '. Make /robots.txt answer 200 or 404.' : '';
        summary.textContent = '';
        if (blocked) {{
          summary.textContent = 'Your robots.txt blocks ' + blockedCrawlers + ' AI search crawlers, so those assistants cannot quote your site. The free audit shows the fix in full.';
          if (window.plausible) window.plausible('result_blocked', {{ props: {{ blocked: blocked }} }});
        }} else if (readable === ASSISTANTS.length) {{
          summary.textContent = 'Your robots.txt lets all three read your site. The free audit checks the rest, in order.';
          if (window.plausible) window.plausible('result_allowed');
        }}
        var host = '';
        try {{ host = new URL(j.robots_url).hostname; }} catch (e) {{}}
        if (!host) {{
          try {{ host = new URL(/^https?:\/\//i.test(v) ? v : 'https://' + v).hostname; }} catch (e) {{}}
        }}
        every.href = '/tools/ai-crawler-checker/?d=' + encodeURIComponent(host);
        answer.hidden = false;
        next.hidden = false;
      }})
      .catch(function () {{
        if (current === request) status.textContent = 'The checker could not be reached. Try again in a minute.';
      }});
  }}
}})();
</script>"""
