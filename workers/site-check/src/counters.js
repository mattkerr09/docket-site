import { VISITOR_DAILY_CAP, HOST_DAILY_CAP, HOST_INTERVAL_MS, GLOBAL_DAILY_CAP,
  DAY_MS, LEASE_MS, PURGE_BATCH, MAX_COUNTER_BYTES, HASH_LABEL, BUSY_MESSAGE } from './limits.js'
import { readCapped, realClock } from './io.js'

const HASH = /^[a-f0-9]{64}$/
const DAY = /^\d{4}-\d{2}-\d{2}$/
const dayAt = (now) => new Date(now).toISOString().slice(0, 10)
const dayEnd = (now) => Math.floor(now / DAY_MS) * DAY_MS + DAY_MS
const unavailable = () => new Error('The free checker could not check its limits. Try again later.')
const json = (body, status = 200) => new Response(JSON.stringify(body), { status, headers: { 'Content-Type': 'application/json', 'Cache-Control': 'no-store' } })

export async function digest(value) {
  const bytes = new Uint8Array(await crypto.subtle.digest('SHA-256', new TextEncoder().encode(value)))
  return [...bytes].map((byte) => byte.toString(16).padStart(2, '0')).join('')
}

const stub = (env) => env.SITE_CHECK_COUNTERS.get(env.SITE_CHECK_COUNTERS.idFromName('global'))

export async function reserve(request, host, env, clock) {
  const ip = request.headers.get('CF-Connecting-IP')
  if (!ip) throw unavailable()
  const day = dayAt(clock.now())
  const visitor = await digest(`${HASH_LABEL}|visitor|${day}|${ip}`)
  const hostHash = await digest(`${HASH_LABEL}|host|${day}|${host}`)
  const response = await stub(env).fetch('https://counter.invalid/reserve', {
    method: 'POST', body: JSON.stringify({ visitor, host: hostHash }),
  })
  const body = await readCapped(response, MAX_COUNTER_BYTES)
  if (body.truncated) throw unavailable()
  const data = JSON.parse(body.text)
  if (response.status === 429 && data.error === 'limit' && typeof data.message === 'string') return { allowed: false, status: 429, error: 'limit', message: data.message }
  if (response.status === 503 && data.error === 'busy' && data.message === BUSY_MESSAGE) return { allowed: false, status: 503, error: 'busy', message: BUSY_MESSAGE }
  if (response.status !== 200 || data.allowed !== true || data.visitor !== visitor || data.day !== day || !HASH.test(data.token)) throw unavailable()
  return data
}

export async function release(reservation, env) {
  const response = await stub(env).fetch('https://counter.invalid/release', {
    method: 'POST', body: JSON.stringify({ visitor: reservation.visitor, token: reservation.token, day: reservation.day }),
  })
  const body = await readCapped(response, MAX_COUNTER_BYTES)
  if (body.truncated || response.status !== 200 || JSON.parse(body.text).released !== true) throw unavailable()
}

async function purge(storage, day) {
  const keys = [...(await storage.list({ prefix: 'd:', end: `d:${day}:` })).keys()]
  for (let i = 0; i < keys.length; i += PURGE_BATCH) await storage.delete(keys.slice(i, i + PURGE_BATCH))
}

export class SiteCheckCounters {
  constructor(state, env, clock = realClock) { this.storage = state.storage; this.clock = clock }

  async fetch(request) {
    try {
      const route = new URL(request.url).pathname
      if (request.method !== 'POST' || !['/reserve', '/release'].includes(route)) return json({ error: 'bad_request', message: 'That counter request is not valid.' }, 400)
      const body = await readCapped(request, MAX_COUNTER_BYTES)
      if (body.truncated) return json({ error: 'bad_request', message: 'That counter request is too large.' }, 400)
      const data = JSON.parse(body.text)
      const fields = Object.keys(data).sort().join(',')
      const valid = route === '/reserve'
        ? fields === 'host,visitor' && HASH.test(data.visitor) && HASH.test(data.host)
        : fields === 'day,token,visitor' && HASH.test(data.visitor) && HASH.test(data.token) && DAY.test(data.day)
      if (!valid) return json({ error: 'bad_request', message: 'That counter request is not valid.' }, 400)
      const now = this.clock.now()
      const day = dayAt(now)
      // Set this before granting a reservation. An alarm error refuses work.
      await this.storage.setAlarm(dayEnd(now))
      return await this.storage.transaction(async (tx) => {
        await purge(tx, day)
        if (route === '/release') {
          if (data.day === day) {
            const key = `d:${day}:v:${data.visitor}`
            const row = await tx.get(key)
            if (row?.token === data.token) await tx.put(key, { count: row.count })
          }
          return json({ released: true })
        }
        const visitorKey = `d:${day}:v:${data.visitor}`
        const hostKey = `d:${day}:h:${data.host}`
        const globalKey = `d:${day}:g`
        const [visitor = { count: 0 }, host = { count: 0, last: 0 }, global = 0] = await Promise.all([
          tx.get(visitorKey), tx.get(hostKey), tx.get(globalKey),
        ])
        // Corrupt state is an error, never a fresh allowance.
        if (!Number.isSafeInteger(global) || global < 0 || !Number.isSafeInteger(visitor.count) || visitor.count < 0 ||
          !Number.isSafeInteger(host.count) || host.count < 0 || !Number.isFinite(host.last) || host.last < 0 || host.last > now ||
          (visitor.token !== undefined && (!HASH.test(visitor.token) || !Number.isFinite(visitor.until) || visitor.until < 0))) throw unavailable()
        if (global >= GLOBAL_DAILY_CAP) return json({ error: 'busy', message: BUSY_MESSAGE }, 503)
        if (visitor.count >= VISITOR_DAILY_CAP || (visitor.token && visitor.until > now)) return json({ error: 'limit', message: 'You can run one check at a time, up to five a day. Try again later.' }, 429)
        if (host.count >= HOST_DAILY_CAP || (host.count > 0 && now - host.last < HOST_INTERVAL_MS)) return json({ error: 'limit', message: 'This site can be checked once a minute, up to three times a day. Try again later.' }, 429)
        const token = await digest(crypto.randomUUID())
        await tx.put(visitorKey, { count: visitor.count + 1, token, until: Math.min(now + LEASE_MS, dayEnd(now)) })
        await tx.put(hostKey, { count: host.count + 1, last: now })
        await tx.put(globalKey, global + 1)
        return json({ allowed: true, visitor: data.visitor, token, day })
      })
    } catch {
      return json({ error: 'unavailable', message: 'The free checker could not check its limits. Try again later.' }, 503)
    }
  }

  async alarm() {
    // Let storage errors throw so the runtime retries the alarm.
    await this.storage.transaction((tx) => purge(tx, dayAt(this.clock.now())))
    await this.storage.setAlarm(dayEnd(this.clock.now()))
  }
}
