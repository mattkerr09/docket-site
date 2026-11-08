// node --test workers/ai-crawler-check/test/
import { test } from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { handle } from '../src/index.js'
import { TOOLS, ACCESS_TOOL_ENABLED, SESSION_LIMIT, DAILY_CAP, DailyCap, clientFamily, familyOf } from '../src/mcp.js'
import { AI_AGENTS } from '../src/agents.js'
import { DISCLAIMER } from '../src/access.js'

// Exercise the real protocol with only the release constant changed. No runtime flag can enable the shipped tool.
const enabledMcp = async () => {
  const file = new URL('../src/mcp.js', import.meta.url)
  const source = readFileSync(file, 'utf8').replace('ACCESS_TOOL_ENABLED = false', 'ACCESS_TOOL_ENABLED = true')
    .replace(/from '(\.\/[^']+)'/g, (_, path) => `from '${new URL(path, file).href}'`)
  return import(`data:text/javascript,${encodeURIComponent(source)}`)
}

function net(routes) {
  const seen = []
  const fetchImpl = async (url, init) => {
    seen.push(url)
    const r = routes[url]
    if (!r) throw new Error('unreachable')
    return new Response(r.body ?? '', { status: r.status ?? 200, headers: r.headers ?? { 'Content-Type': 'text/html' } })
  }
  return { seen, fetchImpl }
}
const call = (body, headers = {}) => new Request('https://w.example.workers.dev/mcp', {
  method: 'POST', headers: { 'Content-Type': 'application/json', Accept: 'application/json, text/event-stream', ...headers },
  body: typeof body === 'string' ? body : JSON.stringify(body) })
const rpc = (method, params, id = 1) => ({ jsonrpc: '2.0', id, method, params })
const tool = (name, args) => rpc('tools/call', { name, arguments: args })
const EXTRACT = { extract: async () => ({ lang: 'en', titles: ['Plumber in Grand Rapids, open all night'], metas: { description: ['A licensed plumber at your door within the hour, any time, with upfront prices and a one-year guarantee.'], viewport: ['width=device-width'], 'og:title': ['x'], 'og:image': ['x'] }, canonicals: [], h1s: ['Plumber'], jsonld: [] }) }

function counter() {
  const store = new Map()
  const state = { storage: { get: async (k) => store.get(k), put: async (k, v) => { store.set(k, v) },
    delete: async (k) => { store.delete(k) }, list: async ({ prefix }) => new Map([...store].filter(([k]) => k.startsWith(prefix))) } }
  const cap = new DailyCap(state)
  return { store, DAILY_CAP: { idFromName: () => 'g', get: () => ({ fetch: (u) => cap.fetch(new Request(u)) }) } }
}

test('client names map to one of three families, including missing, empty and long names', () => {
  for (const [name, family] of [
    ['Claude Desktop', 'claude'], ['ANTHROPIC connector', 'claude'],
    ['OpenAI client', 'chatgpt'], ['cHaTgPt', 'chatgpt'],
    ['', 'other'], ['Unknown client', 'other'], [undefined, 'other'], [42, 'other'],
    ['x'.repeat(200), 'other'], ['x'.repeat(194) + 'ClAuDe', 'claude'],
    ['x'.repeat(194) + 'OpenAI', 'chatgpt'],
  ]) assert.equal(clientFamily({ name }), family)
  assert.equal(clientFamily(), 'other')
  assert.equal(clientFamily(null), 'other')
})

test('initialize session prefixes round trip and other headers have no known family', async () => {
  for (const [name, family] of [['Claude', 'claude'], ['OpenAI', 'chatgpt'], ['Unknown client', 'other'], [undefined, 'other']]) {
    const r = await handle(call(rpc('initialize', { clientInfo: { name } })), fetch, {})
    const session = r.headers.get('Mcp-Session-Id')
    assert.match(session, new RegExp(`^${family}\\.[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$`))
    assert.equal(familyOf(session), family)
  }
  for (const header of [null, undefined, '', 'old-session-id', 'claude', 'chatgpt', 'Claude.id', 'openai.id', 'other.id', 'unknown.claude.id']) {
    assert.equal(familyOf(header), 'other')
  }
})

