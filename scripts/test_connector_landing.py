#!/usr/bin/env python3
"""Offline checks for the connector landing page, email consent and source tags."""
from __future__ import annotations

import datetime
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import subprocess
import sys
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / "articles"))
import ai_assistants  # noqa: E402
import pages  # noqa: E402
from render import LANDING_SOURCE_JS  # noqa: E402


class Markup(HTMLParser):
    def __init__(self, text: str):
        super().__init__()
        self.tags = []
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        self.tags.append((tag, dict(attrs)))


def page(module, builder):
    # Inspect the generator without writing to site/ or running any app/licence code.
    with patch.object(module, "render", side_effect=lambda **kwargs: kwargs):
        return builder()


def node(script: str):
    result = subprocess.run(["node", "-e", script], capture_output=True, text=True)
    if result.returncode:
        raise AssertionError(f"Node exited {result.returncode}: {result.stdout}{result.stderr}")


class ConnectorLandingTests(unittest.TestCase):
    def test_answer_table_licence_and_downloads(self):
        result = page(ai_assistants, ai_assistants.ai_assistants)
        body = result["body"]
        first = re.search(r"<p\b[^>]*>(.*?)</p>", body, re.S)[1]
        self.assertIn("one page", first)
        self.assertIn("whole site", first)
        tags = Markup(body).tags
        self.assertTrue(any(tag == "table" for tag, attrs in tags))
        self.assertTrue(any(attrs.get("id") == "licence" for tag, attrs in tags))
        self.assertIn('class="buy-block', body)
        self.assertLess(body.index('class="buy-block'), body.index('<table'))
        self.assertIn("Try it free for Mac", body)
        self.assertIn("Try it free for Windows", body)
        downloads = [attrs["href"] for tag, attrs in tags if attrs.get("data-ev") == "Download"]
        self.assertGreaterEqual(len(downloads), 5)
        self.assertTrue(all("src=ai-assistants-" in url for url in downloads))
        self.assertIn(ai_assistants.ISSUES, body)
        self.assertIn('src="/assets/free-result.webp"', body)
        self.assertNotRegex(body.lower(), r"\b(?:official|verified|approved)\b")

    def test_email_off_by_default_on_both_pages(self):
        self.assertFalse(pages.EMAIL_BOX_ENABLED)
        for module, builder in ((ai_assistants, ai_assistants.ai_assistants), (pages, pages.download)):
            body = page(module, builder)["body"]
            self.assertNotIn('id="email-box"', body)
            self.assertNotIn("kerr-subscribe", body)
            self.assertNotIn("subscribedOk", body)

    def test_email_enabled_dates_and_placement(self):
        with patch.object(pages, "EMAIL_BOX_ENABLED", True):
            for day, source in (("2026-11-08", "docket-price-reminder"),
                                ("2026-11-30", "docket-price-reminder"),
                                ("2026-12-01", "docket-news")):
                body = pages.email_box(datetime.date.fromisoformat(day))
                tags = Markup(body).tags
                form = next(attrs for tag, attrs in tags if tag == "form")
                self.assertEqual(form["method"], "post")
                self.assertEqual(form["action"], "https://kerr-subscribe.kerrco.workers.dev")
                field = next(attrs for tag, attrs in tags if attrs.get("name") == "source")
                self.assertEqual(field["value"], source)
                card = next(attrs for tag, attrs in tags if attrs.get("id") == "email-box")
                self.assertIn("hidden", card)
                self.assertFalse(any("checked" in attrs for tag, attrs in tags))
                self.assertFalse(any(tag == "script" and "src" in attrs for tag, attrs in tags))
            for module, builder in ((ai_assistants, ai_assistants.ai_assistants), (pages, pages.download)):
                body = page(module, builder)["body"]
                self.assertLess(body.index('data-ev="Buy"'), body.index('id="email-box"'))

    def test_subscribed_ok_five_cases_and_retry(self):
        # Run the complete handler too: no request on load or download, and failures
        # must keep the form available with a working retry button.
        node("""
const assert = require('node:assert/strict');
const vm = require('node:vm');
const source = __SOURCE__;
async function check(day, reply, success) {
  const handlers = {}, requests = [];
  const button = {disabled: false}, message = {}, promise = {};
  const form = {hidden: false, action: 'https://kerr-subscribe.kerrco.workers.dev',
    elements: {source: {value: ''}}, querySelector: () => button,
    addEventListener: (name, fn) => handlers[name] = fn};
  const card = {hidden: true, querySelector: selector => ({
    'form': form, '[role="status"]': message, '[data-promise]': promise,
    '[data-dismiss]': {addEventListener: () => {}}
  })[selector]};
  const fixed = new Date(day);
  const context = {JSON, URLSearchParams, Date: class extends Date {
      constructor() { super(fixed); }
    }, FormData: class { constructor() { return [['source', form.elements.source.value], ['email', 'test@example.com']]; } },
    document: {getElementById: () => card, addEventListener: (name, fn) => handlers[name] = fn},
    fetch: async (url, options) => { requests.push({url, options}); return reply(); }};
  vm.createContext(context);
  vm.runInContext(source, context);
  assert.equal(requests.length, 0);
  assert.equal(card.hidden, true);
  let placed = false;
  const host = {insertAdjacentElement: (where, element) => {
    assert.equal(where, 'afterend'); assert.equal(element, card); placed = true;
  }};
  const link = {href: 'https://kerr-affiliate-hub.kerrco.workers.dev/dl/docket?src=test', closest: () => host};
  handlers.click({target: {closest: () => link}});
  assert.equal(placed, true);
  assert.equal(card.hidden, false);
  assert.equal(requests.length, 0);
  await handlers.submit({preventDefault() {}});
  assert.equal(requests.length, 1);
  assert.equal(requests[0].options.method, 'POST');
  assert.equal(requests[0].options.credentials, 'omit');
  assert.equal(requests[0].options.body.get('source'), day > '2026-11-30' ? 'docket-news' : 'docket-price-reminder');
  assert.equal(form.hidden, success);
  assert.equal(button.disabled, false);
  assert.equal(message.textContent.includes('Check your inbox'), success);
  if (!success) { await handlers.submit({preventDefault() {}}); assert.equal(requests.length, 2); }
  return context;
}
(async () => {
  const ctx = await check('2026-11-30', () => ({status: 200, text: async () => '{"ok":true}'}), true);
  assert.equal(ctx.subscribedOk(200, '{"ok":true}'), true);
  for (const [status, text] of [[500, '{"ok":true}'], [200, '{"ok":false}'],
      [0, ''], [200, 'not json'], [200, 'null'], [200, '{"ok":"true"}']])
    assert.equal(ctx.subscribedOk(status, text), false);
  for (const [status, text] of [[500, 'error'], [200, '{"ok":false}'], [200, 'not json']])
    await check('2026-11-30', () => ({status, text: async () => text}), false);
  await check('2026-11-30', () => { throw new Error('network failure'); }, false);
  await check('2026-12-01', () => ({status: 200, text: async () => '{"ok":true}'}), true);
})().catch(error => { console.error(error); process.exitCode = 1; });
""".replace("__SOURCE__", json.dumps(pages.SUBSCRIBE_JS)))

    def test_landing_sources_in_node(self):
        node("""
const assert = require('node:assert/strict');
const vm = require('node:vm');
function run(search, stored = '', loading = false) {
  const listeners = {};
  const store = {dk_ls: stored};
  const hub = 'https://kerr-affiliate-hub.kerrco.workers.dev/';
  const links = ['dl/docket?src=ai-assistants-mac&to=https://github.com/file', 'buy/docket?src=test'].map(
    path => ({href: hub + path, getAttribute() {return this.href;}, setAttribute(k, v) {this.href = v;}}));
  const context = {URLSearchParams, location: {search},
    sessionStorage: {setItem(k, v) {store[k] = v;}, getItem(k) {return store[k];}},
    document: {readyState: loading ? 'loading' : 'complete', querySelectorAll: () => links,
      addEventListener: (name, fn) => listeners[name] = fn}};
  vm.runInNewContext(__SOURCE__, context);
  if (listeners.DOMContentLoaded) listeners.DOMContentLoaded();
  return links.map(a => new URL(a.href).searchParams);
}
const expected = ['producthunt','product_hunt','ph','hackernews','hn','reddit','twitter','x','youtube',
  'github','betalist','indiehackers','newsletter','linkedin','facebook','instagram','tiktok','google','bing',
  'chatgpt','perplexity','discord','claude','claude-directory','claude-connector','chatgpt-directory'];
for (const value of expected) {
  const links = run('?utm_source=' + value);
  assert.equal(links[0].get('ls'), value);
  assert.equal(links[1].get('metadata_landing_source'), value);
}
for (const [query, value] of [['?utm_source=chatgpt.com','chatgpt'], ['?utm_source=claude.ai','claude'],
    ['?utm_source=CLAUDE-DIRECTORY','claude-directory'], ['?ref=reddit&via=youtube&utm_source=claude','reddit'],
    ['?via=youtube&utm_source=claude','youtube']]) {
  assert.equal(run(query, '', true)[0].get('ls'), value);
}
for (const query of ['?utm_source=unknown', '?utm_source=claude.evil', '?utm_source=claude-directory-extra', ''])
  assert.equal(run(query)[0].get('ls'), null);
assert.equal(run('', 'claude')[0].get('ls'), 'claude');
assert.equal(run('', 'unknown')[0].get('ls'), null);
""".replace("__SOURCE__", json.dumps(LANDING_SOURCE_JS)))

    def test_privacy_matches_email_switch_and_counts(self):
        for enabled in (False, True):
            with patch.object(pages, "EMAIL_BOX_ENABLED", enabled):
                body = page(pages, pages.privacy)["body"]
            self.assertNotIn("The home page has one email field", body)
            for word in ("kerr-subscribe.kerrco.workers.dev", "docket-price-reminder", "docket-news",
                         "daily counts by assistant family", "tool outcome", "never an address, client name or session id",
                         "in local storage for thirty days"):
                self.assertIn(word, body)
            if enabled:
                self.assertIn("We send the emails through MailerLite", body)
            else:
                self.assertIn("are switched off", body)
                self.assertNotIn("We send the emails through MailerLite", body)


if __name__ == "__main__":
    unittest.main()
