#!/usr/bin/env python3
"""Offline content, provenance and duplication checks for the host guides."""
from __future__ import annotations

import hashlib
import itertools
import json
import os
import re
import sys
import tempfile
import unittest
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path
from unittest.mock import patch
from urllib.parse import parse_qs, urlsplit

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path[:0] = [str(HERE), str(HERE.parent)]
import ai_bot_host_pages as hosts
import render
from test_real_questions_2026_11_11 import Document, article, normal, prose, shingles, text
from verify_sibling_links import SIBLINGS

BANNED = re.compile(r'\b(?:fields?|rows?|datasets?|generators?|merges?|evidence|'
                    r'Codex|Article Studio|revolutionary|seamless|unleash|supercharge|'
                    r'game-changing)\b', re.I)
DEFAULT = re.compile(r'\bdefaults?\b', re.I)
QUOTED = re.compile(r'[“"]([^”"]+)[”"]')
PRIVATE_DOCS = Path(os.environ.get(
    'DOCKET_AI_BOT_HOST_DOCS',
    '/Users/matthewkerr/ops/research/articles/data-2026-11-12/ai-bot-host-docs'))


class SourceText(HTMLParser):
    """Decode saved documents, excluding scripts and styles from quotations."""
    def __init__(self, raw):
        super().__init__(convert_charrefs=True)
        self.parts = []
        self.skip = 0
        self.feed(raw)

    def handle_starttag(self, tag, attrs):
        if tag in {'script', 'style'}:
            self.skip += 1
        if not self.skip and tag in {'p', 'div', 'li', 'th', 'td', 'h1', 'h2', 'h3',
                                      'article', 'nav', 'header', 'br', 'pre'}:
            self.parts.append(' ')

    def handle_endtag(self, tag):
        if tag in {'script', 'style'}:
            self.skip -= 1
        if not self.skip and tag in {'p', 'div', 'li', 'th', 'td', 'h1', 'h2', 'h3',
                                      'article', 'nav', 'header', 'br', 'pre'}:
            self.parts.append(' ')

    def handle_data(self, value):
        if not self.skip:
            self.parts.append(value)


def source_text(raw):
    return normal(''.join(SourceText(raw).parts))


def page_items(page):
    return (page['intro'] + list(page.get('bots', {}).values())
            + ([page['bot_note']] if 'bot_note' in page else [])
            + [item for section in page['sections'] for item in section['paragraphs']]
            + page['faq'])


def sentence_count(excerpt):
    # A fragment or a bot list counts as one sentence. Dots inside filenames,
    # hostnames and user-agent versions are not sentence boundaries.
    endings = re.findall(r'''[.!?](?:[”"']|\))?(?=\s|$)''', excerpt)
    tail = re.split(r'''[.!?](?:[”"']|\))?(?:\s+|$)''', excerpt)[-1]
    return max(1, len(endings) + bool(tail.strip()))


def check_fact_excerpts(data, private_docs):
    """Validate short public quotes and, when available, private raw captures."""
    sources = data['sources']
    documents = {}
    for key, source in sources.items():
        assert re.fullmatch(r'[0-9a-f]{64}', source['sha256']), 'Missing or invalid SHA-256'
        assert source['url'].startswith('https://'), 'Missing source URL'
        assert source['read_at'] and source['label'], 'Missing source attribution'
        assert Path(source['file']).name == source['file'], 'Invalid capture filename'
        assert source['facts'], 'Source has no fact excerpts'
        original = None
        if private_docs.exists():
            raw = (private_docs / source['file']).read_bytes()
            assert hashlib.sha256(raw).hexdigest() == source['sha256'], 'Raw capture hash differs'
            original = source_text(raw.decode('utf-8'))
        excerpts = []
        for fact in source['facts'].values():
            assert fact['statement'].strip(), 'Missing fact statement'
            assert fact['url'] == source['url'], 'Fact URL differs from source'
            excerpt = fact['excerpt']
            assert excerpt.strip(), 'Missing fact excerpt'
            assert sentence_count(excerpt) <= 2, 'Fact excerpt exceeds two sentences'
            if original is not None:
                assert normal(excerpt) in original, 'Fact excerpt absent from raw capture'
            excerpts.append(normal(excerpt))
        # Run the same rendered-quotation checks in both modes using only the
        # retained excerpts, so clean clones also require quotation support.
        documents[source['file']] = ' '.join(excerpts)
    for page in data['pages']:
        for item in page_items(page):
            assert set(item['facts']) == set(item['sources']), 'Fact sources differ from citations'
            for key, names in item['facts'].items():
                assert names, 'Cited item has no fact excerpts'
                assert len(names) == len(set(names)), 'Repeated fact reference'
                assert all(name in sources[key]['facts'] for name in names), 'Unknown fact reference'
    return documents


