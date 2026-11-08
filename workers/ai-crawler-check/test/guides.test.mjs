import { test } from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { handle } from '../src/index.js'
import { DailyCap, TOOLS } from '../src/mcp.js'
import { GUIDE_LINKS, GUIDES, guidePath } from '../src/guides.js'

const TITLE = 'A helpful guide to garden plants'
const DESCRIPTION = 'Learn how to choose garden plants and care for them through every season with this simple guide.'
const DATA = { lang: 'en', titles: [TITLE], metas: { description: [DESCRIPTION], viewport: ['width=device-width'],
  'og:title': [TITLE], 'og:image': ['https://example.com/garden.png'], 'og:description': [DESCRIPTION], 'twitter:card': ['summary'] },
  canonicals: ['https://example.com/'], h1s: ['Garden plants'],
  jsonld: [JSON.stringify({ '@context': 'https://schema.org', '@type': 'Article', headline: TITLE })] }
const HEADERS = { 'Content-Type': 'text/html', 'Strict-Transport-Security': 'max-age=31536000',
  'X-Content-Type-Options': 'nosniff', 'Referrer-Policy': 'strict-origin-when-cross-origin' }
const ROUTES = { 'https://example.com/': { headers: HEADERS },
  'https://example.com/robots.txt': { body: 'User-agent: *\nAllow: /', headers: { 'Content-Type': 'text/plain' } } }
const COMMERCE = /\$|price|buy|download|upgrade|licen[cs]e|trial|discount|half price|black friday/i

function request(method, params, session) {
  return new Request('https://worker.example/mcp', { method: 'POST',
    headers: { 'Content-Type': 'application/json', ...(session ? { 'Mcp-Session-Id': session } : {}) },
    body: JSON.stringify({ jsonrpc: '2.0', id: 1, method, params }) })
}
function fetcher(routes) {
  return async (url) => {
    const route = routes[url]
    if (!route) throw new Error('unreachable')
    return new Response(route.body || '', { status: route.status || 200, headers: route.headers || { 'Content-Type': 'text/html' } })
  }
}
function counter() {
  const store = new Map()
  const cap = new DailyCap({ storage: { get: async (k) => store.get(k), put: async (k, v) => store.set(k, v) } })
  return { store, DAILY_CAP: { idFromName: () => 'global', get: () => ({ fetch: (url) => cap.fetch(new Request(url)) }) } }
}
async function run(name, { family = 'claude', args = {}, data = DATA, routes = ROUTES, env = {} } = {}) {
  // Exercise the actual initialization prefix rather than inventing a session in the main scenarios.
  const init = await handle(request('initialize', { clientInfo: { name: family } }), fetcher(routes), env)
  const response = await handle(request('tools/call', { name, arguments: { url: 'example.com', title: TITLE, description: DESCRIPTION, ...args } },
    init.headers.get('Mcp-Session-Id')), fetcher(routes), { extract: async () => data, ...env })
  const { result } = await response.json()
  assert.equal(result.isError, false, name)
  assert.doesNotMatch(result.content[0].text, COMMERCE, name)
  assert.doesNotMatch(JSON.stringify(result.structuredContent), COMMERCE, name)
  return result
}
function linked(result) {
  const findings = result.structuredContent.crawlers || result.structuredContent.findings || []
  return findings.filter((f) => f.guide_url)
}
function assertNoGuide(result) {
  assert.doesNotMatch(JSON.stringify(result), /docketseo\.app|guide_url|How to fix it, step by step:/)
}
function assertGuide(result, path, previousLine) {
  const text = result.content[0].text
  const lines = text.split('\n')
  const guides = lines.filter((line) => line.startsWith('How to fix it, step by step: '))
  assert.equal(guides.length, 1)
  assert.equal((text.match(/https:\/\/docketseo\.app/g) || []).length, 1)
  const expected = `https://docketseo.app${path}?utm_source=claude-connector`
  assert.equal(guides[0], `How to fix it, step by step: ${expected}`)
  const url = new URL(expected)
  assert.equal(url.origin, 'https://docketseo.app')
  assert.match(url.pathname, /^\/(how-to|learn)\/[a-z0-9-]+\/$/)
  assert.equal(url.search, '?utm_source=claude-connector')
  assert.match(lines[lines.indexOf(guides[0]) - 1], previousLine)
  assert.equal(linked(result).length, 1, 'only one structured finding gets a guide')
  assert.equal(linked(result)[0].guide_url, expected)
}

