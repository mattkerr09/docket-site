#!/usr/bin/env python3
"""Offline real-question checks. Build the base and current sources in a temp copy."""
from __future__ import annotations

import ast
from html import unescape
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
from urllib.parse import urlsplit

import app_path
import test_measured_answers as round_one
import test_measured_answers_2 as round_two
import test_measured_answers_3 as round_three
from test_measured_answers import ANSWER, NUMBER, Visible
from test_thank_you_review_ask import environment, protected_state, run, scratch_copy, unstamped

ROOT = Path(__file__).resolve().parent.parent
BASE = '3f393f63b9c4de581ac24e1420b827f0bfb1a332'
# Question words, first-screen sourced figures and allowed rival prices are
# pinned to FACTS.md supplied with this task, read on 20 November 2026.
PAGES = {
    'how-to/test-a-page-as-googlebot': {
        'words': ('googlebot', 'test', 'tester'), 'figures': {'317'}, 'prices': set(),
        'sources': ('https://support.google.com/webmasters/answer/9012289',
                    'https://developers.google.com/static/crawling/ipranges/common-crawlers.json'),
        'inbound': None,
    },
    'how-to/check-a-page-for-noindex': {
        'words': ('meta', 'noindex', 'checker'), 'figures': {'2'}, 'prices': set(),
        'sources': ('https://developers.google.com/search/docs/crawling-indexing/block-indexing',),
        'inbound': None,
    },
    'vs/contentking-vs-se-ranking': {
        'words': ('contentking', 'vs', 'se', 'ranking'), 'figures': {'60', '2,000,000'},
        'prices': {'$129.00', '$103.20', '$279.00', '$223.20'},
        'sources': ('https://www.contentkingapp.com', 'https://seranking.com/website-audit.html'),
        'inbound': 'vs/se-ranking-vs-screaming-frog',
    },
    'vs/screaming-frog-vs-semrush': {
        'words': ('screaming', 'frog', 'vs', 'semrush'), 'figures': {'500', '139.00', '117.33'},
        'prices': {'$279', '£199', '$139.00', '$117.33'},
        'sources': ('https://www.screamingfrog.co.uk/seo-spider/', 'https://www.semrush.com/prices/'),
        'inbound': 'vs/se-ranking-vs-screaming-frog',
    },
    'vs/sitebulb-vs-jetoctopus': {
        'words': ('sitebulb', 'vs', 'jetoctopus'), 'figures': {'18.00', '10,000', '42.00', '500,000'},
        'prices': {'$18.00', '$42.00', '$125.00'},
        'sources': ('https://sitebulb.com/pricing/', 'https://jetoctopus.com/'),
        'inbound': 'vs/jetoctopus-alternative',
    },
}
SOURCE_GENERATORS = ('scripts/build.py', 'scripts/articles/comparisons.py', 'scripts/articles/pages.py')
CHECKED = 'Checked 20 November 2026.'


def article_html(raw):
    match = re.search(r'<article\b[^>]*>.*?</article>', raw, re.S)
    return match.group() if match else raw


def prose(raw):
    return Visible(article_html(raw)).text()


def without_price_helpers(raw):
    # These are the site's shared own-price helpers, not rival statements.
    raw = re.sub(r'<div class="buy-block\b.*?</div>.*?</div>', '', raw, flags=re.S)
    return re.sub(r'<aside class="buy-strip">.*?</aside>', '', raw, flags=re.S)


def shingles(text):
    words = re.findall(r"[\w']+", text.lower())
    return set(zip(*(words[i:] for i in range(5))))


def similarity(a, b):
    return len(a & b) / len(a | b) if a or b else 0


def schemas(raw, kind):
    return [data for block in re.findall(r'<script type="application/ld\+json">(.*?)</script>', raw, re.S)
            if (data := json.loads(block)).get('@type') == kind]