test('initialize answers with a session id and a supported protocol version', async () => {
  const r = await handle(call(rpc('initialize', { protocolVersion: '2025-06-18', capabilities: {}, clientInfo: { name: 't', version: '1' } })), async () => { throw new Error('no fetch') }, {})
  const j = await r.json()
  assert.equal(j.result.protocolVersion, '2025-06-18')
  assert.equal(j.result.serverInfo.name, 'docket-seo')
  assert.ok(r.headers.get('Mcp-Session-Id'))
  const old = await (await handle(call(rpc('initialize', { protocolVersion: '1999-01-01' })), fetch, {})).json()
  assert.equal(old.result.protocolVersion, '2025-06-18')
})

test('a notification gets 202 and no body; GET is refused with 405', async () => {
  const n = await handle(call({ jsonrpc: '2.0', method: 'notifications/initialized' }), fetch, {})
  assert.equal(n.status, 202)
  const g = await handle(new Request('https://w.example.workers.dev/mcp'), fetch, {})
  assert.equal(g.status, 405)
})

test('every tool meets the directory rules: title, read-only, name of 64 characters or fewer, no promotion', async () => {
  const j = await (await handle(call(rpc('tools/list', {})), fetch, {})).json()
  assert.equal(j.result.tools.length, 5)
  for (const t of j.result.tools) {
    assert.ok(t.title && t.annotations.title, `${t.name} has a title`)
    assert.equal(t.annotations.readOnlyHint, true)
    assert.equal(t.annotations.destructiveHint, false)
    assert.ok(t.name.length <= 64)
    assert.doesNotMatch(t.description, /docket|buy|price|\$|download|upgrade|desktop app/i, `${t.name} description promotes nothing`)
  }
})

test('the page check returns a score, problems by area and the top fix, and promotes nothing', async () => {
  const { fetchImpl } = net({
    'https://shop.com/': { status: 200, body: '<html></html>' },
    'https://shop.com/robots.txt': { status: 200, headers: { 'Content-Type': 'text/plain' }, body: 'User-agent: *\nAllow: /\nUser-agent: OAI-SearchBot\nDisallow: /' },
  })
  const j = await (await handle(call(tool('check_page_seo', { url: 'shop.com' })), fetchImpl, EXTRACT)).json()
  assert.equal(j.result.isError, false)
  const s = j.result.structuredContent
  assert.equal(typeof s.score, 'number')
  assert.equal(s.top.area, 'AI search')
  assert.match(j.result.content[0].text, /score \d+\/100/)
  assert.doesNotMatch(j.result.content[0].text, /Docket|desktop app|buy|price/i, 'results promote nothing (OpenAI and Anthropic rules)')
})

test('the AI crawler check covers every crawler in the site data, ShapBot included, and says which rule decides', async () => {
  const fromSite = JSON.parse(readFileSync(new URL('../../../data/ai-agents.json', import.meta.url))).agents
  assert.deepEqual(AI_AGENTS.map((a) => a.agent).sort(), Object.keys(fromSite).sort(), 'agents.js is regenerated from data/ai-agents.json')
  const { fetchImpl } = net({ 'https://b.com/robots.txt': { status: 200, headers: { 'Content-Type': 'text/plain' }, body: 'User-agent: ShapBot\nDisallow: /\n\nUser-agent: *\nAllow: /' } })
  const j = await (await handle(call(tool('check_ai_crawlers', { url: 'b.com' })), fetchImpl, {})).json()
  const shap = j.result.structuredContent.crawlers.find((c) => c.agent === 'ShapBot')
  assert.equal(shap.allowed, false)
  assert.equal(shap.rule, 'Disallow: /')
  assert.match(j.result.content[0].text, /ShapBot \(Parallel Web Systems, search index\): blocked/)
})

test('redirects and headers are traced with each status code', async () => {
  const routes = {
    'http://c.com/': { status: 301, headers: { Location: 'https://c.com/' } },
    'https://c.com/': { status: 302, headers: { Location: 'https://www.c.com/' } },
    'https://www.c.com/': { status: 200, headers: { 'Content-Type': 'text/html', 'Strict-Transport-Security': 'max-age=1' } },
  }
  const r = await (await handle(call(tool('trace_redirects', { url: 'http://c.com/' })), net(routes).fetchImpl, {})).json()
  assert.deepEqual(r.result.structuredContent.hops.map((h) => h.status), [301, 302])
  assert.match(r.result.content[0].text, /2 redirects before the page/)
  const h = await (await handle(call(tool('check_http_headers', { url: 'http://c.com/' })), net(routes).fetchImpl, {})).json()
  assert.equal(h.result.structuredContent.status, 200)
  assert.match(h.result.content[0].text, /strict-transport-security: max-age=1/)
})

