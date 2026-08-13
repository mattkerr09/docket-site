#!/usr/bin/env python3
"""Generate site/updater.json — the manifest Docket's in-app updater reads.

Tauri's updater fetches this, compares `version` against the running build,
downloads `url`, verifies `signature` against the public key compiled into the
binary, then unpacks and relaunches.

Everything here is read from the artifacts the build just produced. The
signature in particular is read out of the `.sig` file rather than pasted:
a manifest whose signature does not match its tarball does not warn anybody,
it simply means every update is silently rejected and users sit on an old
build forever believing they are current. That is the worst failure this file
can have, so nothing in it is typed by hand.

Run after ./scripts/build_docket.sh --ship, before deploying the site.
"""
from __future__ import annotations

import sys as _sys
from pathlib import Path as _Path
_sys.path.insert(0, str(_Path(__file__).resolve().parent))
import app_path  # noqa: E402

import argparse
import datetime
import hashlib
import json
import re
import pathlib
import sys

APP = app_path.find()
OUT = pathlib.Path(__file__).resolve().parent.parent / "site" / "updater.json"

TGZ = APP / "dist" / "Docket.app.tar.gz"
SIG = APP / "dist" / "Docket.app.tar.gz.sig"

#: Where the tarball is served from. The GitHub release, not the site: GitHub
#: Pages has a soft size limit and a 100 MB hard one per file, and serving a
#: 17 MB binary from the same host as the manifest buys nothing.
RELEASE = "https://github.com/mattkerr09/docket-site/releases/download"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--version", required=True,
                    help="the version being published, e.g. 0.1.1")
    ap.add_argument("--tag", default="v0.1.0", help="release tag hosting the asset")
    ap.add_argument("--notes", default="", help="what changed, shown to the user")
    args = ap.parse_args()

    for path in (TGZ, SIG):
        if not path.is_file():
            sys.exit(f"missing {path} — run ./scripts/build_docket.sh --ship first")

    signature = SIG.read_text().strip()
    if not signature:
        sys.exit(f"{SIG} is empty; refusing to publish a manifest that rejects "
                 f"every update")

    data = {
        "version": args.version,
        "notes": args.notes or f"Docket {args.version}",
        "pub_date": datetime.datetime.now(datetime.timezone.utc)
                    .replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "platforms": {
            # Apple Silicon only, and named explicitly. A manifest that also
            # claimed darwin-x86_64 would offer an arm64 binary to Intel Macs,
            # which fails after the download rather than before it.
            "darwin-aarch64": {
                "signature": signature,
                "url": f"{RELEASE}/{args.tag}/Docket.app.tar.gz",
            }
        },
    }
    OUT.write_text(json.dumps(data, indent=2) + "\n")

    # The download size, recorded so the site cannot claim one and ship
    # another. Decimal MB, because that is what a browser's download panel and
    # the Finder show a user — the binary MiB figure reads ~1 MB smaller and
    # would make the page understate the download. It was hardcoded "17 MB"
    # against an 18.3 MB file.
    # Named from the version being published, not typed. It was
    # "Docket-0.1.0-arm64.dmg" hardcoded here and again in render.py, so the
    # first version bump would have pointed the site's download button at a
    # file that does not exist — and a download link that 404s is the single
    # worst bug a product site can have.
    dmg = APP / "dist" / f"Docket-{args.version}-arm64.dmg"
    if dmg.is_file():
        size_path = OUT.parent / "_data" / "download.json"
        size_path.write_text(json.dumps({
            "version": args.version,
            "tag": args.tag,
            "dmg_name": dmg.name,
            "dmg_bytes": dmg.stat().st_size,
            "dmg_mb": round(dmg.stat().st_size / 1_000_000, 1),
            "measured": datetime.datetime.now(datetime.timezone.utc)
                        .strftime("%Y-%m-%d"),
            "note": ("Decimal MB, matching what a browser download panel and "
                     "the Finder report. Written by collect_updater.py from "
                     "the artifact actually published."),
        }, indent=2) + "\n")
        print(f"  dmg       : {dmg.stat().st_size / 1_000_000:.1f} MB "
              f"({dmg.stat().st_size:,} bytes)")

        # The Linux CLI, measured the same way and for the same reason. The
        # download page described "a 12 MB tarball" from memory while no Linux
        # asset had been published since 0.1.0 — seven releases of the desktop
        # app went out without it, because the publish step only ever named the
        # DMG and the updater tarball.
        linux = APP / "dist" / f"docket-{args.version}-linux-x86_64.tar.gz"
        sizes = json.loads(size_path.read_text())
        if linux.is_file():
            sizes.update({
                "linux_name": linux.name,
                "linux_bytes": linux.stat().st_size,
                "linux_mb": round(linux.stat().st_size / 1_000_000, 1),
            })
            print(f"  linux     : {linux.stat().st_size / 1_000_000:.1f} MB "
                  f"({linux.name})")
        else:
            # Drop the previous release's keys rather than leaving them.
            #
            # The `if` above overwrites them; this branch used to write `sizes`
            # back untouched, so the OLD version's filename survived into the
            # NEW version's download.json. render.py builds the link as
            # `{REPO}/releases/download/{RELEASE}/{LINUX_NAME}` — current tag,
            # stale filename — so the page would have offered
            # `v0.1.37/docket-0.1.36-linux-x86_64.tar.gz`: a 404, on the one
            # link a Linux visitor came for.
            #
            # It is a live trap, not a hypothetical. build_docket.sh wipes
            # dist/ on purpose (a Linux CLI built before a source correction
            # carries the same version number as the Mac app built after it),
            # so building Linux and then Mac in that order — the order the
            # release mechanics list them — leaves exactly this state.
            #
            # Offering nothing is worse than offering a working tarball and
            # better than offering a broken link, so the keys go and the page
            # renders no Linux link at all. The word MISSING is the signal to
            # rebuild it; verify_updater.py refuses the deploy either way.
            dropped = [k for k in ("linux_name", "linux_bytes", "linux_mb")
                       if sizes.pop(k, None) is not None]
            print(f"  linux     : MISSING — {linux.name} was not built, so the "
                  f"site cannot offer it")
            if dropped:
                print(f"              dropped {', '.join(dropped)} from "
                      f"download.json; they described an older release and "
                      f"would have rendered a link that 404s")
        size_path.write_text(json.dumps(sizes, indent=2) + "\n")

    digest = hashlib.sha256(TGZ.read_bytes()).hexdigest()[:16]
    print(f"  version   : {args.version}")
    print(f"  tarball   : {TGZ.name} ({TGZ.stat().st_size // 1024} KB, sha {digest})")
    print(f"  signature : {len(signature)} chars, read from {SIG.name}")
    print(f"  written   : {OUT}")

    # The GitHub Action installs a pinned tag, and that pin is a second place
    # the current version lives. It drifted the moment 0.1.47 was published:
    # the deploy gate caught it and stopped the release, which is the gate
    # working — but a gate that requires a human to remember an edit every time
    # is a chore, and chores get skipped. The release step that already knows
    # the version writes it.
    action = pathlib.Path(__file__).resolve().parent.parent / "action.yml"
    if action.exists():
        text = action.read_text()
        bumped, n = re.subn(r"(version:.*?default: ')v[\d.]+(')",
                            rf"\g<1>v{args.version}\g<2>", text, count=1, flags=re.S)
        if n and bumped != text:
            action.write_text(bumped)
            print(f"  action.yml: default pinned to v{args.version}")
        elif n:
            print(f"  action.yml: already v{args.version}")
        else:
            print("  action.yml: could not find the version default to update")


if __name__ == "__main__":
    main()
