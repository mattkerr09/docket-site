#!/usr/bin/env python3
"""Offline gates for check evidence, ownership and the actual rendered articles."""
from __future__ import annotations

import ast
import hashlib
import json
import re
import sys
import tempfile
import unittest
from html import unescape
from pathlib import Path
from unittest.mock import patch
from urllib.parse import urlsplit

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE), str(HERE.parent)]
import check_pages as checks
import facts as F
import render


def numbers(value) -> set[str]:
    if isinstance(value, dict):
        return set().union(*(numbers(v) for v in value.values()))
    if isinstance(value, list):
        return set().union(*(numbers(v) for v in value))
    if isinstance(value, bool) or value is None:
        return set()
    return {n.replace(",", "") for n in checks.NUMBER.findall(str(value))}


def evidence_numbers(row: dict) -> set[str]:
    """Do not accept the explanatory prose itself as proof of its numbers.

    Line positions are not numerical evidence either. Only code expressions,
    literal values and the independently read field totals can supply numbers.
    """
    evidence = row["evidence"]
    values = []
    for key in ("predicates", "conditions", "constants", "local_constants", "numeric_parameters", "patterns", "findings"):
        values.extend({k: v for k, v in item.items() if k != "source"}
                      for item in evidence[key])
    return numbers(values) | numbers({k: row["field_audits"][k] for k in ("found", "sites")})


def prose_paragraphs(raw: str) -> list[str]:
    raw = re.sub(r'<div class="callout compact" id="try">.*?<h2>', '<h2>', raw, flags=re.S)
    raw = re.sub(r'<(head|nav|header|footer|script|style|aside)\b[^>]*>.*?</\1>', ' ', raw, flags=re.S)
    return [checks.visible(p) for p in re.findall(r'<p\b[^>]*>.*?</p>', raw, re.S)
            if not re.search(r'class="(?:byline|crumb)', p)]


def sentence_starts(raw: str) -> list[str]:
    starts = []
    for paragraph in prose_paragraphs(raw):
        for sentence in re.split(r'[.!?][”"’]*\s+', paragraph):
            word = re.search(r"[\w]+(?:['’][\w]+)?", sentence)
            if word:
                starts.append(word[0].casefold())
    return starts


def six_word_sequences(text: str) -> set[tuple[str, ...]]:
    words = re.findall(r"[a-z0-9']+", text.casefold())
    return {tuple(words[i:i + 6]) for i in range(len(words) - 5)}


def numbers_without_units(text: str) -> list[str]:
    """Check every prose number, including counts, ratios and HTTP codes.

    A unit can follow the value or a measurement label can introduce it in
    the same sentence. Do not let a unit elsewhere on the page qualify it.
    """
    unit = (r"(?:pages?|words?|characters?|letters?|digits?|bytes?|seconds?|pixels?|"
            r"clicks?|hops?|entries|entry|occurrences?|appearances?|terms?|families|"
            r"sentences?|matches|fields?|articles?|targets?|sections?|levels?|"
            r"queries|gaps|suggestions?|regions?|links?|numbers?|variants?|tools?|"
            r"labels?|images?|resources?|ampersands?|hosts?|units?|share|days?|"
            r"samples?|headings?|times)\b")
    modifiers = (r"(?:indexable|successful|readable|usable|meaningful|shared|target|"
                 r"distinct|phrase|inward|recognised|profile|HTML|text|half-width|"
                 r"character|RGB|distance|opacity|nested|child|top|titled|local|"
                 r"outgoing|incoming|observed|internal|external|total|different|"
                 r"phone|address|counted|empty|remaining|detected|blocking|positive|"
                 r"response-time|identical|language|optional|region|modern|wide|"
                 r"qualifying|font|shallow|hreflang|domain|missing|alternate|"
                 r"successfully|crawled|sampled|varying|JPEG|redirected|such|"
                 r"accepted|question)")
    after = re.compile(r"^(?:-|\s+)(?:or more\s+)?(?:" + modifiers + r"\s+){0,4}" + unit, re.I)
    ratio = re.compile(r"\b(?:share|coverage|overlap|ratio)\b[^.!?]*$", re.I)
    status = re.compile(r"\bHTTP(?: status(?:es)?)?\s*(?:from\s*|at or above\s*)?$", re.I)
    missing = []
    for sentence in re.split(r"(?<=[.!?])\s+", text):
        for match in checks.NUMBER.finditer(sentence):
            before, remaining = sentence[:match.start()], sentence[match.end():]
            # "Soft 404" names an error class, not a measured threshold.
            if match[0] == "404" and re.search(r"\bsoft[- ]$", before, re.I):
                continue
            if not (after.search(remaining) or ratio.search(before) or status.search(before)):
                missing.append(sentence)
    return missing


class CheckPageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = F.check_pages()
        cls.rows = {r["slug"]: r for r in cls.data["rows"]}
        cls.temp = tempfile.TemporaryDirectory(prefix="check-pages-test-")
        cls.site = Path(cls.temp.name)
        with patch.object(render, "SITE", cls.site):
            paths = checks.build_all()
        cls.raw = {p.parent.name: p.read_text() for p in paths[1:]}
        cls.index = paths[0].read_text()
        cls.existing = checks.existing_pages(checks.ROOT / "site")

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def test_catalogue_and_source_are_complete_and_deterministic(self):
        self.assertEqual(len(self.data["rows"]), len(checks.catalogue()))
        self.assertEqual({r["id"] for r in self.rows.values()}, set(checks.registry()))
        self.assertEqual(checks.encoded(checks.derive_data()), checks.OUTPUT.read_text())
        for row in self.rows.values():
            for name in ("condition", "pages", "reports", "fix"):
                self.assertEqual(row[name]["source"], row["source"])
            self.assertTrue(row["severity"])
            self.assertTrue(row["evidence"]["conditions"])
            for source in row["evidence"]["sources"]:
                lines = checks.source_file(source["file"]).splitlines(keepends=True)
                segment = "".join(lines[source["line"] - 1:source["end_line"]]).rstrip("\n")
                # AST segments can start after indentation on nested objects.
                self.assertEqual(hashlib.sha256(segment.encode()).hexdigest(), source["sha256"])

    def test_visible_length_and_numbers(self):
        for slug, raw in self.raw.items():
            with self.subTest(slug=slug):
                prose = checks.visible(raw)
                self.assertGreaterEqual(len(prose.split()), 300)
                self.assertFalse(numbers(prose) - evidence_numbers(self.rows[slug]),
                                 numbers(prose) - evidence_numbers(self.rows[slug]))
                full_page = checks.visible(raw, include_chrome=True)
                allowed = evidence_numbers(self.rows[slug]) | set(self.rows[slug]["presentation"]["numbers"])
                self.assertFalse(numbers(full_page) - allowed, numbers(full_page) - allowed)

    def test_every_render_call_has_literal_publication_date(self):
        tree = ast.parse(Path(checks.__file__).read_text())
        calls = [n for n in ast.walk(tree) if isinstance(n, ast.Call)
                 and isinstance(n.func, ast.Name) and n.func.id == "render"]
        self.assertEqual(len(calls), 3)
        for call in calls:
            value = next((k.value for k in call.keywords if k.arg == "published"), None)
            self.assertIsInstance(value, ast.Constant)
            self.assertEqual(value.value, "2026-11-11")
        self.assertIn('datetime="2026-11-11"', self.index)
        for raw in self.raw.values():
            blocks = [json.loads(s) for s in re.findall(
                r'<script type="application/ld\+json">(.*?)</script>', raw, re.S)]
            article = next(b for b in blocks if b.get("@type") == "Article")
            self.assertEqual(article["datePublished"], "2026-11-11")

    def test_faq_and_next_step_and_metadata(self):
        for slug, raw in self.raw.items():
            with self.subTest(slug=slug):
                blocks = [json.loads(s) for s in re.findall(
                    r'<script type="application/ld\+json">(.*?)</script>', raw, re.S)]
                faq = next(block for block in blocks if block.get("@type") == "FAQPage")
                self.assertEqual(len(faq["mainEntity"]), 3)
                for question in faq["mainEntity"]:
                    self.assertIn(question["name"], checks.visible(raw))
                    self.assertIn(question["acceptedAnswer"]["text"], checks.visible(raw))
                    self.assertTrue(question["acceptedAnswer"]["text"].strip())
                    body = raw.split('<section class="faq">', 1)[0]
                    repeated = six_word_sequences(checks.visible(body)) & six_word_sequences(
                        question["acceptedAnswer"]["text"])
                    self.assertFalse(repeated, (slug, repeated))
                self.assertEqual(raw.count('id="try"'), 1)
                self.assertLess(raw.index('<section class="faq">'), raw.index('id="try"'))
                self.assertLess(raw.index('<h2>Method note</h2>'), raw.index('id="try"'))
                self.assertLess(len(re.search(r'<title>(.*?)</title>', raw, re.S)[1]), 60)
                self.assertLessEqual(len(self.rows[slug]["answer"]), 165)
        self.assertEqual(self.index.count('id="try"'), 1)
        self.assertLess(self.index.rindex('</ul>'), self.index.index('id="try"'))

    def test_faq_questions_are_unique_and_answers_have_row_facts(self):
        seen = {}
        for slug, row in self.rows.items():
            with self.subTest(slug=slug):
                self.assertEqual(len(row["faq"]), 3)
                expected = []
                for entry in row["faq"]:
                    question = " ".join(entry["question"].casefold().split())
                    self.assertTrue(question.endswith("?"))
                    self.assertNotIn(question, seen, (slug, seen.get(question), question))
                    seen[question] = slug
                    fact = entry["fact"]
                    self.assertIn(fact["field"], ("condition", "pages", "reports"))
                    self.assertEqual(fact["source"], row[fact["field"]]["source"])
                    self.assertIn(fact["text"].casefold(), row[fact["field"]]["text"].casefold())
                    self.assertIn(fact["text"].casefold(), entry["answer"].casefold())
                    self.assertTrue(fact["text"].strip())
                    expected.append((entry["question"], entry["answer"]))
                self.assertEqual(checks.faq(row), expected)
                if row["publish"]:
                    blocks = [json.loads(s) for s in re.findall(
                        r'<script type="application/ld\+json">(.*?)</script>', self.raw[slug], re.S)]
                    schema = next(b for b in blocks if b.get("@type") == "FAQPage")
                    self.assertEqual([(q["name"], q["acceptedAnswer"]["text"])
                                      for q in schema["mainEntity"]], expected)
        self.assertEqual(len(seen), 3 * len(self.rows))

    def test_every_prose_threshold_has_a_unit(self):
        for slug, row in self.rows.items():
            prose = [row[k] for k in ("question", "answer", "why")]
            prose += [row[k]["text"] for k in ("condition", "pages", "reports", "fix")]
            prose += [entry[k] for entry in row["faq"] for k in ("question", "answer")]
            for text in prose:
                with self.subTest(slug=slug, text=text):
                    self.assertFalse(numbers_without_units(text), numbers_without_units(text))

    def test_unit_guard_rejects_bare_thresholds(self):
        for text in ("Display width below 25 is short and above 65 is long.",
                     "A median above 0.8 and at most 1.8 seconds is medium.",
                     "A spread below 7.0 stops the check.",
                     "There must be more than 3.", "Pages above 150000 qualify."):
            self.assertTrue(numbers_without_units(text), text)
        for text in ("Display width below 25 half-width character units is short.",
                     "A median above 0.8 seconds and at most 1.8 seconds is medium.",
                     "A spread below 7.0 words per sentence stops the check.",
                     "More than 3 entries qualify.", "Coverage below 0.3 qualifies."):
            self.assertFalse(numbers_without_units(text), text)

    def test_ownership_and_all_site_similarity(self):
        existing = {url: checks.shingles(checks.visible(raw)) for url, raw in self.existing.items()}
        pages = dict(existing)
        pages["/checks/"] = checks.shingles(checks.visible(self.index))
        # Include every other built page on the site, not just ownership candidates.
        for path in (checks.ROOT / "site").rglob("*.html"):
            url = "/" + path.relative_to(checks.ROOT / "site").as_posix()
            if not url.startswith("/checks/"):
                pages[url] = checks.shingles(checks.visible(path.read_text()))
        for row in self.rows.values():
            owner, score = checks.owner_for(checks.draft(row), existing)
            self.assertEqual(owner, row["owner"])
            self.assertEqual(round(score, 8), row["ownership_jaccard"])
            self.assertEqual(row["publish"], owner is None)
            if not row["publish"]:
                self.assertIn(f'href="{owner}"', self.index)
                self.assertNotIn(row["slug"], self.raw)
        for slug, raw in self.raw.items():
            mine = checks.shingles(checks.visible(raw))
            for url, other in pages.items():
                self.assertLess(checks.jaccard(mine, other), 0.5, (slug, url))
            pages[f"/checks/{slug}/"] = mine

    def test_owner_boundary_and_stable_ties(self):
        # Six words have two five-word shingles. The five-word candidate
        # shares exactly one, making Jaccard exactly the inclusive cutoff.
        raw = "alpha bravo charlie delta echo foxtrot"
        candidate = checks.shingles("alpha bravo charlie delta echo")
        self.assertEqual(checks.owner_for(raw, {"/b/": candidate, "/a/": candidate}), ("/a/", 0.5))
        self.assertEqual(checks.owner_for(raw, {"/c/": checks.shingles("no shared words here at all")})[0], None)

    def test_no_jargon_dashes_identifiers_or_repeated_starts(self):
        for slug, raw in {**self.raw, "": self.index}.items():
            with self.subTest(slug=slug):
                prose = checks.visible(raw)
                self.assertNotRegex(prose, r"[\u2013\u2014]")
                article = re.sub(r'<h2>Method note</h2>\s*<p>.*?</p>', ' ', raw, flags=re.S)
                authored = checks.visible(article)
                self.assertNotRegex(authored, r"(?i)\b(?:branches|branch|helpers?|supply the condition|"
                                    r"the condition|parsed|evidence|content-bearing|lanes?|revisions?|"
                                    r"ctx|check_id|AST|Jaccard|backend|function)\b")
                self.assertNotRegex(authored, r"\b(?:ai|brand|content|cvr|index|intl|links|local|mar|onpage|perf|schema|security|social)\.[a-z_]+\b")
                if slug:
                    self.assertLessEqual(authored.casefold().count(self.rows[slug]["title"].casefold()), 6)
                starts = sentence_starts(raw)
                self.assertFalse([(a, b) for a, b in zip(starts, starts[1:]) if a == b])

    def test_guides_and_anonymous_area_counts(self):
        audits = json.loads((checks.ROOT / "data/field-audits.json").read_text())
        for row in self.rows.values():
            if row["guide"]:
                self.assertTrue(row["guide"].startswith(("/how-to/", "/learn/")))
                guide = self.existing[row["guide"]]
                title = checks.visible(re.search(r'<h1\b[^>]*>(.*?)</h1>', guide, re.S)[1])
                self.assertEqual(row["guide_title"], title)
                link = re.search(r'<a href="' + re.escape(row["guide"]) + r'">(.*?)</a>',
                                 checks.body(row), re.S)
                self.assertIsNotNone(link)
                self.assertEqual(checks.visible(link[1]), title)
            else:
                self.assertEqual(row["guide_title"], "")
                self.assertNotIn('href=""', checks.body(row))
            self.assertEqual(row["field_audits"]["found"], sum(
                a.get("by_area", {}).get(row["lane_label"], 0) > 0 for a in audits["audits"]))
            self.assertEqual(row["field_audits"]["sites"], audits["sites"])
            self.assertIn("These are area totals", checks.visible(checks.body(row)))
            for href in re.findall(r'href="([^"]+)"', checks.body(row)):
                self.assertTrue(href.startswith("/"), href)

    def test_no_page_links_to_itself(self):
        for slug, raw in self.raw.items():
            url = f"/checks/{slug}"
            for href in re.findall(r'<a\b[^>]*href="([^"]+)"', raw):
                self.assertNotEqual(urlsplit(unescape(href)).path.rstrip("/"), url, (slug, href))

    def test_missing_guide_is_omitted(self):
        with patch.object(checks, "existing_pages", return_value={
                "/learn/other/": "<h1>Another subject</h1><p>A different guide.</p>"}):
            rows = checks.derive_data()["rows"]
        for row in rows:
            self.assertEqual(row["guide"], "")
            self.assertEqual(row["guide_title"], "")
            self.assertNotIn('href=""', checks.body(row))

    def test_collector_never_imports_or_runs_engine(self):
        # The only subprocess operations are read-only git show and ls-tree.
        source = Path(checks.__file__).read_text()
        tree = ast.parse(source)
        imports = [n.module for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)]
        self.assertFalse(any((name or "").startswith("seo_engine") for name in imports))
        with self.assertRaises(ValueError):
            checks.copy_rows("unexpected\nshort")

    def test_numeric_arithmetic_preserves_units_and_operators(self):
        path = checks.CHECKS + "indexability.py"
        value = checks.numeric_value(ast.parse("2 * 1024 * 1024", mode="eval").body, path)
        self.assertEqual(value, 2097152)
        self.assertIsNone(checks.numeric_value(ast.parse("int('123')", mode="eval").body, path))
        row = next(r for r in self.rows.values() if r["id"] == "index.byte_cap")
        budget = next(c for c in row["evidence"]["local_constants"] if c["name"] == "budget")
        self.assertEqual(budget["value"], 2096128)
        self.assertTrue(any(t["expression"] == "p.html_bytes > budget"
                            and t["values"].get("budget") == budget["value"]
                            for t in row["evidence"]["thresholds"]))
        language = next(r for r in self.rows.values() if r["id"] == "content.lang_mismatch")
        self.assertTrue(any(t["values"].get("langid.MIN_WORDS") == 40
                            for t in language["evidence"]["thresholds"]))

    def test_title_timing_and_rendering_facts(self):
        title = self.rows["onpage-title"]
        limits = {c["name"]: c["value"] for c in title["evidence"]["constants"]}
        self.assertIn(f'below {limits["TITLE_MIN"]} half-width character units is short',
                      title["condition"]["text"])
        self.assertIn(f'above {limits["TITLE_MAX"]} half-width character units is long',
                      title["condition"]["text"])
        width = next(s for s in title["evidence"]["sources"] if s["function"] == "display_width")
        code = checks.source_file(width["file"]).splitlines()[width["line"] - 1:width["end_line"]]
        self.assertIn('total += 2 if unicodedata.east_asian_width(ch) in ("W", "F") else 1',
                      "\n".join(code))
        self.assertIn("wide and fullwidth Unicode characters twice", title["condition"]["text"])
        timing = self.rows["perf-ttfb"]
        limits = {c["name"]: c["value"] for c in timing["evidence"]["constants"]}
        self.assertIn(f'above {limits["TTFB_GOOD"]} seconds and at most {limits["TTFB_POOR"]} seconds',
                      timing["condition"]["text"])
        rendering = self.rows["ai-rendering"]
        self.assertEqual({s["expression"] for s in rendering["severity"]}, {"Severity.HIGH"})
        self.assertIn("high severity", rendering["reports"]["text"])

    def test_shared_numbers_do_not_depend_on_offer_expiration(self):
        expected = checks.presentation_numbers()
        with patch.object(render, "FOUNDING_LINE", ""), patch.object(render, "FOUNDING_OPEN", False):
            self.assertEqual(checks.presentation_numbers(), expected)


if __name__ == "__main__":
    unittest.main(verbosity=2)
