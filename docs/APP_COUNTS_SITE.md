# Anonymous app counts: server half

`GET https://mcp.docketseo.app/app-event?e=first_opened&v=1.3.161&os=mac`
adds one to each of three daily tallies in the existing `DAILY_CAP` Durable Object named
`global`. The allowed events are `first_opened`, `first_audit_finished` and
`free_limit`. A version has three dot-separated parts, each with one to three
ASCII digits. The system is `mac`, `windows` or `linux`. Missing, repeated or
invalid fields count nothing. Other query parameters are ignored.

The route returns an empty 204 with `Cache-Control: no-store` whether or not it
counts. Other methods get 405. It neither checks Origin nor adds CORS headers.
It reuses `CHECK_LIMITER` when that binding and an IP are available. It does not
use the IP cache fallback. There is no request logging in this route.

The stored keys are `t:YYYY-MM-DD:app:<event>`,
`t:YYYY-MM-DD:app:<event>:<version>` and `t:YYYY-MM-DD:app:<event>:<system>`.
Each value is an integer count. No headers, IP, user agent, site address,
result, licence key, ID or visitor record goes into this store. Cloudflare
receives the network request and sees its IP while answering it. The existing
rate limiter handles the IP separately from the tally store.

Read the numbers with `GET /mcp/stats` on the same host, using the existing
`X-Stats-Key` header set to `STATS_KEY`. Missing or wrong keys still get 404.
The `outcomes` object contains the `app:` counts beside the MCP `tool:outcome`
counts. The existing stats reader sums daily rows from its 35-day cutoff and
deletes older rows when read. Counts are best effort, like the MCP tallies:
missing or failed storage does not change the public 204.

The separate docket-app job owns sending each event once per copy, source-build
and offline suppression, `DOCKET_NO_COUNTS=1`, and the empty `~/.docket/no-counts`
file. The server cannot enforce once per copy without an ID and does not try.
Repeated requests can increase a tally. The privacy section in
`scripts/articles/pages.py` describes this agreed app contract. Coordinate the
app and site releases so those promises hold when the page goes live.

Run the local gate from the repository root:

```
cd workers/ai-crawler-check && npm test && cd ../.. && python3 scripts/test_app_counts_privacy.py
```

The privacy test builds both site brands in scratch copies with
`DOCKET_SKIP_BRAND_ASSETS=1` and `TZ=UTC`. This job does not deploy the Worker.
