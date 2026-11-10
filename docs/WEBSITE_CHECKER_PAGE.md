# Free website checker

`scripts/articles/tools_website_checker.py` builds `/tools/website-checker/` through
the site's tool template. It uses the existing form, report image, FAQ and tracked
download helpers. `scripts/build.py` registers the page next to the free tools.

## Endpoint and contract

Change `const ENDPOINT` at the top of `CHECKER_JS` to change the host. Its default
is `https://site-check.kerrco.workers.dev`. The browser sends a GET request to
`<endpoint>/site-check?url=<encoded address>`, with credentials omitted. The
Worker allows CORS from the site's own origin.

A 200 response contains `site`, `pages_checked`, `truncated`, `blocked_by_robots`,
ranked `issues`, `fine`, `robots`, `checked_at`, `took_ms` and `from_cache`. Each
issue has `id`, `label`, `count`, `of` and up to three example paths. Labels follow
the page count, such as `have no meta description`. The page shows up to eight
issues and five fine items. A refused check returns `site`, `refused` and `reason`.
Errors return `error` and `message` with status 400, 403, 429 or 503.

## States and next step

While reading, the button is disabled and an elapsed counter runs. Results show
the page count, ranked findings and paths, checks that looked fine, robots.txt
and sitemap findings. A clean result says no issues were found by this check.
A shortened crawl says it read the first N pages. A robots refusal says the site
asked not to be checked. Error messages appear verbatim as text. Network failures
and the 45 second client timeout have plain messages. Every completed request
clears the timers and enables another check. Late replies cannot replace a
timeout message.

The result invitation uses `tools-website-checker` source tags through the hub
download helper and carries the existing `data-ev` tracking. Completed results
send Plausible `Checker` with `tool` set to `website` and `issues` set to the number
of issue rows. The event contains no entered address.

Run `python3 scripts/test_website_checker_page.py`. It builds in a temporary copy
with brand asset rendering skipped, runs the generated script in Node with fake
fetches and timers, and checks the sitemap, tool links, stored graph and privacy
gates. The Worker and its retention rules are supplied by the separate Worker job.
