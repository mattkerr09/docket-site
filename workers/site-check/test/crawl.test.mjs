import { test } from 'node:test'
import assert from 'node:assert/strict'
import { crawl, readCapped } from '../src/crawl.js'
import { canonical, siteFrom, unsafeHost, publicAddress, resolvePublic } from '../src/safety.js'
import * as L from '../src/limits.js'
import { clock, deps, fetcher, html, text, perfect } from './fakes.mjs'

const start = new URL('https://public.com/')
const pageCalls = (f) => f.calls.filter(({ url, init }) => init.method === 'GET' && !/\/(robots\.txt|sitemap\.xml)$/.test(new URL(url).pathname))

test('all crawl, request, check, cache and counter bounds are explicit constants', () => {
  assert.equal(L.MAX_PAGES, 25)
  assert.equal(L.MAX_PAGE_BYTES, 1024 * 1024)
  assert.equal(L.PAGE_TIMEOUT_MS, 8000)
  assert.equal(L.DEADLINE_MS, 30000)
  assert.equal(L.MAX_REDIRECTS, 5)
  assert.equal(L.CONCURRENCY, 4)
  assert.ok(L.REQUEST_PAUSE_MS > 0)
  assert.equal(L.MAX_URLS_PER_PATH, 3)
  assert.equal(L.MAX_DISCOVERED_URLS, 250)
  assert.equal(L.MAX_ADDRESS_LENGTH, 2048)
  assert.equal(L.MAX_ROBOTS_RULES, 256)
  assert.equal(L.MAX_ROBOTS_PATTERN_LENGTH, 512)
  assert.equal(L.MAX_ROBOTS_WILDCARDS, 1)
  assert.equal(L.VISITOR_DAILY_CAP, 5)
  assert.equal(L.HOST_DAILY_CAP, 3)
  assert.equal(L.HOST_INTERVAL_MS, 60000)
  assert.equal(L.GLOBAL_DAILY_CAP, 1500)
  assert.equal(L.CACHE_TTL_S, 3600)
  assert.equal(L.DAY_MS, 86400000)
  assert.equal(L.LEASE_MS, 45000)
  assert.equal(L.PURGE_BATCH, 128)
  assert.equal(L.MAX_SUMMARY_BYTES, 32768)
  assert.equal(L.MAX_COUNTER_BYTES, 1024)
  assert.equal(L.COUNTER_TIMEOUT_MS, 2000)
  assert.equal(L.CACHE_TIMEOUT_MS, 1000)
  assert.equal(L.DNS_MAX_BYTES, 65536)
  assert.equal(L.MAX_ISSUES, 8)
  assert.equal(L.MAX_FINE, 5)
  assert.equal(L.MAX_EXAMPLES, 3)
  assert.equal(L.THIN_WORDS, 100)
  assert.equal(L.SLOW_TTFB_MS, 1500)
  assert.equal(L.TITLE_MIN, 25)
  assert.equal(L.TITLE_MAX, 65)
  assert.equal(L.USER_AGENT, 'CheckEngineBot/1.0 (+https://checkengineseo.com/bot/)')
})

test('breadth first, canonical deduplication, query cap and 25-page cap', async () => {
  const f = fetcher()
  const links = ['/a', '/b', '/a#part', '/q?b=2&a=1', '/q?a=1&b=2', '/q?a=2', '/q?a=3', '/q?a=4', ...Array.from({ length: 40 }, (_, i) => `/p${i}`)]
  const r = await crawl(start, deps({ fetch: f, extract: async (body) => perfect({ links: body === '/' ? links : ['/deep'] }) }))
  assert.equal(r.pages_checked, 25)
  assert.equal(r.truncated, true)
  const paths = pageCalls(f).map(({ url }) => new URL(url).pathname + new URL(url).search)
  assert.deepEqual(paths.slice(0, 4), ['/', '/a', '/b', '/q?b=2&a=1'])
  assert.equal(paths.filter((p) => p.startsWith('/q?')).length, 3)
  assert.equal(paths.includes('/deep'), false)
  assert.equal(new Set(paths).size, 25)
})

