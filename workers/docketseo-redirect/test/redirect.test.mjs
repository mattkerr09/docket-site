import { beforeEach, test } from 'node:test'
import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import defaultWorker, { MODE, makeHandler } from '../src/index.js'

const worker = makeHandler('redirect')

const destination = 'https://checkengineseo.com'
const retained = ['/updater.json', '/offer.json', '/data/knowledge.json', '/bot', '/bot/', '/assets/docket-sample-report.pdf']
const isRetained = (path) => retained.includes(path) || path.startsWith('/updates/') || path.startsWith('/bot/')
const requestFor = (path, init) => new Request(`https://docketseo.app${path}`, init)
const json = async (path) => JSON.parse(await readFile(new URL(path, import.meta.url), 'utf8'))

// Every test replaces the real fetch, including tests that must never fetch.
beforeEach((t) => {
  t.mock.method(globalThis, 'fetch', () => assert.fail('Unexpected fetch'))
})

const redirects = await json('../../../data/redirect-pages.json')
const oldPaths = Object.keys(redirects).flatMap((path) => [`/${path}`, `/${path.replace(/index\.html$/, '')}`])
let inventory
try {
  inventory = await json('../../../site/_redirect-map.json')
} catch (error) {
  if (error.code !== 'ENOENT') throw error
  inventory = Object.keys(await json('../../../data/page-lastmod.json')).map((path) => `/${path}`)
}
const pagePaths = [...new Set(inventory
  .filter((path) => path.endsWith('/') || path.endsWith('index.html'))
  .map((path) => path.replace(/index\.html$/, '')))]
  .filter((path) => !isRetained(path))
  .sort()
assert.ok(pagePaths.length >= 40, 'The page inventory must supply at least 40 redirect paths')
const sample = Array.from({ length: 40 }, (_, index) => pagePaths[Math.floor(index * pagePaths.length / 40)])

for (const path of new Set([...oldPaths, ...sample])) {
  if (isRetained(path)) continue
  test(`old page redirects at the same path: ${path}`, async () => {
    const response = await worker.fetch(requestFor(path))
    assert.equal(response.status, 301)
    assert.equal(response.headers.get('Location'), `${destination}${path}`)
    assert.equal(await response.text(), '')
  })
}

for (const path of [
  '/', '/download/', '/download', '/pricing/', '/vs/screaming-frog-alternative/',
  '/buy/', '/score-card', '/updates', '/updates-old/file', '/updates%2Ffile',
  '/botany/', '/bot%2Fdetails', '/updater.json/', '/UPDATER.json', '/__redirect-health/',
  '/Download/UPPER', '/a//b/', '//other.example/path',
  '/pricing/?utm_source=old&tag=one&tag=two',
  '/vs/a%2fb/%E2%9C%93?url=https%3A%2F%2Fexample.com%2Fa%3Fb%3D1&plus=a+b&blank=',
  '/%3F%23%25/%20?q=%2f%2F%26%3D', '/download/?',
]) {
  for (const host of ['docketseo.app', 'www.docketseo.app']) {
    test(`preserves the URL suffix on ${host}: ${path}`, async () => {
      const response = await worker.fetch(new Request(`https://${host}${path}`))
      assert.equal(response.status, 301)
      assert.equal(response.headers.get('Location'), `${destination}${path}`)
    })
  }
}

test('HEAD pages redirect without a body', async () => {
  const response = await worker.fetch(requestFor('/pricing/?from=app', { method: 'HEAD' }))
  assert.equal(response.status, 301)
  assert.equal(response.headers.get('Location'), `${destination}/pricing/?from=app`)
  assert.equal(response.body, null)
})

test('HTTP requests redirect straight to the new HTTPS host', async () => {
  const response = await worker.fetch(new Request('http://www.docketseo.app/download?keep=%2F'))
  assert.equal(response.status, 301)
  assert.equal(response.headers.get('Location'), `${destination}/download?keep=%2F`)
})

