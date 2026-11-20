#!/usr/bin/env python3
"""Offline measured-answer regression gate. Builds only in a disposable copy."""
from __future__ import annotations

import difflib
from html.parser import HTMLParser
from pathlib import Path
import re
import sys
import tempfile
from urllib.parse import urlsplit

from test_thank_you_review_ask import environment, protected_state, run, scratch_copy, sale_copy_allowance, unstamped


ROOT = Path(__file__).resolve().parent.parent
BASE = 'b04efb2bbab790dc83ff1ec3f38c2c9fc06fafc2'
SOURCE = '/vs/screaming-frog-alternative/'
PAGES = {
    'mac-seo-audit-tool/index.html': (
        'scripts/articles/mac_options.py', 'recorded free audit',
        ('4 pages in 12 seconds',),
    ),
    'best/screaming-frog-alternatives/index.html': (
        'scripts/articles/sf_alternatives.py', 'published free audit',
        ('4 pages', '9 problems'),
    ),
    'vs/ahrefs-site-audit-alternative/index.html': (
        'scripts/articles/comparisons.py', 'recorded free audit',
        ('4 pages', '9 problems'),
    ),
}
ANSWER = re.compile(r'<p id="measured-answer">(.*?)</p>', re.S)
NUMBER = re.compile(r'(?<![\w.])\d+(?:[,.]\d+)*(?:%)?(?![\w.])')


class Visible(HTMLParser):
    def __init__(self, raw):
        super().__init__(convert_charrefs=True)
        self.parts = []
        self.links = []
        self.link = None
        self.hidden = []
        self.feed(raw)
        self.close()

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag in {'head', 'script', 'style', 'template', 'noscript'}:
            self.hidden.append(tag)
        if self.hidden:
            return
        if tag in {'p', 'div', 'li', 'td', 'th', 'br', 'h1', 'h2', 'h3'}:
            self.parts.append(' ')
        if tag == 'a':
            self.link = [attrs, []]
            self.links.append(self.link)

    def handle_endtag(self, tag):
        if self.hidden:
            if tag == self.hidden[-1]:
                self.hidden.pop()
            return
        if tag == 'a':
            self.link = None
        if tag in {'p', 'div', 'li', 'td', 'th', 'h1', 'h2', 'h3'}:
            self.parts.append(' ')

    def handle_data(self, data):
        if not self.hidden:
            self.parts.append(data)
            if self.link is not None:
                self.link[1].append(data)

    def text(self):
        return ' '.join(''.join(self.parts).split())


def article(raw):
    raw = sale_copy_allowance(raw)
    match = re.search(r'<article\b[^>]*>.*?</article>', raw, re.S)
    assert match, 'missing article'
    # A new answer cannot become evidence for itself or for another answer.
    # 2026-11-19: Matthew requested the author name Matt Kerr become Matthew Kerr.
    return Visible(ANSWER.sub('', match.group())).text().replace('Matt Kerr', 'Matthew Kerr')



def source_date_allowance(text):
    """20 Nov 2026 (Saban): the rivals' prices were re-read the same day, unchanged, so the Screaming Frog comparison's own
    dateline and its one "read from its pricing page" date moved from 9 and 4 November to 20 November. Only those two dated
    phrases are made equal; every amount and sentence around them is still compared."""
    return (text.replace('Updated 20 November 2026', 'Updated 9 November 2026')
                .replace('read from its pricing page on 20 November 2026', 'read from its pricing page on 4 November 2026'))


