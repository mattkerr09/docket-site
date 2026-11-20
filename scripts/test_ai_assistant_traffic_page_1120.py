#!/usr/bin/env python3
"""Offline assistant-traffic checks, with base/current scratch builds."""
from __future__ import annotations

import ast
from html import unescape
from pathlib import Path
import re
import sys
import tempfile

from test_measured_answers import Visible
from test_real_questions_1120 import (
    article_html, check_answer, prose, schemas, shingles, similarity,
    without_price_helpers,
)
from test_thank_you_review_ask import environment, protected_state, run, scratch_copy

ROOT = Path(__file__).resolve().parent.parent
BASE = 'e9cfb2cb339e4ae79402685485cd2341ea9eaf98'
PAGE = 'how-to/see-ai-assistant-traffic-in-analytics/index.html'
URL = '/' + PAGE.removesuffix('index.html')
HUB = 'how-to/index.html'
FACTS = Path('/Users/matthewkerr/ops/research/articles/data-2026-11-20/ai-assistant-traffic/FACTS.md')
CHANNELS = 'https://support.google.com/analytics/answer/9756891?hl=en'
ACQUISITION = 'https://support.google.com/analytics/answer/12923437?hl=en'
REFERRALS = 'https://support.google.com/analytics/answer/10327750?hl=en'
OPENAI = 'https://developers.openai.com/api/docs/bots'
PERPLEXITY = 'https://docs.perplexity.ai/docs/resources/perplexity-crawlers'
SOURCES = (CHANNELS, ACQUISITION, REFERRALS, OPENAI, PERPLEXITY)
SPEC = {
    'words': ('chatgpt', 'perplexity', 'analytics'),
    'figures': set(), 'sources': (CHANNELS,),
}


def unstamp(raw):
    # Adding a page changes the global build id, but no other existing bytes
    # may change outside the how-to hub and the generated sitemap/inventory.
    return re.sub(r'(<meta name="build-id" content=")[^"]+(">)', r'\1BUILD\2', raw)


