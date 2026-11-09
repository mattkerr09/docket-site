#!/usr/bin/env python3
"""Check cached updater files, or wait for their bytes to reach the live site."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
import time
import urllib.error
import urllib.request

import stage_updates_mirror as mirror

MANIFEST_URL = "https://docketseo.app/updater.json"
HEADERS = {"User-Agent": "kerr-ops/1.0 updates-mirror", "Cache-Control": "no-cache"}


def get_manifest(url: str, timeout: float) -> dict:
    separator = "&" if "?" in url else "?"
    request = urllib.request.Request(f"{url}{separator}cb={time.time_ns()}", headers=HEADERS)
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.load(response)


def check_url(url: str, path: Path, digest: str, deadline: float) -> None:
    def timeout() -> float:
        return max(0.1, min(30, deadline - time.monotonic()))

    # GET headers also describe Range support. No HEAD request is needed.
    request = urllib.request.Request(url, headers=HEADERS)
    actual = hashlib.sha256()
    size = 0
    first_byte = b""
    with urllib.request.urlopen(request, timeout=timeout()) as response:
        supports_range = response.headers.get("Accept-Ranges", "").lower() == "bytes"
        content_type = response.headers.get("Content-Type", "unspecified")
        for block in iter(lambda: response.read(1024 * 1024), b""):
            if not first_byte:
                first_byte = block[:1]
            size += len(block)
            if size >= mirror.MAX_BYTES:
                raise ValueError(f"{url} serves at least 100 MB")
            actual.update(block)
            if time.monotonic() > deadline:
                raise ValueError(f"Time limit reached while fetching {url}")
    if size != path.stat().st_size or actual.hexdigest() != digest:
        raise ValueError(f"Served sha256 or size differs for {url}")
    request = urllib.request.Request(url, headers={**HEADERS, "Range": "bytes=0-0"})
    with urllib.request.urlopen(request, timeout=timeout()) as response:
        supports_range |= response.headers.get("Accept-Ranges", "").lower() == "bytes"
        if response.status == 206:
            if (response.headers.get("Content-Range") != f"bytes 0-0/{size}"
                    or response.read(2) != first_byte):
                raise ValueError(f"Invalid Range response for {url}")
            range_report = "Range returned 206"
        elif response.status == 200 and not supports_range:
            range_report = "Range not supported by this server"
        else:
            raise ValueError(f"Range request returned {response.status} for {url}")
    print(f"{url} verified. {range_report}. Content-Type {content_type}")


def verify_live(expected: dict, cache: Path, url: str, wait: float) -> None:
    # The local manifest anchors the release. A coherent old live manifest
    # must not pass a check of the release that was just pushed.
    started = time.monotonic()
    deadline = started + wait
    while True:
        try:
            remaining = max(0.1, min(30, deadline - time.monotonic()))
            manifest = get_manifest(url, remaining if wait else 30)
            if manifest != expected:
                raise ValueError("Live updater manifest differs from site/updater.json")
            mirror.publish_plan(manifest, cache)
            for version, name in mirror.mirror_entries(manifest):
                path = cache / version / name
                asset_url = next(entry["url"] for entry in manifest["platforms"].values()
                                 if entry["url"].endswith(f"/{version}/{name}"))
                # A zero wait still permits one complete attempt for local checks.
                check_url(asset_url, path, mirror.checked_digest(path),
                          deadline if wait else time.monotonic() + 30)
            return
        except (OSError, ValueError, KeyError) as exc:
            if time.monotonic() >= deadline:
                raise ValueError(f"Live mirror check failed after {wait:g} seconds. {exc}") from exc
            print(f"Waiting for Pages. {exc}", file=sys.stderr)
            time.sleep(min(10, max(0, deadline - time.monotonic())))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--offline", action="store_true")
    mode.add_argument("--live", action="store_true")
    parser.add_argument("--manifest-url", default=MANIFEST_URL,
                        help="live manifest URL, also used for local HTTP tests")
    parser.add_argument("--wait", type=float, default=600,
                        help="seconds to allow Pages to settle, from 0 to 600")
    args = parser.parse_args()
    if not 0 <= args.wait <= 600:
        parser.error("--wait must be from 0 to 600 seconds")
    try:
        expected = json.loads((mirror.ROOT / "site" / "updater.json").read_text())
        plan = mirror.publish_plan(expected)
        if args.live:
            if mirror.mirror_entries(expected):
                verify_live(expected, mirror.CACHE, args.manifest_url, args.wait)
            else:
                print("GitHub updater URLs. Live mirror check skipped.")
        print(f"UPDATES MIRROR ok - {len(plan)} cached files checked")
    except (OSError, ValueError, KeyError) as exc:
        print(f"UPDATES MIRROR FAIL - {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
