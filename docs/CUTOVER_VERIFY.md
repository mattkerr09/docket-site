# Cutover checks

Run from the repo root after each cutover step, then run `final` again before
Product Hunt. This command checks the live site. It changes no account setting.

```sh
python3 scripts/verify_cutover.py --phase passthrough
python3 scripts/verify_cutover.py --phase fallback
python3 scripts/verify_cutover.py --phase redirect
python3 scripts/verify_cutover.py --phase final
```

`--old docketseo.app --new checkengineseo.com` states the default hosts.
Only these two host names are accepted. Requests also reach the old www host
and, in the final phase, `mcp.docketseo.app/health`. TLS checks use the normal
certificate and host checks. Redirects are never followed. A link in a feed
cannot make the checker request another host. By default, requests use GET and HEAD only.

Add `--probe-post` once after the Worker is in `fallback` or `redirect` mode.
It sends one empty POST to `https://docketseo.app/` and one to
`https://docketseo.app/__redirect-health`, with no cookies or credentials,
and checks for 405, the exact Allow header, and no Location header.
It is opt-in because these are the verifier's only requests beyond GET and HEAD,
and the flag is refused in `passthrough` and `final` phases.

| Phase | What a pass proves |
| --- | --- |
| `passthrough` | Old pages and app files return 200 with the expected file type. The old www host sends a 301 to the apex. Current release files support Range. This is a status and type check, not a saved copy of the old site. |
| `fallback` | Both old hosts serve app files with the fallback marker and file type. Current release files return 200 to HEAD and 206 for a one-byte GET. Page probes return 503 with Retry-After. Health says `ok` and `fallback`. |
| `redirect` | Both old hosts keep app files on the same URL with matching SHA-256 body hashes from the new site. Release checks compare both a one-byte Range and the full file hash. Six page paths keep case, escapes and queries in their 301 target. Health says `ok` and `redirect`. |
| `final` | Both hosts pass TLS. The seven main pages return 200 with new-host metadata and the site-bound Plausible snippet. Sitemap and robots use the new host. The OG file is a 1200x630 PNG. MCP health returns 200. All platform URLs in the old updater feed return 206 to HEAD with Range. Every HTML file in the new redirect inventory, plus sitemap pages, passes the old-host scan. |

The old-host scan allows the support address, the MCP host, app paths and
content inside `data-brand-history` elements. It also checks attributes and
inline scripts. A bare old host or an unmarked old email address fails.
The redirect inventory must be published so the scan includes pages outside
the sitemap. Image size alone does not prove the card has the right artwork.
The redirect phase downloads whole release files to compare their hashes.
It hashes them in chunks without keeping installers in memory.

Each row prints PASS or FAIL, its check name and a short reason. Any FAIL gives
exit code 1. Read the path and reason, fix that cutover step, then rerun the same
phase. An HTTP status failure means the expected response was not served.
A header or hash failure means a response arrived but did not match the rule.
A TLS or connection failure needs a host or certificate fix. Do not bypass TLS.
A failed feed or inventory check means later discovered-file checks may be
missing. The run still fails.

## Offline self-test

```sh
python3 scripts/verify_cutover.py --self-test
```

This starts an in-process fake server on a spare loopback port in 8950-8999.
It runs every phase, then plants wrong statuses, headers, bodies, metadata,
URLs and image sizes and requires failures. TLS failure and host limits use
injected fetches. No live hosts are contacted. The test exits 1 if the sandbox
blocks the local server. This repo has no `docs/PORTS.md`; no port row was added.
If that file is added later, the test skips ports listed there.

Both brands use the same site-bound Plausible loader (`pa-9WvL8...js`, async, no `data-domain`) and the same
queue-and-init stub (CEO, 2026-11-10). It counts under the `docketseo.app` Plausible site whatever the hostname, so the
Check Engine host keeps Docket's history. The `checkengineseo.com` Plausible site was repurposed and must not be used.
After the flip is verified, the CEO renames the Plausible site (Site settings, Change domain) to `checkengineseo.com`.
The verifier expects exactly one Plausible loader with that source, `async`, no `data-domain`, and the stub with
`plausible.init`.
No key is needed or changed by these scripts.
