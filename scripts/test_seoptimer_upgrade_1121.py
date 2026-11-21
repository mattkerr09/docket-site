#!/usr/bin/env python3
"""Offline SEOptimer checks, with merge-base/current scratch builds."""
from __future__ import annotations

import ast
from html import unescape
from pathlib import Path
import re
import sys
import tempfile
import xml.etree.ElementTree as ET

import brand
from articles import comparisons as C
from test_measured_answers import Visible
from test_real_questions_1120 import article_html, prose, schemas, shingles, similarity
from test_thank_you_review_ask import environment, protected_state, run, scratch_copy

ROOT = Path(__file__).resolve().parent.parent
GENERATOR = 'scripts/articles/comparisons.py'
PAGE = 'vs/seoptimer-alternative/index.html'
URL = '/vs/seoptimer-alternative/'
QUESTION = 'What is better than SEOptimer?'
MODIFIED = '2026-11-21'


def unstamp(raw):
    return re.sub(r'(<meta name="build-id" content=")[^"]+(">)', r'\1BUILD\2', raw)


def hrefs(raw):
    return {unescape(href) for href in re.findall(r'href="([^"]*)"', raw)}


def title(raw):
    return unescape(re.search(r'<title>(.*?)</title>', raw).group(1))


def check_page(raw):
    assert len(title(raw)) <= 60 and 'SEOptimer alternative' in title(raw), 'title intent'
    assert not re.search('[\u2013\u2014]', raw), 'dash in page'
    description = unescape(re.search(r'<meta name="description" content="([^"]*)"', raw).group(1))
    assert len(description) < 155, 'description too long'
    body = article_html(raw)
    lede = Visible(body.split('<h2>', 1)[0]).text()
    assert f'from ${C._SEOPT_LO} a month' in lede, 'starting price missing'
    assert C.CHECKED_HUMAN['seoptimer'] in lede, 'read date missing'
    assert 'have not been re-checked since' in lede, 'stale price note missing'
    assert 'stay with SEOptimer' in lede and brand.html('pick Docket') in lede, 'choice missing'
    alternatives = body.split('<h2>Other SEOptimer alternatives, by what you need</h2>', 1)[1]
    table = re.search(r'<div class="wrap-tbl"><table\b[^>]*>(.*?)</table></div>', alternatives, re.S)
    assert table, 'alternatives table wrapper missing'
    headers = re.findall(r'<th>(.*?)</th>', table.group(1))
    assert headers == ['Need', 'Alternative', 'What it gives you', 'Our comparison'], 'table columns'
    rows = re.findall(r'<tr>(.*?)</tr>', re.search(r'<tbody>(.*?)</tbody>', table.group(1), re.S).group(1), re.S)
    assert len(rows) == 6, 'table row count'
    for row, name, href in zip(rows,
            ('free', 'team', 'Visual reports', 'desktop crawler', 'monthly cloud', 'Unmetered re-runs'),
            ('/best/free-seo-audit-tools/', '/vs/semrush-site-audit-alternative/',
             '/vs/sitebulb-alternative/', '/vs/screaming-frog-alternative/',
             '/vs/sitechecker-alternative/', '/')):
        assert name in Visible(row).text() and href in hrefs(row), 'table option missing'
        assert not re.search(r'[$£€]\d', Visible(row).text()), 'price in alternatives table'
    faqs = schemas(raw, 'FAQPage')
    assert len(faqs) == 1, 'FAQ schema missing'
    qa = faqs[0]['mainEntity']
    visible = re.findall(r'<div class="faq-item"><h3>(.*?)</h3><p>(.*?)</p></div>', raw, re.S)
    expected = [(Visible(q['name']).text(), Visible(q['acceptedAnswer']['text']).text()) for q in qa]
    assert [(Visible(q).text(), Visible(a).text()) for q, a in visible] == expected, 'FAQ schema differs'
    answers = dict(expected)
    assert QUESTION in answers and QUESTION in Visible(raw).text(), 'new FAQ missing'
    assert 'SEOptimer stays the better pick if you need a lead generation tool' in answers[QUESTION], 'concession missing'
    cost = answers['How much does SEOptimer cost?']
    for name, monthly, _, _ in C._SEOPT_PLANS:
        assert f'{name} at ${monthly} a month' in cost, 'plan price missing'
    assert C.CHECKED_HUMAN['seoptimer'] in cost, 'FAQ read date missing'
    assert schemas(raw, 'Article')[0]['dateModified'] == MODIFIED, 'schema modified date'
    assert f'Updated <time datetime="{MODIFIED}">' in raw, 'visible modified date'
    assert not re.search(r'\b(?:Codex|gate|job|manifest|Article Studio)\b', prose(raw)), 'internal copy'
    assert not re.search(r'\b\d{4}-\d{2}-\d{2}\b|\b\d{2}:\d{2}|\bUTC\b', prose(raw)), 'machine date or time'
    return lede


def only_function_changed(original, current):
    """Keep all shared constants, helpers and other pages byte for byte."""
    def outside(source):
        tree = ast.parse(source)
        function = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'seoptimer')
        lines = source.splitlines(keepends=True)
        return ''.join(lines[:function.lineno - 1] + lines[function.end_lineno:])
    assert outside(original) == outside(current), 'source outside seoptimer changed'
    tree = ast.parse(current)
    function = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'seoptimer')
    assert not any(isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == 'price'
                   for n in ast.walk(function)), 'range helper remains in seoptimer'


