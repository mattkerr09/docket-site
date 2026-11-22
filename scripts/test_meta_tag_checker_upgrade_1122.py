#!/usr/bin/env python3
"""Offline checks for the 22 November title and meta tag checker upgrade.

Reads the built page, so run it after scripts/build.py (the gate does). Literal
lists only: no git calls, no commit hashes. Every recorded noindex case is run
through the Worker's own checkMeta with node, so the table cannot drift from the code.
"""
from __future__ import annotations

import html
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "articles"))
import tools_free  # noqa: E402

PAGE = ROOT / "site" / "tools" / "meta-tag-checker" / "index.html"
PAGE_JS = ROOT / "workers" / "ai-crawler-check" / "src" / "page.js"

KEPT_H2 = [
    "How long should a title be?",
    "How long should a meta description be?",
    "What the other checks mean",
    "What one page cannot tell you",
    "Related",
]
NEW_H2 = "Where noindex checkers disagree"
KEPT_HREFS = {
    "/download/",
    "/tools/website-checker/",
    "/how-to/write-title-tags-that-fit/",
    "/how-to/write-meta-descriptions/",
    "/how-to/fix-duplicate-title-tags/",
    "/tools/json-ld-checker/",
    "/tools/robots-txt-tester/",
}
NEW_HREFS = {"/how-to/check-a-page-for-noindex/"}
KEPT_FAQ = [
    "How long should a title tag be?",
    "How long should a meta description be?",
    "How do I check if a page is set to noindex?",
]
NEW_FAQ = "Does a bingbot noindex tag keep a page out of Google?"
MODIFIED = "2026-11-22"
CASE_COUNT = 12
AGREE = 7

NODE = r"""
import { readFileSync } from 'node:fs'
const { checkMeta } = await import(process.argv[2])
const cases = JSON.parse(readFileSync(process.argv[3], 'utf8'))
const out = []
for (const c of cases) {
  const data = { titles: ['A title of a sensible length for this test'],
    metas: { description: ['A meta description long enough to sit inside the range this check uses, so only the robots findings differ.'], ...c.metas },
    canonicals: [], h1s: ['A heading'], jsonld: [], url: 'https://example.test/', xRobots: c.x }
  const labels = checkMeta(data).findings.map((f) => f.label)
  out.push({ noindex: labels.some((l) => /not to index/.test(l)), indexable: labels.includes('Indexable') })
}
console.log(JSON.stringify(out))
"""


def text(fragment: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", fragment))).strip()


def worker_answers(cases) -> list:
    with tempfile.TemporaryDirectory(prefix="meta-cases-") as tmp:
        script = Path(tmp) / "run.mjs"
        data = Path(tmp) / "cases.json"
        script.write_text(NODE, encoding="utf-8")
        data.write_text(json.dumps([{"metas": c[2], "x": c[3]} for c in cases]), encoding="utf-8")
        got = subprocess.run(["node", str(script), PAGE_JS.as_uri(), str(data)],
                             capture_output=True, text=True, check=True)
    return json.loads(got.stdout)


def check_cases(cases) -> None:
    assert len(cases) == CASE_COUNT, f"case count: {len(cases)}"
    for case, got in zip(cases, worker_answers(cases)):
        assert got["noindex"] is case[7] and got["indexable"] is (not case[7]), \
            f"checkMeta no longer gives the recorded answer: {case[0]} ({got})"
    assert sum(1 for c in cases if c[7] == c[4]) == AGREE, "agreement count"


def check(raw: str) -> None:
    title = text(re.search(r"<title>(.*?)</title>", raw, re.S).group(1))
    assert "noindex" in title and len(title) <= 60, f"title: {title}"
    assert not re.search("[–—]", raw), "en or em dash in page"
    assert 'id="checker"' in raw and 'id="findings"' in raw, "the checker form is gone"

    main = raw.split('id="main"', 1)[1]
    h2s = [text(h) for h in re.findall(r"<h2[^>]*>(.*?)</h2>", main, re.S)]
    missing = [h for h in KEPT_H2 + [NEW_H2] if h not in h2s]
    assert not missing, f"heading removed: {missing}"
    assert h2s.index(NEW_H2) == h2s.index("What the other checks mean") + 1, "new section placement"

    hrefs = set(re.findall(r'href="([^"]+)"', main))
    lost = (KEPT_HREFS | NEW_HREFS) - hrefs
    assert not lost, f"href missing: {sorted(lost)}"

    section = main.split(f">{NEW_H2}</h2>", 1)[1].split("<h2", 1)[0]
    assert '<div class="wrap-tbl">' in section, "table wrapper missing"
    rows = re.findall(r"<tbody>(.*?)</tbody>", section, re.S)[0].count("<tr>")
    assert rows == CASE_COUNT, f"case rows: {rows}"
    prose = text(section)
    for phrase in ("twelve small cases", "agreed with Google on seven and differed on five",
                   "otherbot: noindex", "may skip running"):
        assert phrase in prose, f"missing from the section: {phrase}"
    assert prose.count("differs from Google") == CASE_COUNT - AGREE, "differs marks"

    blocks = [json.loads(b) for b in re.findall(r'<script type="application/ld\+json">(.*?)</script>', raw, re.S)]
    faq = next(b for b in blocks if b.get("@type") == "FAQPage")
    names = [q["name"] for q in faq["mainEntity"]]
    assert all(q in names for q in KEPT_FAQ), "original FAQ removed"
    assert NEW_FAQ in names and len(names) == len(set(names)), "new FAQ missing or duplicated"
    assert NEW_FAQ in text(raw), "new FAQ not visible"
    dated = [b for b in blocks if b.get("dateModified")]
    assert dated and all(b["dateModified"] == MODIFIED for b in dated), "dateModified"


def main() -> int:
    cases = tools_free.META_CASES
    check_cases(cases)
    raw = PAGE.read_text(encoding="utf-8")
    check(raw)
    others = [p for p in (ROOT / "site").rglob("index.html") if p != PAGE and NEW_FAQ in p.read_text(encoding="utf-8")]
    assert not others, f"new FAQ also on {others}"

    flipped = list(cases)
    flipped[7] = flipped[7][:7] + (not flipped[7][7],)
    for label, run in (
        ("recorded answer flipped", lambda: check_cases(flipped)),
        ("en dash put back", lambda: check(raw.replace("Three things cause", "Three things – cause", 1))),
        ("kept heading removed", lambda: check(raw.replace("<h2>What one page cannot tell you</h2>",
                                                           "<h3>What one page cannot tell you</h3>", 1))),
    ):
        try:
            run()
        except (AssertionError, subprocess.CalledProcessError):
            print(f"CONTROL rejected: {label}")
        else:
            raise AssertionError(f"negative control passed: {label}")
    print("META TAG CHECKER UPGRADE 1122 ok")
    return 0


if __name__ == "__main__":
    sys.exit(main())
