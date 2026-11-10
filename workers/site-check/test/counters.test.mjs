import { test } from 'node:test'
import assert from 'node:assert/strict'
import { digest, reserve, release } from '../src/counters.js'
import * as L from '../src/limits.js'
import { clock, binding, NOW } from './fakes.mjs'

const hash = (n) => n.toString(16).padStart(64, '0')
const acquire = async (b, visitor = hash(1), host = hash(2)) => {
  const response = await b.get().fetch('https://counter.invalid/reserve', { method: 'POST', body: JSON.stringify({ visitor, host }) })
  return { status: response.status, ...await response.json() }
}
const finish = async (b, r) => {
  const response = await b.get().fetch('https://counter.invalid/release', { method: 'POST', body: JSON.stringify({ visitor: r.visitor, token: r.token, day: r.day }) })
  assert.equal(response.status, 200)
}

test('visitor one at a time, daily five, with stale release protection', async () => {
  const time = clock()
  const b = binding(time)
  const first = await acquire(b)
  assert.equal(first.allowed, true)
  assert.equal((await acquire(b, hash(1), hash(3))).status, 429)
  await finish(b, first)
  const next = await acquire(b, hash(1), hash(3))
  await finish(b, first)
  assert.equal((await acquire(b, hash(1), hash(4))).status, 429)
  await finish(b, next)
  for (let i = 0; i < 3; i++) await finish(b, await acquire(b, hash(1), hash(i + 10)))
  assert.equal((await acquire(b, hash(1), hash(20))).status, 429)
  time.advance(L.DAY_MS)
  assert.equal((await acquire(b)).allowed, true)
  assert.ok([...b.store.rows.keys()].every((k) => !k.includes('2026-11-10')))
})

test('host one per minute and three per day, even across visitors', async () => {
  const time = clock()
  const b = binding(time)
  await finish(b, await acquire(b))
  assert.equal((await acquire(b, hash(3))).status, 429)
  for (let i = 0; i < 2; i++) {
    time.advance(L.HOST_INTERVAL_MS)
    await finish(b, await acquire(b, hash(i + 3)))
  }
  time.advance(L.HOST_INTERVAL_MS)
  assert.equal((await acquire(b, hash(5))).status, 429)
})

test('global cap is atomic, counts accepted checks only, and has the exact busy message', async () => {
  const b = binding()
  b.store.rows.set('d:2026-11-10:g', L.GLOBAL_DAILY_CAP - 1)
  const results = await Promise.all([acquire(b, hash(1), hash(2)), acquire(b, hash(3), hash(4))])
  assert.equal(results.filter((r) => r.allowed).length, 1)
  const denied = results.find((r) => !r.allowed)
  assert.equal(denied.status, 503)
  assert.equal(denied.error, 'busy')
  assert.equal(denied.message, 'The free checker is busy today. Try again tomorrow.')
  assert.equal(b.store.rows.get('d:2026-11-10:g'), 1500)
})

test('storage get, put, list, delete, transaction and alarm errors all fail closed', async () => {
  for (const method of ['get', 'put', 'list', 'delete', 'transaction', 'setAlarm']) {
    const b = binding()
    b.store.rows.set('d:2026-11-09:g', 1)
    b.store[method] = async () => { throw new Error('storage failed') }
    const r = await acquire(b)
    assert.equal(r.status, 503, method)
    assert.equal(r.allowed, undefined, method)
  }
})

test('alarm purges old dates and schedules the next UTC boundary', async () => {
  const time = clock()
  const b = binding(time)
  await acquire(b)
  assert.equal(await b.store.getAlarm(), Date.parse('2026-11-11T00:00:00Z'))
  time.advance(L.DAY_MS)
  await b.object.alarm()
  assert.equal(b.store.rows.size, 0)
})

