#!/usr/bin/env python3
"""A report walkthrough backed by the captured, capped audit."""
from __future__ import annotations

import json
import sys
from html import escape
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from render import render  # noqa: E402

EVIDENCE = Path(__file__).resolve().parents[2] / "data/real-questions-2026-11-11"
# Check Engine origin/main a2e3c3d: backend/seo_engine/provenance.py:198-200
# says "PageSpeed Insights did not run"; backend/seo_engine/__init__.py sets
# __version__ = "1.3.163". Check Engine release published 2026-11-11T19:46:22Z.
# The sentence names the release by its date, not its number: a version string outside a recorded run summary fails
# the version-string gate at the next release.
PAGESPEED_UPDATE = ("From the Check Engine release of 11 November 2026, a report marks this area "
                    "'Not measured: PageSpeed Insights did not run' instead of scoring it.")


def source(name: str) -> dict:
    return json.loads((EVIDENCE / name).read_text())


def quote(text: str, name: str) -> str:
    return f'<q data-source="{escape(name)}">{escape(text)}</q>'


def fact(label: str, value, name: str, pointer: str) -> str:
    return (f'<span data-source="{escape(name)}" data-pointer="{escape(pointer)}">'
            f'{escape(label)}: {escape(str(value))}</span>')


def note(key: str) -> str:
    return (f'<p class="note" data-source="read-times.json" data-pointer="/notes/{key}">'
            f'{escape(source("read-times.json")["notes"][key])}</p>')


