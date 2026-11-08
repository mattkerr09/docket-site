/** One page's HTML only. A small token reader, not a browser or a full accessible-name implementation. */
import { decodeEntities } from './page.js'

export const STANDARD = 'WCAG 2.1 Level A and AA'
export const DISCLAIMER = 'Automated checks find some accessibility problems, not all. This is not legal advice and does not say whether a site meets the law.'
const MAX_ELEMENTS = 20000
const MAX_FINDINGS = 25
const MAX_NAME_STEPS = 50000
const SC = [
  ['1.1.1', 'Non-text Content'], ['3.1.1', 'Language of Page'], ['2.4.2', 'Page Titled'],
  ['2.4.4', 'Link Purpose (In Context)'], ['4.1.2', 'Name, Role, Value'],
  ['1.3.1', 'Info and Relationships'], ['3.3.2', 'Labels or Instructions'],
  ['4.1.1', 'Parsing'], ['2.4.1', 'Bypass Blocks'],
].map(([sc, sc_name]) => ({ sc, sc_name, level: 'A' }))
const VOID = new Set('area base br col embed hr img input link meta param source track wbr'.split(' '))
const RAW = new Set(['script', 'style', 'textarea', 'title', 'iframe', 'xmp', 'noembed', 'noframes'])
const present = (s) => String(s || '').replace(/[\u200b-\u200f\u2060\ufeff]/g, '').trim()
const clean = (s) => present(decodeEntities(s))
const words = (s) => String(s || '').trim().split(/\s+/).filter(Boolean)

function attributes(source) {
  const out = Object.create(null)
  const re = /([^\s=/>]+)(?:\s*=\s*(?:"([^"]*)"|'([^']*)'|([^\s>]+)))?/g
  for (const m of source.matchAll(re)) {
    const key = m[1].toLowerCase()
    // HTML keeps the first value when an attribute occurs twice.
    if (!(key in out)) out[key] = decodeEntities(m[2] ?? m[3] ?? m[4] ?? '')
  }
  return out
}

