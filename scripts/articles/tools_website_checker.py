#!/usr/bin/env python3
"""The free, limited site check. The crawler is a separate Worker."""
from __future__ import annotations

import html
import json
from pathlib import Path

from brand import SHORT
from render import DATA, N_CHECKS, N_LANES, SAMPLE_REPORT, buy_block, render
from tools_free import _form, audit_next, how_it_works


# Keep the endpoint in one place, at the top of the browser script.
CHECKER_JS = r"""
(function () {
  const ENDPOINT = 'https://site-check.kerrco.workers.dev';
  const form = document.getElementById('checker');
  const input = document.getElementById('checker-url');
  const status = document.getElementById('checker-status');
  const button = form.querySelector('button');
  const result = document.getElementById('website-result');
  const next = document.getElementById('checker-next');

  function el(id) { return document.getElementById(id); }
  function addText(parent, tag, text) {
    const node = document.createElement(tag);
    node.textContent = text;
    parent.appendChild(node);
    return node;
  }

  if (!window.fetch) {
    status.textContent = 'This browser cannot run the checker. Try a newer browser.';
    button.disabled = true;
    return;
  }
  button.disabled = false;

  form.addEventListener('submit', async function (event) {
    event.preventDefault();
    if (button.disabled) return;
    result.hidden = true;
    next.hidden = true;
    const value = input.value.trim();
    if (!value) {
      status.textContent = 'Enter a website address.';
      return;
    }
    let address;
    try {
      address = new URL(/^[a-z][a-z0-9+.-]*:\/\//i.test(value) ? value : 'https://' + value);
      if (!/^https?:$/.test(address.protocol) || !address.hostname) throw new Error('address');
    } catch (error) {
      status.textContent = 'Enter a public http or https website address.';
      return;
    }

    button.disabled = true;
    result.setAttribute('aria-busy', 'true');
    const started = Date.now();
    function progress() {
      status.textContent = 'Reading up to 25 pages of ' + address.host +
        '. This takes about 30 seconds. ' + Math.floor((Date.now() - started) / 1000) + ' seconds elapsed.';
    }
    progress();
    const counter = setInterval(progress, 1000);
    const controller = new AbortController();
    let timedOut = false;
    let timeout;
    try {
      const deadline = new Promise(function (resolve, reject) {
        timeout = setTimeout(function () {
          timedOut = true;
          controller.abort();
          reject(new Error('timeout'));
        }, 45000);
      });
      const response = fetch(ENDPOINT + '/site-check?url=' + encodeURIComponent(address.href), {
        signal: controller.signal,
        credentials: 'omit'
      }).then(async function (response) {
        return { ok: response.ok, data: await response.json() };
      });
      const reply = await Promise.race([response, deadline]);
      const data = reply.data;
      if (!reply.ok || data.error) {
        status.textContent = data.message || 'That website could not be checked. Try again in a minute.';
        return;
      }
      if (data.refused) {
        status.textContent = 'This site asked not to be checked, so we did not look.';
        return;
      }

      const count = data.pages_checked;
      const issues = data.issues.slice(0, 8);
      el('website-heading').textContent = 'What a quick check of ' + count + ' pages found';
      el('website-scope').textContent = (data.truncated
        ? 'We read the first ' + count + ' pages of ' + data.site + '.'
        : 'We read ' + count + ' pages of ' + data.site + '.') +
        ' This is a quick check.';
      el('website-clean').textContent = issues.length ? '' : (count
        ? 'No issues were found by this quick check on the pages read.'
        : 'No pages were read, so there are no page findings to show.');
      const findings = el('website-issues');
      findings.replaceChildren();
      issues.forEach(function (issue) {
        const item = addText(findings, 'li', /^[0-9]+ of /.test(issue.label) ? issue.label : issue.count + ' of ' + issue.of + ' pages ' + issue.label);
        if (issue.examples && issue.examples.length) {
          const paths = document.createElement('p');
          paths.className = 'table-note trace-url';
          issue.examples.slice(0, 3).forEach(function (path) { addText(paths, 'code', path); });
          item.appendChild(paths);
        }
      });
      const fine = el('website-fine');
      fine.replaceChildren();
      data.fine.slice(0, 5).forEach(function (item) { addText(fine, 'li', item.label); });
      el('website-fine-heading').hidden = !fine.children.length;
      el('website-robots').textContent = (data.robots.found
        ? 'We found robots.txt.' : 'We did not find robots.txt.') + ' ' +
        (data.robots.sitemap_found ? 'We found a sitemap.' : 'We did not find a sitemap.') +
        (data.blocked_by_robots ? ' Some pages asked not to be checked, so we left them out.' : '');
      el('checker-own').textContent = 'This quick check read ' + count +
        ' pages. __APP__ reads every page and runs __CHECKS__ checks across __AREAS__ areas.';
      result.hidden = false;
      next.hidden = false;
      status.textContent = data.from_cache
        ? 'Done. This summary was checked within the last hour.' : 'Done. Your quick check is ready.';
      if (window.plausible) window.plausible('Checker', {
        props: { tool: 'website', issues: String(issues.length) }
      });
    } catch (error) {
      status.textContent = timedOut
        ? 'The check took longer than 45 seconds, so we stopped waiting. Try again in a minute.'
        : 'The checker could not be reached. Check your connection and try again in a minute.';
    } finally {
      clearInterval(counter);
      clearTimeout(timeout);
      button.disabled = false;
      result.setAttribute('aria-busy', 'false');
    }
  });
})();
"""