test('only apex and www are one host, other subdomains and credentials refused', async () => {
  const f = fetcher()
  await crawl(start, deps({ fetch: f, extract: async () => perfect({ links: [
    'https://www.public.com/a', 'https://public.com/a', 'https://other.com/', 'https://api.public.com/',
    'https://user:pass@public.com/secret', 'https://public.com:8080/no', 'ftp://public.com/a',
  ] }) }))
  assert.deepEqual(pageCalls(f).map(({ url }) => url), ['https://public.com/', 'https://www.public.com/a'])
  assert.equal(canonical('https://www.public.com/a#x'), canonical('https://public.com/a'))
})

test('specific and wildcard robots rules both apply, and denied paths are never fetched', async () => {
  const f = fetcher({}, { robots: 'User-agent: CheckEngineBot\nAllow: /\nDisallow: /named\nUser-agent: *\nDisallow: /private' })
  const r = await crawl(start, deps({ fetch: f, extract: async () => perfect({ links: ['/named', '/private', '/ok'] }) }))
  assert.deepEqual(pageCalls(f).map(({ url }) => new URL(url).pathname), ['/', '/ok'])
  assert.equal(r.blocked_by_robots, 2)
  assert.ok(r.issues.some((i) => /blocked by robots.txt/i.test(i.label)))
})

for (const robots of ['User-agent: *\nDisallow: /', 'User-agent: CheckEngineBot\nDisallow: /']) {
  test('robots disallow-all stops before any other resource', async () => {
    const f = fetcher({}, { robots })
    const r = await crawl(start, deps({ fetch: f }))
    assert.equal(f.calls.length, 1)
    assert.equal(r.pages_checked, 0)
    assert.match(r.message, /this site asked not to be checked/i)
  })
}

for (const status of [401, 403, 429]) {
  test(`first page ${status} stops without sitemap or links`, async () => {
    const f = fetcher({ '/': new Response('', { status }) })
    const r = await crawl(start, deps({ fetch: f }))
    assert.equal(f.calls.length, 2)
    assert.equal(r.pages_checked, 0)
    assert.match(r.message, /this site asked not to be checked/i)
  })
}

test('unreadable, oversized or forbidden robots fail closed', async () => {
  for (const response of [text('', 503), text('', 403), html('<html>challenge</html>'), text('x'.repeat(L.MAX_PAGE_BYTES + 1))]) {
    const f = fetcher({})
    const run = async (url, init) => new URL(url).pathname === '/robots.txt' ? response.clone() : f(url, init)
    const r = await crawl(start, deps({ fetch: run }))
    assert.equal(r.pages_checked, 0)
    assert.equal(f.calls.length, 0)
    assert.ok(r.message)
  }
})

test('missing robots and sitemap are counted, a sitemap is checked, not just a header', async () => {
  const f = fetcher()
  const run = async (url, init) => ['/robots.txt', '/sitemap.xml'].includes(new URL(url).pathname) ? text('', 404) : f(url, init)
  const r = await crawl(start, deps({ fetch: run }))
  assert.deepEqual(r.robots, { found: false, sitemap_found: false })
  assert.ok(r.issues.some((i) => i.id === 'missing_robots'))
  assert.ok(r.issues.some((i) => i.id === 'missing_sitemap'))
})

test('robots is read for www separately before its pages and redirects', async () => {
  const f = fetcher()
  const run = async (url, init) => {
    if (url === 'https://www.public.com/robots.txt') return text('User-agent: *\nDisallow: /')
    return f(url, init)
  }
  const r = await crawl(start, deps({ fetch: run, extract: async () => perfect({ links: ['https://www.public.com/private'] }) }))
  assert.equal(pageCalls(f).length, 1)
  assert.equal(r.blocked_by_robots, 1)
})

test('redirects are manual, same-host, robot-checked, deduplicated and capped', async () => {
  for (const target of ['https://other.com/', 'http://127.0.0.1/', 'https://public.com:8080/', 'https://u:p@public.com/']) {
    const f = fetcher({ '/': new Response(null, { status: 302, headers: { Location: target } }) })
    const r = await crawl(start, deps({ fetch: f }))
    assert.equal(pageCalls(f).length, 1)
    assert.equal(r.pages_checked, 0)
  }
  const pages = Object.fromEntries(Array.from({ length: 8 }, (_, i) => [`/r${i}`, new Response(null, { status: 302, headers: { Location: `/r${i + 1}` } })]))
  const f = fetcher(pages)
  await crawl(new URL('/r0', start), deps({ fetch: f }))
  assert.equal(pageCalls(f).length, L.MAX_REDIRECTS + 1)
  const denied = fetcher({ '/': new Response(null, { status: 302, headers: { Location: '/private' } }) }, { robots: 'User-agent: *\nDisallow: /private' })
  const r = await crawl(start, deps({ fetch: denied }))
  assert.equal(pageCalls(denied).length, 1)
  assert.equal(r.blocked_by_robots, 1)
})

