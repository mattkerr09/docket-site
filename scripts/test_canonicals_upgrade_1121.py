#!/usr/bin/env python3
"""Offline canonical checks on a scratch build of the current tree.

Headings, links and questions are literals read from the pre-upgrade build.
No historical generator is needed, so the checks still work after merging.
"""
from __future__ import annotations

from html import unescape
from pathlib import Path
import re
import sys
import tempfile

from test_measured_answers import Visible
from test_real_questions_1120 import article_html, prose, schemas, shingles, similarity, without_price_helpers
from test_thank_you_review_ask import environment, protected_state, run, scratch_copy

ROOT = Path(__file__).resolve().parent.parent
PAGE = 'how-to/fix-conflicting-canonicals/index.html'
QUESTION = "How do I find canonical tag issues on my site?"
MODIFIED = '2026-11-21'
KEPT_H2 = [
    'Two canonicals on one page',
    'The canonical points at a noindex page',
    'The canonical points at another site',
    'No canonical at all',
    'The canonical points somewhere unexpected',
    'Why a crawler finds these and a page check does not',
    'Common questions',
]
CRAWL_H2 = 'What a real crawl caught'
# Release-independent: download links are checked by prefix below.
KEPT_HREF_PREFIXES = [
    'https://kerr-affiliate-hub.kerrco.workers.dev/dl/docket?src=how-to-fix-conflicting-canonicals-try-free&to=',
    'https://kerr-affiliate-hub.kerrco.workers.dev/dl/docket?src=how-to-fix-conflicting-canonicals-try-free-intel&to=',
]
KEPT_HREFS = {
    '/',
    '/assets/docket-sample-report.pdf',
    '/how-to/',
    '/how-to/fix-lang-attribute-mismatch/',
    '/learn/canonical-tags/',
    'https://kerr-affiliate-hub.kerrco.workers.dev/buy/docket?src=how-to-fix-conflicting-canonicals',
}
KEPT_FAQ = [
    'What happens if a page has two canonical tags?',
    'Can a canonical tag point to a noindex page?',
    'Should every page canonicalise to itself?',
    'Is a cross-domain canonical ever correct?',
]


def title(raw):
    return unescape(re.search(r'<title>(.*?)</title>', raw).group(1))


def hrefs(raw):
    return {unescape(href) for href in re.findall(r'href="([^"]*)"', raw)}


def section(body, heading):
    return body.split(f'<h2>{heading}</h2>', 1)[1].split('<h2>', 1)[0]


