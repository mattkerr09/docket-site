#!/usr/bin/env python3
"""A browser-only llms.txt generator."""
from pathlib import Path

from render import render
from tools_free import how_it_works


GENERATOR_JS = r"""
(function () {
  const form = document.getElementById('llms-form');
  const name = document.getElementById('llms-name');
  const summary = document.getElementById('llms-summary');
  const output = document.getElementById('llms-output');
  const status = document.getElementById('llms-status');
  const copy = document.getElementById('llms-copy');
  const add = document.getElementById('llms-add');
  const pages = Array.from(form.querySelectorAll('[data-key-page]'));
  let shown = 1;

  function oneLine(value) {
    return value.replace(/\s+/g, ' ').trim();
  }

  function markdown(value) {
    return oneLine(value).replace(/[\\`*_[\]{}<>#!|]/g, '\\$&');
  }

  function update() {
    output.value = '';
    copy.disabled = true;
    if (!oneLine(name.value) || !oneLine(summary.value)) {
      status.textContent = 'Enter a site name and summary to build your file.';
      return;
    }
    const links = [];
    for (let index = 0; index < shown; index += 1) {
      const fields = pages[index].querySelectorAll('input');
      const title = oneLine(fields[0].value);
      const address = fields[1].value.trim();
      const note = oneLine(fields[2].value);
      if (!title && !address && !note) continue;
      if (!title || !address || !note) {
        status.textContent = 'Fill in the title, URL and note for page ' + (index + 1) + ', or clear all three.';
        return;
      }
      let url;
      try {
        url = new URL(address);
        if (!/^https?:$/.test(url.protocol) || !url.hostname || url.username || url.password) {
          throw new Error('address');
        }
      } catch (error) {
        status.textContent = 'Enter a full http or https URL for page ' + (index + 1) + '.';
        return;
      }
      const destination = url.href.replace(/[()<>]/g, function (character) {
        return '%' + character.charCodeAt(0).toString(16).toUpperCase();
      });
      links.push('- [' + markdown(title) + '](' + destination + '): ' + markdown(note));
    }
    output.value = '# ' + markdown(name.value) + '\n\n> ' + markdown(summary.value) +
      '\n\n## Key pages\n' + links.join('\n') + (links.length ? '\n' : '');
    status.textContent = 'Your llms.txt is ready to copy.';
    copy.disabled = false;
  }

  form.addEventListener('submit', function (event) { event.preventDefault(); });
  form.addEventListener('input', update);
  add.addEventListener('click', function () {
    if (shown >= pages.length) return;
    pages[shown].hidden = false;
    pages[shown].querySelector('input').focus();
    shown += 1;
    add.disabled = shown === pages.length;
  });
  copy.addEventListener('click', async function () {
    if (copy.disabled) return;
    try {
      await navigator.clipboard.writeText(output.value);
      status.textContent = 'Copied. Save the text as llms.txt at your site root.';
    } catch (error) {
      output.focus();
      output.select();
      status.textContent = 'The text is selected. Use your browser copy command, then save it as llms.txt.';
    }
  });
  update();
})();
"""


