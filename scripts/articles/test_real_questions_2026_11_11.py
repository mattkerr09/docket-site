#!/usr/bin/env python3
"""Offline checks of the rendered copy, source labels and source attribution."""
from __future__ import annotations

import ast
import copy
import json
import re
import sys
import tempfile
import unittest
from datetime import datetime
from html import unescape
from html.parser import HTMLParser
from pathlib import Path
from unittest.mock import patch
from urllib.parse import urlsplit

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path[:0] = [str(HERE), str(HERE.parent)]
import best_free_seo_audit_plugins as plugins_page
import learn_free_seo_audit_api as api_page
import learn_seo_audit_report as report_page
import render
from verify_sibling_links import SIBLINGS, offenders

DATA = report_page.EVIDENCE
NUMBER = re.compile(r'(?<!\w)\d+(?:,\d{3})*(?:\.\d+)*(?!\w)')
VOID = set('area base br col embed hr img input link meta param source track wbr'.split())
SKIP = {'head', 'script', 'style', 'nav', 'header', 'footer'}
BANNED = re.compile(r'\b(?:fields?|branches|branch|helpers?|matches|endpoints?|entries|rows?|tags|conditions?|generators?|datasets?|manifests?|Codex|Article Studio)\b', re.I)
HEDGING = re.compile(r'does not establish|does not settle|the sources read here|the captured text|'
                     r'the wording we read|we make no such claim here', re.I)
# Counts from the rendered pages at the job's base commit, 7aa50ab08.
HEDGING_BEFORE = {
    'learn/seo-audit-report': 1,
    'best/free-seo-audit-plugins-wordpress': 7,
    'learn/free-seo-audit-api': 4,
}
PAGES = [
    (report_page, 'learn/seo-audit-report', 'seo audit report'),
    (plugins_page, 'best/free-seo-audit-plugins-wordpress', 'free seo audit plugin'),
    (api_page, 'learn/free-seo-audit-api', 'free seo audit api'),
]


def normal(value: str) -> str:
    return ' '.join(unescape(value).split())


class Node:
    def __init__(self, tag='', attrs=None, parent=None):
        self.tag, self.attrs, self.parent = tag, dict(attrs or []), parent
        self.children = []

    def all(self, tag=None):
        for child in self.children:
            if isinstance(child, Node):
                if tag is None or child.tag == tag:
                    yield child
                yield from child.all(tag)


def hidden(node):
    return (node.tag in SKIP or bool(set(node.attrs.get('class', '').split()) &
            {'byline', 'crumb', 'buy-strip', 'skip-link'}) or node.attrs.get('id') == 'try')


def text(node, skip=frozenset()):
    if isinstance(node, str):
        return node
    if hidden(node) or node.tag in skip:
        return ''
    return ' '.join(text(c, skip) for c in node.children)


class Document(HTMLParser):
    def __init__(self, raw):
        super().__init__(convert_charrefs=True)
        self.root = Node()
        self.current = self.root
        self.feed(raw)

    def handle_starttag(self, tag, attrs):
        node = Node(tag, attrs, self.current)
        self.current.children.append(node)
        if tag not in VOID:
            self.current = node

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in VOID:
            self.handle_endtag(tag)

    def handle_endtag(self, tag):
        node = self.current
        while node.parent is not None:
            if node.tag == tag:
                self.current = node.parent
                return
            node = node.parent

    def handle_data(self, data):
        self.current.children.append(data)


def article(doc):
    return next(doc.root.all('article'), next(doc.root.all('main'), doc.root))


