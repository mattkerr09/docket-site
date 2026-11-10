import { beforeEach, test } from 'node:test'
import assert from 'node:assert/strict'
import { makeHandler } from '../src/index.js'

const fallback = makeHandler('fallback')
const raw = 'https://raw.githubusercontent.com/mattkerr09/docket-site/gh-pages'
const requestFor = (path, init) => new Request(`https://docketseo.app${path}`, init)
const moving = 'Check Engine SEO (formerly Docket SEO) is moving to https://checkengineseo.com. Please try again in a few minutes.'

beforeEach((t) => {
  t.mock.method(globalThis, 'fetch', () => assert.fail('Unexpected fetch'))
})

for (const [path, rawPath, contentType] of [
  ['/updater.json', '/updater.json', 'application/json; charset=utf-8'],
  ['/offer.json', '/offer.json', 'application/json; charset=utf-8'],
  ['/data/knowledge.json', '/data/knowledge.json', 'application/json; charset=utf-8'],
  ['/bot', '/bot/index.html', 'text/html; charset=utf-8'],
  ['/bot/', '/bot/index.html', 'text/html; charset=utf-8'],
  ['/assets/docket-sample-report.pdf', '/assets/docket-sample-report.pdf', 'application/pdf'],
  ['/updates/1.0/Docket.tgz', '/updates/1.0/Docket.tgz', 'application/gzip'],
  ['/updates/2.0/Docket.exe', '/updates/2.0/Docket.exe', 'application/octet-stream'],
  ['/updates/', '/updates/index.html', 'text/html; charset=utf-8'],
  ['/updates/2.0/', '/updates/2.0/index.html', 'text/html; charset=utf-8'],
  ['/updates/2.0/archive.gz', '/updates/2.0/archive.gz', 'application/gzip'],
  ['/updates/2.0/unknown.zip', '/updates/2.0/unknown.zip', 'application/octet-stream'],
  ['/updates/2.0/no-extension', '/updates/2.0/no-extension', 'application/octet-stream'],
  ['/updates/2.0/file.constructor', '/updates/2.0/file.constructor', 'application/octet-stream'],
  ['/updates/2.0/FEED.JSON', '/updates/2.0/FEED.JSON', 'application/json; charset=utf-8'],
  ['/bot/details', '/bot/details', 'application/octet-stream'],
  ['/bot/sub/path/', '/bot/sub/path/index.html', 'text/html; charset=utf-8'],
]) {
  test(`fallback streams the raw file with its proper type: ${path}`, async (t) => {
    const bytes = new Uint8Array([0, 255, 13, 10, 128, 65])
    const origin = new Response(bytes, {
      headers: {
        'Content-Type': path.endsWith('.json') ? 'text/plain; charset=utf-8' : 'application/octet-stream',
        'Content-Length': String(bytes.length),
        'Cache-Control': 'max-age=9999',
        'Accept-Ranges': 'bytes',
        ETag: '"raw-release"',
        'Last-Modified': 'Mon, 09 Nov 2026 00:00:00 GMT',
        'X-Content-Type-Options': 'nosniff',
      },
    })
    const mock = t.mock.method(globalThis, 'fetch', async (input, init) => {
      assert.equal(input, `${raw}${rawPath}`)
      assert.equal(init.method, 'GET')
      assert.equal(init.redirect, 'follow')
      return origin
    })
    const response = await fallback.fetch(requestFor(path))
    assert.equal(mock.mock.callCount(), 1)
    assert.equal(response.status, 200)
    assert.equal(response.body, origin.body)
    assert.equal(response.headers.get('Content-Type'), contentType)
    assert.equal(response.headers.get('Content-Length'), String(bytes.length))
    assert.equal(response.headers.get('Cache-Control'), 'public, max-age=300')
    assert.equal(response.headers.get('Accept-Ranges'), 'bytes')
    assert.equal(response.headers.get('ETag'), '"raw-release"')
    assert.equal(response.headers.get('Last-Modified'), 'Mon, 09 Nov 2026 00:00:00 GMT')
    assert.equal(response.headers.get('X-Content-Type-Options'), 'nosniff')
    assert.equal(response.headers.get('X-Served-By'), 'docketseo-redirect-fallback')
    assert.equal(response.headers.get('Location'), null)
    assert.deepEqual(new Uint8Array(await response.arrayBuffer()), bytes)
  })
}

