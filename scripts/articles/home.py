#!/usr/bin/env python3
"""The homepage — a landing page, not an article.

The first version was prose in the article template and read like a blog post.
This one is a real landing page: a hero with a working product mockup, a
before/after that shows the actual difference rather than describing it, a
feature grid, and a chart drawn from the measured Index data.

The product visual is **HTML, not a screenshot**. It stays sharp at any pixel
density, weighs nothing, follows the page theme, and cannot go stale the way a
PNG of last month's UI does. It is a faithful replica of the real results view,
including the numbers, which come from an actual audit.

Two things are kept from the first version because they are the differentiator,
not decoration: the section on what Scout cannot do, and the Index numbers. A
homepage that concedes nothing reads as marketing.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from render import DMG, DMG_SIZE, N_CHECKS, N_LANES, render  # noqa: E402

DATA = Path(__file__).resolve().parents[2] / "data" / "index-2026-08.json"


def _index() -> dict:
    """Measured figures, or empty so the page simply omits the claim."""
    if not DATA.exists():
        return {}
    d = json.loads(DATA.read_text())
    s = d["summary"]
    return {
        "n": s["n"],
        "cit_pct": round(100 * s["blocking_any_citation_bot"] / s["n"]),
        "by_cat": s["by_category"],
        "perplexity": s["by_bot"]["PerplexityBot"],
        "oai": s["by_bot"]["OAI-SearchBot"],
        "collected": d["collected"][:10],
    }


def _ico(path: str) -> str:
    return (f'<svg viewBox="0 0 24 24" width="19" height="19" fill="none" '
            f'stroke="currentColor" stroke-width="1.9" stroke-linecap="round" '
            f'stroke-linejoin="round">{path}</svg>')


ICONS = {
    "order": _ico('<path d="M3 6h13M3 12h9M3 18h5"/><path d="M17 14l3 3 4-5"/>'),
    "ai": _ico('<path d="M12 3v3M12 18v3M3 12h3M18 12h3M5.6 5.6l2.1 2.1M16.3 16.3l2.1 2.1'
               'M5.6 18.4l2.1-2.1M16.3 7.7l2.1-2.1"/><circle cx="12" cy="12" r="3.4"/>'),
    "cart": _ico('<circle cx="9" cy="20" r="1.4"/><circle cx="18" cy="20" r="1.4"/>'
                 '<path d="M2 3h3l2.5 12h11L21 7H6"/>'),
    "pin": _ico('<path d="M12 21s7-6.3 7-11a7 7 0 1 0-14 0c0 4.7 7 11 7 11z"/>'
                '<circle cx="12" cy="10" r="2.6"/>'),
    "lock": _ico('<rect x="4" y="10" width="16" height="10" rx="2"/>'
                 '<path d="M8 10V7a4 4 0 0 1 8 0v3"/>'),
    "clock": _ico('<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3.2 2"/>'),
    "doc": _ico('<path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8z"/>'
                '<path d="M14 3v5h5M9 13h6M9 17h4"/>'),
    "brand": _ico('<path d="M12 2.6l7.4 3.1v5.4c0 4.5-3.1 8.5-7.4 9.9'
                  '-4.3-1.4-7.4-5.4-7.4-9.9V5.7z"/><path d="M9.3 12l1.9 1.9 3.6-3.9"/>'),
    "eye": _ico('<path d="M2 12s3.6-6.5 10-6.5S22 12 22 12s-3.6 6.5-10 6.5S2 12 2 12z"/>'
                '<circle cx="12" cy="12" r="2.8"/>'),
}


def _mockup() -> str:
    """An HTML replica of the results view. Numbers are from a real audit."""
    lanes = [
        ("Crawlability", 100, "var(--ok)"), ("On-page SEO", 93, "var(--ok)"),
        ("Copy & content", 71, "var(--warn)"), ("Conversion", 78, "var(--warn)"),
        ("Brand", 84, "var(--ok)"), ("Tracking", 63, "var(--amber)"),
    ]
    lane_html = "".join(
        f'<div class="mock-lane"><div class="mock-lane-top">'
        f'<span class="mock-lane-name">{name}</span>'
        f'<span class="mock-lane-score" style="color:{col}">{v}</span></div>'
        f'<div class="mock-lane-bar"><i style="width:{v}%;background:{col}"></i></div></div>'
        for name, v, col in lanes
    )
    circ = 2 * 3.14159 * 26
    filled = circ * 0.892
    return f"""
