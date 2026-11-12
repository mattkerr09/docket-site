#!/usr/bin/env python3
"""Build the whole site, then write robots.txt, llms.txt and the sitemap.

    python3 scripts/build.py && python3 scripts/lint.py site

The lint gate is a separate command on purpose: a build that silently refused to
write a page would be worse than one that writes it and then tells you it fails.
"""
from __future__ import annotations

import hashlib
import json
import html
import re
import tempfile
import os

import datetime
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
import brand
sys.path.append(str(HERE / "articles"))

import facts as F  # noqa: E402
from render import BASE, DATA, MAC_HW, MACOS, PRICE, PROCESSOR, SITE, SUPPORT_EMAIL, WINDOWS, render, with_next_step  # noqa: E402

import about  # noqa: E402
import audit_quality  # noqa: E402
from articles import brand as brand_article  # noqa: E402
import logs as logs_article  # noqa: E402
import bytecap  # noqa: E402
import canonicals  # noqa: E402
import best_free  # noqa: E402
import sf_alternatives  # noqa: E402
import white_label  # noqa: E402
import comparisons  # noqa: E402
import directives  # noqa: E402
import entity  # noqa: E402
import rendering  # noqa: E402
import substitution  # noqa: E402
import home  # noqa: E402
import howto_canonicals  # noqa: E402
import howto_cls  # noqa: E402
import howto_render_blocking  # noqa: E402
import howto_link_text  # noqa: E402
import howto_meta_descriptions  # noqa: E402
import howto_image_formats  # noqa: E402
import howto_thin_content  # noqa: E402
import howto_ttfb  # noqa: E402
import howto_nap  # noqa: E402
import howto_favicon  # noqa: E402
import mac_options  # noqa: E402
import corrections  # noqa: E402
import corrections_cases  # noqa: E402
import howto_hreflang  # noqa: E402
import howto_js_audit  # noqa: E402
import howto_content_audit  # noqa: E402
import howto_lang_mismatch  # noqa: E402
import howto_backlink_audit  # noqa: E402
import cloudflare_gptbot  # noqa: E402
import noindex_ai_crawlers  # noqa: E402
import sitemaps_ai_crawlers  # noqa: E402
import googlebot_robots_blocks  # noqa: E402
import www_vs_apex  # noqa: E402
import internal_utm  # noqa: E402
import howto_cdn_blocks_ai  # noqa: E402
import howto_https  # noqa: E402
import howto_schema  # noqa: E402
import howto_deploy_gate  # noqa: E402
import howto_security_headers  # noqa: E402
import howto_open_graph  # noqa: E402
import howto_competing_pages  # noqa: E402
import howto_mobile  # noqa: E402
import howto_pagination  # noqa: E402
import howto_meta_refresh  # noqa: E402
import howto_positioning  # noqa: E402
import howto_rate_limits  # noqa: E402
import howto_brand_name  # noqa: E402
import howto_caveat_gate  # noqa: E402
import howto_identical_bodies  # noqa: E402
import howto_placeholder_text  # noqa: E402
import howto_json_ld_errors  # noqa: E402
import howto_analytics_findings  # noqa: E402
import howto_schema_type  # noqa: E402
import howto_missing_means_empty  # noqa: E402
import howto_address_region  # noqa: E402
import howto_type_matching  # noqa: E402
import bot  # noqa: E402
import howto_hreflang_targets  # noqa: E402
import howto_sitemap_dead_urls  # noqa: E402
import howto_unreachable  # noqa: E402
import howto_cta_forms  # noqa: E402
import howto_sameas  # noqa: E402
import howto_voice  # noqa: E402
import howto_schema_mismatch  # noqa: E402
import howto_utility_pages  # noqa: E402
import howto_money_pages  # noqa: E402
import howto_soft404  # noqa: E402
import howto_title_width  # noqa: E402
import howto_titles  # noqa: E402
import howto_mcp  # noqa: E402
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
import ai_slop  # noqa: E402
import howto_nav_js  # noqa: E402
import howto_phone  # noqa: E402
import eeat  # noqa: E402
import howto_images  # noqa: E402
import email_capture  # noqa: E402
import howto_redirects
import index_coverage  # noqa: E402
import click_depth_orphans  # noqa: E402
import url_structure  # noqa: E402
import howto_hreflang_codes  # noqa: E402
import page_weight  # noqa: E402
import ai_directives  # noqa: E402
import ai_crawler_blocking  # noqa: E402
import ai_crawler_pages  # noqa: E402
import ai_bot_host_pages  # noqa: E402
import llms_adoption  # noqa: E402
import priority_model  # noqa: E402
import howto_headings  # noqa: E402
import howto_broken_links  # noqa: E402
import howto_compression  # noqa: E402
import extractability  # noqa: E402
import tool_ai_crawlers  # noqa: E402
import tools_free  # noqa: E402
import tools_website_checker  # noqa: E402
import ai_assistants  # noqa: E402
import ai_questions  # noqa: E402
import title_ii  # noqa: E402
import public_site_check  # noqa: E402
import help_pages  # noqa: E402
import check_pages  # noqa: E402
import learn_seo_audit_report  # noqa: E402
import best_free_seo_audit_plugins  # noqa: E402
import learn_free_seo_audit_api  # noqa: E402


def hub(cat: str, title: str, desc: str, h1: str, lede: str,
        entries: list[tuple[str, str, str]], intro: str = "") -> Path:
    """A section index. Entries are (href, name, one-line summary).

    Entry titles are h2, not h3. Every hub jumped h1 straight to h3, which
    breaks the outline a screen reader announces and the one a search engine
    reads, and it was purely visual, because the h3 carried an inline style
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
        body=with_next_step(f'<p class="lede">{lede}</p>{intro}{items}', f"hub-{cat}"),
        schema_type="CollectionPage",
    )


def build_hubs() -> list[Path]:
    out = []
    out.append(hub(
        "vs",
        "Docket compared with other SEO audit tools (2026)",
        "Honest comparisons of Docket against Screaming Frog, Sitebulb, Ahrefs and Semrush "
        "Site Audit, including what each of them does better.",
        "How Docket compares",
        "Each of these names at least one thing the other tool does better, because a "
        "comparison that never concedes anything is an advertisement.",
        [
            ("/vs/screaming-frog-alternative/", "Docket vs Screaming Frog",
             "Raw crawl data versus a ranked plan. Screaming Frog supports custom "
             "extraction and crawls at far greater scale; Docket does not."),
            ("/vs/sitebulb-alternative/", "Docket vs Sitebulb",
             "Both draw your site architecture: Sitebulb interactively, Docket as rings by "
             "depth sized by link equity. Docket covers "
             "AI visibility, conversion and tracking, which Sitebulb does not."),
            ("/vs/ahrefs-site-audit-alternative/", "Docket vs Ahrefs Site Audit",
             "Ahrefs has a web-scale index and Docket never will. What you get for $129 a month "
             "if the audit is the part you use."),
            ("/vs/semrush-site-audit-alternative/", "Docket vs Semrush Site Audit",
             "Semrush now checks AI crawler access per bot, tracks issue trends over time and "
             "runs 140+ checks. Where a one-time local auditor still makes sense."),
            ("/vs/se-ranking-vs-screaming-frog/", "SE Ranking vs Screaming Frog",
             "Not a Docket comparison first: a metered cloud audit against an unmetered "
             "local crawler, which is the real difference between them. Where Docket fits, "
             "and the two things it does not do."),
            ("/vs/lighthouse-alternative/", "Docket vs Google Lighthouse",
             "The one here that is not an alternative. Lighthouse is free, it is Google's, "
             "and you should keep running it. Its SEO category is ten scored checks on one "
             "URL, and a crawl is what sits outside that."),
            ("/vs/google-search-console/", "Docket vs Google Search Console",
             "A division of labour rather than a comparison. Search Console holds your real "
             "queries, index status and field Core Web Vitals, and nothing replaces it. What "
             "it cannot answer is what is wrong with a page today."),
            ("/vs/scrutiny-alternative/", "Docket vs Scrutiny",
             "Both are apps you buy once and run on a Mac rather than subscribe to. Scrutiny is the "
             "stronger link checker and has been shipping far longer; Docket ranks what "
             "it finds and covers conversion, brand and AI visibility, which Scrutiny "
             "does not."),
            ("/vs/crawler-sh-alternative/", "Docket vs crawler.sh",
             "Both run locally with no account, and they agree about almost everything "
             "except purpose: crawler.sh turns sites into Markdown for AI training, and "
             "caps pages per session."),
            ("/vs/crawlraven-alternative/", "Docket vs CrawlRaven",
             "Close to Docket's pitch, and cheaper only in its first months. It joins Search Console "
             "and GA4 to a technical audit sold by the month, with a lifetime plan beside "
             "it; Docket's audit is bought once and has no page allowance."),
            ("/vs/jetoctopus-alternative/", "Docket vs JetOctopus",
             "It reads your server logs, which Docket cannot do at all, and meters "
             "crawling in hundreds of thousands to millions of URLs. An enterprise platform "
             "against a desktop app you buy once."),
            ("/vs/profound-alternative/", "Docket vs Profound",
             "An answer-engine tracker sold by demo, with no crawler in its published "
             "platform list. It reports whether AI assistants mention you; Docket checks "
             "whether their crawlers can reach you."),
            ("/vs/sitechecker-alternative/", "Docket vs Sitechecker",
             "It tracks rankings and whether five AI models mention your brand; Docket "
             "does neither. What Docket checks is whether those crawlers can reach you "
             "at all: a precondition rather than the same question."),
            ("/vs/seoptimer-alternative/", "Docket vs SEOptimer",
             "The cheapest way in, and built for selling audits: reports on a custom "
             "domain and an embeddable lead-capture audit. The real difference is the "
             "meter: SEOptimer buys you a set number of crawls a month, Docket does not "
             "count them."),
        ],
        intro=f"""
<h2>The three kinds of tool, and which question each answers</h2>

<p>Most comparisons between SEO tools are unhelpful because they compare things built to
answer different questions. There are broadly three:</p>

<ul>
<li><strong>Crawlers</strong>: Screaming Frog, Sitebulb. You point them at a site and they
return everything, at scale, sortable. The question they answer is "what is on my site". They
are very good at it and Docket does not attempt that scale.</li>
<li><strong>Platforms</strong>: Ahrefs, Semrush. A web-scale index of links and keywords,
with a site audit attached. The question is "where do I stand against everyone else", and
nothing on a desktop can answer it, because the answer requires having crawled the web.</li>
<li><strong>Auditors</strong>: where Docket sits. The question is "what should I change, in
what order", which is a judgement rather than a dataset, and it is the one that needs no
subscription because the data it needs is your own site.</li>
</ul>