test('only HTML bodies count as pages, and error status pages are measured separately', async () => {
  const f = fetcher({ '/pdf': new Response('%PDF', { headers: { 'Content-Type': 'application/pdf' } }), '/error': text('', 500) })
  const r = await crawl(start, deps({ fetch: f, extract: async () => perfect({ links: ['/pdf', '/error'] }) }))
  assert.equal(r.pages_checked, 1)
  assert.ok(r.issues.some((i) => i.id === 'http_errors' && i.count === 1 && i.of === 3))
})

test('the byte cap cancels a fake stream at exactly 1 MiB, without reading another chunk', async () => {
  let reads = 0
  let cancelled = false
  const response = { body: { getReader: () => ({
    async read() { reads++; return { done: false, value: new Uint8Array(65536).fill(65) } },
    async cancel() { cancelled = true },
  }) } }
  const result = await readCapped(response, L.MAX_PAGE_BYTES)
  assert.equal(result.bytes, L.MAX_PAGE_BYTES)
  assert.equal(result.truncated, true)
  assert.equal(reads, 16)
  assert.equal(cancelled, true)
})

test('partial bodies never become missing-tag findings or sources of links', async () => {
  const f = fetcher({ '/': html('x'.repeat(L.MAX_PAGE_BYTES + 5)) })
  const r = await crawl(start, deps({ fetch: f }))
  assert.equal(r.pages_checked, 0)
  assert.equal(r.truncated, true)
  assert.ok(!r.issues.some((i) => i.id === 'missing_title'))
})

test('8-second timeout covers a stalled body, not just response headers', async () => {
  const time = clock()
  const f = fetcher({ '/': () => new Response(new ReadableStream({ start() {} }), { headers: { 'Content-Type': 'text/html' } }) })
  const pending = crawl(start, deps({ fetch: f, clock: time }))
  for (let i = 0; i < 30; i++) await Promise.resolve()
  time.advance(L.PAGE_TIMEOUT_MS)
  const r = await pending
  assert.equal(r.pages_checked, 0)
  assert.equal(time.timers.size, 0)
})

test('overall fake-clock deadline stops new fetches and truncates, including at midnight', async () => {
  for (const startTime of [undefined, Date.parse('2026-11-10T23:59:58Z')]) {
    const time = clock(startTime)
    const f = fetcher({}, { time, delay: 2000 })
    const r = await crawl(start, deps({ fetch: f, clock: time, extract: async () => perfect({ links: Array.from({ length: 40 }, (_, i) => `/p${i}`) }) }))
    assert.equal(r.truncated, true)
    assert.ok(f.calls.every(({ at }) => at < Math.min((startTime ?? Date.parse('2026-11-10T14:00:00Z')) + L.DEADLINE_MS, Date.parse('2026-11-11T00:00:00Z'))))
  }
})

test('concurrency is at most four and actual request starts have a polite gap', async () => {
  let active = 0
  let peak = 0
  const time = clock()
  const f = fetcher()
  const releases = []
  const starts = []
  const run = async (url, init) => {
    starts.push(time.now())
    if (/\/p\d+$/.test(url)) {
      active++; peak = Math.max(peak, active)
      await new Promise((resolve) => releases.push(() => { active--; resolve() }))
    }
    return f(url, init)
  }
  let done = false
  const pending = crawl(start, deps({ clock: time, fetch: run, extract: async () => perfect({ links: Array.from({ length: 12 }, (_, i) => `/p${i}`) }) })).then((r) => { done = true; return r })
  for (let i = 0; i < 1000 && !done; i++) {
    await Promise.resolve()
    if (releases.length >= L.CONCURRENCY || (releases.length && i > 500)) releases.splice(0).forEach((fn) => fn())
  }
  await pending
  assert.equal(peak, 4)
  for (let i = 1; i < starts.length; i++) assert.ok(starts[i] - starts[i - 1] >= L.REQUEST_PAUSE_MS)
})