for (const suffix of ['?v=1&file=a%2Fb&tag=one&tag=two', '?', '?keep=%2f%2F&blank=']) {
  test(`fallback keeps the original query suffix: ${suffix}`, async (t) => {
    t.mock.method(globalThis, 'fetch', async (input) => {
      assert.equal(input, `${raw}/bot/index.html${suffix}`)
      return new Response('bot page')
    })
    const response = await fallback.fetch(new Request(`https://www.docketseo.app/bot${suffix}`))
    assert.equal(response.status, 200)
    assert.equal(await response.text(), 'bot page')
    assert.equal(response.headers.get('Location'), null)
  })
}

test('fallback forwards Range and conditional headers and keeps a 206 response', async (t) => {
  const headers = {
    Range: 'bytes=2-4',
    'If-Range': '"release-1"',
    'If-None-Match': '"old-release"',
    'If-Modified-Since': 'Sun, 08 Nov 2026 00:00:00 GMT',
  }
  t.mock.method(globalThis, 'fetch', async (input, init) => {
    assert.equal(input, `${raw}/updates/2.0/Docket.exe`)
    assert.equal(init.method, 'GET')
    assert.equal(init.redirect, 'follow')
    for (const [name, value] of Object.entries(headers)) assert.equal(init.headers.get(name), value)
    for (const name of ['Cookie', 'Authorization', 'Host', 'Accept-Encoding']) assert.equal(init.headers.get(name), null)
    return new Response(new Uint8Array([2, 3, 4]), {
      status: 206,
      statusText: 'Partial Content',
      headers: {
        'Content-Type': 'application/octet-stream',
        'Content-Range': 'bytes 2-4/10',
        'Content-Length': '3',
        'Accept-Ranges': 'bytes',
        ETag: '"release-1"',
        'Cache-Control': 'max-age=9999',
      },
    })
  })
  const response = await fallback.fetch(requestFor('/updates/2.0/Docket.exe', {
    headers: { ...headers, Cookie: 'private=1', Authorization: 'Bearer fake', Host: 'docketseo.app', 'Accept-Encoding': 'gzip' },
  }))
  assert.equal(response.status, 206)
  assert.equal(response.statusText, 'Partial Content')
  assert.equal(response.headers.get('Content-Range'), 'bytes 2-4/10')
  assert.equal(response.headers.get('Content-Length'), '3')
  assert.equal(response.headers.get('Accept-Ranges'), 'bytes')
  assert.equal(response.headers.get('ETag'), '"release-1"')
  assert.equal(response.headers.get('Cache-Control'), 'public, max-age=300')
  assert.equal(response.headers.get('Location'), null)
  assert.deepEqual(new Uint8Array(await response.arrayBuffer()), new Uint8Array([2, 3, 4]))
})

test('fallback keeps 304 status, ETag and an empty body', async (t) => {
  t.mock.method(globalThis, 'fetch', async (input, init) => {
    assert.equal(init.headers.get('If-None-Match'), '"feed-1"')
    return new Response(null, { status: 304, headers: { ETag: '"feed-1"', 'Cache-Control': 'max-age=9999' } })
  })
  const response = await fallback.fetch(requestFor('/updater.json', { headers: { 'If-None-Match': '"feed-1"' } }))
  assert.equal(response.status, 304)
  assert.equal(response.body, null)
  assert.equal(response.headers.get('ETag'), '"feed-1"')
  assert.equal(response.headers.get('Content-Type'), 'application/json; charset=utf-8')
  assert.equal(response.headers.get('Cache-Control'), 'public, max-age=300')
  assert.equal(response.headers.get('X-Served-By'), 'docketseo-redirect-fallback')
  assert.equal(response.headers.get('Location'), null)
})

for (const status of [404, 416]) {
  test(`fallback keeps raw status ${status} without a Location`, async (t) => {
    t.mock.method(globalThis, 'fetch', async () => new Response('raw detail', {
      status,
      headers: { Location: 'https://other.example/' },
    }))
    const response = await fallback.fetch(requestFor('/updates/2.0/missing.exe'))
    assert.equal(response.status, status)
    assert.equal(response.headers.get('Location'), null)
    assert.equal(response.headers.get('X-Served-By'), 'docketseo-redirect-fallback')
    assert.equal(await response.text(), 'raw detail')
  })
}