def website_checker() -> Path:
    sample = json.loads((DATA / 'sample-run.json').read_text())
    image = sample['image']
    script = (CHECKER_JS.replace('__APP__', SHORT).replace('__CHECKS__', str(N_CHECKS))
              .replace('__AREAS__', str(N_LANES)))
    form = _form('Check this website', 'yourbusiness.com').replace('Page address', 'Website address')
    form = form.replace('type="submit"', 'type="submit" disabled')
    body = f"""
<style>
#website-issues>li{{padding:.8rem 0;border-bottom:1px solid var(--border)}}
#website-issues p{{margin:.4rem 0 0}}
#website-issues code{{display:inline-block;margin-right:.6rem;overflow-wrap:anywhere}}
</style>
<p class="lede">Find the top issues across up to 25 pages of your website. Type your address
and allow about 30 seconds. You will see how many pages each issue affects, with paths you can
look at first. Free, with no account.</p>
{form}
<noscript><p>Turn on JavaScript to run this website check.</p></noscript>

<section class="tool-out" id="website-result" aria-labelledby="website-heading" aria-busy="false" hidden>
  <h2 id="website-heading"></h2>
  <p id="website-scope" class="trace-url"></p>
  <p id="website-clean"></p>
  <ol class="findings" id="website-issues"></ol>
  <h3 id="website-fine-heading">What looked fine</h3>
  <ul id="website-fine"></ul>
  <p class="table-note" id="website-robots"></p>
</section>
{audit_next('tools-website-checker', what='a quick check', own=True,
            summary='Get the fixes in order, with the page and the change to make. '
                    'The free download shows your site score and the top problem in full.')}

<figure class="shot">
  <a href="{SAMPLE_REPORT}" data-ev="Sample report" data-ev-button="tools-website-checker-sample">
    <img src="{html.escape(image['src'])}" width="{image['width']}" height="{image['height']}"
         decoding="async" alt="A real {SHORT} app report, with findings ranked by what to fix first">
  </a>
  <figcaption>The next step in the app. This is our recorded sample report from {sample['recorded']}.
  The quick check above gives you counts and example paths for your own site.</figcaption>
</figure>

{how_it_works([
    'The top issues in order, with a page count for each',
    'Up to three example paths per issue, so you know where to look',
    'Checks that came back fine, plus whether we found robots.txt and a sitemap',
], free='The address goes to our checker. Only a summary is cached for one hour. Nothing else is kept.',
   steps=['Enter the address of the website you want to check.',
          'Press <strong>Check this website</strong> and watch the elapsed time.',
          'Start with the first issue. Use the app to check every page and rank the fixes.'],
   step_up=f'{SHORT} crawls every page and runs {N_CHECKS} checks across {N_LANES} areas. '
           'The app gives you the page and the change to make for each fix.')}

<h2>A quick check before a full crawl</h2>
<p>A homepage can look fine while a shared page template leaves a problem across a section.
This check reads linked pages on the same host, up to the limit, and counts what it finds.
The first issue gives you somewhere to start.</p>
<p>The result covers only the pages read. Pages blocked by robots.txt are left out.
A short check can miss pages and issues that a full crawl finds.</p>
<p>Checked 10 November 2026.</p>

<h2>Related</h2>
<ul>
  <li><a href="/tools/seo-checker/">Check one page in more detail</a></li>
  <li><a href="/tools/robots-txt-tester/">Find the robots.txt rule that blocks a page</a></li>
  <li><a href="/learn/seo-audit/">What an SEO audit checks</a></li>
</ul>
<script>{script}</script>
"""
    return render(
        cat='tools', slug='website-checker',
        title='Free website checker: check up to 25 pages of your site',
        desc=('Check up to 25 pages of your website for free. See the top issues with your own page '
              'counts and example paths. No account. Allow about 30 seconds.'),
        h1='Free website checker: check up to 25 pages of your site',
        crumb=f'<a href="/">{SHORT}</a> / <a href="/tools/">Tools</a> / Website checker',
        body=body,
        published='2026-11-10',
        schema_type='WebPage',
        faq=[
            ('What does this website checker check?',
             'It checks page basics such as meta descriptions across up to 25 linked pages on the same host. '
             'It reports the top issues found, '
             'with counts and example paths. It also says whether it found robots.txt and a sitemap.'),
            ('What does the quick check leave out?',
             'It can miss pages beyond the limit, pages that need JavaScript to show their content, '
             'and pages that refuse access. It does not tell you your search rank or give a whole-site score.'),
            ('How many pages will it read?',
             'Up to 25 pages on the same host. It may read fewer if time runs out, fewer pages can be reached, '
             'or robots.txt blocks them. The result says how many pages were read.'),
            ('Is the check private?',
             'The address you type goes to our checker. Nothing is kept beyond a one-hour cached summary. '
             'Page bodies are not stored. You do not need an account.'),
            ('Does it respect robots.txt?',
             'Yes. If the site asks our checker to stay out, it stops. If only some pages are blocked, '
             'it leaves those pages out and tells you. It identifies itself as CheckEngineBot.'),
            ('Why stop at 25 pages?',
             'The limit keeps this free check short and limits requests to your server. '
             'It gives you a place to start while leaving the full crawl to the app.'),
            (f'How is this different from the {SHORT} app?',
             f'This is a quick check of up to 25 pages. {SHORT} reads every page and runs {N_CHECKS} checks '
             f'across {N_LANES} areas. It ranks the fixes and shows the page and the change to make.'),
        ],
        closer=buy_block('tools-website-checker', try_app='tools-website-checker-try-free'),
    )
