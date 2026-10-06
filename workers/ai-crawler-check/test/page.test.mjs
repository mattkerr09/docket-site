import { test } from 'node:test'
import assert from 'node:assert/strict'
import { checkJsonLd, checkMeta, displayWidth, TITLE_MAX } from '../src/page.js'
import { botCheck, handle } from '../src/index.js'

const base = (over = {}) => ({
  url: 'https://example.com/services/', xRobots: '', lang: 'en',
  titles: ['Emergency plumber in Leeds, open 24 hours'], h1s: ['Emergency plumber'],
  canonicals: ['https://example.com/services/'],
  metas: {
    description: ['Burst pipe or no hot water? A Leeds plumber at your door within the hour, any time, with a fixed call-out price before we start.'],
    viewport: ['width=device-width'], 'og:title': ['x'], 'og:image': ['https://example.com/a.png'],
    'og:description': ['y'], 'twitter:card': ['summary'],
  },
  ...over,
})
const labels = (r) => r.findings.map((f) => `${f.level}:${f.label}`)

test('display width counts East Asian wide characters twice, as words.display_width does', () => {
  assert.equal(displayWidth('abc'), 3)
  assert.equal(displayWidth('小形羊羹 24本入 | 株式会社 虎屋'), 31)   // the docstring's own example
  assert.equal(displayWidth('ＡＢ'), 4)                                 // fullwidth Latin
})

test('a clean page is ok on every count it can be', () => {
  const r = checkMeta(base())
  assert.deepEqual(r.findings.filter((f) => f.level === 'problem' || f.level === 'warning'), [])
  assert.ok(labels(r).some((l) => l.startsWith('ok:Title length is fine')))
  assert.ok(labels(r).includes('ok:Indexable'))
})

test('titles: missing, empty, long, short, several', () => {
  assert.ok(labels(checkMeta(base({ titles: [] }))).includes('problem:No title tag'))
  assert.ok(labels(checkMeta(base({ titles: ['  '] }))).includes('problem:The title tag is empty'))
  const long = 'x'.repeat(TITLE_MAX + 1)
  assert.ok(labels(checkMeta(base({ titles: [long] }))).some((l) => l.startsWith('warning:Long title')))
  assert.ok(labels(checkMeta(base({ titles: ['Home'] }))).some((l) => l.startsWith('warning:Short title')))
  assert.ok(labels(checkMeta(base({ titles: ['A long enough title for a page', 'Second'] }))).includes('warning:2 title tags'))
  // 19 characters of Japanese is 31 wide: not short (the false positive Docket fixed).
  assert.ok(!labels(checkMeta(base({ titles: ['小形羊羹 24本入 | 株式会社 虎屋'] }))).some((l) => l.includes('Short title')))
})

test('noindex in the page or in the header is a problem; none counts as noindex', () => {
  assert.ok(labels(checkMeta(base({ metas: { ...base().metas, robots: ['noindex, follow'] } }))).includes('problem:This page asks search engines not to index it'))
  assert.ok(labels(checkMeta(base({ metas: { ...base().metas, robots: ['none'] } }))).includes('problem:This page asks search engines not to index it'))
  assert.ok(labels(checkMeta(base({ xRobots: 'noindex' }))).includes('problem:The server asks search engines not to index this page'))
  assert.ok(!labels(checkMeta(base({ metas: { ...base().metas, robots: ['index, follow'] } }))).some((l) => l.startsWith('problem')))
})

test('canonicals: this page, another page, several that disagree', () => {
  assert.ok(labels(checkMeta(base())).includes('ok:Canonical points to this page'))
  assert.ok(labels(checkMeta(base({ canonicals: ['/services'] }))).includes('ok:Canonical points to this page'))
  assert.ok(labels(checkMeta(base({ canonicals: ['https://example.com/'] }))).includes('note:Canonical points to another address'))
  assert.ok(labels(checkMeta(base({ canonicals: ['https://example.com/a', 'https://example.com/b'] }))).includes('problem:2 canonical tags that disagree'))
})

test('JSON-LD: invalid JSON names the line and column', () => {
  const r = checkJsonLd(['{\n  "@context": "https://schema.org",\n  "@type": "Product",\n  "name": "Kettle",\n}'])
  const f = r.findings.find((x) => x.level === 'problem')
  assert.match(f.label, /Block 1 is not valid JSON/)
  assert.match(f.detail, /line \d+, column \d+/)
})

test('JSON-LD: required properties come from Docket\'s table, nested nodes included', () => {
  const r = checkJsonLd([JSON.stringify({ '@context': 'https://schema.org', '@type': 'Product', name: 'Kettle',
    offers: { '@type': 'Offer', price: '29.00' } })])
  const l = labels(r)
  assert.ok(l.includes('problem:Product is missing image'))
  assert.ok(l.includes('problem:Offer is missing priceCurrency'))
  const ok = checkJsonLd([JSON.stringify({ '@context': 'https://schema.org', '@graph': [
    { '@type': 'Organization', name: 'Acme' }, { '@type': 'BreadcrumbList', itemListElement: [{ '@type': 'ListItem', position: 1 }] }] })])
  assert.ok(labels(ok).some((x) => x.startsWith('ok:3 items read')))
})

test('JSON-LD: no blocks, and a block with no @context', () => {
  assert.ok(labels(checkJsonLd([])).includes('note:No JSON-LD on this page'))
  assert.ok(labels(checkJsonLd([JSON.stringify({ '@type': 'Organization', name: 'Acme' })])).includes('warning:Block 1 has no @context'))
})

test('/page reads one page and returns the checks, never the HTML', async () => {
  const html = '<html lang="en"><head><title>Secret page body follows</title></head><body>PRIVATE</body></html>'
  const fetchImpl = async () => new Response(html, { status: 200, headers: { 'Content-Type': 'text/html' } })
  const env = { extract: async () => ({ lang: 'en', titles: ['A title that is long enough here'], metas: {}, canonicals: [], h1s: [], jsonld: [] }) }
  const res = await handle(new Request('https://w.example/page?url=example.com/a', { headers: { Origin: 'https://docketseo.app' } }), fetchImpl, env, null)
  const text = await res.text()
  const j = JSON.parse(text)
  assert.equal(res.status, 200)
  assert.equal(j.final_url, 'https://example.com/a')
  assert.ok(j.meta.findings.length > 0)
  assert.ok(!text.includes('PRIVATE'), 'the page body must not come back')
})

test('/page refuses what is not a web page, and private hosts', async () => {
  const pdf = async () => new Response('%PDF', { status: 200, headers: { 'Content-Type': 'application/pdf' } })
  const j = await (await handle(new Request('https://w.example/page?url=example.com/a.pdf'), pdf, {}, null)).json()
  assert.match(j.error, /not a web page/)
  const k = await (await handle(new Request('https://w.example/page?url=localhost/admin'), pdf, {}, null)).json()
  assert.match(k.error, /private|not a public/)
})

test('a bot check served instead of the page is reported, not graded', async () => {
  assert.ok(botCheck(202, '<html></html>'))
  assert.ok(botCheck(200, '<html><title>Just a moment...</title></html>'))
  assert.ok(!botCheck(200, '<html><title>Kettles</title>' + 'x'.repeat(30000) + 'captcha</html>'))
  const challenge = async () => new Response('<html>awswaf</html>', { status: 202, headers: { 'Content-Type': 'text/html' } })
  const j = await (await handle(new Request('https://w.example/page?url=example.com/'), challenge, {}, null)).json()
  assert.match(j.error, /bot check instead of the page \(HTTP 202\)/)
  assert.equal(j.meta, undefined)
})
