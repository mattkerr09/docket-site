#!/usr/bin/env python3
"""Offline checks for the switched-off Public Site Check page. No whole-site build."""
from __future__ import annotations

from brand import NAME, BASE

import ast
from contextlib import ExitStack
from html import escape
from html.parser import HTMLParser
from pathlib import Path
import re
import sys
import tempfile
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / "articles"))
import build  # noqa: E402
import public_site_check as psc  # noqa: E402
import render as renderer  # noqa: E402
from articles import title_ii  # noqa: E402


class Markup(HTMLParser):
    def __init__(self, html: str):
        super().__init__()
        self.tags = []
        self.words = []
        self.hidden = 0
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        self.tags.append((tag, dict(attrs)))
        if tag in ("script", "style"):
            self.hidden += 1

    def handle_endtag(self, tag):
        if tag in ("script", "style"):
            self.hidden -= 1

    def handle_data(self, data):
        if not self.hidden:
            self.words.append(data)

    @property
    def text(self):
        return " ".join(" ".join(self.words).split())


def check_content(html: str) -> None:
    markup = Markup(html)
    text = markup.text
    first = re.search(r'<p class="lede">(.*?)</p>', html, re.S)
    assert first, "the answer must open the page"
    answer = Markup(first[1]).text
    assert len(answer.split()) < 60, answer
    for phrase in ("Public Site Check", "$149", "add-on", "desktop app", "Mac", "64-bit Windows",
                   "public body", "WCAG 2.1 Level A and AA", "Title II date", "board report", "PDF"):
        assert phrase in answer, phrase
    assert f"It works without a {NAME} licence." in text
    assert "By Matt Kerr" in text and "Published" in text
    assert "Checked 8 November 2026." in text

    expected = [
        ("1.1.1", "Non-text Content", "A"),
        ("1.3.1", "Info and Relationships", "A"),
        ("1.4.1", "Use of Color", "A"),
        ("1.4.2", "Audio Control", "A"),
        ("1.4.3", "Contrast (Minimum)", "AA"),
        ("1.4.10", "Reflow", "AA"),
        ("2.4.1", "Bypass Blocks", "A"),
        ("2.4.2", "Page Titled", "A"),
        ("2.4.4", "Link Purpose (In Context)", "A"),
        ("2.4.6", "Headings and Labels", "AA"),
        ("2.4.7", "Focus Visible", "AA"),
        ("3.1.1", "Language of Page", "A"),
        ("3.3.2", "Labels or Instructions", "A"),
        ("4.1.1", "Parsing", "A"),
        ("4.1.2", "Name, Role, Value", "A"),
    ]
    rows = [Markup(row).text for row in re.findall(r"<tr>(.*?)</tr>", html, re.S)]
    assert rows[1:] == [" ".join(row) for row in expected], rows
    assert ("We ran it on our own site first: 26 issues on the first 25 pages it checked, all fixed; "
            "the re-check found none on 39 pages.") in html
    limits = ("Automated checks find some accessibility problems, not all. "
              "This is not legal advice and does not say whether a site meets the law.")
    assert limits in text
    assert html.index(limits) < html.index('<div class="buy-block">'), "show limits before the purchase"
    assert "Public Site Check never recommends an overlay." in text
    for phrase in ("renders a sample of pages", "other checks read the HTML", "tags, language, title",
                   "scanned images", "Word and PowerPoint files are flagged for review",
                   "posted before your date: likely exempt, unless people use it to apply for or take part in something",
                   "posted after your date", "date unknown", "Dates are clues, not proof.",
                   "Which Title II date applies and why", "counts by criterion", "worst pages first, with the fix",
                   "documents table", "limits and the line saying it is not legal advice",
                   "$149 once per licence", "Unlimited sites on that computer", "Updates included", "30-day refund"):
        assert phrase in text, phrase
    for fact in (title_ii.LARGE, title_ii.SMALL, title_ii.POP):
        assert fact in text, fact
    links = [attrs.get("href", "") for tag, attrs in markup.tags if tag == "a"]
    assert "/tools/title-ii-date/" in links
    assert "/learn/ada-title-ii-website-dates/" in links
    assert not any("/thank-you/" in url or "/learn/what-scout-checks/" in url for url in links)
    assert not any("/buy/docket" in url or url == "/download/#buy" for url in links)
    for forbidden in ("compliant", "guaranteed", "compliance guaranteed", "ada certified", "100%",
                      "fully accessible", "avoid lawsuits", "launch offer", "on sale", "not yet on sale"):
        assert forbidden not in text.lower(), forbidden
    # Shared CSS and script comments contain dashes and percentages; check the words readers see.
    assert "\u2014" not in text and "\u2013" not in text and "%" not in text
    assert not any(tag in ("del", "s", "strike") for tag, attrs in markup.tags)
    assert not any("data-founding" in attrs for tag, attrs in markup.tags)


