#!/usr/bin/env python3
"""Build the whole site, then write robots.txt and the sitemap.

    python3 scripts/build.py && python3 scripts/lint.py site

The lint gate is a separate command on purpose: a build that silently refused to
write a page would be worse than one that writes it and then tells you it fails.
"""
from __future__ import annotations

import hashlib

import datetime
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / "articles"))

import facts as F  # noqa: E402
from render import BASE, DATA, SITE, render  # noqa: E402

import about  # noqa: E402
import audit_quality  # noqa: E402
import brand as brand_article  # noqa: E402
import logs as logs_article  # noqa: E402
import bytecap  # noqa: E402
import canonicals  # noqa: E402
import best_free  # noqa: E402
import comparisons  # noqa: E402
import directives  # noqa: E402
import entity  # noqa: E402
import rendering  # noqa: E402
import substitution  # noqa: E402
import home  # noqa: E402
import howto_canonicals  # noqa: E402
import howto_cls  # noqa: E402
import howto_hreflang  # noqa: E402
import howto_https  # noqa: E402
import howto_schema  # noqa: E402
import howto_deploy_gate  # noqa: E402
import howto_security_headers  # noqa: E402
import howto_open_graph  # noqa: E402
import howto_soft404  # noqa: E402
import howto_title_width  # noqa: E402
import howto_titles  # noqa: E402
import outrank  # noqa: E402
import index_page  # noqa: E402
import learn  # noqa: E402
import link_equity  # noqa: E402
import authority_page  # noqa: E402
import conversion  # noqa: E402
import monitoring  # noqa: E402
import martech  # noqa: E402
import mailcheck  # noqa: E402
import pages  # noqa: E402


def hub(cat: str, title: str, desc: str, h1: str, lede: str,
        entries: list[tuple[str, str, str]], intro: str = "") -> Path:
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
        crumb=f'<a href="/">Docket</a> / {h1}',
        # `intro` is the hub's own argument, between the lede and the list.
        # A hub that only lists its children is a page Google has no reason to
        # rank and a reader has no reason to stay on — Docket flagged all three
        # of ours as thin, correctly.
        body=f'<p class="lede">{lede}</p>{intro}{items}',
        schema_type="CollectionPage",
    )