<p>The practical consequence: if you already pay for a platform, Docket does not replace it.
It replaces the part of it you open once a month and then export to a spreadsheet.</p>

<h2>When not to use Docket</h2>

<p>If you need keyword positions or a backlink profile, none of these pages will help. Docket
has neither and is not building either. If your crawl is hundreds of thousands of URLs, use a
crawler built for it. Docket's desktop app runs on {MACOS} or later ({MAC_HW}){' and on 64-bit Windows' if WINDOWS else ''}.
Linux runs the command line only.</p>

<p>Each comparison below names at least one thing the other tool does better. That is not
modesty; a comparison page that concedes nothing tells you only that its author wanted your
money.</p>
""",
    ))
    out.append(hub(
        "learn",
        "SEO audit guides: AI crawlers, canonicals, page weight",
        "Guides to what an SEO audit checks and why: AI crawler access, canonical tags, "
        "JavaScript rendering, page weight, URL structure and how findings are ranked.",
        "Learn",
        "Reference pages, written to be read rather than skimmed for keywords.",
        [
            ("/learn/seo-audit-report/", "Read a real SEO audit report",
             "The score, ranked fixes and limits from a capped crawl of our own site."),
            ("/learn/free-seo-audit-api/", "Free SEO audit API options",
             "Google's key rules, a saved quota error and the local command options."),
            ("/best/free-seo-audit-plugins-wordpress/", "WordPress audit plugin claims",
             "What the plugin listings say they check and which audit features are paid."),
            ("/learn/answer-extractability/", "Answer extractability: can an AI quote your page?",
             "The check reads your question-form headings and nothing under them. What that "
             "measures, what nobody can measure, and why one is a proxy for the other."),
            ("/learn/trust-and-authorship-signals/", "Trust and authorship signals a crawler can see",
             "About, Contact and a privacy page are the reliable half. The authorship half is "
             "looser, and this is the page that says which is which."),
            ("/learn/email-capture-audit/", "The email-capture check that never looks at your form",
             "It reads body text, and body text is defined as the page minus nav, header, footer, "
             "aside and form. What that means for a footer signup."),
            ("/learn/ai-sounding-copy/", "Does your copy read as AI-written?",
             "Docket matches a register, not authorship. It cannot tell you who or what "
             "wrote a page. What it looks for, why it needs more than one tell, and what "
             "that finding is worth."),
            ("/learn/who-blocks-googlebot/", "Who blocks Googlebot, and who blocks GoogleOther",
             "We read robots.txt across a large public sample. A small share deny "
             "Googlebot and rather more deny GoogleOther: what that can, and cannot, "
             "tell you about a site."),
            ("/learn/does-cloudflare-block-gptbot/", "Does Cloudflare block GPTBot?",
             "Cloudflare changed what a new domain does by default, and the answer "
             "differs by which OpenAI crawler is asking. How to check your own."),
            ("/ai-crawlers/hosts/", "AI crawler access by host",
             "Dated host docs, bot controls and checks for your own site."),
            ("/learn/what-is-claudebot/", "What is ClaudeBot?",
             "Anthropic's training crawler, and the two other Anthropic crawlers that "
             "decide whether Claude can find and quote you. What blocking each one does."),
            ("/learn/what-is-llms-txt/", "What is llms.txt?",
             "A Markdown reading list for language models. What goes in it, how many large "
             "sites have one, and why Google says you do not need it."),
            ("/learn/what-is-a-sitemap/", "What is a sitemap?",
             "A list of the URLs you want search engines to find. What goes in one, which "
             "tags Google and Bing ignore, and what four real sitemaps showed."),
            ("/learn/what-is-alt-text/", "What is alt text?",
             "The words that stand in for an image. How to write them, when an empty alt is correct, "
             "and the length rule nobody official set."),
            ("/learn/what-is-structured-data/", "What is structured data?",
             "Markup that tells search engines what a page is about. The formats, what it cannot promise, "
             "and which features Google has retired."),
            ("/learn/what-is-robots-txt/", "What is robots.txt?",
             "A request to crawlers about which URLs not to fetch. How the rules match, "
             "and why it can't keep a page out of search."),
            ("/learn/what-is-a-404-error/", "What is a 404 error?",
             "The server found nothing at that address. When a 404 is harmless, when it isn't, "
             "and the soft 404 that looks fine and isn't."),
            ("/learn/what-is-a-favicon/", "What is a favicon?",
             "The small icon for your site in tabs, bookmarks and search results. "
             "Google's current size and format rules."),
            ("/learn/what-is-https/", "What is HTTPS?",
             "HTTP over an encrypted connection. What it proves and what it doesn't, "
             "and what browsers now do with sites that lack it."),
            ("/learn/what-is-a-url/", "What is a URL?",
             "The address of a page, in five parts. Which parts are case-sensitive, "
             "and why search engines see some variants as different pages."),
            ("/learn/what-is-a-subdomain/", "What is a subdomain?",
             "A name in front of your domain, like shop.example.com. Which search rules "
             "follow the hostname, and which follow the site."),
            ("/learn/does-noindex-stop-ai-crawlers/", "Does noindex stop AI crawlers?",
             "noindex tells an indexer not to list a page; it cannot stop a crawler "
             "fetching it. What robots.txt and your server control instead, and which "
             "layer is refusing yours."),
            ("/learn/click-depth-and-orphan-pages/", "Click depth and orphan pages",
             "How many clicks from the homepage a page sits, and which pages "
             "nothing links to. Plus the crawl conditions under which neither "
             "number means anything."),
            ("/learn/url-structure/", "URL structure: checked vs folklore",
             "What Docket actually enforces about URLs, and which popular rules "
             "have no published source behind them."),
            ("/learn/page-weight/", "Page weight and how heavy is too heavy",
             "Docket grades the HTML document, not the whole page, and says "
             "'at least' when the read was capped."),
            ("/learn/priority-model/", "How Docket decides what to fix first",
             "Severity, impact, reach and effort: the formula an audit ranks "
             "your site with, written out."),
            ("/learn/ai-crawler-directives/", "AI crawler directives: which to block",
             "Training crawlers and search crawlers are different decisions "
             "with different costs."),
            ("/learn/index-coverage/", "Is your page actually indexed?",
             "Whether a page is in Google, Bing or Brave is a fact about their "
             "index, not your HTML. What Docket asks each engine, and the places "
             "it refuses to guess."),
            ("/learn/ai-crawlers-and-sitemaps/", "AI crawlers and your sitemap",
             "A Sitemap: line is a non-group record, so every crawler is offered the "
             "same one, including the crawlers a site is trying to keep out."),
            ("/learn/www-vs-non-www/", "www or no www, and whether it still matters",
             "Every page-one result agrees you should pick one. None of them counted. "
             "We probed a random sample to see how many hosts still serve both."),
            ("/learn/internal-utm-links/", "Internal links that carry UTM parameters",
             "A site tagging its own internal links splits its analytics and can split "
             "its canonical signals. We crawled a sample and counted, and the affected "
             "hosts split into two different problems."),
            ("/learn/googlebot-2mb-limit/", "Googlebot's 2MB cutoff",
             "It reads the first 2MB and indexes that as the whole page. We measured "
             "well-known homepages and found five already past it."),
            ("/learn/audit-tool-accuracy/", "How to tell whether an audit tool is lying to you",
             "Four questions to ask of any SEO finding, each of them learned here by "
             "getting it wrong first."),
            ("/learn/what-docket-got-wrong/", "What Docket got wrong, and the release that fixed it",
             f"A dated list of the findings Docket got wrong, how each was found, which release "
             f"fixed it and the tests that hold it, then {len(corrections_cases.CASES)} worked cases of "
             f"findings that looked wrong."),
            ("/learn/log-file-analysis/", "Log file analysis: what Googlebot actually fetched",
             f"A user-agent proves nothing, which is why Google publishes "
             f"{F.gbot_total_prefixes():,} crawler IP prefixes. Reading a log honestly, "
             f"and where the dedicated tool wins."),
            ("/learn/brand-consistency/", "Brand consistency: the question no crawler asks",
             f"Of {F.brand_social_frame()} company sites linking social profiles, "
             f"{F.brand_social_undeclared()} declared none of them in schema. What the "
             f"brand area checks, and where design tools beat it."),
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
             "Ranking and not being visited. Measured on two live sites (this one at 5% "
             "fully substitutable, a delicatessen at 0%), and three ways we measured it "
             "wrong first."),
            ("/learn/ai-search-visibility/", "AI search visibility",
             "The three gates a model has to clear before it can cite you (access, rendering "
             "and entity clarity) with measured data on who is blocking what."),
            ("/learn/seo-audit/", "What an SEO audit covers",
             "Every area, in the order they should be worked, and the three tests a report has "
             "to pass to be worth acting on."),
            ("/learn/javascript-rendering/", "JavaScript rendering",
             "What a crawler that does not run JavaScript misses. Measured on a page that "
             "serves 0 characters of text and renders 2,068."),
            ("/learn/sameas-entity-signals/", "sameAs and entity signals",
             "The cheapest entity signal there is, and the share of major sites that skip "
             "it: measured, with the dataset attached."),
            ("/learn/canonical-tags/", "Canonical tags",
             "Google calls rel=canonical a hint and overrules it routinely. The seven "
             "ways it gets set wrong, and what each Search Console status is actually "
             "telling you."),
            ("/learn/internal-link-equity/", "Internal link equity",
             "The ranking signal your pages pass to each other, measured on our own site. "
             "Where the download page held a fifth of what an average page did."),
            ("/learn/what-docket-checks/", "What Docket checks",
             "All the checks, by area, with what each one actually looks at."),
        ],
    ))
    return out


def checks_page() -> Path:
    """Every check, from the shipped catalogue, not a hand-maintained list.

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
generated from the shipped build, so it cannot drift from what the tool actually does. Run
<code>docket checks</code> and you will get the same list.</p>

<p><a href="/checks/">Read what each check measures</a>, including its limits and what to review next.</p>

<p>Each check produces a finding only when there is something to report, and each finding
carries what it costs you, how much work the fix is, and the markup to paste. Areas that do
not apply to a site (local business checks on a pure SaaS product, for instance) are marked
not applicable rather than scored as passing.</p>

{''.join(sections)}