def check_page(raw):
    answer = check_answer(raw, SPEC)
    body = article_html(raw)
    text = prose(raw)
    assert 'By Matthew Kerr' in text
    assert 'Published <time datetime="2026-11-20">20 November 2026</time>' in raw
    assert '<h1>How to see ChatGPT and Perplexity visitors in Google Analytics</h1>' in raw
    for source in SOURCES:
        assert f'href="{source}"' in body, f'source missing: {source}'
    assert all(word in answer for word in (
        'AI Assistant', 'Gemini', 'Deepseek', 'Copilot', 'Grok',
        "exclude Google's AI Overviews and AI Mode", 'Reports', 'Acquisition',
        'Traffic acquisition', 'Session source', 'perplexity.ai', 'chatgpt.com',
        "Google's examples do not name Perplexity",
    )), 'first-screen answer incomplete'
    headings = re.findall(r'<h2>(.*?)</h2>', body, re.S)
    assert headings == [
        'Find the AI Assistant channel', 'Check the sources one by one',
        'Crawler visits are not visitors', 'If you see no AI traffic at all',
        'Choose the next check', 'Common questions',
    ], 'section order changed'
    for section in re.split(r'<h2\b[^>]*>.*?</h2>', body, flags=re.S):
        if 'rel="nofollow noopener"' in section and 'faq-item' not in section:
            assert section.count('<p class="verified-note">') == 1, 'expected one source note per section'
            note = section.split('<p class="verified-note">', 1)[1].split('</p>', 1)[0]
            assert 'read 20 November 2026' in note, 'missing dated source block'
            assert 'this product' not in note.lower(), 'source company not named'
            for source, company in ((CHANNELS, 'Google'), (ACQUISITION, 'Google'),
                                    (REFERRALS, 'Google'), (OPENAI, 'OpenAI'),
                                    (PERPLEXITY, 'Perplexity')):
                if f'href="{source}"' in section:
                    assert f'href="{source}"' in note and company in note, 'section source not named'
    for sentence in re.split(r'(?<=[.!?])\s+', text):
        assert not ('chatgpt' in sentence.lower() and re.search(r'\badds\b', sentence, re.I)
                    and 'utm_source=chatgpt.com' in sentence.lower()), 'unverified ChatGPT tagging claim'
        assert not re.search(
            r"\bPerplexity (?:is|is not|isn't|appears|does not appear) "
            r"(?:included |excluded )?(?:in|on|from) Google's (?:AI Assistant )?list"
            r"|Google's (?:AI Assistant )?list (?:includes|excludes|does not include) Perplexity",
            sentence, re.I), 'unverified Perplexity list membership'
    assert '<code>ai-assistant</code>' in body and '<code>(ai-assistant)</code>' in body
    assert all(f'<code>{medium}</code>' in body for medium in ('referral', 'app', 'link'))
    assert 'ignore_referrer=true' in body
    assert 'about 24 hours' in text, 'OpenAI adjustment interval missing'
    assert 'A check cannot make an assistant cite you.' in text, 'citation limit missing'
    assert 'Those settings are independent.' in text, 'search/training distinction missing'
    assert 'not run that tag does not create a tagged page visit' in text, 'tag/log distinction missing'
    for bot in ('PerplexityBot', 'Perplexity-User', 'OAI-SearchBot', 'GPTBot', 'ChatGPT-User'):
        assert f'<strong>{bot}</strong>' in body, f'bot role missing: {bot}'
    for link in ('/ai-crawlers/perplexitybot/', '/ai-crawlers/chatgpt-user/',
                 '/how-to/analytics-findings-name-the-tag/', '/tools/seo-checker/'):
        assert body.count(f'href="{link}"') == 1, f'expected one link: {link}'
    editorial = Visible(without_price_helpers(body)).text()
    assert not re.search(r'Black Friday|November price|\d+% off|[$£€]\d', editorial, re.I), \
        'sale copy outside shared helpers'
    # The parentheses in Google's literal campaign value are part of the rule.
    assert not re.search(r'[\u2013\u2014]|\([^)]*\)', editorial.replace('(ai-assistant)', '')), \
        'dash or parenthesis in authored copy'
    assert not re.search(r'\b(?:Codex|gate|job|manifest|Article Studio)\b', editorial), 'internal copy'
    assert not re.search(r'\b\d{4}-\d{2}-\d{2}\b|\b\d{2}:\d{2}|\bUTC\b', text), \
        'machine date or time in visible copy'
    faqs = schemas(raw, 'FAQPage')
    assert len(faqs) == 1 and 3 <= len(faqs[0]['mainEntity']) <= 5, 'FAQ count'
    qa = faqs[0]['mainEntity']
    visible = re.findall(r'<div class="faq-item"><h3>(.*?)</h3><p>(.*?)</p></div>', raw, re.S)
    expected = [(Visible(q['name']).text(), Visible(q['acceptedAnswer']['text']).text()) for q in qa]
    assert [(Visible(q).text(), Visible(a).text()) for q, a in visible] == expected, 'FAQ schema differs'
    for question in qa:
        assert 'read 20 November 2026' in question['acceptedAnswer']['text'], 'FAQ source date missing'
    return answer, [q['name'] for q in qa]


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
    assert all(source in facts for source in SOURCES), 'source differs from supplied facts'
    assert 'NOT VERIFIED' in facts and 'utm_source=chatgpt.com' in facts
    assert '20 November 2026' in facts and '~24 hours' in facts
    tree = ast.parse((ROOT / 'scripts/articles/howto_ai_assistant_traffic.py').read_text())
    body = next(node.value for node in ast.walk(tree) if isinstance(node, ast.Assign)
                and any(isinstance(target, ast.Name) and target.id == 'body' for target in node.targets))
    assert isinstance(body, ast.JoinedStr), 'article body must interpolate its figures'
    literal = ''.join(part.value for part in body.values if isinstance(part, ast.Constant))
    assert not re.search(r'\d', re.sub(r'<[^>]+>', ' ', literal)), 'typed figure in article body'
    with tempfile.TemporaryDirectory(prefix='test-ai-assistant-traffic-1120-') as temporary:
        destination = Path(temporary)
        scratch_copy(destination)
        env = environment(destination)
        git_dir = run(ROOT, ['git', 'rev-parse', '--absolute-git-dir'], env, quiet=True).strip()
        (destination / '.git').write_text(f'gitdir: {git_dir}\n')
        generator = destination / 'scripts/build.py'
        current = generator.read_bytes()
        generator.write_text(run(ROOT, ['git', 'show', BASE + ':scripts/build.py'], env, quiet=True))
        site = destination / 'site'
        (site / PAGE).unlink(missing_ok=True)
        run(destination, [sys.executable, '-B', 'scripts/build.py'], env)
        old = {p.relative_to(site).as_posix(): p.read_text() for p in site.rglob('*.html')}
        assets = {p.relative_to(site).as_posix(): p.read_bytes() for p in site.rglob('*')
                  if p.is_file() and p.suffix != '.html'
                  and p.name not in {'sitemap.xml', '_redirect-map.json'}}
        generator.write_bytes(current)
        run(destination, [sys.executable, '-B', 'scripts/build.py'], env)
        new = {p.relative_to(site).as_posix(): p.read_text() for p in site.rglob('*.html')}
        assert new.keys() - old.keys() == {PAGE}, 'unexpected page inventory'
        assert old.keys() <= new.keys(), 'old page removed'
        for name in old:
            if name != HUB:
                assert unstamp(new[name]) == unstamp(old[name]), f'unrelated page changed: {name}'
        for name, data in assets.items():
            assert (site / name).read_bytes() == data, f'unrelated asset changed: {name}'
        assert new[HUB].count(f'href="{URL}"') == 1, 'hub link missing or repeated'
        assert f'<loc>https://checkengineseo.com{URL}</loc>' in (site / 'sitemap.xml').read_text()
        for link in ('ai-crawlers/perplexitybot/index.html', 'ai-crawlers/chatgpt-user/index.html',
                     'how-to/analytics-findings-name-the-tag/index.html', 'tools/seo-checker/index.html'):
            assert link in new, f'linked page missing from build: {link}'
        raw = new[PAGE]
        answer, questions = check_page(raw)
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
        expected_strip = nofollow_hub_links(brand.html(buy_strip(('how-to-' + PAGE.split('/')[1])[:60])))
        assert strip and strip.group() == expected_strip, 'sale line differs from shared helper'
        rejected(raw, 'Sources read 20 November 2026', 'Sources read recently', 'missing dated source block')
        rejected(raw, 'Keep the checks separate:',
                 'ChatGPT adds utm_source=chatgpt.com to links. Keep the checks separate:',
                 'unverified ChatGPT tagging claim')
        rejected(raw, 'Keep the checks separate:',
                 "Perplexity is in Google's list. Keep the checks separate:",
                 'unverified Perplexity list membership')
        rejected(raw, 'Keep the checks separate:',
                 "Google's list excludes Perplexity. Keep the checks separate:",
                 'unverified Perplexity list membership')
        rejected(raw, 'A check cannot make an assistant cite you.',
                 'A check makes an assistant cite you.', 'citation limit missing')
        rejected(raw, 'Use the full app below',
                 'Black Friday sale is on. Use the full app below', 'sale copy outside shared helpers')
        rejected(raw, 'about 24 hours', 'about 987 hours', 'OpenAI adjustment interval missing')
        rejected(raw, 'No. Google\'s default channel guide excludes',
                 'Yes. Google\'s default channel guide excludes', 'FAQ schema differs')
        title = unescape(re.search(r'<title>(.*?)</title>', raw).group(1))
        print(f'PAGE {URL} | {title} | {len(prose(raw).split())} words | '
              f'max Jaccard {pairs[0][0]:.4f} with {pairs[0][1]}', flush=True)
        print('ANSWER ' + answer, flush=True)
        run(destination, [sys.executable, '-B', 'scripts/verify_structured_data_matches_page.py'], env)
        # Check Engine regenerates data/ after review. A saved link graph
        # cannot validate a page that has not yet been added to that graph.
    assert protected_state() == before, 'protected source files changed'
    print('AI ASSISTANT TRAFFIC 1120 ok: scratch builds, dated sources, bot roles, '
          'FAQ, similarity, controls and unchanged other pages; protected source tree unchanged')


if __name__ == '__main__':
    main()
