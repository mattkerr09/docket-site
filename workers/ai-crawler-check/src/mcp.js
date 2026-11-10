/**
 * POST /mcp: Docket SEO's free checks as a remote MCP server (Streamable HTTP, JSON responses, no auth).
 *
 * Matthew, 2026-11-07, via the CEO: a free, authless connector for Claude's directory, exposing the checks this worker
 * already runs for docketseo.app/tools/. Anthropic's directory rules, read 2026-11-07 (research/step-change-growth-
 * 2026-11-07.md Part A): every tool has a title and readOnlyHint, names of 64 characters or fewer, errors that say what
 * went wrong, reasonable response sizes, and NO promotion in descriptions or results. A scope line naming the desktop app
 * was removed on 2026-11-07: OpenAI's plugin rules forbid promoting upgrades in results, and one server serves both.
 *
 * Rate limits are per MCP session, not per IP: every claude.ai call comes from Anthropic's address range, so a per-IP
 * limit would throttle all Claude users together. A global daily cap (DailyCap, a Durable Object) keeps the worker from
 * being run up. Nothing about a check is stored; fetched pages are cached for five minutes at the edge.
 */
import { BASE, NAME } from './site-brand.js'
import { fetchPage, fetchRobots, siteFrom, PAGE_AGENT } from './index.js'
import { checkMeta, checkJsonLd, displayWidth, extract } from './page.js'
import { evaluate, parseRobots } from './robots.js'
import { checkHeaders, checkRedirects, trace } from './trace.js'
import { AI_AGENTS } from './agents.js'
import { addGuide } from './guides.js'
import { checkAccessibilityHtml, STANDARD, DISCLAIMER } from './access.js'

// Built for phase F2. The CEO switches it on after 7 Dec 2026, with the paid add-on.
export const ACCESS_TOOL_ENABLED = false

export const PROTOCOL_VERSIONS = ['2025-06-18', '2025-03-26', '2024-11-05']
// icons: the MCP Implementation.icons field (sizes as "WxH" strings). ChatGPT showed a placeholder without it (2026-11-07).
export const SERVER_INFO = { name: 'docket-seo', title: NAME, version: '1.0.0', websiteUrl: BASE,
  icons: [
    { src: `${BASE}/icon.png`, mimeType: 'image/png', sizes: ['512x512'] },
    { src: `${BASE}/apple-touch-icon.png`, mimeType: 'image/png', sizes: ['180x180'] },
  ] }
export const SESSION_LIMIT = 30        // tool calls per session per minute
export const DAILY_CAP = 20000         // tool calls per UTC day, all sessions together
const TITLE_MIN = 25, TITLE_MAX = 65, DESC_MIN = 70, DESC_MAX = 165
const PROBLEM_COST = 12, WARNING_COST = 5
const SEARCH = ['Googlebot', 'Bingbot']
const CITE = ['OAI-SearchBot', 'Claude-SearchBot', 'PerplexityBot']

export function clientFamily(clientInfo) {
  const name = typeof clientInfo?.name === 'string' ? clientInfo.name : ''
  if (/claude|anthropic/i.test(name)) return 'claude'
  if (/openai|chatgpt/i.test(name)) return 'chatgpt'
  return 'other'
}

export function familyOf(header) {
  return typeof header === 'string' ? /^(claude|chatgpt)\./.exec(header)?.[1] || 'other' : 'other'
}

/**
 * The site decided the outcome, not the tool: it refused, failed, timed out or is not a web page. Claude's directory
 * counted every one of these as a tool error (6.5% of 169 calls in the 30 days to 8 Nov 2026), and the person saw one
 * bare sentence. They are facts about the site, so they come back as a normal result that starts "Not checked:", says
 * why in plain words and says what to do. Only a bad address and our own limits stay errors (the assistant can fix the
 * first and must wait out the second).
 */
