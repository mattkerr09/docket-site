#!/usr/bin/env python3
"""Offline page gate. Build only in a scratch copy and run its JS with fake fetch."""
from __future__ import annotations

import csv
from html.parser import HTMLParser
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
from urllib.parse import parse_qs, urlsplit

ROOT = Path(__file__).resolve().parent.parent
ROUTE = '/tools/website-checker/'


class Page(HTMLParser):
    def __init__(self, raw):
        super().__init__(convert_charrefs=True)
        self.tags = []
        self.words = []
        self.scripts = []
        self.hidden = ''
        self.script = ''
        self.feed(raw)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        self.tags.append((tag, attrs))
        if tag in {'script', 'style'}:
            self.hidden = tag
            self.script = ''

    def handle_endtag(self, tag):
        if tag == self.hidden:
            if tag == 'script':
                self.scripts.append(self.script)
            self.hidden = ''

    def handle_data(self, data):
        if self.hidden == 'script':
            self.script += data
        elif not self.hidden:
            self.words.append(data)


def scratch_copy(destination):
    for directory in ('scripts', 'data', 'site', 'workers'):
        shutil.copytree(ROOT / directory, destination / directory,
                        ignore=shutil.ignore_patterns('__pycache__', '*.env', '*.env.*',
                                                     'node_modules', '.DS_Store'))


def run(destination, command):
    env = dict(os.environ, DOCKET_SKIP_BRAND_ASSETS='1', TZ='UTC', PYTHONDONTWRITEBYTECODE='1')
    env.pop('DOCKET_DEPLOY', None)
    env.pop('SITE_BRAND', None)
    completed = subprocess.run(command, cwd=destination, env=env, capture_output=True, text=True)
    output = completed.stdout + completed.stderr
    print('$ ' + ' '.join(command))
    shown = output if completed.returncode else '\n'.join(
        line for line in output.splitlines() if not line.startswith('  site/'))
    print(shown)
    print(f'exit {completed.returncode}')
    assert completed.returncode == 0, output
    return output


def check_page(destination):
    site = destination / 'site'
    raw = (site / ROUTE.strip('/') / 'index.html').read_text()
    page = Page(raw)
    title = re.search(r'<title>(.*?)</title>', raw)[1]
    assert title == 'Free website checker: check up to 25 pages of your site'
    assert len(title) <= 60
    assert f'<h1>{title}</h1>' in raw
    assert ('link', {'rel': 'canonical', 'href': 'https://checkengineseo.com' + ROUTE}) in page.tags
    ids = {attrs['id']: attrs for tag, attrs in page.tags if 'id' in attrs}
    assert 'checker' in ids and 'action' not in ids['checker'] and 'method' not in ids['checker']
    assert ids['checker-url']['name'] == 'url'
    assert any(tag == 'button' and attrs.get('type') == 'submit' and 'disabled' in attrs
               for tag, attrs in page.tags)
    assert ids['checker-status']['aria-live'] == 'polite'
    assert 'hidden' in ids['website-result'] and 'hidden' in ids['checker-next']
    assert ids['website-result']['aria-labelledby'] == 'website-heading'
    assert sum(attrs.get('class') == 'faq-item' for tag, attrs in page.tags) == 7
    schema = [json.loads(script) for script in page.scripts if script.lstrip().startswith('{')]
    assert any(block.get('@type') == 'WebPage' for block in schema)
    faq = next(block for block in schema if block.get('@type') == 'FAQPage')
    assert len(faq['mainEntity']) == 7
    assert any(tag == 'img' and attrs.get('width') and attrs.get('height')
               and attrs.get('src') == '/assets/sample-report-cover.webp' for tag, attrs in page.tags)
    words = ' '.join(' '.join(page.words).split())
    for phrase in ('one-hour cached summary', 'CheckEngineBot', 'robots.txt', '99 checks', '13 areas'):
        assert phrase in words, phrase

    sys.path.insert(0, str(destination / 'scripts'))
    from lint import BANNED
    for phrase in BANNED + ['seamless', 'unleash', 'unlock', 'empower', 'leverage', 'streamline',
                            'lifetime', 'perpetual', 'cheap', 'affordable']:
        assert not re.search(r'(?<!\w)' + re.escape(phrase) + r'(?!\w)', words, re.I), phrase
    links = [attrs for tag, attrs in page.tags if tag == 'a']
    sibling = ('crispvideo.app', 'outlier.host', 'counttwice.app', 'mindtheminutes.com',
               'scoutseo.app', 'docketseo.app', 'builtbykerr.com')
    assert not any(urlsplit(link.get('href', '')).hostname in sibling for link in links)
    assert sum(urlsplit(link.get('href', '')).hostname == 'kerrandcompanyholdings.com' for link in links) == 1
    assert raw.index('href="https://kerrandcompanyholdings.com') > raw.index('<footer')
    downloads = [link for link in links if '/dl/docket?' in link.get('href', '')
                 and parse_qs(urlsplit(link['href']).query).get('src', [''])[0].startswith('tools-website-checker')]
    assert downloads
    for link in downloads:
        assert link['data-ev'] == 'Download'
        assert link['data-ev-button'].startswith('tools-website-checker')
        assert parse_qs(urlsplit(link['href']).query)['src'][0] == link['data-ev-button']
    assert 'https://checkengineseo.com' + ROUTE in (site / 'sitemap.xml').read_text()
    assert f'href="{ROUTE}"' in (site / 'tools/index.html').read_text()
    assert f'href="{ROUTE}"' in (site / 'tools/seo-checker/index.html').read_text()
    for slug in ('robots-txt-tester', 'meta-tag-checker', 'json-ld-checker', 'serp-preview',
                 'redirect-checker', 'http-header-checker'):
        assert f'href="{ROUTE}"' in (site / 'tools' / slug / 'index.html').read_text(), slug
    graph = json.loads((destination / 'data/link-equity.json').read_text())
    node = next(node for node in graph['nodes'] if node['path'] == ROUTE)
    assert node['inlinks'] >= 8
    script = next(script for script in page.scripts if 'const ENDPOINT =' in script)
    assert script.count('https://site-check.kerrco.workers.dev') == 1
    assert script.index('const ENDPOINT =') < script.index('const form =')
    for phrase in BANNED:
        assert phrase not in script.lower(), phrase
    with (destination / 'data/checks.csv').open() as file:
        checks = list(csv.DictReader(file))
    assert f'runs {len(checks)} checks across {len({row["lane"] for row in checks})} areas.' in script
    return script, ids


