import { BASE } from './site-brand.js'

// One switch disables guide text, structured URLs and guide counts together.
export const GUIDE_LINKS = true

// Checked against the local guide pages. Keep unsupported findings unmapped rather than linking a near miss.
export const GUIDES = [
  { label: /^(No title tag|The title tag is empty|Long title:|Short title:)/, path: '/how-to/write-title-tags-that-fit/' },
  { label: /^(No meta description|The meta description is empty|Long description:|Short description:)/, path: '/how-to/write-meta-descriptions/' },
  { label: /^\d+ canonical tags that disagree$/, path: '/how-to/fix-conflicting-canonicals/' },
  { label: /^(No canonical tag|Canonical points to another address|The canonical is a relative address)$/, path: '/learn/canonical-tags/' },
  { label: /^No H1 heading$/, path: '/how-to/fix-heading-structure/' },
  { label: /^No language declared$/, path: '/how-to/fix-lang-attribute-mismatch/' },
  { label: /^No viewport tag$/, path: '/how-to/check-mobile-seo-from-a-crawl/' },
  { label: /^No (og:|twitter:)/, path: '/how-to/fix-missing-open-graph-tags/' },
  { label: /^(The page is not served over HTTPS|The page ends up on plain http|Served over plain http)$/, path: '/how-to/redirect-http-to-https/' },
  { label: /^(Redirect loop|More than \d+ redirects|\d+ redirects before the page|\d+ temporary redirects? \([\d, ]+\))$/, path: '/how-to/fix-redirect-problems/' },
  { label: /^Block \d+ is not valid JSON$/, path: '/how-to/json-ld-parser-errors/' },
  { area: 'Structured data', label: / is missing /, path: '/how-to/fix-structured-data-errors/' },
  { label: /^\d+ of \d+ AI search crawlers are blocked$/, path: '/how-to/fix-ai-crawler-access/' },
  { label: /^(No HSTS header|Missing \d+ baseline security headers?)$/, path: '/how-to/fix-missing-security-headers/' },
  // No current MCP check emits these; do not infer a fault from a raw header's absence.
  { label: /^(No caching headers|No compression)$/, path: '/how-to/fix-compression-and-caching/' },
]

export function guidePath(finding) {
  if (!finding) return null
  if (finding.allowed === false && finding.rule) return '/how-to/fix-ai-crawler-access/'
  return GUIDES.find((g) => (!g.area || g.area === finding.area) && g.label.test(finding.label || ''))?.path || null
}

// The check supplies its first fix and its text line. Never fall through to a less important mapped finding.
export function addGuide(out, family) {
  if (!GUIDE_LINKS || family !== 'claude') return false
  const { finding, after } = out.guide || {}
  if (!finding || !(finding.level === 'problem' || finding.level === 'warning' || finding.allowed === false)) return false
  const path = guidePath(finding)
  if (!path) return false
  const url = `${BASE}${path}?utm_source=claude-connector`
  const lines = out.text.split('\n')
  lines.splice(after + 1, 0, `How to fix it, step by step: ${url}`)
  out.text = lines.join('\n')
  finding.guide_url = url
  return true
}
