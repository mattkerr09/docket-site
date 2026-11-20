#!/usr/bin/env python3
"""Offline Round 2 regression gate. All builds stay in a disposable copy."""
from __future__ import annotations

import difflib
from pathlib import Path
import re
import sys
import tempfile

import test_measured_answers as round_one
from test_measured_answers import ANSWER, SOURCE, article, check_answer, rejected, source_date_allowance, unchanged
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


def morning_allowance(name, old):
    # Morning batch and reviewed copy fixes, 20 November 2026. Exact additions
    # and replacements only; every remaining byte keeps the original assertion.
    if name == 'how-to/index.html':
        added = ('<h2><a href="/how-to/test-a-page-as-googlebot/">Googlebot test: inspect a page or identify a visit</a></h2>\n'
                 '<p>Choose the test that answers your question, then read what its result can establish.</p>\n\n'
                 '<h2><a href="/how-to/check-a-page-for-noindex/">Meta noindex checker: tags and response headers</a></h2>\n'
                 '<p>Inspect both places a noindex directive can appear before changing the page.</p>\n\n')
        assert old.count('<h2>More coming</h2>') == 1
        return old.replace('<h2>More coming</h2>', added + '<h2>More coming</h2>', 1)
    if name == 'download/index.html':
        # 20 November 2026 copy batch: the former-name note and the key's
        # actual purpose. The download, sale and price helpers stay protected.
        marker = '<ol class="steps" id="buy">'
        assert old.count(marker) == 1
        old = old.replace(marker, '<p>Check Engine SEO was called Docket SEO; the installer and app still carry the old name for now.</p>\n' + marker, 1)
        before = '<li><strong>Paste the key</strong> into the field the app shows, and run your first audit.'
        after = '<li>Paste the key into the field the app shows to open the full report and fix plan.'
        assert old.count(before) == 1
        return old.replace(before, after, 1)
    if name == 'legal/privacy/index.html':
        before, after = 'for the current price and any sale, and asks', 'whether a sale is open, and asks'
        assert old.count(before) == 1
        return old.replace(before, after, 1)
    if name == 'legal/terms/index.html':
        for before, after in (
            ('The software is written by Matt Kerr.', 'The software is written by Matthew Kerr.'),
            ('buys is the licence key that lets it run.', 'buys is the licence key that shows the full report and fix plan.'),
        ):
            assert old.count(before) == 1
            old = old.replace(before, after, 1)
    return old


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
        assert source_date_allowance(article((site / SOURCE.strip('/') / 'index.html').read_text())) == article(published), \
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
                if name == 'best/index.html':
                    # 20 November comparison batch: exact hub rewrite only.
                    from test_best_compared_3 import legacy_page as compared_legacy, reviewed_refresh as compared_refresh
                    compared_refresh(name, raw)
                    prior = compared_legacy(destination, env, name, BASE)
                    assert unstamped(prior) == unstamped(morning_allowance(name, old[name])), 'prior hub changed'
                else:
                    assert unstamped(raw) == unstamped(morning_allowance(name, old[name])), f'unrelated page changed: {name}'
                continue
            spec = PAGES[name]
            if name == 'best/free-seo-audit-tools/index.html':
                # First-screen batch, 20 November 2026: permit the exact free
                # audit rewrite and retain Round 2's original answer controls.
                from test_first_screens_1120 import BASE as first_base, legacy_page, reviewed_refresh
                reviewed_refresh(name, raw)
                raw = legacy_page(destination, env, name, spec[0], first_base)
            # Round 1's checker requires a first body paragraph before the
            # first h2, two to four sentences and a visible clean source link.
            # Every number and its measured context must be present in both
            # the scratch source article and its already-published base copy.
            match = check_answer(raw, spec, site, published)
            difference = list(difflib.unified_diff(unchanged(morning_allowance(name, old[name])).splitlines(),
                                                  unchanged(raw).splitlines()))
            assert not difference, f'existing page copy changed: {name}\n' + '\n'.join(difference[:30])
            # 20 Nov 2026 (launch fixes): /download/ gained the phone block today, a content change of that page, so its own
            # dateline legitimately moved from 16 to 20 November; every other Round 2 page keeps 16 November.
            day = ('2026-11-20', '20 November 2026') if name == 'download/index.html' else ('2026-11-16', '16 November 2026')
            assert f'Updated <time datetime="{day[0]}">{day[1]}</time>' in raw
            assert re.search(r'"dateModified":\s*"' + day[0] + '"', raw)
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
