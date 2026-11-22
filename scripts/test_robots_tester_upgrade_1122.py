#!/usr/bin/env python3
"""Offline checks for the 22 November robots.txt tester upgrade.

Reads the built page, so run it after scripts/build.py (the gate does). Literal
lists only: no git calls, no commit hashes. Every recorded case is run through
the Worker's own reader with node, so the table cannot drift from the code.
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

PAGE = ROOT / "site" / "tools" / "robots-txt-tester" / "index.html"
WORKER = ROOT / "workers" / "ai-crawler-check" / "src" / "index.js"

KEPT_H2 = [
    "How to read your robots.txt checker result",
    "Where did Google's robots.txt tester go?",
    "What robots.txt does not do",
    "Checking every page",
    "Related",
]
NEW_H2 = "Where robots.txt testers disagree"
KEPT_HREFS = {
    "/download/",
    "/tools/website-checker/",
    "/learn/seo-audit/",
    "/best/free-seo-audit-tools/",
    "/tools/ai-crawler-checker/",
    "/learn/ai-crawler-directives/",
    "/learn/does-noindex-stop-ai-crawlers/",
    "/vs/ahrefs-site-audit-alternative/",
}
NEW_HREFS = {"/learn/what-is-robots-txt/", "/learn/crawler-directives/"}
KEPT_FAQ = [
    "Is this robots.txt checker free?",
    "Where is the robots.txt tester in Google Search Console?",
    "How do I test my robots.txt?",
    "Does Disallow in robots.txt remove a page from Google?",
    "Why is a page blocked when my * rules allow it?",
]
NEW_FAQ = "Why do two robots.txt testers give different answers?"
MODIFIED = "2026-11-22"
CASE_COUNT = 11
OLDER_WRONG = 6
NEWER_WRONG = 2

NODE = r"""
import { readFileSync } from 'node:fs'
const mod = await import(process.argv[2])
const cases = JSON.parse(readFileSync(process.argv[3], 'utf8'))
const out = []
for (const c of cases) {
  const fake = async () => typeof c.file === 'number'
    ? new Response('', { status: c.file })
    : new Response(c.file, { status: 200, headers: { 'Content-Type': 'text/plain' } })
  const q = `url=${encodeURIComponent('https://example.com' + c.path)}&agents=${c.agent}&path=${encodeURIComponent(c.path)}`
  const j = await (await mod.handle(new Request('https://x.invalid/check?' + q), fake, {}, null)).json()
  out.push({ allowed: (j.results || [])[0]?.allowed, state: j.state })
}
console.log(JSON.stringify(out))
"""


def text(fragment: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", fragment))).strip()


def worker_answers(cases) -> list:
    with tempfile.TemporaryDirectory(prefix="robots-cases-") as tmp:
        script = Path(tmp) / "run.mjs"
        data = Path(tmp) / "cases.json"
        script.write_text(NODE, encoding="utf-8")
        data.write_text(json.dumps([{"file": c[1], "agent": c[2], "path": c[3]} for c in cases]), encoding="utf-8")
        got = subprocess.run(["node", str(script), WORKER.as_uri(), str(data)],
                             capture_output=True, text=True, check=True)
    return json.loads(got.stdout)


def check_cases(cases) -> None:
    assert len(cases) == CASE_COUNT, f"case count: {len(cases)}"
    for case, got in zip(cases, worker_answers(cases)):
        assert got["allowed"] is case[4], f"Worker no longer gives the required answer: {case[0]} ({got})"
    assert sum(1 for c in cases if c[5] != c[4]) == OLDER_WRONG, "older Python count"
    assert sum(1 for c in cases if c[6] != c[4]) == NEWER_WRONG, "newer Python count"


def check(raw: str) -> None:
    title = text(re.search(r"<title>(.*?)</title>", raw, re.S).group(1))
    assert title.startswith("Robots txt tester") and len(title) <= 60, f"title: {title}"
    assert "robots.txt checker" in title, "title lost the checker phrase"
    assert not re.search("[–—]", raw), "en or em dash in page"
    assert 'id="checker"' in raw and 'id="robots-table"' in raw, "the tester form or table is gone"

    main = raw.split('id="main"', 1)[1]
    h2s = [text(h) for h in re.findall(r"<h2[^>]*>(.*?)</h2>", main, re.S)]
    missing = [h for h in KEPT_H2 + [NEW_H2] if h not in h2s]
    assert not missing, f"heading removed: {missing}"
    assert h2s.index(NEW_H2) == h2s.index("How to read your robots.txt checker result") + 1, "new section placement"

    hrefs = set(re.findall(r'href="([^"]+)"', main))
    lost = (KEPT_HREFS | NEW_HREFS) - hrefs
    assert not lost, f"href missing: {sorted(lost)}"

    section = main.split(f">{NEW_H2}</h2>", 1)[1].split("<h2", 1)[0]
    assert '<div class="wrap-tbl">' in section, "table wrapper missing"
    rows = re.findall(r"<tbody>(.*?)</tbody>", section, re.S)[0].count("<tr>")
    assert rows == CASE_COUNT, f"case rows: {rows}"
    prose = text(section)
    for phrase in ("ten of the eleven", "six of the eleven", "fixed four of those", "urllib.robotparser"):
        assert phrase in prose, f"missing from the section: {phrase}"

    blocks = [json.loads(b) for b in re.findall(r'<script type="application/ld\+json">(.*?)</script>', raw, re.S)]
    faq = next(b for b in blocks if b.get("@type") == "FAQPage")
    names = [q["name"] for q in faq["mainEntity"]]
    assert all(q in names for q in KEPT_FAQ), "original FAQ removed"
    assert NEW_FAQ in names and len(names) == len(set(names)), "new FAQ missing or duplicated"
    assert NEW_FAQ in text(raw), "new FAQ not visible"
    dated = [b for b in blocks if b.get("dateModified")]
    assert dated and all(b["dateModified"] == MODIFIED for b in dated), "dateModified"


def main() -> int:
    cases = tools_free.ROBOTS_CASES
    check_cases(cases)
    raw = PAGE.read_text(encoding="utf-8")
    check(raw)
    others = [p for p in (ROOT / "site").rglob("index.html") if p != PAGE and NEW_FAQ in p.read_text(encoding="utf-8")]
    assert not others, f"new FAQ also on {others}"

    flipped = list(cases)
    flipped[0] = flipped[0][:4] + (not flipped[0][4],) + flipped[0][5:]
    for label, run in (
        ("required answer flipped", lambda: check_cases(flipped)),
        ("en dash put back", lambda: check(raw.replace("it says it cannot know", "it says – it cannot know", 1))),
        ("kept heading removed", lambda: check(raw.replace("<h2>What robots.txt does not do</h2>",
                                                           "<h3>What robots.txt does not do</h3>", 1))),
    ):
        try:
            run()
        except (AssertionError, subprocess.CalledProcessError):
            print(f"CONTROL rejected: {label}")
        else:
            raise AssertionError(f"negative control passed: {label}")
    print("ROBOTS TESTER UPGRADE 1122 ok")
    return 0


if __name__ == "__main__":
    sys.exit(main())
