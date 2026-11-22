#!/usr/bin/env python3
"""Offline checks for the five comparisons, supplied facts and protected output."""
from __future__ import annotations

import ast
import hashlib
from html import unescape
from pathlib import Path
import re
import sys
import tempfile

import app_path
from test_measured_answers import ANSWER, NUMBER, Visible
from test_real_questions_1120 import article_html, prose, schemas, shingles, similarity, without_price_helpers
from test_thank_you_review_ask import environment, protected_state, run, scratch_copy, unstamped

ROOT = Path(__file__).resolve().parent.parent
BASE = 'd68c45e9634df3bd71f6e688d4fbcada2a68ef9f'
READ = '20 November 2026'
OWNERSHIP = ('We make Check Engine, one of the tools listed here. We describe every tool '
             'from its own pages, read on 20 November 2026, and we earn money when you buy Check Engine.')
BANNED = re.compile(r'\b(?:independent|unbiased|neutral|honest|best|top|our pick|winner)\b|#1', re.I)
PAGES = {
    'best/index.html': ('SEO tools compared, by the job you are doing', {'500'},
                        ('https://www.screamingfrog.co.uk/seo-spider/',)),
    'best/free-seo-audit-plugins-wordpress/index.html': ('WordPress SEO audit plugins compared', {'1'},
                        ('https://plugin.squirrly.co/wordpress-seo-pricing/',)),
    'best/free-seo-audit-tools/index.html': ('Free SEO audit: tools and limits', {'4', '9', '500', '5,000', '1', '10'},
                        ('/vs/screaming-frog-alternative/', 'https://www.screamingfrog.co.uk/seo-spider/',
                         'https://ahrefs.com/webmaster-tools', 'https://www.semrush.com/prices/')),
    'best/screaming-frog-alternatives/index.html': ('Screaming Frog alternatives for Mac and Windows (2026)', {'500'},
                        ('https://www.screamingfrog.co.uk/seo-spider/',)),
    'best/white-label-seo-audit-tools/index.html': ('White-label SEO audit tools compared', {'599.00'},
                        ('https://www.link-assistant.com/pricing.html',)),
}
GENERATORS = ('scripts/articles/best_free.py', 'scripts/articles/best_free_seo_audit_plugins.py',
              'scripts/articles/sf_alternatives.py', 'scripts/articles/white_label.py',
              'scripts/articles/comparisons.py')
