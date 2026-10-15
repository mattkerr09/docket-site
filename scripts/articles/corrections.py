#!/usr/bin/env python3
"""/learn/what-docket-got-wrong/: the releases that fixed something Docket got wrong, with the day each shipped.

Growth action 3 of ~/ops/research/growth-docket-2026-10-14.md. /learn/audit-tool-accuracy/ teaches the families of
mistake; this page is the dated record behind it, one entry per release, so a reader can check a claim of the form
"this was fixed in 1.3.107 on 13 October" against the release itself.

Every entry is a row of data/corrections.json, written from docs/IMPROVEMENT_LOG.md in the app repo. The deploy
gate scripts/verify_corrections.py checks each row against GitHub (the release exists and was published on that
day), against the app repo (a commit for that release exists, and each named test file is tracked there and was
added no later than that release), and against the page (every row is on it). No count is typed here: the number of
releases, the span and the number of test files are computed from the rows.
"""
from __future__ import annotations

import datetime as dt
import html
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import facts as F  # noqa: E402
from render import buy_block, render  # noqa: E402

DATA = Path(__file__).resolve().parent.parent.parent / "data" / "corrections.json"
#: Where each release lives. The tag page names the day it was published.
RELEASE_URL = "https://github.com/mattkerr09/docket-site/releases/tag/v{}"
SLUG = "what-docket-got-wrong"


def load() -> list:
    return json.loads(DATA.read_text(encoding="utf-8"))["entries"]


def human(iso: str) -> str:
    d = dt.date.fromisoformat(iso)
    return f"{d.day} {d.strftime('%B %Y')}"


def anchor(release: str) -> str:
    return "v" + release.replace(".", "-")


def _entry(e: dict) -> str:
    esc = html.escape
    parts = [
        f'<section id="{anchor(e["release"])}">',
        f"<h2>{esc(e['title'])}</h2>",
        f'<p><strong>Release {esc(e["release"])}</strong>, published {human(e["date"])}. '
        f'<a href="{RELEASE_URL.format(esc(e["release"]))}" rel="noopener">The release on GitHub</a>.</p>',
        f"<p><strong>What was wrong.</strong> {esc(e['wrong'])}</p>",
        f"<p><strong>How we found it.</strong> {esc(e['found'])}</p>",
        f"<p><strong>What changed.</strong> {esc(e['fixed'])}</p>",
    ]
    if e.get("result"):
        parts.append(f"<p><strong>Result.</strong> {esc(e['result'])}</p>")
    if e.get("unproven"):
        parts.append(f"<p><strong>Not proven.</strong> {esc(e['unproven'])}</p>")
    if e.get("see"):
        parts.append("<p>" + " ".join(f'<a href="{esc(s["href"])}">{esc(s["text"])}</a>.' for s in e["see"]) + "</p>")
    parts.append("<p><strong>Tests that hold it.</strong> " + ", ".join(f"<code>{esc(t)}</code>" for t in e["tests"]) + "</p>")
    parts.append("</section>")
    return "\n".join(parts)


def corrections() -> Path:
    entries = load()
    n = len(entries)
    n_tests = len({t for e in entries for t in e["tests"]})
    first, last = entries[-1]["date"], entries[0]["date"]
    body_entries = "\n".join(_entry(e) for e in entries)
    desc = (f"The releases that fixed something Docket got wrong, newest first: what was wrong, how we found it, "
            f"what changed, and the tests that hold it.")
    assert len(desc) <= 165, len(desc)

    body = f"""
<p class="lede">An audit tool that is wrong sends you after a problem you do not have. This page lists
{n} releases of Docket, from {human(first)} to {human(last)}, that fixed something it got wrong. Each entry
names the release and the day it was published, says what was wrong in plain words, how we found it, what changed,
and which tests now hold the fix in place. Where we could not prove something, the entry says so.</p>

<p>This is the part of our log that has shipped as a release. It is not a list of every mistake, only of the ones we
found and fixed. For the questions to ask of any tool's report, ours included, see
<a href="/learn/audit-tool-accuracy/">how to tell whether an audit tool is lying to you</a>; it counts
{F.regression_files()} of Docket's {F.test_files()} test files that record a past mistake in their own words.</p>

<h2>How to check an entry</h2>
<p>The release link under each heading goes to the public release on GitHub, which shows the day it was published.
The test files are the {n_tests} files in Docket's own suite that pin these fixes; their names are given so you can
see what each one is about. Speed-ups and new features are not listed, except where the slow path was leaving
results out.</p>

{body_entries}

<h2>If a finding on your site looks wrong</h2>
<p>Send us the address of the page and the text of the finding through <a href="/contact/">the contact page</a>. We
read the finding against the page itself. If Docket was wrong, the fix gets a test like the ones above.</p>

{buy_block("corrections-page", try_app="corrections-page-try-free", phone=False)}
"""
    return render(
        cat="learn", slug=SLUG,
        title="What Docket got wrong, and the release that fixed it",
        desc=desc,
        h1="What Docket got wrong, and when it was fixed",
        crumb='<a href="/">Docket</a> / <a href="/learn/">Learn</a> / What Docket got wrong',
        body=body,
        faq=[
            ("Has Docket ever reported something that was not true?",
             f"Yes. This page lists {n} releases that fixed findings or behaviour that were wrong, each with the "
             f"day it was published and the tests that hold the fix."),
            ("What should I do if a Docket finding looks wrong on my site?",
             "Send the address of the page and the finding to us through the contact page. We read the finding "
             "against the page, and if Docket was wrong the fix gets a test."),
        ],
    )


def build_all() -> list:
    return [corrections()]