def build() -> Path:
    audit = source("audit.json")
    md = (EVIDENCE / "audit.md").read_text()
    areas = []
    for line in md.splitlines():
        cells = [c.strip() for c in line.strip("|").split("|")]
        if line.startswith("| ") and len(cells) == 3 and cells[0] != "Area":
            areas.append('<tr>' + ''.join(f'<td>{escape(c)}</td>' for c in cells) + '</tr>')
    plan = ''.join(
        f'<tr><td>{item["rank"]}</td><td style="width:5rem;min-width:5rem;padding:0.6rem 1rem">{escape(item["phase"])}</td>'
        f'<td>{quote(item["title"], "audit.json")}</td></tr>' for item in audit["plan"])
    findings = []
    for key in ("brand.colour_drift", "ai.weak_sameas", "cvr.message_mismatch"):
        item = next(p for p in audit["plan"] if p["check_id"] == key)
        findings.append(
            f'<section data-finding="{key}"><h3>{quote(item["title"], "audit.json")}</h3>'
            f'<p><strong>Report detail:</strong> {quote(item["detail"], "audit.json")}</p>'
            f'<p><strong>Report fix:</strong> {quote(item["fix"], "audit.json")}</p>'
            f'<p><strong>Affected:</strong> {escape(", ".join(item["urls"]) or "Site stylesheet")}</p></section>')
    limits = []
    for item in audit["plan"]:
        if item["tool_limit"]:
            limits.append(f'<li>{quote(item["title"], "audit.json")}</li>')
    body = f"""
<p class="lede">An SEO audit report should tell you what to fix, where the evidence is, and how much of your site it actually checked. Here is a real report from our own site, with its good score and its limits left in view.</p>
<p>Read the score beside the crawl coverage before you start work. Then follow the action plan to the pages and styles that need attention.</p>

<h2>The report we are reading</h2>
<p data-source="audit.json" data-pointer="/version" data-run-summary="true">Check Engine {escape(audit['version'])} audited checkengineseo.com on {escape(source('read-times.json')['notes']['report_capture'])}, capped at {audit['stats']['pages_crawled']} pages.</p>

<h2>What the score means here</h2>
<p>The report shows {quote('Score: 99/100', 'audit.md')}, with grade A.
Its warning is just as much a part of the result as the grade:</p>
<blockquote><p>{quote(audit['score']['verdict'], 'audit.json')}</p></blockquote>
<p>The report's crawl finding gives the size of that gap: {quote('This audit found 436 URLs on this site and reached 60 of them.', 'audit.json')}
The score describes the pages reached. Finish the crawl before judging the whole site.</p>

<h2>The scores by area</h2>
<p>This table shows which parts of the audit raised problems. Local business SEO is marked not applicable.</p>
<div class="wrap-tbl"><table data-table="areas"><caption>Report scores by area</caption>
<thead><tr><th>Area</th><th>Score</th><th>Issues</th></tr></thead><tbody>{''.join(areas)}</tbody></table></div>

<h2>The action plan starts with Build, then Polish</h2>
<p>The action plan places the colour work under Build. The rest sits under Polish, in the order shown below. This is the report's order, including notices that ask for a check rather than a repair. Read each explanation before treating the list as a set of changes to make.</p>
<div class="wrap-tbl"><table data-table="plan"><caption>The action plan</caption>
<thead><tr><th>Order</th><th style="width:5rem;min-width:5rem;padding:0.6rem 1rem">Stage</th><th>Finding, in the report's words</th></tr></thead><tbody>{plan}</tbody></table></div>

<h2>Read the finding, not only its heading</h2>
<p>These findings include the report's full detail and fix text. The colour finding is useful because it asks you to check intent. Similar colours can be deliberate. The headline finding gives the actual search title and page headline, so you can decide whether a visitor would find the change of wording confusing.</p>
{''.join(findings)}
<p>The report recommends adding an official profile, with no guarantee of a search position. The title example also needs a person's judgement. Shared words can help make a promise clear, but the wording still has to describe what the page offers.</p>

<h2>What this audit could not measure</h2>
<p>The report separates these limits from work that could recover score points. Its explanation is:
{quote(audit['projection']['excluded_note'], 'audit.json')}</p>
<ul>{''.join(limits)}</ul>
<p>The orphan check needs the pages that might contain incoming links. With much of the crawl missing, it cannot say a page has no links to it. The outbound-link notice says some requests were refused. Those links were not proved broken, and they were not counted as working.</p>
<p>The AI control notice asks the owner to check the account setting inside Search Console.</p>
<p>PageSpeed Insights did not run because its quota was exceeded. The speed area's clean score therefore includes no PageSpeed measurement.</p>
<p>{PAGESPEED_UPDATE}</p>

<h2>What to ask of any good audit report</h2>
<p>Ask for ranked fixes because you need a place to start when the list is long. Ask for evidence per finding because someone must be able to find the page, inspect the problem and check the repair. Ask what could not be checked because a blank result can otherwise look like a clean bill of health.</p>
<p>Save the report before you edit the site. After the repairs, compare the affected pages and the crawl coverage. A changed score is easier to trust when you can trace it to work you did. If you need the meaning of the audit itself, read <a href="/learn/seo-audit/">what an SEO audit is</a>.</p>

<h2>Source note</h2>
<p>We read the report and full audit results. Quotes, area scores, the action plan and finding details come from that run.</p>
"""
    return render(
        cat="learn", slug="seo-audit-report",
        title="SEO audit report: a real example, with its limits",
        desc="Read a real SEO audit report from our own site. See the score, area results, ranked fixes and the checks a capped crawl could not finish.",
        h1="SEO audit report: reading a real result",
        crumb='<a href="/learn/">Learn</a> / SEO audit report',
        body=body, published="2026-11-11",
        faq=[
            ("Should I send a client only the audit score?",
             "Send the coverage note and the fixes with it. A client needs to know which part of their site the result describes before agreeing to the work."),
            ("Why keep an audit notice that has no repair?",
             "It can record a question for the owner to answer. Keep it separate from a defect so nobody bills for a change the evidence does not call for."),
            ("Can I compare this capped report with a later full crawl?",
             "Use the affected URLs to check repairs first. Then read the new coverage note before comparing grades, since the later crawl may have inspected pages missing from this report."),
        ],
    )


def build_all() -> list[Path]:
    return [build()]