def prose(doc):
    return normal(text(article(doc), {'table', 'pre', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'}))


def shingles(value):
    words = re.findall(r"[a-z0-9']+", value.casefold())
    return {' '.join(words[i:i + 5]) for i in range(len(words) - 4)}


def jaccard(a, b):
    return len(a & b) / len(a | b) if a or b else 0.0


def lookup(data, pointer):
    for key in pointer.strip('/').split('/'):
        data = data[int(key)] if isinstance(data, list) else data[key]
    return data


def source_text(name, plugin=None):
    raw = (DATA / name).read_text()
    if name.endswith('.json'):
        data = json.loads(raw)
        if plugin:
            data = next(p['description_text'] for p in data['plugins'] if p['slug'] == plugin)

        def strings(value):
            if isinstance(value, dict):
                return ' '.join(strings(v) for v in value.values())
            if isinstance(value, list):
                return ' '.join(strings(v) for v in value)
            return str(value)
        raw = strings(data)
    return normal(raw)


def ancestor(node, attr):
    while node is not None:
        if attr in node.attrs:
            return node.attrs[attr]
        node = node.parent
    return None


def validate_fact(node):
    """Bind each value to its source label, not a bag of allowed numbers."""
    name, pointer = node.attrs['data-source'], node.attrs['data-pointer']
    value = lookup(report_page.source(name), pointer)
    if name == 'read-times.json':
        assert normal(text(node)) == normal(value), (pointer, text(node))
        return
    if node.attrs.get('data-run-summary') == 'true':
        audit = report_page.source('audit.json')
        window = report_page.source('read-times.json')['notes']['report_capture']
        assert name == 'audit.json' and pointer == '/version'
        expected = (f'Check Engine {audit["version"]} audited checkengineseo.com on {window}, '
                    f'capped at {audit["stats"]["pages_crawled"]} pages.')
        assert normal(text(node)) == expected, (text(node), expected)
        return
    labels = {
        ('psi-checkengineseo-mobile.json', '/error/code'): 'HTTP status',
    }
    if name == 'plugins-trimmed.json':
        label = {'active_installs': 'Active installs', 'rating': 'Rating',
                 'last_updated': 'Last updated'}[pointer.rsplit('/', 1)[1]]
        owner = lookup(report_page.source(name), '/'.join(pointer.split('/')[:-1]))['slug']
        assert ancestor(node, 'data-plugin') == owner, (pointer, 'wrong plugin')
        field = pointer.rsplit('/', 1)[1]
        if field == 'active_installs':
            value = f'{value // 1_000_000}+ million' if value >= 1_000_000 else f'{value:,}+'
        elif field == 'rating':
            value = f'{value / 20:.1f} out of 5'
        else:
            updated = datetime.strptime(value.split()[0], '%Y-%m-%d')
            value = f'{updated.day} {updated:%B %Y}'
    else:
        label = labels[(name, pointer)]
    assert normal(text(node)) == f'{label}: {value}', (pointer, text(node), label, value)


def validate_numbers(node, covered=False):
    if hidden(node):
        return
    if 'data-pointer' in node.attrs:
        validate_fact(node)
        covered = True
    if node.tag == 'q':
        excerpt = normal(text(node))
        assert excerpt in source_text(node.attrs['data-source'], ancestor(node, 'data-plugin')), excerpt
        # A bare digit in quotation marks cannot acquire a new label in prose.
        assert not NUMBER.search(excerpt) or re.search(r'[a-zA-Z]{3}', excerpt), excerpt
        covered = True
    if node.tag == 'table':
        # Area/order tables are compared with the original below. Plugin values
        # still go through the labelled pointer check inside the table.
        covered = True
    for child in node.children:
        if isinstance(child, Node):
            validate_numbers(child, covered)
        elif NUMBER.search(child):
            assert covered, f'Number without labelled source: {child.strip()}'


def faq_items(doc):
    result = []
    for node in doc.root.all():
        if 'faq-item' in node.attrs.get('class', '').split():
            q = next(node.all('h3'))
            answer = next(node.all('p'))
            result.append((normal(text(q)), normal(text(answer))))
    return result


def json_faq(raw):
    found = []

    def walk(value):
        if isinstance(value, dict):
            if value.get('@type') == 'FAQPage':
                found.extend((normal(q['name']), normal(q['acceptedAnswer']['text']))
                             for q in value['mainEntity'])
            for v in value.values():
                walk(v)
        elif isinstance(value, list):
            for v in value:
                walk(v)
    for content in re.findall(r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>', raw, re.S):
        walk(json.loads(content))
    return found


def table_cells(node):
    return [[normal(text(c)) for c in row.children if isinstance(c, Node) and c.tag in {'th', 'td'}]
            for row in node.all('tr')]


class RealQuestionsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix='real-questions-pages-')
        cls.raw, cls.docs = {}, {}
        with patch.object(render, 'SITE', Path(cls.temp.name)):
            for module, slug, _ in PAGES:
                path = module.build()
                cls.raw[slug] = path.read_text()
                cls.docs[slug] = Document(cls.raw[slug])
        cls.nearest = {slug: (0.0, '') for _, slug, _ in PAGES}
        own = {slug: shingles(prose(doc)) for slug, doc in cls.docs.items()}
        cls.existing_faq = set()
        for path in sorted((ROOT / 'site').rglob('*.html')):
            relative = path.parent.relative_to(ROOT / 'site').as_posix()
            raw = path.read_text()
            if relative in own:
                continue
            doc = Document(raw)
            cls.existing_faq.update(q.casefold() for q, _ in faq_items(doc))
            cls.existing_faq.update(q.casefold() for q, _ in json_faq(raw))
            other = shingles(prose(doc))
            for slug, words in own.items():
                score = jaccard(words, other)
                if score > cls.nearest[slug][0]:
                    cls.nearest[slug] = (score, '/' + relative + '/')
        # The new pages must also differ from each other, before or after a full build.
        for slug, words in own.items():
            for other_slug, other in own.items():
                if slug != other_slug:
                    score = jaccard(words, other)
                    if score > cls.nearest[slug][0]:
                        cls.nearest[slug] = (score, '/' + other_slug + '/')

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def test_pages_metadata_length_and_saved_build(self):
        print('\nPage | Prose words | Max 5-word Jaccard | Nearest page')
        for module, slug, query in PAGES:
            with self.subTest(page=slug):
                raw, doc = self.raw[slug], self.docs[slug]
                title = normal(next(doc.root.all('title')).children[0])
                h1 = normal(text(next(doc.root.all('h1'))))
                first = next(n for n in article(doc).all('p') if not hidden(n))
                for target in (title, h1, normal(text(first))):
                    self.assertTrue(set(query.split()) <= set(re.findall(r'[a-z]+', target.casefold())), target)
                self.assertLessEqual(len(title), 60)
                desc = next(n.attrs['content'] for n in doc.root.all('meta') if n.attrs.get('name') == 'description')
                self.assertTrue(120 <= len(desc) <= 160, len(desc))
                self.assertRegex(raw, r'"datePublished"\s*:\s*"2026-11-11"')
                calls = [n for n in ast.walk(ast.parse(Path(module.__file__).read_text()))
                         if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == 'render']
                self.assertTrue(calls)
                for call in calls:
                    self.assertTrue(any(k.arg == 'published' and isinstance(k.value, ast.Constant)
                                        and k.value.value == '2026-11-11' for k in call.keywords))
                count = len(prose(doc).split())
                score, pair = self.nearest[slug]
                print(f'/{slug}/ | {count} | {score:.6f} | {pair}')
                self.assertGreater(count, 600)
                self.assertLess(score, 0.5)
                built = ROOT / 'site' / slug / 'index.html'
                self.assertTrue(built.exists(), 'Run the site build first')
                self.assertEqual(normal(text(article(Document(built.read_text())))), normal(text(article(doc))))

    def test_every_number_has_its_original_label_and_value(self):
        for slug, doc in self.docs.items():
            with self.subTest(page=slug):
                validate_numbers(article(doc))

    def test_number_only_check_would_accept_wrong_label(self):
        # Both values are genuinely in the source. Swapping installs and rating
        # must fail even though a number-only allowlist would accept the claim.
        doc = copy.deepcopy(self.docs['best/free-seo-audit-plugins-wordpress'])
        node = next(n for n in doc.root.all('span') if n.attrs.get('data-pointer', '').endswith('/active_installs'))
        original = normal(text(node))
        node.children = [original.replace('Active installs', 'Rating')]
        self.assertIn(NUMBER.search(text(node))[0], source_text('plugins-trimmed.json'))
        with self.assertRaises(AssertionError):
            validate_numbers(article(doc))
        node.children = [original]
        node.attrs['data-pointer'] = node.attrs['data-pointer'].replace('active_installs', 'rating')
        with self.assertRaises(AssertionError):
            validate_numbers(article(doc))

    def test_quotations_are_exact_and_belong_to_the_named_plugin(self):
        for slug, doc in self.docs.items():
            for q in article(doc).all('q'):
                with self.subTest(page=slug, quote=text(q)):
                    self.assertIn(normal(text(q)), source_text(q.attrs['data-source'], ancestor(q, 'data-plugin')))
                    if slug.startswith('best/'):
                        self.assertLess(len(text(q).split()), 15)
        doc = copy.deepcopy(self.docs['best/free-seo-audit-plugins-wordpress'])
        q = next(article(doc).all('q'))
        q.children = ['Instantly discover which keywords your pages rank for.']
        with self.assertRaises(AssertionError):
            validate_numbers(article(doc))

    def test_plugins_are_selected_for_their_own_check_claim(self):
        data = report_page.source('plugins-trimmed.json')['plugins']
        # Include checking features such as per-post analysis as well as site
        # audits. A generic promise of good SEO scores is not a checking feature.
        claim = re.compile(r'\b(?:audit|analysis|checker)\b', re.I)
        selected = {p['slug'] for p in data if claim.search(unescape(p['description_text']))}
        self.assertEqual(selected, {'all-in-one-seo-pack', 'seo-by-rank-math', 'wp-seopress',
                                   'squirrly-seo', 'smartcrawl-seo', 'xagio-seo', 'broken-link-checker',
                                   'wordpress-seo'})
        doc = self.docs['best/free-seo-audit-plugins-wordpress']
        sections = [n for n in article(doc).all('section') if 'data-plugin' in n.attrs]
        self.assertEqual([n.attrs['data-plugin'] for n in sections],
                         [slug for slug in [r[0] for r in plugins_page.REVIEWS]])
        self.assertEqual({n.attrs['data-plugin'] for n in sections}, selected)
        self.assertEqual(len(sections), len(selected))
        for section in sections:
            values = [n for n in section.all('span') if 'data-pointer' in n.attrs]
            self.assertEqual(len(values), 3)
            for value in values:
                validate_fact(value)
            facts = next(n for n in section.all('p') if n.attrs.get('class') == 'plugin-facts')
            facts_text = normal(text(facts))
            self.assertEqual(facts_text.count('Active installs:'), 1)
            self.assertEqual(facts_text.count('Rating:'), 1)
            self.assertEqual(facts_text.count('Last updated:'), 1)
            self.assertRegex(facts_text, r'Rating: \d\.\d out of 5')
            self.assertRegex(facts_text, r'Last updated: \d{1,2} [A-Z][a-z]+ 2026\b')
        visible = normal(text(article(doc)))
        self.assertIn("Slim SEO's listing says its meta tags are generated for the best SEO scores but describes no checker or audit.", visible)
        yoast = next(n for n in sections if n.attrs['data-plugin'] == 'wordpress-seo')
        yoast_text = normal(text(yoast))
        for expected in ('SEO analysis to guide your keyword targeting',
                         'Readability analysis for clear, engaging, user-friendly writing',
                         'per post or page while you write, not a crawl of the whole site',
                         'up to 5 keyphrases in Premium',
                         'AI tools come with Yoast SEO Premium'):
            self.assertIn(expected, yoast_text)
        for name in ('SEOPress PRO', 'exclusive Pro features', 'Unique Features of Rank Math PRO'):
            self.assertIn(name, visible)

    def test_report_tables_full_findings_and_unknown_checks(self):
        doc = self.docs['learn/seo-audit-report']
        tables = {n.attrs['data-table']: n for n in article(doc).all('table')}
        md = (DATA / 'audit.md').read_text()
        expected = [[c.strip() for c in line.strip('|').split('|')]
                    for line in md.splitlines() if line.startswith('| ') and not line.startswith('| Area')]
        self.assertEqual(table_cells(tables['areas'])[1:], expected)
        data = report_page.source('audit.json')
        self.assertEqual(table_cells(tables['plan'])[1:],
                         [[str(p['rank']), p['phase'], p['title']] for p in data['plan']])
        full = [n for n in article(doc).all('section') if 'data-finding' in n.attrs]
        self.assertGreaterEqual(len(full), 3)
        for section in full:
            finding = next(p for p in data['plan'] if p['check_id'] == section.attrs['data-finding'])
            self.assertEqual([normal(text(q)) for q in section.all('q')],
                             [normal(finding[k]) for k in ('title', 'detail', 'fix')])
        quoted = {normal(text(q)) for q in article(doc).all('q')}
        for p in data['plan']:
            if p['tool_limit']:
                self.assertIn(normal(p['title']), quoted)
        self.assertIn(normal(data['score']['verdict']), quoted)
        self.assertFalse(data['score']['speaks_for_site'])
        self.assertEqual(data['stats']['pages_crawled'], 60)
        self.assertEqual(sum(a.attrs.get('href') == '/learn/seo-audit/' for a in article(doc).all('a')), 1)
        self.assertIn('PageSpeed Insights did not run', normal(text(article(doc))))
        self.assertNotIn('run', tables)
        summary = next(n for n in article(doc).all('p') if 'data-run-summary' in n.attrs)
        self.assertEqual(normal(text(summary)),
                         'Check Engine 1.3.161 audited checkengineseo.com on '
                         '11 November 2026, 13:31 to 13:33 UTC, capped at 60 pages.')
        for row in tables['plan'].all('tr'):
            stage = [n for n in row.children if isinstance(n, Node)][1]
            self.assertIn('width:5rem', stage.attrs['style'])
            self.assertIn('padding:0.6rem 1rem', stage.attrs['style'])

    def test_api_source_and_limits_are_present(self):
        value = normal(text(article(self.docs['learn/free-seo-audit-api'])))
        for expected in ('checkengine audit', '-f json', '-f csv', '-f sarif', '-f junit',
                         'checkengine serve', '127.0.0.1', 'no authentication', 'checkengine mcp',
                         'stdio', 'shared keyless daily quota', 'need a licence key'):
            self.assertIn(expected, value)
        self.assertIn('Binding it anywhere else exposes audit control', value)
        self.assertIn('optional for trial runs, but needed for automated multiple queries', value)
        self.assertIn('https://developers.google.com/speed/docs/insights/rest/v5/pagespeedapi/runpagespeed',
                      (DATA / 'psi-request-canonical.html').read_text())
        self.assertIn('mcp                 serve the engine to an AI assistant over MCP (stdio)',
                      (DATA / 'cli-main-help.txt').read_text())
        doc = self.docs['learn/free-seo-audit-api']
        self.assertEqual(normal(text(next(article(doc).all('pre')))),
                         'checkengine audit https://example.com -f json')
        self.assertIn('We ran the help commands for this article; we did not run this example audit.', value)

    def test_visible_copy_has_plain_facts_and_times(self):
        for slug, doc in self.docs.items():
            value = normal(text(doc.root))
            with self.subTest(page=slug):
                self.assertNotRegex(value, r'(?i)\.(?:json|md|txt)|T13:|\+00:00|Z\.|API scale|job record')
                self.assertNotRegex(value, r'\b\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}')
                self.assertNotRegex(value, r'\d{5,}')
                self.assertNotIn('Local source files read', value)
                self.assertNotIn("saved files' own times", value)
                self.assertNotIn('saved listing response', value)
                self.assertNotIn('run record', value)
        expected = {
            'learn/seo-audit-report': ('11 November 2026, 13:31 to 13:33 UTC',),
            'best/free-seo-audit-plugins-wordpress': ('11 November 2026, between 13:33 and 13:34 UTC',),
            'learn/free-seo-audit-api': ('documentation on 11 November 2026 at 13:34 UTC',
                                       'quota error on 11 November 2026 at 13:34 UTC'),
        }
        for slug, times in expected.items():
            value = normal(text(article(self.docs[slug])))
            for timestamp in times:
                self.assertEqual(value.count(timestamp), 1, (slug, timestamp))
            heading = next(n for n in article(self.docs[slug]).all('h2') if normal(text(n)) == 'Source note')
            following = heading.parent.children[heading.parent.children.index(heading) + 1:]
            notes = []
            for node in following:
                if isinstance(node, Node):
                    if node.tag != 'p':
                        break
                    notes.append(normal(text(node)))
            sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z])', ' '.join(notes))
            self.assertTrue(notes, slug)
            self.assertTrue(1 <= len(sentences) <= 2, (slug, sentences))

    def test_repeated_hedging_is_cut_by_at_least_a_quarter(self):
        print('\nPage | Hedging before | Hedging after')
        for slug, doc in self.docs.items():
            before = HEDGING_BEFORE[slug]
            after = len(HEDGING.findall(normal(text(article(doc)))))
            print(f'/{slug}/ | {before} | {after}')
            self.assertLessEqual(after, before * 0.75, slug)

    def test_voice_and_no_other_kerr_product_links(self):
        for slug, doc in self.docs.items():
            value = normal(text(article(doc)))
            clean = re.sub(r'\b(?:meta|HTML) tags\b', '', value, flags=re.I)
            with self.subTest(page=slug):
                self.assertFalse(BANNED.search(clean), BANNED.search(clean))
                self.assertNotRegex(value, '[\u2013\u2014]')
                # Parentheses in a full source quote must remain exact.
                outside_quotes = copy.deepcopy(article(doc))
                for q in outside_quotes.all('q'):
                    q.children = []
                self.assertNotRegex(normal(text(outside_quotes)), r'[()]')
                self.assertNotRegex(value, r'(?i)Black Friday|% off|half price')
                self.assertLessEqual(value.count('Check Engine'), 6)
                self.assertFalse(offenders({slug + '/index.html': self.raw[slug]}))
                for a in article(doc).all('a'):
                    host = urlsplit(a.attrs.get('href', '')).hostname or ''
                    self.assertFalse(any(host == h or host.endswith('.' + h) for h in (*SIBLINGS, 'docketseo.app')))

    def test_faq_is_unique_and_matches_json_ld(self):
        seen = set(self.existing_faq)
        for slug, doc in self.docs.items():
            questions = faq_items(doc)
            self.assertTrue(3 <= len(questions) <= 5)
            self.assertEqual(questions, json_faq(self.raw[slug]))
            body_without_faq = copy.deepcopy(article(doc))
            for n in body_without_faq.all('section'):
                if 'faq' in n.attrs.get('class', '').split():
                    n.children = []
            body = normal(text(body_without_faq))
            for q, answer in questions:
                self.assertNotIn(q.casefold(), seen, q)
                seen.add(q.casefold())
                self.assertNotIn(answer, body)

    def test_read_provenance_and_captured_files(self):
        info = report_page.source('read-times.json')
        for name, evidence in info['files'].items():
            self.assertTrue((DATA / name).exists())
            self.assertTrue(evidence['read_at'].startswith('2026-11-11T'))
            self.assertRegex(evidence['source_sha256'], r'^[0-9a-f]{64}$')
        self.assertNotIn('local_read', info['notes'])
        for key in ('report_capture', 'plugin_read', 'psi_docs_read', 'psi_call'):
            self.assertIn('11 November 2026', info['notes'][key])


if __name__ == '__main__':
    unittest.main(verbosity=2)