<h2>Where a check has a step-by-step fix</h2>
<p>A finding tells you what changed and hands you the markup. For the checks people most often
arrive here looking for, there is a longer walkthrough with the reasoning behind the fix:</p>
<ul>
<li><a href="/how-to/fix-ai-crawler-access/">AI crawler access</a>: which crawler does what, and
how to allow citation while refusing training.</li>
<li><a href="/how-to/fix-lang-attribute-mismatch/">hreflang and html lang mismatch</a>: the two are
different declarations and only one of them is usually wrong.</li>
<li><a href="/how-to/fix-missing-open-graph-tags/">Open Graph tags</a>: why a shared link shows no
image, and what each platform actually reads.</li>
<li><a href="/how-to/fix-missing-security-headers/">Security headers</a>: which ones a crawler
notices and which are for your users.</li>
<li><a href="/learn/marketing-tag-audit/">Marketing tag audit</a>: whether your tracking is on every
page, which is not the same question as whether it is installed.</li>
<li><a href="/learn/conversion-audit/">Conversion audit</a>: the nine checks that apply to a landing
page rather than to a crawl.</li>
<li><a href="/learn/email-capture-audit/">Email list building</a>: the check that never looks at a
form, and what it reads instead.</li>
<li><a href="/learn/click-depth-and-orphan-pages/">Click depth and orphan pages</a>: two findings from
one crawl, and the one that is withheld when the crawl was too partial.</li>
<li><a href="/how-to/fix-compression-and-caching/">Compression and caching headers</a>: what the check
reads, and the Brotli-only site it can report wrongly.</li>
<li><a href="/how-to/pages-an-audit-could-not-reach/">Pages that could not be reached</a>, with
<a href="/how-to/tell-a-rate-limit-from-a-block/">rate limits</a> and
<a href="/how-to/sitemap-urls-that-are-not-stale/">sitemap URLs</a>: three findings whose usual advice
is wrong for some sites.</li>
</ul>

<h2>How a finding is put together</h2>
<p>A check that fires produces more than a label. Each finding carries four things, and they
are what separate a plan from a list:</p>
<ul>
<li><strong>What it costs you</strong>, in plain language. Not "missing meta description" but
what happens as a result. Google writing your search snippet from whatever text it finds,
often a cookie notice.</li>
<li><strong>Severity</strong>, where critical is reserved for things that stop the page
ranking at all. If everything is critical, nothing is, so the bar is deliberately high.</li>
<li><strong>Effort</strong>, from minutes to a project. Combined with impact, this is what
produces the ordering. A trivial fix on an important page outranks a large fix on
a marginal one.</li>
<li><strong>The change itself</strong>, as markup you can copy. For structured data that means
a complete, valid JSON-LD block with your own business details already in the right fields.</li>
</ul>
<p>Findings are also capped in reach. An issue affecting every page of a large site does not automatically
outrank one affecting the homepage, because reach is compressed logarithmically: without
that, one trivial nit on a large site drowns out everything that matters.</p>

