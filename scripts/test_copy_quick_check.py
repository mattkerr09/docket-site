#!/usr/bin/env python3
"""Offline copy-summary gate. All builds and controls stay in system temp."""
from __future__ import annotations

import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile

from test_website_checker_page import Page, ROUTE, scratch_copy

ROOT = Path(__file__).resolve().parent.parent
BASE = '909dc56cdf5b83c4203b58f75195f42e598bf329'
ACTIVE = 'DOCKET_COPY_QUICK_CHECK_ACTIVE'


def fixture(raw):
    page = Page(raw)
    ids = {attrs['id']: attrs for tag, attrs in page.tags if 'id' in attrs}
    # Include literal text for the fake DOM, including the visible limit and labels.
    for ident, attrs in ids.items():
        match = re.search(r'<([a-z0-9]+)\b[^>]*\bid="' + re.escape(ident)
                          + r'"[^>]*>([^<]*)</\1>', raw)
        attrs['_text'] = match[2] if match else ''
    return {'script': next(s for s in page.scripts if 'const ENDPOINT =' in s), 'ids': ids}


NODE_TEST = r"""
const assert = require('node:assert/strict');
const vm = require('node:vm');
const fs = require('node:fs');
const fixture = JSON.parse(fs.readFileSync(0, 'utf8'));

class Element {
  constructor(attrs = {}, tag = '') {
    this.attrs = {...attrs};
    this.tagName = tag.toUpperCase();
    this.hidden = Object.hasOwn(attrs, 'hidden');
    this.disabled = Object.hasOwn(attrs, 'disabled');
    this.value = '';
    this.text = attrs._text || '';
    this.children = [];
    this.listeners = {};
    this.focused = false;
    this.selected = false;
  }
  set textContent(value) { this.text = String(value); this.children = []; }
  get textContent() { return this.text + this.children.map(child => child.textContent).join(''); }
  set innerHTML(value) { throw new Error('Server text must not become HTML'); }
  appendChild(child) { this.children.push(child); return child; }
  replaceChildren() { this.children = []; this.text = ''; }
  setAttribute(name, value) { this.attrs[name] = value; }
  addEventListener(name, handler) { this.listeners[name] = handler; }
  querySelector(selector) { assert.equal(selector, 'button'); return this.button; }
  focus() { this.focused = true; }
  select() { assert.equal(this.focused, true); this.selected = true; }
  click(detail = 1) {
    if (!this.disabled && this.listeners.click) return this.listeners.click({detail});
  }
}

const base = {
  site: 'https://first.example/', pages_checked: 25, truncated: false, from_cache: false,
  issues: [{id: 'meta', label: '14 of the 25 pages read have no meta description',
            count: 14, of: 25, examples: ['/services/', '/about/', '/contact/']}],
  fine: [{id: 'https', label: 'All checked pages use HTTPS'}],
  robots: {found: true, sitemap_found: true}, blocked_by_robots: false,
  checked_at: 'hidden-date', took_ms: 22000, licence_key: 'hidden-licence',
  cookie: 'hidden-cookie', html: '<b>hidden-html</b>', findings: ['hidden-finding']
};
function response(data = base, status = 200) {
  return Promise.resolve({ok: status < 400, json: async () => structuredClone(data)});
}
function setup(fetcher = () => response(), clipboard = 'success') {
  const elements = Object.fromEntries(Object.entries(fixture.ids).map(([id, attrs]) =>
    [id, new Element(attrs, id === 'website-copy' ? 'button' : '')]));
  const button = new Element();
  elements.checker.button = button;
  elements['checker-url'].value = 'first.example';
  const timers = new Map(), writes = [], requests = [], events = [], forbidden = [];
  let timerId = 0;
  const fetch = (...args) => { requests.push(args); return fetcher(...args); };
  const navigator = {};
  if (clipboard !== 'absent') navigator.clipboard = {writeText(text) {
    writes.push(text);
    if (typeof clipboard === 'function') return clipboard(text);
    if (clipboard === 'throw') throw new Error('denied');
    return clipboard === 'reject' ? Promise.reject(new Error('denied')) : Promise.resolve();
  }};
  const context = {
    document: {getElementById: id => elements[id], createElement: tag => new Element({}, tag)},
    window: {fetch, plausible: (...args) => events.push(args)},
    navigator, fetch, URL, AbortController, Date: {now: () => 0},
    setTimeout: (fn, ms) => { timers.set(++timerId, {fn, ms}); return timerId; },
    setInterval: (fn, ms) => { timers.set(++timerId, {fn, ms}); return timerId; },
    clearTimeout: id => timers.delete(id), clearInterval: id => timers.delete(id)
  };
  for (const name of ['localStorage', 'sessionStorage', 'indexedDB', 'caches']) {
    for (const target of [context, context.window]) Object.defineProperty(target, name, {
      get() { forbidden.push(name); throw new Error('No storage'); }
    });
  }
  Object.defineProperty(context.document, 'cookie', {
    get() { forbidden.push('cookie read'); throw new Error('No cookies'); },
    set() { forbidden.push('cookie write'); throw new Error('No cookies'); }
  });
  vm.runInNewContext(fixture.script, context);
  return {
    elements, writes, requests, events, forbidden, button,
    el(id) { return elements[id]; },
    text(id) { return elements[id].textContent; },
    submit(value = 'first.example') {
      elements['checker-url'].value = value;
      return elements.checker.listeners.submit({preventDefault() {}});
    },
    // Native buttons dispatch click with detail 0 for keyboard activation.
    copy(keyboard = false) { return elements['website-copy'].click(keyboard ? 0 : 1); },
    tick(ms) { for (const timer of [...timers.values()]) if (timer.ms === ms) timer.fn(); }
  };
}
function unavailable(state) {
  assert.equal(state.el('website-copy').hidden, true, 'copy hidden without a current summary');
  assert.equal(state.el('website-copy').disabled, true, 'copy disabled without a current summary');
  assert.equal(state.el('website-copy-fallback').hidden, true);
  assert.equal(state.el('website-copy-text').value, '');
  assert.equal(state.text('website-copy-status'), '');
}
function fallback(state) {
  assert.equal(state.el('website-copy-fallback').hidden, false);
  assert.equal(state.el('website-copy-text').focused, true);
  assert.equal(state.el('website-copy-text').selected, true);
  assert.match(state.text('website-copy-status'), /select|selected/i);
  return state.el('website-copy-text').value;
}
function noExtras(state, expected) {
  assert.equal(state.requests.length, expected, 'copy must not fetch');
  assert.deepEqual(state.forbidden, [], 'copy must not use storage or cookies');
  assert.equal(state.events.length, expected, 'copy must not add analytics');
  for (const [url, options] of state.requests) {
    assert.match(url, /^https:\/\/site-check\.kerrco\.workers\.dev\/site-check\?url=/);
    assert.equal(options.credentials, 'omit');
    assert.deepEqual(Object.keys(options).sort(), ['credentials', 'signal']);
  }
}
async function staleRun() {
  // A successful result followed by a failed result must clear even an open fallback.
  let attempt = 0;
  const state = setup(() => ++attempt === 1 ? response() : Promise.reject(new Error('offline')), 'absent');
  await state.submit();
  await state.copy();
  assert.match(fallback(state), /first.example/);
  const pending = state.submit('second.example');
  unavailable(state);
  await state.copy();
  await pending;
  unavailable(state);
  // Dispatch directly as well: a hidden or disabled button is not the only guard.
  await state.el('website-copy').listeners.click({detail: 0});
  assert.equal(state.el('website-copy-text').value, '', 'stale summary leaked');
  assert.equal(state.writes.length, 0);
}
async function consecutiveRun() {
  let attempt = 0;
  const state = setup(() => response(++attempt === 1 ? {...base, from_cache: true} : {
    ...base, site: 'https://second.example/', pages_checked: 2, issues: [], fine: []
  }), 'absent');
  await state.submit();
  await state.copy();
  assert.match(fallback(state), /checked within the last hour/);
  await state.submit('second.example');
  assert.equal(state.el('website-copy-text').value, '');
  assert.equal(state.text('website-copy-status'), '');
  await state.copy();
  const second = fallback(state);
  assert.match(second, /2 pages.*second.example/, 'stale summary leaked into the next copy');
  for (const old of ['first.example', '/services/', 'checked within the last hour', 'What looked fine']) {
    assert.equal(second.includes(old), false, old);
  }
  noExtras(state, 2);
}
async function main() {
  assert.ok(fixture.ids['website-copy'], 'Copy this summary button missing');
  if (fixture.staleOnly) { await consecutiveRun(); return; }
  const success = setup();
  unavailable(success);
  await success.copy();
  assert.equal(success.writes.length, 0);
  await success.submit();
  assert.equal(success.writes.length, 0, 'copy requires a click');
  assert.equal(success.el('website-copy').hidden, false);
  assert.equal(success.el('website-copy').disabled, false);
  await success.copy(true);
  const text = success.writes[0];
  assert.equal(text, [
    success.text('website-heading'), success.text('website-scope'), success.text('website-limit'),
    base.issues[0].label, ...base.issues[0].examples, 'What looked fine', base.fine[0].label,
    success.text('website-robots')
  ].join('\n'));
  assert.match(text, /25 pages.*first.example/);
  assert.match(text, /only the pages read/);
  assert.match(text, /miss pages and issues/);
  for (const hidden of ['hidden-date', '22000', 'hidden-licence', 'hidden-cookie', 'hidden-html', 'hidden-finding']) {
    assert.equal(text.includes(hidden), false, hidden);
  }
  assert.equal(success.text('website-copy-status'), 'Copied.');
  assert.equal(success.el('website-copy-fallback').hidden, true);
  assert.equal(success.el('checker-next').hidden, false);
  noExtras(success, 1);

  for (const mode of ['reject', 'absent', 'throw']) {
    const state = setup(() => response(), mode);
    await state.submit();
    await state.copy(true);
    assert.equal(fallback(state), text);
    assert.equal(state.writes.length, mode === 'absent' ? 0 : 1);
    noExtras(state, 1);
  }
  for (const cached of [true, false]) {
    const state = setup(() => response({...base, from_cache: cached, truncated: true,
      pages_checked: 12, blocked_by_robots: true, robots: {found: false, sitemap_found: false}}));
    await state.submit();
    await state.copy();
    const copied = state.writes[0];
    assert.match(copied, /first 12 pages/);
    assert.match(copied, /Some pages asked not to be checked/);
    assert.match(copied, /did not find robots.txt/);
    assert.match(copied, /did not find a sitemap/);
    assert.equal(copied.includes('checked within the last hour'), cached);
    if (cached) assert.ok(copied.endsWith(state.text('checker-status')));
    noExtras(state, 1);
  }
  const clean = setup(() => response({...base, issues: [], fine: []}));
  await clean.submit();
  await clean.copy();
  assert.match(clean.writes[0], /No issues were found by this quick check on the pages read/);
  assert.equal(clean.writes[0].includes('What looked fine'), false);

  const unsafe = '<img src=x onerror=alert(1)> & "quoted" </textarea><script>bad()</script>';
  const limits = setup(() => response({...base, site: 'https://labels.example/?q=' + unsafe,
    issues: Array.from({length: 9}, (_, i) => ({...base.issues[0],
      label: i === 8 ? 'hidden-ninth-issue' : unsafe,
      examples: [unsafe, '/two/', '/three/', '/hidden-fourth-example/']})),
    fine: Array.from({length: 6}, (_, i) => ({label: i === 5 ? 'hidden-sixth-fine' : unsafe}))
  }), 'absent');
  await limits.submit();
  await limits.copy();
  const limited = fallback(limits);
  assert.ok(limited.includes(unsafe)); // Literal text, never parsed as markup.
  assert.ok(limits.text('website-issues').includes(unsafe));
  assert.equal(limits.el('website-issues').children.length, 8);
  assert.equal(limits.el('website-fine').children.length, 5);
  assert.equal(limits.el('website-issues').children[0].children[0].children.length, 3);
  for (const hidden of ['hidden-ninth-issue', 'hidden-fourth-example', 'hidden-sixth-fine']) {
    assert.equal(limited.includes(hidden), false, hidden);
  }
  noExtras(limits, 1);

  await staleRun();
  for (const failure of [
    () => response({refused: true}),
    () => response({error: 'denied', message: 'No access'}, 403),
    () => response({error: 'failed', message: 'Try later'}, 503),
    () => Promise.reject(new Error('offline')),
    () => Promise.resolve({ok: true, json: async () => { throw new Error('bad JSON'); }}),
    () => response({...base, pages_checked: 0, issues: [], fine: []})
  ]) {
    let attempt = 0;
    const state = setup(() => ++attempt === 1 ? response() : failure());
    await state.submit();
    await state.copy();
    const pending = state.submit('second.example');
    unavailable(state);
    await pending;
    unavailable(state);
    await state.copy();
    await state.el('website-copy').listeners.click({detail: 0});
    assert.equal(state.writes.length, 1, 'failed check copied an old result');
  }
  for (const invalid of ['', 'ftp://invalid.example', 'https://']) {
    const state = setup();
    await state.submit();
    await state.copy();
    await state.submit(invalid);
    unavailable(state);
    await state.el('website-copy').listeners.click({detail: 0});
    assert.equal(state.writes.length, 1);
    assert.equal(state.requests.length, 1);
  }
  let count = 0, finishFetch;
  const timeout = setup(() => ++count === 1 ? response() : new Promise(resolve => { finishFetch = resolve; }));
  await timeout.submit();
  await timeout.copy();
  const pending = timeout.submit('second.example');
  unavailable(timeout);
  timeout.tick(45000);
  await pending;
  unavailable(timeout);
  assert.match(timeout.text('checker-status'), /longer than 45 seconds/);
  finishFetch(await response({...base, site: 'https://late.example/'}));
  await new Promise(resolve => setImmediate(resolve));
  await timeout.el('website-copy').listeners.click({detail: 0});
  assert.equal(timeout.writes.length, 1);

  await consecutiveRun();

  // Clipboard promises may settle after a new check, even with the same site text.
  for (const rejected of [false, true]) {
    let resolveCopy, rejectCopy;
    const race = setup(() => response(), () => new Promise((resolve, reject) => {
      resolveCopy = resolve; rejectCopy = reject;
    }));
    await race.submit();
    const copying = race.copy();
    await race.submit();
    if (rejected) rejectCopy(new Error('denied')); else resolveCopy();
    await copying;
    assert.equal(race.text('website-copy-status'), '');
    assert.equal(race.el('website-copy-fallback').hidden, true);
    assert.equal(race.el('website-copy-text').value, '');
    assert.equal(race.el('website-copy').disabled, false);
    noExtras(race, 2);
  }
  console.log('COPY JS ok: shown text, limits, cache, truncation, safe labels, clipboard and keyboard click');
  console.log('COPY JS ok: fallback selection, empty, refusal, errors, timeout, consecutive results, late clipboard');
  console.log('COPY JS ok: no extra fetch, analytics, storage or cookie access');
}
main().catch(error => { console.error(error); process.exitCode = 1; });
"""


