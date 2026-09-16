# Check-explainer candidate pool — one page per shipped check with no page

Source: `docket checks` from the INSTALLED 1.3.64 binary, cross-referenced
against the LIVE sitemap (not memory). Each page's measurement is the check
itself: its thresholds, severity and fix text are readable at source, so no
new survey is needed and nothing has to be invented.


## Crawlability & indexing
- `index.robots_blocks_all` — robots.txt blocks the whole site
- `index.broken` — Broken pages (4xx/5xx)
- `index.redirects` — Redirect problems
- `index.soft_404_pages` — Soft 404 pages in the crawl
- `index.depth` — Click depth and orphans
- `index.url_hygiene` — URL structure
- `index.byte_cap` — Googlebot's 2MB fetch limit
- `index.meta_refresh` — Client-side redirects
- `intl.hreflang_self` — hreflang self-reference
- `intl.hreflang_codes` — hreflang language codes
- `intl.hreflang_targets` — hreflang target health

## On-page SEO
- `onpage.description` — Meta descriptions
- `onpage.headings` — Heading structure
- `onpage.images` — Image optimisation
- `onpage.anchors` — Internal link anchor text

## Content quality
- `content.language_scope` — Language coverage
- `content.thin` — Thin content
- `content.placeholder` — Placeholder content
- `content.readability` — Readability
- `content.ai_slop` — Generic AI-sounding copy
- `content.dates` — Freshness signals
- `content.eeat` — Trust and authorship signals
- `content.topic_gaps` — Topics worth writing about

## Speed & Core Web Vitals
- `perf.ttfb` — Server response time
- `perf.page_weight` — Page weight
- `perf.render_blocking` — Render-blocking resources
- `perf.compression` — Compression and caching headers
- `perf.cls_risk` — Layout shift risk
- `perf.redirect_cost` — Redirect latency
- `perf.modern_images` — Image formats

## Structured data
- `schema.invalid` — Invalid JSON-LD
- `schema.incomplete` — Incomplete structured data
- `schema.price` — Schema price vs visible price
- `schema.opportunity` — Rich result opportunities

## Links
- `links.internal_volume` — Internal linking
- `links.broken_external` — Broken outbound links
- `links.outbound_quality` — Outbound link handling
- `links.pagination` — Pagination handling
- `links.nav_not_in_html` — Navigation reachable without JavaScript

## Security & trust
- `security.mixed_content` — Mixed content

## Social & sharing
- `social.twitter` — Twitter/X card
- `social.favicon` — Favicon

## Local business SEO
- `local.applicable` — Local business detection
- `local.schema` — LocalBusiness schema
- `local.geo_targeting` — Location targeting in content
- `local.reviews` — Review signals

## AI search visibility
- `ai.edge_access` — Server access for AI crawlers
- `ai.unmeasurable_optout` — The AI control nothing can detect
- `ai.extractability` — Answer extractability
- `ai.citable_facts` — Citable, specific claims
- `ai.llms_txt` — llms.txt
- `ai.freshness_signal` — Dates AI engines can read

## Conversion & landing pages
- `cvr.value_prop` — Above-the-fold value proposition
- `cvr.form_friction` — Form friction
- `cvr.social_proof` — Social proof
- `cvr.pricing` — Pricing transparency
- `cvr.funnel` — Funnel coverage
- `cvr.message_match` — Title / headline consistency
- `cvr.unusable_phone` — Phone links that will not dial

## Tracking & campaign readiness
- `mar.analytics` — Analytics installed
- `mar.ad_pixels` — Advertising pixels
- `mar.consent` — Consent and privacy compliance
- `mar.utm_hygiene` — UTM tagging hygiene
- `mar.email_capture` — Email list building
- `mar.stack` — Marketing stack inventory

## Brand consistency
- `brand.name_consistency` — Brand name consistency
- `brand.logo` — Logo presence and markup
- `brand.visual_consistency` — Typography and colour consistency
- `brand.positioning` — Consistent positioning statement
- `brand.voice_consistency` — Writing voice consistency
- `brand.social_consistency` — Social profile consistency

## Killed, and why — do not re-propose without new evidence

- **Cookie consent banners** — killed.
- **Schema price vs visible price** — killed (`schema.price` stays off this list).
- **Orphan pages / click depth as a research page** — killed as research; the
  check-explainer for `index.depth` is still open.
- **Publish dates** — measured and killed: 32 of 36 hosts clean.
- **The six AI-crawler research candidates** — measured and killed: 0 of 6 passed.
- **`dead_ai_directives.py`** — killed.

## The two-sided test still applies to every line above

A check having no page is one side. The other is whether a reader is actually
asking, and whether the answer is winnable. Crisp has 121 pages with 19
indexed, which is what volume without winnability buys. A candidate that fails
the second side gets struck from this file with the reason, not quietly skipped.