export class NotChecked extends Error {
  constructor(detail, status = null) {
    super(detail)
    const why = classify(detail, status)
    this.reason = why.reason
    this.advice = why.advice
  }
}
function classify(detail, status) {
  const d = String(detail || '')
  if (status === 401 || status === 403 || status === 429 || /bot check|refused/i.test(d))
    // No product link: the directory's rules (and the "promotes nothing" tests) keep tool results free of promotion.
    return { reason: 'refused', advice: 'The site turned away this checker, which runs on cloud servers; many sites do that to cloud traffic and still let visitors in. Look at the page from your own connection instead, for example in a browser\u2019s page source.' }
  if (status === 404 || status === 410)
    return { reason: 'not_found', advice: 'Check the address. If it is right, the page itself is missing, and visitors see the same error.' }
  if (status && status >= 500)
    return { reason: 'server_error', advice: 'The site\u2019s server failed. Try again in a minute; if it keeps failing, visitors are seeing the error too.' }
  if (status && status >= 400)
    return { reason: 'http_error', advice: 'Check the address. The site answered with an error rather than the page.' }
  if (/within 8 seconds/.test(d))
    return { reason: 'timeout', advice: 'Try again. A page that keeps taking longer than 8 seconds is slow for visitors and search crawlers too.' }
  if (/could not be reached/.test(d))
    return { reason: 'unreachable', advice: 'Check that the address is spelled right and that the site is online.' }
  if (/not a web page/.test(d))
    return { reason: 'not_html', advice: 'Give the address of an HTML page rather than a file.' }
  if (/redirect/i.test(d))
    return { reason: 'redirects', advice: 'The trace_redirects tool lists every hop, so you can see where the chain breaks.' }
  return { reason: 'other', advice: 'Try again, or check the address.' }
}

const url = { type: 'string', description: 'The page address, for example example.com/pricing/. https:// is assumed if left out.' }
export const TOOLS = [
  { name: 'check_page_seo', title: 'Check one page for SEO problems',
    description: 'Reads one web page and its robots.txt and reports a score out of 100, problems by area (crawling and indexing, security, search listing, page basics, AI search, structured data, sharing) and the most serious problem with its fix.',
    inputSchema: { type: 'object', properties: { url }, required: ['url'] }, annotations: { readOnlyHint: true, openWorldHint: true } },
  { name: 'check_ai_crawlers', title: 'Check which AI crawlers robots.txt allows',
    description: "Reads a site's robots.txt and says, for each AI crawler (OpenAI, Anthropic, Perplexity, Google, Apple, Meta, Parallel and others), whether it may fetch the given path and which rule decides.",
    inputSchema: { type: 'object', properties: { url }, required: ['url'] }, annotations: { readOnlyHint: true, openWorldHint: true } },
  { name: 'trace_redirects', title: 'Trace a redirect chain',
    description: 'Follows an address one hop at a time and lists each hop with its HTTP status code and destination, then flags loops, chains of two or more redirects, temporary redirects and pages left on plain http.',
    inputSchema: { type: 'object', properties: { url }, required: ['url'] }, annotations: { readOnlyHint: true, openWorldHint: true } },
  { name: 'check_http_headers', title: 'Check a page’s HTTP response headers',
    description: 'Returns the final status code and the response headers that matter for search and security (X-Robots-Tag, Cache-Control, Strict-Transport-Security, X-Content-Type-Options, Referrer-Policy and others), with a verdict on each.',
    inputSchema: { type: 'object', properties: { url }, required: ['url'] }, annotations: { readOnlyHint: true, openWorldHint: true } },
  { name: 'preview_search_snippet', title: 'Preview a search result title and description',
    description: 'Measures a title and meta description and shows where a search result would cut each off. Fetches nothing.',
    inputSchema: { type: 'object', properties: {
      title: { type: 'string', description: 'The page title.' },
      description: { type: 'string', description: 'The meta description.' } }, required: ['title'] },
    annotations: { readOnlyHint: true, openWorldHint: false } },
]
for (const t of TOOLS) { t.annotations.title = t.title; t.annotations.destructiveHint = false; t.annotations.idempotentHint = true }

// ------------------------------------------------------------------ the checks

