#!/usr/bin/env python3
"""How wide are the homepage titles and descriptions of well-known sites?

    python3 scripts/collect_titles.py            # writes data/titles-<yyyy-mm>.json

Matthew, 2026-11-06, via the CEO: every new feature gets a page that answers a real question with
Docket's own measured numbers. The SERP preview at /tools/serp-preview/ answers "will Google cut off
my title?", and this is the measurement behind it: one GET of each homepage in the Scout Index sample
(data/sites.txt), read with Docket's own fetcher and extractor and measured with Docket's own width
rule and limits (seo_engine.words.display_width, checks/onpage.py), so the page and the app agree.

A page that is a bot-protection interstitial (challenge.vendor_of) is recorded as refused and left out
of every figure: its title is the vendor's, not the site's. A refusal is never retried with another
user agent. Hosts are stored so the figures can be re-derived; the published pages name none of them.
"""
from __future__ import annotations

import sys as _sys
from pathlib import Path as _Path

_sys.path.insert(0, str(_Path(__file__).resolve().parent))
import app_path  # noqa: E402

import datetime
import json
import statistics
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ENGINE = app_path.backend()
sys.path.insert(0, str(ENGINE))

from seo_engine.challenge import vendor_of  # noqa: E402
from seo_engine.checks.onpage import DESC_MAX, DESC_MIN, TITLE_MAX, TITLE_MIN  # noqa: E402
from seo_engine.extract import extract  # noqa: E402
from seo_engine.fetcher import Fetcher  # noqa: E402
from seo_engine.words import display_width  # noqa: E402

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
    resp = Fetcher(timeout=15.0).get(f"https://{host}/")
    rec = {"host": host, "category": category, "status": resp.status, "error": resp.error or ""}
    if resp.error or resp.status != 200 or not resp.body:
        rec["read"] = False
        return rec
    html = resp.body.decode("utf-8", "replace")
    page = extract(resp)
    if vendor_of(html, getattr(page, "text", None), resp.headers):
        rec["read"], rec["refused"] = False, True
        return rec
    title = (page.title or "").strip()
    desc = (page.meta_description or "").strip()
    rec.update(read=True, title_width=display_width(title) if title else 0,
               desc_width=display_width(desc) if desc else 0)
    return rec


def summarise(records: list[dict]) -> dict:
    read = [r for r in records if r.get("read")]
    tw = [r["title_width"] for r in read if r["title_width"]]
    dw = [r["desc_width"] for r in read if r["desc_width"]]
    return {
        "attempted": len(records),
        "read": len(read),
        "refused": sum(1 for r in records if r.get("refused")),
        "no_title": sum(1 for r in read if not r["title_width"]),
        "title_over": sum(1 for w in tw if w > TITLE_MAX),
        "title_under": sum(1 for w in tw if w < TITLE_MIN),
        "title_in_range": sum(1 for w in tw if TITLE_MIN <= w <= TITLE_MAX),
        "title_median": statistics.median(tw) if tw else 0,
        "title_longest": max(tw) if tw else 0,
        "no_desc": sum(1 for r in read if not r["desc_width"]),
        "desc_over": sum(1 for w in dw if w > DESC_MAX),
        "desc_under": sum(1 for w in dw if w < DESC_MIN),
        "desc_in_range": sum(1 for w in dw if DESC_MIN <= w <= DESC_MAX),
        "desc_median": statistics.median(dw) if dw else 0,
    }


def main() -> int:
    if sys.version_info < (3, 11):
        sys.exit("collect_titles.py needs Python 3.11 or newer (urllib follows 308 from 3.11).")
    rows = sample()
    with ThreadPoolExecutor(max_workers=8) as pool:
        records = list(pool.map(lambda hc: measure(*hc), rows))
    now = datetime.datetime.now(datetime.timezone.utc)
    out = {
        "measured": now.date().isoformat(),
        "method": ("One GET of https://<host>/ per site in data/sites.txt with Docket's fetcher; title and meta "
                   "description read by Docket's extractor; width by seo_engine.words.display_width (East Asian "
                   "wide and fullwidth characters count two); limits from seo_engine/checks/onpage.py. "
                   "Bot-protection interstitials are left out, never retried."),
        "limits": {"title_min": TITLE_MIN, "title_max": TITLE_MAX, "desc_min": DESC_MIN, "desc_max": DESC_MAX},
        "summary": summarise(records),
        "records": records,
    }
    path = ROOT / "data" / f"titles-{now:%Y-%m}.json"
    path.write_text(json.dumps(out, indent=1) + "\n")
    print(path, json.dumps(out["summary"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
