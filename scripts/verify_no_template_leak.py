#!/usr/bin/env python3
"""Refuse a build whose pages print their own template code.

2026-11-07: a sentence in privacy() was written as f-string code inside a plain string, and the built privacy page
said `{"WebKit on a Mac ..." if WINDOWS else 'the WebKit engine macOS already ships'}` in public. Every other gate
passed it, because none of them reads for Python left in the prose. This reads every built page's text (scripts,
styles and JSON-LD excluded) for the shapes generator code leaves behind: a {NAME} constant, {F.helper(...)},
{len(...)}, `if WINDOWS else`, or a format spec like {x:,}.

    python3 scripts/verify_no_template_leak.py [--self-test]
"""
import html
import re
import sys
from pathlib import Path

SITE = Path(__file__).resolve().parents[1] / "site"
LEAK = re.compile(r"\{(?:F\.[a-z_]+|len\(|[A-Z][A-Z0-9_]{2,}\}|[a-z_]+\(\)|[A-Za-z_][\w.]*:[,.0-9a-z]*\})"
                  r"|\bif WINDOWS else\b|\bif INTEL else\b|\bf\"[^\"]*\{")
STRIP = re.compile(r"<(script|style|pre|code)\b[^>]*>.*?</\1>", re.S | re.I)


def leaks(page_html: str) -> list:
    text = html.unescape(re.sub(r"<[^>]+>", " ", STRIP.sub(" ", page_html)))
    return [m.group(0) for m in LEAK.finditer(text)]


def self_test() -> None:
    bad = '<p>it renders {"WebKit on a Mac" if WINDOWS else \'x\'}, and {N_CHECKS} checks via {F.ai_agents()}</p>'
    good = '<p>JSON looks like {"a": 1}; CSS {color: red}</p><script>var x = {F.y}</script>'
    assert leaks(bad), "the planted leak was not found"
    assert not leaks(good), f"a false alarm on ordinary braces: {leaks(good)}"


def main() -> int:
    self_test()
    if "--self-test" in sys.argv:
        print("  self-test ok")
        return 0
    found = []
    for p in sorted(SITE.rglob("*.html")):
        for hit in leaks(p.read_text(encoding="utf-8", errors="replace")):
            found.append(f"{p.relative_to(SITE)}: {hit}")
    for p in [SITE / "llms.txt"]:
        if p.exists():
            found += [f"llms.txt: {m.group(0)}" for m in LEAK.finditer(p.read_text())]
    if found:
        print("TEMPLATE LEAK: generator code is printed on a page:\n  " + "\n  ".join(found[:30]))
        return 1
    print(f"TEMPLATE ok: no generator code in {len(list(SITE.rglob('*.html')))} built pages")
    return 0


if __name__ == "__main__":
    sys.exit(main())
