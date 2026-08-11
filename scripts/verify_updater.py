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

import base64
import json
import pathlib
import plistlib
import shutil
import subprocess
import sys
import tarfile
import tempfile

SITE = pathlib.Path(__file__).resolve().parent.parent / "site"
APP = pathlib.Path("/Users/matthewkerr/Downloads/SEO audit app")
MANIFEST = SITE / "updater.json"
TGZ = APP / "dist" / "Docket.app.tar.gz"
SIG = APP / "dist" / "Docket.app.tar.gz.sig"
TAURI_CONF = APP / "ui" / "src-tauri" / "tauri.conf.json"


def fail(message: str) -> None:
    print(f"UPDATER FAIL — {message}")
    sys.exit(1)


def _tarball_version() -> str | None:
    """`CFBundleShortVersionString` from the app inside the tarball.

    The manifest's `version` is what the updater compares against the *running*
    binary. If it claims a version the tarball does not contain, the update is
    offered, downloaded, installed, and then offered again on the next launch,
    for ever — no error, no end, and nothing in any log saying why.
    """
    if not TGZ.is_file():
        return None
    with tarfile.open(TGZ) as archive:
        for member in archive.getmembers():
            if member.name.endswith("Docket.app/Contents/Info.plist"):
                handle = archive.extractfile(member)
                if handle is None:
                    return None
                return plistlib.load(handle).get("CFBundleShortVersionString")
    return None


def _signature_verifies(published: str):
    """Does the published signature actually verify, under the app's own key?

    The string comparison below proves the manifest carries the same text as
    dist/Docket.app.tar.gz.sig. It does not prove that text is a valid signature
    for that tarball under the public key compiled into the binary — and that is
    the failure this whole file exists to prevent. Sign with a key that is not
    the one in tauri.conf.json and both strings still agree with each other
    while every client rejects the update in silence.

    Returns None when minisign is absent: a check that could not run is reported
    as not run, never as a pass.
    """
    exe = shutil.which("minisign")
    if not exe or not TGZ.is_file():
        return None, "minisign not installed" if not exe else "no local tarball"
    try:
        pubkey = json.loads(TAURI_CONF.read_text())["plugins"]["updater"]["pubkey"]
    except (OSError, KeyError, json.JSONDecodeError) as exc:
        return None, f"could not read the updater pubkey from tauri.conf.json ({exc})"

    with tempfile.TemporaryDirectory() as tmp:
        pub = pathlib.Path(tmp) / "docket.pub"
        sig = pathlib.Path(tmp) / "Docket.app.tar.gz.sig"
        pub.write_bytes(base64.b64decode(pubkey))
        sig.write_bytes(base64.b64decode(published))
        result = subprocess.run(
            [exe, "-V", "-p", str(pub), "-x", str(sig), "-m", str(TGZ)],
            capture_output=True, text=True)
    detail = (result.stdout + result.stderr).strip().splitlines()
    return result.returncode == 0, detail[-1] if detail else ""


def _download_links_point_at_this_release() -> None:
    """Every filename in download.json must belong to the release it names.

    render.py builds each download link as `{REPO}/releases/download/{tag}/
    {filename}` — the tag from this release, the filename from this file. So a
    filename left over from the previous release produces a URL that is
    well-formed, looks right in the HTML, passes the link-graph gate (which
    does not fetch GitHub) and 404s for the user.

    `collect_updater.py` used to leave exactly that behind: it overwrote the
    Linux keys when the tarball was present and wrote the dict back untouched
    when it was not, so a release built without one inherited the last one's
    filename. That is now fixed at the source, and this is the gate for it —
    because the source fix only helps when collect_updater.py is the thing that
    wrote the file, and download.json is a small JSON file that anyone can edit.

    Checked against the version string rather than the tag, since the artifacts
    are named for the version (`docket-0.1.37-linux-x86_64.tar.gz`) while the
    URL uses the tag (`v0.1.37`).
    """
    path = SITE / "_data" / "download.json"
    if not path.is_file():
        return
    try:
        data = json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        fail(f"download.json is not valid JSON ({exc}); the download page "
             f"cannot be built and every download link would be wrong")

    version = data.get("version")
    if not version:
        fail("download.json names no version, so nothing can be checked "
             "against it")

    for key in ("dmg_name", "linux_name"):
        name = data.get(key)
        if not name:
            continue
        if version not in name:
            fail(f"download.json is publishing {version} but its {key} is "
                 f"{name!r}, which is a different release. The link is built "
                 f"from this release's tag and that filename, so it would "
                 f"404 — rebuild the artifact for {version}, or remove the "
                 f"key so the page offers nothing rather than something "
                 f"broken.")


def main() -> None:
    _download_links_point_at_this_release()

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

    inside = _tarball_version()
    if inside and inside != data["version"]:
        fail(f"updater.json says {data['version']} but the tarball contains "
             f"{inside}. The updater compares the manifest against the running "
             f"binary, so this update would be offered, installed, and offered "
             f"again on every launch for ever, with no error anywhere.")

    verified, detail = _signature_verifies(published)
    if verified is False:
        fail(f"the published signature does not verify against the updater "
             f"pubkey in tauri.conf.json ({detail}). The manifest and the .sig "
             f"agree with each other, so the check above passed — but every "
             f"client would reject this update in silence. The tarball was "
             f"signed with a different key than the one compiled into the app.")

    size = TGZ.stat().st_size // 1024 if TGZ.is_file() else 0
    crypto = ("signature verifies against the app's pubkey" if verified
              else f"SIGNATURE NOT CRYPTOGRAPHICALLY CHECKED — {detail}")
    print(f"UPDATER ok — {data['version']} (tarball agrees), {crypto} "
          f"({size} KB tarball), {len(platforms)} platform(s)")


if __name__ == "__main__":
    main()