def check_build(enabled: bool, buy_url: str) -> None:
    with tempfile.TemporaryDirectory() as tmp, ExitStack() as stack:
        root = Path(tmp)
        site = root / "site"
        site.mkdir()
        stack.enter_context(patch.object(renderer, "SITE", site))
        stack.enter_context(patch.object(build, "SITE", site))
        stack.enter_context(patch.object(build, "LASTMOD", root / "lastmod.json"))
        stack.enter_context(patch.dict(renderer._PAGE_SOURCE, {}, clear=True))
        stack.enter_context(patch.object(psc, "PUBLIC_SITE_CHECK_PAGE", enabled))
        stack.enter_context(patch.object(psc, "PSC_BUY_URL", buy_url))
        # A pre-existing page represents the rest of the build. The hook must not change it.
        existing = renderer.render(
            cat="", slug="", title="Existing page", desc="Existing page", h1="Existing page",
            crumb="Docket", body='<p><a href="/tools/title-ii-date/">Find your date</a></p>',
            published="2026-11-08", schema_type="WebPage",
        )
        existing_html = existing.read_text()
        before = {p.relative_to(site): p.read_bytes() for p in site.rglob("*") if p.is_file()}
        with patch.object(psc, "render", wraps=psc.render) as render_call:
            # Call only the actual generator used by build.py, never build.main().
            added = build.public_site_check.build_all()
        assert existing.read_text() == existing_html
        assert "/public-site-check/" not in existing_html
        if not enabled:
            assert added == []
            assert render_call.call_count == 0
            after = {p.relative_to(site): p.read_bytes() for p in site.rglob("*") if p.is_file()}
            assert before == after, "the disabled hook must write nothing"
        else:
            assert added == [site / "public-site-check" / "index.html"]
            assert render_call.call_count == 1
            html = added[0].read_text()
            check_content(html)
            markup = Markup(html)
            buttons = [attrs for tag, attrs in markup.tags
                       if tag == "button" or (tag == "a" and
                          ("btn" in attrs.get("class", "").split() or attrs.get("data-ev") == "Buy"))]
            assert len(buttons) == (1 if buy_url else 0), buttons
            if buy_url:
                assert buttons[0]["href"] == buy_url
                assert buttons[0]["data-ev"] == "Buy"
                assert buttons[0]["data-ev-button"] == "public-site-check"
                assert escape(buy_url, quote=True) in html
            scripts = {attrs["src"] for tag, attrs in markup.tags if tag == "script" and "src" in attrs}
            shared_scripts = {attrs["src"] for tag, attrs in Markup(existing_html).tags
                              if tag == "script" and "src" in attrs}
            assert scripts <= shared_scripts, "no new third-party script"
        build.write_sitemap([existing] + added)
        sitemap = (site / "sitemap.xml").read_text()
        assert sitemap.count(f"<loc>{BASE}/public-site-check/</loc>") == int(enabled)
        assert (site / "public-site-check").exists() == enabled
        if not enabled:
            for page in site.rglob("*.html"):
                assert "/public-site-check/" not in page.read_text()


def main() -> int:
    tree = ast.parse((HERE / "build.py").read_text())
    main_fn = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "main")
    assert any(isinstance(node, ast.AugAssign) and ast.unparse(node) == "pages += public_site_check.build_all()"
               for node in main_fn.body), "wire the guarded generator into the sitemap's page list"
    for enabled in (False, True):
        for buy_url in ("", f"{BASE}/test-checkout?src=public-site-check&test=1"):
            check_build(enabled, buy_url)
    print("PUBLIC SITE CHECK ok: off writes nothing; on renders the page and sitemap; checkout is guarded")
    return 0


if __name__ == "__main__":
    sys.exit(main())
