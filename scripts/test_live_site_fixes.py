#!/usr/bin/env python3
"""Offline regression checks for the pricing, download and legal entry points."""
from __future__ import annotations

import html
from pathlib import Path
import re
import sys
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import build  # noqa: E402
import render  # noqa: E402
from lint import is_redirect_stub  # noqa: E402


class LiveSiteFixTests(unittest.TestCase):
    def test_download_article_follows_the_first_spoken_sound(self):
        for size in ("8 MB", "8.5 MB", "11 MB", "18.1 MB", "80 MB", "811 MB", "8,000 MB"):
            with self.subTest(size=size):
                self.assertEqual(render.size_article(size), "an")
        for size in ("0.8 MB", "1 MB", "10 MB", "22.5 MB", "110 MB", "180 MB", "1,800 MB"):
            with self.subTest(size=size):
                self.assertEqual(render.size_article(size), "a")

    def test_receipt_holders_get_the_current_installer_for_each_platform(self):
        for windows in (True, False):
            with self.subTest(windows=windows), patch.object(render, "WINDOWS", windows), \
                    patch.object(build, "render", side_effect=lambda **kwargs: kwargs):
                page = build.pricing_page()
            note = page["body"].split("Bought it already?", 1)[1].split("</p>", 1)[0]
            self.assertIn(render.download_url("pricing-page"), note)
            self.assertIn(render.DMG_SIZE, note)
            if windows:
                self.assertIn(render.download_url("pricing-page-windows", to=render.WIN_SETUP), note)
                self.assertIn(f"{render.WIN_SETUP_SIZE} Windows installer", note)
            else:
                self.assertNotIn("Windows installer", note)

    def test_legal_aliases_are_stubs_and_not_sitemap_pages(self):
        expected = {
            "privacy": "/legal/privacy/", "terms": "/legal/terms/",
            "refund": "/legal/refunds/", "refunds": "/legal/refunds/", "legal": "/legal/privacy/",
        }
        sitemap = (render.SITE / "sitemap.xml").read_text()
        for slug, target in expected.items():
            with self.subTest(slug=slug):
                raw = (render.SITE / slug / "index.html").read_text()
                self.assertTrue(is_redirect_stub(raw))
                self.assertIn(f'<meta http-equiv="refresh" content="0; url={target}">', raw)
                self.assertIn(f'<link rel="canonical" href="{render.BASE}{target}">', raw)
                self.assertIn(f'<a href="{target}">{target}</a>', raw)
                self.assertIn(render.BING_SITE_VERIFICATION, raw)
                self.assertNotIn(f"<loc>{render.BASE}/{slug}/</loc>", sitemap)
                self.assertIn(f"<loc>{render.BASE}{target}</loc>", sitemap)
                self.assertTrue((render.SITE / target.strip("/") / "index.html").is_file())

    def test_built_comparison_tables_do_not_offer_launch_instalments(self):
        checked = 0
        for path in render.SITE.rglob("index.html"):
            for table in re.findall(r'<table\b.*?</table>', path.read_text(), re.S):
                for row in re.findall(r'<tr\b.*?</tr>', table, re.S):
                    text = html.unescape(re.sub(r"<[^>]+>", " ", row))
                    text = " ".join(text.split())
                    if f"{render.PRICE_STR} once" in text:
                        checked += 1
                        self.assertNotIn(render.BNPL_INSTALMENT, text, str(path))
                        self.assertNotIn("four payments", text, str(path))
        self.assertGreater(checked, 0, "build the site before running these checks")


if __name__ == "__main__":
    unittest.main()