test('the snippet preview cuts a long title and measures East Asian width as double', async () => {
  const j = await (await handle(call(tool('preview_search_snippet', { title: 'Emergency plumber in Grand Rapids, open 24 hours a day | Your Business Name', description: 'Short.' })), fetch, {})).json()
  assert.match(j.result.content[0].text, /too long/)
  const ja = await (await handle(call(tool('preview_search_snippet', { title: '小形羊羹 24本入 | 株式会社 虎屋' })), fetch, {})).json()
  assert.equal(ja.result.structuredContent.title_width, 31)
})

test('every tool promotes nothing in its text or structured content on fixture pages', async () => {
  const title = 'A helpful guide to garden plants'
  const description = 'Learn how to choose garden plants and care for them through every season with this simple guide.'
  const data = { lang: 'en', titles: [title], metas: { description: [description], viewport: ['width=device-width'],
    'og:title': [title], 'og:image': ['https://example.com/garden.png'] }, canonicals: ['https://example.com/garden/'],
    h1s: ['Garden plants'], jsonld: [JSON.stringify({ '@context': 'https://schema.org', '@type': 'Article', headline: title })] }
  const { fetchImpl } = net({
    'http://example.com/': { status: 301, headers: { Location: 'https://example.com/' } },
    'https://example.com/': { status: 302, headers: { Location: '/garden/' } },
    'https://example.com/garden/': { body: '<html></html>', headers: { 'Content-Type': 'text/html',
      'Strict-Transport-Security': 'max-age=31536000', 'X-Content-Type-Options': 'nosniff', 'Referrer-Policy': 'strict-origin-when-cross-origin' } },
    'http://example.com/robots.txt': { body: 'User-agent: *\nAllow: /', headers: { 'Content-Type': 'text/plain' } },
  })
  for (const { name } of TOOLS) {
    const j = await (await handle(call(tool(name, { url: 'http://example.com/', title, description })), fetchImpl, { extract: async () => data })).json()
    assert.equal(j.result.isError, false, name)
    assert.ok(j.result.structuredContent, name)
    const promotion = /docket|docketseo|download|buy|price|licen[cs]e|upgrade|\$\d/i
    assert.doesNotMatch(j.result.content[0].text, promotion, `${name} text promotes nothing`)
    assert.doesNotMatch(JSON.stringify(j.result.structuredContent), promotion, `${name} data promotes nothing`)
    if (name === 'check_page_seo') {
      const findings = j.result.structuredContent.findings
      assert.ok(findings.some((f) => f.level === 'ok' && /Title length is fine/.test(f.label)))
      assert.ok(findings.some((f) => f.level === 'ok' && /none missing a required property/.test(f.label)))
    }
    if (name === 'trace_redirects') assert.equal(j.result.structuredContent.hops.length, 2)
    if (name === 'check_http_headers') assert.ok(j.result.structuredContent.headers.some((h) => h.name === 'strict-transport-security'))
  }
})

test('errors say what went wrong', async () => {
  const bad = await (await handle(call(tool('check_page_seo', { url: 'localhost' })), fetch, {})).json()
  assert.equal(bad.result.isError, true)
  assert.match(bad.result.content[0].text, /address is/)
  const none = await (await handle(call(tool('preview_search_snippet', {})), fetch, {})).json()
  assert.equal(none.result.content[0].text, 'Give a title to preview.')
  const unknown = await (await handle(call(tool('nope', {})), fetch, {})).json()
  assert.match(unknown.error.message, /Unknown tool: nope\. The tools are/)
  const junk = await (await handle(call('{not json'), fetch, {})).json()
  assert.equal(junk.error.code, -32700)
})

test('the limit is per session, not per address, and a busy session is told plainly', async () => {
  const seen = []
  const env = { MCP_LIMITER: { limit: async ({ key }) => { seen.push(key); return { success: key !== 'busy' } } } }
  const ok = await (await handle(call(tool('preview_search_snippet', { title: 'A fine title for a page' }), { 'Mcp-Session-Id': 'quiet', 'CF-Connecting-IP': '160.79.104.10' }), fetch, env)).json()
  assert.equal(ok.result.isError, false)
  const busy = await (await handle(call(tool('preview_search_snippet', { title: 'A fine title for a page' }), { 'Mcp-Session-Id': 'busy', 'CF-Connecting-IP': '160.79.104.10' }), fetch, env)).json()
  assert.equal(busy.result.isError, true)
  assert.match(busy.result.content[0].text, new RegExp(`limit is ${SESSION_LIMIT} a minute`))
  assert.deepEqual(seen, ['quiet', 'busy'], 'keyed by session id, never by the shared Anthropic address')
})

