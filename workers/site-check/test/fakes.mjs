import assert from 'node:assert/strict'
import { SiteCheckCounters } from '../src/counters.js'

export const NOW = Date.parse('2026-11-10T14:00:00Z')

export function clock(start = NOW) {
  let now = start
  let next = 0
  const timers = new Map()
  return {
    now: () => now,
    sleep: async (ms) => { now += ms },
    setTimeout(fn, ms) { const id = ++next; timers.set(id, { at: now + ms, fn }); return id },
    clearTimeout: (id) => timers.delete(id),
    advance(ms) {
      now += ms
      for (const [id, timer] of timers) if (timer.at <= now) { timers.delete(id); timer.fn() }
    },
    timers,
  }
}

export function storage() {
  const rows = new Map()
  const writes = []
  let alarm = null
  let pending = Promise.resolve()
  const api = {
    rows, writes,
    async get(key) { return structuredClone(rows.get(key)) },
    async put(key, value) { writes.push([key, structuredClone(value)]); rows.set(key, structuredClone(value)) },
    async delete(keys) { for (const key of Array.isArray(keys) ? keys : [keys]) rows.delete(key) },
    async list({ prefix = '', end } = {}) {
      return new Map([...rows].filter(([key]) => key.startsWith(prefix) && (!end || key < end)))
    },
    async setAlarm(at) { alarm = at },
    async getAlarm() { return alarm },
    async transaction(fn) {
      const run = pending.then(async () => {
        const before = structuredClone(rows)
        try { return await fn(api) } catch (error) {
          rows.clear()
          for (const [key, value] of before) rows.set(key, value)
          throw error
        }
      })
      pending = run.catch(() => {})
      return run
    },
  }
  return api
}

export function cache() {
  const rows = new Map()
  const writes = []
  return {
    rows, writes,
    async match(key) { return rows.get(String(key))?.clone() },
    async put(key, response) {
      writes.push([String(key), response.clone()])
      rows.set(String(key), response.clone())
    },
  }
}

export function perfect(over = {}) {
  return {
    titles: ['A useful title for this test page'],
    metas: { description: ['An original description for this page.'], viewport: ['width=device-width'],
      'og:title': ['A page'], 'og:image': ['/image.png'] },
    h1s: ['A heading'], canonicals: ['/'], lang: 'en', jsonld: ['{}'],
    structured: true, words: 120, imagesMissingAlt: 0, links: [],
    ...over,
  }
}

export const html = (body = '<h1>Page</h1>') => new Response(body, { headers: { 'Content-Type': 'text/html' } })
export const text = (body, status = 200) => new Response(body, { status, headers: { 'Content-Type': 'text/plain' } })

export function fetcher(pages = {}, { robots = '', time, delay = 0 } = {}) {
  const calls = []
  const fn = async (address, init = {}) => {
    const u = new URL(address)
    calls.push({ url: u.href, init, at: time?.now() })
    assert.equal(init.redirect, 'manual')
    assert.equal(init.credentials, 'omit')
    assert.equal(init.headers.Cookie, undefined)
    assert.equal(init.headers.Authorization, undefined)
    if (time && delay) time.advance(delay)
    if (u.pathname === '/robots.txt') return text(robots)
    if (u.pathname === '/sitemap.xml') return new Response('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"></urlset>', { headers: { 'Content-Type': 'application/xml' } })
    const value = pages[u.href] ?? pages[u.pathname + u.search] ?? pages[u.pathname]
    if (typeof value === 'function') return value(u, init)
    return value ? value.clone() : html(u.pathname)
  }
  fn.calls = calls
  return fn
}

export function deps(over = {}) {
  return { clock: clock(), resolve: async () => ['93.184.216.34'], extract: async () => perfect(), ...over }
}

// A small event driver for the production HTMLRewriter callbacks. Parsing itself
// belongs to the Worker runtime. These explicit fixtures test the callbacks.
export class Rewriter {
  static events = []
  handlers = new Map()
  on(selector, handler) { this.handlers.set(selector, handler); return this }
  transform(response) {
    for (const event of Rewriter.events) {
      const handler = this.handlers.get(event.selector)
      if (event.text !== undefined) handler?.text?.({ text: event.text })
      else {
        const ends = []
        handler?.element?.({ getAttribute: (key) => event.attrs?.[key] ?? null, onEndTag: (fn) => ends.push(fn) })
        for (const text of event.chunks || []) handler?.text?.({ text })
        for (const end of ends) end()
      }
    }
    return response
  }
}

export function binding(time = clock()) {
  const store = storage()
  const object = new SiteCheckCounters({ storage: store }, {}, time)
  return {
    store, object,
    idFromName: (name) => { assert.equal(name, 'global'); return 'global' },
    get: () => ({ fetch: (request, init) => object.fetch(new Request(request, init)) }),
  }
}