LISTS = {
    'best/free-seo-audit-plugins-wordpress/index.html': (
        'Bing Webmaster Tools Site Scan', 'SEOKEY', 'SEOPress', 'Slim SEO', 'The SEO Framework',
        'All in One SEO', 'Rank Math', 'Yoast SEO', 'Squirrly SEO', 'Google Lighthouse'),
    'best/screaming-frog-alternatives/index.html': (
        'Netpeak Spider', 'Screaming Frog SEO Spider', 'SEO PowerSuite WebSite Auditor', 'SEOmator',
        'Ahrefs Site Audit', 'Semrush Site Audit', 'Sitebulb', 'Raven Tools', 'SE Ranking',
        'Conductor Monitoring', 'JetOctopus', 'Lumar', 'Oncrawl'),
    'best/white-label-seo-audit-tools/index.html': (
        'SEOPress PRO', 'Netpeak Spider Pro', 'AgencyAnalytics', 'Semrush My Reports Pro', 'Sitebulb Pro',
        'Raven Tools', 'SEO Site Checkup Webmaster', 'SEO PowerSuite Enterprise',
        'SE Ranking with Agency Pack', 'SEOmator Scale', 'Sitechecker Premium'),
}
# Money per vendor, pinned to FACTS.md, not to the article's own data structure.
# Derived year comparisons are checked separately as twelve monthly payments.
VENDOR_PRICES = {
    'Yoast SEO': {'$118.80'}, 'Rank Math': {'$8.99'}, 'All in One SEO': {'$99.00'},
    'SEOPress': {'$49.00'}, 'SEOPress PRO': {'$49.00'}, 'Slim SEO': {'$59.00'},
    'The SEO Framework': {'$7.00'}, 'Squirrly SEO': {'$19.99'}, 'SEOKEY': {'$49.00'},
    'Bing Webmaster Tools Site Scan': set(), 'Google Lighthouse': set(),
    'Ahrefs Site Audit': {'$1,290', '$129.00'}, 'Netpeak Spider': {'$193.00', '$20.00'},
    'Netpeak Spider Pro': {'$193.00', '$20.00'}, 'Screaming Frog SEO Spider': {'$279'},
    'SEO PowerSuite WebSite Auditor': {'$349.00'}, 'SEOmator': {'$490.00', '$49.00'},
    'Semrush Site Audit': {'$117.33', '$139.00'}, 'Sitebulb': {'$180', '$18.00', '$425', '$42.00', '$1,500'},
    'Raven Tools': {'$468', '$49.00'}, 'SE Ranking': {'$103.20', '$129.00'},
    'Conductor Monitoring': set(), 'JetOctopus': set(), 'Lumar': set(), 'Oncrawl': set(),
    'AgencyAnalytics': {'$20.00'}, 'Semrush My Reports Pro': {'$20.00', '$10.00'},
    'Sitebulb Pro': {'$425', '$42.00'}, 'SEO Site Checkup Webmaster': {'$49.00', '$69.00'},
    'SEO PowerSuite Enterprise': {'$599.00'}, 'SE Ranking with Agency Pack': {'$103.20', '$69.00'},
    'Sitechecker Premium': {'$449.00'}, 'SEOmator Scale': {'$2,490.00', '$249.00'},
}
DERIVED = {'Rank Math': 8.99 * 12, 'The SEO Framework': 7 * 12, 'Squirrly SEO': 19.99 * 12,
           'Semrush Site Audit': 117.33 * 12, 'SE Ranking': 103.20 * 12,
           'AgencyAnalytics': 20 * 12, 'Semrush My Reports Pro': 20 * 12,
           'SEO Site Checkup Webmaster': 49 * 12, 'SE Ranking with Agency Pack': (103.20 + 69) * 12,
           'Sitechecker Premium': 449 * 12}
ROW_PRICES = {**VENDOR_PRICES, 'Sitebulb': {'$180', '$18.00'},
              'Semrush My Reports Pro': {'$20.00'}}
MONEY = re.compile(r'[$£€]\d[\d,]*(?:\.\d+)?')
# Pinned output, except the global build stamp. Older gates use these
# hashes only for this dated five-page rewrite and still replay old controls.
REFRESH_HASHES = {'best/index.html': '25a180a30e97b708c58b1181ff0ef8f83f5dcf2fdf5f103bc9452db8d99bd201',
 'best/free-seo-audit-plugins-wordpress/index.html': '994c4d22f0f374704ae7b8a438e486ad524c3623ef5be15c399f38ab31ac90c0',
 'best/free-seo-audit-tools/index.html': '6c10e9cbb0a76f5d79c50d86d46b0ec31f0d9ca1d6a36ae385bd7a96a21769f7',
 'best/screaming-frog-alternatives/index.html': '7ff6dfffc4e063395d1d73996a8e0873e6b9a67399b30394f556761166402bec',
 'best/white-label-seo-audit-tools/index.html': '342851746c4d56327f659d54410096a8bf91656341bdf79d80179eba2d5f1069'}


