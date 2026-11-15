#!/usr/bin/env python3
"""Offline regression checks for the free tool backlog, after a build."""
from html.parser import HTMLParser
import json
from pathlib import Path
import subprocess
from urllib.parse import urlsplit
import xml.etree.ElementTree as ET


SITE = Path(__file__).resolve().parent.parent / "site"
ROUTE = "/tools/llms-txt-generator/"


class Page(HTMLParser):
    def __init__(self, raw):
        super().__init__(convert_charrefs=True)
        self.tags = []
        self.words = []
        self.scripts = []
        self.hidden = []
        self.script = None
        self.feed(raw)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        self.tags.append((tag, attrs))
        hidden = tag in {"script", "style", "template"} or "hidden" in attrs
        if tag not in {"input", "meta", "link", "img", "br", "hr"}:
            self.hidden.append((tag, hidden or bool(self.hidden and self.hidden[-1][1])))
        if tag == "script":
            self.script = []

    def handle_endtag(self, tag):
        if tag == "script" and self.script is not None:
            self.scripts.append("".join(self.script))
            self.script = None
        for index in range(len(self.hidden) - 1, -1, -1):
            if self.hidden[index][0] == tag:
                del self.hidden[index:]
                break

    def handle_data(self, data):
        if self.script is not None:
            self.script.append(data)
        if not self.hidden or not self.hidden[-1][1]:
            self.words.append(data)


def check_tool():
    path = SITE / ROUTE.strip("/") / "index.html"
    assert path.is_file(), f"missing {ROUTE}index.html"
    page = Page(path.read_text(encoding="utf-8"))
    assert not any(tag == "script" and "src" in attrs for tag, attrs in page.tags), \
        "the generator must run without external scripts"
    assert not any(tag == "form" and ("action" in attrs or "method" in attrs)
                   for tag, attrs in page.tags), "the generator must stay in the browser"
    ids = {attrs["id"]: attrs for tag, attrs in page.tags if "id" in attrs}
    assert "readonly" in ids["llms-output"]
    assert "disabled" in ids["llms-copy"]
    assert ids["llms-status"]["aria-live"] == "polite"
    rows = [attrs for tag, attrs in page.tags if "data-key-page" in attrs]
    assert len(rows) == 10 and sum("hidden" not in row for row in rows) == 1
    for index in range(1, 11):
        for field in ("title", "url", "note"):
            assert f"llms-{field}-{index}" in ids
    words = " ".join(" ".join(page.words).split())
    assert "The file does not guarantee that AI assistants will read it." in words
    links = [attrs.get("href", "") for tag, attrs in
             Page((SITE / "tools/index.html").read_text(encoding="utf-8")).tags if tag == "a"]
    assert ROUTE in links, "the tools index must link to the generator"
    sitemap = ET.parse(SITE / "sitemap.xml")
    locations = sitemap.findall(".//{http://www.sitemaps.org/schemas/sitemap/0.9}loc")
    assert any(urlsplit(loc.text).path == ROUTE for loc in locations), \
        "the sitemap must include the generator"
    return page


def check_app_links():
    paths = sorted((SITE / "tools").glob("*/index.html"))
    assert len(paths) == 11, f"expected 11 tool pages, found {len(paths)}"
    for path in paths:
        page = Page(path.read_text(encoding="utf-8"))
        assert any(tag == "a" and attrs.get("href") == "/download/"
                   for tag, attrs in page.tags), f"{path}: missing app link"
        assert sum("data-tool-app" in attrs for tag, attrs in page.tags) == 1, \
            f"{path}: expected one shared app call-out"
        words = " ".join(" ".join(page.words).split())
        assert "Check the whole site in the free Check Engine SEO app" in words, \
            f"{path}: the shared app call-out must be visible"