// Keep the five-tool contract above unchanged while this switch is off.
if (ACCESS_TOOL_ENABLED) TOOLS.push({ name: 'check_accessibility', title: 'Check one page for accessibility problems',
  description: 'Reads one page of HTML for some WCAG 2.1 Level A and AA problems. Reports each problem and a fix. HTML only, with no rendering: colour contrast, focus and reflow are not checked. Automated checks find some problems, not all. This is not legal advice.',
  inputSchema: { type: 'object', properties: { url }, required: ['url'] },
  annotations: { title: 'Check one page for accessibility problems', readOnlyHint: true, openWorldHint: true, destructiveHint: false, idempotentHint: true } })

export async function checkAccessibility(args, fetchImpl) {
  const pg = await fetchPage(siteFrom(args.url), fetchImpl)
  if (pg.error) throw new NotChecked(pg.error, pg.status || null)
  const data = checkAccessibilityHtml(pg.body.text, { truncated: pg.body.truncated })
  const lines = [`Accessibility checks for ${pg.url}`, `Standard: ${STANDARD}`,
    ...data.by_sc.map((r) => `${r.sc} ${r.sc_name}, Level ${r.level}: ${r.count}`)]
  for (const f of data.findings.slice(0, 3)) lines.push(`${f.sc} ${f.sc_name}, Level ${f.level}: ${f.certainty}. ${f.element} ${f.problem} Fix: ${f.fix}`)
  lines.push('HTML only. No rendering. Colour contrast, focus and reflow are not checked.')
  if (data.limits.page_truncated || data.limits.parser_truncated) lines.push('Only part of the HTML was checked. Counts cover the part read.')
  if (data.limits.name_depth_limited || data.limits.name_work_limited) lines.push('Some names need review because the HTML reached this check\'s reading limits.')
  if (data.limits.findings_truncated) lines.push('The data lists the first 25 findings. Counts include all findings in the HTML checked.')
  lines.push(DISCLAIMER)
  return { text: lines.join('\n'), structured: { url: pg.url, checked_at: new Date().toISOString(), standard: STANDARD, ...data } }
}

function areaOf(label) {
  if (/og:|twitter/i.test(label)) return 'Sharing'
  if (/title|description/i.test(label)) return 'Search listing'
  if (/index|canonical|nofollow/i.test(label)) return 'Crawling and indexing'
  return 'Page basics'
}

async function robotsFor(site, path, agents, fetchImpl) {
  const got = await fetchRobots(site, fetchImpl)
  if (got.state === 'blocked') return { state: 'blocked', note: got.note, results: [] }
  if (got.state !== 'parsed') {
    const allowed = got.state === 'unavailable'
    return { state: got.state, status: got.status, robots_url: got.url, note: got.note,
      results: agents.map((agent) => ({ agent, allowed, governedBy: 'status', rule: null })) }
  }
  const parsed = parseRobots(got.body.text)
  return { state: 'parsed', robots_url: got.url, results: agents.map((a) => evaluate(parsed, a, path)) }
}

