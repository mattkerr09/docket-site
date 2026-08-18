#!/usr/bin/env python3
"""What is actually broken on real online shops.

/for/ecommerce/ needs measured findings rather than a list of things an audit
could theoretically check. This audits real shops and records what Docket finds,
so the page can say "this many of these shops have this problem" and be
checkable.

Two things about the frame, both of which the page has to carry:

  * These are large, well-resourced retailers. They are not a random sample of
    the web and they are certainly not a sample of small shops — if anything
    they are the easy case, because they have teams. A finding that shows up
    here is not a story about people being careless.
  * Some shops refuse a crawler or time out. Those are recorded as attempted
    and excluded from every denominator, because a site we could not read
    cannot fail a check, and counting it as a pass would flatter the numbers.

The rating finding is the one worth the page's lead. Google's policy on
`AggregateRating` is that the rating has to be visible on the page carrying the
markup, and the penalty for getting it wrong is a manual action that removes
every rich result the site has. Docket only makes that accusation with rendered
evidence — see the rating-visibility work — so the count here is conservative
by construction.
"""
from __future__ import annotations

import sys as _sys
from pathlib import Path as _Path
_sys.path.insert(0, str(_Path(__file__).resolve().parent))
import app_path  # noqa: E402

import json
import sys
import time
from pathlib import Path

APP = app_path.find()
sys.path.insert(0, str(APP / "backend"))

OUT = Path(__file__).resolve().parent.parent / "data" / "ecommerce.json"
PAGES = 20

SHOPS = [
    "https://www.allbirds.com",
    "https://www.gymshark.com",
    "https://www.brewdog.com",
    "https://www.everlane.com",
    "https://bombas.com",
    "https://ruggable.com",
    "https://www.glossier.com",
    "https://us.oatly.com",
    "https://www.thereformation.com",
    "https://mejuri.com",
    "https://www.johnlewis.com",
    "https://www.lush.com/uk/en/",
]

#: Findings a shop owner would act on, grouped so the page can talk about
#: categories rather than reciting check ids.
GROUPS = {
    "schema": ("schema.missing", "schema.incomplete", "schema.invalid",
               "schema.mismatch", "schema.rating_not_visible"),
    "rating_unconfirmed": ("schema.rating_visibility_unknown",),
    "thin": ("content.very_thin",),
    "indexing": ("index.noindex", "index.canonical_conflict"),
    "contact": ("cvr.dead_contact", "cvr.unusable_phone"),
}


def _measure(url: str) -> dict:
    from seo_engine.audit import run_audit
    from seo_engine.crawler import CrawlConfig

    result = run_audit(url, config=CrawlConfig(
        start_url=url, max_pages=PAGES, max_depth=3,
        check_external_links=False, max_seconds=300))

    pages = [p for p in result.crawl.pages if getattr(p, "status", 0) == 200]
    found = {f.check_id: {"severity": f.severity.value, "count": f.count}
             for f in result.findings}
    return {
        "url": url,
        "pages": len(pages),
        "score": round(result.score.overall, 1),
        "grade": result.score.to_dict()["grade"],
        "findings": found,
        "groups": {name: sorted(cid for cid in ids if cid in found)
                   for name, ids in GROUPS.items()},
    }


def main() -> None:
    results = []
    for url in SHOPS:
        try:
            row = _measure(url)
        except Exception as exc:                          # noqa: BLE001
            print(f"  {url}: unreachable — {type(exc).__name__}")
            results.append({"url": url, "error": type(exc).__name__})
            continue
        results.append(row)
        hits = [n for n, ids in row["groups"].items() if ids]
        print(f"  {url}: {row['pages']}p score {row['score']} {row['grade']} | {hits}")

    ok = [r for r in results if "error" not in r and r["pages"] >= 5]
    if len(ok) < 6:
        raise SystemExit(
            f"only {len(ok)} of {len(SHOPS)} shops produced a usable crawl; a "
            f"proportion over that few is not worth publishing")

    def having(group: str) -> int:
        return sum(1 for r in ok if r["groups"][group])

    scores = sorted(r["score"] for r in ok)
    mid = len(scores) // 2
    median_score = (scores[mid] if len(scores) % 2
                    else round((scores[mid - 1] + scores[mid]) / 2, 1))

    data = {
        "measured": time.strftime("%Y-%m-%d"),
        "page_cap": PAGES,
        "shops_attempted": len(SHOPS),
        "shops_measured": len(ok),
        "shops_unreachable": len(results) - len(ok),
        "median_score": median_score,
        "best_score": max(r["score"] for r in ok),
        "worst_score": min(r["score"] for r in ok),
        "with_schema_problem": having("schema"),
        "with_rating_unconfirmed": having("rating_unconfirmed"),
        "with_thin_pages": having("thin"),
        "with_indexing_problem": having("indexing"),
        "with_contact_problem": having("contact"),
        "results": results,
        "note": (
            f"{len(ok)} large online retailers, {PAGES}-page cap, measured on "
            f"{time.strftime('%Y-%m-%d')} without JavaScript rendering unless "
            "a check demanded it. These are well-resourced companies with "
            "teams, not a random sample of the web and not a sample of small "
            "shops — if anything they are the easy case, so a problem that "
            "shows up here is not a story about carelessness. Shops that "
            "refused the crawler or timed out are recorded and excluded from "
            "every denominator: a site that could not be read cannot fail a "
            "check, and counting it as a pass would flatter the numbers."),
    }
    OUT.write_text(json.dumps(data, indent=2) + "\n")
    print(f"\n{len(ok)}/{len(SHOPS)} shops | median score {median_score} | "
          f"schema {data['with_schema_problem']} | thin {data['with_thin_pages']} "
          f"| indexing {data['with_indexing_problem']}")


if __name__ == "__main__":
    main()
