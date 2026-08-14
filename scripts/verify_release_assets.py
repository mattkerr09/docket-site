#!/usr/bin/env python3
"""Refuse to publish a download page whose release is not fully published.

Every other gate here checks something local: the numbers against their data,
the manifest against the tarball in `dist/`, the page against its own claims.
Nothing checked **the release the page points at**, which lives on GitHub and is
published by a different command, in a different repository, at a different
moment. So the one thing the download page cannot function without was the one
thing nothing verified before the page went live.

`verify_live.py` does check it — and only afterwards, by hand, once the CDN has
propagated. By then the broken page is public. That is the wrong end.

**What already covered part of this, and what it missed.** The contact gate
resolves every URL a built page links, so a tag that does not exist and a
missing `SHA256SUMS` were already caught — it refused a deploy for exactly that
last release. Two things are outside its reach, because it can only check what a
page links and only checks the status code:

* `Docket.app.tar.gz` and its `.sig` are read by the updater and linked from no
  page at all. Without them Tauri downloads nothing, reports nothing, and every
  installed copy sits on an old build believing it is current. `verify_updater.py`
  checks those files in `dist/`, not the ones actually published.
* An asset can answer 200 under the right name and be the *previous* build. The
  link works, the size on the page is wrong, and the published checksum does not
  match the file — which reads to a careful reader as tampering.

**Three ways this has actually gone wrong, all of them silent:**

* `gh release create` without `--repo` uses the *working directory's* origin.
  Run from the app checkout it publishes to the private app repo, so the tag on
  this repo does not exist and every download link on the page 404s, while the
  release page you just opened in a browser looks perfect.
* The upload names the artifacts by hand and one is left out. `SHA256SUMS` went
  missing exactly this way; the page tells the reader to run `shasum -a 256 -c`
  against a file that is not there.
* An asset is present under the right name but is the *previous* build, because
  a re-upload was skipped or `--clobber` was forgotten. The link works, the
  checksum does not match, and that reads to a careful reader as tampering.

The size check catches the third. `download.json` records the byte count of the
artifact `collect_updater.py` measured, so comparing it against the size GitHub
reports for the published asset costs one API call and no downloads, and a
mismatch means the page's "21.8 MB" and the file behind it are different files.

Skips cleanly when GitHub cannot be reached, and says so. A network failure is
not evidence the release is broken, and a gate that fails closed on someone
else's outage teaches people to pass `--force`.
"""
from __future__ import annotations

import json
import pathlib
import subprocess
import sys
import urllib.error
import urllib.request

REPO = "mattkerr09/docket-site"
#: Where the release goes when `--repo` is forgotten. Named so the failure can
#: say what actually happened rather than "not found".
WRONG_REPO = "mattkerr09/docket-app"
SITE = pathlib.Path(__file__).resolve().parent.parent / "site"
DOWNLOAD = SITE / "_data" / "download.json"

#: Assets that do not vary with the version. The updater reads the first two and
#: fails silently without them; the page documents the third.
FIXED = ("Docket.app.tar.gz", "Docket.app.tar.gz.sig", "SHA256SUMS")


def fail(message: str) -> None:
    print(f"RELEASE FAIL — {message}")
    sys.exit(1)


def skip(message: str) -> None:
    print(f"RELEASE skipped — {message}")
    sys.exit(0)


def _release(repo: str, tag: str) -> dict | None:
    """The release, or None if this repo has no such tag.

    `gh` first so a private repo can be checked at all, falling back to the
    public API so the gate still works where `gh` is not installed.
    """
    try:
        out = subprocess.run(
            ["gh", "api", f"repos/{repo}/releases/tags/{tag}"],
            capture_output=True, text=True, timeout=30)
        if out.returncode == 0:
            return json.loads(out.stdout)
        if "Not Found" in out.stderr or "404" in out.stderr:
            return None
    except FileNotFoundError:
        pass
    except (subprocess.TimeoutExpired, json.JSONDecodeError) as exc:
        skip(f"could not read {repo} {tag}: {type(exc).__name__}")

    request = urllib.request.Request(
        f"https://api.github.com/repos/{repo}/releases/tags/{tag}",
        headers={"User-Agent": "docketseo-release-gate/1.0",
                 "Accept": "application/vnd.github+json"})
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.loads(response.read().decode())
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return None
        skip(f"GitHub answered {exc.code} for {repo} {tag}")
    except Exception as exc:                                  # noqa: BLE001
        skip(f"could not reach GitHub: {type(exc).__name__}")
    return None


def main() -> None:
    if not DOWNLOAD.is_file():
        fail(f"{DOWNLOAD} is missing, so the page's download links "
             "cannot be checked against anything")
    data = json.loads(DOWNLOAD.read_text())
    tag = data.get("tag", "")
    if not tag:
        fail("download.json carries no tag")

    release = _release(REPO, tag)
    if release is None:
        # Before saying the release does not exist, look where it goes when the
        # flag is forgotten. "Published to the wrong repository" and "never
        # published" need different fixes, and the first is invisible from here
        # unless something goes and looks.
        stray = _release(WRONG_REPO, tag)
        if stray is not None:
            fail(f"{tag} does not exist on {REPO}, but it does exist on "
                 f"{WRONG_REPO} — `gh release create` without `--repo` uses "
                 f"the working directory's origin. Publish it to {REPO}; "
                 "every download link on the page points there.")
        fail(f"{tag} does not exist on {REPO}, and the download page offers "
             f"{tag} links on every page that mentions downloading")

    published = {a["name"]: a for a in release.get("assets", [])}
    expected = [n for n in (data.get("dmg_name", ""), data.get("linux_name", ""))
                if n] + list(FIXED)

    missing = [n for n in expected if n not in published]
    if missing:
        # Which ones matters, because they fail differently. A missing DMG or
        # SHA256SUMS is a 404 a buyer sees. A missing updater asset is seen by
        # nobody: Tauri finds nothing to download and every installed copy goes
        # on believing it is current.
        quiet = [n for n in missing if n.startswith("Docket.app.tar.gz")]
        loud = [n for n in missing if n not in quiet]
        parts = []
        if loud:
            parts.append(f"{', '.join(loud)} — the page links these, so each "
                         "is a 404 for a buyer")
        if quiet:
            parts.append(f"{', '.join(quiet)} — no page links these and the "
                         "updater reads them, so every installed copy would "
                         "sit on an old build with nothing reporting why")
        fail(f"{tag} is published without {'; and without '.join(parts)}")

    # An asset under the right name can still be the previous build.
    for name, key in ((data.get("dmg_name", ""), "dmg_bytes"),
                      (data.get("linux_name", ""), "linux_bytes")):
        want = data.get(key)
        if not name or not want:
            continue
        got = published[name].get("size")
        if got != want:
            fail(f"{name} on {tag} is {got} bytes and download.json says "
                 f"{want} — the page's size and the file behind it are "
                 "different files, so the published checksum cannot match")

    print(f"RELEASE ok — {tag} on {REPO} carries all "
          f"{len(expected)} advertised assets, sizes agree with download.json")


if __name__ == "__main__":
    main()