test('only day keys with hashes and counters are stored, and invalid payloads write nothing', async () => {
  const b = binding()
  for (const body of [{ visitor: '192.0.2.1', host: 'public.com' }, { visitor: hash(1), host: hash(2), extra: 'secret' }]) {
    const response = await b.get().fetch('https://counter.invalid/reserve', { method: 'POST', body: JSON.stringify(body) })
    assert.equal(response.status, 400)
    assert.equal(b.store.writes.length, 0)
  }
  await acquire(b)
  assert.equal(b.store.rows.size, 3)
  for (const [key, value] of b.store.rows) {
    assert.match(key, /^d:2026-11-10:(g|[vh]:[a-f0-9]{64})$/)
    assert.ok(!JSON.stringify(value).includes('public.com'))
  }
})

test('hashes have date and fixed label separation, and missing identity refuses', async () => {
  assert.equal((await digest('a')).length, 64)
  const b = binding()
  const request = new Request('https://worker.invalid/', { headers: { 'CF-Connecting-IP': '192.0.2.1' } })
  const reservation = await reserve(request, 'public.com', { SITE_CHECK_COUNTERS: b }, clock())
  assert.equal(reservation.allowed, true)
  assert.notEqual(reservation.visitor, await digest('192.0.2.1'))
  await release(reservation, { SITE_CHECK_COUNTERS: b })
  await assert.rejects(() => reserve(new Request(request.url), 'public.com', { SITE_CHECK_COUNTERS: b }, clock()))
})

test('expired leases recover a crashed check and release cannot clear a later lease', async () => {
  const time = clock()
  const b = binding(time)
  const old = await acquire(b)
  time.advance(L.LEASE_MS)
  const fresh = await acquire(b, hash(1), hash(3))
  assert.equal(fresh.allowed, true)
  await finish(b, old)
  assert.equal((await acquire(b, hash(1), hash(4))).status, 429)
})

test('simultaneous visitors and target reservations cannot race past either cap', async () => {
  for (const visitorShared of [true, false]) {
    const b = binding()
    const r = await Promise.all([
      acquire(b, hash(1), hash(2)),
      acquire(b, visitorShared ? hash(1) : hash(3), visitorShared ? hash(4) : hash(2)),
    ])
    assert.equal(r.filter((item) => item.allowed).length, 1)
    assert.equal(r.find((item) => !item.allowed).status, 429)
    assert.equal(b.store.rows.get('d:2026-11-10:g'), 1)
  }
})

test('bad persisted visitor, host or global counters each refuse closed', async () => {
  for (const [key, value] of [
    ['d:2026-11-10:g', 'bad'],
    ['d:2026-11-10:g', null],
    [`d:2026-11-10:v:${hash(1)}`, null],
    [`d:2026-11-10:h:${hash(2)}`, null],
    [`d:2026-11-10:v:${hash(1)}`, { count: 'bad' }],
    [`d:2026-11-10:v:${hash(1)}`, { count: 0, token: '', until: NOW }],
    [`d:2026-11-10:h:${hash(2)}`, { count: 1, last: 'bad' }],
  ]) {
    const b = binding()
    b.store.rows.set(key, value)
    assert.equal((await acquire(b)).status, 503)
  }
})

test('alarm errors throw for runtime retry, and visitor hashes rotate at midnight', async () => {
  const time = clock()
  const b = binding(time)
  const req = new Request('https://worker.invalid/', { headers: { 'CF-Connecting-IP': '192.0.2.1' } })
  const first = await reserve(req, 'public.com', { SITE_CHECK_COUNTERS: b }, time)
  time.advance(L.DAY_MS)
  const next = await reserve(req, 'public.com', { SITE_CHECK_COUNTERS: b }, time)
  assert.notEqual(first.visitor, next.visitor)
  assert.ok([...b.store.rows.keys()].every((k) => k.includes('2026-11-11')))
  b.store.transaction = async () => { throw new Error('storage down') }
  await assert.rejects(() => b.object.alarm())
})
