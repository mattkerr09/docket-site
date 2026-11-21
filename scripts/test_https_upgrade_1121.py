#!/usr/bin/env python3
"""Offline HTTP to HTTPS checks on a scratch build of the current tree.

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
PAGE = 'how-to/redirect-http-to-https/index.html'
QUESTION = "Do I lose rankings when I change to HTTPS?"
MODIFIED = '2026-11-21'
KEPT_H2 = [
    'First, confirm it rather than assume it',
    'The fix, by where the site is hosted',
    'When the setting refuses: the part nobody documents',
    'HSTS is the follow-up, and it is not the same thing',
    'What Check Engine does about it',
    'Common questions',
]
OWN_H2 = 'What our own site returns'
# Seven distinct hosts or server setups in the original list, including the grouped hosts.
HOSTS = [
    'GitHub Pages', 'Netlify', 'Vercel', 'Cloudflare Pages',
    'Cloudflare in front of your own server', 'Nginx', 'Apache',
]
# Release-independent: download URLs are checked by prefix.
KEPT_HREF_PREFIXES = [
    'https://kerr-affiliate-hub.kerrco.workers.dev/dl/docket?src=how-to-redirect-http-to-https-try-free&to=',
    'https://kerr-affiliate-hub.kerrco.workers.dev/dl/docket?src=how-to-redirect-http-to-https-try-free-intel&to=',
]
KEPT_HREFS = {
    '/',
    '/assets/docket-sample-report.pdf',
    '/how-to/',
    '/how-to/fix-missing-security-headers/',
    'https://kerr-affiliate-hub.kerrco.workers.dev/buy/docket?src=how-to-redirect-http-to-https',
}
KEPT_FAQ = [
    'Does a missing HTTPS redirect actually affect ranking?',
    'Should I use a 301 or a 302?',
    "Why does 'Enforce HTTPS' refuse to turn on?",
    'Should I add HSTS at the same time?',
]


def title(raw):
    return unescape(re.search(r'<title>(.*?)</title>', raw).group(1))


def hrefs(raw):
    return {unescape(href) for href in re.findall(r'href="([^"]*)"', raw)}


def section(body, heading):
    return body.split(f'<h2>{heading}</h2>', 1)[1].split('<h2>', 1)[0]


def check_page(raw):
    assert len(title(raw)) <= 60 and 'http to https' in title(raw).casefold(), 'title intent'
    assert not re.search('[\u2013\u2014]', raw), 'dash in page'
    description = unescape(re.search(r'<meta name="description" content="([^"]*)"', raw).group(1))
    assert len(description) < 155, 'description too long'
    body = article_html(raw)
    headings = [Visible(h).text() for h in re.findall(r'<h2>(.*?)</h2>', body, re.S)]
    missing = set(KEPT_H2 + [OWN_H2]) - set(headings)
    assert not missing, f'content heading removed: {sorted(missing)}'
    assert headings.index(OWN_H2) == headings.index(KEPT_H2[0]) + 1, 'own-site section placement'
    missing_links = KEPT_HREFS - hrefs(body)
    assert not missing_links, f'original href removed: {sorted(missing_links)}'
    for prefix in KEPT_HREF_PREFIXES:
        assert any(h.startswith(prefix) for h in hrefs(body)), f'download link removed: {prefix}'
    first = body.split('</h1>', 1)[1].split('<h2>', 1)[0]
    first = re.sub(r'<p class="byline">.*?</p>', '', first, flags=re.S)
    answer = Visible(first).text()
    assert 0 < len(answer.split()) <= 60, 'answer word count'
    assert all(term in answer for term in ('certificate', 'https://', '301', 'http://', 'links', 'images')), 'direct answer missing'
    assert '<h1>How to change http:// to https://, and redirect it</h1>' in body, 'h1 intent'
    assert re.fullmatch(r'\s*<p class="lede">.*?</p>\s*', first, re.S), 'answer must follow byline'
    tables = re.findall(r'<div class="wrap-tbl"><table\b[^>]*>(.*?)</table></div>', body, re.S)
    assert len(tables) == 2, 'expected two wrapped tables'
    for heading, columns, count in (
        (KEPT_H2[1], ['Host or server', 'Where the HTTPS setting is',
                      'How the redirect is made', 'Common blocker'], 7),
        (OWN_H2, ['Request', 'Answer', 'Note'], 4),
    ):
        table = re.search(r'<div class="wrap-tbl"><table\b[^>]*>(.*?)</table></div>',
                          section(body, heading), re.S)
        assert table, f'table missing: {heading}'
        assert re.findall(r'<th>(.*?)</th>', table.group(1)) == columns, 'table columns'
        rows = re.search(r'<tbody>(.*?)</tbody>', table.group(1), re.S)
        assert rows and len(re.findall(r'<tr>.*?</tr>', rows.group(1), re.S)) == count, 'table row count'
        if heading == KEPT_H2[1]:
            assert [Visible(cell).text() for cell in re.findall(r'<tr><td>(.*?)</td>', rows.group(1), re.S)] == HOSTS, 'hosts changed'
        else:
            assert [Visible(row).text() for row in re.findall(r'<tr>(.*?)</tr>', rows.group(1), re.S)] == [
                'http://checkengineseo.com/ 301 to https://checkengineseo.com/ One hop.',
                'http://www.checkengineseo.com/ 301 straight to https://checkengineseo.com/ One hop.',
                'https://www.checkengineseo.com/ 301 to https://checkengineseo.com/ The address without www.',
                'A deep page over http:// 301 to the same path over https://, then 200 The path stays intact.',
            ], 'own-site checks changed'
    own = Visible(section(body, OWN_H2)).text()
    for fact in ('one hop, not two', 'well under a second',
                 'sent no Strict-Transport-Security header when we checked'):
        assert fact in own, f'own-site fact missing: {fact}'
    assert 'href="#hsts"' in section(body, OWN_H2) and 'id="hsts"' in body, 'HSTS link missing'
    assert 'sent no Strict-Transport-Security header when we checked' in Visible(section(body, KEPT_H2[3])).text(), 'HSTS note missing'
    assert '"The site is not served over HTTPS" at critical severity' in prose(raw), 'local audit finding missing'
    faqs = schemas(raw, 'FAQPage')
    assert len(faqs) == 1, 'FAQ schema missing'
    expected = [(Visible(q['name']).text(), Visible(q['acceptedAnswer']['text']).text())
                for q in faqs[0]['mainEntity']]
    visible = re.findall(r'<div class="faq-item"><h3>(.*?)</h3><p>(.*?)</p></div>', raw, re.S)
    assert [(Visible(q).text(), Visible(a).text()) for q, a in visible] == expected, 'FAQ schema differs'
    assert [q for q, _ in expected] == KEPT_FAQ + [QUESTION], 'FAQ questions changed'
    assert all(question in prose(raw) for question in KEPT_FAQ + [QUESTION]), 'FAQ not visible'
    assert dict(expected)[QUESTION] == (
        'Use permanent 301 redirects for every URL so each old address points to its '
        'new HTTPS address. Preserve each path rather than sending every page to the homepage.'
    ), 'FAQ redirect practice changed'
    article = schemas(raw, 'Article')[0]
    assert article['datePublished'] == '2026-08-10', 'published date changed'
    assert article['dateModified'] == MODIFIED, 'schema modified date'
    assert f'Updated <time datetime="{MODIFIED}">' in raw, 'visible modified date'
    assert not re.search(r'\b(?:Codex|gate|job|Article Studio)\b', prose(raw)), 'internal copy'
    return answer


def main():
    before = protected_state()
    with tempfile.TemporaryDirectory(prefix='test-https-upgrade-1121-') as temporary:
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
            (raw.replace('Most hosts', 'Most \u2013 hosts', 1), 'dash in page'),
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
        print(f'PAGE /how-to/redirect-http-to-https/ | title: {title(raw)} | '
              f'visible words {len(prose(raw).split())} | max Jaccard {pairs[0][0]:.4f} with {pairs[0][1]}',
              flush=True)
        print('FIRST SCREEN ' + answer, flush=True)
    assert protected_state() == before, 'protected source files changed'
    print('HTTPS UPGRADE 1121 ok: answer, headings, links, tables, own-site facts, FAQ, '
          'modified date, similarity and negative controls')


if __name__ == '__main__':
    main()
