#!/usr/bin/env python3
"""Offline lang mismatch checks on a scratch build of the current tree.

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
from test_real_questions_1120 import article_html, prose, schemas, shingles, similarity
from test_thank_you_review_ask import environment, protected_state, run, scratch_copy

ROOT = Path(__file__).resolve().parent.parent
PAGE = 'how-to/fix-lang-attribute-mismatch/index.html'
QUESTION = "Does a lang mismatch hurt rankings?"
MODIFIED = '2026-11-21'
KEPT_H2 = [
    'The four mismatches',
    'Which one you have, in one minute',
    'Getting the codes right',
    'Does the mismatch hurt you in search?',
    'Why the wrong attribute gets changed',
    'What Check Engine checks here, and what it does not',
    'After you change it',
]
CRAWL_H2 = 'What a real crawl caught'
# Release-independent: the download links carry a version, so they are checked by prefix below.
KEPT_HREF_PREFIXES = [
    'https://kerr-affiliate-hub.kerrco.workers.dev/dl/docket?src=how-to-fix-lang-attribute-mismatch-try-free&to=',
    'https://kerr-affiliate-hub.kerrco.workers.dev/dl/docket?src=how-to-fix-lang-attribute-mismatch-try-free-intel&to=',
]
KEPT_HREFS = {
    '/',
    '/assets/docket-sample-report.pdf',
    '/how-to/',
    '/how-to/fix-hreflang-return-tags/',
    '/how-to/javascript-seo-audit/',
    '/learn/seo-audit/',
    '/learn/site-monitoring/',
    '/learn/what-docket-checks/',
    'https://developers.google.com/search/docs/specialty/international/localized-versions',
    'https://example.com/de-de/schuhe',
    'https://example.com/en-gb/shoes',
    'https://kerr-affiliate-hub.kerrco.workers.dev/buy/docket?src=how-to-fix-lang-attribute-mismatch',
}
KEPT_FAQ = [
    'What is an hreflang and html lang mismatch?',
    'Which should I fix first, lang or hreflang?',
    'Is en-UK valid?',
    'Do the lang attribute and hreflang have to match exactly?',
    'Does Check Engine detect a mismatch between hreflang and the lang attribute?',
]


def title(raw):
    return unescape(re.search(r'<title>(.*?)</title>', raw).group(1))


def hrefs(raw):
    return {unescape(href) for href in re.findall(r'href="([^"]*)"', raw)}


def section(body, heading):
    return body.split(f'<h2>{heading}</h2>', 1)[1].split('<h2>', 1)[0]


def check_page(raw):
    assert len(title(raw)) <= 60 and 'hreflang and html lang mismatch' in title(raw).casefold(), 'title intent'
    assert not re.search(r'\d', title(raw)), 'digit in title'
    assert not re.search('[\u2013\u2014]', raw), 'dash in page'
    description = unescape(re.search(r'<meta name="description" content="([^"]*)"', raw).group(1))
    assert len(description) < 155, 'description too long'
    body = article_html(raw)
    headings = [Visible(h).text() for h in re.findall(r'<h2>(.*?)</h2>', body, re.S)]
    missing = set(KEPT_H2 + [CRAWL_H2]) - set(headings)
    assert not missing, f'content heading removed: {sorted(missing)}'
    assert headings.index(CRAWL_H2) == headings.index(KEPT_H2[1]) + 1, 'crawl section placement'
    missing_links = KEPT_HREFS - hrefs(body)
    assert not missing_links, f'original href removed: {sorted(missing_links)}'
    for prefix in KEPT_HREF_PREFIXES:
        assert any(h.startswith(prefix) for h in hrefs(body)), f'download link removed: {prefix}'
    first = body.split('</h1>', 1)[1].split('<h2>', 1)[0]
    first = re.sub(r'<p class="byline">.*?</p>', '', first, flags=re.S)
    answer = Visible(first).text()
    assert 0 < len(answer.split()) <= 60, 'answer word count'
    for phrase in ('several faults', 'different language from its text', 'Fix that first',
                   "hreflang self-reference use the same language code as its lang attribute"):
        assert phrase in answer, f'direct answer missing: {phrase}'
    assert re.fullmatch(r'\s*<p class="lede">.*?</p>\s*', first, re.S), 'answer must follow byline'
    crawl_html = section(body, CRAWL_H2)
    tables = re.findall(r'<div class="wrap-tbl"><table\b[^>]*>(.*?)</table></div>', crawl_html, re.S)
    assert len(tables) == 1, 'expected one wrapped crawl table'
    table = tables[0]
    assert re.findall(r'<th>(.*?)</th>', table) == [
        'Fault', 'Example', 'Reported by Check Engine', 'How to fix it'], 'table columns'
    rows = re.search(r'<tbody>(.*?)</tbody>', table, re.S)
    rows = re.findall(r'<tr>.*?</tr>', rows.group(1), re.S) if rows else []
    assert len(rows) == 5, 'table row count'
    for row, facts in zip(rows, (
        ('lang="en"', 'Spanish', 'lang="fr"', 'German', 'Both pages',
         'not in the language they declare', 'medium severity'),
        ('No lang attribute', 'does not declare a language', 'low severity'),
        ('lang="fr"', 'de', 'Not reported', 'audit did not flag it on this test', 'Crawl the hreflang set'),
        ('lang="en-UK"', 'Not reported', 'en-GB', 'GB, not UK'),
        ('Short German text with few common words', 'Not reported', 'Read the text'),
    )):
        text = Visible(row).text()
        for fact in facts:
            assert fact in text, f'crawl row fact missing: {fact}'
    crawl = Visible(crawl_html).text()
    assert not re.search(r'\d', crawl), 'digit in crawl section'
    for fact in ('small local test site', "ran Check Engine's audit", 'under a minute',
                 'stays silent when it is unsure rather than guess'):
        assert fact in crawl, f'crawl fact missing: {fact}'
    faqs = schemas(raw, 'FAQPage')
    assert len(faqs) == 1, 'FAQ schema missing'
    expected = [(Visible(q['name']).text(), Visible(q['acceptedAnswer']['text']).text())
                for q in faqs[0]['mainEntity']]
    visible = re.findall(r'<div class="faq-item"><h3>(.*?)</h3><p>(.*?)</p></div>', raw, re.S)
    assert [(Visible(q).text(), Visible(a).text()) for q, a in visible] == expected, 'FAQ schema differs'
    assert [q for q, _ in expected] == KEPT_FAQ + [QUESTION], 'FAQ questions changed'
    assert all(question in prose(raw) for question in KEPT_FAQ + [QUESTION]), 'FAQ not visible'
    for fact in ('ignores the lang attribute', 'reads the text instead', 'hreflang sets',
                 'screen readers', 'Fix it anyway'):
        assert fact in dict(expected)[QUESTION], f'FAQ fact missing: {fact}'
    assert schemas(raw, 'Article')[0]['dateModified'] == MODIFIED, 'schema modified date'
    assert f'Updated <time datetime="{MODIFIED}">' in raw, 'visible modified date'
    assert not re.search(r'\b(?:Codex|gate|job file|Article Studio)\b', prose(raw)), 'internal copy'
    return answer


def main():
    before = protected_state()
    with tempfile.TemporaryDirectory(prefix='test-lang-mismatch-1121-') as temporary:
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
            (raw.replace('several faults', 'several \u2013 faults', 1), 'dash in page'),
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
        print(f'PAGE /how-to/fix-lang-attribute-mismatch/ | title: {title(raw)} | '
              f'visible words {len(prose(raw).split())} | max Jaccard {pairs[0][0]:.4f} with {pairs[0][1]}',
              flush=True)
        print('FIRST SCREEN ' + answer, flush=True)
    assert protected_state() == before, 'protected source files changed'
    print('LANG MISMATCH UPGRADE 1121 ok: answer, headings, links, tables, crawl facts, FAQ, '
          'modified date, similarity and negative controls')


if __name__ == '__main__':
    main()
