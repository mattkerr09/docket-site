import { test } from 'node:test'
import assert from 'node:assert/strict'
import { dnsAddresses, resolvePublic, publicAddress } from '../src/safety.js'
import { DNS_MAX_BYTES } from '../src/limits.js'

const answer = (data) => new Response(JSON.stringify(data), { headers: { 'Content-Type': 'application/dns-json' } })

test('production DNS uses only the fixed HTTPS resolver, both families, and no request credentials', async () => {
  const calls = []
  const fetch = async (url, init) => {
    const u = new URL(url)
    calls.push(u)
    assert.equal(u.origin + u.pathname, 'https://cloudflare-dns.com/dns-query')
    assert.equal(u.searchParams.get('name'), 'public.com')
    assert.equal(init.credentials, 'omit')
    assert.equal(init.redirect, 'manual')
    assert.equal(init.cache, 'no-store')
    assert.deepEqual(Object.keys(init.headers), ['Accept'])
    return answer({ Status: 0, Answer: u.searchParams.get('type') === 'A'
      ? [{ type: 5, data: 'alias.public.com.' }, { type: 1, data: '93.184.216.34' }]
      : [{ type: 28, data: '2001:4860:4860::8888' }] })
  }
  assert.deepEqual(await dnsAddresses('public.com', fetch), ['93.184.216.34', '2001:4860:4860::8888'])
  assert.deepEqual(calls.map((u) => u.searchParams.get('type')), ['A', 'AAAA'])
})

test('DNS errors, redirects, truncation, incomplete answers and mixed private records refuse', async () => {
  for (const response of [answer({ Status: 3 }), answer({ Status: 0 }), answer({ Status: 0, TC: true }),
    answer({ Status: 0, Answer: [{ type: 1, data: '93.184.216.34' }, { type: 28, data: '::1' }] }),
    answer({ Status: 0, Answer: [{ type: 16, data: 'unexpected' }] }),
    new Response(null, { status: 301, headers: { Location: 'http://localhost/' } }),
    new Response('x'.repeat(DNS_MAX_BYTES + 1)), new Response('not JSON'),
  ]) {
    let calls = 0
    const fetch = async () => { calls++; return response.clone() }
    await assert.rejects(() => resolvePublic('public.com', (host) => dnsAddresses(host, fetch)))
    assert.ok(calls <= 2)
  }
})

test('both address families must be known, and valid public IPv6 remains supported', async () => {
  const fetch = async (url) => new URL(url).searchParams.get('type') === 'A'
    ? answer({ Status: 0, Answer: [{ type: 1, data: '93.184.216.34' }] })
    : answer({ Status: 2 })
  await assert.rejects(() => resolvePublic('public.com', (host) => dnsAddresses(host, fetch)))
  assert.equal(publicAddress('2001:4860:4860::8888'), true)
  assert.equal(publicAddress('2001:0:1234::1'), false)
  assert.equal(publicAddress('2001:20::1'), false)
})
