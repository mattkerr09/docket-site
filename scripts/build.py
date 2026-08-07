#!/usr/bin/env python3
"""Build the whole site, then write robots.txt and the sitemap.

    python3 scripts/build.py && python3 scripts/lint.py site

The lint gate is a separate command on purpose: a build that silently refused to
write a page would be worse than one that writes it and then tells you it fails.
"""
from __future__ import annotations

import datetime
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / "articles"))

from render import BASE, SITE, render  # noqa: E402

import bytecap  # noqa: E402
import comparisons  # noqa: E402
import directives  # noqa: E402
import entity  # noqa: E402
import rendering  # noqa: E402
import substitution  # noqa: E402
import home  # noqa: E402
import index_page  # noqa: E402
import learn  # noqa: E402
import link_equity  # noqa: E402
import pages  # noqa: E402


def hub(cat: str, title: str, desc: str, h1: str, lede: str,
        entries: list[tuple[str, str, str]]) -> Path:
    """A section index. Entries are (href, name, one-line summary).

    Entry titles are h2, not h3. Every hub jumped h1 straight to h3, which
    breaks the outline a screen reader announces and the one a search engine
    reads — and it was purely visual, because the h3 carried an inline style
    anyway. Nothing about a hub needs a level skipped.
    """
    items = "".join(
        f'<h2 style="margin-top:1.5rem;font-size:1.35rem">'
        f'<a href="{href}">{name}</a></h2>'
        f"<p>{summary}</p>"
        for href, name, summary in entries
    )
    return render(
        cat=cat, slug="",
        title=title, desc=desc, h1=h1,
        crumb=f'<a href="/">Scout</a> / {h1}',
        body=f'<p class="lede">{lede}</p>{items}',
        schema_type="CollectionPage",
    )


def build_hubs() -> list[Path]:
    out = []
    out.append(hub(
        "vs",
        "Scout compared with other SEO audit tools (2026)",
        "Honest comparisons of Scout against Screaming Frog, Sitebulb and Ahrefs Site Audit — "
        "including what each of them does better.",
        "How Scout compares",
        "Each of these names at least one thing the other tool does better, because a "
        "comparison that never concedes anything is an advertisement.",
        [
            ("/vs/screaming-frog-alternative/", "Scout vs Screaming Frog",
             "Raw crawl data versus a ranked plan. Screaming Frog supports custom "
             "extraction and crawls at far greater scale; Scout does not."),
            ("/vs/sitebulb-alternative/", "Scout vs Sitebulb",
             "Both draw your site architecture — Sitebulb interactively, Scout as rings by "
             "depth sized by link equity. Scout covers "
             "AI visibility, conversion and tracking, which Sitebulb does not."),
            ("/vs/ahrefs-site-audit-alternative/", "Scout vs Ahrefs Site Audit",
             "Ahrefs has a web-scale index and Scout never will. What you get for $129 a month "
             "if the audit is the part you use."),
        ],
    ))
    out.append(hub(
        "learn",
        "Learn: SEO audits, AI search visibility and technical SEO",
        "Plain explanations of what an SEO audit covers, how AI search visibility works, and "
        "what Scout checks.",
        "Learn",
        "Reference pages, written to be read rather than skimmed for keywords.",
        [
            ("/learn/googlebot-2mb-limit/", "Googlebot's 2MB cutoff",
             "It reads the first 2MB and indexes that as the whole page. We measured "
             "well-known homepages and found five already past it."),
            ("/learn/ai-substitution/", "Which pages an AI answer replaces",
             "Ranking and not being visited. Measured on two live sites — this one at 5% "
             "fully substitutable, a delicatessen at 0% — and three ways we measured it "
             "wrong first."),
            ("/learn/ai-search-visibility/", "AI search visibility",
             "The three gates a model has to clear before it can cite you — access, rendering "
             "and entity clarity — with measured data on who is blocking what."),
            ("/learn/seo-audit/", "What an SEO audit covers",
             "Every area, in the order they should be worked, and the three tests a report has "
             "to pass to be worth acting on."),
            ("/learn/javascript-rendering/", "JavaScript rendering",
             "What a crawler that does not run JavaScript misses — measured on a page that "
             "serves 0 characters of text and renders 2,068."),
            ("/learn/sameas-entity-signals/", "sameAs and entity signals",
             "The cheapest entity signal there is, and the share of major sites that skip "
             "it — measured, with the dataset attached."),
            ("/learn/internal-link-equity/", "Internal link equity",
             "The ranking signal your pages pass to each other, measured on our own site — "
             "where the download page held a fifth of what an average page did."),
            ("/learn/what-scout-checks/", "What Scout checks",
             "All the checks, by area, with what each one actually looks at."),
        ],
    ))
    return out


