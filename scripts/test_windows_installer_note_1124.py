#!/usr/bin/env python3
"""The honest line beside the Windows download buttons (CEO and Quality Desk, 24 Nov 2026): the Windows installer still shows
"Docket" ("Docket Setup", "Welcome to Docket Setup"), found by the Windows first-use walk. Until the renamed installer ships the
home page and /download/ say so. Offline: reads the helpers, and the built pages when site/ is newer than the sources.
TAKE THIS TEST AND THE NOTE OUT TOGETHER when the rename ships."""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import brand  # noqa: E402
import render as R  # noqa: E402

NOTE = "The Windows installer is titled Docket, our earlier name."


def main() -> int:
    assert brand.WIN_INSTALLER_NOTE == NOTE
    # the rename pass must keep the literal "Docket" in this sentence, and still rename ordinary prose
    assert NOTE in brand.text(NOTE + " Docket is great.")
    assert "Check Engine is great" in brand.text(NOTE + " Docket is great.")
    # shown under the Windows download paragraph (home, /download/, /pricing/), for the Check Engine brand only
    if brand.SITE_BRAND == "checkengine" and R.WINDOWS:
        assert NOTE in R.windows_download("t")
    # the home hero's price card carries it beside the Windows button
    src = (ROOT / "scripts" / "articles" / "home.py").read_text(encoding="utf-8")
    assert "WIN_INSTALLER_NOTE" in src and "win-installer-note" in src
    newest = max((ROOT / "scripts" / n).stat().st_mtime for n in ("brand.py", "render.py", "articles/home.py"))
    built = {name: ROOT / "site" / path for name, path in (("home", "index.html"), ("download", "download/index.html"))}
    if all(p.exists() and p.stat().st_mtime >= newest for p in built.values()):
        for name, page in built.items():
            raw = page.read_text(encoding="utf-8")
            assert raw.count(NOTE) >= 1, f"the {name} page lacks the Windows installer note"
        learn = ROOT / "site" / "learn" / "index.html"
        if learn.exists() and learn.stat().st_mtime >= newest:
            assert NOTE not in learn.read_text(encoding="utf-8"), "the note belongs on the Windows download places only"
        print("WINDOWS INSTALLER NOTE ok: helper, rename-pass protection, home hero and lower block, /download/")
    else:
        print("WINDOWS INSTALLER NOTE ok: helper and rename-pass protection (no fresh build here, built pages not read)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
