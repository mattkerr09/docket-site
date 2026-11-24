#!/usr/bin/env python3
"""Offline SEOmator copy checks and full base-build preservation replay."""
from __future__ import annotations

import ast
from decimal import Decimal
from html import unescape
from pathlib import Path
import re
import sys
import tempfile

import app_path
from test_measured_answers import Visible
from test_real_questions_1120 import article_html, prose, schemas, shingles, similarity
from test_thank_you_review_ask import environment, protected_state, run, scratch_copy

ROOT = Path(__file__).resolve().parent.parent
BASE = '3ac514b244a3602612f9a674e4285da2dd8c3e2b'
PAGE = 'vs/seomator-alternative/index.html'
# 24 November 2026: build.py automatically gives every /vs/ article a flat
# redirect. This is the only additional HTML output, and is checked below.
REDIRECT = 'vs-seomator-alternative/index.html'
FACTS = Path('/Users/matthewkerr/ops/research/articles/data-2026-11-24/seomator-read/FACTS.md')
READ = 'read 24 November 2026'
OWNERSHIP = ('We make Check Engine, one of the tools described here. We describe SEOmator from its own '
             'pages, read on 24 November 2026, and we earn money when you buy Check Engine.')
SOURCES = {
    'https://seomator.com/', 'https://seomator.com/pricing',
    'https://seomator.com/free-seo-audit-tool',
    'https://seomator.com/blog/seomator-open-source-seo-audit-skill-cli',
    'https://github.com/seo-skills/seo-audit-skill',
}
VERIFIED_PAGES = {'seomator': PAGE}
MONEY = re.compile(r'\$[\d,]+(?:\.\d+)?')
BANNED = re.compile(r'\b(?:independent|unbiased|neutral|honest|best|top|our pick|winner)\b|#1', re.I)


def unstamped(raw):
    # Compare every byte apart from the global content hash, which changes
    # when any page is added. No prose, prices or dates are normalized.
    return re.sub(r'(<meta name="build-id" content=")[^"]+(">)', r'\1BUILD\2', raw)


def text(raw):
    return Visible(raw).text()


def sourced(section):
    assert section.count(READ) == 1, 'one read date per SEOmator section'
    assert any(f'href="{url}"' in section for url in SOURCES), 'missing primary source'
    assert 'SEOmator' in section, 'dated section must name SEOmator'


