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
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import comparisons  # noqa: E402
from render import (HAS_SAMPLE, INTEL, INTEL_DMG, N_CHECKS, N_LANES, PAY4_BUY, PRICE, PRICE_STR,  # noqa: E402
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
    ("seo-checker", "SEO checker",
     "What is wrong with this page, how bad is it, and what should be fixed first?"),
    ("ai-crawler-checker", "AI crawler checker",
     "Can ChatGPT, Claude, Perplexity and Google's AI Overviews read your site?"),
    ("robots-txt-tester", "Robots.txt tester",
     "Is this exact page open or blocked for Googlebot, Bingbot and the AI crawlers, and which line decides?"),
    ("meta-tag-checker", "Title and meta tag checker",
     "Is this page's title the right length, is it indexable, and what will a shared link show?"),
    ("json-ld-checker", "JSON-LD structured data checker",
     "Is this page's structured data valid, and is anything missing that a rich result needs?"),
    ("serp-preview", "Search result preview",
     "How will a title and description look in a search result, and where will they be cut off?"),
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
    <p class="price-line"><span class="price-big">{PRICE_STR}</span><span class="price-pay4">once{PAY4_BUY}</span></p>
    {price_req_html()}
    <p class="hero-note">{REFUND_DAYS}-day refund, no conditions.</p>
    {intel}
  </div>
</div>"""



def how_it_works(you_see: list[str], *, free: str, steps: list[str], step_up: str) -> str:
    """No sign-up, three steps, what the result shows, then the step up to the app.

    Matthew, 2026-11-06, from reading the free-tool pages of the big SEO suites: they all say
    "no sign-up", give three steps and list what the report contains before the button is
    pressed, and end on what the paid product adds. Every argument is written for its own page:
    one block worded the same on five pages put three of them over lint.py's shared-phrasing
    limit, which is the near-duplicate signal search engines act on."""
    return f"""
<section class="tool-how" aria-label="How this checker works">
<p class="tool-free"><strong>Free, no sign-up required.</strong> {free}</p>
<ol class="tool-steps">{"".join(f"<li>{x}</li>" for x in steps)}</ol>
<p class="tool-see-h"><strong>You will see:</strong></p>
<ul class="tool-see">{"".join(f"<li>{x}</li>" for x in you_see)}</ul>
<p class="tool-step-up">{step_up}</p>
</section>"""

def hub() -> Path:
    items = "".join(
        f'<li><a href="/tools/{slug}/"><strong>{html.escape(name)}</strong></a>: {html.escape(q)}</li>'
        for slug, name, q in TOOLS)
    body = f"""
<p class="lede">Free checks you can run on any page, in your browser. No sign-up required and nothing
to install. Each one answers one question in a few seconds.</p>
<ul class="tool-list">{items}</ul>

<h2>Which one to use</h2>
<p><strong>You want to know what is wrong with a page, and what to fix first.</strong> Start with the
SEO checker. It reads the page and its robots.txt, gives a score, counts the problems in each area and
puts the worst one at the top with the fix. The checkers below go deeper on one question each.</p>
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
<p><strong>You are writing a new title and want to see it first.</strong> The search result
preview shows the title and description as a result would, before anything is published, and marks
where Docket expects each to be cut off. It needs no address: type the words and watch.</p>
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
<li><a href="/vs/seoptimer-alternative/"><strong>SEOptimer alternative</strong></a>: reports on a
custom domain and a monthly crawl allowance against an unmetered audit you run yourself.</li>
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
<p class="lede">Paste the address of any page to see whether Googlebot may crawl it, and which line of
the site's robots.txt decides. The same test runs for Bingbot, the AI crawlers and any other crawler you name.
It works on any site, yours or not, and there is nothing to verify first.</p>

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
{how_it_works([
    "Allowed or blocked for Googlebot, Bingbot and the AI crawlers, one row each",
    "The exact robots.txt line that decides, so you know which line to change",
    "The sitemaps the file lists",
], free="It works on any site, with nothing to verify first.",
   steps=["Paste the address of the page that dropped out of search, not only the homepage.",
          "Add another crawler's name if you want one, then press <strong>Test this page</strong>.",
          "Read each crawler's verdict beside the line that decides it."],
   step_up=(f'One file, read for one page. <a href="/download/">Docket</a> reads it for every page of your '
            f"site, then requests those pages as each crawler to catch the firewall and CDN refusals a file "
            f"cannot show, among its {N_CHECKS} checks."))}
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

<h2>Where did Google's robots.txt tester go?</h2>
<p>Google no longer runs a robots.txt Tester in Search Console. In its place is the robots.txt report. It shows
which robots.txt files Google found for the top {comparisons._GRR["top_hosts"]} hosts of a property, when each was last crawled, and any warnings or
errors, and it lets you request a recrawl of a file in an emergency. It is available only for properties at the domain
level, and Google's help page describes no way to type in a page address and see whether that page is blocked.</p>
<p>This tester does that part. It fetches the file the way a crawler would, for the page you give it, and shows which
rule decided. Use the report to see what Google last fetched, and this to see what a rule does to a page.</p>

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
<li><a href="/vs/ahrefs-site-audit-alternative/">Ahrefs Site Audit</a>: what a paid crawler checks, and how a crawl is paid for</li>
</ul>
{comparisons._verified_note("gsc-robots-report", closing="Google's pages change; if one has moved on from what is described here, <a href='/contact/'>tell us</a> and it will be corrected.")}

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
        title="Google robots.txt tester: is Googlebot blocked?",
        desc=("Free Google robots.txt tester: paste any page address and see whether Googlebot, Bingbot, "
              "GPTBot and other crawlers may crawl it, and which line decides."),
        h1="Google robots.txt tester",
        crumb='<a href="/">Docket</a> / <a href="/tools/">Tools</a> / Robots.txt tester',
        body=body,
        published="2026-10-06",
        schema_type="WebPage",
        faq=[
            ("Where is the robots.txt tester in Google Search Console?",
             "Google replaced it with the robots.txt report, which lists the files Google found, when it last crawled "
             "them and any errors. The report does not take a page address, so to see whether one page is blocked, "
             "paste its address into the tester on this page."),
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
<p class="lede">A title tag length checker: paste the address of any page and it measures the title against
about {TITLE_MAX} characters, the width Docket uses before a search result cuts it off, and the meta description
against {DESC_MIN} to {DESC_MAX}. It then reads the canonical, robots tags, headings and sharing tags, and says
what to fix.</p>
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
{how_it_works([
    "The title and meta description, measured the way Docket measures them, with a verdict on each",
    "Whether the page can be indexed, from its robots tag and its headers",
    "The canonical, the main heading, and what a shared link will show",
], free="Nothing to install; the page is read once and nothing about it is stored.",
   steps=["Paste the address of a live page, yours or a rival's.", "Press <strong>Check this page</strong>.",
          "Start with the first item: the worst comes first, with the change to make."],
   step_up=('One page at a time. <a href="/download/">Docket</a> measures the title and description of '
            "every page on your site and finds the pages that share a title or point a canonical at an "
            "address that cannot be indexed."))}
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
<p>Whether two pages <a href="/how-to/fix-duplicate-title-tags/">share the same title</a>, whether the canonical you point at is itself indexable, and
whether the page's text matches what its tags promise. Docket checks those across every page of a site,
with the rest of its {N_CHECKS} checks, and ranks what to fix first.</p>
{buy_block("tools-meta-checker", try_app="tools-meta-checker-try-free")}

<h2>Related</h2>
<ul>
<li><a href="/how-to/write-title-tags-that-fit/">Write title tags that fit</a></li>
<li><a href="/how-to/write-meta-descriptions/">Write meta descriptions for every page</a></li>
<li><a href="/how-to/fix-favicon-not-showing-in-search/">Fix a favicon that is not showing</a></li>
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
        modified="2026-10-28",
        title="Title tag length checker (free): meta, noindex, OG",
        desc=(f"Free title tag length checker: paste a page to see if its title (about {TITLE_MAX} characters) and "
              "meta description fit, plus noindex, canonical, H1 and Open Graph tags."),
        h1="Title tag and meta description length checker",
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
{how_it_works([
    "Every JSON-LD block on the page, with its type and name",
    "The line and column where broken JSON stops a parser",
    "The properties a rich result needs that are missing",
], free="No account, and nothing about the page you check is stored.",
   steps=["Paste the address of a product, recipe, event or article page.",
          "Press <strong>Check structured data</strong>.",
          "Read each block's verdict and the properties it still needs."],
   step_up=('This reads the page you paste. <a href="/download/">Docket</a> reads the structured data on '
            "every page of your site and checks that what the markup says matches what the page shows."))}
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


#: The worker's copy of words.display_width's wide ranges, read from its source so the preview,
#: the meta tag checker and the app can never measure the same title differently.
_PAGE_JS = Path(__file__).resolve().parents[2] / "workers" / "ai-crawler-check" / "src" / "page.js"


def _wide_ranges_js() -> str:
    m = re.search(r"const WIDE = (\[\[.*?\]\])", _PAGE_JS.read_text(), re.S)
    if not m:
        raise SystemExit(f"{_PAGE_JS}: no WIDE table; the preview would measure differently from the checker")
    return " ".join(m.group(1).split())


def titles_data() -> dict:
    """The newest homepage title survey (scripts/collect_titles.py)."""
    newest = sorted((Path(__file__).resolve().parents[2] / "data").glob("titles-*.json"))[-1]
    return json.loads(newest.read_text())


def _day(iso: str) -> str:
    import datetime
    d = datetime.date.fromisoformat(iso)
    return f"{d.day} {d:%B %Y}"


def serp_preview() -> Path:
    t = titles_data()
    m = t["summary"]
    lim = t["limits"]
    tmin, tmax, dmin, dmax = lim["title_min"], lim["title_max"], lim["desc_min"], lim["desc_max"]
    when = _day(t["measured"])
    with_title = m["read"] - m["no_title"]
    with_desc = m["read"] - m["no_desc"]
    silent = m["attempted"] - m["read"] - m["refused"]
    n403 = sum(1 for r in t["records"] if not r.get("read") and not r.get("refused") and r["status"] == 403)
    title_cut_pct = round(100 * m["title_over"] / with_title)
    desc_cut_pct = round(100 * m["desc_over"] / with_desc)
    body = rf"""
<p class="lede">Type a title and a meta description to see them as a search result shows them. A result
cuts a title off at about {TITLE_PX} pixels, roughly {tmax} Latin characters, and this preview cuts it
where Docket does, so you can move the important words to the front before anything goes live.</p>

<form class="checker-form serp-form" id="serp" autocomplete="off" novalidate onsubmit="return false">
  <label for="serp-title">Title</label>
  <input id="serp-title" type="text" maxlength="300" spellcheck="true"
         value="Emergency plumber in Grand Rapids, open 24 hours a day | Your Business Name">
  <p class="serp-count" id="serp-title-count" aria-live="polite"></p>
  <label for="serp-desc">Meta description</label>
  <textarea id="serp-desc" rows="3" maxlength="700" spellcheck="true">Burst pipe or no hot water? A licensed plumber at your door within the hour, day or night. Upfront prices, and every repair guaranteed for a year.</textarea>
  <p class="serp-count" id="serp-desc-count" aria-live="polite"></p>
  <label for="serp-url">Page address (optional)</label>
  <input id="serp-url" type="text" inputmode="url" placeholder="yourbusiness.com/emergency-plumber/" spellcheck="false">
</form>

<div class="serp-box" id="serp-box">
  <div class="serp-site"><span id="serp-host">yourbusiness.com</span> <span class="serp-path" id="serp-path"></span></div>
  <div class="serp-title" id="serp-title-out"></div>
  <div class="serp-desc" id="serp-desc-out"></div>
</div>
<div class="serp-copy">
  <button class="btn-ghost" type="button" id="serp-copy">Copy the HTML tags</button>
  <span class="serp-count" id="serp-copied" aria-live="polite"></span>
</div>
{how_it_works([
    "The title and description laid out as a search result, with the cut-off point marked in red",
    f"Each one's width in Docket's units, against {tmin} to {tmax} for a title and {dmin} to {dmax} for a description",
    "The two HTML tags, ready to paste into the page's head",
], steps=["Type or paste a title.", "Type or paste a meta description, and the page address if you like.",
          "Watch the preview. Anything past the red mark will not be shown, so move what matters in front of it."],
   free="Nothing to install, and nothing you type leaves your browser.",
   step_up=('These are words you typed. To see the titles a site really serves, <a href="/download/">Docket</a> '
            "reads every page and reports the missing, repeated and cut-off ones."))}

<h2>Will Google cut off my title?</h2>
<p>If it is wider than about {TITLE_PX} pixels, yes. Docket turns that into a width of {tmax}, counting an
East Asian character as two because it renders about twice as wide as a Latin one. Under {tmin} wide, a
result has little to show. Google can also replace a title it thinks does not describe the page, so a
title that fits is necessary, not sufficient.</p>

<h2>How often well-known sites go over</h2>
<p>On {when}, Docket read the homepages of the {m["attempted"]} well-known sites in its measurement
sample with its own fetcher and width rule. {m["read"]} answered with a page. {silent} did not return one
to a plain request ({n403} of them answered 403, access denied) and {m["refused"]} showed a bot check;
those are left out.</p>
<div class="wrap-tbl"><table class="cmp">
<thead><tr><th></th><th>Title</th><th>Meta description</th></tr></thead>
<tbody>
<tr><td>Inside Docket's range</td><td>{m["title_in_range"]} of {with_title}</td><td>{m["desc_in_range"]} of {with_desc}</td></tr>
<tr><td>Wider, so a result cuts it</td><td>{m["title_over"]} ({title_cut_pct}%)</td><td>{m["desc_over"]} ({desc_cut_pct}%)</td></tr>
<tr><td>Shorter than the range</td><td>{m["title_under"]}</td><td>{m["desc_under"]}</td></tr>
<tr><td>None at all</td><td>{m["no_title"]}</td><td>{m["no_desc"]}</td></tr>
<tr><td>Median width</td><td>{m["title_median"]:g}</td><td>{m["desc_median"]:g}</td></tr>
</tbody></table></div>
<p class="table-note">Homepages only, measured {when}. The sites are not named: the figures are the
point, not who they belong to.</p>
<p>A short title can be right for a name people already type into a search box. It is a poor choice
for a page that has to be found by what it does. A long one loses its end first, so a brand name
added after the words that matter is the cheapest thing to lose.</p>

<h2>How long should a meta description be?</h2>
<p>Docket uses {dmin} to {dmax} wide. Google sets no fixed limit and often writes its own snippet from
the page when the description does not match what someone searched for. Put the reason to click in
the first sentence, so it survives a cut.</p>

<h2>A preview checks words; an audit checks the site</h2>
<p>This shows one title you typed. It cannot tell you that a dozen pages share the same title, that a
template left a page with none, or that the live title differs from the one you meant to publish.
Docket reads every page of a site and reports each of those, with the rest of its {N_CHECKS} checks,
ranked by what to fix first. To check a page that is already live, use the
<a href="/tools/meta-tag-checker/">title and meta tag checker</a>.</p>
{buy_block("tools-serp-preview", try_app="tools-serp-preview-try-free")}

<h2>Related</h2>
<ul>
<li><a href="/how-to/write-title-tags-that-fit/">Write title tags that fit</a></li>
<li><a href="/how-to/write-meta-descriptions/">Write meta descriptions for every page</a></li>
<li><a href="/how-to/fix-duplicate-title-tags/">Fix duplicate title tags</a></li>
<li><a href="/tools/meta-tag-checker/">Title and meta tag checker</a></li>
</ul>

<script>
(function () {{
  var WIDE = {_wide_ranges_js()};
  var TMAX = {tmax}, TMIN = {tmin}, DMAX = {dmax}, DMIN = {dmin};
  function cw(ch) {{ var c = ch.codePointAt(0); for (var i = 0; i < WIDE.length; i++) if (c >= WIDE[i][0] && c <= WIDE[i][1]) return 2; return 1; }}
  function width(s) {{ var n = 0; for (var ch of s) n += cw(ch); return n; }}
  function cut(s, max) {{
    if (width(s) <= max) return {{ shown: s, rest: '' }};
    var n = 0, i = 0, chars = Array.from(s);
    for (; i < chars.length; i++) {{ if (n + cw(chars[i]) > max - 1) break; n += cw(chars[i]); }}
    var shown = chars.slice(0, i).join('');
    var sp = shown.lastIndexOf(' ');
    if (sp > shown.length * 0.6) shown = shown.slice(0, sp);
    return {{ shown: shown.replace(/[\s,|:;\-]+$/, ''), rest: chars.slice(shown.length).join('') }};
  }}
  function verdict(w, lo, hi, what) {{
    if (!w) return {{ t: 'No ' + what + ' yet.', over: false }};
    if (w > hi) return {{ t: w + ' wide. Too long: a result cuts it after about ' + hi + '.', over: true }};
    if (w < lo) return {{ t: w + ' wide. Short: under ' + lo + ' leaves a result little to show.', over: false }};
    return {{ t: w + ' wide. Fits Docket\'s range of ' + lo + ' to ' + hi + '.', over: false }};
  }}
  function el(id) {{ return document.getElementById(id); }}
  function put(box, s, max) {{
    box.textContent = '';
    var c = cut(s, max);
    box.appendChild(document.createTextNode(c.shown));
    if (c.rest) {{ var m = document.createElement('span'); m.className = 'serp-cut'; m.textContent = ' …'; m.title = 'Cut here'; box.appendChild(m); }}
  }}
  var sent = false;
  function update() {{
    var t = el('serp-title').value.replace(/\s+/g, ' ').trim();
    var d = el('serp-desc').value.replace(/\s+/g, ' ').trim();
    var u = el('serp-url').value.trim().replace(/^https?:\/\//i, '');
    var host = u.split('/')[0] || 'yourbusiness.com';
    var path = u.split('/').slice(1).filter(Boolean);
    el('serp-host').textContent = host;
    el('serp-path').textContent = path.length ? '› ' + path.join(' › ') : '';
    put(el('serp-title-out'), t || 'Your title appears here', TMAX);
    put(el('serp-desc-out'), d || 'Your description appears here.', DMAX);
    var vt = verdict(width(t), TMIN, TMAX, 'title'), vd = verdict(width(d), DMIN, DMAX, 'description');
    el('serp-title-count').textContent = vt.t; el('serp-title-count').className = 'serp-count' + (vt.over ? ' over' : '');
    el('serp-desc-count').textContent = vd.t; el('serp-desc-count').className = 'serp-count' + (vd.over ? ' over' : '');
  }}
  function esc(s) {{ return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/"/g, '&quot;'); }}
  ['serp-title', 'serp-desc', 'serp-url'].forEach(function (id) {{
    el(id).addEventListener('input', function () {{
      update();
      if (!sent && window.plausible) {{ sent = true; window.plausible('Checker', {{ props: {{ tool: 'serp' }} }}); }}
    }});
  }});
  el('serp-copy').addEventListener('click', function () {{
    var t = el('serp-title').value.replace(/\s+/g, ' ').trim(), d = el('serp-desc').value.replace(/\s+/g, ' ').trim();
    var tags = '<title>' + esc(t) + '</title>\n<meta name="description" content="' + esc(d) + '">';
    var done = function () {{ el('serp-copied').textContent = 'Copied.'; }};
    if (navigator.clipboard) navigator.clipboard.writeText(tags).then(done, function () {{ el('serp-copied').textContent = tags; }});
    else el('serp-copied').textContent = tags;
  }});
  update();
}})();
</script>
"""
    return render(
        cat="tools", slug="serp-preview",
        title="SERP preview tool: will Google cut off your title?",
        desc=(f"Free search result preview: type a title and meta description and see where a result cuts "
              f"them, measured against {tmax} and {dmax} wide. No sign-up."),
        h1="Search result preview: see where your title gets cut off",
        crumb='<a href="/">Docket</a> / <a href="/tools/">Tools</a> / Search result preview',
        body=body,
        published=t["measured"],
        schema_type="WebPage",
        faq=[
            ("Will Google cut off my title?",
             f"Yes, if it is wider than about {TITLE_PX} pixels, roughly {tmax} Latin characters. On {when} "
             f"{m['title_over']} of {with_title} well-known homepages Docket measured had titles that wide."),
            ("How long should a meta description be?",
             f"Docket uses {dmin} to {dmax} wide. Google sets no fixed limit and may write its own snippet "
             "when the description does not match the search."),
            ("Does the preview send what I type anywhere?",
             "No. The preview runs in your browser and nothing you type is sent to Docket or anyone else."),
        ],
    )


#: The page score: 100, less this much for each finding of that level. Stated on the page.
PROBLEM_COST, WARNING_COST = 12, 5
#: Crawlers the checker asks robots.txt about: the two search engines, then the AI search
#: crawlers that decide whether an assistant can find and quote a page (collect_index.py's
#: CITATION_BOTS). Training crawlers are left out: blocking them is a choice, not a fault.
SEO_SEARCH_AGENTS = ["Googlebot", "Bingbot"]
SEO_CITE_AGENTS = ["OAI-SearchBot", "Claude-SearchBot", "PerplexityBot"]
#: Areas in the order the result lists them, the order they fail in: a page that cannot be
#: crawled gains nothing from a better title.
SEO_AREAS = ["Crawling and indexing", "Security", "Search listing", "Page basics", "AI search",
             "Structured data", "Sharing"]


def field_audits() -> dict:
    return json.loads((Path(__file__).resolve().parents[2] / "data" / "field-audits.json").read_text())


def seo_checker() -> Path:
    fa = field_audits()
    fa_when = _day(fa["date"])
    fa_n = fa["sites"]
    fa_pages = fa["median"]["pages"]
    fa_problems = fa["median"]["problems"]
    fa_least = min(a["problems"] for a in fa["audits"])
    fa_most = max(a["problems"] for a in fa["audits"])
    area_rows = "".join(f"<tr><td>{a}</td><td>{w}</td></tr>" for a, w in [
        ("Crawling and indexing", "Whether the page answers, whether robots.txt lets Googlebot and Bingbot "
         "crawl it, any noindex in the page or its headers, the canonical, and the redirects on the way"),
        ("Security", "Whether the page is served over HTTPS"),
        ("Search listing", f"The title and meta description, measured against {TITLE_MIN} to {TITLE_MAX} and "
         f"{DESC_MIN} to {DESC_MAX} wide, and duplicate tags"),
        ("Page basics", "One main heading, a declared language, and a viewport tag for phones"),
        ("AI search", f"Whether robots.txt lets the {len(SEO_CITE_AGENTS)} AI search crawlers read the page, "
         "the ones behind ChatGPT search, Claude and Perplexity"),
        ("Structured data", "Whether each JSON-LD block is valid and has what a rich result needs"),
        ("Sharing", "The Open Graph and X card tags that decide what a shared link shows"),
    ])
    body = rf"""
<p class="lede">Paste the address of any page to get a score, the problems in each area, and the first
thing to fix with the change to make. It reads the page the way a search engine does and checks its
robots.txt for Googlebot and the AI search crawlers. It takes a few seconds.</p>
{_form("Check this page", "yourbusiness.com/services/")}

<div class="seo-result" id="seo-result" hidden>
  <div class="seo-score-row">
    <p class="seo-score"><span class="seo-score-n" id="seo-score"></span><span class="seo-score-of">/ 100</span></p>
    <p class="seo-score-what" id="seo-counts"></p>
  </div>
  <div class="seo-top" id="seo-top" hidden>
    <p class="seo-top-h">Fix this first</p>
    <p class="seo-top-label" id="seo-top-label"></p>
    <p class="seo-top-detail" id="seo-top-detail"></p>
  </div>
  <div class="wrap-tbl"><table class="cmp" id="seo-areas"><thead><tr><th>Area</th><th>Problems</th><th>Worth fixing</th></tr></thead><tbody></tbody></table></div>
  <details class="seo-all"><summary id="seo-all-sum">Every finding on this page</summary><ul class="findings" id="findings"></ul></details>
  <p class="table-note">The score is 100, less {PROBLEM_COST} for each problem and {WARNING_COST} for each
  thing worth fixing, on this one page. Docket's app scores a whole site across {N_LANES} areas, so its
  number will differ.</p>
</div>
{how_it_works([
    "A score out of 100 for the page, and how many problems it has",
    "Problems counted by area, from crawling and indexing to sharing",
    "The worst one in full, with what it means and the change that fixes it",
], free="Nothing to install, and nothing about the page is stored.",
   steps=["Paste a page that matters: your homepage, a service page or a product page.",
          "Press <strong>Check this page</strong>.",
          "Fix the item at the top first, then check again to watch the score move."],
   step_up=(f'This is one page. <a href="/download/">Docket</a> crawls the whole site and runs {N_CHECKS} '
            "checks, including the ones that only show up between pages, like two pages with one title or a "
            "page nothing links to."))}
{audit_next("tools-seo-checker", what="one page, read once")}

<h2>How do I check my website's SEO for free?</h2>
<p>Start with the pages that earn you money: the homepage, then each service or product page. Paste
each one above. Fix what comes first on each, because the result is in the order things fail: a page
search engines cannot crawl gains nothing from a better title. Then check the whole site, because
most sites have problems no single page shows. Docket's free download crawls every page and shows
your site's score and its top problem in full.</p>

<h2>What this checker looks at</h2>
<div class="wrap-tbl"><table class="cmp"><thead><tr><th>Area</th><th>What it checks on the page</th></tr></thead>
<tbody>{area_rows}</tbody></table></div>
<p>The rules are Docket's own, ported from its engine and tested against it, so this page and the app
give the same answer about the same page.</p>

<h2>How many problems does a real site have?</h2>
<p>More than one page can show. On {fa_when}, Docket audited {fa_n} small-business sites with its app
at the default settings. The median site had {fa_pages:g} pages and {fa_problems:g} problems; the
cleanest had {fa_least} and the worst {fa_most}. Many of them exist only between pages: two pages
with one title, a page that nothing links to, a section reached through a chain of redirects. A
one-page check cannot see those, and that is what the app is for.</p>
{buy_block("tools-seo-checker", try_app="tools-seo-checker-try-free")}

<h2>Related</h2>
<ul>
<li><a href="/learn/seo-audit/">What is an SEO audit?</a></li>
<li><a href="/best/free-seo-audit-tools/">Free SEO audit tools, compared</a></li>
<li><a href="/tools/meta-tag-checker/">Title and meta tag checker</a></li>
<li><a href="/tools/robots-txt-tester/">Robots.txt tester</a></li>
<li><a href="/tools/serp-preview/">Search result preview</a></li>
</ul>

<script>
(function () {{
  var PAGE = {json.dumps(WORKER + "/page")}, CHECK = {json.dumps(WORKER + "/check")};
  var SEARCH = {json.dumps(SEO_SEARCH_AGENTS)}, CITE = {json.dumps(SEO_CITE_AGENTS)};
  var AREAS = {json.dumps(SEO_AREAS)}, PCOST = {PROBLEM_COST}, WCOST = {WARNING_COST};
  {RESULT_JS}
  var form = document.getElementById('checker'), input = document.getElementById('checker-url');
  var status = document.getElementById('checker-status');
  if (!form || !window.fetch) return;
  function say(t) {{ status.textContent = t; }}
  function el(id) {{ return document.getElementById(id); }}
  function get(url) {{
    return fetch(url).then(function (r) {{ return r.json().then(function (j) {{ return {{ ok: r.ok, j: j }}; }}); }})
      .catch(function () {{ return {{ ok: false, j: {{ error: 'The checker could not be reached. Try again in a minute.' }} }}; }});
  }}
  function areaOf(label) {{
    if (/og:|twitter/i.test(label)) return 'Sharing';
    if (/title|description/i.test(label)) return 'Search listing';
    if (/index|canonical|nofollow/i.test(label)) return 'Crawling and indexing';
    return 'Page basics';
  }}
  function robotsItems(j, items) {{
    if (!j || j.error) {{ items.push({{ area: 'Crawling and indexing', level: 'note', label: 'robots.txt was not checked', detail: (j && j.error) || '' }}); return; }}
    if (j.state === 'unavailable' && (j.status === 401 || j.status === 403)) {{
      items.push({{ area: 'Crawling and indexing', level: 'note', label: 'The site refused this checker its robots.txt', detail: 'HTTP ' + j.status + '. Crawler access is unknown, so it is not scored.' }}); return; }}
    if (j.state === 'unreachable') {{
      items.push({{ area: 'Crawling and indexing', level: 'problem', label: 'robots.txt could not be read', detail: j.robots_url + (j.status ? ' answered HTTP ' + j.status : ' did not answer') + '. Crawlers stay out until it can be read. Make it return 200, or 404 if you have no rules.' }}); return; }}
    if (j.state === 'blocked') return;
    var by = {{}}; (j.results || []).forEach(function (r) {{ by[r.agent] = r; }});
    SEARCH.forEach(function (a) {{
      var r = by[a]; if (!r) return;
      if (!r.allowed) items.push({{ area: 'Crawling and indexing', level: 'problem', label: a + ' may not crawl this page', detail: 'robots.txt blocks it' + (r.rule ? ' with "' + r.rule + '"' : '') + '. Remove or narrow that line if the page should appear in search.' }});
      else items.push({{ area: 'Crawling and indexing', level: 'ok', label: a + ' may crawl this page', detail: '' }});
    }});
    var shut = CITE.filter(function (a) {{ return by[a] && !by[a].allowed; }});
    if (shut.length) items.push({{ area: 'AI search', level: 'warning', label: shut.length + ' of ' + CITE.length + ' AI search crawlers are blocked', detail: shut.join(', ') + '. These decide whether ChatGPT search, Claude and Perplexity can find and quote the page. Allow them in robots.txt unless you mean to stay out of AI answers.' }});
    else items.push({{ area: 'AI search', level: 'ok', label: 'AI search crawlers may read this page', detail: CITE.join(', ') }});
  }}
  form.addEventListener('submit', function (e) {{
    e.preventDefault();
    var v = (input.value || '').trim();
    if (!v) {{ say('Enter a page address.'); return; }}
    var path = '/';
    try {{ var u = new URL(/^[a-z]+:\/\//i.test(v) ? v : 'https://' + v); path = (u.pathname || '/') + (u.search || ''); }} catch (err) {{}}
    say('Reading the page and its robots.txt…');
    el('seo-result').hidden = true;
    Promise.all([get(PAGE + '?url=' + encodeURIComponent(v)),
                 get(CHECK + '?url=' + encodeURIComponent(v) + '&path=' + encodeURIComponent(path) + '&agents=' + encodeURIComponent(SEARCH.concat(CITE).join(',')))])
      .then(function (res) {{
        var pg = res[0].j, rb = res[1].j;
        if (!res[0].ok || pg.error) {{ say(pg.error || 'That address could not be checked.'); return; }}
        var items = [];
        if (pg.status && pg.status !== 200) items.push({{ area: 'Crawling and indexing', level: 'problem', label: 'The page answered HTTP ' + pg.status, detail: 'Search engines index pages that answer 200. Fix the address or the server.' }});
        if (/^http:/i.test(pg.final_url || '')) items.push({{ area: 'Security', level: 'problem', label: 'The page is not served over HTTPS', detail: 'Browsers mark it not secure. Serve it over HTTPS and redirect the http:// address to it.' }});
        else items.push({{ area: 'Security', level: 'ok', label: 'Served over HTTPS', detail: '' }});
        var hops = (pg.redirects || []).length;
        if (hops > 1) items.push({{ area: 'Crawling and indexing', level: 'warning', label: hops + ' redirects before the page', detail: 'Each hop costs time and crawl budget. Link straight to ' + pg.final_url + '.' }});
        robotsItems(res[1].ok ? rb : (rb || {{}}), items);
        (pg.meta.findings || []).forEach(function (f) {{ items.push({{ area: areaOf(f.label), level: f.level, label: f.label, detail: f.detail }}); }});
        (pg.jsonld.findings || []).forEach(function (f) {{ items.push({{ area: 'Structured data', level: f.level, label: f.label, detail: f.detail }}); }});
        var np = items.filter(function (f) {{ return f.level === 'problem'; }}).length;
        var nw = items.filter(function (f) {{ return f.level === 'warning'; }}).length;
        el('seo-score').textContent = Math.max(0, 100 - PCOST * np - WCOST * nw);
        el('seo-counts').textContent = (np ? np + ' problem' + (np === 1 ? '' : 's') : 'No problems') + ' and ' + (nw ? nw + ' thing' + (nw === 1 ? '' : 's') + ' worth fixing' : 'nothing else worth fixing') + ' on ' + pg.final_url;
        var rank = {{ problem: 0, warning: 1 }};
        var top = items.filter(function (f) {{ return f.level in rank; }}).sort(function (a, b) {{ return rank[a.level] - rank[b.level] || AREAS.indexOf(a.area) - AREAS.indexOf(b.area); }})[0];
        el('seo-top').hidden = !top;
        if (top) {{ el('seo-top-label').textContent = top.label + ' (' + top.area + ')'; el('seo-top-detail').textContent = top.detail; }}
        var tb = document.querySelector('#seo-areas tbody'); tb.innerHTML = '';
        AREAS.forEach(function (a) {{
          var mine = items.filter(function (f) {{ return f.area === a; }}); if (!mine.length) return;
          var tr = document.createElement('tr');
          [a, mine.filter(function (f) {{ return f.level === 'problem'; }}).length, mine.filter(function (f) {{ return f.level === 'warning'; }}).length].forEach(function (t) {{ var td = document.createElement('td'); td.textContent = t; tr.appendChild(td); }});
          tb.appendChild(tr);
        }});
        renderFindings(el('findings'), items);
        el('seo-all-sum').textContent = 'Every finding on this page (' + items.length + ')';
        el('seo-result').hidden = false;
        var next = el('checker-next'); if (next) next.hidden = false;
        say('Read ' + pg.final_url + (hops ? ' after ' + hops + ' redirect' + (hops === 1 ? '' : 's') : '') + '.');
        if (window.plausible) window.plausible('Checker', {{ props: {{ tool: 'seo', issues: String(np + nw) }} }});
      }});
  }});
}})();
</script>
"""
    return render(
        cat="tools", slug="seo-checker",
        title="Free SEO checker: score any page and see what to fix",
        desc=("Free SEO checker: paste any page for a score out of 100, its problems by area and the first "
              "fix to make. Checks robots.txt for Google and AI crawlers. No sign-up."),
        h1="Free SEO checker",
        crumb='<a href="/">Docket</a> / <a href="/tools/">Tools</a> / SEO checker',
        body=body,
        published="2026-11-06",
        schema_type="WebPage",
        faq=[
            ("Is this SEO checker free?",
             "Yes. There is no sign-up and nothing to install. It checks one page at a time, as often as you like."),
            ("How is the score worked out?",
             f"It starts at 100 and loses {PROBLEM_COST} for each problem and {WARNING_COST} for each thing worth "
             "fixing on the page. The rule is the same for every page, so a fix always moves it."),
            ("Can it check my whole website?",
             f"It checks one page. Docket's app crawls the whole site with {N_CHECKS} checks, and its free "
             "download shows the site's score and the top problem in full."),
        ],
    )


BUILDERS = [hub, robots_tester, meta_checker, jsonld_checker, serp_preview, seo_checker]


def build_all() -> list[Path]:
    return [b() for b in BUILDERS]


if __name__ == "__main__":
    for p in build_all():
        print(p)
