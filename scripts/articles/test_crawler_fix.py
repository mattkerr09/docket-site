#!/usr/bin/env python3
"""Offline checks for the crawler fix and the tool's browser result."""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import unittest
from unittest.mock import patch

from crawler_fix import AI_SEARCH_CRAWLERS, FIX_JS, search_names
import tool_ai_crawlers as tool

NODE = shutil.which("node")
SEARCH_NAMES = search_names(tool._crawlers())
HEADER = "# Let AI search crawlers read your site (they are not training crawlers)"


@unittest.skipUnless(NODE, "node was not found on PATH; skipping browser JavaScript cases")
class CrawlerFixTests(unittest.TestCase):
    def build_fix(self, results, search_names=SEARCH_NAMES):
        source = FIX_JS + "\nconsole.log(JSON.stringify(buildCrawlerFix(" + json.dumps(results)
        source += ", " + json.dumps(search_names) + ")));"
        result = subprocess.run([NODE, "-e", source], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        return json.loads(result.stdout)

    def test_all_allowed(self):
        results = [{"agent": name, "allowed": True} for name in ["Googlebot", *SEARCH_NAMES]]
        self.assertEqual(self.build_fix(results), {
            "googleBlocked": False, "byWildcard": [], "byName": [], "byServer": [], "snippet": "",
        })

    def test_wildcard_exact_snippet(self):
        results = [{"agent": name, "allowed": False, "governedBy": "wildcard"}
                   for name in ("OAI-SearchBot", "PerplexityBot")]
        fix = self.build_fix(results)
        self.assertEqual(fix, {
            "googleBlocked": False, "byWildcard": ["OAI-SearchBot", "PerplexityBot"],
            "byName": [], "byServer": [],
            "snippet": HEADER + "\nUser-agent: OAI-SearchBot\nAllow: /\n\nUser-agent: PerplexityBot\nAllow: /",
        })

    def test_named_crawler_excluded_from_snippet(self):
        fix = self.build_fix([
            {"agent": "OAI-SearchBot", "allowed": False, "governedBy": "name"},
            {"agent": "PerplexityBot", "allowed": False, "governedBy": "wildcard"},
        ])
        self.assertEqual(fix["byName"], ["OAI-SearchBot"])
        self.assertEqual(fix["snippet"], HEADER + "\nUser-agent: PerplexityBot\nAllow: /")

    def test_google_blocks_snippet(self):
        fix = self.build_fix([
            {"agent": "Googlebot", "allowed": False},
            {"agent": "OAI-SearchBot", "allowed": False, "governedBy": "wildcard"},
        ])
        self.assertTrue(fix["googleBlocked"])
        self.assertEqual(fix["byWildcard"], ["OAI-SearchBot"])
        self.assertEqual(fix["snippet"], "")

    def test_training_and_google_extended_ignored(self):
        for name in ("GPTBot", "Google-Extended"):
            for governance in ("wildcard", "name", "status"):
                with self.subTest(name=name, governance=governance):
                    fix = self.build_fix([{"agent": name, "allowed": False, "governedBy": governance}])
                    self.assertEqual(fix, {
                        "googleBlocked": False, "byWildcard": [], "byName": [], "byServer": [], "snippet": "",
                    })

    def test_server_governance(self):
        for governance in ("none", "status", None):
            with self.subTest(governance=governance):
                fix = self.build_fix([{"agent": "OAI-SearchBot", "allowed": False, "governedBy": governance}])
                self.assertEqual(fix["byServer"], ["OAI-SearchBot"])
                self.assertEqual(fix["byWildcard"], [])
                self.assertEqual(fix["byName"], [])
                self.assertEqual(fix["snippet"], "")

    def test_unlisted_and_missing_agents_ignored(self):
        fix = self.build_fix([
            {"agent": "other-crawler", "allowed": False, "governedBy": "wildcard"},
            {"allowed": False, "governedBy": "wildcard"}, {},
        ])
        self.assertEqual(fix, {
            "googleBlocked": False, "byWildcard": [], "byName": [], "byServer": [], "snippet": "",
        })

    def test_only_false_is_blocked_and_inputs_stay_unchanged(self):
        source = FIX_JS + r"""
const assert = require('node:assert/strict');
const results = Object.freeze([
  Object.freeze({agent: 'OAI-SearchBot', allowed: null, governedBy: 'wildcard'}),
  Object.freeze({agent: 'PerplexityBot', allowed: 0, governedBy: 'wildcard'})
]);
const names = Object.freeze(['OAI-SearchBot', 'PerplexityBot']);
assert.equal(buildCrawlerFix(results, names).snippet, '');
assert.deepEqual(buildCrawlerFix(results, names), buildCrawlerFix(results, names));
"""
        result = subprocess.run([NODE, "-e", source], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_tool_browser_fix_and_copy(self):
        with patch.object(tool, "render", side_effect=lambda **kwargs: kwargs):
            body = tool.checker()["body"]
        script = re.search(r"<script>(.*?)</script>", body, re.S)[1]
        self.assertIn(FIX_JS, script)
        self.assertEqual(json.loads(re.search(r"var SEARCH_NAMES = (.*?);", script)[1]), SEARCH_NAMES)
        self.assertLess(body.index('id="checker-fix"'), body.index('id="checker-next"'))
        self.assertEqual(body.count("This reads your robots.txt only."), 1)
        # The existing badge preview uses only a validated host. Results must stay text.
        self.assertEqual([line.strip() for line in script.splitlines() if "innerHTML" in line],
                         ["document.getElementById('share-preview').innerHTML = badge(url);"])
        source = r"""
const assert = require('node:assert/strict');
const vm = require('node:vm');
const source = __SOURCE__;
function setup(clipboard = true, analytics = true, fetcher) {
  const elements = {}, events = [], copied = [], handlers = {}, buttons = [], calls = [];
  let results = [], error = false, selected;
  function element(id) {
    if (!elements[id]) elements[id] = {textContent: '', hidden: true};
    return elements[id];
  }
  const form = {addEventListener: (name, fn) => handlers[name] = fn};
  elements.checker = form;
  for (const [id, what] of [['share-url', 'link'], ['share-badge', 'badge'], ['checker-fix-snippet', 'fix']]) {
    const button = {textContent: 'Copy', getAttribute: name => name === 'data-copy' ? id : what,
      addEventListener: (name, fn) => button.click = fn};
    if (what !== 'fix') {
      element(id).value = '';
      element(id).select = () => selected = element(id);
    }
    buttons.push(button);
  }
  const document = {getElementById: element,
    querySelectorAll: selector => selector === '[data-copy]' ? buttons : [],
    createRange: () => ({selectNodeContents: el => selected = el}),
    execCommand: command => {assert.equal(command, 'copy'); copied.push(selected.value ?? selected.textContent);}};
  const fetch = async url => {
    calls.push(url);
    if (fetcher) return fetcher();
    return {ok: !error, json: async () => error ? {error: 'Try again later.'} :
      {state: 'parsed', robots_url: 'https://example.com/robots.txt', results}};
  };
  const window = {fetch, getSelection: () => ({removeAllRanges() {}, addRange() {}})};
  if (analytics) window.plausible = (...args) => events.push(args);
  const navigator = clipboard ? {clipboard: {writeText: async text => copied.push(text)}} : {};
  vm.runInNewContext(source, {document, fetch, window, navigator, URL, URLSearchParams,
    encodeURIComponent, location: {search: '', pathname: '/', hash: ''}, history: {replaceState() {}},
    setTimeout: fn => fn()});
  async function submit(rows, value = 'example.com', failed = false) {
    results = rows;
    error = failed;
    element('checker-url').value = value;
    handlers.submit({preventDefault() {}});
    await new Promise(resolve => setImmediate(resolve));
  }
  return {element, events, copied, buttons, calls, submit};
}
async function main() {
  const s = setup();
  const wildcard = {agent: 'OAI-SearchBot', allowed: false, governedBy: 'wildcard'};
  await s.submit([wildcard, {agent: 'GPTBot', allowed: false, governedBy: 'wildcard'}]);
  assert.equal(s.calls.length, 1);
  assert.equal(new URL(s.calls[0]).searchParams.get('url'), 'example.com');
  assert.equal(s.element('checker-fix').hidden, false);
  assert.equal(s.element('checker-fix-wildcard').hidden, false);
  assert.equal(s.element('checker-fix-google').hidden, true);
  const snippet = s.element('checker-fix-snippet').textContent;
  assert.equal(snippet, __SNIPPET__);
  s.buttons[2].click();
  assert.deepEqual(s.copied, [snippet]);
  assert.deepEqual(s.events.at(-1), ['fix_copied']);
  s.buttons[0].click();
  assert.equal(s.events.at(-1)[0], 'Checker share');
  assert.equal(s.copied.at(-1), __SHARE_URL__);
  await s.submit([wildcard, {agent: 'Claude-SearchBot', allowed: false, governedBy: 'name'},
    {agent: 'PerplexityBot', allowed: false, governedBy: 'status'}]);
  assert.equal(s.element('checker-fix-name').hidden, false);
  assert(s.element('checker-fix-name').textContent.includes('decision: Claude-SearchBot.'));
  assert.equal(s.element('checker-fix-server').hidden, false);
  assert(s.element('checker-fix-server').textContent.endsWith('PerplexityBot. Make /robots.txt answer 200 or 404.'));
  assert.equal(s.element('checker-fix-snippet').textContent, snippet);
  await s.submit([wildcard, {agent: 'Googlebot', allowed: false}]);
  assert.equal(s.element('checker-fix-google').hidden, false);
  assert.equal(s.element('checker-fix-wildcard').hidden, true);
  assert.equal(s.element('checker-fix-snippet').textContent, '');
  for (const rows of [[], [{agent: 'GPTBot', allowed: false}], [{agent: 'Google-Extended', allowed: false}],
    [{agent: 'OAI-SearchBot', allowed: true}]]) {
    await s.submit(rows);
    assert.equal(s.element('checker-fix').hidden, true);
    assert.equal(s.element('checker-fix-snippet').textContent, '');
  }
  for (const [value, failed] of [['', false], ['example.com', true]]) {
    await s.submit([wildcard]);
    await s.submit([], value, failed);
    assert.equal(s.element('checker-fix').hidden, true);
    assert.equal(s.element('checker-fix-snippet').textContent, '');
  }
  for (const clipboard of [false, true]) {
    const fallback = setup(clipboard, false);
    await fallback.submit([wildcard]);
    fallback.buttons[2].click();
    assert.deepEqual(fallback.copied, [snippet]);
    if (!clipboard) {
      fallback.buttons[0].click();
      assert(fallback.copied.at(-1).endsWith('?d=example.com'));
    }
  }
  let finish;
  const racing = setup(true, true, () => new Promise(resolve => finish = resolve));
  await racing.submit([], 'first.example');
  const first = finish;
  await racing.submit([], 'second.example');
  finish({ok: true, json: async () => ({state: 'parsed', results: []})});
  await new Promise(resolve => setImmediate(resolve));
  first({ok: true, json: async () => ({state: 'parsed', results: [wildcard]})});
  await new Promise(resolve => setImmediate(resolve));
  assert.equal(racing.element('checker-fix').hidden, true);
  assert.equal(racing.element('checker-fix-snippet').textContent, '');
  assert.equal(racing.events.length, 1);
}
main().catch(error => {console.error(error); process.exitCode = 1;});
"""
        source = source.replace("__SOURCE__", json.dumps(script))
        source = source.replace("__SNIPPET__", json.dumps(HEADER + "\nUser-agent: OAI-SearchBot\nAllow: /"))
        source = source.replace("__SHARE_URL__", json.dumps(tool.SHARE_BASE + "?d=example.com"))
        result = subprocess.run([NODE, "-e", source], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)



class FixScopeTests(unittest.TestCase):
    def test_scope_is_exactly_the_ai_search_crawlers_the_checker_tests(self):
        self.assertEqual(AI_SEARCH_CRAWLERS, ("OAI-SearchBot", "PerplexityBot", "Claude-SearchBot", "Meta-WebIndexer",
                                              "ChatGPT-User", "Claude-User", "Perplexity-User"))
        tested = {r["name"] for r in tool._crawlers()}
        self.assertEqual(set(search_names(tool._crawlers())), set(AI_SEARCH_CRAWLERS) & tested)
        self.assertEqual(search_names(tool._crawlers()), [n for n in AI_SEARCH_CRAWLERS if n in tested])
        for missing in AI_SEARCH_CRAWLERS:
            self.assertIn(missing, tested, f"{missing} is not one of the checker's crawlers")
        for never in ("GPTBot", "ClaudeBot", "CCBot", "Google-Extended", "Applebot-Extended", "Bytespider",
                      "Googlebot", "Bingbot", "Amazonbot", "meta-externalagent"):
            self.assertNotIn(never, search_names(tool._crawlers()))

if __name__ == "__main__":
    unittest.main(verbosity=2)