def check_answer(raw, spec):
    matches = list(ANSWER.finditer(raw))
    assert len(matches) == 1, 'expected one measured answer'
    match = matches[0]
    h1 = re.search(r'<h1\b[^>]*>(.*?)</h1>', raw, re.S)
    h2 = re.search(r'<h2\b', raw)
    assert h1 and h2 and h1.end() < match.start() < match.end() < h2.start(), 'answer placement'
    preceding = re.sub(r'<p class="byline">.*?</p>', '', raw[h1.end():match.start()], flags=re.S)
    assert not Visible(preceding).text(), 'answer must be first body prose'
    title = unescape(re.search(r'<title>(.*?)</title>', raw, re.S).group(1))
    answer = Visible(match.group(1)).text()
    assert len(title) <= 60, f'title too long: {title}'
    for text in (title, Visible(h1.group(1)).text(), answer):
        tokens = set(re.findall(r'\w+', text.lower()))
        assert set(spec['words']) <= tokens, f'missing question words: {text}'
    # Decimal points and domain names are not sentence endings.
    assert 2 <= len(re.split(r'(?<=[.!?])\s+', answer)) <= 4, 'answer sentence count'
    assert set(NUMBER.findall(answer)) == spec['figures'], 'unsourced answer figure'
    for url in spec['sources']:
        assert f'href="{url}"' in match.group(), 'answer source missing'
    return answer


def check_page(raw, spec):
    answer = check_answer(raw, spec)
    body = article_html(raw)
    text = prose(raw)
    assert not re.search(r'[\u2013\u2014]', text), 'dash in visible prose'
    assert not re.search(r'\b(?:Codex|gate|job|manifest|Article Studio|old domain)\b', text), 'internal copy'
    assert not re.search(r'\b\d{4}-\d{2}-\d{2}\b', text), 'machine date visible'
    assert not re.search(r'\b\S+\.json\b', text), 'range file name visible'
    assert 'Published <time datetime="2026-11-20">20 November 2026</time>' in raw
    editorial = Visible(without_price_helpers(body)).text()
    money = set(re.findall(r'[$£€]\d[\d,]*(?:\.\d+)?', editorial))
    assert money == spec['prices'], f'rival price mismatch: {money}'
    monthly = re.findall(r'(\$\d[\d,]*(?:\.\d+)?) a month', editorial)
    assert all(re.fullmatch(r'\$\d[\d,]*\.\d{2}', value) for value in monthly), 'monthly cents missing'
    # Every authored section with an external factual source ends in a checked
    # note, including the first-screen answer before the first h2.
    for section in re.split(r'<h2\b[^>]*>.*?</h2>', body, flags=re.S):
        if 'rel="nofollow noopener"' in section:
            assert CHECKED in section, 'missing dated source block'
            if '<p class="verified-note">' in section:
                before_note = section.split('<p class="verified-note">', 1)[0]
                if 'rel="nofollow noopener"' in before_note:
                    assert section.index('<p class="verified-note">') > before_note.index('rel="nofollow noopener"'), 'note before rival block'
    faqs = schemas(raw, 'FAQPage')
    assert len(faqs) == 1
    qa = faqs[0]['mainEntity']
    assert 3 <= len(qa) <= 5
    visible = re.findall(r'<div class="faq-item"><h3>(.*?)</h3><p>(.*?)</p></div>', raw, re.S)
    expected = [(Visible(q['name']).text(), Visible(q['acceptedAnswer']['text']).text()) for q in qa]
    assert [(Visible(q).text(), Visible(a).text()) for q, a in visible] == expected, 'FAQ schema differs'
    for q in qa:
        answer_html = q['acceptedAnswer']['text']
        if 'rel="nofollow noopener"' in answer_html:
            assert CHECKED in answer_html, 'FAQ claim missing read date'
    return answer, [q['name'] for q in qa]


def rejected(raw, spec, reason):
    try:
        check_page(raw, spec)
    except AssertionError as error:
        assert reason in str(error), f'control rejected for wrong reason: {error}'
        print(f'CONTROL rejected: {error}', flush=True)
    else:
        raise AssertionError(f'control accepted: {reason}')


def check_earlier(site, new, old, env):
    # Preserve the earlier answer checkers and their published evidence. Their
    # older whole-site snapshots do not know about later page additions.
    for number, earlier in ((1, round_one), (2, round_two), (3, round_three)):
        for name, spec in earlier.PAGES.items():
            source = spec[1] if number == 3 else round_one.SOURCE
            published = run(ROOT, ['git', 'show', earlier.BASE + ':site' + source + 'index.html'], env, quiet=True)
            if number == 3:
                earlier.check_answer(new[name], spec, site, published)
            else:
                round_one.check_answer(new[name], spec, site, published)
            assert round_one.unchanged(new[name]) == round_one.unchanged(old[name]), f'earlier page changed: {name}'
            print(f'PASS earlier measured answer {number}: {name}', flush=True)


