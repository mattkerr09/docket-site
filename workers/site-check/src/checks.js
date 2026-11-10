import { extract, decodeEntities, displayWidth } from '../../ai-crawler-check/src/page.js'
import { MAX_DISCOVERED_URLS, MAX_ISSUES, MAX_FINE, MAX_EXAMPLES, THIN_WORDS, SLOW_TTFB_MS, TITLE_MIN, TITLE_MAX } from './limits.js'

const clean = (value) => decodeEntities(value || '').replace(/\s+/g, ' ').trim()
const meta = (data, name) => clean((data.metas?.[name] || [])[0])
const path = (address) => {
  try { return new URL(address, 'https://path.invalid').pathname } catch { return '/' }
}
const fineLabels = {
  missing_title: 'have a title',
  missing_description: 'have a meta description',
  missing_h1: 'have an H1 heading',
  missing_canonical: 'have a canonical tag',
  missing_alt: 'have no images without an alt attribute',
  missing_viewport: 'have a viewport tag with content',
  missing_lang: 'have a page language',
  missing_og: 'have an Open Graph title and image',
  missing_structured_data: 'have JSON-LD, Microdata or RDFa tags',
  thin_pages: `have at least ${THIN_WORDS} words of page text`,
  slow_ttfb: `returned response headers within ${SLOW_TTFB_MS / 1000} seconds`,
}

// Reuse the existing streaming head extractor. The second bounded pass adds
// crawl links and body facts. Body text excludes script/style/template text.
export async function extractPage(html) {
  const data = await extract(html)
  const links = []
  let base = ''
  let imagesMissingAlt = 0
  let text = ''
  let hidden = 0
  let structured = data.jsonld.length > 0
  let linksTruncated = false
  const rewriter = new HTMLRewriter()
    .on('base[href]', { element(e) { if (!base) base = e.getAttribute('href') || '' } })
    .on('a[href]', { element(e) {
      if (links.length < MAX_DISCOVERED_URLS) links.push(decodeEntities(e.getAttribute('href') || ''))
      else linksTruncated = true
    } })
    .on('img', { element(e) { if (e.getAttribute('alt') === null) imagesMissingAlt++ } })
    .on('[itemscope], [typeof]', { element() { structured = true } })
    .on('script, style, template, noscript', { element(e) {
      hidden++
      e.onEndTag(() => { hidden-- })
    } })
    .on('p, div, h1, h2, h3, h4, h5, h6, li, br, td, section, article', { element(e) {
      if (!hidden) text += ' '
      if (e.tagName !== 'br') e.onEndTag(() => { if (!hidden) text += ' ' })
    } })
    .on('body', { text(t) { if (!hidden) text += t.text } })
  await rewriter.transform(new Response(html)).arrayBuffer()
  const words = clean(text).split(/\s+/).filter(Boolean).length
  return { ...data, base: decodeEntities(base), links, linksTruncated, imagesMissingAlt, words, structured }
}

const noindex = (page) => {
  const values = [...(page.data?.metas?.robots || []), ...(page.data?.metas?.googlebot || []), page.xRobots || '']
  return values.some((value) => /(?:^|[\s,:])(noindex|none)(?=$|[\s,])/i.test(value))
}

