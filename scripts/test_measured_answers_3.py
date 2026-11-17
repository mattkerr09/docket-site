#!/usr/bin/env python3
"""Offline Round 3 regression gate. All builds stay in a disposable copy."""
from __future__ import annotations

import difflib
from pathlib import Path
import re
import sys
import tempfile
from urllib.parse import urlsplit

import test_measured_answers as round_one
import test_measured_answers_2 as round_two
from test_measured_answers import ANSWER, NUMBER, Visible, article, unchanged
from test_thank_you_review_ask import environment, protected_state, run, scratch_copy, unstamped


ROOT = Path(__file__).resolve().parent.parent
BASE = 'e9ea69b3a75afbfb63e3113e3fc4bbcff6a91451'
PAGES = {
    # E5: Sitebulb alternative.
    'vs/sitebulb-alternative/index.html': (
        'scripts/articles/comparisons.py', '/learn/seo-audit/',
        'small-business audit results', ('12 of the 14 sites', 'network checks off'),
    ),
    # E10: how to check my website for technical SEO issues for free.
    'tools/website-checker/index.html': (
        'scripts/articles/tools_website_checker.py', '/tools/seo-checker/',
        'published small-business audits', ('86 pages', '42.5 problems', 'default settings'),
    ),
}


def check_answer(raw, spec, site, published):
    _generator, source, label, facts = spec
    matches = list(ANSWER.finditer(raw))
    assert len(matches) == 1, 'expected one measured answer'
    match = matches[0]
    h1 = re.search(r'<h1\b[^>]*>.*?</h1>', raw, re.S)
    h2 = re.search(r'<h2\b', raw)
    assert h1 and h2 and h1.end() < match.start() < match.end() < h2.start(), \
        'answer must follow h1 and precede first h2'
    preceding = raw[h1.end():match.start()]
    preceding = re.sub(r'<p class="byline">.*?</p>', '', preceding, flags=re.S)
    assert not Visible(preceding).text(), 'answer must come before other body prose'
    answer = Visible(match.group(1))
    text = answer.text()
    assert 2 <= len(re.split(r'(?<=[.!?])\s+', text)) <= 4, 'use two to four sentences'
    assert not re.search(r'[\u2013\u2014()]', text), 'use plain punctuation'
    assert len(answer.links) == 1, 'missing visible source link'
    attrs, words = answer.links[0]
    assert attrs == {'href': source} and ''.join(words).strip() == label, \
        'missing visible source link'
    url = urlsplit(attrs['href'])
    assert not any((url.scheme, url.netloc, url.query, url.fragment)), 'use a local clean link'
    target = (site / url.path.lstrip('/') / 'index.html').resolve()
    assert target.is_relative_to(site.resolve()) and target.is_file(), 'missing source page'
    # Neither a new answer nor a number added elsewhere in this job can become
    # its own evidence. Require the built and already-published source article.
    source_texts = (article(target.read_text(encoding='utf-8')), article(published))
    figures = NUMBER.findall(text)
    assert figures, 'answer must contain a number'
    assert len(set(figures)) <= 2, 'use one or two measured figures'
    for source_text in source_texts:
        sourced = set(NUMBER.findall(source_text))
        for figure in figures:
            assert figure in sourced, f'unsourced number: {figure}'
        for fact in facts:
            assert fact in text and fact in source_text, f'missing measured context: {fact}'
    return match


def rejected(raw, spec, site, published, reason):
    try:
        check_answer(raw, spec, site, published)
    except AssertionError as error:
        assert reason in str(error), f'control failed for the wrong reason: {error}'
        print(f'CONTROL rejected: {error}', flush=True)
    else:
        raise AssertionError(f'control passed unexpectedly: {reason}')


