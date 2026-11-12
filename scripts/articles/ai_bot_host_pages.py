#!/usr/bin/env python3
"""Host AI crawler guides built only from the saved first-party documents."""
from __future__ import annotations

import json
import re
import sys
from html import escape
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import render as site_render

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / 'data' / 'ai-bot-host-2026-11-12'
BOTS = ('GPTBot', 'ClaudeBot', 'PerplexityBot', 'Google-Extended',
        'Applebot-Extended', 'CCBot')


def load_data() -> dict:
    return json.loads((DATA / 'pages.json').read_text(encoding='utf-8'))


def load_sample() -> dict:
    return json.loads((DATA / 'robots-sample-2026-11-12.json').read_text(encoding='utf-8'))


def bot_list(bots: list[str]) -> str:
    return ', '.join(bots[:-1]) + ' and ' + bots[-1] if len(bots) > 1 else bots[0]


def measurements(host: str, sample: dict) -> str:
    record = sample['hosts'][host]
    paragraphs = []
    if not record['sites_confirmed']:
        paragraphs.append('We did not measure any customer site on this host.')
    else:
        sites = record['sites']
        date = sample['read_date']
        count = record['sites_read']
        if not count:
            paragraphs.append(
                f'On the {record["sites_confirmed"]} site checked on {date} there was no '
                f'robots.txt (it answered {sites[0]["robots_status"]}), so no rules apply '
                'to any of the six bots.')
        elif any(bot['group'] == 'named' for site in sites for bot in site['bots'].values()):
            named = [bot for bot in BOTS if sites[0]['bots'][bot]['group'] == 'named']
            wildcard = [bot for bot in BOTS if sites[0]['bots'][bot]['group'] == '*']
            paragraphs.append(
                f'On the {count} site read on {date}, {bot_list(named)} are named in the '
                'file, but its rules are path rules and none blocks the home page. '
                f'{bot_list(wildcard)} is not named and falls under the * group.')
        else:
            no_group = sum(all(bot['group'] == 'none' for bot in site['bots'].values())
                           for site in sites)
            if no_group:
                words = {1: 'one', 2: 'two', 3: 'three'}
                groups = (f'{words[no_group]} site\'s file had no group for any of the six '
                          f'bots, the other {words[count - no_group]} used the * group')
            else:
                groups = 'every site used the * group'
            allowed = all(bot['home_allowed'] for site in sites for bot in site['bots'].values())
            home_rule = 'allowed' if allowed else 'not allowed'
            paragraphs.append(f'On the {count} sites read on {date}, {groups} '
                              f'and the home page was {home_rule} for all six bots.')
        if host == 'vercel':
            paragraphs.append("Two of the three sites may be Vercel's own products, "
                              'so read the rows before generalising.')
        paragraphs.extend([sample['scope'], 'Source: ' + sample['source'] + '.'])
    return ('<section aria-label="What we measured"><h2>What we measured</h2>'
            + ''.join('<p>' + escape(value) + '</p>' for value in paragraphs) + '</section>')


def source_link(key: str, sources: dict, *, dated: bool = False) -> str:
    source = sources[key]
    read_at = f' data-read-at="{source["read_at"]}"' if dated else ''
    return (f'<a href="{escape(source["url"], quote=True)}" '
            f'data-source="{source["file"]}"{read_at}>'
            f'{escape(source["label"])}</a>')


def attributed(text: str, keys: list[str], sources: dict, seen: set[str]) -> str:
    """Introduce each source once within a section, keeping claim text intact."""
    links = [source_link(key, sources) for key in dict.fromkeys(keys) if key not in seen]
    seen.update(keys)
    if not links:
        return escape(text)
    citations = ', '.join(links[:-1]) + ' and ' + links[-1] if len(links) > 1 else links[0]
    return citations + (' say: ' if len(links) > 1 else ' says: ') + escape(text)


def paragraph(item: dict, sources: dict, seen: set[str], *, lede: bool = False) -> str:
    style = ' class="lede"' if lede else ''
    content = attributed(item['text'], item['sources'], sources, seen)
    if item.get('repo_robots'):
        facts = json.loads((ROOT / 'data' / 'robots-txt-facts-2026-11-09.json').read_text())
        content += (f' <a href="{facts["sources"]["google_intro"]}" '
                    'data-repo-source="robots-txt-facts-2026-11-09.json" '
                    f'data-read-at="{facts["read"]}">Google robots.txt introduction. '
                    'Read 9 November 2026</a>')
    return f'<p{style}>' + content + '</p>'


def next_step(host: str) -> str:
    src = 'host-' + host
    return ('<section aria-label="Next step"><h2>Check your site</h2>'
            f'<p>Start with the <a href="/tools/ai-crawler-checker/?src={src}">'
            'free AI crawler checker</a> to read the rules for your address. '
            f'Then <a href="{escape(site_render.download_url(src), quote=True)}">'
            'download Check Engine</a> for an audit on your computer.</p></section>')


