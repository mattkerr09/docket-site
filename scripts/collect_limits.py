#!/usr/bin/env python3
"""What actually bounds a crawl, read from the shipped code.

limits.json used to be typed by hand with a note saying where the numbers came
from. That note was accurate and the numbers still went stale the moment the
page cap became unlimited, which is the whole argument for this file: a figure
only a person can reproduce will drift, and this one is printed on /download/.

Every value here is read out of the source rather than restated. The UI clamp
comes from ui/src/app.js because that is the number a desktop user can actually
type, and it is a different thing from the engine default.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

APP = Path("/Users/matthewkerr/Downloads/SEO audit app")
sys.path.insert(0, str(APP / "backend"))
OUT = Path(__file__).resolve().parent.parent / "site" / "_data" / "limits.json"


def _ui_clamp() -> tuple[int, int]:
    src = (APP / "ui" / "src" / "app.js").read_text()
    m = re.search(r"max_pages:\s*clampInt\([^,]+,\s*(\d+),\s*(\d+),", src)
    if not m:
        raise SystemExit("could not read the UI page clamp from app.js")
    return int(m.group(1)), int(m.group(2))


def main() -> None:
    from seo_engine.crawler import CrawlConfig

    cfg = CrawlConfig(start_url="https://example.com")
    ui_lo, ui_hi = _ui_clamp()

    # 0 is the sentinel for "this dimension does not stop the crawl". It is
    # only meaningful alongside what DOES stop it, so both travel together.
    data = {
        "page_cap_removed": ui_lo == 0,
        "ui_default_pages": cfg.max_pages,
        "cli_default_pages": cfg.max_pages,
        "ui_min_pages": ui_lo,
        "ui_max_pages": ui_hi,
        "max_depth_default": cfg.max_depth,
        "wall_clock_seconds": int(cfg.max_seconds),
        "wall_clock_minutes": round(cfg.max_seconds / 60),
        "delay_seconds": cfg.delay,
        "concurrency": cfg.concurrency,
        "note": (
            "Read from seo_engine.crawler.CrawlConfig and the clamp in "
            "ui/src/app.js by scripts/collect_limits.py, so the published "
            "figures cannot drift from the shipped ones. There is no page "
            "ceiling: 0 means the page count does not stop the crawl. It is "
            "still bounded — by the wall clock, by the frontier running dry, "
            "and in practice by memory, because every page is held in a list. "
            "Publishing 'unlimited' without those three would be a promise the "
            "program cannot keep."),
    }
    OUT.write_text(json.dumps(data, indent=2) + "\n")
    print(f"page cap removed: {data['page_cap_removed']} | default "
          f"{data['ui_default_pages']} | wall clock "
          f"{data['wall_clock_minutes']}m | depth {data['max_depth_default']}")


if __name__ == "__main__":
    main()
