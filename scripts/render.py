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

SITE = Path(__file__).resolve().parent.parent / "site"
BASE = "https://scoutseo.app"

# --------------------------------------------------------------------------
# Design system. Dark, high-contrast, amber accent carried from the app icon.
# --------------------------------------------------------------------------
STYLE = """<style>
:root{
  --bg:#0b0c0f;--surface:#12141a;--surface-2:#181b23;--surface-3:#1f232d;
  --text:#eef0f4;--text-mid:#a7aeba;--text-dim:#767d8b;
  --amber:#F0800F;--amber-light:#FFB528;--amber-soft:rgba(240,128,15,.12);
  --ok:#4ade80;--warn:#fbbf24;--bad:#ff7a6e;
  --border:rgba(255,255,255,.10);--border-strong:rgba(255,255,255,.18);
  --radius:14px;--radius-sm:9px;
  --sans:-apple-system,BlinkMacSystemFont,"Segoe UI",Helvetica,Arial,sans-serif;
  --mono:ui-monospace,"SF Mono",Menlo,Consolas,monospace;
}
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
html{scroll-behavior:smooth;-webkit-text-size-adjust:100%}
body{background:var(--bg);color:var(--text);font-family:var(--sans);font-size:17px;
  line-height:1.68;-webkit-font-smoothing:antialiased;overflow-x:hidden}
a{color:var(--amber-light);text-decoration:none;transition:color .16s}
a:hover{color:var(--text);text-decoration:underline}
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
.nav-links a:hover{color:var(--text);text-decoration:none}
@media(max-width:780px){.nav-links{display:none}}
.btn{display:inline-block;background:var(--amber);color:#17181C;font-weight:700;
  padding:.62rem 1.2rem;border-radius:10px;font-size:.95rem;border:0;cursor:pointer}
.btn:hover{background:var(--amber-light);color:#17181C;text-decoration:none}
.btn-ghost{display:inline-block;border:1px solid var(--border-strong);color:var(--text-mid);
  padding:.6rem 1.15rem;border-radius:10px;font-size:.95rem;font-weight:600}
.btn-ghost:hover{background:var(--surface-2);color:var(--text);text-decoration:none}

article{padding:2.8rem 0 4.5rem}
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
</style>"""


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
<a class="btn" href="/#download">Download</a>
</div></nav>"""

FOOTER = f"""<footer><div class="wrap-wide">
<div class="foot-grid">
<div><h4>Scout</h4>
<a href="/">Overview</a><a href="/#download">Download</a>
<a href="/index/">The Scout Index</a><a href="/learn/what-scout-checks/">What it checks</a></div>
<div><h4>Compare</h4>
<a href="/vs/screaming-frog-alternative/">vs Screaming Frog</a>
<a href="/vs/sitebulb-alternative/">vs Sitebulb</a>
<a href="/vs/ahrefs-site-audit-alternative/">vs Ahrefs</a>
<a href="/vs/">All comparisons</a></div>
<div><h4>Learn</h4>
<a href="/learn/ai-search-visibility/">AI search visibility</a>
<a href="/learn/seo-audit/">What an SEO audit is</a>
<a href="/learn/">All guides</a></div>
<div><h4>Contact</h4>
<a href="mailto:hello@scoutseo.app">hello@scoutseo.app</a>
<a href="https://github.com/mattkerr09/scout-site">GitHub</a>
<a href="/legal/privacy/">Privacy</a><a href="/legal/terms/">Terms</a></div>
</div>
<div class="foot-bottom">
<span>© 2026 Scout · Audits run on your Mac. Nothing is uploaded.</span>
<span>{_mark(15, "var(--text-dim)")}</span>
</div></div></footer>"""


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
        '"description":"Scout crawls a website, runs 80 checks across SEO, content, '
        'speed, structured data, local visibility, AI search visibility and marketing '
        'conversion, and returns a ranked list of what to fix. Runs entirely on your Mac.",'
        '"offers":{"@type":"Offer","price":"0","priceCurrency":"USD"},'
        '"featureList":"80 checks, ranked action plan, PDF report, scheduled monitoring, '
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
) -> Path:
    """Write one page. `body` is the caller's authored HTML — never generated here."""
    # A hub page is a cat with no slug. Joining blindly gives "/vs//", which
    # canonicalises the page to a URL it is not served from — the canonical then
    # argues against itself. Crisp hit exactly this.
    path_parts = [p for p in (cat, slug) if p]
    url = BASE + "/" + ("/".join(path_parts) + "/" if path_parts else "")
    esc = lambda s: s.replace('"', "&quot;")  # noqa: E731

    blocks = [_entity_schema()]
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
<body>
{NAV}
<article><div class="{wrap_class}">
<div class="crumb">{crumb}</div>
<h1>{h1}</h1>
{body}
</div></article>
{FOOTER}
</body>
</html>
"""

    out_dir = SITE.joinpath(*path_parts) if path_parts else SITE
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / "index.html"
    out.write_text(html, encoding="utf-8")
    return out
