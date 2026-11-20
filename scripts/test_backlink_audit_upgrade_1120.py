#!/usr/bin/env python3
"""Offline backlink-audit checks, with base/current scratch builds."""
from __future__ import annotations

import ast
from html import unescape
from pathlib import Path
import re
import sys
import tempfile
import xml.etree.ElementTree as ET

from test_measured_answers import Visible
from test_real_questions_1120 import (
    article_html, check_answer, prose, schemas, shingles, similarity,
    without_price_helpers,
)
from test_thank_you_review_ask import environment, protected_state, run, scratch_copy

ROOT = Path(__file__).resolve().parent.parent
BASE = '18f42da0952516be251029f22d70452f3d385acb'
GENERATOR = 'scripts/articles/howto_backlink_audit.py'
PAGE = 'how-to/backlink-audit/index.html'
URL = '/how-to/backlink-audit/'
READ = '20 November 2026'
OLDER_READ = '19 October 2026'
FACTS = Path('/Users/matthewkerr/ops/research/articles/data-2026-11-20/backlink-audit-upgrade/FACTS.md')
LINKS = 'https://support.google.com/webmasters/answer/9049606?hl=en'
DISAVOW = 'https://support.google.com/webmasters/answer/2648487?hl=en'
SPAM = 'https://developers.google.com/search/docs/essentials/spam-policies'
SPEC = {'words': ('backlink', 'audit'), 'figures': {'1,000', '20', '2026'},
        'sources': (LINKS, DISAVOW)}


def unstamp(raw):
    return re.sub(r'(<meta name="build-id" content=")[^"]+(">)', r'\1BUILD\2', raw)


def section(raw, heading):
    return article_html(raw).split(f'<h2>{heading}</h2>', 1)[1].split('<h2>', 1)[0]


def internal_links(raw):
    return {unescape(href) for href in re.findall(r'href="(/[^"#]*)"', raw)}


