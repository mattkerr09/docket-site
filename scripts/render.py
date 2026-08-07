#!/usr/bin/env python3
"""Render a Scout page into the site shell.

Same split as Crisp: this file owns the *chrome* — head, styles, nav, footer,
schema — and never generates prose. Every article's body is authored by hand in
`scripts/articles/*.py`. Sharing chrome across pages is fine and expected;
sharing phrasing is what trips the duplicate gate and what actually reads as
spam, so the body always comes from the caller.

Ships `Organization` + `SoftwareApplication` + `sameAs` on every page. Crisp's
own strategy audit recorded "no entity schema" as its single highest-ROI gap,
found months after launch — no reason to repeat that here.
"""
from __future__ import annotations

from pathlib import Path
import pathlib

SITE = Path(__file__).resolve().parent.parent / "site"
BASE = "https://scoutseo.app"


def _check_counts() -> tuple:
    """`(checks, lanes)` read from the exported dataset.

    The count was hardcoded in nine places and went stale the moment the engine
    gained a lane. It is a fact about the product, so it is read from the
    product's own exported data and interpolated everywhere.
    """
    import csv
    path = pathlib.Path(__file__).resolve().parent.parent / "site" / "_data" / "checks.csv"
    with path.open() as fh:
        rows = list(csv.DictReader(fh))
    return len(rows), len({r["lane"] for r in rows})


N_CHECKS, N_LANES = _check_counts()

#: The current build. One place, because a download link that 404s is the
#: single worst bug a product site can have.
RELEASE = "v0.1.0"
DMG = f"https://github.com/mattkerr09/scout-site/releases/download/{RELEASE}/Scout-0.1.0-arm64.dmg"
DMG_SIZE = "18 MB"

#: One-time price, in USD. Declared once so the schema, the comparison table and
#: the download page cannot drift apart — which is exactly what happened to the
#: check count and the download size before they were centralised.
PRICE = 149
PRICE_STR = f"${PRICE}"

