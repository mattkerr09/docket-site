/**
 * robots.txt, read the way RFC 9309 says crawlers read it.
 *
 * A port of the rules Docket's own parser applies (docket-app,
 * backend/seo_engine/robots.py), so the free checker and the product give the
 * same answer for the same file. Where the two differ, a test says so.
 *
 * What it does, and where each rule comes from:
 *   - Groups start at a User-agent line; consecutive User-agent lines share
 *     one group; blank lines and comments do not end a group (RFC 9309 §2.2).
 *   - A written user-agent value is cut at the first character outside
 *     [A-Za-z_-], as Google's open-source parser does, so
 *     `User-agent: ChatGPT-User/2.0` addresses ChatGPT-User.
 *   - A crawler obeys every group that names it, merged; only if none does,
 *     every `*` group, merged (§2.2.1). Cloudflare's managed block and a
 *     site's own `*` group are one set of rules, not a race.
 *   - The longest matching path wins; on a tie, Allow wins (§2.2.2).
 *     `*` matches any run of characters and a trailing `$` anchors the end.
 *   - An empty `Disallow:` blocks nothing.
 *
 * Pure: no network, no globals. The worker fetches; this reads.
 */

/** Only these characters count in a product token (RFC 9309 §2.2.1). */
const TOKEN = /^[A-Za-z_-]*/

export function truncateAgent(value) {
  return (String(value || '').trim().match(TOKEN) || [''])[0]
}

/** Is this written user-agent value the wildcard? Google: `*` then end or space. */
function isWildcard(value) {
  const v = String(value || '').trim()
  return v === '*' || /^\*\s/.test(v)
}

/**
 * Percent-encode what RFC 3986 says must be encoded, and upper-case every
 * existing escape, so `/caf%c3%a9` and `/café` compare equal.
 */
export function normalisePath(path) {
  let out = ''
  const bytes = new TextEncoder().encode(String(path || ''))
  for (let i = 0; i < bytes.length; i++) {
    const b = bytes[i]
    if (b === 0x25 && i + 2 < bytes.length &&
        /[0-9a-fA-F]/.test(String.fromCharCode(bytes[i + 1])) &&
        /[0-9a-fA-F]/.test(String.fromCharCode(bytes[i + 2]))) {
      out += '%' + String.fromCharCode(bytes[i + 1], bytes[i + 2]).toUpperCase()
      i += 2
    } else if (b > 0x7e || b <= 0x20) {
      out += '%' + b.toString(16).toUpperCase().padStart(2, '0')
    } else {
      out += String.fromCharCode(b)
    }
  }
  return out
}

function patternRegex(pattern) {
  const anchored = pattern.endsWith('$')
  const body = anchored ? pattern.slice(0, -1) : pattern
  const escaped = normalisePath(body)
    .split('*')
    .map((part) => part.replace(/[.+?^${}()|[\]\\]/g, '\\$&'))
    .join('.*')
  return new RegExp('^' + escaped + (anchored ? '$' : ''))
}

/**
 * Parse a robots.txt body.
 * @returns {{groups: {agents: string[], wildcard: boolean, rules: {allow: boolean, pattern: string}[]}[],
 *            sitemaps: string[], warnings: string[]}}
 */
export function parseRobots(text) {
  const groups = []
  const sitemaps = []
  const warnings = []
  let current = null
  let expectingAgents = false

  const lines = String(text || '').replace(/^﻿/, '').split(/\r\n|\r|\n/)
  for (const raw of lines) {
    const line = raw.split('#', 1)[0].trim()
    if (!line) continue
    const colon = line.indexOf(':')
    if (colon === -1) {
      if (warnings.length < 20) warnings.push(`Not a robots.txt line, ignored: ${raw.trim().slice(0, 80)}`)
      continue
    }
    const key = line.slice(0, colon).trim().toLowerCase()
    const value = line.slice(colon + 1).trim()

    if (key === 'user-agent') {
      if (!current || !expectingAgents) {
        current = { agents: [], wildcard: false, rules: [] }
        groups.push(current)
        expectingAgents = true
      }
      if (isWildcard(value)) current.wildcard = true
      else {
        const token = truncateAgent(value).toLowerCase()
        if (token) current.agents.push(token)
      }
      continue
    }
    if (key === 'sitemap') {
      if (value) sitemaps.push(value)
      continue
    }
    if (key !== 'allow' && key !== 'disallow') continue // crawl-delay etc.: not in the RFC
    if (!current) {
      if (warnings.length < 20) warnings.push(`'${line.slice(0, colon).trim()}' comes before any User-agent line, so no crawler reads it`)
      continue
    }
    expectingAgents = false
    if (value) current.rules.push({ allow: key === 'allow', pattern: value })
  }
  return { groups, sitemaps, warnings }
}

/**
 * Which rules a crawler obeys: every group naming it, else every `*` group.
 * `named` says whether the file addresses this crawler by name.
 */
export function rulesFor(parsed, agent) {
  const token = String(agent || '').toLowerCase()
  const named = parsed.groups.filter((g) => g.agents.includes(token))
  if (named.length) return { named: true, rules: named.flatMap((g) => g.rules) }
  const wild = parsed.groups.filter((g) => g.wildcard)
  return { named: false, wildcard: wild.length > 0, rules: wild.flatMap((g) => g.rules) }
}

/**
 * May `agent` fetch `path`? Longest match wins; Allow wins a tie.
 * Specificity is the pattern's length without a trailing `$`, as in Docket.
 */
export function evaluate(parsed, agent, path = '/') {
  const target = normalisePath(path || '/')
  const { named, wildcard, rules } = rulesFor(parsed, agent)
  let best = null
  for (const rule of rules) {
    if (!patternRegex(rule.pattern).test(target)) continue
    const len = rule.pattern.replace(/\$$/, '').length
    if (!best || len > best.len || (len === best.len && rule.allow && !best.rule.allow)) {
      best = { len, rule }
    }
  }
  return {
    agent,
    allowed: best ? best.rule.allow : true,
    named,
    governedBy: named ? 'name' : (wildcard ? 'wildcard' : 'none'),
    rule: best ? `${best.rule.allow ? 'Allow' : 'Disallow'}: ${best.rule.pattern}` : null,
  }
}