<div class="mock" role="img" aria-label="Scout showing an audit scoring 89 out of 100 with per-area scores and a ranked fix list">
<div class="mock-bar"><span class="mock-dot"></span><span class="mock-dot"></span>
<span class="mock-dot"></span><span class="mock-title">Scout</span></div>
<div class="mock-body">
  <div class="mock-top">
    <svg width="66" height="66" viewBox="0 0 66 66" aria-hidden="true">
      <circle cx="33" cy="33" r="26" fill="none" stroke="rgba(255,255,255,.09)" stroke-width="6"/>
      <circle cx="33" cy="33" r="26" fill="none" stroke="var(--ok)" stroke-width="6"
        stroke-linecap="round" stroke-dasharray="{filled:.1f} {circ:.1f}"
        transform="rotate(-90 33 33)"/>
      <text x="33" y="37" text-anchor="middle" fill="var(--text)"
        font-size="17" font-weight="700" font-family="-apple-system,sans-serif">89</text>
    </svg>
    <div>
      <div class="mock-verdict">Solid foundations with a handful of meaningful gaps worth closing.</div>
      <div class="mock-chips">
        <span class="mock-chip" style="background:rgba(255,122,110,.16);color:#ff9c92">2 high</span>
        <span class="mock-chip" style="background:rgba(251,191,36,.16);color:#fbbf24">5 medium</span>
        <span class="mock-chip" style="background:rgba(255,255,255,.07);color:var(--text-dim)">9 low</span>
      </div>
    </div>
  </div>
  <div class="mock-lanes">{lane_html}</div>
  <div class="mock-find">
    <div class="mock-find-h"><span class="mock-rank">1</span>Analytics is missing from 39 of 40 pages</div>
    <p class="mock-find-p">Sessions break when a visitor crosses an untagged page, so traffic
    gets misattributed to direct. <strong style="color:var(--amber-light)">Fix:</strong> move the
    tag into the shared template.</p>
  </div>
</div></div>"""


def _index_chart(m: dict) -> str:
    if not m:
        return ""
    order = ["news", "reference", "ecommerce", "local", "saas", "seo-tools", "nonprofit"]
    label = {"news": "News &amp; media", "reference": "Reference", "ecommerce": "Ecommerce",
             "local": "Local business", "saas": "SaaS", "seo-tools": "SEO tools",
             "nonprofit": "Nonprofit"}
    rows = ""
    for key in order:
        v = m["by_cat"].get(key)
        if not v:
            continue
        rows += (f'<div class="bar-row"><span class="bar-lbl">{label[key]}</span>'
                 f'<span class="bar-track"><i class="bar-fill" style="width:{max(v["pct"],1.2)}%"></i></span>'
                 f'<span class="bar-val">{v["pct"]:.0f}%</span></div>')
    return f"""
<div class="chart">
{rows}
<p class="chart-note">Share of sites in each category blocking at least one AI <em>search</em>
crawler. {m['n']} sites with a robots.txt, measured {m['collected']} with Scout's own parser.
The script and the site list ship with the dataset — re-run it and check.</p>
</div>"""


def body() -> str:
    m = _index()
    chart = _index_chart(m)

    index_line = ""
    if m:
        index_line = (
            f"<strong>{m['cit_pct']}% of the {m['n']} major sites we measured block at least "
            f"one AI search crawler.</strong> Among those blocking any AI crawler, roughly "
            f"three quarters also blocked the ones that decide whether they appear in "
            f"ChatGPT — almost certainly without meaning to."
        )

    return f"""
