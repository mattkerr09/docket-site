#!/usr/bin/env python3
"""Walk the update path a customer's app actually walks, over the network.

`verify_updater.py` checks the manifest in this repo against the tarball in the
app repo's `dist/`. Both are on this machine. Neither is what an installed copy
of Docket touches.

**What a customer's app does, and where each step could fail silently:**

  1. fetches `https://docketseo.app/updater.json`   — could 404, or be stale
  2. compares `version` with its own                — could be older, or equal
  3. downloads the `url` in the manifest            — could 404 on the release
  4. verifies the signature with the key compiled   — could be last release's
     into the binary                                  signature
  5. installs

Steps 1, 3 and 4 are live and, until now, checked by nothing. And every one of
them fails **silently**: Tauri downloads, fails, and gives up without a message.
The user sits on an old build believing they are current, and no log anywhere
says otherwise. That is why the updater was registered for eight releases and
called by nothing before anybody noticed.

**This downloads the real tarball** — about twenty megabytes — because a
signature check against a local file proves nothing about the file being served.
That is why it is not in the deploy path: it runs on demand, after a release, and
answers the question "would an installed copy actually update".

    python3 scripts/verify_updater_live.py
    python3 scripts/verify_updater_live.py --from 1.1.20   # would this build update?
    python3 scripts/verify_updater_live.py --expect 1.1.34 # is the release live?
"""
from __future__ import annotations

import argparse
import base64
import json
import pathlib
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[1]
MANIFEST_URL = "https://docketseo.app/updater.json"
UA = {"User-Agent": "docketseo-updater-live/1.0"}


def fail(message: str) -> int:
    print(f"UPDATER LIVE FAIL — {message}", file=sys.stderr)
    return 1


def _get(url: str, timeout: int = 120) -> bytes:
    with urllib.request.urlopen(
            urllib.request.Request(url, headers=UA), timeout=timeout) as r:
        return r.read()