def check_page(raw):
    assert len(title(raw)) <= 60 and 'canonical' in title(raw).casefold(), 'title intent'
    assert not re.search(r'\d', title(raw)), 'digit in title'
    assert not re.search('[\u2013\u2014]', raw), 'dash in page'
    description = unescape(re.search(r'<meta name="description" content="([^"]*)"', raw).group(1))
    assert len(description) < 155, 'description too long'
    body = article_html(raw)
    headings = [Visible(h).text() for h in re.findall(r'<h2>(.*?)</h2>', body, re.S)]
    missing = set(KEPT_H2 + [CRAWL_H2]) - set(headings)
    assert not missing, f'content heading removed: {sorted(missing)}'
    assert headings.index(CRAWL_H2) == headings.index(KEPT_H2[-2]) + 1, 'crawl section placement'
    missing_links = KEPT_HREFS - hrefs(body)
    assert not missing_links, f'original href removed: {sorted(missing_links)}'
    for prefix in KEPT_HREF_PREFIXES:
        assert any(h.startswith(prefix) for h in hrefs(body)), f'download link removed: {prefix}'
    first = body.split('</h1>', 1)[1].split('<h2>', 1)[0]
    first = re.sub(r'<p class="byline">.*?</p>', '', first, flags=re.S)
    answer = Visible(first).text()
    assert 0 < len(answer.split()) <= 60, 'answer word count'
    for fact in ('one of four', 'two canonicals on one page', 'a canonical to a noindex page',
                 'a canonical to another domain', 'none at all', 'mixed or wrong signal',
                 'one canonical', 'indexable URL on your own site'):
        assert fact in answer, f'direct answer missing: {fact}'
    assert re.fullmatch(r'\s*<p class="lede">.*?</p>\s*', first, re.S), 'answer must follow byline'
    tables = re.findall(r'<div class="wrap-tbl"><table\b[^>]*>(.*?)</table></div>', body, re.S)
    assert len(tables) == 1, 'expected one wrapped table'
    table = re.search(r'<div class="wrap-tbl"><table\b[^>]*>(.*?)</table></div>',
                      section(body, CRAWL_H2), re.S)
    assert table, 'crawl table missing'
    assert re.findall(r'<th>(.*?)</th>', table.group(1)) == [
        'Issue', 'Example', 'What Check Engine reported', 'How to fix it'], 'table columns'
    rows = re.search(r'<tbody>(.*?)</tbody>', table.group(1), re.S)
    assert rows, 'table body missing'
    cells = [re.findall(r'<td>(.*?)</td>', row, re.S)
             for row in re.findall(r'<tr>(.*?)</tr>', rows.group(1), re.S)]
    assert len(cells) == 5 and all(len(row) == 4 for row in cells), 'table row count'
    assert [Visible(row[2]).text() for row in cells] == [
        'declares more than one canonical URL; high severity',
        'canonicalises to a noindex page; high severity',
        'canonicalises to a different domain; critical severity',
        'has no canonical tag; medium severity',
        'No finding',
    ], 'crawl findings or severity changed'
    assert 'Correct self-referencing canonical' in cells[-1][0], 'control must be last'
    # The unchanged shared buy strip follows the authored section and carries prices.
    crawl = Visible(without_price_helpers(section(body, CRAWL_H2))).text()
    assert not re.search(r'\d', crawl), 'digit in crawl section'
    assert 'small local test site' in crawl and "Check Engine's audit" in crawl, 'crawl context'
    faqs = schemas(raw, 'FAQPage')
    assert len(faqs) == 1, 'FAQ schema missing'
    expected = [(Visible(q['name']).text(), Visible(q['acceptedAnswer']['text']).text())
                for q in faqs[0]['mainEntity']]
    visible = re.findall(r'<div class="faq-item"><h3>(.*?)</h3><p>(.*?)</p></div>', raw, re.S)
    assert [(Visible(q).text(), Visible(a).text()) for q, a in visible] == expected, 'FAQ schema differs'
    assert [q for q, _ in expected] == KEPT_FAQ + [QUESTION], 'FAQ questions changed'
    assert all(question in prose(raw) for question in KEPT_FAQ + [QUESTION]), 'FAQ not visible'
    for fact in ('two canonicals', 'noindex page', 'another domain', 'self-canonical alone'):
        assert fact in dict(expected)[QUESTION], f'FAQ fact missing: {fact}'
    assert schemas(raw, 'Article')[0]['dateModified'] == MODIFIED, 'schema modified date'
    assert f'Updated <time datetime="{MODIFIED}">' in raw, 'visible modified date'
    assert not re.search(r'\b(?:Codex|gate|job|Article Studio)\b', prose(raw)), 'internal copy'
    return answer


def main():
    before = protected_state()
    with tempfile.TemporaryDirectory(prefix='test-canonicals-1121-') as temporary:
        destination = Path(temporary)
        scratch_copy(destination)
        run(destination, [sys.executable, '-B', 'scripts/build.py'], environment(destination))
        site = destination / 'site'
        pages = {p.relative_to(site).as_posix(): p.read_text() for p in site.rglob('*.html')}
        raw = pages[PAGE]
        answer = check_page(raw)
        matches = [name for name, page in pages.items() for faq in schemas(page, 'FAQPage')
                   for question in faq['mainEntity'] if question['name'].casefold() == QUESTION.casefold()]
        assert matches == [PAGE], 'new FAQ reused elsewhere'
        visible_matches = [name for name, page in pages.items() if QUESTION in Visible(page).text()]
        assert visible_matches == [PAGE], 'new question visible elsewhere'
        current = shingles(prose(raw))
        pairs = sorted(((similarity(current, shingles(prose(page))), name)
                        for name, page in pages.items() if name != PAGE), reverse=True)
        assert pairs[0][0] < 0.5, f'page similarity too high: {pairs[0]}'
        for broken, reason in (
            (raw.replace('Most canonical tag issues', 'Most canonical \u2013 tag issues', 1), 'dash in page'),
            (raw.replace(f'<h2>{KEPT_H2[0]}</h2>', '', 1), 'content heading removed'),
        ):
            assert broken != raw, 'negative control did not land'
            try:
                check_page(broken)
            except AssertionError as error:
                assert str(error).startswith(reason), f'control failed for wrong reason: {error}'
                print(f'CONTROL rejected: {error}', flush=True)
            else:
                raise AssertionError(f'control accepted: {reason}')
        print(f'PAGE /how-to/fix-conflicting-canonicals/ | title: {title(raw)} | '
              f'visible words {len(prose(raw).split())} | max Jaccard {pairs[0][0]:.4f} with {pairs[0][1]}',
              flush=True)
        print('FIRST SCREEN ' + answer, flush=True)
    assert protected_state() == before, 'protected source files changed'
    print('CANONICALS UPGRADE 1121 ok: answer, headings, links, tables, crawl facts, FAQ, '
          'modified date, similarity and negative controls')


if __name__ == '__main__':
    main()