test('address parser refuses every literal-IP notation and internal host family', () => {
  for (const address of ['http://127.0.0.1', 'http://10.0.0.1', 'http://169.254.169.254', 'http://[::1]', 'http://[::ffff:127.0.0.1]',
    'http://2130706433', 'http://0x7f000001', 'http://0177.0.0.1', 'localhost', 'a.local', 'a.internal', 'a.localhost', 'a.home.arpa',
    'http://user:pass@public.com', 'https://public.com:444', 'file:///tmp/a', 'ftp://public.com/a', 'https://bad..com', 'https://-bad.com']) {
    assert.throws(() => siteFrom(address), address)
  }
  assert.ok(unsafeHost('[::1]'))
  assert.equal(siteFrom('public.com/path').href, 'https://public.com/path')
  assert.throws(() => siteFrom(`public.com/${'a'.repeat(L.MAX_ADDRESS_LENGTH)}`))
  assert.throws(() => siteFrom(`public.com/${'é'.repeat(500)}`))
})

test('DNS validation refuses nothing, private/mixed answers, bad records, and resolution errors', async () => {
  for (const addresses of [[], ['127.0.0.1'], ['93.184.216.34', '10.1.1.1'], ['::1'], ['fe80::1'], ['fc00::1'], ['::ffff:7f00:1'], ['garbage']]) {
    await assert.rejects(() => resolvePublic('public.com', async () => addresses))
  }
  await assert.rejects(() => resolvePublic('does-not-resolve.com', async () => { throw new Error('NXDOMAIN') }))
  for (const address of ['0.0.0.0', '100.64.0.1', '192.0.0.1', '192.168.0.1', '198.18.0.1', '224.0.0.1', '2001:db8::1', '2002:7f00:1::', '64:ff9b::7f00:1']) assert.equal(publicAddress(address), false, address)
  for (const address of ['93.184.216.34', '2606:4700:4700::1111']) assert.equal(publicAddress(address), true, address)
  let fetched = false
  await assert.rejects(() => crawl(start, deps({ resolve: async () => [], fetch: async () => { fetched = true } })))
  assert.equal(fetched, false)
})

test('an apex-to-www redirect works and a queued final address is read only once', async () => {
  const f = fetcher({ 'https://public.com/': new Response(null, { status: 301, headers: { Location: 'https://www.public.com/' } }) })
  const r = await crawl(start, deps({ fetch: f, extract: async () => perfect({ links: ['https://public.com/', '/a', '/alias'] }) }))
  assert.equal(r.pages_checked, 3)
  assert.deepEqual(pageCalls(f).slice(0, 2).map(({ url }) => url), ['https://public.com/', 'https://www.public.com/'])
  assert.ok(f.calls.some(({ url }) => url === 'https://www.public.com/robots.txt'))
  const aliases = fetcher({ '/alias': new Response(null, { status: 302, headers: { Location: '/a' } }) })
  const other = await crawl(start, deps({ fetch: aliases, extract: async () => perfect({ links: ['/alias', '/a'] }) }))
  assert.equal(other.pages_checked, 2)
  assert.equal(pageCalls(aliases).filter(({ url }) => new URL(url).pathname === '/a').length, 1)
})

test('the per-path query cap also applies during redirect chains', async () => {
  const f = fetcher({ '/': (_u) => html('/'), '/r': (u) => new Response(null, { status: 302, headers: { Location: `/r?n=${Number(u.searchParams.get('n') || 0) + 1}` } }) })
  const r = await crawl(new URL('/r?n=0', start), deps({ fetch: f }))
  assert.equal(pageCalls(f).length, 3)
  assert.equal(r.truncated, true)
})

