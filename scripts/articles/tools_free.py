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

#: The limits and the schema types, as the Worker applies them
#: (workers/ai-crawler-check/src/page.js, ported from Docket's engine).
TITLE_MIN, TITLE_MAX, DESC_MIN, DESC_MAX = 25, 65, 70, 165
#: Where a search result cuts a title off (Docket's onpage.py states it).
TITLE_PX = 580
#: The engine's own example of a title that is short in characters and normal in
#: width (words.display_width). Its numbers are computed below, never typed.
JA_TITLE = "小形羊羹 24本入 | 株式会社 虎屋"


def display_width(text: str) -> int:
    """words.display_width: East Asian wide and fullwidth characters count two."""
    import unicodedata
    return sum(2 if unicodedata.east_asian_width(ch) in ("W", "F") else 1 for ch in text)
REQUIRED_PROPS = {
    "Product": ["name", "image"], "Offer": ["price", "priceCurrency"],
    "Recipe": ["name", "image", "recipeIngredient", "recipeInstructions"],
    "Event": ["name", "startDate", "location"],
    "JobPosting": ["title", "datePosted", "hiringOrganization", "jobLocation"],
    "FAQPage": ["mainEntity"], "HowTo": ["name", "step"], "Article": ["headline"],
    "BlogPosting": ["headline"], "LocalBusiness": ["name", "address"], "Organization": ["name"],
    "Review": ["reviewRating", "author"], "BreadcrumbList": ["itemListElement"],
    "VideoObject": ["name", "thumbnailUrl", "uploadDate"],
    "SoftwareApplication": ["name", "applicationCategory"],
}
REQUIRED_TYPES = list(REQUIRED_PROPS)

