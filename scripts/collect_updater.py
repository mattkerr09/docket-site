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


#: A value that means "the notes are in this file", not "the notes are this
#: string". Anything with a directory separator, or a bare markdown/text
#: filename, is a path — nobody writes release notes that look like that.
def _looks_like_a_path(value: str) -> bool:
    stripped = value.strip()
    if not stripped or "\n" in stripped:
        return False
    return ("/" in stripped
            or stripped.endswith(".md")
            or stripped.endswith(".txt"))


def _notes_text(value: str) -> str:
    """The notes themselves, whether given as text or as a file to read.

    ⚠️ CUSTOMERS WERE SHOWN A TEMP-FILE PATH AS THE RELEASE NOTES.
    Measured on the live manifest, 2026-08-25. `--notes` documented itself as
    "what changed, shown to the user" and stored whatever string it was handed,
    and every caller handed it a filename:

        1.2.4  "notes": "/tmp/notes-1.2.4.md"
        1.2.5  "notes": "/tmp/notes419.md"

    Both shipped. Every installed copy offering an update showed the reader
    `/tmp/notes-1.2.4.md` where the description of the release should have been
    — a path that does not exist on their machine, describing nothing.

    Nothing caught it because every mechanism was working: the tarball agreed
    with the version, the signature verified against the app's public key, and
    the updater gate passed. The field was populated, the manifest was valid,
    and the only thing wrong was the part a person reads.

    So the flag now accepts either, because both callers exist and the
    difference was never visible at the call site. A path that does not resolve
    is fatal rather than silently literal: shipping the string is the failure
    this exists to prevent, and falling back to it would reintroduce it exactly.
    """
    if not _looks_like_a_path(value):
        return value
    path = pathlib.Path(value).expanduser()
    if not path.is_file():
        sys.exit(f"--notes looks like a path but there is no file at {path}. "
                 f"Pass the notes themselves, or a file that exists — the one "
                 f"thing that must not happen is publishing this string to "
                 f"customers as the description of the release.")
    text = path.read_text(encoding="utf-8").strip()
    if not text:
        sys.exit(f"{path} is empty; refusing to publish a release with no notes")
    return text


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--version", required=True,
                    help="the version being published, e.g. 0.1.1")
    # ⚠️ NO DEFAULT TAG. It used to be "v0.1.0" — the marketing version, and a
    # release tag that has not hosted a current asset for months. Omitting
    # --tag then wrote every download link on the site as
    # `/releases/download/v0.1.0/Docket-1.3.14-arm64.dmg`: a real filename
    # under a tag that does not carry it, so every one of them 404s. The
    # contact gate in deploy.sh caught all three and refused to publish, which
    # is the only reason it cost a deploy cycle rather than a day of downloads.
    #
    # A default that is wrong for every release is not a default. The tag is
    # derived from --version unless it is given explicitly.
    ap.add_argument("--tag", default="",
                    help="release tag hosting the asset (default: v<version>)")
    # ⚠️ REQUIRED. It defaulted to "" and line 130 below turned that into
    # `"notes": "Docket 1.3.14"` — a valid manifest whose description of the
    # release is its own version number, shown to every customer the updater
    # prompts. `_notes_text` above refuses an EMPTY FILE for exactly that
    # reason ("refusing to publish a release with no notes") and the empty
    # ARGUMENT walked straight past it into a silent fallback.
    #
    # Shipped that way on 1.3.14, 2026-09-01, and caught by reading the live
    # manifest as a customer rather than by any gate. 1.3.12 and 1.3.13 both
    # carry real notes, so this was a regression in what the update prompt
    # says, not a standing gap.
    ap.add_argument("--notes", required=True,
                    help="what changed, shown to the user — literal text, or a "
                         "path to a file containing it")
    args = ap.parse_args()
    if not args.tag:
        args.tag = f"v{args.version}"
    notes = _notes_text(args.notes)

    for path in (TGZ, SIG):
        if not path.is_file():
            sys.exit(f"missing {path} — run ./scripts/build_docket.sh --ship first")

    signature = SIG.read_text().strip()
    if not signature:
        sys.exit(f"{SIG} is empty; refusing to publish a manifest that rejects "
                 f"every update")

    data = {
        "version": args.version,
        "notes": notes,
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
        # Repo-root data/, NOT site/_data. The measurements moved out of the
        # deployed directory on 2026-08-18 — everything under site/ is pushed
        # to gh-pages and served — and this line was written as a bare "_data"
        # string, so it matched none of the greps that found the rest and kept
        # writing to a directory that no longer exists. The failure was loud in
        # the right place: download.json went stale, so the ACTION gate refused
        # the deploy for pinning an old release.
        size_path = OUT.parent.parent / "data" / "download.json"
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
            # rebuild it.
            #
            # This comment used to end "verify_updater.py refuses the deploy
            # either way", which was not true: that gate's loop read
            # `if not name: continue`, and verify_release_assets.py reported
            # "all advertised assets" because Linux was no longer advertised.
            # Dropping the keys silenced every gate that could have noticed,
            # while six pages went on promising a Linux build in prose. Written
            # 2026-08-15 while publishing 1.1.30, in exactly that state.
            # `_a_promised_linux_build_exists` is now the gate this named.
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