for (const path of [...retained, '/bot/details', '/bot/sub/path/', '/updates/', '/updates/Docket-1.zip', '/updates/windows/Docket-2.exe']) {
  test(`proxies the origin bytes and headers: ${path}`, async (t) => {
    const bytes = new Uint8Array([0, 255, 13, 10, 128, 65])
    const originHeaders = {
      'Content-Type': 'application/octet-stream',
      'Content-Length': String(bytes.length),
      ETag: '"release-1"',
      'Cache-Control': 'public, max-age=120',
      'Last-Modified': 'Mon, 09 Nov 2026 00:00:00 GMT',
      'Accept-Ranges': 'bytes',
    }
    const mock = t.mock.method(globalThis, 'fetch', async (input, init) => {
      assert.equal(input, `${destination}${path}?v=1&file=a%2Fb`)
      assert.equal(init.method, 'GET')
      assert.equal(init.redirect, 'follow')
      return new Response(bytes, { headers: originHeaders })
    })
    const response = await worker.fetch(requestFor(`${path}?v=1&file=a%2Fb`))
    assert.equal(mock.mock.callCount(), 1)
    assert.equal(response.status, 200)
    assert.equal(response.headers.get('Location'), null)
    assert.equal(response.headers.get('X-Served-By'), 'docketseo-redirect')
    for (const [name, value] of Object.entries(originHeaders)) assert.equal(response.headers.get(name), value)
    assert.deepEqual(new Uint8Array(await response.arrayBuffer()), bytes)
  })
}

test('www retained paths proxy to the new apex', async (t) => {
  t.mock.method(globalThis, 'fetch', async (input) => {
    assert.equal(input, `${destination}/offer.json?old=www`)
    return new Response('offer')
  })
  const response = await worker.fetch(new Request('https://www.docketseo.app/offer.json?old=www'))
  assert.equal(response.status, 200)
  assert.equal(await response.text(), 'offer')
})

test('retained requests keep an empty query marker', async (t) => {
  t.mock.method(globalThis, 'fetch', async (input) => {
    assert.equal(input, `${destination}/updater.json?`)
    return new Response('feed')
  })
  const response = await worker.fetch(requestFor('/updater.json?'))
  assert.equal(response.status, 200)
  assert.equal(await response.text(), 'feed')
})

test('Range and conditional headers reach the origin and 206 stays intact', async (t) => {
  const headers = {
    Range: 'bytes=2-4',
    'If-Range': '"release-1"',
    'If-None-Match': '"old-release"',
    'If-Modified-Since': 'Sun, 08 Nov 2026 00:00:00 GMT',
    'If-Match': '"release-1"',
    'If-Unmodified-Since': 'Mon, 09 Nov 2026 00:00:00 GMT',
    Accept: 'application/octet-stream',
  }
  t.mock.method(globalThis, 'fetch', async (input, init) => {
    assert.equal(input, `${destination}/updates/Docket-1.zip`)
    assert.equal(init.method, 'GET')
    assert.equal(init.redirect, 'follow')
    for (const [name, value] of Object.entries(headers)) assert.equal(init.headers.get(name), value)
    for (const name of ['Accept-Encoding', 'Cookie', 'Authorization', 'Host']) assert.equal(init.headers.get(name), null)
    return new Response(new Uint8Array([2, 3, 4]), {
      status: 206,
      statusText: 'Partial Content',
      headers: { 'Content-Range': 'bytes 2-4/10', 'Content-Length': '3', ETag: '"release-1"' },
    })
  })
  const response = await worker.fetch(requestFor('/updates/Docket-1.zip', {
    headers: { ...headers, 'Accept-Encoding': 'gzip', Cookie: 'private=1', Authorization: 'Bearer fake', Host: 'docketseo.app' },
  }))
  assert.equal(response.status, 206)
  assert.equal(response.statusText, 'Partial Content')
  assert.equal(response.headers.get('Content-Range'), 'bytes 2-4/10')
  assert.equal(response.headers.get('Content-Length'), '3')
  assert.equal(response.headers.get('ETag'), '"release-1"')
  assert.equal(response.headers.get('Location'), null)
  assert.equal(response.headers.get('X-Served-By'), 'docketseo-redirect')
  assert.deepEqual(new Uint8Array(await response.arrayBuffer()), new Uint8Array([2, 3, 4]))
})