# --------------------------------------------------------------------------
# Design system. Dark, high-contrast, amber accent carried from the app icon.
# --------------------------------------------------------------------------
STYLE = """<style>
/* Switzer, self-hosted at 74 KB. A Swiss grotesk rather than the geometric
   display faces this category defaults to: Scout is a measuring instrument that
   produces reports, and the type should read as precise rather than friendly.
   Self-hosted because Scout flags render-blocking third-party resources in its
   own audits, and shipping one would be the inconsistency it exists to catch. */
@font-face{font-family:'Switzer';src:url('/fonts/Switzer-400.woff2') format('woff2');
  font-weight:400;font-style:normal;font-display:swap}
@font-face{font-family:'Switzer';src:url('/fonts/Switzer-500.woff2') format('woff2');
  font-weight:500;font-style:normal;font-display:swap}
@font-face{font-family:'Switzer';src:url('/fonts/Switzer-600.woff2') format('woff2');
  font-weight:600;font-style:normal;font-display:swap}
@font-face{font-family:'Switzer';src:url('/fonts/Switzer-700.woff2') format('woff2');
  font-weight:700;font-style:normal;font-display:swap}
@font-face{font-family:'Clash Display';src:url('/fonts/ClashDisplay-700.woff2') format('woff2');
  font-weight:700;font-style:normal;font-display:swap}
@font-face{font-family:'General Sans';src:url('/fonts/GeneralSans-400.woff2') format('woff2');
  font-weight:400;font-style:normal;font-display:swap}
@font-face{font-family:'General Sans';src:url('/fonts/GeneralSans-500.woff2') format('woff2');
  font-weight:500;font-style:normal;font-display:swap}
@font-face{font-family:'General Sans';src:url('/fonts/GeneralSans-600.woff2') format('woff2');
  font-weight:600;font-style:normal;font-display:swap}

:root{
  /* Deeper and slightly cooler than before. A near-black with a trace of blue
     reads as considered where pure #000 reads as unstyled. */
  --bg:#07080d;--surface:#0e1017;--surface-2:#141822;--surface-3:#1b2030;
  --text:#f4f6fa;--text-mid:#a9b1c0;--text-dim:#6f7889;
  --amber:#F0800F;--amber-light:#FFB528;--amber-soft:rgba(240,128,15,.12);
  --ok:#4ade80;--warn:#fbbf24;--bad:#ff7a6e;
  --border:rgba(255,255,255,.08);--border-strong:rgba(255,255,255,.16);
  --radius:16px;--radius-sm:10px;
  --display:'Switzer',-apple-system,BlinkMacSystemFont,"Helvetica Neue",sans-serif;
  --sans:'Switzer',-apple-system,BlinkMacSystemFont,"Segoe UI",Helvetica,sans-serif;
  --mono:ui-monospace,"SF Mono",Menlo,Consolas,monospace;
  /* One vertical rhythm for every section. Space is most of what separates a
     considered page from a cramped one. */
  --sec-y:clamp(5rem,11vw,9.5rem);
}
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
html{scroll-behavior:smooth;-webkit-text-size-adjust:100%}
body{background:var(--bg);color:var(--text);font-family:var(--sans);font-size:17.5px;
  line-height:1.66;-webkit-font-smoothing:antialiased;
  -moz-osx-font-smoothing:grayscale;overflow-x:hidden;
  font-feature-settings:"ss03"}

/* No scroll-reveal. It was built twice — once hiding content by default, once
   arming from JavaScript with a timed backstop — and neither could be shown to
   work: IntersectionObserver does not fire in the webview used to verify this
   site, and nor did the setTimeout fallback.

   Shipping an effect that cannot be verified, on a page whose entire argument
   is that Scout reports only what it can prove, is the wrong trade. The type,
   spacing and depth carry the page; content renders immediately and is never
   contingent on a script. */
}
a{color:var(--amber-light);text-decoration:none;transition:color .16s}
@media(hover:hover){a:hover{color:var(--text);text-decoration:underline}}
.wrap{width:min(820px,calc(100% - 2rem));margin:0 auto}
.wrap-wide{width:min(1080px,calc(100% - 2rem));margin:0 auto}

nav{position:sticky;top:0;z-index:20;background:rgba(11,12,15,.88);
  backdrop-filter:blur(14px);border-bottom:1px solid var(--border)}
.nav-inner{display:flex;align-items:center;justify-content:space-between;height:60px;gap:1rem}
.nav-brand{display:flex;align-items:center;gap:.55rem;font-weight:750;color:var(--text);
  font-size:1.1rem;letter-spacing:-.02em}
.nav-brand:hover{text-decoration:none;color:var(--amber-light)}
.nav-links{display:flex;gap:1.35rem;font-size:.94rem}
.nav-links a{color:var(--text-mid)}
@media(hover:hover){.nav-links a:hover{color:var(--text);text-decoration:none}}
@media(max-width:780px){
  .nav-inner{flex-wrap:wrap;row-gap:.55rem}
  .nav-links{order:3;width:100%;gap:1.15rem;font-size:.88rem;
    overflow-x:auto;-webkit-overflow-scrolling:touch;padding-bottom:.15rem;
    scrollbar-width:none}
  .nav-links::-webkit-scrollbar{display:none}
  .nav-links a{white-space:nowrap}
}
.btn{display:inline-block;background:linear-gradient(180deg,var(--amber-light),var(--amber));
  color:#17181C;font-weight:600;box-shadow:0 1px 0 rgba(255,255,255,.22) inset,
  0 12px 30px -12px rgba(240,128,15,.75);
  padding:.62rem 1.2rem;border-radius:10px;font-size:.95rem;border:0;cursor:pointer}
.btn:hover{background:var(--amber-light);color:#17181C;text-decoration:none}
.btn-ghost{display:inline-block;border:1px solid var(--border-strong);color:var(--text-mid);
  padding:.6rem 1.15rem;border-radius:10px;font-size:.95rem;font-weight:600}
.btn-ghost:hover{background:var(--surface-2);color:var(--text);text-decoration:none}

article{padding:2.8rem 0 4.5rem}
.foot-h{font-size:.82rem;font-weight:600;letter-spacing:.02em;text-transform:none;
  color:var(--text);margin:0 0 .55rem;font-family:var(--sans)}
.crumb{font-family:var(--mono);font-size:.75rem;color:var(--text-dim);
  text-transform:uppercase;letter-spacing:.1em;margin-bottom:1rem}
.crumb a{color:var(--text-dim)}
h1{font-size:2.3rem;line-height:1.14;letter-spacing:-.03em;margin-bottom:1rem}
h2{font-size:1.5rem;letter-spacing:-.02em;margin:2.6rem 0 .9rem}
h3{font-size:1.13rem;margin:1.7rem 0 .5rem}
p{color:var(--text-mid);margin-bottom:1rem}
strong{color:var(--text);font-weight:650}
.lede{font-size:1.17rem;color:var(--text);margin-bottom:1.4rem}
ul,ol{color:var(--text-mid);margin:0 0 1.1rem 1.25rem}
li{margin-bottom:.42rem}
blockquote{border-left:3px solid var(--amber);padding:.2rem 0 .2rem 1.1rem;
  margin:1.3rem 0;color:var(--text)}
code{font-family:var(--mono);font-size:.88em;background:var(--surface-2);
  padding:.14em .4em;border-radius:5px;color:var(--amber-light)}
pre{background:var(--surface);border:1px solid var(--border);border-radius:var(--radius-sm);
  padding:1rem 1.1rem;overflow-x:auto;margin:1.2rem 0;font-size:.86rem;line-height:1.6}
pre code{background:0;padding:0;color:var(--text-mid)}

table.cmp{width:100%;border-collapse:collapse;margin:1.4rem 0;font-size:.94rem}
table.cmp th,table.cmp td{text-align:left;padding:.66rem .72rem;
  border-bottom:1px solid var(--border);vertical-align:top}
table.cmp th{color:var(--text-dim);font-size:.78rem;text-transform:uppercase;
  letter-spacing:.06em;font-weight:650}
table.cmp td:first-child{color:var(--text);font-weight:600}
.yes{color:var(--ok);font-weight:650}
.no{color:var(--bad)}
.wrap-tbl{overflow-x:auto;margin:1.4rem 0}

.callout{background:var(--surface);border:1px solid var(--border);
  border-left:3px solid var(--amber);border-radius:var(--radius-sm);
  padding:1.05rem 1.2rem;margin:1.5rem 0}
.callout p:last-child{margin-bottom:0}
.callout-title{color:var(--amber-light);font-weight:700;font-size:.8rem;
  text-transform:uppercase;letter-spacing:.07em;margin-bottom:.4rem}

.stat-row{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));
  gap:.8rem;margin:1.6rem 0}
.stat{background:var(--surface);border:1px solid var(--border);
  border-radius:var(--radius-sm);padding:1rem 1.1rem}
.stat b{display:block;font-size:1.85rem;letter-spacing:-.03em;color:var(--text);
  line-height:1.1;font-weight:700}
.stat span{font-size:.82rem;color:var(--text-dim)}

footer{border-top:1px solid var(--border);padding:2.6rem 0 3rem;margin-top:3rem;
  font-size:.9rem;color:var(--text-dim)}
.foot-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));
  gap:1.6rem;margin-bottom:2rem}
.foot-grid h4{font-size:.76rem;text-transform:uppercase;letter-spacing:.08em;
  color:var(--text-dim);margin-bottom:.6rem;font-weight:650}
.foot-grid a{display:block;color:var(--text-mid);padding:.17rem 0;font-size:.92rem}
.foot-bottom{display:flex;justify-content:space-between;gap:1rem;flex-wrap:wrap;
  border-top:1px solid var(--border);padding-top:1.3rem}

/* ============ Landing page only ============
   The article shell is a single 820px column, which is right for reading and
   wrong for a homepage. These rules only apply on pages that opt in via
   body.landing, so the article template is untouched. */
body.landing article{padding:0}
.hero-sec{padding:3.2rem 0 4.5rem;position:relative;overflow:hidden}
/* Ambient light. A flat dark page reads as unlit; two soft pools give the
   canvas depth without anything on it looking decorated. */
.hero-sec::before{content:"";position:absolute;inset:-40% -10% auto -10%;height:120%;
  background:radial-gradient(58% 46% at 22% 30%,rgba(240,128,15,.13),transparent 68%),
             radial-gradient(46% 40% at 82% 18%,rgba(88,132,255,.10),transparent 70%);
  pointer-events:none;z-index:0}
.hero-grid{position:relative;z-index:1}

/* The product sits on light rather than beside it. */
.mock{position:relative;transform:perspective(1600px) rotateY(-3.5deg) rotateX(1.5deg);
  transform-origin:left center;
  box-shadow:0 2px 0 rgba(255,255,255,.06) inset,
             0 40px 90px -30px rgba(0,0,0,.9),
             0 0 120px -40px rgba(240,128,15,.30);
  transition:transform .6s cubic-bezier(.16,1,.3,1)}
@media(hover:hover){.mock:hover{transform:perspective(1600px) rotateY(-1.5deg) rotateX(.5deg)}}
@media(max-width:940px){.mock{transform:none}.mock:hover{transform:none}}

/* ---- the signature: a list becoming an order ------------------------------
   Scout's whole claim is that it ranks. Saying so is weaker than showing it, so
   the rows arrive unordered and settle into sequence as the section enters. One
   move, once, on the one idea the product is actually about. */
.rank-demo{display:grid;gap:.6rem;margin:2rem 0 0}
.rank-row{display:flex;align-items:center;gap:.9rem;background:var(--surface-2);
  border:1px solid var(--border);border-radius:11px;padding:.85rem 1.05rem;
  font-size:.95rem;color:var(--text-mid)}
.rank-row .n{flex:none;width:26px;height:26px;border-radius:8px;display:grid;
  place-items:center;font-family:var(--mono);font-size:.78rem;font-weight:600;
  background:rgba(255,255,255,.06);color:var(--text-dim)}
.rank-row.hot .n{background:var(--amber);color:#17181C}
.rank-row.hot{color:var(--text);border-color:rgba(240,128,15,.34)}
/* No entrance animation here. It was built, and IntersectionObserver turned out
   not to fire at all in the webview used to verify it — so the effect could not
   be confirmed working, only confirmed shipped. A motion effect that cannot be
   verified is a liability on a page whose whole argument is rigour, and a
   static ranked list makes the same point without one. */
}
.hero-sec::before{content:"";position:absolute;inset:-40% 0 auto 50%;width:900px;height:600px;
  transform:translateX(-50%);background:radial-gradient(ellipse at center,rgba(240,128,15,.13),transparent 62%);
  pointer-events:none}
.hero-grid{display:grid;grid-template-columns:minmax(0,1.05fr) minmax(0,1fr);gap:3.2rem;
  align-items:center;position:relative}
@media(max-width:940px){.hero-grid{grid-template-columns:1fr;gap:2.4rem}}
.eyebrow{display:inline-flex;align-items:center;gap:.55rem;font-family:var(--mono);
  font-size:.72rem;letter-spacing:.14em;text-transform:uppercase;color:var(--amber-light);
  background:linear-gradient(180deg,rgba(240,128,15,.14),rgba(240,128,15,.06));
  border:1px solid rgba(240,128,15,.26);border-radius:999px;padding:.5rem 1.05rem;
  margin-bottom:1.9rem}
.eyebrow::before{content:"";width:6px;height:6px;border-radius:50%;
  background:var(--ok);box-shadow:0 0 0 3px rgba(74,222,128,.18)}
.hero-h1{font-family:var(--display);font-weight:700;
  /* 84px at the top end, matching the scale premium product sites settle on.
     Tight tracking is what stops large type reading as merely big. */
  font-size:clamp(2.5rem,5.6vw,4.3rem);line-height:1.02;letter-spacing:-.035em;
  margin:0 0 1.35rem;max-width:15ch}
.hero-h1 em{font-style:normal;color:var(--amber-light);display:block}
.hero-h1 em{font-style:normal;background:linear-gradient(100deg,var(--amber-light),var(--amber));
  -webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text}
.hero-sub{font-size:1.11rem;color:var(--text-mid);max-width:33rem;margin-bottom:1.9rem;line-height:1.6}
.hero-cta{display:flex;gap:.7rem;flex-wrap:wrap;align-items:center;margin-bottom:1.1rem}
.btn-lg{padding:1rem 2.05rem;font-size:1.02rem;border-radius:13px;letter-spacing:-.01em}
.hero-note{font-size:.86rem;color:var(--text-dim)}

/* Product mockup — an HTML replica of the app, not a screenshot. Stays sharp at
   any density, weighs nothing, and follows the page theme. */
.mock{background:var(--surface);border:1px solid var(--border-strong);border-radius:16px;
  box-shadow:0 30px 70px rgba(0,0,0,.5),0 0 0 1px rgba(255,255,255,.03);overflow:hidden}
.mock-bar{display:flex;align-items:center;gap:.45rem;padding:.62rem .85rem;
  background:var(--surface-2);border-bottom:1px solid var(--border)}
.mock-dot{width:10px;height:10px;border-radius:99px;background:#3a3f4b}
.mock-title{margin-left:.5rem;font-size:.74rem;color:var(--text-dim);font-family:var(--mono)}
.mock-body{padding:1.05rem}
.mock-top{display:flex;gap:1.05rem;align-items:center;margin-bottom:1rem}
.mock-score{font-size:1.95rem;font-weight:720;letter-spacing:-.03em;line-height:1}
.mock-verdict{font-size:.86rem;color:var(--text-mid);line-height:1.45}
.mock-chips{display:flex;gap:.32rem;margin-top:.45rem;flex-wrap:wrap}
.mock-chip{font-size:.66rem;font-weight:680;padding:.13rem .48rem;border-radius:99px}
.mock-lanes{display:grid;grid-template-columns:1fr 1fr;gap:.42rem}
.mock-lane{background:var(--surface-2);border:1px solid var(--border);border-radius:8px;padding:.5rem .62rem}
.mock-lane-top{display:flex;justify-content:space-between;align-items:baseline;gap:.4rem}
.mock-lane-name{font-size:.7rem;color:var(--text-mid)}
.mock-lane-score{font-size:.86rem;font-weight:700}
.mock-lane-bar{height:3px;border-radius:99px;background:rgba(255,255,255,.09);margin-top:.36rem;overflow:hidden}
.mock-lane-bar i{display:block;height:100%;border-radius:99px}
.mock-find{background:var(--surface-2);border:1px solid var(--border);border-left:2px solid var(--bad);
  border-radius:8px;padding:.6rem .7rem;margin-top:.55rem}
.mock-find-h{display:flex;gap:.45rem;align-items:center;font-size:.76rem;font-weight:640;color:var(--text)}
.mock-rank{background:var(--amber-soft);color:var(--amber-light);font-size:.62rem;font-weight:720;
  width:16px;height:16px;border-radius:4px;display:flex;align-items:center;justify-content:center;flex:0 0 auto}
.mock-find-p{font-size:.68rem;color:var(--text-dim);margin:.3rem 0 0 1.35rem;line-height:1.45}

/* Sections */
.sec{padding:var(--sec-y) 0}
/* Hairlines between every section made the page read as a stack of boxes.
   Space separates them now; a rule is used only where one is doing work. */
.sec + .sec{border-top:1px solid rgba(255,255,255,.045)}
.sec-head{text-align:center;max-width:41rem;margin:0 auto 2.6rem}
.sec-head h2{font-family:var(--display);font-weight:700;
  font-size:clamp(1.9rem,4vw,2.85rem);line-height:1.1;
  letter-spacing:-.03em;margin:0 0 .85rem}
.sec-head h2 em{font-style:normal;color:var(--amber-light)}
.sec-head p{font-size:1.04rem;color:var(--text-mid);margin:0}
.grid-3{display:grid;grid-template-columns:repeat(auto-fit,minmax(268px,1fr));gap:1rem}
.card{background:var(--surface);border:1px solid var(--border);border-radius:13px;padding:1.4rem 1.5rem;
  transition:border-color .18s,transform .18s}
.card:hover{border-color:var(--border-strong);transform:translateY(-2px)}
.card-ico{width:36px;height:36px;border-radius:9px;background:var(--amber-soft);color:var(--amber-light);
  display:flex;align-items:center;justify-content:center;margin-bottom:.85rem}
.card h3{font-size:1.03rem;margin:0 0 .45rem}
.card p{font-size:.92rem;margin:0;color:var(--text-mid)}
.card.wide{grid-column:1/-1}

/* Before/after: a list vs a sequence */
.split{display:grid;grid-template-columns:1fr 1fr;gap:1rem}
@media(max-width:760px){.split{grid-template-columns:1fr}}
.split-col{background:var(--surface);border:1px solid var(--border);border-radius:13px;padding:1.3rem 1.4rem}
.split-col.good{border-color:rgba(240,128,15,.32)}
.split-tag{font-size:.7rem;font-weight:700;letter-spacing:.08em;text-transform:uppercase;
  color:var(--text-dim);margin-bottom:.8rem}
.split-col.good .split-tag{color:var(--amber-light)}
.split-list{list-style:none;margin:0;padding:0;font-size:.88rem}
.split-list li{padding:.42rem 0;border-bottom:1px solid var(--border);color:var(--text-mid);
  display:flex;gap:.55rem;align-items:flex-start}
.split-list li:last-child{border-bottom:0}
.split-list .n{color:var(--amber-light);font-weight:700;font-family:var(--mono);font-size:.78rem;flex:0 0 auto}
.split-phase{font-size:.66rem;text-transform:uppercase;letter-spacing:.07em;color:var(--amber-light);
  font-weight:700;padding-top:.6rem}

/* Index chart, drawn from the measured dataset */
.chart{background:var(--surface);border:1px solid var(--border);border-radius:13px;padding:1.5rem 1.6rem}
.bar-row{display:grid;grid-template-columns:130px 1fr 46px;gap:.85rem;align-items:center;margin-bottom:.62rem}
.bar-lbl{font-size:.83rem;color:var(--text-mid);text-align:right}
.bar-track{height:9px;background:rgba(255,255,255,.06);border-radius:99px;overflow:hidden}
.bar-fill{display:block;height:100%;border-radius:99px;
  background:linear-gradient(90deg,var(--amber),var(--amber-light))}
.bar-val{font-size:.82rem;font-weight:680;color:var(--text);font-variant-numeric:tabular-nums}
.chart-note{font-size:.8rem;color:var(--text-dim);margin:1.1rem 0 0}

.cta-band{text-align:center;padding:4.2rem 0}
.cta-band h2{font-size:clamp(1.7rem,3vw,2.3rem);letter-spacing:-.028em;margin-bottom:.7rem}
.cta-band p{font-size:1.05rem;color:var(--text-mid);max-width:34rem;margin:0 auto 1.6rem}
.faq-item{border-top:1px solid var(--border);padding:1.15rem 0}
.faq-item h3{font-size:1rem;margin:0 0 .4rem}
.faq-item p{font-size:.93rem;margin:0}
</style>
"""