NODE_TEST = r"""
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const script = JSON.parse(fs.readFileSync(0, 'utf8'));

class Element {
  constructor() {
    this.value = '';
    this.textContent = '';
    this.disabled = false;
    this.hidden = false;
    this.listeners = {};
  }
  addEventListener(event, listener) { this.listeners[event] = listener; }
  focus() { this.focused = true; }
  select() { this.selected = true; }
  set innerHTML(value) { throw new Error('User text must stay in text fields'); }
}

async function main() {
  const ids = Object.fromEntries(['form', 'name', 'summary', 'output', 'status', 'copy', 'add']
    .map(id => ['llms-' + id, new Element()]));
  const pages = Array.from({length: 10}, (_, index) => {
    const row = new Element();
    row.hidden = index > 0;
    row.inputs = Array.from({length: 3}, () => new Element());
    row.querySelectorAll = selector => { assert.equal(selector, 'input'); return row.inputs; };
    row.querySelector = selector => { assert.equal(selector, 'input'); return row.inputs[0]; };
    return row;
  });
  const form = ids['llms-form'];
  form.querySelectorAll = selector => { assert.equal(selector, '[data-key-page]'); return pages; };
  const navigator = {};
  vm.runInNewContext(script, {
    document: {getElementById: id => { assert.ok(ids[id], id); return ids[id]; }},
    navigator, URL,
    fetch() { throw new Error('The generator must never fetch'); }
  });
  const output = ids['llms-output'];
  const copy = ids['llms-copy'];
  assert.equal(output.value, '');
  assert.equal(copy.disabled, true);
  let prevented = false;
  form.listeners.submit({preventDefault() { prevented = true; }});
  assert.equal(prevented, true);

  ids['llms-name'].value = 'Example site';
  ids['llms-summary'].value = 'A guide to\n  local walks.';
  form.listeners.input();
  assert.equal(output.value, '# Example site\n\n> A guide to local walks.\n\n## Key pages\n');
  assert.equal(copy.disabled, false);
  pages[0].inputs[0].value = 'Walks [nearby]';
  form.listeners.input();
  assert.equal(output.value, '');
  assert.equal(copy.disabled, true);
  assert.match(ids['llms-status'].textContent, /page 1/);

  pages[0].inputs[2].value = 'Paths\nwith maps.';
  for (const address of ['bad URL', '/relative/', 'javascript:alert(1)', 'ftp://example.com/',
                         'https://user:password@example.com/']) {
    pages[0].inputs[1].value = address;
    form.listeners.input();
    assert.equal(copy.disabled, true, address);
    assert.equal(output.value, '', address);
  }
  pages[0].inputs[1].value = 'https://example.com/walks_(local)?a=1&b=2';
  form.listeners.input();
  assert.ok(output.value.endsWith('- [Walks \\[nearby\\]](https://example.com/walks_%28local%29?a=1&b=2): Paths with maps.\n'));
  ids['llms-name'].value = 'Site <script> [name] \\';
  form.listeners.input();
  assert.ok(output.value.startsWith('# Site \\<script\\> \\[name\\] \\\\\n'));
  ids['llms-name'].value = 'Example site';

  for (let index = 1; index < 10; index += 1) {
    ids['llms-add'].listeners.click();
    assert.equal(pages[index].hidden, false);
    assert.equal(pages[index].inputs[0].focused, true);
    pages[index].inputs[0].value = 'Page ' + (index + 1);
    pages[index].inputs[1].value = 'https://example.com/' + (index + 1);
    pages[index].inputs[2].value = 'A page note.';
  }
  ids['llms-add'].listeners.click();
  assert.equal(ids['llms-add'].disabled, true);
  form.listeners.input();
  assert.equal(output.value.split('\n').filter(line => line.startsWith('- [')).length, 10);

  let copied;
  navigator.clipboard = {writeText(text) { copied = text; return Promise.resolve(); }};
  const click = copy.listeners.click();
  assert.equal(copied, output.value, 'clipboard write must start in the click handler');
  await click;
  assert.match(ids['llms-status'].textContent, /^Copied\./);
  navigator.clipboard = {writeText() { return Promise.reject(new Error('denied')); }};
  await copy.listeners.click();
  assert.equal(output.focused, true);
  assert.equal(output.selected, true);
  output.selected = false;
  delete navigator.clipboard;
  await copy.listeners.click();
  assert.equal(output.selected, true);
  pages[0].inputs.forEach(input => { input.value = ''; });
  form.listeners.input();
  assert.equal(output.value.split('\n').filter(line => line.startsWith('- [')).length, 9);
  ids['llms-name'].value = '  ';
  form.listeners.input();
  assert.equal(output.value, '');
  assert.equal(copy.disabled, true);
  console.log('LLMS GENERATOR ok: live text, valid URLs, Markdown escaping, 10 pages, copy and fallback');
}
main().catch(error => { console.error(error); process.exitCode = 1; });
"""


