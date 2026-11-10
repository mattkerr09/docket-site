import { test } from 'node:test'
import assert from 'node:assert/strict'
import worker, { handle } from '../src/index.js'
import { BASE } from '../src/site-brand.js'
import { deps, fetcher, cache, clock, binding } from './fakes.mjs'
import { COUNTER_TIMEOUT_MS, CACHE_TIMEOUT_MS } from '../src/limits.js'

const request = (address = 'public.com/path?private=yes', origin = BASE, ip = '192.0.2.41') => new Request(`https://worker.invalid/site-check?url=${encodeURIComponent(address)}`, {
  headers: { ...(origin ? { Origin: origin } : {}), ...(ip ? { 'CF-Connecting-IP': ip } : {}), Cookie: 'visitor=secret', Authorization: 'Basic secret' },
})
const setup = (over = {}) => {
  const time = clock()
  const counters = binding(time)
  return { env: { SITE_CHECK_COUNTERS: counters }, runtime: deps({ fetch: fetcher(), cache: cache(), clock: time, ...over }), counters }
}

test('route returns the exact summary fields with no cookies and no-store', async () => {
  const { env, runtime } = setup()
  const response = await handle(request(), env, runtime)
  assert.equal(response.status, 200)
  assert.equal(response.headers.get('Cache-Control'), 'no-store')
  assert.equal(response.headers.get('Access-Control-Allow-Origin'), BASE)
  assert.equal(response.headers.get('Access-Control-Allow-Credentials'), null)
  assert.equal(response.headers.get('Set-Cookie'), null)
  const r = await response.json()
  assert.deepEqual(Object.keys(r).sort(), ['site', 'pages_checked', 'truncated', 'blocked_by_robots', 'issues', 'fine', 'robots', 'checked_at', 'took_ms', 'from_cache'].sort())
  assert.equal(r.site, 'https://public.com')
  assert.equal(r.from_cache, false)
  assert.equal(typeof worker.fetch, 'function')
})

test('only our Origin is allowed, including preflight, and bad addresses are 400', async () => {
  const { env, runtime } = setup({ fetch: async () => { assert.fail('no fetch allowed') } })
  for (const origin of ['https://evil.com', null, 'null', 'https://www.checkengineseo.com']) {
    const r = await handle(request('public.com', origin), env, runtime)
    assert.equal(r.status, 403)
    assert.deepEqual(Object.keys(await r.json()).sort(), ['error', 'message'])
  }
  const preflight = await handle(new Request('https://worker.invalid/site-check', { method: 'OPTIONS', headers: { Origin: BASE } }), env, runtime)
  assert.equal(preflight.status, 204)
  assert.equal(preflight.headers.get('Access-Control-Allow-Methods'), 'GET')
  assert.equal((await handle(request('localhost'), env, runtime)).status, 400)
  assert.equal((await handle(new Request('https://worker.invalid/other', { headers: { Origin: BASE } }), env, runtime)).status, 404)
})

test('kill switch runs before origin, limiter, DNS, cache or target fetch', async () => {
  const fail = () => { assert.fail('disabled checker touched a dependency') }
  const response = await handle(request('public.com', 'https://evil.com'), { SITE_CHECK_DISABLED: '1', SITE_CHECK_COUNTERS: { get: fail } }, { fetch: fail, resolve: fail, cache: { match: fail } })
  assert.equal(response.status, 503)
  assert.equal((await response.json()).error, 'disabled')
})

test('counter errors, missing bindings and malformed allow responses refuse before target/cache access', async () => {
  for (const counter of [undefined, { idFromName() { throw new Error('down') } },
    { idFromName: () => 'global', get: () => ({ fetch: async () => { throw new Error('down') } }) },
    { idFromName: () => 'global', get: () => ({ fetch: async () => new Response('{}') }) },
    { idFromName: () => 'global', get: () => ({ fetch: async () => new Response('{"allowed":true}') }) }]) {
    const fail = () => { assert.fail('fail-closed limiter must prevent work') }
    const response = await handle(request(), { SITE_CHECK_COUNTERS: counter }, deps({ fetch: fail, cache: { match: fail }, resolve: fail }))
    assert.equal(response.status, 503)
    assert.deepEqual(Object.keys(await response.json()).sort(), ['error', 'message'])
  }
})

test('limit denial still applies to a cached result', async () => {
  const { env, runtime } = setup()
  assert.equal((await handle(request(), env, runtime)).status, 200)
  runtime.fetch = () => { assert.fail('cached/limited request fetched') }
  const r = await handle(request(), env, runtime)
  assert.equal(r.status, 429)
})