def checks_page() -> Path:
    """Every check, from the shipped catalogue — not a hand-maintained list.

    Generated from `site/_data/checks.csv`, which is exported from the engine's
    own registry. A hand-written feature list drifts from the product within a
    release or two, and on a page whose entire purpose is "here is exactly what
    it does", drift is the one unacceptable failure.
    """
    import csv
    from collections import OrderedDict

    rows = list(csv.DictReader((SITE / "_data" / "checks.csv").open()))
    by_lane: "OrderedDict[str, list]" = OrderedDict()
    for r in rows:
        by_lane.setdefault(r["lane_label"], []).append(r)

    sections = []
    for lane, items in by_lane.items():
        li = "".join(f"<li><strong>{r['title']}</strong> <code>{r['id']}</code></li>"
                     for r in items)
        sections.append(f"<h2>{lane} <span style='color:var(--text-dim);"
                        f"font-size:1rem;font-weight:400'>({len(items)})</span></h2>"
                        f"<ul>{li}</ul>")

    body = f"""
<p class="lede">Scout runs {len(rows)} checks across {len(by_lane)} areas. This list is
generated from the shipped build, so it cannot drift from what the tool actually does — run
<code>scout checks</code> and you will get the same list.</p>

<p>Each check produces a finding only when there is something to report, and each finding
carries what it costs you, how much work the fix is, and the markup to paste. Areas that do
not apply to a site — local business checks on a pure SaaS product, for instance — are marked
not applicable rather than scored as passing.</p>

{''.join(sections)}

<h2>How a finding is put together</h2>
<p>A check that fires produces more than a label. Each finding carries four things, and they
are what separate a plan from a list:</p>
<ul>
<li><strong>What it costs you</strong>, in plain language. Not "missing meta description" but
what happens as a result — Google writing your search snippet from whatever text it finds,
often a cookie notice.</li>
<li><strong>Severity</strong>, where critical is reserved for things that stop the page
ranking at all. If everything is critical, nothing is, so the bar is deliberately high.</li>
<li><strong>Effort</strong>, from minutes to a project. Combined with impact, this is what
produces the ordering — a trivial fix worth 8 outranks a large fix worth 9.</li>
<li><strong>The change itself</strong>, as markup you can copy. For structured data that means
a complete, valid JSON-LD block with your own business details already in the right fields.</li>
</ul>
<p>Findings are also capped in reach. An issue affecting 5,000 pages does not automatically
outrank one affecting the homepage, because reach is compressed logarithmically — without
that, one trivial nit on a large site drowns out everything that matters.</p>

<h2>What is deliberately not here</h2>
<p>Per-page backlinks and anchor text. Domain authority and the list of referring domains
come from Common Crawl's hyperlink graph, but which individual page links to you, and with
what anchor text, lives in 14&nbsp;TiB of archive files. Search volumes. Scout finds the
queries people actually type, from Google's public autocomplete, and refuses to print a
monthly volume it does not have. Each is a real limitation and each is stated in the report
rather than papered over.</p>
<p><a class="btn" href="/download/">Download Scout</a></p>
"""
    return render(
        cat="learn", slug="what-scout-checks",
        title=f"All {len(rows)} checks Scout runs, by area (2026)",
        desc=(f"The complete list of {len(rows)} checks Scout runs across {len(by_lane)} areas, "
              "generated from the shipped build so it cannot drift from the product."),
        h1=f"All {len(rows)} checks, by area",
        crumb='<a href="/">Scout</a> / <a href="/learn/">Learn</a> / What Scout checks',
        body=body,
    )


def write_robots() -> None:
    """Allow everything, and name the AI crawlers explicitly.

    Naming them costs nothing and makes the file self-documenting for whoever
    edits it next — which, given the Index found three quarters of blocking
    sites did it by accident, is the entire point.
    """
    lines = [
        "# Scout — scoutseo.app",
        "# Everything is open, including AI search and training crawlers.",
        "# Named individually so the next person to edit this file can see the",
        "# difference between a search crawler and a training crawler.",
        "",
        "User-agent: *",
        "Allow: /",
        "",
        "# AI search crawlers — these decide whether we appear in AI answers.",
    ]
    for bot in ("OAI-SearchBot", "PerplexityBot", "Claude-SearchBot", ):
        lines += [f"User-agent: {bot}", "Allow: /", ""]
    lines.append("# Training crawlers — allowed here; blocking these is a valid choice for others.")
    for bot in ("GPTBot", "ClaudeBot", "Applebot-Extended", "CCBot"):
        lines += [f"User-agent: {bot}", "Allow: /", ""]
    lines.append(f"Sitemap: {BASE}/sitemap.xml")
    (SITE / "robots.txt").write_text("\n".join(lines) + "\n")