test('the daily cap refuses politely once reached', async () => {
  const env = { DAILY_CAP: { idFromName: () => 'g', get: () => ({ fetch: async () => new Response(JSON.stringify({ count: 10 ** 9 })) }) } }
  const j = await (await handle(call(tool('preview_search_snippet', { title: 'A fine title for a page' })), fetch, env)).json()
  assert.equal(j.result.isError, true)
  assert.match(j.result.content[0].text, /daily limit/)
})

test('initialize carries the icons, and the favicon on the connector host redirects to the site icon', async () => {
  const j = await (await handle(call(rpc('initialize', { protocolVersion: '2025-06-18', capabilities: {}, clientInfo: { name: 't', version: '1' } })), fetch, {})).json()
  const icons = j.result.serverInfo.icons
  assert.equal(icons[0].src, 'https://docketseo.app/icon.png')
  assert.deepEqual(icons[0].sizes, ['512x512'])
  for (const path of ['/favicon.ico', '/icon.png']) {
    const r = await handle(new Request(`https://mcp.docketseo.app${path}`), fetch, {})
    assert.equal(r.status, 301)
    assert.equal(r.headers.get('Location'), 'https://docketseo.app/icon.png')
  }
})

test('a site that refuses, fails, times out or is not a page is "Not checked", with what to do: not a tool error', async () => {
  const cases = [
    [{ 'https://shop-gr.com/': { status: 403 } }, 'refused'],
    [{ 'https://shop-gr.com/': { status: 503 } }, 'server_error'],
    [{ 'https://shop-gr.com/': { status: 404 } }, 'not_found'],
    [{ 'https://shop-gr.com/': { headers: { 'Content-Type': 'application/pdf' } } }, 'not_html'],
    [{}, 'unreachable'],
  ]
  for (const [routes, reason] of cases) {
    const { fetchImpl } = net(routes)
    const j = await (await handle(call(tool('check_page_seo', { url: 'shop-gr.com' })), fetchImpl, EXTRACT)).json()
    assert.equal(j.result.isError, false, reason)
    assert.match(j.result.content[0].text, /^Not checked: /)
    assert.equal(j.result.structuredContent.checked, false)
    assert.equal(j.result.structuredContent.reason, reason)
    assert.ok(j.result.structuredContent.advice.length > 20)
    assert.doesNotMatch(j.result.content[0].text, /docketseo\.app|Docket SEO|download/i, 'results promote nothing')
  }
  const { fetchImpl } = net({})
  const bad = await (await handle(call(tool('check_page_seo', { url: 'not a url at all' })), fetchImpl, EXTRACT)).json()
  assert.equal(bad.result.isError, true, 'a bad address is still an error the assistant can fix')
})

test('a robots.txt that redirects in a loop says so, never "HTTP null"', async () => {
  const loop = { 'https://shop-gr.com/robots.txt': { status: 301, headers: { Location: 'https://shop-gr.com/robots.txt' } } }
  const { fetchImpl } = net(loop)
  const j = await (await handle(call(tool('check_ai_crawlers', { url: 'shop-gr.com' })), fetchImpl, {})).json()
  assert.equal(j.result.isError, false)
  assert.doesNotMatch(j.result.content[0].text, /null/)
  assert.match(j.result.content[0].text, /More than five redirects/)
})

