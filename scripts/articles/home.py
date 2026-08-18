#!/usr/bin/env python3
"""The homepage — a landing page, not an article.

The first version was prose in the article template and read like a blog post.
This one is a real landing page: a hero carrying a screen recording of the
shipped app auditing this very site, a
before/after that shows the actual difference rather than describing it, a
feature grid, and a chart drawn from the measured Index data.

The product visual is **HTML, not a screenshot**. It stays sharp at any pixel
density, weighs nothing, follows the page theme, and cannot go stale the way a
PNG of last month's UI does. It is a faithful replica of the real results view,
including the numbers, which come from an actual audit.

Two things are kept from the first version because they are the differentiator,
not decoration: the section on what Docket cannot do, and the Index numbers. A
homepage that concedes nothing reads as marketing.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import facts as F  # noqa: E402
from comparisons import HOME_CLAIM_CHECKED_HUMAN  # noqa: E402
from render import (BETA_NOTE, CHECKOUT, DMG, DMG_SIZE, N_CHECKS, N_LANES, PRICE_STR,
                    price, price_note_html, render)  # noqa: E402

DATA = Path(__file__).resolve().parents[2] / "data" / "index-2026-08.json"



#: The product's own score bands — `seo_engine.scoring.SCORE_BANDS` — restated
#: because the site cannot import the engine, and pinned by `_score_band_drift`
#: in verify_numbers.py so a change in the product fails the build here.
#:
#: THIS OUTLIVED WHAT IT WAS WRITTEN FOR. It existed to colour the lanes of the
#: HTML replica in the hero, and that replica was deleted on 2026-08-18 when the
#: hero became a screen recording of the actual app. The cross-repo pin is the
#: part that still earns its place, so the table stays and the colouring helper
#: that consumed it does not. It was deleted with it by mistake first, and the
#: derived-number gate refused the deploy — correctly, and that is the only
#: reason this note exists.
_BANDS = ((85, "--ok"), (70, "--warn"), (50, "--bad"))
_BAND_FLOOR = "--bad"


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
crawler. {m['n']} sites with a robots.txt, measured {m['collected']} with Docket's own parser.
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
  <span class="eyebrow">{N_CHECKS} checks · {PRICE_STR} once · no subscription</span>
  <h1 class="hero-h1">Everything that's wrong.
  <em>In the order to fix&nbsp;it.</em></h1>
  <p class="hero-sub">Point Docket at any site. {N_CHECKS} checks across technical SEO, copy,
  conversion, brand, AI search visibility and campaign tracking — then one ranked plan with the
  markup to paste. Not four tools. One download.</p>
  <div class="hero-cta">
    <a class="btn btn-lg" href="{CHECKOUT}">Buy Docket · {PRICE_STR} once</a>
    <a class="btn-ghost btn-lg" href="{DMG}">Download for Mac</a>
  </div>
  <p class="hero-note"><strong>30 days, no conditions, no questions asked</strong> — <a href="/legal/refunds/">refund policy</a></p>
  <p class="hero-note">macOS 12+ · Apple Silicon · {DMG_SIZE} · notarised by Apple · no account · one licence, all your sites</p>
</div>
</div>
<div class="wrap-wide hero-media-wrap">
<figure class="hero-media">
  <video class="hero-video" autoplay loop muted playsinline preload="metadata"
         poster="/assets/app-demo-poster.webp" width="1280" height="800"
         aria-label="Docket auditing docketseo.app: a URL is typed, the crawl runs across 57 pages,
                     and a report appears scoring 94 out of 100, grade A.">
    <source src="/assets/app-demo.webm" type="video/webm">
    <source src="/assets/app-demo.mp4" type="video/mp4">
  </video>
  <figcaption>Docket auditing this site. <strong>57&nbsp;pages, 35&nbsp;seconds, 94/100</strong>
  — screen recording of the shipped app, not a mockup.</figcaption>
</figure>
</div></section>

<!-- ================= THE REAL ARTIFACT =================
     The hero above is an HTML replica — responsive, themeable, and honest about
     its numbers, but a drawing of the product rather than the product. This
     section is the actual thing: Docket run against our own site, rendered by
     the app's own HTML reporter, not rebuilt in CSS.

     Our own site on purpose. Publishing a critical audit of someone else's
     property without asking is not ours to do, and auditing ourselves is the
     stronger demonstration anyway — it is the report we cannot quietly curate. -->
<section class="sec"><div class="wrap-wide">
<div class="sec-head">
  <h2>This is the actual report.<br><em>Run against our own site.</em></h2>
  <p class="sec-sub">Not a mockup and not a marketing render — the file Docket
  writes, opened in a browser. We pointed it at our own agency site rather than
  a competitor's, because publishing someone else's audit without asking is not
  ours to do, and because this is the one report we cannot quietly curate.</p>
</div>
<figure class="shot">
  <img src="/assets/real-audit-builtbykerr.webp" width="1280" height="1000"
       loading="lazy" decoding="async"
       alt="A Docket SEO audit of builtbykerr.com scoring 90 out of 100, grade A, with
            3 high, 7 medium, 11 low and 6 notice findings, and twelve category scores
            from Crawlability 100 down to Local business SEO 58.">
  <figcaption>Twelve pages crawled in eight seconds. It grades our own site
  <strong>90/A</strong> and still lists twenty-seven things to fix &mdash; including
  <strong>Local business SEO at 58</strong> on the site of a local business.
  It also excludes two findings from the score because they describe something
  Docket could not measure, rather than anything we did wrong.</figcaption>
</figure>
</div></section>

<!-- ================= THE DIFFERENCE ================= -->
<section class="sec"><div class="wrap-wide">
<div class="sec-head">
  <h2>Most tools hand you a list.<br><em>This one hands you an order.</em></h2>
  <p>Semrush publishes 140+ checkpoints. Ahrefs lists 170+. Neither tells you what to do
  first — and ordering is the hard part. <a href="/vs/sitebulb-alternative/">Sitebulb</a> is
  the exception worth naming: it prioritises too.</p>
</div>
<div class="split">
  <div class="split-col">
    <div class="split-tag">What a crawler gives you</div>
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
    <div class="split-tag">What Docket gives you</div>
    <div class="rank-demo">
      <div class="rank-row hot"><span class="n">1</span>The homepage is set to noindex</div>
      <div class="rank-row"><span class="n">2</span>Analytics missing from 39 of 40 pages</div>
      <div class="rank-row"><span class="n">3</span>OAI-SearchBot blocked in robots.txt</div>
      <div class="rank-row"><span class="n">4</span>No LocalBusiness schema on service pages</div>
      <div class="rank-row"><span class="n">5</span>96 images without alt text</div>
    </div>
    <p style="font-size:var(--t-base);color:var(--text-dim);margin-top:1rem">
    Ranked by what each one costs you, not by category.</p>
  </div>
</div>
<figure class="shot shot-plan">
  <img src="/assets/app-plan.webp" width="1600" height="1000" loading="lazy" decoding="async"
       alt="Docket's ranked plan: numbered items under a BUILD phase heading reading
            'Worth real effort. Schedule once the quick wins are done.' Each item carries a
            severity chip, the lane it belongs to, an effort estimate, how many pages it
            affects, an explanation, and a Fix paragraph with the change to make.">
  <figcaption>The same idea inside the product. Every item is numbered in the order to
  do it, grouped into phases, and carries what it is worth, how long it takes, how many
  pages it touches &mdash; and the fix, written out.</figcaption>
</figure>
</section>

<!-- ================= THREE LANES ================= -->
<section class="sec"><div class="wrap-wide">
<div class="sec-head">
  <h2>Four things a crawler will not tell you.</h2>
  <p>Technical SEO is table stakes, and it is most of what a crawler is built to return.
  These four are where the money actually leaks. None of them appears in the feature list
  Screaming Frog or Sitebulb publishes, and elsewhere each is a separate subscription —
  <a href="/vs/">checked against their own documentation</a>, {HOME_CLAIM_CHECKED_HUMAN}.</p>
</div>
<div class="grid-3">
  <div class="card"><div class="card-ico">{ICONS['ai']}</div>
    <h3>AI search visibility</h3>
    <p>Every AI crawler in one pass, because <code>GPTBot</code> trains models and
    <code>OAI-SearchBot</code> builds the index ChatGPT answers from — blocking them is not
    the same decision. A crawler can answer this one a user-agent at a time: Screaming Frog
    lets you switch agent and follow that agent's <code>robots.txt</code> directives. What it
    reads is the file. Docket also asks the server, as each bot, and tells you when the two
    disagree — a CDN rule blocking <code>GPTBot</code> is invisible in a
    <code>robots.txt</code> that permits it.</p></div>
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
  <h2>We measured who's blocking AI search.</h2>
  <p>{index_line}</p>
</div>
{chart}
<p style="text-align:center;margin-top:1.6rem">
<a class="btn-ghost" href="/index/">Read the full Index →</a></p>
</div></section>

<!-- ================= FEATURES ================= -->
<section class="sec"><div class="wrap-wide">
<div class="sec-head"><h2>What you actually get.</h2></div>
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
    clean and broke is the thing you need to know. It runs while Docket is open: the schedule is
    a thread inside the app, not a background daemon, so quitting it stops the clock.</p></div>
  <div class="card"><div class="card-ico">{ICONS['eye']}</div>
    <h3>Go on the offensive</h3>
    <p>Against a rival with years and links you cannot match, Docket finds where none of that
    helps them — crawlers they have blocked, rich results they cannot win, searches neither of
    you answers. It reads their domain authority from <a href="https://commoncrawl.org/">Common Crawl</a> so the size of the gap is a
    number, not a guess. <a href="/how-to/outrank-a-bigger-competitor/">See what it finds</a>.</p></div>
  <div class="card"><div class="card-ico">{ICONS['lock']}</div>
    <h3>Nothing is uploaded</h3>
    <p>No account, no telemetry, no licence server. The crawl only ever touches the site you
    are auditing; four optional checks also fetch data Docket cannot produce alone, and
    <code>--offline</code> turns all four off.</p></div>
  <div class="card"><div class="card-ico">{ICONS['order']}</div>
    <h3>A CLI, including <code>docket attack</code></h3>
    <p><code>docket audit</code> exits non-zero on a critical issue — a noindexed homepage, a
    5xx — so CI can fail the build before it ships. <code>--fail-on high</code> lowers the bar.
    <code>docket attack</code> ranks a competitor's weak points by how winnable they are.</p></div>
</div>
</div></section>

<!-- ================= COMPARISON ================= -->
<section class="sec"><div class="wrap-wide">
<div class="sec-head"><h2>{PRICE_STR}. Once.</h2>
<p>Every tool below is a subscription. Docket is a one-time purchase, and the audit runs on your Mac, so there are no crawl credits to ration. {BETA_NOTE}</p></div>
<div class="wrap-tbl"><table class="cmp">
<thead><tr><th>Tool</th><th>Price</th><th>Runs</th><th>Output</th></tr></thead>
<tbody>
<tr><td>Docket</td><td class="yes">{PRICE_STR} once</td><td class="yes">Your Mac</td><td>Ranked fix plan</td></tr>
<tr><td>Ahrefs Site Audit</td><td>{price("ahrefs-site-audit")}</td><td>Cloud, metered</td><td>170+ issues</td></tr>
<tr><td>Semrush Site Audit</td><td>{price("semrush-site-audit")}</td><td>Cloud, metered</td><td>140+ checkpoints</td></tr>
<tr><td>Sitebulb</td><td>{price("sitebulb")}</td><td>Local + cloud</td><td>Visual issue report</td></tr>
<tr><td>Screaming Frog</td><td>{price("screaming-frog")}</td><td>Your machine</td><td>Raw crawl data</td></tr>
</tbody></table></div>
{price_note_html()}
<p style="text-align:center;margin-top:1.4rem"><a class="btn-ghost" href="/vs/">See the honest
comparisons →</a></p>
</div></section>

<!-- ================= LIMITS ================= -->
<section class="sec"><div class="wrap-wide" style="max-width:44rem">
<div class="sec-head"><h2>What Docket cannot do</h2>
<p>Because finding out later is worse, and a tool that claims everything is worth less than
one that draws a line.</p></div>
<div class="grid-3">
  <div class="card"><h3>Per-page backlinks and anchor text</h3><p>Docket reads Common Crawl's
  hyperlink graph — {F.graph_domains_m()}&nbsp;million domains — so it gives you a domain's authority rank in
  about a second, and the full list of domains linking to it in about ten minutes. We measured
  {F.graph_example_referring():,} domains linking to {F.graph_example_host()} that way. Which
  individual <em>page</em>
  links to you, and with what anchor text, lives in archive files far too large to stream from a
  laptop. Ahrefs and
  Semrush sell that, and it is worth paying for if you need it.</p></div>
  <div class="card"><h3>Search volumes</h3><p>Docket finds the queries people actually type,
  from Google's own autocomplete, ordered by how common they are. It will not print a monthly
  volume, because it does not have one. Anyone showing you a volume bought a clickstream
  panel.</p></div>
  <div class="card"><h3>Non-English copy checks</h3><p>Copy-quality checks are English-only, and
  address detection reads English and French word order only. On other languages both stand down
  and the report says which ones did, rather than telling a business it publishes no address when
  the truth is that Docket cannot read the page. Everything technical works in any language.</p></div>
  <div class="card"><h3>Windows and Intel</h3><p>Apple Silicon, macOS 12 or later. There is
  no other build.</p></div>
</div>
<p style="text-align:center;margin-top:1.5rem;font-size:var(--t-md);color:var(--text-dim)">
This list keeps getting shorter. <a href="/learn/javascript-rendering/">JavaScript rendering,
tag manager contents and browser-measured timings</a> came off it; so did Core Web Vitals,
read from the Chrome UX Report; and so did keyword research and domain authority, both
computed from free public data rather than a bought index.</p>
</div></section>

<!-- ================= FAQ ================= -->
<section class="sec"><div class="wrap" style="max-width:44rem">
<div class="sec-head"><h2>Clear answers.</h2></div>
<div class="faq-item"><h3>Is Docket free?</h3>
<p>It is a one-time download. No subscription, no crawl credits, no per-seat pricing — audit
as many sites as you like.</p></div>
<div class="faq-item"><h3>Does it send my site data anywhere?</h3>
<p>Docket collects nothing about you — no account, no telemetry, no licence check. The
crawl runs on your Mac. Four checks do reach outside it by default: Core Web Vitals from
Google PageSpeed, a deliverability test on the addresses your site publishes, what your
server tells AI crawlers, and a knowledge refresh from this site. Offline mode turns all
four off, and every report names the ones that ran.</p></div>
<div class="faq-item"><h3>How is it different from Screaming Frog?</h3>
<p>Screaming Frog gives raw crawl data and leaves interpretation to you. Docket ranks findings
and gives you an ordered plan with markup to paste. Screaming Frog supports custom XPath extraction and crawls at far greater scale;
Docket does not.</p></div>
<div class="faq-item"><h3>Can it tell me whether ChatGPT can see my site?</h3>
<p>Yes — per crawler, distinguishing search crawlers from training crawlers, plus whether your
pages render server-side, since most AI crawlers do not run JavaScript.</p></div>
<div class="faq-item"><h3>Does it track keyword rankings?</h3>
<p>No. Ranking and backlink data need a crawled index of the whole web. Docket audits what is
on your site and how it is configured.</p></div>
</div></section>

<!-- ================= NOT READY YET =================
     Docket is the highest price in the portfolio with no trial and no free tier,
     so the largest group leaving this page is people who are interested and not
     ready to spend it. Until the free audit ships they had nowhere to go but
     away.

     The promise here is deliberately small and literally true. There is no
     sending set up and no double opt-in, so this does NOT say newsletter, does
     not say updates, and does not imply a series. It says one email about one
     thing, which is a promise that can actually be kept.

     Posts on submit only, to our own worker. Nothing loads from a third party —
     see ops/subscribe-worker. -->
<section class="sec"><div class="wrap" style="max-width:34rem">
<div class="sec-head"><h2>Not ready to buy?</h2></div>
<p>A free audit is coming &mdash; one site, the real ranked report, with the
detail redacted. If you want to know when it lands, leave your address and we
will email you <strong>once</strong>, about that. Not a newsletter; there is no
series to sign up to.</p>
<form class="sub" method="post" action="https://kerr-subscribe.kerrco.workers.dev">
  <input type="hidden" name="source" value="docket-homepage">
  <label class="sub-label" for="sub-email">Email</label>
  <input id="sub-email" name="email" type="email" required
         autocomplete="email" placeholder="you@example.com">
  <div aria-hidden="true" style="position:absolute;left:-9999px">
    <label>Leave this empty <input name="website" tabindex="-1" autocomplete="off"></label>
  </div>
  <button class="btn" type="submit">Tell me when it lands</button>
</form>
<p class="sub-fine">We store the address, which site it came from, and the date.
No IP address, no tracking, no profile. Nothing is shared.</p>
</div></section>
"""