test('sitemap and HTTP probes also obey robots, and unknown probes do not become missing-file claims', async () => {
  const f = fetcher({}, { robots: 'User-agent: *\nDisallow: /sitemap.xml' })
  const run = (url, init) => url === 'http://public.com/robots.txt' ? text('User-agent: *\nDisallow: /') : f(url, init)
  const r = await crawl(start, deps({ fetch: run }))
  assert.ok(!f.calls.some(({ url }) => new URL(url).pathname === '/sitemap.xml'))
  assert.ok(!f.calls.some(({ init }) => init.method === 'HEAD'))
  assert.ok(!r.issues.some((i) => ['missing_sitemap', 'http_no_https'].includes(i.id)))
  assert.ok(!r.fine.some((i) => ['missing_sitemap', 'http_no_https'].includes(i.id)))
})

test('HTTP upgrade is checked with HEAD, and a real same-site HTTPS redirect passes', async () => {
  for (const upgrades of [true, false]) {
    const f = fetcher()
    const run = (url, init) => {
      if (url === 'http://public.com/' && init.method === 'HEAD' && upgrades) return new Response(null, { status: 301, headers: { Location: 'https://www.public.com/' } })
      return f(url, init)
    }
    const r = await crawl(start, deps({ fetch: run }))
    assert.equal(r.issues.some((i) => i.id === 'http_no_https'), !upgrades)
  }
})

test('a stalled fetch is aborted at eight seconds and cannot start a late redirect', async () => {
  const time = clock()
  let aborted = false
  let complete
  const f = fetcher({ '/': (_u, init) => {
    init.signal.addEventListener('abort', () => { aborted = true })
    return new Promise((resolve) => { complete = resolve })
  } })
  const pending = crawl(start, deps({ fetch: f, clock: time }))
  for (let i = 0; i < 100 && !complete; i++) await Promise.resolve()
  assert.ok(complete)
  time.advance(L.PAGE_TIMEOUT_MS)
  const r = await pending
  assert.equal(aborted, true)
  assert.equal(r.truncated, true)
  complete(new Response(null, { status: 302, headers: { Location: '/late' } }))
  for (let i = 0; i < 20; i++) await Promise.resolve()
  assert.equal(pageCalls(f).length, 1)
  assert.equal(time.timers.size, 0)
})

test('deadline aborts all in-flight reads and returns pages already read', async () => {
  const time = clock()
  let stalled = 0
  let cancelled = 0
  const f = fetcher({ '/slow': () => {
    stalled++
    return new Response(new ReadableStream({ start() {}, cancel() { cancelled++ } }), { headers: { 'Content-Type': 'text/html' } })
  } })
  const pending = crawl(start, deps({ fetch: f, clock: time, extract: async () => perfect({ links: ['/slow?a=1', '/slow?a=2', '/slow?a=3'] }) }))
  for (let i = 0; i < 200 && stalled < 3; i++) await Promise.resolve()
  assert.equal(stalled, 3)
  time.advance(L.DEADLINE_MS)
  const r = await pending
  assert.equal(r.pages_checked, 1)
  assert.equal(r.truncated, true)
  assert.equal(cancelled, 3)
  assert.equal(time.timers.size, 0)
})

test('the byte cap also cuts and copies one oversized stream chunk', async () => {
  let reads = 0
  const r = await readCapped({ body: { getReader: () => ({
    read: async () => { reads++; return { value: new Uint8Array(L.MAX_PAGE_BYTES * 2).fill(65), done: false } },
    cancel: async () => {},
  }) } }, L.MAX_PAGE_BYTES)
  assert.equal(reads, 1)
  assert.equal(r.text.length, L.MAX_PAGE_BYTES)
  assert.equal(r.truncated, true)
})

test('malformed or undecodable robots rules refuse, even when ignoring them would allow a page', async () => {
  for (const robots of ['User-agent *\nDisallow: /', 'Disallow: /', 'User-agent: *\nDisallow: /\ufffd']) {
    const f = fetcher({}, { robots })
    const r = await crawl(start, deps({ fetch: f }))
    assert.equal(f.calls.length, 1)
    assert.equal(r.pages_checked, 0)
    assert.match(r.message, /could not be read safely/)
  }
})

