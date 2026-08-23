#!/usr/bin/env bash
# Build, gate, and publish docketseo.app.
#
# Deploys by pushing site/ to the `gh-pages` branch, which GitHub Pages serves
# directly. This replaced an Actions workflow that failed three times in a row
# with "The job was not acquired by Runner of type hosted" — runner starvation
# on GitHub's side, unrelated to anything in this repo, and each failure sat in
# the queue for 15+ minutes before giving up. `timeout-minutes` does not help:
# it bounds execution, not queue wait.
#
# A hosted runner was never needed here. The site is static, and the build and
# the quality gate both run locally in under a second. The workflow remains in
# .github/workflows/ as a fallback and no longer sits on the critical path.
set -euo pipefail

cd "$(dirname "$0")/.."
PY="${PYTHON:-python3}"

echo "==> build"
"$PY" scripts/build.py >/dev/null

echo "==> derived-number gate"
# The Index published 30% over a 26% dataset because a correction updated the
# prose and not the stored aggregate. This refuses to ship a measurement that
# was typed rather than derived, which is the only version of that bug that
# cannot be caught by reading.
"$PY" scripts/verify_numbers.py

echo "==> derived-data freshness gate"
# verify_numbers.py refuses a number that was typed. It cannot see a number
# that was derived from a dataset nobody rebuilt: the prose and the data agree
# with each other and both are stale. /learn/audit-tool-accuracy/ shipped
# "17 of the 35 test files" for six days against a repo with 74 of 145.
"$PY" scripts/verify_derived_data.py

echo "==> quality gate"
# Runs against the built HTML. A failure here must stop the deploy: this is the
# only thing standing between a bad edit and the live site.
"$PY" scripts/lint.py site

echo "==> contact gate"
# The footer advertised hello@scoutseo.app on all 25 pages and the domain has
# no MX record, so every message anyone sent bounced to them silently. A dead
# mailbox is worse than a broken link: a 404 tells the visitor it failed. This
# resolves every mailto domain and requests every advertised contact URL.
"$PY" scripts/verify_contact.py

echo "==> competitive-claim gate"
# The homepage said "Four things crawler tools ignore" — unsourced, undated, on
# the page with more traffic than every /vs/ page combined, and wrong on its
# sharpest point: Screaming Frog's user guide describes switching user-agent and
# following that agent's robots.txt directives, which is the AI-crawler question
# we said it ignored. Every comparison page quotes its source; this makes the
# rest of the site meet the same standard.
"$PY" scripts/verify_competitive_claims.py

echo "==> checkout gate"
# Every "Buy Docket · $79 once" button points at one Polar checkout link and
# nothing checked it still existed, still belonged to the right organisation,
# still sold the right product or still charged $79. The app-side guard that was
# supposed to cover the organisation had never run once — it needed a token this
# machine has never had — and was wrong the whole time: it expected
# kerr-and-company-llc while the money goes to docketseo. Polar renders all
# three facts into the public checkout page, so this needs no token.
"$PY" scripts/verify_checkout.py || exit 1

echo "==> price-claim gate"
# The download page said "v1.1.0 is free … the $79 applies from v1.0" on a live
# site selling v1.1.0. Both halves were written when BETA_FREE was True and the
# release was 0.1.x; flipping the flag updated the constant and left five
# hand-written copies of the same claim across about, two comparison pages, the
# SaaS page and the download page. A site selling an instrument for catching
# stale copy cannot be the counterexample on its own pricing page.
"$PY" scripts/verify_price_claims.py || exit 1

echo "==> brand asset gate"
# Three different marks across four files, found by opening them: the favicon
# was the desktop app's indigo, and icon.png and og.png were still the orange
# Scout diamond from before the rename — og.png being the picture every shared
# link of this site had been showing. lint.py reads HTML, visual_check.py
# asserts computed CSS and verify_live.py checks files are served; a served
# file that is the wrong picture passes all three, because nothing read a
# pixel. This re-renders all four from the --brand token and compares.
"$PY" scripts/render_brand_assets.py --check || exit 1

echo "==> claim-source gate"
# Every claim about a rival cites a page and nothing ever fetched one. A
# citation to a page that is gone looks checkable and is not, which is the decay
# verify_competitive_claims.py says it exists to catch — happening to itself.
# A refusal is not a dead link: Ahrefs and Semrush answer 403 to scripts and
# serve readers fine, so refusals are reported and pass. Only 404/410 fails.
"$PY" scripts/verify_claim_sources.py || exit 1

echo "==> third-party gate"
# This site published a page-by-page audit of a named delicatessen — the domain,
# 33 page URLs, their titles and per-page risk scores — at a public URL and in
# a public repo. Nobody asked us to. The result was flattering, which is not a
# defence: it was flattering that week, and the consent was never there.
#
# "Do not name private parties who never asked to be audited" was a rule in a
# prompt, which means it held for as long as someone remembered it. Now it fails
# a build.
"$PY" scripts/verify_no_named_third_parties.py

