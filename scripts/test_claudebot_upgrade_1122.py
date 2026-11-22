#!/usr/bin/env python3
"""Offline checks for the 22 November ClaudeBot upgrade.

Reads the built page, so run it after scripts/build.py (the gate does). Literal
lists only: no git calls, no commit hashes, no network. The address-check
script on the page is run against a stub list, so the code readers copy works.
"""
from __future__ import annotations

import html
import io
import json
import re
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PAGE = ROOT / "site" / "learn" / "what-is-claudebot" / "index.html"

KEPT_H2 = [
    "Anthropic runs three crawlers, not one",
    "How to block ClaudeBot, and only ClaudeBot",
    "What most sites that block Anthropic actually do",
    "robots.txt is a request, not a lock",
    "Related",
]
NEW_H2 = ["The no-AI-training signal, and which rule wins", "How to detect ClaudeBot, and spot a fake"]
OLD_H2 = "Is a request really from ClaudeBot?"
KEPT_HREFS = {
    "/tools/ai-crawler-checker/?src=learn-what-is-claudebot",
    "/index/ai-directives/",
    "/learn/ai-crawler-directives/",
    "/learn/does-noindex-stop-ai-crawlers/",
    "/how-to/fix-ai-crawlers-blocked-by-your-cdn/",
    "https://claude.com/crawling/bots.json",
}
NEW_HREFS = {"/tools/robots-txt-tester/", "https://datatracker.ietf.org/doc/draft-ietf-aipref-attach/"}
KEPT_FAQ = [
    "Does blocking ClaudeBot remove my site from Claude?",
    "Does ClaudeBot obey robots.txt?",
    "How can I tell a real ClaudeBot request from a fake one?",
]
NEW_FAQ = "Does a no-AI-training signal override my ClaudeBot rule?"
MODIFIED = "2026-11-22"
STUB = {"creationTime": "2026-10-20T00:00:00Z",
        "prefixes": [{"ipv4Prefix": "216.73.216.0/22"}, {"ipv4Prefix": "34.162.230.222/32"}]}


def text(fragment: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", fragment))).strip()


def run_page_script(code: str, ips) -> list:
    seen = {}

    def fake_urlopen(req, *args, **kwargs):
        seen["ua"] = req.get_header("User-agent")
        return io.BytesIO(json.dumps(STUB).encode())

    out = io.StringIO()
    real_open, real_argv, real_stdout = urllib.request.urlopen, sys.argv, sys.stdout
    try:
        urllib.request.urlopen, sys.argv, sys.stdout = fake_urlopen, ["check.py", *ips], out
        exec(compile(code, "check.py", "exec"), {"__name__": "__main__"})
    finally:
        urllib.request.urlopen, sys.argv, sys.stdout = real_open, real_argv, real_stdout
    assert seen.get("ua") and not seen["ua"].startswith("Python-urllib"), "script must name itself"
    return out.getvalue().split()


def check(raw: str) -> None:
    title = text(re.search(r"<title>(.*?)</title>", raw, re.S).group(1))
    assert title.startswith("What is ClaudeBot?") and len(title) <= 60, f"title: {title}"
    assert "detect" in title.lower(), "title lost the detection phrase"
    assert not re.search("[–—]", raw), "en or em dash in page"

    main = raw.split('id="main"', 1)[1]
    h2s = [text(h) for h in re.findall(r"<h2[^>]*>(.*?)</h2>", main, re.S)]
    missing = [h for h in KEPT_H2 + NEW_H2 if h not in h2s]
    assert not missing, f"heading missing: {missing}"
    assert OLD_H2 not in h2s, "old detection heading still there"
    assert h2s.index(NEW_H2[0]) == h2s.index("How to block ClaudeBot, and only ClaudeBot") + 1, "signal placement"

    lede = text(main.split("<h2", 1)[0])
    assert "2026-10-30" in lede and "list Anthropic publishes" in lede, "short answer lost a point"

    hrefs = set(re.findall(r'href="([^"]+)"', main))
    lost = (KEPT_HREFS | NEW_HREFS) - hrefs
    assert not lost, f"href missing: {sorted(lost)}"

    signal = main.split(f">{NEW_H2[0]}</h2>", 1)[1].split("<h2", 1)[0]
    assert "Content-Usage: train-ai=n" in html.unescape(signal), "signal syntax missing"
    assert re.findall(r"<tbody>(.*?)</tbody>", signal, re.S)[0].count("<tr>") == 3, "priority table rows"

    detect = main.split(f">{NEW_H2[1]}</h2>", 1)[1].split("<h2", 1)[0]
    assert re.findall(r"<tbody>(.*?)</tbody>", detect, re.S)[0].count("<tr>") == 2, "check table rows"
    for phrase in ("14 entries", "1,037 IPv4 addresses", "created 2026-10-20", "403 Forbidden"):
        assert phrase in text(detect), f"missing measured fact: {phrase}"
    code = html.unescape(re.findall(r"<pre><code>(.*?)</code></pre>", detect, re.S)[0])
    got = run_page_script(code, ["216.73.217.40", "34.162.230.222", "203.0.113.7", "2001:db8::7"])
    assert got == ["216.73.217.40", "True", "34.162.230.222", "True", "203.0.113.7", "False",
                   "2001:db8::7", "False"], f"page script answers: {got}"

    blocks = [json.loads(b) for b in re.findall(r'<script type="application/ld\+json">(.*?)</script>', raw, re.S)]
    faq = next(b for b in blocks if b.get("@type") == "FAQPage")
    names = [q["name"] for q in faq["mainEntity"]]
    assert all(q in names for q in KEPT_FAQ), "original FAQ removed"
    assert NEW_FAQ in names and len(names) == len(set(names)), "new FAQ missing or duplicated"
    assert NEW_FAQ in text(raw), "new FAQ not visible"
    dated = [b for b in blocks if b.get("dateModified")]
    assert dated and all(b["dateModified"] == MODIFIED for b in dated), "dateModified"


def main() -> int:
    raw = PAGE.read_text(encoding="utf-8")
    check(raw)
    others = [p for p in (ROOT / "site").rglob("index.html") if p != PAGE and NEW_FAQ in p.read_text(encoding="utf-8")]
    assert not others, f"new FAQ also on {others}"
    for label, broken in (
        ("en dash put back", raw.replace("spot a fake</h2>", "spot a fake – tested</h2>", 1)),
        ("script loses its name", raw.replace("log-check/1.0", "", 1).replace(
            "headers={&quot;User-Agent&quot;: &quot;&quot;}", "headers={}", 1)),
        ("kept heading removed", raw.replace("<h2>Related</h2>", "<h3>Related</h3>", 1)),
    ):
        try:
            check(broken)
        except AssertionError:
            print(f"CONTROL rejected: {label}")
        else:
            raise AssertionError(f"negative control passed: {label}")
    print("CLAUDEBOT UPGRADE 1122 ok")
    return 0


if __name__ == "__main__":
    sys.exit(main())