def _mark(size: int = 22, color: str = "var(--amber)") -> str:
    """The Scout shield, inline so there is no extra request and no flash."""
    return (
        f'<svg viewBox="0 0 1024 1024" width="{size}" height="{size}" aria-hidden="true">'
        f'<path d="M512 122 L866 242 L866 522 C866 706 714 838 512 902 '
        f'C310 838 158 706 158 522 L158 242 Z" fill="{color}"/>'
        f'<g fill="none" stroke="var(--bg)" stroke-width="112" stroke-linecap="round" '
        f'stroke-linejoin="round"><path d="M348 636 L676 396"/>'
        f'<path d="M540 388 L688 388 L688 536"/></g></svg>'
    )


NAV = f"""<nav><div class="wrap-wide nav-inner">
<a class="nav-brand" href="/">{_mark(23)}<span>Scout</span></a>
<div class="nav-links">
<a href="/index/">The Index</a>
<a href="/learn/">Learn</a>
<a href="/vs/">Compare</a>
<a href="/how-to/">Fix it</a>
<a href="/for/">For you</a>
</div>
<a class="btn" href="/download/">Download</a>
</div></nav>"""

FOOTER = f"""<footer><div class="wrap-wide">
<div class="foot-grid">
<div><h2 class="foot-h">Scout</h2>
<a href="/">Overview</a><a href="/download/">Download</a>
<a href="/index/">The Scout Index</a><a href="/learn/what-scout-checks/">What it checks</a></div>
<div><h2 class="foot-h">Compare</h2>
<a href="/vs/screaming-frog-alternative/">vs Screaming Frog</a>
<a href="/vs/sitebulb-alternative/">vs Sitebulb</a>
<a href="/vs/ahrefs-site-audit-alternative/">vs Ahrefs</a>
<a href="/vs/">All comparisons</a></div>
<div><h2 class="foot-h">Learn</h2>
<a href="/learn/ai-search-visibility/">AI search visibility</a>
<a href="/learn/seo-audit/">What an SEO audit is</a>
<a href="/learn/">All guides</a></div>
<div><h2 class="foot-h">Contact</h2>
<a href="mailto:hello@scoutseo.app">hello@scoutseo.app</a>
<a href="https://github.com/mattkerr09/scout-site">GitHub</a>
<a href="/legal/privacy/">Privacy</a><a href="/legal/terms/">Terms</a></div>
</div>
<div class="foot-bottom">
<span>© 2026 Scout · Audits run on your Mac. Nothing is uploaded.</span>
<span>{_mark(15, "var(--text-dim)")}</span>
</div></div></footer>"""


