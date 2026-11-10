# Old Docket site Worker

One line at the top of `workers/docketseo-redirect/src/index.js` selects the mode.
The committed default is:

```js
export const MODE = 'passthrough'
```

- `passthrough` sends the original Request to `fetch(request)` and returns the
  original Response. Every path and method goes to the old site's origin. This
  includes the health path. It makes no change to site behavior.
- `fallback` serves app files from the public repo's `gh-pages` branch while the
  new domain waits for HTTPS. Other pages return 503 and ask visitors to wait.
- `redirect` serves app files from `https://checkengineseo.com`. Other pages get
  a 301 to that host with their path, query, case and escapes kept.

Any other value returns 500 with the plain body `bad MODE`. It never fetches.
HEAD error responses have no body.

## App requests

The exact app paths stay the same in fallback and redirect modes:

- `/updater.json`
- `/offer.json`
- `/data/knowledge.json`
- `/bot`
- `/bot/`
- `/assets/docket-sample-report.pdf`

Every path under `/updates/` and `/bot/` is also an app path. `/updates` without
its last slash is a page. Matching uses the path alone. Queries reach the origin.
The host and path lists remain one-line constants: `DESTINATION_HOST`,
`RAW_ORIGIN`, `PASSTHROUGH` and `PREFIXES`.

In fallback mode, the file origin is:

```text
https://raw.githubusercontent.com/mattkerr09/docket-site/gh-pages
```

The Worker adds the request path to that URL. A path ending in `/` gets
`index.html` added. Both `/bot` and `/bot/` fetch `/bot/index.html`.
The original query is kept. Raw redirects are followed inside the Worker.
The browser stays on the old host.

Raw sends some files with the wrong type for app use. Fallback mode sets the
file type from the fetched path:

| File ending | Content-Type |
| --- | --- |
| `.json` | `application/json; charset=utf-8` |
| `.pdf` | `application/pdf` |
| `.html` | `text/html; charset=utf-8` |
| `.gz`, `.tgz` | `application/gzip` |
| `.exe`, anything else | `application/octet-stream` |

Fallback responses keep the origin status and stream, including 206, 304 and
404. They keep `Content-Length`, `Content-Range`, `Accept-Ranges`, `ETag` and
`X-Content-Type-Options`. The Worker replaces raw's cache rule with
`Cache-Control: public, max-age=300` and adds
`X-Served-By: docketseo-redirect-fallback`. A file changed on `gh-pages` can take
up to five minutes to show in fallback mode. Check release files before cutover.

Every other path in fallback mode returns 503 with `Retry-After: 300`,
`Cache-Control: no-store`, no Location header and this plain body:

```text
Check Engine SEO (formerly Docket SEO) is moving to https://checkengineseo.com. Please try again in a few minutes.
```

In redirect mode, app responses keep the new origin's status, stream and
headers, including its Content-Type and Cache-Control. They have
`X-Served-By: docketseo-redirect`.

Both active modes forward Range, If-Range, If-None-Match, If-Modified-Since,
If-Match, If-Unmodified-Since and Accept. The platform controls Accept-Encoding.
File bodies stream without being read into memory. A raw 404 stays a 404.
A network error, origin 5xx or unresolved redirect gives 502 with a short plain
body, `Cache-Control: no-store` and no Location header.

Both active modes accept GET and HEAD. HEAD keeps the status and headers but
has no body. Other methods return 405 with `Allow: GET, HEAD`.
The health path is the one exception: it accepts GET only. In fallback and
redirect modes, `GET /__redirect-health` returns local body `ok`,
`Content-Type: text/plain; charset=utf-8`, `Cache-Control: no-store` and
`X-Mode: fallback` or `X-Mode: redirect`. In passthrough mode it goes to the old
origin, just like every other request.

## Four-step CEO cutover

Claude must review this code before it ships. The steps and commands below are
for the CEO after that review. This job ran offline tests only. Claude must
check current dashboard labels and DNS record values before the live work.
Never use a guessed DNS target.
Run the checks in the same terminal so the check folder and release path stay set.

### Step 1: Save the current setup and prepare the files

