// node --test workers/ai-crawler-check/test/
import { test } from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { handle } from '../src/index.js'
import { TOOLS, SESSION_LIMIT } from '../src/mcp.js'
import { AI_AGENTS } from '../src/agents.js'

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
