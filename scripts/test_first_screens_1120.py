#!/usr/bin/env python3
"""Offline first-screen checks against the supplied 20 November facts."""
from __future__ import annotations

import ast
import hashlib
from html import unescape
from pathlib import Path
import re
import sys
import tempfile

import app_path
from test_measured_answers import ANSWER, NUMBER, Visible, unchanged
from test_real_questions_1120 import article_html, prose, schemas, shingles, similarity, without_price_helpers
from test_thank_you_review_ask import environment, protected_state, run, scratch_copy, unstamped

ROOT = Path(__file__).resolve().parent.parent
BASE = '6fc81c96f4d9f53f919efe26670f805ddafc5155'
READ = '20 November 2026'
# The source file stays outside the repository. These figures and source URLs
# are pinned to FACTS.md and its addendum, including the two Ahrefs counts.
PAGES = {
    'best/free-seo-audit-tools/index.html': {
        'words': ('free', 'seo', 'audit'),
        'figures': {'4', '9', '500', '5,000', '1', '10'},
        'sources': ('/vs/screaming-frog-alternative/',
                    'https://www.screamingfrog.co.uk/seo-spider/',
                    'https://ahrefs.com/webmaster-tools', 'https://www.semrush.com/prices/'),
    },
    'vs/ahrefs-site-audit-alternative/index.html': {
        'words': ('ahrefs', 'site', 'audit'),
        'figures': {'180', '5,000', '129.00', '100,000', '25,000'},
        'sources': ('https://ahrefs.com/site-audit', 'https://ahrefs.com/webmaster-tools',
                    'https://ahrefs.com/pricing', 'https://ahrefs.com/blog/content-audit/'),
    },
    'how-to/content-audit/index.html': {
        'words': ('ahrefs', 'content', 'audit'), 'figures': {'180', '5,000'},
        'sources': ('https://ahrefs.com/site-audit', 'https://ahrefs.com/webmaster-tools',
                    'https://ahrefs.com/blog/content-audit/'),
    },
}
MORNING = ('vs/contentking-vs-se-ranking/index.html', 'vs/screaming-frog-vs-semrush/index.html',
           'vs/sitebulb-vs-jetoctopus/index.html', 'how-to/test-a-page-as-googlebot/index.html',
           'how-to/check-a-page-for-noindex/index.html')
GENERATORS = ('scripts/build.py', 'scripts/articles/comparisons.py', 'scripts/articles/best_free.py',
              'scripts/articles/howto_content_audit.py', 'scripts/articles/real_questions_comparisons.py',
              'scripts/articles/real_questions_sources.py', 'scripts/articles/howto_check_noindex.py',
              'scripts/articles/howto_test_googlebot.py')
# VERIFIED_PAGES in the claims gate covers older landing pages and is outside
# this batch's allowed paths. Extend the same date/source check here, without
# editing that gate or its existing entries.
VERIFIED_PAGES = {'ahrefs': ('vs/ahrefs-site-audit-alternative/index.html', 'how-to/content-audit/index.html'),
                  'first-free': ('best/free-seo-audit-tools/index.html',)}


def check_answer(raw, spec):
    matches = list(ANSWER.finditer(raw))
    assert len(matches) == 1, 'expected one measured answer'
    match = matches[0]
    h1 = re.search(r'<h1\b[^>]*>.*?</h1>', raw, re.S)
    h2 = re.search(r'<h2\b', raw)
    assert h1 and h2 and h1.end() < match.start() < match.end() < h2.start(), 'answer placement'
    if '<p class="ownership">' in raw and 'Free SEO audit: tools and limits' in raw:
        assert READ in raw[h1.end():h2.start()], 'missing first-screen read date'
    preceding = re.sub(r'<p class="byline">.*?</p>', '', raw[h1.end():match.start()], flags=re.S)
    # 20 November comparison batch: the free page now discloses ownership
    # before its answer. Permit only that exact line and the pinned document.
    if '<p class="ownership">' in preceding and 'Free SEO audit: tools and limits' in raw:
        from test_best_compared_3 import OWNERSHIP
        preceding = preceding.replace(f'<p class="ownership">{OWNERSHIP}</p>', '', 1)
    assert not Visible(preceding).text(), 'answer must be first body prose'
    first_screen = raw[h1.end():h2.start()]
    assert not re.search(r'<p class="lede"|id="try-now"', first_screen), 'second first-screen answer'
    answer = Visible(match.group(1)).text()
    title = unescape(re.search(r'<title>(.*?)</title>', raw, re.S).group(1))
    assert len(title) <= 60, 'title too long'
    for text in (title, answer):
        assert set(spec['words']) <= set(re.findall(r'\w+', text.lower())), 'missing search words'
    assert 2 <= len(re.split(r'(?<=[.!?])\s+', answer)) <= 4, 'answer sentence count'
    assert set(NUMBER.findall(answer)) == spec['figures'], 'unsourced answer figure'
    for url in spec['sources']:
        assert f'href="{url}"' in match.group(), 'missing answer source'
    assert READ in first_screen, 'missing first-screen read date'
    return match


