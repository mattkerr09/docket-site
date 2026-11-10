import { parseRobots, evaluate } from '../../ai-crawler-check/src/robots.js'
import { checks, rank, extractPage } from './checks.js'
import { siteFrom, canonical, normalOrigin, hostKey, resolvePublic, dnsAddresses, BadAddress } from './safety.js'
import { bounded, readCapped, discard, realClock, Stopped } from './io.js'
import { MAX_PAGES, MAX_PAGE_BYTES, PAGE_TIMEOUT_MS, DEADLINE_MS, MAX_REDIRECTS,
  CONCURRENCY, REQUEST_PAUSE_MS, MAX_URLS_PER_PATH, MAX_DISCOVERED_URLS, DAY_MS, USER_AGENT,
  MAX_ROBOTS_RULES, MAX_ROBOTS_PATTERN_LENGTH, MAX_ROBOTS_WILDCARDS } from './limits.js'
export { readCapped } from './io.js'

const refused = 'This site asked not to be checked.'
const allowed = (policy, url) => policy.safe &&
  ['CheckEngineBot', '*'].every((agent) => evaluate(policy.parsed, agent, url.pathname + url.search).allowed)

export async function crawl(address, runtime = {}) {
  const start = siteFrom(address)
  const clock = runtime.clock || realClock
  const fetchImpl = runtime.fetch || fetch
  const resolver = runtime.resolve || ((host, signal) => dnsAddresses(host, fetchImpl, signal))
  const extract = runtime.extract || extractPage
  const began = clock.now()
  // Stop at midnight too. Daily visitor hashes and active leases expire then.
  const until = Math.min(began + DEADLINE_MS, Math.floor(began / DAY_MS) * DAY_MS + DAY_MS)
  const siteHost = hostKey(start)
  const policies = new Map()
  const records = []
  const tried = new Set()
  const blocked = new Set()
  const fetched = new Map()
  const seen = new Set()
  const pathVariants = new Map()
  const linked = new Set()
  let truncated = false
  let attempts = 0
  let nextStart = began
  let turn = Promise.resolve()
  let robotsFound = false
  let sitemapFound = null
  let httpUpgrades = null

  const expired = () => clock.now() >= until
  const resource = (action, parent) => bounded(clock, Math.min(until, clock.now() + PAGE_TIMEOUT_MS), action, parent)
  const checkTarget = (address) => {
    const url = siteFrom(address)
    if (hostKey(url) !== siteHost) throw new Error('The check cannot follow a link to another site.')
    return url
  }
  // Every network start, including redirects and auxiliary resources, passes
  // through this one queue. The gap applies across www and apex together.
  const send = async (url, init, pageOwner) => {
    const signal = init.signal
    const current = turn.then(async () => {
      signal.throwIfAborted()
      const wait = Math.max(0, nextStart - clock.now())
      if (wait) await clock.sleep(wait)
      signal.throwIfAborted()
      if (expired()) throw new Stopped('The check ran out of time.')
      nextStart = clock.now() + REQUEST_PAUSE_MS
      const sent = clock.now()
      if (pageOwner) tried.add(pageOwner)
      // Invoke fetch inside the start queue, but do not hold it while the
      // response arrives. This keeps both the gap and concurrency bounds.
      return { pending: fetchImpl(url.href, init), sent }
    })
    turn = current.catch(() => {})
    const { pending, sent } = await current
    return { response: await pending, sent }
  }

  async function requestChain(address, kind, signal) {
    let url = checkTarget(address)
    let hops = 0
    let ttfb = 0
    const visited = new Set()
    const owner = Symbol()
    for (;;) {
      signal.throwIfAborted()
      if (expired()) throw new Stopped('The check ran out of time.')
      const key = canonical(url)
      if (visited.has(url.href)) return { error: true, hops, url: url.href }
      visited.add(url.href)
      if (kind !== 'robots') {
        const policy = await getPolicy(url.origin, signal)
        if (!policy.safe) throw new Error('The robots.txt rules could not be read safely.')
        if (kind === 'page' && policy.found) robotsFound = true
        if (!allowed(policy, url)) {
          if (kind === 'page') blocked.add(url.href)
          return { blocked: true, hops, url: url.href }
        }
      }
      if (kind === 'page') {
        if (fetched.has(key) && fetched.get(key) !== owner) return { duplicate: true, hops, url: url.href }
        if (!admitVariant(key)) return { error: true, hops, url: url.href }
        fetched.set(key, owner)
      }
      await resolvePublic(url.hostname, resolver, signal)
      signal.throwIfAborted()
      const { response, sent } = await send(url, {
        method: kind === 'http' ? 'HEAD' : 'GET', redirect: 'manual', credentials: 'omit',
        signal, cache: 'no-store', cf: { cacheTtl: 0, cacheEverything: false },
        headers: { 'User-Agent': USER_AGENT, Accept: kind === 'page' ? 'text/html' : '*/*' },
      }, kind === 'page' ? owner : null)
      if (signal.aborted) { discard(response); signal.throwIfAborted() }
      if (expired()) { discard(response); throw new Stopped('The check ran out of time.') }
      ttfb += clock.now() - sent
      const result = { url: url.href, status: response.status, hops, ttfb, xRobots: response.headers.get('X-Robots-Tag') || '' }
      if (response.status >= 300 && response.status < 400) {
        const destination = response.headers.get('Location')
        discard(response)
        if (!destination || hops >= MAX_REDIRECTS) return { ...result, error: true }
        try { url = checkTarget(new URL(destination, url)) } catch { return { ...result, error: true } }
        hops++
        continue
      }
      if (kind === 'http' || response.status < 200 || response.status >= 300) {
        discard(response)
        return result
      }
      const type = (response.headers.get('Content-Type') || '').toLowerCase().split(';')[0].trim()
      if (kind === 'page' && type !== 'text/html') { discard(response); return { ...result, nonHtml: true } }
      const body = await readCapped(response, MAX_PAGE_BYTES, signal)
      signal.throwIfAborted()
      return { ...result, body, type }
    }
  }

  function getPolicy(origin, parent) {
    if (!policies.has(origin)) {
      const pending = resource(async (signal) => {
        const result = await requestChain(new URL('/robots.txt', origin), 'robots', signal)
        const missing = result.status === 404 || result.status === 410
        if (missing && !result.error) return { safe: true, found: false, parsed: parseRobots('') }
        const readable = result.status >= 200 && result.status < 300 && result.body && !result.body.truncated &&
          result.type !== 'text/html' && !/^\s*<(!doctype|html)/i.test(result.body.text) && !result.body.text.includes('\ufffd')
        const parsed = parseRobots(readable ? result.body.text : '')
        const rules = parsed.groups.filter((group) => group.wildcard || group.agents.includes('checkenginebot'))
          .flatMap((group) => group.rules)
        // The shared evaluator uses regular expressions. Refuse patterns that
        // could cause excessive backtracking before ever evaluating a path.
        const boundedRules = rules.length <= MAX_ROBOTS_RULES && rules.every((rule) =>
          rule.pattern.length <= MAX_ROBOTS_PATTERN_LENGTH && rule.pattern.split('*').length - 1 <= MAX_ROBOTS_WILDCARDS)
        const safe = readable && parsed.warnings.length === 0 && boundedRules
        return { safe: Boolean(safe), found: Boolean(readable), parsed, refused: [401, 403, 429].includes(result.status) }
      }, parent)
      // Cache only in this check's memory. Failed policies stay failed.
      policies.set(origin, pending)
    }
    return policies.get(origin)
  }

  const result = (message) => {
    for (const page of records) page.linked = linked.has(canonical(page.url))
    return {
      site: normalOrigin(start), pages_checked: records.filter((page) => page.data).length,
      truncated, blocked_by_robots: blocked.size,
      ...rank(checks(records, { robotsFound, sitemapFound, httpUpgrades, attempts: tried.size, blocked: [...blocked] })),
      robots: { found: robotsFound, sitemap_found: sitemapFound === true },
      checked_at: new Date(began).toISOString(), took_ms: clock.now() - began, from_cache: false,
      ...(message ? { message } : {}),
    }
  }

  // DNS failure here is a bad address. A failed robots request refuses all
  // crawling. There are no page or sitemap requests before this succeeds.
  let firstPolicy
  try { firstPolicy = await getPolicy(start.origin) } catch (error) {
    if (error instanceof BadAddress) throw error
    truncated = true
    return result('The site could not be checked safely. Try again later.')
  }
  robotsFound = firstPolicy.found
  if (!firstPolicy.safe) return result(firstPolicy.refused ? refused : 'The robots.txt rules could not be read safely.')
  if (!allowed(firstPolicy, start)) {
    blocked.add(start.href)
    return result(refused)
  }

  function admitVariant(key) {
    const path = new URL(key).pathname
    const variants = pathVariants.get(path) || new Set()
    if (variants.has(key)) return true
    if (variants.size >= MAX_URLS_PER_PATH) { truncated = true; return false }
    variants.add(key)
    pathVariants.set(path, variants)
    return true
  }

  function enqueue(address, list, isLinked = false) {
    let url
    let key
    try { url = checkTarget(address); key = canonical(url) } catch { return }
    if (seen.has(key) || fetched.has(key)) {
      if (isLinked) linked.add(key)
      return
    }
    if (seen.size >= MAX_DISCOVERED_URLS) { truncated = true; return }
    if (!admitVariant(key)) return
    seen.add(key)
    if (isLinked) linked.add(key)
    // Deduplicate by the normal form, but request the first address as given.
    list.push(url)
  }

  async function pageTask(url) {
    if (expired()) { truncated = true; return null }
    attempts++
    try {
      const page = await resource(async (signal) => {
        const got = await requestChain(url, 'page', signal)
        if (got.blocked || (got.duplicate && got.hops === 0)) return null
        if (got.error || got.nonHtml || !got.body) {
          if (got.error) truncated = true
          return { ...got, data: null }
        }
        if (got.body.truncated) { truncated = true; return { ...got, body: undefined, data: null } }
        const data = await extract(got.body.text)
        signal.throwIfAborted()
        if (expired()) throw new Stopped('The check ran out of time.')
        return { ...got, body: undefined, data }
      })
      return page ? { ...page, requested: url.href } : null
    } catch {
      truncated = true
      return { url: url.href, data: null, hops: 0 }
    }
  }

  let level = []
  enqueue(start, level)
  let stop = false
  while (level.length && attempts < MAX_PAGES && !expired() && !stop) {
    const next = []
    for (let i = 0; i < level.length && !stop; i += CONCURRENCY) {
      if (attempts >= MAX_PAGES || expired()) { truncated = true; break }
      const batch = level.slice(i, i + Math.min(CONCURRENCY, MAX_PAGES - attempts))
      const pages = await Promise.all(batch.map(pageTask))
      for (const page of pages) {
        if (!page) continue
        // The first address must succeed before links or optional probes run.
        if (records.length === 0 && [401, 403, 429].includes(page.status)) return result(refused)
        records.push(page)
        if (!page.data) continue
        if (page.data.linksTruncated) truncated = true
        let base = page.url
        try { if (page.data.base) base = new URL(page.data.base, base).href } catch { /* Keep the page base. */ }
        for (const link of page.data.links || []) {
          try { enqueue(new URL(link, base), next, true) } catch { /* Ignore unusable links. */ }
        }
      }
      if (pages.some((p) => p && [401, 403, 429].includes(p.status))) stop = true
      if (attempts >= MAX_PAGES && i + batch.length < level.length) truncated = true
    }
    level = next
  }
  if (level.length || expired() || stop) truncated = true
  if (!records.some((page) => page.data)) return result('No complete HTML pages could be read safely.')
  if (start.protocol === 'http:') httpUpgrades = records[0].url.startsWith('https:') && records[0].hops > 0

  // These probes are deliberately after the first page and share its deadline,
  // robots rules, redirect policy, DNS checks, timeout and polite request queue.
  if (!expired() && !stop) {
    try {
      const sitemap = await resource((signal) => requestChain(new URL('/sitemap.xml', start.origin), 'sitemap', signal))
      if (sitemap.status === 404 || sitemap.status === 410) sitemapFound = false
      else if (sitemap.body) sitemapFound = sitemap.status >= 200 && sitemap.status < 300 &&
        /<(?:[a-z]+:)?(?:urlset|sitemapindex)(?:\s|>)/i.test(sitemap.body.text) && sitemap.type !== 'text/html'
    } catch { truncated = true }
    if (start.protocol === 'https:' && !expired()) {
      try {
        const http = new URL('/', start)
        http.protocol = 'http:'
        const probe = await resource((signal) => requestChain(http, 'http', signal))
        if (!probe.blocked && !probe.error && probe.status) httpUpgrades = probe.url.startsWith('https:') && probe.hops > 0
      } catch { truncated = true }
    }
  }
  if (expired()) truncated = true
  return result()
}