def build_hubs() -> list[Path]:
    out = []
    out.append(hub(
        "vs",
        "Docket compared with other SEO audit tools (2026)",
        "Honest comparisons of Docket against Screaming Frog, Sitebulb, Ahrefs and Semrush "
        "Site Audit — including what each of them does better.",
        "How Docket compares",
        "Each of these names at least one thing the other tool does better, because a "
        "comparison that never concedes anything is an advertisement.",
        [
            ("/vs/screaming-frog-alternative/", "Docket vs Screaming Frog",
             "Raw crawl data versus a ranked plan. Screaming Frog supports custom "
             "extraction and crawls at far greater scale; Docket does not."),
            ("/vs/sitebulb-alternative/", "Docket vs Sitebulb",
             "Both draw your site architecture — Sitebulb interactively, Docket as rings by "
             "depth sized by link equity. Docket covers "
             "AI visibility, conversion and tracking, which Sitebulb does not."),
            ("/vs/ahrefs-site-audit-alternative/", "Docket vs Ahrefs Site Audit",
             "Ahrefs has a web-scale index and Docket never will. What you get for $129 a month "
             "if the audit is the part you use."),
            ("/vs/semrush-site-audit-alternative/", "Docket vs Semrush Site Audit",
             "Semrush now checks AI crawler access per bot, tracks issue trends over time and "
             "runs 140+ checks. Where a one-time local auditor still makes sense."),
            ("/vs/lighthouse-alternative/", "Docket vs Google Lighthouse",
             "The one here that is not an alternative. Lighthouse is free, it is Google's, "
             "and you should keep running it — its SEO category is ten scored checks on one "
             "URL, and a crawl is what sits outside that."),
            ("/vs/google-search-console/", "Docket vs Google Search Console",
             "A division of labour rather than a comparison. Search Console holds your real "
             "queries, index status and field Core Web Vitals, and nothing replaces it. What "
             "it cannot answer is what is wrong with a page today."),
            ("/vs/scrutiny-alternative/", "Docket vs Scrutiny",
             "Both are Mac apps you buy once rather than subscribe to. Scrutiny is the "
             "stronger link checker and has been shipping far longer; Docket ranks what "
             "it finds and covers conversion, brand and AI visibility, which Scrutiny "
             "does not."),
        ],
        intro="""
<h2>The three kinds of tool, and which question each answers</h2>

<p>Most comparisons between SEO tools are unhelpful because they compare things built to
answer different questions. There are broadly three:</p>

<ul>
<li><strong>Crawlers</strong> — Screaming Frog, Sitebulb. You point them at a site and they
return everything, at scale, sortable. The question they answer is "what is on my site". They
are very good at it and Docket does not attempt that scale.</li>
<li><strong>Platforms</strong> — Ahrefs, Semrush. A web-scale index of links and keywords,
with a site audit attached. The question is "where do I stand against everyone else", and
nothing on a desktop can answer it, because the answer requires having crawled the web.</li>
<li><strong>Auditors</strong> — where Docket sits. The question is "what should I change, in
what order", which is a judgement rather than a dataset, and it is the one that needs no
subscription because the data it needs is your own site.</li>
</ul>

<p>The practical consequence: if you already pay for a platform, Docket does not replace it.
It replaces the part of it you open once a month and then export to a spreadsheet.</p>

<h2>When not to use Docket</h2>

<p>If you need keyword positions or a backlink profile, none of these pages will help — Docket
has neither and is not building either. If your crawl is hundreds of thousands of URLs, use a
crawler built for it. If you are not on a Mac, Docket will not run at all.</p>

<p>Each comparison below names at least one thing the other tool does better. That is not
modesty; a comparison page that concedes nothing tells you only that its author wanted your
money.</p>
""",
    ))
    out.append(hub(
        "learn",
        "Learn: SEO audits, AI search visibility and technical SEO",
        "Plain explanations of what an SEO audit covers, how AI search visibility works, and "
        "what Docket checks.",
        "Learn",
        "Reference pages, written to be read rather than skimmed for keywords.",
        [
            ("/learn/googlebot-2mb-limit/", "Googlebot's 2MB cutoff",
             "It reads the first 2MB and indexes that as the whole page. We measured "
             "well-known homepages and found five already past it."),
            ("/learn/audit-tool-accuracy/", "How to tell whether an audit tool is lying to you",
             "Four questions to ask of any SEO finding, each of them learned here by "
             "getting it wrong first."),
            ("/learn/log-file-analysis/", "Log file analysis: what Googlebot actually fetched",
             f"A user-agent proves nothing, which is why Google publishes "
             f"{F.gbot_total_prefixes():,} crawler IP prefixes. Reading a log honestly, "
             f"and where the dedicated tool wins."),
            ("/learn/brand-consistency/", "Brand consistency: the question no crawler asks",
             f"Of {F.brand_social_frame()} company sites linking social profiles, "
             f"{F.brand_social_undeclared()} declared none of them in schema. What the "
             f"brand lane checks, and where design tools beat it."),
            ("/learn/domain-authority-without-a-subscription/",
             "Domain authority without a subscription",
             "Ranked from the public Common Crawl link graph. The useful part is what "
             "it says when it cannot see you, which is what it said about this site."),
            ("/learn/site-monitoring/", "SEO monitoring: what changed, not what is wrong",
             "Re-audits while the app is open, regressions first, and the two "
             "comparisons Docket refuses to make because the number would look useful "
             "and be wrong."),
            ("/learn/conversion-audit/", "Conversion audit: 9 checks on your landing pages",
             "Ranking and then failing to say what to do next costs the same as not "
             "ranking. The 9 mechanical checks, and the judgement calls Docket "
             "refuses to make for you."),
            ("/learn/marketing-tag-audit/", "Marketing tag audit: is your tracking on every page?",
             "Tags are installed on templates; sites grow pages built from other "
             "templates. The 6 tracking checks, and the four-minute version you "
             "can do by hand."),
            ("/learn/dead-contact-address/", "The contact address that cannot receive mail",
             "An address on a domain with no MX record bounces to the sender and never "
             "reaches you, and no tool asks whether yours works."),
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
            ("/learn/canonical-tags/", "Canonical tags",
             "Google calls rel=canonical a hint and overrules it routinely. The seven "
             "ways it gets set wrong, and what each Search Console status is actually "
             "telling you."),
            ("/learn/internal-link-equity/", "Internal link equity",
             "The ranking signal your pages pass to each other, measured on our own site — "
             "where the download page held a fifth of what an average page did."),
            ("/learn/what-docket-checks/", "What Docket checks",
             "All the checks, by area, with what each one actually looks at."),
        ],
    ))
    return out