def main():
    before = protected_state()
    with tempfile.TemporaryDirectory(prefix='test-measured-answers-3-') as temporary:
        destination = Path(temporary)
        # Filter before opening files: no dotfiles, secret-like names, symlinks,
        # node_modules or Python caches. Subprocesses use an isolated home and
        # an audit hook that refuses network access, as in the thank-you test.
        scratch_copy(destination)
        env = environment(destination)
        git_dir = run(ROOT, ['git', 'rev-parse', '--absolute-git-dir'], env, quiet=True).strip()
        # The nested thank-you test reads historical source through this
        # temp-only pointer. No Git objects or credentials are copied.
        (destination / '.git').write_text(f'gitdir: {git_dir}\n', encoding='utf-8')
        published = {}
        current = {}
        for generator, source, _label, _facts in PAGES.values():
            published[source] = run(ROOT, ['git', 'show', BASE + ':site' + source + 'index.html'],
                                    env, quiet=True)
            path = destination / generator
            current[generator] = path.read_bytes()
            base = run(ROOT, ['git', 'show', BASE + ':' + generator], env, quiet=True)
            path.write_text(base, encoding='utf-8')

        print(f'Building Round 3 base {BASE}', flush=True)
        run(destination, [sys.executable, '-B', 'scripts/build.py'], env)
        site = destination / 'site'
        old = {path.relative_to(site).as_posix(): path.read_text(encoding='utf-8')
               for path in site.rglob('*.html')}
        for source, raw in published.items():
            assert article((site / source.strip('/') / 'index.html').read_text()) == article(raw), \
                f'measurement source differs from the published base: {source}'
        for name, spec in PAGES.items():
            assert not ANSWER.search(old[name]), f'{name}: answer already present on base'
            rejected(old[name], spec, site, published[spec[1]], 'expected one measured answer')

        for generator, content in current.items():
            (destination / generator).write_bytes(content)
        print('Building current generators', flush=True)
        run(destination, [sys.executable, '-B', 'scripts/build.py'], env)
        new = {path.relative_to(site).as_posix(): path.read_text(encoding='utf-8')
               for path in site.rglob('*.html')}
        assert old.keys() == new.keys(), 'page inventory changed'
        for name, raw in new.items():
            if name not in PAGES:
                assert unstamped(raw) == unstamped(old[name]), f'unrelated page changed: {name}'
                continue
            spec = PAGES[name]
            source = spec[1]
            match = check_answer(raw, spec, site, published[source])
            difference = list(difflib.unified_diff(unchanged(old[name]).splitlines(),
                                                  unchanged(raw).splitlines()))
            assert not difference, f'existing page copy changed: {name}\n' + '\n'.join(difference[:30])
            assert 'Updated <time datetime="2026-11-16">16 November 2026</time>' in raw
            assert re.search(r'"dateModified":\s*"2026-11-16"', raw)
            # Replace a real figure, rather than append one: the invented
            # figure must fail sourcing, not the two-figure limit.
            figure = NUMBER.search(Visible(match.group(1)).text()).group()
            invented = match.group().replace(figure, '987654.321', 1)
            assert invented != match.group(), 'invented-figure plant did not land'
            rejected(raw[:match.start()] + invented + raw[match.end():], spec, site,
                     published[source], 'unsourced number: 987654.321')
            missing = match.group().replace(f'<a href="{source}">', '').replace('</a>', '')
            assert missing != match.group(), 'missing-link plant did not land'
            rejected(raw[:match.start()] + missing + raw[match.end():], spec, site,
                     published[source], 'missing visible source link')
            late = raw[:match.start()] + raw[match.end():]
            late = late.replace('</article>', match.group() + '</article>', 1)
            rejected(late, spec, site, published[source],
                     'answer must follow h1 and precede first h2')
            print(f'PASS {name}: sourced answer; existing copy preserved', flush=True)

        # Run every earlier page's actual checker even if a standalone older
        # gate rejects later work in its comparison of all pages to its base.
        for number, earlier in ((1, round_one), (2, round_two)):
            source = round_one.SOURCE
            evidence = run(ROOT, ['git', 'show', earlier.BASE + ':site' + source + 'index.html'],
                           env, quiet=True)
            for name, spec in earlier.PAGES.items():
                assert name not in PAGES, f'Round {number} page selected for Round 3'
                assert unstamped(new[name]) == unstamped(old[name]), f'earlier page changed: {name}'
                round_one.check_answer(new[name], spec, site, evidence)
                print(f'PASS Round {number} unchanged: {name}', flush=True)

        for command in ([sys.executable, '-B', 'scripts/lint.py', 'site'],
                        [sys.executable, '-B', 'scripts/verify_structured_data_matches_page.py'],
                        [sys.executable, '-B', 'scripts/test_chatgpt_app_links.py'],
                        [sys.executable, '-B', 'scripts/test_thank_you_review_ask.py'],
                        [sys.executable, '-B', 'scripts/verify_link_graph.py']):
            run(destination, command, env)
    assert protected_state() == before, 'source site/, workers/ or data/ changed'
    print('MEASURED ANSWERS 3 ok: base, sourced figures, controls, earlier pages and scratch gates; '
          'source tree unchanged')


if __name__ == '__main__':
    main()