def run(destination, command, *, expected=0, payload=None):
    env = dict(os.environ, DOCKET_SKIP_BRAND_ASSETS='1', PYTHONDONTWRITEBYTECODE='1',
               TZ='UTC', **{ACTIVE: '1'})
    env.pop('DOCKET_DEPLOY', None)
    env.pop('SITE_BRAND', None)
    completed = subprocess.run(command, cwd=destination, env=env, input=payload,
                               capture_output=True, text=True, timeout=240)
    shown = command[:2] + ['<emitted-script tests>'] if command[:2] == ['node', '-e'] else command
    print('$ ' + ' '.join(shown), flush=True)
    output = completed.stdout + completed.stderr
    print('\n'.join(line for line in output.splitlines() if not line.startswith('  site/')))
    print(f'exit {completed.returncode}', flush=True)
    if completed.returncode != expected:
        raise SystemExit(completed.returncode or 1)
    return completed


def main():
    if os.environ.get(ACTIVE):
        raise SystemExit('Refusing recursive copy-summary gate invocation')
    base = subprocess.run(['git', 'show', BASE + ':site/tools/website-checker/index.html'],
                          cwd=ROOT, capture_output=True, text=True, check=True).stdout
    old = fixture(base)
    assert 'website-copy' not in old['ids'], 'base already has the copy button'
    assert 'Copy this summary' not in base
    print(f'BASE ok: copy button absent at {BASE}', flush=True)
    anchor = (ROOT / 'data/build-id.txt').read_bytes()
    with tempfile.TemporaryDirectory(prefix='test-copy-quick-check-') as temporary:
        destination = Path(temporary)
        scratch_copy(destination)
        run(destination, [sys.executable, '-B', 'scripts/build.py'])
        raw = (destination / 'site' / ROUTE.strip('/') / 'index.html').read_text()
        current = fixture(raw)
        ids = current['ids']
        assert 'website-copy' in ids, 'Copy this summary button missing'
        assert ids['website-copy']['type'] == 'button'
        assert ids['website-copy']['_text'] == 'Copy this summary'
        assert 'hidden' in ids['website-copy'] and 'disabled' in ids['website-copy']
        # The shared .btn-ghost display rule overrides the browser's hidden style.
        assert '#website-copy[hidden]{display:none}' in raw
        section = re.search(r'<section\b[^>]*id="website-result".*?</section>', raw, re.S)[0]
        assert 'id="website-copy"' in section
        assert ids['website-copy-status']['role'] == 'status'
        assert ids['website-copy-status']['aria-live'] == 'polite'
        assert 'hidden' in ids['website-copy-fallback']
        assert 'readonly' in ids['website-copy-text']
        assert 'disabled' not in ids['website-copy-text']
        assert '<label for="website-copy-text">Summary to copy</label>' in section
        # Existing app step, endpoint, fetch policy and analytics stay byte-for-byte intact.
        next_step = r'<div class="checker-next".*?</div>\s*</div>'
        assert re.search(next_step, raw, re.S)[0] == re.search(next_step, base, re.S)[0]
        for pattern in (r"const ENDPOINT = [^;]+;", r"const response = fetch\(.*?\n      \}\);",
                        r"if \(window.plausible\).*?\n      \}\);"):
            assert re.search(pattern, current['script'], re.S)[0] == re.search(pattern, old['script'], re.S)[0]
        page = Page(raw)
        assert [(t, a) for t, a in page.tags if t == 'script' and 'src' in a] == [
            (t, a) for t, a in Page(base).tags if t == 'script' and 'src' in a]
        run(destination, ['node', '-e', NODE_TEST], payload=json.dumps(current))
        # Plant a copy handler that reuses the preceding site's summary.
        mutant = dict(current, staleOnly=True)
        assert current['script'].count('const text = summary;') == 1
        mutant['script'] = current['script'].replace(
            'const text = summary;',
            'const text = window.oldSummary || summary; window.oldSummary = text;', 1)
        control = run(destination, ['node', '-e', NODE_TEST], expected=1, payload=json.dumps(mutant))
        assert 'stale summary leaked into the next copy' in control.stderr, control.stderr
        print('CONTROL ok: stale-summary mutation failed with exit 1', flush=True)
        for command in (
            [sys.executable, '-B', 'scripts/test_website_checker_page.py'],
            [sys.executable, '-B', 'scripts/lint.py', 'site'],
            [sys.executable, '-B', 'scripts/test_chatgpt_app_links.py'],
            [sys.executable, '-B', 'scripts/verify_structured_data_matches_page.py'],
        ):
            run(destination, command)
    assert (ROOT / 'data/build-id.txt').read_bytes() == anchor
    print('COPY QUICK CHECK ok: temp builds, emitted JS, base absence, failing stale control, all gates')


if __name__ == '__main__':
    main()