<h2>What is deliberately not here</h2>
<p>Per-page backlinks and anchor text. Domain authority and the list of referring domains
come from Common Crawl's hyperlink graph, but which individual page links to you, and with
what anchor text, lives in archive files far too large to fetch from a laptop. Search volumes. Docket finds the
queries people actually type, from Google's public autocomplete, and refuses to print a
monthly volume it does not have. Each is a real limitation and each is stated in the report
rather than papered over.</p>
<p>Comparing audit tools? Each of these pages sets out what the other tool costs and limits, read from
its own pages, and when to pick it instead of Docket:
<a href="/vs/se-ranking-vs-screaming-frog/">SE Ranking vs Screaming Frog</a>,
<a href="/vs/ahrefs-site-audit-alternative/">Docket vs Ahrefs Site Audit</a> and
<a href="/vs/seoptimer-alternative/">the SEOptimer alternative</a>.</p>
<p><a class="btn" href="/download/">Download Docket</a></p>
"""
    return render(
        cat="learn", slug="what-docket-checks",
        title=f"Docket SEO audit checklist: all {len(rows)} checks",
        desc=(
            (f"Every check in a Docket audit, by area: crawlability, AI search visibility, content, "
             f"structured data and speed. {len(rows)} checks in {len(by_lane)} areas, from the "
             f"app build.")
            if brand.SITE_BRAND == "checkengine"
            else (f"Every check in a Docket audit, by area: crawlability, AI search visibility, content, "
                  f"structured data and speed. {len(rows)} checks across {len(by_lane)} areas, "
                  "from the shipped build.")
        ),
        h1=f"All {len(rows)} Docket checks, by area",
        crumb='<a href="/">Docket</a> / <a href="/learn/">Learn</a> / What Docket checks',
        body=body,
    )


def write_robots() -> None:
    """Allow everything, and name the AI crawlers explicitly.

    Naming them costs nothing and makes the file self-documenting for whoever
    edits it next: which, given the Index found three quarters of blocking
    sites did it by accident, is the entire point.
    """
    lines = [
        f"# {brand.NAME}. {brand.HOST}",
        "# Everything is open, including AI search and training crawlers.",
        "# Named individually so the next person to edit this file can see the",
        "# difference between a search crawler and a training crawler.",
        "",
        "User-agent: *",
        "Allow: /",
        "",
        "# AI search crawlers: these decide whether we appear in AI answers.",
    ]
    for bot in ("OAI-SearchBot", "PerplexityBot", "Claude-SearchBot", ):
        lines += [f"User-agent: {bot}", "Allow: /", ""]
    lines.append("# Training crawlers. Allowed here; blocking these is a valid choice for others.")
    for bot in ("GPTBot", "ClaudeBot", "Applebot-Extended", "CCBot"):
        lines += [f"User-agent: {bot}", "Allow: /", ""]
    lines.append(f"Sitemap: {BASE}/sitemap.xml")
    (SITE / "robots.txt").write_text("\n".join(lines) + "\n")


#: The ten fix guides search engines show most, by docketseo.app's Search
#: Console reads of 2026-09-07 to 2026-09-24: page impressions where a read
#: lists the page, and the target query's impressions for the four written
#: after the first read. Matthew's order asked for "the best 10 how-tos". This
#: is a selection, so the slugs are listed here. Each title and summary is read
#: from the built page, so a retitle carries through. Re-pick from a fresh read;
#: never publish the counts.
LLMS_HOWTOS = (
    "fix-layout-shift", "fix-hreflang-return-tags", "fix-duplicate-title-tags",
    "write-title-tags-that-fit", "javascript-seo-audit", "fix-conflicting-canonicals",
    "content-audit", "fix-lang-attribute-mismatch", "backlink-audit",
    "redirect-http-to-https",
)


def write_llms_txt() -> None:
    """/llms.txt: an index of this site for language models, in the llmstxt.org
    shape (an H1, a blockquote summary, then H2 sections of annotated links).

    Matthew's order, 2026-09-26 01:28Z ("AI-search visibility"). Written here,
    beside robots.txt and the sitemap, so every build rewrites it with them.
    robots.txt allows every path to every agent, so nothing there blocks it.

    ⚠️ NO FACT IN THIS FUNCTION IS TYPED. The check count and the areas come
    from data/checks.csv, the price, the founding offer, the instalments and the
    sample report from render.py, the seat count from data/licence.json, and
    the macOS floor and download size from the shipped build's own record. A
    price typed here would be a second copy of render.PRICE, and the first time
    the two disagreed this file would be quoting the old one to every model that
    reads it. The wording is the site's own (the terms, the refund policy, the
    homepage), so this file says nothing a page does not.

    What /learn/ai-search-visibility/ says about llms.txt still stands: Google
    has said it ignores the file, and no study has measured an effect on
    citations. It costs nothing, and it is a genuine index of the site rather
    than a keyword list, which is the only kind worth publishing.
    """
    import csv
    import textwrap
    from collections import OrderedDict

    from render import (DMG_SIZE, FREE_LINE, MAC_HW, NO_BUILDS, size_article,
                        WINDOWS, WIN_PUBLISHER, WIN_SETUP_SIZE, HAS_SAMPLE, LINUX, MACOS,
                        N_CHECKS, N_LANES, price_sentence, CHECKOUT_HELP, REPO, SAMPLE_REPORT_URL, SELLER,
                        seller_address)

    # Same order as /learn/what-docket-checks/, which lists them from the same file.
    with (DATA / "checks.csv").open() as fh:
        lanes = list(OrderedDict.fromkeys(r["lane_label"] for r in csv.DictReader(fh)))
    areas = ", ".join(lanes[:-1]) + " and " + lanes[-1]
    seats = F.licence_activations()

    def wrap(text: str, first: str = "", rest: str = "") -> str:
        return textwrap.fill(text, width=86, initial_indent=first, subsequent_indent=rest,
                             break_long_words=False, break_on_hyphens=False)

    def facts(*items: str) -> list:
        return [wrap(t, "- ", "  ") for t in items if t]

    def links(*items: tuple) -> list:
        # One link per line, never wrapped, so a line-by-line reader gets the
        # whole entry.
        return [f"- [{name}]({url}): {note}" for name, url, note in items]

    knowledge_source = (brand.LEGACY_BASE + "/data/knowledge.json"
                        if brand.SITE_BRAND == "checkengine" else brand.HOST)
    if brand.SITE_BRAND == "checkengine":
        app_requests = (
            f"The app asks {brand.LEGACY_BASE}/updater.json whether an update exists. "
            "While its activation screen is showing on a copy with no key, it asks "
            f"{brand.LEGACY_BASE}/offer.json for the current price and offer and whether "
            "the founding offer is still open.")
    else:
        app_requests = (
            f"The app asks {brand.HOST} whether an update exists, and, while its activation "
            "screen is showing on a copy with no key, what the current price and offer "
            "are and whether the founding offer is still open.")

    out = ["# Docket SEO", ""]
    out.append(wrap(
        f"Docket SEO is a Mac and Windows app that audits any website on your own computer: {N_CHECKS} "
        f"checks across {N_LANES} areas, then one ranked plan of what to fix, in order, "
        f"with the markup to paste and a client-ready PDF report. {price_sentence()} "
        f"There is no subscription.", "> ", "> "))
    out += ["", wrap(
        "The crawl and the report stay on your computer, and there is no account. "
        "The app sends three anonymous counts, with no site address or audit result. "
        f"{F.optional_connectors_word().capitalize()} optional checks are on by "
        "default and reach outside it: Google PageSpeed Insights is sent the addresses of "
        "the homepage and top pages; Google's public autocomplete is sent the site's topic "
        "words, typed by the user or read off its titles, headings and descriptions; DNS is "
        "asked about "
        "the mail domains the site publishes; the audited server is asked what it tells AI "
        f"crawlers; and {knowledge_source} serves a knowledge file. Offline mode turns all "
        f"{F.optional_connectors_word()} off. Checking links to other sites, and rendering a "
        "few pages as a browser would, also reach the sites and services those pages link "
        "to or load. The licence key is checked with the payment provider when it is "
        f"activated and about once a day after that. {app_requests}")]
    out += ["", wrap(f"Docket is written by Matt Kerr and sold by {SELLER}, of "
                     f"{seller_address()}.")]

    out += ["", "## What it checks", ""]
    out += facts(
        f"{N_CHECKS} checks across {N_LANES} areas: {areas}.",
        "Every finding is ranked by impact against the effort of fixing it, and carries "
        "its evidence: the page it is on, the exact value found there, and the fix.",
        "AI search visibility: each AI crawler is checked separately (OAI-SearchBot for "
        "ChatGPT Search, PerplexityBot, Claude-SearchBot) and kept apart from training "
        "crawlers such as GPTBot. Google-Extended is reported as what it is: Gemini training "
        "and Gemini Apps grounding, with no effect on AI Overviews. Docket checks robots.txt "
        f"rules for {F.ai_agents()} AI crawlers. A separate check requests your homepage as "
        f"{len(F.probes()['ai'])} AI crawlers plus {F.probes()['search']} to find server refusals "
        "the file cannot show.",
        "A command-line interface ships inside the app. `docket audit` exits non-zero on a "
        "critical issue, so CI can fail a build before it ships.")
    out += links(
        (f"All {N_CHECKS} checks, by area", f"{BASE}/learn/what-docket-checks/",
         "the complete list, generated from the shipped build so it cannot drift from "
         "the product"),
        ("How Docket decides what to fix first", f"{BASE}/learn/priority-model/",
         "severity, impact, reach and effort, and the formula that combines them"))

    if HAS_SAMPLE:
        out += ["", "## Sample report", ""]
        out += links(
            ("Sample report (PDF)", SAMPLE_REPORT_URL,
             "a full sample of the client-ready PDF Docket writes: score, scorecard, "
             "ranked plan, paste-ready markup, and a page on what was and was not "
             "measured"))

    out += ["", "## Requirements", ""]
    out += facts(
        f"A Mac with {MAC_HW} running {MACOS} or later. {NO_BUILDS}",
        f"The Mac app is {size_article(DMG_SIZE)} {DMG_SIZE} download, signed with a Developer ID and notarised "
        f"by Apple.",
        (f"Or a PC with 64-bit Windows: the installer is {size_article(WIN_SETUP_SIZE)} {WIN_SETUP_SIZE} download, signed by "
         f"{WIN_PUBLISHER}.") if WINDOWS else "",
        "A command-line build for Linux x86_64 is on the download page." if LINUX else "",
        # CEO's order from Matthew, 2026-11-03: Claude and ChatGPT should know how to use the product.
        ("AI assistants can run it: Docket speaks MCP over stdio, so Claude Code "
         "(claude mcp add docket -- /Applications/Docket.app/Contents/Resources/docket/docket mcp), "
         "Claude Desktop and the ChatGPT desktop app can audit a site with it. Setup: "
         f"{BASE}/how-to/audit-your-site-from-an-ai-assistant/"))

    out += ["", "## Price and licence", ""]
    out += facts(
        f"{price_sentence()} Priced in US dollars. There is no renewal date and nothing to cancel.",
        html.unescape(re.sub(r"<[^>]+>", "", CHECKOUT_HELP)),
        f"{FREE_LINE} The free version needs no key and no account, and runs the same "
        f"full audit; buying unlocks the audit already run, with no second crawl.",
        f"The licence key arrives by email with the receipt and is pasted into the app "
        f"once. One licence covers {F.licence_covers()}: activating Docket on a "
        f"computer uses one, and deactivating one moves the licence to another.",
        "The licence belongs to the person or company that paid. It covers any number of "
        "websites, including clients' sites, and the work can be billed to those clients. "
        "The application itself may not be resold, sublicensed or redistributed.")

    out += ["", "## Refunds", ""]
    out += facts(
        "Thirty days from the date of purchase, no conditions and no questions asked. The "
        "full purchase price goes back to the payment method it came from.",
        f"To ask, write to {SUPPORT_EMAIL} or reply to the receipt {PROCESSOR} "
        f"sends.",
        "A refund revokes the licence key, and within about a day the copy goes back to "
        "the free version.")

    out += ["", "## What it does not do", ""]
    out += facts(
        "No per-page backlinks or anchor text, and no monthly search volumes.",
        "Copy-quality checks are English-only; the technical checks work in any language.",
        "Not built, on purpose: rank tracking, a cloud version, team accounts, server-side "
        "scheduling and uptime monitoring.",
        "Reports can carry your own name and logo in place of Docket's (paid version: Reports, "
        "then Report branding; or docket audit --brand-name and --brand-logo).",
        "Scheduled re-audits run only while Docket is open: the schedule is a thread "
        "inside the app, so quitting it stops the clock.")

    # The buyer's questions, from the homepage's own FAQ list rather than
    # restated, so the answers here are the answers there.
    import html as _html
    import re as _re

    def plain(text: str) -> str:
        return _html.unescape(_re.sub(r"<[^>]+>", "", text))

    out += ["", "## Frequently asked questions", ""]
    out += facts(*(f"{plain(q)} {plain(a)}" for q, a in home.FAQ))

    out += ["", "## Key pages", ""]
    out += links(
        ("Homepage", f"{BASE}/", "what Docket checks, how it ranks what it finds, and "
         "the price"),
        ("Download Docket SEO for Mac and Windows", f"{BASE}/download/", "the current release, the "
         "requirements, the price, and the command line"),
        ("The Docket Index", f"{BASE}/index/", "who is blocking AI search crawlers, "
         "measured with Docket's own parser; method and dataset included"),
        ("The AI rules in robots.txt that do nothing", f"{BASE}/index/ai-directives/",
         "which AI crawler rules in robots.txt name a token no crawler uses"),
        ("AI crawler blocking, August to October 2026", f"{BASE}/index/ai-crawler-blocking-2026-10/",
         "the same 10,000 sites read again two months later: who blocks which AI crawler, "
         "what changed, and how much of it is Cloudflare's managed robots.txt"),
        ("llms.txt in the top 10,000 sites, August to October 2026",
         f"{BASE}/index/llms-txt-adoption-2026-10/",
         "how many of the same 10,000 sites have a real llms.txt, how that moved in two "
         "months, and why a 200 answer is not proof of a file"),
        ("Learn", f"{BASE}/learn/", "plain explanations of what an SEO audit covers, how "
         "AI search visibility works, and what Docket checks"),
        ("Fix guides", f"{BASE}/how-to/", "the specific problems Docket reports, what "
         "each one costs you, and the change to make"),
        ("How Docket compares", f"{BASE}/vs/", "comparisons with Screaming Frog, "
         "Sitebulb, Ahrefs, Semrush and others, each naming at least one thing the "
         "other tool does better"),
        ("Docket for your situation", f"{BASE}/for/", "SEO agencies, developers, online "
         "shops, local businesses and SaaS companies"),
        ("Best tools, by job", f"{BASE}/best/", "which SEO tool fits which job, with "
         "every claim read from the product's own documentation"),
        ("Free AI crawler checker", f"{BASE}/tools/ai-crawler-checker/", "type an address "
         "and see which AI crawlers its robots.txt lets in, and what each block costs"),
        ("Free robots.txt tester", f"{BASE}/tools/robots-txt-tester/", "paste a page address "
         "and see whether Googlebot, Bingbot and the AI crawlers may crawl it, and which line decides"),
        ("Free title and meta tag checker", f"{BASE}/tools/meta-tag-checker/", "title and "
         "description width, noindex, canonical, H1 and Open Graph tags for one page"),
        ("Free JSON-LD checker", f"{BASE}/tools/json-ld-checker/", "invalid JSON by line and column, "
         "and the properties each structured data item needs for a rich result"),
        ("Free SEO checkers", f"{BASE}/tools/", "every free checker, each answering one question "
         "about one page"),
        ("AI search visibility", f"{BASE}/learn/ai-search-visibility/", "whether a model "
         "can reach, read and quote a site: crawler access, server-side rendering and "
         "entity clarity"),
        ("About Docket", f"{BASE}/about/", "who builds it and what it cannot do"),
        ("Contact", f"{BASE}/contact/", f"{SUPPORT_EMAIL} for a licence or a refund; the "
         "GitHub issue tracker for bugs and wrong findings"),
        ("The Docket crawler", f"{BASE}/bot/", "what Docket's audit crawler requests and "
         "the robots.txt rule that asks it to stay out"))

    # The footer's one off-site link, and no sibling domains: Bing reads sitewide
    # links between commonly owned sites as a link scheme (CEO, 2026-10-13).
    out += ["", "## Made by", ""]
    out += links(
        ("Kerr & Company", "https://kerrandcompanyholdings.com/", "the company behind Docket"))

    def page_entry(path: str) -> tuple:
        page = (SITE / path.strip("/") / "index.html").read_text(encoding="utf-8")
        title = _re.search(r"<title>([^<]+)</title>", page).group(1)
        desc = _re.search(r'<meta name="description" content="([^"]*)"', page).group(1)
        return (plain(title), f"{BASE}{path}", plain(desc))

    out += ["", "## Fix guides people search for most", ""]
    out += links(*(page_entry(f"/how-to/{slug}/") for slug in LLMS_HOWTOS))

    out += ["", "## Policies", ""]
    out += links(
        ("Privacy policy", f"{BASE}/legal/privacy/", "every request the app makes and who "
         "receives it, and the third-party scripts this website loads"),
        ("Terms of use", f"{BASE}/legal/terms/", "licence, price, delivery, refunds, "
         "liability and governing law"),
        ("Refund policy", f"{BASE}/legal/refunds/", "thirty days, no conditions; how to "
         "ask, and what happens to the copy afterwards"))

    out += ["", "## Optional", ""]
    out += links(
        ("All releases", f"{REPO}/releases", "every Docket release, on GitHub"),
        ("Sitemap", f"{BASE}/sitemap.xml", "every indexable page on this site"))

    text = brand.text("\n".join(out) + "\n")
    # These are reader links. The prose formatter otherwise retains their
    # machine hosts, just as it must for installed-app requests above.
    for url in (SAMPLE_REPORT_URL, f"{BASE}/bot/"):
        text = text.replace(f"]({brand.site_url(url)})", f"]({url})")
    (SITE / "llms.txt").write_text(text, encoding="utf-8")

    # Search Console's HTML-file proof of ownership for https://checkengineseo.com/ (asked for on 10 Nov 2026,
    # for the Change of Address from the docketseo.app property). Google re-checks it, so every build writes it.
    (SITE / "google384d8f3f1de83e9f.html").write_text(
        "google-site-verification: google384d8f3f1de83e9f.html\n", encoding="utf-8")


#: The day each page's content last changed, and the fingerprint it had then.
#: Seeded from history by scripts/collect_lastmod.py; updated by every build.
LASTMOD = DATA / brand.LASTMOD_FILE


def page_fingerprint(html: str) -> str:
    """What a reader of the page sees, hashed: title, description, article.

    ⚠️ NOT THE WHOLE FILE: a build id is stamped into the head of every page,
    so every page changes on every build (one content-unchanged page carried
    240 commits). And NOT the source module's git date, which is what this
    replaced (2026-09-24): one module builds many pages, so an edit to
    comparisons.py re-dated all fourteen /vs/ pages and nearly every URL read
    09-23. Nav and footer are outside the article and do not count; a change
    to them is not a change to the page's content.

    ⚠️ THE TEXT, NOT THE MARKUP (2026-10-21): the founding offer's switch added
    an attribute and a span around words that did not change, and every page
    with a Buy button was re-dated that day. Tags are dropped before hashing,
    so only a change a reader can see moves the date.
    """
    import re as _re
    title = _re.search(r"<title>(.*?)</title>", html, _re.S)
    desc = _re.search(r'<meta name="description" content="([^"]*)"', html)
    art = _re.search(r"<article\b.*</article>", html, _re.S)
    part = art.group(0) if art else html
    part = _re.sub(r"<script\b.*?</script>|<style\b.*?</style>", "", part, flags=_re.S)
    part = _re.sub(r"<[^>]+>", " ", part)
    blob = "\n".join([title.group(1) if title else "", desc.group(1) if desc else "",
                      _re.sub(r"\s+", " ", part)])
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()[:16]


def _last_changed(page: Path, today: str, store: dict) -> str:
    """The day this page's content last changed: kept while its fingerprint
    holds, today when it moves. A page never seen before is new today."""
    key = page.relative_to(SITE).as_posix()
    fp = page_fingerprint(page.read_text(encoding="utf-8"))
    rec = store.get(key)
    if rec and rec.get("hash") == fp:
        return rec["date"]
    store[key] = {"hash": fp, "date": today}
    return today


def write_sitemap(pages: list[Path]) -> None:
    today = datetime.date.today().isoformat()
    store = json.loads(LASTMOD.read_text(encoding="utf-8")) if LASTMOD.exists() else {}
    urls = []
    for p in sorted(pages):
        rel = p.parent.relative_to(SITE).as_posix()
        loc = BASE + "/" + (f"{rel}/" if rel != "." else "")
        # The homepage and the Index are the two pages worth prioritising; the
        # rest are equal. Priority is a weak signal at best, so it stays simple.
        priority = "1.0" if rel == "." else ("0.9" if rel == "index" else "0.7")
        lastmod = _last_changed(p, today, store)
        urls.append(f"  <url><loc>{loc}</loc><lastmod>{lastmod}</lastmod>"
                    f"<priority>{priority}</priority></url>")
    (SITE / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.w3.org/1999/sitemaps/0.9">\n'.replace(
            "www.w3.org/1999/sitemaps/0.9", "www.sitemaps.org/schemas/sitemap/0.9")
        + "\n".join(urls) + "\n</urlset>\n"
    )
    # Dropped pages leave the record with them, so a URL that comes back later
    # is dated the day it comes back.
    live = {p.relative_to(SITE).as_posix() for p in pages}
    store = {k: v for k, v in store.items() if k in live}
    LASTMOD.write_text(json.dumps(store, indent=1, sort_keys=True) + "\n", encoding="utf-8")


# Installed app builds 1.3.139 through 1.3.161 trust offer.json only when this
# matches their expected list price. The CEO's 2026-11-11 read-back changed the
# checkout to 3900 cents with a flat 950-cent code. Keep this compatibility value
# until the host confirms that app release 1.3.162, which expects 3900, has reached
# users. Then move it to PRICE * 100.
APP_LIST_PRICE_CENTS = 5900


def write_offer() -> None:
    """/offer.json: the price and offer the app's activation screen shows.

    The CEO's revenue audit, 2026-09-28: about 3,361 downloads, no sales, and
    the only screen an unactivated copy shows had no price and no way to buy.
    The app now shows both. Its EXPECTED_PRICE_CENTS must match
    APP_LIST_PRICE_CENTS for it to accept this file. checkout_price_cents
    carries the live list price from the CEO's 2026-11-11 read-back. The founding
    offer ENDS, so a code baked into a release would keep being advertised by
    every installed copy after it stopped working. This file carries the live
    offer instead, generated from the same constants as every buy button on
    the site, and the app falls back to the list price alone when it cannot
    read it.
    """
    from render import (BNPL_FOUNDING_OK, BNPL_LIVE, BNPL_MIN_CENTS, CHECKOUT, FOUNDING_CODE, FOUNDING_OPEN,
                        FOUNDING_ENDS_AT, FOUNDING_END_DAY, FOUNDING_AFTER_DAY, FOUNDING_OFF_CENTS, HAS_SAMPLE, LATER_PRICE, LATER_STR, REFUND_DAYS, SALE_NAME, APP_SAMPLE_REPORT_URL)
    import math
    price_cents = PRICE * 100
    founding_cents = price_cents - FOUNDING_OFF_CENTS
    offer = {
        "schema": 1,
        "later_price_cents": LATER_PRICE * 100,
        "later_from": datetime.date.fromisoformat(FOUNDING_ENDS_AT[:10]).isoformat(),
        "price_cents": APP_LIST_PRICE_CENTS,
        "checkout_price_cents": price_cents,
        "currency": "USD",
        "after_launch": ({"price_cents": LATER_PRICE * 100, "from": FOUNDING_AFTER_DAY,
                          "description": f"From {FOUNDING_AFTER_DAY}: {LATER_STR}."}
                         if FOUNDING_OPEN else None),
        "instalments": ({"count": 4, "cents": math.ceil(price_cents / 4),
                         "providers": ["Klarna", "Afterpay"], "every_days": 14}
                        if BNPL_LIVE and price_cents >= BNPL_MIN_CENTS else None),
        # null once the offer has ended; the app then shows the list price alone (offer.py).
        "founding": ({"price_cents": founding_cents,
                      # The flat-code price is under Dodo's floor, confirmed by the CEO on 2026-11-11.
                      # null suppresses the instalment beside that price in the app.
                      "instalment_cents": math.ceil(founding_cents / 4) if BNPL_FOUNDING_OK else None,
                      # No "seats" since 2026-11-02: the sale is uncapped. Builds up to 1.3.138 required it, but
                      # they also hold the old $349 list price, so they show no sale line from this file either way.
                      "code": FOUNDING_CODE, "label": SALE_NAME + ", through " + FOUNDING_END_DAY, "ends_at": FOUNDING_ENDS_AT}
                     if FOUNDING_OPEN else None),
        "refund_days": REFUND_DAYS,
        "checkout_url": CHECKOUT,
        # Our buy endpoint: makes the Dodo checkout with the founding code
        # applied while it is honoured, and records which button was pressed.
        "buy_url": "https://kerr-affiliate-hub.kerrco.workers.dev/buy/docket",
        "sample_report_url": APP_SAMPLE_REPORT_URL if HAS_SAMPLE else None,
    }
    (SITE / "offer.json").write_text(json.dumps(offer, indent=1) + "\n", encoding="utf-8")


def write_static() -> None:
    (SITE / "CNAME").write_text(brand.HOST + "\n")
    (ROOT / "workers/ai-crawler-check/src/site-brand.js").write_text(brand.worker_module(), encoding="utf-8")
    notices = SITE / "NOTICES.txt"
    _, _, notice_body = notices.read_text(encoding="utf-8").partition("\n")
    heading = (f"Third-party notices for {brand.HOST}" if brand.SITE_BRAND == "checkengine"
               else f"Third-party notices \N{EM DASH} {brand.HOST}")
    notices.write_text(heading + "\n" + notice_body, encoding="utf-8")

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
              "index-2026-08.json", "knowledge.json",
              "www-canonical-2026-09.json",
              "utm-internal-2026-09.json",
              "ai-crawler-blocking-2026-10.csv",
              "llms-adoption-2026-10.csv")
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
    if os.environ.get("DOCKET_SKIP_BRAND_ASSETS") == "1":
        print("SKIP brand image rendering: DOCKET_SKIP_BRAND_ASSETS=1")
    else:
        render_brand(SITE)
    (SITE / ".nojekyll").write_text("")


def _thank_you_xsell() -> str:
    """Matthew, 2026-11-07 ~00:3xZ via the CEO: "our other apps and bundle should be offered at some point in the
    checkout as well." BELOW the key steps and the support line, never above: this page is the handover, and what a
    buyer must do next comes first. Hub buy links only, nofollow, and no link to a sibling domain (verify_sibling_links:
    only /about/ may). Prices come from data/bundle.json through render.app_price, so the sale wording goes by itself
    at the first build after founding_ends_at (on the 1 December rebuild list)."""
    from render import HUB, app_price
    def item(name: str, key: str, slug: str, blurb: str) -> str:
        return (f'<li><strong>{name}</strong>: {blurb} {app_price(key)}. '
                f'<a href="{HUB}/buy/{slug}?src=ty-docket-xsell" rel="nofollow" data-ev="Buy" '
                f'data-ev-button="ty-docket-xsell-{slug}">Buy {name.split()[0]}</a></li>')
    return f"""