def check_answer(raw, spec, site, published):
    # 20 November 2026 first-screen batch: the two replaced answers use today's
    # rival readings. Keep the original checker below for historical controls.
    for name, title in (
        ('vs/ahrefs-site-audit-alternative/index.html', 'Ahrefs Site Audit: free limits and paid plans'),
        ('best/free-seo-audit-tools/index.html', 'Free SEO audit: tools and limits'),
    ):
        if f'<title>{title}</title>' in raw:
            from test_first_screens_1120 import PAGES as refreshed, check_page
            return check_page(raw, refreshed[name])
    if '<title>Screaming Frog alternatives compared</title>' in raw:
        from test_best_compared_3 import reviewed_refresh as compared_refresh
        compared_refresh('best/screaming-frog-alternatives/index.html', raw)
        return ANSWER.search(raw)
    _generator, label, facts = spec
    matches = list(ANSWER.finditer(raw))
    assert len(matches) == 1, 'expected one measured answer'
    match = matches[0]
    h1 = re.search(r'<h1\b[^>]*>.*?</h1>', raw, re.S)
    h2 = re.search(r'<h2\b', raw)
    assert h1 and h2 and h1.end() < match.start() < match.end() < h2.start(), \
        'answer must follow h1 and precede first h2'
    # It is the first body paragraph after the byline, ahead of the old lede.
    preceding = raw[h1.end():match.start()]
    preceding = re.sub(r'<p class="byline">.*?</p>', '', preceding, flags=re.S)
    assert not Visible(preceding).text(), 'answer must come before other body prose'
    answer = Visible(match.group(1))
    text = answer.text()
    assert 2 <= len(re.split(r'(?<=[.!?])\s+', text)) <= 4, 'use two to four sentences'
    assert not re.search(r'[\u2013\u2014()]', text), 'use plain punctuation'
    assert len(answer.links) == 1, 'missing visible source link'
    attrs, words = answer.links[0]
    assert attrs == {'href': SOURCE} and ''.join(words).strip() == label, \
        'missing visible source link'
    url = urlsplit(attrs['href'])
    assert not any((url.scheme, url.netloc, url.query, url.fragment)), 'use a local clean link'
    target = (site / url.path.lstrip('/') / 'index.html').resolve()
    assert target.is_relative_to(site.resolve()) and target.is_file(), 'missing source page'
    source_texts = (article(target.read_text(encoding='utf-8')), article(published))
    figures = NUMBER.findall(text)
    assert figures, 'answer must contain a number'
    for source in source_texts:
        sourced = set(NUMBER.findall(source))
        for figure in figures:
            assert figure in sourced, f'unsourced number: {figure}'
        for fact in facts:
            assert fact in text and fact in source, f'missing measured context: {fact}'
    return match


def rejected(raw, spec, site, published, reason):
    try:
        check_answer(raw, spec, site, published)
    except AssertionError as error:
        assert reason in str(error), f'control failed for the wrong reason: {error}'
        print(f'CONTROL rejected: {error}', flush=True)
    else:
        raise AssertionError(f'control passed unexpectedly: {reason}')


def unchanged(raw):
    # Only the added paragraph, its page update date and the build stamp may move.
    raw = ANSWER.sub('', raw)
    raw = re.sub(r'"dateModified":\s*"[^"]*",\s*', '', raw)
    raw = re.sub(r'<span class="sep">·</span>Updated <time[^>]*>.*?</time>', '', raw)
    # 20 Nov 2026 (launch fixes): the phone "Send myself the link" block was added to / and /download/ next to the download buttons, and
    # on /download/ it now sits after the old-name note instead of before it. Only that block and that one fixed note are left out of
    # this comparison (both have their own tests); every other line is still compared.
    raw = re.sub(r'<div class="phone-download">.*?</noscript>\s*</div>\n?', '', raw, flags=re.S)
    raw = raw.replace('<p>Check Engine SEO was called Docket SEO; the installer and app still carry the old name for now.</p>\n', '')
    return re.sub(r'\n\s*\n', '\n', unstamped(raw))


