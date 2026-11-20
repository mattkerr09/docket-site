import { beforeEach, test } from 'node:test'
import assert from 'node:assert/strict'
import { makeHandler } from '../src/index.js'
import { OLD_PATHS } from '../src/old_urls.js'

const worker = makeHandler('redirect')
const request = (path, host = 'docketseo.app', init) => new Request(`https://${host}${path}`, init)

beforeEach((t) => {
  t.mock.method(globalThis, 'fetch', () => assert.fail('Unexpected fetch'))
})

test('robots.txt on the old apex is 200, allows everything and names the old-address sitemap', async () => {
  const response = await worker.fetch(request('/robots.txt'))
  assert.equal(response.status, 200)
  assert.match(response.headers.get('Content-Type'), /^text\/plain/)
  assert.equal(await response.text(), 'User-agent: *\nAllow: /\nSitemap: https://docketseo.app/sitemap-old.xml\n')
})

test('sitemap-old.xml is 200 XML listing only old-host URLs, home first, with no lastmod and no duplicates', async () => {
  const response = await worker.fetch(request('/sitemap-old.xml'))
  assert.equal(response.status, 200)
  assert.match(response.headers.get('Content-Type'), /^application\/xml/)
  const body = await response.text()
  const locs = [...body.matchAll(/<loc>([^<]+)<\/loc>/g)].map((m) => m[1])
  assert.equal(locs.length, OLD_PATHS.length)
  assert.ok(locs.length >= 150, 'the old URL list must stay complete')
  assert.equal(new Set(locs).size, locs.length)
  assert.equal(locs[0], 'https://docketseo.app/')
  assert.equal(locs[1], 'https://docketseo.app/download/')
  assert.ok(locs.every((loc) => loc.startsWith('https://docketseo.app/') && !loc.includes('checkengineseo')))
  assert.ok(!/lastmod/.test(body), 'a mass lastmod is what Bing disregards')
})

test('HEAD on the two old-address files has no body; other methods are refused', async () => {
  for (const path of ['/robots.txt', '/sitemap-old.xml']) {
    const head = await worker.fetch(request(path, 'docketseo.app', { method: 'HEAD' }))
    assert.equal(head.status, 200)
    assert.equal(await head.text(), '')
    const post = await worker.fetch(request(path, 'docketseo.app', { method: 'POST' }))
    assert.equal(post.status, 405)
  }
})

test('every other old path still 301s to the same path on checkengineseo.com', async () => {
  for (const path of ['/', '/sitemap.xml', '/robots.txt/', '/sitemap-old.xml/', '/download/', ...OLD_PATHS.slice(0, 30)]) {
    const response = await worker.fetch(request(path))
    assert.equal(response.status, 301, path)
    assert.equal(response.headers.get('Location'), `https://checkengineseo.com${path}`)
  }
})

test('www does not serve the old-address files and keeps redirecting', async () => {
  for (const path of ['/robots.txt', '/sitemap-old.xml']) {
    const response = await worker.fetch(request(path, 'www.docketseo.app'))
    assert.equal(response.status, 301)
    assert.equal(response.headers.get('Location'), `https://checkengineseo.com${path}`)
  }
})
