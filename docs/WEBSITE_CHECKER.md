# Free website checker Worker

`GET /site-check?url=<address>` runs a quick check from the given address. It follows HTML links breadth first on one host. Apex and www count as one site. Each origin gets a robots check. Both bot-specific and wildcard rules must allow the request. Robots denial or a first page answering 401, 403 or 429 stops the check. Only `https://checkengineseo.com` may call it. Missing Origin is refused.

JSON summaries give pages read, robots skips, top issues and passing checks. Checks cover titles, descriptions, H1s, canonical and noindex tags, linked noindex pages, HTTP errors, chains, image alt, viewport, language, Open Graph, schema tags, thin text, slow headers, robots, sitemap and HTTPS. There is no site score. Counts use HTML pages read, HTTP addresses tried, or robots skips as labelled. Partial HTML is skipped. Unknown probes make no missing-file claim. Sitemap checks inspect `/sitemap.xml`. Extra HTTPS probes use HEAD on the root path. Schema checks find tags. Words are space-separated HTML text without scripts, styles or templates. Response time sums time to headers across redirects.

## Limits

All bounds are in `workers/site-check/src/limits.js`. Title bounds are re-exported from the existing page checker.

| Constants | Values |
| --- | --- |
| `MAX_PAGES`, `CONCURRENCY`, `REQUEST_PAUSE_MS` | 25 page addresses tried, 4 page tasks, 100 ms between target request starts |
| `PAGE_TIMEOUT_MS`, `DEADLINE_MS` | 8 seconds per resource including redirects and body reads, 30 seconds per crawl |
| `MAX_PAGE_BYTES`, `MAX_REDIRECTS` | 1 MiB per body, 5 redirect hops |
| `MAX_URLS_PER_PATH`, `MAX_DISCOVERED_URLS`, `MAX_ADDRESS_LENGTH` | 3 URL forms per path including redirects, 250 queued URLs or links per page, 2048 address characters |
| `MAX_ROBOTS_RULES`, `MAX_ROBOTS_PATTERN_LENGTH`, `MAX_ROBOTS_WILDCARDS` | 256 applicable rules, 512 characters per pattern, 1 wildcard per pattern |
| `VISITOR_DAILY_CAP`, `HOST_DAILY_CAP`, `HOST_INTERVAL_MS` | 5 per visitor per day, 3 per host per day, one per host per minute |
| `GLOBAL_DAILY_CAP`, `DAY_MS`, `LEASE_MS` | 1500 per UTC day, 86400000 ms per day, one active visitor lease for up to 45 seconds |
| `COUNTER_TIMEOUT_MS`, `CACHE_TIMEOUT_MS` | 2000 ms per counter call, 1000 ms per cache operation |
| `CACHE_TTL_S`, `MAX_SUMMARY_BYTES`, `MAX_COUNTER_BYTES` | 3600 seconds, 32768 summary bytes, 1024 counter request or response bytes |
| `DNS_MAX_BYTES`, `PURGE_BATCH` | 65536 bytes per DNS answer, 128 old keys per delete batch |
| `MAX_ISSUES`, `MAX_FINE`, `MAX_EXAMPLES` | 8 issues, 5 passing items, 3 path examples per item |
| `TITLE_MIN`, `TITLE_MAX`, `THIN_WORDS`, `SLOW_TTFB_MS` | 25 and 65 title width units, under 100 words, over 1500 ms |

The byte cap stops without reading an extra chunk. An exactly full HTML body is treated as partial. The crawl also stops at UTC midnight so visitor leases cannot carry across days. Caps include cache hits and accepted checks that fail later. `USER_AGENT` is `CheckEngineBot/1.0 (+https://checkengineseo.com/bot/)`. Only HTTP port 80 and HTTPS port 443 are accepted.

## Storage and controls

One `SiteCheckCounters` object named `global` grants all limits in one transaction. Day keys hold counts, timestamps, lease tokens and SHA-256 hashes. Visitor hashes include the connection address, UTC date and `HASH_LABEL`. Host hashes include the host, date and label. An alarm and counter calls purge old days. Any counter error refuses work. Stale releases cannot unlock newer leases.

The Cache API stores summary JSON for one hour under a hash of the normalised origin. Start paths share a summary. Examples omit queries. Bodies, full crawl address lists, raw connection addresses, incoming User-Agents, cookies and credentials are never stored. Queues stay in request memory. Fetch caching and Worker observability are off. The code logs nothing.

Set `SITE_CHECK_DISABLED` to `1` to stop before counters, cache or fetch. The config keeps it on pending host safety review. Change `GLOBAL_DAILY_CAP` to adjust the daily budget. No secret is needed. The host adds routes.

## Abuse model and host review

Floods and query traps face atomic visitor, host and global caps. Redirect checks, bounded robots rules, time and byte caps bound work. Complex or malformed robots files are refused. Private names, IP literals and non-web ports are refused. Every target request gets public A and AAAA validation. Failed, empty or mixed private DNS answers are refused. The fixed HTTPS resolver `cloudflare-dns.com/dns-query` is the only off-site fetch.

DNS preflight cannot pin the IP used by Worker fetch. Keep the switch on until the host confirms Cloudflare blocks private destinations after DNS changes, or adds a pinned transport. Tests fake fetch, streams, DNS, storage, cache, clock and HTMLRewriter events. Native HTMLRewriter, edge caching, alarms and provider request logs need host review.