test('an empty site gives no invented page findings and a perfect 25-page site has no issues', async () => {
  const empty = fetcher({ '/': text('not HTML') })
  const r = await crawl(start, deps({ fetch: empty }))
  assert.equal(r.pages_checked, 0)
  assert.deepEqual(r.issues, [])
  assert.deepEqual(r.fine, [])
  assert.equal(empty.calls.length, 2)
  const f = fetcher()
  const run = (url, init) => url === 'http://public.com/' && init.method === 'HEAD'
    ? new Response(null, { status: 301, headers: { Location: 'https://public.com/' } }) : f(url, init)
  const clean = await crawl(start, deps({ fetch: run, extract: async (body) => perfect({
    titles: [`A useful and unique page title for ${body}`],
    metas: { ...perfect().metas, description: [`An original description for ${body}`] },
    links: body === '/' ? Array.from({ length: 24 }, (_, i) => `/p${i}`) : [],
  }) }))
  assert.equal(clean.pages_checked, 25)
  assert.equal(clean.truncated, false)
  assert.deepEqual(clean.issues, [])
  assert.equal(clean.fine.length, 5)
  assert.ok(clean.fine.every((item) => item.count === 25 && item.of === 25))
})

test('HTTP error denominators exclude paths that robots stopped before any page request', async () => {
  const f = fetcher({ '/error': text('', 500) }, { robots: 'User-agent: *\nDisallow: /blocked' })
  const r = await crawl(start, deps({ fetch: f, extract: async () => perfect({ links: ['/blocked/1', '/blocked/2', '/error'] }) }))
  const error = r.issues.find((item) => item.id === 'http_errors')
  assert.equal(error.count, 1)
  assert.equal(error.of, 2)
  assert.equal(r.pages_checked, 1)
  assert.equal(r.blocked_by_robots, 2)
})

test('a merging redirect chain is still reported at its source path', async () => {
  const f = fetcher({
    '/alias': new Response(null, { status: 301, headers: { Location: '/step' } }),
    '/step': new Response(null, { status: 301, headers: { Location: '/final' } }),
  })
  const r = await crawl(start, deps({ fetch: f, extract: async () => perfect({ links: ['/alias', '/final'] }) }))
  assert.equal(r.pages_checked, 2)
  const chains = r.issues.find((item) => item.id === 'redirect_chains')
  assert.equal(chains.count, 1)
  assert.equal(chains.of, 3)
  assert.deepEqual(chains.examples, ['/alias'])
})

test('robots evaluator work is bounded before any potentially hostile regex runs', async () => {
  for (const rules of [
    'Disallow: /*a*a*a*a*a*b',
    `Disallow: /${'a'.repeat(L.MAX_ROBOTS_PATTERN_LENGTH)}`,
    Array.from({ length: L.MAX_ROBOTS_RULES + 1 }, (_, i) => `Disallow: /path${i}`).join('\n'),
  ]) {
    const f = fetcher({}, { robots: `User-agent: *\n${rules}` })
    const r = await crawl(start, deps({ fetch: f }))
    assert.equal(f.calls.length, 1)
    assert.equal(r.pages_checked, 0)
    assert.match(r.message, /rules could not be read safely/)
  }
})

test('a robots file found after an HTTP-to-HTTPS page redirect counts as found', async () => {
  const f = fetcher()
  const run = (url, init) => {
    if (url === 'http://public.com/robots.txt') return text('', 404)
    if (url === 'http://public.com/') return new Response(null, { status: 301, headers: { Location: 'https://public.com/' } })
    return f(url, init)
  }
  const r = await crawl(new URL('http://public.com/'), deps({ fetch: run }))
  assert.equal(r.pages_checked, 1)
  assert.equal(r.robots.found, true)
  assert.ok(!r.issues.some((item) => ['missing_robots', 'http_no_https'].includes(item.id)))
})

test('a truncated crawl keeps the HTTP upgrade finding measured on its first page', async () => {
  const time = clock()
  let stalled = false
  const f = fetcher({ '/slow': () => {
    stalled = true
    return new Response(new ReadableStream({ start() {} }), { headers: { 'Content-Type': 'text/html' } })
  } })
  const pending = crawl(new URL('http://public.com/'), deps({ fetch: f, clock: time, extract: async () => perfect({ links: ['/slow'] }) }))
  for (let i = 0; i < 200 && !stalled; i++) await Promise.resolve()
  assert.equal(stalled, true)
  time.advance(L.DEADLINE_MS)
  const r = await pending
  assert.equal(r.pages_checked, 1)
  assert.equal(r.truncated, true)
  assert.ok(r.issues.some((item) => item.id === 'http_no_https'))
})