def check_generator_script(page):
    script = next(script for script in page.scripts if "const form = document.getElementById('llms-form')" in script)
    result = subprocess.run(["node", "-e", NODE_TEST], input=json.dumps(script),
                            capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr
    print(result.stdout.strip())


def check_chatgpt_markup():
    line = '<a href="/ai-assistants/">Also inside ChatGPT: check any page from a chat.</a>'
    blocks = {
        "ai-assistants/index.html": (
            '<h2>Use it inside ChatGPT</h2>\n'
            '<p>Check Engine SEO needs no account and runs five read-only checks on one page, covering '
            'SEO score and top fix, AI crawler access, redirects, headers, and snippet preview.</p>\n'
            '<p><a class="btn" href="https://chatgpt.com/plugins/plugin_asdk_app_6aef6b89f90481919a4b2260f5bb14d1" '
            'rel="noopener">Add Check Engine to ChatGPT</a></p>\n\n'
            '<h2>From one page to the whole site</h2>'
        ),
        "index.html": '  title, meta tag and structured data checks.</p>\n  <p class="sec-sub">' + line + '</p>',
        "download/index.html": 'in each area, to send to a client or a colleague.</p>\n<p>' + line + '</p>',
    }
    for relative, block in blocks.items():
        assert (SITE / relative).read_text(encoding="utf-8").count(block) == 1, \
            f"{relative}: keep the ChatGPT block byte-for-byte"


def check_hub_faq():
    page = Page((SITE / "tools/index.html").read_text(encoding="utf-8"))
    questions = {"Are these tools free?", "Do they check my whole site?",
                 "Do you store the sites I check?"}
    words = " ".join(" ".join(page.words).split())
    for question in questions:
        assert question in words, f"tools index must visibly answer: {question}"
    assert sum(attrs.get("class") == "faq-item" for tag, attrs in page.tags) == 3
    schemas = [json.loads(script) for script in page.scripts if script.lstrip().startswith('{')]
    faq = next(schema for schema in schemas if schema.get("@type") == "FAQPage")
    assert {item["name"] for item in faq["mainEntity"]} == questions
    for item in faq["mainEntity"]:
        assert item["name"] in words, "FAQ schema questions must be visible"
        answer = " ".join(" ".join(Page(item["acceptedAnswer"]["text"]).words).split())
        assert answer in words, "FAQ schema answers must be visible"
    privacy = Page((SITE / "legal/privacy/index.html").read_text(encoding="utf-8"))
    privacy_words = " ".join(" ".join(privacy.words).split())
    for phrase in ("The checkers set no cookie and store nothing in your browser.",
                   "keeps a summary of the result for one hour so a repeat check is quick.",
                   "deleted when the day ends"):
        assert phrase in words and phrase in privacy_words, "keep the privacy answer tied to the policy"


def main():
    page = check_tool()
    check_generator_script(page)
    check_app_links()
    check_chatgpt_markup()
    check_hub_faq()
    print("FREE TOOLS BACKLOG ok: generator, index, sitemap, browser-only scripts, "
          "11 app links, exact ChatGPT blocks, visible FAQs")


if __name__ == "__main__":
    main()
