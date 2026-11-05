#!/usr/bin/env python3
"""The Common Crawl graph `docket backlinks` reads: its release and how many domains it ranks.

    python3 scripts/collect_authority.py    # write data/authority.json (needs the network)

WHY THIS EXISTS (Matthew's full audit, 2026-11-04, row 12). data/authority.json was written by hand from the
May to July 2026 graph (117,963,409 domains) and the home and download pages printed that figure. The engine does
not use a fixed release: `seo_engine.authority.release_stats()` asks Common Crawl for the newest one on every run,
and on 2026-11-05 that was cc-main-2026-aug-sep-oct with 134,979,706 domains. So the figure is read the same way
the engine reads it, and the date it was read goes with it.

The `example` block is kept as it is. It is one full count of referring domains for a large, well-linked site,
made on the release it names, and it stays labelled with that release. The site is not named on any page: it is a
third party we measured. A new count needs a full stream of the edges file, which this script does not do.
"""
from __future__ import annotations

import datetime as dt
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "authority.json"
sys.path.insert(0, str(ROOT / "scripts"))
import app_path  # noqa: E402


def main() -> int:
    backend = str(app_path.find() / "backend")
    if backend not in sys.path:
        sys.path.insert(0, backend)
    from seo_engine import authority  # noqa: PLC0415

    release, domains = authority.release_stats()
    if release == authority.FALLBACK_RELEASE and domains == authority.TOTAL_DOMAINS:
        raise SystemExit("collect_authority: Common Crawl's release list did not answer, so the engine fell back to "
                         "its built-in release; nothing written")
    held = json.loads(OUT.read_text()) if OUT.is_file() else {}
    example = held.get("example")
    if example is None and held.get("example_referring_domains"):
        example = {"release": held.get("release"), "referring_domains": held["example_referring_domains"],
                   "complete": bool(held.get("complete"))}
    data = {
        "release": release,
        "domains": domains,
        "read": dt.datetime.now(dt.timezone.utc).date().isoformat(),
        "example": example,
        "source": "seo_engine.authority.release_stats(), the call docket backlinks makes",
        "collected_by": "scripts/collect_authority.py",
    }
    OUT.write_text(json.dumps(data, indent=1) + "\n")
    print(f"AUTHORITY ok: {release}, {domains:,} domains")
    return 0


if __name__ == "__main__":
    sys.exit(main())
