#!/usr/bin/env python3
"""Offline crawler-directive checks on a disposable build, with literal expectations."""
from __future__ import annotations

from html import unescape
from pathlib import Path
import re
import sys
import tempfile

from test_measured_answers import Visible
from test_real_questions_1120 import article_html, prose, schemas, shingles, similarity, without_price_helpers
from test_thank_you_review_ask import environment, protected_state, run, scratch_copy

PAGE = 'learn/crawler-directives/index.html'
DATE = '2026-11-21'
HEADINGS = [
    'The three kinds, side by side',
    'When two directives collide',
    'What a real crawl caught',
    'How to check your own site',
]
QUESTIONS = [
    'If I block a page in robots.txt and add noindex, which wins?',
    'Is nofollow a crawler directive?',
    'Do AI crawlers follow the same directives?',
]


def title(raw):
    return unescape(re.search(r'<title>(.*?)</title>', raw).group(1))


def section(body, heading):
    return body.split(f'<h2>{heading}</h2>', 1)[1].split('<h2>', 1)[0]


def unstamped(raw):
    return re.sub(r'(<meta name="build-id" content=")[^"]+(">)', r'\1BUILD\2', raw)


def check_page(raw):
    assert len(title(raw)) <= 60 and 'Crawler directives' in title(raw), 'title intent'
    assert not re.search('[\u2013\u2014]', raw), 'dash in page'
    description = unescape(re.search(r'<meta name="description" content="([^"]*)"', raw).group(1))
    assert len(description) < 155, 'description too long'
    body = article_html(raw)
    headings = [Visible(h).text() for h in re.findall(r'<h2>(.*?)</h2>', body, re.S)]
    assert headings[:4] == HEADINGS, 'content heading missing or out of order'
    first = body.split('</h1>', 1)[1].split('<h2>', 1)[0]
    first = re.sub(r'<p class="byline">.*?</p>', '', first, flags=re.S)
    answer = Visible(first).text()
    assert 0 < len(answer.split()) <= 60, 'answer word count'
    assert re.fullmatch(r'\s*<p class="lede">.*?</p>\s*', first, re.S), 'answer placement'
    assert all(word in answer for word in ('robots.txt', 'meta robots', 'X-Robots-Tag', 'never sees')), 'answer facts'
    tables = re.findall(r'<div class="wrap-tbl"><table\b[^>]*>(.*?)</table></div>', body, re.S)
    assert len(tables) == 2, 'expected two wrapped tables'
    for table, columns, count in zip(tables, [
        ['Directive', 'Where it lives', 'What it controls', 'What it cannot do'],
        ['Setup', 'What Check Engine reported'],
    ], [3, 6]):
        assert re.findall(r'<th>(.*?)</th>', table) == columns, 'table columns'
        rows = re.search(r'<tbody>(.*?)</tbody>', table, re.S)
        assert rows and len(re.findall(r'<tr>.*?</tr>', rows.group(1), re.S)) == count, 'table row count'
    crawl = Visible(section(body, HEADINGS[2])).text()
    assert not re.search(r'\d', crawl), 'digit in crawl section'
    for fact in ('Two pages disallowed', 'never fetched', 'never reported', 'could not see',
                 'Two pages with noindex', 'high severity', 'One noindex page', 'low severity',
                 'anthropic-ai', 'Claude-Web', 'medium severity', 'nofollow', 'No finding',
                 'X-Robots-Tag', 'Not tested', 'could not send headers'):
        assert fact in crawl, f'crawl fact missing: {fact}'
    faqs = schemas(raw, 'FAQPage')
    assert len(faqs) == 1, 'FAQ schema missing'
    expected = [(Visible(q['name']).text(), Visible(q['acceptedAnswer']['text']).text())
                for q in faqs[0]['mainEntity']]
    visible = re.findall(r'<div class="faq-item"><h3>(.*?)</h3><p>(.*?)</p></div>', raw, re.S)
    assert [(Visible(q).text(), Visible(a).text()) for q, a in visible] == expected, 'FAQ schema differs'
    assert [q for q, _ in expected] == QUESTIONS, 'FAQ questions changed'
    article = schemas(raw, 'Article')[0]
    assert article['datePublished'] == DATE and article['dateModified'] == DATE, 'article dates'
    assert len(prose(raw).split()) >= 900, 'visible word count'
    assert not re.search(r'\b(?:Codex|gate|job|Article Studio)\b', prose(raw)), 'internal copy'
    # The shared CTA is the only authored-body exception to internal links and figures.
    editorial = without_price_helpers(body)
    editorial = re.sub(r'<p class="byline">.*?</p>', '', editorial, flags=re.S)
    assert not re.search(r'\d', Visible(editorial).text()), 'digit in editorial copy'
    assert all(h.startswith('/') for h in re.findall(r'href="([^"]*)"', editorial)), 'external editorial link'
    return answer


