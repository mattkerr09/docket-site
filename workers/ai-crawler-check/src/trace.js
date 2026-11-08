/**
 * /trace: every hop from the address typed to the page it ends on, with each hop's status code, and
 * the final response's headers. Behind two free tools: the redirect checker and the HTTP header
 * checker (docketseo.app/tools/redirect-checker/, /tools/http-header-checker/, added 2026-11-06).
 *
 * The verdicts are Docket's own rules, ported from the engine so a free check and the app agree:
 *   - checks/indexability.py `index.redirects`: a loop is CRITICAL, two or more hops is MEDIUM.
 *   - checks/security.py `security.headers`: no HSTS is LOW, except on a TLD the browsers' HSTS
 *     preload list already forces to HTTPS; a missing X-Content-Type-Options or Referrer-Policy is a
 *     NOTICE. Neither is judged on a page served over plain http.
 * Here CRITICAL and HIGH read as 'problem', MEDIUM and LOW as 'warning', NOTICE as 'note'.
 *
 * The body of the final page is never read: the headers and status are all either tool needs.
 * Set-Cookie values are never returned.
 */
import { unsafeHost } from './index.js'

export const MAX_TRACE = 10
const TIMEOUT_MS = 8000

/** Headers the header checker shows, in display order. Everything else is counted, not shown. */
export const SHOWN = ['content-type', 'cache-control', 'content-encoding', 'last-modified', 'etag', 'vary',
  'x-robots-tag', 'link', 'strict-transport-security', 'content-security-policy',
  'content-security-policy-report-only', 'x-content-type-options', 'x-frame-options', 'referrer-policy',
  'permissions-policy', 'cross-origin-opener-policy', 'server', 'x-powered-by', 'age']

/** checks/security.py HSTS_PRELOADED_TLDS, verbatim. */
export const HSTS_PRELOADED_TLDS = new Set(['amazon', 'android', 'app', 'audible', 'azure', 'bank', 'bing', 'boo',
  'channel', 'chrome', 'dad', 'day', 'dev', 'eat', 'esq', 'fire', 'fly', 'foo', 'fujitsu', 'gle', 'gmail', 'google',
  'hangout', 'hotmail', 'imdb', 'ing', 'insurance', 'kindle', 'meet', 'meme', 'microsoft', 'mov', 'new', 'nexus',
  'office', 'page', 'phd', 'play', 'prime', 'prof', 'rsvp', 'search', 'silk', 'skype', 'windows', 'xbox',
  'xn--cckwcxetd', 'xn--jlq480n2rg', 'youtube', 'zappos', 'zip'])

export async function trace(start, fetchImpl, agent) {
  let url = new URL(start.toString())
  const hops = []
  const seen = new Set()
  for (let i = 0; i <= MAX_TRACE; i++) {
    if (seen.has(url.toString())) return { hops, loop: url.toString() }
    seen.add(url.toString())
    const ctrl = new AbortController()
    const timer = setTimeout(() => ctrl.abort(), TIMEOUT_MS)
    const t0 = Date.now()
    let res
    try {
      res = await fetchImpl(url.toString(), {
        method: 'GET', redirect: 'manual', signal: ctrl.signal,
        headers: { 'User-Agent': agent, Accept: 'text/html,application/xhtml+xml;q=0.9,*/*;q=0.1' },
        cf: { cacheTtl: 300, cacheEverything: true },
      })
    } catch (e) {
      clearTimeout(timer)
      return { hops, error: ctrl.signal.aborted ? `${url} did not answer within 8 seconds.` : `${url} could not be reached.` }
    }
    clearTimeout(timer)
    const ms = Date.now() - t0
    try { if (res.body) await res.body.cancel() } catch { /* the body is never needed */ }
    if (res.status >= 300 && res.status < 400) {
      const loc = res.headers.get('Location')
      let next = null
      try { next = loc ? new URL(loc, url) : null } catch { next = null }
      hops.push({ url: url.toString(), status: res.status, location: next ? next.toString() : (loc || null), ms })
      if (!next) return { hops, error: `A redirect (HTTP ${res.status}) with no usable destination.` }
      const why = (next.protocol === 'http:' || next.protocol === 'https:') ? unsafeHost(next.hostname) : 'not http or https'
      if (why) return { hops, error: `The address redirects to ${why}, which this tool will not follow.` }
      url = next
      continue
    }
    const headers = []
    let other = 0
    res.headers.forEach((value, name) => {
      const n = name.toLowerCase()
      if (SHOWN.includes(n)) headers.push({ name: n, value: String(value).slice(0, 500) })
      else other++
    })
    headers.sort((a, b) => SHOWN.indexOf(a.name) - SHOWN.indexOf(b.name))
    return { hops, final: { url: url.toString(), status: res.status, ms, headers, other } }
  }
  return { hops, tooMany: true }
}