def check_page(name, raw):
    title, figures, sources = PAGES[name]
    actual = unescape(re.search(r'<title>(.*?)</title>', raw, re.S)[1])
    assert actual == title and len(actual) <= 60, 'title or title length'
    body = article_html(raw)
    text = prose(raw)
    assert not BANNED.search(text), 'ranking word in article'
    assert not BANNED.search(actual), 'ranking word in title'
    assert not re.search(r'[\u2013\u2014()]', text), 'plain punctuation required'
    assert not re.search(r'\b\d{4}-\d{2}-\d{2}\b|\b(?:Codex|manifest|Article Studio)\b|\b\S+\.(?:json|py)\b', text), 'internal copy'
    answers = list(ANSWER.finditer(raw))
    assert len(answers) == 1, 'expected one answer'
    answer = answers[0]
    h1 = re.search(r'<h1\b[^>]*>.*?</h1>', raw, re.S)
    h2 = re.search(r'<h2\b', raw)
    assert h1 and h2 and h1.end() < answer.start() < answer.end() < h2.start(), 'answer placement'
    before = re.sub(r'<p class="byline">.*?</p>', '', raw[h1.end():answer.start()], flags=re.S)
    assert Visible(before).text() == OWNERSHIP, 'ownership before answer'
    first = Visible(answer[1]).text()
    assert 2 <= len(re.split(r'(?<=[.!?])\s+', first)) <= 4, 'answer sentence count'
    assert set(NUMBER.findall(first)) == figures, 'unsourced answer figure'
    if 'plugins-wordpress' in name:
        assert '1 audit suite page a month' in first, 'missing sourced plugin allowance'
    for url in sources:
        assert f'href="{url}"' in answer[0], 'answer source missing'
    method = re.search(r'<h2>How this comparison works</h2>(.*?)(?=<h2>)', raw, re.S)
    assert method, 'method missing'
    for wording in ('price for a year', 'free version and its limit', 'desktop, cloud or a plugin',
                    'vendor\'s own pages', READ, 'free first', 'lowest price for a year',
                    'ties alphabetical', 'comparison of stated facts, not a test score'):
        assert wording in Visible(method[1]).text(), 'method criterion missing: ' + wording
    assert 'Updated <time datetime="2026-11-20">20 November 2026</time>' in raw
    assert re.search(r'"dateModified":\s*"2026-11-20"', raw)
    editorial = Visible(without_price_helpers(body)).text()
    assert not re.search(r'percent off|November price', editorial, re.I), 'sale comparison wording'
    monthly = re.findall(r'(\$\d[\d,]*(?:\.\d+)?) a month', editorial)
    assert all(re.fullmatch(r'\$\d[\d,]*\.\d{2}', p) for p in monthly), 'monthly cents missing'
    # Each h2 rival block has its own named dated source note, including the
    # first answer and the table. FAQ source dates follow the existing shape.
    for block in re.split(r'<h2\b[^>]*>.*?</h2>', body, flags=re.S):
        if 'rel="nofollow noopener"' in block:
            assert READ in Visible(block).text(), 'rival section date missing'
            if '<div class="faq-item">' not in block:
                assert 'own pages on ' + READ in block, 'rival section date missing'
    rival_sections = re.findall(r'<section data-rival="([^"]+)">(.*?)</section>', body, re.S)
    for company, block in rival_sections:
        notes = re.findall(r'<p class="verified-note">.*?</p>', block, re.S)
        assert len(notes) == 1, 'one note per rival section'
        note = Visible(notes[0]).text()
        owner = 'Ahrefs' if company == 'Ahrefs SEO plugin' else company
        assert owner in note and 'own pages on ' + READ in note, 'named rival note missing'
    rows = re.findall(r'<tr data-tool="([^"]+)">(.*?)</tr>', body, re.S)
    if name in LISTS:
        assert len(rows) >= 10, 'fewer than ten tools'
        assert tuple(unescape(tool) for tool, _ in rows) == LISTS[name], 'tool order or inventory'
        assert set(tool for tool, _ in rival_sections) == set(LISTS[name]) | (
            {'Ahrefs SEO plugin'} if 'plugins-wordpress' in name else set()), 'rival sections missing'
        for tool, row in rows:
            assert READ in row and 'rel="nofollow noopener"' in row, 'row lacks dated source'
            values = re.findall(r'<td>(.*?)</td>', row, re.S)
            assert len(values) == 5
            price = Visible(values[3]).text()
            assert 'Check Engine' not in tool, 'own product in rival table'
            direct = price.split('Year comparison:')[0]
            assert set(MONEY.findall(direct)) == ROW_PRICES[tool], 'price not in supplied facts: ' + tool
            year = re.search(r'Year comparison: (\$[\d,]+\.\d{2})', price)
            if year:
                expected = f'${DERIVED[tool]:,.2f}' if tool in DERIVED else None
                amount = float(year[1][1:].replace(',', ''))
                known = {float(p[1:].replace(',', '')) for p in VENDOR_PRICES[tool]}
                assert year[1] == expected if expected else amount in known or amount == 0, 'unsupported year cost'
            detail = next(block for company, block in rival_sections if company == tool)
            assert set(MONEY.findall(Visible(detail).text())) <= VENDOR_PRICES[tool], 'section price not in facts: ' + tool
        assert 'Black Friday price shown on 20 November 2026' in body if 'plugins-wordpress' in name else True
    if 'screaming-frog-alternatives' in name:
        assert '9 November 2026' in text and '4 pages' in text and '9 problems' in text
        assert 'billing-period match' in text and not MONEY.search(next(b for c, b in rival_sections if c == 'JetOctopus'))
    if 'white-label' in name:
        assert '11 November 2026' in text and '86 pages' in text and '19 issues' in text
        assert 'after launch, not live' in text
        assert 'logo upload not confirmed' in text
    faq = schemas(raw, 'FAQPage')
    assert len(faq) == 1 and 3 <= len(faq[0]['mainEntity']) <= 5, 'FAQ count'
    visible = re.findall(r'<div class="faq-item"><h3>(.*?)</h3><p>(.*?)</p></div>', raw, re.S)
    assert [(Visible(q).text(), Visible(a).text()) for q, a in visible] == [
        (Visible(q['name']).text(), Visible(q['acceptedAnswer']['text']).text()) for q in faq[0]['mainEntity']], 'FAQ schema differs'
    bodies = re.findall(r'<tbody>(.*?)</tbody>', body, re.S)
    return first, len(rows) if rows else sum(len(re.findall(r'<tr\b', b)) for b in bodies)