export function checks(pages, context) {
  const read = pages.filter((page) => page.data)
  const out = []
  const add = (id, label, severity, matches, of = read.length, kind = 'pages read') => {
    if (!of) return
    out.push({ id, label: `${matches.length} of the ${of} ${kind} ${label}`, count: matches.length, of,
      severity, examples: [...new Set(matches.map((page) => path(id === 'redirect_chains' ? page.requested || page.url : page.url)))].slice(0, MAX_EXAMPLES) })
  }
  const content = (id, label, severity, test) => add(id, label, severity, read.filter(test))
  const duplicates = (get) => {
    const counts = new Map()
    for (const page of read) {
      const value = get(page.data)
      if (value) counts.set(value, (counts.get(value) || 0) + 1)
    }
    return (page) => (counts.get(get(page.data)) || 0) > 1
  }
  const title = (data) => clean((data.titles || [])[0])
  const description = (data) => meta(data, 'description')
  content('missing_title', 'have no title', 3, (p) => !title(p.data))
  content('duplicate_title', 'share a title with another page read', 2, duplicates(title))
  content('short_title', `have a title under ${TITLE_MIN} characters wide`, 1, (p) => title(p.data) && displayWidth(title(p.data)) < TITLE_MIN)
  content('long_title', `have a title over ${TITLE_MAX} characters wide`, 1, (p) => displayWidth(title(p.data)) > TITLE_MAX)
  content('missing_description', 'have no meta description', 2, (p) => !description(p.data))
  content('duplicate_description', 'share a meta description with another page read', 1, duplicates(description))
  content('missing_h1', 'have no H1 heading', 2, (p) => !(p.data.h1s || []).length)
  content('multiple_h1', 'have more than one H1 heading', 1, (p) => p.data.h1s?.length > 1)
  content('missing_canonical', 'have no canonical tag', 1, (p) => !(p.data.canonicals || []).some(clean))
  content('noindex', 'ask search engines not to index them', 3, noindex)
  content('linked_noindex', 'are linked from a page read and ask not to be indexed', 3, (p) => p.linked && noindex(p))
  content('missing_alt', 'have an image without an alt attribute', 2, (p) => p.data.imagesMissingAlt > 0)
  content('missing_viewport', 'have no viewport tag with content', 2, (p) => !meta(p.data, 'viewport'))
  content('missing_lang', 'have no page language', 1, (p) => !clean(p.data.lang))
  content('missing_og', 'lack an Open Graph title or image', 1, (p) => !meta(p.data, 'og:title') || !meta(p.data, 'og:image'))
  content('missing_structured_data', 'have no JSON-LD, Microdata or RDFa tags', 1, (p) => !p.data.structured)
  content('thin_pages', `have fewer than ${THIN_WORDS} words of page text`, 1, (p) => p.data.words < THIN_WORDS)
  content('slow_ttfb', `took over ${SLOW_TTFB_MS / 1000} seconds to return response headers`, 2, (p) => p.ttfb > SLOW_TTFB_MS)
  const attempted = context.attempts ?? pages.length
  add('http_errors', 'answered with a 4xx or 5xx status', 3, pages.filter((p) => p.status >= 400), attempted, 'page addresses tried')
  add('redirect_chains', 'needed two or more redirects', 2, pages.filter((p) => p.hops >= 2), attempted, 'page addresses tried')
  for (const [id, found, label] of [
    ['missing_robots', context.robotsFound, 'belong to a site where robots.txt was not found'],
    ['missing_sitemap', context.sitemapFound, 'belong to a site where sitemap.xml was not found'],
    ['http_no_https', context.httpUpgrades, 'belong to a site whose HTTP check did not redirect to HTTPS'],
  ]) {
    if (typeof found === 'boolean') add(id, label, 1, found ? [] : read)
  }
  if (context.blocked?.length) add('robots_blocked', 'were blocked by robots.txt', 3,
    context.blocked.map((url) => ({ url })), context.blocked.length, 'skipped page addresses')
  return out
}

function publicItem(item, fine = false) {
  return { id: item.id, label: fine ? `${item.of} of the ${item.of} pages read ${fineLabels[item.id]}` : item.label,
    count: fine ? item.of : item.count, of: item.of, examples: (item.examples || []).slice(0, MAX_EXAMPLES) }
}

export function rank(items) {
  const issues = items.filter((item) => item.count > 0)
    .sort((a, b) => b.count / b.of - a.count / a.of || b.severity - a.severity || a.id.localeCompare(b.id))
    .slice(0, MAX_ISSUES).map((item) => publicItem(item))
  const fine = items.filter((item) => item.count === 0 && Object.hasOwn(fineLabels, item.id))
    .slice(0, MAX_FINE).map((item) => publicItem(item, true))
  return { issues, fine }
}