def main():
    before = protected_state()
    # Both authored pages and the history gate must see the same frozen facts.
    tree = ast.parse((ROOT / 'scripts/articles/comparisons.py').read_text())
    recorded = next(ast.literal_eval(node.value) for node in tree.body
                    if isinstance(node, ast.AnnAssign) and node.target.id == 'VERIFIED')
    sys.path.insert(0, str(ROOT / 'scripts/articles'))
    from real_questions_sources import READINGS
    assert {key: recorded[key] for key in READINGS} == READINGS, 'source snapshot differs from dated registry'
    with tempfile.TemporaryDirectory(prefix='test-real-questions-1120-') as temporary:
        destination = Path(temporary)
        scratch_copy(destination)
        env = environment(destination)
        env['DOCKET_APP'] = str(app_path.find())
        git_dir = run(ROOT, ['git', 'rev-parse', '--absolute-git-dir'], env, quiet=True).strip()
        (destination / '.git').write_text(f'gitdir: {git_dir}\n')
        current = {name: (destination / name).read_bytes() for name in SOURCE_GENERATORS}
        for name in SOURCE_GENERATORS:
            (destination / name).write_text(run(ROOT, ['git', 'show', BASE + ':' + name], env, quiet=True))
        # The enclosing gate may already have built these pages. The base
        # generator does not delete retired output, so remove only these new
        # documents and their generated redirect stubs from the temp copy.
        site = destination / 'site'
        for path in PAGES:
            (site / path / 'index.html').unlink(missing_ok=True)
            if path.startswith('vs/'):
                (site / ('vs-' + path.split('/')[1]) / 'index.html').unlink(missing_ok=True)
        run(destination, [sys.executable, '-B', 'scripts/build.py'], env)
        old = {p.relative_to(site).as_posix(): p.read_text() for p in site.rglob('*.html')}
        assets = {name: (site / name).read_bytes() for name in ('llms.txt', 'offer.json')}
        for name, data in current.items():
            (destination / name).write_bytes(data)
        run(destination, [sys.executable, '-B', 'scripts/build.py'], env)
        new = {p.relative_to(site).as_posix(): p.read_text() for p in site.rglob('*.html')}
        sitemap = (site / 'sitemap.xml').read_text()
        new_names = {name + '/index.html' for name in PAGES}
        assert new_names.isdisjoint(old), 'new page already existed'
        # Build creates flat /vs-... redirects for new comparisons as well.
        redirects = {'vs-' + name.split('/')[1] + '/index.html' for name in PAGES if name.startswith('vs/')}
        assert new.keys() - old.keys() == new_names | redirects, 'unexpected page inventory'
        for name in old:
            if name in {'vs/index.html', 'how-to/index.html',
                        'vs/se-ranking-vs-screaming-frog/index.html', 'vs/jetoctopus-alternative/index.html'}:
                continue
            assert unstamped(new[name]) == unstamped(old[name]), f'unrelated page changed: {name}'
        for name, data in assets.items():
            assert (site / name).read_bytes() == data, f'protected asset changed: {name}'
        # Only the requested inbound paragraphs and required date fields move.
        for name in ('vs/se-ranking-vs-screaming-frog/index.html', 'vs/jetoctopus-alternative/index.html'):
            raw = new[name]
            paragraphs = re.findall(r'<p\b[^>]*>.*?</p>', raw, re.S)
            added = [p for p in paragraphs if any(f'href="/{key}/"' in p for key in PAGES)]
            assert len(added) == 1, f'inbound paragraph missing: {name}'
            assert round_one.unchanged(raw.replace(added[0], '')) == round_one.unchanged(old[name]), f'inbound source copy changed: {name}'
        all_shingles = {name: shingles(prose(raw)) for name, raw in new.items()}
        all_questions = {}
        for name, raw in new.items():
            for faq in schemas(raw, 'FAQPage'):
                for q in faq['mainEntity']:
                    all_questions.setdefault(q['name'].casefold(), []).append(name)
        for path, spec in PAGES.items():
            name = path + '/index.html'
            raw = new[name]
            answer, questions = check_page(raw, spec)
            assert f'<loc>https://checkengineseo.com/{path}/</loc>' in sitemap, 'missing sitemap entry'
            hub = path.split('/')[0] + '/index.html'
            assert f'href="/{path}/"' in new[hub], 'missing hub link'
            if spec['inbound']:
                assert f'href="/{path}/"' in new[spec['inbound'] + '/index.html'], 'missing inbound link'
            for q in questions:
                assert all_questions[q.casefold()] == [name], f'FAQ reused: {q}'
            pairs = sorted(((similarity(all_shingles[name], values), other)
                            for other, values in all_shingles.items() if other != name), reverse=True)
            assert pairs[0][0] < 0.5, f'page similarity too high: {pairs[0]}'
            for other in new_names - {name}:
                assert similarity(all_shingles[name], all_shingles[other]) < 0.4, f'new pair too similar: {other}'
            print(f'PAGE /{path}/ | {unescape(re.search(r"<title>(.*?)</title>", raw).group(1))} | '
                  f'{len(prose(raw).split())} words | max Jaccard {pairs[0][0]:.4f} with {pairs[0][1]}', flush=True)
            print('ANSWER ' + answer, flush=True)
            match = ANSWER.search(raw)
            rejected(raw.replace(match.group(), '', 1), spec, 'expected one measured answer')
            figure = NUMBER.search(Visible(match.group(1)).text()).group()
            rejected(raw[:match.start()] + match.group().replace(figure, '987654.321', 1) + raw[match.end():], spec, 'unsourced answer figure')
            rejected(raw.replace('Checked 20 November 2026.', 'Read recently.'), spec, 'missing dated source block')
            late = raw.replace(match.group(), '', 1).replace('</article>', match.group() + '</article>', 1)
            rejected(late, spec, 'answer placement')
        # Test attribution as well as the set of prices: a Core/Growth swap
        # would still contain all four correct numbers.
        sr = new['vs/contentking-vs-se-ranking/index.html']
        core = re.search(r'<tr><th scope="row">Core</th>(.*?)</tr>', sr, re.S).group(1)
        growth = re.search(r'<tr><th scope="row">Growth</th>(.*?)</tr>', sr, re.S).group(1)
        assert Visible(core).text() == '$129.00 a month $103.20 a month 250,000'
        assert Visible(growth).text() == '$279.00 a month $223.20 a month 2,000,000'
        assert 'publishes no dollar prices' in prose(sr)
        sf = prose(new['vs/screaming-frog-vs-semrush/index.html'])
        assert '$279 a year in the USD view' in sf and '£199 a year' in sf
        assert '1 demo project and 10 reports per day' in sf
        assert 'Per-audit page limit Not stated' in sf
        sb = prose(new['vs/sitebulb-vs-jetoctopus/index.html'])
        assert 'Desktop Lite: $18.00 a month, 10,000 URLs per audit.' in sb
        assert 'Desktop Pro: $42.00 a month, 500,000 URLs per audit.' in sb
        assert 'Cloud: from $125.00 a month.' in sb
        for row in ('Growth 500,000 2,000,000', 'Pro 2,000,000 8,000,000', 'Ultra 5,000,000 25,000,000'):
            assert row in sb, 'incorrect JetOctopus allowance'
        google = prose(new['how-to/test-a-page-as-googlebot/index.html'])
        assert 'Google-InspectionTool' in google
        assert not re.search(r'attackers|spoofing threats|protect your site', google, re.I)
        for row in ('Common crawlers 317 170 147', 'Special crawlers 272 136 136',
                    'User-triggered fetchers 1,088 544 544',
                    'Google-controlled user-triggered fetchers 504 252 252',
                    'User-triggered agents 20 12 8'):
            assert row in google, 'incorrect measured range counts'
        noindex = new['how-to/check-a-page-for-noindex/index.html']
        assert '<q>the page or resource must not be blocked by a robots.txt file</q>' in noindex
        assert noindex.count('href="/tools/meta-tag-checker/"') == 1
        assert 'acquired' not in prose(new['vs/contentking-vs-se-ranking/index.html']).lower()
        jet = new['vs/sitebulb-vs-jetoctopus/index.html']
        jet_block = jet.split('<h2>JetOctopus pairs', 1)[1].split('<h2>', 1)[0]
        assert not re.search(r'[$£€]\d', Visible(jet_block).text()), 'JetOctopus price published'
        check_earlier(site, new, old, env)
        for command in ([sys.executable, '-B', 'scripts/verify_numbers.py'],
                        [sys.executable, '-B', 'scripts/verify_structured_data_matches_page.py'],
                        [sys.executable, '-B', 'scripts/verify_link_graph.py'],
                        [sys.executable, '-B', 'scripts/verify_competitive_claims.py']):
            run(destination, command, env)
    assert protected_state() == before, 'protected source files changed'
    print('REAL QUESTIONS 1120 ok: scratch builds, sources, prices, links, FAQ, similarity, controls and earlier answers; protected source tree unchanged')


if __name__ == '__main__':
    main()
