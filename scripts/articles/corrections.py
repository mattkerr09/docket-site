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
sys.path.insert(0, str(Path(__file__).resolve().parent))
import facts as F  # noqa: E402
from corrections_cases import CASES, GROUPS  # noqa: E402
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


def _cases() -> str:
    """The worked cases: fifteen former guides, one short section each (see corrections_cases.py)."""
    esc = html.escape
    k = len(CASES)
    toc = "\n".join(f'<li><a href="#{c["id"]}">{esc(c["title"])}</a></li>' for c in CASES)
    out = [
        f'<h2 id="worked-cases">{k} cases where a finding looked wrong</h2>',
        f"<p>The releases above say what changed. These {k} cases say what the mistake looked like to the person "
        f"reading the report, and what to check on your own. They were first published as separate guides and are "
        f"collected here. They are not release records: none carries a release number or a test list, because the "
        f"guides never claimed either. No site is named.</p>",
        f"<ul>\n{toc}\n</ul>",
    ]
    for group, cases in GROUPS:
        out.append(f"<h2>{esc(group)}</h2>")
        for c in cases:
            parts = [f'<section id="{c["id"]}">', f"<h3>{esc(c['title'])}</h3>"]
            parts += [f"<p>{esc(p)}</p>" for p in c["body"]]
            parts.append(f"<p><strong>On your own report.</strong> {esc(c['try'])}</p>")
            if c["checks"]:
                label = "Registered check" if len(c["checks"]) == 1 else "Registered checks"
                parts.append(f"<p><strong>{label}.</strong> " + ", ".join(f"<code>{esc(x)}</code>" for x in c["checks"]) + ".</p>")
            if c["see"]:
                parts.append("<p>See also: " + ", ".join(f'<a href="{esc(h)}">{esc(t)}</a>' for h, t in c["see"]) + ".</p>")
            parts.append("</section>")
            out.append("\n".join(parts))
    return "\n".join(out)


def corrections() -> Path:
    entries = load()
    n = len(entries)
    n_tests = len({t for e in entries for t in e["tests"]})
    first, last = entries[-1]["date"], entries[0]["date"]
    body_entries = "\n".join(_entry(e) for e in entries)
    k = len(CASES)
    desc = (f"The releases that fixed something Docket got wrong, newest first, with the tests that hold each fix, "
            f"and {k} worked cases of findings that looked wrong.")
    assert len(desc) <= 165, len(desc)

    body = f"""
<p class="lede">An audit tool that is wrong sends you after a problem you do not have. This page lists
{n} releases of Docket, from {human(first)} to {human(last)}, that fixed something it got wrong. Each entry
names the release and the day it was published, says what was wrong in plain words, how we found it, what changed,
and which tests now hold the fix in place. Where we could not prove something, the entry says so.</p>

<p>This is the part of our log that has shipped as a release. It is not a list of every mistake, only of the ones we
found and fixed. For the questions to ask of any tool's report, ours included, see
<a href="/learn/audit-tool-accuracy/">how to tell whether an audit tool is lying to you</a>; it counts
{F.regression_files()} of Docket's {F.test_files()} test files that record a past mistake in their own words.
After the releases, {k} <a href="#worked-cases">worked cases</a> show what such mistakes look like from the reader's
side.</p>

<h2>How to check an entry</h2>
<p>The release link under each heading goes to the public release on GitHub, which shows the day it was published.
The test files are the {n_tests} files in Docket's own suite that pin these fixes; their names are given so you can
see what each one is about. Speed-ups and new features are not listed, except where the slow path was leaving
results out.</p>

{body_entries}

{_cases()}

<h2>If a finding on your site looks wrong</h2>
<p>Send us the address of the page and the text of the finding through <a href="/contact/">the contact page</a>. We
read the finding against the page itself. If Docket was wrong, the fix gets a test like the ones above.</p>

{buy_block("corrections-page", try_app="corrections-page-try-free", phone=False)}
"""
    return render(
        cat="learn", slug=SLUG,
        modified="2026-10-19",
        title="What Docket got wrong, and the release that fixed it",
        desc=desc,
        h1="What Docket got wrong, and when it was fixed",
        crumb='<a href="/">Docket</a> / <a href="/learn/">Learn</a> / What Docket got wrong',
        body=body,
        faq=[
            ("Has Docket ever reported something that was not true?",
             f"Yes. This page lists {n} releases that fixed findings or behaviour that were wrong, each with the "
             f"day it was published and the tests that hold the fix."),
            ("Why would an audit report a problem my site does not have?",
             f"Usually because a check inferred something from text, a count, a tag or a name, and the inference "
             f"failed on a site shaped differently from the ones it was written for. The {k} worked cases on this "
             f"page are {k} such failures in Docket's own checks, each with what to check on your own report."),
            ("A finding's count and its headline disagree. Which is right?",
             "Usually the headline, because a person wrote it and the badge came from a variable. Compare the count "
             "with the list of URLs under the finding before acting on it. One worked case here shows a count of the "
             "wrong thing lifting a minor finding above a more serious one."),
            ("What should I do if a Docket finding looks wrong on my site?",
             "Send the address of the page and the finding to us through the contact page. We read the finding "
             "against the page, and if Docket was wrong the fix gets a test."),
        ],
    )


def build_all() -> list:
    return [corrections()]