#: The free checkers, in the order the hub lists them. (slug, name, question).
TOOLS = [
    ("ai-crawler-checker", "AI crawler checker",
     "Can ChatGPT, Claude, Perplexity and Google's AI Overviews read your site?"),
    ("robots-txt-tester", "Robots.txt tester",
     "Is this exact page open or blocked for Googlebot, Bingbot and the AI crawlers, and which line decides?"),
    ("meta-tag-checker", "Title and meta tag checker",
     "Is this page's title the right length, is it indexable, and what will a shared link show?"),
    ("json-ld-checker", "JSON-LD structured data checker",
     "Is this page's structured data valid, and is anything missing that a rich result needs?"),
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
  and the top problem in full.</p>
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

<p><strong>A search result shows the wrong title, or a cut-off one.</strong> The title and meta tag
checker measures the title and description the way Docket does, by width rather than character
count, and checks the tags that decide whether the page can be indexed and what a shared link shows.</p>
<p><strong>Stars, prices or FAQs never appear under your result.</strong> The JSON-LD checker reads
every structured data block on the page, says which line breaks the JSON, and lists the properties a
rich result needs that are missing.</p>

<h2>What a free check can and cannot tell you</h2>
<p>Each checker reads what a crawler would read at the moment you ask: one robots.txt file, for one
page. It cannot see a firewall or CDN that refuses a crawler the file allows, and it does not look at
the rest of your site. The rules come from Docket, the Mac app these pages belong to, so a free check
and the app give the same answer for the same page. The checkers fetch only what they need, name
themselves in the request, keep a copy for a few minutes so repeated checks do not hit your server,
and store nothing about the sites checked.</p>
<p>Docket runs {N_CHECKS} checks across every page of a site, requests pages as each AI crawler to
find the refusals a file cannot show, and ranks what to fix first.</p>
<h2>Choosing between audit tools?</h2>
<p>These pages set Docket beside the tools people most often weigh it against. Each vendor's prices
and limits are read from its own pages and dated, each page ends with when to pick the other tool
instead, and each shows a real Docket audit.</p>
<ul class="tool-list">
<li><a href="/vs/se-ranking-vs-screaming-frog/"><strong>SE Ranking vs Screaming Frog</strong></a>:
a cloud audit metered by pages per month against a desktop crawler with no meter.</li>
<li><a href="/vs/ahrefs-site-audit-alternative/"><strong>Docket vs Ahrefs Site Audit</strong></a>:
one module of a keyword and backlink platform against a one-time Mac audit.</li>
<li><a href="/vs/seoptimer-alternative/"><strong>SEOptimer alternative</strong></a>: white-label
reports and a monthly crawl allowance against an unmetered audit you run yourself.</li>
</ul>

{buy_block("tools-hub", try_app="tools-hub-try-free")}
"""
    return render(
        cat="tools", slug="",
        title="Free SEO checkers: robots.txt, meta tags, schema",
        desc=("Free online SEO checkers: robots.txt for Googlebot and AI crawlers, title and meta "
              "tags, and JSON-LD structured data, for any page. No account."),
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
        f'<td>{html.escape(o)}</td><td>{html.escape(w)}</td><td class="verdict"></td></tr>'
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


#: The result renderer both page checkers share: one list of findings, each
#: with its level, its label and what to do.
RESULT_JS = """
  function renderFindings(box, findings) {
    box.innerHTML = '';
    var order = { problem: 0, warning: 1, note: 2, ok: 3 };
    var words = { problem: 'Fix', warning: 'Worth fixing', note: 'Note', ok: 'Fine' };
    findings.slice().sort(function (a, b) { return order[a.level] - order[b.level]; }).forEach(function (f) {
      var li = document.createElement('li'); li.className = 'finding ' + f.level;
      var tag = document.createElement('span'); tag.className = 'finding-level'; tag.textContent = words[f.level] || f.level;
      var b = document.createElement('strong'); b.textContent = f.label;
      li.appendChild(tag); li.appendChild(b);
      if (f.detail) { var p = document.createElement('span'); p.className = 'finding-detail'; p.textContent = f.detail; li.appendChild(p); }
      box.appendChild(li);
    });
  }
  function checkPage(v, done, say) {
    say('Reading the page…');
    fetch(PAGE + '?url=' + encodeURIComponent(v))
      .then(function (r) { return r.json().then(function (j) { return { ok: r.ok, j: j }; }); })
      .then(function (res) {
        var j = res.j;
        if (!res.ok || j.error) { say(j.error || 'That address could not be checked.'); return; }
        done(j);
        var next = document.getElementById('checker-next'); if (next) next.hidden = false;
      })
      .catch(function () { say('The checker could not be reached. Try again in a minute.'); });
  }
"""


def _form(button: str, placeholder: str) -> str:
    return f"""
<form class="checker-form" id="checker" autocomplete="off" novalidate>
  <label for="checker-url">Page address</label>
  <div class="checker-row">
    <input id="checker-url" name="url" type="text" inputmode="url" placeholder="{placeholder}"
           spellcheck="false" required>
    <button class="btn" type="submit">{button}</button>
  </div>
  <p class="checker-status" id="checker-status" role="status" aria-live="polite"></p>
</form>"""


def meta_checker() -> Path:
    body = f"""
<p class="lede">Paste the address of any page. The checker reads its title, meta description,
canonical, robots tags, headings and sharing tags, and says what to fix, with the same limits Docket
uses.</p>
{_form("Check this page", "yourbusiness.com/services/")}
<div class="meta-summary" id="meta-summary" hidden>
  <dl>
    <dt>Title</dt><dd id="ms-title"></dd>
    <dt>Description</dt><dd id="ms-desc"></dd>
    <dt>Canonical</dt><dd id="ms-canon"></dd>
    <dt>H1</dt><dd id="ms-h1"></dd>
  </dl>
</div>
<ul class="findings" id="findings"></ul>
{audit_next("tools-meta-checker", what="one page, read once")}

<h2>How long should a title be?</h2>
<p>Search results cut a title off at about {TITLE_PX} pixels, which is roughly {TITLE_MAX} Latin characters.
Docket measures width rather than counting characters, because Chinese, Japanese and Korean characters
render about twice as wide: a {len(JA_TITLE)}-character Japanese title is {display_width(JA_TITLE)} wide and perfectly normal. Below
{TITLE_MIN} wide, a result has little to show. Put the words that say what the page is first; a
brand name at the end is the first thing to be cut.</p>

<h2>How long should a meta description be?</h2>
<p>Between {DESC_MIN} and {DESC_MAX} wide is the range Docket uses. Google writes its own snippet when the
description does not match what someone searched for, so the description is a suggestion. A good one
says what the page offers and why to click, in the first sentence.</p>

<h2>What the other checks mean</h2>
<ul>
<li><strong>Indexable.</strong> A <code>noindex</code> in a robots meta tag, or in the
<code>X-Robots-Tag</code> header, keeps the page out of search. The checker reads both.</li>
<li><strong>Canonical.</strong> It tells search engines which address to show for this page. Pointing at
another address is fine when it is deliberate, such as a filtered view pointing at the main list.</li>
<li><strong>H1, language and viewport.</strong> One main heading, a <code>lang</code> on the
<code>&lt;html&gt;</code> tag, and a viewport tag so phones get a page made for them.</li>
<li><strong>Open Graph.</strong> <code>og:title</code>, <code>og:description</code> and
<code>og:image</code> decide what a link shows when it is shared in a chat or on social media.</li>
</ul>

<h2>What one page cannot tell you</h2>
<p>Whether two pages share the same title, whether the canonical you point at is itself indexable, and
whether the page's text matches what its tags promise. Docket checks those across every page of a site,
with the rest of its {N_CHECKS} checks, and ranks what to fix first.</p>
{buy_block("tools-meta-checker", try_app="tools-meta-checker-try-free")}

<h2>Related</h2>
<ul>
<li><a href="/how-to/write-title-tags-that-fit/">Write title tags that fit</a></li>
<li><a href="/tools/json-ld-checker/">JSON-LD structured data checker</a></li>
<li><a href="/tools/robots-txt-tester/">Robots.txt tester</a></li>
</ul>

<script>
(function () {{
  var PAGE = {json.dumps(WORKER + "/page")};
  {RESULT_JS}
  var form = document.getElementById('checker');
  var input = document.getElementById('checker-url');
  var status = document.getElementById('checker-status');
  if (!form || !window.fetch) return;
  function say(t) {{ status.textContent = t; }}
  function set(id, t) {{ document.getElementById(id).textContent = t; }}
  form.addEventListener('submit', function (e) {{
    e.preventDefault();
    var v = (input.value || '').trim();
    if (!v) {{ say('Enter a page address.'); return; }}
    checkPage(v, function (j) {{
      var m = j.meta;
      set('ms-title', m.title ? m.title + ' (' + m.titleWidth + ' wide)' : 'none');
      set('ms-desc', m.description ? m.description + ' (' + m.descriptionWidth + ' wide)' : 'none');
      set('ms-canon', m.canonical || 'none');
      set('ms-h1', m.h1 && m.h1.length ? m.h1.join(' | ') : 'none');
      document.getElementById('meta-summary').hidden = false;
      renderFindings(document.getElementById('findings'), m.findings);
      var n = m.findings.filter(function (f) {{ return f.level === 'problem' || f.level === 'warning'; }}).length;
      say('Read ' + j.final_url + (j.redirects && j.redirects.length ? ' after ' + j.redirects.length + ' redirect(s)' : '') + '. ' + (n ? n + ' thing' + (n === 1 ? '' : 's') + ' to fix.' : 'Nothing to fix on this page.'));
      if (window.plausible) window.plausible('Checker', {{ props: {{ tool: 'meta', issues: String(n) }} }});
    }}, say);
  }});
}})();
</script>
"""
    return render(
        cat="tools", slug="meta-tag-checker",
        title="Title and meta tag checker: length, noindex, OG",
        desc=("Free title and meta tag checker: paste a page and see its title and description "
              "width, noindex, canonical, H1 and Open Graph tags, and what to fix."),
        h1="Title and meta tag checker",
        crumb='<a href="/">Docket</a> / <a href="/tools/">Tools</a> / Title and meta tag checker',
        body=body,
        published="2026-10-06",
        schema_type="WebPage",
        faq=[
            ("How long should a title tag be?",
             f"Up to about {TITLE_PX} pixels, roughly {TITLE_MAX} Latin characters, before search results "
             "cut it off. Width matters more than count: East Asian characters are about twice as wide."),
            ("How long should a meta description be?",
             f"Between {DESC_MIN} and {DESC_MAX} wide is the range Docket uses. Google may still write "
             "its own snippet when the description does not match the search."),
            ("How do I check if a page is set to noindex?",
             "Paste it into the checker above. It reads the robots meta tag on the page and the "
             "X-Robots-Tag header the server sends, and reports a noindex in either."),
        ],
    )


def jsonld_checker() -> Path:
    types = ", ".join(sorted(REQUIRED_TYPES))
    body = f"""
<p class="lede">Paste the address of any page. The checker reads every JSON-LD block on it, says
which line breaks the JSON if one does, and lists the properties each item needs for a rich result
that are missing.</p>
{_form("Check structured data", "yourshop.com/products/kettle/")}
<div class="wrap-tbl" id="ld-items-wrap" hidden><table class="cmp" id="ld-items">
<thead><tr><th>Block</th><th>Type</th><th>Name</th><th>Missing</th></tr></thead><tbody></tbody></table></div>
<ul class="findings" id="findings"></ul>
{audit_next("tools-jsonld-checker", what="one page, read once")}

<h2>What it checks</h2>
<ul>
<li><strong>Whether each block is valid JSON.</strong> One stray comma makes a search engine discard the
whole block. The checker names the line and column where the parser stopped.</li>
<li><strong>Whether it says it is schema.org.</strong> A block with no <code>@context</code> declares
types that mean nothing to a search engine.</li>
<li><strong>Required properties.</strong> For {len(REQUIRED_TYPES)} types ({types}), the properties Google
requires for a rich result, from the same table Docket uses. Items inside other items, such as an
Offer inside a Product, are checked too.</li>
</ul>

<h2>Which properties each type needs</h2>
<p>The checker reports a type as incomplete when one of these is missing or empty. The list is the one
inside Docket, taken from Google's structured data documentation.</p>
<div class="wrap-tbl"><table class="cmp"><thead><tr><th>Type</th><th>Needs</th></tr></thead><tbody>
{"".join(f"<tr><td><code>{t}</code></td><td>{', '.join(f'<code>{p}</code>' for p in props)}</td></tr>" for t, props in REQUIRED_PROPS.items())}
</tbody></table></div>
<p>An Offer is usually nested inside a Product, and a Review inside a Product or a LocalBusiness. Both
are checked where they sit, so a Product with a complete name and image can still fail on the price
of its Offer.</p>

<h2>What it does not check</h2>
<ul>
<li><strong>Microdata and RDFa.</strong> It reads JSON-LD, the format Google recommends.</li>
<li><strong>Whether the markup matches the page.</strong> A price or rating in the markup that the
visitor cannot see is against Google's guidelines. Docket compares the markup with the visible page;
one free check cannot.</li>
<li><strong>Whether Google will show a rich result.</strong> Valid, complete markup makes a page
eligible. Google decides whether to show it.</li>
</ul>
<p>Docket reads the structured data on every page it crawls, compares it with what each page shows,
and ranks what to fix with the rest of its {N_CHECKS} checks.</p>
{buy_block("tools-jsonld-checker", try_app="tools-jsonld-checker-try-free")}

<h2>Related</h2>
<ul>
<li><a href="/how-to/json-ld-parser-errors/">Fix JSON-LD parser errors</a></li>
<li><a href="/tools/meta-tag-checker/">Title and meta tag checker</a></li>
<li><a href="/tools/robots-txt-tester/">Robots.txt tester</a></li>
</ul>

<script>
(function () {{
  var PAGE = {json.dumps(WORKER + "/page")};
  {RESULT_JS}
  var form = document.getElementById('checker');
  var input = document.getElementById('checker-url');
  var status = document.getElementById('checker-status');
  if (!form || !window.fetch) return;
  function say(t) {{ status.textContent = t; }}
  form.addEventListener('submit', function (e) {{
    e.preventDefault();
    var v = (input.value || '').trim();
    if (!v) {{ say('Enter a page address.'); return; }}
    checkPage(v, function (j) {{
      var ld = j.jsonld;
      var tb = document.querySelector('#ld-items tbody'); tb.innerHTML = '';
      ld.nodes.forEach(function (n) {{
        var tr = document.createElement('tr');
        [String(n.block), n.types.join(', '), n.name || '', n.missing.length ? n.missing.join(', ') : 'nothing'].forEach(function (t, i) {{
          var td = document.createElement('td'); td.textContent = t; if (i === 3) td.className = n.missing.length ? 'verdict no' : 'verdict yes'; tr.appendChild(td);
        }});
        tb.appendChild(tr);
      }});
      document.getElementById('ld-items-wrap').hidden = !ld.nodes.length;
      renderFindings(document.getElementById('findings'), ld.findings);
      say('Read ' + j.final_url + ': ' + ld.blocks + ' JSON-LD block' + (ld.blocks === 1 ? '' : 's') + ', ' + ld.nodes.length + ' item' + (ld.nodes.length === 1 ? '' : 's') + '.');
      if (window.plausible) window.plausible('Checker', {{ props: {{ tool: 'jsonld', blocks: String(ld.blocks) }} }});
    }}, say);
  }});
}})();
</script>
"""
    return render(
        cat="tools", slug="json-ld-checker",
        title="JSON-LD checker: test structured data on any page",
        desc=("Free JSON-LD structured data checker: paste a page and see invalid JSON by line and "
              "column, and which required properties each item is missing."),
        h1="JSON-LD structured data checker",
        crumb='<a href="/">Docket</a> / <a href="/tools/">Tools</a> / JSON-LD checker',
        body=body,
        published="2026-10-06",
        schema_type="WebPage",
        faq=[
            ("How do I test my structured data?",
             "Paste the page address into the checker above. It reads every JSON-LD block on the page, "
             "reports invalid JSON with the line and column, and lists missing required properties."),
            ("Why is my structured data not showing in Google?",
             "Usually because the JSON is invalid, a required property is missing, or the marked-up "
             "content is not visible on the page. Valid, complete markup makes a page eligible; Google "
             "decides whether to show a rich result."),
            ("Does this check Microdata or RDFa?",
             "No. It reads JSON-LD, the format Google recommends for structured data."),
        ],
    )


BUILDERS = [hub, robots_tester, meta_checker, jsonld_checker]


def build_all() -> list[Path]:
    return [b() for b in BUILDERS]


if __name__ == "__main__":
    for p in build_all():
        print(p)