def reviewed_refresh(name, raw):
    assert hashlib.sha256(unstamped(raw).encode()).hexdigest() == REFRESH_HASHES[name], 'unreviewed comparison copy: ' + name
    return check_page(name, raw)


def legacy_page(destination, env, name, revision):
    """Render only one historical page, retaining the caller's current output."""
    generator = ('best_free_seo_audit_plugins.py' if 'plugins-wordpress' in name else
                 'sf_alternatives.py' if 'screaming-frog-alternatives' in name else
                 'white_label.py' if 'white-label' in name else 'best_free.py')
    entry = {'best_free_seo_audit_plugins.py': 'best_free_seo_audit_plugins.build()',
             'sf_alternatives.py': 'sf_alternatives.sf_alternatives()',
             'white_label.py': 'white_label.white_label_tools()',
             'best_free.py': 'best_free.best_hub()' if name == 'best/index.html' else 'best_free.free_seo_audit_tools()'}[generator]
    path = destination / 'scripts/articles' / generator
    page = destination / 'site' / name
    source, output = path.read_bytes(), page.read_bytes()
    registry = destination / 'scripts/articles/comparisons.py'
    registry_source = registry.read_bytes()
    try:
        if generator in {'sf_alternatives.py', 'white_label.py'}:
            registry.write_text(run(ROOT, ['git', 'show', revision + ':scripts/articles/comparisons.py'], env, quiet=True))
        path.write_text(run(ROOT, ['git', 'show', revision + ':scripts/articles/' + generator], env, quiet=True))
        run(destination, [sys.executable, '-B', '-c',
            "import sys; sys.path[:0] = ['scripts', 'scripts/articles']; import " + generator[:-3] + '; ' + entry], env)
        return page.read_text()
    finally:
        path.write_bytes(source)
        registry.write_bytes(registry_source)
        page.write_bytes(output)


