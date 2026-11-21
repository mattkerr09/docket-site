#!/usr/bin/env python3
"""Offline fingerprint, sitemap and spread regressions. Writes only to scratch."""
from __future__ import annotations

import contextlib
import datetime
import io
import json
import shutil
import subprocess
import sys
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import build
import render
from brand import BASE, LASTMOD_FILE
from verify_lastmod_spread import verify

ROOT = Path(__file__).resolve().parents[1]
OLD_SALE = ("Black Friday sale: $19.99 once, 32% off our November price of $29.50, "
            "through December 2. Then $39.")
SALE = "Black Friday sale: $19.99 once through December 2. Then $39."


def article(body="A real answer."):
    return (f'<title>A useful title</title><meta name="description" content="An answer.">'
            f'<article><h1>A heading</h1><p>{body}</p></article>')


class FingerprintTests(unittest.TestCase):
    def assert_same(self, a, b):
        self.assertEqual(build.page_fingerprint(a), build.page_fingerprint(b))

    def test_sale_helpers_in_body_faq_title_and_description(self):
        for before, after in ((OLD_SALE, SALE), (SALE, SALE.replace('$19.99', '$18.99')),
                              (render.PRICE_COMPACT, '$24.99 once through December 3, then $49'),
                              ('$39 once', '$49 once'),
                              ('$39, paid once', '$49, paid once'),
                              ('$39 applies from v1.0', '$49 applies from v1.0')):
            with self.subTest(before=before):
                for raw in (article(before + ' Keep this answer.'),
                            article().replace('A useful title', before + ' A useful title'),
                            article().replace('An answer.', before + ' An answer.'),
                            article(f'<div class="faq-item"><h3>What does it cost?</h3><p>{before}</p></div>')):
                    self.assert_same(raw, raw.replace(before, after))

    def test_shared_markup_can_change_or_be_removed(self):
        blocks = (
            '<p class="byline">By Matt Kerr <span>Published <time>19 November 2026</time></span></p>',
            '<div class="buy-block compact"><div><p>Buy $39</p></div><p>A Buy note.</p></div>',
            '<aside class="buy-strip"><p>Buy now.</p></aside>',
            '<p class="hero-note price-anchor">Shared price note.</p>',
            '<p data-founding-until="2026-12-03"><span>A sale.</span></p>',
            '<div data-founding><div><span>A sale.</span></div></div>',
            '<li data-sister-offer><strong>Crisp</strong> $9.99</li>',
            '<p><a href="https://example.invalid/buy/bundle">All three apps for $34.99</a> ($46.97 bought apart, $34.99 together).</p>',
            '<li><strong>Outlier</strong> $16.99 <a href="https://example.invalid/buy/outlier">Buy</a></li>',
            '<footer aria-label="Next step"><div><p>Try the app.</p></div></footer>',
            '<div id="try"><p>Next step.</p></div>',
            '<p class="next-step"><a href="/download/">Try it</a></p>',
            '<p data-tool-app class="tool-step-up">Check the site.</p>',
            '<section class="related-pages"><h2>Related</h2><p>Links.</p></section>',
            '<h2>Which other crawlers does this operator run?</h2><ul><li>Another crawler</li></ul>',
            '<p><a href="/guide/">A related guide</a></p>',
            '<p>For the other pairings, read <a href="/vs/">a comparison</a>.</p>',
            '<p class="founder-note">Built by Matt Kerr.</p>',
            '<p class="claims-note">Other products here are described from their public pages and are not dated on this page.</p>',
        )
        for block in blocks:
            with self.subTest(block=block):
                self.assert_same(article(), article().replace('</article>', block + '</article>'))
        self.assert_same(article('Published 2026-11-19 Updated 20 November 2026 v1.3.164 98.5 MB'),
                         article('Published 2026-11-20 Updated 21 November 2026 v1.3.165 101 MB'))

    def test_keeps_every_kind_of_own_content(self):
        for body in ('<h2>A heading</h2>', '<p>A body paragraph.</p>',
                     '<div class="faq-item"><h3>A question?</h3><p>An answer.</p></div>',
                     '<table><tr><th>A column</th><td>$279 a year</td></tr></table>',
                     '<p class="hero-note">Checked on 2026-11-19. A competitor fact.</p>',
                     '<p class="claims-note">Checked on 2026-11-19. A sourced fact.</p>'):
            with self.subTest(body=body):
                self.assertNotEqual(build.page_fingerprint(article(body)),
                                    build.page_fingerprint(article(body.replace('A ', 'The ').replace('279', '280'))))
        for old in ('A useful title', 'An answer.'):
            self.assertNotEqual(build.page_fingerprint(article()),
                                build.page_fingerprint(article().replace(old, 'Edited text')))
        self.assert_same(article('Download a 120 MB file.'), article('Download an 80 MB file.'))
        self.assert_same(article('A &amp; B'), article('A &#38; B'))
        self.assert_same(article('Keep this.'), article('Keep <strong>this</strong>.'))


class BuildDateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.site = Path(self.temp.name) / 'site'
        self.site.mkdir()
        self.lastmod = Path(self.temp.name) / 'lastmod.json'
        stack = contextlib.ExitStack()
        self.addCleanup(stack.close)
        stack.enter_context(patch.object(build, 'SITE', self.site))
        stack.enter_context(patch.object(build, 'LASTMOD', self.lastmod))
        self.pages = []
        self.records = {}
        for i in range(3):
            page = self.site / f'page-{i}/index.html'
            page.parent.mkdir()
            page.write_text(article(f'Own answer {i}. Checked on 2026-11-18. {OLD_SALE}')
                            .replace('</article>', '<p class="byline">By Matt Kerr</p></article>'))
            self.pages.append(page)
            self.records[f'page-{i}/index.html'] = {
                'hash': build.page_fingerprint(page.read_text()), 'date': '2026-11-18'}
        self.lastmod.write_text(json.dumps(self.records))

    def rebuild(self):
        build.write_sitemap(self.pages)
        return json.loads(self.lastmod.read_text())

    def test_sale_byline_or_price_changes_move_no_dates(self):
        for page in self.pages:
            page.write_text(page.read_text().replace(OLD_SALE, SALE).replace('Matt Kerr', 'Matthew Kerr'))
        result = self.rebuild()
        self.assertTrue(all(r['date'] == '2026-11-18' and not r['changed_in_build'] for r in result.values()))
        for page in self.pages:
            page.write_text(page.read_text().replace(SALE, SALE.replace('$19.99', '$18.99')))
        self.assertEqual(result, self.rebuild())

    def test_one_article_body_moves_only_that_page(self):
        page = self.pages[1]
        page.write_text(page.read_text().replace('Own answer 1', 'A corrected answer'))
        result = self.rebuild()
        for key, record in result.items():
            changed = key == 'page-1/index.html'
            self.assertEqual(record['date'], datetime.datetime.now(datetime.timezone.utc).date().isoformat() if changed else '2026-11-18')
            self.assertEqual(record['changed_in_build'], changed)
        # Evidence records this build, not a comparison with a committed HEAD.
        self.assertFalse(any(r['changed_in_build'] for r in self.rebuild().values()))

    def test_checked_on_date_is_a_real_change(self):
        page = self.pages[2]
        page.write_text(page.read_text().replace('Checked on 2026-11-18', 'Checked on 2026-11-20'))
        result = self.rebuild()
        self.assertEqual([key for key, rec in result.items() if rec['changed_in_build']], ['page-2/index.html'])
        self.assertEqual(result['page-2/index.html']['date'], datetime.datetime.now(datetime.timezone.utc).date().isoformat())