<!-- ================= HERO ================= -->
<section class="hero-sec"><div class="wrap-wide hero-grid">
<div>
  <span class="eyebrow">{N_CHECKS} checks · {N_LANES} areas · runs on your Mac</span>
  <h1 class="hero-h1">Audit your SEO, copy, conversion and brand
  <em style="display:block">then fix it in the right order</em></h1>
  <p class="hero-sub">Point Scout at any website. It crawls, then runs {N_CHECKS} checks across
  technical SEO, content and copy, conversion, brand consistency, AI search visibility and
  campaign tracking — and hands you one ranked plan with the exact markup to paste. It is not
  four tools. One download, and nothing leaves your machine.</p>
  <div class="hero-cta">
    <a class="btn btn-lg" href="{DMG}">Download for Mac</a>
    <a class="btn-ghost btn-lg" href="/index/">See the Index →</a>
  </div>
  <p class="hero-note">macOS 12+ · Apple Silicon · ~16&nbsp;MB · no account, no subscription</p>
</div>
{_mockup()}
</div></section>

<!-- ================= THE DIFFERENCE ================= -->
<section class="sec"><div class="wrap-wide">
<div class="sec-head">
  <h2>Every other tool hands you a list</h2>
  <p>Semrush publishes 140+ checkpoints. Ahrefs lists 170+. Neither tells you what to do
  first — and ordering is the hard part.</p>
</div>
<div class="split">
  <div class="split-col">
    <div class="split-tag">What you usually get</div>
    <ul class="split-list">
      <li><span class="n">—</span> 412 pages have a short title</li>
      <li><span class="n">—</span> 38 pages missing meta description</li>
      <li><span class="n">—</span> 1 page set to noindex</li>
      <li><span class="n">—</span> 96 images without alt text</li>
      <li><span class="n">—</span> 12 redirect chains</li>
      <li><span class="n">—</span> …and 160 more rows</li>
    </ul>
  </div>
  <div class="split-col good">
    <div class="split-tag">What Scout gives you</div>
    <div class="split-phase">Stop the bleeding</div>
    <ul class="split-list">
      <li><span class="n">1</span> The homepage is set to noindex — remove it today</li>
    </ul>
    <div class="split-phase">Quick wins · under an hour</div>
    <ul class="split-list">
      <li><span class="n">2</span> Analytics missing from 39 of 40 pages</li>
      <li><span class="n">3</span> OAI-SearchBot blocked in robots.txt</li>
    </ul>
    <div class="split-phase">Build</div>
    <ul class="split-list">
      <li><span class="n">4</span> Add LocalBusiness schema to service pages</li>
    </ul>
  </div>
</div>
</div></section>

<!-- ================= THREE LANES ================= -->
<section class="sec"><div class="wrap-wide">
<div class="sec-head">
  <h2>Four things crawler tools don't audit</h2>
  <p>Technical SEO is table stakes, and it is all most tools do. These four are where the
  money actually leaks — and each one is a separate subscription anywhere else.</p>
</div>
<div class="grid-3">
  <div class="card"><div class="card-ico">{ICONS['ai']}</div>
    <h3>AI search visibility</h3>
    <p>Whether ChatGPT, Perplexity and Claude can reach and cite you — checked per crawler,
    because <code>GPTBot</code> trains models and <code>OAI-SearchBot</code> builds the index
    ChatGPT answers from. Blocking them is not the same decision.</p></div>
  <div class="card"><div class="card-ico">{ICONS['cart']}</div>
    <h3>Conversion &amp; landing pages</h3>
    <p>Calls to action, the above-the-fold promise, form friction, social proof, whether the
    price is findable, and whether the headline matches what the search result promised.</p></div>
  <div class="card"><div class="card-ico">{ICONS['brand']}</div>
    <h3>Brand consistency</h3>
    <p>Whether your company name is spelled the same way in your title tags, your schema, your
    og:site_name and your logo alt text — because that is where a knowledge panel and an AI
    citation get it from. Plus typeface and palette sprawl, and whether every page makes the
    same promise or a different one.</p></div>
  <div class="card"><div class="card-ico">{ICONS['pin']}</div>
    <h3>Local business SEO</h3>
    <p>NAP consistency, LocalBusiness schema and its subtypes, opening hours, geo signals,
    review markup — and it knows a software company with an office is not a local business.</p></div>
