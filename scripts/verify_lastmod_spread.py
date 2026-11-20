#!/usr/bin/env python3
"""Reject concentrated sitemap dates unsupported by this build's fingerprints.

DOCKET_LASTMOD_REASON may explain a real site-wide content change in one line.
It is independent of the release churn gate's DOCKET_SITEWIDE_REASON.
"""
from __future__ import annotations

from collections import Counter
import datetime
import json
import os
from pathlib import Path
from urllib.parse import urlsplit
import xml.etree.ElementTree as ET

from brand import BASE, LASTMOD_FILE

ROOT = Path(__file__).resolve().parents[1]


def verify(sitemap: Path, lastmod: Path, reason: str = "") -> int:
    try:
        records = json.loads(lastmod.read_text(encoding="utf-8"))
        entries = ET.parse(sitemap).getroot().findall("{*}url")
        if not entries:
            raise ValueError("The sitemap has no URLs.")
        dates = Counter()
        changed = 0
        seen = set()
        for entry in entries:
            loc = entry.findtext("{*}loc") or ""
            url = urlsplit(loc)
            if url.scheme + "://" + url.netloc != BASE or url.query or url.fragment:
                raise ValueError(f"Unexpected sitemap URL: {loc}")
            key = url.path.lstrip("/") + "index.html"
            if key in seen:
                raise ValueError(f"Repeated sitemap URL: {loc}")
            seen.add(key)
            day = entry.findtext("{*}lastmod") or ""
            if datetime.date.fromisoformat(day).isoformat() != day:
                raise ValueError(f"Invalid lastmod: {day}")
            record = records[key]
            if record["date"] != day or not record["hash"]:
                raise ValueError(f"Sitemap and fingerprint store disagree for {loc}")
            flag = record.get("changed_in_build", False)
            if not isinstance(flag, bool):
                raise ValueError(f"Invalid build evidence for {loc}")
            changed += flag
            dates[day] += 1
    except (OSError, ValueError, KeyError, TypeError, AttributeError, ET.ParseError) as error:
        print(f"LASTMOD FAIL  Could not check sitemap dates. {error}")
        print("Run the build, then run python3 scripts/verify_lastmod_spread.py again.")
        return 1

    print(f"LASTMOD  {len(entries)} URLs; {changed} fingerprints changed in this build.")
    crowded = [(day, count) for day, count in sorted(dates.items())
               if count * 5 > len(entries) and changed < count]
    for day, count in crowded:
        print(f"LASTMOD  {count}/{len(entries)} URLs share {day}, more than 20%.")
    if not crowded:
        print("LASTMOD OK")
        return 0
    reason = reason.strip()
    if reason and len(reason.splitlines()) == 1:
        print(f"LASTMOD OK  DOCKET_LASTMOD_REASON={reason}")
        return 0
    print("LASTMOD FAIL  Restore honest per-page dates with python3 scripts/collect_lastmod.py "
          "and rebuild. For a real site-wide content change, set DOCKET_LASTMOD_REASON "
          "to a one-line sentence explaining it.")
    return 1


def main() -> int:
    return verify(ROOT / "site/sitemap.xml", ROOT / "data" / LASTMOD_FILE,
                  os.environ.get("DOCKET_LASTMOD_REASON", ""))


if __name__ == "__main__":
    raise SystemExit(main())
