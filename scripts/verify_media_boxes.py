#!/usr/bin/env python3
"""Does every image and video reserve the box it actually needs?

**The bug this exists for happened on 2026-08-19.** `app-plan.webp` was
re-cropped from 1600x1000 to 1500x672 and the `width`/`height` attributes in the
markup were not moved with it. Nothing failed: the picture looked right, every
gate stayed green, and the only symptom was the page jolting as the image
loaded, because the browser had reserved a box of the wrong shape and had to
re-lay-out around the real one. That is invisible in a screenshot and invisible
in HTML — it is only visible in the arithmetic.

**It checks the RATIO, not the pixels.** `width="1500" height="672"` on a
3000x1344 file is correct: the attributes exist to give the browser an aspect
ratio to reserve before the bytes arrive. Demanding exact equality would fail
every legitimately retina-scaled asset and the gate would be switched off.

**A missing width/height is also a failure**, not a pass. An image with no
declared box reserves nothing at all, which is the same jolt with none of the
evidence.

    python3 scripts/verify_media_boxes.py
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

SITE = Path(__file__).resolve().parent.parent / "site"
TOL = 0.01

try:
    from PIL import Image
except ImportError:  # pragma: no cover
    print("MEDIA BOX: Pillow is not installed, so nothing was measured.")
    print("That is not a pass.")
    raise SystemExit(1)


def ratio_of(path: Path) -> float | None:
    try:
        w, h = Image.open(path).size
        return w / h if h else None
    except Exception:
        return None


def main() -> int:
    pages = sorted(SITE.rglob("*.html"))
    if not pages:
        print("MEDIA BOX FAIL — no built pages; run scripts/build.py first")
        return 1

    problems: list[str] = []
    checked = 0
    seen: set[tuple] = set()

    for page in pages:
        html = page.read_text(encoding="utf-8", errors="replace")
        for tag in re.findall(r"<(?:img|video)[^>]*>", html):
            src = re.search(r'(?:src|poster)="([^"]+)"', tag)
            if not src or src.group(1).startswith(("http", "data:")):
                continue
            key = (src.group(1), tag[:60])
            if key in seen:
                continue
            seen.add(key)
            rel = page.relative_to(SITE)
            w = re.search(r'width="(\d+)"', tag)
            h = re.search(r'height="(\d+)"', tag)
            target = SITE / src.group(1).lstrip("/")
            if not target.is_file():
                problems.append(f"    {rel}: {src.group(1)} is referenced but not served")
                continue
            if not (w and h):
                problems.append(
                    f"    {rel}: {src.group(1)} declares no width/height, so the "
                    f"browser reserves nothing and the page jolts when it loads")
                continue
            declared = int(w.group(1)) / int(h.group(1))
            actual = ratio_of(target)
            if actual is None:
                continue  # a video poster we cannot read is not a failure
            checked += 1
            if abs(declared - actual) > TOL:
                problems.append(
                    f"    {rel}: {src.group(1)} declares {w.group(1)}x{h.group(1)} "
                    f"(ratio {declared:.3f}) but the file is ratio {actual:.3f}. "
                    f"The reserved box is the wrong shape and the layout will "
                    f"shift as it loads.")

    if problems:
        print(f"MEDIA BOX FAIL — {len(problems)} problem(s):")
        for p in problems:
            print(p)
        return 1
    print(f"MEDIA BOX ok — {checked} media reference(s), every reserved box "
          f"matches the file it holds")
    return 0


if __name__ == "__main__":
    sys.exit(main())