def main():
    before = protected_state()
    with tempfile.TemporaryDirectory(prefix='test-measured-answers-') as temporary:
        destination = Path(temporary)
        scratch_copy(destination)
        env = environment(destination)
        # The nested thank-you test reads a historical generator with git show.
        # A temp-only pointer supplies history without copying secrets or Git objects.
        git_dir = run(ROOT, ['git', 'rev-parse', '--absolute-git-dir'], env, quiet=True).strip()
        (destination / '.git').write_text(f'gitdir: {git_dir}\n', encoding='utf-8')
        published = run(ROOT, ['git', 'show', BASE + ':site' + SOURCE + 'index.html'], env, quiet=True)
        current = {}
        for generator, _label, _facts in PAGES.values():
            path = destination / generator
            current[generator] = path.read_bytes()
            base = run(ROOT, ['git', 'show', BASE + ':' + generator], env, quiet=True)
            path.write_text(base, encoding='utf-8')

        print(f'Building base {BASE}', flush=True)
        run(destination, [sys.executable, '-B', 'scripts/build.py'], env)
        site = destination / 'site'
        old = {path.relative_to(site).as_posix(): path.read_text(encoding='utf-8')
               for path in site.rglob('*.html')}
        # First-screen batch, 20 November 2026: registration keeps the later
        # Ahrefs rewrite during replay. Recover only Round 1's actual old page.
        from test_first_screens_1120 import BASE as first_base, legacy_page, reviewed_refresh
        ahrefs = 'vs/ahrefs-site-audit-alternative/index.html'
        old[ahrefs] = legacy_page(destination, env, ahrefs, PAGES[ahrefs][0], BASE)
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
                # Morning batch, 20 November 2026: allow only Round 3's
                # measured Sitebulb paragraph and its update fields.
                if name == 'vs/sitebulb-alternative/index.html':
                    import test_measured_answers_3 as third
                    source = run(ROOT, ['git', 'show', third.BASE + ':site/learn/seo-audit/index.html'], env, quiet=True)
                    third.check_answer(raw, third.PAGES[name], site, source)
                    assert unchanged(raw) == unchanged(old[name]), 'Sitebulb copy beyond the measured answer changed'
                    assert 'Updated <time datetime="2026-11-16">16 November 2026</time>' in raw
                else:
                    assert unstamped(raw) == unstamped(old[name]), f'unrelated page changed: {name}'
                continue
            spec = PAGES[name]
            if name == ahrefs:
                # First-screen batch, 20 November 2026: permit exactly the
                # sourced Ahrefs rewrite; retain every original round assertion
                # and negative control on its pre-rewrite measured answer.
                reviewed_refresh(name, raw)
                raw = legacy_page(destination, env, name, spec[0], first_base)
            if name == 'best/screaming-frog-alternatives/index.html':
                # 20 November comparison batch: validate the pinned comparison,
                # then retain Round 1's old copy and negative-control assertions.
                from test_best_compared_3 import BASE as compared_base, legacy_page as compared_legacy, reviewed_refresh as compared_refresh
                compared_refresh(name, raw)
                raw = compared_legacy(destination, env, name, compared_base)
            match = check_answer(raw, spec, site, published)
            difference = list(difflib.unified_diff(unchanged(old[name]).splitlines(),
                                                  unchanged(raw).splitlines()))
            assert not difference, f'existing page copy changed: {name}\n' + '\n'.join(difference[:30])
            assert 'Updated <time datetime="2026-11-16">16 November 2026</time>' in raw
            assert re.search(r'"dateModified":\s*"2026-11-16"', raw)
            invented = match.group().replace('pages', '987654.321 pages', 1)
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

        for command in ([sys.executable, '-B', 'scripts/lint.py', 'site'],
                        [sys.executable, '-B', 'scripts/verify_structured_data_matches_page.py'],
                        [sys.executable, '-B', 'scripts/test_chatgpt_app_links.py'],
                        [sys.executable, '-B', 'scripts/test_thank_you_review_ask.py'],
                        [sys.executable, '-B', 'scripts/verify_link_graph.py']):
            run(destination, command, env)
    assert protected_state() == before, 'source site/, workers/ or data/ changed'
    print('MEASURED ANSWERS ok: base, sourced figures, controls and scratch gates; source tree unchanged')


if __name__ == '__main__':
    main()