Record the old GitHub Pages custom domain, the apex and www DNS record types,
targets and proxy states, and both hosts' Worker routes. Save the planned
`checkengineseo.com` DNS records from the approved Pages setup too.
Confirm that all app files and release files exist on the public `gh-pages`
branch. Leave the Pages custom domain and the new domain's DNS alone for now.

Check both old hosts before making changes. Save their headers and the app
bodies so step 2 can be compared with this baseline:

```sh
CHECK_DIR=$(mktemp -d)
for host in docketseo.app www.docketseo.app; do
  curl --silent --show-error --dump-header "$CHECK_DIR/$host.page.headers" \
    --output "$CHECK_DIR/$host.page.body" "https://$host/"
  curl --silent --show-error --dump-header "$CHECK_DIR/$host.health.headers" \
    --output "$CHECK_DIR/$host.health.body" "https://$host/__redirect-health"
  curl --fail --silent --show-error --dump-header "$CHECK_DIR/$host.feed.headers" \
    --output "$CHECK_DIR/$host.feed.body" "https://$host/updater.json"
  cat "$CHECK_DIR/$host.page.headers" "$CHECK_DIR/$host.health.headers" "$CHECK_DIR/$host.feed.headers"
done
```

The pages and feed must still work on the old site. The health request shows
whatever the old origin serves at that path. Do not expect the Worker's `ok`
body or X-Mode header in passthrough mode.

Rollback: this step changes nothing.

### Step 2: Deploy passthrough, add both routes, turn on the orange proxy

Keep this exact line:

```js
export const MODE = 'passthrough'
```

In Cloudflare, open the account that owns the `docketseo.app` zone. Open
**Workers & Pages** and create or open `docketseo-redirect`. In **Edit code**,
use the full reviewed `src/index.js` module and deploy it. The repo config uses
`src/index.js` and compatibility date `2026-11-09`.

In the Worker's **Settings**, **Domains & Routes**, add two **Route** entries
in the `docketseo.app` zone. Choose **Fail closed** if asked:

```text
docketseo.app/*
www.docketseo.app/*
```

Then open the zone's **DNS**, **Records**. Keep the existing apex and www DNS
targets and turn **Proxy status** to **Proxied**, shown by the orange cloud.
Set up both routes before turning on the proxy. `mcp.docketseo.app` keeps its
existing record and separate Worker route. These two routes do not match it.
Use routes, not a Worker custom domain.

Repeat the old-host checks. These commands keep the step 1 baseline files:

```sh
for host in docketseo.app www.docketseo.app; do
  curl --silent --show-error --dump-header - --output /dev/null "https://$host/"
  curl --silent --show-error --include "https://$host/__redirect-health"
  curl --fail --silent --show-error --dump-header "$CHECK_DIR/$host.step2.headers" \
    --output "$CHECK_DIR/$host.step2.body" "https://$host/updater.json"
  cat "$CHECK_DIR/$host.step2.headers"
  cmp "$CHECK_DIR/$host.feed.body" "$CHECK_DIR/$host.step2.body"
done
```

The site must behave as before. Unchanged feeds must compare byte for byte.
The health path must still show the old origin's response, with no local X-Mode
header. There must be no new Worker 301 to `checkengineseo.com`.

Rollback: remove the two routes and restore the saved proxy states and DNS
records. The Pages custom domain has not moved yet. The code rollback line is
also `export const MODE = 'passthrough'`.

### Step 3: Deploy fallback, move the Pages domain, add the grey records

Edit only the mode line, then deploy the reviewed version:

```js
export const MODE = 'fallback'
```

Run the fallback checks below before moving Pages. Then change the GitHub Pages
custom domain to `checkengineseo.com`. Add the approved new-domain DNS records
with **DNS only**, shown by the grey cloud. Keep the old domain's two Worker
routes and orange proxy on. Repeat the fallback checks after the domain move.
The old app URLs must keep working while the new domain waits for HTTPS.

```sh
for host in docketseo.app www.docketseo.app; do
  curl --silent --show-error --include "https://$host/__redirect-health"
  curl --silent --show-error --include "https://$host/pricing/?x=1"
  curl --silent --show-error --head "https://$host/download/"
  curl --silent --show-error --request POST --dump-header - --output /dev/null "https://$host/updater.json"
done
```