echo "==> monitoring-caveat gate"
"$PY" scripts/verify_monitoring_caveat.py

echo "==> action gate"
"$PY" scripts/verify_action.py

echo "==> link-graph gate"
# data/link-equity.json is a measurement of this site, published through
# facts.py by /learn/internal-link-equity/. It was generated by a command that
# existed only in a terminal, so nothing could tell whether it still described
# the site. This recomputes the graph and fails if the dataset has drifted —
# the same fix the article itself argues for, applied to the article's own data.
"$PY" scripts/verify_link_graph.py

echo "==> visual gate"
# lint.py reads HTML and counts braces. Neither can answer "what colour is this
# link, finally" — and two stray braces once silently deleted the rule that
# coloured every link in every article, and the rule that drew the homepage
# hero. This renders the built pages in WebKit and asserts computed values.
#
# It self-tests first: both historical bugs are injected into throwaway copies
# and the gate must fail on each. A gate that has never been seen to fail is
# not evidence of anything, and both of those bugs shipped past a green build.
"$PY" scripts/visual_check.py --self-test
"$PY" scripts/visual_check.py

echo "==> updater gate"
"$PY" scripts/verify_updater.py || exit 1

# Every gate above this line checks something local. This one checks the
# release the page points at, which is published by a different command in a
# different repository at a different moment — and was the only thing the
# download page cannot function without that nothing verified before going
# live. verify_live.py does check it, afterwards, by hand, once the broken
# page is already public.
echo "==> release gate"
"$PY" scripts/verify_release_assets.py || exit 1

# The customer's path: the link on the page, not the tag in a variable.
#
# Every other release gate starts from an artifact somebody already knew was
# right -- dist/, the tag, the manifest. None of them reads a URL off the
# rendered page, so a stale button or a checksum file from the previous release
# leaves every one of them green. Cheap tier here; `--full` downloads the DMG
# and is for a release rather than a deploy.
echo "==> download-path gate"
"$PY" scripts/verify_download_path.py || exit 1

if [ -f scripts/publish_knowledge.py ]; then
  echo "==> knowledge feed gate"
  "$PY" scripts/publish_knowledge.py
fi

# CNAME lives in site/ so it survives into the deployed branch root. Without it
# GitHub drops the custom domain on the next deploy and docketseo.app 404s.
if [ ! -f site/CNAME ]; then
  echo "FAIL — site/CNAME is missing; deploying would drop the custom domain" >&2
  exit 1
fi

if [ -n "$(git status --porcelain site)" ]; then
  echo "==> committing rebuilt site"
  git add site
  git commit -qm "${1:-site: rebuild}"
fi

echo "==> push main"
git push -q origin main

echo "==> publish site/ to gh-pages"
git branch -D gh-pages-tmp >/dev/null 2>&1 || true
git subtree split --prefix site -b gh-pages-tmp >/dev/null
git push -qf origin gh-pages-tmp:gh-pages
git branch -D gh-pages-tmp >/dev/null

# The gap nothing watched. Every gate above checks the BUILD; this is the only
# one that checks the build reached a reader. On 2026-08-17 two merged, green,
# fully-gated commits sat undeployed and the site served neither of them.
# bookbreaker.bet served "0.1.0 is out" on 116 pages while /download/ handed
# over 0.1.2, because the version was typed inline in a banner. Docket ships
# several times an hour, so this is the same accident waiting for the same
# conditions.
echo "==> pixel/disclosure gate"
# render.py has demanded this in a comment for weeks: "Dark is a claim that has
# to be tested in both directions". The dangerous half is the one nobody writes
# — a gate that only proves the DARK case passes forever, including on the day
# someone sets the id and forgets the privacy policy.
if ! python3 scripts/verify_pixel.py; then
  echo "FAIL  the tracker's state and its disclosure do not agree"
  exit 1
fi

echo "==> vendor-match gate"
# The site takes the money and the app validates the key. If those name
# different vendors, a customer pays and the app refuses what they were sent.
# Every other money gate stays green through that: the checkout gate checks the
# price, the download gate checks reachability, and neither knows which vendor
# the binary behind the link will accept a key from.
if ! python3 scripts/verify_vendor_match.py; then
  echo "FAIL  vendor mismatch between the site and the build being shipped"
  exit 1
fi

echo "==> version-string gate"
"$PY" scripts/verify_version_strings.py

echo "==> media-box gate"
"$PY" scripts/verify_media_boxes.py

echo "==> deployed-build gate (waits for the CDN)"
"$PY" scripts/verify_deployed.py --wait 300

echo "==> done — https://docketseo.app (propagation takes a minute)"
echo
echo "    verify what the CDN is actually serving, once it has propagated:"
echo "      python3 scripts/verify_live.py"