NODE_TEST = r"""
const assert = require('node:assert/strict');
const vm = require('node:vm');
const fs = require('node:fs');
const fixture = JSON.parse(fs.readFileSync(0, 'utf8'));

class Element {
  constructor(attrs = {}) {
    this.hidden = Object.hasOwn(attrs, 'hidden');
    this.attrs = {...attrs};
    this.children = [];
    this.text = '';
    this.disabled = false;
    this.value = '';
    this.listeners = {};
  }
  set textContent(text) { this.text = String(text); this.children = []; }
  get textContent() { return this.text + this.children.map(child => child.textContent).join(' '); }
  set innerHTML(value) { throw new Error('Use textContent for server text'); }
  appendChild(child) { this.children.push(child); }
  replaceChildren() { this.children = []; this.text = ''; }
  addEventListener(name, listener) { this.listeners[name] = listener; }
  setAttribute(name, value) { this.attrs[name] = value; }
  querySelector(selector) { assert.equal(selector, 'button'); return this.button; }
}

const base = {
  site: 'https://example.com/', pages_checked: 25, truncated: false, blocked_by_robots: false,
  issues: [{id: 'meta', label: 'have no meta description', count: 14, of: 25,
            examples: ['/services/', '/about/', '/contact/']}],
  fine: [{id: 'https', label: 'All checked pages use HTTPS'}],
  robots: {found: true, sitemap_found: true},
  checked_at: '2026-11-10T15:00:00Z', took_ms: 22000, from_cache: false
};
function setup(fetcher) {
  const elements = Object.fromEntries(Object.entries(fixture.ids).map(([id, attrs]) => [id, new Element(attrs)]));
  const button = new Element();
  elements.checker.button = button;
  elements['checker-url'].value = 'example.com';
  const timers = new Map();
  let timerId = 0, now = 0;
  const events = [], requests = [];
  const fetch = (...args) => { requests.push(args); return fetcher(...args); };
  const context = {
    document: {getElementById: id => elements[id], createElement: () => new Element()},
    window: {fetch, plausible: (...args) => events.push(args)}, fetch, URL, AbortController,
    Date: {now: () => now},
    setTimeout: (fn, ms) => { timers.set(++timerId, {fn, ms, repeat: false}); return timerId; },
    setInterval: (fn, ms) => { timers.set(++timerId, {fn, ms, repeat: true}); return timerId; },
    clearTimeout: id => timers.delete(id), clearInterval: id => timers.delete(id)
  };
  vm.runInNewContext(fixture.script, context);
  return {
    elements, button, events, requests, timers,
    submit() { return elements.checker.listeners.submit({preventDefault() {}}); },
    tick(ms) {
      now += ms;
      for (const [id, timer] of [...timers]) {
        if (timer.ms <= ms && timers.has(id)) {
          if (!timer.repeat) timers.delete(id);
          timer.fn();
        }
      }
    },
    text(id) { return elements[id].textContent; }
  };
}
function response(data = base, status = 200) {
  return Promise.resolve({ok: status < 400, json: async () => structuredClone(data)});
}
function finished(state, visible) {
  assert.equal(state.button.disabled, false);
  assert.equal(state.timers.size, 0);
  assert.equal(state.elements['website-result'].attrs['aria-busy'], 'false');
  assert.equal(state.elements['website-result'].hidden, !visible);
  assert.equal(state.elements['checker-next'].hidden, !visible);
}
async function main() {
  const success = setup(() => response());
  await success.submit();
  finished(success, true);
  assert.equal(success.text('website-heading'), 'What a quick check of 25 pages found');
  assert.match(success.text('website-issues'), /14 of 25 pages have no meta description/);
  // The Worker sends a full sentence that already starts with the counts: it must not be prefixed a second time.
  const worker = setup(() => response({...base, issues: [{id: 'meta', label: '14 of the 25 pages read have no meta description', count: 14, of: 25, examples: ['/a/']}]}));
  await worker.submit();
  assert.equal(worker.text('website-issues').match(/14 of/g).length, 1);
  assert.match(worker.text('website-issues'), /14 of the 25 pages read have no meta description/);
  assert.match(success.text('website-issues'), /\/services\//);
  assert.match(success.text('website-fine'), /All checked pages use HTTPS/);
  assert.match(success.text('checker-own'), /This quick check read 25 pages\. Check Engine reads every page and runs 99 checks across 13 areas\./);
  assert.match(success.requests[0][0], /^https:\/\/site-check\.kerrco\.workers\.dev\/site-check\?url=https%3A%2F%2Fexample\.com%2F$/);
  assert.equal(success.requests[0][1].credentials, 'omit');
  assert.equal(success.events[0][0], 'Checker');
  assert.equal(success.events[0][1].props.tool, 'website');
  assert.equal(success.events[0][1].props.issues, '1');
  assert.equal(JSON.stringify(success.events).includes('example.com'), false);
  const ranked = setup(() => response({...base, issues: [
    {...base.issues[0], label: 'have the first ranked issue'},
    {...base.issues[0], count: 20, label: 'have the second ranked issue'}
  ]}));
  await ranked.submit();
  assert.match(ranked.elements['website-issues'].children[0].textContent, /first ranked issue/);
  assert.match(ranked.elements['website-issues'].children[1].textContent, /second ranked issue/);

  const clean = setup(() => response({...base, issues: [], fine: []}));
  await clean.submit();
  finished(clean, true);
  assert.match(clean.text('website-clean'), /No issues were found by this quick check on the pages read/);
  assert.equal(clean.text('website-issues'), '');
  assert.equal(clean.elements['website-fine-heading'].hidden, true);
  assert.equal(clean.events[0][1].props.issues, '0');

  const truncated = setup(() => response({...base, pages_checked: 12, truncated: true,
    issues: [{...base.issues[0], count: 7, of: 12}],
    blocked_by_robots: true, robots: {found: false, sitemap_found: false}}));
  await truncated.submit();
  finished(truncated, true);
  assert.match(truncated.text('website-scope'), /the first 12 pages/);
  assert.match(truncated.text('website-issues'), /7 of 12 pages have no meta description/);
  assert.match(truncated.text('checker-own'), /read 12 pages/);
  assert.match(truncated.text('website-robots'), /Some pages asked not to be checked/);
  assert.match(truncated.text('website-robots'), /did not find robots.txt/);
  assert.match(truncated.text('website-robots'), /did not find a sitemap/);

  const refused = setup(() => response({site: base.site, refused: true, reason: 'robots.txt'}));
  await refused.submit();
  finished(refused, false);
  assert.equal(refused.text('checker-status'), 'This site asked not to be checked, so we did not look.');
  assert.equal(refused.events.length, 0);
  for (const status of [400, 403, 429, 503]) {
    const message = `Server message for ${status}. <b>Keep this text.</b>`;
    const error = setup(() => response({error: 'machine_code', message}, status));
    await error.submit();
    finished(error, false);
    assert.equal(error.text('checker-status'), message);
    assert.equal(error.events.length, 0);
    assert.equal(error.text('checker-status').includes('machine_code'), false);
  }
  const network = setup(() => Promise.reject(new Error('secret stack trace')));
  await network.submit();
  finished(network, false);
  assert.equal(network.text('checker-status'), 'The checker could not be reached. Check your connection and try again in a minute.');

  let resolveFetch;
  const timeout = setup(() => new Promise(resolve => { resolveFetch = resolve; }));
  const pending = timeout.submit();
  assert.equal(timeout.button.disabled, true);
  assert.equal(timeout.text('checker-status'), 'Reading up to 25 pages of example.com. This takes about 30 seconds. 0 seconds elapsed.');
  timeout.tick(1000);
  assert.match(timeout.text('checker-status'), /1 seconds elapsed/);
  await timeout.submit();
  assert.equal(timeout.requests.length, 1);
  timeout.tick(45000);
  await pending;
  finished(timeout, false);
  assert.equal(timeout.requests[0][1].signal.aborted, true);
  assert.equal(timeout.text('checker-status'), 'The check took longer than 45 seconds, so we stopped waiting. Try again in a minute.');
  resolveFetch(await response());
  await new Promise(resolve => setImmediate(resolve));
  finished(timeout, false);

  let attempt = 0;
  const retry = setup(() => ++attempt === 1 ? response() : Promise.reject(new Error('offline')));
  await retry.submit();
  await retry.submit();
  finished(retry, false);
  assert.equal(retry.events.length, 1);
  let checks = 0;
  const recheck = setup(() => response(++checks === 1 ? base : {...base, issues: [], fine: []}));
  await recheck.submit();
  await recheck.submit();
  finished(recheck, true);
  assert.equal(recheck.text('website-issues'), '');
  assert.equal(recheck.text('website-fine'), '');

  const slowBody = setup(() => Promise.resolve({ok: true, json: () => new Promise(() => {})}));
  const readingBody = slowBody.submit();
  await new Promise(resolve => setImmediate(resolve));
  slowBody.tick(45000);
  await readingBody;
  finished(slowBody, false);
  assert.match(slowBody.text('checker-status'), /longer than 45 seconds/);

  const cached = setup(() => response({...base, from_cache: true}));
  await cached.submit();
  assert.match(cached.text('checker-status'), /checked within the last hour/);
  const zero = setup(() => response({...base, pages_checked: 0, issues: [], fine: []}));
  await zero.submit();
  assert.match(zero.text('website-clean'), /No pages were read/);

  const unsafe = '<img src=x onerror=alert(1)>';
  const limits = setup(() => response({...base,
    issues: Array.from({length: 9}, () => ({...base.issues[0], label: unsafe, examples: [unsafe, '/b', '/c', '/excluded']})),
    fine: Array.from({length: 6}, () => ({id: 'fine', label: unsafe}))}));
  await limits.submit();
  assert.equal(limits.elements['website-issues'].children.length, 8);
  assert.equal(limits.elements['website-fine'].children.length, 5);
  assert.equal(limits.elements['website-issues'].children[0].children[0].children.length, 3);
  assert.match(limits.text('website-issues'), /<img src=x onerror=alert\(1\)>/);
  assert.equal(limits.text('website-issues').includes('/excluded'), false);

  for (const value of ['', 'ftp://example.com', 'https://']) {
    const invalid = setup(() => { throw new Error('must not fetch'); });
    invalid.elements['checker-url'].value = value;
    await invalid.submit();
    assert.equal(invalid.requests.length, 0);
    assert.equal(invalid.button.disabled, false);
    assert.match(invalid.text('checker-status'), /Enter a/);
  }
  const port = setup(() => response());
  port.elements['checker-url'].value = 'example.com:8080';
  await port.submit();
  assert.equal(new URL(port.requests[0][0]).searchParams.get('url'), 'https://example.com:8080/');
  console.log('JS ok - success, clean, truncated, refused, 400, 403, 429, 503, network, timeout');
  console.log('JS ok - elapsed time, limits, cache, empty check, safe text, duplicate submit, retry, late response');
}
main().catch(error => { console.error(error); process.exitCode = 1; });
"""


def main():
    anchor = (ROOT / 'data/build-id.txt').read_bytes()
    with tempfile.TemporaryDirectory(prefix='test-website-checker-') as temporary:
        destination = Path(temporary)
        scratch_copy(destination)
        run(destination, [sys.executable, 'scripts/build.py'])
        run(destination, [sys.executable, 'scripts/verify_link_graph.py'])
        script, ids = check_page(destination)
        node = subprocess.run(['node', '-e', NODE_TEST], input=json.dumps({'script': script, 'ids': ids}),
                              text=True, capture_output=True)
        print(node.stdout + node.stderr, end='')
        assert node.returncode == 0, f'node exit {node.returncode}'
        run(destination, [sys.executable, 'scripts/verify_no_named_third_parties.py'])
        run(destination, [sys.executable, 'scripts/verify_privacy_scripts.py', '--self-test'])
    assert (ROOT / 'data/build-id.txt').read_bytes() == anchor
    print('WEBSITE CHECKER ok - scratch build, page, fake-fetch states, links, privacy')


if __name__ == '__main__':
    main()
