#!/usr/bin/env python3
"""Offline core-update regression checks, with base/current scratch builds."""
from __future__ import annotations

from html import unescape
from pathlib import Path
import re
import sys
import tempfile
from urllib.parse import urlsplit

from test_measured_answers import Visible
from test_real_questions_1120 import (
    check_page as check_question_page, prose, schemas, shingles, similarity,
    without_price_helpers,
)
from test_thank_you_review_ask import environment, protected_state, run, scratch_copy

ROOT = Path(__file__).resolve().parent.parent
BASE = '7e0194f5559db5279452285c6b98e7e4d8ad26c6'
PAGE = 'how-to/traffic-drop-after-november-2026-core-update/index.html'
URL = '/' + PAGE.removesuffix('index.html')
HUB = 'how-to/index.html'
RESEARCH = Path('/Users/matthewkerr/ops/research/articles/data-2026-11-20')
FACTS = RESEARCH / 'google-core-update/FACTS.md'
AUDIT = RESEARCH / 'core-update-audit/AUDIT.md'
DASHBOARD = 'https://status.search.google.com/'
GUIDANCE = 'https://developers.google.com/search/docs/appearance/core-updates'
SPEC = {
    'words': ('traffic', 'november', 'core', 'update'),
    'figures': {'10', '20', '2026', '2'}, 'prices': set(),
    'sources': (DASHBOARD, GUIDANCE),
}
CHECKS = {
    'index.broken', 'index.broken_internal_links', 'index.noindex',
    'index.robots_blocks_all', 'ai.crawler_access', 'ai.edge_access',
    'index.redirects', 'index.internal_link_to_redirect',
    'index.canonical', 'index.canonical_conflict',
    'index.duplicate_content', 'index.duplicate_titles',
    'index.sitemap', 'index.sitemap_missing',
    'security.https', 'security.mixed_content', 'security.mixed_content_passive',
    'perf.cls_risk',
}


def unstamp(raw):
    # The global build id changes when the new page is added. Every other byte
    # must match the base build, including existing price copy and dates.
    return re.sub(r'(<meta name="build-id" content=")[^"]+(">)', r'\1BUILD\2', raw)


def private_identifiers(audit):
    rules = next(line for line in audit.splitlines() if line.startswith('RULES:'))
    host = urlsplit(re.search(r'https?://[^\s)]+', rules).group()).hostname
    assert host, 'audit RULES line must name the private domain'
    host = host.removeprefix('www.')
    # The site's domain label is private too. Do not print it on a failure.
    # 20 Nov 2026 (Article Studio review): also the audited site's owner and his handle.
    return {host, host.split('.')[0], 'jekyllrb', 'mckenzie', 'patio11'}


def check_anonymity(site, identifiers):
    for path in site.rglob('*'):
        if path.is_file():
            raw = path.read_bytes().lower()
            assert all(word.encode() not in raw for word in identifiers), \
                'private audit identifier or unused audit leaked into built site'


