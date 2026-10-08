#!/usr/bin/env python3
"""No visible em-dash on any page. Matthew, 2026-10-05: "make sure all work on
everything looks like a real person wrote/made it and not ai slop"; the content
standard (~/ops/launch/CONTENT-STANDARD.md rule 11) names em-dash chains.

WHAT COUNTS AS VISIBLE: text a reader sees in the body, the <title>, and the
description a search result or a shared link shows (meta description,
og:description, og:title, twitter:description). Read with html.parser, a real
tokenizer, so a comment is a comment however it is written: Crisp's regex
stripper was fooled by a ">" inside an HTML comment and counted the comment's
tail as page text. <script>, <style> and <template> are not text.

WHAT IS LEFT ALONE: <pre> and <code> (output and markup quoted exactly), and the
phrases in ALLOWED, each a quotation that must stay word for word.

    python3 scripts/verify_no_em_dash.py            # gate: exit 1 on any visible em-dash
    python3 scripts/verify_no_em_dash.py --list     # every one, with its context
"""
from __future__ import annotations

import sys
from html.parser import HTMLParser
from pathlib import Path

SITE = Path(__file__).resolve().parent.parent / "site"
DASH = "—"

#: Quotations that keep their dash, because changing them would misquote.
ALLOWED = {
    "Technical SEO audit — coming soon":
        "CrawlRaven's own pricing-page label, quoted on /vs/crawlraven-alternative/.",
    "Emergency plumber, Leeds — Smith & Co":
        "an example title on /how-to/write-title-tags-that-fit/ showing a brand separator.",
    "Smith & Co —":
        "the second half of the same example, which wraps a line in the source.",
    "Plumber — Plumbers in Leeds — Leeds Plumber":
        "a quoted example of a keyword-stuffed title on /how-to/write-title-tags-that-fit/.",
}

SKIP_TEXT = {"script", "style", "template", "noscript", "svg"}
LITERAL = {"pre", "code"}
DESC_META = {"description", "og:description", "og:title", "twitter:description", "twitter:title"}


class _Reader(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.stack: list[str] = []
        self.chunks: list[tuple[str, str]] = []   # (where, text)

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "meta":
            key = (a.get("name") or a.get("property") or "").lower()
            if key in DESC_META and a.get("content"):
                self.chunks.append((f"meta {key}", a["content"]))
            return
        if tag in ("br", "img", "input", "link", "hr", "wbr", "source", "area", "base", "col", "embed", "param", "track"):
            return
        self.stack.append(tag)

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if self.stack and self.stack[-1] == tag:
            self.stack.pop()

    def handle_endtag(self, tag):
        if tag in self.stack:
            while self.stack and self.stack.pop() != tag:
                pass

    def handle_data(self, data):
        if not data.strip():
            return
        tags = set(self.stack)
        if tags & SKIP_TEXT or tags & LITERAL:
            return
        if "head" in tags and "title" not in tags:
            return
        self.chunks.append(("title" if "title" in tags else "body", data))

    # Comments, doctypes and processing instructions are not text.
    def handle_comment(self, data):
        return

    def handle_decl(self, decl):
        return

    def handle_pi(self, data):
        return


def visible_dashes(html: str) -> list[tuple[str, str]]:
    r = _Reader()
    r.feed(html)
    r.close()
    text_by_where: dict[str, str] = {}
    for where, t in r.chunks:
        text_by_where[where] = text_by_where.get(where, "") + " " + t
    hits = []
    for where, text in text_by_where.items():
        text = " ".join(text.split())
        for phrase in ALLOWED:
            text = text.replace(phrase, phrase.replace(DASH, " "))
        i = text.find(DASH)
        while i != -1:
            hits.append((where, text[max(0, i - 60): i + 40]))
            i = text.find(DASH, i + 1)
    return hits


def scan() -> dict[str, list[tuple[str, str]]]:
    out = {}
    for f in sorted(SITE.rglob("*.html")):
        hits = visible_dashes(f.read_text(errors="replace"))
        if hits:
            out["/" + str(f.relative_to(SITE)).replace("index.html", "")] = hits
    return out


def _self_check() -> bool:
    """The trap Crisp hit, and the cases the gate must see."""
    trap = '<html><head><title>A title</title></head><body><!-- a > b — note --><p>Clean.</p></body></html>'
    seen = '<html><head><title>X — Y</title><meta name="description" content="a — b"></head><body><p>one — two</p><pre>a — b</pre></body></html>'
    hits = visible_dashes(seen)
    return not visible_dashes(trap) and sorted(w for w, _ in hits) == ["body", "meta description", "title"]


def main() -> int:
    if not _self_check():
        print("EM-DASH FAIL: the gate's self-check failed; it cannot be trusted to count")
        return 1
    found = scan()
    total = sum(len(v) for v in found.values())
    if "--list" in sys.argv:
        for page, hits in found.items():
            for where, ctx in hits:
                print(f"{page}\t{where}\t{ctx}")
    if total:
        worst = sorted(found.items(), key=lambda kv: -len(kv[1]))[:5]
        print(f"EM-DASH FAIL: {total} visible em-dash(es) on {len(found)} page(s). Worst: "
              + ", ".join(f"{p} {len(h)}" for p, h in worst))
        print("  Rewrite each as a colon, full stop or comma (CONTENT-STANDARD.md rule 11).")
        print("  python3 scripts/verify_no_em_dash.py --list   shows every one.")
        return 1
    print(f"EM-DASH ok: no visible em-dash on {len(list(SITE.rglob('*.html')))} page(s); comments, scripts, "
          "<pre> and <code> skipped; self-check passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