def write_sitemap(pages: list[Path]) -> None:
    today = datetime.date.today().isoformat()
    urls = []
    for p in sorted(pages):
        rel = p.parent.relative_to(SITE).as_posix()
        loc = BASE + "/" + (f"{rel}/" if rel != "." else "")
        # The homepage and the Index are the two pages worth prioritising; the
        # rest are equal. Priority is a weak signal at best, so it stays simple.
        priority = "1.0" if rel == "." else ("0.9" if rel == "index" else "0.7")
        urls.append(f"  <url><loc>{loc}</loc><lastmod>{today}</lastmod>"
                    f"<priority>{priority}</priority></url>")
    (SITE / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.w3.org/1999/sitemaps/0.9">\n'.replace(
            "www.w3.org/1999/sitemaps/0.9", "www.sitemaps.org/schemas/sitemap/0.9")
        + "\n".join(urls) + "\n</urlset>\n"
    )


def write_static() -> None:
    (SITE / "CNAME").write_text("scoutseo.app\n")

    # Copy the Index datasets into the served tree. They live in /data at the
    # repo root so the collection script and its inputs sit together, but only
    # /site is deployed — the Index page links to the dataset, and publishing
    # the method without the data would undercut the whole point of it.
    import shutil
    src = SITE.parent / "data"
    if src.exists():
        dst = SITE / "data"
        dst.mkdir(parents=True, exist_ok=True)
        for f in src.glob("*.json"):
            shutil.copy2(f, dst / f.name)
        shutil.copy2(src / "sites.txt", dst / "sites.txt")
    # Favicon as inline SVG: one file, scales everywhere, no binary in git.
    (SITE / "favicon.svg").write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1024 1024">'
        '<rect width="1024" height="1024" rx="228" fill="#F0800F"/>'
        '<path d="M512 122 L866 242 L866 522 C866 706 714 838 512 902 '
        'C310 838 158 706 158 522 L158 242 Z" fill="#17181C"/>'
        '<g fill="none" stroke="#F0800F" stroke-width="104" stroke-linecap="round" '
        'stroke-linejoin="round"><path d="M348 636 L676 396"/>'
        '<path d="M540 388 L688 388 L688 536"/></g></svg>\n'
    )
    (SITE / ".nojekyll").write_text("")


def not_found() -> Path:
    """/404.html — GitHub Pages serves this for any path that does not exist.

    Written because the default is GitHub's own page: their branding, their
    404 graphic, no way back into the site. A site whose whole argument is that
    it checks the things nobody checks should not leak someone else's error
    page to its own visitors.

    Noindexed and without a canonical, because a soft 404 that search engines
    can index is worse than no page — it is the failure mode this site measured
    in llms.txt handlers.
    """
    body = """
<p class="lede">That page does not exist. The likeliest reason is a link that pointed at a
draft, or a URL that moved when the section was reorganised.</p>

<p>Everything on the site is one of five things:</p>

<ul>
<li><a href="/index/">The Index</a> — first-party measurements. Who blocks which AI crawlers,
and <a href="/index/ai-directives/">which robots.txt rules do nothing</a>.</li>
<li><a href="/learn/">Learn</a> — what an audit covers, AI search visibility, link equity,
JavaScript rendering, entity signals.</li>
<li><a href="/vs/">Compare</a> — honest comparisons against Screaming Frog, Sitebulb and
Ahrefs Site Audit, each naming what the other does better.</li>
<li><a href="/how-to/">Fix it</a> — the exact change to make for a specific finding.</li>
<li><a href="/download/">Download</a> — the app itself, and the command line inside it.</li>
</ul>

<p><a class="btn" href="/">Back to the start</a></p>
"""
    return render(
        cat="", slug="",
        title="Page not found — Scout",
        desc="That page does not exist. Where everything on scoutseo.app lives.",
        h1="Page not found",
        crumb='<a href="/">Scout</a> / Not found',
        body=body,
        schema_type="",
        filename="404.html",
        noindex=True,
    )


def main() -> int:
    pages: list[Path] = [home.build(), index_page.build(), checks_page()]
    pages += comparisons.build_all()
    pages += bytecap.build_all()
    pages += learn.build_all()
    pages += link_equity.build_all()
    pages += entity.build_all()
    pages += directives.build_all()
    pages += rendering.build_all()
    pages += substitution.build_all()
    pages += __import__('pages').build_all()
    pages += build_hubs()

    # NOT appended to `pages`: the sitemap is derived from that list, and
    # render() resolves an empty cat+slug to the site root, so including the
    # 404 emitted a second <loc>https://scoutseo.app/</loc> — a duplicate entry
    # is an invalid sitemap. It is also a page that must never be indexed.
    not_found()

    write_robots()
    write_sitemap(pages)
    write_static()

    print(f"built {len(pages)} pages")
    for p in sorted(pages):
        print("  " + p.relative_to(SITE.parent).as_posix())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