for (const failure of ['network', 500, 502, 503, 599, 301, 302, 307, 308]) {
  for (const method of ['GET', 'HEAD']) {
    test(`fallback ${method} failure ${failure} gives 502 with no Location`, async (t) => {
      t.mock.method(globalThis, 'fetch', async () => {
        if (failure === 'network') throw new Error('offline')
        return new Response(method === 'HEAD' ? null : 'raw failure', {
          status: failure,
          headers: { Location: 'https://other.example/' },
        })
      })
      const response = await fallback.fetch(requestFor('/offer.json', { method }))
      assert.equal(response.status, 502)
      assert.equal(response.headers.get('Location'), null)
      assert.equal(response.headers.get('Content-Type'), 'text/plain; charset=utf-8')
      assert.equal(response.headers.get('Cache-Control'), 'no-store')
      assert.equal(response.headers.get('X-Served-By'), 'docketseo-redirect-fallback')
      if (method === 'HEAD') assert.equal(response.body, null)
      assert.equal(await response.text(), method === 'HEAD' ? '' : 'Origin unavailable\n')
    })
  }
}

test('fallback asks fetch to follow raw redirects inside the Worker', async (t) => {
  // Model fetch's redirect option offline. A manual fetch would expose the 302.
  const mock = t.mock.method(globalThis, 'fetch', async (input, init) => {
    assert.equal(input, `${raw}/updater.json`)
    assert.equal(init.redirect, 'follow')
    if (init.redirect !== 'follow') return Response.redirect('https://other.example/feed.json', 302)
    return new Response('{"followed":true}', { headers: { 'Content-Type': 'text/plain' } })
  })
  const response = await fallback.fetch(requestFor('/updater.json'))
  assert.equal(mock.mock.callCount(), 1)
  assert.equal(response.status, 200)
  assert.equal(response.headers.get('Location'), null)
  assert.equal(response.headers.get('Content-Type'), 'application/json; charset=utf-8')
  assert.equal(await response.text(), '{"followed":true}')
})

for (const path of ['/', '/download/', '/pricing/?x=1', '/UPPER/Path', '/updates', '/updates-old/file', '/updates%2Ffile', '/botany/', '/bot%2Fdetails', '/UPDATER.json', '/updater.json/', '/__redirect-health/']) {
  for (const host of ['docketseo.app', 'www.docketseo.app']) {
    test(`fallback pages wait without redirecting: ${host}${path}`, async () => {
      const get = await fallback.fetch(new Request(`https://${host}${path}`))
      const head = await fallback.fetch(new Request(`https://${host}${path}`, { method: 'HEAD' }))
      assert.equal(get.status, 503)
      assert.equal(head.status, get.status)
      assert.deepEqual([...head.headers], [...get.headers])
      assert.equal(get.headers.get('Retry-After'), '300')
      assert.equal(get.headers.get('Cache-Control'), 'no-store')
      assert.equal(get.headers.get('Content-Type'), 'text/plain; charset=utf-8')
      assert.equal(get.headers.get('Location'), null)
      assert.equal(head.body, null)
      assert.equal(await head.text(), '')
      assert.equal(await get.text(), moving)
    })
  }
}

for (const status of [200, 206, 304, 404]) {
  test(`fallback HEAD keeps GET headers and status ${status} with no body`, async (t) => {
    const mock = t.mock.method(globalThis, 'fetch', async (input, init) => {
      assert.equal(input, `${raw}/updates/2.0/Docket.exe`)
      assert.ok(['GET', 'HEAD'].includes(init.method))
      return new Response(init.method === 'HEAD' || status === 304 ? null : 'abc', {
        status,
        headers: { 'Content-Length': '3', 'Content-Range': 'bytes 0-2/10', 'Accept-Ranges': 'bytes', ETag: '"raw-1"' },
      })
    })
    const get = await fallback.fetch(requestFor('/updates/2.0/Docket.exe'))
    const head = await fallback.fetch(requestFor('/updates/2.0/Docket.exe', { method: 'HEAD' }))
    assert.equal(mock.mock.calls[0].arguments[1].method, 'GET')
    assert.equal(mock.mock.calls[1].arguments[1].method, 'HEAD')
    assert.equal(head.status, status)
    assert.equal(head.status, get.status)
    assert.deepEqual([...head.headers], [...get.headers])
    assert.equal(head.headers.get('Content-Length'), '3')
    assert.equal(head.headers.get('Location'), null)
    assert.equal(head.body, null)
    assert.equal(await head.text(), '')
  })
}

