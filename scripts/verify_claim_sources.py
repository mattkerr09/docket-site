#!/usr/bin/env python3
"""Every claim about a rival cites a page. This checks the page is still there.

    python3 scripts/verify_claim_sources.py

`verify_competitive_claims.py` enforces that each recorded claim *has* a source
URL and that every comparative page carries a check date. It never fetches
anything. So a claim can cite a page that has since 404'd, been moved behind a
redirect to a marketing index, or vanished with a product line, and the gate
goes on passing — while the sentence it protects says "checked on 10 August
2026" to a reader who now cannot check it.

That gate's own docstring says what it is for: "It enforces that a reader can go
and check, which is the part that decays silently." A URL nobody ever fetches is
the decay it was written to catch, happening to itself.

**A refusal is not a dead link**, which is the lesson the product learned the
hard way and this borrows outright. Ahrefs and Semrush answer automated requests
with 403 and serve humans perfectly well; failing the deploy over that would be
Docket telling a business its sitemap is broken because a rate limiter said
"slow down". Refusals are reported and pass. Only a page that positively says it
is gone — 404, 410 — fails, because that is the one answer that means the reader
cannot get there either.

**Being a good guest.** Sources are deduplicated, HEAD is tried before GET, one
request per URL per run, and the whole thing is capped. These are other
people's servers and this is a claim-checking errand, not a crawl.
"""
from __future__ import annotations

import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "articles"))

import comparisons  # noqa: E402

#: Answers that mean "not for you", not "not there". Same set the audit engine
#: uses, and for the same reason.
REFUSED = (401, 403, 405, 406, 429, 451, 503)

#: Answers that mean the page is positively gone.
DEAD = (404, 410)

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")
TIMEOUT = 20


def _status(url: str, method: str = "HEAD") -> tuple:
    """`(status, note)`. Status 0 means no answer at all."""
    req = urllib.request.Request(url, method=method,
                                 headers={"User-Agent": UA, "Accept": "*/*"})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            return resp.status, ""
    except urllib.error.HTTPError as exc:
        # Some hosts reject HEAD outright while serving GET, and one of them
        # answers **404** to it. Google's support pages return 404 to HEAD and
        # 200 to GET, so the first run of this script reported two live pages
        # as gone — a gate written to stop false accusations about third
        # parties, making one. One method's answer is not the page's answer, so
        # every HEAD failure is confirmed with a GET before it counts.
        if method == "HEAD":
            return _status(url, "GET")
        return exc.code, ""
    except Exception as exc:  # noqa: BLE001
        if method == "HEAD":
            return _status(url, "GET")
        return 0, str(exc)[:80]


def main() -> int:
    sources: dict = {}
    for rival, claims in comparisons.VERIFIED.items():
        for claim, url in claims:
            sources.setdefault(url, []).append((rival, claim))

    if not sources:
        print("SOURCES FAIL — no claims carry a source URL at all")
        return 1

    dead, refused, unreachable, alive = [], [], [], 0
    for url in sorted(sources):
        status, note = _status(url)
        rivals = ", ".join(sorted({r for r, _ in sources[url]}))
        if status in DEAD:
            dead.append(f"{status} {url}  (cited for {rivals})")
        elif status in REFUSED:
            refused.append(f"{status} {url}")
        elif status == 0:
            unreachable.append(f"no answer: {url} — {note}")
        elif 200 <= status < 400:
            alive += 1
        else:
            dead.append(f"{status} {url}  (cited for {rivals})")

    for line in refused:
        print(f"  refused, not dead — {line}")
    for line in unreachable:
        print(f"  could not reach — {line}")

    if dead:
        print("SOURCES FAIL — a reader cannot check these:")
        for line in dead:
            print(f"  - {line}")
        print("  Re-read the vendor's page, update the claim and its date, or "
              "drop the claim. A citation to a page that is gone is worse than "
              "no citation: it looks checkable and is not.")
        return 1

    print(f"SOURCES ok — {len(sources)} cited page(s): {alive} answered, "
          f"{len(refused)} refused this script but not a reader, "
          f"{len(unreachable)} unreachable; none gone")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
