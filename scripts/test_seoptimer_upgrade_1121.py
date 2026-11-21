#!/usr/bin/env python3
"""Offline SEOptimer page checks on one scratch build of the current tree.

The links the page must keep are a literal list, read once from the page as it was before the 21 November 2026
upgrade. No git calls and no commit hash: a test that rebuilds its "original" from a merge-base compares the page with
itself once the branch is merged. Download and buy links are left out of the list because they carry the release
version.
"""
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
KEPT_HREFS = {
    '/vs/',
    '/best/free-seo-audit-tools/',
    '/learn/priority-model/',
    '/vs/crawler-sh-alternative/',
    '/vs/screaming-frog-alternative/',
    '/vs/semrush-site-audit-alternative/',
    '/vs/sitebulb-alternative/',
    '/vs/sitechecker-alternative/',
    'https://www.seoptimer.com/pricing',
}


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


def no_range_helper(source):
    """The page states SEOptimer's starting price itself; the shared range helper stays out of seoptimer()."""
    tree = ast.parse(source)
    function = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'seoptimer')
    assert not any(isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == 'price'
                   for n in ast.walk(function)), 'range helper remains in seoptimer'


def kept_links(raw):
    missing = KEPT_HREFS - hrefs(raw)
    assert not missing, f'original href removed: {sorted(missing)}'


def main():
    before = protected_state()
    no_range_helper((ROOT / GENERATOR).read_text())
    with tempfile.TemporaryDirectory(prefix='test-seoptimer-1121-') as temporary:
        destination = Path(temporary)
        scratch_copy(destination)
        env = environment(destination)
        run(destination, [sys.executable, '-B', 'scripts/build.py'], env)
        site = destination / 'site'
        new = {p.relative_to(site).as_posix(): p.read_text() for p in site.rglob('*.html')}
        raw = new[PAGE]
        kept_links(raw)
        lede = check_page(raw)
        ns = {'s': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
        sitemap = ET.parse(site / 'sitemap.xml').getroot()
        lastmod = [item.find('s:lastmod', ns).text for item in sitemap.findall('s:url', ns)
                   if item.find('s:loc', ns).text == 'https://checkengineseo.com' + URL]
        assert len(lastmod) == 1, 'page missing from sitemap'  # its date is set by data/page-lastmod-checkengine.json
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
        try:
            kept_links(raw.replace('href="/vs/sitebulb-alternative/"', 'href="#"'))
        except AssertionError as error:
            assert str(error).startswith('original href removed'), f'control failed for wrong reason: {error}'
            print('CONTROL rejected: an original link removed', flush=True)
        else:
            raise AssertionError('control accepted a removed link')
        print(f'PAGE {URL} | title: {title(raw)} | visible words {len(prose(raw).split())} | '
              f'max Jaccard {pairs[0][0]:.4f} with {pairs[0][1]}', flush=True)
        print('FIRST SCREEN ' + lede, flush=True)
    assert protected_state() == before, 'protected source files changed'
    print('SEOPTIMER UPGRADE 1121 ok: title, dated price, alternatives table, FAQ, kept links, '
          'modified date, similarity and negative controls')


if __name__ == '__main__':
    main()