def check_page(raw, spec):
    match = check_answer(raw, spec)
    text = prose(raw)
    assert not re.search(r'[\u2013\u2014]', text), 'dash in visible prose'
    assert not re.search(r'\b(?:Codex|gate|job|Article Studio|old domain)\b', text), 'internal copy'
    assert not re.search(r'\b\d{4}-\d{2}-\d{2}\b|\b\S+\.(?:json|py)\b', text), 'machine copy'
    assert 'Updated <time datetime="2026-11-20">20 November 2026</time>' in raw
    assert re.search(r'"dateModified":\s*"2026-11-20"', raw)
    for section in re.split(r'<h2\b[^>]*>.*?</h2>', article_html(raw), flags=re.S):
        if '170+' in Visible(section).text():
            assert ('180+' in Visible(section).text() or
                    re.search(r'Webmaster Tools.{0,100}170\+|170\+.{0,100}Webmaster Tools', Visible(section).text())), 'unqualified Ahrefs count'
        # Every refreshed rival section carries a source and its real read date.
        if 'rel="nofollow noopener"' in section:
            dates = re.findall(r'(?:Checked|read)[^.]*?\d{1,2} [A-Z][a-z]+ 2026', Visible(section).text())
            assert dates and any(READ in date for date in dates), 'missing dated rival section'
    monthly = re.findall(r'(\$\d[\d,]*(?:\.\d+)?) a month', Visible(without_price_helpers(raw)).text())
    assert all(re.fullmatch(r'\$\d[\d,]*\.\d{2}', value) for value in monthly), 'monthly cents missing'
    for faq in schemas(raw, 'FAQPage'):
        for question in faq['mainEntity']:
            answer = question['acceptedAnswer']['text']
            if 'rel="nofollow noopener"' in answer:
                assert READ in answer, 'FAQ missing read date'
        visible = re.findall(r'<div class="faq-item"><h3>(.*?)</h3><p>(.*?)</p></div>', raw, re.S)
        assert [(Visible(q).text(), Visible(a).text()) for q, a in visible] == [
            (Visible(q['name']).text(), Visible(q['acceptedAnswer']['text']).text()) for q in faq['mainEntity']], 'FAQ schema differs'
    return match


def check_notes(raw):
    text = prose(raw)
    assert 'this product' not in text, 'generic company note'
    notes = re.findall(r'<p class="verified-note">.*?</p>', raw, re.S)
    words = [Visible(note).text() for note in notes]
    assert words and len(words) == len(set(words)), 'dated note repeated'
    for note in notes:
        assert len(re.findall(r'Checked on .*?own pages on 20 November 2026', Visible(note).text())) == 1, 'note date or company missing'
        assert re.search(r'Google|Conductor|SE Ranking|Screaming Frog|Semrush|Sitebulb|JetOctopus', Visible(note).text()), 'company missing'
    for section in re.split(r'<h2\b[^>]*>.*?</h2>', article_html(raw), flags=re.S):
        assert section.count('<p class="verified-note">') <= 1, 'more than one note in section'


def rejected(raw, spec, reason):
    try:
        check_page(raw, spec)
    except AssertionError as error:
        assert reason in str(error), f'control rejected for wrong reason: {error}'
        print(f'CONTROL rejected: {error}', flush=True)
    else:
        raise AssertionError(f'control accepted: {reason}')


def legacy_page(destination, env, name, generator, revision):
    """Replay a named historical generator without changing any other page.

    Round 1 and 2 still test their original measured additions and controls.
    This batch's replacement answer is checked separately on the actual build.
    """
    path = destination / generator
    page = destination / 'site' / name
    source, output = path.read_bytes(), page.read_bytes()
    entry = ('import comparisons; comparisons.ahrefs()' if generator.endswith('comparisons.py')
             else 'import best_free; best_free.free_seo_audit_tools()')
    try:
        path.write_text(run(ROOT, ['git', 'show', revision + ':' + generator], env, quiet=True))
        run(destination, [sys.executable, '-B', '-c',
            "import sys; sys.path[:0] = ['scripts', 'scripts/articles']; " + entry], env)
        return page.read_text()
    finally:
        path.write_bytes(source)
        page.write_bytes(output)


