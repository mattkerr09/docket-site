// node --test workers/ai-crawler-check/test/
import { test } from 'node:test'
import assert from 'node:assert/strict'
import { ALLOWED_ORIGIN, handle } from '../src/index.js'
import { MAX_TRACE } from '../src/trace.js'

function net(routes) {
  const seen = []
  const fetchImpl = async (url, init) => {
    seen.push({ url, init })
    const r = routes[url]
    if (!r) throw new Error('unreachable')
    return new Response(r.body ?? '', { status: r.status ?? 200, headers: r.headers ?? { 'Content-Type': 'text/html' } })
  }
  return { seen, fetchImpl }
}
const get = (qs) => new Request(`https://w.example.workers.dev/trace?${qs}`, { headers: { Origin: ALLOWED_ORIGIN } })
const run = async (qs, routes) => { const n = net(routes); const r = await handle(get(qs), n.fetchImpl, {}, null); return { j: await r.json(), seen: n.seen } }
const levels = (list) => Object.fromEntries(list.map((f) => [f.label, f.level]))

test('a two-hop chain from http is reported as Docket reports it, with each status code', async () => {
  const { j, seen } = await run('url=http://shop.com/', {
    'http://shop.com/': { status: 301, headers: { Location: 'https://shop.com/' } },
    'https://shop.com/': { status: 302, headers: { Location: 'https://www.shop.com/' } },
    'https://www.shop.com/': { status: 200, headers: { 'Content-Type': 'text/html', 'Set-Cookie': 'sid=secret', 'Strict-Transport-Security': 'max-age=63072000' } },
  })
  assert.deepEqual(j.hops.map((h) => h.status), [301, 302])
  assert.equal(j.final.url, 'https://www.shop.com/')
  const r = levels(j.redirects)
  assert.equal(r['2 redirects before the page'], 'warning')
  assert.equal(r['1 temporary redirect (302)'], 'note')
  assert.equal(r['http:// is sent to HTTPS'], 'ok')
  assert.ok(!JSON.stringify(j).includes('secret'), 'a cookie value must never be returned')
  assert.equal(levels(j.headers)['HSTS is set'], 'ok')
  assert.equal(levels(j.headers)['Missing 2 baseline security headers'], 'note')
  assert.equal(seen[0].init.redirect, 'manual')
})

test('a loop is a problem and is caught on the first repeat', async () => {
  const { j, seen } = await run('url=https://a.com/', {
    'https://a.com/': { status: 301, headers: { Location: 'https://www.a.com/' } },
    'https://www.a.com/': { status: 301, headers: { Location: 'https://a.com/' } },
  })
  assert.equal(j.loop, 'https://a.com/')
  assert.equal(levels(j.redirects)['Redirect loop'], 'problem')
  assert.equal(seen.length, 2)
})

test('more than the limit stops and says so', async () => {
  const routes = {}
  for (let i = 0; i <= MAX_TRACE + 1; i++) routes[`https://x.com/${i}`] = { status: 301, headers: { Location: `https://x.com/${i + 1}` } }
  const { j } = await run('url=https://x.com/0', routes)
  assert.equal(j.tooMany, true)
  assert.equal(levels(j.redirects)[`More than ${MAX_TRACE} redirects`], 'problem')
})

test('no HSTS is a warning, except on a TLD the browsers preload', async () => {
  const plain = await run('url=https://b.com/', { 'https://b.com/': { status: 200, headers: { 'Content-Type': 'text/html', 'X-Content-Type-Options': 'nosniff', 'Referrer-Policy': 'no-referrer' } } })
  assert.equal(levels(plain.j.headers)['No HSTS header'], 'warning')
  assert.equal(levels(plain.j.headers)['X-Content-Type-Options and Referrer-Policy are set'], 'ok')
  const app = await run('url=https://b.app/', { 'https://b.app/': { status: 200 } })
  assert.equal(levels(app.j.headers)['No HSTS header needed: .app is HTTPS-only in every major browser'], 'ok')
})

test('a page left on http is a problem and its security headers are not judged', async () => {
  const { j } = await run('url=http://c.com/', { 'http://c.com/': { status: 200, headers: { 'Content-Type': 'text/html', 'X-Robots-Tag': 'noindex' } } })
  assert.equal(levels(j.redirects)['The page ends up on plain http'], 'problem')
  const h = levels(j.headers)
  assert.equal(h['Served over plain http'], 'problem')
  assert.equal(h['The server asks search engines not to index this page'], 'problem')
  assert.equal(h['No HSTS header'], undefined)
})

test('a redirect to a private address is not followed', async () => {
  const { j, seen } = await run('url=https://d.com/', { 'https://d.com/': { status: 302, headers: { Location: 'http://127.0.0.1/admin' } } })
  assert.match(j.error, /will not follow/)
  assert.equal(seen.length, 1)
})