function read(html) {
  const root = { tag: '', attrs: {}, children: [], parent: null, hidden: false }
  const stack = [root], nodes = [], ids = new Map(), duplicates = new Map(), openTags = new Map()
  const token = /<!--|<!|<\?|<\/?[a-zA-Z][a-zA-Z0-9:-]*/g
  let end = 0, limited = false
  const text = (s) => {
    if (clean(s)) stack[stack.length - 1].text = true
    if (/\bskip\b/i.test(s)) for (let i = stack.length - 1; i > 0; i--) {
      if (stack[i].tag === 'a') { stack[i].skipText = true; break }
    }
  }
  for (let m; (m = token.exec(html));) {
    text(html.slice(end, m.index))
    if (m[0] === '<!--') {
      const close = html.indexOf('-->', token.lastIndex)
      end = close < 0 ? html.length : close + 3
      token.lastIndex = end
      continue
    }
    // Scan a tag once, keeping > inside a quoted attribute. No backtracking over the page.
    let quote = '', at = token.lastIndex
    for (; at < html.length; at++) {
      const ch = html[at]
      if (quote) { if (ch === quote) quote = '' }
      else if (ch === '"' || ch === "'") quote = ch
      else if (ch === '>') break
    }
    if (at === html.length) { end = at; break }
    end = at + 1; token.lastIndex = end
    const raw = html.slice(m.index, end)
    if (/^<[!?]/.test(raw)) continue
    const tag = /^<\/?([^\s/>]+)/.exec(raw)[1].toLowerCase()
    if (raw[1] === '/') {
      const positions = openTags.get(tag)
      if (positions?.length) {
        const depth = positions[positions.length - 1]
        while (stack.length > depth) openTags.get(stack.pop().tag).pop()
      }
      continue
    }
    if (nodes.length === MAX_ELEMENTS) { limited = true; break }
    const attrs = attributes(raw.slice(1 + tag.length, -1))
    const parent = stack[stack.length - 1]
    const hidden = parent.hidden || 'hidden' in attrs || attrs['aria-hidden']?.toLowerCase() === 'true'
    const node = { tag, attrs, parent, children: [], hidden, text: false, element: raw.replace(/\s+/g, ' ').slice(0, 180) }
    node.label = parent.tag === 'label' ? parent : parent.label
    node.svg = tag === 'svg' || parent.svg
    nodes.push(node); parent.children.push(node)
    if (attrs.id) {
      if (ids.has(attrs.id)) duplicates.set(attrs.id, node)
      else ids.set(attrs.id, node)
    }
    // Templates are inert. Raw-text elements may contain things that look like HTML tags.
    if (RAW.has(tag) || tag === 'template') {
      const close = new RegExp(`</${tag}\\s*>`, 'gi')
      close.lastIndex = end
      const match = close.exec(html)
      if (tag === 'title' || tag === 'textarea') node.text = !!clean(html.slice(end, match ? match.index : html.length))
      if (tag === 'template') {
        // Match nested templates without reading their contents as page elements.
        const nested = /<\/?template\b(?:[^'">]|"[^"]*"|'[^']*')*>/gi
        nested.lastIndex = end
        let depth = 1, next
        while ((next = nested.exec(html))) {
          depth += /^<\//.test(next[0]) ? -1 : 1
          if (!depth) break
        }
        end = depth ? html.length : nested.lastIndex
      } else end = match ? close.lastIndex : html.length
      token.lastIndex = end
      continue
    }
    // In HTML, a trailing slash does not close a non-void element.
    if (!VOID.has(tag)) {
      if (!openTags.has(tag)) openTags.set(tag, [])
      openTags.get(tag).push(stack.length)
      stack.push(node)
    }
  }
  if (!limited) text(html.slice(end))
  return { nodes, ids, duplicates, limited }
}

function languageState(value) {
  const tag = String(value || '').trim()
  if (!tag) return 'invalid'
  // Private-use tags and the grandfathered tags are valid BCP 47 spellings too.
  if (/^x(?:-[a-z0-9]{1,8})+$/i.test(tag)) return 'valid'
  if (/^(?:art-lojban|cel-gaulish|en-GB-oed|no-bok|no-nyn|i-(?:ami|bnn|default|enochian|hak|klingon|lux|mingo|navajo|pwn|tao|tay|tsu)|sgn-(?:BE-FR|BE-NL|CH-DE)|zh-(?:min|min-nan|guoyu|hakka|xiang))$/i.test(tag)) return 'valid'
  // Intl accepts Unicode locale IDs, which omit BCP 47 extlangs. Check the rest, but leave these for review.
  const withoutExtlang = tag.replace(/^([a-z]{2,3})(?:-[a-z]{3}){1,3}(?=-|$)/i, '$1')
  try {
    Intl.getCanonicalLocales(withoutExtlang)
  } catch { return 'invalid' }
  const primary = tag.split('-')[0].toLowerCase()
  if (!/^[a-z]{2,3}$/.test(primary)) return 'invalid'
  if (withoutExtlang !== tag) return 'review'
  if (/^q[a-t][a-z]$/.test(primary)) return 'valid'
  try {
    if (new Intl.DisplayNames(['en'], { type: 'language', fallback: 'none' }).of(primary)) return 'valid'
  } catch { return 'review' }
  // Runtime language data is not a complete ISO 639-3 registry. Do not call an unfamiliar three-letter code a failure.
  return primary.length === 3 ? 'review' : 'invalid'
}

export function checkAccessibilityHtml(html, { truncated = false } = {}) {
  const { nodes, ids, duplicates, limited } = read(String(html || ''))
  const by_sc = SC.map((sc) => ({ ...sc, count: 0 }))
  const findings = []
  let total = 0, nameLimited = false, nameSteps = 0, nameWorkLimited = false
  const add = (sc, node, problem, fix, certainty = 'fails') => {
    const row = by_sc.find((r) => r.sc === sc)
    row.count++; total++
    if (findings.length < MAX_FINDINGS) findings.push({ sc, sc_name: row.sc_name, level: row.level, certainty,
      element: node?.element || '<html>', problem, fix })
  }
  // Resolve real ID references, including forward references. Empty attributes are not names.
  const knownNames = new Map()
  const name = (node, seen = new Set(), referenced = false, contents = true) => {
    if (++nameSteps > MAX_NAME_STEPS) { nameWorkLimited = true; return false }
    if (!node || seen.has(node) || (node.hidden && !referenced)) return false
    if (seen.size >= 64) { nameLimited = true; return false }
    const mode = 1 << ((referenced ? 2 : 0) + (contents ? 1 : 0))
    if ((knownNames.get(node) || 0) & mode) return true
    const yes = () => { knownNames.set(node, (knownNames.get(node) || 0) | mode); return true }
    const path = new Set(seen); path.add(node)
    const a = node.attrs
    if (words(a['aria-labelledby']).some((id) => name(ids.get(id), path, true))) return yes()
    if (present(a['aria-label'])) return yes()
    if (['img', 'area'].includes(node.tag) || (node.tag === 'input' && a.type?.toLowerCase() === 'image')) return present(a.alt) || present(a.title) ? yes() : false
    if (contents && (node.text || node.children.some((child) => !['input', 'select', 'textarea'].includes(child.tag) && name(child, path, referenced)))) return yes()
    return present(a.title) ? yes() : false
  }
  const labels = new Map()
  for (const n of nodes) if (n.tag === 'label' && n.attrs.for && name(n, new Set(), true)) labels.set(n.attrs.for, true)
  const absent = truncated || limited ? 'needs review' : 'fails'
  const htmlNode = nodes.find((n) => n.tag === 'html')
  const language = languageState(htmlNode?.attrs.lang)
  if (language !== 'valid') add('3.1.1', htmlNode, language === 'review' ? 'The page language tag needs review.' : 'The page has no valid lang value.',
    'Set lang on <html> to a valid tag for the page language, such as lang="en".', language === 'review' ? 'needs review' : absent)
  const title = nodes.find((n) => n.tag === 'title' && !n.svg)
  if (!title?.text) add('2.4.2', title, 'The page title is missing or empty.', 'Add a <title> in <head> that names this page.', absent)

  let main = false, skip = false
  for (const n of nodes) {
    const a = n.attrs, tag = n.tag
    if (n.hidden) continue
    const role = words(a.role?.toLowerCase())[0]
    if (tag === 'main' || role === 'main') main = true
    if (['img', 'area'].includes(tag) || (tag === 'input' && a.type?.toLowerCase() === 'image')) {
      if (!('alt' in a)) add('1.1.1', n, 'This image has no alt attribute.', 'Add alt text that gives its purpose. Use alt="" for a decorative image.')
    } else if (role === 'img' && !name(n, new Set(), false, false) && !n.children.some((c) => c.tag === 'title' && c.text)) {
      add('1.1.1', n, 'This role="img" element has no accessible name.', 'Add aria-label or aria-labelledby that describes the image.', absent)
    }
    if (tag === 'a' && 'href' in a) {
      if (!name(n)) add('2.4.4', n, 'This link has no accessible name.', 'Add link text, aria-label, aria-labelledby or an image with useful alt text.', absent)
      // A named same-page link to a real target may be a skip link. Its usefulness still needs a person.
      if (/^#[^#]+/.test(a.href || '') && name(n)) {
        let id = a.href.slice(1)
        try { id = decodeURIComponent(id) } catch { /* use the written ID */ }
        const target = ids.get(id)
        if (target && !target.hidden && (n.skipText || /skip|main|content/i.test(`${a.href} ${a['aria-label'] || ''}`))) skip = true
      }
    }
    if (tag === 'button' && !name(n)) add('4.1.2', n, 'This button has no accessible name.', 'Add button text, aria-label or aria-labelledby.', absent)
    if (tag === 'iframe' && !present(a.title)) add('4.1.2', n, 'This iframe has no title.', 'Add a title that says what the frame contains.')
    if (['select', 'textarea'].includes(tag) || (tag === 'input' && !['hidden', 'submit', 'button', 'image'].includes((a.type || '').toLowerCase()))) {
      let labelled = (a.id && labels.has(a.id)) || name(n, new Set(), false, false)
      if (!labelled && n.label && (!n.label.attrs.for || n.label.attrs.for === a.id)) labelled = name(n.label)
      if (!labelled) {
        const problem = 'This form field has no label.'
        const fix = 'Add a label linked with for and id, wrap the field in a label, or add aria-label, aria-labelledby or title.'
        add('1.3.1', n, problem, fix, absent); add('3.3.2', n, problem, fix, absent)
      }
    }
  }
  for (const [id, n] of duplicates) add('4.1.1', n, `The id "${id.slice(0, 120)}${id.length > 120 ? '...' : ''}" is used more than once.`, 'Give each element its own id. Update labels and links that use it.')
  if (!main && !skip) add('2.4.1', null, 'No main landmark or skip link was found.', 'Check how people skip repeated content. Add a <main> landmark or a working skip link.', 'needs review')
  // Deep or incomplete markup cannot establish the absence of a name with certainty.
  if (nameLimited || nameWorkLimited) for (const f of findings) if (/name|label/.test(f.problem)) f.certainty = 'needs review'
  return { by_sc, findings, limits: {
    html_only: true, rendering: false,
    not_checked: ['Colour contrast', 'Focus', 'Reflow', 'CSS visibility', 'Changes made by scripts', 'Full accessible names', 'Full language tag registry', 'Whether names and language match the content'],
    max_page_bytes: 2 * 1024 * 1024, page_truncated: truncated,
    max_elements: MAX_ELEMENTS, parser_truncated: limited, name_depth_limited: nameLimited,
    max_name_steps: MAX_NAME_STEPS, name_work_limited: nameWorkLimited,
    element_excerpt_chars: 180, id_excerpt_chars: 120,
    max_findings: MAX_FINDINGS, findings_truncated: total > MAX_FINDINGS,
    counts_include_all_findings: true,
  } }
}
