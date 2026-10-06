/**
 * One page, read for the free title/meta checker and the JSON-LD checker.
 *
 * The Worker fetches the page once, pulls out ONLY the head tags, the H1s and
 * the JSON-LD blocks (HTMLRewriter, streaming), and runs the checks below. The
 * page's HTML is never sent back, so this is not a proxy for reading pages.
 *
 * The rules are ported from Docket's engine (docket-app, backend/seo_engine):
 *   - title and description widths and bounds: checks/onpage.py TITLE_MIN 25,
 *     TITLE_MAX 65, DESC_MIN 70, DESC_MAX 165, measured with words.display_width
 *     (East Asian wide and fullwidth characters count two);
 *   - required properties per schema type: checks/structured.py REQUIRED_PROPS.
 * `checkMeta` and `checkJsonLd` are pure, so test/page.test.mjs runs them in Node.
 */

export const TITLE_MIN = 25
export const TITLE_MAX = 65
export const DESC_MIN = 70
export const DESC_MAX = 165

/** structured.py REQUIRED_PROPS, verbatim. */
export const REQUIRED_PROPS = {
  Product: ['name', 'image'],
  Offer: ['price', 'priceCurrency'],
  Recipe: ['name', 'image', 'recipeIngredient', 'recipeInstructions'],
  Event: ['name', 'startDate', 'location'],
  JobPosting: ['title', 'datePosted', 'hiringOrganization', 'jobLocation'],
  FAQPage: ['mainEntity'],
  HowTo: ['name', 'step'],
  Article: ['headline'],
  BlogPosting: ['headline'],
  LocalBusiness: ['name', 'address'],
  Organization: ['name'],
  Review: ['reviewRating', 'author'],
  BreadcrumbList: ['itemListElement'],
  VideoObject: ['name', 'thumbnailUrl', 'uploadDate'],
  SoftwareApplication: ['name', 'applicationCategory'],
}

/**
 * words.display_width: half-width units, East Asian Wide (W) and Fullwidth (F)
 * characters count two. Python asks unicodedata; JavaScript has no such table,
 * so these are the W and F blocks, which cover the scripts and symbols that
 * render double width in a search result.
 */
const WIDE = [[0x1100, 0x115f], [0x231a, 0x231b], [0x2329, 0x232a], [0x23e9, 0x23ec], [0x2e80, 0x303e],
  [0x3041, 0x33ff], [0x3400, 0x4dbf], [0x4e00, 0x9fff], [0xa000, 0xa4cf], [0xa960, 0xa97f],
  [0xac00, 0xd7a3], [0xf900, 0xfaff], [0xfe10, 0xfe19], [0xfe30, 0xfe6f], [0xff00, 0xff60],
  [0xffe0, 0xffe6], [0x1f300, 0x1f64f], [0x1f900, 0x1f9ff], [0x20000, 0x2fffd], [0x30000, 0x3fffd]]

export function displayWidth(text) {
  let total = 0
  for (const ch of String(text || '')) {
    const c = ch.codePointAt(0)
    total += WIDE.some(([a, b]) => c >= a && c <= b) ? 2 : 1
  }
  return total
}

/**
 * HTMLRewriter hands text and attribute values over as written, entities and
 * all. A browser shows "Web Design &amp; SEO" as "Web Design & SEO", and a
 * search result measures the decoded text, so decode before showing or
 * measuring anything (builtbykerr.com's title read 4 wider than it is).
 * JSON-LD is not decoded: a browser does not decode entities inside <script>.
 */
const NAMED = { amp: '&', lt: '<', gt: '>', quot: '"', apos: "'", nbsp: '\u00a0', ndash: '\u2013',
  mdash: '\u2014', hellip: '\u2026', lsquo: '\u2018', rsquo: '\u2019', ldquo: '\u201c', rdquo: '\u201d',
  middot: '\u00b7', bull: '\u2022', copy: '\u00a9', reg: '\u00ae', trade: '\u2122', euro: '\u20ac',
  pound: '\u00a3', yen: '\u00a5', cent: '\u00a2', times: '\u00d7', laquo: '\u00ab', raquo: '\u00bb',
  eacute: '\u00e9', egrave: '\u00e8', aacute: '\u00e1', agrave: '\u00e0', oacute: '\u00f3', ouml: '\u00f6',
  uuml: '\u00fc', auml: '\u00e4', ntilde: '\u00f1', ccedil: '\u00e7', szlig: '\u00df', deg: '\u00b0' }