function preloaded(host) {
  const tld = String(host || '').replace(/\.$/, '').split('.').pop().toLowerCase()
  return HSTS_PRELOADED_TLDS.has(tld) ? tld : null
}

/** Redirect findings for one trace, in Docket's words and levels. */
export function checkRedirects(t, startUrl) {
  const out = []
  const add = (level, label, detail = '') => out.push({ level, label, detail })
  const n = t.hops.length
  if (t.loop) add('problem', 'Redirect loop', `The chain comes back to ${t.loop}, so no visitor or crawler ever reaches a page. Browsers show "too many redirects". Trace the rules for this address and break the cycle.`)
  else if (t.tooMany) add('problem', `More than ${MAX_TRACE} redirects`, 'Browsers give up and show "too many redirects", and crawlers stop sooner. Point the first address straight at the last.')
  if (t.error) add('problem', 'The chain breaks', t.error)
  if (!t.loop && !t.tooMany) {
    if (n >= 2) add('warning', `${n} redirects before the page`, `This check reports a chain of two or more. Each hop is another request before anything loads, and crawlers may stop following. Redirect ${t.hops[0].url} straight to ${t.final ? t.final.url : 'its destination'}, and link to that address directly.`)
    else if (n === 1) add('ok', 'One redirect', `${t.hops[0].url} sends visitors to ${t.hops[0].location} in one step.`)
    else if (t.final) add('ok', 'No redirects', 'The address you entered answers directly.')
  }
  const temp = t.hops.filter((h) => h.status === 302 || h.status === 307)
  if (temp.length) add('note', `${temp.length} temporary redirect${temp.length === 1 ? '' : 's'} (${[...new Set(temp.map((h) => h.status))].join(', ')})`, 'A 302 or 307 says the move is temporary. If the old address is gone for good, a 301 or 308 says so.')
  if (t.final) {
    if (t.final.status >= 400) add('problem', `The chain ends on HTTP ${t.final.status}`, 'Visitors and crawlers reach an error, not a page. Fix the destination or point the redirect somewhere that answers 200.')
    const startHttp = /^http:/i.test(startUrl)
    if (/^http:/i.test(t.final.url)) add('problem', 'The page ends up on plain http', 'Browsers mark it not secure. Serve it over HTTPS and redirect http:// to it in one step.')
    else if (startHttp) add('ok', 'http:// is sent to HTTPS', '')
  }
  return out
}

/** Header findings for the final response, in Docket's words and levels. */
export function checkHeaders(t) {
  const out = []
  const add = (level, label, detail = '') => out.push({ level, label, detail })
  if (!t.final) return out
  const get = (n) => (t.final.headers.find((h) => h.name === n) || {}).value
  const xr = String(get('x-robots-tag') || '').toLowerCase()
  if (/\bnoindex\b|\bnone\b/.test(xr)) add('problem', 'The server asks search engines not to index this page', 'The X-Robots-Tag header says noindex. Remove it if the page should appear in search.')
  if (!/^https:/i.test(t.final.url)) {
    add('problem', 'Served over plain http', 'Security headers are only judged on an HTTPS page. Serve the site over HTTPS first.')
    return out
  }
  const host = new URL(t.final.url).hostname
  const tld = preloaded(host)
  if (get('strict-transport-security')) add('ok', 'HSTS is set', get('strict-transport-security'))
  else if (tld) add('ok', `No HSTS header needed: .${tld} is HTTPS-only in every major browser`, `The whole .${tld} domain is on the HSTS preload list built into the browsers, so a first visit is never made over http://.`)
  else add('warning', 'No HSTS header', 'Strict-Transport-Security tells browsers to use HTTPS for this site from now on, closing the window where a first visit over http:// could be intercepted. Add it at your web server or CDN: start with a short max-age, then raise it.')
  const missing = ['x-content-type-options', 'referrer-policy'].filter((h) => !get(h))
  if (missing.length) add('note', `Missing ${missing.length} baseline security header${missing.length === 1 ? '' : 's'}`, `Not set: ${missing.join(', ')}. Low-risk to add at the server or CDN. Referrer-Policy can also be set with a meta tag in the page, which this check does not read.`)
  else add('ok', 'X-Content-Type-Options and Referrer-Policy are set', '')
  return out
}
