import { test } from 'node:test'
import assert from 'node:assert/strict'
import { handle } from '../src/index.js'
import { DailyCap } from '../src/mcp.js'

const EVENTS = ['first_opened', 'first_audit_finished', 'free_limit']
const SYSTEMS = ['mac', 'windows', 'linux']
const DAY = /^t:[0-9]{4}-[0-9]{2}-[0-9]{2}:/
const noFetch = async () => { throw new Error('App counts must not fetch a site') }

function counter() {
  const stored = new Map(), writes = [], forwarded = []
  const cap = new DailyCap({ storage: {
    get: async (key) => stored.get(key),
    put: async (key, value) => { writes.push([key, value]); stored.set(key, value) },
    delete: async (key) => stored.delete(key),
    list: async ({ prefix }) => new Map([...stored].filter(([key]) => key.startsWith(prefix))),
  } })
  return { stored, writes, forwarded, cap, STATS_KEY: 'test-only-stats-key', DAILY_CAP: {
    idFromName: (name) => { assert.equal(name, 'global'); return name },
    get: () => ({ fetch: (url, init) => {
      forwarded.push([url, init])
      return cap.fetch(new Request(url, init))
    } }),
  } }
}

const request = (query = 'e=first_opened&v=1.3.161&os=mac', init) =>
  new Request(`https://mcp.docketseo.app/app-event?${query}`, init)

async function emptyResponse(response, status = 204) {
  assert.equal(response.status, status)
  assert.equal(response.headers.get('Cache-Control'), 'no-store')
  assert.equal(await response.text(), '')
  assert.equal(response.headers.get('Set-Cookie'), null)
  assert.equal(response.headers.get('Vary'), null)
  for (const [name] of response.headers) assert.ok(!name.startsWith('access-control-'))
}

test('each event and system increments only daily event, version and system tallies', async () => {
  for (const event of EVENTS) for (const os of SYSTEMS) {
    const env = counter()
    for (let n = 1; n <= 2; n++) {
      await emptyResponse(await handle(request(`e=${event}&v=1.3.161&os=${os}`), noFetch, env))
      assert.deepEqual([...env.stored].map(([key, value]) => [key.replace(DAY, ''), value]).sort(),
        [[`app:${event}`, n], [`app:${event}:1.3.161`, n], [`app:${event}:${os}`, n]].sort())
    }
    assert.ok([...env.stored.keys()].every((key) => DAY.test(key)))
  }
})

for (const query of [
  '', 'v=1.3.161&os=mac', 'e=&v=1.3.161&os=mac',
  'e=unknown&v=1.3.161&os=mac', 'e=FIRST_OPENED&v=1.3.161&os=mac',
  'e=first_opened%0A&v=1.3.161&os=mac',
  'e=first_opened&os=mac', 'e=first_opened&v=&os=mac',
  ...['1.3', '1.3.161.0', '1000.3.161', '1.1000.161', '1.3.1000', '-1.3.161',
    '1x3x161', 'v1.3.161', '1.3.161-beta', '%201.3.161', '1.3.161%0A', '1.3.161%0D%0A',
    '%EF%BC%91.3.161'].map((version) => `e=first_opened&v=${version}&os=mac`),
  'e=first_opened&v=1.3.161', 'e=first_opened&v=1.3.161&os=',
  ...['Mac', 'darwin', 'win32', 'android', 'linux%0A'].map((os) => `e=first_opened&v=1.3.161&os=${os}`),
  'e=first_opened&e=free_limit&v=1.3.161&os=mac',
  'e=first_opened&v=1.3.161&v=2.0.0&os=mac',
  'e=first_opened&v=1.3.161&os=mac&os=linux',
]) test(`invalid query counts nothing: ${query || 'empty'}`, async () => {
  const env = counter()
  await emptyResponse(await handle(request(query), noFetch, env))
  assert.deepEqual(env.writes, [])
  assert.deepEqual(env.forwarded, [])
})

test('version boundaries allow one to three ASCII digits per part', async () => {
  for (const version of ['0.0.0', '999.999.999', '001.02.3']) {
    const env = counter()
    await emptyResponse(await handle(request(`e=first_opened&v=${version}&os=mac`), noFetch, env))
    assert.equal(env.stored.size, 3)
    assert.ok([...env.stored.keys()].some((key) => key.endsWith(`:app:first_opened:${version}`)))
  }
})

test('POST and all other non-GET methods return 405 without counting or CORS', async () => {
  for (const method of ['POST', 'PUT', 'PATCH', 'DELETE', 'HEAD', 'OPTIONS']) {
    const env = counter()
    const response = await handle(request(undefined, { method, headers: { Origin: 'https://other.example' } }), noFetch, env)
    await emptyResponse(response, 405)
    assert.equal(response.headers.get('Allow'), 'GET')
    assert.deepEqual(env.writes, [])
  }
})