test('one-hour cache stores summary only, keyed by a hash of normalised origin, with counters only elsewhere', async () => {
  const { env, runtime, counters } = setup()
  const response = await handle(request(), env, runtime)
  const first = await response.json()
  assert.equal(runtime.cache.writes.length, 1)
  const [key, stored] = runtime.cache.writes[0]
  assert.match(key, /^https:\/\/summary\.site-check\.invalid\/[a-f0-9]{64}$/)
  assert.equal(stored.headers.get('Cache-Control'), 'public, max-age=3600')
  assert.deepEqual(await stored.json(), first)
  runtime.clock.advance(60000)
  runtime.fetch = () => { assert.fail('cache hit fetched a target') }
  const second = await (await handle(request('https://www.public.com/different?other=private', BASE, '192.0.2.42'), env, runtime)).json()
  assert.equal(second.from_cache, true)
  assert.equal(second.pages_checked, first.pages_checked)
  const persisted = JSON.stringify([...counters.store.rows]) + key
  for (const secret of ['192.0.2.41', 'public.com', 'private=yes', 'visitor=secret', 'Basic secret', 'CheckEngineBot']) assert.ok(!persisted.includes(secret), secret)
  assert.equal(runtime.cache.rows.size, 1)
})

test('an expired cache summary is ignored even when the fake cache does not expire it', async () => {
  const { env, runtime } = setup()
  await handle(request(), env, runtime)
  runtime.clock.advance(3600001)
  let calls = 0
  runtime.fetch = fetcher()
  runtime.extract = async () => { calls++; return { titles: [], metas: {}, h1s: [], canonicals: [], jsonld: [], links: [], words: 0 } }
  const second = await (await handle(request('public.com', BASE, '192.0.2.42'), env, runtime)).json()
  assert.equal(second.from_cache, false)
  assert.ok(calls > 0)
})

test('DNS failure returns bad address, stores no summary, and releases visitor lease', async () => {
  const { env, runtime, counters } = setup({ resolve: async () => [] })
  const response = await handle(request('does-not-resolve.com'), env, runtime)
  assert.equal(response.status, 400)
  assert.equal(runtime.cache.writes.length, 0)
  assert.ok([...counters.store.rows].filter(([k]) => k.includes(':v:')).every(([, v]) => !v.token))
})

test('release failure returns a plain fail-closed error', async () => {
  const { env, runtime, counters } = setup()
  const original = counters.object.fetch.bind(counters.object)
  counters.object.fetch = (r) => new URL(r.url).pathname === '/release' ? Promise.reject(new Error('down')) : original(r)
  const response = await handle(request(), env, runtime)
  assert.equal(response.status, 503)
  assert.deepEqual(Object.keys(await response.json()).sort(), ['error', 'message'])
})

test('no checked addresses, visitor data or response bodies are logged', async () => {
  const saved = { ...console }
  const calls = []
  for (const name of ['log', 'error', 'warn', 'info', 'debug']) console[name] = (...args) => calls.push(args)
  try {
    const { env, runtime } = setup()
    await handle(request(), env, runtime)
    runtime.clock.advance(60000)
    runtime.fetch = async () => { throw new Error('PRIVATE request detail') }
    await handle(request('otherpublic.com', BASE, '192.0.2.42'), env, runtime)
    assert.deepEqual(calls, [])
  } finally { Object.assign(console, saved) }
})

test('a stalled counter RPC fails closed on the fake clock without touching the target', async () => {
  const { env, runtime } = setup()
  env.SITE_CHECK_COUNTERS.get = () => ({ fetch: () => new Promise(() => {}) })
  runtime.fetch = () => { assert.fail('stalled limiter allowed a fetch') }
  const pending = handle(request(), env, runtime)
  runtime.clock.advance(COUNTER_TIMEOUT_MS)
  const response = await pending
  assert.equal(response.status, 503)
  assert.equal(runtime.clock.timers.size, 0)
})

test('cache failures and stalls never bypass the counters or keep a visitor active forever', async () => {
  for (const stalls of [false, true]) {
    const { env, runtime, counters } = setup()
    let entered = false
    runtime.cache = { match: () => {
      entered = true
      if (stalls) return new Promise(() => {})
      throw new Error('cache down')
    }, put: async () => { throw new Error('cache down') } }
    const pending = handle(request(), env, runtime)
    for (let i = 0; i < 100 && !entered; i++) await new Promise((resolve) => setImmediate(resolve))
    assert.equal(entered, true)
    if (stalls) runtime.clock.advance(CACHE_TIMEOUT_MS)
    const response = await pending
    assert.equal(response.status, 200)
    assert.equal([...counters.store.rows].find(([k]) => k.includes(':g'))[1], 1)
    assert.ok([...counters.store.rows].filter(([k]) => k.includes(':v:')).every(([, v]) => !v.token))
    assert.equal(runtime.clock.timers.size, 0)
  }
})

test('a reservation from yesterday cannot start a crawl after midnight', async () => {
  const { env, runtime } = setup()
  runtime.clock.advance(Date.parse('2026-11-10T23:59:59.500Z') - runtime.clock.now())
  runtime.cache.match = async () => { runtime.clock.advance(501); return undefined }
  runtime.fetch = () => { assert.fail('old reservation fetched in a new day') }
  const response = await handle(request(), env, runtime)
  assert.equal(response.status, 503)
})