def generator() -> Path:
    rows = "".join(f"""
  <div data-key-page{'' if index == 1 else ' hidden'}>
    <h3>Page {index}</h3>
    <label for="llms-title-{index}">Page title</label>
    <input id="llms-title-{index}" type="text" maxlength="200">
    <label for="llms-url-{index}">Page URL</label>
    <input id="llms-url-{index}" type="url" inputmode="url" spellcheck="false"
           placeholder="https://example.com/about/">
    <label for="llms-note-{index}">One-line note</label>
    <input id="llms-note-{index}" type="text" maxlength="400">
  </div>""" for index in range(1, 11))
    body = f"""
<p class="lede">Write an llms.txt file for your site. Enter its name, a short summary and up to
10 key pages. The file updates as you type. No account is needed, and the text stays in your browser.</p>

<form class="checker-form serp-form" id="llms-form" autocomplete="off">
  <label for="llms-name">Site name</label>
  <input id="llms-name" type="text" maxlength="200" required>
  <label for="llms-summary">Site summary</label>
  <textarea id="llms-summary" rows="3" maxlength="2000" required></textarea>
  <h2>Key pages</h2>
  <p>Add up to 10 pages. Leave unused pages blank. Use full URLs that start with https:// or http://.</p>
  {rows}
  <button class="btn-ghost" type="button" id="llms-add">Add another page</button>
</form>
<noscript><p>Turn on JavaScript in your browser to build and copy the file.</p></noscript>

<div class="checker-form serp-form">
  <label for="llms-output">Your llms.txt</label>
  <textarea id="llms-output" rows="12" readonly spellcheck="false"></textarea>
  <button class="btn" type="button" id="llms-copy" disabled>Copy</button>
  <p class="checker-status" id="llms-status" role="status" aria-live="polite"></p>
</div>

{how_it_works([
    'Your site name as the main heading',
    'Your summary as a quoted paragraph',
    'A Key pages section with a link and note for each page you add',
], free='Nothing to install, and nothing you type leaves your browser.',
   steps=['Type your site name and a one-paragraph summary.',
          'Add the title, full URL and a short note for each key page.',
          'Press Copy, save the text as llms.txt, and put it at your site root.'],
   step_up=('To check the pages your site serves, <a href="/download/">Check Engine SEO</a> '
            'reads every page and reports what to fix first.'))}

<section aria-labelledby="llms-explainer">
<h2 id="llms-explainer">What is llms.txt?</h2>
<p>llms.txt is a plain text file that gives AI assistants a short guide to your site.
It uses Markdown headings, a summary and links to pages you choose. Put it at your site root,
such as <code>https://example.com/llms.txt</code>, so it has a clear address.
The file does not guarantee that AI assistants will read it.</p>
</section>

<h2>What should I write in the summary?</h2>
<p>Say what your site covers and who it is for. Keep it to one paragraph that still makes sense
when read on its own. Use the name people see on your homepage. A reader should be able to tell
what they will find before opening a link. If your site has several sections, describe their shared
purpose here and use the page notes to explain the parts.</p>

<h2>Which pages should I include?</h2>
<p>Choose pages that help a reader understand your site. Your main service page, product guide,
help section, contact page or documentation may belong in the list. Use the page's real title and
its full public URL. Write a short note about what the page contains. Check each link yourself
before saving the file, since this generator builds the text from what you type.</p>
<p>You can leave the key pages empty while you work on the summary. Once you start a page entry,
fill in all three fields or clear them to leave that entry out. The generator accepts up to 10
entries. You can edit or clear any field and the output will update with it.</p>

<h2>How do I put the file on my site?</h2>
<ol>
<li>Press Copy and paste the result into a plain text editor.</li>
<li>Save it with the exact name <code>llms.txt</code>. Check that your editor has kept the
file as plain text and has not added another file extension.</li>
<li>Upload it to the top folder of your published site. If your site uses a build tool,
put it in the folder that tool copies to the site root.</li>
<li>Open your domain followed by <code>/llms.txt</code> in a browser. You should see the
same heading, summary and links you copied here.</li>
</ol>
<p>If Copy cannot use your clipboard, the generator selects the output. Use your browser's copy
command to copy the selected text. You can also click the output, select all of it and copy it
yourself. Keep a copy with your site's source so you can update it when a page moves.</p>

<h2>When should I update it?</h2>
<p>Read the summary again when your site's purpose changes. Check the page list when you rename,
move or remove a page. Keep the notes tied to what each linked page says. Anyone who opens the file
can read it, so include only text and links you want to make public.</p>

<h2>Related</h2>
<ul>
<li><a href="/tools/ai-crawler-checker/">Check your robots.txt rules for AI crawlers</a></li>
<li><a href="/tools/">All free tools</a></li>
</ul>
<script>{GENERATOR_JS}</script>
"""
    return render(
        cat="tools", slug="llms-txt-generator",
        title="llms.txt generator: write your site's AI file in a minute",
        desc="Write an llms.txt file with your site name, summary and up to 10 key pages. Copy it from your browser and put it at your site root. No account.",
        h1="llms.txt generator",
        crumb='<a href="/">Check Engine SEO</a> / <a href="/tools/">Tools</a> / llms.txt generator',
        body=body,
        published="2026-11-15",
        schema_type="WebPage",
        browser_only=True,
    )
