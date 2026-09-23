#!/usr/bin/env python3
"""Every script the built site loads is named, and counted, on the privacy page.

⚠️ WHY. The privacy page said "five third-party scripts" while the front page
loaded six: the founding-offer bar (founding.js) was never listed, and it is the
one that writes to local storage. A list that says it is complete has to be.
Outlier found the same defect on its own site the same week (four named, six
loaded; ~/ops/UPGRADES.md, 2026-09-21), and the rule from it is this gate:
count script src per page against the disclosure before every ship.

What counts as one script: each distinct external `<script src>` URL (host and
path, query dropped) on any built page, plus the Meta pixel, whose loader is an
inline snippet with no src and is found by the marks verify_pixel.py uses.

Refuses when:
  * the privacy page's "runs N third-party scripts" differs from that count, or
    cannot be read at all;
  * a script's host appears nowhere on the privacy page.

--self-test plants an unlisted script into a copy of a built page's text and
requires the gate to refuse it; then requires the real site to pass.
"""
from __future__ import annotations

import argparse
import pathlib
import re
import sys
from urllib.parse import urlsplit

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from verify_pixel import (PRIVACY, SITE, TRACKER_MARKS,  # noqa: E402
                          declared_script_count)

_SRC = re.compile(r"<script\b[^>]*\bsrc=[\"']([^\"']+)[\"']", re.I)


def loaded_scripts(pages: dict[str, str]) -> dict[str, list[str]]:
    """{script: [pages that load it]} across the built site."""
    out: dict[str, list[str]] = {}
    for name, text in pages.items():
        found = set()
        for src in _SRC.findall(text):
            u = urlsplit(src)
            if u.scheme in ("http", "https") and u.netloc:
                found.add(f"{u.netloc}{u.path}")
        if any(mark in text for mark in TRACKER_MARKS):
            found.add("Meta pixel (connect.facebook.net)")
        for key in found:
            out.setdefault(key, []).append(name)
    return out


def check(pages: dict[str, str], privacy_html: str, declared: int | None) -> list[str]:
    scripts = loaded_scripts(pages)
    bad = []
    if declared is None:
        bad.append("the privacy page's \"runs N third-party scripts\" sentence could not be "
                   "read, so the count is unchecked")
    elif declared != len(scripts):
        bad.append(f"the privacy page says {declared} third-party scripts; the built site "
                   f"loads {len(scripts)}")
    for key, where in sorted(scripts.items()):
        host = key.split("/")[0] if not key.startswith("Meta pixel") else "facebook"
        if host.lower() not in privacy_html.lower():
            bad.append(f"{key} (on {len(where)} page(s), e.g. {where[0]}) is loaded and "
                       f"its host is named nowhere on the privacy page")
    return bad


def _built() -> dict[str, str]:
    return {str(p.relative_to(SITE)): p.read_text(encoding="utf-8", errors="replace")
            for p in sorted(SITE.rglob("*.html"))}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    pages = _built()
    if not pages or not PRIVACY.is_file():
        print("FAIL — no built site or no privacy page to check")
        return 1
    privacy = PRIVACY.read_text(encoding="utf-8", errors="replace")
    declared = declared_script_count()

    if args.self_test:
        planted = dict(pages)
        planted["index.html"] = planted["index.html"].replace(
            "</body>", '<script src="https://unlisted.example/x.js"></script></body>')
        # Refused FOR the planted script, by name — "some failure" would pass
        # a self-test on a site that already fails for another reason.
        if not any("unlisted.example" in b for b in check(planted, privacy, declared)):
            print("SELF-TEST FAILED — an unlisted script on the front page passed")
            return 1
        print("  self-test ok — a planted unlisted script was refused")

    bad = check(pages, privacy, declared)
    scripts = loaded_scripts(pages)
    if bad:
        print(f"FAIL — the privacy page does not describe what the site loads:")
        for b in bad:
            print(f"  {b}")
        for key, where in sorted(scripts.items()):
            print(f"    {len(where):4d} page(s)  {key}")
        return 1
    print(f"PRIVACY SCRIPTS ok — {len(scripts)} third-party script(s) loaded, "
          f"{declared} declared, every host named")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