def check_page(raw):
    answer = check_answer(raw, SPEC)
    body, text = article_html(raw), prose(raw)
    title = unescape(re.search(r'<title>(.*?)</title>', raw).group(1))
    assert title.startswith('Backlink audit') and len(title) <= 60, 'title intent'
    assert f'<h1>{title}</h1>' in raw, 'H1 differs from title'
    assert f'<link rel="canonical" href="https://checkengineseo.com{URL}">' in raw, 'URL changed'
    assert 'By Matthew Kerr' in text, 'byline changed'
    assert 'Published <time datetime="2026-09-14">14 September 2026</time>' in raw, 'published date changed'
    assert f'Updated <time datetime="2026-11-20">{READ}</time>' in raw, 'updated date missing'
    assert schemas(raw, 'Article')[0]['dateModified'] == '2026-11-20', 'schema date missing'
    assert all(phrase in answer for phrase in ('list who links', 'do not recognise',
               'leave most of them alone', 'manual action', READ)), 'direct answer incomplete'
    headings = list(re.finditer(r'<h2>(.*?)</h2>', body, re.S))
    assert headings[0].group(1) == 'How to do a backlink audit, step by step', 'steps not first'
    steps = re.search(r'<ol>(.*?)</ol>', body, re.S)
    assert steps and headings[0].end() < steps.start() < steps.end() < headings[1].start(), 'step placement'
    items = re.findall(r'<li>(.*?)</li>', steps.group(1), re.S)
    assert len(items) == 7, 'step count'
    for item in items:
        assert f'href="{LINKS}"' in item and READ in item, 'step source missing'
    for item, phrases in zip(items, (
        ('Links > External links > Top linking sites', 'verified'),
        ('Export', 'sample'), ('Sort', 'linking site'),
        ('do not recognise', 'context'), ('Top linking text', 'domain-level'),
        ('Leave ordinary links alone', 'removal', 'manual action'),
        ('Re-check later', 'samples', 'does not prove'),
    )):
        assert all(phrase in Visible(item).text() for phrase in phrases), 'step instruction missing'
    assert f'href="{DISAVOW}"' in items[5], 'decision source missing'
    table = section(raw, 'Where to get the list of links')
    assert '<table>' in table and table.count('<tr>') >= 4, 'source table missing'
    for heading in ('What it shows', 'Page-level or domain-level', 'Cost basis as stated', 'Limit'):
        assert heading in table, 'table column missing'
    rows = re.findall(r'<tr>(.*?)</tr>', table, re.S)[1:]
    assert len(rows) == 4, 'unexpected source row'
    for row, phrases in zip(rows, (
        ('Google Search Console', 'verified site', 'Free', 'sample', '1,000', READ),
        ('Check Engine', 'Domain-level only', 'No subscription', 'No linking URLs', 'anchor text', READ),
        ('Ahrefs Backlink Checker', 'Page-level', 'free tier', 'allowance not stated', OLDER_READ),
        ('Ahrefs Site Explorer', 'Page-level', 'Paid', 'allowance not stated', OLDER_READ),
    )):
        assert all(phrase in Visible(row).text() for phrase in phrases), 'table fact changed'
    own = Visible(section(raw, 'We ran it on our own sites')).text()
    assert all(phrase in own for phrase in (READ, 'our own four sites', 'None was found',
               'inconclusive', 'scanned', 'did not request', 'Search Console')), 'own run missing or overstated'
    assert not re.search(r'\b[\w-]+\.(?:com|app|host)\b', own), 'own domain named'
    disavow = Visible(section(raw, 'Should I disavow?')).text()
    assert all(phrase in disavow for phrase in ('both need to apply', 'considerable number',
               'caused, or are likely to cause, a manual action', 'incorrect use can harm', READ)), 'disavow conditions missing'
    quotes = re.findall(r'<q>(.*?)</q>', section(raw, 'Should I disavow?'), re.S)
    assert len(quotes) == 1, 'disavow quotation changed'
    assert Visible(quotes[0]).text() == (
        'In most cases, Google can assess which links to trust without additional '
        'guidance, so most sites will not need to use this tool.'), 'Google quote changed'
    for source in (LINKS, DISAVOW, SPAM):
        assert f'href="{source}"' in body, 'Google source missing'
    for heading in ('The three questions, and which tool answers which',
                    'What Ahrefs actually offers here', 'What an open link graph can tell you',
                    'What Check Engine does and does not do here'):
        assert f'<h2>{heading}</h2>' in body, 'retained section missing'
    assert 'Check Engine does not audit backlinks.' in text, 'product limit missing'
    assert 'no disavow workflow' in text, 'disavow workflow invented'
    rival = Visible(section(raw, 'What Ahrefs actually offers here')).text()
    # Only the base page's named tools, free/paid split and page-level detail.
    assert rival == (
        "Ahrefs's tools are Backlink Checker and Site Explorer. Backlink Checker has a free "
        'tier for the page-level view, including linking URLs and anchor text. Site Explorer '
        'is the paid view of the backlink profile with metrics and filtering. We found no '
        'product called "Backlink Audit" across Ahrefs\'s pricing, Site Audit, Backlink Checker '
        f'and Site Explorer pages when checked {OLDER_READ}. These are the older product '
        'readings, not a fresh check.'), 'unapproved rival claim'
    assert not re.search(r'Semrush|biggest|best backlink|\bDR\b', text), 'unapproved rival claim'
    editorial = Visible(without_price_helpers(body)).text()
    assert not re.search(r'Black Friday|November price|\d+% off|[$£€]\d', editorial, re.I), 'sale copy outside helpers'
    assert not re.search(r'[\u2013\u2014]|\([^)]*\)', editorial), 'dash or parenthesis in copy'
    assert not re.search(r'\b(?:Codex|gate|job|manifest|Article Studio)\b', editorial), 'internal copy'
    assert not re.search(r'\b\d{4}-\d{2}-\d{2}\b|\b\d{2}:\d{2}|\bUTC\b', text), 'machine date or time'
    assert not re.search(r'Check Engine(?: SEO)?\s+\d', editorial), 'product number typed'
    faqs = schemas(raw, 'FAQPage')
    assert len(faqs) == 1 and 4 <= len(faqs[0]['mainEntity']) <= 6, 'FAQ count'
    qa = faqs[0]['mainEntity']
    visible = re.findall(r'<div class="faq-item"><h3>(.*?)</h3><p>(.*?)</p></div>', raw, re.S)
    expected = [(Visible(q['name']).text(), Visible(q['acceptedAnswer']['text']).text()) for q in qa]
    assert [(Visible(q).text(), Visible(a).text()) for q, a in visible] == expected, 'FAQ schema differs'
    return answer, [q['name'] for q in qa], rows