</div>
</div></section>

<!-- ================= THE INDEX ================= -->
<section class="sec"><div class="wrap-wide">
<div class="sec-head">
  <h2>We measured who is blocking AI search</h2>
  <p>{index_line}</p>
</div>
{chart}
<p style="text-align:center;margin-top:1.6rem">
<a class="btn-ghost" href="/index/">Read the full Index →</a></p>
</div></section>

<!-- ================= FEATURES ================= -->
<section class="sec"><div class="wrap-wide">
<div class="sec-head"><h2>What you get</h2></div>
<div class="grid-3">
  <div class="card"><div class="card-ico">{ICONS['order']}</div>
    <h3>A sequence, not a pile</h3>
    <p>Every finding ranked by impact against effort, in four phases. There is always a
    defensible first task.</p></div>
  <div class="card"><div class="card-ico">{ICONS['doc']}</div>
    <h3>Client-ready PDF</h3>
    <p>Designed to send, not rebuild. Score, scorecard, ranked plan, paste-ready markup — and
    a scope page saying exactly what was and was not measured.</p></div>
  <div class="card"><div class="card-ico">{ICONS['clock']}</div>
    <h3>Scheduled monitoring</h3>
    <p>Re-audits on a cadence and tells you what changed. Regressions first — a site that was
    clean and broke is the thing you need to know.</p></div>
  <div class="card"><div class="card-ico">{ICONS['eye']}</div>
    <h3>Competitor comparison</h3>
    <p>Where you lead and trail area by area, plus the issues <em>every</em> rival has already
    fixed. That list sells the work for you.</p></div>
  <div class="card"><div class="card-ico">{ICONS['lock']}</div>
    <h3>Nothing is uploaded</h3>
    <p>No account, no telemetry, no licence server. The only requests Scout makes are to the
    site you are auditing.</p></div>
  <div class="card"><div class="card-ico">{ICONS['order']}</div>
    <h3>A CLI that gates deploys</h3>
    <p><code>scout audit</code> exits non-zero on a critical issue, so CI fails the build if
    someone ships a noindex.</p></div>
</div>
</div></section>

<!-- ================= COMPARISON ================= -->
<section class="sec"><div class="wrap-wide">
<div class="sec-head"><h2>What it costs to run</h2>
<p>Cloud tools meter crawls, which quietly makes you ration audits.</p></div>
<div class="wrap-tbl"><table class="cmp">
<thead><tr><th>Tool</th><th>Price</th><th>Runs</th><th>Output</th></tr></thead>
<tbody>
<tr><td>Scout</td><td>One-time</td><td class="yes">Your Mac</td><td>Ranked fix plan</td></tr>
<tr><td>Ahrefs Site Audit</td><td>$129–$499/mo</td><td>Cloud, metered</td><td>170+ issues</td></tr>
<tr><td>Semrush Site Audit</td><td>$139–$499/mo</td><td>Cloud, metered</td><td>140+ checkpoints</td></tr>
<tr><td>Sitebulb</td><td>$13.50–$34/mo</td><td>Local + cloud</td><td>Visual issue report</td></tr>
<tr><td>Screaming Frog</td><td>£199/yr</td><td>Your machine</td><td>Raw crawl data</td></tr>
</tbody></table></div>
<p style="text-align:center;margin-top:1.4rem"><a class="btn-ghost" href="/vs/">See the honest
comparisons →</a></p>
</div></section>

<!-- ================= LIMITS ================= -->
<section class="sec"><div class="wrap-wide" style="max-width:44rem">
<div class="sec-head"><h2>What Scout cannot do</h2>
<p>Because finding out later is worse, and a tool that claims everything is worth less than
one that draws a line.</p></div>
<div class="grid-3">
  <div class="card"><h3>Keywords and backlinks</h3><p>That needs a crawled index of the web —
  bought, not built. Use Ahrefs or Semrush for research; they are the right tool and we are
  not going to pretend otherwise.</p></div>
  <div class="card"><h3>Non-English copy checks</h3><p>Copy-quality checks are English-only.
  On other languages they stand down and the report says which ones did. Everything
  technical works in any language.</p></div>
  <div class="card"><h3>Windows and Intel</h3><p>Apple Silicon, macOS 12 or later. There is
  no other build.</p></div>