def cited_sources(node, sources, reads):
    found = []
    by_file = {item['file']: item for item in sources.values()}
    for link in node.all('a'):
        if 'data-source' not in link.attrs:
            continue
        source = by_file[link.attrs['data-source']]
        if 'data-read-at' in link.attrs:
            assert link.attrs['data-read-at'] == source['read_at'], 'Incorrect source read time'
        assert link.attrs['href'] == source['url'], 'Incorrect source URL'
        assert (source['read_at'], source['url']) in reads, 'Read time absent from read-at.tsv'
        found.append(source['file'])
    return found


def check_provenance(raw, sources, reads, documents):
    doc = Document(raw)
    body = article(doc)
    container = next((n for n in body.children if not isinstance(n, str)
                      and n.tag == 'div' and n.attrs.get('class') == 'wrap'), body)
    groups = [[]]
    for node in container.children:
        if isinstance(node, str):
            continue
        if node.tag in {'h2', 'section'}:
            groups.append([])
        groups[-1].append(node)
    section_refs = {}
    body_refs = []
    for group in groups:
        refs = [ref for node in group for ref in cited_sources(node, sources, reads)]
        if any(node.attrs.get('class') == 'faq' for node in group):
            refs = body_refs
        body_refs = body_refs + refs
        for node in group:
            for child in itertools.chain([node], node.all()):
                section_refs[id(child)] = refs
    for node in itertools.chain(article(doc).all('p'), article(doc).all('td')):
        refs = section_refs.get(id(node), [])
        value = normal(text(node))
        if DEFAULT.search(value) or node.tag == 'td':
            assert refs, 'Default or table claim has no section source'
        quotes = QUOTED.findall(value)
        quotes += [normal(text(q)) for q in node.all('q')]
        quotes += [normal(text(q)) for q in node.all('blockquote')]
        for quote in quotes:
            assert any(normal(quote) in documents[ref] for ref in refs), 'Quotation absent from source'
    for quote in article(doc).all('blockquote'):
        refs = section_refs.get(id(quote), [])
        assert any(normal(text(quote)) in documents[ref] for ref in refs), 'Quotation absent from source'


def jaccard(left, right):
    union = len(left | right)
    return len(left & right) / union if union else 0.0


def article_prose(raw):
    # Citations are attribution, not authored prose for the word floor.
    raw = re.sub(r'<a\b[^>]*\bdata-(?:repo-)?source="[^"]*"[^>]*>.*?</a>',
                 '', raw, flags=re.S)
    return prose(Document(raw))


def similarities(new, existing):
    """Count only shared shingles, then calculate exact Jaccard for candidates."""
    inverted = {}
    for path, tokens in existing.items():
        for token in tokens:
            inverted.setdefault(token, []).append(path)
    maxima = {}
    for path, tokens in new.items():
        counts = Counter(other for token in tokens for other in inverted.get(token, [])
                         if other != path)
        scores = [(count / (len(tokens) + len(existing[other]) - count), other)
                  for other, count in counts.items()]
        maxima[path] = max(scores, default=(0.0, ''))
    return maxima


class HostPageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = hosts.load_data()
        cls.sources = cls.data['sources']
        cls.pages = cls.data['pages']
        cls.read_log = [line.split('\t') for line in (hosts.DATA / 'read-at.tsv').read_text().splitlines()]
        cls.reads = {(r[0], r[4]) for r in cls.read_log}
        cls.documents = check_fact_excerpts(cls.data, PRIVATE_DOCS)
        cls.scratch = tempfile.TemporaryDirectory(prefix='docket-host-pages-test-')
        cls.addClassCleanup(cls.scratch.cleanup)
        with patch.object(render, 'SITE', Path(cls.scratch.name)):
            paths = hosts.build_all()
        cls.raw = {path.relative_to(cls.scratch.name).as_posix(): path.read_text() for path in paths}
        cls.prose = {path: article_prose(raw) for path, raw in cls.raw.items()}
        cls.shingles = {path: shingles(value) for path, value in cls.prose.items()}
        cls.baseline = {path.relative_to(ROOT / 'site').as_posix(): shingles(article_prose(path.read_text()))
                        for path in (ROOT / 'site').rglob('*.html')}
        cls.new_max = similarities(cls.shingles, cls.shingles)
        cls.site_max = similarities(cls.shingles, cls.baseline)

    def key(self, page):
        return 'ai-crawlers/hosts/' + (page['slug'] + '/' if page['slug'] else '') + 'index.html'

    def test_sample_has_only_anonymous_sites_and_expected_counts(self):
        path = hosts.DATA / 'robots-sample-2026-11-12.json'
        raw = path.read_text()
        sample = hosts.load_sample()
        self.assertEqual(raw, json.dumps(sample, indent=1, sort_keys=True) + '\n')
        self.assertNotIn('http', raw.lower())
        # The method includes a filename and a Python module, both supplied in the job.
        anonymous = raw.replace('robots.txt', '').replace('urllib.robotparser', '')
        self.assertNotRegex(anonymous, r'(?i)\b[a-z0-9-]+\.[a-z]{2,}\b')
        expected = {'vercel': (3, 3), 'netlify': (2, 2), 'shopify': (3, 3),
                    'squarespace': (1, 1), 'github-pages': (1, 0),
                    'cloudflare': (0, 0), 'wix': (0, 0), 'wordpress-com': (0, 0),
                    'webflow': (0, 0)}
        self.assertEqual(set(sample['hosts']), set(expected))
        for host, counts in expected.items():
            record = sample['hosts'][host]
            with self.subTest(host=host):
                self.assertEqual((record['sites_confirmed'], record['sites_read']), counts)
                self.assertEqual(len(record['sites']), counts[0])
                self.assertEqual(sum(site['robots_status'] == 200 for site in record['sites']), counts[1])
                for index, site in enumerate(record['sites'], 1):
                    self.assertEqual(set(site), {'bots', 'index', 'platform', 'robots_status'})
                    self.assertEqual(site['index'], index)
                    self.assertEqual(site['platform'], host)
                    self.assertEqual(set(site['bots']), set(hosts.BOTS))
                    self.assertTrue(all(bot['home_allowed'] for bot in site['bots'].values()))

    def test_measurement_sections_match_the_sample_and_stay_scoped(self):
        sample = hosts.load_sample()
        for page in self.pages:
            raw = self.raw[self.key(page)]
            self.assertNotRegex(normal(text(article(Document(raw)))), r'(?i)\blikely\b')
            if page['kind'] != 'host':
                self.assertNotIn('What we measured', raw)
                continue
            host = page['host']
            body = article(Document(raw))
            section = next(n for n in body.all('section')
                           if n.attrs.get('aria-label') == 'What we measured')
            paragraphs = [normal(text(n)) for n in section.all('p')]
            self.assertFalse(list(section.all('a')))
            self.assertEqual(normal(text(next(section.all('h2')))), 'What we measured')
            siblings = section.parent.children
            previous = [n for n in siblings[:siblings.index(section)] if not isinstance(n, str)][-1]
            self.assertEqual(previous.tag, 'p')
            record = sample['hosts'][host]
            if not record['sites_confirmed']:
                self.assertEqual(paragraphs, ['We did not measure any customer site on this host.'])
                self.assertNotRegex(' '.join(paragraphs), r'(?i)\bmeasured\b')
                continue
            count = record['sites_read']
            phrase = f'On the {count} sites read on {sample["read_date"]}'
            if host == 'github-pages':
                phrase = f'On the 1 site checked on {sample["read_date"]}'
                self.assertNotIn('site read', normal(text(body)))
                self.assertIn('it answered 404', paragraphs[0])
            elif host == 'squarespace':
                phrase = f'On the 1 site read on {sample["read_date"]}'
                self.assertEqual(paragraphs[0],
                                 'On the 1 site read on 12 November 2026, GPTBot, ClaudeBot, '
                                 'Google-Extended, Applebot-Extended and CCBot are named in the '
                                 'file, but its rules are path rules and none blocks the home '
                                 'page. PerplexityBot is not named and falls under the * group.')
                self.assertNotIn('blocked', text(section).lower())
            else:
                self.assertIn('home page was allowed for all six bots', paragraphs[0])
                self.assertIn('every site used the * group' if host != 'vercel' else
                              "one site's file had no group for any of the six bots, "
                              'the other two used the * group', paragraphs[0])
            self.assertTrue(paragraphs[0].startswith(phrase))
            self.assertEqual(paragraphs[-2:], [sample['scope'], 'Source: ' + sample['source'] + '.'])
            if host == 'vercel':
                self.assertEqual(paragraphs[1], "Two of the three sites may be Vercel's own "
                                 'products, so read the rows before generalising.')

    def test_measurements_derive_counts_dates_and_bot_lists_from_sample(self):
        sample = hosts.load_sample()
        sample['read_date'] = '13 November 2026'
        sample['hosts']['netlify']['sites_read'] = 4
        self.assertIn('On the 4 sites read on 13 November 2026', hosts.measurements('netlify', sample))
        bots = sample['hosts']['squarespace']['sites'][0]['bots']
        bots['GPTBot']['group'] = '*'
        bots['PerplexityBot']['group'] = 'named'
        value = normal(text(Document(hosts.measurements('squarespace', sample)).root))
        self.assertIn('ClaudeBot, PerplexityBot, Google-Extended, Applebot-Extended and CCBot are named', value)
        self.assertIn('GPTBot is not named and falls under the * group.', value)

    def test_measurement_section_is_the_only_page_change(self):
        with patch.object(render, 'SITE', Path(self.scratch.name) / 'without-measurements'):
            with patch.object(hosts, 'measurements', return_value=''):
                paths = hosts.build_all()
        for page, path in zip(self.pages, paths):
            raw = self.raw[self.key(page)]
            if page['kind'] == 'host':
                section = hosts.measurements(page['host'], hosts.load_sample())
                self.assertEqual(raw.count(section), 1)
                raw = raw.replace(section, '', 1)
            self.assertEqual(raw, path.read_text())

    def test_every_page_builds_with_title_date_description_and_prose(self):
        self.assertEqual(len(self.raw), len(self.pages))
        for page in self.pages:
            key = self.key(page)
            with self.subTest(page=key):
                doc = Document(self.raw[key])
                title = next(doc.root.all('title'))
                self.assertEqual(normal(text(title.children[0])), page['title'])
                self.assertLessEqual(len(page['title']), 60)
                self.assertGreaterEqual(len(page['description']), 120)
                self.assertLessEqual(len(page['description']), 160)
                schemas = [json.loads(''.join(node.children)) for node in doc.root.all('script')
                           if node.attrs.get('type') == 'application/ld+json']
                self.assertTrue(any(s.get('datePublished') == '2026-11-12' for s in schemas))
                self.assertIn('2026-11-12', next(doc.root.all('time')).attrs['datetime'])
                floor = 350 if page['kind'] == 'bot' else 450
                self.assertGreaterEqual(len(self.prose[key].split()), floor)
                self.assertEqual(len(page['intro']), 2)
                self.assertTrue(all(len(item['text'].split()) <= 55 for item in page['intro']))
                self.assertGreaterEqual(len(page['faq']), 3)
                self.assertLessEqual(len(page['faq']), 5)
        questions = [q['question'] for page in self.pages for q in page['faq']]
        self.assertEqual(len(questions), len(set(questions)))

    def test_prose_is_distinct_from_new_and_existing_pages(self):
        for key in self.raw:
            with self.subTest(page=key):
                self.assertLess(self.new_max[key][0], .40, self.new_max[key])
                self.assertLess(self.site_max[key][0], .50, self.site_max[key])

    def test_sources_have_short_fact_excerpts_with_logged_reads(self):
        self.assertFalse(list(hosts.DATA.glob('*.html')), 'Raw captures must stay private')
        log = {(r[0], r[4]): r for r in self.read_log}
        for source in self.sources.values():
            with self.subTest(source=source['file']):
                record = log[(source['read_at'], source['url'])]
                self.assertEqual(record[2], '200')
                if PRIVATE_DOCS.exists():
                    self.assertEqual((PRIVATE_DOCS / source['file']).stat().st_size, int(record[3]))
                self.assertNotIn('Just a moment...', self.documents[source['file']])
        for raw in self.raw.values():
            check_provenance(raw, self.sources, self.reads, self.documents)

    def test_fact_checks_reject_missing_or_invalid_support(self):
        absent = Path(self.scratch.name) / 'absent-private-docs'
        check_fact_excerpts(self.data, absent)
        mutations = [
            lambda d: d['sources']['cf-policy'].pop('sha256'),
            lambda d: d['sources']['cf-policy']['facts']['default'].update(excerpt=''),
            lambda d: d['sources']['cf-policy']['facts']['default'].update(
                excerpt='First sentence. Second sentence. Third sentence.'),
            lambda d: d['sources']['cf-policy']['facts']['default'].pop('url'),
            lambda d: d['pages'][1]['intro'][0].pop('facts'),
            lambda d: d['pages'][1]['intro'][0]['facts'].update({'cf-policy': []}),
            lambda d: d['pages'][1]['intro'][0]['facts'].update({'cf-policy': ['invented']}),
        ]
        for mutate in mutations:
            with self.subTest(mutation=mutate):
                changed = json.loads(json.dumps(self.data))
                mutate(changed)
                with self.assertRaises((AssertionError, KeyError)):
                    check_fact_excerpts(changed, absent)
        # A small synthetic private capture exercises both checks on clean clones.
        with tempfile.TemporaryDirectory(prefix='docket-host-capture-test-') as scratch:
            capture = Path(scratch) / 'capture.html'
            raw = b'<p>First sentence. Second sentence.</p>'
            capture.write_bytes(raw)
            sample = {'sources': {'sample': {
                'file': capture.name, 'sha256': hashlib.sha256(raw).hexdigest(),
                'url': 'https://example.com/docs', 'read_at': '2026-11-12T00:00:00Z',
                'label': 'Sample documentation', 'facts': {'first': {
                    'statement': 'The first sentence is present.', 'excerpt': 'First sentence.',
                    'url': 'https://example.com/docs'}}}}, 'pages': []}
            check_fact_excerpts(sample, Path(scratch))
            sample['sources']['sample']['facts']['first']['excerpt'] = 'Invented sentence.'
            with self.assertRaisesRegex(AssertionError, 'absent from raw'):
                check_fact_excerpts(sample, Path(scratch))
            sample['sources']['sample']['sha256'] = '0' * 64
            with self.assertRaisesRegex(AssertionError, 'hash differs'):
                check_fact_excerpts(sample, Path(scratch))

    def test_citations_are_short_scoped_and_collected_at_the_end(self):
        for page in self.pages:
            with self.subTest(page=page['slug']):
                raw = self.raw[self.key(page)]
                body = article(Document(raw))
                listing = next(n for n in body.all('section')
                               if n.attrs.get('aria-label') == 'Sources')
                expected = hosts.page_source_keys(page)
                self.assertEqual(cited_sources(listing, self.sources, self.reads),
                                 [self.sources[k]['file'] for k in expected])
                self.assertEqual(list(body.all('section'))[-1], listing)
                for entry, key in zip(listing.all('li'), expected):
                    source = self.sources[key]
                    self.assertEqual(normal(text(entry)).replace(' ,', ','), source['label']
                                     + ', read 12 November 2026 at '
                                     + source['read_at'][11:16] + ' UTC')
                for key, source in self.sources.items():
                    self.assertEqual(raw.count(source['read_at']), int(key in expected))
                for link in body.all('a'):
                    if 'data-source' not in link.attrs:
                        continue
                    self.assertNotIn('read ', text(link).lower())
                    if link not in list(listing.all('a')):
                        self.assertNotIn('data-read-at', link.attrs)
                for faq in (n for n in body.all('section')
                            if n.attrs.get('class') == 'faq'):
                    self.assertFalse(list(faq.all('a')))
                    self.assertEqual([normal(text(n)) for n in faq.all('p')],
                                     [item['answer'] for item in page['faq']])
                groups = [page['intro']] + [s['paragraphs'] for s in page['sections']]
                for items in groups:
                    seen = set()
                    rendered = ''.join(hosts.paragraph(item, self.sources, seen) for item in items)
                    refs = cited_sources(Document(rendered).root, self.sources, self.reads)
                    self.assertEqual(len(refs), len(set(refs)))
                    for item in items:
                        self.assertIn(hosts.escape(item['text']), rendered)
                body_keys = {k for items in groups for item in items for k in item['sources']}
                self.assertTrue({k for item in page['faq'] for k in item['sources']} <= body_keys)

    def test_host_table_cell_text_appears_in_at_most_two_rows(self):
        for page in self.pages:
            if page['kind'] != 'host':
                continue
            with self.subTest(page=page['slug']):
                body = article(Document(self.raw[self.key(page)]))
                for table in body.all('table'):
                    counts = Counter(value for row in table.all('tr')
                                     for value in {normal(text(cell))
                                                   for cell in row.all()
                                                   if cell.tag in {'th', 'td'}})
                    self.assertTrue(all(count <= 2 for count in counts.values()), counts)

    def test_identical_bot_rules_render_as_a_sourced_host_note(self):
        for page in self.pages:
            if page['kind'] != 'host':
                continue
            rules = {(item['default'], item['change']) for item in page['bots'].values()}
            if len(rules) != 1:
                continue
            with self.subTest(page=page['slug']):
                body = article(Document(self.raw[self.key(page)]))
                self.assertFalse(list(body.all('table')))
                note = page['bot_note']
                self.assertIn(hosts.escape(note['text']), self.raw[self.key(page)])
                rendered = hosts.paragraph(note, self.sources, set())
                self.assertEqual(cited_sources(Document(rendered).root, self.sources, self.reads),
                                 [self.sources[key]['file'] for key in note['sources']])

    def test_tables_have_plain_cells_and_one_source_line_per_guide(self):
        for page in self.pages:
            if page['kind'] != 'host':
                continue
            with self.subTest(page=page['slug']):
                body = article(Document(self.raw[self.key(page)]))
                table = next(body.all('table'), None)
                if table is None:
                    continue
                for cell in table.all('td'):
                    self.assertFalse(list(cell.all('a')))
                    self.assertNotRegex(text(cell), r'(?i)read \d|\d{4}-\d{2}-\d{2}')
                wrapper = table.parent
                siblings = wrapper.parent.children
                start = siblings.index(wrapper) + 1
                keys = list(dict.fromkeys(k for bot in hosts.BOTS
                                          for k in page['bots'][bot]['sources']))
                for node, key in zip(siblings[start:start + len(keys)], keys):
                    self.assertEqual(normal(text(node)).replace(' ,', ','),
                                     'Source: ' + self.sources[key]['label']
                                     + ', read 12 November 2026.')
                    self.assertEqual(cited_sources(node, self.sources, self.reads),
                                     [self.sources[key]['file']])

    def test_default_sources_contain_the_claims_and_conflict_is_visible(self):
        claims = {
            'cf-policy': 'For new domains, Search, Agents, and Training use Allow (do not block) by default.',
            'cf-blog': 'Training and Agent will be blocked by default on the pages that display ads',
            'cf-log': 'Training and Agent are blocked on pages that display ads while Search remains allowed',
            'vercel-rules': 'The ruleset is inactive by default. In the dashboard this is labeled Allow.',
            'squarespace': 'We default to having the box unchecked',
        }
        for key, quote in claims.items():
            self.assertTrue(quote in self.documents[self.sources[key]['file']], key)
        cloudflare = self.raw['ai-crawlers/hosts/cloudflare/index.html']
        for key in ('cf-policy', 'cf-blog', 'cf-log'):
            self.assertIn(self.sources[key]['url'], cloudflare)
            self.assertIn(self.sources[key]['read_at'], cloudflare)
        self.assertIn('2 November 2026', cloudflare)
        self.assertIn('15 September 2026', cloudflare)
        self.assertIn('Neither reading explains why those answers differ.', cloudflare)
        self.assertIn('Security &gt; Settings', cloudflare)
        shopify = self.raw['ai-crawlers/hosts/shopify/index.html']
        self.assertIn('rendered template output does not always equal the generated file', shopify)
        self.assertIn('compare', shopify.lower())

    def test_each_host_has_six_bots_and_every_pair_is_accounted_for(self):
        merges = json.loads((hosts.DATA / 'merges.json').read_text())
        host_pages = [page for page in self.pages if page['kind'] == 'host']
        self.assertEqual({p['host'] for p in host_pages},
                         {'cloudflare', 'vercel', 'netlify', 'wix', 'squarespace',
                          'shopify', 'wordpress-com', 'webflow', 'github-pages'})
        expected = {(p['host'], bot) for p in host_pages for bot in hosts.BOTS}
        dedicated = {(p['host'], p['bot']) for p in self.pages if p['kind'] == 'bot'}
        merged = {(m['host'], m['bot']) for m in merges}
        self.assertEqual(len(merged), len(merges))
        self.assertFalse(dedicated & merged)
        self.assertEqual(expected, dedicated | merged)
        for item in merges:
            self.assertGreater(len(item['reason'].split()), 12)
            self.assertEqual(item['url'], '/ai-crawlers/hosts/' + item['host'] + '/')
        for page in host_pages:
            body = article(Document(self.raw[self.key(page)]))
            names = [normal(text(link)) for link in body.all('a')
                     if normal(text(link)) in hosts.BOTS]
            self.assertCountEqual(names, hosts.BOTS)
            self.assertEqual(set(page['bots']), set(hosts.BOTS))
        for page in self.pages:
            if page['kind'] == 'bot':
                self.assertIn(page['bot'], ' '.join(self.documents[self.sources[k]['file']]
                                                  for item in page['intro'] for k in item['sources']))

    def test_next_steps_are_ordered_tracked_and_no_other_kerr_domains_linked(self):
        for page in self.pages:
            with self.subTest(page=page['slug']):
                doc = Document(self.raw[self.key(page)])
                section = next(n for n in article(doc).all('section')
                               if n.attrs.get('aria-label') == 'Next step')
                links = list(section.all('a'))
                self.assertEqual(len(links), 2)
                src = 'host-' + page['host']
                self.assertEqual(links[0].attrs['href'], '/tools/ai-crawler-checker/?src=' + src)
                # The explicitly requested tracking helper is the sole allowed Kerr service.
                self.assertEqual(links[1].attrs['href'], render.download_url(src))
                self.assertEqual(parse_qs(urlsplit(links[1].attrs['href']).query)['src'], [src])
                for link in doc.root.all('a'):
                    href = link.attrs.get('href', '')
                    domain = (urlsplit(href).hostname or '').lower()
                    self.assertFalse(any(domain == s or domain.endswith('.' + s)
                                         for s in (*SIBLINGS, 'kerrandcompanyholdings.com')))
                    if domain.endswith('.kerrco.workers.dev'):
                        self.assertEqual(href, render.download_url(src))
                value = normal(text(article(doc)))
                value = value.replace("Two of the three sites may be Vercel's own products, "
                                      'so read the rows before generalising.', '')
                self.assertIsNone(BANNED.search(value))
                self.assertNotRegex(value, '[\u2013\u2014]')
                self.assertNotRegex(value, r'\$\d')

    def test_bot_links_reuse_existing_reference_addresses(self):
        crawlers = {row['token']: row for row in json.loads(
            (ROOT / 'data/ai-crawler-pages-2026-10.json').read_text())['rows']}
        for page in self.pages:
            if page['kind'] != 'host':
                continue
            body = article(Document(self.raw[self.key(page)]))
            self.assertCountEqual([a.attrs['href'] for a in body.all('a')
                                   if normal(text(a)) in hosts.BOTS],
                                  [hosts.bot_url(bot, crawlers) for bot in hosts.BOTS])
        build = (HERE.parent / 'build.py').read_text()
        self.assertIn('import ai_bot_host_pages', build)
        self.assertIn('pages += ai_bot_host_pages.build_all()', build)
        index = self.raw['ai-crawlers/hosts/index.html']
        for page in self.pages:
            if page['slug']:
                self.assertIn(hosts.page_url(page), index)

    def test_provenance_checks_reject_missing_dates_and_invented_quotes(self):
        source = self.sources['cf-policy']
        good = ('<article><p>The default is described here. '
                + hosts.source_link('cf-policy', self.sources, dated=True) + '</p></article>')
        check_provenance(good, self.sources, self.reads, self.documents)
        with self.assertRaises(AssertionError):
            check_provenance(good.replace(source['read_at'], '2026-11-12T00:00:00Z'),
                             self.sources, self.reads, self.documents)
        with self.assertRaises(AssertionError):
            check_provenance('<article><p>Blocked by default.</p></article>',
                             self.sources, self.reads, self.documents)
        with self.assertRaises(AssertionError):
            check_provenance(good.replace('The default is described here.',
                                          '<q>All six bots are always blocked.</q>'),
                             self.sources, self.reads, self.documents)
        self.assertEqual(jaccard(shingles('one two three four five six'),
                                 shingles('one two three four five six')), 1.0)

    def test_report_page_measurements(self):
        for page in self.pages:
            key = self.key(page)
            maximum = max(self.new_max[key], self.site_max[key])
            print(f'{hosts.page_url(page)} {len(self.prose[key].split())} prose words; '
                  f'max Jaccard {maximum[0]:.4f} with {maximum[1]}')


if __name__ == '__main__':
    unittest.main()