test('family and outcome counts store no address, client details or session id, and the stats need the secret', async () => {
  const { store, DAILY_CAP: daily } = counter()
  const env = { ...EXTRACT, STATS_KEY: 'k'.repeat(32),
    DAILY_CAP: daily }
  const { fetchImpl } = net({ 'https://shop-gr.com/': { status: 403 } })
  const privateDetails = ['shop-gr.com', '160.79.104.10', 'PrivateUserAgent', 'PrivateVersion']
  for (const [name, family] of [['Claude PrivateClient', 'claude'], ['ChatGPT PrivateClient', 'chatgpt'], ['Unknown PrivateClient', 'other']]) {
    const r = await handle(call(rpc('initialize', { clientInfo: { name, version: 'PrivateVersion' } })), fetchImpl, env)
    const session = r.headers.get('Mcp-Session-Id')
    privateDetails.push(name, session)
    await handle(call(tool('check_page_seo', { url: 'shop-gr.com' }), {
      'Mcp-Session-Id': session, 'CF-Connecting-IP': '160.79.104.10', 'User-Agent': 'PrivateUserAgent',
    }), fetchImpl, env)
    const day = new Date().toISOString().slice(0, 10)
    assert.equal(store.get(`t:${day}:init:${family}`), 1)
    assert.equal(store.get(`t:${day}:calls:${family}`), 1)
  }
  // Missing, legacy and unrecognized session prefixes all belong to other.
  await handle(call(tool('check_page_seo', { url: 'shop-gr.com' })), fetchImpl, env)
  for (const session of ['legacy-private-session', 'private-client.private-session']) {
    privateDetails.push(session)
    await handle(call(tool('preview_search_snippet', { title: 'A fine title for a page' }), { 'Mcp-Session-Id': session }), fetchImpl, env)
  }
  for (const [key, count] of store) {
    for (const detail of privateDetails) assert.ok(!key.includes(detail), `never store ${detail}`)
    assert.match(key, /^(n:\d{4}-\d{2}-\d{2}|t:\d{4}-\d{2}-\d{2}:[a-z_]+:[a-z_]+)$/)
    assert.equal(typeof count, 'number')
  }
  assert.equal(await (await handle(new Request('https://w.example.workers.dev/mcp/stats'), fetchImpl, env)).status, 404)
  const stats = await (await handle(new Request('https://w.example.workers.dev/mcp/stats', { headers: { 'X-Stats-Key': 'k'.repeat(32) } }), fetchImpl, env)).json()
  assert.deepEqual(stats.outcomes, { 'init:claude': 1, 'calls:claude': 1, 'check_page_seo:refused': 4,
    'init:chatgpt': 1, 'calls:chatgpt': 1, 'init:other': 1, 'calls:other': 4, 'preview_search_snippet:ok': 2 })
})

test('calls are counted even for an unknown tool, bad input, session limit or daily cap', async () => {
  const { store, DAILY_CAP: daily } = counter()
  const env = { DAILY_CAP: daily }
  const headers = { 'Mcp-Session-Id': 'claude.private-session' }
  await handle(call(tool('unknown', {}), headers), fetch, env)
  await handle(call(tool('preview_search_snippet', {}), headers), fetch, env)
  await handle(call(tool('preview_search_snippet', { title: 'A fine title for a page' }), headers), fetch,
    { ...env, MCP_LIMITER: { limit: async () => ({ success: false }) } })
  const day = new Date().toISOString().slice(0, 10)
  store.set(`n:${day}`, DAILY_CAP)
  const capped = await (await handle(call(tool('preview_search_snippet', { title: 'A fine title for a page' }), headers), fetch, env)).json()
  assert.match(capped.result.content[0].text, /daily limit/)
  assert.equal(store.get(`t:${day}:calls:claude`), 4)
  assert.equal(store.get(`t:${day}:preview_search_snippet:input`), 1)
  assert.equal(store.get(`t:${day}:preview_search_snippet:limit`), 1)
})

test('accessibility is shipped off, unlisted, and exactly an unknown tool without fetching or charging limits', async () => {
  assert.equal(ACCESS_TOOL_ENABLED, false)
  const { store, DAILY_CAP: daily } = counter()
  const env = { DAILY_CAP: daily, ACCESS_TOOL_ENABLED: true,
    MCP_LIMITER: { limit: async () => { assert.fail('unknown tools do not consume limits') } } }
  const noFetch = async () => { assert.fail('disabled tool must not fetch a page') }
  const list = await (await handle(call(rpc('tools/list', {})), noFetch, env)).text()
  assert.equal(list, JSON.stringify({ jsonrpc: '2.0', id: 1, result: { tools: TOOLS } }))
  assert.equal(TOOLS.length, 5)
  const disabled = await (await handle(call(tool('check_accessibility', { url: 'example.com' })), noFetch, env)).text()
  const unknown = await (await handle(call(tool('unknown', {})), noFetch, env)).text()
  assert.equal(disabled, unknown.replace('Unknown tool: unknown.', 'Unknown tool: check_accessibility.'))
  const day = new Date().toISOString().slice(0, 10)
  assert.equal(store.get(`t:${day}:calls:other`), 2)
  assert.ok(![...store.keys()].some((k) => k.includes('check_accessibility')))
})

