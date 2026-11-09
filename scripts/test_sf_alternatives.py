#!/usr/bin/env python3
"""Offline checks for the alternatives page's data, dates and tool counts."""
from __future__ import annotations

import copy
import html
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / "articles"))
import comparisons  # noqa: E402
import sf_alternatives  # noqa: E402


class ScreamingFrogAlternativesTests(unittest.TestCase):
    def page(self):
        with patch.object(sf_alternatives, "render", side_effect=lambda **kwargs: kwargs):
            return sf_alternatives.sf_alternatives()

    def test_claim_dates_default_to_file_date(self):
        data = comparisons._SFA
        claims = comparisons._sfa_facts(data)
        for tool, (claim, source) in zip(data["tools"], claims):
            expected = comparisons._human_date(tool.get("read", data["read"]))
            self.assertIn(f"; read {expected}", claim)
            self.assertEqual(source, tool["source"])
        self.assertEqual(data["read"], "2026-11-05")
        self.assertEqual(comparisons.CHECKED_ISO["sf-alternatives"], "2026-11-09")
        note = comparisons._verified_note("sf-alternatives")
        self.assertIn("Checked 9 November 2026", note)
        self.assertNotIn("were read from its own pages on that date", note)

    def test_legacy_rows_without_read_still_build_claims(self):
        data = copy.deepcopy(comparisons._SFA)
        for tool in data["tools"]:
            tool.pop("read", None)
        claims = comparisons._sfa_facts(data)
        self.assertTrue(all("; read 5 November 2026" in claim
                            for claim, source in claims[:len(data["tools"])]))

    def test_every_rival_is_in_table_and_new_sections(self):
        page = self.page()
        table = page["body"].split('<table class="cmp">', 1)[1].split("</table>", 1)[0]
        names = [html.escape(t["name"]) for t in comparisons._SFA["tools"]]
        positions = [table.index(f'<th scope="row">{name}</th>') for name in names]
        self.assertEqual(positions, sorted(positions))
        for tool in comparisons._SFA["tools"][-2:]:
            for field in ("features", "wins"):
                self.assertIn(html.escape(tool[field]), page["body"])
            self.assertIn(tool["name"], page["faq"][0][1])
        self.assertNotIn("Read 9 November 2026 from each vendor", page["body"])

    def test_counts_and_names_follow_added_data(self):
        tools = dict(sf_alternatives._TOOLS)
        extra = dict(tools["crawly"], slug="test-tool", name="Test tool")
        tools[extra["slug"]] = extra
        with patch.object(sf_alternatives, "_TOOLS", tools):
            page = self.page()
        self.assertIn("Test tool", page["body"])
        self.assertIn("9 Screaming Frog alternatives", page["desc"])
        self.assertIn("10 tools side by side", page["body"])


if __name__ == "__main__":
    unittest.main()
