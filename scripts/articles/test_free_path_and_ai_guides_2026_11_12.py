#!/usr/bin/env python3
"""Offline checks of the free path and edited guides against the job's base."""
from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
import types
import unittest
from collections import Counter
from pathlib import Path
from unittest.mock import patch
from urllib.parse import parse_qs, urlsplit

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path[:0] = [str(HERE), str(HERE.parent)]
import guide_render
import render
from test_real_questions_2026_11_11 import Document, article, normal, text
from verify_sibling_links import offenders

BASE = '053a2d393'
PAGES = {
    'seo-audit': ('learn.py', 'seo_audit'),
    'does-cloudflare-block-gptbot': ('cloudflare_gptbot.py', 'cloudflare_gptbot'),
    'what-is-claudebot': ('ai_questions.py', 'what_is_claudebot'),
    'does-noindex-stop-ai-crawlers': ('noindex_ai_crawlers.py', 'noindex_ai_crawlers'),
}
GUIDES = tuple(slug for slug in PAGES if slug != 'seo-audit')
NUMBER = re.compile(r'(?<!\w)\d+(?:,\d{3})*(?:\.\d+)*(?!\w)')


def build(slug, *, base=False, capture=False):
    """Use both revisions' normal builders with the same local facts and renderer."""
    filename, builder = PAGES[slug]
    path = HERE / filename
    source = (subprocess.run(['git', 'show', f'{BASE}:scripts/articles/{filename}'],
                             cwd=ROOT, check=True, capture_output=True, text=True).stdout
              if base else path.read_text())
    module = types.ModuleType('_free_path_' + slug.replace('-', '_'))
    module.__file__ = str(path)
    if not capture:
        exec(compile(source, str(path), 'exec'), module.__dict__)
        return getattr(module, builder)()
    # Product offers are shared site copy, outside the guide's facts and word count.
    with patch.object(render, 'render', side_effect=lambda **kwargs: kwargs), \
            patch.object(render, 'buy_block', return_value=''), \
            patch.object(guide_render, 'render_free_guide', side_effect=lambda **kwargs: kwargs):
        exec(compile(source, str(path), 'exec'), module.__dict__)
        return getattr(module, builder)()


def links(doc):
    return list(article(doc).all('a'))


def free_links(doc):
    result = []
    for link in links(doc):
        url = urlsplit(link.attrs.get('href', ''))
        if url.path in {'/tools/ai-crawler-checker/', '/download/', '/dl/docket'}:
            result.append(link)
    return result


class FreePathAndAIGuidesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.before = {slug: build(slug, base=True, capture=True) for slug in PAGES}
        cls.after = {slug: build(slug, capture=True) for slug in PAGES}
        cls.scratch = tempfile.TemporaryDirectory(prefix='docket-free-path-test-')
        cls.addClassCleanup(cls.scratch.cleanup)
        cls.raw = {}
        # Render through the normal entry point without touching the checked-in site.
        with patch.object(render, 'SITE', Path(cls.scratch.name)):
            for slug in PAGES:
                cls.raw[slug] = build(slug).read_text()
        cls.docs = {slug: Document(raw) for slug, raw in cls.raw.items()}

    def test_seo_audit_has_two_tracked_free_blocks_at_requested_positions(self):
        doc = self.docs['seo-audit']
        nodes = list(article(doc).all())
        blocks = [node for node in nodes if node.attrs.get('class') == 'free-audit-path']
        self.assertEqual(len(blocks), 2)
        sentence = render.FREE_LINE.partition('. Pro:')[0].replace(
            'Free: ', 'The free version shows ', 1) + '.'
        for block in blocks:
            self.assertEqual(normal(text(block)), sentence + ' Run a free audit of your site .')
            anchors = list(block.all('a'))
            self.assertEqual(len(anchors), 1)
            self.assertEqual(anchors[0].attrs['href'], render.download_url('learn-seo-audit'))
            self.assertEqual(parse_qs(urlsplit(anchors[0].attrs['href']).query)['src'],
                             ['learn-seo-audit'])
        paragraphs = [node for node in nodes if node.tag == 'p'
                      and node.attrs.get('class') != 'byline']
        self.assertIs(paragraphs[1], blocks[0])
        definition = next(node for node in nodes if node.tag == 'h2'
                          and normal(text(node)) == 'What does an SEO audit include?')
        field = next(node for node in nodes if node.tag == 'h2'
                     and normal(text(node)).startswith('What audits of '))
        self.assertLess(nodes.index(definition), nodes.index(blocks[1]))
        self.assertLess(nodes.index(blocks[1]), nodes.index(field))

    def test_seo_audit_has_no_other_copy_changes(self):
        before = normal(self.before['seo-audit']['body'])
        after_body = re.sub(r'<p class="free-audit-path">.*?</p>', '',
                            self.after['seo-audit']['body'], flags=re.S)
        self.assertEqual(normal(after_body), before)
        for key in ('title', 'h1', 'desc', 'faq', 'published'):
            self.assertEqual(self.before['seo-audit'].get(key), self.after['seo-audit'].get(key))

    def test_guides_start_with_two_short_answers_and_one_tracked_next_step(self):
        for slug in GUIDES:
            with self.subTest(slug=slug):
                nodes = list(article(self.docs[slug]).all())
                paragraphs = [node for node in nodes if node.tag == 'p'
                              and node.attrs.get('class') != 'byline']
                first_h2 = next(node for node in nodes if node.tag == 'h2')
                for paragraph in paragraphs[:2]:
                    self.assertLess(nodes.index(paragraph), nodes.index(first_h2))
                    self.assertLessEqual(len(normal(text(paragraph)).split()), 45)
                    self.assertFalse(list(paragraph.all('a')))
                self.assertEqual(paragraphs[2].attrs.get('class'), 'next-step')
                self.assertLess(nodes.index(paragraphs[2]), nodes.index(first_h2))
                anchors = free_links(self.docs[slug])
                self.assertEqual(len(anchors), 1, 'Guide must have exactly one free next-step link')
                self.assertEqual(parse_qs(urlsplit(anchors[0].attrs['href']).query)['src'],
                                 ['learn-' + slug])
                self.assertIs(list(paragraphs[2].all('a'))[0], anchors[0])
                if slug == 'does-cloudflare-block-gptbot':
                    self.assertEqual(anchors[0].attrs['href'], render.download_url('learn-' + slug))
                else:
                    self.assertEqual(urlsplit(anchors[0].attrs['href']).path,
                                     '/tools/ai-crawler-checker/')
                self.assertFalse(any(link.attrs.get('data-ev') == 'Buy'
                                     for link in links(self.docs[slug])))

    def test_guides_keep_entity_schema_without_an_unshown_price(self):
        for slug in GUIDES:
            scripts = re.findall(r'<script type="application/ld\+json">(.*?)</script>',
                                 self.raw[slug], re.S)
            entities = [node for script in scripts for node in json.loads(script).get('@graph', [])]
            app = next(node for node in entities if node.get('@type') == 'SoftwareApplication')
            self.assertNotIn('offers', app)
            self.assertTrue(any(node.get('@type') == 'Organization' for node in entities))

    def test_visible_guide_numbers_and_dates_match_base_including_repetitions(self):
        for slug in GUIDES:
            with self.subTest(slug=slug):
                # Include tables, code and the visible FAQ. Exclude the shared offer and dateline.
                before = self.before[slug]['body'] + ' '.join(
                    q + ' ' + a for q, a in self.before[slug]['faq'])
                old = Counter(NUMBER.findall(normal(text(Document(before).root))))
                new = Counter(NUMBER.findall(normal(text(article(self.docs[slug])))))
                self.assertEqual(new, old)

    def test_titles_publication_dates_and_faq_are_preserved(self):
        questions = []
        for slug in GUIDES:
            for key in ('title', 'h1', 'published', 'faq'):
                with self.subTest(slug=slug, key=key):
                    self.assertEqual(self.after[slug].get(key), self.before[slug].get(key))
            questions.extend(q for q, _ in self.after[slug]['faq'])
        self.assertEqual(len(questions), len(set(questions)))

    def test_updated_datelines_show_the_edit_date(self):
        for slug in PAGES:
            self.assertEqual(self.after[slug]['modified'], '2026-11-12')
            byline = next(node for node in article(self.docs[slug]).all('p')
                          if node.attrs.get('class') == 'byline')
            self.assertEqual(list(byline.all('time'))[-1].attrs['datetime'], '2026-11-12')

    def test_sources_stay_exact_and_guide_copy_uses_plain_words(self):
        for slug in GUIDES:
            before = Document(self.before[slug]['body'])
            after = self.after[slug]['body']
            for paragraph in before.root.all('p'):
                external = [a for a in paragraph.all('a')
                            if a.attrs.get('href', '').startswith('https://')]
                if external or normal(text(paragraph)).startswith('Read on '):
                    self.assertIn(normal(text(paragraph)), normal(text(Document(after).root)))
            self.assertEqual(offenders({f'learn/{slug}/index.html': self.raw[slug]}), [])
            copy = normal(text(article(self.docs[slug])))
            self.assertNotRegex(copy, '[\u2013\u2014]')
            self.assertNotRegex(copy, r'ai\.(?:crawler_access|edge_access)')
            self.assertNotRegex(copy, r'Article Studio|Check Engine reviews|Codex|PLAYBOOK')

    def test_each_guide_is_shorter_and_report_word_counts(self):
        for slug in GUIDES:
            before = normal(text(Document(self.before[slug]['body']).root))
            after = normal(text(Document(self.after[slug]['body']).root))
            old, new = len(before.split()), len(after.split())
            print(f'{slug}: {old} -> {new} words in article body, excluding shared offers and FAQ')
            self.assertLess(new, old)


if __name__ == '__main__':
    unittest.main(verbosity=2)