# 20 November 2026 first-screen batch: exact complete refreshed documents,
# excluding only the global build-id. These are not page skips. The original
# round checks still run on the historical additions via legacy_page, and the
# new answer, source, date and negative checks run on the actual output.
REFRESH_HASHES = {
    'vs/ahrefs-site-audit-alternative/index.html': '32d8ec172bad1cc1e9f2b3ad922a99512193e6c9abc5bdb73388b86f684fd12b',
    'best/free-seo-audit-tools/index.html': '6c10e9cbb0a76f5d79c50d86d46b0ec31f0d9ca1d6a36ae385bd7a96a21769f7',
}


def reviewed_refresh(name, raw):
    # 20 November comparison batch: keep the earlier hash for historical
    # controls and accept only the separately pinned free-tools comparison.
    if name == 'best/free-seo-audit-tools/index.html' and '<p class="ownership">' in raw:
        from test_best_compared_3 import reviewed_refresh as compared_refresh
        compared_refresh(name, raw)
        return check_page(raw, PAGES[name])
    assert hashlib.sha256(unstamped(raw).encode()).hexdigest() == REFRESH_HASHES[name], 'unreviewed refreshed copy: ' + name
    return check_page(raw, PAGES[name])


def reviewed_transition(site, env, name, old, new):
    # First-screen batch, 20 November 2026: the real-question replay restores
    # the old Ahrefs generator as a side effect. Permit exactly this rewrite
    # while comparing every byte of the prior document to its historical form.
    reviewed_refresh(name, new)
    legacy = legacy_page(site.parent, env, name, 'scripts/articles/comparisons.py', BASE)
    assert unchanged(legacy) == unchanged(old), 'unreviewed prior Ahrefs copy'


