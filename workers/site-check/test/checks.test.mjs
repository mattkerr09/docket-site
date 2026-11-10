import { test } from 'node:test'
import assert from 'node:assert/strict'
import { checks, rank, extractPage } from '../src/checks.js'
import { perfect, Rewriter } from './fakes.mjs'

const page = (over = {}) => ({ url: 'https://public.com/', status: 200, hops: 0, ttfb: 100, linked: false, data: perfect(), ...over })
const context = { robotsFound: true, sitemapFound: true, httpUpgrades: true, attempts: 1, blocked: [] }
const find = (pages, id, extra = {}) => checks(pages, { ...context, ...extra }).find((i) => i.id === id)

test('empty and perfect sites have honest denominators', () => {
  assert.deepEqual(checks([], { ...context, attempts: 0 }), [])
  const r = rank(checks([page()], context))
  assert.deepEqual(r.issues, [])
  assert.equal(r.fine.length, 5)
  assert.ok(r.fine.every((i) => i.of === 1 && i.count === 1 && /of the 1 pages read/.test(i.label)))
})

test('each content check runs on extracted fixtures', () => {
  const cases = [
    ['missing_title', { titles: [] }], ['missing_title', { titles: ['  '] }],
    ['short_title', { titles: ['Home'] }], ['long_title', { titles: ['x'.repeat(66)] }],
    ['missing_description', { metas: {} }], ['missing_h1', { h1s: [] }],
    ['multiple_h1', { h1s: ['One', 'Two'] }], ['missing_canonical', { canonicals: [] }],
    ['missing_lang', { lang: '' }], ['missing_viewport', { metas: { viewport: [''] } }],
    ['missing_og', { metas: { 'og:title': ['Title'] } }], ['missing_og', { metas: { 'og:image': ['/a.png'] } }],
    ['missing_structured_data', { structured: false, jsonld: [] }], ['thin_pages', { words: 99 }],
    ['missing_alt', { imagesMissingAlt: 2 }], ['noindex', { metas: { robots: ['NOINDEX, follow'] } }],
    ['noindex', { metas: { googlebot: ['none'] } }],
  ]
  for (const [id, data] of cases) {
    const issue = find([page({ data: perfect(data) })], id)
    assert.equal(issue.count, 1, id)
    assert.equal(issue.of, 1, id)
    assert.deepEqual(issue.examples, ['/'], id)
    assert.match(issue.label, /of the 1 pages read/, id)
  }
  assert.equal(find([page({ ttfb: 1501 })], 'slow_ttfb').count, 1)
  assert.equal(find([page({ ttfb: 1500 })], 'slow_ttfb').count, 0)
  assert.equal(find([page({ data: perfect({ words: 100 }) })], 'thin_pages').count, 0)
  assert.equal(find([page({ xRobots: 'googlebot: noindex' })], 'noindex').count, 1)
  assert.equal(find([page({ xRobots: 'none', linked: true })], 'linked_noindex').count, 1)
})

test('duplicates count all affected pages, decoded and whitespace-normalised, with three paths at most', () => {
  const pages = Array.from({ length: 5 }, (_, i) => page({ url: `https://public.com/p${i}?secret=value`, data: perfect({ titles: [i ? 'Cats & dogs' : ' Cats &amp;  dogs '] }) }))
  for (const id of ['duplicate_title', 'duplicate_description']) {
    const issue = find(pages, id, { attempts: 5 })
    assert.equal(issue.count, 5)
    assert.equal(issue.of, 5)
    assert.deepEqual(issue.examples, ['/p0', '/p1', '/p2'])
  }
})

test('transport, robots and presence checks describe exactly what was measured', () => {
  assert.equal(find([page({ status: 404, data: null })], 'http_errors').count, 1)
  assert.equal(find([page({ status: 503, data: null })], 'http_errors').count, 1)
  assert.equal(find([page({ hops: 2 })], 'redirect_chains').count, 1)
  assert.equal(find([page({ hops: 1 })], 'redirect_chains').count, 0)
  for (const [id, over] of [['missing_robots', { robotsFound: false }], ['missing_sitemap', { sitemapFound: false }], ['http_no_https', { httpUpgrades: false }]]) {
    assert.equal(find([page()], id, over).count, 1)
    assert.match(find([page()], id, over).label, /of the 1 pages read/)
  }
  const blocked = find([page()], 'robots_blocked', { blocked: ['/secret?a=b', '/private'] })
  assert.equal(blocked.count, 2)
  assert.equal(blocked.of, 2)
  assert.match(blocked.label, /blocked by robots.txt/)
  assert.deepEqual(blocked.examples, ['/secret', '/private'])
})

test('rank by affected share, then severity, with bounded issues, examples and fine items', () => {
  const items = [
    { id: 'smaller', count: 2, of: 10, severity: 3, examples: [] },
    { id: 'common', count: 8, of: 10, severity: 1, examples: [] },
    { id: 'severe', count: 8, of: 10, severity: 3, examples: [] },
    ...Array.from({ length: 10 }, (_, i) => ({ id: `issue${i}`, count: 1, of: 10, severity: 1, examples: ['/1', '/2', '/3', '/4'] })),
    ...['missing_title', 'missing_description', 'missing_h1', 'missing_canonical', 'missing_viewport', 'missing_lang']
      .map((id) => ({ id, count: 0, of: 10, label: 'Fine', severity: 1, examples: [] })),
  ]
  const r = rank(items)
  assert.deepEqual(r.issues.slice(0, 3).map((i) => i.id), ['severe', 'common', 'smaller'])
  assert.equal(r.issues.length, 8)
  assert.equal(r.fine.length, 5)
  assert.ok([...r.issues, ...r.fine].every((i) => Object.keys(i).sort().join() === 'count,examples,id,label,of'))
  assert.ok(r.issues.every((i) => i.examples.length <= 3))
})

test('HTMLRewriter extraction reuses metadata and adds links, alt, visible text and all schema formats', async () => {
  const previous = globalThis.HTMLRewriter
  globalThis.HTMLRewriter = Rewriter
  Rewriter.events = [
    { selector: 'html', attrs: { lang: 'en' } },
    { selector: 'title', chunks: ['A useful ', 'page title for the test'] },
    { selector: 'meta', attrs: { name: 'description', content: 'A description' } },
    { selector: 'a[href]', attrs: { href: '/one?x=1&amp;y=2' } },
    { selector: 'a[href]', attrs: { href: 'https://other.com/' } },
    { selector: 'base[href]', attrs: { href: '/base/' } },
    { selector: 'img', attrs: { src: '/one.jpg' } },
    { selector: 'img', attrs: { src: '/decoration.jpg', alt: '' } },
    { selector: 'body', chunks: ['one two', ' three ', 'four'] },
    { selector: 'script, style, template, noscript', chunks: ['hidden words'] },
    { selector: '[itemscope], [typeof]', attrs: { itemscope: '' } },
  ]
  try {
    const data = await extractPage('<html>fixture</html>')
    assert.equal(data.lang, 'en')
    assert.deepEqual(data.titles, ['A useful page title for the test'])
    assert.deepEqual(data.links, ['/one?x=1&y=2', 'https://other.com/'])
    assert.equal(data.base, '/base/')
    assert.equal(data.imagesMissingAlt, 1)
    assert.equal(data.words, 4)
    assert.equal(data.structured, true)
  } finally { globalThis.HTMLRewriter = previous }
})