test('fallback returns the origin stream before any file bytes arrive', async (t) => {
  let controller
  let reads = 0
  const stream = new ReadableStream({
    start(value) { controller = value },
    pull() { reads += 1 },
  }, { highWaterMark: 0 })
  const origin = new Response(stream, { headers: { 'Content-Length': '4' } })
  for (const method of ['arrayBuffer', 'blob', 'bytes', 'formData', 'json', 'text', 'clone']) {
    origin[method] = () => assert.fail(`Worker must not call ${method}`)
  }
  t.mock.method(globalThis, 'fetch', async () => origin)
  const response = await fallback.fetch(requestFor('/updates/2.0/large.tgz'))
  assert.equal(response.body, origin.body)
  assert.equal(response.body, stream)
  assert.equal(stream.locked, false)
  assert.equal(reads, 0)
  assert.equal(response.headers.get('Content-Length'), '4')
  controller.enqueue(new Uint8Array([0, 1, 2, 255]))
  controller.close()
  assert.deepEqual(new Uint8Array(await response.arrayBuffer()), new Uint8Array([0, 1, 2, 255]))
})

for (const path of ['/', '/updater.json', '/updates/2.0/Docket.exe', '/__redirect-health']) {
  for (const method of ['POST', 'PUT', 'DELETE', 'OPTIONS']) {
    test(`fallback rejects ${method} ${path} without fetching`, async () => {
      const response = await fallback.fetch(requestFor(path, { method }))
      assert.equal(response.status, 405)
      assert.equal(response.headers.get('Allow'), path === '/__redirect-health' ? 'GET' : 'GET, HEAD')
      assert.equal(response.headers.get('Location'), null)
      assert.equal(response.headers.get('Content-Type'), 'text/plain; charset=utf-8')
      assert.equal(await response.text(), 'Method not allowed\n')
    })
  }
}

for (const mode of ['fallback', 'redirect']) {
  test(`${mode} health is local with the live mode in a header`, async () => {
    for (const host of ['docketseo.app', 'www.docketseo.app']) {
      const response = await makeHandler(mode).fetch(new Request(`https://${host}/__redirect-health?probe=1`))
      assert.equal(response.status, 200)
      assert.equal(response.headers.get('X-Mode'), mode)
      assert.equal(response.headers.get('Content-Type'), 'text/plain; charset=utf-8')
      assert.equal(response.headers.get('Cache-Control'), 'no-store')
      assert.equal(response.headers.get('Location'), null)
      assert.equal(await response.text(), 'ok')
    }
    const head = await makeHandler(mode).fetch(requestFor('/__redirect-health', { method: 'HEAD' }))
    assert.equal(head.status, 405)
    assert.equal(head.headers.get('Allow'), 'GET')
    assert.equal(head.body, null)
  })
}

test('makeHandler passthrough sends health and other requests to the unchanged origin', async (t) => {
  for (const path of ['/', '/offer.json', '/__redirect-health']) {
    for (const method of ['GET', 'HEAD', 'POST']) {
      const request = requestFor(path, { method })
      const origin = new Response(null, { status: 204, headers: { 'X-Origin': 'unchanged' } })
      const mock = t.mock.method(globalThis, 'fetch', async (...args) => {
        assert.deepEqual(args, [request])
        assert.equal(args[0], request)
        return origin
      })
      const response = await makeHandler('passthrough').fetch(request)
      assert.equal(mock.mock.callCount(), 1)
      assert.equal(response, origin)
      assert.equal(response.headers.get('X-Mode'), null)
    }
  }
})

for (const mode of ['', 'invalid', 'PASSTHROUGH', 'toString', undefined]) {
  test(`unknown MODE ${String(mode)} fails every kind of request locally`, async () => {
    for (const path of ['/', '/updater.json', '/__redirect-health']) {
      for (const method of ['GET', 'HEAD', 'POST']) {
        const response = await makeHandler(mode).fetch(requestFor(path, { method }))
        assert.equal(response.status, 500)
        assert.equal(response.headers.get('Content-Type'), 'text/plain; charset=utf-8')
        assert.equal(response.headers.get('Cache-Control'), 'no-store')
        assert.equal(response.headers.get('Location'), null)
        if (method === 'HEAD') assert.equal(response.body, null)
        assert.equal(await response.text(), method === 'HEAD' ? '' : 'bad MODE')
      }
    }
  })
}
