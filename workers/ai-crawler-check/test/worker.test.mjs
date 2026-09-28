// node --test workers/ai-crawler-check/test/
import { test } from 'node:test'
import assert from 'node:assert/strict'
import { ALLOWED_ORIGIN, USER_AGENT, agentsFrom, handle, siteFrom, unsafeHost } from '../src/index.js'

/** A fake network: maps URL -> {status, body, headers}. Records every request. */
function net(routes) {
  const seen = []
  const fetchImpl = async (url, init) => {
    seen.push({ url, init })
    const r = routes[url]
    if (!r) throw new Error('unreachable')
    return new Response(r.body ?? '', { status: r.status ?? 200, headers: r.headers ?? { 'Content-Type': 'text/plain' } })
  }
  return { seen, fetchImpl }
}

const req = (qs, origin = ALLOWED_ORIGIN, method = 'GET') =>
  new Request(`https://ai-crawler-check.example.workers.dev/check?${qs}`,
    { method, headers: origin ? { Origin: origin } : {} })

test('unsafe hosts are refused in every spelling', () => {
  for (const h of ['localhost', '127.0.0.1', '2130706433', '0x7f000001', '0177.0.0.1', '0x7f.1',
    '10.0.0.1', '[::1]', '::1', 'intranet', 'printer.local', 'db.internal', 'x.home.arpa', 'metadata']) {
    assert.ok(unsafeHost(h), `${h} should be refused`)
  }
  for (const h of ['docketseo.app', 'www.example.co.uk', 'a-b.io', '123.com']) {
    assert.equal(unsafeHost(h), null, `${h} should be allowed`)
  }
})

test('what a person types becomes a safe URL, or a plain error', () => {
  assert.equal(siteFrom('docketseo.app').origin, 'https://docketseo.app')
  assert.equal(siteFrom('http://example.com/a/b').pathname, '/a/b')
  for (const bad of ['', 'ftp://example.com', 'https://u:p@example.com', 'https://example.com:8080',
    'http://169.254.169.254/latest', 'https://localhost', 'javascript:alert(1)']) {
    assert.throws(() => siteFrom(bad), undefined, bad)
  }
})

test('crawler names are validated and capped', () => {
  assert.deepEqual(agentsFrom('GPTBot, OAI-SearchBot,gptbot,bad name,<x>,'), ['GPTBot', 'OAI-SearchBot'])
  assert.equal(agentsFrom(Array.from({ length: 60 }, (_, i) => `Bot${'x'.repeat(i % 5)}${String.fromCharCode(97 + (i % 26))}`).join(',')).length <= 40, true)
})

test('CORS answers docketseo.app and refuses every other origin', async () => {
  const { fetchImpl } = net({ 'https://example.com/robots.txt': { body: 'User-agent: *\nAllow: /' } })
  const ok = await handle(req('url=example.com&agents=GPTBot'), fetchImpl)
  assert.equal(ok.status, 200)
  assert.equal(ok.headers.get('Access-Control-Allow-Origin'), ALLOWED_ORIGIN)
  const evil = await handle(req('url=example.com&agents=GPTBot', 'https://evil.example'), fetchImpl)
  assert.equal(evil.status, 403)
  assert.equal(evil.headers.get('Access-Control-Allow-Origin'), null)
})

test('only /robots.txt on the given host is fetched, and the checker names itself', async () => {
  const { seen, fetchImpl } = net({ 'https://example.com/robots.txt': { body: 'User-agent: GPTBot\nDisallow: /' } })
  const res = await (await handle(req('url=https://example.com/some/page%3Fx&agents=GPTBot,OAI-SearchBot'), fetchImpl)).json()
  assert.deepEqual(seen.map((s) => s.url), ['https://example.com/robots.txt'])
  assert.equal(seen[0].init.headers['User-Agent'], USER_AGENT)
  assert.equal(seen[0].init.redirect, 'manual')
  assert.equal(res.results[0].allowed, false)
  assert.equal(res.results[0].named, true)
  assert.equal(res.results[1].allowed, true)
})