def check_commands() -> str:
    """Examples are displayed text. The build never sends these requests."""
    lines = ["curl -sS -L https://example.com/robots.txt",
             "curl -sS -L -D - -o /dev/null -A 'Mozilla/5.0' https://example.com/"]
    lines += [f"curl -sS -L -D - -o /dev/null -A '{bot}' https://example.com/"
              for bot in BOTS]
    return '<pre><code>' + escape('\n'.join(lines)) + '</code></pre>'


def bot_url(bot: str, crawlers: dict) -> str:
    row = crawlers[bot]
    return row['existing_page'] or '/ai-crawlers/' + row['slug'] + '/'


def host_table(page: dict, sources: dict, crawlers: dict) -> str:
    groups = {}
    for bot in BOTS:
        item = page['bots'][bot]
        groups.setdefault((item['default'], item['change']), []).append(bot)
    heading = '<h2>Rules for each bot</h2>'
    if len(groups) == 1:
        links = ', '.join(f'<a href="{bot_url(bot, crawlers)}">{bot}</a>' for bot in BOTS)
        return (heading + '<p>' + links + '</p>'
                + paragraph(page['bot_note'], sources, set()))
    rows = []
    keys = []
    for (default, change), bots in groups.items():
        for bot in bots:
            keys.extend(page['bots'][bot]['sources'])
        links = ', '.join(f'<a href="{bot_url(bot, crawlers)}">{bot}</a>' for bot in bots)
        rows.append('<tr><th scope="row">'
                    + links + '</th><td>' + escape(default)
                    + '</td><td>' + escape(change) + '</td></tr>')
    return (heading + '<div class="wrap-tbl"><table class="cmp">'
            '<thead><tr><th scope="col">Bot</th><th scope="col">Default on '
            + escape(page['name']) + '</th><th scope="col">How to change it</th>'
            '</tr></thead><tbody>' + ''.join(rows) + '</tbody></table></div>'
            + ''.join('<p>Source: ' + source_link(key, sources)
                      + ', read 12 November 2026.</p>' for key in dict.fromkeys(keys)))


def page_source_keys(page: dict) -> list[str]:
    items = (page['intro']
             + list(page.get('bots', {}).values())
             + ([page['bot_note']] if 'bot_note' in page else [])
             + [item for section in page['sections'] for item in section['paragraphs']]
             + page['faq'])
    return list(dict.fromkeys(key for item in items for key in item['sources']))


def sources_list(page: dict, sources: dict) -> str:
    return ('<section aria-label="Sources"><h2>Sources</h2><ul>'
            + ''.join('<li>' + source_link(key, sources, dated=True)
                      + ', read 12 November 2026 at ' + sources[key]['read_at'][11:16]
                      + ' UTC</li>' for key in page_source_keys(page))
            + '</ul></section>')


def page_url(page: dict) -> str:
    return '/ai-crawlers/hosts/' + (page['slug'] + '/' if page['slug'] else '')


def build_page(page: dict, data: dict) -> Path:
    sources = data['sources']
    crawlers = {row['token']: row for row in json.loads(
        (ROOT / 'data' / 'ai-crawler-pages-2026-10.json').read_text())['rows']}
    seen = set()
    body = ''.join(paragraph(item, sources, seen, lede=i == 0)
                   for i, item in enumerate(page['intro']))
    if page['kind'] == 'host':
        body += host_table(page, sources, crawlers)
        body += measurements(page['host'], load_sample())
    for section in page['sections']:
        seen = set()
        body += '<h2>' + escape(section['heading']) + '</h2>'
        body += ''.join(paragraph(item, sources, seen) for item in section['paragraphs'])
        if section.get('checks'):
            body += check_commands()
        if section.get('code'):
            body += '<pre><code>' + escape(section['code']) + '</code></pre>'
        for link in section.get('links', []):
            body += f'<p><a href="{escape(link[0], quote=True)}">{escape(link[1])}</a></p>'
    if page['kind'] == 'host':
        children = [item for item in data['pages']
                    if item['kind'] == 'bot' and item['host'] == page['host']]
        if children:
            body += '<h2>More help for this host</h2><ul>' + ''.join(
                f'<li><a href="{page_url(child)}">{escape(child["h1"])}</a></li>'
                for child in children) + '</ul>'
    faq = [(item['question'], escape(item['answer']))
           for item in page['faq']]
    path = site_render.render(
        cat='ai-crawlers/hosts', slug=page['slug'], title=page['title'],
        desc=page['description'], h1=page['h1'],
        crumb='<a href="/ai-crawlers/">AI crawlers</a> / '
              '<a href="/ai-crawlers/hosts/">Hosts</a>'
              + (' / ' + escape(page['name']) if page['slug'] else ''),
        body=body, faq=faq, closer=next_step(page['host']) + sources_list(page, sources),
        published="2026-11-12")
    # These guides omit the shared company-site link under the job's link rule.
    # The requested tracked app download remains the existing helper's URL.
    raw = path.read_text(encoding='utf-8')
    raw = re.sub(r'<a href="https://kerrandcompanyholdings.com/">(.*?)</a>',
                 r'\1', raw)
    path.write_text(raw, encoding='utf-8')
    return path


def build_all() -> list[Path]:
    data = load_data()
    return [build_page(page, data) for page in data['pages']]


if __name__ == '__main__':
    for output in build_all():
        print(output)