<h2>Also from Kerr &amp; Company</h2>
<ul class="tool-list">
{item("Crisp Video", "Crisp", "crisp", "Restores and upscales old video to 4K on your own Mac or PC.")}
{item("Outlier", "Outlier", "outlier", "Runs AI models on your Mac with no cloud and no subscription.")}
</ul>
<p>The three-app bundle is not offered here: it includes Docket SEO, which you have just bought.</p>
"""


#: "How did you find Docket?" (plan J3, 2026-11-08; the hub's POST /found/<app> is J4). One tap sends one word from this
#: fixed list to the hub, which adds one to a daily count by answer and country. No storage, no cookie, nothing sent
#: unless a button is pressed, and the question hides after it. ct=1 only on a real (trusted) click, as the hub's
#: snippet does for /dl and /buy. The list must match the hub's FOUND_ANSWERS (affiliate-hub/worker.js).
FOUND_ENDPOINT = "https://kerr-affiliate-hub.kerrco.workers.dev/found/docket"
FOUND_ANSWERS = (("claude", "Claude"), ("chatgpt", "ChatGPT"), ("google", "Google"), ("bing", "Bing"),
                 ("youtube", "YouTube"), ("reddit", "Reddit"), ("producthunt", "Product Hunt"),
                 ("friend", "A friend or colleague"), ("other", "Somewhere else"))


def _thank_you_found() -> str:
    buttons = "\n".join(f'<button type="button" class="btn-ghost" data-found="{key}">{label}</button>'
                         for key, label in FOUND_ANSWERS)
    return f"""
