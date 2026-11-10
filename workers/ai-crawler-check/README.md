# ai-crawler-check

The server half of the free AI crawler checker at
<https://docketseo.app/tools/ai-crawler-checker/>. A browser cannot read another
site's robots.txt, so this Worker fetches it and says, per crawler, whether the
file lets it in.

```
GET /check?url=example.com&agents=GPTBot,OAI-SearchBot&path=/
GET /health
```

## What it does and does not do

- Reads **robots.txt only**, with the rules in `src/robots.js`: a port of
  Docket's own parser (docket-app `backend/seo_engine/robots.py`), following
  RFC 9309.
  - Groups are merged.
  - The longest match wins, and Allow wins a tie.
  - A user-agent value is cut at the first invalid character, as Google does.
- RFC 9309 status rules:
  - 4xx means no file, so everyone may crawl.
  - 5xx or no answer means nobody should crawl.
  - 429 is treated like a server error, as Google does, and the response says so.
- Never requests a page as a crawler and never claims to be one. It sends
  `User-Agent: DocketRobotsCheck/1.0 (+https://docketseo.app/tools/ai-crawler-checker/)`.
- Stores no site address or check result. See the anonymous count route below.

## Safety

Anyone can type any address into the page, so the Worker refuses:

- anything but http(s);
- `user:pass@`;
- non-default ports;
- IP literals in every notation (dotted, decimal, hex, octal, IPv6);
- single-label, localhost and private-use names.

It only fetches `/robots.txt` on the given host. It follows at most five
redirects, re-checking each hop. It reads 512 KiB at most, times out after
8 s, and caches each file at the edge for 10 minutes.

A public name that resolves to a private address, such as a rebinding DNS
service, is not caught by the name checks. Cloudflare's network does not
route Worker subrequests to private address space, which is the backstop.

For the browser check routes, CORS answers only `https://docketseo.app`. Any other `Origin` gets a 403.

Per-IP limit: 20 checks a minute per `CF-Connecting-IP`, then a 429 with
`Retry-After: 60` and a plain sentence the page shows. It uses the
`CHECK_LIMITER` rate-limiting binding in wrangler.toml. If the account cannot
create that binding, delete the block; the Worker then falls back to a per-IP
counter in the Cache API. That counter is per data centre and approximate,
which is enough to stop a flood.

## Anonymous app counts

`GET /app-event?e=first_opened&v=1.3.161&os=mac` counts one of `first_opened`,
`first_audit_finished` or `free_limit`. Versions must have three numeric parts
of one to three digits each; systems are `mac`, `windows` or `linux`.
Each required field must appear once. Other query parameters are ignored.
GET always returns an empty 204 with `Cache-Control: no-store`, including for
invalid input. Other methods return 405. This app route skips Origin checks
and sets no CORS headers or cookies.

It stores daily counts by event, version and system in the same Durable Object
as the MCP tallies. It logs no requests and forwards no request headers to that
store. Only the existing limiter binding is used, with no IP cache fallback.
Read the `app:` keys in `/mcp/stats` with the existing `X-Stats-Key` header.
See [the server notes](../../docs/APP_COUNTS_SITE.md) for keys, retention and the
separate app job's responsibilities.

## Test and deploy

```
npm test                 # node --test, no dependencies
npx wrangler deploy      # from the Mac, with the account's credentials
curl -s 'https://ai-crawler-check.kerrco.workers.dev/check?url=docketseo.app&agents=GPTBot'
```
