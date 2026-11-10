import { MAX_ADDRESS_LENGTH, DNS_MAX_BYTES } from './limits.js'
import { readCapped, discard } from './io.js'
import { unsafeHost as baseUnsafeHost, siteFrom as baseSiteFrom } from '../../ai-crawler-check/src/index.js'

export class BadAddress extends Error {}

export function unsafeHost(hostname) {
  const why = baseUnsafeHost(hostname)
  if (why) return why
  const h = String(hostname || '').toLowerCase().replace(/\.$/, '')
  if (!h.split('.').every((label) => /^[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?$/.test(label))) return 'not a valid host name'
  return null
}

export function siteFrom(input) {
  const raw = String(input || '').trim()
  if (raw.length > MAX_ADDRESS_LENGTH) throw new BadAddress('That website address is too long.')
  let u
  try { u = baseSiteFrom(raw) } catch (error) { throw new BadAddress(error.message) }
  const why = unsafeHost(u.hostname)
  if (why) throw new BadAddress(`That address is ${why}.`)
  u.hostname = u.hostname.replace(/\.$/, '')
  u.hash = ''
  if (u.href.length > MAX_ADDRESS_LENGTH) throw new BadAddress('That website address is too long.')
  return u
}

export const hostKey = (url) => new URL(url).hostname.replace(/^www\./, '')
export const normalOrigin = (url) => {
  const u = new URL(url)
  u.hostname = hostKey(u)
  return u.origin
}

export function canonical(address) {
  const u = siteFrom(address)
  u.hostname = hostKey(u)
  u.pathname = u.pathname.replace(/%[0-9a-f]{2}/gi, (escape) => {
    const ch = String.fromCharCode(parseInt(escape.slice(1), 16))
    return /[A-Za-z0-9._~-]/.test(ch) ? ch : escape.toUpperCase()
  })
  u.searchParams.sort()
  return u.href
}

// Fail closed for all non-global ranges. In particular, mapped IPv4, NAT64,
// 6to4, Teredo and other transition prefixes are refused, not interpreted.
export function publicAddress(address) {
  const ip = String(address).toLowerCase()
  if (ip.includes(':')) {
    if (!/^[0-9a-f:]+$/.test(ip)) return false
    try {
      const u = new URL(`http://[${ip}]/`)
      const first = parseInt(u.hostname.slice(1).split(':')[0], 16)
      if (!(first >= 0x2000 && first <= 0x3fff)) return false
      const second = parseInt(u.hostname.slice(1).split(':')[1], 16) || 0
      if (first === 0x2001 && (second <= 0x1ff || second === 0xdb8)) return false
      if (first === 0x2002 || first === 0x3fff) return false
      return true
    } catch { return false }
  }
  const parts = ip.split('.')
  if (parts.length !== 4 || parts.some((p) => !/^(0|[1-9]\d{0,2})$/.test(p) || Number(p) > 255)) return false
  const [a, b, c] = parts.map(Number)
  if (a === 0 || a === 10 || a === 127 || a >= 224) return false
  if (a === 100 && b >= 64 && b <= 127) return false
  if (a === 169 && b === 254) return false
  if (a === 172 && b >= 16 && b <= 31) return false
  if (a === 192 && (b === 0 || b === 168 || (b === 88 && c === 99))) return false
  if (a === 198 && (b === 18 || b === 19 || (b === 51 && c === 100))) return false
  if (a === 203 && b === 0 && c === 113) return false
  return true
}

export async function resolvePublic(host, resolver, signal) {
  let addresses
  try { addresses = await resolver(host, signal) } catch { throw new BadAddress('The website address could not be checked safely.') }
  signal?.throwIfAborted()
  if (!Array.isArray(addresses) || !addresses.length || !addresses.every(publicAddress)) throw new BadAddress('The website address did not resolve to public web servers.')
}

// This fixed HTTPS resolver is the only request allowed outside the target
// host. Both address families must answer successfully, even if one is empty.
// Cloudflare's fetch egress protection remains required against DNS rebinding
// between this preflight and fetch's own DNS lookup. See the review note.
export async function dnsAddresses(host, fetchImpl, signal) {
  const addresses = []
  for (const type of ['A', 'AAAA']) {
    signal?.throwIfAborted()
    const u = new URL('https://cloudflare-dns.com/dns-query')
    u.searchParams.set('name', host)
    u.searchParams.set('type', type)
    const response = await fetchImpl(u.href, {
      method: 'GET', redirect: 'manual', credentials: 'omit', signal, cache: 'no-store',
      headers: { Accept: 'application/dns-json' }, cf: { cacheTtl: 0, cacheEverything: false },
    })
    if (!response.ok) { discard(response); throw new BadAddress('The website address could not be checked safely.') }
    const body = await readCapped(response, DNS_MAX_BYTES, signal)
    if (body.truncated) throw new BadAddress('The website address could not be checked safely.')
    const data = JSON.parse(body.text)
    if (data.Status !== 0 || data.TC || (data.Answer !== undefined && !Array.isArray(data.Answer))) throw new BadAddress('The website address could not be checked safely.')
    for (const record of data.Answer || []) {
      if (record.type === 1 || record.type === 28) addresses.push(record.data)
      else if (record.type !== 5) throw new BadAddress('The website address could not be checked safely.')
    }
  }
  return addresses
}