def check_page(raw, facts):
    article = article_html(raw)
    title = unescape(re.search(r'<title>(.*?)</title>', raw, re.S).group(1))
    h1 = text(re.search(r'<h1\b[^>]*>.*?</h1>', article, re.S).group())
    assert title == h1 == 'Check Engine SEO vs SEOmator: price, limits, uses'
    assert len(title) <= 60
    # Price helpers are shared copy. Authored product prose and all headings
    # must avoid ranking words, including FAQ and VERIFIED evidence text.
    authored = re.sub(r'<section id="check-engine-price">.*?</section>', '', article, flags=re.S)
    assert not BANNED.search(text(authored)), 'banned ranking word'
    assert not re.search(r'[\u2013\u2014]', unescape(raw)), 'em or en dash'
    assert not re.search(r'\b(?:free forever|no limits|unlimited|SaaSHub)\b', text(article), re.I)
    assert not re.search(r'\b\d{4}-\d{2}-\d{2}\b', text(article)), 'ISO date in visible copy'
    ownership = f'<p class="ownership">{OWNERSHIP}</p>'
    answer = re.search(r'<p id="measured-answer">(.*?)</p>', article, re.S)
    assert answer and article.index(ownership) < answer.start() < article.index('<h2')
    sentences = re.split(r'(?<=[.!?])\s+', text(answer.group(1)))
    assert 2 <= len(sentences) <= 4
    assert all(phrase in text(answer.group()) for phrase in
               ('monthly cloud platform', '$49.00 a month', 'free, open-source audit engine',
                'one payment instead of a subscription'))
    # Each body section has one local note; each FAQ answer is its own unit.
    body = authored.split('<section class="faq"')[0]
    sections = re.split(r'<h2\b[^>]*>.*?</h2>', body, flags=re.S)
    assert len(sections) == 8, 'expected first screen and seven body sections'
    for section in sections:
        sourced(section)
    method = text(sections[1])
    for phrase in ('costs for a year', 'what is free', 'where it runs', 'how many pages',
                   'output', 'own pages and repository', 'not a test score'):
        assert phrase in method, 'comparison method: ' + phrase
    faq = schemas(raw, 'FAQPage')[0]['mainEntity']
    assert 3 <= len(faq) <= 5
    for item in faq:
        assert 'best' not in item['name'].lower()
        sourced(unescape(item['acceptedAnswer']['text']))
    dates = schemas(raw, 'Article')[0]
    assert dates['datePublished'] == dates['dateModified'] == '2026-11-24'
    assert 'Published <time datetime="2026-11-24">' in raw, 'published byline'
    ahead = re.search(r'<h2>Where SEOmator is ahead</h2>(.*?)<h2>', body, re.S).group(1)
    assert ('Check Engine does not do AI-prompt tracking, Google rank tracking, '
            'Search Console data or CMS publishing.') in text(ahead)
    for phrase in ('MIT', '398 rules', '99 checks', 'more rules', 'score gates', 'MCP server',
                   'Claude Code skill', 'Core Web Vitals', 'ChatGPT, Gemini and Google AI Mode',
                   'GitHub Action', 'CLI', 'MCP connector for Claude and ChatGPT'):
        assert phrase in text(ahead), 'missing concession or shared feature: ' + phrase
    table = re.search(r'<table class="cmp">(.*?)</table>', authored, re.S).group(1)
    rows = [re.findall(r'<t[dh]\b[^>]*>(.*?)</t[dh]>', row, re.S)
            for row in re.findall(r'<tr>(.*?)</tr>', table, re.S)]
    assert [text(cell) for cell in rows[0]] == [
        'Tool and plan', 'Price for a year', 'Where it runs', 'What it reads', 'What you get']
    assert [text(row[0]) for row in rows[1:]] == [
        'SEOmator Free web audit', 'SEOmator open-source engine', 'SEOmator Starter',
        'SEOmator Growth', 'SEOmator Scale', 'Check Engine']
    ours = rows[-1]
    assert ours[1] == 'One payment: <a href="#check-engine-price">see the price box</a>'
    assert not MONEY.search(ours[1]) and 'Default 200 pages, a setting' in text(ours[3])
    assert '<section id="check-engine-price">' in article and 'class="price-line"' in article
    amounts = {Decimal(value[1:].replace(',', '')) for value in MONEY.findall(facts)}
    prices = MONEY.findall(text(authored))
    assert set(prices) == {'$49.00', '$99.00', '$249.00', '$490.00', '$990.00', '$2,490.00'}
    assert all(Decimal(value[1:].replace(',', '')) in amounts for value in prices), 'price absent from FACTS.md'
    monthly = re.findall(r'(\$[\d,.]+) a month', text(authored))
    assert set(monthly) == {'$49.00', '$99.00', '$249.00'}
    assert all(re.fullmatch(r'\$[\d,]+\.\d{2}', value) for value in monthly), 'monthly cents missing'
    assert SOURCES <= set(re.findall(r'href="(https?://[^"]+)"', authored))
    return title, h1, text(answer.group(1)), rows


def claim_count(destination, env):
    output = run(destination, [sys.executable, '-B', '-c',
        "import sys; sys.path[:0] = ['scripts', 'scripts/articles']; import comparisons; "
        "print(sum(map(len, comparisons.VERIFIED.values())))"], env, quiet=True)
    return int(output.strip())