Health must be 200 with body `ok`, `X-Mode: fallback` and `Cache-Control: no-store`.
The pricing GET must be 503 with the exact moving text above. The download HEAD
must be 503 with no body. Both page responses must have `Retry-After: 300`,
`Cache-Control: no-store` and no Location header. POST must be 405.

Compare every exact app path with raw. These commands also check the two bot
URLs against the same `index.html` file:

```sh
for host in docketseo.app www.docketseo.app; do
  for app_path in /updater.json /offer.json /data/knowledge.json /bot /bot/ /assets/docket-sample-report.pdf; do
    raw_path="$app_path"
    case "$app_path" in /bot|/bot/) raw_path='/bot/index.html' ;; esac
    curl --fail --silent --show-error --dump-header "$CHECK_DIR/old.headers" \
      --output "$CHECK_DIR/old.body" "https://$host$app_path" || break
    curl --fail --silent --show-error --location --output "$CHECK_DIR/raw.body" \
      "https://raw.githubusercontent.com/mattkerr09/docket-site/gh-pages$raw_path" || break
    cat "$CHECK_DIR/old.headers"
    cmp "$CHECK_DIR/old.body" "$CHECK_DIR/raw.body" || break
  done
done
```

Each old response must be 200 with the file type in the table,
`X-Served-By: docketseo-redirect-fallback`, `Cache-Control: public, max-age=300`
and no Location. Bodies must match. Raw itself may show a different file type.

Check Range with the known sample PDF:

```sh
for host in docketseo.app www.docketseo.app; do
  curl --fail --silent --show-error --range 0-31 --dump-header "$CHECK_DIR/range-old.headers" \
    --output "$CHECK_DIR/range-old.body" "https://$host/assets/docket-sample-report.pdf"
  curl --fail --silent --show-error --location --range 0-31 --output "$CHECK_DIR/range-raw.body" \
    'https://raw.githubusercontent.com/mattkerr09/docket-site/gh-pages/assets/docket-sample-report.pdf'
  cat "$CHECK_DIR/range-old.headers"
  cmp "$CHECK_DIR/range-old.body" "$CHECK_DIR/range-raw.body"
done
```

Expect 206, `Content-Range: bytes 0-31/` followed by the file's total size,
`Content-Length: 32`, `Accept-Ranges: bytes` and matching bytes. Also check two
real release files. Read `/updater.json` and set `UPDATE_PATH` to each existing
`/updates/<version>/<file>` path in turn, then run:

```sh
curl --fail --silent --show-error 'https://docketseo.app/updater.json'
# Set UPDATE_PATH to a real release path from the feed before these commands.
curl --fail --silent --show-error --range 0-31 --dump-header "$CHECK_DIR/update-old.headers" \
  --output "$CHECK_DIR/update-old.body" "https://docketseo.app$UPDATE_PATH"
curl --fail --silent --show-error --location --range 0-31 --output "$CHECK_DIR/update-raw.body" \
  "https://raw.githubusercontent.com/mattkerr09/docket-site/gh-pages$UPDATE_PATH"
cat "$CHECK_DIR/update-old.headers"
cmp "$CHECK_DIR/update-old.body" "$CHECK_DIR/update-raw.body"
```

Expect the same Range result for each file of at least 32 bytes. Choose actual
paths from the current feed, not a made-up release name. For a conditional
check, set `FEED_ETAG` to the full ETag header value from the live feed response:

```sh
curl --silent --show-error --dump-header - --output /dev/null \
  --header "If-None-Match: $FEED_ETAG" 'https://docketseo.app/updater.json'
```

An unchanged feed must return 304 with that ETag and no body. A missing raw file
must return 404 at the old host, with no Location. A known missing test path can
be checked without following redirects:

```sh
curl --silent --show-error --dump-header - --output /dev/null \
  'https://docketseo.app/updates/__redirect_probe_missing__/missing.exe'
```

Confirm that the probe file does not exist before expecting 404. If raw is down,
app requests return 502 with `Cache-Control: no-store` and no Location.

