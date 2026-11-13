#!/usr/bin/env python3
"""Offline checks for measured-site anonymity and the shared launch offer.

Build first. Published per-site downloads are deliberately outside this test:
the CEO's decision here covers page copy, metadata, JSON-LD and llms.txt.
"""
from __future__ import annotations

import html
from pathlib import Path
import re
import sys
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import render  # noqa: E402
from verify_structured_data_matches_page import blocks, visible  # noqa: E402


# Hosts removed from measured results, including dynamically rendered sample
# lists. Operator names, vendor documentation and placeholder subdomains remain
# allowed. Match complete hosts so en.wikipedia.org examples still work.
STRIPPED_HOSTS = frozenset("""
academia.edu airtable.com amazon.com amplitude.com apnews.com asana.com
bbc.co.uk calendly.com canva.com cnn.com dell.com edx.org f95zone.to figma.com
forbes.com foreignpolicy.com forth.gr ft.com hostedemail.com hubspot.com intercom.com
launchpad.net linear.app madewell.com mailchimp.com monday.com nature.com
notion.so office.com pinterest.com reuters.com seekingalpha.com sentry.io
shopify.com slack.com squarespace.com st-andrews.ac.uk stripe.com sudoku.com
theatlantic.com theguardian.com tiktok.com upstart.com utwente.nl vercel.com
washingtonpost.com webflow.com wikipedia.org wix.com wsj.com zendesk.com zoom.us
""".split())
HOST = re.compile(r"(?<![\w.-])(?:" + "|".join(re.escape(h) for h in sorted(STRIPPED_HOSTS))
                  + r")(?![\w-]|\.[a-z0-9])", re.I)
STAFF = re.compile(r"\b(?:our\s+(?:(?:support|engineering|development|research)\s+)?"
                   r"(?:team|staff|engineers|developers|analysts|researchers|experts)"
                   r"|the team at Docket|we are a team)\b", re.I)


def published_copy(raw: str) -> str:
    """Include metadata and JSON-LD, excluding scripts and documentation URLs."""
    metadata = re.findall(r'<meta\b[^>]*\bcontent=(["\'])(.*?)\1[^>]*>', raw, re.I)
    return " ".join([visible(raw), *(html.unescape(s) for _, s in metadata),
                     *(str(block) for block in blocks(raw))])


class SitewideCopyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pages = sorted(render.SITE.rglob("*.html"))
        if not cls.pages:
            raise AssertionError("build the site before running these checks")

    def test_built_pages_do_not_name_the_stripped_hosts(self):
        for path in self.pages:
            with self.subTest(page=str(path.relative_to(render.SITE))):
                self.assertIsNone(HOST.search(published_copy(path.read_text())))
        self.assertIsNone(HOST.search((render.SITE / "llms.txt").read_text()))

    def test_host_check_catches_prose_metadata_and_schema(self):
        for host in STRIPPED_HOSTS:
            for raw in (f"<p>{host.upper()}</p>",
                        f"<p>We measured {host}.</p>",
                        f'<meta name="description" content="Measured {host}">',
                        '<script type="application/ld+json">'
                        f'{{"description": "Measured {host}"}}</script>'):
                with self.subTest(host=host, raw=raw):
                    self.assertIsNotNone(HOST.search(published_copy(raw)))
        for raw in ('<code>https://en.wikipedia.org/wiki/Your_Company</code>',
                    '<a href="https://vercel.com/blog/crawler-study">Vercel study</a>',
                    '<p>chatgpt.com, bigsur.ai, mistral.ai, example.com</p>'):
            self.assertIsNone(HOST.search(published_copy(raw)))

    def test_built_pages_and_llms_do_not_claim_staff(self):
        for path in self.pages:
            with self.subTest(page=str(path.relative_to(render.SITE))):
                self.assertIsNone(STAFF.search(published_copy(path.read_text())))
        self.assertIsNone(STAFF.search((render.SITE / "llms.txt").read_text()))

    def test_offer_sentence_uses_constants_and_closes_with_the_offer(self):
        with patch.multiple(render, FOUNDING_OPEN=True, SALE_NAME="Black Friday sale",
                            FOUNDING_NOW="$12.34", FOUNDING_END_DAY_US="a last day",
                            SALE_PERCENT_OFF=23, NOVEMBER_PRICE_STR="$16",
                            FOUNDING_AFTER_DAY="a next day", LATER_STR="$56", PRICE_STR="$78"):
            self.assertEqual(render.founding_price_sentence(),
                             "Black Friday sale: $12.34 once, 23% off our November price of $16, through a last day. Then $56.")
        with patch.object(render, "FOUNDING_OPEN", False):
            self.assertEqual(render.founding_price_sentence(), "")
            self.assertNotIn(render.SALE_NAME, render.buy_strip("test"))
            self.assertNotIn("data-founding-until", render.buy_strip("test"))

    def test_guide_strip_and_faqs_use_the_exact_offer(self):
        if not render.FOUNDING_OPEN:
            self.skipTest("the launch offer is closed")
        line = render.founding_price_sentence().lower()
        strips = 0
        for path in self.pages:
            raw = path.read_text()
            for strip in re.findall(r'<aside class="buy-strip">.*?</aside>', raw, re.S):
                strips += 1
                self.assertIn(line, visible(strip), str(path))
                self.assertIn(render.FOUNDING_UNTIL, strip, str(path))
                self.assertIn(render.CHECKOUT_HELP, strip, str(path))
                self.assertNotIn(render.FOUNDING_CODE, strip, str(path))
            self.assertNotRegex(visible(raw), r"at the launch price until|launch price \$")
        self.assertGreater(strips, 0)
        for rel in ("index.html", "for/agencies/index.html", "for/saas/index.html"):
            raw = (render.SITE / rel).read_text()
            answers = [q["acceptedAnswer"]["text"] for block in blocks(raw)
                       if block.get("@type") == "FAQPage" for q in block["mainEntity"]]
            self.assertTrue(any(line in answer.lower() for answer in answers), rel)


if __name__ == "__main__":
    unittest.main()