def check_page(raw, audit):
    answer, questions = check_question_page(raw, SPEC)
    text = prose(raw)
    assert 'By Matthew Kerr' in text
    assert '10 November 2026' in text and '20 November 2026' in text
    assert 'still rolling out' in answer
    assert re.search(r'<q>broad in nature, and don\'t target specific sites or individual web pages</q>'
                     r'.*?href="' + re.escape(GUIDANCE) + '"', raw, re.S), 'Google scope quote missing'
    assert 'no end date' in text and 'Rankings can keep moving until Google posts the end.' in text
    assert 'A drop that started before 10 November 2026 is probably something else' in text
    headings = re.findall(r'<h2>(.*?)</h2>', raw, re.S)
    assert headings[:6] == [
        'Check the dates first', 'Rule out the technical causes',
        'What we found on a real site', 'What Check Engine cannot tell you',
        'Choose the next check', 'Common questions',
    ], 'section order changed'
    # All cited Google sections, including the first answer, have one dated note.
    for section in re.split(r'<h2\b[^>]*>.*?</h2>', raw.split('<article>', 1)[1], flags=re.S):
        if 'rel="nofollow noopener"' in section and 'faq-item' not in section:
            assert section.count('<p class="verified-note">') == 1, 'expected one source note per section'
            assert "Checked on Google's own pages on 20 November 2026." in section
            assert 'this product' not in Visible(section).text().lower()
    checklist = raw.split('<h2>Rule out the technical causes</h2>', 1)[1].split('<h2>', 1)[0]
    assert CHECKS <= set(re.findall(r'<code>(.*?)</code>', checklist)), 'check mapping missing'
    assert 'These are not what a core update measures.' in text
    assert 'a public software consulting blog' in text and 'read 593 pages' in text
    assert '1.3.164, build 1669' in text and '128 seconds' in text
    assert '65.5 of 100 on Check Engine\'s own scale, not a Google score.' in text
    expected_scores = re.findall(r'^- (.+?): ([\d.]+) ; findings:', audit, re.M)
    rows = re.findall(r'<tr><th scope="row">(.*?)</th><td>(.*?)</td></tr>', raw, re.S)
    assert len(rows) == len(expected_scores) == 13, 'area score missing'
    for (label, score), (expected_label, expected_score) in zip(rows, expected_scores):
        assert Visible(label).text().split(':')[0] == expected_label
        assert score == expected_score, 'audit area score differs from supplied record'
    speed = next(label for label, _ in rows if label.startswith('Speed'))
    assert 'static estimate only, no Core Web Vitals result' in speed, 'speed score must be a static estimate only'
    assert 'PageSpeed Insights did not run, so Core Web Vitals are not in this score.' in text
    for block in re.findall(r'<(?:p|li|th)\b[^>]*>.*?</(?:p|li|th)>', raw, re.S):
        words = Visible(block).text()
        if 'Core Web Vitals' in words:
            assert ('static estimate' in words or 'not a measured Core Web Vitals result' in words), \
                'Core Web Vitals result claimed'
        if '11 pages' in words and 'layout shift' in words:
            assert 'static estimate' in words, 'layout-shift risk must be a static estimate'
    for finding in (
        '7 pages linked from your own site do not exist',
        '589 pages have no meta description', '34 pages load images over http',
        '11 pages are at high risk of layout shift',
    ):
        assert finding in text, 'audit finding missing'
    assert 'The Local business findings do not apply to this site.' in text, 'local caveat missing'
    assert 'detector treated a software blog as a local business' in text
    assert 'Local business SEO: does not apply to this site' in text
    assert 'Other findings have nothing to do with a core update:' in text
    assert 'no structured data on 593 pages, no contact form, brand and social findings' in text
    assert 'content-quality checks are surface signals only' in text
    assert 'They do not judge helpful, reliable, people-first content' in text
    assert 'Check Engine cannot tell you why Google ranked you lower.' in text
    assert "No tool can establish the reason for one site's drop." in text
    assert not re.search(
        r'\bbecause (?:of )?(?:the|this) update\b'
        r'|\b(?:the|this) update (?:penalis\w*|penaliz\w*|caused|cut|reduced|hurt|hit)\b'
        r'|\b(?:traffic|rankings?|clicks) (?:fell|dropped|declined) (?:due to|from) (?:the|this) update\b',
        text, re.I), 'specific drop cause claimed'
    assert raw.count('href="/tools/seo-checker/"') == 1, 'free checker must be linked once'
    editorial = Visible(without_price_helpers(raw.split('<article>', 1)[1])).text()
    assert not re.search(r'Black Friday|November price|\d+% off|[$£€]\d', editorial, re.I), \
        'sale copy outside shared helpers'
    assert not re.search(r'[\u2013\u2014]|\([^)]*\)', editorial), 'dash or parenthesis in authored copy'
    assert not re.search(r'\b\d{2}:\d{2}|\bUTC\b', text), 'machine time in visible copy'
    return answer, questions


def rejected(raw, audit, original, replacement, reason):
    head, body = raw.split('<article>', 1)
    assert original in body, 'negative control did not land'
    try:
        check_page(head + '<article>' + body.replace(original, replacement, 1), audit)
    except AssertionError as error:
        assert reason in str(error), f'control failed for wrong reason: {error}'
        print(f'CONTROL rejected: {reason}', flush=True)
    else:
        raise AssertionError(f'control accepted: {reason}')