export async function checkPageSeo(args, fetchImpl, env = {}) {
  const site = siteFrom(args.url)
  const path = (site.pathname || '/') + (site.search || '')
  const [pg, rb] = await Promise.all([fetchPage(site, fetchImpl), robotsFor(site, path, [...SEARCH, ...CITE], fetchImpl)])
  if (pg.error) throw new NotChecked(pg.error, pg.status || null)
  const data = await (env.extract || extract)(pg.body.text)
  const items = []
  const add = (area, level, label, detail = '') => items.push({ area, level, label, detail })
  if (/^http:/i.test(pg.url)) add('Security', 'problem', 'The page is not served over HTTPS', 'Serve it over HTTPS and redirect the http:// address to it.')
  if (pg.hops.length > 1) add('Crawling and indexing', 'warning', `${pg.hops.length} redirects before the page`, `Link straight to ${pg.url}.`)
  if (rb.state === 'unavailable' && (rb.status === 401 || rb.status === 403)) add('Crawling and indexing', 'note', 'The site refused this checker its robots.txt', 'Crawler access is unknown, so it is not scored.')
  else if (rb.state === 'unreachable') add('Crawling and indexing', 'problem', 'robots.txt could not be read', 'Crawlers stay out until it can be read. Make it return 200, or 404 if there are no rules.')
  else if (rb.state !== 'blocked') {
    const by = Object.fromEntries(rb.results.map((r) => [r.agent, r]))
    for (const a of SEARCH) if (by[a] && !by[a].allowed) add('Crawling and indexing', 'problem', `${a} may not crawl this page`, `robots.txt blocks it${by[a].rule ? ` with "${by[a].rule}"` : ''}. Remove or narrow that line if the page should appear in search.`)
    const shut = CITE.filter((a) => by[a] && !by[a].allowed)
    if (shut.length) add('AI search', 'warning', `${shut.length} of ${CITE.length} AI search crawlers are blocked`, `${shut.join(', ')}. These decide whether ChatGPT search, Claude and Perplexity can find and quote the page.`)
  }
  for (const f of checkMeta({ ...data, url: pg.url, xRobots: pg.xRobots }).findings) add(areaOf(f.label), f.level, f.label, f.detail)
  for (const f of checkJsonLd(data.jsonld).findings) add('Structured data', f.level, f.label, f.detail)
  const problems = items.filter((f) => f.level === 'problem')
  const warnings = items.filter((f) => f.level === 'warning')
  const score = Math.max(0, 100 - PROBLEM_COST * problems.length - WARNING_COST * warnings.length)
  const top = problems[0] || warnings[0] || null
  const lines = [`${pg.url}: score ${score}/100, ${problems.length} problem(s) and ${warnings.length} thing(s) worth fixing.`]
  if (top) lines.push(`Fix first (${top.area}): ${top.label}. ${top.detail}`)
  for (const f of items.filter((x) => x !== top && (x.level === 'problem' || x.level === 'warning'))) lines.push(`- ${f.level === 'problem' ? 'Problem' : 'Worth fixing'} (${f.area}): ${f.label}. ${f.detail}`)
  lines.push(`Score: 100, less ${PROBLEM_COST} for each problem and ${WARNING_COST} for each thing worth fixing, on this one page.`)
  return { text: lines.join('\n'), structured: { url: pg.url, score, problems: problems.length, worth_fixing: warnings.length, top, findings: items },
    guide: { finding: top, after: 1 } }
}

export async function checkAiCrawlers(args, fetchImpl) {
  const site = siteFrom(args.url)
  const path = (site.pathname || '/') + (site.search || '')
  const rb = await robotsFor(site, path, AI_AGENTS.map((a) => a.agent), fetchImpl)
  if (rb.state === 'blocked') throw new NotChecked(rb.note || 'robots.txt redirects somewhere this tool will not follow.')
  if (rb.state === 'unavailable' && (rb.status === 401 || rb.status === 403)) {
    throw new NotChecked(`${rb.robots_url} refused this checker (HTTP ${rb.status}), so what it tells crawlers is unknown.`, rb.status)
  }
  const meta = Object.fromEntries(AI_AGENTS.map((a) => [a.agent, a]))
  const rows = rb.results.map((r) => ({ agent: r.agent, owner: meta[r.agent].owner, purpose: meta[r.agent].purpose, allowed: r.allowed, rule: r.rule || null }))
  const head = rb.state === 'parsed' ? `Read ${rb.robots_url} for ${path}.`
    : rb.state === 'unavailable' && rb.status ? `${rb.robots_url} was not found (HTTP ${rb.status}), so every crawler may crawl.`
    // No status: robots.txt redirected more than five times (it said "HTTP null" here until 8 Nov 2026).
    : rb.state === 'unavailable' ? `${rb.robots_url}: ${rb.note || 'no robots.txt could be read'} So every crawler may crawl.`
    : `${rb.robots_url} could not be read, so crawlers stay out until it can.`
  const lines = [head, ...rows.map((r) => `- ${r.agent} (${r.owner}, ${r.purpose}): ${r.allowed ? 'allowed' : 'blocked'}${r.rule ? ` by "${r.rule}"` : ''}`)]
  const first = rows.findIndex((r) => !r.allowed)
  return { text: lines.join('\n'), structured: { robots_url: rb.robots_url, path, crawlers: rows },
    guide: { finding: rows[first], after: first + 1 } }
}

