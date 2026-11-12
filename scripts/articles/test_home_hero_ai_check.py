#!/usr/bin/env python3
"""Offline checks of the rendered hero and its browser submit handler."""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import tempfile
import types
import unittest
from html.parser import HTMLParser
from pathlib import Path
from unittest.mock import patch
from urllib.parse import parse_qs, urlencode, urlsplit

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE), str(HERE.parent)]
import facts as F
import comparisons
import hero_check
import home
import render
import tool_ai_crawlers as tool
from crawler_fix import FIX_JS, search_names

BASE = "23cea93a72b107dba1052ade68a3dcd3602e3e0a"
CAVEAT = ("This reads your robots.txt only. A firewall or CDN can still refuse a crawler that "
          "robots.txt allows, and no robots.txt check can see that.")


class Markup(HTMLParser):
    def __init__(self, source):
        super().__init__()
        self.tags = []
        self.words = []
        self.hidden = 0
        self.feed(source)

    def handle_starttag(self, tag, attrs):
        self.tags.append((tag, dict(attrs)))
        if tag in {"script", "style"}:
            self.hidden += 1

    def handle_endtag(self, tag):
        if tag in {"script", "style"}:
            self.hidden -= 1

    def handle_data(self, data):
        if not self.hidden:
            self.words.append(data)


def normal(source):
    return " ".join(" ".join(Markup(source).words).split())


class HomeHeroTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fragment = hero_check.hero_check_block()
        cls.script = re.search(r"<script>(.*?)</script>", cls.fragment, re.S)[1]
        cls.scratch = tempfile.TemporaryDirectory(prefix="docket-home-hero-test-")
        cls.addClassCleanup(cls.scratch.cleanup)
        with patch.object(render, "SITE", Path(cls.scratch.name)):
            cls.page = home.build().read_text()
            cls.tool = tool.checker().read_text()

    def test_heading_form_and_no_script_fallback(self):
        h1 = '<h1 class="hero-h1">Can ChatGPT, Claude and Perplexity <em>read your site?</em></h1>'
        self.assertIn(h1, self.page)
        self.assertEqual(normal(h1), "Can ChatGPT, Claude and Perplexity read your site?")
        self.assertTrue(re.search(re.escape(h1) + r'\s*<form class="hero-check"', home.body()))
        # The shared renderer adds the existing former-brand note after the H1.
        intro = self.page.split(h1, 1)[1].split('<form class="hero-check"', 1)[0]
        self.assertNotIn("hero-sub", intro)
        tags = Markup(self.fragment).tags
        form = next(attrs for tag, attrs in tags if tag == "form")
        self.assertEqual(form, {"class": "hero-check", "action": "/tools/ai-crawler-checker/", "method": "get"})
        inputs = [attrs for tag, attrs in tags if tag == "input"]
        self.assertEqual(len(inputs), 1)
        field = inputs[0]
        for name, value in {"type": "text", "name": "d", "inputmode": "url", "autocomplete": "off",
                            "autocapitalize": "off", "spellcheck": "false", "placeholder": "yoursite.com"}.items():
            self.assertEqual(field[name], value)
        label = next(attrs for tag, attrs in tags if tag == "label")
        self.assertEqual(label["for"], field["id"])
        self.assertIn(">Your website address</label>", self.fragment)
        self.assertIn('type="submit">Check it free</button>', self.fragment)
        self.assertEqual(form["action"] + "?" + urlencode({field["name"]: "example.com"}),
                         "/tools/ai-crawler-checker/?d=example.com")
        self.assertIn("if (!form || !window.fetch) return;", self.script)
        self.assertTrue(any(attrs.get("aria-live") == "polite" for _, attrs in tags))

    def test_shared_endpoint_agents_and_vendor_grouping(self):
        for name in ("ENDPOINT", "AGENTS"):
            hero_value = json.loads(re.search(r"var " + name + r" = (.*?);", self.script)[1])
            tool_value = json.loads(re.search(r"var " + name + r" = (.*?);", self.tool)[1])
            self.assertEqual(hero_value, tool_value)
        self.assertEqual(json.loads(re.search(r"var ENDPOINT = (.*?);", self.script)[1]), tool.CHECKER_ENDPOINT)
        assistants = json.loads(re.search(r"var ASSISTANTS = (.*?);", self.script)[1])
        self.assertEqual(assistants, [
            {"label": "ChatGPT", "agents": ["ChatGPT-User", "OAI-SearchBot"]},
            {"label": "Claude", "agents": ["Claude-SearchBot", "Claude-User"]},
            {"label": "Perplexity", "agents": ["Perplexity-User", "PerplexityBot"]},
        ])
        with patch.object(hero_check, "_crawlers", return_value=[
            {"name": "future-search", "owner": "Anthropic", "purpose": next(iter(tool.CITATION_PURPOSES))},
            {"name": "future-training", "owner": "Anthropic", "purpose": "training"},
        ]):
            fragment = hero_check.hero_check_block()
        groups = json.loads(re.search(r"var ASSISTANTS = (.*?);", fragment)[1])
        self.assertEqual(groups[1]["agents"], ["future-search"])

    def test_copy_privacy_and_prices(self):
        self.assertEqual(self.fragment.count(CAVEAT), 1)
        self.assertNotRegex(self.fragment, "[\u2013\u2014]")
        self.assertNotRegex(self.fragment.lower(), r"\b(?:instant|guarantee|accurate)\b|100%")
        privacy = re.search(r'<p class="hero-check-privacy">(.*?)</p>', self.fragment, re.S)[1]
        self.assertIn("<p>" + privacy + "</p>", self.tool)
        self.assertLess(self.fragment.index("</form>"), self.fragment.index(privacy))
        self.assertNotRegex(self.fragment, r"\$\d")
        self.assertIn(render.buy_block("home-hero", try_app="home-try-free"), home.body())
        self.assertIn(normal(render.price_sentence()), normal(self.page))
        self.assertIn(f'{F.index_citation_pct()}% of the {F.index_n()} major sites', normal(self.page))

    def test_shared_fix_inside_answer(self):
        self.assertIn(FIX_JS, self.script)
        self.assertIn(FIX_JS, self.tool)
        expected = search_names(tool._crawlers())
        for script in (self.script, self.tool):
            names = json.loads(re.search(r"var SEARCH_NAMES = (.*?);", script)[1])
            self.assertEqual(names, expected)
            self.assertNotIn("Google-Extended", names)
            self.assertNotIn("GPTBot", names)
        answer = self.fragment.split('<div id="hero-check-answer" hidden>', 1)[1]
        answer = answer.split('<div class="hero-check-next"', 1)[0]
        self.assertLess(answer.index('id="hero-check-summary"'), answer.index('id="hero-check-fix"'))
        self.assertLess(answer.index('id="hero-check-fix"'), answer.index(CAVEAT))
        self.assertIn('</div>\n    <p>' + CAVEAT + '</p>\n  </div>', answer)
        self.assertEqual(self.fragment.count(CAVEAT), 1)
        self.assertIn("fix_copied", self.script)
        self.assertNotIn("innerHTML", self.script)
        hero_fix = self.fragment.split('<div id="hero-check-fix"', 1)[1].split(CAVEAT, 1)[0]
        for paragraph in re.findall(r"<p\b[^>]*>(.*?)</p>", hero_fix, re.S):
            if paragraph:
                self.assertIn(paragraph, self.tool)
        with patch.object(hero_check, "_crawlers", return_value=[
            {"name": "future-search", "owner": "Anthropic", "purpose": "search index"},
            {"name": "OAI-SearchBot", "owner": "OpenAI", "purpose": "search index"},
            {"name": "future-training", "owner": "Anthropic", "purpose": "training"},
            {"name": "Googlebot", "owner": "Google", "purpose": "search index"},
        ]):
            fragment = hero_check.hero_check_block()
        # A new crawler is never added to a snippet people paste by its data row alone: only the curated set.
        self.assertEqual(json.loads(re.search(r"var SEARCH_NAMES = (.*?);", fragment)[1]), ["OAI-SearchBot"])

    def test_platform_downloads_use_existing_helper(self):
        for windows in (False, True):
            with patch.object(hero_check, "WINDOWS", windows):
                tags = Markup(hero_check.hero_check_block()).tags
            links = [attrs for tag, attrs in tags if tag == "a" and "btn" in attrs.get("class", "").split()]
            self.assertEqual(len(links), 2 if windows else 1)
            self.assertEqual(links[0]["href"], render.download_url("home-hero-check"))
            self.assertEqual("dl-mac" in links[0]["class"].split(), windows)
            if windows:
                self.assertIn("dl-win", links[1]["class"].split())
                self.assertEqual(links[1]["href"], render.download_url("home-hero-check-win", to=render.WIN_SETUP))
                query = parse_qs(urlsplit(links[1]["href"]).query)
                self.assertEqual(query["src"], ["home-hero-check-win"])
                self.assertEqual(query["to"], [render.WIN_SETUP])
        self.assertEqual(self.fragment.count("Run the full free audit</a>"), 2 if render.WINDOWS else 1)

    def test_rest_of_hero_and_page_metadata_match_base(self):
        source = subprocess.run(["git", "show", f"{BASE}:scripts/articles/home.py"],
                                cwd=HERE, capture_output=True, text=True, check=True).stdout
        old = types.ModuleType("_base_home_hero")
        old.__file__ = str(HERE / "home.py")
        exec(compile(source, old.__file__, "exec"), old.__dict__)
        before, after = old.body(), home.body()
        before_sub = re.search(r'<p class="hero-sub">.*?</p>', before, re.S)[0]
        after_sub = re.search(r'<p class="hero-sub">.*?</p>', after, re.S)[0]
        added = ("Save thousands by doing it yourself. Agencies average $3,209 a month for SEO "
                 f'({comparisons.source_link("Ahrefs", "https://ahrefs.com/blog/seo-pricing/")}) '
                 "and one audit is quoted at $500 to $5,000 "
                 f'({comparisons.source_link("SEOProfy", "https://seoprofy.com/blog/seo-audit-pricing/")}). '
                 f"Check Engine is {render.PRICE_COMPACT}.")
        self.assertEqual(normal(after_sub), "Everything that's wrong. In the order to fix it. "
                         + normal(before_sub) + " " + normal(added))
        note = comparisons._verified_note("audit-agency-prices-home", closing="Prices vary with the work and the site.")
        self.assertIn(note, after)
        after = after.replace(after_sub, before_sub, 1).replace("\n  " + note, "", 1)
        # Everything after the changed introduction, including all purchase facts and media.
        before_tail = before.split('<p class="hero-note">No page meter.', 1)[1]
        after_tail = after.split('<p class="hero-note">No page meter.', 1)[1]
        after_tail = after_tail.replace("Everything that's wrong. In the order to fix it. ", "", 1)
        self.assertEqual(before_tail, after_tail)
        self.assertEqual(before.split('<h1 class="hero-h1">')[0], after.split('<h1 class="hero-h1">')[0])
        with patch.object(old, "render", side_effect=lambda **kwargs: kwargs), \
                patch.object(home, "render", side_effect=lambda **kwargs: kwargs):
            before_args, after_args = old.build(), home.build()
        for key in ("title", "desc", "h1", "faq", "closer", "modified"):
            self.assertEqual(before_args[key], after_args[key])

    @unittest.skipUnless(shutil.which("node"), "node was not found on PATH; skipping browser JavaScript cases")
    def test_browser_states_events_and_retries(self):
        source = r"""
const assert = require('node:assert/strict');
const vm = require('node:vm');
const source = __SOURCE__;
const assistants = __ASSISTANTS__;
const names = assistants.flatMap(a => a.agents);
function setup(fetcher, analytics = true, supported = true, clipboard = true) {
  const handlers = {}, calls = [], events = [], clicks = [], copied = [];
  let copyClick, selected;
  const elements = Object.fromEntries(['address', 'status', 'answer', 'summary', 'next', 'every',
    'verdict-0', 'verdict-1', 'verdict-2', 'fix', 'fix-google', 'fix-wildcard', 'fix-snippet',
    'fix-name', 'fix-server'].map(name => ['hero-check-' + name, {textContent: '', hidden: true}]));
  const form = {addEventListener: (name, fn) => handlers[name] = fn};
  const links = [0, 1].map(() => ({addEventListener: (name, fn) => clicks.push(fn)}));
  elements['hero-check-next'].querySelectorAll = () => links;
  elements['hero-check-fix'].querySelector = () => ({textContent: 'Copy',
    getAttribute: () => 'hero-check-fix-snippet', addEventListener: (name, fn) => copyClick = fn});
  const fetch = (url) => {calls.push(url); return fetcher(url);};
  const context = {URL, encodeURIComponent, document: {
    querySelector: () => form, getElementById: id => elements[id],
    createRange: () => ({selectNodeContents: el => selected = el}),
    execCommand: name => {assert.equal(name, 'copy'); copied.push(selected.textContent);}}, fetch,
    navigator: clipboard ? {clipboard: {writeText: async text => copied.push(text)}} : {},
    setTimeout: fn => fn(),
    window: {fetch: supported && fetch, getSelection: () => ({removeAllRanges() {}, addRange() {}})}};
  if (analytics) context.window.plausible = (name, props) => events.push({name, props});
  vm.runInNewContext(source, context);
  async function submit(value) {
    elements['hero-check-address'].value = value;
    let prevented = false;
    handlers.submit({preventDefault() {prevented = true;}});
    assert.equal(prevented, true);
    await new Promise(resolve => setImmediate(resolve));
  }
  return {handlers, calls, events, clicks, elements, submit, copied, copy: () => copyClick(),
    text: name => elements['hero-check-' + name].textContent,
    hidden: name => elements['hero-check-' + name].hidden};
}
function response(j, ok = true) {return Promise.resolve({ok, json: async () => j});}
function result(overrides = {}) {
  return {state: 'parsed', robots_url: 'https://example.com/robots.txt',
    results: names.map(agent => ({agent, allowed: true})), ...overrides};
}
async function main() {
  const allowed = setup(() => response(result({results: [...result().results,
    {agent: 'GPTBot', allowed: false}, {agent: 'ClaudeBot', allowed: false}]})));
  assert.equal(allowed.calls.length, 0);
  await allowed.submit('   ');
  assert.equal(allowed.text('status'), 'Enter your website address.');
  assert.equal(allowed.calls.length, 0);
  await allowed.submit(' https://example.com/a?b=c&d=e ');
  const url = new URL(allowed.calls[0]);
  assert.equal(url.searchParams.get('url'), 'https://example.com/a?b=c&d=e');
  assert.equal(url.searchParams.get('agents'), __AGENTS__);
  for (let i = 0; i < 3; i++) assert.equal(allowed.text('verdict-' + i), 'Can read');
  assert.equal(allowed.text('summary'), 'Your robots.txt lets all three read your site. The free audit checks the rest, in order.');
  assert.equal(allowed.hidden('answer'), false);
  assert.equal(allowed.hidden('next'), false);
  assert.equal(allowed.hidden('fix'), true);
  assert.equal(allowed.elements['hero-check-every'].href, '/tools/ai-crawler-checker/?d=example.com');
  allowed.clicks.forEach(click => click());
  assert.deepEqual(allowed.events.map(e => e.name), ['check_started', 'check_started', 'result_allowed',
    'result_to_download', 'result_to_download']);

  const blockedResults = names.map((agent, i) => ({agent, allowed: i >= 3}));
  const blocked = setup(() => response(result({results: blockedResults})));
  await blocked.submit('example.com');
  assert.deepEqual([0, 1, 2].map(i => blocked.text('verdict-' + i)), ['Blocked', 'Blocked', 'Can read']);
  assert.equal(blocked.text('summary'), 'Your robots.txt blocks 3 AI search crawlers, so those assistants cannot quote your site. The free audit shows the fix in full.');
  assert.equal(blocked.hidden('fix'), false);
  assert.equal(blocked.hidden('fix-server'), false);
  assert.equal(blocked.hidden('fix-wildcard'), true);
  assert.equal(JSON.stringify(blocked.events[1]), JSON.stringify({name: 'result_blocked', props: {props: {blocked: 2}}}));
  for (const agent of names) {
    const one = setup(() => response(result({results: [{agent, allowed: false}]})));
    await one.submit('example.com');
    const index = assistants.findIndex(a => a.agents.includes(agent));
    assert.equal(one.text('verdict-' + index), 'Blocked');
    assert.equal(one.events[1].props.props.blocked, 1);
    assert(one.text('summary').startsWith('Your robots.txt blocks 1 AI search crawlers,'));
  }
  for (const status of [401, 403]) {
    const refused = setup(() => response(result({state: 'unavailable', status, results: blockedResults})));
    await refused.submit('example.com');
    for (let i = 0; i < 3; i++) assert.equal(refused.text('verdict-' + i), 'Unknown: the site refused this checker');
    assert(refused.text('status').includes('HTTP ' + status));
    assert.equal(refused.text('summary'), '');
    assert.equal(refused.events.length, 1);
    assert.equal(refused.hidden('answer'), false);
  }
  for (const results of [[], [{agent: 'GPTBot', allowed: false}], [{agent: names[0], allowed: null}]]) {
    const missing = setup(() => response(result({results})));
    await missing.submit('example.com');
    for (let i = 0; i < 3; i++) assert.equal(missing.text('verdict-' + i), 'Not checked');
    assert.equal(missing.text('summary'), '');
    assert.equal(missing.events.length, 1);
    assert.equal(missing.hidden('fix'), true);
  }
  const partial = setup(() => response(result({results: [{agent: names[0], allowed: true}]})));
  await partial.submit('example.com');
  assert.equal(partial.text('verdict-0'), 'Can read');
  assert.equal(partial.text('verdict-1'), 'Not checked');
  assert.equal(partial.text('summary'), '');
  for (const j of [result({state: 'unavailable', status: 404}),
    result({state: 'unreachable', status: 503, results: blockedResults}),
    result({state: 'blocked', note: 'That address could not be checked.', results: []})]) {
    const state = setup(() => response(j));
    await state.submit('example.com');
    assert(state.text('status').length > 0);
    assert.equal(state.hidden('answer'), false);
  }
  const warnings = setup(() => response(result({note: 'File note.', warnings: ['First warning.', 'Second warning.']})));
  await warnings.submit('example.com');
  assert.equal(warnings.text('status'), 'Read https://example.com/robots.txt. File note. First warning.');
  const wildcard = {agent: 'OAI-SearchBot', allowed: false, governedBy: 'wildcard'};
  const snippet = '# Let AI search crawlers read your site (they are not training crawlers)\nUser-agent: OAI-SearchBot\nAllow: /';
  for (const clipboard of [true, false]) {
    for (const analytics of [true, false]) {
      const fix = setup(() => response(result({results: [wildcard,
        {agent: 'GPTBot', allowed: false, governedBy: 'wildcard'},
        {agent: 'Claude-SearchBot', allowed: false, governedBy: 'name'},
        {agent: 'PerplexityBot', allowed: false, governedBy: 'status'}]})), analytics, true, clipboard);
      await fix.submit('example.com');
      assert.equal(fix.hidden('fix'), false);
      assert.equal(fix.hidden('fix-wildcard'), false);
      assert.equal(fix.hidden('fix-google'), true);
      assert.equal(fix.text('fix-snippet'), snippet);
      assert(fix.text('fix-name').includes('decision: Claude-SearchBot.'));
      assert(fix.text('fix-server').endsWith('PerplexityBot. Make /robots.txt answer 200 or 404.'));
      fix.copy();
      assert.deepEqual(fix.copied, [snippet]);
      if (analytics) assert.equal(JSON.stringify(fix.events.at(-1)), JSON.stringify({name: 'fix_copied'}));
      else assert.equal(fix.events.length, 0);
      await fix.submit('');
      assert.equal(fix.hidden('fix'), true);
      assert.equal(fix.text('fix-snippet'), '');
      assert.equal(fix.text('fix-name'), '');
      assert.equal(fix.text('fix-server'), '');
    }
  }
  const google = setup(() => response(result({results: [wildcard, {agent: 'Googlebot', allowed: false}]})));
  await google.submit('example.com');
  assert.equal(google.hidden('fix-google'), false);
  assert.equal(google.hidden('fix-wildcard'), true);
  assert.equal(google.text('fix-snippet'), '');
  for (const agent of ['GPTBot', 'Google-Extended', 'Googlebot']) {
    const ignored = setup(() => response(result({results: [{agent, allowed: false, governedBy: 'wildcard'}]})));
    await ignored.submit('example.com');
    assert.equal(ignored.hidden('fix'), true);
  }
  for (const [reply, message] of [
    [() => response({error: 'Try again later.'}, false), 'Try again later.'],
    [() => response({}, false), 'That address could not be checked.'],
    [() => Promise.reject(new Error('offline')), 'The checker could not be reached. Try again in a minute.'],
    [() => Promise.resolve({ok: true, json: async () => {throw new Error('bad JSON');}}), 'The checker could not be reached. Try again in a minute.']
  ]) {
    let fail = false;
    const retry = setup(() => fail ? reply() : response(result({results: [wildcard]})));
    await retry.submit('example.com');
    fail = true;
    await retry.submit('example.com');
    assert.equal(retry.text('status'), message);
    assert.equal(retry.hidden('answer'), true);
    assert.equal(retry.hidden('next'), true);
    assert.equal(retry.hidden('fix'), true);
    assert.equal(retry.text('fix-snippet'), '');
    fail = false;
    await retry.submit('example.com');
    assert.equal(retry.hidden('answer'), false);
  }
  let finish;
  const racing = setup(() => new Promise(resolve => {finish = resolve;}));
  await racing.submit('first.example');
  assert.equal(racing.text('status'), 'Reading robots.txt…');
  const first = finish;
  await racing.submit('second.example');
  finish({ok: true, json: async () => result({robots_url: 'https://second.example/robots.txt'})});
  await new Promise(resolve => setImmediate(resolve));
  first({ok: true, json: async () => result({robots_url: 'https://first.example/robots.txt'})});
  await new Promise(resolve => setImmediate(resolve));
  assert.equal(racing.elements['hero-check-every'].href, '/tools/ai-crawler-checker/?d=second.example');
  assert.equal(racing.events.length, 3);
  await setup(() => response(result()), false).submit('example.com');
  const fallback = setup(() => {throw new Error('must not fetch');}, true, false);
  assert.equal(fallback.handlers.submit, undefined);
  const allEvents = [...allowed.events, ...blocked.events];
  assert.deepEqual([...new Set(allEvents.map(e => e.name))].sort(),
    ['check_started', 'result_allowed', 'result_blocked', 'result_to_download']);
  for (const event of allEvents) {
    assert(!/example|https?:|url|host|address/i.test(JSON.stringify(event)));
    if (event.props) assert.deepEqual(Object.keys(event.props.props), ['blocked']);
  }
}
main().catch(error => {console.error(error); process.exitCode = 1;});
"""
        values = {
            "__SOURCE__": self.script,
            "__ASSISTANTS__": json.loads(re.search(r"var ASSISTANTS = (.*?);", self.script)[1]),
            "__AGENTS__": json.loads(re.search(r"var AGENTS = (.*?);", self.script)[1]),
        }
        for name, value in values.items():
            source = source.replace(name, json.dumps(value))
        result = subprocess.run(["node", "-e", source], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        events = re.findall(r"window\.plausible\('([^']+)'", self.script)
        self.assertCountEqual(events, ["check_started", "result_blocked", "result_allowed", "result_to_download", "fix_copied"])
        self.assertEqual(self.script.count("if (window.plausible)"), 5)


if __name__ == "__main__":
    unittest.main(verbosity=2)