test('switching the constant on adds only the sixth read-only tool', async () => {
  const { handleMcp, TOOLS: enabledTools, ACCESS_TOOL_ENABLED: enabled } = await enabledMcp()
  assert.equal(enabled, true)
  const j = await (await handleMcp(call(rpc('tools/list', {})), fetch, {})).json()
  assert.equal(j.result.tools.length, 6)
  assert.deepEqual(j.result.tools.slice(0, 5), TOOLS)
  assert.deepEqual(j.result.tools, enabledTools)
  const tool = j.result.tools[5]
  assert.equal(tool.name, 'check_accessibility')
  assert.equal(tool.annotations.readOnlyHint, true)
  assert.equal(tool.annotations.destructiveHint, false)
  assert.equal(tool.annotations.idempotentHint, true)
  assert.equal(tool.annotations.title, tool.title)
  assert.deepEqual(tool.inputSchema, TOOLS[0].inputSchema)
  assert.match(tool.description, /one page of HTML/)
  assert.match(tool.description, /no rendering: colour contrast, focus and reflow are not checked/)
  assert.doesNotMatch(tool.description, /compliant|certified|guarantee|ADA compliance check|docket|download|buy|upgrade/i)
})

test('enabled accessibility reads only one page through the shared fetch and returns counts and the first three fixes', async () => {
  const { handleMcp } = await enabledMcp()
  const { store, DAILY_CAP: daily } = counter()
  const body = '<html lang="en"><head><title>Garden</title></head><body><main><img><a href="/plants"></a><button></button><iframe></iframe></main></body></html>'
  const { seen, fetchImpl } = net({
    'http://example.com/': { status: 301, headers: { Location: 'https://example.com/garden' } },
    'https://example.com/garden': { body },
  })
  const before = Date.now()
  const j = await (await handleMcp(call(tool('check_accessibility', { url: 'http://example.com' }), { 'Mcp-Session-Id': 'claude.private-session' }), async (url, init) => {
    assert.equal(init.redirect, 'manual')
    assert.equal(init.method, 'GET')
    assert.equal(init.cf.cacheTtl, 300)
    assert.match(init.headers['User-Agent'], /^DocketPageCheck/)
    return fetchImpl(url, init)
  }, { DAILY_CAP: daily })).json()
  assert.equal(j.result.isError, false)
  const s = j.result.structuredContent, text = j.result.content[0].text
  assert.deepEqual(Object.keys(s).sort(), ['url', 'checked_at', 'standard', 'by_sc', 'findings', 'limits'].sort())
  assert.equal(s.url, 'https://example.com/garden')
  assert.ok(Date.parse(s.checked_at) >= before && Date.parse(s.checked_at) <= Date.now())
  assert.equal(s.standard, 'WCAG 2.1 Level A and AA')
  assert.equal(s.by_sc.find((r) => r.sc === '4.1.2').count, 2)
  assert.equal(s.findings.length, 4)
  assert.ok(s.findings.every((f) => f.certainty === 'fails' && f.sc && f.sc_name && f.level === 'A' && f.element && f.problem && f.fix))
  assert.equal(text.split('Fix: ').length - 1, 3)
  for (const f of s.findings.slice(0, 3)) assert.ok(text.includes(`${f.element} ${f.problem} Fix: ${f.fix}`))
  assert.ok(!text.includes(s.findings[3].problem))
  assert.ok(text.startsWith('Accessibility checks for https://example.com/garden'))
  assert.ok(text.endsWith(DISCLAIMER))
  assert.equal(text.split(DISCLAIMER).length - 1, 1)
  assert.doesNotMatch(text + JSON.stringify(s), /docketseo|download|buy|price|upgrade|compliant|certified|guarantee|ADA compliance check/i)
  assert.deepEqual(seen, ['http://example.com/', 'https://example.com/garden'])
  const day = new Date().toISOString().slice(0, 10)
  assert.equal(store.get(`t:${day}:calls:claude`), 1)
  assert.equal(store.get(`t:${day}:check_accessibility:ok`), 1)
  assert.ok(![...store.keys()].some((k) => /example|private-session|guide/.test(k)))
})