<section id="ty-found" aria-labelledby="ty-found-q">
<h2 id="ty-found-q">One question: how did you find Docket?</h2>
<p class="hero-note">One tap, optional. It sends only the answer you pick.</p>
<div class="found-row" style="display:flex;flex-wrap:wrap;gap:8px;margin:8px 0 16px">
{buttons}
</div>
<p id="ty-found-done" role="status" aria-live="polite"></p>
</section>
<script>(function(){{var box=document.getElementById('ty-found');if(!box)return;
box.addEventListener('click',function(e){{var b=e.target.closest&&e.target.closest('[data-found]');if(!b)return;
var u='{FOUND_ENDPOINT}?a='+encodeURIComponent(b.getAttribute('data-found'))+(e.isTrusted?'&ct=1':'');
try{{fetch(u,{{method:'POST',mode:'cors',credentials:'omit',keepalive:true}}).catch(function(){{}})}}catch(x){{}}
box.querySelector('.found-row').hidden=true;box.querySelector('.hero-note').hidden=true;
document.getElementById('ty-found-done').textContent='Thank you.';}});}})();</script>
"""


def thank_you() -> Path:
    """The page a buyer lands on after paying. Built 2026-08-19.

    WHY IT EXISTS. Three of the four products in this portfolio had nowhere for a
    purchase to land. Docket was one of them: the checkout finished on Polar's own
    confirmation screen, so at the moment of payment the buyer left docketseo.app
    and was never told anything by us.

    Three costs, and the third is the expensive one:
      - no sale is countable in analytics, ads or no ads;
      - a Meta `Purchase` event has nowhere to fire, so a campaign has nothing to
        optimise toward, and the symptom of that reads as "the pixel is broken",
        which sends somebody to debug the pixel while the real fault is a missing
        page;
      - the buyer is dropped at peak intent with no idea what happens next, which
        is what turns into a refund request rather than a missing metric.

    ⚠️ WHAT THIS PAGE DELIBERATELY DOES NOT SAY, and why each was left out:

      - **No licence key, and no activation steps.** Docket's site mentions a key
        exactly zero times, and the shipped 1.1.57 build exposes no licence route
        at all: every feature is already open. Telling a buyer to "activate" would
        describe a mechanism that does not exist in the product they just paid for.
      - **No delivery time.** Not "within a minute", not "shortly". No purchase has
        ever completed on this product, so any number here would be a promise
        nobody has measured.
      - **No support response time**, for the same reason.

    Every link below was checked live before shipping: /download/ 200,
    /legal/refunds/ 200, /contact/ 200, and hello@docketseo.app is the address the
    contact page already publishes.

    ⚠️ THIS PAGE WENT FALSE TWICE AND IS THE WORST PLACE ON THE SITE FOR THAT.
    It is what a customer reads in the seconds after the price leaves their account.

    It said the receipt comes from POLAR, for days after the checkout moved to
    Dodo, so a buyer would watch for an email from a company that never took
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
<p id="ty-lede">Your payment went through. The receipt comes by email from Dodo
Payments, who handle the checkout. It may land under a different sender name
than Docket.</p>

<!-- The key, straight off the URL Dodo redirects to. Hidden until there is one:
     an empty box under "your payment went through" reads as a failure. Filled
     with textContent, never innerHTML. The value arrives in a query string, so
     it is attacker-controllable and this URL is the kind of thing people forward. -->
<p id="ty-key-wrap" hidden><strong>Your licence key:</strong>
  <code id="ty-key" style="user-select:all"></code>
  <br><small>Also in your email. Paste it into <strong>Enter licence key</strong>.</small></p>

<h2 id="ty-key-head">Your licence key is in that email</h2>
<p>Docket needs it before it will run an audit. Open the app, click
<strong>Enter licence key</strong> in the title bar, and paste it in. From a
terminal, <code>docket licence --key YOUR-KEY</code> does the same thing.</p>
<p>One licence covers __COVERS__. The key is stored on your own computer.</p>
<p><a class="btn" href="/download/">Download Docket</a></p>

<h2>If something is wrong</h2>
<p>Email <a href="mailto:__SUPPORT__">__SUPPORT__</a> and say what
happened. If the purchase was a mistake, the
<a href="/legal/refunds/">refund policy</a> is on this site and it is short.</p>
__FOUND__
__XSELL__"""
    return render(
        cat="", slug="thank-you",
        title="Thank you | Docket",
        desc="Your Docket purchase is complete. Where to download the app and how to reach us.",
        h1="Thank you",
        crumb='<a href="/">Docket</a> / Thank you',
        body=(body.replace("__SUPPORT__", SUPPORT_EMAIL).replace("__COVERS__", F.licence_covers())
              .replace("__XSELL__", _thank_you_xsell()).replace("__FOUND__", _thank_you_found())),
        # ⚠️ This page told buyers to email hello@docketseo.app — the address
        # Matthew replaced with support@ on 2026-08-13 and ~/ops/bin/contact-gate
        # lists as DISOWNED. The gate never saw it: /thank-you/ is noindexed and
        # linked from nowhere, so a crawl of the site cannot reach the one page
        # every buyer lands on. Found 2026-09-24 reading the page by hand. The
        # address now comes from render.SUPPORT_EMAIL like every other page's.
        closer=(_THANK_YOU_JS.replace("__PRICE__", str(PRICE)).replace("__SUPPORT__", SUPPORT_EMAIL)
                .replace("__PAID_ENDPOINT__", PAID_ENDPOINT)),
        schema_type="",
        noindex=True,
    )


#: ⚠️ ADDING THE REDIRECT IS WHAT MAKES THIS NECESSARY, so it ships in the same
#: change. Until the buy link carried redirect_url, nothing could reach
#: /thank-you/ except somebody typing the URL, so "Your payment went through"
#: was safe to state unconditionally. The moment Dodo starts redirecting here it
#: sends DECLINED cards too — and the fix, shipped alone, would begin telling
#: people their payment succeeded when it did not. That is a defect created by
#: the remedy, and it is worse than the problem it solves. Found by the Crisp
#: session on its own page before either of us shipped.
#:
#: Purchase fires ONLY on status=succeeded. Firing on a failure teaches the ad
#: account to optimise toward people who could not pay. eventID=payment_id so a
#: later CAPI event dedupes against this one; sessionStorage keyed on the same id
#: so a reload or a forwarded link does not count a second sale, while a genuine
#: second purchase still does.
_THANK_YOU_JS = """
<script>
(function () {
  // The head's RETURN_URL_SCRUB has already copied the checkout's parameters
  // here and removed them from the address, so no tracker saw the key.
  var ret = window.__dkReturn || {};
  var q = { get: function (k) { return ret[k] || null; } };
  var status = (q.get('status') || '').toLowerCase();
  var key = q.get('license_key');
  var pid = q.get('payment_id');
  var $ = function (id) { return document.getElementById(id); };

  if (status && status !== 'succeeded') {
    var h1 = document.querySelector('h1');
    if (h1) h1.textContent = 'That payment did not go through';
    if ($('ty-lede')) $('ty-lede').textContent =
      'Your card was not charged. You can try again from the pricing section, or '
      + 'email __SUPPORT__ and we will sort it out.';
    if ($('ty-key-head')) $('ty-key-head').hidden = true;
    return;
  }

  if (key && $('ty-key') && $('ty-key-wrap')) {
    $('ty-key').textContent = key;          // textContent, never innerHTML
    $('ty-key-wrap').hidden = false;
    if ($('ty-key-head')) $('ty-key-head').textContent = 'Your licence key';
  }

  // Plausible "Purchase" with revenue, once per payment_id. The amount is the
  // price on offer when the Buy button was clicked (stored by the site-wide
  // click listener), because Dodo's redirect carries none; with nothing stored
  // it is the list price. A founding buyer who typed the code is therefore
  // recorded at the price they clicked, not the discounted total.
  // The amount recorded with a purchase. First choice: what the buyer actually
  // paid, from our hub's /paid (a succeeded payment from the last 72 hours; it
  // returns only the amount, currency and app, never anything about the
  // buyer). Before that existed, the best available was the price on offer
  // when Buy was clicked (dk_offer), else the list price, and that stays the
  // fallback if /paid answers 404, fails or takes too long. A founding buyer
  // was recorded at $349 while paying $174.50.
  var amt = __PRICE__;
  try { amt = parseFloat(localStorage.getItem('dk_offer')) || __PRICE__; } catch (e) {}

  var record = function (value) {
    var pk = 'dk_pl_purchase_' + (pid || 'nopid');
    var sendP = function () {
      if (typeof plausible === 'function')
        plausible('Purchase', { revenue: { currency: 'USD', amount: value } });
    };
    try {
      if (!localStorage.getItem(pk)) { localStorage.setItem(pk, '1'); sendP(); }
    } catch (e) { sendP(); }

    // The Meta Purchase event that stood here went with the pixel, 2026-11-06 (Matthew: "Remove it").
  };

  if (status !== 'succeeded') return;
  if (!pid || !window.fetch) { record(amt); return; }
  var done = false;
  var finish = function (value) { if (done) return; done = true; record(value); };
  setTimeout(function () { finish(amt); }, 4000);
  fetch('__PAID_ENDPOINT__?payment_id=' + encodeURIComponent(pid))
    .then(function (r) { return r.ok ? r.json() : null; })
    .then(function (j) {
      var v = j && typeof j.amount === 'number' && j.amount > 0 && j.amount < 100000 ? j.amount : amt;
      finish(v);
    })
    .catch(function () { finish(amt); });
})();
</script>
"""


#: What a payment actually came to. Our hub answers for a succeeded payment
#: from the last 72 hours with {"amount", "currency", "app"} and nothing about
#: the buyer; CORS allows only https://docketseo.app.
PAID_ENDPOINT = "https://kerr-affiliate-hub.kerrco.workers.dev/paid"


#: Where every Buy outside this site's own buttons goes: the app's menu, its
#: offline fallback, release notes. Our buy endpoint makes the current Dodo
#: checkout (founding code applied while it is honoured) and records `src`.
BUY_ENDPOINT = "https://kerr-affiliate-hub.kerrco.workers.dev/buy/docket"


def buy_redirect() -> Path:
    """/buy/. A stable address on our own domain that forwards to the buy
    endpoint, keeping `src`.

    Docket 1.3.95 compiles https://docketseo.app/buy/?src=app-menu into the app.
    A payment link frozen into a binary cannot follow a vendor move, and a
    workers.dev address is less durable than our own domain. This page is ours,
    so a release never has to change when the checkout does. Noindexed, not in
    the sitemap, linked from nowhere on the site, like /thank-you/.
    """
    body = f"""