test('ignores Origin and extra query parameters; forwards only validated tally keys, no request data', async () => {
  for (const origin of [undefined, 'https://docketseo.app', 'https://other.example', 'null']) {
    const env = counter()
    const headers = { 'CF-Connecting-IP': '192.0.2.17', 'User-Agent': 'private-agent-marker',
      Cookie: 'private-cookie-marker', Authorization: 'private-key-marker', Referer: 'https://private.example/report' }
    if (origin) headers.Origin = origin
    await emptyResponse(await handle(request('e=first_opened&v=1.3.161&os=mac&url=https://private.example/&id=private-id-marker',
      { headers }), noFetch, env))
    assert.equal(env.writes.length, 3)
    assert.deepEqual(env.forwarded, [
      ['https://cap.invalid/tally?k=app%3Afirst_opened', undefined],
      ['https://cap.invalid/tally?k=app%3Afirst_opened%3A1.3.161', undefined],
      ['https://cap.invalid/tally?k=app%3Afirst_opened%3Amac', undefined],
    ])
    assert.ok(env.writes.every(([, value]) => value === 1))
  }
})

test('reuses the limiter binding without storing an IP in the fallback cache', async () => {
  const env = counter(), limited = [], cacheWrites = []
  env.CHECK_LIMITER = { limit: async ({ key }) => { limited.push(key); return { success: false } } }
  const store = { get: async () => 0, put: async (...args) => cacheWrites.push(args) }
  await emptyResponse(await handle(request(undefined, { headers: { 'CF-Connecting-IP': '192.0.2.17' } }), noFetch, env, store))
  assert.deepEqual(limited, ['192.0.2.17'])
  assert.deepEqual(env.writes, [])
  assert.deepEqual(cacheWrites, [])
  delete env.CHECK_LIMITER
  await emptyResponse(await handle(request(undefined, { headers: { 'CF-Connecting-IP': '192.0.2.17' } }), noFetch, env, store))
  assert.equal(env.stored.size, 3)
  assert.deepEqual(cacheWrites, [])
})

test('missing or failed tally storage still returns the same 204', async () => {
  await emptyResponse(await handle(request(), noFetch, {}))
  await emptyResponse(await handle(request(), noFetch, { DAILY_CAP: {
    idFromName: () => 'global', get: () => ({ fetch: async () => { throw new Error('storage unavailable') } }),
  } }))
})

test('an allowed, missing-IP or failed limiter still acknowledges and counts without the IP cache', async () => {
  for (const mode of ['allowed', 'missing-IP', 'failed']) {
    const env = counter(), limited = []
    env.CHECK_LIMITER = { limit: async ({ key }) => {
      limited.push(key)
      if (mode === 'failed') throw new Error('limiter unavailable')
      return { success: true }
    } }
    const headers = mode === 'missing-IP' ? {} : { 'CF-Connecting-IP': '192.0.2.17' }
    await emptyResponse(await handle(request(undefined, { headers }), noFetch, env))
    assert.equal(env.stored.size, 3)
    assert.deepEqual(limited, mode === 'missing-IP' ? [] : ['192.0.2.17'])
  }
})

test('app counts appear with MCP outcomes only behind STATS_KEY', async () => {
  const env = counter()
  await handle(request(), noFetch, env)
  await env.cap.fetch(new Request('https://cap.invalid/tally?k=check_page_seo:ok'))
  const statsRequest = (headers) => new Request('https://mcp.docketseo.app/mcp/stats', { headers })
  for (const headers of [{}, { 'X-Stats-Key': 'wrong' }]) {
    assert.equal((await handle(statsRequest(headers), noFetch, env)).status, 404)
  }
  const stats = await (await handle(statsRequest({ 'X-Stats-Key': env.STATS_KEY }), noFetch, env)).json()
  assert.deepEqual(stats.outcomes, { 'app:first_opened': 1, 'app:first_opened:1.3.161': 1,
    'app:first_opened:mac': 1, 'check_page_seo:ok': 1 })
})

test('the tally store rejects arbitrary app keys instead of truncating or storing them', async () => {
  const env = counter()
  for (const key of ['app:unknown', 'app:first_opened:unknown', 'app:first_opened:1.2',
    'app:first_opened:mac:192.0.2.17', 'app:first_opened:1.3.161:mac',
    'app:first_opened\n', 'app:first_opened:1.3.161\n', 'app:first_opened:mac\n',
    'app:first_opened:mac' + ' '.repeat(100)]) {
    const response = await env.cap.fetch(new Request(`https://cap.invalid/tally?k=${encodeURIComponent(key)}`))
    assert.equal(response.status, 400, key)
  }
  assert.deepEqual(env.writes, [])
})