def checks_page() -> Path:
    """Every check, from the shipped catalogue — not a hand-maintained list.

    Generated from `data/checks.csv`, which is exported from the engine's
    own registry. A hand-written feature list drifts from the product within a
    release or two, and on a page whose entire purpose is "here is exactly what
    it does", drift is the one unacceptable failure.
    """
    import csv
    from collections import OrderedDict

    rows = list(csv.DictReader((DATA / "checks.csv").open()))
    by_lane: "OrderedDict[str, list]" = OrderedDict()
    for r in rows:
        by_lane.setdefault(r["lane_label"], []).append(r)

    sections = []
    for lane, items in by_lane.items():
        li = "".join(f"<li><strong>{r['title']}</strong> <code>{r['id']}</code></li>"
                     for r in items)
        sections.append(f"<h2>{lane} <span style='color:var(--text-dim);"
                        f"font-size:var(--t-lg);font-weight:400'>({len(items)})</span></h2>"
                        f"<ul>{li}</ul>")

    body = f"""
<p class="lede">Docket runs {len(rows)} checks across {len(by_lane)} areas. This list is
generated from the shipped build, so it cannot drift from what the tool actually does — run
<code>docket checks</code> and you will get the same list.</p>

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
produces the ordering — a trivial fix on an important page outranks a large fix on
a marginal one.</li>
<li><strong>The change itself</strong>, as markup you can copy. For structured data that means
a complete, valid JSON-LD block with your own business details already in the right fields.</li>
</ul>
<p>Findings are also capped in reach. An issue affecting every page of a large site does not automatically
outrank one affecting the homepage, because reach is compressed logarithmically — without
that, one trivial nit on a large site drowns out everything that matters.</p>

<h2>What is deliberately not here</h2>
<p>Per-page backlinks and anchor text. Domain authority and the list of referring domains
come from Common Crawl's hyperlink graph, but which individual page links to you, and with
what anchor text, lives in archive files far too large to fetch from a laptop. Search volumes. Docket finds the
queries people actually type, from Google's public autocomplete, and refuses to print a
monthly volume it does not have. Each is a real limitation and each is stated in the report
rather than papered over.</p>
<p><a class="btn" href="/download/">Download Docket</a></p>
"""
    return render(
        cat="learn", slug="what-docket-checks",
        title=f"All {len(rows)} checks Docket runs, by area (2026)",
        desc=(f"The complete list of {len(rows)} checks Docket runs across {len(by_lane)} areas, "
              "generated from the shipped build so it cannot drift from the product."),
        h1=f"All {len(rows)} checks, by area",
        crumb='<a href="/">Docket</a> / <a href="/learn/">Learn</a> / What Docket checks',
        body=body,
    )