def main():
    before = protected_state()
    with tempfile.TemporaryDirectory(prefix='test-first-screens-1120-') as temporary:
        destination = Path(temporary)
        scratch_copy(destination)
        env = environment(destination)
        env['DOCKET_APP'] = str(app_path.find())
        git_dir = run(ROOT, ['git', 'rev-parse', '--absolute-git-dir'], env, quiet=True).strip()
        (destination / '.git').write_text(f'gitdir: {git_dir}\n')
        current = {name: (destination / name).read_bytes() for name in GENERATORS}
        for name in GENERATORS:
            (destination / name).write_text(run(ROOT, ['git', 'show', BASE + ':' + name], env, quiet=True))
        run(destination, [sys.executable, '-B', 'scripts/build.py'], env)
        site = destination / 'site'
        old = {p.relative_to(site).as_posix(): p.read_text() for p in site.rglob('*.html')}
        assets = {name: (site / name).read_bytes() for name in ('llms.txt', 'offer.json')}
        bundle = (destination / 'data/bundle.json').read_bytes()
        for name, data in current.items():
            (destination / name).write_bytes(data)
        run(destination, [sys.executable, '-B', 'scripts/build.py'], env)
        new = {p.relative_to(site).as_posix(): p.read_text() for p in site.rglob('*.html')}
        assert old.keys() == new.keys(), 'page inventory changed'
        for name, raw in new.items():
            if name not in set(PAGES) | set(MORNING):
                # Byte comparison after replacing only the global build-id.
                if name == 'best/index.html':
                    # 20 November comparison batch: exact hub rewrite only.
                    from test_best_compared_3 import legacy_page as compared_legacy, reviewed_refresh as compared_refresh
                    compared_refresh(name, raw)
                    prior = compared_legacy(destination, env, name, BASE)
                    assert unstamped(prior) == unstamped(old[name]), 'prior hub changed'
                else:
                    assert unstamped(raw) == unstamped(old[name]), f'unrelated page changed: {name}'
            assert schemas(raw, 'SoftwareApplication') == schemas(old[name], 'SoftwareApplication'), f'Offer data changed: {name}'
        for name, data in assets.items():
            assert (site / name).read_bytes() == data, f'protected asset changed: {name}'
        assert (destination / 'data/bundle.json').read_bytes() == bundle
        for name in MORNING:
            check_notes(new[name])
            assert re.search(r'"dateModified":\s*"2026-11-20"', new[name])
            # Morning changes contain only source-note text and the update date.
            strip_notes = lambda raw: re.sub(r'<p class="verified-note">.*?</p>\s*', '', raw, flags=re.S)
            assert unchanged(strip_notes(new[name])) == unchanged(strip_notes(old[name]).replace('and the\ncomputer is awake', 'and the computer is awake')), f'morning prose changed: {name}'
        exact = 'scheduled re-audits run only while the app is open and the computer is awake'
        assert exact in prose(new[MORNING[0]]) and exact in new[MORNING[0]], 'schedule limit changed'
        all_shingles = {name: shingles(prose(raw)) for name, raw in new.items()}
        for name, spec in PAGES.items():
            raw = new[name]
            match = check_page(raw, spec)
            old_published = re.search(r'Published <time[^>]*>.*?</time>', old[name]).group()
            assert old_published in raw, 'published date changed'
            pairs = sorted(((similarity(all_shingles[name], value), other)
                            for other, value in all_shingles.items() if other != name), reverse=True)
            assert pairs[0][0] < 0.5, f'page similarity too high: {pairs[0]}'
            title = unescape(re.search(r'<title>(.*?)</title>', raw).group(1))
            answer = Visible(match.group(1)).text()
            print(f'PAGE /{name.removesuffix("index.html")} | {title} | {len(prose(raw).split())} words | answer {len(answer.split())} words | max Jaccard {pairs[0][0]:.4f}', flush=True)
            print('ANSWER ' + answer, flush=True)
            rejected(raw.replace(match.group(), '', 1), spec, 'expected one measured answer')
            figure = NUMBER.search(answer).group()
            rejected(raw[:match.start()] + match.group().replace(figure, '987654.321', 1) + raw[match.end():], spec, 'unsourced answer figure')
            rejected(raw.replace('20 November 2026', '19 November 2026'), spec, 'missing first-screen read date')
            source = spec['sources'][0]
            rejected(raw.replace(f'href="{source}"', 'href="https://example.invalid/"', 1), spec, 'missing answer source')
            late = raw.replace(match.group(), '', 1).replace('</article>', match.group() + '</article>', 1)
            rejected(late, spec, 'answer placement')
        ahrefs = new['vs/ahrefs-site-audit-alternative/index.html']
        assert '5,000 crawl credits per verified project per month' in prose(ahrefs)
        assert ahrefs.count('href="/how-to/content-audit/"') == 1, 'content-audit link missing or repeated'
        for text in ('Standard $249.00 a month', 'Advanced $449.00 a month'):
            assert text in prose(ahrefs), 'paid plan price missing'
        assert 'Ahrefs does not sell one' in Visible(ANSWER.search(new['how-to/content-audit/index.html'])[1]).text()
        tree = ast.parse((destination / 'scripts/articles/comparisons.py').read_text())
        registry = next(ast.literal_eval(node.value) for node in tree.body
                        if isinstance(node, ast.AnnAssign) and node.target.id == 'VERIFIED')
        dates = {}
        for node in tree.body:
            if isinstance(node, ast.AnnAssign) and node.target.id in {'CHECKED_ISO', 'CHECKED_HUMAN'}:
                dates[node.target.id] = ast.literal_eval(node.value)
        for key, names in VERIFIED_PAGES.items():
            assert dates['CHECKED_ISO'][key] == '2026-11-20' and dates['CHECKED_HUMAN'][key] == READ
            # Not every Ahrefs fact belongs on the process page. Each refreshed
            # source must be present on the main comparison or free tools page.
            for claim, source in registry[key]:
                assert claim and all(f'href="{source}"' in new[name] for name in names), 'registry source missing'
        old_source = run(ROOT, ['git', 'show', BASE + ':scripts/articles/comparisons.py'], env, quiet=True)
        current_source = (destination / 'scripts/articles/comparisons.py').read_text()
        for function in ('source_link', '_verified_note', '_credit_rows', '_months_past_docket'):
            def code(source):
                node = next(n for n in ast.parse(source).body if isinstance(n, ast.FunctionDef) and n.name == function)
                return ast.get_source_segment(source, node)
            assert code(old_source) == code(current_source), f'shared helper changed: {function}'
        run(destination, [sys.executable, '-B', 'scripts/verify_competitive_claims.py'], env)
    assert protected_state() == before, 'protected source tree changed'
    print('FIRST SCREENS 1120 ok: answers, sourced limits, dates, notes, similarity, controls and protected pages')


if __name__ == '__main__':
    main()
