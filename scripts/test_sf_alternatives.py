#!/usr/bin/env python3
"""Offline checks for the alternatives page's data, dates and tool counts."""
from __future__ import annotations

import copy
import html
import json
from pathlib import Path
import re
import sys
import tempfile
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / "articles"))
import comparisons  # noqa: E402
import render  # noqa: E402
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
        for tool in data["tools"]:
            expected = ("2026-11-09" if tool["slug"] in {"crawly", "houtini-seo-audit-console"}
                        else "2026-11-05")
            self.assertEqual(tool.get("read", data["read"]), expected)
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
        self.assertLess(positions[-1], table.index('<th scope="row">Docket SEO</th>'))
        self.assertEqual(table.count('<th scope="row">'), len(sf_alternatives._TOOLS) + 1)
        for tool in comparisons._SFA["tools"]:
            row = table.split(f'<th scope="row">{html.escape(tool["name"])}</th>', 1)[1].split("</tr>", 1)[0]
            for field in ("runs_on", "sold", "free", "urls"):
                self.assertIn(f'<td>{html.escape(tool[field])}</td>', row)
        lede = page["body"].split('<p class="lede">', 1)[1].split("</p>", 1)[0]
        for tool in comparisons._SFA["tools"][-2:]:
            self.assertIn(html.escape(tool["name"]), lede)
            section = page["body"].split(f'<h3>{html.escape(tool["name"])}</h3>', 1)[1].split("</p>", 1)[0]
            for field in ("sold", "runs_on", "features", "wins"):
                self.assertIn(html.escape(tool[field]), section)
            self.assertIn(tool["name"], page["faq"][0][1])
            self.assertIn(tool["runs_on"], page["faq"][2][1])
        self.assertNotIn("Read 9 November 2026 from each vendor", page["body"])
        self.assertIn("Each tool's read date is shown with its source", page["body"])

    def test_current_counts_and_short_answers(self):
        page = self.page()
        self.assertIn("Eight Screaming Frog alternatives", page["desc"])
        self.assertIn("are eight others worth a look", page["body"])
        self.assertIn("Nine tools side by side", page["body"])
        picks = page["body"].split("<ul>", 1)[1].split("</ul>", 1)[0]
        self.assertIn("Crawly on a Mac", picks)
        claude = next(item for item in picks.split("</li>") if "You work in Claude" in item)
        self.assertIn("Search Console data joined to the crawl", claude)
        tool = sf_alternatives._TOOLS["houtini-seo-audit-console"]
        self.assertIn(tool["name"], claude)
        self.assertIn(html.escape(tool["runs_on"]), claude)
        for text in (page["body"], page["desc"], *(answer for question, answer in page["faq"])):
            self.assertNotRegex(text, "[\u2013\u2014]")

    def test_structured_data_matches_visible_answers_and_count(self):
        page = self.page()
        with tempfile.TemporaryDirectory() as directory:
            with patch.object(render, "SITE", Path(directory)):
                output = sf_alternatives.sf_alternatives().read_text(encoding="utf-8")
        schemas = [json.loads(block) for block in
                   re.findall(r'<script type="application/ld\+json">(.*?)</script>', output, re.S)]
        faq = next(block for block in schemas if block.get("@type") == "FAQPage")
        self.assertEqual([(item["name"], item["acceptedAnswer"]["text"]) for item in faq["mainEntity"]],
                         page["faq"])
        article = next(block for block in schemas if "headline" in block)
        self.assertEqual(article["description"], page["desc"])
        for tool in comparisons._SFA["tools"][-2:]:
            self.assertIn(tool["name"], faq["mainEntity"][0]["acceptedAnswer"]["text"])

    def test_counts_and_names_follow_added_data(self):
        tools = dict(sf_alternatives._TOOLS)
        extra = dict(tools["crawly"], slug="test-tool", name="Test tool")
        tools[extra["slug"]] = extra
        with patch.object(sf_alternatives, "_TOOLS", tools):
            page = self.page()
        self.assertIn("Test tool", page["body"])
        self.assertIn("Nine Screaming Frog alternatives", page["desc"])
        self.assertIn("10 tools side by side", page["body"])


if __name__ == "__main__":
    unittest.main()
