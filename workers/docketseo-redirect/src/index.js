export const MODE = 'passthrough'
const DESTINATION_HOST = 'checkengineseo.com'
const RAW_ORIGIN = 'https://raw.githubusercontent.com/mattkerr09/docket-site/gh-pages'
const PASSTHROUGH = ['/updater.json', '/offer.json', '/data/knowledge.json', '/bot', '/bot/', '/assets/docket-sample-report.pdf']
const PREFIXES = ['/updates/', '/bot/']

const FORWARDED_HEADERS = ['Range', 'If-Range', 'If-None-Match', 'If-Modified-Since', 'If-Match', 'If-Unmodified-Since', 'Accept']
const CONTENT_TYPES = { json: 'application/json; charset=utf-8', pdf: 'application/pdf', html: 'text/html; charset=utf-8', gz: 'application/gzip', tgz: 'application/gzip', exe: 'application/octet-stream' }
const MOVING = 'Check Engine SEO (formerly Docket SEO) is moving to https://checkengineseo.com. Please try again in a few minutes.'

function passthrough(request) {
  return fetch(request)
}

function isAppPath(path) {
  return PASSTHROUGH.includes(path) || PREFIXES.some((prefix) => path.startsWith(prefix))
}

async function proxy(request, destination, fallbackPath) {
  const servedBy = fallbackPath ? 'docketseo-redirect-fallback' : 'docketseo-redirect'
  const headers = new Headers()
  for (const name of FORWARDED_HEADERS) {
    if (request.headers.has(name)) headers.set(name, request.headers.get(name))
  }

  try {
    const origin = await fetch(destination, { method: request.method, headers, redirect: 'follow' })
    // Follow origin redirects inside the Worker. Never send an updater away.
    if (origin.status >= 500 || (origin.status >= 300 && origin.status < 400 && origin.status !== 304)) {
      if (origin.body) await origin.body.cancel()
      throw new Error('Origin unavailable')
    }
    const responseHeaders = new Headers(origin.headers)
    responseHeaders.set('X-Served-By', servedBy)
    if (fallbackPath) {
      const extension = fallbackPath.split('.').pop().toLowerCase()
      responseHeaders.set('Content-Type', Object.hasOwn(CONTENT_TYPES, extension) ? CONTENT_TYPES[extension] : 'application/octet-stream')
      responseHeaders.set('Cache-Control', 'public, max-age=300')
      responseHeaders.delete('Location')
    }
    return new Response(request.method === 'HEAD' ? null : origin.body, {
      status: origin.status,
      statusText: origin.statusText,
      headers: responseHeaders,
    })
  } catch {
    return new Response(request.method === 'HEAD' ? null : 'Origin unavailable\n', {
      status: 502,
      headers: {
        'Content-Type': 'text/plain; charset=utf-8',
        'Cache-Control': 'no-store',
        'X-Served-By': servedBy,
      },
    })
  }
}

function fallback(request, url) {
  if (!isAppPath(url.pathname)) {
    return new Response(request.method === 'HEAD' ? null : MOVING, {
      status: 503,
      headers: { 'Retry-After': '300', 'Cache-Control': 'no-store', 'Content-Type': 'text/plain; charset=utf-8' },
    })
  }
  let path = url.pathname === '/bot' ? '/bot/' : url.pathname
  if (path.endsWith('/')) path += 'index.html'
  // Keep the original query suffix, including escapes and an empty query.
  const query = request.url.includes('?') ? request.url.slice(request.url.indexOf('?')) : ''
  return proxy(request, `${RAW_ORIGIN}${path}${query}`, path)
}

function redirect(request, url) {
  // Use the original suffix to retain escapes, query order and an empty query.
  const destination = request.url.replace(/^https?:\/\/[^/]+/, `https://${DESTINATION_HOST}`)
  if (!isAppPath(url.pathname)) return new Response(null, { status: 301, headers: { Location: destination } })
  return proxy(request, destination)
}

export function makeHandler(mode) {
  return {
    async fetch(request) {
      if (mode === 'passthrough') return passthrough(request)
      if (mode !== 'fallback' && mode !== 'redirect') {
        return new Response(request.method === 'HEAD' ? null : 'bad MODE', {
          status: 500,
          headers: { 'Content-Type': 'text/plain; charset=utf-8', 'Cache-Control': 'no-store' },
        })
      }
      const url = new URL(request.url)
      const allowed = url.pathname === '/__redirect-health' ? 'GET' : 'GET, HEAD'
      if (!allowed.split(', ').includes(request.method)) {
        return new Response(request.method === 'HEAD' ? null : 'Method not allowed\n', {
          status: 405,
          headers: { Allow: allowed, 'Content-Type': 'text/plain; charset=utf-8' },
        })
      }
      if (url.pathname === '/__redirect-health') {
        return new Response('ok', {
          headers: { 'Content-Type': 'text/plain; charset=utf-8', 'Cache-Control': 'no-store', 'X-Mode': mode },
        })
      }
      return mode === 'fallback' ? fallback(request, url) : redirect(request, url)
    },
  }
}

export default makeHandler(MODE)
