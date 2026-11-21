#!/usr/bin/env python3
"""Offline hreflang return-tag checks on a scratch build of the current tree.

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
PAGE = 'how-to/fix-hreflang-return-tags/index.html'
QUESTION = "What does 'no return tags' mean?"
MODIFIED = '2026-11-21'
KEPT_H2 = [
    'The rule, in one sentence',
    'What a complete set looks like',
    'The four ways a set breaks',
    'hreflang and canonical must agree',
    'Which code to use',
    'How to check it, and why the check has to crawl',
]
CRAWL_H2 = 'What a real crawl caught'
# Release-independent: the download links carry a version, so they are checked by prefix below.
KEPT_HREF_PREFIXES = [
    'https://kerr-affiliate-hub.kerrco.workers.dev/dl/docket?src=how-to-fix-hreflang-return-tags-try-free&to=',
    'https://kerr-affiliate-hub.kerrco.workers.dev/dl/docket?src=how-to-fix-hreflang-return-tags-try-free-intel&to=',
]
KEPT_HREFS = {
    '/',
    '/assets/docket-sample-report.pdf',
    '/how-to/',
    '/how-to/fix-conflicting-canonicals/',
    'https://example.com/de-de/schuhe',
    'https://example.com/en-gb/shoes',
    'https://example.com/shoes',
    'https://kerr-affiliate-hub.kerrco.workers.dev/buy/docket?src=how-to-fix-hreflang-return-tags',
}
KEPT_FAQ = [
    'What is an hreflang return tag?',
    'Does every page need to list itself in hreflang?',
    'Can hreflang and canonical tags conflict?',
    "Why can't I spot this by viewing the page source?",
]


def title(raw):
    return unescape(re.search(r'<title>(.*?)</title>', raw).group(1))


def hrefs(raw):
    return {unescape(href) for href in re.findall(r'href="([^"]*)"', raw)}


def section(body, heading):
    return body.split(f'<h2>{heading}</h2>', 1)[1].split('<h2>', 1)[0]


def check_page(raw):
    assert len(title(raw)) <= 60 and 'hreflang return tags' in title(raw).casefold(), 'title intent'
    assert not re.search('[\u2013\u2014]', raw), 'dash in page'
    description = unescape(re.search(r'<meta name="description" content="([^"]*)"', raw).group(1))
    assert len(description) < 155, 'description too long'
    body = article_html(raw)
    headings = [Visible(h).text() for h in re.findall(r'<h2>(.*?)</h2>', body, re.S)]
    missing = set(KEPT_H2 + [CRAWL_H2]) - set(headings)
    assert not missing, f'content heading removed: {sorted(missing)}'
    assert headings.index(CRAWL_H2) == headings.index(KEPT_H2[-1]) + 1, 'crawl section placement'
    missing_links = KEPT_HREFS - hrefs(body)
    assert not missing_links, f'original href removed: {sorted(missing_links)}'
    for prefix in KEPT_HREF_PREFIXES:
        assert any(h.startswith(prefix) for h in hrefs(body)), f'download link removed: {prefix}'
    first = body.split('</h1>', 1)[1].split('<h2>', 1)[0]
    first = re.sub(r'<p class="byline">.*?</p>', '', first, flags=re.S)
    answer = Visible(first).text()
    assert 0 < len(answer.split()) <= 60, 'answer word count'
    assert 'list' in answer.casefold() and 'back' in answer.casefold(), 'direct answer missing'
    assert re.fullmatch(r'\s*<p class="lede">.*?</p>\s*', first, re.S), 'answer must follow byline'
    tables = re.findall(r'<div class="wrap-tbl"><table\b[^>]*>(.*?)</table></div>', body, re.S)
    assert len(tables) == 2, 'expected two wrapped tables'
    for heading, columns, count in (
        ('The four ways a set breaks', ['How the set breaks', 'What it looks like', 'How to fix it'], 4),
        (CRAWL_H2, ['Page', 'What was wrong', 'What Check Engine reported'], 5),
    ):
        table = re.search(r'<div class="wrap-tbl"><table\b[^>]*>(.*?)</table></div>',
                          section(body, heading), re.S)
        assert table, f'table missing: {heading}'
        assert re.findall(r'<th>(.*?)</th>', table.group(1)) == columns, 'table columns'
        rows = re.search(r'<tbody>(.*?)</tbody>', table.group(1), re.S)
        assert rows and len(re.findall(r'<tr>.*?</tr>', rows.group(1), re.S)) == count, 'table row count'
    # The unchanged shared buy strip follows the authored section and carries prices.
    crawl = Visible(without_price_helpers(section(body, CRAWL_H2))).text()
    assert not re.search(r'\d', crawl), 'digit in crawl section'
    for fact in ('eight pages', 'seven language versions', 'English, German and French',
                 'Spanish', 'Portuguese', 'Italian', 'Dutch', 'query string',
                 'high severity', 'low severity', 'medium severity', 'few seconds',
                 'not reported as a broken hreflang pair', 'read canonical findings and hreflang findings together'):
        assert fact in crawl, f'crawl fact missing: {fact}'
    faqs = schemas(raw, 'FAQPage')
    assert len(faqs) == 1, 'FAQ schema missing'
    expected = [(Visible(q['name']).text(), Visible(q['acceptedAnswer']['text']).text())
                for q in faqs[0]['mainEntity']]
    visible = re.findall(r'<div class="faq-item"><h3>(.*?)</h3><p>(.*?)</p></div>', raw, re.S)
    assert [(Visible(q).text(), Visible(a).text()) for q, a in visible] == expected, 'FAQ schema differs'
    assert [q for q, _ in expected] == KEPT_FAQ + [QUESTION], 'FAQ questions changed'
    assert all(question in prose(raw) for question in KEPT_FAQ + [QUESTION]), 'FAQ not visible'
    for example in ('query string', 'http instead of https', 'missing trailing slash'):
        assert example in dict(expected)[QUESTION], 'FAQ URL example missing'
    assert schemas(raw, 'Article')[0]['dateModified'] == MODIFIED, 'schema modified date'
    assert f'Updated <time datetime="{MODIFIED}">' in raw, 'visible modified date'
    assert not re.search(r'\b(?:Codex|gate|job|Article Studio)\b', prose(raw)), 'internal copy'
    return answer


def main():
    before = protected_state()
    with tempfile.TemporaryDirectory(prefix='test-hreflang-return-1121-') as temporary:
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
            (raw.replace('exact same URL', 'exact same \u2013 URL', 1), 'dash in page'),
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
        print(f'PAGE /how-to/fix-hreflang-return-tags/ | title: {title(raw)} | '
              f'visible words {len(prose(raw).split())} | max Jaccard {pairs[0][0]:.4f} with {pairs[0][1]}',
              flush=True)
        print('FIRST SCREEN ' + answer, flush=True)
    assert protected_state() == before, 'protected source files changed'
    print('HREFLANG RETURN UPGRADE 1121 ok: answer, headings, links, tables, crawl facts, FAQ, '
          'modified date, similarity and negative controls')


if __name__ == '__main__':
    main()