def write_robots() -> None:
    """Allow everything, and name the AI crawlers explicitly.

    Naming them costs nothing and makes the file self-documenting for whoever
    edits it next — which, given the Index found three quarters of blocking
    sites did it by accident, is the entire point.
    """
    lines = [
        "# Docket — docketseo.app",
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
    (SITE / "CNAME").write_text("docketseo.app\n")

    # Copy the Index datasets into the served tree. They live in /data at the
    # repo root so the collection script and its inputs sit together, but only
    # /site is deployed — the Index page links to the dataset, and publishing
    # the method without the data would undercut the whole point of it.
    #
    # ⚠️ AN EXPLICIT LIST, NOT A GLOB, AND THAT IS THE WHOLE POINT.
    #
    # This was `src.glob("*.json")`, which publishes whatever happens to be in
    # the directory rather than what anyone decided to publish. On 2026-08-18
    # the measurements moved out of `site/_data` — where they had been served
    # by accident of location — into `/data`, and the glob would have picked up
    # all 22 of them and served them again from the new address. The fix for
    # accidental publication cannot itself be a glob.
    #
    # Only five datasets are linked from a page. The other sixteen included
    # `mail-2026-08.json`, which carries 113 email addresses harvested from
    # `mailto:` links on the Tranco top 1500 — addresses those sites publish
    # themselves, but which no page here renders, so serving them bought
    # nothing and handed a spam list a convenient machine-readable form.
    #
    # To publish a new dataset, add it here AND link it from the page that
    # cites it. The check below fails the build if anything else appears in
    # site/data, so this list cannot quietly drift back into a glob.
    import shutil
    #: Linked from a page, so serving them is a decision. Verified by reading
    #: the built HTML for the URLs it actually references — the first attempt at
    #: that used a substring match and reported `googlebot.json` as ours, when
    #: every page mentioning it links to Google's own
    #: developers.google.com/search/apis/ipranges/googlebot.json. Parse the URL,
    #: not the filename.
    LINKED = ("ai-directives-2026-08.json", "entity-2026-08.json",
              "index-2026-08.json", "knowledge.json")
    #: Not linked, published on purpose: the Index states its population, and
    #: the list of sites IS that statement.
    ALSO_PUBLISHED = ("sites.txt",)
    #: The subset this step owns. The rest are written straight into site/data
    #: by the scripts that generate them.
    COPIED_FROM_DATA = ("index-2026-08.json", "sites.txt")

    src = SITE.parent / "data"
    dst = SITE / "data"
    dst.mkdir(parents=True, exist_ok=True)
    for name in COPIED_FROM_DATA:
        f = src / name
        if not f.is_file():
            raise SystemExit(
                f"build: {name} is published but missing from {src}. A page links "
                f"to it, so shipping without it would serve a 404 from the Index.")
        shutil.copy2(f, dst / name)

    # ⚠️ EVERYTHING UNDER site/ IS PUSHED TO gh-pages AND SERVED, so this refuses
    # anything nobody chose to publish. It replaced `for f in src.glob("*.json")`,
    # which served whatever happened to be in the directory.
    #
    # That mattered on 2026-08-18: the measurements moved out of `site/_data`,
    # where 22 of them had been served by accident of location, into `/data` —
    # and the glob promptly copied all 22 to the new address. Among them was
    # `mail-2026-08.json`, carrying 113 email addresses read from mailto: links
    # on the Tranco top 1500. No page renders one of them. The fix for
    # accidental publication cannot itself be a glob.
    for existing in sorted(dst.iterdir()):
        if existing.name not in LINKED + ALSO_PUBLISHED:
            raise SystemExit(
                f"build: site/data/{existing.name} would be served but nothing "
                f"links to it. Link it from the page that cites it and add it to "
                f"LINKED, or delete it.")

    # The favicon is NOT written here any more, and this comment is the reason.
    #
    # It used to be a literal on these lines, filled #818CF8 — the desktop
    # app's indigo, and this site's brand until `9ff83aa`. Because the build
    # rewrote the file every run, the mark could not be corrected: fixing
    # site/favicon.svg by hand worked until the next deploy silently put the
    # indigo back. That is what a copy of a fact does, and it is why the tile
    # now comes from `render_brand_assets.py`, which derives it from the
    # `--brand` token rather than repeating a hex.
    #
    # `deploy.sh` runs that script's `--check` after this build, so a stale
    # tile fails the deploy rather than shipping.
    from render_brand_assets import render as render_brand
    render_brand(SITE)
    (SITE / ".nojekyll").write_text("")


def thank_you() -> Path:
    """The page a buyer lands on after paying. Built 2026-08-19.

    WHY IT EXISTS. Three of the four products in this portfolio had nowhere for a
    purchase to land. Docket was one of them: the checkout finished on Polar's own
    confirmation screen, so at the moment of payment the buyer left docketseo.app
    and was never told anything by us.

    Three costs, and the third is the expensive one:
      - no sale is countable in analytics, ads or no ads;
      - a Meta `Purchase` event has nowhere to fire, so a campaign has nothing to
        optimise toward — and the symptom of that reads as "the pixel is broken",
        which sends somebody to debug the pixel while the real fault is a missing
        page;
      - the buyer is dropped at peak intent with no idea what happens next, which
        is what turns into a refund request rather than a missing metric.

    ⚠️ WHAT THIS PAGE DELIBERATELY DOES NOT SAY, and why each was left out:

      - **No licence key, and no activation steps.** Docket's site mentions a key
        exactly zero times, and the shipped 1.1.57 build exposes no licence route
        at all — every feature is already open. Telling a buyer to "activate" would
        describe a mechanism that does not exist in the product they just paid for.
      - **No delivery time.** Not "within a minute", not "shortly". No purchase has
        ever completed on this product, so any number here would be a promise
        nobody has measured.
      - **No support response time**, for the same reason.

    Every link below was checked live before shipping: /download/ 200,
    /legal/refunds/ 200, /contact/ 200, and hello@docketseo.app is the address the
    contact page already publishes.

    ⚠️ THIS PAGE WENT FALSE TWICE AND IS THE WORST PLACE ON THE SITE FOR THAT.
    It is what a customer reads in the seconds after $199 leaves their account.

    It said the receipt comes from POLAR, for days after the checkout moved to
    Dodo — so a buyer would watch for an email from a company that never took
    their money, conclude the payment failed, and write in at the moment they
    are most anxious about it.

    And it said "nothing to unlock and no key to enter", which licensing
    falsified in 1.1.59. Following that, a buyer downloads, opens Docket, is
    told it is not activated, and reasonably concludes the app is broken.

    Neither is a wording problem: this page is the handover, so what it says
    next has to be the thing they actually do.

    NO DUAL-VENDOR CLAUSE HERE, unlike Crisp and Outlier. Their pages keep Polar
    true for customers who bought before the cutover; Docket has none. Measured
    before writing this: the Polar account shows ZERO orders and ZERO licence
    keys ever issued. A reassurance aimed at customers who do not exist is noise
    on a page that has to be exact.

    The checkout's success_url is a Dodo dashboard setting and Matthew's to
    change. The page exists first so the redirect has somewhere to point.
    """
    body = """
<p>Your payment went through. The receipt comes by email from Dodo Payments, who
handle the checkout — it may land under a different sender name than Docket.</p>

<h2>Your licence key is in that email</h2>
<p>Docket needs it before it will run an audit. Open the app, click
<strong>Enter licence key</strong> in the title bar, and paste it in. From a
terminal, <code>docket licence --key YOUR-KEY</code> does the same thing.</p>
<p>One licence covers up to three machines. The key is stored on your own Mac.</p>
<p><a class="btn" href="/download/">Download Docket</a></p>

<h2>If something is wrong</h2>
<p>Email <a href="mailto:hello@docketseo.app">hello@docketseo.app</a> and say what
happened. If the purchase was a mistake, the
<a href="/legal/refunds/">refund policy</a> is on this site and it is short.</p>
"""
    return render(
        cat="", slug="thank-you",
        title="Thank you — Docket",
        desc="Your Docket purchase is complete. Where to download the app and how to reach us.",
        h1="Thank you",
        crumb='<a href="/">Docket</a> / Thank you',
        body=body,
        schema_type="",
        noindex=True,
    )


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
<li><a href="/vs/">Compare</a> — honest comparisons against Screaming Frog, Sitebulb, Ahrefs
and Semrush Site Audit, each naming what the other does better.</li>
<li><a href="/how-to/">Fix it</a> — the exact change to make for a specific finding.</li>
<li><a href="/download/">Download</a> — the app itself, and the command line inside it.</li>
</ul>

<p><a class="btn" href="/">Back to the start</a></p>
"""
    return render(
        cat="", slug="",
        title="Page not found — Docket",
        desc="That page does not exist. Where everything on docketseo.app lives.",
        h1="Page not found",
        crumb='<a href="/">Docket</a> / Not found',
        body=body,
        schema_type="",
        filename="404.html",
        noindex=True,
    )


def stamp_build_id() -> str:
    """One id over the whole tree, so a stale deploy is detectable from outside.

    The failure this exists for, 2026-08-17: two commits were merged and green,
    the built site/ carried a screenshot and a refund line, and the live site
    served neither. Every gate in deploy.sh checks the BUILD; nothing checked
    that the build reached the CDN, and the answer arrived as "dockets site is
    still the same or its not updating". Matthew made it rule 0.8 the next day:
    a commit is not a ship.

    A hash of index.html alone cannot see it — the .webp that 404'd is not in
    index.html. So this hashes every file under site/, with the placeholder
    still in place, and rewrites the placeholder afterwards. Nothing is hashed
    twice: the placeholder is a fixed-length constant, so stamping cannot change
    the id it stamps.
    """
    manifest = []
    for path in sorted(SITE.rglob("*")):
        if path.is_dir() or path.name == ".nojekyll":
            continue
        manifest.append(path.relative_to(SITE).as_posix().encode()
                        + b"\0" + hashlib.sha256(path.read_bytes()).hexdigest().encode())
    build_id = hashlib.sha256(b"\n".join(manifest)).hexdigest()[:12]

    for page in SITE.rglob("*.html"):
        raw = page.read_text(encoding="utf-8")
        if "__BUILD_ID__" in raw:
            page.write_text(raw.replace("__BUILD_ID__", build_id), encoding="utf-8")
    (DATA).mkdir(parents=True, exist_ok=True)
    (DATA / "build-id.txt").write_text(build_id + "\n", encoding="utf-8")
    return build_id


def main() -> int:
    pages: list[Path] = [home.build(), index_page.build(), checks_page()]
    pages += comparisons.build_all()
    pages += [best_free.best_hub(), best_free.free_seo_audit_tools()]
    pages += [howto_https.http_to_https(),
              howto_hreflang.hreflang_return_tags(),
              howto_canonicals.conflicting_canonicals(),
              howto_soft404.soft_404s(),
              howto_open_graph.howto_open_graph(),
              howto_deploy_gate.deploy_gate(),
              howto_security_headers.security_headers(),
              howto_schema.structured_data_errors(),
              howto_cls.layout_shift(),
              howto_titles.duplicate_titles(),
              howto_title_width.title_tags(),
              outrank.outrank()]
    pages += bytecap.build_all()
    pages += canonicals.build_all()
    pages += learn.build_all()
    pages += link_equity.build_all()
    pages += martech.build_all()
    pages += conversion.build_all()
    pages += authority_page.build_all()
    pages += monitoring.build_all()
    pages += entity.build_all()
    pages += directives.build_all()
    pages += rendering.build_all()
    pages += substitution.build_all()
    pages += __import__('pages').build_all()
    pages += about.build_all()
    pages += audit_quality.build_all()
    pages += brand_article.build_all()
    pages += logs_article.build_all()
    pages += mailcheck.build_all()
    pages += build_hubs()

    # NOT appended to `pages`: the sitemap is derived from that list, and
    # render() resolves an empty cat+slug to the site root, so including the
    # 404 emitted a second <loc>https://docketseo.app/</loc> — a duplicate entry
    # is an invalid sitemap. It is also a page that must never be indexed.
    not_found()
    thank_you()

    write_robots()
    write_sitemap(pages)
    write_static()
    stamp_competitor_claims(pages)

    build_id = stamp_build_id()
    print(f"build id {build_id} — stamped into every page and data/build-id.txt")

    print(f"built {len(pages)} pages")
    for p in sorted(pages):
        print("  " + p.relative_to(SITE.parent).as_posix())
    return 0



#: Pages that discuss another product must let the reader age the claim.
#:
#: The comparison pages and the two pricing tables carry a real date and a
#: source. Seven other pages describe competitors in prose — their rendering
#: engine, their log analyser's price, what they do not cover — with nothing to
#: age it by. Checking every one of those properly is real work and is not done
#: yet; what is not acceptable is silence, which reads as "true now" forever.
#:
#: So an undated page says it is undated, and points at the pages that are
#: dated. lint.py accepts either form and fails on neither present, because the
#: reader's question — how old is this? — has an answer in both.
#
# Wrapped in a section > .wrap, not dropped bare before </article>. The first
# version sat outside every container and the visual gate caught it at 375px:
# "text starts 0px from the edge (p.claims-note)". Same shape as the FAQ that
# ran flush to the viewport edge — the gutter comes from .wrap, and anything
# injected past its closing tag has none.
UNDATED_CLAIMS_NOTE = (
    '<section><div class="wrap">'
    '<p class="claims-note">Other products here are described from their own '
    'public pages and are <strong>not dated on this page</strong>. The dated '
    'checks, with sources, are on the '
    '<a href="/vs/">comparison pages</a>. Products change — if something here '
    'about another tool has gone stale, tell us and it will be corrected.</p>'
    '</div></section>'
)


def stamp_competitor_claims(pages) -> None:
    """Add the undated-claims note to any page that needs one."""
    import sys as _sys
    _sys.path.insert(0, str(Path(__file__).resolve().parent))
    from lint import _names_a_competitor, visible_text

    stamped = 0
    for page in pages:
        raw = page.read_text(encoding="utf-8")
        if "Checked " in raw or "claims-note" in raw:
            continue
        if not _names_a_competitor(visible_text(raw, body_only=True)):
            continue
        if "</article>" not in raw:
            continue
        page.write_text(raw.replace("</article>",
                                    UNDATED_CLAIMS_NOTE + "\n</article>", 1),
                        encoding="utf-8")
        stamped += 1
    if stamped:
        print(f"stamped {stamped} page(s) as carrying undated competitor claims")

if __name__ == "__main__":
    raise SystemExit(main())
