/**
 * ai-crawler-check: the server half of docketseo.app/tools/ai-crawler-checker/.
 *
 *   GET /check?url=<a site>&agents=GPTBot,OAI-SearchBot,…&path=/
 *
 * A browser cannot read another site's robots.txt (CORS), so this fetches it
 * once and returns, per crawler, whether the file lets it in. It reads
 * robots.txt ONLY. It never requests a page as a crawler, and it never
 * pretends to be one: it identifies itself (USER_AGENT below).
 *
 * SAFETY, because anyone can type any address into the page:
 *   - http(s) only; no user:pass@; default ports only; no IP literals in
 *     any notation; no single-label, localhost or private-use names.
 *   - It only ever fetches /robots.txt on the host given, and follows at
 *     most five redirects (RFC 9309 §2.3.1.2), re-checking each hop.
 *   - Reads at most 512 KiB (the RFC asks parsers to handle 500 KiB), with
 *     a timeout, and caches each file for ten minutes at the edge, so a
 *     burst of checks against one site costs that site one request.
 *   - Nothing is stored. The address is not logged beyond Cloudflare's own
 *     request logs.
 *   - CORS answers only https://docketseo.app. Any other Origin gets a 403.
 *     Requests with no Origin (curl) are answered, because a browser is the
 *     only thing CORS protects and a script can fetch robots.txt itself.
 */
import { evaluate, parseRobots } from './robots.js'

export const ALLOWED_ORIGIN = 'https://docketseo.app'
export const USER_AGENT = 'DocketRobotsCheck/1.0 (+https://docketseo.app/tools/ai-crawler-checker/)'
const MAX_BYTES = 512 * 1024
const MAX_REDIRECTS = 5
const TIMEOUT_MS = 8000
const MAX_AGENTS = 40

const PRIVATE_SUFFIXES = ['.localhost', '.local', '.internal', '.intranet', '.lan', '.home',
  '.home.arpa', '.corp', '.test', '.invalid', '.example', '.onion', '.arpa']

/** Why this host must not be fetched, or null. */
export function unsafeHost(hostname) {
  const h = String(hostname || '').toLowerCase().replace(/\.$/, '')
  if (!h || h.length > 253) return 'no host name'
  if (h.startsWith('[') || h.includes(':')) return 'an IP address, not a site name'
  // Every IPv4 spelling a URL parser accepts: dotted, decimal, hex, octal.
  if (/^[0-9.]+$/.test(h) || /^0x[0-9a-f]+$/i.test(h) || /^(0x[0-9a-f]+|[0-9]+)(\.(0x[0-9a-f]+|[0-9]+)){0,3}$/i.test(h)) {
    return 'an IP address, not a site name'
  }
  if (!h.includes('.')) return 'not a public site name'
  if (h === 'localhost' || PRIVATE_SUFFIXES.some((s) => h.endsWith(s))) return 'a private or reserved name'
  if (!/^[a-z0-9.-]+$/.test(h)) return 'not a valid host name'
  return null
}

/** Parse what a person typed into a URL we are willing to use, or throw. */
export function siteFrom(input) {
  let raw = String(input || '').trim()
  if (!raw) throw new Error('Enter a website address.')
  if (!/^[a-z][a-z0-9+.-]*:\/\//i.test(raw)) raw = 'https://' + raw
  let u
  try { u = new URL(raw) } catch { throw new Error('That is not a website address.') }
  if (u.protocol !== 'http:' && u.protocol !== 'https:') throw new Error('Only http and https addresses can be checked.')
  if (u.username || u.password) throw new Error('Addresses with a user name or password are not checked.')
  if (u.port && !((u.protocol === 'https:' && u.port === '443') || (u.protocol === 'http:' && u.port === '80'))) {
    throw new Error('Only the standard web ports are checked.')
  }
  const why = unsafeHost(u.hostname)
  if (why) throw new Error(`That address is ${why}.`)
  return u
}

function cors(origin) {
  return origin === ALLOWED_ORIGIN
    ? { 'Access-Control-Allow-Origin': ALLOWED_ORIGIN, Vary: 'Origin' }
    : { Vary: 'Origin' }
}

function json(body, status, origin) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json; charset=utf-8', 'Cache-Control': 'no-store',
      'X-Content-Type-Options': 'nosniff', ...cors(origin) },
  })
}

async function readCapped(response) {
  if (!response.body) return { text: '', truncated: false, bytes: 0 }
  const reader = response.body.getReader()
  const chunks = []
  let total = 0
  let truncated = false
  for (;;) {
    const { done, value } = await reader.read()
    if (done) break
    const room = MAX_BYTES - total
    if (value.byteLength > room) {
      chunks.push(value.slice(0, room)); total += room; truncated = true
      await reader.cancel()
      break
    }
    chunks.push(value); total += value.byteLength
  }
  const buf = new Uint8Array(total)
  let at = 0
  for (const c of chunks) { buf.set(c, at); at += c.byteLength }
  return { text: new TextDecoder('utf-8', { fatal: false }).decode(buf), truncated, bytes: total }
}

/**
 * Fetch robots.txt for `site`, following redirects by hand so every hop is
 * re-checked. Returns what RFC 9309 §2.3.1 says a crawler should conclude.
 */
