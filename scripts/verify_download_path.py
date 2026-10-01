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
sys.path.insert(0, str(ROOT / "scripts"))
import own_hosts  # noqa: E402
SITE = ROOT / "site"
#: Identifies as a robot (the ops convention, CEO 2026-09-29), so the download
#: counter it HEADs never tallies this check as a person.
UA = {"User-Agent": "kerr-ops/1.0 (verify_download_path)"}

#: Where a release asset lives, whoever links it.
LINK = re.compile(r'href="(https://github\.com/[^"]*/releases/download/[^"]+)"')
#: A Download button wrapped in our counter (render.download_url): the file is
#: the `to=` parameter, which is last and unencoded. The counter itself is
#: checked too (step 2b): a wrapper that forwards somewhere else is a broken
#: button even when the file it names is fine.
HUB_LINK = re.compile(r'href="(https://kerr-affiliate-hub\.kerrco\.workers\.dev/dl/[^"]*?[?&]to='
                      r'(https://github\.com/[^"]*/releases/download/[^"]+))"')


def fail(message: str) -> int:
    print(f"DOWNLOAD PATH FAIL — {message}", file=sys.stderr)
    return 1


def _links() -> dict:
    """Every release-asset URL on the built site, and the pages linking it.
    A counter-wrapped link counts as the file it names."""
    found: dict = {}
    for page in sorted(SITE.rglob("*.html")):
        html = page.read_text(encoding="utf-8", errors="ignore").replace("&amp;", "&")
        for url in LINK.findall(html):
            found.setdefault(url, []).append(str(page.relative_to(SITE)))
        for _wrapped, url in HUB_LINK.findall(html):
            found.setdefault(url, []).append(str(page.relative_to(SITE)))
    return found


def _wrapped() -> dict:
    """Counter URL -> the file it should forward to."""
    out: dict = {}
    for page in sorted(SITE.rglob("*.html")):
        html = page.read_text(encoding="utf-8", errors="ignore").replace("&amp;", "&")
        for wrapped, url in HUB_LINK.findall(html):
            out[wrapped] = url
    return out


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):  # noqa: D401
        return None


def _forwards_to(url: str) -> str:
    """Where the counter sends a visitor (Location of its redirect), or why not."""
    opener = urllib.request.build_opener(_NoRedirect)
    request = urllib.request.Request(url, method="HEAD", headers=UA)
    try:
        opener.open(request, timeout=30)
        return "no redirect"
    except urllib.error.HTTPError as err:
        return err.headers.get("Location", f"HTTP {err.code} with no Location")
    except Exception as err:  # noqa: BLE001
        return f"unreachable ({err})"


def _head(url: str) -> tuple:
    # HEAD_OPENER, not urlopen: urllib re-sends a redirected HEAD as a GET, so
    # this "HEAD" of a release link fetched the DMG behind GitHub's 302.
    request = urllib.request.Request(url, method="HEAD", headers=UA)
    try:
        with own_hosts.HEAD_OPENER.open(request, timeout=30) as response:
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

    # 2b. every counter-wrapped button forwards to exactly the file it names.
    # A HEAD, so the counter's own tally is not inflated by this gate.
    for wrapped, url in sorted(_wrapped().items()):
        went = _forwards_to(wrapped)
        if went != url:
            failures.append(f"the download counter {wrapped} forwards to {went}, not {url}")
        else:
            print(f"  ok  counter -> {url.rsplit('/', 1)[-1]}")

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