test('a 304 conditional response keeps its status, headers and empty body', async (t) => {
  t.mock.method(globalThis, 'fetch', async (input, init) => {
    assert.equal(init.headers.get('If-None-Match'), '"feed-1"')
    return new Response(null, { status: 304, headers: { ETag: '"feed-1"', 'Cache-Control': 'max-age=60' } })
  })
  const response = await worker.fetch(requestFor('/updater.json', { headers: { 'If-None-Match': '"feed-1"' } }))
  assert.equal(response.status, 304)
  assert.equal(response.body, null)
  assert.equal(response.headers.get('ETag'), '"feed-1"')
  assert.equal(response.headers.get('Cache-Control'), 'max-age=60')
  assert.equal(response.headers.get('Location'), null)
  assert.equal(response.headers.get('X-Served-By'), 'docketseo-redirect')
})

test('HEAD is forwarded and keeps Content-Length without a body', async (t) => {
  t.mock.method(globalThis, 'fetch', async (input, init) => {
    assert.equal(init.method, 'HEAD')
    return new Response(null, { headers: { 'Content-Length': '9876543210' } })
  })
  const response = await worker.fetch(requestFor('/updates/Docket-2.exe', { method: 'HEAD' }))
  assert.equal(response.status, 200)
  assert.equal(response.headers.get('Content-Length'), '9876543210')
  assert.equal(response.body, null)
})

test('update streams are returned before any bytes are available', async (t) => {
  let controller
  let reads = 0
  const body = new ReadableStream({
    start(value) { controller = value },
    pull() { reads += 1 },
  }, { highWaterMark: 0 })
  const origin = new Response(body, { headers: { 'Content-Length': '4' } })
  for (const method of ['arrayBuffer', 'blob', 'bytes', 'formData', 'json', 'text', 'clone']) {
    origin[method] = () => assert.fail(`Worker must not call ${method}`)
  }
  t.mock.method(globalThis, 'fetch', async () => origin)
  const response = await worker.fetch(requestFor('/updates/large.zip'))
  assert.equal(response.body, body)
  assert.equal(body.locked, false)
  assert.equal(reads, 0)
  assert.equal(response.headers.get('Content-Length'), '4')
  controller.enqueue(new Uint8Array([0, 1, 2, 255]))
  controller.close()
  assert.deepEqual(new Uint8Array(await response.arrayBuffer()), new Uint8Array([0, 1, 2, 255]))
})

test('encoded origin bytes retain Content-Encoding and Content-Length', async (t) => {
  const compressed = new Uint8Array([31, 139, 8, 0])
  t.mock.method(globalThis, 'fetch', async () => new Response(compressed, {
    headers: { 'Content-Encoding': 'gzip', 'Content-Length': '4', Vary: 'Accept-Encoding' },
  }))
  const response = await worker.fetch(requestFor('/updates/compressed.gz'))
  assert.equal(response.status, 200)
  assert.equal(response.headers.get('Content-Encoding'), 'gzip')
  assert.equal(response.headers.get('Content-Length'), '4')
  assert.equal(response.headers.get('Vary'), 'Accept-Encoding')
  assert.deepEqual(new Uint8Array(await response.arrayBuffer()), compressed)
})

for (const status of [404, 416]) {
  test(`preserves origin status ${status}`, async (t) => {
    t.mock.method(globalThis, 'fetch', async () => new Response('origin detail', { status }))
    const response = await worker.fetch(requestFor('/updates/missing.zip'))
    assert.equal(response.status, status)
    assert.equal(await response.text(), 'origin detail')
    assert.equal(response.headers.get('X-Served-By'), 'docketseo-redirect')
  })
}

