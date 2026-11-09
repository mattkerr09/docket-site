#!/usr/bin/env python3
"""Offline regressions for the Ahrefs comparison's prices, sources and limits."""
from __future__ import annotations

import csv
import html
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from articles import comparisons as C  # noqa: E402
import render  # noqa: E402


class AhrefsComparisonTests(unittest.TestCase):
    def page(self):
        with patch.object(C, "render", side_effect=lambda **kwargs: kwargs):
            return C.ahrefs()

    def test_lite_entry_price_and_matching_read_dates(self):
        page = self.page()
        with (HERE.parent / "data" / "competitors.csv").open() as fh:
            rival = next(row for row in csv.DictReader(fh) if row["slug"] == "ahrefs-site-audit")
        self.assertEqual(C._AH["site_audit_entry_plan"], "Lite")
        self.assertEqual(C._AH_LO, "129")
        self.assertEqual(rival["annual_low"], "1548")
        self.assertEqual(C._AH["read"], C.CHECKED_ISO["ahrefs"])
        self.assertEqual(rival["price_checked"], C._AH["read"])
        self.assertEqual(page["modified"], "2026-11-09")
        self.assertIn("Checked 9 November 2026", page["body"])
        self.assertIn("Starter has no Site Audit allowance", page["body"])
        self.assertNotIn("starter-plan", page["body"])
        text = page["body"] + page["desc"] + str(page["faq"])
        self.assertNotRegex(text, r"\$29(?:\s+to\s+|[–-])\$449")
        self.assertIn("$129/month", page["desc"])

    def test_plan_table_keeps_both_limits_and_computes_year_costs(self):
        rows = C._credit_rows()
        for tier in ("Lite", "Standard", "Advanced"):
            row = rows.split(f"Ahrefs {tier}</th>", 1)[1].split("</tr>", 1)[0]
            self.assertIn(C.F.credits_for(tier), row)
            self.assertIn(C.F.max_pages_for(tier), row)
            self.assertIn(f"${C._AH_PRICE[tier] * 12:,}", row)
        self.assertNotIn("month 1", rows)
        self.assertNotIn("price per 1,000", self.page()["body"])
        # The helper is still needed by the SEOptimer comparison.
        self.assertGreaterEqual(C._months_past_docket(C._SEOPT_LO), 1)

    def test_one_decision_table_and_free_version_proof(self):
        body = self.page()["body"]
        self.assertEqual(body.count("Which audit tool fits your work?"), 1)
        self.assertNotIn("<h2>At a glance</h2>", body)
        self.assertNotIn("<h2>Side by side</h2>", body)
        self.assertLess(body.index("Is Ahrefs Site Audit free?"), body.index("Crawl credits, page caps"))
        self.assertIn('/assets/free-result.webp', body)
        self.assertIn('/assets/vs-docket-run.webp', body)
        self.assertIn("If the site's ownership is verified", self.page()["faq"][1][1])

    def test_honest_docket_limits_stay_visible(self):
        body = self.page()["body"]
        for wording in ("Renders a sample of pages", "does not render every page",
                        "only while the app is open", "No team accounts or shared workspace",
                        "No login setup", "No Search Console or Analytics account connection",
                        "No backlink or keyword index. No rank tracking.",
                        "We have not benchmarked that claim", "default deadline"):
            with self.subTest(wording=wording):
                self.assertIn(wording, body)
        self.assertIn(f"{C.F.crawl_minutes()}-minute", body)
        self.assertIn(f"{C.F.everything_hours()} hours", body)
        self.assertIn("Mac and 64-bit Windows", C.CTA_LINK_EXPERIMENT)

    def test_boost_prices_and_bulk_exports_have_dated_sources(self):
        body = self.page()["body"]
        self.assertIn("Project Boost Pro costs $20 a month per project", body)
        self.assertIn("Project Boost Max costs $200 a month per project", body)
        self.assertIn("export all issues in bulk as ZIP or CSV", body)
        self.assertNotIn("one issue at a time", body)
        self.assertEqual(C._AH["overage_source"], "https://ahrefs.com/pricing")
        claims = C.VERIFIED["ahrefs"]
        for wording, source in claims:
            self.assertTrue(source.startswith("https://"), wording)
            self.assertIn(source, body)
        auto_source = next(source for wording, source in claims if "automatic charges" in wording)
        self.assertEqual(auto_source, "https://ahrefs.com/pricing")
        self.assertEqual(len(self.page()["faq"]), 8)

    def test_offer_uses_site_constants_and_changes_after_sale(self):
        page = self.page()
        offer = render.founding_price_sentence()
        self.assertIn(offer, page["body"])
        self.assertIn(offer, page["faq"][3][1])
        with patch.object(C, "founding_price_sentence", return_value=""), \
                patch.object(C, "_top_cta", return_value=""), \
                patch.object(C, "CTA_LINK_EXPERIMENT", ""):
            after = self.page()
        self.assertNotIn("Launch price", after["body"])
        self.assertNotIn("Launch price", str(after["faq"]))
        self.assertIn(f"{C.PRICE_STR} once", after["body"])
        self.assertNotRegex(html.unescape(page["body"]), r"[—–]")


if __name__ == "__main__":
    unittest.main()
