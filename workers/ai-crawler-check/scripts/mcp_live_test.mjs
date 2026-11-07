// A plain MCP client over Streamable HTTP, for testing the live /mcp endpoint the way a connector host calls it.
//
//   node workers/ai-crawler-check/scripts/mcp_live_test.mjs https://ai-crawler-check.kerrco.workers.dev/mcp [out.json]
//
// initialize (keeps the Mcp-Session-Id and protocol version it is given), notifications/initialized, tools/list, then one
// call of every tool on Docket's own site, and one deliberately bad call. Prints PASS or FAIL per check and, with an
// output path, writes every tool's real output to it. Exits 1 on any FAIL.
import { writeFileSync } from 'node:fs'

const endpoint = process.argv[2]
const outPath = process.argv[3]
if (!endpoint) { console.error('usage: mcp_live_test.mjs <endpoint> [out.json]'); process.exit(2) }
let session = null, version = null, id = 0, fails = 0
const record = {}
const check = (ok, line) => { if (!ok) fails++; console.log(`${ok ? 'PASS' : 'FAIL'}  ${line}`) }

async function send(method, params, notify = false) {
  const headers = { 'Content-Type': 'application/json', Accept: 'application/json, text/event-stream', 'User-Agent': 'docket-mcp-live-test/1' }
  if (session) headers['Mcp-Session-Id'] = session
  if (version) headers['MCP-Protocol-Version'] = version
  const body = notify ? { jsonrpc: '2.0', method, params } : { jsonrpc: '2.0', id: ++id, method, params }
  const t0 = Date.now()
  const r = await fetch(endpoint, { method: 'POST', headers, body: JSON.stringify(body) })
  const ms = Date.now() - t0
  if (notify) return { status: r.status, ms }
  const text = await r.text()
  return { status: r.status, ms, headers: r.headers, json: text ? JSON.parse(text) : null }
}

const init = await send('initialize', { protocolVersion: '2025-06-18', capabilities: {}, clientInfo: { name: 'docket-mcp-live-test', version: '1' } })
session = init.headers.get('mcp-session-id'); version = init.json?.result?.protocolVersion
check(init.status === 200 && !!session && version === '2025-06-18', `initialize: ${init.json?.result?.serverInfo?.title} ${init.json?.result?.serverInfo?.version}, protocol ${version}, session ${session ? 'issued' : 'MISSING'}`)
const note = await send('notifications/initialized', {}, true)
check(note.status === 202, `notifications/initialized: HTTP ${note.status}`)
const list = await send('tools/list', {})
const tools = list.json?.result?.tools || []
check(tools.length === 5 && tools.every((t) => t.title && t.annotations?.readOnlyHint === true && t.name.length <= 64), `tools/list: ${tools.map((t) => t.name).join(', ')}`)
record.tools = tools

const calls = [
  ['check_page_seo', { url: 'docketseo.app' }],
  ['check_ai_crawlers', { url: 'docketseo.app' }],
  ['trace_redirects', { url: 'http://docketseo.app/' }],
  ['check_http_headers', { url: 'docketseo.app' }],
  ['preview_search_snippet', { title: 'Docket SEO: SEO, copy, conversion and brand audits for Mac', description: 'Docket SEO audits any website on your Mac with 99 checks, ranked into a fix plan.' }],
]
record.calls = []
for (const [name, args] of calls) {
  const r = await send('tools/call', { name, arguments: args })
  const res = r.json?.result || {}
  const text = res.content?.[0]?.text || ''
  check(r.status === 200 && res.isError === false && text.length > 0, `${name} in ${r.ms} ms: ${text.split('\n')[0].slice(0, 110)}`)
  record.calls.push({ name, args, ms: r.ms, isError: res.isError, text, structuredContent: res.structuredContent })
}
const bad = await send('tools/call', { name: 'check_page_seo', arguments: { url: 'http://localhost/' } })
check(bad.json?.result?.isError === true && /address is/.test(bad.json.result.content[0].text), `bad input is a clear error: "${bad.json?.result?.content?.[0]?.text}"`)
record.bad = bad.json?.result
if (outPath) writeFileSync(outPath, JSON.stringify({ endpoint, at: new Date().toISOString(), ...record }, null, 1) + '\n')
process.exit(fails ? 1 : 0)
