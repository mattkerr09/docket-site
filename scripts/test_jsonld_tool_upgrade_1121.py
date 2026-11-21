#!/usr/bin/env python3
"""Offline JSON-LD tool checks on a scratch build of the current tree.

Headings, links, tables and questions are literals from the pre-upgrade build.
No historical generator or git calls are needed after merging.
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
PAGE = 'tools/json-ld-checker/index.html'
QUESTION = 'Why does one comma break my whole JSON-LD block?'
MODIFIED = '2026-11-21'
EXAMPLE_H2 = 'What a broken block looks like'
KEPT_H2 = [
    'What it checks',
    'Which properties each type needs',
    'What it does not check',
    'Related',
    'Common questions',
]
KEPT_HREFS = {
    '/', '/tools/', '/download/', '/assets/docket-sample-report.pdf',
    '/tools/website-checker/', '/how-to/json-ld-parser-errors/',
    '/tools/meta-tag-checker/', '/tools/robots-txt-tester/',
    'https://chromewebstore.google.com/detail/docket-seo-check-for-this/pbmopklklnjhoefinjmjhhemjmefcppm?utm_source=docketseo&utm_medium=tools',
    'https://kerr-affiliate-hub.kerrco.workers.dev/buy/docket?src=tools-jsonld-checker',
}
# Release-independent: download destinations include the current version.
KEPT_HREF_PREFIXES = [
    'https://kerr-affiliate-hub.kerrco.workers.dev/dl/docket?src=tools-jsonld-checker-try-free&to=',
    'https://kerr-affiliate-hub.kerrco.workers.dev/dl/docket?src=tools-jsonld-checker-try-free-intel&to=',
    'https://kerr-affiliate-hub.kerrco.workers.dev/dl/docket?src=tools-jsonld-checker-mac&to=',
    'https://kerr-affiliate-hub.kerrco.workers.dev/dl/docket?src=tools-jsonld-checker-win&to=',
]
KEPT_FAQ = [
    'How do I test my structured data?',
    'Why is my structured data not showing in Google?',
    'Does this check Microdata or RDFa?',
]
KEPT_PROPERTIES = [
    ('Product', 'name, image'),
    ('Offer', 'price, priceCurrency'),
    ('Recipe', 'name, image, recipeIngredient, recipeInstructions'),
    ('Event', 'name, startDate, location'),
    ('JobPosting', 'title, datePosted, hiringOrganization, jobLocation'),
    ('FAQPage', 'mainEntity'),
    ('HowTo', 'name, step'),
    ('Article', 'headline'),
    ('BlogPosting', 'headline'),
    ('LocalBusiness', 'name, address'),
    ('Organization', 'name'),
    ('Review', 'reviewRating, author'),
    ('BreadcrumbList', 'itemListElement'),
    ('VideoObject', 'name, thumbnailUrl, uploadDate'),
    ('SoftwareApplication', 'name, applicationCategory'),
]


def title(raw):
    return unescape(re.search(r'<title>(.*?)</title>', raw).group(1))


def hrefs(raw):
    return {unescape(h) for h in re.findall(r'href="([^"]*)"', raw)}


def section(body, heading):
    return body.split(f'<h2>{heading}</h2>', 1)[1].split('<h2>', 1)[0]


def words(text):
    return set(re.findall(r'\w+', text.casefold()))


def check_page(raw):
    assert len(title(raw)) <= 60 and 'JSON-LD testing tool' in title(raw), 'title intent'
    assert not re.search('[\u2013\u2014]', raw), 'dash in page'
    desc = unescape(re.search(r'<meta name="description" content="([^"]*)"', raw).group(1))
    assert len(desc) < 155 and desc.startswith('Find broken JSON-LD'), 'description intent'
    body = article_html(raw)
    assert '<h1>JSON-LD structured data checker</h1>' in body, 'original h1 removed'
    headings = [Visible(h).text() for h in re.findall(r'<h2>(.*?)</h2>', body, re.S)]
    missing = set(KEPT_H2 + [EXAMPLE_H2]) - set(headings)
    assert not missing, f'content heading removed: {sorted(missing)}'
    assert headings == KEPT_H2[:3] + [EXAMPLE_H2] + KEPT_H2[3:], 'example placement'
    assert not KEPT_HREFS - hrefs(body), 'original href removed'
    for prefix in KEPT_HREF_PREFIXES:
        assert any(h.startswith(prefix) for h in hrefs(body)), f'download link removed: {prefix}'
    tables = re.findall(r'<div class="wrap-tbl"[^>]*><table\b[^>]*>(.*?)</table></div>', body, re.S)
    assert len(tables) == 3, 'expected three wrapped tables'
    assert 'id="ld-items-wrap" hidden><table class="cmp" id="ld-items"' in body, 'result table changed'
    assert re.findall(r'<th>(.*?)</th>', tables[0]) == ['Block', 'Type', 'Name', 'Missing']
    assert '<tbody></tbody>' in tables[0], 'result table must start empty'
    assert re.findall(r'<th>(.*?)</th>', tables[1]) == ['Type', 'Needs']
    rows = re.findall(r'<tr><td>(.*?)</td><td>(.*?)</td></tr>', tables[1], re.S)
    assert [(Visible(a).text(), Visible(b).text()) for a, b in rows] == KEPT_PROPERTIES, 'properties table changed'
    example = section(body, EXAMPLE_H2)
    assert tables[2] in example, 'example table placement'
    assert re.findall(r'<th>(.*?)</th>', tables[2]) == [
        'What was wrong', 'What the audit reported', 'How to fix it'], 'example columns'
    rows = re.search(r'<tbody>(.*?)</tbody>', tables[2], re.S)
    assert rows and len(re.findall(r'<tr>.*?</tr>', rows.group(1), re.S)) == 3, 'example body rows'
    text = Visible(example).text()
    assert not re.search(r'\d', text), 'digit in example'
    assert not hrefs(example), 'new external link'
    for fact in ("Check Engine's desktop audit", 'small local test site',
                 'not results from the online tool', 'trailing comma', 'JSON-LD that fails to parse',
                 'High severity', 'Expecting property name enclosed in double quotes',
                 'Product block had no image', 'incomplete Product markup', 'Medium severity',
                 'complete Article block was the control', 'No finding',
                 'Use the tool above to test the JSON-LD on your own page'):
        assert fact in text, f'example fact missing: {fact}'
    faqs = schemas(raw, 'FAQPage')
    assert len(faqs) == 1, 'FAQ schema missing'
    expected = [(Visible(q['name']).text(), Visible(q['acceptedAnswer']['text']).text())
                for q in faqs[0]['mainEntity']]
    visible = re.findall(r'<div class="faq-item"><h3>(.*?)</h3><p>(.*?)</p></div>', raw, re.S)
    assert [(Visible(q).text(), Visible(a).text()) for q, a in visible] == expected, 'FAQ schema differs'
    assert [q for q, _ in expected] == KEPT_FAQ + [QUESTION], 'FAQ questions changed'
    assert all(q in prose(raw) for q in KEPT_FAQ + [QUESTION]), 'FAQ not visible'
    for q in KEPT_FAQ:
        assert similarity(words(QUESTION), words(q)) < 0.5, f'near-copy question: {q}'
    answer = dict(expected)[QUESTION]
    assert not re.search(r'\d', answer), 'digit in FAQ'
    for fact in ('JSON does not allow a trailing comma', 'One trailing comma',
                 'whole JSON-LD block fail to parse', "Check Engine's desktop audit",
                 'Expecting property name enclosed in double quotes'):
        assert fact in answer, f'comma FAQ fact missing: {fact}'
    schema = schemas(raw, 'WebPage')[0]
    assert schema['dateModified'] == MODIFIED, 'schema modified date'
    assert schema['datePublished'] == '2026-10-06', 'published date changed'
    assert f'Updated <time datetime="{MODIFIED}">' in raw, 'visible modified date'
    assert not re.search(r'\b(?:Codex|gate|job|Article Studio)\b', prose(raw)), 'internal copy'


def normalized(raw):
    return re.sub(r'(<meta name="build-id" content=")[^"]+(">)', r'\1BUILD\2', raw)


def main():
    before = protected_state()
    with tempfile.TemporaryDirectory(prefix='test-jsonld-tool-1121-') as temporary:
        destination = Path(temporary)
        scratch_copy(destination)
        site = destination / 'site'
        old = {p.relative_to(site).as_posix(): p.read_text() for p in site.rglob('*.html')}
        run(destination, [sys.executable, '-B', 'scripts/build.py'], environment(destination))
        pages = {p.relative_to(site).as_posix(): p.read_text() for p in site.rglob('*.html')}
        raw = pages[PAGE]
        check_page(raw)
        matches = [name for name, page in pages.items() for faq in schemas(page, 'FAQPage')
                   for q in faq['mainEntity'] if q['name'].casefold() == QUESTION.casefold()]
        assert matches == [PAGE], 'new FAQ reused elsewhere'
        assert [name for name, page in pages.items() if QUESTION in Visible(page).text()] == [PAGE], \
            'new question visible elsewhere'
        current = shingles(prose(raw))
        pairs = sorted(((similarity(current, shingles(prose(page))), name)
                        for name, page in pages.items() if name != PAGE), reverse=True)
        assert pairs[0][0] < 0.5, f'page similarity too high: {pairs[0]}'
        for broken, reason in (
            (raw.replace('small local test site', 'small local \u2013 test site', 1), 'dash in page'),
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
        changed = sorted(name for name in old.keys() | pages.keys() if name != PAGE
                         and normalized(old.get(name, '')) != normalized(pages.get(name, '')))
        print('OTHER BUILT PAGES changed versus copied site, ignoring build ID: ' +
              (', '.join(changed) or 'none'), flush=True)
        print(f'PAGE /tools/json-ld-checker/ | title: {title(raw)} | '
              f'visible words {len(prose(raw).split())} | max Jaccard {pairs[0][0]:.4f} with {pairs[0][1]}',
              flush=True)
        print('FAQ max question Jaccard ' + str(max(
            (similarity(words(QUESTION), words(q)), q) for q in KEPT_FAQ)), flush=True)
    assert protected_state() == before, 'protected source files changed'
    print('JSON-LD TOOL UPGRADE 1121 ok: title, headings, links, tables, audit facts, FAQ, '
          'modified date, similarity and negative controls')


if __name__ == '__main__':
    main()