</div>
<p style="text-align:center;margin-top:1.5rem;font-size:.95rem;color:var(--text-dim)">
Three things that used to be on this list are not any more —
<a href="/learn/javascript-rendering/">JavaScript rendering, tag manager contents and
browser-measured timings</a>.</p>
</div></section>

<!-- ================= FAQ ================= -->
<section class="sec"><div class="wrap" style="max-width:44rem">
<div class="sec-head"><h2>Questions</h2></div>
<div class="faq-item"><h3>Is Scout free?</h3>
<p>It is a one-time download. No subscription, no crawl credits, no per-seat pricing — audit
as many sites as you like.</p></div>
<div class="faq-item"><h3>Does it send my site data anywhere?</h3>
<p>No. The audit runs on your Mac and the only network requests are to the site you are
auditing. No account, no telemetry.</p></div>
<div class="faq-item"><h3>How is it different from Screaming Frog?</h3>
<p>Screaming Frog gives raw crawl data and leaves interpretation to you. Scout ranks findings
and gives you an ordered plan with markup to paste. Screaming Frog renders JavaScript and
supports custom XPath extraction; Scout does not.</p></div>
<div class="faq-item"><h3>Can it tell me whether ChatGPT can see my site?</h3>
<p>Yes — per crawler, distinguishing search crawlers from training crawlers, plus whether your
pages render server-side, since most AI crawlers do not run JavaScript.</p></div>
<div class="faq-item"><h3>Does it track keyword rankings?</h3>
<p>No. Ranking and backlink data need a crawled index of the whole web. Scout audits what is
on your site and how it is configured.</p></div>
</div></section>

<!-- ================= CTA ================= -->
<section class="cta-band"><div class="wrap">
<h2>Audit your site in about a minute</h2>
<p>Download it, type a domain, press Run. There is no onboarding because none is needed.</p>
<a class="btn btn-lg" href="{DMG}">Download Scout for Mac</a>
</div></section>
"""


FAQ = [
    ("Is Scout free?",
     "Scout is a one-time download for macOS. There is no subscription, no crawl credits and "
     "no per-seat pricing — you can audit as many sites as you like."),
    ("Does Scout send my site data anywhere?",
     "No. The audit runs entirely on your Mac. The only network requests Scout makes are to "
     "the site you are auditing. There is no telemetry and no account."),
    ("How is Scout different from Screaming Frog?",
     "Screaming Frog gives you raw crawl data and leaves the interpretation to you. Scout "
     "ranks every finding by impact against effort and gives you an ordered plan with the "
     "exact markup to paste. Screaming Frog renders JavaScript and supports custom XPath "
     "extraction; Scout does not."),
    ("Can Scout tell me if ChatGPT can see my website?",
     "Yes. Scout checks each AI crawler separately — OAI-SearchBot for ChatGPT Search, "
     "PerplexityBot, Claude-SearchBot and Google-Extended — and distinguishes them from "
     "training crawlers like GPTBot, which many sites block deliberately."),
    ("Does Scout track keyword rankings?",
     "No. Ranking and backlink data require a crawled index of the entire web, which is bought "
     "rather than built. Scout audits what is on your site and how it is configured."),
]


def build() -> Path:
    return render(
        cat="", slug="",
        title="Scout — SEO, copy, conversion and brand audits for Mac",
        desc=(f"Scout audits any website on your Mac: {N_CHECKS} checks across SEO, copy, brand, "
              "data, local visibility, AI search visibility and marketing conversion. Ranked "
              "fix plan, client-ready PDF, one-time price, nothing uploaded."),
        h1="SEO audits that tell you what to fix, in order",
        crumb="Scout for Mac",
        body=body(),
        schema_type="WebPage",
        faq=FAQ,
        landing=True,
    )


if __name__ == "__main__":
    print(build())