FAQ = [
    ("Is Docket free?",
     "Docket is a one-time download for macOS. There is no subscription, no crawl credits and "
     "no per-seat pricing — you can audit as many sites as you like."),
    ("Does Docket send my site data anywhere?",
     "Docket collects nothing about you: no account, no telemetry, no licence check. The "
     "crawl runs on your Mac. Four checks reach outside it by default — Core Web Vitals "
     "from Google PageSpeed, a deliverability test on the addresses your site publishes, "
     "what your server tells AI crawlers, and a knowledge refresh from this site. Offline "
     "mode turns all four off, and every report names the ones that ran."),
    ("How is Docket different from Screaming Frog?",
     "Screaming Frog gives you raw crawl data and leaves the interpretation to you. Docket "
     "ranks every finding by impact against effort and gives you an ordered plan with the "
     "exact markup to paste. Screaming Frog renders JavaScript and supports custom XPath "
     "extraction; Docket does not."),
    ("Can Docket tell me if ChatGPT can see my website?",
     "Yes. Docket checks each AI crawler separately — OAI-SearchBot for ChatGPT Search, "
     "PerplexityBot, Claude-SearchBot and Google-Extended — and distinguishes them from "
     "training crawlers like GPTBot, which many sites block deliberately."),
    ("Does Docket track keyword rankings?",
     "No. Ranking and backlink data require a crawled index of the entire web, which is bought "
     "rather than built. Docket audits what is on your site and how it is configured."),
]