export async function traceRedirects(args, fetchImpl) {
  const site = siteFrom(args.url)
  const t = await trace(site, fetchImpl, PAGE_AGENT)
  const findings = checkRedirects(t, site.toString())
  const lines = t.hops.map((h, i) => `${i + 1}. ${h.url} -> HTTP ${h.status} -> ${h.location || '(no destination)'}`)
  if (t.final) lines.push(`${t.hops.length + 1}. ${t.final.url} -> HTTP ${t.final.status} (the page)`)
  for (const f of findings) lines.push(`${f.level === 'ok' ? 'Fine' : f.level === 'note' ? 'Note' : f.level === 'warning' ? 'Worth fixing' : 'Problem'}: ${f.label}${f.detail ? `. ${f.detail}` : ''}`)
  const first = findings.findIndex((f) => f.level === 'problem' || f.level === 'warning')
  return { text: lines.join('\n'), structured: { hops: t.hops, final: t.final ? { url: t.final.url, status: t.final.status } : null, findings },
    guide: { finding: findings[first], after: t.hops.length + (t.final ? 1 : 0) + first } }
}

export async function checkHttpHeaders(args, fetchImpl) {
  const site = siteFrom(args.url)
  const t = await trace(site, fetchImpl, PAGE_AGENT)
  if (!t.final) throw new NotChecked(t.error || (t.loop ? `The address redirects in a loop through ${t.loop}.` : 'The redirects did not end on a page.'))
  const findings = checkHeaders(t)
  const lines = [`HTTP ${t.final.status} from ${t.final.url}${t.hops.length ? ` after ${t.hops.length} redirect(s)` : ''}.`,
    ...t.final.headers.map((h) => `${h.name}: ${h.value}`),
    ...findings.map((f) => `${f.level === 'ok' ? 'Fine' : f.level === 'note' ? 'Note' : f.level === 'warning' ? 'Worth fixing' : 'Problem'}: ${f.label}${f.detail ? `. ${f.detail}` : ''}`)]
  const first = findings.findIndex((f) => f.level === 'problem' || f.level === 'warning')
  return { text: lines.join('\n'), structured: { url: t.final.url, status: t.final.status, headers: t.final.headers, findings },
    guide: { finding: findings[first], after: t.final.headers.length + 1 + first } }
}

function cut(text, max) {
  if (displayWidth(text) <= max) return text
  let n = 0, out = ''
  for (const ch of text) { const w = displayWidth(ch); if (n + w > max - 1) break; n += w; out += ch }
  const sp = out.lastIndexOf(' ')
  return (sp > out.length * 0.6 ? out.slice(0, sp) : out).replace(/[\s,|:;-]+$/, '') + ' …'
}
function verdict(w, lo, hi, what) {
  if (!w) return `No ${what}.`
  if (w > hi) return `${w} wide: too long, a search result cuts it after about ${hi}.`
  if (w < lo) return `${w} wide: short, under ${lo} leaves a result little to show.`
  return `${w} wide: fits the range of ${lo} to ${hi}.`
}
export function previewSnippet(args) {
  const title = String(args.title || '').replace(/\s+/g, ' ').trim()
  const desc = String(args.description || '').replace(/\s+/g, ' ').trim()
  if (!title) throw new Error('Give a title to preview.')
  const tw = displayWidth(title), dw = displayWidth(desc)
  const lines = [`Title as shown: ${cut(title, TITLE_MAX)}`, `Title: ${verdict(tw, TITLE_MIN, TITLE_MAX, 'title')}`]
  if (desc) lines.push(`Description as shown: ${cut(desc, DESC_MAX)}`)
  lines.push(`Description: ${verdict(dw, DESC_MIN, DESC_MAX, 'description')}`,
    'Width counts East Asian wide characters as two, as search results render them about twice as wide.')
  const findings = []
  if (tw > TITLE_MAX) findings.push({ level: 'warning', label: `Long title: ${tw} wide` })
  if (dw > DESC_MAX) findings.push({ level: 'warning', label: `Long description: ${dw} wide` })
  return { text: lines.join('\n'), structured: { title_width: tw, description_width: dw, title_shown: cut(title, TITLE_MAX), description_shown: desc ? cut(desc, DESC_MAX) : '', findings },
    guide: { finding: findings[0], after: tw > TITLE_MAX ? 1 : 3 } }
}

