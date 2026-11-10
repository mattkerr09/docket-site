import { BASE } from './site-brand.js'
import { siteFrom, hostKey, normalOrigin, BadAddress } from './safety.js'
import { crawl } from './crawl.js'
import { reserve, release, digest } from './counters.js'
import { realClock, readCapped, bounded } from './io.js'
import { CACHE_TTL_S, MAX_SUMMARY_BYTES, COUNTER_TIMEOUT_MS, CACHE_TIMEOUT_MS } from './limits.js'
export { SiteCheckCounters } from './counters.js'

const json = (body, status, origin) => new Response(JSON.stringify(body), {
  status,
  headers: { 'Content-Type': 'application/json; charset=utf-8', 'Cache-Control': 'no-store',
    'X-Content-Type-Options': 'nosniff', Vary: 'Origin',
    ...(origin === BASE ? { 'Access-Control-Allow-Origin': BASE } : {}) },
})
const unavailable = { error: 'unavailable', message: 'The free checker could not check its limits. Try again later.' }

async function cached(cache, key, clock) {
  if (!cache) return null
  try {
    return await bounded(clock, clock.now() + CACHE_TIMEOUT_MS, async (signal) => {
      const hit = await cache.match(key)
      if (!hit) return null
      const body = await readCapped(hit, MAX_SUMMARY_BYTES, signal)
      if (body.truncated) return null
      const summary = JSON.parse(body.text)
      const age = clock.now() - Date.parse(summary.checked_at)
      if (!Number.isFinite(age) || age < 0 || age >= CACHE_TTL_S * 1000 || !Array.isArray(summary.issues) || !Array.isArray(summary.fine)) return null
      return { ...summary, from_cache: true }
    })
  } catch { return null }
}

export async function handle(request, env = {}, runtime = {}) {
  const origin = request.headers.get('Origin')
  if (env.SITE_CHECK_DISABLED === '1') return json({ error: 'disabled', message: 'The free checker is turned off. Try again later.' }, 503, origin)
  if (origin !== BASE) return json({ error: 'origin', message: 'This checker only answers checkengineseo.com.' }, 403, origin)
  const url = new URL(request.url)
  if (url.pathname !== '/site-check') return json({ error: 'not_found', message: 'That checker address was not found.' }, 404, origin)
  if (request.method === 'OPTIONS') return new Response(null, { status: 204, headers: {
    'Access-Control-Allow-Origin': BASE, 'Access-Control-Allow-Methods': 'GET', Vary: 'Origin', 'Cache-Control': 'no-store',
  } })
  if (request.method !== 'GET') return json({ error: 'method', message: 'Use GET to run a check.' }, 405, origin)
  let site
  try { site = siteFrom(url.searchParams.get('url')) } catch (error) { return json({ error: 'bad_address', message: error.message }, 400, origin) }
  const clock = runtime.clock || realClock
  let reservation
  try {
    reservation = await bounded(clock, clock.now() + COUNTER_TIMEOUT_MS, () => reserve(request, hostKey(site), env, clock))
  } catch { return json(unavailable, 503, origin) }
  if (!reservation.allowed) return json({ error: reservation.error, message: reservation.message }, reservation.status, origin)
  let summary
  let failure
  const cache = runtime.cache ?? globalThis.caches?.default
  try {
    const key = `https://summary.site-check.invalid/${await digest(normalOrigin(site))}`
    summary = await cached(cache, key, clock)
    if (!summary) {
      if (new Date(clock.now()).toISOString().slice(0, 10) !== reservation.day) throw new Error('The daily limit window ended.')
      summary = await crawl(site, runtime)
      const body = JSON.stringify(summary)
      if (cache && new TextEncoder().encode(body).byteLength < MAX_SUMMARY_BYTES) {
        try {
          await bounded(clock, clock.now() + CACHE_TIMEOUT_MS, () => cache.put(key, new Response(body, {
            headers: { 'Content-Type': 'application/json', 'Cache-Control': `public, max-age=${CACHE_TTL_S}` },
          })))
        } catch { /* A cache error never bypasses a limit. */ }
      }
    }
  } catch (error) {
    failure = error instanceof BadAddress
      ? json({ error: 'bad_address', message: error.message }, 400, origin)
      : json({ error: 'unavailable', message: 'The site could not be checked safely. Try again later.' }, 503, origin)
  }
  try {
    await bounded(clock, clock.now() + COUNTER_TIMEOUT_MS, () => release(reservation, env))
  } catch { return json(unavailable, 503, origin) }
  return failure || json(summary, 200, origin)
}

export default { fetch: (request, env) => handle(request, env) }