<p class="lede" id="buy-lede">Taking you to the secure checkout&hellip;</p>
<p>If nothing happens, <a id="buy-go" href="{BUY_ENDPOINT}?src=site-buy">continue to checkout</a>.</p>
<script>
(function () {{
  var raw = new URLSearchParams(location.search).get('src') || 'site-buy';
  var src = raw.replace(/[^a-zA-Z0-9-]/g, '').slice(0, 40) || 'site-buy';
  var to = {json.dumps(BUY_ENDPOINT)} + '?src=' + encodeURIComponent(src);
  var a = document.getElementById('buy-go');
  if (a) a.href = to;
  location.replace(to);
}})();
</script>
"""
    return render(
        cat="", slug="buy",
        title="Buy Docket SEO",
        desc="Forwarding to the secure checkout for Docket SEO.",
        h1="Buy Docket",
        crumb='<a href="/">Docket</a> / Buy',
        body=body,
        schema_type="",
        noindex=True,
    )


def pricing_page() -> Path:
    """/pricing/: the address people and AI assistants guess first.

    It answered 404 until 2026-09-30 (CEO). A small real page, the same shape as
    outlier.host/pricing/: noindexed with a self canonical, one heading, and the
    homepage's own buy block, so every number on it comes from the same source
    as every other price on the site. Not in the sitemap: it is a door, not an
    article.
    """
    from render import (DMG_SIZE, FOUNDING_AFTER_DAY, FREE_LINE, MAC_HW, MACOS, MACS, NO_BUILDS, price_sentence, REFUND_DAYS,
                        FOUNDING_END_DAY, PRICE_COMPACT, SALE_NAME, WINDOWS, WIN_SETUP, WIN_SETUP_SIZE,
                        buy_block, download_url, windows_waitlist)
    # The prose below is this page's own. The quality gate's duplicate check
    # judged the first version (the buy block alone) a copy of 18 pages,
    # rightly: a page that is only the shared block says nothing of its own.
    # Every fact is from the terms, the refund policy and the FAQ, re-worded.
    bundle = json.loads((DATA / "bundle.json").read_text(encoding="utf-8"))
    # The founding bundle price is promised only until the founding codes end;
    # after that moment the page states the standard price instead, so a rebuild is
    # all it takes to stop quoting a price the checkout no longer gives. The moment,
    # not the day: the codes expire at 01:26:53Z on 25 November, and a date compare
    # kept the founding price on the page for the rest of that day.
    founding = (datetime.datetime.now(datetime.timezone.utc)
                < datetime.datetime.fromisoformat(bundle["founding_ends_at"].replace("Z", "+00:00")))
    apps = ", ".join(bundle["apps"][:-1]) + " and " + bundle["apps"][-1]
    # $49.50 since 2026-11-02: a whole-dollar format printed "$49.5".
    def usd(x):
        return f"${x:,.2f}" if x != int(x) else f"${int(x):,}"
    bundle_line = (
        f'<a href="{bundle["url"]}?src=docket-pricing" data-ev="Buy" data-ev-button="pricing-bundle">'
        f'All three apps, {apps}, for {usd(bundle["founding_price"])} once: the launch price, through {FOUNDING_END_DAY}.</a> '
        f'From {FOUNDING_AFTER_DAY} it is {usd(bundle["standard_price"])}.'
        if founding else
        f'<a href="{bundle["url"]}?src=docket-pricing" data-ev="Buy" data-ev-button="pricing-bundle">'
        f'All three apps, {apps}, for {usd(bundle["standard_price"])} once.</a>')
    apart = sum(bundle["list_prices"].values())
    bundle_sum = (f'{usd(apart)} bought apart, '
                  f'{usd(bundle["standard_price"])} together.')
    if founding:
        launch_apart = apart * (100 - bundle["founding_pct"]) / 100
        bundle_sum += (
            f' <span data-founding-until="{bundle["founding_ends_at"]}">'
            f'{SALE_NAME} through {FOUNDING_END_DAY}: '
            f'{usd(launch_apart)} bought apart, {usd(bundle["founding_price"])} together.</span>')
    body = f"""
<p class="lede">One price, paid once. No subscription, no page meter, nothing to cancel.</p>
{buy_block("pricing-page", try_app="pricing-page-try-free", phone=False)}
<p class="hero-note"{' data-founding-until="' + bundle["founding_ends_at"] + '"' if founding else ""}>{bundle_line}</p>
<p class="hero-note" id="bundle-sum">{bundle_sum}</p>
<p class="hero-note">Bought it already? <a href="{download_url('pricing-page')}" data-ev="Download"
data-ev-button="pricing-page">Get the {DMG_SIZE} Mac download</a>{(f' or <a href="{download_url("pricing-page-windows", to=WIN_SETUP)}" data-ev="Download" data-ev-button="pricing-page-windows">the {WIN_SETUP_SIZE} Windows installer</a>') if WINDOWS else ''} and paste the key from your receipt.</p>

<h2>What an audit costs elsewhere</h2>
<p>{comparisons.source_link("SEOProfy", "https://seoprofy.com/blog/seo-audit-pricing/")} quotes an SEO audit at {comparisons.SEO_AUDIT_RANGE}, read 12 November 2026.
{comparisons.source_link("WebFX", "https://www.webfx.com/seo/pricing/how-much-does-seo-audit-cost/")}'s survey says most businesses, {comparisons.WEBFX_AUDIT_SHARE}, pay {comparisons.WEBFX_AUDIT_RANGE} for an audit, read 12 November 2026.
{comparisons.source_link("Ahrefs", "https://ahrefs.com/blog/seo-pricing/")} says agencies charge {comparisons.AGENCY_SEO_MONTHLY} a month on average for SEO, read 12 November 2026.</p>
<p>Check Engine finds and ranks what is wrong and shows the fix. It does not do the fixing for you.</p>
<p>Check Engine is {PRICE_COMPACT}.</p>
{comparisons._verified_note("audit-agency-prices-pricing", closing="Prices vary with the work and the site.")}

<h2>What you get</h2>
<ul>
<li>A Docket licence for life, in US dollars, with no renewal date. Use it on {F.licence_covers()},
and move it by deactivating one.</li>
<li>No limit on sites. Audit your own, a client's or a prospect's, as often as you want, and
bill clients for the work. Nothing is counted per page or per site.</li>
<li>Every 1.x release, delivered by the updater inside the app. If a 2.0 ever costs money,
the version you bought keeps running.</li>
<li>The key by email, on the receipt. No account to sign up for. The app sends three anonymous counts,
with no site address or audit result. <a href="/legal/privacy/">What is sent and how to turn it off</a>.</li>
</ul>

<h2>How paying works</h2>
<p>The checkout belongs to Dodo Payments, the reseller and merchant of record for the sale.
Pay the whole amount at once.</p>

<h2>When the price changes</h2>
<p>The {SALE_NAME.lower()} applies to everything bought up to the end of {FOUNDING_END_DAY}; the price from {FOUNDING_AFTER_DAY}
applies to everything bought after it. Either way you pay once. Nothing is taken on the day the price changes, nothing renews,
and a licence bought at the {SALE_NAME.lower()} is never asked to pay the difference later.</p>

<h2>If Docket turns out not to suit you</h2>
<p>Within {REFUND_DAYS} days of the receipt date, write to the support address or reply to the
receipt and you get every cent back, to whatever you paid with. There are no conditions and no
form. The refund revokes the key, so within roughly a day the app goes back to the free
version.</p>

<h2>What is free</h2>
<p>{FREE_LINE} The free version needs no key and no account and runs the same full audit, so
you can see how much is wrong on your site, and the worst of it, before you pay for the rest.</p>

<h2>Before you buy: what it runs on</h2>
<p>A Mac with {MAC_HW}, on {MACOS} or later{', or a PC with 64-bit Windows' if WINDOWS else ''}. {NO_BUILDS} If
you are unsure, open the full sample report first; it shows what an audit hands you.</p>
{windows_waitlist("pricing")}

<h2>Writing or making videos about Docket?</h2>
<p>Kerr &amp; Company, the company that sells Docket, runs an affiliate programme that pays a
commission on each sale, using a personal code the buyer enters at checkout instead of a tracking
link. The rates, the payout terms and the disclosure you owe your readers are on the affiliates page
of the Kerr &amp; Company site (kerrandcompanyholdings.com/affiliates), linked from the footer.</p>
"""
    return render(
        cat="", slug="pricing",
        title="Docket pricing and licence",
        desc=f"{price_sentence()} For {MACS}. No subscription.",
        h1="Docket pricing",
        crumb='<a href="/">Docket</a> / Pricing',
        body=body,
        schema_type="",
        noindex=True,
        self_canonical=True,
    )


def not_found() -> Path:
    """/404.html. GitHub Pages serves this for any path that does not exist.

    Written because the default is GitHub's own page: their branding, their
    404 graphic, no way back into the site. A site whose whole argument is that
    it checks the things nobody checks should not leak someone else's error
    page to its own visitors.

    Noindexed and without a canonical, because a soft 404 that search engines
    can index is worse than no page. It is the failure mode this site measured
    in llms.txt handlers.
    """
    body = """
<p class="lede">That page does not exist. The likeliest reason is a link that pointed at a
draft, or a URL that moved when the section was reorganised.</p>

<p>Everything on the site is one of five things:</p>

<ul>
<li><a href="/index/">The Index</a>: first-party measurements. Who blocks which AI crawlers,
and <a href="/index/ai-directives/">which robots.txt rules do nothing</a>.</li>
<li><a href="/learn/">Learn</a>: what an audit covers, AI search visibility, link equity,
JavaScript rendering, entity signals.</li>
<li><a href="/vs/">Compare</a>: honest comparisons against Screaming Frog, Sitebulb, Ahrefs
and Semrush Site Audit, each naming what the other does better.</li>
<li><a href="/how-to/">Fix it</a>: the exact change to make for a specific finding.</li>
<li><a href="/download/">Download</a>: the app itself, and the command line inside it.</li>
</ul>