test('RFC 9309 status rules: 4xx allows everyone, 5xx and no answer block everyone', async () => {
  for (const [status, allowed, state] of [[404, true, 'unavailable'], [410, true, 'unavailable'],
    [503, false, 'unreachable'], [500, false, 'unreachable'], [429, false, 'unreachable']]) {
    const { fetchImpl } = net({ 'https://example.com/robots.txt': { status, body: 'x' } })
    const res = await (await handle(req('url=example.com&agents=GPTBot'), fetchImpl)).json()
    assert.equal(res.state, state, `status ${status}`)
    assert.equal(res.results[0].allowed, allowed, `status ${status}`)
  }
  const { fetchImpl } = net({})
  const down = await (await handle(req('url=example.com&agents=GPTBot'), fetchImpl)).json()
  assert.equal(down.state, 'unreachable')
  assert.equal(down.results[0].allowed, false)
})

test('a redirect to a private address is not followed', async () => {
  const { seen, fetchImpl } = net({
    'https://example.com/robots.txt': { status: 301, headers: { Location: 'http://127.0.0.1/robots.txt' } },
  })
  const res = await (await handle(req('url=example.com&agents=GPTBot'), fetchImpl)).json()
  assert.equal(res.state, 'blocked')
  assert.equal(seen.length, 1)
})

test('redirects are followed to five hops, then treated as no file', async () => {
  const routes = {}
  for (let i = 0; i < 7; i++) {
    routes[`https://example.com/r${i}`] = { status: 302, headers: { Location: `/r${i + 1}` } }
  }
  routes['https://example.com/robots.txt'] = { status: 301, headers: { Location: '/r0' } }
  const { seen, fetchImpl } = net(routes)
  const res = await (await handle(req('url=example.com&agents=GPTBot'), fetchImpl)).json()
  assert.equal(res.state, 'unavailable')
  assert.equal(seen.length, 6)
  const ok = net({
    'https://example.com/robots.txt': { status: 301, headers: { Location: 'https://www.example.com/robots.txt' } },
    'https://www.example.com/robots.txt': { body: 'User-agent: *\nDisallow: /' },
  })
  const r2 = await (await handle(req('url=example.com&agents=GPTBot'), ok.fetchImpl)).json()
  assert.equal(r2.state, 'parsed')
  assert.equal(r2.results[0].allowed, false)
})

test('an HTML page served as robots.txt is flagged, and a huge file is capped', async () => {
  const { fetchImpl } = net({ 'https://example.com/robots.txt': { body: '<!doctype html><title>Not found</title>', headers: { 'Content-Type': 'text/html' } } })
  const res = await (await handle(req('url=example.com&agents=GPTBot'), fetchImpl)).json()
  assert.match(res.warnings[0], /web page/)
  const big = 'User-agent: *\nDisallow: /late\n'.padEnd(600 * 1024, '#') + '\nUser-agent: GPTBot\nDisallow: /'
  const n2 = net({ 'https://example.com/robots.txt': { body: big } })
  const r2 = await (await handle(req('url=example.com&agents=GPTBot'), n2.fetchImpl)).json()
  assert.equal(r2.bytes, 512 * 1024)
  assert.match(r2.warnings[0], /512 KiB/)
  assert.equal(r2.results[0].allowed, true, 'the GPTBot group past 512 KiB is not read')
})

test('bad input gets a 400 with a sentence, other paths 404, other methods 405', async () => {
  const { fetchImpl } = net({})
  const bad = await handle(req('url=printer.local&agents=GPTBot'), fetchImpl)
  assert.equal(bad.status, 400)
  assert.match((await bad.json()).error, /private or reserved/)
  assert.equal((await handle(req('url=example.com'), fetchImpl)).status, 400)
  assert.equal((await handle(new Request('https://w.dev/other'), fetchImpl)).status, 404)
  assert.equal((await handle(req('url=example.com&agents=GPTBot', ALLOWED_ORIGIN, 'POST'), fetchImpl)).status, 405)
})