const SCENARIOS = [
  { name: 'check_page_seo', path: '/how-to/write-title-tags-that-fit/', previous: /^Fix first .*No title tag/,
    options: { data: { ...DATA, titles: [] } } },
  { name: 'check_ai_crawlers', path: '/how-to/fix-ai-crawler-access/', previous: /^- Amazonbot .*blocked/,
    options: { routes: { ...ROUTES, 'https://example.com/robots.txt': { body: 'User-agent: *\nDisallow: /' } } } },
  { name: 'trace_redirects', path: '/how-to/fix-redirect-problems/', previous: /^Problem: Redirect loop/,
    options: { routes: { 'https://example.com/': { status: 301, headers: { Location: '/' } } } } },
  { name: 'check_http_headers', path: '/how-to/fix-missing-security-headers/', previous: /^Worth fixing: No HSTS header/,
    options: { routes: { 'https://example.com/': {} } } },
  { name: 'preview_search_snippet', path: '/how-to/write-title-tags-that-fit/', previous: /^Title: .*too long/,
    options: { args: { title: 'Garden plants '.repeat(10), description: 'Garden care '.repeat(20) } } },
  { name: 'preview_search_snippet', path: '/how-to/write-meta-descriptions/', previous: /^Description: .*too long/,
    options: { args: { description: 'Garden care '.repeat(20) } } },
]

test('only Claude gets one relevant guide under the first fix, with a matching structured URL and family tally', async () => {
  assert.equal(GUIDE_LINKS, true)
  for (const scenario of SCENARIOS) {
    for (const family of ['claude', 'chatgpt', 'other']) {
      const { store, DAILY_CAP } = counter()
      const result = await run(scenario.name, { ...scenario.options, family, env: { DAILY_CAP } })
      if (family === 'claude') {
        assertGuide(result, scenario.path, scenario.previous)
        if (scenario.name === 'check_page_seo') assert.equal(result.structuredContent.top.guide_url, linked(result)[0].guide_url)
      } else assertNoGuide(result)
      const guideCounts = [...store].filter(([key]) => key.includes(':guide:'))
      assert.deepEqual(guideCounts, family === 'claude' ? [[`t:${new Date().toISOString().slice(0, 10)}:guide:claude`, 1]] : [])
    }
  }
})

test('clean checks, short snippets and note-only answers have no guide or guide count', async () => {
  const { store, DAILY_CAP } = counter()
  for (const { name } of TOOLS) assertNoGuide(await run(name, { env: { DAILY_CAP } }))
  assertNoGuide(await run('preview_search_snippet', { args: { title: 'Short', description: '' }, env: { DAILY_CAP } }))
  assertNoGuide(await run('check_page_seo', { data: { ...DATA, canonicals: [], jsonld: [] }, env: { DAILY_CAP } }))
  assertNoGuide(await run('check_http_headers', { routes: { 'https://example.com/': { headers: { 'Strict-Transport-Security': 'max-age=1' } } }, env: { DAILY_CAP } }))
  assertNoGuide(await run('trace_redirects', { routes: { 'https://example.com/': { status: 302, headers: { Location: '/garden/' } },
    'https://example.com/garden/': {} }, env: { DAILY_CAP } }))
  assert.ok(![...store.keys()].some((k) => k.includes(':guide:')))
})

test('an unmapped first fix never borrows a guide from a later finding', async () => {
  const { store, DAILY_CAP } = counter()
  const blocked = await run('check_page_seo', { data: { ...DATA, titles: [] }, routes: { ...ROUTES,
    'https://example.com/robots.txt': { body: 'User-agent: Googlebot\nDisallow: /' } }, env: { DAILY_CAP } })
  assert.match(blocked.content[0].text, /^.*\nFix first .*Googlebot/)
  assertNoGuide(blocked)
  const headers = await run('check_http_headers', { routes: { 'https://example.com/': { headers: { 'X-Robots-Tag': 'noindex' } } }, env: { DAILY_CAP } })
  assertNoGuide(headers)
  assert.ok(![...store.keys()].some((k) => k.includes(':guide:')))
})

test('site-side Not checked outcomes, input errors and denied calls never get a guide count', async () => {
  const { store, DAILY_CAP } = counter()
  const env = { DAILY_CAP }
  for (const name of ['check_page_seo', 'check_ai_crawlers', 'check_http_headers']) {
    const routes = name === 'check_ai_crawlers' ? { 'https://example.com/robots.txt': { status: 403 } } :
      name === 'check_http_headers' ? {} : { 'https://example.com/': { status: 403 } }
    const result = await run(name, { routes, env })
    assert.equal(result.structuredContent.checked, false)
    assertNoGuide(result)
  }
  // Unreadable robots.txt blocks every row by default, not by a rule the guide can fix.
  assertNoGuide(await run('check_ai_crawlers', { routes: {}, env }))
  for (const [args, extra] of [[{}, {}], [{ title: 'Garden plants '.repeat(10) }, { MCP_LIMITER: { limit: async () => ({ success: false }) } }]]) {
    const result = (await (await handle(request('tools/call', { name: 'preview_search_snippet', arguments: args }, 'claude.test'),
      fetcher({}), { ...env, ...extra })).json()).result
    assert.equal(result.isError, true)
    assertNoGuide(result)
  }
  assert.ok(![...store.keys()].some((k) => k.includes(':guide:')))
})

