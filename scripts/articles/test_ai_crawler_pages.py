#!/usr/bin/env python3
"""Offline regression checks, including every generated crawler's visible copy."""
from __future__ import annotations

import copy
import gzip
import html
import itertools
import json
import re
import sys
import tempfile
import unittest
from html.parser import HTMLParser
from pathlib import Path
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))
import ai_crawler_pages as crawlers
import facts as F
import render
import lint

NUMBER = re.compile(r'(?<![\w])[-+]?\d[\d,]*(?:\.\d+)?(?![\w])')


class Visible(HTMLParser):
    """Strip document chrome, retaining article tables, code, and visible FAQ."""

    def __init__(self, *, prose_only=False):
        super().__init__(convert_charrefs=True)
        self.parts = []
        self.stack = []
        self.prose_only = prose_only

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        hidden = (tag in {'head', 'nav', 'header', 'footer', 'script', 'style'}
                  or attributes.get('class') in {'byline', 'crumb', 'skip-link'}
                  or self.prose_only and tag in {'table', 'pre'})
        if tag not in {'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 'link', 'meta', 'param', 'source', 'track', 'wbr'}:
            self.stack.append((tag, hidden or bool(self.stack and self.stack[-1][1])))
        self.parts.append(' ')

    def handle_endtag(self, tag):
        for index in range(len(self.stack) - 1, -1, -1):
            if self.stack[index][0] == tag:
                del self.stack[index:]
                break
        self.parts.append(' ')

    def handle_data(self, data):
        if not self.stack or not self.stack[-1][1]:
            self.parts.append(data)


def visible(raw: str, *, prose_only=False) -> str:
    parser = Visible(prose_only=prose_only)
    parser.feed(raw)
    return ' '.join(''.join(parser.parts).split())


def body_prose(raw: str) -> str:
    """Visible article prose, including headings and FAQ, without the H1."""
    raw = re.sub(r'<h1\b[^>]*>.*?</h1>', ' ', raw, flags=re.S | re.I)
    return visible(raw, prose_only=True)


def sentence_starts(raw: str) -> list[str]:
    """Read prose sentences in order, skipping tables, code and site chrome."""
    raw = re.sub(r'<(head|nav|header|footer|script|style|table|pre)\b[^>]*>.*?</\1>',
                 ' ', raw, flags=re.S | re.I)
    starts = []
    for paragraph in re.findall(r'<p\b[^>]*>.*?</p>', raw, re.S | re.I):
        text = visible(paragraph, prose_only=True)
        for sentence in re.split(r'[.!?][”"’]*\s+', text):
            first = re.search(r"[\w]+(?:[’'][\w]+)?", sentence)
            if first:
                starts.append(first[0].casefold())
    return starts


def shingles(text: str) -> set[str]:
    words = re.findall(r"[a-z0-9']+", text.lower())
    return {' '.join(words[i:i + 5]) for i in range(max(0, len(words) - 4))}


def numbers(value) -> set[str]:
    """Numbers must be present in a row, including quoted names and parser versions."""
    found = set()
    if isinstance(value, dict):
        for child in value.values():
            found.update(numbers(child))
    elif isinstance(value, list):
        for child in value:
            found.update(numbers(child))
    elif not isinstance(value, bool) and value is not None:
        for match in NUMBER.findall(str(value)):
            found.add(match.replace(',', '').lstrip('+-'))
    return found


def population_hostnames(raw: str, hosts: set[str], reference_tokens: set[str]) -> set[str]:
    """Exempt exact reference spellings only in the three token positions."""
    def is_token(text):
        return html.unescape(text) in reference_tokens

    def token_position(match):
        block = match.group()
        if block.startswith('<pre>'):
            return '\n'.join('User-agent: [token]' if line.startswith('User-agent: ')
                             and is_token(line[len('User-agent: '):]) else line
                             for line in block.replace('<pre><code>', '<pre><code>\n').split('\n'))
        if block.startswith('<td>'):
            value = block[4:-5]
            link = re.fullmatch(r'<a\b[^>]*>([^<]*)</a>', value)
            if is_token(link[1] if link else value):
                return '<td>[token]</td>'
            return block
        return re.sub(r'<code>([^<]*)</code>',
                      lambda m: '<code>[token]</code>' if is_token(m[1]) else m[0], block)

    sanitized = re.sub(r'<pre><code>.*?</code></pre>|<td>.*?</td>|<p class="crawler-spellings">.*?</p>',
                       token_position, raw, flags=re.S)
    # URLs are citations and shared links. Visible copy, metadata, titles and
    # FAQ text must still pass; none of those prose fields gets an exemption.
    text = visible(sanitized)
    text += ' ' + ' '.join(html.unescape(m) for m in re.findall(r'<meta\b[^>]*content="([^"]*)"', raw))
    text += ' ' + ' '.join(html.unescape(m) for m in re.findall(r'<title>(.*?)</title>', raw, re.S))
    for value in re.findall(r'<script type="application/ld\+json">(.*?)</script>', raw, re.S):
        block = json.loads(value)
        if block.get('@type') == 'FAQPage':
            text += ' ' + ' '.join(item['name'] + ' ' + item['acceptedAnswer']['text']
                                   for item in block['mainEntity'])
    found = re.findall(r'(?<![\w.-])(?:[a-z0-9-]+\.)+[a-z]{2,}(?![\w.-])', text.lower())
    return set(found) & hosts


class CrawlerPageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.scratch = tempfile.TemporaryDirectory(prefix='ai-crawler-pages-')
        cls.root = Path(cls.scratch.name)
        with patch.object(render, 'SITE', cls.root):
            cls.paths = crawlers.build_all()
        cls.data = F.ai_crawler_pages()
        cls.rows = {row['slug']: row for row in cls.data['rows'] if row['publish']}
        cls.raw = {path.parent.name: path.read_text() for path in cls.paths if path.parent != cls.root / 'ai-crawlers'}
        cls.copy = {slug: visible(raw) for slug, raw in cls.raw.items()}
        cls.index = (cls.root / 'ai-crawlers' / 'index.html').read_text()
        with gzip.open(crawlers.ROOT / 'data' / 'ai-directives-survey-2026-10.json.gz', 'rt') as handle:
            cls.survey = json.load(handle)
        cls.hosts = {record['host'].lower() for record in cls.survey['records']}
        with gzip.open(crawlers.ROOT / 'data' / 'ai-robots-txt-reference-2026-10.json.gz', 'rt') as handle:
            cls.reference_tokens = set(json.load(handle))

    @classmethod
    def tearDownClass(cls):
        cls.scratch.cleanup()

    def test_ordinals(self):
        expected = {1: '1st', 2: '2nd', 3: '3rd', 4: '4th', 10: '10th',
                    11: '11th', 12: '12th', 13: '13th', 20: '20th',
                    21: '21st', 22: '22nd', 23: '23rd', 24: '24th',
                    101: '101st', 111: '111th', 112: '112th', 113: '113th',
                    121: '121st', 122: '122nd', 123: '123rd'}
        for value, ordinal in expected.items():
            with self.subTest(value=value):
                self.assertEqual(crawlers._ordinal(value), ordinal)

    def test_rank_wording(self):
        for row in self.data['rows']:
            position = row['naming_position']
            rank = '' if position == 1 else crawlers._ordinal(position) + ' '
            self.assertIn(f"It's the {rank}most-named crawler of the {row['eligible_count']} we counted",
                          visible(crawlers._context(row, self.data['rows'])))
        self.assertFalse(any("It's the 1st most-named" in raw for raw in self.raw.values()))

    def test_index_phone_summary_preserves_desktop_columns(self):
        self.assertIn('@media (max-width: 639px)', self.index)
        self.assertIn('.crawler-index thead, .crawler-index table.cmp td:nth-child(n+3) { display: none; }', self.index)
        self.assertIn('.crawler-index .crawler-counts { display: none; }', self.index)
        self.assertIn('.crawler-index .crawler-counts { display: inline; flex-shrink: 0; }', self.index)
        table = re.search(r'<div class="crawler-index">(.*?)</table>', self.index, re.S)[1]
        rows = re.findall(r'<tr>(.*?)</tr>', table, re.S)[1:]
        self.assertEqual(len(rows), len(self.data['rows']))
        for row, raw in zip(self.data['rows'], rows):
            cells = re.findall(r'<td>(.*?)</td>', raw, re.S)
            self.assertEqual(len(cells), 5)
            self.assertEqual(visible(cells[0]), row['token'])
            self.assertIn(f'href="{crawlers._url(row)}"', cells[0])
            summary = (f"{row['operator']} · named by {row['overall']['named']:,} "
                       f"({row['overall']['named_pct']:.1f}%) · blocked by {row['overall']['blocked']:,} "
                       f"({row['overall']['blocked_pct']:.1f}%)")
            self.assertEqual(visible(cells[1]), summary)
            self.assertEqual(visible(cells[2]), row['function'])
            self.assertEqual(visible(cells[3]), f"{row['overall']['named']:,}")
            self.assertEqual(visible(cells[4]), f"{row['overall']['blocked']:,}")

    def test_data_is_deterministic_and_only_aggregates(self):
        self.assertEqual(crawlers.derive_data(), self.data)
        self.assertEqual(json.loads(crawlers.OUTPUT.read_text()), self.data)
        self.assertEqual(len(self.rows) + 1, len(self.paths))
        self.assertEqual(len(self.rows), len(self.raw))
        self.assertEqual(self.data['method']['readable'], sum(r['state'] == 'ok' for r in self.survey['records']))
        for row in self.data['rows']:
            self.assertNotIn('host', row)
            self.assertGreaterEqual(row['overall']['named'], self.data['method']['minimum_named'])
            self.assertEqual(row['publish'], row['overall']['named'] >= self.data['method']['minimum_named'] and not row['existing_page'])
            if row['existing_page']:
                self.assertNotIn(row['slug'], self.raw)

    def test_aliases_merge_and_deduplicate_sites(self):
        rows = {crawlers.token_key(row['token']): row for row in self.data['rows']}
        for aliases in [('meta-externalagent', 'Meta-ExternalAgent'), ('Brightbot', 'Brightbot 1.0'),
                        ('iaskspider', 'iaskspider/2.0'), ('MistralAI-User', 'MistralAI-User/1.0'),
                        ('Terra Cotta', 'TerraCotta'), ('panscient.com', 'Panscient'),
                        ('quillbot.com', 'QuillBot'), ('webzio-extended', 'Webzio-Extended')]:
            with self.subTest(aliases=aliases):
                row = rows[crawlers.token_key(aliases[0])]
                self.assertTrue(set(aliases) <= set(row['spellings']))
                records = [r for r in self.survey['records'] if r['state'] == 'ok']
                expected = sum(any(crawlers.token_key(t) == crawlers.token_key(aliases[0])
                                   for t in record['ua_tokens']) for record in records)
                self.assertEqual(expected, row['overall']['named'])
        records = [dict(ua_tokens=['example', 'EXAMPLE/1.0'], access={'Example': False}, ext_blocked_by_name=[])]
        self.assertEqual(crawlers._counts(records, 'example', ['Example'])['named'], 1)
        self.assertEqual(crawlers._counts(records, 'example', ['Example'])['blocked'], 1)
        self.assertEqual(crawlers._counts(records, 'example', [])['blocked'], 0)
        records[0]['ua_tokens'] = ['*']
        self.assertEqual(crawlers._counts(records, 'example', ['Example'])['named'], 0)
        self.assertEqual(crawlers._counts(records, 'example', ['Example'])['blocked'], 1)
        records[0]['ext_blocked_by_name'] = ['Example', 'EXAMPLE/1.0']
        self.assertEqual(crawlers._counts(records, 'example', [])['blocked'], 1)

    def test_counts_shares_cloudflare_and_available_changes(self):
        records = [r for r in self.survey['records'] if r['state'] == 'ok']
        saved = json.loads((crawlers.ROOT / 'data' / 'ai-crawler-blocking-2026-10.json').read_text())
        cloudflare = {crawlers.token_key(t) for t in self.survey['method']['cloudflare_agents']}
        for row in self.data['rows']:
            key = crawlers.token_key(row['token'])
            self.assertEqual(row['cloudflare_managed'], key in cloudflare)
            for band, sample in [('overall', records),
                                 ('top', [r for r in records if r['rank'] <= self.data['method']['top_limit']])]:
                named = sum(any(crawlers.token_key(t) == key for t in r['ua_tokens']) for r in sample)
                if row['probe_tokens']:
                    blocked = sum(any(r['access'][t] is False for t in row['probe_tokens']) for r in sample)
                else:
                    blocked = sum(any(crawlers.token_key(t) == key for t in r['ext_blocked_by_name']) for r in sample)
                with self.subTest(token=row['token'], band=band):
                    self.assertEqual(row[band]['readable'], len(sample))
                    self.assertEqual(row[band]['named'], named)
                    self.assertEqual(row[band]['blocked'], blocked)
                    self.assertEqual(row[band]['named_pct'], round(100 * named / len(sample), 1))
                    self.assertEqual(row[band]['blocked_pct'], round(100 * blocked / len(sample), 1))
            if row['change']:
                metric = 'bot:' + row['probe_tokens'][0]
                for field, expected in saved['change'].get(metric, {}).items():
                    self.assertEqual(row['change'][field], expected)
                self.assertEqual(row['change']['shares']['oct'], row['overall']['blocked'])
                self.assertEqual(row['change']['net'], row['change']['gained'] - row['change']['lost'])

    def test_august_reproduces_every_published_bot_change_exactly(self):
        with gzip.open(crawlers.ROOT / 'data' / 'ai-directives-survey-2026-08.json.gz', 'rt') as handle:
            august = json.load(handle)
        saved = json.loads((crawlers.ROOT / 'data' / 'ai-crawler-blocking-2026-10.json').read_text())
        changes = crawlers._probe_changes(august, self.survey, self.survey['probe_bots'])
        for metric, expected in saved['change'].items():
            if not metric.startswith('bot:'):
                continue
            with self.subTest(metric=metric):
                got = changes[metric]
                self.assertEqual({field: got[field] for field in expected}, expected)
                self.assertEqual(got['shares'], saved['shares'][metric])
                self.assertEqual(got['panel'], saved['panel']['n'])
                self.assertEqual(got['aug_readable'], saved['aug']['readable'])
        self.assertTrue(crawlers._published_changes_match(changes, saved))
        before_308 = {h['host']: h['was'] for run in self.survey['reread'] if run['kind'] == '308'
                      for h in run['hosts']}
        self.assertTrue(before_308)
        original = {**self.survey, 'records': [before_308.get(r['host'], r) for r in self.survey['records']]}
        self.assertFalse(crawlers._published_changes_match(
            crawlers._probe_changes(august, original, self.survey['probe_bots']), saved))
        print('August reproduction: every published bot change and share matches exactly')

    def test_missing_changes_use_the_same_panel_and_block_definition(self):
        with gzip.open(crawlers.ROOT / 'data' / 'ai-directives-survey-2026-08.json.gz', 'rt') as handle:
            august = json.load(handle)
        aug = {r['host']: r for r in august['records'] if r['state'] == 'ok'}
        oct_ = {r['host']: r for r in self.survey['records'] if r['state'] == 'ok'}
        panel = aug.keys() & oct_.keys()
        saved = json.loads((crawlers.ROOT / 'data' / 'ai-crawler-blocking-2026-10.json').read_text())
        filled = []
        for row in self.rows.values():
            if not row['probe_tokens'] or 'bot:' + row['probe_tokens'][0] in saved['change']:
                continue
            filled.append(row['token'])
            bot = row['probe_tokens'][0]
            a = {h for h, r in aug.items() if r['access'][bot] is False}
            o = {h for h, r in oct_.items() if r['access'][bot] is False}
            change = row['change']
            self.assertEqual(change['panel'], len(panel))
            self.assertEqual(change['gained'], len((o - a) & panel))
            self.assertEqual(change['lost'], len((a - o) & panel))
            self.assertEqual(change['both'], len(a & o & panel))
            self.assertEqual(change['neither'], len(panel - (a | o)))
            self.assertEqual(change['shares']['aug'], len(a))
            self.assertEqual(change['shares']['oct'], len(o))
            self.assertIn('since August', self.copy[row['slug']])
        self.assertEqual(len(filled), 26)
        self.assertTrue(self.data['method']['august_changes_verified'])
        print(f'New August comparisons: {len(filled)}')

    def test_any_published_mismatch_prevents_all_missing_changes(self):
        saved = json.loads((crawlers.ROOT / 'data' / 'ai-crawler-blocking-2026-10.json').read_text())
        with gzip.open(crawlers.ROOT / 'data' / 'ai-directives-survey-2026-08.json.gz', 'rt') as handle:
            august = json.load(handle)
        changes = crawlers._probe_changes(august, self.survey, self.survey['probe_bots'])
        for metric in changes.keys() & saved['change'].keys():
            for field in saved['change'][metric]:
                bad = copy.deepcopy(changes)
                bad[metric][field] += 1
                self.assertFalse(crawlers._published_changes_match(bad, saved))
            for field in saved['shares'][metric]:
                bad = copy.deepcopy(changes)
                bad[metric]['shares'][field] += 1
                self.assertFalse(crawlers._published_changes_match(bad, saved))
        with patch.object(crawlers, '_published_changes_match', return_value=False):
            fallback = crawlers.derive_data()
        for row in fallback['rows']:
            if row['probe_tokens'] and 'bot:' + row['probe_tokens'][0] not in saved['change']:
                self.assertIsNone(row['change'])
                self.assertEqual(crawlers._change(row), '')

    def test_minimum_words_and_pairwise_similarity(self):
        counts = sorted((len(visible(raw, prose_only=True).split()), slug) for slug, raw in self.raw.items())
        print(f'Crawler pages: {len(counts)}; index pages: 1')
        print('Five shortest pages:')
        for count, slug in counts[:5]:
            print(f'  {slug}: {count} words')
        for count, slug in counts:
            self.assertGreaterEqual(count, 300, f'{slug}: {count} words')
        self.assertGreaterEqual(len(visible(self.index).split()), 300)
        sets = {slug: shingles(text) for slug, text in self.copy.items()}
        sets['ai-crawlers-index'] = shingles(visible(self.index))
        # Compare each new page with the rest of the site as well as this batch.
        existing_raw = {path.relative_to(crawlers.ROOT / 'site').as_posix(): path.read_text()
                        for path in sorted((crawlers.ROOT / 'site').rglob('*.html'))
                        if 'ai-crawlers' not in path.relative_to(crawlers.ROOT / 'site').parts}
        existing = {path: shingles(visible(raw)) for path, raw in existing_raw.items()}
        lint_sets = {path: lint.shingles(lint.visible_text(raw, body_only=True))
                     for path, raw in {**self.raw, 'ai-crawlers-index': self.index, **existing_raw}.items()}
        highest_lint = (0.0, '', '')
        highest = (0.0, '', '')
        pairs = itertools.chain(itertools.combinations(sorted(sets), 2),
                                itertools.product(sorted(sets), sorted(existing)))
        for a, b in pairs:
            left, right = sets[a], sets[b] if b in sets else existing[b]
            union = left | right
            score = len(left & right) / len(union) if union else 0.0
            highest = max(highest, (score, a, b))
            lint_left, lint_right = lint_sets[a], lint_sets[b]
            smaller = min(len(lint_left), len(lint_right))
            if smaller >= 40:
                overlap = len(lint_left & lint_right) / smaller
                highest_lint = max(highest_lint, (overlap, a, b))
        print(f'Other site pages checked: {len(existing)}')
        print(f'Highest pairwise 5-word Jaccard: {highest[0]:.6f} ({highest[1]}, {highest[2]})')
        self.assertLess(highest[0], 0.5, str(highest))
        print(f'Highest lint {lint.SHINGLE_N}-word overlap: {highest_lint[0]:.6f} '
              f'({highest_lint[1]}, {highest_lint[2]})')
        self.assertLessEqual(highest_lint[0], lint.DUP_RATIO, str(highest_lint))

    def test_token_mentions_are_limited_in_visible_body_prose(self):
        for slug, row in self.rows.items():
            count = len(re.findall(r'(?<![\w])' + re.escape(row['token']) + r'(?![\w])',
                                   body_prose(self.raw[slug]), flags=re.I))
            with self.subTest(slug=slug):
                self.assertLessEqual(count, 7, f'{slug}: {count} token mentions')

    def test_visible_copy_has_no_internal_jargon(self):
        banned = [r'probe access field', r'ext_blocked_by_name', r'extended[^.!?]*\bfield',
                  r'eligible rows', r'token order breaking ties', r'saved corrections',
                  r'readable base', r'naming set', r'root block']
        for slug, raw in [*self.raw.items(), ('index', self.index)]:
            for phrase in banned:
                with self.subTest(slug=slug, phrase=phrase):
                    self.assertNotRegex(visible(raw).casefold(), phrase)

    def test_consecutive_sentences_have_different_first_words(self):
        for slug, raw in self.raw.items():
            starts = sentence_starts(raw)
            for before, after in zip(starts, starts[1:]):
                with self.subTest(slug=slug, word=before):
                    self.assertNotEqual(before, after)

    def test_robots_instructions_explain_location_and_group_precedence(self):
        for slug, raw in self.raw.items():
            with self.subTest(slug=slug):
                rules = visible(crawlers._rules(self.rows[slug]))
                self.assertIn('robots.txt', rules)
                self.assertIn('root', rules)
                self.assertIn('User-agent: *', rules)
                self.assertRegex(rules, r'takes? precedence|gives .*precedence|yields|overrides|priority')
                self.assertIn('https://www.rfc-editor.org/rfc/rfc9309#section-2.2.1', raw)
                self.assertEqual(len(re.findall(r'<pre><code>.*?</code></pre>', raw, re.S)), 2)


    def test_prose_changes_with_the_recorded_role_and_blocking_rate(self):
        by_token = {r['token']: r for r in self.data['rows']}
        examples = [by_token[t] for t in ['GPTBot', 'ChatGPT-User', 'Bytespider', 'AgentDataBot']]
        self.assertEqual(len({crawlers._opening(row) for row in examples}), len(examples))
        self.assertEqual(crawlers._role(by_token['GPTBot']), 'training')
        self.assertEqual(crawlers._role(by_token['ChatGPT-User']), 'user')
        self.assertEqual(crawlers._role(by_token['Bytespider']), 'ignores')
        # Exercise the majority branch without claiming the survey has such a row.
        majority = dict(by_token['GPTBot'])
        majority['overall'] = dict(majority['overall'])
        majority['overall']['blocked'] = majority['overall']['readable']
        majority['overall']['blocked_pct'] = 100.0
        self.assertIn('Most readable files block', crawlers._opening(majority))
        self.assertIn('a majority', crawlers._measurement(majority))
        self.assertIn('Few readable files block', crawlers._opening(by_token['AgentDataBot']))

    def test_siblings_use_explicit_operators_and_link_existing_articles(self):
        for row in self.rows.values():
            if not row['operator_group']:
                continue
            siblings = [other for other in self.data['rows']
                        if other['operator_group'] == row['operator_group'] and other is not row
                        and (other['publish'] or other['existing_page'])]
            for sibling in siblings:
                self.assertIn('href="' + crawlers._url(sibling) + '"', self.raw[row['slug']])
        by_token = {r['token']: r for r in self.data['rows']}
        self.assertEqual(by_token['MistralAI-User']['operator_group'], by_token['MistralAI-Index']['operator_group'])
        self.assertEqual(by_token['Amazonbot']['operator_group'], by_token['Amzn-User']['operator_group'])
        for token in ['ClaudeBot', 'Claude-SearchBot', 'Claude-User']:
            row = by_token[token]
            self.assertTrue((crawlers.ROOT / 'site' / row['existing_page'].strip('/') / 'index.html').is_file())

    def test_no_population_hostnames_in_published_copy(self):
        failures = []
        for path in self.paths:
            for host in population_hostnames(path.read_text(), self.hosts, self.reference_tokens):
                failures.append((path.parent.name, host))
        self.assertEqual([], failures)
        exempted = sorted(t for t in self.reference_tokens if t.lower() in self.hosts)
        print('Reference-token hostname exemptions: ' + ', '.join(exempted))

    def test_hostname_exemptions_are_exact_and_only_in_token_positions(self):
        # Exercise every reference spelling shaped like a hostname, even when
        # the current survey does not include that host (such as panscient.com).
        tokens = {t for t in self.reference_tokens if re.fullmatch(r'(?:[\w-]+\.)+[a-z]{2,}', t, re.I)}
        self.assertIn('quillbot.com', tokens)
        self.assertIn('panscient.com', tokens)
        hosts = self.hosts | {t.lower() for t in tokens}
        for token in tokens:
            escaped = html.escape(token)
            approved = [f'<table><tr><td>{escaped}</td></tr></table>',
                        f'<p class="crawler-spellings">Use <code>{escaped}</code>.</p>',
                        f'<pre><code>User-agent: {escaped}\nDisallow: /</code></pre>']
            forbidden = [f'<p>{escaped} blocks this crawler.</p>',
                         f'<p class="crawler-spellings">{escaped} blocks this crawler.</p>',
                         f'<table><tr><td>{escaped} blocks this crawler.</td></tr></table>',
                         f'<pre><code>{escaped} blocks this crawler.</code></pre>',
                         f'<meta name="description" content="{escaped} blocks this crawler.">',
                         f'<title>{escaped} blocks this crawler</title>']
            faq = {'@type': 'FAQPage', 'mainEntity': [
                {'name': 'Who blocks it?', 'acceptedAnswer': {'text': token + ' blocks it.'}}]}
            forbidden.append('<script type="application/ld+json">' + json.dumps(faq) + '</script>')
            for raw in approved:
                self.assertEqual(population_hostnames(raw, hosts, self.reference_tokens), set(), raw)
            for raw in forbidden:
                self.assertIn(token.lower(), population_hostnames(raw, hosts, self.reference_tokens), raw)
        # Even a token-shaped table cell needs an exact reference key.
        self.assertIn('example.com', population_hostnames('<td>example.com</td>', {'example.com'}, self.reference_tokens))

    def test_titles_use_the_first_form_that_fits_lint(self):
        counts = dict.fromkeys('abcd', 0)
        for slug, row in self.rows.items():
            token = row['token']
            forms = [f'{token}: who runs it and how many sites block it',
                     f'{token}: who runs it and who blocks it',
                     f'{token} crawler: operator and block rate',
                     f'{token}: AI crawler facts']
            title = html.unescape(re.search(r'<title>(.*?)</title>', self.raw[slug], re.S)[1].strip())
            chosen = next(i for i, form in enumerate(forms) if len(form) <= 60)
            self.assertEqual(title, forms[chosen])
            self.assertLessEqual(len(title), 60)
            self.assertNotIn(row['method']['month'], title)
            lede = re.search(r'<p class="lede">(.*?)</p>', self.raw[slug], re.S)[1]
            self.assertIn(row['method']['month'], lede)
            counts['abcd'[chosen]] += 1
        # Exercise all fallbacks, including lengths not in today's reference.
        for length in range(1, 43):
            token = 'x' * length
            self.assertLessEqual(len(crawlers._title(token)), 60)
        print('Title forms: ' + ', '.join(f'{form}={count}' for form, count in counts.items()))

    def test_every_authored_number_is_in_its_row(self):
        for slug, row in self.rows.items():
            # The standard product CTA is shared chrome backed by its own facts.
            text = visible(self.raw[slug])
            unknown = numbers(text) - numbers(row)
            self.assertEqual(set(), unknown, f'{slug}: numbers absent from row JSON')
        index = (self.root / 'ai-crawlers' / 'index.html').read_text()
        self.assertEqual(set(), numbers(visible(index)) - numbers(self.data))

    def test_required_content_and_schema(self):
        index = (self.root / 'ai-crawlers' / 'index.html').read_text()
        self.assertEqual(index.count('data-crawler-sort="'), 5)
        for slug, row in self.rows.items():
            raw = self.raw[slug]
            text = visible(raw)
            self.assertNotRegex(text, '[\u2013\u2014]')
            all_visible = re.sub(r'<(head|script|style)\b[^>]*>.*?</\1>', ' ', raw, flags=re.S | re.I)
            all_visible = html.unescape(re.sub(r'<[^>]+>', ' ', all_visible))
            self.assertNotRegex(all_visible, '[\u2013\u2014]')
            self.assertIn('id="try"', raw)
            next_step = '<footer aria-label="Next step">' + render.with_next_step('', 'ai-crawlers-' + slug)
            next_step = next_step.replace('&ndash;', '-').replace('&mdash;', ', ')
            next_step = next_step.replace('\u2013', '-').replace('\u2014', ', ')
            next_step = render.nofollow_hub_links(render.brand_html(next_step))
            self.assertTrue(next_step in raw, f'{slug}: standard next step differs')
            self.assertIn('<h1>' + html.escape(row['token']) + '</h1>', raw)
            self.assertIn('<title>' + html.escape(crawlers._title(row['token'])) + '</title>', raw)
            self.assertIn('href="/ai-crawlers/"', raw)
            self.assertIn('href="/learn/ai-crawler-directives/"', raw)
            self.assertIn('href="' + crawlers.REFERENCE + '"', raw)
            for spelling in row['spellings']:
                self.assertIn('User-agent: ' + html.escape(spelling), raw)
            self.assertIn('Disallow: /', raw)
            self.assertIn('Allow: /', raw)
            blocks = [json.loads(value) for value in re.findall(r'<script type="application/ld\+json">(.*?)</script>', raw, re.S)]
            faq = next(block for block in blocks if block.get('@type') == 'FAQPage')
            self.assertEqual(len(faq['mainEntity']), 3)
            for item in faq['mainEntity']:
                self.assertIn(item['name'], text)
                self.assertIn(item['acceptedAnswer']['text'], text)
        for row in self.data['rows']:
            if row['publish'] or row['existing_page']:
                self.assertIn('href="' + crawlers._url(row) + '"', index)


if __name__ == '__main__':
    unittest.main(verbosity=2)