for (const failure of ['network', 500, 502, 503, 599, 301, 302, 307, 308]) {
  test(`origin failure ${failure} returns 502 without a redirect`, async (t) => {
    t.mock.method(globalThis, 'fetch', async () => {
      if (failure === 'network') throw new Error('offline')
      return new Response('origin error', { status: failure, headers: { Location: 'https://other.example/' } })
    })
    const response = await worker.fetch(requestFor('/updater.json'))
    assert.equal(response.status, 502)
    assert.equal(response.headers.get('Location'), null)
    assert.equal(response.headers.get('Content-Type'), 'text/plain; charset=utf-8')
    assert.equal(response.headers.get('Cache-Control'), 'no-store')
    assert.equal(await response.text(), 'Origin unavailable\n')
  })
}

test('HEAD origin failure has no body', async (t) => {
  t.mock.method(globalThis, 'fetch', async () => { throw new Error('offline') })
  const response = await worker.fetch(requestFor('/offer.json', { method: 'HEAD' }))
  assert.equal(response.status, 502)
  assert.equal(response.body, null)
  assert.equal(response.headers.get('Location'), null)
})

for (const path of ['/', '/updater.json', '/updates/Docket-1.zip', '/__redirect-health']) {
  for (const method of ['POST', 'PUT', 'DELETE', 'OPTIONS']) {
    test(`${method} ${path} is rejected without fetching`, async () => {
      const response = await worker.fetch(requestFor(path, { method }))
      assert.equal(response.status, 405)
      assert.equal(response.headers.get('Allow'), path === '/__redirect-health' ? 'GET' : 'GET, HEAD')
      assert.equal(response.headers.get('Location'), null)
    })
  }
}

test('health is a read-only local GET', async () => {
  for (const host of ['docketseo.app', 'www.docketseo.app']) {
    const response = await worker.fetch(new Request(`https://${host}/__redirect-health?probe=1`))
    assert.equal(response.status, 200)
    assert.equal(await response.text(), 'ok')
    assert.equal(response.headers.get('Content-Type'), 'text/plain; charset=utf-8')
    assert.equal(response.headers.get('Cache-Control'), 'no-store')
    assert.equal(response.headers.get('X-Mode'), 'redirect')
  }
  const head = await worker.fetch(requestFor('/__redirect-health', { method: 'HEAD' }))
  assert.equal(head.status, 405)
  assert.equal(head.headers.get('Allow'), 'GET')
})

test('the committed mode is one known mode, and passthrough forwards the original request and response unchanged', async (t) => {
  assert.ok(['passthrough', 'fallback', 'redirect'].includes(MODE))
  const source = await readFile(new URL('../src/index.js', import.meta.url), 'utf8')
  assert.equal(source.match(/^export const MODE = '(passthrough|fallback|redirect)'$/gm)?.length, 1)
  const passthrough = makeHandler('passthrough')
  for (const path of ['/', '/updater.json', '/updates/release/file.exe', '/__redirect-health']) {
    for (const method of ['GET', 'HEAD', 'POST', 'PUT', 'DELETE', 'OPTIONS']) {
      const request = requestFor(`${path}?keep=%2f`, {
        method,
        headers: { 'X-Original': 'keep' },
        ...(method === 'POST' ? { body: 'original body' } : {}),
      })
      const origin = new Response(null, { status: 204, headers: { 'X-Original-Response': 'keep' } })
      const mock = t.mock.method(globalThis, 'fetch', async (...args) => {
        assert.deepEqual(args, [request])
        assert.equal(args[0], request)
        if (method === 'POST') assert.equal(await args[0].text(), 'original body')
        return origin
      })
      assert.equal(await passthrough.fetch(request), origin)
      assert.equal(mock.mock.callCount(), 1)
    }
  }
})