def main():
    before = protected_state()
    facts = FACTS.read_text()
    with tempfile.TemporaryDirectory(prefix='test-vs-seomator-') as temporary:
        destination = Path(temporary)
        scratch_copy(destination)
        # The gate builds before invoking this test. Remove only this job's
        # generated outputs from the disposable copy before replaying base;
        # build.py deliberately leaves old HTML in place.
        for name in (PAGE, REDIRECT):
            (destination / 'site' / name).unlink(missing_ok=True)
        env = environment(destination)
        env['DOCKET_APP'] = str(app_path.find())
        git_dir = run(ROOT, ['git', 'rev-parse', '--absolute-git-dir'], env, quiet=True).strip()
        (destination / '.git').write_text(f'gitdir: {git_dir}\n')
        generators = ('scripts/build.py', 'scripts/articles/comparisons.py')
        current = {name: (destination / name).read_bytes() for name in generators}
        for name in generators:
            (destination / name).write_text(run(ROOT, ['git', 'show', BASE + ':' + name], env, quiet=True))
        count_before = claim_count(destination, env)
        run(destination, [sys.executable, '-B', 'scripts/build.py'], env)
        site = destination / 'site'
        old = {p.relative_to(site).as_posix(): p.read_text() for p in site.rglob('*.html')}
        assert PAGE not in old and REDIRECT not in old, 'base already has comparison'
        for name, source in current.items():
            (destination / name).write_bytes(source)
        count_after = claim_count(destination, env)
        assert count_after > count_before, 'sourced claim count must rise'
        run(destination, [sys.executable, '-B', 'scripts/build.py'], env)
        new = {p.relative_to(site).as_posix(): p.read_text() for p in site.rglob('*.html')}
        assert new.keys() - old.keys() == {PAGE, REDIRECT}, 'unexpected new HTML'
        assert not old.keys() - new.keys(), 'existing HTML removed'
        for name, prior in old.items():
            if name != 'vs/index.html':
                assert unstamped(prior) == unstamped(new[name]), 'unrelated page changed: ' + name
        # Pin the hub to exactly one added entry, without permitting other edits.
        hub = new['vs/index.html']
        addition = re.search(r'<h2[^>]*><a href="/vs/seomator-alternative/">.*?</h2><p>.*?</p>', hub, re.S)
        assert addition and '>Check Engine SEO vs SEOmator</a>' in addition.group()
        assert unstamped(hub.replace(addition.group(), '', 1)) == unstamped(old['vs/index.html'])
        redirect = new[REDIRECT]
        assert '<meta name="robots" content="noindex,follow">' in redirect
        assert '<meta http-equiv="refresh" content="0; url=/vs/seomator-alternative/">' in redirect
        raw = new[PAGE]
        title, h1, answer, rows = check_page(raw, facts)
        for name, other in new.items():
            if name != PAGE:
                assert raw != other, 'byte-identical page: ' + name
                for question in schemas(other, 'FAQPage'):
                    assert not ({q['name'] for q in question['mainEntity']}
                                & {q['name'] for q in schemas(raw, 'FAQPage')[0]['mainEntity']}), 'FAQ reused: ' + name
        ours = shingles(prose(raw))
        pair = max((similarity(ours, shingles(prose(other))), name)
                   for name, other in new.items() if name != PAGE)
        assert pair[0] < 0.5, 'Jaccard similarity: ' + str(pair)
        # Extend VERIFIED_PAGES locally: the shared gate is outside allowed_paths.
        source = (destination / 'scripts/articles/comparisons.py').read_text()
        tree = ast.parse(source)
        verified = next(ast.literal_eval(node.value) for node in tree.body
                        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name)
                        and node.target.id == 'VERIFIED')
        note = re.search(r'<p class="verified-note">.*?</p>', raw, re.S).group()
        assert 'Checked 24 November 2026.' in text(note)
        for _, url in verified['seomator']:
            assert f'href="{url}"' in note, 'VERIFIED source missing'
        assert VERIFIED_PAGES['seomator'] == PAGE
        print('Title:', title)
        print('H1:', h1)
        print('Word count:', len(prose(raw).split()))
        print('First screen:', answer)
        for row in rows[1:]:
            print('Table row:', ' | '.join(map(text, row)))
        print(f'Max Jaccard: {pair[0]:.6f} with {pair[1]}')
        print(f'VERIFIED claims: {count_before} -> {count_after}')
        print(f'Base preservation: {len(old) - 1} existing HTML files identical except build-id; hub adds one entry')
    assert protected_state() == before, 'source site, workers or data changed'
    print('SEOMATOR ok: copy, sources, dates, prices, concessions and base-build preservation')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