const RUN = { check_page_seo: checkPageSeo, check_ai_crawlers: checkAiCrawlers, trace_redirects: traceRedirects,
  check_http_headers: checkHttpHeaders, preview_search_snippet: (a) => previewSnippet(a),
  ...(ACCESS_TOOL_ENABLED ? { check_accessibility: checkAccessibility } : {}) }

// ------------------------------------------------------------------ the protocol

function reply(body, status = 200, headers = {}) {
  return new Response(body === null ? null : JSON.stringify(body), { status,
    headers: { 'Content-Type': 'application/json', 'Cache-Control': 'no-store', ...headers } })
}
const rpcError = (id, code, message) => reply({ jsonrpc: '2.0', id: id ?? null, error: { code, message } })

async function overSession(key, env) {
  if (env.MCP_LIMITER && typeof env.MCP_LIMITER.limit === 'function') {
    const { success } = await env.MCP_LIMITER.limit({ key })
    return !success
  }
  return false
}
async function overDailyCap(env) {
  if (!env.DAILY_CAP) return false
  const stub = env.DAILY_CAP.get(env.DAILY_CAP.idFromName('global'))
  const r = await stub.fetch('https://cap.invalid/hit')
  const { count } = await r.json()
  return count > DAILY_CAP
}

export async function handleMcp(request, fetchImpl = fetch, env = {}) {
  if (request.method === 'GET') return new Response('This MCP server answers POST only; it does not open an event stream.', { status: 405, headers: { Allow: 'POST' } })
  if (request.method === 'DELETE') return new Response(null, { status: 204 })
  if (request.method !== 'POST') return new Response('POST only.', { status: 405, headers: { Allow: 'POST' } })
  let msg
  try { msg = await request.json() } catch { return rpcError(null, -32700, 'The request body is not valid JSON.') }
  if (Array.isArray(msg)) return rpcError(null, -32600, 'Send one JSON-RPC message per request; batches are not supported.')
  if (!msg || msg.jsonrpc !== '2.0' || typeof msg.method !== 'string') return rpcError(msg && msg.id, -32600, 'Not a JSON-RPC 2.0 request.')
  const { id, method, params = {} } = msg
  if (id === undefined) return new Response(null, { status: 202 })   // a notification, e.g. notifications/initialized

  if (method === 'initialize') {
    const asked = params.protocolVersion
    const version = PROTOCOL_VERSIONS.includes(asked) ? asked : PROTOCOL_VERSIONS[0]
    const family = clientFamily(params.clientInfo)
    await tally(env, 'init', family)
    return reply({ jsonrpc: '2.0', id, result: { protocolVersion: version, capabilities: { tools: { listChanged: false } },
      serverInfo: SERVER_INFO,
      instructions: 'Free, read-only checks of public web pages: a one-page SEO check, AI crawler access in robots.txt, redirect chains, HTTP headers and a search snippet preview. Each tool takes a page address; nothing is stored.' } },
    200, { 'Mcp-Session-Id': `${family}.${crypto.randomUUID()}` })
  }
  if (method === 'ping') return reply({ jsonrpc: '2.0', id, result: {} })
  if (method === 'tools/list') return reply({ jsonrpc: '2.0', id, result: { tools: TOOLS } })
  if (method !== 'tools/call') return rpcError(id, -32601, `Unknown method: ${method}.`)

  const family = familyOf(request.headers.get('Mcp-Session-Id'))
  await tally(env, 'calls', family)
  const name = params.name
  const run = RUN[name]
  if (!run) return rpcError(id, -32602, `Unknown tool: ${name}. The tools are ${TOOLS.map((t) => t.name).join(', ')}.`)
  const session = request.headers.get('Mcp-Session-Id') || request.headers.get('CF-Connecting-IP') || 'anonymous'
  if (await overSession(session, env)) {
    await tally(env, name, 'limit')
    return reply({ jsonrpc: '2.0', id, result: { isError: true, content: [{ type: 'text', text: `Too many checks in this conversation: the limit is ${SESSION_LIMIT} a minute. Wait a minute and try again.` }] } })
  }
  if (await overDailyCap(env)) {
    return reply({ jsonrpc: '2.0', id, result: { isError: true, content: [{ type: 'text', text: 'The free checks have reached their daily limit. They reset at midnight UTC.' }] } })
  }
  try {
    const out = await run(params.arguments || {}, fetchImpl, env)
    if (addGuide(out, family)) await tally(env, 'guide', family)
    await tally(env, name, 'ok')
    return reply({ jsonrpc: '2.0', id, result: { content: [{ type: 'text', text: out.text }], structuredContent: out.structured, isError: false } })
  } catch (e) {
    if (e instanceof NotChecked) {
      await tally(env, name, e.reason)
      return reply({ jsonrpc: '2.0', id, result: { isError: false,
        content: [{ type: 'text', text: `Not checked: ${e.message} ${e.advice}` }],
        structuredContent: { checked: false, reason: e.reason, detail: e.message, advice: e.advice } } })
    }
    await tally(env, name, 'input')
    return reply({ jsonrpc: '2.0', id, result: { isError: true, content: [{ type: 'text', text: String((e && e.message) || e || 'The check failed.') }] } })
  }
}