def main():
    before = protected_state()
    with tempfile.TemporaryDirectory(prefix='test-seoptimer-1121-') as temporary:
        destination = Path(temporary)
        scratch_copy(destination)
        env = environment(destination)
        base = run(ROOT, ['git', 'merge-base', 'HEAD', 'origin/main'], env, quiet=True).strip()
        git_dir = run(ROOT, ['git', 'rev-parse', '--absolute-git-dir'], env, quiet=True).strip()
        (destination / '.git').write_text(f'gitdir: {git_dir}\n')
        generator = destination / GENERATOR
        current = generator.read_text()
        original = run(ROOT, ['git', 'show', base + ':' + GENERATOR], env, quiet=True)
        only_function_changed(original, current)
        generator.write_text(original)
        run(destination, [sys.executable, '-B', 'scripts/build.py'], env)
        site = destination / 'site'
        old = {p.relative_to(site).as_posix(): p.read_text() for p in site.rglob('*.html')}
        assets = {p.relative_to(site).as_posix(): p.read_bytes() for p in site.rglob('*')
                  if p.is_file() and p.suffix != '.html' and p.name not in {'sitemap.xml', 'llms.txt'}}
        old_sitemap = (site / 'sitemap.xml').read_text()
        old_llms = (site / 'llms.txt').read_text()
        generator.write_text(current)
        run(destination, [sys.executable, '-B', 'scripts/build.py'], env)
        new = {p.relative_to(site).as_posix(): p.read_text() for p in site.rglob('*.html')}
        assert old.keys() == new.keys(), 'page inventory changed'
        old_title, new_title = title(old[PAGE]), title(new[PAGE])
        changed = []
        for name in old:
            if name == PAGE:
                continue
            expected = old[name]
            if name == 'vs/index.html':
                expected = expected.replace(old_title, new_title)
            assert unstamp(new[name]) == unstamp(expected), f'unrelated page changed: {name}'
            if unstamp(old[name]) != unstamp(new[name]):
                changed.append(name)
        for name, data in assets.items():
            assert (site / name).read_bytes() == data, f'unrelated asset changed: {name}'
        old_map, new_map = ET.fromstring(old_sitemap), ET.parse(site / 'sitemap.xml').getroot()
        ns = {'s': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
        for item in old_map.findall('s:url', ns):
            if item.find('s:loc', ns).text == 'https://checkengineseo.com' + URL:
                item.find('s:lastmod', ns).text = MODIFIED
        assert ET.tostring(old_map) == ET.tostring(new_map), 'unrelated sitemap change'
        new_llms = (site / 'llms.txt').read_text()
        old_lines = [line for line in old_llms.splitlines() if URL in line]
        new_lines = [line for line in new_llms.splitlines() if URL in line]
        assert len(old_lines) == len(new_lines), 'llms inventory changed'
        expected_llms = old_llms
        for old_line, new_line in zip(old_lines, new_lines):
            assert old_line.replace(old_title, new_title) == new_line, 'unrelated inventory change'
            expected_llms = expected_llms.replace(old_line, new_line, 1)
        assert expected_llms == new_llms, 'unrelated llms inventory change'
        raw = new[PAGE]
        assert hrefs(old[PAGE]) <= hrefs(raw), f'base href removed: {hrefs(old[PAGE]) - hrefs(raw)}'
        lede = check_page(raw)
        matches = [name for name, page in new.items() for faq in schemas(page, 'FAQPage')
                   for question in faq['mainEntity'] if question['name'].casefold() == QUESTION.casefold()]
        assert matches == [PAGE], 'new FAQ reused elsewhere'
        current_shingles = shingles(prose(raw))
        pairs = sorted(((similarity(current_shingles, shingles(prose(page))), name)
                        for name, page in new.items() if name != PAGE), reverse=True)
        assert pairs[0][0] < 0.5, f'page similarity too high: {pairs[0]}'
        try:
            check_page(raw.replace('from $', 'from \u2013 $', 1))
        except AssertionError as error:
            assert str(error) == 'dash in page', f'control failed for wrong reason: {error}'
            print('CONTROL rejected: en dash put back in the lede', flush=True)
        else:
            raise AssertionError('control accepted en dash')
        print(f'PAGE {URL} | base {base} | old title: {old_title} | new title: {new_title} | '
              f'visible words {len(prose(old[PAGE]).split())} -> {len(prose(raw).split())} | '
              f'max Jaccard {pairs[0][0]:.4f} with {pairs[0][1]}', flush=True)
        print('FIRST SCREEN ' + lede, flush=True)
        print(f'OTHER CHANGED PAGES {changed}: derived comparison hub title only; '
              'sitemap.xml: target lastmod only; '
              f'llms.txt changed: {old_llms != new_llms}; build-id stamps ignored on all pages', flush=True)
        print(f'PRESERVED {len(old) - 1} other pages and all base hrefs; assets unchanged', flush=True)
    assert protected_state() == before, 'protected source files changed'
    print('SEOPTIMER UPGRADE 1121 ok: title, dated price, alternatives table, FAQ, links, '
          'modified date, similarity, negative control and unchanged other pages')


if __name__ == '__main__':
    main()