export function decodeEntities(s) {
  return String(s || '').replace(/&(#x[0-9a-f]+|#[0-9]+|[a-z][a-z0-9]*);/gi, (m, e) => {
    if (e[0] === '#') {
      const n = e[1] === 'x' || e[1] === 'X' ? parseInt(e.slice(2), 16) : parseInt(e.slice(1), 10)
      return n > 0 && n <= 0x10ffff ? String.fromCodePoint(n) : m
    }
    const v = NAMED[e.toLowerCase()]
    return v === undefined ? m : v
  })
}

const clean = (s) => decodeEntities(s).replace(/\s+/g, ' ').trim()

function directives(value) {
  return clean(value).toLowerCase().split(/[\s,]+/).filter(Boolean)
}

/**
 * The title/meta checks for one page. `data` is what `extract` returns plus
 * `url` (the address read) and `xRobots` (the X-Robots-Tag header, or '').
 * Each finding: { level: 'problem' | 'warning' | 'note' | 'ok', label, detail }.
 */
export function checkMeta(data) {
  const out = []
  const add = (level, label, detail = '') => out.push({ level, label, detail })
  const titles = (data.titles || []).map(clean)
  const title = titles[0]
  if (!titles.length) add('problem', 'No title tag', 'Search results and browser tabs show the page with no name. Add a <title> in the <head>.')
  else if (!title) add('problem', 'The title tag is empty', 'The <title> element is there but has no text in it.')
  else {
    const w = displayWidth(title)
    if (w > TITLE_MAX) add('warning', `Long title: ${w} wide`, `Search results cut titles off at about 580 pixels, roughly ${TITLE_MAX} Latin characters. Put the words that matter first.`)
    else if (w < TITLE_MIN) add('warning', `Short title: ${w} wide`, `Under ${TITLE_MIN} gives a search result little to show. Say what the page is and who it is for.`)
    else add('ok', `Title length is fine: ${w} wide`, `Inside ${TITLE_MIN} to ${TITLE_MAX}, the range Docket uses.`)
  }
  if (titles.length > 1) add('warning', `${titles.length} title tags`, 'Search engines use the first one. Remove the others.')

  const descs = (data.metas.description || []).map(clean)
  const desc = descs[0]
  if (!descs.length) add('warning', 'No meta description', 'Search engines write their own snippet from the page text, which is often not the sentence you would choose.')
  else if (!desc) add('warning', 'The meta description is empty', 'The tag is there with no text in its content attribute.')
  else {
    const w = displayWidth(desc)
    if (w > DESC_MAX) add('warning', `Long description: ${w} wide`, `Snippets are cut at about ${DESC_MAX}. Put the reason to click in the first sentence.`)
    else if (w < DESC_MIN) add('warning', `Short description: ${w} wide`, `Under ${DESC_MIN} leaves room a search result will fill with whatever text it picks.`)
    else add('ok', `Description length is fine: ${w} wide`, `Inside ${DESC_MIN} to ${DESC_MAX}.`)
  }
  if (descs.length > 1) add('note', `${descs.length} meta descriptions`, 'Only one is used. Remove the others.')

  const robots = [...(data.metas.robots || []), ...(data.metas.googlebot || [])].flatMap(directives)
  const header = directives(data.xRobots)
  const noindex = (list) => list.includes('noindex') || list.includes('none')
  if (noindex(robots)) add('problem', 'This page asks search engines not to index it', 'A robots meta tag on the page says noindex. Remove it if the page should appear in search.')
  if (noindex(header)) add('problem', 'The server asks search engines not to index this page', 'The X-Robots-Tag header says noindex. Remove it if the page should appear in search.')
  if (!noindex(robots) && !noindex(header)) add('ok', 'Indexable', 'No noindex in the page or its headers.')
  if (robots.includes('nofollow') || header.includes('nofollow')) add('note', 'Links on this page are nofollow', 'Search engines are asked not to follow any link on the page.')

  const canon = [...new Set((data.canonicals || []).map(clean).filter(Boolean))]
  if (!canon.length) add('note', 'No canonical tag', 'Search engines pick the address to show themselves. A canonical says which one you mean.')
  else if (canon.length > 1) add('problem', `${canon.length} canonical tags that disagree`, `They point at ${canon.join(' and ')}. Search engines may ignore all of them.`)
  else {
    let target = null
    try { target = new URL(canon[0], data.url) } catch { add('warning', 'The canonical is not a valid address', canon[0]) }
    if (target) {
      const here = new URL(data.url)
      const same = target.origin === here.origin && target.pathname.replace(/\/$/, '') === here.pathname.replace(/\/$/, '')
      if (same) add('ok', 'Canonical points to this page', target.toString())
      else add('note', 'Canonical points to another address', `${target.toString()}. Search engines are asked to show that address instead of this one.`)
      if (!/^https?:\/\//i.test(canon[0])) add('note', 'The canonical is a relative address', 'It works, but an absolute address cannot be misread.')
    }
  }

  const h1s = (data.h1s || []).map(clean)
  if (!h1s.length) add('warning', 'No H1 heading', 'The main heading tells readers and search engines what the page is about.')
  else if (h1s.length > 1) add('note', `${h1s.length} H1 headings`, 'One main heading per page is clearest.')
  else add('ok', 'One H1 heading', h1s[0].slice(0, 120))

  if (!clean(data.lang)) add('warning', 'No language declared', 'Add lang to the <html> tag, for example lang="en". Screen readers and search engines use it.')
  if (!(data.metas.viewport || []).length) add('warning', 'No viewport tag', 'Phones show a desktop-width page shrunk down. Add <meta name="viewport" content="width=device-width, initial-scale=1">.')

  const og = (k) => clean((data.metas[k] || [])[0])
  if (!og('og:title')) add('warning', 'No og:title', 'Links shared on social apps and in chats fall back to whatever they can find.')
  if (!og('og:image')) add('warning', 'No og:image', 'Links shared on social apps and in chats show no picture.')
  if (!og('og:description')) add('note', 'No og:description', 'Shared links fall back to the meta description, or to nothing.')
  if (!og('twitter:card')) add('note', 'No twitter:card', 'X falls back to the Open Graph tags, so this is minor.')

  return {
    title: title || null, titleWidth: title ? displayWidth(title) : null,
    description: desc || null, descriptionWidth: desc ? displayWidth(desc) : null,
    canonical: canon[0] || null, lang: clean(data.lang) || null, h1: h1s.slice(0, 3),
    og: { title: og('og:title') || null, description: og('og:description') || null, image: og('og:image') || null },
    findings: out,
  }
}

function lineCol(text, pos) {
  const before = text.slice(0, pos).split('\n')
  return { line: before.length, column: before[before.length - 1].length + 1 }
}

function typesOf(node) {
  const t = node['@type']
  return (Array.isArray(t) ? t : [t]).filter((x) => typeof x === 'string').map((x) => x.replace(/^.*[/#:]/, ''))
}

function walk(value, visit, depth = 0) {
  if (depth > 12 || value === null || typeof value !== 'object') return
  if (Array.isArray(value)) { value.forEach((v) => walk(v, visit, depth + 1)); return }
  if ('@type' in value) visit(value)
  for (const [k, v] of Object.entries(value)) if (k !== '@context') walk(v, visit, depth + 1)
}

function present(v) {
  if (v === undefined || v === null) return false
  if (typeof v === 'string') return v.trim() !== ''
  if (Array.isArray(v)) return v.length > 0
  return true
}

/** The JSON-LD checks for one page's blocks (each the raw text of one script). */
export function checkJsonLd(blocks) {
  const findings = []
  const nodes = []
  const add = (level, label, detail = '') => findings.push({ level, label, detail })
  if (!blocks.length) {
    add('note', 'No JSON-LD on this page', 'No <script type="application/ld+json"> block was found. This checker does not read Microdata or RDFa.')
    return { blocks: 0, nodes, findings }
  }
  blocks.forEach((raw, i) => {
    const text = String(raw).trim().replace(/^<!--/, '').replace(/-->$/, '').trim()
    let data
    try { data = JSON.parse(text) } catch (e) {
      const m = /position (\d+)/.exec(e.message)
      const at = m ? lineCol(text, Number(m[1])) : null
      add('problem', `Block ${i + 1} is not valid JSON`, `${e.message.replace(/ in JSON at position \d+.*$/, '')}${at ? ` at line ${at.line}, column ${at.column}` : ''}. Search engines discard the whole block.`)
      return
    }
    const roots = Array.isArray(data) ? data : [data]
    if (!roots.some((r) => r && typeof r === 'object' && '@context' in r)) {
      add('warning', `Block ${i + 1} has no @context`, 'Without "@context": "https://schema.org" the types in it mean nothing to a search engine.')
    }
    walk(data, (node) => {
      const types = typesOf(node)
      const missing = []
      for (const t of types) for (const p of REQUIRED_PROPS[t] || []) if (!present(node[p]) && !missing.includes(p)) missing.push(p)
      nodes.push({ block: i + 1, types, name: typeof node.name === 'string' ? clean(node.name).slice(0, 80) : null, missing })
      if (missing.length) add('problem', `${types.join(', ')} is missing ${missing.join(', ')}`, `Google requires ${missing.length === 1 ? 'it' : 'them'} for a rich result. The markup is read but earns no rich result without ${missing.length === 1 ? 'it' : 'them'}.`)
    })
  })
  if (nodes.length && !findings.some((f) => f.level === 'problem')) add('ok', `${nodes.length} item${nodes.length === 1 ? '' : 's'} read, none missing a required property`, 'Checked against the properties Google requires for each type Docket knows.')
  return { blocks: blocks.length, nodes: nodes.slice(0, 40), findings }
}

/**
 * Pull the head tags, H1s and JSON-LD out of `html` with HTMLRewriter. Only
 * what the checks read is kept; the rest of the page is discarded as it streams.
 */
export async function extract(html) {
  const d = { lang: '', titles: [], metas: {}, canonicals: [], h1s: [], jsonld: [] }
  let title = null; let h1 = null; let ld = null; let svg = 0
  const meta = (k, v) => { (d.metas[k] = d.metas[k] || []).push(v) }
  const wanted = (k) => ['description', 'robots', 'googlebot', 'viewport'].includes(k) || k.startsWith('og:') || k.startsWith('twitter:')
  const rw = new HTMLRewriter()
    .on('html', { element(e) { if (!d.lang) d.lang = e.getAttribute('lang') || '' } })
    // An inline SVG icon carries its own <title> (github.com had 24 of them):
    // it names the icon, not the page, so titles inside <svg> are not counted.
    .on('svg', { element(e) { svg++; try { e.onEndTag(() => { svg-- }) } catch { svg-- } } })
    .on('title', {
      element(e) { if (svg === 0 && d.titles.length < 5) { title = ''; e.onEndTag(() => { d.titles.push(title); title = null }) } },
      text(t) { if (title !== null && title.length < 1000) title += t.text },
    })
    .on('meta', {
      // Both attributes, not either: gov.uk writes
      // <meta name="title" property="og:title" content="…"> on one tag.
      element(e) {
        const keys = new Set([e.getAttribute('name'), e.getAttribute('property')]
          .map((k) => (k || '').toLowerCase().trim()).filter(Boolean))
        for (const k of keys) if (wanted(k)) meta(k, e.getAttribute('content') || '')
      },
    })
    .on('link', {
      element(e) {
        const rel = (e.getAttribute('rel') || '').toLowerCase().split(/\s+/)
        if (rel.includes('canonical') && d.canonicals.length < 5) d.canonicals.push(e.getAttribute('href') || '')
      },
    })
    .on('h1', {
      element(e) { if (d.h1s.length < 10) { h1 = ''; e.onEndTag(() => { d.h1s.push(h1); h1 = null }) } },
      text(t) { if (h1 !== null && h1.length < 300) h1 += t.text },
    })
    .on('script', {
      element(e) {
        if ((e.getAttribute('type') || '').toLowerCase().trim() !== 'application/ld+json' || d.jsonld.length >= 20) return
        ld = ''
        e.onEndTag(() => { d.jsonld.push(ld); ld = null })
      },
      text(t) { if (ld !== null && ld.length < 200000) ld += t.text },
    })
  await rw.transform(new Response(html)).arrayBuffer()
  return d
}
