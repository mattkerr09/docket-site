#!/usr/bin/env python3
"""Offline thank-you regression gate. All builds stay in a disposable copy."""
from __future__ import annotations

from html.parser import HTMLParser
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parent.parent
# Reviewed main after the free-tools backlog, before this ask was added.
BASE = '99d68510ed1fefe3f250d9b48691fb93a6877cd5'
LISTING = 'https://alternativeto.net/software/docket-seo/'
ASK = 'Used Check Engine? Add an honest review on AlternativeTo.'
DIRECTORIES = ('scripts', 'data', 'site', 'workers')


class Page(HTMLParser):
    def __init__(self, raw):
        super().__init__(convert_charrefs=True)
        self.tags = []
        self.words = []
        self.hidden = ''
        self.feed(raw)

    def handle_starttag(self, tag, attrs):
        self.tags.append((tag, dict(attrs)))
        if tag in {'script', 'style', 'template', 'noscript'}:
            self.hidden = tag

    def handle_endtag(self, tag):
        if tag == self.hidden:
            self.hidden = ''

    def handle_data(self, data):
        if not self.hidden:
            self.words.append(data)

    def text(self):
        return ' '.join(' '.join(self.words).split())


def excluded(directory, names):
    """Filter names before copytree opens files, including hidden credentials."""
    ignored = set()
    for name in names:
        lower = name.lower()
        if (name.startswith('.') or lower in {'node_modules', '__pycache__'}
                or '.env' in lower or lower.endswith(('.pem', '.key', '.p12', '.pfx', '.keystore'))
                or re.search(r'(^|[._-])(secrets?|credentials?|passwords?|tokens?|auth)([._-]|$)', lower)
                or (Path(directory) / name).is_symlink()):
            ignored.add(name)
    return ignored


def scratch_copy(destination):
    for directory in DIRECTORIES:
        shutil.copytree(ROOT / directory, destination / directory, ignore=excluded)


def environment(destination):
    # An isolated home and temp directory, with no inherited app credentials.
    for name in ('home', 'tmp', 'offline'):
        (destination / name).mkdir(exist_ok=True)
    (destination / 'offline/sitecustomize.py').write_text(
        "import sys\n"
        "def offline(event, args):\n"
        "    if event in {'socket.connect', 'socket.getaddrinfo', 'socket.bind'}:\n"
        "        raise RuntimeError('Network is disabled in this scratch build')\n"
        "sys.addaudithook(offline)\n")
    return dict(PATH=os.environ.get('PATH', os.defpath), HOME=str(destination / 'home'),
                TMPDIR=str(destination / 'tmp'), TZ='UTC', PYTHONDONTWRITEBYTECODE='1',
                DOCKET_SKIP_BRAND_ASSETS='1', SITE_BRAND='checkengine',
                PYTHONPATH=str(destination / 'offline'))


def run(destination, command, env, quiet=False):
    print('$ ' + ' '.join(command), flush=True)
    completed = subprocess.run(command, cwd=destination, env=env, capture_output=True, text=True)
    output = completed.stdout + completed.stderr
    if completed.returncode or not quiet:
        print(output if completed.returncode else '\n'.join(
            line for line in output.splitlines() if not line.startswith('  site/')))
    print(f'exit {completed.returncode}', flush=True)
    if completed.returncode:
        raise SystemExit(completed.returncode)
    return output