def rejected(name, raw, reason):
    try:
        check_page(name, raw)
    except AssertionError as error:
        assert reason in str(error), f'wrong rejection: {error}'
        print('CONTROL rejected: ' + str(error), flush=True)
    else:
        raise AssertionError('control accepted: ' + reason)


def main():
    before = protected_state()
    with tempfile.TemporaryDirectory(prefix='test-best-compared-3-') as temporary:
        destination = Path(temporary)
        scratch_copy(destination)
        env = environment(destination)
        env['DOCKET_APP'] = str(app_path.find())
        git_dir = run(ROOT, ['git', 'rev-parse', '--absolute-git-dir'], env, quiet=True).strip()
        (destination / '.git').write_text(f'gitdir: {git_dir}\n')
        current = {name: (destination / name).read_bytes() for name in GENERATORS}
        for name in GENERATORS:
            (destination / name).write_text(run(ROOT, ['git', 'show', BASE + ':' + name], env, quiet=True))
        run(destination, [sys.executable, '-B', 'scripts/build.py'], env)
        site = destination / 'site'
        old = {p.relative_to(site).as_posix(): p.read_text() for p in site.rglob('*.html')}
        assets = {name: (site / name).read_bytes() for name in ('llms.txt', 'offer.json')}
        bundle = (destination / 'data/bundle.json').read_bytes()
        for name, content in current.items():
            (destination / name).write_bytes(content)
        run(destination, [sys.executable, '-B', 'scripts/build.py'], env)
        new = {p.relative_to(site).as_posix(): p.read_text() for p in site.rglob('*.html')}
        assert old.keys() == new.keys(), 'URL inventory changed'
        stamp_only = lambda text: re.sub(r'(<meta name="build-id" content=")[^"]+(">)', r'\1BUILD\2', text)
        for name, raw in new.items():
            if name not in PAGES:
                assert stamp_only(raw) == stamp_only(old[name]), 'unrelated page changed: ' + name
            assert schemas(raw, 'SoftwareApplication') == schemas(old[name], 'SoftwareApplication'), 'Offer changed: ' + name
        for name, content in assets.items():
            assert (site / name).read_bytes() == content, 'protected asset changed: ' + name
        assert (destination / 'data/bundle.json').read_bytes() == bundle
        all_shingles = {name: shingles(prose(raw)) for name, raw in new.items()}
        questions = {}
        for name, raw in new.items():
            for faq in schemas(raw, 'FAQPage'):
                for q in faq['mainEntity']:
                    questions.setdefault(q['name'].casefold(), []).append(name)
        for name in PAGES:
            raw = new[name]
            first, rows = check_page(name, raw)
            reviewed_refresh(name, raw)
            assert re.search(r'<p class="byline">.*?Published <time[^>]*>.*?</time>', old[name], re.S)[0].split('<span class="sep">·</span>Updated')[0] in raw, 'byline or publication changed'
            pairs = sorted(((similarity(all_shingles[name], value), other) for other, value in all_shingles.items() if other != name), reverse=True)
            assert pairs[0][0] < .5, 'site Jaccard too high'
            assert all(similarity(all_shingles[name], all_shingles[other]) < .40 for other in PAGES if other != name), 'batch Jaccard too high'
            for q in schemas(raw, 'FAQPage')[0]['mainEntity']:
                assert questions[q['name'].casefold()] == [name], 'FAQ reused on site'
            print(f'PAGE /{name.removesuffix("index.html")} | {PAGES[name][0]} | rows {rows} | {len(prose(raw).split())} words | max Jaccard {pairs[0][0]:.4f} with /{pairs[0][1].removesuffix("index.html")}', flush=True)
            print('ANSWER ' + first, flush=True)
            rejected(name, raw.replace(OWNERSHIP, 'We make a tool.', 1), 'ownership before answer')
            rejected(name, raw.replace('How this comparison works', 'About the list', 1), 'method missing')
            rejected(name, raw.replace('<h1', '<h1', 1).replace('</h1>', ' winner</h1>', 1), 'ranking word')
            rejected(name, raw.replace('own pages on ' + READ, 'own pages on 19 November 2026'), 'rival section date')
            match = ANSWER.search(raw)
            number = NUMBER.search(Visible(match[1]).text())[0]
            invented = match[0].replace(number, '987654.321', 1)
            rejected(name, raw.replace(match[0], invented, 1), 'unsourced answer figure')
            missing_source = match[0].replace(f'href="{PAGES[name][2][0]}"', 'href="https://example.invalid/"', 1)
            rejected(name, raw.replace(match[0], missing_source, 1), 'answer source missing')
            if name in LISTS:
                rows = list(re.finditer(r'<tr data-tool="[^"]+">.*?</tr>', raw, re.S))
                rejected(name, raw.replace(rows[0][0], '', 1),
                         'fewer than ten tools' if len(rows) == 10 else 'tool order or inventory')
                priced = next(row for row in rows if MONEY.search(row[0].split('Year comparison:')[0]))
                value = MONEY.search(priced[0])[0]
                rejected(name, raw.replace(priced[0], priced[0].replace(value, '$987654.32', 1), 1), 'price not in supplied facts')
                monthly = re.search(r'\$\d[\d,]*\.\d{2} a month', raw)
                assert monthly, 'monthly control missing'
                rejected(name, raw.replace(monthly[0], re.sub(r'\.\d{2}', '', monthly[0]), 1), 'monthly cents missing')

        sys.path.insert(0, str(ROOT / 'scripts/articles'))
        import comparisons
        assert sum(map(len, comparisons.VERIFIED.values())) >= 162, 'sourced claims dropped'
        verified_pages = {'sf-alternatives': 'best/screaming-frog-alternatives/index.html',
                          'wl-tools': 'best/white-label-seo-audit-tools/index.html',
                          'wordpress-compared': 'best/free-seo-audit-plugins-wordpress/index.html'}
        for key, names in {'sf-alternatives': LISTS['best/screaming-frog-alternatives/index.html'],
                           'wl-tools': LISTS['best/white-label-seo-audit-tools/index.html'],
                           'wordpress-compared': LISTS['best/free-seo-audit-plugins-wordpress/index.html']}.items():
            assert comparisons.CHECKED_ISO[key] == '2026-11-20'
            assert comparisons.CHECKED_HUMAN[key] == READ
            for claim, source in comparisons.VERIFIED[key]:
                assert claim and f'href="{source}"' in new[verified_pages[key]], 'registry source missing'
            assert set(names) <= {claim.split(':', 1)[0] for claim, _ in comparisons.VERIFIED[key]}
        old_source = run(ROOT, ['git', 'show', BASE + ':scripts/articles/comparisons.py'], env, quiet=True)
        current_source = (ROOT / 'scripts/articles/comparisons.py').read_text()
        def functions(source):
            return {n.name: ast.get_source_segment(source, n) for n in ast.parse(source).body if isinstance(n, ast.FunctionDef)}
        assert functions(old_source) == functions(current_source), 'shared comparison helper changed'
        run(destination, [sys.executable, '-B', 'scripts/verify_competitive_claims.py'], env)
    assert protected_state() == before, 'protected source tree changed'
    print('BEST COMPARED 3 ok: five comparisons, dated facts, ordering, controls, similarity and protected output')


if __name__ == '__main__':
    main()