def main():
    before = protected_state()
    with tempfile.TemporaryDirectory(prefix='test-crawler-directives-1121-') as temporary:
        destination = Path(temporary)
        scratch_copy(destination)
        site = destination / 'site'
        old = {p.relative_to(site).as_posix(): unstamped(p.read_text()) for p in site.rglob('*.html')}
        run(destination, [sys.executable, '-B', 'scripts/build.py'], environment(destination))
        pages = {p.relative_to(site).as_posix(): p.read_text() for p in site.rglob('*.html')}
        assert PAGE in pages, 'page missing'
        assert '<loc>https://checkengineseo.com/learn/crawler-directives/</loc>' in (site / 'sitemap.xml').read_text(), 'sitemap entry missing'
        raw = pages[PAGE]
        answer = check_page(raw)
        assert 'href="/learn/crawler-directives/"' in pages['learn/what-is-robots-txt/index.html'], 'inbound link missing'
        for question in QUESTIONS:
            matches = [name for name, page in pages.items() for faq in schemas(page, 'FAQPage')
                       for item in faq['mainEntity'] if item['name'].casefold() == question.casefold()]
            assert matches == [PAGE], f'FAQ reused elsewhere: {question}'
            assert [name for name, page in pages.items() if question in Visible(page).text()] == [PAGE], 'visible question reused'
        current = shingles(prose(raw))
        pairs = sorted(((similarity(current, shingles(prose(page))), name)
                        for name, page in pages.items() if name != PAGE), reverse=True)
        assert pairs[0][0] < 0.5, f'page similarity too high: {pairs[0]}'
        for broken, reason in (
            (raw.replace('They control fetching', 'They control \u2013 fetching', 1), 'dash in page'),
            (raw.replace(f'<h2>{HEADINGS[0]}</h2>', '', 1), 'content heading'),
        ):
            assert broken != raw, 'negative control did not land'
            try:
                check_page(broken)
            except AssertionError as error:
                assert str(error).startswith(reason), f'control failed for wrong reason: {error}'
                print(f'CONTROL rejected: {error}', flush=True)
            else:
                raise AssertionError(f'control accepted: {reason}')
        changed = sorted(name for name, page in pages.items()
                         if name != PAGE and old.get(name) != unstamped(page))
        print('OTHER BUILT PAGES CHANGED versus copied output: ' + ', '.join(changed), flush=True)
        print(f'PAGE /learn/crawler-directives/ | title: {title(raw)} | '
              f'visible words {len(prose(raw).split())} | max Jaccard {pairs[0][0]:.4f} with {pairs[0][1]}', flush=True)
        print('FIRST SCREEN ' + answer, flush=True)
    assert protected_state() == before, 'protected source files changed'
    print('CRAWLER DIRECTIVES 1121 ok: answer, headings, tables, crawl facts, FAQ, dates, sitemap, '
          'inbound link, words, similarity and negative controls')


if __name__ == '__main__':
    main()