def _newer(a: str, b: str) -> bool:
    """Is `a` a later version than `b`? Numeric, not lexical — "1.1.9" is not
    later than "1.1.20" and a string compare says it is."""
    def parts(v):
        return [int(x) for x in v.split(".") if x.isdigit()]
    return parts(a) > parts(b)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--from", dest="installed", default=None,
                        help="pretend an installed build is this version")
    parser.add_argument("--expect", default=None, metavar="VERSION",
                        help="the version just released; fails if the served "
                             "manifest never catches up to it")
    parser.add_argument("--settle", type=int, default=90, metavar="SECONDS",
                        help="how long to allow the CDN to catch up (default 90)")
    args = parser.parse_args()

    # 1. the manifest, as served
    try:
        manifest = json.loads(_get(MANIFEST_URL, timeout=30))
    except urllib.error.HTTPError as exc:
        return fail(f"{MANIFEST_URL} answered {exc.code}. Every installed copy "
                    "asks for this file and would get the same.")
    except Exception as exc:                                  # noqa: BLE001
        return fail(f"could not fetch {MANIFEST_URL}: {type(exc).__name__}")

    version = manifest.get("version", "")
    platforms = manifest.get("platforms", {})
    if not version or not platforms:
        return fail(f"the manifest is served but carries no {'version' if not version else 'platforms'}")
    print(f"  manifest : {version}, {len(platforms)} platform(s)")

    # 1a. is it the release we just made?
    #
    # The docstring above has always said step 1 "could 404, **or be stale**",
    # and staleness was the one thing nothing checked. Found 2026-08-15,
    # publishing 1.1.34: this script printed `UPDATER LIVE ok — offers 1.1.33`
    # and exited zero. Everything it verified was true — that manifest is
    # coherent, its tarball downloads, its signature verifies — and every one of
    # those things is equally true of a manifest that never gets replaced again.
    #
    # A deploy that silently fails to publish updater.json leaves customers on
    # an old build for ever, which is the exact failure this file was written to
    # catch, and the check would have gone on saying ok.
    #
    # **The wait is for the CDN, not for the deploy.** GitHub Pages serves the
    # previous file for a short window after a push, so a bare comparison would
    # fail every release for a reason that is not a fault. It re-reads with
    # cache-busting until the served version catches up or the window closes;
    # only then is it stale. Opt-in via --expect, so running this on its own to
    # answer "would an installed copy update" still works with no release in
    # mind.
    if args.expect and version != args.expect:
        deadline = time.monotonic() + max(0, args.settle)
        while time.monotonic() < deadline:
            time.sleep(10)
            try:
                fresh = json.loads(_get(f"{MANIFEST_URL}?cb={int(time.time())}",
                                        timeout=30))
            except Exception:                                 # noqa: BLE001
                continue
            if fresh.get("version") == args.expect:
                manifest, version = fresh, args.expect
                platforms = manifest.get("platforms", {})
                print(f"  manifest : {version} after CDN propagation")
                break
        else:
            return fail(
                f"{MANIFEST_URL} still offers {version}, not the {args.expect} "
                f"just released, {args.settle}s after the deploy. Everything "
                f"else about that manifest may be perfectly valid — a stale "
                f"manifest is coherent, downloads and verifies — and every "
                f"installed copy will go on believing it is current. Check that "
                f"the deploy published site/updater.json.")

    # 2. would an installed build take it?
    installed = args.installed
    if installed:
        if not _newer(version, installed):
            return fail(f"an installed {installed} would not update: the "
                        f"manifest offers {version}, which is not newer. "
                        "Tauri compares versions and says nothing when it "
                        "declines.")
        print(f"  offer    : {installed} → {version}, so an installed copy takes it")

    exe = shutil.which("minisign")
    if not exe:
        print("  signature: SKIPPED — minisign is not installed, so the step "
              "that matters most was not checked.")
        return 0

    try:
        pubkey = json.loads(
            (ROOT.parent / "docket-app" / "ui" / "src-tauri"
             / "tauri.conf.json").read_text())["plugins"]["updater"]["pubkey"]
    except Exception as exc:                                  # noqa: BLE001
        return fail(f"could not read the updater pubkey: {type(exc).__name__}")

    for name, entry in platforms.items():
        url, signature = entry.get("url", ""), entry.get("signature", "")
        if not url or not signature:
            return fail(f"{name} has no {'url' if not url else 'signature'}")

        # 3. the tarball, from the URL the manifest gives — not from dist/
        try:
            payload = _get(url, timeout=300)
        except urllib.error.HTTPError as exc:
            return fail(f"{name}: the manifest points at {url}, which answers "
                        f"{exc.code}. Every update attempt downloads nothing "
                        "and gives up without a message.")
        except Exception as exc:                              # noqa: BLE001
            return fail(f"{name}: could not download {url}: {type(exc).__name__}")
        print(f"  download : {name} — {len(payload) // 1024} KB from the release")

        # 4. the signature, against the key compiled into the shipped binary
        with tempfile.TemporaryDirectory() as tmp:
            pub = pathlib.Path(tmp) / "docket.pub"
            sig = pathlib.Path(tmp) / "update.sig"
            tgz = pathlib.Path(tmp) / "update.tar.gz"
            pub.write_bytes(base64.b64decode(pubkey))
            sig.write_bytes(base64.b64decode(signature))
            tgz.write_bytes(payload)
            result = subprocess.run(
                [exe, "-V", "-p", str(pub), "-x", str(sig), "-m", str(tgz)],
                capture_output=True, text=True)
        if result.returncode != 0:
            detail = (result.stdout + result.stderr).strip().splitlines()
            return fail(f"{name}: the signature in the live manifest does not "
                        f"verify against the file it points at "
                        f"({detail[-1] if detail else 'no output'}). Tauri "
                        "would reject this update and tell nobody.")
        print(f"  signature: {name} — verifies against the app's own key")

    print(f"\nUPDATER LIVE ok — {MANIFEST_URL} offers {version}, the file it "
          "points at downloads, and its signature verifies under the key "
          "compiled into the shipped binary.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
