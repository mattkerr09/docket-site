#!/usr/bin/env python3
"""Walk the path a customer walks: the page, the button, the file.

Every release is verified on the machine that built it — checksums against
`dist/`, `gh release download` against the tag, the installed app against its own
`--version`. All of that starts from an artifact somebody already knew was the
right one.

A customer starts somewhere else. They open the site, click a button, and open
what lands in their downloads folder. Nothing checked that path end to end until
it was walked by hand on 2026-08-15, and nothing compares **the file the site
links** against **the checksums the site links** — two things the site itself
offers, which can disagree with each other while every existing gate passes:

  * `verify_release_assets.py` compares the release against `download.json`.
  * `verify_updater.py` compares the manifest against the tarball in `dist/`.
  * `publish_checksums.sh` compares `SHA256SUMS` against `dist/`.

None of them reads a link off the rendered page. A tag that moved, a stale
button, a `SHA256SUMS` left behind from the previous release — each produces a
site that offers a file and a checksum that do not match, and each of those gates
stays green.

Two tiers, for the reason `verify_updater_live.py` gives: the cheap half belongs
in the deploy path, the 21 MB half does not.

    python3 scripts/verify_download_path.py           # links resolve, tag agrees
    python3 scripts/verify_download_path.py --full    # downloads and compares

`--full` is what a release should run. The default is what every deploy can
afford.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import re
import sys
import urllib.error
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[1]
SITE = ROOT / "site"
UA = {"User-Agent": "docketseo-download-path/1.0"}

#: Where a release asset lives, whoever links it.
LINK = re.compile(r'href="(https://github\.com/[^"]*/releases/download/[^"]+)"')


def fail(message: str) -> int:
    print(f"DOWNLOAD PATH FAIL — {message}", file=sys.stderr)
    return 1


def _links() -> dict:
    """Every release-asset URL on the built site, and the pages linking it."""
    found: dict = {}
    for page in sorted(SITE.rglob("*.html")):
        for url in LINK.findall(page.read_text(encoding="utf-8", errors="ignore")):
            found.setdefault(url, []).append(str(page.relative_to(SITE)))
    return found


def _head(url: str) -> tuple:
    request = urllib.request.Request(url, method="HEAD", headers=UA)
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return response.status, response.headers.get("content-length", "")
    except urllib.error.HTTPError as exc:
        return exc.code, ""
    except Exception as exc:                                  # noqa: BLE001
        return 0, type(exc).__name__


def _get(url: str, timeout: int = 300) -> bytes:
    with urllib.request.urlopen(
            urllib.request.Request(url, headers=UA), timeout=timeout) as response:
        return response.read()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--full", action="store_true",
                        help="download the DMG and check it against the "
                             "SHA256SUMS the site links (about 21 MB)")
    args = parser.parse_args()

    data_path = ROOT / "data" / "download.json"
    if not data_path.is_file():
        return fail("data/download.json is missing, so there is no tag to "
                    "check the links against")
    data = json.loads(data_path.read_text())
    tag = data.get("tag", "")
    if not tag:
        return fail("download.json names no tag")

    links = _links()
    if not links:
        return fail("no release-download links on the built site at all. Either "
                    "the download button is gone or its markup changed — both "
                    "are worth stopping for")

    failures: list = []

    # 1. every link points at the release this site is publishing
    for url, pages in sorted(links.items()):
        if f"/download/{tag}/" not in url:
            failures.append(
                f"{url} is linked from {', '.join(sorted(set(pages))[:3])} and "
                f"is not from {tag}. A visitor clicking it downloads a different "
                f"release from the one this site describes.")

    # 2. and each one actually resolves
    for url in sorted(links):
        status, detail = _head(url)
        if status != 200:
            failures.append(
                f"{url} answers {status or detail}. The page offers it and "
                f"GitHub does not have it.")
        else:
            print(f"  ok  {url.rsplit('/', 1)[-1]} ({detail} bytes)")

    if failures:
        print("DOWNLOAD PATH FAIL", file=sys.stderr)
        for f in failures:
            print(f"  {f}", file=sys.stderr)
        return 1

    if not args.full:
        print(f"\nDOWNLOAD PATH ok — {len(links)} linked asset(s), all from {tag} "
              f"and all served. Run --full to download and check the checksum.")
        return 0

    # 3. the file the site links against the checksums the site links
    #
    # Deliberately not against dist/ or against a `gh release download`. Those
    # answer "did we build what we think we built". This answers "does what the
    # site offers agree with itself", which is the only version of the question a
    # customer can be affected by.
    sums_url = next((u for u in links if u.endswith("SHA256SUMS")), "")
    dmg_url = next((u for u in links if u.endswith(".dmg")), "")
    if not sums_url or not dmg_url:
        return fail(f"the site links no {'SHA256SUMS' if not sums_url else 'DMG'}, "
                    f"so a visitor has nothing to verify their download against")

    try:
        sums = _get(sums_url, timeout=60).decode("utf-8", "replace")
        blob = _get(dmg_url)
    except Exception as exc:                                  # noqa: BLE001
        return fail(f"could not download from the site's own links: {exc}")

    name = dmg_url.rsplit("/", 1)[-1]
    published = ""
    for line in sums.splitlines():
        parts = line.split()
        if len(parts) == 2 and parts[1].lstrip("*") == name:
            published = parts[0]
    if not published:
        return fail(f"{name} is linked from the site and is not listed in the "
                    f"SHA256SUMS the site also links. A visitor who checks their "
                    f"download has nothing to check it against.")

    got = hashlib.sha256(blob).hexdigest()
    if got != published:
        return fail(
            f"the DMG the site links does not match the SHA256SUMS the site "
            f"links.\n    published {published}\n    downloaded {got}\n"
            f"  Both come from this site. One of them is from a different build.")

    print(f"\nDOWNLOAD PATH ok — {name} ({len(blob):,} bytes) downloaded from the "
          f"link on the page and matching the SHA256SUMS on the page: {got}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