/**
 * Initializations and calls by assistant family, plus how each tool call ended, counted per UTC day: never a client
 * name, session id or address. Read with GET /mcp/stats and the STATS_KEY secret (index.js).
 */
async function tally(env, tool, outcome) {
  if (!env.DAILY_CAP) return
  try {
    const stub = env.DAILY_CAP.get(env.DAILY_CAP.idFromName('global'))
    await stub.fetch(`https://cap.invalid/tally?k=${encodeURIComponent(`${tool}:${outcome}`)}`)
  } catch { /* a count is never worth a failed check */ }
}

/** One counter for the whole worker, per UTC day; and the outcome tally above. */
export class DailyCap {
  constructor(state) { this.state = state }
  async fetch(request) {
    const u = new URL(request ? request.url : 'https://cap.invalid/hit')
    const day = new Date().toISOString().slice(0, 10)
    if (u.pathname === '/tally') {
      const k = (u.searchParams.get('k') || '').slice(0, 80)
      if (!/^[a-z_]+:[a-z_]+$/.test(k)) return new Response('bad key', { status: 400 })
      const key = `t:${day}:${k}`
      await this.state.storage.put(key, ((await this.state.storage.get(key)) || 0) + 1)
      return new Response('ok')
    }
    if (u.pathname === '/stats') {
      const since = new Date(Date.now() - 35 * 86400e3).toISOString().slice(0, 10)
      const rows = {}
      for (const [key, n] of await this.state.storage.list({ prefix: 't:' })) {
        const [, d, k] = key.match(/^t:([^:]+):(.+)$/) || []
        if (!d) continue
        if (d < since) { await this.state.storage.delete(key); continue }
        rows[k] = (rows[k] || 0) + n
      }
      return new Response(JSON.stringify({ since, outcomes: rows }), { headers: { 'Content-Type': 'application/json' } })
    }
    const key = `n:${day}`
    const n = ((await this.state.storage.get(key)) || 0) + 1
    await this.state.storage.put(key, n)
    return new Response(JSON.stringify({ day, count: n }), { headers: { 'Content-Type': 'application/json' } })
  }
}