def _breadcrumb_schema(crumb: str) -> str:
    """BreadcrumbList built from the crumb already on the page.

    Derived from the visible trail rather than declared separately, so the
    markup and what a reader sees cannot drift. Without it a result shows the
    raw URL where it could show the path.
    """
    import re as _re

    parts = _re.findall(r'<a href="([^"]+)">([^<]+)</a>|>\s*([^<>]+?)\s*$', crumb)
    items, position = [], 0
    for href, label, tail in parts:
        name = (label or tail or "").strip()
        if not name:
            continue
        position += 1
        entry = ('{"@type":"ListItem","position":' + str(position)
                 + ',"name":"' + name.replace('"', "'") + '"')
        if href:
            entry += ',"item":"' + BASE + href + '"'
        items.append(entry + "}")
    if len(items) < 2:
        return ""
    # Bare JSON — the caller wraps every block in its own <script> tag, and
    # returning one here nested them and produced a block that would not parse.
    return ('{"@context":"https://schema.org","@type":"BreadcrumbList",'
            '"itemListElement":[' + ",".join(items) + "]}")


def _entity_schema() -> str:
    """Organization + SoftwareApplication + sameAs, on every page.

    `sameAs` is what lets a language model resolve "Scout" to this specific
    product rather than the dozen other things called Scout — the single
    highest-leverage piece of markup for being cited by name.
    """
    return (
        '{"@context":"https://schema.org","@graph":['
        '{"@type":"Organization","@id":"' + BASE + '/#org",'
        '"name":"Scout","url":"' + BASE + '/",'
        '"logo":"' + BASE + '/icon.png",'
        '"description":"Scout makes local SEO and marketing audit software for Mac.",'
        '"sameAs":["https://github.com/mattkerr09"]},'
        '{"@type":"WebSite","@id":"' + BASE + '/#site",'
        '"url":"' + BASE + '/","name":"Scout",'
        '"publisher":{"@id":"' + BASE + '/#org"}},'
        '{"@type":"SoftwareApplication","@id":"' + BASE + '/#app",'
        '"name":"Scout","applicationCategory":"BusinessApplication",'
        '"applicationSubCategory":"SEO audit software",'
        '"operatingSystem":"macOS 12 or later, Apple Silicon",'
        '"description":"Scout crawls a website, runs ' + str(N_CHECKS) + ' checks across SEO, copy, '
        'speed, structured data, local visibility, AI search visibility and marketing '
        'conversion, and returns a ranked list of what to fix. Runs entirely on your Mac.",'
        '"offers":{"@type":"Offer","price":"' + str(PRICE) + '","priceCurrency":"USD",'
        '"availability":"https://schema.org/InStock"},'
        '"featureList":"' + str(N_CHECKS) + ' checks, ranked action plan, PDF report, scheduled monitoring, '
        'competitor comparison, AI crawler access audit",'
        '"publisher":{"@id":"' + BASE + '/#org"}}]}'
    )