class HistoryTests(unittest.TestCase):
    def test_walks_past_shared_edits_and_keeps_noindex_examples_and_new_pages(self):
        import collect_lastmod
        with tempfile.TemporaryDirectory(prefix="test-lastmod-history-") as temporary:
            root = Path(temporary)
            site = root / 'site'
            site.mkdir()
            store = root / 'lastmod.json'
            env = dict(os.environ, GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_NOSYSTEM='1')

            def git(*args):
                return subprocess.run(['git', *args], cwd=root, env=env,
                                      capture_output=True, text=True, check=True)

            def commit(day):
                env['GIT_AUTHOR_DATE'] = env['GIT_COMMITTER_DATE'] = day + 'T12:00:00Z'
                git('add', 'site/index.html')
                git('-c', 'user.name=History Test', '-c', 'user.email=test@example.invalid',
                    '-c', 'commit.gpgsign=false', '-c', f'core.hooksPath={os.devnull}',
                    'commit', '--quiet', '-m', 'Page revision')

            git('init', '--quiet')
            page = site / 'index.html'
            first = article('An article with a noindex example: &lt;meta content="noindex"&gt;. ' + OLD_SALE)
            page.write_text(first)
            commit('2026-11-10')
            page.write_text(first.replace(OLD_SALE, SALE).replace('</article>', '<p class="byline">By Matthew Kerr</p></article>'))
            commit('2026-11-19')
            fresh = site / 'new/index.html'
            fresh.parent.mkdir()
            fresh.write_text(article('New content not committed yet.'))
            (site / 'sitemap.xml').write_text(f'<urlset><url><loc>{BASE}/</loc></url>'
                                             f'<url><loc>{BASE}/new/</loc></url></urlset>')
            with patch.object(collect_lastmod, 'ROOT', root), patch.object(collect_lastmod, 'LASTMOD', store), \
                    patch.object(sys, 'argv', ['collect_lastmod.py', '--site', str(site)]), \
                    patch.dict(os.environ, env), contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(collect_lastmod.main(), 0)
            records = json.loads(store.read_text())
            self.assertEqual(set(records), {'index.html', 'new/index.html'})
            self.assertEqual(records['index.html']['date'], '2026-11-10')
            self.assertEqual(records['new/index.html']['date'], datetime.datetime.now(datetime.timezone.utc).date().isoformat())
            self.assertEqual(records['index.html']['hash'], build.page_fingerprint(page.read_text()))


class WholeSiteTests(unittest.TestCase):
    def test_shared_renderer_changes_leave_all_sitemap_dates_alone(self):
        # Exercise the actual renderer and all pages, including helper text in
        # title/description/FAQ, rather than only synthetic HTML substitutions.
        from test_launch_price_copy import scratch
        with tempfile.TemporaryDirectory(prefix="test-honest-lastmod-") as temporary:
            root = Path(temporary)
            scratch(root)
            env = dict(os.environ, DOCKET_SKIP_BRAND_ASSETS="1", SITE_BRAND="checkengine")
            env.pop("DOCKET_DEPLOY", None)

            def rebuild():
                result = subprocess.run([sys.executable, "scripts/build.py"], cwd=root,
                                        env=env, capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stderr[-4000:])
                return json.loads((root / "data/page-lastmod-checkengine.json").read_text())

            seeded = json.loads((root / "data/page-lastmod-checkengine.json").read_text())
            before = rebuild()
            self.assertEqual({k: (v['hash'], v['date']) for k, v in seeded.items()},
                             {k: (v['hash'], v['date']) for k, v in before.items()})
            self.assertFalse(any(v['changed_in_build'] for v in before.values()))
            renderer = root / "scripts/render.py"
            original = renderer.read_text()
            variants = (
                original.replace('By Matthew Kerr', 'By A Different Author'),
                original.replace('FOUNDING_OFF_CENTS = 1901', 'FOUNDING_OFF_CENTS = 1902'),
                original.replace('f"{SALE_NAME}: {FOUNDING_NOW} once through {FOUNDING_END_DAY_US}. Then {LATER_STR}."',
                                 'f"{SALE_NAME}: {FOUNDING_NOW} once, 32% off our November price of "'
                                 'f"{NOVEMBER_PRICE_STR}, through {FOUNDING_END_DAY_US}. Then {LATER_STR}."'),
            )
            for source in variants:
                self.assertNotEqual(original, source)
                renderer.write_text(source)
                # Discard bytecode so same-second source rewrites cannot reuse
                # a cached renderer in the child interpreter.
                shutil.rmtree(root / 'scripts/__pycache__', ignore_errors=True)
                after = rebuild()
                self.assertEqual({k: v['date'] for k, v in before.items()},
                                 {k: v['date'] for k, v in after.items()})
                self.assertEqual({k: v['hash'] for k, v in before.items()},
                                 {k: v['hash'] for k, v in after.items()})
                self.assertFalse(any(v['changed_in_build'] for v in after.values()))


class SpreadTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.site = Path(self.temp.name)
        self.sitemap = self.site / 'sitemap.xml'
        self.store = self.site / 'lastmod.json'

    def run_spread(self, records, reason=''):
        urls = ''.join(f'<url><loc>{BASE}/{key.removesuffix("index.html")}</loc>'
                       f'<lastmod>{record["date"]}</lastmod></url>' for key, record in records.items())
        self.sitemap.write_text('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' + urls + '</urlset>')
        self.store.write_text(json.dumps(records))
        with contextlib.redirect_stdout(io.StringIO()) as output:
            result = verify(self.sitemap, self.store, reason)
        return result, output.getvalue()

    def fixture(self, crowded=441, changed=0, count=455):
        return {f'page-{i}/index.html': {'date': '2026-11-19' if i < crowded else f'2026-10-{i % 28 + 1:02}',
                                      'hash': str(i), 'changed_in_build': i < changed}
                for i in range(count)}

    def test_441_of_455_fails_and_tells_operator_what_to_do(self):
        code, output = self.run_spread(self.fixture())
        self.assertEqual(code, 1)
        self.assertIn('441/455', output)
        self.assertIn('DOCKET_LASTMOD_REASON', output)
        self.assertIn('collect_lastmod.py', output)

    def test_real_changes_or_one_line_reason_pass(self):
        self.assertEqual(self.run_spread(self.fixture(changed=441))[0], 0)
        self.assertEqual(self.run_spread(self.fixture(), 'We revised the content on every article.')[0], 0)
        for reason in ('', '  ', 'Line one\nLine two'):
            self.assertEqual(self.run_spread(self.fixture(), reason)[0], 1)
        self.assertEqual(self.run_spread(self.fixture(changed=440))[0], 1)

    def test_twenty_percent_boundary_and_missing_evidence(self):
        self.assertEqual(self.run_spread(self.fixture(crowded=91))[0], 0)
        self.assertEqual(self.run_spread(self.fixture(crowded=92))[0], 1)
        records = self.fixture()
        for record in records.values():
            del record['changed_in_build']
        self.assertEqual(self.run_spread(records)[0], 1)

    def test_distributed_dates_pass_without_a_reason(self):
        self.assertEqual(self.run_spread(self.fixture(crowded=0))[0], 0)

    def test_reseeded_history_obeys_the_same_rule(self):
        records = json.loads((ROOT / 'data' / LASTMOD_FILE).read_text())
        self.assertEqual(records['ai-crawlers/addsearchbot/index.html']['date'], '2026-11-11')
        self.assertEqual(records['checks/ai-crawler-access/index.html']['date'], '2026-11-11')
        # Real history includes pages created together. The requested strict
        # rule rejects historical clusters too; it needs the explicit reason.
        from collections import Counter
        counts = Counter(record['date'] for record in records.values())
        crowded = max(counts.values()) * 5 > len(records)
        code, output = self.run_spread(records)
        self.assertEqual(code, int(crowded), output)
        code, output = self.run_spread(records,
                                      'The crawler and check articles were created together on 11 November.')
        self.assertEqual(code, 0, output)

    def test_missing_and_mismatched_input_fails_even_with_reason(self):
        self.run_spread(self.fixture())
        self.store.write_text('{}')
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(verify(self.sitemap, self.store, 'A real change.'), 1)
            self.sitemap.unlink()
            self.assertEqual(verify(self.sitemap, self.store, 'A real change.'), 1)


if __name__ == '__main__':
    unittest.main()
