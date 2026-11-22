#!/usr/bin/env python3
"""The 30 October 2026 Anthropic change is stated on the three pages that talk about AI crawler rules.

Reads the built pages, so run it after scripts/build.py. Offline, no git calls.
Anthropic's help article does not name Content-Usage or train-ai=n; only the IETF aipref draft does. The pages
may say Anthropic honours "a signal that follows an IETF draft" and may show the draft's syntax as the draft's,
but must never say Anthropic confirmed that exact syntax.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PAGES = {
    "learn/ai-crawler-directives": ["30 October 2026", "no AI training", "IETF draft", "/learn/what-is-claudebot/"],
    "tools/robots-txt-tester": ["30 October 2026", "no AI training", "Content-Usage", "ignores", "/learn/what-is-claudebot/"],
    "learn/what-is-claudebot": ["2026-10-30", "no AI training", "aipref", "Content-Usage: train-ai=n", "names ClaudeBot"],
}
STALE = "It is also the only mechanism these operators document"
CONFIRMED = re.compile(r"Anthropic (confirmed|says|states)[^.<]{0,80}(Content-Usage|train-ai)", re.I)


def text(slug: str) -> str:
    raw = (ROOT / "site" / slug / "index.html").read_text()
    raw = re.sub(r"<script.*?</script>|<style.*?</style>", " ", raw, flags=re.S)
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", raw)).replace("&ldquo;", '"').replace("&rdquo;", '"').replace("&rsquo;", "'")


def stale_or_unconfirmed(body: str) -> list[str]:
    problems = []
    if STALE in body:
        problems.append("still says robots.txt is the only documented mechanism")
    if CONFIRMED.search(body):
        problems.append("says Anthropic confirmed the Content-Usage syntax, which its article does not name")
    return problems


def main() -> int:
    failures = []
    for slug, needles in PAGES.items():
        body = text(slug)
        for needle in needles:
            if needle.replace("\\", "") not in body and needle not in (ROOT / "site" / slug / "index.html").read_text():
                failures.append(f"{slug}: missing {needle!r}")
        for problem in stale_or_unconfirmed(body):
            failures.append(f"{slug}: {problem}")
    # negative controls: the checker must catch each fault
    assert stale_or_unconfirmed(f"x {STALE}. y"), "control: stale sentence not caught"
    assert stale_or_unconfirmed("Anthropic says it honours Content-Usage: train-ai=n"), "control: overclaim not caught"
    assert not stale_or_unconfirmed("the draft shows Content-Usage: train-ai=n; Anthropic says a ClaudeBot rule wins"), "control: false alarm"
    for failure in failures:
        print("FAIL", failure)
    print("ok" if not failures else f"{len(failures)} failure(s)")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