def check_ask(raw):
    page = Page(raw)
    links = [attrs for tag, attrs in page.tags if tag == 'a'
             and 'alternativeto' in attrs.get('href', '').lower()]
    assert len(links) == 1, 'show one AlternativeTo review link'
    assert links[0] == {'href': LISTING, 'rel': 'noreferrer'}, 'exact destination, no tracking'
    assert not urlsplit(links[0]['href']).query and not urlsplit(links[0]['href']).fragment
    paragraphs = [p for p in re.findall(r'<p\b[^>]*>.*?</p>', raw, re.S)
                  if LISTING in p]
    assert len(paragraphs) == 1
    paragraph = paragraphs[0]
    assert Page(paragraph).text() == ASK, 'optional honest ask only, without a reward'
    assert page.text().count(ASK) == 1
    assert raw.index('href="/download/"', raw.index('id="ty-lede"')) < raw.index(paragraph)
    assert raw.index('href="/legal/refunds/"') < raw.index(paragraph), 'help comes first'
    assert ('meta', {'name': 'robots', 'content': 'noindex'}) in page.tags
    assert ('meta', {'name': 'referrer', 'content': 'strict-origin-when-cross-origin'}) in page.tags
    scrub = 'history.replaceState(null, \'\', location.pathname + location.hash);'
    assert scrub in raw and 'catch (e) { location.replace(location.pathname); }' in raw
    assert raw.index('window.__dkReturn = keep;') < raw.index(scrub) < raw.index('<link ')
    assert "var ret = window.__dkReturn || {};" in raw
    return paragraph


def rejected(raw, label):
    try:
        check_ask(raw)
    except AssertionError as error:
        print(f'CONTROL rejected {label}: {error}')
    else:
        raise AssertionError(f'control passed unexpectedly: {label}')


def unstamped(raw):
    return re.sub(r'(<meta name="build-id" content=")[^"]+(">)', r'\1BUILD\2', raw)


def protected_state():
    # Metadata only: do not open any source-tree credential or customer file.
    return {str(path.relative_to(ROOT)): (path.lstat().st_size, path.lstat().st_mtime_ns)
            for directory in ('site', 'workers', 'data')
            for path in (ROOT / directory).rglob('*') if not path.is_dir()}


def main():
    before = protected_state()
    with tempfile.TemporaryDirectory(prefix='test-thank-you-review-') as temporary:
        destination = Path(temporary)
        scratch_copy(destination)
        env = environment(destination)
        generator = destination / 'scripts/build.py'
        current = generator.read_bytes()
        base = run(ROOT, ['git', 'show', BASE + ':scripts/build.py'], env, quiet=True)
        generator.write_text(base)
        print(f'Building base {BASE}', flush=True)
        run(destination, [sys.executable, '-B', 'scripts/build.py'], env)
        thank_you = destination / 'site/thank-you/index.html'
        old = thank_you.read_text()
        assert LISTING not in old and ASK not in Page(old).text(), 'ask is already present on base'
        rejected(old, 'base without the ask')

        generator.write_bytes(current)
        print('Building current generator', flush=True)
        run(destination, [sys.executable, '-B', 'scripts/build.py'], env)
        raw = thank_you.read_text()
        paragraph = check_ask(raw)
        # Byte comparison apart from the added paragraph and derived build id
        # protects receipt, key display, verification, scripts and refund copy.
        assert unstamped(raw.replace(paragraph + '\n', '', 1)) == unstamped(old), \
            'existing thank-you content or purchase/privacy handling changed'
        rejected(raw.replace('review on AlternativeTo.', 'review on AlternativeTo. Get a reward.'),
                 'reward offer')
        rejected(raw.replace(LISTING, LISTING + '?license_key=TEST-KEY&payment_id=TEST-PAYMENT'),
                 'leaked purchase query')

        checked = 0
        for path in (destination / 'site').rglob('*.html'):
            if path == thank_you:
                continue
            other = path.read_text()
            assert 'alternativeto' not in other.lower() and ASK not in Page(other).text(), path
            checked += 1
        for path in (destination / 'workers').rglob('*.js'):
            assert 'alternativeto' not in path.read_text().lower(), path
        print(f'PASS: one honest ask; {checked} other pages and worker/free-result sources have no ask')
        print('PASS: existing thank-you HTML unchanged apart from the ask and build id')
        for command in ([sys.executable, '-B', 'scripts/lint.py', 'site'],
                        [sys.executable, '-B', 'scripts/test_chatgpt_app_links.py'],
                        [sys.executable, '-B', 'scripts/verify_structured_data_matches_page.py']):
            run(destination, command, env)
    assert protected_state() == before, 'source site/, workers/ or data/ changed'
    print('THANK-YOU REVIEW ASK ok: scratch builds, base and unsafe controls, unchanged source tree')


if __name__ == '__main__':
    main()