test('enabled accessibility keeps NotChecked results and tallies site outcomes and bad input', async () => {
  const { handleMcp } = await enabledMcp()
  const { store, DAILY_CAP: daily } = counter()
  for (const [route, reason] of [
    [{ status: 403 }, 'refused'], [{ status: 503 }, 'server_error'], [{ status: 404 }, 'not_found'],
    [{ headers: { 'Content-Type': 'application/pdf' }, body: '%PDF' }, 'not_html'],
    [{ body: '<html><title>Just a moment...</title></html>' }, 'refused'],
    [null, 'unreachable'], [{ status: 301, headers: { Location: 'http://127.0.0.1/' } }, 'redirects'],
  ]) {
    const { seen, fetchImpl } = net(route ? { 'https://example.com/': route } : {})
    const j = await (await handleMcp(call(tool('check_accessibility', { url: 'example.com' })), fetchImpl, { DAILY_CAP: daily })).json()
    assert.equal(j.result.isError, false, reason)
    assert.match(j.result.content[0].text, /^Not checked: /)
    assert.equal(j.result.structuredContent.checked, false)
    assert.equal(j.result.structuredContent.reason, reason)
    assert.ok(j.result.structuredContent.advice)
    assert.equal(j.result.structuredContent.findings, undefined)
    assert.deepEqual(seen, ['https://example.com/'])
  }
  for (const url of ['localhost', 'http://127.0.0.1/', 'file:///tmp/page', 'https://user:pass@example.com', 'https://example.com:8443', '']) {
    const j = await (await handleMcp(call(tool('check_accessibility', { url })), async () => { assert.fail('unsafe addresses must not be fetched') }, { DAILY_CAP: daily })).json()
    assert.equal(j.result.isError, true, url)
  }
  const day = new Date().toISOString().slice(0, 10)
  for (const [outcome, expected] of [['refused', 2], ['server_error', 1], ['not_found', 1], ['not_html', 1], ['unreachable', 1], ['redirects', 1], ['input', 6]]) {
    assert.equal(store.get(`t:${day}:check_accessibility:${outcome}`), expected)
  }
})

test('enabled accessibility uses existing session and daily limits before fetching', async () => {
  const { handleMcp } = await enabledMcp()
  const { store, DAILY_CAP: daily } = counter()
  const noFetch = async () => { assert.fail('limited tool must not fetch a page') }
  const j = await (await handleMcp(call(tool('check_accessibility', { url: 'example.com' })), noFetch,
    { DAILY_CAP: daily, MCP_LIMITER: { limit: async () => ({ success: false }) } })).json()
  assert.equal(j.result.isError, true)
  assert.match(j.result.content[0].text, /limit is 30 a minute/)
  const day = new Date().toISOString().slice(0, 10)
  assert.equal(store.get(`t:${day}:check_accessibility:limit`), 1)
  store.set(`n:${day}`, DAILY_CAP)
  const cap = await (await handleMcp(call(tool('check_accessibility', { url: 'example.com' })), noFetch, { DAILY_CAP: daily })).json()
  assert.equal(cap.result.isError, true)
  assert.match(cap.result.content[0].text, /daily limit/)
})

test('enabled accessibility discloses the shared two MiB page cap and the 25-finding cap', async () => {
  const { handleMcp } = await enabledMcp()
  const body = '<html lang="en"><head><title>Garden</title></head><body><main>' + '<img>'.repeat(40) + 'x'.repeat(2 * 1024 * 1024) + '<button></button></main></body></html>'
  const { fetchImpl } = net({ 'https://example.com/': { body } })
  const j = await (await handleMcp(call(tool('check_accessibility', { url: 'example.com' })), fetchImpl)).json()
  const s = j.result.structuredContent
  assert.equal(j.result.isError, false)
  assert.equal(s.limits.page_truncated, true)
  assert.equal(s.limits.findings_truncated, true)
  assert.equal(s.limits.max_page_bytes, 2 * 1024 * 1024)
  assert.equal(s.findings.length, 25)
  assert.equal(s.by_sc.find((r) => r.sc === '1.1.1').count, 40)
  assert.equal(s.by_sc.find((r) => r.sc === '4.1.2').count, 0)
  assert.match(j.result.content[0].text, /Only part of the HTML was checked/)
  assert.match(j.result.content[0].text, /first 25 findings/)
  assert.ok(j.result.content[0].text.endsWith(DISCLAIMER))
})