test('guide mapping covers only findings answered by the checked local pages', () => {
  for (const [labels, path, area] of [
    [['No title tag', 'The title tag is empty', 'Long title: 80 wide', 'Short title: 10 wide'], '/how-to/write-title-tags-that-fit/'],
    [['No meta description', 'The meta description is empty', 'Long description: 200 wide', 'Short description: 10 wide'], '/how-to/write-meta-descriptions/'],
    [['2 canonical tags that disagree'], '/how-to/fix-conflicting-canonicals/'],
    [['No canonical tag', 'Canonical points to another address', 'The canonical is a relative address'], '/learn/canonical-tags/'],
    [['No H1 heading'], '/how-to/fix-heading-structure/'],
    [['No language declared'], '/how-to/fix-lang-attribute-mismatch/'],
    [['No viewport tag'], '/how-to/check-mobile-seo-from-a-crawl/'],
    [['No og:title', 'No og:image', 'No og:description', 'No twitter:card'], '/how-to/fix-missing-open-graph-tags/'],
    [['The page is not served over HTTPS', 'The page ends up on plain http', 'Served over plain http'], '/how-to/redirect-http-to-https/'],
    [['Redirect loop', 'More than 10 redirects', '2 redirects before the page', '1 temporary redirect (302)'], '/how-to/fix-redirect-problems/'],
    [['Block 1 is not valid JSON'], '/how-to/json-ld-parser-errors/'],
    [['Article is missing headline', 'Recipe is missing name, image'], '/how-to/fix-structured-data-errors/', 'Structured data'],
    [['2 of 3 AI search crawlers are blocked'], '/how-to/fix-ai-crawler-access/'],
    [['No HSTS header', 'Missing 1 baseline security header', 'Missing 2 baseline security headers'], '/how-to/fix-missing-security-headers/'],
    [['No caching headers', 'No compression'], '/how-to/fix-compression-and-caching/'],
  ]) for (const label of labels) assert.equal(guidePath({ label, area }), path, label)
  assert.equal(guidePath({ agent: 'Amazonbot', allowed: false, rule: 'Disallow: /' }), '/how-to/fix-ai-crawler-access/')
  for (const label of ['The canonical is not a valid address', 'This page asks search engines not to index it',
    'The server asks search engines not to index this page', 'Block 1 has no @context', 'Googlebot may not crawl this page',
    'Bingbot may not crawl this page', 'The chain breaks', 'The chain ends on HTTP 404', 'robots.txt could not be read',
    '2 title tags', '2 meta descriptions', 'No JSON-LD on this page', 'New unknown finding']) assert.equal(guidePath({ label }), null, label)
  assert.equal(guidePath({ allowed: false, rule: null }), null)
})

test('every mapped path is a local how-to or learn page, never a sales page or another domain', () => {
  for (const path of new Set(GUIDES.map((g) => g.path))) {
    assert.match(path, /^\/(how-to|learn)\/[a-z0-9-]+\/$/)
    const html = readFileSync(new URL(`../../../site${path}index.html`, import.meta.url), 'utf8')
    assert.match(html, /<h1[ >]/)
  }
})

test('the one-line switch suppresses text and structured guide URLs', async () => {
  const source = readFileSync(new URL('../src/guides.js', import.meta.url), 'utf8')
  const disabled = await import(`data:text/javascript,${encodeURIComponent(source.replace('GUIDE_LINKS = true', 'GUIDE_LINKS = false'))}`)
  const out = { text: 'Fix first: No title tag', guide: { finding: { level: 'problem', label: 'No title tag' }, after: 0 } }
  assert.equal(disabled.addGuide(out, 'claude'), false)
  assert.equal(out.text, 'Fix first: No title tag')
  assert.equal(out.guide.finding.guide_url, undefined)
})

test('TOOLS and server instructions remain byte-for-byte unchanged from J1', () => {
  const snapshot = JSON.parse(readFileSync(new URL('./fixtures/mcp-contract.json', import.meta.url), 'utf8'))
  const source = readFileSync(new URL('../src/mcp.js', import.meta.url), 'utf8')
  assert.equal(source.slice(source.indexOf('const url = '), source.indexOf('// ------------------------------------------------------------------ the checks')), snapshot.tools)
  assert.equal(/      instructions: ('.*') \} \},/.exec(source)[1], snapshot.instructions)
})
