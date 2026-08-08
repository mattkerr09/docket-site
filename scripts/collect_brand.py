#!/usr/bin/env python3
"""How consistent real companies actually are about their own brand.

Scout has a brand lane — six checks asking whether a site looks and sounds
like one company — and no competitor's crawler asks the question at all. That
makes it the most differentiated thing in the product and, until now, the least
evidenced: the site claimed the lane existed and never showed what it finds.

So this measures it. Every figure the brand article publishes comes from here.

What is counted, and what that is worth:

  * Typefaces and colours are counted from the CSS the pages actually ship.
    That is a proxy for design-system discipline and it is stated as one — a
    site with five typefaces may be beautiful. It is still five typefaces.
  * Social profiles linked versus social profiles declared in `sameAs`. This
    one is not a proxy for anything: either the machine-readable declaration is
    there or it is not.
  * Naming: whether the company calls itself the same thing in its titles, its
    og:site_name, its Organization schema and its logo alt text.

Frame: public commercial sites across several sectors, small by design. The
dataset records every host so anybody can re-run it, and the article must
present this as what it is — a sample of the visible web, not a census.

Run from the site repo; it imports Scout's engine from the app checkout.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from statistics import median

APP = Path("/Users/matthewkerr/Downloads/SEO audit app")
sys.path.insert(0, str(APP / "backend"))

OUT = Path(__file__).resolve().parent.parent / "site" / "_data" / "brand.json"
PAGES = 15

#: Deliberately spread across sectors and build styles. Two of these are
#: engineering-led companies whose design systems are public, which is a useful
#: control: if the counting were noise they would score like everybody else.
SITES = [
    "https://stripe.com",
    "https://www.ikea.com/gb/en/",
    "https://www.johnlewis.com",
    "https://www.bbc.co.uk",
    "https://www.airbnb.co.uk",
    "https://www.deliveroo.co.uk",
    "https://www.gymshark.com",
    "https://www.lush.com/uk/en/",
    "https://www.brewdog.com",
    "https://www.pret.co.uk",
    "https://www.allbirds.com",
    "https://www.thefarmersdog.com",
    "https://pizzapilgrims.co.uk",
    "https://basecamp.com",
    "https://www.gov.uk",
    "https://www.patagonia.com",
    "https://monzo.com",
    "https://www.notion.com",
    "https://www.warbyparker.com",
    "https://www.tesco.com",
    "https://scoutseo.app",
]

BRAND_CHECKS = ("brand.name_consistency", "brand.logo", "brand.visual_consistency",
                "brand.visual_unreadable", "brand.colour_drift",
                "brand.positioning", "brand.voice_consistency",
                "brand.social_consistency")


def _measure(url: str) -> dict:
    from seo_engine import brandsig
    from seo_engine.audit import run_audit
    from seo_engine.crawler import CrawlConfig

    result = run_audit(url, config=CrawlConfig(
        start_url=url, max_pages=PAGES, max_depth=3,
        check_external_links=False, max_seconds=180))

    pages = [p for p in result.crawl.pages if getattr(p, "status", 0) == 200]
    fonts, colors = set(), set()
    for page in pages:
        fonts.update(getattr(page, "font_families", ()) or ())
        colors.update(getattr(page, "colors", ()) or ())

    fired = {f.check_id: f.severity.value for f in result.findings
             if f.check_id in BRAND_CHECKS}

    # Social profiles linked vs declared. Read off the finding rather than
    # recomputed here, so the published number is what the product says.
    linked = declared = None
    for finding in result.findings:
        if finding.check_id == "brand.social_consistency":
            ev = finding.evidence or {}
            linked = len(ev.get("undeclared", [])) + len(ev.get("declared", []))
            declared = len(ev.get("declared", []))

    drift = next((f.count for f in result.findings
                  if f.check_id == "brand.colour_drift"), 0)
    return {
        "url": url,
        "pages": len(pages),
        "colour_drift_groups": drift,
        "typefaces": len(fonts),
        "colours": len(colors),
        "brand_findings": fired,
        "social_linked": linked,
        "social_declared": declared,
        "score": round(result.score.overall, 1),
    }


def main() -> None:
    results = []
    for url in SITES:
        try:
            row = _measure(url)
        except Exception as exc:                      # noqa: BLE001
            print(f"  {url}: FAILED — {type(exc).__name__}: {exc}")
            results.append({"url": url, "error": f"{type(exc).__name__}: {exc}"})
            continue
        results.append(row)
        print(f"  {url}: {row['pages']}p, {row['typefaces']} typefaces, "
              f"{row['colours']} colours, {len(row['brand_findings'])} brand findings")

    ok = [r for r in results if "error" not in r and r["pages"] >= 3]
    if len(ok) < 6:
        raise SystemExit(
            f"only {len(ok)} of {len(SITES)} sites produced a usable crawl; a "
            f"proportion over that few is not worth publishing")

    typefaces = [r["typefaces"] for r in ok]
    colours = [r["colours"] for r in ok]
    # A site with no social links cannot fail to declare them, so it is not in
    # the denominator. Reporting it as a pass would flatter the numerator.
    social_frame = [r for r in ok if r["social_linked"]]
    undeclared = [r for r in social_frame if not r["social_declared"]]

    data = {
        "measured": time.strftime("%Y-%m-%d"),
        "page_cap": PAGES,
        "sites_attempted": len(SITES),
        "sites_measured": len(ok),
        # How often the typeface question could be answered AT ALL. Scout
        # reads inline <style> only, so on a site serving linked stylesheets
        # this signal is structurally absent. Publishing a median across sites
        # where it was never measurable would report blindness as tidiness.
        "css_readable": sum(1 for r in ok if r["typefaces"] or r["colours"]),
        "drift_frame": sum(1 for r in ok if r["typefaces"] or r["colours"]),
        "with_colour_drift": sum(1 for r in ok if r.get("colour_drift_groups")),
        "median_typefaces": median(typefaces),
        "max_typefaces": max(typefaces),
        "min_typefaces": min(typefaces),
        "over_four_typefaces": sum(1 for n in typefaces if n > 4),
        "median_colours": median(colours),
        "max_colours": max(colours),
        "social_frame": len(social_frame),
        "social_undeclared": len(undeclared),
        "naming_inconsistent": sum(
            1 for r in ok if "brand.name_consistency" in r["brand_findings"]),
        "logo_unnamed": sum(1 for r in ok if "brand.logo" in r["brand_findings"]),
        "results": results,
        "note": (
            f"{len(ok)} public commercial sites, {PAGES}-page cap, measured on "
            f"{time.strftime('%Y-%m-%d')}. A sample of the visible web, not a "
            "census — the frame is small and chosen, and every host is listed "
            "so it can be re-run. Typeface and colour counts come from the CSS "
            "the pages ship and are a proxy for design-system discipline, "
            "stated as one: five typefaces may be deliberate. The social "
            "figure is not a proxy — sameAs is either declared or it is not — "
            "and its denominator excludes sites that link no profiles at all, "
            "since they cannot fail to declare them."),
    }
    OUT.write_text(json.dumps(data, indent=2) + "\n")
    print(f"\n{len(ok)} sites | typefaces median {data['median_typefaces']} "
          f"(max {data['max_typefaces']}) | {data['social_undeclared']}/"
          f"{data['social_frame']} link profiles without declaring them")


if __name__ == "__main__":
    main()