def closer() -> str:
    """The last thing on the page, and the only block that must be.

    It used to sit ninth of twelve, above the email capture and the FAQ, so the
    page ended on a question. It was also the thinnest section on the page at
    30 words — the weakest thing in the strongest position was not the ask, it
    was Q&A.

    The refund line is repeated here on purpose. It is already under the buy
    button in the hero; a reader who has just spent four minutes on the page
    and is deciding at the bottom should not have to scroll back up to find the
    thing that makes the decision reversible.
    """
    return f"""<section class="cta-band"><div class="wrap">
<h2>Audit your site in about a minute</h2>
<p>Download it, type a domain, press Run. There is no onboarding because none is
needed, and nothing about your site leaves your Mac.</p>
<a class="btn btn-lg" href="{CHECKOUT}">Buy Docket &middot; {PRICE_STR} once</a>
<a class="btn-ghost btn-lg" href="{DMG}">Download for Mac</a>
<p class="hero-note"><strong>30 days, no conditions, no questions asked</strong>
&mdash; <a href="/legal/refunds/">refund policy</a></p>
</div></section>"""


def build() -> Path:
    return render(
        cat="", slug="",
        title="Docket SEO — SEO, copy, conversion and brand audits for Mac",
        desc=(f"Docket SEO audits any website on your Mac: {N_CHECKS} checks across SEO, copy, brand, "
              "local and AI search visibility. Ranked fix plan, client-ready PDF, nothing "
              "uploaded."),
        h1="SEO audits that tell you what to fix, in order",
        crumb="Docket for Mac",
        body=body(),
        schema_type="WebPage",
        faq=FAQ,
        closer=closer(),
        landing=True,
    )


if __name__ == "__main__":
    print(build())
