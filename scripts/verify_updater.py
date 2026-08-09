#!/usr/bin/env python3
"""Refuse to publish an update manifest that would reject every update.

This is the quietest failure in the whole product. A manifest whose signature
does not match its tarball produces no error anybody sees: Tauri downloads the
update, fails the signature check, and gives up. Users sit on an old build
indefinitely, believing they are current, and nothing in any log says so.

So the manifest is checked against the artifacts on disk before the site goes
out, and the deploy fails if they disagree.

Skips cleanly when there is no local build — the site is deployed far more
often than the app is, and a site-only deploy must not require a 17 MB tarball
to be sitting in dist/.
"""
from __future__ import annotations

import json
import pathlib
import sys

SITE = pathlib.Path(__file__).resolve().parent.parent / "site"
APP = pathlib.Path("/Users/matthewkerr/Downloads/SEO audit app")
MANIFEST = SITE / "updater.json"
TGZ = APP / "dist" / "Docket.app.tar.gz"
SIG = APP / "dist" / "Docket.app.tar.gz.sig"


def fail(message: str) -> None:
    print(f"UPDATER FAIL — {message}")
    sys.exit(1)


def main() -> None:
    if not MANIFEST.is_file():
        print("UPDATER skipped — no updater.json yet")
        return

    try:
        data = json.loads(MANIFEST.read_text())
    except json.JSONDecodeError as exc:
        fail(f"updater.json is not valid JSON ({exc}); every client would fail "
             f"to parse it and no user would ever be offered an update")

    for key in ("version", "platforms", "pub_date"):
        if key not in data:
            fail(f"updater.json has no {key!r}")

    platforms = data["platforms"]
    if not platforms:
        fail("updater.json lists no platforms, so it offers nothing to anybody")

    for name, entry in platforms.items():
        for key in ("signature", "url"):
            if not entry.get(key):
                fail(f"{name} has no {key}")
        if not entry["url"].startswith("https://"):
            fail(f"{name} url is not https — an update channel over plain http "
                 f"is a remote code execution vector")

    # Docket is Apple Silicon only. Claiming darwin-x86_64 would hand an arm64
    # binary to an Intel Mac, failing after the download rather than before it.
    if "darwin-x86_64" in platforms:
        fail("updater.json offers darwin-x86_64 and there is no Intel build")

    if not SIG.is_file():
        print(f"UPDATER ok (shape) — {data['version']}, "
              f"{len(platforms)} platform(s); no local build to compare against")
        return

    local = SIG.read_text().strip()
    published = platforms.get("darwin-aarch64", {}).get("signature", "")
    if published != local:
        fail("the signature in updater.json does not match "
             "dist/Docket.app.tar.gz.sig. Every update would be silently "
             "rejected and users would never be told. Re-run "
             "scripts/collect_updater.py after the build.")

    size = TGZ.stat().st_size // 1024 if TGZ.is_file() else 0
    print(f"UPDATER ok — {data['version']}, signature matches this build's "
          f".sig ({size} KB tarball), {len(platforms)} platform(s)")


if __name__ == "__main__":
    main()
