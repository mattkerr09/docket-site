#!/usr/bin/env python3
"""Offline Round 2 regression gate. All builds stay in a disposable copy."""
from __future__ import annotations

import difflib
from pathlib import Path
import re
import sys
import tempfile

import test_measured_answers as round_one
from test_measured_answers import ANSWER, SOURCE, article, check_answer, rejected, unchanged
from test_thank_you_review_ask import environment, protected_state, run, scratch_copy, unstamped


ROOT = Path(__file__).resolve().parent.parent
BASE = '29b643ec934f97debdf877d3e771c4187477b943'
PAGES = {
    # E6: free website SEO audit tool.
    'best/free-seo-audit-tools/index.html': (
        'scripts/articles/best_free.py', 'recorded free audit',
        ('4 pages', '9 problems'),
    ),
    # E7: how do I find broken links and SEO problems on my website.
    'how-to/fix-broken-outbound-links/index.html': (
        'scripts/articles/howto_broken_links.py', 'recorded free audit',
        ('4 pages', '9 problems'),
    ),
    # E9: SEO audit software without a monthly subscription.
    'download/index.html': (
        'scripts/articles/pages.py', 'recorded free audit',
        ('4 pages', '12 seconds'),
    ),
}


def main():
    before = protected_state()
    with tempfile.TemporaryDirectory(prefix='test-measured-answers-2-') as temporary:
        destination = Path(temporary)
        # Uses the thank-you test's filter before opening files: no dotfiles,
        # secret-like names, symlinks, node_modules or Python caches.
        scratch_copy(destination)
        env = environment(destination)
        # The nested thank-you test needs historical source. A temp-only
        # pointer supplies read-only history without copying Git objects.
        git_dir = run(ROOT, ['git', 'rev-parse', '--absolute-git-dir'], env, quiet=True).strip()
        (destination / '.git').write_text(f'gitdir: {git_dir}\n', encoding='utf-8')
        published = run(ROOT, ['git', 'show', BASE + ':site' + SOURCE + 'index.html'], env, quiet=True)
        current = {}
        for generator, _label, _facts in PAGES.values():
            path = destination / generator
            current[generator] = path.read_bytes()
            base = run(ROOT, ['git', 'show', BASE + ':' + generator], env, quiet=True)
            path.write_text(base, encoding='utf-8')

        print(f'Building Round 2 base {BASE}', flush=True)
        run(destination, [sys.executable, '-B', 'scripts/build.py'], env)
        site = destination / 'site'
        old = {path.relative_to(site).as_posix(): path.read_text(encoding='utf-8')
               for path in site.rglob('*.html')}
        assert article((site / SOURCE.strip('/') / 'index.html').read_text()) == article(published), \
            'measurement source differs from the published base'
        for name, spec in PAGES.items():
            assert not ANSWER.search(old[name]), f'{name}: answer already present on base'
            rejected(old[name], spec, site, published, 'expected one measured answer')

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
            # Round 1's checker requires a first body paragraph before the
            # first h2, two to four sentences and a visible clean source link.
            # Every number and its measured context must be present in both
            # the scratch source article and its already-published base copy.
            match = check_answer(raw, spec, site, published)
            difference = list(difflib.unified_diff(unchanged(old[name]).splitlines(),
                                                  unchanged(raw).splitlines()))
            assert not difference, f'existing page copy changed: {name}\n' + '\n'.join(difference[:30])
            assert 'Updated <time datetime="2026-11-16">16 November 2026</time>' in raw
            assert re.search(r'"dateModified":\s*"2026-11-16"', raw)
            invented = match.group().replace('pages', '987654.321 pages', 1)
            assert invented != match.group(), 'invented-figure plant did not land'
            rejected(raw[:match.start()] + invented + raw[match.end():], spec, site, published,
                     'unsourced number: 987654.321')
            missing = match.group().replace(f'<a href="{SOURCE}">', '').replace('</a>', '')
            assert missing != match.group(), 'missing-link plant did not land'
            rejected(raw[:match.start()] + missing + raw[match.end():], spec, site, published,
                     'missing visible source link')
            late = raw[:match.start()] + raw[match.end():]
            late = late.replace('</article>', match.group() + '</article>', 1)
            rejected(late, spec, site, published, 'answer must follow h1 and precede first h2')
            print(f'PASS {name}: sourced answer; existing copy preserved', flush=True)

        # Round 1's whole-site comparison predates this job. Check each of
        # its pages explicitly even if its standalone gate rejects a new page.
        published_one = run(ROOT, ['git', 'show', round_one.BASE + ':site' + SOURCE + 'index.html'],
                            env, quiet=True)
        for name, spec in round_one.PAGES.items():
            assert name not in PAGES, 'Round 1 page selected for Round 2'
            assert unstamped(new[name]) == unstamped(old[name]), f'Round 1 page changed: {name}'
            check_answer(new[name], spec, site, published_one)
            print(f'PASS Round 1 unchanged: {name}', flush=True)

        for command in ([sys.executable, '-B', 'scripts/lint.py', 'site'],
                        [sys.executable, '-B', 'scripts/verify_structured_data_matches_page.py'],
                        [sys.executable, '-B', 'scripts/test_chatgpt_app_links.py'],
                        [sys.executable, '-B', 'scripts/test_thank_you_review_ask.py'],
                        [sys.executable, '-B', 'scripts/verify_link_graph.py']):
            run(destination, command, env)
    assert protected_state() == before, 'source site/, workers/ or data/ changed'
    print('MEASURED ANSWERS 2 ok: base, sourced figures, controls, Round 1 and scratch gates; source tree unchanged')


if __name__ == '__main__':
    main()
