#!/usr/bin/env python3
"""Offline phone handoff checks. Rendered pages stay in temporary folders."""
from __future__ import annotations

import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import brand
import build
import render
sys.path.insert(1, str(HERE / "articles"))
import home
import pages
from test_sitewide_copy import sale_comparison

BASE = "81a0e2ddb96dde32d4130a689ce49959def705a2"
SALE = "Black Friday sale: $19.99 once through December 2. Then $39."
LABEL = "Download the app to run the full audit"


def previous(path):
    source = subprocess.check_output(["git", "show", f"{BASE}:scripts/{path}"], cwd=HERE, text=True)
    module = types.ModuleType("_previous_" + Path(path).stem)
    module.__file__ = str(HERE / path)
    exec(compile(source, module.__file__, "exec"), module.__dict__)
    return module


class PhoneDownloadTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.old_render = previous("render.py")
        cls.old_home = previous("articles/home.py")
        cls.old_home.hero_check_block = previous("articles/hero_check.py").hero_check_block
        cls.temp = tempfile.TemporaryDirectory(prefix="test-phone-download-")
        cls.addClassCleanup(cls.temp.cleanup)
        root = Path(cls.temp.name)
        with patch.object(render, "SITE", root / "after"):
            cls.after = {"home": home.build().read_text(), "download": pages.download().read_text()}
        with patch.object(cls.old_render, "SITE", root / "before"), \
                patch.object(cls.old_home, "render", cls.old_render.render), \
                patch.object(pages, "render", cls.old_render.render):
            cls.before = {"home": cls.old_home.build().read_text().replace('data-ref="$29.50" ', ""),
                          "download": pages.download().read_text().replace('data-ref="$29.50" ', "")}  # 20 Nov: the mount lost data-ref

    def test_blocks_and_no_javascript_fallback(self):
        block = brand.html(render.PHONE_DOWNLOAD_BLOCK)
        self.assertIn("Check Engine runs on a Mac or a Windows PC. Send yourself the link and open it there.", block)
        self.assertIn('data-phone-send>Send myself the link</a>', block)
        self.assertIn('data-phone-copy aria-live="polite">Copy the link</button>', block)
        self.assertIn('<noscript><p>https://checkengineseo.com/download/</p></noscript>', block)
        for route, raw in self.after.items():
            self.assertEqual(raw.count(block), 2 if route == "home" else 1)
            self.assertEqual(raw.count('id="phone-download-script"'), 1)
            self.assertEqual(raw.count('id="phone-download-style"'), 1)
            self.assertIsNone(sale_comparison(raw, route))
        strip = re.search(r'<aside id="product-hunt-welcome".*?</aside>', self.after["home"], re.S)[0]
        self.assertIn(block, strip)
        self.assertIn('class="product-hunt-strip" hidden', strip)
        self.assertLess(self.after["download"].index(block), self.after["download"].index('<ol class="steps"'))

    def test_desktop_markup_and_all_existing_links_are_byte_identical(self):
        for route, raw in self.after.items():
            # Include installer tracking attributes and the Windows variant.
            links = lambda page: re.findall(r'<a\b[^>]*data-ev="Download"[^>]*>.*?</a>', page, re.S)
            self.assertEqual(links(self.before[route]), links(raw))
        for windows in (False, True):
            for both in (False, True):
                with patch.object(render, "WINDOWS", windows), patch.object(self.old_render, "WINDOWS", windows):
                    self.assertEqual(render.download_buttons("mac", "win", both=both),
                                     self.old_render.download_buttons("mac", "win", both=both))
        raw = self.after["home"]
        for added in (render.PHONE_DOWNLOAD_STYLE, render.PHONE_DOWNLOAD_JS):
            raw = raw.replace("\n" + brand.html(added), "", 1)
        block = brand.html(render.PHONE_DOWNLOAD_BLOCK)
        raw = raw.replace("\n  " + block, "", 1).replace("\n" + block, "", 1)
        raw = raw.replace(LABEL, "Run the full free audit")
        self.assertEqual(raw, self.before["home"])

    def test_phone_css_keeps_wide_and_tablet_widths_unchanged(self):
        css = render.PHONE_DOWNLOAD_STYLE
        base, media = css.split("@media", 1)
        self.assertIn(".phone-download{display:none}", base)
        self.assertNotIn('data-ev-button', base)
        queries = re.findall(r'@media ([^{]+)\{', css)
        self.assertEqual(queries, ["(max-width:700px)", "(max-width:700px) and (pointer:coarse)"])
        # Every media rule is bounded at 700px, including the touch variant,
        # so wider tablets retain the same styles as desktop.
        self.assertIn('.phone-download{display:block;', media)
        for selector in ('#product-hunt-welcome>.hero-cta [data-ev="Download"]',
                         '.hero-sec [data-ev-button="home-try-free"]',
                         '.hero-sec [data-ev-button="home-hero-win"]'):
            self.assertIn(selector, media)
        self.assertIn('.hero-sec .phone-link,.hero-sec .mac-alt{display:none}', media)

    def test_sale_once_beside_buy_and_structured_offers_unchanged(self):
        before, after = self.before["download"], self.after["download"]
        self.assertEqual(before.count(SALE), 4)
        self.assertEqual(after.count(SALE), 1)
        self.assertIn('<p class="price-line">' + SALE + '</p>', after)
        schema = lambda raw: re.findall(r'<script type="application/ld\+json">.*?</script>', raw, re.S)
        self.assertEqual(schema(before), schema(after))
        compact = brand.html(render.PRICE_COMPACT)
        self.assertEqual(before.count(compact), after.count(compact))
        for route in self.before:
            self.assertNotEqual(build.page_fingerprint(self.before[route]), build.page_fingerprint(self.after[route]))

    def test_other_page_is_byte_identical(self):
        args = dict(cat="learn", slug="phone-test", title="A title", desc="An answer", h1="A title",
                    crumb="Home", body="<p>A useful answer.</p>", published="2026-11-19")
        for overrides in ({}, dict(cat="", slug="", filename="404.html", noindex=True)):
            with patch.object(render, "SITE", Path(self.temp.name) / "after"):
                after = render.render(**(args | overrides)).read_bytes()
            with patch.object(self.old_render, "SITE", Path(self.temp.name) / "before"):
                before = self.old_render.render(**(args | overrides)).read_bytes().replace(b'data-ref="$29.50" ', b"")
            self.assertEqual(before, after)

    def test_email_referrals_and_clipboard_with_fallback(self):
        source = re.search(r'<script[^>]*>(.*?)</script>', render.PHONE_DOWNLOAD_JS, re.S)[1]
        self.assertNotRegex(source, r'fetch|XMLHttpRequest|sendBeacon|Storage|cookie|navigator\.share')
        harness = r'''
const assert = require('node:assert/strict');
const vm = require('node:vm');
const source = __SOURCE__;
async function check(href, expected, mode) {
  const sends = [{}, {}], clicks = [], copies = [], texts = [];
  let focused = false, removed = 0;
  const buttons = [0, 1].map(() => ({textContent: 'Copy the link',
    addEventListener: (event, fn) => { assert.equal(event, 'click'); clicks.push(fn); }}));
  const context = {URL, encodeURIComponent, window: {location: {href}}, navigator: {}, document: {
    activeElement: {focus() { focused = true; }},
    querySelectorAll: selector => selector === '[data-phone-send]' ? sends : buttons,
    createElement: tag => { assert.equal(tag, 'textarea'); const text = {style: {},
      select() { texts.push(this.value); }, remove() { removed++; }}; return text; },
    body: {appendChild() {}}, execCommand: name => { assert.equal(name, 'copy'); return mode !== 'failed'; }
  }};
  if (mode === 'clipboard' || mode === 'reject') context.navigator.clipboard = {
    writeText: text => { copies.push(text); return mode === 'reject' ? Promise.reject(Error('Denied')) : Promise.resolve(); }
  };
  vm.runInNewContext(source, context);
  for (const send of sends) {
    const mail = new URL(send.href);
    assert.equal(mail.protocol, 'mailto:');
    assert.equal(mail.pathname, '');
    assert.equal(mail.searchParams.get('subject'), 'Check Engine: download link');
    assert.equal(mail.searchParams.get('body'), 'Open this on your Mac or Windows PC to download Check Engine:\n\n' + expected);
  }
  clicks[0]();
  await Promise.resolve(); await Promise.resolve();
  assert.equal(buttons[0].textContent, mode === 'failed' ? 'Copy the link' : 'Link copied');
  assert.equal(buttons[1].textContent, 'Copy the link');
  assert.deepEqual(copies, ['clipboard', 'reject'].includes(mode) ? [expected] : []);
  assert.deepEqual(texts, mode === 'clipboard' ? [] : [expected]);
  assert.equal(removed, mode === 'clipboard' ? 0 : 1);
  assert.equal(focused, mode !== 'clipboard');
}
(async () => {
  for (const mode of ['clipboard', 'fallback', 'reject', 'failed']) {
    await check('https://checkengineseo.com/?ref=producthunt#try',
      'https://checkengineseo.com/download/?ref=producthunt', mode);
    await check('https://checkengineseo.com/download/?ref=PH%20%26%20friends&email=private',
      'https://checkengineseo.com/download/?ref=PH+%26+friends', mode);
    await check('https://example.test/?other=value', 'https://example.test/download/', mode);
  }
})().catch(error => { console.error(error); process.exitCode = 1; });
'''.replace("__SOURCE__", json.dumps(source))
        result = subprocess.run(["node", "-e", harness], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