def main():
    before = protected_state()
    facts, audit = FACTS.read_text(), AUDIT.read_text()
    assert '2026-11-10T18:06:00' in facts and 'end: none' in facts
    assert 'up to 2 weeks' in facts and "don't target specific sites" in facts
    identifiers = private_identifiers(audit)
    with tempfile.TemporaryDirectory(prefix='test-core-update-1120-') as temporary:
        destination = Path(temporary)
        scratch_copy(destination)
        env = environment(destination)
        git_dir = run(ROOT, ['git', 'rev-parse', '--absolute-git-dir'], env, quiet=True).strip()
        (destination / '.git').write_text(f'gitdir: {git_dir}\n')
        generator = destination / 'scripts/build.py'
        current = generator.read_bytes()
        generator.write_text(run(ROOT, ['git', 'show', BASE + ':scripts/build.py'], env, quiet=True))
        site = destination / 'site'
        (site / PAGE).unlink(missing_ok=True)
        run(destination, [sys.executable, '-B', 'scripts/build.py'], env)
        old = {p.relative_to(site).as_posix(): p.read_text() for p in site.rglob('*.html')}
        assets = {p.relative_to(site).as_posix(): p.read_bytes() for p in site.rglob('*')
                  if p.is_file() and p.suffix != '.html'
                  and p.name not in {'sitemap.xml', '_redirect-map.json'}}
        generator.write_bytes(current)
        run(destination, [sys.executable, '-B', 'scripts/build.py'], env)
        new = {p.relative_to(site).as_posix(): p.read_text() for p in site.rglob('*.html')}
        assert new.keys() - old.keys() == {PAGE}, 'unexpected page inventory'
        assert old.keys() <= new.keys(), 'old page removed'
        for name in old:
            if name != HUB:
                assert unstamp(new[name]) == unstamp(old[name]), f'unrelated page changed: {name}'
        for name, data in assets.items():
            assert (site / name).read_bytes() == data, f'unrelated asset changed: {name}'
        assert f'href="{URL}"' in new[HUB], 'hub link missing'
        assert f'<loc>https://checkengineseo.com{URL}</loc>' in (site / 'sitemap.xml').read_text()
        check_anonymity(site, identifiers)
        raw = new[PAGE]
        answer, questions = check_page(raw, audit)
        all_questions = {}
        for name, page in new.items():
            for faq in schemas(page, 'FAQPage'):
                for question in faq['mainEntity']:
                    all_questions.setdefault(question['name'].casefold(), []).append(name)
        for question in questions:
            assert all_questions[question.casefold()] == [PAGE], 'FAQ reused elsewhere'
        current_shingles = shingles(prose(raw))
        pairs = sorted(((similarity(current_shingles, shingles(prose(page))), name)
                        for name, page in new.items() if name != PAGE), reverse=True)
        assert pairs[0][0] < 0.5, f'page similarity too high: {pairs[0]}'
        # The shared strip must be the helper output after normal brand rendering.
        import brand
        from render import buy_strip, nofollow_hub_links
        strip = re.search(r'<aside class="buy-strip">.*?</aside>', raw, re.S)
        expected_strip = nofollow_hub_links(brand.html(buy_strip(('how-to-' + PAGE.split('/')[1])[:60])))
        assert strip and strip.group() == expected_strip, \
            'sale line differs from shared helper'
        rejected(raw, audit, 'may take up to 2 weeks',
                 'may take up to 987 weeks', 'unsourced answer figure')
        rejected(raw, audit, "Checked on Google's own pages on 20 November 2026.",
                 'Checked recently.', 'missing dated source block')
        rejected(raw, audit, 'static estimate only, no Core Web Vitals result',
                 'measured Core Web Vitals result', 'static estimate only')
        rejected(raw, audit, 'The Local business findings do not apply to this site.',
                 'The Local business findings are faults on this site.', 'local caveat missing')
        rejected(raw, audit, 'Keep a record of technical',
                 'Traffic fell because the update penalised this site. Keep a record of technical',
                 'specific drop cause claimed')
        rejected(raw, audit, 'Use the full app below',
                 'Black Friday sale is on. Use the full app below', 'sale copy outside shared helpers')
        (site / 'privacy-control.txt').write_text(next(iter(identifiers)))
        try:
            check_anonymity(site, identifiers)
        except AssertionError:
            print('CONTROL rejected: private identifier in built site', flush=True)
        else:
            raise AssertionError('private identifier control accepted')
        (site / 'privacy-control.txt').unlink()
        title = unescape(re.search(r'<title>(.*?)</title>', raw).group(1))
        print(f'PAGE {URL} | {title} | {len(prose(raw).split())} words | '
              f'max Jaccard {pairs[0][0]:.4f} with {pairs[0][1]}', flush=True)
        print('ANSWER ' + answer, flush=True)
        run(destination, [sys.executable, '-B', 'scripts/verify_structured_data_matches_page.py'], env)
        # The reviewer regenerates the saved link graph under data/. Its old
        # page count cannot validate an addition before that regeneration.
    assert protected_state() == before, 'protected source files changed'
    print('CORE UPDATE 1120 ok: scratch builds, dated sources, anonymous audit, caveats, '
          'FAQ, similarity, controls and unchanged other pages; protected source tree unchanged')


if __name__ == '__main__':
    main()