export async function fetchRobots(site, fetchImpl = fetch) {
  let url = new URL('/robots.txt', site.origin)
  const hops = []
  for (let i = 0; i <= MAX_REDIRECTS; i++) {
    const ctrl = new AbortController()
    const timer = setTimeout(() => ctrl.abort(), TIMEOUT_MS)
    let res
    try {
      res = await fetchImpl(url.toString(), {
        method: 'GET',
        redirect: 'manual',
        signal: ctrl.signal,
        headers: { 'User-Agent': USER_AGENT, Accept: 'text/plain,*/*;q=0.5' },
        cf: { cacheTtl: 600, cacheEverything: true },
      })
    } catch (e) {
      clearTimeout(timer)
      return { state: 'unreachable', status: null, url: url.toString(), hops,
        note: ctrl.signal.aborted ? 'The server did not answer within 8 seconds.' : 'The server could not be reached.' }
    }
    clearTimeout(timer)
    if (res.status >= 300 && res.status < 400) {
      const loc = res.headers.get('Location')
      if (!loc) return { state: 'unavailable', status: res.status, url: url.toString(), hops, note: 'A redirect with no destination.' }
      let next
      try { next = new URL(loc, url) } catch { return { state: 'unavailable', status: res.status, url: url.toString(), hops, note: 'A redirect to an address that is not a URL.' } }
      const why = (next.protocol === 'http:' || next.protocol === 'https:') ? unsafeHost(next.hostname) : 'not http or https'
      if (why) return { state: 'blocked', status: res.status, url: url.toString(), hops, note: `robots.txt redirects to ${why}, which this tool will not follow.` }
      hops.push(next.toString())
      url = next
      continue
    }
    if (res.status >= 200 && res.status < 300) {
      const body = await readCapped(res)
      const type = (res.headers.get('Content-Type') || '').toLowerCase()
      return { state: 'parsed', status: res.status, url: url.toString(), hops, body,
        html: type.includes('text/html') || /^\s*<(!doctype|html)/i.test(body.text) }
    }
    if (res.status === 429) {
      return { state: 'unreachable', status: 429, url: url.toString(), hops,
        note: 'The server answered 429 (too many requests). Google treats that like a server error and stays out; RFC 9309 would read it as "no robots.txt".' }
    }
    if (res.status >= 400 && res.status < 500) return { state: 'unavailable', status: res.status, url: url.toString(), hops }
    return { state: 'unreachable', status: res.status, url: url.toString(), hops }
  }
  return { state: 'unavailable', status: null, url: url.toString(), hops, note: 'More than five redirects; RFC 9309 lets a crawler treat that as no robots.txt.' }
}

export function agentsFrom(param) {
  const list = String(param || '').split(',').map((s) => s.trim()).filter(Boolean)
  const seen = new Set()
  const out = []
  for (const a of list) {
    if (!/^[A-Za-z_-]{1,40}$/.test(a) || seen.has(a.toLowerCase())) continue
    seen.add(a.toLowerCase()); out.push(a)
    if (out.length >= MAX_AGENTS) break
  }
  return out
}

export async function handle(request, fetchImpl = fetch) {
  const origin = request.headers.get('Origin')
  if (origin && origin !== ALLOWED_ORIGIN) return json({ error: 'This checker only answers docketseo.app.' }, 403, origin)
  if (request.method === 'OPTIONS') {
    return new Response(null, { status: 204, headers: { ...cors(origin), 'Access-Control-Allow-Methods': 'GET', 'Access-Control-Max-Age': '86400' } })
  }
  if (request.method !== 'GET') return json({ error: 'GET only.' }, 405, origin)
  const u = new URL(request.url)
  if (u.pathname === '/health') return json({ ok: true }, 200, origin)
  if (u.pathname !== '/check') return json({ error: 'Not found.' }, 404, origin)

  let site
  try { site = siteFrom(u.searchParams.get('url')) } catch (e) { return json({ error: e.message }, 400, origin) }
  const agents = agentsFrom(u.searchParams.get('agents'))
  if (!agents.length) return json({ error: 'No crawlers to check.' }, 400, origin)
  let path = u.searchParams.get('path') || site.pathname || '/'
  if (!path.startsWith('/')) path = '/' + path
  path = path.slice(0, 2048)

  const got = await fetchRobots(site, fetchImpl)
  const base = { site: site.origin, path, robots_url: got.url, redirects: got.hops, status: got.status,
    state: got.state, note: got.note || null, checked_at: new Date().toISOString() }

  if (got.state === 'blocked') return json({ ...base, results: [] }, 200, origin)
  if (got.state !== 'parsed') {
    // RFC 9309 §2.3.1.3 and §2.3.1.4: no file means everyone may crawl;
    // a file the server failed to serve means nobody should.
    const allowed = got.state === 'unavailable'
    return json({ ...base, results: agents.map((agent) => ({ agent, allowed, named: false, governedBy: 'status', rule: null })),
      warnings: [], sitemaps: [] }, 200, origin)
  }
  const parsed = parseRobots(got.body.text)
  const warnings = [...parsed.warnings]
  if (got.body.truncated) warnings.unshift('The file is larger than 512 KiB; only the first 512 KiB was read, as most crawlers do.')
  if (got.html) warnings.unshift('The server answered /robots.txt with a web page, not a robots.txt file. Crawlers read it as text and find no rules in it.')
  return json({ ...base, bytes: got.body.bytes,
    results: agents.map((agent) => evaluate(parsed, agent, path)),
    warnings: warnings.slice(0, 20), sitemaps: parsed.sitemaps.slice(0, 20) }, 200, origin)
}

export default {
  fetch(request) { return handle(request) },
}
