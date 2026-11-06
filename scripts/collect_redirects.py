#!/usr/bin/env python3
"""How many redirects stand between a typed address and the homepage, and which security headers does it send?

    python3 scripts/collect_redirects.py         # writes data/redirects-<yyyy-mm>.json

CEO, 2026-11-06: the redirect checker and the HTTP header checker answer "how do I check a redirect
chain", "why does my site have too many redirects" and "how do I check my HTTP headers" with Docket's
own numbers. This is the measurement: for each homepage in the Scout Index sample (data/sites.txt),
one walk from http://<host>/ (what a person types) with Docket's fetcher, counting the hops, then the
security headers on the page it ends on, judged with the engine's rules (checks/security.py: HSTS,
except on a TLD the browsers preload; X-Content-Type-Options; Referrer-Policy).

A site that refuses the request, or answers with a bot-protection page, is recorded and left out of
every figure, never retried with another user agent. Hosts are stored so the figures can be
re-derived; the published pages name none of them.
"""
from __future__ import annotations

import sys as _sys
from pathlib import Path as _Path

_sys.path.insert(0, str(_Path(__file__).resolve().parent))
import app_path  # noqa: E402

import collections
import datetime
import json
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ENGINE = app_path.backend()
sys.path.insert(0, str(ENGINE))

from seo_engine.challenge import vendor_of  # noqa: E402
from seo_engine.checks.security import preloaded_tld  # noqa: E402
from seo_engine.fetcher import Fetcher  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent


def sample() -> list[tuple[str, str]]:
    rows = []
    for line in (ROOT / "data" / "sites.txt").read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            host, _, category = line.partition(",")
            rows.append((host.strip(), category.strip()))
    return rows


def measure(host: str, category: str) -> dict:
    resp = Fetcher(timeout=15.0).get(f"http://{host}/")
    rec = {"host": host, "category": category, "status": resp.status, "error": resp.error or "",
           "hops": len(resp.chain), "final": resp.url}
    if resp.error or resp.status != 200:
        rec["read"] = False
        return rec
    if vendor_of(resp.body.decode("utf-8", "replace"), None, resp.headers):
        rec["read"], rec["refused"] = False, True
        return rec
    h = {k.lower() for k in resp.headers}
    rec.update(read=True, https=resp.url.startswith("https://"),
               hsts="strict-transport-security" in h, preloaded=bool(preloaded_tld(resp.url)),
               xcto="x-content-type-options" in h, referrer="referrer-policy" in h,
               csp="content-security-policy" in h)
    return rec


def summarise(records: list[dict]) -> dict:
    read = [r for r in records if r.get("read")]
    https = [r for r in read if r["https"]]
    judged = [r for r in https if not r["preloaded"]]
    hops = collections.Counter(r["hops"] for r in read)
    return {
        "attempted": len(records),
        "read": len(read),
        "refused": sum(1 for r in records if r.get("refused")),
        "status_403": sum(1 for r in records if not r.get("read") and not r.get("refused") and r["status"] == 403),
        "hops": {str(k): hops[k] for k in sorted(hops)},
        "two_or_more": sum(1 for r in read if r["hops"] >= 2),
        "max_hops": max((r["hops"] for r in read), default=0),
        "ended_http": sum(1 for r in read if not r["https"]),
        "https": len(https),
        "hsts_judged": len(judged),
        "no_hsts": sum(1 for r in judged if not r["hsts"]),
        "no_xcto": sum(1 for r in https if not r["xcto"]),
        "no_referrer": sum(1 for r in https if not r["referrer"]),
        "no_csp": sum(1 for r in https if not r["csp"]),
    }


def main() -> int:
    if sys.version_info < (3, 11):
        sys.exit("collect_redirects.py needs Python 3.11 or newer (urllib follows 308 from 3.11).")
    rows = sample()
    with ThreadPoolExecutor(max_workers=8) as pool:
        records = list(pool.map(lambda hc: measure(*hc), rows))
    now = datetime.datetime.now(datetime.timezone.utc)
    out = {
        "measured": now.date().isoformat(),
        "method": ("One walk from http://<host>/ per site in data/sites.txt with Docket's fetcher, following "
                   "redirects; hops = URLs walked before the page. Headers read from the page it ends on and "
                   "judged with seo_engine/checks/security.py (HSTS not expected on a preloaded TLD). Refusals "
                   "and bot-protection pages left out, never retried."),
        "summary": summarise(records),
        "records": records,
    }
    path = ROOT / "data" / f"redirects-{now:%Y-%m}.json"
    path.write_text(json.dumps(out, indent=1) + "\n")
    print(path, json.dumps(out["summary"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