Rollback before the Pages move: set `export const MODE = 'passthrough'` and
redeploy. Rollback after the Pages move: keep fallback active while restoring
the old Pages custom domain and saved old DNS origin. Confirm that the old
origin can serve both old hosts over HTTPS. Then set
`export const MODE = 'passthrough'` and redeploy. Restore any changed new-domain
records from the step 1 record. For a full route rollback, remove the two routes
and restore the old proxy states only after the old origin works again.
Passthrough alone cannot repair an old origin after Pages has moved away.

### Step 4: Check new HTTPS, then deploy redirect

Check the new domain before changing the mode. Do not bypass certificate checks:

```sh
curl --fail --silent --show-error --dump-header - --output /dev/null 'https://checkengineseo.com/'
curl --fail --silent --show-error --dump-header - --output /dev/null 'https://checkengineseo.com/updater.json'
curl --fail --silent --show-error --head 'https://checkengineseo.com/bot/'
curl --fail --silent --show-error --location --range 0-31 --dump-header - --output /dev/null \
  "https://checkengineseo.com$UPDATE_PATH"
```

The site and feed must answer successfully over HTTPS with a valid certificate.
Verify all app paths and both chosen release files at the new origin too.
Only then edit the one line and deploy:

```js
export const MODE = 'redirect'
```

```sh
for host in docketseo.app www.docketseo.app; do
  curl --silent --show-error --include "https://$host/__redirect-health"
  curl --silent --show-error --head "https://$host/download/?from=old&keep=a%2Fb"
  curl --silent --show-error --head "https://$host/UPPER/Path?keep=%2f"
  curl --silent --show-error --head "https://$host/updates"
  curl --silent --show-error --request POST --dump-header - --output /dev/null "https://$host/updater.json"
  for app_path in /updater.json /offer.json /data/knowledge.json /bot /bot/ /assets/docket-sample-report.pdf; do
    curl --fail --silent --show-error --dump-header "$CHECK_DIR/old.headers" \
      --output "$CHECK_DIR/old.body" "https://$host$app_path" || break
    curl --fail --silent --show-error --location --output "$CHECK_DIR/new.body" \
      "https://checkengineseo.com$app_path" || break
    cat "$CHECK_DIR/old.headers"
    cmp "$CHECK_DIR/old.body" "$CHECK_DIR/new.body" || break
  done
done
```

Health must be 200 with body `ok`, `X-Mode: redirect` and `Cache-Control: no-store`.
The page checks must be 301. Each Location must be `https://checkengineseo.com`
plus the exact original path and query, including case and escapes. POST must
be 405. App responses must be 200 with `X-Served-By: docketseo-redirect`, no
Location, and bytes matching the new site.

Repeat the two release Range checks against the new origin:

```sh
for host in docketseo.app www.docketseo.app; do
  curl --fail --silent --show-error --range 0-31 --dump-header "$CHECK_DIR/range-old.headers" \
    --output "$CHECK_DIR/range-old.body" "https://$host$UPDATE_PATH"
  curl --fail --silent --show-error --location --range 0-31 --output "$CHECK_DIR/range-new.body" \
    "https://checkengineseo.com$UPDATE_PATH"
  cat "$CHECK_DIR/range-old.headers"
  cmp "$CHECK_DIR/range-old.body" "$CHECK_DIR/range-new.body"
done
```

Expect 206, Content-Range, Content-Length of 32 and matching bytes. For a 304
check, repeat the earlier conditional command with the new origin's current
feed ETag. An unchanged feed should return 304 if the new origin supports it.

Rollback: if the new HTTPS origin fails, change to
`export const MODE = 'fallback'` and redeploy. App files then come from raw and
pages return 503 while the origin is fixed. For a full rollback, restore the
old Pages domain and DNS origin first, then use
`export const MODE = 'passthrough'`. Remove routes and restore saved proxy
states only once that origin works. Cached 301 responses in browsers and other
clients can outlast any Worker rollback.

## Offline test gate

From the repo root:

```sh
cd workers/docketseo-redirect && node --test
```

Tests replace fetch with offline fakes. The old redirect suite runs through
`makeHandler('redirect')`. It covers the old page inventory, both hosts, URL
suffixes, app files, conditional requests, Range, streaming, errors and methods.
Mode tests cover the raw file mapping and types, 503 pages, HEAD, health,
passthrough identity and an invalid mode. The default export uses `MODE`.