<p><a class="btn" href="/">Back to the start</a></p>
"""
    return render(
        cat="", slug="",
        title="Page not found | Docket",
        desc="That page does not exist. Where everything on docketseo.app lives.",
        h1="Page not found",
        crumb='<a href="/">Docket</a> / Not found',
        body=body,
        schema_type="",
        filename="404.html",
        noindex=True,
    )


def legal_redirect_stubs() -> list[Path]:
    """Keep guessed legal addresses working, using the existing Moved stub shape."""
    from render import BING_SITE_VERIFICATION

    redirects = {
        "privacy": ("Privacy policy", "/legal/privacy/"),
        "terms": ("Terms", "/legal/terms/"),
        "refund": ("Refunds", "/legal/refunds/"),
        "refunds": ("Refunds", "/legal/refunds/"),
        "legal": ("Privacy policy", "/legal/privacy/"),
    }
    pages = []
    for slug, (title, target) in redirects.items():
        page = SITE / slug / "index.html"
        page.parent.mkdir(parents=True, exist_ok=True)
        page.write_text(f'''<!doctype html><html lang="en"><head><meta charset="utf-8">
{BING_SITE_VERIFICATION}
<title>Moved: {title}</title>
<link rel="canonical" href="{BASE}{target}">
<meta name="robots" content="noindex,follow">
<meta http-equiv="refresh" content="0; url={target}">
</head><body>
<p>This page has moved to <a href="{target}">{target}</a>.</p>
<footer>
<p>Made by <a href="https://kerrandcompanyholdings.com/">Kerr &amp; Company</a></p>
</footer>
</body></html>
''', encoding="utf-8")
        pages.append(page)
    return pages


def stamp_build_id() -> str:
    """One id over the whole tree, so a stale deploy is detectable from outside.

    The failure this exists for, 2026-08-17: two commits were merged and green,
    the built site/ carried a screenshot and a refund line, and the live site
    served neither. Every gate in deploy.sh checks the BUILD; nothing checked
    that the build reached the CDN, and the answer arrived as "dockets site is
    still the same or its not updating". Matthew made it rule 0.8 the next day:
    a commit is not a ship.

    A hash of index.html alone cannot see it: the .webp that 404'd is not in
    index.html. So this hashes every file under site/, with the placeholder
    still in place, and rewrites the placeholder afterwards. Nothing is hashed
    twice: the placeholder is a fixed-length constant, so stamping cannot change
    the id it stamps.
    """
    manifest = []
    for path in sorted(SITE.rglob("*")):
        if path.is_dir() or path.name in {".nojekyll", "_redirect-map.json"}:
            continue
        manifest.append(path.relative_to(SITE).as_posix().encode()
                        + b"\0" + hashlib.sha256(path.read_bytes()).hexdigest().encode())
    build_id = hashlib.sha256(b"\n".join(manifest)).hexdigest()[:12]

    for page in SITE.rglob("*.html"):
        raw = page.read_text(encoding="utf-8")
        if "__BUILD_ID__" in raw:
            page.write_text(raw.replace("__BUILD_ID__", build_id), encoding="utf-8")
    # ⚠️ THE ANCHOR FILE IS WRITTEN ONLY BY A DEPLOY, AND HERE IS WHY.
    #
    # `data/build-id.txt` is what the deployed-matches-committed gate compares
    # the live build against. Every local `build.py` run used to rewrite it, so
    # the checkout went dirty whenever anyone built without deploying — and by
    # 2026-09-15 that was most runs, because a full audit of our own site became
    # a per-cycle routine. The ops checklist row failed for two hours on exactly
    # that.
    #
    # Committing the local value was the wrong fix, even when it happened to
    # match production: "a local build that happens to match is exactly the case
    # where the next one silently will not" (CEO, 2026-09-15). The gate must stay
    # strict, so the file must stop moving unless a deploy moved it.
    #
    # `deploy.sh` exports DOCKET_DEPLOY=1 before calling this. Any other run
    # writes the id to a scratch path instead, so it is still inspectable and
    # the tree stays clean.
    if os.environ.get("DOCKET_DEPLOY") == "1":
        (DATA).mkdir(parents=True, exist_ok=True)
        (DATA / "build-id.txt").write_text(build_id + "\n", encoding="utf-8")
    else:
        scratch = Path(tempfile.gettempdir()) / "docket-build-id.txt"
        scratch.write_text(build_id + "\n", encoding="utf-8")
    return build_id


def main() -> int:
    pages: list[Path] = [home.build(), index_page.build(), checks_page()]
    pages += comparisons.build_all()
    pages += [best_free.best_hub(), best_free.free_seo_audit_tools(), sf_alternatives.sf_alternatives(),
              white_label.white_label_tools()]
    pages += [howto_https.http_to_https(),
              howto_hreflang.hreflang_return_tags(),
              howto_canonicals.conflicting_canonicals(),
              howto_competing_pages.competing_pages(),
              howto_money_pages.money_pages(),
              howto_mobile.mobile(),
              howto_pagination.pagination(),
              howto_utility_pages.utility_pages(),
              howto_meta_refresh.meta_refresh(),
              howto_schema_mismatch.schema_mismatch(),
              howto_positioning.positioning(),
              howto_voice.voice(),
              howto_sameas.sameas(),
              howto_rate_limits.rate_limits(),
              howto_cta_forms.cta_forms(),
              howto_brand_name.brand_name(),
              howto_unreachable.unreachable(),
              howto_sitemap_dead_urls.sitemap_dead_urls(),
              howto_caveat_gate.caveat_gate(),
              howto_identical_bodies.identical_bodies(),
              howto_placeholder_text.placeholder_text(),
              howto_json_ld_errors.json_ld_errors(),
              howto_hreflang_targets.hreflang_targets(),
              howto_analytics_findings.analytics_findings(),
              howto_schema_type.schema_type(),
              howto_missing_means_empty.missing_means_empty(),
              howto_address_region.address_region(),
              howto_type_matching.type_matching(),
              bot.bot(),
              howto_soft404.soft_404s(),
              howto_open_graph.howto_open_graph(),
              howto_deploy_gate.deploy_gate(),
              howto_security_headers.security_headers(),
              howto_schema.structured_data_errors(),
              howto_cls.layout_shift(),
              howto_render_blocking.render_blocking(),
              howto_link_text.link_text(),
              howto_meta_descriptions.meta_descriptions(),
              howto_image_formats.image_formats(),
              howto_thin_content.thin_content(),
              howto_ttfb.ttfb(),
              howto_nap.nap(),
              howto_favicon.favicon(),
              mac_options.mac_options(),
              howto_mcp.mcp_setup(),
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
    pages += howto_js_audit.build_all()
    pages += howto_content_audit.build_all()
    pages += howto_lang_mismatch.build_all()
    pages += howto_backlink_audit.build_all()
    pages += cloudflare_gptbot.build_all()
    pages += howto_cdn_blocks_ai.build_all()
    pages += index_coverage.build_all()
    pages += click_depth_orphans.build_all()
    pages += url_structure.build_all()
    pages += howto_hreflang_codes.build_all()
    pages += page_weight.build_all()
    pages += priority_model.build_all()
    pages += ai_directives.build_all()
    pages += ai_crawler_blocking.build_all()
    pages += ai_crawler_pages.build_all()
    pages += ai_bot_host_pages.build_all()
    pages += llms_adoption.build_all()
    pages += noindex_ai_crawlers.build_all()
    pages += sitemaps_ai_crawlers.build_all()
    pages += googlebot_robots_blocks.build_all()
    pages += www_vs_apex.build_all()
    pages += internal_utm.build_all()
    pages += substitution.build_all()
    pages += __import__('pages').build_all()
    pages += about.build_all()
    pages += audit_quality.build_all()
    pages += corrections.build_all()
    pages += brand_article.build_all()
    pages += logs_article.build_all()
    pages += mailcheck.build_all()
    pages += ai_slop.build_all()
    pages += howto_nav_js.build_all()
    pages += howto_phone.build_all()
    pages += eeat.build_all()
    pages += howto_images.build_all()
    pages += email_capture.build_all()
    pages += howto_redirects.build_all()
    pages += howto_headings.build_all()
    pages += howto_broken_links.build_all()
    pages += howto_compression.build_all()
    pages += extractability.build_all()
    pages += tool_ai_crawlers.build_all()
    pages += tools_free.build_all()
    pages.append(tools_website_checker.website_checker())
    pages += ai_assistants.build_all()
    pages += ai_questions.build_all()
    pages += title_ii.build_all()
    pages += public_site_check.build_all()
    pages += help_pages.build_all()
    pages += check_pages.build_all()
    pages += learn_seo_audit_report.build_all()
    pages += best_free_seo_audit_plugins.build_all()
    pages += learn_free_seo_audit_api.build_all()
    pages += build_hubs()

    # NOT appended to `pages`: the sitemap is derived from that list, and
    # render() resolves an empty cat+slug to the site root, so including the
    # 404 emitted a second <loc>https://docketseo.app/</loc> — a duplicate entry
    # is an invalid sitemap. It is also a page that must never be indexed.
    not_found()
    thank_you()
    buy_redirect()
    pricing_page()
    # Redirect stubs are not sitemap entries, just like the retired article addresses.
    legal_redirect_stubs()

    write_robots()
    write_llms_txt()
    write_offer()
    write_sitemap(pages)
    write_static()
    stamp_competitor_claims(pages)

    # Redirects predate the assembler. Their source copy lets either brand be
    # rebuilt after the other without carrying words over from the last mode.
    redirects = json.loads((DATA / "redirect-pages.json").read_text(encoding="utf-8"))
    for relative, source in redirects.items():
        branded = brand.html(source)
        if brand.FORMERLY:
            branded = branded.replace("</footer>", brand.formerly_note() + "</footer>", 1)
        (SITE / relative).write_text(branded, encoding="utf-8")

    # This inventory is derived from the tree and excluded from the build-id
    # input so adding it cannot change an otherwise identical default build.
    paths = set()
    for path in SITE.rglob("*"):
        if path.is_file():
            rel = "/" + path.relative_to(SITE).as_posix()
            paths.add(rel)
            if path.name == "index.html":
                paths.add(rel.removesuffix("index.html"))
    paths.add("/_redirect-map.json")
    (SITE / "_redirect-map.json").write_text(json.dumps(sorted(paths), indent=2) + "\n")

    build_id = stamp_build_id()
    print(f"build id {build_id}. Stamped into every page and data/build-id.txt")

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
    '<a href="/vs/">comparison pages</a>. Products change. If something here '
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