def render(
    *,
    cat: str,
    slug: str,
    title: str,
    desc: str,
    h1: str,
    crumb: str,
    body: str,
    published: str = "2026-08-06",
    modified: str | None = None,
    schema_type: str = "Article",
    faq: list[tuple[str, str]] | None = None,
    wide: bool = False,
    landing: bool = False,
) -> Path:
    """Write one page. `body` is the caller's authored HTML — never generated here."""
    # A hub page is a cat with no slug. Joining blindly gives "/vs//", which
    # canonicalises the page to a URL it is not served from — the canonical then
    # argues against itself. Crisp hit exactly this.
    path_parts = [p for p in (cat, slug) if p]
    url = BASE + "/" + ("/".join(path_parts) + "/" if path_parts else "")
    esc = lambda s: s.replace('"', "&quot;")  # noqa: E731

    blocks = [_entity_schema()]
    crumb_schema = _breadcrumb_schema(crumb)
    if crumb_schema:
        blocks.append(crumb_schema)
    if schema_type:
        blocks.append(
            '{"@context":"https://schema.org","@type":"' + schema_type + '",'
            f'"headline":"{esc(h1)}","description":"{esc(desc)}",'
            f'"datePublished":"{published}","dateModified":"{modified or published}",'
            '"author":{"@type":"Person","name":"Matt Kerr",'
            '"description":"Builds Scout. Every number on this site comes from running it."},'
            '"publisher":{"@id":"' + BASE + '/#org"},'
            f'"mainEntityOfPage":"{url}","inLanguage":"en"}}'
        )
    if faq:
        qa = ",".join(
            '{"@type":"Question","name":"' + esc(q) + '",'
            '"acceptedAnswer":{"@type":"Answer","text":"' + esc(a) + '"}}'
            for q, a in faq
        )
        blocks.append(
            '{"@context":"https://schema.org","@type":"FAQPage","mainEntity":[' + qa + "]}"
        )

    schema = "\n".join(
        f'<script type="application/ld+json">{b}</script>' for b in blocks
    )
    wrap_class = "wrap-wide" if wide else "wrap"

    # A landing page supplies its own full-bleed sections; an article gets the
    # single reading column with a breadcrumb and an H1 above it.
    if landing:
        body_class = ' class="landing"'
        opening = "<article>"
        closing = "</article>"
    else:
        body_class = ""
        opening = (f'<article><div class="{wrap_class}">'
                   f'<div class="crumb">{crumb}</div><h1>{h1}</h1>')
        closing = "</div></article>"

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<meta name="description" content="{esc(desc)}">
<meta name="theme-color" content="#0b0c0f">
<link rel="canonical" href="{url}">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<link rel="apple-touch-icon" href="/apple-touch-icon.png">
<meta property="og:type" content="{'website' if schema_type == 'WebPage' else 'article'}">
<meta property="og:title" content="{esc(h1)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:url" content="{url}">
<meta property="og:site_name" content="Scout">
<meta property="og:image" content="{BASE}/og.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{esc(h1)}">
<meta name="twitter:description" content="{esc(desc)}">
<meta name="twitter:image" content="{BASE}/og.png">
{STYLE}
{schema}
</head>
<body{body_class}>
{NAV}
{opening}
{body}
{closing}
{FOOTER}
</body>
</html>
"""

    out_dir = SITE.joinpath(*path_parts) if path_parts else SITE
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / "index.html"
    out.write_text(html, encoding="utf-8")
    return out