def rejected(raw, original, replacement, reason):
    head, body = raw.split('<article>', 1)
    assert original in body, 'negative control did not land'
    try:
        check_page(head + '<article>' + body.replace(original, replacement, 1))
    except AssertionError as error:
        assert reason in str(error), f'control failed for wrong reason: {error}'
        print(f'CONTROL rejected: {reason}', flush=True)
    else:
        raise AssertionError(f'control accepted: {reason}')


def main():
    before = protected_state()
    facts = FACTS.read_text()
    assert all(source in facts for source in (LINKS, DISAVOW, SPAM)) and READ in facts
    tree = ast.parse((ROOT / GENERATOR).read_text())
    evidence = next(ast.literal_eval(n.value) for n in tree.body if isinstance(n, ast.Assign)
                    and any(isinstance(t, ast.Name) and t.id == 'EVIDENCE' for t in n.targets))
    assert evidence == {'read': READ, 'modified': '2026-11-20', 'published': '2026-09-14',
                        'ahrefs_read': OLDER_READ, 'table_rows': 1000, 'own_sites': 'four', 'own_found': 'None'}
    body = next(n.value for n in ast.walk(tree) if isinstance(n, ast.Assign)
                and any(isinstance(t, ast.Name) and t.id == 'body' for t in n.targets))
    assert isinstance(body, ast.JoinedStr), 'body must derive figures'
    literal = ''.join(p.value for p in body.values if isinstance(p, ast.Constant))
    assert not re.search(r'\d', re.sub(r'<[^>]+>', ' ', literal)), 'typed figure in body'
    with tempfile.TemporaryDirectory(prefix='test-backlink-audit-1120-') as temporary:
        destination = Path(temporary)
        scratch_copy(destination)
        env = environment(destination)
        git_dir = run(ROOT, ['git', 'rev-parse', '--absolute-git-dir'], env, quiet=True).strip()
        (destination / '.git').write_text(f'gitdir: {git_dir}\n')
        generator = destination / GENERATOR
        current = generator.read_bytes()
        original = run(ROOT, ['git', 'show', BASE + ':' + GENERATOR], env, quiet=True)
        assert all(claim in original for claim in ('Backlink Checker', 'Site Explorer',
                   'free tier', 'paid, full version', 'anchor text', '2026-10-19')), 'rival claim not in base'
        generator.write_text(original)
        run(destination, [sys.executable, '-B', 'scripts/build.py'], env)
        site = destination / 'site'
        old = {p.relative_to(site).as_posix(): p.read_text() for p in site.rglob('*.html')}
        assets = {p.relative_to(site).as_posix(): p.read_bytes() for p in site.rglob('*')
                  if p.is_file() and p.suffix != '.html' and p.name not in {'sitemap.xml', 'llms.txt'}}
        old_sitemap = (site / 'sitemap.xml').read_text()
        old_llms = (site / 'llms.txt').read_text()
        generator.write_bytes(current)
        run(destination, [sys.executable, '-B', 'scripts/build.py'], env)
        new = {p.relative_to(site).as_posix(): p.read_text() for p in site.rglob('*.html')}
        assert old.keys() == new.keys(), 'page inventory changed'
        old_title = unescape(re.search(r'<title>(.*?)</title>', old[PAGE]).group(1))
        new_title = unescape(re.search(r'<title>(.*?)</title>', new[PAGE]).group(1))
        for name in old:
            if name == PAGE:
                continue
            expected = old[name]
            if name == 'how-to/index.html':
                expected = expected.replace(old_title, new_title)
            assert unstamp(new[name]) == unstamp(expected), f'unrelated page changed: {name}'
        for name, data in assets.items():
            assert (site / name).read_bytes() == data, f'unrelated asset changed: {name}'
        old_map, new_map = ET.fromstring(old_sitemap), ET.parse(site / 'sitemap.xml').getroot()
        ns = {'s': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
        for item in old_map.findall('s:url', ns):
            if item.find('s:loc', ns).text == 'https://checkengineseo.com' + URL:
                item.find('s:lastmod', ns).text = '2026-11-20'
        assert ET.tostring(old_map) == ET.tostring(new_map), 'unrelated sitemap change'
        # The unedited builder derives this inventory line from title and description.
        old_line = next(line for line in old_llms.splitlines() if URL in line)
        new_llms = (site / 'llms.txt').read_text()
        new_line = next(line for line in new_llms.splitlines() if URL in line)
        assert old_llms.replace(old_line, new_line, 1) == new_llms, 'unrelated llms inventory change'
        assert old_title in old_line and new_title in new_line, 'inventory title differs'
        raw = new[PAGE]
        assert internal_links(old[PAGE]) <= internal_links(raw), 'base internal link removed'
        answer, questions, rows = check_page(raw)
        all_questions = {}
        for name, page in new.items():
            for faq in schemas(page, 'FAQPage'):
                for question in faq['mainEntity']:
                    all_questions.setdefault(question['name'].casefold(), []).append(name)
        for question in questions:
            assert all_questions[question.casefold()] == [PAGE], 'FAQ reused elsewhere'
        current_shingles = shingles(prose(raw))
        pairs = sorted(((similarity(current_shingles, shingles(prose(page))), name)
                        for name, page in new.items() if name != PAGE), reverse=True)
        assert pairs[0][0] < 0.5, f'page similarity too high: {pairs[0]}'
        import brand
        from render import buy_strip, nofollow_hub_links
        strip = re.search(r'<aside class="buy-strip">.*?</aside>', raw, re.S)
        expected_strip = nofollow_hub_links(brand.html(buy_strip('how-to-backlink-audit')))
        assert strip and strip.group() == expected_strip, 'sale line differs from helper'
        rejected(raw, '<ol>', '<ul>', 'step placement')
        rejected(raw, 'None was found', 'All were found', 'own run missing or overstated')
        rejected(raw, 'incorrect use can harm', 'incorrect use cannot harm', 'disavow conditions missing')
        rejected(raw, 'These are the older product readings', 'Ahrefs is the best. These are the older product readings', 'unapproved rival claim')
        rejected(raw, 'Check Engine does not audit backlinks.', 'Check Engine audits backlinks.', 'product limit missing')
        rejected(raw, 'Export the sample and review', 'Export every backlink and review', 'FAQ schema differs')
        print(f'PAGE {URL} | old title: {old_title} | new title: {new_title} | '
              f'words {len(prose(old[PAGE]).split())} -> {len(prose(raw).split())} | '
              f'max Jaccard {pairs[0][0]:.4f} with {pairs[0][1]}', flush=True)
        print('ANSWER ' + answer, flush=True)
        for row in rows:
            print('TABLE ' + Visible(row).text(), flush=True)
        print(f'PRESERVED {len(old) - 1} other pages, all base internal links and protected assets; '
              'only derived hub title, sitemap lastmod and llms inventory line follow this page', flush=True)
        run(destination, [sys.executable, '-B', 'scripts/verify_structured_data_matches_page.py'], env)
    assert protected_state() == before, 'protected source files changed'
    print('BACKLINK AUDIT UPGRADE 1120 ok: steps, table, dated sources, own run, rival limits, '
          'FAQ, links, similarity, controls and unchanged other pages; protected source tree unchanged')


if __name__ == '__main__':
    main()
